# HF-RV-Nuisance (Option 3, DEC-98) und A2-Ereigniszensus - adversarisches Review

> Zweiter, adversarischer Gutachter (Gate-Auditor-Rolle, Veto-Recht, Richtung Strenge), Stand 2026-10-21.
> Gegenstand: `state/herleitung_hfrv/` (NUISANCE_HFRV.md, nuisance_hfrv.json, ENTSCHEIDUNGSVORLAGEN.md,
> A2_EREIGNISZENSUS.md, a2_census.json) und die Skripte unter `scratchpad/hfrv_herleitung/`. Geprueft gegen den
> Auftrag `scratchpad/SPEC_HFRV_herleitung.md` (woertlich gelesen) und die Massstaebe Verfassung, DEC-94 (P-1),
> DEC-96 (E2, E3), DEC-97/GL-034, DEC-98 (Nachtraege 2 und 4), `herleitung_h27/FEASIBILITY.md` (P-1..P-9),
> `REVIEW_H27.md` (B-1, B-2), `PROGRAMM_BILANZ_2026-10-18.md` (Zeilen 264-280, Abschnitt 2.4),
> `src/bybit_edge/research/power_p1.py`. Nichts hier ist registriert oder beschlossen; entscheiden darf nur der
> Orchestrator.
> **Kuerzel:** `[R:<datei>]` = Review-Skript unter `scratchpad/hfrv_review/` (sha256 in Abschnitt 7);
> `[nj:]` / `[aj:]` / `[fj:]` wie in den Herleitungsdateien; VP = Vol-Punkte.
> **Ergebnisblindheit dieses Reviews:** Abschnitt 6 (kein Praemienmittel, kein Vorzeichen, kein DVOL-Mittel,
> keine Preise ab 2024-06-01, keine Siegeldatei, kein Harvest-Client).

## 0. Gesamturteil

**ZUSTIMMUNG MIT AUFLAGEN** zum Befund "Option 3 traegt nicht: die Hochfrequenz-RV senkt die Streuung der Praemie
nicht; die UNBELEGT-Annahme SD ~15,1 ist nicht bestaetigt" und zum A2-Ereigniszensus. Kein VETO.

- **Nachrechnung vollstaendig und exakt.** Mit eigenem Code (eigener Lader ueber pyarrow, Bereichs-Assert aus den
  Parquet-Metadaten vor jedem Preis, IV-Stunde aus `ts_exchange_ms`, RV aus Blocksummen der 1-min-Renditen, eigene
  Kerne) wurden 346 Zahlen der Herleitung nachgerechnet: groesste relative Abweichung 2,3e-12, keine Abweichung
  > 1 %, keine Regime- oder Datumsabweichung [R:review_hfrv.py, R:compare.py]. A2: alle Zaehlungen, Erstdaten,
  Zeitlagen und deliveryPrices-Daten identisch [R:a2_review.py].
- **Siegel-Treue bestaetigt.** Kein Praemienmittel, kein Vorzeichen, kein DVOL-Mittel in JSON, MD, Skripten oder
  Ausgaben; Waechter laufen auf dem ganzen Ausgabe-Dict; keine Rendite nach 2024-05-31; IV-Tage <= 2024-05-01; kein
  Harvest-Client im Lauf. Determinismus: Neulauf der Herleitungsskripte in einer Kopie ergibt identische JSON-Dateien
  (bis auf die Skript-Hashes der Kopie).
- **Kernaussage robust, eine Teilaussage ueberzogen (B-1).** Unter keinem der zwoelf geprueften c-Schaetzer bringt die
  HF-RV einen materiellen Gewinn: das Verhaeltnis der Langfristvarianz HF (iii) / cc liegt bei 0,87..1,31 (die
  Bilanz-Annahme entsprach 0,66 bzw. 0,43). Die Groesse "+12 % Tage mit Regel-c" und der Satz "HF ist in jeder Lesart
  spaeter" haengen aber an einem einzelnen Batch-Means-Schaetzer, dessen Wert die Blockausrichtung bestimmt: die
  verwendete Ausrichtung ist bei cc und HF das Maximum ueber alle 56 moeglichen Ausrichtungen.
- **Prior (B-2).** Die Kopfzahlen (751,7 Tage, "fruehestens 2030-09-11") stehen auf pi-2 zentral 9,47 VP, den DEC-98
  Nachtrag 2 als nicht gestuetzt fuehrt; mit dem Band 3,2..10,5 VP liegt die Dauer je Fenster zwischen ~1,7 und ~18,5
  Jahren. Das ist Richtung Strenge auszuweisen und blockiert jede Fensterlaenge (B-7).
- Die Auflagen (Abschnitt 4) betreffen Wortlaut, Lesart der Kopfzahlen, eine Konventionsangleichung und eine
  Bereinigung der A2-JSON vor jedem Commit. Keine Auflage aendert den Befund "Option 3 traegt nicht".

## 1. Nachrechnung (Herleitung gegen Review)

Unabhaengig gewaehlt: Lader (pyarrow statt polars), Stundenzuordnung der DVOL-Kerze (`ts_exchange_ms` statt
Payload-`timestamp`; 0 Abweichungen an 2 x 1.135 IV-Tagen), RV als Quadratsumme von Blocksummen der 1-min-Renditen
(statt Gitterpreisen), RV_fwd30 ueber kumulierte Summen, eigene ACF-, Bartlett-, Batch-Means- und Taper-Kerne.
`power_p1` fuer jede Power-, Regime- und Dauerzahl (Bisektion auf `assign_regime`, `assign_regime_a3_practice`,
`dec52_gate_power`; eigener Loeser). [R:review_hfrv.py], Vergleich [R:compare.py].

**Daten (BTC und ETH):** je 1.677.600 Zeilen, 1.165 Tage 2021-03-24..2024-05-31, jeder Tag 1.440 Minuten, 0 Duplikate,
0 nicht-positive Schlusskurse; letzter Tag laut Parquet-Statistik 2024-05-31 (Assert vor dem Lesen der Preise);
IV-Tage 1.135 je Symbol, keiner fehlt. Identisch mit [nj:data_kline], [nj:data_dvol], [nj:missing].

**BTC S1 (Vol-Punkte), n = 1.135 je Serie** - Herleitung = Review in jeder Zelle (Abweichung < 1e-11):

| Variante | SD | c Regel P-3 (traegt) | Konsens-c | Bartlett 60/90/120 | stat. Bootstrap 30/60/90 | ACF 30 | kappa L2,3,5 | rms RV_fwd30 % | / 30-min |
|---|---:|---|---:|---|---|---:|---:|---:|---:|
| (i) 1-min | 18,58 | 31,61 (BM 90) | 24,46 | 20,4 / 21,6 / 21,2 | 17,8 / 20,2 / 20,0 | -0,042 | 2,06 | 65,32 | 1,052 |
| (ii) 5-min | 19,47 | 30,96 (BM 90) | 23,12 | 20,3 / 21,2 / 20,6 | 17,6 / 19,1 / 18,9 | -0,053 | 2,51 | 65,98 | 1,063 |
| (iii) 5-min sub | 18,62 | 31,46 (BM 90) | 24,36 | 20,5 / 21,7 / 21,2 | 17,8 / 19,5 / 19,2 | -0,039 | 2,05 | 64,95 | 1,046 |
| (iv) 15-min | 19,27 | 31,31 (BM 90) | 26,47 | 20,7 / 22,5 / 22,4 | 18,2 / 21,0 / 20,9 | -0,049 | 2,54 | 63,35 | 1,021 |
| (v) 30-min | 17,69 | 30,65 (BM 90) | 23,84 | 20,1 / 21,2 / 20,7 | 17,8 / 20,0 / 19,4 | -0,042 | 2,20 | 62,07 | 1,000 |
| (vi) cc | 18,60 | 28,17 (BM 90) | 18,58 | 16,9 / 17,4 / 17,8 | 15,9 / 17,7 / 17,5 | -0,155 | 4,78 | 61,55 | 0,992 |

- Bartlett zusaetzlich mit `power_p1.variance_factor` gerechnet: identisch mit dem eigenen Kern.
- 180-Regel (P-3): ACF(120) liegt in allen Varianten unter 0,10 (BTC -0,005..0,025), Regel nicht ausgeloest - bestaetigt.
- cc aus dem letzten 1-min-close: SD 18,5974 gegen H-27 18,5974 [fj:nuisance.BTC.S1.sd], c 28,1723 gegen 28,1723.
  Der Rest (< 1e-6 relativ) stammt aus genau einem Tag: Panel-close 2021-03-24 weicht vom letzten 1-min-close um
  2,1e-4 ab; dieser Tag ist nur Anker der ersten RV und beruehrt nur das erste Ziel (IV-Tag 2021-03-24) - Erklaerung
  der Herleitung bestaetigt.
- Zerlegung (iii): SD(D) 8,14 VP, Corr(D, P_HF) -0,22 - bestaetigt. Rausch-SD cc nach Delta-Methode 10,92 VP
  (REVIEW_H27 B-1) reproduziert.
- Weitere Zellen identisch: S2-/S3-SD und S3-c je Variante, ETH S1 SD/c/Signatur je Variante (z. B. (iii) 27,32 /
  35,40 / 1,041; cc 25,10 / 27,64), Korrelation BTC/ETH S1 ((iii) 0,922; cc 0,831), Kurtosis, erster Lag < 0,10,
  Lag-1-ACF der 1-min-/5-min-Renditen (BTC +0,019 / -0,047).

**Power und Fensterlaenge (BTC S1, SE = max(SD sqrt(c/n), SE_null 4,17 sqrt(365/n)), `power_p1`):**

| Groesse | Herleitung | Review | Beleg |
|---|---|---|---|
| L = 12, (iii), Regel-c: SE / Power / Regime bei n 335 | 5,70 / 0,506 / GL012, A3 GL012 | identisch | [R:review_hfrv.py] |
| dto. n 365 | 5,47 / 0,535 / GL012 | identisch | dto. |
| dto. n 365, pi-2 oben 13,72 | 0,807, C10 nur durch DEC-94 | 0,807, C10, `zugelassen_nur_durch_dec94` True | dto. |
| cc, Regel-c, n 365 (GL-034-Referenz) | 5,17 / 0,575 | identisch | dto. |
| Tage je Fenster C10 P-1, pi-2 9,47, (iii) Regel-c / Konsens-c | 751,7 / 582,1 | 751,7 / 582,1 | dto. |
| dto. DEC-52 P-1 / C10 A3-Praxis, (iii) Regel-c | 822,9 / 1.346,7 | identisch | dto. |
| "voll" (iii) Regel-c: C10 P-1 / DEC-52 / A3 | 2030-09-11 / 2031-01-31 / 2033-12-14 | identisch | dto. |
| Tage C10 P-1 Regel-c je Variante (i)/(ii)/(iv)/(v)/(vi) | 752,3 / 809,4 / 801,6 / 661,7 / 671,8 | identisch | dto. |
| Konsens-c je Variante (i)/(ii)/(iv)/(v)/(vi) | 582,2 / 604,6 / 677,5 / 514,7 / 443,0 | identisch | dto. |
| Prior 7,14 (DEC-98 N2): (iii) / cc | 1.322,1 (2033-10-27) / 1.181,7 | identisch | dto. |
| Prior 3,16 (DEC-98 N2, Q-Dichte): (iii) / cc | (iii) nur im JSON | 6.750 (2063-07-16) / 6.033 | dto. |
| H-27-Referenz (Loeser-Gegenprobe) | 671,8 / 735,5 / 1.203,6; 2030-04-04 | identisch | dto. |
| Selektions-K 12 / 18 / 54, (iii) | 764 / 883 / 1.204 Tage | 763,8 / 883,4 / 1.204,3 | dto. |
| Fenster-Power bei n 752 (H-33-Entwurf) | "C10 genau an der Grenze" | 0,8002, C10; A3 GL012 -> nur durch DEC-94 | dto. |
| H-33-Kalender (iii) 752 / 1.323, cc 672 / 1.182 | Tabelle Vorlage (c) | alle 16 Daten identisch | dto. |
| Bilanz-Zeile HF 15,1 / c 28,17 | 442,9 | 442,9 (mit c 28,2: 443,3) | dto. |
| Bilanz-Zeile HF 15,1 / c 18,6 | 292,4 | 292,4 nur mit SE_null 1,39 (Bilanz-Eingabe); mit SE_null 4,17 wie alle uebrigen Zeilen: **438,4** (2028-12-24) | dto., `programm_bilanz.json` H27.inputs |

**Abweichungen > 1 %:** keine in der Nachrechnung. Zwei Lesart-Unterschiede (keine Rechenfehler): B-1 (c-Schaetzer)
und B-4 (SE_null der Bilanz-Vergleichszeilen).

**A2 (nur Kalender/Zeitlage), Herleitung = Review:** 217.728 Zeilen, 0 nicht parsebare Namen, delivery 177.999
(Futures 950, Optionen 177.049), settlement 39.729 (Futures 33.963, Perpetual 5.766); Datum des Zeitstempels =
Verfallsdatum aus dem Namen 177.999/177.999. Ereignisse 2020-03-25..2026-06-30: 251 Woche ohne Monat / 76 Monat inkl.
Quartal (26 Quartal) / 1.962 Tag / 2.289 alle; Vorperiode 168 / 51 (17) / 1.310; W1 und W2 je 40 / 12 (4) / 313;
W2 nach DEC-99 311 Tage; blind 13 / 3 (1) / 96; je Jahr identisch; 0 verfallsfreie Kalendertage. Erstdaten: BTC-
Optionen woechentlich 2017-09-01, taeglich 2020-02-04; ETH 2019-04-05 / 2020-02-18; Futures jeder Freitag ab
2021-02-19 (BTC) / 2021-03-12 (ETH). Zeitlage Optionen-Delivery q01 / q50 / q99 0,007 / 0,040 / 0,50 s nach
08:00:00 UTC, keine Zeile vor 08:00, Ausreissertage (> 60 s) 2018-05-04, 2020-08-27, 2024-08-19, 2026-07-15;
Jahresmedian 2017 5,8 s, 2021 0,011 s, 2026 0,067 s. deliveryPrices: btc_usd taeglich ab 2020-02-04, eth_usd ab
2020-02-18, Datumsmengen = Delivery-Daten (0 Abweichungen) [R:a2_review.py].

## 2. Pruefpunkte

| # | Pruefpunkt | Befund | Richtung / Anmerkung |
|---|---|---|---|
| 1 | Siegel-Treue | **BESTAETIGT** (mit B-5, B-8) | Kein Praemienmittel, kein Vorzeichen, kein DVOL-Mittel in JSON (Schluessel-Scan [R:keyscan.py] plus Code-Lektuere), MD (Textsuche), Skripten (nur Fortschrittsausgaben) und `tables.md`; `no_mean` + `guard_keys` laufen rekursiv auf dem ganzen Ausgabe-Dict vor dem Schreiben (beide JSON). Kline-Extrakte enden 2024-05-31 (Assert beim Laden). IV nur fuer t <= 2024-05-01 gespeichert (DVOL-Juni-Werte weder vorhanden noch geparst). Keine Siegeldatei, keine WP-10-IV-RV-Datei, nichts unter `data/harvest`. Rest siehe B-5 (Strike-Zaehlungen im Blindfenster) und B-8 (Panel-Lesen, latenter Harvest-Pfad). |
| 2 | Definitionstreue | **BESTAETIGT** | RV_fwd30 = sqrt((365/30) Summe RV(t+1..t+30)), UTC-Tage nach dem IV-Tag; S1/S2/S3 wie `h27_series.premium_frame`; IV = close der 23:00-UTC-Kerze / 100 (Payload-Zeitstempel = `ts_exchange_ms` in allen Zeilen); UTC-Tag = `start_ms // 86.400.000`, Tagesanker close 23:59 des Vortags; unvollstaendiger Tag -> fehlend, nie gefuellt (Regel R-2 strikt 1.440; kein Fall); Duplikate: keine. cc reproduziert H-27. |
| 3 | HF-RV-Schaetzer | **BESTAETIGT** | Alle sechs Varianten unabhaengig nachgebaut (Blocksummen statt Gitterpreise) und identisch. kappa wie REVIEW_H27 B-1 (L 2, 3, 5; ab 2021-03-25); cc-kappa 4,78 reproduziert. Niveau-Verzerrung benannt (rms (iii) / cc 1,055) und als eigenes J UNBELEGT gefuehrt. Phasen-Diagnose des Reviews: rms-Verhaeltnis der fuenf 5-min-Phasen zu cc 1,072 / 1,050 / 1,043 / 1,059 / 1,052 (BTC), Phase 0 (Gitter ab voller Stunde) ist das Maximum - die Beobachtung der Herleitung zu (ii) ist bestaetigt und stuetzt (iii). |
| 4 | c-Regel P-3 | **BESTAETIGT** (Anwendung); **ABWEICHUNG in der Lesart** (B-1) | `max(1, max{B 60/90/120, BM 60/90/120})`, 180-Regel geprueft (nicht ausgeloest), stationaerer Bootstrap mit `power_p1.stationary_bootstrap_se`, 2.000 Replikate, Seed 27 (identisch reproduziert). Konsens-c als Bericht/Gabelung gefuehrt, nicht als Regel. Die Regel-Werte tragen aber kein belastbares "c steigt um x %" (B-1). Richtung der Lesart der Herleitung: Strenge. |
| 5 | Fensterlaenge/Power | **BESTAETIGT** (Arithmetik); **ABWEICHUNG** (B-2, B-3, B-4) | `power_p1` fuer jede Zahl; SE_W = SD sqrt(c/335) bzw. 365; bindende SE = max(SE_nuis, SE_null H-27 skaliert); Tage je Fenster C10 nach P-1 und A3-Praxis, DEC-52, Kalenderdaten (Start 2026-07-01, voll = Start + 2 ceil(n) - 1 + 30) alle reproduziert. "SD 15,1 nicht bestaetigt" ist nach der vorab fixierten Regel R-9 nur aus der SD hergeleitet (ohne Mittel). Abweichungen: Kopfzahlen auf dem nicht gestuetzten Prior 9,47 (B-2, Strenge), n-335-Konvention gegen DEC-97 (B-3, Strenge), SE_null der Bilanz-Vergleichszeilen (B-4, Dokumentation). |
| 6 | Gabelungen | **BESTAETIGT** (mit B-7, B-9) | RV-Wahl als Regel R-10 vor jeder Zahl fixiert (Plausibilitaet: `hfrv_common.py` zuletzt 13:01 geaendert, DVOL-Extrakt erst 13:27 geschrieben - vor der ersten Praemie konnte keine Zahl existieren; kein Beweis, aber konsistent); Kriterien Mikrostruktur-Signatur und Definitionsgleichheit, SD und kappa nur Bericht (Richtung neutral, ausgewiesen); Gabelungstabelle mit Richtung je Zeile; Etikett "beschlossen nach Kenntnis der H-27-Feasibility (GL-034)" im H-33-Entwurf; GL-034/DEC-97 ausdruecklich unveraendert, kein Torpfosten fuer H-27. |
| 7 | A2-Zensus | **BESTAETIGT** (mit B-5, B-6) | Parser (Perpetual/Future/Option) unabhaengig nachgebaut, 0 unparsebar, Klassenzaehlungen identisch. Klassifikation zusaetzlich datenseitig geprueft: Lebensdauer der Futures (erste Settlement-Zeile bis Delivery, Verfaelle 2018-06..2026-06) Median Quartal 363 / Monat 62 / Woche 13 / Tag 3 Tage; Optionen-Strikes je Verfall in der Vorperiode (BTC) Median Tag 16 / Woche 32 / Monat 35,5 / Quartal 45 - die Kalenderklassen sind durch das Listungsverhalten gestuetzt, nicht nur angenommen. Zeitlage in UTC, Sekunden ab 08:00:00 des eigenen UTC-Tages, korrekt. Keine Preise/Renditen (Spaltenmenge per Assert). sigma30 nur als offene Vorlage. |
| 8 | Vollstaendigkeit/Belege | **BESTAETIGT** | Jede tragende Zahl mit [nj:]/[aj:]/[fj:]/[S:]-Quelle; UNBELEGT markiert (J der HF-Welt, SE_null HF, ETH-Prior, RV-Definition der Literatur, Konsens-c als Regel, Abdeckung `rest.kline1m` ab 2026-07-01); ETH nur Bericht; deterministisch (Neulauf identisch, Seeds fest). |

## 3. Befunde

### B-1 (mittel; Lesart der Kopfzahl, Richtung neutral): "c steigt um ~12 %" und "HF ist in jeder Lesart spaeter" haengen an der Blockausrichtung eines 12-Block-Schaetzers

- In allen Varianten traegt Batch-Means L 90 die Regel (12 Bloecke, Kopf-Ausrichtung: die letzten 55 Tage fallen weg).
  Das Review hat BM 90 fuer alle 56 moeglichen Ausrichtungen gerechnet [R:c_robust.py]:
  - cc: 14,3..28,2 (Mitte 17,3); die verwendete Kopf-Ausrichtung ist das **Maximum**.
  - (iii): 15,6..31,5 (Mitte 20,7); die verwendete Kopf-Ausrichtung ist ebenfalls das **Maximum**.
  - (v) 30-min: 18,2..30,7; Kopf = Maximum.
- Folge fuer den Vergleich HF gegen cc (Tage je Fenster C10 P-1, pi-2 9,47; Verhaeltnis der Langfristvarianz SD^2 c):

| c-Schaetzer | c (iii) / cc | Tage (iii) / cc | Langfristvarianz (iii) / cc |
|---|---|---|---:|
| Regel P-3 (wie fixiert, Kopf-Ausrichtung) | 31,46 / 28,17 | 751,7 / 671,8 | 1,12 |
| Regel P-3 mit End-Ausrichtung der Bloecke | 21,69 / 24,88 | 518,2 / 593,3 | **0,87** |
| Regel P-3 mit Ausrichtungs-Mitte | 22,99 / 18,83 | 549,2 / 449,0 | 1,22 |
| Bartlett B 90 | 21,69 / 17,45 | 518,2 / 416,0 | 1,25 |
| ueberlappende Batch-Means L 90 | 19,70 / 18,74 | 470,8 / 446,9 | 1,05 |
| Konsens (getaperte ACF-Summe) | 24,36 / 18,58 | 582,1 / 443,0 | 1,31 |
| stationaerer Bootstrap 60 | 19,52 / 17,75 | 466,4 / 423,3 | 1,10 |

- **Was robust ist:** Keine Lesart bringt einen materiellen Gewinn; die Spanne 0,87..1,31 liegt weit ueber dem, was die
  Bilanz unterstellt hatte (0,66 mit Regel-c, 0,43 mit Konsens-c). Bei allen stabilen Schaetzern (Bartlett,
  ueberlappende Batch-Means, Konsens, Bootstrap) ist die HF-Praemie gleich oder unguenstiger (+5..+31 %). Der
  Mechanismus (die negative ACF um Lag 30 faellt weg: cc -0,155, HF -0,04..-0,05) ist reproduziert.
- **Was nicht robust ist:** die Zahl "+12 % (Regel-c)" und der Satz in NUISANCE 6 "HF ist in jeder Lesart spaeter".
  Mit einer anderen, ebenso regelkonformen Blockausrichtung (P-3 fixiert die Ausrichtung nicht; die Kopf-Ausrichtung
  ist eine Implementierungsfolge des H-27-Codes) waere HF unter der Regel um 13 % kuerzer.
- Die Herleitung hat die Regel korrekt angewandt (Code unveraendert, wie verlangt). Eine Aenderung von P-3 wird hier
  nicht empfohlen: sie waere nach Kenntnis dieser Zahlen eine Wahl in Richtung Testbarkeit (eigene DEC). Der Befund
  verschaerft REVIEW_H27 B-2: der bindende Wert der Regel liegt am Rand seiner eigenen Ausrichtungsverteilung.

### B-2 (mittel; Richtung Strenge): Die Kopfzahlen stehen auf dem Prior 9,47 VP, den DEC-98 Nachtrag 2 als nicht gestuetzt fuehrt

- Der Auftrag verlangte pi-2 zentral 9,47 als Tabellenreferenz; die Herleitung hat das befolgt und 7,14 als Zeile
  ergaenzt. DEC-98 Nachtrag 2 haelt aber fest: "Der zentrale H-27-Wert 9,47 VP ist nicht gestuetzt; ... jede
  kuenftige VRP-Hypothese rechnet mit dem Band 3,2..10,5 VP."
- Im Band (Variante (iii), Regel-c, C10 P-1): 10,48 (pi-1, Obergrenze) 613,6 Tage; 7,14 (pi-2 BVIX) 1.322,1 Tage
  (voll 2033-10-27); 3,16 (Q-Dichte) **6.750 Tage je Fenster** (voll 2063-07-16). cc: 1.181,7 bzw. 6.033 Tage.
- Die Dauer haengt damit um den Faktor ~11 am UNBELEGTEN Prior-Niveau. Nach der Logik von P-9 ("haengt am UNBELEGTEN
  Niveau" blockiert wie UNBELEGT) laesst sich aus dieser Nuisance **keine** Fensterlaenge vorab fixieren, solange der
  Prior nicht belegt ist. Die Kopfzeile "fruehestes VRP-Urteil mit HF-RV 2030-09-11" ist in diesem Sinn optimistisch.

### B-3 (niedrig; Richtung Strenge): n 335 als "bindend" bei L = 12 widerspricht der DEC-96-E2/DEC-97-Zaehlung

- P-4 (n_W 335 bindend) gehoerte zu den W1/W2-Fenstern und ist laut FEASIBILITY Anhang A ueberholt. Fuer W3/W4 hat
  H-27 n = Kalendertage des Fensters gerechnet (L 12: n 365, SE 5,17, Power 0,575 - die Zahl in DEC-97/GL-034).
  Der Auftrag fuer die HF-Herleitung nennt wieder 335 als bindend; die Herleitung hat das befolgt.
- Folgen: (a) Vorlage (a) mischt in einer Zeile n 335 (cc 0,544; HF 0,506) mit einer Review-Zahl bei n 365 (0,73);
  (b) die Gabelungstabelle (NUISANCE 8) fuehrt n 365 als "Testbarkeit", obwohl es die beschlossene Zaehlung ist;
  (c) die Tage-je-Fenster-Rechnung nutzt (richtig) die DEC-97-/Bilanz-Konvention (n IV-Tage = Kalendertage, Ziel 30
  Tage ueber das Fensterende) - innerhalb des Dokuments also zwei Konventionen.
- Wie-mit-wie zu GL-034: cc 0,575 gegen (iii) 0,535 bei n 365. Die Zuordnung aendert sich nicht (alles GL012).

### B-4 (niedrig; Dokumentation): Die "widerlegten" Bilanz-Zeilen rechnen mit einer anderen SE_null

- `programm_bilanz.json` (H27.inputs) setzt fuer die HF-Zeilen `se_null_hf_365` = 1,39 (rauschfreie Nullwelt aus
  REVIEW_H27 B-1, UNBELEGT); die Herleitung rechnet nach R-8 mit 4,17 (cc-Welt). Mit 4,17 wuerde die Bilanz-Zeile
  "HF 15,1 / Konsens-c 18,6" nicht 292,4, sondern 438,4 Tage ergeben (dort bindet SE_null).
- Fuer alle gemessenen HF-Zeilen bindet die Nuisance, die Wahl der SE_null ist dort ohne Wirkung; die Aussage
  "Bilanz-Zeilen widerlegt" bleibt richtig. Die Vergleichszeile ist aber nicht wie-mit-wie und sollte so markiert sein.

### B-5 (niedrig bis mittel; Offenlegung, Naehe Blind-Siegel E3): `a2_census.json` speichert Strike-Zahlen je Verfallstag auch im Blindfenster

- `expiry_dates_table` enthaelt fuer jeden Verfallstag die Zahl gelieferter Optionen je Waehrung, auch fuer die 31
  Tage 2026-07-01..2026-07-31 (blind) und 760 Tage 2024-06..2026-06. Der Auftrag verlangte "je Verfallsdatum: Zahl der
  gelieferten Instrumente"; DEC-96 E3 erlaubt "Zeilen je Tag". Formal also gedeckt.
- Inhaltlich ist die Strike-Zahl eines Tagesverfalls aber ein schwacher Stellvertreter fuer die Preisbewegung (neue
  Strikes werden gelistet, wenn der Preis wandert) - dieselbe Klasse wie die Bytesummen, die DEC-97 A-3 "kuenftig
  vermeiden" laesst. Die Markdown-Datei zitiert keine Blindfenster-Strikezahl; die Quantile reichen bis 2026-06-30 und
  schliessen W1/W2 ein (dort ist die BTC-Vol bereits in der Akte, DEC-95 E2).
- Das Review hat keine Strike-Zahl ab 2024-06-01 gerechnet oder angesehen (nur Zaehlung der Zeilen mit Wert > 0, ohne
  Werte; eigene Strike-Signatur nur fuer Verfaelle <= 2024-05-31).

### B-6 (niedrig; Praezision V-5a): "Seit wann woechentlich" ist im Kalender ab 2017-05-25 beantwortet, nicht absolut

- `deliveryPrices` btc_usd hat bereits ab 2016-03-18 woechentliche Freitags-Termine (2016: 42, 2017 bis 05-19 lueckenlos
  7-Tage-Abstaende), dann 2017-05-26..08-25 nur Monatsabstaende (35/28/28), ab 2017-09-01 wieder woechentlich
  [R:a2_review.py, Lueckenhistogramm 7: 189, 35: 1, 28: 2, 4: 1]. Der Instrumenttyp vor 2017-05-25 ist nicht im
  Extrakt.
- Die Formulierung "schliesst den offenen Punkt 'Beginn der Wochenverfaelle UNBELEGT'" (A2 2) gilt nur fuer "jeden
  Freitag lueckenlos ab 2017-08-25". Der Beginn liegt spaetestens 2016-03-18; Typ und Regel davor bleiben UNBELEGT.
  Fuer A2 (ab 2020-03-25) ohne Wirkung.

### B-7 (mittel; Programmebene): Der H-33-Entwurf folgt nicht aus Option 3 und hat einen grossen Siegel-Preis

- Option 3 (Bilanz Teil C, DEC-98 E4) lautete: "bestaetigt sich SD ~15,1, eine neue VRP-Hypothese ... herleiten".
  Die Bedingung ist nicht erfuellt. Der Entwurf (c) ist in der Sache H-27 mit Fenstern ueber 12 Monate - die Bilanz
  hat das ausdruecklich als "neue Hypothese nach Kenntnis der Feasibility, keine Zulassung" gefuehrt. Er braucht eine
  eigene DEC mit Etikett und ist keine Folge dieser Messung (die Herleitung sagt das in ihrem Hinweis zur Tragweite
  selbst; es gehoert in den Kopf der Vorlage).
- Eine solche Hypothese hielte das Blind-Siegel DEC-96 E3 auf BTC/ETH-Vol bis 2030-04 (cc, 9,47) bzw. 2033-01 (cc,
  7,14) oder laenger und sperrte bis dahin jede Klasse-W-/A1-Rechnung auf Fenstern ab 2026-07-01 (DEC-98 E1 (b)).
  Das ist Teil der offenen Reihenfolge-Frage an den Nutzer (DEC-98 E4 (b)) und nicht allein vom Orchestrator zu
  entscheiden.
- Die RV-Wahl im Entwurf ("(iii) oder cc - Wahl vor der Registrierung") faellt jetzt nach Kenntnis beider Dauern:
  cc ist mit Regel-c 11 % kuerzer, mit gemessenem Konsens-c 24 %. Wird cc gewaehlt, ist das zu etikettieren (bekannte
  Definition, aber Wahl nach Kenntnis dieser Nuisance), und beide Varianten zaehlen in K.

### B-8 (Hinweis; Verfahren): latente Risiken im wiederverwendeten Code

- R-13 liest die Panel-Partition 2024 vollstaendig in den Speicher und verwirft Tage nach 2024-05-31 vor jeder
  Verwendung (strenger als H-27, das alle Jahre las; Praezedenzfall akzeptiert). Kuenftig per Lesefilter, damit Werte
  nach dem Stichtag nie materialisiert werden.
- Die unveraenderte Kopie `h27_series.py` enthaelt mit `dvol_daily_close` einen Pfad zum Harvest-Client. Er wird im
  HF-Lauf nicht ausgefuehrt (`premium_frame` wird nie aufgerufen; nur importiert). Kuenftiger HF-/VRP-Code sollte ihn
  nicht mitfuehren.
- Die Waechter sind schluesselbasiert. Dass kein Wert unter einem harmlosen Schluessel ein Mittel traegt, hat das Review
  durch Code-Lektuere festgestellt, nicht durch den Waechter.

### B-9 (Hinweis; Ermessen R-10): Die Signaturgrenze 1,05 entscheidet knapp

- (iii) liegt mit 1,046 (BTC) / 1,041 (ETH) knapp im Band; bei einer Grenze von 1,04 waere (iv) 15-min gewaehlt worden
  (801,6 statt 751,7 Tage, Regel-c). Die Regel war vorab fixiert; der Befund aendert sich nicht (alle HF-Varianten
  661,7..809,4 Tage gegen cc 671,8). Die Phasen-Diagnose (Abschnitt 2, Pruefpunkt 3) stuetzt die Wahl von (iii) sachlich.

## 4. Auflagen (vor einem DEC-Nachtrag zu Option 3)

- **A-1 (B-1):** Den HF-Befund so fassen: "Hochfrequenz-RV bringt keinen Gewinn: Langfristvarianz HF (iii) / cc
  0,87..1,31 je nach c-Schaetzer (Regel P-3: 1,12; stabile Schaetzer 1,05..1,31); die Bilanz-Annahme (0,66 bzw.
  0,43) ist widerlegt." Den Satz "HF ist in jeder Lesart spaeter" streichen oder auf "in keiner Lesart materiell
  frueher" aendern. Bei c = 31,46 / 28,17 vermerken, dass die Kopf-Ausrichtung von BM 90 bei HF und cc das Maximum
  ueber alle Ausrichtungen ist. Keine Aenderung von P-3 (waere Testbarkeit nach Kenntnis, eigene DEC).
- **A-2 (B-2):** In DEC-Text und Vorlage die Dauer fuer den Prior nach DEC-98 Nachtrag 2 ausweisen (pi-2 7,14 als
  Referenz; Band 3,2..10,5 VP mit 6.750 / 1.322 / 614 Tagen je Fenster fuer (iii), 6.033 / 1.182 / 548 fuer cc) und
  festhalten: eine Fensterlaenge ist aus dieser Nuisance nicht vorab fixierbar, solange der Prior am UNBELEGTEN Niveau
  um den Faktor ~11 haengt (P-9-Logik).
- **A-3 (B-3):** L-12-Zeilen wie GL-034 mit n 365 ausweisen (cc 0,575 gegen (iii) 0,535), n 335 als Bericht; das
  Gabelungs-Etikett "n 365 = Testbarkeit" korrigieren; im Auftragstext kuenftiger VRP-Herleitungen die DEC-96-E2-
  Zaehlung nennen.
- **A-4 (B-4):** Die Bilanz-Vergleichszeilen mit ihrer SE_null 1,39 kennzeichnen (oder mit 4,17 neu rechnen: 442,9 /
  438,4 Tage).
- **A-5 (B-5):** Vor jedem Commit von `a2_census.json` die Tabelle `expiry_dates_table` auf Daten <= 2026-06-30
  kuerzen (fuer das Blindfenster nur Datum/Klasse) und im Kontaminations-Register (C.17) vermerken, dass Strike-Zahlen
  je Verfallstag fuer W1/W2 und 31 Blindtage berechnet, aber nicht zitiert wurden. Kuenftig im Blindfenster nur
  Existenz und Klasse eines Verfallsdatums.
- **A-6 (B-6):** V-5a-Satz praezisieren: "woechentliche Liefertermine spaetestens ab 2016-03-18 (deliveryPrices; Typ
  vor 2017-05-25 nicht im Extrakt), Pause 2017-05-26..08-25, jeder Freitag lueckenlos ab 2017-08-25".
- **A-7 (B-7):** Den H-33-Entwurf als eigene Vorlage fuehren ("Fenster ueber 12 Monate, beschlossen nach Kenntnis
  GL-034"), nicht als Ergebnis von Option 3; den Siegel-Preis (E3 bis 2030..2033, Sperre Klasse W/A1 ab 2026-07)
  in die Reihenfolge-Frage an den Nutzer (DEC-98 E4 (b)) aufnehmen; eine spaetere RV-Wahl etikettieren und alle
  gerechneten Varianten in K zaehlen.

Nicht blockierend: B-8 (Lesefilter, Harvest-Pfad aus kopiertem Code entfernen), B-9 (Signaturband als Ermessen
nennen) und der Merkposten der Herleitung zur Exzess-Kurtosis 2,6 (Normal-Naeherung der Power-Zeile, Positivkontrolle).

## 5. Was NICHT folgt

- Kein Verdikt ueber die Volatilitaets-Risikopraemie, keine Aussage ueber ihr Niveau oder Vorzeichen (weder in der
  Herleitung noch im Review berechnet oder gesehen). GL-034 / DEC-97 bleiben unveraendert; H-26 bleibt gesperrt.
- Keine Regelaenderung: weder Konsens-c noch eine andere BM-Ausrichtung wird fuer P-3 vorgeschlagen (B-1 ist eine
  Lesart-Auflage, keine Regel). DEC-96 E2 bleibt fuer H-27 unberuehrt.
- Option 3 eroeffnet keinen kuerzeren Weg zur VRP; der H-33-Entwurf ist durch dieses Review nicht befuerwortet - nur
  seine Arithmetik (Tage, Kalender, K, Regime) ist nachgerechnet.
- Keine Aussage ueber W1/W2 oder die blinden Fenster; gerechnet wurde nur auf 2021-03-24..2024-05-31 (Preise) bzw.
  Kalender/Zeitstempel (A2).
- A2 bleibt durch V-5b gesperrt; sigma30 ist weder von der Herleitung noch vom Review gerechnet. Der Zensus zeigt nur,
  dass es seit 2020-02 keinen verfallsfreien Tag gibt (Placebo-Design vorab fixieren).
- Keine Aussage, dass 1-min-Daten fuer andere Klassen nutzlos sind.

## 6. Ergebnisblindheit dieses Reviews (Offenlegung)

- **Daten:** nur die Extrakte unter `scratchpad/hf_data/raw/`; kein Harvest-Client, kein Netz, kein Listing. Vor dem
  Lesen eines Preises wurde der Zeitbereich der Kline-Extrakte aus den Parquet-Statistiken geprueft (letzter Tag
  2024-05-31) und danach auf der geladenen Spalte erneut. DVOL-Werte nur fuer IV-Tage 2021-03-24..2024-05-01 geparst.
  Das Union-Panel wurde vom Review nicht gelesen.
- **Ausgaben:** nur SD, ACF, Varianzfaktoren, Verhaeltnisse, Korrelationen, RV-Niveaus (rms), Power- und Dauerzeilen,
  Kalender- und Zeitstempelzaehlungen; eigener Waechter auf jedem Ausgabe-Dict (verweigert jeden Schluessel mit
  mean/avg/median/sign/Mittel/Vorzeichen); Schluessel-Scan aller Review-JSON. Die Praemie existierte nur im Speicher.
- **Determinismus-Neulauf** der Herleitungsskripte in einer Kopie unter `scratchpad/hfrv_review/rerun/` (Ausgabepfad
  umgelenkt); die Kopie der Ausgaben wurde nach dem Vergleich geloescht.
- **A2:** Strike-Zahlen nur fuer Verfaelle <= 2024-05-31; fuer das Blindfenster nur Kalender (Existenz/Klasse) und
  Zeitstempel; aus `a2_census.json` nur Zaehlung der Blindfenster-Zeilen mit Wert > 0 (ohne Werte).
- Nicht geoeffnet: Siegeldateien, WP-10(A2)-/WP-10(A)-IV-RV-Dateien, `data/harvest`. Aus `feasibility.json` nur
  SE_null, Priors, SD, c und RV-rms der H-27-Akte gelesen (nach Schluessel-Scan).
- Vorwissen wie in KONTAMINATION.md; nicht verwendet.

## 7. Skripte (`scratchpad/hfrv_review/`, sha256 gekuerzt) und Reproduktion

| Datei | sha256 | Inhalt |
|---|---|---|
| `review_hfrv.py` | `a749af2f...165394a4` | Lader mit Metadaten-Assert, RV-Varianten aus Blocksummen, Statistiken, Power/Dauer ueber `power_p1` -> `review_hfrv.json` |
| `compare.py` | `3d91572e...57b8cb58` | 346 Zellvergleiche Herleitung gegen Review (max. relative Abweichung 2,3e-12) |
| `c_robust.py` | `de3fd9d5...17cd1ad0` | c-Schaetzer-Robustheit (BM-Ausrichtungen, OBM, Bartlett, Konsens, Bootstrap) -> `c_robust.json` |
| `a2_review.py` | `830c4dab...a5f789d2` | eigener Parser, Ereigniszaehlung, Futures-Lebensdauer, Strike-Signatur (Vorperiode), Zeitlage, deliveryPrices -> `a2_review.json` |
| `keyscan.py` | `a643d013...b0c27469` | Schluessel-Scan der JSON-Ausgaben (Herleitung, H-27, Review) |

Aufruf: `python3 -I review_hfrv.py` (~5 s), `python3 -I compare.py`, `python3 -I c_robust.py`, `python3 -I a2_review.py`
(jeweils mit `PYTHONPATH=/home/user/scinance/src` bzw. dem im Skript gesetzten Pfad). Skript-sha256 der Herleitung
gegen `[nj:skripte_sha256]` geprueft: identisch; die vier aus `h27_herleitung/` kopierten Dateien sind bytegleich mit
den Originalen.
