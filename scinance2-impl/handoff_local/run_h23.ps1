# ========================================================================
# run_h23.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 7, H-23)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h23.ps1
#
# H-23 = C-17-Venue-Fingerprint WIEDERHOLUNG mit Voll-Distanzserie.
# Aufloesung des GL-019-Schwebezustands: dort war das registrierte
# Non-Redundanz-Gate NICHT auswertbar, weil die taegliche Embedding-
# Distanzserie nur auf den Fold-TEST-Tagen existierte (2 bzw. nach dem
# Envelope-Fix 9 Ueberlappungstage gegen einen 10-Tage-Floor). H-23
# definiert sie ueber ALLE Panel-Tage: jedes Fenster wird von genau dem
# Fold-Encoder eingebettet, dessen ausgelassenes Symbol es traegt -
# Symbol-Ausschluss bleibt fuer JEDES Fenster gewahrt. Erwartete
# Ueberlappung ~85 Tage; erst das gibt dem Gate Trennschaerfe.
#
# BEIDE Gates muessen auf DIESEM Lauf bestehen - der GL-019-Messbefund
# wird NICHT importiert (neue Trainings sind stochastisch neu).
#
# KOSTEN: die 5 HAUPT-Trainings laufen NEU (die Encoder-Gewichte liegen
# nicht in den Checkpoints, nur die Test-Embeddings). Die 100 Null-
# Retrainings RESUMEN aus den vorhandenen Checkpoints - der globale
# Run-Fingerabdruck bleibt dafuer unangetastet; invalidiert wird nur die
# Haupt-Trainings-Identitaet (eigene kind-Kennung). Eine GPU-Nacht.
#
# COMPUTE-GATING (verbindlich): ohne echtes CUDA + Batch>=2048 ist der
# Lauf NIE verdikt-tragend - der Runner ueberspringt ihn dann.
#
# KAPITALFREI: reine Struktur-/Existenzfrage. H-17b-Tradability bleibt
# ausdruecklich NICHT impliziert.
#
# Schritte: GPU_CHECK -> H23_VENUE_FULL. Exit: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h23_<timestamp>\
#             + SUMMARY_<datum>.md (Gate-Urteil: gate-auditor gegen H-23).
#
# Optionale Env-Overrides wie run_h17.ps1, mit H23_-Praefix; zusaetzlich
# HANDOFF_H23_FORCE_NO_GPU=1 (nur Pipeline-Diagnose, KEIN Gate-Urteil).
# PS 5.1-kompatibel, ASCII-only.
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
$TmoMain = if ($env:HANDOFF_H23_TIMEOUT_S) { [int]$env:HANDOFF_H23_TIMEOUT_S } else { 172800 }  # 48h Budget PRO AUFRUF (Resume, s. Kopf)
$ForceNoGpu = ($env:HANDOFF_H23_FORCE_NO_GPU -and ($env:HANDOFF_H23_FORCE_NO_GPU -ne '0'))
# ABSICHTLICH das H-17-Checkpoint-Verzeichnis: dort liegen die 100 Null-
# Retrainings, die H-23 wiederverwendet (globaler Fingerabdruck unveraendert).
# Die 5 Haupt-Trainings tragen eine eigene kind-Kennung und laufen neu, ohne
# die alten Haupt-Checkpoints zu lesen oder zu ueberschreiben.
$CkptDir = if ($env:H23_CKPT_DIR) { $env:H23_CKPT_DIR } else { Join-Path $ScriptDir 'results\h17_checkpoints' }
New-Item -ItemType Directory -Force -Path $CkptDir | Out-Null

# Cutoff (End-Datum) PINNEN (run_h16-Muster): ein Resume-Lauf ueber mehrere
# Naechte MUSS dasselbe registrierte Datenfenster behalten - sonst bricht
# der Checkpoint-Fingerprint (absichtlich) hart ab. Der beim ERSTEN Aufruf
# benutzte Cutoff wird deshalb neben den Checkpoints festgeschrieben und
# bei jedem weiteren Aufruf wiederverwendet; auch eine spaetere Aenderung
# des Skript-Defaults kann so einen laufenden Resume nicht mehr brechen.
# (H23_END_DATE-Env uebersteuert; dann bei geaenderten Werten Checkpoints
# loeschen oder H23_CKPT_DIR wechseln.)
$EndDatePin = Join-Path $CkptDir 'H23_END_DATE.pin'
if ($env:H23_END_DATE) {
    $EndDate = $env:H23_END_DATE
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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h23_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h23') | Out-Null
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

Write-Host ("RUN_H23 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
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
    Record-Step -Name 'H23_VENUE_FULL' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $bybitPath + " / " + $binancePath + ")")
} else {
    # -- GPU-Vorbedingung (verbindlich) ------------------------------------
    $gpuRc = Invoke-GpuCheck -ScriptPath $Script -TimeoutSec $TmoGpuCheck
    $gpuOk = $DryRun -or ($gpuRc -eq 0)

    if (-not $gpuOk -and -not $ForceNoGpu) {
        Write-Host ("WARNUNG: kein echtes CUDA-Device gefunden (GPU_CHECK rc=" + $gpuRc + ") - voller H-23-Lauf waere NIE verdikt-tragend (registrierter Batch>=2048-Bedarf) - uebersprungen. Override: `$env:HANDOFF_H23_FORCE_NO_GPU=1 (nur Pipeline-Diagnose, KEIN Gate-Urteil).")
        Record-Step -Name 'H23_VENUE_FULL' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("kein CUDA-Device (GPU_CHECK rc=" + $gpuRc + ")")
    } else {
        $cmdArgs = @(
            $Script,
            '--base-dir', $HarvestDir, '--symbols', $Symbols, '--exchanges', $Exchanges,
            '--start-date', $StartDate, '--end-date', $EndDate,
            '--n-perm', "$NPerm", '--steps', "$Steps", '--batch-size', "$BatchSize",
            '--seed', "$Seed", '--device', 'auto',
            '--ckpt-dir', $CkptDir,
            '--h23-full-panel',
            '--out-dir', (Join-Path $RunDir 'h23')
        )
        if ($C12ResultsJson) { $cmdArgs += @('--c12-results', $C12ResultsJson) }
        [void](Invoke-Step -Name 'H23_VENUE_FULL' -TimeoutSec $TmoMain -CmdArgs $cmdArgs)
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
[void]$sb.AppendLine("# H-23 Venue-Fingerprint mit VOLL-Distanzserie (GL-019-Aufloesung) - T3")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) | Panel: " + $Symbols + " x {" + $Exchanges + "}")
[void]$sb.AppendLine("- **Fenster:** " + $StartDate + ".." + $EndDate + " (Cutoff gepinnt in ``" + $EndDatePin + "``)")
[void]$sb.AppendLine("- **Checkpoints (STABIL, ueberlebt Neustarts):** ``" + $CkptDir + "``")
[void]$sb.AppendLine("- **n_perm=" + $NPerm + " steps=" + $Steps + " batch_size=" + $BatchSize + " seed=" + $Seed + " | F-VENUE BH-FDR a=0.10**")
[void]$sb.AppendLine("- **C12-Redundanz-Gate-Quelle:** " + $(if ($C12ResultsJson) { $C12ResultsJson } else { "<keine - Gate nicht auswertbar>" }))
[void]$sb.AppendLine("- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE bps/PnL/Sharpe/Friction.")
[void]$sb.AppendLine("- **H-23-Umfang:** 5 HAUPT-Trainings laufen NEU (eigene Checkpoint-Kennung); die 100 Null-Retrainings RESUMEN aus den H-17-Checkpoints. Distanzserie ueber ALLE Panel-Tage statt nur der Fold-Test-Tage -> Redundanz-Gate erstmals auswertbar.")
[void]$sb.AppendLine("- **RESUME-FAEHIG:** ~105 volle Trainings (~35h+ GPU brutto; H-23 erwartet deutlich weniger, da die Nulls resumen) - jeder Aufruf setzt aus den Checkpoints in ``" + $CkptDir + "`` fort (je Einzeltraining atomar geschrieben). Ein TIMEOUT/FAIL bei unvollstaendigem Plan ist NORMAL, kein Datenverlust - ein Abbruch kostet hoechstens das gerade laufende Einzeltraining. EINFACH ERNEUT STARTEN. Steht im err.log eine CheckpointMismatchError: Lauf-Parameter wurden zwischen Aufrufen geaendert - Checkpoints loeschen ODER H23_CKPT_DIR wechseln ODER die alten Parameter wiederherstellen; NIEMALS mischen.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-23 (Roh-JSON unter ``h23\c23_venue_full_results.json``).")
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
