# Auftrag an das Data-Harvest-Projekt: Nachladen der fehlenden delisteten Perps und Register-Angleichung (2026-10-20)

> Bezug: euer Register `scinance_delisting_register_2026-10-20.csv` (angenommen). Kein Hostname, keine Zugangsdaten.
> Ergebnis des Abgleichs (Scinance, nur Symbol- und Datumslisten, keine Marktwerte): von euren 306 delisteten linearen
> USDT-Perps bis 2026-09-28 fehlen **44 vollstaendig** in unserem Panel (weder im Ueberlebenden- noch im Delisted-Baum),
> darunter ~30 mit letztem Handelstag Okt./Nov. 2025 und 5 in 2024-07..2025-06. Unser Register traegt zudem das
> Ankuendigungsdatum statt des letzten Handelstags (259 von 262 gemeinsamen Symbolen weichen um Tage ab).

## Auftrag P-1 (Prioritaet 1): Tageskerzen und Funding aller delisteten linearen USDT-Perps als Backfill
- Fuer JEDES Symbol eures Registers mit `category=linear`, `quoteCoin=USDT` (310 Stand 2026-10-20, kuenftig laufend):
  Tageskerzen (`GET /v5/market/kline`, interval D) und Funding je Abrechnung (`funding/history`) vom `launch_day` bis
  zum `last_trading_day` (Teilkerze am letzten Tag erlaubt), so weit die Bybit-API sie fuer geschlossene Kontrakte
  liefert; liefert die API fuer ein Symbol nichts, bitte als Luecke benennen (Symbolliste), nie fuellen.
- Ablage im selben Layout wie `bybit/rest.kline1d` / `rest.fundingRateAll` (Partition je Tag, `symbol=ALL`), rueckwirkend
  bis 2021-01-01, als eigener Backfill-Lauf mit Abschlussmeldung (Zahl der Symbole, Tage, Luecken). Volumen klein.
- Zweck: vollstaendiges Point-in-Time-Universum fuer die Klasse W (DEC-72: delistete Symbole bis zum letzten Bar halten);
  ohne die 44 Symbole traegt jedes Fenster seit 2024 eine Ueberlebenden-Verzerrung.

## Auftrag P-2: Register als Quelle des letzten Handelstags
- `bybit/delisting_dates` bleibt die bindende Quelle fuer `last_trading_day` (= Kalendertag von deliveryTime - 1 ms).
  Bitte zusaetzlich, falls verfuegbar, `announcement_day` je Symbol (Datum der Delisting-Ankuendigung) als Spalte -
  Scinance fuehrt beide (Ankuendigung als Etikett, letzter Handelstag als Maskenende).
- Sechs Symbole stehen nur in unserem Announcement-Register, nicht in eurem (`DATAUSDT`, `KORUUSDT`, `LITUSDT`,
  `MONUSDT`, `SPCXUSDT`, `ZKUSDT`): bitte pruefen, ob sie unter anderem Namen weiterlaufen, nie delistet wurden oder
  im Instrumenten-Schnappschuss fehlen (status != Closed?).

## Nicht noetig
- Kein neuer Panel-Zip-Export: Scinance baut den Delisted-Baum aus den Backfill-Partitionen selbst und prueft
  Fingerprints. Keine Preis-/Rendite-Statistik in der Abschlussmeldung (Blind-Siegel ab 2026-07-01 fuer BTC/ETH,
  fuer das Panel generell nur Zaehlungen).

## Rueckmeldung erbeten
Abschlussmeldung mit: Zahl der nachgeladenen Symbole, erster/letzter Tag je Symbol (CSV), Symbole ohne API-Daten,
Antwort zu den sechs Symbolen.
