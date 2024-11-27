# (impetus_env) PS C:\Users\ian.palacin\Projectes\impetus-utils\src\streamlit_apps> streamlit run .\1_demo.py
import streamlit as st
import re
from itertools import groupby
from operator import itemgetter
import pandas as pd
from datetime import datetime
import sys
import json
import matplotlib.pyplot as plt
import procedures.clean_procedure as cp
import plotly.graph_objs as go
import requests


variable_options = ["avg_speed", "max_wind_gust"]
general_functions = ["LogTransformation", "ZeroToMeanTransformation"]  # Tus funciones generales
mask_generators = ["ZScoreOutlierMask"]  # Generadores de máscaras
mask_imputators = ["ZeroMaskImputation", "MeanMaskImputation"]  # Imputadores específicos de máscaras

def parse_variable_form_to_method(data):
    values_to_variables = {0: "variable", 1: 'function', 2: 'imputator', 3:'arg'}
    variables_to_values = {y: x for x, y in values_to_variables.items()}

    elementwise_config = [[variables_to_values[key.split("_")[0]], int(key.split("_")[1]), int(key.split("_")[2])] for key in data.keys()]
    elementwise_config.sort(key = lambda row: (row[1],row[2], row[0]))
    elementwise_config = [ "_".join([values_to_variables[x],str(y),str(z)]) for [x,y,z] in elementwise_config ]
    arg_grouped_list, i = [], 0
    while i <= len(elementwise_config)-1:
        if i + 1 < len(elementwise_config) and 'arg_' in elementwise_config[i + 1]:
            arg_grouped_list.append([elementwise_config[i], elementwise_config[i + 1]])
            i += 1
        else:
            arg_grouped_list.append([elementwise_config[i]])
        i += 1

    final_list, i = [], len(arg_grouped_list)-1
    while i >= 0:
        if 'imputator' in arg_grouped_list[i][0]:
            final_list.append([arg_grouped_list[i-1], arg_grouped_list[i]])
            i -= 1
        else:
            final_list.append([arg_grouped_list[i]])
        i -= 1
    final_list = final_list[::-1]
    column = data[final_list[0][0][0]]
    methods = [[ [data[component_of_function] for component_of_function in function_with_args] for function_with_args in list_of_functions] for list_of_functions in final_list[1:]]
    return column, methods

def form_to_methods( data ):
    sorted_data = sorted(data.items(), key=lambda x: int(x[0].split('_')[1]))
    grouped_data = {k: dict(v) for k, v in groupby(sorted_data, key=lambda x: int(x[0].split('_')[1]))}
    return {variable_column: method_list for value in grouped_data.values() for variable_column, method_list in [parse_variable_form_to_method(value)]}

def draw_rows():
    for row_idx, cols in enumerate(st.session_state.rows):
        columns = st.columns(len(cols))

        for col_idx, col_info in enumerate(cols):
            if col_idx == 0:
                # Columna de selección de variables
                label, options, key = 'Variable', variable_options, f'variable_{row_idx}_0'
            else:
                # Columna de selección de funciones/transformaciones
                # Verificamos si la columna anterior fue un generador de máscaras y si es así,
                # establecemos las opciones a los imputadores de máscaras
                if cols[col_idx - 1]['selected'] in mask_generators:
                    label, options, key = 'Imputator', mask_imputators, f'imputator_{row_idx}_{col_idx}'
                    col_info['is_imputator'] = True  # Marcamos esta columna como un imputador
                else:
                    label, options, key = 'Function', general_functions + mask_generators, f'function_{row_idx}_{col_idx}'

            selected = columns[col_idx].selectbox(label, options, key=key, index=col_info.get('index', 0))
            st.session_state.rows[row_idx][col_idx]['selected'] = selected

            if selected in mask_generators:
                # Si la selección actual es un generador de máscaras y no hay una siguiente columna o no es un imputador
                if col_idx + 1 == len(cols) or not cols[col_idx + 1].get('is_imputator', False):
                    # Añadimos una nueva columna para la imputación de máscaras con las opciones de mask_imputators
                    st.session_state.rows[row_idx].append({'index': 0, 'selected': mask_imputators[0], 'is_imputator': True})
                    st.rerun()

            elif selected in general_functions:
                # Si se selecciona una función general y hay una columna de imputador de máscaras después, la eliminamos
                while col_idx + 1 < len(cols) and cols[col_idx + 1].get('is_imputator', False):
                    st.session_state.rows[row_idx].pop(col_idx + 1)
                    st.rerun()

            # Si no es ni un generador de máscaras ni una función general, pero hay una columna adicional que no corresponde, la eliminamos
            elif selected not in mask_generators + general_functions:
                if col_idx + 1 < len(cols) and cols[col_idx + 1].get('is_imputator', False):
                    st.session_state.rows[row_idx].pop(col_idx + 1)
                    st.rerun()

            # Caso especial para máscaras que requieren una entrada adicional (como ZScoreOutlierMask)
            if selected == "ZScoreOutlierMask":
                # Supongamos que 'ZScoreOutlierMask' requiere que el usuario introduzca un valor 'z'
                if 'z_value' not in col_info:
                    col_info['z_value'] = 3  # Valor por defecto
                z_key = f'arg_{row_idx}_{col_idx}'
                z_value = columns[col_idx].number_input('z', key=z_key, value=col_info['z_value'])
                st.session_state.rows[row_idx][col_idx]['z_value'] = z_value
# Función para añadir una nueva transformación o imputador
def add_new_transformation():
    # Añade un nuevo diccionario a la última fila existente con una función general por defecto
    st.session_state.rows[-1].append({'index': 0, 'selected': mask_generators[0], 'is_transformation': True})
    st.rerun()
# Función para añadir una nueva variable
def add_new_variable():
    # Añade una nueva fila que contiene un diccionario para una nueva variable
    st.session_state.rows.append([{'index': 0, 'selected': variable_options[0], 'is_variable': True}])
    st.rerun()

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

def generate_read_payload(start_time, end_time):
    url = "https://data-manager.climate-impetus.eu/access/historical/entities"
    params = {
        'start_time': start_time,
        'end_time': end_time,
        'entity_type': 'windsensor',
        'format': 'COLUMN'
    }
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    return response # print(response.json())

def parse_api_response_to_df(payload):
    root = payload['urn:ngsi-ld:Impetus:windSensor:Manresa']
    column_names = [key for key in root.keys() if key not in ["date_observed", "entity_type", "origin"]]
    df = pd.DataFrame(root)
    df.loc[0, "avg_speed"] = 1
    df.date_observed = pd.to_datetime( df.date_observed, format="%Y-%m-%dT%H:%M:%S")
    df = df.set_index( "date_observed", drop=True )
    df = df[~df.index.duplicated( keep="last") ]
    return df

def send_data_with_session(data, session):
    url_local = 'http://impetus-orion:1026/ngsi-ld/v1/entityOperations/upsert'
    url_remote = 'https://data-manager.climate-impetus.eu/broker/ngsi-ld/v1/entityOperations/upsert'
    response = session.post(url=url_remote, headers={"content-type": "application/ld+json"},data=json.dumps(data))
    print(response.status_code)
    return response

def generate_payload_from_df(df_payload):
    date_list = df_payload.index.strftime('%Y-%m-%d %H:%M:%S')
    max_wind_gust_list = df_payload.max_wind_gust.values
    avg_speed_list = df_payload.avg_speed.values
    payloads = [ gen_payload(date_list[i],"PROCESSED", avg_speed_list[i] ,max_wind_gust_list[i])[0] for i in range(len(date_list))]
    return payloads

def send_data_through_api(payload_list):
    with requests.Session() as session:
        for payload in payload_list:
            print("sending...")
            send_data_with_session([payload], session)

def form_configuration_logic():

    st.title("Data cleaning methods")
    st.subheader("Add the transformations you want to be made to the data")
    st.write("")

    if 'rows' not in st.session_state:
        st.session_state.rows = [[{'index': 0, 'selected': variable_options[0]}]]
    draw_rows()
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Add new variable'):
            add_new_variable()
            st.rerun()
    with col2:
        if st.button('Add new transformation'):
            add_new_transformation()
            st.rerun()
    
    st.write("")
    st.write("")
    st.write("")

    if st.button('Submit transformations'):
        st.write('Methods configured correctly!')
        form_result = st.session_state.to_dict()
        del form_result["rows"]
        del form_result["current_logic"]
        st.write(form_result)
        methods = form_to_methods(form_result)
        st.session_state.methods = methods
        st.session_state.current_logic = "date_selection"  # Marcar el formulario como enviado
        st.rerun()

def date_selection_logic():
    st.title("Date selection")
    st.subheader("Select the start date and end date to implement the data cleaning.")
    st.write("")

    col_start, col_end = st.columns(2)
    with col_start:
        start_time = st.date_input("Start time", datetime.now())
    with col_end:
        end_time = st.date_input("End time", datetime.now())

    # Verificar que la fecha de inicio no es posterior a la fecha de fin
    if start_time > end_time:
        st.error("Start time cannot be after end time. Please select a valid date range.")
    else:

        st.write("")
        st.write("")
        st.write("")
        if st.button('Submit Dates'):
            # Aquí manejas la lógica de envío del segundo formulario
            # ... (procesar las fechas seleccionadas)
            st.success('Date range submitted successfully!')
            # Guardar las fechas en el estado de la sesión si es necesario
            st.session_state.start_time = start_time
            st.session_state.end_time = end_time
            st.session_state.current_logic = "data_retrieval"  # Marcar el formulario como enviado
            st.rerun()

def data_retrieval_logic():
    st.title("Configuration json")
    st.subheader("This configuration json has been generated from the previous selections.")
    st.write("")

    config_file = {
        "data_source_type": "api",
        "data_source": "https://data-manager.climate-impetus.eu/access/historical/entities",
        "api_additional_info":{
            "start_time":  "2017-01-01T00:00:00",
            "end_time": "2017-04-10T00:00:00",
            "entity_type": "windsensor",
            "format": "COLUMN",
            "origin": "DEVICE"}, 
        
        "methods": {
            # "avg_speed": [ [["ZScoreOutlierMask", 2], ["MeanMaskImputation"]] ],  
            # "max_wind_gust": [ [["ZScoreOutlierMask", 2], ["MeanMaskImputation"]] ],  
            # "max_wind_gust": [ [["ZeroToMeanTransformation"]], [["LogTransformation"]]],  
            # "avg_speed": [ [["ZeroToMeanTransformation"]], ],  
            # "max_wind_gust": [ [["ZeroToMeanTransformation"]], ],  
            "avg_speed": [ [["ZeroToMeanTransformation"]], [["ZScoreOutlierMask", 2], ["MeanMaskImputation"]] ],  
            "max_wind_gust": [ [["ZeroToMeanTransformation"]], [["ZScoreOutlierMask", 2], ["MeanMaskImputation"]] ],  
            }
    }

    st.session_state.start_time = pd.to_datetime(st.session_state.start_time).strftime('%Y-%m-%dT%H:%M:%S')
    st.session_state.end_time = pd.to_datetime(st.session_state.end_time).strftime('%Y-%m-%dT%H:%M:%S')
    
    # config_file["api_additional_info"]["start_time"] = st.session_state.start_time   # TODO
    # config_file["api_additional_info"]["end_time"] = st.session_state.end_time       # TODO
    # config_file["methods"] = st.session_state.methods                                # TODO Uncomment 3 above to un-hardcode
    st.session_state.config_file = config_file
    
    st.write(config_file)
    st.subheader("With the dates from the configuration file, we can generate a payload and retrieve the data from the API.")
    if st.button('Send payload to API'):
        st.session_state.current_logic = "raw_data_recieve_and_plot"  # Marcar el formulario como enviado
        config = st.session_state.config_file
        cleaner = cp.DataCleaner(data_source_type=config['data_source_type'], data_source=config['data_source'], config=config)
        df_pre_clean = cleaner.load_data_from_api(config['data_source'], config['api_additional_info'])
        st.session_state.data_pre_clean = df_pre_clean.copy()
        st.session_state.data = df_pre_clean
        st.rerun()
    
def send_payload_and_plot_data_logic():
    st.title("Raw dataframe")
    st.subheader("This is the data retrieved from the API.")
    st.write("")

    st.dataframe(st.session_state.data_pre_clean)  
    st.line_chart(st.session_state.data_pre_clean)

    cleaning_methods = {
        "ZScoreOutlierMask": cp.ZScoreOutlierMask,
        "ZeroMaskImputation": cp.ZeroMaskImputation,
        "MeanMaskImputation": cp.MeanMaskImputation,
        "LogTransformation": cp.LogTransformation,
        "ZeroToMeanTransformation": cp.ZeroToMeanTransformation
    }
    # cleaning_config = 
    for column, list_of_joint_methods in st.session_state.config_file["methods"].items():
        for joint_methods in list_of_joint_methods:
            with st.expander(f"**Variable**: {column}\n\n**Methods:** {', '.join([' '.join([str(e) for e in y]) for y in joint_methods ])}"):
                if len(joint_methods) == 1:
                    function_name, *function_args = joint_methods[0]
                    st.subheader(f"Function: {function_name} {' '.join([str(a) for a in function_args])}")
                    st.session_state.data[column] = cleaning_methods[function_name](*function_args).transform(st.session_state.data[[column]])
                    st.line_chart(st.session_state.data)
                elif len(joint_methods) == 2:
                    mask_name, *mask_args = joint_methods[0]
                    imputation_name, *imputation_args = joint_methods[1]
                    mask = cleaning_methods[mask_name](*mask_args).generate_mask(st.session_state.data[[column]])
                    data_masked = st.session_state.data[[column]]
                    data_masked_true = data_masked[mask[column]]
                    data_masked_false = data_masked[~mask[column]]
                    trace_false = go.Scatter( x=data_masked_false.index, y=data_masked_false[column], mode='markers', name='False', line=dict(color='blue'))
                    trace_true = go.Scatter( x=data_masked_true.index, y=data_masked_true[column], mode='markers', name='True', line=dict(color='red'))
                    # Crear la figura
                    fig = go.Figure()
                    fig.add_trace(trace_false)
                    fig.add_trace(trace_true)
                    # Mostrar el gráfico en Streamlit
                    st.subheader(f"Mask: {mask_name} {' '.join([str(a) for a in mask_args])}")
                    st.plotly_chart(fig)
                    st.subheader(f"Imputation: {imputation_name} {' '.join([str(a) for a in imputation_args])}")
                    st.session_state.data[column] = cleaning_methods[imputation_name](*imputation_args).clean(st.session_state.data[[column]], mask)
                    st.line_chart(st.session_state.data[[column]])
                elif len(joint_methods) != 0:
                    print(joint_methods)
                    raise ValueError("Maximum of 2 methods has been exceeded")

    st.title("Final dataframe")
    st.subheader("This is the dataframe after the application of every transformation you selected.")
    st.line_chart(st.session_state.data)
    st.subheader("We can now generate the payload to send back the data to the API.")
    if st.button('Generate payload'):
        st.session_state.current_logic = "generate_payload_to_send_back_data"  # Marcar el formulario como enviado
        st.rerun()

def generate_payload_to_send_back_data_logic():
    st.title("Payload to send back")
    st.subheader("This is an example of the payload that will be sent with the data now processed.")
    payload_list = generate_payload_from_df(st.session_state.data)
    st.subheader(f"There are {len(payload_list)} elements like this, as much as rows in the data.")
    st.write(payload_list[0])
    if st.button('Send payload to API'):
        st.subheader("Sending data...")
        send_data_through_api(payload_list)
        st.session_state.current_logic = "send_clean_data_back"  # Marcar el formulario como enviado
        st.rerun()


def send_clean_data_back_and_plot_new_logic():
    st.title("Data comparison")
    st.subheader("Clean data has been sent and stored.")
    st.subheader("We can now retrieve it back with the flag \"PROCESSED\" and compare it.")
    response = generate_read_payload( st.session_state.config_file["api_additional_info"]["start_time"], st.session_state.config_file["api_additional_info"]["end_time"])

    st.write(f"Retrieve data with \"PROCESSED\" flag: ")
    st.write(response)

    st.header(f"Freshly uploaded data")
    df_response = parse_api_response_to_df(response.json())
    df_response = df_response[variable_options].sort_index()
    st.dataframe(df_response)  
    st.line_chart(df_response)
    st.title(f"Column by Column comparison:")
    st.header("raw data vs \"PROCESSED\" data")
    st.write("*If a column has not been transformed within this session, the comparison will be between raw data and an already processed state stored in the database.")
    for variable in variable_options:
        processed_column_data = df_response[variable]
        raw_column_data = st.session_state.data_pre_clean[variable].copy()
        
        raw_trace = go.Scatter( x=raw_column_data.index, y=raw_column_data, mode='lines', name=f'Raw {variable}', line=dict(color='blue'))
        processed_trace = go.Scatter( x=processed_column_data.index, y=processed_column_data, mode='lines', name=f'Processed {variable}', line=dict(color='red'))
        fig = go.Figure()
        fig.update_layout(title_text=f'{variable}', title_x=0.5)
        fig.add_trace(raw_trace)
        fig.add_trace(processed_trace)
        st.plotly_chart(fig)



def main():
    if 'current_logic' not in st.session_state:
        st.session_state.current_logic = "method_configuration"  # Inicializar el estado del
        # st.session_state.current_logic = "date_selection"  # Inicializar el estado del

    if st.session_state.current_logic == "method_configuration":
        form_configuration_logic()
    elif st.session_state.current_logic == "date_selection":
        date_selection_logic()
    elif st.session_state.current_logic == "data_retrieval":
        data_retrieval_logic()
    elif st.session_state.current_logic == "raw_data_recieve_and_plot":
        send_payload_and_plot_data_logic()
    elif st.session_state.current_logic == "generate_payload_to_send_back_data":
        generate_payload_to_send_back_data_logic()
    elif st.session_state.current_logic == "send_clean_data_back":
        send_clean_data_back_and_plot_new_logic()



if __name__ == "__main__":
    main()




