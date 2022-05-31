import pandas as pd
import pyodbc
import os
import datetime
from sqlalchemy import create_engine


class DB_connector():

    def __init__(self):
        # инициализация данных для подключения к БД
        self.params = self.param_reader()
        self.driver = 'Driver={' + self.params[0] + '};'
        self.server = 'Server=' + self.params[1] + ';' #192.168.20.139;'
        self.port = 'PORT=' + self.params[2] + ';' #1433;'
        self.db = 'Database=' + self.params[3] + ';' #TEST;'
        self.db_raw = self.params[3]
        self.user = 'UID=' + self.params[4] + ';' #sa;'
        self.password = 'PWD=' + self.params[5] + ';' #KznZN43'
        #self.connection = pyodbc.connect(self.driver + self.server + self.port + self.db + self.user + self.password)
        self.connection = pyodbc.connect(self.driver + self.server + self.db + self.user + self.password + "Trusted_Connection=no;") #"Trusted_Connection=yes;"
        #self.connection = pyodbc.connect(self.driver + self.server + self.db + "Trusted_Connection=yes;")

        self.table = self.params[6]
        self.table_to_write = self.params[7]
        #self.password = 'PWD=369147'

    def param_reader(self):
        with open(os.getcwd()+"\\DB_connection_parameters.txt") as f:
            db_params = f.readlines()
            db_params = [x.strip() for x in db_params]
            f.close()

        return db_params

    def db_to_pd(self, rows):
        """
        Подключение к БД MS SQL Server и конвертация в pandas датафрейм
        :param rows: количество строк для считывания
        :return: pandas series
        """
        # connection = pyodbc.connect(self.driver + self.server + self.port + self.db + self.user + self.password)
        sql_query = "SELECT * FROM (SELECT TOP " + str(rows) + " * FROM [" + self.db_raw + "].[dbo].[" + self.table + "] ORDER BY [DT] DESC)[" + self.db_raw + "] ORDER BY [DT] DESC"
        data = pd.read_sql(sql_query, self.connection, index_col='DT')
        hourly_data_means = data.resample('H').mean()
        # data.to_csv('datah.csv')
        # hourly_data_means.to_csv('hdatah.csv')

        return data, hourly_data_means

    def db_from_csv(self):


        data = pd.read_csv('datah.csv', index_col='DT')
        #hourly_data_means = pd.read_csv('hdatah.csv')


        #hourly_data_means = data.resample('H').mean()
        # data.to_csv('datah.csv')
        # hourly_data_means.to_csv('hdatah.csv')

        return data #, hourly_data_means


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

    def decision_to_sql(self, df):
        """

        :return:
        """
        #connection = pyodbc.connect(self.driver + self.server + self.port + self.db + self.user + self.password)

        #engine = create_engine(
        #    "mssql+pyodbc://"+self.params[3]+":"+self.params[4]+"@"+self.params[0]+":"+self.params[1]+"/"+self.params[2]+"?"+"driver=SQL+Server+Native+Client+11.0")

        #df.to_sql('temporary1', engine, if_exists='append')

        sql_query = "UPDATE [" + self.db_raw + "].[dbo].[" + self.table_to_write + "] SET [Mass_Pess1_set] = " +\
                    str(df.iloc[0]) + ",[Mass_Pess2_set] = " + str(df.iloc[1]) + ",[Mass_Qess_st1_set] = " +\
                    str(df.iloc[2]) + ",[Mass_Qess_st2_set] = " + str(df.iloc[3]) + ",[Mass_Qess1_set] = " +\
                    str(df.iloc[4]) + ",[Mass_Qess2_set] = " + str(df.iloc[5]) + ",[Mass_ESS1_mode_set] = " +\
                    str(df.iloc[6]) + ",[Mass_ESS2_mode_set] = " + str(df.iloc[7]) + ",[Mass_D1_onoff] = ?" +\
                    ",[Mass_D2_onoff] = ?" +  ",[Mass_D3_onoff] = ?" + ",[Mass_D4_onoff] = ?" +\
                    ",[Mass_Ppv1_lim] = " + str(df.iloc[12]) + ",[Mass_Ppv2_lim] = " +\
                    str(df.iloc[13]) + ",[Mass_Ppv3_lim] = " + str(df.iloc[14]) + ",[Mass_Ppv4_lim] = " +\
                    str(df.iloc[15]) + ",[Mass_Ppv5_lim] = " + str(df.iloc[16]) + ",[Mass_Ppv6_lim] = " +\
                    str(df.iloc[17]) + ",[Mass_Ppv7_lim] = " + str(df.iloc[18]) + ",[Mass_Ppv1_lim_cr] = " +\
                    str(df.iloc[19]) + ",[Mass_Ppv2_lim_cr] = " + str(df.iloc[20]) + ",[Mass_Ppv3_lim_cr] = " +\
                    str(df.iloc[21]) + ",[Mass_Ppv4_lim_cr] = " + str(df.iloc[22]) + ",[Mass_Ppv5_lim_cr] = " +\
                    str(df.iloc[23]) + ",[Mass_Ppv6_lim_cr] = " + str(df.iloc[24]) + ",[Mass_Ppv7_lim_cr] = " +\
                    str(df.iloc[25]) + ",[Mass_Ppv1_lim_sw] = " + str(df.iloc[26]) + ",[Mass_Ppv2_lim_sw] = " +\
                    str(df.iloc[27]) + ",[Mass_Ppv3_lim_sw] = " + str(df.iloc[28]) + ",[Mass_Ppv4_lim_sw] = " +\
                    str(df.iloc[29]) + ",[Mass_Ppv5_lim_sw] = " + str(df.iloc[30]) + ",[Mass_Ppv6_lim_sw] = " +\
                    str(df.iloc[31]) + ",[Mass_Ppv7_lim_sw] = " + str(df.iloc[32]) + ",[Mass_PV1_start] = " +\
                    str(df.iloc[33]) + ",[Mass_PV2_start] = " + str(df.iloc[34]) + ",[Mass_PV3_start] = " +\
                    str(df.iloc[35]) + ",[Mass_PV4_start] = " + str(df.iloc[36]) + ",[Mass_PV5_start] = " +\
                    str(df.iloc[37]) + ",[Mass_PV6_start] = " + str(df.iloc[38]) + ",[Mass_PV7_start] = " +\
                    str(df.iloc[39]) + ",[Mass_PV1_stop] = " + str(1-df.iloc[33]) + ",[Mass_PV2_stop] = " +\
                    str(1-df.iloc[34]) + ",[Mass_PV3_stop] = " + str(1-df.iloc[35]) + ",[Mass_PV4_stop] = " +\
                    str(1-df.iloc[36]) + ",[Mass_PV5_stop] = " + str(1-df.iloc[37]) + ",[Mass_PV6_stop] = " +\
                    str(1-df.iloc[38]) + ",[Mass_PV7_stop] = " + str(1-df.iloc[39]) + ", [DT] = ?"

        cursor = self.connection.cursor()
        cursor.execute(sql_query, int(df.iloc[8]), int(df.iloc[9]), int(df.iloc[10]), int(df.iloc[11]), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.connection.commit()

        return

    def decision_to_csv(self, df):

        df.to_csv('decision_found.csv')

        return

    def indicator_to_sql(self, increment):

        #sql_query = "WITH CTE AS (SELECT TOP 1 * FROM [TEST].[dbo].[temporary_0]) UPDATE CTE SET [index1] = "

        sql_query = "UPDATE [" + self.db_raw + "].[dbo].[INDEX_RT] SET [index] = " + str(increment)

        #sql_query = "INSERT INTO [TEST].[dbo].[INDEX_RT] ([index]) VALUES (" + str(increment) +")"

        cursor = self.connection.cursor()
        cursor.execute(sql_query)
        self.connection.commit()

        return

    def equipment_availability(self, data_from_sql):

        dgu1_availability = data_from_sql['F23'][0]
        dgu2_availability = data_from_sql['F24'][0]
        dgu3_availability = data_from_sql['F25'][0]
        dgu4_availability = data_from_sql['F26'][0]

        pv1_inv_availability = data_from_sql['F57'][0]
        pv2_inv_availability = data_from_sql['F58'][0]
        pv3_inv_availability = data_from_sql['F59'][0]
        pv4_inv_availability = data_from_sql['F60'][0]
        pv5_inv_availability = data_from_sql['F61'][0]
        pv6_inv_availability = data_from_sql['F62'][0]
        pv7_inv_availability = data_from_sql['F63'][0]

        ess1_inv_availability = data_from_sql['F74'][0]
        ess2_inv_availability = data_from_sql['F75'][0]

        return [dgu1_availability, dgu2_availability, dgu3_availability, dgu4_availability], \
               [pv1_inv_availability, pv2_inv_availability, pv3_inv_availability, pv4_inv_availability,
                pv5_inv_availability, pv6_inv_availability, pv7_inv_availability], [ess1_inv_availability,
                                                                                    ess2_inv_availability]

    def dgu_states(self, data_from_sql):  # data_from_sql равноценно db_datah[0]

        dgu1_statuses = list()
        dgu2_statuses = list()
        dgu3_statuses = list()
        dgu4_statuses = list()

        for hour in range(0, 3):
            if data_from_sql['F1'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 0 \
                    and data_from_sql['F9'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] != 30: # ранее вместо 51 было 30
                dgu1_statuses = dgu1_statuses + [0]
            elif data_from_sql['F9'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 30: # ранее вместо 51 было 30
                dgu1_statuses = dgu1_statuses + [1]

            if data_from_sql['F2'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 0 \
                    and data_from_sql['F10'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] != 30:
                dgu2_statuses = dgu2_statuses + [0]
            elif data_from_sql['F10'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 30:
                dgu2_statuses = dgu2_statuses + [1]

            if data_from_sql['F3'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 0 \
                    and data_from_sql['F11'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] != 30:
                dgu3_statuses = dgu3_statuses + [0]
            elif data_from_sql['F11'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 30:
                dgu3_statuses = dgu3_statuses + [1]

            if data_from_sql['F4'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 0 \
                    and data_from_sql['F12'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] != 30:
                dgu4_statuses = dgu4_statuses + [0]
            elif data_from_sql['F12'].groupby(data_from_sql.index.hour, sort=False).mean().iloc[hour] == 30:
                dgu4_statuses = dgu4_statuses + [1]

        return dgu1_statuses, dgu2_statuses, dgu3_statuses, dgu4_statuses

#conn_entity = DB_connector()
#db_datah = conn_entity.db_to_pd(240)






# print((db_datah[0].resample('H').mean()['F9'][-6:] == 30).sum())

# print((db_datah[1]['F9'][-6:] == 30))

# print(db_datah[1].groupby('F9').cumcount()[-1:])

# print(db_datah[0]['F9'][-1:])

#print(db_datah[1].loc[(db_datah[1]['F9'] == 30) & (db_datah[1]['F23'] == 0)])

#db_datah[0].to_csv('wtho.csv')

# print(DB_connector().DG_before(db_datah))

#print(db_datah[0]['F9'][0])

# print(db_datah[0]['F1'].groupby(db_datah[0].index.hour, sort=False).mean()[0])

# if db_datah[0]['F1'].groupby(db_datah[0].index.hour, sort=False).mean()[0:3].all() == 0:
#     print('hava')
#
#
#
# print(dgu_states(db_datah[0]))
#
# print(equipment_availability(db_datah[0]))

#print(db_datah[0])