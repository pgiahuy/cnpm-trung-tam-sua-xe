import requests
from requests.auth import HTTPBasicAuth

admin_user = "admin_nc"       # user admin Nextcloud
admin_pass = "M77xC-MpCdY-reftW-6Rx5k-Npsit"  # password admin
username = "19"

url = f"https://triplehstorage.site/ocs/v1.php/cloud/users/{username}"
headers = {"OCS-APIRequest": "true"}

response = requests.delete(url, auth=HTTPBasicAuth(admin_user, admin_pass), headers=headers)

print(response.status_code)
print(response.text)
