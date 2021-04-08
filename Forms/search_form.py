from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    text = StringField("Введите данные пользователя")
    submit = SubmitField("Найти")
