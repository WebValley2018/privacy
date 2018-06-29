from user import User
from uuid import uuid4
import hashlib


class Admin(User):
    """
    ADMIN CLASS for admins
    the super class is User

    METHODS:
        0. see the methods of the user class

    INITIALIZATION:
        1. username -> username of the admin
        2. name -> name of the admin
        3. surname -> surname of the admin
        4. mail -> mail of the admin

    """
    def __init__(self, username, name, surname, mail, pw):
        self.username = username
        self.name = name
        self.surname = surname
        self.mail = mail
        self.salt = str(uuid4().hex)
        self.h_pw = hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest()
