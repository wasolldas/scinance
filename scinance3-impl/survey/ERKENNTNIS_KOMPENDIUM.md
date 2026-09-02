# ERKENNTNIS-KOMPENDIUM — Scinance-Forschungsprogramm

> Zusammengestellt aus: `FINAL_PRD.md` (Scinance 2.0, Stand 2026-06-11),
> `scinance2-impl/CLAUDE.md` (Programm-Verfassung), `state/hypothesis_registry.md`
> (H-01..H-26, 31 Wellen-Registrierungen), `state/gate_log.md` (GL-001..GL-031,
> alle Gate-Urteile), `state/decisions.md` (DEC-01..DEC-50, alle Architektur-
> und Methoden-Entscheidungen), alle Wellen-/WP-Befunddokumente in
> `scinance2-impl/state/`, sowie den Vorgaenger-Rahmenwerken
> `edge_research_framework/` (Generation 1, erzeugte das Original-PRD fuer
> Scinance 1.0), `implementation_framework/` (baute Scinance 1.0: S1-S5,
> M1-M26), `edge-reconciliation/` (erzeugte `FINAL_PRD.md` = Scinance-2.0-
> Verfassung aus dem Scinance-1.0-Scherbenhaufen) und `edge-research-v3/`
> (Cross-Domain-Recherche, Quelle fuer H-09..H-13).
>
> Stand der Auswertung: nach GL-031 (2026-08-20) und DEC-50 (2026-09-01).
> **Programm-Bilanz in einer Zeile:** 31 Gate-Eintraege, 0 Torpfosten-
> Verschiebungen, **0 handelbare Kanten**. Sieben kapitalfreie Mess-WEITER
> (H-04, H-05b, H-11 [mit Etiketten], H-15, H-16 [korrigierte Lesart], H-23),
> jede einzelne davon in der eigens dafuer registrierten Tradability-Pruefung
> PARK oder gar nicht erst getestet. Der einzige noch aktive Strategie-Pfad
> ist die (gesperrte) VRP-Messung H-26 auf Optionen.

---

## A. HYPOTHESEN-TABELLE

Verdikt-Kuerzel: **WEITER** = kapitalfreies Mess-Gate bestanden (impliziert
NIE Handelbarkeit); **DROP** = Gate verfehlt, endgueltig; **GESPERRT** =
data-gated, Lauf noch nicht moeglich; **PARK** = Tradability-Gate verfehlt
(Kapital-Status geparkt); **KEIN VERDIKT** = Lauf technisch/methodisch
ungueltig, keine inhaltliche Aussage; **REFUTED** = aus der Scinance-1.0-Aera,
forensisch isoliert widerlegt; **UNTESTED/eingefroren** = nie gelaufen, Wave-1
bewusst nicht gebaut.

### A.1 — Scinance-1.0-Erbe (vor der Registry, REFUTED-Register aus FINAL_PRD §6)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund (ein Satz) | Referenz |
|---|---|---|---|---|---|
| CS-01 | „Seismischer Cascade Detector" (S1), Hawkes-Kaskaden | Futures-Perp, Liquidationen+Trades | REFUTED | Das vorgeschaltete rho-Gate (C-14) erreicht den importierten Schwellwert 0,85 strukturell nie (rho-Median ~2e-7, 6 Groessenordnungen darunter) — S1 feuert 0 Trades auf allen 5 Symbolen, nicht aus Datenmangel. | FINAL_PRD §6, E-01/E-02 |
| CS-02 | „Entropie-Momentum" (S2) | Futures-Perp, Orderflow/Entropie | REFUTED | Drei unabhaengige Forensiken: Maker-Only-Test roh negativ auf JEDEM Symbol auch bei 0 Fees (-3,45 bps Aggregat); Mirror-Test zeigt hit_sum 0,179 statt 1,0 (nicht invertierbar, execution-loss-bound); Friktion dominiert Richtung ~35x. | FINAL_PRD §6, E-03/E-04/E-16 |
| C-14 | Hawkes-Spektralradius rho(Phi), Schwelle+Estimator | Futures-Perp | REFUTED (Konzept UNTESTED) | Importierter Threshold 0,85 aus fremder Mikrostruktur (Bacry-Mastromatteo-Muzy) nie auf Bybit-Erreichbarkeit geprueft; auf Bybit sechs Groessenordnungen unerreichbar. Branching-Konzept selbst lebt sauber in C-27/H-Familie weiter. | FINAL_PRD §6, E-01 |
| CS-03/C-22 | S3 Pre-Settlement Funding-Pressure | Futures-Perp, Funding | -> siehe H-01 | Bug-Fix-Run (iter-5) unter E-15-Vorbehalt aktiv gehalten, dann via H-01 endgueltig adjudiziert. | FINAL_PRD §3, siehe A.2/H-01 |
| CS-04 | S4 Pattern x Foundation-Modell | Futures-Perp | UNTESTED, eingefroren | 0 Trades wegen `insufficient_models` 96-99,99% — der Modell-Loader war nie verdrahtet (E-13). Mess-Luecke, keine Niederlage; S4/S5-Falle: teure Infra vor validiertem Basissignal ist die teuerste Form, nichts zu lernen. In Welle 1 bewusst NICHT gebaut. | FINAL_PRD §2.4, E-13 |
| CS-05 | S5 Cross-Sectional Reversion (Panel-Harness) | Futures-Perp, Multi-Symbol | UNTESTED, eingefroren | 0 Trades wegen `single_symbol_replay_unsupported` 100% — Single-Symbol-Replayer kann Cross-Sectional-Logik prinzipiell nicht ausfuehren (E-14). Panel-Harness bewusst nicht in Welle 1. | FINAL_PRD §2.4, E-14 |
| C-36 | Recording-Engine F0 (gedeckelter Infrastruktur-Pilot) | Futures/Spot, neue Streams (rpi/insurance/adl/premium-index/options) | PILOT-STATUS (kein Alpha-Gate) | 8h-Dauertest: premium_index_kline OK (REST-Pfad), rpi/insurance NO_DATA (Subscribe bestaetigt, 0 Frames), option_tickers NO_DATA (falscher Endpunkt — spaeter geklaert: Optionen liegen auf `wss://.../v5/public/option`, nicht auf der Linear-WS). Kein Alpha-Gate, reines Infrastruktur-Fundament. | GL-004 (1. Eintrag), DEC-46 |

### A.2 — Welle 1 (H-01..H-03, die vier PRD-Piloten)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-01 | E-15/CS-03 S3 Pre-Settlement, iter-5-Fix | Futures-Perp, Funding-Pressure-Release | DROP | Aggregierte Netto-Edge -15,47 bps (klar unter der -10-bps-DROP-Schwelle); der iter-5-Fix (Tick-Zeit-Time-Stop, friction-aware Hard-Stop) wirkt mechanisch (Tails gekappt), aber die RAW-Edge bleibt bei -4,48 bps — das Problem war nie der Exit, sondern ein Entry-Signal ohne Edge. | H-01 Registry, GL-004 (2. Eintrag) |
| H-02 | C-42-Reproduktion (LightGBM/HAR-RV, Vol-Stack-Anker) | Futures+Spot, `kline_1min`, 36 Features | DROP/PARK | 0 von 5 Symbolen bestehen OOS-R^2>=0,15 UND QLIKE<HAR gemeinsam ueber purged Walk-Forward; FDR liefert 0/36 signifikante Features. Der dokumentierte Test-R^2~=0,249 (research_notes) war ein L1-Selbstauskunfts-Artefakt, das die Peso/L0-Verschaerfung nicht ueberlebt. Sperrt C-10/C-35/C-11/C-12/C-34 + VRP-RV-Bein dauerhaft. | H-02 Registry, GL-001 |
| H-03 | C-31 Cyclostationary CFAR (einziger neuer Alpha-Test Welle 1) | Futures-Perp, publicTrade-Inter-Arrivals | DROP | Surrogate-p ~1,0 auf BTC/ETH in beiden Fenstern (weit ueber 0,05); gemessene Edge 0,01-0,04 bps — ~250x unter der 11-bps-Friction-Wand. "Abgegraste HFT-Anomalie" wie im PRD-A-priori vorhergesagt. | H-03 Registry, GL-005 |

### A.3 — Welle 2 (H-04..H-06, kapitalfrei) und ihre Tradability-Folgen

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-04 | C-17/C-41 Cross-Sectional Lead-Lag (Mess-Gate) | Futures-Perp BTC/ETH, `trades` | WEITER (kapitalfrei; Kapital PARK) | Gerichtete Information BTC->ETH FDR-signifikant in BEIDEN Fenstern (TE + WCOH, p_crit bis 0,0050), Lead-Symbol BTC stabil ueber beide Fenster, signifikante Lags 1-3 s. Reine Mess-Existenz — keine Edge-/bps-Aussage registriert. | H-04 Registry, GL-006 |
| H-04b | Lead-Lag-TRADABILITY (Friction+Latenz-Konfrontation) | wie H-04, +Kostenmodell | PARK | Netto-Edge nach 300-ms-Latenz-Haircut und 11-bps-Wand in BEIDEN Fenstern klar negativ (-14,95/-14,83 bps), Bootstrap p=1,0000, 0 FDR-Survivor; brutto-Einfang max. +0,19 bps — ~80x unter der Wand. Selbst der Maker-Sekundaerfall bleibt negativ (-5,9 bps). | H-04b Registry, GL-009 |
| H-05 | C-01 OFI-Vorzeichen-Test (INC-02-Anker, Aggression-Folge-These) | Futures-Perp, `trades` | DROP (+C-09-OFI-Bein +C-14-OFI-Erbe) | Kein Symbol/delta zeigt FDR-signifikant POSITIVES Vorzeichen in BEIDEN Fenstern; der einzige robuste FDR-Effekt ist INVERS (ETH, corr -0,0550, p=0,0050) — die PRD-v1/CS-02-Aggression-Folge-These ist widerlegt, der INC-02-Falsifikator (E-04) reproduziert. | H-05 Registry, GL-007 |
| H-05b | OFI-Vorzeichen INVERSE Lesart (MM-Replenishment, OOS) | Futures-Perp SOL, Harvester-Backfill April/Mai | WEITER (kapitalfrei; Kapital PARK) | SOLUSDT delta1s/delta5s zeigen ueber 2 disjunkte, echt OOS-Fenster konsistent negatives, FDR-signifikantes OFI-Vorzeichen — aber schmal (nur 1 Symbol, 2 kuerzeste Lags, |corr| nur 0,010-0,051, ueberwiegend ueber sekundaeren Hit-Rate-Anker getragen). | H-05b Registry, GL-010 |
| H-05c | OFI-Fade-TRADABILITY (SOL, invers) | wie H-05b, +Kostenmodell | PARK | Netto-Edge in allen 4 Zellen ~-14,9 bps, Bootstrap p=1,0000, 0 FDR-Survivor; brutto-Einfang nur +0,03 bis +0,10 bps — 150-500x unter der 15-bps-Gesamt-Wand. OFI-Vorzeichen-Komplex damit vollstaendig abgearbeitet (DROP/WEITER/PARK). | H-05c Registry, GL-011 |
| H-06 | C-07 Permutation Entropy (Vol-Cluster-Vorbote) | Futures-Perp, `kline_1min` | DROP | PRE-Gate rho>=0,30 in ALLEN 10 Symbol×Fenster-Zellen verfehlt (Maximum +0,0145, ~20x zu klein) -> hartes Ein-Fenster-DROP schon hier. Zusaetzlich verfehlt das Haupt-Gate den AUC-Lift (+0,0072 statt >=+0,03). | H-06 Registry, GL-008 |

### A.4 — Welle 3 (H-07/H-08, C-06 Cross-Sectional Mean-Reversion)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-07 | C-06 XMR mit absolutem z-Threshold (|z|>=2,5) | Futures-Perp, 5-Symbol-Panel | DROP (struktureller A-priori-Power-DROP) | Mathematische Gewissheit: auf N=5 Symbolen ist max\|z\| = sqrt(N-1) = 2,0 (Populationsvarianz) bzw. 1,79 (Sample) — beides < dem registrierten Z_THRESH=2,5. Achse A feuert NIE, N=0 Events, N-Floor reisst mit Sicherheit. Kein Datenlauf noetig. | H-07 Registry, GL-012 |
| H-08 | C-06 XMR mit rang-basierter (schwellenfreier) Ueber-Dehnung | wie H-07, Achse A = argmax\|z\| | DROP (empirisch) | 0 von 6 Zellen FDR-signifikant; Nicht-Trivialitaets-Anker (nicht-ueberlappende CIs kond. vs. Baseline) in ALLEN Zellen verfehlt; Fenster B (Mai) zeigt sogar negatives mu_rev bei h6 — der April-only-Survivorship-Effekt (research_notes) wurde vom vorregistrierten 2-Fenster-Guard korrekt aussortiert. C-06 damit vollstaendig erschoepft. | H-08 Registry, GL-013 |

### A.5 — Welle 4 (H-09..H-13, Cross-Domain-Track aus `edge-research-v3`)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-09 | Risk-Limit-Tier-Bunching (Margin-Kink-Vermeidung) | Futures-Perp, 5 Symbole, Order-Aggregate | DROP (empirisch) | 0 von 10 Zellen bestehen, 0 FDR-Survivor; Bunching-Schaetzer vorzeichen-wild (-3,49 bis +10,20) — Muster von Rauschen, nicht systematischem Kanten-Bunching. Das A-priori (Rundzahl-Praeferenz statt Order-Level-Steuerung) bestaetigt. | H-09 Registry, GL-016 |
| H-10 | Cross-Stream-Pointer-Days + Pre-Event-Drift | Futures-Perp+Deribit-dvol, 30 Detektions-Serien | DROP (empirisch) | Im gesamten 79-Tage-Fenster existiert KEIN einziger Pointer-Tag (>=60% Serien gleichgerichtet); N_pointer=0, harter N-Floor (>=3) reisst in beiden Stufen. Existenz-DROP fuer dieses Regime, kein Belege-gegen-Crash-Regimes-Befund. | H-10 Registry, GL-017 |
| H-11 | AnEn-Vol-Regime-Forecast vs. HAR-RV (CRPS, 3-Tage-Horizont) | Futures-Perp BTC/ETH | WEITER (kapitalfrei, MIT bindenden Einschraenkungs-Etiketten) | Alle 4 Zellen bestehen CRPSS>=0,05 & p<=0,05 (4-6x der Schwelle) — ABER: dieselbe CRPS-Regel schenkt einer informationsfrei gedressten HAR bereits CRPSS~0,21-0,29 (Dirac-vs-Verteilung-Artefakt); Schwelle 0,05 war Faktor 4-5 zu niedrig. Verdikt steht (Registry-Disziplin), Interpretation ist entwertet -> H-11c. | H-11 Registry, GL-022, DEC-31 |
| H-11c | AnEn gegen dispersions-gematchte (gedresste) HAR-Baseline | wie H-11, echte Informationsfrage | DROP (empirisch) | 0 von 4 Zellen bestehen; CRPSS_dressed in 3/4 Zellen NEGATIV (AnEn schlechter als kostenlos gedresste HAR), kein p unter 0,29. Das "Geschenk" durch reines Dressing (26-30% gemessen) ist in jeder Zelle groesser als der unter der alten Regel gemessene Vorsprung. C-11-Linie als Quelle eines Prognose-Vorsprungs geschlossen. | H-11c Registry, GL-024, DEC-33 |
| H-12 | Cross-Exchange-Fragmentierungsmatrix (RMT/Marchenko-Pastur) | Futures-Perp+Deribit, BTC/ETH x 3 Boersen | DROP (empirisch) | W1 (valide, 47/50 Tage): Kriterium (b) Median-IPR(v2)=0,169 liegt praktisch exakt auf dem theoretischen Minimum 1/6~=0,167 eines VOLLSTAENDIG DELOKALISIERTEN Vektors — kein boersenlokalisierter zweiter Faktor. Nach Envelope-Loader-Fix (2026-08-10) auch W2 valide UND ebenfalls DROP — Verdikt auf breiterer Basis bestaetigt. | H-12 Registry, GL-018 |
| H-13 | Tail-Form-Konsistenz GPD-xi (physisch) vs. risikoneutral | Futures-Perp+Deribit-Options-Surface | GESPERRT (data-gated) | Braucht 2 vol-regime-disjunkte Snapshot-Tage mit >=12 Strikes je Symbol im noch jungen `markprice.options`-Fenster (43 Tage Stand 2026-08-10). Nie gelaufen. | H-13 Registry |

### A.6 — Welle 5 (H-14..H-18, GPU-Pattern-Mining)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-14 | Conditional Cross-Venue-Lead-Lag-Graph (12-Node-Panel, Node-Ablation) | Futures-Perp, 12 Nodes (Bybit/Binance/Deribit) | METHODISCH INVALIDE (kein Verdikt) | Die vorregistrierte Positivkontrolle (bekannte BTC->ETH-Kante muss detektierbar sein) scheitert in BEIDEN Fenstern (0/9 Kanten ueber Null-q95) — die Ablations-Maschinerie sieht nicht einmal den bekannten Effekt, ihr Null-Befund auf allen anderen Kanten ist uninformativ. | H-14 Registry, GL-020 |
| H-15 | Trade-Tape-Event-Grammatik jenseits Markov (Causal-Transformer) | Futures-Perp, 5 Symbole, publicTrade-Tokenstream | WEITER (kapitalfrei) | 4/5 Symbole bestehen: Transformer schlaegt beste Markov-k<=4-Baseline um >=2% relative Cross-Entropy, Luecke ueberlebt 200 saisonalitaetserhaltende Block-Shuffle-Surrogate, FDR-signifikant. Laengerreichweitige Sequenzstruktur jenseits Kurzgedaechtnis-Modellen nachgewiesen. | H-15 Registry, GL-021 |
| H-16 | Time-Arrow-CNN: Zeit-Irreversibilitaet im Trade-Flow (CNN, Forward-vs-Reversed) | Futures-Perp, 5 Symbole, Scalogramme | WEITER (kapitalfrei; KORRIGIERTE Lesart) | 4/5 Symbole AUC>=0,60 gegen exakte Bayes-Null 0,5, Leak-Kontrolle bestanden — ABER die vorregistrierte Ablation zeigt: 85-106% des Effekts stammt aus der Asymmetrie des Aktivitaets-/Volatilitaets-ENVELOPES (verwandt zum Leverage-Effekt), NICHT aus der Flussrichtung. Verdikt steht, urspruengliche "zeitgerichtete Struktur"-Formulierung zurueckgezogen. | H-16 Registry, GL-015 + Nachtrag 2026-08-10, DEC-30 |
| H-17 | Venue-Fingerprint: Boersen-Identitaet in shape-normalisiertem Orderflow | Futures-Perp, 10 Nodes (5 Symbole x 2 Boersen) | VERDIKT AUSSTEHEND (aufgeloest als H-23) | Mess-Gate klar bestanden (5/5 Folds, Pooled-Accuracy 0,8944) — aber das registrierte Non-Redundanz-Gate gegen H-12 ist NICHT auswertbar (nur n=2 Ueberlappungstage < 10-Floor). Kein Torpfosten-Verschieben: kein Verdikt, bis eine Wiederholung das Redundanz-Gate auswertbar macht. | H-17 Registry, GL-019 |
| H-18 | Lead-Lag High-N-Surrogat-Aufloesungs-Audit (n_surrogates 200->100.000) | wie H-04, reines Aufloesungs-Audit | AUDIT-BEFUND (kein Hypothesen-Verdikt; GL-006 bleibt unveraendert) | GL-006 wird NICHT falsifiziert: 12/12 Survivor bleiben bei 500x Aufloesung BH-signifikant. Praezisierung: 4 Zellen (beide WCOH + 2 TE-Zellen) hart bestaetigt (p<1e-5), 8 Zellen — darunter ALLE ETH->BTC-Kanten — ab jetzt als "aufloesungsbedingt fragil" etikettiert (Zitierpflicht). | H-18 Registry, GL-014 |

### A.7 — Welle 6 (H-19..H-22, CPU-first, Bar-Cache-Aera)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-19 | C-19 DRIFT — Stationaritaet der Tape-Struktur ueber Kalenderzeit (META/AUDIT) | Futures-Perp, 5 Symbole, WP-0-Bar-Cache | BEFUND: STATIONAER-GENUG (kein WEITER/DROP) | 0 von 15 Zellen zeigen \|rho_p\|>=0,30 in BEIDEN OOS-Fenstern gleichen Vorzeichens. Regime-Splitting-Auflage fuer H-20/H-21/H-22 wird NICHT ausgeloest. (D3-Aktivitaets-Konzentration zeigt zwar einen einmaligen Uebergang bis ~2022->2024, aber keinen laufenden Drift.) | H-19 Registry, GL-025 |
| H-20 | C-20 TAIL-AFTERMATH — Reversion nach 3,5-sigma-Stunden | Futures-Perp, 5 Symbole, WP-0-Bar-Cache | DROP (empirisch) | OOS-1 verfehlt beide Bedingungen (Mittel unter Boden, p=0,40); OOS-2 erreicht den +10-bps-Boden (+17,3 bps), aber p=0,17 (3,5x ueber der Schwelle). Vorzeichen ueber Symbole/Fenster instabil (BTC -16->+36, ETH +32->-12 bps). Hartes Ein-Fenster-Kriterium greift zweifach. | H-20 Registry, GL-026 |
| H-21 | C-21 LIQ-TAG — Informationsgehalt des Liquidations-Labels | Futures-Perp BTC/ETH, `allLiquidation` | GESPERRT (data-gated bis 2026-12-27) | Braucht lueckenlose `done_days` fuer `allLiquidation`+`publicTrade` ueber zwei feste 90-Tage-Kalenderfenster (2026-07-01..09-28, 09-29..12-27). Noch nie gelaufen. | H-21 Registry |
| H-22 | C-22 L2-TILT — Tages-Buchneigung -> Folgetags-Rendite | Futures-Perp BTC (urteilstragend; ETH nur Bericht) | DROP (empirisch) | Beide urteilstragenden BTC-Fenster verfehlen beide Bedingungen: IC +0,0665 (W-L2-1) / -0,0112 (W-L2-2), beide < Schwelle 0,10, p 0,10/0,57. Die von Lane C vorab benannte A-priori ("DROP erwartet — Buchtiefe gegen 1-Tages-Horizont widerspricht Zerfallsstruktur") ist bestaetigt. | H-22 Registry, GL-027 |

### A.8 — Welle 7 (H-23/H-24, What-else + Reservekandidat)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-23 | C-17-Venue-Fingerprint mit Voll-Distanzserie (Aufloesung von GL-019) | wie H-17, Distanzserie ueber ALLE 100 Panel-Tage | WEITER (kapitalfrei) | Beide Gates bestanden: Mess-Gate 5/5 Folds (Pooled 0,8914, repliziert ueber 2 unabhaengige Trainings-Kohorten), Non-Redundanz-Gate jetzt auswertbar (n=78 Ueberlappungstage statt 2): Spearman rho=-0,414 gegen c12-lambda2, klar unter der 0,6-Redundanzschwelle. GL-019-Schwebezustand aufgeloest (nach zwei Werkzeug-Fehlschlaegen GL-029/GL-030, s. Abschnitt C). | H-23 Registry, GL-031 |
| H-24 | C-24 IMPACT-PERSISTENZ — Minuten-Fluss-Lead auf 30-Min-Forward-Rendite | Futures-Perp, 5 Symbole, WP-0-Bar-Cache, REZENZ-Klausel | DROP (empirisch) | Positivkontrolle bestanden (gleichzeitiger IC +0,53/+0,54, 5,3x ueber Floor) — aber IC30 in BEIDEN juengsten Halbjahres-Fenstern NEGATIV (-0,0179/-0,0169), entgegengesetztes Vorzeichen zur Hypothese, p am Ceiling (1,0000). Ueber 10 Halbjahre 2021-2026 STABIL: der einzige ueber die gesamte Historie regime-invariante Befund des Programms — Minuten-Impact ist ueberwiegend PERMANENT, nicht Fortsetzung. | H-24 Registry, GL-028 |

### A.9 — Welle 8 (H-26, Options-Pfad)

| ID | Titel (kurz) | Familie/Markt/Daten | Verdikt | Entscheidender Grund | Referenz |
|---|---|---|---|---|---|
| H-26 | C-26 Varianz-Risiko-Praemie auf Deribit (zweiseitig: Verkaeufer- + Kaeufer-Frage) | Optionen, Deribit BTC/ETH, dvol+publicTrade | GESPERRT (data-gated bis ~Mitte November 2026) | Braucht lueckenlose `done_days` fuer Deribit `dvol` UND `publicTrade` je Symbol ueber >=210 zusammenhaengende Tage. Der einzige noch aktive Strategie-Pfad des Programms. Blockiert war lange NICHT die Datenlage, sondern dass der Live-Sammelpfad des Harvesters keine Manifest-Zeilen schrieb (DEC-46/49/50) — inzwischen behoben, Entsperrung haengt jetzt nur noch an Kalenderzeit. | H-26 Registry, DEC-45/49/50 |

### A.10 — WP-Reihe (Arbeitspakete, keine Hypothesen — Zensus/Infrastruktur mit eigenem Binaer-Befund)

| ID | Titel (kurz) | Zweck | Befund/Verdikt | Referenz |
|---|---|---|---|---|
| WP-0 | Deterministischer 1-min-Bar-Cache | Korrektheits-Fundament fuer Welle 6+ (behebt den nicht-deterministischen Trade-/RV-Lesepfad, DEC-34) | Gebaut, 5 Symbole, 10.054 Cache-Tage, 14,4 Mio Minutenbars, bit-identisch ueber unabhaengige Laeufe; ordnungs-unabhaengige Aggregate statt Thread-Zwang. | DEC-35/36 |
| WP-1 | L2-Zensus (Snapshot+Delta-Lesart pruefen) | Vorbedingung fuer H-22 (Registrierungs-Gate: "faellt der Zensus gegen die Delta-Lesart aus, wird L2-TILT nicht registriert") | BESTAETIGT: schon das historische `orderbook.500`-Regime ist Snapshot+Delta (~0,4-1,3 GB/Tag statt der befuerchteten 17 TB). H-22-Vorbedingung erfuellt. | WP1_L2_ZENSUS_BEFUND, DEC-35/36 |
| WP-2 | L2-Tilt-Extraktion (Ein-Pass, hash-gepinnt) | Vorleistung fuer H-22 | 3 Fenster extrahiert (99,2%/93,2%/99,8% Abdeckung), Fingerabdruecke gepinnt; H-22 lief darauf (-> DROP). | H-22-Nachtrag 2026-08-17 |
| WP-3 | (noch nicht gebaut) L2-Sweep-Ereignis-Extraktion | Vorbedingung fuer den vertagten Kandidaten SWEEP-PRE (V-01) | NICHT registriert, NICHT gebaut — vertagt nach H-23/H-24 ("billig" ist kein Registrierungsgrund). | DEC-38 |
| WP-4 | Quote-Spread-Zensus (Bybit-Perp-Majors) | Vorfrage fuer den Maker-Spread-Capture-Kandidaten | TOT: Top-of-Book-Spread ist EXAKT EIN TICK (0,016-0,054 bp), 75-255x unter dem Maker-Roundtrip (4,0 bp). H-25 wird NICHT registriert. Programm-Konstante: Spread-Capture ist auf diesen Maerkten a priori tot. | WP4_SPREAD_ZENSUS_BEFUND, DEC-42 |
| WP-5 | Bybit-Options-Quote-Zensus (Kettensnapshot) | Klaert, ob der Options-Quote-Spread eine VRP-Strategie a priori toetet | WIDERLEGT eigene Vorab-Fehlaussage (n=1-Extrapolation aus degenerierter ITM-1-Tag-Ecke): im gehandelten Band (7-14 DTE, |Delta| 0,15-0,30) ist der Spread eng (0,14/0,26 Vol-Punkte BTC/ETH). Bindende Nebenbedingung wird die (damals ungepruefte) Gebuehr. | WP5_OPTIONS_SPREAD_ZENSUS_BEFUND, DEC-44 |
| WP-6 | Options-Stress-Spread-Zensus (Stresstag 19.08.) | Prueft, ob die Quote-Enge im Stress haelt | Haelt zu 97-99% der Minuten; Verbreiterung episodisch und punktgenau an Schockminuten (BTC 0,66%, ETH 2,82% der Minuten). Long-Vol-Reaktions-Kauf auf Signal hin wird quantifiziert toedlich (Spread allein ~9,5 Vol-Punkte = 3x die C-33-Kante am Schub). | WP6_STRESS_SPREAD_BEFUND, DEC-47/48 |

---

## B. PROGRAMM-KONSTANTEN

Jede Zahl hier ist gemessen, dokumentiert und darf ohne Neuherleitung zitiert
werden. Quelle steht dahinter.

1. **Round-Trip-Friction-Wand: 11 bps (Taker) bzw. ~15 bps inkl. Slippage.**
   Die Kernrelation des gesamten Programms — jede gemessene Rohkante (max.
   4-7 bps in Scinance 1.0) liegt darunter. (`verdict.md` §2 Kernrelation,
   FINAL_PRD §1, durchgehend zitiert bis GL-031)
2. **Perp-Top-of-Book-Spread = EXAKT EIN TICK, praktisch konstant.**
   BTC 0,0157 bp (RECENT) / 0,0196 bp (2024Q1); ETH 0,0537 bp. Dispersion
   p90-p10 nur 0,8-2,7% des Medians — der harte Boden, unter den nicht
   gemessen werden kann. (WP-4, DEC-42)
3. **Maker-/Taker-Gebuehr Perp (kanonische Repo-Konstanten):** `FEE_MAKER` =
   2,0 bp je Bein (4,0 bp Roundtrip), `FEE_TAKER` = 5,5 bp je Bein.
   (DEC-42, WP-4)
4. **Options-Gebuehr (verifiziert, getrennt von den Perp-Konstanten, da auf
   den Index statt aufs Notional gerechnet):** `FEE_OPTION_MAKER_OF_INDEX` =
   0,0002 (2 bp des Index), `FEE_OPTION_TAKER_OF_INDEX` = 0,0003 (3 bp des
   Index). Kein Rabatt auf der Options-Karte aktiv. (DEC-45)
5. **vega/S (Umrechnung Options-Gebuehr <-> Vol-Punkte):** 5,28 bp Index je
   Vol-Punkt (BTC), 5,10 bp je Vol-Punkt (ETH), im Bein-Band (7-14 DTE,
   |Delta| 0,15-0,30). Skalen-invariant trotz 31-fach unterschiedlichem
   Basiswert-Niveau — per Unit-Test gepinnt. (WP-5, DEC-44)
6. **Options-Quote-Breite im Bein-Band (7-14 DTE, |Delta| 0,15-0,30):**
   volle Quote-Breite 0,14 Vol-Punkte (BTC) / 0,26 Vol-Punkte (ETH); eng
   ueber neun aufeinanderfolgende Verfalltermine (bis ~123 Tage), erst LEAPS
   brechen weg (BTC 1,0-1,6; ETH 18-28 Vol-Punkte). (WP-5, DEC-44)
7. **Break-even-Gebuehr fuer die C-33-Schwelle von 3 Vol-Punkten:** passiver
   Einstieg + Halten bis Verfall (2 Fills) frisst 25% (BTC) / 26% (ETH) der
   Kante, Rest 2,24/2,22 Vol-Punkte; Taker-Round-Trip (4 Fills) frisst
   85%/96% — praktisch tot. (DEC-45)
8. **Options-Quote-Breite im Stress (19.08.2026, groesster gemessener
   Schock):** haelt in 97-99% der Minuten (Stundenmedian BTC 0,16-0,17 wie
   an Ruhe-Tagen); Verbreiterung episodisch: BTC 0,66% der Minuten breit
   (laengste Episode 8 min, Spitze 9,53 Vol-Punkte), ETH 2,82% (laengste
   75 min, Spitze 53,8 Vol-Punkte). Renormalisierung binnen Minuten bis
   max. ~2 h. Die Enge haengt am SCHOCK-UEBERGANG, nicht am IV-Niveau.
   (WP-6, DEC-47/48)
9. **Dressing-Artefakt (strukturelles CRPS-Geschenk gegen eine
   Dirac-Baseline):** ein informationsfreies Dressing (Gauss/Laplace/t5,
   k=20) erzeugt CRPSS zwischen 0,21 und 0,29 — theoretisch hergeleitet
   (GL-022 E1) UND empirisch bestaetigt: 26,3-30,3% Geschenk allein durch
   Dressing (GL-024). Jede CRPS-Verteilung-vs-Punktprognose-Bewertung muss
   dagegen kalibrieren.
10. **Vol-Regressions-Prognose (AnEn) schlaegt eine gleich breit gedresste
    HAR-Baseline NICHT:** 0 von 4 Zellen, CRPSS_dressed in 3/4 Zellen
    negativ, kein p unter 0,29 (GL-024). Der C-42-LightGBM-Anker selbst
    reproduziert ebenfalls nicht (0/5 Symbole, GL-001).
11. **Cross-Sectional-z struktureller Deckel:** max\|z\| = sqrt(N-1) auf
    einem N-Symbol-Panel; bei N=5 also 2,0 (Populationsvarianz) — mathematisch
    unerreichbar fuer jeden Literatur-Threshold >=2,5. (GL-012)
12. **Zeit-Irreversibilitaets-Signatur (H-16):** AUC bis 0,7353 (BTC/ETH)
    gegen exakte Bayes-Null 0,5 — aber 85-106% des Effekt-Ueberschusses
    stammen aus der Asymmetrie des Aktivitaets-/Volatilitaets-Envelopes,
    NICHT aus der Flussrichtung (unsigned/signed-AUC-Verhaeltnis 85-106%
    je Symbol). (GL-015-Nachtrag, DEC-30)
13. **Venue-Fingerprint-Staerke:** Pooled-Balanced-Accuracy bis 0,9950
    (Einzel-Fold), 0,8944/0,8914 gepoolt ueber zwei unabhaengige Trainings-
    Kohorten (GL-019, GL-031). Redundanz zur Fragmentierungs-Eigenstruktur
    (H-12): Spearman rho=-0,414 (n=78 Tage), klar unter der 0,6-Schwelle —
    eigenstaendiges Strukturmerkmal, keine Doppelmessung.
14. **Minuten-Fluss-Impact, ein programm-weit stabiler stilisierter Fakt
    (H-24):** gleichzeitiger IC konstant ~+0,53 bis +0,61, Forward-IC30
    konstant ~-0,011 bis -0,022 — ueber ZEHN Halbjahre 2021-2026 stabil
    (die einzige ueber die gesamte Historie regime-invariante Groesse des
    Programms). Der Impact ist ueberwiegend PERMANENT, nicht fortsetzend.
15. **Numerischer Rauschboden des Trade-/RV-Lesepfads:** maximale relative
    Lauf-zu-Lauf-Streuung 3,8e-9 (float-Summations-Nichtdeterminismus in
    paralleler DuckDB-Aggregation) — sieben Groessenordnungen unter jedem
    bisher urteilsrelevanten Gate-Abstand. (DEC-32/34)
16. **Datenreichweite (Stand 2026-08-10):** `bybit/publicTrade` fuer alle
    5 Symbole lueckenlos von 2020-03-25 (BTC) bzw. 2021-06-29 (SOL/BNB) bis
    heute — 5-6 Jahre, mehrere Marktregime (Corona-Crash, Bull 2021, Baer
    2022). Das ist die Voraussetzung fuer Horizonte von Tagen bis Wochen
    ueberhaupt und der einzige bekannte Weg aus dem Horizont-Problem
    (Sekunden-Skalen-Befunde x 80-500 unter der Wand). (DATA_INVENTORY
    2026-08-10)
17. **Hardware-Konstante:** Zielmaschine fuer alle T2/T3-Laeufe = RTX 5060 Ti
    (Blackwell), CUDA 12.8+/PyTorch 2.7+, 82 GB RAM, Windows. Die Sandbox
    (Orchestrator-Umgebung) hat kein torch/keine GPU — jeder GPU-Lauf ist
    zwingend ein lokaler T3-Overnight-Lauf.

---

## C. METHODEN-LEHREN

Jede Regel hier wurde durch einen konkreten Vorfall erzwungen, nicht am
Schreibtisch erdacht.

1. **Registry-Disziplin / Pre-Registration, append-only, kein Torpfosten-
   Verschieben.** Grundregel seit PRD §8; ueber alle 31 GL-Eintraege
   durchgehalten — selbst wenn ein Verdikt unangenehm war (H-11 WEITER trotz
   erkanntem Schwellendefekt, DEC-31), wurde nicht die Schwelle nachtraeglich
   angehoben, sondern eine NEUE, vorab registrierte Folge-Hypothese (H-11c)
   gebaut. Symmetrisch: auch ein unliebsames PASS wird nicht wegkorrigiert.
2. **Mess-Gate != Tradability-Gate (die zentrale Programm-Doktrin).**
   Jede kapitalfreie Existenzfrage (`capital_free=true`) ist strikt getrennt
   von der Frage der Handelbarkeit. Etabliert an H-04 (WEITER kapitalfrei)
   -> H-04b (PARK, eigener Registry-Eintrag, eigenes Gate, Anti-Gaming-
   Klausel) und wiederholt an H-05b -> H-05c. Verhindert den S2/2023-Fehler
   ("OFI hat Signal -> OFI ist handelbar").
3. **Anti-Gaming-Klausel fuer Tradability-Gates.** Friction-Wand (11 bps),
   Latenz-Haircut (300 ms Default) und Fill-Annahme (Taker primaer) sind vor
   dem Lauf fixiert und duerfen NICHT abgesenkt werden, um ein WEITER zu
   erzwingen — jede Abweichung waere Torpfosten-Verschiebung. (DEC-13/16,
   angewendet in H-04b/H-05c)
4. **Struktureller Nulleffekt der Metrik VOR der Schwellenfestlegung
   ausrechnen (Dirac-vs-Verteilung-Lehre).** Ausloeser: H-11/GL-022 — die
   registrierte Schwelle (CRPSS>=0,05) lag Faktor 4-5 UNTER dem Boden, den
   ein informationsfreies Dressing strukturell erzeugt. Seit DEC-31/33 ist
   das Ausrechnen des strukturellen Nulleffekts Pflichtzeile jeder neuen
   Registrierung (Welle 6 wendet das durchgehend an: rho-Rauschboden
   1/sqrt(N), IC-Rauschboden etc.).
5. **Jede Hypothese braucht ein positives UND ein negatives synthetisches
   Fixture (DEC-39-Pflicht).** Ausloeser: H-24 — beim Bau der Test-Fixtures
   zeigte sich VOR dem Lauf, dass die registrierte Metrik (IC30>=0,02) eine
   ANDERE, staerkere Frage misst als der Hypothesentext behauptete
   (permanenter Impact liefert IC30~=0, nicht Persistenz). Seither Pflicht:
   mindestens ein Regime, das den behaupteten Effekt zeigt, eines, das ihn
   nicht zeigt — beide als Fixture gepinnt.
6. **Materialitaets-Schranke statt Bit-Identitaet gegen einen lebenden
   Speicher.** Ausloeser: H-11c Lauf 1 verfehlte eine 1e-9-Bit-Identitaets-
   Vorbedingung gegen ein Archiv aus einem lebenden, sich bewegenden
   Datenspeicher — strukturell unerfuellbar. Ersatz: eine aus der
   Gate-Arithmetik hergeleitete relative Schranke (hier 1e-4, 250x unter der
   Gate-Schwelle) plus ein SHA-256-Fingerabdruck fuer forensische
   Nachvollziehbarkeit. (DEC-32)
7. **N=2 beweist KEINEN Determinismus.** Zwei uebereinstimmende Laeufe
   wurden in GL-024 faelschlich als Determinismus-Beleg gelesen — ein
   dritter Lauf traf dann exakt den urspruenglichen (abweichenden) Wert und
   entlarvte den Fehler: es waren zwei zufaellig gleiche Ziehungen aus einem
   tatsaechlich nicht-deterministischen Pfad (paralleler Float-Summation +
   Tie-Break-Mehrdeutigkeit in 4 Loadern, programmweit). Determinismus wird
   durch Wiederholung MIT Fingerabdruck belegt, nie durch zwei zufaellig
   passende Laeufe. (DEC-34)
8. **Negative Behauptungen brauchen eine Inhaltsprobe, keine
   Namenskonvention.** Ausloeser: die eigene Behauptung "der Harvest-Baum
   enthaelt keinen Bybit-Options-Strom" war falsch — sie schloss aus dem
   FEHLEN eines Ordners namens `option_tickers` auf Datenabwesenheit, obwohl
   die Optionsdaten laengst im `tickers`-Strom neben den Perp-Tickern lagen
   (3.751 Symbole waeren fuer reine Linear-Perps viel zu viele gewesen —
   das Indiz stand schon da). Dieselbe Fehlerklasse wie N=2 (Punkt 7) und
   n=1-Extrapolation (Punkt 9): Schluss aus Abwesenheit von Beweis statt aus
   Beweis von Abwesenheit. (DEC-46)
9. **n=1-Extrapolation ohne Kontrolle der erzeugenden Achse ist gefaehrlich.**
   Ausloeser: aus EINEM Options-Ticker-Sample (9,55 Vol-Punkte Quote-Breite)
   wurde geschlossen, der Eintrittsabschlag sei "die groesste erhoffte
   Kante" — das Sample lag exakt in der einen degenerierten Ecke (1 Tag bis
   Verfall, tief im Geld, Vega~0). Im tatsaechlich gehandelten Band war die
   Breite 37-68x enger. Konsequenz: jede IV-Statistik wird seither NUR NOCH
   nach |Delta| getrennt ausgewiesen, ein Unit-Test pinnt das Pooling-
   Artefakt als Fixture. (DEC-44)
10. **Hartes Ein-Fenster-Abbruchkriterium, kein Nachverhandeln.** Verfehlt
    eine Schwelle in EINEM von >=2 disjunkten Fenstern, ist das DROP/PARK —
    unabhaengig davon, wie stark andere Fenster performen. (PRD §8.5,
    durchgehend angewendet, z.B. H-20: OOS-2 erreicht die Magnitude, aber
    OOS-1 nicht -> DROP)
11. **Modul != Strategie (Forensik-Disziplin).** Das Scheitern einer
    integrierten Strategie widerlegt nur die Module, deren Versagen
    forensisch ISOLIERT nachgewiesen ist. Aus CS-01 ist NUR C-14 REFUTED
    (C-15/C-26 bleiben SUSPECT, weil das rho-Gate ihre Ausloesung blockierte);
    aus CS-02 wird KEIN Modul automatisch REFUTED. (FINAL_PRD §2.1)
12. **Struktureller A-priori-DROP vor jedem Datenlauf pruefen
    (Feasibility-Check, GL-012-Lehre).** Vor jeder Schwellenfestlegung
    pruefen, ob sie auf der verfuegbaren Datenbasis MATHEMATISCH erreichbar
    ist. H-07 (Z_THRESH=2,5 auf N=5-Panel) war es nicht — ein Datenlauf war
    gar nicht noetig, um DROP zu urteilen. Seither Pflichtschritt in jeder
    neuen Registrierung ("Feasibility (GL-012-Check)").
13. **Positivkontrolle als Pflichtbestandteil komplexer Mess-Maschinerien.**
    Eine Ablations-/Graph-Pipeline (H-14) muss einen BEKANNTEN Effekt (den
    H-04-Lead) wiederfinden koennen, sonst ist ihr Null-Befund auf allen
    anderen Kanten uninformativ -> "methodisch invalide", nicht DROP.
    (GL-020-Muster, spaeter auch fuer H-24 angewendet)
14. **Loud-Fail-Doktrin.** Fehlende Vorbedingungen (ein nicht uebergebener
    Referenz-Datensatz, ein Payload-Format ohne erwartete Felder, ein
    Manifest ohne Zeile) muessen LAUT scheitern, nie still einen falschen
    Nullbefund erzeugen. Mehrfach erzwungen: GL-018 (Envelope-Payload-Form),
    GL-029 (fehlende Redundanz-Referenz — Runner-Bedienfehler, kein
    Methodenfehler), DEC-46 (Manifest-Registrar fuer Live-Stroeme).
15. **Checkpoint-Systeme brauchen einen getesteten Round-Trip, nicht nur
    einen getesteten Rechenpfad.** GL-030: eine neue Checkpoint-Kennung
    (`main_full`) wurde beim Schreiben korrekt behandelt, aber die
    Pflichtschluessel-Tabelle beim LESEN nicht aktualisiert — vier
    bestehende Tests deckten nur den Rechenpfad ab, keiner das Lesen aus
    dem Checkpoint-Verzeichnis.
16. **Zweistufige FDR ueber Kohorten (Familie -> Ueber-Familie).** Laufen
    mehrere vorregistrierte Hypothesen als gemeinsame Kohorte (>=2), greift
    ZUSAETZLICH zur familien-internen BH-FDR eine zweite, uebergeordnete
    BH-FDR ueber die gepoolten Survivor (F-WAVE2 fuer Welle 2, F-XDOM1 fuer
    Welle 4) — rein verschaerfend, nie erleichternd. (DEC-22, Registry-
    Disziplin-Nachtrag 2026-06-15)
17. **Data-Snooping-Offenlegung + Entdeckungszellen-Ausschluss bei aus
    Daten geborenen Folge-Hypothesen.** H-05b entstand aus einer post-hoc
    beobachteten Zelle (ETH w0 delta1s) — die Registry verlangt seither
    explizit: die Entdeckungszelle ist NICHT konfirmatorisch, Konfirmation
    braucht ANDERE Zellen/Fenster, moeglichst echte OOS-Daten. (H-05b
    Registry, "Entstehungs-/Data-Snooping-Offenlegung")
18. **REZENZ-Klausel: urteilstragende Fenster muessen das juengste
    Marktregime abdecken; aeltere Historie ist rein deskriptives
    Aera-Profil.** Ausloeser: Welle-6-Querbefund (D3-Uebergang endet
    ~Mitte 2024, H-20-Vorzeichen kippt zwischen Aeren, H-22-IC lebt nur
    2023/24) — eine Hypothese kann formal bestehen und trotzdem nur
    Marktarchaeologie messen. Ab DEC-38 verbindliche Pflicht fuer jede
    kuenftige Registrierung (H-24 wendet sie erstmals an: nur die zwei
    juengsten Halbjahre urteilstragend).
19. **Reversibelste-Option-Prinzip bei jeder Unterspezifikation.** Wo PRD
    oder Registry zu einem Implementierungsparameter schweigen (Grid,
    Surrogate-Form, Storage-Deckel, Modul-Heimat), entscheidet der
    architect fuer die reversibelste Option und dokumentiert als DEC-xx —
    NIE eine Gate-Schwelle selbst. Durchgehendes Muster ueber DEC-03 bis
    DEC-18 (research-Paket-Konvention, ein Verzeichnis loeschen = voller
    Rueckbau).

---

## D. VERWORFENE ANSAETZE (a priori tot, nie wieder zu reiten)

Diese Ansaetze sind nicht bloss "aktuell DROP", sondern gelten als
programmweit erledigt — jede Wiederholung ohne nachweislich neues Signal
waere ein Verstoss gegen die Registry-Disziplin.

1. **Spread-Capture / Market-Making auf Bybit-Perp-Majors.** Der Top-of-Book-
   Spread ist ein Tick (0,01-0,05 bp), 75-255x unter jeder Gebuehrenwand.
   Verallgemeinerbarer Programm-Befund: JEDE kuenftige Idee, deren
   Ertragsquelle "den Spread einfangen" ist, ist auf diesen Maerkten a
   priori tot; handelbare Ertragsquellen muessen Preisbewegung sein.
   (WP-4, DEC-42)
2. **Hawkes-Branching-Ratio-Schwelle (C-14, 0,85) und jede direkte
   Wiederholung.** Sechs Groessenordnungen unter dem importierten
   Threshold auf Bybit-Daten; jeder Branching-Ratio-Ansatz (auch C-30
   Natural-Time kappa_1) muss zuerst die Erreichbarkeit seiner Schwelle per
   Distributions-Check beweisen. (FINAL_PRD §6, E-01)
3. **Entropie-Momentum / einfache Sign-Flip-Strategien auf Orderflow-
   Entropie (CS-02/S2).** Verliert auch bei 0 Fees, nicht invertierbar.
   Kein Re-Test der S2-Richtungsthese, keine simple Invertierung erlaubt.
   (FINAL_PRD §6)
4. **Cyclostationary CFAR (C-31) auf publicTrade-Inter-Arrivals.**
   "Abgegraste HFT-Anomalie" — Edge 250x unter der Wand, Surrogate-p~1,0.
   (H-03, GL-005)
5. **OFI-Vorzeichen als direktes Follow-Signal (Aggression-Folge-These,
   C-01/H-05).** Kein Symbol zeigt konsistent-positives, FDR-signifikantes
   Vorzeichen; die einzige robuste Struktur ist invers und selbst dort nicht
   handelbar (H-05c). Zieht C-09-OFI-Bein und C-14-OFI-Erbe mit.
6. **Permutation Entropy als Vol-Cluster-Vorbote (C-07/H-06).** PRE-Gate-
   Korrelation praktisch null (max 0,0145 gegen Schwelle 0,30) — die
   Grundannahme selbst traegt nicht.
7. **Cross-Sectional Mean-Reversion auf dem 5-Symbol-Panel, jede
   Ueber-Dehnungs-Definition (C-06/H-07/H-08).** Absolute z-Schwelle
   mathematisch unerreichbar (max\|z\|=2,0 < 2,5); rang-basierte,
   schwellenfreie Definition empirisch DROP (0 FDR-Survivor, kein
   Nicht-Trivialitaets-Nachweis). C-06 auf diesem Panel erschoepft.
8. **Risk-Limit-Tier-Bunching (C-09/H-09) als Order-Placement-Signal.**
   Reine Rundzahl-Praeferenz, kein Kanten-Effekt; 0/10 Zellen, Rauschmuster.
9. **Cross-Stream-Pointer-Days / Synchronisations-Detektion in diesem
   Marktregime (C-10/H-10).** N=0 Pointer-Tage im gesamten 79-Tage-Fenster —
   Existenz-DROP, keine Neuauflage ohne laengeres/regime-reicheres Fenster.
10. **Cross-Exchange-Fragmentierungs-Eigenstruktur via RMT (C-12/H-12).**
    Der zweite Eigenmodus ist praktisch vollstaendig delokalisiert
    (IPR~1/6) — kein boersenlokalisierter Faktor, auf breiterer (2-Fenster-)
    Basis bestaetigt.
11. **Conditional Cross-Venue-Lead-Lag-Graph via Deep-Learning-Ablation
    (H-14) in dieser Architektur/diesem Horizont.** Positivkontrolle
    scheitert — nicht ohne Horizont-/Architektur-Neufassung als neue,
    eigens vorregistrierte Hypothese wiederholbar.
12. **Tail-Aftermath-Reversion nach Vol-Schocks (C-20/H-20) auf 3,5-sigma-
    Basis.** Vorzeichen ueber Symbole und Aeren instabil; keine
    Sigma-/Horizont-/Luecken-Nachsuche erlaubt ohne neue Vorregistrierung.
13. **L2-Buchneigung als Folgetags-Richtungssignal (C-22/H-22).** Buchtiefe
    binnen ±25 bps traegt auf 1-Tages-Horizont nichts — Zerfallsstruktur-
    A-priori bestaetigt.
14. **Minuten-Netto-Fluss als Fortsetzungs-/Lead-Signal (C-24/H-24).**
    Ueber zehn Halbjahre stabil NEGATIVER Forward-IC — der Impact ist
    permanent, kuendigt keine weitere Bewegung an. Kein H-24-Ergebnis
    rehabilitiert C-01/OFI.
15. **Reaktives Long-Vol (Strangle-Kauf auf ein Bewegungssignal hin).**
    Quantifiziert toedlich: der Einstieg faellt zwangslaeufig in die
    Schock-Minuten, in denen der Spread das 10-100-fache betraegt (WP-6);
    ausserdem existiert keine Prognose-Hypothese, die VOR dem Schub feuert
    (GL-024-Lehre: die eigene RV-Prognose schlaegt keine Gratis-Baseline).
16. **Schwere Multi-Modell-/Panel-Infrastruktur VOR validiertem
    Basissignal (S4/S5-Falle).** CS-04 (Modell-Loader) und CS-05
    (Panel-Harness) wurden bewusst NICHT in Welle 1 gebaut — teure Infra
    ohne validiertes Kernsignal ist die teuerste Form, nichts zu lernen.
    (FINAL_PRD §2.4)
17. **Aus v1/v3 superseded/gestrichene Kandidaten:** DSM-03
    (Funding-Premium-Vorhersage) — Premium-Index nur 43 Tage und nur als
    Delta-Strom, nicht registrierbar; Options-Chain-Kandidaten (CHAIN-GRAPH,
    SET-SHAPE) — Tardis-Sampling nur 2 Tage/3 Monate, endgueltig tot;
    Bitmex-Multi-Zyklen-Ideen — nur 112 Tage Tiefe statt der angenommenen
    2014er-Historie. (DATA_INVENTORY 2026-08-10)

---

## E. OFFENE FAEDEN (registriert-aber-gesperrt, ausstehend oder vertagt)

Vollstaendige Liste aller Punkte, die weder verworfen noch abgeschlossen
sind — mit der jeweiligen Entsperr-Bedingung oder dem Grund der Vertagung.

1. **H-21 · LIQ-TAG (C-21, Liquidations-Label-Information) — GESPERRT bis
   2026-12-27.** Braucht lueckenlose `done_days` fuer bybit `allLiquidation`
   UND `publicTrade`, BTC+ETH, ueber zwei feste 90-Tage-Kalenderfenster
   (W1 2026-07-01..09-28, W2 2026-09-29..12-27). Bewusst NICHT auf den
   heute verfuegbaren 43 Tagen gestartet (haette dieselbe N-Falle wie
   H-10/H-13 wiederholt).
2. **H-26 · Varianz-Risiko-Praemie (C-26, Deribit, zweiseitig) — GESPERRT
   bis ~Mitte November 2026.** Braucht >=210 zusammenhaengende `done_days`
   fuer Deribit `dvol` UND `publicTrade`, je Symbol (BTC/ETH). Der einzige
   noch aktive Strategie-Pfad des Programms. War lange NICHT durch
   Datenmangel blockiert, sondern weil der Harvester-Live-Pfad keine
   Manifest-Zeilen schrieb (DEC-46) — inzwischen durch einen Manifest-
   Registrar mit Watchdog+Baseline-Alarm behoben (DEC-49); die zwei fuer
   H-26 noetigen Stroeme (dvol, publicTrade) waren dabei zunaechst BEWUSST
   ausgenommen (Vermeidung von Pauschal-DONE auf partiellen Tagen) —
   Scinance hat gezielt zurueckgemeldet, genau diese zwei Stroeme mit
   begrenztem Nachlauf (<=3 Tage) zu registrieren (DEC-50,
   `RUECKMELDUNG_HARVESTER_DVOL_PUBLICTRADE.md`); Antwort/Umsetzung des
   Harvest-Projekts steht zum Auswertungsstand noch aus.
3. **H-13 · Tail-Form-Konsistenz (GPD-xi physisch vs. risikoneutral) —
   GESPERRT, kein festes Datum.** Braucht 2 vol-regime-disjunkte
   Snapshot-Tage mit >=12 Strikes je Symbol im noch jungen
   `markprice.options`-Fenster (43 Tage Stand 2026-08-10, waechst
   kalendarisch). Deterministische, nicht-diskretionaere Tageswahl bereits
   in der Registrierung fixiert.
4. **H-17 · Venue-Fingerprint (urspruengliche Fassung) — durch H-23/GL-031
   AUFGELOEST**, bleibt aber als eigener, historischer "VERDIKT
   AUSSTEHEND"-Eintrag stehen (append-only; wird NICHT rueckwirkend
   geaendert).
5. **SWEEP-PRE (V-01) / WP-3 — NICHT registriert, vertagt.** Braucht eine
   eigene L2-Sweep-Ereignis-Extraktion (WP-3, noch nicht gebaut); Wert ist
   Execution-Timing UNTER der Friktionswand. Bleibt Kandidat nach H-23/H-24,
   "billig" allein ist kein Registrierungsgrund. (DEC-38)
6. **H-26b (Options-VRP-Tradability) — NICHT registrierbar, bis:**
   (a) das Bybit-Options-Gebuehrenschema-Delivery-/Exercise-Gebuehr bei
   Verfall verifiziert ist (bindende, noch ungemessene Kostenkomponente —
   trifft ausgerechnet das beste DEC-45-Szenario), UND (b) ein
   Options-Spread-Zensus mit reparierter/durchgaengiger Bybit-Aufzeichnung
   vorliegt (bislang nur EIN Snapshot + eine 5-Tage-Stress-Stichprobe auf
   Deribit-Basis; ein durchgaengiger Bybit-Quote-Datensatz existiert noch
   nicht), UND (c) H-26 selbst gemessen ist. Reihenfolge verbindlich, sonst
   wuerde die Schwelle nach dem Sehen der Zahl gesetzt. (DEC-44/45)
7. **C-33 (Options-VRP-Kapitalfreigabe, PRD-Original) bleibt unabhaengig
   von H-26 bindend an >=12 Monate IV-Recording MIT Stress-Periode
   gebunden** — ein H-26-PASS auf Deribit-Daten ist maximal "kapitalfrei
   WEITER"; die 12-Monats-Uhr fuer eine echte Kapitalfreigabe laeuft
   unabhaengig und fruehestens Mitte 2027 ab.
8. **ETH-Options-Aufzeichnungsluecke 2026-08-22 08:00 bis 08-27 08:00 UTC
   — ENDGUELTIG verloren.** Serverseitiger Subscription-Verlust im
   Settlement-Fenster (Ursache identifiziert, DEC-49); fuer 22.08.-24.08.
   14:00 existiert GAR KEINE Quelle. Root Cause behoben (Ist-Abgleich beim
   taeglichen Refresh, 30-Minuten-Watchdog, Baseline-Alarm), betrifft aber
   keine Stress-Phase — als verschmerzbar eingestuft.
9. **Bybit-native Options-Bid/Ask-Historie vor 2026-08-24 (WP-5-REST-
   Sampler-Start) — nicht durchgehend vorhanden.** Der Harvester zeichnet
   die WS-Ticker seit dortigem WP-12/DEC-08 auf, aber die genaue
   historische Tiefe/Vollstaendigkeit VOR der Entdeckung dieses Stroms
   (DEC-46) ist fuer Scinance nicht unabhaengig verifiziert; der REST-
   Sampler (15-min-Takt, seit 24.08.) und der WS-Strom laufen seither
   redundant.
10. **Keine der `capital_free`-WEITER-Hypothesen impliziert eine
    Tradability-Folge**, solange diese nicht separat registriert ist —
    folgende Folge-Hypothesen sind explizit NICHT registriert und NICHT
    impliziert: H-04c (andere Latenz/Wand-Annahme fuer Lead-Lag), H-05d
    (weitere OFI-Variante), H-07b, H-09b, H-10b, H-11b (VRP-Monetarisierung
    des toten AnEn-Vorsprungs — a fortiori tot), H-12b, H-13b, H-15b,
    H-16b, H-17b (Venue-Fingerprint-Tradability), H-20b, H-24b.
11. **Konditionale GPU-Scan-Folgekandidaten, nie registriert:** DSM-02
    (Memory-Horizon-Ablation der Trade-Tape-Grammatik) und DSM-04
    (Cross-Symbol-Zero-Shot-Universalitaet), beide vorgemerkt seit dem
    H-15-WEITER (GL-021), aber durch dieses WEITER NICHT automatisch
    ausgeloest.
12. **Cascade-Module C-27/C-28/C-29/C-39/C-30 (Kaskaden-Cockpit CS-06,
    seismisch inspiriert)** bleiben im urspruenglichen PRD-PARK-Register
    stehen, an einen Recording-Vorlauf mit ausreichend Bulk-Kaskaden
    gebunden — in der Scinance-2.0-Registry (H-01..H-26) bislang NIE
    aufgegriffen; ob/wann eine Pre-Registration erfolgt, ist offen.
13. **C-40 (RPI Hidden-Liquidity), C-02 (SpikeWavformer-Effizienz-Claim),
    C-43 (Conformal Prediction als Enabler)** — allesamt im
    PRD-PARK-Register mit klar benannten Entsperr-Bedingungen, aber ohne
    Fortschritt seit FINAL_PRD; die C-36-Recording-Engine (Bybit-eigene
    rpi/insurance-Stroeme) blieb laut GL-004 defekt bzw. wird gemaess
    DEC-43 nicht repariert (der Harvester deckt die relevanten Stroeme
    inzwischen anderweitig ab).

---

## F. DATENBESTAND

### F.1 Rohdaten-Stroeme im Data-Harvest-Baum (Stand 2026-08-10, DATA_INVENTORY;
punktuelle Updates aus spaeteren DECs vermerkt)

| Strom | Abdeckung | Bewertung |
|---|---|---|
| `bybit/publicTrade` BTC/ETH/XRP/SOL/BNB | 2020-03-25 (BTC) .. heute, LUECKENLOS, 5 Symbole, 5-6 Jahre | Hauptbefund: das eigentliche Fundament des Programms — von keiner Hypothese vor H-19+ genutzt |
| `bybit/orderbook` (L2) BTC/ETH | 961/530 Tage seit 2023-01-18, 74%/41% Abdeckung | Format-Bruch: `orderbook.500` (Snapshot-Aera, bis 2025-08/2024-05) vs. `orderbook.1000` (Delta-Aera, live ab 2026-06); WP-1-Zensus bestaetigt: schon die Snapshot-Aera ist Snapshot+Delta (~0,4-1,3 GB/Tag), nicht reine Snapshots |
| `bybit/orderbook` SOL/BNB/XRP | nur 35 Tage | zu duenn fuer L2-Hypothesen |
| `bybit/tickers` | 3.751 Symbole, 43 Tage; enthaelt seit Harvester-WP-12/DEC-08 auch die Bybit-OPTIONS-Ticker (`option_per_strike_tickers`), NICHT in eigenem Strom-Namen, sondern neben den Perp-Tickern (DEC-46-Korrektur) | markPrice/openInterestValue nur als Delta (nur geaenderte Felder) — Premium-Index nur per zustandsbehaftetem Merging rekonstruierbar |
| `bybit/rest.fundingRate` | 113 Tage (ab 2026-03-19) | war der praezise lokalisierte H-11-Blocker (heute geloest via Bar-Cache-Route) |
| `bybit/rest.openInterest` | 113 Tage | |
| `bybit/allLiquidation` | 43 Tage (BTC/ETH), 35 (Rest) | Blocker fuer H-21 (>=90 Tage/Fenster noetig) |
| `bybit/insurance` | 43 Tage | Kaskaden-N-Floor (>=30 Events) weiter offen |
| `binance/publicTrade` | BTC 519 Tage (ab 2025-01-01), uebrige 4 Symbole je 128 Tage (ab ~2026-03-27, nach Backfill DEC-28) | ab 2026-03-27 vollstaendig fuer Cross-Venue |
| `binance/orderbook` | 4 Symbole 106 Tage, BTC nur 23 Tage (luecken) | Cross-Venue-L2 nur eingeschraenkt |
| `deribit/publicTrade` BTC-/ETH-PERPETUAL | je 126 Tage (ab 2026-03-27, nach Backfill DEC-28) | ok fuer Cross-Venue-Fenster; RV-Quelle fuer H-26 |
| `deribit/dvol` BTC+ETH | 112 Tage (Stand 2026-08-10), waechst kalendarisch | IV-Quelle fuer H-26; Manifest-DONE-Luecke (s. E.2) |
| `deribit/markprice.options` | btc_usd/eth_usd je 43 Tage (ab 2026-06-16) | waechst kalendarisch; H-13-Entsperrung offen |
| `deribit/tickers` | 5.964 Symbole, ~38 Tage | volle Optionskette per Strike inkl. Greeks — reich, aber jung |
| `bitmex/publicTrade` XBTUSD | nur 112 Tage (2026-03-19..2026-08-01) | die in aelteren Docs genannte 2014er-Tiefe existiert NICHT |
| `tardis/options_chain` | 2 Tage ueber 3 Monate | 1-Tag-pro-Monat-Sampling, Options-Chain-Kandidaten damit endgueltig tot |
| Deribit-Alt-Streams "BTC"/"ETH" | 2026-03-19..2026-06-24, vor der Umbenennung zu "BTC-PERPETUAL" | ~9 Tage Ueberlappung mit der neuen Benennung; musste in H-14/H-17-Loadern vereinigt werden |

### F.2 Abgeleitete Speicher (im Scinance-2.0-Repo selbst gebaut, read-only auf den Harvest-Baum)

- **WP-0 Bar-Cache** (`data/barcache`, `src/bybit_edge/research/bar_cache.py`):
  deterministischer 1-Minuten-Bar-Cache, 5 Symbole, 10.054 Cache-Tage,
  14,4 Mio Minutenbars (Stand 2026-08-15). Spalten: `minute_idx, px_first,
  px_last, px_high, px_low, vol_buy, vol_sell, vol_total, n_trades, n_buy,
  n_sell, n_size_unparsed`. Ordnungs-unabhaengige Aggregate (kein Thread-
  Zwang noetig), SHA-256-Fingerabdruck je Symbol/Range, nur Manifest-DONE-
  Tage werden eingefroren. Fundament fuer H-19/H-20/H-22 (Return-Serie)/
  H-24.
- **WP-2 L2-Tilt-Store**: hash-gepinnte Ein-Pass-Extraktion des taeglichen
  Near-Touch-Tilts (±25 bps um Mid, 1-min-Abtastung, Tages-Median) fuer
  BTC (2 Fenster) + ETH (1 Bericht-Fenster). Vorleistung fuer H-22.
- **WP-4 Spread-Store** (`spread_1min`, ueber `extract_spread_window` in
  `c22`): deterministischer Minuten-Quote-Spread-Speicher, wiederverwendet
  aus der WP-2-Replay-Maschinerie, eigener Pfad (WP-2-Store nachweislich
  unberuehrt). Jede kuenftige Frage nach Buch-Enge/Spread-Regimen ist
  darauf in Minuten beantwortbar.
- **Options-Snapshots**: (a) `state/wp5_20260824/` — zwei vollstaendige
  Bybit-Options-Ketten-Snapshots (BTC 762, ETH 658 Symbole, SHA-256-gepinnt);
  (b) `data/optchain_snaps/` — laufender REST-Sampler (15-Min-Takt, seit
  2026-08-24 13:56 UTC) als Redundanz-Quelle, insbesondere kritisch fuer die
  ETH-Luecke 22.-27.08.; (c) `state/wp6_20260826/` +
  `state/wp6_ext_20260828/` — Minuten-Zeitreihen der Options-Quote-Breite
  um den Stresstag 19.08. (10.367 bzw. 26.390 Zeilen).
- **Harvest-Manifest**: `harvest_manifest.backup.sqlite` (aktuelle Wahrheit,
  vom Registrar naechtlich gepflegt, inkl. rueckwirkender DONE-Zeilen fuer
  `deribit/tickers`, `markprice.options`, `orderbook`) vs. die alte
  `harvest_manifest.sqlite` (eingefrorene Windows-Aera OHNE Registrar-
  Zeilen). Scinance-Resolver bevorzugt seit DEC-50 ueberall die Backup-
  Datei.

### F.3 Hardware

- **Nutzer-Maschine (alle T2/T3-Laeufe, insb. alle GPU-Hypothesen H-14..
  H-18/H-23):** RTX 5060 Ti (Blackwell-Architektur), CUDA 12.8+/PyTorch
  2.7+, 82 GB RAM, Windows. Einzelne GPU-Wellen-Laeufe erreichten bis zu
  ~180 h GPU brutto (H-15) bzw. ~59 h (H-17), verteilt ueber mehrere
  Checkpoint-Sessions und Neustarts.
- **Sandbox/Orchestrator-Umgebung:** kein torch, keine GPU — reine CPU-
  Ausfuehrung fuer T0/T1-Tests, Orchestrierung und alle CPU-Hypothesen
  (H-01..H-13, H-19..H-26 ausser den GPU-Wellen). Jeder GPU-Lauf ist
  zwingend ein lokaler, unbeaufsichtigter Overnight-/Mehrtage-Lauf auf der
  Nutzer-Maschine mit Checkpoint/Resume-Pflicht.

---

*Ende ERKENNTNIS_KOMPENDIUM.md — zusammengestellt am 2026-09-02 aus dem
vollstaendigen Bestand von `scinance2-impl/state/` (hypothesis_registry.md,
gate_log.md, decisions.md sowie allen Wellen-/WP-Befunddokumenten),
`FINAL_PRD.md` und den vier Vorgaenger-Rahmenwerken. Nach Registry-
Disziplin gilt: diese Zusammenfassung ersetzt keine Primaerquelle — im
Zweifel gilt der woertliche Text in `state/hypothesis_registry.md` und
`state/gate_log.md`.*
