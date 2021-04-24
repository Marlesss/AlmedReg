from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField, TelField, DateField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    first_name = StringField("Имя", validators=[DataRequired()])
    surname = StringField("Фамилия", validators=[DataRequired()])
    middle_name = StringField("Отчество")
    phone = TelField("Номер телефона", validators=[DataRequired()])
    birthdate = DateField("Дата рождения", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired()])
    submit = SubmitField("Зарегистрироваться")
