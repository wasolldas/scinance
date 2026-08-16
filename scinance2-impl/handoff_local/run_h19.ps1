# ========================================================================
# run_h19.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 6, H-19)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h19.ps1
#
# H-19 = DRIFT: Stationaritaet der Tape-Struktur ueber Kalenderzeit.
# META/AUDIT (H-18-Muster): beide Zweige informativ, KEIN WEITER/DROP.
# Drei Tages-Deskriptoren (lag-1-AC der 1-min-Renditen, Varianz-Signatur
# RV5/RV1, Herfindahl der Minutenvolumina) gegen den Tagesindex,
# konditioniert auf log-RV und log-Volumen (partieller Spearman).
# BEFUND-Regel (magnitudengetrieben, vorregistriert): |rho_p| >= 0,30 in
# BEIDEN OOS-Fenstern mit gleichem Vorzeichen. p-Werte nicht
# urteilstragend (bei N~550 ueberpowert - H-07-Spiegel-Lehre).
#
# Liest AUSSCHLIESSLICH den WP-0-Bar-Cache (data\barcache) - KEIN
# Roh-Tick-Zugriff (DEC-34). Die registrierten Cache-Fingerabdruecke
# werden VOR der Messung geprueft; Abweichung -> rc=3, gate_valid=false.
#
# KAPITALFREI: reine Messung, keine bps/Edge/PnL/Friction-Rechnung.
#
# Schritte: H19_DRIFT. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (Cache fehlt) *
#           3 = Fingerprint-Mismatch (Befund nicht tragfaehig).
# Ergebnisse: scinance2-impl\handoff_local\results\h19_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor protokolliert den Befund).
#
# Optionale Env-Overrides: BARCACHE_DIR, H19_RESULTS_DIR, H19_TIMEOUT_SEC,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$CacheDir  = if ($env:BARCACHE_DIR) { $env:BARCACHE_DIR } else { Join-Path $RepoRoot 'data\barcache' }

$Symbols = 'BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,BNBUSDT'
# CPU; Panel liegt im Cache, Rotation-Null 1000x je Zelle -> Minuten bis ~1 h.
$TmoStep = if ($env:H19_TIMEOUT_SEC) { [int]$env:H19_TIMEOUT_SEC } else { 7200 }

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
$ResultsBase = if ($env:H19_RESULTS_DIR) { $env:H19_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("h19_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h19') | Out-Null
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

Write-Host ("RUN_H19 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Bar-Cache: " + $CacheDir + " (WP-0, read-only) | Symbole: " + $Symbols)
Write-Host "Fingerprint-Pruefung VOR der Messung; META/AUDIT - kein WEITER/DROP."
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$CacheOk = $true
$barsPath = Join-Path $CacheDir 'bars_1min'
if ((-not $DryRun) -and (-not (Test-Path $barsPath))) {
    $CacheOk = $false
    Write-Host ("WARNUNG: Bar-Cache fehlt (" + $barsPath + ") - erst run_wp0_barcache.ps1 ausfuehren oder BARCACHE_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\c19_drift.py'
$rcRun = 2
if (-not $CacheOk) {
    Record-Step -Name 'H19_DRIFT' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Bar-Cache fehlt (" + $barsPath + ")")
} else {
    $rcRun = Invoke-Step -Name 'H19_DRIFT' -TimeoutSec $TmoStep -OkRcs @(0) -CmdArgs @(
        $CliScript,
        '--cache-dir', $CacheDir,
        '--symbols', $Symbols,
        '--out-dir', (Join-Path $RunDir 'h19')
    )
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($rcRun -eq 3) { $exit = 3 } elseif ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-19 DRIFT Stationaritaets-Messung (Welle 6) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Bar-Cache:** ``" + $CacheDir + "`` (WP-0, read-only) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Semantik:** META/AUDIT (H-18-Muster) - kein WEITER/DROP; jeder DRIFT-BEFUND loest die registrierte Regime-Splitting-Auflage fuer nachfolgende Welle-6-Auswertungen aus.")
[void]$sb.AppendLine("- **Befund-Regel:** |rho_p| >= 0,30 in BEIDEN OOS-Fenstern, gleiches Vorzeichen (magnitudengetrieben; p nicht urteilstragend).")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Messung.")
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
if ($exit -eq 3) {
    [void]$sb.AppendLine("**LAUT-FEHLER: Cache-Fingerabdruecke stimmen nicht mit der Registrierung ueberein.**")
    [void]$sb.AppendLine("``gate_valid=false`` - Befund NICHT tragfaehig. Cache-Stand pruefen (neu gebaut? falscher Pfad?).")
} elseif ($exit -eq 2) {
    [void]$sb.AppendLine("**SKIP** - Bar-Cache nicht gefunden. Erst run_wp0_barcache.ps1 ausfuehren.")
} elseif ($exit -eq 1) {
    [void]$sb.AppendLine("**FEHLER** - ``H19_DRIFT.err.log`` pruefen.")
} else {
    [void]$sb.AppendLine("*Befund unter ``h19\c19_drift_results.{json,md}``. Der gate-auditor protokolliert den")
    [void]$sb.AppendLine("META/AUDIT-Befund im Gate-Log (kein WEITER/DROP); DRIFT-Befunde binden nachfolgende")
    [void]$sb.AppendLine("Welle-6-Auswertungen an regime-gesplittete Berichterstattung. Ergebnisse hochladen.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
