# install_autopilot.ps1 -- einmalig ausfuehren. Registriert die geplante
# Aufgabe "Scinance Autopilot": alle 15 Minuten (und bei Anmeldung) startet
# pythonw.exe (kein Fenster) autopilot.py. Der Autopilot fuehrt Auftraege
# aus scinance3-impl\state\queue\auftrag.json im Git-Branch aus und pusht
# die Ergebnisse. Benutzerebene, kein Admin, kein gespeichertes Passwort.
# Voraussetzung: PC an und Nutzer angemeldet (Sperrbildschirm ist ok).
# Entfernen: uninstall_autopilot.ps1. ASCII-only, PowerShell 5.1.

param(
    [string]$RepoRoot = "",
    [int]$IntervalMinutes = 15
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path }
$py = (Get-Command python -ErrorAction Stop).Source
$pyw = Join-Path (Split-Path $py) "pythonw.exe"
if (-not (Test-Path $pyw)) { throw "pythonw.exe nicht gefunden neben $py" }
$script = Join-Path $RepoRoot "scinance3-impl\handoff_local\autopilot.py"
if (-not (Test-Path $script)) { throw "autopilot.py nicht gefunden: $script" }

$action = New-ScheduledTaskAction -Execute $pyw -Argument ('"' + $script + '"') -WorkingDirectory $RepoRoot
$tRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$tLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun
Register-ScheduledTask -TaskName "Scinance Autopilot" -Action $action -Trigger @($tRepeat, $tLogon) `
    -Settings $settings -Description "Scinance: Auftraege aus dem Git-Branch unbeaufsichtigt ausfuehren (autopilot.py)" -Force | Out-Null

$info = Get-ScheduledTask -TaskName "Scinance Autopilot" | Get-ScheduledTaskInfo
Write-Host "Scinance Autopilot registriert. Naechster Lauf: $($info.NextRunTime)"
Write-Host "Protokoll: $RepoRoot\data\autopilot\autopilot.log"
Write-Host "Hinweis: PC nicht in den Energiesparmodus schicken, sonst warten Auftraege bis zum Aufwachen."
