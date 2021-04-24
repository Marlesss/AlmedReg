from flask import Flask, render_template, redirect, url_for, request, make_response, session, abort
from flask import session as note_session
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime as dt
import pprint

from Forms.register_form import RegisterForm
from Forms.login_form import LoginForm
from Forms.search_form import SearchForm
from Forms.note_form import NoteForm
from data import db_session
from data.users import User
from for_tests import TALONS, PATIENT, DOCTOR, INTERVALS
from Archimed import get_response, TODAY, NEXT_WEEK, NEXT_MONTH

WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS = ["Янв.", "Фев.", "Марта", "Апр.", "Мая",
          "Июня", "Июля", "Авг.", "Сент.", "Окт.", "Нояб.", "Дек."]

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = dt.timedelta(minutes=180)
Bootstrap(app)

app.config["SECRET_KEY"] = 'secret_key'
app.config["PERMANENT_SESSION_LIFETIME"] = dt.timedelta(days=365)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def text_without_letters(text):
    date = ""
    for lit in text:
        if lit.isdigit():
            date += lit
    return date


def main():
    db_session.global_init("db/almed_database.db")
    session = db_session.create_session()
    admin = session.query(User).filter(User.email == "admin").first()
    if not admin:
        admin = User(telephone="admin", email="admin", type_of_user=User.SUPERADMIN)
        admin.set_password("admin")
        session.add(admin)
        session.commit()
    app.run(port=8080, host="127.0.0.1")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        # Проверка на корректность данных
        # /Проверка на корректность данных
        # Проверка на уникальность данных
        if session.query(User).filter(User.telephone == form.telephone.data).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Этот номер телефона уже зарегистрирован!")
        if form.email.data and session.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Эта электронная почта уже зарегистрирована!")
        # /Проверка на уникальность данных
        user = User(
            telephone=form.telephone.data
        )
        if form.email.data:
            user.email = form.email.data
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/appointment", methods=["GET", "POST"])
def get_appointment():
    try:
        if session.get("step", 0) == 0:
            session["step"] = 0
            spec = get_response("specializations")
            session["steps"] = [spec["data"]]
            return render_template("appointment_step_1.html", specializations=spec["data"], step=session["step"])
        elif session["step"] == 1:
            intervals = get_response("intervals", params=[f"date_from={TODAY}", f"date_to={NEXT_MONTH}"])["doctors"]
            doctors = list(filter(lambda doc: doc["primary_spec"] == session["steps"][0]["name"], intervals))
            day_today, month_today, year_today = map(int, session["interval"][0].split("."))
            day_week, month_week, year_week = map(int, session["interval"][1].split("."))
            time_is = str(dt.datetime.now()).split()[1].split(":")[:2]
            time_is = int(time_is[0]) * 60 + int(time_is[1])
            date_today = dt.date(day=day_today, month=month_today, year=year_today)
            date_week = dt.date(day=day_week, month=month_week, year=year_week)
            week = []
            for i in range(7):
                day = dt.date(int(year_today), int(month_today), int(day_today)) + dt.timedelta(days=i)
                week.append([WEEK[day.weekday()], str(day.day) + " " + MONTHS[day.month - 1]])
            for doc in doctors:
                current_schedules = []
                last_date = date_today
                for i in range(len(doc["schedules"])):
                    day, month, year = map(int, doc["schedules"][i]["date"].split("."))
                    date = dt.date(year=year, day=day, month=month)
                    if date >= date_today:
                        if date_week >= date:
                            if date.day - last_date.day > 1:
                                current_schedules = (current_schedules +
                                                     [[] for k in
                                                      range(int(str(date - last_date).split()[0]))]
                                                     + [doc["schedules"][i]])
                            else:
                                current_schedules = (current_schedules + [doc["schedules"][i]])
                            last_date = date
                        else:
                            break
                if len(current_schedules) < 7:
                    doc["schedules"] = (current_schedules[::]
                                        + [[] for k in range(7 - len(current_schedules))])
                else:
                    doc["schedules"] = current_schedules[::]
                for schedule in doc["schedules"]:
                    if schedule != []:
                        for interval in schedule["intervals"]:
                            if interval["free"]:
                                schedule["free"] = True
            session["steps"] = session["steps"][:1] + [doctors]
            if session["interval"][0] == TODAY:
                today = True
            else:
                today = False
            return render_template("appointment_step_2.html", doctors=doctors, step=session["step"],
                                   week=week, time=time_is, int=int, len=len, today=today)
        elif session["step"] == 2:
            intervals = session["steps"][1]["schedules"]
            session["steps"] = session["steps"][:2] + [intervals]
            print(intervals)
            return render_template("appointment_step_3.html", intervals=intervals, step=session["step"])
        else:
            return render_template("appointment_finish.html", appointment=session["steps"], step=session["step"])
    except Exception as e:
        return render_template("appointment_step_1.html")


@app.route("/change_interval/<int:change_type>")
def change_interval(change_type):
    if change_type == 1:
        day = session["interval"][1].split(".")
        right_date = ".".join(str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2]))
                                + dt.timedelta(days=7)).split("-")[::-1])
        left_date = ".".join(str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2]))
                                + dt.timedelta(days=1)).split("-")[::-1])
        session["interval"] = [left_date, right_date]
    elif change_type == 2:
        day = session["interval"][0].split(".")
        left_date = ".".join(str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2])) - dt.timedelta(days=7)).split("-")[::-1])
        right_date = ".".join(
            str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2])) - dt.timedelta(days=1)).split("-")[::-1])
        session["interval"] = [left_date, right_date]
    else:
        session["interval"] = [TODAY, NEXT_WEEK]
    print(session["interval"])
    return redirect("/appointment")


@app.route("/select_doc/<int:doc_ind>/<int:day_ind>")
def select_doc(doc_ind, day_ind):
    session["steps"][session["step"]] = session["steps"][session["step"]][doc_ind]
    session["steps"][session["step"]]["schedules"] = session["steps"][session["step"]]["schedules"][day_ind]
    session["step"] = 2
    return redirect("/appointment")


@app.route("/change_step/<string:step>/<string:ind>", methods=["GET", "POST"])
def change_step(step, ind):
    ind = int(ind)
    session["interval"] = [TODAY, NEXT_WEEK]
    if step != "finish":
        step = int(step)
    else:
        session["steps"][session["step"]] = session["steps"][session["step"]]["intervals"][ind]
        appointment = session["steps"]
        return render_template("appointment_finish.html", appointment=appointment)
    print(session["step"], session["steps"], ind, sep="\n")
    if ind >= 0:
        session["steps"][session["step"]] = session["steps"][session["step"]][ind]
    session["step"] = step
    return redirect("/appointment")


@app.route("/check_note/<int:note_id>", methods=["GET", "POST"])
def check_note(note_id):
    note = get_response("talons", id=str(note_id))
    if note and note["patient_id"] == current_user.med_card_id:
        patient = get_response("medcards", id=str(note["patient_id"]))
        doctor = get_response("doctors", id=str(note["docs"][0]["id"]))
        return render_template("check_note.html", note=note, patient=patient, doc=doctor)
    print("Не нашлось талона")
    return redirect("/")


@app.route("/post_appointment")
def post_appointment():
    pprint.pprint(session["steps"])
    post_data = {
        "doc_id": session["steps"][1]["id"],
        "begintime": session["steps"][2]["start"],
        "date": session["steps"][1]["schedules"]["date"],
        "patient_id": current_user.med_card_id
    }
    print(post_data)
    # Тута пост запрос
    return redirect("/clear_session")


@app.route("/clear_session")
def clear_session():
    session["step"] = 0
    session["steps"] = []
    session['interval'] = []
    return redirect(f"/self_page/{current_user.id}")


@app.route("/self_page/<int:self_id>", methods=["GET", "POST"])
def self_page(self_id):
    if not current_user.is_authenticated:
        return redirect("/")
    if current_user.id != self_id:
        return redirect("/")
    params = ["fields[]=id", "fields[]=last_name", "fields[]=first_name", "fields[]=middle_name",
              "fields[]=birthdate", "fields[]=email"]
    patient = get_response("medcards", str(current_user.med_card_id), params)
    notes = list(filter(lambda note: note["patient_id"] == patient["id"],
                        get_response("talons",
                                     params=["filters[0][field]=patient_id",
                                             f"filters[0][value]={patient['id']}"])["data"]))
    form = NoteForm()
    if form.validate_on_submit():
        text = form.text.data
        if text == "":
            pass
        elif not text.isalpha():
            date = text_without_letters(text)
            notes = list(filter(lambda note: text_without_letters(note["date"]) == date or date in note["date"].split("."), notes))
        else:
            notes = list(filter(lambda note: note["docs"][0]["type"].lower() == text.lower(), notes))
    green_notes = list(filter(lambda note: note["status_id"] == 1, notes))
    grey_notes = list(filter(lambda note: note["status_id"] == 3, notes))
    red_notes = list(filter(lambda note: note["status_id"] == 4, notes))
    notes = (sorted(green_notes, key=lambda note: note["datetime"])
             + sorted(red_notes, key=lambda note: note["datetime"])
             + sorted(grey_notes, key=lambda note: note["datetime"]))
    return render_template("self_page.html", title="Личный кабинет", notes=notes, patient=patient, form=form)


@app.route("/login", methods=['GET', "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.telephone == form.login.data).first()
        if not user:
            user = session.query(User).filter(User.email == form.login.data).first()
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


@app.route("/admin", methods=['GET', "POST"])
def admin_interface():
    if not (current_user.is_authenticated and
            current_user.type_of_user in (User.ADMIN, User.SUPERADMIN)):
        return redirect("/")
    form = SearchForm()
    session = db_session.create_session()
    if form.validate_on_submit():
        filter_text = f'%{form.text.data}%'
        list_of_users = session.query(User).filter(User.telephone.like(filter_text) |
                                                   User.email.like(filter_text)).all()[:10]
        return render_template("admin.html", title="Панель администратора",
                               list_of_users=list_of_users, form=form)
    list_of_users = session.query(User).all()[:10]
    return render_template("admin.html", title="Панель администратора",
                           list_of_users=list_of_users, form=form)


@app.route("/redefine_role/<string:role>/<int:id>")
def redefine_role(role, id):
    if not (current_user.is_authenticated and
            current_user.type_of_user in (User.ADMIN, User.SUPERADMIN)):
        return redirect("/")
    try:
        session = db_session.create_session()
        user = session.query(User).get(id)
        user.type_of_user = {"admin": User.ADMIN, "patient": User.PATIENT,
                             "doctor": User.DOCTOR}[role]
        session.merge(user)
        session.commit()
    except Exception:
        pass
    return redirect("/admin")


if __name__ == "__main__":
    main()
