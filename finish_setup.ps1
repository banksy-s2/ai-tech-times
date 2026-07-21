# AI TECH TIMES finish script: register secrets + test run
# Called from the .bat on Desktop. ASCII only (PS5.1 reads ps1 as ANSI without BOM).
$ErrorActionPreference = "Continue"
$repo = "banksy-s2/ai-tech-times"

Write-Host "=== [1/4] GEMINI / YOUTUBE keys ==="
$g = (Select-String "$env:USERPROFILE\Desktop\explainer-studio\.env" -Pattern '^GEMINI_API_KEY=').Line.Split('=', 2)[1]
$y = (Select-String "$env:USERPROFILE\Desktop\youtube-ai-studio\.env" -Pattern '^YOUTUBE_API_KEY=').Line.Split('=', 2)[1]
gh secret set GEMINI_API_KEY --repo $repo --body $g
gh secret set YOUTUBE_API_KEY --repo $repo --body $y

Write-Host "=== [2/4] X (Twitter) tokens ==="
$e = "$env:USERPROFILE\Desktop\_Projects\kane-kizuki-bot\.env"
foreach ($k in 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET') {
    $v = (Select-String $e -Pattern ('^' + $k + '=')).Line.Split('=', 2)[1]
    gh secret set $k --repo $repo --body $v
}

Write-Host "=== [3/4] FIREBASE token ==="
$cfg = "$env:APPDATA\configstore\firebase-tools.json"
$ft = $null
if (Test-Path $cfg) {
    $j = Get-Content $cfg -Raw | ConvertFrom-Json
    if ($j.tokens -and $j.tokens.refresh_token) { $ft = $j.tokens.refresh_token }
}
if (-not $ft) {
    Write-Host "No local token. A browser window will open - please click ALLOW."
    $out = firebase login:ci 2>&1 | Out-String
    $m = [regex]::Match($out, '1//[0-9A-Za-z_\-]+')
    if ($m.Success) { $ft = $m.Value }
}
if ($ft) {
    gh secret set FIREBASE_TOKEN --repo $repo --body $ft
    Write-Host "FIREBASE_TOKEN OK"
} else {
    Write-Host "!! FIREBASE token not found (site deploy can be done by Claude, OK for now)"
}

Write-Host "=== [4/4] Start test run ==="
gh workflow run daily-news --repo $repo
Write-Host ""
Write-Host "=== KANRYO! (Done) Check the site in 5 minutes: ==="
Write-Host "    https://ai-tech-times.web.app/"
Write-Host "    https://github.com/banksy-s2/ai-tech-times/actions"
