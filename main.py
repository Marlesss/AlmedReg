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
from Forms.user_management_form import UserManagementForm
from Forms.change_password_form import ChangePasswordForm
from data import db_session
from data.users import User
from for_tests import TALONS, PATIENT, DOCTOR, INTERVALS
from Archimed import *

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


def unformated_phone(formated_phone):
    return (formated_phone[:2] + formated_phone[3:6] + formated_phone[7:10] +
            formated_phone[11:13] + formated_phone[14:16])


def text_without_letters(text):
    date = ""
    for lit in text:
        if lit.isdigit():
            date += lit
    return date


def main():
    db_session.global_init("db/almed_database.db")
    session = db_session.create_session()
    admin = session.query(User).filter(User.phone == "+70000000000").first()
    if not admin:
        admin = User(phone="+70000000000", type_of_user=User.SUPERADMIN)
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
        phone = unformated_phone(form.phone.data)
        session = db_session.create_session()
        # Проверка на корректность данных
        if form.password.data != form.password_again.data:
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Пароли не совпадают")
        if "_" in phone:
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Введите номер телефона")
        # /Проверка на корректность данных
        # Проверка на уникальность данных
        if session.query(User).filter(User.phone == phone).first():
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Этот номер телефона уже зарегистрирован")
        # /Проверка на уникальность данных
        # Создаём мед. карту
        data = {
            "last_name": form.surname.data,
            "first_name": form.first_name.data,
            "middle_name": form.middle_name.data,
            "birthdate": f"{str(form.birthdate.data.day).rjust(2, '0')}.\
{str(form.birthdate.data.month).rjust(2, '0')}.{str(form.birthdate.data.year).rjust(4, '0')}",
            "phone": phone
        }
        # report = create_med_card(data)
        report = {
            "status": "Ok",
            "id": 1234
        }
        print(report)
        # /Создаём мед. карту
        if report['status'] != "Ok":
            return render_template("register.html", title="Регистрация", form=form,
                                   message="Ошибка при регистрации")
        user = User(
            phone=phone,
            med_card_id=report["id"]
        )
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
            return render_template("appointment_step_1.html", specializations=spec["data"],
                                   step=session["step"])
        elif session["step"] == 1:
            intervals = \
            get_response("intervals", params=[f"date_from={TODAY}", f"date_to={NEXT_MONTH}"])[
                "doctors"]
            doctors = list(
                filter(lambda doc: doc["primary_spec"] == session["steps"][0]["name"], intervals))
            day_today, month_today, year_today = map(int, session["interval"][0].split("."))
            day_week, month_week, year_week = map(int, session["interval"][1].split("."))
            time_is = str(dt.datetime.now()).split()[1].split(":")[:2]
            time_is = int(time_is[0]) * 60 + int(time_is[1])
            date_today = dt.date(day=day_today, month=month_today, year=year_today)
            date_week = dt.date(day=day_week, month=month_week, year=year_week)
            week = []
            for i in range(7):
                day = dt.date(int(year_today), int(month_today), int(day_today)) + dt.timedelta(
                    days=i)
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
            return render_template("appointment_step_3.html", intervals=intervals,
                                   step=session["step"])
        else:
            return render_template("appointment_finish.html", appointment=session["steps"],
                                   step=session["step"])
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
        left_date = ".".join(str(
            dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2])) - dt.timedelta(
                days=7)).split("-")[::-1])
        right_date = ".".join(
            str(dt.date(day=int(day[0]), month=int(day[1]), year=int(day[2])) - dt.timedelta(
                days=1)).split("-")[::-1])
        session["interval"] = [left_date, right_date]
    else:
        session["interval"] = [TODAY, NEXT_WEEK]
    print(session["interval"])
    return redirect("/appointment")


@app.route("/select_doc/<int:doc_ind>/<int:day_ind>")
def select_doc(doc_ind, day_ind):
    session["steps"][session["step"]] = session["steps"][session["step"]][doc_ind]
    session["steps"][session["step"]]["schedules"] = session["steps"][session["step"]]["schedules"][
        day_ind]
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


@app.route("/self_page", methods=["GET", "POST"])
def self_page():
    if not current_user.is_authenticated:
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
            notes = list(filter(
                lambda note: text_without_letters(note["date"]) == date or date in note[
                    "date"].split("."), notes))
        else:
            notes = list(
                filter(lambda note: note["docs"][0]["type"].lower() == text.lower(), notes))
    green_notes = list(filter(lambda note: note["status_id"] == 1, notes))
    grey_notes = list(filter(lambda note: note["status_id"] == 3, notes))
    red_notes = list(filter(lambda note: note["status_id"] == 4, notes))
    notes = (sorted(green_notes, key=lambda note: note["datetime"])
             + sorted(red_notes, key=lambda note: note["datetime"])
             + sorted(grey_notes, key=lambda note: note["datetime"]))
    return render_template("self_page.html", title="Личный кабинет", notes=notes, patient=patient,
                           form=form)


@app.route("/login", methods=['GET', "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        phone = unformated_phone(form.phone.data)
        if "_" in phone:
            return render_template("login.html", title="Авторизация",
                                   message="Введите номер телефона",
                                   form=form)

        session = db_session.create_session()
        user = session.query(User).filter(User.phone == phone).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template("login.html", title="Авторизация",
                               message="Неправильный номер телефона или пароль", form=form)
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
            list_of_users = list_of_users.filter(User.phone.like(filter_text))
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
        user.med_card_id = None
        session.merge(user)
        session.commit()
    except Exception:
        pass
    return redirect(f"/user_management/{id}")


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


@app.route("/user_management/<int:id>", methods=["GET", "POST"])
def user_management(id):
    if not (current_user.is_authenticated and
            current_user.type_of_user in (User.ADMIN, User.SUPERADMIN)):
        return redirect("/")
    session = db_session.create_session()
    user = session.query(User).get(id)
    if not user or user.type_of_user <= current_user.type_of_user:
        return redirect("/")
    form = UserManagementForm()
    if form.validate_on_submit():
        try:
            med_card_id = int(form.med_card_id.data)
        except Exception:
            return render_template("card.html", title="Управление пользователем", user=user,
                                   form=form, message="Ошибка при вводе id")
        if user.type_of_user == user.PATIENT:
            report = get_response("medcards",
                                  params=["filters[0][field]=number",
                                          f"filters[0][value]={med_card_id}"])
            if not report['data']:
                return render_template("card.html", title="Управление пользователем", user=user,
                                       form=form, message="Мед. карта не найдена")
            med_card = report['data'][0]
            user.med_card_id = med_card['id']
            session.merge(user)
            session.commit()
            return render_template("card.html", title="Управление пользователем", user=user,
                                   form=form,
                                   message=f"Мед. карта на имя {med_card['last_name']}\
 {med_card['first_name']} {med_card['middle_name']} найдена")
        elif user.type_of_user == user.DOCTOR:
            report = get_response("doctors", id=str(med_card_id))
            if not report:
                return render_template("card.html", title="Управление пользователем", user=user,
                                       form=form, message="Доктор не найден")
            user.med_card_id = report["id"]
            session.merge(user)
            session.commit()
            return render_template("card.html", title="Управление пользователем", user=user,
                                   form=form,
                                   message=f"Доктор по имени {report['name']}\
 {report['name1']} {report['name2']} найден")

        return render_template("card.html", title="Управление пользователем", user=user,
                               form=form)
    if user.med_card_id:
        med_card = get_response("medcards", id=str(user.med_card_id))
        form.med_card_id.data = med_card["number"]
    return render_template("card.html", title="Управление пользователем", user=user,
                           form=form)


if __name__ == "__main__":
    main()
