import os
import time
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, Response, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

load_dotenv()

app = Flask(__name__)

# Metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)


def measure_metrics(endpoint):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            response = f(*args, **kwargs)
            duration = time.time() - start_time

            status = 200
            if isinstance(response, tuple):
                status = response[1]

            request_duration.labels(method=request.method, endpoint=endpoint).observe(
                duration
            )
            request_count.labels(
                method=request.method, endpoint=endpoint, status=status
            ).inc()
            return response

        return wrapper

    return decorator


@app.route("/")
@measure_metrics(endpoint="/")
def home():
    time.sleep(0.01)
    return {"message": "order-flow microservice is running"}


@app.route("/health")
@measure_metrics(endpoint="/health")
def health():
    time.sleep(0.01)
    return {"status": "healthy"}, 200


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


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
