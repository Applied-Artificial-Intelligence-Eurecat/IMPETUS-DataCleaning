import requests

url = "https://data-manager.climate-impetus.eu/historical/v2/entities?type=MeasurementStation"
headers = {"Fiware-Service": "Testing"}
response = requests.get(url=url, headers=headers)
print(response.json())