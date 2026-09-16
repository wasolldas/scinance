# run_wp12_delisting.ps1 -- Delisting-Register + Survivorship-Fixture
# (PRD 4.1 B3, DEC-67 Entscheidung 5, DEC-70). Vier Schritte, immer in
# dieser Reihenfolge:
#
#   1) Announce -- PUBLIC Bybit-Announcements (keyfrei) -> Rohantworten +
#                  register.parquet + Manifest unter data\delisting_register
#                  (NIE unter data\harvest). Braucht echtes Netz.
#   2) Probe    -- fuer jedes delistete lineare Symbol im Register: liefert
#                  Bybit noch Tages-Kline-Historie in den 90 Tagen vor
#                  Delisting? (5 Req/s Drossel, wenige Minuten.)
#   3) Report   -- --mode fixture: WP-7-panel_1d (Ueberlebende) + reale
#                  oder (falls keine Historie verfuegbar) SYNTHETISCHE
#                  delistete Rueckgabepfade -> Momentum-IC-Verzerrung +
#                  Cluster-Bootstrap-CI -> scinance3-impl\state\wp12_<datum>.
#                  KEIN PASS/FAIL -- die registrierte Schwelle ist noch
#                  nicht gesetzt (A3 nicht registriert, DEC-67 E1).
#   4) Delisted-Panel fetchen (WP-12b, DEC-70) -- volle Tages-Historie
#                  (+Funding) je delistetem linearem Symbol, ab -StartYear
#                  bis zu seinem Delisting-Datum -> data\panel_1d_delisted
#                  (NIE data\panel_1d, NIE data\harvest). Braucht echtes
#                  Netz (5 Req/s Drossel). Speist
#                  run_wp7_universe.ps1 -IncludeDelisted.
#
# ASCII-only (PowerShell 5.1). Bricht bei einer fehlgeschlagenen
# Vorbedingung (rc != 0) hart ab, nie mit offenem Prompt.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$RegisterBase = "",
    [string]$PanelBase = "",
    [string]$Manifest = "",
    [string]$DelistedPanelBase = "",
    [string]$StartYear = "2021",
    [string]$EndYear = "",
    [string]$AsOf = "",
    [string]$OutDir = "",
    [string]$WindowDays = "90",
    [string]$Seed = "53",
    [string]$NBoot = "1000",
    [switch]$SkipAnnounce,
    [switch]$SkipProbe,
    [switch]$SkipDelistedFetch,
    [switch]$AllowPartial,
    [switch]$ProbeOnly
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if ($RegisterBase -eq "") {
    $RegisterBase = Join-Path $RepoRoot "data\delisting_register"
}
if ($PanelBase -eq "") {
    $PanelBase = Join-Path $RepoRoot "data\panel_1d"
}
if ($Manifest -eq "") {
    $Manifest = Join-Path $PanelBase "panel_manifest.sqlite"
}
if ($DelistedPanelBase -eq "") {
    $DelistedPanelBase = Join-Path $RepoRoot "data\panel_1d_delisted"
}
if ($EndYear -eq "") {
    $EndYear = (Get-Date).Year
}
if ($AsOf -eq "") {
    $AsOf = (Get-Date).ToString("yyyy-MM-dd")
}
if ($OutDir -eq "") {
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp12_$(Get-Date -Format yyyyMMdd)"
}

if (-not $SkipAnnounce) {
    Write-Host "=== WP-12 Schritt 1: Delisting-Register (Bybit public announcements) ==="
    python scripts\wp12_delisting.py --announce --register-base $RegisterBase
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Announce fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEINE Probe, KEIN Report."
        exit $LASTEXITCODE
    }
}

if (-not $SkipProbe) {
    Write-Host ""
    Write-Host "=== WP-12 Schritt 2: Kline-Verfuegbarkeits-Probe ($WindowDays Tage) ==="
    python scripts\wp12_delisting.py --probe-klines --register-base $RegisterBase --window-days $WindowDays
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Kline-Probe fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Report."
        exit $LASTEXITCODE
    }
}

$mode = "fixture"
if ($ProbeOnly) { $mode = "probe" }

$partialArgs = @()
if ($AllowPartial) { $partialArgs = @("--allow-partial") }

Write-Host ""
Write-Host "=== WP-12 Schritt 3: Report (--mode $mode) -> $OutDir ==="
python scripts\wp12_delisting.py --mode $mode --register-base $RegisterBase `
    --panel-base $PanelBase --manifest $Manifest --start-year $StartYear --end-year $EndYear `
    --as-of $AsOf --seed $Seed --n-boot $NBoot --out $OutDir @partialArgs
$rc = $LASTEXITCODE

if (-not $SkipDelistedFetch) {
    Write-Host ""
    Write-Host "=== WP-12 Schritt 4: Delisted-Panel fetchen (WP-12b, DEC-70) -> $DelistedPanelBase ==="
    python scripts\wp12_delisting.py --fetch-delisted-panel --register-base $RegisterBase `
        --delisted-panel-base $DelistedPanelBase --start-year $StartYear
    $delistedRc = $LASTEXITCODE
    if ($delistedRc -ne 0) {
        Write-Error "Delisted-Panel-Fetch fehlgeschlagen (rc=$delistedRc). Ausgabe oben pruefen."
        exit $delistedRc
    }
} else {
    Write-Host ""
    Write-Host "=== WP-12 Schritt 4: Delisted-Panel fetchen -- UEBERSPRUNGEN (-SkipDelistedFetch) ==="
}

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Delisted-Panel in: $DelistedPanelBase (fuer run_wp7_universe.ps1 -IncludeDelisted)"
Write-Host "Bitte wp12_report.md und wp12_summary.json hochladen (rc=$rc)."
Write-Host "Hinweis: KEIN PASS/FAIL -- die registrierte B3-Schwelle ist noch nicht gesetzt (DEC-67 E1)."
exit $rc
