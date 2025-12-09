import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)


@app.route("/")
def home():
    return {"message": "order-flow microservice is running"}


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    response.headers["Server"] = "unknown"  # Obfuscate server info
    return response


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # nosec B104
    port = int(os.getenv("FLASK_PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host=host, port=port, debug=debug)
