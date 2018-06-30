import mysql.connector as mariadb
from user import User
from collections import namedtuple
from auth_token import Token
from time import localtime, time
from admin import Admin


class Transaction:
    def __init__(self, dbdata):
        self.id = dbdata[0].decode("utf-8")
        self.timestamp=int(dbdata[1])


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
        self.cursor.execute("INSERT INTO Token VALUES (%s, %s, %s, %s);", (token.token_value, token.ttl, token.creation_date, token.user))
        self.mariadb_connection.commit()

    def set_token_ttl(self, token_value):  # et ttl of a token to 0
        self.cursor.execute("UPDATE Token SET TTL = 0 WHERE TokenValue = %s", (token_value,))
        self.mariadb_connection.commit()

    def register_user(self, user):  # register new user in the db
        if self.check_user(user.username) or self.check_mail(user.mail):
            return False
        self.cursor.execute("INSERT INTO Users VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (user.username, user.name, user.surname, user.mail, user.id, user.salt, user.organization, user.trust))
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
    
    def save_audit_transaction(self, id):
        self.cursor.execute("INSERT INTO Audit VALUES (%s, %s)", (id,str(int(time()))))
        self.mariadb_connection.commit()
    
    def get_audit_data(self):
        self.cursor.execute("SELECT * FROM Audit")
        return [Transaction(l) for l in self.cursor.fetchall()]
