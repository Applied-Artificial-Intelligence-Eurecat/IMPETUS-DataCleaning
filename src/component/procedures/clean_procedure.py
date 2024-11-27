# Librerías necesarias
import pandas as pd
import numpy as np
from scipy import stats
from abc import ABC, abstractmethod
import argparse
import os
from datetime import datetime
import json
import sys
import requests
import functools

def gen_payload(date, origin, avg_speed, max_wind_gust): 
    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%SZ')
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
    return response

def send_data_with_session(data, session):
    url_local = 'http://impetus-orion:1026/ngsi-ld/v1/entityOperations/upsert'
    url_remote = 'https://data-manager.climate-impetus.eu/broker/ngsi-ld/v1/entityOperations/upsert'
    response = session.post(url=url_remote, headers={"content-type": "application/ld+json"},data=json.dumps(data))
    print(response.status_code)
    return response

def parse_api_response_to_df(payload, origin):
    root = payload['urn:ngsi-ld:Impetus:windSensor:Manresa']
    column_names = [key for key in root.keys() if key not in ["date_observed", "entity_type", "origin"]]
    df = pd.DataFrame(root)
    df.date_observed = pd.to_datetime( df.date_observed, format="%Y-%m-%dT%H:%M:%S")
    df = df.set_index( "date_observed", drop=True )
    df = df[df.origin == origin ].drop(["entity_type","origin"], axis=1)
    df = df[~df.index.duplicated( keep="last") ]
    return df

def generate_read_payload(url, start_time, end_time ):
    params = {
        'start_time': start_time,
        'end_time': end_time,
        'entity_type': 'windsensor',
        'format': 'COLUMN'
    }
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    return response 

    

# Clase base para cualquier método de limpieza de datos. Recibe los datos y una máscara, aplica el algoritmo correctivo a los datos en función de la máscara.
class MaskImputatorMethod(ABC):

    @abstractmethod
    def clean(self, data, mask):
        pass

class MaskGeneratorMethod(ABC):

    @abstractmethod
    def generate_mask(self, data):
        pass

class TransformationMethod(ABC):

    @abstractmethod
    def transform(self, data):
        pass

class LogTransformation(TransformationMethod):

    def transform(self, data):
        data[data <= 0] = np.nan
        data = np.log(data)
        return data

class ZeroToMeanTransformation(TransformationMethod):

    def transform(self, data):
        mean_non_zero = data[data != 0].mean().iloc[0]
        data = data.replace(0, mean_non_zero)
        return data
# Implementación concreta para manejo de outliers
class ZScoreOutlierMask(MaskGeneratorMethod):
    
    def __init__(self, threshold=2):
        self.threshold = threshold

    def generate_mask(self, data):
        z_scores = np.abs(stats.zscore(data))
        mask = (z_scores > self.threshold)
        return mask

class LOFOutlierMask(MaskGeneratorMethod):

    # TODO: To implement 
    def __init__(self):
        pass

    def generate_mask(self, data):
        pass
        # return mask

class MeanMaskImputation(MaskImputatorMethod):
    def clean(self, data, mask):
        return  np.where(mask, data.mean(), data)

class ZeroMaskImputation(MaskImputatorMethod):
    def clean(self, data, mask):
        return  np.where(mask, 0, data)

# Clase de limpieza de datos que utiliza los métodos de limpieza definidos
class DataCleaner:

    def __init__(self, data_source_type, data_source, config):
        self.data_source_type = data_source_type
        if self.data_source_type == "csv":
            self.data_source = os.path.join(*data_source.split('/'))
        else:
            self.data_source = data_source
            self.api_info = config['api_additional_info']
        
    
    def load_data(self):
        print("DATA SOURCE", self.data_source)
        if self.data_source_type == "csv":
            self.data = self.load_data_from_csv(self.data_source)
        elif self.data_source_type == "api":
            self.data = self.load_data_from_api(self.data_source, self.api_info)
        else:
            raise ValueError(f"Tipo de fuente de datos no reconocido: {self.data_source_type}")
        if self.data is None:
            raise Exception(f"No se pudo cargar los datos, {self.data_source_type}")

    def load_data_from_csv(self, file_path):
        """Carga los datos desde un archivo CSV"""
        try:
            return pd.read_csv(file_path, index_col=0)
        except FileNotFoundError:
            print(f"No se encontró el archivo en la ruta especificada: {file_path}")
            return None

    def load_data_from_api(self, url, api_info):
        response = generate_read_payload(url, api_info['start_time'], api_info['end_time'])
        if response.status_code != 200:
            print(f"Error al obtener datos de la API: {response.status_code}")
            return None
        data = response.json()
        df = parse_api_response_to_df(data, api_info["origin"])
        return df

    def clean_data(self, cleaning_config):
        """Limpia los datos usando la configuración de limpieza proporcionada"""
        cleaning_methods = {
            "MeanMaskImputation": MeanMaskImputation,
            "ZScoreOutlierMask": ZScoreOutlierMask,
            "ZeroToMeanTransformation": ZeroToMeanTransformation,
            "ZeroMaskImputation": ZeroMaskImputation,
            "LogTransformation": LogTransformation
        }
        print(len(cleaning_config), cleaning_config.items())
        for column, list_of_joint_methods in cleaning_config.items():
            for joint_methods in list_of_joint_methods:
                if len(joint_methods) == 1:
                    self.data[column] = cleaning_methods[joint_methods[0]].clean(self.data[[column]])
                if len(joint_methods) == 2:
                    print(joint_methods)
                    mask_name, *mask_args = joint_methods[0]
                    imputation_name, *imputation_args = joint_methods[1]
                    mask = cleaning_methods[mask_name](*mask_args).generate_mask(self.data[[column]])
                    self.data[column] = cleaning_methods[imputation_name](*imputation_args).clean(self.data[[column]], mask)
                elif len(joint_methods) != 0:
                    raise ValueError("Maximum of 2 methods has been exceeded")
                


    def save_clean_data(self, output_path):
        """Guarda los datos limpios en la ruta especificada"""
        if output_path is None:
            if self.data_source_type == "csv":
                base_name, ext = os.path.splitext(self.data_source)
                output_path = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif self.data_source_type == "api":
                # output_path = f"api_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv" #TODO Save to api
                self.send_data_through_api()
                return 0
            else:
                raise ValueError(f"Tipo de fuente de datos no reconocido: {self.data_source_type}")
        self.data.to_csv(output_path, index=True)
    
    def send_data_through_api(self ):
        df_payload = self.data
        date_list = df_payload.index.strftime('%Y-%m-%d %H:%M:%S')
        max_wind_gust_list = df_payload.max_wind_gust.values
        avg_speed_list = df_payload.avg_speed.values
        payloads = [ gen_payload(date_list[i],"PROCESSED", avg_speed_list[i] ,max_wind_gust_list[i])[0] for i in range(len(date_list))]
        print(len(date_list), " dates")
        print(len(payloads),"payloads")

        with requests.Session() as session:
            for payload in payloads:
                print("sending...")
                send_data_with_session([payload], session)


# Uso de la clase
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean a dataset.')
    parser.add_argument('cleaning_config', type=str, help='Path al archivo JSON con la configuración de limpieza de datos')
    parser.add_argument('--output_path', type=str, help='Path donde se guardarán los datos limpios (opcional)')
    args = parser.parse_args()
    
    with open(args.cleaning_config, 'r') as f:
        cleaning_config = json.load(f)

    cleaner = DataCleaner(
        data_source_type=cleaning_config["data_source_type"],
        data_source=cleaning_config["data_source"],
        config = cleaning_config
    )
    cleaner.load_data()
    cleaner.clean_data(cleaning_config["methods"])
    cleaner.save_clean_data(args.output_path) # TODO: Parametritzar

    sys.exit(0)