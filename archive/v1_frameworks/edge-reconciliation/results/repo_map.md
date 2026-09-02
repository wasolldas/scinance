# Repo Map — scinance

*Erstellt: 2026-06-11 | Branch: `claude/subagent-prd-development-T16fE` | Letzter Commit: `aeff39a [RECON] Init edge-reconciliation run: framework + input corpus`*

---

## 1. Überblick Repository-Wurzel

```
/home/user/scinance/
├── src/bybit_edge/          # Haupt-Implementierung (5-Layer-Pipeline + Strategien)
├── scripts/                 # CLI-Einstiegspunkte (Backfill, Replay, Train, Dashboard)
├── tests/                   # Unit- und Integrationstests (88+ Tests)
├── data/                    # Persistierte Marktdaten (Parquet + trades_journal.csv)
├── docker/                  # Container-Setup (CLAUDE.md + agents/)
├── edge-reconciliation/     # Dieses Framework (Reconciliation-Workflow)
├── edge_research_framework/ # Älteres Forschungsframework (CLAUDE.md + agents/)
├── implementation_framework/# Implementierungsrahmen (CLAUDE.md + README + agents/)
├── pyproject.toml           # Projektdefinition (uv-basiert)
├── environment.yml          # Conda-Umgebung
└── start.bat                # Windows-Starter
```

---

## 2. Kern-Implementierung: `src/bybit_edge/`

### 2.1 5-Layer-Pipeline — Vollständig implementiert (C-01 bis C-26)

#### L1 — Ingestion (`layers/l1_ingestion/`)
| Datei | Modul | Claim |
|---|---|---|
| `m1_spikewavformer.py` | M1 SpikewavFormer | C-01 |
| `m2_ofi.py` | M2 Order-Flow-Imbalance | C-02 |
| `m3_iceberg.py` | M3 Iceberg-Detektor | C-03 |

#### L2 — Denoising (`layers/l2_denoising/`)
| Datei | Modul | Claim |
|---|---|---|
| `m4_wavelet.py` | M4 Wavelet-Denoising | C-04 |
| `m5_ffd.py` | M5 FFD-Fraktionierung | C-05 |

#### L3 — Regime (`layers/l3_regime/`)
| Datei | Modul | Claim |
|---|---|---|
| `m6_entropy.py` | M6 Shannon-Entropie | C-06 |
| `m7_permutation_entropy.py` | M7 Permutation-Entropie | C-07 |
| `m8_bocpd.py` | M8 BOCPD | C-08 |
| `m9_hmm.py` | M9 HMM Regime | C-09 |
| `m10_mfdfa.py` | M10 MF-DFA | C-10 |
| `m11_tda.py` | M11 TDA/Persistent Homology | C-11 |
| `m12_rqa.py` | M12 RQA | C-12 |
| `m13_cross_sectional_z.py` | M13 Cross-Sectional Z | C-13 |

#### L4 — Pattern (`layers/l4_pattern/`)
| Datei | Modul | Claim |
|---|---|---|
| `m14_hawkes.py` | M14 Hawkes-Prozess | C-14 |
| `m15_gr_omori.py` | M15 GR/Omori-Gesetz | C-15 |
| `m16_tfsax_sw.py` | M16 TF-SAX Sliding Window | C-16 |
| `m17_renyi_te.py` | M17 Rényi Transfer-Entropie | C-17 |
| `m18_patchtst.py` | M18 PatchTST | C-18 |
| `m19_timesnet.py` | M19 TimesNet | C-19 |
| `m20_moment.py` | M20 MOMENT-Stiftungsmodell | C-20 |
| `m21_ls_ratio.py` | M21 Long/Short-Ratio | C-21 |

#### L5 — Risk (`layers/l5_risk/`)
| Datei | Modul | Claim |
|---|---|---|
| `m22_funding_pressure.py` | M22 Funding-Pressure | C-22 |
| `m23_basis_convergence.py` | M23 Basis-Convergence | C-23 |
| `m24_kalman_premium.py` | M24 Kalman Premium-Index | C-24 |
| `m25_kyle_lambda.py` | M25 Kyle Lambda | C-25 |
| `m26_sir.py` | M26 SIR-Liquidations-Modell | C-26 |

### 2.2 Strategien (`strategies/`) — S1-S5 implementiert

| Datei | Strategie | Claim | Empirischer Status (P-01/P-02) |
|---|---|---|---|
| `strategy1_cascade.py` | S1 Cascade | CS-01 | ABANDON (ρ-Schwelle empirisch 6 Größenordnungen daneben) |
| `strategy2_entropy_momentum.py` | S2 Entropy-Momentum | CS-02 | ABANDON (Richtungsthese invertiert, Forensik liefert −4.55 bps) |
| `strategy3_pre_settlement.py` | S3 Pre-Settlement | CS-03 | PROMISING/TEILGETESTET (Entry-Signal roh vorhanden, Exit-Seite defekt; iter-5 ausstehend) |
| `strategy4_pattern_ensemble.py` | S4 Pattern-Ensemble | CS-04 | UNTESTED (Modell-Loader architekturgebunden) |
| `strategy5_cross_sectional.py` | S5 Cross-Sectional | CS-05 | UNTESTED (Panel-Replayer fehlt) |

### 2.3 Infrastruktur-Komponenten

| Datei/Verzeichnis | Funktion |
|---|---|
| `state/orderbook_state.py` | Orderbook-Zustandsverwaltung |
| `state/ticker_state.py` | Ticker-Zustandsverwaltung (inkl. envelope_ts-Fix) |
| `state/trade_buffer.py` | Trade-Ringpuffer |
| `state/liquidation_buffer.py` | Liquidations-Ringpuffer (allLiquidation WS) |
| `collector/ws_collector.py` | WebSocket-Collector (Bybit V5 WS-Streams) |
| `persistence/db.py` | SQLite-Persistenz |
| `persistence/backfill.py` | REST-Backfill (historical data) |
| `backtester/engine.py` | Backtest-Engine |
| `replay_backtester.py` | Replay-Backtester (walk-forward, diagnostics) |
| `replay_all.py` | Multi-Symbol-Replay-Aggregator |
| `execution/bybit_executor.py` | Live-Execution (Bybit V5 REST/WS) |
| `live_runner.py` | Live-Runner (Echtzeit-Strategie-Ausführung) |
| `multi_runner.py` | Multi-Symbol-Live-Runner |
| `pipeline.py` | 5-Layer-Pipeline-Orchestrator |
| `decision_aggregator.py` | Signal-Aggregation über Strategien |
| `risk/budget.py` | Risiko-Budget-Manager |
| `scheduler.py` | Aufgaben-Scheduler |
| `monitor.py` | System-Monitoring |
| `dashboard/app.py` | Streamlit-Dashboard |
| `dashboard/data.py` | Dashboard-Datenlayer |
| `training/dataset.py` | ML-Trainingsdaten-Aufbereitung |
| `tuning/optuna_tuner.py` | Optuna-Hyperparameter-Tuning |
| `config.py` | Globale Konfiguration |

---

## 3. Scripts (`scripts/`)

| Datei | Funktion |
|---|---|
| `backfill.py` | Historische Daten via REST nachladen |
| `backtest.py` | Backtest-Runner |
| `replay_backtest.py` | Replay-Backtest mit Diagnose-Flag |
| `replay_all.py` | Multi-Symbol-Replay (CLI-Wrapper) |
| `train_models.py` | ML-Modell-Training (PatchTST, TimesNet, MOMENT) |
| `tune.py` | Optuna-Hyperparameter-Optimierung |
| `dashboard.py` | Dashboard starten |
| `_profile_replay.py` | Performance-Profiling (Hotspot-Analyse) |
| `setup_local.sh` | Lokales Setup-Skript |

---

## 4. Tests (`tests/`)

### Unit-Tests je Modul (tests/unit/)

| Testdatei | Abgedecktes Modul |
|---|---|
| `test_m1_spikewavformer.py` | M1 / C-01 |
| `test_m2_ofi.py` | M2 / C-02 |
| `test_m3_iceberg.py` | M3 / C-03 |
| `test_m4_wavelet.py` | M4 / C-04 |
| `test_m5_ffd.py` | M5 / C-05 |
| `test_m6_entropy.py` | M6 / C-06 |
| `test_m7_permutation_entropy.py` | M7 / C-07 |
| `test_m8_bocpd.py` | M8 / C-08 |
| `test_m9_hmm.py` | M9 / C-09 |
| `test_m10_mfdfa.py` | M10 / C-10 |
| `test_m11_tda.py` | M11 / C-11 |
| `test_m12_rqa.py` | M12 / C-12 |
| `test_m13_csz.py` | M13 / C-13 |
| `test_m14_hawkes.py` | M14 / C-14 |
| `test_m15_gr_omori.py` | M15 / C-15 |
| `test_m16_tfsax.py` | M16 / C-16 |
| `test_m17_renyi_te.py` | M17 / C-17 |
| `test_m18_patchtst.py` | M18 / C-18 |
| `test_m19_timesnet.py` | M19 / C-19 |
| `test_m20_moment.py` | M20 / C-20 |
| `test_m21_ls_ratio.py` | M21 / C-21 |
| `test_m22_funding_pressure.py` | M22 / C-22 |
| `test_m23_basis.py` | M23 / C-23 |
| `test_m24_kalman.py` | M24 / C-24 |
| `test_m25_kyle.py` | M25 / C-25 |
| `test_m26_sir.py` | M26 / C-26 |

### Infrastruktur- und Strategietests (tests/unit/)

| Testdatei | Abgedeckter Bereich |
|---|---|
| `test_strategies.py` | Strategie-Gesamtintegration S1-S5 |
| `test_strategy1_rho_instrument.py` | S1 ρ-Instrumentation (C-14-Abhängigkeit) |
| `test_strategy3.py` | S3 Grundfunktion |
| `test_strategy3_bounded_exits.py` | S3 Exit-Logik (T2-Fix: friction-aware hard-stop) |
| `test_strategy_direction_inversion.py` | S2/S3 Richtungsinversion (--invert-strategies) |
| `test_replay_backtester.py` | Replay-Backtester |
| `test_replay_backtester_maker_only.py` | Maker-only Forensik (S2) |
| `test_replay_all.py` | Multi-Symbol-Aggregator |
| `test_replay_backtest_cli.py` | CLI-Interface |
| `test_pipeline.py` | 5-Layer-Pipeline-Integration |
| `test_multi_runner.py` | Multi-Runner |
| `test_infrastructure.py` | WS-Collector, State, Persistence |
| `test_backfill.py` | REST-Backfill |
| `test_backtest_driver.py` | Backtest-Engine |
| `test_dashboard.py` | Dashboard-Datenlayer |
| `test_execution_live.py` | Live-Executor |
| `test_training.py` | ML-Training |
| `test_tuning.py` | Optuna-Tuning |
| `test_risk_budget.py` | Risiko-Budget |
| `conftest.py` | Gemeinsame Fixtures |

**Aktueller Test-Stand:** 88 Tests pass (laut letztem Commit-Banner vor RECON-Commit).

---

## 5. Code-zu-Claim-Mapping: Abdeckung

### Vollständig implementiert (C-01 bis C-26, CS-01 bis CS-05)

Alle Module aus PRD-v1 (M1-M26) sind als Python-Dateien vorhanden.
Alle fünf Strategien aus PRD-v1 (S1-S5) sind implementiert.
Jedes Modul hat einen dedizierten Unit-Test.

### NICHT implementiert (C-27 bis C-43, CS-06 bis CS-13)

Alle Claims aus PRD-fable5 und PRD-kestrel-basis, die über PRD-v1 hinausgehen, haben **keinen entsprechenden Code** im Repo:

| Claim | Beschreibung | Fehlender Code-Bereich |
|---|---|---|
| C-27 | Cori-Rₜ Renewal Equation | Kein `m_cori.py` oder analoges Modul |
| C-28 | NB-k Superspreading | Kein Negativ-Binomial-Cluster-Modul |
| C-29 | Avalanche Shape Collapse | Kein Avalanche-Skalierungs-Modul |
| C-30 | Natural Time κ₁ | Kein Naturzeit-Modul |
| C-31 | Zyklisches Spektrum | Kein Cyclostationary-Spektrum-Modul |
| C-32 | Funding Contrarian | Kein eigenständiges Funding-Contrarian-Modul |
| C-33 | VRP Short-Vola (Optionen) | Kein Options-Modul vorhanden |
| C-34 | GMM-VRP (Kestrel) | Kein GMM-basiertes VRP-Modul |
| C-35 | CEEMDAN kausal | Kein CEEMDAN-Dekompositions-Modul |
| C-36 | F0 Recording Infrastructure | Kein Phase-0-Datenerfassungs-Modul (RPI-Book, Insurance-Pool-Delta, ADL-Alert) |
| C-37 | Spread-Market Execution | Keine Nutzung von `/v5/spread/*` API-Endpunkten |
| C-38 | TFT mit known-future-funding | Kein TFT-Modul (M18 ist PatchTST, kein TFT) |
| C-39 | Kaskaden-Anatomie extended | Basis in C-26 (SIR), aber Konkurs-Preis/Insurance/ADL-Signale nicht eingebunden |
| C-40 | RPI Hidden Liquidity | Kein `orderbook.rpi` WS-Handler |
| C-41 | Wavelet Coherence | Kein Wavelet-Kohärenz-Modul (M4 macht Denoising, nicht Kohärenz) |
| C-42 | LightGBM Vol-Baseline | Kein LightGBM-Modul im `src/bybit_edge/`-Baum (war in separatem Kestrel-v1.4-Notebook) |
| C-43 | Conformal Prediction | Kein Conformal-Prediction-Kalibriermodul |
| CS-06 bis CS-10 | PRD-fable5-Strategien A-E | Keine entsprechenden Strategie-Dateien |
| CS-11 bis CS-13 | PRD-kestrel-Strategien K1-K3 | Keine entsprechenden Strategie-Dateien |

### Kritische Infrastruktur-Lücken (C-36 spezifisch)

PRD-kestrel-basis definiert Phase 0 (C-36/F0) als Voraussetzung für 12 nachgelagerte Claims. Der WS-Collector (`collector/ws_collector.py`) sammelt aktuell:
- tickers (100ms)
- allLiquidation (500ms)
- Orderbook (Standard-Streams)
- publicTrade

**Nicht gesammelt:**
- `orderbook.rpi` (100ms) — RPI-Orderbook (kein Archiv verfügbar, First-Mover-Dataset)
- `insurance.USDT` (1s) — Insurance-Pool-Delta
- `adlAlert` (1s) — ADL-Alarm-Ereignisse
- Premium-Index-Kline (REST `premium-index-price-kline`) — tiefer historischer Bestand
- Options-Tickers (IV/Greeks) — kein Archiv laut PRD-kestrel

---

## 6. Daten (`data/`)

```
data/
├── parquet/    # Persistierte Marktdaten im Parquet-Format
└── trades_journal.csv  # Handelsjournal (Replay-/Backtest-Ergebnisse)
```

Format und Inhalt der Parquet-Dateien: nicht im Detail untersucht (außerhalb des Inventory-Scope).

---

## 7. Weitere Framework-Verzeichnisse

| Verzeichnis | Inhalt | Relevanz |
|---|---|---|
| `edge_research_framework/` | Älteres Forschungsframework (CLAUDE.md + agents/) | Vorgänger des aktuellen `edge-reconciliation/`-Setups |
| `implementation_framework/` | Implementierungsrahmen (CLAUDE.md + README + agents/) | Parallel-Framework; agents/ vorhanden |
| `docker/` | Container-Konfiguration (CLAUDE.md + agents/) | Docker/VPS-Deployment |

---

## 8. Git-Status

- **Aktiver Branch:** `claude/subagent-prd-development-T16fE`
- **Remote:** `origin/claude/subagent-prd-development-T16fE`
- **Letzter Commit:** `aeff39a [RECON] Init edge-reconciliation run: framework + input corpus`
- **Vorherige Commit-Geschichte:** Aktive Entwicklung von S1/S2/S3 mit bugfix-Kette (ts=0-Envelope-Bug, BOCPD, Omori-Throttle, T1/T2-Fixes für S3, Multi-Symbol-Replay, Walk-Forward)
- **Test-Banner im letzten Entwicklungscommit:** 88/88 Tests pass

---

## 9. Lücken-Zusammenfassung (Bezug zu Claims)

| Kategorie | Anzahl fehlender Claims | Wichtigste Beispiele |
|---|---|---|
| Neue epidemiologische Methoden (PRD-fable5) | 5 | C-27, C-28, C-29, C-30, C-31 |
| Neue Kestrel-spezifische Methoden | 8 | C-34–C-41 |
| Options-Markt | 2 | C-33, CS-09 |
| Recording Infrastructure (Voraussetzung für ~12 Claims) | 1 | C-36 (F0) |
| Validierter ML-Baseline außerhalb des Repo-Baums | 1 | C-42 |
| Calibration-Framework | 1 | C-43 |
| Neue Strategien (fable5 A-E + kestrel K1-K3) | 8 | CS-06 bis CS-13 |

**Fazit:** Von 43 Modul-Claims (C-01 bis C-43) und 13 Strategie-Claims (CS-01 bis CS-13) sind **26 Modul-Claims (C-01–C-26) und 5 Strategie-Claims (CS-01–CS-05) im Code vorhanden**. Die restlichen **17 Modul-Claims und 8 Strategie-Claims** haben keinerlei Implementierung im Repo.
