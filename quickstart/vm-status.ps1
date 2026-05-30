# Show the VM state + (if running and creds are set) the app health.
# Usage:  .\vm-status.ps1
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_config.ps1"
if (Test-Path "$PSScriptRoot\secrets.local.ps1") { . "$PSScriptRoot\secrets.local.ps1" }

$state = aws ec2 describe-instances --instance-ids $AiopsInstanceId --region $AiopsRegion `
    --query "Reservations[0].Instances[0].State.Name" --output text
$ip = aws ec2 describe-instances --instance-ids $AiopsInstanceId --region $AiopsRegion `
    --query "Reservations[0].Instances[0].PublicIpAddress" --output text

Write-Host "Instance : $AiopsInstanceId"
Write-Host "State    : $state"
Write-Host "Public IP: $ip"

if ($state -eq "running") {
    $haveCreds = $AppUser -and $AppPass -and ($AppPass -ne "REPLACE_ME")
    if ($haveCreds) {
        Write-Host "App health:" -ForegroundColor Cyan
        curl.exe -s -u "${AppUser}:${AppPass}" "$AiopsDomain/api/v1/health" | Out-Host
        Write-Host ""
    } else {
        Write-Host "(fill secrets.local.ps1 to also print app health)" -ForegroundColor Yellow
    }
}
