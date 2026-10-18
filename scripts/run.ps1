#Requires -Version 5.1
<#
.SYNOPSIS
    Starts the application stack and prints the URL.
.DESCRIPTION
    Checks Docker, creates .env if missing, validates the secret key,
    runs docker compose up -d, waits for containers to reach the running
    state, optionally seeds demo data, and prints the URL. Non-interactive
    by default when -NonInteractive is set (defaults: seed=yes, browser=no).
.PARAMETER Seed
    Load demo data after startup. Skips the prompt.
.PARAMETER NoSeed
    Do not load demo data. Skips the prompt.
.PARAMETER NoBrowser
    Do not open the browser automatically.
.PARAMETER NonInteractive
    Do not prompt at all. Implies -Seed unless -NoSeed is also set,
    and does not open the browser.
.PARAMETER Rebuild
    Pass --build to docker compose up (useful after updating the code).
#>
[CmdletBinding()]
param(
    [switch]$Seed,
    [switch]$NoSeed,
    [switch]$NoBrowser,
    [switch]$NonInteractive,
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'

# --- Native helpers -------------------------------------------------------
# Under $ErrorActionPreference = 'Stop', stderr from a native command can
# become a terminating NativeCommandError. These helpers run the command
# with Continue for the duration and return only a scalar, so callers can
# use `-eq 0` / `-ne 0` without array-vs-scalar surprises.

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

# --- Locate project root ---------------------------------------------------
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $projectRoot 'docker-compose.yml'))) {
    if (Test-Path (Join-Path $PSScriptRoot 'docker-compose.yml')) {
        $projectRoot = $PSScriptRoot
    } else {
        Write-Host "ERROR: docker-compose.yml not found next to scripts\." -ForegroundColor Red
        exit 1
    }
}

# --- Docker sanity ---------------------------------------------------------
if (-not (Get-Command docker -CommandType Application -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "       Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Fast path on Windows: the named pipe is absent when the daemon is down.
$isWindowsHost = ($PSVersionTable.PSEdition -eq 'Desktop') -or $IsWindows
if ($isWindowsHost -and -not (Test-Path '\\.\pipe\docker_engine')) {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

if ((Invoke-NativeQuiet { docker info }) -ne 0) {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# --- Ensure .env exists ----------------------------------------------------
$envFile = Join-Path $projectRoot '.env'
if (-not (Test-Path $envFile)) {
    Write-Host "No .env found, generating one..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot 'init-env.ps1')
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: failed to create .env." -ForegroundColor Red
        exit 1
    }
}

# --- Validate .env ---------------------------------------------------------
$envContent = Get-Content $envFile -Raw
if ($envContent -match '(?m)^\s*DJANGO_SECRET_KEY\s*=\s*your-secret') {
    Write-Host "ERROR: DJANGO_SECRET_KEY still has the placeholder value in .env." -ForegroundColor Red
    Write-Host "       Delete .env and run this script again to regenerate it." -ForegroundColor Yellow
    exit 1
}
if ($envContent -match '(?m)^\s*DJANGO_SECRET_KEY\s*=\s*(\r?\n|$)') {
    Write-Host "ERROR: DJANGO_SECRET_KEY is empty in .env." -ForegroundColor Red
    Write-Host "       Delete .env and run this script again to regenerate it." -ForegroundColor Yellow
    exit 1
}

$nginxPort = '80'
if ($envContent -match '(?m)^\s*NGINX_PORT\s*=\s*(\d+)') {
    $nginxPort = $Matches[1]
}

# --- Decide whether to seed ------------------------------------------------
$doSeed = $false
if ($Seed) {
    $doSeed = $true
} elseif ($NoSeed) {
    $doSeed = $false
} elseif ($NonInteractive) {
    $doSeed = $true
    $NoBrowser = $true
} else {
    $answer = Read-Host "Load demo data? [Y/n]"
    if ([string]::IsNullOrWhiteSpace($answer) -or $answer -match '^(?i)y(es)?$') {
        $doSeed = $true
    }
}

# --- Start stack -----------------------------------------------------------
Push-Location $projectRoot
try {
    $upArgs = @('compose', 'up', '-d')
    if ($Rebuild) { $upArgs += '--build' }

        Write-Host "Starting containers..." -ForegroundColor Yellow

    # Call docker directly so it keeps a real console handle. Pipe or
    # function wrapper breaks the TTY on Windows and can emit
    # "failed to get console: The handle is invalid".
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $upCode = 1
    try {
        & docker @upArgs
        $upCode = if ($null -eq $LASTEXITCODE) { 1 } else { $LASTEXITCODE }
    } catch {
        $upCode = 1
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    # Compose can return non-zero even when containers start (control
    # server startup error on some Docker Desktop builds). Only treat
    # non-zero as a failure if no containers exist after a short settle.
    if ($upCode -ne 0) {
        Start-Sleep -Seconds 2
        $anyContainer = Invoke-NativeCapture { docker compose ps -q 2>$null } | Where-Object { $_ }
        if (-not $anyContainer) {
            Write-Host "ERROR: docker compose up failed." -ForegroundColor Red
            Write-Host "       Run 'docker compose logs' to see details." -ForegroundColor Yellow
            exit 1
        }
        Write-Host "WARNING: docker compose up returned non-zero, but containers exist; continuing." -ForegroundColor Yellow
    }

    # --- Wait for containers to be running --------------------------------
    Write-Host "Waiting for containers to start..." -ForegroundColor Yellow
    $running = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        $states = Invoke-NativeCapture { docker compose ps --format "{{.State}}" 2>$null } | Where-Object { $_ }
        if ($states -and -not ($states | Where-Object { $_ -ne 'running' })) {
            $running = $true
            break
        }
    }
    if (-not $running) {
        Write-Host "ERROR: containers did not reach running state." -ForegroundColor Red
        Write-Host "       Run 'docker compose logs' to see details." -ForegroundColor Yellow
        exit 1
    }

    # --- Wait for the superuser (created by entrypoint after migrations) --
    # The container reports "running" as soon as entrypoint.sh starts, but
    # the superuser exists only after migrations. Poll for it before
    # seeding, otherwise seed_demo aborts with
    # "Superuser 'admin' not found".
    if ($doSeed) {
        Write-Host "Waiting for the superuser to be created..." -ForegroundColor Yellow
        $superuserReady = $false
        $probe = "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)"
        for ($i = 0; $i -lt 180; $i++) {
            Start-Sleep -Seconds 1
            if ((Invoke-NativeQuiet { & docker compose exec -T web python src/manage.py shell -c $probe }) -eq 0) {
                $superuserReady = $true
                break
            }
        }
        if (-not $superuserReady) {
            Write-Host "WARNING: no superuser found after 180 seconds. Skipping demo data." -ForegroundColor Yellow
            Write-Host "         The app is running; you can seed later with:" -ForegroundColor Yellow
            Write-Host "           docker compose exec web python src/manage.py seed_demo" -ForegroundColor Yellow
            $doSeed = $false
        }
    }

    # --- Seed demo data ----------------------------------------------------
    if ($doSeed) {
        Write-Host "Loading demo data..." -ForegroundColor Yellow
        $seedCode = 1
        try {
            & docker compose exec -T web python src/manage.py seed_demo
            $seedCode = if ($null -eq $LASTEXITCODE) { 1 } else { $LASTEXITCODE }
        } catch {
            $seedCode = 1
        }
        if ($seedCode -ne 0) {
            Write-Host "WARNING: seed_demo failed. The app is still running." -ForegroundColor Yellow
            Write-Host "         Retry manually with:" -ForegroundColor Yellow
            Write-Host "           docker compose exec web python src/manage.py seed_demo" -ForegroundColor Yellow
        } else {
            Write-Host "OK: demo data loaded." -ForegroundColor Green
        }
    }

    # --- Print URL and next steps ------------------------------------------
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Application is running" -ForegroundColor Green
    Write-Host "  Open: http://localhost:$nginxPort/" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Stop:    docker compose down"
    Write-Host "  Reset:   scripts\reset.ps1"
    Write-Host "  Logs:    docker compose logs -f"
    Write-Host ""

    if (-not $NoBrowser) {
        try {
            Start-Process "http://localhost:$nginxPort/" | Out-Null
        } catch {
            Write-Host "WARNING: could not open browser automatically." -ForegroundColor Yellow
        }
    }
} finally {
    Pop-Location
}
