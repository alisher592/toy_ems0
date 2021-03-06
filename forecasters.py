import math
import time as timeh
import pandas as pd
import numpy as np
import pvlib
from sklearn.model_selection import train_test_split
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import median_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.metrics import explained_variance_score
from sklearn.metrics import max_error
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import pytz
from datetime import datetime, timedelta, date
from simplejson import loads
from requests import get
#from tensorflow import keras




class Load_forecaster:

    def __init__(self, files_destination):

        # вызывается больше 1 раза!

        self.model = pickle.load(open(files_destination[0], 'rb'))  # загрузка модели из pickle-файла

        self.X_scaler = MinMaxScaler()
        self.Y_scaler = MinMaxScaler()

        self.X_scaler.min_ = pickle.load(open(files_destination[1], 'rb'))[0]
        self.X_scaler.scale_ = pickle.load(open(files_destination[1], 'rb'))[1]

        self.Y_scaler.min_ = pickle.load(open(files_destination[2], 'rb'))[0]
        self.Y_scaler.scale_ = pickle.load(open(files_destination[2], 'rb'))[1]

        self.current_datetime = datetime.now().astimezone(pytz.timezone("Asia/Vladivostok")) #+ timedelta(days=30)
        self.dtrange = pd.date_range(self.current_datetime, freq='H', periods=24).round('H')

        self.location = pvlib.location.Location(67.55, 133.39, tz='Asia/Vladivostok',
                                                altitude=140, name='Verkhoyansk')

    def hour_of_year(self, date):
        """
        Функция получения порядкового номера текущего часа в разрезе года
        :return:
        """
        beginning_of_year = datetime(date.year, 1, 1, tzinfo=date.tzinfo)
        return (date - beginning_of_year).total_seconds() // 3600

    def get_hourly_forecast(self):
        """
        Функция почасового прогноза на основе текущей даты
        :param datetime:
        :return:
        """
        # Сбор признаков HOY, DOY, Month, Day, Hour (именно в таком порядке)
        # hoy, doy, month, day, \
        # hour = np.array([self.hour_of_year(date) for date in pd.date_range(datetime.now(),
        #                                                                   freq='H', periods=24).round('H')]).T[0:5]

        features = self.X_scaler.transform(np.array([[self.hour_of_year(date), date.timetuple().tm_yday,
                                                      date.month, date.day, date.hour] for date in self.dtrange]))
        raw_fcst = self.model.predict(features)

        load_forecast = pd.DataFrame(index = self.dtrange)
        load_forecast['Load_Forecast'] = self.Y_scaler.inverse_transform(raw_fcst.reshape(len(raw_fcst), -1))

        # plt.plot(self.Y_scaler.inverse_transform(self.model.predict(features).reshape(len(model.predict(ft)), -1)))

        return load_forecast


    def daylight_hours(self):



        return pvlib.solarposition.spa_python(self.dtrange, self.location.latitude, self.location.longitude, self.location.altitude)['apparent_zenith'], pvlib.solarposition.spa_python(self.dtrange, self.location.latitude, self.location.longitude,
                                       self.location.altitude)['zenith']

    def self_consumption_forecast(self):

        self_consumption = pd.DataFrame()

        solar_zenith = pvlib.solarposition.spa_python(self.dtrange, self.location.latitude, self.location.longitude,
                                       self.location.altitude)['zenith']

        self_consumption['zenith'] = pvlib.solarposition.spa_python(self.dtrange, self.location.latitude, self.location.longitude,
                                       self.location.altitude)['apparent_zenith']

        current_month = date.today().month

        if 6 <= current_month <= 8:

            self_consumption['ЩСН 1 СНЭ'] = 1.39
            self_consumption['ЩСН РУ 6 СНЭ'] = 0.168
            self_consumption['ЩУ СНЭ'] = 11.569
            self_consumption['ЩСН СЭC'] = 0.935
            self_consumption['ЩСН РУ 6 СЭС'] = 0.16
            self_consumption['ЩСН 40 фут'] = 2.558

        else:

            self_consumption['ЩСН 1 СНЭ'] = 1.335
            self_consumption['ЩСН РУ 6 СНЭ'] = 2.106
            self_consumption['ЩУ СНЭ'] = 11.08
            self_consumption['ЩСН СЭC'] = 4.49
            self_consumption['ЩСН РУ 6 СЭС'] = 2.11
            self_consumption['ЩСН 40 фут'] = 4.72



        # self_consumption['Отопление контейнера СЭС'] = 4.4 + 2.2*2
        # self_consumption['Отопление контейнера СНЭ'] = 2
        # self_consumption['Прочее'] = 3
        # self_consumption['Наружное освещение'] = 2.2
        # self_consumption.loc[self_consumption['zenith'] <= 90, 'Наружное освещение'] = 0

        # self_consumption['Собственные нужды'] = self_consumption['Отопление контейнера СЭС'] + self_consumption['Отопление контейнера СНЭ'] + self_consumption['Прочее'] + self_consumption['Наружное освещение']

        self_consumption['Собственные нужды'] = self_consumption['ЩСН 1 СНЭ'] + self_consumption['ЩСН РУ 6 СНЭ'] + \
                                                self_consumption['ЩУ СНЭ'] + self_consumption['ЩСН СЭC'] + \
                                                self_consumption['ЩСН РУ 6 СЭС'] + self_consumption['ЩСН 40 фут']


        return self_consumption





class PV_forecaster:

    def __init__(self, files_destination):
        #self.model = keras.models.load_model(files_destination[0])  # загрузка модели из pickle-файла

        self.model = pickle.load(open(files_destination[0], 'rb'))  # загрузка модели из pickle-файла

        self.X_scaler = MinMaxScaler()
        self.Y_scaler = MinMaxScaler()

        self.X_scaler.min_ = pickle.load(open(files_destination[1], 'rb'))[0]
        self.X_scaler.scale_ = pickle.load(open(files_destination[1], 'rb'))[1]

        self.Y_scaler.min_ = pickle.load(open(files_destination[2], 'rb'))[0]
        self.Y_scaler.scale_ = pickle.load(open(files_destination[2], 'rb'))[1]

        self.current_datetime = datetime.now()

        self.location = pvlib.location.Location(67.55, 133.39, tz='Asia/Vladivostok',
                                                altitude=140, name='Verkhoyansk')
        self.surface_tilt = 52 #угол наклона ФЭМ
        self.surface_azimuth = 180 #азимутальный угол установки ФЭМ

        self.pv_modules_CEC = pvlib.pvsystem.retrieve_sam(path='base/CEC_Modules.csv')
        self.inverters_CEC = pvlib.pvsystem.retrieve_sam(path='base/CEC_Inverters.csv')

    def yrnoparser(self, horizon=24,
                   useragent='mpei.ru, NarynbayevA@mpei.ru, student project'):

        """
        useragent (str) - UserAgent для авторизации в системе yr.no
        latitude (float) - широта местности, для которой запрашивается прогноз
        longitude (float) - долгота местности, для которой запрашивается прогноз
        set_timezone (str) - часовой пояс в формате pytz
        horizon (float) - (min=2, max=91, default=24) - горизонт упреждения прогноза в часах
        """

        headers = {'User-Agent': useragent}
        url = 'https://api.met.no/weatherapi/locationforecast/2.0/complete?lat=' + \
              str(self.location.latitude) + '&lon=' + str(self.location.longitude)

        # запрос хэдеров со статистикой последних обновлений прогнозов
        try:

            print()
            print("...Загрузка данных метеопрогноза...", end=" ")



            if get('https://api.met.no/weatherapi/locationforecast/2.0/status',
                   headers=headers).status_code == 200:
                # сервер работает и UserAgent не заблокирован
                # local_time_now=datetime.utcnow().replace(tzinfo=UTC).astimezone(
                # timezone(str(get_localzone()))) #присвоение часового пояса по времени на компьютере

                # подгрузка json-ов
                raw_forecast = loads(get(url, headers=headers).text)
                raw_DataFrame = pd.DataFrame.from_dict(raw_forecast.get('properties',
                                                                        {}).get('timeseries'))

                # генерация pandas-датафрейма с прогнозом погоды
                listed_forecast = []
                for i in range(len(raw_forecast.get('properties',
                                                    {}).get('timeseries', {'data'}))):
                    listed_forecast.append(
                        dict(raw_forecast['properties']['timeseries'][i])['data']['instant']['details'])

                forecast = pd.DataFrame(listed_forecast, raw_DataFrame['time'])
                forecast.index = pd.to_datetime(forecast.index)
                forecast = forecast.tz_localize(None)
                forecast = forecast.tz_localize('UTC').tz_convert(str(self.location.tz))
                forecast[['zenith', 'solar_azimuth']] = pvlib.solarposition.spa_python(forecast.index,
                                                                                       self.location.latitude,
                                                                                       self.location.longitude)[
                    ['apparent_zenith',
                     'azimuth']]



            else:
                return ('****** ОШИБКА! Сервер метеопрогнозов не отвечает, либо доступ к API запрещен! ******')
        except Exception as e:
            return ('****** ОШИБКА! Не удалось подключиться к серверу метепрогнозов! ******', e)
        return forecast.iloc[1:horizon + 1]  # возвращает датайфрейм с прогнозом


    def get_hourly_irrad_forecast(self):

        start_timeh = timeh.time()
        print()
        print("...Прогнозирование интенсивности солнечной радиации...")


        Weather = self.yrnoparser()  # получаем прогноз погоды
        SPA = pvlib.solarposition.spa_python(Weather.index, self.location.latitude, self.location.longitude)
        Weather['solar_azimuth'] = SPA['azimuth']
        Weather['zenith'] = SPA['apparent_zenith']
        # light_weather = Weather.loc[Weather['zenith'] < 90].dropna()
        features = self.X_scaler.transform(Weather[['air_temperature', 'relative_humidity',
                                                    'cloud_area_fraction', 'cloud_area_fraction_low',
                                                    'cloud_area_fraction_medium',
                                                    'cloud_area_fraction_high', 'zenith']])
        raw_fcst = self.Y_scaler.inverse_transform(self.model.predict(features)).T
        irrad_fcst = pd.DataFrame()
        irrad_fcst.index = Weather.index
        irrad_fcst['pressure'] = Weather['air_pressure_at_sea_level']
        irrad_fcst['dew_temp'] = Weather['dew_point_temperature']
        irrad_fcst['ghi'] = raw_fcst[0]
        irrad_fcst['dhi'] = raw_fcst[1]
        irrad_fcst['dfhi'] = raw_fcst[2]
        irrad_fcst['zenith'] = Weather['zenith']
        irrad_fcst['solar_azimuth'] = Weather['solar_azimuth']

        irrad_fcst.loc[
            irrad_fcst['zenith'] > 90, ['ghi', 'dhi', 'dfhi']] = 0  # заменяем СР на ноль по критерию светового дня

        clearsky_dni = self.location.get_clearsky(irrad_fcst.index)['dni']

        irrad_fcst['dni'] = pvlib.irradiance.dni(irrad_fcst['ghi'],
                                                  irrad_fcst['dfhi'],
                                                  irrad_fcst['zenith'],
                                                 clearsky_dni=clearsky_dni,
                                                 clearsky_tolerance=1.1,
                                                  zenith_threshold_for_zero_dni=88.0,
                                                  zenith_threshold_for_clearsky_limit=80.0)

        DNI_erbs = pvlib.irradiance.erbs(irrad_fcst['ghi'], irrad_fcst['zenith'], irrad_fcst.index,
                              min_cos_zenith=0.065, max_zenith=87)

        dirint = pvlib.irradiance.dirint(irrad_fcst['ghi'], irrad_fcst['zenith'], irrad_fcst.index,
                                         pressure=1000*irrad_fcst['pressure'], use_delta_kt_prime=True,
                                         temp_dew=irrad_fcst['dew_temp'],
                                min_cos_zenith=0.065, max_zenith=87)

        irrad_fcst['dirint_dni'] = dirint #DNI_erbs['dni']
        irrad_fcst['clearsky_dni'] = clearsky_dni

        oblakah = Weather['cloud_area_fraction'].mean()

        disc = pvlib.irradiance.disc(irrad_fcst['ghi'], irrad_fcst['zenith'], irrad_fcst.index,
                                     pressure=1000*irrad_fcst['pressure'],
                                     min_cos_zenith=0.065, max_zenith=87, max_airmass=12)

        #plt.plot(DNI_erbs['dni'])
        #plt.plot(disc['dni'])
        #plt.plot(dirint)

        ghii = irrad_fcst['ghi']
        dnii = irrad_fcst['dni']

        #plt.plot(irrad_fcst['dni'])
        #plt.plot(irrad_fcst['ghi'])
        #plt.show()
        #print(dirint)
        #print(irrad_fcst['pressure'])


        poa_irrad_fcst = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.surface_tilt,
            surface_azimuth=self.surface_azimuth,
            dni=irrad_fcst['dni'], #irrad_fcst['dirint_dni'],
            ghi=irrad_fcst['ghi'],
            dhi=irrad_fcst['dfhi'],
            solar_zenith=irrad_fcst['zenith'],
            solar_azimuth=irrad_fcst['solar_azimuth'], dni_extra=pvlib.irradiance.get_extra_radiation(irrad_fcst.index,
                                                                                                      solar_constant=1366.1,
                                                                                                      method='spencer',
                                                                                                      epoch_year=2022),
            model='isotropic', surface_type='snow')

        poa_irrad_fcst['air_temperature'] = Weather['air_temperature']
        poa_irrad_fcst['wind_speed'] = Weather['wind_speed']
        poa_irrad_fcst['cloud'] = Weather['cloud_area_fraction']

        print("--- %s сек. ---" % round((timeh.time() - start_timeh), 3))

        if oblakah <= 70:

            return irrad_fcst.fillna(0), poa_irrad_fcst.fillna(0)

        elif 70 < oblakah < 80  :

            return irrad_fcst.fillna(0)/3, poa_irrad_fcst.fillna(0)/3

        elif 80 <= oblakah <= 100  :

            return irrad_fcst.fillna(0)/4, poa_irrad_fcst.fillna(0)/4


    def get_pv_forecast(self):

        poa_irrad_fcst = self.get_hourly_irrad_forecast()[1]


        module = self.pv_modules_CEC.T.iloc[9502]  # -4 относительно таблицы csv
        # добавление параметров модуля JAM72S10-410/MR
        module['Bifacial'] = 0
        module['STC'] = 410
        module['PTC'] = 385.3
        module['A_c'] = 2.015 * 0.996
        module['N_s'] = 72
        module['I_sc_ref'] = 10.45
        module['V_oc_ref'] = 50.12
        module['I_mp_ref'] = 9.79
        module['V_mp_ref'] = 41.88
        module['T_NOCT'] = 45
        module['Name'] = 'JAM72S10-410/MR'

        cec_estimation = pvlib.ivtools.sdm.fit_cec_sam(celltype='monoSi',
                                                       v_mp=module['V_mp_ref'], i_mp=module['I_mp_ref'],
                                                       v_oc=module['V_oc_ref'], i_sc=module['I_sc_ref'],
                                                       alpha_sc=0.00044 * module['I_sc_ref'],
                                                       beta_voc=(-0.00272 * module['V_oc_ref']),
                                                       gamma_pmp=-0.35, cells_in_series=72, temp_ref=25)

        module['I_L_ref'] = cec_estimation[0]
        module['I_o_ref'] = cec_estimation[1]
        module['R_s'] = cec_estimation[2]
        module['R_sh_ref'] = cec_estimation[3]
        module['a_ref'] = cec_estimation[4]
        module['Adjust'] = cec_estimation[5]

        weather = pd.DataFrame()
        weather['ghi'] = poa_irrad_fcst['poa_global']
        weather['dni'] = poa_irrad_fcst['poa_direct']
        # weather['dni']=ClearSky['ghi']*1.25
        weather['dhi'] = poa_irrad_fcst['poa_diffuse']
        weather['temp_air'] = poa_irrad_fcst['air_temperature']
        weather['wind_speed'] = poa_irrad_fcst['wind_speed']
        weather.columns = ['poa_global', 'poa_direct', 'poa_diffuse', 'temp_air', 'wind_speed']

        # pd.options.mode.chained_assignment = None  # default='warn' #убрать ошибку A value is trying to copy a slice

        inverter = self.inverters_CEC.T.iloc[471]
        # Эмулируем параметры инвертора GW136K-HTH
        # Sandia_inv = pvlib.inverter.fit_sandia(np.array([136000, 136000, 150000]),
        #                                        np.array([205000, 205000, 205000]),
        #                                        np.array([180, 750, 1100]),
        #                                        np.array(['Vmin', 'Vnom', 'Vmax']), 136000, 2)
        # inverter['Paco'] = Sandia_inv['Paco']
        # inverter['Pdco'] = Sandia_inv['Pdco']
        # inverter['Pso'] = Sandia_inv['Pso']
        # inverter['C0'] = Sandia_inv['C0']
        # inverter['C1'] = Sandia_inv['C1']
        # inverter['C2'] = Sandia_inv['C2']
        # inverter['C3'] = Sandia_inv['C3']
        # inverter['Pnt'] = Sandia_inv['Pnt']
        #
        # inverter.Vac = 500
        # inverter.Vdcmax = 1100
        # inverter.Idcmax = 186.36
        # inverter.Mppt_low = 180
        # inverter.Mppt_high = 1000

        temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm'][
            'open_rack_glass_glass']  # температурная модель Sandia

        system = pvlib.pvsystem.PVSystem(surface_tilt=self.surface_tilt, surface_azimuth=self.surface_azimuth,
                                         module_parameters=module,
                                         inverter_parameters=inverter,
                                         temperature_model_parameters=temperature_model_parameters,
                                         modules_per_string=17,
                                         strings_per_inverter=21)
        mc = pvlib.modelchain.ModelChain(system, self.location, aoi_model='physical', spectral_model='no_loss',
                                         losses_model='pvwatts')
        mc.run_model_from_poa(weather)

        rocco  = mc.results.ac

        #plt.plot(mc.results.ac * 7)
        #plt.show()


        return mc.results.ac * 7 #*0.04

# pv_files = ['models/pv_keras', 'models/pv_keras/pv_X_scaler_par.sca',
#              'models/pv_keras/pv_Y_scaler_par.sca']
#
#p = PV_forecaster(pv_files)
#
# # print(p.get_hourly_irrad_forecast()[1])
#
#(p.get_hourly_irrad_forecast()[1]).plot()
#plt.show()
#
#(p.get_pv_forecast()*7).plot()
#plt.show()

# linke_turbidity = pvlib.clearsky.lookup_linke_turbidity(p.get_hourly_irrad_forecast()[1].index,
#                                                         p.location.latitude, p.location.longitude)
#
# ineichen = clearsky.ineichen(apparent_zenith, airmass, linke_turbidity, altitude, dni_extra)
#
# plt.plot(linke_turbidity)
# plt.show()

#files = ['models/mlp_load_hourly.vrk', 'models/X_scaler_par.sca', 'models/Y_scaler_par.sca']
#L = Load_forecaster(files)

#print(L.get_hourly_forecast().index)

#print(L.self_consumption_forecast())


#L.self_consumption_forecast().plot.area()
#plt.plot(L.self_consumption_forecast())

#plt.show()

# plt.plot(L.get_hourly_forecast())
# plt.show()

