# ========================================================================
# run_overnight.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 1, WP-5)
#
# Aufruf (keine Pflicht-Parameter, laeuft UNBEAUFSICHTIGT ueber Nacht, ~8h+):
#   powershell -ExecutionPolicy Bypass -File .\run_overnight.ps1
#
# Vorher Standby deaktivieren (sonst schlaeft der Rechner ein):
#   powercfg /change standby-timeout-ac 0
#
# Bloecke (jeder einzeln gekapselt: try/catch + Timeout + weitermachen,
# NIE ein offener Prompt):
#   RECORDER_LONG    Recorder-Dauertest im Hintergrund (Default 8h, Cap 50 GB)
#   C42_WF_<sym>     C-42 Voll-Walk-Forward je Symbol (BTC/ETH/SOL/BNB/XRP),
#                    Modell lightgbm mit har-Fallback wenn Import scheitert
#   C31_CFAR_<sym>   C-31 CFAR auf echten Ticks (DuckDB-trades, 200 Surrogates,
#                    2 disjunkte Fenster) je Symbol
#   REPLAY_ITER5     NUR Hinweis: replay_all.py (12h-Replays) wird bewusst
#                    NICHT automatisch gestartet - User-Entscheidung
#   RECORDER_CHECK   Parquet/Row-Count/Schema-Version + Storage-Deckel
#   SUMMARY          aggregate_results.py -> results\SUMMARY_<yyyy-mm-dd>.md
#
# Exit-Code: 0 = alle OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl\handoff_local\results\overnight_<timestamp>\
#             + results\SUMMARY_<datum>.md (Morgen-Auswertung gate-auditor)
#
# Optionale Env-Overrides: HANDOFF_RECORDER_HOURS, HANDOFF_RECORDER_CAP_GB,
# HANDOFF_DUCKDB, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel.
# ========================================================================
$ErrorActionPreference = 'Continue'

# -- Pfade (bei Bedarf HIER anpassen - siehe README_RUN.md) --------------
$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
# Lokale DuckDB mit kline_1min/trades. Default = Repo-ueblicher Pfad aus
# persistence/db.py (DATA_DIR/bybit_edge.duckdb). Override: $env:HANDOFF_DUCKDB.
$DuckDbPath = if ($env:HANDOFF_DUCKDB) { $env:HANDOFF_DUCKDB } else { Join-Path $RepoRoot 'data\bybit_edge.duckdb' }
$E15Results = Join-Path $RepoRoot 'edge_research_framework\results\replay_all_results.json'

$RecorderHours = 8
if ($env:HANDOFF_RECORDER_HOURS) { $RecorderHours = [double]$env:HANDOFF_RECORDER_HOURS }
$RecorderCapGb = 50
if ($env:HANDOFF_RECORDER_CAP_GB) { $RecorderCapGb = [double]$env:HANDOFF_RECORDER_CAP_GB }
$RecorderDurationS = [int]($RecorderHours * 3600)
$Symbols = @('BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT')
$C31Windows = 2
$C31Surrogates = 200

# -- Umgebung -------------------------------------------------------------
$PythonExe = if ($env:PYTHON) { $env:PYTHON } else { 'python' }
$SrcPath = Join-Path $RepoRoot 'src'
$env:PYTHONPATH = if ($env:PYTHONPATH) { $SrcPath + ';' + $env:PYTHONPATH } else { $SrcPath }
if (-not $env:BYBIT_DATA_DIR) { $env:BYBIT_DATA_DIR = Join-Path $RepoRoot 'data' }
Set-Location $RepoRoot
# Ressourcen-Disziplin: eigener Prozess niedrig - Kindprozesse erben die Klasse.
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch { }

$DryRun = ($env:HANDOFF_DRY_RUN -and ($env:HANDOFF_DRY_RUN -ne '0'))
$DryRc  = 0
if ($env:HANDOFF_DRY_RC) { $DryRc = [int]$env:HANDOFF_DRY_RC }

$Ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("overnight_" + $Ts)
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

# Gekapselter Schritt: try/catch + ExitCode-Pruefung + Timeout (Kill).
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
            try { $p.PriorityClass = 'BelowNormal' } catch { }
            if (-not $p.WaitForExit($TimeoutSec * 1000)) {
                try { $p.Kill() } catch { }
                $rc = 124
                $detail = "TIMEOUT nach $TimeoutSec s"
            } else {
                $rc = $p.ExitCode
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

Write-Host ("RUN_OVERNIGHT (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Recorder: " + $RecorderHours + "h, Cap " + $RecorderCapGb + " GB | DuckDB: " + $DuckDbPath)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# -- Block 1: Recorder-Dauertest im Hintergrund starten ------------------
$RecProc = $null
$RecT0 = Get-Date
if (-not $DryRun) {
    try {
        $RecProc = Start-Process -FilePath $PythonExe -ArgumentList @(
            '-m', 'bybit_edge.recorder',
            '--duration', "$RecorderDurationS", '--cap-gb', "$RecorderCapGb"
        ) -NoNewWindow -PassThru `
          -RedirectStandardOutput (Join-Path $RunDir 'RECORDER_LONG.log') `
          -RedirectStandardError (Join-Path $RunDir 'RECORDER_LONG.err.log')
        try { $RecProc.PriorityClass = 'BelowNormal' } catch { }
        Write-Host ("RECORDER_LONG gestartet (PID " + $RecProc.Id + ", " + $RecorderDurationS + "s)")
    } catch {
        Record-Step -Name 'RECORDER_LONG' -Status 'FAIL' -Rc -1 -Dur 0 `
            -Detail ("Start fehlgeschlagen: " + $_.Exception.Message)
        $RecProc = $null
    }
}

# -- Block 2: C-42 Voll-Walk-Forward multi-symbol -------------------------
$C42Model = 'lightgbm'
if (-not $DryRun) {
    $lgbmOk = $false
    try {
        & $PythonExe -c 'import lightgbm' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $lgbmOk = $true }
    } catch { $lgbmOk = $false }
    if (-not $lgbmOk) {
        $C42Model = 'har'
        Write-Host 'lightgbm-Import scheitert -> har-Fallback (DEC-04; pip install -e .[vol] fuer Reproduktions-Treue)'
    }
}
if ((-not $DryRun) -and (-not (Test-Path $DuckDbPath))) {
    Record-Step -Name 'C42_WF' -Status 'SKIP' -Rc 0 -Dur 0 `
        -Detail ("DuckDB fehlt (" + $DuckDbPath + ") - Pfad oben im Skript / HANDOFF_DUCKDB anpassen")
} else {
    foreach ($sym in $Symbols) {
        $rc = Invoke-Step -Name ("C42_WF_" + $sym) -TimeoutSec 7200 -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c42_repro.py'), '--model', $C42Model,
            '--symbol', $sym, '--n-folds', '3', '--db-path', $DuckDbPath,
            '--out', (Join-Path $RunDir ('c42_' + $sym)))
        if (($rc -eq 2) -and ($C42Model -ne 'har')) {
            # Modell-Dependency fehlte zur Laufzeit doch -> einmaliger har-Fallback.
            [void](Invoke-Step -Name ("C42_WF_" + $sym + "_HARFB") -TimeoutSec 7200 -CmdArgs @(
                (Join-Path $RepoRoot 'scripts\c42_repro.py'), '--model', 'har',
                '--symbol', $sym, '--n-folds', '3', '--db-path', $DuckDbPath,
                '--out', (Join-Path $RunDir ('c42_' + $sym))))
        }
    }
}

# -- Block 3: C-31 CFAR auf echten Ticks (DuckDB-trades) ------------------
if ((-not $DryRun) -and (-not (Test-Path $DuckDbPath))) {
    Record-Step -Name 'C31_CFAR' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
} else {
    foreach ($sym in $Symbols) {
        [void](Invoke-Step -Name ("C31_CFAR_" + $sym) -TimeoutSec 5400 -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c31_cfar.py'), '--db', $DuckDbPath,
            '--symbol', $sym, '--windows', "$C31Windows",
            '--surrogates', "$C31Surrogates",
            '--out', (Join-Path $RunDir ('c31_' + $sym))))
    }
}

# -- Block 4: Hinweis iter-5-Replay (bewusst NICHT automatisch starten) ---
if (Test-Path $E15Results) {
    Record-Step -Name 'REPLAY_ITER5' -Status 'INFO' -Rc 0 -Dur 0 `
        -Detail 'iter-5-Ergebnisse vorhanden - E-15-Auswertung laeuft im run_short (Schritt E15_EVAL)'
} else {
    Record-Step -Name 'REPLAY_ITER5' -Status 'INFO' -Rc 0 -Dur 0 `
        -Detail 'iter-5-Replay fehlt noch: scripts/replay_all.py separat starten (12h) - Runner startet das bewusst NICHT (User-Entscheidung)'
}

# -- Block 5: Auf Recorder warten, dann pruefen (inkl. Storage-Deckel) ----
if ($DryRun) {
    $st = 'FAIL'; if ($DryRc -eq 0) { $st = 'OK' }
    Record-Step -Name 'RECORDER_LONG' -Status $st -Rc $DryRc -Dur 0 -Detail ("dry-run rc=" + $DryRc)
} elseif ($RecProc) {
    try {
        $elapsed = [int]((Get-Date) - $RecT0).TotalSeconds
        $remaining = $RecorderDurationS + 600 - $elapsed
        if ($remaining -lt 60) { $remaining = 60 }
        if (-not $RecProc.WaitForExit($remaining * 1000)) {
            try { $RecProc.Kill() } catch { }
            Record-Step -Name 'RECORDER_LONG' -Status 'FAIL' -Rc 124 `
                -Dur ([int]((Get-Date) - $RecT0).TotalSeconds) `
                -Detail 'TIMEOUT: lief nach duration+600s noch - gekillt'
        } else {
            $recRc = $RecProc.ExitCode
            $st = 'FAIL'; if ($recRc -eq 0) { $st = 'OK' }
            Record-Step -Name 'RECORDER_LONG' -Status $st -Rc $recRc `
                -Dur ([int]((Get-Date) - $RecT0).TotalSeconds) -Detail ("rc=" + $recRc)
        }
    } catch {
        Record-Step -Name 'RECORDER_LONG' -Status 'FAIL' -Rc -1 `
            -Dur ([int]((Get-Date) - $RecT0).TotalSeconds) -Detail $_.Exception.Message
    }
}

$RecAgeMin = [int]($RecorderDurationS / 60 + 120)
[void](Invoke-Step -Name 'RECORDER_CHECK' -TimeoutSec 300 -CmdArgs @(
    (Join-Path $ScriptDir 'check_recording.py'), '--max-age-min', "$RecAgeMin",
    '--cap-gb', "$RecorderCapGb", '--json', (Join-Path $RunDir 'recording_check.json')))

# -- Block 6: SUMMARY_<datum>.md aggregieren (Morgen-Auswertung) ----------
$SummaryDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$aggRc = Invoke-Step -Name 'SUMMARY' -TimeoutSec 300 -CmdArgs @(
    (Join-Path $ScriptDir 'aggregate_results.py'), '--run-dir', $RunDir,
    '--label', 'overnight', '--date', $SummaryDate)
if ($aggRc -ne 0) {
    Write-Host ("WARNUNG: SUMMARY-Aggregation fehlgeschlagen - Roh-JSONs liegen in " + $RunDir)
}

# -- Gesamt-Summary: 1 Zeile je Block + Exit-Code -------------------------
$nOk = 0; $nFail = 0; $nSkip = 0
$summaryLines = @('-------- RUN_OVERNIGHT SUMMARY --------')
foreach ($r in $Script:Results) {
    $summaryLines += ($r.Name + ': ' + $r.Status + ' (' + $r.Detail + ')')
    if ($r.Status -eq 'OK') { $nOk++ }
    elseif ($r.Status -eq 'FAIL') { $nFail++ }
    elseif ($r.Status -eq 'SKIP' -and (-not $r.OptionalSkip)) { $nSkip++ }
}
$exitCode = 0
if ($nSkip -gt 0) { $exitCode = 2 }
if ($nFail -gt 0) { $exitCode = 1 }
$summaryLines += ("RUN_OVERNIGHT GESAMT: ok=$nOk fail=$nFail skip=$nSkip -> exit $exitCode | Ergebnisse: " + $RunDir)
$summaryLines | ForEach-Object { Write-Host $_ }
Set-Content -Path (Join-Path $RunDir 'summary.txt') -Value ($summaryLines -join "`r`n")
exit $exitCode
