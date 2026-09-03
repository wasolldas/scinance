# REVIEW S1-S5 - Adversarischer Gate-Audit des Wissenschafts-Exkurses (Phase 3b)

**Rolle:** adversarischer Reviewer / Gate-Auditor, read-only.
**Stand:** 2026-09-03
**Geprueft:** `BRIEF_EXKURS.md`; `S1_SURVIVAL_EPIDEMIOLOGIE.md`, `S2_OEKOLOGIE_KRITISCHE_UEBERGAENGE.md`,
`S3_ASTROSTATISTIK.md`, `S4_NATUERLICHE_EXPERIMENTE.md`, `S5_AKTUAR_RUIN.md` (je vollstaendig).
**Gegen gelesen:** `survey/ERKENNTNIS_KOMPENDIUM.md` B/C/D/E (+F), `PRD_SCINANCE3.md` 3.2-3.3, 4.1,
4.3, 4.4, 5.1, 5.2, 9.1, 9.2, 9.3, `state/decisions.md` DEC-51..57,
`archive/v1_frameworks/edge-research-v3/results/CROSSDOMAIN_PARK.md`; zur Verifikation zusaetzlich
`scinance2-impl/state/gate_log.md` GL-026 (Zeilen 1141-1152).

**Vorbemerkung zum Massstab.** Ich pruefe nicht, ob eine Methode gut ist, sondern ob sie (a) etwas
misst, das im Programm nicht schon gemessen wird, (b) auf den bekannten N eine Chance hat, (c) auf
Belegen steht, die einen Cutoff tragen koennen, und (d) eine Entscheidung aendert, die ansonsten
anders fiele. Rechnungen habe ich nachgerechnet, wo Zahlen stehen; Rechenfehler sind markiert.
Die 16 Vorschlaege sind ueberdurchschnittlich diszipliniert - fast alle Power-Zeilen stimmen
arithmetisch. Der Angriffspunkt liegt fast nie in der Arithmetik, sondern in der
Entscheidungsrelevanz und im Belegstatus der tragenden Boersenmechanik.

---

## 0. Vorab: drei Feststellungen, die mehrere Urteile unten tragen

**F-1. Der 8h/1h-Ausschluss in A1 ist KEIN fixes Designmerkmal, sondern ein V-1-bedingter
Rueckfall.** PRD 5.1(b), woertlich: *"Der Zins-Term fuer 1h-Symbole ist UNBELEGT - V-1; solange er
offen ist, laeuft A1 nur auf der homogenen 8h-Klasse und weist die ausgeschlossene Symbolmenge
namentlich aus."* S1 (X-SURV-2) und S4 (X-NEXP-2) behandeln den Ausschluss beide als gesetzt und
bauen darauf ihre staerkste Warnung. Das ist die zentrale Ueberzeichnung des gesamten Exkurses:
klaert V-1 den Zins-Term, entfaellt der Ausschluss und mit ihm der Grossteil der behaupteten
Selektion. Uebrig bliebe nur die Normierungsfrage (`funding_n`), die das PRD bereits kennt.

**F-2. Die Bybit-Mechanik, auf der S4 (und der Selektions-Arm von S1) vollstaendig ruht, ist
durchgehend [sek] aus Suchtreffer-Snippets.** clamp-Grenze +/-0,05 %, `I = 0,01 %/8h`,
`Cap = min((IMR-MMR)*k, MMR)` mit `k = 0,75`, der automatische 8h->1h-Wechsel ab 2025-10-30 und die
Ausnahmeliste der acht Majors - kein einziger Primaerbeleg (Hosts egress-gesperrt, S4 sagt das
selbst offen). Die Knickpunkte P* = -0,04 % und P** = +0,06 % sind reine Ableitungen aus diesen
[sek]-Werten. Ein RDD/RKD, dessen Cutoff auf einem Suchtreffer steht, ist die C-14-Fehlerklasse
(importierte Schwelle) mit einem Zwischenschritt. Konsequenz: **kein X-NEXP-Vorschlag ist vor einer
erweiterten V-1 an der Primaerquelle registrierbar**; S4 fordert das selbst, es muss aber als
harte Vorbedingung stehen, nicht als Empfehlung.

**F-3. Kalendarische Lage schlaegt Methodik.** Die Gebuehrenaenderung (2026-09-01) liegt **nach**
allen urteilstragenden Fenstern (A1: bis 2026-06-30; A2: bis 2026-08-31). Der automatische
1h-Wechsel (2025-10-30/11-03) liegt **innerhalb** von A1s W2 und **vollstaendig ausserhalb** von
A1s W1. Beides hat niemand ausgerechnet; beides aendert die Konsequenzen der zwei zugehoerigen
Warnungen erheblich (Abschnitt 2).

---

## 1. Urteil je Vorschlag

Legende Urteil: **E** = AUFNEHMEN als Enabler/WP - **H** = AUFNEHMEN als Hypothesen-Kandidat -
**A** = NUR MIT AUFLAGE - **T** = TOT - **D** = DUPLIKAT.

| ID | Klasse laut Scout | Urteil | Der eine entscheidende Grund | Auflagen |
|---|---|---|---|---|
| **X-SURV-1** Delisting-Hazard/IPCW | X | **E** (Beifahrer WP-7, kein eigenes Paket) | WP-7 prueft die Zensierungsverzerrung heute nur binaer am synthetischen Fixture (PRD 4.1 T1-adversarial); eine Zahl auf Echtdaten ist ein echter Zuwachs zu <1 CPU-h und 0 Downloads. | (1) Zuerst `N_c` = Zahl distinkter Delisting-**Chargen** zaehlen; unter 32 nur deskriptiv (S1 fixiert das selbst korrekt vorab). (2) Die Ammann-et-al.-Zahlen (0,93 %/62,19 %, [sek], Host gesperrt) duerfen in **keine** Schwelle eingehen - Groessenordnungs-Anker, sonst L-1. (3) Schoenfelds `d` sind **Ereignisse**, nicht Cluster; die Gleichsetzung mit Delisting-Tagen ist konservativ und muss als solche etikettiert werden. |
| **X-SURV-2 (X-Arm)** Intervallwechsel als endogene Selektion | X | **E**, aber **nur als Zaehl-Vorfrage**, verschmolzen mit S4 (s. Abschnitt 3) | Die Frage "wie viele Symbol-Wochen des obersten Dezils entfernt der Ausschluss?" kostet Minuten und ist eine A1-Feasibility-Zahl; das volle Multi-State-/IPCW-Geruest ist dafuer unverhaeltnismaessig. | (1) F-1 zuerst: bei geklaertem `I` entfaellt der Ausschluss und damit der Anlass. (2) Vorzeichen der Verzerrung ist **nicht** bestimmt (s. 2.i). (3) Reweighting erst nach der Zaehlung und nur bei vorab fixierter Materialitaet. |
| **X-SURV-2 (R-Arm)** Dauerabhaengigkeit der Funding-Regime | R | **A** | Detektierbar ist HR 1,32 je SD auf 104 Wochen-Clustern (nachgerechnet: `sqrt(7,849/104) = 0,2747`, korrekt) - aber ein PASS bindet A1 nicht: A1s Halteperiode ist mit einer Woche registriert und nicht frei. | Eigene Registrierung mit eigenem K; die Behauptung "A1s Halteperiode haengt an der gemessenen Regimedauer" ist zu streichen - sie wuerde nach einem Lauf eine Designgroesse bewegen (Torpfosten). |
| **X-SURV-3** Time-to-Fill als Competing Risk | X | **E** als **Schaetzer-Spezifikation in WP-10(B)**, kein eigenes Paket | WP-10(B) verlangt woertlich, dass "die Messung den zweiten Fall trennt" (PRD 4.3 T1-adversarial), nennt aber keinen Schaetzer, der das kann; das Verhaeltnis kann es prinzipiell nicht. Nulleffekt exakt hergeleitet und nachgerechnet (0,4323 vs. 0,6321, Faktor 1,46; Grenzfall 2,00 - beide korrekt). | (1) **Der Konkurrenzausgang "adverse Bewegung" ist keine Naturkonstante, sondern eine Cancel-/Repricing-Politik** - ohne vorregistrierte Politik ist die CIF nicht identifiziert. (2) Die Behauptung "nur die CIF ist unverzerrt" ist **falsch**: die CIF korrigiert das Konkurrenzrisiko, **nicht** die L2-Luecken; Aufzeichnungsluecken korrelieren plausibel mit Last/Stress, also potenziell informativ - dafuer braucht es eine eigene Sensitivitaet oder IPCW. (3) Registrierung des Schaetzerwechsels **vor** dem Lauf (S1 sieht das korrekt, C.3). |
| **X-SURV-4** Case-Crossover / Referenzwahl-Bias | X | **D** (Teile a+b) / **T** (Teil c) | Teile (a)+(b) sind keine neue Idee, sondern die bereits geltende Pflicht: C.4 und L-2 verlangen, dass der Nulleffekt **am Null-Fixture gemessen** und nicht angenommen wird; PRD 3.3.5/5.2 schreiben die Placebo-Maschinerie vor. Der Vorschlag deckt eine Lueckenbehauptung auf, die faktisch eine Nichtbefolgung waere. | Umsetzen als **Auflage im A2-Registrierungstext** ("Erwartungswert des Placebo-Schemas wird berichtet, nicht auf 0 gesetzt"), nicht als Paket. Teil (c) ist vom Scout selbst als kaum wirksam ausgewiesen. |
| **X-OEKO-1 Arm (a)** Relaxationsrate nach Schockstunden | X | **E** - Top-5 | Einziger Vorschlag mit **primaer verifiziertem** grossem N: GL-026 (gate_log Z. 1143/1152) weist 403/362 Ereignistage und 1.044/962 Ereignisse aus, Laufzeit 95 s. Kein neuer Parameter (Ereignis-Definition aus H-20 geerbt), kein Download, Arm (a) kann nicht wertlos enden. | (1) D.12-Konformitaet ist gegeben (keine Sigma-/Horizont-/Luecken-Variation), muss aber im Registrierungstext ausdruecklich behauptet und gepinnt werden. (2) `T_half` ist Deskriptor, nie Gate. (3) Die Bindung an die 24-h-Kill-Regel aus R3-K-34 ist Bericht, keine Herleitung einer Schwelle. |
| **X-OEKO-1 Arm (b)** Resilienz als Zustandsvariable | R | **A** | Detektierbares Varianzverhaeltnis 1,20 (nachgerechnet: `sqrt(2/361) = 0,0744`, `2,4865*0,0744 = 0,185`, `e^0,185 = 1,203` - korrekt), aber die Effektgroesse ist **UNBELEGT**, einziger Fachbeleg N=7 [sek]. | (1) `SE(ln Var)` unterstellt annaehernde Normalitaet der `lambda`-Schaetzer; Exponentialfits liefern schwere Raender - die 1,20 ist optimistisch und muss am Fixture nachgemessen werden. (2) Eigene Registrierung, Ueber-Familie mit jedem spaeteren R-Kandidaten aus X-OEKO-3 vorab. |
| **X-OEKO-2** Anytime-valid / e-Werte | X | **A**, nicht in Welle 1 | **Der Hauptnutzen ist bereits geliefert:** L-17 (Stouffer/Fisher nur als Evidenz-Obergrenze) ist ein reines 2.0-Artefakt, weil die Roh-Serien fehlten - **DEC-53 schliesst genau das fuer jeden 3.0-Lauf**, der gepoolte fenster-geclusterte Bootstrap ist damit kuenftig nachrechenbar. Bleibt der Preis: Faktor 2,43-3,27 in N (Schranken nachgerechnet: 3,656/3,082/3,036/3,062 - alle vier korrekt) fuer die N-aermsten Fragen des Programms. | (1) Zweitdesign neben DEC-52 ist ein Governance-Risiko: zwei Designs erlauben Wahl nach dem Sehen - falls ueberhaupt, dann eine DEC mit strikter Vorab-Zuordnungsregel je Hypothese. (2) Der Retro-Nutzen ist per C.1 ausgeschlossen (Scout sieht das korrekt). |
| **X-OEKO-3** EWS-Nulleffekt-Zensus | X | **A** | Der `n_eff = T/w`-Befund ist der wertvollste Teil und ist bereits **ohne Lauf** verfuegbar (Tabelle nachgerechnet: 2 / 4,7 / 9,4 / 23,5 - korrekt; die kritischen Kendall-tau bei n=23,5 sind mit ~0,29 eher zu hoch angesetzt, ~0,25 waere praezise - konservativ, unschaedlich). Der 120-Varianten-Lauf ist demgegenueber teuer und traegt die K-Inflation des Exkurses. | (1) **Streichen: "genau einer ausserhalb -> er allein wird Kandidat".** Ein Null-Zensus darf niemals einen Kandidaten promoten - genau so entstehen H-11-Wiedergaenger. Zulaessige Ausgaenge: D-Eintrag oder "nicht ausgeschlossen". (2) Surrogat-Maschinerie mit X-ASTRO-3 teilen (ein Modul, nicht zwei). |
| **X-OEKO-4** Change-Point als REZENZ-Operationalisierung | X/R | **E, nur verschmolzen mit X-ASTRO-1** | Die REZENZ-Klausel wird heute per Kalenderkonvention gesetzt (C.18/L-16); eine Fenster-Schnitt-Regel mit gemessener Langgedaechtnis-Null ist ein echter Zuwachs. `delta_det`-Rechnung korrekt (0,371 sigma bei m=90; 1,015 bei m=12). | (1) **Darf bereits fixierte Fenster (A1 W1/W2, A2 W1/W2) nicht rueckwirkend bewegen** - sonst ist die Regel eine Torpfosten-Maschine. Gilt nur fuer kuenftige Registrierungen. (2) Eigene DEC vor dem ersten Kandidaten, der sie nutzt (Sequenz-Zwang). (3) Anti-Snooping-Klausel des Scouts (Partition nie auf der Testreihe) ist bindend zu uebernehmen. |
| **X-ASTRO-1** Bayesian Blocks | X/R | **D** zu X-OEKO-4 in der Segmentierungsfrage; Restwert = dritter Detektor | Der Alleinstellungsanspruch "liefert die **gemessene Cluster-Einheit** fuer DEC-51 Punkt 3" ist ein **Kategorienfehler**: DEC-51 Punkt 3 fragt nach der Einheit, innerhalb derer Beobachtungen **gemeinsame Schocks** teilen (Querschnitts-/Serienabhaengigkeit), nicht nach einer zeitlichen Regime-Zerlegung; die Blocklaenge liefert der stationaere Bootstrap (Politis/White, R4-Kanon), `rho(BTC,ETH)` misst WP-7 ohnehin (PRD 4.1, Datenquellen-Absatz). | Aufgehen in dem einen Change-Point-Paket als Detektor 3 mit `p0`-Etikett; `ncp_prior`-Formel korrekt nachgerechnet (6,332 bei N=2008; 5,850 bei N=730) und uebernehmbar. |
| **X-ASTRO-2 (analytischer Teil)** Formretention von `r_pre` | E-Enabler/X | **E** - Top-5, als Nachtrag zu PRD 5.2 / V-5 | Eine Stunde, kein Datenlauf, und sie beruehrt A2s **einzige** urteilstragende Statistik. Skalarprodukt-Rechnung korrekt (`0,5/(1/sqrt3) = 0,866`, 13,4 % SNR-Verlust). | Die Formulierung "garantiertes Nullurteil" ist zu streichen (s. 2.ii) - der Verlust tritt nur bei **innenliegendem** Wendepunkt ein, und PRD 5.2 registriert `r_pre` gerade **negativ**, unterstellt also den Wendepunkt am Fensterrand. |
| **X-ASTRO-2 (Messteil)** Matched-Filter-Bank auf dem Aktivitaetskanal | E-Enabler/X | **A**, nach V-5 | Der Aktivitaetskanal ist tatsaechlich guenstiger als A2s Renditekanal (SE-Rechnungen korrekt: 0,718/0,647/0,345/0,311), aber die Ereignis-zu-Ereignis-SD des SNR ist **UNGEMESSEN** - ohne sie ist die Power-Zeile nicht ausfuellbar und die Registrierung nach 3.3.1 unzulaessig. | (1) K = 3 vorregistriert (Scout tut das - gut). (2) **Formwahl darf nicht auf denselben Ereignissen erfolgen, auf denen spaeter der Renditetest laeuft** (C.17 Entdeckungszelle); zulaessig ist die Aera-Profil-Menge vor 2024. (3) chi^2-Veto ist Pflichtbestandteil, sonst misst man "an Verfallstagen ist mehr los". |
| **X-ASTRO-3** LS/Z^2_n-Periodizitaets-Inventar | X/R | **A** | Beste Power im Feld (Trials-Rechnung korrekt: M = 358, `z = ln(7160) = 8,876` gegen naiv 3,00, Faktor 2,96; SE-Tabelle durchgehend korrekt) - aber der naechste Nachbar ist mit H-03/C-31 ein **D.4-Eintrag mit Surrogat-p ~ 1,0**, und der Scout zitiert das selbst als staerkstes Gegenargument. | (1) Positivkontrolle (8h-Funding-Linie) muss **zuerst und allein** bestehen (C.13/3.3.8); ohne sie ist jeder Nullbefund uninformativ. (2) Vollband-Scan ausdruecklich nicht urteilstragend, Deflation nach X-ASTRO-4 Pflicht. (3) Der Liquidations-Arm ist auf ~33 Tagen/Fenster (detektierbar 43 % Leistungsueberschuss) ein GL-012-Fall - nur die 8h-Linie darf dort ueberhaupt berichtet werden. |
| **X-ASTRO-4** Upcrossing-Trials-Faktor (Gross/Vitells) | X | **A** (bedingt bauen) | Rechnung korrekt (`p_global = 0,0563`, Trials 41,7) und die Lueckenbehauptung stimmt: BH/FDR deckt keine Kontinua, Bailey/LdP beantwortet eine andere Frage. Aber PRD 3.0 verbietet Scans weitgehend (5.2 "kein Fenster-Scan") - ein Modul ohne Anwendungsfall ist Infrastruktur vor Bedarf. | Erst bauen, wenn eine Registrierung tatsaechlich einen kontinuierlichen Parameter durchsucht; bis dahin als Methodennotiz in `stats3`-Doku. Die Erreichbarkeitspruefung (QQ gegen 100.000 Toys) ist bindend. |
| **X-NEXP-1 (Totzonen-Zensus)** Anteil `F == I` exakt | R/X | **E** - **Top-1** | Liegt ein grosser Teil des Querschnitts mechanisch auf **demselben** Wert `0,01 %`, ist A1s Dezil-Sortierung ueber weite Teile **degeneriert** und das effektive K bricht ein - eine GL-012-relevante A1-Feasibility-Zahl, die im gesamten PRD nicht vorkommt. Die Totzone ist 10 bp breit in P; fuer ruhige Alt-Perps ist die Bindung der Normalfall. | (1) **Erste Messung auf den bereits vorhandenen 113 Tagen `bybit/rest.fundingRate` (F.1) - kein Backfill noetig**; danach auf dem A1-Backfill wiederholen. (2) Ergebnis als Feasibility-Zeile in A1 aufnehmen, mit vorab fixierter Konsequenz (Bindungsanteil ueber X -> Sortierung auf den ungebundenen Teil oder GL-012). |
| **X-NEXP-1 (RKD selbst)** Knick an der Funding-Klemme | R/X | **A** | Die Identifikation ist elegant, aber sie steht auf drei ungeloesten Punkten gleichzeitig: [sek]-Cutoffs (F-2), **UNBELEGTE** Historientiefe von `premium-index-price-kline` (V-S4-1), und - vom Scout unterschaetzt - **Messfehler in der Laufvariablen**: gerechnet wird mit dem 1h-Praemien-Index als Naeherung an Bybits Minuten-TWAP. Messfehler in der Laufvariablen verschmiert einen Knick systematisch; das ist kein Berichtsposten, sondern ein potenzieller struktureller Kill. | (1) Vorab fixierte Kill-Regel: uebersteigt die gemessene SD des Approximationsfehlers einen benannten Bruchteil der Bandbreite, keine Registrierung. (2) V-1-Erweiterung an der Primaerquelle **vor** allem anderen. (3) Ganong/Jaeger-Permutation ist bindend (Scout fordert das selbst korrekt). (4) `N_eff`-Tabelle enthaelt einen **Rechenfehler**: bei `N_c = 365, rho = 0,02` ist `365/(1+364*0,02) = 44,08`, nicht 44,4 (folgenlos fuer die Aussage). |
| **X-NEXP-2** Diff-in-Disc an der Funding-Kappe | E/R | **A** | Sauberste Identifikation des Feldes und mit dem Vor-Reform-RDD ein gratis empirischer Nulleffekt - aber `N_cluster` ist **UNGEMESSEN** (V-S4-2), das Treatment ist **[sek]**, und die Behandlung ist **nicht absorbierend**: die Rueckkehr auf laengere Intervalle erfolgt laut derselben Quelle "ohne Vorankuendigung", also diskretionaer, mitten im 24h-7d-Ergebnisfenster. | (1) Zaehlung zuerst (verschmolzen, s. Abschnitt 3); `N_eff < 20` -> GL-012 (Scout fixiert das korrekt vorab, keine Absenkung). (2) Zensierung am Rueckwechsel vorab registrieren. (3) Die Positivkontrolle (realisierte Carry MUSS springen) ist Pflicht und richtig gewaehlt. |
| **X-NEXP-3 Arm 1** Gestaffelte DiD, Cross-Venue-Kontrolle | E | **A**, niedrigste Prioritaet | Braucht einen **Binance-Backfill ausserhalb der PRD-7.1-Tabelle** (Scout markiert das ehrlich als Orchestrator-Entscheidung), eine neue Schaetzerfamilie (Callaway/Sant'Anna, Kolari/Pynnoenen, Rambachan/Roth) und beantwortet keine Vorbedingung eines Welle-1-Kandidaten. Das ist die D.16-Signatur. | Nur nach WP-7 und nur mit eigener DEC zum 7.1-Scope; Kontrollebenen (i)+(ii) reichen fuer eine Vorprobe ohne Backfill. |
| **X-NEXP-3 Arm 2** Risk-Limit-Batches | E | **T** (historisch) | Der Arm braucht das taegliche Point-in-Time-Instrument-Roster - genau den Strom, den PRD 7.2 als "grundsaetzlich nicht nachholbar" fuehrt und der noch nicht gesammelt wird. Ohne ihn bleibt Ankuendigungs-Scraping, das PRD 4.1 (B3) ausdruecklich aus Welle 1 ausschliesst. | Nur als Argument fuer den Recording-Start des Rosters verwertbar, nicht als Analysevorschlag. |
| **X-NEXP-4** IV Verfallstakt -> Fluss -> lambda | X | **A**, an V-5(a) gebunden | Der Scout fixiert die Kill-Regel selbst korrekt vorab (`N_cluster = 12 < 20` ohne woechentliche Verfaelle -> GL-012, kein Ausweichen auf gepoolte 24). Bleibt: die Exklusionsrestriktion folgt aus keiner Boersenregel (Scout etikettiert ehrlich "spekulativ"), und das Ergebnis ist eine **Kostenkonstante** - nach C.2 Etikett, nie Gate. | (1) Erst nach V-5(a). (2) `lambda_2SLS` darf keine PASS-Bedingung irgendwo tragen. (3) Anderson-Rubin statt t; Loud-Fail bei schwachem Instrument (Scout spezifiziert das korrekt). |
| **X-AKT-1** Praemienprinzipien / TPR | X | **T** als eigenes Paket | Der Scout weist selbst nach, dass drei Viertel der Methode unter Normalitaet auf den Sharpe kollabieren und dessen Untestbarkeit erben (K-0.2), und dass der neue Teil an 6-10 Stress-Episoden mit weit offenem CI haengt (`SE(z) = 0,474`, PRD 4.3). Ein Mass, dessen CI vorab als "weitgehend offen" bekannt ist, aendert keine Entscheidung. | Restwert: `TPR` und `alpha_implizit/R` als **optionale Berichtszeile** innerhalb von X-AKT-2, ohne eigenes Paket und ohne Personentage. |
| **X-AKT-2 (MaxDD-Korrektur)** Ruin-Kapital statt driftlosem Boden | X | **E** - als Konstanten-Nachtrag zu PRD 3.6 | Der Befund ist ohne jeden Lauf verfuegbar und korrekt: `E[MaxDD] = 1,2533*sigma_ann*sqrt(T)` ignoriert `mu` vollstaendig und waechst mit `sqrt(T)`. Tabelle vollstaendig nachgerechnet (R = 66,6/37,0/18,5/9,25; u(1 %) = 6,9/12,5/24,9/49,8 %; E[MaxDD] = 21,0 %) - **fehlerfrei**. Die Rangumkehr ist real. | `R`, `psi`, `u(eps)` sind **Bericht, nie Gate** (Scout fixiert das korrekt; sonst waere es ein Sharpe-Gate mit Extraschritt). Aufnahme als Fussnote in 3.6, nicht als Paket. |
| **X-AKT-2 (xi-Arm)** leicht/schwer-Verdikt | X | **A** mit vorab fixiertem "nicht entscheidbar" | Die eigene Power-Rechnung ist vorbildlich und toetet den Arm: Power 0,13 (Woche) bzw. 0,49 (Tag) gegen 0,80; `k ~ 465` Exzedenzen entspraechen 23 % Exzedenzrate, wo die GPD-Asymptotik nicht mehr traegt. Nachgerechnet: `SE = 0,284/0,092`, Crossover `xi = 0,150` - alles korrekt. | Nur als Intervall mit Schwellen-Sensitivitaetskurve berichten; als registrierte Frage waere es ein GL-012-Fall. |
| **X-AKT-3 Stufe 1** Insurance Fund als Ruin-Prozess | R/X | **A**; die Vorfrage V-AKT-1 selbst = **E** | **V-AKT-1 ist kein neuer Vorschlag, sondern eine bereits geschuldete Pflicht**: PRD 3.3.7 verlangt vor jeder daten-gated-Sperre eine dokumentierte Probe auf oeffentliche Nachladbarkeit - fuer `bybit/insurance` (43 Tage, F.1) ist sie nie erfolgt. Zehn Minuten, unabhaengig vom Ruin-Modell. | Zum Modell: die Zielzeile 3.3.9(c) ist ein **Etikett** (Abschlag 10-20 % des Erwartungswerts bei 1 %/a); ein modellabhaengiges Intervall, das plausibel 0,1 %-5 % umspannt, aendert keine Entscheidung. Zulaessig nur als benanntes Intervall mit Modellfamilien-Sensitivitaet, nie als Punktzahl (Scout fordert das selbst). |
| **X-AKT-3 Stufe 2** Chain-Ladder auf `allLiquidation` | X | **T** (vertagt, vom Scout selbst) | ~66 Tage gegen H-21s reservierte 2x90-Tage-Fenster; identische N-Falle wie H-10/H-13. | - |
| **X-AKT-4 (L2)** Herleitung des 0,30-Design-Parameters | X | **E** - als Beifahrer in WP-7 | Die Aequivalenz ist korrekt hergeleitet und nachgerechnet: `z = w/(w+k) >= 0,30 <=> k <= 2,333*w`, bei `w = 9..21` also `k <= 21..49`. Aus einem gesetzten Skalar (PRD 5.1 Kill-4) wird eine pruefbare Aussage - genau das, was C.12/L-1 verlangen. | Die Aequivalenz "Reliabilitaet ~ Autokorrelation" gilt fuer die **Zeitreihen**-Autokorrelation je Symbol; PRD 5.1 Kill-4 sagt nur "Autokorrelation des Funding-Sortierschluessels ueber eine Woche". Vor der Uebernahme ist festzulegen, welchen Schaetzer WP-7 baut - sonst wird eine Herleitung an die falsche Groesse geheftet. |
| **X-AKT-4 (L1/L3)** Credibility-Zerlegung `a` vs. `s^2` | X | **A**, mit hoher Erwartung eines Leerbefunds | Der Scout benennt die Obergrenze selbst (bei gleichen `w_i` ist Schrumpfung affin und laesst den Rank-IC exakt unveraendert) - und uebersieht dann, dass genau das hier eintritt: WP-7 laesst ein Symbol erst ab **>= 8 Wochen** Bars zu (PRD 4.1 DoD (4)), womit jedes zugelassene Symbol den vollen 3-7-Tage-Lookback hat; in der **homogenen 8h-Klasse** (F-1) ist `w_i` damit praktisch konstant. Der Enabler laeuft leer, bevor er gebaut ist. | Zuerst die Verteilung von `w_i` messen (Minuten). Ist sie degeneriert, entfaellt L1/L3 ersatzlos und nur L2 bleibt. |

**Zaehlung.** 8x AUFNEHMEN als Enabler (davon 5 als Beifahrer/Nachtrag ohne eigenes Paket),
0x AUFNEHMEN als Hypothesen-Kandidat, 13x NUR MIT AUFLAGE, 4x TOT, 2x DUPLIKAT.
Bemerkenswert: **kein einziger Vorschlag ist ein Hypothesen-Kandidat.** Das ist kein Mangel der
Scouts, sondern die korrekte Antwort auf Randbedingung 4 des Briefs - es sollte aber nicht als
Ertrag verbucht werden. Der Exkurs hat null Alpha-Kandidaten erzeugt und war auch nicht dazu da.

---

## 2. Die drei programmweiten Warnungen

### 2.i S1+S4: der automatische 8h->1h-Wechsel als endogene Zensierung auf A1s Sortierschluessel

**Der Mechanismus ist korrekt beschrieben, die Warnung ist in vier Punkten zu korrigieren.**

*Richtig:* Wenn ein Symbol bei Cap-Treffer automatisch auf 1h-Abrechnung wechselt und A1 die
1h-Klasse ausschliesst, dann korreliert der Ausschluss mit dem Sortierschluessel selbst. Das ist
definitionsgemaess informative Selektion und nicht exogen. Beide Scouts sehen das unabhaengig
voneinander, S4 mit der schaerferen Formulierung ("durch A1s Sortierung selbst ausgeloest").

*Korrektur 1 - der Ausschluss ist bedingt.* F-1: PRD 5.1(b) macht den Ausschluss ausdruecklich
vom offenen Zins-Term `I` fuer 1h-Symbole abhaengig, also von **V-1**. Klaert V-1, dass `I`
identisch ist, laufen 1h-Symbole intervall-normiert mit und die Selektion verschwindet weitgehend.
Beide Scouts behandeln den Ausschluss als gesetzt und ueberzeichnen die Folge dadurch erheblich.

*Korrektur 2 - die Datierung schlaegt die Methodik.* Der automatische Wechsel existiert laut
[sek]-Quellen erst ab 2025-10-30 (Vollausrollung 2025-11-03). A1s Fenster sind
W1 = 2024-07-01..2025-06-30 und W2 = 2025-07-01..2026-06-30. Also: **W1 ist vollstaendig
vor-mechanisch, W2 zu rund zwei Dritteln nach-mechanisch.** Damit ist das Problem kein globaler
A1-Bias, sondern eine **Fenster-Inhomogenitaet zwischen W1 und W2** - und die trifft direkt auf
C.10 (hartes Ein-Fenster-Kriterium): eine Diskrepanz zwischen W1 und W2 koennte kuenftig als
Regime-Instabilitaet gelesen werden, obwohl sie eine Regelaenderung des Betreibers ist. Diese
Konsequenz zieht **keiner der beiden Scouts**, obwohl S4 fuer das eigene X-NEXP-2 exakt deshalb
W2a/W2b definiert. Sie ist die praktisch wichtigste Folge der ganzen Warnung.

*Korrektur 3 - das Vorzeichen des Bias ist nicht bestimmt.* Beide Scouts argumentieren, der
Ausschluss "entfernt die Traeger der Praemie". Das gilt fuer das **Funding-Bein**. A1s
urteilstragende Groesse ist aber nach PRD 5.1(c) ausdruecklich die **SUMME aus Funding-Akkumulation
und Preisbein**, und die Cap-Treffer-Symbole sind Squeeze-Zustaende, deren Preisbein auf der
Short-Seite plausibel stark negativ ist. Es ist damit a priori offen, ob der Ausschluss die
gemessene Gesamtrendite nach oben oder unten verzerrt. Die Behauptung "A1 ist ohne IPCW nicht
registrierbar" (S1) ist in dieser Schaerfe nicht gedeckt.

*Korrektur 4 - Verhaeltnismaessigkeit.* Der Cap liegt bei typischen Tier-Werten um 0,375 %/8h,
also ~1,275 %/Tag Praemie (S4s eigene Rechnung, nachgerechnet und korrekt). Das sind ausgepraegte
Squeeze-Zustaende. Der betroffene Anteil der obersten Dezil-Symbolwochen ist plausibel klein - aber
**UNGEMESSEN**. Ein Multi-State-/Fine-Gray-/IPCW-Geruest zu bauen, bevor diese Zahl existiert, ist
selbst ein D.16-Fall.

**Was A1 (PRD 5.1) deshalb aendern muss - vier Punkte, in dieser Reihenfolge:**
1. **V-1 erweitern und zuerst beantworten** (Zins-Term je Kontraktklasse, clamp-Grenze, Cap-Formel
   `k`, Ausnahmeliste, Auto-Switch-Regel) - an der Primaerquelle, Nutzer-Maschine. Ohne das ist die
   Frage nicht einmal gestellt.
2. **Zaehl-Vorfrage** (Minuten, auf dem ohnehin geplanten Backfill; erste Naeherung sogar auf den
   113 vorhandenen Harvest-Tagen): Zahl der Intervallwechsel je Kalendertag, davon Anteil in den
   obersten/untersten Dezilen, Anteil betroffener Symbol-Wochen je Fenster. Mit vorab fixierter
   Materialitaetsgrenze.
3. **A1-Registrierungstext:** (a) der Ausschluss wird als **look-ahead-freie Symbol-Wochen-Regel**
   formuliert (nie "Symbole, die je 1h hatten"); (b) die ausgeschlossene Menge wird je Woche und
   Dezil ausgewiesen - dafuer braucht `panel_1d` neben `funding_n` eine Intervallklassen-Spalte;
   (c) eine **Pflicht-Sensitivitaet** "mit intervall-normiert eingeschlossenen 1h-Symbolen" wird
   berichtet, nicht als zweites Gate (K bleibt 3).
4. **Fenster-Inhomogenitaet schriftlich vorab feststellen** (PRD 9.3 Punkt 6): W1 vor-, W2
   ueberwiegend nach-Reform; eine W1/W2-Divergenz ist damit nicht automatisch als Regime-Befund
   lesbar. Das ist eine Zeile, kostet nichts, und verhindert eine Fehlinterpretation nach dem Lauf.

IPCW-Gewichtung: erst wenn Punkt 2 Materialitaet zeigt - und dann als **vorab registrierte**
Schaetzeraenderung, nie danach (C.3).

### 2.ii S3: `r_pre` ist der Matched Filter fuer eine Stufe, nicht fuer die V-Umkehr

**Die Geometrie stimmt. Die Schlussfolgerung "garantiertes Nullurteil" stimmt nicht.**

*Geometrie, nachgerechnet.* `r_pre = log p(08:00) - log p(07:30)` ist als Filter auf der
Minuten-Renditereihe der Gewichtsvektor "alles Einsen", also der Matched Filter fuer eine
konstante Drift in den Renditen (= eine lineare Rampe im Preis). Gegen eine Rampe verliert ein
Rechteck `1 - 0,866 = 13,4 %` SNR (Skalarprodukt korrekt). Und ja: eine **symmetrische V-Umkehr mit
Wendepunkt streng innerhalb** des Fensters, die auf das Ausgangsniveau zurueckkehrt, annulliert
`r_pre` exakt. Das ist richtig und steht in keinem Programmdokument.

*Warum daraus kein garantiertes Nullurteil folgt.* PRD 5.2 registriert die Richtung von `r_pre`
ausdruecklich **negativ** ("die Literatur beschreibt eine V-foermige Umkehr; das Vorzeichen von
`r_pre` ist damit negativ zu registrieren"). Das Programm liest die V also mit dem Wendepunkt am
**Fensterrand 08:00** - was mechanisch die naheliegende Lage ist: der Settlement-TWAP endet um
08:00, der Hedgebedarf faellt dort auf null. Unter dieser Lesart ist `r_pre` nahezu optimal, nicht
formblind. S3s Fall tritt nur ein, wenn der Wendepunkt **innerhalb** von `[07:30, 08:00)` liegt.
Das ist eine Sensitivitaet, kein Kill.

*Was den Punkt trotzdem tragfaehig macht.* Die Zeitgeometrie der Umkehr ist **nirgends belegt**.
Die tragende Quelle ist "Finance Research Letters, Juni 2026", und R3 vermerkt woertlich: Autoren
nicht ermittelbar, Volltext gesperrt. Damit steht A2s **Richtungsregistrierung** - eine
Pflichtangabe nach DEC-51 Punkt 1 - auf demselben unbelegten Fundament wie die Effektgroesse.
A2 ist ohnehin bis V-5 ein GL-012-Fall (PRD 5.2, woertlich); die Formfrage ist ein **zweiter,
unabhaengiger** Grund, V-5 zu erweitern.

**Entscheidung:**
- **V-5 bekommt eine Teilfrage (c):** Nennt die Primaerquelle die Zeitlage der Umkehr relativ zu
  08:00 UTC? Vorab fixierte Konsequenz: ohne Beleg wird A2s Richtung nicht registrierbar - und
  damit A2 insgesamt nicht, was den bestehenden GL-012-Status nur bestaetigt.
- **Die analytische Formretentions-Rechnung wird als Nachtrag in PRD 5.2 aufgenommen** (eine
  Stunde, kein Lauf) - sie ist die billigste Zeile des gesamten Exkurses.
- **Kein Ersatz von `r_pre` durch einen Filter nach dem Sehen von Daten.** Ein Formwechsel nach
  einer Messung auf denselben Ereignissen ist Torpfostenverschiebung; wird die Form gemessen, dann
  auf der Aera-Profil-Menge vor 2024 und mit vorregistriertem K.
- Der Messteil von X-ASTRO-2 (Aktivitaetskanal) ist als **Mechanismus-Vorpruefung** zulaessig,
  aber erst nach V-5 und mit der UNGEMESSENEN Ereignis-SD als Vorbedingung (3.3.1).

### 2.iii S4: Bybit-Gebuehrenaenderung 2026-09-01 (Altcoin-Maker 0 % ueber Pro-Stufen, [sek])

**Beruehrte Konstanten - wenn der [sek]-Snippet zutrifft:**

| Konstante | Beruehrt? | Wirkung |
|---|---|---|
| **B.3 / DEC-42** `FEE_MAKER` 2,0 bp, `FEE_TAKER` 5,5 bp | **ja, potenziell** | Gilt fuer die Altcoin-Gruppe - exakt das Universum, in dem A1 und A3 handeln wuerden. |
| **B.1** Friktionswand 11 bp Taker / ~15 bp inkl. Slippage | ja, mittelbar | 11 bp = 2 x 5,5 bp; sinkt der Taker fuer Altcoins, sinkt die Wand fuer genau die Klasse-W-/P-Kandidaten. |
| **K-0.1** Horizont-Friktions-Kurve | ja, mittelbar | Rechnet gegen 11 bp (Taker) und 4 bp (Maker RT). Bei Maker 0 % waere der Maker-Ast der Kurve gegenstandslos. |
| **WP-10(B)** `adv_sel_max = (FEE_TAKER - FEE_MAKER)/2 = 1,75 bp` | **ja, direkt** | Bei `FEE_MAKER = 0` waere der Maker-Vorteil 5,5 statt 3,5 bp, also `adv_sel_max = 2,75 bp` - **+57 %**. Das ist die konkreteste Folge und steht in keinem Dokument. |
| **A1-Etikett** 18 bps Wochenkosten / 36 bps Mindestmagnitude; **A3** `sigma_xs_min = 342 bps/Woche` | ja | Reine Etikettgroessen (C.2), aber sie wuerden sich verschieben. |
| **DEC-45 / B.4-B.7** Options-Gebuehren auf den Index | **nach Beleglage nein** | Der Snippet betrifft Derivate-/Perp-Stufen, nicht die Optionskarte. **Aber: "nicht erwaehnt" ist kein Status.** Bleibt [sek]/UNBELEGT und gehoert in die V-4-Pruefung. |

**Drei Feststellungen, die die Sache entschaerfen - keine davon steht bei S4:**
1. **Kein urteilstragendes Fenster ist betroffen.** Wirksam 2026-09-01; A1s Fenster enden
   2026-06-30, A2s W2 endet 2026-08-31. Die Aenderung beruehrt **keine Messung**, nur die
   vorwaertsgerichtete Tradability-Etikettierung.
2. **Laut demselben Snippet bleibt VIP-Retail unveraendert** und die Aenderung betrifft
   "Pro levels". Der Einzelbetreiber ist damit vermutlich unberuehrt - und der Einzelbetreiber ist
   die Kostenbasis, die `tradability3` abbilden muss. "Vermutlich" ist unter der Belegregel aber
   kein Status.
3. **C.2 bleibt unangetastet.** Gebuehren sind Etikett, nie Gate. Kein Gate, keine Schwelle und
   kein Verdikt aendert sich durch diese Meldung - was sich aendert, ist die Pflicht, die
   Konstante zu verifizieren.

**Erforderliche Handlung:** eine Konstanten-Pruefung in V-4-Nachbarschaft an der Primaerquelle auf
der Nutzer-Maschine (Minuten). Bis zum Ergebnis gilt 3.3.6: **ungemessene Konstanten RAISEN** -
`tradability3` darf 2,0/5,5 bp nicht still weiterverwenden, wenn ihr Status strittig ist. S4s
zweiter Hinweis (eine echte ex-ante-Vorregistrierung auf die Nachperiode, "jetzt oder nie") ist
methodisch reizvoll, aber ein DiD auf einer Gebuehrenaenderung mit `N_cluster = 1` und
unbeobachtbarer Behandlungsintensitaet ist genau das, was der Scout selbst ablehnt - kein
Registrierungsgrund.

---

## 3. Ueberschneidungen zwischen den Scouts

**(1) S1 X-SURV-2 (X-Arm) + S4 X-NEXP-2 - VEREINEN im Zaehl-Teil, TRENNEN im Analyse-Teil.**
Beide sitzen auf demselben Ereignis (8h->1h-Wechsel bei Cap-Treffer) und beide brauchen als erstes
dieselbe Zahl: wie oft, wann, welche Symbole, welches Dezil. Diese Zaehlung ist **eine** Vorfrage
(S1s UNGEMESSEN-Punkt 2, S4s V-S4-2 und V-S4-3 sind dieselbe Messung in drei Formulierungen). Die
Analyse danach ist verschieden und darf nicht verschmolzen werden: S1 fragt eine
**Selektionsfrage** (verzerrt der Ausschluss A1?), S4 eine **Kausalfrage** (aendert die Regel die
Praemien-Dynamik?). Reihenfolge: eine Zaehl-Vorfrage -> S1s Selektions-Antwort (billig, A1-relevant)
-> S4s Diff-in-Disc nur, wenn `N_eff >= 20`.

**(2) S2 X-OEKO-4 + S3 X-ASTRO-1 - VEREINEN, zwingend.**
Beide segmentieren dieselben Tagesreihen in Regime, beide gegen dieselbe Langgedaechtnis-Null,
beide liefern als Hauptprodukt eine REZENZ-/Fenster-Aussage. Getrennt registriert waeren das zwei
Methodenvarianten derselben Frage - also **K-Inflation nach 3.3.4** ohne inhaltlichen Zugewinn.
Ergebnis: **ein** Paket, drei Detektoren (PELT primaer, STARS zweiter, Bayesian Blocks dritter),
S2s 2-von-3-Regel und Toleranzfenster als Design-Parameter, S3s `ncp_prior`-Formel und
`p0`-Etikett uebernommen, S2s Anti-Snooping-Klausel bindend. Zu streichen ist S3s Anspruch,
damit die **Cluster-Einheit** nach DEC-51 Punkt 3 zu messen - das ist eine andere Groesse
(gemeinsame Schocks, nicht zeitliche Segmentierung), und die Blocklaenge liefert der stationaere
Bootstrap, `rho(BTC,ETH)` liefert WP-7.

**(3) S1 X-SURV-3 + WP-10(B) - VEREINEN, als Spezifikation.**
X-SURV-3 ist ausdruecklich kein neues Paket (der Scout sagt das selbst), sondern der fehlende
Schaetzer fuer eine bereits geplante Kurve. Aufnahme in die WP-10(B)-Spezifikation, mit den zwei
Auflagen aus Abschnitt 1 (Cancel-Politik definiert die Konkurrenzhazard; die CIF loest die
Luecken-Zensierung **nicht**). Ein eigener Registry-Eintrag waere Etikettenschwindel.

**(4) S5 X-AKT-4 + WP-7 - VEREINEN, als Beifahrer.**
Dieselbe Panel-Maschinerie, dieselben Fingerabdruecke, Laufzeit Sekunden. Der Teil, der bleibt,
ist L2 (Herleitung des 0,30-Design-Parameters) plus die `w_i`-Verteilung; L1/L3 laufen in der
homogenen 8h-Klasse voraussichtlich leer (Abschnitt 1). Kein eigenes Paket, keine 0,3 Personentage
als eigene Position.

**(5) Nicht genannt, aber real: S2 X-OEKO-3 + S3 X-ASTRO-3 - TRENNEN, Surrogat-Modul teilen.**
Verschiedene Metriken (Rolling-EWS vs. Spektralleistung) und verschiedene Fragen, aber identische
Nullmaschinerie (Block-Bootstrap, IAAFT/phasenrandomisiert, ARFIMA/FIGARCH). Ein Surrogat-Modul in
`stats3`, von beiden benutzt; zwei Module waeren doppelte Kalibrierungspflicht mit doppeltem
Fehlerrisiko.

**(6) Nicht genannt, aber real: S5 X-AKT-1 + X-AKT-2 - VEREINEN.**
Beide leben von denselben DEC-53-Cluster-Serien und denselben vier WP-10(A)-Proxies, beide sind
Berichtsgroessen ohne Gate, und `alpha_implizit/R` verknuepft sie ohnehin zu einer
Konsistenzpruefung. Eine Berichtszeile, nicht zwei Pakete.

**(7) Nicht genannt: S3 X-ASTRO-2 (P2-Bezug) + S3 X-ASTRO-3 (8h-Funding-Linie) + A2s Placebo P2.**
Alle drei fragen, ob der Funding-Takt 00/08/16 UTC den Verfallseffekt vortaeuscht. A2 hat dafuer
bereits P2 registriert. Zulaessig ist, P2 quantitativ zu unterfuettern - nicht, dieselbe Frage ein
drittes Mal als eigenes Paket zu fuehren.

---

## 4. Top-5 ueber alle Scouts - und die drei groessten Risiken

### Top-5 (Kriterium: aendert eine Entscheidung in Welle 1, kostet Minuten bis Stunden, beide Ausgaenge verwertbar)

1. **Totzonen-/Bindungs-Zensus (aus S4 X-NEXP-1, dort nur "Nebenbefund").**
   Anteil der Symbol-Intervalle mit `F` **exakt** `0,01 %`. Bei breiter Bindung ist A1s
   Dezil-Sortierung ueber weite Teile degeneriert, das effektive K bricht ein, und die
   Feasibility-Frage stellt sich vor dem Backfill. Erste Messung auf den **113 vorhandenen
   Harvest-Tagen** - null Download, Minuten. Das ist die wertvollste einzelne Zeile des gesamten
   Exkurses und sie steht bei ihrem eigenen Autor an vierter Stelle eines Abschnitts.
2. **Analytische Formretention von `r_pre` (aus S3 X-ASTRO-2).**
   Eine Stunde, kein Datenlauf, beruehrt A2s einzige urteilstragende Statistik und erweitert V-5
   um eine notwendige Teilfrage. Aufnahme als Nachtrag zu PRD 5.2 - nicht als Paket.
3. **Intervallwechsel-Zensus (verschmolzen aus S1 X-SURV-2 und S4 X-NEXP-2).**
   Zaehlung der Wechsel je Tag/Dezil/Fenster; entscheidet, ob A1s Registrierungstext geaendert
   werden muss und ob X-NEXP-2 ueberhaupt `N_eff >= 20` erreicht. Laeuft auf dem A1-Backfill mit.
4. **X-OEKO-1 Arm (a) - Relaxationsrate nach Schockstunden.**
   Der einzige Vorschlag mit primaer verifiziertem grossem N (403/362 Ereignistage, GL-026),
   ohne neuen Parameter, ohne Download, 20-60 min CPU. Haertet B.8 von n=1 zu einer Verteilung und
   gibt jedem Fill-/Slippage-Modell auf `STRESS_ABS` eine gemessene Erholungszeit.
5. **Konstanten-Nachtrag Klasse P (X-AKT-4 L2 + X-AKT-2 MaxDD-Korrektur).**
   Zwei Herleitungen ohne Lauf: das gesetzte 0,30 aus PRD 5.1 Kill-4 wird zu `k <= 2,333*w`, und
   der MaxDD-Boden in 3.6 wird als driftlos und `sqrt(T)`-abhaengig kenntlich gemacht. Zusammen
   eine Seite PRD-Text, null Rechenzeit, dauerhafte Wirkung auf jede kuenftige P-Registrierung.

*Knapp verpasst:* V-AKT-1 (Insurance-Fund-Nachladbarkeit) - nicht weil es unwichtig waere, sondern
weil es nach 3.3.7 ohnehin geschuldet ist und deshalb kein Vorschlag, sondern eine offene Pflicht.

### Die drei hoechsten Risiken

1. **X-NEXP-3 - "teure Infra vor validiertem Signal" (D.16 in Reinform).**
   Neuer Boersen-Backfill ausserhalb der PRD-7.1-Tabelle, neue Schaetzerfamilie mit fuenf
   Literaturstraengen, und die beantwortete Frage ist Vorbedingung **keines** Welle-1-Kandidaten.
   Arm 2 ist zusaetzlich historisch nicht rekonstruierbar. Genau die Bauform, die CS-04/CS-05 in
   2.0 bewusst nicht gebaut wurden.
2. **X-OEKO-2 - teure Methodeninfrastruktur, deren Hauptbegruendung entfallen ist.**
   Der zentrale Verkaufspunkt (L-17: Fenster-Kombination nur als Stouffer/Fisher-Obergrenze) ist
   durch **DEC-53** fuer alle kuenftigen Laeufe bereits geschlossen. Uebrig bleibt ein zweites
   Inferenz-Regime neben dem gerade erst beschlossenen DEC-52, zum ehrlich ausgewiesenen Preis von
   Faktor 2,4-3,3 in N - fuer genau die Fragen, denen N fehlt. Zwei koexistierende Designs sind
   ausserdem ein offener Torpfosten, solange die Zuordnung nicht hypothesenweise vorab fixiert ist.
3. **X-OEKO-3 - "Methodenvariante = K-Inflation" in Reinform.**
   Eine Pipeline mit `K = |w| x |Detrending| x |Indikatoren|` in der Groessenordnung 100-150, deren
   vorab fixierte Regel ausdruecklich vorsieht, dass ein ueberlebender Indikator **Kandidat** wird.
   Das ist der Entstehungsweg von H-11: eine Metrik aus einer grossen Variantenfamilie, deren
   Nulleffekt-Kalibrierung anschliessend als Legitimation dient. Der wertvolle Teil (`n_eff = T/w`)
   ist ohne jeden Lauf verfuegbar; der Rest ist Risiko. *Runner-up:* X-ASTRO-3, mit demselben
   Muster in kleinerem Massstab und mit einem D.4-Eintrag als naechstem Nachbarn.

---

## 5. Was allen fuenf fehlt (blinde Flecken)

1. **Die Abhaengigkeit vom WP-7-Befund B1 wird nirgends durchgerechnet.** Faellt B1 (Klasse W
   statistisch nicht testbar), sind X-SURV-1, X-SURV-2, X-AKT-4, X-NEXP-1 und X-NEXP-2 ohne
   Adressaten - fuenf der sechzehn Vorschlaege haengen an A1/A3/WP-7. Kein Scout schreibt eine
   Zeile "was von meinem Vorschlag bleibt, wenn WP-7 B1 liefert".
2. **Niemand bilanziert das aggregierte K und die Ueber-Familie des Exkurses.** DEC-22/C.16
   verlangen eine zweistufige FDR ueber Kohorten. 16 neue Messpakete, von denen mehrere
   ausdruecklich Kandidaten fuer spaetere R-Registrierungen erzeugen sollen, veraendern die
   Selektions-Decke des Programms. Jeder Scout rechnet sein eigenes K; keiner rechnet das gemeinsame.
3. **Die knappe Ressource ist falsch bestimmt.** Alle fuenf optimieren CPU-Minuten und
   Personentage. Der bindende Engpass ist nach PRD 9.3 die **Registrierungs-Bandbreite des
   Orchestrators und der Sequenz-Zwang** (Zensus vor jedem Alpha-Slot, Regelaenderung vor dem
   ersten Kandidaten, der sie braucht). Zusammengenommen wuerden die 16 Vorschlaege Welle 1
   ungefaehr verdoppeln - das wird nirgends als Kosten benannt.
4. **Der Konflikt zwischen datengetriebenen Fensterregeln und append-only-Disziplin bleibt offen.**
   S2/S3 wollen REZENZ mechanisch bestimmen. Was passiert, wenn der Detektor einen Change Point
   **innerhalb** von A1s W1 oder A2s W2 findet, nachdem die Fenster bereits schriftlich fixiert
   sind? Keiner von beiden beantwortet das; ohne eine Vorab-Antwort ist die Regel eine
   Torpfosten-Maschine.
5. **Kein Scout prueft den Datenbestand neu.** Alle rechnen auf F.1 mit Stand 2026-08-10 und
   schreiben Kalenderzuwachs fort (43 -> 66 bzw. 67 Tage) - S1 vermerkt sogar ausdruecklich, dass
   im Sandbox-Baum kein Harvest-Manifest auffindbar ist. Jede N-Zeile, die auf diesen Zahlen steht,
   ist unverifiziert. Eine neue Inventur kostet Minuten und geht jeder Power-Zeile voraus (C.8).
6. **Die Nutzer-Maschine als Ausfuehrungsort wird kaum mitgedacht.** Jeder Backfill (Praemien-Index,
   Binance-Klines, Insurance-Historie, Funding) laeuft nach PRD 4/7.1 zwingend auf dem Windows-PC
   als unbeaufsichtigter Ein-Befehl-Runner mit rc != 0 bei Vorbedingungsfehlern. Vier Vorschlaege
   fordern Backfills, keiner spezifiziert den Runner - und keiner nennt das Schutzgut
   "Harvest-Baum read-only, eigener Store mit SHA-256" (WP-9-Muster), das fuer jeden neuen Speicher
   gilt.
7. **Positivkontrollen sind unterspezifiziert.** C.13/3.3.8 sind Pflicht bei komplexen
   Maschinerien; nur S3 (X-ASTRO-3, Funding-Linien) und S4 (X-NEXP-2, springende Carry) benennen
   eine. Fuer X-OEKO-3, X-OEKO-4/X-ASTRO-1 und X-SURV-2 fehlt sie - bei Detektoren, deren
   Nullbefund sonst uninformativ waere (GL-020-Muster).
8. **Belegasymmetrie wird nicht als Risiko bepreist.** S4s vier Vorschlaege ruhen komplett auf
   [sek]-Snippets zu Boersenregeln; S2/S3 auf gesperrten Volltexten. Alle markieren das
   vorbildlich - aber keiner formuliert die Konsequenz als **Vorbedingung**: eine Boersenmechanik,
   die einen Cutoff definiert, ohne Primaerbeleg zu registrieren, waere die C-14-Fehlerklasse.
9. **Niemand fragt, ob eine gemessene Enabler-Zahl je ein Verdikt aendern wuerde.** Bei
   X-AKT-3 (ADL-Wahrscheinlichkeit) ist die Antwort nachweislich nein: 3.3.9(c) ist ein Etikett mit
   10-20 % Erwartungswert-Abschlag, und ein Intervall von 0,1 % bis 5 % aendert keine Entscheidung.
   Diese Pruefung ("welche Entscheidung kippt bei welchem Messwert?") fehlt in zwoelf von sechzehn
   Entscheidungsrelevanz-Zeilen - sie sagen, was ein PASS **bedeutet**, nicht, was er **aendert**.

---

## 6. Kurzliste: was VOR einer Aufnahme in das PRD (als Nachtrag) zu tun ist

1. **Datenbestand neu inventarisieren.** F.1 ist Stand 2026-08-10; alle N-Zeilen des Exkurses sind
   fortgeschrieben, nicht gemessen. Manifest-Wahrheit ist
   `harvest_manifest.backup.sqlite`. Ohne diesen Schritt keine Power-Zeile.
2. **V-1 erweitern und beantworten** (Primaerquelle, Nutzer-Maschine): Zins-Term `I` je
   Kontraktklasse **inkl. 1h**, clamp-Grenze, Cap-Formel und `k`, Ausnahmeliste, Auto-Switch-Regel
   und Rueckwechsel-Praxis. Vorab fixierte Konsequenz: ohne Primaerbeleg ist kein X-NEXP-Vorschlag
   registrierbar und der A1-Ausschluss bleibt bestehen (F-1/F-2).
3. **Eine gemeinsame Zaehl-Vorfrage formulieren** (loest S1s UNGEMESSEN-2, S4s V-S4-2 und V-S4-3
   zugleich): Totzonen-/Bindungsanteil des Sortierschluessels, Intervallwechsel je Tag/Dezil,
   Verteilung von `w_i`. Erste Naeherung auf den 113 vorhandenen Harvest-Tagen, danach auf dem
   A1-Backfill. Materialitaetsgrenzen vorab fixieren.
4. **V-5 um Teilfrage (c) erweitern** (Zeitgeometrie der Umkehr relativ zu 08:00 UTC) und A2s
   Richtungsregistrierung ausdruecklich daran binden; die analytische Formretentions-Rechnung als
   Nachtrag in PRD 5.2 aufnehmen.
5. **Gebuehren-Konstantenpruefung in V-4-Nachbarschaft** an der Primaerquelle; bis zum Ergebnis
   `tradability3` nach 3.3.6 RAISEN statt still weiterrechnen. Kein Gate wird beruehrt (C.2). Die
   `adv_sel_max`-Formel in WP-10(B) bekommt eine Fussnote zur Gebuehrenabhaengigkeit.
6. **A1-Registrierungstext (PRD 5.1) um vier Punkte ergaenzen** (Abschnitt 2.i): bedingter
   Ausschluss als Symbol-Wochen-Regel, Intervallklassen-Spalte in `panel_1d`, Pflicht-Sensitivitaet
   mit eingeschlossenen 1h-Symbolen, schriftliche Feststellung der W1/W2-Inhomogenitaet vor jeder
   Registrierung (PRD 9.3 Punkt 6).
7. **Verschmelzungsbeschluss Change-Point:** ein Paket (S2 X-OEKO-4 + S3 X-ASTRO-1), drei
   Detektoren, 2-von-3-Regel, eigene DEC fuer die Fenster-Schnitt-Regel **mit ausdruecklicher
   Nicht-Rueckwirkung** auf bereits fixierte Fenster.
8. **Drei Vorschlaege als Spezifikationen einarbeiten, nicht als Pakete registrieren:**
   X-SURV-3 -> WP-10(B); X-AKT-4 (L2 + `w_i`) und X-SURV-1 -> WP-7; X-AKT-1/X-AKT-2 -> eine
   Berichtszeile der Klasse P plus Fussnote in 3.6. Das reduziert die 16 Vorschlaege auf
   ~6 eigenstaendige Objekte.
9. **Null-Zensus-Klausel als Verfassungszeile:** ein Nulleffekt-/Erreichbarkeits-Zensus darf
   **niemals** einen Kandidaten promoten; zulaessige Ausgaenge sind D-Eintrag oder "nicht
   ausgeschlossen". Betrifft X-OEKO-3 und X-ASTRO-3 unmittelbar und schliesst den H-11-Pfad.
10. **K-/Ueber-Familien-Bilanz des gesamten Exkurses** vor der Aufnahme: welche der verbleibenden
    Objekte tragen eine Teststatistik, welche gehen in welche `F-...`-Familie, wie veraendert sich
    die Selektions-Decke (3.3.4/K-0.3). Ohne diese Bilanz waere der Nachtrag selbst eine
    unkontrollierte Variantenvermehrung.
11. **Sequenz-Zwang wahren (PRD 9.3):** nichts von alledem vor den Stress-Fixtures und V-1..V-5;
    nichts, was A1/A3 voraussetzt, vor WP-7; Regelaenderungen (Fenster-Schnitt-Regel, etwaige
    sequentielle Designform) als DEC **vor** dem ersten Kandidaten, der sie braucht.
12. **Speicher-/Schutzgut-Disziplin fuer jeden neuen Backfill:** eigener Store nach WP-9-Muster
    (SCHEMA_VERSION, SHA-256-Sidecar, Manifest-Gate, Loud-Fail), niemals in den Harvest-Baum
    schreiben; der Binance-Backfill aus X-NEXP-3 braucht zusaetzlich eine eigene DEC zum
    PRD-7.1-Scope.

---

## 7. Abschliessende Bewertung

Der Exkurs hat geliefert, was er liefern konnte: **null Alpha-Kandidaten und eine Handvoll
Messungen, die vorhandene Pakete praeziser machen.** Der Ertrag konzentriert sich auf drei Zeilen,
die zusammen weniger als einen Personentag kosten - Totzonen-Zensus, Formretention von `r_pre`,
Herleitung des 0,30-Parameters - plus zwei billige Messungen (Intervallwechsel-Zaehlung,
Relaxationsrate). Alles Uebrige ist entweder Auflagen-behaftet, dupliziert eine bestehende Pflicht
oder ist teure Methodik vor einem validierten Bedarf.

Die groesste inhaltliche Leistung der fuenf Berichte ist gleichzeitig ihre groesste Schwaeche: die
Bybit-Mechanik, die S4 rekonstruiert und die S1 unabhaengig als Selektionsproblem erkennt, ist real
und im Programm bislang unbemerkt - steht aber vollstaendig auf Suchtreffern. Der richtige
naechste Schritt ist deshalb keine neue Methode, sondern **eine erweiterte V-1 an der
Primaerquelle**. Danach entscheidet sich, ob aus dem Exkurs zwei PRD-Nachtragsseiten werden oder
sechs.

*Ende REVIEW_S1_S5.md - read-only im Repo; geschrieben ausschliesslich im Scratchpad.*
