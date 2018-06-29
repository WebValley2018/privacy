from user import User
from uuid import uuid4
import pyotp
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
    def __init__(self, username, name, surname, pw):
        self.username = username
        self.name = name
        self.surname = surname
        self.salt = str(uuid4().hex)
        self.id = 'A' + str(uuid4())
        self.otp_key = pyotp.random_base32()
        self.h_pw = hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest()
