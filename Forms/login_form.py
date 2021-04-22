from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    telephone = TelField("Номер телефона")
    email = EmailField("Почта")
    password = PasswordField("Пароль:", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить пароль")
    submit = SubmitField("Войти")
