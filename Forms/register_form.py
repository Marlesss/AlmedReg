from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    first_name = StringField("Имя", validators=[DataRequired()])
    surname = StringField("Фамилия", validators=[DataRequired()])
    middle_name = StringField("Отчество")
    telephone = TelField("Номер телефона", validators=[DataRequired()])
    email = EmailField("Почта")
    password = PasswordField("Пароль", validators=[DataRequired()])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired()])
    submit = SubmitField("Зарегистрироваться")
