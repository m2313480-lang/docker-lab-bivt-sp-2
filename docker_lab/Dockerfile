FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py app.py

ENV SERVER_PORT=8080

EXPOSE 8080

ENTRYPOINT ["python", "app.py"]
