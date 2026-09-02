# FINAL PRD — Bybit Retail Edge Research System
**Product Requirements Document · Edge Research Framework v1**
**Datum:** 2026-06-10 · **Autor:** PRD Architect · **Status:** FINAL
**Grundlage:** `synthesis.md` (26 validierte Methoden), `critic_report_1.md` (PASS), `round_1_scout.md`, `round_1_quant.md`, `data_audit.md` (verifizierter Bybit-Katalog, Stand 2026-06-10)
**Zielgruppe:** Algorithmischer Trader mit Python-Grundkenntnissen, erfahren in Strategieentwicklung/Backtesting. Hardware: RTX 5060 Ti (16 GB VRAM), 82 GB RAM lokal; VPS mit Docker/Ubuntu. Kein Code in diesem Dokument — Konzept-Blaupause für die Implementierung.

---

## Inhaltsverzeichnis

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

Autonome Identifikation, Bewertung und Priorisierung innovativer Mustererkennungs-Methoden für Bybit Perpetual Futures (ergänzend Options/Spot), die einem Retail-Trader einen messbaren statistischen Edge verschaffen — unter den verbindlichen Realitätsgrenzen des Daten-Audits (Fees: 2/5.5 bp Maker/Taker, EU-VPS-Latenz ~145–200 ms RTT, REST 600 req/5 s) und gegen die empirische Kestrel-v1.4-Baseline: Richtungsprognose AUC ≈ 0.50 (Münzwurf), Realisierte-Volatilitäts-Prognose R² ≈ 0.25 (deutlich prognostizierbar). Aus 31 erforschten Methoden wurden nach Critic-Evaluation 26 validiert (20 Strong Accept, 6 Accept) und zu einer 5-Layer-Pipeline mit 5 Kombinationsstrategien synthetisiert.

### Top-3-Erkenntnisse

1. **Der Edge liegt nicht in der Preisreihe, sondern in der Derivate-Mechanik.** Die höchsten Critic-Scores erreichen Methoden, die Information nutzen, die in OHLCV strukturell nicht existiert: Funding-Clamp-Stau via 1-min-Premium-Index-Kline (Q1, Score 11), Liquidations-Anatomie mit Bankruptcy-Preisen, Insurance-Delta und ADL-`pr` (Q2), exakte Taker-Side + RPI-Flags für Toxic-Flow (Q6, Score 11). Direktionale Claims sind nur regime-konditioniert zulässig (bedingte AUC > 0.55), unkonditioniert gilt die 0.50-Baseline.
2. **Historie ist der Engpass, nicht Bandbreite.** 8 der 26 Methoden benötigen Datenströme ohne jede API-Historie (Liquidationen, Insurance, ADL, RPI-Buch, IV-Flächen, Orderbuch-Deltas, sub-5-min-OI). Jeder Tag ohne eigene 24/7-Aufzeichnung ist unwiederbringlich verloren — deshalb ist die Recording-Infrastruktur (~30–70 GB/Monat komprimiert) **Phase 0 und erster Implementierungsschritt überhaupt**. Bybit-exklusive Streams (RPI-Orderbook, ADL-Alert) sind in der Literatur unerschlossene First-Mover-Datensätze.
3. **Volatilität ist das einzige belegte Signal — und wird zum Fundament.** Der L5-Risk-Layer (Q4 PatchTST-RV als Kern, Q15/Q16/Q17/Q2 als Zusatzkanäle, hartes Gate: out-of-sample R² > 0.25) versorgt alle direktionalen Module mit Sizing und Stops. Das Quantum-Risk-Modul der ursprünglichen Referenz-Pipeline wurde nach Critic-Befund (S6: Edge = 0, Analogie ohne kausalen Mechanismus) durch dieses empirisch fundierte Risk-Bundle ersetzt.

### Empfohlene Architektur in 3 Sätzen

Eine event-getriebene 5-Layer-Kaskade: L1-Ingestion (deterministischer F0-Schwellwert-Trigger ab Tag 1, SNN-Gate S7 als spätere Erweiterung) filtert die Datenflut, L2 entrauscht (Symlet-DWT, kausales CEEMDAN), L3 entscheidet über Handelbarkeit via 3-Gate-Stack (schnell: PE+KL-Kollaps; mittel: BOCPD; langsam: GMM-Vol-Regime+VRP) plus unbedingtem VPIN-Veto. L4 erzeugt Signale in vier Modulen (Kaskaden-Lebenszyklus, Funding-Uhr, Lead-Lag-Graph, Hidden-Liquidity-Karte), L5 (Risk-Bundle Q2×Q4×Q15×Q17) bestimmt Sizing, Stops und Strategie-Freischaltung. Alle Komponenten sind als Sekunden-bis-Minuten-Features spezifiziert — kein Latenz-Race, kein Colocation-Bedarf.

### Erwarteter Edge-Typ

Primär **Timing** (Settlement-Fenster, Kaskaden-Nachbeben, Lead-Lag-Fenster) und **Risk/Vol** (RV-Prognose, Tail-Schutz, Vol-Targeting); sekundär **Regime** (Gate-konditionierte Direktionalität) und **Microstructure** (OFI, Hidden Liquidity als Feature, nicht als Race).

### Grober Zeitplan

- **Woche 1–2:** Recording-Infrastruktur + F0-Trigger (Phase 0)
- **Woche 3–6:** Quick Wins backtesten (Q1, Q12+S9, Q7+Q11, Q6) — erste Edge-Bestätigung/Falsifikation
- **Woche 7–12:** Risk-Fundament (Q4-Vol-Stack, Q8, Q17, Q2-Live-Score)
- **Woche 13–20:** Mini-Strategien K1–K3 komplett; Beginn Paper-Trading auf Bybit Testnet/Demo
- **Ab Woche 21:** Moonshots (S2, Q14+S12, S7, Q9) + Live-Testing-Gate: Sharpe ≥ 1.5 nach Fees, Max Drawdown < 15 %, Win-Rate > 52 % über ≥ 3 Monate Paper-Trading

**Erste live-testbare Version (K2 Funding-Uhr, minimal):** realistisch ab Woche 10–13.

---

## 2. PROBLEMDEFINITION

### Warum haben Retail-Trader auf Bybit standardmäßig keinen Edge?

1. **Empirische Baseline:** Eigene Vorarbeit (Kestrel v1.4) zeigt: Richtungsprognose mit klassischen Features auf OHLCV liefert AUC ≈ 0.50. Alles, was nur Preis-/Volumenhistorie verarbeitet (Indikatoren, Standard-ML auf Candles), ist auf diesem Markt informationslos.
2. **Fee-Hürde:** Taker-Roundtrip Perp = 11 bp + Slippage. Jede direktionale Taker-Strategie braucht > 12–15 bp erwartete Bewegung pro Trade. Hochfrequente Signale sind nur maker-fähig (4 bp Roundtrip) überlebensfähig — mit Adverse-Selection-Risiko und Konkurrenz durch unsichtbare RPI-Orders.
3. **Latenz-Realität:** Matching Engine in AWS Singapur; EU-VPS ~145–200 ms RTT. Der 10-ms-L1-Orderbuch-Push ist bei Reaktion ~15–20 Updates alt. Queue-Position-Games, Sub-Sekunden-Marketmaking und Cross-Exchange-Latency-Arb sind **ausgeschlossen**.
4. **Gesättigte Methoden:** Einfacher Funding-Carry (BIS-dokumentiert, seit 2024 komprimiert), Standard-Momentum/Mean-Reversion auf Candles, simple Orderbuch-Imbalance auf L1 — institutionell abgegrast bzw. nach Fees tot.

### Welche Informationsasymmetrien sind ausbeutbar?

- **Mechanische Zwangsflüsse:** Liquidationen sind preisinsensitive Marktaufträge; Funding-Settlement ist ein deterministisch getimter Zwangstermin. Wer *muss* handeln, ist prognostizierbarer als wer *will*.
- **Bybit-exklusive Datenströme, die fast niemand aufzeichnet:** `allLiquidation` mit Bankruptcy-Preis (Hebel-Anatomie der liquidierten Kohorte), Insurance-Pool-Delta (1 s, echte Illiquidität), ADL-`pr` (plattformweiter Stress-Sensor), RPI-Orderbuch (direkt beobachtbare Hidden Liquidity), 1-min-Premium-Index-Kline (kontinuierlicher Funding-Druck), Spread-Markt (handelbare Basis mit eigenem Orderbuch).
- **Aufzeichnungs-Asymmetrie:** Da diese Streams keine Historie haben, besitzt sie nur, wer ab Tag 1 aufzeichnet — ein Edge gegen alle, die später starten (First-Mover-Datensatz).
- **Regime-Konditionierung:** Zeitvariierende Markteffizienz (Adaptive Market Hypothesis) ist für Krypto dokumentiert; in Niedrig-Entropie-Fenstern kann bedingte Direktionalität existieren, wo sie unkonditioniert nicht existiert.

### Abgrenzung — was scheidet aus

Colocation/HFT-Stack, Latenz-Races jeder Art, L3-/Account-Level-Daten (nicht verfügbar), Cross-Exchange-Arbitrage mit Latenzkomponente, alles was im Daten-Audit nicht CONFIRMED/PARTIAL ist. Mikrostruktur-Daten werden ausschließlich als *Feature* (Prognose-Horizont ≥ Sekunden–Minuten) verwendet, nie als Execution-Race.

---

## 3. BYBIT-DATENBASIS

Vollständige Kartierung der genutzten Signale. Alle Angaben aus dem verifizierten Daten-Audit (`data_audit.md`, 2026-06-10). **Verbindlich: Was hier nicht steht, gilt als nicht verfügbar.** Korrektur durchgängig angewendet: WS `orderbook.500` existiert NICHT (L1 = 10 ms, L50 = 20 ms, L200 = 100 ms, L1000 = 200 ms); „ob500" ist nur das Download-Archiv.

| Signal | Endpoint | Frequenz | Relevante Felder | Historie | Genutzt in Layer |
|---|---|---|---|---|---|
| Ticker (Preis/OI/Funding live) | WS `tickers.{symbol}` | 100 ms (Derivate) | lastPrice, markPrice, indexPrice, openInterest, fundingRate, nextFundingTime, fundingCap | keine → Aufzeichnung | L1 (F0, S7), L3 (Q7, Q12), L4 (Q1, S3, S11) |
| Liquidationen (alle, mit Bankruptcy-Preis) | WS `allLiquidation.{symbol}` | 500 ms | T, s, v, p (Bankruptcy!), S | **keine REST-Historie** → Aufzeichnung/Tardis | L1 (F0, S7), L4 (S2, S4), L5 (Q2) |
| Orderbuch-Deltas flach | WS `orderbook.50.{symbol}` | 20 ms | b/a (Preis+Size je Level), seq/u | keine → Aufzeichnung | L1 (S7), L4 (Q3, Q14), L3 (S1) |
| Orderbuch-Deltas tief | WS `orderbook.200.{symbol}` (alt.: `orderbook.1000`, 200 ms) | 100 ms | b/a, seq/u | keine → Aufzeichnung | L2 (S12), L3 (S9), L4 (S2) |
| Trades (Taker-Side, Flags) | WS `publicTrade.{symbol}` | real-time | price, size, side (Taker), BT-, RPI-Flag | Archiv `public.bybit.com/trading/` (mehrjährig) | L3 (Q6 VPIN), L4 (S3, S11, Q3, Q14), L3 (S1) |
| RPI-Orderbuch (Hidden Liquidity sichtbar) | WS `orderbook.rpi.{symbol}` + REST `/v5/market/rpi_orderbook` | 100 ms / Poll | RPI-Size vs. Nicht-RPI-Size je Level (50 Level) | keine → **First-Mover-Aufzeichnung** | L4 (Q14) |
| Insurance-Pool | WS `insurance.USDT` (+REST `/v5/market/insurance`) | 1 s | balance, USD-Wert je Pool | keine → Aufzeichnung | L5 (Q2) |
| ADL-Alert | WS `adlAlert.{coin}` + REST `/v5/market/adl-alert` | 1 s / 1 min | `pr` (8h-PnL-Drawdown-Ratio), Trigger-Schwellen | keine → Aufzeichnung | L5 (Q2) |
| Kline OHLCV | REST `GET /v5/market/kline` (+WS `kline.1`) | 1 min+, 1000/Req | OHLCV, confirm-Flag | bis Symbol-Launch (BTC ab ~2018/2020) | L2 (Q16), L3 (Q8, Q12, Q17), L4 (S5, Q9), L5 (Q4, Q15) |
| Premium-Index-Kline | REST `GET /v5/market/premium-index-price-kline` | 1 min, 1000/Req | Premium-Index-OHLC | tief paginierbar | L4 (Q1, Q5-Proxy, Q9), L3 (Q8), L2 (Q16) |
| Funding-Historie | REST `GET /v5/market/funding/history` | je fundingInterval (1–8 h), 200/Req | fundingRate, fundingRateTimestamp | volle Settlement-Historie | L4 (Q1, S5, Q9), L3 (Q8) |
| Open Interest (Historie) | REST `GET /v5/market/open-interest` | 5 min–1 d | openInterest, singleOpenInterest | bis Launch | L3 (Q7), L5 (Q2), L4 (Q9) |
| OI (sub-5-min) | via WS `tickers` | 100 ms | openInterest | nur live → Aufzeichnung | L1 (F0), L3 (Q7) |
| Long/Short-Account-Ratio | REST `GET /v5/market/account-ratio` | 5 min–1 d, 500/Page | buyRatio, sellRatio | **ab 2020-07-20** (≈6 Jahre gratis) | L3 (Q11-Feature) |
| Options-Kette (IV/Greeks) | REST `GET /v5/market/tickers?category=option&baseCoin=BTC`; WS `tickers.{symbol}` | 1 Request/Kette; 100 ms | markIv, bid1Iv/ask1Iv, delta/vega, OI je Strike, underlyingPrice | **keine IV-Historie** → Aufzeichnung | L3+L5 (Q17 VRP) |
| Historical Volatility Index | REST `GET /v5/market/historical-volatility` | stündlich | HV je Periode (7–270 d) | 2 Jahre | L3+L5 (Q17) |
| Spread-Markt (Basis handelbar) | REST/WS `/v5/spread/*` (orderbook 25 Level, tickers, recent-trade) | real-time | Spread-Bid/Ask/Last | keine → Aufzeichnung (Premium-Index als Backtest-Proxy) | L4/Execution (Q5) |
| Instruments-Info | REST `GET /v5/market/instruments-info` | statisch | fundingInterval (Minuten!), launchTime, tickSize | — | alle (Stammdaten) |
| Tick-/Orderbuch-Archiv | `public.bybit.com` (`trading/`, ob500-Snapshots) | Download csv.gz | Tick-Trades mit Taker-Side; 500-Level-Tages-Snapshots | Trades mehrjährig; ob500 uneinheitlich (PARTIAL) | Backtests Q6, Q3, Q15 |

**Rahmenwerte:** REST-Limit 600 req/5 s (Poll-Budget der Pipeline: < 15 req/min — unkritisch). WS-Limits großzügig (1000 Verbindungen/IP, hunderte Symbole parallel streambar). Speicher Live-Aufzeichnung: **~30–70 GB/Monat komprimiert** (~0.5–1 TB/Jahr) — VPS + lokale Spiegelung ausreichend.

---

## 4. METHODEN-KATALOG

Volleinträge, gruppiert nach Layer. Priorität gemäß Synthese: **Quick Win** (Priorität > 3.0, LOW/MED-Komplexität), **Moonshot** (Novelty 3, HIGH-Komplexität, Edge ≥ 2), sonst **Standard**. Alle Validierungskriterien sind harte Gates mit Abbruchkriterium; sämtliche Validierung erfolgt **walk-forward, niemals in-sample**.

---

### L1 — INGESTION

#### F0 — Fallback-Schwellwert-Trigger [L1] [Quick Win / Pflichtbaustein Tag 1]

**Herkunft:** System-Engineering (Critic-Auflage: Mitigation für Single-Point-of-Failure S7).
**Kernprinzip:** Deterministisches Regelwerk, das die Pipeline „scharf schaltet", sobald mindestens eine von vier Anomalie-Bedingungen erfüllt ist. Trivial, testbar, regime-neutral — und dauerhaftes Schatten-Gate zur Überwachung von S7.
**Mathematische Grundlage:** Rollierende Perzentile über 30 Tage je Symbol. Trigger wenn: `Liq-Volumen(1min) > P99` ODER `|dOI(1min)| > P99` ODER `|dPremiumIndex(1min)| > P98` ODER (`RV(1min) > P98` ODER `Spread > P98`).
**Bybit-Anwendung:** WS `tickers` (100 ms, inkl. OI), WS `allLiquidation` (500 ms), REST `open-interest`. Output: Trigger-Event an L2–L4.
**Implementierungsskizze:** Streaming-Aggregation auf 1-min-Buckets (polars/eigener Aggregator im Collector-Dienst); Perzentil-Speicher pro Symbol; Event-Bus (z. B. Redis Pub/Sub oder ZeroMQ).
**Backtesting-Ansatz:** Replay der eigenen Aufzeichnung + Tick-Archiv; Label „relevantes Event" = nachfolgende 30-min-RV im Top-Dezil.
**Validierungskriterien:** Recall ≥ 95 % auf gelabelten Großevents; ≤ 5 Fehl-Trigger/Tag/Symbol im Median. Abbruch: nicht vorgesehen (Pflichtbaustein); Schwellen werden nur aus Trainingsfenstern kalibriert.
**Hardware:** CPU-only, vernachlässigbar. RTX 5060 Ti nicht benötigt.
**Abhängigkeiten:** Recording-Infrastruktur (Phase 0).
**Zeitschätzung:** 2–3 Tage.
**Risiken:** Schwellen-Tuning auf In-Sample-Daten (Gegenmaßnahme: Perzentile nur aus Trainingsfenster); False Negatives bei neuartigen Events.

#### S7 — SpikeWavformer: SNN-Ingestion mit DWT [L1] [Moonshot]

**Herkunft:** Neurowissenschaft / Neuromorphic Computing.
**Kernprinzip:** Ein Spiking Neural Network feuert nur bei echten Anomalien (Membranpotenzial über Schwelle) und triggert dann eine Wavelet-Sub-Band-Analyse — radikale Datenreduktion: Die Analyse-Engine läuft nur bei Signal, nicht kontinuierlich.
**Mathematische Grundlage:** LIF-Neuron `tau * dV/dt = -(V - V_rest) + R * I(t)`, Spike wenn `V >= V_th`; DWT `W(j,k) = Sum_t x(t) * psi(j,k,t)` mit Symlet-Basis. Inputs als Spike-Trains kodiert (Rate-/Delta-Encoding von OI, Liquidationsvolumen, Buch-Imbalance).
**Bybit-Anwendung:** WS `tickers` (openInterest), `allLiquidation`, `orderbook.50` (20 ms). Output: Trigger + Sub-Band-Zerlegung an L2/L4.
**Implementierungsskizze:** snnTorch oder Norse (PyTorch); Encoding-Schicht → LIF-Layer → Schwellen-Logik; PyWavelets für DWT; Training/Kalibrierung offline auf aufgezeichneten Events, Inferenz auf VPS-CPU oder lokal.
**Backtesting-Ansatz:** Schatten-Betrieb gegen F0 (Disagreement-Monitoring): feuert S7 systematisch später/seltener als F0 bei relevanten Events → Rekalibrierung.
**Validierungskriterien:** S7 muss F0 dominieren: gleicher oder besserer Event-Recall (≥ 95 %) bei ≤ 50 % der F0-Trigger-Rate über 2 Monate Schattenbetrieb. Abbruch: nach 2 Kalibrierungs-Iterationen ohne Dominanz bleibt F0 das Gate, S7 wird archiviert.
**Hardware:** Training auf RTX 5060 Ti problemlos (SNN-Modelle hier < 1 GB VRAM); Inferenz CPU-tauglich.
**Abhängigkeiten:** F0 (Benchmark), Phase-0-Aufzeichnung (Event-Labels).
**Zeitschätzung:** 4–6 Wochen.
**Risiken:** Encoding-/Schwellen-Tuning (MITTEL); kein direkter Edge — Nutzen ist Effizienz/Latenz des Gesamtsystems.

---

### L2 — DENOISING

#### S12 — Symlet-DWT Spoofing-/Iceberg-Detektor [L2 (+L4)] [Standard]

**Herkunft:** Signalverarbeitung (phasenpräzise Wavelets).
**Kernprinzip:** Die Tiefe einzelner Orderbuch-Level als Zeitreihe; Symlet-Detail-Koeffizienten der feinsten Skalen isolieren abrupte, lokalisierte Sprünge — die Signatur wiederholt erscheinender/verschwindender Großorders (Spoofing) und nachfüllender Eisberge.
**Mathematische Grundlage:** DWT `W(j,k) = Sum_t x(t) * psi(j,k,t)`, psi aus Symlet-Filterbank; Anomalie-Score je Level = Energie der Detail-Koeffizienten feinster Skala, normiert auf rollierende Basis.
**Bybit-Anwendung:** WS `orderbook.200` (100 ms Deltas; Korrektur: „orderbook.500" existiert nicht). Signal: gegen die gespoofte Seite handeln, sobald die Wall verschwindet; Eisberg-Level als S/R-Marker an K5-Karte.
**Implementierungsskizze:** Buch-Rekonstruktor (geteilter Baustein) → Level-Zeitreihen → PyWavelets-DWT rollierend → Score-Stream.
**Backtesting-Ansatz:** Auf eigener `orderbook.200`-Aufzeichnung (Phase 0); indirekte Validierung mangels Ground-Truth-Labels.
**Validierungskriterien:** (a) S/R-Halte-Quote markierter Echte-Wall-Level ≥ 60 % über 30-min-Horizont; (b) „Wall verschwindet"-Signal: bedingte Richtungs-AUC > 0.55 out-of-sample. Abbruch: beide Gates nach 2 Monaten Datenlage verfehlt → nur noch passives Feature für K5.
**Hardware:** CPU-only (DWT auf Level-Reihen ist billig).
**Abhängigkeiten:** Phase-0-Buchaufzeichnung, Buch-Rekonstruktor.
**Zeitschätzung:** 2 Wochen.
**Risiken:** Buchführung aus Deltas fehleranfällig (seq-Lücken-Detektion zwingend); in Kaskadenphasen bedeutungslos (Bücher leeren sich).

#### Q16 — CEEMDAN-Dekomposition, streng kausal [L2] [Standard, bedingt]

**Herkunft:** Signalverarbeitung (Empirical Mode Decomposition; als Erweiterung zur v1-Wavelet-Denoising-Idee gekennzeichnet).
**Kernprinzip:** Rauschstabilisierte EMD zerlegt RV-/Premium-Index-Reihen datenadaptiv in Intrinsic Mode Functions (IMF). Energie-Shift Richtung Hochfrequenz = Stress-Indikator; niederfrequente IMFs = entrauschte Inputs für den Vol-Stack. **Kritisch: naive EMD ist Lookahead-behaftet — nur streng kausale Online-Varianten zulässig.**
**Mathematische Grundlage:** `x(t) = Sum_i IMF_i(t) + r(t)`; CEEMDAN über Ensemble `E_i[x + eps_i * w]` mit adaptivem Rauschen; Feature: IMF-Energieverteilung `E_i / Sum E_j` je Fenster.
**Bybit-Anwendung:** REST `kline` (1 min), `premium-index-price-kline`, `open-interest`. Output: Feature-Kanäle an Q4/Q9.
**Implementierungsskizze:** PyEMD mit strikt rollierendem Fenster (Zerlegung nur auf Daten bis t, Randbehandlung dokumentiert); 1-min-Batch.
**Backtesting-Ansatz:** Ablation im Vol-Stack: Q4 mit/ohne IMF-Kanäle, identische Walk-Forward-Splits.
**Validierungskriterien:** Kausalitäts-Nachweis (Bit-für-Bit-Reproduktion der Live-Features im Replay) + inkrementelles ΔR² ≥ +0.01 im Q4-Vol-Stack. Abbruch: ΔR² ≤ 0 oder Kausalitäts-Nachweis scheitert → Kanal entfällt (Critic-Auflage).
**Hardware:** CPU-only, 1-min-Batch unkritisch.
**Abhängigkeiten:** Q4 (Abnehmer).
**Zeitschätzung:** 1–2 Wochen (inkl. Kausalitätstest).
**Risiken:** Notorisches Lookahead-Problem der EMD-Literatur (Edge = 1 beim Critic); Randeffekte der Online-Zerlegung.

---

### L3 — REGIME (3 Gates + 1 Veto, konsolidiert per Critic-Auflage)

#### Q12 — Permutation Entropy als Effizienz-Fenster-Detektor [L3, Gate G1-schnell] [Quick Win]

**Herkunft:** Nichtlineare Dynamik / Informationstheorie (absorbiert Scout S10).
**Kernprinzip:** PE misst die Entropie der Ordinalmuster-Verteilung — O(n), ausreißerrobust, streamtauglich. PE ≈ 1 → Random Walk (nicht handeln); PE-Einbruch → temporärer Determinismus = Edge-Fenster. Cross-Sectional über das gesamte Perp-Universum.
**Mathematische Grundlage:** `H_PE(n) = -Sum_pi p(pi) * ln p(pi) / ln(n!)` über Ordinalmuster pi der Einbettungsdimension n (4–6); handelbar: rollierendes PE-Perzentil je Symbol + Cross-Sectional-Ranking.
**Bybit-Anwendung:** REST/WS `kline.1` (confirm-Flag), optional `tickers`-Ticks. G1-Gate: nur die ~10 % Symbole mit niedrigster PE freischalten.
**Implementierungsskizze:** Eigene Ordinalmuster-Zählung (oder `ordpy`/`antropy`) auf rollierenden 4-h-Fenstern, 1-min-Update; Fusion mit S9 zu einem Effizienz-Score (UND-Verknüpfung konservativ, alternativ Score-Mittel).
**Backtesting-Ansatz:** Konditionierungs-Test: Performance nachgelagerter Signale (z. B. K3-Follower) in Niedrig-PE- vs. Hoch-PE-Fenstern, Walk-Forward über volle Kline-Historie.
**Validierungskriterien:** Bedingte AUC nachgelagerter Richtungssignale in G1-Fenstern ≥ +0.03 gegenüber unkonditioniert UND gated Sharpe ≥ +20 % relativ. Abbruch: kein messbarer Konditionierungs-Effekt nach Walk-Forward über ≥ 2 Jahre Historie → Gate entfällt.
**Hardware:** CPU-only, trivial.
**Abhängigkeiten:** keine (sofort validierbar).
**Zeitschätzung:** 3–5 Tage.
**Risiken:** Fenster-/Dimensions-Tuning; Effekt kann über Marktzyklen wandern (G2 überwacht).

#### S9 — KL-Divergenz Entropie-Kollaps-Greenlight [L3, Gate G1-schnell] [Quick Win]

**Herkunft:** Informationstheorie.
**Kernprinzip:** Orderbuch-Volumenverteilung gegen Random-Walk-Referenz; steigt die KL-Divergenz schlagartig (Entropie kollabiert), verlässt der Markt den Zufallszustand — institutionelle Synchronisation. Komplementär zu Q12 (Buch-Querschnitt statt Preis-Zeitachse) → Doppelbestätigung aus verschiedenen Datenräumen.
**Mathematische Grundlage:** `H = -Sum p_i * log p_i`; `D_KL(P||Q) = Sum P(x) * log[P(x)/Q(x)]`, P = normierte L2-Volumenverteilung, Q = Referenzmaß; Flag via Perzentil-Schwelle (Neyman-Pearson-Logik).
**Bybit-Anwendung:** WS `orderbook.200` (100 ms), `publicTrade`.
**Implementierungsskizze:** Buch-Rekonstruktor → Level-Histogramm → H/D_KL je 100-ms-Takt, geglättet auf 1–10 s; Fusion mit Q12 (G1).
**Backtesting-Ansatz:** Auf eigener Buchaufzeichnung (Phase 0); Konditionierungs-Test wie Q12.
**Validierungskriterien:** identisch zu Q12 (bedingte AUC +0.03, gated Sharpe +20 %); zusätzlich: G1-Fusion (Q12 UND S9) muss jede Einzelkomponente schlagen. Abbruch wie Q12.
**Hardware:** CPU-only.
**Abhängigkeiten:** Phase-0-Buchaufzeichnung (Backtest), Buch-Rekonstruktor.
**Zeitschätzung:** 1 Woche.
**Risiken:** Wahl des Referenzmaßes Q; Backtest erst nach Aufzeichnungs-Vorlauf möglich.

#### Q8 — Bayesian Online Change Point Detection [L3, Gate G2-mittel] [Standard]

**Herkunft:** Bayes-Statistik (Adams/MacKay 2007).
**Kernprinzip:** Rekursive Posterior über die Run-Länge seit dem letzten Strukturbruch — online, O(1)-Update, ohne Lookahead. Kein Richtungssignal, sondern Meta-Schicht: erkennt, wann Funding-/Vol-/OI-Regime gebrochen sind → Modelle de-aktivieren und neu fitten statt weiterhandeln (adressiert Edge-Decay direkt).
**Mathematische Grundlage:** `P(r_t | x_1:t) ~ Sum_{r_t-1} P(x_t | r_t-1, x^(r)) * P(r_t | r_t-1) * P(r_t-1 | x_1:t-1)` mit Hazard `H(r) = 1/lambda`; Bruch-Flag bei `P(r_t = 0) > Schwelle`.
**Bybit-Anwendung:** Parallele Instanzen auf (1) 1-h-RV, (2) Funding-Rate-Reihe, (3) FracDiff-OI (aus Q7), (4) Basis-z-Score. REST `kline`, `funding/history`, `open-interest`, `premium-index-price-kline`.
**Implementierungsskizze:** Eigene BOCPD-Implementierung oder `bayesian_changepoint_detection`; konjugierte Normal-Gamma-Likelihoods; 1-min- bis 1-h-Takt.
**Backtesting-Ansatz:** Historische Brüche (bekannte Events: Kaskaden, Funding-Regimewechsel) als Referenz; A/B: Strategien mit/ohne G2-Abschaltung.
**Validierungskriterien:** Detektions-Verzögerung ≤ 24 h bei den 10 größten historischen Brüchen; False-Alarm-Rate < 1/Woche je Reihe; G2-gated Strategien: Max-Drawdown-Reduktion ≥ 20 % relativ bei Sharpe-Verlust ≤ 10 %. Abbruch: Gates verfehlt → fixe Re-Fit-Kadenz (wöchentlich) als Ersatz.
**Hardware:** CPU-only.
**Abhängigkeiten:** Q7 (FracDiff-Reihe), Q5/Q1 (Basis-z).
**Zeitschätzung:** 1–2 Wochen.
**Risiken:** Hazard-/Prior-Wahl; zu sensitive Schwellen erzeugen Modell-Flattern.

#### Q17 — GMM-Vol-Regime + Variance Risk Premium [L3 Gate G3-langsam + L5] [Standard, strategisch zentral]

**Herkunft:** Statistik + Optionsmärkte (Carr/Wu 2009).
**Kernprinzip:** GMM-Clustering auf RV-Feature-Vektoren (Level, Persistenz, Term-Struktur, Semivarianzen) identifiziert 4–6 diskrete Vol-Regime; die Options-Kette liefert implizite Vol als Forward-Looking-Dimension. VRP = IV² − realisierte Varianz trennt Regime schärfer als RV allein. G3 = Zustandsmaschine, die Strategie-Familien freischaltet (Carry nur Range, Kaskaden-Fade nur Stress, …).
**Mathematische Grundlage:** `p(x) = Sum_k pi_k * N(x | mu_k, Sigma_k)` via EM; Regime-Posterior `gamma_k(x_t)`; `VRP = IV^2_t - RV_{t -> t+tau}`; empirische Übergangsmatrix `T_ij = #(i->j) / #(i)`.
**Bybit-Anwendung:** REST `kline` (RV), `historical-volatility` (2 J., stündlich), Options-Kette `tickers?category=option&baseCoin=BTC` (1 Request, 1-min-Poll); eigene IV-Flächen-Aufzeichnung ab Tag 1 (keine API-Historie!).
**Implementierungsskizze:** scikit-learn GMM, stündlicher Batch-Refit nach G2-Bruchsignal; VRP-Berechnung aus ATM-markIv vs. nachfolgender RV; Regime-Output an G3-Freischaltung + L5-Sizing.
**Backtesting-Ansatz:** RV-Teil sofort auf Kline-Historie + 2 J. HV-Index; VRP-Teil nach IV-Aufzeichnungs-Vorlauf (≥ 3 Monate).
**Validierungskriterien:** Regime-Persistenz median ≥ 24 h (kein Flattern); VRP-Kanal: ΔR² ≥ +0.02 im Q4-Vol-Stack; G3-gesteuertes Sizing: Sharpe ≥ +0.2 absolut gegenüber statischem Sizing im Walk-Forward. Abbruch: VRP-Kanal ohne ΔR² → Q17 läuft RV-only; scheitert auch das, Fallback auf Q10 (NHHM, zurückgestellt).
**Hardware:** CPU-only (GMM auf Feature-Vektoren ist trivial); 82 GB RAM erlauben volle IV-Flächen im Speicher.
**Abhängigkeiten:** Phase-0-IV-Aufzeichnung, Q4 (gegenseitig).
**Zeitschätzung:** 2 Wochen.
**Risiken:** GMM-Cluster-Drift (Re-Fit nach G2); IV-Datenlücke in den ersten Monaten.

#### Q6 — VPIN / Kyle-Lambda Toxic-Flow-Veto [L3 Veto V0 (+L5)] [Quick Win (strategisch zentral)]

**Herkunft:** Marktmikrostruktur (Easley/López de Prado/O'Hara, RFS 2012).
**Kernprinzip:** VPIN schätzt in Volumen-Zeit die Wahrscheinlichkeit informierten (toxischen) Flows; hohe Toxizität geht Preissprüngen und Liquiditätsrückzug voraus (für BTC empirisch bestätigt). Bybit-Verfeinerung: exakte Taker-Side statt Bulk-Volume-Heuristik + RPI-Flag-Segmentierung (Retail- vs. Nicht-Retail-Toxizität). Unbedingtes Trade-Veto über ALLEN Modulen.
**Mathematische Grundlage:** `VPIN = Sum_{tau=1..n} |V_B(tau) - V_S(tau)| / (n * V_bucket)` über Volumen-Buckets; `Kyle-lambda: dP = lambda * Q_signed`; `Amihud = |r_t| / Vol_t`.
**Bybit-Anwendung:** WS `publicTrade` (side, size, BT/RPI-Flags); Backtest über mehrjähriges Tick-Archiv `public.bybit.com/trading/`. Veto: kein Entry, kein Maker-Quoting bei VPIN > P95; sekundär Jump-Kanal für Q4.
**Implementierungsskizze:** Volumen-Bucket-Builder (geteilter Feature-Bus-Baustein); rollierende VPIN-Perzentile je Symbol; Kyle-λ via rollierender Regression signiertes Volumen → Preisänderung.
**Backtesting-Ansatz:** Voll backtestbar auf Tick-Archiv: Event-Studie VPIN-P95-Fenster vs. nachfolgende Jumps (definiert als |r| > 4 sigma auf 5 min).
**Validierungskriterien:** Jump-Wahrscheinlichkeit in VPIN-P95-Fenstern ≥ 3× Basisrate (Odds Ratio > 3, p < 0.01); Veto im Strategie-Backtest: Max-DD-Reduktion ≥ 15 % relativ bei Bruttorendite-Verlust ≤ 5 %. Abbruch: OR < 1.5 → VPIN nur noch als Q4-Feature, Veto entfällt.
**Hardware:** CPU-only; Archiv-Verarbeitung profitiert von 82 GB RAM (mehrjährige Tickdaten chunked via DuckDB/polars).
**Abhängigkeiten:** Feature-Bus.
**Zeitschätzung:** 1–2 Wochen.
**Risiken:** Bucket-Größen-Wahl; VPIN-Kritik aus Equity-Literatur (hier durch exakte Taker-Side entschärft).

#### Q7 — OI/Preis-Divergenz mit FracDiff-Zuständen [L3 Feature-Spender] [Quick Win]

**Herkunft:** Ökonometrie / Derivate-Mechanik (López de Prado FracDiff).
**Kernprinzip:** Vorzeichen-Kombinatorik aus dPreis und dOI trennt vier Mechanik-Zustände (Long-Aufbau, Short-Aufbau, Long-Squaring, Short-Covering): Rallye bei fallendem OI = Short-Covering ohne neuen Kaufdruck → fade. Fraktionale Differenzierung macht OI-Niveaus stationär ohne Memory-Verlust.
**Mathematische Grundlage:** FracDiff `(1-B)^d X_t = Sum_k w_k * X_{t-k}`, `w_k = -w_{k-1} * (d-k+1)/k`, kleinstes d mit ADF-Stationarität (typ. 0.3–0.6); Zustands-Feature `s_t = sign(dP_t) * sign(dOI_t)` + Magnitude `|dOI|/OI`.
**Bybit-Anwendung:** REST `open-interest` (5 min+, Historie bis Launch); WS `tickers` für sub-5-min-OI (Eigenaufzeichnung); REST `kline`. Pflicht-Feature für Q2, Q9, G2-Eingangsreihen — **nie standalone**.
**Implementierungsskizze:** FracDiff-Gewichte einmalig je d; rollierender ADF-Check; Zustands-Klassifikation auf 5-min- bis 4-h-Horizonten.
**Backtesting-Ansatz:** Sofort auf voller OI-Historie; bedingte Forward-Return-Verteilungen je Zustand, FDR-korrigiert.
**Validierungskriterien:** Zustands-konditionierte Forward-Returns signifikant (p < 0.01 nach FDR); Fade-Signal Short-Covering nahe Settlement: Win-Rate ≥ 55 % und Sharpe ≥ 0.8 nach Fees auf 1–4-h-Horizont; als Feature: ΔAUC ≥ +0.02 in Q2/Q9. Abbruch: keine Signifikanz → nur deskriptives Monitoring.
**Hardware:** CPU-only.
**Abhängigkeiten:** keine (sofort validierbar).
**Zeitschätzung:** 1 Woche.
**Risiken:** OI-Daten bei Extremvolatilität verzögert (dokumentiert); Mehrfachtests über Zustände × Horizonte (FDR zwingend).

#### Q11 — Long/Short-Account-Ratio Crowding [L3 Feature-Spender] [Standard, nur Feature]

**Herkunft:** Sentiment-/Positionierungsanalyse (keine Peer-Review-Primärquelle — ehrlich deklariert).
**Kernprinzip:** Anteil long- vs. short-positionierter *Accounts* (≈ Retail-gewichtet: 1 Wal = 1 Account) in 5-min-Auflösung seit 2020-07. Crowded Longs sind Liquidations-Brennstoff — Konditionierungs-Feature für Kaskaden-/Squeeze-Setups, **niemals standalone** (Critic-Auflage).
**Mathematische Grundlage:** Crowding-z `z_t = (buyRatio_t - mu_roll) / sigma_roll`; Divergenz `d_t = z_t * sign(-r_{t,k})`; Brennstoff-Index `B_t = z_t * dOI_t` (mit Q7).
**Bybit-Anwendung:** REST `GET /v5/market/account-ratio` (verifizierter Pfad; 5 min–1 d, Historie ab 2020-07-20).
**Implementierungsskizze:** Stündlicher Poll-Job, z-Score-Berechnung im Feature-Bus; Einspeisung in Q2, Q9, Brennstoff-Index.
**Backtesting-Ansatz:** Sofort, ~6 Jahre Gratis-Historie; Ablation in Q2/Q9.
**Validierungskriterien:** ΔAUC ≥ +0.02 bzw. ΔR² ≥ +0.01 in den Abnehmermodellen. Abbruch: kein inkrementeller Beitrag → Drop (kostet fast nichts, daher niedrige Priorität, hohe Option).
**Hardware:** CPU-only, trivial.
**Abhängigkeiten:** Q2/Q9 als Abnehmer.
**Zeitschätzung:** 2–3 Tage.
**Risiken:** Schwache Evidenzbasis (Edge = 1); Indikator ist öffentlich → Crowding des Crowding-Signals möglich.

#### S1 — Ergodizitäts-Defekt als Regime-Flag [L3, Flag in K3] [Standard, nur Flag]

**Herkunft:** Statistische Mechanik (Peters/Gell-Mann).
**Kernprinzip:** Driften Time-Average und Ensemble-Average des Order-Flows über das Top-N-Perp-Ensemble auseinander, hat das System sein lokales Gleichgewicht verloren — ein gerichteter Ausbruch wird strukturell wahrscheinlicher. Kein eigenes Gate (Critic-Konsolidierung), sondern Flag INNERHALB des Lead-Lag-Moduls K3 auf dessen vorhandener Multi-Asset-L2-Infrastruktur.
**Mathematische Grundlage:** `E_d(t) = | (1/T) * Int_0^T x(s) ds - <x>_ensemble |`, operationalisiert als rollierende Differenz aus Time-Average (je Symbol, OFI/Returns) und Cross-Sectional-Average über das Ensemble.
**Bybit-Anwendung:** WS `orderbook.50` + `publicTrade` (Top-N synchron) — identische Datenbasis wie S3/S11/Q3 (Grenzkosten gering).
**Implementierungsskizze:** Auf dem K3-Feature-Strom: zwei rollierende Mittelwert-Schätzer + Defekt-Norm; Flag bei Perzentil-Überschreitung.
**Backtesting-Ansatz:** Ablation: K3-Performance mit/ohne S1-Flag-Bedingung.
**Validierungskriterien:** K3-Hit-Rate in Flag-Fenstern ≥ +5 Prozentpunkte gegenüber ohne Flag. Abbruch: kein Uplift → Drop (Edge = 1 laut Critic, bewusst als Billig-Option geführt).
**Hardware:** CPU-only.
**Abhängigkeiten:** K3-Infrastruktur (S3/S11/Q3) muss stehen.
**Zeitschätzung:** 1 Woche (auf bestehender K3-Basis).
**Risiken:** Schätzer-Rauschen bei kleinen Fenstern; konzeptionell anspruchsvoll, empirisch unerprobt.

---

### L4 — PATTERN

#### Q1 — Funding-Settlement-Zyklus & Premium-Index-Druck [L4] [Quick Win #1 — erste Methode überhaupt]

**Herkunft:** Derivate-Mechanik (absorbiert Scout S13 „Bragg-Periodizität"; FFT/PSD nur als Verifikations-Substep).
**Kernprinzip:** Der Funding-Mechanismus erzeugt eine deterministisch getimte Ereignis-Asymmetrie: Die Clamp-Funktion staut Druck („Staudamm-Effekt"), die TWAP-Gewichtung des Premium-Index macht das Verhalten um Settlements rhythmisch. Die 1-min-Premium-Index-Kline macht den Druckaufbau ZWISCHEN Settlements kontinuierlich und historisch tief sichtbar — fast kein Retail nutzt sie. Funding-Prognostizierbarkeit ist akademisch belegt (SSRN 5576424; BIS WP 1087).
**Mathematische Grundlage:** `F = P + clamp(I - P, -0.05%, +0.05%)` mit Premium-Index `P = [max(0, FairBid - Index) - max(0, Index - ImpactAsk)] / Index`; Signal: kumulierter geklemmter Überdruck `D_t = Sum_{s in Fenster} (P_s - F_implied,s)` × Zeit-bis-Settlement `tau = nextFundingTime - t` als Interaktionsterm.
**Bybit-Anwendung:** REST `premium-index-price-kline` (1 min, tiefe Historie), `funding/history`, `instruments-info` (`fundingInterval` symbolabhängig 1–8 h!); WS `tickers` (fundingRate, nextFundingTime, fundingCap). Anwendungsfälle: (1) Drift-Prognose im Fenster [T−60 min, T+30 min] konditioniert auf |F| nahe fundingCap; (2) Maker-Entry gegen extreme Funding-Seite vor Settlement, Exit nach Entladung.
**Implementierungsskizze:** Historien-Download (Pagination), D_t-Berechnung, Event-Studie um Settlements; Live: 1-min-Poll + Ticker; Execution maker-fähig via Q5-Spread-Markt.
**Backtesting-Ansatz:** Walk-Forward über die volle Premium-Index-Historie (mehrere Jahre, mehrere Symbole mit unterschiedlichen fundingIntervals); Fees: Maker 4 bp Roundtrip; Slippage-Puffer 2 bp.
**Validierungskriterien:** Out-of-sample Sharpe ≥ 1.2 nach Fees, Win-Rate ≥ 55 %, Profit-Faktor ≥ 1.3 über ≥ 200 Settlement-Trades. **Abbruchkriterium:** Walk-Forward-Sharpe < 0.5 → Methode fällt, K2 wird neu bewertet.
**Hardware:** CPU-only; Backtest auf 82 GB RAM komfortabel.
**Abhängigkeiten:** keine (einzige 3/3/3-Kern-Methode beim Critic; sofort startbar).
**Zeitschätzung:** 1–2 Wochen.
**Risiken:** Carry-/Funding-Kompression seit 2024 (dokumentiert) → G2-BOCPD auf Funding-Reihe als Abschalt-Kriterium; Crowding des Settlement-Fensters.

#### Q3 — Multi-Level Order Flow Imbalance, Cross-Asset [L4] [Standard]

**Herkunft:** Marktmikrostruktur (Cont/Kukanov/Stoikov 2014; Cont/Cucuringu/Zhang 2023).
**Kernprinzip:** OFI erklärt kurzfristige Preisänderungen linear — der robusteste replizierte Mikrostruktur-Befund. Retail-tauglich nur als aggregiertes 1–5-min-Feature (kein Race); Cross-OFI (BTC-OFI prognostiziert Altcoin-Moves) ist die dritte Messachse des K3-Lead-Lag-Graphen.
**Mathematische Grundlage:** `e_n = 1{Pb_n >= Pb_n-1} * qb_n - 1{Pb_n <= Pb_n-1} * qb_n-1 - 1{Pa_n <= Pa_n-1} * qa_n + 1{Pa_n >= Pa_n-1} * qa_n-1`; `OFI_t = Sum_n e_n`; Multi-Level: erste Hauptkomponente über `[OFI^(1) ... OFI^(10)]`; Preismodell `dP_t = beta * OFI_t + eps_t`.
**Bybit-Anwendung:** WS `orderbook.50` (20-ms-Deltas, akkumuliert auf 1–5 min), `publicTrade`; Backtest via ob500-Archiv-Snapshots + Eigenaufzeichnung.
**Implementierungsskizze:** Buch-Rekonstruktor → e_n-Strom → Minuten-Aggregat im Feature-Bus; PCA über Level; Cross-Regression BTC→Follower.
**Backtesting-Ansatz:** Rollierende Regressionen OFI→Forward-Return (5–30 min), Walk-Forward; Cross-Kanten mit FDR-Korrektur.
**Validierungskriterien:** OOS-R² ≥ 1 % der 1–5-min-Returns; bedingte Richtungs-AUC > 0.55 auf 5–30-min-Horizont in G1-Fenstern; Cross-OFI-Kanten signifikant nach FDR (q < 0.05). Abbruch: AUC-Gate verfehlt → OFI nur noch als Q4/Q9-Feature.
**Hardware:** CPU-only; 20-ms-Delta-Verarbeitung erfordert effiziente Streams (Rust-ähnliche Python-Pfade: polars, numba).
**Abhängigkeiten:** Phase-0-Buchaufzeichnung, Buch-Rekonstruktor.
**Zeitschätzung:** 2 Wochen.
**Risiken:** Archiv-Snapshots uneinheitlich (PARTIAL); Beta-Instabilität über Regime (G2-Re-Fit).

#### Q5 — Basis/Carry über den Spread-Markt [L4 / Execution-Schiene] [Standard]

**Herkunft:** Derivate (BIS WP 1087 „Crypto Carry").
**Kernprinzip:** Die Perp-Spot-Basis ist der dokumentiert profitabelste systematische Krypto-Trade (seit 2024 komprimiert — ehrlich benannt). Bybit quotiert Spreads als EIGENEN handelbaren Markt mit eigenem Orderbuch → Basis-Signale ohne Selbstrechnung und Ein-Bein-Maker-Execution (4 bp statt 11 bp, kein Leg-Risk). Primär Execution-Schiene für K2.
**Mathematische Grundlage:** Basis `b_t = (P_perp - P_index) / P_index`; annualisierter Carry `c_t = b_t * (365*24/h) + E[Sum F_i]`; Signal `z_t = (b_t - mu_b) / sigma_b`, Konvergenz-Trade bei |z| > 2.
**Bybit-Anwendung:** REST/WS `/v5/spread/*` (tickers, orderbook 25 Level, recent-trade); ergänzend `tickers` (markPrice, indexPrice) und `premium-index-price-kline` als Backtest-Proxy (Spread-Markt hat keine Historie).
**Implementierungsskizze:** Spread-Ticker-Aufzeichnung ab Phase 0; z-Score-Engine; Order-Routing-Konzept: Settlement-Fenster-Trades als Spread-Order statt zwei Beine.
**Backtesting-Ansatz:** Proxy-Backtest auf Premium-Index-Historie; Live-Validierung der Ausführungsqualität im Paper-Trading.
**Validierungskriterien:** Delta-neutraler Carry: Sharpe ≥ 1.5 nach Fees, Max-DD < 10 %; Konvergenz-Trade: Win-Rate ≥ 60 % bei |z| > 2; Execution-Test: realisierte Maker-Quote ≥ 70 % der K2-Orders. Abbruch: Spread-Markt-Liquidität unzureichend (Spread-Buch-Tiefe < Ordergröße in > 30 % der Fenster) → Fallback Zwei-Bein-Execution.
**Hardware:** CPU-only.
**Abhängigkeiten:** Q1 (Signalgeber für K2), Phase-0-Spread-Aufzeichnung.
**Zeitschätzung:** 1–2 Wochen.
**Risiken:** Keine Historie (Proxy-Risiko); Carry-Kompression; Liquidität des Spread-Buchs unbekannt bis zur Aufzeichnung.

#### S2 — Hawkes-Spektralradius rho(G) — Reflexivitäts-Kritikalität [L4] [Moonshot #1]

**Herkunft:** Seismologie / Punktprozess-Theorie (Hardiman/Bouchaud; als Erweiterung des v1-Hawkes-Moduls gekennzeichnet).
**Kernprinzip:** Orderbuch-Events (MO±, LO±, CX±) bilden ein selbsterregendes System; der Spektralradius der Branching-Matrix misst die Endogenität. rho → 1 = nahe-kritisch: ein einzelner Marktauftrag kann eine Kaskade auslösen. Kritikalitäts-Thermometer mit Vorlauf VOR der Kaskade (Kaskaden-VORHERSAGE statt -Reaktion).
**Mathematische Grundlage:** `lambda_i(t) = mu_i + Sum_j Int_0^t phi_ij(t-s) dN_j(s)`, Kernel `phi_ij(t) = alpha_ij * beta_ij * exp(-beta_ij * t)`; Branching-Matrix `G_ij = alpha_ij / beta_ij`; Signal `rho(G) = max |eig(G)|`. Risikoarmer Start: **Branching-Ratio-Approximation** (Hardiman/Bouchaud-Schätzer) statt voller MLE.
**Bybit-Anwendung:** WS `publicTrade`, `orderbook.200` oder `orderbook.1000` (Korrektur: „orderbook.500" existiert nicht), `allLiquidation`. rho-Update alle 1–10 s genügt (kein ms-Race).
**Implementierungsskizze:** Event-Klassifikator (geteilter Baustein: Trade/LO/CX aus Deltas + Taker-Side) → Eventströme → `tick`-Library (Hawkes-Schätzer) bzw. eigener Branching-Ratio-Schätzer rollierend; Eigenwert-Berechnung numpy.
**Backtesting-Ansatz:** Auf eigener Aufzeichnung (Phase 0; 3+ Monate Vorlauf nötig): Event-Studie rho-Anstieg vs. nachfolgende Kaskaden (Q2-Definition).
**Validierungskriterien:** Kaskaden-Vorhersage (Event-AUC, nicht Richtungs-AUC) > 0.65 bei Median-Lead-Time ≥ 10 min; K1-Risk-Off auf rho-Basis: Max-DD-Reduktion ≥ 20 % relativ. **Abbruchkriterium:** nach 3 Monaten Daten + 2 Schätzer-Iterationen kein Signal → S2 wird archiviert, K1 läuft mit Q2+S4 allein.
**Hardware:** Volle MLE rechenintensiv → lokal auf Workstation (CPU-parallel; 82 GB RAM hilfreich); Branching-Ratio-Approximation läuft auf VPS. GPU nicht erforderlich.
**Abhängigkeiten:** Phase-0-Aufzeichnung, Event-Klassifikator, Q2 (Kaskaden-Labels).
**Zeitschätzung:** 3–4 Wochen.
**Risiken:** Event-Klassifikation aus L2-Deltas nicht-trivial; wenige unabhängige Kaskaden-Events pro Jahr → Event-basierte CV statt Zeit-CV (Overfitting-Schutz).

#### S4 — Liquidations-Omori-Gesetz (Nachbeben-Timing) [L4 (+L5)] [Standard, K1-Kern]

**Herkunft:** Seismologie (Lillo/Mantegna PRE 2003; Weber et al. 2007).
**Kernprinzip:** Nach einem Liquidations-Crash klingt die Rate der Folge-Liquidationen wie seismische Nachbeben mit Potenzgesetz ab. Das liefert ein QUANTITATIVES Mean-Reversion-Entry-Fenster: nicht in den Crash, sondern in die verebbende Nachbebenphase einsteigen.
**Mathematische Grundlage:** Omori `n(t) = K / (t + c)^p`, p ≈ 1; Gutenberg-Richter `log10 N(>=m) = a - b*m` für die Magnitudenverteilung der Liquidationsvolumina; b-Wert-Drift = Stress-Aufbau-Indikator.
**Bybit-Anwendung:** WS `allLiquidation` (500 ms; KEINE REST-Historie → Eigenaufzeichnung oder Tardis-Zukauf ab 2020-12). Nach Initial-Spike (F0/Q2-Trigger) Live-Fit; Entry wenn Rate unter Schwelle UND Q2-Erschöpfung bestätigt.
**Implementierungsskizze:** Liquidations-Eventstore (geteilter Baustein) → Spike-Detektion → rollierender Potenzgesetz-Fit (scipy, MLE auf Wartezeiten), Update alle 10 s.
**Backtesting-Ansatz:** Auf gewachsener Eigenaufzeichnung (3+ Monate) bzw. Tardis-Historie; Event-basierte Cross-Validation über Kaskaden.
**Validierungskriterien:** Omori-Fit-Güte R² ≥ 0.8 auf ≥ 70 % der Kaskaden; Reversion-Entries: Win-Rate ≥ 58 %, Sharpe ≥ 1.0 nach Fees (Taker einkalkuliert, da Ereignis-getrieben), Zeit-Stop = Omori-Halbwertszeit. Abbruch: Fit-Güte < 0.6 im Median → nur Q2-Erschöpfung als Entry-Logik.
**Hardware:** CPU-only.
**Abhängigkeiten:** Phase-0-Liquidationsaufzeichnung, Q2 (Anatomie), F0 (Trigger).
**Zeitschätzung:** 2 Wochen.
**Risiken:** Wenige Events/Jahr; Tardis-Kosten falls Aufzeichnung zu kurz; funktioniert nur in Stress-Phasen (per Design ok).

#### S3 — Transfer-Entropy Lead-Lag-Graph [L4] [Standard, K3-Achse 1]

**Herkunft:** Informationstheorie (Schreiber PRL 2000; Krypto-TE Physica A 2022).
**Kernprinzip:** TE misst modellfrei und nichtlinear, wie viel Information von Asset Y in den zukünftigen Preis von Asset X fließt → gerichtete Führungsstruktur des Perp-Universums („BTC führt, Altcoin folgt mit Lag tau").
**Mathematische Grundlage:** `T_{Y->X} = Sum p(x_n+1, x_n^(k), y_n^(k)) * log[ p(x_n+1 | x_n^(k), y_n^(k)) / p(x_n+1 | x_n^(k)) ]`; effektive TE via Surrogat-Subtraktion gegen Bias; Returns quantil-gebinnt (Symbolisierungs-Pipeline wiederverwendet).
**Bybit-Anwendung:** WS `publicTrade`/`tickers` (Top-20-Perps, synchronisiert); historisch via Tick-Archiv sofort validierbar.
**Implementierungsskizze:** Gemeinsamer Multi-Asset-Sync-Strom (mit S11, Q3, S1); TE-Schätzung (IDTxl/pyinform oder eigene Histogramm-Schätzer) rollierend; Kanten mit Ablaufdatum.
**Backtesting-Ansatz:** Rollierender Graph auf Tick-Archiv-Historie; Follower-Strategie nur auf Kanten mit ≥ 2/3-Achsen-Konsens (S3/S11/Q3), Bonferroni/FDR auf Kantenebene.
**Validierungskriterien:** Konsens-Kanten: bedingte Richtungs-AUC > 0.55 in G1-Fenstern; K3-Strategie Sharpe ≥ 0.8 nach Fees. Abbruch: Konsens-Kanten ohne AUC-Gate über 2 Walk-Forward-Jahre → K3 entfällt.
**Hardware:** CPU-parallel (Paare × Lags); 82 GB RAM für Multi-Symbol-Historie nützlich.
**Abhängigkeiten:** Symbolisierungs-Pipeline, Multi-Asset-Sync.
**Zeitschätzung:** 2 Wochen.
**Risiken:** Multiple Testing (viele Paare × Lags) → Konsens + FDR zwingend; Leader-Struktur instabil (Altseason).

#### S11 — Cross-Asset Wavelet Coherence [L4] [Standard, K3-Achse 2]

**Herkunft:** Neurowissenschaft / EEG-Signalverarbeitung (Grinsted 2004).
**Kernprinzip:** Kohärenzanalyse misst, in welchem Frequenzband und mit welcher Phasendifferenz zwei Assets synchronisiert sind; stabile Phasenführung in einem Band zeigt, wer auf welchem Zeithorizont führt — die frequenzaufgelöste Achse des Lead-Lag-Graphen.
**Mathematische Grundlage:** `R^2(s,tau) = |S(s^-1 * W_XY)|^2 / [ S(s^-1 * |W_X|^2) * S(s^-1 * |W_Y|^2) ]`; Phasendifferenz aus `arg(W_XY)`; Morlet-CWT.
**Bybit-Anwendung:** WS `publicTrade`/`tickers` (synchronisierte Returns BTC vs. ETH/SOL/Top-Alts).
**Implementierungsskizze:** pycwt; Cone-of-Influence-Handling; Signifikanz via Surrogate; Kanten-Output (Band, Phase, Lag) in den Konsens-Graphen.
**Backtesting-Ansatz:** wie S3 (gemeinsamer K3-Backtest).
**Validierungskriterien:** wie S3 (Konsens-Gate); zusätzlich Phasen-Stabilität: Kanten nur handelbar, wenn Phasenführung ≥ 80 % des Fensters konsistent. Abbruch: wie S3.
**Hardware:** CPU-only; CWT über Top-20 parallel unkritisch.
**Abhängigkeiten:** Multi-Asset-Sync.
**Zeitschätzung:** 1–2 Wochen.
**Risiken:** Randeffekte (Cone of Influence); Mehrfachtests über Bänder.

#### S5 — TFSAX + Smith-Waterman Alignment [L4] [Standard, hartes Gate]

**Herkunft:** Bioinformatik/Genomik (als Erweiterung der v1-TFSAX-Idee gekennzeichnet).
**Kernprinzip:** Preis- und Funding-Reihen werden trend-erhaltend symbolisiert; genomische Alignment-Algorithmen finden historisch ähnliche Marktphasen trotz zeitlicher Stauchung/Dehnung. Top-Matches liefern bedingte Forward-Return-Verteilungen. Ehrliche Einordnung des Critic: Edge = 1, kein belegter Mechanismus gegen die 0.50-Baseline → härtestes Falsifizierbarkeits-Gate des Katalogs.
**Mathematische Grundlage:** PAA `C_i = (w/n) * Sum c_j`; SAX-Breakpoints via Gauß-Quantile + Trend-Symbole (TFSAX); Smith-Waterman `H(i,j) = max{0, H(i-1,j-1)+s(a_i,b_j), H(i-1,j)-d, H(i,j-1)-d}`.
**Bybit-Anwendung:** REST `kline`, `funding/history`; WS `tickers`. Alignment offline-fähig (1 min – 1 h Takt).
**Implementierungsskizze:** Symbolisierungs-Pipeline (geteilt mit S3-Binning); Alignment-Datenbank mit Indexierung (z. B. k-mer-Vorfilter wie BLAST); bedingte Verteilungen der Top-k-Matches.
**Backtesting-Ansatz:** Strikter Walk-Forward: Datenbank enthält nur Vergangenheit; bedingte Verteilungen out-of-sample evaluiert.
**Validierungskriterien (Critic-Auflage):** Bedingte OOS-AUC > 0.55 der Match-konditionierten Richtungsprognosen. **Abbruchkriterium: Gate verfehlt → ersatzloser Drop** (keine zweite Chance, schwacher Mechanismus).
**Hardware:** CPU-parallel; Alignment-DB profitiert von 82 GB RAM. GPU optional (SW ist parallelisierbar, aber nicht nötig).
**Abhängigkeiten:** Symbolisierungs-Pipeline.
**Zeitschätzung:** 2–3 Wochen.
**Risiken:** HOCH: Symbolisierungs-+Alignment-Parameter (Overfitting), Muster-Stationarität über Marktzyklen fraglich.

#### Q14 — Iceberg-/RPI-Hidden-Liquidity-Detektion [L4] [Moonshot #2]

**Herkunft:** Marktmikrostruktur (Christensen/Woodmansey 2013; Zotikov arXiv:1909.09495) + Bybit-Exklusivum.
**Kernprinzip:** Eisberge verraten sich durch sofortiges Auffüllen desselben Levels nach Teil-Executions. Bybit-Besonderheit: RPI-Orders sind im Normalbuch UNSICHTBAR, im separaten RPI-Buch SICHTBAR — die Differenz beider Bücher plus `isRPITrade`-Flags ist eine direkt beobachtbare Hidden-Liquidity-Karte ohne Inferenz. In der Literatur nirgends genutzt → First-Mover-Edge mit Verfallsdatum.
**Mathematische Grundlage:** Eisberg-Heuristik: Level i Kandidat, wenn `exec_volume(i) > k * max_displayed(i)` innerhalb dt bei Preiskonstanz; Restgrößen-Schätzer via Gamma-Verteilung über beobachtete Peak-Sizes bzw. Logit auf Replenishment-Features; RPI-Karte: `Hidden(level) = Size_rpi_book(level) - Size_normal_book(level)`.
**Bybit-Anwendung:** WS `orderbook.50` (20 ms) + `publicTrade` (Matching Executions↔Levels); WS `orderbook.rpi` (100 ms) + REST `rpi_orderbook` (50 Level, RPI- vs. Nicht-RPI-Size).
**Implementierungsskizze:** Doppelter Buch-Rekonstruktor (normal + RPI); Trade-zu-Level-Matching; Replenishment-Sequenz-Detektor; Karten-Output (S/R-Zonen) an K1–K3-Entry/Stop-Platzierung.
**Backtesting-Ansatz:** Nur auf Eigenaufzeichnung (keine Historie); Validierung indirekt über S/R-Halte-Quote und Stop-Qualität.
**Validierungskriterien:** Eisberg-/RPI-Level als S/R: Halte-Quote ≥ 65 % auf 30-min-Horizont (vs. ≤ 50 % Zufalls-Level als Kontrolle); Stop-Platzierung an Karten-Zonen: Slippage-/Stop-Out-Reduktion ≥ 10 % relativ in K1–K3. Abbruch: keine Diskriminierung gegenüber Zufalls-Levels nach 3 Monaten Daten → Archiv.
**Hardware:** CPU; 20-ms-Delta-Last ist die höchste der Pipeline (effiziente Serialisierung, ggf. nur Top-5-Symbole).
**Abhängigkeiten:** Phase-0-RPI-Aufzeichnung, Buch-Rekonstruktor, Event-Matching.
**Zeitschätzung:** 3–4 Wochen.
**Risiken:** HIGH-Komplexität Buchführung; keine Ground-Truth-Labels; Edge verfällt, sobald RPI-Analyse populär wird.

#### Q9 — Temporal Fusion Transformer mit Known-Future-Funding [L4] [Standard, gewählte DL-Erweiterung]

**Herkunft:** Deep Learning (Lim et al., IJF 2021). **Gewählt als EINZIGE lernende L4-Erweiterung** (Critic-Auflage DL-Konsolidierung; Q13 TimesNet zurückgestellt als Alternativ-Architektur).
**Kernprinzip:** TFT trennt architektonisch beobachtete Vergangenheit von BEKANNTER Zukunft — und das Funding-Settlement-Raster (nextFundingTime, tau-bis-Settlement, Funding-Vorzeichen) ist deterministisch bekannte Zukunft, die publizierte Krypto-DL-Arbeiten nicht nutzen (dokumentierte Lücke). Quantil-Output (P10/P50/P90) dient direkt den L5-Stops.
**Mathematische Grundlage:** Quantil-Loss `L = Sum_q Sum_t QL(y_t, yhat_t^(q), q)`, `QL = max(q*(y-yhat), (q-1)*(y-yhat))`; Gating `GRN(a,c) = LayerNorm(a + GLU(eta_1))`; Variable-Selection-Netze liefern Interpretierbarkeit.
**Bybit-Anwendung:** REST `kline`, `funding/history`, `open-interest`, `account-ratio`; eigene Aufzeichnungen (Liquidations-/OFI-Aggregate); known-future: tau, Funding-Vorzeichen, Wochentag/Stunde. Einsatz NUR als K2-Verstärker, erst nach Q1-Live-Proof.
**Implementierungsskizze:** pytorch-forecasting (TFT) auf 1-min-Feature-Bus; Training nachts lokal, Inferenz 1-min-Takt auf VPS-CPU; Quantile P10/P50/P90 der Drift im Settlement-Fenster.
**Backtesting-Ansatz:** Strikter Walk-Forward (rollierende Re-Trainings, purged splits); Ablation gegen Q1-Regelwerk allein.
**Validierungskriterien:** Quantil-Kalibrierung: empirische Coverage-Abweichung < 2 Prozentpunkte (P10/P90); Richtungs-AUC > 0.55 im Settlement-Fenster ODER RV-R² > 0.25 OOS; K2-Uplift: Sharpe ≥ +0.3 absolut gegenüber Q1 allein. **Abbruch: kein Uplift nach 2 Trainings-Iterationen → Q9 entfällt, Q1 bleibt regelbasiert.**
**Hardware:** **RTX 5060 Ti (16 GB VRAM) ausreichend:** TFT mit Hidden-Size 64–256, Kontext ≤ 30 Tage 1-min-Bars, Batch 64–128 → 4–10 GB VRAM. Trainingszeit Stunden/Nacht.
**Abhängigkeiten:** Q1 (live profitabel), Feature-Bus, Q7/Q11-Features.
**Zeitschätzung:** 3–4 Wochen.
**Risiken:** HOCH (DL-Overfitting, Feature-Selektion) → purged Walk-Forward, früh stoppen; Komplexitätsfalle für Solo-Entwickler (deshalb nachgelagert).

---

### L5 — RISK (Risk-Bundle, ersetzt Quantum-Modul — Begründung siehe Abschnitt 5)

#### Q2 — Liquidations-Kaskaden-Anatomie [L5 (+L4)] [Quick Win #2]

**Herkunft:** Derivate-Mechanik (absorbiert Scout S8 SIR/R0; SIR-Framing liefert das OI-als-Suszeptible-Feature).
**Kernprinzip:** Liquidationen sind preisinsensitive Zwangsflüsse. Bybit pusht ALLE Liquidationen inkl. Bankruptcy-Preis: Distanz Bankruptcy↔Mark verrät den Hebel der liquidierten Kohorte — Information, die in OHLCV nicht existiert (bester Mechanismus gegen die AUC-0.50-Baseline laut Critic). Plus Insurance-Delta (Abfluss = Fill schlechter als Bankruptcy = echte Illiquidität) und ADL-`pr` → plattformweiter Stress-Score.
**Mathematische Grundlage:** Implizierter Hebel `L_hat ≈ 1 / |1 - p_bankruptcy / p_mark|`; Kaskaden-Intensität `lambda(t) = mu + Sum_{t_i<t} alpha * exp(-beta*(t-t_i)) * v_i` (Hawkes-artig, als v1-Erweiterung gekennzeichnet); Slippage-Proxy `dInsurance_t / Sum v_i`; Erschöpfung: `lambda(t) < mu`.
**Bybit-Anwendung:** WS `allLiquidation` (500 ms), `insurance.USDT` (1 s), `adlAlert.{coin}` (1 s) + REST `adl-alert`, `open-interest`. Output: (a) Risk-Off-Ampel für ALLE Strategien, (b) Erschöpfungs-Signal als K1-Entry-Bedingung, (c) Intensitäts-Kanal für Q4.
**Implementierungsskizze:** Liquidations-Eventstore + Insurance-/ADL-Logger (Phase 0); Live-Score ab Tag 1 (sofort nützlich, auch ohne Backtest); Intensitäts-Fit exponentiell gleitend.
**Backtesting-Ansatz:** Volle Backtests erst nach Aufzeichnungs-Vorlauf (oder Tardis-Zukauf ab 2020-12); Event-basierte CV über Kaskaden.
**Validierungskriterien:** Kaskaden-Erkennung (Score > Schwelle vor/zu Beginn): Recall ≥ 90 % der Top-Events; Risk-Off-Anwendung: Max-DD-Reduktion ≥ 25 % relativ im Portfolio-Backtest; Erschöpfungs-Entry (mit S4): Win-Rate ≥ 58 %. Abbruch: Recall < 70 % nach Kalibrierung → nur F0-artige Grobampel.
**Hardware:** CPU-only.
**Abhängigkeiten:** Phase-0-Aufzeichnung (Liquidationen/Insurance/ADL), Q7/Q11 (Brennstoff-Features).
**Zeitschätzung:** 2–3 Wochen (Live-Score: 1 Woche).
**Risiken:** Dreifache Historie-Lücke (Daten = 2 beim Critic); wenige Events/Jahr; Schwellen-Disziplin.

#### Q4 — PatchTST Realized-Volatility-Prognose [L5, Vol-Stack-Kern] [Quick Win (strategisch zentral)]

**Herkunft:** Deep Learning (Nie et al., ICLR 2023).
**Kernprinzip:** Die einzige empirisch belegte Prognostizierbarkeit der Baseline ist Volatilität (R² ≈ 0.25). PatchTST (Patching + Channel-Independence) ist auf Long-Horizon-Benchmarks konsistent top. Ziel: RV-R² über 0.25 heben durch lange Kontextfenster + Mikrostruktur-Kanäle (OFI, Liquidations-Intensität, Funding, Δh, IMF-Energien, VRP). Kein Richtungs-Claim. Output versorgt ALLE Strategien (Vol-Targeting, Stops).
**Mathematische Grundlage:** Patching `x_p in R^{P x N}`, `N = floor((L-P)/S) + 1` → Attention O(L²) → O((L/S)²); Ziel `RV_{t+h} = Sum r_i^2` aus 1-min-Returns, Horizonte 1 h / 8 h / 24 h.
**Bybit-Anwendung:** REST `kline` (1 min, bis Launch), `open-interest`, `funding/history`; Kanäle aus Eigenaufzeichnung (Liquidationen, OFI, VPIN).
**Implementierungsskizze:** neuralforecast/HuggingFace-PatchTST; Benchmark: HAR-RV (Ehrlichkeits-Referenz); Training lokal (Nacht-Batch), Inferenz 1-min-Takt VPS-CPU; kanal-weise Ablation.
**Backtesting-Ansatz:** Walk-Forward mit rollierendem Re-Training (purged splits); Metriken R², QLIKE.
**Validierungskriterien (Gate des gesamten Vol-Stacks):** OOS-R² > 0.25 (Kestrel-Baseline) im Walk-Forward UND QLIKE ≥ 5 % besser als HAR-RV; jeder Zusatzkanal nur bei inkrementellem ΔR² > 0 (Ablation). **Abbruch: PatchTST schlägt HAR-RV nicht → HAR-RV wird produktiv gesetzt (das Gate gilt dem Modell, nicht dem Ziel).**
**Hardware:** **RTX 5060 Ti (16 GB VRAM) ausreichend:** PatchTST 1–10 M Parameter, Kontext 7–30 Tage 1-min, Batch 128 → 3–8 GB VRAM; Training < 1 Nacht. 82 GB RAM für Datenpipeline komfortabel.
**Abhängigkeiten:** Feature-Bus; Kanäle aus Q15/Q16/Q17/Q2.
**Zeitschätzung:** 2–3 Wochen.
**Risiken:** HOCH (DL + viele Kanäle) → hartes R²-Gate + Ablations-Pflicht; Regime-Robustheit der RV-Prognose ist immerhin belegt (geringste Regime-Abhängigkeit aller Gruppen).

#### Q15 — MF-DFA / Hölder-Regularität als Tail-Feature [L5 (+L3)] [Standard]

**Herkunft:** Econophysics (Kantelhardt 2002; BTC-Rough-Vol arXiv:2507.00575).
**Kernprinzip:** BTC ist robust multifraktal; die Spektrumsbreite Δh und der lokale Hölder-Exponent α(t) messen, ob der Markt mono- (effizient) oder multifraktal (heterogen, fat tails, Herding) operiert — prädiktive Features für RV-Persistenz und Tail-Risiko; Übergang mono→multifraktal = Stress-Frühwarnung (komplementär zu BOCPD).
**Mathematische Grundlage:** `F_q(s) = { (1/N_s) * Sum_v [F^2(v,s)]^{q/2} }^{1/q} ~ s^{h(q)}`; `Delta_h = h(q_min) - h(q_max)`; Singularitätsspektrum `f(alpha) = q*alpha - tau(q)`, `alpha = d tau / dq`; lokaler Hölder via Wavelet-Leaders.
**Bybit-Anwendung:** REST `kline` (1 min); Tick-Archiv für feinere Schätzung. Rollierende 1–7-Tage-Fenster, 1-min-Update.
**Implementierungsskizze:** MFDFA-Bibliothek (PyPI `MFDFA`) bzw. eigene Implementierung; Features (Δh, α(t)) in Feature-Bus → Q4-Kanal + Tail-Score für Sizing.
**Backtesting-Ansatz:** Sofort auf Kline-Historie; Ablation im Vol-Stack; Event-Studie α(t)-Abfall vor RV-Spikes.
**Validierungskriterien:** ΔR² ≥ +0.02 im Q4-Vol-Stack; Tail-Frühwarnung: AUC > 0.60 für „RV-Spike in nächsten 24 h" (Spike = RV > P95). Abbruch: beide Gates verfehlt → Drop.
**Hardware:** CPU-only.
**Abhängigkeiten:** Q4 (Abnehmer).
**Zeitschätzung:** 1 Woche.
**Risiken:** Schätzfenster-Sensitivität; Multifraktalität teils Stichproben-Artefakt (Literatur-Warnung) → strenge OOS-Disziplin.

*(Q17 ist oben unter L3/G3 vollständig dokumentiert und gehört gleichzeitig zum L5-Risk-Bundle.)*

---

## 5. REFERENZ-ARCHITEKTUR

### 5.1 Abweichung von der ursprünglichen Referenz-Pipeline (dokumentationspflichtig)

Die CLAUDE.md-Referenz-Pipeline sah als L5 ein **Quantum Risk Module** (Schrödinger-Gleichung, Funding-Clamp als Potenzialbarriere) vor. **Diese Komponente wird ersetzt.** Critic-Befund (critic_report_1.md, Lücke 3): Der einzige Quanten-Kandidat S6 (Bohmsche Pilotwelle) erhielt **Edge = 0** — „Analogie ohne kausalen Mechanismus"; sein operativer Kern (Orderbuch-Dichtekrümmung, Sentiment-Drift) ist durch S9/Q3/Q11 bereits abgedeckt. Der RISK-Layer ist durch das Bundle **Q2 (Kaskaden-Risk-Off) × Q4 (RV-Sizing) × Q15 (Tail-Score) × Q17 (Regime-Sizing/VRP)** mechanistisch sauberer und empirisch fundierter besetzt (RV-Prognose ist das einzige belegte Signal der Baseline). Weitere Critic-getriebene Anpassungen: **F0-Fallback-Trigger** in L1 (Mitigation Single-Point-of-Failure S7), **L3 konsolidiert** auf 3 Gates + VPIN-Veto (statt 9 Parallel-Methoden), Endpoint-Korrektur `orderbook.500` → `orderbook.200`/`orderbook.1000`.

### 5.2 ASCII-Pipeline (final)

```
[BYBIT-DATENQUELLEN]
 WS: tickers(100ms) · allLiquidation(500ms) · orderbook.50(20ms) · orderbook.200(100ms)
     publicTrade(rt) · orderbook.rpi(100ms) · insurance.USDT(1s) · adlAlert(1s) · spread.*
 REST-Poll: premium-index-kline(1min) · kline · open-interest · funding/history
            account-ratio · options-tickers(IV, 1min) · historical-volatility
        │
        ▼
[PHASE-0-RECORDING + FEATURE-BUS]  (24/7-Collector, Docker/VPS, Parquet+Tagesrotation,
  Auto-Reconnect, seq-Lücken-Detektion · geteilte Bausteine: Buch-Rekonstruktor,
  Event-Klassifikator, Liquidations-Eventstore, 1-min-Feature-Bus, Symbolisierung)
        │
        ▼
┌─ L1: INGESTION (Event-Gate, immer aktiv) ─────────────────────────────────┐
│  F0 Fallback-Trigger (Pflicht, Tag 1): 4 Perzentil-Regeln (Liq>P99,       │
│    |dOI|>P99, |dPremium|>P98, RV/Spread>P98) — deterministisch, ≤1s       │
│  S7 SpikeWavformer (Moonshot, später): LIF-SNN + Symlet-DWT,              │
│    dauerhaft gegen F0-Schatten gebenchmarkt                                │
│  Libraries: snnTorch/Norse, PyWavelets, polars                             │
└──────┬─────────────────────────────────────────────────────────────────────┘
       │ Trigger
       ▼
┌─ L2: DENOISING (nach L1-Spike) ───────────────────────────────────────────┐
│  S12 Symlet-DWT auf Level-Zeitreihen → Spoof-/Iceberg-Signaturen          │
│  Q16 kausales CEEMDAN auf RV/Premium-Reihen → IMF-Energie-Features        │
│  Libraries: PyWavelets, PyEMD (streng kausal)                              │
└──────┬─────────────────────────────────────────────────────────────────────┘
       │            (parallel zu L2)
       ▼
┌─ L3: REGIME — 3 Gates + 1 Veto (konsolidiert) ────────────────────────────┐
│  G1 schnell (100ms–1min): Q12 Permutation Entropy × S9 KL-Kollaps         │
│     → fusionierter Effizienz-Score: "Ist JETZT ein Edge-Fenster?"          │
│  G2 mittel (1min–1h): Q8 BOCPD auf RV/Funding/FracDiff-OI/Basis-z         │
│     → Regime-Bruch ⇒ De-Aktivierung + Re-Fit                               │
│  G3 langsam (1h): Q17 GMM-Vol-Regime + VRP → Strategie-Freischaltung      │
│  V0 VETO (unbedingt, über allem): Q6 VPIN > P95 ⇒ kein Entry/Quoting      │
│  Feature-Spender: Q7 FracDiff-OI-Zustände · Q11 Crowding-z (nie alleine)  │
│  Libraries: ordpy/antropy, eigene BOCPD, scikit-learn (GMM), numpy        │
└──────┬─────────────────────────────────────────────────────────────────────┘
       │ Greenlight (G1 ∧ G2 ∧ G3-Freischaltung ∧ ¬V0)
       ▼
┌─ L4: PATTERN (vier Module, parallel) ─────────────────────────────────────┐
│  KASKADEN-MODUL: S2 Hawkes-rho(G) (Vorlauf) → S4 Omori (Entry-Timing)     │
│  FUNDING-MODUL:  Q1 Clamp-Stau D_t × tau  + Q9 TFT-Quantile (Verstärker)  │
│  LEAD-LAG-MODUL: S3 Transfer Entropy × S11 Wavelet Coherence × Q3 Cross-  │
│     OFI → EIN Konsens-Graph (Kante nur bei ≥2/3 Achsen) + S1-Flag         │
│  HIDDEN-LIQUIDITY: Q14 RPI-Buch-Differenz + Replenishment × S12-Signale   │
│     → Liquiditätskarte (S/R-Zonen) als Service für alle Module            │
│  Pattern-Suche: S5 TFSAX+Smith-Waterman (hartes AUC-Gate)                 │
│  Libraries: tick (Hawkes), scipy, IDTxl/pyinform, pycwt,                  │
│             pytorch-forecasting (TFT)                                      │
└──────┬─────────────────────────────────────────────────────────────────────┘
       │ Signal-Kandidaten
       ▼
┌─ L5: RISK-BUNDLE (ersetzt Quantum-Modul; Critic-Begründung s. 5.1) ───────┐
│  Q4 PatchTST-RV (Kern, Gate OOS-R²>0.25) ← Kanäle: Q15 (Δh, alpha(t)),    │
│     Q16 (IMF-Energien), Q17 (IV/VRP), Q2 (Liquidations-Intensität)        │
│  Q2 Kaskaden-Risk-Off-Ampel (plattformweiter Stress-Score)                │
│  Q17 G3-Regime-Sizing + VRP-Dimmer (VRP negativ ⇒ Exposure runter)        │
│  Output: Multi-Horizont-RV (1h/8h/24h) → Vol-Targeting, Stop-Distanzen,   │
│     Position-Size; Q9-P10/P90-Quantile → Stop-/Target-Level               │
│  Libraries: neuralforecast/HF-PatchTST, MFDFA, scikit-learn               │
└──────┬─────────────────────────────────────────────────────────────────────┘
       ▼
[EXECUTION DECISION]
  Long / Short / Wait + Size (Vol-Targeting) + Stop (Q9-Quantile, Q14-Zonen)
  Settlement-Trades maker-fähig via Q5 SPREAD-MARKT (4bp statt 11bp, 1 Bein)
```

### 5.3 Layer-Beschreibungen

- **L1 INGESTION** — immer aktiv; reduziert die Datenflut auf Events. F0 ist in Stunden gebaut und deterministisch testbar; S7 ist die lernende Erweiterung mit Schatten-Benchmark. *Libraries: polars, snnTorch/Norse, PyWavelets.*
- **L2 DENOISING** — wird nach L1-Spike aktiv. Trennung von MM-Rauschen und struktureller Bewegung über Symlet-DWT (Buch-Level) und kausales CEEMDAN (Reihen). *Libraries: PyWavelets, PyEMD.*
- **L3 REGIME** — parallel zu L2. Hierarchisierter Gate-Stack statt 9 Parallel-Detektoren: G1 beantwortet „jetzt?", G2 „ist das Modell noch gültig?", G3 „welche Strategie-Familie?", V0 vetot toxischen Flow unbedingt. *Libraries: ordpy/antropy, scikit-learn, eigene BOCPD.*
- **L4 PATTERN** — vier parallele Module (Kaskade, Funding, Lead-Lag, Hidden Liquidity) + Pattern-Suche; nur aktiv bei Greenlight. *Libraries: tick, scipy, IDTxl/pyinform, pycwt, pytorch-forecasting.*
- **L5 RISK** — Risk-Bundle statt Quantum-Modul; bestimmt Größe, Stop und Freischaltung jeder Order; RV-Prognose als einziges empirisch belegtes Signal ist hier das Fundament. *Libraries: neuralforecast/HuggingFace, MFDFA, scikit-learn.*

**Deployment:** VPS (Docker/Ubuntu): Collector, Feature-Bus, Gates, Inferenz (CPU). Lokale Workstation (RTX 5060 Ti, 82 GB RAM): Training (Q4/Q9/S7), Backtests, Archiv-Verarbeitung. Transport: Parquet-Sync VPS→lokal (Tagesrotation), Modell-Artefakte lokal→VPS.

---

## 6. PRIORISIERUNGSMATRIX

Alle 26 validierten Methoden. Priorität = (Edge × Novelty) / Komplexität (LOW = 1, MED = 2, HIGH = 3); Scores aus der Critic-Bewertungstabelle (0–3-Skala). F0 ist als Pflicht-Infrastruktur ohne Score geführt.

| # | Methode | Layer | Daten | Edge | Retail | Novelty | Critic-Total | Komplexität | Priorität | Kategorie | Phase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| — | F0 Fallback-Trigger | L1 | 3 | — | 3 | — | Pflicht | LOW | ∞ (Pflicht) | Infrastruktur | 0 |
| 1 | Q1 Funding-Zyklus/Premium-Druck | L4 | 3 | 3 | 3 | 2 | 11 | LOW | **6.0** | Quick Win | 1 |
| 2 | Q2 Kaskaden-Anatomie | L5(+L4) | 2 | 3 | 2 | 3 | 10 | MED | **4.5** | Quick Win | 2 |
| 3 | Q7 OI/Preis-Divergenz + FracDiff | L3 | 3 | 2 | 3 | 2 | 10 | LOW | **4.0** | Quick Win (Feature) | 1 |
| 3 | Q12 Permutation Entropy | L3/G1 | 3 | 2 | 3 | 2 | 10 | LOW | **4.0** | Quick Win | 1 |
| 3 | S9 KL-Entropie-Kollaps | L3/G1 | 2 | 2 | 3 | 2 | 9 | LOW | **4.0** | Quick Win | 1 |
| 6 | Q6 VPIN/Kyle-λ (Veto V0) | L3(+L5) | 3 | 3 | 3 | 2 | 11 | MED | 3.0 | Standard (zentral) | 1 |
| 6 | Q4 PatchTST-RV | L5 | 3 | 3 | 2 | 2 | 10 | MED | 3.0 | Standard (zentral) | 2 |
| 6 | Q17 GMM-Vol-Regime + VRP | L3/G3+L5 | 2 | 3 | 3 | 2 | 10 | MED | 3.0 | Standard | 2 |
| 6 | Q3 Multi-Level-OFI | L4 | 2 | 3 | 2 | 2 | 9 | MED | 3.0 | Standard | 3 |
| 6 | Q5 Basis/Spread-Markt | L4/Exec | 2 | 3 | 2 | 2 | 9 | MED | 3.0 | Standard | 3 |
| 6 | S2 Hawkes-Spektralradius | L4 | 2 | 3 | 2 | 3 | 10 | HIGH | 3.0 | **Moonshot** | 4 |
| 6 | S4 Omori-Timing | L4(+L5) | 2 | 2 | 3 | 3 | 10 | MED | 3.0 | Standard | 3 |
| 13 | Q8 BOCPD (G2) | L3/G2 | 3 | 2 | 3 | 2 | 10 | MED | 2.0 | Standard | 2 |
| 13 | S3 Transfer Entropy | L4 | 3 | 2 | 2 | 2 | 9 | MED | 2.0 | Standard | 3 |
| 13 | S11 Wavelet Coherence | L4 | 3 | 2 | 2 | 2 | 9 | MED | 2.0 | Standard | 3 |
| 13 | Q15 MF-DFA / Hölder | L5(+L3) | 3 | 2 | 2 | 2 | 9 | MED | 2.0 | Standard | 2 |
| 13 | S12 Symlet-Spoof-Detektor | L2(+L4) | 2 | 2 | 2 | 2 | 8 | MED | 2.0 | Standard | 4 |
| 13 | S7 SpikeWavformer | L1 | 2 | 2 | 2 | 3 | 9 | HIGH | 2.0 | **Moonshot** | 4 |
| 13 | Q14 Iceberg/RPI | L4 | 2 | 2 | 2 | 3 | 9 | HIGH | 2.0 | **Moonshot** | 4 |
| 13 | Q10 NHHM | L3 | 3 | 2 | 2 | 2 | 9 | MED | 2.0 | **ZURÜCKGESTELLT** (redundant zu Q17/G3; Fallback bei IV-Datenlücke) | — |
| 21 | S5 TFSAX + Smith-Waterman | L4 | 3 | 1 | 2 | 3 | 9 | MED | 1.5 | Standard (hartes Gate: OOS-AUC > 0.55 sonst Drop) | 4 |
| 22 | Q9 TFT Known-Future-Funding | L4 | 3 | 2 | 1 | 2 | 8 | HIGH | 1.33 | Standard (einzige DL-Erweiterung; nur als K2-Verstärker) | 4 |
| 22 | Q13 TimesNet | L4 | 3 | 2 | 1 | 2 | 8 | HIGH | 1.33 | **ZURÜCKGESTELLT** (DL-Redundanz; Alternative zu Q9) | — |
| 24 | S1 Ergodizitäts-Defekt | L3 (K3-Flag) | 2 | 1 | 2 | 3 | 8 | HIGH | 1.0 | Standard (nur Flag auf K3-Infrastruktur) | 3 |
| 24 | Q11 L/S-Crowding | L3 | 3 | 1 | 3 | 1 | 8 | LOW | 1.0 | Standard (nur Feature, nie standalone) | 1 |
| 24 | Q16 CEEMDAN kausal | L2 | 3 | 1 | 1 | 2 | 7 | MED | 1.0 | Standard (nur mit Kausalitäts-Nachweis) | 4 (opt.) |

**Verworfen (nicht in der aktiven Pipeline; Details Abschnitt 9.6):** S6 Bohmsche Pilotwelle (Edge = 0), S14 Compressed Sensing (Edge = 0, Robust-PCA-Restidee optional in K5). **Merged:** S8→S2/Q2, S10→Q12, S13→Q1.

---

## 7. KOMBINATIONSSTRATEGIEN

Fünf Mini-Strategie-Konzepte aus der Synthese; K1–K3 sind die Pflicht-Kombinationen, K4/K5 sind Service-Module.

### K1 — „Seismograph": Kaskaden-Lebenszyklus-Trader

- **Methoden:** S2 (rho-Vorlauf) + Q2 (Anatomie) + S4 (Omori-Timing); Features Q7/Q11 (Brennstoff-Index); Veto Q6; Sizing Q4.
- **Logik:** Drei Phasen DESSELBEN selbsterregenden Prozesses: rho(G) → 1 UND Brennstoff-Index hoch ⇒ Risk-Off/Short-Bias-Bereitschaft (VOR dem Beben). Kaskade läuft (Q2: lambda > Schwelle, Insurance-Abfluss, ADL-pr steigt) ⇒ KEIN Entry (kein Messer-Fangen). Nachbebenphase ⇒ quantitativ getimter Reversion-Entry.
- **Entry-Bedingung:** Omori-Rate `n(t) < Schwelle` UND `lambda(t) < mu` (Q2-Erschöpfung) UND `VPIN < P95` UND G3-Regime = Stress (Strategie freigeschaltet).
- **Exit-Bedingung:** Zeit-Stop = Omori-Halbwertszeit ODER Reversion-Ziel aus Q4-RV-Band erreicht; Hard-Stop via Q9-P10/P90 bzw. Q14-Zonen.
- **Edge-Quelle:** Preisinsensitiver Zwangsfluss + quantitatives Nachbeben-Timing — Information, die in OHLCV nicht existiert.
- **Validierungs-Gate:** Win-Rate ≥ 58 %, Sharpe ≥ 1.0 nach Fees über ≥ 30 Kaskaden-Events (Event-CV).

### K2 — „Funding-Uhr": Settlement-Fenster-Harvester

- **Methoden:** Q1 (Signal) + Q9 (TFT-Verstärker, optional/nachgelagert) + Q5 (Spread-Execution); Gate Q8/G2; Veto Q6.
- **Logik:** Kumulierter Clamp-Überdruck D_t und tau-bis-Settlement aus Q1; Q9 liefert P10/P50/P90-Quantile der Drift im Fenster [T−60, T+30] min; Execution maker-fähig über den Spread-Markt — delta-neutral oder direktional.
- **Entry-Bedingung:** `|D_t| > P90` (historisch) UND Q9-P50 gleichgerichtet (sofern Q9 aktiv; sonst Q1-Regelwerk allein) UND G2 = kein Funding-Regime-Bruch UND `VPIN < P95`.
- **Exit-Bedingung:** Nach Settlement-Entladung (Drift-Umkehr) ODER Quantil-Stop (Q9-P10/P90); spätestens T+30 min.
- **Edge-Quelle:** Deterministisch getimte Ereignis-Asymmetrie + 1-min-Premium-Index-Sensor (von Retail praktisch ungenutzt) + Fee-Strukturvorteil (Maker 4 bp via Spread-Markt — die Fee-Hürde wird Edge-Bestandteil).
- **Validierungs-Gate:** Sharpe ≥ 1.2 nach Fees, Win-Rate ≥ 55 %, ≥ 200 Settlement-Trades walk-forward (siehe Q1).

### K3 — „Rudel-Läufer": Lead-Lag-Follower-Rotation

- **Methoden:** S3 + S11 + Q3 (drei orthogonale Messachsen → EIN Konsens-Graph) + S1-Flag; Gate G1 (Q12/S9); Veto Q6.
- **Logik:** Konsolidierter Leader-Follower-Graph über Top-20-Perps; eine Kante gilt nur als handelbar bei ≥ 2/3-Achsen-Konsens (drastische False-Positive-Reduktion, Multiple-Testing-Schutz). Leader (meist BTC) bewegt sich signifikant ⇒ Follower-Entry vor dem Nachziehen — nur in G1-Greenlight-Fenstern (niedrige PE des Followers) und bei gesetztem S1-Flag (Ensemble verlässt Gleichgewicht).
- **Entry-Bedingung:** Leader-Move > Schwelle UND Kanten-Lag tau noch nicht verstrichen UND G1 grün UND S1-Flag gesetzt UND `VPIN < P95`.
- **Exit-Bedingung:** Lag-Fenster abgelaufen ODER Kohärenz-/TE-Kante bricht weg (rollierende Re-Schätzung); Stop via Q4-Vol-Band.
- **Edge-Quelle:** Cross-Impact-Information (Q3) + nichtlineare Informationsflüsse (S3) + Phasenführung (S11), regime-konditioniert — konsistent zur Baseline: bedingte AUC > 0.55 als Gate.
- **Validierungs-Gate:** Bedingte AUC > 0.55 auf Konsens-Kanten, Sharpe ≥ 0.8 nach Fees, FDR-korrigiert.

### K4 — „Vol-Cockpit": Meta-Strategie Risiko & Sizing (Service-Modul)

- **Methoden:** Q4 + Q15 + Q16 + Q17 + Q2-Intensität (= L5-Risk-Bundle).
- **Logik:** Keine eigene Direktionalität. Multi-Horizont-RV (1 h/8 h/24 h) speist Vol-Targeting, Stops und G3-Freischaltung; VRP-Vorzeichen als Risiko-Dimmer (negativ ⇒ Markt unterschätzt kommende Vol ⇒ Exposure runter).
- **Gate:** OOS-R² > 0.25 im Walk-Forward; jeder Input-Kanal mit Ablations-ΔR² > 0, sonst raus.
- **Edge-Quelle:** Das einzige empirisch belegte Signal der Baseline, ausgebaut mit Bybit-exklusiven Kanälen.

### K5 — „Schatten-Kartograph": Hidden-Liquidity-Zonen (Service-Modul)

- **Methoden:** Q14 + S12 (optional später: Robust-PCA-Reformulierung der S14-Restidee).
- **Logik:** Kontinuierliche Karte echter (Iceberg/RPI) vs. künstlicher (Spoof) Liquidität; kein Standalone-Trader, sondern S/R-Zonen-Lieferant für Entry-/Stop-Platzierung von K1–K3.
- **Edge-Quelle:** Bybit-exklusive RPI-Buch-Differenz — direkt beobachtbare Hidden Liquidity, in der Literatur ungenutzt; First-Mover-Datensatz ab Aufzeichnungsbeginn.

---

## 8. IMPLEMENTIERUNGS-ROADMAP

Leitprinzip (Synthese): **Erst aufzeichnen (vergangene Daten sind unwiederbringlich), dann billige sofort validierbare Bausteine, dann Module, dann Moonshots.** Alle Wochenangaben für eine Einzelperson mit Python-Grundkenntnissen kalibriert; jede Phase endet mit Git-Commit + dokumentiertem Gate-Ergebnis.

### Phase 0 — Recording & Foundation (Woche 1–2)

- 24/7-Collector-Dienst (Docker auf VPS): WS-Multiplexer mit Auto-Reconnect, Sequenz-Lücken-Detektion, Parquet + Tagesrotation. Aufzeichnung ab Tag 1: `allLiquidation` (alle Symbole), `insurance` + `adlAlert`, `orderbook.200`-Deltas (Top-Symbole), `orderbook.50` + `publicTrade`, `orderbook.rpi`, Options-Kette/IV (1-min-Poll), `tickers` 100 ms (inkl. sub-5-min-OI), Spread-Markt-Ticker. Speicherbudget ~30–70 GB/Monat.
- **F0-Fallback-Trigger** (in Stunden gebaut) + Feature-Bus-Grundgerüst (1-min-Bars: OFI-Aggregat, VPIN-Buckets, PE, RV, Premium-Index, FracDiff-OI, Crowding-z).
- Historien-Downloads: Kline/Premium-Index/Funding/OI/account-ratio voll paginieren; Tick-Archiv selektiv.
- **Gate Phase 0:** Collector läuft ≥ 7 Tage ohne unbemerkte seq-Lücken; F0-Replay reproduzierbar.

### Phase 1 — Quick Wins & Gate-Gerüst (Woche 3–6)

- **Q1** Backtest auf voller Premium-Index-Historie (erste Methode überhaupt: höchste Priorität 6.0, LOW-Komplexität, 3/3/3-Kern, maker-fähig — schnellster ehrlicher Walk-Forward-Test der Gesamtthese).
- **Q12 + S9** → Gate G1; **Q7 + Q11** → Feature-Spender; **Q6** VPIN-Veto (Backtest auf Tick-Archiv).
- **Gate Phase 1:** Q1-Gates (Sharpe ≥ 1.2 / WR ≥ 55 % / PF ≥ 1.3) entschieden; Q6-Odds-Ratio > 3; G1-Konditionierungseffekt gemessen.

### Phase 2 — Risk-Fundament (Woche 7–12)

- **Q4** Vol-Stack-Kern (PatchTST, Training auf RTX 5060 Ti; Gate OOS-R² > 0.25 + QLIKE vs. HAR-RV) + **Q15** als erster Zusatzkanal.
- **Q8** (G2-BOCPD) + **Q17** (G3; IV-Aufzeichnung läuft seit Phase 0; VRP-Kanal nach ≥ 3 Monaten IV-Daten).
- **Q2-Live-Score** (Risk-Off-Ampel aus laufender Aufzeichnung — schützt ab sofort).
- **Gate Phase 2:** K4-Vol-Cockpit produktiv (Q4 oder HAR-RV-Fallback); Risk-Off-Ampel live.

### Phase 3 — Mini-Strategien (Woche 13–20)

- **K1 Seismograph:** S4-Omori auf gewachsener Liquidations-Historie (jetzt 3+ Monate) + Q2-Anatomie.
- **K2 Funding-Uhr:** Q1 live + **Q5**-Spread-Execution (Maker-Quote-Test).
- **K3 Lead-Lag:** S3 + S11 + Q3-Konsens-Graph + S1-Flag.
- Beginn **Paper-Trading auf Bybit Testnet/Demo** für jede Strategie, die ihre Backtest-Gates besteht.
- **Gate Phase 3:** ≥ 1 Strategie besteht Backtest-Gates und läuft im Paper-Trading.

### Phase 4 — Moonshots & Live-Gate (ab Woche 21)

- **S2** Hawkes-rho (erst Branching-Ratio-Approximation, dann volle MLE) · **Q14 + S12** (K5-Karte) · **S7** SNN gegen F0-Schatten · **Q9** TFT als K2-Verstärker (NUR falls Q1 live profitabel) · **S5** mit hartem AUC-Gate · optional **Q16** nach Kausalitäts-Nachweis. Jeder Moonshot mit definiertem Abbruchkriterium (siehe Katalog).
- **Live-Testing-Gate (Paper → Real, kleines Kapital):** über ≥ 3 Monate Paper-Trading: **Sharpe ≥ 1.5 nach Fees, Max Drawdown < 15 %, Win-Rate > 52 %**, plus Übereinstimmung Paper vs. Backtest (Slippage-Abweichung < 30 %). Erst danach reales Kapital, beginnend mit minimaler Size.

**Dauerprinzipien:** Walk-Forward ist Pflicht-Validierung für ALLES (keine In-Sample-Claims); Schwellen/Perzentile nur aus Trainingsfenstern; jede verworfene Methode wird mit Begründung in `results/` dokumentiert (negative Ergebnisse sind Wissen).

---

## 9. RISIKEN & EINSCHRÄNKUNGEN

### 9.1 Overfitting (Hauptrisiko, methodengruppenweise)

| Gruppe | Risiko | Pflicht-Gegenmaßnahme |
|---|---|---|
| Kaskaden (S2, S4, Q2) | NIEDRIG–MITTEL: wenige Parameter, aber wenige unabhängige Events/Jahr | Event-basierte CV statt Zeit-CV; Schwellen-Perzentile nur aus Trainingsfenster |
| Funding (Q1, Q5, Q9) | Q1 NIEDRIG (regelbasiert); Q9 HOCH (DL) | Q9 erst nach Q1-Live-Proof; purged Walk-Forward |
| Lead-Lag (S3, S11, Q3, S1) | MITTEL–HOCH: Paare × Lags × Bänder = Multiple Testing | ≥ 2/3-Achsen-Konsens + Bonferroni/FDR auf Kantenebene; Kanten mit Ablaufdatum |
| Regime-Gates (Q12, S9, Q8, Q17, Q6) | NIEDRIG: wenige Parameter; Schwellen-Tuning | Schwellen nie global kalibrieren; G3-Re-Fit nur nach G2-Bruch |
| Vol-Stack (Q4, Q15, Q16, Q17) | HOCH: DL + viele Kanäle | Hartes Gate OOS-R² > 0.25; kanal-weises Ablations-ΔR²; HAR-RV-Benchmark |
| Hidden Liquidity (Q14, S12) | MITTEL: Heuristik-Parameter ohne Ground Truth | Indirekte Validierung (S/R-Halte-Quote) mit Zufalls-Level-Kontrolle |
| Pattern (S5) | HOCH: schwacher Mechanismus | Hartes Gate bedingte OOS-AUC > 0.55, sonst ersatzloser Drop |

**Generalregel:** Walk-Forward-Disziplin ist nicht verhandelbar. Jede Methode hat ein VOR Implementierung fixiertes Validierungs-Gate und Abbruchkriterium (Abschnitt 4) — Gate verfehlt heißt Drop oder Degradierung, nie „Parameter nachjustieren bis es passt".

### 9.2 Bybit-/API-spezifisch

- **REST 600 req/5 s** (IP-Limit; Verstoß → ~10 min Sperre): Poll-Budget der Pipeline < 15 req/min — unkritisch, aber Backoff-Logik + `X-Bapi-Limit-Status`-Auswertung im Collector Pflicht.
- **WS-Reconnect-Handling:** Sequenz-Lücken-Detektion zwingend (Buch-Rekonstruktion bricht sonst still); Snapshot-Resync nach jedem Reconnect; Ping/Pong ~20 s.
- **Endpoint-Disziplin (Anti-Halluzination):** Nur Audit-CONFIRMED-Endpoints verwenden; `orderbook.500` als WS-Topic existiert NICHT; account-ratio-Pfad ist `/v5/market/account-ratio`; `fundingInterval` ist symbolabhängig (1–8 h) und MUSS aus instruments-info gelesen werden.
- **Historie-Lücken als systemisches Risiko:** 8 Methoden hängen an Eigenaufzeichnung; Collector-Ausfall = Datenverlust → Monitoring + Alerting + lokale Spiegelung; optional Tardis-Zukauf (Liquidationen ab 2020-12) als Backfill.
- **Plattform-Änderungsrisiko:** Bybit kann Streams/Felder ändern (z. B. RPI-Buch, ADL-Alert) — Schema-Versionierung im Collector; Methoden mit Bybit-Exklusiv-Daten (Q14, Q2) tragen Plattform-Abhängigkeit.

### 9.3 Regime-Abhängigkeiten

- Kaskaden-Modul liefert NUR in Stress-/High-Vol-Phasen Signal (per Design ok: sonst Risk-On-Default).
- Funding-Edge schrumpft in Niedrig-Funding-Regimen (Carry-Kompression seit 2024 dokumentiert) → G2-BOCPD auf der Funding-Reihe als automatisches Abschalt-Kriterium.
- Lead-Lag-Struktur instabil (BTC-Dominanz vs. Altseason) → rollierender Graph, Kanten mit Ablaufdatum.
- Hidden-Liquidity-Karte ist in Kaskaden bedeutungslos (Bücher leeren sich).
- RV-Prognostizierbarkeit ist regimerobust (belegt) — deshalb ist der Vol-Stack das Fundament.
- Direktionale Claims gelten grundsätzlich nur regime-konditioniert (bedingte AUC > 0.55); unkonditioniert gilt AUC ≈ 0.50.

### 9.4 Hardware-Grenzen (RTX 5060 Ti, 16 GB VRAM / 82 GB RAM / VPS)

- **Passt problemlos in 16 GB VRAM:** PatchTST (1–10 M Parameter, 3–8 GB bei Batch 128), TFT (4–10 GB bei Hidden 64–256), snnTorch-SNNs (< 1 GB). Trainingszeiten: Stunden pro Nacht-Batch — Re-Training-Kadenz wöchentlich realistisch.
- **Nicht sinnvoll auf dieser Karte:** Foundation-Model-Training from scratch, Modelle > ~7 B Parameter ohne Quantisierung — wird von keiner Katalog-Methode benötigt.
- **CPU-/RAM-Engpässe statt GPU:** Hawkes-MLE (S2) ist CPU-intensiv → Branching-Ratio-Approximation zuerst; Tick-Archiv-Verarbeitung (Q6, Q3) braucht Out-of-Core-Tools (DuckDB/polars), 82 GB RAM sind dafür komfortabel; 20-ms-Buchdelta-Ströme (Q14, Q3) sind der Durchsatz-Engpass des Collectors → ggf. auf Top-5-Symbole beschränken.
- **VPS:** Inferenz aller produktiven Modelle läuft im 1-min-Takt auf CPU; GPU im VPS nicht erforderlich.

### 9.5 Rechtliches & Operatives (keine Rechtsberatung — vor Live-Gang prüfen)

- **Zugang:** Bybit-Verfügbarkeit für EU-/deutsche Retail-Kunden ist regulatorisch im Fluss (MiCA-Übergang; Lizenz-/Entity-Wechsel möglich). Kein Anspruch auf dauerhaften API-Zugang; KYC-/Jurisdiktions-Änderungen können das System stilllegen → Plattform-Risiko einplanen, Datenpipeline so bauen, dass ein Exchange-Wechsel (z. B. via CCXT-Abstraktion der REST-Teile) nicht bei null beginnt.
- **Steuern (Deutschland):** Gewinne aus Perpetual Futures sind Termingeschäfte (Kapitaleinkünfte, § 20 EStG); die Verlustverrechnung für Termingeschäfte wurde gesetzlich mehrfach geändert (Beschränkung 2024 rückwirkend entschärft) — Stand vor Live-Gang mit Steuerberater verifizieren; lückenlose Trade-Historie exportieren (eigene Aufzeichnung hilft).
- **Keine Anlageberatung/Marktmanipulation:** Spoofing-DETEKTION (S12) ist legal; eigenes Quoting muss frei von manipulativen Mustern bleiben. Nur Eigenhandel; Verwaltung fremden Kapitals wäre erlaubnispflichtig (KWG/WpIG).
- **Operationell:** API-Keys mit minimalen Rechten (kein Withdrawal); Secrets-Management im Docker-Setup; Kill-Switch (alle Positionen schließen) als erste Order-Routine, die gebaut wird.

### 9.6 Verworfene & zurückgestellte Methoden (negative Ergebnisse sind Wissen)

| Methode | Status | Begründung (Critic/Synthese) |
|---|---|---|
| **S6 Bohmsche Pilotwelle** | VERWORFEN | Edge = 0: „Führungswelle" ist Analogie ohne kausalen Mechanismus; rauschanfällige zweite Ableitungen; operativer Kern (Buch-Dichtekrümmung, Sentiment-Drift) bereits durch S9/Q3/Q11 abgedeckt. Folge: Quantum-Slot der Referenz-Pipeline ersatzlos gestrichen (→ L5-Risk-Bundle, Abschnitt 5.1). |
| **S14 Compressed Sensing** | VERWORFEN (Restidee offen) | Edge = 0: Prämisse inkonsistent — das L2-Buch ist vollständig beobachtbar, es gibt nichts aus „wenigen Messungen" zu rekonstruieren. Rettbarer Kern (Low-Rank+Sparse/Robust-PCA als Anomaliedetektor) optional später in K5. |
| **Q13 TimesNet** | ZURÜCKGESTELLT | DL-Redundanz zu Q4/Q9; Q9 gewählt (Quantil-Output dient direkt L5-Stops; Known-Future-Funding mechanisch sauberer). Dokumentierte Alternativ-Architektur, nicht parallel bauen. |
| **Q10 NHHM** | ZURÜCKGESTELLT | Funktional deckungsgleich mit Q17 als langsame G3-Zustandsmaschine; Q17 gewinnt (höherer Score, Forward-Looking via VRP, Doppelnutzen in L5). Dokumentierter Fallback, falls Q17 an der IV-Aufzeichnungslücke scheitert. |
| S8 SIR/R0 · S10 PE (Scout) · S13 Bragg | MERGED | In S2/Q2 (gleiche Kritikalitätsgröße auf demselben Eventstream), Q12 (≥ 80 % identisch) bzw. Q1 (identisches handelbares Signal; FFT/PSD nur Verifikations-Substep) aufgegangen. |

---

## Qualitäts-Checkliste (Self-Check des PRD Architect)

- [x] Alle 9 Abschnitte vollständig
- [x] Jede Katalog-Methode: Kernformel + exakter Bybit-Endpoint + Backtesting-Ansatz + Validierungskriterien mit konkreten Schwellwerten (keine TBDs) + Zeitschätzung + Hardware-Einschätzung
- [x] Alle 5 Pipeline-Layer beschrieben (ASCII-Diagramm + Textbeschreibung + Libraries); L5-Quantum-Ersatz mit Critic-Begründung dokumentiert
- [x] ≥ 3 Kombinationsstrategien mit Entry-/Exit-Bedingungen (K1–K3, plus K4/K5)
- [x] Priorisierungsmatrix: alle 26 validierten Methoden inkl. zurückgestellter Q10/Q13
- [x] Recording-Infrastruktur als Phase 0; Roadmap Phase 0–4 mit Wochenangaben, realistisch für Einzelperson
- [x] Walk-Forward als Pflicht-Validierung; Abbruchkriterien je Methode; Abschnitt „Verworfene Methoden" mit Begründung
- [x] RTX 5060 Ti (16 GB VRAM), 82 GB RAM, VPS explizit adressiert (4.x, 5.3, 9.4)
- [x] Kein Code; Markdown GitHub-kompatibel; Inhaltsverzeichnis mit Anchors; Formeln in ASCII
