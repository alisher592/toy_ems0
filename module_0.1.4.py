import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import sys
import os.path
#import pyomo
import pyomo.environ as pyo
#import pvlib
#import math
#from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import time
from pyomo.environ import *
import sys,os
sys.path.append(os.getcwd())
import random
import os
from datetime import datetime
import logging
import traceback
from shutil import copyfile
import multiprocessing
#import cloudpickle
from pyomo.common.tempfiles import TempfileManager
import forecasters

if not os.path.exists(os.getcwd()+"\\tempo"):
    os.makedirs(os.getcwd()+"\\tempo")
TempfileManager.tempdir = os.getcwd()+"\\tempo"

logging.basicConfig(filename='C:\project\log.txt', level=logging.INFO,
                                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger = logging.getLogger(__name__)

def counter_time():
    start_time = time.time()
    fls = reading.files()[1]
    increment = 0
    while True:
        increment+=1
        #with open(fls, 'w') as file:
            # file.write(str('\n'))
            # file.write(str(increment))
            # file.close()
            # time.sleep(10)
        try:
            bazah = db_readeru.DB_connector()
            bazah.indicator_to_sql(increment)
            print('')
            print('*****************************************')
            print('Модуль в работе ' + str(int(time.time() - start_time)) + ' c. Индикатор <' + str(
                increment) + '> записан в БД')
            print('*****************************************')
            print('')
            time.sleep(10)
        except Exception as e:
            logging.error(traceback.format_exc())
            print('--!!!--')
            print('Ошибка при записи индикатора связи в БД! Следующая попытка через 10 секунд...')
            print('--!!!--')
            time.sleep(10)




        # file = open(fls, 'w')
        # file.write('1')
        # file.close
        # print('')
        # print('*****************************************')
        # print('Модуль в работе '+ str(int(time.time()-start_time)) + ' c. Индикатор (1) записан в ' + fls)
        # print('*****************************************')
        # print('')
        # time.sleep(10)

##t1 = threading.Thread(target=counter_time)
##t1.daemon = True
###t2 = threading.Thread(target=counter_time)
##t1.start()
###t2.start()

load_files = ['models/mlp_load_hourly.vrk', 'models/X_scaler_par.sca', 'models/Y_scaler_par.sca']


pv_files = ['models/pv_keras', 'models/pv_keras/pv_X_scaler_par.sca',
            'models/pv_keras/pv_Y_scaler_par.sca']
#pv_fcst = forecasters.PV_forecaster(pv_files).get_pv_forecast()

#print(np.asarray(load_fcst)[23])

fig, ax = plt.subplots(8, 1, figsize=(18, 14))

try:
    import db_readeru
    db_datah = db_readeru.DB_connector().db_to_pd(120)
except Exception as e:
    print('--!!!--')
    print('Ошибка при подключении к базе данных!')
    print('--!!!--')
    logging.error(traceback.format_exc())

class reading:

    Load=[0,0,0,0,0]
    PV=[0,0,0,0,0,0,0]

    output = []

    N = 4
    N = np.array([n for n in range(0, N)])
    T = np.array([t for t in range(0, 24)])
    T1 = 0
    T2 = 24

    p12 = np.arange(0, 321)
    p34 = np.arange(0, 521)
    p_PV = np.arange(0, 137)
    p_BESS = np.arange(0, 151)


    DGU1_pmax = 400 #кВт
    DGU1_pmin = 0.5*DGU1_pmax

    DGU2_pmax = 400 #кВт
    DGU2_pmin = 0.5*DGU2_pmax

    DGU3_pmax = 536 #кВт
    DGU3_pmin = 0.5*DGU3_pmax

    DGU4_pmax = 536 #кВт
    DGU4_pmin = 0.5*DGU4_pmax

    DGU1_fuel = 0.3031*p12
    DGU2_fuel = 0.3031*p12
    DGU3_fuel = 0.2788*p34
    DGU4_fuel = 0.2788*p34

    d1_min_up_time = 3
    d2_min_up_time = 3
    d3_min_up_time = 3
    d4_min_up_time = 3

    d1_min_down_time = 3
    d2_min_down_time = 3
    d3_min_down_time = 3
    d4_min_down_time = 3

    d12_startup_cost = 1000
    d34_startup_cost = 2000

    d12_shutdown_cost = 1100
    d34_shutdown_cost = 2100

    Fuel_price = 70 #цена за литр диз.топлива 
    #коэффициенты из расходных характеристик ДГУ
    DGU12_a = 0.0219
    DGU12_b = 0.3125
    DGU34_a = 0.049
    DGU34_b = 0.2788

    ESS_inv = 150

    bat1_dod = 40
    bat2_dod = 40

    soc1_after = 100
    soc2_after = 100

    PV_inv_Pmax = 136

    # fig, ax = plt.subplots(1,1)

    # ax.plot(DGU1_fuel, label='ДГУ1-2')
    # ax.plot(DGU3_fuel, label='ДГУ3-4')

    # ax.set_xlim(0, 600)
    # ax.set_ylim(0, 500)
    # ax.set_xlabel('Мощность, кВт')
    # ax.set_ylabel('Расход топлива, л/ч')
    # ax.legend(loc='best')
    # ax.grid()



    def conv(x):
        return x.replace(',', '.').encode()

    def files():
        with open(os.getcwd()+"\\parameters.txt") as f:
            param_file = f.readlines()
            param_file = [x.strip() for x in param_file]
        return param_file



    
    def init_data_import(): #в эту функцию позже нужно добавить функции прогнозирования !!! Проследить, как часто она вызывается!
        fls = reading.files() #чтение пути к файлу импорта
        
        try:
            load_fcst = forecasters.Load_forecaster(load_files).get_hourly_forecast()
            self_consumption_fcst = forecasters.Load_forecaster(load_files).self_consumption_forecast()
            #if os.path.isfile(fls[2]):
            if len(db_datah) != 0:
                #print('СТАРТ ОТСЛЕЖИВАНИЯ ИЗМЕНЕНИЙ', datetime.now())
                #inn=np.genfromtxt((reading.conv(x) for x in open(fls[2])), delimiter=';')
                if db_datah[0].shape[1] == 79:
                    out0=pd.read_csv(fls[3], delimiter=';')
                    out=np.array(out0)

                    #print(inn)

                    #Псевдопрогноз нагрузки
                    # Load = [0,0,0,0,0]
                    # Load[0] = inn[0:7].sum()+inn[28:30].sum()+inn[42:46].sum()+inn[66]+inn[68]+inn[70]
                    # Load[1] = Load[0] + random.uniform(-65.0,65.0)*(-1)
                    # Load[2] = Load[0] + random.uniform(-65.0,65.0)*(-1)
                    # Load[3] = Load[0] + random.uniform(-65.0,65.0)*(-1)
                    # Load[4] = Load[0] + random.uniform(-65.0,65.0)*(-1)

                    Load = load_fcst.values + self_consumption_fcst['Собственные нужды'].values

                    #псевдопрогноз выработки СЭС
                    # PV=[inn[0:7].sum(), inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1), inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1),
                    # inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1),inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1)]
                    PV = np.array([0]*24)

                    #print(PV)

                    #PV = (pv_fcst/1000).values.reshape(24,1)
                    #PV[PV<0] = 0




                    # обработка данных по СНЭ из MS SQL
                    soc1_before = db_datah[0]['F68'][0]/10  # последнее на данную минуту значение уровня заряда СНЭ1 # inn[34]/10
                    soc2_before = db_datah[0]['F69'][0]/10  # последнее на данную минуту значение уровня заряда СНЭ2 # inn[35]/10
                    ess1_availability_state = db_datah[0]['F74'][0]
                    ess2_availability_state = db_datah[0]['F75'][0]

                    # обработка данных по ДГУ из MS SQL
                    # граничные условия по статусам ДГУ
                    DGU_starts_statuses = db_readeru.DB_connector().DG_before(db_datah)[0] # список со статусами ДГУ
                    DGU_up_times = db_readeru.DB_connector().DG_before(db_datah)[1] # список с числом часов ДГУ в работе
                    DGU_down_times = db_readeru.DB_connector().DG_before(db_datah)[2]  # список с числом часов ДГУ в простое
                    DGU_availability = db_readeru.DB_connector().DG_before(db_datah)[3]  # список со статусами доступности ДГУ

                    u1_start = DGU_starts_statuses[0]
                    d1_up_before = DGU_up_times[0]
                    d1_down_before = DGU_down_times[0]
                    d1_availability_state = DGU_availability[0]

                    u2_start = DGU_starts_statuses[1]
                    d2_up_before = DGU_up_times[1]
                    d2_down_before = DGU_down_times[1]
                    d2_availability_state = DGU_availability[1]

                    u3_start = DGU_starts_statuses[2]
                    d3_up_before = DGU_up_times[2]
                    d3_down_before = DGU_down_times[2]
                    d3_availability_state = DGU_availability[2]

                    u4_start = DGU_starts_statuses[3]
                    d4_up_before = DGU_up_times[3]
                    d4_down_before = DGU_down_times[3]
                    d4_availability_state = DGU_availability[3]

                    # print(u1_start, d1_up_before, d1_down_before, d1_availability_state, u2_start, d2_up_before, d2_down_before, d2_availability_state,
                    # u3_start, d3_up_before, d3_down_before, d3_availability_state,
                    # u4_start, d4_up_before, d4_down_before, d4_availability_state)


                    # if inn[50]==30 and inn[62]==1 and inn[42]!=0:
                    #     u1_start = 1
                    #     d1_up_before = 2
                    #     d1_down_before = 1
                    # # elif inn[50]==23 and inn[62]==1 and inn[42]!=0:
                    # #     u1_start = 0
                    # #     d1_up_before = 0
                    # #     d1_down_before = 3
                    # else:
                    #     u1_start = 0
                    #     d1_up_before = 0
                    #     d1_down_before = 3
                    # if inn[51]==30 and inn[63]==1 and inn[43]!=0:
                    #     u2_start = 1
                    #     d2_up_before = 2
                    #     d2_down_before = 1
                    # else:
                    #     u2_start = 0
                    #     d2_up_before = 0
                    #     d2_down_before = 3
                    # if inn[52]==30 and inn[64]==1 and inn[44]!=0:
                    #     u3_start = 1
                    #     d3_up_before = 2
                    #     d3_down_before = 1
                    # else:
                    #     u3_start = 0
                    #     d3_up_before = 0
                    #     d3_down_before = 3
                    # if inn[53]==30 and inn[65]==1 and inn[45]!=0:
                    #     u4_start = 1
                    #     d4_up_before = 2
                    #     d4_down_before = 1
                    # else:
                    #     u4_start = 0
                    #     d4_up_before = 0
                    #     d4_down_before = 3
                    #
                    # #ava states
                    # d1_availability_state = int(inn[62])
                    # d2_availability_state = int(inn[63])
                    # d3_availability_state = int(inn[64])
                    # d4_availability_state = int(inn[65])
                    #
                    # ess1_availability_state = int(inn[40])
                    # ess2_availability_state = int(inn[41])



                    return [Load, PV, soc1_before, soc2_before, u1_start, d1_up_before, d1_down_before, d1_availability_state, u2_start, d2_up_before, d2_down_before, d2_availability_state,
                    u3_start, d3_up_before, d3_down_before, d3_availability_state,
                    u4_start, d4_up_before, d4_down_before, d4_availability_state, ess1_availability_state, ess2_availability_state, soc1_before, soc2_before]
                else:
                    logging.error('Недопустимый ответ от БД. Количество строк в теле ответа не равно 79!')
                    print('')
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    print('ОШИБКА! Недопустимый ответ от базы данных!')
                    print('Количество строк в файле не равно 79!')
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    print('')
            else:
                logging.error('Не удалось подключиться к БД')
                print('')
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                print('ОШИБКА! Не удалось подключиться к базе данных!')
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                print('')
   
        except Exception as e:

            logger=logging.getLogger(__name__)
            logging.error(traceback.format_exc())

            if not os.path.exists(fls[0]+'ошибки'):
                os.makedirs(fls[0]+'ошибки')
            dst=os.path.join(fls[0]+'ошибки\\')
            copyfile(fls[2], dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'imported_file.csv')
            copyfile(fls[3], dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'exported_file.csv')
            print()
            print('-----------------------------------------------------')
            print('ОШИБКА! Проблема с получением ответа от базы данных!. Лог в ' + fls[0]+'log.txt')
            print('-----------------------------------------------------')
            print()
            print('*************************************************')
            print('Обращение к БД данных возобновится через 5 секунд')
            print('*************************************************')
            print()
            time.sleep(5)
            flag = 1

            return 0
            #continue
        #break
    def output_file_read():
        
        fileName = reading.files()[3]
        out0=pd.read_csv(fileName, delimiter=';')
        out=np.array(out0)
        return out0, out

class opt_pyomo_formulating:

    
    m = pyo.ConcreteModel()
    m.N = pyo.Set(initialize=reading.N)
    m.T = pyo.Set(initialize=reading.T)


    #Ограничения
    def balance(self, model, i):
        return self.m.x1[i] + self.m.x2[i] + self.m.x3[i] + self.m.x4[i] + \
               self.m.bat1_dch[i] - self.m.bat1_ch[i] + self.m.bat2_dch[i] - self.m.bat2_ch[i] + \
               self.m.PV1[i] + self.m.PV2[i] + self.m.PV3[i] + self.m.PV4[i] + self.m.PV5[i] + self.m.PV6[i] + \
               self.m.PV7[i] == reading.init_data_import()[0][:,0][i] #(np.asarray(

    def d1_start_up_cost(self, model, i):
        if i == reading.T1:
            return self.m.suc1[i] >= reading.d12_startup_cost*(self.m.u1[i]-reading.init_data_import()[4])
        else:
            return self.m.suc1[i] >= reading.d12_startup_cost*(self.m.u1[i]-self.m.u1[i-1])
        
    def d2_start_up_cost(self, model, i):
        if i == reading.T1:
            return self.m.suc2[i] >= reading.d12_startup_cost*(self.m.u2[i]-reading.init_data_import()[8])
        else:
            return self.m.suc2[i] >= reading.d12_startup_cost*(self.m.u2[i]-self.m.u2[i-1])
        
    def d3_start_up_cost(self, model, i):
        if i == reading.T1:
            return self.m.suc3[i] >= reading.d34_startup_cost*(self.m.u3[i]-reading.init_data_import()[12])
        else:
            return self.m.suc3[i] >= reading.d34_startup_cost*(self.m.u3[i]-self.m.u3[i-1])
        
    def d4_start_up_cost(self, model, i):
        if i == reading.T1:
            return self.m.suc4[i] >= reading.d34_startup_cost*(self.m.u4[i]-reading.init_data_import()[16])
        else:
            return self.m.suc4[i] >= reading.d34_startup_cost*(self.m.u4[i]-self.m.u4[i-1])
        
    def d1_shut_down_cost(self, model, i):
        if i == reading.T1:
            return self.m.sdc1[i] >= reading.d12_shutdown_cost*(reading.init_data_import()[4]-self.m.u1[i])
        else:
            return self.m.sdc1[i] >= reading.d12_shutdown_cost*(self.m.u1[i-1]-self.m.u1[i])

    def d2_shut_down_cost(self, model, i):
        if i == reading.T1:
            return self.m.sdc2[i] >= reading.d12_shutdown_cost*(reading.init_data_import()[8]-self.m.u2[i])
        else:
            return self.m.sdc2[i] >= reading.d12_shutdown_cost*(self.m.u2[i-1]-self.m.u2[i])
        
    def d3_shut_down_cost(self, model, i):
        if i == reading.T1:
            return self.m.sdc3[i] >= reading.d34_shutdown_cost*(reading.init_data_import()[12]-self.m.u3[i])
        else:
            return self.m.sdc3[i] >= reading.d34_shutdown_cost*(self.m.u3[i-1]-self.m.u3[i])

    def d4_shut_down_cost(self, model, i):
        if i == reading.T1:
            return self.m.sdc4[i] >= reading.d34_shutdown_cost*(reading.init_data_import()[16]-self.m.u4[i])
        else:
            return self.m.sdc4[i] >= reading.d34_shutdown_cost*(self.m.u4[i-1]-self.m.u4[i])


    # def d1o(model, i):
    #     if i == T1:
    #         return m.u1[i] - d1_min_up_time*(m.u1[i] - u1_start) >= 0
    #     else:

    #         return sum(uj) >= d1_min_up_time*(m.u1[i] - m.u1[i-1])


    # def d2o(model, i):
    #     if i == T1:
    #         return (1-m.u3[i]) >= d3_min_down_time*(u3_start - m.u3[i])
    #     if i > T2-3:
    #         return m.u3[i+1] + m.u3[i+2] + m.u3[i+3]  >= d1_min_down_time*(m.u1[i-1] - m.u1[i])

    # def d1_partial(model, i):
    #     return m.x1

    def d1_min_up_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[5] - reading.d1_min_up_time)*(reading.init_data_import()[4] - self.m.u1[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u1[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u1[j])
            return ((sum(uj) - reading.d1_min_up_time)*(self.m.u1[i-1] - self.m.u1[i])) >= 0
        else:
            return ((self.m.u1[i-1] + self.m.u1[i-2] + self.m.u1[i-3] - reading.d1_min_up_time)*(self.m.u1[i-1] - self.m.u1[i])) >= 0
        
    def d2_min_up_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[9] - reading.d2_min_up_time)*(reading.init_data_import()[8] - self.m.u2[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u2[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u2[j])
            return ((sum(uj) - reading.d2_min_up_time)*(self.m.u2[i-1] - self.m.u2[i])) >= 0
        else:
            return ((self.m.u2[i-1] + self.m.u2[i-2] + self.m.u2[i-3] - reading.d2_min_up_time)*(self.m.u2[i-1] - self.m.u2[i])) >= 0
        
    def d3_min_up_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[13] - reading.d3_min_up_time)*(reading.init_data_import()[12] - self.m.u3[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u3[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u3[j])
            return ((sum(uj) - reading.d3_min_up_time)*(self.m.u3[i-1] - self.m.u3[i])) >= 0
        else:
            return ((self.m.u3[i-1] + self.m.u3[i-2] + self.m.u3[i-3] - reading.d3_min_up_time)*(self.m.u3[i-1] - self.m.u3[i])) >= 0

    def d4_min_up_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[17] - reading.d4_min_up_time)*(reading.init_data_import()[16] - self.m.u4[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u4[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u4[j])
            return ((sum(uj) - reading.d4_min_up_time)*(self.m.u4[i-1] - self.m.u4[i])) >= 0
        else:
            return ((self.m.u4[i-1] + self.m.u4[i-2] + self.m.u4[i-3] - reading.d4_min_up_time)*(self.m.u4[i-1] - self.m.u4[i])) >= 0

    def d1_min_down_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[6] + reading.d1_min_down_time)*(-reading.init_data_import()[4] + self.m.u1[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u1[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u1[j])
            return ((sum(uj) - 2 + reading.d1_min_down_time)*(-self.m.u1[i-1] + self.m.u1[i])) <= 0
        else:
            return ((self.m.u1[i-1] + self.m.u1[i-2] + self.m.u1[i-3] - 3 + reading.d1_min_down_time)*(-self.m.u1[i-1] + self.m.u1[i])) <= 0

    def d2_min_down_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[10] + reading.d2_min_down_time)*(-reading.init_data_import()[8] + self.m.u2[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u2[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u2[j])
            return ((sum(uj) - 2 + reading.d2_min_down_time)*(-self.m.u2[i-1] + self.m.u2[i])) <= 0
        else:
            return ((self.m.u2[i-1] + self.m.u2[i-2] + self.m.u2[i-3] - 3 + reading.d2_min_down_time)*(-self.m.u2[i-1] + self.m.u2[i])) <= 0

    def d3_min_down_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[14] + reading.d3_min_down_time)*(-reading.init_data_import()[12] + self.m.u3[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u3[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u3[j])
            return ((sum(uj) - 2 + reading.d3_min_down_time)*(-self.m.u3[i-1] + self.m.u3[i])) <= 0
        else:
            return ((self.m.u3[i-1] + self.m.u3[i-2] + self.m.u3[i-3] - 3 + reading.d3_min_down_time)*(-self.m.u3[i-1] + self.m.u3[i])) <= 0

    def d4_min_down_time_c(self, model, i):
        if i == reading.T1:
            return (reading.init_data_import()[18] + reading.d4_min_down_time)*(-reading.init_data_import()[16] + self.m.u4[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(self.m.u4[i-1])
            for j in range(reading.T1, i):
                uj.append(self.m.u4[j])
            return ((sum(uj) - 2 + reading.d4_min_down_time)*(-self.m.u4[i-1] + self.m.u4[i])) <= 0
        else:
            return ((self.m.u4[i-1] + self.m.u4[i-2] + self.m.u4[i-3] - 3 + reading.d4_min_down_time)*(-self.m.u4[i-1] + self.m.u4[i])) <= 0

    #ограничение глубины разряда СНЭ  
    def soc1_ctrl(self, model, i):
        if i == reading.T1:
            return self.m.soc1[i] == reading.init_data_import()[22] - 100*self.m.bat1_dch[i]/(0.78*700) + 0.78*100*self.m.bat1_ch[i]/700 #0.8 round trip efficiency
        else:
            return self.m.soc1[i] == self.m.soc1[i-1] - 100*self.m.bat1_dch[i]/(0.78*700) + 0.78*100*self.m.bat1_ch[i]/700 #0.8 round trip efficiency

    def soc2_ctrl(self, model, i):
        if i == reading.T1:
            return self.m.soc2[i] == reading.init_data_import()[23] - 100*self.m.bat2_dch[i]/(0.78*700) + 0.78*100*self.m.bat2_ch[i]/700
        else:
            return self.m.soc2[i] == self.m.soc2[i-1] - 100*self.m.bat2_dch[i]/(0.78*700) + 0.78*100*self.m.bat2_ch[i]/700
        
    #СНЭ не должна заряжаться и разряжаться одновременно     
    def ch_x_dch1 (self, model, i):
        return self.m.bat1_ch[i] * self.m.bat1_dch[i] == 0

    def ch_x_dch2 (self, model, i):
        return self.m.bat2_ch[i] * self.m.bat2_dch[i] == 0

    def ess12(self, model, i):
        return self.m.bat1_dch[i] - self.m.bat2_ch[i] - self.m.bat1_dch[i] == 0 #m.bat1_dch[i] - m.bat2_ch[i] - m.bat1_dch[i] <= 0 

    def ess21(self, model, i):
        return self.m.bat2_dch[i] - self.m.bat1_ch[i] - self.m.bat2_dch[i] == 0 

    #если СНЭ заряжена не на 100%, не ограничиваем инверторы СЭС 
    def curtailment_control1 (self, model, i):
        return self.m.PV1[i]+ self.m.PV2[i]+self.m.PV3[i]+self.m.PV4[i]+self.m.PV5[i]+self.m.PV6[i]+self.m.PV7[i] - reading.init_data_import()[1][i] - self.m.bat1_ch[i]/reading.ESS_inv  <= 0 

    def curtailment_control2 (self, model, i):
        return self.m.PV1[i]+ self.m.PV2[i]+self.m.PV3[i]+self.m.PV4[i]+self.m.PV5[i]+self.m.PV6[i]+self.m.PV7[i] - reading.init_data_import()[1][i] - self.m.bat2_ch[i]/reading.ESS_inv  <= 0 

    def d1_availability (self, model, i):
        return self.m.u1[i] == self.m.u1[i] * reading.init_data_import()[7]

    def d2_availability (self, model, i):
        return self.m.u2[i] == self.m.u2[i] * reading.init_data_import()[11]

    def d3_availability (self, model, i):
        return self.m.u3[i] == self.m.u3[i] * reading.init_data_import()[15]

    def d4_availability (self, model, i):
        return self.m.u4[i] == self.m.u4[i] * reading.init_data_import()[19]


    def ess1_availability (self, model, i):
        return self.m.bat1_dch[i] + self.m.bat1_ch[i] == (self.m.bat1_dch[i] + self.m.bat1_ch[i]) * reading.init_data_import()[20]

    def ess2_availability (self, model, i):
        return self.m.bat2_dch[i] + self.m.bat2_ch[i] == (self.m.bat2_dch[i] + self.m.bat2_ch[i]) * reading.init_data_import()[21]

    def cycle1(self, model, i):
        return self.m.soc1[reading.T1+reading.T2-reading.T1-1] >= reading.soc1_after

    def cycle2(self, model, i):
        return self.m.soc2[reading.T1+reading.T2-reading.T1-1] >= reading.soc2_after

    def as_one1(self, model, i):
        return self.m.bat1_dch[i] == self.m.bat2_dch[i]

    def as_one2(self, model, i):
        return self.m.bat1_ch[i] == self.m.bat2_ch[i]

    def unit_commitment(self):
 

        self.m.x1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU1_pmax))
        self.m.u1 = pyo.Var(self.m.T, domain=pyo.Binary)
        
        self.m.x2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU2_pmax))
        self.m.u2 = pyo.Var(self.m.T, domain=pyo.Binary)
        
        self.m.x3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU3_pmax))
        self.m.u3 = pyo.Var(self.m.T, domain=pyo.Binary)
        
        self.m.x4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU4_pmax))
        self.m.u4 = pyo.Var(self.m.T, domain=pyo.Binary)
        
        self.m.bat1_dch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        self.m.bat1_ch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        
        self.m.bat2_dch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        self.m.bat2_ch = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        
        self.m.soc1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (reading.bat1_dod, 100))
        self.m.soc2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (reading.bat2_dod, 100))
        
        self.m.suc1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_startup_cost))
        self.m.suc2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_startup_cost))
        self.m.suc3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_startup_cost))
        self.m.suc4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_startup_cost))
        
        self.m.sdc1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_shutdown_cost))
        self.m.sdc2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_shutdown_cost))
        self.m.sdc3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_shutdown_cost))
        self.m.sdc4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_shutdown_cost))
        
        self.m.PV1 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        self.m.PV2 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        self.m.PV3 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        self.m.PV4 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        self.m.PV5 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        self.m.PV6 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        self.m.PV7 = pyo.Var(self.m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        
        #m.PV1_s = pyo.Var(m.T, domain=pyo.Binary)
        #m.PV2_s = pyo.Var(m.T, domain=pyo.Binary)
        
        
        # целевая функция
        self.m.cost = pyo.Objective(expr = sum(reading.Fuel_price*((reading.DGU12_a*reading.DGU1_pmax*self.m.u1[t] + reading.DGU12_b*self.m.x1[t]) + (reading.DGU12_a*reading.DGU2_pmax*self.m.u2[t] + reading.DGU12_b*self.m.x2[t]) +
                                          (reading.DGU34_a*reading.DGU3_pmax*self.m.u3[t] + reading.DGU34_b*self.m.x3[t]) + (reading.DGU34_a*reading.DGU4_pmax*self.m.u4[t] + reading.DGU34_b*self.m.x4[t])) + self.m.suc1[t] +
                                          self.m.suc2[t] + self.m.suc3[t] + self.m.suc4[t] + self.m.sdc1[t] +
                                          self.m.sdc2[t] + self.m.sdc3[t] + self.m.sdc4[t]
                                          #self.m.u1[t]*100 + self.m.u2[t]*100 + self.m.u3[t]*100 + self.m.u4[t]*100
                                            #27432 * 0.000033 * (self.m.bat1_ch[t] + self.m.bat1_dch[t]) + 27432 * 0.000033 * (
                                             #self.m.bat2_ch[t] + self.m.bat2_dch[t])  # пока здесь указаны левые цифры


                                          for t in self.m.T), sense=pyo.minimize)
        
        
        self.m.demand = pyo.Constraint(self.m.T, rule=self.balance)
             

        
        self.m.lb1 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU1_pmin*m.u1[t] <= m.x1[t])
        self.m.ub1 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU1_pmax*m.u1[t] >= m.x1[t])
        self.m.lb2 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU2_pmin*m.u2[t] <= m.x2[t])
        self.m.ub2 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU2_pmax*m.u2[t] >= m.x2[t])
        self.m.lb3 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU3_pmin*m.u3[t] <= m.x3[t])
        self.m.ub3 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU3_pmax*m.u3[t] >= m.x3[t])
        self.m.lb4 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU4_pmin*m.u4[t] <= m.x4[t])
        self.m.ub4 = pyo.Constraint(self.m.T, rule=lambda m, t: reading.DGU4_pmax*m.u4[t] >= m.x4[t])

        self.m.pv1 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV1[t] <= 0)  # 7 - число инверторов СЭС
        self.m.pv2 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV2[t] <= 0)
        self.m.pv3 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV3[t] <= 0)
        self.m.pv4 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV4[t] <= 0)
        self.m.pv5 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV5[t] <= 0)
        self.m.pv6 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV6[t] <= 0)
        self.m.pv7 = pyo.Constraint(self.m.T, rule=lambda m, t: m.PV7[t] <= 0)
        
        self.m.pv1_curtailment = pyo.Constraint(self.m.T, rule=self.curtailment_control1)
        self.m.pv2_curtailment = pyo.Constraint(self.m.T, rule=self.curtailment_control2)
        
        self.m.min_up_time_d1 = pyo.Constraint(self.m.T, rule=self.d1_min_up_time_c)
        self.m.min_up_time_d2 = pyo.Constraint(self.m.T, rule=self.d2_min_up_time_c)
        self.m.min_up_time_d3 = pyo.Constraint(self.m.T, rule=self.d3_min_up_time_c)
        self.m.min_up_time_d4 = pyo.Constraint(self.m.T, rule=self.d4_min_up_time_c)
        
        self.m.min_down_time_d1 = pyo.Constraint(self.m.T, rule=self.d1_min_down_time_c)
        self.m.min_down_time_d2 = pyo.Constraint(self.m.T, rule=self.d2_min_down_time_c)
        self.m.min_down_time_d3 = pyo.Constraint(self.m.T, rule=self.d3_min_down_time_c)
        self.m.min_down_time_d4 = pyo.Constraint(self.m.T, rule=self.d4_min_down_time_c)
        
        self.m.su1 = pyo.Constraint(self.m.T, rule=self.d1_start_up_cost)
        self.m.su2 = pyo.Constraint(self.m.T, rule=self.d2_start_up_cost)
        self.m.su3 = pyo.Constraint(self.m.T, rule=self.d3_start_up_cost)
        self.m.su4 = pyo.Constraint(self.m.T, rule=self.d4_start_up_cost)
        
        self.m.sd1 = pyo.Constraint(self.m.T, rule=self.d1_shut_down_cost)
        self.m.sd2 = pyo.Constraint(self.m.T, rule=self.d2_shut_down_cost)
        self.m.sd3 = pyo.Constraint(self.m.T, rule=self.d3_shut_down_cost)
        self.m.sd4 = pyo.Constraint(self.m.T, rule=self.d4_shut_down_cost)
        
        self.m.d1_ava = pyo.Constraint(self.m.T, rule=self.d1_availability)
        self.m.d2_ava = pyo.Constraint(self.m.T, rule=self.d2_availability)
        self.m.d3_ava = pyo.Constraint(self.m.T, rule=self.d3_availability)
        self.m.d4_ava = pyo.Constraint(self.m.T, rule=self.d4_availability)
        
        self.m.soc1_ctrl = pyo.Constraint(self.m.T, rule=self.soc1_ctrl)
        self.m.soc2_ctrl = pyo.Constraint(self.m.T, rule=self.soc2_ctrl)
        self.m.chdch1 = pyo.Constraint(self.m.T, rule=self.ch_x_dch1)
        self.m.chdch2 = pyo.Constraint(self.m.T, rule=self.ch_x_dch2)
        #m.ess12 = pyo.Constraint(m.T, rule=ess12)
        #m.ess21 = pyo.Constraint(m.T, rule=ess21)
        self.m.ess1_ava = pyo.Constraint(self.m.T, rule=self.ess1_availability)
        self.m.ess2_ava = pyo.Constraint(self.m.T, rule=self.ess2_availability)
        #m.d1_cstr1 = pyo.Constraint(m.T, rule=d1_cstr1)
        #m.curt1 = pyo.Constraint(m.T, rule=curtailment_control1) 
        #m.ess1_cyc = pyo.Constraint(m.T, rule=cycle1)
        #m.ess2_cyc = pyo.Constraint(m.T, rule=cycle2)
        
        self.m.as_one1 = pyo.Constraint(self.m.T, rule=self.as_one1)
        self.m.as_one2 = pyo.Constraint(self.m.T, rule=self.as_one2)

        #self.m.pprint()

        return self.m
        
class optimization:

    #m1 = opt_pyomo_formulating.unit_commitment(self)

    def __init__(self):
        self.fls = reading.files()
        self.entity = opt_pyomo_formulating()


    def optimizer(self):
        
        #print(os.getcwd())
        opt =  pyo.SolverFactory('scipampl',executable=os.getcwd()+'\scipampl-7.0.0.win.x86_64.intel.opt.spx2')
        #opt =  pyo.SolverFactory('couenne', executable=os.getcwd() +'\\couenne67.exe')
        #opt =  pyo.SolverFactory('couenne', executable=os.getcwd() +'\\scipampl-7.0.0.win.x86_64.intel.opt.spx2')
        print()
        print('&*&*&*&*&*&*&*&*&*&*&*&*&*&*&')
        print('ПОИСК ОПТИМАЛЬНОГО РЕШЕНИЯ...')
        print('&*&*&*&*&*&*&*&*&*&*&*&*&*&*&')
        print()
        results = opt.solve(self.entity.unit_commitment(), logfile='optimizer_log.log', tee=True, timelimit=600, keepfiles=True)




        results.write()
        
        #pyo.SolverFactory('mindtpy').solve(m, mip_solver='cbc', nlp_solver='ipopt', tee=True).write()
        

        # Extract model output in list
        output = []
        Date = list([0,1,2,3,4])
        output.append([Date, self.entity.m.x1.get_values().values(), self.entity.m.x2.get_values().values(), 
                        self.entity.m.x3.get_values().values(), self.entity.m.x4.get_values().values(), self.entity.m.bat1_dch.get_values().values(),
                        self.entity.m.bat1_ch.get_values().values()]) 
                        #m.bat1_dch.get_values().values(), m.bat1_ch.get_values().values(), ])

        if (results.solver.status == SolverStatus.ok) or (results.solver.termination_condition == TerminationCondition.optimal): #sum(np.fromiter(self.entity.m.x1.get_values().values(), dtype=float)) is not None:
        #if 1<2:

            load_fcst = forecasters.Load_forecaster(load_files).get_hourly_forecast()
            self_consumption_fcst = forecasters.Load_forecaster(load_files).self_consumption_forecast()

            dfout = pd.DataFrame()
            #dfout.index=Load[T].index
            #dfout['Load'] = reading.init_data_import()[0][:,0]
            #dfout['Нагрузка'] = load_fcst
            dfout['Нагрузка'] = load_fcst
            #dfout['Собственные нужды без учета СНЭ'] = self_consumption_fcst



            dfout['ДГУ1'] = self.entity.m.x1.get_values().values()
            dfout['ДГУ2'] = self.entity.m.x2.get_values().values()
            dfout['ДГУ3'] = self.entity.m.x3.get_values().values()
            dfout['ДГУ4'] = self.entity.m.x4.get_values().values()
            # dfout['d1_suc'] = .suc1.get_values().values()
            # dfout['d2_suc'] = m.suc2.get_values().values()
            # dfout['d3_suc'] = m.suc3.get_values().values()
            # dfout['d4_suc'] = m.suc4.get_values().values()
            # dfout['d1_sdc'] = m.sdc1.get_values().values()
            # dfout['d2_sdc'] = m.sdc2.get_values().values()
            # dfout['d3_sdc'] = m.sdc3.get_values().values()
            # dfout['d4_sdc'] = m.sdc4.get_values().values()
            dfout['Разряд СНЭ 1'] = self.entity.m.bat1_dch.get_values().values()
            dfout['Заряд СНЭ 1'] = self.entity.m.bat1_ch.get_values().values()
            dfout['Разряд СНЭ 2'] = self.entity.m.bat2_dch.get_values().values()
            dfout['Заряд СНЭ 2'] = self.entity.m.bat2_ch.get_values().values()
            dfout['Уровень заряда СНЭ 1'] = self.entity.m.soc1.get_values().values()
            dfout['Уровень заряда СНЭ 2'] = self.entity.m.soc2.get_values().values()
            dfout['Инвертор СЭС 1'] = 0
            dfout['Инвертор СЭС 2'] = 0
            dfout['Инвертор СЭС 3'] = 0
            dfout['Инвертор СЭС 4'] = 0
            dfout['Инвертор СЭС 5'] = 0
            dfout['Инвертор СЭС 6'] = 0
            dfout['Инвертор СЭС 7'] = 0
            #dfout['bat1_ch'] = -dfout['bat1_ch']
            #dfout['bat2_ch'] = -dfout['bat2_ch']
            #dfout['dd1'] = m.u1.get_values().values()


            #print(self_consumption_fcst['Наружное освещение'])

            #dfout['Собственные нужды'] = dfout['Собственные нужды без учета СНЭ'] + dfout['Заряд_СНЭ 1'] + dfout['Заряд_СНЭ 2']
            dfout['Наружное освещение'] = self_consumption_fcst['Наружное освещение']

            dfout['Отопление/кондиционирование конт. СНЭ'] = self_consumption_fcst['Отопление контейнера СНЭ']
            dfout['Отопление/кондиционирование конт. СЭС'] = self_consumption_fcst['Отопление контейнера СЭС']
            dfout['Прочее'] = self_consumption_fcst['Прочее']

            #print('OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOKKKKKKKKKKKKKKKKKKKK')
            #print(dfout)

            dfout.index = load_fcst.index

            out0 = reading.output_file_read()[0]
            out = reading.output_file_read()[1][0]            

            #print(dfout)

            #dfout.to_csv('dfout.csv')

            dfout.groupby(['ДГУ1', 'ДГУ2', 'ДГУ3', 'ДГУ4', 'Инвертор СЭС 1',
                        'Инвертор СЭС 2', 'Инвертор СЭС 3', 'Инвертор СЭС 4',
                        'Инвертор СЭС 5', 'Инвертор СЭС 7', 'Разряд СНЭ 1', 'Разряд СНЭ 2']).size().unstack().plot(kind='bar', stacked=True)

            #dfout.plot(kind='bar', stacked=True)
            #plt.show()
            #out = list(out[0])
        
            out[0] = dfout.iloc[0][5]+dfout.iloc[0][6]
            out[1] = dfout.iloc[0][7]+dfout.iloc[0][8]
            out[2] = 1
            out[3] = 1
            out[4] = 0
            out[5] = 0
            out[6] = 1
            out[7] = 1
            out[8] = bool(np.fromiter(self.entity.m.u1.get_values().values(), dtype=float)[0])
            out[9] = bool(np.fromiter(self.entity.m.u2.get_values().values(), dtype=float)[0])
            out[10] = bool(np.fromiter(self.entity.m.u3.get_values().values(), dtype=float)[0])
            out[11] = bool(np.fromiter(self.entity.m.u4.get_values().values(), dtype=float)[0])
            out[12] = int(100*dfout.iloc[0][11]/136)
            out[13] = int(100*dfout.iloc[0][12]/136)
            out[14] = int(100*dfout.iloc[0][13]/136)
            out[15] = int(100*dfout.iloc[0][14]/136)
            out[16] = int(100*dfout.iloc[0][15]/136)
            out[17] = int(100*dfout.iloc[0][16]/136)
            out[18] = int(100*dfout.iloc[0][17]/136)
            out[19] = 128
            out[20] = 128
            out[21] = 128
            out[22] = 128
            out[23] = 128
            out[24] = 128
            out[25] = 128
            out[26] = 0
            out[27] = 0
            out[28] = 0
            out[29] = 0
            out[30] = 0
            out[31] = 0
            out[32] = 0
            out[33] = 1
            out[34] = 1
            out[35] = 1
            out[36] = 1
            out[37] = 1
            out[38] = 1
            out[39] = 1
            out[40] = 0
            out[41] = 0
            out[42] = 0
            out[43] = 0
            out[44] = 0
            out[45] = 0
            out[46] = 0

            out[47] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logging.info(str(out[47]))
            logging.info(type(out[47]))

            out0[:]=[out]

            out0['DT'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logging.info('Оптимальное решение найдено...')

            print()
            print()
            print('##############################')
            print('ОПТИМАЛЬНОЕ РЕШЕНИЕ НАЙДЕНО...')
            print('##############################')
            print()

            try:
                bazah = db_readeru.DB_connector()
                bazah.decision_to_sql(out)
                logging.info('Оптимальное решение записано в БД...')
                print()
                print('Выходные данные сохранены в БД')
                print()
            except Exception as e:
                logging.error(traceback.format_exc())
                print('--!!!--')
                print('Ошибка при записи оптимального решения в БД!')
                print('--!!!--')

            #out0.to_csv(reading.files()[3],sep=';',index=False, decimal=',')

            #np.savetxt("C:\PROJECT\Path.csv", np.round(np.genfromtxt('C:\PROJECT\PathFromWrite.csv', delimiter=',')**2, decimals=0), delimiter=",", fmt='%i')
            #originalTime = os.path.getmtime(fileName)

            print()
            print('Следующая попытка через 15 секунд...')
            print()
            try:
                if 2>1:
                    ax[0].cla()
                    ax[1].cla()
                    ax[2].cla()
                    ax[3].cla()
                    ax[4].cla()
                    ax[5].cla()
                    ax[6].cla()
                    ax[7].cla()

                    plt.rcParams['axes.grid'] = True
                    #print(dfout)
                    fig.suptitle('Оптимальный сценарий. Получен в ' + datetime.now().strftime("%H:%M %d-%m-%Y"))
                    #ax[0].bar(dfout.index, dfout['Нагрузка'], width=10)
                    ax[0].set_xlim(reading.T1, reading.T2)
                    ax[0].set_ylim(0, 1.1 * 900)
                    dfout.index = dfout.index.strftime('%b %d,\n%H:%M')
                    dfout['Нагрузка'].plot.bar(ax=ax[0], rot=1)
                    #ax[0].set_xticks(dfout.index)
                    #ax[0].xaxis.set_major_formatter(mdates.DateFormatter("%m %H:%M"))
                    #ax[0].xaxis.set_minor_formatter(mdates.DateFormatter("%m %H:%M"))
                    #date_form = DateFormatter("%m-%d %H:%M")
                    #ax[0].xaxis.set_major_formatter(date_form)



                    #ax[0].bar(reading.T, [reading.init_data_import()[0][:,0][t] for t in reading.T])

                    #ax[0].plot(ax[1].get_xlim(), np.array([100, 100]), 'r--')
                    #ax[0].plot(ax[1].get_xlim(), np.array([30, 30]), 'r--')
                    ax[0].set_title('Нагрузка + собственные нужды (прогноз)')
                    ax[0].set_ylabel('кВт')

                    #ax[1].bar(reading.T, [self.entity.m.x1[t]() for t in reading.T])
                    ax[1].set_xlim(reading.T1, reading.T2)
                    ax[1].set_ylim(0, 1.1*reading.DGU1_pmax)
                    ax[1].plot(ax[1].get_xlim(), np.array([reading.DGU1_pmax, reading.DGU1_pmax]), 'r--')
                    ax[1].plot(ax[1].get_xlim(), np.array([reading.DGU1_pmin, reading.DGU1_pmin]), 'r--')
                    ax[1].set_title('ДГУ1')
                    dfout['ДГУ1'].plot.bar(ax=ax[1], rot=1)
                    ax[1].set_ylabel('Активная\nмощность, кВт')

                    # ax[2].bar(reading.T, [self.entity.m.x1[t]() for t in reading.T])
                    ax[2].set_xlim(reading.T1, reading.T2)
                    ax[2].set_ylim(0, 1.1 * reading.DGU2_pmax)
                    ax[2].plot(ax[2].get_xlim(), np.array([reading.DGU2_pmax, reading.DGU2_pmax]), 'r--')
                    ax[2].plot(ax[2].get_xlim(), np.array([reading.DGU2_pmin, reading.DGU2_pmin]), 'r--')
                    ax[2].set_title('ДГУ2')
                    dfout['ДГУ2'].plot.bar(ax=ax[2], rot=1)
                    ax[2].set_ylabel('Активная\nмощность, кВт')

                    # ax[3].bar(reading.T, [self.entity.m.x1[t]() for t in reading.T])
                    ax[3].set_xlim(reading.T1, reading.T2)
                    ax[3].set_ylim(0, 1.1 * reading.DGU3_pmax)
                    ax[3].plot(ax[3].get_xlim(), np.array([reading.DGU3_pmax, reading.DGU3_pmax]), 'r--')
                    ax[3].plot(ax[3].get_xlim(), np.array([reading.DGU3_pmin, reading.DGU3_pmin]), 'r--')
                    ax[3].set_title('ДГУ3')
                    dfout['ДГУ3'].plot.bar(ax=ax[3], rot=1)
                    ax[3].set_ylabel('Активная\nмощность, кВт')

                    # ax[4].bar(reading.T, [self.entity.m.x1[t]() for t in reading.T])
                    ax[4].set_xlim(reading.T1, reading.T2)
                    ax[4].set_ylim(0, 1.1 * reading.DGU4_pmax)
                    ax[4].plot(ax[4].get_xlim(), np.array([reading.DGU4_pmax, reading.DGU4_pmax]), 'r--')
                    ax[4].plot(ax[4].get_xlim(), np.array([reading.DGU4_pmin, reading.DGU4_pmin]), 'r--')
                    ax[4].set_title('ДГУ4')
                    dfout['ДГУ4'].plot.bar(ax=ax[4], rot=1)
                    ax[4].set_ylabel('Активная\nмощность, кВт')

                    #ax[5].bar(reading.T, [self.entity.m.pv1[t]()+ self.entity.m.pv2[t]()+self.entity.m.pv3[t]()+self.entity.m.pv4[t]()+self.entity.m.pv5[t]()+self.entity.m.pv6[t]()+self.entity.m.pv7[t]() for t in reading.T])
                    ax[5].set_xlim(reading.T1, reading.T2)
                    ax[5].set_ylim(0, 1.1*1000)
                    ax[5].bar(reading.T, [reading.init_data_import()[1][t] for t in reading.T], alpha=0.5)
                    dfout[['Инвертор СЭС 1', 'Инвертор СЭС 2', 'Инвертор СЭС 3', 'Инвертор СЭС 4', 'Инвертор СЭС 5', 'Инвертор СЭС 6', 'Инвертор СЭС 7']].plot.bar(ax=ax[5], rot=1, legend=False)
                    #ax[5].plot(ax[5].get_xlim(), np.array([0, 0]), 'r--')
                    ax[5].set_ylabel('Активная\nмощность, кВт')
                    ax[5].set_title('СЭС')

                    ax2 = ax[6].twinx()
                    ax[6].set_xlim(reading.T1, reading.T2)
                    ax[6].set_ylim(-1.1 * 150, 1.1 * 150)
                    ax2.set_ylim(0, 105)
                    #ax2.plot(reading.T, [self.entity.m.soc1[t]() for t in reading.T], color='red', linewidth=2, label='Уровень заряда')
                    #ax[6].bar(reading.T, [self.entity.m.bat1_dch[t]()-self.entity.m.bat1_ch[t]() for t in reading.T])
                    (dfout['Разряд СНЭ 1'] - dfout['Заряд СНЭ 1']).plot.bar(ax=ax[6], rot=1)
                    dfout['Уровень заряда СНЭ 1'].plot(ax=ax2, rot=1, legend=True)
                    #ax[6].plot(ax[1].get_xlim(), np.array([160, 160]), 'r--')
                    ax2.plot(ax[6].get_xlim(), np.array([30, 30]), 'r--')
                    ax[6].set_title('СНЭ1')
                    ax[6].set_ylabel('Активная\nмощность, кВт')
                    ax2.set_ylabel('Уровень заряда\nСНЭ1, %')

                    ax3 = ax[7].twinx()
                    ax[7].set_xlim(reading.T1, reading.T2)
                    ax[7].set_ylim(-1.1*150, 1.1*150)
                    ax3.set_ylim(0, 105)
                    #ax3.plot(reading.T, [self.entity.m.soc2[t]() for t in reading.T], color='red', linewidth=2)
                    #ax[7].bar(reading.T, [self.entity.m.bat2_dch[t]()-self.entity.m.bat2_ch[t]() for t in reading.T])
                    (dfout['Разряд СНЭ 2'] - dfout['Заряд СНЭ 2']).plot.bar(ax=ax[7], rot=1)
                    dfout['Уровень заряда СНЭ 2'].plot(ax=ax3, rot=1, legend=True)
                    #ax[7].plot(ax[1].get_xlim(), np.array([160, 160]), 'r--')
                    ax3.plot(ax[7].get_xlim(), np.array([30, 30]), 'r--')
                    ax[7].set_title('СНЭ2')
                    ax[7].set_ylabel('Активная\nмощность, кВт')
                    ax3.set_ylabel('Уровень заряда\nСНЭ2, %')

                    # u1 = np.fromiter(self.entity.m.u1.get_values().values(), dtype=float)
                    # u2 = np.fromiter(self.entity.m.u2.get_values().values(), dtype=float)
                    # u3 = np.fromiter(self.entity.m.u3.get_values().values(), dtype=float)
                    # u4 = np.fromiter(self.entity.m.u4.get_values().values(), dtype=float)

                    # def autolabel(rects):
                    #     """
                    #     Attach a text label above each bar displaying its height
                    #     """
                    #     for rect in rects:
                    #         height = rect.get_height()
                    #         ax.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                    #                 '%d' % int(height),
                    #                 ha='center', va='bottom')

                    for p in ax[0].patches:
                        ax[0].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')

                    for p in ax[1].patches:
                        ax[1].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')

                    for p in ax[2].patches:
                        ax[2].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')

                    for p in ax[3].patches:
                        ax[3].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')

                    for p in ax[4].patches:
                        ax[4].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')

                    # for p in ax[5].patches:
                    #     ax[5].annotate(np.round(p.get_height(), decimals=2),
                    #               (p.get_x() + p.get_width() / 2., p.get_height()),
                    #                    ha='center', va='center', xytext=(0, 10),
                    #                                                  textcoords='offset points')

                    for p in ax[6].patches:
                        ax[6].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')

                    for p in ax[7].patches:
                        ax[7].annotate(np.round(p.get_height(), decimals=2),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                       ha='center', va='center', xytext=(0, 10),
                                                                     textcoords='offset points')




                    fig.tight_layout()
                    fig.savefig('C:\project\opt_schedule.png')
                    print('График оптимального сценария сохранен в С:\project\opt_schedule.png')
                    print()
                    #plt.show()
                    plt.close(fig)
                    #ax2.cla()
                    #ax3.cla()
                    time.sleep(10)
            except Exception as e:
                logging.error(traceback.format_exc())
                print('--!!!--')
                print('Ошибка при построении графика с прогнозом!')
                print('--!!!--')



        elif (results.solver.termination_condition == TerminationCondition.infeasible):
            print()
            print()
            print('////////////////////////////////////////////////////////////////////////')
            print('ОШИБКА! ЗАДАЧА ОПТИМИЗАЦИИ С ТЕКУЩИМИ ВХОДНЫМИ ДАННЫМИ НЕ ИМЕЕТ РЕШЕНИЯ!')
            print('////////////////////////////////////////////////////////////////////////')
            print()
            #fls = reading.files()
            logging.error(traceback.format_exc())
    
    def optimizer_cycling(self):

        #fileName = self.fls[2]
        # originalTime = os.path.getmtime(fileName) #считываем время изменения файла filename
        # with open(fileName) as f0:
            # file0 = f0.read()
        while(True):
            try:
                # time.sleep(5)
                # with open(fileName) as f1:
                #     print('read0')
                #     file1 = f1.read()
                #     print(file1[0])
                # if file1 != file0:

                # if (os.path.getmtime(fileName) > originalTime):
                    #print('I am trying!')
                    #print('file ' + fls[2] + 'was changed')
                #ddd = reading.init_data_import()
                #opto = optimization()
                self.optimizer()
                #     print('++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                #     print('Считывание входных данных возобновится через 10 секунд')
                #     print('++++++++++++++++++++++++++++++++++++++++++++++++++++++')


                # time.sleep(5)
                # with open(fileName) as f0:
                #     print('read')
                #     file0 = f0.read()
                #     print(file0[0])

            #         originalTime = os.path.getmtime(fileName)
            except Exception as e:
                #logging.basicConfig(filename=self.fls[0]+'log.txt', level=logging.DEBUG,
                                         #format='%(asctime)s %(levelname)s %(name)s %(message)s')
                #logger=logging.getLogger(__name__)
                logging.error(traceback.format_exc())

                #if not os.path.exists(self.fls[0]+'ошибки'):
                #    os.makedirs(self.fls[0]+'ошибки')
                #dst=os.path.join(self.fls[0]+'ошибки\\')
                #copyfile(self.fls[2], dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'imported_file.csv')
                #copyfile(self.fls[3], dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'exported_file.csv')
                print()
                print('//////////////////////////////////////////////////////////////////////////////////')
                print('ОШИБКА ВВОДА-ВЫВОДА ЛИБО ЗАДАЧА ОПТИМИЗАЦИИ С ТЕКУЩИМИ ВХОДНЫМИ ДАННЫМИ НЕРЕШАЕМА!')
                print('//////////////////////////////////////////////////////////////////////////////////')
                print()
                print('******************************************************')
                print('Считывание входных данных возобновится через 65 секунд')
                print('******************************************************')
                print()
                #plt.plot(ddd[0])
                #plt.plot(ddd[1])
                #plt.show()

                #print('&&&&&&&&&&&&&&&&&&&&&&')
                #print(reading.init_data_import())

                time.sleep(65)

#сама функция оптимизации
def the_process():
    #fls = reading.files()
    #ddd = reading.init_data_import()
    #print(ddd)
    #первоначальное считывание. Можно потом убрать этот блок
    #try:
    opto = optimization()

    print()
    print('&*&*&*&*&*&*&*&*&*&*&*&*&*&*&')
    print('ПОДКЛЮЧЕНИЕ К БД УСПЕШНО.....')
    print('&*&*&*&*&*&*&*&*&*&*&*&*&*&*&')
    print()

    opto.optimizer()
    # except Exception as e:
    #
    #     logging.error(traceback.format_exc())
    #
    #     if not os.path.exists(fls[0]+'ошибки'):
    #         os.makedirs(fls[0]+'ошибки')
    #     dst=os.path.join(fls[0]+'ошибки\\')
    #     copyfile(fls[2], dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'imported_file.csv')
    #     copyfile(fls[3], dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'exported_file.csv')
    #     print()
    #     print('------')
    #     print('ОШИБКА! ЗАДАЧА ОПТИМИЗАЦИИ НЕ ИМЕЕТ РЕШЕНИЯ!')
    #     print('------')
    #     print()
    #     print('************************************')
    #     print('Следующая попытка через 65 секунд...')
    #     print('************************************')
    #     print()
    #     #plt.plot(ddd[0])
    #     #plt.plot(ddd[1])
    #     #plt.show()
    #     #print('&&&&&&&&&&&&&&&&&&&&&&')
    #     #print(reading.init_data_import()[0][:, 0][0])
    opto.optimizer_cycling()

if __name__ == '__main__':
    multiprocessing.freeze_support()

    p = multiprocessing.Process(target=counter_time)
    
    p1 = multiprocessing.Process(target=the_process)
    p.start()
    p1.start()
    # if flag == 1:
    #     p.stop()
