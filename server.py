from flask import Flask, request, g, session, redirect, url_for, render_template, abort
from flask import render_template_string
from flask.ext.github import GitHub

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import json
import urllib2
import os
from pprint import pprint
from forms import AddUser, PickSmallGroup, getSmallGroups
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

app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID', "")
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET', "")

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
    return github.authorize()


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/request_login')
def requestLogin():
    if g.user:
        return redirect(url_for("index"))
    return render_template("request_login.html")


@app.route('/export')
def export():
    return str(json.loads(open('smallgroups.json').read()))


@app.route('/selectsmallgroup', methods=('GET', 'POST'))
def selectSmallGroup():
    if not g.user:
        return redirect(url_for("requestLogin"))

    form = PickSmallGroup(request.form)
    form.small_group.choices = getSmallGroups()
    if request.method == 'POST' and form.validate():
        session['small_group'] = request.form['small_group']
        session.modified = True
        return redirect(url_for("index"))

    return render_template("select_smallgroup.html", form=form)


@app.route('/newsmallgroup', methods=['POST'])
def newSmallGroup():
    print "HERE", request.form['title']
    if request.form['title'] != "":
        print "SUCCESS"
        new_title = request.form['title']
        data = json.loads(open('smallgroups.json').read())
        for group in data.get("groups", []):
            if group['title'] == new_title:
                flash("There is already a smallgroup with this name!", "error")
                return redirect(url_for("selectSmallGroup"))
        new_group = {"title": new_title, "users": []}
        data['groups'].append(new_group)
        with open('smallgroups.json', 'w') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    else:
        flash("Must enter a group name!", "error")
    return redirect(url_for("selectSmallGroup"))


@app.route("/", methods=('GET', 'POST'))
def index():
    if not g.user:
        return redirect(url_for("requestLogin"))
    if session.get('small_group', None) is None:
        return redirect(url_for("selectSmallGroup"))
    form = AddUser(request.form)
    if request.method == 'POST' and form.validate():
        user = {
            "fname": request.form['fname'],
            "lname":  request.form['lname'],
            "email": request.form['email'],
            "project": request.form['project'],
            "github": request.form['github'],
            "rcosio": request.form['rcosio']
        }
        if insertUser(user):
            return redirect("/")

    g.users, g.projects, g.title = parseGroups()
    return render_template("index.html", form=form)


@app.route("/user/<username>")
def user(username):
    if not g.user:
        return redirect(url_for("requestLogin"))
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
    if not g.user:
        return redirect(url_for("requestLogin"))
    project = getProject("%s/%s" % (user, repo))
    pprint(project)

    try:
        data = github.get('repos/%s/%s/events' % (user, repo))
    except:
        abort(404)

    events = getProjectEvents("%s/%s" % (user, repo), github)

    return render_template("project.html", project=project, events=events)


@app.route("/remove/<github>")
def removeUser(github):
    smallgroup = session.get("small_group")
    data = json.loads(open('smallgroups.json').read())
    new_groups = []
    for group in data.get("groups", []):
        if group['title'] == smallgroup:
            new_users = []
            for user in group['users']:
                if user['github'] != github:
                    new_users.append(user)
            group['users'] = new_users
        new_groups.append(group)
    data['groups'] = new_groups

    with open('smallgroups.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    return redirect(url_for("index"))



@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
