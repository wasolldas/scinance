# A2-Ereigniszensus (EXP-CLOCK): Deribit-Verfallskalender und Zeitlage - NUR KALENDER UND ZEITSTEMPEL

> ENTWURF der Herleitung (Nuisance/Zensus), Stand 2026-10-21. Nichts hier ist registriert oder beschlossen; entscheiden
> darf nur der Orchestrator. A2 bleibt durch V-5b gesperrt (Effektgroesse); dieser Zensus liefert nur den Datenteil
> von V-5a (Kalender) und V-5c (Zeitlage) sowie die Placebo-Mengen.
> **Etikett:** "A2-Ereigniszensus: nur Kalender und Zeitlage (Zeitstempel) der Deribit-Settlements/-Deliveries und
> Datumsliste der deliveryPrices; keine Preise, Renditen oder Volatilitaeten (nicht im Extrakt)." Die Extrakte
> enthalten keine Preisspalten (Assert auf die Spaltenmenge in `a2_census.py`). Blind-Siegel DEC-96 E3: Kalender und
> Zeitstempel ab 2026-07-01 sind als Vollstaendigkeits-/Zeitstempelangaben zulaessig; keine Niveau- oder
> Streuungsgroesse wurde berechnet.
> **Kuerzel:** `[aj:<pfad>]` = `a2_census.json` (gleicher Ordner); `[S:a2_census.py]` unter `scratchpad/hfrv_herleitung/`
> (sha256 in [aj:skript_sha256]); `[abg.]` hier abgeleitet; `[sek]` Sekundaerbeleg.

## 0. Befund in Kuerze

1. **Kalender (V-5a, aus den Daten geprueft):** Verfall immer 08:00 UTC; Klassen nach Kalender: quartalsweise = letzter
   Freitag Maerz/Juni/September/Dezember, monatlich = letzter Freitag der uebrigen Monate, woechentlich = uebrige
   Freitage, taeglich = Nicht-Freitage. Pruefung 2018-01..2026-09: in jedem Monat liegt ein Verfall auf dem letzten
   Freitag, und wo Futures im Monat verfallen, ist der letzte Freitag darunter - **keine Feiertagsverschiebung**
   [aj:last_friday_check_2018_01..2026_09].
2. **Seit wann:** BTC-Optionen monatlich ab 2017-05-26 (Beginn des Kalenders), quartalsweise ab 2017-06-30,
   **woechentlich ab 2017-09-01, jeder Freitag lueckenlos ab 2017-08-25**; **taeglich ab 2020-02-04, jeder Kalendertag
   lueckenlos seither** (auch Samstag/Sonntag). ETH-Optionen: Kalender ab 2019-03-29, jeder Freitag ab 2019-03-29,
   taeglich ab 2020-02-18. Futures: woechentlich (jeder Freitag) ab 2021-02-19 (BTC) / 2021-03-12 (ETH); taegliche
   Futures ab 2026-04-04 (BTC) bzw. lueckenlos ab 2026-05-20 (ETH) [aj:first_expiry_by_class, aj:continuity_within_coverage].
3. **Ereignisse 2020-03-25..2026-06-30 (BTC und ETH haben an jedem Verfallsdatum beide Verfaelle; gepoolt = je
   Waehrung):** 251 Wochen-ohne-Monatsverfaelle, 76 Monatsverfaelle (davon 26 Quartale, 50 ohne Quartal), 1.962
   Tagesverfaelle - **jeder Kalendertag ist ein Verfallstag**. Je Jahr ab 2021: 40-41 Wochen, 12 Monat (8 + 4 Quartal),
   312-314 Tage [aj:event_counts.pooled].
4. **Teilperioden:** Vorperiode 2020-03-25..2024-05-31: 168 Wochen / 51 Monat (34 + 17 Q) / 1.310 Tage; W1 2024-07..
   2025-06: 40 / 12 (8 + 4) / 313; W2 2025-07..2026-06: 40 / 12 (8 + 4) / 313 (bis 2026-06-28 nach DEC-99: 311 Tage);
   blind ab 2026-07-01 (bis 2026-10-20): 13 / 3 (2 + 1) / 96 - aber Optionsdaten nur bis 2026-07-31 (Punkt 6).
5. **Zeitlage (V-5c, Datenteil):** Delivery-Zeitstempel Optionen 177.049 Zeilen: Median 0,040 s nach 08:00:00 UTC, 99 %
   innerhalb 0,50 s, keiner vor 08:00; Datum des Zeitstempels = Verfallsdatum aus dem Namen in 177.999/177.999
   Deliveries. Ausreisser (> 60 s) nur an vier Tagen: 2018-05-04 (+62 min), 2020-08-27 (+78 min), 2024-08-19 (+60 min),
   2026-07-15 (+39 min). Taegliche Settlements (Perpetual/Futures) ebenso 08:00 UTC (Median 0,04 s). Stabil seit 2021
   (Jahres-Median 0,01..0,07 s; 2017 noch 4..6 s) [aj:timing_seconds_after_0800_utc].
6. **Datenluecke (benannt, nicht gefuellt):** Options-Deliveries enden im Extrakt am **2026-07-31**; 2026-08-01..10-20
   (81 Tage) nur Futures-Deliveries und taegliche Settlements [aj:option_delivery_coverage_gap]. Fuer A2-Rechnungen vor
   2026-07 ohne Belang; als Rueckfrage an Data-Harvest (Stream `deribit/rest.settlements` ab 2026-08).
7. **Placebo:** Seit 2020-03-25 gibt es **keinen verfallsfreien Tag** (0 Freitage, 0 Mo-Do ohne Delivery). Placebo-Mengen
   koennen nur "Freitage mit nur Wochenverfall" (Vorperiode 168, W1 40, W2 40) oder "Tage mit nur Tagesverfall"
   (Mo-Do: 874 / 209 / 209; Wochenende 436 / 104 / 104) sein - nie "kein Verfall" im Slot 07:30-08:00 [aj:placebo_calendar].
8. **deliveryPrices:** btc_usd 2016-03-18..2020-01-31 nur Freitage (woechentlich; 2017-05-26..08-25 nur Monatsabstaende
   35/28/28 Tage), taeglich lueckenlos ab 2020-02-04; eth_usd Freitage ab 2019-03-29, taeglich ab 2020-02-18. Die Daten
   decken sich exakt mit den Delivery-Daten des Settlement-Kalenders (0 Abweichungen) [aj:deliveryPrices_dates].

---

## 1. Daten (B-1) [aj:rows, aj:rows_by_ccy_type, aj:kinds_by_type, aj:schema]

| Stueck | Befund |
|---|---|
| Download-Log | `ALLDONE deribit {"settlements": [], "deliveryPrices": []}` - keine fehlenden Monate |
| Settlement-Kalender | 217.728 Zeilen, Spalten `column_symbol, instrument_name, type, timestamp_ms` (keine Preisspalte); BTC 111.316 (ab 2017-05-25), ETH 106.412 (ab 2019-03-15), bis 2026-10-20 |
| Typen | delivery 177.999 (Futures 950, Optionen 177.049), settlement 39.729 (Futures taeglich 33.963, Perpetual 5.766); keine anderen Instrumentnamen, 0 Zeitstempel = 0, 0 exakte Duplikate, kein Instrument zweimal geliefert, kein Perpetual-"delivery" |
| Abweichung vom Auftragstext | `column_symbol` traegt den Instrumentnamen (= `instrument_name` in allen Zeilen), nicht die Waehrung; die Waehrung wird aus dem Namenspraefix gelesen [aj:column_symbol_eq_instrument_name] |
| Taegliche Settlement-Zeilen | an jedem Tag vorhanden: BTC 3.436 Tage (2017-05-25..2026-10-20), ETH 2.777 Tage (2019-03-15..) - keine Luecke [aj:settlement_row_day_gaps] |
| deliveryPrices | 5.128 Zeilen, nur `index_name` und `date`; btc_usd 2.644 Daten, eth_usd 2.484; keine Duplikate |

**Vorab fixierte Regeln (C-1..C-6, Docstring von `a2_census.py`):** Typ aus dem Namen (Perpetual `CCY-PERPETUAL`, Future
`CCY-DDMMMYY`, Option `CCY-DDMMMYY-STRIKE-C|P`); Verfallsdatum aus dem Namen; Ereignis = Verfallsdatum (BTC und ETH am
selben Datum = ein Cluster, DEC-67); Kalenderklasse wie Befund 1 (gegen die Daten geprueft, nicht angenommen);
Perioden wie Abschnitt 3; Zeitlage = Sekunden nach 08:00:00 UTC des eigenen UTC-Tages, Ausreisser |dt| > 60 s.

## 2. Verfallskalender je Instrumenttyp (B-1)

**Wochentage und Abstaende** [aj:expiry_dates_by_kind]

| Typ | Verfallsdaten | Zeitraum | Wochentage | Abstaende aufeinanderfolgender Verfaelle (Tage: Anzahl) | Klassen |
|---|---:|---|---|---|---|
| Optionen | 2.501 | 2017-05-26..2026-07-31 | Fr 470; Mo/Sa/So je 338; Di/Mi/Do je 339 | 1: 2.369; 7: 127; 28: 2; 35: 1; 4: 1 | taeglich 2.031, woechentlich 359, monatlich 74, quartalsweise 37 |
| Futures | 495 | 2017-05-26..2026-10-20 | Fr 323; uebrige je 28-29 | 7: 267; 1: 200; 91: 8; 28: 10; 35: 6; 14, 56, 77: je 1 | taeglich 172 (nur 2026), woechentlich 229, monatlich 56, quartalsweise 38 |

**Erstes Auftreten je Klasse** [aj:first_expiry_by_class] und **Lueckenlosigkeit** [aj:continuity_within_coverage]

| | Optionen BTC | Optionen ETH | Futures BTC | Futures ETH |
|---|---|---|---|---|
| quartalsweise | 2017-06-30 | 2019-03-29 | 2017-06-30 | 2019-03-29 |
| monatlich | 2017-05-26 | 2019-04-26 | 2017-05-26 (2019-2020 keine Monatsfutures) | 2021-04-30 |
| woechentlich | 2017-09-01; jeder Freitag ab 2017-08-25 | 2019-04-05; jeder Freitag ab 2019-03-29 | 2019-03-15 (einzeln); jeder Freitag ab 2021-02-19 | 2021-03-12; jeder Freitag ab 2021-03-12 |
| taeglich | 2020-02-04; jeder Tag seither (bis Datenende 2026-07-31) | 2020-02-18; jeder Tag seither | 2026-04-04; jeder Tag ab 2026-04-03 | lueckenlos ab 2026-05-20 |

- **V-5a beantwortet (Datenteil):** Wochenverfaelle (Optionen) seit 2017-09-01, lueckenlos jeden Freitag; Tagesverfaelle
  seit 2020-02-04 (BTC) / 2020-02-18 (ETH). Das bestaetigt den Sekundaerbeleg "Tagesverfaelle BTC ab 2020-02-04" (DEC-98
  Nachtraege 1/2) und schliesst den dort offenen Punkt "Beginn der Wochenverfaelle UNBELEGT" fuer den Kalender (nicht
  fuer die Settlement-Regel 6-s/4-s-Takt).
- **Instrumente je Verfallsdatum (2020-03-25..2026-06-30; Optionen je Waehrung, Quantile q05 / q50 / q95)**
  [aj:instruments_per_expiry_date_quantiles_2020-03-25..2026-06-30]:

| Klasse | n Daten | BTC-Optionen | ETH-Optionen | Futures je Waehrung |
|---|---:|---|---|---|
| taeglich | 1.962 | 15 / 28 / 53 (min 10, max 95) | 14 / 30 / 62 (min 10, max 100) | 0 (taegliche Futures erst ab 2026-04) |
| woechentlich | 251 | 36 / 58 / 91 (min 26) | 29 / 50 / 85 (min 20) | meist 1 (ab 2021) |
| monatlich | 50 | 49 / 77 / 130 | 44 / 66 / 98 | meist 1 (ab 2021) |
| quartalsweise | 26 | 61 / 92 / 148 | 62 / 94 / 127 | immer 1 |

## 3. Ereigniszahlen je Periode und Jahr (B-1) [aj:event_counts]

Gezaehlt sind Verfallsdaten mit mindestens einer Futures- oder Options-Delivery. BTC, ETH, gepoolt und "BTC und ETH am
selben Datum" sind seit 2020-03-25 in jeder Zelle identisch (jeder Verfallstag hat beide Waehrungen); Cluster je Datum
= 1 (DEC-67).

| Periode | Woche ohne Monat | Monat inkl. Quartal | Monat ohne Quartal | Quartal | Tag (Nicht-Freitag) | alle |
|---|---:|---:|---:|---:|---:|---:|
| gesamt 2020-03-25..2026-06-30 | 251 | 76 | 50 | 26 | 1.962 | 2.289 |
| Vorperiode 2020-03-25..2024-05-31 | 168 | 51 | 34 | 17 | 1.310 | 1.529 |
| W1 2024-07-01..2025-06-30 | 40 | 12 | 8 | 4 | 313 | 365 |
| W2 2025-07-01..2026-06-30 | 40 | 12 | 8 | 4 | 313 | 365 |
| W2 nach DEC-99 (bis 2026-06-28) | 40 | 12 | 8 | 4 | 311 | 363 |
| W gesamt 2024-07-01..2026-06-30 | 80 | 24 | 16 | 8 | 626 | 730 |
| blind 2026-07-01..2026-10-20 (Kalender; Optionen nur bis 07-31) | 13 | 3 | 2 | 1 | 96 | 112 |

| Jahr | Woche ohne Monat | Monat inkl. Q | davon Q | Tag | alle |
|---|---:|---:|---:|---:|---:|
| 2020 (ab 03-25) | 30 | 10 | 4 | 242 | 282 |
| 2021 | 41 | 12 | 4 | 312 | 365 |
| 2022 | 40 | 12 | 4 | 313 | 365 |
| 2023 | 40 | 12 | 4 | 313 | 365 |
| 2024 | 40 | 12 | 4 | 314 | 366 |
| 2025 | 40 | 12 | 4 | 313 | 365 |
| 2026 (bis 10-20) | 33 | 9 | 3 | 251 | 293 |

Nur Futures-Verfaelle (Bericht): Vorperiode 132 Wochen / 44 Monat (27 + 17 Q) / 0 Tage; W1 40 / 12 / 0; W2 40 / 12 / 76
(taegliche Futures ab April 2026) [aj:event_counts.pooled_future_only]. Die Grenze 2026-06-28 von DEC-99 verschiebt nur
zwei Tagesverfaelle (06-29, 06-30).

Die Bilanz-Arbeitswerte (PROGRAMM_BILANZ 2.4: 52 Wochen-, 12 Monatsverfaelle je Jahr) sind bestaetigt: 52 Freitage je
Jahr, davon 40 Wochen- und 12 Monats-/Quartalsverfaelle.

## 4. Zeitlage (B-2) [aj:timing_seconds_after_0800_utc, aj:delivery_ts_date_eq_name_date]

| Typ | Zeilen | q01 / q50 / q99 (s nach 08:00:00 UTC) | max | Zeilen > 5 s | vor 08:00 | Ausreisser-Tage (> 60 s: Zeilen, max) |
|---|---:|---|---:|---:|---:|---|
| delivery Optionen | 177.049 | 0,007 / 0,040 / 0,50 | 4.718 | 1.020 | 0 | 2018-05-04 (2, +3.720 s); 2020-08-27 (50, +4.718 s); 2024-08-19 (34, +3.600 s); 2026-07-15 (32, +2.358 s) |
| delivery Futures | 950 | 0,007 / 0,054 / 3,49 | 2.358 | 7 | 0 | 2019-03-15 (1, +960 s); 2026-07-15 (1, +2.358 s) |
| settlement Futures (taeglich) | 33.963 | 0,006 / 0,042 / 6,04 | 10.649 | 387 | 0 | 2017-05-25 (2, +4.489 s); 2017-11-09 (2, +10.649 s); 2017-12-11 (2, +907 s); 2019-03-15 (15, +900 s); 2020-08-27 (6); 2024-08-19 (6); 2026-07-15 (10) |
| settlement Perpetual | 5.766 | 0,007 / 0,043 / 0,49 | 4.718 | 4 | 0 | 2020-08-27 (2); 2024-08-19 (1); 2026-07-15 (1) |

**Stabilitaet ueber die Jahre (Optionen-Delivery, Median / q99 in s):** 2017 5,8 / 11,7; 2018 0,14 / 19,1; 2019 0,20 /
0,41; 2020 0,10 / 0,53; 2021 0,011 / 0,059; 2022 0,044 / 0,12; 2023 0,028 / 0,085; 2024 0,043 / 0,15; 2025 0,041 /
0,11; 2026 0,067 / 0,22. Stunde des Zeitstempels: 08 h in 176.963, 09 h in 86 Zeilen (nur die Ausreisser-Tage).

- **Datum des Zeitstempels = Verfallsdatum aus dem Namen:** 177.999 von 177.999 Deliveries; kein Verfall am Vortag oder
  Folgetag.
- **Lesart:** Der Zeitstempel ist der Buchungszeitpunkt des Settlements unmittelbar nach dem Ende des Mittelungsfensters;
  er belegt die 08:00-UTC-Lage, nicht selbst die Fensterlaenge 07:30-08:00 (TWAP-Regel primaer belegt in DEC-98
  Nachtrag 2). An den vier Ausreisser-Tagen wurde spaeter gebucht; ob dort auch der Mittelungszeitraum abwich, zeigt der
  Kalender nicht (Merkposten fuer jede A2-Ereignisliste: diese Tage markieren oder vorab ausschliessen, Regel vor jeder
  Zahl).

## 5. Placebo-Kalender (B-3) [aj:placebo_calendar]

| Periode | Freitage | davon Woche / Monat / Quartal | Freitage ohne Delivery | Mo-Do | Mo-Do ohne Delivery | Wochenendtage (alle mit Delivery) |
|---|---:|---|---:|---:|---:|---:|
| gesamt 2020-03-25..2026-06-30 | 327 | 251 / 50 / 26 | 0 | 1.308 | 0 | 654 |
| Vorperiode 2020-03-25..2024-05-31 | 219 | 168 / 34 / 17 | 0 | 874 | 0 | 436 |
| W1 2024-07-01..2025-06-30 | 52 | 40 / 8 / 4 | 0 | 209 | 0 | 104 |
| W2 2025-07-01..2026-06-30 | 52 | 40 / 8 / 4 | 0 | 209 | 0 | 104 |
| W2 nach DEC-99 (bis 06-28) | 52 | 40 / 8 / 4 | 0 | 207 | 0 | 104 |
| blind 2026-07-01..2026-10-20 | 16 | 13 / 2 / 1 | 0 | 64 | 0 | 32 |

**Folge fuer V-5c/A2 (nur Kalender, keine Empfehlung eines Designs):** Ein "verfallsfreier" Placebo-Slot 07:30-08:00 UTC
existiert seit 2020-02 nicht mehr; jeder Tag hat einen Tagesverfall mit 10..100 Optionen je Waehrung. Ein
Placebo-Kontrast misst daher "grosser gegen kleiner Verfall" (Monat gegen Woche, Woche gegen Tag), oder er braucht
einen anderen Uhrzeit-Slot am selben Tag (z. B. 06:30-07:00 UTC, Bericht). Diese Wahl ist vor jeder sigma30-Zahl zu
fixieren.

## 6. deliveryPrices-Datumsreihe (B-3) [aj:deliveryPrices_dates]

| Index | Daten | erstes / letztes Datum | woechentlich (nur Freitage) | taeglich lueckenlos ab | Luecken (Abstand nicht 1 oder 7 Tage) |
|---|---:|---|---|---|---|
| btc_usd | 2.644 | 2016-03-18 / 2026-10-20 | 2016: 42, 2017: 42, 2018: 52, 2019: 52 Freitage | 2020-02-04 | 2017-05-26 -> 06-30 (35), 06-30 -> 07-28 (28), 07-28 -> 08-25 (28); 2020-01-31 -> 02-04 (4, Umstellung) |
| eth_usd | 2.484 | 2019-03-29 / 2026-10-20 | 2019: 40 Freitage | 2020-02-18 | 2020-02-14 -> 02-18 (4, Umstellung) |

- Ab 2017-05-26 (BTC) bzw. 2019-03-29 (ETH) stimmen die deliveryPrices-Daten exakt mit den Delivery-Daten des
  Settlement-Kalenders ueberein (0 Daten nur in einer Quelle). Vor 2017-05-26 (2016-03-18..2017-05-19) gibt es nur die
  deliveryPrices-Freitage (Settlement-Kalender beginnt 2017-05-25).
- 2017-05-26..2017-08-25: nur Monatsabstaende - vor dem Start der Wochenoptionen (2017-09-01) gab es im Kalender nur
  Monatsverfaelle.

## 7. Offene Vorlage: sigma30 (NICHT gerechnet)

Naechste Nuisance-Messung fuer A2 (PROGRAMM_BILANZ 2.4 "Was gemessen werden muesste (3)"), hier nur benannt:
- **Groesse:** sigma30 = SD der 30-min-Log-Rendite r_pre 07:30-08:00 UTC, gepoolt BTC/ETH (Bybit-Perps, 1-min-Kerzen
  `bybit/rest.kline1m`), an Verfallstagen je Menge (Monat inkl. Quartal 51, Woche ohne Monat 168, Tag 1.310 in der
  Vorperiode) und an den Placebo-Slots (Abschnitt 5), dazu rho(BTC, ETH) je Ereignis und die Autokorrelation ueber
  Ereignisse.
- **Periode:** Vorperiode 2020-03-25 (BTC; ETH-Kerzen ab 2021-03-15 laut DEC-98 Nachtrag 4) bis 2024-05-31, Waechter
  wie `h27_common` (keine Rendite nach 2024-05-31, kein Mittel von r_pre ausgegeben - nur Streuung).
- **Vorab zu fixieren:** Ereignismenge, Placebo-Definition (Abschnitt 5), Umgang mit den vier Ausreisser-Tagen
  (Abschnitt 4), Anker der 30-min-Rendite (close 07:29 bis close 07:59, wie R-3 der HF-RV).
- **Daten:** die vorhandenen 1-min-Extrakte decken BTC/ETH nur 2021-03-24..2024-05-31; fuer 2020-03-25..2021-03-23 (BTC)
  waere ein weiterer Abzug noetig (Orchestrator-Entscheidung, nicht Teil dieses Auftrags).

## 8. Reproduktion

`python3 -I a2_census.py` (~3 s; liest nur die beiden Kalender-Extrakte), schreibt `a2_census.json`; fuenf Laeufe mit
gleicher sha256 (`d4168dea...8d771d83`). Eingaben-sha256 in [aj:inputs_sha256]. Die Ausgabe passiert `no_mean` und `guard_keys`.
