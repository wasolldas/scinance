# ========================================================================
# run_h24.ps1 - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 7, H-24)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\run_h24.ps1
#
# H-24 = Fuehrt der Minuten-Nettofluss die FOLGENDE 30-Minuten-Bewegung?
# Taeglicher Rang-IC zwischen F_m = vol_buy - vol_sell und der Forward-
# Bewegung m -> m+30min (Fenster beginnt am NAECHSTEN Minuten-Close,
# Bounce ausgeschlossen). Gate: BEIDE Rezenz-Fenster mean(IC30) >= 0,02
# UND tages-geclusterter Bootstrap-p <= 0,05 nach BH-FDR a=0,10 ueber
# F-IMP; hartes Ein-Fenster-DROP.
#
# BINDENDE POSITIVKONTROLLE (GL-020-Muster): der gleichzeitige IC muss je
# Fenster >= 0,10 erreichen - sonst ist der Lauf METHODISCH INVALIDE
# (kein Verdikt, NICHT DROP).
#
# REZENZ-KLAUSEL (DEC-38): urteilstragend sind NUR die zwei juengsten
# Halbjahre (2025-08..2026-01, 2026-02..2026-07); acht aeltere Halbjahre
# laufen als deskriptives Aera-Profil mit und tragen KEIN Urteil.
#
# LESART (DEC-39, nicht urteilstragend): das VORZEICHEN von IC30 trennt
# reversal (transienter Impact) / permanent (Impact bleibt, Forward-IC ~0)
# / continuation (Fluss fuehrt weitere Bewegung). Das Gate prueft
# ausschliesslich continuation.
#
# Liest AUSSCHLIESSLICH den WP-0-Bar-Cache (data\barcache) - KEIN
# Roh-Tick-Zugriff (DEC-34). Die fuenf registrierten Cache-Fingerabdruecke
# werden VOR der Messung geprueft; Abweichung -> rc=3, gate_valid=false.
#
# KAPITALFREI: reine Messung, keine bps/Edge/PnL/Friction-Rechnung.
#
# Schritte: H24_IMPACT. Exit: 0 = OK * 1 = FAIL * 2 = SKIP (Cache fehlt) *
#           3 = Fingerprint-Mismatch (Lauf nicht urteilstragend).
# Ergebnisse: scinance2-impl\handoff_local\results\h24_<timestamp>\
#             + SUMMARY_<datum>.md (Gate-Urteil: gate-auditor gegen H-24).
#
# Optionale Env-Overrides: BARCACHE_DIR, H24_RESULTS_DIR, H24_TIMEOUT_SEC,
# HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC). PS 5.1-kompatibel, ASCII-only.
# ========================================================================
$ErrorActionPreference = 'Continue'

$ScriptDir = $PSScriptRoot
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$CacheDir  = if ($env:BARCACHE_DIR) { $env:BARCACHE_DIR } else { Join-Path $RepoRoot 'data\barcache' }

$Symbols = 'BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,BNBUSDT'
# CPU; alles im Cache, 10 Fenster x 5 Symbole -> Minuten bis ~1 h.
$TmoStep = if ($env:H24_TIMEOUT_SEC) { [int]$env:H24_TIMEOUT_SEC } else { 7200 }

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
$ResultsBase = if ($env:H24_RESULTS_DIR) { $env:H24_RESULTS_DIR } else { Join-Path $ScriptDir 'results' }
$RunDir = Join-Path $ResultsBase ("h24_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunDir 'h24') | Out-Null
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

Write-Host ("RUN_H24 (T2) - Repo: " + $RepoRoot + " - Ergebnisse: " + $RunDir)
Write-Host ("Bar-Cache: " + $CacheDir + " (WP-0, read-only) | Symbole: " + $Symbols)
Write-Host "Fingerprints VOR der Messung; Positivkontrolle bindend; Rezenz-Klausel aktiv."
if ($DryRun) { Write-Host "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." }

$CacheOk = $true
$barsPath = Join-Path $CacheDir 'bars_1min'
if ((-not $DryRun) -and (-not (Test-Path $barsPath))) {
    $CacheOk = $false
    Write-Host ("WARNUNG: Bar-Cache fehlt (" + $barsPath + ") - erst run_wp0_barcache.ps1 ausfuehren oder BARCACHE_DIR setzen")
}

$CliScript = Join-Path $RepoRoot 'scripts\c24_impact.py'
$rcRun = 2
if (-not $CacheOk) {
    Record-Step -Name 'H24_IMPACT' -Status 'SKIP' -Rc 2 -Dur 0 -Detail ("Bar-Cache fehlt (" + $barsPath + ")")
} else {
    $rcRun = Invoke-Step -Name 'H24_IMPACT' -TimeoutSec $TmoStep -OkRcs @(0) -CmdArgs @(
        $CliScript,
        '--cache-dir', $CacheDir,
        '--symbols', $Symbols,
        '--out-dir', (Join-Path $RunDir 'h24')
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
[void]$sb.AppendLine("# H-24 Minuten-Fluss-Lead Mess-Gate (Welle 7) - T2")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- **Erzeugt:** " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + " UTC")
[void]$sb.AppendLine("- **Run-Dir:** ``" + $RunDir + "``")
[void]$sb.AppendLine("- **Bar-Cache:** ``" + $CacheDir + "`` (WP-0, read-only) | Symbole: " + $Symbols)
[void]$sb.AppendLine("- **Gate:** BEIDE Rezenz-Fenster mean(IC30) >= 0,02 UND p <= 0,05 (BH-FDR a=0,10, F-IMP); hartes Ein-Fenster-DROP. Positivkontrolle (gleichzeitiger IC >= 0,10) BINDEND - sonst methodisch invalide, kein Verdikt.")
[void]$sb.AppendLine("- **Rezenz-Klausel (DEC-38):** urteilstragend NUR 2025-08..2026-01 und 2026-02..2026-07; acht aeltere Halbjahre = deskriptives Aera-Profil.")
[void]$sb.AppendLine("- **KAPITALFREI** - reine Messung.")
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
    [void]$sb.AppendLine("**LAUT-FEHLER: Cache-Fingerabdruecke stimmen nicht mit der Registrierung ueberein.**")
    [void]$sb.AppendLine("``gate_valid=false`` - Befund NICHT tragfaehig. Cache-Stand pruefen (neu gebaut? falscher Pfad?).")
} elseif ($exit -eq 2) {
    [void]$sb.AppendLine("**SKIP** - Bar-Cache nicht gefunden. Erst run_wp0_barcache.ps1 ausfuehren.")
} elseif ($exit -eq 1) {
    [void]$sb.AppendLine("**FEHLER** - ``H24_IMPACT.err.log`` pruefen.")
} else {
    [void]$sb.AppendLine("*Ergebnisse unter ``h24\c24_impact_results.{json,md}``. WEITER verlangt: BEIDE")
    [void]$sb.AppendLine("Rezenz-Fenster mean(IC30) >= 0,02 UND p <= 0,05 nach BH-FDR a=0,10 ueber F-IMP,")
    [void]$sb.AppendLine("bei bestandener Positivkontrolle. Hartes Ein-Fenster-DROP. Ergebnisse hochladen.*")
}
[System.IO.File]::WriteAllText($SummaryPath, $sb.ToString())

Write-Host ""
Write-Host ("SUMMARY: " + $SummaryPath)
Write-Host ("Gesamt: ok=" + $ok + " fail=" + $fail + " skip=" + $skip + " -> exit " + $exit)
exit $exit
