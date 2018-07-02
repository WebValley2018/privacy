from collections import namedtuple
from time import localtime, time

from auth_token import Token
from excel import Excel
import mysql.connector as mariadb
from user import User

class DB:
    """
    CLASS DB FOR database integration
    -self.mariadb_connection -> connection to the database
    -self.cursor -> cursor to the database

    -METHODS:
        1. get_user_from_id -> get user class from user id --> PROBLEM!! the created user class doesn't has pw
        2. check_user -> check if user with given id exists
        3. check_token -> check if token with given value exists
        4.  get_id_from_username -> get user id from username
        5. register_token -> register new token in the db

    -INITIALIZATION:
        1. user -> user of db
        2. password -> password of dbK
        3. database -> db
        4. host -> host in db
    """
    def __init__(self, user='Tovel', password='tovelwaterdoggo', database='Tovel', host='192.168.210.173'):
        self.mariadb_connection = mariadb.connect(user=user, password=password, database=database, host=host)
        self.cursor = self.mariadb_connection.cursor()

    def get_user_from_id(self, id):  # get user information, the user class has no pw, could raise errors
        self.cursor.execute("SELECT Name, Surname, Username, Organization, Mail, Trusted, ID, Salt FROM Users WHERE ID=%s", (id,))
        for i in self.cursor:  # before passing the strings to the user class they are decoded
            user = namedtuple('UserTuple', 'name, surname, username, organization, mail, trust, id, salt')   # construct with named tuple
            new_user = User(user_data=user(i[0].decode('utf-8'), i[1].decode('utf-8'), i[2].decode('utf-8'), i[3].decode('utf-8'), i[4].decode('utf-8'), i[5], i[6].decode('utf-8'), i[7].decode('utf-8')))
            return new_user

    def check_user(self, id):
        self.cursor.execute("SELECT count(1) FROM Users WHERE ID=%s", (id,))
        for i in self.cursor:
            return True if i[0] == 1 else False

    def check_token(self, token_value):
        if token_value is None:
            return False
        self.cursor.execute("SELECT count(1), TTL, CreationDate FROM Token WHERE TokenValue=%s", (token_value,))
        for i in self.cursor:
            if i[0] == 1:
                return True if i[1] + i[2] > int(time()) else False
            else:
                return False

    def get_id_from_username(self, username):
        self.cursor.execute("SELECT ID FROM Users WHERE Username=%s", (username,))
        for i in self.cursor:
            return i[0].decode('utf-8')
        return False

    def register_token(self, token):  # register new token in the db
        self.cursor.execute("SELECT count(1) FROM Token WHERE TokenValue=%s", (token.token_value,))
        for i in self.cursor:
            if i[0] == 1:
                return False

        self.cursor.execute("INSERT INTO Token VALUES (%s, %s, %s, %s);", (token.token_value, token.ttl, token.creation_date, token.user))
        self.mariadb_connection.commit()
        return True
    
    def python_type_to_sql(self, t):
        """This method converts Python type names to the matching SQL ones"""
        types={
            "bool": "INTEGER",
            "int": "INTEGER",
            "float": "DOUBLE",
            "str": "TEXT",
            "datetime.date": "INT"
        }
        return types[t]
    
    def cast_python_type_for_sql(self, typestring, variable):
        functions = {
            "bool": int,
            "int": int,
            "float": float,
            "str": str,
            "datetime.date": lambda x: x.strftime('%s')
        }
        return str(functions[typestring](variable))
    
    def _get_parameters_generate_table(self, a, d):
        for e in a:
            yield from (e, self.python_type_to_sql(d[e]))
    def import_excel(self, fn, dataset_name):
        file = Excel(fn)
        #  Add table based on Excel file columns
        columns = file.get_columns()
        columns_data_type={c: file.get_data_type(i) for i, c in enumerate(columns)}

        #  TODO: Sanitize the query
        query = f'''CREATE TABLE `{dataset_name}` ({', '.join(f'`{c}` {self.python_type_to_sql(columns_data_type[c])}' for c in columns)});'''
        self.cursor.execute(query)
        self.mariadb_connection.commit()
        data = file.get_data()
        for d in data:
            query = f"""INSERT INTO `{dataset_name}` VALUES({', '.join(["%s" for _ in columns])});"""
            self.cursor.execute(query, tuple(self.cast_python_type_for_sql(columns_data_type[columns[i]], c) for i,c in enumerate(d)))
        self.mariadb_connection.commit()

d = DB()
d.import_excel("TestData.xlsx", "Test dataset")