import time
import jwt as pyjwt
import requests
from pprint import pprint

api_id = '1e02efa605f4745744d7281ae1af28a0'
api_secret = "f2a08627c8a550488f309bce75089a39"
last_jwt = 0


def get_jwt():
    global last_jwt
    JWT = pyjwt.encode({"iss": api_id, "exp": time.time() + 3600}, api_secret, algorithm="HS256")
    last_jwt = time.time() + 3600
    return JWT


jwt = get_jwt()


def get_response(method, id="", params=""):
    global jwt
    if time.time() >= last_jwt:
        jwt = get_jwt()
    url = f"https://newapi.archimed-soft.ru/api/v4/{method}/"
    header = {"Authorization": "Bearer " + jwt}
    if params != "":
        params = "&".join(params)
    response = requests.get(url + id + "?" + params, headers=header).json()
    return response


def post_response(method, data, id="", params=""):
    global jwt
    if time.time() >= last_jwt:
        jwt = get_jwt()
    url = f"https://newapi.archimed-soft.ru/api/v4/{method}"
    header = {"Authorization": "Bearer " + jwt}
    if params != "":
        params = "&".join(params)
    response = requests.post(url, data=data, headers=header).json()
    return response


def put_response(method, data, id=""):
    global jwt
    if time.time() >= last_jwt:
        jwt = get_jwt()
    url = f"https://newapi.archimed-soft.ru/api/v4/{method}/{id}"
    header = {"Authorization": "Bearer " + jwt}
    response = requests.put(url, data=data, headers=header).json()
    return response


def create_med_card(data):
    return post_response("medcards", data)


# pprint(get_response("medcards", id="14401"))

# pprint(get_response("doctors", id="20"))

# pprint(put_response("talons", id=21623, data={
#     "status_id": 4
# }))
#
# pprint(get_response("talons", id="21623", params=["withDeleted=1"]))

# pprint(get_response("medcards", id="14370"))
# for patient in get_response("medcards", params=["limit=2000"])['data']:
#     if str(patient["number"]) == "14217":
#         pprint(patient)

# pprint(post_response("talons", data_inp={
#     "doc_id": 20,
#     "begintime": "16:45",
#     "endtime": "17:00",
#     "date": "28.04.2021",
#     "last_name": "Тестовый",
#     "first_name": "Пациент",
#     "middle_name": "Тестиковский",
#     "birthdate": "23.04.2000",
#     "phone": "+79555555555"
# }))


"""
Здравствуйте, звоню по работе с апи от "Эльче".
Возникла проблема с получением расписания работы врачей 
(за 2 года не найдено ни одного расписания, хотя на компьютере в мед. центре они есть).
Создать мед. карту через Post-запрос получилось, в мед. центре она так же появилась.
Создать талон через Post-запрос не получатеся, при указании всех необходимых данных возникает ошибка
403 (Врач не указал время приема).
Подскажите, как решить проблему? 

В программе интервал приёма у врача указан 
Но по обращению к doctors/id у врачей maxtime=0
????????


Клиника, город, Эльче, как мы запрос составляем, версия приложения на пк, еще раз ошибку, описать проблему
"""

# "last_name": "Тестовый",
#     "first_name": "Пациент",
#     "middle_name": "Тестиковский",
#     "birthdate": "23.04.2000",
#     "phone": "+79555555555"
# "patient_id": 14370
# response = requests.post("https://newapi.archimed-soft.ru/api/v4/medcards", data={
#    "last_name": "Тестовый",
#    "first_name": "Пациент",
#    "middle_name": "Тестиковский",
#    "birthdate": "23.04.2000",
#    "phone": "+79555555555",
#    "phone_alt": "+79001232323",
#    "email": "email@mail.ru",
# }, headers=header)

# pprint(get_response("medcards", id="14215"))
# talons = [talon for talon in get_response("talons", params=["limit=20000"])["data"] if
#           talon['date'].endswith("2021")]
# talons.sort(key=lambda talon: talon["data"])
# pprint(talons)
# Ена М.Е. 96
# pprint(get_response("doctors", id='89'))

# latest_date, latest = None, None
# for talon in get_response("talons", params=["limit=20000"])['data']:
#     talon["dat"]
#
#         pprint(talon)

# 20704

# pprint(get_response("intervals", params=["date_from=20.04.2021", "date_to=28.04.2021"]))
