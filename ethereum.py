from collections import namedtuple
from json import dumps, loads
from os.path import isfile
from time import time
from uuid import uuid4

from solc import compile_source
import web3
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
        self.w3 = web3.Web3(web3.Web3.HTTPProvider(providerAddress))
        #  Tell the blockchain which account to use
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]
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

        #  Loading logging smart contract
        if not isfile("smart-contracts/logging.json"):
            with open("smart-contracts/logging.sol") as f:
                #  Read Solidity source code
                logging_contract_source = f.read()  # read login smart contract from sourcefile
            #  Compile Solidity
            compiled_logging_contract = compile_source(logging_contract_source)
            #  Get interface for the contract
            logging_contract_iface = compiled_logging_contract["<stdin>:Logging"]
            #  Start the registration contract onto the blockchain
            Logging = self.w3.eth.contract(abi=logging_contract_iface['abi'], bytecode=logging_contract_iface['bin'])
            #  Initialize transaction
            tx_hash = Logging.constructor().transact()
            #  Get transaction details
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            #  Save ABI and contract address to file
            sc_log_abi=logging_contract_iface["abi"]
            sc_log_address=tx_receipt.contractAddress
            f = open("smart-contracts/logging.json", 'w')
            f.write(dumps({"address": sc_log_address, "abi": sc_log_abi}))
            f.close()
        else:
            #  Load smart contract data from file
            with open("smart-contracts/logging.json") as f:
                dati_sc_log = loads(f.read())
            sc_log_address = dati_sc_log["address"]
            sc_log_abi = dati_sc_log["abi"]
        #  Prepare the smart contract
        self.user_details = self.w3.eth.contract(
            address=sc_ud_address,
            abi=sc_ud_abi,
        )
        self.logging = self.w3.eth.contract(
            address=sc_log_address,
            abi=sc_log_abi,
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
        attempt_id = 'l'+str(uuid4())
        # attempt_id is the id of the event
        # The blockchain doesn'th have the capabilities to get the list of transaction
        # moreover, if you have a mismatch between the blockchain and the db it could
        # mean that the DB has been compromised. Therefore, let's save basic transaction data there too
        # Save on the blockchain the attempt_id and the user_id
        tx_hash = self.logging.functions.addEvent(attempt_id, dumps({
            "timestamp": int(time()),
            "user_id": user_id,
            "status": "in_progress"
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
        return attempt_id

    def _get_event(self, ev_id):
        return self.logging.functions.getEvent(ev_id).call()
    
    def save_auth_outcome(self, auth_id, outcome):
        # Save authentication outcome into the blockchain provided the authentication id
        # attempt_id is the id of the event, same as above
        #
        # Save on the blockchain the attempt_id and the outcome, that can be either True or False
        event = loads(self._get_event(auth_id))
        event["status"] = outcome
        tx_hash = self.logging.functions.addEvent(auth_id, dumps(event)).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)

    def report_login_failure(self, ip):
        attempt_id = 'F'+str(uuid4())
        #  Save basic transaction data on the DB
        tx_hash = self.logging.functions.addEvent(attempt_id, dumps({
            "timestamp": int(time()),
            "IP": ip
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
