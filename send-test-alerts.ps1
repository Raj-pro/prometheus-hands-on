Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Sends many alerts to Alertmanager to demonstrate grouping + dedup.
# Requires the docker-compose stack to be running.

param(
  # Optional run identifier to force a fresh alert group when re-running.
  # If set, this is appended to the `service` label.
  [string]$RunId
)

$alertmanagerUrl = $env:ALERTMANAGER_URL
if (-not $alertmanagerUrl) {
  $alertmanagerUrl = 'http://localhost:9093'
}

$api = "$alertmanagerUrl/api/v2/alerts"

$now = [DateTime]::UtcNow
$startsAt = $now.ToString('o')
$endsAt = $now.AddHours(2).ToString('o')

$alerts = @()

$service = 'payments'
if ($RunId) {
  $service = "$service-$RunId"
}

# 50 distinct alerts (like 50 pods failing the same DB)
1..50 | ForEach-Object {
  $i = $_
  $alerts += @{
    labels = @{
      alertname = 'DatabaseConnectionFailed'
      severity  = 'critical'
      team      = 'database'
      cluster   = 'demo'
      service   = $service
      instance  = ("pod-{0:000}" -f $i)
    }
    annotations = @{
      summary = 'Pods failing to connect to DB'
      description = 'Synthetic alert to demonstrate grouping/dedup'
    }
    startsAt = $startsAt
    endsAt   = $endsAt
  }
}

# Add duplicates (these should be deduplicated by Alertmanager)
$alerts += $alerts

Write-Host "Posting $($alerts.Count) alerts to $api"
if ($RunId) {
  Write-Host "Using service label: $service"
} else {
  Write-Host "Tip: if you already ran this recently, Alertmanager may not notify again until group_interval/repeat_interval." 
  Write-Host "     Re-run with -RunId (Get-Date -Format yyyyMMdd-HHmmss) to force a fresh group." 
}

$body = $alerts | ConvertTo-Json -Depth 10
Invoke-RestMethod -Method Post -Uri $api -ContentType 'application/json' -Body $body | Out-Null

Write-Host "Done. Watch grouped notifications via: docker logs -f flask-app"
Write-Host "Also check Alertmanager UI: $alertmanagerUrl" 
