from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class UserManagementForm(FlaskForm):
    med_card_id = StringField("Поле ввода id", validators=[DataRequired()])
    submit = SubmitField("Подтвердить")
