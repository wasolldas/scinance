# H-27 (VRP auf DVOL-Backfill, W3/W4) - adversarisches Review des Befunds "GL-012 vor der Registrierung"

> Zweiter, adversarischer Gutachter, Stand 2026-10-17. Gegenstand: `state/herleitung_h27/` (FEASIBILITY.md,
> DATENPROBE.md, KONTAMINATION.md, feasibility.json) und die Skripte unter `scratchpad/h27_herleitung/`; Auftrag
> `SPEC_H27_herleitung.md` inkl. FORTSETZUNG. Massstab: Verfassung, DEC-51/52/94/95/96 (mit Nachtraegen), GL-032/033,
> `src/bybit_edge/research/power_p1.py`. Nichts hier ist registriert oder beschlossen; entscheiden darf nur der
> Orchestrator. Eigene Skripte unter `scratchpad/h27_review/` (Kuerzel `[R:<datei>]`, sha256 in Abschnitt 6).
> Ergebnisblindheit dieses Reviews: Abschnitt 5 (nur Vorperiode, kein Praemienmittel, kein DVOL-Mittel, nichts ab
> 2024-06-01 ausser Abdeckung). Kuerzel wie in FEASIBILITY.md: VP = Vol-Punkte, [sek] Sekundaerbeleg.

## 0. Urteil

**ZUSTIMMUNG MIT AUFLAGEN** zum Befund "H-27 ist nach DEC-96 E2 GL-012 vor der Registrierung; kein Urteil ueber die
Volatilitaets-Risikopraemie".

- Alle tragenden Zahlen wurden mit eigenem Code reproduziert (Abschnitt 1): SD 18,60, ACF, c-Regel 28,17, Nullwelt-J
  2,08, Prior 9,47 (Band 7,00..13,72), Zuordnung L 6/9/12 = GL012/GL012/GL012 unter P-1 und unter der A3-Praxis.
- Kein Fehler in Richtung Testbarkeit gefunden. Die Abweichungen, die das Review findet, liegen in Richtung Strenge
  (c-Regel, nu der Nullwelt) oder sind neutral (Prior-Niveau). Auch mit dem Konsens-c (18,6 statt 28,2) bleibt die
  Referenz bei L = 12 GL012 (Power 0,73).
- Die einzige Designwahl mit materiellem Potenzial ist eine Hochfrequenz-RV (B-1). Sie reicht nur zusammen mit einer
  zweiten Lesart in Richtung Testbarkeit (Konsens-c) und waere jetzt eine Wahl nach Kenntnis der Feasibility. Sie
  fehlt in der Gabelungstabelle der Herleitung; das ist die Hauptauflage.
- Die Auflagen (Abschnitt 4) betreffen die Vollstaendigkeit von Gabelungen und Offenlegung sowie den Wortlaut. Keine
  aendert die Zuordnung.

## 1. Nachgerechnete Zahlen (Herleitung gegen Review)

Die Herleitung wurde mit eigenem Code nachgerechnet. Unabhaengig gewaehlt: Lader, IV-Stunde aus `ts_exchange_ms` statt
aus dem Payload-Zeitstempel, Summen ueber Kalenderindex und kumulierte Summen, eigene Kernschaetzer, eigene Nullwelt.

| Groesse (BTC, Vorperiode IV-Tage 2021-03-24..2024-05-01, Preise <= 2024-05-31) | Herleitung | Review | Beleg |
|---|---|---|---|
| n / Luecken | 1.135 / 0 | 1.135 / 0 | [R:nuisance_review.py] |
| SD der Praemie S1 (VP) | 18,60 | 18,597 | dto. |
| ACF Lag 1 / 10 / 20 / 30 / 60 / 120 | 0,955 / 0,514 / 0,107 / -0,155 / 0,054 / 0,012 | identisch | dto. |
| c Bartlett B 60 / 90 / 120 | 16,9 / 17,5 / 17,8 | 16,9 / 17,4 / 17,8 (eigener Kern = `power_p1`) | dto. |
| c Batch-Means L 60 / 90 / 120 | 19,2 / 28,2 / 15,2 | 19,2 / 28,2 / 15,2 | dto. |
| **c nach Regel P-3 (max aus sechs)** | **28,17** | **28,17** | dto. |
| weitere c-Schaetzer (nur Review) | - | ACF-Summe K 29/45/60/90/120: 20,6/17,1/16,5/19,5/18,6; Parzen B 60..180: 18,2..18,5; ueberlappende Batch-Means L 60/90/120: 17,8/18,7/20,1; stat. Bootstrap 30/60/90: 15,7/15,8/16,9; Fenster-exakt n 365 (Lags <= 120): 18,4 | dto. |
| Monatsvariante SD / ACF 1 | 18,70 / -0,16 | 18,70 / -0,164 | dto. |
| rms RV_fwd30 BTC / ETH | 61,55 % / 79,32 % | 61,55 % / 79,32 % | dto. |
| SD S1 ETH / S3 BTC / Korr. BTC-ETH S1 | 25,10 / 0,304 / 0,83 | 25,10 / 0,304 / 0,83 | dto. |
| Nullwelt SV (phi 0,996, eta 0,06, nu 4,5): J (S1, Referenzniveau) | +2,09 | +2,08 +- 0,05 | [R:nullworld_review.py] |
| SE_null n 184 / 274 / 365 | 5,64 / 4,65 / 4,17 | 5,75 / 4,83 / 4,03 (Monte-Carlo-Streuung bei t(4,5)) | dto. |
| c_null; J bei nu 6 / 15; J S3 | ~27; 1,49 / 1,12; 0,059 | 26,9; 1,57 / 1,10; 0,058 | dto. |
| Prior: IV 0,75 -> RV 0,650, 10,0 VP, ln 0,1431 | wie links | identisch | [R:power_review.py] |
| Prior S1 pi-2 zentral / Band / pi-1 | 9,47 / 7,00..13,72 / 10,48 | 9,469 / 6,999..13,722 / 10,480 | dto. |
| Zuordnung L 6 / 9 / 12: Fenster-Power | 0,366 / 0,477 / 0,575 | identisch (mit Herleitungs- **und** Review-Inputs) | dto. |
| DEC-52-Gate Produkt (exakt, Bericht) | 0,105 / 0,223 / 0,359 (0,222 / 0,359 / 0,491) | identisch | dto. |
| MDE80 Fenster / Gate | 18,1 / 14,8 / 12,85; 17,4 / 14,2 / 12,3 | identisch | dto. |
| A3-Praxis Power / Gate | 0,118 / 0,184 / 0,257; 0,030 / 0,083 / 0,164 | identisch | dto. |
| Regime P-1 / A3 | GL012 x 3 / GL012 x 3 | GL012 x 3 / GL012 x 3 | dto. |
| Tage je Fenster fuer C10 (zentral, nur Nuisance) | 672 | 672 | dto. |
| Konvention Panel-close = letzter Trade vor 00:00 UTC | 12/12 | 12/12; zusaetzlich Panel-high/low = Trade-Max/Min 12/12 | [R:conv_review.py] |
| Gleichstand am letzten Zeitstempel 2022-11-09 | 37 / 86 Trades | 37 / 86 Trades mit **16 / 15 verschiedenen Preisen** | dto. |

Folge der letzten Zeile: Die Reihenfolgeregel bei Gleichstand ist ergebnisrelevant. Damit ist der offene Punkt der
Herleitung bestaetigt (FEASIBILITY 6, letzte Zeile); er gehoert in jede Lauf-Spezifikation.

## 2. Befunde

### B-1 (mittel; Vollstaendigkeit der Gabelungen; Richtung Testbarkeit): Die Wahl des RV-Schaetzers ist nicht als Gabelung ausgewiesen

Pruefpunkt 4 fragt nach einem anderen RV-Schaetzer. FEASIBILITY 5 rechnet diese Gabelung nicht. DATENPROBE A.2 nennt
Spannweiten-Schaetzer nur als Stufe-2-Vorlage. Das Review rechnet sie nach [R:nuisance_review.py],
[R:noise_share.py], [R:power_review.py].

**Spannweiten-Schaetzer aus derselben Tageskerze (Parkinson, Garman-Klass, Rogers-Satchell): kein Gewinn.**
- SD der Praemie: S1 19,9 / 20,9 / 22,4 gegen 18,6 bei close-to-close; S3 0,288 / 0,291 / 0,305 gegen 0,304.
- Die SE in S3 nach Regel P-3 sinkt nur um 4,6 % (Parkinson); mit Bartlett-c wird sie groesser.
- Grund (gemessen, nur RV der Vorperiode): Das taegliche Rauschmass kappa = E[x^2] / E[x_s x_{s+L}] (L 2..5) betraegt
  bei close-to-close 4,8, bei Parkinson aber 3,3. Unter Brownscher Bewegung waeren es fuer Parkinson 1,41. Die
  Tagesspanne eines Perps traegt Dochte.
- Zusaetzlich ist rms(RV_pk) / rms(RV_cc) = 1,088. Das ist eine Niveau-Verzerrung; ein Spannweiten-Design braeuchte ein
  eigenes J.
- Die Definitionsgleichheit waere gegeben (Panel-high/low = Trade-Max/Min, 12/12). Der Schaetzer hilft trotzdem nicht.

**Hochfrequenz-RV (z. B. 5-min-Renditen aus `bybit/publicTrade`): der einzige Hebel mit materiellem Potenzial.**
- Messrauschen von RV_cc (Delta-Methode, kappa 4,8): ~10,9 VP, das sind ~34 % der Praemienvarianz.
- Rauschfrei laege die SD bei ~15,1 statt 18,6. Das ist eine Schaetzung (UNBELEGT). Die SV-Nullwelt mit nu 6 bestaetigt
  die Groessenordnung (Rausch-SD 11,2 VP). Die rauschfreie SE_null betraegt dort nur 1,39 (n 365), die Nuisance bindet.
- Zuordnung bei L = 12, zentraler Prior: mit c nach P-3 (28,2) SE 4,18, Power 0,73 -> **GL012**.
- Nur zusammen mit dem Konsens-c ~18,6 ergibt sich SE 3,40, Power 0,87, Gate 0,87 -> **C10**. Unter der A3-Praxis
  bleibt es GL012 (Etikett "zugelassen nur durch DEC-94").
- Bei L = 9 bleibt es GL012 (0,78).
- Das sind zwei Lesarten in Richtung Testbarkeit zugleich, also das A1-Gabelungsmuster (DEC-93 H-1). Die Trade-Daten
  der Vorperiode (BTCUSDT 2021-03..2024-05, laut DATENPROBE A.2 ~29 GB) sind nicht geladen.

**Wuerdigung.**
- Die Schaetzerwahl war vor jeder Zahl fixiert (DATENPROBE A.2 und P-9, 2026-10-13). Sie war vom Auftrag gedeckt
  (FORTSETZUNG: "Tagesschluesse").
- Der Grund "Datenvolumen" ist mit DEC-96 teilweise entfallen: W1/W2 entfallen, und die W3/W4-Schluesse kommen ohnehin
  aus vollen `publicTrade`-Tagen.
- Ein Wechsel jetzt faellt nach Kenntnis der GL-012-Feasibility, gilt nur fuer diesen Kandidaten und wirkt zu seinen
  Gunsten. Nach DEC-93 E3 und DEC-92 E2 ist das eine Torpfosten-Verschiebung.
- Zulaessig waere er nur als neue Hypothese mit eigenem K (DEC-58 E2), mit dem Etikett "beschlossen nach Kenntnis der
  H-27-Feasibility (GL-012)" und mit der hier gezaehlten Variante in K.
- Weil W3/W4 vollstaendig blind sind, ist das Restrisiko Selektion, nicht Ergebniswissen.
- Ueber den Ausweis hinaus empfiehlt das Review nichts; die Entscheidung liegt beim Orchestrator.

### B-2 (niedrig; Richtung Strenge; fuer die Zuordnung nicht relevant): c = 28,2 ist das Maximum eines einzelnen unsicheren Schaetzers

- Der Wert 28,2 stammt allein aus Batch-Means mit L 90, also aus 12 Bloecken. Die uebrigen Schaetzer des Reviews
  liegen bei 15,2..20,6: ACF-Summen, Bartlett, Parzen, Batch-Means mit L 30/60/120, ueberlappende Batch-Means mit
  L 60..120, Bootstrap. Ausnahme sind ueberlappende Batch-Means mit L 184 (23,5), bei denen die Reihe nur rund sechs
  Fensterlaengen umfasst. Der Konsens (getaperte ACF-Summe) ist ~18,6.
- Monte-Carlo-Pruefung der Regel [R:nuisance_review.py, `mc_rule_bias`]: Gauss-Reihen mit n 1.135 und der gemessenen
  ACF, wahres c 18,6. Die Regel "max aus sechs" liefert im Median 20,3 (q10 / q90: 14,0 / 29,9); P(Regel >= 28) =
  14 %. Die Regel ist also nach oben verzerrt, wie vorab mit "Richtung Strenge" etikettiert.
- Zur Theorie: Eine reine 30-Tage-Ueberlappung ohne Rueckkopplung ergibt c -> h = 30 (Dreiecks-ACF bis Lag 29). Die
  SV-Nullwelt gibt 26,9, weil die IV dort nicht auf das Renditerauschen reagiert.
- Real ist die ACF ab Lag 25 negativ (-0,155 bei Lag 30): DVOL reagiert auf genau die Renditen, die im Ziel-Monat der
  frueheren Praemie liegen. Eine GARCH-Nullwelt, in der die IV auf Renditen reagiert, gibt c_null 17,4
  [R:nullworld_review.py]. Das bestaetigt den Mechanismus. Ein theoretisches c ~ h ist fuer die reale Statistik zu
  hoch.
- c ist an der Teststatistik gemessen (DEC-94 (4)): Der Varianzfaktor der Tagesreihe ist der Faktor des
  Fenstermittels. Die endliche Fensterlaenge (n 184..365) aendert ihn um weniger als 3 % (18,1..18,4).
- Folge: Mit c 18,6 bleibt die Referenz GL012 (L 12: SE 4,20 gegen die C10-Grenze 3,81; Power 0,73; Gate 0,62). Das c
  wirkt nur in den Gabelungen. Dort sollte stehen, dass der bindende Wert auf einem 12-Block-Schaetzer beruht.

### B-3 (niedrig; Hinweis fuer jedes kuenftige S1-Design): Jensen-J haengt stark vom Modell ab

- SV-Nullwelt mit nu 4,5 / 6 / 15: J = 2,08 / 1,57 / 1,10 VP.
- GARCH(1,1)-t per ML auf den Vorperioden-Renditen (Persistenz am Rand 0,9999, nu 3,2): J 8,7 VP, SE_null 5,3 (n 365).
- Als Nullwelt ist das GARCH-Modell unplausibel: Seine taegliche Null-SD (21,1) liegt ueber der realen Praemien-SD
  (18,6). Es zeigt aber, dass die Unsicherheit von J die Groessenordnung des Priors erreicht (C.4).
- nu 4,5 ist als "konservativ" vertretbar: Die Daten-Kurtosis (Leave-one-out-standardisiert) betraegt 6,7. Simuliert
  ergibt nu 6 den Wert 6,1 +- 1,9, nu 4,5 den Wert 14,6 bei sehr schiefer Verteilung. Die Daten liegen eher bei
  nu >= 5, also bei kleinerem J und kleinerer SE_null (Richtung Strenge).
- Fuer die Zuordnung ohne Belang: Die Nuisance-SE bindet, und die Power rechnet mit dem Netto-Prior.

### B-4 (niedrig; neutral): Prior-Umrechnung richtig, zwei Praezisierungen

- Arithmetik bestaetigt: IV 0,75 -> RV 0,650 -> 10,0 VP und ln 0,1431. Auf 61,55 % ergibt das 9,47; Band 7,00..13,72;
  pi-1 10,48.
- (a) Die Bewertung auf dem rms-Niveau ist konsistent. Die gepoolte SD traegt ebenfalls ein rms-Niveau, und unter pi-2
  skalieren Prior und SE gleich. Auf dem Mittelwert-Niveau der Vol (mean/rms = 0,946) waere der Prior 8,96 (Richtung
  Strenge, weiterhin GL012).
- (b) Unter pi-2 mit konstantem l = ln(IV/RV) gilt E[IV^2] (1 - e^(-2l)) = 0,14. Das "IV-Niveau der L-1-Stichprobe" im
  Band ist also als rms-IV zu lesen, nicht als mittlere IV.
- Fuer Deribit-BTC 2017-07..2022-12 liegt eine rms-IV von 0,65 (oberer, C10-seitiger Prior-Rand) nach allgemeinem
  Vorwissen eher unterhalb des Plausiblen (Vorwissen, UNBELEGT; Zeitraum vor jedem Fenster). Der C10-Rand ist damit eher
  unwahrscheinlich als wahrscheinlich.
- Das Band bleibt UNBELEGT. Es ist als Unsicherheitsangabe plausibel, nicht als Konfidenzband. Die Quelle L-1 wurde nur
  sekundaer gesehen [sek]; vor jeder kuenftigen Nutzung ist sie im Original zu pruefen (wie in der Herleitung vermerkt).

### B-5 (niedrig; Offenlegung): KONTAMINATION.md ist in drei Punkten unvollstaendig

- (a) Abschnitt 1.1 ist fuer DEC-96 Nachtrag 1 und 3 nicht nachgefuehrt. Der Orchestrator hat im Blindbereich ab
  2026-07-01 Katalog-Metadaten von `bybit/publicTrade` gesehen: rows/Status, "rows zu klein" und die 582-s-Handelspause
  BTCUSDT am 2026-10-08. Das sind schwache Aktivitaets-Stellvertreter, wie die offengelegten Bytesummen, und gehoeren in
  die Liste.
- (b) Die Bytesummen 2026-07-01..10-16 (`catalog_check2.py`) waren fuer die Vollstaendigkeit nicht noetig; n und
  `hd.gaps` genuegen. KONTAMINATION stellt sie zudem gegen einen Median vor dem Blindfenster (~73 / ~82 gegen ~71 MB je
  Tag). Damit liegt eine Vergleichsaussage ueber die Aktivitaet im Blindfenster vor. Das ist korrekt offengelegt, sollte
  kuenftig aber vermieden werden; DEC-96 E3 erlaubt nur Zeilen, Luecken, Zeitstempel und Schema.
- (c) Residualrisiko: Der Sitzungs-Cache `scratchpad/h27_herleitung/hcache/raw/deribit/dvol/` enthaelt die
  DVOL-Stundenkerzen bis 2026-10-16. Darunter sind W1/W2 und die blinden W3-Tage, geladen von `dvol_probe.py`; Werte
  wurden nicht ausgegeben. Jeder spaetere Prozess kann sie ohne Netzanfrage lesen. Empfohlen: ein Vermerk in
  KONTAMINATION und das Loeschen der Cache-Partitionen ab 2024-07-01 (nur Cache, keine Primaerdaten). Die Entscheidung
  liegt beim Orchestrator.
- Ein Regelverstoss wurde nicht gefunden (Pruefpunkt 5).

### B-6 (niedrig; Dokumentation): Die Abweichung von der vorab fixierten Regel P-5 ist nicht ausgewiesen

- P-5 nannte als Kalibrierungsmomente: Mittel und SD von ln RV30 ueber nicht ueberlappende Bloecke, deren Lag-1-ACF und
  die Kurtosis.
- `nullworld.py` nutzt stattdessen die SD der ueberlappenden y, ACF 30 und ACF 90, die Kurtosis und das Niveau ueber mu.
  Das ist gleichwertig bis informativer: ACF 30 der ueberlappenden Reihe entspricht ungefaehr dem Lag-1-Wert der Bloecke.
- A-3 verlangt fuer Abweichungen eine Begruendung und die Gabelungs-Richtung; beides fehlt. Ohne Wirkung, weil ueberall
  die Nuisance-SE bindet.

### B-7 (Hinweis fuer jede kuenftige Registrierung): Lauf-SE und Power-SE passen nicht zusammen

- Der stationaere Bootstrap mit mittlerer Blocklaenge 30 / 60 Tage liefert c 15,7 / 15,8. Das liegt unter dem Konsens
  18,6; bei der Default-Blocklaenge von 4 Wochen waere es noch weniger.
- Eine Lauf-SE nach DEC-94 (4) waere damit gegenueber der Power-Zeile antikonservativ, solange die Blocklaenge nicht aus
  der gemessenen ACF fixiert wird (>= 90 Tage).
- Fuer GL-012 ohne Belang.

### B-8 (Hinweis): Selektions-K ist nicht fixiert

- z_max(K) = 1,52 (K 9) / 1,665 (K 12) / 1,85 (K 18). Ab K 12 bindet DEC-94 (7) statt z_krit 1,6449.
- Gerechnet wurden 3 Einheiten x 3 Beine, dazu die Monatsvariante und die c- und Prior-Lesarten; das liegt nahe K 12.
- Fuer GL-012 ohne Belang. Bei jeder Neufassung ist K als Zahl zu fixieren, inklusive der hier gerechneten Varianten.

### B-9 (Wortlaut, Pruefpunkt 6): Die Schlussfolgerung ist richtig, sollte aber das Design benennen

"GL-012 vor der Registrierung, kein Urteil ueber die VRP" folgt mechanisch aus DEC-96 E2. Der Wortlaut sollte wie in
GL-032/033 das Design nennen, die Gabelungen vollstaendig aufzaehlen (inkl. B-1) und festhalten, was nicht folgt.
Vorschlag fuer DEC/GL:

> H-27 (VRP, DVOL-Backfill, EV-0c) ist nach DEC-96 E2 **GL-012 vor der Registrierung** und wird nicht registriert. In
> der vorab fixierten Referenz erreicht keine Fensterlaenge L in {6, 9, 12} Monaten C10 oder DEC52. Die Referenz:
> S1 = Fenstermittel IV - RV_fwd30 aus 30 Bybit-Tagesschluessen minus Nullwelt-J, Bein BTC,
> SE = max(Nuisance mit c nach P-3, Nullwelt), Prior pi-2 zentral 9,47 VP aus BVRP 0,14 [sek].
> Bei L 12: Fenster-Power 0,575, DEC-52-Gate (Produkt) 0,359. Die A3-Praxis ergibt ebenfalls GL012. Zusaetzlich haengt
> die Zuordnung bei L 12 am UNBELEGTEN IV-Niveau der Literaturstichprobe (P-9). **KEIN Verdikt ueber die
> Volatilitaets-Risikopraemie**; die DROP-Zeile der Entscheidungsrelevanz greift nicht; H-26 (2.0) bleibt unberuehrt;
> keine Outcome-Groesse berechnet. Testbar waere H-27 nur unter Lesarten in Richtung Testbarkeit, jeweils nur unter P-1
> ("zugelassen nur durch DEC-94"), und keine davon ist beschlossen:
> (a) oberer Rand des Prior-Bands;
> (b) c ohne Batch-Means zusammen mit pi-1 oder dem oberen Rand;
> (c) Hochfrequenz-RV zusammen mit dem Konsens-c.
> Fenster ueber 12 Monate sieht DEC-96 E2 nicht vor.

## 3. Pruefpunkte 1-6 (Kurzantworten)

1. **Nuisance.**
   - SD 18,60, ACF und alle sechs Regelschaetzer sind reproduziert.
   - Als Punktschaetzung ist c = 28,2 zu konservativ (Konsens 18,6; MC: Regel-Median 20,3). Als vorab fixierte Regel
     ist der Wert korrekt (Richtung Strenge).
   - Die Theorie h = 30 gilt nur ohne IV-Rueckkopplung (SV-Null 26,9, GARCH-Null 17,4, real 18,6).
   - c ist an der Teststatistik gemessen (DEC-94 (4)).
   - Jensen-J reproduziert (+2,08), modellabhaengig (B-3).
   - Fuer die Zuordnung ohne Belang (B-2).
2. **Prior.**
   - Umrechnung 0,14 -> 10,0 VP / ln 0,1431 -> 9,47 auf 61,55 % ist richtig.
   - Das Band 7,0..13,7 ist als Annahme plausibel. Sein IV-Niveau ist als rms-IV zu lesen; der obere Rand ist eher
     unplausibel (B-4).
   - Die Bewertung auf dem rms-Niveau ist konsistent zur SD.
3. **Power und Zuordnung.**
   - Mit `power_p1.assign_regime` und `assign_regime_a3_practice` exakt reproduziert, sowohl mit den Inputs der
     Herleitung als auch mit den eigenen.
   - L 6 / 9 / 12: GL012 / GL012 / GL012 unter P-1 und unter der A3-Praxis.
   - Strengere Lesarten (Prior auf dem Vol-Mittel 8,96; unterer Rand 7,00) bleiben GL012.
   - Gabelungen der Herleitung bestaetigt: oberer Rand bei L 12 C10 (0,844; nur DEC-94); pi-1 0,65.
4. **Vorab begruendbare Designwahl im Rahmen von DEC-96?**
   - Nicht ueberlappende Monatsstatistik: schlechter. Weil die ACF negativ ist, gilt c_m = 1 ohne Gutschrift; SE 5,40
     gegen 5,17.
   - Spannweiten-RV: kein Gewinn (B-1).
   - BTC+ETH als S3-Bein: SE -2..-6 %, zudem ist der ETH-Prior UNBELEGT.
   - Fenster ueber 12 Monate: von DEC-96 E2 ausgeschlossen. Noetig waeren je Fenster 672 / 443 / ~290 Tage (Regel-c /
     Konsens-c / rauschfreie RV mit Konsens-c).
   - Hochfrequenz-RV: der einzige materielle Hebel, aber nur zusammen mit dem Konsens-c. Nach Kenntnis dieser
     Feasibility ist das ein Torpfosten, sofern nicht neue Hypothese (B-1).
   - Ergebnis: Keine einzelne, vorab begruendbare und zulaessige Wahl macht H-27 testbar.
5. **Ergebnisblindheit.** Code gelesen; kein Verstoss.
   - `h27_common` schneidet Preise bei 2024-05-31 und DVOL-Niveaus bei 2024-06-30 ab und prueft die Ausgaben mit
     `no_mean`.
   - `h27_series` schneidet vor jeder Rendite ab.
   - `nuisance.py` gibt nur Streuung, ACF, c und RV-Niveau aus.
   - `nullworld.py` nutzt nur RV.
   - `dvol_probe.py` laedt zwar alle Werte, gibt aber nur Zaehlungen aus; Betraege nur bis 2024-06-30, Stetigkeit nur bis
     2026-06-30, ab 2026-07-01 nur Schema und Zeitstempel.
   - `conv_check.py` nutzt nur Tage vor 2024-06.
   - Die JSON-Schluessel aller Ausgaben wurden maschinell gescannt [R:keyscan.py]: kein Mittel- oder Niveauschluessel von
     Praemie oder DVOL.
   - Offenlegungen in KONTAMINATION: drei Ergaenzungen noetig (B-5).
6. **Formulierung.** Inhaltlich korrekt; Praezisierung siehe B-9.

## 4. Auflagen (vor Uebernahme in DEC/GL; keine aendert die Zuordnung)

- **A-1 (B-1):** Die Gabelungstabelle in FEASIBILITY 5 um zwei Zeilen ergaenzen:
  - Spannweiten-RV: GL012;
  - Hochfrequenz-RV: mit Regel-c GL012, mit Konsens-c C10 bei L 12, nur unter DEC-94.
  Dazu die Datenlage (Trades der Vorperiode nicht geladen, UNBELEGT) und die Torpfosten-Lesart.
- **A-2 (B-2):** Bei c bindend 28,17 vermerken: beruht auf einem 12-Block-Schaetzer; Konsens 18,6; MC-Verzerrung der
  Regel. Keine Aenderung der Regel.
- **A-3 (B-5):** KONTAMINATION.md nachtragen:
  - die Orchestrator-Sicht auf die `publicTrade`-Metadaten im Blindbereich;
  - die Bewertung der Bytesummen;
  - den Cache mit blinden DVOL-Werten (Vermerk und Loesch-Empfehlung).
- **A-4 (B-6):** Die P-5-Abweichung mit Begruendung und Richtung dokumentieren.
- **A-5 (B-9):** Den Wortlaut von DEC/GL mit Design-Benennung und vollstaendiger Gabelungsliste fassen. B-3, B-7 und B-8
  als Merkposten fuer jede kuenftige VRP-Hypothese fuehren.

## 5. Ergebnisblindheit dieses Reviews (Offenlegung)

- **Daten.**
  - Keine Netzanfrage, die Daten lieferte. Gelesen wurden nur Kopien aus dem Sitzungs-Cache der Herleitung, kopiert per
    Datumsschleife [R:setup_cache.py]: DVOL BTC/ETH bis 2024-05-01 sowie die sechs `publicTrade`-Pruefungstage vor
    2024-06.
  - Das Panel wird beim Lesen bei 2024-05-31 abgeschnitten, vor jeder Rendite oder Spanne [R:rv_common.py].
  - Der Katalog wurde nicht neu geladen, der Bucket nicht gelistet.
  - Ein erster Lauf ueber `hd.load` stellte fuer die nicht kompaktierten Backfill-Partitionen je Partition eine
    HEAD-Anfrage an den geteilten Endpunkt. Er wurde nach ~10 min ohne Ausgabe abgebrochen. Danach liest der Review-Lader
    die Cache-Kopien zu den Katalogschluesseln direkt (`read_cached`, loud fail bei fehlender Datei).
- **Ausgaben.**
  - Nur SD, ACF, Varianzfaktoren, Verhaeltnisse, RV-Niveaus der Vorperiode (rms, mean/rms) und Nullwelt-Groessen;
    Waechter `guard_out`.
  - Kein Praemienmittel, kein DVOL-Mittel, keine RV ab 2024-06-01, nichts ab 2026-07-01.
  - Nicht geoeffnet: Siegeldateien, die WP-10(A2)- und WP-10(A)-IV-RV-Dateien, die WP-9-Differenzserie. Von
    `feasibility.json` / `power.json` wurden nur die Schluessel maschinell gescannt; die Zahlen stammen aus den
    Markdown-Dateien.
- **Vorwissen.** Wie KONTAMINATION 0.3; es gilt gleichermassen fuer diesen Gutachter. Einzige Verwendung: die
  Plausibilitaetsaussage in B-4 (b) ueber IV-Niveaus 2017-2022, also vor jedem Fenster. Keine Web-Suche.

## 6. Skripte (`scratchpad/h27_review/`, sha256 gekuerzt)

| Datei | sha256 | Inhalt |
|---|---|---|
| `rv_common.py` | `bd8880ab...bb59b147` | Lader, Abschneide-Waechter, RV-Schaetzer cc/pk/gk/rs, Ausgabe-Waechter |
| `nuisance_review.py` | `ffd9469d...12faa63a` | SD, ACF, 14 c-Schaetzer, Monatsvariante, Spannweiten-Schaetzer, MC der Regel P-3 |
| `nullworld_review.py` | `82a80181...ab1ff267` | SV-Nullwelt (eigene Implementierung), nu-Sensitivitaet, Kurtosis-Pruefung, GARCH(1,1)-t, rauschfreie Schranke |
| `noise_share.py` | `a4f4f14e...b8b7627c` | Rauschanteil der RV-Schaetzer (kappa, Delta-Methode) |
| `power_review.py` | `e45e4102...5b4c1cb2` | Prior-Umrechnung, Zuordnung `power_p1` (P-1, A3), Sensitivitaeten |
| `conv_review.py` | `8ffd90a0...f9be7deb` | Panel-close / high / low gegen `publicTrade` (sechs Tage vor 2024-06), Gleichstaende |
| `setup_cache.py`, `keyscan.py` | `fd944b22...cc47f238`, `8113ae8d...e8f869fa` | Cache-Kopie der Vorperiode; Schluessel-Scan der Ausgaben |

Ergebnisdateien im selben Ordner: `nuisance_review.json`, `nullworld_review.json`, `noise_share.json`,
`power_review.json` (alle ohne Praemien- oder DVOL-Mittel).
