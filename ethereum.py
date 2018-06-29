from collections import namedtuple
from uuid import uuid4

namedtuple('userData', 'id, h_pw')  # user data (id and hashe pw


class Ethereum:
    """
    CLASS ETHEREUM FOR INTERACTING WITH THE BlOCK CHAIN

    -METHODS:
        1. get_user -> get namedtuple(id, and hashed pw) given id, as long there will ce no bc the string will be empty
    -INITIALIZATION -> none
    """
    def __init__(self):
        pass

    def get_user(self, id):
        h_pw = 'f5b47c9bfcee500f0f460a902b70f7909a96d03c3c8efe069262ba5312a14e7e52e655e0c32e3e6c2f4f6519e48e9501f9b2edee55cabb191f9c49eec8af07bd'  # as long the blockchain isn't working the hashed pw will be a dummy string
        user = namedtuple('user_data', 'user_id user_pwd_hash')
        return user(id, h_pw)
    
    def save_auth_attempt(self, user_id):
        # Save authentication attempt into the blockchain provided the user id, None if the user doesn't exist
        attempt_id = str(uuid4)
        # attempt_id is the id of the event
        #
        # Save on the blockchain the attempt_id and the user_id
        #
        return attempt_id

    def save_auth_outcome(self, auth_id, outcome):
        # Save authentication outcome into the blockchain provided the authentication id
        # attempt_id is the id of the event, same as above
        #
        # Save on the blockchain the attempt_id and the outcome, that can be either True or False
        #
        pass
