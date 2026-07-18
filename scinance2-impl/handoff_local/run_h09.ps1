# ========================================================================
# run_h09.ps1 - T2 LOCAL Runner (Scinance 2.0 Welle 4, H-09)
#
# Aufruf (keine Pflicht-Parameter, laeuft je nach Datenvolumen 15-90 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h09.ps1
#
# H-09 = Risk-Limit-Tier-Bunching (F-BUNCH, DEC-19, KAPITALFREI).
# Taker-Order-Aggregate (konsekutive publicTrade-Records gleichen
# symbol/side/ts_exchange_ms gemerged) -> Notional-Binning um die Tier-1-
# Kante K_s (Band [0.4,1.3)*K_s, 90 Bins a 0.01*K_s) -> Polynom-Grad-7-
# Counterfactual (Ausschluss [0.90,1.10)*K_s) -> Excess-Mass b- (B- =
# [0.95,1.00)*K_s) vs b+ (B+ = (1.00,1.05]*K_s) -> Residuen-Bootstrap
# (500 Reps) -> Placebos 0.50/0.75*K_s (NICHT in FDR-Familie).
# KAPITALFREI: reiner Struktur-/Verhaltensfakt, KEINE Kosten-/Handelsspalten.
#
# !!! K_s-PLATZHALTER-WARNUNG: nur BTCUSDT=2.000.000 USDT ist registry-
# beziffert; ETH/SOL/BNB/XRP sind PLATZHALTER (src/bybit_edge/research/
# c09_bunch/kinks.py) - vor echtem Lauf gegen die aktuelle Bybit-Risk-
# Limit-Tabelle verifizieren (Konstanz ueber W1+W2!), DEC-09-Muster,
# datierter append-only Operationalisierungs-Nachtrag erforderlich. !!!
#
# Datenbasis (Registry H-09, vorregistriert): read-only Harvester-Backfill
# ueber die Junction data\harvest. 5-Symbol-Panel BTC/ETH/SOL/BNB/XRP,
# zwei disjunkte Kalender-Fenster:
#   W1: 2026-03-27 .. 2026-05-15
#   W2: 2026-05-16 .. 2026-07-04
# N-Floor: >=2.000 Order-Beobachtungen im Band UND Counterfactual-
# Erwartung in B- >=50, sonst Zelle ungueltig. F-BUNCH = 5 Symbole x 2
# Fenster (Order-Level), BH-FDR a=0.10. Gate-neutral - gate-auditor urteilt.
#
# EIN Block: H09_BUNCH. Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h09_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-09).
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols   = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$WinAStart = '2026-03-27'
$WinAEnd   = '2026-05-15'
$WinBStart = '2026-05-16'
$WinBEnd   = '2026-07-04'
$Bootstrap = 500
$Seed      = 42
$TmoStep   = 7200   # 120 min Budget (Laden von ~100 Tagen publicTrade dominiert)

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h09_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h09') | Out-Null
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

Write-Host ("RUN_H09 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Panel: " + $Symbols)
Write-Host ("W1: " + $WinAStart + ".." + $WinAEnd + " | W2: " + $WinBStart + ".." + $WinBEnd + " | Bootstrap=" + $Bootstrap + " Seed=" + $Seed)
Write-Host "K_s-PLATZHALTER: ETH/SOL/BNB/XRP unverifiziert (kinks.py) - vor echtem Gate-Urteil Nachtrag noetig!"
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# Junction-Pruefung.
$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

if (-not $HarvestOk) {
    Record-Step -Name 'H09_BUNCH' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
    [void](Invoke-Step -Name 'H09_BUNCH' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c09_bunch.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--window-a-start', $WinAStart, '--window-a-end', $WinAEnd,
        '--window-b-start', $WinBStart, '--window-b-end', $WinBEnd,
        '--n-bootstrap', "$Bootstrap", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h09')
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
[void]$sb.AppendLine("# H-09 Risk-Limit-Tier-Bunching Mess-Gate (F-BUNCH) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Panel: " + $Symbols)
[void]$sb.AppendLine("- **Fenster (Registry H-09):** W1 " + $WinAStart + ".." + $WinAEnd + " + W2 " + $WinBStart + ".." + $WinBEnd)
[void]$sb.AppendLine("- **Methodik:** Order-Aggregat | Band [0.4,1.3)*K_s, 90 Bins | Polynom Grad 7 (Ausschluss [0.9,1.1)) | B-/B+ | Residuen-Bootstrap " + $Bootstrap + " | Placebos 0.5/0.75*K_s | F-BUNCH BH-FDR a=0.10 | N-Floor 2000/50")
[void]$sb.AppendLine("- **K_s-PLATZHALTER:** ETH/SOL/BNB/XRP unverifiziert (kinks.py) - vor Gate-Urteil append-only Nachtrag (DEC-09-Muster) + Konstanz-Pruefung ueber W1+W2 noetig; nur BTCUSDT=2.000.000 USDT registry-beziffert.")
[void]$sb.AppendLine("- **KAPITALFREI** - reiner Struktur-/Verhaltensfakt; Tradability waere NEUE H-09b.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-09 (Roh-JSON unter ``h09\c09_bunch_results.json``).")
[void]$sb.AppendLine("WEITER verlangt fuer >=1 Symbol in BEIDEN Fenstern (gueltige Zelle): Bootstrap-p<=0.05 nach")
[void]$sb.AppendLine("BH-FDR a=0.10 ueber F-BUNCH UND b->=1.0 UND b- - b+>=0.5 UND b- > max(b_P1,b_P2).")
[void]$sb.AppendLine("N-Floor: >=2.000 Order-Beobachtungen im Schaetzband UND Counterfactual-Erwartung in B- >=50,")
[void]$sb.AppendLine("sonst Zelle ungueltig; alle 5 Zellen eines Fensters ungueltig -> DROP wegen Power (keine")
[void]$sb.AppendLine("Floor-Absenkung). Hartes Ein-Fenster-DROP, kein GRAUBEREICH. A-priori: DROP (Rundzahl-")
[void]$sb.AppendLine("Praeferenz). Ergebnisse hochladen -> GL-014ff. (erster Welle-4-Lauf).*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
