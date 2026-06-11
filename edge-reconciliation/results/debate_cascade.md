# Debatte: Liquidations-Cascade / Kritikalität

Cluster **cascade** — Claims: C-15, C-26, C-27, C-28, C-29, C-30, C-39, CS-06, CS-10, CS-11 + Konzeptrest C-14 (Hawkes-Idee jenseits des REFUTED Estimators/Schwelle).
Strategien: CS-06 (Epidemiologisches Kaskaden-Cockpit, C-27/C-28/C-29/C-43), CS-10 (Cross-Coin-Contagion-Lead, CCM/C-27/C-28), CS-11 (Seismograph K1, C-14/C-39/C-15).
Quellen-Stand: alignment_matrix.md, evidence_register.md (E-01..E-18, GM-1..6).

---

## Advocate

### Vorbemerkung — die zentrale Lektion, an der jedes Pro-Argument hängt

Die alte Cascade-Familie (CS-01 = C-14 + C-15 + C-26) ist in ihrer Implementierung tot, und sie ist auf eine **lehrreiche, strukturell vermeidbare** Weise gestorben. Zwei harte Befunde aus GEEIGNETEN Fenstern markieren die Falle:

- **E-01 (Schwellen-Falle):** Der ρ-Estimator erreicht den importierten Threshold 0.85 nie — Median ~2e-7, sechs Größenordnungen darunter, konsistent über alle 5 Symbole, über 56k–87k Ticks. Der Fehler ist **nicht** „Kaskaden gibt es nicht", sondern „ein aus fremder Mikrostruktur importierter, absoluter, unkalibrierter Schwellwert wurde nie auf Erreichbarkeit geprüft" (INC-01).
- **E-02 (Spärlichkeits-Falle):** S1 feuert 0 Trades — `rho_below_threshold` ist die Ursache, **nicht** Datenmangel: Liquidationen sind auf 4/5 Symbolen reichlich vorhanden, nur `liquidations_below_min_events` auf BNB relevant (28.192 = 33 %; Spanne 794–28k je Symbol). Die Cascade-Detektion scheiterte estimator-/schwellen-bedingt, nicht event-bedingt — aber jedes neue volumen-/zähl-abhängige Verfahren läuft in **dieselbe** Spärlichkeits-Wand, sobald es auf ein dünnes Fenster trifft.

Mein gesamtes Pro-Argument für C-27/C-28/C-29 steht und fällt mit einer Behauptung: **Diese drei Verfahren vermeiden die E-01/E-02-Falle nicht durch besseres Tuning, sondern durch ihre mathematische Konstruktion.** Das wird in A-1 bis A-3 explizit gemacht; alles Übrige (A-4 bis A-8) baut darauf auf.

Randbedingung für alle Argumente: GM-1 (alles L0, kein Claim erreicht CONFIRMED) und die Kostenrelation (Friktion 11 bps Taker-Round-Trip > jede gemessene Roh-Edge). Cascade-Signale haben hier einen strukturellen Vorteil: sie sind **Risk-Off-/Timing-Gates**, kein Mikro-Edge-Scalping — sie müssen nicht die 11-bps-Schwelle per Trade schlagen, sondern die Verlustverteilung verschieben (Max-DD-Reduktion, Erschöpfungs-Entry mit großem Reversal-Move). Das ist die einzige Signalklasse im gesamten Register, die der Friktions-Wand strukturell ausweicht.

---

### A-1 — C-27 (Cori-Rₜ) vermeidet die E-01-Schwellen-Falle durch volumen-normierte Selbstverstärkung und einen empirisch fixierten Kernel statt eines importierten Thresholds

**Mechanismus:** Die Renewal-Gleichung Iₜ = Rₜ · Σ_{s≥1} I_{t−s}·ω_s normiert die laufende Liquidations-Inzidenz **auf ihre eigene jüngste Historie**. Die Entscheidungsgröße ist Rₜ, eine dimensionslose Verzweigungsrate mit dem **selbst-kalibrierenden** kritischen Punkt Rₜ = 1 — nicht ein absoluter Außenwert wie ρ = 0.85. Genau das ist die Schwäche, an der C-14 starb (E-01/INC-01): ρ = 0.85 wurde aus Bacry-Mastromatteo-Muzy importiert und nie auf Erreichbarkeit in Bybit-Mikrostruktur geprüft. Rₜ = 1 ist demgegenüber kein importierter Wert, sondern die mathematische Definition von Kritikalität (Branching-Prozess: subkritisch < 1 < superkritisch). Es **gibt keinen freien Threshold-Parameter, der ins Leere kalibriert werden könnte.**

- **Futures (Perpetuals):** **PILOT-Kandidat, stärkster im Cluster.** Zielmarkt der Quelle (C-27). Gamma-Konjugat-Posterior in geschlossener Form → kein ML-Training, kein Overfitting-Spielraum, deterministisch reproduzierbar. allLiquidation-Feed (seit 2024) liefert den Inzidenz-Strom direkt. Validierungs-Gate der Quelle ist bereits korrekt geschnitten: BA ≥ 0.55 OOS in ≥ 2 disjunkten Fenstern + Brier < Volumen-Baseline.
- **Spot:** **DROP/irrelevant.** Spot hat keine Zwangsliquidationen → kein Inzidenz-Punktprozess. Das epidemische Modell hat dort keinen Mechanismus.
- **Optionen:** **DROP als Primärsignal, PARK als Risiko-Overlay.** Kein eigener Liquidations-Strom; allenfalls als Markt-weites Risk-Off-Gate für Short-Vola (C-33) verwendbar — aber nur abgeleitet aus dem Futures-Rₜ.

**Stärkstes Einzelargument:** Rₜ ersetzt den toten importierten Absolut-Threshold (ρ=0.85, E-01) durch einen self-calibrating kritischen Punkt (Rₜ=1) und macht damit den exakten Tod von C-14 konstruktiv unmöglich.

**Was ich zugestehe:** Die Volumen-Normierung verteidigt gegen E-01, **nicht** gegen E-02. Der Generationszeit-Kernel ω_s muss aus Bulk-Historie geschätzt werden, und seine Stabilität über Regime ist laut Quelle selbst die kritischste Annahme (CS-06-Bruchpunkt). Ist ω_s instabil, kippt Rₜ zusammen mit C-28 (korrelierter Fehler).

**Validierungs-Gate (PILOT):** Vorgeschaltetes **Distributions-/Erreichbarkeits-Gate analog E-01** (siehe A-7): Erreicht Rₜ überhaupt jemals den Bereich ≥ 1 in der Bulk-Historie? Erst danach BA ≥ 0.55 OOS / Brier < Volumen-Baseline auf event-getriggertem CV (≥ 30 Kaskaden, nicht Kalender-Fenstern).

---

### A-2 — C-28 (NB-k) vermeidet die E-02-Spärlichkeits-Falle, indem es Spärlichkeit zur Messgröße macht statt sie als Datenmangel zu erleiden

**Mechanismus:** Die alten Verfahren brauchten **dichte** Events, um zu feuern (E-02: kein Threshold ohne genug Liquidationen). C-28 dreht das um: Es modelliert die Offspring-Verteilung (Folgeliquidationen je Auslöser) als Negativ-Binomial NB(R,k); der Dispersionsparameter **k misst genau die Tail-Heterogenität** — kleines k = seltene, aber explosive Kaskaden. Spärlich-aber-explosiv ist hier kein Bug, sondern das Signal selbst. Die Edge-Hypothese ist ökonomisch sauber: Standard-Risikomaße betrachten Mittelwerte (R), die Tail-Dispersion (k) ist nicht eingepreist.

- **Futures:** **PILOT, aber gebündelt mit C-27.** Teilt den ω_s-Kernel von C-27 (kein freier Parameter) → schließt mit C-27 zusammen am selben Bulk-Datensatz auf. Validierungs-Gate scharf und ehrlich: Precision@k-Lift ≥ 1.2 OOS in ≥ 2 Fenstern UND NB signifikant überdispers gegen Poisson (LR-Test p < 0.05). Letzteres ist ein **echter Nullhypothesen-Test** — bestehen oder fallen, kein graduelles Schönrechnen.
- **Spot / Optionen:** **DROP** (kein Liquidations-Offspring-Prozess; identisch zu A-1).

**Stärkstes Einzelargument:** C-28 macht aus der E-02-Spärlichkeit (die C-14/C-26 zum Schweigen brachte) die eigentliche Messgröße — der Überdispersions-LR-Test p < 0.05 ist ein binäres Falsifikations-Gate, kein tunbarer Schwellwert.

**Was ich zugestehe:** k-Schätzung braucht **viele** Kaskaden für Stabilität — und genau die liefert ein 24h-Fenster nicht (E-02, GM-6). Die Spärlichkeit ist zwar das Signal, aber sie ist auch der Feind der Schätz-Stabilität. Ohne Bulk-Historie mit dutzenden Kaskaden-Episoden ist k nicht belastbar schätzbar; der LR-Test hat dann keine Power.

**Validierungs-Gate (PILOT):** Identisch gebündelt mit C-27 am Bulk-Datensatz; harter Abbruch bei p ≥ 0.05 oder Lift ≤ 1.2.

---

### A-3 — C-29 (Avalanche Shape Collapse) liefert das, was S3 nachweislich gefehlt hat: ein Restdauer-/Exit-Timing-Signal — und es ist von der E-01/E-02-Threshold-Frage komplett entkoppelt

**Mechanismus:** C-29 prognostiziert aus dem Profil der **laufenden** Kaskade (reskalierte Aktivitätsrate, crackling-noise Shape-Collapse auf invertierte Parabel) die **Restdauer**. Es braucht keinen Kritikalitäts-Threshold (kein ρ, kein Rₜ=1) — es greift erst, wenn eine Kaskade bereits läuft, und beantwortet nur „wie lange noch". Damit ist es der einzige Cluster-Ansatz, der die E-01-Schwellen-Frage gar nicht erst stellt.

Die empirische Motivation ist im Register **direkt belegt**: E-10 (S3-Tail-Signatur) zeigt, dass die schlechtesten Trades 1.7–3.0× länger gehalten wurden als der Durchschnitt — robust über 5 Symbole UND beide Mirror-Arme (BTC/ETH/SOL). Halte-/Burst-DAUER ist also ein **empirisch nachgewiesener** Verlusttreiber, und S3 hatte kein Werkzeug dagegen (E-07: der Time-Stop war wegen Wall-Clock-Bug faktisch tot, 1× statt 68×). C-29 adressiert exakt diese Lücke mit einem Restdauer-MAE-Gate.

- **Futures:** **PILOT, eigenständig vom ω_s-Risiko der A-1/A-2-Bündelung.** Parameter sind nur Detektionsschwelle + Fenstergröße (geringer Overfitting-Spielraum). Validierungs-Gate: Collapse-Residual ≤ 30 % OOS + Restdauer-MAE < Konstant-Mittelwert-Baseline.
- **Spot:** **DROP** (kein Liquidations-Burst-Prozess).
- **Optionen:** **DROP** als Primär; theoretisch als Hedge-Unwind-Timing denkbar, aber ohne Datengrundlage (INC-04) reine Spekulation.

**Stärkstes Einzelargument:** C-29 ist threshold-frei (umgeht E-01 strukturell) und füllt exakt die durch E-10 belegte und durch E-07 offengelassene Exit-Timing-Lücke von S3 — es ist der einzige Cluster-Ansatz mit direkter empirischer Motivation aus diesem Register.

**Was ich zugestehe:** Die Annahme „Bybit-Kaskaden folgen einer universellen Skalenfunktion" ist physikalisch importiert und auf diesem Markt unbelegt; scheitert der Shape-Collapse (Residual > 30 %), ist das Signal wertlos. Und es braucht wieder genug Burst-Events auf den Trainings-Splits (E-02-Randbedingung).

**Validierungs-Gate (PILOT):** Residual ≤ 30 % + MAE < Baseline auf event-CV; Abbruch bei Residual > 30 %.

---

### A-4 — Der Konzeptrest von C-14 (Reflexivität/Branching) ist NICHT durch E-01 widerlegt — nur Schwelle und Single-Channel-Estimator sind tot

Die Alignment-Matrix trennt explizit (Statusregel 4; C-14-Eintrag): E-01 ist REFUTED für **Schwelle 0.85 + Estimator-Output**, das **Branching-/Reflexivitäts-Konzept bleibt UNTESTED**. Methodische Schwäche der widerlegenden Evidenz, die ich legitim benennen darf (Advocate-Regel): E-01 misst den **Single-Channel**-Hawkes-Estimator-Output; die Floor-Saturation bei ~1e-3 auf BTC/ETH p90/p95 ist laut E-01 selbst ein **numerisches Artefakt**, kein zweiter Modus. Das heißt: E-01 falsifiziert sauber „dieser Estimator erreicht 0.85", aber **nicht** „eine normierte Branching-Ratio-Approximation (Hardiman/Bouchaud, PRD-kestrel-Variante) misst keine Kritikalität". Letzteres ist nie getestet worden.

- **Futures:** **PILOT nur in der normierten Branching-Ratio-Form** (genau die, die PRD-kestrel als „risikoarmen Start" vorschlägt), niemals in der M14-0.85-Form. C-27 (Rₜ) ist faktisch die sauberere Inkarnation derselben Idee — daher: C-14-Konzept geht in C-27 auf, M14-Implementierung bleibt REFUTED.
- **Spot/Optionen:** **DROP** (Liquidations-Reflexivität existiert dort nicht).

**Stärkstes Einzelargument:** E-01 tötet einen Estimator und eine Zahl, nicht ein Konzept — und das überlebende Konzept ist bereits in C-27 sauber re-implementiert.

**Was ich zugestehe:** Das ist kein eigenständiger neuer Ansatz, sondern eine Umetikettierung. Wenn C-27 validiert, braucht niemand C-14 separat; validiert C-27 nicht, ist auch der „Konzeptrest" praktisch wertlos. C-14 verdient kein eigenes Pilot-Budget neben C-27.

---

### A-5 — C-39 (Kaskaden-Anatomie) und C-26 (SIR) liefern Bybit-exklusive Stress-Datenströme, die der E-02-Spärlichkeit eine zweite, unabhängige Messachse entgegensetzen

C-39 erweitert C-26 um drei Bybit-exklusive Ströme: Bankruptcy-Preis (impliziter Hebel der Kohorte aus |1 − p_bankruptcy/p_mark|), Insurance-Pool-Delta (Slippage-Proxy: Fill schlechter als Bankruptcy = echte Illiquidität), ADL-`pr` (plattformweiter Stress-Score). Strategischer Wert: Diese Ströme messen **Stress-Intensität pro Event**, nicht nur Event-Zähl-Dichte. Wo E-02 zeigt, dass reine Event-Counts in dünnen Fenstern verstummen, liefert der Bankruptcy-Preis auch bei **wenigen** Liquidationen ein Hebel-/Illiquiditäts-Signal — eine zur Inzidenz orthogonale Achse. Das ist genau die Diversifikation gegen Spärlichkeit, die C-14/C-26 fehlte.

- **Futures:** **PILOT als Risk-Off-Ampel**, nicht als Direktional-Alpha. Gate der Quelle: Recall ≥ 90 % auf Top-Events; Abbruch bei Recall < 70 % → degradiert zur F0-Grobampel. Sauber gestuftes Abbruchkriterium.
- **Spot/Optionen:** **DROP** als Primär; Futures-Stress-Score als markt-weites Overlay für Spot-Sizing / Options-Short-Vola denkbar (PARK).

**Stärkstes Einzelargument:** Der Bankruptcy-Preis gibt pro Einzel-Liquidation eine Hebel-/Illiquiditäts-Messung — eine zur Event-Dichte orthogonale Achse, die in genau den dünnen Fenstern trägt, in denen E-02 die zähl-basierten Verfahren verstummen lässt.

**Was ich zugestehe:** Insurance/ADL haben **kein REST-Archiv** (C-39-Abhängigkeit) → ohne ≥ 1 Woche (Live-Score) bis 3 Monate (Backtest) Eigenaufzeichnung ist hier gar nichts messbar. Die schärfsten Datenströme sind die am schlechtesten verfügbaren. Reiner Live-Score ohne Backtest ist außerdem nicht walk-forward-validierbar.

**Validierungs-Gate (PILOT):** Erst nach Aufzeichnungs-Vorlauf; Recall ≥ 90 % gegen gelabelte Großevents; bis dahin PARK.

---

### A-6 — Die Strategien CS-06 / CS-11 / CS-10: Cockpit > Seismograph > Cross-Coin (in dieser Reihenfolge der Pilot-Würdigkeit)

- **CS-06 (Epidemiologisches Kaskaden-Cockpit, C-27+C-28+C-29+C-43):** **stärkster Strategie-Pilot des Clusters.** Baut ausschließlich auf den drei threshold-/volumen-robusten Ansätzen (A-1..A-3) + Conformal-Sizing (C-43). Kein einziges der REFUTED/SUSPECT-Module aus PRD-v1 ist verbaut — anders als CS-11. Methodisch ehrlich: die Quelle benennt die schwächste Annahme selbst (stabiles ω_s, korrelierter C-27/C-28-Fehler).
- **CS-11 (Seismograph K1, C-14+C-39+C-15):** **PILOT nur nach Modul-Ersetzung.** Erbt direkt das C-14-Schwellen-Risiko (E-01) und C-15 (SUSPECT, nie ausgelöst weil ρ-Gate blockierte, E-02). PRD-kestrel adressiert das bereits durch Branching-Ratio-Approximation statt 0.85 (siehe A-4) — d. h. CS-11 ist überlebensfähig **nur**, wenn man C-14→C-27 und das ρ-Gate→Rₜ-Gate ersetzt. Dann konvergiert CS-11 inhaltlich auf CS-06 + Omori-Exit (C-15). Das Lebenszyklus-Framing (Risk-Off vor Kaskade / kein Entry während / Erschöpfungs-Entry danach) ist konzeptionell wertvoll und friktions-robust (großer Reversal-Move statt Mikro-Edge).
- **CS-10 (Cross-Coin-Contagion-Lead, CCM+C-27+C-28):** **PARK.** Doppelte Hypothek: dieselbe Panel-Daten-Lücke wie S5 (E-14, single_symbol_replay_unsupported 100 %) UND die CCM-Takens-Einbettung auf verrauschten Multi-Coin-Liquidations-Strömen ist laut Critic „gestreckt". Erst aufschließbar, wenn der Panel-Harness existiert.

- **Futures:** wie oben (alle drei Futures-only).
- **Spot/Optionen:** **DROP** für alle drei.

**Stärkstes Einzelargument:** CS-06 ist die einzige Cascade-Strategie, die komplett auf threshold-freien, volumen-normierten Modulen steht und **kein** REFUTED/SUSPECT-PRD-v1-Modul mitschleppt — sie ist die saubere Neugeburt von CS-01 ohne dessen E-01/E-02-Erbschulden.

**Was ich zugestehe:** Alle drei sind UNTESTED, nicht implementiert. CS-06 und CS-10 teilen über C-27/C-28 denselben ω_s-Single-Point-of-Failure — ein korrelierter Fehler, der beide gleichzeitig kippt. Die „Ensemble-Diversität" zwischen C-27, C-28 und CS-10 ist geringer, als die getrennten IDs suggerieren.

---

### A-7 — Das billigste, härteste Pilot-Gate für den ganzen Cluster existiert schon als Vorlage: der E-01-Distributions-Check

Bevor irgendein Cascade-Strategie-Budget fließt, lässt sich der teuerste Fehler von C-14 für wenig Geld ausschließen. Die Alignment-Matrix nennt das explizit (Kritische Datenlücken #4; C-30-Eintrag): ein **reiner Distributions-Check analog E-01** auf den normierten Schätzern beantwortet *vor* jedem Strategie-Aufwand die Frage, die C-14 fatal war — **wird die kritische Region überhaupt jemals erreicht?**

- Für **C-27:** Erreicht Rₜ in der Bulk-Historie jemals ≥ 1 (und mit welcher Frequenz)?
- Für **C-30 (Natural Time κ₁):** Nähert sich κ₁ je dem theoretischen 0.070? C-30 trägt **dasselbe** unkalibrierte-Threshold-Risiko wie C-14 (importierter theoretischer Wert) — daher **PILOT nur nachrangig zu C-27, mit vorgeschaltetem κ₁-Erreichbarkeits-Gate**; ohne diesen Check ist C-30 ein C-14-Wiedergänger.

**Stärkstes Einzelargument:** Der Fehler, der C-14 tötete (E-01), ist für alle Nachfolger mit einem billigen Distributions-Check abprüfbar, bevor ein Euro Strategie-Aufwand fließt — dieses Gate ist Pflicht-Vorschaltung für C-27, C-30, CS-06, CS-11.

**Was ich zugestehe:** Der Distributions-Check beantwortet nur „Schwelle erreichbar?", nicht „prädiktiv?". Erreichbarkeit ist notwendig, nicht hinreichend. Und er braucht bereits die Bulk-Historie, die wir noch nicht aufgezeichnet haben.

---

### A-8 — Warum die Friktions-Wand (Kostenbaseline) den Cluster WENIGER trifft als jeden anderen

Die Kernrelation des Evidence-Registers — Friktion 11 bps Round-Trip > jede gemessene Roh-Edge — hat S2 und S3 erlegt (E-16: Friktion ~35× Richtung; E-09: Roh-Edge -5.8 bps < 11 bps). Cascade-Signale sind die einzige Klasse, die dieser Wand strukturell ausweicht, weil sie **nicht** per Trade eine Mikro-Edge gegen die Fee verdienen müssen:

1. **C-39/C-26/CS-11 als Risk-Off:** Wert liegt in Max-DD-Reduktion (Verlust-VERMEIDUNG), nicht in Per-Trade-Edge. Eine vermiedene -50-bps-Kaskade (vgl. E-09 min bps: -56.6 BNB, -48.9 SOL, -47.7 BTC) bezahlt viele 11-bps-Round-Trips.
2. **C-15/C-29 Erschöpfungs-Entry:** zielt auf den großen Mean-Reversion-Move NACH der Kaskade — Reversal-Amplituden weit über 11 bps (E-11: BNB -195→+187 bps Mirror-Flip zeigt die Größenordnung handelbarer Reversal-Bewegungen, auch wenn dieser Einzelfall N=16/NIEDRIG belastbar ist).

- **Futures:** wie oben.
- **Spot:** DROP (kein Mechanismus). **Optionen:** der Futures-Stress-Score als Risk-Off-Overlay für C-33 Short-Vola ist der einzige plausible Options-Bezug, aber datenlos (INC-04).

**Stärkstes Einzelargument:** Cascade-Signale müssen die 11-bps-Friktions-Wand nicht pro Trade schlagen — sie verschieben die Verlustverteilung (DD-Reduktion / großer Reversal-Move), und das ist die einzige Signalklasse im Register, der die Friktions-Wand strukturell weniger anhaben kann.

**Was ich zugestehe:** Das ist ein **Mechanismus-Argument ohne einen einzigen positiven Outcome-Befund.** Im gesamten Register gibt es null Evidenz, dass irgendein Cascade-Signal Geld verdient — E-01/E-02 zeigen nur, dass das alte gar nicht erst feuerte. Der DD-Reduktions-Anspruch (C-39 ≥ 25 %, CS-11 ≥ 20 %) ist reine PRD-Behauptung. Und GM-6 bleibt: ohne ein stress-reiches Fenster ist selbst ein gutes Cascade-Signal nicht falsifizierbar.

---

### Advocate — Synthese je Markt (für den Judge)

| Ansatz | Spot | Futures | Optionen |
|---|---|---|---|
| C-27 Cori-Rₜ | DROP | **PILOT (Cluster-Spitze)** | DROP (Overlay: PARK) |
| C-28 NB-k | DROP | **PILOT (mit C-27 gebündelt)** | DROP |
| C-29 Avalanche | DROP | **PILOT (eigenständig, E-10-motiviert)** | DROP |
| C-30 Natural-Time κ₁ | DROP | PILOT (nachrangig, κ₁-Erreichbarkeits-Gate Pflicht) | DROP |
| C-39 Kaskaden-Anatomie | DROP | PILOT (Risk-Off, nach Aufzeichnungs-Vorlauf) | Overlay PARK |
| C-26 SIR | DROP | geht in C-39 auf | DROP |
| C-15 GR+Omori | DROP | PILOT nur als Erschöpfungs-Exit (in CS-06/11) | DROP |
| C-14 Konzeptrest | DROP | geht in C-27 auf; M14-Form DROP | DROP |
| CS-06 Cockpit | DROP | **PILOT (sauberster Strategie-Pilot)** | DROP |
| CS-11 Seismograph | DROP | PILOT nur nach C-14→C-27-Ersetzung | DROP |
| CS-10 Cross-Coin | DROP | PARK (Panel-Harness fehlt, E-14) | DROP |

**Pflicht-Vorschaltung für alle Futures-Pilots:** E-01-analoger Distributions-/Erreichbarkeits-Check (A-7) + event-getriggertes CV auf Bulk-Historie mit ≥ 30 Kaskaden statt Kalender-Fenster (E-02/GM-6).

---

*Skeptic antwortet ab hier — bitte Punkt für Punkt auf A-1 bis A-8.*
