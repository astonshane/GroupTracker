from flask import Flask, request, g, session, redirect, url_for, render_template, abort
from flask import render_template_string
from flask.ext.github import GitHub

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import json
import urllib2
from pprint import pprint
from forms import AddUser
from helpers import *

DATABASE_URI = 'sqlite:////tmp/github-flask.db'
SECRET_KEY = 'development key'
DEBUG = True

# Set these values
GITHUB_CLIENT_ID = 'XXX'
GITHUB_CLIENT_SECRET = 'YYY'

# setup flask
app = Flask(__name__)
app.config.from_object(__name__)

config = json.loads(open('config.json').read())
app.config['GITHUB_CLIENT_ID'] = config['GITHUB_CLIENT_ID']
app.config['GITHUB_CLIENT_SECRET'] = config['GITHUB_CLIENT_SECRET']

# setup github-flask
github = GitHub(app)

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(200))
    github_access_token = Column(String(200))

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@app.route('/tmp')
def index2():
    if g.user:
        t = 'Hello! <a href="{{ url_for("user") }}">Get user</a> ' \
            '<a href="{{ url_for("logout") }}">Logout</a>'
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template_string(t)


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)
    user.github_access_token = access_token
    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize()
    else:
        return 'Already logged in'


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/user')
def user2():
    return str(github.get('repos/astonshane/GroupTracker/events'))


@app.route("/", methods=('GET', 'POST'))
def index():
    form = AddUser(request.form)
    if request.method == 'POST' and form.validate():
        user = {
            "name": "%s %s" % (request.form['fname'], request.form['lname']),
            "email": request.form['email'],
            "project": request.form['project'],
            "github": request.form['github'],
            "rcosio": request.form['rcosio']
        }
        if insertUser(user):
            return redirect("/")

    g.users, g.projects = parseGroups()
    return render_template("userlist.html", form=form)


@app.route("/user/<username>")
def user(username):
    try:
        data = github.get('users/%s/events' % username)
    except:
        abort(404)

    if len(data) == 0:
        abort(404)

    user_obj = getUser(username)
    if user_obj is None:
        user_obj = {}
        user_obj['RCOS'] = False
        user_obj['name'] = data[0]['actor']['login']
        user_obj['github'] = data[0]['actor']['login']
    else:
        user_obj['RCOS'] = True

    user_obj['pic'] = data[0]['actor']['avatar_url']

    events = getUserEvents(username, github)

    return render_template("user.html", user=user_obj, events=events)


@app.route("/project/<user>/<repo>")
def project(user, repo):
    project = getProject("%s/%s" % (user, repo))
    pprint(project)

    try:
        data = github.get('repos/%s/%s/events' % (user, repo))
    except:
        abort(404)

    events = getProjectEvents("%s/%s" % (user, repo), github)

    return render_template("project.html", project=project, events=events)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
