import os
import time

from flask import Flask, Response, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

request_count = Counter(
    "app_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)

request_duration = Histogram(
    "app_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
)


@app.get("/api/hello")
def hello() -> Response:
    start = time.perf_counter()
    status_code = 200
    try:
        time.sleep(0.1)
        return jsonify({"message": "Hello World"})
    finally:
        elapsed = time.perf_counter() - start
        request_duration.labels(endpoint="/api/hello").observe(elapsed)
        request_count.labels(
            method=request.method,
            endpoint="/api/hello",
            http_status=str(status_code),
        ).inc()


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
