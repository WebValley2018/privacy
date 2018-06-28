from uuid import uuid4
import hashlib
from time import sleep
from collections import namedtuple

namedtuple('UserTuple', 'name, surname, organization, mail, trust, id')  # tuple for storing the User


class User:
    """"
    USER WILL BE A CLASS CONTAINING THE INFORMATION RELATED TO THE USER

    CLASS USER
    -self.name -> name of the user
    -self.surname -> surname of the user
    -self.mail -> mail of the user
    -self.id -> id of user
    -self.salt -> salt (is it more convenient to use rand instead of uuid4?)
    -self.h_pw -> hashed password of the user
    -self.organization -> Organization which the user belongs to
    -self.trust -> trust level of the level

    -METHODS:
         1. get_name -> get the name of the user
         2. get_surname -> get surname pf the user
         3. get mail -> get mail of the user
         4. get_id -> get id of the user
         5. get_trust -> get trust level of the user
         6. set_pw_hash -> set new hashed password
         7. verify_pw -> method taking as argument a string verifying the validity of a password
         8. get_user -> get user data in form of a namedtuple

    -INITIALIZATION:
         1. name -> name of the user
         2. surname -> surname of the user
         3. organization -> Organization which the user belongs to
         4. mail -> mail of the user
         5. pw -> password of the user
         6. trust -> trust level of the user
         7. id -> user id, if not provided it is created
         8. user_data -> named tuple, if it is not none the class is initialized with its values
    """
    def __init__(self, name='', surname='', organization='', mail='', pw='', trust=False, id=None, user_data=None):
        if user_data is not None:
            self.name = user_data.name
            self.surname = user_data.surname
            self.organization = user_data.organization
            self.mail = user_data.mail
            self.trust = user_data.trust
            self.id = user_data.id
        else:
            self.name = name
            self.surname = surname
            self.mail = mail
            self.organization = organization
            if id is None:
                self.id = str(uuid4())
            else:
                self.id = id
            if pw is not None:
                self.salt = str(uuid4().hex)
                self.h_pw = hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest()
            self.trust = trust

    def __string__(self):
        return self.name + " " + self.surname

    def get_name(self):  # get the name of the user
        return self.name

    def get_surname(self):  # get mail of the user
        return self.surname

    def get_mail(self):  # get mail of the user
        return self.mail

    def get_id(self):  # get id of the user
        return self.id

    def get_trust_level(self):  # get the trust level of the user
        return self.trust

    def set_pw_hash(self, pw):
        self.salt = str(uuid4().hex)
        self.h_pw = hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest()

    def verify_pw(self, pw):  # method taking as argument a string verifying the validity of a password
        print(pw)
        print(self.salt)
        print(self.h_pw)
        if self.h_pw is None:
            return False
        if hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest() == self.h_pw:
            return True
        else:
            sleep(1)
            return False

    def get_user(self):  # get user as named tuple
        user = namedtuple('UserTuple', 'name, surname, organization, mail, trust, id')
        return user(self.name, self.surname, self.organization, self.mail, self.trust, self.id)

