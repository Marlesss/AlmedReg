from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = EmailField("Логин:", validators=[DataRequired()])
    password = PasswordField("Пароль:", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить пароль")
    submit = SubmitField("Войти")
