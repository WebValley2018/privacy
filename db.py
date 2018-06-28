import mysql.connector as mariadb
from user import User
from collections import namedtuple
from token import Token


class DB:
    """
    CLASS DB FOR database integration
    -self.mariadb_connection -> connection to the database
    -self.cursor -> cursor to the database

    -METHODS:
        1. get_user_from_id -> get user class from user id --> PROBLEM!! the created user class doesn't has pw
        2. check_user -> check if user with given id exists

    -INITIALIZATION:
        1. user -> user of db
        2. password -> password of db
        3. database -> db
        4. host -> host in db
    """
    def __init__(self, user='Tovel', password='tovelwaterdoggo', database='Tovel', host='192.168.210.173'):
        self.mariadb_connection = mariadb.connect(user=user, password=password, database=database, host=host)
        self.cursor = self.mariadb_connection.cursor()

    def get_user_from_id(self, id):  # get user information, the user class has no pw, could raise errors
        self.cursor.execute("SELECT Name, Surname, Organization, Mail, Trusted, ID FROM Users WHERE ID=%s", (id,))
        for i in self.cursor:  # before passing the strings to the user class they are decoded
            user = namedtuple('TokenTuple', 'token_value, creation_date, dl_time, user')  # construct with named tuple
            new_user = User(user(i[0].decode('utf-8'), i[1].decode('utf-8'), i[2].decode('utf-8'), i[3].decode('utf-8'), i[4], i[5].decode('utf-8')))
            return new_user

    def check_user(self, id):
        self.cursor.execute("SELECT count(1) FROM Users WHERE ID=%s", (id,))
        for i in self.cursor:
            return True if i[0] == 1 else False
