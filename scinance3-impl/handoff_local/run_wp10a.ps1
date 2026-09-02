# run_wp10a.ps1 -- WP-10 Teil A: Praemien-Kohaerenz im Stress (deskriptiv)
# (WP10_SPEZIFIKATION.md, Teil A). Drei Schritte, immer in dieser Reihenfolge:
#
#   1) Probe        -- welche Serien/Felder vorhanden sind, Abdeckung.
#                       NUR bei rc=0 geht es weiter.
#   2) Stress-Kanon -- STRESS_REL (DEC-55) + STRESS_ABS (DEC-56) Fixturen
#                       aus dem WP-0-Bar-Cache schreiben (append-only).
#   3) Run          -- Serien laden, Kohaerenz-Matrix + Portfolio-Nulleffekt
#                       rechnen, JSON+Markdown+DEC-53-Artefakte schreiben.
#
# ASCII-only (PowerShell 5.1). rc != 0 bei Probe-Fehler bricht den Lauf ab.
# Teil A ist rein deskriptiv -- dieses Skript faellt kein PASS/FAIL-Urteil.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$HarvestBase = "E:\Claude\Projects\scinance\data\harvest",
    [string]$CacheDir = "",
    [string]$FundingSymbols = "BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT",
    [string]$IvrvCurrencies = "BTC,ETH",
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
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp10a_$(Get-Date -Format yyyyMMdd)"
}

$rangeArgs = @()
if ($Start -ne "") { $rangeArgs += @("--start", $Start) }
if ($End -ne "") { $rangeArgs += @("--end", $End) }

Write-Host "=== WP-10(A) Schritt 1: Probe (Serien/Felder, Abdeckung) ==="
python scripts\wp10_coherence.py --probe --base $HarvestBase --cache-dir $CacheDir `
    --funding-symbols $FundingSymbols --ivrv-currencies $IvrvCurrencies --basis-symbols $BasisSymbols
if ($LASTEXITCODE -ne 0) {
    Write-Error "Probe fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Stress-Kanon, KEIN Run."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-10(A) Schritt 2: Stress-Kanon (STRESS_REL/DEC-55, STRESS_ABS/DEC-56) ==="
python scripts\wp10_coherence.py --stress-canon --cache-dir $CacheDir `
    --stress-canon-out $StressCanonOut @rangeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Stress-Kanon fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Run."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-10(A) Schritt 3: Run (Kohaerenz + Portfolio-Nulleffekt) ==="
python scripts\wp10_coherence.py --run --base $HarvestBase --cache-dir $CacheDir `
    --funding-symbols $FundingSymbols --ivrv-currencies $IvrvCurrencies --basis-symbols $BasisSymbols `
    --stress-canon-out $StressCanonOut --out $OutDir --seed $Seed @rangeArgs
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp10a_summary.json und wp10a_report.md hochladen (rc=$rc)."
Write-Host "Teil A ist deskriptiv -- kein PASS/FAIL-Urteil in diesem Lauf."
exit $rc
