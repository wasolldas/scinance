# ========================================================================
# uninstall_recorder_autostart.ps1 - Entfernt den Autostart-Task.
#
# Effekt: Recorder startet bei Anmeldung nicht mehr automatisch. Ein laufender
# Recorder-Prozess (wenn vorhanden) wird NICHT beendet - das musst du extra
# tun (Ctrl+C im Recorder-Fenster oder taskkill /F /IM python.exe vorsichtig).
#
# Aufruf:
#   powershell -ExecutionPolicy Bypass -File .\uninstall_recorder_autostart.ps1
# ========================================================================

$ErrorActionPreference = "Stop"
$taskName = "Scinance C-36 Recorder"

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -eq $existing) {
    Write-Host "Task '$taskName' existiert nicht - nichts zu tun." -ForegroundColor Yellow
    exit 0
}

Write-Host "Entferne Task '$taskName'..." -ForegroundColor Cyan
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
Write-Host "OK entfernt." -ForegroundColor Green
Write-Host ""
Write-Host "Hinweis: ein bereits laufender Recorder-Prozess wurde NICHT beendet." -ForegroundColor Yellow
Write-Host "Pruefen mit:  Get-Process python | Where-Object {`$_.CommandLine -like '*bybit_edge.recorder*'}"
