# ゲートウェイ単体の確認（Claude Code を繋ぐ前に実行する）。
# 使い方: pwsh -File .\smoke-test.ps1 [-Model gpt-5-mini]
param([string]$Model = "gpt-5-mini")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .env)) { throw ".env がない。.env.example をコピーして埋める。" }
$vars = @{}
Get-Content .env | Where-Object { $_ -match '^\s*[^#\s].*=' } | ForEach-Object {
  $k, $v = $_ -split '=', 2
  $vars[$k.Trim()] = $v.Trim()
}
$port = if ($vars.ContainsKey('LITELLM_PORT')) { $vars['LITELLM_PORT'] } else { '4000' }
$base = "http://127.0.0.1:$port"
$healthTimeoutSec = 30
$messageTimeoutSec = 120
$headers = @{ Authorization = "Bearer $($vars['LITELLM_MASTER_KEY'])" }

Write-Output "== 1. liveliness =="
Invoke-RestMethod "$base/health/liveliness" -TimeoutSec $healthTimeoutSec | ConvertTo-Json -Compress

Write-Output "== 2. 公開モデル一覧（config.yaml の alias だけが出ること） =="
(Invoke-RestMethod "$base/v1/models" -Headers $headers -TimeoutSec $healthTimeoutSec).data.id

Write-Output "== 3. Messages 契約（Anthropic 形式で返ること） =="
$body = @{ model = $Model; max_tokens = 64; messages = @(@{ role = "user"; content = "reply with OK" }) } | ConvertTo-Json -Depth 5
Invoke-RestMethod "$base/v1/messages" -Method Post -Headers ($headers + @{ "anthropic-version" = "2023-06-01" }) -ContentType "application/json" -Body $body -TimeoutSec $messageTimeoutSec | ConvertTo-Json -Depth 6

Write-Output "OK: 3層とも通った。次は README.md の「Claude Code を繋ぐ」へ。"
