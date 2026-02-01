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
 - Alertmanager UI: http://localhost:9093
 - Grafana UI: http://localhost:3000 (admin/admin)

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

## Alerting: Grouping, dedup, routing
This lab includes Alertmanager with grouping + routing enabled:
- Alertmanager config: [alertmanager/alertmanager.yml](alertmanager/alertmanager.yml)
- Prometheus alert rules: [prometheus/alerts.yml](prometheus/alerts.yml)

### Grouping and deduplication
If 50 pods fail to connect to the same DB, you usually want *one* notification with context (not 50 separate pages).

In Alertmanager, grouping is controlled by the top-level `route`:
- `group_by`: labels that define “same incident” (this repo uses `alertname`, `cluster`, `service`)
- `group_wait`: wait to collect related alerts before first notification
- `group_interval`: wait before sending more alerts for an existing group
- `repeat_interval`: resend cadence for ongoing firing alerts

Alertmanager also deduplicates alerts with identical label sets.

### Test it (simulate an alert storm)
1) Watch notifications arriving (grouped) in the Flask container logs:

```bash
docker logs -f flask-app
```

2) In another terminal, send a burst of alerts (includes duplicates to show dedup):

```powershell
./send-test-alerts.ps1
```

Wait ~10–15 seconds (`group_wait`) and you should see a small number of webhook deliveries even though many alerts were posted.

If you re-run the script immediately, Alertmanager may *not* send a new notification until `group_interval`/`repeat_interval`.
To force a fresh group for a new run:

```powershell
./send-test-alerts.ps1 -RunId (Get-Date -Format yyyyMMdd-HHmmss)
```

### Routing and receivers
Routing is a tree (like triage): match labels and send to different receivers.

This lab routes:
- `severity=critical` → `pagerduty-critical` receiver
- `team=database` → `database-team` receiver

For simplicity, all receivers use a webhook pointing at the Flask app (`/alert`).

### Silences and inhibition
- **Silences**: temporary muting during planned maintenance (created in the Alertmanager UI or API).
- **Inhibition**: suppresses “symptom” alerts when a “cause” alert is firing (example included in the config).

### High availability (notes)
Alertmanager clustering uses a gossip protocol so that multiple instances share state and only one sends each notification.
For real HA, run at least 3 instances and configure Prometheus to send to all of them.

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

## Grafana: variables, data sources, links, tags
This lab includes Grafana pre-provisioned with a Prometheus data source and an example dashboard:
- Datasource provisioning: [grafana/provisioning/datasources/datasource.yml](grafana/provisioning/datasources/datasource.yml)
- Dashboard provisioning: [grafana/provisioning/dashboards/dashboards.yml](grafana/provisioning/dashboards/dashboards.yml)
- Example dashboard JSON: [grafana/dashboards/prometheus-hands-on.json](grafana/dashboards/prometheus-hands-on.json)

### Variables (dropdowns)
Variables make dashboards dynamic and reusable (one dashboard, many servers/environments).
In the example dashboard you’ll see:
- **Query variable**: `instance` (populated from Prometheus via `label_values(up, instance)`)
- **Custom variable**: `environment` (`dev,staging,prod`)
- **Constant variable**: `cluster` (hidden; set to `demo`)
- **Interval variable**: `interval` (`1m,5m,15m,1h`) for use in `rate(...[$interval])`
- **Datasource variable**: `datasource` so the same dashboard can switch Prometheus backends

Use variables in PromQL like: `node_cpu_seconds_total{instance=~"$instance"}` and in titles like: `CPU Usage - $instance ($environment)`.

### Data sources
Grafana data sources define where Grafana fetches data from.
This lab provisions Prometheus with URL `http://prometheus:9090` (server-side access).

### Links
Links guide investigation paths.
The example dashboard includes top-level links to Alertmanager and Prometheus.

### Tags
Tags help organize dashboards (team/env/tech/criticality). The example dashboard is tagged with `hands-on`, `prometheus`, `grafana`, `demo`.

### Dashboard JSON import/export
Grafana dashboards are stored as JSON (panels, queries, variables, layout).
Common workflow:
- Export (copy JSON) → store in git → import into another Grafana → map data sources

## Quiz answers (Grafana)
- Manager wants one dashboard with a dropdown for server CPU: **C. Variables**
- Variable type that fetches values from Prometheus: **C. Query variable**
- Primary role of a data source: **C. Define where Grafana fetches data from**
- Best practice for data source security: **C. Restrict sensitive data sources**
- Where dashboard links appear: **C. At the top of a dashboard**
- Common use of external links: **C. Opening incident runbooks**
- Tags statement: **C. A dashboard can have multiple tags**
- Panel definition: **B. A single visualization of data**
- Dashboard versioning advantage: **C. Ability to roll back and audit changes**
- Valid way to export dashboard JSON: **B. Copy JSON to clipboard**
- Practice that helps prevent reuse issues: **C. Maintaining JSON in version control**

## Quick quiz answers
- 3 AM receiving 500 alerts for a single issue mainly indicates: **B. Lack of alert grouping and deduplication**
- Alertmanager component responsible for suppressing alerts during maintenance: **C. Silencer**
