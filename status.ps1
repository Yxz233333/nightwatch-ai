$root=$PSScriptRoot
$entry=Join-Path $root 'server.mjs';$config=Join-Path $root 'ai-tunnel.yml';$relay=Join-Path $root 'tunnel-relay.ps1'
$processes=Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='cloudflared-update.exe' OR Name='pwsh.exe'"
$p=@($processes | Where-Object {$_.Name -eq 'node.exe' -and $_.CommandLine -like ('*"'+$entry+'"*')})
$t=@($processes | Where-Object {$_.Name -eq 'cloudflared-update.exe' -and $_.CommandLine -like ('*'+$config+'*')})
$r=@($processes | Where-Object {$_.Name -eq 'pwsh.exe' -and $_.CommandLine -notmatch '\s-Command\s' -and $_.CommandLine -like ('*-File*'+$relay+'*')})
$f=Get-Item (Join-Path $root 'data\nightwatch.sqlite*') -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
[pscustomobject]@{serverCount=$p.Count;tunnelCount=$t.Count;relayCount=$r.Count;serverStarted=if($p.Count){$p[0].CreationDate.ToString('o')}else{''};lastDataWrite=if($f){$f.LastWriteTime.ToString('o')}else{''}} | ConvertTo-Json -Compress
