# ========================================================================
# run_h16.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-16)
#
# Aufruf (keine Pflicht-Parameter, laeuft ueber Nacht unbeaufsichtigt):
#   powershell -ExecutionPolicy Bypass -File .\run_h16.ps1
#
# H-16 = Time-Arrow-CNN: Classifier-Two-Sample-Test (Lopez-Paz & Oquab 2017).
# Ein ResNet-18 klassifiziert FORWARD vs. TIME-REVERSED Morlet-CWT-Log-Power-
# Scalogramme der 1s-signed-Trade-Imbalance-Serie (5 Symbole). Reversal auf
# der Roh-Serie VOR der CWT. Bayes-optimale AUC=0.5 ist die exakte Null.
# KAPITALFREI: reine Struktur-/Existenzfrage, KEINE Kosten-/Ertragsrechnung.
# GPU ZWINGEND: ein Lauf ohne echtes CUDA-Device ist NIEMALS verdikt-tragend.
#
# DIFFERENZIERUNG (Registry-Pflicht, wortgleich im JSON/MD-Report): H-16 ist
# KEIN Duplikat des gesperrten Informationstheorie-/Nichtlineare-Dynamik-
# Clusters (PE/TE/RQA/MFDFA/TDA) - kein Entropie-Schaetzer, andere Eigenschaft
# (Zeit-Irreversibilitaet statt Komplexitaet), exakte Bayes-Null statt
# geschaetztem Schwellenwert.
#
# Ablauf: (1) H16_GPU_CHECK via --check-gpu-only (rc 2 = kein CUDA -> SKIP,
# der volle Lauf startet dann NICHT), (2) nur bei rc 0: H16_ARROW voller Lauf
# (5 Symbole, 5 Seeds Haupt-C2ST + 20 IAAFT-Surrogat-Retrainings + 3
# Ablations-Seeds je Symbol, F-ARROW BH-FDR a=0.10). Gate-neutral - der
# gate-auditor urteilt gegen H-16; eine Leak-Kontrolle > 0.52 markiert das
# Modul selbst als METHOD_INVALID_NO_VERDICT (eigener Zustand, KEIN DROP).
#
# Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP (kein CUDA-Device gefunden).
# Ergebnisse: scinance2-impl\handoff_local\results\h16_<timestamp>\
#             + SUMMARY_<datum>.md.
#
# Optionale Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC),
# H16_END_DATE (Cutoff, default = gestern UTC), H16_N_SEEDS, H16_N_SURROGATES,
# H16_ABLATION_SEEDS, H16_TIMEOUT_SEC (Default 8h Budget).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols   = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$StartDate = '2026-03-27'
$EndDate   = if ($env:H16_END_DATE) { $env:H16_END_DATE } else { (Get-Date).ToUniversalTime().AddDays(-1).ToString('yyyy-MM-dd') }
$Seed      = 42
$NSeeds       = if ($env:H16_N_SEEDS) { [int]$env:H16_N_SEEDS } else { 5 }
$NSurrogates  = if ($env:H16_N_SURROGATES) { [int]$env:H16_N_SURROGATES } else { 20 }
$AblationSeeds = if ($env:H16_ABLATION_SEEDS) { [int]$env:H16_ABLATION_SEEDS } else { 3 }
$TmoGpuCheck = 120
$TmoFull   = if ($env:H16_TIMEOUT_SEC) { [int]$env:H16_TIMEOUT_SEC } else { 28800 }  # 8h Default

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h16_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h16') | Out-Null
$StepsTsv = Join-Path $RunDir 'steps.tsv'

$Script:Results = New-Object System.Collections.ArrayList

function Record-Step {
    param([string]$Name, [string]$Status, [int]$Rc, [int]$Dur, [string]$Detail)
    Add-Content -Path $StepsTsv -Value ($Name + "`t" + $Status + "`t" + $Rc + "`t" + $Dur + "`t" + $Detail)
    [void]$Script:Results.Add([pscustomobject]@{ Name = $Name; Status = $Status; Rc = $Rc; Dur = $Dur; Detail = $Detail })
}

function Invoke-Step {
    param([string]$Name, [int]$TimeoutSec, [string[]]$CmdArgs, [string]$SkipDetail)
    # rc 2 des CLI = kein Compute-Gate -> Status SKIP (kein FAIL).
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

Write-Host ("RUN_H16 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Symbole: " + $Symbols + " | Fenster: " + $StartDate + ".." + $EndDate)
Write-Host ("Seeds=" + $NSeeds + " Surrogate=" + $NSurrogates + " Ablation=" + $AblationSeeds + " Seed=" + $Seed)
Write-Host ("H-16 ist GPU ZWINGEND: erst ehrlicher Compute-Check, dann (nur bei echtem CUDA) voller Lauf.")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$SkipMsg = 'H-16 SKIP - kein verdikt-taugliches CUDA-Device gefunden (torch/CUDA-Check negativ)'

$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$HarvestOk = $true
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

if (-not $HarvestOk) {
    Record-Step -Name 'H16_GPU_CHECK' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester-Pfad fehlt (" + $tradePath + ")")
} else {
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-rc=2-Bug meiden).
    $rcGpu = Invoke-Step -Name 'H16_GPU_CHECK' -TimeoutSec $TmoGpuCheck -SkipDetail $SkipMsg -CmdArgs @(
        (Join-Path $RepoRoot 'scripts\c16_arrow.py'),
        '--check-gpu-only',
        '--out-dir', (Join-Path $RunDir 'h16')
    )
    if ($rcGpu -eq 0) {
        [void](Invoke-Step -Name 'H16_ARROW' -TimeoutSec $TmoFull -SkipDetail $SkipMsg -CmdArgs @(
            (Join-Path $RepoRoot 'scripts\c16_arrow.py'),
            '--base-dir', $HarvestDir, '--symbols', $Symbols,
            '--start-date', $StartDate, '--end-date', $EndDate,
            '--n-seeds', "$NSeeds", '--n-surrogates', "$NSurrogates",
            '--ablation-seeds', "$AblationSeeds", '--seed', "$Seed",
            '--device', 'cuda',
            '--out-dir', (Join-Path $RunDir 'h16')
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
[void]$sb.AppendLine("# H-16 Time-Arrow-CNN Mess-Gate - T3 (GPU zwingend)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Fenster:** " + $StartDate + ".." + $EndDate + " | Held-out-Day-Split (letzte 20% valide Tage)")
[void]$sb.AppendLine("- **Methodik (vorregistriert):** Morlet-CWT-Log-Power-Scalogram (64 Skalen 2s-256s x 512 Zeit-Bins, Stride 64s), ResNet-18, Reversal auf Roh-Serie VOR CWT, " + $NSeeds + " Seeds, " + $NSurrogates + " IAAFT-Surrogat-Retrainings (Pflicht-Leak-Kontrolle <=0.52), " + $AblationSeeds + " Ablations-Seeds auf |Imbalance| (Pflicht-Report, nicht urteilstragend), Seed " + $Seed + " | F-ARROW BH-FDR a=0.10")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE Kosten-/Ertragsrechnung.")
[void]$sb.AppendLine("- **DIFFERENZIERUNG (Registry-Pflicht):** KEIN Duplikat des gesperrten Informationstheorie-/Nichtlineare-Dynamik-Clusters (PE/TE/RQA/MFDFA/TDA) - kein Entropie-Schaetzer, gemessene Eigenschaft ist Zeit-Irreversibilitaet statt Komplexitaet/Vorhersagbarkeit, exakte Bayes-Null AUC=0.5 statt geschaetztem Schwellenwert.")
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
    [void]$sb.AppendLine("*SKIP: " + $SkipMsg + ". Ein voller Lauf ohne echtes CUDA-Device ist NIEMALS verdikt-tragend (Registry H-16) und wurde deshalb NICHT gestartet.*")
} else {
    [void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-16 (Roh-JSON unter ``h16\c16_arrow_results.json``).")
    [void]$sb.AppendLine("WEITER verlangt: Held-out-Day-Forward-vs-Reversed-AUC >=0.60 MIT IAAFT-Surrogat-Null-95.-Perzentil<0.53,")
    [void]$sb.AppendLine("bei >=4/5 Symbolen nach BH-FDR a=0.10 ueber F-ARROW, UND die Leak-Kontrolle bleibt <=0.52")
    [void]$sb.AppendLine("(sonst methodisch invalide -> status=METHOD_INVALID_NO_VERDICT, eigener Zustand, KEIN DROP).")
    [void]$sb.AppendLine("DROP nur: AUC<0.60 bei <4/5 Symbolen. Kein Graubereich, keine nachtraegliche Skalen-/")
    [void]$sb.AppendLine("Fenster-Anpassung. Ergebnisse hochladen -> Morgen-Auswertung.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
