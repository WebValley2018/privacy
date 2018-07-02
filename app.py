from flask import Flask, request, make_response, redirect
from db import DB
from ethereum import Ethereum
from auth_token import Token
from user import User
import utilities
app = Flask(__name__)


database = DB()
ethereum=Ethereum()

# Main page


@app.route("/")
def mainPage():
    if database.check_token(request.cookies.get("tovel_token")):
        # If the user is logged in, let's display his personal page
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False))
        replace_list = {
            "#Name" :  user.name + " " + user.surname
        }
        with open("static-assets/user.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
        return html
    else:
        with open("static-assets/login.html") as f:
            if "tovel_token" in request.cookies:
                resp = make_response(redirect("/?sessionexpired"))
                resp.set_cookie('tovel_token', '', expires=0)
                return resp
            elif "sessionexpired" in request.args:  # if redirected to "session expired" print Warning message
                return f.read().replace("{{loginmessage}}", '''<div class="alert alert-warning" 
                                            role="alert">Session expired or not valid</div>''')
            elif "loginfailed" in request.args:    # if redirected to "loginfailed" print Error message
                return f.read().replace("{{loginmessage}}", '''<div class="alert alert-danger"
                                            role="alert">Login failed. Please check your credentials</div>''')
            elif "logoutsuccess" in request.args:  # if redirected to "logoutsuccess" print Success message
                return f.read().replace("{{loginmessage}}", '''<div class="alert alert-success"
                                            role="alert">Logout succeded</div>''')
            else:
                return f.read().replace("{{loginmessage}}", '')

@app.route("/admin")
def adminPage():
    if database.check_admin_token(request.cookies.get("tovel_token_admin")):
        # If the user is logged in, let's display his personal page
        admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
        replace_list = {
            "#Name" :  admin.name + " " + admin.surname
        }
        with open("static-assets/admin.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
        return html
    else:
        with open("static-assets/login-admin.html") as f:
            if "tovel_token" in request.cookies:
                resp = make_response(redirect("/admin?sessionexpired"))
                resp.set_cookie('tovel_token_admin', '', expires=0)
                return resp
            elif "sessionexpired" in request.args:  # if redirected to "session expired" print Warning message
                return f.read().replace("{{loginmessage}}", '''<div class="alert alert-warning" 
                                            role="alert">Session expired or not valid</div>''')
            elif "loginfailed" in request.args:    # if redirected to "loginfailed" print Error message
                return f.read().replace("{{loginmessage}}", '''<div class="alert alert-danger"
                                            role="alert">Login failed. Please check your credentials</div>''')
            elif "logoutsuccess" in request.args:  # if redirected to "logoutsuccess" print Success message
                return f.read().replace("{{loginmessage}}", '''<div class="alert alert-success"
                                            role="alert">Logout succeded</div>''')
            else:
                return f.read().replace("{{loginmessage}}", '')

@app.route("/change-password")
def changePassword():
    user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False))
    replace_list = {
        "#Name": user.name + " " + user.surname
    }
    with open("static-assets/change_password.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
    return html

@app.route("/logout")
def logoutPage():
    database.set_token_ttl(request.cookies.get("tovel_token"))
    resp = make_response(redirect("/?logoutsuccess"))
    resp.set_cookie('tovel_token', '', expires=0)
    return resp  # Redirect to the /

@app.route("/admin/logout")
def adminLogoutPage():
    database.set_admin_token_ttl(request.cookies.get("tovel_token_admin"))
    resp = make_response(redirect("/admin?logoutsuccess"))
    resp.set_cookie('tovel_token_admin', '', expires=0)
    return resp  # Redirect to the /

@app.route("/admin/register-user", methods = ['POST', 'GET'])
def register_user():
    if not database.check_admin_token(request.cookies.get("tovel_token_admin")):
        resp = make_response(redirect("/admin?sessionexpired"))
        resp.set_cookie('tovel_token_admin', '', expires=0)
        return resp
    registration_outcome = ""
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        username = request.form["username"]
        organization = request.form["organization"]
        mail = request.form["mail"]
        trusted = True if "trusted" in request.form else False
        new_user_password = utilities.generate_password()
        new_user = User(username=username, name=name, surname=surname, organization=organization, mail=mail, trust=trusted, pw=new_user_password)
        if database.register_user(new_user):
            ethereum.set_user_hash(new_user.get_id(), new_user.h_pw)
            registration_outcome = '''<div class="alert alert-success"
                                    role="alert">User registration was successful. User's password is <b><pre>'''+ new_user_password + '''
                                    </pre></b></div>'''
            ethereum.log_user_registration(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True), new_user.get_id())
        else:
            registration_outcome = '''<div class="alert alert-danger"
                                    role="alert">User with same username already exists</div>'''

    admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    replace_list = {
        "#Name": admin.name + " " + admin.surname
    }
    with open("static-assets/user_registration.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
    return html.replace("{{outcome}}", registration_outcome)



@app.route("/login", methods=["POST"])
def loginPage():
    username = request.form["username"]
    password = request.form["password"]
    user_id = database.get_id_from_username(username)
    if user_id is None:
        ethereum.report_login_failure(request.remote_addr)  # Report false username
        resp = make_response(redirect("/?loginfailed"))  # Redirect to the homepage and display an error message
        return resp
    # The user ID is needed for the blockchain to get the password hash, so let's retrieve it from the DB
    # Store in the blockchain the authentication attempt and get the ID stored in the blockchain
    user = database.get_user_from_id(user_id)
    # Get the User object from the database
    user.set_pw_hash(ethereum.get_user(user_id).user_pwd_hash)
    # Update the user object with the hash from the blockchain
    if database.check_user(username) and user.verify_pw(password):  # If the authentication is successful
        ethereum.save_auth(user_id, True)  # Update the auth autcome in the blockchain
        token = Token(user = user_id, time_delta=60*5)  # Generate a new token
        database.register_token(token)  # Register it to the DB
        resp = make_response(redirect("/"))  # Redirect to the homepage
        resp.set_cookie("tovel_token", token.get_token_value())  # Set the cookie
        return resp
    else:
        ethereum.save_auth(user_id, False)  # Update the auth autcome in the blockchain
        resp = make_response(redirect("/?loginfailed"))  # Redirect to the homepage and display an error message
        return resp


@app.route("/admin/login", methods=["POST"])
def adminLoginPage():
    username = request.form["username"]
    password = request.form["password"]
    admin_id = database.get_admin_id_from_username(username)
    if admin_id is None:
        ethereum.report_login_failure(request.remote_address, True)  # Report false username
        resp = make_response(redirect("/admin?loginfailed"))  # Redirect to the homepage and display an error message
        return resp
    # The admin ID is needed for the blockchain to get the password hash, so let's retrieve it from the DB
    # Store in the blockchain the authentication attempt and get the ID stored in the blockchain
    admin = database.get_admin(admin_id)
    # Get the Admin object from the database

    if database.check_admin(username) and admin.verify_pw(password) and admin.verify_otp(request.form["totp"]):  # If the authentication is successful
        ethereum.save_auth(admin_id, True, True)  # Update the auth autcome in the blockchain
        token = Token(user=admin_id, time_delta=600)  # Generate a new token
        database.register_admin_token(token)  # Register it to the DB
        resp = make_response(redirect("/admin"))  # Redirect to the homepage
        resp.set_cookie("tovel_token_admin", token.get_token_value())  # Set the cookie
        return resp
    else:
        ethereum.save_auth(admin_id, False, True)  # Update the auth autcome in the blockchain
        resp = make_response(redirect("/admin?loginfailed"))  # Redirect to the homepage and display an error message
        return resp


app.run(host='0.0.0.0', debug=True)  # to do: remove the Bug True in production
