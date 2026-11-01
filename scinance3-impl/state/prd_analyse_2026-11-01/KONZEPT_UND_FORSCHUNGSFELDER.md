# Grundsatzanalyse Scinance 3.0: konzeptionelle und strukturelle Luecken, unentdeckte Forschungsfelder

> Auftrag: der Konzept-Auftrag des Orchestrators (`prd_review/BRIEF_konzept.md`); Regeln: `prd_review/REGELN_UND_LESELISTE.md` (nur lesen, keine
> Datenrechnung, keine Siegeldateien, kein Harvest-Client). Gelesen: die vollstaendige Leseliste (PRD 1-11, Verfassung,
> Kompendium A-F, DEC-51..103 mit Nachtraegen, GL-032..036, Bilanz 2026-10-18 mit Vermerken, STAND bis 2026-10-31,
> UEBERGABEN 10-09/10-12 mit Nachtraegen 1-13, A2-Akte vollstaendig, H32/H33/HFRV-Vorlagen, 2.0-Berichte, Dateninventar
> 2026-11-01, DATA_ACCESS, Code-Modulliste, Exkurs-Synthese Abschnitt 3). Analytische Rechnungen: Skript
> `state/prd_analyse_2026-11-01/scripts/konzept_calc.py` (nur Formeln und Nuisance-Zahlen aus der Akte; Ausgabe im Anhang zitiert).
> Konventionen: **Fakt** = belegt (Fundstelle), **Urteil** = meine Bewertung, **Vorschlag** = Richtung angegeben
> (Strenge / Testbarkeit / neutral). UNBELEGT und Vermutung sind als solche markiert. Rollen statt Modellnamen.
> Stand 2026-11-01.

---

## 0. Befund in Kuerze

1. **Fakt.** Scinance 3.0 hat seit dem PRD (2026-09-02) sechs Gate-Eintraege erzeugt (GL-032..036 plus H-32-Pilot),
   davon null Verdikte ueber einen Markteffekt: alle sind "GL-012 vor dem Lauf/vor der Registrierung" oder "GL-012
   (Pilot)". Keine reale Signal-Rendite-Statistik der Klassen P, W, E wurde je auf einem urteilstragenden Fenster
   berechnet (STAND 2026-10-18 Abschnitt 3; DEC-101 E12; GL-036).
2. **Urteil.** Die naturwissenschaftliche Idee ist als **Pruefdisziplin** weitgehend realisiert (Vorregistrierung,
   Blindheit, gemessener Rauschboden, Nullmodelle je Hypothese, Positivkontrolle in Produktionskonfiguration, Power mit
   der SE des registrierten Tests). Als **Messinstitution** ist sie nicht realisiert: das Programm kennt nur die
   Ausgaben PASS / DROP / GL-012, nie "Effekt = x mit Intervall [a, b]". Es ist in Buchhaltung umgeschlagen, wo die
   Buchhaltung (Siegel, Verbrauch, Gabelungs-Etiketten) die Messung ersetzt statt sie zu schuetzen.
3. **Urteil.** Der bindende Engpass ist nicht Daten, nicht Code, nicht Power im engeren Sinn, sondern eine
   Entscheidungsregel: Power wird gegen einen **Literatur-Punktprior** gerechnet; fehlt er (theta, fm8-IC, V-5b),
   endet die Kette bei UNBELEGT. Eine Institution, die nur bestaetigen darf, was die Literatur schon gemessen hat, kann
   auf einem jungen Markt (Bybit-Perps 2024-2026) nichts entdecken.
4. **Fakt/Rechnung.** Der "Mittelweg" Tageshorizont ist weder a priori tot noch geprueft: Kompendium D enthaelt auf
   Tagesbasis nur H-22 (ein Praediktor, BTC, Schwelle IC 0,10 bei einer MDE von ~0,11 je Fenster). Mit 2.000-2.400
   BTC/ETH-Tagen ist ein Tages-Rank-IC von 0,051-0,056 (ein Fenster) bzw. 0,072-0,079 (C.10 je Haelfte) aufloesbar,
   das sind 10,6-16,4 bp/Tag brutto bei sigma 262 bp - genau die Groessenordnung der Friktionswand (Maker 4 / Taker
   11 / gesamt 15 bp je Umschlag). Der Tages-Querschnitt auf dem vollen Perp-Panel (2.130 Tage, K 300-600) loest
   IC 0,006-0,013 auf und hat einen Literatur-Prior (Ein-Tages-Reversal).
5. **Vorschlag.** Ein Drei-Zonen-Datenregime (Exploration / Validierung / versiegelte Konfirmation) mit
   institutionsweitem Fehlerbudget-Konto, rollierender Quartalsfreigabe und gruppensequentiellen Blicken ersetzt
   "Einmal-Gut + Blind-Siegel + zwei starre 12-Monats-Fenster". Es ist an drei Stellen Lockerung, an vier Stellen
   Verschaerfung; fuenf Punkte muss der Nutzer entscheiden (Abschnitt 3).
6. **Urteil.** Nicht-statistische Luecken: ein Strenge-Ratschen-Mechanismus ohne Gegenkraft (Reviews duerfen nur
   verschaerfen), ein Dokumentations-zu-Ergebnis-Verhaeltnis ohne Obergrenze, ein Blind-Siegel, das alle Klassen fuer
   eine Hypothese sperrt, die nach eigener Rechnung vor 2029 nicht testbar ist, und eine Nutzerrolle, die als
   "nie fragen" definiert ist, aber faktisch jede Programmentscheidung traegt und sie per Default (= strengste Option)
   ausfallen laesst.

---

## 1. Frage 1 - Wie weit ist die Idee realisiert, wo ist sie in Buchhaltung umgeschlagen, welche Instrumente fehlen?

### T-1 Die Pruefdisziplin ist realisiert; die Messinstitution nicht
- **Beleg.** Realisiert: Vorregistrierung mit Hash (DEC-90, DEC-101 E9), Blindheit mit Waechtern (DEC-96 E3, DEC-99
  (3)), gemessener Rauschboden (WP-7, DEC-67/70), Nullmodelle je Hypothese (faktorerhaltende Null DEC-75..88, Peso-
  Fixture PRD 3.3.5, Label-Permutation J-(i) DEC-103 E4), Positivkontrolle in Produktionskonfiguration, die einen
  Fehler vor der ersten realen Zahl fing (DEC-89/91), Power mit der SE des registrierten Tests (DEC-94 P-1),
  Stress-Kanon (DEC-55/56), Artefaktpflicht (DEC-53). Nicht realisiert: In 14 Monaten 3.0 (seit PROGRAMMENTWURF)
  existiert kein einziger Effektschaetzer mit Konfidenzintervall ueber irgendeine Praemie, einen Querschnitts-IC oder
  einen Ereigniseffekt; die Zustandsmaschine (Verfassung 3.0, Orchestrierungs-Protokoll) kennt nur ZENSUS -> REGISTRIERUNG -> LAUF -> GATE_CHECK.
  Der Zensus misst Nuisance (SD, c, K, Spreads, p_fill), nie den Effekt. STAND 2026-10-27: "Programm im
  Aufzeichnungsmodus ... keine registrierbare Hypothese in der Pipeline."
- **Gegenargument.** Genau diese Disziplin hat 2.0 vor Scheinbefunden bewahrt (31 Eintraege, 0 Torpfosten) und in 3.0
  drei falsch gepowerte Registrierungen vor dem Lauf gestoppt (GL-032..034). "Nichts gemessen" ist der Preis fuer
  "nichts erfunden".
- **Richtung.** Diagnose, neutral. **Zustaendigkeit.** Nutzer (Programmfrage PRD Par. 8: soll 3.0 eine
  Pruefinstitution fuer Literaturpraemien sein oder eine Messinstitution, die Effektgroessen mit Intervallen
  produziert?). Der Orchestrator kann ohne Nutzer die Pflicht-Berichtszeile "Effektschaetzer + CI + obere
  Ausschlussgrenze" fuer jeden Lauf einfuehren (T-2).

### T-2 Der Punktprior-Zwang macht aus der Institution einen Replikator; das fehlende Instrument sind Ausschlussgrenzen und Prior-Verteilungen
- **Beleg.** DEC-51 (2): Power 0,80 gegen den "benannten Mindesteffekt"; der Mindesteffekt kommt aus der Literatur
  (IC_prior 0,03 [sek], BVRP 0,14 [sek], 16,5 bp [sek]). Alle sechs 3.0-Feststellungen scheitern an dieser Stelle:
  GL-032 (Prior 0,03 fuer ein breites Perp-Universum nicht gestuetzt, DEC-98 N2), GL-033 (theta UNBELEGT, DEC-93 E2),
  GL-034 (Prior-Band 3,2..10,5 VP entscheidet Faktor 4..11 in der Dauer, DEC-98 N2/N5), GL-035 (Pilot ersetzt den
  Prior und findet das Gegenteil), GL-036 (kein Reversal-Prior fuer liquide Universen), A2 (V-5b UNBELEGT, DEC-103).
  In der Physik ist die Standardausgabe ohne Entdeckung die **obere Ausschlussgrenze** ("Effekt < x bei 95 %"); sie
  braucht keinen Prior. Rechnung (Anhang 9): auf 2.400 BTC-Tagen liegt die einseitige 95-%-Obergrenze bei beobachtetem
  IC 0 bei 0,034 (7,0 bp/Tag) - das ist Wissen, das heute nicht erzeugt wird, weil die Fenster fuer einen
  Bestaetigungstest aufgespart werden, der laut Bilanz vor 2028-2031 nicht kommt (PROGRAMM_BILANZ 0.1).
- **Gegenargument.** (a) Eine Ausschlussgrenze kann als "kein Effekt" gelesen werden - die Null-Zensus-Klausel
  (DEC-58 E2) schuetzt vor Promotion, nicht vor Demotion; es braeuchte eine Spiegelklausel. (b) Ohne Prior gibt es
  keine Power-Zeile; DEC-51 (2) wuerde zur Berichtszeile. (c) DEC-99 (Pilot-Schaetzfenster) ist bereits der halbe
  Schritt - um den Preis des "Verbrauchs".
- **Richtung.** Testbarkeit (neue Ausgabeart), ohne Aenderung von alpha oder Power-Ziel. **Zustaendigkeit.**
  Orchestrator: Berichtszeile "Schaetzer, 95-%-CI, obere Ausschlussgrenze, Shrinkage" als Pflicht in DEC-53 aufnehmen
  (kein Verdikt, keine Promotion). Nutzer: ob "Prior UNBELEGT" weiter die Registrierung blockiert oder ob eine
  Prior-**Verteilung** (Band mit Gewichten, erwarteter Informationsgewinn) als Power-Grundlage zugelassen wird
  (Programmfrage; Richtung Testbarkeit; Etikett Pflicht).

### T-3 Es fehlt ein gemeinsames, kalibriertes generatives Marktmodell (digitaler Zwilling) - jede Hypothese baut ihre Null neu und baut sie mehrfach falsch
- **Beleg.** A3: sechs Vorlaeufe (v2..v6b) und drei zurueckgezogene Registrierungen, weil die Null nacheinander
  Drift-Prognostizierbarkeit enthielt (DEC-76), Beta-Schaetzrauschen als Dispersion zaehlte (DEC-78, Faktor ~25),
  die Marktspalte falsch simulierte (DEC-85 D1), die W1-Kalibrierung mit W2-Werten rechnete (DEC-86 Nachtrag) und am
  Ende die reale Wochenstreuung um das 2,3..2,6-fache unterschaetzte (GL-035 Nebenbefund, DEC-101 E2 "skalierte
  Null"). H-27: Jensen-Term modellabhaengig 1,1..8,7 VP (DEC-97 B-3). A2: eigene Permutations-Null, eigene
  Stress-Kalibrierung (DEC-103 N1). Legacy-Code enthaelt Hawkes, HMM, BOCPD, GPD, MFDFA, Kyle-Lambda (tests/unit
  test_m8..m26), nie als gemeinsame Welt zusammengefuehrt.
- **Was fehlt.** Ein einmal auf der Vorperiode kalibriertes Mehrsymbol-Modell (Marktfaktor mit stochastischer Vol und
  Spruengen, Beta-Dispersion, idiosynkratische schwere Raender, Funding-Mechanik mit Totzone und Caps, Delisting-
  Hazard, Volumen-Vol-Kopplung, Tageszeitprofil), validiert gegen gemessene Invarianten (T-6), als EINE Quelle fuer:
  Nullverteilungen, Power-Zeilen, adversariale Fixtures, Operating-Characteristics-Simulation der gesamten Pipeline
  (T-16) und simulationsbasierte Inferenz (SBI: Posterior ueber Effektgroesse aus Summary-Statistiken, wenn die
  Likelihood nicht geschlossen ist - genau der Fall von Konjunktions-Gates wie bei A2).
- **Gegenargument.** Ein gemeinsames Modell propagiert einen Fehler in alle Hypothesen (S4/S5-Falle D.16:
  Infrastruktur vor validiertem Signal); seine Kalibrierung braucht Daten, die unter Siegel stehen; die
  hypothesenspezifische Null bleibt als Gegenprobe noetig.
- **Richtung.** Strenge (bessere Nullen) und Testbarkeit (konsistente, einmal geprueften Power). **Zustaendigkeit.**
  Orchestrator mit Herleitungsagent und Reviewer; keine Nutzerentscheidung; Vorperiode <= 2024-05-31 als
  Kalibrierbasis ist bereits mehrfach geoeffnet (Nuisance-Akten) und damit die natuerliche Quelle.

### T-4 Es fehlt sequentielle Inferenz (Alpha-Spending, gruppensequentielle Blicke); das Fixed-Sample-Design ist der eigentliche Zeitfresser
- **Beleg.** PROGRAMM_BILANZ Teil C Option 4 listet ausschliesslich Fixed-Sample-Varianten (Power-Ziel, alpha je
  Fenster, ein oder zwei Fenster). Die Exkurs-Synthese Abschnitt 3 verwirft anytime-valid/e-Werte mit der
  Begruendung "zweites Inferenz-Regime neben DEC-52 = offener Torpfosten". Rechnung (Anhang 7, Monte Carlo):
  O'Brien-Fleming-artige Grenzen bei einseitigem alpha 0,05 kosten mit 4 (8) Blicken 3,4 % (4,0 %) mehr maximale
  Information, senken aber die erwartete Information unter H1 auf 0,79 (0,75) und mit Futility-Grenze unter H0 auf
  0,72 (0,70) des Fixed-Designs. Zum Vergleich: die Zwei-Fenster-Regel braucht bei gleicher Gesamtfehlerrate und
  gleicher gemeinsamer Power 0,80 rund 26 % mehr Daten (DEC-98 A-3), ohne jede Moeglichkeit frueh aufzuhoeren.
- **Gegenargument.** Der Exkurs-Einwand ist richtig, solange C.10/DEC-52 UND ein sequentielles Regime nebeneinander
  stehen. Die Regime-Robustheit (Zweck von C.10, PRD 3.5 (a)) muss im sequentiellen Design neu kodiert werden (letzter
  Blick muss das juengste Quartal enthalten; Vorzeichenkonsistenz ueber Haelften als Bericht). Interimsblicke oeffnen
  Daten, die heute versiegelt sind - mit festem Spending-Plan ist das kein Torpfosten, aber eine Lockerung gegenueber
  C.10.
- **Richtung.** Testbarkeit (Zeit), neutral in der Fehlerrate. **Zustaendigkeit.** Nutzer (Verfassungsaenderung von
  C.10/DEC-52 zu einem einzigen sequentiellen Regime; PRD Par. 8). Der Orchestrator kann die Spending-Funktion,
  die Blick-Kadenz und den Code (`power_p1`-Erweiterung) vorbereiten.

### T-5 Blindheit wird fuer eine Verwendung aufgespart, die nicht kommt; Messung ohne Urteil ist verboten, obwohl sie frei waere
- **Beleg.** DEC-96 E3 versiegelt programmweit jede BTC/ETH-Vol- und Renditestreuungsstatistik ab 2026-07-01 fuer
  einen VRP-Lauf, der nach DEC-98 N5 "auf keinem Datenweg vor 2029 erreichbar" ist (mit Literatur-Prior 7,1 VP eher
  2033). DEC-98 E1 (b): das Siegel sperrt damit auch jede Klasse-W- und A1-Rechnung ab 2026-07-01. W1/W2 (2024-07..
  2026-06) bleiben fuer fm8-Statistiken "ungeoeffnet" (GL-036), obwohl kein registrierbarer Kandidat mehr existiert.
  Die Reihenfolge-Frage (DEC-98 E4 (b)) ist seit 2026-10-18 offen; der Default ist "niemand rechnet dort".
- **Gegenargument.** Ein geoeffnetes Fenster ist fuer jede korrelierte Statistik unwiederbringlich verbraucht
  (DEC-99 (5)); der Nutzer hat zweimal den Default gewaehlt (GL-036, P-0); die realisierte Vol der Fenster ist
  ohnehin schon in der Akte (DEC-95 E2) - das Siegel schuetzt heute vor allem gegen Vorwissen der Agenten, nicht gegen
  Daten.
- **Richtung.** Testbarkeit. **Zustaendigkeit.** Nutzer: Reihenfolge entscheiden. Vorschlag mit Default-Vorschlag:
  (a) VRP erhaelt ein enges Siegel nur auf DVOL-Niveaustatistiken; (b) realisierte Vol/Renditestreuung ab 2026-07-01
  wird fuer Zensus und Klasse W/E freigegeben mit Etikett "VRP-RV-Haelfte gesehen"; (c) W1/W2 werden zur
  Explorationszone erklaert (Abschnitt 3), weil kein konfirmatorischer Nutzer mehr existiert.

### T-6 Es fehlen Invarianten, Skalengesetze und Ereigniszeit als Messprogramm - nicht als Alpha-Suche
- **Beleg.** Das Programm hat eine einzige regime-invariante Groesse (B.14, Minuten-Impact-Permanenz ueber zehn
  Halbjahre) und sonst Konstanten (B.1-B.17, DEC-62/65/67/70/71). Keine Messung der Vol-Skalierung ueber Horizonte
  (1 min -> 1 d -> 1 w), der Volumen-Vol-Kopplung, der Varianzverhaeltnisse, der Funding-OI-Liquidations-Kopplung.
  Das 48-Slot-Tageszeitprofil (A2-Akte NUISANCE_SIGMA30 B-1: Minimum 37 bp um 04:00, Spitze 74 bp um 12:30-14:00
  UTC) entstand als Beifang und ist genau so eine Invariante. Alle Fenster sind Kalenderfenster; die A2-Akte zeigt
  Faktor 2,3 Streuungsunterschied zwischen 2021 und 2023 - ein 12-Monats-Fenster traegt je nach Jahr die halbe oder
  doppelte Information. Ereigniszeit (Volumen-/Vol-Zeit) wird nirgends verwendet.
- **Gegenargument.** Null-Zensus-Klausel: ein Zensus promotet keinen Kandidaten - richtig, und genau deshalb ist er
  risikolos; D.16 warnt vor Infrastruktur ohne Signal - Invarianten sind kein Signal, sondern die Kalibrierbasis fuer
  T-3 und fuer die Horizontwahl (T-7).
- **Richtung.** neutral. **Zustaendigkeit.** Orchestrator (kleine Pakete auf kline1m/publicTrade/kline1d, nur
  Vorperiode, nur Streuung).

### T-7 Welche "wissenschaftlichen" Instrumente heute auf den Daten sofort anwendbar sind (Inventar)
| Instrument | Status im Programm | Auf heutigen Daten anwendbar? | Bemerkung |
|---|---|---|---|
| Generatives Marktmodell / digitaler Zwilling | fehlt (hypothesenspezifische Nullen) | ja: Vorperiode <= 2024-05-31 (kline1m BTC/ETH, kline1d ALL, fundingRateAll, DVOL) | T-3 |
| Simulationsbasierte Inferenz / Operating Characteristics | teilweise (Positivkontrolle 3..200 Seeds) | ja, rein synthetisch | T-16 |
| Modellvergleich statt Punkt-Hypothese | fehlt (nur NHST einseitig) | ja | T-2; braucht Programmfrage |
| Ausschlussgrenzen / Intervallschaetzung | fehlt | ja, auf jedem Fenster, das nicht versiegelt ist | T-2 |
| Sequentielle Inferenz / Alpha-Spending | fehlt (Exkurs verwirft e-Werte) | ja (Code), Anwendung erst nach Verfassungsaenderung | T-4 |
| Mess-Invarianten, Skalengesetze | ein Fall (B.14) | ja: kline1m 2020-2026, publicTrade 5 Symbole | T-6 |
| Informationstheorie (TE, Entropie) | 2.0 auf Sekunden (H-04, H-06, H-15), nie auf Tagen | ja (kline1d, 2.130 Tage), Prior fehlt | Feld F7 |
| Netzwerk / Lead-Lag auf Tagesbasis | nur Sekunden (D.11, H-04) | nur Fluss-Varianten sinnvoll (Preise sind arbitragegleich) | Feld F7 |
| Ereigniszeit statt Kalenderzeit | fehlt | ja (Volumen aus publicTrade/kline) | T-6, Abschnitt 3 |
| Regime-/Zustandsmodelle (HMM, BOCPD) | Legacy-Code, D.-nah (C-08 "Ockham-tot") | ja, als Konditionierung mit eigenem K | Feld F11 |
| Extremwerttheorie | H-13 (GPD, gesperrt), C-20 | ja fuer Tagesrenditen 2020-2026; fuer Optionen seit 2026-06 | Nullmodell, kein Alpha |
| Hawkes/Punktprozesse fuer Liquidationen | C-14 REFUTED (Schwelle), H-21 gesperrt bis 2026-12-27 | nur 130 Tage allLiquidation (seit 2026-06-16) | Feld F9, erst Erreichbarkeits-Zensus |
| Mikro-zu-Makro-Aggregation | fehlt (H-24 nur Minuten) | ja: Bar-Cache/publicTrade 5 Symbole, 2.400 Tage | Feld F4 |

---

## 2. Frage 2 - Horizont-Schere: ist der Mittelweg a priori tot oder nie geprueft?

### T-8 Der Tageshorizont ist nicht a priori tot; Kompendium D enthaelt dort genau einen unterpowerten Versuch
- **Beleg (Kompendium D, Abgleich).** Tagesbasis: nur D.13 (H-22, L2-Buchneigung -> Folgetagsrendite, BTC
  urteilstragend, zwei Fenster, Schwelle IC >= 0,10; GL-027: IC +0,0665 / -0,0112). Bei ~500 Tagen je Fenster ist die
  MDE80 0,11 (Anhang 1) - der Test konnte nur einen riesigen Effekt sehen; der DROP sagt ueber IC <= 0,07 nichts.
  D.12 (Stunden), D.14 (30-Minuten-Vorwaerts-IC), D.4/D.5 (Sekunden), R2-K-06 (Kalender, 33 bp/Tag MDE) betreffen
  andere Horizonte oder andere Praediktoren. Funding-Dynamik, OI, Liquidationen, Optionsfluss wurden auf Tagesbasis
  nie getestet (H-01 war intraday, A1 ist eine Wochen-Praemie, H-21 gesperrt). WELLE6-Synthese strich "Wochenzyklus"
  und "BDEPTH-DIR" wegen Power, nicht wegen Befund.
- **Gegenargument.** Die Verfassung erlaubt den Tageshorizont ausdruecklich ("Tages- bis Wochen-Horizont", Klasse W);
  das PRD hat ihn aber auf den Wochen-Querschnitt verengt (PRD 4.1, 5.3) und K-0.1 nennt bei IC 0,05 einen
  Taker-Mindesthorizont von 2,7 Tagen - der Tageshorizont ist also beim Taker knapp unter der Wand.
- **Richtung.** Testbarkeit. **Zustaendigkeit.** Orchestrator (Herleitung); Registrierung scheitert heute am Prior
  (T-2) - dafuer Nutzer.

### T-9 Rechnung: aufloesbare Effektgroessen auf 2.000-2.400 Tagen und ihr Preis gegen die Wand
Annahmen (Akte): SE(Rank-IC) ~ 1/sqrt(N) (Tagesrenditen schwach autokorreliert, Spearman robust gegen schwere
Raender); sigma_1d BTC 262 bp (K-0.1) bzw. 210 bp (W2-aehnlich, DEC-85 Wochen-SD 5,5 %); bp/Tag = 0,798 x IC x
sigma_1d (Vorzeichenposition, Gauss); BTC+ETH als ein Cluster, rho 0,815 (DEC-67) -> N_eff-Faktor 1,10.

| N Tage | MDE80 ein Fenster (P-1) | MDE80 je Fenster bei C.10 (N/2) | MDE80 gepoolt (DEC-52, 2,5287) | bp/Tag bei 262 (ein Fenster / C.10) | bp/Tag bei 210 |
|---:|---:|---:|---:|---|---|
| 480 (H-22-Fenster) | 0,114 | 0,161 | 0,154 | 23,7 / 33,6 | 19,0 / 26,9 |
| 970 (OI seit 2024-03) | 0,080 | 0,113 | 0,108 | 16,7 / 23,6 | 13,4 / 18,9 |
| 2.000 | 0,056 | 0,079 | 0,075 | 11,6 / 16,4 | 9,3 / 13,2 |
| 2.130 (Panel seit 2021-01) | 0,054 | 0,076 | 0,073 | 11,3 / 15,9 | 9,0 / 12,8 |
| 2.400 (BTC-Trades seit 2020-03) | 0,051 | 0,072 | 0,069 | 10,6 / 15,0 | 8,5 / 12,0 |

Kostendeckung je Tag (IC_min = Kosten_RT x Umschlag / (0,798 x sigma); Umschlag = erwartete Vorzeichenwechsel je
Tag, bei AR(1)-Signal phi: 0,5 / 0,33 / 0,21 fuer phi 0 / 0,5 / 0,8):

| Kostenblock | Umschlag 1,0 | 0,5 | 0,33 |
|---|---:|---:|---:|
| Maker 4 bp RT (sigma 262) | 0,019 | 0,010 | 0,006 |
| Taker 11 bp RT | 0,053 | 0,026 | 0,017 |
| Gesamt 15 bp RT | 0,072 | 0,036 | 0,024 |
| Taker 11 bp bei sigma 210 | 0,066 | 0,033 | 0,022 |

**Lesart (Urteil).** Was statistisch auf der ganzen Historie aufloesbar ist (IC 0,05-0,08), ist zugleich die
Groessenordnung der Wand: bei vollem Tagesumschlag Taker-Grenze 0,053, Maker 0,019; bei persistenten Signalen
(phi 0,5) Taker 0,026. Der Tageshorizont ist also der einzige Horizont, auf dem ein kapitalfreies PASS auch
oekonomisch nicht automatisch "unter_wand" ist (Wochen-IC 0,03 traegt das Etikett `unter_wand`, DEC-73 E4; der
Sekundenhorizont liegt 80-500x darunter). Gewinn gegenueber dem Wochen-Querschnitt: 2.400 statt 104 Beobachtungen;
Verlust: 1,1 statt ~500 Querschnittseinheiten, also keine Querschnittsdiversifikation der Faktorstreuung - dafuer
aber keine faktorbedingte IC-Streuung (die A3 getoetet hat, GL-032). Die Trefferquote eines IC 0,05 ist 51,6 %
(Anhang 2): das ist ein Signal, das nur mit Umschlagskontrolle (Signalglaettung, Band) handelbar waere - das ist eine
Tradability-Frage (C.2), keine Mess-Frage.

**OOS-Disziplin fuer diesen Weg (Vorschlag, Strenge).** (1) Rank-IC mit PIT-standardisierten Praediktoren
(rollierend, kein Vollstichproben-z-Score). (2) BTC und ETH ein Cluster; Tagesgrenze 00:00 UTC, Funding-Termine
00/08/16 UTC als Kontrollvariable (H-01-Lehre). (3) Praediktoren-Register mit K: bei K = 10 ist E[max z] 1,58 ~
z_krit (Anhang 6) - die Schwelle muss die Decke nach DEC-51 (4) uebersteigen. (4) Chronologische Zonen (Abschnitt 3):
Exploration 2020-2023, Validierung 2024-2025, Konfirmation rollierend ab 2026, letzter Blick enthaelt das juengste
Quartal (REZENZ). (5) Pflichtausgabe Effektschaetzer + CI + Ausschlussgrenze (T-2). (6) Oekonomisches Etikett als
Kurve (Kosten als Funktion von Umschlag und p_fill, DEC-71), nicht als 11/15-bp-Konstante (T-10).

### T-10 Die Wand ist als Konstante fehlspezifiziert und hat die Mission fehlgeleitet
- **Beleg.** PRD 1 "Die vier Zahlen": Wand 11/15 bp als Konstante; WP-10(B) misst p_fill(60 s) 0,06 (FIFO) bis
  0,35 (pro-rata) und adv_sel 0,7 bp (DEC-71) - der Maker-Pfad ist eine Verteilung (Mehrminuten-Prozess mit
  Taker-Rueckfall), kein Skalar; `tradability3` existiert nur als RAISE-Stubs (PRD 6). Die Mission "ausschliesslich
  dort suchen, wo die Wand irrelevant wird" (Verfassung 3.0, Mission) hat das Programm auf Praemien (A1, H-27) und Wochen-Querschnitt
  gelenkt; A3 traegt trotzdem `unter_wand` (DEC-73 E4), A1 und H-27 brauchen bis 2030. Der Tageshorizont mit
  persistenten Signalen (Kosten 1-5 bp/Tag) wurde nie gegen die gemessene Fill-Kurve bewertet.
- **Gegenargument.** C.2: die Wand ist Etikett, kein Gate - formal hat sie nichts entschieden. Aber die Klassenwahl
  (PRD 3.2) ist eine Wand-Entscheidung. Eine Kurve statt Konstante aendert kein Verdikt, nur die Richtung der Suche.
- **Richtung.** neutral. **Zustaendigkeit.** Orchestrator (`tradability3.constants` mit Fill-Kurve ist beschlossen,
  DEC-71 E1, nicht gebaut); Programmfrage fuer den Missionstext.

---

## 3. Frage 3 - Fenster-Politik: ein gleich strenges Regime ohne jahrelange Wartezeit

### T-11 Vier Regeln multiplizieren sich zur Kalenderuhr
- **Beleg.** (i) "Einmal-Gut": nach einem Pilot ist der Abschnitt fuer jede korrelierte Statistik verbraucht (DEC-99
  (5)); (ii) Blind-Siegel programmweit (DEC-96 E3, DEC-98 E1 (b)); (iii) REZENZ: juengstes Fenster muss bestehen
  (DEC-99 (1)); (iv) zwei starre 12-Monats-Fenster, beide muessen bestehen (C.10; W2 endet 2026-06-28, DEC-99 (8)).
  Folge: jede neue Klasse braucht 24 Monate unberuehrter Daten nach dem Siegeldatum; das Siegeldatum wandert nur
  vorwaerts; jede Nuisance-Ausgabe bedroht es (B-2-Kanal, DEC-103 N1 (2): aus veroeffentlichten Klassenstreuungen ist
  der Pilot-Kontrast auf zwei Kandidaten rekonstruierbar - "die Blindheit haengt an Disziplin"). PROGRAMM_BILANZ 0.1:
  A3 2031, VRP 2030, A1 2030, A4 2029.
- **Gegenargument.** Jede der vier Regeln hat einen dokumentierten Anlass (C.18 Welle-6-Querbefund; DEC-95 RV-Haelfte
  gesehen; DEC-99 (5) Pilot-Verbrauch nach H-32). Das Problem ist ihr Produkt, nicht ihre Einzelberechtigung.
- **Richtung.** Diagnose. **Zustaendigkeit.** Nutzer (alle vier sind Verfassungs- oder Programmregeln).

### T-12 Vorschlag: Drei-Zonen-Regime mit institutionsweitem Fehlerbudget-Konto und rollierender Freigabe
**Zonen (rollierend am Kalender, Quartalsraster):**
- **Zone E (Exploration): alles aelter als 36 Monate.** Freie, wiederholte Nutzung durch alle Agenten. Pflicht: jede
  Abfrage (Statistik x Fenster x Variante) wird in ein **Konto** eingetragen (Hash, Familie, K); Ausgaben sind
  Effektschaetzer mit CI, Ausschlussgrenzen, Nuisance - **nie Verdikte**. Selektion wird ueber K (Bailey/LdP-Decke,
  DEC-51 (4)) und ueber die Validierungsstufe bezahlt, nicht ueber "Verbrauch". Ein Pilot (DEC-99 (2a)) ist eine
  E-Abfrage.
- **Zone V (Validierung): 36..12 Monate alt.** Genau ein vorab registrierter Blick je Hypothesenfamilie; alpha aus dem
  Jahresbudget; Blindheit **mechanisch**: eine Hypothese darf nur Quartale nutzen, die beim Zeitpunkt ihrer
  Registrierung noch in Zone K lagen (Registrierung vor der Daten-Existenz als V-Daten) - das ersetzt den Siegel-
  Waechter durch ein Datum.
- **Zone K (Konfirmation): die juengsten 12 Monate, versiegelt.** Jedes Quartal wandert das aelteste K-Quartal nach
  V. Eine registrierte Hypothese sammelt in K Information in **gruppensequentiellen Blicken** (O'Brien-Fleming,
  Spending-Plan im YAML): Abbruch wegen Wirksamkeit oder Futility, sonst weiter; der letzte zulaessige Blick muss das
  juengste Quartal enthalten (REZENZ). Ein Blick erzeugt (Verdikt, CI, Hash); die Outcome-Serie des Quartals wird fuer
  diese Statistik danach nie mehr geoeffnet ("nie zweimal gesehen" = Identitaet Statistik x Quartal im Konto). Eine
  andere Familie mit anderer Statistik darf dasselbe Quartal nutzen; die Abhaengigkeit wird ueber BY ueber alle
  Blicke des Jahres bezahlt.
- **Fehlerbudget-Konto (neu):** ein Jahresbudget je Institution (z. B. alpha_Jahr 0,05 einseitig, per Spending-Funktion
  auf Registrierungen verteilt; oder FDR q 0,10 BY ueber alle Blicke des Jahres einschliesslich Validierung und
  Pilot-Uebergaben). Heute: FDR je Welle (C.16, F-WEEK), kein jahresuebergreifendes Konto, Pilots und Zensus-Blicke
  zaehlen nicht (DEC-99 (7) zaehlt nur getestete Hypothesen).

**Rechenbeispiele.** Gruppensequentiell K = 4 Blicke (Quartale) bei alpha 0,05 einseitig: Grenzen auf B-Skala 1,73
(erste z-Grenze 3,47, letzte 1,73); maximale Information +3,4 % gegen Fixed; erwartete Information unter H1 0,79, mit
Futility unter H0 0,72 (Anhang 7). Gegen C.10 (gemeinsame Power 0,64, +26 % Daten nach DEC-98 A-3) spart das im
Erwartungswert rund ein Drittel der Kalenderzeit bei gleicher Fehlerrate - und beendet hoffnungslose Hypothesen frueh,
statt sie zwei Jahre laufen zu lassen.

**Was Lockerung, was Verschaerfung ist (Etikett, Pflicht):**
| Punkt | gegen heute | Richtung |
|---|---|---|
| Wiederverwendung von Zone E ohne "Verbrauch" (Ersatz von DEC-99 (5) durch Konto + K) | Lockerung | Testbarkeit |
| Korrelierte, aber verschiedene Statistiken duerfen dasselbe Quartal nutzen (BY statt Sperre) | Lockerung | Testbarkeit |
| Interimsblicke mit Spending statt zwei Vollfenster (ersetzt C.10/DEC-52 durch EIN Regime) | Lockerung in der Zeit, neutral in alpha | Testbarkeit |
| Jahresweites Fehlerbudget ueber alle Blicke, Pilots und outcome-beruehrende Zensus | Verschaerfung | Strenge |
| Mechanische Blindheit (Registrierung vor Datenexistenz) statt Waechter und Disziplin | Verschaerfung | Strenge |
| Futility-Stopp (heute laeuft jede Hypothese bis zum Ende) | Verschaerfung | Strenge |
| Pflicht-Ausgabe Ausschlussgrenze auch bei GL-012 (Wissen statt Nichts) | Verschaerfung der Berichtspflicht | neutral |

**Was der Nutzer entscheiden muss (PRD Par. 8):** (1) Hoehe und Form des Jahresbudgets (alpha-Spending oder FDR q);
(2) Zonenlaengen (36/12 Monate) und Freigabekadenz (Quartal); (3) Ersatz von C.10/DEC-52 durch das sequentielle Regime
(Verfassung) und wie Regime-Robustheit kodiert wird (letzter Blick juengstes Quartal; Vorzeichenkonsistenz als
Bericht oder als Gate); (4) Behandlung der bereits kontaminierten Fenster: W1/W2 fuer Klasse W und die A2-Vorperiode
als Zone E deklarieren (Lockerung, ehrlich: sie sind faktisch nicht mehr blind, DEC-103 N1 (2)); (5) ob
Explorations-Schaetzer die Richtung einer Registrierung bestimmen duerfen (heute Etikett "Richtungswahl nach
Kenntnis", DEC-102 E2) - im Konto-Regime ist das der Normalfall, bezahlt ueber K.
- **Gegenargument.** Der Exkurs hat anytime-valid-Inferenz verworfen; die Literatur zum wiederverwendbaren Holdout
  [sek: Dwork et al. 2015, Thresholdout] zeigt, dass selbst disziplinierte Wiederverwendung leckt - ein Konto haelt
  nur ehrliche Agenten; die B-2-Lehre (Leck ueber Nuisance-Ausgaben) wird durch kein Konto geschlossen, nur durch die
  Ausgaberegel (DEC-103 N1 (2c), die bleibt). Die Regime-Robustheit von C.10 ist in einem sequentiellen Design
  schwaecher. Der Nutzer hat bisher jede Lockerung abgelehnt.
- **Richtung.** gemischt, je Zeile etikettiert. **Zustaendigkeit.** Nutzer (Punkte 1-5); Orchestrator kann vorab das
  Konto (Inventar aller bisher geoeffneten Statistik x Fenster-Paare aus den C.17-Listen), die Zoneninventur und den
  Spending-Code bauen - ohne Regelwirkung.

### T-13 Regel-Stapelung ohne Strenge-Budget: der A2-Pilot als Lehrstueck
- **Beleg.** PILOT_ROUTE_A2 T10/T11: Grundfassung c_A2 24,4 bp; Stress-Kalibrierung +2,8, skalierte Null +2,1,
  Gate-(4)-Faktor +2,8 -> 32,1 bp; dazu Produkt-Zuordnung (konservative Untergrenze: gemeinsame Power 0,914 gegen
  Produkt x Gate-4 0,825), drei Placebos, 12-Monats-Fenster. Pilot-Uebergabe beim einzigen belegten Prior (16,5 bp):
  0,0001. Jede Festlegung einzeln ist "Richtung Strenge" und begruendet (DEC-103 N1 (8)); die Summe macht den Test
  gegen jeden plausiblen Effekt blind. Es gibt keine Regel, die die **kumulierte** Strenge begrenzt - das
  Gabelungs-Etikett zaehlt Richtungen, summiert sie aber nicht.
- **Gegenargument.** Jede Verschaerfung schloss ein reales Leck (B-1-Kanal, Futures-Tage, PRD-Placebosatz). Ein
  "Strenge-Budget" waere selbst eine Gabelung Richtung Testbarkeit.
- **Richtung.** neutral (Transparenzregel). **Zustaendigkeit.** Orchestrator: Pflichtzeile "MDE80 (alle Festlegungen)
  / MDE80 (Grundfassung)" in jeder Registrierung; ab Faktor 1,3 ausdrueckliche Nutzer-Vorlage.

---

## 4. Frage 4 - Unentdeckte Forschungsfelder

Vorbemerkung zur Power-Spalte: alle Zahlen analytisch aus Akten-Nuisance (Anhang); "Vermutung" markiert Annahmen
ohne Fundstelle. MDE80 nach P-1 (Faktor 2,4865), "C.10" = je Haelfte. Dateninventar Stand 2026-11-01.

| Nr | Feld / Hypothesenfamilie | Mechanismus und Zahler | Statistik | Daten vorhanden | nachzubestellen | Power (analytisch) | Friktions-Etikett | Risiken | Kompendium-D-Bezug |
|---|---|---|---|---|---|---|---|---|---|
| F1 | Tages-Querschnitts-Reversal (1-3 Tage) auf dem vollen USDT-Perp-Panel, Gap-Design (ein Tag Luecke), beta-neutral | Liquiditaetsbereitstellung; Zahler: Fluss, der grosse Positionen durchdrueckt, liquidierte Hebelhalter | mittlerer taeglicher Rank-IC, skalierte Null, Cluster = Tag | `bybit/rest.kline1d ALL` 2021-01-01..2026-10-31 (2.130 Tage, K 300-600), `delisting_dates`, `rest.instruments` | nichts | SD(IC_t) 2,5 x Boden (Vermutung aus GL-035): K 500, N 1.065: MDE80 0,0085 (~11 bp/Tag L/S brutto); N 2.130: 0,0060 | `unter_wand` (Taker, Tagesumschlag); Maker-Pfad mit p_fill 0,06-0,35 Bericht | Bid-Ask-Bounce (Gap-Design Pflicht); Universums-Zuordnung der Literatur (H-33-Lehre); Delisting (Union-Panel vorhanden) | D.7 war N=5 (nicht einschlaegig); D.13 anderer Praediktor; H-33 (Wochen) GL-036 - Tag ist andere Statistik; Prior: Ein-Tages-Reversal belegt [sek: Bianchi et al., Top-100, IC 0,09 EW / 0,023 VW; BELEGE_AUS_PDF] |
| F2 | Funding-Dynamik als Tages-Praediktor: (a) Zeitreihe BTC/ETH (Funding-Niveau/-Aenderung -> 1-5-Tages-Rendite), (b) Tages-Querschnitt (Funding-z -> Folgetag) | Ueberhebelte Positionierung -> Abbau; Zahler: spaete Hebel-Longs/Shorts | Rank-IC TS (N 2.130) bzw. XS (K 300-600) | `rest.fundingRateAll` 2021-01-01.., `rest.fundingRate` 5 Symbole ab 2024-03, kline1d | nichts | TS: MDE80 0,054 (ein Fenster) / 0,076 (C.10) = 11,3 / 15,9 bp/Tag; XS wie F1 | TS mit phi >= 0,5: Taker-Grenze IC 0,026 -> moeglich `ueber_wand`; XS `unter_wand` | 47 % Totzone (F = I) -> nullinflationierter Praediktor (DEC-59/84); Auto-Switch seit 2025-10-30 (Regimebruch); Prior UNBELEGT -> heute GL-012 vor Registrierung (T-2) | H-01 (intraday Settlement) DROP, anderer Horizont; A1 (Wochen-Praemie) GL-033, andere Frage (Praemie statt Prognose) |
| F3 | OI-Dynamik (OI-Aenderung, OI/Volumen, Hebelmass) -> Tagesrendite und Tagesvol BTC/ETH | Positionierungsmass; Zahler: Zwangsliquidierte bei Hebelabbau | Rank-IC TS; Vol: Zusatzregressor gegen gedresste HAR (C.4/B.9-Lehre) | `bybit/rest.openInterest` BTC/ETH 2024-03-01.. (970 Tage), 5 Symbole ab 2026-03, `binance/rest.openInterest` ab 2026-05 | OI-Historie aller Perps (Bybit REST `open-interest`, Tiefe UNBELEGT - PRD 7.2 Punkt 3); Binance OI-Backfill | N 970: MDE80 0,080 (16,7 bp/Tag) / C.10 0,113 - grenzwertig; waechst mit ~365 Tagen/Jahr | wie F2 | Vol-Prognose ist D-nah (H-02/H-11: muss gedresste HAR schlagen); kurze Historie | nicht in D; H-09 (Risk-Limit-Bunching) ist anderer Mechanismus |
| F4 | Mikro-zu-Makro: taeglich aggregierter Netto-Orderfluss (buy-sell aus publicTrade) -> gleichzeitige Tagesrendite (Kyle-lambda-Invariante) und Folgetagsrendite | Permanenter Impact (B.14) aggregiert; Zahler: Liquiditaetsnehmer | Invariante: Regressionskoeffizient je Jahr mit CI; Prognose: Rank-IC TS | `bybit/publicTrade` 5 Symbole 2020-03-25.. (2.413 Tage BTC), WP-0-Bar-Cache (vol_buy/vol_sell) | nichts | Invariante: trivial (N 2.400, gleichzeitiger IC ~0,5 auf Minuten, B.14); Prognose: MDE80 0,051 / 0,072 | Prognose `unter_wand`/Grenze wie F2 | D.14-Nachbarschaft: "kein H-24-Ergebnis rehabilitiert OFI" - gilt fuer Minuten-Fortsetzung; Tagesaggregation ist andere Statistik, Etikett Pflicht | D.5, D.14 (Minuten), hier Tage |
| F5 | Delisting-/Listing-Ereignisse im Panel: CAR um Ankuendigung, letzten Handelstag, erste 1-8 Wochen nach Listung; Delisting-Hazard (IPCW, DEC-58 E1 (g)) | Zwangsschliessung von Positionen; Listing-Pump (PRD 4.1 DoD (4) schneidet 8 Wochen ab = unbewiesene Annahme); Zahler: Halter ohne Ausstieg | Ereignis-CAR, Placebo = Zufallstage gleicher Kalenderstruktur, Cluster = Tag | `delisting_dates` (306 Symbole), `rest.instruments` ab 2026-10-20 (launchTime, deliveryTime), kline1d ab 2021 (~800 Listungen, ~300 Delistungen) | nichts (irreversibler Roster laeuft) | Alt-Tagesvol ~650 bp (Vermutung aus Median-Wochenvol 17 %): N 300 -> SE 37 bp, MDE80 93 bp/Tag; Listing N 800 (Vol 900 bp): MDE80 79 bp/Tag | Delisting-Short praktisch unhandelbar (`unhandelbar`); Listing `unter_wand`/offen | Ankuendigungs- vs. Handelsende-Datum (Median +2 Tage, DEC-100); Survivorship per Konstruktion; Stichprobe aller Delistungen = eine Aera | nicht in D; methodischer Nutzen fuer jede Klasse-W-Korrektur (Survivorship +0,003 gemessen, WP-7 B3) |
| F6 | Makro-Ereignisse (FOMC-Entscheid, CPI, NFP): 30-min- und 1-Tages-Fenster, Vor-Ankuendigungs-Drift | Exogener Kalender (Klasse E), Informationsfreigabe; Zahler: ungehedgte Vol-Verkaeufer/ spaete Reagierer | CAR ueber EIN registriertes Fenster, Placebo = gleicher Slot an Nicht-Ereignistagen | `rest.kline1m` BTC 2020-03-25.., ETH 2021-03-15.. | oeffentliche Termin-Kalender (BLS/Fed, frei) als Datei; keine Marktdaten noetig | FOMC N 48 (6 J): 30-min-Slot SD ~74 bp (A2-Profil 12:30-14:00 als Proxy) -> MDE80 26,6 bp; 1-Tag MDE80 94 bp; CPI N 72: 21,7 / 77 bp | ein Trade je Ereignis: Wand praktisch irrelevant (`ueber_wand`, sofern Effekt > 15 bp) | Prior fuer Krypto UNBELEGT (Aktien-Analogon Vor-FOMC-Drift ~49 bp [sek], seit 2016 verblasst); US-Makro-Slots kontaminieren A2-P3 (A2-Akte) | nicht in D; R2-K-06 (Kalender-Interaktion) war Wochenende/Session, anderes |
| F7 | Informationsfluss auf Tagesbasis zwischen Venues/Instrumenten: Fluss-Anteile (Binance/Bybit/Deribit Perp-Volumen, Options- vs. Perp-Fluss) -> Folgetagsrendite; Transfer-Entropie auf Tagesreihen | Informierte Venue-Wahl; Zahler: Spaetreagierer | Rank-IC TS; TE mit Block-Surrogaten | `binance/publicTrade` BTC ab 2025-01 (610 Tage), 4 Symbole ab 2026-03; `deribit/publicTrade` ab 2025-08 (251 Tage, Inhalt der Symbole "BTC"/"ETH" ungeprueft - C.8-Probe); `bitmex` 2026-03..09 | Inhaltsprobe `deribit/publicTrade` Symbol "BTC" (Optionstape?) | N 610: MDE80 0,101 - zu kurz; ab 2027 ~0,07 | `unter_wand` | Preise sind arbitragegleich (nur Fluss traegt Information); Prior UNBELEGT | D.11 (Deep-Learning-Graph, Sekunden), H-04 (Sekunden): anderer Horizont |
| F8 | Optionsfluss/GEX-Konditionierung der Verfallseffekte (A2 nur Freitage mit OI im obersten Dezil; Netto-GEX-Vorzeichen) | Hedge-Fluss der Market-Maker, skaliert mit ATM-OI; Zahler: Optionshalter am Settlement | A2-Kontrast konditioniert; GEX aus OI je Strike und Greeks | `deribit/tickers` (OI, IV, Greeks je Strike) und `bybit/tickers` Optionen seit 2026-06-16; `tardis/options_chain` 2019-2026 nur 91 Tage (1 Tag/Monat: fuer Fluss unbrauchbar, fuer monatliche Skew-/Term-Struktur 91 Punkte) | nichts Neues (Strom laeuft, irreversibel); historisches OI je Strike nicht nachladbar | Freitage mit GEX bis 2027-06: 52 -> MDE80 15,1 bp; bis 2028-06: 104 -> 10,7 bp; nur oberstes OI-Dezil: N 10 -> 34 bp | Ereignis, `ueber_wand` bei > 15 bp | Weiss et al. [sek] finden den Effekt NUR im obersten OI-Dezil -> Teilmenge klein; K-Inflation durch Konditionierung | R3-K-32 (GEX-KOND) im PRD 9.1 vertagt "nicht vor A2-PASS" - mit der laufenden Aufzeichnung ist die Vorbedingung umgekehrt: GEX ist die Effektgroessen-Quelle, die V-5b fehlt |
| F9 | Liquidations-Kaskaden: Groessenverteilung, Branching-Ratio (Erreichbarkeits-Zensus zuerst, D.2), Nachlauf in Ereigniszeit; Insurance-Fund-Dynamik | Zwangsverkaeufe erzeugen Zwangsverkaeufe; Zahler: Liquidierte | Zaehlung, GPD-Tail, Hawkes nur nach Erreichbarkeits-Check; Superposed-Epoch wie WP-11 | `bybit/allLiquidation` 5 Symbole ab 2026-06-16 (~130 Tage, 163 k Zeilen), `bybit/insurance` ab 2026-06-16; `binance` keine Liquidationen | Liquidations-Historie anderer Boersen (Binance forceOrder-Stream nur live; historisch nur kommerziell) | Ereigniszahl UNGEMESSEN; 130 Tage reichen fuer Verteilungsform, nicht fuer Nachlauf-CAR | Stunden-Horizont: unter der Wand; Wert: Nullmodell/Kosten (Stress-Fills, DEC-71 E2 RAISE) | D.2 (Branching-Schwelle importiert) - Erreichbarkeit vor jeder Schwelle; H-21 (LIQ-TAG) gesperrt bis 2026-12-27 | D.2, E.1, E.12 (CS-06 Kaskaden-Cockpit) |
| F10 | Term-Struktur der Basis auf Deribit-Futures (A4-Vorlaeufer): realisierter Wedge je Verfallzyklus seit 2017 | Laufzeitsicherheit (Hedger zahlt), DEC-59 A4 | w je Zyklus, Cluster = Verfall | `deribit/rest.settlements` (BTC ab 2017-05, ETH ab 2019-03), `rest.deliveryPrices` ab 2016; Einstiegsbasis (Futures-Preis bei Listung/Roll) NICHT im Archiv; `deribit/publicTrade` ab 2025-08 (Inhalt pruefen) | historische Deribit-Futures-Kurse verfallener Instrumente (API fuer expired instruments UNBELEGT; sonst kommerziell) | 8 Quartalszyklen/2 J: MDE80 = 0,879 sigma_w (PRD 5.4); mit 2017-2026 ~36 Quartale: 0,41 sigma_w | kapitalgebunden 90 Tage; `ueber_wand` laut R1 0.3 | sigma_w UNGEMESSEN; Deribit-Futures sind inverse Kontrakte (anderes Produkt als Bybit-A4) | A4 recording-first (DEC-59), Daten ab 2026-10-20; hier historische Umgehung |
| F11 | Zustandsabhaengigkeit: Konditionierung von F1/F2/F6 auf DVOL-Terzile bzw. HMM-Zustand; Modellvergleich (konditional vs. unkonditional) statt zweier Tests | Praemien/Prognosen sind regimeabhaengig (WP-10(A2): Funding-Kohaerenz 0,6-0,7 im Stress gegen 0,2-0,35) | Bayes-Faktor / vorhergesagte Log-Likelihood out-of-sample; K zaehlt Zustaende | `deribit/dvol` 2021-03-24.. (2.048 Tage), RV aus kline1m | nichts | je Terzil N/3: MDE80 x 1,73; nur mit Modellvergleich sinnvoll | wie Basisfeld | Forking paths (K); C-08 BOCPD "Ockham-tot" (nach H-01) - als Konditionierung mit eigenem K nicht einschlaegig | D.-nah (C-08), R2-K-07 Vol-Targeting nur als vorab fixierte Variante |
| F12 | Stablecoin-Angebot und Boersen-Netflows als Tages-/Wochen-Praediktor | Primaer-Liquiditaetszufluss; Zahler: Zufluss-Spaetkaeufer | Rank-IC TS (Supply-Aenderung -> 1-7-Tages-Rendite) | keine | USDT/USDC-Gesamtangebot taeglich (DefiLlama-API frei, ab ~2021 [sek]), Exchange-Netflows (kommerziell: Glassnode/CryptoQuant) | N ~1.800: MDE80 0,059 / 0,083 | Wochenhorizont, `ueber_wand`-faehig bei IC >= 0,03 (Wochen-TS) | Datenqualitaet/Revisionen; Literatur [sek: Griffin/Shams, Tether] aeltere Aera | nicht in D; einzige Feld ohne Datenbasis |

**Zustaendigkeit je Feld.** F1, F2(b), F4 (Invariante), F5, F6: Orchestrator kann Herleitung und Nuisance-Zensus
sofort beauftragen (nur Vorperiode, Waechter). F1 und F5 haben Literatur-Prioren (Bianchi; Delisting-Literatur
Aktien [sek]) und sind unter heutigen Regeln registrierbar. F2(a), F3, F4 (Prognose), F7, F12: Prior UNBELEGT -> ohne
T-2-Entscheidung des Nutzers GL-012 vor Registrierung; als Explorations-Messung mit Ausschlussgrenze sofort
moeglich. F8, F10: Data-Harvest (Inhaltsproben C.8: `deribit/publicTrade` Symbole "BTC"/"ETH"; Deribit expired
instruments). F9: Zaehl-Zensus zuerst. F11: nur als registrierte Variante eines Basisfelds.

**Rangfolge (Urteil, nach Testbarkeit heute x Passung zur Mission):** F1 > F5 > F2 > F4 > F6 > F8 > F3 > F12 > F10 >
F11 > F7 > F9. F1 ist das einzige Feld, in dem grosse Daten (2.130 Tage x 500 Symbole), ein Literatur-Prior und ein
kapitalfreies Design zusammenkommen; sein Preis ist das Etikett `unter_wand` beim Taker.

---

## 5. Frage 5 - Was wir uebersehen haben, das nichts mit Statistik zu tun hat

### T-14 Strenge-Ratsche: der adversariale Review hat keine Gegenkraft
- **Beleg.** Alle Reviews der Akte enden mit "Zustimmung mit Auflagen" oder VETO; jede Auflage ist "Richtung
  Strenge" (REVIEW_A2_TEILC A-1..A-9, REVIEW_H32 A-1..A-9, REVIEW_H33 bedingtes Vorab-VETO, REVIEW_H28_H30 v1-v3).
  Eine Auflage Richtung Testbarkeit waere definitionsgemaess Torpfosten (DEC-93 E3, DEC-97). Folge: drei
  Registrierungsfassungen A3, zwei Fassungen jeder A2-Datei, kumulierte Strenge ohne Deckel (T-13). Es gibt keine
  Abbruchregel fuer die Review-Schleife und keinen symmetrischen Pruefauftrag ("ist der Test gegen den
  Literatur-Prior noch sensitiv?").
- **Gegenargument.** Die Reviews haben reale Fehler gefangen (DEC-85 D1, DEC-101 B-1, DEC-103 B-1). Asymmetrie ist
  bei Falsifikationsprogrammen gewollt.
- **Richtung.** Testbarkeit (Symmetrie im Mandat), Strenge in der Sache. **Zustaendigkeit.** Orchestrator: Review-
  Mandat um die Pflichtfrage "Sensitivitaet gegen den Prior nach allen Auflagen" und eine Schleifen-Obergrenze
  (zwei Fassungen, dann Nutzer-Vorlage) ergaenzen.

### T-15 Dokumentationslast ohne Obergrenze; Zustand ist Prosa, nicht Maschine
- **Beleg.** `decisions.md` DEC-51..103: 675 Zeilen dichter Text, einzelne Nachtraege ueber 60 Zeilen (DEC-98 N5);
  A2-Akte ~6.800 Zeilen fuer eine Hypothese ohne Registrierung; UEBERGABE Nachtrag 10a-10e: fuenf Teilschritte eines
  Tages. Maschinenlesbar ist nur die H-32-YAML. Eine "vollautomatische Institution" (Auftrag) braucht Zustand als
  Daten (Konto, Register, Zonen, Siegel) - heute muss jede neue Sitzung tausende Zeilen lesen, um nichts zu verletzen
  (die Leseliste dieses Auftrags: ~6.000 Zeilen).
- **Gegenargument.** Die Prosa ist der Audit-Trail; ohne sie waeren DEC-85/91/101 nicht nachvollziehbar.
- **Richtung.** neutral. **Zustaendigkeit.** Orchestrator: DEC-Schema (JSON/YAML: Regel, Etikett, Richtung,
  Fehlerrate, betroffene Konstanten) neben der Prosa; Konto als Tabelle (T-12). Nutzer: Budget fuer Agentenzeit.

### T-16 Fehlerkultur: gut im Fangen, spaet im Fangen; es fehlt die Operating-Characteristics-Simulation
- **Beleg.** Neun materielle Selbstkorrekturen in acht Wochen (DEC-60 Schaetzer uninformativ, DEC-64 Null fehlte,
  DEC-69 Slice-Fehler, DEC-85 D1/D2, DEC-86 Nachtrag W1-mit-W2-Kalibrierung, DEC-88/91 Boden-SE, DEC-101 B-1 USDC-
  Zwillinge, DEC-103 B-1/B-2 Varianzzerlegungs-Kanal). Alle wurden nach einem Lauf oder im Review gefunden, nicht
  durch einen Test der Pipeline. Der Standard klinischer Studien - die gesamte Entscheidungskette (Daten -> Gate ->
  FDR -> Verdikt) unter H0 und H1 tausendfach zu simulieren und alpha/Power empirisch zu bestaetigen - fehlt; die
  Positivkontrolle (3 Seeds DEC-89, 200 Seeds im A2-Design) ist der Anfang davon. Der B-2-Kanal ist eine andere
  Fehlerklasse (Informationsleck ueber veroeffentlichte Nuisance); DEC-103 N1 (2c) (Ausgabe nur als Partition) ist die
  richtige Antwort, eine Verbotsliste ist es nicht.
- **Gegenargument.** Die Korrekturen zeigen, dass das System funktioniert; eine OC-Simulation braucht das
  generative Modell (T-3), das es nicht gibt.
- **Richtung.** Strenge (Methode), Testbarkeit (Durchsatz). **Zustaendigkeit.** Orchestrator (T0-Pflicht
  "OC-Simulation der Gate-Kette, >= 1.000 Seeds" vor jeder Registrierung).

### T-17 Die Nutzerrolle widerspricht sich: "nie fragen", aber jede Programmentscheidung liegt beim Nutzer und faellt per Default streng aus
- **Beleg.** Verfassung 3.0, Autonomie-Protokoll 3 ("niemals den Nutzer fragen"); offene Nutzerentscheidungen: Reihenfolge
  der Blindperiode (seit 2026-10-18), P-0..P-3 (A2), H-33-Prior (Default gewaehlt), PDFs (kostenpflichtig, nicht
  beschafft). Default ist stets die reversibelste = strengste Option (C.19) -> die Institution driftet per Konstruktion
  in den Aufzeichnungsmodus. Zugleich ist der Nutzer der einzige Literaturkanal: arXiv, SSRN, Verlage, Deribit-Doku,
  CME sind aus der Umgebung gesperrt (DEC-98 N1, DEC-103 Netzsperre) - eine autonome Institution, die Prioren aus der
  Literatur braucht (T-2), aber die Literatur nicht lesen darf.
- **Gegenargument.** Programmfragen (PRD Par. 8) gehoeren zum Nutzer; die Strenge-Defaults sind gewollt.
- **Richtung.** neutral. **Zustaendigkeit.** Nutzer: (a) stehende Default-Politik festlegen ("bei Stille gilt
  Option X" je Fragetyp, auch Richtung Testbarkeit); (b) Netzwerk-Freigabe fuer arXiv/SSRN/Deribit-Doku in den
  Umgebungseinstellungen (billig, kein Geld); (c) Budget fuer Volltexte. Orchestrator: Liste der offenen Fragen mit
  Default und Kosten der Verzoegerung als Pflichtteil jeder Uebergabe.

### T-18 Kostenstruktur und Data-Harvest: die Daten sind nicht der Engpass
- **Beleg.** Alle Datenauftraege B-0..B-5 (DEC-98 E3) wurden binnen Tagen erfuellt, der Tagesstrom aller Perps bis
  2021-01-01 rueckgefuellt (DEC-100 N1), 1-min-Kerzen ab 2020/2021, Settlements ab 2017; Dateninventar 2026-11-01:
  ~2,3 TB, 29 Stroeme. STAND Abschnitt 4: "Nicht wegen der Daten. Nicht wegen des Codes." Die Kosten des Programms
  sind Agentenzeit fuer Herleitung/Review/Prosa; CPU-Zeit ist Minuten bis Stunden (PRD 7.3).
- **Gegenargument.** Irreversible Stroeme (Roster, A4-Quotes, Options-OI) muessen weiter laufen; sie sind billig.
- **Richtung.** neutral. **Zustaendigkeit.** Data-Harvest ueber den Nutzer: nur noch die drei Inhaltsproben/Auftraege
  aus der Felder-Tabelle (F7/F10 `deribit/publicTrade`-Inhalt; F3 OI-Historie aller Perps; F12 Stablecoin-Angebot,
  frei); Negativ-Panel (ANFRAGE 2026-10-31) bleibt.

---

## 6. Was NICHT folgt

- Kein Verdikt ueber Momentum, Reversal, Carry, VRP, Verfallseffekt oder irgendeinen Markteffekt; alle Zahlen in
  Abschnitt 2 und 4 sind Aufloesungsgrenzen aus Nuisance, keine Effektgroessen.
- Keine Empfehlung, ein Siegel zu brechen oder eine Regel still zu aendern; jede Lockerung in Abschnitt 3 ist als
  solche etikettiert und braucht den Nutzer (PRD Par. 8) - der Orchestrator kann nur vorbereiten (Konto, Inventar,
  Code, Berichtszeilen).
- Keine Aussage, dass der Tageshorizont handelbar ist: die Rechnung zeigt "aufloesbar ~ Wand", also eine offene
  Tradability-Frage (C.2), keine Kante.
- Keine Entwertung der 2.0-Lehren C.1-C.19 oder der 3.0-Feststellungen GL-032..036: sie stehen; kritisiert wird
  die Kombination der Regeln und das Fehlen von Mess-Ausgaben, nicht einzelne Urteile.
- Keine Uebernahme der im Exkurs verworfenen Instrumente (SIR, Fruehwarnsignale, DiD mit Binance-Backfill usw.);
  das sequentielle Design (T-4/T-12) ist bewusst als Ersatz, nicht als zweites Regime vorgeschlagen.
- Die Power-Zahlen der Felder-Tabelle beruhen auf markierten Annahmen (Faktor 2,5 x Boden fuer den Tages-Querschnitt,
  Alt-Tagesvol 650 bp, Slot-SD 74 bp); vor jeder Herleitung sind sie auf der Vorperiode zu messen (nur Streuung).

---

## Anhang - Rechenweg (Skript `state/prd_analyse_2026-11-01/scripts/konzept_calc.py`, nur Formeln)

1. Tages-TS-IC: MDE80 = 2,4865/sqrt(N) (ein Fenster), 2,4865/sqrt(N/2) (C.10), 3,3703/sqrt(N) (DEC-52 gepoolt unter
   P-1); bp/Tag = 0,798 x IC x sigma_1d. N 2.400: 0,0508 / 0,0718 / 0,0688 -> 10,6 / 15,0 / 14,4 bp (sigma 262).
2. Kostendeckung: IC_min = c x tau / (0,798 x sigma); Vorzeichenwechsel-Rate AR(1): arccos(phi)/pi; Trefferquote
   p = 0,5 + arcsin(IC)/pi (IC 0,05 -> 0,516; p 0,55 entspraeche IC 0,156).
3. Tages-Querschnitt: Boden 1/sqrt(K-1); SD(IC_t) = Boden x 2,5 (Vermutung, GL-035); MDE80 = 2,4865 x SD/sqrt(N);
   L/S brutto = 3,51 x IC x sigma_xs_d mit sigma_xs_d = 9,85 %/sqrt(7) = 370 bp (Vermutung).
4. Ereignisstudien: MDE80 = 2,4865 x SD/sqrt(N) mit SD aus A2-Akte (Freitag 43,8 bp; Slot 12:30-14:00 ~74 bp) bzw.
   Vermutungen (Alt-Tagesvol 650/900 bp).
5. Selektionsdecke: E[max z] = (1-g) Phi^-1(1-1/K) + g Phi^-1(1-1/(K e)), g 0,5772: K 10 -> 1,575.
6. Gruppensequentiell: Brownsche Pfade (200.000), Grenzen c/sqrt(t_k) (O'Brien-Fleming-Form), c per Bisektion auf
   alpha 0,05 einseitig; K 4: c 1,733, alpha 0,0494, Power am Fixed-MDE 0,789, E[Info] H1 0,793, mit Futility
   (B(t) < 0 ab halber Information) E[Info] H0 0,717; Drift fuer Power 0,80: 2,529 -> Inflation 1,034. K 8: c 1,780,
   Inflation 1,040, E[Info] H1 0,752.
7. Zwei-Fenster-Regel: ein Fenster alpha 0,0025 hat z_krit 2,807, MDE-Faktor 3,649 auf N; C.10 je Fenster 2,4865 auf
   N/2 entspricht 3,516 auf N bei gemeinsamer Power 0,64 - bei gleicher Power 0,80 braucht C.10 +26 % (DEC-98 A-3).
8. Ausschlussgrenze: obere einseitige 95-%-Grenze bei beobachtetem IC 0 = 1,6449/sqrt(N): N 2.400 -> 0,034 (7,0 bp/Tag).
9. Vergleich Wochen-Querschnitt: IC 0,03 x 3,51 x 985 bp = 104 bp/Woche brutto gegen 18 bp Kosten (Faktor 5,8);
   Tages-TS IC 0,05 auf BTC: 73 bp/Woche brutto gegen 77 bp (7 Taker-RT) / 28 bp (Maker).

---

## Kurzfassung an den Orchestrator (12 Zeilen)

1. 3.0 ist als Pruefdisziplin realisiert, als Messinstitution nicht: null Effektschaetzer mit CI in 14 Monaten; alle sechs Gate-Eintraege sind GL-012 vor dem Lauf.
2. Bindender Engpass ist der Literatur-Punktprior (DEC-51 (2)): fehlt er, endet alles bei UNBELEGT; die Institution kann nur replizieren, nicht entdecken.
3. Fehlende Instrumente mit sofortiger Anwendbarkeit: Ausschlussgrenzen/CI als Pflichtausgabe, gemeinsames kalibriertes Marktmodell (digitaler Zwilling), OC-Simulation der Gate-Kette, Invarianten/Skalengesetze, Ereigniszeit; verfassungsrelevant: sequentielle Inferenz mit Alpha-Spending.
4. Tageshorizont ist nicht a priori tot (Kompendium D nur H-22, unterpowert): auf 2.000-2.400 Tagen ist IC 0,051-0,079 aufloesbar = 10,6-16,4 bp/Tag ~ Wand (Maker 4 / Taker 11 / 15); Kostendeckung IC 0,019-0,053 je Umschlag.
5. Tages-Querschnitt auf dem vollen Panel (2.130 Tage, K 300-600) loest IC 0,006-0,013 auf und hat einen Literatur-Prior (Ein-Tages-Reversal) - staerkstes neues Feld (F1).
6. Fenster-Politik: Einmal-Gut x Blind-Siegel x REZENZ x zwei starre Fenster = Kalenderuhr bis 2029-2031; Blind-Siegel sperrt alle Klassen fuer eine VRP, die vor 2029 nicht testbar ist.
7. Vorschlag Drei-Zonen-Regime (Exploration >36 M frei mit Konto / Validierung ein Blick / Konfirmation 12 M versiegelt, quartalsweise rollierend, gruppensequentiell): Lockerung an 3, Verschaerfung an 4 Stellen; OBF 4 Blicke: +3,4 % Max-Info, E[Info] 0,79 (H1) / 0,72 (H0 mit Futility).
8. Nutzer muss entscheiden: Jahres-Fehlerbudget, Zonenlaengen, Ersatz C.10/DEC-52, Behandlung der kontaminierten Fenster (W1/W2, A2-Vorperiode als Zone E), Prior-Verteilung statt Punktprior.
9. Zwoelf Felder tabelliert mit Dateninventar; sofort und regelkonform: F1 Tages-Reversal, F5 Delisting/Listing-Ereignisse; mit Prior-Entscheidung: F2 Funding-Dynamik, F4 Fluss-Aggregation, F6 Makro-Ereignisse; Data-Harvest: Inhaltsprobe deribit/publicTrade, OI-Historie aller Perps, Stablecoin-Angebot (frei).
10. Nicht-statistisch: Strenge-Ratsche ohne Gegenkraft (A2-Pilot c 24 -> 32 bp, Uebergabe 0,0001), Dokumentation ohne Obergrenze, Zustand als Prosa, Nutzer als einziger Literaturkanal bei gesperrtem Netz, Defaults stets strengste Option.
11. Orchestrator kann ohne Nutzer: Berichtszeile CI/Ausschlussgrenze, Konto-Inventar aller geoeffneten Statistik x Fenster, OC-Simulation als T0, Review-Mandat symmetrisch, Strenge-Quotient MDE80(alle Festlegungen)/MDE80(Grundfassung).
12. Was nicht folgt: kein Verdikt ueber irgendeinen Effekt, kein Siegelbruch, keine stille Regelaenderung; alle Power-Zahlen sind Aufloesungsgrenzen aus Akten-Nuisance mit markierten Annahmen.
