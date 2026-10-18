$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$entry=Join-Path $root 'server.mjs'
$processes=Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='cloudflared-update.exe' OR Name='pwsh.exe'"
if(-not ($processes | Where-Object {$_.Name -eq 'node.exe' -and $_.CommandLine -like ('*"'+$entry+'"*')})){Start-Process 'C:\Program Files\nodejs\node.exe' -ArgumentList ('"'+$entry+'"') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'server.log') -RedirectStandardError (Join-Path $root 'error.log')}
$relay=Join-Path $root 'tunnel-relay.ps1'
if(-not ($processes | Where-Object {$_.Name -eq 'pwsh.exe' -and $_.CommandLine -like ('*-File*'+$relay+'*') -and $_.CommandLine -notmatch '\s-Command\s'})){Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList @('-NoProfile','-File',('"'+$relay+'"')) -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'relay.log') -RedirectStandardError (Join-Path $root 'relay-error.log')}
$config=Join-Path $root 'ai-tunnel.yml'
if(-not ($processes | Where-Object {$_.Name -eq 'cloudflared-update.exe' -and $_.CommandLine -like ('*'+$config+'*')})){Start-Process -FilePath 'H:\shichangdiaoyan\sites\reading-preferences\.local-tunnel-runtime\cloudflared-update.exe' -ArgumentList @('--config',('"'+$config+'"'),'tunnel','--edge','127.0.0.1:17845','run') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'tunnel.log') -RedirectStandardError (Join-Path $root 'tunnel-error.log')}
