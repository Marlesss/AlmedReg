from flask import Flask, render_template, redirect, url_for, request, make_response, session, abort
from flask import jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
from flask_restful import reqparse, abort, Api, Resource

from Forms.register_form import RegisterForm
from Forms.login_form import LoginForm
from data import db_session
from data.users import User
from for_tests import TALONS, PATIENT, DOCTOR

app = Flask(__name__)

app.config["SECRET_KEY"] = 'secret_key'
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def main():
    db_session.global_init("db/almed_database.db")
    app.run(port=8080, host="127.0.0.1")


@app.route("/")
def index():
    session = db_session.create_session()
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Эта электронная почта уже зарегистрирована!")
        user = User(
            email=form.email.data,
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/check_note/<int:note_id>", methods=["GET", "POST"])
def check_note(note_id):
    notes = TALONS["data"]
    for note in notes:
        if note["id"] == note_id:
            patient = PATIENT
            doctor = DOCTOR
            return render_template("check_note.html", note=note, patient=patient, doc=doctor)
    print("Не нашлось талона")
    return redirect("/")


@app.route("/self_page", methods=["GET", "POST"])
def self_page():
    patient = PATIENT
    notes = list(filter(lambda note: note["patient_id"] == patient["id"], TALONS["data"]))
    return render_template("self_page.html", title="Личный кабинет", notes=notes, patient=patient)


@app.route("/login", methods=['GET', "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template("login.html", title="Авторизация",
                               message="Неправильный логин или пароль", form=form)
    return render_template("login.html", title="Авторизация", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    main()
