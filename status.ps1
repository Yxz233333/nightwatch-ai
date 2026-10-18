$entry=Join-Path $PSScriptRoot 'server.mjs'
$p=@(Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object {$_.CommandLine -like ('*"'+$entry+'"*')})
$f=Get-Item (Join-Path $PSScriptRoot 'data\nightwatch.sqlite*') -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
[pscustomobject]@{serverCount=$p.Count;serverStarted=if($p.Count){$p[0].CreationDate.ToString('o')}else{''};lastDataWrite=if($f){$f.LastWriteTime.ToString('o')}else{''}} | ConvertTo-Json -Compress
