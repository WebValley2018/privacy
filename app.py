from flask import Flask, request
app = Flask(__name__)

class DB:
    """Dummy DB class"""
    def init(self):
        pass
    
    def check_token(self, session_id):
        return True
    
    def get_user_from_token(self, token_id):
        user_id="qwertuiop"
        return user_id


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

@app.route("/login")
def loginPage():
    return "Check login and then redirect as needed"

app.run(host='0.0.0.0')