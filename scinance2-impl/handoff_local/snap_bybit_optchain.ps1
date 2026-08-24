# snap_bybit_optchain.ps1 -- Ueberbrueckungs-Sampler fuer Bybit-Optionsketten
#
# Zweck: Der WP-5-Zensus steht bei n=1 in der Zeit. Bis der Harvester den
# Options-Strom aufzeichnet (AUFTRAG_HARVESTER_BYBIT_OPTIONS.md), erzeugt
# dieses Skript eine billige Zeitreihe aus dem OEFFENTLICHEN REST-Endpoint.
#
# Oeffentlich, read-only, KEINE Keys, KEINE Orders.
#
# Schreibt je Lauf und Basiswert eine schlanke JSON-Datei, die genau die
# Felder enthaelt, die der Zensus liest:
#   <out>\<COIN>\<COIN>_<yyyyMMdd_HHmmss>Z.json
#
# Volumen (gemessen am 2026-08-24-Snapshot): rund 276 KB (BTC) + 224 KB (ETH)
# je Lauf, zusammen ~0,5 MB. Bei 15-Minuten-Takt also ~48 MB/Tag, ~1,4 GB/Monat.
#
# Verwendung (einmaliger Testlauf):
#   powershell -ExecutionPolicy Bypass -File .\snap_bybit_optchain.ps1 `
#       -OutDir "E:\Claude\Projects\scinance\data\optchain_snaps"
#
# Dauerbetrieb -- als geplante Aufgabe alle 15 Minuten registrieren:
#   $a = New-ScheduledTaskAction -Execute "powershell.exe" `
#        -Argument '-ExecutionPolicy Bypass -File "C:\pfad\snap_bybit_optchain.ps1" -OutDir "E:\...\optchain_snaps"'
#   $t = New-ScheduledTaskTrigger -Once -At (Get-Date) `
#        -RepetitionInterval (New-TimeSpan -Minutes 15)
#   Register-ScheduledTask -TaskName "BybitOptChainSnap" -Action $a -Trigger $t

param(
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string[]]$BaseCoins = @("BTC", "ETH"),
    [int]$RetryCount = 3
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Genau die Felder, die bybit_edge.research.wp5_optchain.census.load_snapshot liest.
$KEEP = @(
    "symbol", "bid1Price", "bid1Size", "bid1Iv",
    "ask1Price", "ask1Size", "ask1Iv",
    "markPrice", "markIv", "underlyingPrice",
    "delta", "gamma", "vega", "theta",
    "openInterest", "volume24h", "turnover24h"
)

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$rc = 0

foreach ($coin in $BaseCoins) {
    $url = "https://api.bybit.com/v5/market/tickers?category=option&baseCoin=$coin"
    $list = $null
    for ($try = 1; $try -le $RetryCount; $try++) {
        try {
            $resp = Invoke-RestMethod -Uri $url -TimeoutSec 30
            if ($resp.retCode -ne 0) {
                throw "retCode=$($resp.retCode) retMsg=$($resp.retMsg)"
            }
            $list = $resp.result.list
            break
        } catch {
            Write-Warning "$coin Versuch $try/$RetryCount fehlgeschlagen: $($_.Exception.Message)"
            if ($try -lt $RetryCount) { Start-Sleep -Seconds ([Math]::Pow(2, $try)) }
        }
    }

    # Laut scheitern statt still einen leeren Tag zu schreiben (Programm-Lehre GL-004).
    if ($null -eq $list -or $list.Count -eq 0) {
        Write-Error "$coin : keine Symbole erhalten -- KEINE Datei geschrieben."
        $rc = 1
        continue
    }

    $slim = $list | Select-Object -Property $KEEP
    $dir = Join-Path $OutDir $coin
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $path = Join-Path $dir ("{0}_{1}Z.json" -f $coin, $stamp)

    # -Depth 4 reicht fuer eine flache Objektliste; ohne Depth kuerzt PS still.
    $json = $slim | ConvertTo-Json -Depth 4 -Compress
    [IO.File]::WriteAllText($path, $json, (New-Object Text.UTF8Encoding($false)))

    $kb = [Math]::Round((Get-Item $path).Length / 1KB, 1)
    Write-Host ("{0}: {1} Symbole -> {2} ({3} KB)" -f $coin, $slim.Count, $path, $kb)
}

exit $rc
