import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import os.path
import pyomo
import pyomo.environ as pyo
#import pvlib
import math
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

start_time = time.time()

d1_min_up_time = 3
d2_min_up_time = 3 
d3_min_up_time = 3 
d4_min_up_time = 3

d1_min_down_time = 3
d2_min_down_time = 3 
d3_min_down_time = 3 
d4_min_down_time = 3 

flag = 0


def counter_time():
    while True:
        print('')
        print('*****************************************')
        print('Модуль в работе. Индикатор записан в файл')
        print('*****************************************')
        print('')
        time.sleep(10)
        print('')
        print('*****************************************')
        print('Модуль в работе. Индикатор записан в файл')
        print('*****************************************')
        print('')
        time.sleep(10)

##t1 = threading.Thread(target=counter_time)
##t1.daemon = True
###t2 = threading.Thread(target=counter_time)
##t1.start()
###t2.start()



class reading:

    Load=[0,0,0,0,0]
    PV=[0,0,0,0,0,0,0]

    output = []

    N = 4
    N = np.array([n for n in range(0, N)])
    T = np.array([t for t in range(0, 5)])
    T1 = 0
    T2 = 5

    p12 = np.arange(0, 321)
    p34 = np.arange(0, 521)
    p_PV = np.arange(0, 137)
    p_BESS = np.arange(0, 151)


    DGU1_pmax = 320 #кВт
    DGU1_pmin = 0.5*DGU1_pmax

    DGU2_pmax = 320 #кВт
    DGU2_pmin = 0.5*DGU2_pmax

    DGU3_pmax = 520 #кВт
    DGU3_pmin = 0.5*DGU3_pmax

    DGU4_pmax = 520 #кВт
    DGU4_pmin = 0.5*DGU4_pmax

    DGU1_fuel =  0.3031*p12
    DGU2_fuel =  0.3031*p12
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

    Fuel_price = 60 #цена за литр диз.топлива 
    #коэффициенты из расходных характеристик ДГУ
    DGU12_a = 0.0219
    DGU12_b = 0.3125
    DGU34_a = 0.049
    DGU34_b = 0.2788

    ESS_inv = 150

    bat1_dod = 50
    bat2_dod = 50

    soc1_after = 100
    soc1_after = 100

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

    
    def init_data_import(): #в эту функцию позже нужно добавить функции прогнозирования !!!
        fileName = 'C:\PROJECT\PathFromWrite.csv'
        try:
            if os.path.isfile(fileName):
                originalTime = os.path.getmtime(fileName)
                print('СТАРТ ОТСЛЕЖИВАНИЯ ИЗМЕНЕНИЙ', datetime.now())
                inn=np.genfromtxt((reading.conv(x) for x in open('C:\PROJECT\PathFromWrite.csv')), delimiter=';')
                out0=pd.read_csv('C:\PROJECT\Path.csv', delimiter=';')
                out=np.array(out0)
                
                print(inn)
                
                Load = [0,0,0,0,0]
                Load[0] = inn[0:6].sum()+inn[29:31].sum()+inn[43:47].sum()+inn[67]+inn[69]+inn[71]
                Load[1] = Load[0] + random.uniform(-65.0,65.0)*(-1)
                Load[2] = Load[0] + random.uniform(-65.0,65.0)*(-1)
                Load[3] = Load[0] + random.uniform(-65.0,65.0)*(-1)
                Load[4] = Load[0] + random.uniform(-65.0,65.0)*(-1)

                print(Load)
                
                PV=[inn[0:7].sum(), inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1), inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1),
                   inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1),inn[0:7].sum()+random.uniform(-5.0,5.0)*(-1)]
                soc1_before = inn[35]/10
                soc2_before = inn[36]/10

                if inn[51]==30 and inn[63]==1 and inn[43]!=0:
                    u1_start = 1
                    d1_up_before = 2
                    d1_down_before = 1
                else:
                    u1_start = 0
                    d1_up_before = 0
                    d1_down_before = 3
                if inn[52]==30 and inn[64]==1 and inn[44]!=0:
                    u2_start = 1
                    d2_up_before = 2
                    d2_down_before = 1
                else:
                    u2_start = 0
                    d2_up_before = 0
                    d2_down_before = 3
                if inn[53]==30 and inn[65]==1 and inn[45]!=0:
                    u3_start = 1
                    d3_up_before = 2
                    d3_down_before = 1
                else:
                    u3_start = 0
                    d3_up_before = 0
                    d3_down_before = 3
                if inn[54]==30 and inn[66]==1 and inn[46]!=0:
                    u4_start = 1
                    d4_up_before = 2
                    d4_down_before = 1
                else:
                    u4_start = 0
                    d4_up_before = 0
                    d4_down_before = 3

                #ava states
                d1_availability_state = inn[63]
                d2_availability_state = inn[64]
                d3_availability_state = inn[65]
                d4_availability_state = inn[66]

                ess1_availability_state = inn[41]
                ess2_availability_state = inn[42]

                return [Load, PV, soc1_before, soc2_before, u1_start, d1_up_before, d1_down_before, d1_availability_state, u2_start, d2_up_before, d2_down_before, d2_availability_state,
                u3_start, d3_up_before, d3_down_before, d3_availability_state,
                u4_start, d4_up_before, d4_down_before, d4_availability_state, ess1_availability_state, ess2_availability_state, soc1_before, soc2_before]
               
        except Exception as e:
            logging.basicConfig(filename='C:\PROJECT\log.txt', level=logging.DEBUG, 
                                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
            logger=logging.getLogger(__name__)
            logging.error(traceback.format_exc())

            if not os.path.exists('C:\PROJECT\ошибки'):
                os.makedirs('C:\PROJECT\ошибки')
            dst=os.path.join('C:\\', 'Project', 'ошибки\\')
            copyfile('C:\PROJECT\PathFromWrite.csv', dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'PathFromWrite.csv')
            copyfile('C:\PROJECT\Path.csv', dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'Path.csv')
            print()
            print('------')
            print('ОШИБКА! Не удалось считать файл с входными данными. Лог в C:\PROJECT\log.txt')
            print('------')
            print()
            print('******************************************************')
            print('Считывание входных данных возобновится через 30 секунд')
            print('******************************************************')
            print()
            time.sleep(30)
            flag = 1

            return 0
            #continue
        #break


class opt_pyomo_formulating:

    m = pyo.ConcreteModel()

    #Ограничения
    def balance(self, model, i):
        return m.x1[i] + m.x2[i] + m.x3[i] + m.x4[i] + m.bat1_dch[i] - m.bat1_ch[i] + m.bat2_dch[i] - m.bat2_ch[i] + m.PV1[i] + m.PV2[i] + m.PV3[i] + m.PV4[i] + m.PV5[i] + m.PV6[i] + m.PV7[i] == (np.asarray(reading.init_data_import()[0])[i]) 

    def d1_start_up_cost(model, i):
        if i == reading.T1:
            return m.suc1[i] >= reading.d12_startup_cost*(m.u1[i]-reading.init_data_import()[4])
        else:
            return m.suc1[i] >= reading.d12_startup_cost*(m.u1[i]-m.u1[i-1])
        
    def d2_start_up_cost(model, i):
        if i == reading.T1:
            return m.suc2[i] >= reading.d12_startup_cost*(m.u2[i]-reading.init_data_import()[8])
        else:
            return m.suc2[i] >= reading.d12_startup_cost*(m.u2[i]-m.u2[i-1])
        
    def d3_start_up_cost(model, i):
        if i == reading.T1:
            return m.suc3[i] >= reading.d34_startup_cost*(m.u3[i]-reading.init_data_import()[12])
        else:
            return m.suc3[i] >= reading.d34_startup_cost*(m.u3[i]-m.u3[i-1])
        
    def d4_start_up_cost(model, i):
        if i == reading.T1:
            return m.suc4[i] >= reading.d34_startup_cost*(m.u4[i]-reading.init_data_import()[16])
        else:
            return m.suc4[i] >= reading.d34_startup_cost*(m.u4[i]-m.u4[i-1])
        
    def d1_shut_down_cost(model, i):
        if i == reading.T1:
            return m.sdc1[i] >= reading.d12_shutdown_cost*(reading.init_data_import()[4]-m.u1[i])
        else:
            return m.sdc1[i] >= reading.d12_shutdown_cost*(m.u1[i-1]-m.u1[i])

    def d2_shut_down_cost(model, i):
        if i == reading.T1:
            return m.sdc2[i] >= reading.d12_shutdown_cost*(reading.init_data_import()[8]-m.u2[i])
        else:
            return m.sdc2[i] >= reading.d12_shutdown_cost*(m.u2[i-1]-m.u2[i])
        
    def d3_shut_down_cost(model, i):
        if i == reading.T1:
            return m.sdc3[i] >= reading.d34_shutdown_cost*(reading.init_data_import()[12]-m.u3[i])
        else:
            return m.sdc3[i] >= reading.d34_shutdown_cost*(m.u3[i-1]-m.u3[i])

    def d4_shut_down_cost(model, i):
        if i == reading.T1:
            return m.sdc4[i] >= reading.d34_shutdown_cost*(reading.init_data_import()[16]-m.u4[i])
        else:
            return m.sdc4[i] >= reading.d34_shutdown_cost*(m.u4[i-1]-m.u4[i])


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

    def d1_min_up_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[5] - reading.d1_min_up_time)*(reading.init_data_import()[4] - m.u1[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u1[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u1[j])
            return ((sum(uj) - reading.d1_min_up_time)*(m.u1[i-1] - m.u1[i])) >= 0
        else:
            return ((m.u1[i-1] + m.u1[i-2] + m.u1[i-3] - reading.d1_min_up_time)*(m.u1[i-1] - m.u1[i])) >= 0
        
    def d2_min_up_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[9] - reading.d2_min_up_time)*(reading.init_data_import()[8] - m.u2[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u2[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u2[j])
            return ((sum(uj) - reading.d2_min_up_time)*(m.u2[i-1] - m.u2[i])) >= 0
        else:
            return ((m.u2[i-1] + m.u2[i-2] + m.u2[i-3] - reading.d2_min_up_time)*(m.u2[i-1] - m.u2[i])) >= 0
        
    def d3_min_up_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[13] - reading.d3_min_up_time)*(reading.init_data_import()[12] - m.u3[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u3[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u3[j])
            return ((sum(uj) - reading.d3_min_up_time)*(m.u3[i-1] - m.u3[i])) >= 0
        else:
            return ((m.u3[i-1] + m.u3[i-2] + m.u3[i-3] - reading.d3_min_up_time)*(m.u3[i-1] - m.u3[i])) >= 0

    def d4_min_up_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[17] - reading.d4_min_up_time)*(reading.init_data_import()[16] - m.u4[i]) >= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u4[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u4[j])
            return ((sum(uj) - reading.d4_min_up_time)*(m.u4[i-1] - m.u4[i])) >= 0
        else:
            return ((m.u4[i-1] + m.u4[i-2] + m.u4[i-3] - reading.d4_min_up_time)*(m.u4[i-1] - m.u4[i])) >= 0

    def d1_min_down_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[6] + d1_min_down_time)*(-reading.init_data_import()[4] + m.u1[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u1[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u1[j])
            return ((sum(uj) - 2 + reading.d1_min_down_time)*(-m.u1[i-1] + m.u1[i])) <= 0
        else:
            return ((m.u1[i-1] + m.u1[i-2] + m.u1[i-3] - 3 + reading.d1_min_down_time)*(-m.u1[i-1] + m.u1[i])) <= 0

    def d2_min_down_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[10] + reading.d2_min_down_time)*(-reading.init_data_import()[8] + m.u2[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u2[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u2[j])
            return ((sum(uj) - 2 + reading.d2_min_down_time)*(-m.u2[i-1] + m.u2[i])) <= 0
        else:
            return ((m.u2[i-1] + m.u2[i-2] + m.u2[i-3] - 3 + reading.d2_min_down_time)*(-m.u2[i-1] + m.u2[i])) <= 0

    def d3_min_down_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[14] + reading.d3_min_down_time)*(-reading.init_data_import()[12] + m.u3[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u3[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u3[j])
            return ((sum(uj) - 2 + reading.d3_min_down_time)*(-m.u3[i-1] + m.u3[i])) <= 0
        else:
            return ((m.u3[i-1] + m.u3[i-2] + m.u3[i-3] - 3 + reading.d3_min_down_time)*(-m.u3[i-1] + m.u3[i])) <= 0

    def d4_min_down_time_c(model, i):
        if i == reading.T1:
            return (reading.init_data_import()[18] + reading.d4_min_down_time)*(-reading.init_data_import()[16] + m.u4[i]) <= 0
        elif i <= reading.T1+2:
            uj = []
            uj.append(m.u4[i-1])
            for j in range(reading.T1, i):
                uj.append(m.u4[j])
            return ((sum(uj) - 2 + reading.d4_min_down_time)*(-m.u4[i-1] + m.u4[i])) <= 0
        else:
            return ((m.u4[i-1] + m.u4[i-2] + m.u4[i-3] - 3 + reading.d4_min_down_time)*(-m.u4[i-1] + m.u4[i])) <= 0

    #ограничение глубины разряда СНЭ  
    def soc1_ctrl(model, i):
        if i == reading.T1:
            return m.soc1[i] == reading.init_data_import()[22] - 100*m.bat1_dch[i]/700 + 100*m.bat1_ch[i]/700
        else:
            return m.soc1[i] == m.soc1[i-1] - 100*m.bat1_dch[i]/700 + 100*m.bat1_ch[i]/700

    def soc2_ctrl(model, i):
        if i == reading.T1:
            return m.soc2[i] == reading.init_data_import()[23] - 100*m.bat2_dch[i]/700 + 100*m.bat2_ch[i]/700
        else:
            return m.soc2[i] == m.soc2[i-1] - 100*m.bat2_dch[i]/700 + 100*m.bat2_ch[i]/700
        
    #СНЭ не должна заряжаться и разряжаться одновременно     
    def ch_x_dch1 (model, i):
        return m.bat1_ch[i] * m.bat1_dch[i] == 0

    def ch_x_dch2 (model, i):
        return m.bat2_ch[i] * m.bat2_dch[i] == 0

    def ess12(model, i):
        return m.bat1_dch[i] - m.bat2_ch[i] - m.bat1_dch[i] == 0 #m.bat1_dch[i] - m.bat2_ch[i] - m.bat1_dch[i] <= 0 

    def ess21(model, i):
        return m.bat2_dch[i] - m.bat1_ch[i] - m.bat2_dch[i] == 0 

    #если СНЭ заряжена не на 100%, не ограничиваем инверторы СЭС 
    def curtailment_control1 (model, i):
        return m.PV1[i]+ m.PV2[i]+m.PV3[i]+m.PV4[i]+m.PV5[i]+m.PV6[i]+m.PV7[i] - reading.init_data_import()[1][i] - m.bat1_ch[i]/reading.ESS_inv  <= 0 

    def curtailment_control2 (model, i):
        return m.PV1[i]+ m.PV2[i]+m.PV3[i]+m.PV4[i]+m.PV5[i]+m.PV6[i]+m.PV7[i] - reading.init_data_import()[1][i] - m.bat2_ch[i]/reading.ESS_inv  <= 0 

    def d1_availability (model, i):
        return m.u1[i] == m.u1[i] * reading.init_data_import()[7]

    def d2_availability (model, i):
        return m.u2[i] == m.u2[i] * reading.init_data_import()[11]

    def d3_availability (model, i):
        return m.u3[i] == m.u3[i] * reading.init_data_import()[15]

    def d4_availability (model, i):
        return m.u4[i] == m.u4[i] * reading.init_data_import()[19]


    def ess1_availability (model, i):
        return m.bat1_dch[i] + m.bat1_ch[i] == (m.bat1_dch[i] + m.bat1_ch[i]) * reading.init_data_import()[20]

    def ess2_availability (model, i):
        return m.bat2_dch[i] + m.bat2_ch[i] == (m.bat2_dch[i] + m.bat2_ch[i]) * reading.init_data_import()[21]

    def cycle1(model, i):
        return m.soc1[T1+T2-T1-1] >= reading.soc1_after

    def cycle2(model, i):
        return m.soc2[T1+T2-T1-1] >= reading.soc2_after

    def as_one1(model, i):
        return m.bat1_dch[i] == m.bat2_dch[i] 

    def as_one2(model, i):
        return m.bat1_ch[i] == m.bat2_ch[i] 

    def unit_commitment():
        m = pyo.ConcreteModel()
        m.N = pyo.Set(initialize=reading.N)
        m.T = pyo.Set(initialize=reading.T)

        m.x1 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU1_pmax))
        m.u1 = pyo.Var(m.T, domain=pyo.Binary)
        
        m.x2 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU2_pmax))
        m.u2 = pyo.Var(m.T, domain=pyo.Binary)
        
        m.x3 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU3_pmax))
        m.u3 = pyo.Var(m.T, domain=pyo.Binary)
        
        m.x4 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.DGU4_pmax))
        m.u4 = pyo.Var(m.T, domain=pyo.Binary)
        
        m.bat1_dch = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        m.bat1_ch = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        
        m.bat2_dch = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        m.bat2_ch = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.ESS_inv))
        
        m.soc1 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (reading.bat1_dod, 100))
        m.soc2 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (reading.bat2_dod, 100))
        
        m.suc1 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_startup_cost))
        m.suc2 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_startup_cost))
        m.suc3 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_startup_cost))
        m.suc4 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_startup_cost))
        
        m.sdc1 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_shutdown_cost))
        m.sdc2 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d12_shutdown_cost))
        m.sdc3 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_shutdown_cost))
        m.sdc4 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.d34_shutdown_cost))
        
        m.PV1 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        m.PV2 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        m.PV3 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        m.PV4 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        m.PV5 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        m.PV6 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        m.PV7 = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds = (0, reading.PV_inv_Pmax))
        
        #m.PV1_s = pyo.Var(m.T, domain=pyo.Binary)
        #m.PV2_s = pyo.Var(m.T, domain=pyo.Binary)
        
        
        # целевая функция
        m.cost = pyo.Objective(expr = sum(reading.Fuel_price*((reading.DGU12_a*reading.DGU1_pmax*m.u1[t] + reading.DGU12_b*m.x1[t]) + (reading.DGU12_a*reading.DGU2_pmax*m.u2[t] + reading.DGU12_b*m.x2[t]) +
                                          (reading.DGU34_a*reading.DGU3_pmax*m.u3[t] + reading.DGU34_b*m.x3[t]) + (reading.DGU34_a*reading.DGU4_pmax*m.u4[t] + reading.DGU34_b*m.x4[t])) + m.suc1[t] +
                                          m.suc2[t] + m.suc3[t] + m.suc4[t] + m.sdc1[t] +
                                          m.sdc2[t] + m.sdc3[t] + m.sdc4[t] +
                                          27432*0.000033*(m.bat1_ch[t]+m.bat1_dch[t]) + 27432*0.000033*(m.bat2_ch[t]+m.bat2_dch[t]) + #пока здесь указаны левые цифры
                                          m.u1[t]*100 + m.u2[t]*100 + m.u3[t]*100 + m.u4[t]*100
                                          for t in m.T), sense=pyo.minimize)
        
        
        m.demand = pyo.Constraint(m.T, rule=opt_pyomo_formulating.balance)
        
        
        m.lb1 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU1_pmin*m.u1[t] <= m.x1[t])
        m.ub1 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU1_pmax*m.u1[t] >= m.x1[t])
        m.lb2 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU2_pmin*m.u2[t] <= m.x2[t])
        m.ub2 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU2_pmax*m.u2[t] >= m.x2[t])
        m.lb3 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU3_pmin*m.u3[t] <= m.x3[t])
        m.ub3 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU3_pmax*m.u3[t] >= m.x3[t])
        m.lb4 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU4_pmin*m.u4[t] <= m.x4[t])
        m.ub4 = pyo.Constraint(m.T, rule=lambda m, t: reading.DGU4_pmax*m.u4[t] >= m.x4[t])
        
        m.pv1 = pyo.Constraint(m.T, rule=lambda m, t: m.PV1[t] <= reading.PV[t]/7) #7 - число инверторов СЭС
        m.pv2 = pyo.Constraint(m.T, rule=lambda m, t: m.PV2[t] <= reading.PV[t]/7)
        m.pv3 = pyo.Constraint(m.T, rule=lambda m, t: m.PV3[t] <= reading.PV[t]/7)
        m.pv4 = pyo.Constraint(m.T, rule=lambda m, t: m.PV4[t] <= reading.PV[t]/7)
        m.pv5 = pyo.Constraint(m.T, rule=lambda m, t: m.PV5[t] <= reading.PV[t]/7)
        m.pv6 = pyo.Constraint(m.T, rule=lambda m, t: m.PV6[t] <= reading.PV[t]/7)
        m.pv7 = pyo.Constraint(m.T, rule=lambda m, t: m.PV7[t] <= reading.PV[t]/7)
        
        m.pv1_curtailment = pyo.Constraint(m.T, rule=curtailment_control1)
        m.pv2_curtailment = pyo.Constraint(m.T, rule=curtailment_control2)
        
        m.min_up_time_d1 = pyo.Constraint(m.T, rule=d1_min_up_time_c)
        m.min_up_time_d2 = pyo.Constraint(m.T, rule=d2_min_up_time_c)
        m.min_up_time_d3 = pyo.Constraint(m.T, rule=d3_min_up_time_c)
        m.min_up_time_d4 = pyo.Constraint(m.T, rule=d4_min_up_time_c)
        
        m.min_down_time_d1 = pyo.Constraint(m.T, rule=d1_min_down_time_c)
        m.min_down_time_d2 = pyo.Constraint(m.T, rule=d2_min_down_time_c)
        m.min_down_time_d3 = pyo.Constraint(m.T, rule=d3_min_down_time_c)
        m.min_down_time_d4 = pyo.Constraint(m.T, rule=d4_min_down_time_c)
        
        m.su1 = pyo.Constraint(m.T, rule=d1_start_up_cost)
        m.su2 = pyo.Constraint(m.T, rule=d2_start_up_cost)
        m.su3 = pyo.Constraint(m.T, rule=d3_start_up_cost)
        m.su4 = pyo.Constraint(m.T, rule=d4_start_up_cost)
        
        m.sd1 = pyo.Constraint(m.T, rule=d1_shut_down_cost)
        m.sd2 = pyo.Constraint(m.T, rule=d2_shut_down_cost)
        m.sd3 = pyo.Constraint(m.T, rule=d3_shut_down_cost)
        m.sd4 = pyo.Constraint(m.T, rule=d4_shut_down_cost)
        
        m.d1_ava = pyo.Constraint(m.T, rule=d1_availability)
        m.d2_ava = pyo.Constraint(m.T, rule=d2_availability)
        m.d3_ava = pyo.Constraint(m.T, rule=d3_availability)
        m.d4_ava = pyo.Constraint(m.T, rule=d4_availability)
        
        m.soc1_ctrl = pyo.Constraint(m.T, rule=soc1_ctrl)
        m.soc2_ctrl = pyo.Constraint(m.T, rule=soc2_ctrl)
        m.chdch1 = pyo.Constraint(m.T, rule=ch_x_dch1)
        m.chdch2 = pyo.Constraint(m.T, rule=ch_x_dch2)
        #m.ess12 = pyo.Constraint(m.T, rule=ess12)
        #m.ess21 = pyo.Constraint(m.T, rule=ess21)
        m.ess1_ava = pyo.Constraint(m.T, rule=ess1_availability)
        m.ess2_ava = pyo.Constraint(m.T, rule=ess2_availability)
        #m.d1_cstr1 = pyo.Constraint(m.T, rule=d1_cstr1)
        #m.curt1 = pyo.Constraint(m.T, rule=curtailment_control1) 
        #m.ess1_cyc = pyo.Constraint(m.T, rule=cycle1)
        #m.ess2_cyc = pyo.Constraint(m.T, rule=cycle2)
        
        m.as_one1 = pyo.Constraint(m.T, rule=as_one1)
        m.as_one2 = pyo.Constraint(m.T, rule=as_one2)
        
        return m


    



class optimization:

    #m1 = opt_pyomo_formulating.unit_commitment(self)

    def optimizer():
        #opt =  pyo.SolverFactory('scipampl',executable=os.getcwd()+'\scipampl-7.0.0.win.x86_64.intel.opt.spx2')
        opt =  pyo.SolverFactory('couenne',executable=os.getcwd()+'\\couenne.exe')
        results = opt.solve(opt_pyomo_formulating.unit_commitment(), logfile='optimizer_log.log', tee=False, timelimit=6000, keepfiles=True)
        results.write()
        #pyo.SolverFactory('mindtpy').solve(m, mip_solver='cbc', nlp_solver='ipopt', tee=True).write()
        
        # Extract model output in list
        output = []
        Date = list([0,1,2,3,4])
        output.append([Date, m.x1.get_values().values(), m.x2.get_values().values(), 
                        m.x3.get_values().values(), m.x4.get_values().values(), m.bat1_dch.get_values().values(),
                        m.bat1_ch.get_values().values()]) 
                        #m.bat1_dch.get_values().values(), m.bat1_ch.get_values().values(), ])

        if sum(np.fromiter(m.x1.get_values().values(), dtype=float)[3]) is not None:
            dfout = pd.DataFrame()
            #dfout.index=Load[T].index
            dfout['Load'] = reading.init_data_import()[0]
            dfout['d1'] = m.x1.get_values().values()
            dfout['d2'] = m.x2.get_values().values()
            dfout['d3'] = m.x3.get_values().values()
            dfout['d4'] = m.x4.get_values().values()
            # dfout['d1_suc'] = m.suc1.get_values().values()
            # dfout['d2_suc'] = m.suc2.get_values().values()
            # dfout['d3_suc'] = m.suc3.get_values().values()
            # dfout['d4_suc'] = m.suc4.get_values().values()
            # dfout['d1_sdc'] = m.sdc1.get_values().values()
            # dfout['d2_sdc'] = m.sdc2.get_values().values()
            # dfout['d3_sdc'] = m.sdc3.get_values().values()
            # dfout['d4_sdc'] = m.sdc4.get_values().values()
            dfout['bat1_dch'] = m.bat1_dch.get_values().values()
            dfout['bat1_ch'] = m.bat1_ch.get_values().values()
            dfout['bat2_dch'] = m.bat2_dch.get_values().values()
            dfout['bat2_ch'] = m.bat2_ch.get_values().values()
            dfout['soc1'] = m.soc1.get_values().values()
            dfout['soc2'] = m.soc2.get_values().values()
            dfout['pv1'] = m.PV1.get_values().values()
            dfout['pv2'] = m.PV2.get_values().values()
            dfout['pv3'] = m.PV3.get_values().values()
            dfout['pv4'] = m.PV4.get_values().values()
            dfout['pv5'] = m.PV5.get_values().values()
            dfout['pv6'] = m.PV6.get_values().values()
            dfout['pv7'] = m.PV7.get_values().values()
            dfout['bat1_ch'] = -dfout['bat1_ch']
            dfout['bat2_ch'] = -dfout['bat2_ch']
            #dfout['dd1'] = m.u1.get_values().values()

            dfout.index = Date
            dfout['Load'] = Load
            
            out = list(out[0])
        
            out[0] = dfout.iloc[3][5]+dfout.iloc[3][6]
            out[1] = dfout.iloc[3][7]+dfout.iloc[3][8]
            out[2] = 1
            out[3] = 1
            out[4] = 0
            out[5] = 0
            out[6] = 1
            out[7] = 1
            out[8] = bool(np.fromiter(m.u1.get_values().values(), dtype=float)[3])
            out[9] = bool(np.fromiter(m.u2.get_values().values(), dtype=float)[3])
            out[10] = bool(np.fromiter(m.u3.get_values().values(), dtype=float)[3])
            out[11] = bool(np.fromiter(m.u4.get_values().values(), dtype=float)[3])
            out[12] = int(100*dfout.iloc[3][11]/136)
            out[13] = int(100*dfout.iloc[3][12]/136)
            out[14] = int(100*dfout.iloc[3][13]/136)
            out[15] = int(100*dfout.iloc[3][14]/136)
            out[16] = int(100*dfout.iloc[3][15]/136)
            out[17] = int(100*dfout.iloc[3][16]/136)
            out[18] = int(100*dfout.iloc[3][17]/136)
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

            out0[:]=[out]


            
            out0.to_csv('C:\PROJECT\Path.csv',sep=';',index=False, decimal=',')
            #np.savetxt("C:\PROJECT\Path.csv", np.round(np.genfromtxt('C:\PROJECT\PathFromWrite.csv', delimiter=',')**2, decimals=0), delimiter=",", fmt='%i')
            originalTime = os.path.getmtime(fileName)
            print()
            print()
            print('##############################################')
            print('ОПТИМАЛЬНОЕ РЕШЕНИЕ НАЙДЕНО...')
            print('Выходные данные сохранены в C:\PROJECT\Path.csv')
            print()
        else:
            print()
            print()
            print('##############################################')
            print('ОШИБКА! ЗАДАЧА ОПТИМИЗАЦИИ С ТЕКУЩИМИ ВХОДНЫМИ ДАННЫМИ НЕ ИМЕЕТ РЕШЕНИЯ!')
            print()
    
    def optimizer_cycling():
        fileName = 'C:\PROJECT\PathFromWrite.csv'
        start_time = time.time()
        originalTime = os.path.getmtime(fileName) #считываем время изменения файла filename
        while(True):
            try:
                
                if(os.path.getmtime(fileName) > originalTime):
                    print('I am trying!')
                    print('file C:\PROJECT\PathFromWrite.csv was changed')
                    ddd = reading.init_data_import()
                    optimization.optimizer()
            except Exception as e:
                logging.basicConfig(filename='C:\PROJECT\log.txt', level=logging.DEBUG, 
                                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
                logger=logging.getLogger(__name__)
                logging.error(traceback.format_exc())

                if not os.path.exists('C:\PROJECT\ошибки'):
                    os.makedirs('C:\PROJECT\ошибки')
                dst=os.path.join('C:\\', 'Project', 'ошибки\\')
                copyfile('C:\PROJECT\PathFromWrite.csv', dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'PathFromWrite.csv')
                copyfile('C:\PROJECT\Path.csv', dst + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + 'Path.csv')
                print()
                print('------')
                print('ОШИБКА! Не удалось считать файл с входными данными. Лог в C:\PROJECT\log.txt')
                print('------')
                print()
                print('******************************************************')
                print('Считывание входных данных возобновится через 30 секунд')
                print('******************************************************')
                print()
                time.sleep(30)
                flag = 1


optimization.optimizer_cycling()



# if __name__ == '__main__':
#     p = multiprocessing.Process(target=counter_time)
    
#     p1 = multiprocessing.Process(target=da_thing)
#     p.start()
#     p1.start()
#     if flag == 1:
#         p.stop()
