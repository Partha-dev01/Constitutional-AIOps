# Start the AIOps GPU VM and wait until the app answers on the domain.
# Usage:  .\vm-start.ps1
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_config.ps1"
if (Test-Path "$PSScriptRoot\secrets.local.ps1") { . "$PSScriptRoot\secrets.local.ps1" }

Write-Host "Starting $AiopsInstanceId in $AiopsRegion ..." -ForegroundColor Cyan
aws ec2 start-instances --instance-ids $AiopsInstanceId --region $AiopsRegion `
    --query "StartingInstances[0].CurrentState.Name" --output text | Out-Host

aws ec2 wait instance-running --instance-ids $AiopsInstanceId --region $AiopsRegion
$ip = aws ec2 describe-instances --instance-ids $AiopsInstanceId --region $AiopsRegion `
    --query "Reservations[0].Instances[0].PublicIpAddress" --output text
Write-Host "Instance running at $ip." -ForegroundColor Green
Write-Host "Waiting for the app + dual vLLM models to warm up (typically 3-5 min)..." -ForegroundColor Cyan

$haveCreds = $AppUser -and $AppPass -and ($AppPass -ne "REPLACE_ME")
$deadline  = (Get-Date).AddMinutes(8)
$code      = "000"
do {
    Start-Sleep -Seconds 15
    try {
        if ($haveCreds) {
            $code = curl.exe -s -o NUL -w "%{http_code}" -u "${AppUser}:${AppPass}" "$AiopsDomain/api/v1/health"
        } else {
            $code = curl.exe -s -o NUL -w "%{http_code}" "$AiopsDomain/api/v1/health"
        }
    } catch { $code = "000" }
    Write-Host ("  health -> {0}" -f $code)
} while ($code -ne "200" -and (Get-Date) -lt $deadline)

if ($code -eq "200") {
    Write-Host "App is UP at $AiopsDomain" -ForegroundColor Green
} else {
    Write-Host "Timed out waiting for health=200 (last: $code). The stack may still be warming;" -ForegroundColor Yellow
    Write-Host "re-check with .\vm-status.ps1 in a minute." -ForegroundColor Yellow
}
