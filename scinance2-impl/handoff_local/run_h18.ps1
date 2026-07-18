# ========================================================================
# run_h18.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-18)
#
# Aufruf:
#   powershell -ExecutionPolicy Bypass -File .\run_h18.ps1
#
# H-18 = GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit.
# **AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** Re-Execution der byte-
# identischen, bereits adjudizierten F-LEADLAG-Pipeline aus GL-006 mit GENAU
# EINER Aenderung: n_surrogates 200 -> 100.000, als GPU-Tensor-Batches
# (torch.fft.rfft/irfft Phase-Shuffle-Primitive, batched TE-Histogramme via
# scatter_add, batched CWT via FFT-Convolution). Das GL-006-Verdikt bleibt
# append-only UNVERAENDERT stehen; dieser Runner schreibt NICHT gate_log.md.
# KAPITALFREI: identisch GL-006.
#
# **Compute-Gating-Pflicht:** ein voller 100k-Surrogat-Lauf ist NUR auf
# einem echten CUDA-Device verdikt-tragend. Ablauf:
#   (1) H18_SELFTEST  - Methodik-Aequivalenz-Test gegen die ORIGINALE
#       c17_c41_lead_lag-Pipeline bei kleinem N (synthetisch) - MUSS rc=0.
#   (2) H18_GPU_CHECK - --check-gpu-only; rc 0 = CUDA vorhanden, rc 3 = kein
#       CUDA (sauberer SKIP fuer Schritt 3).
#   (3) H18_AUDIT     - nur bei rc 0 aus (2): voller Lauf, 100.000
#       Surrogate, Seed 42, --backend cuda.
#
# Exit-Code: 0 = OK (inkl. GPU-los mit sauberem SKIP von Schritt 3)
#            1 = FAIL * 2 = kein FAIL, aber SKIP (kein CUDA-Device).
# Ergebnisse: scinance2-impl\handoff_local\results\h18_<timestamp>\h18\...
#             + SUMMARY_<datum>.md
#
# Optionale Env-Overrides: HANDOFF_DUCKDB, PYTHON, HANDOFF_DRY_RUN=1
# (+HANDOFF_DRY_RC). PS 5.1-kompatibel (handle-cache + BelowNormal).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$DuckDbPath = if ($env:HANDOFF_DUCKDB) { $env:HANDOFF_DUCKDB } else { Join-Path $RepoRoot 'data\bybit_edge.duckdb' }

$Pair = 'BTCUSDT,ETHUSDT'
$NWindows = 2
$NSurrogates = 100000
$Seed = 42
$TmoSelftest = 600
$TmoGpuCheck = 120
$TmoAudit = 10800

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h18_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h18') | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{ Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail })
}

function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs)
    # rc 3 aus H18_GPU_CHECK -> SKIP (kein Fehler); jeder andere rc != 0 -> FAIL.
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
    elseif ($Name -eq 'H18_GPU_CHECK' -and $rc -eq 3) { $status = 'SKIP'; $detail = 'kein CUDA-Device gefunden' }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_H18 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("H-18 ist AUFLOESUNGS-AUDIT von GL-006/H-04, KEINE NEU-ADJUDIKATION. DuckDB: " + $DuckDbPath)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$Script = Join-Path $RepoRoot 'scripts\c18_leadlag_audit.py'

# -- Schritt 1: Methodik-Aequivalenz-Test (immer, unabhaengig von GPU) ---
$rcSelftest = Invoke-Step -Name 'H18_SELFTEST' -TimeoutSec $TmoSelftest -CmdArgs @(
    $Script, '--self-test', '--seed', "$Seed", '--out', (Join-Path $RunDir 'h18')
)
if ($rcSelftest -ne 0 -and -not $DryRun) {
    Write-Host "FAIL: H18_SELFTEST - Methodik-Aequivalenz zur ORIGINALEN c17_c41_lead_lag-Pipeline gebrochen. Kein Audit-Lauf."
}

# -- Schritt 2: GPU/CUDA-Status (Compute-Gating-Pflicht) ------------------
$rcGpu = Invoke-Step -Name 'H18_GPU_CHECK' -TimeoutSec $TmoGpuCheck -CmdArgs @(
    $Script, '--check-gpu-only', '--out', (Join-Path $RunDir 'h18')
)

# -- Schritt 3: voller 100k-Surrogat-Audit-Lauf, nur bei echtem CUDA UND
# bestandenem Selftest (Audit-Befund H-1: beide Bedingungen sind Pflicht,
# nicht nur $rcGpu - ein gebrochener Selftest darf den teuren Lauf nie
# durchlassen, das ist genau das Szenario, vor dem das Compute-Gating
# schuetzen soll). --------------------------------------------------------
if ($DryRun) {
    [void](Invoke-Step -Name 'H18_AUDIT' -TimeoutSec $TmoAudit -CmdArgs @(
        $Script, '--db', $DuckDbPath, '--pair', $Pair, '--windows', "$NWindows",
        '--surrogates', "$NSurrogates", '--seed', "$Seed", '--db-copy', '--backend', 'cuda',
        '--out', (Join-Path $RunDir 'h18')
    ))
} elseif ($rcSelftest -ne 0) {
    Record-Step -Name 'H18_AUDIT' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("H18_SELFTEST fehlgeschlagen (rc=" + $rcSelftest + ") - Methodik-Aequivalenz nicht bestaetigt, kein Audit-Lauf")
    Write-Host "SKIP: H18_AUDIT - H18_SELFTEST fehlgeschlagen, Aequivalenz-Grundlage nicht gesichert (Compute-Gating-Pflicht)."
} elseif ($rcGpu -eq 0) {
    if (-not (Test-Path $DuckDbPath)) {
        Record-Step -Name 'H18_AUDIT' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("DuckDB fehlt (" + $DuckDbPath + ")")
        Write-Host ("SKIP: H18_AUDIT - DuckDB fehlt (" + $DuckDbPath + ")")
    } else {
        [void](Invoke-Step -Name 'H18_AUDIT' -TimeoutSec $TmoAudit -CmdArgs @(
            $Script, '--db', $DuckDbPath, '--pair', $Pair, '--windows', "$NWindows",
            '--surrogates', "$NSurrogates", '--seed', "$Seed", '--db-copy', '--backend', 'cuda',
            '--out', (Join-Path $RunDir 'h18')
        ))
    }
} else {
    Record-Step -Name 'H18_AUDIT' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("kein CUDA-Device (H18_GPU_CHECK rc=" + $rcGpu + ") - 100k-Surrogat-Lauf ohne CUDA ist NICHT verdikt-tragend")
    Write-Host "SKIP: H18_AUDIT - kein CUDA-Device, ein voller Lauf waere nicht verdikt-tragend (Compute-Gating-Pflicht)."
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

# Datenbindungs-Status gegen GL-006 fuer die SUMMARY sichtbar machen (Audit-
# Befund M-1: darf nicht nur im JSON-Report-Koerper stehen).
$DataBindingJson = Join-Path $RunDir 'h18\c18_leadlag_audit_results.json'
$DataBindingStatus = 'n/a (kein Report)'
if (Test-Path $DataBindingJson) {
    try {
        $resultObj = Get-Content -Raw -Path $DataBindingJson | ConvertFrom-Json
        $DataBindingStatus = [string]$resultObj.data_binding_vs_gl006.all_windows_match_gl006
    } catch {
        $DataBindingStatus = 'n/a (Parse-Fehler)'
    }
}

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-18 GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit - T3 (Welle 5)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("**AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** Das GL-006-Verdikt (WEITER,")
[void]$sb.AppendLine("Mess-Existenz, Kapital PARK) bleibt append-only UNVERAENDERT stehen. Dieser")
[void]$sb.AppendLine("Runner schreibt NICHT ``gate_log.md`` - ein neuer, eigener GL-Eintrag")
[void]$sb.AppendLine("(GL-014ff.) wird SPAETER manuell aus ``h18\c18_leadlag_audit_results.json``")
[void]$sb.AppendLine("erstellt.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **DuckDB:** ``" + $DuckDbPath + "`` (read-only, --db-copy)")
[void]$sb.AppendLine("- **Methodik (vorregistriert, EINZIGE Aenderung ggue. GL-006):** n_surrogates 200 -> " + $NSurrogates + ", Paar " + $Pair + ", Fenster=" + $NWindows + ", Seed=" + $Seed + ", F-LEADLAG BH-FDR alpha=0.10 je Fenster")
[void]$sb.AppendLine("- **KAPITALFREI** - identisch GL-006, keine bps/Edge/PnL/Friction-Metrik.")
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
[void]$sb.AppendLine("**Datenbindung vs. GL-006 (all_windows_match_gl006): " + $DataBindingStatus + "**")
[void]$sb.AppendLine("- bei ``False`` misst dieser Lauf NICHT die archivierten GL-006-Fenster,")
[void]$sb.AppendLine("T1/T2 sind dann NICHT als Aufloesung von GL-006 lesbar (s. Report).")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("*Ergebnis: ``h18\c18_leadlag_audit_results.json`` (+ .md) enthaelt die")
[void]$sb.AppendLine("vorregistrierten Teil-Claims T1 (12 GL-006-Stage-1-FDR-Survivor bei p<=1e-3")
[void]$sb.AppendLine("neu signifikant) und T2 (ETH->BTC F0 Lag1/Lag2 loesen sich mit >5 MC-SE auf)")
[void]$sb.AppendLine("als separate Felder, plus ``verdict_carrying`` (nur bei echtem CUDA + 100k")
[void]$sb.AppendLine("Surrogaten true). Kein automatisches Gate-Urteil - gate-auditor liest den")
[void]$sb.AppendLine("Payload und erstellt manuell GL-014ff.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
