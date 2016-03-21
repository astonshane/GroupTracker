from flask import Flask, render_template, g, abort
import json
import urllib2
from pprint import pprint

app = Flask(__name__)


def parseGroups():
    data = json.loads(open('smallgroup.json').read())

    users = []
    projects = set()

    for user in data.get("users", {}):
        pprint(user)
        users.append(user)
        projects.add(user['project'])

    print users

    print projects
    return users, projects


def getUser(username):
    data = json.loads(open('smallgroup.json').read())
    for user in data.get("users", {}):
        if user['github'].lower() == username.lower():
            return user
    return None


def getProject(projectname):
    data = json.loads(open('smallgroup.json').read())

    project = {"name": projectname, "RCOS": False, "users": []}

    for user in data.get("users", {}):
        if user['project'].lower() == projectname.lower():
            project['users'].append(user)
            project['RCOS'] = True

    return project


@app.route("/")
def users():
    g.users, g.projects = parseGroups()
    return render_template("userlist.html")


@app.route("/user/<username>")
def user(username):
    try:
        data = json.loads(urllib2.urlopen('https://api.github.com/users/%s/events' % username).read())
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

    events = []

    for event in data:
        event_obj = {}
        event_obj['type'] = event['type']
        event_obj['repo'] = event['repo']['name']
        event_obj['date'] = event['created_at']
        events.append(event_obj)

    return render_template("user.html", user=user_obj, events=events)


@app.route("/project/<user>/<repo>")
def project(user, repo):
    project = getProject("%s/%s" % (user, repo))
    pprint(project)
    events = []

    try:
        data = json.loads(urllib2.urlopen('https://api.github.com/repos/%s/%s/events' % (user, repo)).read())
    except:
        abort(404)

    for event in data:
        event_obj = {}
        event_obj['type'] = event['type']
        event_obj['user'] = event['actor']['login']
        event_obj['date'] = event['created_at']
        events.append(event_obj)

    return render_template("project.html", project=project, events=events)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
