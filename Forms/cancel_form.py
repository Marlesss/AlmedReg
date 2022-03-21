from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from Archimed import *


class CancelForm(FlaskForm):
    reasons = RadioField("Причина отказа", choices=[(reason["id"],
                         reason["name"]) for reason in get_response("talondeletereasons")["data"]])
    submit = SubmitField("Отменить")
