from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class NoteForm(FlaskForm):
    text = StringField("Введите дату(День.Месяц.Год) или название врача")
    search = SubmitField("Найти")
