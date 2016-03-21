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


def getUserEvents(data):
    events = []
    for event in data:
        event_obj = {}
        event_obj['type'] = event['type']
        event_obj['repo'] = event['repo']['name']
        event_obj['date'] = event['created_at']

        if event['type'] == "IssuesEvent":
            event_obj['detail'] = event['payload']['issue']['title']

        elif event['type'] == "PushEvent":
            event_obj['branch'] = event['payload']['ref'].split("/")[-1]

            commits = event['payload']['commits']
            if len(commits) == 1:
                event_obj['detail'] = commits[0]['message']

            else:
                log = "<ul>"
                for commit in commits:
                    log += "<li>%s</li>" % commit['message']

                event_obj['detail'] = log + "</ul>"

        elif event['type'] == "PullRequestEvent":
            payload = event['payload']
            pr = payload['pull_request']
            event_obj['branch'] = "%s -> %s" % (pr['head']['label'], pr['base']['label'])
            event_obj['detail'] = "<i>%s</i>: %s" % (payload['action'], pr['title'])

        elif event['type'] == "CreateEvent":
            payload = event['payload']
            if payload['ref_type'] == "repository":
                event_obj['detail'] = "<i>repo:</i> %s" % event_obj['repo']
            else:
                event_obj['detail'] = "<i>%s:</i> %s" % (payload['ref_type'], payload['ref'])


        events.append(event_obj)

    return events
