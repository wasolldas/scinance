# run_wp9_dvol.ps1 -- Deribit DVOL REST-Backfill + Quellen-Kreuzvalidierung
# (WP9_SPEZIFIKATION.md). Drei Schritte, immer in dieser Reihenfolge:
#
#   1) Probe   -- Feldlayout ([sek]) und Tiefe (F1) fuer 3 Anker-Tage je
#                 Waehrung. NUR bei rc=0 geht es weiter.
#   2) Fetch   -- Vollhistorie-Backfill -> data\dvol_rest\<CUR>_1D.parquet
#                 + Manifest-JSON mit SHA-256-Fingerprint. NIE data\harvest.
#   3) Crossval -- REST vs. geharvesteter deribit\dvol-Strom (F2) ->
#                 Report-JSON + Markdown nach scinance3-impl\state\wp9_<datum>.
#
# ASCII-only (PowerShell 5.1). rc != 0 bei Probe-Fehler bricht den Lauf ab.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$HarvestBase = "E:\Claude\Projects\scinance\data\harvest",
    [string]$RestDir = "",
    [string]$Currencies = "BTC,ETH",
    [string]$SymbolTemplate = "{cur}_DVOL",
    [string]$OutDir = "",
    [string]$Fixture = ""
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if ($RestDir -eq "") {
    $RestDir = Join-Path $RepoRoot "data\dvol_rest"
}
if ($OutDir -eq "") {
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp9_$(Get-Date -Format yyyyMMdd)"
}

$fixtureArgs = @()
if ($Fixture -ne "") {
    $fixtureArgs = @("--fixture", $Fixture)
}

Write-Host "=== WP-9 Schritt 1: Probe (Feldlayout [sek] + Tiefe F1) ==="
python scripts\wp9_dvol_backfill.py --probe --currencies $Currencies @fixtureArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Probe fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Fetch, KEIN Crossval."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-9 Schritt 2: Fetch (REST-Backfill -> $RestDir) ==="
python scripts\wp9_dvol_backfill.py --fetch --currencies $Currencies --rest-dir $RestDir @fixtureArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Fetch fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Crossval."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-9 Schritt 3: Crossval (F2, gegen den Harvest-Baum) ==="
python scripts\wp9_dvol_backfill.py --crossval --currencies $Currencies `
    --base $HarvestBase --rest-dir $RestDir --symbol-template $SymbolTemplate --out $OutDir
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp9_summary.json und wp9_report.md hochladen (rc=$rc)."
exit $rc
