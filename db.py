import mysql.connector as mariadb
#import user_class

#mariadb_connection = mariadb.connect(user='Tovel', password='tovelwaterdoggo', database='Tovel', host='192.168.210.173')
#cursor = mariadb_connection.cursor()


class DB:
    def __init__(self, user='Tovel', password='tovelwaterdoggo', database='Tovel', host='192.168.210.173'):
        # self.mariadb_connection = mariadb.connect(user=user, password=password, database=database, host=host)
        # self.cursor = mariadb_connection.cursor()



'''
-> get user form id and hashed pw
->

'''