from datetime import datetime, timedelta
from uuid import uuid4
import secrets


class Token:
    """
   TOKEN WILL BE STRING OF GIVEN LENGTH COMPOSED OF UNDERCASE LETTERS('a' - 'z') AND DIGITS('0' - '9')

   CLASS TOKEN:
   -self.act_time = time of creation of the token
   -self.ttl = expiration date of the token
   -self.token_length = length of the token
   -self.token_value = value of the token
   -self.user = id of the user which created the token

   -METHODS:
     1. get_act_time -> get time of creation of the token
     2. get_dl_time -> get expiration date of the token
     3. get_rem_time -> get remaining time in which token will be valid
     4. get_token_value -> get value of the token
     5. get_token -> get list of 4 elements which store self.token_value, self.act_time, self.dl_time, self.user

   -INITIALIZATION:
     1. token_lenght -> lenght of the token
     2. time delta -> time in which token will be valid
     3. user -> user id which created token
     4. token_data -> array of 4 elements, if token_data is not None token_value, act_time, dl_time, user of the class will be get value of token_data
   """
    def __init__(self, token_length=16, time_delta=15, user=str(uuid4()), token_data=None):  # timedelta is in minutes
        if token_data is None:  # if token_data is not provided in arguments initialize with custom values
            self.act_time = datetime.now()  # time of creation of the token
            self.dl_time = self.act_time + timedelta(minutes=time_delta)  # expiration date of the token
            self.token_length = token_length  # length of the token
            self.token_value = secrets.token_hex(token_length)  # value of the token
            self.user = user  # id of the user which created the token
        else:  # else initialize with values provided by the token_data list
            self.token_value = token_data[0]
            self.act_time = token_data[1]
            self.dl_time = token_data[2]
            self.user = token_data[3]
            self.token_lenght = len(self.token_value)

    def __str__(self):
        return self.token_value

    def __len__(self):
        return self.token_length

    def get_act_time(self):  # get time of creation of the token
        return self.act_time

    def get_dl_time(self):  # get expiration date of the token
        return self.dl_time

    def get_rem_time(self):  # get remaining time in which token will be valid
        return self.dl_time - self.act_time

    def get_token_value(self):  # get value of the token
        return self.token_value

    def get_token(self):  # get list of 4 elements which store self.token_value, self.act_time, self.dl_time, self.user
        return [self.token_value, self.act_time, self.dl_time, self.user]