# ========================================================================
# run_h20.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 6, H-20)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h20.ps1
#
# H-20 = TAIL-AFTERMATH: reversions-signierte Nachbewegung 2-24 h nach
# 3,5-sigma-Stundenereignissen (kausale MAD-Skala, 24h-Non-Overlap,
# 2h-Bounce-Luecke). Gepoolt ueber 5 Symbole; tages-geclusterter
# Bootstrap. Gate: BEIDE OOS-Fenster mean >= +10 bp UND p <= 0,05 nach
# BH-FDR a=0,10 ueber F-TAIL; N-Floor 100 Event-Tage/Fenster (darunter
# KEIN VERDIKT). Hartes Ein-Fenster-DROP. A-priori: offen (~30-40%).
#
# Liest AUSSCHLIESSLICH den WP-0-Bar-Cache (data\barcache) - KEIN
# Roh-Tick-Zugriff (DEC-34). Die registrierten Cache-Fingerabdruecke
# werden VOR der Messung geprueft; Abweichung -> rc=3, gate_valid=false.
#
# KAPITALFREI: reine Messung, keine bps/Edge/PnL/Friction-Rechnung.
#
# Schritte: H20_TAIL. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (Cache fehlt) *
#           3 = Fingerprint-Mismatch (Befund nicht tragfaehig).
# Ergebnisse: scinance2-impl\handoff_local\results\h19_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor protokolliert den Befund).
#
# Optionale Env-Overrides: BARCACHE_DIR, H20_RESULTS_DIR, H20_TIMEOUT_SEC,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$CacheDir  = if ($env:BARCACHE_DIR) { $env:BARCACHE_DIR } else { Join-Path $RepoRoot 'data\barcache' }

$Symbols = 'BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,BNBUSDT'
# CPU; Panel liegt im Cache, Rotation-Null 1000x je Zelle -> Minuten bis ~1 h.
$TmoStep = if ($env:H20_TIMEOUT_SEC) { [int]$env:H20_TIMEOUT_SEC } else { 7200 }

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
$ResultsBase = if ($env:H20_RESULTS_DIR) { $env:H20_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("h20_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h20') | Out-Null
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

Write-Host ("RUN_H20 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Bar-Cache: " + $CacheDir + " (WP-0, read-only) | Symbole: " + $Symbols)
Write-Host "Fingerprint-Pruefung VOR der Messung; Gate-Urteil faellt der gate-auditor."
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$CacheOk = $true
$barsPath = Join-Path $CacheDir 'bars_1min'
if ((-not $DryRun) -and (-not (Test-Path $barsPath))) {
    $CacheOk = $false
    Write-Host ("WARNUNG: Bar-Cache fehlt (" + $barsPath + ") - erst run_wp0_barcache.ps1 ausfuehren oder BARCACHE_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\c20_tail.py'
$rcRun = 2
if (-not $CacheOk) {
    Record-Step -Name 'H20_TAIL' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Bar-Cache fehlt (" + $barsPath + ")")
} else {
    $rcRun = Invoke-Step -Name 'H20_TAIL' -TimeoutSec $TmoStep -OkRcs @(0) -CmdArgs @(
        $CliScript,
        '--cache-dir', $CacheDir,
        '--symbols', $Symbols,
        '--out-dir', (Join-Path $RunDir 'h20')
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
[void]$sb.AppendLine("# H-20 TAIL-AFTERMATH Mess-Gate (Welle 6) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Bar-Cache:** ``" + $CacheDir + "`` (WP-0, read-only) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Gate:** BEIDE OOS-Fenster gepoolt mean >= +10 bp UND p <= 0,05 (BH-FDR a=0,10, F-TAIL); N-Floor 100 Event-Tage/Fenster; hartes Ein-Fenster-DROP.")
[void]$sb.AppendLine("- **Hinweis:** Falls H-19 DRIFT-Befunde ergab, gilt die Regime-Splitting-Auflage fuer die Berichts-Lesart.")
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
    [void]$sb.AppendLine("**FEHLER** - ``H20_TAIL.err.log`` pruefen.")
} else {
    [void]$sb.AppendLine("*Ergebnisse unter ``h20\c20_tail_results.{json,md}``. WEITER verlangt: BEIDE OOS-Fenster")
    [void]$sb.AppendLine("gepoolt mean >= +10 bp UND Cluster-Bootstrap-p <= 0,05 nach BH-FDR a=0,10 ueber F-TAIL.")
    [void]$sb.AppendLine("Hartes Ein-Fenster-DROP, kein Graubereich. Ergebnisse hochladen -> Gate-Log.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
