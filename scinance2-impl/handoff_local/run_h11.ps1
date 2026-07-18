# ========================================================================
# run_h11.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-11)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h11.ps1
#
# H-11 = AnEn-Vol-Regime-Forecast vs. HAR-RV (IC-CLIM-1, 3-Tage-Horizont).
# KAPITALFREI: reines Mess-Gate (CRPS-Verteilungsvergleich), KEINE
# bps/Edge/PnL/Sharpe/Friction-Rechnung (Monetarisierung waere NEUE H-11b).
#
# WICHTIG - H-11 ist DATA-GATED (Registry: GESPERRT). Dieser Runner prueft
# ZUERST die Entsperr-Bedingung (lueckenlose done_days fuer bybit
# publicTrade UND rest.fundingRate, BTC+ETH, 2024-03-27..2026-03-26,
# >=730 Tage) - primaer per harvest_manifest.sqlite-Query, Partitions-
# Ordner-Scan nur als Fallback ohne Manifest. Ist sie NICHT erfuellt:
# sauberer SKIP mit Meldung "H-11 gesperrt - Manifest-Coverage <730 Tage,
# Entsperr-Bedingung nicht erfuellt" und Exit-Code 2 - KEIN Fehler, KEIN
# Datenlauf.
#
# Nach Entsperrung laeuft der volle Gate-Lauf: Tuning-Bereich
# L=2024-03-27..2025-09-30 (LOO-CRPS-Gewichte, Grid {0;0.5;1;1.5;2}^5,
# danach eingefroren), W1=2025-10-01..2026-03-26, W2=2026-03-27..2026-06-30,
# k=20, 30-Tage-Embargo, Block-Bootstrap (5 Tage, 1000 Reps),
# F-ANEN BH-FDR a=0.10. Gate-neutral - der gate-auditor urteilt.
#
# Schritte: H11_UNLOCK_CHECK -> H11_ANEN. Exit: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h11_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-11).
#
# Optionale Env-Overrides: HARVEST_DIR, H11_RESULTS_DIR,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel
# (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols    = 'BTCUSDT,ETHUSDT'
$TuneStart  = '2024-03-27'; $TuneEnd = '2025-09-30'
$W1Start    = '2025-10-01'; $W1End   = '2026-03-26'
$W2Start    = '2026-03-27'; $W2End   = '2026-06-30'
$UnlockStart= '2024-03-27'; $UnlockEnd = '2026-03-26'
$MinUnlock  = 730
$KAnalogs   = 20
$Embargo    = 30
$WeightGrid = '0,0.5,1,1.5,2'
$BlockLen   = 5
$Bootstrap  = 1000
$Seed       = 42
$TmoCheck   = 300    # 5 min Budget fuer den Entsperr-Check
$TmoStep    = 3600   # 60 min Budget fuer den vollen Lauf (3125 Gewichts-Kombos)

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
$ResultsBase = if ($env:H11_RESULTS_DIR) { $env:H11_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("h11_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h11') | Out-Null
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
                $detail = "TIMEOUT nach $TimeoutSec s"
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

Write-Host ("RUN_H11 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Symbole: " + $Symbols + " | DATA-GATED (Entsperr-Check zuerst)")
Write-Host ("L=" + $TuneStart + ".." + $TuneEnd + " | W1=" + $W1Start + ".." + $W1End + " | W2=" + $W2Start + ".." + $W2End + " | k=" + $KAnalogs + " Embargo=" + $Embargo + "d seed=" + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# Junction-Pruefung (Vorbild run_h05b_oos.ps1).
$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags
# (Vorbild run_h08.ps1; NICHT den run_h05c-Bug wiederholen).
$CliScript = Join-Path $RepoRoot 'scripts\c11_anen.py'
$Locked = $false

if (-not $HarvestOk) {
    Record-Step -Name 'H11_UNLOCK_CHECK' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
    $Locked = $true
} else {
    # Schritt 1: Entsperr-Bedingung pruefen (rc 0 = entsperrt, rc 2 = gesperrt).
    $rcUnlock = Invoke-Step -Name 'H11_UNLOCK_CHECK' -TimeoutSec $TmoCheck -OkRcs @(0) -SkipRcs @(2) -CmdArgs @(
        $CliScript,
        '--check-unlock-only',
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--unlock-start', $UnlockStart, '--unlock-end', $UnlockEnd,
        '--min-unlock-days', "$MinUnlock"
    )
    if ($rcUnlock -eq 2) { $Locked = $true }
    elseif ($rcUnlock -ne 0) {
        Write-Host "FEHLER: Entsperr-Check fehlgeschlagen - kein Lauf."
    }
}

if ($Locked) {
    Write-Host ""
    Write-Host "H-11 gesperrt - Manifest-Coverage <730 Tage, Entsperr-Bedingung nicht erfuellt"
    Write-Host "(lueckenlose done_days bybit publicTrade + rest.fundingRate, BTC+ETH,"
    Write-Host (" " + $UnlockStart + ".." + $UnlockEnd + " noetig). Kein Datenlauf, kein Gate-Urteil.")
    Record-Step -Name 'H11_ANEN' -Status 'SKIP' -Rc 2 -Dur 0 -Detail 'H-11 gesperrt - Entsperr-Bedingung nicht erfuellt'
} elseif (($Script:Results | Where-Object { $_.Name -eq 'H11_UNLOCK_CHECK' -and $_.Status -eq 'OK' }).Count -gt 0) {
    # Schritt 2: voller Gate-Lauf (nur nach bestandenem Entsperr-Check).
    [void](Invoke-Step -Name 'H11_ANEN' -TimeoutSec $TmoStep -OkRcs @(0) -SkipRcs @(2) -CmdArgs @(
        $CliScript,
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--tune-start', $TuneStart, '--tune-end', $TuneEnd,
        '--w1-start', $W1Start, '--w1-end', $W1End,
        '--w2-start', $W2Start, '--w2-end', $W2End,
        '--unlock-start', $UnlockStart, '--unlock-end', $UnlockEnd,
        '--min-unlock-days', "$MinUnlock",
        '--k', "$KAnalogs", '--embargo-days', "$Embargo",
        '--weight-grid', $WeightGrid,
        '--block-len', "$BlockLen", '--n-bootstrap', "$Bootstrap",
        '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h11')
    ))
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-11 AnEn-Vol-Regime-Forecast vs. HAR-RV Mess-Gate - T2 (data-gated)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Entsperr-Bedingung:** lueckenlose done_days (Manifest-Query, Ordner-Scan-Fallback) publicTrade + rest.fundingRate, BTC+ETH, " + $UnlockStart + ".." + $UnlockEnd + " (>=" + $MinUnlock + " Tage)")
[void]$sb.AppendLine("- **Fenster:** L=" + $TuneStart + ".." + $TuneEnd + " (Tuning) | W1=" + $W1Start + ".." + $W1End + " | W2=" + $W2Start + ".." + $W2End)
[void]$sb.AppendLine("- **Methode:** k=" + $KAnalogs + ", Embargo " + $Embargo + "d, Grid {" + $WeightGrid + "}^5 eingefroren, Block-Bootstrap " + $BlockLen + "d x " + $Bootstrap + " | F-ANEN BH-FDR a=0.10")
[void]$sb.AppendLine("- **KAPITALFREI** - reines Mess-Gate, KEINE bps/Edge/PnL/Sharpe/Friction-Rechnung.")
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
if ($Locked) {
    [void]$sb.AppendLine("**H-11 gesperrt - Manifest-Coverage <" + $MinUnlock + " Tage, Entsperr-Bedingung nicht erfuellt.**")
    [void]$sb.AppendLine("Kein Datenlauf, kein Gate-Urteil. Erneut pruefen, sobald der Deep-Backfill")
    [void]$sb.AppendLine("die Range " + $UnlockStart + ".." + $UnlockEnd + " abdeckt (siehe README_H11.md).")
} else {
    [void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-11 (Roh-JSON unter ``h11\c11_anen_results.json``).")
    [void]$sb.AppendLine("WEITER verlangt: fuer >=1 Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS>=0.05 UND")
    [void]$sb.AppendLine("Block-Bootstrap-p<=0.05 nach BH-FDR a=0.10 ueber F-ANEN. Hartes Ein-Fenster-DROP,")
    [void]$sb.AppendLine("kein GRAUBEREICH, keine k-/Gewichts-/Feature-Nachsuche. A-priori: DROP")
    [void]$sb.AppendLine("(HAR-RV ist ein notorisch harter Benchmark). Ergebnisse hochladen -> Gate-Log.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
