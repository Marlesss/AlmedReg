import datetime
import sqlalchemy
import sqlalchemy.orm as orm
from .db_session import SQLAlchemyBase
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin


class User(SQLAlchemyBase, UserMixin):
    SUPERADMIN, ADMIN, PATIENT, DOCTOR = -10, 0, 5, 10
    __tablename__ = "users"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    phone = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    med_card_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    type_of_user = sqlalchemy.Column(sqlalchemy.Integer, default=PATIENT)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'User {self.id}: {self.telephone} {self.email} {self.type_of_user}'
