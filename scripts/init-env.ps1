#Requires -Version 5.1
<#
.SYNOPSIS
    Creates .env from .env.example with a generated DJANGO_SECRET_KEY.
.DESCRIPTION
    Does nothing if .env already exists. To regenerate, delete .env first.
    Writes UTF-8 without BOM to avoid breaking .env parsers.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# Locate project root: parent of this script, or this script's dir if it
# contains docker-compose.yml (i.e. someone put the script in the root).
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $projectRoot 'docker-compose.yml'))) {
    if (Test-Path (Join-Path $PSScriptRoot 'docker-compose.yml')) {
        $projectRoot = $PSScriptRoot
    } else {
        Write-Host "ERROR: docker-compose.yml not found next to scripts\." -ForegroundColor Red
        exit 1
    }
}

$envFile     = Join-Path $projectRoot '.env'
$exampleFile = Join-Path $projectRoot '.env.example'

if (-not (Test-Path $exampleFile)) {
    Write-Host "ERROR: .env.example not found at $exampleFile" -ForegroundColor Red
    exit 1
}

if (Test-Path $envFile) {
    Write-Host "OK: .env already exists at $envFile" -ForegroundColor Green
    Write-Host "    Nothing to do. Delete it manually if you want to regenerate" -ForegroundColor Yellow
    Write-Host "    (this will invalidate all sessions and reset cookies)." -ForegroundColor Yellow
    exit 0
}

# Generate a cryptographically strong key, base64url alphabet
# (A-Za-z0-9-_), no + / = so it never needs quoting in .env.
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $bytes = New-Object byte[] 48
    $rng.GetBytes($bytes)
    $key = [Convert]::ToBase64String($bytes).Replace('+','-').Replace('/','_').TrimEnd('=')
} finally {
    $rng.Dispose()
}

# Read .env.example and replace only the value of DJANGO_SECRET_KEY.
# $1 captures "DJANGO_SECRET_KEY=<sep>", so indentation and spacing survive.
$content = [System.IO.File]::ReadAllText($exampleFile)
$pattern = '(?m)^(\s*DJANGO_SECRET_KEY\s*=\s*)[^\r\n]*'
if ($content -match $pattern) {
    $content = [regex]::Replace($content, $pattern, ('${1}' + $key))
} else {
    if (-not $content.EndsWith("`n")) { $content += "`n" }
    $content += "DJANGO_SECRET_KEY=$key`n"
    Write-Host "WARNING: DJANGO_SECRET_KEY line not found in .env.example, appended at the end." -ForegroundColor Yellow
}

# UTF-8 without BOM. BOM breaks some .env loaders and turns the first
# variable name into an invisible-prefixed one.
[System.IO.File]::WriteAllText($envFile, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "OK: created $envFile" -ForegroundColor Green
Write-Host "    DJANGO_SECRET_KEY generated (48 bytes, base64url)." -ForegroundColor Green
Write-Host "    It is stored in .env; keep that file private and do not commit it." -ForegroundColor Yellow
