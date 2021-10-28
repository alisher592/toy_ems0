import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPRegressor

X = pd.read_csv('models/load161718.csv', index_col = [0], parse_dates=True)
Ys = X['Load']

features = X[['HOY', 'DOY', 'Month', 'Day', 'Hour']]

X_train0, X_test0, y_train0, y_test0 = train_test_split(features, Ys, test_size=0.15, random_state=0, shuffle=True) #доля тестовой выборки - 25%
#преобразование датафреймов в массивы типа numpy
X_train=X_train0.to_numpy()
y_train=y_train0.to_numpy().reshape(len(y_train0), -1)
X_test=X_test0.to_numpy()
y_test=y_test0.to_numpy().reshape(len(y_test0), -1)
scaler1 = MinMaxScaler()
scaler2 = MinMaxScaler()
#Масштабируем данные
X_train = scaler1.fit_transform(X_train)
y_train=scaler2.fit_transform(y_train)
X_test = scaler1.fit_transform(X_test)
y_test=scaler2.fit_transform(y_test)

scaler1_min = scaler1.min_
scaler1_scale = scaler1.scale_

scaler2_min = scaler2.min_
scaler2_scale = scaler2.scale_

MLP = MLPRegressor(hidden_layer_sizes=(100,100),verbose=True, random_state=0)
MLP.fit(X_train, y_train)

#models and params dumping out

import pickle
with open('models/mlp_load_hourly.vrk', 'wb') as f:
    pickle.dump(MLP, f)

with open('models/X_scaler_par.sca', 'wb') as f1:
    pickle.dump([scaler1.min_, scaler1.scale_], f1)

with open('models/Y_scaler_par.sca', 'wb') as f2:
    pickle.dump([scaler2.min_, scaler2.scale_], f2)

