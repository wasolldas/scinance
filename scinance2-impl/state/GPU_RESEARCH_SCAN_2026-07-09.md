# GPU-Research-Scan (Fable-5), 2026-07-09

## Was das hier ist

Dies ist der Output eines Fable-5-Recherche-Scouting-Netzwerks: 1 Inventory-Scout
(Bestandsaufnahme von bereits Getestetem, vorhandenem GPU-Code, Programmzustand,
Datenverfügbarkeit) + 6 parallele Disziplin-Lanes, die jeweils GPU-notwendige
"Hidden Pattern"-Kandidaten für die Bybit-Handelsdaten vorschlagen, + 1 gepoolter
Kritiker, der alle Kandidaten auf einer 0–12-Skala über vier Dimensionen
(Novelty / Data-Fit / GPU-Utility / Falsifiability) bewertet — mit einer harten
Obergrenze von 5 SHORTLIST-Verdikten pro Runde.

**Das hier ist ausschließlich eine RESEARCH SURVEY.** Es wurde kein Code
geschrieben, nichts wurde in die `hypothesis_registry.md` vorregistriert. Die
Kandidaten unten sind Text in **Pre-Registration-Qualität**, gedacht als
Entscheidungsgrundlage für den Nutzer, bevor über eine Build-Welle entschieden
wird — analog zum Ablauf der vorherigen edge-research-v3-Runde: erst Survey,
dann Grünlicht durch den Nutzer, erst danach Build.

Insgesamt wurden **19 Kandidaten** gescoutet, alle 19 wurden bewertet, **5**
davon erhielten das Verdikt SHORTLIST (Cap erreicht), die restlichen 14 wurden
PARK oder REJECT.

---

## Ausgangslage

*(Inventory-Brief des Scout-Agenten, leicht redigiert für Lesbarkeit — Inhalt unverändert)*

### 1. Bereits getestet — NICHT erneut vorschlagen (Methode → Ergebnis)

**REFUTED (nie wiederholen):** C-14 Hawkes-ρ-threshold (ρ≈2e-7, 6 Größenordnungen unter 0,85) · CS-01 Cascade-Detector (Gate öffnet nie) · CS-02 Entropy-Momentum (rohe Edge negativ, nicht invertierbar).

- **H-01** S3 Pre-Settlement-Entry — DROP, rohe Edge −4,48bps über alle Symbole.
- **H-02** LightGBM/HAR-RV Vol-Forecast — DROP, 0/5 Symbole, 0/36 Features FDR-signifikant; **sperrt den gesamten Vol-Stack** (C-10/C-11 TDA/C-12 RQA/C-34/C-35 CEEMDAN).
- **H-03** Cyclostationary CFAR — DROP, p≈1,0, ~250× unter der Friction Wall.
- **H-04/H-04b** BTC→ETH Lead-Lag (TE/Wavelet-Coherence) — Messung WEITER, aber Tradability PARK (Capture +0,19bps, ~80× unter Wall).
- **H-05/H-05b/H-05c** OFI-Sign (positiv DROP; invers/MM-Replenishment Messung WEITER; Fade-Tradability PARK ~150–500× unter Wall) — OFI-Komplex für erschöpft erklärt, kein H-05d.
- **H-06** Permutation Entropy — DROP (ρ ~20× unter 0,30).
- **H-07/H-08** Cross-Sectional-z Mean-Reversion (absolut + Rank) — DROP strukturell (max|z|=√(N−1)=2,0<2,5 bei N=5) + empirisch; C-06 triple-closed.
- **Gesperrte Cluster:** Seismologie (Hawkes/GR-Omori/Avalanche/Natural-Time — data-gated Aug–Okt 2026), Informationstheorie (PE/TE), TDA/RQA + CEEMDAN (Vol-Anchor), CFAR/Radar, SIR-Epidemiologie.
- **Welle 4 registriert, noch keine Verdikte (GL bleibt bei 013):** H-09 Tier-Bunching, H-10 Pointer-Days, H-12 RMT/MP-IPR-Fragmentierung (alle "sofort testbar", alle CPU-getaggt); H-11 AnEn-Vol (braucht ≥730 Tage Backfill) und H-13 GPD-Tail-Shape (braucht 2 IV-Snapshot-Tage) GESPERRT.

### 2. Programmzustand

`PROGRAM_FINAL_REPORT.md` (2026-07-06): 3 Wellen, 13 vorregistrierte Verdikte — **9 DROP, 2 PARK, 2 kapitalfreie Messungen-WEITER, 0 tradbare Edges, 0 Goalpost-Moves**. Friction Wall von 11bps Taker / ~15bps All-in hat alles geschlagen. Pipeline "data-gated, not work-gated". Constitution-Constraints: Pre-Registration, BH-FDR α=0,10 pro Familie, hartes One-Window-DROP, Trennung Messung vs. Tradability-Gate, capital_free-first.

### 3. GPU-fähiger Code

`m18_patchtst.py` / `m19_timesnet.py`: **vollständige, echte PyTorch-Implementierungen** (PatchTST ICLR'23 mit RevIN+Transformer-Encoder; TimesNet mit FFT-Top-k-Perioden + Inception2D), `device="auto"`→cuda, fit/save/load, Numpy-Fallback, unit-getestet — aber **nur** eingebunden in `strategies/strategy4_pattern_ensemble.py` (DEPRECATE, S4 DROP gemäß CLEANUP_PLAN) und offline `scripts/train_models.py`. **Keine Research/Gate-Pipeline nutzt sie = ungenutztes Scaffolding.** Ebenfalls GPU-relevant: `m1_spikewavformer` (snntorch SNN), `m20_moment` (Foundation-Model, geparkt für C-20 New-Listings). pyproject `[gpu]`-Extra: torch≥2.3, torchvision≥0.18, torchaudio≥2.3, snntorch≥0.9; `[foundation]`: momentfm, transformers≥4.46, peft. **torch NICHT installiert in dieser Sandbox** (Zielmaschine: RTX 5060 Ti Blackwell, CUDA 12.8+/PyTorch 2.7+, 82GB RAM, gemäß edge-research-v3 CLAUDE.md §2.7).

### 4. Datenverfügbarkeit (`audit_inventory.md`, doc-derived, NICHT live-verifiziert)

Sofort nutzbar: Base-Stock 2026-03-27→heute, 5 Perps (BTC/ETH/SOL/BNB/XRP): Bybit/Binance publicTrade, Funding, OI (~30 Tage rolling only), Deribit dvol/book_summary. Live-only seit ~2026-06-16 (~3 Wochen): L2-Orderbook, volle Deribit-IV-Surface, Liquidation-/Insurance-Streams. Deep-Backfill in Arbeit (Ziel 2014 BitMEX / 2019 Deribit/Binance) — nutzbar erst nach Manifest-Coverage-Check. Tardis-Options-Chain: 1 Tag/Monat Samples seit 2019. Strukturelle Lücken: kein L2 vor 2023, keine IV-Surface vor Collector-Start außer Tardis-Samples, Bybit-L2-Backfill 404-tot.

**Schlüsseldateien:** `/home/user/scinance/scinance2-impl/state/{hypothesis_registry.md,PROGRAM_FINAL_REPORT.md,gate_log.md,CLEANUP_PLAN.md}`, `/home/user/scinance/edge-research-v3/{CLAUDE.md,results/audit_inventory.md}`, `/home/user/scinance/src/bybit_edge/layers/l4_pattern/{m18_patchtst.py,m19_timesnet.py,m20_moment.py}`, `/home/user/scinance/pyproject.toml`.

---

## Shortlist

Die eigentliche Lieferung dieser Runde: 5 Kandidaten mit Verdikt SHORTLIST,
absteigend nach Gesamtscore sortiert.

### 1. PANEL-LAG: Conditional cross-venue lead-lag graph via node-ablated cross-attention forecaster (12-node panel)

| Novelty | Data-Fit | GPU-Utility | Falsifiability | **Total** |
|---|---|---|---|---|
| 3 | 3 | 3 | 3 | **12 / 12** |

**Lane:** cross-asset-panel-dl

**Methode:** Aufbau des größten sofort verfügbaren Trade-Panels: 12 Nodes = BTC/ETH × {Bybit, Binance, Deribit-PERPETUAL} + SOL/BNB/XRP × {Bybit, Binance}, publicTrade auf das Standard-1s-Grid resampled. Pro Node ein PatchTST-Style-Encoder (Wiederverwendung von `m18_patchtst`, aktuell ungenutztes Scaffolding), gespeist in einen Cross-Node-Multi-Head-Attention-Layer; Target = Vorzeichen der nächsten 10s-Rendite jedes Nodes. Edge-Statistik T(j→i) = Out-of-Sample-Δ-Log-Loss auf Target i zwischen Vollmodell und einem Modell, das mit zirkulär geshiftetem Surrogat für Source-Node j RETRAINIERT wurde (Retrain-Ablation, nicht Attention-Weight-Reading). Null aus ~100 Retrainings mit komplett surrogaten Cross-Node-Inputs. Zwei disjunkte chronologische Fenster, BH-FDR α=0,10 über ~110 gerichtete Kanten mit Non-BTC-Source.

**Warum GPU zwingend notwendig:** Das Design braucht in der Größenordnung (1 volles + 12 Single-Source-Ablationen + ~100 Null-Retrainings) × 2 Fenster ≈ 226 volle Transformer-Trainings, jedes ein Multi-Head-Attention-Modell über 12 Nodes × Millionen 1s-Schritte. Auf der RTX 5060 Ti ~10–20 min pro Training (~2–3 GPU-Tage total). Auf CPU läuft derselbe Encoder-Stack ~50–100× langsamer → mehrere Monate für einen einzigen vorregistrierten Lauf, d.h. die methodisch ehrliche Retrain-basierte Null ist auf CPU schlicht nicht durchführbar; eine billigere CPU-Null (Frozen-Model-Shuffling) wäre eine schwächere, angreifbare Statistik.

**Falsifizierbarer Claim:** In BEIDEN disjunkten Fenstern (W1=2026-03-27..2026-05-15, W2=2026-05-16..Cutoff) muss mindestens eine gerichtete Kante (j→i) mit Non-BTC-Source j eine Retrain-Ablation-Δ-Log-Loss über dem 95. Perzentil der 100-Surrogat-Null aufweisen UND BH-FDR α=0,10 über alle ~110 Non-BTC-Source-Kanten überleben. Hartes One-Window-DROP: null überlebende Non-BTC-Source-Kanten in einem der beiden Fenster = DROP. Die BTC→ETH-Kante ist explizit von der Pass-Kriterium ausgeschlossen (bereits durch H-04 etabliert) und dient nur als Positivkontrolle — scheitert das Modell daran, diese zu recovern, gilt der Lauf als methodisch invalide statt informativ.

**Begründung des Kritikers (SHORTLIST):** Bester Kandidat der Runde. Stellt eine Frage, die paarweise Methoden strukturell nicht beantworten können (residuale gerichtete Kanten nach Konditionierung auf das volle 12-Node-Panel, mit entferntem gemeinsamen BTC-Treiber), was echt neu ist gegenüber H-04 (paarweise TE/WCOH) und H-12 (ungerichtete gleichzeitige Eigenstruktur). Retrain-Ablation-Statistik statt Attention-Weight-Reading ist methodisch ehrlich, und die ~226-Trainings-Retrain-Null ist genau die Arbeitslast, die dies GPU-gated macht (Monate auf CPU). Daten sind reines Base-Stock-publicTrade, sofort testbar. Pass-Kriterium ist scharf: ≥1 überlebende Non-BTC-Source-Kante in BEIDEN Fenstern, BH-FDR über ~110 Kanten, BTC→ETH vom Pass ausgeschlossen und nur als Positivkontrolle mit deklariertem Invaliditätspfad genutzt. Vollständig vorregistrierbar.

---

### 2. DSM-01: Trade-tape event grammar beyond Markov (causal transformer vs. variable-order Markov null)

| Novelty | Data-Fit | GPU-Utility | Falsifiability | **Total** |
|---|---|---|---|---|
| 2 | 3 | 3 | 3 | **11 / 12** |

**Lane:** deep-sequence-models

**Methode:** Tokenisierung des Bybit-publicTrade-Streams jedes Symbols in diskrete Events: Side (2) × Signed-Size-Quantil-Bucket (8, Quantile nur auf Train-Fold gefittet) × Log-Inter-Arrival-Bucket (8) → Vocab 128 (optional × Tick-Direction → 256). Training eines kleinen Decoder-only-Causal-Transformers (~2–4M Params, Kontext 1024 Token, Next-Token-Cross-Entropy) pro Symbol auf dem Base-Stock 2026-03-27→heute. Baseline: interpoliertes/KT-geglättetes Variable-Order-Markov-Modell, k≤4, auf demselben Train-Fold gefittet. Purged Walk-Forward (4 Folds über ~100 Tage, 1-Tag-Embargo), 3 Seeds. Null: ≥200 saisonalitätserhaltende Surrogate via Within-Hour-of-Day-Block-Shuffle (Blocklänge 256 Events).

**Warum GPU zwingend notwendig:** Allein BTC hat zig Millionen Trade-Events über den Base-Stock; Training = 5 Symbole × 4 Folds × 3 Seeds × mehrere Epochen über 1024-Token-Kontexte, plus ≥200 Surrogat-Evaluierungsläufe = Milliarden Token-Forward-Passes durch Attention. Stunden auf der Ziel-RTX-5060-Ti; mehrere Wochen auf CPU, was zwingen würde, die von der Constitution geforderte Seed/Fold/Surrogat-Disziplin zu kürzen. Die Markov-Baseline ist CPU-billig, weshalb der Test nur mit GPU für den neuronalen Arm überhaupt durchführbar ist.

**Falsifizierbarer Claim:** OOS-Token-Level-Cross-Entropy des Transformers ist ≥2% relativ niedriger als die beste Markov-k-(k≤4)-Baseline bei ≥4/5 Symbolen, UND die CE-Lücke übersteigt das 95. Perzentil der Lücken-Verteilung auf den saisonalitätserhaltenden Surrogaten (BH-FDR α=0,10, einzelnes vorregistriertes Fenster, hartes One-Window-DROP). Reine Existence-of-Structure-Messung (enthält Order Flow Grammatik jenseits niedrigordrigem Markov + Saisonalität?); keine Rendite-, Vol- oder PnL-Vorhersage wird gemacht oder impliziert.

**Begründung des Kritikers (SHORTLIST):** Sauberer Existence-of-Structure-Test mit korrekt registrierter Null (Markov-k + saisonalitätserhaltende Block-Shuffle-Surrogate), überzeugend differenziert von den gesperrten H-06/H-04-Informationstheorie-Items (Event-Stream statt Renditen, CE als Scoring-Rule statt Entropie-Schätzer, kein ρ/Trading-Gate). Novelty auf 2 gedeckelt: "Transformer schlägt Markov auf Order Flow" ist in der Literatur ein Ergebnis mit geringer Überraschung, wenn auch in dieser Registry ungetestet. GPU-Necessity ist real (Milliarden Token-Passes × Folds × Seeds × 200 Surrogate). Schwellenwerte (≥2% relative CE, ≥4/5 Symbole, Surrogat-95.-Perzentil, BH-FDR) sind vollständig vorregistrierbar mit hartem One-Window-DROP. Auch der Anker für die DSM-02/DSM-04-Folgekandidaten.

---

### 3. V-02 Time-Arrow CNN: classifier two-sample test for time-irreversibility localization in trade-flow scalograms

| Novelty | Data-Fit | GPU-Utility | Falsifiability | **Total** |
|---|---|---|---|---|
| 2 | 3 | 3 | 3 | **11 / 12** |

**Lane:** image-spectrogram-methods

**Methode:** Repräsentation: 1s-signed-Trade-Imbalance-Serie (Buy − Sell Taker-Volumen, pro Sekunde) aus Bybit publicTrade, Fenster von 512s mit 64s-Stride; jedes Fenster → komplexes Morlet-CWT-Log-Power-Scalogram, 64 Skalen (2s–256s) × 512 Zeit-Bins, Single-Channel-Bild. Task: Training eines CNN (ResNet-18 oder kompaktes ConvNeXt) zur Klassifikation FORWARD vs. TIME-REVERSED Fenster (Reversal auf die Rohserie vor der CWT angewendet). Dies ist ein Classifier-Two-Sample-Test (C2ST, Lopez-Paz & Oquab 2017): für jeden zeitreversiblen Prozess ist die Bayes-optimale AUC exakt 0,5, was eine saubere, vorab spezifizierbare Null liefert. Pflicht-Kontrollen: (a) Pipeline-Leak-Kontrolle — dieselbe Pipeline auf IAAFT-phasenrandomisierten Surrogaten muss Held-out-AUC ≤0,52 liefern; (b) Volatility-Asymmetry-Ablation — Wiederholung auf |Imbalance| (unsigned) zur Trennung von Leverage-Effekt-Asymmetrie und Flow-Richtungs-Asymmetrie.

**Warum GPU zwingend notwendig:** Zwei multiplikative GPU-Anforderungen: (1) Batch-CWT von ~8,9M Sekunden × 5 Symbole ist eine große Batched-FFT-Arbeitslast (torch.fft, trivial auf GPU, Stunden auf CPU); (2) die Surrogat-Null ERFORDERT volles CNN-Retraining pro Draw — 20 Surrogat-Trainings + 5 Seeds × 5 Symbole auf ~135k Scalogrammen von je 64×512 ≈ 145 Trainings. Auf GPU ~10–20 min je Training; auf CPU ist dieses genestete Retraining-Design schlicht nicht durchführbar (~Monate), weshalb C2ST-Irreversibilitätstests bei dieser Auflösung ohne GPU nicht machbar sind.

**Falsifizierbarer Claim:** Held-out-Day-Forward-vs-Reversed-AUC ≥0,60 mit Surrogat-Null-95.-Perzentil unter 0,53, bei ≥4/5 Symbolen nach BH-FDR α=0,10 (Familie F-ARROW), UND die phasenrandomisierte Leak-Kontrolle bleibt ≤0,52. Bei AUC<0,60 (oder Scheitern der Leak-Kontrolle) gilt der Claim "Bybit-Perp-Trade-Flow ist bei 2s–256s-Skalen für ein diskriminatives Vision-Modell erkennbar zeitirreversibel" bei dieser Auflösung als REFUTED und die Repräsentation wird verworfen. Kapitalfrei; keine Trading-Konsequenz impliziert.

**Begründung des Kritikers (SHORTLIST):** Am besten designter Test seiner Lane: C2ST liefert eine exakte Bayes-AUC=0,5-Null für reversible Prozesse, plus Pipeline-Leak-Kontrolle (IAAFT-Surrogate müssen ≤0,52 liefern) und eine Unsigned-|Imbalance|-Ablation zur Trennung von Leverage-Effekt-Asymmetrie und Flow-Richtungs-Asymmetrie — ein seltenes, vollständig kontrolliertes Design. Data-Fit ist der stärkste der Lane (voller publicTrade-Base-Stock, ~135k Fenster/Symbol). Die 145-Retraining-Surrogat-Null ist genuin GPU-gated. Novelty auf 2 gedeckelt wegen konzeptioneller Nähe zum gesperrten Informationstheorie-/Nichtlineare-Dynamik-Cluster — es ist KEIN Duplikat (kein Entropie-Schätzer, andere Eigenschaft, exakte Null), aber die Registrierung muss den Differenzierungsabsatz wörtlich enthalten.

---

### 4. VENUE-FINGERPRINT: symbol-invariant venue identity in shape-normalized order flow via large-batch contrastive embedding

| Novelty | Data-Fit | GPU-Utility | Falsifiability | **Total** |
|---|---|---|---|---|
| 2 | 3 | 3 | 3 | **11 / 12** |

**Lane:** cross-asset-panel-dl

**Methode:** Für jeden der 10 Nodes (5 Symbole × {Bybit, Binance}) wird publicTrade in 5-min-Event-Fenster geschnitten: Sequenzen von (Inter-Trade-Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction), jeder Kanal pro Node pro Tag quantil-normalisiert — dies zerstört bewusst triviale Venue-Tells (Tick-Size, Fee-getriebenes Size-Clustering, Aktivitätslevel) und lässt nur die zeitliche Abhängigkeits-SHAPE des Flows übrig. Training eines Temporal-CNN/Transformer-Encoders mit InfoNCE (Positive = Fenster desselben Nodes zu anderen Zeiten, Negative = voller Batch) und Evaluierung eines Frozen-Linear-Probes für Venue-Identität unter Leave-One-Symbol-Out. Sekundärer Output: tägliche Cross-Venue-Embedding-Distance-Serie ("nichtlinearer Fragmentierungsindex") pro Symbol.

**Warum GPU zwingend notwendig:** InfoNCE-Qualität hängt direkt von der Negative-Sample-Anzahl ab: Batches von ≥2048 Fenstern × ~512 Events × 4 Kanäle ≈ 4M Token pro Optimizer-Step durch einen Temporal-Encoder, für ~10^5 Steps. Dieses Batch-Size-Regime IST die Methode — Small-Batch-CPU-Contrastive-Training verschlechtert die Embedding messbar und würde ein Null-Ergebnis konfundieren. Zusätzlich brauchen Design und Null ~(5 Leave-One-Symbol-Out-Folds) × (1 echtes + 20 Label-Permutation-Retrainings) = ~105 volle Trainings. GPU: ~1–2 Tage; CPU: ~50–100× langsamer und kann den erforderlichen Batch-Durchsatz nicht halten — dramatisch schlechter, nicht nur langsamer.

**Falsifizierbarer Claim:** Held-out-Balanced-Accuracy der Venue-Klassifikation (Bybit vs. Binance) auf dem ausgelassenen Symbol der letzten 3 Wochen ist ≥0,60 in ≥4 von 5 Leave-One-Symbol-Out-Folds, gegenüber einer Within-Symbol-Within-Day-Label-Permutation-Null (20 Retrainings, erwartetes 99. Perzentil ~0,52), BH-FDR α=0,10 über die 5 Folds; hartes One-Window-DROP falls Pooled-Accuracy <0,55. Vorregistriertes Non-Redundanz-Gate: die tägliche Embedding-Distance-Fragmentierungsserie muss |Spearman ρ|<0,6 gegen die c12_frag-Tages-λ2/IPR-Serie an überlappenden Tagen aufweisen — |ρ|≥0,6 = als redundant zu H-12 deklariert = DROP unabhängig von der Accuracy.

**Begründung des Kritikers (SHORTLIST):** Stärkste der drei in dieser Runde vorgeschlagenen Venue-Signature-Varianten (vs. XV-DUAL-RETRIEVAL und V-03): Leave-One-Symbol-Out macht den Symbol-INVARIANZ-Claim real statt dekorativ, Per-Day-Quantil-Normalisierung tötet die trivialen Tells, die Null nutzt 20 Label-Permutation-RETRAININGS (kein Frozen-Model-Shuffling), und das vorregistrierte |ρ|<0,6-Redundanz-DROP-Gate gegen H-12/c12_frag ist vorbildliche Programmdisziplin. Trades-only-Base-Stock = sicherste Datenklasse. Large-Batch-InfoNCE (≥2048) plus ~105 Trainings ist legitim GPU-gebunden. Novelty 2, weil Venue-Distinguishability ein wahrscheinlich wahrer Effekt ist und zwei Schwesterkandidaten dasselbe Konstrukt anzielen; dieser gewinnt den Slot durch Design.

---

### 5. GL-006 / H-04 Lead-Lag High-N Surrogate Power-Audit (TE + WCOH, n_surrogates 200 → 100.000)

| Novelty | Data-Fit | GPU-Utility | Falsifiability | **Total** |
|---|---|---|---|---|
| 1 | 3 | 3 | 3 | **10 / 12** |

**Lane:** large-n-resampling

**Methode:** Re-Execution der byte-identischen, bereits vorregistrierten F-LEADLAG-Pipeline aus GL-006 (BTC/ETH-Perp-Paar, 1000ms-Grid, dieselben zwei disjunkten Fenster F0/F1, Shannon-Transfer-Entropy + Wavelet-Coherence-Phase-Lead-Achsen, Lags {1,2,3,5,10}, Per-Fenster BH-FDR α=0,10 über die 22-Varianten-Familie), mit genau einer vorab deklarierten Änderung: n_surrogates 200 → 100.000 (500×). Surrogate werden als GPU-Tensor-Batches erzeugt: Phase-Shuffle via `torch.fft.rfft/irfft` mit randomisierten Phasen, Permutation-Surrogate via Argsort von Uniform-Random-Keys, TE via Batched-3D-Histogramme (scatter_add), WCOH via Batched-CWT (FFT-Convolution über ~50 Skalen). Neue p-Wert-Untergrenze wird 1e-5 mit MC-SE ≤2,2e-4 bei p=0,005. Registriert als NEUER kapitalfreier Registry-Eintrag (Welle-5-Konvention); das GL-006-Verdikt selbst bleibt append-only unverändert stehen — dies ist ein Auflösungs-Audit, keine Neu-Adjudikation.

**Warum GPU zwingend notwendig:** Bei N=200 ist die Frage konstruktionsbedingt unentscheidbar: die Permutation-p-Untergrenze ist 1/201=0,005, sodass die stärksten Zellen an der Untergrenze zensiert sind und das BH-Ranking unter ihnen eine willkürliche Bindung ist; die Grenzfall-Zellen tragen einen MC-SE (~0,017–0,018) vergleichbar mit p_crit selbst. Auflösung braucht N~1e5, also 500× den Originallauf. Workload: 1e5 Surrogate × ~22 Varianten × (50-Skalen-CWT + 3D-TE-Histogramme) auf ~3.900-Punkte-Serien ≈ 1e12 Flops plus bandbreitengebundene Shuffles; der originale N=200-CPU-Lauf verbrauchte bereits einen erheblichen Anteil eines Welle-2-Overnight-T3-Budgets, sodass 500× auf CPU mehrwöchig wäre und jede Overnight-Wall durchbricht. Auf GPU passt ein 10k-Surrogat-Chunk in <4GB VRAM, kompletter Lauf in etwa einer Stunde auf der RTX 5060 Ti.

**Falsifizierbarer Claim:** Zwei vorregistrierte, schwellenwert-fixierte Teil-Claims. T1: alle 12 GL-006-Stage-1-FDR-Survivor (inkl. beider WCOH-Zellen, p bei 0,0050 in beiden Fenstern floored, und der TE-BTC→ETH-Lag1-3-Zellen) messen bei p≤1e-3 (≥5× unter der alten Untergrenze) neu und bleiben unter dem neu berechneten BH-Step-up signifikant; jeder abdriftende Survivor falsifiziert T1 und markiert das stehende Messungen-WEITER als auflösungsbedingt (Audit-Finding im Gate-Log geloggt, kein Goalpost-Move). T2: die zwei Lesart-Entscheidungszellen ETH→BTC F0 Lag1 und Lag2 lösen sich auf eine Seite von p_crit mit >5 MC-SE auf.

**Begründung des Kritikers (SHORTLIST):** Niedrige Novelty konstruktionsbedingt (Re-Execution bei höherem N), aber maximale Entscheidungsrelevanz pro GPU-Stunde: der N=200-Lauf hinterließ 12 Survivor zensiert am 1/201-p-Floor und zwei Lesart-Entscheidungszellen innerhalb 1 MC-SE von p_crit — bei archivierter Auflösung genuin unentscheidbar. T1/T2 sind mit fixen Schwellenwerten vorregistriert und beide Zweige sind informativ. Anders als GL-010 braucht der Workload (1e5 Surrogate × 22 Varianten × 50-Skalen-CWT + 3D-TE-Histogramme, ~1e12 Flops) genuin GPU-Batched-FFT/scatter_add. Der TE-Cluster-Lock greift nicht: keine neue informationstheoretische Hypothese, byte-identische registrierte Pipeline — genau das Mandat dieser Lane. Billig (~1 GPU-Stunde), sofort aus archivierten Fenstern lauffähig.

---

## Geparkt / Abgelehnt

Alle 14 nicht-shortlisteten bewerteten Kandidaten, zur Vollständigkeit / als Audit-Trail. Absteigend nach Score sortiert.

| Name | Lane | Total | Verdikt | Begründung (Kurzfassung) |
|---|---|---|---|---|
| XV-DUAL-RETRIEVAL: Cross-venue dual-encoder (InfoNCE) retrieval on price-residualized tape | self-supervised-anomaly | 11 | PARK | Score 11, aber wegen Cap geparkt: Konstrukt-Overlap mit VENUE-FINGERPRINT (beide testen Cross-Venue-Flow-Texture); Kontrollen matchen Hour-of-Day, aber nicht Within-Hour-Aktivität, macht den Claim trivially-true-anfällig (F=2). |
| DSM-02: Memory-horizon ablation in order flow (state-space model context-truncation test) | deep-sequence-models | 11 | PARK | Genuinst GPU-gated der Runde (32k-Kontext-SSM-Training CPU-unmöglich), aber selbst-deklariert konditional auf DSM-01-Erfolg — Registrierung jetzt würde einen Cap-Slot auf eine evtl. hinfällige Hypothese verbrennen (F=2). |
| DSM-03: Wire m18 PatchTST to its designed target — funding-premium residual forecast skill | deep-sequence-models | 10 | PARK | Solide 10, rein durch Cap geparkt. GPU-Utility ehrlich als "stark vorteilhaft statt strikt gated" geflaggt (G=2) — schwächster GPU-Case unter den lauffähigen 10+-Scorern, was den Tiebreak verliert. |
| N-SVI-RESID — Deep-smoothing residual field of the intraday IV surface | options-surface-dl | 10 | PARK | Bester Options-Lane-Kandidat, durch Cap geparkt. Docked bei Data (nur ~3-Wochen-Fenster, einzelnes Vol-Regime) und GPU (25 Trainings über T3-Wall, aber nicht Größenordnungen unerreichbar; G=2). |
| DSM-04: Cross-symbol zero-shot universality of the order-flow grammar (conditional on DSM-01) | deep-sequence-models | 10 | PARK | Wissenschaftlich attraktiv, aber marginaler Compute nur ein paar GPU-Minuten Evaluation (G=1, nicht standalone GPU-notwendig) — sollte als Secondary-Endpoint an DSM-01 angehängt werden statt eigenen Slot zu verbrauchen. |
| V-01 Book-Heatmap Sweep-Precursor (incremental-information C2ST over scalar-OFI baseline) | image-spectrogram-methods | 10 | PARK | Konzept richtig, aber auf statistischer Power geparkt: ~21 L2-Tage geben nur ~4 Test-Tage, Day-Block-Bootstrap-CI aus 4 Blöcken erlaubt keine saubere Adjudikation (F=2, D=2). |
| L2-MAE-GHOST: Masked-autoencoder anomaly score on L2 depth images | self-supervised-anomaly | 10 | PARK | Gut designt, aber selbst-geflaggt data-conditional: braucht ≥45 gesammelte Tage gegen aktuelles ~3-Wochen-L2-Fenster; L2-Backfill strukturell tot, Warten der einzige Weg (D=1). |
| CHAIN-GRAPH: joint BTC+ETH full-options-chain graph transformer | cross-asset-panel-dl | 10 | PARK | Ambitioniert und gut gegated, aber data-gated auf die Tardis-1-Tag/Monat-Samples, deren Coverage doc-derived und NICHT live-verifiziert ist; Pflicht-Manifest-Check (≥60 nutzbare Dual-Underlying-Tage) muss zuerst bestehen (D=1). |
| SSL-EMB-LIQ: Contrastive tape-snippet embedding + MMD two-sample test for pre-liquidation-cluster signature | self-supervised-anomaly | 9 | PARK | Data-Fit-Claim widerspricht dem Inventory-Brief: Liquidation-Streams sind Live-only seit ~2026-06-16, nicht im 2026-03-27-Base-Stock — die Power-Prämisse ist unverifiziert und vermutlich ~5× zu hoch angesetzt (D=1). |
| VQ-FLOW-LEX: VQ-VAE order-flow lexicon + funding-window token-distribution shift | self-supervised-anomaly | 9 | PARK | Konfundierte Null: Funding-Settlements liegen an festen UTC-Stunden, ein zirkulärer Shift des Funding-Grids verschiebt Vergleichsfenster auf andere Uhrzeiten — gewöhnliche Intraday-Saisonalität allein könnte "Signifikanz" erzeugen (F=2). |
| V-03 Venue-Fingerprint CNN: does normalized book geometry carry venue identity? | image-spectrogram-methods | 9 | PARK | Gleiches Konstrukt wie das shortlistete VENUE-FINGERPRINT, aber auf dem schwächsten Datensatz (nur ~3 Wochen gematchtes Dual-Venue-L2). Eine Venue-Signature-Hypothese pro Runde; die Trade-basierte Variante gewinnt auf Data (D=1). |
| SURF-EVENT — PatchTST over surface-state sequences predicts pre-defined 25-delta risk-reversal band-break events | options-surface-dl | 8 | PARK | Sauber gegated, aber selbst-deklariert GESPERRT auf eigenem N-Floor: ≥300 gepoolte OOS-Events noch nicht erreicht im ~3-Wochen-Surface-Fenster, braucht geschätzt 2–6 weitere Wochen (D=1); GPU-gated eher convenient als strikt (G=2). |
| GL-010 / H-05b F-OFI-INV Breadth Power-Audit (n_surrogates 200 → 100.000) | large-n-resampling | 8 | REJECT | Scheitert am GPU-Necessity-Filter der Runde arithmetisch: Workload ist auf der Größenordnung Stunden bis eine einzelne Overnight-Session in vektorisiertem Numpy, nicht das behauptete "multi-day-to-week" (G=1). Empfehlung: als reguläre CPU-T3-Overnight-Aufgabe außerhalb dieser Runde laufen lassen. |
| SET-SHAPE — Set-transformer chain embeddings carry vol-regime information | options-surface-dl | 7 | REJECT | Doppelte Disqualifikation: (1) GPU-Necessity scheitert nach eigenem Eingeständnis des Vorschlags ("strongly benefits" statt "strictly requires", CPU ~1–2 Tage, G=1), und (2) data-gated auf das unverifizierte Tardis-Manifest mit hartem Requirement, das das Live-Fenster nicht substituieren kann (D=1). |

---

## Nächster Schritt

Dieses Dokument ist ausschließlich eine **Survey-Lieferung**. Es wurde nichts
in die `hypothesis_registry.md` vorregistriert, kein Code wurde geschrieben,
und keine Build-Welle wurde gestartet. Die 5 Shortlist-Kandidaten oben sind
Text in Pre-Registration-Qualität — bereit zur Prüfung, aber noch keine
verbindliche Registrierung.

Der natürliche nächste Schritt, **falls der Nutzer grünes Licht gibt**, wäre
eine formale Pre-Registration der ausgewählten Kandidaten (oder einer Teilmenge
davon) in `hypothesis_registry.md`, gefolgt von einer Build-Welle analog zum
Agenten-Netzwerk-Muster aus Welle 4 (H-09..H-13): parallele Implementierungs-
Agenten pro Kandidat, gefolgt von Gate-Adjudikation nach der bestehenden
Constitution (BH-FDR α=0,10, hartes One-Window-DROP, capital_free-first,
Trennung Messung vs. Tradability).

**Keine solche Verpflichtung wurde bisher eingegangen.** Diese Entscheidung
liegt beim Nutzer.
