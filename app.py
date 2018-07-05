from uuid import uuid4
import hashlib
import os
from json import dumps, loads

from flask import Flask, request, make_response, redirect, abort
from middleware import healthCheckMW
from werkzeug.utils import secure_filename
from db import DB
from ethereum import Ethereum
from auth_token import Token
from user import User
import utilities
from time import strftime, gmtime, time
from qr import QR
import pyotp
from admin import Admin

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"


if not os.path.isfile("config.json"):
    database = None
    ethereum = None
else:
    with open("config.json") as f:
        dati = loads(f.read())
    database = DB(user=dati["user"], password=dati["password"], database=dati["database"], host=dati["host"])
    ethereum=Ethereum(providerAddress=dati["provider"])

app.wsgi_app = healthCheckMW(app.wsgi_app)
# Main page


@app.route("/")
def mainPage():
    if database is None:
        return make_response(redirect("/set-up"))
    elif database.check_token(request.cookies.get("tovel_token")):
        # If the user is logged in, let's display his personal page
        last_pwd_change = ethereum.get_user_last_pwd_change(database.get_userid_from_token(request.cookies.get("tovel_token")))
        if time() - (0 if last_pwd_change is None else last_pwd_change) > 30*24*60*60:
            resp = make_response(redirect("/change-password?mustchange"))
            return resp
        
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False))
        edit_table = '''<div class="card d-inline-block" style="width: 18rem; min-height: 10rem; margin: 1em;" >
                            <div class="card-body">
                              <h5 class="card-title">Edit Table</h5>
                              <p class="card-text">Edit a Dataset</p>
                              <a href="/choose-table" class="btn btn-primary">Edit</a>
                            </div>
                        </div>'''
        replace_list = {
            "#Name":  user.name + " " + user.surname,
            "{{actions}}": edit_table if user.trust_level == 2 else ""
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
    
    must_change_banner = '<div class="alert alert-info" role="alert">In order to access your account you must change your password</div>'

    #  Get user data
    user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False)) if "tovel_token" in request.cookies else database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))
    replace_list = {
        "#Name": user.name + " " + user.surname,
        "{{outcome}}": '',
        "{{security}}": "3" if "tovel_token" in request.cookies else "4",
        "{{admin}}": '' if not "tovel_token_admin" in request.cookies else "admin",
        "{{pwdchange}}": must_change_banner if "mustchange" in request.args else ''
    }

    if request.method == "POST":
        #  If the form has been submitted
        if "tovel_token" in request.cookies:
            user_id = user.id
            #  Procedure for the regular user
            user.set_pw_hash(ethereum.get_user(database.get_userid_from_token(request.cookies.get("tovel_token"), False)).user_pwd_hash)
            if user.verify_pw(request.form["old_password"]) and user.verify_pw(request.form["password"]):
                replace_list["{{outcome}}"] = '''<div class="alert alert-danger"
                                                    role="alert">Please enter a new password and not the old one</div>'''
            elif user.verify_pw(request.form["old_password"]): #  If the saved password matches with the one provided by the user
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
            replace_list["{{admin}}"] = "/admin"
            #  Procedure for the admins
            if database.change_admin_pwd(user, request.form["old_password"], request.form["password"]) == 0:
                replace_list["{{outcome}}"] = '''<div class="alert alert-danger"
                                            role="alert">Please enter a new password and not the old one</div>'''
            elif database.change_admin_pwd(user, request.form["old_password"], request.form["password"]) == 2:
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
            "#btns": buttons,
            "#trusted": "dati['dom']='Bfrtip';dati['buttons']= ['excel'];" if user.trust_level>0 else ''
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
    if database.check_admin_token(request.cookies.get("tovel_token_admin")):

        # last_pwd_change = ethereum.get_user_last_pwd_change(database.get_admin_id_from_username(request.cookies.get("tovel_token")))
        # if time() - (0 if last_pwd_change is None else last_pwd_change) > 30*24*60*60:
        #     resp = make_response(redirect("/change-password?mustchange"))
        #     return resp
        
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

@app.route("/edit-table/<dataset>")
def editTable(dataset):
    if database.check_token(request.cookies.get("tovel_token")):
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
        ds = database.get_dataset(dataset, user.get_trust_level(), True)
        columns = '<th scope="col"></th><th scope="col"></th>'
        for c in ds["columns"][1:]:
            columns += '''<th scope="col">''' + c["title"] + '''</th>'''
        data = ''
        for idx, r in enumerate(ds["data"]):
            data += f'<tr><td class="filterable-cell"><a href="/edit-table/edit-row/{dataset}/{str(r[0])}/{idx}"><i class="far fa-edit"></i></a></td>'
            data += f'<td class="filterable-cell"><a href="/edit-table/delete-row/{dataset}/{str(r[0])}"><i class="far fa-trash-alt"></i></a></td>'
            for c in r[1:]:
                data += '''<td class="filterable-cell">''' + str(c) + "</td>"
            data += '</tr>'
        changebutton = f'<a href="/edit-table/new-row/{dataset}" class="m-3 btn btn-primary">New Record</a>'
        replace_list = {
            "#Name": user.name + " " + user.surname,
            "#TableName": database.get_dataset_name(dataset, user.get_trust_level()).decode('utf-8'),
            "{{columns}}": columns,
            "{{content}}": data,
            "{{changebutton}}": changebutton

        }
        with open("static-assets/edit_table.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
            return html
    else:
        resp = make_response(redirect("/"))
        return resp  # Redirect to the /

@app.route("/edit-table/edit-row/<dataset>/<row_id>/<row>", methods=["GET", "POST"])
def editRow(dataset, row_id, row):
    if database.check_token(request.cookies.get("tovel_token")):
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
        ds = database.get_dataset_row(dataset, row_id, user.get_trust_level())
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
            database.modify_row(dataset, new_values, row_id, user.get_trust_level())
            ethereum.log_record_edit(user=user.id, dataset=dataset, record=row_id)
            return redirect(f"/edit-table/edit-row/{dataset}/{row_id}/{row}")

        replace_list = {
            "#Name": user.name + " " + user.surname,
            "#TableName": database.get_dataset_name(dataset, user.get_trust_level()).decode('utf-8'),
            "#RowNumber": row,
            "#datasetid": dataset,
            "{{content}}": data
        }
        with open("static-assets/edit_row.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
            return html
    else:
        resp = make_response(redirect("/"))
        return resp  # Redirect to the /

@app.route("/edit-table/delete-row/<dataset>/<row_id>")
def deleteRow(dataset, row_id):
    if database.check_token(request.cookies.get("tovel_token")):
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
        database.delete_row(dataset, row_id, user.get_trust_level())
        resp = make_response(redirect(f"/edit-table/{dataset}"))
        ethereum.log_record_delete(user=user.id, dataset=dataset, record=row_id)
        return resp  # Redirect to the /
    else:
        resp = make_response(redirect("/"))
        return resp  # Redirect to the /

@app.route("/edit-table/new-row/<dataset>", methods=["GET", "POST"])
def newRow(dataset):
    if database.check_token(request.cookies.get("tovel_token")):
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token")))
        ds = database.get_dataset_columns(dataset, user.get_trust_level())
        l = ds["columns"]
        data = ''
        for lb in l:
            data += '<div class="form-group">'
            data += '''<label for="exampleFormControlInput1">''' + str(lb) + '''</label>'''
            data += f'''<input type="string" class="form-control" name="{str(lb)}"">'''
            data += '</div>'

        if request.method == "POST":
            new_values = []
            [new_values.append(request.form[str(c)]) for c in l]

            #database.delete_row()
            database.new_row(dataset, tuple(new_values), user.get_trust_level())
            #ethereum.log_record_add(user=user.id, dataset=dataset, record=row_id)
            return redirect(f"/edit-table/{dataset}")

        replace_list = {
            "#Name": user.name + " " + user.surname,
            "#TableName": database.get_dataset_name(dataset, user.get_trust_level()).decode('utf-8'),
            "#datasetid": dataset,
            "{{content}}": data
        }
        with open("static-assets/new_row.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
            return html
    else:
        resp = make_response(redirect("/"))
        return resp  # Redirect to the /



@app.route("/choose-table")
def chooseTable():
    if database.check_token(request.cookies.get("tovel_token")):
        # If the user is logged in, let's display his personal page
        user = database.get_user_from_id(database.get_userid_from_token(request.cookies.get("tovel_token"), False))
        datasets = database.get_datasets(user.trust_level)
        buttons = ''
        for d in datasets:
            buttons += f'''<a class="btn btn-primary btn-lg btn-block" href="/edit-table/{d["id"]}" role="button">{d['name']}</a>'''
        replace_list = {
            "#Name":  user.name + " " + user.surname,
            "{{datasets}}": buttons
        }
        with open("static-assets/choose_table.html") as f:
            html = f.read()
            for search, replace in replace_list.items():
                html = html.replace(search, replace)
        return html
    else:
        resp = make_response(redirect("/"))
        return resp  # Redirect to the /

@app.route("/set-up", methods=["POST", "GET"])
def setUp():
    global database
    global ethereum
    if database is not None:
        abort(403)
    replace_list={
        "{{outcome}}": ''
    }
    if request.method == "POST":
        #  Setting up
        config_data = {
            "user": request.form["dbusername"],
            "password": request.form["dbpassword"],
            "host": request.form["dbserver"],
            "database": request.form["dbname"],
            "provider": request.form["ethprovider"]
        }
        config_file = open("config.json", 'w')
        config_file.write(dumps(config_data))
        config_file.close()
        import mysql.connector as mariadb
        db = mariadb.connect(user=config_data["user"], password=config_data["password"], host=config_data["host"])
        cursor = db.cursor()
        # Create DB
        cursor.execute(f"CREATE DATABASE {config_data['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE {config_data['database']};")
        db.commit()
        # Create tables
        queries="""CREATE TABLE `Administrators` (`ID` text COLLATE utf8_bin NOT NULL,`Username` text COLLATE utf8_bin NOT NULL,`Name` text COLLATE utf8_bin NOT NULL,`Surname` text COLLATE utf8_bin NOT NULL,`Password` text COLLATE utf8_bin NOT NULL,`Salt` text COLLATE utf8_bin NOT NULL,`OTPKey` text COLLATE utf8_bin NOT NULL);
CREATE TABLE `AdminToken` (`TokenValue` text COLLATE utf8_bin NOT NULL,`TTL` int(11) NOT NULL,`CreationDate` bigint(20) NOT NULL,`User` text COLLATE utf8_bin NOT NULL);
CREATE TABLE `Audit` (`Transaction` text COLLATE utf8_bin NOT NULL,`Timestamp` int(11) NOT NULL);
CREATE TABLE `Datasets` (`Name` text COLLATE utf8_bin NOT NULL,`ID` text COLLATE utf8_bin NOT NULL,`RequiredTrust` int(11) DEFAULT NULL);
CREATE TABLE `Token` (`TokenValue` text COLLATE utf8_bin NOT NULL,`TTL` int(11) NOT NULL,`CreationDate` bigint(20) NOT NULL,`User` text COLLATE utf8_bin NOT NULL);
CREATE TABLE `Users` (`Username` text COLLATE utf8_bin NOT NULL,`Name` text COLLATE utf8_bin NOT NULL,`Surname` text COLLATE utf8_bin NOT NULL,`Mail` text COLLATE utf8_bin NOT NULL,`ID` text COLLATE utf8_bin NOT NULL,`Salt` text COLLATE utf8_bin NOT NULL,`Organization` text COLLATE utf8_bin NOT NULL,`TrustLevel` smallint(6) NOT NULL);""".split(";\n")
        for query in queries:
            cursor.execute(query)
        db.commit()
        # Create admin
        name = request.form["name"]
        surname = request.form["surname"]
        password = request.form["password"]
        username = request.form["username"]
        admin = Admin(username=username, name=name, surname=surname, pw=password)
        cursor.execute("INSERT INTO Administrators VALUES (%s, %s, %s, %s, %s, %s, %s);", (
            admin.id, admin.username, admin.name, admin.surname, admin.h_pw, admin.salt, admin.otp_key,))
        resp = make_response(redirect("/get-totp-key"))  # Redirect to the homepage
        resp.set_cookie("admin_id", admin.id)  # Set the cookie
        db.commit()
        with open("config.json") as f:
            dati = loads(f.read())
        database = DB(user=dati["user"], password=dati["password"], database=dati["database"], host=dati["host"])
        ethereum = Ethereum(providerAddress=dati["provider"])
        return resp

    with open("static-assets/set_up.html") as page:
        html = page.read()
    for search, replace in replace_list.items():
        html = html.replace(search, replace)
    return html

@app.route("/admin/new-admin", methods=['POST', 'GET'])
def newAdmin():
    if not database.check_admin_token(request.cookies.get("tovel_token_admin")):
        resp = make_response(redirect("/admin?sessionexpired"))
        resp.set_cookie('tovel_token_admin', '', expires=0)
        return resp
    admin = database.get_admin(database.get_userid_from_token(request.cookies.get("tovel_token_admin"), True))

    response = ''
    if request.method == "POST":
        print(dumps(request.form))
        name = request.form["name"]
        surname = request.form["surname"]
        password = request.form["password"]
        username = request.form["username"]
        if not database.check_admin(username):
            admin = Admin(username=username, name=name, surname=surname, pw=password)
            database.register_admin(admin)
            resp = make_response(redirect("/get-totp-key"))  # Redirect to the homepage
            resp.set_cookie("admin_id", admin.id)  # Set the cookie
            return resp
        else:
            response = '''<div class="alert alert-danger"
                                    role="alert">Admin with the same username already exists</div>'''
            pass

    replace_list = {
        "#Name": admin.name + " " + admin.surname,
        "{{outcome}}": response
    }

    with open("static-assets/new_admin.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
    return html

@app.route("/get-totp-key")
def getQrCode():
    admin_id = request.cookies.get("admin_id")
    admin = database.get_admin(admin_id)
    url = pyotp.totp.TOTP(admin.otp_key).provisioning_uri(admin.username, issuer_name="Tovel")
    qr = QR(url).get_svg()
    replace_list = {
        "{{qrcode}}": qr
    }

    with open("static-assets/get_qrcode.html") as f:
        html = f.read()
        for search, replace in replace_list.items():
            html = html.replace(search, replace)
    return html

@app.route("/delete-cookie")
def deleteCookie():
    resp = make_response(redirect("/admin"))
    resp.set_cookie('admin_id', expires=0)
    return resp


app.run(host='0.0.0.0')  # to do: remove debug True in production


