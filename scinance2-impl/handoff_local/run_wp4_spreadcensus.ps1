# ========================================================================
# run_wp4_spreadcensus.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 8, WP-4)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_wp4_spreadcensus.ps1
#
# WP-4 = Quote-Spread-Zensus (DEC-40) - entscheidet den Maker-Spread-
# Capture-Kandidaten BINAER: gemessener Top-of-Book-Spread (Minutenraster
# via Snapshot+Delta-Replay, gleiche Maschinerie wie WP-2) gegen die
# kanonische Maker-Gebuehr (FEE_MAKER = 2 bp je Bein). Liegt der halbe
# Median-Spread unter der Gebuehr je Bein, ist der Kandidat ohne weiteren
# Aufwand tot; liegt er darueber, existiert erstmals die Zahl, die der
# Entwurf bisher nur behauptet hat.
#
# Fenster: REZENZ zuerst (BTC ab 2026-06-22, ETH ab 2026-06-19 - die
# orderbook.1000-Aera; aktuelle Spreads entscheiden eine aktuelle
# Strategie) plus ein historisches Referenzfenster (BTC 2024Q1).
# Der WP-2-Tilt-Store bleibt unberuehrt (eigener spread_1min-Store).
#
# Schritte: WP4_SPREAD. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (Harvester fehlt).
# Ergebnisse: scinance2-impl\handoff_local\results\wp4_<timestamp>\
#             + SUMMARY_<datum>.md
#
# Optionale Env-Overrides: HARVEST_DIR, L2TILT_DIR, WP4_RESULTS_DIR,
# WP4_TIMEOUT_SEC (Default 14400 = 4 h),
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$TiltDir = if ($env:L2TILT_DIR) { $env:L2TILT_DIR } else { Join-Path $RepoRoot 'data\l2tilt' }
$TmoStep = if ($env:WP4_TIMEOUT_SEC) { [int]$env:WP4_TIMEOUT_SEC } else { 14400 }

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
$ResultsBase = if ($env:WP4_RESULTS_DIR) { $env:WP4_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("wp4_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'wp4') | Out-Null
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

Write-Host ("RUN_WP4 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " (read-only) -> Spread-Store: " + $TiltDir + " | Rezenz-Fenster + 2024Q1-Referenz")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$HarvestOk = $true
$rawPath = Join-Path $HarvestDir 'raw\bybit'
if ((-not $DryRun) -and (-not (Test-Path $rawPath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $rawPath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\wp4_spread_census.py'
if (-not $HarvestOk) {
    Record-Step -Name 'WP4_SPREAD' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester fehlt (" + $rawPath + ")")
} else {
    [void](Invoke-Step -Name 'WP4_SPREAD' -TimeoutSec $TmoStep -OkRcs @(0) -CmdArgs @(
        $CliScript,
        '--base-dir', $HarvestDir,
        '--out-dir', $TiltDir,
        '--report-dir', (Join-Path $RunDir 'wp4')
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
[void]$sb.AppendLine("# WP-4 Quote-Spread-Zensus (DEC-40) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) -> Spread-Store ``" + $TiltDir + "`` (spread_1min; WP-2-Store unberuehrt)")
[void]$sb.AppendLine("- **Entscheidungsgroesse:** halber Median-Spread vs. FEE_MAKER (2 bp/Bein) - binaere Vorfrage des Maker-Kandidaten (DEC-40). Report: wp4\wp4_spread_census.json")
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
    [void]$sb.AppendLine("*Report unter ``wp4\wp4_spread_census.json``. ENTSCHEIDUNGSREGEL (DEC-40):")
    [void]$sb.AppendLine("halber Median-Spread < FEE_MAKER je Bein -> Maker-Kandidat TOT ohne weiteren")
    [void]$sb.AppendLine("Aufwand; darueber -> H-25-Registrierung wird diskutabel. Ergebnisse hochladen.*")
} elseif ($exit -eq 2) {
    [void]$sb.AppendLine("**SKIP** - kein Harvester oder keine orderbook-Streams gefunden.")
} else {
    [void]$sb.AppendLine("**FEHLER** - ``WP4_SPREAD.err.log`` pruefen.")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
