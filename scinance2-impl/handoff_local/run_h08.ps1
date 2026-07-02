# ========================================================================
# run_h08.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 3, H-08)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 10-30 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h08.ps1
#
# H-08 = C-06 Cross-Sectional MR mit RANG-Ueber-Dehnung (DEC-18).
# Achse A (NEU, schwellen-frei): je Bar das EINE extremste Symbol
# i* = argmax |z| (Gleichstand: alphabetisch erstes Symbol, deterministisch).
# KEIN Magnitude-Schwellwert (jede |z|-Schwelle < 2.5 waere eine verkappte
# Z_THRESH-Absenkung). Achse B (Crash-Dezil) UNVERAENDERT aus H-07/DEC-17.
# KAPITALFREI: reiner Mess-/Verstaerkungs-Test, KEINE bps/Edge/PnL/Sharpe/Friction.
#
# Datenbasis (DEC-15/DEC-17/DEC-18, vorregistriert): read-only Harvester-
# Backfill ueber die Junction data\harvest. 5-Symbol-Panel BTC/ETH/SOL/BNB/XRP,
# zwei disjunkte Kalender-Fenster (je 2 Kalendertage):
#   Fenster A: ab 2026-04-15 00:00 UTC
#   Fenster B: ab 2026-05-15 00:00 UTC
# 5-min-Last-Price-Bars, kontemporaer synchronisiert (forward-fill <=1 Bar).
# L=12 Bars, Crash-Dezil 0.9, Horizonte {1,3,6} Bars, N-Floor 30,
# Surrogates 200, F-XMR-RANK BH-FDR a=0.10. Gate-neutral - gate-auditor urteilt.
#
# EIN Block: H08_XMR_RANK. Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h08_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-08).
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols   = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$WinAStart = '2026-04-15'
$WinBStart = '2026-05-15'
$CalDays   = 2
$BarMin    = 5
$Lookback  = 12
$CrashDec  = 0.9
$Horizons  = '1,3,6'
$Surrogates= 200
$Bootstrap = 1000
$NFloor    = 30
$Seed      = 42
$TmoStep   = 2400   # 40 min Budget

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h08_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h08') | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{ Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail })
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
    if ($rc -eq 0) { $status = 'OK' }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_H08 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Panel: " + $Symbols)
Write-Host ("Fenster A: " + $WinAStart + " | Fenster B: " + $WinBStart + " | Horizonte=" + $Horizons + " | Achse A=RANG (argmax |z|, schwellen-frei) N-Floor=" + $NFloor + " seed=" + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# Junction-Pruefung.
$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

if (-not $HarvestOk) {
    Record-Step -Name 'H08_XMR_RANK' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
    [void](Invoke-Step -Name 'H08_XMR_RANK' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c06_xmr.py'),
        '--overextension', 'rank',
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--window-a-start', $WinAStart, '--window-b-start', $WinBStart,
        '--calendar-days', "$CalDays", '--bar-min', "$BarMin",
        '--lookback-bars', "$Lookback",
        '--crash-decile', "$CrashDec", '--horizons', $Horizons,
        '--n-surrogates', "$Surrogates", '--n-bootstrap', "$Bootstrap",
        '--n-floor', "$NFloor", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h08')
    ))
}

# -- Zusammenfassung -----------------------------------------------------
$ok = ($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = ($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = ($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-08 C-06 Cross-Sectional MR mit RANG-Ueber-Dehnung Mess-Gate - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Panel: " + $Symbols)
[void]$sb.AppendLine("- **Fenster (DEC-15):** A@" + $WinAStart + " + B@" + $WinBStart + ", je " + $CalDays + " Kalendertage | 5-min-Bars")
[void]$sb.AppendLine("- **Achse A: RANG (argmax |z| je Bar, schwellen-frei, DEC-18) | L=" + $Lookback + " Crash-Dezil=" + $CrashDec + " Horizonte " + $Horizons + " N-Floor=" + $NFloor + " | F-XMR-RANK BH-FDR a=0.10**")
[void]$sb.AppendLine("- **KAPITALFREI** - reiner Mess-/Verstaerkungs-Test, KEINE bps/Edge/PnL/Sharpe/Friction.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-08 (Roh-JSON unter ``h08\c06_xmr_results.json``).")
[void]$sb.AppendLine("WEITER verlangt: konditioniert mu_rev>0 UND p<=0.05 (BH-FDR F-XMR-RANK) UND >=2-Fenster-")
[void]$sb.AppendLine("Konsistenz UND nicht-ueberlappende 95%-CIs (konditioniert > Baseline) fuer >=1 Horizont in")
[void]$sb.AppendLine(">=2 Fenstern UND N>=30/Fenster. Nicht-Trivialitaets-Anker traegt die GESAMTE Beweislast")
[void]$sb.AppendLine("(Rang-1 feuert jede Bar = Verduennung; die unkonditionierte Trivial-MR, E-04-/PRD-6-verboten,")
[void]$sb.AppendLine("zaehlt NIE als Erfolg). Hartes Ein-Fenster-DROP, kein GRAUBEREICH. A-priori: DROP.")
[void]$sb.AppendLine("Ergebnisse hochladen -> GL-013.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
