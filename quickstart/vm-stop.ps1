# Stop the AIOps GPU VM to save cost (~$0.80/hr while running).
# Data persists on the EBS volume; the full stack auto-restarts on next start.
# Usage:  .\vm-stop.ps1
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_config.ps1"

Write-Host "Stopping $AiopsInstanceId in $AiopsRegion ..." -ForegroundColor Cyan
aws ec2 stop-instances --instance-ids $AiopsInstanceId --region $AiopsRegion `
    --query "StoppingInstances[0].CurrentState.Name" --output text | Out-Host
Write-Host "Stop requested. (The idle-stop alarm also stops it after ~30 min of <5% CPU.)" -ForegroundColor Green
