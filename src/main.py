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
    # Spectre protection
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    # Prevent caching
    cache_control_header = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Cache-Control"] = cache_control_header
    response.headers["Server"] = "unknown"
    return response


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # nosec B104
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host=host, port=port, debug=debug)
