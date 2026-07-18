# ========================================================================
# run_h13.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-13)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 5-30 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h13.ps1
#
# H-13 = Tail-Form-Konsistenz: statistisches GPD-xi (xi_P, POT auf 1-min-
# Verlusten, Bybit-Perp publicTrade) vs. risikoneutraler Tail-Shape (xi_Q,
# Deribit markprice.options -> SVI -> Breeden-Litzenberger-RND -> GPD-PWM).
# KAPITALFREI: reine Mess-/Konsistenzfrage, KEINE Kosten-/Ertragsrechnung.
# DATA-GATED / GESPERRT: Entsperr-Bedingung sind 2 vol-regime-disjunkte
# Live-IV-Snapshot-Tage D1<D2 (|log(RV_5d-Ratio)|>=log(1.5), >=10 Kalender-
# tage Abstand, je Tag/Symbol >=12 Strikes mit 0.01<=|Delta|<=0.5 im
# 20-45-DTE-Tenor). Die D1/D2-Suche laeuft PROGRAMMATISCH (kein Hartcoden);
# ohne gueltiges Paar -> sauberer SKIP, kein Fit, kein Gate-Urteil.
#
# Ablauf: (1) H13_UNLOCK_CHECK via --check-unlock-only (rc 2 = gesperrt ->
# SKIP), (2) nur bei rc 0: H13_TAILSHAPE voller Lauf (500 Bootstrap-Reps
# je Seite, Seed 42, F-TAILSHAPE BH-FDR a=0.10). Gate-neutral - der
# gate-auditor urteilt gegen H-13.
#
# Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP (H-13 gesperrt).
# Ergebnisse: scinance2-impl\handoff_local\results\h13_<timestamp>\
#             + SUMMARY_<datum>.md.
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols   = 'BTC,ETH'
$Bootstrap = 500
$TrailDays = 60
$SnapHour  = 8
$Seed      = 42
$TmoUnlock = 900    # 15 min Budget fuer die D1/D2-Suche
$TmoFull   = 3600   # 60 min Budget fuer den vollen Lauf

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h13_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h13') | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{ Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail })
}

function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs, [string]$SkipDetail)
    # rc 2 des CLI = H-13 gesperrt -> Status SKIP (kein FAIL).
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
    elseif ($rc -eq 2) { $status = 'SKIP'; if ($SkipDetail) { $detail = $SkipDetail } }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_H13 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Symbole: " + $Symbols + " | Bootstrap=" + $Bootstrap + " Seed=" + $Seed)
Write-Host ("H-13 ist DATA-GATED: erst deterministische D1/D2-Suche, dann (nur bei Entsperrung) voller Lauf.")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$SkipMsg = 'H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage im Live-Fenster gefunden'

# Pfad-Pruefung: beide Datenseiten muessen existieren.
$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$optPath   = Join-Path $HarvestDir 'raw\deribit\markprice.options'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}
if ((-not $DryRun) -and (-not (Test-Path $optPath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Options-Pfad fehlt (" + $optPath + ") - Live-Fenster markprice.options pruefen")
}

if (-not $HarvestOk) {
    Record-Step -Name 'H13_UNLOCK_CHECK' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester-/Options-Pfad fehlt (" + $tradePath + " / " + $optPath + ")")
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-rc=2-Bug meiden).
    $rcUnlock = Invoke-Step -Name 'H13_UNLOCK_CHECK' -TimeoutSec $TmoUnlock -SkipDetail $SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c13_tailshape.py'),
        '--check-unlock-only',
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--snapshot-hour', "$SnapHour", '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h13')
    )
    if ($rcUnlock -eq 0) {
        [void](Invoke-Step -Name 'H13_TAILSHAPE' -TimeoutSec $TmoFull -SkipDetail $SkipMsg -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c13_tailshape.py'),
            '--base-dir', $HarvestDir, '--symbols', $Symbols,
            '--n-bootstrap', "$Bootstrap", '--trailing-days', "$TrailDays",
            '--snapshot-hour', "$SnapHour", '--seed', "$Seed",
            '--out-dir', (Join-Path $RunDir 'h13')
        ))
    } elseif ($rcUnlock -eq 2) {
        Write-Host ("SKIP: " + $SkipMsg)
    }
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-13 Tail-Form-Konsistenz xi_P vs. xi_Q Mess-Gate - T2 (data-gated)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Methodik (vorregistriert):** POT 99.5%-Quantil / GPD-MLE / 60-min-Block-Bootstrap / Hill; SVI -> BL-RND -> GPD-PWM / Strike-Bootstrap; Tenor 20-45 DTE, Delta 0.01-0.5, " + $Bootstrap + " Reps, Seed " + $Seed + " | F-TAILSHAPE BH-FDR a=0.10")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Mess-/Konsistenzfrage, KEINE Kosten-/Ertragsrechnung.")
[void]$sb.AppendLine("- **DATA-GATED** - Entsperr-Bedingung (waechst mit Kalenderzeit, wird NICHT gesenkt): 2 Snapshot-Tage D1<D2 mit |log(RV_5d-Ratio)|>=log(1.5), >=10 Tage Abstand, je >=12 Strikes im Delta-Band.")
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
if ($exit -eq 2) {
    [void]$sb.AppendLine("*SKIP: " + $SkipMsg + ". H-13 bleibt GESPERRT - kein Fit, kein Gate-Urteil.*")
} else {
    [void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-13 (Roh-JSON unter ``h13\c13_tailshape_results.json``).")
    [void]$sb.AppendLine("WEITER verlangt: fuer >=1 Symbol in {BTC,ETH} an BEIDEN Snapshot-Tagen sign(Delta_xi)")
    [void]$sb.AppendLine("identisch UND |Delta_xi|>=0.15 UND Bootstrap-p<=0.05 nach BH-FDR a=0.10 ueber F-TAILSHAPE")
    [void]$sb.AppendLine("UND Hill-Gegenprobe widerspricht dem GPD-Vorzeichen nicht. DROP sonst (hartes")
    [void]$sb.AppendLine("Ein-Fenster-/Ein-Tag-Kriterium, kein GRAUBEREICH; u_P, Tenor-Band, RND-Quantil und 0.15")
    [void]$sb.AppendLine("nicht verhandelbar). Ergebnisse hochladen -> Morgen-Auswertung.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
