FROM python:3.8-slim


WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10009

CMD ["streamlit", "run", "src/streamlit_apps/1_demo.py", "--server.port=10009", "server_address=0.0.0.0"]