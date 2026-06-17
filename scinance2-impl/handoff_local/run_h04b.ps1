# ========================================================================
# run_h04b.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 2, H-04b Handoff)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 10-30 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h04b.ps1
#
# H-04b = C-17/C-41 Lead-Lag-TRADABILITY-Gate (Paar BTC/ETH). Erste NICHT-
# kapitalfreie Hypothese: das Gate konfrontiert Edge-bps gegen die verbindliche
# 11-bps-Friction-Wand nach 300-ms-Latenz-Haircut. Es bleibt ein HISTORISCHER
# BACKTEST MIT KOSTENMODELL auf dem read-only trades-Bestand - KEIN Live-Order-
# Code, KEIN Geldeinsatz (CLAUDE.md Paragraf 4 / Autonomie-Protokoll Paragraf 3).
#
# Bloecke (jeder einzeln gekapselt: try/catch + Timeout + weitermachen,
# NIE ein offener Prompt):
#   H04B_PRIMARY   URTEILSTRAGEND: latency=300ms, friction=11bps, Taker (Default-
#                  Punkt). NUR an diesem Punkt faellt das Pass-Urteil (Anti-
#                  Gaming-Klausel registry H-04b, gate_valid_assumptions=true).
#   H04B_LAT100    ROBUSTHEIT (NICHT urteilstragend): latency=100ms.
#   H04B_LAT500    ROBUSTHEIT (NICHT urteilstragend): latency=500ms.
#   H04B_MAKER     SEKUNDAER (NICHT urteilstragend): --maker-secondary, adverse-
#                  selection-vorbehaltlich; gate_valid_assumptions=false.
#
# Die drei Robustheits-/Sekundaer-Bloecke setzen gate_valid_assumptions=false im
# Output und sind als Sensitivitaets-Spanne MIT-berichtet - sie duerfen ein
# WEITER NICHT erzwingen. Das Pass-Urteil faellt der gate-auditor AUSSCHLIESSLICH
# am H04B_PRIMARY-Punkt (300ms/11bps/Taker).
#
# Exit-Code: 0 = alle Bloecke OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl\handoff_local\results\h04b_<timestamp>\
#             + SUMMARY_<datum>.md (Morgen-Auswertung durch gate-auditor)
#
# Optionale Env-Overrides: HANDOFF_DUCKDB, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body + UTF-8-BOM).
# ========================================================================
$ErrorActionPreference = 'Continue'

# -- Pfade (bei Bedarf HIER anpassen - siehe README_H04B.md) -------------
$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$DuckDbPath = if ($env:HANDOFF_DUCKDB) { $env:HANDOFF_DUCKDB } else { Join-Path $RepoRoot 'data\bybit_edge.duckdb' }

$Pair         = 'BTCUSDT,ETHUSDT'
$Windows      = 2
$Lags         = '1,2,3'
$FrictionBps  = 11        # verbindliche Friction-Wand (verdict.md sek. 2 Taker-Baseline)
$LatPrimary   = 300       # URTEILSTRAGENDER Latenz-Default (DEC-13, Anti-Gaming)
$LatLow       = 100       # Robustheits-Spanne unten - NICHT urteilstragend
$LatHigh      = 500       # Robustheits-Spanne oben  - NICHT urteilstragend
$Bootstrap    = 200
$Seed         = 42
$MaxTicks     = 150000    # DEC-10-Daten-Scoping (Gate-Schwellen UNVERAENDERT)
$GridMs       = 1000

# Per-Schritt-Budget (grosszuegig, aber endlich; CLAUDE.md T2/T3-Regel).
$TmoStep = 1800   # 30 min je Lauf

# -- Umgebung ------------------------------------------------------------
$PythonExe = if ($env:PYTHON) { $env:PYTHON } else { 'python' }
$SrcPath = Join-Path $RepoRoot 'src'
$env:PYTHONPATH = if ($env:PYTHONPATH) { $SrcPath + ';' + $env:PYTHONPATH } else { $SrcPath }
if (-not $env:BYBIT_DATA_DIR) { $env:BYBIT_DATA_DIR = Join-Path $RepoRoot 'data' }
Set-Location $RepoRoot
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch { }

$DryRun = ($env:HANDOFF_DRY_RUN -and ($env:HANDOFF_DRY_RUN -ne '0'))
$DryRc  = 0
if ($env:HANDOFF_DRY_RC) { $DryRc = [int]$env:HANDOFF_DRY_RC }

$Ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$SummaryDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h04b_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h04b') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h04b_lat100') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h04b_lat500') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h04b_maker') | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail,
          [bool]$OptionalSkip = $false)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{
        Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur
        Detail = $Detail; OptionalSkip = $OptionalSkip
    })
}

# Gekapselter Schritt: try/catch + ExitCode-Pruefung + Timeout (Kill).
function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs)
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
            # PS 5.1 quirk: cache the handle BEFORE the process exits,
            # otherwise $p.ExitCode is $null after WaitForExit().
            $null = $p.Handle
            try { $p.PriorityClass = 'BelowNormal' } catch { }
            if (-not $p.WaitForExit($TimeoutSec * 1000)) {
                try { $p.Kill() } catch { }
                $rc = 124
                $detail = "TIMEOUT nach $TimeoutSec s"
            } else {
                $rc = $p.ExitCode
                if ($null -eq $rc) {
                    $rc = -2
                    $detail = 'ExitCode war null (Handle-Quirk) - Log pruefen'
                }
            }
        } catch {
            $rc = -1
            $detail = $_.Exception.Message
        }
    }
    $dur = [int]((Get-Date) - $t0).TotalSeconds
    $status = 'FAIL'
    if ($rc -eq 0) { $status = 'OK' }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_H04B (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("DuckDB: " + $DuckDbPath + " | Paar: " + $Pair + " | windows=" + $Windows + " lags=" + $Lags)
Write-Host ("URTEILSTRAGEND: latency=" + $LatPrimary + "ms friction=" + $FrictionBps + "bps Taker | bootstrap=" + $Bootstrap + " seed=" + $Seed)
Write-Host ("ROBUSTHEIT (NICHT urteilstragend): latency=" + $LatLow + "ms, latency=" + $LatHigh + "ms, --maker-secondary")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# DuckDB-Pruefung.
$DbOk = $true
if ((-not $DryRun) -and (-not (Test-Path $DuckDbPath))) {
    $DbOk = $false
    Write-Host ("WARNUNG: DuckDB fehlt (" + $DuckDbPath + ") - HANDOFF_DUCKDB setzen oder Pfad oben anpassen")
}

# -- Block 1: H04B_PRIMARY (URTEILSTRAGEND, 300ms/11bps/Taker) -----------
# --db-copy: Temp-Kopie der DuckDB lesen (lock-frei gegen den laufenden 1.0-
# Collector). Registry-konforme Defaults: latency=300, friction=11, Taker -
# die EINZIGEN Pass-gueltigen Werte. NICHT ueberschreiben (Anti-Gaming Par.2).
# --max-ticks-per-window=150000 ist DEC-10-Daten-Scoping; Gate-Schwellen UNVER-
# AENDERT. lags=1,2,3 = H-04-Survivor; horizon=lag im Driver vorab fixiert.
if (-not $DbOk) {
    Record-Step -Name 'H04B_PRIMARY' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H04B_PRIMARY' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c17_c41_tradability.py'),
        '--db', $DuckDbPath, '--pair', $Pair,
        '--windows', "$Windows", '--lags', $Lags,
        '--latency-ms', "$LatPrimary", '--friction-bps', "$FrictionBps",
        '--bootstrap', "$Bootstrap", '--seed', "$Seed",
        '--db-copy', '--max-ticks-per-window', "$MaxTicks", '--grid-ms', "$GridMs",
        '--out', (Join-Path $RunDir 'h04b')))
}

# -- Block 2: H04B_LAT100 (ROBUSTHEIT - NICHT urteilstragend) ------------
# Sensitivitaets-Spanne untere Latenz. Setzt gate_valid_assumptions=false; ein
# WEITER hier zaehlt NICHT (kuerzere Latenz darf das WEITER nicht erzwingen,
# registry H-04b Anti-Gaming-Klausel).
if (-not $DbOk) {
    Record-Step -Name 'H04B_LAT100' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H04B_LAT100' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c17_c41_tradability.py'),
        '--db', $DuckDbPath, '--pair', $Pair,
        '--windows', "$Windows", '--lags', $Lags,
        '--latency-ms', "$LatLow", '--friction-bps', "$FrictionBps",
        '--bootstrap', "$Bootstrap", '--seed', "$Seed",
        '--db-copy', '--max-ticks-per-window', "$MaxTicks", '--grid-ms', "$GridMs",
        '--out', (Join-Path $RunDir 'h04b_lat100')))
}

# -- Block 3: H04B_LAT500 (ROBUSTHEIT - NICHT urteilstragend) ------------
# Sensitivitaets-Spanne obere Latenz. Setzt gate_valid_assumptions=false.
if (-not $DbOk) {
    Record-Step -Name 'H04B_LAT500' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H04B_LAT500' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c17_c41_tradability.py'),
        '--db', $DuckDbPath, '--pair', $Pair,
        '--windows', "$Windows", '--lags', $Lags,
        '--latency-ms', "$LatHigh", '--friction-bps', "$FrictionBps",
        '--bootstrap', "$Bootstrap", '--seed', "$Seed",
        '--db-copy', '--max-ticks-per-window', "$MaxTicks", '--grid-ms', "$GridMs",
        '--out', (Join-Path $RunDir 'h04b_lat500')))
}

# -- Block 4: H04B_MAKER (SEKUNDAER - NICHT urteilstragend) --------------
# Maker-Sekundaerfall: adverse-selection-vorbehaltlich (Maker-Fills auf einem
# 1-3s-Lead-Signal werden bevorzugt gefuellt, wenn man falsch liegt). NIE das
# Primaer-Pass-Kriterium; Driver setzt gate_valid_assumptions=false. Bei
# Default-Latenz 300ms gefahren, damit nur der Maker-Aspekt variiert.
if (-not $DbOk) {
    Record-Step -Name 'H04B_MAKER' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H04B_MAKER' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c17_c41_tradability.py'),
        '--db', $DuckDbPath, '--pair', $Pair,
        '--windows', "$Windows", '--lags', $Lags,
        '--latency-ms', "$LatPrimary", '--friction-bps', "$FrictionBps", '--maker-secondary',
        '--bootstrap', "$Bootstrap", '--seed', "$Seed",
        '--db-copy', '--max-ticks-per-window', "$MaxTicks", '--grid-ms', "$GridMs",
        '--out', (Join-Path $RunDir 'h04b_maker')))
}

# -- Gesamt-Summary: 1 Zeile je Block + Exit-Code ------------------------
$nOk = 0; $nFail = 0; $nSkip = 0
$summaryLines = @('-------- RUN_H04B SUMMARY --------')
foreach ($r in $Script:Results) {
    $summaryLines += ($r.Name + ': ' + $r.Status + ' (' + $r.Detail + ', ' + $r.Dur + 's)')
    if ($r.Status -eq 'OK') { $nOk++ }
    elseif ($r.Status -eq 'FAIL') { $nFail++ }
    elseif ($r.Status -eq 'SKIP' -and (-not $r.OptionalSkip)) { $nSkip++ }
}
$exitCode = 0
if ($nSkip -gt 0) { $exitCode = 2 }
if ($nFail -gt 0) { $exitCode = 1 }
$summaryLines += ("RUN_H04B GESAMT: ok=$nOk fail=$nFail skip=$nSkip -> exit $exitCode | Ergebnisse: " + $RunDir)
$summaryLines += "URTEIL: NUR H04B_PRIMARY (300ms/11bps/Taker). Robustheit/Maker NICHT urteilstragend."
$summaryLines | ForEach-Object { Write-Host $_ }
Set-Content -Path (Join-Path $RunDir 'summary.txt') -Value ($summaryLines -join "`r`n")

# SUMMARY_<datum>.md (maschinen- und menschenlesbar fuer den gate-auditor)
$mdLines = @()
$mdLines += '# H-04b - C-17/C-41 Lead-Lag-TRADABILITY Runner (T2)'
$mdLines += ''
$mdLines += ("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + ' UTC')
$mdLines += ("- **Run-Dir:** ``" + $RunDir + '``')
$mdLines += ("- **DuckDB:** ``" + $DuckDbPath + '``')
$mdLines += ("- **Paar:** " + $Pair + " | windows=" + $Windows + " | lags=" + $Lags + " | bootstrap=" + $Bootstrap + " | seed=" + $Seed)
$mdLines += '- **capital_free = FALSE** (erste nicht-kapitalfreie Hypothese; aber HISTORISCHER'
$mdLines += '  BACKTEST mit Kostenmodell auf read-only trades - KEIN Live-Order-Code, KEIN Geld).'
$mdLines += ''
$mdLines += '## Urteilstragender Punkt (Anti-Gaming-Klausel)'
$mdLines += ''
$mdLines += ("Das H-04b-Pass-Urteil faellt **AUSSCHLIESSLICH** am Block **H04B_PRIMARY** (latency=" + $LatPrimary + "ms,")
$mdLines += ("friction=" + $FrictionBps + "bps, Taker) - der EINZIGE Punkt mit ``gate_valid_assumptions=true``.")
$mdLines += 'Die Bloecke H04B_LAT100 / H04B_LAT500 / H04B_MAKER sind **Robustheits-/Sekundaer-Laeufe'
$mdLines += '(NICHT urteilstragend)**, MIT-berichtet als Sensitivitaets-Spanne; sie setzen'
$mdLines += '``gate_valid_assumptions=false`` und duerfen ein WEITER NICHT erzwingen (registry H-04b'
$mdLines += 'Anti-Gaming-Klausel).'
$mdLines += ''
$mdLines += '| Block | Rolle | Status | rc | Dauer | Detail |'
$mdLines += '|---|---|---|---:|---:|---|'
$roleMap = @{
    'H04B_PRIMARY' = 'URTEILSTRAGEND (300ms/11bps/Taker)'
    'H04B_LAT100'  = 'Robustheit (NICHT urteilstragend)'
    'H04B_LAT500'  = 'Robustheit (NICHT urteilstragend)'
    'H04B_MAKER'   = 'Sekundaer (NICHT urteilstragend)'
}
foreach ($r in $Script:Results) {
    $role = $roleMap[$r.Name]
    if (-not $role) { $role = '-' }
    $mdLines += ('| ' + $r.Name + ' | ' + $role + ' | ' + $r.Status + ' | ' + $r.Rc + ' | ' + $r.Dur + 's | ' + $r.Detail + ' |')
}
$mdLines += ''
$mdLines += ("**Gesamt:** ok=" + $nOk + " fail=" + $nFail + " skip=" + $nSkip + " -> exit " + $exitCode)
$mdLines += ''
$mdLines += '*H-04b-Gate-Urteil faellt der gate-auditor gegen die Registry (Roh-JSON unter'
$mdLines += '`h04b/c17_c41_tradability_results.json`; das harte Ein-Fenster-PARK-Kriterium und die'
$mdLines += 'Anti-Gaming-Klausel gelten - WEITER nur am H04B_PRIMARY-Punkt).*'
Set-Content -Path (Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")) -Value ($mdLines -join "`r`n") -Encoding UTF8

exit $exitCode
