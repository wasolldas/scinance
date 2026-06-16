# ========================================================================
# run_wave2.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 2, WP-4 Handoff)
#
# Aufruf (keine Pflicht-Parameter, laeuft UNBEAUFSICHTIGT 2-4h):
#   powershell -ExecutionPolicy Bypass -File .\run_wave2.ps1
#
# Vorher Standby deaktivieren (sonst schlaeft der Rechner ein):
#   powercfg /change standby-timeout-ac 0
#
# Bloecke (jeder einzeln gekapselt: try/catch + Timeout + weitermachen,
# NIE ein offener Prompt):
#   H04            C-17/C-41 Lead-Lag-Mess-Gate (Paar BTC/ETH, KAPITALFREI)
#   H05            C-01 OFI-Vorzeichen-Test (5 Symbole, KAPITALFREI)
#   H06            C-07 Permutation Entropy (5 Symbole, KAPITALFREI)
#   WAVE2_FDR      F-WAVE2 zweistufige BH-FDR-Aggregation (Stage 1 + Stage 2)
#
# Exit-Code: 0 = alle Bloecke OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl\handoff_local\results\wave2_<timestamp>\
#             + WAVE2_SUMMARY.md (Morgen-Auswertung durch gate-auditor)
#
# Optionale Env-Overrides: HANDOFF_DUCKDB, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body + UTF-8-BOM).
# ========================================================================
$ErrorActionPreference = 'Continue'

# -- Pfade (bei Bedarf HIER anpassen - siehe README_WAVE2.md) ------------
$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$DuckDbPath = if ($env:HANDOFF_DUCKDB) { $env:HANDOFF_DUCKDB } else { Join-Path $RepoRoot 'data\bybit_edge.duckdb' }

$Pair          = 'BTCUSDT,ETHUSDT'
$Symbols       = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$NWindows      = 2
$NSurrogates   = 200
$Seed          = 42
$MaxTicks      = 150000
$MaxBars       = 43200

# Per-Schritt-Budgets (grosszuegig, aber endlich; CLAUDE.md T3-Regel).
$TmoH04 = 5400   # 90 min
$TmoH05 = 7200   # 120 min
$TmoH06 = 7200   # 120 min
$TmoAgg = 600    # 10 min

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("wave2_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h04') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h05') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h06') | Out-Null
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

Write-Host ("RUN_WAVE2 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("DuckDB: " + $DuckDbPath + " | Paar: " + $Pair + " | Symbole: " + $Symbols)
Write-Host ("Fenster: " + $NWindows + " Surrogates: " + $NSurrogates + " Seed: " + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# DuckDB-Pruefung.
$DbOk = $true
if ((-not $DryRun) -and (-not (Test-Path $DuckDbPath))) {
    $DbOk = $false
    Write-Host ("WARNUNG: DuckDB fehlt (" + $DuckDbPath + ") - HANDOFF_DUCKDB setzen oder Pfad oben anpassen")
}

# -- Block 1: H-04 C-17/C-41 Lead-Lag ------------------------------------
# --db-copy: Temp-Kopie der DuckDB lesen (lock-frei gegen den laufenden 1.0-
# Collector). --max-ticks-per-window=150000 ist DEC-10-Daten-Scoping; die
# H-04-Gate-Schwellen bleiben unveraendert. Lag-Universum kommt aus dem Driver
# (DEFAULT_LAGS) - KEIN CLI-Override, da im Driver vorregistriert.
if (-not $DbOk) {
    Record-Step -Name 'H04' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H04' -TimeoutSec $TmoH04 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c17_c41_lead_lag.py'),
        '--db', $DuckDbPath, '--pair', $Pair,
        '--windows', "$NWindows", '--surrogates', "$NSurrogates", '--seed', "$Seed",
        '--db-copy', '--max-ticks-per-window', "$MaxTicks",
        '--out', (Join-Path $RunDir 'h04')))
}

# -- Block 2: H-05 C-01 OFI-Vorzeichen -----------------------------------
# delta-Lag-Universum (1,5,15,60,300s) ist im Driver vorregistriert - kein
# CLI-Override hier. --max-ticks-per-window=150000 = DEC-11-Daten-Scoping.
if (-not $DbOk) {
    Record-Step -Name 'H05' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H05' -TimeoutSec $TmoH05 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c01_ofi_sign.py'),
        '--db', $DuckDbPath, '--symbols', $Symbols,
        '--windows', "$NWindows", '--surrogates', "$NSurrogates", '--seed', "$Seed",
        '--db-copy', '--max-ticks-per-window', "$MaxTicks",
        '--out', (Join-Path $RunDir 'h05')))
}

# -- Block 3: H-06 C-07 Permutation Entropy ------------------------------
# m=4/tau=1 sind read-only Konstanten im Driver (PE_M/PE_TAU), KEIN CLI-Flag.
# --max-bars-per-window=43200 (30 Tage) = DEC-12-Stationaritaets-Scoping.
if (-not $DbOk) {
    Record-Step -Name 'H06' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    [void](Invoke-Step -Name 'H06' -TimeoutSec $TmoH06 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c07_pe.py'),
        '--db', $DuckDbPath, '--symbols', $Symbols,
        '--windows', "$NWindows", '--surrogates', "$NSurrogates", '--seed', "$Seed",
        '--db-copy', '--max-bars-per-window', "$MaxBars",
        '--out', (Join-Path $RunDir 'h06')))
}

# -- Block 4: F-WAVE2 zweistufige BH-FDR-Aggregation ---------------------
$SummaryDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
[void](Invoke-Step -Name 'WAVE2_FDR' -TimeoutSec $TmoAgg -CmdArgs @(
    (Join-Path $ScriptDir 'aggregate_wave2_fdr.py'),
    '--h04', (Join-Path $RunDir 'h04'),
    '--h05', (Join-Path $RunDir 'h05'),
    '--h06', (Join-Path $RunDir 'h06'),
    '--out', (Join-Path $RunDir 'WAVE2_SUMMARY.md'),
    '--json', (Join-Path $RunDir 'wave2_summary.json'),
    '--label', ("wave2_" + $Ts)))

# -- SUMMARY_<datum>.md zusaetzlich (T3-Konvention, optional) ------------
$AggOptional = Join-Path $ScriptDir 'aggregate_results.py'
if (Test-Path $AggOptional) {
    $aggRc = Invoke-Step -Name 'SUMMARY' -TimeoutSec 300 -CmdArgs @(
        $AggOptional, '--run-dir', $RunDir, '--label', 'wave2', '--date', $SummaryDate)
    if ($aggRc -ne 0) {
        Write-Host "INFO: aggregate_results.py ist Welle-1-zugeschnitten - WAVE2_SUMMARY.md ist die verbindliche Welle-2-Auswertung."
    }
}

# -- Gesamt-Summary: 1 Zeile je Block + Exit-Code ------------------------
$nOk = 0; $nFail = 0; $nSkip = 0
$summaryLines = @('-------- RUN_WAVE2 SUMMARY --------')
foreach ($r in $Script:Results) {
    $summaryLines += ($r.Name + ': ' + $r.Status + ' (' + $r.Detail + ')')
    if ($r.Status -eq 'OK') { $nOk++ }
    elseif ($r.Status -eq 'FAIL') { $nFail++ }
    elseif ($r.Status -eq 'SKIP' -and (-not $r.OptionalSkip)) { $nSkip++ }
}
$exitCode = 0
if ($nSkip -gt 0) { $exitCode = 2 }
if ($nFail -gt 0) { $exitCode = 1 }
$summaryLines += ("RUN_WAVE2 GESAMT: ok=$nOk fail=$nFail skip=$nSkip -> exit $exitCode | Ergebnisse: " + $RunDir)
$summaryLines += ("F-WAVE2-Aggregat: " + (Join-Path $RunDir 'WAVE2_SUMMARY.md') + " (Morgen-Auswertung gate-auditor)")
$summaryLines | ForEach-Object { Write-Host $_ }
Set-Content -Path (Join-Path $RunDir 'summary.txt') -Value ($summaryLines -join "`r`n")
exit $exitCode
