import requests
import json
import datetime

def gen_payload(date, origin, avg_speed, max_wind_gust): 
    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%SZ')
    return [{
        "id": "urn:ngsi-ld:Impetus:windSensor:Manresa",
        "type": "WindSensor",
        "observed_at": {
            "type": "Property",
            "value": date,
            "observedAt": date,
        },      
        "origin": {
            "type": "Property",
            "value": origin,
            "observedAt": date,
        },
        "avg_speed":{
            "type": "Property",
            "value": avg_speed*1.0,
            "observedAt": date,
        },
        "max_wind_gust": {
            "type": "Property",
            "value": max_wind_gust*1.0,
            "observedAt": date,
        }        
        ,"@context": ["https://data-manager.climate-impetus.eu/schemas/WindSensor/schema.jsonld"]
    }]

def send_data(data):
    url_local = 'http://impetus-orion:1026/ngsi-ld/v1/entityOperations/upsert'
    url_remote = 'https://data-manager.climate-impetus.eu/broker/ngsi-ld/v1/entityOperations/upsert'
    response = requests.post(url=url_remote, headers={"content-type": "application/ld+json"},data=json.dumps(data))
    print(response.status_code)


if __name__ == '__main__':
    date = '1970-01-01T00:00:00'
    origin = "PROCESED" #"DEVICE"
    avg_speed = 0.0
    max_wind_gust = 0.0
    data = gen_payload(date, origin, avg_speed, max_wind_gust)
    send_data(data)
    