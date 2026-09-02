[SCOUT → CRITIC] STATUS: COMPLETE | METHODS: 14 | DOMAINS: 7

### METHODE: Quantum Coupled-Wave Bid/Ask + Ergodizitätsverletzung [PRIORITY]
- Herkunftsbereich: Quantenmechanik / Quantum Finance
- Kernprinzip: Bid- und Ask-Preise werden als Eigenwerte eines 2×2 Preis-Operators in verschränktem Zustand modelliert (ψ_AB = ψ_A ⊗ ψ_B). Gerichtete Preisbewegung entsteht NICHT durch externe Kräfte, sondern durch Ergodizitätsverletzung — wenn zeitlicher Mittelwert ≠ Ensemble-Mittelwert, hat das Orderbuch sein Gleichgewicht verloren und ein Ausbruch ist unausweichlich.
- Kernformel: E_t[X] − ⟨X⟩_ensemble ≠ 0 ; iℏ ∂ψ/∂t = Ĥψ mit Ĥ = Ĥ_bid ⊗ I + I ⊗ Ĥ_ask + V_int
- Übertragungsidee: Rolling 1-min Mittelwert des Mid-Price vs. Ensemble-Mittelwert über parallele Symbole (BTCUSDT, ETHUSDT, SOLUSDT). Wenn |E_t − ⟨⟩| > kσ → Edge-Fenster für Direction-Trade.
- Bybit-Endpoint(s): WebSocket `orderbook.1.{symbol}` (Top-of-Book bid/ask) + `tickers.{symbol}` über mehrere Symbole parallel
- Benötigte Datenfelder: bid1Price, ask1Price, lastPrice, markPrice, ts (Millisekunden-Timestamp)
- Novelty-Score: 5 | Begründung: Ergodizitätsverletzung als Echtzeit-Direction-Signal ist in retail Bybit-Bots praktisch unerforscht.
- Umsetzungskomplexität: HIGH | Begründung: Erfordert simultane Multi-Symbol-Streams und sorgfältige Definition des Ensemble-Operators.
- Edge-Typ: Regime
- Literatur-Hinweis: Choustova (arXiv:quant-ph/0109122, 2007); Shen & Haven "Quantum coupled-wave theory" (arXiv:2002.04212, 2020)

### METHODE: SpikeWavformer Event-Driven Ingestion [PRIORITY]
- Herkunftsbereich: Neurowissenschaft / Spiking Neural Networks
- Kernprinzip: Spiking-Neuronen feuern nur, wenn das Membranpotenzial einen Schwellenwert überschreitet. Kombiniert mit Diskreter Wavelet-Transformation (DWT) und Spiking Self-Attention entsteht ein energie-effizienter Event-Filter, der Polling ersetzt: Engine aktiviert sich NUR bei genuinen Anomalien (OI-Sprung, Liquidations-Cluster).
- Kernformel: V_m(t+Δt) = αV_m(t) + Σw_i s_i(t) − V_reset·s_out(t) ; DWT: c_{j,k} = Σ x[n]·ψ*_{j,k}[n]
- Übertragungsidee: openInterestValue-Delta + allLiquidation-Volume bilden Input-Spikes. DWT (Symlets sym4) zerlegt Tick-Stream; Membranpotenzial integriert über Sliding Window 500ms; Spike triggert Downstream-Pipeline.
- Bybit-Endpoint(s): WebSocket `tickers.{symbol}` (100ms) + `allLiquidation.{symbol}` (500ms)
- Benötigte Datenfelder: openInterest, openInterestValue, lastPrice, ts ; aus allLiquidation: T, s, v, p, S
- Novelty-Score: 5 | Begründung: SpikeWavformer ist BCI/EEG-State-of-the-Art (2025), Übertragung auf Crypto-Microstructure ist neu.
- Umsetzungskomplexität: HIGH | Begründung: snnTorch/Norse-Stack + DWT-Live-Streaming benötigt sorgfältiges Tuning der Spike-Schwellen.
- Edge-Typ: Microstructure / Timing
- Literatur-Hinweis: SpikeWavformer (Frontiers in Neuroscience 2025, doi:10.3389/fnins.2025.1652274); Lu et al. "MTSA-SNN" (arXiv:2402.05423)

### METHODE: Multivariater Hawkes-Prozess Spektralradius ρ(Φ) [PRIORITY]
- Herkunftsbereich: Geophysik / Seismologie → Point-Process-Theorie
- Kernprinzip: Orderbuch als 6-dimensionales selbst-erregendes Punktprozess-System (MO±, LO±, CX±). Branching Matrix Φ̄_ij = α_ij beschreibt endogene Kausalität. Spektralradius ρ(Φ) → 1 markiert kritischen Zustand: minimaler Trigger löst Kaskade aus (empirisch 70-90% des HFT-Flows endogen).
- Kernformel: λ_i(t) = μ_i + Σ_j ∫₀ᵗ φ_ij(t−s) dN_j(s) ; φ_ij(t) = α_ij β_ij e^(−β_ij t)
- Übertragungsidee: Aus dem trades-Stream + orderbook-Deltas die 6 Event-Typen extrahieren, rollend (5-min Fenster) MLE der Matrix; wenn ρ(Φ) > 0.9 → Kaskaden-Alarm, Position-Sizing reduzieren oder Momentum-Entry.
- Bybit-Endpoint(s): WebSocket `publicTrade.{symbol}` + `orderbook.50.{symbol}`
- Benötigte Datenfelder: aus publicTrade: T, p, v, S (Buy/Sell); aus orderbook: u (updateId), b/a arrays mit price/size, ts
- Novelty-Score: 4 | Begründung: In Equity-LOB etabliert (Bacry/Muzy), in Bybit-Crypto-Retail-Pipelines selten.
- Umsetzungskomplexität: HIGH | Begründung: 6-D MLE mit Exponential-Kernel ist rechenintensiv; tick benutzt das `tick` Paket oder eigene C++-Routine.
- Edge-Typ: Microstructure / Risk
- Literatur-Hinweis: Achab et al. "Analysis of order book flows using nonparametric estimation of branching ratio matrix" (arXiv:1706.03411); Rambaldi/Bacry/Lillo (2017); Frangos et al. "Hawkes-based cryptocurrency forecasting" (arXiv:2312.16190)

### METHODE: Gutenberg-Richter + Omori auf Liquidationskaskaden
- Herkunftsbereich: Seismologie
- Kernprinzip: Liquidationen folgen Erdbeben-Statistik: Magnituden-Verteilung log₁₀ N(≥M) = a − bM (Gutenberg-Richter); Aftershock-Rate n(t) = K/(t+c)^p (Omori-Utsu). Nach Mainshock kann man Aftershock-Rate vorhersagen und Mean-Reversion-Entry timen, bevor Liquidations-Echo abklingt.
- Kernformel: log N(≥M) = a − bM ; λ(t|H_t) = K/(t−t_main+c)^p ; Mainshock-Schwelle: v_USD > Quantil_99(rolling 24h)
- Übertragungsidee: allLiquidation-Stream aggregieren auf 1-s-Buckets; Mainshock = größtes Liq-Event in 5min; danach Omori-Fit für die nächsten 30min Aftershocks; b-Wert < 1 → unausgewogene Volatilität → Trend-Fortsetzung.
- Bybit-Endpoint(s): WebSocket `allLiquidation.{symbol}` (500ms aggregierte Pushes)
- Benötigte Datenfelder: T (timestamp), s (symbol), v (size), p (price), S (side Buy/Sell)
- Novelty-Score: 4 | Begründung: Lillo/Mantegna haben Omori für Indizes gezeigt; auf Bybit Liquidations-Stream direkt anwenden ist neu.
- Umsetzungskomplexität: MEDIUM | Begründung: MLE für b-Wert und Omori-Parameter ist Standard (scipy), nur Stream-Aggregation nötig.
- Edge-Typ: Timing / Risk
- Literatur-Hinweis: Lillo & Mantegna "Power-law relaxation in a complex system: Omori law after a financial market crash" (Phys. Rev. E 68, 016119, 2003; arXiv:cond-mat/0111257); Petrosky-Nadeau "Aftershock prediction for HF markets" (arXiv:1203.5893)

### METHODE: Topologische Datenanalyse / Persistent Homology
- Herkunftsbereich: Algebraische Topologie / Materialwissenschaft
- Kernprinzip: Aus rollender Multi-Asset-Returns-Matrix wird Punktwolke gebaut; Vietoris-Rips-Filtration berechnet Geburts-/Sterbe-Zeiten topologischer Features (Löcher H_1). Die L¹-Norm der Persistence Landscape steigt vor Crashes signifikant — robuster Early-Warning-Indikator.
- Kernformel: L¹(λ) = Σ_k ∫|λ_k(t)|dt mit Persistence Landscape λ_k(t)=max{min(t−b_i, d_i−t), 0}_k-max
- Übertragungsidee: Rolling 100-Bar-Fenster über (BTC, ETH, SOL, BNB, XRP) 1-min Returns auf Bybit; Ripser/giotto-tda berechnet PH; L¹-Spike > z=3 → Risk-Off-Signal (Hedge oder Position abbauen).
- Bybit-Endpoint(s): REST `/v5/market/kline` (interval=1) ODER WebSocket `kline.1.{symbol}` über 5+ Symbole
- Benötigte Datenfelder: open, high, low, close, volume, startTime
- Novelty-Score: 4 | Begründung: TDA ist in Equity-Markets (Gidea/Katz 2017) etabliert, auf Bybit-Multi-Coin-Korrelationsstruktur noch selten.
- Umsetzungskomplexität: MEDIUM | Begründung: Ripser++ rechnet PH in <100ms für 100×5 Matrizen; Pipeline-Integration trivial.
- Edge-Typ: Regime / Risk
- Literatur-Hinweis: Gidea & Katz "Topological Data Analysis of Financial Time Series: Landscapes of Crashes" (arXiv:1703.04385, Physica A 2018); MDPI Computers 2025 "Topological ML for Financial Crisis Detection"

### METHODE: Recurrence Quantification Analysis (RQA)
- Herkunftsbereich: Nichtlineare Dynamik (Eckmann/Kamphorst/Ruelle)
- Kernprinzip: Phasenraum-Rekonstruktion (Takens-Einbettung) erzeugt Trajektorie; Recurrence Plot R_ij=Θ(ε−‖x_i−x_j‖). Metriken DET (Determinismus), LAM (Laminarität), ENTR detektieren kritische Regimes vor Phasenübergängen.
- Kernformel: R_ij = Θ(ε − ‖x_i − x_j‖) ; DET = Σ_{l≥l_min} lP(l)/Σ_l lP(l)
- Übertragungsidee: Auf 5-min Mid-Price-Returns von BTCUSDT/ETHUSDT, Einbettungs-Dimension m=3, Delay τ via mutual information; DET-Spike + LAM-Spike → Laminar-Phase (Konsolidierung vor Breakout).
- Bybit-Endpoint(s): WebSocket `kline.5.{symbol}` oder aggregiert aus `publicTrade.{symbol}`
- Benötigte Datenfelder: close, ts
- Novelty-Score: 4 | Begründung: RQA in Crypto-Bots wenig verbreitet; Crash-Vorhersage bei DAX/NASDAQ funktionierte (Strozzi).
- Umsetzungskomplexität: MEDIUM | Begründung: pyrqa-Bibliothek vorhanden; CPU-effizient bei Fenster <500.
- Edge-Typ: Regime
- Literatur-Hinweis: Strozzi, Zaldívar, Zbilut "Recurrence Plot and RQA for Detecting Critical Regime" (Int. J. Mod. Phys. C 16(05), 2005, arXiv:cond-mat/0412765); Bastos/Caiado (Physica A 390, 2011)

### METHODE: Wavelet-Symlet-Denoising des Orderbuch-Imbalance
- Herkunftsbereich: Neurowissenschaft / Biomedical Signal Processing (EEG-Pipeline)
- Kernprinzip: Diskrete Wavelet-Transformation mit Symlets (sym4-sym8) hat fast linear-phasige Filter → exakte Latenz-Erhaltung. Trennt Market-Maker-Mikrorauschen von Smart-Money-Tape via Soft-Thresholding der Detail-Koeffizienten.
- Kernformel: W_{j,k} = Σ_n x[n]ψ*_{j,k}[n] ; x̂[n]=Σ thresh(W_{j,k}, λ_j)·ψ_{j,k}[n] ; λ_j = σ_j√(2 log N)
- Übertragungsidee: Orderbuch-Imbalance I(t) = (Σbid_size − Σask_size)/(Σbid+Σask) auf Top-20-Levels; auf I(t) DWT sym6 mit 4-Level-Zerlegung; rekonstruiertes Signal speist Hawkes/SNN-Layer.
- Bybit-Endpoint(s): WebSocket `orderbook.50.{symbol}` (50-Level Delta-Stream)
- Benötigte Datenfelder: b (Bid-Array [price,size]), a (Ask-Array), u (updateId), ts
- Novelty-Score: 3 | Begründung: Wavelet-Denoising in TA bekannt, aber direkte Anwendung auf L2-Imbalance + Symlet-Wahl mit Phasenpräzision ist seltener.
- Umsetzungskomplexität: LOW | Begründung: PyWavelets `pywt.swt`/`pywt.dwt` läuft <1ms pro Update.
- Edge-Typ: Microstructure
- Literatur-Hinweis: Mallat "A Wavelet Tour of Signal Processing" (1999); Daubechies Symlets construction; Frontiers Neuroscience 2025 (SpikeWavformer-Vorarbeit)

### METHODE: TFSAX + Smith-Waterman Sequence Alignment
- Herkunftsbereich: Bioinformatik / Genomik
- Kernprinzip: Preiszeitreihe wird via PAA + z-Norm + Gauß-Bins in Symbolsequenz transformiert; TFSAX fügt Trend-Distanz- und Trend-Form-Faktor hinzu. Smith-Waterman findet lokal optimale Alignments mit Insertions/Deletions → toleriert zeitliche Verzerrungen, an denen Euklid-Distanz scheitert.
- Kernformel: PAA: C̄_i = (w/n)Σ_{j=n/w(i-1)+1}^{n/w·i} c_j ; SW: H(i,j)=max{0, H(i-1,j-1)+s(a_i,b_j), H(i-1,j)−d, H(i,j-1)−d}
- Übertragungsidee: 24h Kline-1min-Returns → TFSAX-Sequenz Länge 1440 mit Alphabet |A|=5; in 1-Jahres-Historie nach ähnlichen Sequenzen suchen; konditionale Forward-Return-Verteilung der Top-k Matches.
- Bybit-Endpoint(s): REST `/v5/market/kline?category=linear&symbol={s}&interval=1&start=...&end=...`
- Benötigte Datenfelder: close, volume, startTime (Liste der Kline-Tuples)
- Novelty-Score: 4 | Begründung: TFSAX (2019) kombiniert mit Bioinformatik-Alignment auf Bybit ist im Retail-Bereich praktisch unbenutzt.
- Umsetzungskomplexität: MEDIUM | Begründung: saxpy/tslearn + Bio.pairwise2 → CPU-rechenintensiv bei großer Historie, GPU-SW möglich.
- Edge-Typ: Pattern
- Literatur-Hinweis: Yu, Zhu, Wan "A Novel Trend Symbolic Aggregate Approximation" (arXiv:1905.00421, 2019); Smith & Waterman (J. Mol. Biol. 1981); Lin et al. SAX (DMKD 2007)

### METHODE: Renyi-Transfer-Entropy Lead-Lag-Graph BTC→Alt
- Herkunftsbereich: Informationstheorie
- Kernprinzip: Renyi-Transfer-Entropy verallgemeinert Schreiber-TE und gewichtet Tail-Events stärker (q>1) → fängt non-lineare extreme Kopplung. Asymmetrie T_X→Y ≠ T_Y→X liefert gerichteten Informationsfluss.
- Kernformel: T^q_Y→X = (1/(1−q)) log Σ p(x_{n+1},x_n^{(k)})·[Σ p(y_n^{(l)}|x_n^{(k)})·p(x_{n+1}|x_n^{(k)},y_n^{(l)})^{q-1}]/Σ p(x_{n+1}|x_n^{(k)})^q
- Übertragungsidee: 1-min Returns für Top-20 Bybit-Perps; rollend 4h-Fenster; gerichtete Kanten T>0.05 Bit bilden Lead-Lag-Graph. BTC führt typisch → Alt-Trade nach BTC-Move mit 30-60s Lag.
- Bybit-Endpoint(s): REST `/v5/market/kline` oder WebSocket `kline.1.{symbol}` parallel für 20 Symbole
- Benötigte Datenfelder: close, ts
- Novelty-Score: 4 | Begründung: Standard-TE wurde für Crypto angewandt, aber Renyi-Variante mit Tail-Gewichtung + Echtzeit-Graph-Update ist neuer.
- Umsetzungskomplexität: MEDIUM | Begründung: IDTxl/PyInform-Bibliotheken vorhanden; Latenz ~50ms bei 20×20 Matrix.
- Edge-Typ: Pattern / Timing
- Literatur-Hinweis: Assaf et al. "Using transfer entropy to measure information flows between cryptocurrencies" (Physica A 586, 2022, S0378437121007573); Keskin & Aste "Information-theoretic measures for non-linear causality" (R. Soc. Open Sci. 2020, arXiv:1906.05740)

### METHODE: Shannon-Entropie Kollaps des L2-Orderbuchs
- Herkunftsbereich: Informationstheorie / Thermodynamik
- Kernprinzip: H = −Σp_i log p_i über die Größen-Verteilung der Top-N Bid+Ask-Level quantifiziert Heterogenität. Hohe H = chaotisch, random-walk-nah, kein Edge. Niedrige H = institutionelle Synchronisation, Edge-Fenster.
- Kernformel: p_i = size_i / Σ size ; H = −Σ p_i log₂ p_i ; KL: D(P‖Q) = Σ p_i log(p_i/q_i)
- Übertragungsidee: Auf orderbook.50 Stream, alle 100ms H_bid und H_ask berechnen; gleitendes Quantil; wenn H < Quantil_5 → Greenlight für Direction-Trade (gefolgt von Hawkes-Bestätigung).
- Bybit-Endpoint(s): WebSocket `orderbook.50.{symbol}`
- Benötigte Datenfelder: b (Array [price,size]), a, u, ts
- Novelty-Score: 3 | Begründung: H in LOB-Literatur erwähnt (ECB), aber als binärer Greenlight-Filter selten umgesetzt.
- Umsetzungskomplexität: LOW | Begründung: O(N) pro Update, trivial vektorisierbar.
- Edge-Typ: Regime / Microstructure
- Literatur-Hinweis: Gould et al. "Limit order books" (Quant. Finance 13, 2013); ECB Working Paper zu LOB-Entropie unter HFT

### METHODE: Permutation Entropy Volatility Early-Warning
- Herkunftsbereich: Nichtlineare Dynamik / Informationstheorie (Bandt & Pompe)
- Kernprinzip: PE quantifiziert ordinalen Komplexitätsgrad einer Zeitreihe, robust gegen Skalierung/Drift. Niedrige PE (verbotene Muster häufen sich) ist Vorbote von Vol-Spikes — empirisch 34% höhere Detektionsrate als GARCH.
- Kernformel: PE_m = −Σ p(π) log p(π) , über alle m! Ordnungspermutationen π von Embedding-Dim m
- Übertragungsidee: Tick-Mid-Price oder 5s-Returns, m=4 oder 5, τ=1; rollendes Fenster N=500; PE-Drop unterhalb 5%-Quantil → erwarte Vol-Cluster in den nächsten 5-15 min → Volatility-Breakout-Long oder Straddle-artige Strategie.
- Bybit-Endpoint(s): WebSocket `publicTrade.{symbol}` aggregiert auf 5s, oder `kline.1.{symbol}`
- Benötigte Datenfelder: p (price) bzw. close, ts
- Novelty-Score: 3 | Begründung: PE in HF-Finance bekannt (Zanin 2012), aber kombiniert mit Forbidden-Pattern-Coupling und Bybit-Tick-Stream neuartig.
- Umsetzungskomplexität: LOW | Begründung: ordpy/antropy-Paket; O(N) Updates.
- Edge-Typ: Regime / Timing
- Literatur-Hinweis: Bandt & Pompe (Phys. Rev. Lett. 88, 2002); Zanin et al. "Permutation approach, HFT and variety of micro patterns" (Physica A 2014, S0378437114005020); Preprints 2025 "Multiscale PE and Forbidden Patterns"

### METHODE: SIR-Kompartiment-Modell für Liquidations-Contagion
- Herkunftsbereich: Epidemiologie (Kermack-McKendrick)
- Kernprinzip: Trader-Population zerfällt in S (Susceptible, gehebelte Longs nahe Liq-Preis), I (Infected, gerade liquidiert), R (Recovered, geschlossen/gestoppt). dI/dt = βSI − γI modelliert Kaskaden-Ausbreitung. R₀=β/γ > 1 → Kaskade selbsterhaltend.
- Kernformel: dS/dt=−βSI ; dI/dt=βSI−γI ; dR/dt=γI ; R₀=βS₀/γ
- Übertragungsidee: S ≈ openInterest abzüglich kürzlich liquidiertem Volumen; I = laufende Liquidationsrate aus allLiquidation; β kalibriert über rollende OLS. Wenn geschätztes R₀ > 1 → Reverse-Position (Counter-Trend nach Klimax) oder Risk-Off.
- Bybit-Endpoint(s): WebSocket `allLiquidation.{symbol}` + `tickers.{symbol}` (openInterest)
- Benötigte Datenfelder: openInterest, openInterestValue; aus allLiquidation: T, v, p, S
- Novelty-Score: 4 | Begründung: SIR für DeFi-Risk-Contagion existiert akademisch, aber direkte Echtzeit-R₀-Schätzung auf Bybit-Liquidation-Stream ist neu.
- Umsetzungskomplexität: MEDIUM | Begründung: ODE-Fit via scipy.integrate + curve_fit, Online-Update möglich.
- Edge-Typ: Risk / Timing
- Literatur-Hinweis: Demiralay & Golitsis "Game-based delayed risk contagion" (Annals Op. Res. 2025); SIR-Hawkes (arXiv:1711.01679); SSRN 5611392 zu Oct-2025 19B-Liquidation-Cascade

### METHODE: Multifractal Detrended Fluctuation Analysis (MF-DFA)
- Herkunftsbereich: Statistische Physik / Geophysik (Kantelhardt et al.)
- Kernprinzip: Skalierungs-Exponent h(q) für verschiedene Momenten-Ordnungen q quantifiziert Multifraktalität: Δh = h(q_min)−h(q_max) misst Heterogenität der Skalierungs-Eigenschaften. Δh ist groß in ineffizienten/regimewechsel-Phasen.
- Kernformel: F_q(s) = {(1/2N_s)Σ[F²(ν,s)]^{q/2}}^{1/q} ∝ s^{h(q)} ; τ(q)=qh(q)−1
- Übertragungsidee: Auf 1-min Bybit BTCUSDT Returns rollend N=2048 Bars; MF-DFA in [s_min=16, s_max=256], q∈[−5,5]; Δh-Spike > z=2 → Regime-Change-Alarm, Strategie umschalten (Mean-Reversion ↔ Momentum).
- Bybit-Endpoint(s): REST `/v5/market/kline?category=linear&symbol=BTCUSDT&interval=1`
- Benötigte Datenfelder: close, ts
- Novelty-Score: 3 | Begründung: MF-DFA für BTC etabliert (Shrestha 2021), Anwendung als Echtzeit-Regime-Switch in Trading-Pipeline weniger publiziert.
- Umsetzungskomplexität: MEDIUM | Begründung: MFDFA-Paket (python) ~200ms pro Fenster.
- Edge-Typ: Regime
- Literatur-Hinweis: Shrestha "MF-DFA of Return on Bitcoin" (Int. Rev. Finance 21, 2021); Watorek et al. "Multifractality and its sources in digital currency market" (arXiv:2510.13785, 2025); Drozdz et al. (arXiv:2411.05951)

### METHODE: Kalman-Filter für Funding-Rate-Premium-Decomposition
- Herkunftsbereich: Kontrolltheorie / Aerospace (Kalman 1960)
- Kernprinzip: Funding Rate = Interest Rate Component + Premium Index. Premium-Index ist ungeobserved → State-Space-Modell mit Kalman-Filter trennt den persistenten "fair-funding"-Drift vom transienten Sentiment-Spike. Sentiment-Spike >2σ ist Contrarian-Signal.
- Kernformel: x_t = F·x_{t-1} + w_t ; z_t = H·x_t + v_t ; K_t = P_t H'(HP_tH'+R)^{-1}
- Übertragungsidee: z_t = aktuelle Funding-Rate (8h Bybit-Wert) + basis = (markPrice−indexPrice)/indexPrice; State = [trend_funding, transient_sentiment]; bei |sentiment_t| > 2·sqrt(P_{22,t}) → Fade-Trade gegen Overcrowded Side.
- Bybit-Endpoint(s): WebSocket `tickers.{symbol}` (fundingRate, nextFundingTime, markPrice, indexPrice) ; REST `/v5/market/funding/history`
- Benötigte Datenfelder: fundingRate, nextFundingTime, markPrice, indexPrice, lastPrice
- Novelty-Score: 3 | Begründung: Kalman-Filter auf Funding-Rate ist in Quant-Bots vereinzelt zu finden, Decomposition in Trend+Transient als explizites Contrarian-Signal weniger systematisch.
- Umsetzungskomplexität: LOW | Begründung: filterpy/pykalman, einfache 2-D State-Space-Implementation.
- Edge-Typ: Timing / Risk
- Literatur-Hinweis: Ackerer, Hugonnier, Jermann "Perpetual Futures Pricing" (arXiv:2310.11771); Angeris et al. "Designing funding rates for perpetual futures" (arXiv:2506.08573, 2025); He & Manela "Fundamentals of Perpetual Futures" (arXiv:2212.06888)
