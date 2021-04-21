import datetime

import requests
import base64
import json
import time
import jwt
from pprint import pprint
import datetime as dt

api_id = '1e02efa605f4745744d7281ae1af28a0'
api_secret = "f2a08627c8a550488f309bce75089a39"
print(dt.date(day=1, month=2, year=2010) > dt.date(day=30, month=11, year=2010))
JWT = jwt.encode({"iss": api_id, "exp": time.time() + 3600}, api_secret, algorithm="HS256")
url = "https://newapi.archimed-soft.ru/api/v4/"
header = {"Authorization": "Bearer " + JWT}
response = requests.get(url, headers=header)
pprint(response.json())
