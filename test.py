import requests
from requests.auth import HTTPBasicAuth

admin_user = "admin_nc"
admin_pass = "KbDJ7-MF5WB-8t85q-q29fq-Rq3jA"
username = "22"

url = f"https://triplehstorage.site/ocs/v1.php/cloud/users/{username}"
headers = {"OCS-APIRequest": "true"}

response = requests.delete(url, auth=HTTPBasicAuth(admin_user, admin_pass), headers=headers)

print(response.status_code)
print(response.text)
