# vorfragen_v1_v4.ps1 -- Scinance 3.0, Welle 1: die vier 10-Minuten-Vorfragen
# Oeffentliche Bybit-v5-Endpunkte, KEINE Keys, KEINE Orders, read-only.
#
#   V-1  Tiefe der Funding-Historie je Symbol (/v5/market/funding/history)
#   V-2  Liquiditaet der datierten Bybit-Futures (turnover24h)
#   V-3  Median(Ist-Funding - Zinsanker I) auf den letzten 43 Tagen
#   V-1b Zins-Term/Intervall/Cap je Kontrakt, V-6 Totzonen-Zensus, V-5a Deribit-Verfaelle
#   V-4  Delivery-/Settlement-Gebuehr: NICHT automatisierbar -> Anleitung am Ende
#
# Aufruf:  powershell -ExecutionPolicy Bypass -File .\scinance3-impl\handoff_local\vorfragen_v1_v4.ps1
# Ausgabe: Konsole + scinance3-impl\handoff_local\results\vorfragen_<datum>.txt

$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$base = "https://api.bybit.com"
$outDir = Join-Path $PSScriptRoot "results"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$outFile = Join-Path $outDir ("vorfragen_{0}.txt" -f (Get-Date -Format yyyyMMdd_HHmm))
Start-Transcript -Path $outFile | Out-Null

function Get-Json($url) {
    try { return Invoke-RestMethod -Uri $url -TimeoutSec 30 }
    catch { Write-Warning "FEHLER $url : $($_.Exception.Message)"; return $null }
}
function ToDate($ms) { return [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ms).UtcDateTime }

Write-Host "=============================================================="
Write-Host " V-1  Funding-Historie: wie weit zurueck?"
Write-Host "=============================================================="
$symbols = @("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT","DOGEUSDT","AVAXUSDT")
$v3 = @{}
foreach ($s in $symbols) {
    $endTime = $null; $n = 0; $earliest = $null; $latest = $null; $rates = @()
    for ($page = 0; $page -lt 400; $page++) {   # 400 x 200 = 80.000 Records max
        $url = "$base/v5/market/funding/history?category=linear&symbol=$s&limit=200"
        if ($endTime) { $url += "&endTime=$endTime" }
        $r = Get-Json $url
        if ($null -eq $r -or $r.retCode -ne 0) { break }
        $list = $r.result.list
        if (-not $list -or $list.Count -eq 0) { break }
        $n += $list.Count
        $ts = $list | ForEach-Object { [int64]$_.fundingRateTimestamp }
        $minTs = ($ts | Measure-Object -Minimum).Minimum
        $maxTs = ($ts | Measure-Object -Maximum).Maximum
        if ($null -eq $earliest -or $minTs -lt $earliest) { $earliest = $minTs }
        if ($null -eq $latest -or $maxTs -gt $latest) { $latest = $maxTs }
        if ($page -eq 0) { $rates = $list }   # neueste 200 Records fuer V-3 merken
        $endTime = $minTs - 1
        Start-Sleep -Milliseconds 120
    }
    if ($n -gt 0) {
        $days = [Math]::Round(($latest - $earliest) / 86400000.0, 1)
        Write-Host ("{0,-10} Records={1,6}  von {2:yyyy-MM-dd}  bis {3:yyyy-MM-dd}  = {4} Tage" -f $s, $n, (ToDate $earliest), (ToDate $latest), $days)
        $v3[$s] = $rates
    } else {
        Write-Host ("{0,-10} KEINE Daten" -f $s)
    }
}

Write-Host ""
Write-Host "=============================================================="
Write-Host " V-2  Datierte Futures auf Bybit: gibt es sie, sind sie liquide?"
Write-Host "=============================================================="
foreach ($cat in @("linear","inverse")) {
    $info = Get-Json "$base/v5/market/instruments-info?category=$cat&limit=1000"
    if ($null -eq $info) { continue }
    $dated = $info.result.list | Where-Object { $_.contractType -match "Futures" }
    Write-Host ("category={0}: {1} Instrumente gesamt, davon {2} datierte (contractType~Futures)" -f $cat, $info.result.list.Count, $dated.Count)
    if ($dated.Count -gt 0) {
        $tick = Get-Json "$base/v5/market/tickers?category=$cat"
        $tmap = @{}
        foreach ($t in $tick.result.list) { $tmap[$t.symbol] = $t }
        foreach ($d in $dated | Sort-Object deliveryTime) {
            $t = $tmap[$d.symbol]
            $turn = if ($t) { [double]$t.turnover24h } else { 0 }
            $oi   = if ($t) { $t.openInterest } else { "-" }
            Write-Host ("  {0,-22} Verfall {1:yyyy-MM-dd}  turnover24h={2,14:N0} USD  OI={3}" -f $d.symbol, (ToDate $d.deliveryTime), $turn, $oi)
        }
    }
}

Write-Host ""
Write-Host "=============================================================="
Write-Host " V-3  Median(Ist-Funding - Zinsanker I) auf den neuesten ~43 Tagen"
Write-Host "      I = 0,01 % je 8 h (Bybit-Zinsterm). Ausgabe annualisiert."
Write-Host "=============================================================="
foreach ($s in $symbols) {
    if (-not $v3.ContainsKey($s)) { continue }
    $recs = $v3[$s]
    # Funding-Intervall aus den Zeitstempeln ableiten (1h- vs 8h-Symbole!)
    $tsSorted = $recs | ForEach-Object { [int64]$_.fundingRateTimestamp } | Sort-Object
    $gaps = @(); for ($i = 1; $i -lt $tsSorted.Count; $i++) { $gaps += ($tsSorted[$i] - $tsSorted[$i-1]) }
    # Median von Hand (PowerShell 5.1 kennt Measure-Object -Median nicht)
    $gs = $gaps | Sort-Object
    $gapH = [Math]::Round(($gs[[int]($gs.Count/2)]) / 3600000.0, 2)
    $perYear = 8760.0 / $gapH
    $I = 0.0001 * ($gapH / 8.0)
    $cut = [int64]((Get-Date).ToUniversalTime().AddDays(-43) - (Get-Date "1970-01-01")).TotalMilliseconds
    $vals = $recs | Where-Object { [int64]$_.fundingRateTimestamp -ge $cut } | ForEach-Object { [double]$_.fundingRate - $I } | Sort-Object
    if ($vals.Count -eq 0) { Write-Host ("{0,-10} keine Records in 43 Tagen" -f $s); continue }
    $med = $vals[[int]($vals.Count/2)]
    $mean = ($vals | Measure-Object -Average).Average
    Write-Host ("{0,-10} Intervall={1,4}h  n={2,4}  Median(F-I)={3,8:P4} je Intervall = {4,7:N2}% p.a.   Mean = {5,7:N2}% p.a." -f $s, $gapH, $vals.Count, $med, ($med*$perYear*100), ($mean*$perYear*100))
}

Write-Host ""
Write-Host "=============================================================="
Write-Host " V-1b Zins-Term / Funding-Intervall / Cap je Kontrakt (instruments-info)"
Write-Host "      und V-6 Totzonen-Zensus (Anteil Funding exakt = I) auf V-1-Daten"
Write-Host "=============================================================="
$info = Get-Json "$base/v5/market/instruments-info?category=linear&limit=1000"
if ($info) {
    $lst = $info.result.list
    Write-Host ("linear: {0} Instrumente; Feldnamen des ersten: {1}" -f $lst.Count, (($lst[0].PSObject.Properties.Name) -join ","))
    $grp = $lst | Group-Object fundingInterval | Sort-Object Name
    foreach ($g in $grp) { Write-Host ("  fundingInterval={0,5} min : {1,4} Symbole" -f $g.Name, $g.Count) }
    $caps = $lst | Group-Object upperFundingRate | Sort-Object Name
    foreach ($g in $caps) { Write-Host ("  upperFundingRate={0,-10} : {1,4} Symbole" -f $g.Name, $g.Count) }
    foreach ($s in @("BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT")) {
        $x = $lst | Where-Object { $_.symbol -eq $s }
        if ($x) { Write-Host ("  {0,-9} interval={1} upper={2} lower={3} launch={4}" -f $s, $x.fundingInterval, $x.upperFundingRate, $x.lowerFundingRate, $x.launchTime) }
    }
}
foreach ($s in $symbols) {
    if (-not $v3.ContainsKey($s)) { continue }
    $recs = $v3[$s]
    $rates = $recs | ForEach-Object { [double]$_.fundingRate }
    $n = $rates.Count
    $exact = ($rates | Where-Object { [Math]::Abs($_ - 0.0001) -lt 1e-9 }).Count
    $near  = ($rates | Where-Object { [Math]::Abs($_ - 0.0001) -lt 1e-6 }).Count
    Write-Host ("  {0,-9} Totzone: exakt I in {1,3} von {2,3} Records ({3,5:P1}); |F-I|<1e-6: {4,5:P1}" -f $s, $exact, $n, ($exact/[double]$n), ($near/[double]$n))
}

Write-Host ""
Write-Host "=============================================================="
Write-Host " V-5a Deribit-Verfallskalender (oeffentlich): Wochentag/Abstand der Verfaelle"
Write-Host "=============================================================="
foreach ($cur in @("BTC","ETH")) {
    $d = Get-Json "https://www.deribit.com/api/v2/public/get_instruments?currency=$cur&kind=option&expired=false"
    if ($null -eq $d) { continue }
    $exps = $d.result | ForEach-Object { [int64]$_.expiration_timestamp } | Sort-Object -Unique
    Write-Host ("{0}: {1} Verfalltermine offen" -f $cur, $exps.Count)
    foreach ($e in $exps) { $dt = ToDate $e; Write-Host ("  {0:yyyy-MM-dd ddd HH:mm} UTC" -f $dt) }
}
Write-Host " Ohne Primaerbeleg zur Zeitlage der Umkehr um 08:00 UTC (V-5c, Literatur) bleibt A2 gesperrt."

Write-Host ""
Write-Host "=============================================================="
Write-Host " V-4  Delivery-/Settlement-Gebuehr (manuell, Primaerquelle)"
Write-Host "=============================================================="
Write-Host " Bitte im Bybit-Konto unter Gebuehren / Fee Rate ablesen und hier eintragen:"
Write-Host "   (a) Optionen: Delivery Fee bei Verfall (in % des Index) und Deckelung (in % der Praemie/Intrinsic)"
Write-Host "   (b) Datierte Futures (USDC/Inverse): Delivery/Settlement Fee bei Verfall"
Write-Host " Ohne diese zwei Zahlen bleiben R1-K-03 und der Options-Block gesperrt (RAISE statt Default)."
Write-Host ""
Write-Host "=============================================================="
Write-Host " V-5a  Deribit-Verfallskalender: gibt es woechentliche Verfaelle?"
Write-Host "       (oeffentlich, keine Keys; Frage (b) Effektgroesse bleibt Literatur)"
Write-Host "=============================================================="
foreach ($cur in @("BTC","ETH")) {
    $ins = Get-Json "https://www.deribit.com/api/v2/public/get_instruments?currency=$cur&kind=option&expired=false"
    if ($null -eq $ins -or -not $ins.result) { Write-Host "$cur : keine Antwort"; continue }
    $exp = $ins.result | ForEach-Object { [int64]$_.expiration_timestamp } | Sort-Object -Unique
    Write-Host ("{0}: {1} Optionsserien, {2} verschiedene Verfallstermine (naechste 12):" -f $cur, $ins.result.Count, $exp.Count)
    $prev = $null
    foreach ($e in ($exp | Select-Object -First 12)) {
        $d = ToDate $e
        $gap = if ($prev) { [Math]::Round(($e - $prev) / 86400000.0, 1) } else { "-" }
        Write-Host ("   {0:yyyy-MM-dd ddd HH:mm} UTC   Abstand zum vorigen: {1} Tage" -f $d, $gap)
        $prev = $e
    }
}
Write-Host " Lesart: Abstaende von 1 Tag = Tages-, 7 Tage = Wochen-, ~30 = Monats-, ~90 = Quartalsverfaelle."
Write-Host ""
Write-Host "Ausgabe gespeichert: $outFile"
Stop-Transcript | Out-Null
