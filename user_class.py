from uuid import uuid4
import hashlib
from time import sleep


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
         6. verify_pw -> method taking as argument a string verifying the validity of a password

    -INITIALIZATION:
         1. name -> name of the user
         2. surname -> surname of the user
         3. organization -> Organization which the user belongs to
         4. mail -> mail of the user
         5. pw -> password of the user
         6. trust -> trust level of the user
    """
    def __init__(self, name, surname, organization, mail, pw, trust=False):
        self.name = name
        self.surname = surname
        self.mail = mail
        self.organization = organization
        self.id = str(uuid4())
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

    def get_trust(self):  # get the trust level of the user
        return self.trust

    def verify_pw(self, pw):  # method taking as argument a string verifying the validity of a password
        if hashlib.sha512((pw + self.salt).encode("utf-8")).hexdigest() == self.h_pw:
            return True
        else:
            sleep(1)
            return False

