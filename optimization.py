import formulation
import os
import pyomo.environ as pyo
import db_readeru
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys
import traceback
import multiprocessing
from pyomo.common.tempfiles import TempfileManager
import time


# игнорирование предупреждений. Потом нужно разобраться с каждым
import warnings
warnings.filterwarnings("ignore")

import logging


if not os.path.exists(os.getcwd()+"\\tempo"):
    os.makedirs(os.getcwd()+"\\tempo")

if not os.path.exists(os.getcwd()+"\\log"):
    os.makedirs(os.getcwd()+"\\log")
TempfileManager.tempdir = os.getcwd()+"\\tempo"

logging.basicConfig(filename='.\log\logging.log', level=logging.ERROR,
                                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger = logging.getLogger(__name__)

class DecisionSeeking:

    def __init__(self, db_data, total_load, pv_fcst, dgu_states, equipment_availa, datetime, solver):

        self.datetime = datetime #self.data_importer.get_forecasts()[3].index  # .strftime("%Y-%m-%d %H:%M:%S")
        self.db_data = db_data
        self.total_load = total_load
        self.pv_fcst = pv_fcst
        self.dgu_states = dgu_states
        self.equipment_availa = equipment_availa

        if solver == 'solver=1':
            self.optimizer = pyo.SolverFactory('couenne', executable=os.getcwd() + '\\couenne67.exe') #'\\couenne67.exe')

        else:
            self.optimizer = pyo.SolverFactory('scipampl', executable=os.getcwd() + '\scipampl-7.0.0.win.x86_64.intel.opt.spx2')

    # def get_latest_data(self):
    #
    #     datetime = self.data_importer.get_forecasts()[3].index #.strftime("%Y-%m-%d %H:%M:%S")
    #     db_data = db_readeru.DB_connector().db_to_pd(240)[0]
    #     total_load = self.data_importer.get_forecasts()[0][:, 0]
    #     pv_fcst = self.data_importer.get_forecasts()[1][:, 0]
    #     dgu_states = self.data_importer.eq_status()[1]
    #     equipment_availa = self.data_importer.eq_status()[0]
    #
    #     return db_data, total_load, pv_fcst, dgu_states, equipment_availa, datetime

    def optimizatione(self, model):

        #optimizer = pyo.SolverFactory('scipampl', executable=os.getcwd() + '\scipampl-7.0.0.win.x86_64.intel.opt.spx2')

        #optimizer = pyo.SolverFactory('couenne', executable=os.getcwd() + '\\couenne67.exe')

        results = self.optimizer.solve(model, logfile='.\log\optimizer_log.log', tee=True, timelimit=700,
                                  keepfiles=True)
        results.write()

        #print(results)

        result_df = pd.DataFrame()

        result_df['Общая нагрузка, кВт'] = self.total_load
        result_df['Акт. мощность ДГУ 1, кВт'] = model.x1.get_values().values()
        result_df['Акт. мощность ДГУ 2, кВт'] = model.x2.get_values().values()
        result_df['Акт. мощность ДГУ 3, кВт'] = model.x3.get_values().values()
        result_df['Акт. мощность ДГУ 4, кВт'] = model.x4.get_values().values()
        result_df['Статус ДГУ 1'] = model.u1.get_values().values()
        result_df['Статус ДГУ 2'] = model.u2.get_values().values()
        result_df['Статус ДГУ 3'] = model.u3.get_values().values()
        result_df['Статус ДГУ 4'] = model.u4.get_values().values()
        result_df['Акт. мощность заряда инвертора СНЭ 1, кВт'] = model.bat1_ch.get_values().values()
        result_df['Акт. мощность разряда инвертора СНЭ 1, кВт'] = model.bat1_dch.get_values().values()
        result_df['Акт. мощность заряда инвертора СНЭ 2, кВт'] = model.bat2_ch.get_values().values()
        result_df['Акт. мощность разряда инвертора СНЭ 2, кВт'] = model.bat2_dch.get_values().values()
        result_df['Уровень заряда СНЭ 1, кВт'] = model.soc1.get_values().values()
        result_df['Уровень заряда СНЭ 2, кВт'] = model.soc2.get_values().values()
        result_df['Акт. мощность инвертора СЭС 1, кВт'] = model.PV1.get_values().values()
        result_df['Акт. мощность инвертора СЭС 2, кВт'] = model.PV2.get_values().values()
        result_df['Акт. мощность инвертора СЭС 3, кВт'] = model.PV3.get_values().values()
        result_df['Акт. мощность инвертора СЭС 4, кВт'] = model.PV4.get_values().values()
        result_df['Акт. мощность инвертора СЭС 5, кВт'] = model.PV5.get_values().values()
        result_df['Акт. мощность инвертора СЭС 6, кВт'] = model.PV6.get_values().values()
        result_df['Акт. мощность инвертора СЭС 7, кВт'] = model.PV7.get_values().values()
        result_df['Статус инвертора СЭС 1'] = model.PV1_u.get_values().values()
        result_df['Статус инвертора СЭС 2'] = model.PV2_u.get_values().values()
        result_df['Статус инвертора СЭС 3'] = model.PV3_u.get_values().values()
        result_df['Статус инвертора СЭС 4'] = model.PV4_u.get_values().values()
        result_df['Статус инвертора СЭС 5'] = model.PV5_u.get_values().values()
        result_df['Статус инвертора СЭС 6'] = model.PV6_u.get_values().values()
        result_df['Статус инвертора СЭС 7'] = model.PV7_u.get_values().values()


        inverters_array = result_df[['Акт. мощность инвертора СЭС 1, кВт','Акт. мощность инвертора СЭС 2, кВт',
                                     'Акт. мощность инвертора СЭС 3, кВт','Акт. мощность инвертора СЭС 4, кВт',
                                     'Акт. мощность инвертора СЭС 5, кВт','Акт. мощность инвертора СЭС 6, кВт',
                                     'Акт. мощность инвертора СЭС 7, кВт',]]

        inverters_array['pv1_lim_sw'] = np.nan
        inverters_array['pv2_lim_sw'] = np.nan
        inverters_array['pv3_lim_sw'] = np.nan
        inverters_array['pv4_lim_sw'] = np.nan
        inverters_array['pv5_lim_sw'] = np.nan
        inverters_array['pv6_lim_sw'] = np.nan
        inverters_array['pv7_lim_sw'] = np.nan

        inverters_array['pv1_lim_cr'] = [0]*24
        inverters_array['pv2_lim_cr'] = [0]*24
        inverters_array['pv3_lim_cr'] = [0]*24
        inverters_array['pv4_lim_cr'] = [0]*24
        inverters_array['pv5_lim_cr'] = [0]*24
        inverters_array['pv6_lim_cr'] = [0]*24
        inverters_array['pv7_lim_cr'] = [0]*24


        Ppv_lim_sw = []
        Ppv_lim_sw0 = [[]]

        for i in range(0, 24):

            inverters_array.loc[inverters_array.index[i - 0], 'pv1_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 1, кВт']
            inverters_array.loc[inverters_array.index[i - 0], 'pv2_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 2, кВт']
            inverters_array.loc[inverters_array.index[i - 0], 'pv3_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 3, кВт']
            inverters_array.loc[inverters_array.index[i - 0], 'pv4_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 4, кВт']
            inverters_array.loc[inverters_array.index[i - 0], 'pv5_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 5, кВт']
            inverters_array.loc[inverters_array.index[i - 0], 'pv6_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 6, кВт']
            inverters_array.loc[inverters_array.index[i - 0], 'pv7_lim_sw'] = \
            (round(inverters_array.loc[i].astype(float), 3) < round(inverters_array.loc[i].astype(float).mean(), 3))['Акт. мощность инвертора СЭС 7, кВт']

        inverters_array['pv1_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 1, кВт'] * inverters_array['pv1_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv1_lim'][(inverters_array['pv1_lim'] == 0) & (inverters_array['pv1_lim_sw'] == False)] = 100
        inverters_array['pv2_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 2, кВт'] * inverters_array['pv2_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv2_lim'][(inverters_array['pv2_lim'] == 0) & (inverters_array['pv2_lim_sw'] == False)] = 100
        inverters_array['pv3_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 3, кВт'] * inverters_array['pv3_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv3_lim'][(inverters_array['pv3_lim'] == 0) & (inverters_array['pv3_lim_sw'] == False)] = 100
        inverters_array['pv4_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 4, кВт'] * inverters_array['pv4_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv4_lim'][(inverters_array['pv4_lim'] == 0) & (inverters_array['pv4_lim_sw'] == False)] = 100
        inverters_array['pv5_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 5, кВт'] * inverters_array['pv5_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv5_lim'][(inverters_array['pv5_lim'] == 0) & (inverters_array['pv5_lim_sw'] == False)] = 100
        inverters_array['pv6_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 6, кВт'] * inverters_array['pv6_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv6_lim'][(inverters_array['pv6_lim'] == 0) & (inverters_array['pv6_lim_sw'] == False)] = 100
        inverters_array['pv7_lim'] = np.around((100 * inverters_array['Акт. мощность инвертора СЭС 7, кВт'] * inverters_array['pv7_lim_sw'] / 136).astype(float)).astype(int)
        inverters_array['pv7_lim'][(inverters_array['pv7_lim'] == 0) & (inverters_array['pv7_lim_sw'] == False)] = 100

        decision_list = pd.DataFrame()

        decision_list['Pess1_set'] = result_df['Акт. мощность разряда инвертора СНЭ 1, кВт'] - result_df[
            'Акт. мощность заряда инвертора СНЭ 1, кВт']

        decision_list['Pess2_set'] = result_df['Акт. мощность разряда инвертора СНЭ 2, кВт'] - result_df[
            'Акт. мощность заряда инвертора СНЭ 2, кВт']


        decision_list['Qess_st1_set'] = 1
        decision_list['Qess_st2_set'] = 1

        decision_list['Qess1_set'] = 0
        decision_list['Qess2_set'] = 0

        decision_list['ESS1_mode_set'] = 0
        decision_list['ESS2_mode_set'] = 0


        decision_list['D1_onoff'] = {int(k):int(round(v)) for k,v in model.u1.get_values().items()}.values()
        decision_list['D2_onoff'] = {int(k):int(round(v)) for k,v in model.u2.get_values().items()}.values()
        decision_list['D3_onoff'] = {int(k):int(round(v)) for k,v in model.u3.get_values().items()}.values()
        decision_list['D4_onoff'] = {int(k):int(round(v)) for k,v in model.u4.get_values().items()}.values()

        decision_list['Ppv1_lim'] = inverters_array['pv1_lim']
        decision_list['Ppv2_lim'] = inverters_array['pv2_lim'].round(0).astype(int)
        decision_list['Ppv3_lim'] = inverters_array['pv3_lim'].round(0).astype(int)
        decision_list['Ppv4_lim'] = inverters_array['pv4_lim'].round(0).astype(int)
        decision_list['Ppv5_lim'] = inverters_array['pv5_lim'].round(0).astype(int)
        decision_list['Ppv6_lim'] = inverters_array['pv6_lim'].round(0).astype(int)
        decision_list['Ppv7_lim'] = inverters_array['pv7_lim'].round(0).astype(int)

        decision_list['Ppv1_lim_cr'] = 128
        decision_list['Ppv2_lim_cr'] = 128
        decision_list['Ppv3_lim_cr'] = 128
        decision_list['Ppv4_lim_cr'] = 128
        decision_list['Ppv5_lim_cr'] = 128
        decision_list['Ppv6_lim_cr'] = 128
        decision_list['Ppv7_lim_cr'] = 128

        decision_list['Ppv1_lim_sw'] = inverters_array['pv1_lim_sw'].astype(int)
        decision_list['Ppv2_lim_sw'] = inverters_array['pv2_lim_sw'].astype(int)
        decision_list['Ppv3_lim_sw'] = inverters_array['pv3_lim_sw'].astype(int)
        decision_list['Ppv4_lim_sw'] = inverters_array['pv4_lim_sw'].astype(int)
        decision_list['Ppv5_lim_sw'] = inverters_array['pv5_lim_sw'].astype(int)
        decision_list['Ppv6_lim_sw'] = inverters_array['pv6_lim_sw'].astype(int)
        decision_list['Ppv7_lim_sw'] = inverters_array['pv7_lim_sw'].astype(int)

        decision_list['PV1_start'] = {int(k):int(v) for k,v in model.PV1_u.get_values().items()}.values()
        decision_list['PV2_start'] = {int(k):int(v) for k,v in model.PV2_u.get_values().items()}.values()
        decision_list['PV3_start'] = {int(k):int(v) for k,v in model.PV3_u.get_values().items()}.values()
        decision_list['PV4_start'] = {int(k):int(v) for k,v in model.PV4_u.get_values().items()}.values()
        decision_list['PV5_start'] = {int(k):int(v) for k,v in model.PV5_u.get_values().items()}.values()
        decision_list['PV6_start'] = {int(k):int(v) for k,v in model.PV6_u.get_values().items()}.values()
        decision_list['PV7_start'] = {int(k):int(v) for k,v in model.PV7_u.get_values().items()}.values()

        decision_list['DT'] = self.datetime

        #decision_list['PV1_stop'] = 1 - model.PV1_u.get_values().values()
        #decision_list['PV2_stop'] = 1 - model.PV2_u.get_values().values()
        #decision_list['PV3_stop'] = 1 - model.PV3_u.get_values().values()
        #decision_list['PV4_stop'] = 1 - model.PV4_u.get_values().values()
        #decision_list['PV5_stop'] = 1 - model.PV5_u.get_values().values()
        #decision_list['PV6_stop'] = 1 - model.PV6_u.get_values().values()
        #decision_list['PV7_stop'] = 1 - model.PV7_u.get_values().values()


        #
        # decision_list.append(1)  # Режим выдачи реактивной мощности  инвертора 1 СНЭ
        # decision_list.append(1)  # Режим выдачи реактивной мощности  инвертора 2 СНЭ
        #
        # decision_list.append(0)  # Реактивная мощность  инвертора 1 СНЭ
        # decision_list.append(0)  # Реактивная мощность  инвертора 2 СНЭ
        #
        # decision_list.append(1)  # Режим работы инвертора 1 СНЭ
        # decision_list.append(1)  # Режим работы инвертора 2 СНЭ
        #
        # decision_list.append(model.u1.get_values().values())    # Пуск/останов ДГУ 1
        # decision_list.append(model.u2.get_values().values())    # Пуск/останов ДГУ 2
        # decision_list.append(model.u3.get_values().values())    # Пуск/останов ДГУ 3
        # decision_list.append(model.u4.get_values().values())    # Пуск/останов ДГУ 4
        #
        # decision_list.append(inverters_array['pv1_lim'])    # Ограничение активной мощности инвертора 1 СЭС
        # decision_list.append(inverters_array['pv2_lim'])    # Ограничение активной мощности инвертора 2 СЭС
        # decision_list.append(inverters_array['pv3_lim'])    # Ограничение активной мощности инвертора 3 СЭС
        # decision_list.append(inverters_array['pv4_lim'])    # Ограничение активной мощности инвертора 4 СЭС
        # decision_list.append(inverters_array['pv5_lim'])    # Ограничение активной мощности инвертора 5 СЭС
        # decision_list.append(inverters_array['pv6_lim'])    # Ограничение активной мощности инвертора 6 СЭС
        # decision_list.append(inverters_array['pv7_lim'])    # Ограничение активной мощности инвертора 7 СЭС
        #
        # decision_list.append(inverters_array['pv7_lim'])
        #
        # decision_list.append(inverters_array['pv1_lim_sw']) # Регулировка активной мощности инвертора 1 СЭС с поправкой на текущий режим работы
        # decision_list.append(inverters_array['pv2_lim_sw']) # Регулировка активной мощности инвертора 2 СЭС с поправкой на текущий режим работы
        # decision_list.append(inverters_array['pv3_lim_sw']) # Регулировка активной мощности инвертора 3 СЭС с поправкой на текущий режим работы
        # decision_list.append(inverters_array['pv4_lim_sw']) # Регулировка активной мощности инвертора 4 СЭС с поправкой на текущий режим работы
        # decision_list.append(inverters_array['pv5_lim_sw']) # Регулировка активной мощности инвертора 5 СЭС с поправкой на текущий режим работы
        # decision_list.append(inverters_array['pv6_lim_sw']) # Регулировка активной мощности инвертора 6 СЭС с поправкой на текущий режим работы
        # decision_list.append(inverters_array['pv7_lim_sw']) # Регулировка активной мощности инвертора 7 СЭС с поправкой на текущий режим работы
        #
        # decision_list.append(model.PV1_u.get_values().values())  # Включение в сеть инвертора 1 СЭС
        # decision_list.append(model.PV2_u.get_values().values())  # Включение в сеть инвертора 2 СЭС
        # decision_list.append(model.PV3_u.get_values().values())  # Включение в сеть инвертора 3 СЭС
        # decision_list.append(model.PV4_u.get_values().values())  # Включение в сеть инвертора 4 СЭС
        # decision_list.append(model.PV5_u.get_values().values())  # Включение в сеть инвертора 5 СЭС
        # decision_list.append(model.PV6_u.get_values().values())  # Включение в сеть инвертора 6 СЭС
        # decision_list.append(model.PV7_u.get_values().values())  # Включение в сеть инвертора 7 СЭС

        return result_df, decision_list

    def plot_summary(self, df):

        df.index = self.datetime.strftime("%H:%M %d-%m")

        fig, ax = plt.subplots(1, figsize=(25, 15))



        PV_power = df[['Акт. мощность инвертора СЭС 1, кВт', 'Акт. мощность инвертора СЭС 2, кВт',
                       'Акт. мощность инвертора СЭС 3, кВт', 'Акт. мощность инвертора СЭС 4, кВт',
                       'Акт. мощность инвертора СЭС 5, кВт', 'Акт. мощность инвертора СЭС 6, кВт',
                       'Акт. мощность инвертора СЭС 7, кВт']].sum(axis=1)
        ax.bar(df.index, PV_power, label='СЭС', edgecolor="black", width=0.75, hatch='//', color='orange')
        ax.bar(df.index, -df['Акт. мощность заряда инвертора СНЭ 1, кВт'], width=0.75, edgecolor='black', hatch='o', color='slateblue')
        ax.bar(df.index, -df['Акт. мощность заряда инвертора СНЭ 2, кВт'],
               bottom = -df['Акт. мощность заряда инвертора СНЭ 1, кВт'], width=0.75, edgecolor='black', hatch='o',
               color='darkslateblue')

        ax.bar(df.index, df['Акт. мощность разряда инвертора СНЭ 1, кВт'], bottom = df['Акт. мощность ДГУ 3, кВт'] +
                                                                               df['Акт. мощность ДГУ 4, кВт'] +
                                                                               df['Акт. мощность ДГУ 1, кВт'] +
                                                                                     df['Акт. мощность ДГУ 2, кВт'] +
                                                                                     PV_power, label='Инвертор СНЭ 1', width=0.75,
               edgecolor='black', hatch='o',
               color='slateblue')
        ax.bar(df.index, df['Акт. мощность разряда инвертора СНЭ 2, кВт'], bottom=df['Акт. мощность ДГУ 3, кВт'] +
                                                                                   df['Акт. мощность ДГУ 4, кВт'] +
                                                                                   df['Акт. мощность ДГУ 1, кВт'] +
                                                                                   df['Акт. мощность ДГУ 2, кВт'] +
                                                                df['Акт. мощность разряда инвертора СНЭ 1, кВт'] +
                                                                                   PV_power, label='Инвертор СНЭ 2', width=0.75,
               edgecolor='black', hatch='o',
               color='darkslateblue')


        ax.bar(df.index, df['Акт. мощность ДГУ 1, кВт'], label='ДГУ 1', bottom=PV_power +
                                                                               df['Акт. мощность ДГУ 3, кВт'] +
                                                                               df['Акт. мощность ДГУ 4, кВт'],
               edgecolor="black", align='center', width=0.75, hatch="//", color='royalblue')
        ax.bar(df.index, df['Акт. мощность ДГУ 2, кВт'], label='ДГУ 2', bottom=PV_power +
                                                                               df['Акт. мощность ДГУ 3, кВт'] +
                                                                               df['Акт. мощность ДГУ 4, кВт'] +
                                                                               df['Акт. мощность ДГУ 1, кВт'],
               edgecolor="black", align='center', width=0.75, hatch="//", color='dimgray')
        ax.bar(df.index, df['Акт. мощность ДГУ 3, кВт'], label='ДГУ 3', bottom=PV_power,
               edgecolor="black", align='center', width=0.75, hatch="//", color='teal')
        ax.bar(df.index, df['Акт. мощность ДГУ 4, кВт'], label='ДГУ 4', bottom=PV_power + df['Акт. мощность ДГУ 3, кВт'],
               edgecolor="black", align='center', width=0.75, hatch="//", color='deepskyblue')

        ax.grid()
        ax.set_axisbelow(True)

        ax2 = ax.twinx()
        ax2.set_ylabel('Уровень заряда, %', fontsize=18)
        ax.set_ylabel('Мощность, кВт', fontsize=18)

        ax2.plot(df.index, df['Уровень заряда СНЭ 1, кВт'], '--', color='darkred', label='Уровень заряда\nСНЭ 1', linewidth=3,
                 marker='o', markeredgecolor='black', markersize=10)

        ax2.plot(df.index, df['Уровень заряда СНЭ 2, кВт'], '--', color='darkred', label='Уровень заряда\nСНЭ 2',
                 linewidth=3,
                 marker='s', markeredgecolor='black', markersize=10)

        ax.plot(df.index, df['Общая нагрузка, кВт'], color='red', label='Общая нагрузка', linewidth=4, marker='o', markeredgecolor='black',
                markersize=10)


        ax.legend(ncol=4, bbox_to_anchor=(0.9, 1.15), fancybox=True, fontsize=18)

        ax.set_xlabel('Дата и время', fontsize=15)

        major_ticks = np.arange(-200, 801, 50)
        minor_ticks = np.arange(-200, 801, 25)

        major_ticks2 = np.arange(0, 101, 10)
        minor_ticks2 = np.arange(0, 101, 5)

        ax.set_yticks(major_ticks)
        ax.set_yticks(minor_ticks, minor=True)

        xfmt = mdates.DateFormatter('%H:%M')
        # ax.xaxis.set_major_formatter(xfmt, fontsize = 15)

        ax.tick_params(axis='x', which='major', rotation=90, labelsize=15) #labelsize=15
        ax.tick_params(axis='y', labelsize=18)
        ax2.tick_params(axis='y', labelsize=18)
        # ax.tick_params(axis='x', which='minor', labelsize=8)
        ax2.legend(loc='lower left', fontsize=18)
        ax2.patch.set_alpha(0)
        ax2.set_ylim([30, 100])
        ax2.grid(None)
        #plt.show()
        plt.savefig('оптимальное_решение.png')

        return




def the_process():
    try:
        #отладить позднее
        print()
        print("...Запуск...")

        # for remaining in range(10, 0, -1):
        #     sys.stdout.write("\r")
        #     sys.stdout.write("{:2d} seconds remaining.".format(remaining))
        #     sys.stdout.flush()
        #     time.sleep(1)

        #sys.stdout.write("\rComplete!            \n")


        with open(os.getcwd() + "\\parameters.txt") as f:
            parameters = f.readlines()
            parameters = [x.strip() for x in parameters]
            f.close()

        data_importer = formulation.Data_Importer()
        datetime = data_importer.get_forecasts()[3].index

        # # #

        #db_data = db_readeru.DB_connector().db_to_pd(240)[0] # импортируем данные из БД

        # # #

        db_data = db_readeru.DB_connector().db_from_csv()

        total_load = data_importer.get_forecasts()[0][:, 0] #

        try:
            print()
            print("...Выполнение прогнозирования мощности СЭС...")
            pv_fcst = data_importer.get_forecasts()[1][:, 0]
        except Exception as e:
            logging.error(traceback.format_exc())
            print()
            print("****** ОШИБКА! Не удалось выполнить прогнозирование мощности СЭС! ******")
            print()
            print("////// Модуль завершил работу. //////")
            print()
            sys.exit(1)


        dgu_states = data_importer.eq_status()[1]
        equipment_availa = data_importer.eq_status()[0]
        ent = DecisionSeeking(db_data, total_load, pv_fcst, dgu_states, equipment_availa, datetime, parameters[1])

        print()
        print("...Вспомогательные файлы и данные успешно загружены...")
    except Exception as e:
        logging.error(traceback.format_exc())
        print()
        print("****** ОШИБКА! Не удалось импортировать данные! ******")
        print()
        print("////// Модуль завершил работу. //////")
        print()
        sys.exit(1)

    try:
        entity = formulation.Problemah(total_load, pv_fcst, dgu_states, equipment_availa, db_data, parameters[0])
    except Exception as e:
        logging.error(traceback.format_exc())
        print()
        print("****** ОШИБКА! Не удалось корректно сформулировать задачу оптимизации! ******")
        print()
        print("////// Модуль завершил работу. //////")
        print()
        sys.exit(1)

    try:
        print()
        print("...Выполнение поиска оптимального решения...")
        print()
        resultado = ent.optimizatione(entity.m)
        # print('resultadfo')
        # print(resultado[0]['Статус ДГУ 4'])
        # print(resultado[1].loc[0])
        print()
        print("...Оптимальное решение найдено!...")
    except Exception as e:
        logging.error(traceback.format_exc())
        print()
        print("****** ОШИБКА! Задача оптимизации не имеет решения! ******")
        print()
        print("////// Модуль завершил работу. //////")
        print()
        sys.exit(1)

    try:
        #sql_stuff = db_readeru.DB_connector()
        print()
        print("...Запись найденного оптимального решения в БД MS SQL Server...")
        db_readeru.DB_connector().decision_to_sql(resultado[1].loc[0])
        print()
        print("...Оптимальное решение успешно записано в БД MS SQL Server...")
    except Exception as e:
        logging.error(traceback.format_exc())
        print()
        print("****** ОШИБКА! Не удалось записать найденное решение в БД MS SQL Server ******")
        print()
        print("////// Модуль завершил работу. //////")
        print()
        sys.exit(1)

    try:
        print()
        print("...Запись найденного оптимального решения в графический файл...")
        ent.plot_summary(resultado[0])
        print()
        print("...Решение успешно сохранено в файл оптимальное_решение.png...")
    except Exception as e:
        logging.error(traceback.format_exc())
        print()
        print("****** ОШИБКА! Не удалось экспортировать найденное решение в графический файл ******")
        print()
        print("////// Модуль успешно завершил работу. //////")
        print()
        sys.exit(1)


the_process()

# def progress():
#     start_time = time.time()
#     print('Модуль в работе ' + str(int(time.time() - start_time)))
#     while True:
#     # bar_len = 60
#     # filled_len = int(round(bar_len * count / float(total)))
#     #
#     # percents = round(100.0 * count / float(total), 1)
#     # bar = '=' * filled_len + '-' * (bar_len - filled_len)
#
#     # sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
#     # sys.stdout.flush()
#
#         sys.stdout.write('Модуль в работе ' + str(int(time.time() - start_time)))
#         sys.stdout.write("\033[F")
#         sys.stdout.flush()
#         time.sleep(.1)



# if __name__ == '__main__':
#     multiprocessing.freeze_support()
#
#     p = multiprocessing.Process(target=progress())
#
#     p1 = multiprocessing.Process(target=the_process)
#     p.start()
#     p1.start()
#     # if flag == 1:
#     #     p.stop()





