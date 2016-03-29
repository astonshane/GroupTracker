from wtforms import Form, TextField, validators, RadioField
import os
import json


def getSmallGroups():
    smallgroups = []
    files = os.listdir("smallgroups/")
    for smallgroup in files:
        data = json.loads(open('smallgroups/%s' % smallgroup).read())
        smallgroups.append((smallgroup, data.get('title', 'no-title')))

    return smallgroups


class AddUser(Form):
    fname = TextField('First Name', validators=[validators.required()])
    lname = TextField('Last Name', validators=[validators.required()])
    email = TextField('Email', validators=[validators.required(), validators.email()])
    github = TextField('Github Username', validators=[validators.required()])
    project = TextField('Project', validators=[validators.required()])
    rcosio = TextField('rcos.io ID', validators=[validators.required()])


class PickSmallGroup(Form):
    small_group = RadioField('Small Group', validators=[validators.required()], choices=getSmallGroups())
