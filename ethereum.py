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
        h_pw = ''  # as long the blockchain isn't working the hashed pw will be an empty string
        user = namedtuple('userData', 'id, h_pw')
        return user(id, h_pw)
