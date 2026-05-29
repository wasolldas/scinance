# STATUS BOARD — Edge Coding Framework

> **Living Document.** Spiegelt den Implementierungs-, Test- und Review-Stand pro Modul/Strategie/Infra.
> Quelle des Ist-Zustands: tatsächliches Repo bei Commit **`d5ed327`** ("…379 tests pass").
> Spec of Record: `../edge_research_framework/results/FINAL_PRD.md` (§4 Methoden, §7 Strategien, §8 Roadmap, §9 Risiken).
> Stand der Aufnahme: 2026-05-29.

## Legende
- **Impl?** — Implementierungsdatei existiert im Repo.
- **Test?** — eigene Testdatei existiert.
- **Klasse** — A = Sandbox-verifizierbar (Pure-Python/Logik/statisch); B = Hardware-Gated (numpy/scipy/duckdb/torch/live/large-data).
- **Sandbox-Status** — was hier (ohne numpy/torch/duckdb/GPU) bewiesen werden kann.
- **Hardware-Status** — was auf Nutzer-Hardware (RTX 5060 Ti + VPS + Bybit-Testnet) verifiziert/gehandoffet werden muss.

**Hinweis zur Klassen-Logik:** Alle Layer-Module M2–M21 importieren numpy (z. T. scipy/statsmodels/PyWavelets/hmmlearn) → **Klasse B** für Laufzeit-/Test-Verifikation, obwohl reine CPU. M18/M19/M20 sind im `src/`-Pfad **numpy-only** (kein torch); torch lebt nur im optionalen `[gpu]`-Extra (M20 LoRA/Training) → der GPU-Pfad ist zusätzlich GPU-gated. **M1 SpikeWavformer** ist Pure-Python (LIF) → Kern-Logik Klasse A; numpy-Integrationspfade B.

---

## Infrastruktur (PRD §8 Phase 0)

| Komponente | Datei | Impl? | Test? | Klasse | Sandbox-Status | Hardware-Status |
|------------|-------|:-----:|:-----:|:------:|----------------|-----------------|
| WS-Collector | `collector/ws_collector.py` | ✓ | ⚠ (über `test_infrastructure.py`) | B (live) | Logik/Reconnect statisch prüfbar | Live-WS/Resync auf VPS testen |
| Persistence (DuckDB) | `persistence/db.py` | ✓ | ⚠ (über `test_infrastructure.py`) | B (duckdb) | Import-/Schema-Logik statisch | Roundtrip + Parquet auf Hardware |
| State-Buffer | `state/{orderbook,ticker,trade,liquidation}_*.py` | ✓ | ⚠ (über `test_infrastructure.py`) | B (numpy) | Pub/Sub-Logik statisch | numpy-Buffer-Tests auf Hardware |
| Scheduler (Funding-Cron) | `scheduler.py` | ✓ | ⚠ | A/B | Cron-Zeit-Logik (Klasse A) | Live-Trigger auf VPS |
| Backtester | `backtester/engine.py` | ✓ | ✓ (`test_backtest_driver.py`) | B (numpy) | Walk-Forward/Fee-Logik statisch | Backtest-Lauf + Metriken auf Hardware |
| Config | `config.py` | ✓ | — | B (duckdb-import) | Param-Struktur statisch | — |
| Monitor | `monitor.py` | ✓ | ✓ (`test_infrastructure.py`) | A/B | Logik prüfbar | Prometheus live |
| Executor | `execution/bybit_executor.py` | ✓ | ✓ (`test_execution_live.py`) | B (live) | Signatur-/HMAC-Logik statisch | Testnet-Order (Mainnet verweigert) |
| LiveRunner | `live_runner.py` | ✓ | ✓ (`test_execution_live.py`) | B (live) | Loop-Verdrahtung statisch | Live/Paper-Lauf auf VPS |
| DecisionAggregator | `decision_aggregator.py` | ✓ | — (über `test_pipeline.py`?) | B (numpy) | Selector/Sizing-Logik statisch | End-to-End mit ≥2 Strategien |
| Pipeline | `pipeline.py` | ✓ | ✓ (`test_pipeline.py`) | B (numpy) | Kaskaden-Wiring statisch | Lauf mit echten Modulen |

⚠ = durch Sammeltest abgedeckt, ggf. dediziertere Tests sinnvoll.

---

## Methoden M1–M26 (PRD §4)

| M# | Name | Layer | Tag | Impl-Datei | Test-Datei | Klasse | Sandbox-Status | Hardware-Status |
|----|------|:-----:|-----|-----------|-----------|:------:|----------------|-----------------|
| M1 | SpikeWavformer (SNN+DWT) | L1 | Moonshot | `layers/l1_ingestion/m1_spikewavformer.py` | `test_m1_spikewavformer.py` | A(Kern)/B | LIF-Logik smoke-fähig | DWT/Integrationspfad auf Hardware |
| M2 | OFI Cont-Kukanov-Stoikov | L1 | Quick Win | `layers/l1_ingestion/m2_ofi.py` | `test_m2_ofi.py` | B (numpy) | Formel-Review vs PRD | Unit-Test auf Hardware |
| M3 | Iceberg-Detection | L1 | Standard | `layers/l1_ingestion/m3_iceberg.py` | `test_m3_iceberg.py` | B (numpy) | Formel-Review | Unit-Test auf Hardware |
| M4 | Wavelet-Symlet-Denoising | L2 | Standard | `layers/l2_denoising/m4_wavelet.py` | `test_m4_wavelet.py` | B (PyWavelets) | Review | Unit-Test auf Hardware |
| M5 | FFD (López de Prado) | L2 | Standard | `layers/l2_denoising/m5_ffd.py` | `test_m5_ffd.py` | B (numpy/statsmodels) | Review; statsmodels-Skip-Pattern vorhanden | Unit-Test auf Hardware |
| M6 | Shannon-Entropie L2 | L3 | Quick Win | `layers/l3_regime/m6_entropy.py` | `test_m6_entropy.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M7 | Permutation Entropy | L3 | Quick Win | `layers/l3_regime/m7_permutation_entropy.py` | `test_m7_permutation_entropy.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M8 | BOCPD auf OI | L3 | Quick Win | `layers/l3_regime/m8_bocpd.py` | `test_m8_bocpd.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M9 | HMM (3-state) | L3 | Standard | `layers/l3_regime/m9_hmm.py` | `test_m9_hmm.py` | B (hmmlearn) | Review; Walk-Forward prüfen | Train+Unit auf Hardware |
| M10 | MF-DFA | L3 | Standard | `layers/l3_regime/m10_mfdfa.py` | `test_m10_mfdfa.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M11 | TDA / Persistent Homology | L3 | Standard | `layers/l3_regime/m11_tda.py` | `test_m11_tda.py` | B (numpy/ripser?) | Review; Dep prüfen | Unit-Test auf Hardware |
| M12 | RQA | L3 | Standard | `layers/l3_regime/m12_rqa.py` | `test_m12_rqa.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M13 | Cross-Sectional-Z | L3 | Standard | `layers/l3_regime/m13_cross_sectional_z.py` | `test_m13_csz.py` | B (numpy) | Review; Delisting/Survivorship prüfen | Multi-Symbol-Test auf Hardware |
| M14 | Hawkes ρ(Φ) (1-D→6-D) | L4 | Moonshot | `layers/l4_pattern/m14_hawkes.py` | `test_m14_hawkes.py` | B (numpy; numba hot) | Review; 1-D vs 6-D Stand prüfen | MLE/Intensität auf Hardware |
| M15 | Gutenberg-Richter + Omori | L4 | Quick Win | `layers/l4_pattern/m15_gr_omori.py` | `test_m15_gr_omori.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M16 | TFSAX + Smith-Waterman | L4 | Moonshot | `layers/l4_pattern/m16_tfsax_sw.py` | `test_m16_tfsax.py` | B (numpy) | Review; Library-Aufbau-Pfad | Alignment-Lauf auf Hardware |
| M17 | Renyi-Transfer-Entropy | L4 | Standard | `layers/l4_pattern/m17_renyi_te.py` | `test_m17_renyi_te.py` | B (numpy) | Review; Delisting prüfen | Lead-Lag-Graph auf Hardware |
| M18 | PatchTST (numpy-only) | L4 | Standard | `layers/l4_pattern/m18_patchtst.py` | `test_m18_patchtst.py` | B (numpy) | Review; Walk-Forward (PRD §9.1) | Forecast-Lauf auf Hardware |
| M19 | TimesNet (numpy-only) | L4 | Standard | `layers/l4_pattern/m19_timesnet.py` | `test_m19_timesnet.py` | B (numpy) | Review; Walk-Forward | Forecast-Lauf auf Hardware |
| M20 | MOMENT (Zero-Shot+LoRA) | L4 | Standard | `layers/l4_pattern/m20_moment.py` | `test_m20_moment.py` | B (numpy; **torch/GPU** für LoRA) | Review; numpy-Fallback statisch | **GPU**: LoRA/FineTune; VRAM ≤16GB (PRD §9.4) |
| M21 | L/S-Ratio Smart-Money | L4 | Quick Win | `layers/l4_pattern/m21_ls_ratio.py` | `test_m21_ls_ratio.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M22 | Funding-Clamp Pressure-Release | L5 | **Top-Prio** | `layers/l5_risk/m22_funding_pressure.py` | `test_m22_funding_pressure.py` | B (numpy) | Review; **config-driven Funding-Params (§9.2)** prüfen | Backtest + Unit auf Hardware |
| M23 | Mark-Index Basis Convergence | L5 | Quick Win | `layers/l5_risk/m23_basis_convergence.py` | `test_m23_basis.py` | B (numpy) | Review; config-Params | Unit-Test auf Hardware |
| M24 | Kalman-Funding-Premium | L5 | Standard | `layers/l5_risk/m24_kalman_premium.py` | `test_m24_kalman.py` | B (pykalman/filterpy) | Review; config-Params | Unit-Test auf Hardware |
| M25 | Kyle's Lambda | L5 | Standard | `layers/l5_risk/m25_kyle_lambda.py` | `test_m25_kyle.py` | B (numpy) | Review | Unit-Test auf Hardware |
| M26 | SIR-Liquidations-Contagion | L5 | Standard | `layers/l5_risk/m26_sir.py` | `test_m26_sir.py` | B (numpy/scipy) | Review | Unit-Test auf Hardware |

---

## Strategien (PRD §7)

| # | Name | Methoden-Set (PRD §7) | Impl-Datei | Test-Datei | Klasse | Sandbox-Status | Hardware-Status |
|---|------|------------------------|-----------|-----------|:------:|----------------|-----------------|
| 1 | Seismischer Cascade Detector | M14 + M15 + M26 | `strategies/strategy1_cascade.py` | `test_strategies.py` | B | Logik-Review vs PRD §7 | Backtest (Sharpe/MaxDD/WinRate) auf Hardware |
| 2 | Entropie-Momentum | M6 + M7 + M2 (+OFI/Funding) | `strategies/strategy2_entropy_momentum.py` | `test_strategies.py` | B | Logik-Review | Backtest auf Hardware |
| 3 | Pre-Settlement Pressure-Release | M22 + M23 + M24 | `strategies/strategy3_pre_settlement.py` | `test_strategy3.py` | B | Logik-Review; **Top-Prio live** | Backtest + Testnet-Paper (Prio 1) |
| 4 | Pattern-Ensemble | M5 + M16 + M18 + M19 + M20 | `strategies/strategy4_pattern_ensemble.py` | `test_strategies.py` | B (+GPU via M20) | Logik-Review; Multi-Model-Konsens | Backtest auf Hardware; M20 GPU |
| 5 | Cross-Sectional Ergodicity-Reversion | M13 + M17 + M9 | `strategies/strategy5_cross_sectional.py` | `test_strategies.py` | B | Logik-Review | Backtest auf Hardware |

*Methoden-Sets gegen PRD §7 verbindlich verifizieren; obige Sets sind aus §7-Lektüre abgeleitet.*

---

## Zusammenfassung

- **Code vorhanden:** alle 26 Module, alle 5 Strategien, vollständige Infra. → Dies ist primär ein **Verifikations-, Reconcile- und Hardening-Backlog**, kein Greenfield.
- **Sandbox-verifizierbar (Klasse A) jetzt:** statische Qualität (`ruff`/`mypy`), Dateiexistenz-Gates, Wiring-Konsistenz, Pure-Python-Smoke (M1-LIF, Config-/Cron-/Sizing-Logik), Marker-Skip-Verhalten, Spec-Abgleich (Review-Lesen).
- **Pending user hardware test (Klasse B):** praktisch alle M-Modul-Unit-Tests (numpy), Persistence-Roundtrips (duckdb), Backtest-Metriken (numpy/large-data), Live/Testnet (WS/Executor/LiveRunner), und der **GPU-Pfad M20 LoRA/Training**.
- **Baseline 379 Tests:** Diese laufen auf Nutzer-Hardware grün (inkl. numpy etc.); in der Sandbox laufen davon nur die dependency-freien, der Rest muss **sauber skippen** — ggf. fehlt dafür noch ein `tests/conftest.py` mit Marker-/Dep-Guards (offener Klasse-A-Task für den Test Engineer).

## Offene Verifikations-Tasks (Klasse A, in Sandbox abzuarbeiten)
1. `tests/conftest.py` mit Dep-/Marker-Guards anlegen, damit Sandbox-Lauf nur skippt, nie erstellt erroren (analog `_HAS_STATSMODELS`).
2. Marker (`gpu`, `live`, `slow`, `requires_numpy`, `requires_duckdb`) in `pyproject.toml` registrieren und in Tests setzen.
3. Spec-Abgleich M22/M23/M24 auf **config-driven Funding-Params** (§9.2) — falls hartkodiert: Reconcile-Task.
4. Walk-Forward/Purged-CV/Hold-Out-Struktur (§9.1) in M9/M16/M18/M19/M20 + Strategien gegen PRD prüfen.
5. Wiring-Konsistenz `pipeline.py` ↔ vorhandene Module per Import-Check verifizieren.
