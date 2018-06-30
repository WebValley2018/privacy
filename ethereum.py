from collections import namedtuple
from uuid import uuid4
from json import dumps, loads
from os.path import isfile
import web3
import json

from solc import compile_source
from web3 import Web3 
from web3.contract import ConciseContract

namedtuple('userData', 'id, h_pw')  # user data (id and hashe pw


class Ethereum:
    """
    Ethereum class to deal with smart contracts

    -METHODS:
        1. get_user -> get namedtuple(id, and hashed pw) given id, as long there will ce no bc the string will be empty
        -- Jakob please implement
    -INITIALIZATION -> FIXIT
    """
    def __init__(self, providerAddress = 'http://127.0.0.1:7545'):
        #  Inizialize Web3 object
        self.w3 = Web3(Web3.HTTPProvider(providerAddress))
        #  Now dealing with User details smart contract
        if not isfile("smart-contracts/user-details.json"):
            with open("smart-contracts/user-details.sol") as f:
                #  Read Solidity source code
                login_contract_source = f.read()  # read login smart contract from sourcefile
            #  Compile Solidity
            compiled_login_contract = compile_source(login_contract_source)
            #  Get interface for the contract
            login_contract_iface = compiled_login_contract["<stdin>:UserDetails"]
            #  Start the registration contract onto the blockchain
            UserDetails = self.w3.eth.contract(abi=login_contract_iface['abi'], bytecode=login_contract_iface['bin'])
            #  Tell the blockchain which account to use
            self.w3.eth.defaultAccount = self.w3.eth.accounts[0]
            #  Initialize transaction
            tx_hash = UserDetails.constructor().transact()
            #  Get transaction details
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            #  Save ABI and contract address to file
            sc_ud_abi=login_contract_iface["abi"]
            sc_ud_address=tx_receipt.contractAddress
            f = open("smart-contracts/user-details.json", 'w')
            f.write(dumps({"address": sc_ud_address, "abi": sc_ud_abi}))
            f.close()
        else:
            #  Load smart contract data from file
            with open("smart-contracts/user-details.json") as f:
                dati_sc_ud = loads(f.read())
            sc_ud_address = dati_sc_ud["address"]
            sc_ud_abi = dati_sc_ud["abi"]
        #  Prepare the smart contract
        self.user_details = self.w3.eth.contract(
            address=sc_ud_address,
            abi=sc_ud_abi,
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
