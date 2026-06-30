# ========================================================================
# run_h05c.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 3, H-05c)
#
# Aufruf (keine Pflicht-Parameter, laeuft ca. 10-30 min):
#   powershell -ExecutionPolicy Bypass -File .\run_h05c.ps1
#
# H-05c = C-01 OFI-Fade-TRADABILITY-Gate (SOLUSDT). Zweite NICHT-kapitalfreie
# Hypothese: das Gate konfrontiert die in GL-010 gemessene inverse OFI-Kante
# (SOL delta1s/delta5s) gegen die 11-bps-Friction-Wand nach 300-ms-Latenz-Haircut.
# HISTORISCHER BACKTEST MIT KOSTENMODELL auf read-only Harvester-Backfill -
# KEIN Live-Order-Code, KEIN Geldeinsatz (CLAUDE.md Paragraf 4). Kapital PARK.
#
# Datenbasis (DEC-15/DEC-16): read-only Junction data\harvest, SOLUSDT, zwei OOS-
# Fenster A@2026-04-15 + B@2026-05-15 (je 300k Ticks), delta {1,5}s (GL-010-Survivor).
#
# Bloecke (try/catch + Timeout + weitermachen, NIE offener Prompt):
#   H05C_PRIMARY   URTEILSTRAGEND: latency=300ms, friction=11bps, Taker (Default-
#                  Punkt). NUR hier faellt das Pass-Urteil (gate_valid_assumptions=true).
#   H05C_LAT100    ROBUSTHEIT (NICHT urteilstragend): latency=100ms.
#   H05C_LAT500    ROBUSTHEIT (NICHT urteilstragend): latency=500ms.
#   H05C_MAKER     SEKUNDAER (NICHT urteilstragend): --maker-secondary, adverse-
#                  selection-vorbehaltlich; gate_valid_assumptions=false.
#
# Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# Ergebnisse: scinance2-impl\handoff_local\results\h05c_<timestamp>\
#             + SUMMARY_<datum>.md (gate-auditor urteilt gegen H-05c).
#
# Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC).
# PS 5.1-kompatibel (handle-cache + BelowNormal + ASCII-Body).
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$HarvestDir = if ($env:HARVEST_DIR) { $env:HARVEST_DIR } else { Join-Path $RepoRoot 'data\harvest' }

$Symbol    = 'SOLUSDT'
$WinAStart = '2026-04-15'
$WinBStart = '2026-05-15'
$Deltas    = '1,5'
$MaxTicks  = 300000
$FrictionBps = 11
$LatPrimary  = 300
$LatLow      = 100
$LatHigh     = 500
$Bootstrap = 200
$Seed      = 42
$TmoStep   = 2400

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
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("h05c_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
foreach ($d in @('h05c','h05c_lat100','h05c_lat500','h05c_maker')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RunDir $d) | Out-Null
}
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
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] START " + $Name)
    $t0 = Get-Date; $rc = -1; $detail = ''
    if ($DryRun) {
        Add-Content -Path $log -Value ("[DRY-RUN] " + ($CmdArgs -join ' ')); $rc = $DryRc; $detail = "dry-run rc=$rc"
    } else {
        try {
            $quoted = @(); foreach ($a in $CmdArgs) { if ($a -match '\s') { $quoted += ('"' + $a + '"') } else { $quoted += $a } }
            $p = Start-Process -FilePath $PythonExe -ArgumentList $quoted -NoNewWindow -PassThru `
                 -RedirectStandardOutput $log -RedirectStandardError $errLog
            $null = $p.Handle
            try { $p.PriorityClass = 'BelowNormal' } catch { }
            if (-not $p.WaitForExit($TimeoutSec * 1000)) { try { $p.Kill() } catch { }; $rc = 124; $detail = "TIMEOUT nach $TimeoutSec s" }
            else { $rc = $p.ExitCode; if ($null -eq $rc) { $rc = -2; $detail = 'ExitCode null (Handle-Quirk)' } }
        } catch { $rc = -1; $detail = $_.Exception.Message }
    }
    $dur = [int]((Get-Date) - $t0).TotalSeconds
    $status = 'FAIL'; if ($rc -eq 0) { $status = 'OK' }
    if (-not $detail) { $detail = "rc=$rc" }
    Record-Step -Name $Name -Status $status -Rc $rc -Dur $dur -Detail $detail
    Write-Host ("[" + (Get-Date -Format 'HH:mm:ss') + "] END   " + $Name + ": " + $status + " (" + $detail + ", " + $dur + "s)")
    return $rc
}

Write-Host ("RUN_H05C (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Harvest: " + $HarvestDir + " | Symbol: " + $Symbol + " | Fenster A@" + $WinAStart + " B@" + $WinBStart + " | delta " + $Deltas)
Write-Host ("URTEILSTRAGEND: latency=" + $LatPrimary + "ms friction=" + $FrictionBps + "bps Taker")
Write-Host ("ROBUSTHEIT (NICHT urteilstragend): latency=" + $LatLow + "ms, " + $LatHigh + "ms, --maker-secondary")
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv." }

$Script = Join-Path $RepoRoot 'scripts\c01_ofi_tradability.py'
$tradePath = Join-Path $HarvestDir 'raw\bybit\publicTrade'
$HarvestOk = $true
if ((-not $DryRun) -and (-not (Test-Path $tradePath))) {
    $HarvestOk = $false
    Write-Host ("WARNUNG: Harvester-Pfad fehlt (" + $tradePath + ") - Junction data\harvest pruefen oder HARVEST_DIR setzen")
}

$CommonArgs = @('--base-dir', $HarvestDir, '--symbol', $Symbol,
    '--window-a-start', $WinAStart, '--window-b-start', $WinBStart,
    '--deltas', $Deltas, '--max-ticks', "$MaxTicks", '--friction-bps', "$FrictionBps",
    '--n-bootstrap', "$Bootstrap", '--seed', "$Seed")

if (-not $HarvestOk) {
    foreach ($n in @('H05C_PRIMARY','H05C_LAT100','H05C_LAT500','H05C_MAKER')) {
        Record-Step -Name $n -Status 'SKIP' -Rc 0 -Dur 0 -Detail ("Harvester fehlt (" + $tradePath + ")")
    }
} else {
    [void](Invoke-Step -Name 'H05C_PRIMARY' -TimeoutSec $TmoStep -CmdArgs ($CommonArgs + @('--latency-ms', "$LatPrimary", '--out-dir', (Join-Path $RunDir 'h05c'))))
    [void](Invoke-Step -Name 'H05C_LAT100'  -TimeoutSec $TmoStep -CmdArgs ($CommonArgs + @('--latency-ms', "$LatLow",  '--out-dir', (Join-Path $RunDir 'h05c_lat100'))))
    [void](Invoke-Step -Name 'H05C_LAT500'  -TimeoutSec $TmoStep -CmdArgs ($CommonArgs + @('--latency-ms', "$LatHigh", '--out-dir', (Join-Path $RunDir 'h05c_lat500'))))
    [void](Invoke-Step -Name 'H05C_MAKER'   -TimeoutSec $TmoStep -CmdArgs ($CommonArgs + @('--latency-ms', "$LatPrimary", '--maker-secondary', '--out-dir', (Join-Path $RunDir 'h05c_maker'))))
}

$ok = ($Script:Results | Where-Object { $_.Status -eq 'OK' }).Count
$fail = ($Script:Results | Where-Object { $_.Status -eq 'FAIL' }).Count
$skip = ($Script:Results | Where-Object { $_.Status -eq 'SKIP' }).Count
$exit = 0; if ($fail -gt 0) { $exit = 1 } elseif ($skip -gt 0) { $exit = 2 }

$SummaryPath = Join-Path $RunDir ("SUMMARY_" + $SummaryDate + ".md")
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# H-05c OFI-Fade-Tradability (C-01, SOLUSDT) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Harvest:** ``" + $HarvestDir + "`` (read-only) | Symbol " + $Symbol)
[void]$sb.AppendLine("- **Fenster (DEC-15):** A@" + $WinAStart + " + B@" + $WinBStart + ", je " + $MaxTicks + " Ticks | delta " + $Deltas + "s (GL-010-Survivor)")
[void]$sb.AppendLine("- **capital_free=FALSE** (Tradability), aber historischer Backtest mit Kostenmodell - KEIN Live-Order, KEIN Geld. Kapital PARK.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Urteilstragender Punkt (Anti-Gaming-Klausel)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("Das Pass-Urteil faellt AUSSCHLIESSLICH am Block **H05C_PRIMARY** (latency=300ms,")
[void]$sb.AppendLine("friction=11bps, Taker) - der EINZIGE Punkt mit gate_valid_assumptions=true.")
[void]$sb.AppendLine("H05C_LAT100/LAT500/MAKER sind Robustheits-/Sekundaer-Laeufe (NICHT urteilstragend).")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Schritt | Rolle | Status | rc | Dauer | Detail |")
[void]$sb.AppendLine("|---|---|---|---:|---:|---|")
$roles = @{ 'H05C_PRIMARY'='URTEILSTRAGEND (300ms/11bps/Taker)'; 'H05C_LAT100'='Robustheit (NICHT urteilstragend)'; 'H05C_LAT500'='Robustheit (NICHT urteilstragend)'; 'H05C_MAKER'='Sekundaer (NICHT urteilstragend)' }
foreach ($r in $Script:Results) {
    $role = $roles[$r.Name]; if (-not $role) { $role = '-' }
    [void]$sb.AppendLine("| " + $r.Name + " | " + $role + " | " + $r.Status + " | " + $r.Rc + " | " + $r.Dur + "s | " + $r.Detail + " |")
}
[void]$sb.AppendLine("")
[void]$sb.AppendLine("**Gesamt:** ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
[void]$sb.AppendLine("")
[void]$sb.AppendLine("*Gate-Urteil: gate-auditor gegen H-05c (Roh-JSON h05c\h05c_results.json). Hartes Ein-")
[void]$sb.AppendLine("Fenster-PARK-Kriterium, kein GRAUBEREICH; WEITER nur am H05C_PRIMARY-Punkt. A-priori PARK.*")
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
