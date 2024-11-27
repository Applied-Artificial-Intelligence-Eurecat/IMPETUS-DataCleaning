from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from subprocess import Popen, PIPE
import requests
import os
import subprocess
import json

app = FastAPI()

DEBUG = False
# SCRIPT_PATH = "app/procedures"
SCRIPT_PATH = "procedures"
SCRIPT_PATH_LOCAL = "procedures"


if DEBUG:
    SCRIPT_PATH = SCRIPT_PATH_LOCAL

class Comando:
    def __init__(self, script_path, args):
        self.script_path = script_path
        self.args = args

    def ejecutar(self):
        try:
            response = subprocess.run(
                ["python", self.script_path] + self.args,
                capture_output=True,
                text=True,
                check=True
            )
            return self._procesar_salida(response)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with error code {e.returncode}:\n{e.stderr}")
            raise
        except Exception as e:
            # logging.error(f"Error al ejecutar el script: {e}")
            print(f"Error al ejecutar el script: {e}")
            raise
    
    def _procesar_salida(self, response):
        try:

            print("RESULTADO\n", response.stdout)
            resultado = json.loads(response.stdout)
            return resultado
        except json.JSONDecodeError:
                # logging.warning("La salida del script no es JSON válido.")
                print("La salida del script no es JSON válido.")
                return str(response.stdout)

class Componente:
    def __init__(self, comando, url, timeout=20):
        self.comando = comando
        self.url = url
        self.timeout = timeout

    def gestionar(self):
        try:
            resultado = self.comando.ejecutar()
            return self._enviar_a_access_manager(resultado)
        except Exception as e:
            # logging.error(f"Error en la gestión: {e}")
            print(f"Error en la gestión: {e}")
            raise

    def _enviar_a_access_manager(self, resultado):
        try:
            headers = {"Content-Type": "application/json"}
            # response = requests.post(self.url, headers=headers, data=json.dumps(resultado), timeout=self.timeout)
            # return response.status_code
        except requests.exceptions.RequestException as e:
            # logging.error(f"Error al enviar los datos al Access Manager: {e}")
            print(f"Error al enviar los datos al Access Manager: {e}")
            raise

class ScriptInput(BaseModel):
    script_name: str
    script_parameters: str

@app.post("/execute_script/")
async def execute_script(input: ScriptInput):
    if not os.path.isfile(f"{SCRIPT_PATH}/{input.script_name}"):
        raise HTTPException(status_code=404, detail="Script not found")
    
    comando = Comando(f"{SCRIPT_PATH}/{input.script_name}", input.script_parameters.split(" ") )
    componente = Componente(comando, "http://127.0.0.1:8080/results")

    try:
        resultado = componente.gestionar()
        # logging.info(f"Resultado: {resultado}")
        print(f"Resultado: {resultado}")
    except Exception as e:
        # logging.error(f"Error en el programa principal: {e}")
        print(f"Error en el programa principal: {e}")