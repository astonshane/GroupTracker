from flask import Flask, render_template, g
import json
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


@app.route("/")
def hello():
    return "hello world!"


@app.route("/users/")
def users():
    g.users, g.projects = parseGroups()
    return render_template("userlist.html")


@app.route("/user/<username>")
def user(username):
    return render_template("user.html")


@app.route("/project/<user>/<repo>")
def project(user, repo):
    return render_template("project.html")

if __name__ == "__main__":
    app.run(debug=True)
