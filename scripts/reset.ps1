#Requires -Version 5.1
<#
.SYNOPSIS
    Stops containers and deletes all application data (volumes).
.DESCRIPTION
    Deletes the database, uploaded files and users. Does NOT touch .env
    or the source code. Asks for confirmation unless -Yes is passed.
#>
[CmdletBinding()]
param(
    [Alias('y')]
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $projectRoot 'docker-compose.yml'))) {
    if (Test-Path (Join-Path $PSScriptRoot 'docker-compose.yml')) {
        $projectRoot = $PSScriptRoot
    } else {
        Write-Host "ERROR: docker-compose.yml not found next to scripts\." -ForegroundColor Red
        exit 1
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "       Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}
$null = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

if (-not $Yes) {
    Write-Host "WARNING: this will delete ALL application data:" -ForegroundColor Yellow
    Write-Host "  - PostgreSQL database (all users, records, settings)"
    Write-Host "  - uploaded files"
    Write-Host ""
    Write-Host "The .env file and the application code will NOT be touched."
    Write-Host ""
    $answer = Read-Host "Continue? [y/N]"
    if ($answer -notmatch '^(?i)y(es)?$') {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

Push-Location $projectRoot
try {
    Write-Host "Removing containers and volumes..." -ForegroundColor Yellow
    & docker compose down -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: docker compose down -v failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: all data reset." -ForegroundColor Green
    Write-Host "    Run scripts\run.ps1 to start with a clean database." -ForegroundColor Green
} finally {
    Pop-Location
}
