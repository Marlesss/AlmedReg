from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField, TelField, DateField
from wtforms.validators import DataRequired, Regexp


class RegisterForm(FlaskForm):
    first_name = StringField("Имя", validators=[DataRequired()])
    surname = StringField("Фамилия", validators=[DataRequired()])
    middle_name = StringField("Отчество")
    phone = TelField("Номер телефона", validators=[DataRequired()])
    birthdate = DateField("Дата рождения", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired(),
                                                   Regexp('^.*(?=.{8,})(?=.*[a-zA-Z])(?=.*\d).*$',
                                                          message="Пароль должен состоять минимум\
 из 8 символов, включать цифры, прописные и строчные латинские буквы")])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired()])
    submit = SubmitField("Зарегистрироваться")
