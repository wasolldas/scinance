# ========================================================================
# run_cfar_only.ps1 - H-03-Notausgang (Scinance 2.0 Welle 1, WP-3)
#
# Standalone-Runner NUR fuer C-31 CFAR ueber alle 5 Symbole (BTC/ETH/SOL/
# BNB/XRP). Gedacht als 1-2h-Schnelldurchgang falls run_overnight kippt:
# H-03 bleibt der einzige unbeschiedene Welle-1-Pilot, daher dieser Pfad
# (overnight-Defekt 2026-06-13: Block 3 wurde nie erreicht; Hauptrunner
# starb zwischen Block 2 und Block 3).
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_cfar_only.ps1
#
# Macht NUR:
#   C31_CFAR_<sym>   C-31 CFAR auf DuckDB-trades mit --db-copy
#                    (lock-frei, 30s Open-Timeout im Driver)
#                    Default-Parameter wie run_overnight (Windows 2,
#                    Surrogates 200, Seed 42); Pro-Symbol-Timeout 1800s.
#
# Exit-Code: 0 = alle OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl\handoff_local\results\cfar_<timestamp>\
#             + SUMMARY.md (eigenes Mini-Summary nur fuer H-03)
#
# Optionale Env-Overrides:
#   HANDOFF_DUCKDB=<pfad>    HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC)
# PS 5.1-kompatibel + ASCII + UTF-8 BOM.
# ========================================================================
$ErrorActionPreference = 'Continue'

# -- Pfade ---------------------------------------------------------------
$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$DuckDbPath = if ($env:HANDOFF_DUCKDB) { $env:HANDOFF_DUCKDB } else { Join-Path $RepoRoot 'data\bybit_edge.duckdb' }

$Symbols = @('BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT')
$C31Windows = 2
$C31Surrogates = 200
$C31MaxTicks = 150000   # DEC-09: deterministische Tick-Obergrenze je Fenster
$C31TimeoutSec = 1800   # 30 min/Symbol - mit Tick-Cap + --db-copy reichlich

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("cfar_" + $Ts)
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

Write-Host ("RUN_CFAR_ONLY (H-03 Notausgang) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("DuckDB: " + $DuckDbPath + " | windows=" + $C31Windows + " surrogates=" + $C31Surrogates + " timeout=" + $C31TimeoutSec + "s/symbol")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# -- C31 CFAR je Symbol --------------------------------------------------
if ((-not $DryRun) -and (-not (Test-Path $DuckDbPath))) {
    foreach ($sym in $Symbols) {
        Record-Step -Name ("C31_CFAR_" + $sym) -Status 'SKIP' -Rc 0 -Dur 0 `
            -Detail ("DuckDB fehlt (" + $DuckDbPath + ") - HANDOFF_DUCKDB setzen")
    }
} else {
    foreach ($sym in $Symbols) {
        # --max-ticks-per-window (DEC-09): juengste windows x max-ticks Ticks je
        # Symbol -> rechenbar + stationaer (Gate-Schwellen UNVERAENDERT).
        [void](Invoke-Step -Name ("C31_CFAR_" + $sym) -TimeoutSec $C31TimeoutSec -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c31_cfar.py'), '--db', $DuckDbPath,
            '--symbol', $sym, '--windows', "$C31Windows",
            '--surrogates', "$C31Surrogates",
            '--max-ticks-per-window', "$C31MaxTicks", '--db-copy',
            '--out', (Join-Path $RunDir ('c31_' + $sym))))
    }
}

# -- Mini-Summary (eigene SUMMARY.md fuer H-03) --------------------------
$nOk = 0; $nFail = 0; $nSkip = 0
foreach ($r in $Script:Results) {
    if ($r.Status -eq 'OK') { $nOk++ }
    elseif ($r.Status -eq 'FAIL') { $nFail++ }
    elseif ($r.Status -eq 'SKIP' -and (-not $r.OptionalSkip)) { $nSkip++ }
}
$exitCode = 0
if ($nSkip -gt 0) { $exitCode = 2 }
if ($nFail -gt 0) { $exitCode = 1 }

$summaryLines = @('-------- RUN_CFAR_ONLY SUMMARY --------')
foreach ($r in $Script:Results) {
    $summaryLines += ($r.Name + ': ' + $r.Status + ' (' + $r.Detail + ', ' + $r.Dur + 's)')
}
$summaryLines += ("RUN_CFAR_ONLY GESAMT: ok=$nOk fail=$nFail skip=$nSkip -> exit $exitCode | Ergebnisse: " + $RunDir)
$summaryLines | ForEach-Object { Write-Host $_ }
Set-Content -Path (Join-Path $RunDir 'summary.txt') -Value ($summaryLines -join "`r`n")

# SUMMARY.md (maschinen- und menschenlesbar fuer den gate-auditor)
$mdLines = @()
$mdLines += '# H-03 Notausgang - C-31 CFAR Runner'
$mdLines += ''
$mdLines += ("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + ' UTC')
$mdLines += ("- **Run-Dir:** ``" + $RunDir + '``')
$mdLines += ("- **DuckDB:** ``" + $DuckDbPath + '``')
$mdLines += ("- **Parameter:** windows=" + $C31Windows + ", surrogates=" + $C31Surrogates + ", --db-copy, timeout=" + $C31TimeoutSec + "s/symbol")
$mdLines += ''
$mdLines += '| Symbol | Status | rc | Dauer | Detail |'
$mdLines += '|---|---|---:|---:|---|'
foreach ($r in $Script:Results) {
    $mdLines += ('| ' + $r.Name + ' | ' + $r.Status + ' | ' + $r.Rc + ' | ' + $r.Dur + 's | ' + $r.Detail + ' |')
}
$mdLines += ''
$mdLines += ("**Gesamt:** ok=" + $nOk + " fail=" + $nFail + " skip=" + $nSkip + " -> exit " + $exitCode)
$mdLines += ''
$mdLines += '*H-03-Gate-Urteil faellt der gate-auditor gegen die Registry (Roh-JSONs je Symbol unter `c31_<symbol>/c31_cfar_results.json`).*'
Set-Content -Path (Join-Path $RunDir 'SUMMARY.md') -Value ($mdLines -join "`r`n") -Encoding UTF8

exit $exitCode
