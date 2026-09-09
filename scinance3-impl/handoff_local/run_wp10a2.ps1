# run_wp10a2.ps1 -- WP-10 Teil A2: Praemien-Kohaerenz im Stress auf
# nachgeladenen Tagesserien (DEC-62, WP-10(A) auf Bestandsserien war NICHT
# messbar -- Stress-Ueberlappung 0-3 Tage). Backfill-Modus: Funding aus
# panel_1d.funding_sum (WP-7) oder ersatzweise direktem oeffentlichem
# REST-Abruf, IV aus dem REST-DVOL-Backfill (WP-9/DEC-61) minus WP-0-Bar-
# Cache-RV; Basis-Proxy bleibt Harvest-only (unveraendert). Mirror von
# run_wp10a.ps1 mit --source backfill. Drei Schritte, immer in dieser
# Reihenfolge:
#
#   1) Probe        -- dvol_rest-Parquet-Praesenz (Pflicht, DEC-61) und
#                       WP-0-Bar-Cache-Abdeckung; panel_1d-Praesenz wird
#                       NUR gemeldet (informativ) -- fehlt panel_1d, laeuft
#                       der Funding-Teil trotzdem ueber den direkten
#                       oeffentlichen REST-Abruf weiter, KEIN Abbruch.
#                       NUR bei rc=0 (dvol_rest + Bar-Cache vorhanden)
#                       geht es weiter.
#   2) Stress-Kanon -- STRESS_REL (DEC-55) + STRESS_ABS (DEC-56) Fixturen
#                       aus dem WP-0-Bar-Cache schreiben (append-only,
#                       quellen-unabhaengig -- identisch zu run_wp10a.ps1).
#   3) Run          -- --source backfill: Serien laden (Bestand als
#                       Vergleichszeile, DEC-60-Lehre), Kohaerenz-Matrix +
#                       Portfolio-Nulleffekt rechnen, JSON+Markdown+
#                       DEC-53-Artefakte + Bestand-vs-Backfill-Vergleich
#                       schreiben.
#
# ASCII-only (PowerShell 5.1). rc != 0 bei Probe-Fehler bricht den Lauf ab.
# WP-10(A2) ist rein deskriptiv -- dieses Skript faellt kein PASS/FAIL-
# Urteil.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$HarvestBase = "E:\Claude\Projects\scinance\data\harvest",
    [string]$CacheDir = "",
    [string]$PanelBase = "E:\Claude\Projects\scinance\data\panel_1d",
    [string]$DvolRestDir = "E:\Claude\Projects\scinance\data\dvol_rest",
    [string]$FundingSymbols = "BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT",
    [string]$IvrvCurrencies = "BTC,ETH",
    [string]$DvolSymbolTemplate = "",
    [string]$BasisSymbols = "BTCUSDT,ETHUSDT",
    [string]$Start = "",
    [string]$End = "",
    [string]$StressCanonOut = "",
    [string]$OutDir = "",
    [int]$Seed = 53
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if ($CacheDir -eq "") {
    $CacheDir = Join-Path $RepoRoot "data\barcache"
}
if ($StressCanonOut -eq "") {
    $StressCanonOut = Join-Path $RepoRoot "scinance3-impl\state\wp10_stress_canon"
}
if ($OutDir -eq "") {
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp10a2_$(Get-Date -Format yyyyMMdd)"
}

$rangeArgs = @()
if ($Start -ne "") { $rangeArgs += @("--start", $Start) }
if ($End -ne "") { $rangeArgs += @("--end", $End) }

$dvolSymbolTemplateArgs = @()
if ($DvolSymbolTemplate -ne "") {
    $dvolSymbolTemplateArgs = @("--dvol-symbol-template", $DvolSymbolTemplate)
}

Write-Host "=== WP-10(A2) Vorprobe: dvol_rest-Parquet + panel_1d Praesenz (lokal, vor dem Python-Probe) ==="
foreach ($cur in $IvrvCurrencies.Split(",")) {
    $curPath = Join-Path $DvolRestDir "${cur}_1D.parquet"
    if (Test-Path $curPath) {
        Write-Host "  $cur : dvol_rest vorhanden -> $curPath"
    } else {
        Write-Host "  $cur : dvol_rest FEHLT -> $curPath (erst scripts\wp9_dvol_backfill.py --fetch ausfuehren, Pflicht, DEC-61)"
    }
}
if (Test-Path $PanelBase) {
    Write-Host "  panel_1d vorhanden -> $PanelBase (Funding bevorzugt aus panel_1d.funding_sum, WP-7)"
} else {
    Write-Host "  panel_1d FEHLT -> $PanelBase (Funding laeuft ueber den direkten oeffentlichen REST-Abruf weiter -- KEIN Abbruch)"
}

Write-Host ""
Write-Host "=== WP-10(A2) Schritt 1: Probe (--source backfill: dvol_rest/Bar-Cache Pflicht, panel_1d informativ) ==="
python scripts\wp10_coherence.py --probe --source backfill --base $HarvestBase --cache-dir $CacheDir `
    --panel-base $PanelBase --dvol-rest-dir $DvolRestDir `
    --funding-symbols $FundingSymbols --ivrv-currencies $IvrvCurrencies --basis-symbols $BasisSymbols `
    @dvolSymbolTemplateArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Probe fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen (dvol_rest/Bar-Cache); KEIN Stress-Kanon, KEIN Run."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-10(A2) Schritt 2: Stress-Kanon (STRESS_REL/DEC-55, STRESS_ABS/DEC-56) ==="
python scripts\wp10_coherence.py --stress-canon --cache-dir $CacheDir `
    --stress-canon-out $StressCanonOut @rangeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Stress-Kanon fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Run."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-10(A2) Schritt 3: Run (Backfill-Kohaerenz + Bestand-vs-Backfill-Vergleich) ==="
python scripts\wp10_coherence.py --run --source backfill --base $HarvestBase --cache-dir $CacheDir `
    --panel-base $PanelBase --dvol-rest-dir $DvolRestDir `
    --funding-symbols $FundingSymbols --ivrv-currencies $IvrvCurrencies --basis-symbols $BasisSymbols `
    --stress-canon-out $StressCanonOut --out $OutDir --seed $Seed @rangeArgs @dvolSymbolTemplateArgs
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp10a_summary.json und wp10a_report.md hochladen (rc=$rc)."
Write-Host "WP-10(A2) ist deskriptiv -- kein PASS/FAIL-Urteil in diesem Lauf."
Write-Host "Der Report enthaelt eine Bestand-vs-Backfill-Vergleichszeile je Serie (DEC-60-Lehre)."
exit $rc
