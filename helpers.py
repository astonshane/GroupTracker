from flask import Flask, render_template, g, abort, request, flash
import json
import urllib2
from pprint import pprint


def parseGroups():
    data = json.loads(open('smallgroup.json').read())

    users = []
    projects = set()

    for user in data.get("users", {}):
        users.append(user)
        projects.add(user['project'])

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


def insertUser(user):
    data = json.loads(open('smallgroup.json').read())
    for user2 in data.get("users", {}):
        if user['github'] == user2['github']:
            flash("Already have a user with this Github id!", "error")
            return False
        if user['email'] == user2['email']:
            flash("Already have a user with this email!", "error")
    data['users'].append(user)

    with open('smallgroup.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4, separators=(',', ': '))
    return True
