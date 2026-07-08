# ========================================================================
# run_h12.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-12)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 20-40 min -- rechenintensiv
# wegen 2 Fenster x 1000 MC-Replikationen je Tag):
#   powershell -ExecutionPolicy Bypass -File .\run_h12.ps1
#
# H-12 = C-12-FRAG Cross-Exchange-Fragmentierungsmatrix (RMT/MP-IPR, F-FRAG).
# 6-Serien-Minuten-Panel (BTC/ETH x Bybit/Binance/Deribit), Tagesfenster
# (UTC, T=1440), Korrelationsmatrix-Eigenzerlegung je gueltigem Tag.
# Nullhypothese zweistufig: (a) MC-Gaussian-Wishart-Referenz (1000 Ziehungen,
# NICHT urteilstragend), (b) Ein-Faktor-Gauss-Null je Tag (1000 Replikationen,
# urteilstragend). EINE F-FRAG BH-FDR-Familie ueber BEIDE Fenster.
# KAPITALFREI: reine Mess-/Explorationsfrage, KEINE bps/PnL/Sharpe/Friction.
#
# Datenbasis (Registry H-12, vorregistriert): read-only Harvester-Baum ueber
# die Junction data\harvest. 6 Serien = 2 Symbole (BTCUSDT, ETHUSDT) x
# 3 Boersen (bybit, binance, deribit) publicTrade. Deribit-Notation
# BTC-PERPETUAL/ETH-PERPETUAL (panel.DERIBIT_SYMBOL_MAP).
# Fenster (identisch H-09): W1 = 2026-03-27..2026-05-15,
#                            W2 = 2026-05-16..2026-07-04.
# Tag gueltig >=1380/1440 gueltige Minuten je Serie (Forward-Fill <=1 min).
#
# EIN Block: H12_FRAG. Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h12_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-12).
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols   = 'BTCUSDT,ETHUSDT'
$Exchanges = 'bybit,binance,deribit'
$WinAStart = '2026-03-27'
$WinAEnd   = '2026-05-15'
$WinBStart = '2026-05-16'
$WinBEnd   = '2026-07-04'
$NMc       = 1000
$Seed      = 42
$TmoStep   = 2400   # 40 min Budget (rechenintensiv: 2 Fenster x 1000 MC-Reps/Tag)

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h12_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h12') | Out-Null
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

Write-Host ("RUN_H12 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Panel: " + $Symbols + " x {" + $Exchanges + "}")
Write-Host ("Fenster: W1 " + $WinAStart + ".." + $WinAEnd + " | W2 " + $WinBStart + ".." + $WinBEnd + " | n_mc=" + $NMc + " seed=" + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# Junction-Pruefung: alle DREI Boersen-Pfade muessen existieren (6-Serien-Panel).
$HarvestOk = $true
$bybitPath   = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$binancePath = Join-Path $HarvestDir 'raw\binance\publicTrade'
$deribitPath = Join-Path $HarvestDir 'raw\deribit\publicTrade'
if (-not $DryRun) {
    foreach ($pair in @(@('bybit', $bybitPath), @('binance', $binancePath), @('deribit', $deribitPath))) {
        if (-not (Test-Path $pair[1])) {
            $HarvestOk = $false
            Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $pair[1] + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
        }
    }
}

if (-not $HarvestOk) {
    Record-Step -Name 'H12_FRAG' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $bybitPath + " / " + $binancePath + " / " + $deribitPath + ")")
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
    [void](Invoke-Step -Name 'H12_FRAG' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c12_frag.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols, '--exchanges', $Exchanges,
        '--window-a-start', $WinAStart, '--window-a-end', $WinAEnd,
        '--window-b-start', $WinBStart, '--window-b-end', $WinBEnd,
        '--n-mc', "$NMc", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h12')
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
[void]$sb.AppendLine("# H-12 Cross-Exchange-Fragmentierungsmatrix Mess-Gate (RMT/MP-IPR) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Panel: " + $Symbols + " x {" + $Exchanges + "}")
[void]$sb.AppendLine("- **Fenster:** W1 " + $WinAStart + ".." + $WinAEnd + " | W2 " + $WinBStart + ".." + $WinBEnd + " (identisch H-09)")
[void]$sb.AppendLine("- **n_mc=" + $NMc + " (Stufe a + Stufe b) | seed=" + $Seed + " | F-FRAG BH-FDR a=0.10**")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Mess-/Explorationsfrage, KEINE bps/PnL/Sharpe/Friction.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-12 (Roh-JSON unter ``h12\c12_frag_results.json``).")
[void]$sb.AppendLine("WEITER verlangt in BEIDEN Fenstern: (a) Anteil gueltiger Tage mit lambda2 nach BH-FDR")
[void]$sb.AppendLine("alpha=0.10 ueber F-FRAG signifikant ueber der Ein-Faktor-Null >=20% UND (b) Median-IPR(v2)")
[void]$sb.AppendLine("ueber den FDR-signifikanten Tagen >=0.40 UND (c) an >=70% der FDR-signifikanten Tage")
[void]$sb.AppendLine("groesste v2^2-Boersenlast auf derselben Boerse. Validitaets-Vorbedingung (KEIN Gate-")
[void]$sb.AppendLine("Bestandteil): IPR(v1)<=0.25 an >=90% der gueltigen Tage UND >=35 gueltige Tage je Fenster")
[void]$sb.AppendLine("- sonst Lauf UNGUELTIG (kein Verdikt, NICHT DROP). Hartes Ein-Fenster-DROP sonst, kein")
[void]$sb.AppendLine("Graubereich. A-priori: DROP erwartet. Ergebnisse hochladen -> GL-Zaehlung.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
