# Claims Register — Edge Reconciliation Framework
**Phase:** 1 — INVENTORY
**Stand:** 2026-06-11
**Erstellt von:** inventory-analyst
**Quellen:** FINAL_PRD.md (PRD-v1), FINAL_PRD-fable5.md (PRD-fable5), FINAL_PRD-kestrel-basis.md (PRD-kestrel), research_notes.md (Kestrel-v1.4-Erfahrungsbericht)

---

## Vorbemerkung zur ID-Vergabe

Die drei PRDs nutzen kollidierende interne Bezeichner:
- **PRD-v1** (FINAL_PRD.md): M1–M26, Strategien S1–S5
- **PRD-fable5** (FINAL_PRD-fable5.md): M-S11–M-S23, M-Q11–M-Q18, Strategien A–E
- **PRD-kestrel** (FINAL_PRD-kestrel-basis.md): F0, S1–S12, Q1–Q17, Strategien K1–K5

Kanonische IDs in diesem Register: **C-01 bis C-xx** (Module/Methoden), **CS-01 bis CS-xx** (Kombinationsstrategien).
Alias-Tabelle am Ende des Dokuments.

---

## Teil I — Modul-Claims (Einzelne Methoden/Estimatoren)

---

### [C-01] OFI Cont-Kukanov-Stoikov
- **Quelle:** FINAL_PRD.md §4 M2; FINAL_PRD-kestrel-basis.md §4 Q3
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Über kurze Intervalle (1–5 s) sind Preisänderungen linear durch Order-Flow-Imbalance an Best-Bid/Ask getrieben (Slope umgekehrt proportional zur Markttiefe). Retail-Edge liegt in aggregierten Fenstern (1–5 min) unter der HFT-Arbitragegrenze. Cross-OFI (BTC → Altcoin) ist eine dritte Messachse.
- **Kernannahme(n):** Informierter Flow hinterlässt Imbalance-Muster im Orderbuch; OFI-Vorzeichen identifiziert korrekt die aggressive Seite; Beta-Koeffizient ist über 24h stabil genug für Re-Kalibrierung.
- **Behaupteter Nutzen:** R²(1s-Forecast) ≥ 0.05; Sharpe ≥ 1.0 nach Fees (2 bps); Hit-Rate ≥ 53 % (PRD-v1). OOS-R² ≥ 1 % auf 1–5-min Returns; bedingte Richtungs-AUC > 0.55 in G1-Fenstern (PRD-kestrel).
- **Validierungs-Gate:** PRD-v1: R² ≥ 0.05 | Sharpe ≥ 1.0 | Hit-Rate ≥ 53 %. PRD-kestrel: AUC-Gate > 0.55 OOS, sonst nur Feature.
- **Abhängigkeiten:** Orderbook-State-Engine, orderbook.50-Stream (20 ms Deltas)
- **Reifegrad laut Quelle:** Implementiert (m2_ofi.py vorhanden; PRD-kestrel: getestet, aber in S2-Kontext problematisch)

---

### [C-02] SpikeWavformer SNN+DWT Event-Ingestion
- **Quelle:** FINAL_PRD.md §4 M1; FINAL_PRD-kestrel-basis.md §4 S7
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Spiking Neural Network (LIF-Neuron) feuert nur bei echten Anomalien (OI-Sprung, Liquidations-Cluster, Imbalance-Burst); DWT zerlegt Inputs in Sub-Bänder. Radikale Datenreduktion: Analyse-Engine läuft nur bei Signal, nicht kontinuierlich. Kein direkter Trading-Edge — Effizienzvorteil des Gesamtsystems.
- **Kernannahme(n):** SNN-Encoding repräsentiert relevante Anomalien präziser als Schwellwert-Regeln; surrogate-gradient-Training konvergiert stabil; Inferenz-Latenz auf CPU ≤ 50 ms.
- **Behaupteter Nutzen:** PRD-v1: Precision ≥ 0.6 / Recall ≥ 0.4 / F1 ≥ 0.5 auf Vol-Spike-Detection; PRD-kestrel: gleiches oder besseres Event-Recall wie F0 (≥ 95 %) bei ≤ 50 % der F0-Trigger-Rate über 2 Monate Schattenbetrieb.
- **Validierungs-Gate:** PRD-v1: F1 ≥ 0.5. PRD-kestrel: Dominanz über F0 nach 2 Kalibrierungs-Iterationen.
- **Abhängigkeiten:** F0-Fallback-Trigger als Benchmark (PRD-kestrel), Phase-0-Aufzeichnung, orderbook.50/allLiquidation/tickers
- **Reifegrad laut Quelle:** Idee/spezifiziert (m1_spikewavformer.py vorhanden, als Moonshot eingestuft)

---

### [C-03] Iceberg-Detection via Queue-Replenishment
- **Quelle:** FINAL_PRD.md §4 M3
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Eisberg-Orders verraten sich durch kontinuierliche Größen-Wiederherstellung nach jedem Hit am gleichen Preislevel. Rein statistische Inferenz via Auto-Korrelation von Level-Sizes; kein Iceberg-Flag von Bybit. Flagged Levels dienen als Support/Resistance-Marker.
- **Kernannahme(n):** Replenishment-Rate > 0.7 × Pre-Hit-Size innerhalb 500 ms identifiziert echte Eisberge zuverlässig; MM-Orders mit Replenishment-Struktur erzeugen keine Falsch-Positive.
- **Behaupteter Nutzen:** Bounce-Rate ≥ 60 % auf Iceberg-Level innerhalb 5 min nach Touch.
- **Validierungs-Gate:** Bounce-Rate ≥ 60 % auf Iceberg-Level.
- **Abhängigkeiten:** orderbook.200-Stream (separat von orderbook.50), publicTrade-Stream
- **Reifegrad laut Quelle:** Spezifiziert (m3_iceberg.py vorhanden, als optional/Phase 5 eingestuft)

---

### [C-04] Wavelet-Symlet-Denoising (Orderbuch-Imbalance)
- **Quelle:** FINAL_PRD.md §4 M4; FINAL_PRD-kestrel-basis.md §4 S12 (verwandter Ansatz)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** DWT mit Symlets (sym4–sym8) hat fast lineare Phaseneigenschaft → exakte Latenzerhaltung. Soft-Thresholding (Donoho-VisuShrink) der Detail-Koeffizienten trennt MM-Mikrorauschen vom Smart-Money-Tape. Output speist Hawkes/SpikeWavformer-Layer. Variante (S12/PRD-kestrel): DWT auf einzelne Orderbuch-Level-Zeitreihen zur Spoof-/Iceberg-Detektion.
- **Kernannahme(n):** Symlet-DWT mit Fensterbreite 256 Ticks liefert bei ≤ 1 ms Latenz ausreichend entrauschtes Signal; VisuShrink-Lambda ist universell anwendbar ohne symbol-spezifisches Re-Tuning.
- **Behaupteter Nutzen:** R²-Verbesserung gegenüber Roh-Imbalance ≥ 10 %; S12-Variante: Wall-Verschwindet-Signal AUC > 0.55 OOS; S/R-Halte-Quote ≥ 60 %.
- **Validierungs-Gate:** PRD-v1: R²-Lift ≥ 10 %. PRD-kestrel S12: beide Gates (S/R-Quote + AUC) nach 2 Monaten.
- **Abhängigkeiten:** Orderbook-State-Engine + Imbalance-Stream; S12: orderbook.200-Aufzeichnung
- **Reifegrad laut Quelle:** Implementiert (m4_wavelet.py vorhanden)

---

### [C-05] Fraktionale Differenzierung (FFD, López de Prado)
- **Quelle:** FINAL_PRD.md §4 M5; FINAL_PRD-kestrel-basis.md §4 Q7 (FracDiff-Zustand als Feature)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Fraktionale Differenzierung d ∈ (0,1) macht Zeitreihen (OI, Preis, Funding) stationär bei minimalem Memory-Verlust — entscheidend für ML-Features. Q7-Variante (PRD-kestrel): Vorzeichen-Kombinatorik dPreis × dOI identifiziert vier Mechanik-Zustände (Long-Aufbau, Short-Aufbau, Long-Squaring, Short-Covering).
- **Kernannahme(n):** ADF-Test findet konsistent minimales stationäres d; Beta-Gewichte bleiben über 30–90 Tage stabil genug; Mechanik-Zustände aus dPreis × dOI sind kausal interpretierbar.
- **Behaupteter Nutzen:** ADF p < 0.05 nach FFD; ML-Downstream-Sharpe-Lift ≥ 10 %. Q7: zustands-konditionierte Forward-Returns signifikant (p < 0.01 nach FDR); Fade-Signal Win-Rate ≥ 55 %, Sharpe ≥ 0.8.
- **Validierungs-Gate:** ADF p < 0.05; Lift ≥ 10 % (PRD-v1). FDR-korrigierte Signifikanz + Sharpe-Gate (PRD-kestrel Q7).
- **Abhängigkeiten:** Kline-Backfill (REST); OI-Historie
- **Reifegrad laut Quelle:** Implementiert (m5_ffd.py vorhanden)

---

### [C-06] Shannon-Entropie L2-Orderbuch (Greenlight)
- **Quelle:** FINAL_PRD.md §4 M6; FINAL_PRD-kestrel-basis.md §4 S9 (KL-Divergenz-Variante)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** H = -Σ p_i log p_i über die Größen-Verteilung der Top-N Bid+Ask-Levels. Niedrige H = institutionelle Synchronisation = Edge-Fenster (Greenlight). S9-Variante: KL-Divergenz der Orderbuch-Volumenverteilung gegen Random-Walk-Referenz als Entropie-Kollaps-Signal. Komplementär zu PE (Buch-Querschnitt vs. Preis-Zeitachse).
- **Kernannahme(n):** Q5-Quantil der H-Verteilung über 24h identifiziert valide Edge-Fenster; institutionelle Synchronisation ist aus Level-Größen ableitbar; KL-Divergenz-Spike ist im Millisekundenbereich stabil genug für 100-ms-Updates.
- **Behaupteter Nutzen:** Win-Rate-Lift bei nachgelagertem OFI-Trade ≥ 2 pp. PRD-kestrel S9: bedingte AUC +0.03 und gated Sharpe +20 %.
- **Validierungs-Gate:** PRD-v1: Win-Rate-Lift ≥ 2 pp. PRD-kestrel: AUC +0.03 OOS; Fusion (Q12 UND S9) schlägt jede Einzelkomponente.
- **Abhängigkeiten:** Orderbook-State-Engine; S9: Phase-0-Buchaufzeichnung (Backtest), Buch-Rekonstruktor
- **Reifegrad laut Quelle:** Implementiert (m6_entropy.py vorhanden)

---

### [C-07] Permutation Entropy (Bandt-Pompe, Effizienz-Detektor)
- **Quelle:** FINAL_PRD.md §4 M7; FINAL_PRD-kestrel-basis.md §4 Q12
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Ordnungsbasierte Komplexitätsmessung auf Preis-Zeitreihe. PE ≈ 1 → Random Walk (nicht handeln); PE-Einbruch → temporärer Determinismus = Edge-Fenster. PRD-kestrel: Cross-Sectional über das gesamte Perp-Universum; nur die ~10 % Symbole mit niedrigster PE freischalten.
- **Kernannahme(n):** Embedding-Parameter m=4, τ=1 ist für Bybit-Perp-Daten optimal; PE-Drop unter Median korreliert mit Volatilitäts-Clustern; Cross-Sectional-Ranking über Symbole ist stabil genug für 4-h-Fenster.
- **Behaupteter Nutzen:** PRD-v1: PE-Drop korreliert mit Vol-Cluster in [t, t+15min] mit ρ ≥ 0.3. PRD-kestrel: bedingte AUC nachgelagerter Richtungssignale in G1-Fenstern ≥ +0.03.
- **Validierungs-Gate:** ρ ≥ 0.3 (PRD-v1). Bedingte AUC +0.03 + gated Sharpe +20 % über ≥ 2 Jahre Historie (PRD-kestrel).
- **Abhängigkeiten:** Tickers-Stream (1-min-Kline); keine weiteren Abhängigkeiten
- **Reifegrad laut Quelle:** Implementiert (m7_permutation_entropy.py vorhanden)

---

### [C-08] BOCPD auf openInterest / Funding / RV (Regime-Bruch-Detektor)
- **Quelle:** FINAL_PRD.md §4 M8; FINAL_PRD-kestrel-basis.md §4 Q8
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Online-Bayes-Inferenz über Position des letzten Strukturbruchs (Adams & MacKay 2007). Kein Richtungssignal — Meta-Schicht: erkennt, wann Funding-/Vol-/OI-Regime gebrochen sind → Modelle de-aktivieren und neu fitten. PRD-kestrel: parallele Instanzen auf 1h-RV, Funding-Rate, FracDiff-OI, Basis-z-Score.
- **Kernannahme(n):** Geometrische Run-Length-Prior mit Hazard 1/λ ist auf Bybit-Regimes kalibrierbar; Student-t-Likelihood ist ausreichend für alle vier Reihen; Hazard-Prior-Fehlkalibrierung erzeugt nicht zu viele False Positives (< 1/Woche je Reihe).
- **Behaupteter Nutzen:** Detection-Latenz ≤ 2 min (PRD-v1). PRD-kestrel: Detektions-Verzögerung ≤ 24 h bei Top-10-Brüchen; G2-gated Strategien: Max-DD-Reduktion ≥ 20 % bei Sharpe-Verlust ≤ 10 %.
- **Validierungs-Gate:** PRD-v1: Detection-Latenz ≤ 2 min, FP ≤ 10 %/Tag. PRD-kestrel: DD-Reduktion ≥ 20 %.
- **Abhängigkeiten:** Tickers-Stream + OI-Historie; Q7 (FracDiff-Reihe) für PRD-kestrel-Variante
- **Reifegrad laut Quelle:** Implementiert (m8_bocpd.py vorhanden)

---

### [C-09] HMM Vola-OFI-Funding (3-State, Regime-Klassifikation)
- **Quelle:** FINAL_PRD.md §4 M9
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** 3-State-HMM (Trend / Mean-Revert / High-Vol-Crash) auf Merkmals-Vektor [realized_vol_5min, sign(OFI_5min), fundingRate]. State-Posterior als Gating-Feature für Strategie-Aktivierung (Mean-Revert-Strategien nur in State 2). Baum-Welch-Training, Viterbi für Online-Decoding.
- **Kernannahme(n):** Drei latente Zustände sind ausreichend zur Beschreibung der Marktphasen; Emission-Verteilungen sind gaussisch; Label-Switching wird durch fixe Transition-Priors oder Label-Alignment verhindert.
- **Behaupteter Nutzen:** State-Stabilität ≥ 80 % der Bars; Strategie-Win-Rate pro State signifikant unterschiedlich (Chi² p < 0.01).
- **Validierungs-Gate:** Chi² p < 0.01 Signifikanztest auf Win-Rate-Unterschied pro State.
- **Abhängigkeiten:** OFI-Stream (C-01/M2), Funding-Stream, Kline-Backfill
- **Reifegrad laut Quelle:** Implementiert (m9_hmm.py vorhanden); research_notes empfiehlt als Weiterentwicklung des Quantile-Classifiers

---

### [C-10] MF-DFA Multifraktal / Hölder-Regularität
- **Quelle:** FINAL_PRD.md §4 M10; FINAL_PRD-kestrel-basis.md §4 Q15
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Skalierungs-Exponent h(q) für verschiedene Moment-Ordnungen quantifiziert Multifraktalität. Δh = h(q_min) − h(q_max) misst Spektrumsbreite. PRD-kestrel: BTC ist robust multifraktal; lokaler Hölder-Exponent α(t) misst ob Markt mono- (effizient) oder multifraktal (fat tails, Herding) operiert — prädiktives Feature für RV-Persistenz und Tail-Risiko.
- **Kernannahme(n):** Rolling N=2048 1-min-Returns ist ausreichende Stichprobe für stabile h(q)-Schätzung; Δh-Spike > z=2 identifiziert echte Regime-Änderungen; BTC-Multifraktalität ist persistent genug für Features.
- **Behaupteter Nutzen:** PRD-v1: Δh erkennt 70 % historischer Regime-Shifts mit ≤ 30 min Vorlauf. PRD-kestrel: ΔR² ≥ +0.02 im Vol-Stack; Tail-AUC > 0.60 für „RV-Spike in 24h".
- **Validierungs-Gate:** PRD-v1: 70 % Detection-Rate. PRD-kestrel: ΔR² ≥ +0.02; Tail-AUC > 0.60.
- **Abhängigkeiten:** Kline-1min-Backfill; Q4/PatchTST-RV als Abnehmer (PRD-kestrel)
- **Reifegrad laut Quelle:** Implementiert (m10_mfdfa.py vorhanden), als Diagnose-Tool/Ensemble klassifiziert

---

### [C-11] TDA / Persistent Homology (Multi-Asset Crash-Frühwarnung)
- **Quelle:** FINAL_PRD.md §4 M11; FINAL_PRD-fable5.md §4 M-S17 (IV-Surface-Variante)
- **Zielmarkt laut Quelle:** Futures (Perpetual); Optionen (M-S17-Variante)
- **Kernidee:** Rolling Multi-Asset-Returns-Matrix → Vietoris-Rips-Filtration → Persistence Landscape L¹-Norm. L¹-Spike > z=3 → Risk-Off. M-S17-Variante: IV-Surface als 3D-Mannigfaltigkeit — topologische Brüche als Tail-Risk-Frühwarnung; kombiniert Orderbuch-Tiefe (Liquiditätslücken) und IV-Surface.
- **Kernannahme(n):** 5-Symbol-Panel (BTC, ETH, SOL, BNB, XRP) liefert topologisch informative Punktwolke; L¹-Norm ist sensitiv gegenüber Crash-Vorläufern; Bybit-Options-Liquidität reicht für verlässliche IV-Surface (M-S17).
- **Behaupteter Nutzen:** PRD-v1: ρ(L¹-z-Score → Forward-24h-DD) ≥ 0.4; Risk-Off reduziert Max-DD ≥ 20 %. PRD-fable5 M-S17: Precision@k ≥ 1.2× Zufallsbasis OOS in ≥ 2 Fenstern.
- **Validierungs-Gate:** PRD-v1: ρ ≥ 0.4. PRD-fable5: Lift ≥ 1.2× konsistent OOS.
- **Abhängigkeiten:** Multi-Symbol-Kline-Backfill; M-S17: options-tickers WS (IV/Greeks, kein Archiv → Aufzeichnung), orderbook.200/1000
- **Reifegrad laut Quelle:** Implementiert (m11_tda.py vorhanden); M-S17-Variante: spezifiziert, aufwändig (M-Klasse)

---

### [C-12] RQA (Recurrence Quantification Analysis)
- **Quelle:** FINAL_PRD.md §4 M12
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Phasenraum-Rekonstruktion (Takens-Einbettung) erzeugt Trajektorie; Recurrence Plot via ε-Schwelle. DET (Determinismus) + LAM (Laminarität) detektieren kritische Regime vor Phasenübergängen. DET-Spike + LAM-Spike → Laminar-Phase = Konsolidierung vor Breakout.
- **Kernannahme(n):** Optimales τ via Mutual-Information ist berechenbar; ε-Schwelle ist über Symbole übertragbar; DET > 0.7 ist diskriminativ genug für Breakout-Timing.
- **Behaupteter Nutzen:** DET > 0.7 → |Return| > 1 % in 1h: Hit-Rate ≥ 55 %.
- **Validierungs-Gate:** Hit-Rate ≥ 55 % bei DET > 0.7 und nachfolgendem Breakout.
- **Abhängigkeiten:** Kline-5min-Stream
- **Reifegrad laut Quelle:** Implementiert (m12_rqa.py vorhanden)

---

### [C-13] Cross-Sectional Ergodicity-Reversion Z-Score
- **Quelle:** FINAL_PRD.md §4 M13; FINAL_PRD-kestrel-basis.md §4 S1 (Ergodizitäts-Defekt-Flag)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Symbole mit Zeit-gemitteltem Return weit weg vom Ensemble-Mittel (|z| > 2.5) tendieren zur Mean-Reversion. S1-Variante (PRD-kestrel): Ergodizitäts-Defekt aus OFI/Returns → Flag für gerichteten Ausbruch innerhalb des Lead-Lag-Moduls K3 (kein eigenständiges Gate, nur Flag).
- **Kernannahme(n):** Top-20-USDT-Perp-Panel liefert ausreichende Querschnittsbreite; z > 2.5 ist nicht durch BTC-Dominanz allein erklärbar; Ergodizitätsverletzung ist kausal mit Mean-Reversion verknüpft.
- **Behaupteter Nutzen:** PRD-v1: Sharpe ≥ 1.0 nach Fees (Long-Short-Portfolio); Hit-Rate ≥ 53 %. PRD-kestrel S1: K3-Hit-Rate ≥ +5 Prozentpunkte in Flag-Fenstern.
- **Validierungs-Gate:** PRD-v1: Sharpe ≥ 1.0. PRD-kestrel: K3-Hit-Rate-Uplift ≥ +5 pp.
- **Abhängigkeiten:** Multi-Symbol-Panel-Infrastruktur; K3-Infrastruktur (S3/S11/Q3, PRD-kestrel)
- **Reifegrad laut Quelle:** Implementiert (m13_cross_sectional_z.py vorhanden); S5-Strategie noch nicht testbar (Harness-blockiert)

---

### [C-14] Hawkes-Spektralradius ρ(Φ) (Reflexivitäts-Kritikalität)
- **Quelle:** FINAL_PRD.md §4 M14; FINAL_PRD-kestrel-basis.md §4 S2
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Orderbuch + Liquidationen als 6-D selbst-erregender Punktprozess; Branching-Matrix Φ beschreibt endogene Kausalität; ρ(Φ) → 1 = kritischer Zustand vor Kaskade. PRD-kestrel risikoarmer Start: Branching-Ratio-Approximation (Hardiman/Bouchaud) statt voller MLE.
- **Kernannahme(n):** 6 Event-Typen (MO±, LO±, CX±) + 2 Liquidations-Channels modellieren das Orderbuch vollständig; ρ > 0.85 ist auf Bybit ein valider Kritikalitätsschwellwert (PRD-v1; empirisch in Frage gestellt); Rolling-Window 5 min ist kurz genug für Echtzeitanwendung.
- **Behaupteter Nutzen:** PRD-v1: ρ steigt ≥ 0.7 ≥ 30 s vor 80 % historischer Kaskaden; FP ≤ 2/Tag. PRD-kestrel S2: Kaskaden-AUC > 0.65 bei Lead-Time ≥ 10 min; K1-Max-DD-Reduktion ≥ 20 %.
- **Validierungs-Gate:** PRD-v1: 80 % Detection-Rate, FP ≤ 2/Tag. PRD-kestrel: AUC > 0.65; nach 3 Monaten + 2 Iterationen sonst Archiv.
- **Abhängigkeiten:** Orderbook-State + Trade-Stream + Liquidation-Buffer; Phase-0-Aufzeichnung
- **Reifegrad laut Quelle:** Implementiert (m14_hawkes.py vorhanden); empirisch: Schwellwert 0.85 wird nie erreicht (ρ-Median ~2e-7 auf BTC)

---

### [C-15] Gutenberg-Richter b-Wert + Omori-Utsu Nachbeben-Timing
- **Quelle:** FINAL_PRD.md §4 M15; FINAL_PRD-kestrel-basis.md §4 S4
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Liquidationen folgen Erdbeben-Statistik: GR: log₁₀ N(≥M) = a − bM; Omori: λ(t) = K/(t+c)^p. b-Wert < 1 → Trend-Fortsetzung; Omori-Fit nach Mainshock liefert quantitatives Entry-Timing für Mean-Reversion (Nachbebenphase). PRD-kestrel: Entry nicht in den Crash, sondern wenn Rate unter Schwelle (Erschöpfung).
- **Kernannahme(n):** Liquidations-Magnitudenverteilung folgt Potenzgesetz (GR); Aftershock-Rate folgt Omori-Potenzgesetz mit stabilen K,c,p; scipy.curve_fit konvergiert mit ≥ 50 Events.
- **Behaupteter Nutzen:** PRD-v1: b-Wert-Drift erkennt 70 % Mainshocks ≥ 10 min Vorlauf; Omori-MSE < Baseline. PRD-kestrel: Omori-Fit-Güte R² ≥ 0.8 auf ≥ 70 % der Kaskaden; Win-Rate ≥ 58 %, Sharpe ≥ 1.0.
- **Validierungs-Gate:** PRD-v1: Detection-Rate 70 %. PRD-kestrel: R² ≥ 0.8 / Win-Rate ≥ 58 % / Sharpe ≥ 1.0.
- **Abhängigkeiten:** Liquidation-Event-Buffer; Phase-0-Aufzeichnung; Q2 (Erschöpfungs-Bestätigung, PRD-kestrel)
- **Reifegrad laut Quelle:** Implementiert (m15_gr_omori.py vorhanden)

---

### [C-16] TFSAX + Smith-Waterman Sequence Alignment
- **Quelle:** FINAL_PRD.md §4 M16; FINAL_PRD-kestrel-basis.md §4 S5; FINAL_PRD-fable5.md §4 M-S23 (Verwandter Ansatz auf Orderflow)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Preiszeitreihe wird via PAA + z-Norm + Gauß-Bins in Symbolsequenz transformiert (TFSAX: + Trend-Distanz). Smith-Waterman findet lokal optimale Alignments mit Insertions/Deletions → toleriert zeitliche Verzerrungen. Top-k-Matches in 5y-Bibliothek liefern bedingte Forward-Return-Verteilungen. M-S23-Variante (PRD-fable5): symbolisierter Orderflow (Taker-Side-basiert) statt Preis-Reihe.
- **Kernannahme(n):** Historische Marktphasen wiederholen sich mit genug Regelmäßigkeit für valide Präzedenz-Matches; TFSAX-Encoding ist stationär über Marktregime; Match-Score-Schwelle 0.75 ist diskriminativ.
- **Behaupteter Nutzen:** PRD-v1: Hit-Rate ≥ 56 %; Sharpe ≥ 1.2. PRD-kestrel: bedingte OOS-AUC > 0.55 (hartes Gate, sonst Drop). PRD-fable5 M-S23: Balanced Accuracy ≥ 0.55 OOS + Surrogate-Test bestanden (p < 0.05).
- **Validierungs-Gate:** PRD-v1: Hit-Rate ≥ 56 %. PRD-kestrel: OOS-AUC > 0.55 sonst ersatzloser Drop. PRD-fable5: BA ≥ 0.55 + Surrogate p < 0.05.
- **Abhängigkeiten:** Kline-Backfill (5y); Sequenz-Library-Storage; M-S23: publicTrade-Archiv
- **Reifegrad laut Quelle:** Implementiert (m16_tfsax_sw.py vorhanden); als Moonshot/hartes Gate klassifiziert

---

### [C-17] Renyi-Transfer-Entropy Lead-Lag-Graph / Transfer-Entropy (Shannon)
- **Quelle:** FINAL_PRD.md §4 M17; FINAL_PRD-kestrel-basis.md §4 S3
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Renyi-TE verallgemeinert Schreiber-TE und gewichtet Tail-Events stärker (q > 1); asymmetrische Kanten T_X→Y ≠ T_Y→X liefern gerichteten Informationsfluss. BTC führt Alts mit 30–60 s Lag. PRD-kestrel S3: Standard-Shannon-TE als K3-Achse 1 (von drei Konsens-Achsen).
- **Kernannahme(n):** Renyi-q Parameter q > 1 ist optimal für crypto-relevante Tail-Events; 30–60 s Lead-Lag-Fenster ist über Retail-Latenz und damit handelbar; BTC-Lead-Struktur ist über Altseason hinweg stabil genug.
- **Behaupteter Nutzen:** PRD-v1: ρ(Alt-Forward-Return, BTC-Move) bei T > 0.05: ρ ≥ 0.3. PRD-kestrel K3: bedingte Richtungs-AUC > 0.55 auf Konsens-Kanten; Sharpe ≥ 0.8.
- **Validierungs-Gate:** PRD-v1: ρ ≥ 0.3. PRD-kestrel: AUC > 0.55 + Sharpe ≥ 0.8; FDR-korrigiert.
- **Abhängigkeiten:** Multi-Symbol-Kline-Stream; Symbolisierungs-Pipeline; IDTxl/PyInform
- **Reifegrad laut Quelle:** Implementiert (m17_renyi_te.py vorhanden)

---

### [C-18] PatchTST (Funding-Cycle-Forecast / RV-Prognose)
- **Quelle:** FINAL_PRD.md §4 M18; FINAL_PRD-kestrel-basis.md §4 Q4
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Zeitreihe in Subseries-Patches segmentieren, channel-independent über Transformer. PRD-v1: Direktionale 5-min-Return-Prognose vor Funding-Settlement. PRD-kestrel Q4 (zentral): Realized-Volatility-Prognose (RV) als einziges empirisch belegtes Signal der Baseline; versorgt ALLE Strategien mit Vol-Targeting und Stops. Hartes R²-Gate.
- **Kernannahme(n):** PatchTST übertrifft HAR-RV-Baseline auf Bybit-Daten bei OOS-R² > 0.25; Channel-Independence und lange Lookbacks sind für Funding-Zyklen optimal; Kestrel-v1.4-Baseline (R² = 0.25) ist replizierbares Referenzniveau.
- **Behaupteter Nutzen:** PRD-v1: Direktional-Accuracy ≥ 55 %; Sharpe ≥ 1.0. PRD-kestrel: OOS-R² > 0.25 + QLIKE ≥ 5 % besser als HAR-RV; Abbruch falls HAR-RV nicht geschlagen.
- **Validierungs-Gate:** PRD-v1: Dir-Accuracy ≥ 55 %. PRD-kestrel: R² > 0.25 + QLIKE-Gate (hartes Gate des gesamten Vol-Stacks).
- **Abhängigkeiten:** FFD-M5, Kline-Backfill, Funding-History, RTX 5060 Ti; Kanäle Q15/Q16/Q17/Q2 für PRD-kestrel
- **Reifegrad laut Quelle:** Implementiert (m18_patchtst.py vorhanden); Kestrel-v1.4: Vol-Prognose R²=0.249 auf Test (bestätigt)

---

### [C-19] TimesNet 2D-Periodizität
- **Quelle:** FINAL_PRD.md §4 M19; FINAL_PRD-kestrel-basis.md §4 Q13 (zurückgestellt)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** 1D-Zeitreihe via FFT in dominante Perioden zerlegt → 2D-Tensor (Inter-Period × Intra-Period). 2D-Inception-CNN erkennt zyklische Muster, die 1D-Models verpassen. Ideal für 8h-Funding-Zyklen + 24h-Tagesrhythmus + Wochenzyklus.
- **Kernannahme(n):** FFT identifiziert stabil Top-3-Perioden (8h, 24h, 168h); 2D-CNN übertrifft PatchTST im 8h-Period-Forecast; Perioden sind über Marktregime stabil.
- **Behaupteter Nutzen:** Outperformance von PatchTST in 8h-Period-Forecast-MSE. PRD-kestrel: zurückgestellt (DL-Redundanz zu Q4/Q9; als dokumentierte Alternativ-Architektur geführt).
- **Validierungs-Gate:** MSE-Outperformance gegen PatchTST (PRD-v1).
- **Abhängigkeiten:** FFD (M5), Kline-5min; RTX 5060 Ti
- **Reifegrad laut Quelle:** Implementiert (m19_timesnet.py vorhanden); PRD-kestrel: zurückgestellt

---

### [C-20] MOMENT Foundation Model (Zero-Shot-Forecasting)
- **Quelle:** FINAL_PRD.md §4 M20
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Pre-trained Time-Series Foundation Model (T5-Architektur, RevIN-Normierung). Erlaubt Zero-Shot-Forecasting auf unbekannte Symbole — kritisch für Altcoin-Rotation bei Neulisting. Fine-Tune via LoRA für etablierte Symbole.
- **Kernannahme(n):** MOMENT-base (110 M Parameter) verallgemeinert auf Bybit-Crypto-Daten ohne Fine-Tuning; Zero-Shot-MASE < 1.0 auf Bybit; LoRA-Fine-Tune verbessert performance ohne Overfitting.
- **Behaupteter Nutzen:** MASE < 1.0 zero-shot; Sharpe ≥ 0.8 signalbasiert.
- **Validierungs-Gate:** MASE < 1.0; Sharpe ≥ 0.8.
- **Abhängigkeiten:** Kline-Backfill, FFD (M5); RTX 5060 Ti 16 GB (MOMENT-large: nicht trainierbar)
- **Reifegrad laut Quelle:** Implementiert (m20_moment.py vorhanden)

---

### [C-21] Long/Short-Account-Ratio Smart-Money-Divergenz / Crowding
- **Quelle:** FINAL_PRD.md §4 M21; FINAL_PRD-kestrel-basis.md §4 Q11
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Bybit-Long/Short-Ratio aggregiert über Konten (≈ Retail-gewichtet; 1 Wal = 1 Account). Extremer Retail-Skew + gegenläufige Preisbewegung → Smart-Money-Counter-Trade. PRD-kestrel: nur als Feature (Brennstoff-Index für Kaskaden, Konditionierungs-Input), nie standalone.
- **Kernannahme(n):** Konto-aggregierter Skew (nicht volumen-gewichtet) ist ein valider Contrarian-Indikator; buyRatio-Schwelle 0.25 ist diskriminativ; API-Daten ab 2020-07 sind repräsentativ.
- **Behaupteter Nutzen:** PRD-v1: Hit-Rate ≥ 54 %; Sharpe ≥ 0.8. PRD-kestrel: ΔAUC ≥ +0.02 in Abnehmermodellen (Q2/Q9).
- **Validierungs-Gate:** PRD-v1: Hit-Rate ≥ 54 %. PRD-kestrel: ΔAUC ≥ +0.02; sonst Drop.
- **Abhängigkeiten:** L/S-Ratio-Poller (REST /v5/market/account-ratio); Q2/Q9 als Abnehmer
- **Reifegrad laut Quelle:** Implementiert (m21_ls_ratio.py vorhanden)

---

### [C-22] Funding-Rate-Clamp Pressure-Release (Settlement-Timing)
- **Quelle:** FINAL_PRD.md §4 M22; FINAL_PRD-kestrel-basis.md §4 Q1 (erweitert)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Bybit clamped F bei ±0.05 % (fundingCap symbolabhängig!). Clamp-Funktion staut Druck → Pressure-Release nach Settlement. Q1-Variante (PRD-kestrel): kumulierter geklemmter Überdruck D_t × τ (Zeit-bis-Settlement) als kontinuierlicher Drucksensor aus 1-min-Premium-Index-Kline (tiefe Historie).
- **Kernannahme(n):** Mechanismus ist deterministisch; Premium-Index-Kline enthält vollständigen Druckverlauf zwischen Settlements; fundingInterval symbolabhängig (MUSS aus instruments-info gelesen werden); Pressure-Release-Richtung ist vorhersehbar.
- **Behaupteter Nutzen:** PRD-v1: Sharpe ≥ 1.5; Hit-Rate ≥ 56 %; Max-DD < 10 %. PRD-kestrel: OOS-Sharpe ≥ 1.2, Win-Rate ≥ 55 %, PF ≥ 1.3 über ≥ 200 Trades; Abbruch bei Sharpe < 0.5.
- **Validierungs-Gate:** PRD-v1: Sharpe ≥ 1.5. PRD-kestrel: Sharpe ≥ 1.2 / WR ≥ 55 % / PF ≥ 1.3.
- **Abhängigkeiten:** Tickers-Stream + Settlement-Scheduler; REST premium-index-price-kline (PRD-kestrel); Q5 Spread-Markt (Execution, PRD-kestrel)
- **Reifegrad laut Quelle:** Implementiert (m22_funding_pressure.py vorhanden); empirisch getestet (S3-Strategie); Thesis teilweise bestätigt (entry ok, exit unzureichend)

---

### [C-23] Mark-Index-Basis Settlement Convergence
- **Quelle:** FINAL_PRD.md §4 M23
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Basis = (markPrice − indexPrice) / indexPrice. Persistent positive Basis → Perp überbewertet → Funding zieht Basis Richtung 0 vor Settlement. Convergence-Trade in [Settlement − 60 min, Settlement].
- **Kernannahme(n):** Basis-Threshold 0.0008 (0.08 %) ist historisch diskriminativ; Convergence ist innerhalb des Settlement-Fensters zuverlässig genug für Taker-Cost.
- **Behaupteter Nutzen:** Hit-Rate ≥ 58 %; Sharpe ≥ 1.5.
- **Validierungs-Gate:** Hit-Rate ≥ 58 %; Sharpe ≥ 1.5.
- **Abhängigkeiten:** Tickers-Stream + Settlement-Scheduler
- **Reifegrad laut Quelle:** Implementiert (m23_basis_convergence.py vorhanden)

---

### [C-24] Kalman-Funding-Premium-Decomposition
- **Quelle:** FINAL_PRD.md §4 M24
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Funding Rate = persistenter Fair-Funding-Drift + transienter Sentiment-Spike (State-Space-Modell). Kalman-Filter trennt beide Komponenten. Sentiment-Spike > 2σ → Contrarian-Fade-Signal.
- **Kernannahme(n):** 2-D State-Space mit pykalman ist ausreichend; Kalman-Gain-Kalibrierung über Q,R-Parameter ist stabil; sentiment_t ist i.i.d. Rauschen relativ zum trend_funding.
- **Behaupteter Nutzen:** Sharpe ≥ 1.0 für Fade-Strategie.
- **Validierungs-Gate:** Sharpe ≥ 1.0.
- **Abhängigkeiten:** Tickers-Stream + Funding-History
- **Reifegrad laut Quelle:** Implementiert (m24_kalman_premium.py vorhanden)

---

### [C-25] Kyle's Lambda (Adverse Selection / Toxic Flow Filter)
- **Quelle:** FINAL_PRD.md §4 M25; FINAL_PRD-kestrel-basis.md §4 Q6 (VPIN + Kyle-λ als Veto)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Permanenter Preisimpakt pro Volume-Einheit via OLS über signiertes Volumen. Anstieg λ → informierte Trader aktiv → MM ziehen Liquidität ab → Toxic-Flow-Frühwarnung. PRD-kestrel: VPIN (Volume-basiert) + Kyle-λ + Bybit-Verfeinerung: exakte Taker-Side statt Bulk-Heuristik + RPI-Flag-Segmentierung. Unbedingtes Trade-Veto (V0) über allen Modulen.
- **Kernannahme(n):** OLS-Regression über 100 Trades gibt stabile λ-Schätzung; VPIN > P95 geht Preissprüngen voraus (empirisch für BTC bestätigt); RPI-Flag-Segmentierung erhöht Treffsicherheit.
- **Behaupteter Nutzen:** PRD-v1: Limit-Order-Loss-Reduktion ≥ 30 %. PRD-kestrel: Jump-OR > 3 (p < 0.01); Veto im Strategie-Backtest: Max-DD-Reduktion ≥ 15 % bei Bruttorendite-Verlust ≤ 5 %.
- **Validierungs-Gate:** PRD-v1: Loss-Reduktion ≥ 30 %. PRD-kestrel: Odds-Ratio > 3; OR < 1.5 → nur Feature.
- **Abhängigkeiten:** publicTrade + Orderbook-State; mehrjähriges Tick-Archiv (PRD-kestrel)
- **Reifegrad laut Quelle:** Implementiert (m25_kyle_lambda.py vorhanden)

---

### [C-26] SIR-Kompartiment-Liquidations-Contagion
- **Quelle:** FINAL_PRD.md §4 M26; FINAL_PRD-kestrel-basis.md §4 Q2 (erweiterte Variante)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Trader-Population in S (Susceptible, gehebelte Positionen nahe Liq-Preis), I (Infected, gerade liquidiert), R (Recovered). R₀ = β/γ > 1 → Kaskade selbsterhaltend. PRD-kestrel Q2: erweitert um Bankruptcy-Preis (implizierter Hebel der Kohorte), Insurance-Pool-Delta (Slippage-Proxy) und ADL-`pr` (plattformweiter Stress-Score). Dreigleisige Risk-Off-Ampel.
- **Kernannahme(n):** OI ≈ susceptible Population; Liquidationsrate ≈ I; β kalibrierbar über OLS; Bybit pusht vollständige Liquidationsströme mit Bankruptcy-Preis; Insurance/ADL ohne REST-Historie → Aufzeichnung nötig.
- **Behaupteter Nutzen:** PRD-v1: R₀ > 1 mit ≥ 5 min Vorlauf zu 70 % der Mainshock-Cascades. PRD-kestrel Q2: Recall ≥ 90 % Top-Events; Max-DD-Reduktion ≥ 25 %; Erschöpfungs-Entry Win-Rate ≥ 58 %.
- **Validierungs-Gate:** PRD-v1: 70 % Detection-Rate. PRD-kestrel: Recall ≥ 90 %.
- **Abhängigkeiten:** Liquidation-Buffer + Tickers-Stream; Phase-0-Aufzeichnung (Insurance/ADL, PRD-kestrel); Q7/Q11 als Brennstoff-Features
- **Reifegrad laut Quelle:** Implementiert (m26_sir.py vorhanden)

---

### [C-27] Cori-Rₜ Renewal-Equation auf Liquidations-Inzidenz *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-S21 (Rang 1)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Renewal-Gleichung Iₜ = Rₜ · Σ_{s≥1} I_{t−s}·ω_s mit ω_s = Generationszeit-Kernel (einmalig aus Bulk-Historie fixiert). Rₜ > 1 zeigt selbstverstärkende Kaskade VOR messbarer Volumenseskalation. Geschlossene Gamma-Konjugat-Posterior-Form → kein ML-Training nötig. Unterschied zu C-14/C-26: normierte, volumenunabhängige Selbstverstärkungs-Rate.
- **Kernannahme(n):** Liquidations-Punktprozess ist strukturell isomorph zum epidemischen Inzidenz-Punktprozess; Generationszeit-Kernel ω_s ist über Marktregime stabil (kritischste Annahme — Strategie-A-Bruchpunkt); allLiquidation-Feed ist vollständig (neuer Feed seit 2024).
- **Behaupteter Nutzen:** Balanced Accuracy ≥ 0.55 OOS (walk-forward, ≥ 2 disjunkte Fenster) für „Großkaskade in Folgefenster" UND Brier-Score besser als reiner Volumen-Schwellwert.
- **Validierungs-Gate:** BA ≥ 0.55 OOS in ≥ 2 disjunkten Zeitfenstern + Brier < Volumen-Baseline. Abbruch: BA ≤ 0.55 in einem Fenster.
- **Abhängigkeiten:** allLiquidation WS (#12, live); Bulk-Download (#34) für einmalige ω_s-Schätzung
- **Reifegrad laut Quelle:** Idee/spezifiziert (nicht im Repo implementiert; Quick Win S/Tage eingeschätzt)

---

### [C-28] NB-k Superspreading-Dispersion der Liquidations-Contagion *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-S22 (Rang 2)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Offspring-Verteilung (Zahl der Folgeliquidationen je Auslöser) als Negativ-Binomial NB(R,k). Dispersionsparameter k misst Tail-Heterogenität der Kaskaden-Verzweigung. Kleines k = seltenere, aber explosivere Kaskaden. Edge-Hypothese: Tail-Heterogenität ist nicht eingepreist, weil Standard-Risikomaße nur Mittelwerte betrachten. Generationszeit-Fenster aus C-27 fixiert (kein freier Parameter).
- **Kernannahme(n):** NB ist signifikant überdispers gegen Poisson (p < 0.05 via LR-Test); Generationszeit-Fenster aus C-27 ist ausreichend stabil; BTC/ETH haben genug Kaskaden für stabile k-Schätzung.
- **Behaupteter Nutzen:** Precision@k-Lift ≥ 1.2 gegenüber unbedingter Tail-Event-Rate OOS in ≥ 2 Zeitfenstern UND NB signifikant überdispers.
- **Validierungs-Gate:** Lift ≥ 1.2 OOS; NB p < 0.05 LR-Test. Abbruch: Lift ≤ 1.2 oder p ≥ 0.05.
- **Abhängigkeiten:** allLiquidation WS (#12), Bulk-Download (#34); C-27 (ω_s-Fenster gebunden)
- **Reifegrad laut Quelle:** Idee/spezifiziert (Quick Win S/Tage)

---

### [C-29] Avalanche Shape Collapse / universelle Skalenfunktion *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-S13 (Rang 3)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Reskalierte Liquidations-Burst-Profile (Aktivitätsrate über Zeit) kollabieren auf universelle invertierte Parabel (crackling-noise-Theorie). Aus der Profilform der *laufenden* Kaskade lässt sich die **Restdauer** prognostizieren — quantitatives Exit-Timing-Signal für Mean-Reversion-Entry.
- **Kernannahme(n):** Bybit-Liquidations-Kaskaden folgen universeller Skalenfunktion (invertierte Parabel); genug Burst-Events für stabilen Collapse auf Trainings-Splits; Detektionsschwelle und Fenstergröße als einzige Parameter.
- **Behaupteter Nutzen:** Collapse-Residual ≤ 30 % OOS in ≥ 2 Fenstern UND Restdauer-MAE besser als Konstant-Mittelwert-Baseline.
- **Validierungs-Gate:** Residual ≤ 30 % + MAE < Baseline. Abbruch: Residual > 30 % oder MAE nicht besser.
- **Abhängigkeiten:** allLiquidation WS (#12), Bulk-Download (#34)
- **Reifegrad laut Quelle:** Idee/spezifiziert (Aufwand M/Wochen)

---

### [C-30] Natural Time κ₁-Ordnungsparameter (Seismologie) *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-S11 (Rang 4)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** κ₁ (Varianz der natural-time-gewichteten Marken) nähert sich beim Übergang zur Kritikalität dem universellen Wert 0.070. Eigenständiger zweiter Kaskaden-Indikator mit anderem mathematischen Kern als C-27 (Rₜ) → Ensemble-Diversität. Schwellwert ist theoretisch, nicht gefittet.
- **Kernannahme(n):** Liquidations-Punktprozess erfüllt die Voraussetzungen der Natural-Time-Analyse (selber Strukturmatch wie seismische Sequenzen); κ₁ ≈ 0.070 ist universeller kritischer Wert auf diesem Markt.
- **Behaupteter Nutzen:** ROC-AUC ≥ 0.55 OOS (walk-forward, ≥ 2 Zeitfenster) für Kaskaden-Vorhersage. Zusatz: inkrementelle Information über C-27 (Rₜ) hinaus.
- **Validierungs-Gate:** AUC ≥ 0.55 OOS. Abbruch: AUC ≤ 0.55; falls AUC > 0.55 aber keine inkrementelle Information → zurückstellen (nicht verwerfen).
- **Abhängigkeiten:** allLiquidation WS (#12), publicTrade WS (#8), Bulk-Download (#34)
- **Reifegrad laut Quelle:** Idee/spezifiziert (Quick Win S/Tage)

---

### [C-31] Cyclostationary Cyclic Spectrum + CFAR-Detektion (Algorithmischer Footprint) *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-S14 (Rang 7)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** TWAP/Iceberg-Bots erzeugen periodische Muster in Inter-Arrival-Zeiten der Trades; Cyclic Spectrum (SCF) macht sie sichtbar, CFAR detektiert Peaks bei kontrollierter Falschalarmrate. Orthogonal zu C-16 (Frequenz- vs. Sequenzdomäne).
- **Kernannahme(n):** Algorithmische Ausführungs-Muster persistieren über das Validierungsfenster hinaus (adaptiver Gegner = Hauptrisiko); Handelbarer Lead-Zeit > 50 ms Retail-Latenz; Sekunden-Horizont übersteigt Fee-Schwelle (fraglich).
- **Behaupteter Nutzen:** Peak-Stabilität gegen Surrogate (geshuffelte Inter-Arrivals) bestanden, p ≤ 0.05, in ≥ 2 Zeitfenstern.
- **Validierungs-Gate:** Surrogate p ≤ 0.05 in ≥ 2 Fenstern. Abbruch: p > 0.05 oder Lead-Zeit < 50 ms.
- **Abhängigkeiten:** publicTrade WS (#8), Inter-Arrival-Zeiten
- **Reifegrad laut Quelle:** Idee/spezifiziert (Aufwand M/Wochen; gelbe Flagge: Sekunden-Horizont evtl. unter Fee-Schwelle)

---

### [C-32] Funding-Rate Contrarian (Extremwert) *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-Q12 (Rang 8)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Extreme Funding-Rate → Überextension durch Haltekosten und Arbitrage-Kapital → Zwangskorrektur. Konträres Direktionalsignal auf 24h-Horizont (REST-only, mittelfristig, kein Echtzeitbedarf). Abgegrenzt von C-22 (kurzfristig, mechanischer Settlement-Trigger).
- **Kernannahme(n):** Extremwert ±2σ über 30-Tage-Rolling ist dauerhaft diskriminativ; Carry-Kompression seit 2024 reduziert Signal (dokumentiert, schneller Zerfall erwartet).
- **Behaupteter Nutzen:** Mittlerer Contrarian-Return > 0 auf 24h-Basis OOS über 180-Tage-Fenster, in ≥ 2 Fenstern, nach Kosten (> 0.11 % je Round-Trip).
- **Validierungs-Gate:** Return > 0 nach Kosten OOS in ≥ 2 × 180-Tage-Fenster. Abbruch: Return ≤ 0 in einem Fenster.
- **Abhängigkeiten:** tickers WS, Funding History REST, Premium-Index, OI REST — alle CONFIRMED
- **Reifegrad laut Quelle:** Idee/spezifiziert (Quick Win S/Tage; Persistenz unter aktuellem Carry-Regime fraglich)

---

### [C-33] Volatilitäts-Risikoprämie / Short-Vola Optionen *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §4 M-Q14 (Rang 10)
- **Zielmarkt laut Quelle:** **Optionen** (Bybit BTC-Optionen)
- **Kernidee:** Strukturelle Absicherungsnachfrage → systematisch überbewertete implizite Volatilität → ernterbare Prämie (IV − RV). Short-Vola-Strategie mit Delta-Hedge. ATM-fokussiert (geringes Overfitting-Risiko). Einziger Ansatz, der explizit Optionen adressiert.
- **Kernannahme(n):** IV − RV ≥ 3 % auf 12-Monats-Basis; Bybit-Options-Liquidität reicht für verlässliche ATM-Positionierung; Mindestkapital ~$5k für Margin/Delta-Hedge.
- **Behaupteter Nutzen:** (IV − RV) ≥ 3 % im 12-Monats-OOS in ≥ 2 Fenstern; ernterbar nach Hedging-Kosten.
- **Validierungs-Gate:** (IV − RV) ≥ 3 % OOS. Abbruch: < 3 % in einem Fenster; Liquidität unzureichend.
- **Abhängigkeiten:** options-tickers WS (#10, public), hist. Volatility REST (#29), Kline; kein IV-Archiv → Eigenaufzeichnung; Options-Taker-Fee 0.03 %
- **Reifegrad laut Quelle:** Idee/spezifiziert (Aufwand L/Wochen+; höchste Eintrittsschwelle)

---

### [C-34] GMM-Vol-Regime + Variance Risk Premium (G3-Gate) *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 Q17
- **Zielmarkt laut Quelle:** Futures (Perpetual); Optionen (VRP-Kanal)
- **Kernidee:** GMM-Clustering auf RV-Feature-Vektoren (Level, Persistenz, Term-Struktur, Semivarianzen) → 4–6 diskrete Vol-Regime. VRP = IV² − realisierte Varianz als Forward-Looking-Dimension. G3-Zustandsmaschine: Strategie-Familien regime-bedingt freischalten (Carry nur Range, Kaskaden-Fade nur Stress). Doppelfunktion in L3 (Gate) und L5 (Sizing).
- **Kernannahme(n):** GMM-Cluster sind über 24h hinweg persistent (kein Flattern); VRP-Schätzung verbessert Regime-Trennung gegenüber RV allein; Options-Kette liefert verlässliches ATM-markIv (kein IV-Archiv → Aufzeichnungs-Vorlauf nötig).
- **Behaupteter Nutzen:** Regime-Persistenz median ≥ 24 h; VRP-Kanal ΔR² ≥ +0.02 im Vol-Stack; G3-Sizing Sharpe ≥ +0.2 absolut gegenüber statischem Sizing.
- **Validierungs-Gate:** Persistenz ≥ 24 h + ΔR² ≥ +0.02 + Sharpe +0.2. Abbruch: VRP ohne ΔR² → RV-only; dann Fallback Q10 (NHHM).
- **Abhängigkeiten:** Q4 (C-18) gegenseitig; Phase-0-IV-Aufzeichnung (≥ 3 Monate Vorlauf für VRP); historical-volatility REST (2 J.)
- **Reifegrad laut Quelle:** Spezifiziert; kein IV-Archiv → erst nach Aufzeichnungs-Vorlauf vollständig testbar

---

### [C-35] CEEMDAN-Dekomposition streng kausal *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 Q16
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Rauschstabilisierte EMD zerlegt RV-/Premium-Index-Reihen in Intrinsic Mode Functions (IMF). Energie-Shift Richtung Hochfrequenz = Stress-Indikator; niederfrequente IMFs = entrauschte Inputs für Vol-Stack. Kritisch: NUR streng kausale Online-Variante (naive EMD ist Lookahead-behaftet).
- **Kernannahme(n):** Kausal-kausale Online-CEEMDAN vermeidet Lookahead vollständig; IMF-Energie-Features liefern inkrementellen Beitrag über Standard-Features hinaus (ΔR² > 0); Randbehandlung ist dokumentiert und reproduzierbar.
- **Behaupteter Nutzen:** Kausalitäts-Nachweis (bit-für-bit Reproduktion) + inkrementelles ΔR² ≥ +0.01 im Q4-Vol-Stack.
- **Validierungs-Gate:** Kausalitäts-Nachweis + ΔR² ≥ +0.01. Abbruch: ΔR² ≤ 0 oder Kausalitäts-Nachweis scheitert.
- **Abhängigkeiten:** Q4 (C-18) als Abnehmer; REST Kline, premium-index-price-kline
- **Reifegrad laut Quelle:** Spezifiziert; als bedingte Methode (Kausalitäts-Pflichtnachweis) geführt

---

### [C-36] F0 Fallback-Schwellwert-Trigger (Pflicht-Ingestion-Gate) *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 F0
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Deterministisches Regelwerk mit vier Anomalie-Bedingungen: Liq-Volumen(1min) > P99 ODER |dOI(1min)| > P99 ODER |dPremiumIndex(1min)| > P98 ODER RV(1min) > P98. Trivial, testbar, regime-neutral. Dauerhaftes Schatten-Gate zur Überwachung von C-02 (SpikeWavformer). Pflichtbaustein ab Tag 1.
- **Kernannahme(n):** 30-Tage-Rolling-Perzentile aus Trainingsfenstern sind stabil; vier Bedingungen decken relevante Großevents vollständig ab; ≤ 5 Fehl-Trigger/Tag/Symbol ist operationell akzeptabel.
- **Behaupteter Nutzen:** Recall ≥ 95 % auf gelabelten Großevents; ≤ 5 Fehl-Trigger/Tag/Symbol.
- **Validierungs-Gate:** Recall ≥ 95 % (kein Abbruch — Pflichtbaustein, nur Schwellen-Re-Kalibrierung).
- **Abhängigkeiten:** Recording-Infrastruktur (Phase 0); tickers WS, allLiquidation WS
- **Reifegrad laut Quelle:** Neu spezifiziert (nicht im bestehenden Repo); Aufwand 2–3 Tage

---

### [C-37] Basis/Carry über den Spread-Markt (Execution-Schiene) *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 Q5
- **Zielmarkt laut Quelle:** Futures (Perpetual) — Spot/Perp-Basis
- **Kernidee:** Bybit quotiert Spreads als eigenständigen handelbaren Markt mit eigenem Orderbuch (/v5/spread/*) → delta-neutrale Basis-Trades mit Maker-Execution (4 bp Roundtrip statt 11 bp, kein Leg-Risk). Primär Execution-Schiene für K2-Funding-Uhr. Basis-z-Score als Konvergenz-Signal.
- **Kernannahme(n):** Bybit-Spread-Markt hat ausreichend Liquidität (Spread-Buch-Tiefe ≥ Ordergröße in > 70 % der Fenster); Premium-Index-Kline ist valider Backtest-Proxy (kein Spread-Archiv); annualisierter Carry + erwartete Funding-Summe ist prognostizierbar.
- **Behaupteter Nutzen:** Delta-neutraler Carry: Sharpe ≥ 1.5, Max-DD < 10 %; Konvergenz-Trade: Win-Rate ≥ 60 % bei |z| > 2; Maker-Quote ≥ 70 % der K2-Orders.
- **Validierungs-Gate:** Sharpe ≥ 1.5; Win-Rate ≥ 60 %; Maker-Quote ≥ 70 %. Abbruch: Spread-Buch-Tiefe < Ordergröße in > 30 % der Fenster → Zwei-Bein-Fallback.
- **Abhängigkeiten:** Q1 (C-22, Signalgeber); Phase-0-Spread-Aufzeichnung; /v5/spread/*-Endpoints (kein Archiv)
- **Reifegrad laut Quelle:** Neu spezifiziert; Spread-Markt kein Archiv → Proxy-Backtest + Live-Validation

---

### [C-38] TFT mit Known-Future-Funding *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 Q9
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Temporal Fusion Transformer trennt architektonisch beobachtete Vergangenheit von BEKANNTER Zukunft. Funding-Settlement-Raster (nextFundingTime, τ-bis-Settlement, Funding-Vorzeichen) ist deterministisch bekannte Zukunft → bisher von publizierter Krypto-DL-Literatur nicht genutzt. Quantil-Output (P10/P50/P90) dient direkt L5-Stops.
- **Kernannahme(n):** Known-Future-Funding-Features liefern inkrementellen Uplift über Q1-Regelwerk hinaus; Quantil-Kalibrierung ist verlässlich; TFT auf Hidden-Size 64–256 ist auf RTX 5060 Ti trainierbar; nur als K2-Verstärker nach Q1-Live-Proof.
- **Behaupteter Nutzen:** Quantil-Kalibrierung: empirische Coverage-Abweichung < 2 pp; Richtungs-AUC > 0.55 im Settlement-Fenster ODER RV-R² > 0.25; K2-Uplift: Sharpe ≥ +0.3 gegenüber Q1 allein.
- **Validierungs-Gate:** Sharpe +0.3 Uplift (hartes Gate); kein Uplift nach 2 Trainings-Iterationen → Q9 entfällt.
- **Abhängigkeiten:** Q1 (C-22) muss live profitabel sein; Feature-Bus; Q7/Q11; RTX 5060 Ti
- **Reifegrad laut Quelle:** Neu spezifiziert; DL-Komplexitätsfalle für Solo-Entwickler (nachgelagert, Phase 4)

---

### [C-39] Liquidations-Kaskaden-Anatomie (Bankruptcy-Preis + Insurance + ADL) *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 Q2
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Bybit pusht ALLE Liquidationen inkl. Bankruptcy-Preis: implizierter Hebel der Kohorte aus |1 − p_bankruptcy/p_mark|. Insurance-Pool-Delta = Abfluss → Fill schlechter als Bankruptcy → echte Illiquidität. ADL-`pr` = plattformweiter Stress-Score. Dreigleisige Risk-Off-Ampel. Erweiterung von C-26 (SIR) um Bybit-exklusive Datenströme ohne REST-Archiv.
- **Kernannahme(n):** Bankruptcy-Preis ist im allLiquidation-Feed zuverlässig befüllt; Insurance-Delta und ADL-pr sind valide Proxies für Systemstress; alle drei Ströme haben keine REST-Historie → Aufzeichnung unabdingbar.
- **Behaupteter Nutzen:** Kaskaden-Recall ≥ 90 %; Risk-Off: Max-DD-Reduktion ≥ 25 %; Erschöpfungs-Entry Win-Rate ≥ 58 %.
- **Validierungs-Gate:** Recall ≥ 90 %. Abbruch: Recall < 70 % → nur F0-artige Grobampel.
- **Abhängigkeiten:** Phase-0-Aufzeichnung (allLiquidation + insurance.USDT + adlAlert.{coin}); Q7/Q11 als Brennstoff-Features; kein REST-Archiv für Insurance/ADL
- **Reifegrad laut Quelle:** Neu spezifiziert; Quick Win (Live-Score ab 1 Woche nach Aufzeichnung), volle Backtests erst nach Vorlauf

---

### [C-40] RPI-/Iceberg-Hidden-Liquidity-Karte (Bybit-Exklusivum) *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 Q14
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Bybit-RPI-Orders sind im Normalbuch UNSICHTBAR, im separaten RPI-Buch SICHTBAR. Differenz beider Bücher + isRPITrade-Flags = direkt beobachtbare Hidden-Liquidity-Karte ohne statistische Inferenz. First-Mover-Datensatz — nirgends in der Literatur genutzt. Kombiniert mit Eisberg-Replenishment-Detektion (vgl. C-03).
- **Kernannahme(n):** RPI-Buch ist öffentlich zugänglich und hat ausreichende Tiefe; Differenz RPI/Normal-Buch ist stabil genug für S/R-Zonen; Edge verfällt, sobald RPI-Analyse populär wird.
- **Behaupteter Nutzen:** Eisberg-/RPI-Level als S/R: Halte-Quote ≥ 65 % auf 30-min-Horizont (vs. ≤ 50 % Zufalls-Level); Stop-Slippage-Reduktion ≥ 10 % in K1–K3.
- **Validierungs-Gate:** Halte-Quote ≥ 65 % über 3 Monate Daten. Abbruch: keine Diskriminierung.
- **Abhängigkeiten:** Phase-0-Aufzeichnung (orderbook.rpi); orderbook.50 (20 ms) + publicTrade; doppelter Buch-Rekonstruktor
- **Reifegrad laut Quelle:** Neu spezifiziert; Moonshot #2; kein Archiv → nur auf Eigenaufzeichnung

---

### [C-41] Cross-Asset Wavelet Coherence (Lead-Lag, K3-Achse 2) *(NEU: PRD-kestrel)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §4 S11
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** Kohärenzanalyse (Morlet-CWT, Cross-Wavelet-Power) misst in welchem Frequenzband und mit welcher Phasendifferenz zwei Assets synchronisiert sind → frequenzaufgelöste Phasenführung. Komplementär zu C-17 (Transfer-Entropy) als K3-Achse 2.
- **Kernannahme(n):** Morlet-CWT liefert stabile Kohärenz-Schätzungen bei rollierenden Fenstern; Phasenstabilität ≥ 80 % des Fensters ist notwendige Bedingung für handelbare Kanten; Cone-of-Influence korrekt behandelt.
- **Behaupteter Nutzen:** Bedingte Richtungs-AUC > 0.55 in G1-Fenstern auf Konsens-Kanten (≥ 2/3 Achsen); Phasen-Stabilität ≥ 80 %.
- **Validierungs-Gate:** Konsens-Kanten AUC > 0.55; Phasen-Stabilität ≥ 80 %. Abbruch: wie S3/K3.
- **Abhängigkeiten:** Multi-Asset-Sync-Strom; pycwt; publicTrade/tickers
- **Reifegrad laut Quelle:** Neu spezifiziert (Aufwand 1–2 Wochen)

---

### [C-42] Volatilitäts-Prognose-Baseline (LightGBM/HAR-RV) *(Erfahrungsbericht)*
- **Quelle:** research_notes.md §Empirical results (Kestrel-v1.4)
- **Zielmarkt laut Quelle:** Futures (Perpetual)
- **Kernidee:** LightGBM-Regression auf 36-Feature-Snapshot (1-min Bars, MODWT Wavelets, Funding/OI, Cross-Venue-Features) prognostiziert log(realised_vol_60m). Test-R² = 0.249, Pearson = 0.578 — der einzige deployable predictive signal im Kestrel-v1.4-Codebase.
- **Kernannahme(n):** Volatilitäts-Clustering ist persistent und durch Standard-Features erfassbar; Modell verallgemeinert auf Out-of-Sample (Apr 2026 Test nach Jan–Mar Training); Feature-Wichtigkeit: atr_60 (35.8 %) und Trade-Flow-Features (38 %).
- **Behaupteter Nutzen:** Vol-Forecasting R² ≈ 0.25 OOS — etablierte Baseline; verwendbar als Risk Gauge, Position Sizing, Stop-Loss-Kalibrierung. NICHT als Richtungssignal.
- **Validierungs-Gate:** R² > 0.25 auf OOS-Test (bestanden); Baseline-Referenz für alle nachfolgenden Vol-Modelle.
- **Abhängigkeiten:** 1-min Kline + MODWT + Funding/OI/Cross-Venue; vollständige Feature-Pipeline (Kestrel-v1.4 Codebase)
- **Reifegrad laut Quelle:** Getestet / deployed-ready (vollständige Kestrel-v1.4 Pipeline)

---

### [C-43] Konforme Prädikation als Querschnitts-Kalibrator (M-Q17) *(NEU: PRD-fable5)*
- **Quelle:** FINAL_PRD-fable5.md §5, §7 (Querschnitts-L4)
- **Zielmarkt laut Quelle:** Futures (Perpetual) / unspezifiziert
- **Kernidee:** Conformal Prediction liefert verteilungsfreies Konfidenzband über L3-Signale → Sizing nur bei engem Intervall. Kein Alpha-Generator. 90%-Intervall deckt ≥ 85 % der OOS-Fälle (CP-Gate).
- **Kernannahme(n):** Exchangeability-Annahme der Conformal Prediction ist auf rollierende Finanzdaten ausreichend; enge Coverage-Intervalle korrelieren mit höherer Treffsicherheit.
- **Behaupteter Nutzen:** 90%-Intervall deckt ≥ 85 % der OOS-Fälle (CP-Gate); als universeller Sizing-Kalibrator über alle L3-Signale.
- **Validierungs-Gate:** Coverage ≥ 85 % OOS.
- **Abhängigkeiten:** Alle L3-Signale (C-06, C-07, C-08, C-27, C-28, C-29, C-30 je nach Strategie)
- **Reifegrad laut Quelle:** Spezifiziert (nicht im bestehenden Repo implementiert)

---

## Teil II — Strategie-Claims (Kombinationen mehrerer Module)

---

### [CS-01] „Seismischer Cascade Detector" (S1/PRD-v1)
- **Quelle:** FINAL_PRD.md §7.1
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-14 (Hawkes ρ), C-15 (GR+Omori), C-26 (SIR R₀), implizit C-25 (Kyle-λ als Sizing)
- **Logik:** ρ > 0.85 (steigend) AND b < b̄_30d−2σ AND Omori aktiv AND R₀ > 1 → Mean-Reversion-Entry gegen Liquidations-Seite
- **Validierungs-Gate:** Sharpe ≥ 1.5; Hit-Rate ≥ 56 %; Max-DD < 10 %
- **Reifegrad:** Implementiert (strategy1_cascade.py); 0 Trades in iter-3 (ρ-Schwelle nie erreicht)

---

### [CS-02] „Entropie-Momentum" (S2/PRD-v1)
- **Quelle:** FINAL_PRD.md §7.2
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-06 (Shannon-Entropie), C-01 (OFI), C-22 (Funding-Clamp), C-07 (PE)
- **Logik:** Entropie-Kollaps AND OFI > Q90 AND sign(Funding-Pressure) == sign(OFI) AND PE < Median → Folge institutioneller Aggression
- **Validierungs-Gate:** Sharpe ≥ 1.0; Hit-Rate ≥ 53 %
- **Reifegrad:** Implementiert (strategy2_entropy_momentum.py); empirisch refutiert: 6–8 % Hit-Rate auf BTC/ETH (anti-Signal), drei forensische Tests negativ

---

### [CS-03] „Pre-Settlement Pressure-Release" (S3/PRD-v1)
- **Quelle:** FINAL_PRD.md §7.3
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-22 (Funding-Clamp), C-23 (Basis Convergence), C-24 (Kalman Premium), C-08 (BOCPD)
- **Logik:** T_settlement − t < 30 min AND |Pressure| > Q90 AND Basis-Richtung = Pressure-Richtung AND BOCPD kein Change-Point → Timing-präziser Bet auf Pressure-Release
- **Validierungs-Gate:** Sharpe ≥ 1.5; Hit-Rate ≥ 56 %; Max-DD < 10 %
- **Reifegrad:** Implementiert (strategy3_pre_settlement.py); empirisch: Entry-Thesis intakt, Exit unzureichend (fehlendes Bounded-Loss); iter-4 mit Time-Stop+Hard-Stop; iter-5 Fixes pending

---

### [CS-04] „Pattern × Foundation Ensemble" (S4/PRD-v1)
- **Quelle:** FINAL_PRD.md §7.4
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-05 (FFD), C-16 (TFSAX+SW), C-20 (MOMENT), C-18 (PatchTST)
- **Logik:** ≥ 2 von 3 Modellen gleichgerichtet > 0.5 % in h ∈ {15min, 1h, 4h} AND Pairwise-Pearson > 0.6 AND TFSAX-Match > 0.75
- **Validierungs-Gate:** Sharpe ≥ 1.2; Hit-Rate ≥ 56 %
- **Reifegrad:** Implementiert (strategy4_pattern_ensemble.py); UNTESTBAR — `insufficient_models` 96–99.99 % (Modell-Loader nicht verdrahtet)

---

### [CS-05] „Cross-Sectional Ergodicity Reversion" (S5/PRD-v1)
- **Quelle:** FINAL_PRD.md §7.5
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-13 (Cross-Sectional-Z), C-17 (Renyi-TE), C-09 (HMM)
- **Logik:** |z| > 2.5 AND Renyi-TE(BTC→Alt) > 0.05 AND HMM-State ≠ Crash → Mean-Reversion gegen Z
- **Validierungs-Gate:** Sharpe ≥ 1.0; Hit-Rate ≥ 53 %
- **Reifegrad:** Implementiert (strategy5_cross_sectional.py); UNTESTBAR — Harness-blockiert (`single_symbol_replay_unsupported` 100 %)

---

### [CS-06] „Epidemiologisches Kaskaden-Cockpit" (Strategie A / PRD-fable5) *(NEU)*
- **Quelle:** FINAL_PRD-fable5.md §5
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-27 (Cori-Rₜ), C-28 (NB-k), C-29 (Shape Collapse), C-43 (Conformal Prediction)
- **Logik:** allLiquidation → Rₜ + NB-k + Restdauer → gemeinsames Kaskaden-Risiko-Gate → CP-Sizing/Exit
- **Schwächste Annahme:** Stabiles Generationszeit-Fenster ω_s über Regime (korrelierter Fehler C-27+C-28)
- **Validierungs-Gate:** Per Einzel-Methoden-Gate (BA ≥ 0.55, Lift ≥ 1.2, Residual ≤ 30 %)
- **Reifegrad laut Quelle:** Idee/spezifiziert (nicht implementiert)

---

### [CS-07] „Algorithmischer Footprint-Detektor" (Strategie B / PRD-fable5) *(NEU)*
- **Quelle:** FINAL_PRD-fable5.md §5
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-16 (M-S23 SW/Profil-HMM auf Orderflow), C-31 (Cyclic Spectrum), C-43 (CP)
- **Logik:** publicTrade-Symbolisierung → SW-Alignment PARALLEL Cyclic-Spectrum → Konsens-Filter → CP-Sizing
- **Schwächste Annahme:** Algorithmische Muster persistieren; Sekunden-Horizont über Fee-Schwelle
- **Validierungs-Gate:** BA ≥ 0.55 + Surrogate p < 0.05 (beide Detektoren)
- **Reifegrad laut Quelle:** Idee/spezifiziert

---

### [CS-08] „Regime-konditioniertes Richtungs-Signal" (Strategie C / PRD-fable5) *(NEU)*
- **Quelle:** FINAL_PRD-fable5.md §5
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-07 (PE, Funding-Regime), C-08 (BOCPD/OI-Strukturbruch), C-01 (OBI), C-32 (Funding-Contrarian), C-21 (L/S-Ratio), C-43 (CP)
- **Logik:** Regime-Gate (PE+BOCPD) → gefilterte Signale (OBI+Contrarian+L/S) → CP-Sizing
- **Schwächste Annahme:** Detektiertes Regime ist zum Handelszeitpunkt noch gültig
- **Validierungs-Gate:** Je Einzel-Methoden-Gate
- **Reifegrad laut Quelle:** Idee/spezifiziert

---

### [CS-09] „Topologisch-direktionaler Options-Block" (Strategie D / PRD-fable5) *(NEU)*
- **Quelle:** FINAL_PRD-fable5.md §5
- **Zielmarkt:** **Optionen + Futures (kombiniert)**
- **besteht_aus:** C-11 (PH-Bruch IV-Surface, M-S17), IV-Skew-Dynamik (M-Q15, zurückgestellt), C-33 (VRP Short-Vola), C-43 (CP)
- **Logik:** IV-Surface PH-Bruch + 25Δ-Skew → konditioniert VRP-Short-Vola + CP
- **Schwächste Annahme:** Bybit-Options-Liquidität reicht (60–80 % der Stunden fällt Liquiditäts-Check durch)
- **Validierungs-Gate:** (IV−RV) ≥ 3 %; Precision@k ≥ 1.2×
- **Reifegrad laut Quelle:** Idee/spezifiziert

---

### [CS-10] „Cross-Coin-Contagion-Lead" (Strategie E / PRD-fable5) *(NEU)*
- **Quelle:** FINAL_PRD-fable5.md §5
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** M-S16 (Convergent Cross Mapping, zurückgestellt), C-27 (Rₜ), C-28 (NB-k), C-43 (CP)
- **Logik:** Multi-Symbol allLiquidation → CCM-Kopplungsrichtung → Follower-Coin → Rₜ+NB-k
- **Schwächste Annahme:** CCM-Takens-Einbettung für verrauschte Multi-Coin-Ströme; Lead-Lag > 50 ms
- **Validierungs-Gate:** Per Einzel-Methoden-Gate
- **Reifegrad laut Quelle:** Optional/Idee (CCM-Analogie gestreckt laut Critic)

---

### [CS-11] „Seismograph" / Kaskaden-Lebenszyklus-Trader (K1 / PRD-kestrel) *(NEU)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §7 K1
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-14 (S2/Hawkes-rho), C-39 (Q2/Kaskaden-Anatomie), C-15 (S4/Omori-Timing); Features C-05/C-21 (Brennstoff-Index); Veto C-25 (VPIN); Sizing C-18 (Q4-RV)
- **Logik:** rho(G) → 1 AND Brennstoff-Index hoch → Risk-Off-Bereitschaft (VOR Kaskade). Laufende Kaskade → kein Entry. Nachbebenphase (Omori-Rate < Schwelle AND Erschöpfung) → Reversion-Entry
- **Validierungs-Gate:** Win-Rate ≥ 58 %, Sharpe ≥ 1.0 über ≥ 30 Kaskaden-Events (Event-CV)
- **Reifegrad laut Quelle:** Spezifiziert; Kern-Daten erst nach 3+ Monaten Aufzeichnung

---

### [CS-12] „Funding-Uhr" / Settlement-Fenster-Harvester (K2 / PRD-kestrel) *(NEU)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §7 K2
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-22 (Q1/Clamp-Stau D_t×τ), C-38 (Q9/TFT, optional), C-37 (Q5/Spread-Execution); Gate C-08 (G2-BOCPD); Veto C-25 (VPIN)
- **Logik:** |D_t| > P90 AND Q9-P50 gleichgerichtet (sofern aktiv) AND kein Funding-Regime-Bruch AND VPIN < P95 → Maker-Execution über Spread-Markt
- **Validierungs-Gate:** Sharpe ≥ 1.2, Win-Rate ≥ 55 %, ≥ 200 Trades walk-forward
- **Reifegrad laut Quelle:** Spezifiziert; K2 als erste live-testbare Version ab Woche 10–13

---

### [CS-13] „Rudel-Läufer" / Lead-Lag-Follower-Rotation (K3 / PRD-kestrel) *(NEU)*
- **Quelle:** FINAL_PRD-kestrel-basis.md §7 K3
- **Zielmarkt:** Futures (Perpetual)
- **besteht_aus:** C-17 (S3/Transfer-Entropy), C-41 (S11/Wavelet-Coherence), C-01 (Q3/Multi-Level-OFI); Flag C-13 (S1/Ergodizitäts-Defekt); Gate C-06/C-07 (G1); Veto C-25
- **Logik:** Konsens-Graph (≥ 2/3 Achsen) → handelbare Kanten; Leader-Move > Schwelle AND Lag-Fenster aktiv AND G1 grün AND S1-Flag AND VPIN < P95
- **Validierungs-Gate:** Bedingte AUC > 0.55, Sharpe ≥ 0.8, FDR-korrigiert
- **Reifegrad laut Quelle:** Spezifiziert

---

## Teil III — Vorab-Urteile (Sekundär-Quellen, P-xx)

*(Registrierung ohne Wertung; eigene Bewertung erfolgt in Phase 5 unabhängig)*

### [P-01] STRATEGY_CONCEPT_REVIEW_iter3.md
- **Quelle:** `input/STRATEGY_CONCEPT_REVIEW_iter3.md`
- **Scope:** Konzeptuelle Überprüfung S1–S5 gegen iter-3-Daten (Original-Arm)
- **Urteile je Strategie:**
  - CS-01 (S1): UNTESTABLE — ρ-Threshold-Problem, nicht Daten-Problem
  - CS-02 (S2): BROKEN — thesis inverted; Entropie-Kollaps = Mean-Reversion-Signal, nicht Momentum
  - CS-03 (S3): CONFIRMED (entry) / BROKEN (exit) — fehlendes Bounded-Loss-Konzept
  - CS-04 (S4): UNTESTABLE — architecture-bound (model loader)
  - CS-05 (S5): UNTESTABLE — harness-bound (panel replayer)
- **Betroffene Claims:** C-14 (ρ-Instrument), C-22 (Pressure-Entry), alle CS-01 bis CS-05

### [P-02] PRD_VS_REALITY_SYNTHESIS.md
- **Quelle:** `input/PRD_VS_REALITY_SYNTHESIS.md`
- **Scope:** 3 Replay-Iterationen (iter-3 baseline + inverted, iter-4 drei Flags), iter-5 pending
- **Urteile je Strategie:**
  - CS-01 (S1): **ABANDON** (aktuelle M14-Implementierung) — ρ-Median ~2e-7, Threshold 6 Größenordnungen entfernt
  - CS-02 (S2): **ABANDON** — drei unabhängige Forensiken (Richtung, Spiegel, Maker-Only) alle negativ
  - CS-03 (S3): **PROMISING** (pending iter-5) → wahrscheinlich MODIFY
  - CS-04 (S4): **UNTESTED** — Modell-Loader nicht verdrahtet
  - CS-05 (S5): **UNTESTED** — Panel-Harness fehlt
- **Modul-Urteile:** C-14 (M14): ABANDON in aktueller Form; C-01 (M2 OFI): SUSPECT; C-22 (M22): NEEDS INSTRUMENTATION; C-08 (M8 BOCPD): NEEDS INSTRUMENTATION
- **Systemische Befunde:** Fehlende Bounded-Loss-Policy; Richtungs-Bias 100 % Long in S2/S3 (window-spezifisch oder strukturell?); Friction-vs-Holding-Horizon-Constraint fehlend im PRD

---

## Teil IV — Inkonsistenzen zwischen Quellen

### INC-01: Hawkes-Spektralradius ρ — Threshold-Kollision
- **Konflikt:** PRD-v1 setzt ρ > 0.85 als Gate (aus Bacry-Mastromatteo-Muzy 2015 importiert). Empirische Messung (iter-4): ρ-Median ≈ 2e-7 auf BTC/ETH; p95 ≈ 1e-3; p99 ≈ 1e-3. Threshold liegt 6 Größenordnungen über dem Median. PRD-kestrel übernimmt denselben Ansatz (S2), empfiehlt aber Branching-Ratio-Approximation als risikoarmen Start.
- **Konsequenz:** C-14/CS-01 sind in ihrer aktuellen Form nicht testbar; Threshold wurde aus anderer Mikrostruktur-Umgebung übernommen.

### INC-02: OFI-Vorzeichen-Interpretation — PRD-v1 vs. empirische Beobachtung
- **Konflikt:** PRD-v1 (CS-02, S2): „OFI markiert institutionelle Aggression, folge ihr." Empirisch: 6–8 % Hit-Rate (CS-02, drei Forensiken) — OFI markiert MM-Replenishment, das sofort gefadet wird. PRD-kestrel nennt OFI (Q3) als Feature-Input, nicht als Direktionssignal.
- **Konsequenz:** C-01 (M2 OFI) als Direktionssignal ist suspect; als Feature in anderen Modulen (C-09 HMM, C-14 Hawkes) möglicherweise ebenfalls falsch orientiert.

### INC-03: S3-Funding-Pressure Trigger-Rate
- **Konflikt:** PRD-v1 §7.3 beschreibt S3 als „Settlement-Window-Trade" (3 Settlements/Tag/Symbol). Empirisch feuert S3 50–60 Trades/24h/Symbol — weit mehr als Settlement-Framing impliziert.
- **Konsequenz:** C-22 M22-Threshold |Pressure| > Q90 wird über-getriggert; Q90 entspricht möglicherweise nicht Settlement-Qualitätsniveau.

### INC-04: Zielmarkt-Erweiterung PRD-fable5 vs. PRD-v1
- **Konflikt:** PRD-v1 adressiert ausschließlich Futures (Perpetuals). PRD-fable5 fügt erstmals explizit **Optionen** (C-33, M-Q14; CS-09, Strategie D) und die Option-IV-Surface als Input (C-11 M-S17) hinzu. PRD-kestrel integriert Options-IV als G3-Kanal (C-34 Q17) ohne eigenständige Options-Strategie.
- **Konsequenz:** Der Options-Markt als Zielmarkt ist neu und in keinem Dokument vollständig durchdacht (Liquiditätsbeschränkung explizit als größtes Risiko genannt).

### INC-05: Richtungs-Prognose-Grundhaltung
- **Konflikt:** PRD-v1 enthält mehrere Module mit direktionalen Prognose-Ansprüchen (M9 HMM, M18 PatchTST ≥ 55 % Direktional-Accuracy). Kestrel-v1.4-Erfahrungsbericht (research_notes): Richtungsprognose AUC ≈ 0.50 (Münzwurf) auf 1h/4h-Horizont mit klassischen Features. PRD-fable5 und PRD-kestrel übernehmen diese Baseline explizit als Nullhypothese; direktionale Claims nur regime-konditioniert (bedingte AUC > 0.55).
- **Konsequenz:** Alle unkonditional-direktionalen Claims in PRD-v1 (M9, M16, M18, M20, M21) stehen unter Revisionsdruck; Validierungs-Gates in PRD-v1 wurden vermutlich ohne Berücksichtigung der empirischen Baseline formuliert.

### INC-06: Endpoint-Korrektheit
- **Konflikt:** PRD-v1 nennt `orderbook.500` als WebSocket-Topic. PRD-kestrel korrigiert explizit: WS `orderbook.500` existiert NICHT (L1=10ms, L50=20ms, L200=100ms, L1000=200ms). Nur ob500-Snapshots als Download verfügbar.
- **Konsequenz:** Methoden in PRD-v1, die implizit 500-Level-WS-Daten voraussetzen, müssen auf orderbook.200 (100 ms) oder orderbook.1000 (200 ms) umgestellt werden.

---

## Teil V — ID-Mapping-Tabelle

| Kanonisch (C-xx / CS-xx) | PRD-v1 (FINAL_PRD.md) | PRD-fable5 (FINAL_PRD-fable5.md) | PRD-kestrel (FINAL_PRD-kestrel-basis.md) | research_notes.md |
|---|---|---|---|---|
| C-01 | M2 (OFI CKS) | M-Q11 | Q3 (Multi-Level OFI, Cross-Asset) | — |
| C-02 | M1 (SpikeWavformer) | — | S7 (SpikeWavformer) | — |
| C-03 | M3 (Iceberg-Detection) | — | — (vgl. Q14 C-40) | — |
| C-04 | M4 (Wavelet-Denoising) | — | S12 (Symlet-Spoof-Detektor, verwandt) | — |
| C-05 | M5 (FFD) | — | Q7 (FracDiff-Zustand, verwandt) | — |
| C-06 | M6 (Shannon-Entropie) | — | S9 (KL-Divergenz-Kollaps, verwandt) | — |
| C-07 | M7 (Permutation Entropy) | — | Q12 (PE, Cross-Sectional) | — |
| C-08 | M8 (BOCPD auf OI) | M-Q16 (OI-CUSUM, verwandt, zurückgestellt) | Q8 (BOCPD auf RV/Funding/OI/Basis) | — |
| C-09 | M9 (HMM 3-State) | — | — (NHHM Q10 zurückgestellt als Fallback) | Q10 NHHM als open follow-up |
| C-10 | M10 (MF-DFA) | — | Q15 (MF-DFA/Hölder) | — |
| C-11 | M11 (TDA/PH) | M-S17 (PH auf OB/IV-Surface) | — | — |
| C-12 | M12 (RQA) | — | — | — |
| C-13 | M13 (Cross-Sectional-Z) | — | S1 (Ergodizitäts-Defekt-Flag, verwandt) | — |
| C-14 | M14 (Hawkes ρ(Φ) 6-D) | M-Q13 (Hawkes-Baseline, zurückgestellt) | S2 (Hawkes-Spektralradius, Branching-Approx) | — |
| C-15 | M15 (GR+Omori) | M-S12 (AE improved b-value, zurückgestellt) | S4 (Omori-Timing) | — |
| C-16 | M16 (TFSAX+SW auf Preis) | M-S23 (SW+Profil-HMM auf Orderflow) | S5 (TFSAX+SW, hartes Gate) | — |
| C-17 | M17 (Renyi-TE) | M-S16 (CCM, zurückgestellt) | S3 (Transfer-Entropy) | — |
| C-18 | M18 (PatchTST funding) | — | Q4 (PatchTST RV, strategisch zentral) | LightGBM-Vol-Prognose (analog) |
| C-19 | M19 (TimesNet) | — | Q13 (zurückgestellt) | — |
| C-20 | M20 (MOMENT Zero-Shot) | — | — | — |
| C-21 | M21 (L/S-Ratio Divergenz) | M-Q18 (L/S-Extremwert, zurückgestellt) | Q11 (L/S-Crowding, nur Feature) | — |
| C-22 | M22 (Funding-Clamp Pressure) | M-Q12 (Funding-Contrarian, verwandt) | Q1 (Funding-Zyklus/Premium-Druck, erweitert) | — |
| C-23 | M23 (Mark-Index Basis) | — | (in Q1/Q5 integriert) | — |
| C-24 | M24 (Kalman-Premium) | — | (in Q1 integriert) | — |
| C-25 | M25 (Kyle's Lambda) | — | Q6 (VPIN+Kyle-λ, Taker-Side-verfeinert) | — |
| C-26 | M26 (SIR Contagion R₀) | (Backbone in M-S21/M-S22) | Q2 (Kaskaden-Anatomie, Bybit-exklusiv-erweitert) | — |
| C-27 | — | M-S21 (Cori-Rₜ Renewal) | — | — |
| C-28 | — | M-S22 (NB-k Superspreading) | — | — |
| C-29 | — | M-S13 (Avalanche Shape Collapse) | — | — |
| C-30 | — | M-S11 (Natural Time κ₁) | — | — |
| C-31 | — | M-S14 (Cyclic Spectrum CFAR) | — | — |
| C-32 | — | M-Q12 (Funding Contrarian) | — | — |
| C-33 | — | M-Q14 (VRP Short-Vola Options) | — | — |
| C-34 | — | (M-Q17 VRP+GMM verwandt) | Q17 (GMM-Vol-Regime+VRP) | — |
| C-35 | — | — | Q16 (CEEMDAN kausal) | — |
| C-36 | — | — | F0 (Fallback-Trigger) | — |
| C-37 | — | — | Q5 (Basis/Spread-Markt) | — |
| C-38 | — | — | Q9 (TFT Known-Future) | — |
| C-39 | M26 (SIR, Basis) | M-S21/22 (Basis) | Q2 (Kaskaden-Anatomie, erweitert) | — |
| C-40 | M3 (Iceberg, Basis) | — | Q14 (RPI-Hidden-Liquidity) | — |
| C-41 | — | — | S11 (Wavelet Coherence) | — |
| C-42 | — | — | — | LightGBM-Vol-Baseline |
| C-43 | — | M-Q17 (Conformal Prediction) | — | — |
| CS-01 | S1 (Seismischer Cascade) | — | K1 (Seismograph, verwandt) | — |
| CS-02 | S2 (Entropie-Momentum) | — | — | — |
| CS-03 | S3 (Pre-Settlement) | — | K2 (Funding-Uhr, verwandt) | — |
| CS-04 | S4 (Pattern Ensemble) | — | — | — |
| CS-05 | S5 (Cross-Sectional Rev.) | — | K3 (Rudel-Läufer, verwandt) | — |
| CS-06 | — | Strategie A (Kaskaden-Cockpit) | — | — |
| CS-07 | — | Strategie B (Footprint-Detektor) | — | — |
| CS-08 | — | Strategie C (Regime-Signal) | — | — |
| CS-09 | — | Strategie D (Options-Block) | — | — |
| CS-10 | — | Strategie E (Cross-Coin-Contagion) | — | — |
| CS-11 | — | — | K1 (Seismograph) | — |
| CS-12 | — | — | K2 (Funding-Uhr) | — |
| CS-13 | — | — | K3 (Rudel-Läufer) | — |

---

*Ende claims_register.md*
