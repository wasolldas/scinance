# ========================================================================
# run_short.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 1, WP-5)
#
# Aufruf (keine Pflicht-Parameter, ~10-20 min):
#   powershell -ExecutionPolicy Bypass -File .\run_short.ps1
#
# Schritte (jeder einzeln gekapselt: try/catch + Timeout + weitermachen):
#   1) RECORDER_SMOKE   5-min-Live-Smoke der F0-Recording-Engine (C-36)
#   2) RECORDER_CHECK   Parquet-Existenz + Row-Count je Stream + Schema-Version
#   3) E15_EVAL         E-15/H-01-Auswertung der echten iter-5-Ergebnisse
#                       (Baseline: iter-4 aus edge-reconciliation\input\iter4_raw\)
#   4) C42_QUICK_HAR    C-42-Quick-Fit BTCUSDT, HAR-Baseline (laeuft immer)
#   5) C42_QUICK_LGBM   dito mit LightGBM, NUR falls installiert (optional)
#
# Ende: 1 Zeile je Schritt (OK/FAIL/SKIP) + Exit-Code:
#   0 = alle OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Details: scinance2-impl\handoff_local\results\short_<timestamp>\
#
# Dry-Run (Mechanik-Test):  $env:HANDOFF_DRY_RUN='1'; .\run_short.ps1
# Kompatibel mit Windows PowerShell 5.1 und PowerShell 7.
# ========================================================================
$ErrorActionPreference = 'Continue'

# -- Pfade (bei Bedarf HIER anpassen - siehe README_RUN.md) --------------
$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
# Lokale DuckDB mit kline_1min/trades. Default = Repo-ueblicher Pfad aus
# persistence/db.py (DATA_DIR/bybit_edge.duckdb). Override: $env:HANDOFF_DUCKDB.
$DuckDbPath = if ($env:HANDOFF_DUCKDB) { $env:HANDOFF_DUCKDB } else { Join-Path $RepoRoot 'data\bybit_edge.duckdb' }
# iter-5-Replay-Artefakte (DEC-02-Default-Pfade von replay_all.py).
$E15Results     = Join-Path $RepoRoot 'edge_research_framework\results\replay_all_results.json'
$E15Trades      = Join-Path $RepoRoot 'edge_research_framework\results\trades_all.csv'
# iter-4-Baseline fuer den E-17-Divergenz-Check.
$E15BaseResults = Join-Path $RepoRoot 'edge-reconciliation\input\iter4_raw\replay_all_results.json'
$E15BaseTrades  = Join-Path $RepoRoot 'edge-reconciliation\input\iter4_raw\trades_all.csv'

# -- Umgebung -------------------------------------------------------------
$PythonExe = if ($env:PYTHON) { $env:PYTHON } else { 'python' }
$SrcPath = Join-Path $RepoRoot 'src'
$env:PYTHONPATH = if ($env:PYTHONPATH) { $SrcPath + ';' + $env:PYTHONPATH } else { $SrcPath }
if (-not $env:BYBIT_DATA_DIR) { $env:BYBIT_DATA_DIR = Join-Path $RepoRoot 'data' }
Set-Location $RepoRoot

$DryRun = ($env:HANDOFF_DRY_RUN -and ($env:HANDOFF_DRY_RUN -ne '0'))
$DryRc  = 0
if ($env:HANDOFF_DRY_RC) { $DryRc = [int]$env:HANDOFF_DRY_RC }

$Ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("short_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
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

# Gekapselter Schritt: try/catch + $LASTEXITCODE-/ExitCode-Pruefung + Timeout.
# Fehler werden geloggt, der Lauf geht IMMER weiter. Rueckgabe = rc.
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

Write-Host ("RUN_SHORT (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# -- Schritt 1: Recorder-Smoke (5 min live gegen echte Bybit-WS) ---------
[void](Invoke-Step -Name 'RECORDER_SMOKE' -TimeoutSec 420 -CmdArgs @(
    '-m', 'bybit_edge.recorder', '--duration', '300', '--cap-gb', '5'))

# -- Schritt 2: Parquet-/Row-Count-/Schema-Version-Check je Stream -------
[void](Invoke-Step -Name 'RECORDER_CHECK' -TimeoutSec 120 -CmdArgs @(
    (Join-Path $ScriptDir 'check_recording.py'), '--max-age-min', '30',
    '--json', (Join-Path $RunDir 'recording_check.json')))

# -- Schritt 3: E-15-Auswertung auf echten iter-5-Ergebnissen ------------
if ((-not $DryRun) -and (-not (Test-Path $E15Results))) {
    Record-Step -Name 'E15_EVAL' -Status 'SKIP' -Rc 0 -Dur 0 `
        -Detail ("iter-5-Ergebnisse fehlen (" + $E15Results + ") - scripts/replay_all.py separat laufen lassen")
} else {
    [void](Invoke-Step -Name 'E15_EVAL' -TimeoutSec 600 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\evaluate_e15.py'),
        '--results-path', $E15Results, '--trades-path', $E15Trades,
        '--baseline-results', $E15BaseResults, '--baseline-trades', $E15BaseTrades,
        '--out', (Join-Path $RunDir 'e15')))
}

# -- Schritt 4: C-42-Quick-Fit BTCUSDT (HAR, laeuft immer) ---------------
if ((-not $DryRun) -and (-not (Test-Path $DuckDbPath))) {
    Record-Step -Name 'C42_QUICK_HAR' -Status 'SKIP' -Rc 0 -Dur 0 `
        -Detail ("DuckDB fehlt (" + $DuckDbPath + ") - Pfad oben im Skript / HANDOFF_DUCKDB anpassen")
    Record-Step -Name 'C42_QUICK_LGBM' -Status 'SKIP' -Rc 0 -Dur 0 -Detail 'DuckDB fehlt' -OptionalSkip $true
} else {
    [void](Invoke-Step -Name 'C42_QUICK_HAR' -TimeoutSec 900 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c42_repro.py'), '--quick', '--model', 'har',
        '--symbol', 'BTCUSDT', '--db-path', $DuckDbPath,
        '--out', (Join-Path $RunDir 'c42_quick_har')))

    # -- Schritt 5 (optional): zusaetzlich LightGBM, falls installiert ---
    $lgbmOk = $false
    if ($DryRun) { $lgbmOk = $true }
    else {
        try {
            & $PythonExe -c 'import lightgbm' 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { $lgbmOk = $true }
        } catch { $lgbmOk = $false }
    }
    if ($lgbmOk) {
        [void](Invoke-Step -Name 'C42_QUICK_LGBM' -TimeoutSec 900 -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c42_repro.py'), '--quick', '--model', 'lightgbm',
            '--symbol', 'BTCUSDT', '--db-path', $DuckDbPath,
            '--out', (Join-Path $RunDir 'c42_quick_lightgbm')))
    } else {
        Record-Step -Name 'C42_QUICK_LGBM' -Status 'SKIP' -Rc 0 -Dur 0 `
            -Detail 'lightgbm nicht installiert (optional; pip install -e .[vol])' -OptionalSkip $true
    }
}

# -- Gesamt-Summary: 1 Zeile je Schritt + Exit-Code ----------------------
$nOk = 0; $nFail = 0; $nSkip = 0
$summaryLines = @('-------- RUN_SHORT SUMMARY --------')
foreach ($r in $Script:Results) {
    $summaryLines += ($r.Name + ': ' + $r.Status + ' (' + $r.Detail + ')')
    if ($r.Status -eq 'OK') { $nOk++ }
    elseif ($r.Status -eq 'FAIL') { $nFail++ }
    elseif ($r.Status -eq 'SKIP' -and (-not $r.OptionalSkip)) { $nSkip++ }
}
$exitCode = 0
if ($nSkip -gt 0) { $exitCode = 2 }
if ($nFail -gt 0) { $exitCode = 1 }
$summaryLines += ("RUN_SHORT GESAMT: ok=$nOk fail=$nFail skip=$nSkip -> exit $exitCode | Ergebnisse: " + $RunDir)
$summaryLines | ForEach-Object { Write-Host $_ }
Set-Content -Path (Join-Path $RunDir 'summary.txt') -Value ($summaryLines -join "`r`n")
exit $exitCode
