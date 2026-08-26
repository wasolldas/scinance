# run_wp6_stresszensus.ps1 -- Options-Quote-Breite ueber das Stress-Fenster
# um den 2026-08-19, gelesen aus dem Harvest-Baum (read-only).
#
# SCHRITT 1 ist immer die Probe. Sie prueft, ob unter raw/bybit/tickers
# tatsaechlich Options-Symbole liegen und ob die Frames bid/ask fuehren.
# Der Zensus laeuft nur, wenn die Probe rc=0 liefert.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$HarvestBase = "E:\Claude\Projects\scinance\data\harvest",
    [string]$Dates = "2026-08-15..2026-08-23",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot
if ($OutDir -eq "") {
    $OutDir = Join-Path $RepoRoot "scinance2-impl\state\wp6_$(Get-Date -Format yyyyMMdd)"
}

Write-Host "=== WP-6 Schritt 1: Probe (Stress-Tag) ==="
python scripts\wp6_optstress_census.py --base $HarvestBase --dates 2026-08-19 --probe
if ($LASTEXITCODE -ne 0) {
    Write-Error "Probe fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben an Claude geben; KEIN Zensus."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-6 Schritt 2: Zensus $Dates ==="
python scripts\wp6_optstress_census.py --base $HarvestBase --dates $Dates --out $OutDir
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp6_summary.json und wp6_minute_spread.csv hochladen (rc=$rc)."
exit $rc
