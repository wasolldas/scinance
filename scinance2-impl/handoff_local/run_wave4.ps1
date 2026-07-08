# ========================================================================
# run_wave4.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 4, Phase E)
#
# Aufruf (keine Pflicht-Parameter, laeuft UNBEAUFSICHTIGT):
#   powershell -ExecutionPolicy Bypass -File .\run_wave4.ps1
#
# Vorher Standby deaktivieren (sonst schlaeft der Rechner ein):
#   powercfg /change standby-timeout-ac 0
#
# Bloecke (jeder einzeln gekapselt: try/catch + Timeout + weitermachen,
# NIE ein offener Prompt):
#   H11_UNLOCK_CHECK  H-11 Entsperr-Check (--check-unlock-only; rc 2 = SKIP)
#   H13_UNLOCK_CHECK  H-13 Entsperr-Check (--check-unlock-only; rc 2 = SKIP)
#   H09               Risk-Limit-Tier-Bunching (F-BUNCH) - KAPITALFREI
#   H10               Cross-Stream-Pointer-Days (F-POINTER) - KAPITALFREI
#   H12               Cross-Exchange-Fragmentierung (F-FRAG, laengster Block)
#   H11 / H13         volle Laeufe NUR bei bestandenem Entsperr-Check
#   WAVE4_FDR         F-XDOM1 zweistufige BH-FDR-Aggregation (Registry/DEC-22)
#
# WICHTIG: H-11/H-13 sind GESPERRT registriert; ein SKIP mit Diagnose ist
# der ERWARTETE, korrekte Ausgang (kein Datenzugriff, kein Verdikt). Die
# Kohorten-Regel der Registry verlangt F-XDOM1 VOR diesem Lauf -
# registriert 2026-07-08 (hypothesis_registry.md, DEC-22).
#
# Exit-Code: 0 = alle Bloecke OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl\handoff_local\results\wave4_<timestamp>\
#             + WAVE4_SUMMARY.md + SUMMARY_<datum>.md (Morgen-Auswertung)
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# WAVE4_FDR laeuft auch im Dry-Run ECHT (reine lokale JSON-Aggregation ohne
# Datenzugriff) - WAVE4_SUMMARY.md entsteht IMMER.
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body + UTF-8-BOM).
# ========================================================================
$ErrorActionPreference = 'Continue'

# -- Pfade (bei Bedarf HIER anpassen - siehe README_WAVE4.md) ------------
$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

# Registrierte Default-Parameter (identisch zu den auditierten T2-Runnern
# run_h09/run_h10/run_h11/run_h12/run_h13 - KEINE Abweichung).
$Symbols5    = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$Symbols2    = 'BTCUSDT,ETHUSDT'
$SymbolsH13  = 'BTC,ETH'
$ExchangesH12 = 'bybit,binance,deribit'
$Seed        = 42
# H-09 (Registry-Fenster, identisch H-12):
$H09WaStart = '2026-03-27'; $H09WaEnd = '2026-05-15'
$H09WbStart = '2026-05-16'; $H09WbEnd = '2026-07-04'
$H09Boot    = 500
# H-10 (Tagesraster + Burn-in + Registry-Fenster):
$H10DataStart = '2026-03-27'; $H10DataEnd = '2026-07-04'; $H10BurnIn = 21
$H10W1Start = '2026-04-17'; $H10W1End = '2026-05-25'
$H10W2Start = '2026-05-26'; $H10W2End = '2026-07-04'
$H10Surr = 1000; $H10Perm = 1000
# H-11 (data-gated; Parameter nur fuer den Fall der Entsperrung):
$H11TuneStart = '2024-03-27'; $H11TuneEnd = '2025-09-30'
$H11W1Start = '2025-10-01';   $H11W1End = '2026-03-26'
$H11W2Start = '2026-03-27';   $H11W2End = '2026-06-30'
$H11UnlockStart = '2024-03-27'; $H11UnlockEnd = '2026-03-26'; $H11MinUnlock = 730
$H11K = 20; $H11Embargo = 30; $H11Grid = '0,0.5,1,1.5,2'
$H11Block = 5; $H11Boot = 1000
# H-12 (Registry-Fenster identisch H-09):
$H12NMc = 1000
# H-13 (data-gated; Parameter nur fuer den Fall der Entsperrung):
$H13Boot = 500; $H13TrailDays = 60; $H13SnapHour = 8

# Per-Schritt-Budgets (grosszuegig, aber endlich; CLAUDE.md T3-Regel).
# H-12 ist laut README_H12.md der rechenintensivste Block (1000 MC-Reps PRO
# gueltigem Tag, ~70-100 Tage => genannt 20-40 min, T2-Budget 2400 s) -
# hier mit ECHTER Marge auf 7200 s (2 h) gedeckelt.
$TmoUnlockH11 = 600    # 10 min
$TmoUnlockH13 = 900    # 15 min
$TmoH09 = 7200         # 120 min
$TmoH10 = 3600         # 60 min
$TmoH12 = 7200         # 120 min (laengster Block)
$TmoH11 = 3600         # 60 min - nur bei Entsperrung
$TmoH13 = 3600         # 60 min - nur bei Entsperrung
$TmoAgg = 600          # 10 min

# -- Umgebung ------------------------------------------------------------
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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("wave4_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
foreach ($sub in @('h09', 'h10', 'h11', 'h12', 'h13')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RunDir $sub) | Out-Null
}
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{
        Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail
    })
}

# Gekapselter Schritt: try/catch + ExitCode-Pruefung + Timeout (Kill).
# SkipRc: dieser Exit-Code zaehlt als SKIP statt FAIL (Entsperr-Checks:
# rc 2 = gesperrt). ForceReal: Schritt laeuft auch im Dry-Run echt (nur
# fuer die lokale F-XDOM1-Aggregation).
function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs,
          [int]$SkipRc = -999, [string]$SkipDetail = '',
          [switch]$ForceReal)
    $log = Join-Path $RunDir ($Name + '.log')
    $errLog = Join-Path $RunDir ($Name + '.err.log')
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] START " + $Name + ": " + $PythonExe + " " + ($CmdArgs -join ' '))
    $t0 = Get-Date
    $rc = -1
    $detail = ''
    if ($DryRun -and (-not $ForceReal)) {
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
    elseif ($rc -eq $SkipRc) {
        $status = 'SKIP'
        if ($SkipDetail) { $detail = $SkipDetail }
    }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_WAVE4 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " (read-only Junction) | Seed: " + $Seed)
Write-Host "Kohorte: H-09 + H-10 + H-12 (F-XDOM1 vorregistriert, DEC-22)"
Write-Host "Data-gated: H-11 + H-13 (Entsperr-Check zuerst; SKIP = erwarteter Ausgang)"
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Modul-Laeufe (Aggregation laeuft echt)." }

# Datenpfade (je Modul die Pfade der auditierten T2-Runner):
$TradePath        = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$BinanceTradePath = Join-Path $HarvestDir 'raw\binance\publicTrade'
$DeribitTradePath = Join-Path $HarvestDir 'raw\deribit\publicTrade'
$DvolPath         = Join-Path $HarvestDir 'raw\deribit\dvol'
$BinanceFundPath  = Join-Path $HarvestDir 'raw\binance\rest.fundingRate'
$BinanceOiPath    = Join-Path $HarvestDir 'raw\binance\rest.openInterest'
$OptPath          = Join-Path $HarvestDir 'raw\deribit\markprice.options'

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags
# (Vorbild run_h08..run_h13; NICHT den run_h05c-Bug wiederholen).

# -- Block 1: H-11 Entsperr-Check (DATA-GATED, GESPERRT registriert) ------
$H11SkipMsg = "H-11 gesperrt - Manifest-Coverage <$H11MinUnlock Tage, Entsperr-Bedingung nicht erfuellt"
$H11Locked = $true
if ((-not $DryRun) -and (-not (Test-Path $TradePath))) {
    Record-Step -Name 'H11_UNLOCK_CHECK' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester-Pfad fehlt (" + $TradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
} else {
    $rcU11 = Invoke-Step -Name 'H11_UNLOCK_CHECK' -TimeoutSec $TmoUnlockH11 -SkipRc 2 -SkipDetail $H11SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c11_anen.py'),
        '--check-unlock-only',
        '--base-dir', $HarvestDir, '--symbols', $Symbols2,
        '--unlock-start', $H11UnlockStart, '--unlock-end', $H11UnlockEnd,
        '--min-unlock-days', "$H11MinUnlock")
    if ($rcU11 -eq 0) { $H11Locked = $false }
}

# -- Block 2: H-13 Entsperr-Check (DATA-GATED, GESPERRT registriert) ------
$H13SkipMsg = 'H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage im Live-Fenster gefunden'
$H13Locked = $true
if ((-not $DryRun) -and ((-not (Test-Path $TradePath)) -or (-not (Test-Path $OptPath)))) {
    Record-Step -Name 'H13_UNLOCK_CHECK' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester-/Options-Pfad fehlt (" + $TradePath + " / " + $OptPath + ")")
} else {
    $rcU13 = Invoke-Step -Name 'H13_UNLOCK_CHECK' -TimeoutSec $TmoUnlockH13 -SkipRc 2 -SkipDetail $H13SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c13_tailshape.py'),
        '--check-unlock-only',
        '--base-dir', $HarvestDir, '--symbols', $SymbolsH13,
        '--snapshot-hour', "$H13SnapHour", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h13'))
    if ($rcU13 -eq 0) { $H13Locked = $false }
}

# -- Block 3: H-09 Risk-Limit-Tier-Bunching (Kohorte) ---------------------
# K_s-PLATZHALTER-WARNUNG: nur BTCUSDT registry-beziffert; ETH/SOL/BNB/XRP
# Platzhalter (kinks.py) - der Driver setzt gate_valid_assumptions korrekt.
if ((-not $DryRun) -and (-not (Test-Path $TradePath))) {
    Record-Step -Name 'H09' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester-Pfad fehlt (" + $TradePath + ")")
} else {
    [void](Invoke-Step -Name 'H09' -TimeoutSec $TmoH09 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c09_bunch.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols5,
        '--window-a-start', $H09WaStart, '--window-a-end', $H09WaEnd,
        '--window-b-start', $H09WbStart, '--window-b-end', $H09WbEnd,
        '--n-bootstrap', "$H09Boot", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h09')))
}

# -- Block 4: H-10 Cross-Stream-Pointer-Days (Kohorte) --------------------
# Alle 4 Datenpfade noetig (audit_h10 BUG-5): bybit-Detektion, dvol-Hold-out,
# binance funding + OI.
if ((-not $DryRun) -and ((-not (Test-Path $TradePath)) -or (-not (Test-Path $DvolPath)) `
        -or (-not (Test-Path $BinanceFundPath)) -or (-not (Test-Path $BinanceOiPath)))) {
    Record-Step -Name 'H10' -Status 'SKIP' -Rc 0 -Dur 0 -Detail "Harvester-/Hold-out-Pfad fehlt (bybit publicTrade / deribit dvol / binance fundingRate / binance openInterest)"
} else {
    [void](Invoke-Step -Name 'H10' -TimeoutSec $TmoH10 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c10_pointer.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols5,
        '--data-start', $H10DataStart, '--data-end', $H10DataEnd,
        '--burn-in-days', "$H10BurnIn",
        '--w1-start', $H10W1Start, '--w1-end', $H10W1End,
        '--w2-start', $H10W2Start, '--w2-end', $H10W2End,
        '--n-surrogates', "$H10Surr", '--n-permutations', "$H10Perm",
        '--seed', "$Seed", '--out-dir', (Join-Path $RunDir 'h10')))
}

# -- Block 5: H-12 Cross-Exchange-Fragmentierung (Kohorte, laengster Block)
if ((-not $DryRun) -and ((-not (Test-Path $TradePath)) -or (-not (Test-Path $BinanceTradePath)) `
        -or (-not (Test-Path $DeribitTradePath)))) {
    Record-Step -Name 'H12' -Status 'SKIP' -Rc 0 -Dur 0 -Detail "Harvester-Pfad fehlt (bybit/binance/deribit publicTrade)"
} else {
    [void](Invoke-Step -Name 'H12' -TimeoutSec $TmoH12 -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c12_frag.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols2, '--exchanges', $ExchangesH12,
        '--window-a-start', $H09WaStart, '--window-a-end', $H09WaEnd,
        '--window-b-start', $H09WbStart, '--window-b-end', $H09WbEnd,
        '--n-mc', "$H12NMc", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h12')))
}

# -- Block 6: H-11 voller Lauf - NUR bei bestandenem Entsperr-Check -------
if ($H11Locked) {
    Record-Step -Name 'H11' -Status 'SKIP' -Rc 2 -Dur 0 -Detail "H-11 gesperrt - Entsperr-Bedingung nicht erfuellt (kein Datenlauf, kein Gate-Urteil; erwarteter Ausgang)"
} else {
    [void](Invoke-Step -Name 'H11' -TimeoutSec $TmoH11 -SkipRc 2 -SkipDetail $H11SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c11_anen.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols2,
        '--tune-start', $H11TuneStart, '--tune-end', $H11TuneEnd,
        '--w1-start', $H11W1Start, '--w1-end', $H11W1End,
        '--w2-start', $H11W2Start, '--w2-end', $H11W2End,
        '--unlock-start', $H11UnlockStart, '--unlock-end', $H11UnlockEnd,
        '--min-unlock-days', "$H11MinUnlock",
        '--k', "$H11K", '--embargo-days', "$H11Embargo",
        '--weight-grid', $H11Grid,
        '--block-len', "$H11Block", '--n-bootstrap', "$H11Boot",
        '--seed', "$Seed", '--out-dir', (Join-Path $RunDir 'h11')))
}

# -- Block 7: H-13 voller Lauf - NUR bei bestandenem Entsperr-Check -------
if ($H13Locked) {
    Record-Step -Name 'H13' -Status 'SKIP' -Rc 2 -Dur 0 -Detail "H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage (kein Fit, kein Gate-Urteil; erwarteter Ausgang)"
} else {
    [void](Invoke-Step -Name 'H13' -TimeoutSec $TmoH13 -SkipRc 2 -SkipDetail $H13SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c13_tailshape.py'),
        '--base-dir', $HarvestDir, '--symbols', $SymbolsH13,
        '--n-bootstrap', "$H13Boot", '--trailing-days', "$H13TrailDays",
        '--snapshot-hour', "$H13SnapHour", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h13')))
}

# -- Block 8: F-XDOM1 zweistufige BH-FDR-Aggregation ----------------------
# Laeuft IMMER echt (auch im Dry-Run und bei fehlenden Driver-Outputs):
# reine lokale JSON-Aggregation ohne Datenzugriff; fehlende Driver werden
# als Luecke im Bericht dokumentiert, nie als Absturz.
[void](Invoke-Step -Name 'WAVE4_FDR' -TimeoutSec $TmoAgg -ForceReal -CmdArgs @(
    (Join-Path $ScriptDir 'aggregate_wave4_fdr.py'),
    '--h09', (Join-Path $RunDir 'h09'),
    '--h10', (Join-Path $RunDir 'h10'),
    '--h12', (Join-Path $RunDir 'h12'),
    '--out', (Join-Path $RunDir 'WAVE4_SUMMARY.md'),
    '--json', (Join-Path $RunDir 'wave4_summary.json'),
    '--label', ("wave4_" + $Ts)))

# -- SUMMARY_<datum>.md (T3-Konvention, immer geschrieben) ----------------
$nOk = 0; $nFail = 0; $nSkip = 0
foreach ($r in $Script:Results) {
    if ($r.Status -eq 'OK') { $nOk++ }
    elseif ($r.Status -eq 'FAIL') { $nFail++ }
    elseif ($r.Status -eq 'SKIP') { $nSkip++ }
}
$exitCode = 0
if ($nSkip -gt 0) { $exitCode = 2 }
if ($nFail -gt 0) { $exitCode = 1 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
# Markdown-Header ohne '#'-Literal in Strings (Lint: Kommentar-Strip vor
# String-Strip, siehe test_aggregate_wave4_fdr.py brace/paren-Balance).
$Hash = [string][char]35
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine($Hash + " Welle-4-Kohorten-Lauf (H-09/H-10/H-12 + Entsperr-Checks H-11/H-13) - T3")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "`` | Harvest ``" + $HarvestDir + "`` (read-only Junction)")
[void]$sb.AppendLine("- **Kohorte:** H-09 (F-BUNCH) + H-10 (F-POINTER) + H-12 (F-FRAG); Ueber-Familie F-XDOM1")
[void]$sb.AppendLine("  (zweite BH-FDR alpha=0.10 ueber die Stage-1-Survivor, Registry-Eintrag F-XDOM1/DEC-22,")
[void]$sb.AppendLine("  VOR diesem Lauf registriert). Eine Hypothese besteht nur, wenn sie BEIDE Stufen ueberlebt.")
[void]$sb.AppendLine("- **Data-gated:** H-11 + H-13 - Entsperr-Check via --check-unlock-only; gesperrt -> sauberer")
[void]$sb.AppendLine("  SKIP ohne Datenzugriff (erwarteter Ausgang, kein Fehler, kein Verdikt).")
[void]$sb.AppendLine("- **KAPITALFREI** - alle 5 Module sind reine Mess-Gates ohne bps/Edge/PnL/Friction-Rechnung.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine($Hash + $Hash + " Schritte")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Schritt | Status | rc | Dauer | Detail |")
[void]$sb.AppendLine("|---|---|---:|---:|---|")
foreach ($r in $Script:Results) {
    [void]$sb.AppendLine("| " + $r.Name + " | " + $r.Status + " | " + $r.Rc + " | " + $r.Dur + "s | " + $r.Detail + " |")
}
[void]$sb.AppendLine("")
[void]$sb.AppendLine("**Gesamt:** ok=" + $nOk + " fail=" + $nFail + " skip=" + $nSkip + " -> exit " + $exitCode)
[void]$sb.AppendLine("")
[void]$sb.AppendLine("*F-XDOM1-Aggregat: ``WAVE4_SUMMARY.md`` + ``wave4_summary.json`` (gate-neutral, KEIN")
[void]$sb.AppendLine("Gesamturteil). Gate-Urteile faellt der gate-auditor gegen H-09/H-10/H-12 unter der")
[void]$sb.AppendLine("Beide-Stufen-Regel; Roh-JSONs unter h09\, h10\, h12\ (h11\, h13\ nur bei Entsperrung).")
[void]$sb.AppendLine("Ergebnisse hochladen -> GL-014ff. (erster Welle-4-Lauf).*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

# -- Gesamt-Summary: 1 Zeile je Block + Exit-Code ------------------------
$summaryLines = @('-------- RUN_WAVE4 SUMMARY --------')
foreach ($r in $Script:Results) {
    $summaryLines += ($r.Name + ': ' + $r.Status + ' (' + $r.Detail + ')')
}
$summaryLines += ("RUN_WAVE4 GESAMT: ok=$nOk fail=$nFail skip=$nSkip -> exit $exitCode | Ergebnisse: " + $RunDir)
$summaryLines += ("F-XDOM1-Aggregat: " + (Join-Path $RunDir 'WAVE4_SUMMARY.md') + " (Morgen-Auswertung gate-auditor)")
$summaryLines += ("SUMMARY: " + $SummaryPath)
$summaryLines | ForEach-Object { Write-Host $_ }
Set-Content -Path (Join-Path $RunDir 'summary.txt') -Value ($summaryLines -join "`r`n")
exit $exitCode
