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
    # survive file locks (orphan tail.exe etc): retry, then fallback file
    for ($i = 0; $i -lt 3; $i++) {
        try { Add-Content -Path $log -Value $line -Encoding utf8 -ErrorAction Stop; return }
        catch { Start-Sleep -Milliseconds 300 }
    }
    try { Add-Content -Path "$proj\logs\run-fallback.log" -Value $line -Encoding utf8 -ErrorAction Stop } catch {}
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
    try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}  # avoid mojibake when capturing python output
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
    $pipeExit = $LASTEXITCODE
    try { Add-Content -Path $log -Value $out -Encoding utf8 -ErrorAction Stop }
    catch { try { Add-Content -Path "$proj\logs\run-fallback.log" -Value $out -Encoding utf8 } catch {} }
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
    # NOTE: under Task Scheduler, env-var based paths resolved wrong (APPDATA mystery).
    # Use hardcoded literal paths, try multiple strategies, log environment for diagnosis.
    Log ("env check: local-js=" + (Test-Path "C:\Users\User\Desktop\ai-tech-times\tools\firebase-tools\lib\bin\firebase.js") + " npm-js=" + (Test-Path "C:\Users\User\AppData\Roaming\npm\node_modules\firebase-tools\lib\bin\firebase.js") + " cfg=" + (Test-Path "C:\Users\User\.config\configstore\firebase-tools.json"))
    $fbArgs = @("deploy", "--only", "hosting", "--project", "ai-tech-times", "--non-interactive")
    $strategies = @(
        @{n="node-local"; exe="C:\Program Files\nodejs\node.exe"; pre=@("C:\Users\User\Desktop\ai-tech-times\tools\firebase-tools\lib\bin\firebase.js")},
        @{n="node-direct"; exe="C:\Program Files\nodejs\node.exe"; pre=@("C:\Users\User\AppData\Roaming\npm\node_modules\firebase-tools\lib\bin\firebase.js")},
        @{n="firebase-cmd"; exe="C:\Users\User\AppData\Roaming\npm\firebase.cmd"; pre=@()},
        @{n="cmd-shell"; exe="C:\Windows\System32\cmd.exe"; pre=@("/c", "C:\Users\User\AppData\Roaming\npm\firebase.cmd")}
    )
    $dep = ""
    $depExit = 1
    foreach ($s in $strategies) {
        if (($s.pre.Count -eq 0 -or $s.n -eq "cmd-shell") -and -not (Test-Path $s.exe)) { Log ("deploy skip " + $s.n + ": exe missing"); continue }
        try {
            $dep = & $s.exe ($s.pre + $fbArgs) 2>&1 | Out-String
            $depExit = $LASTEXITCODE
        } catch {
            $dep = $s.n + " threw: " + $_.Exception.Message
            $depExit = 1
        }
        Log ("deploy try " + $s.n + " -> exit " + $depExit)
        if ($depExit -eq 0) { break }
    }
    try { $dep | Out-File "$proj\logs\deploy-last.log" -Encoding utf8 } catch {}  # always keep for diagnosis
    if ($depExit -ne 0) {
        Log "deploy FAILED (exit $depExit) - see logs/deploy-last.log"
        exit 1
    }
    Log "deploy OK"
    Log "=== edition end ==="
} finally {
    Remove-Item -Path $lock -ErrorAction SilentlyContinue
}
