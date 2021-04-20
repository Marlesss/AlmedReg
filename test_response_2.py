import requests
import base64
import json
import time
import jwt
from pprint import pprint

api_id = '1e02efa605f4745744d7281ae1af28a0'
api_secret = "f2a08627c8a550488f309bce75089a39"

JWT = jwt.encode({"iss": api_id, "exp": time.time() + 3600}, api_secret, algorithm="HS256")
url = "https://newapi.archimed-soft.ru/api/v4/specializations"
header = {"Authorization": "Bearer " + JWT}
response = requests.get(url, headers=header)
pprint(response.json())
