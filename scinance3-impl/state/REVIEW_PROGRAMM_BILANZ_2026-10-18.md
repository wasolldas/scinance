# Review P-2 (adversarisch): Programm-Bilanz / Power-Zensus 2026-10-18

> Zweiter, adversarischer Gutachter, Stand 2026-10-18. Gegenstand: `state/PROGRAMM_BILANZ_2026-10-18.md` (548 Zeilen,
> Commit `35d4471`), `state/programm_bilanz.json` (sha256 `c4b29702...48cb4f`), Skripte `scratchpad/bilanz/`
> (`bilanz_census.py` sha256 `4f90415f...c34bfb`, identisch mit dem JSON-Feld `skript`). Auftrag
> `scratchpad/SPEC_BILANZ_review.md`, Herleitungsauftrag `scratchpad/SPEC_BILANZ_power_zensus.md`. Massstab: Verfassung
> `scinance3-impl/CLAUDE.md`, PRD, DEC-51/52/58/59/61/67/73/92-97, `src/bybit_edge/research/power_p1.py`, 2.0-Registry
> H-26. Nichts hier ist beschlossen; entscheiden darf nur der Orchestrator, die Programmrichtung waehlt der Nutzer
> (PRD Par. 8). Eigene Skripte unter `scratchpad/bilanz_review/` (Kuerzel `[R:<datei>]`, sha256 in Abschnitt 8).
> `Z. n` = Zeile n in PROGRAMM_BILANZ_2026-10-18.md. Fehler wurden in beiden Richtungen gesucht; jeder Befund nennt
> seine Richtung (zu pessimistisch = Bilanz macht etwas schwerer/spaeter, als die Regeln verlangen; zu optimistisch =
> umgekehrt).

## 0. Urteil

**ZUSTIMMUNG MIT AUFLAGEN.**

- **Rechenkern (Teil A): Zustimmung.** Jede gepruefte Dauer-, Datums- und Hebelzahl wurde mit eigenem Code
  reproduziert (Abschnitt 1). Kein Rechenfehler, keine Regelverletzung: keine Siegeldatei, keine WP-10(A)/(A2)-Datei,
  keine Outcome-Groesse, Blind-Siegel DEC-96 E3 gewahrt. Das Census-Skript laeuft deterministisch; eine nach
  `scratchpad/` umgeleitete Kopie erzeugt dasselbe JSON (bis auf das Feld `skript`).
- **Entscheidungsvorlage (Teil C): in vier Punkten nicht weitergabefaehig.** Die Auflagen A-1 bis A-4 sind vor der
  Weitergabe an den Nutzer zu erfuellen. Keine davon aendert eine Zahl aus Teil A.
  1. **Ein Weg fehlt, den DEC-92 selbst benennt (B-1, Bilanz zu pessimistisch).** Ein A3-Design mit `fm_neutral_8w`
     als Primaerstatistik auf den REZENZ-Fenstern W1/W2 ist schon heute C10. Die reale IC dieser Fenster wurde nie
     berechnet. Voraussetzung ist ein belegter Prior >= 0,021 (P-1) bzw. >= 0,027 (A3-Praxis). Dafuer muesste man
     weder warten noch eine Regel lockern, und das Blind-Siegel waere nicht beruehrt.
  2. **Die Entsperrdaten vor dem VRP-Lauf vertragen sich nicht mit dem Blind-Siegel (B-2, Bilanz zu optimistisch).**
     Betroffen sind A3 und A1 auf blinden Fenstern ab 2026-10-05. `fm_neutral_8w` regressiert auf BTCUSDT, und die
     Kalibrierung wird je Fenster gerechnet. DEC-96 E3/DEC-97 verbieten genau diese Rechnungen auf Tagen ab
     2026-07-01, bis eine VRP-Hypothese gelaufen ist. Option 1 ist in dieser Form nicht in sich konsistent.
  3. **Der Strukturbefund "Zwei-Fenster-Regel kein Zeitfresser" vergleicht ungleiche Power (B-3).** Bei gleicher
     Fehlerrate und gleicher Gesamt-Power kostet die Regel 23-26 % mehr Daten.
  4. **"Einmal-Gut" ist ueberzeichnet, und die Reihenfolge H-26 / VRP-Nachfolger ist nicht als Optionen
     ausgewiesen (B-4, B-5).** Je nach Lesart ist die H-26-Entsperrung womoeglich schon jetzt erreicht.

## 1. Nachgerechnete Zahlen (Pruefpunkt 1)

Unabhaengiger Weg `[R:review_check.py]`:

- Die Nuisance wird selbst aus den Akten gelesen, mit Waechter gegen Siegelnamen und WP-10(A)-Verzeichnisse.
- Gesucht ist die kleinste **ganzzahlige** Fensterlaenge, fuer die `power_p1.assign_regime` (bzw.
  `assign_regime_a3_practice`) das Ergebnis C10 liefert. Die Bilanz loest stattdessen per Bisektion.
- Das DEC-52-Gate wird separat mit `dec52_gate_power` gerechnet.
- Daten werden ueber Ordinalzahlen bestimmt, Quartalsverfaelle mit `calendar`.
- Zusaetzlich wurde die Kopie des Census-Skripts nachgefahren `[R:rerun/census_copy.py]`.

| Zeile | Bilanz | Review | eingegangene Nuisance / Regel | Beleg |
|---|---|---|---|---|
| H-27 C10 je Fenster, voll | 671,8 Tage, 2030-04-04 | 672, 2030-04-04 | SD 18,60 VP (BTC S1, Vorperiode 2021-03-24..2024-05-31); c 28,17 (Regel P-3 = Maximum aus sechs Schaetzern, getragen von Batch-Means L 90); SE_null 4,17 bei n 365 bindet nie (Verhaeltnis konstant in n); Prior pi-2 zentral 9,47 | Z. 259 |
| H-27 DEC-52 / A3-Praxis | 736 / 1.204 Tage; 2030-08-10 / 2033-03-03 | identisch | dto. | Z. 259 |
| H-27 Prior-Band 7,00 / 13,72 | 2033-04-24 / 2028-05-02 | identisch (1.230 / 321 Tage) | dto. | Z. 260-261 |
| A3 mom1, W1-stress (bindend) | 119,3 Wochen, 2031-05-11 | 120 ganzzahlig, 2031-05-11 | SD 0,1302 (`methods.none.factor_sd`, stress, 300 Rep.); c 1,0245 (c_hat der Null, MC-Fehler ~8 %); Boden 0,0486 bindet nicht; Prior 0,03 [sek] | Z. 146 |
| A3 mom1, W1-measured | 56,7 Wochen, 2028-12-10 | 57, 2028-12-10 | SD 0,0901, c 1,015 | Z. 148 |
| A3 rev_gap, W1-stress | 131,5 Wochen, 2031-10-26 | 132, identisch | SD 0,1286, c 1,157 | Z. 147 |
| A3-Praxis W1-stress mom1 | 213,8 Wochen, 2034-12-17 | 214, identisch | dto. | Z. 146 |
| A1 theta 1 / 0,77 | 84,8 / 143,0 Wochen; 2030-01-06 / 2032-04-11 | 85 / 144; identisch | SD 372,9 bp (W1-Projektion P2, bindend); c = 1 nach P-1 (c_hat 0,76, keine Gutschrift); prem = Spread W1 175,8 x phi 0,573 x theta | Z. 219, 221 |
| A4, 4 Zyklen je Fenster | 2029-06-29 | 2029-06-29 (Verfall Nr. 8 ab 2027-06-25, Freitag) | sigma_w UNGEMESSEN; reine Kalenderrechnung | Z. 335 |
| DEC-52-Mehrbedarf | +9,5 % | Zulassung bei prior/SE 2,6017 statt 2,4865 -> x1,0948 | Produkt-Gate, z gepoolt 2,5287, Screens 0,894 SE je Fenster | Z. 39, 89 |
| A3-Praxis-Faktor | 1,79 | (3,3281 / 2,4865)^2 = 1,7916 | - | Z. 49, 91 |
| Ein-Fenster-Vergleich | +7,7 % | 1,0766: Arithmetik richtig, Lesart falsch (B-3) | alpha 0,0025 / Power 0,80 gegen 2 x Power 0,80 | Z. 59, 486 |
| Selektions-K 20 | +22 % | (1,901 + 0,8416)^2 / 2,4865^2 = 1,217 | DEC-94 (7) | Z. 80, 200 |
| Startdaten | 2026-10-05 / 2026-07-01 / 2027-06-25 | Montag / Mittwoch / Freitag; Regeln "Start + 2n Wochen - 1 Tag" bzw. "Start + 2n - 1 + 30 Tage" bestaetigt | - | Z. 97-99 |

**Hebel (Pruefpunkt 2):**

| Hebel | Bilanz | Review | Bewertung |
|---|---|---|---|
| mehr Symbole (A3) | -14 %, Faktoranteil 86 % | Varianzanteil 0,861; K -> unendlich: 102,7 Wochen | richtig, additive Naeherung offen etikettiert; unter measured -29 % |
| zweite Boerse | ~0 | - | richtig fuer doppelt gelistete Coins; nur boersenexklusive Coins erhoehen K, Obergrenze -14 % |
| fm8 als Primaerstatistik | -81 % | 22,8 Wochen bei Prior 0,03 | **nur Illustration**: gleich schnell wie der Roh-IC bei Prior 0,0131 (44 % von 0,03); Prior 0,02 -> 51 Wochen, 0,015 -> 91 Wochen (B-6) |
| HF-RV | -34 % / -57 % | (15,1 / 18,6)^2 = 0,659; 442,9 / 292,4 Tage | Zahl UNBELEGT; ein unveraendertes c ist eher konservativ (B-9) |
| BTC+ETH ein Bein | -4..-9 % | 615 / 632 / 641 Tage (rho 0,83 / 0,88 / 0,907); Tagesmittel 643 | richtig; ETH-Prior UNBELEGT |
| nicht ueberlappende Monatsziele | +8 % | 24,12 Monate = 723,5 Tage (x1,077); Power bei L 12: 0,543 gegen 0,575 | siehe unten |
| A1-Hedge | -7 % | Residualvarianz 0,9316 -> -6,8 % | richtig |

Zu den nicht ueberlappenden Monatszielen: Ueberlappend liefert ein Jahr 365 / 28,17 = 12,96 effektive Beobachtungen,
nicht ueberlappend 12 (c_m = 1). Hinzu kommt SD 18,70 gegen 18,60. Die +8 % sind damit unter der Regel-c plausibel.
Mit dem Konsens-c (19,6 effektive Beobachtungen je Jahr) waere die Monatsvariante sogar 63 % schlechter. Vorne laege
sie nur mit einer Gutschrift fuer die negative ACF1 (-0,16); diese Gutschrift verbietet P-1 (DEC-94 (4)). Der Satz
"Monatsvariante hat 12x weniger Punkte" im Auftrag trifft es nicht: Es sind 30x weniger Rohpunkte, aber nur ~1,08x
weniger effektive.

## 2. Befunde

### B-1 (hoch; Vollstaendigkeit Teil A/C; Bilanz zu pessimistisch): A3 mit fm8-Primaerstatistik auf den REZENZ-Fenstern W1/W2 fehlt - schon heute C10, wenn ein Prior belegt wird

**Die Bilanz** rechnet fm8 nur auf kuenftigen blinden Fenstern ab 2026-10-05 ("voll 2027-08-22", Z. 45, 185, 370).
Die historischen Fenster behandelt sie nur fuer das registrierte Roh-IC-Design, mit dem Vermerk "nicht zulaessig:
DEC-94 nicht rueckwirkend" (Z. 202).

**Was die Akte dazu sagt:**

- DEC-92 ("Was nicht folgt") nennt ausdruecklich "ein anderes Design (z. B. der fm8-neutralisierte IC als
  Primaerstatistik, gepoolte Fenster) ... als NEUE Hypothese ... bisher wurde keine reale IC berechnet".
- GL-032: "Anderes Design nur als neue Hypothese mit eigenem K".
- `STAND_2026-10-18.md` Abschnitt 3: "Keine reale IC wurde je berechnet; die Siegel sind geschlossen".
- W1/W2 (2024-07-01..2026-06-30) sind die REZENZ-Fenster des PRD (PRD Z. 483).
- Der Vermerk "nicht rueckwirkend" betrifft die registrierte Drittfassung, nicht die Fenster. Eine neue Hypothese faellt
  unter P-1 (DEC-94, Geltung).

**Nachrechnung** `[R:review_check.py, A3_fm8_on_W1_W2]`:

- Quelle: `wp13a_prelaunch.json` `windows.<W>.beta_control_recommended_high_rep.<cal>.variants.mom1` (1.000 Rep.,
  SD des Fenster-Mittels unter der kalibrierten Null; c ist damit enthalten).
- SE stress W1 / W2: 0,00788 / 0,00636. Null-Mittel: 0,0008 / 0,0005, driftend 0,0009 / 0,0005.
- `power_p1.assign_regime` mit Prior 0,03 abzueglich Null-Mittel: **C10**, Fenster-Power 0,98 / 1,00.
- Unter der A3-Praxis ebenfalls **C10** (0,88 / 0,98). Die Zulassung haengt also nicht an DEC-94.
- Mindest-Prior fuer C10 (Break-even): 0,0203 (stress) bzw. 0,0206 (driftend) unter P-1; 0,0270 / 0,0273 unter der
  A3-Praxis.
- Keine Kollision mit dem Blind-Siegel, denn W2 endet am 2026-06-30.

**Bedingungen (gleichwertig zur theta-Blockade bei A1):**

1. Ein Beleg fuer den Prior des neutralisierten IC (UNBELEGT, Z. 194).
2. Eine neue Hypothese mit eigenem K, das die sieben F-XSEC1-Varianten mitzaehlt (DEC-94 (7) bindet ab K 12).
3. Die Etiketten "beschlossen nach Kenntnis von GL-032" und C.17 (Beta-Kalibrierungs-IC und Lag-Profil gesehen).
4. Eine Blindheits-Inventur W1/W2 fuer die fm8-Statistik.
5. Das Beta-Kontroll-Quantil ist auf dem Niveau 0,95 neu zu fixieren (die Akte fuehrt es bei 0,9936).

**Folge:** Der fruehestmoegliche Zeitpunkt fuer fm8 ist "sobald ein Prior-Beleg vorliegt", nicht 2027-08-22. In Teil C
fehlt dieser Weg als eigene Option (Beleg-Weg, neben A1-theta).

### B-2 (hoch; Konsistenz Teil C; Bilanz zu optimistisch): A3/A1-Laeufe auf blinden Fenstern ab 2026-10-05 kollidieren mit dem Blind-Siegel DEC-96 E3 / DEC-97

**Der Wortlaut des Siegels:**

- DEC-96 E3 verbietet "keine realisierte Volatilitaet bzw. Renditestreuung von BTC oder ETH auf Tagen ab 2026-07-01 -
  auch nicht als Nebenprodukt anderer Pakete (z. B. Marktfaktor-SD ...)".
- DEC-97 haelt das Siegel offen fuer "jede kuenftige, neu vorab registrierte VRP-Hypothese".

**Was A3 und A1 dafuer rechnen muessten:**

- A3: `fm_neutral_8w` nutzt `market_symbol` = BTCUSDT mit 8-Wochen-Betas (`wp13a_prelaunch.json`). Die
  Null-Kalibrierung wird je Fenster aus der Faktor-Vol des Fensters gerechnet (DEC-87 (D)). Die Positivkontrolle
  kalibriert ihre Welt auf die Faktorstruktur des Fensters (DEC-89 E2).
- Jeder A3-Lauf auf Fenstern ab 2026-10-05 rechnet damit genau die verbotene Groesse. Das gilt schon fuer die
  Formations-Betas ab 2026-08-10.
- A1: Die Streuung der Universums-Rendite liegt im Grenzbereich und ist zu klaeren.

**Die Bilanz** erwaehnt E3 nur fuer H-26 und A2 (Z. 62, 316, 359).

**Folgen fuer die Daten in Option 1:**

- Alle A3/A1-Daten, die vor einem registrierten VRP-Lauf liegen, sind ohne neue DEC nicht erreichbar: A1 bei theta 1
  mit W1-Spread (2030-01-06, vor VRP 2030-04-04), A1 mit W2-Spread (2027-08-22), A3 unter measured/W2 (2027-10..2028-12)
  und A3-fm8 auf kuenftigen Fenstern (2027-08-22).
- Das bindende A3-Datum 2031-05-11 liegt nur zufaellig nach der VRP-Referenz.
- Wird nie eine VRP-Hypothese registriert und gerechnet (Option 5, oder Option 3 nicht gewaehlt), bleiben A3/A1 auf
  blinden Fenstern unbefristet gesperrt.

**Vier Auswege:**

1. Reihenfolge: VRP zuerst.
2. Programmweiter Zuschnitt von E3 (Regelfrage, vor dem ersten Kandidaten, der ihn braucht; Etikett).
3. Ein A3-Design mit einem Marktfaktor ohne BTC/ETH. Das ist eine neue Hypothese und nur ein schwacher Ausweg, denn der
   Faktor bleibt korreliert.
4. Der Weg B-1 auf W1/W2, der keine Kollision hat.

### B-3 (mittel; Strukturbefund; schont C.10): "Zwei-Fenster-Regel kein Zeitfresser" vergleicht Power 0,80 mit 0,64

**Die Aussage der Bilanz:** "Ein Fenster mit alpha 0,0025 braucht 7,7 % MEHR Daten" (Z. 58-60, 426-427), "die
Zwei-Fenster-Struktur kostet bei gleicher Rate nichts" (Z. 496).

**Warum der Vergleich nicht traegt:** O5 hat Power 0,80, O0 nur eine gemeinsame Power von 0,64. Bei gleicher
Fehlerrate (0,25 %) und gleicher Gesamt-Power ergibt sich `[R:review_check.py, windows_compare]`:

| gemeinsame Power | ein Fenster | zwei Fenster | Mehrbedarf zwei Fenster |
|---|---|---|---|
| 0,64 | 0,810 | 1,00 | +23 % |
| 0,80 | 1,077 (O5) | 1,356 (O6) | +26 % |

**Richtige Lesart:** Die Zwei-Fenster-Regel kostet 23-26 % mehr Daten. Das ist der Preis der Regime-Robustheit (C.10,
PRD 3.5 (a)) und als solcher legitim. Der groessere Hebel ist das Power-Ziel je Fenster (O1: 0,44..0,76).

**Warum das zaehlt:** Die falsche Lesart laesst die Ein-Fenster-Zeilen von Option 4 nutzloser erscheinen, als sie sind.

### B-4 (mittel; Teil C; Bilanz zu restriktiv): "Blinde Fenster sind ein Einmal-Gut" ist ueberzeichnet

Gemeint sind Z. 58, 422-425 und 468. Die Blindheit verbraucht sich nicht dadurch, dass eine Hypothese auf den Fenstern
"laeuft". Sie verbraucht sich durch die erste Outcome-Rechnung auf einem Zeitabschnitt, und zwar nur fuer Hypothesen,
die danach festgelegt werden. Daraus folgt:

- (a) Mehrere Hypothesen, die VOR der ersten Rechnung registriert sind, teilen dieselben blinden Fenster. Das kostet
  K und eine Familien-Korrektur (DEC-51 (4)), aber keine Blindheit.
- (b) Kuenftige Tage sind immer blind. Eine Rechnung auf einem Abschnitt kostet nur diesen Abschnitt.
- (c) Beispiel H-26 (Lesart a): verbraucht 2026-07-01..2026-11-16. Ein VRP-Nachfolger startete dann am 2026-11-17 und
  waere am 2030-08-21 voll statt am 2030-04-04, also 139 Tage spaeter. Das ist eine Verzoegerung, kein Verlust des
  Guts.

Vorschlag fuer den Wortlaut: "Blinde Daten sind ein Einmal-Gut je Zeitabschnitt: Die erste Outcome-Rechnung auf einem
Abschnitt entwertet ihn fuer jede danach festgelegte Hypothese derselben Groesse; vorher registrierte Hypothesen teilen
ihn; spaetere Abschnitte bleiben blind."

### B-5 (mittel; H-26; Dringlichkeit): Die Entsperrung haengt an der Lesart, liegt womoeglich schon hinter uns, und die Reihenfolge-Optionen fehlen

Gemeint sind Z. 61-63 und 353-363. Die Bilanz setzt "~Mitte November 2026" aus der 2.0-Inventur und vermerkt die
Zaehlung als UNBELEGT. Diese Inventur ist aber mit den Luecken aus DEC-96 nicht vereinbar: Nach der Luecke
2026-08-02..03 begaenne jede zusammenhaengende Zaehlung neu.

Die Kalenderrechnung (nur Daten aus DEC-96 und der H-26-Formel, `[R:review_check.py, H26]`) ergibt vier Lesarten:

| Lesart | Streambeginn | W1 / W2 | Entsperrung (Tag 210) | im Blindbereich ab 2026-07-01 |
|---|---|---|---|---|
| (a) 2.0-Inventur, 112 Tage am 2026-08-10 | 2026-04-21 | ..07-19 / 07-20..10-17 | 2026-11-16 | W2 ganz, W1 mit 49 Tagen (inkl. 30-Tage-RV) |
| (b) Harvester ab Lueckenende 2026-03-20, per REST geheilte Tage zaehlen | 2026-03-20 | ..06-17 / 06-18..09-15 | **2026-10-15 (bereits vorbei)** | W2 ganz, W1 mit 17 Tagen |
| (c) geheilte Tage zaehlen nicht, Neubeginn nach Luecke 2026-09-20 | 2026-09-21 | 2026-09-21..2027-03-19 | 2027-04-18 | beide ganz |
| (d) voller REST-Backfill zaehlt, `deribit/publicTrade` lueckenlos ab 2025-08-01 (UNBELEGT) | 2025-08-01 | 2025-08-01..2026-01-27 | 2026-02-26 (vorbei) | keins |

**Bewertung:**

- Die Aussage der Bilanz ("mindestens das zweite Fenster") stimmt in den Lesarten (a) bis (c).
- In (a) ragt auch W1 hinein.
- Lesart (d) loest den Konflikt. Sie ist aber eine Lesart in Richtung frueheres Testen, gewaehlt nach Kenntnis der
  Kollision, und PRD Z. 388 ("gegen `done_days` des Harvesters") spricht gegen sie.
- Die Entscheidung kann damit schon jetzt faellig sein.
- Die Reihenfolge-Optionen stehen in Abschnitt 4.

### B-6 (mittel; Ehrlichkeit; Bilanz zu optimistisch gerahmt): Die fm8-Zahl -81 % ist eine Funktion des Priors, keine Dauer

Die Zahl -81 % / "voll 2027-08-22" steht in Abschnitt 0 und in der Doppelausweis-Tabelle neben den anderen Dauern
(Z. 44-46, 370, 392). Sie gilt nur, wenn der volle Roh-Prior 0,03 die Beta-Neutralisierung ueberlebt.

- **Gleich schnell wie der Roh-IC** waere fm8 bei Prior 0,0131 (44 %).
- Bei Prior 0,02 braucht es 51 Wochen, bei 0,015 dann 91 Wochen.
- Es gibt einen konkreten Grund, den neutralisierten Prior kleiner anzusetzen: Markt-Persistenz erzeugt mechanisches
  Querschnitts-Momentum in Hoehe von IC_prior (DEC-77).
- Die Bilanz fuehrt den Prior als UNBELEGT (richtig, Z. 194). Die Zahl sollte aber als Kurve n(Prior) mit Break-even
  erscheinen, nicht als einzelnes Datum.

Kontext: DEC-88 hatte 0,03 auch fuer die fm8-Bedingung gesetzt, dort aber als Zusatzbedingung neben dem Roh-IC. Ein
Beleg fuer eine Primaerstatistik ist das nicht.

### B-7 (mittel; Ehrlichkeit, Pruefpunkt 6): Was Recording-first fuer das Programm heisst, wird nicht ausgesprochen

Option 1 nennt "1,5..5 Jahre Wartezeit ohne Urteil" (Z. 439). Das untere Ende stammt nur aus nicht bindenden Lesarten
(W2/measured; fm8 mit UNBELEGTEM Prior).

**Unter bindender Nuisance und zentralem Prior** sind die Daten erst zu diesen Zeitpunkten vollstaendig (Registrierung,
Positivkontrolle und Lauf kommen noch hinzu):

- A4: 2029-06-29, und nur wenn prior >= 1,24 sigma_w (beides UNBELEGT);
- VRP: 2030-04-04;
- A3: 2031-05-11;
- A1: ohne theta-Beleg nie.

**Unangenehme Folgen, die hineingehoeren:**

1. 3.0 liefert bei reinem Recording-first vor Mitte 2029 keine Alpha-Aussage, unter bindender Lesart erst 2030/31.
2. Die gemeinsame Power am Prior betraegt 0,64. Selbst ein echter Effekt in Literaturgroesse wird also mit 36 %
   Wahrscheinlichkeit verfehlt, auch nach dem Warten.
3. Die PK-Klausel DEC-94 (5) laesst die Positivkontrolle scheitern, wenn die SD der Kontrollwelt mehr als 10 % ueber der
   Power-Zeile liegt. Ist die Faktor-Vol im kuenftigen Fenster hoeher als in W1-stress, endet das Warten in einer
   gescheiterten Positivkontrolle.
4. Die Literatur-Priors (Stichproben 2017-2022) koennen bis 2031 erodiert sein (L-16, REZENZ).

### B-8 (niedrig; Bilanz leicht zu optimistisch): Die A1-Schlagzeile nutzt den W1-Spread, nicht den strengsten

Betroffen sind Z. 36-37, 371 und 434. W1-Spread 175,8 ergibt 2030-01-06. Der strengste bekannte Spread (Nuisance
2022-04..2024-06: 145,3) mit bindender SD ergibt 124,0 Wochen und damit 2031-07-20 `[R:review_check.py, A1]`. Z. 236-238
legt das offen. Die Schlagzeile sollte die Spanne 2030-01..2031-07 nennen.

### B-9 (niedrig; Bilanz eher konservativ): Das c der HF-RV-Praemie ist vermutlich kleiner als angenommen

Die Rechnung:

- Das RV-Messrauschen (~34 % der Praemienvarianz, REVIEW_H27 B-1) ist bei 30-Tage-Summen unabhaengiger Tagesfehler
  dreiecksfoermig autokorreliert, mit c ~ 30.
- Entfernt man es, sinkt das c der Rest-Praemie, zur Illustration [abg., UNBELEGT] auf (18,6 - 0,34 x 30) / 0,66 = 12,7
  (Konsens) bzw. 27,2 (Regel).
- HF mit Konsens-c laege dann bei ~200 statt 292 Tagen.

Die Bilanz haelt c konstant und fuehrt "ihr c" als UNBELEGT. Das ist korrekt und streng. Der Richtungshinweis gehoert
nach 2.3, damit B-3 SD UND c der HF-Praemie misst.

### B-10 (niedrig bis mittel; Teil B, Pruefpunkt 4)

Die Liste ist umsetzbar (Strom, Symbole, Aufloesung, Zeitraum, Zweck und Volumen sind plausibel). Auch "irreversibel"
ist richtig gesetzt: B-1, B-2 und B-5 sind irreversibel, B-3 und B-4 nachladbar. Es fehlt Folgendes:

- (a) **Neue Zeile, Prioritaet 1, eilig:** eine `done_days`-Inventur fuer H-26. Je Tag und Symbol der DONE-Status von
  `deribit/dvol` und `deribit/publicTrade` seit 2025-08-01, mit Herkunft (Live oder REST-geheilt). Das ist eine reine
  Vollstaendigkeitspruefung und nach E3 erlaubt. Sie entscheidet zwischen den Lesarten (a) bis (d) aus B-5.
- (b) Die Inhaltsprobe der Options-Ticker (B-5) ist ebenso irreversibel wie B-2(a); im JSON steht `irreversibel: true`,
  in der Tabelle fehlt der Vermerk. Sie gehoert in dieselbe Probe wie B-2(a) und damit auf Prioritaet 2. Fehlen
  Bid/Ask (wie bei WP-7 `bid1Price` im Delta-Strom), ist jeder weitere Tag fuer A5/H-26b verloren.
- (c) Das Delisting-Register (Bybit-Announcements, DEC-67 E5 / WP-12) laufend fortschreiben. Der Instruments-
  Schnappschuss aus B-1 liefert den Status, nicht das Ankuendigungsdatum. Das gehoert als Unterpunkt zu B-1.
- (d) B-1 ist optionsneutral und sollte sofort laufen. Seine Nutzung fuer blinde A3/A1-Laeufe haengt aber an B-2.
- (e) Ein Binance-Aequivalent zu DVOL ist fuer die Power nicht noetig. Engpass sind Praemienvariation und RV-Rauschen,
  nicht die IV-Messung. Dass es fehlt, ist richtig.

### B-11 (niedrig; fehlende und scheinbare Hebel, Pruefpunkt 3)

| Hebel | Status | Bewertung |
|---|---|---|
| fm8 auf W1/W2 (B-1) | fehlt | einziger Weg zu Power 0,80 ohne Warten und ohne Regelaenderung; braucht einen Prior-Beleg |
| laengere VRP-Nuisance-Periode (2021-03..2026-06, nur SD/c) | fehlt | Die Batch-Means-Schaetzer der c-Regel P-3 haetten dann ~21 statt 12 Bloecke (L 90), die Regel streut weniger. Zur Illustration bei c 20,3 (MC-Median der Regel bei wahrem 18,6, REVIEW_H27 B-2): 484 statt 672 Tage. Die Richtung ist ex ante offen. Zulaessig nur mit vorab fixierter Regel (Periode = alle nicht blinden Daten bis 2026-06-30, bindend in beide Richtungen) und einer DEC zu DEC-95 E2 / DEC-96 E1; sonst Nuisance-Shopping. |
| Varianz-/Log-Form (Varianz-Swap) | nicht erwaehnt | Schon in der H-27-FEASIBILITY gerechnet: S3 724 Tage, S2 GL012, also kein Hebel. DVOL ist selbst ein modellfreier Varianz-Swap-Index; eine Replikation aus Options-Quotes gibt es erst ab 2026-06-16 (ohne Vorperiode). |
| A2 mit Deribit-Tagesverfaellen (V-5a) | fehlt | 365 Ereignisse je Jahr, aber ohne Placebo-Slots (jeder Tag ist Verfallstag). Das waere ein OI-Dosis-Design; Prior UNBELEGT. |
| mehr VRP-Underlyings ueber eigene IV aus `deribit/tickers` | Bilanz: "kein Datenweg" | scheinbar: keine Vorperiode, hohe Korrelation, Prior UNBELEGT |
| historische A3-Fenster vor 2024-07 (Roh-IC versiegelt, ungesehen) | fehlt | scheinbar: C.18 REZENZ ("Historie vor 2024-07 ist Aera-Profil", PRD Z. 483) schliesst sie aus. Ginge nur ueber eine Regelaenderung (Option 4, Richtung Testbarkeit), zudem ueberlappt die Literaturstichprobe und es gibt Vorwissen. Der Nutzer wird fragen, warum der Panel-Bestand von fuenf Jahren nicht hilft; die Antwort gehoert in die Bilanz. |
| Kalibrierungs- und Schaetzerwahl nach GL-032..034 (W2 statt Maximum, Konsens-c, oberer Bandrand, W2-Spread) | etikettiert | Datenschnueffel-Typ; die Bilanz kennzeichnet ihn korrekt |
| Komposit aus mom1 und rev_gap | fehlt | neue Hypothese, Prior UNBELEGT; nicht quantifizierbar |

### B-12 (niedrig; Wortlaut)

- (a) Z. 50-51 und 378: "A2 Monatsverfaelle mit 3-Jahres-Fenstern" dient als Beispiel fuer "nur durch DEC-94". Das
  Design braucht zusaetzlich den Verzicht auf REZENZ (Z. 307-308) und ist deshalb auch unter P-1 ohne Regelaenderung
  nicht zulaessig.
- (b) Z. 462: "programmweite Aenderung der c-Regel P-3". P-3 ist eine Regel der H-27-Herleitung. Programmweit gilt nur
  DEC-94 (4), und das legt keinen Schaetzer fest. Ein Nachfolger fixiert seinen eigenen Schaetzer; ein weicherer nach
  GL-034 traegt das Etikett. Inhaltlich aendert sich nichts.
- (c) Z. 202: Siehe B-1. "Nicht zulaessig" gilt fuer die registrierte Fassung, nicht fuer die Fenster.
- (d) A4: Die sigma_w-Messung 2026-06-16..2027-06-16 liegt im Blindbereich. Der Wedge ist keine BTC-RV, haengt aber
  ueber Funding und Basis mit der Vol zusammen. Den E3-Zuschnitt fuer A4 ausdruecklich klaeren.

## 3. Pruefpunkte 1-6 (Kurzantworten)

1. **Arithmetik.**
   - Alle Zeilen sind reproduziert (Abschnitt 1).
   - Die Nuisance je Zeile steht in der Tabelle von Abschnitt 1. Bindend ist stress W1, die c-Regel ist max(1, c_hat)
     nach P-1, bei H-27 die Regel P-3.
   - Startdaten und Kalenderrechnung stimmen.
   - Der Ein-Fenster-Vergleich ist richtig gerechnet, aber falsch gelesen (B-3).
2. **Hebel.**
   - Symbole, zweite Boerse, BTC+ETH, Monatsziele und A1-Hedge sind richtig.
   - fm8 -81 % ist eine Illustration (B-6).
   - HF-RV ist UNBELEGT und beim c eher konservativ (B-9).
3. **Fehlende Hebel.**
   - Ein realer Weg ohne Regellockerung und ohne Outcome-Kenntnis fehlt: fm8 auf W1/W2 (B-1).
   - Die uebrigen fehlenden oder scheinbaren Hebel stehen in B-11, darunter REZENZ als Grund, warum die Historie vor
     2024-07 nicht hilft, und die Nuisance-Periode der VRP als Messung mit Shopping-Risiko.
4. **Teil B.**
   - Umsetzbar, die Prioritaeten B-1 bis B-3 sind richtig.
   - Es fehlt die eilige H-26-Inventur. Die B-5-Probe gehoert zu B-2(a), das Delisting-Register ist zu ergaenzen (B-10).
5. **Teil C.**
   - Neutral, mit Richtung und Kosten; die Fehlerraten der Option 4 sind richtig (alle neun Zeilen nachgerechnet).
   - Es fehlen der Beleg-Weg (B-1), die E3-Sequenzbedingung (B-2) und die H-26-Reihenfolge (B-5).
   - "Einmal-Gut" ist ueberzeichnet (B-4), "kein Zeitfresser" falsch gelesen (B-3).
6. **Ehrlichkeit.**
   - Die UNBELEGT-Punkte sind vollstaendig gefuehrt (Abschnitt 5 der Bilanz).
   - Die Konsequenz "keine Alpha-Aussage vor 2029/2031" fehlt in klarer Form (B-7).
   - Die Schlagzeilen zu fm8 und A1 sind guenstig gerahmt (B-6, B-8).

## 4. Reihenfolge H-26 gegen VRP-Nachfolger (Pruefpunkt 5)

| Option | Inhalt | Kosten | Reversibilitaet |
|---|---|---|---|
| R-1 H-26 bleibt gesperrt bis zur Richtungsentscheidung | kein Lauf; die H-26-Fenster stehen per Formel fest und bleiben rechenbar | H-26-Verdikt, A5-Bedingung E.6 (c) und der Ausloeser R3-K-37 verschieben sich | **voll reversibel**: H-26 kann spaeter auf denselben Fenstern laufen, ein VRP-Nachfolger kann weiter ab 2026-07-01 starten |
| R-2 Nachfolger zuerst registrieren, danach H-26 | braucht eine DEC, die E3 mit der Registrierung aller Fenster-Nutzer enden laesst statt mit dem Lauf; das Design des Nachfolgers muss in Wochen stehen (Tagesschluss-Variante sofort, HF-Variante erst nach B-3) | K/Familie; Zeitdruck beim Design; das H-26-Ergebnis ist vor dem Nachfolger-Urteil sichtbar (Torpfosten-Versuchung, Registry append-only) | teilweise |
| R-3 H-26 jetzt (2.0-Lesart) | verbraucht den H-26-Datenabschnitt | Der Nachfolger startet nach dem H-26-Datenende. Lesart (a): 2026-11-17, voll 2030-08-21 (+139 Tage). Lesart (c): 2027-04-19, voll ~2031-01-21 (+292 Tage) | irreversibel |
| R-4 Lesart (d): voller Backfill zaehlt | H-26 auf 2025-08..2026-01, keine Kollision | Lesart in Richtung frueheres Testen, gewaehlt nach Kenntnis der Kollision (Etikett); PRD Z. 388; Lueckenlosigkeit von `publicTrade` UNBELEGT | irreversibel nach dem Lauf |
| R-5 H-26 nicht mehr verfolgen | neue 3.0-DEC (die 2.0-Akte bleibt unveraendert) | der einzige registrierte Strategie-Pfad faellt weg; A5 bleibt nach E.6 gesperrt | schwer reversibel |

**Am reversibelsten ist R-1** (Reversibelste-Option-Prinzip C.19; es betrifft keine Gate-Schwelle). R-1 sollte als
dokumentierter Default gelten, bis der Nutzer entscheidet. Die Inventur B-10 (a) sollte sofort laufen.

## 5. Auflagen

**Blockierend vor der Weitergabe an den Nutzer** (Aufwand: Text plus wenige Code-Zeilen, keine neuen Daten):

- **A-1 (B-1):** In 2.1 und Teil C den Beleg-Weg "neue A3-Hypothese, fm8 primaer, W1/W2" aufnehmen:
  - Break-even-Prior 0,020 (P-1) / 0,027 (A3-Praxis);
  - die Bedingungen 1-5;
  - Z. 202 praezisieren.
- **A-2 (B-2):** Die E3-Sequenzbedingung in die Praeambel von Teil C und in Option 1 aufnehmen:
  - jedes A3/A1-Datum vor einem registrierten VRP-Lauf markieren mit "erreichbar nur nach VRP-Lauf oder nach
    programmweiter DEC zum Siegel-Zuschnitt";
  - den Zuschnitt als Regel-Option mit Richtung ausweisen.
- **A-3 (B-3, B-4):** Beide Strukturbefunde korrigieren (Z. 56-60, 421-427, 468, 496):
  - Zwei-Fenster-Regel: +23..26 % bei gleicher Rate und Power;
  - "Einmal-Gut je Zeitabschnitt".
- **A-4 (B-5, B-10 (a)):** H-26 neu fassen:
  - die Lesarten (a) bis (d) mit Daten;
  - die Optionen R-1 bis R-5 mit Kosten und Reversibilitaet;
  - Dringlichkeit, denn die Entsperrung ist womoeglich schon erreicht;
  - die Inventur als neue Zeile in Teil B mit Prioritaet 1.

**Nicht blockierend:**

- **A-5:**
  - fm8 als Kurve n(Prior) darstellen (B-6);
  - die Recording-first-Konsequenz woertlich in Abschnitt 0 und Option 1 (B-7);
  - die A1-Spanne in der Schlagzeile (B-8);
  - den HF-c-Richtungshinweis (B-9);
  - B-10 (b) und (c);
  - die Hebel aus B-11 in 2.8 (mit REZENZ-Erklaerung und S2/S3-Verweis);
  - die Wortlaute aus B-12.

## 6. Empfehlung an den Orchestrator: wie die Vorlage an den Nutzer gehen soll

1. **Teil A unveraendert uebernehmen** (zugestimmt). Die Auflagen A-1 bis A-4 vorher in die Akte einarbeiten; das ist
   kleiner Aufwand ohne neue Rechnung auf Daten.
2. **Fuer den Nutzer eine kurze Seite** im Stil von `STAND_2026-10-18.md`, ohne Jargon, mit drei Kernsaetzen:
   - (a) Was ist unter bindender Lesart wann testbar? A4 fruehestens 2029-06 (bedingt), VRP 2030-04, A3 2031-05, A1
     nie ohne theta. Dazu: gemeinsame Power 0,64, E3-Reihenfolge.
   - (b) Was ist sofort testbar, aber nur mit einem Beleg? A3-fm8 auf W1/W2 ab Prior 0,020; A1 ab theta 0,99 auf
     W1/W2 bzw. mit Belegen auf kuenftigen Fenstern.
   - (c) Was ist ohne Regelaenderung nicht testbar? Die Historie vor 2024-07 (REZENZ); jedes Fenster ueber 12 Monate
     fuer H-27 (DEC-96 E2) nur als neue Hypothese.
3. **Optionstabelle** mit Richtung, Kosten und Falsch-Positiv-Rate:
   - Recording-first inklusive E3-Reihenfolge;
   - Beleg-Weg (fm8-Prior, theta, VRP-Volltext, V-5c), mit vorab fixierter Regel, welche Quelle als Prior zaehlt -
     sonst wird die Quellenwahl selbst zur Gabelung;
   - Ereignis- und Einheiten-Designs;
   - HF-VRP;
   - Regel-Optionen nur als Preisschild mit DEC-94-Etikett, nicht als Menue (DEC-93 E3, DEC-97);
   - Pause.
4. **H-26-Reihenfolge als eigene, eilige Nutzerfrage** mit dem Default R-1 (dokumentiert, nicht still entschieden;
   Autonomie-Protokoll 3).
5. **Sofort und optionsneutral**, ohne Nutzerentscheidung:
   - B-1 (Panel-Strom inklusive Delisting-Register);
   - die Inhaltsprobe B-2(a) zusammen mit B-5;
   - die H-26-`done_days`-Inventur;
   - die Siegel bleiben geschlossen, keine Registrierung.
6. **Die E3-Zuschnittsfrage (B-2) ist eine Programmregel.** Sie ist vor dem ersten Kandidaten zu entscheiden, der sie
   braucht (Sequenz-Zwang), mit Richtung und Etikett.

## 7. Ergebnisblindheit dieses Reviews (Offenlegung)

**Gelesen:**

- `runs/wp13a_20261012_v5e/wp13a_prelaunch.json`, nur die Teilbaeume `beta_control_method_study`,
  `beta_control_recommended_high_rep`, `noise_floor_and_threshold` sowie die Schluessel `market_symbol` und
  `beta_window_weeks`;
- `herleitung_a1/feasibility.json` (power.inputs, Spread-Mittel der Formationsseite, Hedge-R^2);
- `herleitung_h27/feasibility.json` (nuisance BTC/LEG_MEAN S1, Priors, Nullwelt bei 365);
- die Markdown-Akten (Verfassung, PRD-Ausschnitte, decisions, gate_log, STAND, UEBERGABE, REVIEW_H27, H-27-FEASIBILITY
  per grep, 2.0-Registry H-26).

**Nachgefahren:** Die Kopie des Census-Skripts laedt wie die Bilanz `wp7_report.json` und gibt nur K, SD_null, N_eff,
sigma_LS und die Funding-Autokorrelation aus. Geschrieben wurde nur nach `scratchpad/`.

**Nicht geoeffnet:** Siegeldateien, WP-10(A)/(A2)-Dateien, `pair_corr_*`, WP-7-Serien.

**Nicht getan:** kein Laden von Panel, DVOL oder Trades, kein Katalogzugriff, kein Netz, keine Outcome-Groesse. Die
H-26-Daten sind reine Kalenderrechnung aus DEC-96 und der Registry-Formel. Vorwissen wurde nicht verwendet.

## 8. Skripte (`scratchpad/bilanz_review/`)

| Datei | sha256 | Inhalt |
|---|---|---|
| `review_check.py` | `b3bdc074...a1bb3fdf` | Nuisance-Lesung mit Waechter; ganzzahlige C10-/DEC-52-/A3-Praxis-Dauern mit `power_p1`; Daten; fm8 auf W1/W2; Ein- gegen Zwei-Fenster bei gleicher Power; A4-Verfaelle; H-26-Lesarten |
| `review_check.json` | `92e8c17a...b3a39f9c` | Ergebnisse (keine Outcome-Groesse) |
| `rerun/census_copy.py` | `21ed2e70...8797b1de` | Kopie von `bilanz_census.py`, Ausgabe nach `scratchpad/` umgeleitet; JSON identisch bis auf das Feld `skript` |
