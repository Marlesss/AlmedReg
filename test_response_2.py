import requests
import base64
import json
import time
import jwt

api_id = '1e02efa605f4745744d7281ae1af28a0'
api_secret = "f2a08627c8a550488f309bce75089a39"


payload = base64.b64encode(bytes(json.dumps({"iss": f"{api_id}",
                                             "exp": time.time() + 3600}), "utf-8"))
JWT = jwt.encode({"some": str(payload)[2:-1]}, api_secret, algorithm="HS256")
url = "https://newapi.archimed-soft.ru/api/v4/talonstatuses"
header = {"Authorization": "Bearer " + JWT}
response = requests.get(url, headers=header)
print(response)
