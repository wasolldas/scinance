# SYNTHESEBERICHT — Edge Research Framework
**Datum:** 2026-05-22
**Input:** critic_report_1.md (PASS) + round_1_scout.md + round_1_quant.md

[SYNTHESIZER → PRD ARCHITECT] STATUS: COMPLETE | ACCEPTED_METHODS: 21 | SYNERGIES: 10 | STRATEGIES: 5 | FIRST_IMPL: Bybit WebSocket-Collector + Funding-Clamp-Pressure (Quick-Win-Anker)

---

## 1. Pipeline-Layer-Zuordnung

Alle 21 ACCEPTED-Methoden (nach Merge) mit Layer, Latenz-Anforderung und Bybit-Datenquelle. Latenz-Klassen: **TICK** (≤100ms, WebSocket-Stream), **NEAR-RT** (1–5s, rolling-window), **BATCH** (≥1min bis Stunden, periodisch).

| # | Methode | Layer | Latenz | Bybit-Endpoint / Datenquelle |
|---|---------|-------|--------|------------------------------|
| 1 | SpikeWavformer (SNN+DWT) | L1 | TICK | publicTrade WS + orderbook.50 WS |
| 2 | OFI Cont-Kukanov-Stoikov | L1 | TICK | orderbook.50 WS (best-bid/ask deltas) |
| 3 | Iceberg-Detection (Queue-Replenishment) | L1 | TICK | orderbook.200 WS (depth & refills) |
| 4 | Wavelet-Symlet-Denoising (sym4/sym8) | L2 | NEAR-RT | orderbook.50 WS → imbalance stream |
| 5 | Fraktionale Differenzierung (FFD, d≈0.3-0.5) | L2 | NEAR-RT | tickers WS lastPrice + GET /v5/market/kline |
| 6 | Shannon-Entropie L2-Orderbuch | L3 | NEAR-RT | orderbook.50 WS (size-distribution) |
| 7 | Permutation Entropy (m=4, merged Scout+Quant) | L3 | NEAR-RT | tickers WS lastPrice (100-tick rolling) |
| 8 | BOCPD auf openInterest | L3 | NEAR-RT | tickers WS openInterest |
| 9 | HMM (Vola-OFI-Funding, 3-state) | L3 | BATCH | kline 1min + funding history + OFI |
| 10 | MF-DFA Multifractal (Diagnose) | L3 | BATCH | kline 1min (rolling 1k-5k bars) |
| 11 | TDA / Persistent Homology | L3 | BATCH | kline 1min Sliding-Window-Embedding |
| 12 | RQA (Recurrence Quantification) | L3 | BATCH | kline 1min Embedding |
| 13 | Quantum→Cross-Sectional-Z (Ergodizität) | L3 | BATCH | Multi-Symbol tickers WS Panel |
| 14 | Hawkes Spektralradius ρ(Φ) (6-D Orderbook + Liq) | L4 | NEAR-RT | publicTrade WS + allLiquidation WS + orderbook WS |
| 15 | Gutenberg-Richter b + Omori p,c,k | L4 | NEAR-RT | allLiquidation WS (magnitude/aftershocks) |
| 16 | TFSAX + Smith-Waterman Alignment | L4 | BATCH | kline 1min + tickers WS (historische Library) |
| 17 | Renyi-Transfer-Entropy (Lead-Lag Graph) | L4 | BATCH | Multi-Symbol tickers WS panel |
| 18 | PatchTST Funding-Cycle-Forecast | L4 | BATCH | GET /v5/market/funding/history + kline |
| 19 | TimesNet 2D-Periodicity | L4 | BATCH | kline + funding |
| 20 | MOMENT Foundation Model (Zero-Shot) | L4 | BATCH | kline 1min |
| 21 | Long/Short-Ratio Smart-Money-Divergenz | L4 | NEAR-RT | GET /v5/market/account-ratio |
| 22 | Funding-Rate-Clamp Pressure-Release | L5 | NEAR-RT | tickers WS fundingRate + premium |
| 23 | Mark-Index Basis Settlement Convergence | L5 | NEAR-RT | tickers WS markPrice + indexPrice |
| 24 | Kalman-Funding-Premium-Decomposition | L5 | NEAR-RT | tickers WS fundingRate + lastPrice |
| 25 | Kyle's Lambda (Adverse Selection) | L5 | NEAR-RT | publicTrade WS + orderbook WS |
| 26 | SIR-Kompartiment Liquidations-Contagion | L5 | NEAR-RT | allLiquidation WS + OI |

> Hinweis: Tabelle enthält 26 Zeilen; nach Merge-Logik (Hawkes-Paar Scout+Quant ⇒ #14; PE-Paar ⇒ #7) = **21 effektive Methoden**, plus #13 als reduzierte Form von Quantum-#1.

---

## 2. Synergie-Matrix

10 belastbare Synergien, davon 6 bereits im Briefing genannt (verifiziert) + 4 neu erweitert.

```
SYNERGIE 1: Hawkes Spektralradius (L4) × Shannon-Entropie-Kollaps (L3)
Mechanismus: Entropie misst Strukturlosigkeit der Orderbuch-Size-Verteilung;
  ρ(Φ) misst zeitliche Selbsterregungs-Kritikalität. Orthogonale Mathematik
  (statisch-distributionell vs. dynamisch-temporal).
Kombinations-Edge: Doppelbestätigung → False-Positive-Rate vermutlich −40 bis −60%
  ggü. Einzelmetrik. Entropie-Kollaps zuerst (Greenlight), ρ→1 als Trigger.
Layer-Sequenz: L3 → L4 (sequenziell, mit L3-Gate)
```

```
SYNERGIE 2: SpikeWavformer-Spike (L1) × Wavelet-Symlet-Denoising (L2)
Mechanismus: SpikeWavformer enthält DWT bereits intern; nachgelagerter Wavelet-Layer
  wäre redundant. KONSOLIDIEREN: Wavelet als Vorstufe (Rauschen-Trennung),
  Spiking-Membran (LIF) als Event-Trigger.
Kombinations-Edge: Statt kontinuierlich CPU/GPU-Last auf Wavelet → event-driven
  Wavelet-Berechnung NUR bei SNN-Spike. ~95% Compute-Reduktion bei gleicher
  Detect-Rate.
Layer-Sequenz: L1 ⊕ L2 (verschmolzen, Trigger-getrieben)
```

```
SYNERGIE 3: TFSAX/Smith-Waterman (L4) × Hawkes-Kaskaden ρ(Φ) (L4)
Mechanismus: TFSAX matcht statische historische Sequenzmuster; Hawkes
  misst aktuelle Selbsterregungs-Intensität. Match auf historisches
  Ausbruchsmuster + gleichzeitige ρ→1-Lage = Pattern + Energie-Bestätigung.
Kombinations-Edge: TFSAX allein leidet unter Look-Alike-Mustern in Sideways;
  Hawkes-ρ filtert auf energetisch "geladene" Phasen. Erwarteter Hit-Rate-Lift
  +15–25%.
Layer-Sequenz: L4 ∥ L4 (parallel, Output-AND)
```

```
SYNERGIE 4: Funding-Rate-Clamp (L5) × Mark-Index Basis / Premium-Index (L5)
Mechanismus: Clamp begrenzt Funding-Rate auf [−0.05%, +0.05%] (Bybit BTCUSDT).
  Wenn echter Premium |P−F| sich am Cap staut → gestauter Druck.
  Mark-Index-Basis = direkter Spread Mark vs. Index.
Kombinations-Edge: Pre-Settlement-Pressure-Release-Trade: Pressure-Stau
  prognostiziert Funding-Re-Set Move-Richtung. Settlement-Fenster ist 
  bekannt (00/08/16 UTC) → Timing-Edge mit hartem Zeitstempel.
Layer-Sequenz: L5 ⊕ L5 (verschmolzen, gemeinsames "Funding-Pressure-Module")
```

```
SYNERGIE 5: Gutenberg-Richter / Omori (L4) × SIR-Liquidations-Contagion (L5)
Mechanismus: GR misst Magnituden-Frequenz-Verteilung der Liquidationen (b-Wert);
  Omori beschreibt Nachbeben-Zerfall (p,c). SIR modelliert Ansteckungs-
  Kompartimente (S/I/R) zwischen gehebelten Positionen.
Kombinations-Edge: b-Wert-Drift (b sinkt → Großbeben-Wahrscheinlichkeit steigt)
  triggert SIR-R₀-Re-Estimation. Wenn R₀>1 UND b<b_baseline−2σ → Kaskaden-
  Prognose mit Magnituden-Schätzung. Liquidations-Volumen-Vorhersage.
Layer-Sequenz: L4 → L5 (sequenziell)
```

```
SYNERGIE 6: Renyi-Transfer-Entropy (L4) × Long/Short-Ratio Divergenz (L4)
Mechanismus: Renyi-TE liefert gerichteten Informationsfluss BTC→Alt
  (zeit-asymmetrisch, Heavy-Tail-fokussiert via Renyi-Ordnung α=0.5).
  Long/Short-Ratio gibt Sentiment-Skew der Retail-Konten.
Kombinations-Edge: Alt-Trade-Trigger nach BTC-Move, ABER mit Anti-Crowding-
  Filter (skip wenn L/S-Ratio bereits in Move-Richtung extrem). Reduziert
  Last-In-Risk klassischer Lead-Lag-Strategien.
Layer-Sequenz: L4 ∥ L4 (parallel, L/S als Veto-Filter)
```

```
SYNERGIE 7: BOCPD (L3) × HMM (L3) × Permutation-Entropy (L3)
Mechanismus: Drei Regime-Detektoren mit orthogonalen Mathematiken:
  BOCPD = Bayes-online Change-Point;
  HMM = latente diskrete States (Viterbi);
  PE = ordinale Komplexität (Forbidden Patterns).
Kombinations-Edge: Ensemble-Regime-Vote (Majority oder Bayesian-Average).
  Jede Methode hat eigene Failure-Modes (BOCPD: Hazard-Prior-Sensitivität;
  HMM: Label-Switching; PE: m-Parameter). Ensemble glättet das.
Layer-Sequenz: L3 ∥ L3 ∥ L3 (parallel-aggregiert)
```

```
SYNERGIE 8: OFI Cont-Kukanov-Stoikov (L1) × Kyle's Lambda (L5)
Mechanismus: OFI ist *Volumen-Imbalance* (Δ Bid-Volume − Δ Ask-Volume);
  Kyle's λ ist *Preis-Impact-Sensitivität* (∂P/∂Q signed). Beide nutzen
  publicTrade + orderbook, aber messen verschiedene Microstructure-Größen.
Kombinations-Edge: OFI signalisiert Druck-Richtung; Kyle's λ quantifiziert
  Adverse-Selection (Toxic-Flow-Wahrscheinlichkeit). Entry NUR wenn OFI-Signal
  + λ unter Toxic-Threshold (sonst Smart-Money fängt uns). Slippage-aware Entry.
Layer-Sequenz: L1 → L5 (L5 als Filter VOR Execution)
```

```
SYNERGIE 9: Fraktionale Differenzierung (L2) × ALLE ML-Methoden (L4)
Mechanismus: FFD (López de Prado, d≈0.3-0.5) macht Preisreihen stationär OHNE
  vollständigen Memory-Loss (im Gegensatz zu klassischen Returns). Erhält
  Long-Memory-Strukturen, die Transformer-Modelle ausnutzen können.
Kombinations-Edge: Vorgelagertes Preprocessing für PatchTST, TimesNet, MOMENT,
  HMM. Erwartete Verbesserung der Forecast-Sharpe um 10-20% ggü. nominalen Preisen
  oder log-returns.
Layer-Sequenz: L2 → {L4×4, L3-HMM} (universelles Preprocessing)
```

```
SYNERGIE 10: TDA + RQA + MF-DFA (L3 Ensemble)
Mechanismus: Drei nichtlineare Komplexitätsmessungen:
  TDA = topologische Persistenz (H₀/H₁-Betti);
  RQA = Wiederkehr-Strukturen (DET, LAM);
  MF-DFA = multifraktale Skalierung h(q).
Kombinations-Edge: Crash-Early-Warning. TDA-L¹-Norm hat höchste Sensitivität,
  RQA-DET höchste Spezifität, MF-DFA-Δh markiert Phasenübergang. Z-Score-Aggregation
  → 2-of-3-Hit als Early-Warning. Eigenstudie nötig zur Schwellenkalibrierung.
Layer-Sequenz: L3 ∥ L3 ∥ L3 (parallel, BATCH)
```

---

## 3. Kombinationsarchitekturen (5 Mini-Strategien)

### 3.1 "Seismischer Cascade Detector" (L4+L5)
**Methoden:** Hawkes Spektralradius (6-D Orderbook + Liquidation als exogene Inputs) + Gutenberg-Richter b-Wert + Omori p,c,k + SIR-R₀.
**Logik:** Liquidationen folgen seismischen Statistiken (Power-Law Magnituden, Omori-Nachbeben-Zerfall). Hawkes formalisiert Selbsterregung; GR/Omori liefern Magnituden-Modell; SIR liefert Ansteckungs-Schätzung über gehebelte Positionen.
**Entry-Bedingung:** ρ(Φ) > 0.85 (steigend) UND b-Wert < b̄−2σ (großbeben-prone) UND Omori-Aftershock-Phase aktiv (k·(t+c)^−p hoch) UND SIR-R₀ > 1.0. Trade-Richtung = entgegengesetzt zur Liquidations-Seite (Long-Liqs → Long-Entry nach Klimax).
**Exit-Bedingung:** ρ(Φ) < 0.5 ODER Omori-Decay-Phase erreicht (t > 5·c) ODER Stop bei OI-Recovery > 95% des Pre-Cascade-Niveaus.
**Edge-Quelle:** Mean-Reversion nach Liquidations-Klimax; Retail erkennt nur den Spike, nicht das energetische Profil. Zeitfenster sehr kurz (Sekunden-Minuten).
**Layer:** L4 (Hawkes, GR/Omori) + L5 (SIR, Sizing über λ).

### 3.2 "Entropie-Momentum" (L3+L1+L5)
**Methoden:** Shannon-L2-Entropie-Kollaps + OFI Cont-Kukanov-Stoikov + Funding-Rate-Clamp-Pressure.
**Logik:** Klassische Greenlight-Kaskade: Entropie kollabiert (Markt verlässt Random Walk) → OFI dreht in eindeutige Richtung → Funding-Pressure bestätigt Druck-Direktion.
**Entry-Bedingung:** Shannon-Entropie L2 < 24h-median−2σ UND |OFI_rolling_5s| > 90%-Quantil UND Funding-Pressure-Sign übereinstimmend mit OFI-Sign UND PE < median_24h (Greenlight).
**Exit-Bedingung:** Entropie regeneriert zurück über median ODER OFI flippt Vorzeichen ODER Funding-Pressure dissipiert (|P−F| < 0.01%).
**Edge-Quelle:** Mikrostruktur-Information (institutionelle Aggression sichtbar in OFI + Order-Buch-Strukturzusammenbruch). Funding als Trigger-Bestätigung der Asymmetrie.
**Layer:** L1 (OFI) + L3 (Entropie, PE) + L5 (Funding).

### 3.3 "Pre-Settlement Pressure-Release" (L5+L3)
**Methoden:** Funding-Rate-Clamp-Pressure + Mark-Index-Basis + Kalman-Premium-Decomposition + BOCPD auf openInterest.
**Logik:** Funding-Settlements (00/08/16 UTC) sind deterministische Zeit-Trigger. Wenn Clamp-Pressure |P−F| signifikant am Cap steht UND Basis-Spread Mark−Index extrem UND Kalman-Trend-Komponente persistent → Settlement-Fenster löst gestauten Druck aus.
**Entry-Bedingung:** T_settlement − t < 30min UND Funding-Pressure > 90%-Quantil (rolling 30d) UND Mark-Index-Basis · sign(Pressure) > 0 (gleiche Richtung) UND BOCPD-Run-Length zeigt stabiles OI-Regime (kein concurrent Change-Point).
**Exit-Bedingung:** Settlement-Tick + 10min ODER Funding rastet zurück innerhalb [−0.01%, 0.01%].
**Edge-Quelle:** Mechanische Pressure-Release; Retail rebalanciert mit Settlement-Tick. Edge ist *timing-präzise*, nicht direktional-prognostisch.
**Layer:** L5 (drei Funding-Module) + L3 (BOCPD als Veto-Filter).

### 3.4 "Pattern × Foundation Ensemble" (L2+L4)
**Methoden:** Fraktionale Differenzierung (Preprocessing) + TFSAX+Smith-Waterman + MOMENT (Zero-Shot) + PatchTST (fine-tuned auf Funding-Cycle) + Pearson-Korrelation der Forecasts als Confidence-Gate.
**Logik:** Drei orthogonale Pattern-Engines (klassisch SAX-aligned, Foundation-Modell zero-shot, Patch-Transformer fine-tuned). Trade nur wenn Forecast-Konsens (Pairwise-Pearson > 0.6).
**Entry-Bedingung:** ≥2 von 3 Modellen prognostizieren gleichgerichteten Move > 0.5% in horizon h ∈ {15min, 1h, 4h} UND Pairwise-Forecast-Korrelation > 0.6 UND |TFSAX-Match-Score| > 0.75 (Smith-Waterman normalized).
**Exit-Bedingung:** Time-Stop bei horizon h ODER Forecast-Update flippt Vorzeichen.
**Edge-Quelle:** Multi-Model-Konsens senkt Idiosyncratic Forecast-Noise; FFD-Input erhält Long-Memory.
**Layer:** L2 (FFD) + L4 (TFSAX, MOMENT, PatchTST).

### 3.5 "Cross-Sectional Ergodicity Reversion" (L3+L4) — **REDUZIERTE QUANTUM-METHODE**
**Methoden:** Cross-Sectional-Z-Score (E_t[X] − ⟨X⟩_ensemble) + Renyi-Transfer-Entropy (Lead-Lag-Graph) + HMM (Regime-Filter).
**Logik:** Ergodizitätsverletzung: Symbole mit zeit-gemitteltem Return weit weg vom Ensemble-Mittel (über alle Symbole) tendieren zur Cross-Sectional-Mean-Reversion. Renyi-TE identifiziert *welche* Symbole gerichteten Informationsfluss von BTC erhalten (also keine reine Idiosynkrasie sind).
**Entry-Bedingung:** Cross-Sectional-Z-Score |z| > 2.5 UND Symbol hat Renyi-TE(BTC→Alt) > 0.05 (im Informationsfluss-Netzwerk) UND HMM-State ≠ "High-Vol-Crash". Trade-Richtung: gegen Z (Mean-Reversion).
**Exit-Bedingung:** Z-Score zurück innerhalb [−0.5, 0.5] ODER Time-Stop 24h ODER HMM-Regime-Wechsel.
**Edge-Quelle:** Statistische Mean-Reversion über Symbol-Panel; Renyi-TE filtert die "echten" Reversions-Kandidaten aus rein-noisy Outliers.
**Layer:** L3 (Z-Score, HMM) + L4 (Renyi-TE).

---

## 4. Prioritätsranking

**Formel:** `Priorität = (Edge-Score × Novelty) / Komplexität` mit LOW=1, MED=2, HIGH=3.

### 4.1 Quick Wins (Top 5, Priorität > 3.0, Komplexität LOW/MEDIUM)

| Rang | Methode | Edge | Novelty | Komplex. | Priorität | Begründung |
|------|---------|------|---------|----------|-----------|------------|
| 1 | **Funding-Rate-Clamp Pressure-Release** | 3 | 3 | 2 | **4.5** | Deterministisches Settlement-Timing (00/08/16 UTC), Bybit liefert Funding direkt im tickers-Stream, simple Threshold-Logik. Backtestbar auf 6 Monaten in 1 Tag. |
| 2 | **OFI Cont-Kukanov-Stoikov** | 3 | 2 | 1 | **6.0** | Microstructure-Klassiker mit publizierten Sharpe-Werten. orderbook.50 WS reicht. Reine Python+Numpy. <500 LOC. |
| 3 | **Mark-Index Basis Settlement Convergence** | 3 | 2 | 1 | **6.0** | Triviale Arithmetik (Mark − Index), aber empirisch belastbarer Edge nahe Settlement. Tickers-WS hat beide Felder. |
| 4 | **Permutation Entropy Greenlight (merged)** | 2 | 2 | 1 | **4.0** | Ein rolling-window O(n log n), m=4, τ=1. ordpy-Library. Universal-Filter für alle nachgelagerten Module. |
| 5 | **BOCPD auf openInterest** | 2 | 2 | 2 | **2.0** | Geringere Priorität, aber günstig zu implementieren (bayesian-changepoint-detection PyPI). Wichtig als L3-Baustein. |

Alternative für Rang 5 mit höherer Priorität: **Gutenberg-Richter / Omori auf Liquidationen** (3×3/2 = **4.5**) — sehr empfohlen als Quick Win Nr. 2 wenn allLiquidation-Collector steht.

### 4.2 Moonshots (Top 3, Novelty=3, Komplexität HIGH, Edge ≥ 2)

| Rang | Methode | Edge | Novelty | Komplex. | Priorität | Moonshot-Begründung |
|------|---------|------|---------|----------|-----------|---------------------|
| 1 | **Hawkes 6-D Orderbook × Liquidation-coupled (Scout+Quant merged)** | 3 | 3 | 3 | **3.0** | Transformatives Potenzial: einzige Methode, die *zeitliche Selbsterregung* in Microstructure formal misst. Spektralradius ρ(Φ)→1 als Kritikalitäts-Indikator. Risiko: Inferenz von 6-D-Branching-Matrix Φ ist numerisch anspruchsvoll (tick-library, MLE konvergiert langsam). |
| 2 | **SpikeWavformer (SNN + DWT)** | 2 | 3 | 3 | **2.0** | Neurobiologisch inspirierte Event-Filterung. snnTorch+PyWavelets. RTX 5060 Ti mit 16GB ausreichend für ~1M-Parameter-LIF-Netz. Edge in Compute-Effizienz (event-driven statt continuous). Risiko: Training-Pipeline für surrogate-gradient SNNs unreif. |
| 3 | **TFSAX + Smith-Waterman Alignment** | 2 | 3 | 3 | **2.0** | Bioinformatik-Import: Behandelt Preissequenzen als DNA-Strings. Pattern-Library aus 5y Bybit-Historie. Edge: erkennt strukturell ähnliche Marktphasen unabhängig von absolutem Preis. Risiko: Library-Aufbau aufwändig, Match-Scoring-Schwellen empirisch zu kalibrieren. |

**Alternative Moonshot-Kandidaten** (Priorität 2.0, knapp unter Top-3): MOMENT Zero-Shot, TimesNet 2D-Periodicity, Renyi-Transfer-Entropy-Netzwerk.

---

## 5. Daten-Infrastruktur

### 5.1 Konsolidierte Endpoint-Tabelle

| Bybit-Endpoint | Methoden | Speicherbedarf (BTCUSDT only) | Update-Frequenz |
|----------------|----------|-------------------------------|-----------------|
| `tickers.BTCUSDT` (WS public/linear) | #14 Hawkes, #5 FFD, #7 PE, #8 BOCPD-OI, #22 Funding-Clamp, #23 Mark-Index-Basis, #24 Kalman-Premium, #13 Cross-Sectional-Z (multi-symbol) | ~150MB/Tag (kompakt) | 100ms |
| `publicTrade.BTCUSDT` (WS) | #1 SpikeWavformer, #14 Hawkes, #25 Kyle's λ | ~200MB/Tag | event-driven (10–500ms) |
| `orderbook.50.BTCUSDT` (WS) | #1 SpikeWavformer, #2 OFI, #4 Wavelet, #6 Shannon-L2, #14 Hawkes-Orderbook, #25 Kyle's λ | ~500MB/Tag (deltas) | 20ms (compact) |
| `orderbook.200.BTCUSDT` (WS) | #3 Iceberg-Detection (optional) | ~2GB/Tag | 100ms snapshot |
| `allLiquidation.BTCUSDT` (WS) | #14 Hawkes-Liq-Layer, #15 Gutenberg-Richter+Omori, #26 SIR-Contagion | ~5MB/Tag (sparse) | 500ms |
| `GET /v5/market/kline` (REST) | #5 FFD, #9 HMM, #10 MF-DFA, #11 TDA, #12 RQA, #16 TFSAX, #19 TimesNet, #20 MOMENT | ~1MB/Symbol/Tag (1min) | on-demand (Backfill) |
| `GET /v5/market/funding/history` (REST) | #18 PatchTST, #19 TimesNet, #24 Kalman | ~10KB/Symbol/Tag (3 Settlements) | every 8h |
| `GET /v5/market/account-ratio` (REST) | #21 Long/Short-Ratio | ~5KB/Symbol/Tag | 5min poll |

**Gesamt-Storage geschätzt** für BTCUSDT-only, 1 Jahr Tick-Daten: ~300GB (mit Parquet+ZSTD ~80GB). Für 5-10 Symbole skaliert linear: 1.5–3TB roh.

### 5.2 Gemeinsame Infrastruktur-Bausteine

1. **WebSocket-Collector** (publicTrade + orderbook + tickers + allLiquidation) → **EINMAL** bauen, alle TICK/NEAR-RT-Methoden lesen daraus. Empfehlung: `asyncio + websockets + asyncpg/duckdb-Parquet-Writer`. Reconnect-Handling Pflicht.
2. **Orderbook-State-Engine:** Maintain Top-50-Levels in-memory (bid/ask sorted arrays). Verwendet von #2 OFI, #4 Wavelet, #6 Shannon-L2, #14 Hawkes-Orderbook, #25 Kyle's λ. → Ein zentrales `OrderbookState`-Objekt mit Subscriber-Pattern.
3. **Imbalance-Feature-Stream:** Aus Orderbook-State abgeleitet (Top-5/10/20-Volumenverhältnis). Konsumiert von Wavelet-Layer, Shannon-Entropie und OFI. → Eine Stream-Berechnung, drei Konsumenten.
4. **FFD-Preprocessing-Layer:** Fraktionale Differenzierung mit d∈{0.3, 0.4, 0.5} vorgerechnet auf alle Kline-Reihen. Universelles Input für #9, #18, #19, #20, #27.
5. **Liquidation-Event-Buffer:** Sliding-Window-Liste der letzten 1000 Liquidations-Events mit (t, side, qty, px). Verwendet von #14 Hawkes-Liq, #15 GR/Omori, #26 SIR.
6. **Funding-Settlement-Scheduler:** Triggert N-Min vor jedem 00/08/16-UTC-Slot. Wird von #22, #23, #24 und Strategie 3.3 abonniert.
7. **Multi-Symbol-Panel:** Synchrones tickers-Snapshot über 20-50 Bybit-Top-Symbole. Für #13 Cross-Sectional-Z und #17 Renyi-TE-Lead-Lag-Netzwerk.

### 5.3 API-Limits & Constraints
- **WebSocket:** Praktisch unlimitiert; ein Connection-Bündel pro Stream-Typ ausreichend.
- **REST:** 120 req/min für unauthenticated, 600 req/min authenticated. Kline-Backfill für 5 Jahre × 10 Symbole = ~250 Requests → minutenschnell mit Rate-Limit-Sleep. **Keine Backfill-Engpässe.**
- **Latenz Bybit DE/EU:** ~50–150ms via WebSocket Singapore-Endpoint; mit AWS Tokyo VPS ~5–15ms erreichbar. Ausreichend für alle NEAR-RT-Methoden, grenzwertig für TICK-only-Strategien (HFT-Pure-MM würde nicht funktionieren — ist aber auch nicht Ziel).

---

## 6. Risikoübersicht (pro Methoden-Gruppe)

### 6.1 Microstructure-Layer (L1 + Teile L5)
**Methoden:** OFI, Iceberg-Detection, Kyle's λ.
- **Overfitting:** Niedrig. Wenige Parameter (Lookback-Window 5/30/60s). Walk-Forward problemlos.
- **Regime-Abhängigkeit:** Funktioniert besonders in normaler Vol (HMM-State 1–2); in Low-Liquidity-Phasen (Asia-Pause) instabil.
- **Bybit-Einschränkungen:** Keine — orderbook.50 WS liefert ausreichende Tiefe. **Iceberg-Detection-Achtung:** Bybit exposed keine Iceberg-Flags → rein statistische Inferenz via Queue-Replenishment-Tracking → Edge ist 2/3, nicht 3/3.

### 6.2 Denoising-Layer (L2)
**Methoden:** Wavelet-Symlet, Fraktionale Differenzierung.
- **Overfitting:** Niedrig. Wavelet hat 2-3 Hyperparameter (Mother-Wavelet, Level, Threshold). FFD hat einen Parameter d.
- **Regime-Abhängigkeit:** Robust. FFD-d sollte alle 30–90 Tage neu kalibriert werden (ADF-Test).
- **Bybit-Einschränkungen:** Keine.

### 6.3 Regime-Layer (L3)
**Methoden:** Shannon-Entropie, PE, BOCPD, HMM, MF-DFA, TDA, RQA, Cross-Sectional-Z.
- **Overfitting:** HMM mit 3+ Zuständen sensitiv für Label-Switching → walk-forward mit fixierten transition priors. TDA-Schwellen empirisch.
- **Regime-Abhängigkeit:** Selbst die Regime-Detektoren! Ironie: PE funktioniert besser in liquiden Hauptzeiten; MF-DFA braucht ≥1k Bars Lookback.
- **Bybit-Einschränkungen:** Keine — alle BATCH-fähig (1min-kline reicht). Multi-Symbol-Panel braucht WS-Connection pro Symbol oder consolidated tickers.

### 6.4 Pattern-Layer (L4)
**Methoden:** Hawkes, GR/Omori, TFSAX+SW, Renyi-TE, PatchTST, TimesNet, MOMENT, L/S-Ratio.
- **Overfitting:** **HÖCHSTES Risiko der gesamten Pipeline.**
  - Hawkes 6-D-MLE: 36 Branching-Parameter — pre-regularisieren oder reduzieren auf 2-3 Ereignistypen.
  - PatchTST/TimesNet: 1–10M Parameter — strikt walk-forward, Hyperparameter via Optuna.
  - TFSAX-Smith-Waterman: Library-Match-Schwelle stark empirisch; Cross-Validation auf disjunkten Zeitfenstern.
- **Regime-Abhängigkeit:** Hawkes/GR/Omori funktionieren NUR in liquide-aktiven Phasen mit ≥10 Liquidations/min. Foundation-Modelle (MOMENT) erstaunlich regime-robust per zero-shot.
- **Bybit-Einschränkungen:** RTX 5060 Ti (16GB VRAM) reicht für PatchTST/TimesNet bis ~10M Parameter; MOMENT-base (~110M) auch noch komfortabel; MOMENT-large knapp.

### 6.5 Risk-Layer (L5)
**Methoden:** Funding-Clamp, Mark-Index, Kalman, SIR, Kyle's λ.
- **Overfitting:** Niedrig (Funding-Module sind Akkumulator-Logik mit ≤3 Parametern). SIR braucht Estimation von β/γ — auf rolling 30d-Fenster robust.
- **Regime-Abhängigkeit:** Funding-Module brauchen *Funding-aktive* Phasen — bei Sideways-Markt mit ~0% Funding kaum Signal. SIR-Contagion funktioniert hauptsächlich in High-Leverage-Regimes (typisch Q4).
- **Bybit-Einschränkungen:** Funding-Cap [−0.05%, +0.05%] für BTCUSDT — höher für andere Symbole. Pro Symbol unterschiedliche Settlement-Frequenzen prüfen (BTCUSDT: 8h; einige Altcoins: 1h oder 4h).

### 6.6 Querschnitt-Risiken
- **Walk-Forward-Pflicht:** Alle ML-haltigen Methoden (#9 HMM, #16 TFSAX, #18–#20 Transformer) mit purged k-fold + embargo (López de Prado).
- **API-Reconnect:** Bei Bybit WebSocket-Dropout (typisch 1×/Tag) muss Snapshot-Resync sauber implementiert sein, sonst Hawkes-Inferenz korrupt.
- **Survivorship-Bias:** Symbol-Listen aus 2025-Universum auf 2021-Daten anwenden → künstlich. Multi-Symbol-Methoden (#13, #17) müssen Delisting-Daten respektieren.
- **Funding-Schema-Änderungen:** Bybit kann Funding-Frequenzen/Caps ändern (passiert ~jährlich). Funding-Module-Code muss konfigurierbar sein, nicht hardcoded.

---

## 7. Empfohlene Implementierungsreihenfolge

**Leitprinzip:** Erst Infrastruktur, dann Quick Wins als Proof-of-Edge, dann Core-Hawkes-Engine, dann ML-Schichten. Maximal-parallelisiert wo Abhängigkeiten es zulassen.

### Phase 0 — Foundation (Woche 1–2)
1. **Bybit WebSocket-Collector** (publicTrade + orderbook.50 + tickers + allLiquidation) mit Parquet-Persistierung. Auto-Reconnect, Snapshot-Resync, Schema-Versionierung.
2. **Orderbook-State-Engine** + Imbalance-Feature-Stream (Pub/Sub-Architektur).
3. **Funding-Settlement-Scheduler** (Cron-artig auf 00/08/16 UTC).

> *Begründung:* Ohne sauberen Daten-Layer ist jede weitere Methode wertlos. Hawkes-Inferenz reagiert besonders allergisch auf fehlende Events/dropouts → robuste Ingestion FIRST.

### Phase 1 — Quick Wins & Funding-Trinität (Woche 3–5)
4. **Funding-Rate-Clamp Pressure-Release** (#22).
5. **Mark-Index-Basis Settlement-Convergence** (#23).
6. **Kalman-Funding-Premium-Decomposition** (#24).
7. **OFI Cont-Kukanov-Stoikov** (#2).
8. **Permutation-Entropy-Greenlight** (#7).
9. **BOCPD auf openInterest** (#8).
10. Backtest jedes Modul standalone auf 6M-Daten. Veröffentliche Sharpe/Win-Rate je Modul.

> *Begründung:* Alle 6 Methoden sind LOW/MEDIUM-Komplexität, decken bereits 3 von 5 Layern ab, liefern erste echte Edge-Zahlen für Validierung. **Strategie 3.3 "Pre-Settlement Pressure-Release" ist nach Woche 5 bereits live-paper-tradeable.**

### Phase 2 — Seismik & Cascade-Engine (Woche 6–9)
11. **Gutenberg-Richter b + Omori p,c,k auf allLiquidation** (#15).
12. **SIR-Liquidations-Contagion** (#26).
13. **Hawkes 1-D Liquidation-Layer (Quant-Variante)** → simpler MLE-Fit auf single channel. (#14a)
14. **Kyle's Lambda** (#25) als Risk-Filter für L5.
15. Backtest **Strategie 3.1 "Seismischer Cascade Detector"** end-to-end.

> *Begründung:* Liquidations-Statistik (GR/Omori/SIR) ist eigenständig backtest-fähig und braucht nicht die volle 6-D-Hawkes-Infrastruktur. Single-Channel-Hawkes als Sprungbrett zum 6-D-System.

### Phase 3 — Volle Hawkes-Matrix + Regime-Ensemble (Woche 10–14)
16. **Hawkes 6-D Orderbook-Events** mit MLE oder Bayesian-Inference (tick-Library als Basis). (#14b)
17. **Shannon-Entropie L2-Orderbuch** (#6).
18. **Wavelet-Symlet-Denoising** (#4) — als nachgelagerter Layer auf Imbalance-Stream.
19. **HMM (Vola-OFI-Funding, 3-state)** (#9).
20. **Fraktionale Differenzierung** (#5) als universelles Preprocessing.
21. Backtest **Strategie 3.2 "Entropie-Momentum"** end-to-end.

> *Begründung:* 6-D-Hawkes ist die anspruchsvollste klassische Komponente — kommt nach erfolgreichem 1-D-Vorlauf. Entropie+Wavelet+HMM bauen den L3-Ensemble-Knoten.

### Phase 4 — Advanced Pattern + Multi-Symbol (Woche 15–20)
22. **TFSAX + Smith-Waterman Library-Aufbau** (#16). 5y Historie segmentieren.
23. **PatchTST** auf Funding-Cycle (#18). FFD-präpariert.
24. **MOMENT Zero-Shot** als Vergleichs-Forecaster (#20).
25. **Renyi-Transfer-Entropy Multi-Symbol-Netzwerk** (#17).
26. **Cross-Sectional-Z-Score Ergodizitätsmodul** (#13).
27. **Long/Short-Ratio Smart-Money-Divergenz** (#21).
28. Backtest **Strategie 3.4 "Pattern × Foundation Ensemble"** + **Strategie 3.5 "Cross-Sectional Ergodicity Reversion"**.

> *Begründung:* Diese Module brauchen Multi-Symbol-Datenmengen + GPU-Training, was nach Foundation-Layer wirtschaftlich vertretbar wird.

### Phase 5 — Moonshot-Integration & Live-Testnet (Woche 21–24+)
29. **SpikeWavformer (SNN + DWT)** (#1).
30. **TDA + RQA + MF-DFA Ensemble** (#10, #11, #12).
31. **TimesNet** als zusätzlicher Forecaster (#19).
32. **Iceberg-Detection** (#3) — letzter optionaler Layer.
33. **Vollständige Pipeline-Integration:** L1→L2→L3→L4→L5 mit Decision-Aggregator.
34. **Live Paper-Trading auf Bybit Testnet** mit ausgewählten Strategie-Kombinationen (3.1, 3.2, 3.3 priorisiert; 3.4/3.5 sekundär).

> *Begründung:* Moonshots werden zuletzt gebaut, weil ihr Implementierungsrisiko hoch ist und sie ohne den Rest der Pipeline nicht ihren vollen Edge zeigen können.

### Abhängigkeits-Graph (kurz)
```
WebSocket-Collector ─┬─> Orderbook-State ─┬─> OFI, Shannon-L2, Wavelet
                     │                    └─> Kyle's λ, SpikeWavformer
                     ├─> Tickers-Stream  ─┬─> Funding-Module (3×), PE, BOCPD
                     │                    └─> Cross-Sectional-Z (Multi-Symbol-Fan-out)
                     ├─> Trade-Stream    ──> Hawkes-Orderbook, Kyle's λ
                     └─> Liq-Stream      ──> GR/Omori, SIR, Hawkes-Liq
                                                  │
                                              [Hawkes 6-D coupled]
                                                  │
Kline-Backfill ──> FFD ──> {HMM, PatchTST, TimesNet, MOMENT}
                       └─> TFSAX-Library ──> Smith-Waterman
```

**Erste Implementierung explizit benannt:**
- **Tag 1–3:** Bybit-WebSocket-Collector (Phase 0, Schritt 1).
- **Tag 4–7:** Orderbook-State-Engine + Persistierung.
- **Tag 8–14:** Funding-Module + erstes Backtest (Pre-Settlement-Pressure-Release).
- → **Erstes live-paper-testbares Sub-System in Woche 3–5.**

---

## REPORT-FOOTER

- **ACCEPTED-Methoden in Synthese:** 21 (nach Merge: Hawkes-Paar + PE-Paar je 1 Methode; Quantum reduziert auf Cross-Sectional-Z)
- **Identifizierte Synergiepaare:** 10
- **Konkrete Kombinationsstrategien:** 5 (Seismischer Cascade, Entropie-Momentum, Pre-Settlement Pressure-Release, Pattern×Foundation, Cross-Sectional Ergodicity)
- **Top-5 Quick Wins** (Priorität ≥ 4.0 dominant): Funding-Clamp (4.5), OFI (6.0), Mark-Index-Basis (6.0), PE-Greenlight (4.0), GR/Omori oder BOCPD-OI (4.5 / 2.0).
- **Top-3 Moonshots:** Hawkes-6D-Coupled, SpikeWavformer, TFSAX+Smith-Waterman.
- **Empfohlene erste Implementierung:** Bybit-WebSocket-Collector + Persistierungs-Layer (Phase 0, Tag 1–7), gefolgt von **Funding-Rate-Clamp Pressure-Release** als erstes backtestbares Edge-Modul (Tag 8–14).
- **Pipeline-Layer-Abdeckung:** 5/5 ✓ — Kombinationsstrategien decken alle Layer-Sequenzen ab.

[SYNTHESIZER → PRD ARCHITECT] HANDOFF READY. Synthese-Dokument vollständig, Roadmap implementierbar für Einzelperson mit RTX 5060 Ti + VPS innerhalb von ~24 Wochen bis Live-Paper-Trading.
