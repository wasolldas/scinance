# Antwort Data Harvest → Scinance (2026-10-20) zum Auftrag vom 2026-10-18

Alle Ströme liegen im normalen Archiv-Layout und stehen nach dem nächsten
Katalog-Export in `hd.catalog()`. Ausgegeben werden nur Zählungen, Zeitstempel
und Feldnamen, keine Preis-, Rendite- oder Vol-Statistik (Blind-Siegel DEC-96 E3).
Lücken sind benannt und nicht gefüllt. Volumina sind Schätzungen.

Gemeinsames Format der neuen REST-Ströme: Kestrel-Schema (6 Spalten),
`payload_json` = API-Zeile wörtlich (Zahlen als Strings), ergänzt um
`category`, wo die API sie nicht mitliefert. Wo eine Zeile je Instrument
entsteht, gibt es **eine Partition je Tag mit `symbol=ALL`**. Das Instrument
steht in der Spalte `symbol` und in `payload_json`. So wächst der Katalog nicht
um ~900 Mini-Partitionen pro Tag. Jeder Tag wird einmal und vollständig
geschrieben und gilt dann als `DONE`. Die Läufe holen fehlende Tage der letzten
30 Tage selbst nach (Selbstheilung). Die Taktung kommt von Timern auf dem
Datenserver: täglich 00:20 und 12:20 UTC, Quotes alle 15 Minuten.

## B-0 — Inventur `done_days` für H-26 (nur Zählung)

Tagestabelle (je Paar und Tag: Manifest-Status, Herkunft, Zeilen, Abdeckung):
`state/scinance_b0_done_days_2026-10-20.csv` im Data-Harvest-Repo. Zeitraum
2025-08-01 … 2026-10-19 (445 Tage). BTC und ETH ergeben jeweils dieselben Tage.

- **`deribit/dvol` wird nie live gesammelt**, nur per REST (lückenlos `DONE`
  ab 2021-03-24). In der strengen Lesart („beide Ströme live“) gibt es daher
  **0 Tage**; diese Lesart ist nicht erfüllbar.
- **`deribit/publicTrade` BTC-/ETH-PERPETUAL:** Die Herkunft ist über die
  Topic-Spalte eindeutig (`trades.*` = live, `publicTrade.*` = REST). 112 Tage
  live (ab 2026-06-16), 126 Tage per REST, 207 Tage ohne Partition (vor allem
  2025-08 … 2026-03). Kein Tag ist gemischt.
- **Live-vollständig** heißt hier: Live-Trades vom Tagesanfang bis zum
  Tagesende (Rand höchstens 30 bzw. 60 Min) ohne Lücke über der Grenze, gemessen
  nach Ankunftszeit, und beide Ströme `DONE`:

| Lesart | Tage | längste Folge | laufende Folge (bis 2026-10-19) | 210 Tage erreicht |
|---|---|---|---|---|
| streng (beide live) | 0 | 0 | 0 | nicht erfüllbar |
| dvol DONE + Perp live, Lücke ≤ 30 Min | 76 | 15 (2026-09-16 … 09-30) | 6 | frühestens 2027-05-11 |
| dvol DONE + Perp live, Lücke ≤ 60 Min | 81 | 41 (2026-09-09 … 10-19) | 41 | frühestens 2027-04-06 |
| dvol DONE + Perp live, Lücke ≤ 120 Min | 82 | 41 (2026-09-09 … 10-19) | 41 | frühestens 2027-04-06 |
| Manifest `DONE` (live oder REST) | 238 | 207 (2026-03-27 … 10-19) | 207 | **2026-10-22**, falls ohne Unterbrechung |

Die Grenze 30 gegen 60 Min entscheidet über 13 Monate. Die Gründe für die
gescheiterten Live-Tage stehen in der Tabelle: Im Juni/Juli lief der Collector
nicht ganztägig, im August gab es Ausfälle von 40 Min bis 15 h.

## B-1 — Tages-Panel aller linearen Bybit-Perps (Variante B)

| Strom | Inhalt | Start | Lücken |
|---|---|---|---|
| `bybit/rest.instruments` | Tagesschnappschuss linear + inverse, **alle Status** (Trading, PreLaunch, Delivering, Closed): status, launchTime, deliveryTime, fundingInterval, upper/lowerFundingRate, deliveryFeeRate | **2026-10-20** (nicht nachladbar; erster Tag 2.017 Instrumente) | keine |
| `bybit/rest.kline1d` | Tageskerze jedes linearen Perps, der an dem Tag lebte, delistete bis zum letzten Handelstag (USDT- und USDC-Perps) | 2026-09-29 | keine (850–868 Perps je Tag) |
| `bybit/rest.fundingRateAll` | jede Funding-Abrechnung aller linearen Perps (Intervalle 1 h, 4 h, 8 h) | 2026-09-29 | keine (~3.800–3.900 Abrechnungen je Tag) |
| `bybit/delisting_dates` | Delisting-Register je Stichtag; jüngste Partition = aktueller Stand | 2026-10-20 | — |

- **Wichtig:** Ohne Filter liefert instruments-info nur `Trading`. Geschlossene
  Kontrakte gibt es nur mit `status=Closed`. Der Schnappschuss fragt alle Status
  ab. Alle 330 geschlossenen Linear-Perps tragen `deliveryTime` (= Delisting).
  Das Register reicht damit sofort zurück bis 2022: heute 333 delistete Perps
  (327 linear, 6 invers).
- **Register-Felder:** `last_trading_day` = Kalendertag von `deliveryTime − 1 ms`
  (Stichtag nach DEC-72; Delisting meist 09:00 UTC → derselbe Tag);
  `first_seen_closed` = erster Schnappschuss, in dem der Status `Closed` war
  (`null` für alle, die schon vor dem 2026-10-20 delistet waren).
- **Kerzen und Funding** antworten für delistete Symbole bis zum Delisting-Tag
  (geprüft an 5 Delistings im Okt./Sep. 2026). Der Delisting-Tag ist eine
  Teilkerze.
- **Funding aller Perps** liegt im **eigenen Strom `rest.fundingRateAll`**.
  `bybit/rest.fundingRate` bleibt unverändert (5 Majors je Symbol), um die
  Partitionierung nicht zu mischen.
- Tagesschluss BTC/ETH: steht in `rest.kline1d`. Volumen (gemessen): ~0,1 MB/Tag für Kerzen + Funding, 0,15 MB je Instruments-Schnappschuss.

## B-2 — Quotes der datierten Bybit-Futures (A4)

**(a) Befund `bybit/tickers`:** Datierte Kontrakte werden dort **nicht**
gesammelt (nur BTC/ETH/SOL/BNB/XRP-USDT-Perps und Optionen). Die Perp-Ticker
per WebSocket sind **Deltas**: Je Nachricht stehen nur geänderte Felder drin.
Bid1/Ask1 fehlen in etwa einem Viertel der Nachrichten; `markPrice` steht in
~9 %, `openInterest` in ~1 %. Feldnamen mit „1“: `bid1Price`, `bid1Size`,
`ask1Price`, `ask1Size`. Kein `deliveryTime` und kein `basis` im Perp-Strom.
Deshalb (b):

**(b) `bybit/rest.tickers15m`** — REST-Schnappschuss alle 15 Minuten (:00,
:15, :30, :45 UTC), ab **2026-10-20**, eine Datei je Schnappschuss in der
Tagespartition `symbol=ALL`:
- alle datierten BTC/ETH-Futures (heute 20: USDT-Monats-/Quartalskontrakte
  `BTCUSDT-23OCT26` … `-24SEP27` sowie die inversen `BTCUSDZ26`, `BTCUSDH27`
  und ETH-Pendants),
- dazu die Perps BTCUSDT, ETHUSDT, BTCUSD, ETHUSD, BTCPERP, ETHPERP (heute 26
  Kontrakte).
- Felder: `bid1Price`, `bid1Size`, `ask1Price`, `ask1Size`, `markPrice`,
  `indexPrice`, `deliveryTime`, `basis`, `basisRate`, `basisRateYear`,
  `openInterest`, `deliveryFeeRate`, `predictedDeliveryPrice`, `fundingRate` u. a.
- Neue Kontrakte kommen automatisch hinzu. Volumen ~1,5 MB/Monat.

**(c)** `bybit/rest.deliveryPrice`: Settlement-Historie, soweit die API sie
hat (linear ab 2023-03-24, invers ab 2021-06-25, letzte bisher 2026-09-25; 302
Lieferungen an 119 Tagen, Partition = Liefertag). instruments-info linear + invers täglich mit `deliveryFeeRate`:
siehe `rest.instruments` (B-1).

## B-3 — 1-Minuten-Kerzen `bybit/rest.kline1m`

- **Probe:** BTCUSDT hat 1-Minuten-Kerzen ab **2020-03-25 ~16:38 UTC**. Der
  optionale Start 2020-03-25 ist also möglich; der erste Tag ist eine Teilkerze.
  **ETHUSDT gibt es bei Bybit erst ab 2021-03-15**, nicht ab 2021-03-01. Davor
  existiert das Symbol nicht.
- Je Symbol und Tag eine Partition. `rows` im Katalog < 1440 zeigt eine Lücke
  an; sie wird benannt, nie gefüllt. Danach täglich laufend.
- Stand: Der Backfill läuft seit 2026-10-20 18:34 (~4.450 Tage, ~9.000 Aufrufe)
  und ist voraussichtlich in der Nacht fertig. Danach ist er im Katalog. Die
  Liste der unvollständigen Tage (< 1440 Minuten) liefern wir mit dem Abschluss nach.
  Ein Tag (BTCUSDT 2020-04-13) wurde von Bybit zunächst abgelehnt („svc error“)
  und ging beim zweiten Versuch durch; abgelehnte Tage werden wiederholt, nie übersprungen.

## B-4 — Deribit-Verfallskalender und Settlement

| Strom | Inhalt | Start |
|---|---|---|
| `deribit/rest.settlements` (`symbol=BTC` / `ETH`) | Delivery- und Settlement-Ereignisse je Instrument: Zeitpunkt, Instrument, Typ, `index_price`, `mark_price` | BTC 2017-05-25, ETH 2019-03-15; lückenlos (BTC 3.435, ETH 2.776 Tage) |
| `deribit/rest.deliveryPrices` (`symbol=ALL`) | täglicher Delivery-Preis btc_usd, eth_usd | btc_usd 2016-03-18, eth_usd 2019-03-29 |
| `deribit/rest.instruments` (`symbol=ALL`) | Tagesschnappschuss Futures + Optionen (aktiv und am Tag verfallen): expiration_timestamp, settlement_period (day/week/month/perpetual), creation_timestamp | 2026-10-20 (1.790 Instrumente) |

- `get_instruments(expired=true)` liefert bei Deribit **nur die am selben Tag
  verfallenen** Instrumente, keine Historie. Die Ereignismenge vor dem
  2026-10-20 (Verfallstermine, Settlement-Zeitlage) steckt vollständig in
  `rest.settlements`: Typ `delivery` je verfallenem Instrument, Typ
  `settlement` = tägliche Abrechnung. Ab heute kommt der Vorwärtskalender
  täglich aus `rest.instruments`.
- Volumen (gemessen): Settlements 28 MB, Delivery-Preise 6 MB für die ganze Historie; danach < 0,1 MB/Tag.

## B-5 — Options-Quotes (nur Prüfung)

| Strom | Art | best bid/ask | IV | Greeks | sonst |
|---|---|---|---|---|---|
| `deribit/tickers` (Optionen, seit 2026-06-16) | voller Schnappschuss je Nachricht | `best_bid_price/amount`, `best_ask_price/amount` | `bid_iv`, `ask_iv`, `mark_iv` | delta, gamma, vega, theta, rho | open_interest, underlying_price/index, mark_price, settlement_price |
| `bybit/tickers` (Optionen) | `type=snapshot` (voll) | `bidPrice/bidSize`, `askPrice/askSize` (ohne „1“) | `bidIv`, `askIv`, `markPriceIv` | delta, gamma, vega, theta (kein rho) | openInterest, underlyingPrice, indexPrice, markPrice |
| `deribit/markprice.options` (`btc_usd`, `eth_usd`) | je Instrument | — | `iv` | — | `mark_price` |

Die Felder sind über den ganzen Zeitraum gleich geblieben (Stichproben 2026-06-16,
-08-25, -10-19). Für Bybit-Optionen gibt es zusätzlich den reduzierten Strom
`bybit/tickers_1h` (letzter Record je Instrument und Stunde, DEC-61).

**Tagesgenaue Lückenkarte** (je Tag: Instrumente mit Daten, abgedeckte UTC-Stunden):
`state/scinance_b5_chain_coverage_2026-10-20.csv`. Kurzfassung 2026-06-16 … 10-19:
- an **14 Tagen keine Optionsdaten auf beiden Börsen**: 06-26, 07-06 … 07-16, 08-01, 08-14;
- an **9 weiteren Tagen keine Bybit-Optionen**: 06-17, 06-19, 06-20, 06-22,
  06-24, 06-27, 07-17, 07-25, 08-02;
- **Deribit** an 81 Tagen 24/24 h. An 31 Tagen nur teilweise (4–23 h), vor
  allem 06-16 … 06-25 (~9 h je Tag), 07-17 (4 h) und mehrere Augusttage;
- Bybit-Stunden je Tag: Die Spalte füllt sich erst nach dem `tickers_1h`-Nachbau;
  wir liefern die vollständige Karte nach.

## Nicht beauftragt, nicht gebaut

Binance-Perp-Panel, getrennter Archiv-Trade-Strom BTC/ETH.
