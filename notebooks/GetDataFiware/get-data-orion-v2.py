import requests

url = "https://data-manager.climate-impetus.eu/broker/v2/entities"
headers = {"Fiware-Service": "Testing"}
response = requests.get(url=url, headers=headers)
print(response.json())