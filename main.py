from flask import Flask, render_template, redirect, url_for, request, make_response, session, abort
from flask import session as note_session
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
from pprint import pprint

from Forms.register_form import RegisterForm
from Forms.login_form import LoginForm
from Forms.search_form import SearchForm
from Forms.note_form import NoteForm
from Forms.user_management_form import UserManagementForm
from Forms.change_password_form import ChangePasswordForm
from data import db_session
from data.users import User
from for_tests import TALONS, PATIENT, DOCTOR
from Archimed import *

REGISTER_STEPS = []

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=180)
Bootstrap(app)

app.config["SECRET_KEY"] = 'secret_key'
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)
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
    if session["step"] == 1:
        session["steps"] = []
    #        buildings = get_response("specializations")
    #        return render_template("appointment_step_1.html", buildings=buildings["data"])
    elif session["step"] == 2:
        session["steps"] = session["steps"][:1]
    elif session["step"] == 3:
        session["steps"] = session["steps"][:2]
    return render_template("base.html")


@app.route("/change_step/<int:step>", methods=["GET", "POST"])
def change_step(step):
    session["step"] = step
    redirect("/appointment")


"""
@app.route("/appointment/1", methods=["GET", "POST"])
def get_building():
    global REGISTER_STEPS
    REGISTER_STEPS = [get_response("buildings", params=["fields[]=name", "fields[]=address", "fields[]=id"])["data"]]
    return render_template("appointment_step_1.html", buildings=REGISTER_STEPS[0], step=1)


@app.route("/appointment/2/<int:chosen_building>")
def get_spec(chosen_building):
    global REGISTER_STEPS
    spec = get_response("specializations", params=["fields[]=name", "fields[]=id"])["data"]
    if REGISTER_STEPS[0].__class__.__name__ == "list":
        REGISTER_STEPS = [REGISTER_STEPS[0][chosen_building], spec]
    else:
        REGISTER_STEPS = [REGISTER_STEPS[0], spec]
    print(REGISTER_STEPS)
    return render_template("appointment_step_2.html", specializations=REGISTER_STEPS[1],
                           chosen_building=chosen_building, step=2)


@app.route("/appointment/3/<int:chosen_building>/<int:chosen_specialization>")
def get_doc(chosen_building, chosen_specialization):
    global REGISTER_STEPS
    if REGISTER_STEPS[1].__class__.__name__ == "list":
        REGISTER_STEPS = [REGISTER_STEPS[0], REGISTER_STEPS[1][chosen_specialization], ["врач1", "врач2", "врач3"]]
    else:
        REGISTER_STEPS = REGISTER_STEPS[:2] + [["врач1", "врач2", "врач3"]]
    print(REGISTER_STEPS)
    return render_template("appointment_step_3.html", doctors=REGISTER_STEPS[2], chosen_building=chosen_building,
                           chosen_specialization=chosen_specialization, step=3)


@app.route("/appointment/4/<int:chosen_building>/<int:chosen_specialization>/<int:chosen_doc>")
def get_interval(chosen_building, chosen_specialization, chosen_doc):
    global REGISTER_STEPS
    if REGISTER_STEPS[2].__class__.__name__ == "list":
        REGISTER_STEPS = REGISTER_STEPS[:2] + [REGISTER_STEPS[2][chosen_doc], ["10:10", "11:11", "12:12"]]
    else:
        REGISTER_STEPS = REGISTER_STEPS[:3] + [["10:10", "11:11", "12:12"]]
    print(REGISTER_STEPS)
    return render_template("appointment_step_4.html", intervals=REGISTER_STEPS[3], chosen_building=chosen_building,
                           chosen_specialization=chosen_specialization, chosen_doc=chosen_doc, step=4)


@app.route("/appointment/finish/<int:chosen_building>/<int:chosen_specialization>/<int:chosen_doc>/<int:chosen_interval>")
def finish_appointment(chosen_building, chosen_specialization, chosen_doc, chosen_interval):
    global REGISTER_STEPS
    REGISTER_STEPS = REGISTER_STEPS[:3] + [REGISTER_STEPS[3][chosen_interval]]
    return render_template("appointment_finish.html", chosen_building=REGISTER_STEPS[0],
                           chosen_specialization=REGISTER_STEPS[1], chosen_doc=REGISTER_STEPS[2],
                           chosen_interval=REGISTER_STEPS[3])
"""


@app.route("/check_note/<int:note_id>", methods=["GET", "POST"])
def check_note(note_id):
    notes = TALONS["data"]
    for note in notes:
        if note["id"] == note_id and note["patient_id"] == current_user.med_card_id:
            patient = PATIENT
            doctor = DOCTOR
            return render_template("check_note.html", note=note, patient=patient, doc=doctor)
    print("Не нашлось талона")
    return redirect("/")


@app.route("/self_page", methods=["GET", "POST"])
def self_page():
    if not current_user.is_authenticated:
        return redirect("/")
    self_id = current_user.id
    # patient = archimed_response(current_user.med_card_id)
    patient = PATIENT
    notes = list(filter(lambda note: note["patient_id"] == patient["id"], TALONS["data"]))
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
        elif text != "":
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
