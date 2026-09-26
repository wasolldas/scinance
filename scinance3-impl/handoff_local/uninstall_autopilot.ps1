# uninstall_autopilot.ps1 -- entfernt die geplante Aufgabe "Scinance Autopilot".
# Laufende Auftraege werden nicht abgebrochen. ASCII-only, PowerShell 5.1.
Unregister-ScheduledTask -TaskName "Scinance Autopilot" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Scinance Autopilot entfernt."
