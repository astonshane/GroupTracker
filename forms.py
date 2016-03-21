from wtforms import Form, TextField, validators

class AddUser(Form):
    fname = TextField('First Name', validators=[validators.required()])
    lname = TextField('Last Name', validators=[validators.required()])
    email = TextField('Email', validators=[validators.required(), validators.email()])
    github = TextField('Github Username', validators=[validators.required()])
    project = TextField('Project', validators=[validators.required()])
