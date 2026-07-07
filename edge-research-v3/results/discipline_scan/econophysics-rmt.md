# DISCIPLINE-SCAN — econophysics-rmt

**Fachgebiet:** Random Matrix Theory / Spektralanalyse von Korrelationsmatrizen
**Stand:** 2026-07-07, Datenbasis: `results/audit_inventory.md` (dokumentiert, nicht live verifiziert)

---

## Schritt 1 — Methodenrecherche (Pflicht)

Recherche via WebSearch über die vier Startpunkt-Methoden der Rollen-Datei
(MP-Denoising, λ1-Anteil, IPR-Eigenvektor-Lokalisierung, Tracy-Widom) hinaus. Sieben
zusätzliche Kandidaten geprüft, mit Aufnahme-/Verwerfungsgrund:

1. **Rotationally-Invariant-Estimators (RIE) / Nichtlineares Shrinkage
   (Ledoit-Péché, Bun-Bouchaud-Potters/QuEST)** — *AUFGENOMMEN.* Aktuelle Literatur
   (u. a. "Quantifying the information lost in optimal covariance matrix cleaning",
   2024) zeigt, dass reine MP-Schwellen-Truncation Information verschenkt; RIE
   verändert nur die Eigenwerte, nicht die Eigenvektoren, und ist informations-
   theoretisch optimaler. Übernommen als Cleaning-Methode in IC-RMT-1 statt naiver
   Schwelle (vermeidet zusätzlich das GL-012-Muster: eine hart-kodierte Schwelle statt
   einer datengetriebenen Referenzverteilung).
2. **Power-law/Lévy-stabile Random-Matrix-Ensembles (Free Random Lévy Matrices,
   Biroli/Bouchaud/Potters; Lévy-Matrix-Spektraltheorie)** — *AUFGENOMMEN.*
   Krypto-Returns/Liquidationsintensitäten sind bekannt fat-tailed; die
   Standard-Gaussian-Wishart-MP-Referenz kann fehlspezifiziert sein. Eigener Vorschlag
   IC-RMT-3 prüft das explizit als Alternative zur naiven MP-Null in IC-RMT-1.
3. **ResNet-Hybrid-ML-Denoising von Kovarianzmatrizen** (arXiv 2510.19130,
   Krypto-Portfolio-Anwendung) — *VERWORFEN.* Deep-Learning-Layer über der
   Kovarianzschätzung überschneidet sich methodisch mit dem gefallenen
   Vol-Stack-Anker (H-02/C-42, LightGBM/HAR, 0/5 Symbole bestanden OOS-R²), zusätzlich
   GPU-lastig entgegen der CPU-Faustregel für RMT-Methoden. Nicht adoptiert.
4. **Dynamische/rollierende Eigenwert-Trajektorien-Verfolgung mit
   Changepoint-Erkennung auf λ1(t)** — *TEILWEISE VERWORFEN als eigener IC.* Sobald
   man einen Changepoint auf der *skalaren Zeitreihe* λ1(t) sucht, wird die Frage zu
   einer Einzelserien-Zeitdynamik-Frage — das ist C-08-BOCPD-Territorium, nicht
   RMT-Querschnitt (siehe Abgrenzungsprüfung in der Rollen-Datei). Rollierendes
   Neu-Schätzen der Matrix bleibt aber als Monitoring-Komponente *innerhalb* von
   IC-RMT-1 erhalten (kein eigener IC, um nicht in C-08-Nähe zu geraten).
5. **Implied-Volatility-Surface-RMT/PCA** (Cont/Fonseca-Linie, Aktien-IV-Surface-
   Literatur) — *AUFGENOMMEN.* Bisher nirgends in den drei Wellen auf die
   Options-Surface angewendet; orthogonal zu Preis-Returns. Basis für IC-RMT-4.
6. **Minimum-Spanning-Tree / hierarchisches Clustering aus der Korrelationsmatrix**
   (Mantegna 1999) — *NICHT ADOPTIERT, aber vielversprechend.* Das ist im Kern
   Graphentheorie auf einer Distanzmatrix, nicht Spektralanalyse → siehe
   `Cross-Domain-Hinweis` unten, gehört ins `network-topology`-Ressort.
7. **Free Probability / rechteckige freie Faltung** für Matrizen ungleicher Dimension
   (z. B. Cross-Exchange-Universum mit unterschiedlicher Symbolzahl je Börse) —
   *AUFGENOMMEN als Hilfstechnik*, nicht als eigener IC — relevant für IC-RMT-2, falls
   sich die Börsen-Universen (Deribit nur BTC/ETH vs. bybit/binance 5 Symbole)
   unterscheiden.

---

## Schritt 2-4 — IC-Vorschläge

### IC-RMT-1 — Multi-Feature-RIE-Denoising als Risiko-Overlay
Fachgebiet: Econophysics/RMT
Kernfrage: Enthält die Multi-Feature-Korrelationsmatrix (Returns, Funding-Änderungen,
OI-Änderungen, Liquidations-Intensität über 5 Symbole) im Basis-Bestand-Fenster mehr
signifikante (Tracy-Widom-getestete) Eigenwerte außerhalb des MP-Bulks, als ein
Gaussian-Wishart-Null-Ensemble gleicher Dimension erwarten lässt — und lässt sich der
RIE-gereinigte λ1-Anteil als vorlaufender Regime-/Risiko-Indikator zur Sizing-Anpassung
bestehender Exposures nutzen?
Erwogene Alternativen: siehe Schritt 1, Punkte 1 (RIE, adoptiert als Cleaning-Methode),
3 (ResNet-ML, verworfen: H-02-Nähe/GPU), 4 (rollierende λ1-Trajektorie, als
Monitoring-Feature integriert statt eigener IC, um C-08-Nähe zu vermeiden).
Datenbindung: Basis-Bestand 2026-03-27…heute (audit_inventory.md §1.3 Punkt 1,
SOFORT NUTZBAR laut Dokumentation, nicht live verifiziert). Stündliche Aggregation:
bybit `publicTrade` (Returns), `rest.fundingRate`, `rest.openInterest`, Binance
`liquidationSnapshot` (Basis-Bestand-Teil, NICHT Bybit `allLiquidation` — das ist nur
~3 Wochen Live-only, siehe IC-RMT-3 für dessen Nutzung) — je 5 Symbole → N=20 Spalten,
T≈2440 Stunden (~102 Tage) → T/N≈122, komfortabel über der 10er-Faustregel.
Nullhypothese/Referenzverteilung: Marchenko-Pastur-Bulk (Q=T/N≈122) für die
Basis-Nullhypothese; Tracy-Widom-Fluktuationsstatistik für λ1 statt harter Schwelle;
RIE (Ledoit-Péché/Bun-Bouchaud-Potters) als Eigenwert-Cleaning statt naiver Truncation.
Nicht-Redundanz: Kein H-04-Reprise (H-04 ist paarweiser zeitverschobener Lead-Lag,
hier volles gleichzeitiges Spektrum über N=20 Merkmalsspalten). Keine C-06-Kollision
(Ergänzung 1 in audit_inventory.md: Eigenwert-Spektrum ≠ Cross-Sectional-Z, explizit
nicht durch H-07/H-08 gesperrt). Keine Hawkes/Natural-Time-Überschneidung (Querschnitt
über Instrumente, nicht Punktprozess-Zeitdynamik einer Einzelserie — Abgrenzungsprüfung
der Rollen-Datei bestanden).
Friktions-Rolle: Risiko-Overlay (Sizing-Multiplikator auf bestehende Positionen bei
λ1-Anteil-Spike) — keine neue Round-Trip-Position, umgeht die Friction-Wand strukturell.
Rechenaufwand: CPU.
Cross-Domain-Hinweis: Ein aus derselben Matrix ableitbarer Minimum-Spanning-Tree/
Cluster-Dendrogramm (Mantegna) ist Netzwerktheorie, nicht Spektralanalyse — Hinweis an
`network-topology`.
Offene Punkte für data-feasibility-scout: Ist Binance `liquidationSnapshot` und
`rest.openInterest` im Basis-Bestand-Fenster tatsächlich lückenlos (Manifest-Check)?
Der 30-Tage-Rolling-Caveat für OI (DATASET.md §9.6) kann das nutzbare Fenster für die
OI-Spalte auf einen kürzeren Zeitraum verkürzen als die übrigen drei Feature-Typen —
falls ja, T/N-Rechnung neu ziehen (getrennte Sub-Fenster je Feature-Typ prüfen).

### IC-RMT-2 — Cross-Exchange-Fragmentierungsmatrix
Fachgebiet: Econophysics/RMT
Kernfrage: Zeigt die IPR-lokalisierte Struktur der Cross-Exchange-Return-
Korrelationsmatrix (BTC-PERP und ETH-PERP gleichzeitig auf bybit, binance,
deribit-perpetual) einen stabilen dominanten "gemeinsamer-Preis"-Modus nahe
Eigenwert≈N, oder treten lokalisierte, börsenspezifische Restmoden auf, die auf
strukturelle (nicht arbitrierte) Fragmentierung hindeuten?
Erwogene Alternativen: siehe Schritt 1, insbes. Punkt 7 (rechteckige freie Faltung,
falls Symbolzahl je Börse divergiert — hier symmetrisch mit 2 Symbolen × 3 Börsen
umgangen); Punkt 2 (Lévy-RMT) hier nicht nötig, da Returns (anders als Liquidationen)
weniger extrem fat-tailed sind — bewusst getrennt von IC-RMT-3 gehalten, um
FDR-Familien nicht zu vermischen.
Datenbindung: Basis-Bestand, Minutenbars für BTC-PERP/ETH-PERP auf bybit, binance,
deribit (N=6 Spalten: 2 Symbole × 3 Börsen). Rollierende Tagesfenster (N=6, T=1440
Minuten/Tag → T/N=240) statt eines einzigen Panels über die volle Fensterlänge, um
Nicht-Stationarität zu adressieren.
Nullhypothese/Referenzverteilung: MP-Bulk je rollierendem Tagesfenster (Q=240); IPR-
Nullverteilung für Eigenvektor-Lokalisierung (Marktmodus vs. Exchange-Restmodus).
Nicht-Redundanz: Orthogonal zu H-04 (zeitverschobener paarweiser Lead-Lag) — hier
gleichzeitige Multi-Venue-Kopplungsstärke, keine Zeitverschiebung. Keine
C-06-Kollision (kein Cross-Sectional-Z).
Friktions-Rolle: Reine Mess-/Explorationsfrage nach Fragmentierungskapazität,
capital_free. Falls daraus ein handelbares Arbitragesignal folgt, ist das gemäß §2
Punkt 2 explizit eine SEPARATE Folge-Hypothese — hier bewusst kein Handels-Claim.
Rechenaufwand: CPU.
Offene Punkte für data-feasibility-scout: Deribit führt nur BTC/ETH (kein SOL/BNB/XRP)
— Universum bewusst auf 2 Symbole begrenzt, nicht auf 5 erweiterbar ohne
asymmetrische Matrixbehandlung. Uhr-Synchronität zwischen Börsen-Zeitstempeln bei
Minutenbars prüfen (Rundungsfehler/Offsets könnten Scheinkorrelationen erzeugen).

### IC-RMT-3 — Lévy-stabile RMT-Nullverteilung für liquidationsgetriebene Korrelationen
Fachgebiet: Econophysics/RMT
Kernfrage: Passt die empirische Eigenwertverteilung der liquidationsintensitäts-
gewichteten Korrelationsmatrix (5 Symbole) besser zu einer Lévy-stabilen/Free-Random-
Lévy-Matrix-Nullverteilung als zur Standard-Gaussian-Wishart-MP-Verteilung — d. h. ist
die MP-Referenz für Krypto-Liquidationscluster (bekannt fat-tailed) fehlspezifiziert
und verzerrt das Denoising in IC-RMT-1?
Erwogene Alternativen: siehe Schritt 1 Punkt 2 (Lévy/Free-Random-Matrices, hier
zentraler Gegenstand); Punkt 3 (ResNet-ML) erneut verworfen aus denselben Gründen.
Datenbindung: Binance `liquidationSnapshot`, Basis-Bestand (SOFORT NUTZBAR laut Audit
— bewusst NICHT Bybit `allLiquidation`, das nur ~3 Wochen Live-Historie seit ~2026-06-16
hat und für eine stabile Tail-Index-Schätzung zu kurz wäre). Stündliche
Liquidations-Notional-Summen je Symbol, N=5, T≈2440 Stunden → T/N≈488.
Nullhypothese/Referenzverteilung: Zwei konkurrierende Nullmodelle im Vergleich:
(a) Gaussian-Wishart-MP, (b) Lévy-stabiler Free-Random-Matrix-Kern
(Biroli/Bouchaud/Potters) mit aus den Liquidations-Notionals selbst geschätztem
Tail-Index α.
Nicht-Redundanz: Keine C-14/CS-01-Wiederholung — Hawkes-Branching-Ratio ist eine
Punktprozess-/Zeitdynamik-Aussage über Interarrival-Zeiten EINER Ereignisreihe; hier
ist es eine Querschnitts-Kovarianzstruktur über 5 gleichzeitige Reihen. Auch keine
Überschneidung mit der Insurance-Fund-Kaskaden-Schwelle (C-27/28/29, zielt auf
Ereignisdichte ~7/h) — hier geht es um Ko-Bewegung, nicht Ereigniszählung.
Friktions-Rolle: Methodik-Validierung / Risiko-Overlay-Zulieferer — kein eigener
Handels-Claim; korrigiert ggf. die Referenzverteilung für IC-RMT-1.
Rechenaufwand: CPU (Tail-Index-Schätzung + Eigenwert-Fit; explizit kein Deep Learning
— Abgrenzung zum verworfenen ResNet-Ansatz).
Cross-Domain-Hinweis: Die Tail-Index-Schätzung (Hill-Estimator o. ä.) überschneidet
sich methodisch mit `evt-actuarial` — Abstimmungsbedarf in DECONFLICT, damit der
Tail-Index nicht doppelt und mit unterschiedlichen Konventionen geschätzt wird.
Offene Punkte für data-feasibility-scout: Coverage-Lücken von Binance
`liquidationSnapshot` im Basis-Bestand-Fenster real prüfen. Stundenbuckets können viele
Nullen enthalten (Liquidationen sind Punktereignisse) — falls die Tail-Index-Schätzung
darunter leidet, Tagesaggregation als Fallback (T/N fällt auf ~14, noch über der
10er-Grenze, aber knapper).

### IC-RMT-4 — Options-IV-Surface-Spektrum als Cross-Sectional-Snapshot
Fachgebiet: Econophysics/RMT
Kernfrage: Zerfällt die Korrelationsmatrix der Mark-IV-Änderungen über alle aktiven
Strikes/Tenors der Deribit-Options-Surface (BTC, ETH) in einen dominanten
"Level"-Modus (Parallelverschiebung der gesamten Surface) plus wenige lokalisierte
"Skew/Term-Structure"-Moden — analog zur Aktien-IV-Surface-RMT-Literatur — oder liegt
die gesamte Surface im MP-Bulk (kein strukturiertes Signal)?
Erwogene Alternativen: siehe Schritt 1 Punkt 5 (IV-Surface-RMT/PCA, hier zentraler
Gegenstand, bisher nirgends im Programm auf Options-Daten angewendet).
Datenbindung: Deribit Live (`markprice.options`, SRC-11), Fenster ab ~2026-06-16
(~3 Wochen zum Audit-Datum, SOFORT NUTZBAR laut Audit als Live-only-Fenster).
Intraday-Minutenraster über alle aktiven Strikes je Tenor; N = Anzahl aktiver Strikes
(grob geschätzt 40-150 je Expiry, NICHT verifiziert), T = Minutenticks im 3-Wochen-
Fenster (~30.000) — T/N-Verhältnis muss vor Pre-Registration am realen Feed geprüft
werden.
Nullhypothese/Referenzverteilung: MP-Bulk + IPR-Lokalisierungstest je Eigenvektor
(Level- vs. Skew-Modus-Unterscheidung über den IPR-Wert).
Nicht-Redundanz: Orthogonal zu C-33 VRP (IV−RV-Spread-Level, PARK laut Ergänzung 2 in
audit_inventory.md) — hier geht es um die Korrelationsstruktur ÜBER Strikes an einem
Zeitpunkt, nicht um den Spread-Level selbst. Keine Überschneidung mit C-11/C-12
(TDA/RQA, PARK durch H-02) — kein RV-Vorhersage-Anker involviert.
Friktions-Rolle: capital_free Mess-Frage / potenzieller Risiko-Overlay für
Options-Sizing — explizit KEIN Round-Trip-Claim in dieser Runde.
Rechenaufwand: CPU.
Cross-Domain-Hinweis: Formvergleich des Skew-Eigenvektors über die Zeit grenzt an
`evt-actuarial` (Tail-Form der risikoneutralen Verteilung) — Abstimmung in DECONFLICT
empfohlen.
Offene Punkte für data-feasibility-scout: **Data-gated für Mehrregime-Aussagen** —
das Live-Fenster deckt bislang nur ~3 Wochen / EIN Marktregime ab, keine
Crash-/Stress-Episode. Sofort testbar NUR als Einzel-Snapshot-/Einzelregime-Aussage,
NICHT als Mehrregime-Vergleich. Entsperr-Bedingung für die Mehrregime-Erweiterung:
Live-Fenster wächst auf ≥ 3 Monate. Zusätzlich: tatsächliche Anzahl aktiver Strikes je
Zeitpunkt am realen Feed verifizieren (die N-Schätzung oben ist ungeprüft) und Tardis
Monats-Stichproben NICHT als Ersatz für ein tägliches Panel missverstehen (audit_
inventory.md §1.4 — Tardis-Chain ist strukturell 1 Tag/Monat, kein Panel).

---

## Selbstkill-Check
Alle vier Vorschläge bestanden die T/N≥10-Faustregel für ihr jeweiliges Kern-Fenster
(IC-RMT-1: ~122, IC-RMT-2: 240 je Tagesfenster, IC-RMT-3: ~488 stündlich bzw. ~14 als
Tagesfallback, IC-RMT-4: am realen Feed noch zu verifizieren — deshalb dort explizit
als Offener Punkt markiert, nicht verworfen). Keiner der vier ist eine Umformulierung
von C-14/C-30 (Punktprozess-/Zeitdynamik-Fragen) — alle vier sind explizit
Querschnitts-/Kopplungsstruktur-Fragen über mehrere gleichzeitige Serien.
