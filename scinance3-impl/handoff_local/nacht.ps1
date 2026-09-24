# nacht.ps1 -- EIN Befehl fuer alles, was auf der Nutzer-Maschine zu tun ist.
#
#   powershell -ExecutionPolicy Bypass -File .\scinance3-impl\handoff_local\nacht.ps1
#
# Ablauf: git pull -> alle in -Tasks genannten Laeufe nacheinander (ein
# Fehlschlag bricht die anderen NICHT ab) -> Ergebnisordner nach
# scinance3-impl\state\runs\ kopieren (Dateien > 5 MB bleiben lokal) ->
# commit + push auf den Arbeitsbranch -> Protokoll unter state\runs\nacht_*.log.
# Der Orchestrator liest die Ergebnisse direkt aus dem Repo; kein Upload noetig.
# ASCII-only, PowerShell 5.1, oeffentliche Endpunkte, keine Keys, keine Orders,
# nie ein Schreibzugriff unter data\harvest.
#
# Aufgaben (Standard: die aktuell offenen; der Orchestrator pflegt die Liste):
#   wp13a   Vorlauf v3 (40-60 min)
#   wp10b   Maker-Fill-Schattenmessung, kompletter Neulauf (-NoResume, ~6 h)
#   wp7     Universums-Zensus auf der Union (Minuten)
#   wp10a2  Praemien-Kohaerenz Backfill (Minuten)
#   wp12    Delisting-Register + Fixture (Minuten, Netz)
#   wp13run Echter A3-Lauf; braucht -Registered und -RegisteredSha256
#   diag    Store-Diagnose + Manifest-Status (Sekunden)

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string[]]$Tasks = @("wp13a", "wp10b"),
    [string]$Branch = "claude/subagent-prd-development-T16fE",
    [string]$Registered = "",
    [string]$RegisteredSha256 = "",
    [int]$MaxCommitFileMB = 5,
    [switch]$NoPush,
    [switch]$Wp10bResume
)

$ErrorActionPreference = "Continue"
Set-Location $RepoRoot
$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$runsDir = Join-Path $RepoRoot "scinance3-impl\state\runs"
if (-not (Test-Path $runsDir)) { New-Item -ItemType Directory -Path $runsDir | Out-Null }
$log = Join-Path $runsDir "nacht_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$t0 = Get-Date
$hl = Join-Path $RepoRoot "scinance3-impl\handoff_local"
$results = @()

Write-Host "=== nacht.ps1 $stamp : Tasks = $($Tasks -join ', ') ==="
git pull --rebase --autostash origin $Branch 2>&1 | Write-Host
git log -1 --oneline 2>&1 | Write-Host

function Run-Task($name, $cmd) {
    Write-Host ""
    Write-Host "##### START $name  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') #####"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $cmd
        $rc = $LASTEXITCODE
    } catch {
        Write-Host "AUSNAHME in $name : $_"
        $rc = 99
    }
    $sw.Stop()
    Write-Host "##### ENDE  $name  rc=$rc  Dauer=$([int]$sw.Elapsed.TotalMinutes) min #####"
    $script:results += "$name rc=$rc dauer_min=$([int]$sw.Elapsed.TotalMinutes)"
}

# "powershell -File ... -Tasks a,b" uebergibt EIN Argument "a,b" -> hier splitten
$Tasks = @($Tasks | ForEach-Object { $_ -split "[,; ]+" } | Where-Object { $_ -ne "" })
Write-Host "Aufgaben (aufgeloest): $($Tasks -join ', ')"
foreach ($t in $Tasks) {
    switch ($t) {
        "wp13a"  { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp13_prelaunch.ps1" -AllowPartial } }
        "wp10b"  { if ($Wp10bResume) { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp10b.ps1" } }
                   else { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp10b.ps1" -NoResume } } }
        "wp7"    { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp7_universe.ps1" -SkipFetch -AllowPartial -IncludeDelisted } }
        "wp10a2" { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp10a2.ps1" } }
        "wp12"   { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp12_delisting.ps1" -SkipAnnounce -SkipProbe -AllowPartial -SkipDelistedFetch } }
        "wp13run" {
            if ($Registered -eq "" -or $RegisteredSha256 -eq "") { Write-Host "wp13run uebersprungen: -Registered und -RegisteredSha256 fehlen."; $results += "wp13run uebersprungen" }
            else { Run-Task $t { powershell -ExecutionPolicy Bypass -File "$hl\run_wp13_run.ps1" -Registered $Registered -RegisteredSha256 $RegisteredSha256 } }
        }
        "diag"   { Run-Task $t { python "$hl\wp10b_store_status.py"; python "$hl\harvest_manifest_status.py"; python "$hl\wp7_manifest_partial.py"; python "$hl\wp10b_dup_check.py" BTCUSDT 2026-08-13 2026-08-12; python "$hl\wp10b_dup_check.py" ETHUSDT 2026-08-13 } }
        default  { Write-Host "Unbekannte Aufgabe: $t"; $results += "$t unbekannt" }
    }
}

Write-Host ""
Write-Host "=== Ergebnisse einsammeln (neuer als Start, Dateien <= $MaxCommitFileMB MB) ==="
$stateDir = Join-Path $RepoRoot "scinance3-impl\state"
$limit = $MaxCommitFileMB * 1MB
$copied = @()
Get-ChildItem $stateDir -Directory | Where-Object { $_.Name -match '^(wp\d+[a-z0-9]*|welle\d+)_\d{8}' -and $_.LastWriteTime -ge $t0 } | ForEach-Object {
    $dst = Join-Path $runsDir $_.Name
    if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }
    Get-ChildItem $_.FullName -File -Recurse | ForEach-Object {
        if ($_.Length -le $limit) {
            $rel = $_.FullName.Substring($_.Directory.FullName.Length + 1)
            Copy-Item $_.FullName (Join-Path $dst $_.Name) -Force
            $copied += "$($_.Directory.Name)\$($_.Name)"
        } else {
            Write-Host "  (nicht committet, > $MaxCommitFileMB MB) $($_.FullName)"
        }
    }
    Write-Host "  -> $dst"
}
Write-Host ""
Write-Host "=== Zusammenfassung ==="
$results | ForEach-Object { Write-Host "  $_" }
Stop-Transcript | Out-Null

if (-not $NoPush) {
    git add "scinance3-impl/state/runs" 2>&1 | Write-Host
    $msg = "results(nacht $stamp): " + ($results -join "; ")
    git commit -q -m $msg 2>&1 | Write-Host
    $pushed = $false
    for ($i = 1; $i -le 4 -and -not $pushed; $i++) {
        git pull --rebase --autostash origin $Branch 2>&1 | Write-Host
        git push origin $Branch 2>&1 | Write-Host
        if ($LASTEXITCODE -eq 0) { $pushed = $true } else { Start-Sleep -Seconds (10 * $i) }
    }
    if ($pushed) { Write-Host "Ergebnisse gepusht: $msg" } else { Write-Host "PUSH FEHLGESCHLAGEN - bitte 'git push origin $Branch' manuell." }
}
Write-Host "Fertig. Protokoll: $log"
