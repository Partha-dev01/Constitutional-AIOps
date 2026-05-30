# Run a test layer. Usage:
#   .\test.ps1 smoke         # 1-call live health check (default)
#   .\test.ps1 live          # Playwright live e2e, headless
#   .\test.ps1 live-headed   # Playwright live e2e, watch the browser
#   .\test.ps1 backend       # pytest (mocked LLM/Neo4j, no VM needed)
#   .\test.ps1 frontend      # vitest + tsc build (no VM needed)
param(
    [ValidateSet("smoke","live","live-headed","backend","frontend")]
    [string]$Layer = "smoke"
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_config.ps1"
if (Test-Path "$PSScriptRoot\secrets.local.ps1") { . "$PSScriptRoot\secrets.local.ps1" }

$repo     = Split-Path $PSScriptRoot -Parent          # ...\constitutional-aiops
$frontend = Join-Path $repo "frontend"
$haveCreds = $AppUser -and $AppPass -and ($AppPass -ne "REPLACE_ME")

switch ($Layer) {
    "smoke" {
        if (-not $haveCreds) { throw "Set creds in secrets.local.ps1 first." }
        Write-Host "GET $AiopsDomain/api/v1/health" -ForegroundColor Cyan
        curl.exe -s -u "${AppUser}:${AppPass}" "$AiopsDomain/api/v1/health" | Out-Host
        Write-Host ""
    }
    "live" {
        if (-not $haveCreds) { throw "Set creds in secrets.local.ps1 first." }
        $env:E2E_USER = $AppUser; $env:E2E_PASS = $AppPass; $env:E2E_BASE_URL = $AiopsDomain
        Push-Location $frontend
        try { npm run test:e2e:live } finally { Pop-Location }
    }
    "live-headed" {
        if (-not $haveCreds) { throw "Set creds in secrets.local.ps1 first." }
        $env:E2E_USER = $AppUser; $env:E2E_PASS = $AppPass; $env:E2E_BASE_URL = $AiopsDomain
        Push-Location $frontend
        try { npm run test:e2e:live:headed } finally { Pop-Location }
    }
    "backend" {
        Push-Location $repo
        try { pytest tests/ -v } finally { Pop-Location }
    }
    "frontend" {
        Push-Location $frontend
        try { npm run test; npm run build } finally { Pop-Location }
    }
}
