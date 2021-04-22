import time
import jwt as pyjwt
import requests

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


# print(get_response("intervals", params=["date_from=01.08.2020", "date_to=31.12.2021"]))
