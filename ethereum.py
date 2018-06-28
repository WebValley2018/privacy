from collections import namedtuple

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
        user = namedtuple('user_data', 'user_id username user_pwd_hash')
        return user(id, "eutampieri", h_pw)
