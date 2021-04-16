import requests
import base64
from hashlib import sha256
import json
import hmac
import time
import binascii
import jwt


api_id = '1e02efa605f4745744d7281ae1af28a0'
api_secret = "f2a08627c8a550488f309bce75089a39"

header = base64.b64encode(bytes(json.dumps({'alg': 'HS256', 'typ': 'JWT'}), "utf-8"))
payload = base64.b64encode(bytes(json.dumps({"iss": f"{api_id}",
                                             "exp": time.time() + 3600}), "utf-8"))
note = base64.b64encode(bytes(".", "utf-8"))
secret = binascii.unhexlify(api_secret)
sign = hmac.new(secret, header + payload, sha256)
JWT = str(header)[2:-1] + "." + str(payload)[2:-1] + "." + sign.hexdigest()
print(JWT)
url = "https://newapi.archimed-soft.ru/api/v4/medcards?fields[]=id&fields[]=last_name&filters[0][field]=phone&filters[0][value]=1"
header = {"Authorization": "Bearer" + JWT}
response = requests.get(url, headers=header)
print(response)


