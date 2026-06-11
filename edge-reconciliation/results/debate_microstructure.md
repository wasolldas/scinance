# Debatte: Mikrostruktur / Orderbuch / Toxic-Flow

**Cluster-Claims:** C-01 (OFI), C-03 (Iceberg/Queue-Replenishment), C-04 (Wavelet-Symlet-Denoising), C-06 (Shannon-Entropie), C-07 (Permutation Entropy), C-25 (Kyle's Lambda / VPIN Toxic Flow), C-40 (RPI Hidden Liquidity), CS-08 (Regime-konditioniertes Richtungs-Signal).
**Querschnitts-Claims (mitgeführt):** C-02 (SpikeWavformer Event-Ingestion), C-36 (F0 Fallback-Trigger / Recording-Infrastruktur).
**Stand:** 2026-06-11 · **Phase:** 4 — DEBATE

---

## Advocate

### Vorbemerkung — Verbindliche Randbedingungen, an denen ich mein Argument ausrichte

Drei harte Fakten aus dem Evidence-Register strukturieren jedes folgende Argument; ich gehe sie offensiv an, statt sie zu umgehen:

- **(K1) Kostenbaseline ist das Todesurteil für Taker-Mikrostruktur.** Round-Trip-Friktion 11 bps (Taker) bzw. ~15 bps (inkl. Slippage) übersteigt jede gemessene Roh-Edge (Kernrelation Evidence-Register; E-16: Friktion dominiert Richtung ~35×). S2 (CS-02) starb genau hier — E-03 zeigt: selbst im Maker-Only-Run mit **0 Fees** bleibt die Roh-Edge auf jedem Symbol negativ (-3.45 bps Aggregat). **Konsequenz für mein Argument:** Kein Mikrostruktur-Claim dieses Clusters wird von mir als kurzfristiges Taker-Direktionssignal verteidigt. Ich verteidige sie ausschließlich in zwei Modi: (i) **Maker-/passive Execution** (Edge wird zur Spread-/Rebate-Vereinnahmung statt Spread-Überquerung) oder (ii) **als Filter/Veto/Sizing-Layer**, der Friktion einspart statt Friktion zu bezahlen, oder (iii) **auf längeren Horizonten** (Minuten bis Stunden), auf denen ein realer Move die 15-bps-Schwelle überschreiten kann.
- **(K2) Recording-First ist hier am dringendsten.** C-40 (RPI Hidden Liquidity) ist ein dokumentiertes **First-Mover-Dataset ohne jedes Archiv** — die Edge existiert nur, solange aufgezeichnet wird, und verfällt mit Popularität (C-40 Kernannahme). C-36 (Recording-/F0-Infrastruktur) ist die billigste, schnellste und am wenigsten spekulative Investition im gesamten Register. Das Pro-Argument für **sofortiges Recording** ist in diesem Cluster stärker als irgendwo sonst.
- **(K3) Datenverfügbarkeit je Claim ehrlich.** INC-06: Das in PRD-v1 angenommene WS-Topic `orderbook.500` **existiert nicht**. Real verfügbar: `orderbook.1` (10 ms), `orderbook.50` (20 ms), `orderbook.200` (100 ms), `orderbook.1000` (200 ms). Jeder Claim, der Tiefe voraussetzt, wird unten an diese realen Streams gebunden; wo ein Claim keinen historischen Stream hat, sage ich es und mache Recording zur Vorbedingung.

Alle Cluster-Claims sind in der Alignment-Matrix **UNTESTED** — Ausnahme C-06 (**PARTIAL**). Ich argumentiere daher überwiegend über **Mechanismus + günstigsten realistischen Validierungspfad**, nicht über vorhandene positive Evidenz (die es nicht gibt). Das ist die ehrliche Ausgangslage, und sie ist für mehrere dieser Claims trotzdem stark, weil die *Nicht*-Tests strukturell sind (Loader/Harness/Archiv), nicht inhaltliche Widerlegungen.

---

### A-1 — C-36 / C-02: Recording-Infrastruktur + F0-Trigger zuerst bauen (das Fundament-Argument)

**Spot:** EMPFEHLUNG ANWENDEN (als reine Infrastruktur). F0 ist ein deterministisches Perzentil-Regelwerk (Liq-Vol > P99 ODER |dOI| > P99 ODER |dPremium| > P98 ODER RV > P98); auf Spot entfällt zwar Liq/OI, aber RV-/Volumen-Anomalie-Trigger und die Buch-Aufzeichnung selbst sind 1:1 übertragbar. Datenlage: tickers/publicTrade/orderbook.50 existieren live für Spot.
**Futures:** EMPFEHLUNG ANWENDEN (höchste Priorität). F0 ist laut Quelle in 2–3 Tagen baubar (C-36 Reifegrad), regime-neutral und Pflichtbaustein ab Tag 1. Es liefert zwei Dinge gleichzeitig: (a) den **fehlenden Schatten-Benchmark für C-02** (SpikeWavformer kann ohne F0 gar nicht validiert werden — die Matrix nennt das explizit als kritische, billig schließbare Datenlücke) und (b) den **Recording-Trigger**, der alle übrigen Cluster-Claims überhaupt erst testbar macht.
**Optionen:** EMPFEHLUNG MITNEHMEN. Dieselbe Recording-Engine muss options-tickers (IV/Greeks) aufzeichnen — kein IV-Archiv existiert (INC-04). Wer jetzt nicht aufzeichnet, kann später keinen einzigen Options-Claim prüfen.
**Stärkstes Einzelargument:** F0/Recording ist die einzige Investition im Cluster, deren Nutzen NICHT vom Erfolg einer Hypothese abhängt — sie ist die Vorbedingung dafür, dass *irgendein* anderer Claim je ein Verdikt jenseits von UNTESTED bekommen kann.
**Zugeständnis:** F0 selbst erzeugt keinen Alpha; sein Recall ≥ 95 %-Gate (C-36) ist ungemessen und kann an schlechter Perzentil-Kalibrierung scheitern. Es ist ein Enabler, kein Edge.
**Validierungs-Gate (PILOT/ADOPT-Enabler):** Recall ≥ 95 % auf gelabelten Großevents bei ≤ 5 Fehl-Triggern/Tag/Symbol, gemessen auf den ersten 2–4 Wochen Eigen-Recording.

---

### A-2 — C-40: RPI-/Hidden-Liquidity-Karte SOFORT aufzeichnen (das First-Mover-Argument)

**Spot:** EMPFEHLUNG MITNEHMEN, niedrigere Priorität. RPI-Orderbuch-Mechanik ist auf Bybit primär für Perp/Spot-Taker-Schutz relevant; auf Spot ist die Hidden-Liquidity-Differenz vorhanden, aber der direktionale Hebel geringer.
**Futures:** EMPFEHLUNG ANWENDEN — aber ausdrücklich als **Recording-jetzt, Validierung-später** (C-40 ist Moonshot #2). Der Mechanismus ist qualitativ einzigartig: Bybit-RPI-Orders sind im Normalbuch UNSICHTBAR, im separaten RPI-Buch SICHTBAR; Differenz beider Bücher + isRPITrade-Flags ergeben eine **direkt beobachtbare** Hidden-Liquidity-Karte **ohne statistische Inferenz** (C-40 Kernidee). Das ist qualitativ überlegen gegenüber C-03 (Iceberg via Auto-Korrelation), das dieselbe Information nur indirekt schätzt.
**Optionen:** NICHT ANWENDBAR (kein RPI-Buch für Optionen relevant).
**Stärkstes Einzelargument:** C-40 ist ein **First-Mover-Datensatz ohne Archiv** — die Edge verfällt, sobald RPI-Analyse populär wird (C-40 Kernannahme). Der Wert der sofortigen Aufzeichnung ist deshalb **asymmetrisch und zeitkritisch**: Recording kostet wenig, ein verpasstes Archiv ist unwiederbringlich. Selbst wenn die Halte-Quote-These (≥ 65 %) scheitert, bleibt der Datensatz als Forschungs-Asset einzigartig.
**Zugeständnis:** C-40 ist als *handelbares Signal* der spekulativste Claim des Clusters — Halte-Quote ≥ 65 % auf 30-min-Horizont ist ungemessen, RPI-Buch-Tiefe und -Stabilität sind ungeprüft, und die Edge ist per Konstruktion selbst-zerstörend. Ich verteidige hier **Recording**, nicht das Signal. Als S/R-Marker (Stop-Platzierung, Slippage-Reduktion) statt Direktionssignal umgeht es die Kostenbaseline (K1).
**Validierungs-Gate (PILOT):** Nach 3 Monaten Eigen-Recording: Halte-Quote ≥ 65 % der RPI/Iceberg-Level auf 30-min-Horizont gegen ≤ 50 %-Zufallsbasis; Stop-Slippage-Reduktion ≥ 10 % als sekundäres Maß. Recording-Start hat KEIN Gate (Pflicht ab sofort).

---

### A-3 — C-25: Kyle's Lambda + VPIN als Toxic-Flow-Veto (das Friktions-Spar-Argument)

**Spot:** EMPFEHLUNG ANWENDEN (Veto-Modus). Adverse Selection ist auf Spot real; ein Veto, das Entries in toxischen Fenstern unterdrückt, ist markt-agnostisch wertvoll. publicTrade + Orderbook-State existieren für Spot.
**Futures:** EMPFEHLUNG ANWENDEN (stärkster Markt). PRD-kestrel verfeinert C-25 Bybit-spezifisch: VPIN + Kyle-λ + **exakte Taker-Side** (statt Bulk-Heuristik) + RPI-Flag-Segmentierung (C-25 Kernidee). Als unbedingtes Trade-Veto (V0) über allen Modulen.
**Optionen:** NICHT PRIORISIEREN (Liquidität zu dünn für stabile λ-Schätzung über 100 Trades; INC-04).
**Stärkstes Einzelargument:** C-25 ist der **einzige Cluster-Claim, der die Kostenbaseline (K1) nicht bekämpfen muss, sondern ausnutzt**: Ein Veto generiert keinen Trade, zahlt also keine 11 bps — es *spart* sie, indem es genau die Entries verhindert, in denen informierter Flow den passiven Maker abräumt. Genau dieser Mechanismus (Execution-Loss durch toxischen Gegenflow) ist in E-04 forensisch sichtbar: S2 war nicht anti-prädiktiv, sondern **execution-loss-bound** (hit_sum = 0.179 ≠ 1.0). Ein Toxic-Flow-Veto adressiert die nachgewiesene Verlustquelle direkt.
**Zugeständnis:** C-25 ist in keinem Replay aktiv gemessen — in CS-01 nur nominell als „implizites Sizing" gelistet, kein Funnel-Trace (Matrix: grenzwertiger SUSPECT, konservativ ohne Vermerk). Sein Loss-Reduktions-Claim (≥ 30 % PRD-v1 / Odds-Ratio > 3 PRD-kestrel) ist reine Spezifikation. Als reiner Filter braucht es zudem ein Basis-Signal, auf das es wirkt — es ist kein Standalone-Alpha.
**Validierungs-Gate (PILOT):** Auf den S3-iter-5-Trades (E-15) oder einem F0-getriggerten Recording: Jump-Odds-Ratio bei VPIN > P95 muss > 3 sein (p < 0.01); im Veto-Backtest Max-DD-Reduktion ≥ 15 % bei Bruttorendite-Verlust ≤ 5 %. OR < 1.5 ⇒ nur Feature.

---

### A-4 — C-06: Shannon-Entropie als Gate — verteidigt als Regime-/Konditionierungs-Layer, NICHT als S2-Momentum

**Spot:** NICHT PRIORISIEREN als Direktionssignal; als Liquiditäts-Konzentrations-Diagnostik mitführbar.
**Futures:** EMPFEHLUNG ANWENDEN — **aber nur in umgekehrter Lesart und als Gate, nicht als Momentum-Trigger**. Hier setze ich am einzigen PARTIAL-Claim des Clusters an. E-05 zeigt: Das Entropie-Kollaps-Gate ist der **dominante, messbar feuernde Filter** in S2 (~97 % der Ticks, strukturiert, nicht dekorativ) — das Modul funktioniert mechanisch. Was scheiterte, ist die **Richtung** des nachgelagerten Trades (Momentum, „folge der Aggression"), nicht die Detektion des Edge-Fensters. P-01 formuliert genau das: „Entropie-Kollaps = Mean-Reversion-Signal, nicht Momentum". Die Matrix vergibt deshalb bewusst PARTIAL (Gate wirkt, prädiktiver Edge nicht widerlegt), nicht REFUTED.
**Optionen:** NICHT ANWENDBAR (kein L2-Orderbuch-Entropie-Äquivalent ohne IV-Surface-Umbau).
**Stärkstes Einzelargument:** C-06 ist das **einzige Cluster-Modul, das in einem GEEIGNETEN Testfenster nachweislich strukturiert feuert** (E-05, ~97 % Filterung) — sein prädiktiver Wert wurde nie von OFI/PE/Funding isoliert. Es als Regime-Gate (PRD-kestrel S9: KL-Divergenz-Variante, bedingte AUC +0.03) für ein *separat gewähltes* Direktionssignal zu nutzen, ist der naheliegende, billig prüfbare Rehabilitierungspfad.
**Zugeständnis:** Bei Auslösung lag die Roh-Hit-Rate bei 6–8 % (E-05), und die Gesamt-S2-Edge ist negativ ohne invertierbares Anti-Signal (E-03/E-04). Der **eigenständige** prädiktive Wert des Entropie-Signals ist nie nachgewiesen — möglich, dass das Gate ein valides Vol-Cluster-Fenster markiert, das danach folgende Signal aber trotzdem Münzwurf bleibt (INC-05). C-06 ist zudem in CS-02 (REFUTED) verbaut und damit SUSPECT.
**Validierungs-Gate (PILOT):** Isolierter Test: bedingte AUC eines neutralen Folge-Signals in Low-Entropy-Fenstern ≥ +0.03 OOS gegen Random-Fenster; Fusion (PE-Querschnitt UND Entropie) schlägt jede Einzelkomponente. Pflicht: Mean-Reversion- statt Momentum-Hypothese testen.

---

### A-5 — C-07: Permutation Entropy als Cross-Sectional Regime-Selektor

**Spot:** NICHT PRIORISIEREN.
**Futures:** EMPFEHLUNG ANWENDEN — in der **PRD-kestrel-Cross-Sectional-Variante** (Q12), nicht der PRD-v1-Einzelsymbol-Variante. Mechanismus: PE ≈ 1 → Random Walk (nicht handeln); PE-Einbruch → temporärer Determinismus = Edge-Fenster; Cross-Sectional nur die ~10 % Symbole mit niedrigster PE freischalten (C-07 Kernidee). PE braucht nur den Tickers-/Kline-Stream — **keine Tiefe, keine vom INC-06-Problem betroffene Orderbuch-Annahme** (C-07 Abhängigkeiten: keine weiteren). Datenlage daher unkritisch.
**Optionen:** NICHT ANWENDBAR.
**Stärkstes Einzelargument:** PE ist der **datenmäßig billigste Regime-Gate-Kandidat** des Clusters (nur 1-min-Kline, kein Tiefen-Stream, kein Archiv-Problem) und liefert genau die *Konditionierung*, die INC-05 als Bedingung für jeden Direktional-Claim erzwingt (unkonditional = Münzwurf; bedingt regime-gated = potenziell AUC > 0.55).
**Zugeständnis:** In S2 war PE nur tertiäres Gate (`pe_no_greenlight` 39–102 Ticks, E-05) — es feuerte kaum und wurde nie isoliert auf den ρ ≥ 0.3-Vol-Cluster-Claim getestet (SUSPECT, S2-Glied). Die Cross-Sectional-Variante ist gar nicht implementiert. Die Embedding-Parameter (m=4, τ=1) sind ungeprüfte Annahmen.
**Validierungs-Gate (PILOT):** ρ(PE-Drop, Vol-Cluster in [t, t+15min]) ≥ 0.3 als Vorprüfung; dann bedingte AUC nachgelagerter Signale in Low-PE-Fenstern ≥ +0.03 OOS über ≥ 2 disjunkte Fenster.

---

### A-6 — CS-08: Regime-konditioniertes Richtungs-Signal (die Cluster-Synthese)

**Spot:** NICHT PRIORISIEREN (Funding/OI-Achsen fehlen auf Spot).
**Futures:** EMPFEHLUNG ALS PILOT — die plausibelste integrierte Strategie des Clusters, **weil sie die INC-05-Lehre architektonisch einbaut**. CS-08 = Regime-Gate (C-07 PE + C-08 BOCPD) → gefilterte Signale (C-01 OFI + C-32 Funding-Contrarian + C-21 L/S) → C-43 CP-Sizing. Der entscheidende Punkt: Die Strategie behauptet **kein** unkonditionales Richtungssignal (das wäre Münzwurf, INC-05), sondern schaltet Signale **nur in detektierten Regimen** frei. Genau das ist der von INC-05 vorgeschriebene einzige überlebensfähige Pfad für Direktional-Claims.
**Optionen:** NICHT ANWENDBAR.
**Stärkstes Einzelargument:** CS-08 ist die einzige Cluster-Strategie, deren Grundarchitektur (Regime-Gate VOR Direktionssignal) die härteste empirische Lehre des gesamten Registers — INC-05, unkonditionale Richtung = AUC 0.50 — bereits als Konstruktionsprinzip respektiert, statt sie zu ignorieren wie PRD-v1 (M9/M16/M18).
**Zugeständnis:** CS-08 enthält C-01 (SUSPECT aus CS-02, INC-02: OFI-Vorzeichen markiert evtl. MM-Replenishment statt Aggression — also potenziell falsch orientiert) und C-07 (SUSPECT). Wenn das OFI-Direktions-Mapping falsch ist, erbt CS-08 diesen Defekt. Die Strategie ist nicht implementiert; jedes Glied ist UNTESTED. Sie ist eine Architektur-Wette, kein Befund.
**Validierungs-Gate (PILOT):** Schrittweise — zuerst C-07/C-08-Regime-Gate isoliert (A-5), dann OFI-Vorzeichen-Orientierung gegen INC-02 prüfen (markiert OFI Aggression oder Replenishment?), erst dann konditionale AUC > 0.55 der Gesamtkette FDR-korrigiert.

---

### A-7 — C-01: OFI als Feature/Sizing-Input auf längerem Horizont, NICHT als Taker-Direktionssignal

**Spot:** NICHT PRIORISIEREN (Cross-OFI-Achse BTC→Alt ist Perp-zentriert).
**Futures:** EMPFEHLUNG ALS FEATURE (nicht standalone). Ich verteidige C-01 ausdrücklich **nicht** in seiner S2-Rolle (kurzfristiges Taker-Momentum — dort starb es an K1/E-03). PRD-kestrel nutzt OFI korrekt nur noch als Feature-Input (Q3 Multi-Level + Cross-Asset), nicht als Direktionssignal (INC-02-Konsequenz). Der überlebensfähige Mechanismus: OFI auf **aggregierten 1–5-min-Fenstern** (PRD-v1 C-01: „Retail-Edge in 1–5-min unter der HFT-Arbitragegrenze") als Konditionierungs-/Sizing-Feature in regime-gated Strategien (CS-08). Datenlage: orderbook.50 (20 ms Deltas) existiert real — INC-06-konform, keine 500er-Annahme nötig.
**Optionen:** NICHT ANWENDBAR.
**Stärkstes Einzelargument:** Der direktionale Beitrag von OFI wurde **nie isoliert gemessen** — die S2-Forensik widerlegte die GESAMT-Kette, nicht das OFI-Modul (Modul ≠ Strategie; Matrix: UNTESTED, nicht REFUTED). Auf 1–5-min-Aggregaten als Feature ist die K1-Schwelle handhabbar, weil ein realer 1–5-min-Move die 15 bps überschreiten kann.
**Zugeständnis:** INC-02 ist ein ernster, konkreter Verdacht: Das OFI-Vorzeichen könnte MM-Replenishment statt informierter Aggression markieren — dann ist die handelsübliche Vorzeichen-Konvention falsch orientiert, und OFI als Feature wäre nicht nur wertlos, sondern systematisch irreführend (auch in C-09 HMM, C-14). Das ist die schwächste Stelle dieses Sub-Arguments.
**Validierungs-Gate (PILOT):** Vor jeder Strategie-Nutzung: isolierter Vorzeichen-Test — korreliert sign(OFI_1-5min) mit Forward-Return oder mit MM-Replenishment? OOS-R² der 1–5-min-Return-Prognose ≥ 1 %; bedingte AUC > 0.55 nur in regime-gated Fenstern.

---

### A-8 — C-03 & C-04: Iceberg-Detection und Wavelet-Denoising — ehrlich nachrangig, datenblockiert

**Spot:** NICHT PRIORISIEREN.
**Futures:** EMPFEHLUNG ZURÜCKSTELLEN (PARK-Tendenz), mit klarem Recording-Pfad. Beide sind UNTESTED und beide hängen an Daten, die heute nicht archiviert sind:
- **C-03 (Iceberg via Queue-Replenishment):** braucht `orderbook.200` (100 ms) — der korrekte, INC-06-konforme Stream (NICHT das nicht-existente orderbook.500). Mechanismus solide (Replenishment-Rate > 0.7× Pre-Hit-Size → S/R-Marker), aber C-40 (RPI) liefert dieselbe Hidden-Liquidity-Information **direkt und ohne statistische Inferenz** — C-03 ist damit der schwächere Zwilling und wird durch C-40 weitgehend dominiert.
- **C-04 (Wavelet-Symlet-Denoising):** Symlet-DWT mit linearer Phase (Latenzerhaltung) zur Trennung von MM-Mikrorauschen vom Smart-Money-Tape; R²-Lift-Claim (≥ 10 % gegen Roh-Imbalance) nie gemessen. Ist ein **Vorverarbeitungs-Layer**, kein Standalone-Signal — sein Wert ist nur messbar, sobald ein Abnehmer-Signal (OFI/Imbalance) existiert.
**Optionen:** NICHT ANWENDBAR (C-04 IV-Surface-Variante denkbar, aber kein IV-Archiv, INC-04).
**Stärkstes Einzelargument:** Beide umgehen K1 strukturell, weil sie als **S/R-Marker bzw. Vorverarbeitung** wirken, nicht als Taker-Trades — sie zahlen keine 11 bps. Als Stop-Platzierungs-Hilfe (C-03) bzw. Signal-Entrauschung (C-04) sind sie Friktions-neutral.
**Zugeständnis:** Beide sind reine Mechanismus-Argumente ohne jede Evidenz, beide datenblockiert, und C-03 wird von C-40 inhaltlich dominiert. Ich gestehe zu, dass diese zwei die schwächsten ANWENDUNGS-Kandidaten des Clusters sind — ihr realistischer Status ist „Recording aktivieren, Validierung deferieren", nicht „jetzt bauen".
**Validierungs-Gate (PILOT, nachgelagert):** C-03: Bounce-Rate ≥ 60 % auf Iceberg-Level innerhalb 5 min nach Touch, gemessen auf orderbook.200-Recording. C-04: R²-Lift ≥ 10 % gegen Roh-Imbalance als Input für ein bereits validiertes Abnehmer-Signal.

---

### A-9 — C-02: SpikeWavformer — Effizienz-Argument, kein Edge-Argument

**Spot/Futures:** EMPFEHLUNG ZURÜCKSTELLEN, an C-36 koppeln. C-02 behauptet ausdrücklich **keinen** Trading-Edge, sondern einen **Effizienzvorteil** (Analyse-Engine läuft nur bei echtem Signal statt kontinuierlich; C-02 Kernidee). Sein einziger sinnvoller Validierungspfad ist der Schatten-Vergleich gegen F0 (C-36): gleiches/besseres Event-Recall (≥ 95 %) bei ≤ 50 % der F0-Trigger-Rate.
**Optionen:** NICHT ANWENDBAR.
**Stärkstes Einzelargument:** C-02 ist kein Alpha-Claim und konkurriert daher gar nicht mit der Kostenbaseline — es ist ein System-Effizienz-Claim, dessen Benchmark (F0/C-36) ohnehin gebaut werden muss (A-1).
**Zugeständnis:** Moonshot-Status (Matrix), nichts implementiert/getestet, und solange F0 (der Benchmark) nicht läuft, ist C-02 gar nicht bewertbar. Es rangiert klar hinter dem deterministischen, in Tagen baubaren F0.
**Validierungs-Gate (PILOT, nachgelagert nach C-36):** Dominanz über F0 nach 2 Kalibrierungs-Iterationen über 2 Monate Schattenbetrieb (Recall ≥ F0 bei ≤ 50 % Trigger-Rate).

---

### Zusammenfassung Advocate — Tendenz je Claim × Markt

| Claim | Spot | Futures | Optionen | Modus (umgeht K1 wie?) |
|---|---|---|---|---|
| C-36 / C-02-Benchmark | ANWENDEN | **ANWENDEN (Prio 1)** | mitnehmen (IV-Rec.) | Infra, kein Trade |
| C-40 RPI Hidden Liquidity | mitnehmen | **ANWENDEN (Recording sofort)** | n/a | S/R-Marker, Recording-First |
| C-25 Kyle-λ / VPIN | ANWENDEN | **ANWENDEN (Veto)** | nein | spart Friktion (Veto) |
| C-06 Shannon-Entropie | nein | **ANWENDEN (Gate, MR-Lesart)** | n/a | Gate, kein Taker-Momentum |
| C-07 Permutation Entropy | nein | ANWENDEN (Cross-Sect.) | n/a | Regime-Gate, kein Tiefen-Stream |
| CS-08 Regime-Richtung | nein | PILOT | n/a | Regime-gated (INC-05-konform) |
| C-01 OFI | nein | FEATURE (1–5 min) | n/a | längerer Horizont + Feature |
| C-03 / C-04 | nein | ZURÜCKSTELLEN | n/a | S/R / Vorverarbeitung |
| C-02 SpikeWavformer | zurückstellen | ZURÜCKSTELLEN (an C-36) | n/a | Effizienz, kein Edge |

**Drei stärkste Argumente:** A-1 (C-36/Recording als Fundament — nutzenunabhängig von jeder Hypothese), A-2 (C-40 First-Mover-Recording, zeitkritisch-asymmetrisch), A-3 (C-25 Toxic-Flow-Veto — spart Friktion statt sie zu bezahlen, adressiert die in E-04 nachgewiesene Verlustquelle direkt).

**Ehrlich schwächster Punkt (cluster-weit):** Mit Ausnahme von C-06 (PARTIAL) ist JEDER Cluster-Claim UNTESTED — ich argumentiere durchgehend über Mechanismus und Validierungspfad, nicht über positive Evidenz, die nicht existiert. Und der einzige Claim mit gemessenem Feuern (C-06) feuert in einer als REFUTED bewerteten Strategie (CS-02) mit 6–8 % Hit-Rate. Mein gesamtes Pro-Argument steht und fällt mit der Bereitschaft, ZUERST in Recording zu investieren, bevor irgendein Edge belegt werden kann.

---

*Advocate-Part Ende. Skeptic antwortet Punkt für Punkt auf A-1 … A-9.*
