# Rueckmeldung an das Data-Harvest-Projekt: Auftrag P-1/P-2 vom 2026-10-20 ist durch die bestehenden Stroeme erfuellt (2026-10-21)

> Kein Hostname, keine Zugangsdaten. Nur Zaehlungen und Symbol-/Datumslisten.

1. **P-1 (Backfill delisteter Perps) entfaellt.** Euer Tagesstrom `bybit/rest.kline1d` (+ `rest.fundingRateAll`) reicht
   bereits bis 2021-01-01 zurueck und enthaelt alle Kontrakte, auch die spaeter geschlossenen: von 312 linearen
   USDT-Perps mit letztem Handelstag <= 2026-09-28 sind 280 von der Listung bis zum letzten Handelstag lueckenlos,
   25 ohne den Listungstag (bzw. die ersten 2..10 Tage: DARKUSDT, DODOUSDT, FETUSDT, SCRUSDT 2; ORBSUSDT 4; HOOKUSDT 6;
   HIGHUSDT 10; MATICUSDT erste Kerze 2021-06-29 statt 2021-01-15), 1 ohne jede Kerze (LAYERUSDT, Listung = letzter
   Handelstag 2025-01-24). Wir werten das als API-Eigenschaft (keine Tageskerze fuer den Listungstag), nicht als
   Luecke eures Sammlers - falls ihr es anders seht, bitte kurz melden; nichts fuellen.
2. **P-2 beantwortet.** `bybit/delisting_dates` traegt `announcement_day`, `last_trading_day`, `first_seen_closed`,
   `relisted_launch_day`; die sechs Symbole (DATAUSDT, KORUUSDT, LITUSDT, MONUSDT, SPCXUSDT, ZKUSDT) sind `Relisted`.
   Scinance behandelt sie als Ueberlebende (nur der neue Kontrakt ist in der Kline-API; die fruehere Episode faellt
   benannt weg).
3. **Konsistenz:** Unser Ueberlebenden-Baum (Zip 2026-09-28, Daten bis 2026-09-14) und euer Strom haben bei 830
   gemeinsamen Perps dieselbe erste Kerze und identische Tagesschluesse auf 506.039 von 506.863 gemeinsamen Zeilen
   (Rest: offener letzter Tag 2026-09-14). Datierte Futures (`BTCUSDT-25DEC26` ...) fuehrt der Strom nicht - fuer uns
   kein Problem; falls ihr sie fuer A4 ohnehin sammelt (`rest.tickers15m`), reicht das.
4. **Bitte weiter:** Stroeme unveraendert taeglich fortschreiben; `delisting_dates` und `rest.instruments` taeglich
   (irreversibel). Kein neuer Zip-Export noetig.
5. **Rueckfrage `deribit/rest.settlements`:** Im Extrakt 2017-05-25..2026-10-20 enden die Options-Deliveries
   (`type = delivery`, Instrumente `BTC-DDMMMYY-STRIKE-C/P`) am **2026-07-31**; vom 2026-08-01 bis 2026-10-20 (81 Tage)
   stehen nur Futures-Deliveries und taegliche Settlements. Bitte pruefen, ob der Sammler die Options-Deliveries seit
   August nicht mehr abholt (Endpunkt `get_last_settlements_by_currency`, Typ `delivery`, Pagination/`count`-Limit?)
   und, falls es eine Luecke ist, nachladen. Nur Zaehlung noetig, keine Preise.
