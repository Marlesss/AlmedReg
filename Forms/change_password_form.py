from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Regexp


class ChangePasswordForm(FlaskForm):
    password = PasswordField("Введите новый пароль",
                             validators=[DataRequired(),
                                         Regexp('^.*(?=.{8,})(?=.*[a-zA-Z])(?=.*\d).*$',
                                                message="Пароль должен состоять минимум\
 из 8 символов, включать цифры, прописные и строчные латинские буквы")])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired()])
    submit = SubmitField("Изменить пароль")
