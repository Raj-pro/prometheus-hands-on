Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location $PSScriptRoot
try {
  docker compose up --build -d
  Write-Host "Prometheus: http://localhost:9090"
  Write-Host "Targets:    http://localhost:9090/targets"
  Write-Host "Flask app:  http://localhost:5000/api/hello"
} finally {
  Pop-Location
}
