[QUANT → CRITIC] STATUS: COMPLETE | METHODS: 14 | CATEGORIES: 5

---

### METHODE: Funding Rate Clamp Pressure-Release [PRIORITY]
- Kategorie: A
- Kernprinzip: Bybit clamped die Funding Rate F bei ±0.05% via `F = P + clamp(I − P, 0.05%, −0.05%)`. Bei extremer Marktdivergenz wird der "echte" Premium-Druck im System gestaut und entlädt sich rhythmisch nach Settlement. Edge entsteht, wenn |P| ≥ 0.1% während F gekappt bleibt — der Stau ist messbar UND mean-reverting.
- Kernformel: `Pressure_t = P_t − F_t` (gekappter Rest); Signal wenn `|Pressure_t| > 2·σ(Pressure)` über letzte 24h
- Konkreter Anwendungsfall: Long Mean-Reversion-Trade in den 30 min nach Settlement, wenn aufgestaute Negative-Premium-Pressure die Clamp-Grenze überschritten hatte (Shorts haben "zu wenig" gezahlt, Reversion kommt)
- Bybit-Endpoint(s): WS `tickers.{symbol}` (fundingRate, nextFundingTime, indexPrice, markPrice) + REST `/v5/market/funding/history`
- Benötigte Datenfelder: fundingRate, markPrice, indexPrice, bid1Price, ask1Price (zur Impact-Ask-Approximation)
- Novelty-Score: 5 | Spezifisch Bybit-Mechanik, in Literatur nicht beschrieben
- Umsetzungskomplexität: MEDIUM
- Edge-Typ: Alpha + Entry-Timing
- Literatur/Paper: Bybit Help Center — "Introduction to Funding Rate"; Palepu (2021) "Funding rates: under the hood"

### METHODE: Order Flow Imbalance (Cont-Kukanov-Stoikov) [PRIORITY]
- Kategorie: B
- Kernprinzip: Über kurze Intervalle sind Preisänderungen primär durch OFI an Best-Bid/Ask getrieben. Linear in OFI, Slope umgekehrt proportional zur Markttiefe. Robust intraday und zwischen Symbolen.
- Kernformel: `OFI_n = Σ e_n` mit `e_n = I(P^b_n ≥ P^b_{n−1})·q^b_n − I(P^b_n ≤ P^b_{n−1})·q^b_{n−1} − I(P^a_n ≤ P^a_{n−1})·q^a_n + I(P^a_n ≥ P^a_{n−1})·q^a_{n−1}`
- Konkreter Anwendungsfall: 1-Sekunden-Forecast für Mid-Price-Drift auf BTCUSDT-Perp; Filter für Entry-Timing (nur shorten wenn OFI < 0)
- Bybit-Endpoint(s): WS `orderbook.50.{symbol}` (Delta-Stream Level-1 Daten + Tiefe für λ-Normierung)
- Benötigte Datenfelder: bid1Price, bid1Size, ask1Price, ask1Size, Delta-Updates
- Novelty-Score: 3 | Klassisch, aber selten auf Bybit-Perps angewandt
- Umsetzungskomplexität: LOW
- Edge-Typ: Entry-Timing
- Literatur/Paper: Cont, Kukanov, Stoikov (2014) "The Price Impact of Order Book Events", J. Financial Econometrics 12(1):47-88, arXiv:1011.6402

### METHODE: Liquidation Cascade Predictor (Hawkes Self-Excitation) [PRIORITY]
- Kategorie: A
- Kernprinzip: Liquidations-Events auf Bybit feuern als preisunabhängige Marktorders → bewegen Preis → triggern nächste Liquidationen. Selbst-anregender Hawkes-Prozess. Spektralradius ρ(Φ) der Branching-Matrix → Kritikalität (ρ → 1 = Kaskaden-Regime).
- Kernformel: `λ(t) = μ + Σ_{t_i < t} α·exp(−β(t − t_i))·v_i^γ`; Kritikalität: `n_∞ = α/β` (Verzweigungsverhältnis)
- Konkreter Anwendungsfall: Wenn n_∞ > 0.8 auf BTCUSDT in rollendem 5-min-Fenster → Risk-Off (keine neuen Longs nahe Mark-Price-Cluster)
- Bybit-Endpoint(s): WS `allLiquidation.{symbol}` (500ms) + WS `tickers.{symbol}` (openInterest, markPrice)
- Benötigte Datenfelder: T, S (Side), v (Volume), p (Bankrott-Preis), openInterest
- Novelty-Score: 5 | Bybit-spezifische Datenqualität (jede Liquidation, nicht 1/sec) ermöglicht erst seit 2025
- Umsetzungskomplexität: HIGH
- Edge-Typ: Risk-Mgmt + Regime-Filter
- Literatur/Paper: Hawkes (1971) "Spectra of self-exciting"; Bacry, Mastromatteo, Muzy (2015) "Hawkes processes in finance"

### METHODE: PatchTST für Funding-Cycle-Forecast
- Kategorie: C
- Kernprinzip: Zeitreihe in Subseries-Patches segmentieren, channel-independent über Transformer. Quadratische Attention-Reduktion → lange Lookbacks möglich. Ideal für 8h-Funding-Zyklen mit 100ms-Granularität.
- Kernformel: `x_p ∈ R^{P×N}` mit P = Patch-Länge, N = Anzahl Patches = ⌊(L−P)/S⌋+2; Attention auf Patches statt Time-Steps
- Konkreter Anwendungsfall: Predict 5-min-Return auf BTCUSDT 30 min vor Funding-Settlement; channel-independence erlaubt Cross-Symbol-Transfer
- Bybit-Endpoint(s): WS `tickers.{symbol}` + REST `/v5/market/kline?interval=1`
- Benötigte Datenfelder: lastPrice, fundingRate, openInterest (~10h Lookback bei 1-min-Bars)
- Novelty-Score: 4 | SOTA, aber kaum auf Crypto-Perps mit Funding-Features dokumentiert
- Umsetzungskomplexität: MEDIUM
- Edge-Typ: Alpha
- Literatur/Paper: Nie, Nguyen et al. (2023) "A Time Series is Worth 64 Words", ICLR 2023, arXiv:2211.14730

### METHODE: MOMENT Foundation Model Zero-Shot Altcoin Transfer
- Kategorie: C
- Kernprinzip: Pre-trained Time-Series Foundation Model (ICML 2024, CMU/Auton Lab). Erlaubt Zero-Shot-Forecasting auf unbekannte Symbole — kritisch für Altcoin-Rotation auf Bybit, wo neue Listings ständig erscheinen.
- Kernformel: Encoder-only T5-Architektur mit Patch-Tokenisierung + reversibler Instance-Normalisierung
- Konkreter Anwendungsfall: Neulisting auf Bybit (z.B. neue USDT-Perp) → Forecast ohne Fine-Tuning für ersten 24h aktivierbar; Fine-Tune später auf RTX 5060 Ti
- Bybit-Endpoint(s): REST `/v5/market/kline` + WS `tickers.{symbol}` für Live-Stream
- Benötigte Datenfelder: OHLCV (1-min), openInterest, fundingRate
- Novelty-Score: 5 | Foundation-Modelle in Crypto-Trading praktisch unangewandt (Stand 2025)
- Umsetzungskomplexität: HIGH
- Edge-Typ: Alpha (Cross-Symbol)
- Literatur/Paper: Goswami et al. (2024) "MOMENT: A Family of Open Time-Series Foundation Models", ICML 2024, arXiv:2402.03885

### METHODE: Bayesian Online Change Point Detection (BOCPD) auf OI
- Kategorie: D
- Kernprinzip: Online-Bayes-Inference über Position des letzten Strukturbruchs. Run-Length-Posterior P(r_t | x_{1:t}) via Message-Passing. Kein Lookback-Bias, exakt — sofort einsetzbar.
- Kernformel: `P(r_t | x_{1:t}) ∝ Σ P(r_t | r_{t−1})·P(x_t | r_{t−1},x)·P(r_{t−1} | x_{1:t−1})`; Hazard h(r) = const → geometrische Run-Length
- Konkreter Anwendungsfall: Strukturbruch in OI-Time-Series auf BTCUSDT detect within 2 min → Regime-Filter für Trend-Following-Strategien
- Bybit-Endpoint(s): REST `/v5/market/open-interest?intervalTime=5min` + WS `tickers.{symbol}` (openInterest live)
- Benötigte Datenfelder: openInterest, openInterestValue
- Novelty-Score: 4 | Standard-Methode, aber selten auf OI (statt Preis) angewandt
- Umsetzungskomplexität: MEDIUM
- Edge-Typ: Regime-Filter
- Literatur/Paper: Adams & MacKay (2007) "Bayesian Online Changepoint Detection", arXiv:0710.3742

### METHODE: Mark-Index Basis Settlement Convergence
- Kategorie: A
- Kernprinzip: Basis = markPrice − indexPrice. Persistent positive Basis → Perp überbewertet → Funding zieht Basis Richtung 0 vor Settlement. Convergence-Trade in Window [Settlement − 60min, Settlement].
- Kernformel: `Basis_t = (markPrice_t − indexPrice_t) / indexPrice_t`; Signal wenn `Basis_t > 0.0008` UND Time-to-Settlement < 1h
- Konkreter Anwendungsfall: Short Perp / Long Spot (Cash-and-Carry) wenn Basis > Funding-Expected-Cost; oder reiner Perp-Short ohne Hedge bei extremer Basis
- Bybit-Endpoint(s): WS `tickers.{symbol}` (markPrice, indexPrice, nextFundingTime, fundingRate)
- Benötigte Datenfelder: markPrice, indexPrice, nextFundingTime, fundingRate
- Novelty-Score: 3 | Bekannt, aber 100ms-Granularität auf Bybit selten genutzt
- Umsetzungskomplexität: LOW
- Edge-Typ: Alpha + Entry-Timing
- Literatur/Paper: Bybit Help Center — "Mark Price Calculation"

### METHODE: Kyle's Lambda (Adverse Selection / Toxic Flow)
- Kategorie: B
- Kernprinzip: Permanenter Preisimpakt pro Volume-Einheit. Bei Anstieg von λ → informierte Trader aktiv → Market-Maker ziehen Liquidität ab. Toxic-Flow-Frühwarnung.
- Kernformel: `Δp_t = λ·v_t·sign_t + ε_t` mit OLS-Regression über N letzte Trades; v_t signed volume
- Konkreter Anwendungsfall: Wenn λ_{5min} > 95-Perzentil λ_{30d} → keine Limit-Orders mehr (Adverse-Selection-Risiko); nur Market-Order oder Flat
- Bybit-Endpoint(s): REST `/v5/market/recent-trade` + WS `publicTrade.{symbol}` (Side, Size, Price)
- Benötigte Datenfelder: Trade-Side, Trade-Size, Trade-Price, Mid-Price-Time-Series
- Novelty-Score: 3 | Klassisch, Anwendung auf Bybit selten
- Umsetzungskomplexität: LOW
- Edge-Typ: Risk-Mgmt + Position-Sizing
- Literatur/Paper: Kyle (1985) "Continuous Auctions and Insider Trading", Econometrica 53(6); Hasbrouck (2007) "Empirical Market Microstructure"

### METHODE: TimesNet 2D-Periodicity Faltung
- Kategorie: C
- Kernprinzip: 1D-Zeitreihe wird via FFT in dominante Perioden zerlegt und in 2D-Tensoren gefaltet (Inter-Period × Intra-Period). 2D-CNN-Blocks erkennen zyklische Muster, die 1D-Models verpassen.
- Kernformel: `X_2D = Reshape_{p_i, f_i}(X_1D)` mit p_i = Top-k-Frequenzen aus FFT
- Konkreter Anwendungsfall: 8h-Funding-Periodizität + 24h-Tag-Zyklus + Wochen-Zyklus auf BTCUSDT — natürlicher Multi-Period-Use-Case
- Bybit-Endpoint(s): REST `/v5/market/kline?interval=5` (mehrere Wochen Lookback)
- Benötigte Datenfelder: OHLCV, fundingRate (als zusätzlicher Channel)
- Novelty-Score: 4 | SOTA-Modell, Funding-Zyklus passt mathematisch ideal
- Umsetzungskomplexität: MEDIUM
- Edge-Typ: Alpha + Regime-Filter
- Literatur/Paper: Wu et al. (2023) "TimesNet: Temporal 2D-Variation Modeling for General Time Series Analysis", ICLR 2023, arXiv:2210.02186

### METHODE: Fraktionale Differenzierung (López de Prado)
- Kategorie: E
- Kernprinzip: Integer-Differenzierung erzwingt Stationarität, zerstört aber Memory. Fraktionale Differenzierung d ∈ (0,1) macht Reihe stationär bei minimalem Memory-Verlust — entscheidend für ML-Features auf Preis-/OI-Zeitreihen.
- Kernformel: `(1−B)^d X_t = Σ_{k=0}^∞ (−1)^k·C(d,k)·X_{t−k}`; gewichteter Backshift-Operator mit Fixed-Width-Window
- Konkreter Anwendungsfall: Preprocessing für openInterest- und cumulativeFunding-Features vor ML-Modellen; d-Wert via ADF-Test minimieren
- Bybit-Endpoint(s): REST `/v5/market/open-interest`, `/v5/market/funding/history`, `/v5/market/kline`
- Benötigte Datenfelder: openInterest, fundingRate, lastPrice (alle als Zeitreihe)
- Novelty-Score: 3 | Bekannte Methode, selten auf Bybit-OI angewandt
- Umsetzungskomplexität: LOW
- Edge-Typ: Feature-Engineering (alle Edges)
- Literatur/Paper: López de Prado (2018) "Advances in Financial Machine Learning", Kap. 5

### METHODE: Permutation Entropy Regime-Filter
- Kategorie: E
- Kernprinzip: Ordnungs-basierte Komplexitätsmessung. Robust gegen Outlier, O(N·log N) — schnell genug für 100ms-Stream. Niedrige PE = strukturiertes Regime = höhere Edge-Wahrscheinlichkeit.
- Kernformel: `PE = −Σ p(π)·log p(π)` über alle Ordinal-Patterns π von Embedding-Dim m
- Konkreter Anwendungsfall: PE(lastPrice, m=4) auf rolling 100-Tick-Window; Trading nur erlaubt wenn PE < median(PE_{24h})
- Bybit-Endpoint(s): WS `tickers.{symbol}` (lastPrice 100ms)
- Benötigte Datenfelder: lastPrice
- Novelty-Score: 4 | Selten in Crypto, Streaming-Eignung hoch
- Umsetzungskomplexität: LOW
- Edge-Typ: Regime-Filter
- Literatur/Paper: Bandt & Pompe (2002) "Permutation Entropy: A Natural Complexity Measure for Time Series", Phys. Rev. Lett. 88

### METHODE: Long/Short Ratio Smart-Money Divergenz
- Kategorie: A
- Kernprinzip: Bybit's Long/Short-Ratio aggregiert über Konten (nicht Volumen). Bei extremem Retail-Skew (buyRatio > 0.75) UND gegenläufiger Preisbewegung → kleine Zahl institutioneller Gegenpositionen → Smart-Money-Signal.
- Kernformel: `Divergenz_t = sign(Return_{1h}) − sign(buyRatio − 0.5)`; Signal wenn Divergenz < 0 UND |buyRatio − 0.5| > 0.25
- Konkreter Anwendungsfall: Counter-Trend-Entry auf BTCUSDT, wenn Retail extrem long aber Preis fällt → Position-Größe der Smart-Money-Seite folgen
- Bybit-Endpoint(s): REST `/v5/market/long-short-ratio?period=1h` (auch 5min, 15min, 4h verfügbar)
- Benötigte Datenfelder: buyRatio, sellRatio, timestamp
- Novelty-Score: 4 | Bybit-spezifisches Konten-Aggregat statt Volume → seltener Datentyp
- Umsetzungskomplexität: LOW
- Edge-Typ: Alpha + Entry-Timing
- Literatur/Paper: Bybit Docs `/v5/market/long-short-ratio`; analog Han et al. (2022) "Sentiment-Aware Volatility Forecasting"

### METHODE: Hidden Markov Model (HMM) auf Vola-OFI-Funding
- Kategorie: D
- Kernprinzip: Latente Marktphasen (Trend-Up, Trend-Down, Mean-Revert, Hochvol) als versteckte Zustände. Emission-Wahrscheinlichkeiten über realized vol, OFI-Sign, fundingRate. Viterbi für Online-Decoding.
- Kernformel: `P(z_t | x_{1:t}) ∝ Σ P(z_t | z_{t−1})·P(x_t | z_t)·α_{t−1}(z_{t−1})` (Forward-Algorithm); Baum-Welch für Parameter-Estimation
- Konkreter Anwendungsfall: 4-State-HMM auf BTCUSDT; State-Wahrscheinlichkeiten als Gating-Features für Strategie-Aktivierung
- Bybit-Endpoint(s): WS `tickers.{symbol}` + WS `orderbook.50.{symbol}` (OFI-Berechnung)
- Benötigte Datenfelder: lastPrice (für Realized-Vol), bid/ask Sizes (OFI), fundingRate
- Novelty-Score: 3 | Klassisch, aber bewährt; Bybit-Features (Funding) als Emission neu
- Umsetzungskomplexität: MEDIUM
- Edge-Typ: Regime-Filter
- Literatur/Paper: Hamilton (1989) "A New Approach to the Economic Analysis of Nonstationary Time Series"; Rabiner (1989) "HMM Tutorial"

### METHODE: Iceberg-Order Detection via Queue-Replenishment
- Kategorie: B
- Kernprinzip: Iceberg-Orders zeigen sich als kontinuierliche Größen-Wiederherstellung auf demselben Preislevel nach jedem Hit. Detection via Auto-Korrelation von Level-Sizes nach Trade-Events.
- Kernformel: `IcebergScore_p = Σ I(Size_{p,t+δ} ≥ 0.8·Size_{p,t}) / N_hits`; wenn Score > 0.7 bei N > 5 → Iceberg vermutet
- Konkreter Anwendungsfall: Identifiziere institutionelle Akkumulation/Distribution auf BTCUSDT; Front-Run der versteckten Liquidität, alternativ als Support/Resistance-Level
- Bybit-Endpoint(s): WS `orderbook.200.{symbol}` (Delta-Stream) + WS `publicTrade.{symbol}`
- Benötigte Datenfelder: bid/ask Sizes pro Preislevel über Zeit, Trade-Side, Trade-Price
- Novelty-Score: 4 | Schwer, da Bybit keine echten Iceberg-Flags exponiert — Detection rein statistisch
- Umsetzungskomplexität: HIGH
- Edge-Typ: Entry-Timing + Alpha
- Literatur/Paper: De Prado, Easley, López (2012) "The Volume Clock"; Hautsch & Huang (2012) "Limit Order Book Dynamics"
