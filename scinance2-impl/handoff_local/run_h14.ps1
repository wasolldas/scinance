# ========================================================================
# run_h14.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-14)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h14.ps1
#
# H-14 = C-14-PANELLAG Conditional Cross-Venue-Lead-Lag-Graph via
# Node-Ablation-Cross-Attention. 12-Node-1s-Panel (BTC/ETH x {Bybit,
# Binance, Deribit-PERP} + SOL/BNB/XRP x {Bybit, Binance}), pro Node ein
# PatchTST-Style-Encoder (m18_patchtst-Wiederverwendung) + Cross-Node-
# Multi-Head-Attention, Target = Vorzeichen der naechsten 10s-Rendite.
# Edge-Statistik T(j->i) = OOS-Delta-Log-Loss (Vollmodell vs. Single-
# Source-j-Retrain-Ablation). Null: ~100 Retrainings mit komplett
# surrogaten Cross-Node-Inputs je Fenster. ZWEI Fenster W1/W2 (identisch
# H-09/H-12). F-PANELLAG BH-FDR a=0.10 ueber 99 Non-BTC-Source-Kanten je
# Fenster (Registry-Schaetzung "~110"). KAPITALFREI: reine Struktur-/
# Existenzfrage, KEINE Kosten-/Ertragsrechnung. GPU ZWINGEND: ein Lauf ohne
# echtes CUDA-Device ist NIEMALS verdikt-tragend.
#
# **EXTREME LAUFZEIT (~226 volle Trainings, ~2-3 GPU-Tage auf RTX 5060 Ti)
# - DIESER RUNNER IST RESUME-FAEHIG.** Jedes abgeschlossene Training
# schreibt SOFORT einen eigenen Checkpoint (atomic write) nach einem
# STABILEN, NICHT zeitgestempelten Verzeichnis (results\h14_checkpoints\).
# Ein Stromausfall, ein Timeout dieses Runners oder ein manueller Abbruch
# verliert HOECHSTENS das gerade laufende einzelne Training (10-20 Min) -
# nicht den restlichen Fortschritt. EINFACH DIESES SKRIPT ERNEUT STARTEN:
# es laedt automatisch alle bereits abgeschlossenen Trainings aus
# results\h14_checkpoints\ und trainiert nur die fehlenden weiter. Der
# volle Lauf braucht typischerweise MEHRERE Aufrufe dieses Skripts ueber
# mehrere Naechte (Default-Budget pro Aufruf s.u.) - das ist der
# VORGESEHENE Betriebsmodus, kein Fehler.
#
# Ablauf: (1) H14_GPU_CHECK via --check-gpu-only (rc 2 = kein CUDA -> SKIP,
# der volle Lauf startet dann NICHT), (2) nur bei rc 0: H14_PANELLAG voller
# (Teil-)Lauf innerhalb des Zeitbudgets dieses Aufrufs; schreibt
# c14_panellag_results.{json,md} NUR wenn ALLE Trainings beider Fenster
# abgeschlossen sind (sonst TIMEOUT/FAIL bei diesem Aufruf, aber Fortschritt
# bleibt in results\h14_checkpoints\ erhalten -> naechster Aufruf macht weiter).
#
# Exit-Code: 0 = OK (voller Lauf komplett, Ergebnis-JSON geschrieben) *
#            1 = FAIL (inkl. TIMEOUT dieses Aufrufs bei noch unvollstaendigem
#                Plan - KEIN Datenverlust, einfach erneut starten) *
#            2 = SKIP (kein CUDA-Device gefunden).
# Ergebnisse: scinance2-impl\handoff_local\results\h14_<timestamp>\
#             + SUMMARY_<datum>.md. Checkpoints (STABIL, ueberlebt Neustarts):
#             scinance2-impl\handoff_local\results\h14_checkpoints\{W1,W2}\*.json
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC),
# H14_N_NULL (Default 100), H14_TIMEOUT_SEC (Default 36000 = 10h Budget PRO
# AUFRUF - der Gesamtlauf braucht mehrere Aufrufe, s.o.), H14_CKPT_DIR
# (Default results\h14_checkpoints, NICHT aendern zwischen Aufruefen
# desselben Laufs - sonst kein Resume!).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$WinAStart = '2026-03-27'; $WinAEnd = '2026-05-15'
$WinBStart = '2026-05-16'; $WinBEnd = '2026-07-04'
$NNull = if ($env:H14_N_NULL) { [int]$env:H14_N_NULL } else { 100 }
$Seed  = 42
$TmoGpuCheck = 120
$TmoFull = if ($env:H14_TIMEOUT_SEC) { [int]$env:H14_TIMEOUT_SEC } else { 36000 }  # 10h Default PRO AUFRUF
$CkptDir = if ($env:H14_CKPT_DIR) { $env:H14_CKPT_DIR } else { Join-Path $ScriptDir 'results\h14_checkpoints' }

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h14_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h14') | Out-Null
New-Item -ItemType Directory -Force -Path $CkptDir | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{ Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail })
}

function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs, [string]$SkipDetail)
    # rc 2 des CLI = kein Compute-Gate -> Status SKIP (kein FAIL). Ein
    # TIMEOUT bei H14_PANELLAG (unvollstaendiger ~226-Trainings-Plan) ist
    # NORMAL - Checkpoints in $CkptDir bleiben erhalten, naechster Aufruf
    # resumed automatisch (s. Kopf-Kommentar).
    $log = Join-Path $RunDir ($Name + '.log')
    $errLog = Join-Path $RunDir ($Name + '.err.log')
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] START " + $Name + " (timeout " + $TimeoutSec + "s): " + $PythonExe + " " + ($CmdArgs -join ' '))
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
                $detail = "TIMEOUT nach $TimeoutSec s (Plan unvollstaendig - Checkpoints erhalten, naechster Aufruf resumed)"
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

Write-Host ("RUN_H14 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | 12-Node-Panel (BTC/ETH x Bybit/Binance/Deribit + SOL/BNB/XRP x Bybit/Binance)")
Write-Host ("Fenster: W1 " + $WinAStart + ".." + $WinAEnd + " | W2 " + $WinBStart + ".." + $WinBEnd + " | n_null=" + $NNull + " seed=" + $Seed)
Write-Host ("Checkpoints (STABIL ueber Neustarts): " + $CkptDir)
Write-Host ("H-14 ist GPU ZWINGEND: erst ehrlicher Compute-Check, dann (nur bei echtem CUDA) voller Lauf.")
Write-Host ("RESUME-FAEHIG: bereits abgeschlossene Trainings werden uebersprungen (s. Kopf-Kommentar).")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$SkipMsg = 'H-14 SKIP - kein verdikt-taugliches CUDA-Device gefunden (torch/CUDA-Check negativ)'

# Alle 12 Node-Pfade muessen existieren (Panel braucht alle 12 Serien).
# Reihenfolge/Deribit-Notation identisch panel.DEFAULT_NODES.
$NodePaths = @(
    'bybit\publicTrade\symbol=BTCUSDT',
    'binance\publicTrade\symbol=BTCUSDT',
    'deribit\publicTrade\symbol=BTC-PERPETUAL',
    'bybit\publicTrade\symbol=ETHUSDT',
    'binance\publicTrade\symbol=ETHUSDT',
    'deribit\publicTrade\symbol=ETH-PERPETUAL',
    'bybit\publicTrade\symbol=SOLUSDT',
    'binance\publicTrade\symbol=SOLUSDT',
    'bybit\publicTrade\symbol=XRPUSDT',
    'binance\publicTrade\symbol=XRPUSDT',
    'bybit\publicTrade\symbol=BNBUSDT',
    'binance\publicTrade\symbol=BNBUSDT'
)
$HarvestOk = $true
if (-not $DryRun) {
    foreach ($rel in $NodePaths) {
        $full = Join-Path (Join-Path $HarvestDir 'raw') $rel
        if (-not (Test-Path $full)) {
            $HarvestOk = $false
            Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $full + ")")
        }
    }
}

if (-not $HarvestOk) {
    Record-Step -Name 'H14_GPU_CHECK' -Status 'SKIP' -Rc 0 -Dur 0 -Detail 'Harvester-Pfad(e) fehlen (12-Node-Panel unvollstaendig)'
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-rc=2-Bug meiden).
    $rcGpu = Invoke-Step -Name 'H14_GPU_CHECK' -TimeoutSec $TmoGpuCheck -SkipDetail $SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c14_panellag.py'),
        '--check-gpu-only',
        '--out-dir', (Join-Path $RunDir 'h14')
    )
    if ($rcGpu -eq 0) {
        [void](Invoke-Step -Name 'H14_PANELLAG' -TimeoutSec $TmoFull -SkipDetail $SkipMsg -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c14_panellag.py'),
            '--base-dir', $HarvestDir,
            '--window-a-start', $WinAStart, '--window-a-end', $WinAEnd,
            '--window-b-start', $WinBStart, '--window-b-end', $WinBEnd,
            '--n-null', "$NNull", '--seed', "$Seed", '--device', 'cuda',
            '--ckpt-dir', $CkptDir,
            '--out-dir', (Join-Path $RunDir 'h14')
        ))
    } elseif ($rcGpu -eq 2) {
        Write-Host ("SKIP: " + $SkipMsg)
    }
}

# -- Zusammenfassung -----------------------------------------------------
$ok = ($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = ($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = ($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-14 Conditional Cross-Venue-Lead-Lag-Graph (Node-Ablation-Cross-Attention) - T3 (GPU zwingend)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only)")
[void]$sb.AppendLine("- **Checkpoints (STABIL, ueberlebt Neustarts):** ``" + $CkptDir + "``")
[void]$sb.AppendLine("- **Panel:** 12 Nodes = BTC/ETH x {Bybit, Binance, Deribit-PERP} + SOL/BNB/XRP x {Bybit, Binance}, publicTrade 1s-Grid")
[void]$sb.AppendLine("- **Fenster:** W1 " + $WinAStart + ".." + $WinAEnd + " | W2 " + $WinBStart + ".." + $WinBEnd + " (identisch H-09/H-12)")
[void]$sb.AppendLine("- **Methodik (vorregistriert):** pro Node PatchTST-Style-Encoder (m18-Wiederverwendung) + Cross-Node-Multi-Head-Attention, Target = Vorzeichen der naechsten 10s-Rendite. T(j->i) = OOS-Delta-Log-Loss (Vollmodell vs. Single-Source-j-Retrain-Ablation). n_null=" + $NNull + " Retrainings je Fenster (zirkulaeres Surrogat), seed=" + $Seed + " | F-PANELLAG BH-FDR a=0.10 ueber 99 Non-BTC-Source-Kanten je Fenster")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE Kosten-/Ertragsrechnung.")
[void]$sb.AppendLine("- **RESUME-FAEHIG:** ~226 Trainings, ~2-3 GPU-Tage total - dieser Runner braucht typischerweise MEHRERE Aufrufe ueber mehrere Naechte; jeder Aufruf setzt aus den Checkpoints in ``" + $CkptDir + "`` fort. Ein TIMEOUT/FAIL bei unvollstaendigem Plan ist NORMAL, kein Datenverlust.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Schritte (dieser Aufruf)")
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
    [void]$sb.AppendLine("*SKIP: " + $SkipMsg + ". Ein voller Lauf ohne echtes CUDA-Device ist NIEMALS verdikt-tragend (Registry H-14) und wurde deshalb NICHT gestartet.*")
} elseif ($exit -eq 1) {
    [void]$sb.AppendLine("*FAIL/TIMEOUT bei diesem Aufruf. Pruefe ``" + (Join-Path $RunDir 'H14_PANELLAG.err.log') + "``. Falls TIMEOUT: das ist bei ~226 Trainings ERWARTET -")
    [void]$sb.AppendLine("Fortschritt liegt sicher in ``" + $CkptDir + "`` (atomic writes je abgeschlossenem Training). EINFACH DIESES SKRIPT ERNEUT STARTEN -")
    [void]$sb.AppendLine("es ueberspringt alle bereits abgeschlossenen Trainings und macht nur mit den fehlenden weiter. c14_panellag_results.json wird")
    [void]$sb.AppendLine("erst geschrieben, wenn ALLE Trainings beider Fenster fertig sind (rc=0).*")
} else {
    [void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-14 (Roh-JSON unter ``h14\c14_panellag_results.json``).")
    [void]$sb.AppendLine("WEITER verlangt in BEIDEN Fenstern mindestens eine gerichtete Non-BTC-Source-Kante ueber dem 95. Perzentil")
    [void]$sb.AppendLine("der ~100-Surrogat-Null UND BH-FDR a=0.10 ueber F-PANELLAG ueberlebend. DROP (hartes Ein-Fenster-Kriterium):")
    [void]$sb.AppendLine("null ueberlebende Non-BTC-Source-Kanten in einem Fenster. BTC->ETH ist Positivkontrolle (vom Pass ausgeschlossen;")
    [void]$sb.AppendLine("Scheitern = methodisch invalide, kein Verdikt, KEIN DROP). Pruefe im JSON zwingend ``compute_gating.gate_valid``")
    [void]$sb.AppendLine("(muss true sein) und ``weiter_indication`` (null = nicht verdikt-tragend, sollte bei echtem GPU-Lauf nicht")
    [void]$sb.AppendLine("vorkommen). Kein Graubereich, keine nachtraegliche Kanten-/Schwellen-Anpassung. A-priori: DROP erwartet.")
    [void]$sb.AppendLine("Ergebnisse (kompletten Ordner ``" + $RunDir + "`` + ``" + $CkptDir + "``) hochladen -> Morgen-Auswertung.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
