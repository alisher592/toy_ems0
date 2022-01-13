import pandas as pd
import pyodbc
import os

class DB_connector:

    def __init__(self):
        # инициализация данных для подключения к БД
        self.params = self.param_reader()
        self.driver = 'Driver={SQL Server};'
        self.server = 'Server=' + self.params[0] + ';' #192.168.20.139;'
        self.port = 'PORT=' + self.params[1] + ';' #1433;'
        self.db = 'Database=' + self.params[2] + ';' #TEST;'
        self.user = 'UID=' + self.params[3] + ';' #sa;'
        self.password = 'PWD=' + self.params[4] + ';' #KznZN43'
        #self.password = 'PWD=369147'

    def param_reader(self):
        with open(os.getcwd()+"\\DB_connection_parameters.txt") as f:
            db_params = f.readlines()
            db_params = [x.strip() for x in db_params]
        return db_params

    def db_to_pd(self, rows):
        """
        Подключение к БД MS SQL Server и конвертация в pandas датафрейм
        :param rows: количество строк для считывания
        :return: pandas series
        """
        connection = pyodbc.connect(self.driver + self.server + self.port + self.db + self.user + self.password)
        sql_query = "SELECT * FROM (SELECT TOP " + str(rows) + " * FROM [TEST].[dbo].[Table2] ORDER BY [DT] DESC)[TEST] ORDER BY [DT] DESC"
        data = pd.read_sql(sql_query, connection, index_col='DT')
        hourly_data_means = data.resample('H').mean()

        return data, hourly_data_means


    def DG_before(self, data):
        """
        :param data: данные из SQL
        :return:
        """
        DG_start_status = list()
        DG_hours_up_before = list()
        DG_hours_down_before = list()
        DG_availability = list()

        conseq1 = data[1].groupby('F9').cumcount()[-1:].to_numpy() # количество последовательных статусов на текущий час
        vl1 = db_datah[0]['F9'][-1:] # последняя текущая (минутная) величина
        power1 = db_datah[0]['F1'][-1:] # последняя текущая (минутная) величина мощности
        availability1 = db_datah[0]['F23'][-1:] # последняя текущая (минутная) доступность

        conseq2 = data[1].groupby('F10').cumcount()[-1:].to_numpy()  # количество последовательных статусов на текущий час
        vl2 = db_datah[0]['F10'][-1:]  # последняя текущая (минутная) величина
        power2 = db_datah[0]['F2'][-1:]  # последняя текущая (минутная) величина мощности
        availability2 = db_datah[0]['F24'][-1:]  # последняя текущая (минутная) доступность

        conseq3 = data[1].groupby('F11').cumcount()[-1:].to_numpy()  # количество последовательных статусов на текущий час
        vl3 = db_datah[0]['F11'][-1:]  # последняя текущая (минутная) величина
        power3 = db_datah[0]['F3'][-1:]  # последняя текущая (минутная) величина мощности
        availability3 = db_datah[0]['F25'][-1:]  # последняя текущая (минутная) доступность

        conseq4 = data[1].groupby('F12').cumcount()[-1:].to_numpy()  # количество последовательных статусов на текущий час
        vl4 = db_datah[0]['F12'][-1:]  # последняя текущая (минутная) величина
        power4 = db_datah[0]['F4'][-1:]  # последняя текущая (минутная) величина мощности
        availability4 = db_datah[0]['F26'][-1:]  # последняя текущая (минутная) доступность

        # ДГУ1
        if (vl1.all() == 30 or power1.all() != 0) and availability1.all() == 1:
            DG_start_status.append(1)
            DG_hours_up_before.append(2) #conseq1[0]
            DG_hours_down_before.append(1)
            DG_availability.append(1)
        if (vl1.all() != 30 or power1.all() == 0) or availability1.all() == 0:
            DG_start_status.append(0)
            DG_hours_down_before.append(3)
            DG_hours_up_before.append(0)
            DG_availability.append(0)

        # ДГУ2
        if (vl2.all() == 30 or power2.all() != 0) and availability2.all() == 1:
            DG_start_status.append(1)
            DG_hours_up_before.append(2)
            DG_hours_down_before.append(1)
            DG_availability.append(1)
        elif (vl2.all() != 30 or power2.all() == 0) or availability2.all() == 0:
            DG_start_status.append(0)
            DG_hours_down_before.append(3)
            DG_hours_up_before.append(0)
            DG_availability.append(0)

        # ДГУ3
        if (vl3.all() == 30 or power3.all() != 0) and availability3.all() == 1:
            DG_start_status.append(1)
            DG_hours_up_before.append(2)
            DG_hours_down_before.append(1)
            DG_availability.append(1)
        elif (vl3.all() != 30 or power3.all() == 0) or availability3.all() == 0:
            DG_start_status.append(0)
            DG_hours_down_before.append(3)
            DG_hours_up_before.append(0)
            DG_availability.append(0)

        # ДГУ4
        if (vl4.all() == 30 or power4.all() != 0) and availability4.all() == 1:
            DG_start_status.append(1)
            DG_hours_up_before.append(2)
            DG_hours_down_before.append(1)
            DG_availability.append(1)
        elif (vl4.all() != 30 or power4.all() == 0) or availability4.all() == 0:
            DG_start_status.append(0)
            DG_hours_down_before.append(3)
            DG_hours_up_before.append(0)
            DG_availability.append(0)


        return DG_start_status, DG_hours_up_before, DG_hours_down_before, DG_availability



db_datah = DB_connector().db_to_pd(12)

# print((db_datah[0].resample('H').mean()['F9'][-6:] == 30).sum())

# print((db_datah[1]['F9'][-6:] == 30))

# print(db_datah[1].groupby('F9').cumcount()[-1:])

# print(db_datah[0]['F9'][-1:])

#print(db_datah[1].loc[(db_datah[1]['F9'] == 30) & (db_datah[1]['F23'] == 0)])

#db_datah[0].to_csv('wtho.csv')

print(DB_connector().DG_before(db_datah))

print(db_datah[0])