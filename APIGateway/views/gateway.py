import json
import os

import requests
from flakon import SwaggerBlueprint
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import (login_user, logout_user, login_required, current_user)
from werkzeug.exceptions import BadRequestKeyError

from APIGateway.classes.User import User
from APIGateway.forms import LoginForm, UserForm, StoryForm

yml_path = os.path.join(os.path.dirname(__file__), '..', 'yamls')

authapi = SwaggerBlueprint('gateway', '__name__', swagger_spec=os.path.join(yml_path, 'auth-api.yaml'))
usersapi = SwaggerBlueprint('users', '__name__', swagger_spec=os.path.join(yml_path, 'users-api.yaml'))
diceapi = SwaggerBlueprint('dice', '__name__', swagger_spec=os.path.join(yml_path, 'dice-api.yaml'))
storiesapi = SwaggerBlueprint('stories', '__name__', swagger_spec=os.path.join(yml_path, 'stories-api.yaml'))

HOME_URL = 'http://127.0.0.1'
GATEWAY_URL = HOME_URL + ':5000/'

USER_PORT = ':5001'
DICE_PORT = ':5002'
STORY_PORT = ':5003'
REACTION_PORT = ':5004'


#               Auth


@authapi.operation('home')
def _home():
    stories = []
    if current_user is not None and hasattr(current_user, 'id'):
        s = requests.get(HOME_URL + STORY_PORT + '/stories/users/{}'.format(current_user.id))
        if s.status_code < 300:
            stories = s.json()

    return render_template("index.html", stories=stories, home_url=GATEWAY_URL)


@authapi.operation('getRegisterPage')
def _get_reg():
    form = UserForm()
    return render_template("create_user.html", form=form, home_url=GATEWAY_URL)


@authapi.operation('register')
def _register():
    form = UserForm()
    if form.validate_on_submit():
        data = ({"firstname": form.data['firstname'],
                 "lastname": form.data['lastname'],
                 "password": form.data['password'],
                 "email": form.data['email'],
                 "dateofbirth": str(form.data['dateofbirth'])})
        x = requests.post(HOME_URL + USER_PORT + '/users/create', data=json.dumps(data))
        body = x.json()
        if x.status_code < 300:
            return redirect(url_for("users._get_all_users"))
        else:
            flash(body['description'], 'error')

    return render_template("create_user.html", form=form, home_url=GATEWAY_URL)


@authapi.operation('getLoginPage')
def _get_log():
    form = LoginForm()
    return render_template('login.html', form=form, home_url=GATEWAY_URL)


@authapi.operation('login')
def _login():
    form = request.form
    data = ({"email": form['email'],
             "password": form['password']})
    x = requests.post(HOME_URL + USER_PORT + '/users/login', data=json.dumps(data))
    body = x.json()
    if x.status_code < 300:
        user = User(body['id'], body['firstname'], body['lastname'], body['email'])
        login_user(user)
        return redirect(url_for('gateway._home'))

    else:
        flash(body['description'], 'error')  # e refresh stessa pagina
        return redirect(url_for('gateway._get_log'))


@authapi.operation('logout')
@login_required
def _logout():
    logout_user()
    return redirect(url_for("gateway._home"))


@authapi.operation('search')
def _search():
    x = requests.get(HOME_URL + USER_PORT + '/search')
    data = x.json()
    # to be done
    return render_template("search.html", data=data, home_url=GATEWAY_URL)


#               Users

@usersapi.operation('getAll')
def _get_all_users():
    x = requests.get(HOME_URL + USER_PORT + '/users')
    users = x.json()
    return render_template("users.html", users=users, home_url=GATEWAY_URL)


@usersapi.operation('getUser')
def _get_user(id_user):
    s = requests.get(HOME_URL + STORY_PORT + '/users/' + id_user + '/stories')
    x = requests.get(HOME_URL + USER_PORT + '/users/' + id_user)
    data = x.json()
    stories = s.json()

    return render_template("wall.html", data=data, stories=stories, home_url=GATEWAY_URL)


@usersapi.operation('followUser')
@login_required
def _follow_user(id_user):
    x = requests.post(HOME_URL + USER_PORT + '/users/' + id_user + '/follow')
    data = x.json()
    if x.status_code != 200:
        flash('erur', 'error')

    return render_template("wall.html", data=data, home_url=GATEWAY_URL)


@usersapi.operation('unfollowUser')
@login_required
def _unfollow_user(id_user):
    x = requests.post(HOME_URL + USER_PORT + '/users/' + id_user + '/unfollow')
    data = x.json()
    if x.status_code != 200:
        flash('erur', 'error')

    return render_template("wall.html", data=data, home_url=GATEWAY_URL)


@usersapi.operation('getFollowers')
def _get_followers(id_user):
    x = requests.get(HOME_URL + USER_PORT + '/users/' + id_user + '/followers')
    data = x.json()

    return render_template("followers.html", data=data, home_url=GATEWAY_URL)


@usersapi.operation('getStoriesOfUser')
def _get_stories_of_user(id_user):
    x = requests.get(HOME_URL + USER_PORT + '/users/' + id_user + '/stories')
    data = x.json()

    return render_template("user_stories.html", data=data, home_url=GATEWAY_URL)


#                   Dice

@diceapi.operation('getSettingsPage')
@login_required
def _get_settings_page():
    x = requests.get(HOME_URL + DICE_PORT + '/sets')
    if x.status_code == 204:
        flash("No dice set found. Please contact Jacopo Massa")
        redirect(url_for('gateway._home'))
    else:
        sets = x.json()
        return render_template("settings.html", sets=sets, home_url=GATEWAY_URL)


@diceapi.operation('getRollPage')
@login_required
def _get_roll_page():
    try:
        dice_number = int(request.form['dice_number'])
        session['dice_number'] = dice_number
    except BadRequestKeyError:
        dice_number = session['dice_number']

    try:
        s = request.form['dice_img_set'].split('_', 1)
        id_set = s[0]
        name_set = s[1]
        session['id_set'] = id_set
        session['name_set'] = name_set
    except BadRequestKeyError:
        id_set = session['id_set']
        name_set = session['name_set']

    data = {'dice_number': dice_number}
    x = requests.post(HOME_URL + DICE_PORT + '/sets/{}/roll'.format(id_set), json=data)
    body = x.json()
    if x.status_code < 300:
        words = []
        dice_indexes = []
        for n, fig in body.items():
            dice_indexes.append(int(n) - 1)
            words.append(fig)
        session['figures'] = words

        context_vars = {"dice_number": dice_number, "dice_img_set": name_set,
                        "words": words, "dice_indexes": dice_indexes, "home_url": GATEWAY_URL}
        return render_template("roll_dice.html", **context_vars)
    else:
        flash(body['description'], 'error')
        return redirect(url_for('dice._get_settings_page'))


#                   Stories

@storiesapi.operation('getAll')
def _get_all_stories():
    x = requests.get(HOME_URL + STORY_PORT + '/stories')
    stories = x.json()

    return render_template("stories.html", stories=stories, home_url=GATEWAY_URL)


@storiesapi.operation('getLatest')
def _get_latest():
    x = requests.get(HOME_URL + STORY_PORT + '/stories/latest')
    stories = x.json()

    return render_template("stories.html", stories=stories, home_url=GATEWAY_URL)


@storiesapi.operation('getRange')
def _get_range():
    begin = request.args.get('begin')
    end = request.args.get('end')
    x = requests.get(HOME_URL + STORY_PORT + '/stories/range?begin={}&end={}'.format(begin, end))
    body = x.json()
    if x.status_code < 300:
        return render_template("stories.html", stories=body, home_url=GATEWAY_URL)
    else:
        flash(body['description'])
        return redirect(url_for('stories._get_all_stories'))


@storiesapi.operation('getDrafts')
@login_required
def _get_drafts():
    x = requests.get(HOME_URL + STORY_PORT + '/stories/getDrafts')
    data = x.json()

    return render_template("drafts.html", data=data, home_url=GATEWAY_URL)


@storiesapi.operation('getStory')
def _get_story(id_story):
    x = requests.get(HOME_URL + STORY_PORT + '/stories/{}'.format(id_story))
    body = x.json()
    return render_story(body)


@storiesapi.operation('deleteStory')
def _delete_story(id_story):
    x = requests.delete(HOME_URL + STORY_PORT + '/stories/{}'.format(id_story), json={'user_id': current_user.id})
    print(x.status_code)
    body = x.json()
    flash(body['description'])
    return redirect(url_for('gateway._home'))


@storiesapi.operation('getWritePage')
@login_required
def _get_write_page():
    form = StoryForm()
    if 'figures' not in session:
        flash("You need to set a story before", 'error')
        redirect(url_for('gateway._home'))

    return render_template("write_story.html", form=form, id_draft=None, words=session['figures'], home_url=GATEWAY_URL)


@storiesapi.operation('writeNew')
@login_required
def _write_new():
    form = request.form
    figures = '#' + '#'.join(session['figures']) + '#'
    data = {"as_draft": bool(int(form['as_draft'])), "text": form['text'],
            "user_id": current_user.id, "figures": figures}
    x = requests.post(HOME_URL + STORY_PORT + '/stories', json=data)
    body = x.json()
    if x.status_code < 300:
        session.pop('figures')
        session.pop('id_set')
        session.pop('name_set')
        session.pop('dice_number')
        return redirect(url_for('stories._get_all_stories'))
    else:
        new_form = StoryForm()
        new_form.text.data = form['text']
        return render_template("write_story.html", message=body['description'],
                               form=new_form, words=session['figures'], home_url=GATEWAY_URL)


@storiesapi.operation('getDraftPage')
@login_required
def _get_draft_page(id_story):
    form = StoryForm()
    x = requests.get(HOME_URL + STORY_PORT + '/stories/{}'.format(id_story))
    body = x.json()
    if x.status_code < 300:
        if body['author_id'] == current_user.id:
            form.text.data = body['text']
            session['figures'] = body['figures'].split('#')
        else:
            flash("You are not the author of the story", 'error')
            return redirect(url_for('gateway._home'))
    else:
        flash(body['description'], 'error')
        return redirect(url_for('gateway._home'))

    return render_template("write_story.html", form=form, id_draft=id_story, words=session['figures'][1:-1],
                           home_url=GATEWAY_URL)


@storiesapi.operation('completeDraft')
@login_required
def _complete_draft(id_story):
    form = request.form
    figures = '#' + '#'.join(session['figures']) + '#'
    data = {"as_draft": bool(int(form['as_draft'])), "text": form['text'],
            "user_id": current_user.id, "figures": figures}

    x = requests.put(HOME_URL + STORY_PORT + '/stories/{}'.format(id_story), json=data)
    body = x.json()

    if x.status_code < 300:
        session.pop('figures')
        return redirect(url_for('stories._get_all_stories'))
    else:
        new_form = StoryForm()
        new_form.text.data = form['text']
        return render_template("write_story.html", message=body['description'],
                               form=new_form, id_draft=id_story, words=session['figures'][1:-1], home_url=GATEWAY_URL)


@storiesapi.operation('getRandom')
def _get_random():
    method = '/stories/random'
    if current_user is not None and hasattr(current_user, 'id'):
        method += '?user_id={}'.format(current_user.id)

    x = requests.get(HOME_URL + STORY_PORT + method)
    body = x.json()
    if x.status_code < 300:
        return render_story(body)
    else:
        flash(body['description'], "error")

    return redirect(url_for("stories._get_all_stories"))


@storiesapi.operation('reactStory')
@login_required
def _react_story(id_story, reaction_caption):
    data = {"story_id": id_story, "reaction_caption": reaction_caption, "current_user": current_user.id}

    x = requests.post(HOME_URL + REACTION_PORT + "/react", json=data)
    body = x.json()

    flash(body['description'])
    s = requests.get(HOME_URL + STORY_PORT + "/stories/{}".format(id_story))
    print(s.status_code)
    if s.status_code < 300:
        return redirect(url_for('stories._get_story', id_story=id_story))
    else:
        flash("Error retrieving story!", 'error')
        return redirect(url_for('gateway._home'))


def render_story(story=None):
    context_vars = {"home_url": GATEWAY_URL, "react_url": GATEWAY_URL + 'stories/{}/react',
                    "exists": (story is not None)}
    if story:
        u = requests.get(HOME_URL + USER_PORT + "/users/{}".format(story['author_id']))
        if u.status_code < 300:
            r = requests.get(HOME_URL + REACTION_PORT + '/reactions/stats/{}'.format(story['id']))
            if r.status_code < 300:
                rolled_dice = story['figures'].split('#')
                rolled_dice = rolled_dice[1:-1]
                context_vars.update({"rolled_dice": rolled_dice, "story": story,
                                     "user": u.json(), "reactions": r.json()})
        else:
            flash("Can't find author of this story", "error")
            return redirect(url_for('stories._get_all_stories'))
    return render_template("story.html", **context_vars)
