# ========================================================================
# run_h11c.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0, H-11c)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h11c.ps1
#
# H-11c = AnEn gegen DISPERSIONS-GEMATCHTE HAR-Baseline (Dressed-HAR).
# Registrierte Folge-Auflage aus GL-022: das H-11-Gate verglich eine
# DIRAC-Baseline mit einer 20-Mitglieder-Verteilung; das schenkt einem
# informationsfreien Prognostiker bereits CRPSS ~0,21-0,29, also das
# 4-5-Fache der registrierten 0,05-Schwelle. H-11c entfernt genau diesen
# Term: die HAR-PUNKTPROGNOSE bleibt unveraendert und wird lediglich mit
# einer k=20-Wolke aus der EMPIRISCHEN Verteilung ihrer eigenen In-Fit-
# Residuen desselben Monats-Refits umhuellt (kein Look-ahead, keine
# Verteilungsannahme, kein Zufall). BEIDE Seiten werden mit derselben
# registrierten Ensemble-CRPS-Formel bewertet.
#
# KAPITALFREI: reines Mess-Gate. KEINE bps/Edge/PnL/Friction-Rechnung -
# die 25-75x-Friktionsnotiz aus H-11 ist nach GL-022 E5 ENTKOPPELT.
#
# KEIN Re-Tuning: die Gewichte sind aus dem GL-022-Lauf eingefroren
# (BTC [2;2;0,5;0;0], ETH [2;0,5;0;0;0]) und im Code Konstanten. Deshalb
# entfaellt das 3124-Kombos-LOO-Grid - der Lauf dauert MINUTEN, nicht
# Stunden. Vorbedingung: die AnEn-Seite muss die archivierten GL-022-
# Summen exakt reproduzieren; tut sie das nicht, ist das Gate UNGUELTIG
# (rc=3, gate_valid=false) - laut, nicht still.
#
# Schritte: H11C_DRESSED. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (gesperrt) *
#           3 = AnEn-Seite reproduziert GL-022 NICHT (Gate ungueltig).
# Ergebnisse: scinance2-impl\handoff_local\results\h11c_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-11c).
#
# Optionale Env-Overrides: HARVEST_DIR, H11C_RESULTS_DIR, H11C_TIMEOUT_SEC,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols    = 'BTCUSDT,ETHUSDT'
$W1Start    = '2025-10-01'; $W1End   = '2026-03-26'
$W2Start    = '2026-03-27'; $W2End   = '2026-06-30'
$UnlockStart= '2024-03-27'; $UnlockEnd = '2026-03-26'
$MinUnlock  = 730
$KAnalogs   = 20
$Embargo    = 30
$BlockLen   = 5
$Bootstrap  = 1000
$Seed       = 42
# Ohne LOO-Grid dominiert der Panel-Bau. 2 h Budget ist grosszuegig.
$TmoStep    = if ($env:H11C_TIMEOUT_SEC) { [int]$env:H11C_TIMEOUT_SEC } else { 7200 }

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
$ResultsBase = if ($env:H11C_RESULTS_DIR) { $env:H11C_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("h11c_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h11c') | Out-Null
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

Write-Host ("RUN_H11C (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Symbole: " + $Symbols + " | Gewichte EINGEFROREN (kein Re-Tuning)")
Write-Host ("W1=" + $W1Start + ".." + $W1End + " | W2=" + $W2Start + ".." + $W2End + " | k=" + $KAnalogs + " Embargo=" + $Embargo + "d seed=" + $Seed)
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\c11c_dressed.py'
$rcRun = 2
if (-not $HarvestOk) {
    Record-Step -Name 'H11C_DRESSED' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
} else {
    $rcRun = Invoke-Step -Name 'H11C_DRESSED' -TimeoutSec $TmoStep -OkRcs @(0) -SkipRcs @(2) -CmdArgs @(
        $CliScript,
        '--base-dir', $HarvestDir, '--symbols', $Symbols,
        '--w1-start', $W1Start, '--w1-end', $W1End,
        '--w2-start', $W2Start, '--w2-end', $W2End,
        '--unlock-start', $UnlockStart, '--unlock-end', $UnlockEnd,
        '--min-unlock-days', "$MinUnlock",
        '--k', "$KAnalogs", '--embargo-days', "$Embargo",
        '--block-len', "$BlockLen", '--n-bootstrap', "$Bootstrap",
        '--seed', "$Seed",
        '--out-dir', (Join-Path $RunDir 'h11c')
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
[void]$sb.AppendLine("# H-11c AnEn gegen dispersions-gematchte HAR (Dressed-HAR) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only Junction) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Fenster:** W1=" + $W1Start + ".." + $W1End + " | W2=" + $W2Start + ".." + $W2End + " (identisch H-11)")
[void]$sb.AppendLine("- **Methode:** k=" + $KAnalogs + ", Embargo " + $Embargo + "d, Gewichte EINGEFROREN aus GL-022 (kein Re-Tuning); Baseline = HAR-Punktprognose unveraendert + k-Quantil-Wolke der eigenen In-Fit-Residuen; BEIDE Seiten mit derselben Ensemble-CRPS-Formel | F-ANEN-C BH-FDR a=0.10")
[void]$sb.AppendLine("- **KAPITALFREI** - reines Mess-Gate; die 25-75x-Friktionsnotiz aus H-11 ist nach GL-022 E5 ENTKOPPELT.")
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
    [void]$sb.AppendLine("**LAUT-FEHLER: Die AnEn-Seite reproduziert die archivierten GL-022-Summen NICHT.**")
    [void]$sb.AppendLine("``gate_valid=false`` - die Ergebnisse sind geschrieben, aber NICHT urteilstragend.")
    [void]$sb.AppendLine("Ursache klaeren (Datenstand veraendert? Gewichte? k? Fenster?), bevor irgendein")
    [void]$sb.AppendLine("Gate-Urteil gefaellt wird.")
} elseif ($exit -eq 2) {
    [void]$sb.AppendLine("**SKIP** - Entsperr-Bedingung unerfuellt oder Harvester nicht erreichbar. Kein Gate-Urteil.")
} else {
    [void]$sb.AppendLine("*Gate-Urteil faellt der gate-auditor gegen H-11c (Roh-JSON unter ``h11c\c11c_dressed_results.json``).")
    [void]$sb.AppendLine("WEITER verlangt: fuer >=1 Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS_dressed>=0.05 UND")
    [void]$sb.AppendLine("Block-Bootstrap-p<=0.05 nach BH-FDR a=0.10 ueber F-ANEN-C. Hartes Ein-Fenster-DROP,")
    [void]$sb.AppendLine("kein GRAUBEREICH, keine Nachsuche. A-priori: DROP erwartet (GL-022 E2/E3).")
    [void]$sb.AppendLine("Ergebnisse hochladen -> Gate-Log.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
