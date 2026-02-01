import os
import time
import json
import logging
import sys

from flask import Flask, Response, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
log = logging.getLogger("alert-webhook")

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

alertmanager_notifications_total = Counter(
    "alertmanager_notifications_total",
    "Total Alertmanager webhook notifications received",
    ["receiver"],
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


@app.post("/alert")
def alert_webhook() -> Response:
    payload = request.get_json(silent=True)
    receiver = "unknown"
    if isinstance(payload, dict):
        receiver = str(payload.get("receiver", "unknown"))

    alertmanager_notifications_total.labels(receiver=receiver).inc()
    # Print a compact line for easy `docker logs -f flask-app`
    event = {
        "receiver": receiver,
        "alerts": len(payload.get("alerts", [])) if isinstance(payload, dict) else None,
        "groupLabels": payload.get("groupLabels") if isinstance(payload, dict) else None,
        "commonLabels": payload.get("commonLabels") if isinstance(payload, dict) else None,
    }
    log.info(json.dumps(event, separators=(",", ":"), default=str))
    return Response(status=200)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
