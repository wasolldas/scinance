# run_wp13_run.ps1 -- WP-13 Lauf-Modus (DEC-75 Entscheidung 1/2, PRD 5.3).
#
# STARTSPERRE (DEC-75 Entscheidung 2, letzter Satz): dieses Script erzwingt
# -Registered UND -RegisteredSha256; scripts\wp13_xsec.py --run prueft den
# sha256 der -Registered-Datei gegen -RegisteredSha256 BEVOR irgendein
# Panel-Byte gelesen wird und bricht mit rc=1 ab, wenn beides nicht
# uebereinstimmt (oder -RegisteredSha256 fehlt). Dieses Script fetcht
# selbst nie (wie run_wp13_prelaunch.ps1); es liest nur, was WP-7/WP-12
# bereits geschrieben haben.
#
# ASCII-only (PowerShell 5.1). Bricht bei fehlender Vorbedingung (rc != 0)
# hart ab, nie mit offenem Prompt.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [Parameter(Mandatory=$true)][string]$Registered,
    [Parameter(Mandatory=$true)][string]$RegisteredSha256,
    [string]$PanelBase = "",
    [string]$DelistedBase = "",
    [string]$DelistedManifest = "",
    [string]$DelistingDates = "",
    [string]$StartYear = "2021",
    [string]$EndYear = "",
    [string]$AsOf = "",
    [string]$OutDir = "",
    [string]$Convention = "close_at_last",
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
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp13_run_$(Get-Date -Format yyyyMMdd)"
}

if (-not (Test-Path $Registered)) {
    Write-Error "Keine registrierte Schwellen-Datei unter $Registered gefunden. Kein Lauf."
    exit 1
}
if ($RegisteredSha256 -eq "") {
    Write-Error "Startsperre: -RegisteredSha256 ist Pflicht. Kein Lauf ohne den registrierten Hash."
    exit 1
}
if (-not (Test-Path (Join-Path $PanelBase "panel_manifest.sqlite"))) {
    Write-Error "Kein panel_1d-Manifest unter $PanelBase -- zuerst run_wp7_universe.ps1 (--fetch) ausfuehren. Kein Lauf."
    exit 1
}
if (-not (Test-Path (Join-Path $DelistedBase "panel_manifest.sqlite"))) {
    Write-Error "Kein panel_1d_delisted-Manifest unter $DelistedBase -- zuerst run_wp12_delisting.ps1 (Schritt 4) ausfuehren. Kein Lauf."
    exit 1
}

$extraArgs = @()
if ($AllowPartial) { $extraArgs = $extraArgs + @("--allow-partial") }
if ($DelistedManifest -ne "") { $extraArgs = $extraArgs + @("--delisted-manifest", $DelistedManifest) }
if ($DelistingDates -ne "") { $extraArgs = $extraArgs + @("--delisting-dates", $DelistingDates) }

Write-Host "=== WP-13 Lauf-Modus (DEC-75 Entscheidung 1/2, Startsperre) -> $OutDir ==="
Write-Host "Registered: $Registered"
Write-Host "RegisteredSha256: $RegisteredSha256"
python scripts\wp13_xsec.py --run `
    --registered $Registered --registered-sha256 $RegisteredSha256 `
    --panel-base $PanelBase --delisted-base $DelistedBase `
    --start-year $StartYear --end-year $EndYear --as-of $AsOf `
    --out $OutDir --convention $Convention @extraArgs
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp13_run.json und die IC-Wochen-CSV-Dateien hochladen (rc=$rc)."
Write-Host "Hinweis: das L-Fenster liegt versiegelt in wp13_run_L_window_sealed.json."
exit $rc
