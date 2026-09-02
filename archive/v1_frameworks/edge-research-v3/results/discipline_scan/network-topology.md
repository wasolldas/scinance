# DISCIPLINE-SCAN — network-topology

**Fachgebiet:** Netzwerktheorie/Graphentheorie über das volle Multi-Asset-/Multi-Exchange-Universum
**Stand:** 2026-07-07. Datenbasis: `reference/DATASET.md` (Snapshot 2026-07-02, NICHT live verifiziert,
siehe `results/audit_inventory.md`). Kein Code, keine Backtests — reine Pre-Registrations-Vorbereitung.

---

## Schritt 1 — Methodenrecherche (Pflicht, über den Werkzeugkasten der Rollen-Datei hinaus)

Recherchiert per WebSearch (Quellen unten je Fund zitiert). Über die Startpunkte (MST, PMFG, Zentralität,
Louvain, Transfer-Entropy-Kanten) hinaus geprüft:

1. **Threshold-Netzwerke (TN)** als Alternative zu MST/PMFG — behalten Kanten oberhalb einer
   Korrelationsschwelle statt eines Baum-/Planaritäts-Zwangs; können isolierte Knoten/Komponenten
   erzeugen (im Gegensatz zum MST, der immer zusammenhängend bleibt). Quelle: ScienceDirect
   "Network analysis of a financial market based on genuine correlation and threshold method";
   ScienceDirect "Constructing financial network based on PMFG and threshold method". **Aufgenommen**
   als Kontrastmethode in IC-NET-1 (MST vs. TN als Robustheits-Check derselben Frage).
2. **Graph-Laplacian / algebraische Konnektivität (Fiedler-Wert λ₂(L))** — jüngste Literatur (PMC 2025,
   "Indicator from the graph Laplacian of stock market time series cross-sections can precisely
   determine the durations of market crashes"; ResearchGate "Algebraic connectivity and graph
   robustness") zeigt fallende algebraische Konnektivität als Fragilitäts-/Crash-Dauer-Signal.
   **Aufgenommen** in IC-NET-1 als Aggregatmaß — strukturell näher an RMT (Eigenwert-basiert), daher
   explizite Abgrenzung nötig (siehe Feld unten).
3. **Katz-Zentralität und PageRank-Zentralität** als Alternativen zu Grad-/Eigenvektor-/Betweenness-
   Zentralität — Katz korreliert stärker mit Ansteckungsfähigkeit in unbesicherten Interbank-Netzen,
   PageRank stärker mit Zins-Spreads in besicherten Netzen (Springer/Annals of Operations Research,
   "Early warning of systemic risk in global banking"). **Aufgenommen** als Zentralitäts-Variantenset
   in IC-NET-2/IC-NET-3.
4. **DebtRank / rekursive Feedback-Zentralität** (Battiston et al., Nature Sci. Rep. "DebtRank: Too
   Central to Fail?") — misst rekursiv den Ansteckungs-Impact über bilaterale Exposure-Matrizen.
   **Verworfen**: braucht eine Bilanz-/Exposure-Matrix (wer schuldet wem wie viel), die für Perp-Futures-
   Korrelationsnetze schlicht nicht existiert (keine Kreditbeziehungen zwischen BTC und ETH). Als
   `Cross-Domain-Hinweis` an `mechanism-design` weitergegeben (Insurance-Fund/ADL-Exposure-Struktur ist
   näher an einer echten Exposure-Matrix als ein Korrelationsnetz).
5. **Core-Periphery-Blockmodelle** (arXiv 2601.00395, "Core-Periphery Dynamics in Market-Conditioned
   Financial Networks: A Conditional P-Threshold Mutual Information Approach") — Alternative zu
   Louvain-Modularität für asymmetrische Hub/Peripherie-Struktur statt symmetrischer Cluster.
   **Aufgenommen** in IC-NET-2 als Variante zur Fragmentierungsfrage (welche Exchange ist Kern, welche
   Peripherie).
6. **Triangulated Maximally Filtered Graph (TMFG)** — schnellere Big-Data-Alternative zu PMFG.
   **Verworfen**: für N≤13 (unser gesamtes erreichbares Universum) kein Vorteil gegenüber PMFG, TMFG
   lohnt sich erst bei hunderten Knoten (ResearchGate, "Network Filtering for Big Data: Triangulated
   Maximally Filtered Graph").
7. **Dynamische/multiplexe Netzwerkmodelle** (Preis-/Funding-/OI-Serien als getrennte Layer desselben
   Graphen) — **aufgenommen** in IC-NET-3 als Weg, die Knotenzahl über reine Cross-Asset-Korrelation
   hinaus zu erhöhen, ohne auf Cross-Exchange zurückzugreifen.
8. **Netzwerk-Rekonfigurations-/Edge-Turnover-Rate** über rollierende Fenster als Aggregatmetrik (statt
   eines einzelnen Hub-Zentralitätswerts) — **aufgenommen** in IC-NET-1, um die GL-012-Degenerations-
   falle bei N=5 zu umgehen (siehe unten).

Cross-Domain-Funde ohne eigene Verwendung: DebtRank (→ mechanism-design, s.o.); ein "Navier-Stokes-
Framework für Netzwerk-Kontagion" (arXiv 2510.19630) wirkt eher wie PDE-basierte Physik als
Graphentheorie — nicht weiterverfolgt, aber als Kuriosum vermerkt, falls ein zukünftiger
Fluid-Dynamics-Agent existiert.

---

## Feasibility-Vorbemerkung (verbindlich, GL-012-Analogie)

**N=5 (reines Cross-Asset-Netz, Basis-Bestand 2026-03-27…heute, ~102 Tage lückenlos) ist für die
meisten Netzwerk-Metriken strukturell degeneriert:**
- Ein MST auf 5 Knoten hat *immer* genau 4 Kanten (N−1) — die Baumstruktur selbst trägt kaum
  Freiheitsgrade; "wer ist Hub" reduziert sich bei einer sternförmigen MST fast auf eine
  Ein-Knoten-Aussage (Risiko: kollabiert in eine H-04-artige Paar-Aussage, wenn man nur "BTC ist immer
  Zentrum" behauptet).
- Community-Detection/Louvain-Modularität bei N=5 hat nur eine Handvoll möglicher Partitionen
  (im Wesentlichen 2^(5-1)/Symmetrien ≈ wenige eindeutige Bipartitionen) — keine belastbare
  Modularitäts-Landschaft, keine sinnvolle Nullverteilung per Bootstrap. **Deshalb wird
  Community-Detection hier NICHT als Cross-Asset-IC vorgeschlagen**, sondern ausschließlich im
  Cross-Exchange-Netz (N≈12-13, IC-NET-2), wo die Partitions-Anzahl real informativ ist.
- Was bei N=5 NICHT degeneriert: Aggregatmetriken, die über die Zeit variieren, ohne von der
  Kombinatorik einzelner Knoten abzuhängen — Edge-Turnover-Rate zwischen aufeinanderfolgenden
  MST-Fenstern, algebraische Konnektivität λ₂(L), mittlere Kantengewicht-Dichte. Diese sind die
  einzigen bei N=5 vertretbaren Cross-Asset-Metriken (→ IC-NET-1 ist entsprechend eng geschnitten).

**Stress-Ground-Truth ist unabhängig davon knapp:** `allLiquidation`/`insurance`/`adlAlert` sind
Bybit-Live-Streams erst ab ~2026-06-16 (~3 Wochen zum Audit-Datum) — für "Vorher/Nachher"-Tests um
Stress-Episoden strukturell zu wenig Ereignisse (Analogie zum C-27/28/29-Vorlauf bis Aug.-Okt. 2026,
`audit_inventory.md` Zeile 53). Jeder Vorschlag unten trennt daher explizit "Struktur-Konstruktion
sofort möglich" von "Stress-Validierung data-gated".

---

### IC-NET-1 — Cross-Asset-Netzwerk-Rekonfigurationsrate als Regime-Frühwarnfilter
Fachgebiet: Netzwerktheorie/Graphentheorie
Kernfrage: Steigt die Rekonfigurationsrate des Cross-Asset-Korrelationsnetzes (Kanten-Turnover
zwischen aufeinanderfolgenden rollierenden MST-/Threshold-Netz-Fenstern; alternativ fallende
algebraische Konnektivität λ₂(L)) messbar VOR Liquidations-/Insurance-Stress-Episoden, über alle 5
Symbole (BTC/ETH/SOL/BNB/XRP)?
Erwogene Alternativen: (1) reine MST-Hub-Zentralität — verworfen, bei N=5 fast Paar-Aussage
(Selbstkill-Risiko H-04); (2) Louvain-Community-Detection — verworfen, bei N=5 strukturell
degeneriert (siehe Feasibility-Vorbemerkung), verschoben nach IC-NET-2; (3) PMFG statt MST — bei N=5
liefert PMFG praktisch densel­ben vollständigen Graphen wie die Korrelationsmatrix selbst (zu wenig
Filterung bei so kleinem N), daher MST + Threshold-Netz als Kontrastpaar bevorzugt; (4) TMFG —
verworfen, kein Vorteil bei N≤5 (siehe Schritt 1 Punkt 6).
Datenbindung: Bybit `publicTrade` Returns (1min/5min-Aggregation), Basis-Bestand 2026-03-27…heute,
alle 5 Symbole, lückenlos laut DATASET.md §5 (NICHT live verifiziert). Rollierende Korrelationsfenster
z.B. 6h/24h, MST + Threshold-Netz (ρ-Schwelle vorab fixieren) + λ₂(L) pro Fenster.
Ground-Truth „Stress": Bybit `allLiquidation`-Intensität > 90. Perzentil (rollierend) ODER
`insurance`-Fund-Drawdown-Event, beide aus Live-Stream ab ~2026-06-16.
Nicht-Redundanz zu H-04/econophysics-rmt: H-04 testete ein gerichtetes Paar (BTC→ETH TE); hier ist die
Messgröße eine Aggregat-Eigenschaft des gesamten 5-Knoten-Graphen (Kantenmenge, nicht ein Kantenwert).
Gegenüber econophysics-rmt: λ₂(L) ist eine Laplacian- (Grad-minus-Adjazenz-)Größe der GEFILTERTEN
Netzwerkstruktur (MST/Threshold), RMT analysiert die vollen Eigenwerte der ROHEN Korrelationsmatrix —
verwandt, aber verschiedene Matrix; Abstimmung mit `econophysics-rmt` über identische Return-Fenster-
Definition nötig, damit `registry-keeper` keine verdeckte Doppelzählung einsortiert.
Friktions-Rolle: Risiko-Overlay/Regime-Filter (capital_free Messfrage), keine eigenständige
Round-Trip-Strategie.
Rechenaufwand: CPU (networkx, N=5 trivial).
Offene Punkte für data-feasibility-scout: (a) exakte lückenlose Länge des Basis-Bestands ohne
Manifest-Zugriff nicht hart verifizierbar; (b) Stress-Ground-Truth nur ~3 Wochen — für ein sauberes
Vorher/Nachher-Fenster mutmaßlich zu kurz, explizit als **data-gated bis ausreichend Stress-Events
akkumuliert sind** markieren, nicht als "sofort testbar" einstufen.

---

### IC-NET-2 — Cross-Exchange-Fragmentierungs-Topologie (Community-Detection + Zentralität bei N≈12-13)
Fachgebiet: Netzwerktheorie/Graphentheorie
Kernfrage: Bildet sich im Netzwerk derselben 5 Symbole über bybit/binance/deribit(/bitmex) als
getrennte Knoten (N≈12-13) eine stabile Exchange-Cluster- oder Asset-Cluster-Struktur (Louvain-
Modularität bzw. Core-Periphery-Blockmodell), und verändert sich diese Cluster-Zusammensetzung
(Fragmentierung: Cross-Exchange-Kanten schwächer als Cross-Asset-Kanten) messbar vor bzw. während
Liquidations-/Funding-Dispersions-Stress?
Erwogene Alternativen: (1) DebtRank/Feedback-Zentralität — verworfen, braucht Exposure-/Bilanzmatrix,
die hier nicht existiert (→ Cross-Domain-Hinweis an mechanism-design); (2) reine Grad-Zentralität ohne
Community-Struktur — verworfen, beantwortet nicht die Fragmentierungsfrage (Kern des Vorschlags);
(3) Katz-/PageRank-Zentralität als Ergänzung statt Ersatz für Louvain — aufgenommen als
Robustheits-Check, welcher Knoten-Typ (Exchange vs. Asset) die höhere Zentralität trägt; (4) TMFG
statt PMFG bei N≈13 — geprüft, aber Vorteil erst ab deutlich höherem N, daher PMFG/Threshold-Netz
gewählt.
Datenbindung: `publicTrade` Returns Bybit (5 Perp) + Binance (5 Perp, aggTrades) + Deribit
(BTC-PERPETUAL, ETH-PERPETUAL) [+ BitMEX XBTUSD als 13. Knoten, falls Symbol-Mapping zu
BTCUSDT eindeutig ist], Basis-Bestand 2026-03-27…heute (laut DATASET.md je Quelle im Basis-Bestand
fertig). Rollierendes Korrelationsfenster, Louvain-Modularität + Core-Periphery-Blockmodell +
Katz/PageRank-Zentralität pro Fenster.
Ground-Truth „Stress": Funding-Rate-Dispersion über Exchanges (>90. Perzentil rollierend, aus
`rest.fundingRate`, im Basis-Bestand verfügbar — LÄNGERE Historie als die Liquidations-Streams,
daher bevorzugte Ground-Truth-Variante) ODER Bybit `allLiquidation` (nur ~3 Wochen, sekundär).
Nicht-Redundanz zu H-04/econophysics-rmt: kein Paartest — die Kernaussage ist eine Graph-Partitions-
Eigenschaft (welcher Cluster-Typ dominiert), die bei N=5 (IC-NET-1) strukturell nicht auswertbar wäre;
gegenüber econophysics-rmt: RMT auf 12-13×12-13-Korrelationsmatrix würde primär λ₁-Anteil/Markt-Modus
liefern, nicht die diskrete Cluster-Zugehörigkeit — beide Agenten sollten sich auf dieselbe Return-
Rohdatenbasis einigen, aber unterschiedliche Endpunkte (Eigenwert-Spektrum vs. Partitionsstruktur)
berichten.
Friktions-Rolle: Risiko-Overlay/Regime-Filter (capital_free), kein Handels-Claim.
Rechenaufwand: CPU (networkx/python-louvain, N≈13 trivial).
Cross-Domain-Hinweis: DebtRank/Feedback-Zentralität passt eher zu `mechanism-design` (ADL-/Insurance-
Fund-Exposure hat eine echte "wer trägt wessen Verlust"-Struktur, im Gegensatz zu einem
Korrelationsnetz).
Offene Punkte für data-feasibility-scout: (a) Symbol-Mapping BitMEX XBTUSD vs. BTCUSDT (gleiches
Underlying, andere Kontraktspezifikation) — muss geklärt werden, ob als 13. Knoten zulässig oder
methodisch verzerrend; (b) Deribit liefert nur BTC/ETH als Perp — die anderen 3 Symbole (SOL/BNB/XRP)
fehlen auf Deribit strukturell, Netz ist damit für diese 3 Symbole nur 2-Exchange (bybit+binance) tief,
nicht 3 — muss im Pre-Registration-Text als Asymmetrie explizit stehen, kein Fehler, aber
interpretationsrelevant.

---

### IC-NET-3 — Gerichteter Multiplex-Informationsfluss-Graph (Preis/Funding/OI als Netzwerk-Layer)
Fachgebiet: Netzwerktheorie/Graphentheorie
Kernfrage: Gibt es einen stabilen Netzwerk-Hub-KNOTENTYP (nicht ein einzelnes Knotenpaar) im
gerichteten Transfer-Entropy-Graphen über Preis-, Funding- und Open-Interest-Serien aller 5 Symbole
(bis zu N=15 Knoten: 5×Preis, 5×Funding, 5×OI) — z.B. "Funding-Knoten haben systematisch höhere
PageRank-/In-Degree-Zentralität als Preis-Knoten" — und ist dieser Netzwerkeffekt (viele gleichzeitige
gerichtete Kanten) robuster/größer als der isolierte BTC→ETH-Preis-Effekt aus H-04?
Erwogene Alternativen: (1) Einzelpaar-TE (BTC-Preis→ETH-Preis) — das IST H-04, explizit ausgeschlossen,
hier bewusst durch Multiplex-Graph mit Knotentyp-Aggregation ersetzt; (2) Katz-Zentralität statt
PageRank für die Hub-Typ-Frage — aufgenommen als Robustheits-Zweitmaß, da Katz stärker
kontagionssensitiv, PageRank stärker "Informationsfluss"-orientiert kalibriert ist (Quelle:
Annals of Operations Research, s. Schritt 1 Punkt 3); (3) Graph-Laplacian-Konnektivität für dieses
gerichtete Netz — verworfen, λ₂(L) ist für gerichtete Graphen nicht direkt definiert (asymmetrische
Adjazenzmatrix), stattdessen In-/Out-Degree-Verteilung; (4) DebtRank — verworfen wie in IC-NET-2
(keine Exposure-Matrix).
Datenbindung: Bybit `publicTrade` (Returns), `rest.fundingRate`, `rest.openInterest`, alle 5 Symbole,
Basis-Bestand 2026-03-27…heute. **Caveat OI:** laut audit_inventory.md strukturell nur ~30 Tage
Historie belastbar (Binance-OI-Caveat, evtl. auch Bybit betroffen — ungeklärt) — schränkt das
nutzbare Fenster für die OI-Layer auf die letzten ~30 Tage ein, während Preis/Funding den vollen
Basis-Bestand (~102 Tage) tragen könnten. Multiplex-Graph ist damit zeitlich durch die kürzeste Layer-
Historie (OI) gedeckelt, nicht durch die längste.
Ground-Truth „Stress": `allLiquidation`/`insurance` >90. Perzentil (Live, ~3 Wochen) — sekundär auch
Funding-Dispersion (>90. Perzentil, Basis-Bestand-Länge) als länger verfügbare Alternative.
Nicht-Redundanz zu H-04/econophysics-rmt: H-04 ist ein einzelner gerichteter Kantenwert
(BTC→ETH-Preis); hier ist die Messgröße eine Verteilungsaussage über ALLE gerichteten Kanten
gleichzeitig, aggregiert nach Knotentyp (Preis/Funding/OI) — fällt die Aussage auf ein einzelnes Paar
zurück, ist das automatischer Selbstkill (Rollen-Datei-Kriterium). Gegenüber econophysics-rmt: TE-Graph
ist gerichtet/nichtlinear-informationstheoretisch, RMT ist ungerichtet/linear-spektral — verschiedene
Fragestellung an denselben Rohdaten, Abstimmung über Fenster-Definition erforderlich.
Friktions-Rolle: Risiko-Overlay/Regime-Filter (capital_free), kein Handels-Claim — TE-Schätzung selbst
ist ohnehin nur als Existenzfrage zu verstehen (H-04-Lehre: reales Signal, 80× unter Friktionswand).
Rechenaufwand: CPU (TE-Schätzung für N≤15 mit z.B. `pyinform`/`JIDT`-Äquivalent ist bei Minuten-
Aggregation handhabbar; bei zu granularer Sekunden-Auflösung ggf. GPU-vorteilhaft für die
Permutations-Surrogate — vorsorglich als CPU|GPU-vorteilhaft-Grenzfall taggen).
Offene Punkte für data-feasibility-scout: (a) OI-Historientiefe für Bybit spezifisch prüfen (Caveat
im Audit bezieht sich primär auf Binance); (b) Anzahl nötiger Surrogat-Permutationen für ein N=15-Netz
gegen Rechenzeit-Budget abschätzen, bevor Pre-Registration die FDR-Familie fixiert.

---

## Zusammenfassung für Orchestrator

3 IC-Vorschläge, alle **capital_free Regime-/Frühwarnfilter**, keiner ein eigenständiger
Round-Trip-Trade. IC-NET-1 (Cross-Asset, N=5, eng auf degenerationsresistente Aggregatmetriken
geschnitten) ist die einzige Variante, deren Struktur-Konstruktion mit dem längsten verfügbaren
Fenster (Basis-Bestand, ~102 Tage) sofort möglich ist — aber Stress-Validierung data-gated (~3 Wochen
Liquidations-Historie). IC-NET-2 (Cross-Exchange, N≈12-13) ist die einzige Variante, bei der
Community-Detection/Zentralitäts-Kontraste nicht strukturell degeneriert sind — bevorzugte
Ground-Truth ist Funding-Dispersion (Basis-Bestand-lang) statt der kurzen Liquidations-Streams.
IC-NET-3 (Multiplex-TE-Graph) ist am rechenintensivsten und durch die kürzeste Layer-Historie (OI,
~30 Tage) gedeckelt.

**Cross-Domain-Hinweise:** DebtRank/rekursive Feedback-Zentralität passt eher zu `mechanism-design`
(ADL-/Insurance-Fund hat echte Exposure-Struktur). Abstimmungsbedarf mit `econophysics-rmt` auf
identische Return-/Funding-/OI-Fensterdefinitionen für alle drei ICs, damit `registry-keeper` getrennte
FDR-Familien (Struktur-/Partitions-Aussage vs. Spektral-Aussage) sauber zuweisen kann.
