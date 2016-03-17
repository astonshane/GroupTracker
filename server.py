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
        if user['github'] == username:
            return user
    return None


@app.route("/")
def users():
    g.users, g.projects = parseGroups()
    return render_template("userlist.html")


@app.route("/user/<username>")
def user(username):
    user_obj = getUser(username)
    if user_obj is None:
        abort(404)

    data = json.loads(urllib2.urlopen('https://api.github.com/users/%s/events' % username).read())

    user_obj['pic'] = "https://acrobatusers.com/assets/images/template/author_generic.jpg"
    if len(data) > 0:
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
    events = []

    data = json.loads(urllib2.urlopen('https://api.github.com/repos/%s/%s/events' % (user, repo)).read())

    for event in data:
        event_obj = {}
        event_obj['type'] = event['type']
        event_obj['user'] = event['actor']['login']
        event_obj['date'] = event['created_at']
        events.append(event_obj)

    return render_template("project.html", project=repo, events=events)

if __name__ == "__main__":
    app.run(debug=True)
