# ========================================================================
# run_wp1_l2census.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 6, WP-1)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_wp1_l2census.ps1
#
# WP-1 = L2-Pre-Flight-Zensus (Synthese Welle 6, Abschnitt 3) - READ-ONLY Discovery,
# KEIN Byte Feature-Extraktion. Harte Vorbedingung fuer die Registrierung
# von L2-TILT: Die Inventur fand bybit-L2 deutlich tiefer als dokumentiert
# (BTC 961 Tage, 74 % Abdeckung), aber mit vermutetem Format-Bruch
# (historisch orderbook.500 SNAPSHOT, live orderbook.1000 DELTA). Der
# Zensus misst je Symbol auf einer Tages-Stichprobe: Record-Typ- und
# Topic-Verteilung, tatsaechliche Buchtiefe (json_array_length, nicht
# Topic-Label), Bytes, Sequenz-Brueche der Update-IDs, Regime-Zeitleiste.
#
# ENTSCHEIDUNGSREGEL (vorab fixiert): Faellt der Zensus gegen die
# Snapshot+Delta-Lesart aus, wird L2-TILT NICHT registriert.
#
# Schritte: WP1_L2CENSUS. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (kein L2/kein Harvester).
# Ergebnisse: scinance2-impl\handoff_local\results\wp1_<timestamp>\
#             + SUMMARY_<datum>.md
#
# Optionale Env-Overrides: HARVEST_DIR, WP1_RESULTS_DIR, WP1_TIMEOUT_SEC
# (Default 14400 = 4 h), WP1_SYMBOLS, WP1_SAMPLE_EVERY,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbols     = if ($env:WP1_SYMBOLS) { $env:WP1_SYMBOLS } else { 'BTCUSDT,ETHUSDT' }
$SampleEvery = if ($env:WP1_SAMPLE_EVERY) { [int]$env:WP1_SAMPLE_EVERY } else { 14 }
$TmoStep     = if ($env:WP1_TIMEOUT_SEC) { [int]$env:WP1_TIMEOUT_SEC } else { 14400 }

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
$ResultsBase = if ($env:WP1_RESULTS_DIR) { $env:WP1_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("wp1_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'wp1') | Out-Null
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

Write-Host ("RUN_WP1 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " (read-only) | Symbole: " + $Symbols + " | Sampling: jeder " + $SampleEvery + ". Tag")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$HarvestOk = $true
$rawPath = Join-Path $HarvestDir 'raw\bybit'
if ((-not $DryRun) -and (-not (Test-Path $rawPath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $rawPath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\l2_census.py'
if (-not $HarvestOk) {
    Record-Step -Name 'WP1_L2CENSUS' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester fehlt (" + $rawPath + ")")
} else {
    [void](Invoke-Step -Name 'WP1_L2CENSUS' -TimeoutSec $TmoStep -OkRcs @(0) -SkipRcs @(2) -CmdArgs @(
        $CliScript,
        '--base-dir', $HarvestDir,
        '--symbols', $Symbols,
        '--sample-every', "$SampleEvery",
        '--out-dir', (Join-Path $RunDir 'wp1')
    ))
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# WP-1 L2-Pre-Flight-Zensus (Welle 6) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Sampling:** jeder " + $SampleEvery + ". Tag + erster/letzter je Stream")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Discovery, kein Byte Feature-Extraktion.")
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
if ($exit -eq 0) {
    [void]$sb.AppendLine("*Zensus unter ``wp1\l2_census.{json,md}``. ENTSCHEIDUNGSREGEL (vorab fixiert):")
    [void]$sb.AppendLine("Faellt der Zensus gegen die Snapshot+Delta-Lesart aus, wird L2-TILT NICHT")
    [void]$sb.AppendLine("registriert. Ergebnisse hochladen -> Orchestrator entscheidet die H-22-Registrierung.*")
} elseif ($exit -eq 2) {
    [void]$sb.AppendLine("**SKIP** - kein Harvester oder keine orderbook-Streams gefunden.")
} else {
    [void]$sb.AppendLine("**FEHLER** - ``WP1_L2CENSUS.err.log`` pruefen. Einzelne Fehlertage sind im Zensus")
    [void]$sb.AppendLine("selbst als nicht-fatal verzeichnet; ein FAIL hier ist ein harter Abbruch.")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
