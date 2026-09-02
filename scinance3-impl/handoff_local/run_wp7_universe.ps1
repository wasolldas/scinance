# run_wp7_universe.ps1 -- Universums-Zensus (Klasse-W-Feasibility),
# WP7_SPEZIFIKATION.md. Vier Schritte, immer in dieser Reihenfolge:
#
#   1) Probe   -- Inhaltsprobe auf den vorhandenen bybit/tickers-Strom
#                 (bid1Price/ask1Price/openInterest/fundingRate). NUR bei
#                 rc=0 (oder gewuerdigtem rc!=0) geht es weiter.
#   2) Fetch   -- instruments-info + Tages-Klines -> panel_1d (NIE unter
#                 data\harvest). Braucht echtes Netz (5 Req/s Drossel,
#                 ~10 min, ~1000 Symbole).
#   3) Zensus  -- K, SD_null(IC_t), N_eff, sigma_xs, sigma_LS,
#                 PERP_SPREAD_BP, rho(BTC,ETH) -> Befund B1..B5,
#                 Report-JSON + Markdown nach scinance3-impl\state\wp7_<datum>.
#   4) Reverify -- 1%-Zufallsstichprobe eingefrorener Partitionen neu
#                 gezogen, Fingerprints geprueft (monatlich, Provenienz).
#
# ASCII-only (PowerShell 5.1). rc != 0 bei Probe-Fehler bricht NICHT hart
# ab (die Probe kann legitim rc=1 liefern, wenn der REST-Fallback noetig
# ist) -- der Fetch-Schritt laeuft trotzdem, nur mit einer Warnung.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$HarvestBase = "E:\Claude\Projects\scinance\data\harvest",
    [string]$PanelBase = "",
    [string]$BarCacheDir = "",
    [string]$Dates = "2026-08-19..2026-08-20",
    [string]$StartYear = "2021",
    [string]$EndYear = "",
    [string]$CorrStart = "",
    [string]$CorrEnd = "",
    [string]$OutDir = "",
    [switch]$SkipFetch
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if ($PanelBase -eq "") {
    $PanelBase = Join-Path $RepoRoot "data\panel_1d"
}
if ($BarCacheDir -eq "") {
    $BarCacheDir = Join-Path $RepoRoot "data\barcache"
}
if ($EndYear -eq "") {
    $EndYear = (Get-Date).Year
}
if ($OutDir -eq "") {
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp7_$(Get-Date -Format yyyyMMdd)"
}

Write-Host "=== WP-7 Schritt 1: Probe (bybit/tickers Inhaltsprobe) ==="
python scripts\wp7_universe_census.py --probe-tickers --harvest-base $HarvestBase --dates $Dates
$probeRc = $LASTEXITCODE
if ($probeRc -ne 0) {
    Write-Host "WARNUNG: Inhaltsprobe rc=$probeRc -- Spread-Zensus faellt auf den REST-Tickers-Call zurueck (spread_probe.perp_snapshot_from_rest)."
}

if (-not $SkipFetch) {
    Write-Host ""
    Write-Host "=== WP-7 Schritt 2: Fetch (instruments-info + Klines -> $PanelBase) ==="
    python scripts\wp7_universe_census.py --fetch --panel-base $PanelBase --start-year $StartYear --end-year $EndYear
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Fetch fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Zensus."
        exit $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "=== WP-7 Schritt 3: Zensus -> $OutDir ==="
python scripts\wp7_universe_census.py --census --panel-base $PanelBase --out $OutDir `
    --bar-cache-dir $BarCacheDir --corr-start $CorrStart --corr-end $CorrEnd
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "=== WP-7 Schritt 4: Reverify (1% Provenienz-Stichprobe) ==="
python scripts\wp7_universe_census.py --reverify --panel-base $PanelBase
$reverifyRc = $LASTEXITCODE
if ($reverifyRc -ne 0) {
    Write-Error "Reverify-ALARM (rc=$reverifyRc) -- Fingerprint-Abweichung, siehe Ausgabe oben."
}

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp7_report.json und wp7_report.md hochladen (Zensus-rc=$rc, Reverify-rc=$reverifyRc)."
exit $rc
