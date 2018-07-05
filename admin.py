from user import User
from uuid import uuid4
import pyotp
import hashlib
from collections import namedtuple
from time import sleep


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
    def __init__(self, username='', name='', surname='', pw='', admin_data=None):
        if admin_data is None:
            self.username = username
            self.name = name
            self.surname = surname
            self.salt = str(uuid4().hex)
            self.id = 'A' + str(uuid4())
            self.otp_key = pyotp.random_base32()
            self.totp = pyotp.TOTP(self.otp_key)
            self.h_pw = hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest()
        else:
            self.username = admin_data.username
            self.name = admin_data.name
            self.surname = admin_data.surname
            self.id = admin_data.id
            self.h_pw = admin_data.h_pw
            self.otp_key = admin_data.otp_key
            self.totp = pyotp.TOTP(self.otp_key)
            self.salt = admin_data.salt

    def get_admin(self):
        admin = namedtuple('AdminTuple', 'id, username, name, surname, h_pw, salt, otp_key')
        return admin(self.id, self.username, self.name, self.surname, self.h_pw, self.salt, self.otp_key)

    def verify_otp(self, otp):
        return self.totp.verify(otp)

    def new_opt_key(self, key):
        self.otp_key = key
        self.totp = pyotp.TOTP(self.otp_key)



