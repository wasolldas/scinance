# Herleitungs-Auftrag P-2: Programm-Bilanz als Power-Zensus - wo ist auf unserem Bestand Power 0,80 erreichbar?

Du bist der Herleitungs-Agent (Power, Rauschboden, Gate-Design) im Forschungsprogramm Scinance 3.0. Der Orchestrator
entscheidet, nicht du; der Nutzer entscheidet die Programmrichtung (PRD Par. 8). Repo `/home/user/scinance`, Python
mit `PYTHONPATH=/home/user/scinance/src`. Eigene Skripte nur unter
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/bilanz/` (anlegen). Volltext nach
`scinance3-impl/state/PROGRAMM_BILANZ_2026-10-18.md` plus `scinance3-impl/state/programm_bilanz.json` (anlegen).
An den Orchestrator nur eine Kurzfassung (hoechstens 10 Zeilen). Nichts committen, nichts pushen.

## Anlass
Drei Kandidaten sind nacheinander VOR dem Lauf an der Power gescheitert, nicht an Daten oder Code:
A3 (GL-032: Roh-IC, SD(IC_t) unter stress 0,13/0,08 gegen Boden 0,049, Prior 0,03), A1 (GL-033: Funding-Long-Bein,
theta UNBELEGT, unter DEC-67 E4 selbst bei theta = 1 GL-012), H-27 (GL-034: VRP, c ~ 28 durch ueberlappende 30-Tage-
Ziele, Prior 9,47 VP, L = 12 Monate Power 0,575). A2 (V-5c), A4 (Recording-first) und A5 (E.6) sind gesperrt.
Die Frage des Nutzers: Was wissen wir, was nicht, warum nicht, was brauchen wir? Diese Bilanz liefert den
quantitativen Kern: **fuer jede Klasse und jeden Kandidaten, bei welcher Datenlage (Dauer, Einheiten, Quelle) waere
unter der geltenden Power-Konvention (DEC-51, DEC-94) ueberhaupt Power 0,80 erreichbar - und wann.**

## Pflichtlektuere
- `scinance3-impl/CLAUDE.md`, `scinance3-impl/UEBERGABE_2026-10-12.md` (alle Nachtraege), `scinance3-impl/PRD_SCINANCE3.md`
  (Abschnitte 3.3, 4, 5.1-5.5, 8, 9.2), `state/decisions.md` DEC-51/52/58/59/61/67/70/73/87/91-97,
  `state/gate_log.md` GL-032..034, `state/WELLE1_GESAMTBILANZ_2026-09-21.md`.
- Akten mit Nuisance-Zahlen (NUR diese Zahlen benutzen, nichts neu auf Outcome-Daten rechnen):
  `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json` (A3: factor_sd je Methode/Kalibrierung/Fenster, e_floor,
  w_judged - NICHT die Siegeldateien), `state/herleitung_a1/feasibility.json` + `FEASIBILITY.md`,
  `state/herleitung_h27/feasibility.json` + `FEASIBILITY.md` + `REVIEW_H27.md`,
  `state/runs/wp7_20260921/wp7_report.json` (K je Woche, SD_null, N_eff, sigma_LS), `state/runs/v1x_20261012/`.
- Code: `src/bybit_edge/research/power_p1.py` (PFLICHT fuer jede Power-/MDE-/Zuordnungszahl).
- Datenbestand: Katalog-Uebersicht steht unten (Stand 2026-10-17); 2.0-Akte `scinance2-impl/state/PROGRAM_FINAL_REPORT.md`
  nur fuer die Einordnung (Mikrostruktur-Klassen sind dort erledigt: an der Friktionswand gescheitert).

## Harte Regeln
1. **Keine Outcome-Rechnung.** Nur Nuisance-Groessen aus den Akten (SD, c, Boden, K, Prior aus Literatur). Keine
   Siegeldatei (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`), keine WP-10(A2)-IV-RV-
   Dateien, kein Panel-/DVOL-/Trade-Laden fuer neue Statistiken. Blind-Siegel DEC-96 E3 (ab 2026-07-01) gilt.
2. Jede Zahl mit Herleitung oder Quelle; `[sek]` fuer Sekundaerbelege; Fehlendes heisst UNBELEGT.
3. Keine Empfehlung, die eine Regel zugunsten eines bestimmten Kandidaten lockert (Torpfosten). Regelaenderungen nur
   als programmweite Option mit ehrlicher Falsch-Positiv-Rate ausweisen (wie DEC-94). Richtung jeder Option
   (Testbarkeit/Strenge) benennen.
4. Keine Zugangsdaten, keine Hostnamen, keine Modellnamen in Dateien. Doku Deutsch (ASCII-safe), Code Englisch.

## Bestand (Harvest-Katalog 2026-10-17, vom Orchestrator gelesen; nur exakte Schluessel, kein Listing)
| exchange/stream | Symbole | von | bis | Bemerkung |
|---|---|---|---|---|
| bybit/publicTrade | 5 (BNB/BTC/ETH/SOL/XRP) | 2020-03-25 | laufend | Trades, ~75 MB/Tag/Symbol |
| bybit/orderbook | 5 | 2023-01-18 | laufend | L2 |
| bybit/rest.fundingRate, rest.openInterest | 5 | 2024-03-01 | laufend | |
| bybit/tickers | 11.925 Symbole (inkl. ~8.600 datierte Futures/Optionen) | 2026-06-16 | laufend | A4-Quote-Aufzeichnung laeuft seit 2026-06-16 |
| bybit/allLiquidation, insurance | 5 / 1 | 2026-06-16 | laufend | |
| deribit/dvol | BTC, ETH | 2021-03-24 | laufend | lueckenlos |
| deribit/publicTrade | 4 | 2025-08-01 | laufend | |
| deribit/markprice.options, orderbook | 2 | 2026-06-16 | laufend | |
| deribit/tickers | 14.810 | 2026-06-16 | laufend | |
| binance/publicTrade | 5 | 2025-01-01 | laufend | plus orderbook, funding, OI |
| tardis/options_chain | 1 | 2026-05-01 | 2026-08-01 | Probe |
| Panel `panel_1d` + `_delisted` (Zip-Export) | 1.138 Perps | 2021 | 2026-09-28 | Tageskerzen + Funding; taeglicher Strom (Variante B) bei Data-Harvest vorgemerkt |
Data-Harvest kann Datenaenderungen jetzt selbststaendig umsetzen (Nutzer 2026-10-18) - formuliere den Datenbedarf
so, dass er direkt als Auftrag taugt (Strom, Symbole, Aufloesung, Zeitraum, Zweck, Prioritaet).

## Aufgabe
### Teil A - Power-Zensus je Kandidat (Tabelle + JSON), alles mit `power_p1`
Fuer A3 (mom1, rev_gap; measured UND stress), A1 (theta-Gitter 0,5/0,77/1,0; c = 1 und DEC-67 E4), H-27 (Prior 9,47,
Band 7,0/13,7; c 28,2 und Konsens 18,6; RV Tagesschluss und HF-RV UNBELEGT 15,1), A2 (Ereignisdesign: N Verfaelle,
sigma_w UNGEMESSEN -> nur Formel und was gemessen werden muesste), A4 (8 Quartalszyklen je 2 Jahre, sigma_w UNGEMESSEN,
Quote-Aufzeichnung seit 2026-06-16), A5 (gesperrt, E.6 - nur Bedingungen auflisten), H-26 (2.0, 210 done_days, nur Status):
1. **Benoetigte Dauer je Fenster** fuer Fenster-Power 0,80 (C.10) und fuer den DEC-52-Zweig (Produkt-Gate 0,80) beim
   Literatur-Prior - in Wochen/Monaten; dazu das Datum, an dem zwei blinde Fenster ab dem fruehestmoeglichen blinden
   Start (A3/A1: Panel-Strom ab Verfuegbarkeit, fruehestens 2026-10; H-27: 2026-07-01; A4: 2026-06-16 + 12 Monate
   Aufzeichnung) voll waeren. Zeige die Formel (`W = (z_mde * SD_eff / prior)^2` je Bedingung) und die Sensitivitaet
   gegenueber dem Prior (Band).
2. **Benoetigte Einheiten** statt Dauer, wo das Design es erlaubt: mehr Symbole (A3: hilft nicht, wenn faktorbedingte
   Streuung dominiert - zeigen), mehr Boersen (Binance-Panel? nur als Option mit Datenbedarf), mehr Underlyings (VRP
   auf BTC+ETH als ein Bein nach DEC-62 E3: Korrelation ~0,9 -> kaum Gewinn, rechnen), mehr Ereignisse (A2/A4).
3. **Welcher Hebel wirkt wo:** laengere Zeit, HF-Statistiken (VRP: HF-RV; A3: nichts), Design mit weniger Autokorrelation
   (H-27: nicht ueberlappende Monatsziele - Power vergleichen), kleinere Nuisance durch Hedge/Neutralisierung (A3:
   fm_neutral_8w als Primaerstatistik = NEUE Hypothese nach DEC-92; nur als Option mit DEC-58-E2-Vorbehalt).
4. **Doppelausweis:** jede Zahl unter P-1 (DEC-94) und unter der A3-Praxis (`assign_regime_a3_practice`).

### Teil B - Datenbedarf (als Auftragsliste fuer Data-Harvest, priorisiert)
Je Zeile: Strom/Quelle, Symbole, Aufloesung, Zeitraum (Backfill und/oder laufend), welcher Kandidat/welche Frage,
was es an Power bringt (Zahl aus Teil A oder "UNBELEGT, Messung noetig"), Prioritaet, grobes Volumen. Kandidaten:
taeglicher Panel-Strom aller Perps (Variante B), getrennter Archiv-Trade-Strom oder 1-Minuten-Kerzen BTC/ETH fuer
HF-RV (Backfill ab 2021 fuer die Nuisance!), A4-Quotes datierter Futures (laeuft - pruefen, ob Tiefe/Spread dabei),
Deribit-Verfallskalender/Settlement-Zeitreihen fuer A2 (V-5b/c), Options-Quotes fuer A5/H-26b, Binance-Perp-Panel als
zweites Universum (nur falls Teil A zeigt, dass es hilft).

### Teil C - Entscheidungsvorlage fuer den Nutzer (PRD Par. 8), neutral, jede Option mit Richtung und Kosten
Mindestens: (1) Recording-first-Programm: blinde Aufzeichnung mit vorab fixierten Entsperrdaten je Kandidat (aus Teil A),
bis dahin nur Zensus/Infrastruktur; (2) Ereignis-/Einheiten-Designs vorziehen (A2 nach V-5b/c, A4 nach 12 Monaten);
(3) HF-Daten-Weg fuer die VRP (Datenbedarf, UNBELEGT-Status, wann belegbar); (4) programmweite Regelaenderung
(z. B. Power-Ziel oder Fensterzahl) - mit Falsch-Positiv-Rate und dem Etikett, das sie tragen muesste (DEC-94-Muster;
nicht empfehlen, nur ausweisen); (5) Pause/Abschluss 3.0 mit Bilanz. Was NICHT folgt: kein Verdikt ueber Momentum,
Carry oder VRP.

## Rueckmeldung
Hoechstens 10 Zeilen: die drei wichtigsten Dauer-/Datums-Zahlen, welcher Hebel wo wirkt, Top-3 des Datenbedarfs,
Dateiliste, UNBELEGT-Punkte.
