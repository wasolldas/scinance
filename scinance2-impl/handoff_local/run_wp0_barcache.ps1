# ========================================================================
# run_wp0_barcache.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 6, WP-0)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_wp0_barcache.ps1
#
# WP-0 = geteilter deterministischer 1-min-Bar-Cache (DEC-34/35).
# Hintergrund: Drei H-11c-Laeufe auf identischem Code und identischem
# Datenstand lieferten unterschiedliche Panels - der Roh-Tick-Lesepfad ist
# nicht-deterministisch (parallele Float-Summation; max_by-Tie bei
# gleichem Millisekunden-Zeitstempel). Welle 6 liest deshalb NUR noch aus
# diesem Cache: jede Spalte ist ein ordnungs-UNabhaengiges Aggregat
# (arg_max/arg_min ueber (ts,px)-Tupel, DECIMAL-exakte Volumensummen,
# exakte Counts), jeder Tag wird EINMAL eingefroren (nur Manifest-DONE-
# Tage) und traegt einen SHA-256-Sidecar. Der Range-Fingerabdruck je
# Symbol gehoert in jede Welle-6-Registrierung.
#
# KAPITALFREI: reine Mess-Infrastruktur. Der Cache liegt in data\barcache
# (NEUER Pfad) - in den read-only Harvester-Baum wird NIE geschrieben.
#
# INKREMENTELL + RESUMEBAR: bereits gecachte Tage werden uebersprungen.
# Abbruch/Reboot mitten in der Nacht kostet nichts - einfach neu starten.
#
# Schritte: WP0_BARCACHE (alle 5 Symbole, volle Historie). Danach steht
# der Fingerabdruck je Symbol in wp0\barcache_build.json.
# Exit: 0 = OK * 1 = FAIL (inkl. Loud-Fail-Tage) * 2 = SKIP (Harvester fehlt).
# Ergebnisse: scinance2-impl\handoff_local\results\wp0_<timestamp>\
#             + SUMMARY_<datum>.md
#
# Optionale Env-Overrides: HARVEST_DIR, BARCACHE_DIR, WP0_RESULTS_DIR,
# WP0_TIMEOUT_SEC (Default 43200 = 12 h), WP0_SYMBOLS, WP0_START, WP0_END,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }
$CacheDir   = if ($env:BARCACHE_DIR) { $env:BARCACHE_DIR } else { Join-Path $RepoRoot 'data\barcache' }

$Symbols = if ($env:WP0_SYMBOLS) { $env:WP0_SYMBOLS } else { 'BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,BNBUSDT' }
$Start   = if ($env:WP0_START) { $env:WP0_START } else { '2020-03-25' }
$End     = if ($env:WP0_END) { $env:WP0_END } else { '2026-07-31' }
# Eine CPU-Nacht laut Synthese; 12 h Budget, ueberschreibbar.
$TmoStep = if ($env:WP0_TIMEOUT_SEC) { [int]$env:WP0_TIMEOUT_SEC } else { 43200 }
# DuckDB-Speicherdeckel je Verbindung (DEC-36: Lauf 2026-08-14 crashte OOM
# nach ~4300 Tages-Queries ohne Deckel). Ueberschuss spillt auf Platte.
$MemLimit = if ($env:WP0_MEMORY_LIMIT) { $env:WP0_MEMORY_LIMIT } else { '4GB' }

$PythonExe = if ($env:PYTHON) { $env:PYTHON } else { 'python' }
$SrcPath = Join-Path $RepoRoot 'src'
$env:PYTHONPATH = if ($env:PYTHONPATH) { $SrcPath + ';' + $env:PYTHONPATH } else { $SrcPath }
Set-Location $RepoRoot
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch { }

$DryRun = ($env:HANDOFF_DRY_RUN -and ($env:HANDOFF_DRY_RUN -ne '0'))
$DryRc  = 0
if ($env:HANDOFF_DRY_RC) { $DryRc = [int]$env:HANDOFF_DRY_RC }

$Ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$SummaryDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$ResultsBase = if ($env:WP0_RESULTS_DIR) { $env:WP0_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("wp0_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'wp0') | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{ Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail })
}

function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs, [int[]]$OkRcs = @(0), [int[]]$SkipRcs = @())
    $log = Join-Path $RunDir ($Name + '.log')
    $errLog = Join-Path $RunDir ($Name + '.err.log')
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] START " + $Name + ": " + $PythonExe + " " + ($CmdArgs -join ' '))
    $t0 = Get-Date
    $rc = -1
    $detail = ''
    if ($DryRun) {
        Add-Content -Path $log -Value ("[DRY-RUN] " + ($CmdArgs -join ' '))
        $rc = $DryRc
        $detail = "dry-run rc=$rc"
    } else {
        try {
            $quoted = @()
            foreach ($a in $CmdArgs) {
                if ($a -match '\s') { $quoted += ('"' + $a + '"') } else { $quoted += $a }
            }
            $p = Start-Process -FilePath $PythonExe -ArgumentList $quoted -NoNewWindow -PassThru `
                 -RedirectStandardOutput $log -RedirectStandardError $errLog
            $null = $p.Handle
            try { $p.PriorityClass = 'BelowNormal' } catch { }
            if (-not $p.WaitForExit($TimeoutSec * 1000)) {
                try { $p.Kill() } catch { }
                $rc = 124
                $detail = "TIMEOUT nach $TimeoutSec s (Cache ist inkrementell - einfach neu starten)"
            } else {
                $rc = $p.ExitCode
                if ($null -eq $rc) { $rc = -2; $detail = 'ExitCode war null (Handle-Quirk) - Log pruefen' }
            }
        } catch {
            $rc = -1
            $detail = $_.Exception.Message
        }
    }
    $dur = [int]((Get-Date) - $t0).TotalSeconds
    $status = 'FAIL'
    if ($OkRcs -contains $rc) { $status = 'OK' }
    if ($SkipRcs -contains $rc) { $status = 'SKIP' }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_WP0 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " (read-only) -> Cache: " + $CacheDir + " (NEUER Pfad)")
Write-Host ("Symbole: " + $Symbols + " | Range: " + $Start + ".." + $End + " | inkrementell/resumebar")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\build_bar_cache.py'
$OutJson = Join-Path (Join-Path $RunDir 'wp0') 'barcache_build.json'
$rcRun = 2
if (-not $HarvestOk) {
    Record-Step -Name 'WP0_BARCACHE' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
} else {
    $rcRun = Invoke-Step -Name 'WP0_BARCACHE' -TimeoutSec $TmoStep -OkRcs @(0) -CmdArgs @(
        $CliScript,
        '--base-dir', $HarvestDir,
        '--cache-dir', $CacheDir,
        '--symbols', $Symbols,
        '--start', $Start, '--end', $End,
        '--memory-limit', $MemLimit
    )
    # stdout (JSON mit Fingerabdruecken) in die Ergebnisse kopieren
    $stepLog = Join-Path $RunDir 'WP0_BARCACHE.log'
    if (Test-Path $stepLog) { Copy-Item $stepLog $OutJson -Force }
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# WP-0 Bar-Cache-Aufbau (Welle 6) - T3")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) -> **Cache:** ``" + $CacheDir + "``")
[void]$sb.AppendLine("- **Symbole:** " + $Symbols + " | **Range:** " + $Start + ".." + $End)
[void]$sb.AppendLine("- **Determinismus:** ordnungs-unabhaengige Aggregate (arg_max/arg_min ueber (ts,px), DECIMAL-Summen, exakte Counts); nur Manifest-DONE-Tage; SHA-256-Sidecar je Tag (DEC-34/35).")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Mess-Infrastruktur, kein Kosten-/PnL-Begriff.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Schritte")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Schritt | Status | rc | Dauer | Detail |")
[void]$sb.AppendLine("|---|---|---:|---:|---|")
foreach ($r in $Script:Results) {
    [void]$sb.AppendLine("| " + $r.Name + " | " + $r.Status + " | " + $r.Rc + " | " + $r.Dur + "s | " + $r.Detail + " |")
}
[void]$sb.AppendLine("")
[void]$sb.AppendLine("**Gesamt:** ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
[void]$sb.AppendLine("")
if ($exit -eq 0) {
    [void]$sb.AppendLine("*Die Range-Fingerabdruecke je Symbol stehen in ``wp0\barcache_build.json`` -")
    [void]$sb.AppendLine("sie gehoeren woertlich in jede Welle-6-Registrierung (DEC-34 Punkt 4).")
    [void]$sb.AppendLine("Der Cache ist inkrementell: ein spaeterer Lauf friert nur NEUE Manifest-DONE-Tage ein.*")
} elseif ($exit -eq 1) {
    [void]$sb.AppendLine("**FEHLER** - Log pruefen (``WP0_BARCACHE.err.log``). Ein Loud-Fail-Tag (Rohzeilen")
    [void]$sb.AppendLine("vorhanden, 0 parsebare Trades) stoppt das betroffene Symbol laut, statt leere Bars")
    [void]$sb.AppendLine("einzufrieren. Der Lauf ist nach Klaerung gefahrlos wiederholbar (inkrementell).")
} else {
    [void]$sb.AppendLine("**SKIP** - Harvester nicht erreichbar. Junction pruefen (ensure_harvest_junction.ps1).")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
