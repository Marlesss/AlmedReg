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
print(JWT)
url = "https://newapi.archimed-soft.ru/api/v4/accounts"
header = {"Authorization": "Bearer " + JWT}
response = requests.get(url, headers=header)
print(response)
# eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpc3MiOiAiMWUwMmVmYTYwNWY0NzQ1NzQ0ZDcyODFhZTFhZjI4YTAiLCAiZXhwIjogMTYxODI1Njk4NS4yODU4ODM0fQ==.c3acf544f4df7ec1bcdaec6c6b7d56b51b18d3f3fa009555307cf7029c5fedaa -> 1
# eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoiZXlKcGMzTWlPaUFpTVdVd01tVm1ZVFl3TldZME56UTFOelEwWkRjeU9ERmhaVEZoWmpJNFlUQWlMQ0FpWlhod0lqb2dNVFl4T0RJMU56RXpPUzR4TkRVNE5qZ3pmUT09In0.RK65h8lVukDiyU5722uuBfhMlTJ3CRfTHYmUFD_E5KI -> 2
