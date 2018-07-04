from uuid import uuid4
import hashlib
import os
from json import dumps

from flask import Flask, request, make_response, redirect
from middleware import healthCheckMW
from werkzeug.utils import secure_filename
from db import DB
from ethereum import Ethereum
from auth_token import Token
from user import User
import utilities
from time import strftime, gmtime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"


database = DB()
ethereum=Ethereum()

app.wsgi_app = healthCheckMW(app.wsgi_app)
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

@app.route("/change-password", methods=["GET", "POST"])
def changePassword():
    #  Check that the user has the authorizations needed
    if not "tovel_token" in request.cookies and "tovel_token_admin" not in request.cookies:
        resp = make_response(redirect("/"))
        return resp
    elif "tovel_token" in request.cookies and not database.check_token(request.cookies.get("tovel_token")):
        resp = make_response(redirect("/?sessionexpired"))
        resp.set_cookie('tovel_token', '', expires=0)
        return resp
    elif "tovel_token_admin" in request.cookies and not database.check_admin_token(request.cookies.get("tovel_token_admin")):
        resp = make_response(redirect("/admin?sessionexpired"))
        resp.set_cookie('tovel_token_admin', '', expires=0)
        return resp
    
    #  Get user data
    user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False)) if "tovel_token" in request.cookies else database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    replace_list = {
        "#Name": user.name + " " + user.surname,
        "{{outcome}}": '',
        "{{security}}": "3" if "tovel_token" in request.cookies else "4"
    }

    if request.method == "POST":
        #  If the form has been submitted
        if "tovel_token" in request.cookies:
            user_id = user.id
            #  Procedure for the regular user
            user.set_pw_hash(ethereum.get_user(database.get_userid_from_token(request.cookies.get("tovel_token"), False)).user_pwd_hash)
            if user.verify_pw(request.form["old_password"]): #  If the saved password matches with the one provided by the user
                salt = str(uuid4().hex)
                database.change_user_salt(user_id, salt)
                #  Update the salt in DB
                hash_pw = hashlib.sha512((request.form["password"] + salt).encode("utf-8")).hexdigest()
                ethereum.set_user_hash(user_id, hash_pw)
                replace_list["{{outcome}}"] = '''<div class="alert alert-success"
                                    role="alert">Password has been changed successfully</div>'''
                ethereum.log_change_pwd(user_id)
            else:
                replace_list["{{outcome}}"] = '''<div class="alert alert-danger"
                                    role="alert">Please check your old password</div>'''

        elif "tovel_token_admin" in request.cookies:
            #  Procedure for the admins
            if database.change_admin_pwd(user, request.form["old_password"], request.form["password"]):
                replace_list["{{outcome}}"] = '''<div class="alert alert-success"
                            role="alert">Password has been changed successfully</div>'''
            else:
                replace_list["{{outcome}}"] = '''<div class="alert alert-danger"
                            role="alert">Please check your old password</div>'''
    
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

@app.route("/login", methods=["POST"])
def loginPage():
    username = request.form["username"]
    password = request.form["password"]
    user_id = database.get_id_from_username(username)
    if user_id is None:
        ethereum.report_login_failure(request.remote_address)  # Report false username
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

@app.route("/get-dataset/<format>/<dataset_id>")
def get_dataset(format, dataset_id):
    if database.check_token(request.cookies.get("tovel_token")):
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
        if format == 'json':
            ethereum.log_data_access(database.get_userid_from_token(request.cookies.get("tovel_token"), False), dataset_id)
            return dumps(database.get_dataset(dataset_id, user.get_trust_level()))
    else:
        return "{\"error\": \"Session expired\"}"

@app.route("/query")
def query():
    if database.check_token(request.cookies.get("tovel_token")):
        # If the user is logged in, let's display his personal page
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False))
        buttons = ""
        for dataset in database.get_datasets(user.get_trust_level()):
            buttons = buttons + f"<button type=\"button\" class=\"btn btn-primary btn-lg btn-block\" onclick=\"loadDS('{dataset['id']}');\">{dataset['name']}</button>\n"
        replace_list = {
            "#Name" :  user.name + " " + user.surname,
            "#btns": buttons
        }
        with open("static-assets/query.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
        return html
    else:
        resp = make_response(redirect("/"))
        return resp  # Redirect to the /

@app.route("/admin")
def adminPage():
    print(database.check_admin_token(request.cookies.get("tovel_token_admin")))
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
        trustlevel = int(request.form["trustlevel"])
        new_user_password = utilities.generate_password()
        new_user = User(username=username, name=name, surname=surname, organization=organization, mail=mail, trust=trustlevel if trustlevel < 2 else 0, doctor=True if trustlevel == 2 else False, pw=new_user_password)
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

@app.route("/admin/log")
def adminLog():
    if not database.check_admin_token(request.cookies.get("tovel_token_admin")):
        resp = make_response(redirect("/admin?sessionexpired"))
        resp.set_cookie('tovel_token_admin', '', expires=0)
        return resp
    admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    trs = ethereum.get_audit_data()
    data = ""
    for t in trs:
        data += '''<div class="alert alert-''' + t.security_score() + '''"
                                        role="alert">''' + t.event_description() + '<br>' + strftime("%a, %d %b %Y %H:%M:%S", gmtime(t.timestamp)) + '</div>'

    replace_list = {
        "#Name": admin.name + " " + admin.surname,
        "{{transactions}}": data,
        "{{warning}}": '''<div class="alert alert-danger mb-5"
                                    role="alert">Warning: the log on the blockchain doesn't match 
                                    with the log on the database</div>''' if not ethereum.healthy_log() else ''
    }
    with open("static-assets/log.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
    return html

@app.route("/admin/import-xls", methods = ['POST', 'GET'])
def import_excel():
    if not database.check_admin_token(request.cookies.get("tovel_token_admin")):
        resp = make_response(redirect("/admin?sessionexpired"))
        resp.set_cookie('tovel_token_admin', '', expires=0)
        return resp
    upload_outcome = ""
    if request.method == "POST":
        if database.check_dataset_exsistence(request.form["dataset_name"]):
            upload_outcome = '''<div class="alert alert-danger"
                                    role="alert">A dataset with this name already exists on the system</div>'''
        elif 'xls' not in request.files:
            upload_outcome = '''<div class="alert alert-danger"
                                    role="alert">The system was unable to import your data</div>'''
        else:
            file = request.files['xls']
            if file.filename == '':
                upload_outcome = '''<div class="alert alert-danger"
                                    role="alert">The system was unable to import your data -1ßß</div>'''
            else:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                upload_outcome = '''<div class="alert alert-success"
                                        role="alert">Data import was successful</div>'''
                dataset_id = database.import_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename), request.form["dataset_name"], int(request.form["trustlevel"]))
                ethereum.log_dataset_import(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True), dataset_id)
                os.unlink(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        

    admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    replace_list = {
        "#Name": admin.name + " " + admin.surname
    }
    with open("static-assets/import-xls.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
    return html.replace("{{outcome}}", upload_outcome)

@app.route("/admin/login", methods=["POST"])
def adminLoginPage():
    username = request.form["username"]
    password = request.form["password"]
    admin_id = database.get_admin_id_from_username(username)
    if admin_id is None:
        ethereum.report_login_failure(request.remote_addr, True)  # Report false username
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

@app.route("/admin/edit-table/<dataset>")
def editableTable(dataset):
    # admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
    ds = database.get_dataset(dataset, user.get_trust_level())
    columns = '<th scope="col"></th>'
    for c in ds["columns"]:
        columns += '''<th scope="col">''' + c["title"] + '''</th>'''
    data = ''
    for idx, r in enumerate(ds["data"]):
        data += f'<tr><td class="filterable-cell"><a href="/admin/edit-table/edit-row/{dataset}/{idx}"><i class="far fa-edit"></i></a></td>'
        for c in r:
            data += '''<td class="filterable-cell">''' + str(c) + "</td>"
        data += '</tr>'
    replace_list = {
        # "#Name": admin.name + " " + admin.surname
        "#TableName": database.get_dataset_name(dataset, user.get_trust_level()).decode('utf-8'),
        "{{columns}}": columns,
        "{{content}}": data

    }
    with open("static-assets/edit_table.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
        return html

@app.route("/admin/edit-table/edit-row/<dataset>/<row>", methods=["GET", "POST"])
def editRow(dataset, row):
    # admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
    ds = database.get_dataset_row(dataset, int(row), user.get_trust_level())
    l = ds["columns"]
    r = ds["data"]
    data = ''
    for c, lb in zip(r, l):
        data += '<div class="form-group">'
        data += '''<label for="exampleFormControlInput1">''' + str(lb) + '''</label>'''
        data += f'''<input type="string" class="form-control" name="{str(lb)}" value="{str(c)}"">'''
        data += '</div>'

    if request.method == "POST":
        new_values = []
        [new_values.append(request.form[str(c)]) for c in l]
        # print(new_values)
        database.modify_row(dataset, new_values, row, user.get_trust_level())
        return redirect(f"/admin/edit-table/edit-row/{dataset}/{row}")

    replace_list = {
        # "#Name": admin.name + " " + admin.surname
        "#TableName": database.get_dataset_name(dataset, user.get_trust_level()).decode('utf-8'),
        "#RowNumber": str(int(row) + 1),
        "#datasetid": dataset,
        "{{content}}": data
    }
    with open("static-assets/edit_row.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
        return html

app.run(host='0.0.0.0', debug=True)  # to do: remove debug True in production


