import pyomo.environ as pyo
import numpy as np
from pyomo.core import simple_constraint_rule
import os
import sys
import db_readeru
import traceback
import logging
import forecasters
import re
import time as timeh

logging.basicConfig(filename='.\log\logging.log', level=logging.ERROR,
                                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger = logging.getLogger(__name__)

class Data_Importer():


    def __init__(self, rows=240):

        try:
            print()
            print("...Попытка подключения к БД MS SQL Server...")
            self.db_connection = db_readeru.DB_connector()
            print()
            print("...Подключение успешно!...")
        except Exception as e:
            logging.error(traceback.format_exc())
            print()
            print("****** ОШИБКА! Не удалось подключиться к БД MS SQL server! ******")
            print()
            print("////// Модуль аварийно завершил работу. //////")
            print()
            print("////// Окно закроется автоматически через 30 секунд. //////")
            timeh.sleep(30)
            sys.exit(1)

        try:
            start_timeh = timeh.time()
            print()
            print("...Загрузка вспомогательных файлов...")
            self.load_files = ['models/mlp_load_hourly.vrk', 'models/X_scaler_par.sca', 'models/Y_scaler_par.sca']
            self.pv_files = ['models/pv_keras', 'models/pv_keras/pv_X_scaler_par.sca',
                             'models/pv_keras/pv_Y_scaler_par.sca']
            self.pv_files2 = ['models/mlp_irrad_hourly_weather.vrk', 'models/irr_w_X_scaler_par.sca', 'models/irr_w_Y_scaler_par.sca']
            self.rowses = rows
            print()
            print("...Загрузка данных из БД SQL Server...")
            self.data_from_sql = self.db_connection.db_to_pd(rows=self.rowses)[0]
            print()
            print(self.data_from_sql)
            print()
            print("--- Данные из БД загружены за %s сек. ---" % round((timeh.time() - start_timeh), 3))

        except Exception as e:
            logging.error(traceback.format_exc())
            print()
            print("****** ОШИБКА! Не удалось загрузить вспомогательные файлы. ******")
            print()
            print("////// Модуль аварийно завершил работу. //////")
            print()
            print("////// Окно закроется автоматически через 30 секунд. //////")
            timeh.sleep(30)
            sys.exit(1)

    def eq_status(self):
        self.data_from_sql = self.db_connection.db_to_pd(self.rowses)[0]
        availabilities = self.db_connection.equipment_availability(self.data_from_sql)
        dgu_states = self.db_connection.dgu_states(self.data_from_sql)
        return availabilities, dgu_states

    def current_data(self):
        soc1_before = self.data_from_sql['F68'][0] / 10 # последнее на данную минуту значение уровня заряда СНЭ1
        soc2_before = self.data_from_sql['F69'][0] / 10  # последнее на данную минуту значение уровня заряда СНЭ2
        return [soc1_before, soc2_before]

    def get_forecasts(self):
        load_fcst = forecasters.Load_forecaster(self.load_files).get_hourly_forecast()
        self_consumption_fcst = forecasters.Load_forecaster(self.load_files).self_consumption_forecast()
        total_load_fcst = load_fcst.values + self_consumption_fcst['Собственные нужды'].values
        pv_fcst = forecasters.PV_forecaster(self.pv_files2).get_pv_forecast()
        pv_fcst = (pv_fcst/1000).values.reshape(24, 1)
        pv_fcst[pv_fcst < 0] = 0

        return total_load_fcst, pv_fcst, self_consumption_fcst, load_fcst




#точка входа
#data_importer = Data_Importer()
#db_data = db_readeru.DB_connector().db_to_pd(240)[0]

#print(db_data['F68'][0])

#total_load = data_importer.get_forecasts()[0][:, 0]
#pv_fcst = data_importer.get_forecasts()[1][:, 0]
#dgu_states = data_importer.eq_status()[1]

#equipment_availa = data_importer.eq_status()[0]

#print(dgu_states)


class Problemah:

    def __init__(self, total_load, pv_fcst, dgu_states, equipment_availa, db_data, parameters):
        # задаем фиксированные исходные данные

        # горизонт прогнозирования/оптимизации
        self.T1 = 0
        self.T2 = 24

        #
        self.total_load = total_load
        self.pv_fcst = pv_fcst
        self.dgu_states = dgu_states
        self.equipment_availa = equipment_availa
        self.db_data = db_data
        self.parameters = parameters #параметры режима ДГУ и СНЭ - принудительный и обычный


        # ДГУ
        self.DGU_quantity = 4  # количество ДГУ
        self.DGU1_P_nom = float(re.findall(r"\d+", str(self.parameters[11]))[1])  # номинальная или доступная мощность ДГУ1, кВт
        self.DGU2_P_nom = float(re.findall(r"\d+", str(self.parameters[12]))[1])  # номинальная или доступная мощность ДГУ2, кВт
        self.DGU3_P_nom = float(re.findall(r"\d+", str(self.parameters[13]))[1])  # номинальная или доступная мощность ДГУ3, кВт
        self.DGU4_P_nom = float(re.findall(r"\d+", str(self.parameters[14]))[1])  # номинальная или доступная мощность ДГУ4, кВт
        self.DGU1_P_min = float(re.findall("\d+\.\d+", str(self.parameters[15]))[0]) * self.DGU1_P_nom  # минимальная мощность ДГУ1, кВт
        self.DGU2_P_min = float(re.findall("\d+\.\d+", str(self.parameters[16]))[0]) * self.DGU2_P_nom  # минимальная мощность ДГУ2, кВт
        self.DGU3_P_min = float(re.findall("\d+\.\d+", str(self.parameters[17]))[0]) * self.DGU3_P_nom  # минимальная мощность ДГУ3, кВт
        self.DGU4_P_min = float(re.findall("\d+\.\d+", str(self.parameters[18]))[0]) * self.DGU4_P_nom  # минимальная мощность ДГУ4, кВт
        self.DGU1_F_a = 0.0219  # коэффициент расходной характеристики ДГУ1
        self.DGU2_F_a = 0.0219  # коэффициент расходной характеристики ДГУ2
        self.DGU3_F_a = 0.0491  # коэффициент расходной характеристики ДГУ3
        self.DGU4_F_a = 0.0491  # коэффициент расходной характеристики ДГУ4
        self.DGU1_F_b = 0.3031  # коэффициент расходной характеристики ДГУ1
        self.DGU2_F_b = 0.3331  # коэффициент расходной характеристики ДГУ2
        self.DGU3_F_b = 0.2788  # коэффициент расходной характеристики ДГУ3
        self.DGU4_F_b = 0.2988  # коэффициент расходной характеристики ДГУ4

        self.DGU1_startup_cost = 1000  # затраты на один холодный пуск ДГУ1, у.е.
        self.DGU2_startup_cost = 1000  # затраты на один холодный пуск ДГУ2, у.е.
        self.DGU3_startup_cost = 1200  # затраты на один холодный пуск ДГУ3, у.е.
        self.DGU4_startup_cost = 1200  # затраты на один холодный пуск ДГУ4, у.е.
        self.DGU1_shutdown_cost = 1100  # затраты на остановку ДГУ1, у.е.
        self.DGU2_shutdown_cost = 1100  # затраты на остановку ДГУ2, у.е.
        self.DGU3_shutdown_cost = 1300  # затраты на остановку ДГУ3, у.е.
        self.DGU4_shutdown_cost = 1300  # затраты на остановку ДГУ4, у.е.

        # минимальное допустимое число последовательных часов работы ДГУ, ч
        self.DGU1_min_up_time = 3
        self.DGU2_min_up_time = 3
        self.DGU3_min_up_time = 3
        self.DGU4_min_up_time = 3

        # минимальное допустимое число последовательных часов простоя ДГУ, ч
        self.DGU1_min_down_time = 3
        self.DGU2_min_down_time = 3
        self.DGU3_min_down_time = 3
        self.DGU4_min_down_time = 3

        self.Fuel_price = 72  # руб/л

        # СЭС
        self.PV_inv_P_nom = 136  # номинальная единичная активная мощность инверторов СЭС, кВт
        self.PV_inv_P_fcst = self.pv_fcst

        # СНЭ
        self.ESS_inv_P_nom = 150  # номинальная единичная активная мощность инверторов СНЭ, кВт
        self.battery1_dod = float(re.findall(r"\d+", str(self.parameters[19]))[1]) #40  # глубина разряда массива АКБ 1, %
        self.battery2_dod = float(re.findall(r"\d+", str(self.parameters[20]))[1]) #40 глубина разряда массива АКБ 2, %
        # настраиваемый уровень заряда СНЭ на конец расчетного периода (если нужно зарядить/разрядить АКБ принудительно)
        self.soc1_after = self.db_data['F68'][0]/10 # 80
        self.soc2_after = self.db_data['F69'][0]/10 # 80

        # объект Concrete-модели Pyomo
        self.m = pyo.ConcreteModel()
        self.m.DGU = pyo.Set(initialize=np.array([n for n in range(0, self.DGU_quantity)]))  # набор ДГУ
        self.m.T = pyo.Set(
            initialize=np.array([t for t in range(self.T1, self.T2)]))  # набор часов в горизонте прогнозирования


        # определение наборов искомых переменных
        self.m.x1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU1_P_nom))  # мощность ДГУ 1
        self.m.u1 = pyo.Var(self.m.T, domain=pyo.Binary)  # бинарный статус ДГУ1
        #self.m.s1 = pyo.Var(self.m.T, domain=pyo.Binary)

        self.m.x2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU2_P_nom))  # мощность ДГУ 2
        self.m.u2 = pyo.Var(self.m.T, domain=pyo.Binary)  # бинарный статус ДГУ2
        #self.m.s2 = pyo.Var(self.m.T, domain=pyo.Binary)

        self.m.x3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU3_P_nom))  # мощность ДГУ 3
        self.m.u3 = pyo.Var(self.m.T, domain=pyo.Binary)  # бинарный статус ДГУ3
        #self.m.s3 = pyo.Var(self.m.T, domain=pyo.Binary)

        self.m.x4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU4_P_nom))  # мощность ДГУ 4
        self.m.u4 = pyo.Var(self.m.T, domain=pyo.Binary)  # бинарный статус ДГУ2
        #self.m.s4 = pyo.Var(self.m.T, domain=pyo.Binary)

        self.m.bat1_dch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.ESS_inv_P_nom))  # разряд СНЭ 1
        self.m.bat1_ch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.ESS_inv_P_nom))  # разряд СНЭ 1

        self.m.bat2_dch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.ESS_inv_P_nom))  # разряд СНЭ 2
        self.m.bat2_ch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.ESS_inv_P_nom))  # заряд СНЭ 2

        self.m.soc1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(self.battery1_dod, 100))  # глубина разряда
        self.m.soc2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(self.battery2_dod, 100))  # глубина разряда

        # затраты на пуск и останов ДГУ
        self.m.suc1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU1_startup_cost))
        self.m.suc2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU2_startup_cost))
        self.m.suc3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU3_startup_cost))
        self.m.suc4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU4_startup_cost))

        self.m.sdc1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU1_shutdown_cost))
        self.m.sdc2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU2_shutdown_cost))
        self.m.sdc3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU3_shutdown_cost))
        self.m.sdc4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.DGU4_shutdown_cost))

        # наборы мощностей инверторов СЭС
        self.m.PV1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))
        self.m.PV2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))
        self.m.PV3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))
        self.m.PV4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))
        self.m.PV5 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))
        self.m.PV6 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))
        self.m.PV7 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds=(0, self.PV_inv_P_nom))

        self.m.PV1_u = pyo.Var(self.m.T, domain=pyo.Binary)
        self.m.PV2_u = pyo.Var(self.m.T, domain=pyo.Binary)
        self.m.PV3_u = pyo.Var(self.m.T, domain=pyo.Binary)
        self.m.PV4_u = pyo.Var(self.m.T, domain=pyo.Binary)
        self.m.PV5_u = pyo.Var(self.m.T, domain=pyo.Binary)
        self.m.PV6_u = pyo.Var(self.m.T, domain=pyo.Binary)
        self.m.PV7_u = pyo.Var(self.m.T, domain=pyo.Binary)

        # целевая функция, которую мы минимизируем
        self.m.objective_fun = pyo.Objective(expr=sum(self.Fuel_price * (
                (self.DGU1_F_a * self.DGU1_P_nom * self.m.u1[t] + self.DGU1_F_b * self.m.x1[t]) +
                (self.DGU2_F_a * self.DGU2_P_nom * self.m.u2[t] + self.DGU2_F_b * self.m.x2[t]) +
                (self.DGU3_F_a * self.DGU3_P_nom * self.m.u3[t] + self.DGU3_F_b * self.m.x3[t]) +
                (self.DGU4_F_a * self.DGU4_P_nom * self.m.u4[t] + self.DGU4_F_b * self.m.x4[t])) +
                                                      self.m.suc1[t] + self.m.suc2[t] + self.m.suc3[t] + self.m.suc4[
                                                         t] + self.m.sdc1[t] +
                                                      self.m.sdc2[t] + self.m.sdc3[t] + self.m.sdc4[t] +
                                                      self.m.u1[t]*100 + self.m.u2[t]*100 + self.m.u3[t]*100 + self.m.u4[t]*100 +
                                                      27432 * 0.000033 * (self.m.bat1_ch[t] + self.m.bat1_dch[t]) + 27432 * 0.000033 * (
                                                      self.m.bat2_ch[t] + self.m.bat2_dch[t])
                                                      for t in self.m.T), sense=pyo.minimize)

        # включение в модель ограничений
        self.m.power_balance = pyo.Constraint(self.m.T, rule=self.cnstr_balance)  # баланс мощности

        # # пределы допустимых мощностей ДГУ
        self.m.lb1 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU1_P_min * m.u1[t] <= m.x1[t])
        self.m.ub1 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU1_P_min * m.u1[t] >= m.x1[t])
        self.m.lb2 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU2_P_min * m.u2[t] <= m.x2[t])
        self.m.ub2 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU2_P_min * m.u2[t] >= m.x2[t])
        self.m.lb3 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU3_P_min * m.u3[t] <= m.x3[t])
        self.m.ub3 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU3_P_min * m.u3[t] >= m.x3[t])
        self.m.lb4 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU4_P_min * m.u4[t] <= m.x4[t])
        self.m.ub4 = pyo.Constraint(self.m.T, rule=lambda m, t: self.DGU4_P_min * m.u4[t] >= m.x4[t])

        # # пределы ограничения мощности инверторов СЭС
        self.m.pv1_curtailment = pyo.Constraint(self.m.T, rule=self.cnstr_curtailment_control1)
        self.m.pv2_curtailment = pyo.Constraint(self.m.T, rule=self.cnstr_curtailment_control2)

        # # минимальное число последовательных часов работы ДГУ
        # # # ДГУ 1
        if self.parameters[3] == 'DGU1_min_up_time=3':
            self.m.DGU1_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_min_up_time)
        elif self.parameters[3] == 'DGU1_min_up_time=2':
            self.m.DGU1_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_min_up_time_2)
        # # # ДГУ 2
        if self.parameters[5] == 'DGU2_min_up_time=3':
            self.m.DGU2_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_min_up_time)
        elif self.parameters[5] == 'DGU2_min_up_time=2':
            self.m.DGU2_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_min_up_time_2)
        # # # ДГУ 3
        if self.parameters[7] == 'DGU3_min_up_time=3':
            self.m.DGU3_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_min_up_time)
        elif self.parameters[7] == 'DGU3_min_up_time=2':
            self.m.DGU3_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_min_up_time_2)
        # # # ДГУ 4
        if self.parameters[9] == 'DGU4_min_up_time=3':
            self.m.DGU4_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_min_up_time)
        elif self.parameters[9] == 'DGU4_min_up_time=2':
            self.m.DGU4_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_min_up_time_2)

        # # минимальное число последовательных часов простоя ДГУ
        # # # ДГУ 1
        if self.parameters[4] == 'DGU1_min_down_time=3':
            self.m.DGU1_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_min_down_time)
        elif self.parameters[4] == 'DGU1_min_down_time=2':
            self.m.DGU1_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_min_down_time_2)
        # # # ДГУ 2
        if self.parameters[6] == 'DGU2_min_down_time=3':
            self.m.DGU2_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_min_down_time)
        elif self.parameters[6] == 'DGU2_min_down_time=2':
            self.m.DGU1_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_min_down_time_2)
        # # # ДГУ 3
        if self.parameters[8] == 'DGU3_min_down_time=3':
            self.m.DGU3_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_min_down_time)
        elif self.parameters[8] == 'DGU3_min_down_time=2':
            self.m.DGU3_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_min_down_time_2)
        # # # ДГУ 4
        if self.parameters[10] == 'DGU4_min_down_time=3':
            self.m.DGU4_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_min_down_time)
        elif self.parameters[10] == 'DGU4_min_down_time=2':
            self.m.DGU4_min_up_time = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_min_down_time_2)


        #принудительная работа ДГУ
        if self.parameters[0] == 'DGU_forced_mode=1':
            self.m.DGU_forced_on = pyo.Constraint(self.m.T, rule=self.DGU_forced)

        # # ограничения затрат на запуск ДГУ
        self.m.su1 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_start_up_cost)
        self.m.su2 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_start_up_cost)
        self.m.su3 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_start_up_cost)
        self.m.su4 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_start_up_cost)
        # # ограничения затрат на останов ДГУ
        self.m.sd1 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_shut_down_cost)
        self.m.sd2 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_shut_down_cost)
        self.m.sd3 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_shut_down_cost)
        self.m.sd4 = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_shut_down_cost)

        # # ограничение доступности ДГУ
        self.m.DGU1_ava = pyo.Constraint(self.m.T, rule=self.cnstr_dgu1_availability)
        self.m.DGU2_ava = pyo.Constraint(self.m.T, rule=self.cnstr_dgu2_availability)
        self.m.DGU3_ava = pyo.Constraint(self.m.T, rule=self.cnstr_dgu3_availability)
        self.m.DGU4_ava = pyo.Constraint(self.m.T, rule=self.cnstr_dgu4_availability)

        # # ограничение уровня заряда СНЭ в допустимых пределах
        self.m.soc1_ctrl = pyo.Constraint(self.m.T, rule=self.cnstr_soc1_ctrl)
        self.m.soc2_ctrl = pyo.Constraint(self.m.T, rule=self.cnstr_soc2_ctrl)

        # # ограничение, запрещающее одновременный заряд и разряд СНЭ
        self.m.chdch1 = pyo.Constraint(self.m.T, rule=self.cnstr_ch_x_dch1)
        self.m.chdch2 = pyo.Constraint(self.m.T, rule=self.cnstr_ch_x_dch2)

        # # ограничение доступности СНЭ
        self.m.ess1_ava = pyo.Constraint(self.m.T, rule=self.cnstr_ess1_availability)
        self.m.ess2_ava = pyo.Constraint(self.m.T, rule=self.cnstr_ess2_availability)

        # # ограничение синхронной работы СНЭ
        self.m.ess_as_one1 = pyo.Constraint(self.m.T, rule=self.cnstr_ess_as_one1)
        self.m.ess_as_one2 = pyo.Constraint(self.m.T, rule=self.cnstr_ess_as_one2)

        # # ограничение на равенство уровней заряда СНЭ в начале и в конце расчетного периода
        if self.parameters[2] == 'SOC_forced_cycle=1':
            self.m.ess_cycled1 = pyo.Constraint(self.m.T, rule=self.cnstr_ess_cycle1)
            self.m.ess_cycled2 = pyo.Constraint(self.m.T, rule=self.cnstr_ess_cycle2)

        # # пределы допустимых мощностей инверторов СЭС
        self.m.pv1 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV1[t] <= self.PV_inv_P_fcst[t]/7) #PV_inv_P_nom
        self.m.pv2 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV2[t] <= self.PV_inv_P_fcst[t]/7)
        self.m.pv3 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV3[t] <= self.PV_inv_P_fcst[t]/7)
        self.m.pv4 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV4[t] <= self.PV_inv_P_fcst[t]/7)
        self.m.pv5 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV5[t] <= self.PV_inv_P_fcst[t]/7)
        self.m.pv6 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV6[t] <= self.PV_inv_P_fcst[t]/7)
        self.m.pv7 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV7[t] <= self.PV_inv_P_fcst[t]/7)

        # статусы оборудования (из SQL)
        self.equipment_availa = equipment_availa[0]  # доступность оборудования
        self.dgu_states = equipment_availa[1]  # доступность оборудования

        # получение прогнозных данных при инициализации
        #self.data_importer = Data_Importer()
        #self.total_load = self.data_importer.get_forecasts()[0][:, 0]
        #self.pv_prod =  self.data_importer.get_forecasts()[1][:, 0]

    # функциональные формулировки ограничений

    def cnstr_balance(self, m,  i):
        return self.m.x1[i] + self.m.x2[i] + self.m.x3[i] + self.m.x4[i] + \
               self.m.bat1_dch[i] - self.m.bat1_ch[i] + self.m.bat2_dch[i] - self.m.bat2_ch[i] + \
               self.m.PV1[i] * self.m.PV1_u[i] + self.m.PV2[i] * self.m.PV2_u[i] + \
               self.m.PV3[i] * self.m.PV3_u[i] + self.m.PV4[i] * self.m.PV4_u[i] + \
               self.m.PV5[i] * self.m.PV5_u[i] + self.m.PV6[i] * self.m.PV6_u[i] + \
               self.m.PV7[i] * self.m.PV7_u[i] == self.total_load[i]

    def cnstr_dgu1_start_up_cost(self, m, i):
        if i == self.T1:
            return self.m.suc1[i] >= self.DGU1_startup_cost * (self.m.u1[i] - self.dgu_states[0][-1])
        else:
            return self.m.suc1[i] >= self.DGU1_startup_cost * (self.m.u1[i] - self.m.u1[i - 1])

    def cnstr_dgu2_start_up_cost(self, m, i):
        if i == self.T1:
            return self.m.suc2[i] >= self.DGU2_startup_cost * (self.m.u2[i] - self.dgu_states[1][-1])
        else:
            return self.m.suc2[i] >= self.DGU2_startup_cost * (self.m.u2[i] - self.m.u2[i - 1])

    def cnstr_dgu3_start_up_cost(self, m, i):
        if i == self.T1:
            return self.m.suc3[i] >= self.DGU3_startup_cost * (self.m.u3[i] - self.dgu_states[2][-1])
        else:
            return self.m.suc3[i] >= self.DGU3_startup_cost * (self.m.u3[i] - self.m.u3[i - 1])

    def cnstr_dgu4_start_up_cost(self, m, i):
        if i == self.T1:
            return self.m.suc4[i] >= self.DGU4_startup_cost * (self.m.u4[i] - self.dgu_states[3][-1])
        else:
            return self.m.suc4[i] >= self.DGU4_startup_cost * (self.m.u4[i] - self.m.u4[i - 1])

    def cnstr_dgu1_shut_down_cost(self, m, i):
        if i == self.T1:
            return m.sdc1[i] >= self.DGU1_shutdown_cost * (self.dgu_states[0][-1] - m.u1[i])
        else:
            return m.sdc1[i] >= self.DGU1_shutdown_cost * (m.u1[i - 1] - m.u1[i])

    def cnstr_dgu2_shut_down_cost(self, m, i):
        if i == self.T1:
            return m.sdc2[i] >= self.DGU2_shutdown_cost * (self.dgu_states[1][-1] - m.u2[i])
        else:
            return m.sdc2[i] >= self.DGU2_shutdown_cost * (m.u2[i - 1] - m.u2[i])

    def cnstr_dgu3_shut_down_cost(self, m, i):
        if i == self.T1:
            return m.sdc3[i] >= self.DGU3_shutdown_cost * (self.dgu_states[2][-1] - m.u3[i])
        else:
            return m.sdc3[i] >= self.DGU3_shutdown_cost * (m.u3[i - 1] - m.u3[i])

    def cnstr_dgu4_shut_down_cost(self, m, i):
        if i == self.T1:
            return m.sdc4[i] >= self.DGU4_shutdown_cost * (self.dgu_states[3][-1] - m.u4[i])
        else:
            return m.sdc4[i] >= self.DGU4_shutdown_cost * (m.u4[i - 1] - m.u4[i])

    def cnstr_curtailment_control1 (self, m, i):
        return self.m.PV1[i]+ self.m.PV2[i]+self.m.PV3[i]+self.m.PV4[i]+self.m.PV5[i]+self.m.PV6[i]+self.m.PV7[i] - \
               self.pv_fcst[i] - self.m.bat1_ch[i]/self.ESS_inv_P_nom <= 0

    def cnstr_curtailment_control2 (self, m, i):
        return self.m.PV1[i]+ self.m.PV2[i]+self.m.PV3[i]+self.m.PV4[i]+self.m.PV5[i]+self.m.PV6[i]+self.m.PV7[i] - \
               self.pv_fcst[i] - self.m.bat2_ch[i]/self.ESS_inv_P_nom <= 0

    # 3-ЧАСОВАЯ РАБОТА
    @simple_constraint_rule
    def cnstr_dgu1_min_up_time(self, m, i):
        if i == self.T1:
            return (self.dgu_states[0][2] + self.dgu_states[0][1] + self.dgu_states[0][0] - self.DGU1_min_up_time) * (
                    self.dgu_states[0][-1] - m.u1[i]) >= 0
        if i == self.T1 + 1:
            # if d1_past_up_statuses[0] == 0 and d1_past_up_statuses[1] == 0:
            # return ((d1_past_up_statuses[2] + d1_past_up_statuses[1] + m.u1[i-1] - d1_min_up_time)*(m.u1[i-1] - m.u1[i])) >= 0
            # else:
            # return ((d1_past_up_statuses[2] + d1_past_up_statuses[1] + m.u1[i-1] - d1_min_up_time)*(m.u1[i-1] - m.u1[i]) - m.u1[i]) >= 0
            return (self.dgu_states[0][2] + self.dgu_states[0][1] + m.u1[i - 1] - self.DGU1_min_up_time) * (
                        m.u1[i - 1] - m.u1[i]) >= 0
        if i == self.T1 + 2:
            return (self.dgu_states[0][2] + m.u1[i - 2] + m.u1[i - 1] - self.DGU1_min_up_time) * (m.u1[i - 1] - m.u1[i]) >= 0
        # elif T1 < i <= T1+2:
        #    uj = []
        #    #uj.append(m.u1[i-1])
        #    for j in range(T1, i):
        #        uj.append(m.u1[j])
        #    return ((sum(uj) - d1_min_up_time)*(m.u1[i-1] - m.u1[i])) >= 0
        else:
            return (m.u1[i - 1] + m.u1[i - 2] + m.u1[i - 3] - self.DGU1_min_up_time) * (m.u1[i - 1] - m.u1[i]) >= 0

    @simple_constraint_rule
    def cnstr_dgu2_min_up_time(self, m, i):
        if i == self.T1:
            return (self.dgu_states[1][2] + self.dgu_states[1][1] + self.dgu_states[1][0] - self.DGU2_min_up_time) * (
                        self.dgu_states[1][-1] - m.u2[i]) >= 0
        if i == self.T1 + 1:
            return (self.dgu_states[1][2] + self.dgu_states[1][1] + m.u2[i - 1] - self.DGU2_min_up_time) * (
                        m.u2[i - 1] - m.u2[i]) >= 0
        if i == self.T1 + 2:
            return (self.dgu_states[1][2] + m.u2[i - 2] + m.u2[i - 1] - self.DGU2_min_up_time) * (m.u2[i - 1] - m.u2[i]) >= 0
        else:
            return (m.u2[i - 1] + m.u2[i - 2] + m.u2[i - 3] - self.DGU2_min_up_time) * (m.u2[i - 1] - m.u2[i]) >= 0

    @simple_constraint_rule
    def cnstr_dgu3_min_up_time(self, m, i):
        if i == self.T1:
            return (self.dgu_states[2][2] + self.dgu_states[2][1] + self.dgu_states[2][0] -
                    self.DGU3_min_up_time) * (
                           self.dgu_states[2][-1] - m.u3[i]) >= 0
        if i == self.T1 + 1:
            return (self.dgu_states[2][2] + self.dgu_states[2][1] + m.u3[i - 1] - self.DGU3_min_up_time) * (
                    m.u3[i - 1] - m.u3[i]) >= 0
        if i == self.T1 + 2:
            return (self.dgu_states[2][2] + m.u3[i - 2] + m.u3[i - 1] - self.DGU3_min_up_time) * (
                        m.u3[i - 1] - m.u3[i]) >= 0
        else:
            return (m.u3[i - 1] + m.u3[i - 2] + m.u3[i - 3] - self.DGU3_min_up_time) * (m.u3[i - 1] - m.u3[i]) >= 0

    @simple_constraint_rule
    def cnstr_dgu4_min_up_time(self, m, i):
        if i == self.T1:
            return (self.dgu_states[3][2] + self.dgu_states[3][1] + self.dgu_states[3][0] -
                    self.DGU4_min_up_time) * (
                           self.dgu_states[3][-1] - m.u4[i]) >= 0
        if i == self.T1 + 1:
            return (self.dgu_states[3][2] + self.dgu_states[3][1] + m.u4[i - 1] - self.DGU4_min_up_time) * (
                    m.u2[i - 1] - m.u4[i]) >= 0
        if i == self.T1 + 2:
            return (self.dgu_states[3][2] + m.u4[i - 2] + m.u4[i - 1] - self.DGU4_min_up_time) * (
                    m.u4[i - 1] - m.u4[i]) >= 0
        else:
            return (m.u4[i - 1] + m.u4[i - 2] + m.u4[i - 3] - self.DGU4_min_up_time) * (m.u4[i - 1] - m.u4[i]) >= 0

    # 2-ЧАСОВАЯ РАБОТА
    @simple_constraint_rule
    def cnstr_dgu1_min_up_time_2(self, m, i):
        if i == self.T1:
            return (self.dgu_states[0][2] + self.dgu_states[0][1] - 2) * (
                           self.dgu_states[0][-1] - m.u1[i]) >= 0
        if i == self.T1 + 1:
            # if d1_past_up_statuses[0] == 0 and d1_past_up_statuses[1] == 0:
            # return ((d1_past_up_statuses[2] + d1_past_up_statuses[1] + m.u1[i-1] - d1_min_up_time)*(m.u1[i-1] - m.u1[i])) >= 0
            # else:
            # return ((d1_past_up_statuses[2] + d1_past_up_statuses[1] + m.u1[i-1] - d1_min_up_time)*(m.u1[i-1] - m.u1[i]) - m.u1[i]) >= 0
            return (self.dgu_states[0][2] + m.u1[i - 1] - 2) * (
                    m.u1[i - 1] - m.u1[i]) >= 0
        # if i == self.T1 + 2:
        #     return (self.dgu_states[0][2] + m.u1[i - 2] + m.u1[i - 1] - self.DGU1_min_up_time) * (
        #                 m.u1[i - 1] - m.u1[i]) >= 0
        # elif T1 < i <= T1+2:
        #    uj = []
        #    #uj.append(m.u1[i-1])
        #    for j in range(T1, i):
        #        uj.append(m.u1[j])
        #    return ((sum(uj) - d1_min_up_time)*(m.u1[i-1] - m.u1[i])) >= 0
        else:
            return (m.u1[i - 1] + m.u1[i - 2]  - 2) * (m.u1[i - 1] - m.u1[i]) >= 0

    @simple_constraint_rule
    def cnstr_dgu2_min_up_time_2(self, m, i):
        if i == self.T1:
            return (self.dgu_states[1][2] + self.dgu_states[1][1] - 2) * (
                           self.dgu_states[1][-1] - m.u2[i]) >= 0
        if i == self.T1 + 1:
            return (self.dgu_states[1][2] + m.u2[i - 1] - 2) * (
                    m.u2[i - 1] - m.u2[i]) >= 0
        # if i == self.T1 + 2:
        #     return (self.dgu_states[1][2] + m.u2[i - 2] + m.u2[i - 1] - self.DGU2_min_up_time) * (
        #                 m.u2[i - 1] - m.u2[i]) >= 0
        else:
            return (m.u2[i - 1] + m.u2[i - 2] - 2) * (m.u2[i - 1] - m.u2[i]) >= 0

    @simple_constraint_rule
    def cnstr_dgu3_min_up_time_2(self, m, i):
        if i == self.T1:
            return (self.dgu_states[2][2] + self.dgu_states[2][1] - 2) * (
                           self.dgu_states[2][-1] - m.u3[i]) >= 0
        if i == self.T1 + 1:
            return (self.dgu_states[2][2] + m.u3[i - 1] - 2) * (
                    m.u3[i - 1] - m.u3[i]) >= 0
        # if i == self.T1 + 2:
        #     return (self.dgu_states[2][2] + m.u3[i - 2] + m.u3[i - 1] - self.DGU3_min_up_time) * (
        #             m.u3[i - 1] - m.u3[i]) >= 0
        else:
            return (m.u3[i - 1] + m.u3[i - 2] - 2) * (m.u3[i - 1] - m.u3[i]) >= 0

    @simple_constraint_rule
    def cnstr_dgu4_min_up_time_2(self, m, i):
        if i == self.T1:
            return (self.dgu_states[3][2] + self.dgu_states[3][1] -
                    2) * (
                           self.dgu_states[3][-1] - m.u4[i]) >= 0
        if i == self.T1 + 1:
            return (self.dgu_states[3][2] + m.u4[i - 1] - 2) * (
                    m.u2[i - 1] - m.u4[i]) >= 0
        # if i == self.T1 + 2:
        #     return (self.dgu_states[3][2] + m.u4[i - 2] + m.u4[i - 1] - self.DGU4_min_up_time) * (
        #             m.u4[i - 1] - m.u4[i]) >= 0
        else:
            return (m.u4[i - 1] + m.u4[i - 2] - 2) * (m.u4[i - 1] - m.u4[i]) >= 0

    # 3-ЧАСОВОЙ ПРОСТОЙ
    @simple_constraint_rule
    def cnstr_dgu1_min_down_time(self, m, i):
        if i == self.T1:
            return (-(1-self.dgu_states[0][2] + 1-self.dgu_states[0][1] + 1-self.dgu_states[0][0])
                    + self.DGU1_min_down_time) * (-self.dgu_states[0][2] + m.u1[i]) <= 0
        if i == self.T1 + 1:
            return (-(1-self.dgu_states[0][2] + 1-self.dgu_states[0][1] + (1 - m.u1[i - 1])) + self.DGU1_min_down_time) * (
                        -m.u1[i - 1] + m.u1[i]) <= 0
        if i == self.T1 + 2:
            return (-(1-self.dgu_states[0][2] + (1 - m.u1[i - 2]) + (1 - m.u1[i - 1])) + self.DGU1_min_down_time) * (
                        -m.u1[i - 1] + m.u1[i]) <= 0
        # elif i <= T1+2:
        #    uj = []
        #    uj.append(m.u1[i-1])
        #    for j in range(T1, i):
        #        uj.append(m.u1[j])
        #    return ((sum(uj) - 2 + d1_min_down_time)*(-m.u1[i-1] + m.u1[i])) <= 0
        else:
            return (-(1 - m.u1[i - 1] + 1 - m.u1[i - 2] + 1 - m.u1[i - 3]) + self.DGU1_min_down_time) * (
                        -m.u1[i - 1] + m.u1[i]) <= 0

    @simple_constraint_rule
    def cnstr_dgu2_min_down_time(self, m, i):
        if i == self.T1:
            return (-(1-self.dgu_states[1][2] + 1-self.dgu_states[1][1] + 1-self.dgu_states[1][0]) +
                    self.DGU2_min_down_time) * (-self.dgu_states[1][2] + m.u2[i]) <= 0
        if i == self.T1 + 1:
            return (-(1-self.dgu_states[1][2] + 1-self.dgu_states[1][1] + (1 - m.u2[i - 1])) + self.DGU2_min_down_time) * (
                        -m.u2[i - 1] + m.u2[i]) <= 0
        if i == self.T1 + 2:
            return (-(1-self.dgu_states[1][2] + (1 - m.u2[i - 2]) + (1 - m.u2[i - 1])) + self.DGU2_min_down_time) * (
                        -m.u2[i - 1] + m.u2[i]) <= 0
        else:
            return (-(1 - m.u2[i - 1] + 1 - m.u2[i - 2] + 1 - m.u2[i - 3]) + self.DGU2_min_down_time) * (
                        -m.u2[i - 1] + m.u2[i]) <= 0

    @simple_constraint_rule
    def cnstr_dgu3_min_down_time(self, m, i):
        if i == self.T1:
            return (-(1-self.dgu_states[2][2] + 1-self.dgu_states[2][1] + 1-self.dgu_states[2][0]) +
                    self.DGU3_min_down_time) * (-self.dgu_states[2][2] + m.u3[i]) <= 0
        if i == self.T1 + 1:
            return (-(1-self.dgu_states[2][2] + 1-self.dgu_states[2][1] + (1 - m.u3[i - 1])) + self.DGU3_min_down_time) * (
                        -m.u3[i - 1] + m.u3[i]) <= 0
        if i == self.T1 + 2:
            return (-(1-self.dgu_states[2][2] + (1 - m.u3[i - 2]) + (1 - m.u3[i - 1])) + self.DGU3_min_down_time) * (
                        -m.u3[i - 1] + m.u3[i]) <= 0
        else:
            return (-(1 - m.u3[i - 1] + 1 - m.u3[i - 2] + 1 - m.u3[i - 3]) + self.DGU3_min_down_time) * (
                        -m.u3[i - 1] + m.u3[i]) <= 0

    @simple_constraint_rule
    def cnstr_dgu4_min_down_time(self, m, i):
        if i == self.T1:
            return (-(1-self.dgu_states[3][2] + 1-self.dgu_states[3][1] + 1-self.dgu_states[3][0]) +
                    self.DGU4_min_down_time) * (-self.dgu_states[3][2] + m.u4[i]) <= 0
        if i == self.T1 + 1:
            return (-(1-self.dgu_states[3][2] + 1-self.dgu_states[3][1] + (1 - m.u4[i - 1])) + self.DGU4_min_down_time) * (
                        -m.u4[i - 1] + m.u4[i]) <= 0
        if i == self.T1 + 2:
            return (-(1-self.dgu_states[3][2] + (1 - m.u4[i - 2]) + (1 - m.u4[i - 1])) + self.DGU4_min_down_time) * (
                        -m.u4[i - 1] + m.u4[i]) <= 0
        else:
            return (-(1 - m.u4[i - 1] + 1 - m.u4[i - 2] + 1 - m.u4[i - 3]) + self.DGU4_min_down_time) * (
                        -m.u4[i - 1] + m.u4[i]) <= 0

    # 2-ЧАСОВОЙ ПРОСТОЙ
    @simple_constraint_rule
    def cnstr_dgu1_min_down_time_2(self, m, i):
        if i == self.T1:
            return (-(self.dgu_states[0][2] + self.dgu_states[0][1])
                    + 2) * (-self.dgu_states[0][2] + m.u1[i]) <= 0
        if i == self.T1 + 1:
            return (-(self.dgu_states[0][2] +(
                        1 - m.u1[i - 1])) + 2) * (
                           -m.u1[i - 1] + m.u1[i]) <= 0
        # if i == self.T1 + 2:
        #     return (-(1 - self.dgu_states[0][2] + (1 - m.u1[i - 2]) + (
        #                 1 - m.u1[i - 1])) + self.DGU1_min_down_time) * (
        #                    -m.u1[i - 1] + m.u1[i]) <= 0
        # elif i <= T1+2:
        #    uj = []
        #    uj.append(m.u1[i-1])
        #    for j in range(T1, i):
        #        uj.append(m.u1[j])
        #    return ((sum(uj) - 2 + d1_min_down_time)*(-m.u1[i-1] + m.u1[i])) <= 0
        else:
            return (-(1 - m.u1[i - 1] + 1 - m.u1[i - 2]) + 2) * (
                    -m.u1[i - 1] + m.u1[i]) <= 0

    @simple_constraint_rule
    def cnstr_dgu2_min_down_time_2(self, m, i):
        if i == self.T1:
            return (-(self.dgu_states[1][2] + self.dgu_states[1][1]) +
                    2) * (-self.dgu_states[1][2] + m.u2[i]) <= 0
        if i == self.T1 + 1:
            return (-(1 - self.dgu_states[1][2] + 1 - self.dgu_states[1][1] + (
                        1 - m.u2[i - 1])) + self.DGU2_min_down_time) * (
                           -m.u2[i - 1] + m.u2[i]) <= 0
        # if i == self.T1 + 2:
        #     return (-(1 - self.dgu_states[1][2] + (1 - m.u2[i - 2]) + (
        #                 1 - m.u2[i - 1])) + self.DGU2_min_down_time) * (
        #                    -m.u2[i - 1] + m.u2[i]) <= 0
        else:
            return (-(1 - m.u2[i - 1] + 1 - m.u2[i - 2]) + 2) * (
                    -m.u2[i - 1] + m.u2[i]) <= 0

    @simple_constraint_rule
    def cnstr_dgu3_min_down_time_2(self, m, i):
        if i == self.T1:
            return (-(self.dgu_states[2][2] + self.dgu_states[2][1]) +
                    2) * (-self.dgu_states[2][2] + m.u3[i]) <= 0
        if i == self.T1 + 1:
            return (-(self.dgu_states[2][2] + (
                        1 - m.u3[i - 1])) + 2) * (
                           -m.u3[i - 1] + m.u3[i]) <= 0
        # if i == self.T1 + 2:
        #     return (-(1 - self.dgu_states[2][2] + (1 - m.u3[i - 2]) + (
        #                 1 - m.u3[i - 1])) + self.DGU3_min_down_time) * (
        #                    -m.u3[i - 1] + m.u3[i]) <= 0
        else:
            return (-(1 - m.u3[i - 1] + 1 - m.u3[i - 2]) + 2) * (
                    -m.u3[i - 1] + m.u3[i]) <= 0

    @simple_constraint_rule
    def cnstr_dgu4_min_down_time_2(self, m, i):
        if i == self.T1:
            return (-(self.dgu_states[3][2] - self.dgu_states[3][1]) +
                    2) * (-self.dgu_states[3][2] + m.u4[i]) <= 0
        if i == self.T1 + 1:
            return (-(self.dgu_states[3][2] + (
                        1 - m.u4[i - 1])) + 2) * (
                           -m.u4[i - 1] + m.u4[i]) <= 0
        # if i == self.T1 + 2:
        #     return (-(1 - self.dgu_states[3][2] + (1 - m.u4[i - 2]) + (
        #                 1 - m.u4[i - 1])) + self.DGU4_min_down_time) * (
        #                    -m.u4[i - 1] + m.u4[i]) <= 0
        else:
            return (-(1 - m.u4[i - 1] + 1 - m.u4[i - 2]) + 2) * (
                    -m.u4[i - 1] + m.u4[i]) <= 0


    # Сюда позже нужно добавить ограничения по расписанию
    def cnstr_dgu1_availability(self, m, i):
        return self.m.u1[i] == self.m.u1[i] * self.equipment_availa[0][0]

    def cnstr_dgu2_availability(self, m, i):
        return self.m.u2[i] == self.m.u2[i] * self.equipment_availa[0][0]

    def cnstr_dgu3_availability(self, m, i):
        return self.m.u3[i] == self.m.u3[i] * self.equipment_availa[0][0]

    def cnstr_dgu4_availability(self, m, i):
        return self.m.u4[i] == self.m.u4[i] * self.equipment_availa[0][0]

    def DGU_forced(self, m, i):
        return m.u1[i] + m.u2[i] + m.u3[i] + m.u4[i] >= 1



    def cnstr_ess1_availability(self, m, i):
        return self.m.bat1_dch[i] + self.m.bat1_ch[i] == (self.m.bat1_dch[i] + self.m.bat1_ch[i]) * self.equipment_availa[2][0]

    def cnstr_ess2_availability(self, m, i):
        return self.m.bat2_dch[i] + self.m.bat2_ch[i] == (self.m.bat2_dch[i] + self.m.bat2_ch[i]) * self.equipment_availa[2][1]

    def cnstr_as_one1(self, m, i):
        return self.m.bat1_dch[i] == self.m.bat2_dch[i]

    def cnstr_as_one2(self, m, i):
        return self.m.bat1_ch[i] == self.m.bat2_ch[i]

    #ограничение глубины разряда СНЭ
    def cnstr_soc1_ctrl(self, m, i):
        if i == self.T1:
            return self.m.soc1[i] == self.db_data['F68'][0]/10 - 100*self.m.bat1_dch[i]/(0.95*0.9*700) + 0.9*100*self.m.bat1_ch[i]/700 #0.8 round trip efficiency 0.95 inverter efficiency
        else:
            return self.m.soc1[i] == self.m.soc1[i-1] - 100*self.m.bat1_dch[i]/(0.95*0.9*700) + 0.9*100*self.m.bat1_ch[i]/700 #0.8 round trip efficiency

    def cnstr_soc2_ctrl(self, m, i):
        if i == self.T1:
            return self.m.soc2[i] == self.db_data['F69'][0]/10 - 100*self.m.bat2_dch[i]/(0.95*0.9*700) + 0.9*100*self.m.bat2_ch[i]/700
        else:
            return self.m.soc2[i] == self.m.soc2[i-1] - 100*self.m.bat2_dch[i]/(0.95*0.9*700) + 0.9*100*self.m.bat2_ch[i]/700

    # СНЭ не должна заряжаться и разряжаться одновременно
    def cnstr_ch_x_dch1(self, m, i):
        return self.m.bat1_ch[i] * self.m.bat1_dch[i] == 0

    def cnstr_ch_x_dch2(self, m, i):
        return self.m.bat2_ch[i] * self.m.bat2_dch[i] == 0

    # одинаковый заряд/разряд СНЭ
    def cnstr_ess_as_one1(self, m, i):
        return self.m.bat1_dch[i] == self.m.bat2_dch[i]

    def cnstr_ess_as_one2(self, m, i):
        return self.m.bat1_ch[i] == self.m.bat2_ch[i]

    # условие одинакового уровня заряда СНЭ в начале и в конце расчетного периода
    def cnstr_ess_cycle1(self, m, i):
        return self.m.soc1[self.T2 - 1] >= self.soc1_after

    def cnstr_ess_cycle2(self, m, i):
        return self.m.soc2[self.T2 - 1] >= self.soc2_after



# entity = Problemah()

# conn = Data_Importer()

# print(total_load)

# print(pv_fcst)

# print(entity.m)

# entity.equipment_statuses = conn.eq_status()[0]

# print(conn.eq_status()[1][0])

# print(entity.equipment_statuses)

def optimizatione(model):


    # optimizer = pyo.SolverFactory('scipampl', executable=os.getcwd() + '\scipampl-7.0.0.win.x86_64.intel.opt.spx2')

    optimizer =  pyo.SolverFactory('couenne', executable=os.getcwd() +'\\couenne67.exe')

    results = optimizer.solve(model, logfile='optimizer_log.log', tee=True, timelimit=600,
                        keepfiles=True)
    results.write()

    return

#optimizatione(entity.m)



