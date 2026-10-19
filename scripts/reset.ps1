#Requires -Version 5.1
<#
.SYNOPSIS
    Stops containers and deletes all application data (volumes).
.DESCRIPTION
    Deletes the database, uploaded files and users. Does NOT touch .env
    or the source code. Asks for confirmation unless -Yes is passed.
.PARAMETER Yes
    Skip the confirmation prompt.
#>
[CmdletBinding()]
param(
    [Alias('y')]
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

function Invoke-NativeQuiet {
    param([scriptblock]$Command)
    $prev = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $null = & $Command 2>&1
        if ($null -eq $LASTEXITCODE) { return 1 }
        return $LASTEXITCODE
    } catch {
        return 1
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Invoke-NativeCapture {
    param([scriptblock]$Command)
    $prev = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Command
    } catch {
    } finally {
        $ErrorActionPreference = $prev
    }
}

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $projectRoot 'docker-compose.yml'))) {
    if (Test-Path (Join-Path $PSScriptRoot 'docker-compose.yml')) {
        $projectRoot = $PSScriptRoot
    } else {
        Write-Host "ERROR: docker-compose.yml not found next to scripts\." -ForegroundColor Red
        exit 1
    }
}

if (-not (Get-Command docker -CommandType Application -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "       Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

$isWindowsHost = ($PSVersionTable.PSEdition -eq 'Desktop') -or $IsWindows
if ($isWindowsHost -and -not (Test-Path '\\.\pipe\docker_engine')) {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

if ((Invoke-NativeQuiet { docker info }) -ne 0) {
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

    # Call docker directly so it keeps a real console handle. Piping
    # through a function breaks the TTY and produces plain output
    # instead of Compose progress. Do not trust $LASTEXITCODE alone:
    # Compose returns non-zero on some Docker Desktop builds for the
    # non-fatal control server error even when the operation succeeded.
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & docker compose down -v
    } catch {
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    # Defensive: if down reported non-zero, verify no containers remain.
    # If none do, the reset actually worked and we should not fail.
    $left = Invoke-NativeCapture { docker compose ps -q 2>$null } | Where-Object { $_ }
    if ($left) {
        Write-Host "ERROR: docker compose down -v failed; containers are still present." -ForegroundColor Red
        exit 1
    }

    Write-Host "OK: all data reset." -ForegroundColor Green
    Write-Host "    Run scripts\run.ps1 to start with a clean database." -ForegroundColor Green
} finally {
    Pop-Location
}
