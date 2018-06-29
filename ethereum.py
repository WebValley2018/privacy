from collections import namedtuple
from uuid import uuid4

namedtuple('userData', 'id, h_pw')  # user data (id and hashe pw

# CanCan*er starts here

import web3
import json

from solc import compile_source
from web3 import Web3 
from web3.contract import ConciseContract


class Ethereum:
    """
    CLASS ETHEREUM FOR INTERACTING WITH THE BlOCK CHAIN

    -METHODS:
        1. get_user -> get namedtuple(id, and hashed pw) given id, as long there will ce no bc the string will be empty
    -INITIALIZATION -> none
    """
    def __init__(self, providerAddress = 'http://127.0.0.1:7545'):
        self.w3 = Web3(Web3.HTTPProvider(providerAddress))
        with open("smart-contracts/user-details.sol") as f:
            login_contract_source = f.read()  # read login smart contract from sourcefile
        #with open("smart-contracts/auth-logging.sol") as f:
        #    login_contract = f.read()
        compiled_login_contract = compile_source(login_contract_source)
        login_contract_iface = compiled_login_contract["<stdin>:UserDetails"]
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]
        UserDetails = self.w3.eth.contract(abi=login_contract_iface['abi'], bytecode=login_contract_iface['bin'])
        tx_hash = UserDetails.constructor().transact()
        # Wait for the transaction to be mined, and get the transaction receipt
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        # Create the contract instance with the newly-deployed address
        self.user_details = self.w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=login_contract_iface['abi'],
        )


    def get_user(self, id):
        h_pw = self.user_details.functions.getPwdHash(id).call()
        user = namedtuple('user_data', 'user_id user_pwd_hash')
        return user(id, h_pw)
    
    def set_user_hash(self, uid, p_hash):
        tx_hash = self.user_details.functions.addUser(uid, p_hash).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)

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

    def report_login_failure(self):
        # Save authentication outcome into the blockchain provided the authentication id
        # attempt_id is the id of the event, same as above
        #
        # Save on the blockchain the attempt_id and the outcome, that can be either True or False
        #
        pass
