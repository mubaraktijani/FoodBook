from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileField
from wtforms import StringField, IntegerField, TextAreaField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[Required(), Length(1, 30)])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[Required()])
    new_password = PasswordField('New Password', validators=[Required()])
    confirm_password = PasswordField('Confirm Password', validators=[Required()])
    submit = SubmitField('Update Password')

class UserForm(FlaskForm):
    card_id = IntegerField('User Card ID', validators=[Required()])
    fullname = StringField('Fullname', validators=[Required(), Length(1, 50)])
    email = StringField('Email Address', validators=[Required(), Length(1, 50)])
    password = PasswordField('Password', validators=[Required()])
    photo = FileField('photo', validators=[FileRequired()])
    submit = SubmitField('Add Staff')

class MenuItemForm(FlaskForm):
    name = StringField('Name', validators=[Required(), Length(1, 30)])
    price = IntegerField('Price', validators=[Required()])
    desc = TextAreaField('Description')
    photo = FileField('photo', validators=[FileRequired()])
    submit = SubmitField('Add Item')

class UpdateBalanceForm(FlaskForm):
    amount = IntegerField('Amount', validators=[Required()])
    submit = SubmitField('Update')