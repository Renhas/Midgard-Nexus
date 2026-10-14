# Thin wrapper around `docker compose exec web manage.py`.
# Usage: .\scripts\manage.ps1 seed_demo --clear
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

docker compose exec -u django web python src/manage.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
