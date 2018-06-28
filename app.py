from flask import Flask, request
from db import DB
app = Flask(__name__)


database = DB()

@app.route("/")
def mainPage():
    if database.check_token(request.cookies.get("tovel_token")):
        return "User page"
    else:
        return "Login page"

@app.route("/logout")
def logoutPage():
    return "Reditrect to the /"

@app.route("/login", methods=["POST"])
def loginPage():
    username = request.form["username"]
    password = request.form["password"]
    return "Check login and then redirect as needed"

app.run(host='0.0.0.0')