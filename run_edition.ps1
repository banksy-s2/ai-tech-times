# AI TECH TIMES edition runner (local scheduled task version)
# Reads all keys from local .env files at run time - no secrets stored anywhere.
# ASCII only (PS5.1 reads ps1 as ANSI without BOM).
param([switch]$NoPost)

$ErrorActionPreference = "Continue"
$proj = "$env:USERPROFILE\Desktop\ai-tech-times"
$log = "$proj\logs\run.log"
New-Item -ItemType Directory -Force "$proj\logs" | Out-Null
Set-Location $proj

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $log -Value $line -Encoding utf8
}

Log "=== edition start ==="

# --- env keys (read fresh from local files) ---
$env:GEMINI_API_KEY = (Select-String "$env:USERPROFILE\Desktop\explainer-studio\.env" -Pattern '^GEMINI_API_KEY=').Line.Split('=', 2)[1]
$env:YOUTUBE_API_KEY = (Select-String "$env:USERPROFILE\Desktop\youtube-ai-studio\.env" -Pattern '^YOUTUBE_API_KEY=').Line.Split('=', 2)[1]
if (-not $NoPost) {
    $e = "$env:USERPROFILE\Desktop\_Projects\kane-kizuki-bot\.env"
    foreach ($k in 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET') {
        $v = (Select-String $e -Pattern ('^' + $k + '=')).Line.Split('=', 2)[1]
        Set-Item -Path ("env:" + $k) -Value $v
    }
}
$env:PYTHONIOENCODING = "utf-8"

# --- pipeline ---
$out = & "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe" "$proj\run_pipeline.py" 2>&1 | Out-String
Add-Content -Path $log -Value $out -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Log "pipeline FAILED (exit $LASTEXITCODE) - skip deploy"
    exit 1
}

# --- push (best effort) ---
git add data docs company 2>&1 | Out-Null
git commit -m ("edition: " + (Get-Date -Format "yyyy-MM-dd HH:mm")) 2>&1 | Out-Null
git push 2>&1 | Out-Null
Log "git push done (or skipped)"

# --- deploy ---
$dep = & "$env:APPDATA\npm\firebase.cmd" deploy --only hosting --project ai-tech-times --non-interactive 2>&1 | Out-String
Add-Content -Path $log -Value $dep -Encoding utf8
Log "=== edition end ==="
