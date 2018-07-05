from collections import namedtuple
from time import localtime, time
import datetime
from uuid import uuid4
import hashlib
import string
from admin import Admin
import json


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
        2. check_user -> check if user with given username exists
        3. check_token -> check if token with given value exists
        4. get_id_from_username -> get user id from username
        5. register_token -> register new token in the db
        6. check_mail -> check if user with given mail exists
        7. set_token_ttl -> set ttl of a token to 0
        8. register_user -> register new user in the db
        9. register_admin -> register new admin in the db
        10. check_admin -> check if admin with given username exists
        11. register_admin -> register admin given an admin object
        12. get_otp_key -> get otp key of admin
        13. get_admin -> get admin object given the admin id
        14. get_admin_id_from_username -> get the id of a user given the username
        15. set_admin_token_ttl -> set the ttl of a admin token to 0, in order to make the session expire
        16. check_admin_token -> check if admin token exists end if it's expired
        17. register_admin_token -> insert new admin token in the database given token object
        18. save_audit_transaction -> save a new audit transaction in the databse
        19. get_userid_from_token -> give an active token find the user_id of the user, admin -> True if it's an admin Token
        20. python_type_to_sql -> transforms the phython types to sql types
        21. cast_python_type_for_sql -> cast phython types to sql types
        22. _get_parameters_generate_table -> get parameters from general table
        23. _sanitize_col_nam -> sanitaze name
        24. import_excel -> import new exel file to database
        25. change_admin_pwd -> set a new admin password hash
        26. change_user_salt -> change the password salt of an user
        27. _can_load_ds -> check if user with given trust level can have access to a database
        28. check_dataset_exsistence -> check if database exists
        29. get_dataset -> load a dataset from database given his id
        30. get_datasets -> get all dataset of a user with given trust level
        31. get_dataset_name -> get the name of al datset given his id and the trust level of the user
        32. get_dataset_row -> get a row of a dataset given id and trust level
        33. get_dataset_columns -> get names of columns of a datset given dataset id and trust level
        34. modify_row -> modify row of a datset given dataset id and trust level
        35. delete_row -> delete row of a datset given dataset id and trust level
        36. new_row -> create new row of a datset given dataset id and trust level

    -INITIALIZATION:
        1. user -> user of db
        2. password -> password of dbK
        3. database -> db
        4. host -> host in db
    """
    def __init__(self, user='Tovel', password='tovelwaterdoggo', database='Tovel', host='192.168.210.173'):
        self.database_name = database
        self.mariadb_connection = mariadb.connect(user=user, password=password, database=database, host=host)
        self.cursor = self.mariadb_connection.cursor()

    def get_user_from_id(self, id):  # get user information, the user class has no pw, could raise errors
        self.cursor.execute("SELECT Name, Surname, Username, Organization, Mail, TrustLevel, ID, Salt FROM Users WHERE ID=%s", (id,))
        for i in self.cursor:  # before passing the strings to the user class they are decoded
            user = namedtuple('UserTuple', 'name, surname, username, organization, mail, trust_level, id, salt')   # construct with named tuple
            new_user = User(user_data=user(i[0].decode('utf-8'), i[1].decode('utf-8'), i[2].decode('utf-8'), i[3].decode('utf-8'), i[4].decode('utf-8'), i[5], i[6].decode('utf-8'), i[7].decode('utf-8')))
            return new_user

    '''def check_user(self, id):  # should check user get id or username???
        self.cursor.execute("SELECT count(1) FROM Users WHERE ID=%s", (id,))
        for i in self.cursor:
            return True if i[0] == 1 else False'''
    
    def check_token(self, token_value):  # check if token with given value exists
        if token_value is None:
            return False
        self.cursor.execute("SELECT count(1), TTL, CreationDate FROM Token WHERE TokenValue=%s", (token_value,))
        for i in self.cursor:
            if i[0] == 1:
                return True if i[1] + i[2] > int(time()) else False
            else:
                return False

    def check_user(self, username):  # check if user with given username exists
        if username is None:
            return False
        self.cursor.execute("SELECT count(1) FROM Users WHERE Username=%s", (username,))
        for i in self.cursor:
            return True if i[0] else False

    def check_mail(self, mail):  # check if user with given mail exists
        if mail is None:
            return False
        self.cursor.execute("SELECT count(1) FROM Users WHERE Mail=%s", (mail,))
        for i in self.cursor:
            return True if i[0] else False

    def get_id_from_username(self, username):  # get user id from username
        if not self.check_user(username):
            return None
        self.cursor.execute("SELECT ID FROM Users WHERE Username=%s", (username,))
        for i in self.cursor:
            return i[0].decode('utf-8')
        return None
    
    def register_token(self, token):  # register new token in the db
        self.cursor.execute("SELECT count(1) FROM Token WHERE TokenValue=%s", (token.token_value,))
        for i in self.cursor:
            if i[0] == 1:
                return False
        self.cursor.execute("INSERT INTO Token VALUES (%s, %s, %s, %s);", (token.token_value, token.ttl, token.creation_date, token.user))
        self.mariadb_connection.commit()
        return True

    def set_token_ttl(self, token_value):  # et ttl of a token to 0
        self.cursor.execute("UPDATE Token SET TTL = 0 WHERE TokenValue = %s", (token_value,))
        self.mariadb_connection.commit()

    def register_user(self, user):  # register new user in the db
        if self.check_user(user.username) or self.check_mail(user.mail):
            return False
        self.cursor.execute("INSERT INTO Users VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (user.username, user.name, user.surname, user.mail, user.id, user.salt, user.organization, user.trust_level))
        self.mariadb_connection.commit()
        return True

    def check_admin(self, username):  # check if admin with given username exists
        if username is None:
            return False
        self.cursor.execute("SELECT count(1) FROM Administrators WHERE Username=%s", (username,))
        for i in self.cursor:
            return True if i[0] else False

    def register_admin(self, admin):  # register new admin in the db
        if self.check_admin(admin.username):
            return False
        self.cursor.execute("INSERT INTO Administrators VALUES (%s, %s, %s, %s, %s, %s, %s);", (admin.id, admin.username, admin.name, admin.surname, admin.h_pw, admin.salt, admin.otp_key,))
        self.mariadb_connection.commit()
        return True

    def get_otp_key(self, id):
        self.cursor.execute("SELECT count(1), OTPKey FROM Administrators WHERE ID=%s", (id,))
        for i in self.cursor:
            return None if i[0] == 0 else i[1].decode('utf-8')
    
    def get_admin(self, id):
        self.cursor.execute("SELECT ID, Username, Name, Surname, Password, Salt, OTPKey FROM Administrators WHERE ID=%s", (id,))
        for i in self.cursor:
            admin = namedtuple('AdminTuple', 'id, username, name, surname, h_pw, salt, otp_key')
            return Admin(admin_data=admin(i[0].decode('utf-8'), i[1].decode('utf-8'), i[2].decode('utf-8'), i[3].decode('utf-8'), i[4].decode('utf-8'), i[5].decode('utf-8'), i[6].decode('utf-8')))

    def get_admin_id_from_username(self, username):  # get user id from username
        if not self.check_admin(username):
            return None
        self.cursor.execute("SELECT ID FROM Administrators WHERE Username=%s", (username,))
        for i in self.cursor:
            return i[0].decode('utf-8')
        return None

    def set_admin_token_ttl(self, token_value):  # et ttl of a token to 0
        self.cursor.execute("UPDATE AdminToken SET TTL = 0 WHERE TokenValue = %s", (token_value,))
        self.mariadb_connection.commit()

    def check_admin_token(self, token_value):  # check if token with given value exists
        if token_value is None:
            return False
        self.cursor.execute("SELECT count(1), TTL, CreationDate FROM AdminToken WHERE TokenValue=%s", (token_value,))
        for i in self.cursor:
            if i[0] == 1:
                return True if i[1] + i[2] > int(time()) else False
            else:
                return False

    def register_admin_token(self, token):  # register new token in the db
        self.cursor.execute("INSERT INTO AdminToken VALUES (%s, %s, %s, %s);", (token.token_value, token.ttl, token.creation_date, token.user))
        self.mariadb_connection.commit()
    
    def save_audit_transaction(self, id):
        self.cursor.execute("INSERT INTO Audit VALUES (%s, %s)", (id,str(int(time()))))
        self.mariadb_connection.commit()
    
    def get_userid_from_token(self, token, admin=False):
        self.cursor.execute("SELECT User FROM "+("Admin" if admin else '')+"Token WHERE TokenValue = %s", (token, ))
        return self.cursor.fetchall()[0][0].decode("utf-8")
    
    def python_type_to_sql(self, t):
        """This method converts Python type names to the matching SQL ones"""
        types={
            "bool": "INTEGER",
            "int": "INTEGER",
            "float": "DOUBLE",
            "str": "TEXT",
            "datetime.date": "TEXT"
        }
        return types[t]
    
    def cast_python_type_for_sql(self, typestring, variable):
        functions = {
            "bool": int,
            "int": lambda x: int(x) if x else None,
            "float": float,
            "str": str,
            "datetime.date": str#lambda x: x.strftime('%s')
        }
        return variable if variable == '' else str(functions[typestring](variable))
    
    def _get_parameters_generate_table(self, a, d):
        for e in a:
            yield from (e, self.python_type_to_sql(d[e]))
    
    def _sanitize_col_name(self, col):
        col = col.title()
        return ''.join(['' if not(c in [str(n) for n in range(10)] or c in string.ascii_letters or c in ["_"]) else c for c in col])

    def import_excel(self, fn, dataset_name, trust_level=2):
        file = Excel(fn)
        dataset_id = str(uuid4())
        #  Add table based on Excel file columns
        columns = file.get_columns()
        columns_data_type={c: file.get_data_type(i) for i, c in enumerate(columns)}
        self.cursor.execute("INSERT INTO Datasets VALUES (%s, %s, %s)", (dataset_name, dataset_id, str(trust_level)))
        #  TODO: Sanitize the query
        query = f'''CREATE TABLE `{dataset_name}` (_row_id TEXT, {', '.join(f'`{self._sanitize_col_name(c) if c else "column_"+str(i)}` {self.python_type_to_sql(columns_data_type[c])}' for i,c in enumerate(columns))});'''
        self.cursor.execute(query)
        self.mariadb_connection.commit()
        data = file.get_data()
        for d in data:
            row_id = str(uuid4()).replace('-','')
            query = f"""INSERT INTO `{dataset_name}` VALUES(%s, {', '.join(["%s" for _ in columns])});"""
            self.cursor.execute(query, (row_id,) + tuple(self.cast_python_type_for_sql(columns_data_type[columns[i]], c) for i,c in enumerate(d)))
            self.mariadb_connection.commit()
    
    def change_admin_pwd(self, admin, oldpwd, pwd):
        """This function changes admin's password given the old password and the new password. Returns True on success"""
        if admin.verify_pw(oldpwd) and admin.verify_pw(pwd):
            return 0
        elif admin.verify_pw(oldpwd):
            salt = str(uuid4().hex)
            hash_pw = hashlib.sha512((pwd + salt).encode("utf-8")).hexdigest()
            self.cursor.execute("UPDATE Administrators SET Salt = %s, Password = %s WHERE ID = %s", (salt, hash_pw, admin.id))
            self.mariadb_connection.commit()
            return 2
        else:
            return 1
    
    def change_user_salt(self, userid, salt):
        self.cursor.execute("UPDATE Users SET Salt = %s WHERE ID = %s", (salt, userid))
        self.mariadb_connection.commit()

    def _can_load_ds(self, dataset, tl):
        self.cursor.execute("SELECT RequiredTrust FROM Datasets WHERE ID = %s", (dataset, ))
        return int(self.cursor.fetchall()[0][0])<=tl

    def check_dataset_exsistence(self, dataset):
        self.cursor.execute("SELECT * FROM Datasets WHERE Name = %s;", (dataset,))
        res = self.cursor.fetchall()
        return len(res) == 1
    
    def get_dataset(self, dataset_id, trust_level, return_row_id=False):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s",(dataset_id,))
        dataset_name = self.cursor.fetchall()[0][0]
        #  dataset_name = dataset_name.decode("utf-8") if type(dataset_name) is bytes else dataset_name
        self.cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s", (dataset_name,))
        #print(self.cursor.fetchall())
        colonne = [{"title": row[3]} for row in (self.cursor.fetchall() if return_row_id else self.cursor.fetchall()[1:])]
        self.cursor.execute("SELECT * FROM `"+str(dataset_name.decode('utf-8'))+"`;")
        return {"data": [[(str(j.decode("utf-8")) if type(j) is bytes else j) for j in [n for n in (list(r) if return_row_id else list(r)[1:])]] for r in list(self.cursor)], "columns": colonne}
    
    def get_datasets(self, trust_level):
        self.cursor.execute("SELECT Name, ID FROM Datasets WHERE RequiredTrust <= %s", (trust_level,))
        return [{"name":e[0].decode("utf-8"), "id": e[1].decode("utf-8")} for e in self.cursor.fetchall()]

    def get_dataset_name(self, dataset_id, trust_level):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s", (dataset_id,))
        return self.cursor.fetchall()[0][0]

    def get_dataset_row(self, dataset_id, row, trust_level):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s",(dataset_id,))
        dataset_name = self.cursor.fetchall()[0][0]
        self.cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s", (dataset_name,))
        #print(self.cursor.fetchall())
        colonne = [row[3] for row in self.cursor.fetchall()[1:]]
        self.cursor.execute("SELECT * FROM `"+str(dataset_name.decode('utf-8'))+"` WHERE _row_id = %s;", (row,))
        res=self.cursor.fetchall()
        return {"data": [str(v.decode("utf-8")) if type(v) is bytes else v for v in res[0][1:]], "columns": colonne}

    def get_dataset_columns(self, dataset_id, trust_level):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s",(dataset_id,))
        dataset_name = self.cursor.fetchall()[0][0]
        self.cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s", (dataset_name,))
        colonne = [row[3] for row in self.cursor.fetchall()[1:]]
        return {"columns": colonne}

    def modify_row(self, dataset_id, data, row, trust_level):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s", (dataset_id,))
        dataset_name = self.cursor.fetchall()[0][0]
        self.cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s", (dataset_name,))
        new_data = []
        for d in data:
            new_data.append(d.decode('utf-8') if type(d) == bytes else d)
        if type(dataset_name) is bytes:
            dataset_name = dataset_name.decode('utf-8')
        colonne = [row[3] for row in self.cursor.fetchall()[1:]]
        for idx, c in enumerate(colonne):
            self.cursor.execute("UPDATE `" + str(dataset_name) + "` SET `" + c + "`=%s WHERE _row_id = %s", (str(new_data[idx]), str(row),))
            self.mariadb_connection.commit()

    def delete_row(self, dataset_id, row, trust_level):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s", (dataset_id,))
        dataset_name = self.cursor.fetchall()[0][0]
        if type(dataset_name) is bytes:
            dataset_name = dataset_name.decode('utf-8')
        self.cursor.execute(f"DELETE FROM `{dataset_name}` WHERE _row_id = %s", (row,))
        self.mariadb_connection.commit()

    def new_row(self, dataset_id, data, trust_level):
        if not self._can_load_ds(dataset_id, trust_level):
            return None
        self.cursor.execute("SELECT Name FROM Datasets WHERE ID = %s", (dataset_id,))
        dataset_name = self.cursor.fetchall()[0][0]
        if type(dataset_name) is bytes:
            dataset_name = dataset_name.decode('utf-8')
        val = '%s, '
        for i in range(len(data)):
            val += '%s'
            if not i == len(data) - 1:
                val += ','
        new_row_id = str(uuid4())
        # print(f"INSERT INTO `{dataset_name}` VALUES ({val});", (new_row_id, ) + data)
        self.cursor.execute(f"INSERT INTO `{dataset_name}` VALUES ({val}) ;", (new_row_id, ) + data)
        self.mariadb_connection.commit()

