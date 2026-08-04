# ========================================================================
# run_wave5.ps1 - Welle-5-Overnight-Orchestrator (Scinance 2.0, H-14..H-18)
#
# Faehrt die 5 GPU-Hypothesen SEQUENZIELL in der in der Registry
# ("Welle-5-Sequenzierung + Rechenaufwand-Hinweis") vorregistrierten
# Budget-Reihenfolge (guenstigster zuerst):
#
#   1. H-18  (~1h)        run_h18.ps1  - GL-006 High-N-Aufloesungs-Audit
#   2. H-16  (~145 Trng.) run_h16.ps1  - Time-Arrow-CNN
#   3. H-17  (~1-2 Tage)  run_h17.ps1  - Venue-Fingerprint Contrastive
#   4. H-15  (Stunden)    run_h15.ps1  - DSM-01 Grammar
#   5. H-14  (~2-3 Tage)  run_h14.ps1  - PANEL-LAG Node-Ablation (RESUME-faehig)
#
# KEINE Kohorte: jede Hypothese laeuft einzeln nacheinander (VRAM/Zeit-
# Konkurrenz um dieselbe Karte); jede hat ihre eigene FDR-Familie. Dieser
# Orchestrator aendert NICHTS an den Einzel-Runnern - er ruft sie nur der
# Reihe nach auf, protokolliert Exit-Codes/Dauern und schreibt am Ende
# eine Gesamt-Summary. Ein FAIL/SKIP einer Hypothese bricht die Nacht
# NICHT ab - die naechste startet trotzdem (jeder Einzel-Runner macht
# seinen eigenen GPU-Check in Sekunden).
#
# WICHTIG - MEHRNAECHTE-BETRIEB IST VORGESEHEN: H-17 und H-14 sind in
# einer Nacht NICHT fertig. H-14 ist checkpoint-/resume-faehig (Default
# 10h Budget PRO AUFRUF via H14_TIMEOUT_SEC): einfach dieses Skript in
# der naechsten Nacht ERNEUT starten - bereits abgeschlossene Ergebnis-
# JSONs (h1X-Results) bzw. H-14-Checkpoints werden erkannt bzw.
# weiterverwendet. Mit -SkipCompleted (Default AN) wird eine Hypothese
# uebersprungen, deren Ergebnis-JSON bereits existiert.
#
# Aufruf (Beispiele):
#   powershell -ExecutionPolicy Bypass -File .\run_wave5.ps1
#   powershell -ExecutionPolicy Bypass -File .\run_wave5.ps1 -MaxHours 9
#   powershell -ExecutionPolicy Bypass -File .\run_wave5.ps1 -Only h18,h16
#   powershell -ExecutionPolicy Bypass -File .\run_wave5.ps1 -NoSkipCompleted
#
# Parameter:
#   -MaxHours <double>   Zeitbudget: nach Ablauf wird KEINE NEUE Hypothese
#                        mehr gestartet (die laufende wird nie gekillt -
#                        jeder Einzel-Runner hat eigene Timeouts).
#                        0 = unbegrenzt (Default).
#   -Only <liste>        Nur diese Hypothesen, z.B. -Only h18,h16
#                        (Reihenfolge bleibt die registrierte).
#   -NoSkipCompleted     Auch Hypothesen mit bereits vorhandenem
#                        Ergebnis-JSON erneut starten.
#
# Exit-Code: 0 = alle gestarteten Hypothesen OK *
#            1 = mindestens ein FAIL *
#            2 = kein FAIL, aber mindestens ein SKIP (z.B. kein CUDA).
# Ergebnisse: results\wave5_<timestamp>\WAVE5_SUMMARY_<datum>.md
#             + die Einzel-Ergebnisse der Kind-Runner (eigene results\-Dirs).
# PS 5.1-kompatibel, ASCII-only, BelowNormal-Prioritaet wie die Kind-Runner.
# ========================================================================
param(
    [double]$MaxHours = 0,
    [string[]]$Only = @(),
    [switch]$NoSkipCompleted
)
$ErrorActionPreference = 'Continue'

# ------------------------------------------------------------------------
# CONCURRENCY-SCHUTZ: Am 2026-07-18 liefen drei run_wave5-Instanzen
# gleichzeitig (12:51 Voll-Lauf + 13:11 -Only h16 + 13:14 -Only h15,h14)
# und haben sich gegenseitig RAM/GPU weggenommen — zwei OOMs und ein
# 8h-Timeout waren die direkte Folge. Ein benannter System-Mutex laesst
# nur EINE Instanz zu; eine zweite bricht sofort laut ab. Der Mutex wird
# vom OS freigegeben, wenn der Prozess endet (auch bei Fenster-Schliessen
# oder Absturz) — kein stale-Lock-Risiko wie bei Lock-Dateien.
# ------------------------------------------------------------------------
$WaveMutex = New-Object System.Threading.Mutex($false, 'Local\scinance_run_wave5')
if (-not $WaveMutex.WaitOne(0)) {
    Write-Host ("FEHLER: Eine andere run_wave5.ps1-Instanz laeuft bereits auf dieser " +
                "Maschine. Parallele Instanzen konkurrieren um GPU/RAM und haben am " +
                "2026-07-18 OOMs verursacht. Erst die laufende Instanz beenden " +
                "(oder auslaufen lassen), dann neu starten.") -ForegroundColor Red
    exit 1
}

$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

# Junction-Guard: data\harvest ist nach Reboots/Harvest-Kompaktierungen
# schon zweimal verschwunden (2026-07-17, 2026-08-03) und hat Sessions zu
# SKIP gezwungen. Der Guard repariert eine tote/fehlende Junction
# selbstheilend (loescht NIE echte Verzeichnisse - Sicherheits-Stopp im
# Skript). Ein Guard-FEHLER bricht hier nicht ab: die Kind-Runner skippen
# dann selbst laut mit klarer Meldung.
$JunctionGuard = Join-Path $ScriptDir 'ensure_harvest_junction.ps1'
if (Test-Path $JunctionGuard) {
    & powershell -ExecutionPolicy Bypass -File $JunctionGuard | Out-Host
}

$Ts = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
$SummaryDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$RunDir = Join-Path (Join-Path $ScriptDir 'results') ("wave5_" + $Ts)
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$MasterLog = Join-Path $RunDir 'wave5_orchestrator.log'

function Log-Line {
    param([string]$Msg)
    $line = ((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss') + 'Z  ' + $Msg)
    Write-Host $line
    Add-Content -Path $MasterLog -Value $line
}

# Registrierte Reihenfolge (Registry "Welle-5-Sequenzierung"): NICHT umsortieren.
# done_glob (Wildcard, relativ zu handoff_local): matcht das finale
# Ergebnis-JSON im zeitgestempelten Run-Dir des Kind-Runners einer
# FRUEHEREN Nacht - dann gilt die Hypothese als abgeschlossen und wird
# ohne -NoSkipCompleted uebersprungen. (Die Kind-Runner schreiben ihr
# Ergebnis-JSON erst bei vollstaendigem Lauf - ein Teil-Lauf/TIMEOUT
# erzeugt es NICHT, s. run_h14.ps1-Header.)
$Plan = @(
    @{ id='h18'; name='H-18 GL-006 High-N-Aufloesungs-Audit'; script='run_h18.ps1';
       done_glob='results\h18_*\h18\c18_leadlag_audit_results.json' },
    @{ id='h16'; name='H-16 Time-Arrow-CNN';                  script='run_h16.ps1';
       done_glob='results\h16_*\h16\c16_arrow_results.json' },
    @{ id='h17'; name='H-17 Venue-Fingerprint Contrastive';   script='run_h17.ps1';
       done_glob='results\h17_*\h17\c17_venue_results.json' },
    @{ id='h15'; name='H-15 DSM-01 Grammar';                  script='run_h15.ps1';
       done_glob='results\h15_*\h15\c15_grammar_results.json' },
    @{ id='h14'; name='H-14 PANEL-LAG Node-Ablation (resume)'; script='run_h14.ps1';
       done_glob='results\h14_*\h14\c14_panellag_results.json' }
)

# Robust gegen BEIDE Aufrufarten: nativer Aufruf (.\run_wave5.ps1 -Only h15,h14
# -> echtes Array) UND powershell -File (-Only h15,h14 kommt als EIN String
# "h15,h14" an - -File parst keine PowerShell-Array-Syntax). Deshalb jedes
# Element zusaetzlich an Komma/Leerzeichen splitten + lowercase-normalisieren.
$OnlyIds = @()
foreach ($o in $Only) {
    foreach ($tok in ($o -split '[,\s]+')) {
        if ($tok) { $OnlyIds += $tok.ToLower() }
    }
}
if ($OnlyIds.Count -gt 0) {
    $sel = @()
    foreach ($p in $Plan) { if ($OnlyIds -contains $p.id) { $sel += ,$p } }
    $Plan = $sel
    if ($Plan.Count -eq 0) {
        Log-Line ("FEHLER: -Only '" + ($OnlyIds -join ',') + "' matcht keine Hypothese (gueltig: h14,h15,h16,h17,h18) - Abbruch.")
        exit 1
    }
}

$StartTime = Get-Date
$Rows = @()
$AnyFail = $false
$AnySkip = $false

Log-Line ("WAVE5 START | plan=" + (($Plan | ForEach-Object { $_.id }) -join ',') +
          " | MaxHours=" + $MaxHours + " | SkipCompleted=" + (-not $NoSkipCompleted))

foreach ($p in $Plan) {
    $elapsedH = ((Get-Date) - $StartTime).TotalHours
    if (($MaxHours -gt 0) -and ($elapsedH -ge $MaxHours)) {
        Log-Line ("BUDGET erschoepft (" + [math]::Round($elapsedH,2) + "h >= " + $MaxHours + "h) -> " + $p.id + " NICHT gestartet")
        $Rows += ,@($p.id, 'NOT_STARTED', '-', '0', 'Zeitbudget erschoepft - naechste Nacht erneut starten')
        $AnySkip = $true
        continue
    }

    $doneGlob = Join-Path $ScriptDir $p.done_glob
    if ((-not $NoSkipCompleted) -and (Test-Path $doneGlob)) {
        $doneFile = (Resolve-Path $doneGlob | Select-Object -First 1).Path
        Log-Line ($p.id + " SKIP_COMPLETED (Ergebnis existiert bereits: " + $doneFile + ")")
        $Rows += ,@($p.id, 'DONE_EARLIER', '0', '0', ('Ergebnis-JSON vorhanden: ' + $doneFile))
        continue
    }

    $scriptPath = Join-Path $ScriptDir $p.script
    if (-not (Test-Path $scriptPath)) {
        Log-Line ($p.id + " FAIL (Runner fehlt: " + $scriptPath + ")")
        $Rows += ,@($p.id, 'FAIL', '-', '0', 'Runner-Skript nicht gefunden')
        $AnyFail = $true
        continue
    }

    Log-Line ("START " + $p.id + " (" + $p.name + ") -> " + $p.script)
    $t0 = Get-Date
    & powershell -ExecutionPolicy Bypass -File $scriptPath 2>&1 |
        Tee-Object -FilePath (Join-Path $RunDir ($p.id + '_child.log'))
    $rc = $LASTEXITCODE
    $durMin = [int](((Get-Date) - $t0).TotalMinutes)

    $status = 'OK'
    if ($rc -eq 1) { $status = 'FAIL'; $AnyFail = $true }
    elseif ($rc -eq 2) { $status = 'SKIP'; $AnySkip = $true }
    elseif ($rc -ne 0) { $status = ('RC_' + $rc); $AnyFail = $true }

    Log-Line ("ENDE  " + $p.id + " | rc=" + $rc + " status=" + $status + " dauer=" + $durMin + "min")
    $Rows += ,@($p.id, $status, [string]$rc, [string]$durMin, $p.name)
}

# ---------------------------- Summary -----------------------------------
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# WAVE5 Overnight-Summary $SummaryDate ($Ts UTC)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("Registrierte Reihenfolge: H-18 -> H-16 -> H-17 -> H-15 -> H-14 (Registry 'Welle-5-Sequenzierung').")
[void]$sb.AppendLine("Exit-Codes der Kind-Runner: 0=OK, 1=FAIL, 2=SKIP (kein CUDA).")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Hypothese | Status | rc | Dauer (min) | Detail |")
[void]$sb.AppendLine("|---|---|---:|---:|---|")
foreach ($r in $Rows) {
    [void]$sb.AppendLine("| " + $r[0] + " | " + $r[1] + " | " + $r[2] + " | " + $r[3] + " | " + $r[4] + " |")
}
[void]$sb.AppendLine("")
[void]$sb.AppendLine("Gesamtdauer: " + [math]::Round(((Get-Date) - $StartTime).TotalHours, 2) + "h.")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("Naechste Schritte: FAIL -> <id>_child.log in diesem Verzeichnis pruefen. ")
[void]$sb.AppendLine("NOT_STARTED/TIMEOUT (insb. H-14/H-17) -> dieses Skript in der naechsten ")
[void]$sb.AppendLine("Nacht einfach erneut starten (H-14 setzt via results\h14_checkpoints fort; ")
[void]$sb.AppendLine("fertige Hypothesen werden automatisch uebersprungen).")
$SummaryPath = Join-Path $RunDir ("WAVE5_SUMMARY_" + $SummaryDate + ".md")
$sb.ToString() | Set-Content -Path $SummaryPath -Encoding UTF8

Log-Line ("WAVE5 ENDE | Summary: " + $SummaryPath)

$exit = 0
if ($AnyFail) { $exit = 1 } elseif ($AnySkip) { $exit = 2 }
$WaveMutex.ReleaseMutex()
$WaveMutex.Dispose()
exit $exit
