from flask import Flask, render_template, g, abort, request, flash, session
import json
import urllib2
from pprint import pprint
from datetime import datetime, timedelta


def parseGroups():
    smallgroup = session.get('small_group')
    data = json.loads(open('smallgroups.json').read())

    users = []
    projects = set()

    for group in data.get("groups", []):
        print "group", group['title']
        if group['title'] == smallgroup:
            for user in group.get("users", {}):
                users.append(user)
                projects.add(user['project'])
            break

    return users, projects, smallgroup


def getUser(username):
    data = json.loads(open('smallgroups.json').read())
    for group in data.get("groups", []):
        for user in group.get("users", {}):
            if user['github'].lower() == username.lower():
                return user
    return None


def getProject(projectname):
    data = json.loads(open('smallgroups.json').read())

    project = {"name": projectname, "RCOS": False, "users": []}

    for group in data.get("groups", []):
        for user in group.get("users", {}):
            if user['project'].lower() == projectname.lower():
                project['users'].append(user)
                project['RCOS'] = True

    return project


def insertUser(user):
    current_smallgroup = session.get("small_group")
    new_data = {"groups": []}
    data = json.loads(open('smallgroups.json').read())
    for group in data.get("groups", []):
        if group['title'] == current_smallgroup:
            members = group.get("users", [])
            for user2 in group.get("users", {}):
                if user['github'] == user2['github']:
                    flash("Already have a user with this Github id!", "error")
                    return False
                if user['email'] == user2['email']:
                    flash("Already have a user with this email!", "error")
                    return False
            members.append(user)
            group['users'] = members
        new_data['groups'].append(group)

    with open('smallgroups.json', 'w') as outfile:
        json.dump(new_data, outfile, sort_keys=True, indent=4, separators=(',', ': '))
    return True


def parseEvent(event):
    event_obj = {}

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
        event_obj['detail'] = "<i>%s:</i> %s" % (payload['ref_type'], payload['ref'])

    elif event['type'] == "ForkEvent":
        event_obj['detail'] = event['payload']['forkee']['full_name']

    elif event['type'] == "MemberEvent":
        member = event['payload']['member']['login']
        event_obj['detail'] = "Added <a href='/user/%s'>%s</a> to the Repository" % (member, member)

    elif event['type'] == "DeleteEvent":
        event_obj['detail'] = "<i>%s</i>: %s" % (event['payload']['ref_type'], event['payload']['ref'])

    elif event['type'] == "IssueCommentEvent":
        event_obj['detail'] = "<i>%s</i>: %s" % (event['payload']['issue']['title'], event['payload']['comment']['body'])
    return event_obj


def getUserEvents(username, github):
    data = github.get("users/%s/events?per_page=100" % username)

    events = []

    for event in data:
        event_obj = {}
        event_obj['type'] = event['type']
        event_obj['repo'] = event['repo']['name']

        date = event['created_at']

        date_object = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        now = datetime.utcnow()
        two_weeks = timedelta(weeks=2)
        if (now-date_object) < two_weeks:
            event_obj['date'] = date_object.strftime("%m/%d/%Y")

            parsed = parseEvent(event)
            for cat in parsed:
                event_obj[cat] = parsed[cat]

            events.append(event_obj)

    return events


def getProjectEvents(project, github):
    data = github.get("repos/%s/events?per_page=100" % project)

    events = []

    for event in data:
        event_obj = {}
        event_obj['type'] = event['type']
        event_obj['user'] = event['actor']['login']
        date = event['created_at']

        date_object = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        now = datetime.utcnow()
        two_weeks = timedelta(weeks=2)
        if (now-date_object) < two_weeks:
            event_obj['date'] = date_object.strftime("%m/%d/%Y")
            parsed = parseEvent(event)
            for cat in parsed:
                event_obj[cat] = parsed[cat]

            events.append(event_obj)

    return events
