FROM python:3.11-slim

WORKDIR /app

RUN pip install flask

COPY app.py .

RUN mkdir -p /logs

CMD ["python", "app.py"]
