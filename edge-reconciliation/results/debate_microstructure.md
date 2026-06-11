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

---

## SKEPTIC — Antwort

### Vorbemerkung — wo ich dem Advocate folge, und wo der Bruch liegt

Ich teile drei Prämissen des Advocates ausdrücklich: (i) Die Kostenbaseline (11 bps Taker / ~15 bps inkl. Slippage, E-03/E-16) ist real und tötet jedes Taker-Direktionssignal in diesem Cluster — die Verschiebung auf Veto/Feature/Maker-Modi ist die einzig ehrliche Antwort. (ii) Die Datenlücken sind strukturell (Loader/Harness/Archiv, E-13/E-14, INC-04/INC-06), nicht inhaltliche Widerlegungen — der Advocate inflationiert hier KEINE Evidenz, im Gegenteil, er gesteht die UNTESTED-Lage offen ein. (iii) Verlorene Daten sind unwiederbringlich (Steelman zu A-2, s.u.). **Der Bruch liegt woanders:** Der Advocate verkauft ein UNGEDECKELTES Infrastruktur-Investment (Recording) mit einem Nutzen-Argument, das per Konstruktion kein Abbruchkriterium hat — und genau das verlangt die GRUNDHALTUNG (CLAUDE.md: „Jeder Ansatz braucht ein messbares Validierungs-Gate UND ein Abbruchkriterium"). Recording-First ohne Recording-Stop ist ein Data-Lake, kein Edge-Programm.

---

### A-1 — C-36/C-02: Recording-Infrastruktur zuerst

- **Steelman:** F0/Recording ist die einzige Investition im Cluster, deren Nutzen NICHT vom Erfolg einer einzelnen Hypothese abhängt — sie ist die notwendige Vorbedingung dafür, dass irgendein UNTESTED-Claim je ein Verdikt jenseits von UNTESTED bekommt (Alignment: 0 CONFIRMED, 48 UNTESTED). Ohne Eigen-Recording bleibt der ganze Cluster dauerhaft unbewertbar. Das ist korrekt und stark.
- **Der Kern-Fehlschluss:** „Nützlich unabhängig von Hypothesen" ist exakt das klassische Data-Lake-Argument — und es ist nicht-falsifizierbar. Ein Posten, dessen Rechtfertigung lautet „er könnte sich irgendwann für irgendeinen Claim lohnen", hat per Konstruktion KEIN Abbruchkriterium. Die GRUNDHALTUNG (CLAUDE.md) verlangt für JEDEN übernommenen Ansatz ein Abbruchkriterium; C-36 hat in der Quelle sogar explizit „kein Abbruch — Pflichtbaustein" (claims_register C-36 Validierungs-Gate). Das ist genau die Stelle, an der ein Dauer-Betriebsposten ungeprüft durchrutscht.
- **Kostenrealität (vom Advocate unterschlagen):** Der Advocate nennt F0 „die billigste Investition im Register" und meint die BAU-Kosten (2–3 Tage, C-36 Reifegrad). Das ist eine Bait-and-Switch: F0-Code ist billig, aber **Recording ist der schwerste Dauer-Betriebsposten** — Storage (orderbook.1 = 10 ms-Deltas × N Symbole × 24/7), Uptime/Gap-Management, Schema-Pflege über Bybit-API-Änderungen, Monitoring. Diese Kosten skalieren mit Zeit, nicht mit einem einmaligen Build. Kein E-xx und keine Quelle beziffert sie — die Behauptung „billig" ist unbelegt für genau den teuren Teil.
- **Die Recall-Lücke macht F0 selbst spekulativ:** Der Advocate gesteht zu, dass das Recall-≥-95-%-Gate (C-36) ungemessen ist und an Perzentil-Kalibrierung scheitern kann. Damit ist F0 nicht „deterministisch sicher", sondern selbst ein UNTESTED-Claim (Alignment C-36: UNTESTED, keine Evidenz). Der „Enabler" muss erst beweisen, dass er die Events überhaupt einfängt, bevor er als Trigger für teures Recording taugt.
- **Spot:** PILOT-fähig, aber NUR mit hartem Recording-Budget-Deckel. RV-/Volumen-Trigger sind 1:1 übertragbar (Advocate korrekt), Liq/OI entfallen — also feuert F0 auf Spot mit reduzierter Bedingungsbasis, was die Recall-Frage verschärft, nicht entschärft.
- **Futures:** PILOT (höchste Cluster-Priorität gestehe ich zu), aber das Verdikt muss lauten: F0/Recording wird gebaut MIT einem definierten Recording-Abbruchkriterium (s.u.), nicht „ADOPT als Pflicht ab Tag 1".
- **Optionen:** Hier ist das Argument am schwächsten. „Wer jetzt nicht IV aufzeichnet, kann später keinen Options-Claim prüfen" stimmt — aber der einzige Options-Claim (C-33, UNTESTED) hängt an INC-04: Options-Liquidität fällt laut Quelle in 60–80 % der Stunden durch den Mindest-Check (Alignment CS-09). Man zeichnet ein IV-Archiv für einen Markt auf, der mehrheitlich illiquide ist. Recording-Kosten gegen einen einzigen, strukturell liquiditätsblockierten Claim — das ist die schlechteste Recording-ROI im Cluster.
- **Härtester Einwand (1 Satz):** „Hypothesenfrei nützlich" ist ein nicht-falsifizierbares Data-Lake-Argument, das die GRUNDHALTUNG (Abbruchkriterium-Pflicht) verletzt, und es kaschiert per Bait-and-Switch (billiger Build ↔ teurer Dauerbetrieb), dass der einzige messbare Recording-Erfolgsindikator — landet je ein Claim jenseits UNTESTED — selbst ungemessen ist.
- **Minimale Bedingung für PILOT (statt unbeschränktem ADOPT):** Recording bekommt selbst ein Abbruchkriterium: **(a)** harter Storage/Kosten-Deckel ex ante festgelegt; **(b)** F0-Recall ≥ 95 % auf gelabelten Großevents in den ersten 2–4 Wochen (sonst Trigger-Rekalibrierung oder Stopp, nicht „läuft weiter"); **(c)** ein **Sunset-Review nach Fenster X** (z.B. 3 Monate): hat in dieser Zeit MINDESTENS ein Cluster-Claim ein PARTIAL-Upgrade aus Eigen-Recording erreicht? Wenn nein → Recording-Scope wird gekürzt, nicht stillschweigend verstetigt. Ohne (a)–(c) ist es DROP-würdig als ungedeckelter Betriebsposten.

---

### A-2 — C-40: RPI-Hidden-Liquidity sofort aufzeichnen (First-Mover)

- **Steelman (mit Würdigung der Zeitkritikalität):** Das First-Mover-Argument hat einen echten, irreversiblen Kern: Es existiert KEIN RPI-Archiv (C-40 Reifegrad, Alignment UNTESTED), und ein nicht aufgezeichnetes Fenster ist physikalisch unwiederbringlich — anders als Code oder Modelle lässt sich vergangene Mikrostruktur nicht nachträglich erzeugen. Der Mechanismus ist zudem qualitativ überlegen gegenüber C-03: RPI-Buch-Differenz + isRPITrade-Flags liefern Hidden Liquidity **direkt beobachtbar ohne statistische Inferenz** (C-40 Kernidee), während C-03 dasselbe nur via Auto-Korrelation schätzt. Wenn die These trägt, ist die Asymmetrie real: Recording kostet wenig, ein verpasstes Archiv kostet alles. Das ist der stärkste zeitkritische Punkt des Clusters, und ich lasse ihn stehen.
- **Aber: First-Mover beim RECORDING ≠ First-Mover beim EDGE.** Hier liegt der Trugschluss. „Kein Archiv existiert" gilt symmetrisch für ALLE Marktteilnehmer — auch für die HFT-Firmen, die das RPI-Buch **live** lesen. Das RPI-Buch ist laut C-40 Kernannahme „öffentlich zugänglich". Wer das Signal live handelt, braucht kein Archiv; er sieht die Hidden Liquidity in Echtzeit und reagiert in Mikrosekunden. Der Edge in „Hidden Liquidity als S/R" — falls er existiert — wird von genau diesen Live-Lesern bereits arbitriert, bevor das erste Byte in unserem Archiv landet. Unser Archiv-Vorsprung ist ein **Forschungs**-Vorsprung (wir können post-hoc analysieren), kein **Handels**-Vorsprung. Der Advocate gesteht das halb zu („bleibt als Forschungs-Asset einzigartig") — aber ein Forschungs-Asset rechtfertigt keinen Handels-Edge-Claim, und die Asymmetrie „Recording billig, Archiv unwiederbringlich" gilt nur für den Forschungswert, nicht für den behaupteten S/R-Edge.
- **Selbstzerstörender Edge — gegen sich selbst gewendet:** C-40 Kernannahme sagt explizit „Edge verfällt, sobald RPI-Analyse populär wird". Das ist kein Detail, sondern fatal für das Recording-Argument: Wenn der Edge mit Popularität verfällt UND HFT ihn live liest, dann ist er bereits am Verfallen, während wir noch 3 Monate aufzeichnen (C-40 Gate: Halte-Quote nach 3 Monaten). Wir investieren in ein Archiv für ein Signal, dessen Halbwertszeit per Konstruktion kürzer sein kann als unser Mess-Vorlauf.
- **Spot:** DROP-Tendenz für das Signal. Advocate selbst: „direktionaler Hebel geringer". Recording mitnehmen nur, falls die Engine ohnehin läuft (Grenzkosten ~0).
- **Futures:** PARK (nicht ADOPT). Recording-Start als billiges Forschungs-Asset akzeptabel, ABER unter denselben Deckel wie A-1 — und ohne Illusion eines Handels-Edge. Der Validierungs-Claim (Halte-Quote ≥ 65 % vs. ≤ 50 % Zufall, C-40 Gate) ist der spekulativste des Clusters (Advocate gesteht zu: RPI-Buch-Tiefe/-Stabilität ungeprüft).
- **Optionen:** n/a (Advocate korrekt, kein RPI-Buch relevant).
- **Härtester Einwand (1 Satz):** First-Mover beim Recording ist kein First-Mover beim Edge — das öffentlich-live-lesbare RPI-Buch wird von HFT bereits arbitriert, sodass unser Archiv ein Forschungs-Asset ohne nachweisbaren Handels-Vorsprung ist, dessen Ziel-Edge laut eigener Kernannahme sogar selbstzerstörend verfällt.
- **Minimale Bedingung für PILOT:** Recording-Start nur als Anhängsel an die ohnehin laufende F0-Engine (Grenzkosten nahe 0, kein eigener Posten); explizite Umwidmung des Claims von „Handels-Edge" zu „Forschungs-/S-R-Marker"; Gate ehrlich an Stop-Slippage-Reduktion ≥ 10 % (das sekundäre, friktions-sparende Maß) statt an die Halte-Quote-Direktional-These koppeln.

---

### A-3 — C-25: Kyle-λ + VPIN als Toxic-Flow-Veto

- **Steelman:** C-25 ist der einzige Cluster-Claim, der die Kostenbaseline nicht bekämpfen muss, sondern ausnutzt: Ein Veto generiert keinen Trade, zahlt also keine 11 bps — es spart sie. Und es adressiert eine in E-04 forensisch sichtbare Verlustquelle: S2 war execution-loss-bound (hit_sum = 0.179 ≠ 1.0), nicht anti-prädiktiv — also Verlust durch toxischen Gegenflow beim passiven Fill, genau das, was ein Toxic-Flow-Veto unterdrücken soll. Das ist mechanistisch das sauberste Argument des Clusters.
- **Das Zirkularitätsproblem (identisch zum Regime-Filter):** Ein Veto ist nur dann MESSBAR wertvoll, wenn es eine positive Basis-Strategie gibt, deren Trades es selektiv unterdrückt. Der Advocate gesteht das zu („braucht ein Basis-Signal, kein Standalone-Alpha"). Aber im gesamten Register existiert KEINE positive Basis-Strategie: 0 CONFIRMED, alle CS-xx sind REFUTED/UNTESTED/PARTIAL-negativ (Alignment-Endverteilung). Auf was soll das Veto wirken? Man kann den Veto-Nutzen („Max-DD-Reduktion ≥ 15 % bei Bruttorendite-Verlust ≤ 5 %", C-25 Gate) nicht messen, wenn die Bruttorendite, die geschützt werden soll, selbst negativ ist (E-03: -3.45 bps, E-09: -16.81 bps). Ein Veto auf eine verlustreiche Strategie reduziert nur die Frequenz des Verlierens — das ist kein Edge, das ist Schadensbegrenzung an etwas, das man ohnehin nicht handeln sollte.
- **Die E-04-Lesart ist überdehnt:** Der Advocate liest aus hit_sum = 0.179 „execution-loss durch toxischen Gegenflow". E-04 sagt enger: S2 ist execution-loss-bound, nicht direction-bound — die Verlustquelle ist Friktion + doppelseitige Slippage (RMS 8.0 bps BTC/ETH, E-04), NICHT nachgewiesenermaßen „informierter Gegenflow". Friktion frisst einen Coin-Flip (E-05: 6–8 % Hit = Rauschen, nicht inverses Signal). Ein Toxic-Flow-Veto adressiert „informierten Gegenflow" — aber die forensisch belegte Verlustquelle ist Fee+Slippage auf einem Nullsignal. Das Veto würde die Friktion nicht senken; es würde nur seltener handeln. Das ist genau das, was ein Schwellwert auf das Roh-Signal auch täte — kein VPIN nötig.
- **VPIN-Bucketing = neue freie Parameter = GM-2:** VPIN auf Bybit-Perp-Ticks braucht Volume-Bucket-Größen, Bucket-Anzahl, das P95-Toxicity-Quantil (C-25 Gate: VPIN > P95). Das sind mindestens 3 neue, ungesetzte freie Parameter — und das Register hat KEINE FDR-/Bonferroni-Korrektur über 3 Iterationen × 5 Symbole × Strategien (GM-2). Jeder gefundene „Jump-OR > 3" auf den N=190/213 Trades wäre unkorrigiert. Hinzu: Kyle-λ verlangt eine stabile OLS-Schätzung über 100 Trades (C-25 Kernannahme) — auf den vorhandenen Stichproben (S2 N=11–71/Symbol, E-03) ist diese Mindestmenge je Symbol teils gar nicht erreichbar.
- **Evidenzlage des Claims selbst:** C-25 ist UNTESTED, in keinem Replay-Funnel aktiv messbar, in CS-01 nur nominell als „implizites Sizing" ohne Trace (Alignment C-25: nicht einmal SUSPECT, weil kein Replay-Trace existiert). Der Loss-Reduktions-Claim (≥ 30 % PRD-v1 / OR > 3 PRD-kestrel) ist reine Spezifikation (Advocate gesteht zu).
- **Spot:** DROP für jetzt — adverse Selection real, aber kein Basis-Signal, auf das das Veto wirken könnte; publicTrade-Existenz allein macht keinen testbaren Veto-Nutzen.
- **Futures:** PARK, nicht ADOPT. Rettbar genau dann, wenn zuerst ein positives Basis-Signal existiert (zirkuläre Vorbedingung), das es heute nicht gibt.
- **Optionen:** DROP (Advocate korrekt: Liquidität zu dünn für stabile λ über 100 Trades, INC-04).
- **Härtester Einwand (1 Satz):** C-25 hat dasselbe Zirkularitätsproblem wie jeder Filter — sein einziges Erfolgsmaß (DD-Reduktion bei Bruttorendite-Erhalt) ist auf einem Register ohne einzige positive Basis-Strategie unmessbar — und VPIN-Bucketing fügt 3+ unkorrigierte freie Parameter (GM-2) zu einer Verlustquelle hinzu, die laut E-04 ohnehin Friktion ist, nicht informierter Flow.
- **Minimale Bedingung für PILOT:** Existenz EINES validierten (mind. PARTIAL mit positiver Roh-Edge) Basis-Signals, auf das das Veto angewendet wird; VPIN-Bucket-Parameter vorab fixiert (kein In-Sample-Tuning); Test FDR-korrigiert (GM-2); Gate exakt nach C-25 PRD-kestrel: OR > 3 (p < 0,01), OR < 1,5 ⇒ nur Feature, niemals Veto.

---

### A-4 — C-06: Shannon-Entropie als Gate (MR-Lesart)

- **Steelman:** C-06 ist der EINZIGE PARTIAL-Claim des Clusters und das einzige Modul, das in einem geeigneten Testfenster nachweislich strukturiert feuert (E-05: Entropie-Kollaps-Gate filtert ~97 % der Ticks, nicht dekorativ). Was scheiterte, war die nachgelagerte RICHTUNG (Momentum), nicht die Detektion des Fensters — die Matrix vergibt deshalb bewusst PARTIAL, nicht REFUTED. Die MR-Umlesart (P-01: „Entropie-Kollaps = Mean-Reversion, nicht Momentum") ist ein legitimer, billig prüfbarer Rehabilitierungspfad. Das ist fair und der beste Einzelpunkt des Advocates.
- **Wieviel PARTIAL bleibt wirklich? — Die 6-8-%-Zahl entkernt das Gate:** E-05 zeigt: bei Auslösung lag die Roh-Hit-Rate bei 6–8 % (BTC/ETH). Der Advocate trennt „Gate feuert strukturell" von „Richtung falsch". Aber diese Trennung ist dünner als sie klingt: Wenn das Gate ein „valides Edge-Fenster" markiert, sollte IRGENDEINE Lesart (Momentum ODER Reversion) in diesem Fenster über Münzwurf liegen. E-04 hat die Reversion-Lesart bereits indirekt getestet — der Mirror-Test ist genau die Inversion, und hit_sum = 0.179 ≠ 1.0 zeigt: Die invertierte Richtung ist NICHT der Gewinner, Inversion macht es schlimmer (-3.45 → -4.55 bps, E-04). Die MR-Hypothese, die der Advocate als „ungetestet, billig prüfbar" verkauft, ist in ihrer simpelsten Form (Sign-Flip) bereits gescheitert. Was bleibt, ist die Hoffnung, dass eine SOPHISTICIERTERE MR-Lesart (nicht Sign-Flip, sondern separates Signal in Low-Entropy-Fenstern) funktioniert — aber das ist ein NEUER Claim, kein Rest des PARTIAL.
- **Das Gate markiert evtl. nur Vol-Cluster, nicht Edge:** INC-05 (Münzwurf-Baseline) plus E-05 lassen die naheliegendste Erklärung offen: Das Entropie-Kollaps-Gate markiert ein Volatilitäts-Cluster-Fenster (deshalb feuert es strukturiert auf 97 %), aber das nachfolgende Signal bleibt in diesem Fenster ein Münzwurf, den die Friktion frisst. Strukturiertes Feuern ≠ prädiktiver Wert. Der Advocate gesteht genau das zu („möglich, dass das Gate ein valides Vol-Cluster-Fenster markiert, das Folgesignal aber Münzwurf bleibt"). Damit schrumpft der PARTIAL-Gehalt auf: „C-06 ist ein funktionierender Vol-Cluster-Detektor" — was ein Feature-Status ist, kein Gate-für-Edge-Status.
- **SUSPECT-Erbe:** C-06 ist in CS-02 (REFUTED) verbaut und Beitrag nie isoliert (Alignment C-06: PARTIAL + SUSPECT). Die GRUNDHALTUNG (Modul ≠ Strategie) rettet C-06 vor automatischem REFUTED — aber sie zwingt auch zu: SUSPECT bleibt, bis standalone getestet.
- **Spot:** DROP als Direktionssignal (Advocate stimmt zu); als Vol-Cluster-Diagnostik = Feature, nicht Gate.
- **Futures:** PILOT, aber NUR mit der Pflicht-Klarstellung, dass die simple Sign-Flip-MR-Lesart durch E-04 bereits widerlegt ist und die sophisticiertere MR-Variante als NEUER Claim mit eigenem AUC-Gate (+0.03 OOS, A-4) FDR-korrigiert (GM-2) geprüft wird.
- **Optionen:** n/a (Advocate korrekt, kein L2-Äquivalent ohne IV-Surface-Umbau).
- **Härtester Einwand (1 Satz):** Die als „billig prüfbar" verkaufte MR-Umlesart ist in ihrer einfachen Sign-Flip-Form durch E-04 (hit_sum 0.179, Inversion macht es schlimmer) bereits gescheitert, sodass vom PARTIAL real nur ein Vol-Cluster-DETEKTOR (Feature) übrigbleibt, kein Edge-Gate.
- **Minimale Bedingung für PILOT:** Isolierter Test der NICHT-trivialen MR-Hypothese (separates Folge-Signal, nicht Sign-Flip) auf einem disjunkten Fenster: bedingte AUC ≥ +0.03 OOS gegen Random-Fenster, FDR-korrigiert; explizite Trennung von „Vol-Cluster-Detektion" (Feature, unstrittig) und „prädiktivem Edge im Fenster" (der eigentliche, offene Claim).

---

### A-5 — C-07: Permutation Entropy als Cross-Sectional Regime-Selektor

- **Steelman:** PE ist der datenmäßig billigste Regime-Gate-Kandidat des Clusters — nur 1-min-Kline, kein Tiefen-Stream, kein Archiv-Problem, kein INC-06-Risiko (C-07 Abhängigkeiten: keine weiteren). Das macht ihn zum billigsten Test im Cluster und liefert genau die Konditionierung, die INC-05 als Bedingung für jeden Direktional-Claim erzwingt. Fair: niedrige Daten-Hürde ist ein echter Vorteil.
- **„Billig zu testen" ≠ „wahrscheinlich erfolgreich":** Der Advocate verwechselt Test-Kosten mit Erfolgswahrscheinlichkeit. PE ist UNTESTED + SUSPECT (Alignment C-07), feuerte in S2 nur als tertiäres Gate kaum (`pe_no_greenlight` 39–102 Ticks, E-05) und wurde nie auf den ρ ≥ 0,3-Vol-Cluster-Claim isoliert. Die Cross-Sectional-Variante (Q12) ist gar nicht implementiert. Embedding-Parameter (m=4, τ=1) sind ungeprüfte Annahmen (Advocate gesteht zu) — das sind erneut freie Parameter unter GM-2.
- **Das Konditionierungs-Versprechen ist unbewiesen:** Der Advocate argumentiert, PE liefere die von INC-05 geforderte Konditionierung. Aber INC-05 sagt nur, dass UNKONDITIONALE Richtung Münzwurf ist — es sagt NICHT, dass IRGENDEINE Konditionierung (und schon gar nicht PE-Konditionierung) den Münzwurf bricht. Dass „bedingt regime-gated = potenziell AUC > 0.55" ist eine Hoffnung, kein Befund. Kein E-xx zeigt, dass Low-PE-Fenster eine bedingte Edge tragen.
- **Spot:** DROP (Advocate stimmt zu).
- **Futures:** PILOT akzeptabel — wegen der niedrigen Test-Kosten, NICHT wegen Evidenz. Es ist der billigste Lottoschein, kein wahrscheinlicher Gewinner.
- **Optionen:** n/a.
- **Härtester Einwand (1 Satz):** Niedrige Test-Kosten sind kein Erfolgsindikator — PE-Konditionierung den Münzwurf bricht, ist eine reine Hoffnung ohne jeden E-xx-Beleg, mit ungeprüften Embedding-Parametern unter GM-2.
- **Minimale Bedingung für PILOT:** Vorprüfung ρ(PE-Drop, Vol-Cluster) ≥ 0,3 als billiges Gate-vor-dem-Gate; m/τ vorab fixiert; bedingte AUC ≥ +0.03 OOS über ≥ 2 disjunkte Fenster, FDR-korrigiert. Scheitert die ρ-Vorprüfung → DROP, kein weiterer Aufwand.

---

### A-6 — CS-08: Regime-konditioniertes Richtungs-Signal

- **Steelman:** CS-08 ist die einzige Cluster-Strategie, deren Grundarchitektur (Regime-Gate VOR Direktionssignal) die härteste empirische Lehre des Registers — INC-05, unkonditionale Richtung = AUC ~0.50 — bereits als Konstruktionsprinzip respektiert, statt sie wie PRD-v1 zu ignorieren. Architektonisch ist das die reifste Synthese des Clusters.
- **Eine Architektur-Wette ist kein Befund:** Der Advocate sagt es selbst: „Sie ist eine Architektur-Wette, kein Befund." CS-08 ist UNTESTED, nicht implementiert, JEDES Glied UNTESTED (Alignment CS-08). Sie setzt sich aus SUSPECT-Modulen zusammen: C-01 (SUSPECT, INC-02-Verdacht falsche Orientierung), C-07 (SUSPECT), C-08 (SUSPECT, No-Op in S3, E-12), C-32/C-21 (UNTESTED, INC-05-Druck). Eine Kette aus ungetesteten, teils verdächtigen Gliedern erbt jeden Einzeldefekt multiplikativ.
- **Der INC-02-Defekt ist fatal für die Richtungsachse:** CS-08 enthält C-01 OFI als Direktionssignal. Wenn INC-02 stimmt (OFI-Vorzeichen markiert MM-Replenishment statt Aggression), ist die Richtungsachse der Strategie systematisch falsch orientiert — und dann hilft das beste Regime-Gate nichts, weil es ein falsch gerichtetes Signal freischaltet. Das Gate kann nur filtern WANN gehandelt wird, nicht die Korrektheit von WOHIN.
- **Spot:** DROP (Funding/OI-Achsen fehlen, Advocate stimmt zu).
- **Futures:** PARK, nicht PILOT. PILOT würde ein konkretes Testdesign mit absehbarem Erfolg verlangen; hier müsste man zuerst 3–4 SUSPECT-Module einzeln rehabilitieren (A-5, A-7), bevor die Integration überhaupt sinnvoll testbar ist. Das ist eine Forschungsagenda, kein Pilot.
- **Optionen:** n/a.
- **Härtester Einwand (1 Satz):** Eine architektonisch elegante Kette aus 4+ SUSPECT/UNTESTED-Gliedern ist gegen die GRUNDHALTUNG „Evidenz schlägt Idee" — sie erbt jeden Einzeldefekt (v.a. INC-02 auf der OFI-Richtungsachse) und ist erst testbar, nachdem ihre Glieder einzeln rehabilitiert sind.
- **Minimale Bedingung für PILOT:** Sequenzielle Vorbedingung — zuerst C-07-Regime-Gate (A-5) UND C-01-Vorzeichen gegen INC-02 (A-7) einzeln bestanden; erst dann konditionale AUC > 0.55 der Gesamtkette, FDR-korrigiert. Vorher: PARK.

---

### A-7 — C-01: OFI als Feature/Sizing auf längerem Horizont

- **Steelman:** Der direktionale Beitrag von OFI wurde NIE isoliert gemessen — die S2-Forensik widerlegte die Gesamt-Kette, nicht das OFI-Modul (Alignment C-01: UNTESTED, nicht REFUTED; Modul ≠ Strategie). Auf 1–5-min-Aggregaten als Feature ist die K1-Schwelle handhabbar, weil ein realer 1–5-min-Move die 15 bps überschreiten kann. Die Verteidigung als Feature (nicht als S2-Taker-Momentum) ist korrekt aus der GRUNDHALTUNG abgeleitet.
- **INC-02 ist die schwächste Stelle — und der Advocate gesteht sie zu:** Wenn das OFI-Vorzeichen MM-Replenishment statt informierte Aggression markiert, ist OFI als Feature nicht nur wertlos, sondern systematisch irreführend (auch in C-09, C-14). Das ist kein vager Verdacht, sondern ein konkreter, im Register dreifach referenzierter Mechanismus-Defekt (INC-02). Solange er nicht ausgeräumt ist, ist JEDE OFI-Nutzung — Feature, Sizing, Gate — kontaminiert.
- **Der Horizont-Wechsel ist eine ungetestete Annahme:** „OFI auf 1–5-min funktioniert als Feature" ist eine PRD-v1-Behauptung („Retail-Edge unter HFT-Arbitragegrenze") ohne E-xx. Die einzige OFI-Messung im Register ist die S2-Tick-Rolle (gescheitert, E-03/E-05). Der Sprung auf 1–5-min ist plausibel, aber unbelegt — und auf längerem Horizont sinkt die Trade-Frequenz, was die N für jede Validierung weiter schrumpft (GM-4 verschärft).
- **Spot:** DROP (Cross-OFI BTC→Alt ist Perp-zentriert, Advocate stimmt zu).
- **Futures:** PILOT NUR nach INC-02-Klärung — die Reihenfolge ist nicht verhandelbar. Erst der Vorzeichen-Test (korreliert sign(OFI) mit Forward-Return oder mit Replenishment?), dann alles Weitere.
- **Optionen:** n/a.
- **Härtester Einwand (1 Satz):** Solange INC-02 ungeklärt ist, ist OFI in jeder Rolle potenziell systematisch falsch orientiert — ein Feature, das die falsche Richtung zeigt, ist schädlicher als gar keins, und der Horizont-Wechsel auf 1–5 min ist selbst unbelegt.
- **Minimale Bedingung für PILOT:** Isolierter Vorzeichen-Test ZUERST (sign(OFI_1-5min) vs. Forward-Return vs. MM-Replenishment); nur bei eindeutiger Aggressions-Orientierung weiter zu OOS-R² ≥ 1 % / bedingter AUC > 0.55. Scheitert der Vorzeichen-Test → DROP für den gesamten OFI-Stack (C-01/C-09/C-14-Erbe).

---

### A-8 — C-03 & C-04: Iceberg-Detection & Wavelet-Denoising

- **Steelman:** Beide umgehen K1 strukturell, weil sie als S/R-Marker (C-03) bzw. Vorverarbeitung (C-04) wirken, nicht als Taker-Trades — sie zahlen keine 11 bps. Das ist friktions-neutral und damit nicht von der Kostenbaseline getötet.
- **Der Advocate hat hier bereits selbst kapituliert — ich stimme zu:** Er stuft beide explizit als „schwächste ANWENDUNGS-Kandidaten des Clusters" ein, „Recording aktivieren, Validierung deferieren, nicht jetzt bauen". Beide UNTESTED ohne jede Evidenz (Alignment C-03/C-04). C-03 wird von C-40 inhaltlich dominiert (RPI liefert dieselbe Hidden-Liquidity DIREKT, C-03 nur via Auto-Korrelation) — und da ich C-40 selbst nur als gedeckeltes Forschungs-Recording durchlasse (A-2), erbt C-03 dessen Schwäche und ist als der dominierte Zwilling erst recht DROP.
- **C-04 ist ein Layer ohne Abnehmer:** Wavelet-Denoising ist Vorverarbeitung; sein R²-Lift-Claim (≥ 10 %, C-04 Gate) ist nur messbar, sobald ein VALIDIERTES Abnehmer-Signal existiert (OFI/Imbalance) — das es nicht gibt (C-01 SUSPECT/INC-02). Ein Vorverarbeitungs-Layer für ein nicht-existentes Signal ist nicht testbar.
- **Spot:** DROP. **Futures:** PARK (Recording-Pfad mitnehmen, Validierung deferiert) — exakt die Advocate-Position, ich widerspreche nicht. **Optionen:** n/a.
- **Härtester Einwand (1 Satz):** C-03 ist der von C-40 dominierte schwächere Zwilling und C-04 ist ein Vorverarbeitungs-Layer ohne validierten Abnehmer — beide sind PARK-bestenfalls, und der Advocate gesteht das selbst zu.
- **Minimale Bedingung für PILOT:** C-03: nur falls C-40-RPI-Recording NICHT realisiert wird (sonst redundant), Bounce-Rate ≥ 60 % auf orderbook.200-Recording. C-04: erst nachdem ein Abnehmer-Signal mind. PARTIAL+positiv ist, dann R²-Lift ≥ 10 %. Vorher beide PARK/DROP.

---

### A-9 — C-02: SpikeWavformer (Effizienz, kein Edge)

- **Steelman:** C-02 ist kein Alpha-Claim und konkurriert daher gar nicht mit der Kostenbaseline — es ist ein System-Effizienz-Claim (Analyse-Engine läuft nur bei echtem Signal), dessen Benchmark (F0/C-36) ohnehin gebaut werden muss. Das ist sauber abgegrenzt.
- **Abhängig von einem ungemessenen Benchmark:** C-02 ist nur bewertbar, sobald F0 läuft — und F0 selbst ist UNTESTED mit ungemessenem Recall (A-1). Ein Effizienz-Claim, dessen Benchmark selbst unvalidiert ist, kann nicht vor dem Benchmark validiert werden. C-02 ist Moonshot-Status, nichts implementiert (Alignment C-02: UNTESTED, kein SUSPECT, weil nicht in Replay verbaut). Es rangiert klar hinter dem deterministischen, in Tagen baubaren F0 — Advocate stimmt zu.
- **Spot/Futures:** PARK (an C-36 gekoppelt, nachgelagert). **Optionen:** n/a.
- **Härtester Einwand (1 Satz):** Ein Effizienz-Claim, dessen einziger Benchmark (F0) selbst ungemessen ist, ist doppelt deferiert und gehört eindeutig hinter F0 in die Warteschlange.
- **Minimale Bedingung für PILOT:** Nachgelagert nach validiertem F0; Dominanz-Test (Recall ≥ F0 bei ≤ 50 % Trigger-Rate) über 2 Kalibrierungs-Iterationen / 2 Monate Schattenbetrieb. Vorher PARK.

---

### Gesamt-Konsequenz aus A-9 / der Advocate-Selbstauskunft

Der Advocate gesteht zu: „Mit Ausnahme von C-06 ist JEDER Cluster-Claim UNTESTED; mein gesamtes Pro-Argument steht und fällt mit der Bereitschaft, ZUERST in Recording zu investieren." Die ehrliche Konsequenz für die Markt-Verdikte: Wenn alles an Recording-First hängt, UND Recording-First selbst kein Abbruchkriterium hat (A-1), DANN ist der gesamte Cluster ein **konditionales Forschungsprogramm**, kein Edge-Programm. Die einzige Sache, die kein neues Recording braucht, ist C-06 (PARTIAL, Daten vorhanden) — und dessen einfachste Rehabilitierung (Sign-Flip-MR) ist durch E-04 bereits gescheitert (A-4). Markt-Verdikte konsequent:

- **Spot:** durchgehend DROP/PARK. Kein Claim hat auf Spot einen messbaren Pfad, der nicht entweder am fehlenden Basis-Signal (C-25) oder an Perp-Zentrierung (C-01/C-40) scheitert.
- **Futures:** Einziges PILOT mit echtem Vorrang: **C-36/Recording — aber GEDECKELT, mit Sunset-Review** (nicht ADOPT-Pflicht). Alles andere PARK/bedingtes PILOT, sequenziell hinter (a) Recording-Sunset-Review, (b) INC-02-Klärung, (c) Existenz eines positiven Basis-Signals. C-06 PILOT als einziger nicht-recording-abhängiger Test.
- **Optionen:** durchgehend n/a oder schlechteste-ROI-Recording (IV-Archiv für einen 60–80 % illiquiden Markt, INC-04).

Die GRUNDHALTUNG „Evidenz schlägt Idee" und die Abbruchkriterium-Pflicht zwingen zu: Recording ja, aber als gedeckeltes Experiment mit Stop, nicht als Dauer-Pflichtposten — sonst rutscht der teuerste Betriebsposten des Registers ohne Falsifizierbarkeit ins PRD.
