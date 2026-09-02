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

---

## Skeptic

**Rahmen:** Ich teile die Grundhaltung des Advocates, dass die Cascade-Familie *konzeptionell* nicht durch E-01/E-02 erledigt ist (alignment_matrix Statusregel 4; C-14 = REFUTED nur für Schwelle+Estimator, Konzept UNTESTED). Mein Angriff zielt nicht auf das Konzept, sondern auf die Behauptung, der neue Ansatz vermeide die Fallen **durch Konstruktion** statt durch Tuning — und auf die Frage, ob die behauptete Friktions-Immunität (A-8) überhaupt einen messbaren Bezugspunkt hat. Drei Märkte: Spot ist im ganzen Cluster mechanismuslos (kein Liquidations-Punktprozess) — ich folge dem Advocate hier bei DROP für ALLE Ansätze und wiederhole es unten nicht jedes Mal. Optionen sind durchgängig datenlos (INC-04, C-33). Der reale Streit ist Futures.

---

### S-1 auf A-1 — C-27 (Cori-Rₜ): „self-calibrating" verschiebt den freien Parameter, er verschwindet nicht

**Steelman:** Der Advocate hat recht, und das ist sein stärkster Cluster-Punkt: Rₜ=1 ist *definitorisch* der kritische Punkt eines Verzweigungsprozesses, kein importierter Außenwert wie ρ=0.85 (E-01). Damit ist der **exakte Tod von C-14 (E-01/INC-01) konstruktiv ausgeschlossen** — die Schwelle kann nicht mehr „ins Leere kalibriert" werden. Diesen Fehlertyp-Vermeidungs-Punkt erkenne ich vorbehaltlos an; er ist der eigentliche Fortschritt des Clusters.

**Aber — drei Einwände, die der Advocate selbst zur Hälfte einräumt und dann verharmlost:**

1. **Rₜ=1 ist nur kritischer Punkt, WENN der Prozess ein Verzweigungsprozess IST.** Das ist eine *Modellannahme über Bybit-Liquidationen*, kein freies Geschenk. Die Renewal-Gleichung setzt voraus, dass Folgeliquidationen tatsächlich epidemisch von Vorläufer-Liquidationen erzeugt werden (Offspring-Struktur), nicht von einem gemeinsamen exogenen Preis-Schock, der alle gehebelten Positionen *gleichzeitig* trifft. Bei einem Margin-Call-Crash ist Letzteres der Normalfall — dann ist Rₜ ein fehlspezifiziertes Maß, und Rₜ=1 bedeutet gar nichts. Der claims_register-Eintrag C-27 nennt genau das („Liquidations-Punktprozess ist strukturell isomorph zum epidemischen Inzidenz-Punktprozess") als **Kernannahme** — also als *ungetestete Voraussetzung*, nicht als Befund. Self-calibrating heißt nur: der Schwellwert ist endogen. Es heißt **nicht**: das Modell ist korrekt spezifiziert.

2. **Der freie Parameter ist nicht weg, er heißt jetzt ω_s.** Der Advocate räumt das unter „Was ich zugestehe" ein, zieht aber nicht die Konsequenz. Der Generationszeit-Kernel ω_s ist ein vollständiger funktionaler Parameter (Form + Länge), aus Bulk-Historie geschätzt, laut Quelle selbst der **kritischste Bruchpunkt** (claims_register C-27: „Strategie-A-Bruchpunkt"; alignment_matrix CS-06). Rₜ ist *linear* in der ω_s-Gewichtung — eine falsch geschätzte Kernel-Länge skaliert Rₜ direkt und verschiebt die Überschreitung von Rₜ=1 beliebig. „Self-calibrating" tauscht einen sichtbaren skalaren Schwellwert (0.85, sofort als unerreichbar falsifizierbar — das war der *Vorteil* von E-01!) gegen einen **versteckten funktionalen Parameter, dessen Fehlkalibrierung sich NICHT in einem simplen Distributions-Check zeigt.** Das ist eher eine Verschlechterung der Falsifizierbarkeit als eine Verbesserung.

3. **Schätzvarianz bei E-02-Spärlichkeit — der eigentliche Knockout.** E-02 zeigt `liquidations_below_min_events` 794–28.192 je Symbol (BNB 33 % der Ticks unter Mindestzahl). Cori-Rₜ ist genau das Verfahren, das in der Epidemiologie bei *niedriger Inzidenz* berüchtigt instabil ist: die Gamma-Posterior-Varianz von Rₜ skaliert ~1/(Σ erwartete Fälle im Fenster). Bei wenigen Events pro Schätzfenster sind die glaubwürdigen Intervalle so breit, dass „Rₜ > 1" statistisch nicht von „Rₜ < 1" unterscheidbar ist. Der Advocate beziffert weder die Fensterlänge noch die Varianz — **genau die Zahlen, nach denen der Auftrag fragt und die über PILOT/DROP entscheiden.** Solange das nicht beziffert ist, ist „Rₜ schätzbar" eine Behauptung, kein Befund. Die geschlossene Posterior-Form macht das *schlimmer*, nicht besser: sie liefert auch bei N=3 Events einen scheinbar präzisen Punktschätzer mit riesiger, gern ignorierter Varianz.

- **Futures:** Der Advocate-PILOT ist **nur** akzeptabel, wenn das Validierungs-Gate die Schätzvarianz selbst zum Gate macht — nicht nur „erreicht Rₜ je ≥ 1?" (A-7), sondern „erreicht das **untere** glaubwürdige Intervall von Rₜ je ≥ 1, und wie oft?". Sonst misst man Rauschspitzen.
- **Härtester Einwand:** Self-calibrating ist nur ein Umzug des freien Parameters vom sichtbaren Schwellwert (0.85) zum versteckten Kernel ω_s — und der Kernel ist bei E-02-Spärlichkeit weder stabil schätzbar noch durch einen billigen Distributions-Check (A-7) prüfbar.
- **Minimale Bedingung für PILOT (statt DROP):** (a) Bulk-Historie mit ≥ 30 abgegrenzten Kaskaden (GM-6) vorhanden; (b) **gemeldete Posterior-Breite** von Rₜ pro Schätzfenster, nicht nur Punktschätzer; (c) Gate auf dem unteren Kredibilitäts-Intervall. Ohne (b) ist es DROP, weil dann „Rₜ > 1" ein nicht-falsifizierbares Artefakt der Punktschätzung sein kann.

---

### S-2 auf A-2 — C-28 (NB-k): das LR-Test-Gate ist ehrlich, aber bei E-02-Spärlichkeit machtlos — und kein eigenständiger Schuss

**Steelman:** Der Überdispersions-LR-Test (p < 0.05 NB gegen Poisson) ist ein **echtes binäres Falsifikations-Gate**, kein tunbarer Schwellwert — das ist methodisch sauberer als alles in PRD-v1, und der Advocate verdient Anerkennung dafür, dass er ein Verfahren mit eingebautem Null-Test wählt.

**Aber:**

1. **Das Gate hat keine Power, genau wo es zählt.** Der Advocate räumt ein, dass k „viele Kaskaden" braucht. Schärfer: Der LR-Test gegen Poisson hat bei kleiner Eventzahl (E-02) **niedrige statistische Power** — er übersieht echte Überdispersion (Typ-II), nicht weil sie fehlt, sondern weil N zu klein ist. Ein p ≥ 0.05 ist dann *nicht* „NB widerlegt", sondern „Fenster zu dünn" — also derselbe Nicht-Falsifizierbarkeits-Zustand wie GM-6. Das Gate fällt nicht ehrlich, es fällt *uninformativ*.
2. **k ist die instabilste Größe überhaupt.** Der Dispersionsparameter eines NB ist notorisch schwer zu schätzen; seine Schätzvarianz explodiert bei kleinem N und gerade im Tail (kleines k = die seltenen explosiven Kaskaden — also die wenigsten Datenpunkte). Die „Edge" (Tail-Dispersion nicht eingepreist) hängt an der am schlechtesten schätzbaren Zahl des ganzen Clusters.
3. **Kein unabhängiger Schuss (GM-2).** C-28 teilt den ω_s-Kernel mit C-27 (claims_register C-28: „Generationszeit-Fenster aus C-27 fixiert"). Der Advocate verkauft das als „kein freier Parameter" — korrekt — verschweigt aber die Kehrseite: **C-27 und C-28 sind statistisch nicht unabhängig.** Sie laufen auf demselben Bulk-Datensatz, mit demselben Kernel, auf demselben Punktprozess. Das ist im Multiple-Testing-Sinn (GM-2, alignment_matrix Statusregel 5) **kein zweiter unabhängiger Bestätigungs-Schuss**, sondern dieselbe Hypothese in NB-Notation. Die im Auftrag genannten „drei Schüsse auf dasselbe Ziel" (Cori/NB-k/Avalanche) sind über C-27/C-28 mindestens 1,5 korrelierte Schüsse.

- **Futures:** PILOT nur gebündelt — aber dann muss der Judge wissen, dass C-27+C-28 **ein** Test ist, nicht zwei. Eine getrennte ADOPT-Zählung wäre Doppelzählung.
- **Härtester Einwand:** Der ehrliche LR-Test verliert bei E-02-Spärlichkeit seine Power, sodass ein „Bestehen" ein N-Artefakt und ein „Fallen" uninformativ sein kann — und über den geteilten ω_s-Kernel ist C-28 ohnehin kein von C-27 unabhängiger Befund (GM-2).
- **Minimale Bedingung für PILOT:** Power-Analyse VOR dem Run (wie viele Kaskaden braucht der LR-Test für 80 % Power bei plausiblem k?) + explizite Kennzeichnung als **gemeinsamer** Test mit C-27 im Verdict. Ohne Power-Analyse: DROP, weil das Gate sonst nur scheinbar binär ist.

---

### S-3 auf A-3 — C-29 (Avalanche Shape Collapse): der einzige empirisch motivierte Ansatz — aber Shape-Collapse braucht die Eventdichte, die E-02 verneint

**Steelman:** Der Advocate hat hier seinen *besten* Punkt, und ich sage es explizit: C-29 ist der **einzige** Cluster-Ansatz mit direkter empirischer Motivation aus diesem Register (E-10: schlechteste Trades 1.7–3.0× länger gehalten, robust über 5 Symbole UND beide Mirror-Arme; E-07: Time-Stop war wegen Wall-Clock-Bug faktisch tot). Halte-/Burst-Dauer IST ein nachgewiesener Verlusttreiber, und C-29 ist threshold-frei — es umgeht die E-01-Frage strukturell, weil es erst greift, wenn eine Kaskade *läuft*. Das ist real und der Judge sollte es würdigen.

**Aber — der Auftrag fragt scharf nach der Eventdichte, und die Antwort ist ungünstig:**

1. **Shape-Collapse ist ein Vielprobenverfahren.** Crackling-noise Shape-Collapse (Sethna et al.) kalibriert die universelle Skalenfunktion, indem **viele** Avalanche-Profile reskaliert und übereinandergelegt werden — die Methode lebt davon, über Hunderte Avalanches zu mitteln. Auf einem **Bybit-Einzelsymbol** in den verfügbaren ~24h-Fenstern (GM-6) gibt es nicht annähernd genug abgegrenzte Liquidations-Bursts dafür. E-02 zeigt die Spärlichkeit direkt; der Advocate räumt „braucht genug Burst-Events auf den Trainings-Splits" ein, beziffert aber nicht, wie viele Bursts ein Einzelsymbol-Fenster liefert. Verdacht (begründet): **deutlich unter dem, was ein stabiler Collapse braucht.**
2. **E-10 motiviert Restdauer-Prognose generell — nicht den Shape-Collapse-MECHANISMUS.** Das ist der subtile Transfer-Fehler. E-10 sagt: lange Trades sind schlecht. Daraus folgt, dass *irgendein* Restdauer-/Exit-Timing-Signal wertvoll wäre — ein simpler Hazard-Schätzer oder gar ein fixer Time-Stop (der wegen E-07 nie getestet wurde!) täte es vielleicht auch. E-10 ist **kein** Beleg, dass Bybit-Kaskaden einer *universellen invertierten Parabel* folgen. Der Advocate gesteht das unter „Was ich zugestehe" zu — gut —, aber es entwertet das „stärkste Einzelargument": die empirische Motivation stützt die *Lücke*, nicht das *spezifische Werkzeug*.
3. **Billigerer Konkurrent existiert.** Bevor man einen physikalisch importierten Shape-Collapse kalibriert, sollte man den simplen, threshold-freien Time-Stop, der wegen des Wall-Clock-Bugs (E-07) nie gemessen wurde, *zuerst* korrekt laufen lassen (E-15 pending). Wenn ein reparierter Time-Stop die E-10-Tail-Signatur schon zu 80 % einfängt, ist der Opportunitätskosten-Fall (Prüfschwerpunkt 4) gegen C-29 erdrückend.

- **Futures:** PILOT eigenständig vom ω_s-Risiko — das stimmt, C-29 hängt **nicht** am Kernel (Pluspunkt gegenüber C-27/C-28). Aber das Residual-≤-30-%-Gate ist wertlos, wenn zu wenige Bursts für einen Collapse da sind: dann ist das Residual ein Overfit an eine Handvoll Profile.
- **Härtester Einwand:** Shape-Collapse braucht viele Avalanches zur Kalibrierung, die Eventdichte auf Bybit-Einzelsymbolen (E-02, GM-6) liefert sie vermutlich nicht, und E-10 motiviert nur die Restdauer-Lücke generisch — nicht ausgerechnet die universelle Skalenfunktion.
- **Minimale Bedingung für PILOT:** (a) Beziffern, wie viele abgegrenzte Bursts ≥ Mindestgröße pro Symbol-Fenster verfügbar sind, und Nachweis, dass der Collapse mit dieser Zahl überhaupt identifizierbar ist; (b) **Baseline-Pflicht:** Restdauer-MAE muss nicht nur den Konstant-Mittelwert, sondern den reparierten Time-Stop (E-15) UND einen simplen Hazard-Schätzer schlagen. Schlägt es nur den trivialen Mittelwert, ist es DROP (Scheinsieg gegen Strohmann).

---

### S-4 auf A-4 — C-14-Konzeptrest: Zustimmung, mit Verschärfung

**Steelman:** Der Advocate hat recht: E-01 tötet einen Estimator und eine Zahl (0.85), nicht das Branching-Konzept (alignment_matrix Statusregel 4, C-14-Eintrag explizit). Und er ist *fair*, indem er selbst sagt, dies sei „keine eigenständige neue Idee, sondern eine Umetikettierung", die in C-27 aufgeht und **kein eigenes Pilot-Budget** verdient. Dem stimme ich vollständig zu — hier gibt es keinen Streit.

**Einzige Verschärfung:** Genau weil C-14-Konzept vollständig in C-27 aufgeht, darf es im Verdict **nicht als separater Posten** erscheinen, der die Cluster-Evidenzbasis optisch verbreitert. Sonst entsteht der Eindruck mehrerer unabhängiger Cascade-Ansätze, wo es real einer ist (Rₜ) plus zwei daran gekoppelte (NB-k über Kernel, Konzeptrest über Identität).

- **Futures:** DROP als eigener Posten; geht in S-1/C-27 auf. **Minimale Bedingung:** keine — korrekt als „in C-27 absorbiert" zu führen, nicht als eigener PILOT.

---

### S-5 auf A-5 — C-39 (Kaskaden-Anatomie): die schärfste Achse ist die am schlechtesten verfügbare — und der Recall-Claim ist outcome-frei

**Steelman:** Der Bankruptcy-Preis als zur Event-*Dichte* orthogonale Hebel-/Illiquiditäts-Achse ist ein echtes Argument: er liefert auch bei *wenigen* Liquidationen ein Stress-Signal, genau dort, wo zähl-basierte Verfahren (C-27/C-28) an E-02 verstummen. Das ist die einzige Diversifikation gegen Spärlichkeit im Cluster, die nicht selbst zähl-abhängig ist — konzeptionell stark.

**Aber:**

1. **GM-6 / Daten-Vorlaufzeit ist hier am tödlichsten.** Der Advocate gesteht es: Insurance/ADL haben **kein REST-Archiv** (claims_register C-39; alignment_matrix C-39). Das bedeutet 1 Woche (Live-Score) bis **3 Monate** (Backtest) Eigenaufzeichnung, BEVOR überhaupt etwas messbar ist — und reiner Live-Score ohne Backtest ist nicht walk-forward-validierbar (bleibt damit unter GM-1 auf L0-äquivalent). Die orthogonale Achse ist real, aber sie ist monatelang **leer**. Das ist kein PILOT, das ist ein PARK mit Aufzeichnungs-Auftrag.
2. **Recall ≥ 90 % ist ein Detektions-Gate, kein Outcome-Gate.** Selbst perfekter Recall auf gelabelte Großevents sagt **nichts** darüber, ob das Risk-Off-Signal Geld spart — das ist exakt die A-8-Zirkularität (siehe S-8). Ein Detektor kann 95 % der Kaskaden erkennen und trotzdem netto verlieren, wenn die False-Positive-Ausstiege mehr Carry kosten als die vermiedenen Drawdowns.

- **Futures:** PARK, nicht PILOT — der Advocate landet selbst bei „bis dahin PARK". Ich mache das verbindlich: ohne Aufzeichnungs-Vorlauf ist es nicht pilotierbar.
- **Härtester Einwand:** Die einzige spärlichkeits-robuste Achse des Clusters ist monatelang datenleer (GM-6, kein REST-Archiv), und ihr Recall-Gate misst Detektion, nicht Profitabilität.
- **Minimale Bedingung für PILOT:** abgeschlossener Aufzeichnungs-Vorlauf (≥ 3 Monate für Backtest) UND ein Gate, das DD-Reduktion *netto nach entgangenem Carry* misst, nicht nur Recall.

---

### S-6 auf A-6 — Strategien: CS-06 ist die sauberste, aber der ω_s-Single-Point-of-Failure macht die „Ensemble-Diversität" zur Illusion

**Steelman:** CS-06 ist tatsächlich die **einzige** Cascade-Strategie, die kein einziges REFUTED/SUSPECT-PRD-v1-Modul mitschleppt (anders als CS-11, das C-14-Schwelle und C-15-SUSPECT erbt). Sie steht komplett auf threshold-/volumen-robusten Bausteinen, und die Quelle benennt ihren schwächsten Punkt selbst. Das ist intellektuell ehrlich und der saubereste Pilot-Kandidat des Clusters — anerkannt.

**Aber der Advocate liefert mir hier mein eigenes schärfstes Argument frei Haus:**

1. **ω_s-Single-Point-of-Failure (vom Advocate selbst benannt).** CS-06 *und* CS-10 hängen über C-27/C-28 an **demselben** ω_s-Kernel. Ein instabiler Kernel kippt C-27, C-28, CS-06 und CS-10 **gleichzeitig** (korrelierter Fehler). Damit ist die scheinbare Vielfalt „Cori + NB-k + Cross-Coin" real **ein** Risiko-Faktor. Die getrennten IDs (C-27/C-28/CS-06/CS-10) suggerieren Diversifikation, die es nicht gibt — das ist genau die Multiple-Testing-/Schein-Robustheits-Falle aus GM-2. Im Verdict muss CS-06 als **am Kernel-Risiko hängend** markiert sein, nicht als breit abgestütztes Ensemble.
2. **CS-11 konvergiert nach Modul-Ersetzung auf CS-06** — dann ist CS-11 redundant, kein zweiter Pilot. C-29 ist die einzige echte Diversifikation (kernel-unabhängig, S-3), und die hat ihr eigenes Eventdichte-Problem.
3. **Alle drei sind UNTESTED, nicht implementiert** (alignment_matrix CS-06/10/11 = 0 Evidenz). Der gesamte Strategie-Teil ist Architektur auf dem Papier.

- **Futures:** CS-06 PILOT — aber explizit als kernel-risiko-gekoppelt deklariert. CS-10 PARK (E-14 Panel-Lücke + CCM laut Critic „gestreckt"). CS-11 nur falls C-29-Omori-Exit eigenständigen Wert über CS-06 zeigt, sonst redundant.
- **Härtester Einwand:** Der ω_s-Kernel ist ein vom Advocate selbst benannter Single-Point-of-Failure, der C-27/C-28/CS-06/CS-10 gemeinsam kippt — die Cluster-„Diversität" ist überwiegend ein ID-Artefakt, kein echter Risiko-Spread (GM-2).
- **Minimale Bedingung für PILOT (CS-06):** ω_s-Stabilitäts-Test über ≥ 2 disjunkte Regime VOR dem Strategie-Run, als Pflicht-Vorschaltung neben A-7. Bricht ω_s über Regime, fällt der halbe Cluster — das muss zuerst geklärt sein.

---

### S-7 auf A-7 — Distributions-Check: notwendig, aber der Advocate überschätzt, was er ausschließt

**Steelman:** Vollständig zugestimmt: Der E-01-analoge Distributions-/Erreichbarkeits-Check ist das **billigste, härteste Pflicht-Gate** und schließt den teuersten C-14-Fehler aus, bevor ein Euro fließt (alignment_matrix Kritische Datenlücke #4). Pflicht-Vorschaltung für C-27/C-30/CS-06/CS-11. Das ist die beste konkrete Idee der gesamten Advocate-Seite.

**Aber zwei Begrenzungen, die der Advocate halb einräumt:**

1. **Er prüft Erreichbarkeit, nicht Spezifikation.** Für C-27 zeigt der Check „erreicht Rₜ je ≥ 1?" — aber wegen S-1 (Punktschätzer-Varianz) kann Rₜ ≥ 1 auch reines Schätzrauschen bei dünnen Events sein. Der Check muss auf dem **unteren Kredibilitäts-Intervall** laufen, sonst produziert er falsch-positive „erreichbar"-Urteile. Erreichbarkeit des *Punktschätzers* ist nicht Erreichbarkeit des *Signals*.
2. **C-30 (Natural Time κ₁) ist ein C-14-Wiedergänger und gehört nicht in denselben Atemzug wie C-27 gelobt.** κ₁ ≈ 0.070 ist ein **importierter theoretischer Schwellwert** (claims_register C-30; alignment_matrix C-30: „dasselbe Risiko eines unkalibrierten theoretischen Schwellwerts wie C-14"). Das ist genau der E-01-Fehlertyp, den C-27 zu vermeiden vorgibt. Der Advocate führt C-30 korrekt nur nachrangig mit κ₁-Gate — aber im Multiple-Testing-Bild (GM-2) ist C-30 der **dritte, vierte Schuss auf dasselbe Kaskaden-Ziel** mit der schwächsten Konstruktion. Ich würde C-30 härter behandeln: PARK bis C-27 validiert, nicht parallel pilotieren.

- **Futures:** Distributions-Check ADOPT als Pflicht-Gate (kein eigener Alpha-Ansatz, ein Filter). C-30 PARK statt PILOT.
- **Minimale Bedingung:** Check läuft auf Intervall-Untergrenze, nicht Punktschätzer; C-30 erst nach C-27-Validierung.

---

### S-8 auf A-8 — „muss die Friktions-Wand nicht schlagen": der Zirkularitäts-Vorwurf trifft ins Zentrum

**Steelman:** Der Mechanismus-Punkt ist legitim und wichtig: Ein Risk-Off-/Timing-Gate verdient seinen Wert über die **Verschiebung der Verlustverteilung** (DD-Reduktion, großer Reversal-Move), nicht über eine Per-Trade-Mikro-Edge gegen die 11-bps-Fee (E-16: Friktion ~35× Richtung; E-09: Roh-Edge -5.8 bps < 11 bps). Eine vermiedene -50-bps-Kaskade (E-09 min bps: BNB -56.6, SOL -48.9, BTC -47.7) bezahlt viele Round-Trips. Das ist die *einzige* Signalklasse im Register mit diesem strukturellen Profil, und der Advocate hat recht, das herauszustellen.

**Aber hier ist der Knockout, und der Advocate hat ihn selbst hingeschrieben:** „Das ist ein **Mechanismus-Argument ohne einen einzigen positiven Outcome-Befund.**" Genau. Ich treibe es weiter:

1. **DD-Reduktion ist nur wertvoll relativ zu einer Basis-Strategie, deren DD reduziert wird — und die existiert im Register nicht.** Ein Risk-Off-Overlay senkt den Drawdown *einer profitablen Long-Position*. Im gesamten Register gibt es **null** Strategie mit positiver Edge: CS-01 REFUTED, CS-02 REFUTED, CS-03 PARTIAL/negativ (E-09), CS-04/05 nie gelaufen (E-13/E-14). Der einzige positive Befund im ganzen Register ist C-42 (RV-Prognose R²=0.249) — und das ist ein **Volatilitäts**-Schätzer, **keine direktionale Basis-Strategie**, auf die ein Cascade-Risk-Off aufsetzen könnte. **Ein Drawdown-Reduzierer ohne profitable Basis reduziert den Drawdown von Null auf etwas-unter-Null — er macht aus einer Nicht-Strategie eine teurere Nicht-Strategie.** Das ist die Zirkularität in Reinform: A-8 begründet den Cluster-Wert mit einer DD-Reduktion an einer Position, die das Register nicht besitzt.
2. **Der Erschöpfungs-Entry (C-15/C-29) ist die einzige *eigenständige* Geldverdien-These — und ihre Evidenz ist E-11, das schwächste Stück im Register.** Der Reversal-Amplituden-Beleg (E-11: BNB -195 → +187 bps Mirror-Flip) ist laut Register selbst **NIEDRIG belastbar, N=16, ein einziger Trade, in iter-4 NICHT reproduziert** (worst BNB dann nur -56.6 bps). Auf diesem Ein-Trade-Artefakt darf kein Geldverdien-Anspruch ruhen. Der Advocate zitiert es korrekt mit Vorbehalt — aber damit bleibt die einzige offensive Cascade-These empirisch praktisch unbelegt.
3. **DD-Reduktions-Ziele (C-39 ≥ 25 %, CS-11 ≥ 20 %) sind reine PRD-Behauptung** (alignment_matrix: beide UNTESTED, 0 Evidenz). GM-6 bleibt: ohne stress-reiches Fenster ist selbst ein gutes Cascade-Signal nicht falsifizierbar — der Cluster kann seine zentrale Wertbehauptung im vorhandenen Datenmaterial **nicht testen**.

- **Futures:** Das Mechanismus-Argument rettet den Cluster vor der Friktions-Wand — aber **nur konditional** darauf, dass irgendwann eine profitable Basis-Strategie existiert ODER der Erschöpfungs-Entry standalone positiv misst. Beides fehlt heute.
- **Härtester Einwand:** DD-Reduktion ist wertlos ohne eine positive Basis-Strategie, deren DD reduziert wird — die im gesamten Register nicht existiert (alle CS REFUTED/negativ/ungelaufen; C-42 ist kein Direktional-Alpha) — also begründet A-8 den Cluster-Wert zirkulär mit einem Bezugspunkt, den es nicht gibt.
- **Minimale Bedingung dafür, dass A-8 mehr als Rhetorik ist:** Entweder (a) eine im Register *belegte* profitable Basis-Position, deren Max-DD das Cascade-Overlay nachweislich senkt (netto nach entgangenem Carry/False-Positive-Kosten), oder (b) ein standalone-positiver Erschöpfungs-Entry auf belastbarer Stichprobe (nicht E-11/N=16). Ohne (a) oder (b) ist die Friktions-Immunität ein nicht einlösbarer Scheck.

---

### Skeptic — Synthese je Markt (für den Judge)

Spot: DROP für alle (kein Mechanismus, unstrittig). Optionen: DROP/PARK für alle (datenlos, INC-04). Futures unten.

| Ansatz | Futures — Skeptic-Position vs. Advocate |
|---|---|
| C-27 Cori-Rₜ | PILOT **nur** mit Posterior-Varianz-Gate auf Intervall-Untergrenze; sonst DROP (S-1). Self-calibrating ≠ parameterfrei. |
| C-28 NB-k | PILOT nur gebündelt + Power-Analyse; im Verdict als **ein** Test mit C-27 führen, nicht zwei (S-2, GM-2). |
| C-29 Avalanche | PILOT nur nach Eventdichte-Nachweis + Baseline gegen reparierten Time-Stop (E-15); stärkster eigenständiger Kandidat, aber Collapse braucht viele Bursts (S-3). |
| C-30 κ₁ | **PARK** (nicht PILOT) — importierter Theorie-Schwellwert, C-14-Wiedergänger, dritter korrelierter Schuss (S-7, GM-2). |
| C-39 Anatomie | **PARK** (nicht PILOT) — monatelang datenleer, Recall-Gate misst Detektion statt Profit (S-5). |
| C-14 Konzeptrest | DROP als eigener Posten, in C-27 absorbiert (S-4, Zustimmung). |
| CS-06 Cockpit | PILOT — sauberste Strategie, aber explizit als **ω_s-kernel-risiko-gekoppelt** deklarieren (S-6). |
| CS-11 Seismograph | PARK/redundant — konvergiert auf CS-06; erbt C-14/C-15-Lasten (S-6). |
| CS-10 Cross-Coin | PARK — E-14-Panel-Lücke + geteilter Kernel + CCM „gestreckt" (S-6). |

**Pflicht-Vorschaltung (Zustimmung zu A-7, verschärft):** (1) E-01-analoger Distributions-Check **auf Intervall-Untergrenze**; (2) ω_s-Stabilitäts-Test über ≥ 2 Regime; (3) Bulk-Historie mit ≥ 30 Kaskaden (GM-6); (4) jedes Outcome-Gate netto nach Carry/False-Positive-Kosten, nicht Recall. Solange keine profitable Basis-Strategie im Register existiert, bleibt die A-8-Friktions-Immunität ein konditionaler Scheck.

---

*Ende Skeptic.*
