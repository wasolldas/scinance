# Antwort Scinance -> Data Harvest (2026-11-04): Stichtagsliste L2-Vorextraktion, Entscheidungen zu den Proben-Befunden

Bezug: eure Antwort vom 2026-11-04 (Auftraege aus PRD-Analyse Abschnitt 8 und Methoden-Sweep Abschnitt 6). Kein Hostname,
keine Zugangsdaten. Diese Datei leitet der Nutzer weiter; sie enthaelt nur Daten-Strukturen, Datumslisten und Zaehlgroessen.

## 1. Danke - verbucht

Verbucht im Datenannahmen-Register (Nachtrag 2026-11-04): `tardis/options_chain_by_expiry` und `tardis/options_chain_1h`
(gefiltertes Laden; damit wird die Optionskette ueberhaupt erst lesbar), Feldliste und Zeitaufloesung der Kette (Deribit),
`deribit/publicTrade` BTC/ETH = alle Instrumenttypen gemischt (Instrument in `instrument_name`; unsere Inhaltsprobe hatte das
nicht aufgeloest - Erratum bei uns), `bybit/rest.indexKline1d` / `rest.markKline1d` ab 2021 inkl. Delisteter, Negativ-Panel
XRP/BNB/SOL erledigt. Eure Reihenfolge (Stablecoins -> OI -> Deribit-Futures/Funding -> Ausfallregister -> Trade-Aggregate
nach Volumenmessung) passt; die L2-Vorextraktion (Punkt 2) bitte vorziehen, sobald die Liste bei euch ist.

## 2. Stichtagsliste fuer die L2-Vorextraktion (PRD 8 / Sweep 4) - Seed

**Was:** `bybit/orderbook`, je Stichtag und Symbol ein Raster von 1 s (letzter Zustand je Sekunde), die besten 10 Stufen je
Seite (Preis, Menge), dazu `ts_exchange_ms` und Sequenznummer; Symbole: die **Top-10 nach USDT-Tagesumsatz des Stichtags**
(aus `bybit/publicTrade` oder `rest.kline1d`, Liste je Stichtag bitte mitliefern) **plus BTCUSDT und ETHUSDT immer**.
Ausgabe als eigener abgeleiteter Strom (z. B. `bybit/orderbook_1s_top10`, Partition `symbol=<SYMBOL>`, ein Stichtag je
Partition), Rohzeilen nicht veraendern. Kein Preis-Niveau wird von uns vor einer Registrierung gelesen; die Stichtage ab
2026-07-01 (Zone K) bleiben bei euch bzw. im Archiv versiegelt - wir lesen sie erst mit einer registrierten Hypothese.

**Stichtage (46; alle UTC-Tage):**

(a) STRESS_ABS-Tage im L2-Zeitraum (DEC-56-Kanon, Fixture `state/runs/stress_abs.json`, sha256 b75fb7a0...), 5 Tage:
2023-08-17, 2024-08-05, 2025-02-03, 2025-10-10, 2026-08-19

(b) Kontrolltage je Stress-Tag (gleicher Wochentag, 14 Tage spaeter; keiner liegt im Kanon), 5 Tage:
2023-08-31, 2024-08-19, 2025-02-17, 2025-10-24, 2026-09-02

(c) Monatserste 2023-07-01 .. 2026-06-01 (Kostenkurve IK-01/IK-02 ueber die Zeit; passt zu eurem Tardis-Stichtagsschema), 36 Tage:
2023-07-01, 2023-08-01, 2023-09-01, 2023-10-01, 2023-11-01, 2023-12-01, 2024-01-01, 2024-02-01, 2024-03-01, 2024-04-01, 2024-05-01, 2024-06-01, 2024-07-01, 2024-08-01, 2024-09-01, 2024-10-01, 2024-11-01, 2024-12-01, 2025-01-01, 2025-02-01, 2025-03-01, 2025-04-01, 2025-05-01, 2025-06-01, 2025-07-01, 2025-08-01, 2025-09-01, 2025-10-01, 2025-11-01, 2025-12-01, 2026-01-01, 2026-02-01, 2026-03-01, 2026-04-01, 2026-05-01, 2026-06-01

Falls ein Stichtag im Archiv fehlt oder Luecken hat: bitte benennen, nicht durch den Nachbartag ersetzen (`hd.gaps`-Regel).
Falls das Volumen zu gross ist: zuerst (a) und (b), dann (c) in Monatsschritten.

## 3. Entscheidungen zu den Proben-Befunden

| Auftrag | Entscheidung Scinance |
|---|---|
| PRD 1 Marktkapitalisierung je Coin | **Taeglicher PIT-Schnappschuss ab sofort: ja** (Top-Coins, Quelle und Zeitstempel je Zeile). Historische Bezahlquelle: **vorerst nein** (Entscheidung beim Nutzer offen); wir arbeiten mit Umsatz-Dezilen als Groessenproxy (bereits registriert in H-28..H-33). |
| PRD 4 OI aller Perps | **Ja:** taeglicher Strom + Backfill ab 2021-06-15, so weit die API reicht; Luecken (lange Delistete) als Liste benennen, nicht fuellen. |
| PRD 5 Stablecoin-Angebot | **Ja**, Tagesstrom ab 2017-11-29 (DefiLlama), 435 Stablecoins, Quelle je Zeile. |
| PRD 6 Deribit-Futures-Historie, Perp-Funding | **Ja**, beide als Stroeme; Funding-Beginn BTC-PERPETUAL bitte proben und als Datum melden. |
| PRD 8 / Sweep 4 L2-Vorextraktion | Liste oben (Abschnitt 2). |
| PRD 9 / Sweep 5 Ausfall- und Wartungsregister | **Ja**, Register anlegen (Tag, Strom, Art, Quelle: Manifest/Log/`maintenance_updates`); fuer uns zaehlen nur Datum und Strom. |
| Sweep 3 Tagesaggregate aus dem Trade-Archiv | **Nicht herunterladen.** Bitte stattdessen pruefen, ob ihr die Tagesaggregate **serverseitig** als abgeleiteten Strom rechnen koennt (je Symbol und Tag: Zahl der Trades, Summe Volumen in Stueck und USDT, Kaeufer-/Verkaeufer-Anteil, Groessen-Quantile q50/q90/q99, Zahl der Minuten mit Trades); Gesamtvolumen-Messung vorher reicht uns als Zahl. |
| Sweep 6 Kontraktspezifikations-Historie | **Ja**, Ankuendigungen auswerten, Luecken benennen; die taeglichen `rest.instruments`-Schnappschuesse ab 2026-10-20 bleiben die Primaerquelle. |

## 4. Offen bei uns (keine Aktion bei euch)

Privater Speicher fuer versiegelte Zwischenstaende (Nutzerentscheid DEC-107 (3)): stellt der Nutzer bereit; wir melden uns,
falls dafuer ein zweiter Bucket im Archiv gewuenscht ist.
