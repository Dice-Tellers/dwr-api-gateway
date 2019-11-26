import json

import requests
from flakon import SwaggerBlueprint
from flask import render_template, redirect, url_for, request
from flask_login import current_user, logout_user, login_required, login_user

from APIGateway.classes.User import User
from APIGateway.forms import UserForm, LoginForm
from APIGateway.urls import *

authapi = SwaggerBlueprint('gateway', '__name__', swagger_spec=os.path.join(YML_PATH, 'auth-api.yaml'))


# Renders the Home page (index.html).
# It renders different data, depending whether an user is logged or not.
@authapi.operation('home')
def _home():
    # Stories is an empty list, so it can be iterated in the HTML
    stories = []

    # If there's a logged user, we get his stories
    if current_user is not None and hasattr(current_user, 'id'):
        s = requests.get(STORY_URL + '/stories/users/{}'.format(current_user.id))

        if check_service_up(s):
            if s.status_code < 300:
                stories = s.json()

    return render_template("index.html", stories=stories, home_url=GATEWAY_URL)


# Renders the Register page (create_user.html)
@authapi.operation('getRegisterPage')
def _get_reg():
    form = UserForm()
    return render_template("create_user.html", form=form, home_url=GATEWAY_URL)


# The operation to register a new user into the service.
@authapi.operation('register')
def _register():
    form = UserForm()

    # Simple checks on the input datas
    if form.validate_on_submit():
        data = ({"firstname": form.data['firstname'],
                 "lastname": form.data['lastname'],
                 "password": form.data['password'],
                 "email": form.data['email'],
                 "dateofbirth": str(form.data['dateofbirth'])})
        x = requests.post(USER_URL + '/users/create', data=json.dumps(data))

        if check_service_up(x):
            body = x.json()

            # If everything's fine, redirect to a list of all the registered users
            if x.status_code < 300:
                return redirect(url_for("users._get_all_users"))
            # Else we flash the message the microservice returned
            else:
                flash(body['description'], 'error')

    # If we get here, the form wasn't valid so just update the page
    return render_template("create_user.html", form=form, home_url=GATEWAY_URL)


# Renders the Login page (login.html)
@authapi.operation('getLoginPage')
def _get_log():
    form = LoginForm()
    return render_template('login.html', form=form, home_url=GATEWAY_URL)


# The operation to login an already registered user into the service.
@authapi.operation('login')
def _login():
    form = request.form

    # Get input data, then send it to the Users microservice
    data = ({"email": form['email'],
             "password": form['password']})
    x = requests.post(USER_URL + '/users/login', data=json.dumps(data))

    if check_service_up(x):
        body = x.json()

        # If the email and password were correct
        if x.status_code < 300:

            # flask_login requires an instance of a class User, then redirect to the Home
            user = User(body['id'], body['firstname'], body['lastname'], body['email'])
            login_user(user)
            return redirect(url_for('gateway._home'))

        # Else flash the returned error and refresh the login page to retry the login
        else:
            flash(body['description'], 'error')
            return redirect(url_for('gateway._get_log'))
    else:
        return redirect(url_for('gateway._get_log'))


# The operation to log out of the service a logged user
@authapi.operation('logout')
@login_required
def _logout():
    logout_user()
    return redirect(url_for("gateway._home"))


# TODO Search
@authapi.operation('search')
def _search():
    x = requests.get(USER_URL + '/search')
    data = x.json()
    return render_template("search.html", data=data, home_url=GATEWAY_URL)
