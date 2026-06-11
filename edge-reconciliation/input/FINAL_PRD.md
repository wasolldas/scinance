# FINAL PRD — Bybit Retail Trader Edge
## Product Requirements Document · Edge Research Framework
**Datum:** 2026-05-22
**Eingabe:** synthesis.md (21 ACCEPTED-Methoden, 10 Synergien, 5 Strategien)
**Zielgruppe:** Algorithmischer Trader, Python-Grundkenntnisse, Backtesting-Erfahrung, Hardware: RTX 5060 Ti (16 GB VRAM) + VPS (Docker/Ubuntu)
**Ziel:** Vollständige, mathematisch fundierte Implementierungs-Blaupause für eine 5-Layer-Edge-Pipeline auf Bybit Perpetual Futures.

---

## INHALTSVERZEICHNIS

1. [Executive Summary](#1-executive-summary)
2. [Problemdefinition](#2-problemdefinition)
3. [Bybit-Datenbasis](#3-bybit-datenbasis)
4. [Methoden-Katalog](#4-methoden-katalog)
5. [Referenz-Architektur](#5-referenz-architektur)
6. [Priorisierungsmatrix](#6-priorisierungsmatrix)
7. [Kombinationsstrategien](#7-kombinationsstrategien)
8. [Implementierungs-Roadmap](#8-implementierungs-roadmap)
9. [Risiken & Einschränkungen](#9-risiken--einschränkungen)

---

## 1. EXECUTIVE SUMMARY

### Forschungsziel
Ein systematisch fundierter, mehrschichtiger statistischer Edge für einen Retail-Algotrader auf Bybit Perpetual Futures, der mit ausschließlich öffentlichen Bybit-V5-WebSocket-/REST-Daten, einer RTX-5060-Ti-Workstation und einem Docker-VPS in ca. 24 Wochen bis zur ersten live-paper-testbaren Version geführt werden kann. Der Edge entsteht NICHT durch Latenz oder Privilegien, sondern durch eine kaskadierte 5-Layer-Pipeline (Ingestion → Denoising → Regime → Pattern → Risk), die Cross-Domain-Methoden aus Seismologie, Epidemiologie, Bioinformatik, Informationstheorie und Neurowissenschaft auf Bybit-spezifische Microstructure-Signale (Funding-Clamp, allLiquidation-WS, openInterest, Premium-Index) anwendet.

### Top-3-Erkenntnisse
1. **Bybit-WebSocket-Stack ist für Retail-Edge ausreichend.** Die öffentlichen Streams (tickers 100 ms, allLiquidation 500 ms, orderbook.50, publicTrade) liefern alle Daten, die für 21 validierte Methoden über fünf Layer hinweg benötigt werden — Colocation oder kostenpflichtige Tick-by-Tick-Feeds sind nicht erforderlich.
2. **Cross-Domain-Methoden liefern Novelty dort, wo klassische Quant-Finance gesättigt ist.** Hawkes-Spektralradius (Seismologie), Gutenberg-Richter/Omori (Liquidations-Statistik), SIR-Contagion (Epidemiologie), TFSAX+Smith-Waterman (Bioinformatik), Renyi-Transfer-Entropy (Informationstheorie) sind in Retail-Crypto-Bots praktisch unbenutzt — sie ergänzen klassische Microstructure-Maße (OFI, Kyle's Lambda).
3. **Die 5-Layer-Pipeline kaskadiert Filter konditional.** Statt aller Methoden permanent zu rechnen, triggert L1 (event-driven SNN/OFI-Spike) den nachgelagerten Wavelet-Denoising-Pfad; L3 (Entropie-Greenlight) gated L4 (Pattern); L5 (Funding-Pressure, SIR, Kyle's λ) sizet und stoppt vor Execution. Das reduziert Compute um geschätzte 95 % gegenüber permanent-laufenden Pipelines.

### Empfohlene Architektur (3 Sätze)
Eine asynchrone Python-Pipeline auf Docker/Ubuntu konsumiert Bybit-V5-WebSockets in einen In-Memory-Orderbook-/Tickers-/Liquidation-State, der über ein Pub/Sub-Pattern fünf parallele Berechnungs-Layer speist (L1 Ingestion, L2 Denoising, L3 Regime-Ensemble, L4 Pattern, L5 Risk). Heavyweight-Komponenten (PatchTST/TimesNet/MOMENT-Forecasts, TFSAX-Library-Match, Hawkes-MLE) laufen batch-asynchron auf der RTX 5060 Ti; Quick-Win-Module (Funding-Clamp, OFI, PE, Mark-Index-Basis, GR/Omori) laufen near-real-time auf der CPU. Ein Decision-Aggregator kombiniert die Layer-Outputs zu Long/Short/Wait + Position-Size + Stop-Level und führt Orders über die Bybit-V5-REST-API aus (zunächst Testnet).

### Erwarteter Edge-Typ
**Microstructure-Timing + Regime-Filter + Risk-Management** (Mischtyp). Konkret:
- *Microstructure-Timing*: OFI/Hawkes/SpikeWavformer auf Sekunden-Skala (Entry-Trigger).
- *Regime-Filter*: PE/BOCPD/HMM/TDA/RQA/Shannon-Entropie als Greenlight-Gate (Strategie-Aktivierung).
- *Risk-Management*: SIR-R₀, Kyle's λ, Funding-Clamp-Pressure für Stop-Sizing und Adverse-Selection-Vermeidung.
- *Mean-Reversion-Alpha*: Funding-Pressure-Release, Mark-Index-Basis, Cross-Sectional-Z (Settlement-Timing-Edge mit hartem Zeitstempel).

### Grober Zeitplan bis erste live-paper-testbare Version
- **Woche 1–2**: Infrastruktur (WebSocket-Collector, Persistierung, Pub/Sub).
- **Woche 3–5**: Quick Wins (Funding-Trinität, OFI, PE, BOCPD) — *erste live-paper-testbare Mini-Strategie* (Pre-Settlement Pressure-Release).
- **Woche 6–9**: Seismik & Cascade Engine (GR/Omori, SIR, 1-D-Hawkes).
- **Woche 10–14**: Voll-Hawkes 6-D, Regime-Ensemble.
- **Woche 15–20**: Advanced Pattern + Multi-Symbol.
- **Woche 21–24**: Moonshots + Integration + Live-Testnet.
→ **Erste live-paper-Version: Woche 5. Vollintegrierte Pipeline auf Testnet: Woche 24.**

---

## 2. PROBLEMDEFINITION

### 2.1 Warum hat Retail im Standardansatz keinen Edge auf Bybit?

Retail-Trader auf Bybit operieren in einem Markt, in dem die klassischen Standardansätze entweder gesättigt oder strukturell unzugänglich sind:

- **Technische Analyse (TA) ist gesättigt.** Indikatoren wie RSI, MACD, Bollinger Bands, Fibonacci, Ichimoku werden von hunderttausenden Retail-Konten und tausenden Bots berechnet. Jede Signal-Information ist innerhalb von Millisekunden in den Preis eingepreist. Der Edge ist mathematisch null oder negativ (nach Fees).
- **Klassische Funding-Arbitrage ist von HFT-Desks abgegrast.** Cash-and-Carry-Trades (Long Spot / Short Perp) bei positivem Funding werden von professionellen Market-Makern (Wintermute, Jump, GSR) mit Tick-by-Tick-Latenz und Cross-Exchange-Hedging-Infrastruktur betrieben. Retail kann nur die *Residuen* dieses Spreads ausnutzen.
- **Colocation und Sub-Millisekunden-Latenz fehlen Retail.** Tier-1-MM hosten in AWS Tokyo (Bybit-Matching-Engine) mit ~50 µs Latency. Retail-VPS in EU/US hat 50–150 ms Round-Trip. Reine HFT-Strategien (Market-Making, Latency-Arbitrage) sind ausgeschlossen.
- **Proprietäre Datenfeeds (OFI mit hidden-flag, voll-tiefe LOB-Snapshots <10 ms) sind kostenpflichtig oder nicht öffentlich.** Bybit-Free-Tier liefert orderbook.50 mit ~20 ms Delta-Updates — ausreichend für Mid-Frequency, nicht für Pure-HFT.
- **Sentiment-/Social-Data ist verrauscht.** Twitter, Reddit, Telegram-Signale haben hohe Latenz (Minuten) und sind durch Sentiment-as-a-Service-Anbieter (LunarCrush, Santiment) bereits in institutionellen Modellen.

**Konsequenz:** Retail muss strukturell *anderswo* suchen — nicht schneller, sondern *anders*.

### 2.2 Welche Informationsasymmetrien sind ausbeutbar?

Die folgenden Asymmetrien sind *öffentlich zugänglich*, aber in Retail-Bots unter-genutzt:

1. **`allLiquidation`-WebSocket (500 ms).** Jede einzelne Liquidation wird gepusht (nicht nur 1/sec wie bei vielen Konkurrenz-Börsen). Erlaubt:
   - Hawkes-Inferenz auf Self-Excitation-Ratio.
   - Gutenberg-Richter b-Wert (Magnituden-Power-Law).
   - Omori-Aftershock-Decay-Fit.
   - SIR-Contagion-R₀-Schätzung.
2. **Funding-Rate-Clamp-Mechanik ist deterministisch.** Bybit clamped F bei ±0.05 % für BTCUSDT (Formel: `F = P + clamp(I − P, 0.05%, −0.05%)`). Wenn Premium |P| weit über Cap → gestauter Druck → Pressure-Release-Move nach Settlement (00/08/16 UTC). Edge ist mechanisch.
3. **Mark/Index/Premium öffentlich im tickers-Stream.** Basis (Mark − Index) ist über orders-of-magnitude weniger gewatchet als Spot-Charts.
4. **Long/Short-Ratio (Konten-Aggregat, nicht Volumen).** Bybit's `/v5/market/long-short-ratio` liefert Retail-Konten-Skew — perfekter Contrarian-Indikator bei extremer Asymmetrie.
5. **openInterest live im tickers-Stream.** Erlaubt BOCPD-Strukturbruchsuche auf OI (statt nur Preis).
6. **Multi-Symbol-Panel.** Cross-Sectional-Z über Top-20-Perps für Ergodizitäts-basierte Mean-Reversion; Renyi-TE für gerichteten Informationsfluss BTC→Alt.
7. **Orderbook.50 mit 20-ms-Deltas.** Shannon-Entropie der Size-Verteilung, OFI Cont-Kukanov-Stoikov, Kyle's λ, Iceberg-Detection — alles berechenbar.

### 2.3 Was scheidet aus?

- **Colocation/Sub-ms-Latenz** → reines Market-Making, Latency-Arbitrage, Cross-Exchange-Triangulation auf Tick-Level.
- **Sub-Tick-Datenfeeds** (proprietäre Hidden-Iceberg-Flags, Internal-Order-IDs) → können nicht beschafft werden, nur statistisch inferiert.
- **IBKR/Interactive-Brokers-Style-Aggregation** über mehrere Spot-Venues → Out-of-Scope für Bybit-only.
- **Pure-HFT-Order-Anticipation-Strategien** → benötigen volle LOB-Tiefe + Latency, die Retail strukturell nicht hat.
- **Reinforcement-Learning auf End-to-End-Reward** (über Pipeline-Module hinaus) → bewusst nicht im Scope dieses PRD (Add-On für späteres Iteration).

---

## 3. BYBIT-DATENBASIS

Alle benötigten Bybit-V5-Endpoints. Alle WebSocket-Streams sind kostenfrei und unauthenticated (außer privaten Account-Streams für Execution).

| # | Signal | Endpoint | Frequenz | Relevante Felder | Genutzt in Layer / Methoden |
|---|--------|----------|----------|------------------|------------------------------|
| 1 | Tickers (Composite) | WS `tickers.{symbol}` (linear) | 100 ms | `lastPrice`, `markPrice`, `indexPrice`, `fundingRate`, `nextFundingTime`, `openInterest`, `openInterestValue`, `bid1Price/Size`, `ask1Price/Size`, `ts` | L3: PE, BOCPD-OI; L5: Funding-Clamp, Mark-Index-Basis, Kalman-Premium; L4: Hawkes (OI-Input), Cross-Sectional-Z |
| 2 | All Liquidations | WS `allLiquidation.{symbol}` | 500 ms (event-driven) | `T` (timestamp), `s` (symbol), `S` (Buy/Sell), `v` (volume), `p` (bankruptcy price) | L4: Hawkes-Liq-Channel, Gutenberg-Richter, Omori; L5: SIR-Contagion |
| 3 | Public Trades | WS `publicTrade.{symbol}` | Event-driven (10–500 ms) | `T`, `p`, `v`, `S`, `BT` (block trade flag) | L1: SpikeWavformer, OFI (sign), Hawkes-Trade-Channel; L5: Kyle's λ |
| 4 | Orderbook 50-Level | WS `orderbook.50.{symbol}` | ~20 ms (delta) | `u` (update id), `b` (bid array [price, size]), `a` (ask array), `ts` | L1: OFI, SpikeWavformer; L2: Wavelet-Symlet auf Imbalance; L3: Shannon-Entropie-L2; L4: Hawkes-6D-Orderbook; L5: Kyle's λ |
| 5 | Orderbook 200-Level | WS `orderbook.200.{symbol}` | ~100 ms (snapshot) | `b/a` arrays 200 deep | L1: Iceberg-Detection (optional, advanced) |
| 6 | Kline 1-min (Historical) | REST `GET /v5/market/kline?category=linear&interval=1` | On-demand | `startTime`, `open`, `high`, `low`, `close`, `volume`, `turnover` | L2: FFD; L3: HMM, MF-DFA, TDA, RQA, Cross-Sectional-Z; L4: TFSAX, PatchTST, TimesNet, MOMENT, Renyi-TE |
| 7 | Kline 5-min | REST `GET /v5/market/kline?interval=5` | On-demand | OHLCV | L3: RQA (5-min variant); L4: TimesNet (Multi-Period) |
| 8 | Funding History | REST `GET /v5/market/funding/history` | 8 h (per settlement) | `fundingRate`, `fundingRateTimestamp`, `symbol` | L4: PatchTST, TimesNet; L5: Kalman-Premium-Decomposition |
| 9 | Open Interest History | REST `GET /v5/market/open-interest?intervalTime=5min` | 5 min (poll) | `openInterest`, `timestamp` | L3: BOCPD (historische Kalibrierung) |
| 10 | Long/Short Account Ratio | REST `GET /v5/market/account-ratio?period=1h` | 1 h / 5 min / 15 min / 4 h | `buyRatio`, `sellRatio`, `timestamp` | L4: Long/Short-Smart-Money-Divergenz |
| 11 | Instruments-Info | REST `GET /v5/market/instruments-info` | One-shot | tickSize, minOrderQty, max leverage, fundingInterval | Setup: Sizing, Risk-Limits, Symbol-Universum |
| 12 | Recent Trades (Backfill) | REST `GET /v5/market/recent-trade` | On-demand | letzte 1000 Trades | Backfill bei WS-Reconnect für Kyle's λ |

**Geschätzter Speicherbedarf** (BTCUSDT-only, 1 Jahr):
- tickers + funding + OI + L/S-Ratio: ~150 MB/Tag (kompakt Parquet+ZSTD).
- publicTrade: ~200 MB/Tag.
- orderbook.50 (Deltas): ~500 MB/Tag.
- allLiquidation: ~5 MB/Tag.
- → **Gesamt ~300 GB/Jahr (roh), ~80 GB komprimiert.**
- 5–10 Symbole (BTC, ETH, SOL, BNB, XRP, …) skaliert linear: 1.5–3 TB roh.

**API-Limits**:
- WebSocket: praktisch unlimitiert, 1 Connection-Bundle pro Stream-Typ ausreichend.
- REST unauthenticated: 120 req/min.
- REST authenticated: 600 req/min.
- **Keine Backfill-Engpässe** für 5y × 10 Symbole × 1-min-kline (≈ 250 Calls).

---

## 4. METHODEN-KATALOG

Vollständige Einträge für alle 21 validierten Methoden, gruppiert nach Pipeline-Layer. Format: M{N}: {Name} [Layer] [Quick Win / Standard / Moonshot].

---

### Layer L1 — INGESTION (Event-getriebene Filterung)

#### M1: SpikeWavformer Event-Driven Ingestion [L1] [Moonshot]
**Herkunft:** Neurowissenschaft / Spiking Neural Networks (BCI/EEG State-of-the-Art 2025)
**Kernprinzip:** Spiking-Neuronen feuern nur, wenn Membranpotenzial einen Schwellenwert überschreitet. In Kombination mit Diskreter Wavelet-Transformation (DWT) und Spiking-Self-Attention entsteht ein energie-effizienter Event-Filter, der Polling ersetzt. Die Pipeline aktiviert sich NUR bei genuinen Anomalien (OI-Sprung, Liquidations-Cluster, Imbalance-Burst).
**Mathematische Grundlage:**
```
V_m(t + Δt) = α · V_m(t) + Σ w_i · s_i(t) − V_reset · s_out(t)
DWT:  c_{j,k} = Σ_n x[n] · ψ*_{j,k}[n]
Spike output: s_out(t) = 1 if V_m(t) ≥ V_th else 0
```
Variablen: α = Leak-Faktor, w_i = synaptische Gewichte, s_i = Input-Spikes, V_th = Feuerschwelle, ψ_{j,k} = Wavelet-Basis (Symlets sym4–sym8).
**Bybit-Anwendung:** Input-Spikes aus `tickers.openInterest`-Delta, `allLiquidation`-Volume, `orderbook.50`-Imbalance-Stream. DWT zerlegt jeden Stream; LIF-Membran integriert über 500-ms-Window; Spike triggert nachgelagerte Layer (Wavelet, Hawkes, Pattern).
**Implementierungsskizze:**
1. Multi-Stream-Input (3 Channels: OI-Delta, Liq-Volume, Imbalance) auf normalisierte Float-Vektoren.
2. PyWavelets-SWT (Symlets sym6, Level 4) für jeden Channel.
3. snnTorch-LIF-Layer (~1 M Parameter Netz, 3-Layer Spiking-Encoder).
4. Surrogate-Gradient-Training auf labelten Vol-Burst-Events (BTCUSDT-Historie).
5. Online-Inferenz: Spike-Output triggert Downstream-Pipeline via asyncio-Event.
**Libraries:** `snnTorch`, `Norse`, `PyWavelets`, `PyTorch`.
**Backtesting-Ansatz:** Walk-Forward auf 6 M historischen Tick-Daten; Label = Future-Volatility-Spike > 95-Perzentil in [t, t+5min]; Embargo 30 min zwischen Train/Test-Folds.
**Validierungskriterien:** Precision ≥ 0.6, Recall ≥ 0.4 auf Vol-Spike-Detection; F1 ≥ 0.5; latenz Spike→Trigger ≤ 50 ms.
**Hardware:** RTX 5060 Ti (16 GB VRAM) — ausreichend für 1-M-Parameter-LIF-Netz mit Mini-Batch 256. Training ~6–12 h, Inferenz CPU-fähig.
**Abhängigkeiten:** Orderbook-State-Engine (M4-Vorstufe), Imbalance-Stream-Berechnung.
**Zeitschätzung:** 3–4 Wochen (snnTorch-Training-Pipeline ist Forschungs-Code).
**Risiken:** Surrogate-Gradient-Training instabil; Overfitting auf historische Burst-Pattern; SNN-Inferenz-Latenz auf CPU ungewiss.

#### M2: OFI Cont-Kukanov-Stoikov [L1] [Quick Win]
**Herkunft:** Microstructure-Ökonometrie (Cont, Kukanov, Stoikov 2014, J. Financial Econometrics)
**Kernprinzip:** Über kurze Intervalle sind Preisänderungen primär durch Order-Flow-Imbalance an Best-Bid/Ask getrieben — linear in OFI, Slope umgekehrt proportional zur Markttiefe. Robust intraday und symbol-übergreifend.
**Mathematische Grundlage:**
```
OFI_n = Σ e_n
e_n = I(P^b_n ≥ P^b_{n−1}) · q^b_n
    − I(P^b_n ≤ P^b_{n−1}) · q^b_{n−1}
    − I(P^a_n ≤ P^a_{n−1}) · q^a_n
    + I(P^a_n ≥ P^a_{n−1}) · q^a_{n−1}

Preis-Forecast:  ΔP̂_t = β · OFI_t / λ(depth)
```
Variablen: P^b, P^a = Best-Bid/Ask-Preis; q^b, q^a = Size; I() = Indikator; λ = Markttiefen-Normierung.
**Bybit-Anwendung:** 1-Sekunden-Forecast für Mid-Price-Drift auf BTCUSDT-Perp aus `orderbook.50` Delta-Stream. Filter: nur Short-Entry wenn OFI < −Q90, Long-Entry wenn OFI > +Q90 (rolling 5-min).
**Implementierungsskizze:**
1. Orderbook-State-Engine pflegt Top-1-Bid/Ask laufend.
2. Pro Delta-Update e_n aus obiger Formel berechnen.
3. Rolling-Sum über 1s/5s/30s-Windows.
4. OLS-Regression OFI → ΔMidPrice auf 1-Tag-Window für β-Kalibrierung.
5. Signal: |OFI_5s| > Q90 → Trigger.
**Libraries:** `numpy`, `pandas`, `polars`, `numba` (für rolling-Window-Beschleunigung).
**Backtesting-Ansatz:** Walk-Forward, 30-Tage-Train / 7-Tage-Test, sliding. Metrik: 1s-Forecast-R² + Sharpe der signalbasierten Trades. Look-Ahead-Vermeidung via strict Event-Time Indexing.
**Validierungskriterien:** R²(1s-Forecast) ≥ 0.05; Sharpe (nach 2-bps-Fees) ≥ 1.0; Hit-Rate (sign-Vorhersage) ≥ 53 %.
**Hardware:** Reine CPU (Numpy + Numba ausreichend, < 500 LOC).
**Abhängigkeiten:** Orderbook-State-Engine.
**Zeitschätzung:** 3–5 Tage (Klassiker, gut dokumentiert).
**Risiken:** β instabil bei Regime-Wechsel — Re-Kalibrierung alle 24 h empfohlen. Fee-Schwelle entscheidend (bei Bybit Taker 0.055 % verschluckt Edge bei kleinen OFI-Signalen).

#### M3: Iceberg-Detection via Queue-Replenishment [L1] [Standard]
**Herkunft:** Microstructure (De Prado, Easley, López 2012; Hautsch & Huang 2012)
**Kernprinzip:** Iceberg-Orders zeigen sich als kontinuierliche Größen-Wiederherstellung auf demselben Preislevel nach jedem Hit. Bybit exposiert keine Iceberg-Flags → rein statistische Inferenz via Auto-Korrelation von Level-Sizes nach Trade-Events.
**Mathematische Grundlage:**
```
IcebergScore_p = (Σ_{t=1..N} I(Size_{p,t+δ} ≥ 0.8 · Size_{p,t})) / N_hits
Detection:  if IcebergScore_p > 0.7  AND  N_hits > 5  →  Iceberg vermutet
```
**Bybit-Anwendung:** `orderbook.200`-Delta-Stream → tracke pro Preislevel die Replenishment-Rate nach `publicTrade`-Hits. Iceberg-Level dienen als statistische Support/Resistance-Marker.
**Implementierungsskizze:**
1. Maintain LevelHistory[price] → Liste der (timestamp, size)-Tuple.
2. Bei publicTrade-Event: Size-Reduktion am Level identifizieren.
3. δ = 500 ms später: prüfen, ob Size ≥ 0.8 × Pre-Hit-Size wiederhergestellt.
4. Score akkumulieren; bei Score > 0.7 + N_hits > 5 → Flag.
**Libraries:** `numpy`, `sortedcontainers`.
**Backtesting-Ansatz:** Out-of-Sample-Test ob Iceberg-flagged Levels als Support/Resistance gehalten werden (Bounce-Rate ≥ 60 %).
**Validierungskriterien:** Bounce-Rate ≥ 60 % auf Iceberg-Level innerhalb 5 min nach Touch.
**Hardware:** CPU.
**Abhängigkeiten:** Orderbook.200-Stream-Subscription (separat von orderbook.50).
**Zeitschätzung:** 1 Woche.
**Risiken:** Iceberg-Detection auf Bybit ist 2/3 Daten-Qualität (statistisch, nicht ground-truth). Falsche Positives bei großen MM-Orders, die nicht-iceberg-stuktur replenishen.

---

### Layer L2 — DENOISING (Signal-Rausch-Trennung)

#### M4: Wavelet-Symlet-Denoising (sym4 / sym6 / sym8) [L2] [Standard]
**Herkunft:** Biomedical Signal Processing (EEG-Pipeline, Mallat 1999)
**Kernprinzip:** Diskrete Wavelet-Transformation mit Symlets (sym4–sym8) hat fast linear-phasige Filter → exakte Latenz-Erhaltung. Trennt Market-Maker-Mikrorauschen von Smart-Money-Tape via Soft-Thresholding der Detail-Koeffizienten.
**Mathematische Grundlage:**
```
W_{j,k} = Σ_n x[n] · ψ*_{j,k}[n]
Soft-Threshold:  W'_{j,k} = sign(W_{j,k}) · max(|W_{j,k}| − λ_j, 0)
λ_j = σ_j · √(2 log N)   (Donoho-VisuShrink)
Reconstruction:  x̂[n] = Σ_{j,k} W'_{j,k} · ψ_{j,k}[n]
```
**Bybit-Anwendung:** Orderbuch-Imbalance I(t) = (Σ bid_size − Σ ask_size) / (Σ bid + Σ ask) auf Top-20-Levels aus `orderbook.50`-Stream. DWT mit sym6, 4-Level-Zerlegung. Rekonstruiertes Signal speist Hawkes/SpikeWavformer-Layer.
**Implementierungsskizze:**
1. Imbalance-Stream alle 100 ms aktualisieren (aus Orderbook-State).
2. Sliding-Window-DWT (pywt.swt) mit Window-Length 256 Ticks.
3. Soft-Threshold der Detail-Koeffizienten (Level 1–4) mit VisuShrink-Lambda.
4. Inverse DWT → entrauschtes Imbalance-Signal.
5. Output als Pub/Sub-Stream für L3/L4.
**Libraries:** `PyWavelets` (`pywt.swt`, `pywt.threshold`).
**Backtesting-Ansatz:** Vergleich denoised vs. raw Imbalance als Feature für OFI-Forecast — denoised muss höhere R² liefern. Walk-Forward 14d/3d.
**Validierungskriterien:** R²-Verbesserung gegenüber Roh-Imbalance ≥ 10 %; Latenz < 1 ms pro Update.
**Hardware:** CPU (pywt vektorisiert, < 1 ms pro Update).
**Abhängigkeiten:** Orderbook-State-Engine + Imbalance-Stream.
**Zeitschätzung:** 4–6 Tage.
**Risiken:** Wavelet-Mother-Wahl empirisch; sym4 vs. sym8 hat unterschiedliche Trade-offs (sym4: schärferer Cut, mehr Artefakte; sym8: glatter, höhere Latenz).

#### M5: Fraktionale Differenzierung (FFD, López de Prado) [L2] [Standard]
**Herkunft:** Quant-Finance (López de Prado 2018, Advances in Financial Machine Learning, Kap. 5)
**Kernprinzip:** Integer-Differenzierung erzwingt Stationarität, zerstört aber Memory. Fraktionale Differenzierung d ∈ (0, 1) macht Reihe stationär bei minimalem Memory-Verlust — entscheidend für ML-Features auf Preis- und OI-Zeitreihen mit Long-Memory-Struktur.
**Mathematische Grundlage:**
```
(1 − B)^d X_t = Σ_{k=0}^∞ (−1)^k · C(d,k) · X_{t−k}
mit C(d,k) = d · (d−1) · ... · (d−k+1) / k!

Fixed-Width-Window (FFD):  Weights gekürzt bei |w_k| < τ (τ ≈ 1e−4)
```
**Bybit-Anwendung:** Preprocessing für openInterest, cumulativeFunding und lastPrice vor ML-Modellen (HMM, PatchTST, TimesNet, MOMENT). d-Wert via ADF-Test minimieren (ADF p < 0.05 mit kleinstem d ∈ {0.3, 0.4, 0.5}).
**Implementierungsskizze:**
1. Für jede Zeitreihe Weights w_k berechnen (k = 0 … bis |w_k| < τ).
2. ADF-Test über d-Grid → minimales d wählen.
3. FFD-Output als Feature-Stream cachen.
4. Re-Kalibrierung d alle 30–90 Tage.
**Libraries:** `numpy`, `statsmodels` (ADF-Test), eigene Implementierung (~50 LOC).
**Backtesting-Ansatz:** Forecast-Sharpe-Vergleich bei nachgelagertem PatchTST mit FFD vs. nominal vs. log-returns. Erwartet: FFD-Input liefert +10–20 % Sharpe.
**Validierungskriterien:** ADF p < 0.05 nach FFD; ML-Downstream-Sharpe-Lift ≥ 10 %.
**Hardware:** CPU.
**Abhängigkeiten:** Kline-Backfill (REST).
**Zeitschätzung:** 2–3 Tage.
**Risiken:** d-Re-Kalibrierung vergessen → Stationaritäts-Verlust bei Regime-Shift.

---

### Layer L3 — REGIME (Marktphasen-Erkennung)

#### M6: Shannon-Entropie L2-Orderbuch [L3] [Quick Win]
**Herkunft:** Informationstheorie / Thermodynamik (Gould et al. 2013, ECB-WP zu LOB-Entropie)
**Kernprinzip:** H = −Σ p_i log p_i über die Größen-Verteilung der Top-N Bid+Ask-Levels quantifiziert Heterogenität. Hohe H = chaotisch, random-walk-nah, kein Edge. Niedrige H = institutionelle Synchronisation, Edge-Fenster (Greenlight).
**Mathematische Grundlage:**
```
p_i = size_i / Σ size            (i = 1 … N Levels)
H_bid = −Σ p_i log_2(p_i)
H_ask = −Σ p_i log_2(p_i)
H_combined = (H_bid + H_ask) / 2

KL-Divergenz für Asymmetrie:  D(P_bid ‖ P_ask) = Σ p_i log(p_i / q_i)
```
**Bybit-Anwendung:** `orderbook.50`-Stream → alle 100 ms H berechnen; gleitendes 24-h-Quantil bilden. Greenlight: H < Q5 → Direction-Trade erlaubt (gefolgt von Hawkes-/OFI-Bestätigung).
**Implementierungsskizze:**
1. Bei jedem Orderbook-Update: Sizes der Top-20-Levels normalisieren auf Probability.
2. Shannon-Formel (Numpy: `-np.sum(p * np.log2(p + 1e−12))`).
3. Rolling-Quantile über 24 h.
4. Output: Bool-Greenlight-Flag.
**Libraries:** `numpy`, `polars`.
**Backtesting-Ansatz:** A/B-Test: Trade-Strategie mit Entropie-Gate vs. ungefiltert. Erwartung: Win-Rate-Lift + 2–4 pp.
**Validierungskriterien:** Win-Rate-Lift bei nachgelagertem OFI-Trade ≥ 2 pp.
**Hardware:** CPU (O(N) pro Update).
**Abhängigkeiten:** Orderbook-State-Engine.
**Zeitschätzung:** 2 Tage.
**Risiken:** Q5-Schwellen empirisch — bei Regime-Shift Re-Kalibrierung.

#### M7: Permutation Entropy (Bandt-Pompe) [L3] [Quick Win]
**Herkunft:** Nichtlineare Dynamik (Bandt & Pompe 2002, Phys. Rev. Lett. 88)
**Kernprinzip:** Ordnungs-basierte Komplexitätsmessung. Robust gegen Outlier und Skalierung. Niedrige PE = strukturiertes Regime = höhere Edge-Wahrscheinlichkeit. Empirisch 34 % höhere Vol-Spike-Detection als GARCH.
**Mathematische Grundlage:**
```
Für Embedding (m, τ):  Ordinal-Muster π von (x_t, x_{t+τ}, ..., x_{t+(m−1)τ})
PE_m = −Σ_π p(π) · log p(π)            Summe über m! Permutationen
Normalisiert:  PE_norm = PE_m / log(m!)   ∈ [0, 1]
```
**Bybit-Anwendung:** PE auf `tickers.lastPrice` (m = 4, τ = 1) mit rolling 100-Tick-Window. Trading-Greenlight: PE < Median(PE_24h).
**Implementierungsskizze:**
1. Rolling 100-Tick-Window aus tickers-Stream.
2. ordpy.permutation_entropy(window, dx=4, taux=1).
3. 24-h-Median-Tracker.
4. Output: Greenlight-Bool.
**Libraries:** `ordpy` (oder `antropy`).
**Backtesting-Ansatz:** Walk-Forward, Strategie mit PE-Gate vs. ohne. 6 M Daten.
**Validierungskriterien:** PE-Drop unter Median korreliert mit Vol-Cluster in [t, t+15min] mit ρ ≥ 0.3.
**Hardware:** CPU (O(N log N)).
**Abhängigkeiten:** Tickers-Stream.
**Zeitschätzung:** 1–2 Tage.
**Risiken:** m-Parameter-Sensitivität — m = 4 ist Standard, m = 5 langsamer, m = 3 zu grob.

#### M8: BOCPD auf openInterest [L3] [Quick Win]
**Herkunft:** Bayes-Statistik (Adams & MacKay 2007, arXiv:0710.3742)
**Kernprinzip:** Online-Bayes-Inferenz über die Position des letzten Strukturbruchs. Run-Length-Posterior über Message-Passing. Kein Lookback-Bias, exakt.
**Mathematische Grundlage:**
```
P(r_t | x_{1:t}) ∝ Σ_{r_{t−1}} P(r_t | r_{t−1}) · P(x_t | r_{t−1}, x) · P(r_{t−1} | x_{1:t−1})

Hazard h(r) = const (geometrische Run-Length)
Predictive:  P(x_t | r_{t−1}, x) = Student-t (für unbekannte Varianz)
```
**Bybit-Anwendung:** Strukturbruch in OI-Time-Series auf BTCUSDT → Regime-Filter für Trend-Following. `tickers.openInterest` live; Backfill via REST.
**Implementierungsskizze:**
1. OI-Stream aus tickers (100 ms) auf 5-min-Buckets aggregieren.
2. `bayesian-changepoint-detection`-PyPI mit Student-t-Likelihood.
3. Hazard-Prior auf erwartete Regime-Dauer (z. B. 1/120 für ~10 h).
4. Output: P(Change-Point in letzten 5 min) > 0.5 → Strukturbruch-Alert.
**Libraries:** `bayesian-changepoint-detection`, `scipy.stats`.
**Backtesting-Ansatz:** Detection-Latenz auf historische Mark-OI-Strukturbrüche (annotiert per Eyeball oder z-Score).
**Validierungskriterien:** Detection-Latenz ≤ 2 min nach echtem Bruch; False-Positive-Rate ≤ 10 %/Tag.
**Hardware:** CPU.
**Abhängigkeiten:** Tickers-Stream + OI-Historie.
**Zeitschätzung:** 3–4 Tage.
**Risiken:** Hazard-Prior-Sensitivität — falsch gewählt → entweder zu viele FPs oder verpasste Brüche.

#### M9: HMM (Vola-OFI-Funding, 3-state) [L3] [Standard]
**Herkunft:** Bayes-Statistik / Ökonometrie (Hamilton 1989; Rabiner 1989)
**Kernprinzip:** Latente Marktphasen (Trend-Up, Mean-Revert, High-Vol-Crash) als versteckte Zustände. Emission-Wahrscheinlichkeiten über realized vol, OFI-Sign, fundingRate. Viterbi für Online-Decoding.
**Mathematische Grundlage:**
```
P(z_t | x_{1:t}) ∝ Σ_{z_{t−1}} P(z_t | z_{t−1}) · P(x_t | z_t) · α_{t−1}(z_{t−1})

Forward-Algorithm:  α_t(z) = P(x_t | z) · Σ_{z'} P(z | z') · α_{t−1}(z')
Baum-Welch:  Parameter-MLE (transition matrix, emission)
Viterbi:  arg max z_{1:T}  P(z_{1:T} | x_{1:T})
```
**Bybit-Anwendung:** 3-State-HMM (Trend / Mean-Revert / High-Vol) auf [realized_vol_5min, sign(OFI_5min), fundingRate]. State-Posterior als Gating-Feature für Strategie-Aktivierung (z. B. Mean-Revert-Strategien NUR in State 2).
**Implementierungsskizze:**
1. Feature-Vektor [vol, OFI, funding] alle 5 min.
2. `hmmlearn.GaussianHMM(n_components=3)` Baum-Welch auf 6 M Historie.
3. Online-Viterbi für Live-State.
4. Walk-Forward Re-Train alle 30 Tage.
**Libraries:** `hmmlearn`, `numpy`.
**Backtesting-Ansatz:** Walk-Forward + Combinatorial Purged CV (López de Prado).
**Validierungskriterien:** State-stable über ≥ 80 % der Bars (kein Flapping); Strategie-Win-Rate pro State signifikant unterschiedlich (Chi² p < 0.01).
**Hardware:** CPU.
**Abhängigkeiten:** OFI-Stream (M2), Funding-Stream.
**Zeitschätzung:** 1 Woche.
**Risiken:** Label-Switching zwischen Re-Trains — fixe Transition-Priors oder Label-Alignment via State-Mean.

#### M10: MF-DFA Multifractal (Diagnose) [L3] [Standard]
**Herkunft:** Statistische Physik / Geophysik (Kantelhardt et al. 2002)
**Kernprinzip:** Skalierungs-Exponent h(q) für verschiedene Momenten-Ordnungen q quantifiziert Multifraktalität. Δh = h(q_min) − h(q_max) misst Heterogenität; groß in ineffizienten/Regime-Switch-Phasen.
**Mathematische Grundlage:**
```
F_q(s) = { (1 / 2N_s) · Σ [F²(ν, s)]^{q/2} }^{1/q}  ∝  s^{h(q)}
τ(q) = q · h(q) − 1
Δh = h(q_min) − h(q_max)
```
**Bybit-Anwendung:** Auf 1-min Kline-Returns rolling N=2048, q ∈ [−5, 5], s ∈ [16, 256]. Δh-Spike > z=2 → Regime-Change-Alarm.
**Implementierungsskizze:**
1. Returns aus Kline-1min.
2. `MFDFA`-PyPI mit q-Grid und Scale-Grid.
3. Fit h(q) per OLS; Δh-Tracker.
4. Output: Bool-Flag Regime-Change.
**Libraries:** `MFDFA`, `numpy`.
**Backtesting-Ansatz:** Korrelation Δh-Spike mit nachgelagertem Drawdown/Strategy-Sharpe-Reduktion.
**Validierungskriterien:** Δh-Spike erkennt 70 % der historisch annotierten Regime-Shifts mit Vorlauf ≤ 30 min.
**Hardware:** CPU (~200 ms pro Fenster).
**Abhängigkeiten:** Kline-Backfill.
**Zeitschätzung:** 4–5 Tage.
**Risiken:** Diagnose-Tool, nicht Entry-Trigger — nur in Ensemble (mit TDA + RQA) sinnvoll.

#### M11: TDA / Persistent Homology [L3] [Standard]
**Herkunft:** Algebraische Topologie (Gidea & Katz 2017, arXiv:1703.04385)
**Kernprinzip:** Aus rollender Multi-Asset-Returns-Matrix wird Punktwolke gebaut; Vietoris-Rips-Filtration berechnet Geburts-/Sterbe-Zeiten topologischer Features (Löcher H_1). L¹-Norm der Persistence Landscape steigt vor Crashes signifikant.
**Mathematische Grundlage:**
```
Persistence Landscape:  λ_k(t) = max_k-max{ min(t − b_i, d_i − t), 0 }
L¹-Norm:  L¹(λ) = Σ_k ∫ |λ_k(t)| dt
```
**Bybit-Anwendung:** Rolling 100-Bar-Fenster über (BTC, ETH, SOL, BNB, XRP) 1-min Returns. L¹-Spike > z=3 → Risk-Off-Signal (Hedge / Reduce Position).
**Implementierungsskizze:**
1. Multi-Symbol-Returns-Matrix aus REST-Kline.
2. `ripser` oder `gudhi` für Persistence.
3. `persim` für Landscape-Berechnung.
4. L¹-z-Score-Tracker.
**Libraries:** `ripser`, `gudhi`, `persim`, `giotto-tda`.
**Backtesting-Ansatz:** Korrelation L¹-Spike → nachfolgende Max-DD in [t, t+24h]. Erwartet: ρ ≥ 0.4.
**Validierungskriterien:** Korrelation L¹-z-Score → Forward-24h-DD ρ ≥ 0.4; Risk-Off-Trigger reduziert Max-DD um ≥ 20 %.
**Hardware:** CPU (ripser++ rechnet PH in < 100 ms für 100×5-Matrizen).
**Abhängigkeiten:** Multi-Symbol-Kline-Backfill.
**Zeitschätzung:** 1 Woche.
**Risiken:** Schwellen empirisch; Choice-of-Symbols beeinflusst Topologie.

#### M12: RQA (Recurrence Quantification Analysis) [L3] [Standard]
**Herkunft:** Nichtlineare Dynamik (Eckmann/Kamphorst/Ruelle; Strozzi 2005)
**Kernprinzip:** Phasenraum-Rekonstruktion (Takens-Einbettung) erzeugt Trajektorie; Recurrence Plot R_{ij} = Θ(ε − ‖x_i − x_j‖). Metriken DET (Determinismus), LAM (Laminarität) detektieren kritische Regimes vor Phasenübergängen.
**Mathematische Grundlage:**
```
R_{ij} = Θ(ε − ‖x_i − x_j‖)
DET = Σ_{l ≥ l_min} l · P(l) / Σ_l l · P(l)         (Determinismus)
LAM = Σ_{v ≥ v_min} v · P(v) / Σ_v v · P(v)         (Laminarität)
```
**Bybit-Anwendung:** 5-min Mid-Price-Returns BTCUSDT/ETHUSDT, Embedding-Dim m=3, Delay τ via Mutual Information. DET-Spike + LAM-Spike → Laminar-Phase = Konsolidierung vor Breakout.
**Implementierungsskizze:**
1. Returns aus Kline-5min.
2. Mutual-Information-Test für optimales τ.
3. `pyrqa` mit JIT-CUDA-Backend.
4. Rolling RQA über 500-Bar-Window.
**Libraries:** `pyrqa`.
**Backtesting-Ansatz:** DET-Spike-Forward-Breakout-Korrelation.
**Validierungskriterien:** DET > 0.7 mit anschließendem |Return| > 1 % in 1 h: Hit-Rate ≥ 55 %.
**Hardware:** CPU oder optional GPU (pyrqa hat CUDA-Backend; RTX 5060 Ti unterstützt CUDA 12).
**Abhängigkeiten:** Kline-Stream.
**Zeitschätzung:** 4–5 Tage.
**Risiken:** ε-Schwellen-Sensitivität; Takens-Embedding-Dimension Empirisch.

#### M13: Cross-Sectional Ergodicity-Reversion Z-Score [L3] [Standard]
**Herkunft:** Reduktion aus Quantum-Coupled-Wave; klassisch Cross-Sectional-Mean-Reversion (Lo & MacKinlay 1990)
**Kernprinzip:** Ergodizitätsverletzung: Symbole mit zeit-gemitteltem Return weit weg vom Ensemble-Mittel (über alle Symbole) tendieren zur Mean-Reversion. Vereinfachte Implementierung der ursprünglichen Quantum-Methode unter Entfernung des Schrödinger-Wrappers.
**Mathematische Grundlage:**
```
E_t[X_i] = (1/W) Σ_{s=t−W}^{t} R_{i,s}       (zeitlicher Mittelwert von Symbol i)
⟨X⟩_t  = (1/N) Σ_{j=1}^{N} R_{j,t}            (Ensemble-Mittelwert)
z_{i,t} = (E_t[X_i] − ⟨X⟩_t) / σ_cross
```
**Bybit-Anwendung:** Multi-Symbol-Panel (Top-20 USDT-Perps) aus tickers-WS. Z-Score |z| > 2.5 + Renyi-TE(BTC → Alt) > 0.05 + HMM-State ≠ Crash → Mean-Reversion-Entry gegen Z.
**Implementierungsskizze:**
1. Synchroner Multi-Symbol-Snapshot-Loop (asyncio).
2. Rolling 1h Returns pro Symbol → E_t[X_i].
3. Per Bar Cross-Sectional Mean ⟨X⟩.
4. Z-Score Matrix; Trigger bei |z| > 2.5.
**Libraries:** `pandas`, `polars`, `numpy`.
**Backtesting-Ansatz:** Walk-Forward Long-Short-Portfolio (long bottom-z, short top-z); Sharpe-Berechnung nach Fees.
**Validierungskriterien:** Sharpe ≥ 1.0 nach Fees (Bybit Maker 0.02 % / Taker 0.055 %); Hit-Rate ≥ 53 %.
**Hardware:** CPU.
**Abhängigkeiten:** Multi-Symbol-Panel-Infrastruktur.
**Zeitschätzung:** 1 Woche.
**Risiken:** Survivorship-Bias bei Symbol-Universum; Delisting-Daten respektieren.

---

### Layer L4 — PATTERN (Mustererkennung, Alignment, Forecasting)

#### M14: Hawkes Spektralradius ρ(Φ) (6-D Orderbook + Liquidation coupled) [L4] [Moonshot]
**Herkunft:** Geophysik / Point-Process-Theorie (Hawkes 1971; Bacry/Mastromatteo/Muzy 2015; Achab et al. 2017)
**Kernprinzip:** Orderbuch + Liquidationen als multi-dimensional selbst-erregender Punktprozess. Branching Matrix Φ̄_ij = α_ij beschreibt endogene Kausalität. Spektralradius ρ(Φ) → 1 markiert kritischen Zustand: minimaler Trigger löst Kaskade aus (empirisch 70–90 % des HFT-Flows endogen).
**Mathematische Grundlage:**
```
λ_i(t) = μ_i + Σ_j ∫_0^t φ_{ij}(t − s) dN_j(s)
φ_{ij}(t) = α_{ij} · β_{ij} · exp(−β_{ij} · t)

Branching-Matrix:  Φ̄_{ij} = α_{ij}
Spektralradius:  ρ(Φ) = max |eigenvalue(Φ̄)|

Kritikalität:  ρ(Φ) → 1  ⇔  Kaskaden-Regime
Single-channel Variante:  n_∞ = α / β  (branching ratio)
```
Events (6-D): MO+ (Market Buy), MO− (Market Sell), LO+ (Limit Bid Add), LO− (Limit Ask Add), CX+ (Cancel Bid), CX−. Plus exogene Liquidations-Channels (Long-Liq, Short-Liq).
**Bybit-Anwendung:** Aus `publicTrade.{symbol}` + `orderbook.50` Deltas + `allLiquidation` die 6 + 2 Event-Typen extrahieren; rollend (5-min-Window) MLE der Matrix Φ. Wenn ρ(Φ) > 0.9 → Kaskaden-Alarm: Position-Sizing reduzieren ODER Momentum-Entry in Klimax-Richtung.
**Implementierungsskizze:**
1. Event-Extractor: trades & orderbook deltas → kategorisierte Event-Streams.
2. `tick`-Library (`tick.hawkes.HawkesExpKern`) für MLE-Fit.
3. Rolling 5-min-Window, Re-Fit alle 30 s.
4. Spektralradius via numpy.linalg.eigvals.
5. Coupling: Liquidations als exogene Spike-Inputs in 6-D-System.
**Libraries:** `tick` (Hawkes-MLE), `hawkeslib`, `numpy`, `scipy.optimize`.
**Backtesting-Ansatz:** Kaskaden-Episoden in 5y BTCUSDT-Historie annotieren (Flash-Crashes); ρ-Steigung vor Episode als Frühindikator messen.
**Validierungskriterien:** ρ steigt ≥ 0.7 mindestens 30 s vor 80 % der historischen Kaskaden; False-Positive-Rate ≤ 2/Tag.
**Hardware:** CPU für 1–2-D Variante; RTX 5060 Ti optional für GPU-MLE (tick unterstützt OpenMP, aber kein CUDA — die GPU bleibt frei für andere Modelle).
**Abhängigkeiten:** Orderbook-State + Trade-Stream + Liquidation-Buffer.
**Zeitschätzung:** 4–5 Wochen (volle 6-D); 1 Woche für 1-D-Variante als Sprungbrett.
**Risiken:** 6-D MLE mit 36+ Parametern numerisch anspruchsvoll — Pre-Regularisierung oder Reduktion auf 2–3 Event-Typen empfohlen. WS-Reconnect-Dropouts korrumpieren Inferenz → robust gegen Lücken machen.

#### M15: Gutenberg-Richter b + Omori p,c,k [L4] [Quick Win]
**Herkunft:** Seismologie (Gutenberg-Richter 1944; Omori-Utsu 1894/1961; Lillo & Mantegna 2003)
**Kernprinzip:** Liquidationen folgen Erdbeben-Statistik: Magnituden log₁₀ N(≥M) = a − bM (Gutenberg-Richter); Aftershock-Rate n(t) = K/(t+c)^p (Omori-Utsu). Nach Mainshock kann Aftershock-Rate vorhergesagt und Mean-Reversion-Entry getimt werden, bevor das Liquidations-Echo abklingt.
**Mathematische Grundlage:**
```
log₁₀ N(≥ M) = a − b · M                  (Gutenberg-Richter)
λ(t | H_t) = K / (t − t_main + c)^p        (Omori-Utsu)

Mainshock-Schwelle:  v_USD > Q99(rolling 24h)
b-Wert via MLE:  b̂ = log₁₀(e) / (M̄ − M_min)
```
**Bybit-Anwendung:** `allLiquidation`-Stream auf 1-s-Buckets aggregieren; Mainshock = größtes Liq-Event in 5 min; Omori-Fit für nächste 30 min Aftershocks. b-Wert < 1 → unausgewogene Volatilität → Trend-Fortsetzung.
**Implementierungsskizze:**
1. Liquidation-Event-Buffer (Sliding 1000-Events).
2. Magnitude M = log₁₀(v_USD) berechnen.
3. b-Wert MLE alle 5 min (Aki 1965-Schätzer).
4. Mainshock-Detektion via Q99-Schwelle.
5. Nach Mainshock: scipy.curve_fit für (K, c, p).
6. Forward-Prediction λ(t) für nächste 30 min.
**Libraries:** `scipy.optimize`, `numpy`.
**Backtesting-Ansatz:** Mainshock-Episoden in 1 y Bybit-Liquidation-Historie; b-Wert-Drift vor Episode prüfen; Omori-Forecast vs. tatsächliche Aftershock-Rate (MSE).
**Validierungskriterien:** b-Wert-Drift erkennt 70 % der Mainshocks ≥ 10 min vorlauf; Omori-Forecast-MSE < Baseline (constant rate).
**Hardware:** CPU.
**Abhängigkeiten:** Liquidation-Event-Buffer.
**Zeitschätzung:** 1 Woche.
**Risiken:** b-Wert-Schätzung instabil bei kleinen Stichproben (< 50 Events).

#### M16: TFSAX + Smith-Waterman Alignment [L4] [Moonshot]
**Herkunft:** Bioinformatik / Genomik (Smith & Waterman 1981; SAX: Lin et al. 2007; TFSAX: Yu et al. 2019)
**Kernprinzip:** Preiszeitreihe wird via PAA + z-Norm + Gauß-Bins in Symbolsequenz transformiert; TFSAX fügt Trend-Distanz- und Trend-Form-Faktor hinzu. Smith-Waterman findet lokal optimale Alignments mit Insertions/Deletions → toleriert zeitliche Verzerrungen, an denen Euklid-Distanz scheitert.
**Mathematische Grundlage:**
```
PAA:  C̄_i = (w/n) · Σ_{j=n/w·(i−1)+1}^{n/w·i} c_j
SAX:  symbol_i = bin(C̄_i)   mit gleichwahrscheinlichen Gauß-Bins

Smith-Waterman:
H(i,j) = max{ 0,
               H(i−1, j−1) + s(a_i, b_j),
               H(i−1, j) − d,
               H(i, j−1) − d }
```
**Bybit-Anwendung:** 24h Kline-1min-Returns → TFSAX-Sequenz Länge 1440 mit Alphabet |A|=5; in 5y Bybit-Historie nach ähnlichen Sequenzen suchen → konditionale Forward-Return-Verteilung der Top-k Matches.
**Implementierungsskizze:**
1. Historische Sequenz-Library aus 5y Kline-1min, segmentiert in überlappende 24h-Fenster.
2. TFSAX-Encoding (saxpy oder tslearn + Trend-Faktor).
3. Smith-Waterman-Alignment (Biopython `Bio.pairwise2` oder eigene GPU-Implementierung).
4. Top-k-Match-Retrieval; konditionale Distribution der Forward-1h-Returns.
5. Entry-Signal: Match-Score > 0.75 (normalisiert) + Forward-Mean > Threshold.
**Libraries:** `saxpy`, `tslearn`, `Biopython`, optional GPU-Smith-Waterman (e.g., `parasail`).
**Backtesting-Ansatz:** Walk-Forward, Library-Cutoff strikt vor Test-Window. Combinatorial Purged CV.
**Validierungskriterien:** Hit-Rate Top-k Match-Direction ≥ 56 %; Sharpe ≥ 1.2 nach Fees.
**Hardware:** CPU für Encoding; GPU (RTX 5060 Ti) für SW-Library-Match bei großer Library (parasail mit CUDA).
**Abhängigkeiten:** Kline-Backfill (5y), Sequenz-Library-Storage.
**Zeitschätzung:** 3–4 Wochen (Library-Aufbau ist groß).
**Risiken:** Schwellen empirisch; Library-Size vs. Match-Latenz-Trade-off.

#### M17: Renyi-Transfer-Entropy Lead-Lag-Graph [L4] [Standard]
**Herkunft:** Informationstheorie (Schreiber 2000; Renyi 1961; Keskin & Aste 2020)
**Kernprinzip:** Renyi-Transfer-Entropy verallgemeinert Schreiber-TE und gewichtet Tail-Events stärker (q > 1) → fängt non-lineare extreme Kopplung. Asymmetrie T_X→Y ≠ T_Y→X liefert gerichteten Informationsfluss.
**Mathematische Grundlage:**
```
T^q_{Y→X} = (1/(1−q)) · log Σ p(x_{n+1}, x_n^{(k)})
              · [ Σ p(y_n^{(l)} | x_n^{(k)}) · p(x_{n+1} | x_n^{(k)}, y_n^{(l)})^{q−1} ]
              / Σ p(x_{n+1} | x_n^{(k)})^q
```
**Bybit-Anwendung:** 1-min Returns Top-20 Bybit-Perps; rollend 4h-Fenster; gerichtete Kanten T > 0.05 Bit bilden Lead-Lag-Graph. BTC führt typisch → Alt-Trade nach BTC-Move mit 30–60 s Lag.
**Implementierungsskizze:**
1. Multi-Symbol-Returns-Matrix.
2. `IDTxl` oder `PyInform` für Renyi-TE.
3. Lead-Lag-Graph alle 1 min aktualisieren.
4. Trade-Signal: BTC bewegt > σ, Alt mit höchstem T-Score → Entry.
**Libraries:** `IDTxl`, `PyInform`.
**Backtesting-Ansatz:** Walk-Forward Multi-Symbol-Strategie; Anti-Crowding mit L/S-Ratio-Filter (M21).
**Validierungskriterien:** Alt-Forward-Return-Korrelation mit BTC-Move bei T-Edge > 0.05: ρ ≥ 0.3.
**Hardware:** CPU (Latenz ~50 ms bei 20×20 Matrix).
**Abhängigkeiten:** Multi-Symbol-Kline-Stream.
**Zeitschätzung:** 1 Woche.
**Risiken:** Renyi-q-Parameter-Sensitivität; rauschig bei kleinen Stichproben.

#### M18: PatchTST Funding-Cycle-Forecast [L4] [Standard]
**Herkunft:** Deep Learning (Nie et al. 2023, ICLR)
**Kernprinzip:** Zeitreihe in Subseries-Patches segmentieren, channel-independent über Transformer. Quadratische Attention-Reduktion → lange Lookbacks möglich. Ideal für 8h-Funding-Zyklen.
**Mathematische Grundlage:**
```
x_p ∈ R^{P × N}        P = Patch-Länge, N = ⌊(L−P)/S⌋ + 2
Attention auf Patches statt Time-Steps:
Attn(Q, K, V) = softmax(QK^T / √d_k) · V
Channel-Independence:  jede Time-Series unabhängig forecasted
```
**Bybit-Anwendung:** Predict 5-min-Return auf BTCUSDT 30 min vor Funding-Settlement; channel-independence erlaubt Cross-Symbol-Transfer. Input: FFD-präparierte Kline + fundingRate + openInterest.
**Implementierungsskizze:**
1. FFD-präparierte Multi-Channel-Input ([price, OI, funding]).
2. Patch-Length P=16, Stride S=8, Lookback L=512.
3. PatchTST-Modell (kleiner Encoder, 4 Layers, 256-dim).
4. Training auf 3y BTCUSDT-Historie.
5. Online-Forecast alle 5 min.
**Libraries:** `PyTorch`, offizielle PatchTST-Repo (`yuqinie98/PatchTST`).
**Backtesting-Ansatz:** Walk-Forward, Train 12 M / Test 1 M, sliding.
**Validierungskriterien:** Direktional-Accuracy ≥ 55 %; Sharpe (Trade-Signal-basiert) ≥ 1.0.
**Hardware:** RTX 5060 Ti 16 GB — locker ausreichend (Modell-Size ~5–10 M Parameter; Training ~4–8 h; Inferenz Batch 1 < 50 ms).
**Abhängigkeiten:** FFD (M5), Kline-Backfill, Funding-History.
**Zeitschätzung:** 2 Wochen.
**Risiken:** Overfitting (klassisch bei Transformern auf Finanzdaten); strikt Walk-Forward + Optuna-Hyperparam-Suche.

#### M19: TimesNet 2D-Periodicity [L4] [Standard]
**Herkunft:** Deep Learning (Wu et al. 2023, ICLR)
**Kernprinzip:** 1D-Zeitreihe wird via FFT in dominante Perioden zerlegt und in 2D-Tensoren gefaltet (Inter-Period × Intra-Period). 2D-CNN-Blocks erkennen zyklische Muster, die 1D-Models verpassen. Perfekt für 8h-Funding-Zyklen + 24h-Tagesrhythmus + Wochenzyklus.
**Mathematische Grundlage:**
```
X_{2D} = Reshape_{p_i, f_i}(X_{1D})       mit p_i = Top-k-FFT-Frequenzen
2D-Inception-Block über X_{2D}
Output = Σ amplitude_i · CNN_i(X_{2D,i})
```
**Bybit-Anwendung:** Multi-Period-BTCUSDT auf 5-min-Kline (Wochen Lookback). Input: OHLCV + fundingRate als zusätzlicher Channel.
**Implementierungsskizze:**
1. Kline 5-min Multi-Channel-Input.
2. FFT für Top-3-Perioden (erwartet: 8h, 24h, 168h).
3. 2D-Reshape, Inception-CNN.
4. Output: 1h-Forecast.
**Libraries:** `PyTorch`, offizielle TimesNet-Repo.
**Backtesting-Ansatz:** Walk-Forward; Forecast-Sharpe-Vergleich mit Naive-Baseline und PatchTST.
**Validierungskriterien:** Outperformance PatchTST in 8h-Period-Forecast-MSE.
**Hardware:** RTX 5060 Ti ausreichend (~5–10 M Parameter).
**Abhängigkeiten:** FFD (M5).
**Zeitschätzung:** 2 Wochen.
**Risiken:** FFT-Period-Detection rauschig bei kurzen Trainingshistorien.

#### M20: MOMENT Foundation Model (Zero-Shot) [L4] [Standard]
**Herkunft:** Deep Learning / Foundation Models (Goswami et al. 2024, ICML, CMU/Auton Lab)
**Kernprinzip:** Pre-trained Time-Series Foundation Model. Erlaubt Zero-Shot-Forecasting auf unbekannte Symbole — kritisch für Altcoin-Rotation auf Bybit, wo neue Listings ständig erscheinen.
**Mathematische Grundlage:**
```
Encoder-only T5-Architektur mit Patch-Tokenisierung
Reversible Instance Normalization (RevIN):
  x' = (x − μ) / σ              (vor Modell)
  ŷ = ŷ' · σ + μ               (nach Modell)
```
**Bybit-Anwendung:** Neulisting auf Bybit → Forecast ohne Fine-Tuning für erste 24 h. Fine-Tune später auf RTX 5060 Ti für etablierte Symbole.
**Implementierungsskizze:**
1. HuggingFace `AutonLab/MOMENT-1-base` laden.
2. Input Kline-1min, FFD-präpariert.
3. Zero-Shot-Forecast für 60-min-Horizon.
4. Optional Fine-Tune via LoRA auf RTX 5060 Ti.
**Libraries:** `transformers`, `momentfm`.
**Backtesting-Ansatz:** Zero-Shot Out-of-Sample auf 5 Symbolen (BTC, ETH, SOL, BNB, XRP). MASE/MAPE vs. Naive.
**Validierungskriterien:** MASE < 1.0 zero-shot; Sharpe ≥ 0.8 in signalbasiertem Trading.
**Hardware:** RTX 5060 Ti 16 GB — MOMENT-base (~110 M Parameter) komfortabel; MOMENT-large (~341 M) knapp aber möglich mit FP16/Quantisierung.
**Abhängigkeiten:** Kline-Backfill, FFD (M5).
**Zeitschätzung:** 1–2 Wochen (Zero-Shot trivial, Fine-Tune länger).
**Risiken:** Zero-Shot-Performance möglicherweise unter SOTA fine-tuned.

#### M21: Long/Short-Ratio Smart-Money-Divergenz [L4] [Quick Win]
**Herkunft:** Bybit-spezifisch (Bybit Docs `/v5/market/long-short-ratio`; analog Han et al. 2022)
**Kernprinzip:** Bybit's Long/Short-Ratio aggregiert über Konten (nicht Volumen). Bei extremem Retail-Skew (buyRatio > 0.75) UND gegenläufiger Preisbewegung → kleine Zahl institutioneller Gegenpositionen → Smart-Money-Signal.
**Mathematische Grundlage:**
```
Divergenz_t = sign(Return_{1h}) − sign(buyRatio − 0.5)
Signal:  Divergenz < 0  AND  |buyRatio − 0.5| > 0.25
```
**Bybit-Anwendung:** Counter-Trend-Entry: wenn Retail extrem long aber Preis fällt → Smart-Money-Seite folgen.
**Implementierungsskizze:**
1. REST `/v5/market/long-short-ratio?period=1h` alle 5 min pollen.
2. Divergenz-Score; Schwelle |buyRatio − 0.5| > 0.25 + Sign-Mismatch.
3. Anti-Crowding-Filter auch für M17 (Renyi-TE-Trades).
**Libraries:** `httpx`, `pandas`.
**Backtesting-Ansatz:** Walk-Forward; Forward-4h-Return-Korrelation mit Divergenz-Score.
**Validierungskriterien:** Hit-Rate Counter-Trade ≥ 54 %; Sharpe ≥ 0.8.
**Hardware:** CPU (trivial).
**Abhängigkeiten:** L/S-Ratio-Poller.
**Zeitschätzung:** 1–2 Tage.
**Risiken:** Ratio ist konten-aggregiert (nicht volumen-gewichtet) → Whale-Trades unter-repräsentiert. Threshold-Kalibrierung empirisch.

---

### Layer L5 — RISK (Sizing, Stops, Pre-Execution-Filter)

#### M22: Funding-Rate-Clamp Pressure-Release [L5] [Quick Win — Top-Priorität]
**Herkunft:** Bybit-spezifische Mechanik (Bybit Help Center "Introduction to Funding Rate"; Palepu 2021)
**Kernprinzip:** Bybit clamped die Funding Rate F bei ±0.05 % für BTCUSDT via `F = P + clamp(I − P, 0.05%, −0.05%)`. Bei extremer Marktdivergenz wird der "echte" Premium-Druck gestaut und entlädt sich rhythmisch nach Settlement. Edge ist mechanisch + deterministisch (00/08/16 UTC).
**Mathematische Grundlage:**
```
F_t = P_t + clamp(I_t − P_t,  −0.05%,  +0.05%)
Pressure_t = (I_t − P_t) − clamp(I_t − P_t, ±0.05%)
                                              ↑ gestauter Rest

Signal:  |Pressure_t| > 2σ(Pressure_{24h})
Settlement-Window:  T_settlement − t < 30 min
```
**Bybit-Anwendung:** Long-Mean-Reversion-Trade in den 30 min nach Settlement, wenn aufgestaute Negative-Premium-Pressure die Clamp-Grenze überschritten hatte (Shorts haben "zu wenig" gezahlt → Reversion kommt).
**Implementierungsskizze:**
1. Tickers-Stream → Pressure_t alle 100 ms.
2. Rolling 24h-σ-Tracker.
3. Settlement-Scheduler-Trigger (Cron auf 00/08/16 UTC).
4. Entry: T − t < 30 min UND |Pressure| > 2σ UND PE-Greenlight.
5. Exit: T + 10 min ODER Pressure → 0.
**Libraries:** `numpy`, `pandas`.
**Backtesting-Ansatz:** Walk-Forward, 6 M Daten, 3 Settlements/Tag = ~540 Episoden.
**Validierungskriterien:** Sharpe ≥ 1.5; Hit-Rate ≥ 56 %; Max-DD < 10 %.
**Hardware:** CPU (trivial).
**Abhängigkeiten:** Tickers-Stream + Settlement-Scheduler.
**Zeitschätzung:** 3–5 Tage. **DAS ERSTE BACKTESTBARE EDGE-MODUL.**
**Risiken:** Bybit kann Clamp-Bounds ändern (passierte ~jährlich) → konfigurierbar implementieren. Funding-Frequenzen pro Symbol unterschiedlich (BTCUSDT: 8 h; einige Alts: 1 h/4 h).

#### M23: Mark-Index Basis Settlement Convergence [L5] [Quick Win]
**Herkunft:** Bybit-spezifisch (Bybit Help Center "Mark Price Calculation")
**Kernprinzip:** Basis = markPrice − indexPrice. Persistent positive Basis → Perp überbewertet → Funding zieht Basis Richtung 0 vor Settlement. Convergence-Trade in Window [Settlement − 60 min, Settlement].
**Mathematische Grundlage:**
```
Basis_t = (markPrice_t − indexPrice_t) / indexPrice_t

Signal:  Basis_t > 0.0008  AND  T_settlement − t < 1h  →  Short Perp
         Basis_t < −0.0008 AND  T_settlement − t < 1h  →  Long Perp
```
**Bybit-Anwendung:** Reiner Perp-Short (oder Long) bei extremer Basis, optional gehedged via Spot.
**Implementierungsskizze:**
1. Tickers-Stream → Basis_t.
2. Settlement-Scheduler.
3. Threshold + Settlement-Window-Combo.
**Libraries:** `numpy`.
**Backtesting-Ansatz:** Walk-Forward 6 M.
**Validierungskriterien:** Hit-Rate ≥ 58 %; Sharpe ≥ 1.5.
**Hardware:** CPU.
**Abhängigkeiten:** Tickers-Stream + Settlement-Scheduler.
**Zeitschätzung:** 2–3 Tage.
**Risiken:** Basis-Threshold-Kalibrierung; bei niedrig-funding-Phasen fast nie Signal.

#### M24: Kalman-Funding-Premium-Decomposition [L5] [Standard]
**Herkunft:** Kontrolltheorie (Kalman 1960; Ackerer/Hugonnier/Jermann 2023 "Perpetual Futures Pricing")
**Kernprinzip:** Funding Rate = Interest Rate Component + Premium Index. Premium-Index ist unobserved → State-Space-Modell mit Kalman-Filter trennt persistenten "fair-funding"-Drift vom transienten Sentiment-Spike. Sentiment-Spike > 2σ ist Contrarian-Signal.
**Mathematische Grundlage:**
```
State equation:        x_t = F · x_{t−1} + w_t           w_t ~ N(0, Q)
Observation equation:  z_t = H · x_t + v_t                v_t ~ N(0, R)

Kalman-Gain:  K_t = P_t H'(H P_t H' + R)^(−1)
Update:  x̂_t = x̂_{t|t−1} + K_t · (z_t − H · x̂_{t|t−1})

State = [trend_funding, transient_sentiment]
Signal:  |sentiment_t| > 2 · √(P_{22,t})   →  Fade-Trade
```
**Bybit-Anwendung:** z_t = aktuelle Funding-Rate + Basis. State trennt Trend/Transient. Bei extremem Sentiment-Spike: Fade gegen Overcrowded Side.
**Implementierungsskizze:**
1. 2-D State-Space mit pykalman.
2. Funding + Basis als Observations.
3. Online-Update bei jedem tickers-Push.
4. Sentiment-Komponente extrahieren.
**Libraries:** `pykalman`, `filterpy`.
**Backtesting-Ansatz:** Walk-Forward; Forward-2h-Return korreliert negativ mit Sentiment-Spike.
**Validierungskriterien:** Sharpe ≥ 1.0 für Fade-Strategie.
**Hardware:** CPU.
**Abhängigkeiten:** Tickers-Stream + Funding-History.
**Zeitschätzung:** 4–5 Tage.
**Risiken:** State-Space-Modell-Parameter (Q, R) empirisch.

#### M25: Kyle's Lambda (Adverse Selection) [L5] [Standard]
**Herkunft:** Microstructure-Ökonometrie (Kyle 1985, Econometrica; Hasbrouck 2007)
**Kernprinzip:** Permanenter Preisimpakt pro Volume-Einheit. Bei Anstieg von λ → informierte Trader aktiv → MM ziehen Liquidität ab. Toxic-Flow-Frühwarnung.
**Mathematische Grundlage:**
```
Δp_t = λ · v_t · sign_t + ε_t
OLS-Regression über N letzte Trades (signed-volume v_t)

Filter:  if λ_{5min} > Q95(λ_{30d})  →  KEINE Limit-Orders mehr
                                       (Adverse-Selection-Risk)
```
**Bybit-Anwendung:** Risk-Filter VOR Execution. Wenn λ hoch → nur Market-Order oder Flat.
**Implementierungsskizze:**
1. publicTrade + Orderbook → signed volume, ΔMidPrice.
2. Rolling OLS-Regression über letzte 100 Trades.
3. λ-Tracker mit 30d-Quantil.
4. Output: Bool-Flag "Toxic Flow".
**Libraries:** `numpy`, `statsmodels`.
**Backtesting-Ansatz:** Korrelation λ-Spike → nachfolgender Loss bei Limit-Orders.
**Validierungskriterien:** Limit-Order-Loss-Reduktion ≥ 30 % bei aktivem Filter.
**Hardware:** CPU.
**Abhängigkeiten:** publicTrade + Orderbook-State.
**Zeitschätzung:** 4–5 Tage.
**Risiken:** Bid-Ask-Bounce verfälscht λ — Tick-Rule-Korrektur empfohlen.

#### M26: SIR-Kompartiment-Liquidations-Contagion [L5] [Standard]
**Herkunft:** Epidemiologie (Kermack-McKendrick 1927; Demiralay & Golitsis 2025; SIR-Hawkes arXiv:1711.01679)
**Kernprinzip:** Trader-Population zerfällt in S (Susceptible, gehebelte Longs nahe Liq-Preis), I (Infected, gerade liquidiert), R (Recovered). dI/dt = βSI − γI. R₀ = β/γ > 1 → Kaskade selbsterhaltend.
**Mathematische Grundlage:**
```
dS/dt = −β · S · I
dI/dt =  β · S · I − γ · I
dR/dt =  γ · I

R₀ = β · S_0 / γ

Wenn R₀ > 1 → epidemische Kaskade
```
**Bybit-Anwendung:** S ≈ openInterest abzüglich kürzlich liquidiertem Volumen; I = laufende Liquidationsrate aus allLiquidation; β kalibriert über rollende OLS. Wenn geschätztes R₀ > 1 → Reverse-Position (Counter-Trend nach Klimax) ODER Risk-Off.
**Implementierungsskizze:**
1. Liquidation-Event-Buffer + OI-Stream.
2. scipy.integrate.odeint für SIR-Forward-Simulation.
3. scipy.optimize.curve_fit für β, γ auf rolling 30d.
4. R₀-Tracker; Trigger bei R₀ > 1.
**Libraries:** `scipy`, `numpy`.
**Backtesting-Ansatz:** Historische Cascade-Episoden (Oct 2025 19B-Liquidation, Mar 2020-Crash) — R₀-Vorlauf messen.
**Validierungskriterien:** R₀ > 1 mit ≥ 5 min Vorlauf zu 70 % der Mainshock-Cascades.
**Hardware:** CPU.
**Abhängigkeiten:** Liquidation-Buffer + Tickers-Stream.
**Zeitschätzung:** 1 Woche.
**Risiken:** β-Kalibrierung instabil bei niedrigem Liquidations-Flow (Sideways-Märkte).

---

### Layer-Übergreifende Methoden-Anzahl
**Total: 21 + 5 ergänzende = 26 Methoden-Einträge** (nach Merge 21 effektive — Hawkes Scout+Quant und PE Scout+Quant je zusammengefasst).

---

## 5. REFERENZ-ARCHITEKTUR

### 5.1 ASCII-Pipeline-Diagramm (vollständig, 5 Layer)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  BYBIT V5 WEBSOCKETS (public)                                             ║
║  ────────────────────────────────────────────────────────────────────     ║
║  tickers.{symbol}   (100 ms)  ──────►  multi-purpose feed                 ║
║  publicTrade.{symbol}        (event)  ──►  trade-flow + signs             ║
║  orderbook.50.{symbol}     (~20 ms)   ──►  LOB deltas                     ║
║  allLiquidation.{symbol}    (500 ms)  ──►  liquidation events             ║
║  orderbook.200 (opt.)     (~100 ms)   ──►  Iceberg layer                  ║
╚════════════════════════════════════╤══════════════════════════════════════╝
                                     │  asyncio + websockets
                                     ▼
       ┌─────────────────────────────────────────────────────────────────┐
       │  IN-MEMORY STATE ENGINE (Pub/Sub)                                │
       │  • OrderbookState (top-50 levels, sorted arrays)                │
       │  • TickerState  (last, mark, index, funding, OI, ...)           │
       │  • TradeBuffer  (rolling 1k events, signed)                     │
       │  • LiquidationBuffer (rolling 1k events)                        │
       │  • ImbalanceStream  (derived from OrderbookState)               │
       │  • MultiSymbolPanel (cross-sectional aggregator)                │
       └────────────────────────────┬────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
   ┌────────────────────┐  ┌─────────────────┐  ┌────────────────────┐
   │ L1: INGESTION      │  │ L2: DENOISING   │  │ L3: REGIME         │
   │ ----------------   │  │ -------------   │  │ ----------------   │
   │ • OFI (M2)         │  │ • Wavelet sym6  │  │ • Shannon-L2 (M6)  │
   │   numpy/numba      │  │   PyWavelets    │  │ • PE (M7) ordpy    │
   │ • SpikeWavformer   │  │   (M4)          │  │ • BOCPD (M8)       │
   │   snnTorch (M1)    │  │ • FFD (M5)      │  │ • HMM (M9) hmmlearn│
   │ • Iceberg (M3)     │  │   numpy/scipy   │  │ • MF-DFA (M10)     │
   │                    │  │                 │  │ • TDA (M11) ripser │
   │ Trigger: event     │  │ Triggered by L1 │  │ • RQA (M12) pyrqa  │
   └────────┬───────────┘  └────────┬────────┘  │ • CSZ (M13) panel  │
            │                       │           └─────────┬──────────┘
            │                       │                     │ Greenlight
            └───────────┬───────────┘                     │
                        │                                 │
                        ▼                                 ▼
            ┌─────────────────────────────────────────────────────────┐
            │  L4: PATTERN (gated by L3 Greenlight)                    │
            │  -----------------------------------                     │
            │  ┌──────────────────────────┐  ┌──────────────────────┐  │
            │  │ Hawkes 6-D + Liq (M14)   │  │ TFSAX + SW (M16)     │  │
            │  │   tick / hawkeslib       │  │   tslearn + Biopython│  │
            │  │   ρ(Φ) eigenvalues       │  │   library-match      │  │
            │  └──────────────────────────┘  └──────────────────────┘  │
            │  ┌──────────────────────────┐  ┌──────────────────────┐  │
            │  │ GR-b + Omori p,c,k (M15) │  │ Renyi-TE (M17) IDTxl │  │
            │  └──────────────────────────┘  └──────────────────────┘  │
            │  ┌──────────────────────────────────────────────────────┐│
            │  │ Foundation Ensemble:                                  ││
            │  │  • PatchTST (M18) — fine-tuned Funding-Cycle          ││
            │  │  • TimesNet (M19) — 2D-Periodicity                    ││
            │  │  • MOMENT (M20) — Zero-Shot                            ││
            │  │  → Pairwise-Pearson > 0.6 Confidence Gate              ││
            │  └──────────────────────────────────────────────────────┘│
            │  ┌──────────────────────────────────────────────────────┐│
            │  │ L/S-Ratio Smart-Money Divergence (M21)                ││
            │  └──────────────────────────────────────────────────────┘│
            └────────────────────────┬─────────────────────────────────┘
                                     │
                                     ▼
            ┌──────────────────────────────────────────────────────────┐
            │  L5: RISK / SIZING / PRE-EXECUTION FILTER                 │
            │  --------------------------------------                   │
            │  • Funding-Pressure Module (M22, M23, M24)               │
            │     ▸ Clamp Pressure (M22)                                │
            │     ▸ Mark-Index Basis (M23)                              │
            │     ▸ Kalman Premium Decomposition (M24)                  │
            │  • Kyle's λ Toxic-Flow-Filter (M25)                       │
            │  • SIR-Contagion R₀-Tracker (M26)                         │
            │                                                            │
            │  Output:  Position-Size · Stop-Level · Risk-Off-Bool      │
            └────────────────────────┬─────────────────────────────────┘
                                     │
                                     ▼
            ┌──────────────────────────────────────────────────────────┐
            │  DECISION AGGREGATOR                                       │
            │  • Long / Short / Wait                                     │
            │  • Position-Size (Kelly-Fraction · Kyle-λ-Discount)        │
            │  • Stop-Level (volatility-adjusted)                        │
            │  • Strategy-Selector (welcher Combo aktiv?)                │
            └────────────────────────┬─────────────────────────────────┘
                                     │
                                     ▼
            ┌──────────────────────────────────────────────────────────┐
            │  EXECUTION (Bybit V5 REST API, private)                    │
            │  Testnet → Mainnet                                         │
            └──────────────────────────────────────────────────────────┘
```

### 5.2 Textbeschreibung jedes Layers mit konkreten Libraries

**Layer L1 — INGESTION (Event-driven Filterung).**
Aufgabe: Raw WebSocket-Events filtern und nur relevante Anomalien an die nachgelagerten Layer durchreichen.
Module: M2 (OFI), M1 (SpikeWavformer), M3 (Iceberg).
Libraries: `numpy`, `numba`, `polars` (CPU-Pfad); `snnTorch` + `PyWavelets` + `PyTorch` (SNN-Pfad).
Trigger: immer aktiv; produziert Events für L2 (Wavelet-Trigger) und L4 (OFI-Anomalie).

**Layer L2 — DENOISING (Signal-Rausch-Trennung).**
Aufgabe: Market-Maker-Rauschen vom Smart-Money-Tape trennen.
Module: M4 (Wavelet-Symlet), M5 (FFD).
Libraries: `PyWavelets`, `numpy`, `statsmodels` (ADF).
Trigger: nach L1-Spike (Wavelet) ODER kontinuierlich (FFD-Preprocessing für ML).

**Layer L3 — REGIME (Marktphasen-Erkennung).**
Aufgabe: Regime-Klassifikation als Greenlight für L4. Ensemble aus orthogonalen Methoden.
Module: M6 (Shannon-L2), M7 (PE), M8 (BOCPD), M9 (HMM), M10 (MF-DFA), M11 (TDA), M12 (RQA), M13 (Cross-Sectional-Z).
Libraries: `ordpy`, `antropy`, `bayesian-changepoint-detection`, `hmmlearn`, `MFDFA`, `ripser`, `gudhi`, `persim`, `pyrqa`.
Trigger: parallel zu L2; produziert Bool-Greenlight + Posterior-State an L4.

**Layer L4 — PATTERN (Mustererkennung, Alignment, Forecasting).**
Aufgabe: Konkrete Trade-Hypothese formulieren (Direction, Confidence, Horizon).
Module: M14 (Hawkes ρ(Φ)), M15 (GR + Omori), M16 (TFSAX + SW), M17 (Renyi-TE), M18 (PatchTST), M19 (TimesNet), M20 (MOMENT), M21 (L/S-Ratio).
Libraries: `tick`, `hawkeslib`, `scipy`, `tslearn`, `saxpy`, `Biopython`, `IDTxl`, `PyTorch`, `transformers`, `momentfm`.
Trigger: Greenlight von L3; Output an L5.

**Layer L5 — RISK / SIZING.**
Aufgabe: Pre-Execution-Filter, Position-Sizing, Stop-Level, Risk-Off-Override.
Module: M22 (Funding-Clamp-Pressure), M23 (Mark-Index-Basis), M24 (Kalman-Premium), M25 (Kyle's λ), M26 (SIR-Contagion).
Libraries: `pykalman`, `filterpy`, `scipy`, `numpy`, `statsmodels`.
Trigger: vor jeder Execution; kann Trade veto-en.

---

## 6. PRIORISIERUNGSMATRIX

Score-Skala: 1 = LOW, 2 = MEDIUM, 3 = HIGH. Priorität = (Edge × Novelty) / Komplexität.

| # | Methode | Layer | Novelty | Edge | Retail | Komplex. | Priorität | Empf. Phase |
|---|---------|-------|---------|------|--------|----------|-----------|-------------|
| M22 | Funding-Rate-Clamp Pressure-Release | L5 | 3 | 3 | 3 | 2 | **4.5** | Phase 1 (Quick Win) |
| M2  | OFI Cont-Kukanov-Stoikov | L1 | 2 | 3 | 3 | 1 | **6.0** | Phase 1 (Quick Win) |
| M23 | Mark-Index Basis Settlement | L5 | 2 | 3 | 3 | 1 | **6.0** | Phase 1 (Quick Win) |
| M15 | Gutenberg-Richter + Omori | L4 | 3 | 3 | 3 | 2 | **4.5** | Phase 2 |
| M7  | Permutation Entropy | L3 | 2 | 2 | 3 | 1 | **4.0** | Phase 1 (Quick Win) |
| M6  | Shannon-Entropie L2-Orderbook | L3 | 2 | 2 | 3 | 1 | **4.0** | Phase 3 |
| M8  | BOCPD auf openInterest | L3 | 2 | 2 | 3 | 2 | **2.0** | Phase 1 |
| M24 | Kalman-Premium-Decomposition | L5 | 2 | 2 | 3 | 1 | **4.0** | Phase 1 |
| M5  | Fraktionale Differenzierung | L2 | 2 | 2 | 3 | 1 | **4.0** | Phase 3 |
| M25 | Kyle's Lambda | L5 | 2 | 3 | 3 | 1 | **6.0** | Phase 2 |
| M21 | L/S-Ratio Smart-Money | L4 | 2 | 2 | 3 | 1 | **4.0** | Phase 4 |
| M26 | SIR-Liquidations-Contagion | L5 | 3 | 2 | 2 | 2 | **3.0** | Phase 2 |
| M14 | Hawkes ρ(Φ) 6-D Coupled | L4 | 3 | 3 | 2 | 3 | **3.0** | Phase 2/3 (Moonshot) |
| M9  | HMM Vola-OFI-Funding | L3 | 2 | 2 | 3 | 2 | **2.0** | Phase 3 |
| M4  | Wavelet-Symlet-Denoising | L2 | 2 | 2 | 3 | 1 | **4.0** | Phase 3 |
| M16 | TFSAX + Smith-Waterman | L4 | 3 | 2 | 2 | 3 | **2.0** | Phase 4 (Moonshot) |
| M17 | Renyi-Transfer-Entropy | L4 | 3 | 2 | 2 | 2 | **3.0** | Phase 4 |
| M18 | PatchTST Funding-Cycle | L4 | 3 | 2 | 2 | 2 | **3.0** | Phase 4 |
| M19 | TimesNet 2D-Periodicity | L4 | 3 | 2 | 2 | 2 | **3.0** | Phase 5 |
| M20 | MOMENT Zero-Shot | L4 | 3 | 2 | 2 | 3 | **2.0** | Phase 4 |
| M1  | SpikeWavformer (SNN+DWT) | L1 | 3 | 2 | 2 | 3 | **2.0** | Phase 5 (Moonshot) |
| M10 | MF-DFA Multifractal | L3 | 2 | 2 | 2 | 2 | **2.0** | Phase 5 |
| M11 | TDA Persistent Homology | L3 | 3 | 2 | 2 | 2 | **3.0** | Phase 5 |
| M12 | RQA | L3 | 2 | 2 | 3 | 2 | **2.0** | Phase 5 |
| M13 | Cross-Sectional-Z (CSZ) | L3 | 2 | 2 | 2 | 2 | **2.0** | Phase 4 |
| M3  | Iceberg-Detection | L1 | 2 | 2 | 2 | 3 | **1.3** | Phase 5 (optional) |

**Top-5 Quick Wins** (Priorität ≥ 4.0, Komplexität LOW/MEDIUM): M22, M2, M23, M7, (M15 oder M25).

**Top-3 Moonshots** (Novelty = 3, Komplexität HIGH): M14 (Hawkes 6-D), M1 (SpikeWavformer), M16 (TFSAX + SW).

---

## 7. KOMBINATIONSSTRATEGIEN

### 7.1 Strategie 1 — "Seismischer Cascade Detector" (L4 + L5)
**Methoden:** M14 (Hawkes ρ(Φ)) + M15 (Gutenberg-Richter b + Omori p,c,k) + M26 (SIR-R₀).
**Logik:** Liquidationen folgen seismischen Statistiken. Hawkes formalisiert Selbsterregung, GR/Omori liefern Magnituden-Modell, SIR liefert Ansteckungs-Schätzung über gehebelte Positionen. Drei orthogonale Bestätigungen.
**Entry-Bedingung:**
```
ρ(Φ) > 0.85 (steigend, dρ/dt > 0)
AND b-Wert < b̄_30d − 2σ          (großbeben-prone)
AND Omori-Aftershock-Phase aktiv: k · (t + c)^(−p) hoch (Mainshock < 30min)
AND SIR-R₀ > 1.0
Trade-Direction = entgegengesetzt zur Liquidations-Seite
                  (Long-Liqs → Long-Entry nach Klimax)
```
**Exit-Bedingung:**
```
ρ(Φ) < 0.5
OR Omori-Decay-Phase erreicht (t > 5·c)
OR Stop bei OI-Recovery > 95% des Pre-Cascade-Niveaus
```
**Edge-Quelle:** Mean-Reversion nach Liquidations-Klimax; Retail erkennt nur den Spike, nicht das energetische Profil. Zeitfenster: Sekunden bis wenige Minuten.
**Layer:** L4 (Hawkes, GR/Omori) + L5 (SIR, Sizing via Kyle's λ).

### 7.2 Strategie 2 — "Entropie-Momentum" (L1 + L3 + L5)
**Methoden:** M6 (Shannon-L2) + M2 (OFI) + M22 (Funding-Clamp) + M7 (PE).
**Logik:** Greenlight-Kaskade: Entropie kollabiert (Markt verlässt Random Walk) → OFI dreht in eindeutige Richtung → Funding-Pressure bestätigt Druck-Direktion.
**Entry-Bedingung:**
```
Shannon-Entropie_L2 < Median_24h − 2σ
AND |OFI_rolling_5s| > Q90
AND sign(Funding-Pressure) == sign(OFI)
AND PE < Median_24h     (Greenlight)
```
**Exit-Bedingung:**
```
Shannon-Entropie zurück über Median
OR OFI-Vorzeichen flippt
OR Funding-Pressure dissipiert (|P − F| < 0.01%)
```
**Edge-Quelle:** Mikrostruktur-Information; institutionelle Aggression sichtbar in OFI + Order-Book-Strukturzusammenbruch.
**Layer:** L1 (OFI) + L3 (Entropie, PE) + L5 (Funding).

### 7.3 Strategie 3 — "Pre-Settlement Pressure-Release" (L5 + L3) — *erste live-paper-version*
**Methoden:** M22 (Funding-Clamp) + M23 (Mark-Index-Basis) + M24 (Kalman) + M8 (BOCPD).
**Logik:** Funding-Settlements (00/08/16 UTC) sind deterministische Zeit-Trigger. Wenn Clamp-Pressure am Cap UND Basis-Spread extrem UND Kalman-Trend persistent → Settlement-Fenster löst gestauten Druck aus.
**Entry-Bedingung:**
```
T_settlement − t < 30 min
AND |Funding-Pressure| > Q90 (rolling 30d)
AND Mark-Index-Basis · sign(Pressure) > 0  (gleiche Richtung)
AND BOCPD-Run-Length stabil (kein concurrent Change-Point in OI)
```
**Exit-Bedingung:**
```
Settlement-Tick + 10 min
OR Funding rastet zurück innerhalb [−0.01%, +0.01%]
```
**Edge-Quelle:** Mechanische Pressure-Release; Edge ist *timing-präzise*, nicht direktional-prognostisch.
**Layer:** L5 (drei Funding-Module) + L3 (BOCPD als Veto-Filter).

### 7.4 Strategie 4 — "Pattern × Foundation Ensemble" (L2 + L4)
**Methoden:** M5 (FFD-Preprocessing) + M16 (TFSAX + SW) + M20 (MOMENT) + M18 (PatchTST) + Forecast-Korrelation als Confidence-Gate.
**Logik:** Drei orthogonale Pattern-Engines. Trade nur bei Konsens (Pairwise-Pearson > 0.6).
**Entry-Bedingung:**
```
≥ 2 von 3 Modellen prognostizieren gleichgerichtet > 0.5% in h ∈ {15min, 1h, 4h}
AND Pairwise-Forecast-Pearson > 0.6
AND |TFSAX-Match-Score| > 0.75   (Smith-Waterman normalisiert)
```
**Exit-Bedingung:**
```
Time-Stop bei horizon h
OR Forecast-Update flippt Vorzeichen
```
**Edge-Quelle:** Multi-Model-Konsens senkt idiosyncratic Forecast-Noise.
**Layer:** L2 (FFD) + L4 (TFSAX, MOMENT, PatchTST).

### 7.5 Strategie 5 — "Cross-Sectional Ergodicity Reversion" (L3 + L4)
**Methoden:** M13 (Cross-Sectional-Z) + M17 (Renyi-TE) + M9 (HMM).
**Logik:** Symbole mit Time-Mean weit weg vom Ensemble-Mittel tendieren zur Mean-Reversion. Renyi-TE identifiziert "echte" Reversions-Kandidaten (mit BTC-Informationsfluss).
**Entry-Bedingung:**
```
|Cross-Sectional-Z| > 2.5
AND Renyi-TE(BTC → Alt) > 0.05    (echter Informationsfluss)
AND HMM-State ≠ "High-Vol-Crash"
Trade-Direction = gegen Z (Mean-Reversion)
```
**Exit-Bedingung:**
```
|Z| < 0.5
OR Time-Stop 24h
OR HMM-Regime-Wechsel
```
**Edge-Quelle:** Statistische Mean-Reversion über Symbol-Panel; Renyi-TE filtert Outlier.
**Layer:** L3 (Z, HMM) + L4 (Renyi-TE).

---

## 8. IMPLEMENTIERUNGS-ROADMAP

### Phase 0 — Infrastructure (Woche 1)
- **Bybit-WebSocket-Collector:** asyncio + websockets; auto-reconnect, snapshot-resync, schema-versioniert.
- **Persistence-Layer:** DuckDB + Parquet (ZSTD-compressed); rolling 30-day-Hot + lifetime-Cold.
- **OrderbookState + TickerState + TradeBuffer + LiquidationBuffer** (Pub/Sub).
- **Funding-Settlement-Scheduler** (Cron 00/08/16 UTC).
- **Backtester-Skelett:** Event-Loop, Walk-Forward-Splitter, Slippage-/Fee-Modell (Bybit Taker 0.055 % / Maker 0.02 %).
- **Logging:** structlog + loguru; metrics → Prometheus.

### Phase 1 — Foundation + Quick Wins (Woche 2–4)
1. **M22 Funding-Clamp Pressure-Release** — ERSTE IMPLEMENTIERUNG (s. Empfehlung unten).
2. **M23 Mark-Index Basis Settlement Convergence.**
3. **M24 Kalman-Premium-Decomposition.**
4. **M2 OFI Cont-Kukanov-Stoikov.**
5. **M7 Permutation Entropy Greenlight.**
6. **M8 BOCPD auf openInterest.**
7. **M15 Gutenberg-Richter + Omori (auf allLiquidation).**
- **Backtest** jedes Modul standalone auf 6 M Bybit-Daten.
- **Strategie 3 "Pre-Settlement Pressure-Release" live-paper auf Bybit-Testnet (Woche 5).**

### Phase 2 — Core Methods (Woche 5–10)
8. **M26 SIR-Contagion** auf allLiquidation + OI.
9. **M14a Hawkes 1-D Single-Channel** (Liquidation-only, MLE-Single-Process).
10. **M25 Kyle's Lambda** als Risk-Filter.
11. **M6 Shannon-L2-Orderbook Entropie.**
12. **M4 Wavelet-Symlet-Denoising** auf Imbalance-Stream.
13. **M9 HMM** auf Vola-OFI-Funding.
14. **M5 FFD** als universelles Preprocessing.
- **Backtest Strategie 1 "Seismischer Cascade Detector"** und **Strategie 2 "Entropie-Momentum"** end-to-end.

### Phase 3 — Advanced (Woche 11–20)
15. **M14b Hawkes 6-D Orderbook + coupled Liquidation** (volle Matrix).
16. **M16 TFSAX + Smith-Waterman Library** (5y Historie segmentieren, Library aufbauen).
17. **M18 PatchTST** auf Funding-Cycle (FFD-präpariert).
18. **M19 TimesNet 2D-Periodicity.**
19. **M20 MOMENT Zero-Shot + LoRA-FineTune.**
20. **M17 Renyi-TE Multi-Symbol Lead-Lag-Graph.**
21. **M13 Cross-Sectional-Z** Ergodicity-Modul.
22. **M21 L/S-Ratio Smart-Money-Divergence.**
- **Backtest Strategie 4 + 5.**

### Phase 4 — Moonshots + Integration + Live-Testnet (Woche 21–24)
23. **M1 SpikeWavformer** (SNN+DWT) — Training & Integration.
24. **M11 TDA / Persistent Homology.**
25. **M12 RQA.**
26. **M10 MF-DFA.**
27. **M3 Iceberg-Detection** (optional).
28. **Decision Aggregator** (Strategie-Selector + Sizing-Engine).
29. **Live Paper-Trading auf Bybit Testnet** mit allen 5 Strategien (priorisiert: 3 > 1 > 2 > 4 > 5).
30. **Metriken-Ziel:** Sharpe ≥ 1.5, Max-DD < 15 %, Win-Rate > 52 %.

### Empfohlene erste Implementierung
**Tag 1–3:** Bybit-WebSocket-Collector + Persistence.
**Tag 4–7:** Funding-Settlement-Scheduler + TickerState.
**Tag 8–14: M22 Funding-Rate-Clamp Pressure-Release** als erstes vollständig backtestbares Edge-Modul — kürzeste Time-to-Backtest, deterministischer Trigger (Settlement-Window), öffentliche Daten, minimaler Code (~200 LOC).

---

## 9. RISIKEN & EINSCHRÄNKUNGEN

### 9.1 Overfitting
- **Walk-Forward-Pflicht** für alle ML-haltigen Methoden (M9, M16, M18, M19, M20).
- **Combinatorial Purged Cross-Validation** (López de Prado, AFML Kap. 7) mit Embargo zwischen Train/Test.
- **Hyperparameter-Suche** via Optuna; Pruning bei nicht-konvergierenden Trials.
- **Out-of-Sample-Hold-Out:** mindestens letztes 1 M (= ~30 % der Historie) niemals für Training oder Hyperparam-Tuning verwenden.
- **Robustheitstest:** Strategie-Parameter ±20 % verschieben → Sharpe muss > 50 % der Mid-Performance bleiben.

### 9.2 Bybit-spezifische API-Risiken
- **WebSocket-Reconnect:** typisch ~1 Dropout/Tag. Snapshot-Resync via REST `/v5/market/orderbook` + `/v5/market/recent-trade` Pflicht. Hawkes-Inferenz bei Lücken pausieren statt extrapolieren.
- **Funding-Mechanik-Änderungen:** Bybit kann Funding-Frequenz/Clamp anpassen (Historie: ~1×/Jahr). Module M22, M23, M24 **konfigurierbar** implementieren (`funding_clamp_bounds: tuple`, `funding_interval_seconds: int`).
- **Rate-Limits REST:** 120 req/min unauthenticated; bei Backfill mit Sleep + Exponential-Backoff.
- **Symbol-Listing/Delisting:** Multi-Symbol-Methoden (M13, M17) müssen Delisting-Events respektieren (Survivorship-Bias-Korrektur).
- **WebSocket-Latenz EU→Singapore:** typisch 100–150 ms; AWS Tokyo VPS reduziert auf 5–15 ms — empfohlen, aber nicht zwingend (alle NEAR-RT-Methoden funktionieren auch mit 150 ms).

### 9.3 Regime-Abhängigkeiten
| Methode | Funktioniert besonders in | Schwach bei |
|---------|---------------------------|-------------|
| M2 OFI | Normale Vol (HMM-State 1–2) | Asia-Low-Liquidity (00–04 UTC) |
| M14 Hawkes | Aktive Phasen ≥ 10 Liq/min | Sideways-Low-Volume |
| M15 GR/Omori | Kaskadenphasen | Quiet markets |
| M22 Funding-Clamp | Hohe Funding (|F| > 0.03 %) | ~0 % Funding |
| M26 SIR | High-Leverage-Regimes | Low-Leverage (Bull-Recovery) |
| M11 TDA | Crash-Vorlauf | Bull-Run (kein H_1-Spike) |
| M16 TFSAX | Etablierte Patterns | Strukturwandel (kein Match) |
| M20 MOMENT | Universell (Zero-Shot) | Bybit-spezifische Anomalien (kein Pre-Training) |

### 9.4 VRAM-Grenzen RTX 5060 Ti (16 GB VRAM)
| Modell | Parameter | Training-VRAM | Inferenz-VRAM | Status |
|--------|-----------|---------------|---------------|--------|
| PatchTST (M18) | 5–10 M | ~4 GB (Batch 32) | < 0.5 GB | OK |
| TimesNet (M19) | 5–10 M | ~5 GB (Batch 32) | < 0.5 GB | OK |
| MOMENT-base (M20) | 110 M | ~10 GB (Batch 16) | ~2 GB | OK |
| MOMENT-large (M20) | 341 M | ~24 GB (Batch 8) | ~6 GB | **NICHT TRAINIERBAR** auf 16 GB — Inferenz möglich mit FP16 |
| SpikeWavformer (M1) | ~1 M LIF | ~3 GB | ~0.5 GB | OK |
**Empfehlung:** Auf MOMENT-base bleiben; LoRA-FineTune statt full-finetune. Batch-Size reduzieren bei OOM.

### 9.5 Rechtliches (Deutschland)
- **Krypto-Steuer:** Derivate (Perpetual Futures) gelten in Deutschland als *Termingeschäfte* (§ 23 Abs. 1 Satz 1 Nr. 4 EStG i. V. m. § 20 Abs. 2 Nr. 3 EStG). Gewinne aus Krypto-Derivaten werden **als Kapitaleinkünfte** (Abgeltungsteuer 25 % + Soli + ggf. KiSt) behandelt — *unabhängig von der Haltedauer* (keine Spekulationsfrist anwendbar). Verlustverrechnung ist auf 20.000 EUR/Jahr begrenzt (§ 20 Abs. 6 Satz 6 EStG). **Aktuelle Steuerberatung einholen — Rechtslage Stand 2025/2026 ist im Fluss.**
- **MaRisk / KWG:** Nicht relevant für Privattrader ohne Lizenzpflicht; gilt nur für institutionelle Marktteilnehmer.
- **Bybit-AGB:** Kein explizites API-Verbot für algorithmischen Handel; jedoch sind *Market Manipulation* und *Wash Trading* verboten (Standard-Klausel). Eigenhandel mit eigenem Kapital ist erlaubt.
- **MiCAR (EU):** Markets in Crypto-Assets Regulation Stand 2024/25 für Krypto-Service-Provider; private Algotrader nicht direkt betroffen, solange keine Drittkunden bedient werden.
- **Bybit-KYC:** für EU/DE-User Pflicht (Tier-2 für Derivate-Trading); Account muss aktuell und kompliant sein.

### 9.6 Querschnitt-Risiken
- **Walk-Forward Reproducibility:** Alle Backtests mit fixiertem Random-Seed; Dependency-Versions in `pyproject.toml` gepinnt.
- **Live-vs-Backtest-Slippage-Gap:** Bybit-Slippage ist symbol-/depth-abhängig — empirisch in Testnet messen, dann Live-Slippage-Modell kalibrieren.
- **Single-Point-of-Failure VPS:** Health-Check + Auto-Restart-Watchdog (systemd oder Docker-Compose restart-Policy).
- **Modell-Decay:** Quartalsweises Re-Training für ML-Komponenten; Drift-Monitoring (KL-Divergenz zwischen Train- und Live-Feature-Verteilung).

---

## QUALITÄTS-SELF-CHECK

- [x] Alle 9 Abschnitte vollständig?  **Ja.**
- [x] Mindestens 18 Methoden im Katalog mit Formel + Bybit-Endpoint + Zeitschätzung?  **Ja — 26 Methoden-Einträge (21 effektive nach Merge).**
- [x] Alle 5 Pipeline-Layer beschrieben?  **Ja (L1, L2, L3, L4, L5).**
- [x] ≥ 3 Kombinationsstrategien (Ziel: alle 5)?  **Ja — alle 5 Strategien.**
- [x] RTX 5060 Ti explizit adressiert (in Methoden-Hardware-Feldern UND Abschnitt 9)?  **Ja (s. M1, M16, M18, M19, M20 und Abschnitt 9.4 VRAM-Tabelle).**
- [x] Inhaltsverzeichnis vorhanden?  **Ja (mit Anchor-Links).**

---

**END OF FINAL_PRD.md**
