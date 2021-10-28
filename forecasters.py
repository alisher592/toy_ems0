import pandas as pd
import numpy as np
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
from datetime import datetime, timedelta

class LoadForecaster:

    def __init__(self, files_destination):
        self.model = pickle.load(open(files_destination[0], 'rb'))  # загрузка модели из pickle-файла

        self.X_scaler = MinMaxScaler()
        self.Y_scaler = MinMaxScaler()

        self.X_scaler.min_ = pickle.load(open(files_destination[1], 'rb'))[0]
        self.X_scaler.scale_ = pickle.load(open(files_destination[1], 'rb'))[1]

        self.Y_scaler.min_ = pickle.load(open(files_destination[2], 'rb'))[0]
        self.Y_scaler.scale_ = pickle.load(open(files_destination[2], 'rb'))[1]

        self.current_datetime = datetime.now()

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
        #Сбор признаков HOY, DOY, Month, Day, Hour (именно в таком порядке)
        # hoy, doy, month, day, \
        # hour = np.array([self.hour_of_year(date) for date in pd.date_range(datetime.now(),
        #                                                                   freq='H', periods=24).round('H')]).T[0:5]

        dtrange = pd.date_range(datetime.now(), freq='H', periods=24).round('H')

        features = self.X_scaler.transform(np.array([[self.hour_of_year(date), date.timetuple().tm_yday,
                                                      date.month, date.day, date.hour] for date in dtrange]))
        raw_fcst = self.model.predict(features)


        load_forecast = pd.DataFrame(index=dtrange)
        load_forecast['Load_Forecast'] = self.Y_scaler.inverse_transform(raw_fcst.reshape(len(raw_fcst), -1))

        # plt.plot(self.Y_scaler.inverse_transform(self.model.predict(features).reshape(len(model.predict(ft)), -1)))

        return load_forecast

# files = ['models/mlp_load_hourly.vrk', 'models/X_scaler_par.sca', 'models/Y_scaler_par.sca']
# L = LoadForecaster(files)

# plt.plot(L.get_hourly_forecast())
# plt.show()




