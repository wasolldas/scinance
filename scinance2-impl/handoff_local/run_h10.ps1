# ========================================================================
# run_h10.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-10)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 5-20 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h10.ps1
#
# H-10 = C-10 Cross-Stream-Pointer-Days + Pre-Event-Drift (F-POINTER).
# Stufe 1: Pointer-Tage (>=60% von 30 Serien gleichzeitig |Cropper-C|>=1.5
# gleicher Richtung, n_avail>=18) vs. zirkulaere Surrogat-Null (1000/Serie).
# Stufe 2: Pre-Event-Drift des GEHALTENEN Deribit-dvol-Index (BTC+ETH,
# NIE in der Detektion) 1-5 Tage VOR Pointer-Tagen vs. Permutations-Null
# (1000 Ziehungen, >=6 Tage Abstand zu jedem Pointer-Tag).
# KAPITALFREI: reine Mess-/Existenzfrage, KEINE Kapital-Metriken.
#
# Datenbasis (Registry H-10, vorregistriert): read-only Harvester-Baum ueber
# die Junction data\harvest. 30 Detektions-Serien = 5 Perp-Symbole x
# {bybit,binance} x {RV(publicTrade), Funding(rest.fundingRate),
# dlogOI(rest.openInterest)}; Hold-out deribit/dvol Symbole BTC+ETH.
# Tagesraster 2026-03-27..2026-07-04, Burn-in 21 Tage,
#   W1: 2026-04-17..2026-05-25 (39 Tage)
#   W2: 2026-05-26..2026-07-04 (40 Tage)
# Surrogate/Permutationen 1000/1000, F-POINTER BH-FDR a=0.10.
# Gate-neutral - gate-auditor urteilt.
#
# EIN Block: H10_POINTER. Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h10_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-10).
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols    = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$DataStart  = '2026-03-27'
$DataEnd    = '2026-07-04'
$BurnIn     = 21
$W1Start    = '2026-04-17'
$W1End      = '2026-05-25'
$W2Start    = '2026-05-26'
$W2End      = '2026-07-04'
$Surrogates = 1000
$Permut     = 1000
$Seed       = 42
$TmoStep    = 2400   # 40 min Budget

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h10_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h10') | Out-Null
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

Write-Host ("RUN_H10 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Panel: " + $Symbols + " x {bybit,binance} x {RV,Funding,dlogOI} | Hold-out deribit/dvol BTC+ETH")
Write-Host ("Raster: " + $DataStart + ".." + $DataEnd + " (Burn-in " + $BurnIn + ") | W1 " + $W1Start + ".." + $W1End + " | W2 " + $W2Start + ".." + $W2End + " | surr/perm " + $Surrogates + "/" + $Permut + " seed=" + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

# Junction-Pruefung: Detektions- UND Hold-out-Pfad muessen existieren.
$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$dvolPath  = Join-Path $HarvestDir 'raw\deribit\dvol'
if (-not $DryRun) {
    if (-not (Test-Path $tradePath)) {
        $HarvestOk = $false
        Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
    }
    if (-not (Test-Path $dvolPath)) {
        $HarvestOk = $false
        Write-Host ("WARNUNG: Hold-out-Pfad fehlt (" + $dvolPath + ") - deribit dvol wird fuer Stufe 2 zwingend gebraucht")
    }
}

if (-not $HarvestOk) {
    Record-Step -Name 'H10_POINTER' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester/Hold-out fehlt (" + $tradePath + " / " + $dvolPath + ")")
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
    [void](Invoke-Step -Name 'H10_POINTER' -TimeoutSec $TmoStep -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c10_pointer.py'),
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--data-start', $DataStart, '--data-end', $DataEnd,
        '--burn-in-days', "$BurnIn",
        '--w1-start', $W1Start, '--w1-end', $W1End,
        '--w2-start', $W2Start, '--w2-end', $W2End,
        '--n-surrogates', "$Surrogates", '--n-permutations', "$Permut",
        '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h10')
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
[void]$sb.AppendLine("# H-10 C-10 Cross-Stream-Pointer-Days + Pre-Event-Drift Mess-Gate - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Panel: " + $Symbols + " x {bybit,binance} x {RV,Funding,dlogOI}")
[void]$sb.AppendLine("- **Hold-out (NIE in Detektion):** deribit/dvol BTC+ETH")
[void]$sb.AppendLine("- **Raster:** " + $DataStart + ".." + $DataEnd + " (Burn-in " + $BurnIn + ") | W1 " + $W1Start + ".." + $W1End + " | W2 " + $W2Start + ".." + $W2End)
[void]$sb.AppendLine("- **Surrogate/Permutationen " + $Surrogates + "/" + $Permut + " | F-POINTER BH-FDR a=0.10 | N-Floor 3 (NICHT absenkbar)**")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Mess-/Existenzfrage, KEINE Kapital-Metriken.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-10 (Roh-JSON unter ``h10\c10_pointer_results.json``).")
[void]$sb.AppendLine("WEITER verlangt nach BH-FDR a=0.10 ueber F-POINTER ALLE 4 Zellen: Stufe-1-Surrogat-p<=0.05")
[void]$sb.AppendLine("in W1 UND W2 UND N_pointer>=3 je Fenster (Floor NICHT absenkbar) UND Stufe-2-Permutations-")
[void]$sb.AppendLine("p<=0.05 (zweiseitig) in W1 UND W2. Hartes Ein-Fenster-DROP, kein GRAUBEREICH.")
[void]$sb.AppendLine("A-priori: Stufe 1 WEITER-nah, Stufe 2 DROP erwartet. Ergebnisse hochladen -> GL-Zaehlung.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
