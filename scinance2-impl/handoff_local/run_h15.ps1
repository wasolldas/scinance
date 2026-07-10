# ========================================================================
# run_h15.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-15)
#
# Aufruf (keine Pflicht-Parameter, laeuft Stunden - ueber Nacht):
#   powershell -ExecutionPolicy Bypass -File .\run_h15.ps1
#
# H-15 = C-15 Trade-Tape-Event-Grammatik jenseits Markov (F-GRAMMAR).
# Decoder-only Causal-Transformer (~2-4M Parameter, Kontext 1024 Token) vs.
# KT-geglaettetes Variable-Order-Markov (k<=4), gleicher Train-Fold, purged
# Walk-Forward (4 Folds, 1-Tag-Embargo, 3 Seeds), Null via >=200 Within-
# Hour-of-Day-Block-Shuffle-Surrogate (Blocklaenge 256 Events). KAPITALFREI:
# reine Existence-of-Structure-Messung, KEINE Kapital-Metriken.
#
# WICHTIG - Compute-Gating (verbindlich): ein verdikt-tragender Lauf braucht
# echtes CUDA (Registry: "GPU, zwingend"). Dieser Runner prueft VOR dem
# Hauptlauf per `--check-gpu-only`:
#   * CUDA verfuegbar      -> MODE=full (Standard), volles Gate.
#   * CUDA NICHT verfuegbar -> sauberer SKIP (exit 2), KEIN automatischer
#     CPU-Fallback. Override: $env:MODE='mechanics' (dann NIE verdikt-
#     tragend, gate_valid bleibt false).
#
# Datenbasis (Registry H-15, vorregistriert): Basis-Bestand 2026-03-27..
# Cutoff (~100 Tage), 5 Bybit-Perp-Symbole, publicTrade-Tokenstream je
# Symbol. EIN Fenster (Purged Walk-Forward, kein W1/W2-Split).
# >=200 Surrogate, F-GRAMMAR BH-FDR a=0.10.
#
# EIN Block: H15_GRAMMAR. Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h15_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-15).
#
# Optionale Env-Overrides: HARVEST_DIR, MODE (full|mechanics, Default full),
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols     = 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT'
$DataStart   = '2026-03-27'
$DataEnd     = '2026-07-04'
$NFolds      = 4
$EmbargoDays = 1
$Seeds       = '42,43,44'
$NSurrogates = 200
$BlockLen    = 256
$Mode        = if ($env:MODE) { $env:MODE } else { 'full' }
$TmoStep     = 43200   # 12h Budget fuer den einen Gesamtblock

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h15_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h15') | Out-Null
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

Write-Host ("RUN_H15 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Panel: " + $Symbols + " x publicTrade | Raster " + $DataStart + ".." + $DataEnd)
Write-Host ("Walk-Forward: " + $NFolds + " Folds, " + $EmbargoDays + "-Tag-Embargo, Seeds " + $Seeds + " | Surrogate " + $NSurrogates + " (Block " + $BlockLen + ") | Modus " + $Mode)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$Script = Join-Path $RepoRoot 'scripts\c15_grammar.py'
$TradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'

$HarvestOk = $true
if (-not $DryRun) {
    if (-not (Test-Path $TradePath)) {
        $HarvestOk = $false
        Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $TradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
    }
}

if (-not $HarvestOk) {
    Record-Step -Name 'H15_GRAMMAR' -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $TradePath + ")")
} else {
    # Compute-Gate-Vorlauf: --check-gpu-only ist eine reine Statusabfrage
    # (rc=0 immer), NIE der eigentliche Lauf.
    $GpuLog = Join-Path $RunDir 'gpu_status.json'
    $CudaOk = $false
    if ($DryRun) {
        Set-Content -Path $GpuLog -Value '[DRY-RUN] check-gpu-only'
        $CudaOk = $true
    } else {
        & $PythonExe $Script --check-gpu-only 1>$GpuLog 2>(Join-Path $RunDir 'gpu_status.err.log')
        $gpuText = Get-Content $GpuLog -Raw -ErrorAction SilentlyContinue
        if ($gpuText -match '"cuda_available":\s*true') { $CudaOk = $true }
    }
    Write-Host ("GPU-Status: " + ((Get-Content $GpuLog -Raw -ErrorAction SilentlyContinue) -replace "`r?`n", ' '))

    if ($Mode -eq 'full' -and -not $DryRun -and -not $CudaOk) {
        Write-Host "WARNUNG: kein CUDA-Geraet gefunden - Modus 'full' waere nicht verdikt-faehig (Registry: GPU, zwingend)."
        Write-Host "Sauberer SKIP statt irrefuehrendem CPU-Ersatzlauf. Override: `$env:MODE='mechanics' (NIE verdikt-tragend)."
        Record-Step -Name 'H15_GRAMMAR' -Status 'SKIP' -Rc 0 -Dur 0 -Detail "kein CUDA-Geraet (Modus full)"
    } else {
        [void](Invoke-Step -Name 'H15_GRAMMAR' -TimeoutSec $TmoStep -CmdArgs @(
            $Script,
            '--base-dir', $HarvestDir, '--symbols', $Symbols,
            '--data-start', $DataStart, '--data-end', $DataEnd,
            '--mode', $Mode,
            '--n-folds', "$NFolds", '--embargo-days', "$EmbargoDays",
            '--seeds', $Seeds, '--n-surrogates', "$NSurrogates", '--block-len', "$BlockLen",
            '--out-dir', (Join-Path $RunDir 'h15')
        ))
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
[void]$sb.AppendLine("# H-15 C-15 Trade-Tape-Event-Grammatik Mess-Gate - T3")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Modus:** " + $Mode + " (full = verdikt-faehig, braucht CUDA; mechanics = NIE verdikt-tragend)")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Panel: " + $Symbols + " x publicTrade")
[void]$sb.AppendLine("- **Raster:** " + $DataStart + ".." + $DataEnd)
[void]$sb.AppendLine("- **Walk-Forward:** " + $NFolds + " Folds, " + $EmbargoDays + "-Tag-Embargo, Seeds " + $Seeds)
[void]$sb.AppendLine("- **Surrogate " + $NSurrogates + " (Within-Hour-of-Day-Block-Shuffle, Blocklaenge " + $BlockLen + ") | F-GRAMMAR BH-FDR a=0.10**")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Existence-of-Structure-Messung, KEINE Kapital-Metriken.")
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
[void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-15 (Roh-JSON unter ``h15\c15_grammar_results.json``).")
[void]$sb.AppendLine("WEITER verlangt: OOS-Token-CE des Transformers >=2% relativ niedriger als die beste Markov-k-")
[void]$sb.AppendLine("(k<=4)-Baseline bei >=4/5 Symbolen UND CE-Luecke ueber dem 95. Perzentil der Surrogat-Luecken-")
[void]$sb.AppendLine("Verteilung, nach BH-FDR a=0.10 ueber F-GRAMMAR. Hartes Kriterium, kein GRAUBEREICH. WICHTIG:")
[void]$sb.AppendLine("nur bei ran_on_gpu=true UND gate_valid=true ist ein Urteil zulaessig.")
[void]$sb.AppendLine("A-priori: DROP erwartet. Ergebnisse hochladen -> GL-Zaehlung.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
