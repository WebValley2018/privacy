from datetime import datetime, timedelta
from uuid import uuid4
import secrets
from collections import namedtuple
from time import localtime, time

namedtuple('TokenTuple', 'token_value, creation_date, ttl, user')  # tuple for storing the Token


class Token:
    """
   TOKEN WILL BE STRING OF GIVEN LENGTH COMPOSED OF UNDERCASE LETTERS('a' - 'z') AND DIGITS('0' - '9')

   CLASS TOKEN:
   -self.creation_date = time of creation of the token
   -self.ttl = expiration date of the token
   -self.token_length = length of the token
   -self.token_value = value of the token
   -self.user = id of the user which created the token

   -METHODS:
     1. get_creation_date -> get time of creation of the token
     2. get_dl_time -> get expiration date of the token
     3. get_rem_time -> get remaining time in which token will be valid
     4. get_token_value -> get value of the token
     5. get_token -> get a tuple of 4 elements which stores self.token_value, self.creation_date, self.dl_time, self.user

   -INITIALIZATION:
     1. token_length -> length of the token
     2. time delta -> time in which token will be valid
     3. user -> user id which created token
     4. token_data -> tuple of 4 elements, if token_data is not None token_value, creation_date, dl_time, user of the class
            will be get value of token_data
   """
    def __init__(self, token_length=16, time_delta=15, user=None, token_data=None):  # timedelta is in seconds
        if token_data is None:  # if token_data is not provided in arguments initialize with custom values
            self.creation_date = int(time())  # time of creation of the token
            self.dl_time =  self.creation_date + time_delta * 60 # expiration date of the token
            self.token_length = token_length  # length of the token
            self.token_value = secrets.token_hex(token_length)  # value of the token
            self.user = user  # id of the user which created the token
            self.ttl = time_delta
        else:  # else initialize with values provided by the TokenTuple
            self.token_value = token_data.token_value
            self.creation_date = token_data.creation_date
            self.dl_time = token_data.creation_date + token_data.ttl
            self.user = token_data.user
            self.token_length = len(self.token_value)
            self.ttl = token_data.ttl

    def __str__(self):
        return self.token_value

    def __len__(self):
        return self.token_length

    def get_creation_date(self):  # get time of creation of the token
        return self.creation_date

    def get_dl_time(self):  # get expiration date of the token
        return self.dl_time

    def get_rem_time(self):  # get remaining time in which token will be valid
        return self.dl_time - self.creation_date

    def get_token_value(self):  # get value of the token
        return self.token_value

    def get_token(self):  # get named tuple which stores self.token_value, self.creation_date, self.dl_time, self.user
        tkn = namedtuple('TokenTuple', 'token_value, creation_date, dl_time, user')  # named tuple "TokenTuple"
        return tkn(self.token_value, self.creation_date, self.ttl, self.user)