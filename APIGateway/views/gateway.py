from flakon import SwaggerBlueprint
from flask import render_template, request, redirect, url_for
import requests          # requirements

from monolith.forms import LoginForm, UserForm
from monolith.urls import HOME_URL

authapi= SwaggerBlueprint('gateway', spec='auth-api.yml')
usersapi = SwaggerBlueprint('users', spec='users-api.yml')
diceapi = SwaggerBlueprint('dice', spec='dice-api.yml')
storiesapi = SwaggerBlueprint('stories', spec='stories-api.yml')


AUTH_PORT = ':5000'
USER_PORT = ':5001'
DICE_PORT = ':5002'
STORY_PORT = ':5003'

#               Auth

@authapi.operation('home')
def _home():
    x = requests.get(HOME_URL + AUTH_PORT)  # not sure about stories=data
    data = x.json()
    return render_template("index.html", stories=data, home_url=HOME_URL)


@authapi.operation('getRegisterPage')
def _get_reg():
    form = UserForm()
    return render_template("create_user.html", form=form, home_url=HOME_URL)


@authapi.operation('register')
def _register():
    form = UserForm()
    x = requests.post(HOME_URL + AUTH_PORT + '/users/create')
    data = x.json()
    if x.status_code == QUALCOSA:
        flash('roba')
    return render_template("create_user.html", data=data, home_url=HOME_URL)


@authapi.operation('getLoginPage')
def _get_log():
    form = LoginForm()
    return render_template('login.html', form=form, home_url=HOME_URL)


@authapi.operation('login')
def _login():
    x = requests.post(HOME_URL + AUTH_PORT + '/users/login')
    if x.status_code == QUALCOSA:
        flash('roba') # e refresh stessa pagina
    return render_template('index.html', home_url=HOME_URL)


@authapi.operation('logout')
def _logout():
    x = requests.post(HOME_URL + AUTH_PORT + '/users/logout')
    redirect(url_for("_home"))


@authapi.operation('search')
def _search():
    x = requests.get(HOME_URL + AUTH_PORT + '/search')
    data = x.json()
    return render_template("search.html", data=data, home_url=HOME_URL)


#               Users

@usersapi.operation('getAll')
def _get_all():
    x = requests.get(HOME_URL + USER_PORT + '/users')
    data = x.json()
    return render_template("users.html", data=data, home_url=HOME_URL)


@usersapi.operation('getUser')
def _get_user(id_user):
    x = requests.get(HOME_URL + USER_PORT + '/users/' + id_user)
    data = x.json()
    return render_template("wall.html", data=data, home_url=HOME_URL)


@usersapi.operation('followUser')
def _follow_user(id_user):
    x = requests.post(HOME_URL + USER_PORT + '/users/' + id_user + '/follow')
    data = x.json()
    if x.status_code == QUALCOSA:
        flash('erur', 'error')

    return render_template("wall.html", data=data, home_url=HOME_URL)


@usersapi.operation('unfollowUser')
def _unfollow_user(id_user):
    x = requests.post(HOME_URL + USER_PORT + '/users/' + id_user + '/unfollow')
    data = x.json()
    if x.status_code == QUALCOSA:
        flash('erur', 'error')

    return render_template("wall.html", data=data, home_url=HOME_URL)


@usersapi.operation('getFollowers')
def _get_followers(id_user):
    x = requests.get(HOME_URL + USER_PORT + '/users/' + id_user + '/followers')
    data = x.json()

    return render_template("followers.html", data=data, home_url=HOME_URL)


@usersapi.operation('getStoriesOfUser')
def _get_stories_of_user(id_user):
    x = requests.get(HOME_URL + USER_PORT + '/users/' + id_user + '/stories')
    data = x.json()

    return render_template("user_stories.html", data=data, home_url=HOME_URL)


#                   Dice

@diceapi.operation('getSettingsPage')
def _get_settings_page():
    x = requests.get(HOME_URL + DICE_PORT + '/stories/new/settings')
    data = x.json()

    return render_template("settings.html", data=data, home_url=HOME_URL)


@diceapi.operation('getRollPage')
def _get_roll_page():
    x = requests.get(HOME_URL + DICE_PORT + '/stories/new/roll')
    data = x.json()

    return render_template("roll_dice.html", data=data, home_url=HOME_URL)


#                   Stories

@storiesapi.operation('getAll')
def _get_all():
    x = requests.get(HOME_URL + STORY_PORT + '/stories')
    data = x.json()

    return render_template("stories.html", data=data, home_url=HOME_URL)


@storiesapi.operation('getLatest')
def _get_latest():
    x = requests.get(HOME_URL + STORY_PORT + '/stories/latest')
    data = x.json()

    return render_template("stories.html", data=data, home_url=HOME_URL)


@storiesapi.operation('getRange')
def _get_range():
    begin = request.args.get('begin')
    end = request.args.get('end')
    x = requests.get(HOME_URL + STORY_PORT + '/stories/range?begin=' + begin + '&end=' + end)
    data = x.json()

    return render_template("stories.html", data=data, home_url=HOME_URL)


@storiesapi.operation('getDrafts')
def _get_drafts():
    x = requests.get(HOME_URL + STORY_PORT + '/stories/getDrafts')
    data = x.json()

    return render_template("drafts.html", data=data, home_url=HOME_URL)


@storiesapi.operation('getStory')
def _get_story(id_story):
    x = requests.get(HOME_URL + STORY_PORT + '/stories/' + id_story)
    data = x.json()

    return render_template("story.html", data=data, home_url=HOME_URL)


@storiesapi.operation('writeNew')
def _write_new():
    x = requests.get(HOME_URL + STORY_PORT + '/stories/new/write')
    data = x.json()

    return render_template("write_story.html", data=data, home_url=HOME_URL)


@storiesapi.operation('completeDraft')
def _complete_draft(id_story):
    x = requests.get(HOME_URL + STORY_PORT + '/stories/new/write/' + id_story)
    data = x.json()

    return render_template("write_story.html", data=data, home_url=HOME_URL)


@storiesapi.operation('getRandom')
def _get_random():
    x = requests.get(HOME_URL + STORY_PORT + '/stories/random')
    data = x.json()

    return render_template("story.html", data=data, home_url=HOME_URL)