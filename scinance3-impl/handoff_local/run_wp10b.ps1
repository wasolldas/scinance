# run_wp10b.ps1 -- WP-10 Teil B: Maker-Fill-Schattenmessung (kapitalfrei)
# (WP10_SPEZIFIKATION.md, Teil B). Drei Schritte, immer in dieser Reihenfolge:
#
#   1) Positivkontrolle -- synthetische Quote mit bekannter Warteschlangen-
#                           Position muss einen bekannten Fill liefern
#                           (PRD 3.3.8). NUR bei rc=0 geht es weiter.
#   2) Probe             -- welche Tage orderbook.1000/publicTrade vorliegen
#                           und manifest-DONE sind.
#   3) Run                -- L2+Trade-Replay, fillshadow_1min-Store,
#                           Fill-Rate-Kurven + adv_sel-Bericht (DEC-53-
#                           Artefakte).
#
# ASCII-only (PowerShell 5.1). rc != 0 bei Positivkontrolle oder Run bricht
# ab. Teil B ist kapitalfrei und faellt kein PASS/FAIL -- adv_sel <= 1,75 bp
# ist ein ETIKETT ("Maker-Vorteil traegt"/"traegt nicht"), keine Schwelle.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$HarvestBase = "E:\Claude\Projects\scinance\data\harvest",
    [string]$StoreOut = "",
    [string]$Symbols = "BTCUSDT,ETHUSDT",
    [string]$Start = "2026-06-22",
    [string]$End = "",
    [string]$StressCanonDir = "",
    [string]$ReportDir = "",
    [double]$HorizonS = 60.0,
    [double]$AdvSelHorizonS = 60.0,
    [double]$QuoteSizeFraction = 0.1,
    [int]$Seed = 53,
    [int]$NBootstrap = 1000
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if ($StoreOut -eq "") {
    $StoreOut = Join-Path $RepoRoot "data\l2tilt"
}
if ($End -eq "") {
    $End = Get-Date -Format yyyy-MM-dd
}
if ($StressCanonDir -eq "") {
    $StressCanonDir = Join-Path $RepoRoot "scinance3-impl\state\wp10_stress_canon"
}
if ($ReportDir -eq "") {
    $ReportDir = Join-Path $RepoRoot "scinance3-impl\state\wp10b_$(Get-Date -Format yyyyMMdd)"
}

Write-Host "=== WP-10(B) Schritt 1: Positivkontrolle (PRD 3.3.8) ==="
python scripts\wp10_fillshadow.py --positive-control
if ($LASTEXITCODE -ne 0) {
    Write-Error "Positivkontrolle FEHLGESCHLAGEN (rc=$LASTEXITCODE). Fuellmaschinerie defekt -- Lauf abgebrochen, KEIN Probe, KEIN Run."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-10(B) Schritt 2: Probe ($Symbols, $Start..$End) ==="
python scripts\wp10_fillshadow.py --probe --base $HarvestBase --symbols $Symbols --start $Start --end $End
$probeRc = $LASTEXITCODE
if ($probeRc -ne 0) {
    Write-Host "WARNUNG: Probe rc=$probeRc -- fehlende Rohdaten fuer mind. ein Symbol. Run laeuft trotzdem (einzelne Tage werden im Store als no_raw markiert, nie still uebersprungen)."
}

Write-Host ""
Write-Host "=== WP-10(B) Schritt 3: Run -> $ReportDir ==="
python scripts\wp10_fillshadow.py --run --base $HarvestBase --out $StoreOut --symbols $Symbols `
    --dates "$Start..$End" --stress-canon $StressCanonDir --report-dir $ReportDir `
    --horizon-s $HorizonS --adv-sel-horizon-s $AdvSelHorizonS `
    --quote-size-fraction $QuoteSizeFraction --seed $Seed --n-bootstrap $NBootstrap
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $ReportDir"
Write-Host "Bitte wp10b_summary.json und wp10b_report.md hochladen (rc=$rc)."
Write-Host "Teil B ist kapitalfrei -- kein PASS/FAIL; adv_sel <= 1,75 bp ist ein Etikett, keine Schwelle."
exit $rc
