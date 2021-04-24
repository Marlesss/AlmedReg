import time
import jwt as pyjwt
import requests
import datetime as dt
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
today = str(dt.datetime.today()).split()[0].split("-")[::-1]
TODAY = ".".join(today)
month = dt.date(day=int(today[0]), month=int(today[1]), year=int(today[2])) + dt.timedelta(days=30)
NEXT_MONTH = ".".join(str(month).split()[0].split("-")[::-1])
week = dt.date(day=int(today[0]), month=int(today[1]), year=int(today[2])) + dt.timedelta(days=6)
NEXT_WEEK = ".".join(str(week).split()[0].split("-")[::-1])
time_is = ":".join(str(dt.datetime.now()).split()[1].split(":")[:2])


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

