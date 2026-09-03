# run_wp11_relax.ps1 -- WP-11: Relaxationsrate der Aktivitaet nach
# Schockstunden (X-OEKO-1 Arm (a), PRD_SCINANCE3.md 11.3, DEC-58).
# Rein deskriptiv -- dieses Skript faellt kein PASS/FAIL-Urteil.
#
# Zwei Schritte, immer in dieser Reihenfolge:
#
#   1) Stress-Kanon -- STRESS_ABS (DEC-56) Fixture aus dem WP-0-Bar-Cache
#                       schreiben (append-only; wiederverwendet, falls
#                       WP-10(A) bereits eines geschrieben hat).
#   2) Run           -- H-20-Ereignisse einlesen (c20_tail.driver, kein
#                       neuer Parameter), Relaxationsraten fitten, JSON +
#                       Markdown + DEC-53-Artefakte schreiben.
#
# ASCII-only (PowerShell 5.1). rc != 0 bei Stress-Kanon-Fehler bricht ab.

param(
    [string]$RepoRoot = "E:\Claude\Projects\scinance",
    [string]$CacheDir = "",
    [string]$Symbols = "BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,BNBUSDT",
    [string]$StressCanonOut = "",
    [string]$OutDir = "",
    [int]$Seed = 42
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
    $OutDir = Join-Path $RepoRoot "scinance3-impl\state\wp11_$(Get-Date -Format yyyyMMdd)"
}

Write-Host "=== WP-11 Schritt 1: Stress-Kanon (STRESS_ABS/DEC-56) ==="
python scripts\wp10_coherence.py --stress-canon --cache-dir $CacheDir --stress-canon-out $StressCanonOut
if ($LASTEXITCODE -ne 0) {
    Write-Error "Stress-Kanon fehlgeschlagen (rc=$LASTEXITCODE). Ausgabe oben pruefen; KEIN Run."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== WP-11 Schritt 2: Run (Relaxationsrate) ==="
$StressAbsPath = Join-Path $StressCanonOut "stress_abs.json"
python scripts\wp11_relax.py --cache-dir $CacheDir --symbols $Symbols `
    --stress-abs $StressAbsPath --out-dir $OutDir --seed $Seed
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "Ergebnis in: $OutDir"
Write-Host "Bitte wp11_summary.json und wp11_report.md hochladen (rc=$rc)."
Write-Host "WP-11 ist deskriptiv -- kein PASS/FAIL-Urteil in diesem Lauf."
exit $rc
