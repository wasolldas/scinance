# ========================================================================
# run_h05b_oos.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 3, H-05b OOS)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 10-30 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h05b_oos.ps1
#
# H-05b = C-01 OFI-Vorzeichen INVERSE Lesart (MM-Replenishment), OOS-Konfirmation.
# KAPITALFREI: reiner Vorzeichen-/Korrelations-Mess-Test, KEINE bps/Edge/PnL.
#
# Datenbasis (DEC-15, vorregistriert): read-only Harvester-Backfill ueber die
# Junction data\harvest. Zwei disjunkte OOS-Fenster, je 300k Ticks/Symbol:
#   Fenster A: ab 2026-04-15 00:00 UTC
#   Fenster B: ab 2026-05-15 00:00 UTC
# Sauberes Backfill (weit vor der ~06-15 Backfill/Live-Grenze), Entdeckungszelle
# (ETHUSDT Juni w0 d1s) per Konstruktion ausgeschlossen.
#
# Symbole BTC/ETH/SOL/BNB/XRP, delta {1,5,15,60,300}s, F-OFI-INV BH-FDR a=0.10.
# Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h05b_oos_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-05b).
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
$MaxTicks  = 300000
$Surrogates= 200
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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h05b_oos_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h05b') | Out-Null
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

Write-Host ("RUN_H05B_OOS (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Symbole: " + $Symbols)
Write-Host ("Fenster A: " + $WinAStart + " | Fenster B: " + $WinBStart + " | max_ticks=" + $MaxTicks + " | surrogates=" + $Surrogates + " seed=" + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# Junction-Pruefung.
$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

if (-not $HarvestOk) {
    Record-Step -Name 'H05B_OOS' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
} else {
    [void](Invoke-Step -Name 'H05B_OOS' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c01_ofi_sign_oos.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--window-a-start', $WinAStart, '--window-b-start', $WinBStart,
        '--max-ticks', "$MaxTicks", '--n-surrogates', "$Surrogates", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h05b')
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
[void]$sb.AppendLine("# H-05b OOS-Konfirmation (C-01 inverse OFI-Vorzeichen) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction)")
[void]$sb.AppendLine("- **Fenster (DEC-15, vorregistriert):** A@" + $WinAStart + " + B@" + $WinBStart + ", je " + $MaxTicks + " Ticks/Symbol")
[void]$sb.AppendLine("- **Symbole:** " + $Symbols + " | delta {1,5,15,60,300}s | F-OFI-INV BH-FDR a=0.10")
[void]$sb.AppendLine("- **KAPITALFREI** - Entdeckungszelle (ETHUSDT Juni w0 d1s) per Konstruktion ausgeschlossen.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-05b (Roh-JSON unter ``h05b\h05b_oos_results.json``).")
[void]$sb.AppendLine("WEITER (inverse Mess-Existenz) verlangt: sign=- UND p<=0.05 (BH-FDR F-OFI-INV) UND inverse-")
[void]$sb.AppendLine("Konsistenz in >=2 disjunkten Fenstern UND |corr|>=0.05 ODER Hit-Rate<=0.47. Hartes Ein-")
[void]$sb.AppendLine("Fenster-DROP, kein GRAUBEREICH. Symmetrie-Falle: weder positiv (H-05) noch negativ -> beide")
[void]$sb.AppendLine("Lesarten verworfen, KEIN H-05c.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
