import requests
# Optional Paremeters
# fromDate
# toDate
# limit
# offset
url = "https://data-manager.climate-impetus.eu/historical/v2/entities/urn:ngsi-ld:Impetus:measurementStation:A?fromDate=2023-06-21T09:30:00&toDate=2023-06-21T10:30:00&limit=5&offset=5"
headers = {"Fiware-Service": "Testing"}
response = requests.get(url=url, headers=headers)
print(response.json())