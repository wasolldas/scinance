# R4 - METHODIK UND INFRASTRUKTUR FUER SCINANCE 3.0

> Auftrag: Methoden-/Infrastruktur-Recherche (Researcher R4), Phase 3.
> Gelesen: `BRIEF_COMMON.md`, `ERKENNTNIS_KOMPENDIUM.md` (vollstaendig),
> `INFRA_OPS_MAP.md` (1, 2, 6, 7), `FINAL_PRD.md` (1, 2, 5, 8, 9),
> `CODE_MAP.md` (1, 2.11, 3, 7), `UMBAU_SPEZIFIKATION.md`,
> `src/bybit_edge/research/bar_cache.py` (vollstaendig),
> `c24_impact/driver.py` (Docstring-Muster), `c17_c41_tradability/net_edge.py`,
> `config.py` (Kosten-Konstanten), `hypothesis_registry.md` (H-01..H-06).
>
> **Belegstatus:** Alle Formeln in Abschnitt 0 sind aus Standard-Statistik
> HERGELEITET und mit den im Text angegebenen Eingangsgroessen nachrechenbar -
> sie sind keine Zitate. Literatur ist mit Autor/Jahr belegt. API-Fakten:
> der Egress-Proxy dieser Sandbox blockiert `bybit-exchange.github.io`,
> `api.bybit.com`, `docs.deribit.com` und `r.jina.ai` (403 CONNECT, im
> Proxy-Log nachgewiesen). Was ueber Websuche belegbar war, ist belegt;
> alles andere ist ausdruecklich **UNBELEGT - Probe-Pflicht** markiert.
> Kein Wert in diesem Dokument ist geschaetzt und als gemessen ausgegeben.

---

## 0. KERNBEFUNDE IN ZAHLEN (das Rueckgrat des Berichts)

Diese sieben Groessen entscheiden fast alles Weitere. Sie sind alle aus den Programm-Konstanten
(Kompendium B) plus Standardstatistik herleitbar und haetten in den letzten drei Monaten jederzeit
ausgerechnet werden koennen.

### K-0.1 Horizont-Friktions-Kurve (die wichtigste fehlende Konstante)

Fuer eine gerichtete Wette gilt bei normalverteilten Renditen `E|r_h| = 0,798 * sigma_h` und bei
Trefferquote p eine erwartete Brutto-Kante `edge_h = (2p - 1) * 0,798 * sigma_h`. Mit BTC-Tagesvol
`sigma_1d = 262 bp` (aus 50 % annualisiert / sqrt(365)):

| Horizont | sigma_h (bp) | edge bei p=0,55 | edge bei p=0,516 (IC~0,05) |
|---|---|---|---|
| 1 s   | 0,89 | 0,07 bp | 0,02 bp |
| 1 min | 6,9  | 0,55 bp | 0,18 bp |
| 30 min| 37,8 | 3,0 bp  | 0,97 bp |
| 1 h   | 53,5 | 4,3 bp  | 1,4 bp |
| 4 h   | 107  | 8,5 bp  | 2,7 bp |
| 1 d   | 262  | 20,9 bp | 6,7 bp |
| 1 Woche| 693 | 55,3 bp | 17,7 bp |
| 1 Monat| 1435| 114,5 bp| 36,6 bp |

Daraus folgen drei Zahlen, die in die 3.0-Verfassung gehoeren:

- **Ein PERFEKTES 1-Sekunden-Orakel (p=1,0) verdient 0,71 bp** und verliert gegen die
  11-bp-Taker-Wand 10,3 bp je Round-Trip. Der gesamte Sekunden-/Minuten-Track (H-03, H-04b, H-05c,
  H-24) war damit **a priori und ohne jeden Datenlauf tot** - nicht empirisch, sondern arithmetisch.
- **Mindest-Halteperiode gegen die Taker-Wand (11 bp) bei p=0,55: ~6,6 h.** Gegen die Maker-Wand (4
  bp): ~53 min.
- **Bei realistischem Wochen-IC 0,05 (p=0,516): Mindest-Halteperiode ~2,7 Tage (Taker) bzw. ~7 h
  (Maker).** Ein Wochen-Rebalance liefert dann 17,7 - 11 = **6,7 bp netto je Zyklus, ~3,5 %/Jahr
  brutto** vor Funding, Kapitalbindung und Small-Cap-Aufschlag. Das ist die ehrliche Groessenordnung
  der Klasse (ii) - positiv, aber duenn.

**Konsequenz:** Der 3.0-Pivot auf Tage/Wochen ist quantitativ richtig, aber er kauft *Luft*, keine
Sicherheit. Jede Wochen-Hypothese braucht neben der statistischen Schwelle eine **oekonomische
Mindestmagnitude** (unten 1.2).

### K-0.2 Wieviel Historie ein Sharpe-Test braucht (Lo 2002)

Lo (2002, FAJ 58(4)) gibt fuer i.i.d.-Renditen `Var(SR_p) = (1 + SR_p^2/2)/n`. Annualisiert mit q
Beobachtungen/Jahr und T Jahren ergibt das `SE(SR_ann) = sqrt((1 + SR_ann^2/(2q)) / T)`. Fuer
einseitiges alpha=0,05 und Power 0,80 braucht man `SR_ann / SE >= z_0,95 + z_0,80 = 2,4865`, also

**`T_min [Jahre] ~= 6,18 / SR_ann^2`** (Tagesdaten; der q-Term ist < 0,3 %).

| Sharpe (ann.) | T_min bei Power 0,8 |
|---|---|
| 2,0 | 1,55 Jahre |
| 1,5 | 2,75 Jahre |
| 1,0 | **6,19 Jahre** |
| 0,75| 11,0 Jahre |
| 0,5 | **24,7 Jahre** |

Mit Nicht-Normalitaet (Mertens-Erweiterung in Lo 2002: `Var(SR_p) = (1 + SR_p^2/2 - g3*SR_p +
(g4-3)/4 * SR_p^2)/n`) wird es deutlich schlechter. Fuer eine typische Short-Vol-Praemie mit
monatlicher Schiefe g3 = -2 und Exzess-Kurtosis 10 bei SR_ann = 1,0 ist der Varianz-Faktor 1,827,
also **T_min = 11,3 statt 6,2 Jahre**.

**Konsequenz - das haerteste Ergebnis dieses Berichts:** Der Datenbestand reicht 5-6 Jahre
(Kompendium B.16). Ein Sharpe-Test kann darauf **Sharpe 1,0 gerade eben** und **Sharpe 0,5 gar
nicht** nachweisen; bei realistischer Schiefe reicht er auch fuer 1,0 nicht. **Der Sharpe darf
deshalb NICHT die urteilstragende Groesse einer Praemien-Hypothese sein.** Urteilstragend muss die
**Praemie selbst** sein (Abschnitt 1.1) - sie hat bei 3 Funding-Intervallen/Tag oder taeglichen
IV-RV-Paaren 10^3-10^4 Beobachtungen statt 5 Jahres-Renditen.

### K-0.3 Der Rauschboden des Sharpe unter Variantensuche (Bailey/Lopez de Prado)

`E[max SR ueber K Versuche] ~= sigma_SR * ((1-g)*Phi^-1(1-1/K) + g*Phi^-1(1-1/(K*e)))`, g = 0,5772
(Euler-Mascheroni) - Bailey & Lopez de Prado (2014, "The Deflated Sharpe Ratio", SSRN 2460551;
Formel per Websuche bestaetigt). Mit `sigma_SR ~= 1/sqrt(T)` und T = 5 Jahren:

| K Varianten | Rausch-Decke E[max SR] |
|---|---|
| 5   | 0,53 |
| 10  | 0,70 |
| 20  | **0,85** |
| 50  | **1,02** |
| 100 | 1,13 |

**Konsequenz:** Auf 5 Jahren erzeugt schon eine Suche ueber 50 Varianten einen erwarteten
Bestwert-Sharpe von 1,02 aus reinem Rauschen. Eine vorregistrierte Sharpe-Schwelle von 1,0 ist damit
bei K>=50 **strukturell bedeutungslos** - exakt das DEC-31-Muster (Schwelle unter dem Nulleffekt),
nur in einer anderen Metrik. **K muss vorab gezaehlt und registriert werden**, und die Schwelle muss
oberhalb der zugehoerigen Decke liegen.

### K-0.4 Der Rauschboden des Max-Drawdown

Fuer eine driftlose Brownsche Bewegung ist `E[MaxDD] = sqrt(pi/2) * sigma * sqrt(T)` = `1,2533 *
sigma_ann * sqrt(T_Jahre)` (Magdon-Ismail et al. 2004, "On the maximum drawdown of a Brownian
motion", J. Appl. Prob. 41(1)).

| sigma_ann | E[MaxDD] ueber 5 Jahre |
|---|---|
| 10 % | 28 % |
| 15 % | 42 % |
| 20 % | 56 % |

**Konsequenz:** Eine importierte Schwelle "MaxDD < 30 %" ist fuer eine 20-%-Vol-Strategie ueber 5
Jahre **strukturell unerreichbar, auch fuer eine perfekte Strategie**. Das ist der GL-012-Fehler
(C-14-rho-Schwelle) in neuem Gewand. MaxDD-Schwellen muessen aus sigma und T hergeleitet werden.

### K-0.5 Der IC-Rauschboden und was Universumsbreite wirklich kauft

Quer-Schnitt-IC je Periode hat unter der Null `SD(IC_t) ~= 1/sqrt(N_eff - 1)`, mit `N_eff = N_c / (1
+ (N_c-1)*rho_quer)` (rho_quer = mittlere Rest-Korrelation nach Quer-Schnitts-Demeaning). Ueber T
Perioden: `SE(mean IC) = SD(IC_t)/sqrt(T)`; detektierbar bei t=2 ist `2*SE`.

Mit T = 104 Wochen (2 Jahre, REZENZ-konform):

| N_c Symbole | rho_quer | N_eff | detektierbarer mittlerer IC |
|---|---|---|---|
| 5   | 0    | 5    | **0,098** |
| 50  | 0    | 50   | 0,028 |
| 50  | 0,05 | 14,5 | 0,053 |
| 50  | 0,10 | 8,5  | 0,072 |
| 200 | 0,05 | 18,3 | 0,047 |
| 200 | 0,10 | 10,5 | 0,064 |

**Zwei Konsequenzen:**
1. **Auf 5 Symbolen ist ein realistischer Wochen-Faktor (IC 0,03-0,06) grundsaetzlich unmessbar** -
   die Nachweisgrenze liegt bei 0,098. Das ist die praezise Verallgemeinerung von GL-012 (`max|z| =
   sqrt(N-1) = 2,0`): nicht nur die z-Schwelle, sondern die gesamte Quer-Schnitts-Statistik ist auf
   N=5 unbrauchbar. **Das breite Universum ist keine Kuer, es ist die Existenzbedingung der Klasse
   (ii).**
2. **Die Breite hilft stark von 5 auf ~50 und danach kaum noch**, weil `rho_quer` den Gewinn
   deckelt. Die entscheidende Groesse `rho_quer` ist **UNGEMESSEN** - das ist ein eigener, billiger
   Zensus (WP-7, Abschnitt 3.5) und muss VOR jeder Wochen-Registrierung vorliegen.

### K-0.6 Was das harte Ein-Fenster-DROP-Kriterium wirklich kostet

PRD 8.5 / Kompendium C.10: Schwelle in EINEM von >=2 Fenstern verfehlt = DROP. Wenn die
Per-Fenster-Power `1-beta` ist, gilt `P(beide bestehen) = (1-beta)^2`:

| Per-Fenster-Power | P(echter Effekt ueberlebt) |
|---|---|
| 0,80 | 0,64 |
| 0,50 | **0,25** |
| 0,35 | 0,12 |

Bei der in K-0.2/K-0.5 gezeigten Datenlage liegt die realistische Per-Fenster-Power der Klassen (i)
und (ii) zwischen 0,3 und 0,6. Die Regel verwirft dann **drei von vier echten Effekten**. Das ist
keine Konservativitaet mehr, das ist eine Typ-II-Maschine.

Gegenrechnung fuer eine **Vorzeichen-Konsistenz** statt Signifikanz je Fenster: bei einem echten
Effekt mit Per-Fenster-t = 1,4 ist `P(Vorzeichen richtig) = Phi(1,4) = 0,919`, also `P(beide) =
0,845` - gegenueber `P(beide signifikant bei t>1,645) = 0,42^2 = 0,18`. **Faktor 4,7 mehr Retention
bei praktisch gleicher Falsch-Positiv-Kontrolle**, wenn das eigentliche Signifikanz-Urteil auf dem
GEPOOLTEN Schaetzer mit fenster-geclustertem Bootstrap liegt. Vorschlag in Abschnitt 6.3.

### K-0.7 Kosten-Nutzen der bisherigen GPU-Wellen

Aus INFRA_OPS_MAP 6: H-15 ~180 h, H-16 ~57 h, H-14 ~2-3 GPU-Tage, H-17 ~1-2 GPU-Tage, H-18 192 s.
Summe **~350 GPU-Stunden ~ 15 Maschinen-Tage** ueber 9+4+n Checkpoint-Sessions. Ertrag: 2
kapitalfreie WEITER (H-15; H-16 mit zurueckgezogener Lesart), 1 methodisch invalider Lauf (H-14), 1
Audit. Handelbare Kanten: 0. Registrierte Tradability-Folgen: 0 (Kompendium E.10 listet H-15b und
H-16b explizit als NICHT registriert). Stromkosten sind irrelevant (~32 kWh ~ 10 EUR); der reale
Preis war **Kalenderzeit und die Aufmerksamkeit des einzigen Betreibers**.

Gegenrechnung: der komplette Broad-Universe-REST-Backfill (Abschnitt 3) ist ein **Wochenend-Job
unter 10 Stunden und unter 5 GB**.

---

## 1. GATE-DESIGN FUER DREI HYPOTHESEN-KLASSEN

### 1.0 Gemeinsames Registrierungs-Geruest (neue Pflichtzeilen 3.0)

Zusaetzlich zu den 2.0-Feldern traegt jede 3.0-Registrierung sechs Pflichtzeilen. Jede ist durch
einen konkreten Programm-Vorfall erzwungen, keine ist Geschmackssache.

| Pflichtzeile | Erzwingender Vorfall |
|---|---|
| **Struktureller Nulleffekt** - Zahl, Herleitung UND Messung am Null-Fixture | DEC-31/33 (CRPSS-Geschenk 0,21-0,29). Neu: auch messen, nicht nur herleiten. |
| **Selektions-Decke** - K = Zahl gerechneter Varianten, E[max] nach K-0.3 | H-11-Muster in einer zweiten Metrik; ohne K ist jede Sharpe-/AUC-Schwelle wertlos. |
| **Power-Zeile** - detektierbare Effektgroesse bei Power 0,8 auf dem registrierten Fenster | K-0.2/K-0.5/K-0.6: in 26 Registrierungen keine einzige Power-Rechnung. |
| **Oekonomische Mindestmagnitude** - aus der Horizont-Friktions-Kurve K-0.1, nicht aus der Statistik | H-03/H-04b/H-05c: saubere Messungen 80-500x unter der Wand. |
| **Entscheidungsrelevanz** - welche Entscheidung loest ein WEITER aus, welche schliesst ein DROP? | H-14..H-17: 350 GPU-h fuer Hypothesen, deren bestmoegliches Ergebnis nichts entschieden haette. |
| **Resampling-Einheit + effektives N** (nicht das rohe N) | H-10/H-21 (N-Floor); Kolari/Pynnoenen fuer Klasse (iii). |

Ausserdem **drei statt zwei Fixtures** (Erweiterung von DEC-39): positiv, null und **adversarial** -
ein Regime, das die Metrik aus einem BEKANNTEN Artefakt heraus positiv aussehen laesst. Die
adversarialen Fixtures sind je Klasse unten benannt; sie sind der Ort, an dem das Programm bisher am
meisten Geld verloren haette.

---

### 1.1 KLASSE P - PRAEMIEN-ERNTE (Carry / VRP / Skew)

Die Ertragsquelle ist kein Vorzeichen-Forecast, sondern ein Erwartungswert-Keil zwischen zwei
beobachtbaren Preisen. Der Keil ist direkt und kapitalfrei messbar - Existenzfrage und Sharpe-Frage
gehoeren deshalb in zwei getrennte Registrierungen (Kompendium C.2, unveraendert bindend).

**1.1.a Urteilstragend ist die PRAEMIE, nicht der Sharpe.** Begruendung K-0.2: der Sharpe braucht
6-25 Jahre, die Praemie hat 1.095 Funding-Beobachtungen bzw. 365 IV/RV-Paare pro Jahr. Konkret:
`prem_carry(t) = f(t) - r_drift(t)` (realisiertes Funding minus realisierte Basisbewegung),
annualisiert `1095 * mean`; `prem_vrp(t) = IV_t^2 - RV_{t,t+30d}^2` in Varianzpunkten (Carr & Wu
2009; Bakshi & Kapadia 2003); `prem_skew(t) = IV_put(-0,25 delta) - IV_call(+0,25 delta)` gegen die
realisierte Folge-Schiefe.

**1.1.b Struktureller Nulleffekt - sechs Quellen, je einzeln herzuleiten:**

1. **Jensen-/Konvexitaets-Term:** `E[IV^2] - E[RV^2]` ist auch risikoneutral nicht null, wenn IV als
   Volatilitaet und RV als Wurzel-Varianz gemessen wird (`E[sqrt(X)] != sqrt(E[X])`); die Verzerrung
   ist ~ `-nu^2/(8*sigma)` bei Vol-of-Vol nu. Ausrechnen und die Schwelle darueber legen - sonst
   wiederholt sich DEC-31 exakt.
2. **Ueberlappung:** 30-Tage-VRP taeglich gemessen ist 30-fach ueberlappend; effektives N = T/30.
3. **Peso-Term (der teuerste):** Short-Vol/Short-Carry zeigt in jedem crashfreien Fenster einen
   positiven Mittelwert. Nicht analytisch - **per adversarialem Fixture zu messen** (1.1.d).
4. **Selektions-Decke** nach K-0.3 mit dem registrierten K.
5. **MaxDD-Boden** nach K-0.4 aus der gemessenen sigma.
6. **Tail-Ratio:** unter symmetrischer Null exakt 1,0. **Achtung Richtungsfehler:** eine echte
   Praemie hat strukturell Tail-Ratio < 1 (negative Schiefe ist ihr Preis). Ein Gate "Tail-Ratio > 1"
   wuerde jede echte Praemie toeten - es ist Risiko-Deskriptor mit Untergrenze, nie Existenzkriterium.

**1.1.c Schwellen, zweistufig und getrennt registriert:**

- **Stufe P-A (kapitalfrei, Existenz):** Metrik `mean(prem)` je Fenster in annualisierten bp bzw.
  Vol-Punkten. Null per **stationaerem Block-Bootstrap** (Politis & Romano 1994) mit automatischer
  Blocklaenge (Politis & White 2004) - Praemienreihen sind stark autokorreliert, der
  i.i.d.-Bootstrap unterschaetzt den SE massiv. PASS: `mean >= max(strukturelle Null, oekonomische
  Mindestmagnitude)` UND `p <= 0,05` nach BH-FDR ueber F-PREM-<name> UND gleiches Vorzeichen in
  beiden Fenstern. Die oekonomische Mindestmagnitude ist **Zyklus-Kosten aus Abschnitt 2 mal Faktor
  2** - Faktor 2, weil die Kostenkonstanten fuer das breite Universum ungemessen sind (2.5). Das ist
  ein GL-012-Feasibility-Check, keine Tradability-Aussage.
- **Stufe P-B (Tradability, erst nach P-A):** Sharpe mit Block-Bootstrap-CI **und** Deflated Sharpe
  gegen das registrierte K **und** Minimum Track Record Length (Bailey & Lopez de Prado 2012):
  `MinTRL = 1 + (1 - g3*SR + (g4-1)/4*SR^2) * (z_alpha/(SR - SR*))^2`. **Ist MinTRL groesser als die
  verfuegbare Historie: PARK, kein Urteil** - der ehrliche Ausgang, und bei Sharpe < ~1,2 der
  Regelfall. Dazu MaxDD gegen den K-0.4-Boden, Tail-Ratio als Untergrenze, Kapital/Margin aus
  Abschnitt 2.
- **Regime-Bedingtheit als Gleichheits-, nicht als Differenztest.** Bei 5 Jahren und 4 Regimen hat
  jeder Teil-Sharpe SE ~ sqrt(4/5) = 0,89; Teil-Sharpes streuen rein zufaellig um ~1,8. "Praemie ist
  in Regime X hoeher" ist bei dieser Streuung nicht interpretierbar. Registriert wird stattdessen:
  gleiches Vorzeichen in ALLEN K Regimen bei abgesenkter Per-Regime-Schwelle.

**1.1.d Fixtures.** *Positiv:* GBM mit RV = 60 %, Optionen zu IV = 66 % bepreist; der Schaetzer muss
die injizierte Praemie im CI wiederfinden. *Null:* identisch mit IV = RV; zwei Pflicht-Ausgaben -
(a) `mean(prem)` im CI um 0, (b) **die komplette Selektions-Pipeline ueber alle K Varianten laeuft
auf dem Null-Fixture und ihre Bestwert-Verteilung wird gemessen**; das ist die empirische
Selektions-Decke und genau dieser Schritt hat bei H-11 gefehlt. *Adversarial (Peso-Fixture, das
wichtigste):* Nullpraemie plus Merton-Spruenge mit Rate 1/3 Jahre und Hoehe -35 %; ein 5-Jahres-
Fenster enthaelt mit Wahrscheinlichkeit `e^-1,67 = 0,19` **keinen einzigen Sprung** und zeigt dann
eine scheinbar hohe, hochsignifikante Praemie. **Das Gate MUSS hier durchfallen**, sonst ist es
kaputt. Operativ folgt daraus die Klausel "urteilstragendes Fenster enthaelt mindestens eine
Stress-Episode" - sie steht bereits als C-33-Auflage (Kompendium E.7) und ist auf die ganze Klasse
auszuweiten.

**1.1.e FDR.** Familie `F-PREM-<name>` = alle Parametervarianten EINER Praemie (DTE-Band,
|Delta|-Band, Rebalancing-Takt, Universum); Ueber-Familie `F-PREM` ueber alle Praemien-Hypothesen der
Welle (DEC-22, rein verschaerfend). **Zusatz:** die Varianten sind hoch korreliert; BH ist dann
konservativ in der FDR, deckt aber die Selektions-Decke nicht ab. Deshalb zusaetzlich DSR mit
`K_eff = (sum lambda_i)^2 / sum lambda_i^2` (Partizipationszahl des Eigenwertspektrums der
Varianten-Korrelationsmatrix). Beide Zahlen werden berichtet, das Gate nutzt die strengere.

---

### 1.2 KLASSE W - WOCHEN-HORIZONT-RICHTUNGSFAKTOREN

**1.2.a Nicht ueberlappend messen.** Ueberlappende h-Perioden-Renditen im Basistakt blaehen die
Varianz des Mittelwerts um ~h auf; das effektive N ist `T/h`. **Ueberlappung kauft keine Power**, sie
stabilisiert nur den Punktschaetzer und handelt sich eine HAC-Korrektur ein, die bei T ~ 250
nachweislich ueberverwirft. Verbindlich: urteilstragend ist die **nicht-ueberlappende** Wochen-
Rendite; ueberlappende Fassungen laufen als deskriptive Robustheitspruefung ohne Urteilslast
(H-24-Muster: ein registrierter Horizont, weitere berichtet). Ist Ueberlappung unvermeidbar, gilt
**stationaerer Bootstrap vor HAC**; Newey-West (1987) mit Andrews-Bandbreite (1991) und
Hansen-Hodrick (1980, Lag h-1) sind zulaessig, aber HH ist in kleinen Stichproben oft nicht positiv
semidefinit und beide ueberverwerfen bei T ~ 250. Der Bootstrap behandelt zusaetzlich die
Nicht-Normalitaet der IC-Verteilung.

**1.2.b Struktureller Nulleffekt - drei Quellen, alle Pflicht:**

1. **Quer-Schnitts-Permutations-Null (operative Hauptnull).** Der Faktor wird INNERHALB jeder Woche
   ueber die Symbole permutiert, 1.000-fach, die ganze Pipeline neu gerechnet. Die resultierende
   Verteilung von `mean(IC)` **enthaelt die tatsaechliche effektive Breite exakt**, ohne dass
   `rho_quer` geschaetzt werden muss. Rechenaufwand: Sekunden.
2. **Persistenz-Null.** Boudoukh/Richardson/Whitelaw (2008) und Valkanov (2003): ein persistenter
   Praediktor erzeugt in Langhorizont-Regressionen mechanisch R^2 und t-Werte, die mit dem Horizont
   wachsen - auch unter der Null. Pflicht: AR(1) an den Faktor fitten, unter der Null simulieren, die
   Pipeline darauf fahren, die IC-/t-Verteilung als zweite Null berichten.
3. **Selektions-Decke** ueber die Zahl gerechneter Faktorvarianten (K-0.3-Analogon fuer IC).

**1.2.c Die REZENZ-Klemme bei ~250 Wochen.** DEC-38 verlangt juengste Regime, PRD 8.5 verlangt >=2
disjunkte Fenster; bei 250 Wochen kollidiert beides:

| Aufteilung | T je Fenster | detektierbarer IC (N_c=50, rho=0,05) |
|---|---|---|
| 2 x 26 Wochen (juengstes Jahr) | 26 | 0,106 |
| 2 x 52 Wochen (juengste 2 Jahre) | 52 | 0,075 |
| 2 x 78 Wochen (juengste 3 Jahre) | 78 | 0,061 |
| 1 x 156 Wochen gepoolt | 156 | 0,043 |

Ein realistischer Wochen-IC liegt bei 0,03-0,06 - **nur die gepoolte 3-Jahres-Variante ist
trennscharf**. Empfehlung: zwei disjunkte REZENZ-Fenster von je 78 Wochen mit **geteilten Rollen** -
je Fenster nur Vorzeichen-Konsistenz plus Magnituden-Band (`IC > 0`, innerhalb [0,4x; 2,5x] des
gepoolten Werts), das Signifikanzurteil auf dem **gepoolten** Schaetzer mit fenster-geclustertem
stationaerem Bootstrap (Begruendung K-0.6, Faktor 4,7 Retention). Aeltere Historie ausschliesslich
als Aera-Profil ohne Urteilslast. **Die Power-Zeile ist hier der Feasibility-Check:** Registrierung
nur zulaessig, wenn der Permutations-Rauschboden auf dem TATSAECHLICHEN Panel unter der
registrierten Schwelle liegt; sonst struktureller A-priori-DROP nach GL-012, ohne Datenlauf wie H-07.

**1.2.d Oekonomische Mindestmagnitude.** Aus K-0.1: Netto-Kante bei Wochen-Rebalance und Taker-Wand
ist `0,798*(2p-1)*693 bp - 11 bp` mit `p = 0,5 + arcsin(IC)/pi`; Break-even bei **IC = 0,031**,
Faktor 2 darueber also **IC_min = 0,062**. Gegen die Nachweisgrenzen aus K-0.5 (N_c=5: 0,098;
N_c=50, T=156: 0,043) folgt die praeziseste Aussage dieses Berichts: **Klasse W ist auf dem heutigen
5-Symbol-Bestand strukturell untestbar und wird auf einem 50-200-Symbol-Panel gerade eben testbar.**
Der Datenausbau (Abschnitt 3) ist keine Kuer, sondern die Existenzbedingung der Klasse.

**1.2.e Fixtures.** *Positiv:* Panel mit injiziertem Quer-Schnitts-IC 0,06 inklusive gemeinsamem
BTC-Beta-Faktor und Sektor-Bloecken. *Null:* Faktor zufaellig permutiert. *Adversarial:* ein Faktor,
der mechanisch mit dem Markt-Beta korreliert (Vol- oder Groessen-Proxy) auf einem Panel mit
dominantem Marktfaktor - in Krypto ist praktisch alles Beta zu BTC, und ein "Quer-Schnitts"-Befund,
der in Wahrheit Markt-Timing ist, ist DIE Fehlerklasse dieser Familie. Faellt das Gate hier nicht
durch, ist die Neutralisierung defekt.

**1.2.f FDR - mit einer wichtigen Korrektur.** Familie `F-WEEK-<faktor>` = alle Horizonte x
Universumsdefinitionen x Neutralisierungen EINES Faktors; Ueber-Familie `F-WEEK`. **Korrektur zur
2.0-Praxis:** In H-06/H-08/H-09/H-22 wurden Symbol-Zellen als eigene Tests gezaehlt ("0 von 10
Zellen"). Bei N=5 tolerabel, bei N=200 zerstoert es die Power vollstaendig. **Ein Panel-Mitglied ist
eine Beobachtung, keine Hypothese** - die FDR-Familie besteht aus Hypothesen-VARIANTEN,
Panel-Mitglieder werden zu EINER Teststatistik gepoolt. Sonst erzeugt das Programm sein
Multiple-Testing-Problem selbst.

---

### 1.3 KLASSE E - EREIGNIS-STUDIEN

**1.3.a Konstruktion.** `AR_i(t) = r_i(t) - beta_i * r_mkt(t)`, beta auf einem **gepurgten**
Vor-Fenster (Purge >= Ereignisfensterlaenge). `CAR_i = sum AR_i` ueber genau EIN vorregistriertes
Fenster, kein Fenster-Scan.

**1.3.b Struktureller Nulleffekt = die Placebo-Verteilung.** Der CAR ist unter der Null nur null,
wenn das Normal-Rendite-Modell unverzerrt ist; in Krypto ist es das nicht (ein auf einer Bullenphase
geschaetztes alpha erzeugt out-of-sample systematisch negative CARs). Operativ: die gesamte Pipeline
laeuft auf **Zufallsterminen mit identischer Kalenderverteilung** (gleiche Anzahl, gleiche
Wochentags-/Tageszeit-/Cluster-Struktur), 1.000-fach. Mittelwert und Quantile dieser Verteilung sind
der Nulleffekt, die Schwelle liegt darueber. Rechenzeit: Minuten.

**1.3.c Resampling-Einheit ist das CLUSTER, nicht das Ereignis.** Kolari & Pynnoenen (2010, RFS
23(11): 3996-4025): schon geringe Quer-Korrelation der abnormalen Renditen fuehrt bei
Ereignis-Datums-Clustering zu massivem Ueberverwerfen. In Krypto clustert praktisch alles -
Funding-Settlements sind symbolgleichzeitig, Makro-Termine global, Listings kommen in Schueben.
Verbindlich: Bootstrap-Einheit ist das Kalender-Cluster mit ALLEN seinen Ereignissen, und **der
registrierte N-Floor gilt fuer `N_cluster`, nicht fuer `N_events`** (typisch Faktor 5-50 weniger -
genau die Falle von H-10 und H-21). Zusaetzlich zu berichten: die standardisierte
Quer-Schnitts-Statistik nach Boehmer/Musumeci/Poulsen (1991, robust gegen ereignis-induzierte
Varianzerhoehung) und der Rangtest nach Corrado (1989) als nichtparametrischer Anker - beides
Diagnostik, urteilstragend ist der Cluster-Bootstrap.

**1.3.d Fixtures.** *Positiv:* injizierter CAR +50 bp an bekannten, absichtlich stark geclusterten
Terminen. *Null:* dieselben Termine ohne Effekt. *Adversarial:* Ereignisse, die auf VERGANGENEN
Renditen selektiert werden ("grosse Bewegung") auf einem reinen Random Walk - das erzeugt scheinbare
Mean-Reversion im Ereignisfenster und ist exakt die Fehlerklasse H-20. Nach Placebo-Kalibrierung MUSS
der Effekt verschwinden.

**1.3.e FDR.** `F-EVENT-<typ>` = alle Fenster-Varianten x Ereignis-Definitionen EINES Typs;
Ueber-Familie `F-EVENT`. Da nur EIN Fenster urteilstragend registriert wird, ist die Familie klein -
das ist Absicht.

---

## 2. TRADABILITY-MODELL 3.0 (Repo-Modul-Skizze, keine Implementierung)

### 2.1 Grundsatz

Das Kostenmodell ist ein **Mess-Artefakt, kein Parametersatz**. Jede Konstante ist entweder (a)
gemessen und eingefroren, (b) ungemessen und dann als **zweiseitige Pflicht-Sensitivitaet**
ausgewiesen, oder (c) ungemessen und dann ein **harter Abbruch** (Loud-Fail, Kompendium C.14).
Stille Defaults sind verboten - sie waeren die Torpfosten-Verschiebung, die DEC-13/16
(Anti-Gaming-Klausel) genau verhindern soll.

### 2.2 Modul-Layout

`src/bybit_edge/research/tradability3/`

| Datei | Inhalt / Schnittstelle (Signaturen, keine Implementierung) |
|---|---|
| `constants.py` | Alle gemessenen Programm-Konstanten mit Quellen-Tag und Unit-Test-Pin: `FEE_MAKER=2,0 bp`, `FEE_TAKER=5,5 bp` je Bein (DEC-42/WP-4); `FEE_OPTION_MAKER_OF_INDEX=2 bp`, `..._TAKER_=3 bp` (DEC-45); `VEGA_OVER_S = {BTC: 5,28, ETH: 5,10}` bp Index je Vol-Punkt (WP-5/DEC-44); `PERP_TOB_SPREAD_BP = {BTC: 0,0157, ETH: 0,0537}` (WP-4/DEC-42); `OPT_QUOTE_WIDTH_VOLPTS` je (DTE-Bucket, |Delta|-Bucket) aus WP-5; `STRESS_EPISODE_STATS` aus WP-6. Plus `assert_constants_unmodified()`. |
| `perp.py` | `perp_roundtrip(symbol, notional_usd, entry: Fill, exit: Fill, regime) -> CostReport`. Bestandteile: Gebuehr je Bein, halber Spread je gekreuztem Bein (aus dem WP-4-Spread-Store, symbol- und regime-bedingt - GEMESSEN, nicht angenommen), Impact. |
| `impact.py` | `impact_bps(notional_usd, adv_usd, daily_vol_bp, k) -> float`, Wurzelgesetz `k * sqrt(notional/ADV) * daily_vol_bp` (Almgren et al. 2005, J. Risk 18(4) - Funktionalform belegt, **k fuer Bybit UNKALIBRIERT**). Pflicht: jedes Ergebnis wird bei `k=0` (optimistisch) UND `k=1` (realistisch) berichtet. Kein Einzelwert. |
| `option.py` | `option_leg_cost_volpts(coin, dte, abs_delta, side, n_fills, stress: bool) -> float` ueber `FEE_OPTION_*_OF_INDEX / VEGA_OVER_S` plus halbe Quote-Breite. **`delivery_fee_of_index` hat Default `None` und der Aufruf eines Halte-bis-Verfall-Pfads ohne gesetzten Wert RAISED** - die Delivery-/Exercise-Gebuehr ist die einzige bindende, noch ungemessene Options-Kostenkomponente (Kompendium E.6a) und trifft ausgerechnet das beste DEC-45-Szenario. |
| `funding.py` | `funding_pnl(symbol, side, t0, t1, panel) -> float` aus dem Funding-Panel (Abschnitt 3). Fuer Carry-Strategien ist das die Ertrags-, nicht die Kostenseite - deshalb dasselbe Modul, entgegengesetztes Vorzeichen. |
| `capital.py` | `capital_profile(position) -> CapitalReport`: gebundenes Kapital, Initial-/Maintenance-Margin, Margin-Multiplikator. **Bybit-Margin-Regeln sind fuer dieses Programm UNGEMESSEN** - deshalb: Modellierung als Kapital-Multiplikator `m` mit konservativem Default und Pflicht-Sensitivitaet; eine echte Kapital-Aussage braucht vorher einen eigenen WP (Regel-Verifikation). |
| `episode.py` | `stress_overlay(cost: CostReport, episode: StressProfile) -> CostReport`. Jede Kostenrechnung wird in "normaler Minute" UND "Stress-Minute" ausgewiesen. **Zwangsregel:** eine Strategie, deren Einstieg AUF ein Schock-Signal hin erfolgt, wird per Konstruktion in Stress-Minuten bepreist (WP-6/DEC-47/48 - reaktives Long-Vol ist genau daran gestorben). |
| `report.py` | `CostReport`-Dataclass, die JEDES Tradability-Gate emittiert: `fee_bp, spread_bp, impact_bp_k0, impact_bp_k1, funding_bp, delivery_bp, total_bp_k0, total_bp_k1, capital_multiplier, regime, constants_hash`. Ein Gate-Auditor vergleicht damit Gleiches mit Gleichem. |

### 2.3 Einheiten-Bruecke

Perp-Kosten in bp des Notionals; Options-Kosten in bp des **Index** (nicht des Notionals - DEC-45)
und, ueber `VEGA_OVER_S`, in **Vol-Punkten**. Das Modul muss beide Einheiten fuehren und ihre
Umrechnung per Unit-Test pinnen (die 5,28/5,10-Konstante ist skalen-invariant und bereits getestet,
WP-5).

### 2.4 Anti-Gaming-Bindung

`constants_hash` im `CostReport` ist der SHA-256 ueber `constants.py`. Ein Tradability-Lauf, dessen
Hash nicht dem in der Registrierung zitierten entspricht, ist **kein gueltiger Lauf**. Das macht die
DEC-13/16-Klausel maschinell pruefbar statt nur schriftlich bindend.

### 2.5 Die grosse offene Luecke

Alle gemessenen Kostenkonstanten stammen von **BTC/ETH-Majors**. Fuer ein 50-200-Symbol-Universum
sind Spread und Tiefe **vollstaendig ungemessen**. Ohne diese Messung ist jede
Broad-Universe-Tradability-Aussage wertlos. Der Zensus dafuer ist billig und in Abschnitt 3.6 (WP-8)
beschrieben; er ist **Vorbedingung** fuer jedes Klasse-W-Tradability-Gate.

---

## 3. DATEN-ERWEITERUNG UEBER OEFFENTLICHE ENDPUNKTE

> **Belegstatus:** Die Fakten unten stammen aus Websuche-Treffern auf die Original-Doku (deren
> Domains vom Egress-Proxy blockiert sind); alles nicht so Belegbare ist **UNBELEGT - Probe-Pflicht**
> markiert. Auf der Nutzer-Maschine klaert jede dieser Fragen EIN Request.

### 3.1 Endpunkte, Limits, Tiefe

| Endpunkt | Belegte Fakten | Unbelegt / Probe noetig |
|---|---|---|
| `GET /v5/market/kline` | `limit` in [1,1000], Default 500 (Bybit-Doku via Suche belegt). Public-Rate-Limit: **600 Requests je 5 s je IP** ueber alle `api.bybit.com`-Hosts; Ueberschreitung -> "403 access too frequent", 10 min Sperre (Bybit Rate-Limit-Doku via Suche belegt). | Genaue `interval`-Liste; Rueckreichweite je Symbol (vermutlich bis Listing) - **Probe-Pflicht** |
| `GET /v5/market/funding/history` | Params `category`(linear/inverse), `symbol`, `startTime`, `endTime`, `limit` in [1,200] Default 200; nur `startTime` allein ist ein Fehler; ohne Zeiten kommen die 200 juengsten (Bybit-Doku via Suche belegt). | **Maximale Rueckreichweite UNBELEGT.** Vermutet: bis Listing des Kontrakts, per Paginierung. Probe: BTCUSDT rueckwaerts bis 2020 paginieren, erste leere Antwort ist die Tiefe. |
| `GET /v5/market/open-interest` | Params `category`, `symbol`, `intervalTime`, `startTime`, `endTime`, `limit`, Cursor-Paginierung; 200 Punkte je Aufruf (via Suche belegt). | **Tiefe UNBELEGT und der kritischste offene Punkt.** In der Community wird eine Begrenzung berichtet; die von der Suche gefundene 6-Monats-Aussage betrifft nachweislich einen ANDEREN Endpunkt. **Wenn OI-Historie tatsaechlich flach ist, ist OI unwiederbringlich und muss SOFORT kontinuierlich geerntet werden** (siehe 3.4). |
| `GET /v5/market/instruments-info` | Existiert, liefert Kontraktspezifikationen mit `status` und Cursor-Paginierung. | **Ob delistete Symbole enthalten sind: UNBELEGT.** Erfahrungsgemaess verschwinden vollstaendig delistete Symbole aus dem Live-Roster. Falls ja: **Survivorship ist NICHT rueckwirkend heilbar** -> 3.4. |
| `GET /v5/market/tickers` | Ein Request liefert eine ganze Kategorie. Der Harvest-Baum hat bereits `bybit/tickers` mit **3.751 Symbolen** (Kompendium F.1). | Ob `bid1Price/ask1Price/openInterest/fundingRate` je Symbol enthalten sind und in welchem Takt - **Inhaltsprobe statt Namensschluss (Kompendium C.8!)**. Der Strom liegt schon da; erst pruefen, dann bauen. |
| Deribit `/public/get_volatility_index_data` | Params `currency`, `start_timestamp`, `end_timestamp`, `resolution`; Antwort OHLC je Bucket (via Suche belegt). **DVOL-Historie ab ~2021-04-01 verfuegbar** (Amberdata-Doku via Suche; Deribit-eigene Doku nicht erreichbar). | Genaue Resolution-Werte (vermutet 60/3600/43200/1D) und Punkte-Limit je Aufruf - **Probe-Pflicht** |
| Deribit `/public/get_last_settlements_by_currency`, `/public/get_delivery_prices`, `/public/get_instruments?expired=true` | Existieren als Public-Endpunkte. | **Tiefe und Semantik UNBELEGT.** Fuer historische Options-Settlements der wahrscheinlichste Pfad; Probe zwingend vor jeder Planung. |
| Binance `GET /fapi/v1/klines` | Gewichts-basiertes Limit, **2400 Gewicht/min je IP**, ~2 Gewicht je Kline-Aufruf; `startTime`/`endTime`-Paginierung bis Futures-Start 2019 (via Suche belegt). | `limit`-Maximum (1000 vs. 1500) widerspruechlich in den Quellen - **Probe-Pflicht** |

### 3.2 Volumenschaetzung (parametrisch, mit selbst gewaehlter Drossel 5 Req/s)

5 Req/s sind **0,4 %** des belegten Bybit-Limits (600/5 s = 120/s) - extrem sicher, und selbst dann
ist der ganze Backfill ein Wochenende. Annahmen: ~600 Linear-Perps + ~600 Spot + ~300 delistete =
**~1.500 Symbol-Historien, im Mittel 3 Jahre** (Annahme, per `instruments-info`-Probe zu ersetzen).

| Backfill | Requests | Zeit @5 Req/s | Zeilen | Parquet (geschaetzt) |
|---|---|---|---|---|
| 1d-Klines, gesamtes Universum | ~3.000 | **10 min** | 1,7 Mio | 40-80 MB |
| 1h-Klines, gesamtes Universum | ~40.500 | **2,3 h** | 40 Mio | 0,6-1,2 GB |
| 1m-Klines, Top-50 | ~80.000 | **4,5 h** | 80 Mio | 1,5-2,5 GB |
| 1m-Klines, gesamtes Universum | ~4,7 Mio | **260 h** | 4,7 Mrd | ~100 GB |
| Funding-Historie, gesamtes Universum | ~25.500 | **1,4 h** | 5 Mio | ~60 MB |
| Deribit DVOL 1d, BTC+ETH | < 20 | Sekunden | ~4.000 | < 1 MB |
| Binance 1h, 5 Symbole, seit 2019 | ~350 | ~1 min | 300k | ~5 MB |

**Die operative Aussage:** Zeilen 1, 2, 3, 5, 6, 7 zusammen sind **~8,5 Stunden und ~4 GB** - ein
Wochenende, PC-tauglich, ohne Keys, ohne Kosten. Zeile 4 (Minutenbars fuer das ganze Universum) ist
die einzige Position, die **NICHT** gemacht werden sollte: 260 h und 100 GB fuer einen Horizont, der
nach K-0.1 ohnehin unter der Friktionswand liegt.

### 3.3 Was in den HARVESTER gehoert (kontinuierlich)

Kriterium: **Irreversibilitaet.** Nur was sich spaeter nicht nachladen laesst, rechtfertigt einen
Dauerstrom (Anti-Data-Lake, PRD 9 / microstr S-A1).

1. **Taegliches Point-in-Time-Instrument-Roster** (`instruments-info` je Kategorie, 1-3
   Requests/Tag, wenige hundert kB). **Hoechste Prioritaet.** Es ist die einzige Verteidigung gegen
   Survivorship und es kann **grundsaetzlich nicht nachgeholt** werden. Jeder Tag, an dem es nicht
   laeuft, ist unwiederbringlich verloren.
2. **Universums-Ticker-Panel** (`tickers` je Kategorie, 15-min-Takt) - Spread, OI, Funding-Rate,
   Turnover fuer ALLE Symbole. **Zuerst Inhaltsprobe auf den bereits existierenden
   `bybit/tickers`-Strom** (Kompendium C.8-Lehre: nicht aus einem Namen auf Abwesenheit schliessen).
   Volumen bei 15-min-Takt und getrimmten Spalten: ~2,5-5 GB/Jahr.
3. **Open Interest**, falls die Tiefen-Probe (3.1) eine flache Historie zeigt - dann irreversibel,
   5-min- oder 1-h-Takt.
4. Bereits laufend und beizubehalten: Deribit `dvol`, `markprice.options`, `tickers`; Bybit
   Options-Ticker.
5. **Nicht** in den Harvester: Klines und Funding-Historie jeder Aufloesung - beliebig nachladbar,
   also ein Dauerstrom ohne Gegenwert.

### 3.4 Was Einmal-Backfill im Scinance-Repo ist

Alles aus 3.2 ausser Zeile 4. Wichtige Architektur-Bindung: **Backfills schreiben NIE in den
Harvest-Baum** (Schutzgut, read-only, per CLI-Guard erzwungen) - sie gehen in einen neuen, eigenen
Speicher unter derselben Disziplin wie der WP-0-Bar-Cache.

**Der wertvollste Einzel-Backfill:** Deribit-DVOL. Der Harvest-Baum hat 112 Tage (Kompendium F.1);
H-26 ist bis ~Mitte November auf 210 zusammenhaengende Tage gesperrt (Kompendium E.2). Die
oeffentliche Deribit-API haelt DVOL **ab ~2021-04** (belegt, s. 3.1) - das waeren ~1.980 statt 112
Tage, **sofort verfuegbar**.

**Wichtige Registry-Klarstellung:** Das ist KEINE Entsperrung von H-26 und kein
Torpfosten-Verschieben. H-26 ist gegen `done_days` des Harvesters vorregistriert und bleibt es. Ein
DVOL-REST-Backfill ist eine **neue, eigens vorzuregistrierende Hypothese** (H-27) auf einer anderen
Datenquelle, mit eigener Quellen-Verifikation (stimmen die 112 ueberlappenden Tage zwischen
REST-Backfill und Harvester bit-nah ueberein? Das ist zugleich der beste denkbare
Kreuz-Validierungstest der Quelle). Beide koennen nebeneinander stehen.

### 3.5 Vorschlag: deterministischer DAILY-PANEL-CACHE (WP-7)

Analog WP-0, mit drei bewussten Abweichungen.

**Layout.** `<cache>/panel_1d/source=<src>/category=<cat>/symbol=<sym>/year=<yyyy>/panel.parquet`
plus Sidecar `manifest.json`.

*Abweichung 1 - Jahres- statt Tages-Partitionen.* Der Bar-Cache partitioniert je Symbol-Tag: bei 5
Symbolen x 2.000 Tagen sind das 10.000 Verzeichnisse, bei 1.500 Symbolen x 2.190 Tagen waeren es
**3,3 Mio** - auf NTFS ein Betriebs-Desaster (Verzeichnis-Metadaten, Small-File-Overhead, Backup).
Jahres-Partitionen ergeben ~10.500 Dateien; Preis: das laufende Jahr ist nicht unveraenderlich.

*Abweichung 2 - `frozen/` vs. `open/`.* Abgeschlossene Kalenderjahre liegen unter `frozen/`, sind
unveraenderlich und fingerprint-tragend. Das laufende Jahr liegt unter `open/` und wird bei jedem
Build neu geschrieben. Ein urteilstragender Lauf muss entweder ausschliesslich `frozen/`-Jahre
nutzen ODER den Fingerprint der `open/`-Partition zur Laufzeit pinnen und in der Registrierung
zitieren. Das ist die reversibelste Option (DEC-19).

*Abweichung 3 - eigenes Manifest statt Harvest-Manifest.* Ein REST-Backfill hat keine
Harvester-Manifest-Zeilen, `manifest_done_days()` ist hier nicht anwendbar. Ersatz:
`panel_manifest.sqlite`, Tabelle `partitions(source, category, symbol, year, status, n_rows,
first_date, last_date, expected_days, sha256_values, fetched_at, api_note)` mit `status in {DONE,
PARTIAL, EMPTY, FAILED}`. **DONE** verlangt `n_rows == expected_days`, wobei `expected_days` aus dem
Listing-Datum des Instruments (Roster, 3.3.1) und dem Jahresende abgeleitet wird. **Loud-Fail**
(Kompendium C.14) bei Abweichung - nie stilles Einfrieren eines Loch-Jahres.

**Schema (Spalten je Symbol-Tag).**
```
day_idx            int64    Epoch-Tage UTC (analog minute_idx)
px_open, px_high, px_low, px_close    float64
vol_base, turnover_quote              float64
funding_sum, funding_n                float64 / int64
oi_close_base, oi_close_quote         float64 (NULL wo keine Historie)
is_listed                             bool    (aus Point-in-Time-Roster)
src_kline_rows, src_funding_rows, src_oi_rows   int64  (Provenienz)
```
**Bewusst NICHT im Cache:** abgeleitete Faktoren (Momentum, Vol, Ranks). Der Cache haelt Aggregate,
die Treiber rechnen Faktoren - das ist die WP-0-Lehre und sie verhindert, dass eine Faktordefinition
heimlich in die Infrastruktur wandert und dort unversioniert mutiert.

**`funding_n` ist kein Luxus:** Bybit hat Symbole mit 8-h- UND mit 1-h- Funding, und Intervalle
aendern sich ueber die Historie. Ohne die Zaehlung addiert man stillschweigend Aepfel und Birnen -
dieselbe Fehlerklasse wie die zwei `publicTrade`-Dialekte (INFRA_OPS_MAP 1.4), die 19 von 50 H-12-
Tagen entwertet hat.

**Fingerprints.** `panel_fingerprint(source, category, symbol, year)` = SHA-256 ueber die exakten
Wertbytes aller Spalten in kanonischer Reihenfolge, identisches Muster zu `bars_fingerprint`. Dazu
ein **Bereichs-Fingerprint** ueber (Symbolmenge, Jahresbereich), den jede Registrierung zitiert -
forensisch, nie ein Gate-Flag (bar_cache-Docstring).

**Integritaets-Nachpruefung (neu gegenueber WP-0).** Der Harvest-Baum ist lokal und unveraenderlich;
ein REST-Backfill nicht - Boersen revidieren historische Klines gelegentlich. Deshalb: ein geplanter
Job zieht monatlich eine **1-%-Zufallsstichprobe** eingefrorener Partitionen neu und vergleicht
Fingerprints. Abweichung = lautes Alarm-Ereignis, kein stilles Ueberschreiben.

### 3.6 WP-8 - Universums-Spread-Zensus (Vorbedingung fuer Klasse W)

WP-4 hat den Spread fuer BTC/ETH gemessen (exakt ein Tick). Fuer alles ausserhalb der Majors ist er
ungemessen. Der Zensus ist praktisch gratis: `tickers` liefert je Kategorie in EINEM Request
Bid1/Ask1 fuer alle Symbole. Erste Handlung ist jedoch die **Inhaltsprobe** auf den bereits
vorhandenen `bybit/tickers`-Strom (3.751 Symbole, 43 Tage) - moeglicherweise ist der Zensus auf
Bestandsdaten in Minuten rechenbar und braucht gar keine neue Sammlung. Ergebnis: `PERP_SPREAD_BP`
je Symbol-Dezil, was die Kostenkonstante fuer `tradability3.perp` ueberhaupt erst definierbar macht.

---

## 4. RECHEN-BUDGET

### 4.1 CPU, Minuten (die 3.0-Normallast)

| Aufgabe | Groesse | Erwartete Laufzeit |
|---|---|---|
| Faktor-Berechnung auf dem Daily-Panel | 1.500 Sym x 2.190 Tage = 3,3 Mio Zeilen | **Sekunden** (numpy/polars) |
| Quer-Schnitts-IC + 1.000 Permutations-Nullen | 250 Wochen x 1.500 Sym x 1.000 | **< 1 min** |
| Stationaerer Block-Bootstrap, 10.000 Replikate, 200 Varianten | | **Minuten** |
| Placebo-Verteilung Ereignis-Studie, 1.000 Laeufe | | **Minuten** |
| Hourly-Panel-Aggregation (40 Mio Zeilen, DuckDB) | | **~10-30 min** |
| Minuten-Panel Top-50 (80 Mio Zeilen, ein Voll-Pass) | | **~1-2 h**, out-of-core |
| Voller REST-Backfill (3.2, Zeilen 1/2/3/5/6/7) | | **~8,5 h**, netz-, nicht CPU-gebunden |

**Kernaussage:** Die gesamte 3.0-Methodik der Klassen P, W und E ist **CPU-Arbeit in Minuten**. Der
82-GB-RAM-Rechner ist hier grosszuegig dimensioniert, nicht knapp.

### 4.2 Was die RTX 5060 Ti (16 GB) wirklich braucht

Ehrliche Antwort: **in den Klassen P, W und E nichts.** Keine der Metriken (IC, Praemie, CAR,
Bootstrap, Permutation, FDR) ist GPU-gebunden. Die GPU wird nur gebraucht fuer:
- Sequenzmodelle auf Tick-Tapes (H-15-Klasse),
- grosse Hyperparameter-Sweeps von Deep-Modellen (H-14/H-17-Klasse),
- CNN-Klassifikation auf Bild-/Skalogramm-Darstellungen (H-16-Klasse).

Alle drei haben in 2.0 zusammen ~350 GPU-Stunden gekostet und **null registrierte
Tradability-Folge** erzeugt (K-0.7).

### 4.3 Was auf diesem PC NICHT machbar ist

- **L2-Buchrekonstruktion ueber ein breites Universum.** Die Daten existieren gar nicht
  (Harvest-Baum: L2 nur BTC/ETH, 961/530 Tage; SOL/BNB/ XRP je 35 Tage) und waeren im TB-Bereich.
- **Tick-Analysen ueber ein breites Universum.** `publicTrade` existiert nur fuer 5 Symbole.
- **Minutenbars fuer das gesamte Universum** (3.2 Zeile 4): 260 h Netz, ~100 GB - und der Horizont
  ist nach K-0.1 ohnehin unter der Wand.
- **Training eines Foundation-Modells von Grund auf**, oder Long-Context-Transformer ueber
  Millionen-Token-Tapes bei brauchbarer Batch-Groesse - 16 GB VRAM sind dafuer die harte Grenze.
- **Alles, was einen zweiten, gleichzeitigen Grosslauf braucht.** Ein Einzelbetreiber, eine
  Maschine: Laeufe sind seriell, und die Kalenderzeit ist die knappe Ressource, nicht die FLOPS.

### 4.4 Lehren aus H-15 (180 h GPU) - verbindliche Budget-Regeln

1. **GPU-Standardbudget je Hypothese = 0.** Ein GPU-Lauf braucht eine registrierte Begruendung,
   warum die CPU-Fassung die Frage nicht beantworten kann.
2. **Harte Obergrenze 24 h Wall-Clock je Hypothese** (statt 180 h). Wer mehr braucht, hat die Frage
   falsch geschnitten.
3. **Checkpoint/Resume-Pflicht mit getestetem LESE-Pfad.** GL-030: die Checkpoint-Kennung
   `main_full` wurde beim Schreiben korrekt behandelt, beim Lesen nicht - vier Tests deckten nur den
   Rechenpfad ab. Regel: ein Checkpoint-Test ist nur gruen, wenn er schreibt, den Prozess
   simuliert-abbricht, neu laedt und bit-identisch fortsetzt.
4. **Zwischenergebnis-Checkpoint mindestens stuendlich**, damit ein abgebrochener Lauf trotzdem
   etwas liefert.
5. **Positivkontrolle laeuft ZUERST und separat**, als billiger T1-Schritt, und ihr PASS ist
   Vorbedingung fuer die Einplanung des teuren Laufs. H-14 hat 2-3 GPU-Tage verbrannt und ist danach
   an der Positivkontrolle gescheitert (GL-020) - die Reihenfolge haette das verhindert.
6. **Entscheidungsrelevanz vorab** (1.0): ein GPU-Lauf, dessen bestmoegliches Ergebnis keine
   Entscheidung aendert, wird nicht eingeplant.

---

## 5. REPO-STRUKTUR FUER 3.0

### 5.1 Modul-Konvention (das Bestehende formalisieren, nicht ersetzen)

Das etablierte Muster ist gut und bleibt: `src/bybit_edge/research/<id>/{__init__.py, driver.py,
...}` + `scripts/<id>.py` (duenner CLI-Wrapper mit `sys.path`-Shim) +
`scinance3-impl/handoff_local/run_<id>.ps1`. Ein Verzeichnis loeschen = voller Rueckbau
(DEC-19-Prinzip).

**Eine Verschaerfung:** Der `c24_impact/driver.py`-Docstring ist das beste Artefakt des ganzen Repos:
er nennt Hypothese, registriertes Gate, Benennungs-Korrektur, Positivkontrolle, REZENZ-Klausel,
Abgrenzung zu toten Ansaetzen und Kapitalfreiheit. Vorschlag: **dieser Docstring wird zur
Pflicht-Vorlage** mit festen Abschnitts-Ueberschriften, und ein Test (`test_driver_docstrings.py`)
prueft mechanisch, dass jedes 3.0-Research-Paket alle Pflichtabschnitte traegt. Kosten: eine
Stunde. Nutzen: die beste vorhandene Praxis wird zur Regel statt zur Ausnahme.

### 5.2 Geteiltes Statistik-Modul `research/stats3/`

Befund: `benjamini_hochberg` ist in **17 Research-Paketen dupliziert** (c06, c07, c09, c12, c13, c14, c15,
c16, c17_venue, c17_c41_lead_lag, c17_c41_tradability, c19, c20, c24, c31, c42, c01). Der Grund ist
dokumentiert und gut ("jedes Research-Paket haelt seine eigene Kopie, kein Cross-Import des
FDR-Helpers") - ein adjudizierter Lauf darf sich nie nachtraeglich unter der Hand aendern.

Vorschlag, der beides bewahrt: **`research/stats3/` als NEUES, versioniertes Modul, das
ausschliesslich 3.0-Module importieren.** Bestehende Pakete bleiben unberuehrt (append-only).
Inhalt: `benjamini_hochberg`, `stationary_bootstrap`, `politis_white_block_length`,
`cluster_bootstrap`, `permutation_null_ic`, `deflated_sharpe`, `min_track_record_length`,
`expected_max_drawdown`, `nw_hac_se`, `hansen_hodrick_se`, `lo_sharpe_se`, `expected_max_sharpe`.
Jede Funktion mit gepinntem Unit-Test und einer `STATS3_VERSION`, die in jeden Ergebnis-Payload
wandert.

### 5.3 Registry-Format: YAML neben Markdown?

**Vorteile einer maschinenlesbaren Registry:**
- Die neuen Pflichtzeilen (struktureller Nulleffekt, Power, Selektions-Decke, oekonomische
  Mindestmagnitude, Entscheidungsrelevanz, FDR-Familie) werden zu **Feldern, die ein Linter
  erzwingen kann** - ein Lauf ohne vollstaendigen Eintrag startet gar nicht erst.
- Der Gate-Auditor kann ein Ergebnis-JSON **mechanisch** gegen die registrierten Schwellen pruefen.
  Das ist die groesste verbleibende menschliche Fehlerquelle (GL-029 war ein Runner-Bedienfehler,
  kein Methodenfehler).
- Die zweistufige FDR (DEC-22) wird automatisch anwendbar, weil die Familienzugehoerigkeit
  berechenbar wird statt von Hand gefuehrt.
- Ein Test kann pruefen: "hat jeder Treiber mit `HYPOTHESIS_ID` einen Registry-Eintrag, und stimmen
  die Schwellen im Code mit denen im Eintrag ueberein?"

**Nachteile:**
- YAML traegt die **Prosa nicht**, die den eigentlichen Gehalt ausmacht. Der H-04-Eintrag lebt von
  seiner Begruendung, nicht von seinen Zahlen.
- Zwei Quellen der Wahrheit laden zum Auseinanderdriften ein - und die Registry ist append-only und
  urteilstragend, ein Drift waere fatal.
- Migration der 26 Bestands-Eintraege wuerde einen **append-only-Datensatz nachtraeglich anfassen**.
  Das ist ein Verstoss gegen die Kernregel.

**Empfehlung (reversibelste Option, DEC-19):**
1. **Die 2.0-Registry wird NICHT migriert. Punkt.**
2. Fuer 3.0: der Markdown-Eintrag bleibt der **normative Text**. In den Eintrag wird ein **gezaunter
   YAML-Block** eingebettet, der die maschinenlesbare Teilmenge haelt: `id, capital_free, metric,
   windows[], threshold, structural_null, selection_ceiling_K, power_at_threshold, economic_minimum,
   fdr_family, over_family, feasibility_verdict, decision_relevance,
   fixtures{positive,null,adversarial}, data_fingerprints[], stats3_version`. **Eine Datei, eine
   Quelle der Wahrheit**, per Parser extrahierbar.
3. Ein Test erzwingt: jeder 3.0-Eintrag parst, hat alle Pflichtschluessel, und jeder registrierte
   `id` hat genau einen Treiber. Migrationsaufwand: **null fuer 2.0, ~1 h Werkzeugbau fuer 3.0.**

### 5.4 Test-Pflichten je Research-Modul (3.0)

| Stufe | Inhalt | Ausgeloest durch |
|---|---|---|
| T0 | Unit-Tests der reinen Funktionen auf synthetischen Eingaben | Standard |
| T1 | **Drei Fixtures als echte Tests**: positiv (Effekt wird gefunden), null (kein Effekt), adversarial (bekanntes Artefakt wird NICHT als Effekt gemeldet) | DEC-39, erweitert (1.0) |
| T2 | **Determinismus mit N>=3** Laeufen plus Fingerprint-Vergleich | DEC-34 / Kompendium C.7 ("N=2 beweist keinen Determinismus") |
| T3 | **Checkpoint-Round-Trip**: schreiben, abbrechen, laden, bit-identisch fortsetzen | GL-030 |
| T4 | **Gate-Arithmetik-Test**: die Gate-Entscheidungsfunktion liefert auf einem konservierten Ergebnis-Payload das registrierte Urteil | neu - macht das Gate maschinell pruefbar |
| T5 | **Kosten-Konstanten-Pin** fuer jedes Tradability-Modul (`constants_hash`) | DEC-13/16, Anti-Gaming (2.4) |
| T6 | **Legacy-Import-Sperre**: `test_no_legacy_imports.py` verbietet jedem 3.0-Modul Importe ausserhalb `{config, persistence.db, research}` | macht die `_legacy_v1`-Quarantaene der UMBAU_SPEZIFIKATION dauerhaft statt einmalig |

Zusaetzlich unveraendert bindend aus der Abnahme-Checkliste (INFRA_OPS_MAP 7): Test-Anzahl vorher ==
nachher, die vier Forensik-Tests byteidentisch, `data/harvest` ueberall read-only, Fingerprint- und
Schema-Version-Mechanik in jedem abgeleiteten Speicher.

---

## 6. KRITISCHE WUERDIGUNG DER BISHERIGEN METHODIK

### 6.1 Was unnoetig teuer war

**(a) GPU-Wellen H-14..H-18: ~350 GPU-Stunden ohne Tradability-Perspektive.** Das ist nicht die
Kritik "Deep Learning bringt nichts", sondern eine strukturelle: Kompendium E.10 listet H-15b und
H-16b als **explizit NICHT registriert und NICHT impliziert**. Die Hypothesen waren also so
geschnitten, dass ihr **bestmoegliches Ergebnis keine Entscheidung aendern konnte** - es gab keinen
Pfad von "Transformer schlaegt Markov um 2 % Cross-Entropy" zu irgendeiner Handlung. Das war zum
Registrierungszeitpunkt aus der Registry ablesbar, nicht erst im Nachhinein. *Gegenmittel:
Entscheidungsrelevanz-Klausel (1.0).*

**(b) Sechsfache Messung derselben Friktions-Arithmetik.** H-03 (0,01-0,04 bp), H-04b (+0,19 bp),
H-05c (+0,03-0,10 bp), H-09, H-24 - alle auf Sekunden-/Minuten-Horizonten, alle 80-500x unter einer
Wand, die seit PRD 1 bekannt war. Die Horizont-Friktions-Kurve (K-0.1) ist drei Zeilen Arithmetik und
haette alle fuenf a priori erledigt. GL-012 verlangt bereits die Erreichbarkeit der METRIK-Schwelle;
sie muss auf die OEKONOMISCHE ausgeweitet werden. *Gegenmittel: oekonomische Mindestmagnitude (1.0).*

**(c) H-14: Positivkontrolle nach dem teuren Lauf.** 2-3 GPU-Tage, dann faellt die vorregistrierte
Positivkontrolle durch und der ganze Lauf ist "methodisch invalide" - kein Verdikt, keine Aussage.
Kompendium C.13 macht die Kontrolle zur Pflicht, aber nicht zum vorgeschalteten Gate. *Gegenmittel:
Positivkontroll-Vorschaltung (4.4.5).*

**(d) Sperren auf Kalenderzeit, ohne die oeffentliche Alternative zu pruefen.** H-26 wartet seit
Monaten auf 210 Harvester-Tage, waehrend die oeffentliche Deribit-API plausibel ~5 Jahre DVOL haelt
(3.4) - niemand hat einen Request abgesetzt. Dieselbe Fehlerklasse wie Kompendium C.8 (Schluss aus
Abwesenheit von Beweis), nur eine Ebene hoeher. *Gegenmittel: vor jeder daten-gated-Sperre eine
dokumentierte Probe auf oeffentliche Nachladbarkeit.*

### 6.2 Was gefehlt hat

**(a) Portfolio-Sicht.** 26 Hypothesen, jede als isolierte Einzelfrage. Sieben kapitalfreie WEITER
und **keine einzige Messung, wie sie zusammen aussehen** - keine Korrelationsmatrix der ueberlebenden
Signale, keine Kapitalallokation, keine Frage, ob N mittelmaessige Signale gemeinsam ueber die Wand
kommen (Fundamentalgleichung des aktiven Managements: IR ~ IC * sqrt(Breite)). *Vorschlag: eine
eigene Hypothesen-Klasse "Portfolio-Gate" mit eigenem strukturellem Nulleffekt - dem erwarteten
Sharpe einer zufaelligen Gleichgewichtung von K Rauschsignalen.*

**(b) Die Praemien-Klasse.** PRD 1 nennt "nicht-direktionale Praemie" als einen von vier Wegen an der
Wand vorbei - und 25 von 26 Hypothesen gingen in Prognose und Struktur. Die einzige Praemien-
Hypothese (H-26) ist gesperrt.

**(c) Breites Universum.** GL-012 hat bewiesen, dass ein N=5-Panel keine Quer-Schnitts-Statistik
traegt (`max|z| = 2,0`); K-0.5 zeigt, dass das nicht nur die z-Schwelle, sondern die ganze Klasse
betrifft. Trotzdem lief jede Welle auf denselben fuenf Symbolen - bei einem Datenausbau, der ein
Wochenende und 4 GB kostet.

**(d) Explizite Power-Rechnung.** In 26 Registrierungen steht kein einziges Mal, welchen Effekt das
gewaehlte Fenster ueberhaupt sehen kann. Bei H-20 (p=0,17 bei erreichter Magnitude) und H-22
(IC 0,0665 gegen Schwelle 0,10) ist ungeklaert, ob ein echter Effekt verworfen oder korrekt abgelehnt
wurde.

### 6.3 Regeln fuer die 3.0-Verfassung

**Unveraendert uebernehmen** (jede durch einen Vorfall erzwungen): Registry-Disziplin /
Pre-Registration / append-only (C.1); Mess-Gate != Tradability-Gate (C.2); Anti-Gaming-Klausel (C.3);
struktureller Nulleffekt vor der Schwelle (C.4); Determinismus nur mit Wiederholung + Fingerprint,
N=2 zaehlt nicht (C.7); Inhaltsprobe statt Namensschluss (C.8); keine n=1-Extrapolation (C.9); Modul
!= Strategie (C.11); Feasibility-Check GL-012 (C.12); Loud-Fail (C.14); Checkpoint-Round-Trip (C.15);
zweistufige FDR (C.16); Data-Snooping-Offenlegung und Entdeckungszellen-Ausschluss (C.17);
REZENZ-Klausel (C.18); reversibelste Option (C.19).

**Neu aufnehmen**, je mit dem erzwingenden Vorfall: (1) Entscheidungsrelevanz-Klausel - H-14..H-17;
(2) Power-Zeile - 26 Registrierungen ohne Power-Rechnung; (3) oekonomische Mindestmagnitude aus der
Horizont-Friktions-Kurve - H-03/H-04b/H-05c; (4) Selektions-Deflation (K zaehlen, DSR/K_eff
berichten, Decke am Null-Fixture messen) - H-11 in einer zweiten Metrik; (5) drittes, adversariales
Fixture - H-20 und das Peso-Problem; (6) Cluster-Einheit-Klausel (Resampling-Einheit und effektives N
benennen) - Kolari/Pynnoenen, H-10/H-21; (7) Kostenmodell-Bindung (`constants_hash` im Ergebnis) -
macht C.3 maschinell pruefbar; (8) Irreversibilitaets-Regel (nur nicht-nachladbare Daten
rechtfertigen einen Dauerstrom; keine daten-gated-Sperre ohne Nachladbarkeits-Probe) - H-26/DVOL;
(9) Positivkontroll-Vorschaltung - H-14; (10) Panel-Mitglieder sind keine Hypothesen -
H-06/H-08/H-09/H-22-Praxis, die bei N=200 die Power zerstoeren wuerde.

**Entschaerfen - mit Herleitung, nicht mit Bauchgefuehl:**

*Das harte Ein-Fenster-DROP-Kriterium (PRD 8.5 / C.10)* ist fuer billige, hoch-gepowerte Messungen
richtig und bleibt dort unveraendert. Fuer die Klassen P und W ist es nach K-0.6 eine Typ-II-
Maschine: bei Per-Fenster-Power 0,5 verwirft es drei von vier echten Effekten. Vorschlag: je Fenster
nur **Vorzeichen-Konsistenz plus Magnituden-Band**, das Signifikanzurteil auf dem **gepoolten**
Schaetzer mit fenster-geclustertem stationaerem Bootstrap; Retention steigt nach K-0.6 um Faktor ~4,7
bei praktisch unveraenderter Falsch-Positiv-Kontrolle, weil die gepoolte Statistik das alpha traegt.
**Diese Aenderung wird VOR jedem 3.0-Lauf beschlossen und schriftlich hergeleitet** - sie ist damit
ausdruecklich keine Torpfosten-Verschiebung (die waere: nach dem Sehen einer Zahl). Wer sie nach
einem Lauf vorschlaegt, verstoesst gegen C.1.

*"Kein Live-Order-Code"* bleibt, aber sein Preis muss benannt werden: Fill-Wahrscheinlichkeiten sind
nie messbar, also bleibt jede Maker-Annahme unfalsifizierbar - und Maker ist nach K-0.1 der
Unterschied zwischen 53 Minuten und 6,6 Stunden Mindesthorizont. Mittelweg ohne Regelbruch: eine
kapitalfreie **Quote-Schatten-Messung** (aus rein oeffentlichen Daten die Warteschlangen-Position
einer hypothetischen eigenen passiven Quote rekonstruieren, Fill-Rate schaetzen). Keine Order, kein
Kapital, kein Key.

*Recording-Engine F0 als "Schutzgut #1"* schreibt Stroeme, die **kein Treiber liest** (DEC-43), und
mindestens ein Ziel ist anderweitig abgedeckt (DEC-46). Die dafuer vorgesehene **Sunset-Review (PRD
9, faellig ~2026-09-11) ist nie gelaufen.** Empfehlung: nicht abschalten, sondern die Review
planmaessig durchfuehren und danach nur behalten, was eine registrierte 3.0-Hypothese namentlich
braucht. Die Anti-Data-Lake-Regel steht im PRD; sie wurde nur nie vollzogen.

---

## 7. WAS ICH NICHT VORSCHLAGE - UND WARUM

- **Keine Migration der 2.0-Registry nach YAML.** Sie ist append-only und urteilstragend; sie
  nachtraeglich anzufassen waere ein schwererer Fehler als jeder Komfortgewinn (5.3).
- **Keine Neufassung bestehender Research-Pakete auf ein geteiltes Statistik-Modul.** Ein
  adjudizierter Lauf darf sich nicht unter der Hand aendern; `stats3` gilt nur fuer Neues (5.2).
- **Kein CI-System als Vorbedingung.** Es existiert heute keines (INFRA_OPS_MAP 7); die
  Test-Pflichten aus 5.4 duerfen nicht davon abhaengen - der reale Qualitaets-Gate ist
  `pytest tests/unit/` plus die Handoff-Runner.
- **Keine Minutenbars fuer das gesamte Universum** (260 h, 100 GB) fuer einen Horizont, der nach
  K-0.1 unter der Wand liegt.
- **Keine bezahlten Datenquellen.** Alles in Abschnitt 3 ist oeffentlich und key-frei; Tardis ist
  ohnehin tot (2 Tage / 3 Monate Sampling, Kompendium D.17).
- **Keine neue GPU-Welle in Welle 1 von 3.0** - nicht weil GPU-Methoden schlecht sind, sondern weil
  keine der drei tragenden Klassen sie braucht (4.2) und die Entscheidungsrelevanz-Klausel sie a
  priori nicht durchlaesst.
- **Keine Wiederauflage eines Kompendium-D-Ansatzes**, insbesondere kein Spread-Capture (D.1), kein
  OFI-Vorzeichen (D.5), kein Branching-Ratio ohne Erreichbarkeits-Nachweis (D.2), kein reaktives
  Long-Vol (D.15).

---

## 8. QUELLEN

**Literatur (belegt).** Lo (2002, FAJ 58(4)) SE des Sharpe inkl. Mertens-Erweiterung fuer
Schiefe/Kurtosis. Bailey & Lopez de Prado (2014, SSRN 2460551) Deflated Sharpe Ratio; die
E[max]-Formel `(1-g)*Phi^-1(1-1/K) + g*Phi^-1(1-1/(K*e))`, g ~ 0,5772, ist per Websuche gegen die
Quelle bestaetigt (dortiges Beispiel: 1.000 unabhaengige Backtests -> erwarteter Max-Sharpe 3,26 bei
wahrem SR = 0). Bailey & Lopez de Prado (2012, JPM 40(1)) Minimum Track Record Length. Politis &
Romano (1994, JASA 89(428)) stationaerer Bootstrap; Politis & White (2004, Econometric Reviews 23(1),
Korrektur Patton/Politis/White 2009) automatische Blocklaenge. Newey & West (1987, Econometrica
55(3)); Andrews (1991, Econometrica 59(3)); Hansen & Hodrick (1980, JPE 88(5)).
Boudoukh/Richardson/Whitelaw (2008, RFS 21(4)) und Valkanov (2003, JFE 68(2)) zu Langhorizont-
Scheinprognostizierbarkeit. Kolari & Pynnoenen (2010, RFS 23(11): 3996-4025) Ereignis-Clustering und
Ueberverwerfen - per Websuche belegt. Boehmer/Musumeci/Poulsen (1991, JFE 30(2)); Corrado (1989, JFE
23(2)); Brown & Warner (1985, JFE 14(1)). Magdon-Ismail et al. (2004, J. Appl. Prob. 41(1))
E[MaxDD] driftloser BM. Carr & Wu (2009, RFS 22(3)) und Bakshi & Kapadia (2003, RFS 16(2))
Varianzrisikopraemie. Harvey/Liu/Zhu (2016, RFS 29(1)) t-Huerde bei Multiple Testing. Almgren et al.
(2005, J. Risk 18(4)) Wurzelgesetz des Market Impact - Funktionalform belegt, k fuer Bybit UNBELEGT.

**API-Fakten (Websuche auf die Original-Doku; die Domains selbst sind vom Egress-Proxy blockiert,
daher nicht direkt verifiziert).** Bybit `/v5/market/kline`: `limit` [1,1000], Default 500. Bybit
Rate Limit: 600 Requests / 5 s / IP fuer `api.bybit.com`, Ueberschreitung -> "403 access too
frequent" plus 10 min Sperre. Bybit `/v5/market/funding/history`: `limit` [1,200] Default 200,
`startTime` allein ist ein Fehler. Bybit `/v5/market/open-interest`: 200 Punkte je Aufruf,
Cursor-Paginierung. Deribit DVOL: historisch verfuegbar ab ~2021-04-01 (Amberdata-Doku). Binance
`/fapi/v1/klines`: 2.400 Gewicht/min/IP, ~2 Gewicht je Aufruf, Historie ab Futures-Start 2019.

**UNBELEGT - je ein Request klaert es auf der Nutzer-Maschine.** Rueckreichweite der
Bybit-Funding- und OI-Historie; ob `instruments-info` delistete Symbole fuehrt; Feldinhalt und Takt
des vorhandenen `bybit/tickers`-Stroms; Deribit-Resolution-Werte und Punkte-Limit; Tiefe von
`get_last_settlements_by_currency` / `get_delivery_prices` / `get_instruments?expired=true`;
Binance-`limit`-Maximum (1000 vs. 1500); Bybit-Margin-Regeln; Bybit-Options-Delivery-/Exercise-
Gebuehr; Impact-Parameter k; Symbolzahl je Bybit-Kategorie (die 1.500 in 3.2 ist eine erklaerte
Annahme, keine Messung).

*Ende R4_METHODIK_INFRA.md*
