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

# --- log rotation (keep it small) ---
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 2MB)) {
    Move-Item -Force $log "$proj\logs\run.old.log"
}

# --- mutex: skip if another edition is running (stale lock >25min is ignored) ---
$lock = "$proj\logs\edition.lock"
if (Test-Path $lock) {
    $age = (Get-Date) - (Get-Item $lock).LastWriteTime
    if ($age.TotalMinutes -lt 25) {
        Log "SKIP: another edition is running (lock age $([int]$age.TotalMinutes)min)"
        exit 0
    }
}
Set-Content -Path $lock -Value $PID -Encoding utf8

try {
    Log "=== edition start ==="

    # --- env keys (read fresh from local files, verify non-empty) ---
    function ReadKey($file, $name) {
        if (-not (Test-Path $file)) { Log "KEY FAILED: $file not found"; return $null }
        $m = Select-String $file -Pattern ('^' + $name + '=')
        if (-not $m) { Log "KEY FAILED: $name not in $file"; return $null }
        $v = $m.Line.Split('=', 2)[1].Trim()
        if (-not $v) { Log "KEY FAILED: $name is empty" }
        return $v
    }
    $env:GEMINI_API_KEY = ReadKey "$env:USERPROFILE\Desktop\explainer-studio\.env" "GEMINI_API_KEY"
    $env:YOUTUBE_API_KEY = ReadKey "$env:USERPROFILE\Desktop\youtube-ai-studio\.env" "YOUTUBE_API_KEY"
    if ($NoPost) {
        # guarantee no posting even if parent process had X env vars
        foreach ($k in 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET') {
            Remove-Item -Path ("env:" + $k) -ErrorAction SilentlyContinue
        }
    } else {
        $e = "$env:USERPROFILE\Desktop\_Projects\kane-kizuki-bot\.env"
        foreach ($k in 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET') {
            $v = ReadKey $e $k
            if ($v) { Set-Item -Path ("env:" + $k) -Value $v }
        }
    }
    if (-not $env:GEMINI_API_KEY) {
        Log "ABORT: GEMINI_API_KEY missing - pipeline cannot run"
        exit 1
    }
    $env:PYTHONIOENCODING = "utf-8"

    # --- pipeline ---
    $out = & "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe" "$proj\run_pipeline.py" 2>&1 | Out-String
    Add-Content -Path $log -Value $out -Encoding utf8
    $pipeExit = $LASTEXITCODE
    if ($pipeExit -ne 0) {
        Log "pipeline FAILED (exit $pipeExit) - skip deploy"
        exit 1
    }

    # --- push (best effort, but log real result) ---
    git add data docs company 2>&1 | Out-Null
    git commit -m ("edition: " + (Get-Date -Format "yyyy-MM-dd HH:mm")) 2>&1 | Out-Null
    $null = git push 2>&1
    if ($LASTEXITCODE -eq 0) { Log "git push OK" } else { Log "git push FAILED (exit $LASTEXITCODE) - continuing" }

    # --- deploy (must succeed, otherwise articles are invisible) ---
    $dep = & "$env:APPDATA\npm\firebase.cmd" deploy --only hosting --project ai-tech-times --non-interactive 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Add-Content -Path $log -Value $dep -Encoding utf8
        Log "deploy FAILED (exit $LASTEXITCODE)"
        exit 1
    }
    Log "deploy OK"
    Log "=== edition end ==="
} finally {
    Remove-Item -Path $lock -ErrorAction SilentlyContinue
}
