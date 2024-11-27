from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import requests
import uvicorn
import json

# RESULT_RETURN_URL = "http://host.docker.internal:8080/results"
PUERTO_COMPONENTE = 8000

app = FastAPI()

class ScriptData(BaseModel):
    script_name: str
    args: List[str]

@app.post("/run")
async def run_script(data: ScriptData):
    script_name = data.script_name
    arguments = ' '.join(data.args)
    url = f"http://127.0.0.1:{PUERTO_COMPONENTE}/execute_script/"
    payload = {
        "script_name": script_name,
        "script_parameters": arguments
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()


    return {"message": f"Ejecutando {script_name} con argumentos: {arguments}"}


@app.post("/results", status_code=201)
async def receive_results(request: Request) -> dict:
    data = await request.json()
    if data:
        print(f"Script result: {data}")
        return {"status": "received", "data": data}
    else:
        raise HTTPException(status_code=400, detail="No data received")

if __name__ == "__main__":
    uvicorn.run("access_manager_simulation:app", host="127.0.0.1", port=8080, reload=True)



