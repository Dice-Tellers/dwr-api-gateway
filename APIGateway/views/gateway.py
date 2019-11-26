import json
import os

import requests
from flakon import SwaggerBlueprint
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import (login_user, logout_user, login_required, current_user)
from werkzeug.exceptions import BadRequestKeyError

from APIGateway.classes.User import User
from APIGateway.forms import LoginForm, UserForm, StoryForm
from APIGateway.urls import *

# Path where the .yaml file are
yml_path = os.path.join(os.path.dirname(__file__), '..', 'yamls')

# Loading a SwaggerBlueprint for each yaml file
authapi = SwaggerBlueprint('gateway', '__name__', swagger_spec=os.path.join(yml_path, 'auth-api.yaml'))
usersapi = SwaggerBlueprint('users', '__name__', swagger_spec=os.path.join(yml_path, 'users-api.yaml'))
diceapi = SwaggerBlueprint('dice', '__name__', swagger_spec=os.path.join(yml_path, 'dice-api.yaml'))
storiesapi = SwaggerBlueprint('stories', '__name__', swagger_spec=os.path.join(yml_path, 'stories-api.yaml'))

#               Auth microservice

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


#               Users microservice

# Renders a page (users.html) with a list of all the users
@usersapi.operation('getAll')
def _get_all_users():

    x = requests.get(USER_URL + '/users')
    users = []

    if check_service_up(x):
        users = x.json()

    return render_template("users.html", users=users, home_url=GATEWAY_URL)


# Renders a page (wall.html) with the wall of a specified user
@usersapi.operation('getUser')
def _get_user(id_user):
    u = requests.get(HOME_URL + USER_PORT + '/users/{}'.format(id_user))

    if u.status_code < 300:
        user = u.json()
        fs = requests.get(HOME_URL + USER_PORT + '/users/{}/stats'.format(id_user))
        followers_stats = fs.json()

        if fs.status_code < 300:
            ss = requests.get(HOME_URL + STORY_PORT + '/stories/stats/{}'.format(id_user))
            stories_stats = ss.json()
            rs = requests.get(HOME_URL + REACTION_PORT + '/reactions/stats/user/{}'.format(id_user))
            if rs.status_code < 300:
                reactions_stats = rs.json()
            else:
                reactions_stats = {"tot_num_reactions": 0, "avg_reactions": 0.0}

            stats = {'follower_stats': followers_stats, 'stories_stats': stories_stats,
                     'reactions_stats': reactions_stats}

            return render_template("wall.html", my_wall=(current_user.id == user['id']), not_found=False,
                                   user_info=user, stats=stats, home_url=GATEWAY_URL)
        else:
            flash("Can't retrieve stories stats")
            return redirect(url_for('gateway._home'))
    else:
        return render_template("wall.html", not_found=True, home_url=GATEWAY_URL)


# TODO
# The operation to follow a specific user
@usersapi.operation('followUser')
@login_required
def _follow_user(id_user):

    x = requests.post(USER_URL + '/users/' + id_user + '/follow')

    if check_service_up(x):
        body = x.json()
        if x.status_code < 300:
            flash(body['description'], 'error')

    return render_template("wall.html", home_url=GATEWAY_URL)


# TODO
# The operation to unfollow a specific user
@usersapi.operation('unfollowUser')
@login_required
def _unfollow_user(id_user):

    x = requests.post(USER_URL + '/users/' + id_user + '/unfollow')

    if check_service_up(x):
        body = x.json()
        if x.status_code < 300:
            flash(body['description'], 'error')

    return render_template("wall.html", home_url=GATEWAY_URL)


# Get a list of all the followers of a specified user
@usersapi.operation('getFollowers')
def _get_followers(id_user):

    x = requests.get(USER_URL + '/users/' + id_user + '/followers')
    data = None

    if check_service_up(x):
        data = x.json()

    return render_template("followers.html", data=data, home_url=GATEWAY_URL)


# Get all the posted stories of a specified user
@usersapi.operation('getStoriesOfUser')
def _get_stories_of_user(id_user):
    s = requests.get(HOME_URL + STORY_PORT + '/users/{}/stories'.format(id_user))
    stories = []
    if s.status_code < 300:
        stories = s.json()

    return render_template("user_stories.html", stories=stories, home_url=GATEWAY_URL)


#                   Dice microservice

# Renders the Setting page (settings.html), where the set and number of dice can be chosen.
@diceapi.operation('getSettingsPage')
@login_required
def _get_settings_page():

    x = requests.get(DICE_URL + '/sets')

    if check_service_up(x):
        # No dice sets are loaded into the dice microservice
        if x.status_code == 204:
            flash("No dice set found. Please contact Jacopo Massa")
            redirect(url_for('gateway._home'))
        else:       # status_code < 300 ?
            sets = x.json()
            return render_template("settings.html", sets=sets, home_url=GATEWAY_URL)
    else:
        return redirect(url_for('gateway._home'))


# Renders the Roll page (roll_dice.html) with the rolled dice (set and num of dice previously chosen).
@diceapi.operation('getRollPage')
@login_required
def _get_roll_page():

    # Tries to get the dice_number from the request and set it into session
    try:
        dice_number = int(request.form['dice_number'])
        session['dice_number'] = dice_number
    # If it fails, set the dice_number with the one in session
    except BadRequestKeyError:
        dice_number = session['dice_number']

    # Tries to get the set id and name, which are in the form of "ID_NAME"
    try:
        s = request.form['dice_img_set'].split('_', 1)
        id_set = s[0]
        name_set = s[1]
        session['id_set'] = id_set
        session['name_set'] = name_set
    # If it fails, set the set's id and name with the ones in session
    except BadRequestKeyError:
        id_set = session['id_set']
        name_set = session['name_set']

    # Actually roll the dice
    data = {'dice_number': dice_number}
    x = requests.post(DICE_URL + '/sets/{}/roll'.format(id_set), json=data)

    if check_service_up(x):
        body = x.json()

        # If everything's fine, show the rolled dice and save references
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

        # Else flash the error and redirect to the first page (settings.html) to restart
        else:
            flash(body['description'], 'error')
            return redirect(url_for('dice._get_settings_page'))
    else:
        return redirect(url_for('gateway._home'))


#                   Stories microservice

# Renders the Stories page (stories.html), where ALL the published stories are seen
@storiesapi.operation('getAll')
def _get_all_stories():

    x = requests.get(STORY_URL + '/stories')
    stories = []

    if check_service_up(x):
        stories = x.json()

    return render_template("stories.html", stories=stories, home_url=GATEWAY_URL)


# Renders the Stories page (stories.html) with only the last published story for each registered user
@storiesapi.operation('getLatest')
def _get_latest():

    x = requests.get(STORY_URL + '/stories/latest')
    stories = []

    if check_service_up(x):
        stories = x.json()

    return render_template("stories.html", stories=stories, home_url=GATEWAY_URL)


# Renders the Stories page (stories.html) with only the stories published in a specified period
@storiesapi.operation('getRange')
def _get_range():

    # Get the begin and end date to put it into the query
    begin = request.args.get('begin')
    end = request.args.get('end')
    x = requests.get(STORY_URL + '/stories/range?begin={}&end={}'.format(begin, end))
    if check_service_up(x):
        body = x.json()

        if x.status_code < 300:
            return render_template("stories.html", stories=body, home_url=GATEWAY_URL)

        else:
            flash(body['description'])
            return redirect(url_for('stories._get_all_stories'))
    else:
        return redirect(url_for('gateway._home'))


# Renders the Drafts page (drafts.html) with al the drafts of the logged user
@storiesapi.operation('getDrafts')
@login_required
def _get_drafts():
    s = requests.get(HOME_URL + STORY_PORT + '/stories/drafts?user_id={}'.format(current_user.id))
    stories = []
    if s.status_code < 300:
        stories = s.json()

    return render_template("drafts.html", drafts=stories, home_url=GATEWAY_URL)


# Renders the Story page (story.html) with the specified story
@storiesapi.operation('getStory')
def _get_story(id_story):

    x = requests.get(STORY_URL + '/stories/{}'.format(id_story))

    if check_service_up(x):
        body = x.json()
        return render_story(body)
    else:
        return redirect(url_for('gateway._home'))


# The operation to delete a previously published story
@storiesapi.operation('deleteStory')
def _delete_story(id_story):

    x = requests.delete(STORY_URL + '/stories/{}'.format(id_story), json={'user_id': current_user.id})

    if check_service_up(x):
        body = x.json()
        flash(body['description'])

    return redirect(url_for('gateway._home'))


# Renders the Write page (write_story.html) where it's possible to publish a story (or save it as draft)
@storiesapi.operation('getWritePage')
@login_required
def _get_write_page():

    form = StoryForm()
    # If the user gets here in an unexpected way, redirect to home
    if 'figures' not in session:
        flash("You need to set a story before", 'error')
        redirect(url_for('gateway._home'))

    return render_template("write_story.html", form=form, id_draft=None, words=session['figures'], home_url=GATEWAY_URL)


# The operation to actually publish (or save as draft) a story
@storiesapi.operation('writeNew')
@login_required
def _write_new():

    form = request.form
    # Get the needed data from the form, then post it to the Stories service
    figures = '#' + '#'.join(session['figures']) + '#'
    data = {"as_draft": bool(int(form['as_draft'])), "text": form['text'],
            "user_id": current_user.id, "figures": figures}
    x = requests.post(STORY_URL + '/stories', json=data)

    if check_service_up(x):
        body = x.json()

        # If everything's fine, remove from the session the loaded data and redirect to the page with all the stories
        if x.status_code < 300:
            session.pop('figures')
            session.pop('id_set')
            session.pop('name_set')
            session.pop('dice_number')
            return redirect(url_for('stories._get_all_stories'))
        # Else reload the page with the specified error
        else:
            new_form = StoryForm()
            new_form.text.data = form['text']
            return render_template("write_story.html", message=body['description'],
                                   form=new_form, words=session['figures'], home_url=GATEWAY_URL)
    else:
        return redirect(url_for('gateway._home'))

# Renders the Write page (write_story.html) with a previously created draft
@storiesapi.operation('getDraftPage')
@login_required
def _get_draft_page(id_story):
    form = StoryForm()
    x = requests.get(STORY_URL + '/stories/{}'.format(id_story))

    if check_service_up(x):
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
    else:
        return redirect(url_for('gateway._home'))


# The operation to complete a draft, similar to the previous one
@storiesapi.operation('completeDraft')
@login_required
def _complete_draft(id_story):
    form = request.form
    figures = '#' + '#'.join(session['figures']) + '#'
    data = {"as_draft": bool(int(form['as_draft'])), "text": form['text'],
            "user_id": current_user.id, "figures": figures}

    x = requests.put(STORY_URL + '/stories/{}'.format(id_story), json=data)

    if check_service_up(x):
        body = x.json()

        if x.status_code < 300:
            session.pop('figures')
            return redirect(url_for('stories._get_all_stories'))
        else:
            new_form = StoryForm()
            new_form.text.data = form['text']
            return render_template("write_story.html", message=body['description'],
                                   form=new_form, id_draft=id_story, words=session['figures'][1:-1], home_url=GATEWAY_URL)
    else:
        return redirect(url_for('gateway._home'))


# Renders the Story page (story.html) with a randomly chosen story from other authors
@storiesapi.operation('getRandom')
def _get_random():
    method = '/stories/random'
    # If there's a logged user, then we concatenate its id to not get his stories
    if current_user is not None and hasattr(current_user, 'id'):
        method += '?user_id={}'.format(current_user.id)

    x = requests.get(STORY_URL + method)

    if check_service_up(x):
        body = x.json()

        if x.status_code < 300:
            return render_story(body)
        else:
            flash(body['description'], "error")

        return redirect(url_for("stories._get_all_stories"))
    else:
        return redirect(url_for('gateway._home'))


# The operation to react to a specific story
@storiesapi.operation('reactStory')
@login_required
def _react_story(id_story, reaction_caption):

    data = {"story_id": id_story, "reaction_caption": reaction_caption, "current_user": current_user.id}

    x = requests.post(REACTION_URL + "/react", json=data)
    body = x.json()

    flash(body['description'])
    s = requests.get(STORY_URL + "/stories/{}".format(id_story))

    if check_service_up(x) and check_service_up(s):
        if s.status_code < 300:
            return redirect(url_for('stories._get_story', id_story=id_story))
        else:
            flash("Error retrieving story!", 'error')

    return redirect(url_for('gateway._home'))


#                   Useful functions

def render_story(story=None):

    context_vars = {"home_url": GATEWAY_URL, "react_url": GATEWAY_URL + 'stories/{}/react',
                    "exists": (story is not None)}
    if story:
        u = requests.get(USER_URL + "/users/{}".format(story['author_id']))

        if u.status_code < 300:
            r = requests.get(REACTION_URL + '/reactions/stats/{}'.format(story['id']))

            if r.status_code < 300:
                rolled_dice = story['figures'].split('#')
                rolled_dice = rolled_dice[1:-1]
                context_vars.update({"rolled_dice": rolled_dice, "story": story,
                                     "user": u.json(), "reactions": r.json()})

        else:
            flash("Can't find author of this story", "error")
            return redirect(url_for('stories._get_all_stories'))

    return render_template("story.html", **context_vars)


def check_service_up(response):

    if response.status_code == 500:
        flash('The requested microservice is not up.', 'error')
        return False

    return True
