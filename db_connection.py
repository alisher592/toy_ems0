import pymssql
import pandas as pd

host = r'192.168.20.139'
port = r'1433'
user = r'ASU-TP'
password = r'#KznZN43'
database = r'TEST'


conn = pymssql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database
)
cursor = conn.cursor(as_dict=True)

#conn = pymssql.connect(server, user, password, "tempdb")
# cursor = conn.cursor()
# cursor.execute("""
# IF OBJECT_ID('persons', 'U') IS NOT NULL
#     DROP TABLE persons
# CREATE TABLE persons (
#     id INT NOT NULL,
#     name VARCHAR(100),
#     salesrep VARCHAR(100),
#     PRIMARY KEY(id)
# )
# """)
#
# cursor.execute('Select top 4 location_id, description from t_location with (nolock)')
# data = cursor.fetchall()
# data_df = pd.DataFrame(data)

cursor.close()