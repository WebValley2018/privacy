from flask import Flask, request
from db import DB
from ethereum import Ethereum
app = Flask(__name__)


database = DB()
ethereum=Ethereum()

@app.route("/")
def mainPage():
    if database.check_token(request.cookies.get("tovel_token")):
        return "User page"
    else:
        return """<form action="login" method="POST">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit">
        </form>
        """

@app.route("/logout")
def logoutPage():
    return "Reditrect to the /"

@app.route("/login", methods=["POST"])
def loginPage():
    username = request.form["username"]
    password = request.form["password"]
    user_id=database.get_id_from_username(username)
    user=database.get_user_from_id(user_id)
    user.set_pw_hash(ethereum.get_user(user_id).user_pwd_hash)
    print(user.verify_pw(password))
    return "Check login and then redirect as needed"

app.run(host='0.0.0.0', debug=True)