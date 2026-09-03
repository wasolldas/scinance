# S1 - SURVIVAL-ANALYSE UND EPIDEMIOLOGIE

**Phase:** 3b Wissenschafts-Exkurs (Scinance 3.0)
**Scout:** S1, Disziplin Survival-Analyse / Epidemiologie
**Stand:** 2026-09-03
**Gelesen (vollstaendig):** `survey/ERKENNTNIS_KOMPENDIUM.md` (A-F), `PRD_SCINANCE3.md`
(1, 2, 3.1-3.5, 4.1-4.4, 5.1-5.2, 9.1-9.3), `results/CROSSDOMAIN_PARK.md`,
`results/CROSSDOMAIN_PRD.md`, ergaenzend `scinance2-impl/FINAL_PRD_SCINANCE2.md`
Par. 5/6, `state/decisions.md` DEC-54..57, `src/bybit_edge/_legacy_v1/layers/
l5_risk/m26_sir.py`, `strategies/strategy1_cascade.py`, `tests/unit/
test_m26_sir.py`, `scinance2-impl/state/CRITICAL_REVIEW_2026-07-09.md` und
`CRITICAL_REVIEW_2_2026-07-13.md`.

> **Umfang.** ~730 Zeilen statt der angepeilten 300-500. Der Ueberhang liegt
> im Pflichtteil zu `m26_sir.py` (Abschnitt 1, ~95 Zeilen Code-Forensik) und in
> Abschnitt 4.1, wo die GL-012-Arithmetik fuer die gesamte Liquidations-
> Kontagionsfamilie ausgerechnet statt behauptet wird. Die vier Vorschlaege
> selbst liegen bei ~90 Zeilen je Eintrag - das ist die Untergrenze fuer die
> zehn Pflichtfelder aus dem Ausgabeformat.

> **Belegregel dieses Dokuments.** Jede Zahl traegt Herleitung oder Quelle.
> `[sek]` = nur ueber Sekundaerquelle belegt, mit Nennung. **UNBELEGT** wo
> nichts vorliegt. **UNGEMESSEN - <Paket>** wo die Zahl im Programm noch nicht
> existiert. Der Egress-Proxy blockte `papers.ssrn.com`,
> `www.alexandria.unisg.ch` und `www.sebastianstoeckl.com` - Volltexte nicht
> primaer geprueft, entsprechend etikettiert.

---

## 0. Was diese Disziplin beitraegt - und was nicht

Survival-Analyse ist die Statistik von **Zeit bis Ereignis unter unvollstaendiger
Beobachtung**. Ihr Beitrag ist nicht ein weiteres Prognosemodell, sondern die
korrekte Behandlung dreier Datensituationen, die im Bestand ueberall vorliegen
und im Programm bisher **nie** als solche benannt wurden: **Rechts-Zensierung**
(Symbol delistet, L2-Aufzeichnung reisst, Fenster endet), **Links-Trunkierung**
(WP-7: Eintritt erst nach `>= 8 Wochen` Bars) und **konkurrierende Risiken**
(Order: Fill vs. adverse Bewegung; Funding-Regime: Vorzeichenwechsel vs.
Intervallwechsel vs. Delisting).

Wo Zensierung **informativ** ist - also mit der gesuchten Groesse korreliert -
sind naive Schaetzer verzerrt, in einer vorab bestimmbaren Richtung. Deshalb
liefert die Disziplin hier **Enabler und Nulleffekt-Kalibrierungen** (Klasse X),
keine Kante. Alle vier Vorschlaege sind horizontfrei (Randbedingung 3), keiner
braucht neue Daten ausser dem in PRD 7.1 ohnehin geplanten Funding-Backfill,
keiner braucht GPU (DEC-57 eingehalten).

**Was diese Disziplin hier NICHT beitragen kann:** die epidemischen
Kontagionsmodelle (SIR/SEIR) fuer Liquidationsausbreitung. Das ist der
unangenehmste Teil des Auftrags und steht deshalb zuerst.

---

## 1. PFLICHTTEIL: `m26_sir.py` - was es tat, und wie es zu bewerten ist

### 1.1 Was der Code tatsaechlich tut

`src/bybit_edge/_legacy_v1/layers/l5_risk/m26_sir.py`, 312 Zeilen, Klasse
`M26SIR`, Schnittstelle `compute(liq_events, open_interest, current_ts)`:

- **Kompartimente:** `S = OI - kumuliertes Liq-Volumen` (Untergrenze 1,0),
  `I = Volumen des juengsten Liquidations-Events`, `R = kumuliertes
  Liq-Volumen`.
- **Kalibrierung:** OLS von `dI/dt` auf `[S*I, I]` ueber die juengsten
  **20** Events (`_CALIBRATION_WINDOW_MAX_EVENTS`), geschlossene
  Normalgleichung; Fallback `beta = 0,001`, `gamma = 0,1` bei < 10 Events,
  singulaerer Matrix oder unplausiblem Vorzeichen.
- **Signal:** `r0 = beta * s_current / gamma`, Alarm bei
  `r0 > SIR_R0_CASCADE_THRESHOLD = 1.0` (`config.py:419`).
- **Vorwaerts-Simulation:** `scipy.integrate.odeint` ueber 30 min in 180
  Schritten auf **normalisierten** Anteilen `y0/n_total`, daraus
  `peak_i_forecast`.
- **Confidence:** Heuristik `min(n_events/50, 1)*0,5 + min(|r0-1|/2, 1)*0,5`.

Verbraucher: `pipeline.py:190/291` (Feld `sir` im `decision_aggregator`) und
`strategy1_cascade.py:127` - also **S1**, nicht S3/S5 (die Auftragszeile
"Layer-Modul fuer S3/S5" ist zu korrigieren; S3 nutzt `m22_funding_pressure`).
In S1 ist `r0 > 1,0` die **vierte** von vier Eintrittsbedingungen
(`strategy1_cascade.py:258-260`).

### 1.2 Zwei bestaetigte Konstruktionsfehler, je von 3/3 Pruefern

- **Einheiten-Inkonsistenz** (`CRITICAL_REVIEW_2026-07-09.md`, `m26_sir.py:225`):
  `beta`/`gamma` werden auf **absoluter** S-Skala (Groessenordnung OI) je
  Event-Index kalibriert, `r0` aber gegen die **epidemiologische** Schwelle 1,0
  verglichen, und dieselben Parameter auf **normalisierte** Anteile losgelassen.
  Im Fallback (`beta=0,001`) ist `r0 = 0,01 * s_current` - bei OI in
  Zehntausenden also Hunderter- bis Millionenbereich; `cascade_risk` feuert
  praktisch bei jedem Tick.
- **Konstante-OI-Approximation** (`CRITICAL_REVIEW_2_2026-07-13.md`,
  `m26_sir.py:219`): `oi_history = [open_interest] * len(calib_events)` speist
  fuer JEDEN historischen Zeitpunkt das aktuelle (waehrend einer Kaskade:
  niedrigste) OI ein. `S(t)` ist fuer die fruehen Events massiv unterschaetzt -
  genau dort, wo das Modul messen soll.

### 1.3 Testlage: 13 Unit-Tests, kein Datenlauf

`tests/unit/test_m26_sir.py` enthaelt 13 Tests, alle auf **synthetischen**
Events (`_make_liq_events`), teils mit direkt gesetzten `_beta`/`_gamma`:
Massenerhaltung, Division-durch-Null-Schutz, Return-Keys, Reset. **Kein Test
prueft die Einheiten-Konsistenz, keiner die Erreichbarkeit der Schwelle 1,0 auf
echten Daten.** Ein isolierter Datenlauf hat nie stattgefunden - das ist der
Kern der Auftragsfrage.

### 1.4 Verdikt: SUSPECT nach Buchstabe, tot nach Entsperrbedingung

**Nach C.11 (Modul != Strategie) bleibt C-26 formal SUSPECT.** Der Weg von
CS-01 zu einer Widerlegung ist blockiert: S1 scheiterte an Bedingung 1
(`rho <= 0,85`, `rho`-Median ~2e-7, D.2), erreichte Bedingung 4 (`r0 > 1`) nie,
und `FINAL_PRD_SCINANCE2.md` Par. 6 haelt das woertlich fest: "nur C-14 ist
isoliert belastet; C-15/C-26 bleiben SUSPECT/UNTESTED". Ein Upgrade auf REFUTED
waere ein Registry-Verstoss.

**Operativ ist es trotzdem tot, und zwar aus drei unabhaengigen Gruenden:**

1. **Das Programm hat ihm bereits das Pilot-Budget entzogen.**
   `FINAL_PRD_SCINANCE2.md` Par. 5 PARK-Register, woertlich:
   `C-26 SIR R0 | SUSPECT (CS-01, E-02); in C-39 absorbiert | geht in C-39 auf;
   kein eigener Pilot`. Das ist keine Interpretation, das ist die eingetragene
   Entscheidung.
2. **Die Entsperrbedingung ist unerreichbar geworden.** C-39 entsperrt "nach
   C-36-Recording von insurance.USDT/adlAlert + Stress-reichem Fenster". C-36
   lieferte laut GL-004 fuer `rpi`/`insurance` NO_DATA (Subscribe bestaetigt, 0
   Frames), und Kompendium E.13 haelt fest, dass C-36 **gemaess DEC-43 nicht
   repariert wird**. Eine Entsperrbedingung, deren Vorbedingung planmaessig nie
   erfuellt wird, ist keine Bedingung mehr.
3. **`R0` IST ein Branching-Ratio** - der entscheidende Punkt. `R0 =
   beta*S0/gamma` ist definitionsgemaess die erwartete Zahl Sekundaerfaelle je
   Primaerfall, also dieselbe Groesse, die im Hawkes-Prozess der
   Verzweigungsgrad `n = Integral des Kernels` ist (Aequivalenz auch in der
   Literatur, u. a. Rizoiu et al. "SIR-Hawkes" [sek, Suchtreffer]; fuer das
   Argument nicht noetig, die Definition genuegt). **D.2 verbietet jeden
   Branching-Ratio-Ansatz ohne vorgeschaltete Erreichbarkeitspruefung der
   Schwelle.** "SIR-Kaskadenalarm bei R0 > 1" ist damit eine Umbenennung von
   C-14 mit anderem Schaetzer - und zwar spiegelbildlich: C-14s importierte
   0,85 war strukturell **nie** erreichbar, M26s 1,0 wegen des Einheitenfehlers
   strukturell **immer** ueberschritten. Dieselbe Fehlerklasse (L-1), zweimal,
   in beide Richtungen.

**Der einzige nicht-branching-artige Inhalt von SIR** ist der Erschoepfungsterm
`-beta*S*I`: Hawkes ist linear und kennt keine Depletion, SIR kennt sie. Eine
Depletion-These waere formal keine Umbenennung - sie ist aber (a) keine
ODE-Frage, sondern eine Hazard-Frage mit zeitabhaengiger Kovariate "kumulativ
liquidiertes Notional relativ zum verfuegbaren OI", also Werkzeug **dieser**
Disziplin statt der Epidemiologie, und (b) auf dem verfuegbaren Design
strukturell nicht powerbar (Rechnung in 4.1(c)). Ein GL-012-Fall und deshalb
**kein Vorschlag**.

---

## 2. VORSCHLAEGE

Vier Vorschlaege, alle Klasse **X (Enabler-Messung)**, X-SURV-2 zusaetzlich mit
einem Regime-Arm (R).

---

### X-SURV-1 - Delisting-Hazard und IPCW-Korrektur des Point-in-Time-Universums (WP-7)

**Methode.** Das Delisting eines Perp-Symbols ist ein rechts-zensiertes
Ereignis; der WP-7-Eintritt (`>= 8 Wochen Bars`) ist eine
**Links-Trunkierung**. Das Point-in-Time-Universum ist damit formal ein
links-trunkierter, rechts-zensierter Survival-Datensatz, keine simple Tabelle.
Gemessen wird (a) die Delisting-Hazard mit einem Diskret-Zeit-Hazard-Modell
(Symbol-Wochen-Panel, gepoolte Logit-Form; Cox 1972 JRSS-B 34:187-220 in der
Zaehlprozess-Form von Andersen/Gill 1982 Ann. Statist. 10:1100-1120; kanonische
Finanz-Uebertragung: Shumway 2001 J. Business 74:101-124) mit den
A3-Charakteristika (Momentum, Reversal, Vol) als zeitabhaengigen Kovariaten;
(b) daraus die **Inverse-Probability-of-Censoring-Gewichte** und ein
IPCW-gewichteter Querschnitts-IC (Robins/Finkelstein 2000 Biometrics
56:779-788). Die Frage: **haengt die Delisting-Hazard von genau der
Charakteristik ab, auf die A3 sortiert?** Wenn ja, ist die Zensierung informativ
und der naive IC verzerrt - und die Verzerrung wird bezifferbar statt nur
"vorhanden". Fundament Links-Trunkierung: Klein/Moeschberger 2003.

**Uebertragung auf den Bestand.** Strom: ausschliesslich das in WP-7 ohnehin
gebaute `panel_1d` (`instruments-info?category=linear` fuer `status`,
`kline?interval=D` fuer die Historie, ~1.000 Symbole inkl. delisteter, ~3.000
Calls, ~10 min, 40-80 MB, PRD 4.1). Aufloesung: Tag fuer die Historie, Woche
fuer die Risikomenge. Symbole: das volle Bybit-Linear-Perp-Universum, nicht die
5 Majors. Horizont: entfaellt. Klasse: **X**. Kein zusaetzlicher Download.

**Struktureller Nulleffekt der Metrik.** Drei Komponenten, alle exakt bekannt
oder am Fixture messbar: (i) Unter unabhaengiger Zensierung ist der
Cox-Score-Test asymptotisch exakt chi^2_1 und `beta_hat -> 0`; das ist ein
**echter Nulleffekt, kein Dressing-Geschenk** (Gegenbeispiel zu B.9). (ii)
IPCW-Gewichtung **erhoeht** die Varianz des IC mechanisch, auch wenn sie den
Punktschaetzer nicht bewegt - dieser Aufschlag ist der Nulleffekt der
Korrektur und wird am WP-7-Null-Fixture (unabhaengige Reihen, lognormale
Vol-Streuung `sigma_log = 0,6`) gemessen, nicht angenommen. (iii) Die
Links-Trunkierung selbst erzeugt bei abhaengigem Eintritt eine Verzerrung, deren
Vorzeichen aus der Konstruktion folgt: die 8-Wochen-Regel schneidet das
Listing-Pump-Artefakt ab, also **gegen** ein Momentum-Signal.

**Feasibility-Skizze.** Cluster-Einheit nach DEC-51 Punkt 3 ist **nicht** das
Symbol: Bybit delistet in angekuendigten **Chargen**, mehrere Symbole am selben
Tag. Die Cluster-Einheit ist damit der **Delisting-Ankuendigungstag**, `N_c` =
Zahl distinkter Delisting-Tage - **UNGEMESSEN, misst dieses Paket zuerst**.
Power nach Schoenfeld 1983 Biometrics 39:499-503 fuer eine
standardisierte stetige Kovariate, zweiseitig (Zensus-Frage, DEC-51 Punkt 1,
`z = 2,8016`, `z^2 = 7,849`), `d` = Zahl der Ereignisse:

```
d = z^2 / (sigma_x^2 * beta^2),  sigma_x = 1
  beta = 0,20 (HR 1,221 je SD) -> d = 197
  beta = 0,30 (HR 1,350 je SD) -> d =  88
  beta = 0,50 (HR 1,649 je SD) -> d =  32
```

Vorab fixierte Lesart: liegt die Zaehlung unter `d = 32` Clustern, ist nur ein
sehr grosser Effekt sichtbar und das Paket berichtet rein deskriptiv (kein
Verdikt, C.12-Etikett). Erwartete Effektgroesse: Ammann/Burdorf/Liebi/Stoeckl
2022, SSRN 4287573, messen auf 3.904 Kryptowaehrungen 2014-2021 eine
annualisierte Verzerrung von **0,93 % (value-weighted) bzw. 62,19 %
(equal-weighted)** und berichten, dass die **1-Wochen-Momentum-Beziehung nach
Korrektur verschwindet** [**sek**, Host gesperrt, s. Abschnitt 5].
**Uebertragungs-Vorbehalt:** das ist ein Spot-Coin-Universum mit weit mehr
Schrott; das kuratierte Bybit-Perp-Universum sollte eine **kleinere**
Verzerrung zeigen - Groessenordnungs-Anker, nicht Prior. REZENZ (C.18): die
urteilstragenden Fenster sind die A1/A3-Fenster (2024-07-01..2025-06-30,
2025-07-01..2026-06-30); aeltere Historie liefert nur die Hazard-Schaetzung.

**Rechenbudget.** ~10^5-10^6 Symbol-Wochen, gepoolte Logit-Schaetzung Sekunden;
1.000 Permutationen fuer die IPCW-vs-naiv-Differenz Minuten. **< 1 CPU-Stunde,
< 1 GB RAM, keine GPU** (DEC-57 erfuellt).

**Nicht-Duplikat-Nachweis.** Naechster Nachbar ist das WP-7-Adversarial-Fixture
(PRD 4.1, T1: signalfreies Panel, 30 % der Symbole nach Drawdown-Trigger
geloescht, der kontrollierte Schaetzer darf keine Momentum-Praemie zeigen). Das
ist ein **binaerer Funktionstest auf synthetischen Daten**. Mein Vorschlag misst
auf **echten Daten**, ob die Zensierung informativ ist, liefert eine **Groesse**
statt eines Haekchens und liefert das Korrekturverfahren (IPCW), das die
WP-7-Definition-of-Done unter "Bias-Richtung vorab" nur qualitativ behauptet. In
CROSSDOMAIN_PARK/PRD kommt keine Survival-Methode vor (die 20 IC-Vorschlaege
verteilen sich auf Klimatologie, Dendrochronologie, RMT, EVT, Mechanism Design,
Netzwerktopologie); ein Grep ueber `surviv|hazard|cox|kaplan|censor|truncat`
findet dort null Treffer. D.x enthaelt nichts Verwandtes.

**Entscheidungsrelevanz.** *PASS* (informative Zensierung nachgewiesen): A3
darf nur mit IPCW-gewichtetem IC als urteilstragender Groesse registriert werden,
und `SD_null(IC_t)` muss auf der gewichteten Statistik gemessen werden - sonst
misst WP-7 den Rauschboden eines Schaetzers, den A3 gar nicht verwendet.
*DROP* (keine informative Zensierung): die WP-7-Regel "bis zum letzten Bar
halten" ist nachweislich ausreichend, ein heute offenes, unbeziffertes Risiko
ist geschlossen, A3 laeuft mit dem naiven IC.
**Kostenloses Nebenprodukt:** dasselbe Modell liefert
`P(Delisting innerhalb einer Woche | unterstes Dezil)` - die bisher **gesetzte**
Zahl der Venue-Ereignis-Zeile (3.3.9c rechnet mit "1 %/Jahr Totalverlust-
wahrscheinlichkeit" als Annahme) wird dadurch **gemessen**.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* Panel mit Delisting-Wahrscheinlichkeit
monoton fallend im 12-Wochen-Momentum (informative Zensierung by design) - die
Hazard-Kovariate muss FDR-signifikant negativ, und die IPCW-korrigierte
IC-Differenz muss ausserhalb des Bootstrap-CI der naiven Schaetzung liegen.
*Negativ:* identisches Panel, Delistings rein zufaellig gezogen mit identischer
Randhaeufigkeit - `beta_hat` im CI von 0, IPCW-korrigierter und naiver IC
ununterscheidbar; zeigt der Schaetzer hier einen Effekt, ist er untauglich
(L-2b).

**Risiko-Etikett: Enabler.** Kein Alpha-Anspruch, keine Handelsaussage.

---

### X-SURV-2 - Die Funding-Historie als Multi-State-Survival-Objekt (Regime-Dauer + endogene Intervall-Selektion)

**Methode.** Ein Multi-State-Modell mit den Zustaenden
`{8h-Funding positiv, 8h-Funding negativ, 1h-Funding, delistet}`; geschaetzt
werden die Uebergangsintensitaeten nichtparametrisch (Aalen-Johansen) und
kovariatenabhaengig als konkurrierende Risiken (Fine/Gray 1999 JASA
94:496-509 fuer die Subdistribution; Putter/Fiocco/Geskus 2007 Stat. Med.
26:2389-2430 als kanonische Multi-State-Darstellung). Zwei Fragen in einem
Objekt:

- **(R) Dauerabhaengigkeit.** Steigt oder faellt die Hazard eines
  Funding-Vorzeichenwechsels mit dem **Alter** des Regimes? Das ist exakt die
  Frage, die Diebold/Rudebusch 1990 JPE 98:596-616 ("A Nonparametric
  Investigation of Duration Dependence in the American Business Cycle")
  nichtparametrisch fuer Konjunkturphasen gestellt haben; die Uebertragung auf
  Funding-Vorzeichenregime ist direkt.
- **(X) Endogene Zensierung durch den Intervallwechsel.** Bybit schaltet ein
  Symbol bei Anschlag der Cap-Grenze von 8h- auf 1h-Funding [sek, R1 0.2 via
  PRD 5.1(b)]. A1 schliesst 1h-Symbole aus ("laeuft nur auf der homogenen
  8h-Klasse"). **Dieser Ausschluss ist nicht exogen:** der Wechsel passiert
  gerade dann, wenn das Funding extrem ist - also genau bei den Symbolen, die
  in A1s aeusserstes Dezil gehoeren. Der Ausschluss entfernt systematisch die
  Traeger der behaupteten Praemie. Das ist informative Zensierung auf A1s
  eigenem Sortierschluessel, und das Multi-State-Modell beziffert sie
  (Hazard des 8h->1h-Uebergangs als Funktion des Funding-Dezils; anschliessend
  IPCW-Reweighting der verbleibenden 8h-Kohorte).

**Uebertragung auf den Bestand.** Strom: `GET /v5/market/funding/history`
(oeffentlich, keyfrei) - **derselbe Backfill, den PRD 7.1 fuer A1 ohnehin
plant** (~9.300 Calls, ~31 min bei 5 Req/s), plus `funding_n` und der
`status`-Verlauf aus WP-7s `panel_1d`. **Marginale Datenkosten: null.**
Aufloesung: Settlement (8h bzw. 1h). Symbole: alle Linear-Perps mit Historie in
den Fenstern. Horizont: entfaellt (Regime/Enabler). Klasse: **X mit R-Arm.**

**Struktureller Nulleffekt der Metrik.** Unter einer i.i.d.-Vorzeichenfolge sind
Laufzeiten **geometrisch** verteilt, die Hazard also **konstant** - der
Nulleffekt der Dauerabhaengigkeits-Frage ist exakt bekannt und braucht kein
Surrogat. Aber ein naiver "konstante Hazard"-Nullwert waere hier **falsch
kalibriert**, weil Bybits Zinsanker `I = 0,01 %/8h = 3,0 bp/Tag` (PRD 5.1(a),
[sek] R1 0.2) das Vorzeichen mechanisch nach oben verschiebt: negative Regime
sind a priori seltener und kuerzer. Der korrekte Nulleffekt ist deshalb ein
**Block-Permutations-Surrogat**, das Randhaeufigkeit je Symbol UND
Kalender-Blockstruktur erhaelt und nur die Reihenfolge zerstoert. Fuer den
Intervallwechsel-Arm: unter zufaelligem Wechsel ist `beta_hat` auf dem
Funding-Dezil null und die IPCW-gewichtete Praemie gleich der ungewichteten.

**Feasibility-Skizze.** Fenster W1/W2 aus PRD 5.1 (2024-07-01..2026-06-30,
730 Tage) ergeben je 8h-Symbol 2.190 Settlements; bei K ~ 170 durchgehenden
Symbolen ~372.000 Symbol-Settlements. Die Zahl der Regime ist
**UNGEMESSEN - dieses Paket misst sie**. Cluster-Einheit nach DEC-51 Punkt 3:
Regimewechsel treten symboluebergreifend an denselben Kalendertagen auf, also
**Kalenderwoche**, `N_c = 104` gepoolt. Konsequenz, ehrlich getrennt:

```
Markt-Ebene (Kovariate variiert nur ueber Wochen):
  detektierbar beta = sqrt(7,849/104) = 0,275  ->  HR 1,32 je SD
Querschnitts-Ebene (Kovariate variiert innerhalb der Woche ueber Symbole,
  Wochen-Fixed-Effect absorbiert den gemeinsamen Schock):
  effektives N ist die Zahl der Symbol-Regime, nicht 104; hier gut gepowert.
```

Der Intervallwechsel-Arm ist ein Querschnitts-Effekt und faellt in den gut
gepowerten Zweig; der Dauerabhaengigkeits-Arm ist gemischt und wird mit
LWYY-Cluster-Sandwich nach Kalenderwoche gerechnet (Lin/Wei/Yang/Ying 2000
JRSS-B 62:711-730). REZENZ: beide Fenster sind die A1-Fenster, per Konstruktion
konform. Zusatzgroesse: **RMST** (Royston/Parmar 2013) als interpretierbare
Regimedauer in Tagen, robust gegen nicht-proportionale Hazards.

**Rechenbudget.** Nach dem (A1 zugerechneten) Download: Aalen-Johansen und
Fine-Gray auf ~4*10^5 Zeilen - **Minuten CPU, < 2 GB RAM, keine GPU.**

**Nicht-Duplikat-Nachweis.** Naechster Nachbar ist A1s Feasibility-Kill (4):
"die in WP-7 gemessene Autokorrelation des Funding-Sortierschluessels ueber eine
Woche liegt unter 0,30" - **ein linearer Skalar bei einem festen Lag**. Meine
Groesse ist die **Verteilung der Regimelaufzeiten** plus die Dauerabhaengigkeit
der Hazard; eine Ein-Lag-Autokorrelation kann das prinzipiell nicht enthalten:
ein Prozess mit rho = 0,45 kann aus vielen kurzen oder wenigen langen Regimen
bestehen, und nur die zweite Variante rechtfertigt eine Wochen-Halteperiode.
Zweiter Nachbar: PRD 5.1(b) behandelt die 8h/1h-Heterogenitaet als
**Normierungsproblem** (`funding_n`); dass derselbe Mechanismus ein
**Selektionsproblem** auf dem Sortierschluessel ist, steht nirgends im Programm.
D.17 (DSM-03) ist eine Prognose-Hypothese auf dem Premium-Index-Delta-Strom und
beruehrt weder Dauer noch Selektion. CROSSDOMAIN: kein Eintrag zu Funding-Dauern.

**Entscheidungsrelevanz.** *PASS Dauerabhaengigkeit:* A1s Halteperiode ist nicht
mehr frei waehlbar, sie haengt an der gemessenen Regimedauer, und die
Cluster-Zeile (3.3.3) bekommt ein gemessenes `N_eff` statt eines Skalars.
*PASS Intervall-Selektion:* A1 ist ohne IPCW-Gewichtung **nicht registrierbar**,
weil der Ausschluss die Traeger der Praemie entfernt - das aendert A1s
Registrierungstext, nicht seine Schwelle. *DROP beides:* A1s Bauform ist
unbedenklich und der Punkt dauerhaft abgeraeumt.

**Fixture-Paar.** *Positiv:* synthetische Funding-Serie mit Weibull-Laufzeiten
(Shape 1,5, steigende Hazard) plus ein Intervallwechsel, dessen
Wahrscheinlichkeit monoton im Funding-Dezil steigt - beide Effekte muessen
detektiert werden. *Negativ:* i.i.d.-Vorzeichen mit derselben Randhaeufigkeit
und zufaelligem Intervallwechsel - konstante Hazard, `beta_hat` im CI von 0.

**Risiko-Etikett: Enabler** (der R-Arm ist "Blick wert", der Selektions-Arm ist
ein reiner Enabler und der wertvollere der beiden).

---

### X-SURV-3 - Time-to-Fill als konkurrierendes Risiko: der richtige Schaetzer fuer die WP-10(B)-Fill-Kurve

**Methode.** Die Lebensdauer einer passiven Order am Touch ist ein klassisches
Competing-Risks-Problem: die Order verlaesst die Risikomenge durch **Fill**,
durch **adverse Bewegung** (der Touch wird gegen einen geraeumt) oder durch
**administrative Zensierung** (Fensterende, Datenluecke). Die oekonomisch
relevante Groesse ist die **kumulative Inzidenzfunktion** des Fills in Gegenwart
des Konkurrenzereignisses - geschaetzt mit Aalen-Johansen, kovariatenabhaengig
mit Fine/Gray 1999. Dass Fill und Cancel/Adverse ein Competing-Risks-Paar sind,
ist in der Mikrostruktur-Literatur etabliert (Lo/MacKinlay/Zhang 2002 J. Fin.
Econ. 65:31-71, "Econometric models of limit-order executions"; Multiple-Spell-
Duration-Fassung bei Cebiroglu et al. 2019 Ann. Oper. Res. [sek, Suchtreffer]).

**Uebertragung auf den Bestand.** Genau derselbe Ein-Pass-Replay, den WP-10(B)
plant (86 min je Fenster, WP-2/WP-4-Maschinerie, `bybit/orderbook` L2 BTC/ETH
plus `publicTrade`). Aufloesung: Tick/Sekunde. Symbole: BTC/ETH. Horizont:
Sekunden bis Minuten - **zulaessig, weil es eine reine Kosten- und
Strukturmessung ist** (Randbedingung 3), nie eine Kante. Klasse: **X**. Kein
zusaetzlicher Download, kein zusaetzlicher Replay-Pass.

**Warum das kein kosmetischer Schaetzerwechsel ist.** Die L2-Abdeckung ist
**74 % (BTC, 961 Tage) und 41 % (ETH, 530 Tage)** (F.1). Ein erheblicher Teil
der Schatten-Order-Spells endet damit nicht durch Fill oder adverse Bewegung,
sondern durch eine **Datenluecke**. Ein naives Verhaeltnis "Fills / platzierte
Orders bis tau" behandelt jeden luecken-abgeschnittenen Spell als Nicht-Fill und
**unterschaetzt** `p_fill` systematisch - Richtung: gegen die eigenen
Kandidaten, denn Maker-Rehedging ist laut R1 0.4 "Existenzbedingung, nicht
Optimierung". **Genau deshalb muss der Wechsel VOR dem Lauf registriert werden**
(C.3, Anti-Gaming): eine Schaetzeraenderung, die die eigene Seite beguenstigt,
ist nach dem Lauf nicht mehr zulaessig, vorher schon - und beide Zahlen (naiv
und korrigiert) werden berichtet.

**Struktureller Nulleffekt der Metrik.** Exakt herleitbar, kein Import. Bei
konstanten Hazards `l_f` (Fill) und `l_a` (adverse Bewegung):

```
CIF_fill(t)       = l_f/(l_f+l_a) * (1 - exp(-(l_f+l_a) t))
naives 1-KM(t)    = 1 - exp(-l_f t)            [ignoriert das Konkurrenzrisiko]
bei l_f = l_a und t = 1/l_f:  CIF = 0,4323 gegen 1-KM = 0,6321  -> Faktor 1,46
bei l_f = l_a und t -> unendlich: CIF = 0,50   gegen 1-KM = 1,00 -> Faktor 2,00
```

Das ist der strukturelle Nulleffekt in beide Richtungen: **1-KM ueberschaetzt**
den Fill (bis Faktor 2), das **naive Verhaeltnis unterschaetzt** ihn bei
Zensierung. Nur die CIF ist unverzerrt. Genau diese Zahl fehlt der aktuellen
WP-10(B)-Spezifikation.

**Feasibility-Skizze.** Cluster-Einheit Kalendertag, ~180 Cluster je Fenster
(PRD 4.3, "gut gepowert"); die Zahl der Spells geht in die Millionen, bindend
ist allein `N_cluster = 180`. Detektierbare Differenz naiv vs. CIF:
`2,8016 * SD_tag / sqrt(180) = 0,2088 * SD_tag`, mit `SD_tag` der
Tages-Fill-Rate **UNGEMESSEN - WP-10(B)**. Erwartete Effektgroesse: **26 %
(BTC) / 59 % (ETH)** der Kalendertage sind gar nicht abgedeckt; der Anteil
gap-abgeschnittener Spells innerhalb abgedeckter Tage ist **UNGEMESSEN**.
REZENZ: die von WP-10(B) gewaehlten Halbjahre werden uebernommen, keine eigene
Fensterwahl.

**Rechenbudget.** Kein eigener Replay-Pass; Aalen-Johansen auf den
Spell-Tabellen des bestehenden Passes: **Sekunden bis Minuten CPU**, keine GPU.

**Nicht-Duplikat-Nachweis.** WP-10(B) ist der naechste Nachbar - der Vorschlag
ist ausdruecklich **kein neues Paket, sondern eine Schaetzer-Spezifikation fuer
ein bereits geplantes**. WP-10(B) formuliert die Anforderung ("Adversarial: Buch,
in dem der Touch nur bei adverser Bewegung geraeumt wird ... die Messung muss den
zweiten Fall trennen"), benennt aber **keinen Schaetzer, der das leistet**; ein
Verhaeltnis-Schaetzer kann es prinzipiell nicht, weil er die Austrittsgruende
nicht unterscheidet. D.1 (Spread-Capture tot) ist nicht betroffen: hier wird
keine Spread-Ertragsquelle behauptet, sondern eine Kostenkonstante gemessen;
WP-4 hat die Spread-BREITE gemessen, nie eine Fill-Wahrscheinlichkeit.

**Entscheidungsrelevanz.** *PASS* (materieller Unterschied): die
`p_fill(tau)`-Kurve wandert als **CIF** nach `tradability3`; jedes spaetere
Maker-Szenario rechnet mit einer unverzerrten Zahl, und `adv_sel` wird **bedingt
auf die bereits gewartete Zeit** ausgewiesen statt als Fenster-Skalar. *DROP:*
das naive Verhaeltnis ist gerechtfertigt - dokumentiert statt unterstellt.

**Fixture-Paar.** *Positiv:* synthetisches Buch mit `l_a = l_f` und 30 %
kuenstlichen Datenluecken - die CIF muss die eingebaute wahre Fill-Rate treffen,
das naive Verhaeltnis muss sie um den vorab berechneten Betrag verfehlen.
*Negativ:* Buch ohne adverse Bewegungen und ohne Luecken - CIF und naives
Verhaeltnis muessen bis auf numerisches Rauschen identisch sein (Anschluss an
B.15, 3,8e-9).

**Risiko-Etikett: Enabler.**

---

### X-SURV-4 - Selbstkontrollierte Ereignisdesigns und die Messung der Referenzwahl-Verzerrung fuer Klasse E

**Methode.** Die Epidemiologie hat fuer transiente, exogen getaktete Expositionen
zwei selbstkontrollierte Designs entwickelt, die alle zeitinvarianten
Confounder **per Konstruktion** eliminieren, weil jede Einheit ihre eigene
Kontrolle ist: das **Case-Crossover-Design** (Maclure 1991, Am. J. Epidemiol.
133:144-153) und die **Self-Controlled Case Series** (Farrington 1995,
Biometrics 51:228-235). Der entscheidende, hier uebertragbare Befund ist
allerdings nicht das Design selbst, sondern seine Pathologie: **die Wahl der
Referenzzeitpunkte bestimmt den Nulleffekt**, und naive Referenzschemata
erzeugen auf reinem Rauschen einen **von null verschiedenen** Erwartungswert -
die "Overlap Bias" (Janes/Sheppard/Lumley 2005, Stat. Med. 24:285-300; dazu
Janes/Sheppard/Lumley 2005b, Epidemiology 16:717-726, zu Referenzwahl-
Strategien). Das ist exakt die Fehlerklasse, die in 2.0 das Dressing-Artefakt
war (B.9, DEC-31): eine Metrik, deren Nulleffekt nicht null ist, mit einer
Schwelle unterhalb dieses Nulleffekts.

**Uebertragung auf den Bestand.** PRD 3.2 legt fuer Klasse E fest: "Nulleffekt
ist die Placebo-Verteilung auf Zufallsterminen mit identischer Kalender-
verteilung." Das ist ein Referenzwahl-Schema - und **das Programm setzt seinen
Erwartungswert stillschweigend auf null, ohne ihn zu messen.** Der Vorschlag
lautet: (a) den Erwartungswert und die Streuung dieses Schemas auf reinem
Rauschen mit identischer Kalender-, Vol- und Wochentagsstruktur **messen**;
(b) ihn gegen zwei alternative, in der Literatur als bias-frei ausgewiesene
Schemata halten (zeitgeschichtete Referenzwahl, symmetrisch-bidirektional);
(c) die Kalender-Cluster-Struktur (BTC/ETH teilen Verfallstage, L-6) im
selbstkontrollierten Rahmen behandeln, wo sie durch die Konditionierung
innerhalb des Symbols entfaellt statt durch eine Korrektur repariert werden zu
muessen. Strom: WP-0-Bar-Cache (10.054 Cache-Tage, 14,4 Mio Minutenbars) plus
der Verfallskalender aus V-5. Aufloesung: 30 min bis 1 Tag. Symbole: die 5
Majors. Horizont: entfaellt (Enabler/Nulleffekt-Kalibrierung). Klasse: **X**.

**Struktureller Nulleffekt der Metrik.** Das IST der Gegenstand: gemessen wird
der Nulleffekt eines Nulleffekt-Konstruktionsverfahrens. Bedingter Nulleffekt
zweiter Ordnung: die konditionale Likelihood des Case-Crossover (bedingte
Logit) hat unter der Null einen exakt bekannten Score-Test (chi^2), gegen den
die empirische Placebo-Verteilung gehalten wird.

**Feasibility-Skizze.** Cluster-Einheit: das **Ereignis** (alle Symbole desselben
Verfalls = ein Cluster, DEC-51 Punkt 3). PRD 5.2 beziffert fuer A2:
`N_eff = 57,8` (woechentliche Variante) bzw. `13,3` (monatlich),
`SE(Delta) = 5,11` bzw. `11,24 bps`. Das sind **die Zahlen, gegen die der
gemessene Referenz-Bias zu halten ist**: uebersteigt der gemessene Bias-
Erwartungswert einen materiellen Anteil von 5,11 bps, ist der A2-Nulleffekt
falsch kalibriert und die Schwelle `12,7 bps` steht auf einem verschobenen
Nullpunkt. Power: die Frage ist eine reine Simulations-/Resampling-Frage auf
6 Jahren Bar-Cache - die Praezision der Bias-Schaetzung skaliert mit der Zahl
der Ziehungen (10.000 Placebo-Saetze), nicht mit `N_cluster`; sie ist deshalb
**nicht power-limitiert**. Was power-limitiert bleibt, ist A2 selbst - dieser
Vorschlag repariert das nicht und behauptet es auch nicht.
**Ehrliche Begrenzung:** der reine Effizienzgewinn eines selbstkontrollierten
Designs ist bei **rohen Mittelwert-Renditen gering** (die Autokorrelation
gematchter Renditefenster ist nahe null, es gibt also wenig
Matching-Varianzreduktion); er ist substanziell nur fuer **vol-normalisierte
Renditen und fuer Zaehl-/Raten-Groessen** (z. B. Tail-Minuten-Zahl um den
Verfall). Das schmaelert Teil (c) des Vorschlags; Teil (a)+(b) - die Messung
des Referenz-Bias - ist davon unberuehrt und traegt den Vorschlag.

**Rechenbudget.** 10.000 Placebo-Saetze auf 6 Jahren Minuten-/Tagesdaten:
**Minuten bis wenige CPU-Stunden**, < 4 GB RAM. **Keine GPU.**

**Nicht-Duplikat-Nachweis.** Naechster Nachbar ist PRD 3.2/5.2 selbst
(Placebo-Verteilung P1/P2 fuer A2). Dort werden Placebos **verwendet**; hier
wird ihr eigener Nulleffekt **gemessen** - genau der Schritt, dessen Fehlen
GL-022/DEC-31 verursacht hat und den L-2 seither zur Pflicht macht ("der
Nulleffekt wird zusaetzlich am Null-Fixture GEMESSEN"). Im CROSSDOMAIN-Register
existiert kein Eintrag zu Ereignisstudien-Design; die naechsten Nachbarn dort
(IC-DEND-1/H-10 Pointer-Days) sind Detektions-, keine Design-Fragen.
D.x enthaelt nichts Verwandtes.

**Entscheidungsrelevanz.** *PASS* (Referenzschema erzeugt materiellen Bias):
die Klasse-E-Nulleffekt-Zeile von A2 und jeder kuenftigen Ereignis-Hypothese
wird auf ein bias-freies Schema umgestellt, **bevor** eine Schwelle gesetzt
wird - ein DEC-31-Wiedergaenger wird verhindert. *DROP* (kein materieller
Bias): die bestehende Placebo-Konstruktion ist belegt statt unterstellt, und
die Klasse E hat ihre Nulleffekt-Zeile mit Messung statt Behauptung.
**Wichtig:** dieser Vorschlag belebt A2 nicht wieder - A2 bleibt an V-5
(Effektgroessen-Beleg) gebunden und ist ohne den ein GL-012-Fall.

**Fixture-Paar.** *Positiv:* reine Rauschreihe mit starkem Wochentags- und
Monatsende-Muster plus ein unidirektionales Referenzschema - der gemessene
Bias muss deutlich von null abweichen (der bekannte Overlap-Bias-Fall).
*Negativ:* dieselbe Reihe mit zeitgeschichteter, symmetrischer Referenzwahl -
der gemessene Bias muss im Bootstrap-CI von null liegen.

**Risiko-Etikett: Enabler** (Teil a+b), **spekulativ** (Teil c, Effizienzgewinn
nur bedingt).

---

## 3. RANGLISTE

| Rang | ID | Warum an dieser Stelle |
|---|---|---|
| 1 | **X-SURV-1** | Haengt an WP-7, dem Rang-1-Paket des gesamten Feldes. WP-7 baut ein links-trunkiertes, rechts-zensiertes Universum und prueft die Verzerrung heute nur **binaer an einem synthetischen Fixture**. Der Vorschlag ersetzt ein Haekchen durch eine Zahl, kostet < 1 CPU-Stunde und null zusaetzliche Daten - und liefert die Venue-Ereignis-Wahrscheinlichkeit (3.3.9c) als Nebenprodukt gratis mit. |
| 2 | **X-SURV-2** | Betrifft A1, den Rang-2-Kandidaten, an zwei Stellen: die Cluster-/Halteperioden-Zeile und eine **bisher unbemerkte endogene Selektion** auf A1s eigenem Sortierschluessel (8h->1h-Wechsel). Reitet vollstaendig auf dem ohnehin geplanten A1-Backfill. Nachrangig zu 1, weil A1 selbst nach WP-7 kommt. |
| 3 | **X-SURV-3** | Reine Schaetzer-Spezifikation fuer ein bereits geplantes Paket, mit exakt herleitbarem Nulleffekt (Faktor bis 2,0) und einer bezifferten Zensierungsquelle (L2-Abdeckung 74 %/41 %). Nachrangig, weil sein Ergebnis nur ins Kostenmodell wandert - und Kosten sind nach C.2 Etikett, nie Gate. |
| 4 | **X-SURV-4** | Billigster und methodisch sauberster der vier, aber sein Hauptnutzniesser (A2) ist selbst durch V-5 blockiert, und der Design-Effizienzarm traegt nur bedingt. Wert liegt in der Nulleffekt-Messung fuer **jede kuenftige** Klasse-E-Hypothese. |

---

## 4. NICHT VORGESCHLAGEN - UND WARUM

### 4.1 SIR/SEIR-Kontagion fuer Liquidationsausbreitung ueber Symbole oder Boersen

**Vier unabhaengige Gruende, jeder allein hinreichend.**

**(a) `R0` ist ein Branching-Ratio - D.2.** `R0 = beta*S0/gamma` ist
definitionsgemaess die erwartete Zahl Sekundaerereignisse je Primaerereignis,
also dieselbe Groesse wie der Hawkes-Verzweigungsgrad. Ein Alarm bei "R0 > 1"
ist die 0,85-Schwelle von C-14 unter anderem Namen. Ich habe keinen Weg
gefunden, einen SIR-Vorschlag zu formulieren, der **nicht** an einer
Branching-Groesse haengt - ausser ueber den Depletion-Term, und der stirbt an
(c).

**(b) Die Entsperrbedingung des Programms ist unerreichbar.** C-26 steht mit
"kein eigener Pilot; geht in C-39 auf" im PARK-Register; C-39 haengt an
C-36-Recording von `insurance`/`adlAlert`; C-36 liefert NO_DATA (GL-004) und
wird gemaess DEC-43 **nicht repariert** (Kompendium E.13). Damit ist der
formal-korrekte Status "SUSPECT" praktisch ein Dauerzustand ohne Ausgang.

**(c) Struktureller A-priori-DROP nach C.12/GL-012 fuer jede
Liquidations-Kaskaden-Hypothese auf dem heute planbaren Design.** Rechnung,
vor jedem Datenlauf: `bybit/allLiquidation` hat 43 Tage (BTC/ETH, Stand
2026-08-10, F.1), kalendarisch gewachsen auf ~67 Tage (Stand 2026-09-03, nicht
unabhaengig verifiziert). H-21 fordert zwei feste 90-Tage-Fenster, BTC+ETH.
Cluster-Einheit nach DEC-51 Punkt 3 ist der **Kalendertag** (BTC und ETH
kaskadieren an denselben Tagen, L-6) bzw. die **Kaskaden-Episode**. Zahl der
Episoden je 90-Tage-Fenster nach den programmeigenen Stress-Definitionen:

```
STRESS_ABS (99-Perzentil der Gesamthistorie, DEC-56): 0,01 * 90 = 0,9 Tage
STRESS_REL (97,5-Perzentil, 24 Monate, DEC-55):       0,025 * 90 = 2,25 Tage
selbst eine lockere "Top-5-%-Liq-Notional"-Definition: 0,05 * 90 = 4,5 Tage
(PRD 4.3 nennt fuer STRESS_ABS ueber BEIDE urteilstragenden Fenster
 unabhaengig davon die Groessenordnung 6-10 Episoden)
Schoenfeld, standardisierte Kovariate, einseitig z = 2,4865 (z^2 = 6,183):
  d = 4  -> detektierbar beta = sqrt(6,183/4)  = 1,243 -> HR 3,47 je SD
  d = 9  -> detektierbar beta = sqrt(6,183/9)  = 0,829 -> HR 2,29 je SD
```

Unter der harten Ein-Fenster-Regel (C.10) muss **jedes** Fenster fuer sich
bestehen, also gilt `d = 4-5`. **Kein Hazard-Verhaeltnis unter etwa 3,5 je SD
ist detektierbar.** Mehr Symbole helfen nicht, weil sie dieselben Kalendertage
teilen (L-6). Das ist ein struktureller A-priori-DROP, nicht ein "warten bis
2026-12-27": auch am 2026-12-27 aendert sich an dieser Arithmetik nichts.

**(d) Kein Zahler, keine Ertragsquelle.** Selbst ein PASS waere ein
Detektionsbefund. Das Programm hat dafuer bereits ein Etikett: C-39s eigene
Entsperrzeile sagt woertlich "Recall-Gate >= 90 %, aber **Detektion != Profit**".

**Wiedereintritts-Bedingung, falls die Frage je wieder gestellt wird:** eine
Depletion-These (nicht Branching) - "die Hazard weiterer Liquidationen faellt
mit dem kumulativ liquidierten Notional relativ zum verfuegbaren OI, ueber eine
Omori-artige reine Zeitabhaengigkeit hinaus" - formuliert als Cox-Modell mit
zeitabhaengiger Kovariate, registrierbar erst wenn `>= 30` disjunkte
Kaskaden-Episoden mit lueckenlosem `allLiquidation` UND OI-Zeitreihe vorliegen
(bei einer Episodenrate von 2-5 % der Tage heisst das **>= 3-4 Jahre**
Aufzeichnung). Nicht vor 2029/2030. Als Vorschlag heute unzulaessig.

### 4.2 Cox-Modell fuer die Ueberlebensdauer einer Quote am Touch (als eigenstaendige Hypothese)

Die Frage ist real und interessant, aber sie ist als eigenstaendiger Kandidat
**doppelt tot**: die Ertragsquelle waere "den Spread einfangen" (D.1: auf
Bybit-Perp-Majors a priori tot, Spread exakt ein Tick, B.2), und der Horizont
liegt bei Sekunden (Randbedingung 3: gerichtete Vorschlaege unter ~1 Tag sind
nur als Kosten-/Strukturmessung zulaessig). Genau als solche Messung ist sie in
**X-SURV-3** enthalten - und dort nicht als Hypothese, sondern als
Schaetzer-Spezifikation eines bestehenden Pakets.

### 4.3 Kaplan-Meier-Vergleich Stress gegen Ruhe fuer die Dauer einer Stress-Episode nach DEC-56

Als eigenstaendiger Vorschlag verworfen, weil er an seiner eigenen Power
stirbt: `STRESS_ABS` liefert nach PRD 4.3 ueber **beide** urteilstragenden
Fenster zusammen 6-10 Episoden; `STRESS_REL` erzeugt per Konstruktion 2,5 %
Stress-Tage in jedem Fenster (DEC-56 (1)) und ist ausdruecklich
**Abdeckungs-Nachweis, nie Filter oder Gate**. Mit `d = 6-10` ist nach
Schoenfeld nur `beta = sqrt(7,849/8) = 0,99`, also `HR ~ 2,7` je SD
detektierbar. Ein Log-Rank-Vergleich auf dieser Basis waere eine Messung mit
weitgehend offenem CI - genau der Zustand, den WP-10(A) fuer die
Kohaerenzfrage bereits **bewusst deskriptiv** stehen laesst statt ihn in ein
Gate zu zwingen. Eine zweite Groesse in denselben offenen CI zu legen, aendert
keine Entscheidung.

### 4.4 Andersen-Gill-Modelle fuer Liquidations-Folgen (rekurrente Ereignisse)

Verworfen aus demselben Grund wie 4.1(c): die rekurrente Struktur wuerde auf
`d = 4-5` Kaskaden-Clustern je Fenster geschaetzt. Zusaetzlich waere die
interessante Groesse - die Intensitaets-Erhoehung nach einem Ereignis - wieder
die Verzweigungsgroesse aus D.2. Der methodisch saubere Teil von AG (die
cluster-robuste LWYY-Sandwich-Varianz) ist **in X-SURV-2 verwendet**, wo er
104 Wochen-Cluster statt 4 Episoden-Cluster hat.

### 4.5 Weitere geprueft und verworfen

- **Frailty-/Random-Effects-Cox ueber Symbole** - loest kein offenes Problem,
  das der LWYY-Sandwich nicht billiger loest, und fuegt eine
  Verteilungsannahme (Gamma-Frailty) hinzu, deren Nulleffekt neu kalibriert
  werden muesste. Kein Netto-Gewinn.
- **Beschleunigte Lebensdauermodelle (AFT) statt Cox** - waere nur dann
  vorzuziehen, wenn Proportionalitaet verletzt ist; dafuer gibt es hier keine
  Evidenz, und die Frage wird in X-SURV-2 durch RMST ohnehin
  proportionalitaets-robust beantwortet.
- **Cure-Modelle (Mischung aus "wird nie delistet" und "wird delistet")** -
  attraktiv fuer X-SURV-1, aber die Identifikation der Cure-Fraktion braucht
  eine lange Nachbeobachtung ohne Ereignisse; bei 5,5 Jahren Historie und einem
  jungen, wachsenden Perp-Universum ist sie schwach identifiziert. Als
  Sensitivitaet in X-SURV-1 berichtbar, nicht als eigener Vorschlag.
- **SEIR mit Latenzkompartiment** - erbt alle vier Probleme von 4.1 und fuegt
  einen weiteren unbeobachtbaren Zustand hinzu.
- **Epidemische Netzwerkmodelle ueber Boersen** - liegt zu nah an
  IC-NET-1/2/3 (CROSSDOMAIN_PARK (b), "Overlay-ueber-Nichts", entsperrt erst
  bei existierender positiver Basis-Strategie) und an H-12/H-14 (beide DROP
  bzw. methodisch invalide). Duplikat-Risiko zu hoch.

---

## 5. BELEGSTATUS

**Primaerliteratur, Zitat vollstaendig, Volltext nicht in jedem Fall geprueft
(Bibliografische Angaben ueber Suchmaschinen-Treffer und Verlagsseiten
verifiziert; wo nur das gilt, steht [bibl]):**

| Nr | Quelle | Verwendet in |
|---|---|---|
| 1 | Cox, D. R. (1972). Regression models and life-tables. *JRSS-B* 34(2):187-220. [bibl] | X-SURV-1, 4.1(c) |
| 2 | Kaplan, E. L., Meier, P. (1958). Nonparametric estimation from incomplete observations. *JASA* 53(282):457-481. [bibl] | X-SURV-3, 4.3 |
| 3 | Andersen, P. K., Gill, R. D. (1982). Cox's regression model for counting processes: a large sample study. *Ann. Statist.* 10(4):1100-1120. | X-SURV-1, 4.4 |
| 4 | Fine, J. P., Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk. *JASA* 94(446):496-509. | X-SURV-2, X-SURV-3 |
| 5 | Lin, D. Y., Wei, L. J., Yang, I., Ying, Z. (2000). Semiparametric regression for the mean and rate functions of recurrent events. *JRSS-B* 62:711-730. | X-SURV-2, 4.4 |
| 6 | Robins, J. M., Finkelstein, D. M. (2000). Correcting for noncompliance and dependent censoring ... IPCW log-rank tests. *Biometrics* 56(3):779-788. | X-SURV-1, X-SURV-2 |
| 7 | Schoenfeld, D. A. (1983). Sample-size formula for the proportional-hazards regression model. *Biometrics* 39:499-503. | alle Power-Zeilen |
| 8 | Klein, J. P., Moeschberger, M. L. (2003). *Survival Analysis: Techniques for Censored and Truncated Data*, 2. Aufl., Springer. [bibl] | X-SURV-1 (Links-Trunkierung) |
| 9 | Putter, H., Fiocco, M., Geskus, R. B. (2007). Tutorial in biostatistics: competing risks and multi-state models. *Stat. Med.* 26:2389-2430. [bibl] | X-SURV-2 |
| 10 | Diebold, F. X., Rudebusch, G. D. (1990). A nonparametric investigation of duration dependence in the American business cycle. *JPE* 98(3):596-616. | X-SURV-2 (R-Arm) |
| 11 | Shumway, T. (2001). Forecasting bankruptcy more accurately: a simple hazard model. *J. Business* 74(1):101-124. | X-SURV-1 (Finanz-Uebertragung) |
| 12 | Maclure, M. (1991). The case-crossover design. *Am. J. Epidemiol.* 133(2):144-153. [bibl] | X-SURV-4 |
| 13 | Farrington, C. P. (1995). Relative incidence estimation from case series for vaccine safety evaluation. *Biometrics* 51:228-235. | X-SURV-4 |
| 14 | Janes, H., Sheppard, L., Lumley, T. (2005). Overlap bias in the case-crossover design ... *Stat. Med.* 24:285-300; dazu dieselben (2005b), *Epidemiology* 16:717-726. | X-SURV-4 (Nulleffekt) |
| 15 | Royston, P., Parmar, M. K. B. (2013). Restricted mean survival time. *BMC Med. Res. Methodol.* 13:152. [bibl] | X-SURV-2 |
| 16 | Lo, A. W., MacKinlay, A. C., Zhang, J. (2002). Econometric models of limit-order executions. *J. Fin. Econ.* 65:31-71. [bibl] | X-SURV-3 |
| 17 | Kermack, W. O., McKendrick, A. G. (1927). A contribution to the mathematical theory of epidemics. *Proc. R. Soc. A* 115:700-721. [bibl] | Abschnitt 1 (SIR-Herkunft) |

**Sekundaerbelege `[sek]`, Host egress-gesperrt:**

- Ammann, M., Burdorf, T., Liebi, L., Stoeckl, S. (2022). *Survivorship and
  Delisting Bias in Cryptocurrency Markets*. SSRN 4287573, Working Paper
  Univ. St. Gallen / Univ. Liechtenstein. Zahlen (3.904 Coins 2014-2021;
  annualisierte Verzerrung 0,93 % VW / 62,19 % EW; Size-Praemie um 50 %
  ueberschaetzt; 1-Wochen-Momentum verschwindet nach Korrektur) stammen aus
  einer Suchmaschinen-Zusammenfassung des Abstracts. `papers.ssrn.com`,
  `www.alexandria.unisg.ch` und `www.sebastianstoeckl.com` sind vom
  Egress-Proxy geblockt - **Volltext nicht primaer verifiziert**.
- Aequivalenz Hawkes-Verzweigungsgrad / epidemisches `R0`: nur ueber
  Suchtreffer belegt (u. a. Rizoiu et al., "SIR-Hawkes"; PLOS-One-Arbeiten zu
  diskret-zeitlichen selbstanregenden COVID-Modellen). **Fuer die Argumentation
  in 1.4(3) nicht bindend** - dort genuegt die Definition selbst:
  `R0 = erwartete Sekundaerfaelle je Primaerfall` ist per Definition ein
  Verzweigungsgrad, unabhaengig von jeder Sekundaerquelle.
- Cebiroglu et al. (2019), Multiple-Spell-Duration-Modell fuer Limit-Order-
  Platzierung, *Ann. Oper. Res.* - nur ueber Suchtreffer, **kein
  urteilstragender Beleg**, dient nur der Einordnung.
- Bybit-Funding-Mechanik (`I = 0,01 %/8h`, Cap-Umschaltung 8h->1h): [sek] ueber
  R1 0.2 via PRD 5.1(a)/(b); Primaerseiten `bybit.com` sind gesperrt (PRD 4).

**UNGEMESSEN / UNBELEGT, in dieser Reihenfolge zu klaeren:**

1. Zahl der Bybit-Linear-Perp-Delistings und Zahl distinkter
   Delisting-**Chargen** in 2020-2026 - **UNGEMESSEN**, bindend fuer
   X-SURV-1s Power; erste Messung des Pakets.
2. Verteilung der Funding-Vorzeichen-Regimelaufzeiten und Zahl der
   8h->1h-Uebergaenge - **UNGEMESSEN**, bindend fuer X-SURV-2.
3. Anteil luecken-abgeschnittener Schatten-Order-Spells innerhalb abgedeckter
   L2-Tage - **UNGEMESSEN**, bindend fuer X-SURV-3s Effektgroesse.
4. Erwartungswert des Klasse-E-Placebo-Schemas auf reinem Rauschen -
   **UNGEMESSEN**, Gegenstand von X-SURV-4.
5. Tatsaechliche `allLiquidation`-Tiefe zum 2026-09-03 - im Sandbox-Baum kein
   Harvest-Manifest vorhanden (`/home/user/scinance/data` enthaelt nur
   `trades_journal.csv`); die ~67 Tage sind aus F.1 kalendarisch
   fortgeschrieben, **nicht unabhaengig verifiziert**.

---

*Ende S1_SURVIVAL_EPIDEMIOLOGIE.md. Read-only im Repo: keine Datei ausserhalb
dieses Scratchpads angelegt oder geaendert.*
