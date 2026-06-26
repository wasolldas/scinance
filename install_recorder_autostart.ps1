# ========================================================================
# install_recorder_autostart.ps1 - Registriert C-36-Recorder als Windows-Task
#
# Effekt:
#   - Bei jeder Benutzer-Anmeldung startet der Recorder automatisch
#     (30s Delay, damit das Netzwerk steht).
#   - Lauft versteckt im Hintergrund (kein Fenster pop-up).
#   - Bei Crash: 3x Neustart im Minutenabstand.
#   - Kein Execution Time Limit (Recorder soll dauerhaft laufen).
#   - Logs landen wie immer in logs\recorder\recorder_*.log.
#
# Idempotent: erneutes Ausfuehren ersetzt die Task ohne Fehler.
# Reversibel: .\uninstall_recorder_autostart.ps1
#
# Aufruf (KEIN Admin noetig, User-Level-Task):
#   powershell -ExecutionPolicy Bypass -File .\install_recorder_autostart.ps1
# ========================================================================

$ErrorActionPreference = "Stop"

$taskName    = "Scinance C-36 Recorder"
$repoRoot    = $PSScriptRoot
$scriptPath  = Join-Path $repoRoot "start_recorder.ps1"

if (-not (Test-Path $scriptPath)) {
    Write-Host "FEHLER: start_recorder.ps1 nicht gefunden unter $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Installation: $taskName" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Task: $taskName"
Write-Host "Trigger: bei Anmeldung von $env:USERNAME (30s Delay)"
Write-Host "Skript: $scriptPath"
Write-Host "Repo:   $repoRoot"
Write-Host ""

# Eventuell existierende Task entfernen (idempotent)
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $existing) {
    Write-Host "Vorhandene Task wird entfernt..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Action: powershell.exe ruft start_recorder.ps1 versteckt auf
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $repoRoot

# Trigger: bei Anmeldung des aktuellen Users, 30s Delay
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$trigger.Delay = "PT30S"

# Settings: dauerhaft, restart on failure, kein Time Limit, Akku-tolerant
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)
# Kein Execution Time Limit (PT0S = unlimited im XML-Schema)
$settings.ExecutionTimeLimit = "PT0S"

# Principal: aktueller User, interaktiv, geringste Rechte (kein Admin noetig)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Task registrieren
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Scinance 2.0 C-36 Recording-Engine (Schutzgut #1). Startet bei Anmeldung. Logs: logs\recorder\." | Out-Null

Write-Host ""
Write-Host "OK Task installiert." -ForegroundColor Green
Write-Host ""
Write-Host "Status:"
Get-ScheduledTask -TaskName $taskName |
    Select-Object TaskName, State, @{N="Trigger";E={$_.Triggers[0].CimClass.CimClassName}} |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Manuell starten (zum Test, ohne neuen Login):" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName `"$taskName`""
Write-Host ""
Write-Host "Status pruefen:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTaskInfo -TaskName `"$taskName`""
Write-Host ""
Write-Host "Deinstallieren:" -ForegroundColor Cyan
Write-Host "  .\uninstall_recorder_autostart.ps1"
Write-Host ""
