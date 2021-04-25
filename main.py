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
from Forms.cancel_form import CancelForm
from Forms.change_password_form import ChangePasswordForm
from data import db_session
from data.users import User
from Archimed import get_response, TODAY, NEXT_WEEK, put_response

WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS = ["Янв.", "Фев.", "Марта", "Апр.", "Мая",
          "Июня", "Июля", "Авг.", "Сент.", "Окт.", "Нояб.", "Дек."]
SPECIALIZATIONS = ['Терапевт', 'Массажист', 'Стоматолог', 'Педиатр',
                   'Маммолог', 'Оториноларинголог', 'Уролог', 'Невролог',
                   'Врач', 'УЗИ', 'Гинеколог', 'Кардиолог', 'Эндокринолог',
                   'Холтер', 'Дерматовенеролог', 'Офтальмолог', 'Аллерголог',
                   'Онколог', 'Хирург', 'Ортопед', 'Инфекционист', 'Фтизиатр',
                   'Психиатр', 'Нарколог', 'Рентгенолог', 'Профпатолог',
                   'Психотерапевт', 'Психолог', 'Логопед', 'Гастроэнтеролог',
                   'Травматолог', 'Нейрохирург']

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


def unformated_phone(formated_phone):
    return (formated_phone[:2] + formated_phone[3:6] + formated_phone[7:10] +
            formated_phone[11:13] + formated_phone[14:16])


def text_without_letters(text):
    date = ""
    for lit in text:
        if lit.isdigit():
            date += lit
    return date


def date_int(date):
    date_time = date.split()
    return sum(map(int, date_time[0].split("."))) + sum(map(int, date_time[1].split(":")))


def main():
    db_session.global_init("db/almed_database.db")
    session = db_session.create_session()
    admin = session.query(User).filter(User.email == "admin").first()
    if not admin:
        admin = User(telephone="admin", email="admin@admin", type_of_user=User.SUPERADMIN)
        admin.set_password("admin")
        session.add(admin)
        session.commit()

    app.run(port=8080, host="127.0.0.1")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect("/")
    form = RegisterForm()
    if form.validate_on_submit():
        phone = unformated_phone(form.telephone.data)
        session = db_session.create_session()
        # Проверка на корректность данных
        if form.password.data != form.password_again.data:
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Пароли не совпадают!")
        if "_" in phone:
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Введите номер телефона!")
        # /Проверка на корректность данных
        # Проверка на уникальность данных
        if session.query(User).filter(User.telephone == phone).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Этот номер телефона уже зарегистрирован!")
        if form.email.data and session.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Эта электронная почта уже зарегистрирована!")
        # /Проверка на уникальность данных
        # Создаём мед. карту
        print(form.first_name.data, form.middle_name.data, form.surname.data)
        # /Создаём мед. карту
        user = User(
            telephone=phone
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
            spec = get_response("specializations")["data"]
            form = NoteForm()
            if form.validate_on_submit():
                spec_name = form.text.data
                spec = sorted(list(filter(lambda sp: spec_name.lower() in sp["name"].lower(), spec)),
                              key=lambda sp: sp["name"])
            else:
                spec = sorted(list(filter(lambda sp: sp["name"] in SPECIALIZATIONS, spec)), key=lambda sp: sp["name"])
            session["steps"] = [list(filter(lambda sp: sp["name"] in SPECIALIZATIONS, spec))]
            return render_template("appointment_step_1.html", specializations=spec, step=session["step"], form=form)
        elif session["step"] == 1:
            intervals = get_response("intervals", params=[f"date_from={session['interval'][0]}",
                                                          f"date_to={session['interval'][1]}"])["doctors"]
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
                last_date = dt.date(int(year_today), int(month_today), int(day_today)) - dt.timedelta(days=1)
                for i in range(len(doc["schedules"])):
                    day, month, year = map(int, doc["schedules"][i]["date"].split("."))
                    date = dt.date(year=year, day=day, month=month)
                    if date >= date_today:
                        if date_week >= date:
                            if date.day - last_date.day > 1:
                                current_schedules = (current_schedules +
                                                     [[] for k in
                                                      range(date.day - last_date.day - 1)]
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
            time_is = str(dt.datetime.now()).split()[1].split(":")[:2]
            time_is = int(time_is[0]) * 60 + int(time_is[1])
            if session["steps"][1]["schedules"]["date"] == TODAY:
                today = True
            else:
                today = False
            return render_template("appointment_step_3.html", intervals=intervals, step=session["step"], time=time_is,
                                   int=int, today=today)
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
        if session["interval"][0] == TODAY:
            return redirect("/appointment")
        day = session["interval"][0].split(".")
        left_date = ".".join(str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2])) - dt.timedelta(days=7)).split("-")[::-1])
        right_date = ".".join(
            str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2])) - dt.timedelta(days=1)).split("-")[::-1])
        session["interval"] = [left_date, right_date]
    else:
        session["interval"] = [TODAY, NEXT_WEEK]
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
        if len(session["steps"]) == 3:
            if "intervals" in session["steps"][session["step"]]:
                session["steps"][session["step"]] = session["steps"][session["step"]]["intervals"][ind]
            appointment = session["steps"]
            return render_template("appointment_finish.html", appointment=appointment)
        return redirect("/appointment")
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
        session["doctor"] = doctor
        session["note"] = note
        return render_template("check_note.html", note=note, patient=patient, doc=doctor)
    print("Не нашлось талона")
    return redirect("/")


@app.route("/cancel_note", methods=["GET", "POST"])
def cancel_note():
    form = CancelForm()
    if form.validate_on_submit():
        reason = form.reasons.data
        put_response("talons", {"status_id": 4}, id=str(session["note"]["id"]))
        return redirect("/self_page")
    return render_template("cancel_note.html", note=session["note"], doc=session["doctor"], form=form)


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
    return redirect(f"/self_page")


@app.route("/self_page", methods=["GET", "POST"])
def self_page():
    if not current_user.is_authenticated:
        return redirect("/")
    if current_user.type_of_user == 5:
        params = ["fields[]=id", "fields[]=last_name", "fields[]=first_name", "fields[]=middle_name",
                  "fields[]=birthdate", "fields[]=email"]
        patient = get_response("medcards", str(current_user.med_card_id), params)
        notes = get_response(f"medcards/{patient['id']}/talons")["data"]
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
        notes = (sorted(green_notes, key=lambda note: date_int(note["datetime"]))
                 + sorted(red_notes, key=lambda note: date_int(note["datetime"]))
                 + sorted(grey_notes, key=lambda note: date_int(note["datetime"])))
        return render_template("self_page.html", title="Личный кабинет", notes=notes, patient=patient, form=form, type=5)
    else:
        params = ["fields[]=id", "fields[]=last_name", "fields[]=first_name", "fields[]=middle_name",
                  "fields[]=type", "fields[]=scientific_degree"]
        doctor = get_response("doctors", str(current_user.med_card_id), params)
        notes = get_response(f"/doctors/{current_user.med_card_id}/talons", params=["filters[0][field]=status_id",
                                                                                    "filters[0][value]=1"])["data"]
        form = NoteForm()
        if form.validate_on_submit():
            text = form.text.data
            if text == "":
                pass
            elif not text.isalpha():
                date = text_without_letters(text)
                notes = list(
                    filter(lambda note: text_without_letters(note["date"]) == date or date in note["date"].split("."),
                           notes))
            else:
                notes = list(filter(lambda note: note["docs"][0]["type"].lower() == text.lower(), notes))
        notes = sorted(notes, key=lambda note: date_int(note["datetime"]))
        return render_template("self_page.html", title="Личный кабинет", notes=notes, doctor=doctor, form=form, type=10)


@app.route("/login", methods=['GET', "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        phone = unformated_phone(form.telephone.data)
        email = form.email.data
        if "_" in phone and not email:
            return render_template("login.html", title="Авторизация",
                                   message="Введите номер телефона или адрес электронной почты",
                                   form=form)

        session = db_session.create_session()
        if phone:
            user = session.query(User).filter(User.telephone == phone).first()
        else:
            user = session.query(User).filter(User.email == email).first()
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
        list_of_users = session.query(User)
        if form.text.data:
            filter_text = f'%{form.text.data}%'
            list_of_users = list_of_users.filter(User.telephone.like(filter_text) |
                                                 User.email.like(filter_text))
        list_of_users = list_of_users.all()
        return render_template("admin.html", title="Панель администратора",
                               list_of_users=list_of_users, form=form)
    list_of_users = session.query(User).all()
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


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template("change_password.html", title="Изменить пароль", form=form,
                                   message="Пароли не совпадают")
        if current_user.check_password(form.password.data):
            return render_template("change_password.html", title="Изменить пароль", form=form,
                                   message="Пароль не должен совпадать с предыдущим")
        session = db_session.create_session()
        user = session.query(User).get(current_user.id)
        user.set_password(form.password.data)
        session.merge(user)
        session.commit()
        return redirect("/")
    return render_template("change_password.html", title="Изменить пароль", form=form)


@app.route("/delete/<int:id>")
def delete_user(id):
    if not (current_user.is_authenticated and
            current_user.type_of_user in (User.ADMIN, User.SUPERADMIN)):
        return redirect("/")
    try:
        session = db_session.create_session()
        user = session.query(User).get(id)
        if user and user.type_of_user > current_user.type_of_user:
            session.delete(user)
            session.commit()
    except Exception:
        pass
    return redirect("/admin")


if __name__ == "__main__":
    main()
