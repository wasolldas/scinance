# run_wp13_prelaunch.ps1 -- WP-13a Vorlauf (DEC-74 Entscheidung 3, PRD 5.3).
#
# EIN Schritt: der Vorlauf-Report ueber scripts\wp13_xsec.py --prelaunch,
# auf dem BEREITS GEFETCHTEN Union-Panel (data\panel_1d + data\
# panel_1d_delisted -- kein Netz hier; -SkipFetch-Stil wie
# run_wp7_universe.ps1: dieses Script fetcht selbst nie, es liest nur,
# was WP-7 --fetch / WP-12 --fetch-delisted-panel bereits geschrieben
# haben). Berechnet KEINE reale Signal-Outcome-IC (Siegel-Test) -- nur
# Rauschboden/Schwellen (a), Persistenz-Null (b)/(c), Gate-(5)-
# Erreichbarkeit (g), H-30-Feasibility auf L (h), Delisting-Zaehlung +
# NO_HISTORY-Symbole (i), STRESS_REL/STRESS_ABS-Abdeckung, Selektions-
# Decke K=7.
#
# ASCII-only (PowerShell 5.1). Bricht bei fehlender Vorbedingung (rc != 0)
# hart ab, nie mit offenem Prompt.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$PanelBase = "",
    [string]$DelistedBase = "",
    [string]$DelistedManifest = "",
    [string]$DelistingDates = "",
    [string]$StartYear = "2021",
    [string]$EndYear = "",
    [string]$AsOf = "",
    [string]$OutDir = "",
    [string]$Seed = "53",
    [string]$NSims = "1000",
    [string]$Convention = "close_at_last",
    [string]$StressRel = "",
    [string]$StressAbs = "",
    [switch]$AllowPartial
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if ($PanelBase -eq "") {
    $PanelBase = Join-Path $RepoRoot "data\panel_1d"
}
if ($DelistedBase -eq "") {
    $DelistedBase = Join-Path $RepoRoot "data\panel_1d_delisted"
}
if ($EndYear -eq "") {
    $EndYear = (Get-Date).Year
}
if ($AsOf -eq "") {
    $AsOf = (Get-Date).ToString("yyyy-MM-dd")
}
if ($OutDir -eq "") {
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp13a_$(Get-Date -Format yyyyMMdd)"
}
if ($StressRel -eq "") {
    $StressRel = Join-Path $RepoRoot "scinance3-impl\state\wp10_stress_canon\stress_rel.json"
}
if ($StressAbs -eq "") {
    $StressAbs = Join-Path $RepoRoot "scinance3-impl\state\wp10_stress_canon\stress_abs.json"
}

if (-not (Test-Path (Join-Path $PanelBase "panel_manifest.sqlite"))) {
    Write-Error "Kein panel_1d-Manifest unter $PanelBase -- zuerst run_wp7_universe.ps1 (--fetch) ausfuehren. Kein Vorlauf."
    exit 1
}
if (-not (Test-Path (Join-Path $DelistedBase "panel_manifest.sqlite"))) {
    Write-Error "Kein panel_1d_delisted-Manifest unter $DelistedBase -- zuerst run_wp12_delisting.ps1 (Schritt 4) ausfuehren. Kein Vorlauf."
    exit 1
}

$extraArgs = @()
if ($AllowPartial) { $extraArgs = $extraArgs + @("--allow-partial") }
if ($DelistedManifest -ne "") { $extraArgs = $extraArgs + @("--delisted-manifest", $DelistedManifest) }
if ($DelistingDates -ne "") { $extraArgs = $extraArgs + @("--delisting-dates", $DelistingDates) }

Write-Host "=== WP-13a Vorlauf (DEC-74 Entscheidung 3) -> $OutDir ==="
python scripts\wp13_xsec.py --prelaunch `
    --panel-base $PanelBase --delisted-base $DelistedBase `
    --start-year $StartYear --end-year $EndYear --as-of $AsOf `
    --out $OutDir --seed $Seed --n-sims $NSims --convention $Convention `
    --stress-rel $StressRel --stress-abs $StressAbs @extraArgs
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp13a_prelaunch.md und wp13a_prelaunch.json hochladen (rc=$rc)."
Write-Host "Hinweis: KEIN VERDIKT -- der Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung (Siegel-Test, DEC-74 Entscheidung 3)."
exit $rc
