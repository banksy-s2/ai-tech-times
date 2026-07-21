# Register the 4x daily schedule for AI TECH TIMES (runs on this PC)
# ASCII only (PS5.1 reads ps1 as ANSI without BOM).
$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$env:USERPROFILE\Desktop\ai-tech-times\run_edition.ps1`""
$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At 07:00),
    (New-ScheduledTaskTrigger -Daily -At 12:30),
    (New-ScheduledTaskTrigger -Daily -At 17:30),
    (New-ScheduledTaskTrigger -Daily -At 21:30)
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "AI-Tech-Times-Edition" -Action $action -Trigger $triggers -Settings $settings `
    -Description "AI TECH TIMES news site: generate articles and deploy 4x daily" -Force | Out-Null

$state = (Get-ScheduledTask -TaskName "AI-Tech-Times-Edition").State
Write-Host ""
Write-Host "=== SUCCESS! Schedule registered (state: $state) ==="
Write-Host "The news site now updates automatically at 7:00 / 12:30 / 17:30 / 21:30."
