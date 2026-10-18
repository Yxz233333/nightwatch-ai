$ErrorActionPreference='Stop'
$healthy=Invoke-RestMethod http://127.0.0.1:8791/api/health -NoProxy -TimeoutSec 3
if(-not $healthy.ok){throw 'AI本机服务未响应，不自动重启数据库。'}
$config=Join-Path $PSScriptRoot 'ai-tunnel.yml';$relay=Join-Path $PSScriptRoot 'tunnel-relay.ps1'
Get-CimInstance Win32_Process -Filter "Name='cloudflared-update.exe' OR Name='pwsh.exe'" | Where-Object {($_.Name -eq 'cloudflared-update.exe' -and $_.CommandLine -like ('*'+$config+'*')) -or ($_.Name -eq 'pwsh.exe' -and $_.CommandLine -notmatch '\s-Command\s' -and $_.CommandLine -like ('*-File*'+$relay+'*'))} | ForEach-Object {Stop-Process -Id $_.ProcessId}
& (Join-Path $PSScriptRoot 'start-local.ps1')
