# Prometheus Hands-on

This folder gives you a hands-on Prometheus setup with:
- Prometheus (UI: http://localhost:9090)
- Node Exporter (metrics: http://localhost:9100/metrics)
- A small Flask app exposing metrics: http://localhost:5000/metrics

It includes all three common installation methods.

## Method 1: Binary install (Linux)
Download + run Prometheus:

```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64
./prometheus --config.file=prometheus.yml
```

Download + run Node Exporter:

```bash
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.0.linux-amd64.tar.gz
cd node_exporter-1.6.0.linux-amd64
./node_exporter
```

Use [prometheus/prometheus.local.yml](prometheus/prometheus.local.yml) as a starter config when everything runs on the same machine.

## Method 2: Docker (recommended for this repo)
### Prereqs
- Docker Desktop (with `docker compose` available)

### Run
From this folder:

```bash
docker compose up --build -d
```

Open:
- Prometheus UI: http://localhost:9090
- Targets page: http://localhost:9090/targets

Generate some traffic:

```powershell
1..20 | ForEach-Object { Invoke-RestMethod http://localhost:5000/api/hello | Out-Null }
```

Stop:

```bash
docker compose down
```

Notes:
- Prometheus scrapes other containers using compose service names (`prometheus`, `node-exporter`, `flask-app`) via [prometheus/prometheus.yml](prometheus/prometheus.yml).
- On Windows Docker Desktop, the `node-exporter` container reports container-level metrics (not full host metrics). On Linux, you can bind-mount host paths and use `pid: host` if you want true host metrics.

## Method 3: Kubernetes (Helm)
Install the community chart:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus
```

To scrape your own apps in Kubernetes, you typically add `ServiceMonitor` resources (Prometheus Operator) or configure extra scrape configs depending on the chart you choose.

## Useful PromQL queries
- Request counter: `app_requests_total`
- Rate (per second): `rate(app_requests_total[1m])`
- P95-ish latency: `histogram_quantile(0.95, sum by (le) (rate(app_request_duration_seconds_bucket[5m])))`
