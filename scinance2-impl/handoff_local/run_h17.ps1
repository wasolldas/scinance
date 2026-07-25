# ========================================================================
# run_h17.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-17)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h17.ps1
#
# H-17 = C-17-VENUE Venue-Fingerprint-Mess-Gate (Contrastive-Embedding
# InfoNCE + Frozen-Linear-Probe, F-VENUE). 10 Nodes (5 Symbole x {Bybit,
# Binance}, publicTrade only), 5-Min-Event-Fenster, 4 Kanaele (Inter-
# Trade-Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction) mit Pro-
# Tag-Quantil-Normalisierung je Kanal/Node. Leave-One-Symbol-Out (5
# Folds), je Fold EIN echtes Training + 20 VOLLE Permutations-Retrainings
# (Within-Symbol-Within-Day-Label-Permutation, KEIN Frozen-Model-
# Shuffling). ONE F-VENUE BH-FDR-Familie ueber die 5 Fold-p-Werte.
# VORREGISTRIERTES Non-Redundanz-Gate gegen c12_frag/H-12 (|Spearman rho|
# < 0.6 gegen die c12-Tages-lambda2/IPR-Serie, sonst REDUNDANT = DROP
# unabhaengig von der Accuracy). KAPITALFREI.
#
# ZWINGENDE GPU-VORBEDINGUNG (registry H-17, verbindlich): Batch >= 2048
# ist Teil der registrierten Methode. Der Runner prueft ZUERST per
# --check-gpu-only, ob ein echtes CUDA-Device sichtbar ist. OHNE CUDA
# wird der volle Lauf UEBERSPRUNGEN (SKIP, exit 2) statt stundenlang eine
# NICHT-verdikt-tragende CPU/Numpy-Pipeline-Smoke zu produzieren - selbst
# ein erzwungener Lauf waere wegen des eingebauten Compute-Gates in
# driver.run() (compute.verdict_bearing) NIE urteilstragend. Override
# fuer einen erzwungenen Smoke-Lauf trotz fehlender GPU (NUR Pipeline-
# Diagnose, NIE fuer ein Gate-Urteil): $env:HANDOFF_H17_FORCE_NO_GPU=1.
#
# **EXTREME LAUFZEIT (registry-Schaetzung: GPU ~1-2 Tage, ~105 volle
# Trainings: 5 Folds x (1 echtes InfoNCE-Training + 20 Permutations-
# Retrainings) + Probe-Fits) - DIESER RUNNER IST RESUME-FAEHIG / EINFACH
# ERNEUT STARTEN (run_h14/run_h16-Muster).** Jedes abgeschlossene
# Einzeltraining (Fold-Symbol x {main, null} x Index) schreibt SOFORT einen
# eigenen Checkpoint (atomic write) nach einem STABILEN, NICHT
# zeitgestempelten Verzeichnis (results\h17_checkpoints\<Symbol>\). Ein
# Windows-Neustart, ein TIMEOUT dieses Runners oder ein geschlossenes
# Fenster verliert HOECHSTENS das gerade laufende einzelne Training - nicht
# den restlichen Fortschritt. EINFACH DIESES SKRIPT ERNEUT STARTEN: es
# laedt automatisch alle bereits abgeschlossenen Trainings aus
# results\h17_checkpoints\ (Start-Log: 'X/Y Trainings bereits als
# Checkpoint vorhanden, Z noch offen') und trainiert nur die fehlenden
# weiter. Timeout-Default 172800s = 48h PRO AUFRUF (Override
# $env:HANDOFF_H17_TIMEOUT_S); braucht der Gesamtlauf mehrere Aufrufe, ist
# das der VORGESEHENE Betriebsmodus, kein Fehler. Die Checkpoints sind
# gegen die Lauf-Parameter gefingerprintet: ein Parameterwechsel (anderes
# Datenfenster/Seed/Batch/Steps/Device/...) unter demselben Checkpoint-
# Pfad bricht HART ab (CheckpointMismatchError, rc=1) statt
# stillschweigend stale Ergebnisse zu mischen.
#
# EIN Block: H17_VENUE (plus vorgelagerter GPU_CHECK). Exit: 0=OK 1=FAIL
# (inkl. TIMEOUT dieses Aufrufs bei unvollstaendigem Plan - KEIN
# Datenverlust, einfach erneut starten) 2=SKIP. Ergebnisse:
# scinance2-impl\handoff_local\results\h17_<ts>\ + SUMMARY_<datum>.md
# (gate-auditor urteilt gegen H-17). Checkpoints (STABIL, ueberlebt
# Neustarts): scinance2-impl\handoff_local\results\h17_checkpoints\.
#
# Optionale Env-Overrides: HARVEST_DIR, C12_RESULTS_JSON (Pfad zu einem
# vorhandenen c12_frag_results.json fuer das Redundanz-Gate),
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC), HANDOFF_H17_TIMEOUT_S,
# HANDOFF_H17_FORCE_NO_GPU, H17_END_DATE (Cutoff, Default 2026-07-04; wird
# beim ERSTEN Aufruf neben den Checkpoints in
# results\h17_checkpoints\H17_END_DATE.pin festgeschrieben und bei jedem
# weiteren Aufruf wiederverwendet - ein Resume ueber mehrere Naechte
# behaelt so dasselbe registrierte Datenfenster, sonst braeche der
# Checkpoint-Fingerprint absichtlich hart ab), H17_CKPT_DIR (Default
# results\h17_checkpoints, NICHT aendern zwischen Aufrufen desselben
# Laufs - sonst kein Resume!).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }
$C12ResultsJson = if ($env:C12_RESULTS_JSON) { $env:C12_RESULTS_JSON } else { '' }

$Symbols   = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$Exchanges = 'bybit,binance'
$StartDate = '2026-03-27'
$NPerm     = 20
$Steps     = 10000
$BatchSize = 2048
$Seed      = 42
$TmoGpuCheck = 60
$TmoMain = if ($env:HANDOFF_H17_TIMEOUT_S) { [int]$env:HANDOFF_H17_TIMEOUT_S } else { 172800 }  # 48h Budget PRO AUFRUF (Resume, s. Kopf)
$ForceNoGpu = ($env:HANDOFF_H17_FORCE_NO_GPU -and ($env:HANDOFF_H17_FORCE_NO_GPU -ne '0'))
$CkptDir = if ($env:H17_CKPT_DIR) { $env:H17_CKPT_DIR } else { Join-Path $ScriptDir 'results\h17_checkpoints' }
New-Item -ItemType Directory -Force -Path $CkptDir | Out-Null

# Cutoff (End-Datum) PINNEN (run_h16-Muster): ein Resume-Lauf ueber mehrere
# Naechte MUSS dasselbe registrierte Datenfenster behalten - sonst bricht
# der Checkpoint-Fingerprint (absichtlich) hart ab. Der beim ERSTEN Aufruf
# benutzte Cutoff wird deshalb neben den Checkpoints festgeschrieben und
# bei jedem weiteren Aufruf wiederverwendet; auch eine spaetere Aenderung
# des Skript-Defaults kann so einen laufenden Resume nicht mehr brechen.
# (H17_END_DATE-Env uebersteuert; dann bei geaenderten Werten Checkpoints
# loeschen oder H17_CKPT_DIR wechseln.)
$EndDatePin = Join-Path $CkptDir 'H17_END_DATE.pin'
if ($env:H17_END_DATE) {
    $EndDate = $env:H17_END_DATE
} elseif (Test-Path $EndDatePin) {
    $EndDate = (Get-Content -Path $EndDatePin -TotalCount 1).Trim()
} else {
    $EndDate = '2026-07-04'
}
Set-Content -Path $EndDatePin -Value $EndDate

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h17_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h17') | Out-Null
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
                $detail = "TIMEOUT nach $TimeoutSec s (Plan unvollstaendig - Checkpoints erhalten, verloren ging hoechstens das laufende Training; naechster Aufruf resumed)"
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

# GPU_CHECK is a diagnostic PROBE, not a pass/fail step: rc=3 ("kein CUDA")
# is an EXPECTED, informative outcome (e.g. every sandbox/non-GPU run) and
# must NOT count as a runner FAIL - only a genuine crash (rc not in {0,3})
# does. Records to steps.tsv as INFO/FAIL, returns the raw rc.
function Invoke-GpuCheck {
    param([string]$ScriptPath, [int]$TimeoutSec)
    $log = Join-Path $RunDir 'GPU_CHECK.log'
    $errLog = Join-Path $RunDir 'GPU_CHECK.err.log'
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] START GPU_CHECK: " + $PythonExe + " " + $ScriptPath + " --check-gpu-only")
    $t0 = Get-Date
    $rc = -1
    $detail = ''
    if ($DryRun) {
        Add-Content -Path $log -Value ("[DRY-RUN] " + $ScriptPath + " --check-gpu-only")
        $rc = $DryRc
        $detail = "dry-run rc=$rc"
    } else {
        try {
            $p = Start-Process -FilePath $PythonExe -ArgumentList @($ScriptPath, '--check-gpu-only') -NoNewWindow -PassThru `
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
    if (-not $detail) { $detail = "rc=$rc" }
    $status = 'INFO'
    if ($rc -ne 0 -and $rc -ne 3) { $status = 'FAIL' }
    Record-Step -Name 'GPU_CHECK' -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   GPU_CHECK: " + $status + " (" + $detail + ", " + $dur + "s) log=" + $log)
    return $rc
}

Write-Host ("RUN_H17 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Panel: " + $Symbols + " x {" + $Exchanges + "}")
Write-Host ("Fenster: " + $StartDate + ".." + $EndDate + " (Cutoff gepinnt in " + $EndDatePin + ") | n_perm=" + $NPerm + " steps=" + $Steps + " batch_size=" + $BatchSize + " seed=" + $Seed)
Write-Host ("Checkpoints (STABIL ueber Neustarts): " + $CkptDir)
Write-Host ("RESUME-FAEHIG: bereits abgeschlossene Einzeltrainings werden uebersprungen - ein Timeout/Abbruch verliert hoechstens das gerade laufende Training; einfach erneut starten (s. Kopf-Kommentar).")
Write-Host ("C12-Ergebnisse fuer Redundanz-Gate: " + $(if ($C12ResultsJson) { $C12ResultsJson } else { "<keiner - Gate bleibt nicht auswertbar>" }))
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$bybitPath   = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$binancePath = Join-Path $HarvestDir 'raw\binance\publicTrade'
$HarvestOk = $true
if (-not $DryRun) {
    foreach ($pair in @(@('bybit', $bybitPath), @('binance', $binancePath))) {
        if (-not (Test-Path $pair[1])) {
            $HarvestOk = $false
            Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $pair[1] + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
        }
    }
}

$Script = Join-Path $RepoRoot 'scripts\c17_venue.py'

if (-not $HarvestOk) {
    Record-Step -Name 'H17_VENUE' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $bybitPath + " / " + $binancePath + ")")
} else {
    # -- GPU-Vorbedingung (verbindlich) ------------------------------------
    $gpuRc = Invoke-GpuCheck -ScriptPath $Script -TimeoutSec $TmoGpuCheck
    $gpuOk = $DryRun -or ($gpuRc -eq 0)

    if (-not $gpuOk -and -not $ForceNoGpu) {
        Write-Host ("WARNUNG: kein echtes CUDA-Device gefunden (GPU_CHECK rc=" + $gpuRc + ") - voller H-17-Lauf waere NIE verdikt-tragend (registrierter Batch>=2048-Bedarf) - uebersprungen. Override: `$env:HANDOFF_H17_FORCE_NO_GPU=1 (nur Pipeline-Diagnose, KEIN Gate-Urteil).")
        Record-Step -Name 'H17_VENUE' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("kein CUDA-Device (GPU_CHECK rc=" + $gpuRc + ")")
    } else {
        $cmdArgs = @(
            $Script,
            '--base-dir', $HarvestDir, '--symbols', $Symbols, '--exchanges', $Exchanges,
            '--start-date', $StartDate, '--end-date', $EndDate,
            '--n-perm', "$NPerm", '--steps', "$Steps", '--batch-size', "$BatchSize",
            '--seed', "$Seed", '--device', 'auto',
            '--ckpt-dir', $CkptDir,
            '--out-dir', (Join-Path $RunDir 'h17')
        )
        if ($C12ResultsJson) { $cmdArgs += @('--c12-results', $C12ResultsJson) }
        [void](Invoke-Step -Name 'H17_VENUE' -TimeoutSec $TmoMain -CmdArgs $cmdArgs)
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
[void]$sb.AppendLine("# H-17 Venue-Fingerprint Mess-Gate (Contrastive-Embedding) - T3")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) | Panel: " + $Symbols + " x {" + $Exchanges + "}")
[void]$sb.AppendLine("- **Fenster:** " + $StartDate + ".." + $EndDate + " (Cutoff gepinnt in ``" + $EndDatePin + "``)")
[void]$sb.AppendLine("- **Checkpoints (STABIL, ueberlebt Neustarts):** ``" + $CkptDir + "``")
[void]$sb.AppendLine("- **n_perm=" + $NPerm + " steps=" + $Steps + " batch_size=" + $BatchSize + " seed=" + $Seed + " | F-VENUE BH-FDR a=0.10**")
[void]$sb.AppendLine("- **C12-Redundanz-Gate-Quelle:** " + $(if ($C12ResultsJson) { $C12ResultsJson } else { "<keine - Gate nicht auswertbar>" }))
[void]$sb.AppendLine("- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE bps/PnL/Sharpe/Friction.")
[void]$sb.AppendLine("- **RESUME-FAEHIG:** ~105 volle Trainings (~35h+ GPU) - jeder Aufruf setzt aus den Checkpoints in ``" + $CkptDir + "`` fort (je Einzeltraining atomar geschrieben). Ein TIMEOUT/FAIL bei unvollstaendigem Plan ist NORMAL, kein Datenverlust - ein Abbruch kostet hoechstens das gerade laufende Einzeltraining. EINFACH ERNEUT STARTEN. Steht im err.log eine CheckpointMismatchError: Lauf-Parameter wurden zwischen Aufrufen geaendert - Checkpoints loeschen ODER H17_CKPT_DIR wechseln ODER die alten Parameter wiederherstellen; NIEMALS mischen.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-17 (Roh-JSON unter ``h17\c17_venue_results.json``).")
[void]$sb.AppendLine("WEITER verlangt: Held-out-Balanced-Accuracy >=0.60 in >=4/5 Leave-One-Symbol-Out-Folds gegen")
[void]$sb.AppendLine("die 20-Retrainings-Permutations-Null nach BH-FDR alpha=0.10 ueber F-VENUE UND Non-Redundanz-")
[void]$sb.AppendLine("Gate |Spearman rho| < 0.6 gegen die c12_frag-Tages-lambda2/IPR-Serie. DROP: Pooled-Accuracy")
[void]$sb.AppendLine("< 0.55 ODER < 4/5 Folds ODER |rho| >= 0.6 (REDUNDANT zu H-12, DROP unabhaengig von der")
[void]$sb.AppendLine("Accuracy). WICHTIG: das JSON-Feld compute.verdict_bearing MUSS true sein, sonst ist der Lauf")
[void]$sb.AppendLine("eine reine Pipeline-Smoke OHNE Gate-Anspruch. Kein Graubereich. Ergebnisse hochladen -> GL-Zaehlung.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
