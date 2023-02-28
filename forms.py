from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, URL, Optional


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class AddItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    odds = StringField('odds', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    price = DecimalField('Price', places=2, validators=[DataRequired()])
    detailed_description = TextAreaField('Detailed description', validators=[DataRequired()])
    img_url = StringField('Image Url', validators=[DataRequired()])
    submit = SubmitField('Add Item')