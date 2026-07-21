# Register the HOURLY schedule for AI TECH TIMES (runs on this PC)
# Full edition at 7/12/17/21 JST (all categories + buzz + X post),
# light edition (1 rotating category) every other hour. Logic lives in run_pipeline.py.
# ASCII only (PS5.1 reads ps1 as ANSI without BOM).
$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$env:USERPROFILE\Desktop\ai-tech-times\run_edition.ps1`""
$triggers = @(0..23 | ForEach-Object { New-ScheduledTaskTrigger -Daily -At (Get-Date -Hour $_ -Minute 0 -Second 0) })
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "AI-Tech-Times-Edition" -Action $action -Trigger $triggers -Settings $settings `
    -Description "AI TECH TIMES news site: hourly edition (full at 7/12/17/21)" -Force | Out-Null

$info = Get-ScheduledTaskInfo -TaskName "AI-Tech-Times-Edition"
$state = (Get-ScheduledTask -TaskName "AI-Tech-Times-Edition").State
Write-Host ""
Write-Host "=== SUCCESS! Hourly schedule registered (state: $state) ==="
Write-Host ("Next run: " + $info.NextRunTime)
Write-Host "Full edition at 7:00 / 12:00 / 17:00 / 21:00, light edition every other hour."
