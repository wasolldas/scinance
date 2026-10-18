# Auftrag an das Data-Harvest-Projekt: Datenstroeme fuer die blinden Fenster von Scinance 3.0 (2026-10-18)

> Grundlage: Programm-Bilanz `state/PROGRAMM_BILANZ_2026-10-18.md` Teil B, Review und DEC-98 (Orchestrator-Freigabe). Data-Harvest
> setzt Datenaenderungen jetzt selbststaendig um (Nutzer 2026-10-18). Kein Hostname, keine Zugangsdaten in dieser Datei.

## Gemeinsame Regeln fuer alle Auftraege
- Data-Harvest speichert und prueft Vollstaendigkeit (Zeilen, Luecken, Zeitstempel, Schema); keine Preis-, Rendite-
  oder Volatilitaetsstatistik. Scinance berechnet ab 2026-07-01 keine BTC/ETH-Vol- oder Renditestreuung (Blind-Siegel
  DEC-96 E3); bitte in Zusammenfassungen oder Logs keine Niveaus/Streuungen fuer diese Zeit ausgeben.
- Luecken benennen (`hd.gaps`), nie fuellen oder interpolieren; Selbstheilung wie beim DVOL-Strom (30 Tage Nachholen).
- Neue Stroeme im normalen Archiv-Layout, sichtbar in `hd.catalog()`; Scinance liest nur exakte Schluessel.
- Volumina sind Schaetzungen.

## B-0 (Prioritaet 1, nur Messung): Inventur der `done_days` fuer H-26 (2.0)
- Fuer `deribit/dvol` UND `deribit/publicTrade`, je Symbol (BTC, ETH bzw. BTC-/ETH-PERPETUAL): je Tag seit 2025-08-01,
  ob die Partition aus der LIVE-Sammlung stammt oder per REST nachgeladen wurde, und ob sie als geschlossen (DONE) gilt.
  Daraus: laengste zusammenhaengende Folge von Tagen, an denen BEIDE Stroeme je Symbol live-vollstaendig sind, und das
  Datum, an dem 210 solche Tage erreicht sind oder waeren.
- Zweck: Die 2.0-Hypothese H-26 ist gegen `done_days` des Harvesters vorregistriert; ihre Entsperrung haengt an genau
  dieser Zaehlung. Scinance entscheidet damit die Reihenfolge gegenueber den blinden VRP-Fenstern (DEC-98 E2). Bitte nur
  Zaehlung und Daten liefern, keine Werte.

## B-1 (Prioritaet 1, irreversibel): taeglicher Panel-Strom aller linearen Bybit-Perps (Variante B)
- `bybit/rest.kline1d`: GET /v5/market/kline, category=linear, interval=D, ALLE linearen USDT-Perps (auch spaeter
  delistete bis zu ihrem letzten Handelstag), 1 Zeile je Symbol und Tag.
- `bybit/rest.instruments`: GET /v5/market/instruments-info, category=linear (und inverse), EIN Tagesschnappschuss je
  Tag (status, launchTime, deliveryTime, fundingInterval, upper/lowerFundingRate, deliveryFeeRate). Dieser Schnappschuss
  ist das Point-in-Time-Universum; er ist nicht nachladbar - deshalb irreversibel.
- `bybit/rest.fundingRate` auf ALLE Perps erweitern (je Abrechnung, 1h..8h).
- Zeitraum: Backfill 2026-09-29..heute (Anschluss an den Zip-Export 2026-09-28), dann taeglich laufend.
- Zweck: blinde Fenster fuer die Klasse W (A3-Nachfolger) und A1; Delisting-Register (DEC-72: Delistungen aus dem
  Instruments-Schnappschuss, Stichdatum = letzter Handelstag) - bitte als eigene Tabelle `delisting_dates` mitfuehren;
  Tagesschluss BTC/ETH fuer kuenftige VRP-Fenster. Volumen < 5 MB/Tag.

## B-2 (Prioritaet 2, irreversibel): Quotes der datierten Bybit-Futures (A4)
- (a) Inhaltsprobe des laufenden `bybit/tickers` fuer datierte Kontrakte (LinearFutures USDC, InverseFutures): Sind
  es Snapshots oder nur Deltas? Enthalten sie Bid/Ask-Preis und -Groesse (Feldnamen mit und ohne "1" pruefen),
  markPrice, indexPrice, deliveryTime, basis, openInterest? Kurzer Befund reicht.
- (b) Falls nur Deltas oder ohne Bid/Ask: REST-Schnappschuss GET /v5/market/tickers (category linear UND inverse) alle
  15 Minuten fuer alle datierten BTC/ETH-Kontrakte plus die zugehoerigen Perps, ab sofort laufend.
- (c) GET /v5/market/delivery-price (Settlement-Historie, Backfill so weit verfuegbar) und instruments-info linear+inverse
  taeglich (deliveryFeeRate).
- Zweck: A4 (Perp gegen datierten Future), Nuisance ab 2027-06 messbar. Volumen ~10 MB/Monat.

## B-3 (Prioritaet 3, reversibel, billig): 1-Minuten-Kerzen BTCUSDT/ETHUSDT mit Backfill ab 2021
- `bybit/rest.kline1m`: GET /v5/market/kline, category=linear, interval=1, BTCUSDT und ETHUSDT.
- Zeitraum: Backfill 2021-03-01..heute (zuerst Probe: reicht die 1-Minuten-Historie bei Bybit bis 2021? Falls nicht,
  bitte melden, ab wann), optional ab 2020-03-25; dann taeglich laufend.
- Zweck: Hochfrequenz-Volatilitaet fuer eine kuenftige VRP-Hypothese (Nuisance wird NUR auf 2021-03..2024-05 gerechnet)
  und A2-Nuisance (Vorverfalls-Fenster 07:30-08:00 UTC). Volumen ~0,1-0,3 GB gesamt, ~5.900 REST-Aufrufe.

## B-4 (Prioritaet 4, klein): Deribit-Verfallskalender und Settlement
- `public/get_instruments` (BTC, ETH; future und option; expired=true: expiration_timestamp, settlement_period),
  `public/get_delivery_prices` (btc_usd, eth_usd), `public/get_last_settlements_by_currency`.
- Zeitraum: Backfill so weit verfuegbar (mindestens ab 2020-03-25), dann laufend.
- Zweck: A2 (Verfallskalender als Ereignistakt): Ereignismenge, Settlement-Zeitlage, Placebo-Kalender. Volumen < 10 MB.

## B-5 (Teil von B-2(a), nur Pruefung): Options-Quotes
- Inhaltsprobe `deribit/tickers` (seit 2026-06-16), `deribit/markprice.options`, Bybit-Optionen im `bybit/tickers`-Strom:
  Snapshot oder Delta, best bid/ask, mark_iv, Greeks; eine tagesgenaue Luecken-Karte der Ketten. Kein neuer Strom noetig.
- Zweck: A5 (Skew) und spaeter H-26b; beide gesperrt, nur Vorbereitung.

## Nicht beauftragen
- Binance-Perp-Panel als zweites Universum (bringt fuer A3/A1 praktisch nichts, Bilanz Teil A).
- Getrennter Archiv-Trade-Strom BTC/ETH nur als Ersatzweg, falls 1-Minuten-Kerzen fuer die RV nicht genuegen.

## Rueckmeldung erbeten
Je Auftrag: Stromname im Katalog, Startdatum, Luecken, Befund der Inhaltsproben (B-2a, B-3-Probe, B-5).
