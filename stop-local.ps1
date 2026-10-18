$root=$PSScriptRoot
$entry=Join-Path $root 'server.mjs';$config=Join-Path $root 'ai-tunnel.yml';$relay=Join-Path $root 'tunnel-relay.ps1'
Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='cloudflared-update.exe' OR Name='pwsh.exe'" | Where-Object {($_.Name -eq 'node.exe' -and $_.CommandLine -like ('*"'+$entry+'"*')) -or ($_.Name -eq 'cloudflared-update.exe' -and $_.CommandLine -like ('*'+$config+'*')) -or ($_.Name -eq 'pwsh.exe' -and $_.CommandLine -notmatch '\s-Command\s' -and $_.CommandLine -like ('*-File*'+$relay+'*'))} | ForEach-Object {Stop-Process -Id $_.ProcessId}
