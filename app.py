from flask import Flask, request
from db import DB
from ethereum import Ethereum
from auth_token import Token
app = Flask(__name__)


database = DB()
ethereum=Ethereum()

@app.route("/")
def mainPage():
    if database.check_token(request.cookies.get("tovel_token")):
        return "User page"
    else:
        with open("static-assets/login.html") as f:
            if "loginfailed" in request.args:
                return f.read().replace("{{loginmessage}}",'<div class="alert alert-danger" role="alert">Login failed. Please check your credentials</div>')
            if "logoutsuccess" in request.args:
                return f.read().replace("{{loginmessage}}",'<div class="alert alert-success" role="alert">Logout succeded</div>')
            else:
                return f.read().replace("{{loginmessage}}",'')

@app.route("/logout")
def logoutPage():
    return "Redirect to the /"

@app.route("/login", methods=["POST"])
def loginPage():
    username = request.form["username"]
    password = request.form["password"]
    user_id=database.get_id_from_username(username)
    user=database.get_user_from_id(user_id)
    user.set_pw_hash(ethereum.get_user(user_id).user_pwd_hash)
    if user.verify_pw(password):
        token=Token(user=user_id)
        database.register_token(token)
        
    else:
        pass

app.run(host='0.0.0.0', debug=True)