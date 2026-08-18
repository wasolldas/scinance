# ========================================================================
# run_h22.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 6, H-22)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h22.ps1
#
# H-22 = L2-TILT: Tages-Buchneigung (Median der Minuten-Tilts, +-25 bp
# um Mid, aus dem WP-2-Store) gegen die Folgetags-Rendite (WP-0-Closes).
# Gate: BTC in BEIDEN L2-Fenstern Spearman-IC >= 0,10 UND Bootstrap-p
# <= 0,05 nach BH-FDR a=0,10 ueber F-L2; 85%-Abdeckungs-Floor je
# urteilstragendem Fenster (darunter SKIP, kein Verdikt); hartes
# Ein-Fenster-DROP. ETH ein Fenster, NUR Bericht. A-priori: DROP
# erwartet (Lane C woertlich).
#
# Liest die zwei unveraenderlichen Stores (data\l2tilt + data\barcache);
# BEIDE Fingerabdruecke werden VOR der Messung geprueft; Abweichung ->
# rc=3, gate_valid=false.
#
# KAPITALFREI: reine Messung, keine bps/Edge/PnL/Friction-Rechnung.
#
# Schritte: H22_L2TILT. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (Store fehlt
#           oder Abdeckungs-Floor verfehlt) * 3 = Fingerprint-Mismatch.
# Ergebnisse: scinance2-impl\handoff_local\results\h22_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor protokolliert den Befund).
#
# Optionale Env-Overrides: BARCACHE_DIR, L2TILT_DIR, H22_RESULTS_DIR, H22_TIMEOUT_SEC,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$CacheDir  = if ($env:BARCACHE_DIR) { $env:BARCACHE_DIR } else { Join-Path $RepoRoot 'data\barcache' }
$TiltDir   = if ($env:L2TILT_DIR) { $env:L2TILT_DIR } else { Join-Path $RepoRoot 'data\l2tilt' }

# CPU, Minuten (beide Stores liegen fertig auf Platte).
$TmoStep = if ($env:H22_TIMEOUT_SEC) { [int]$env:H22_TIMEOUT_SEC } else { 3600 }

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
$ResultsBase = if ($env:H22_RESULTS_DIR) { $env:H22_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("h22_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h22') | Out-Null
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

Write-Host ("RUN_H22 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Tilt-Store: " + $TiltDir + " (WP-2) + Bar-Cache: " + $CacheDir + " (WP-0), beide read-only")
Write-Host "Beide Fingerprints VOR der Messung geprueft; Gate-Urteil faellt der gate-auditor."
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$CacheOk = $true
$barsPath = Join-Path $CacheDir 'bars_1min'
$tiltPath = Join-Path $TiltDir 'tilt_1min'
if ((-not $DryRun) -and (-not (Test-Path $barsPath))) {
    $CacheOk = $false
    Write-Host ("WARNUNG: Bar-Cache fehlt (" + $barsPath + ")")
}
if ((-not $DryRun) -and (-not (Test-Path $tiltPath))) {
    $CacheOk = $false
    Write-Host ("WARNUNG: Tilt-Store fehlt (" + $tiltPath + ") - erst run_wp2_l2extract.ps1 ausfuehren")
}

$CliScript = Join-Path $RepoRoot 'scripts\c22_l2tilt.py'
$rcRun = 2
if (-not $CacheOk) {
    Record-Step -Name 'H22_L2TILT' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Bar-Cache fehlt (" + $barsPath + ")")
} else {
    $rcRun = Invoke-Step -Name 'H22_L2TILT' -TimeoutSec $TmoStep -OkRcs @(0) -SkipRcs @(2) -CmdArgs @(
        $CliScript,
        '--tilt-dir', $TiltDir,
        '--cache-dir', $CacheDir,
        '--out-dir', (Join-Path $RunDir 'h22')
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
[void]$sb.AppendLine("# H-22 L2-TILT Mess-Gate (Welle 6) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Stores:** ``" + $TiltDir + "`` (WP-2) + ``" + $CacheDir + "`` (WP-0), beide read-only + fingerprint-gepinnt")
[void]$sb.AppendLine("- **Gate:** BTC beide L2-Fenster IC >= 0,10 UND p <= 0,05 (BH-FDR a=0,10, F-L2); 85%-Abdeckungs-Floor; hartes Ein-Fenster-DROP. ETH nur Bericht.")
[void]$sb.AppendLine("- **A-priori (registriert):** DROP erwartet - +-5-bp-Buchtiefe gegen 1-Tages-Horizont widerspricht der Zerfallsstruktur.")
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
    [void]$sb.AppendLine("**LAUT-FEHLER: Store-Fingerabdruecke stimmen nicht mit der Registrierung ueberein.**")
    [void]$sb.AppendLine("``gate_valid=false`` - Lauf NICHT urteilstragend. Store-Stand pruefen.")
} elseif ($exit -eq 2) {
    [void]$sb.AppendLine("**SKIP** - Store fehlt oder Abdeckungs-Floor (85%) in einem urteilstragenden")
    [void]$sb.AppendLine("Fenster verfehlt. Kein Verdikt (vorregistrierte SKIP-Semantik).")
} elseif ($exit -eq 1) {
    [void]$sb.AppendLine("**FEHLER** - ``H22_L2TILT.err.log`` pruefen.")
} else {
    [void]$sb.AppendLine("*Ergebnisse unter ``h22\c22_l2tilt_results.{json,md}``. WEITER verlangt: BTC in")
    [void]$sb.AppendLine("BEIDEN L2-Fenstern IC >= 0,10 UND p <= 0,05 nach BH-FDR a=0,10 ueber F-L2.")
    [void]$sb.AppendLine("Hartes Ein-Fenster-DROP. Ergebnisse hochladen -> Gate-Log.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
