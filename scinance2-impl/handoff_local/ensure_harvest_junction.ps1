# ========================================================================
# ensure_harvest_junction.ps1 - Junction-Guard fuer data\harvest
#
# Prueft, ob die read-only Harvester-Junction
#     <RepoRoot>\data\harvest  ->  <Target>
# existiert und funktioniert (raw\bybit\publicTrade erreichbar), und
# stellt sie bei Bedarf wieder her. Hintergrund: Die Junction ist nach
# Reboots/Aufraeum-Aktionen im Data-Harvest-Projekt zweimal verschwunden
# (2026-07-17 defekt-ueberlebt, 2026-08-03/04 komplett weg) und hat damit
# Overnight-Laeufe zu SKIP gezwungen.
#
# SICHERHEIT (Schutzgut-Doktrin): Dieses Skript loescht data\harvest NUR,
# wenn der Eintrag ein ReparsePoint (Junction/Symlink) ist oder gar nicht
# existiert. Ist data\harvest ein ECHTES Verzeichnis (womoeglich mit
# materialisierten Daten), bricht es LAUT ab und fasst nichts an.
#
# Aufruf (manuell oder per geplanter Aufgabe bei Anmeldung):
#   powershell -ExecutionPolicy Bypass -File .\ensure_harvest_junction.ps1
#
# Registrierung als Autostart (einmalig, KEIN Admin noetig, laeuft bei
# jeder Anmeldung des aktuellen Nutzers):
#   schtasks /Create /TN "Scinance Harvest Junction Guard" `
#     /TR "powershell -ExecutionPolicy Bypass -File \"E:\Claude\Projects\scinance\scinance2-impl\handoff_local\ensure_harvest_junction.ps1\"" `
#     /SC ONLOGON /RL LIMITED /F
#
# Env-Overrides: HARVEST_JUNCTION_TARGET (Default s.u.).
# Exit-Codes: 0 = OK (vorhanden oder repariert) * 1 = FEHLER (Ziel fehlt
# oder data\harvest ist ein echtes Verzeichnis - manuelle Klaerung noetig).
# Log: results\junction_guard.log (append, mit Zeitstempel).
# PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$Junction  = Join-Path $RepoRoot 'data\harvest'
$Target    = if ($env:HARVEST_JUNCTION_TARGET) { $env:HARVEST_JUNCTION_TARGET }
             else { 'E:\Claude\Projects\Data Harvest\data-harvest\data' }
$Probe     = Join-Path $Junction 'raw\bybit\publicTrade'
$LogDir    = Join-Path $ScriptDir 'results'
$LogFile   = Join-Path $LogDir 'junction_guard.log'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Log-Line {
    param([string]$Msg)
    $line = ((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + 'Z  ' + $Msg)
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

# 1) Schnellpfad: alles gesund?
if (Test-Path $Probe) {
    Log-Line ("OK: Junction gesund (" + $Probe + " erreichbar). Nichts zu tun.")
    exit 0
}

Log-Line ("PRUEFUNG: '" + $Probe + "' NICHT erreichbar - beginne Reparatur-Check.")

# 2) Ziel muss existieren, sonst kann keine Junction helfen.
$TargetProbe = Join-Path $Target 'raw\bybit\publicTrade'
if (-not (Test-Path $TargetProbe)) {
    Log-Line ("FEHLER: Junction-ZIEL fehlt oder unvollstaendig ('" + $TargetProbe + "' nicht gefunden). " +
              "Data-Harvest-Projekt pruefen (Laufwerk gemountet? Verzeichnis umbenannt/kompaktiert?). KEINE Aktion.")
    exit 1
}

# 3) Existiert am Junction-Pfad irgendetwas?
$item = Get-Item -LiteralPath $Junction -Force -ErrorAction SilentlyContinue
if ($null -ne $item) {
    $isReparse = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if (-not $isReparse) {
        Log-Line ("FEHLER: '" + $Junction + "' existiert, ist aber KEIN ReparsePoint, sondern ein echtes " +
                  "Verzeichnis/Datei. SICHERHEITS-STOPP - wird NICHT geloescht (Schutzgut). Manuell klaeren.")
        exit 1
    }
    # Toter ReparsePoint (Junction zeigt ins Leere) -> Eintrag entfernen.
    # rmdir auf eine Junction loescht NUR den Verweis, NIE den Zielinhalt.
    Log-Line ("REPARATUR: toter ReparsePoint gefunden (Ziel laut Eintrag: '" +
              ($item.Target -join ';') + "') - entferne Verweis.")
    cmd /c rmdir "$Junction" 2>&1 | Out-Null
    if (Test-Path -LiteralPath $Junction) {
        Log-Line "FEHLER: Verweis liess sich nicht entfernen. Manuell klaeren."
        exit 1
    }
}

# 4) Junction neu anlegen und verifizieren.
Log-Line ("REPARATUR: lege Junction neu an: '" + $Junction + "' -> '" + $Target + "'")
cmd /c mklink /J "$Junction" "$Target" 2>&1 | ForEach-Object { Log-Line ("mklink: " + $_) }
if (Test-Path $Probe) {
    Log-Line "OK: Junction repariert und verifiziert."
    exit 0
}
Log-Line "FEHLER: Junction angelegt, aber Probe-Pfad weiterhin nicht erreichbar. Manuell klaeren."
exit 1
