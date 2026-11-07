# Wächter für den Transkriptionslauf: wartet auf einen laufenden Prozess (optional PID als Argument) und startet
# transcribe_local.py so lange neu, bis es mit Exit-Code 0 („fertig: keine offenen Folgen mehr“) endet.
# Aufruf auf Alex' PC:  powershell -File scripts\transcribe_watch.ps1 [PID]
param([int]$WaitPid = 0)
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
if ($WaitPid -gt 0) { while (Get-Process -Id $WaitPid -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 30 } }
for ($i = 0; $i -lt 40; $i++) {
    Add-Content -Path "data\transcripts\progress.log" -Value ("{0} Wächter: Lauf {1} gestartet" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), ($i + 1))
    & python -u scripts\transcribe_local.py *>> "data\transcripts\run.out"
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 20
}
Add-Content -Path "data\transcripts\progress.log" -Value ("{0} Wächter: beendet (Exit {1})" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $LASTEXITCODE)
