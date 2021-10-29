import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pvlib
from pvlib.location import Location
import seaborn as sns
from scipy.stats import pearsonr
from pvlib import solarposition

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import median_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.metrics import explained_variance_score
from sklearn.metrics import max_error
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import LSTM
from keras.layers import RepeatVector
from keras.layers import TimeDistributed
from keras.layers import ConvLSTM2D
import pickle
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf


location = Location(67.55, 133.39, tz='Asia/Vladivostok', altitude=140, name='Verkhoyansk')
path='models/verkhoyansk_era5.csv'
data0=pd.read_csv(path,skiprows=9,parse_dates=[0], sep=',')
data0['timestamp'] = pd.to_datetime(data0['timestamp'], format = '%Y-%m-%dT%H:%M:%S.%f')
data0 = data0.set_index('timestamp')
day=data0.index.dayofyear
time=data0.index.hour + data0.index.minute/60  #переводим 17:30 в 17.5 - в десятичный формат
data0.index = data0.index.tz_localize(location.tz)

SPA = pvlib.solarposition.spa_python(data0.index, location.latitude, location.longitude)

X = data0[['Верхоянск Temperature [2 m elevation corrected]',
       'Верхоянск Precipitation Total',
       'Верхоянск Relative Humidity [2 m]',
       'Верхоянск Wind Speed [10 m]',
       'Верхоянск Wind Direction [10 m]', 'Верхоянск Cloud Cover Total',
       'Верхоянск Cloud Cover High [high cld lay]',
       'Верхоянск Cloud Cover Medium [mid cld lay]',
       'Верхоянск Cloud Cover Low [low cld lay]',
       'Верхоянск Shortwave Radiation',
       'Верхоянск Direct Shortwave Radiation',
       'Верхоянск Diffuse Shortwave Radiation',
       'Верхоянск Mean Sea Level Pressure [MSL]']]
X['solar_azimuth']=SPA['azimuth']
X['zenith']=SPA['apparent_zenith']
X_light_day = X.loc[X['zenith']<90]
X_light_day = X_light_day.dropna()
X_light_day['dni']=pvlib.irradiance.dni(X_light_day['Верхоянск Shortwave Radiation'],
                     X_light_day['Верхоянск Diffuse Shortwave Radiation'],
                     X_light_day['zenith'], clearsky_dni=None, clearsky_tolerance=1.1,
                     zenith_threshold_for_zero_dni=88.0, zenith_threshold_for_clearsky_limit=80.0)

Xs=X_light_day[['Верхоянск Temperature [2 m elevation corrected]', 'Верхоянск Relative Humidity [2 m]',
          'Верхоянск Cloud Cover Total', 'Верхоянск Cloud Cover Low [low cld lay]',
         'Верхоянск Cloud Cover Medium [mid cld lay]', 'Верхоянск Cloud Cover High [high cld lay]', 'zenith']]
Ys = X_light_day[['Верхоянск Shortwave Radiation',
                  'Верхоянск Direct Shortwave Radiation', 'Верхоянск Diffuse Shortwave Radiation']]
Xs=Xs.dropna()

X_train0, X_test0, y_train0, y_test0 = train_test_split(Xs, Ys, test_size=0.25, random_state=0, shuffle=False) #доля тестовой выборки - 25%
#преобразование датафреймов в массивы типа numpy
X_train=X_train0.to_numpy()
y_train=y_train0.to_numpy().reshape(len(y_train0), -1)
X_test=X_test0.to_numpy()
y_test=y_test0.to_numpy().reshape(len(y_test0), -1)
scaler1 = MinMaxScaler()
scaler2 = MinMaxScaler()
#Масштабируем данные
X_train = scaler1.fit_transform(X_train)
y_train = scaler2.fit_transform(y_train)
X_test = scaler1.fit_transform(X_test)
y_test = scaler2.fit_transform(y_test)

with open('models/pv_keras/pv_X_scaler_par.sca', 'wb') as f1:
    pickle.dump([scaler1.min_, scaler1.scale_], f1)

with open('models/pv_keras/pv_Y_scaler_par.sca', 'wb') as f2:
    pickle.dump([scaler2.min_, scaler2.scale_], f2)

# define model

# np.random.seed(0)
# tf.random.set_seed(0)
#
# model = Sequential()
# model.add(Dense(500, activation='relu', input_dim=7))
# model.add(Dense(100))
# model.add(Dense(100))
# #model.add(Dense(1000))
# #model.add(Dense(100))
# #model.add(Dense(100))
# #model.add(Dense(100))
# model.add(Dense(3))
# model.compile(optimizer='adam', loss='mse')
# # fit model
#
# callback=keras.callbacks.EarlyStopping(
#     monitor='loss', min_delta=0, patience=5, verbose=2, mode='auto',
#     baseline=None, restore_best_weights=True)
#
# model.fit(X_train, y_train, epochs=200, verbose=1, callbacks=[callback])
# model.save('models/pv_keras/')

# model = keras.models.load_model('models/pv_keras/')
#
# prediction=model.predict(X_test, verbose=1) #прогнозирование по тестовым признакам
# prediction0=model.predict(X_train, verbose=1) #прогнозирование по обучающим признакам
# y_pred0=prediction0.reshape(len(prediction0), -1)
# Ipred=prediction.reshape(len(prediction), -1)
# #на выходе модели выдается масштабированная величина I, которую для лучшей интерпретации результатов необходимо преобразовать обратно в именованную
# ytrain=scaler2.inverse_transform(y_train) #обратное преобразование фактических величин I из обучающей выборки
# y_pred_train=scaler2.inverse_transform(y_pred0) #обратное преобразование спрогнозированных величин I по обучающей выборке
# y_pred=scaler2.inverse_transform(Ipred) #обратное преобразование спрогнозированных величин I
# y_real=scaler2.inverse_transform(y_test) #обратное преобразование фактических величин I
#
# fig, ax = plt.subplots(3, 1, figsize=(18,10))
# ax[0].plot(y_pred.T[0][190:350], label='Предсказанные значения суммарной СР')
# ax[0].plot(y_real.T[0][190:350], label='Фактические данные суммарной СР')
# ax[0].legend()
#
# ax[1].plot(y_pred.T[1][190:350], label='Предсказанные значения прямой СР')
# ax[1].plot(y_real.T[1][190:350], label='Фактические данные прямой СР')
# ax[1].legend()
#
# ax[2].plot(y_pred.T[2][190:350], label='Предсказанные значения диффузной СР')
# ax[2].plot(y_real.T[2][190:350], label='Фактические данные диффузной СР')
# ax[2].legend()
#
# plt.show()

DNI = np.array(X_light_day['dni'])

dni_extra = pvlib.irradiance.get_extra_radiation(X_light_day.index, method='spencer')
plt.plot(dni_extra)
plt.show()