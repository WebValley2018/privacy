from collections import namedtuple
from json import dumps, loads
from os.path import isfile
from time import time
from uuid import uuid4

from db import DB
from solc import compile_source
import web3
from web3.contract import ConciseContract

namedtuple('userData', 'id, h_pw')  # user data (id and hashe pw
database = DB()


class Transaction:
    def __init__(self, dbdata, eth):
        self.id = dbdata[0].decode("utf-8")
        self.timestamp=int(dbdata[1])
        eth_data = eth.get_event(self.id)
        self.data = loads("{}" if eth_data == '' else eth_data )
    
    def event_description(self):
        kinds = {
            "F": "Unrecognized user with IP address #IP tried to login",
            "l": "User " + ("#userid logged in" if (self.data["status"] if "status" in self.data.keys() else '') else "failed to log in"),
            "g": "Nonexisting admin tried to login from IP address #IP",
            "n": "Existing admin #adminid " + ("logged in" if (self.data["status"] if "status" in self.data.keys() else '') else "failed to log in"),
            "x": "User #userid accessed the dataset '#dataset'",
            "q": "User #userid queried the dataset '#dataset'",
            "p": "User #userid changed his password",
            "m": "record edited", #  TODO: Fix everything there
            "D": "record added",
            "t": "record deleted",
            "h": "health",
            "i": "import",
            "r": "user registration"
        }
        kind = kinds[self.id[0]]
        if self.id[0] == "n":
            if "status" in self.data.keys():
                admin = database.get_admin(self.data["user_id"])
                kind = kind.replace("#adminid", admin.name + " " + admin.surname)
            else:
                kind = kind.replace("#adminid", "")
        elif self.id[0] in ["l", 'x', 'q', 'p'] and "status" in self.data.keys():
            user = database.get_user_from_id(self.data["user_id"])
            kind = kind.replace("#userid", user.name + " " + user.surname + " from " + user.organization)
        elif self.id[0] in ["l", 'x', 'q', 'p'] and "user" in self.data.keys():
            user = database.get_user_from_id(self.data["user"])
            kind = kind.replace("#userid", user.name + " " + user.surname + " from " + user.organization)

        for k, val in self.data.items():
            kind = kind.replace('#' + str(k), str(val))
        return kind

    def security_score(self):
        dict = {
            "F": "danger",
            "l": ("warning" if not (self.data["status"] if "status" in self.data.keys() else '') else "success"),
            "g": "danger",
            "n": ("warning" if not (self.data["status"] if "status" in self.data.keys() else '') else "success"),
            "x": "success",
            "q": "success",
            "p": "success",
            "m": "success",
            "D": "success",
            "t": "warning",
            "h": "danger",
            "i": "success",
            "r": "success"
        }
        return dict[self.id[0]]


class Ethereum:
    """
    Ethereum class to deal with smart contracts

    -METHODS:
        1. get_user -> get namedtuple(id, and hashed pw) given id, as long there will ce no bc the string will be empty
        -- Jakob please implement
    -INITIALIZATION -> FIXIT
    """
    def __init__(self, providerAddress = 'http://192.168.210.173:8545'):
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

    def save_auth(self, user_id, outcome, admin=False):
        # Save authentication attempt into the blockchain provided the user id, None if the user doesn't exist
        attempt_id = ('n' if admin else 'l')+str(uuid4())
        # attempt_id is the id of the event
        # The blockchain doesn'th have the capabilities to get the list of transaction
        # moreover, if you have a mismatch between the blockchain and the db it could
        # mean that the DB has been compromised. Therefore, let's save basic transaction data there too
        database.save_audit_transaction(attempt_id)
        # Save on the blockchain the attempt_id and the user_id
        tx_hash = self.logging.functions.addEvent(attempt_id, dumps({
            "timestamp": int(time()),
            "user_id": user_id,
            "status": outcome
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)

    def get_event(self, ev_id):
        return self.logging.functions.getEvent(ev_id).call()

    def report_login_failure(self, ip, admin=False):
        #  TODO: Fix IP
        attempt_id = ('g' if admin else 'F')+str(uuid4())
        #  Save basic transaction data on the DB
        database.save_audit_transaction(attempt_id)
        tx_hash = self.logging.functions.addEvent(attempt_id, dumps({
            "timestamp": int(time()),
            "IP": ip
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def get_audit_len(self):
        return self.logging.functions.getEventsLength().call()
    
    def log_data_access(self, user, dataset):
        transaction_id = "x" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user,
            "dataset": dataset
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def log_query(self, user, dataset, query):
        transaction_id = "q" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user,
            "dataset": dataset,
            "query_hash": None #  TODO: put the hash and save query in DB
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)

    def log_change_pwd(self, user):
        transaction_id = "p" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def log_record_edit(self, record, dataset, user):
        transaction_id = "m" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user,
            "record": record,
            "dataset": dataset
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def log_record_add(self, record, dataset, user):
        transaction_id = "D" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user,
            "record": record,
            "dataset": dataset
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def log_record_delete(self, record, dataset, user):
        transaction_id = "t" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user,
            "record": record,
            "dataset": dataset
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def log_user_registration(self, admin, user):
        transaction_id = "r" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "user": user,
            "admin": admin
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def log_dataset_import(self, admin, dataset):
        transaction_id = "i" + str(uuid4())
        database.save_audit_transaction(transaction_id)
        tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
            "timestamp": int(time()),
            "dataset": dataset,
            "admin": admin
        })).transact()
        self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def get_audit_data(self):
        database.cursor.execute("SELECT * FROM Audit ORDER BY Timestamp DESC")
        return [Transaction(l, self) for l in database.cursor.fetchall()]
    
    def healthy_log(self):
        database.cursor.execute("SELECT * FROM Audit")
        return len(database.cursor.fetchall()) == self.get_audit_len()

    def healthcheck(self):
        if not self.healthy_log():
            transaction_id = "h" + str(uuid4())
            database.save_audit_transaction(transaction_id)
            tx_hash = self.logging.functions.addEvent(transaction_id, dumps({
                "timestamp": int(time())
            })).transact()
            self.w3.eth.waitForTransactionReceipt(tx_hash)
    
    def get_user_last_pwd_change(self, user_id):
        database.cursor.execute("SELECT * FROM Audit WHERE Transaction LIKE \"p%\" ORDER BY Timestamp DESC;")
        events = database.cursor.fetchall()
        for event in events:
            eth_data = self.get_event(event[0])
            if eth_data == '':
                continue
            event_data = loads(eth_data)
            if event_data["user"] == user_id:
                return event_data["timestamp"]
        return None
