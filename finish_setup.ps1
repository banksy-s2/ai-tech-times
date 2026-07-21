# AI TECH TIMES 仕上げスクリプト: Secrets一括登録 + テスト実行
# デスクトップの「ニュースサイト仕上げ(ダブルクリック).bat」から呼ばれる
$ErrorActionPreference = "Continue"
$repo = "banksy-s2/ai-tech-times"

Write-Host "=== [1/4] Gemini / YouTube キーを登録 ==="
$g = (Select-String "$env:USERPROFILE\Desktop\explainer-studio\.env" -Pattern '^GEMINI_API_KEY=').Line.Split('=', 2)[1]
$y = (Select-String "$env:USERPROFILE\Desktop\youtube-ai-studio\.env" -Pattern '^YOUTUBE_API_KEY=').Line.Split('=', 2)[1]
gh secret set GEMINI_API_KEY --repo $repo --body $g
gh secret set YOUTUBE_API_KEY --repo $repo --body $y

Write-Host "=== [2/4] X(おっちゃん垢)のトークン4つを登録 ==="
$e = "$env:USERPROFILE\Desktop\_Projects\kane-kizuki-bot\.env"
foreach ($k in 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET') {
    $v = (Select-String $e -Pattern ('^' + $k + '=')).Line.Split('=', 2)[1]
    gh secret set $k --repo $repo --body $v
}

Write-Host "=== [3/4] Firebaseデプロイ用トークンを登録 ==="
$cfg = "$env:APPDATA\configstore\firebase-tools.json"
$ft = $null
if (Test-Path $cfg) {
    $j = Get-Content $cfg -Raw | ConvertFrom-Json
    if ($j.tokens -and $j.tokens.refresh_token) { $ft = $j.tokens.refresh_token }
}
if (-not $ft) {
    Write-Host "ローカルトークンが見つからないため、ブラウザでGoogleの許可画面を開きます。「許可」を押してください。"
    $out = firebase login:ci 2>&1 | Out-String
    $m = [regex]::Match($out, '1//[0-9A-Za-z_\-]+')
    if ($m.Success) { $ft = $m.Value }
}
if ($ft) {
    gh secret set FIREBASE_TOKEN --repo $repo --body $ft
    Write-Host "FIREBASE_TOKEN 登録OK"
} else {
    Write-Host "!! Firebaseトークンが取得できませんでした(サイト更新はClaude側で対応可能なので一旦OK)"
}

Write-Host "=== [4/4] テスト実行を開始 ==="
gh workflow run daily-news --repo $repo
Write-Host ""
Write-Host "=== 完了！5分後くらいに https://ai-tech-times.web.app/ を見てください ==="
Write-Host "実行状況: https://github.com/banksy-s2/ai-tech-times/actions"
