# ========================================================================
# run_wp2_l2extract.ps1 - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 6, WP-2)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_wp2_l2extract.ps1
#
# WP-2 = L2-Tilt-Ein-Pass fuer H-22 (Snapshot+Delta-Buchrekonstruktion).
# Registrierte Vorleistung (Registry H-22, Zensus-Befund DEC-36): das
# bybit-Orderbook ist ueber die GESAMTE Historie Snapshot(~2/Tag)+Delta,
# also wird das Buch je Fenster sequenziell replayed (Update-ID-
# Kontinuitaet gezaehlt, Validierung an jedem Voll-Snapshot mit Resync,
# Tage mit >10 Bruechen LAUT verworfen) und der Near-Touch-Tilt
# (+-25 bp um Mid) im Minutenraster abgetastet. Ausgabe hash-gepinnt
# je Tag (WP-0-Muster) nach data\l2tilt (NEUER Pfad).
#
# Fenster (registriert): BTC W-L2-1 2023-07-01..2024-06-30 und
# W-L2-2 2024-07-01..2025-06-30 (urteilstragend), ETH 2023-04-01..
# 2024-04-30 (nur Bericht). Der 85%-Abdeckungs-Floor wird hier
# INFORMATIV gemeldet; erzwungen wird er vom H-22-Treiber.
#
# KAPITALFREI: reine Mess-Extraktion. Ein Fenster-Pass ist deterministisch
# (Wiederholung bit-identisch); bei Abbruch einfach neu starten - der
# Pass laeuft dann komplett neu (Ein-Pass-Semantik, kein Tages-Resume).
#
# Schritte: WP2_L2EXTRACT (3 Fenster). Fingerabdruecke je Fenster in
# wp2\l2tilt_extract.json.
# Exit: 0 = OK * 1 = FAIL * 2 = SKIP (Harvester fehlt).
# Ergebnisse: scinance2-impl\handoff_local\results\wp2_<timestamp>\
#             + SUMMARY_<datum>.md
#
# Optionale Env-Overrides: HARVEST_DIR, L2TILT_DIR, WP2_RESULTS_DIR,
# WP2_TIMEOUT_SEC (Default 43200 = 12 h),
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }
$TiltDir   = if ($env:L2TILT_DIR) { $env:L2TILT_DIR } else { Join-Path $RepoRoot 'data\l2tilt' }

# ~1100 Fenster-Tage x 144k-864k Records: mehrere Stunden. 12 h Budget.
$TmoStep = if ($env:WP2_TIMEOUT_SEC) { [int]$env:WP2_TIMEOUT_SEC } else { 43200 }

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
$ResultsBase = if ($env:WP2_RESULTS_DIR) { $env:WP2_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("wp2_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'wp2') | Out-Null
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
                $detail = "TIMEOUT nach $TimeoutSec s (Cache ist inkrementell - einfach neu starten)"
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

Write-Host ("RUN_WP2 (T3) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " (read-only) -> Tilt-Store: " + $TiltDir + " (NEUER Pfad)")
Write-Host "Fenster: BTC W-L2-1/W-L2-2 (urteilstragend) + ETH (Bericht) | Ein-Pass je Fenster"
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$HarvestOk = $true
$tradePath = Join-Path $HarvestDir 'raw\bybit\orderbook'
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\wp2_l2_extract.py'
$OutJson = Join-Path (Join-Path $RunDir 'wp2') 'l2tilt_extract.json'
$rcRun = 2
if (-not $HarvestOk) {
    Record-Step -Name 'WP2_L2EXTRACT' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
} else {
    $rcRun = Invoke-Step -Name 'WP2_L2EXTRACT' -TimeoutSec $TmoStep -OkRcs @(0) -CmdArgs @(
        $CliScript,
        '--base-dir', $HarvestDir,
        '--out-dir', $TiltDir
    )
    # stdout (JSON mit Fingerabdruecken) in die Ergebnisse kopieren
    $stepLog = Join-Path $RunDir 'WP2_L2EXTRACT.log'
    if (Test-Path $stepLog) { Copy-Item $stepLog $OutJson -Force }
}

# -- Zusammenfassung -----------------------------------------------------
$ok = @($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = @($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = @($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0
if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# WP-2 L2-Tilt-Ein-Pass (Welle 6, H-22-Vorleistung) - T3")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) -> **Tilt-Store:** ``" + $TiltDir + "``")
[void]$sb.AppendLine("- **Fenster:** BTC W-L2-1 2023-07-01..2024-06-30, W-L2-2 2024-07-01..2025-06-30 (urteilstragend); ETH 2023-04-01..2024-04-30 (Bericht)")
[void]$sb.AppendLine("- **Methode:** sequentieller Snapshot+Delta-Replay je Fenster; Update-ID-Brueche gezaehlt, Snapshot-Validierung mit Resync, >10 Brueche/Tag = lauter Verwurf; Tilt +-25bp um Mid, Minutenraster; SHA-256 je Tag.")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Mess-Infrastruktur, kein Kosten-/PnL-Begriff.")
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
    [void]$sb.AppendLine("*Fenster-Fingerabdruecke und Abdeckung in ``wp2\l2tilt_extract.json``. Der")
    [void]$sb.AppendLine("85%-Abdeckungs-Floor wird hier informativ gemeldet; erzwungen wird er vom")
    [void]$sb.AppendLine("H-22-Treiber vor dem Lauf. Ergebnisse hochladen -> H-22-Lauf folgt.*")
} elseif ($exit -eq 1) {
    [void]$sb.AppendLine("**FEHLER** - ``WP2_L2EXTRACT.err.log`` pruefen. Der Pass ist nach Klaerung")
    [void]$sb.AppendLine("gefahrlos wiederholbar (Ein-Pass, deterministisch).")
} else {
    [void]$sb.AppendLine("**SKIP** - Harvester/Orderbook-Stream nicht erreichbar. Junction pruefen.")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
