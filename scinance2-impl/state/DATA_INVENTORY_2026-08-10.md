# Verifizierte Daten-Inventur — Stand 2026-08-10

> Vollständige Verzeichnis-Inventur der Nutzer-Maschine + Stichproben-
> Verifikation der Payload-Formen auf historischen UND aktuellen Tagen.
> **Zweck: Ende der Annahmen.** Zwei Wellen wurden durch Datenverfügbarkeits-
> Claims verzögert, die nie gegen `done_days` geprüft wurden (Welle-5-Scout:
> Verzeichnis-Existenz statt Symbol×Datum-Abdeckung; H-11-Unlock: Lebenszeit-
> Ordner statt Fenster-Abdeckung). Jede künftige Pre-Registration bindet sich
> an dieses Dokument oder an eine neuere Inventur — nicht an Erinnerung.

## 1. Der Hauptbefund: lückenlose Mehrjahres-Tickhistorie

| Strom | Zeitraum | Tage | Kalendertage | Status |
|---|---|---:|---:|---|
| `bybit/publicTrade` BTCUSDT | 2020-03-25 .. 2026-08-10 | 2330 | 2330 | **LÜCKENLOS (6,4 Jahre)** |
| `bybit/publicTrade` ETHUSDT | 2020-10-21 .. 2026-08-10 | 2120 | 2120 | **LÜCKENLOS (5,8 Jahre)** |
| `bybit/publicTrade` XRPUSDT | 2021-05-13 .. 2026-08-10 | 1916 | 1916 | **LÜCKENLOS** |
| `bybit/publicTrade` SOLUSDT | 2021-06-29 .. 2026-08-10 | 1869 | 1869 | **LÜCKENLOS** |
| `bybit/publicTrade` BNBUSDT | 2021-06-29 .. 2026-08-10 | 1869 | 1869 | **LÜCKENLOS** |

**Format verifiziert (Stichproben 2021-09-15, 2024-06-03, 2026-07-25):** durchgehend die FLACHE Backfill-Form
`{"timestamp":"…","symbol":"…","side":"Buy|Sell","size":"…","price":"…","tickDirection":"…","trdMatchID":"…"}`
— also exakt die Form, die alle Loader bit-identisch lesen. Dichte real
(BTC: 218k Trades am 2021-09-15, 1,46 M am 2024-06-03).

**Tragweite:** Alle bisherigen Hypothesen (H-01..H-18) liefen auf Fenstern
von ~100 Tagen. Verfügbar sind 5–6 Jahre über fünf Symbole und mehrere
Marktregime (Corona-Crash 2020, Bull 2021, Bär 2022, 2023–24, 2025–26).
Das ist die Voraussetzung dafür, Horizonte von Tagen bis Wochen überhaupt
vorregistrierbar zu machen — und damit der einzige bekannte Weg aus dem
im Welle-5-Abschlussbericht diagnostizierten **Horizont-Problem**
(alle bisherigen Befunde leben auf Sekunden-Skalen, wo die ~15-bps-Wand
jede Monetarisierung um Faktor 80–500 erschlägt).

## 2. Der H-11-Blocker — präzise lokalisiert

Die H-11-Entsperrbedingung verlangt lückenlose `done_days` für bybit
`publicTrade` **UND** `rest.fundingRate`, BTC+ETH, über 2024-03-27..2026-03-26
(≥730 Tage).

| Strom | Abdeckung | reicht? |
|---|---|---|
| `bybit/publicTrade` BTC/ETH | 2330 / 2120 Tage ab 2020 | **ja, längst** |
| `bybit/rest.fundingRate` | nur 2026-03-19 .. 2026-08-01 (113 Tage) | **NEIN — einziger Blocker** |

Die Arithmetik bestätigt es: Der Unlock-Check meldete „8 von 730 Tagen" —
exakt die Überlappung von `fundingRate` (ab 2026-03-19) mit dem Fensterende
(2026-03-26). **Benötigt wird ausschließlich ein Funding-Backfill**
(~730 Tage × 3 Settlements × 2 Symbole ≈ 4.400 REST-Records über
`/v5/market/funding/history`), NICHT der ursprünglich beauftragte
Trade-Deep-Backfill.

## 3. Übrige Ströme (Kurzfassung)

| Strom | Abdeckung | Bewertung |
|---|---|---|
| `bybit/orderbook` BTC / ETH | 961 / 530 Tage ab 2023-01-18, **lückenhaft (74 % / 41 %)** | L2 existiert deutlich tiefer als bisher dokumentiert (alter Stand: „forward-only ab 2026-06-16"). **Format gemischt:** historisch `orderbook.500` SNAPSHOT, live `orderbook.1000` DELTA — eine L2-Hypothese müsste beide Regime behandeln oder sich auf eines beschränken. 432k–863k Zeilen/Tag. |
| `bybit/orderbook` SOL/BNB/XRP | 35 Tage | zu dünn |
| `binance/publicTrade` | BTC 519 Tage (ab 2025-01-01), übrige 4 je 128 Tage | für Cross-Venue ab 2026-03-27 vollständig |
| `binance/orderbook` | 4 Symbole 106 Tage, **BTC nur 23 Tage** (Lücken) | Cross-Venue-L2 nur eingeschränkt |
| `deribit/publicTrade` | BTC-/ETH-PERPETUAL je 126 Tage (ab 2026-03-27) | ok für Cross-Venue-Fenster |
| `deribit/dvol` | BTC+ETH je 112 Tage | Vol-Index-Zielmetrik |
| `deribit/markprice.options` | btc_usd/eth_usd je 43 Tage (ab 2026-06-16) | wächst kalendarisch; H-13-Entsperrung noch offen |
| `deribit/tickers` | 5964 Symbole, ~38 Tage | volle Optionskette per Strike — reich, aber jung |
| `bybit/tickers` | 3751 Symbole, 43 Tage | enthält `markPrice`/`openInterestValue` als **Delta** (nur geänderte Felder, 705k Zeilen/Tag) → Premium-Index nur per zustandsbehaftetem Delta-Merging rekonstruierbar. **Zu jung für DSM-03.** |
| `bybit/rest.openInterest` | 113 Tage | |
| `bybit/allLiquidation` | 43 Tage (BTC/ETH), 35 (übrige) | |
| `bybit/insurance` | 43 Tage | Kaskaden-Schwelle (≥30 Events) weiter offen |
| `bitmex/publicTrade` XBTUSD | **nur 112 Tage** (2026-03-19 .. 2026-08-01) | die in älteren Docs genannte 2014er-Tiefe existiert NICHT |
| `tardis/options_chain` | **2 Tage** über 3 Monate | bestätigt 1-Tag-pro-Monat-Sampling → Options-Chain-Kandidaten (CHAIN-GRAPH, SET-SHAPE) endgültig nicht registrierbar |

## 4. Direkte Konsequenzen

1. **H-11 ist mit minimalem Aufwand entsperrbar** (4.400 Funding-Records) — der einzige registrierte Pfad mit Friktions-Arithmetik ÜBER der Wand (25–75×).
2. **DSM-03 (Funding-Premium) ist NICHT registrierbar** — Premium-Index nur 43 Tage und nur als Delta-Strom. Vom Welle-6-Vorschlag gestrichen.
3. **Options-Chain-Kandidaten sind tot** (Tardis-Sampling), **Bitmex-Multi-Zyklen-Ideen ebenfalls** (keine Tiefe).
4. **L2-Kandidaten sind möglich, aber teurer als gedacht** (Format-Bruch snapshot-500/delta-1000, 26 %/59 % Lücken).
5. **Der eigentliche Hebel ist die lückenlose 5-Symbol-Mehrjahres-Tickhistorie** — sie ist von keiner einzigen bisherigen Hypothese genutzt worden und adressiert als einzige das Horizont-Problem.
