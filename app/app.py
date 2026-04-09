from flask import Flask, jsonify
import logging
import random
import os

app = Flask(__name__)

# Create logs directory if not exists
os.makedirs('/logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='/logs/app.log',
    format='%(asctime)s %(levelname)s GET %(url)s status=%(status)s response_time=%(response_time)sms ip=%(ip)s',
    level=logging.INFO
)

class RequestFilter(logging.Filter):
    def filter(self, record):
        return True

@app.route('/')
def index():
    response_time = random.randint(50, 300)
    status = random.choices(
        [200, 200, 200, 200, 404, 500],
        weights=[70, 70, 70, 70, 10, 5]
    )[0]
    ip = f"192.168.1.{random.randint(1, 100)}"

    extra = {'url': '/', 'status': status,
             'response_time': response_time, 'ip': ip}
    logging.info("Request", extra=extra)

    return jsonify({"status": status, "response_time": response_time}), status

@app.route('/api/data')
def data():
    response_time = random.randint(100, 400)
    status = random.choices([200, 200, 404], weights=[80, 80, 20])[0]
    ip = f"10.0.0.{random.randint(1, 50)}"

    extra = {'url': '/api/data', 'status': status,
             'response_time': response_time, 'ip': ip}
    logging.info("Request", extra=extra)

    return jsonify({"data": "ok"}), status

@app.route('/load')
def load():
    # Simulates anomaly — very high response time
    response_time = random.randint(3000, 8000)
    ip = f"10.0.0.{random.randint(1, 10)}"

    extra = {'url': '/load', 'status': 200,
             'response_time': response_time, 'ip': ip}
    logging.warning("Request", extra=extra)

    return jsonify({"warning": "high load", "response_time": response_time})

@app.route('/error')
def error():
    # Simulates anomaly — server errors
    response_time = random.randint(200, 500)
    ip = f"172.16.0.{random.randint(1, 20)}"

    extra = {'url': '/error', 'status': 500,
             'response_time': response_time, 'ip': ip}
    logging.error("Request", extra=extra)

    return jsonify({"error": "internal server error"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
