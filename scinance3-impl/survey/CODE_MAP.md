# Scinance — CODE_MAP.md

Survey date: 2026-09-02. Git history in this working copy starts 2026-07-19 (single
squashed import commit); internal docs (`scinance2-impl/state/*.md`) carry earlier
provenance dates back to ~2026-06-11 for the recorder and ~2026-06-13 for the "Scinance
1.0" strategy portfolio. Repo self-documents its own archaeology in
`scinance2-impl/state/CLEANUP_PLAN.md` (2026-06-23) and `PROGRAM_FINAL_REPORT.md`
(2026-07-06) — both were used as corroborating primary sources below, cross-checked
against live `grep`/import evidence (imports can drift from what old docs say; every
verdict below is import-evidence-based, docs are used only as provenance/dating color).

Legend: **LIVE-INFRA** = used by the running recorder/replay/backtester-core/config.
**RESEARCH-V2** = under `src/bybit_edge/research/*`, driven by a `scripts/c*.py` /
`scripts/wp*.py` driver that a `scinance2-impl/handoff_local/run_*.ps1` script calls.
**LEGACY-V1** = the original "Scinance 1.0" strategy/live-trading stack — not imported by
any RESEARCH-V2 driver or by `start.bat`/recorder path. **UNKNOWN** = ambiguous.

---

## 1. Top-level directories and files

| Path | Purpose | Era / provenance | Size |
|---|---|---|---|
| `README.md` | Original project pitch: "Edge Research Framework" multi-agent system, describes the fantastical L1-L5 pipeline (SNN Ingestion → Wavelet → Entropy → TFSAX/Hawkes → Quantum Risk) | **v0/v1 concept doc** — names match `src/bybit_edge/layers/` module names exactly | 1.3 KB |
| `FINAL_PRD.md` | The "constitution" — Scinance 2.0 Final PRD referenced by `scinance2-impl/CLAUDE.md` as governing document | v1→v2 transition artifact | 36 KB |
| `edge_research_framework/` | Pure-markdown multi-agent research pipeline (`agents/01_orchestrator.md` … `06_prd_architect.md`, `results/*.md`) that *produced* `FINAL_PRD.md`. No code. | **v1 research-agent framework** (matches README pipeline names) | 284 KB, 0 .py |
| `edge-reconciliation/` | Markdown multi-agent "debate" framework (advocate/skeptic/judge agents) reconciling competing PRD drafts (`FINAL_PRD-kestrel-basis.md`, `FINAL_PRD-fable5.md`) into one verdict. No code. | **v1.5 reconciliation framework**, post-dates original PRD, pre-dates scinance2-impl | 1 MB, 0 .py |
| `edge-research-v3/` | Markdown multi-agent "discipline scan" framework (econophysics-rmt, dendrochronology-crossdating, mechanism-design, etc.) hunting cross-domain analogues for new hypotheses. No code. | **speculative v3 research framework**, appears not to have fed any implemented code (no `c-` module in `src/` traces to these discipline names) | 492 KB, 0 .py |
| `implementation_framework/` | Markdown agent definitions (`01_analyst`, `02_infra_builder`, `03_module_builder`, `04_test_integrator_devops`) — generic "build the PRD" agent framework, precursor to `scinance2-impl/.claude/agents/`. No code. | v1→v2 transition scaffolding | 80 KB, 0 .py |
| `scinance2-impl/` | **The actual v2 orchestration record**: `CLAUDE.md` (orchestrator protocol), `state/*.md` (~50 files: decisions, gate log, hypothesis registry, per-wave final reports, `CLEANUP_PLAN.md`), `handoff_local/` (T2/T3 runner scripts + committed run logs/results), `.claude/agents/`. | **v2 "scinance2-impl"** — live project-management substrate, still being written to (last commit 2026-09-01) | 15 MB (mostly logs/JSON results) |
| `scripts/` | 40 Python CLI entry points: v2 research drivers (`c01_*.py` … `c24_*.py`, `wp*.py`) + legacy v1 tools (`backtest.py`, `train_models.py`, `tune.py`, `dashboard.py`, `backfill.py`, `replay_*.py`) + `setup_local.sh` (stale onboarding script referencing a dead `run_backtest.py`) | mixed — see §3 | 504 KB, 8013 LoC |
| `src/` | The `bybit_edge` Python package — see §2 | mixed v1/v2 | 3.2 MB, 206 .py, 56 555 LoC |
| `tests/` | 86 test files (`tests/unit/` 83 files, `tests/integration/` and `tests/backtests/` empty stubs, `tests/fixtures/` data) | mixed v1/v2 | 13 MB (mostly fixture data) |
| `pyproject.toml` | Package `bybit-edge`, no `[project.scripts]` entry points; deps below (§6) | current | 1.5 KB |
| `environment.yml` | Conda env for GPU (torch+CUDA) local machine | current | 0.3 KB |
| `start.bat` | Windows menu launcher — **already stripped of the legacy live-pipeline option** (see §5); explicitly labels "Scinance-1.0-Live-Pipeline ist DEPRECATED (CLEANUP_PLAN.md)" | v2, updated | 3.9 KB |
| `start_recorder.ps1`, `install_recorder_autostart.ps1`, `uninstall_recorder_autostart.ps1` | Recorder (C-36) launcher + Windows Task Scheduler autostart install/uninstall | **LIVE-INFRA entry points**, v2 | 5.5/3.9/1.6 KB |

---

## 2. `src/bybit_edge/` — subpackages and modules >150 LoC

### 2.1 Package-level / shared infra

| Module | LoC | Purpose | Imported by (grep evidence) | Class |
|---|---|---|---|---|
| `config.py` | 633 | Central config: Bybit endpoints, `MULTI_SYMBOL_UNIVERSE`, `DB_PATH`, PRD constants, fee/latency constants | 71 files across src/scripts/tests — universally imported | **LIVE-INFRA** |
| `__main__.py` | 156 | `python -m bybit_edge` entry — dispatches `MultiSymbolRunner` vs `LiveRunner` | Only itself; **no longer referenced from `start.bat`** (menu option removed) | **LEGACY-V1** (dead entry point) |
| `live_runner.py` | 864 | Live trading loop: Collector→Pipeline→Strategies S1-S5→order eval→persistence flush | `multi_runner.py`, `__main__.py`; tests: `test_multi_runner.py`, `test_execution_live.py` | **LEGACY-V1** |
| `multi_runner.py` | 169 | 5-symbol parallelization of `LiveRunner` | `__main__.py`; `test_multi_runner.py` | **LEGACY-V1** |
| `pipeline.py` | 325 | Glue: state-engines → L1-L5 layers → strategies → `DecisionAggregator` | `live_runner.py`; `test_pipeline.py` | **LEGACY-V1** |
| `decision_aggregator.py` | 160 | Weights S1-S5 signals into one decision | `pipeline.py`; `test_strategies.py` | **LEGACY-V1** |
| `monitor.py` | 122 | TUI for PnL/equity, reads `bybit_edge.duckdb` | none (no test file, no script beyond dead `start.bat` option 3) | **LEGACY-V1**, effectively orphaned |
| `scheduler.py` | 136 | Risk-reset clock for live execution | `test_infrastructure.py` only | **LEGACY-V1** |
| `replay_backtester.py` | 1770 | Forensic replay/backtest engine reproducing live-pipeline fills bar-by-bar | `scripts/tune.py`, `scripts/replay_all.py`, `scripts/replay_backtest.py`, `scripts/_profile_replay.py`; **not** imported by any RESEARCH-V2 driver (only docstring references disclaiming it) | **LEGACY-V1**, but explicitly retained per policy as forensic audit tool (see `CLEANUP_PLAN.md` §3.1) |
| `replay_all.py` | 440 | Full-replay loop over all strategies (forensic tool) | `scripts/replay_all.py` only | **LEGACY-V1** |

### 2.2 `collector/` — LEGACY-V1

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `ws_collector.py` | 327 | Bybit WS collector for tickers/publicTrade/orderbook/liquidations, writes `bybit_edge.duckdb` | `live_runner.py`, `multi_runner.py`, `dashboard/data.py`, `dashboard/app.py`; `test_execution_live.py` | **LEGACY-V1** — CLEANUP_PLAN verdict "REPLACE by external Harvester"; superseded operationally by the recorder + external harvester, not started by current `start.bat` |

### 2.3 `recorder/` — LIVE-INFRA (Schutzgut #1 / "protected asset #1")

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `recording_engine.py` | 748 | C-36 recording engine — writes `rpi_orderbook`, `insurance_pool`, `premium_index_kline`, `option_tickers`, `adl_alerts` to `data/parquet/recording_f0/` | `recorder/__main__.py`; tests: `test_recorder_engine.py` | **LIVE-INFRA** — running continuously since ~2026-06-11, must never stop |
| `storage.py` | 509 | Parquet storage layer, ring-buffer cap | `recording_engine.py`; `test_recorder_storage.py` | **LIVE-INFRA** |
| `sunset.py` | 201 | Sunset-review clock/logic for the recorder | `recorder/__main__.py`; `test_recorder_sunset.py` | **LIVE-INFRA** |
| `__main__.py` | 150 | `python -m bybit_edge.recorder [--streams ...]` — the entry point `start_recorder.ps1` calls | invoked by `start_recorder.ps1` | **LIVE-INFRA** (top-level entry point) |
| `__init__.py` | 51 | Package exports | — | **LIVE-INFRA** |

### 2.4 `persistence/`

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `db.py` | 892 | DuckDB layer over `bybit_edge.duckdb` (hot+cold) | **Dual-use**: legacy (`live_runner.py`, `multi_runner.py`, `replay_all.py`, `replay_backtester.py`) **and** RESEARCH-V2 drivers (`research/c01_ofi_sign/driver.py`, `c07_pe/driver.py`, `c17_c41_lead_lag/driver.py`, `c31_cfar/driver.py`) which still read historical `trades`/`kline_1min` from the frozen duckdb file; `scripts/c42_repro.py`, `scripts/_profile_replay.py` | **SHARED / dual-status** — CLEANUP_PLAN verdict "REPLACE by Harvester (eventually)" but as of this survey still actively read by 4 KEEP research drivers; not yet migrated |
| `backfill.py` | 486 | REST kline backfill into `bybit_edge.duckdb` | Only `scripts/backfill.py` + its own test | **LEGACY-V1** — CLEANUP_PLAN verdict "REPLACE by Harvester" |

### 2.5 `execution/` and `risk/` — LEGACY-V1, marked REMOVE in CLEANUP_PLAN

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `execution/bybit_executor.py` | 281 | REST order-routing (would place live orders) | `monitor.py`, `live_runner.py`, `dashboard/data.py`, `dashboard/app.py`; `test_execution_live.py` | **LEGACY-V1** — project charter (`scinance2-impl/CLAUDE.md`) explicitly forbids building live-order code; this module predates that rule and is inert |
| `risk/budget.py` | 379 | Daily loss-cap for live execution | `live_runner.py`; `test_risk_budget.py`, `test_execution_live.py` | **LEGACY-V1** |

### 2.6 `dashboard/` — LEGACY-V1

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `app.py` | 685 | Streamlit frontend for the live pipeline | `scripts/dashboard.py`; `test_dashboard.py` | **LEGACY-V1** — data source (`bybit_edge.duckdb` live write path) is being retired |
| `data.py` | 800 | Data-loading layer for the dashboard | `dashboard/app.py`; `test_dashboard.py` | **LEGACY-V1** |

### 2.7 `backtester/` — LEGACY-V1

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `engine.py` | 394 | Classic bar-based backtester for S1-S5 | `scripts/backtest.py`; `test_backtest_driver.py`, `test_infrastructure.py`, `test_replay_backtester.py`, `test_tuning.py`, `test_replay_all.py` | **LEGACY-V1** |

### 2.8 `training/` and `tuning/` — LEGACY-V1

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `training/dataset.py` | 301 | Training-dataset builder for L4-pattern models (PatchTST/TimesNet/Moment) | `scripts/train_models.py`; `test_training.py` | **LEGACY-V1** |
| `tuning/optuna_tuner.py`, `spaces.py`, `params.py` | 182/157/175 | Optuna hyperparameter tuning for strategies S1-S5 | `scripts/tune.py`, `replay_backtester.py`, `strategy3_pre_settlement.py`; `test_tuning.py` | **LEGACY-V1** |

### 2.9 `strategies/` — LEGACY-V1, all 5 empirically DROP'd per `WAVE1_FINAL_REPORT.md`

| Module | LoC | Purpose | Imported by | Class |
|---|---|---|---|---|
| `strategy1_cascade.py` | 417 | S1 cascade strategy | `pipeline.py`; `test_strategies.py`, `test_strategy1_rho_instrument.py` | **LEGACY-V1** |
| `strategy2_entropy_momentum.py` | 339 | S2 entropy-momentum | `pipeline.py`; `test_strategies.py`, `test_strategy_direction_inversion.py` | **LEGACY-V1** |
| `strategy3_pre_settlement.py` | 453 | S3 pre-settlement (also imports `tuning`) | `pipeline.py`; `test_strategy3.py`, `test_strategy3_bounded_exits.py` | **LEGACY-V1** |
| `strategy4_pattern_ensemble.py` | 359 | S4 pattern ensemble (consumes L4 layer outputs) | `pipeline.py`; `test_strategies.py` | **LEGACY-V1** |
| `strategy5_cross_sectional.py` | 316 | S5 cross-sectional | `pipeline.py`; `test_strategies.py` | **LEGACY-V1** |

### 2.10 `layers/` — LEGACY-V1, all 26 modules (L1-L5), the literal README pipeline

Only strategies S1-S5 (all DROP'd) consumed these. All are imported exclusively from
`strategies/*.py`, `pipeline.py`, and their own `tests/unit/test_m*.py`; two exceptions
noted below are used by legacy *scripts*, not by any v2 driver.

| Layer | Modules (LoC) | Class |
|---|---|---|
| L1 Ingestion | `m1_spikewavformer.py` (480, also `scripts/train_models.py`), `m2_ofi.py` (189), `m3_iceberg.py` (204) | **LEGACY-V1** |
| L2 Denoising | `m4_wavelet.py` (255), `m5_ffd.py` (233) | **LEGACY-V1** |
| L3 Regime | `m6_entropy.py` (153), `m7_permutation_entropy.py` (184), `m8_bocpd.py` (293 — has a known unfixed shape-mismatch bug, deliberately not fixed per DEC-14), `m9_hmm.py` (370), `m10_mfdfa.py` (228), `m11_tda.py` (231), `m12_rqa.py` (320), `m13_cross_sectional_z.py` (180) | **LEGACY-V1** |
| L4 Pattern | `m14_hawkes.py` (281), `m15_gr_omori.py` (460), `m16_tfsax_sw.py` (338), `m17_renyi_te.py` (331), `m18_patchtst.py` (522, lazy `import torch`), `m19_timesnet.py` (442, torch), `m20_moment.py` (307, also `scripts/train_models.py`), `m21_ls_ratio.py` (119) | **LEGACY-V1** |
| L5 Risk | `m22_funding_pressure.py` (182), `m23_basis_convergence.py` (104), `m24_kalman_premium.py` (233), `m25_kyle_lambda.py` (177), `m26_sir.py` (312) | **LEGACY-V1** |

`state/{trade_buffer,orderbook_state,ticker_state,liquidation_buffer}.py` (81-203 LoC each)
are the online aggregators feeding `pipeline.py`/`live_runner.py` — also **LEGACY-V1**
(imported only from the live chain and their own `test_*` files).

### 2.11 `research/` — RESEARCH-V2 (every subpackage confirmed live by a driver script)

Every listed subpackage below is imported by exactly one `scripts/c*.py` or
`scripts/wp*.py` driver (full mapping in §3), which is in turn invoked by a
`scinance2-impl/handoff_local/run_*.ps1` script. All are **RESEARCH-V2**.

| Subpackage | Total LoC | Driver script | Empirical verdict (from state docs, informational only) |
|---|---|---|---|
| `bar_cache.py` (496, top-level, not a subpkg) | 496 | `scripts/build_bar_cache.py`; also imported by `c19_drift`,`c20_tail`,`c22_l2tilt`,`c24_impact` drivers | Shared infra for wave 4+ (WP-0) |
| `payload_sql.py` (195, top-level) | 195 | Shared SQL-dialect resolver, imported by 10+ research drivers (`c09_bunch`,`c15_grammar`,`c12_frag`,`c16_arrow`,`c14_panellag`,`c01_ofi_sign/oos.py`,`c17_venue`,`c13_tailshape`,`c10_pointer`,`c11_anen`) | Shared v2 payload-dialect infra |
| `c01_ofi_sign/` | 1058 | `scripts/c01_ofi_sign.py`, `c01_ofi_sign_oos.py`, `c01_ofi_tradability.py` | H-05 DROP; H-05b OOS WEITER (SOL δ1s/δ5s) |
| `c01_ofi_tradability/` | 692 | `scripts/c01_ofi_tradability.py` | H-05c tradability PARK |
| `c06_xmr/` | 1079 | `scripts/c06_xmr.py` | wave-4+ pilot |
| `c07_pe/` | 1389 | `scripts/c07_pe.py` | H-06 DROP |
| `c09_bunch/` | 1232 | `scripts/c09_bunch.py` | wave-4 |
| `c10_pointer/` | 1341 | `scripts/c10_pointer.py` | wave-4 |
| `c11_anen/` | 2312 | `scripts/c11_anen.py`, `c11c_dressed.py` | H-11/H-11c |
| `c12_frag/` | 1041 | `scripts/c12_frag.py` | wave-4 |
| `c13_tailshape/` | 1889 | `scripts/c13_tailshape.py` | options-tail work |
| `c14_panellag/` | 2213 | `scripts/c14_panellag.py` | wave-5/6 |
| `c15_grammar/` | 2833 | `scripts/c15_grammar.py` (largest driver.py in repo, 1488 LoC) | wave-6 |
| `c16_arrow/` | 2436 | `scripts/c16_arrow.py` | wave-6 |
| `c17_c41_lead_lag/` | 1252 | `scripts/c17_c41_lead_lag.py`, `c18_leadlag_audit.py` | H-04 WEITER (capital-free) |
| `c17_c41_tradability/` | 1120 | `scripts/c17_c41_tradability.py` | H-04b PARK |
| `c17_venue/` | 2724 | `scripts/c17_venue.py` (driver.py alone 1203 LoC) | wave-7 |
| `c18_leadlag_audit/` | 1723 | `scripts/c18_leadlag_audit.py` | audit wave |
| `c19_drift/` | 487 | `scripts/c19_drift.py` | H-19 |
| `c20_tail/` | 465 | `scripts/c20_tail.py` | H-20 |
| `c22_l2tilt/` | 878 | `scripts/c22_l2tilt.py`, also `wp2_l2_extract.py`, `wp4_spread_census.py` | H-22 + WP-1/WP-4 |
| `c24_impact/` | 509 | `scripts/c24_impact.py` | H-24 |
| `c31_cfar/` | 1482 | `scripts/c31_cfar.py` | H-03 DROP |
| `c42_rv/` | 1196 | `scripts/c42_repro.py` | H-02 DROP |
| `e15_eval/` | 731 | `scripts/evaluate_e15.py` | H-01/wave-1 eval stack |
| `wp5_optchain/` | 250 | `scripts/wp5_option_chain_census.py`, `wp5_snap_timeseries.py`, `wp6_optstress_census.py` | WP-5 options census (Aug 2026) |
| `wp6_optstress/` | 163 | `scripts/wp6_optstress_census.py` | WP-6 stress census (Aug 2026, newest wave) |

---

## 3. `scripts/` — every script

| Script | LoC | Purpose | Calls (src modules) | Era |
|---|---|---|---|---|
| `c01_ofi_sign.py` | 158 | Driver wrapper, H-05 OFI sign | `research.c01_ofi_sign` | v2 wave 2 |
| `c01_ofi_sign_oos.py` | 148 | OOS confirmatory run, H-05b | `research.c01_ofi_sign` | v2 wave 3 |
| `c01_ofi_tradability.py` | 99 | Tradability gate H-05c | `research.c01_ofi_sign`, `.c01_ofi_tradability` | v2 wave 3 |
| `c06_xmr.py` | 151 | Driver H-07/H-08 (cross-sectional z) | `research.c06_xmr` | v2 wave 3 |
| `c07_pe.py` | 168 | Driver H-06 permutation entropy | `research.c07_pe` | v2 wave 2 |
| `c09_bunch.py` | 151 | Driver, bunching estimator | `research.c09_bunch` | v2 wave 4 |
| `c10_pointer.py` | 196 | Driver, pointer/cropper analysis | `research.c10_pointer` | v2 wave 4 |
| `c11_anen.py` | 173 | Driver H-11 analog ensemble | `research.c11_anen` | v2 wave 4/5 |
| `c11c_dressed.py` | 144 | Driver H-11c dressed-analog variant | `research.c11_anen` | v2 wave 5 |
| `c12_frag.py` | 139 | Driver H-12 fragmentation | `research.c12_frag` | v2 wave 4 |
| `c13_tailshape.py` | 133 | Driver, options tail-shape/SVI | `research.c13_tailshape` | v2 |
| `c14_panellag.py` | 269 | Driver H-14 panel-lag encoder | `research.c14_panellag` | v2 wave 5/6 |
| `c15_grammar.py` | 266 | Driver H-15 grammar/transformer model | `research.c15_grammar` | v2 wave 6 |
| `c16_arrow.py` | 198 | Driver H-16 CNN/scalogram | `research.c16_arrow` | v2 wave 6 |
| `c17_c41_lead_lag.py` | 162 | Driver H-04 lead-lag | `research.c17_c41_lead_lag` | v2 wave 2 |
| `c17_c41_tradability.py` | 197 | Driver H-04b tradability | `research.c17_c41_tradability` | v2 wave 2 |
| `c17_venue.py` | 314 | Driver H-17/venue redundancy | `research.c17_venue` | v2 wave 7 |
| `c18_leadlag_audit.py` | 242 | Audit driver, GPU-batched TE/wcoh | `research.c17_c41_lead_lag`, `.c18_leadlag_audit` | v2 |
| `c19_drift.py` | 87 | Driver H-19 drift | `research.bar_cache`, `.c19_drift` | v2 wave 8 |
| `c20_tail.py` | 85 | Driver H-20 tail | `research.bar_cache`, `.c20_tail` | v2 wave 8 |
| `c22_l2tilt.py` | 80 | Driver H-22 L2 tilt | `research.bar_cache`, `.c22_l2tilt` | v2 wave 8 |
| `c24_impact.py` | 88 | Driver H-24 impact | `research.bar_cache`, `.c24_impact` | v2 wave 8 |
| `c31_cfar.py` | 118 | Driver H-03 CFAR | `research.c31_cfar` | v2 wave 1 |
| `c42_repro.py` | 270 | Driver H-02 vol-RV repro | `research.c42_rv`, `persistence.db` | v2 wave 1 |
| `evaluate_e15.py` | 139 | E-15 evaluation report | `research.e15_eval` | v2 wave 1 |
| `wp2_l2_extract.py` | 106 | WP-2 L2 extraction | `research.c22_l2tilt` (extract module) | v2 (Aug 2026) |
| `wp4_spread_census.py` | 127 | WP-4 spread census | `research.c22_l2tilt` | v2 (Aug 2026) |
| `wp5_option_chain_census.py` | 78 | WP-5 options chain census | `research.wp5_optchain` | v2 (Aug 2026) |
| `wp5_snap_timeseries.py` | 157 | WP-5 timeseries of option snapshots | `research.wp5_optchain` | v2 (Aug 2026) |
| `wp6_optstress_census.py` | 210 | WP-6 stress-window census | `research.wp5_optchain`, `.wp6_optstress` | v2 (Aug 2026, newest) |
| `l2_census.py` | 233 | L2 census tool, self-contained (no `bybit_edge` src import — reads harvest tree directly) | none | v2 (Aug 2026, standalone tool) |
| `build_bar_cache.py` | 114 | Builds the bar cache from harvest data | `research.bar_cache` | v2 WP-0 |
| `backtest.py` | 315 | Legacy strategy comparison S1-S5 over history | `backtester.engine`, `config`, `layers.l3_regime.m7_permutation_entropy` | **v1, DEPRECATE** |
| `backfill.py` | 185 | REST kline backfill into `bybit_edge.duckdb` | `config`, `persistence.backfill` | **v1, REPLACE (Harvester)** |
| `dashboard.py` | 57 | Streamlit launcher subprocess wrapper | none directly (`subprocess`→`dashboard/app.py`) | **v1, DEPRECATE** |
| `train_models.py` | 310 | Training pipeline for L4-pattern models | `config`, `layers.l1_ingestion.m1_spikewavformer`, `layers.l4_pattern.{m18,m19,m20}`, `training.dataset` | **v1, DEPRECATE** |
| `tune.py` | 221 | Optuna hyper-tuning for S1-S5 | `config`, `replay_backtester`, `tuning.optuna_tuner`, `tuning.spaces` | **v1, DEPRECATE** |
| `replay_all.py` | 1044 | Full-replay loop, all strategies (forensic, iter-5 run) | `duckdb` directly, no `bybit_edge` src import found in top-level scan (self-contained) | **v1/tool, DEPRECATE** |
| `replay_backtest.py` | 475 | Thinner replay CLI | `config`, `replay_backtester` | **v1/tool, DEPRECATE** |
| `_profile_replay.py` | 206 | cProfile wrapper around replay | `persistence.db`, `replay_backtester`, `state.liquidation_buffer`, `state.ticker_state`, `state.trade_buffer` | **v1/tool, DEPRECATE** |
| `setup_local.sh` | (shell) | Onboarding script — clones repo, builds conda env, runs tests, prints "Collector starten: `python -m bybit_edge`" and references a **nonexistent** `scripts/run_backtest.py` | n/a | **stale v1 onboarding doc**, out of date vs. current `start.bat` |

---

## 4. `tests/` — grouped

`tests/unit/` = 83 files (80 with `test_*.py` matching glob at repo root count of 80 —
`conftest.py` and `__init__.py` are the other two). `tests/integration/` and
`tests/backtests/` contain only `__init__.py` stubs (no tests). `tests/fixtures/`
holds only data (c42, e15/{weiter,grau,drop}).

| Group | Files (count) | Would break if LEGACY-V1 modules moved to archive? |
|---|---|---|
| Forensic protected-asset tests | `test_replay_backtester_maker_only.py`, `test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`, `test_strategy1_rho_instrument.py` (4) | **YES** — import `strategies.*`, `replay_backtester`; explicitly "keep untouched" per project charter, but they DO import legacy modules, so an archive move needs `sys.path`/import-path fixups, not deletion |
| RESEARCH-V2 wave 2 (`c01/c07/c17_c41`) | `test_c01_ofi_sign.py`, `test_c01_oos.py`, `test_c01_ofi_tradability.py`, `test_c07_pe.py`, `test_c17_c41_lead_lag.py`, `test_c17_c41_tradability.py`, `test_aggregate_wave2_fdr.py` (7) | No |
| RESEARCH-V2 wave 1 (`c31/c42/e15`) | `test_c31_cfar.py`, `test_c42_rv.py`, `test_e15_eval.py` (3) | No — but `test_c31_cfar.py` imports `persistence.db` (shared, not legacy-exclusive) |
| RESEARCH-V2 waves 4-8 | `test_c06_xmr.py`, `test_c09_bunch.py`, `test_c10_pointer.py`, `test_c11_anen.py`, `test_c11c_dressed.py`, `test_c12_frag.py`, `test_c13_tailshape.py`, `test_c14_panellag.py`, `test_c15_grammar.py`, `test_c16_arrow.py`, `test_c17_venue.py`, `test_c18_leadlag_audit.py`, `test_c19_drift.py`, `test_c20_tail.py`, `test_c22_driver.py`, `test_c22_extract.py`, `test_c24_impact.py`, `test_bar_cache.py`, `test_payload_dialects.py`, `test_wp5_optchain.py`, `test_wp6_optstress.py`, `test_aggregate_wave4_fdr.py` (22) | No |
| Recorder (Schutzgut #1) | `test_recorder_engine.py`, `test_recorder_storage.py`, `test_recorder_sunset.py` (3) | No |
| Replay-backtester tool tests | `test_replay_backtester.py`, `test_replay_all.py`, `test_replay_backtest_cli.py`, `test_backtest_driver.py` (4) | **YES** — test `replay_backtester.py`/`backtester.engine`/`replay_all.py` directly |
| Strategy behavior validation (S1-S5) | `test_strategies.py`, `test_strategy3.py` (2) | **YES** — import `strategies.*`, `decision_aggregator`, `pipeline` |
| Layer modules m1-m26 | `test_m1_spikewavformer.py` … `test_m26_sir.py` (26 files) | **YES** — each imports its corresponding `layers.*` module |
| Live-pipeline / infra stack | `test_pipeline.py`, `test_multi_runner.py`, `test_execution_live.py`, `test_risk_budget.py`, `test_training.py`, `test_tuning.py`, `test_dashboard.py`, `test_backfill.py` (8) | **YES** — import `pipeline`, `multi_runner`, `live_runner`, `execution.*`, `risk.budget`, `training.dataset`, `tuning.*`, `dashboard.*`, `persistence.backfill`, `collector.ws_collector` |
| Infrastructure (config/modes/endpoints) | `test_infrastructure.py` (1) | **YES** — imports `bybit_edge.scheduler`, `bybit_edge.backtester` alongside `config` (mixed: mostly config, partly legacy) |

**Full list of test files that import a LEGACY-V1 module** (would need import-path
handling if the corresponding `src/` module moves to an archive folder):
`test_m1_spikewavformer.py`, `test_m2_ofi.py`, `test_m3_iceberg.py`, `test_m4_wavelet.py`,
`test_m5_ffd.py`, `test_m6_entropy.py`, `test_m7_permutation_entropy.py`,
`test_m8_bocpd.py`, `test_m9_hmm.py`, `test_m10_mfdfa.py`, `test_m11_tda.py`,
`test_m12_rqa.py`, `test_m13_csz.py`, `test_m14_hawkes.py`, `test_m15_gr_omori.py`,
`test_m16_tfsax.py`, `test_m17_renyi_te.py`, `test_m18_patchtst.py`,
`test_m19_timesnet.py`, `test_m20_moment.py`, `test_m21_ls_ratio.py`,
`test_m22_funding_pressure.py`, `test_m23_basis.py`, `test_m24_kalman.py`,
`test_m25_kyle.py`, `test_m26_sir.py`, `test_strategies.py`, `test_strategy3.py`,
`test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`,
`test_strategy1_rho_instrument.py`, `test_pipeline.py`, `test_multi_runner.py`,
`test_execution_live.py`, `test_risk_budget.py`, `test_training.py`, `test_tuning.py`,
`test_dashboard.py`, `test_backfill.py`, `test_replay_backtester.py`,
`test_replay_backtester_maker_only.py`, `test_replay_all.py`,
`test_replay_backtest_cli.py`, `test_backtest_driver.py`, `test_infrastructure.py`
(**44 of 83 files**, roughly matching CLEANUP_PLAN's ~370-test DEPRECATE estimate,
though newer wave 4-8 tests were added after that plan's date and are unaffected).

---

## 5. Entry points referenced by local-machine automation

These paths are consumed by an external scheduler, a person's shortcut, or a `.ps1`/`.bat`
double-click flow. **Do not move/rename without leaving a stub or updating the caller.**

| Path | Referenced by | Note |
|---|---|---|
| `start_recorder.ps1` (repo root) | `start.bat` option 2 (`start "Scinance C-36 Recorder" powershell.exe ... -File "%~dp0start_recorder.ps1"`), `install_recorder_autostart.ps1` (Task Scheduler Action target) | **LIVE-INFRA critical path** — Windows Task Scheduler task "Scinance C-36 Recorder" invokes this by absolute path derived from `$PSScriptRoot`/repo root |
| `install_recorder_autostart.ps1`, `uninstall_recorder_autostart.ps1` | `start.bat` option 6 submenu | Registers/removes the Task Scheduler autostart entry |
| `scinance2-impl/handoff_local/run_wave2.ps1` | `start.bat` option 4 | Runs H-04+H-05+H-06 wave 2 |
| `scinance2-impl/handoff_local/check_recording.py` | `start.bat` option 3 | Recorder audit snapshot, read-only |
| `scinance2-impl/handoff_local/run_*.ps1` / `run_*.sh` (55 files: `run_cfar_only`, `run_h04b`, `run_h05b_oos`, `run_h05c`, `run_h07`…`run_h24`, `run_overnight`, `run_short`, `run_wave2`, `run_wave4`, `run_wave5`, `run_wp0_barcache`, `run_wp1_l2census`, `run_wp2_l2extract`, `run_wp4_spreadcensus`, `run_wp6_stresszensus`, `snap_bybit_optchain.ps1`, `ensure_harvest_junction.ps1`) | Person runs these directly on the Windows machine (T2/T3 tier of the test pyramid); not invoked by `start.bat` beyond the two named above, but are the actual overnight/long-running automation surface | Every one calls `python scripts\<driver>.py` with a relative path from repo root — **moving `scripts/*.py` breaks all of these** |
| `python -m bybit_edge.recorder` | `start_recorder.ps1` | Module invocation — moving/renaming `src/bybit_edge/recorder/` breaks this |
| `pyproject.toml` | no `[project.scripts]` entries exist — **no console-script entry points to worry about** | n/a |

None of the `.ps1`/`.bat` files reference `edge_research_framework/`, `edge-reconciliation/`,
`edge-research-v3/`, or `implementation_framework/` — those four directories are pure
Claude-agent documentation trees, safe to archive/move without any automation impact.

---

## 6. Dependency footprint

From `pyproject.toml` (`[project.dependencies]`): `websockets`, `aiohttp`, `duckdb`,
`polars`, `numpy`, `numba`, `scipy`, `statsmodels`, `pandas`, `python-dotenv`,
`structlog`, `sortedcontainers`, `pykalman`, `filterpy`, `hmmlearn`, `PyWavelets`.

Optional extras: `gpu` (torch/torchvision/torchaudio/snntorch — **only** L4-pattern
layer modules `m18_patchtst.py`/`m19_timesnet.py` lazy-`import torch` inside
try/except, no other module in the repo imports torch directly), `foundation`
(momentfm/transformers/peft — for `m20_moment.py`), `dev` (pytest/ruff/mypy),
`dashboard` (streamlit/plotly — LEGACY-V1 only), `tuning` (optuna — LEGACY-V1 only),
`vol` (lightgbm/scikit-learn — used by `research/c42_rv/models.py` (RESEARCH-V2) and
`tuning/*` (LEGACY-V1)).

| Dependency | Needed by |
|---|---|
| `duckdb` | `persistence/db.py` (shared), several research drivers reading `bybit_edge.duckdb`, `scripts/replay_all.py` — 20 files total |
| `polars` | 3 files (lighter footprint than expected given `polars>=0.20` is a hard dependency) |
| `torch` (extra) | ONLY `layers/l4_pattern/m18_patchtst.py`, `m19_timesnet.py` — both LEGACY-V1, guarded by try/except so absence doesn't break import |
| `lightgbm`/`optuna`/`scikit-learn` | `research/c42_rv/models.py` (RESEARCH-V2, live), `scripts/tune.py` + `tuning/*` (LEGACY-V1), `scripts/c42_repro.py` |
| `pykalman`/`filterpy`/`hmmlearn` | `layers/l5_risk/m24_kalman_premium.py`, `layers/l3_regime/m9_hmm.py` — LEGACY-V1 only |
| `streamlit`/`plotly` (extra) | `dashboard/*` — LEGACY-V1 only |
| GPU/CUDA (`environment.yml`) | Optional; `c18_leadlag_audit/surrogate_gpu.py`, `te_batched.py`, `wcoh_batched.py` are GPU-batched RESEARCH-V2 modules — the one place RESEARCH-V2 actually wants GPU |

---

## 7. Candidate archive set

Modules/directories that appear dead — no import from `persistence/db.py`-adjacent
live infra, no RESEARCH-V2 driver reference, no `scripts/wp*`/`scripts/c*` reference —
ranked by confidence.

| Candidate | Confidence | Evidence |
|---|---|---|
| `src/bybit_edge/layers/` (all 26 `m*.py`, ~6900 LoC) | **HIGH** | Only consumed by `strategies/*` (all DROP'd) and `scripts/backtest.py`/`train_models.py` (both themselves LEGACY-V1); no RESEARCH-V2 driver imports `bybit_edge.layers` anywhere (confirmed by full-repo grep) |
| `src/bybit_edge/strategies/` (5 files, ~1880 LoC) | **HIGH** | `WAVE1_FINAL_REPORT.md` explicitly states all 5 empirically DROP'd; only consumed by `pipeline.py`/`live_runner.py` chain, itself dead |
| `src/bybit_edge/live_runner.py`, `multi_runner.py`, `pipeline.py`, `decision_aggregator.py`, `__main__.py` | **HIGH** | `start.bat`'s live-pipeline menu option was already removed; no automation path reaches these; internal `CLEANUP_PLAN.md` verdict is DEPRECATE/none |
| `src/bybit_edge/monitor.py`, `scheduler.py` | **HIGH** | Zero or near-zero test coverage tied to real use (`monitor.py` has no test at all); only reachable via the dead live-pipeline chain |
| `src/bybit_edge/execution/bybit_executor.py`, `risk/budget.py` | **HIGH** | Project charter (`scinance2-impl/CLAUDE.md` §Autonomie-Protokoll) forbids live-order code outright; `CLEANUP_PLAN.md` verdict is explicit REMOVE |
| `src/bybit_edge/dashboard/` (app.py, data.py) | **HIGH** | Reads `bybit_edge.duckdb` live-write path that is being retired; `scripts/dashboard.py` is its only caller and is itself dead |
| `src/bybit_edge/backtester/engine.py` | **HIGH** | Only `scripts/backtest.py` (dead) and its own tests |
| `src/bybit_edge/training/dataset.py`, `tuning/*` | **HIGH** | Only `scripts/train_models.py`/`scripts/tune.py` (both dead), and `strategy3_pre_settlement.py`/`replay_backtester.py` (forensic-only) |
| `src/bybit_edge/collector/ws_collector.py` | **MED** | Superseded operationally by recorder+harvester per `CLEANUP_PLAN.md`, but still imported transitively by `live_runner.py`/`dashboard/*`/tests — archiving needs to happen alongside those, not alone |
| `src/bybit_edge/persistence/backfill.py` | **MED** | Only `scripts/backfill.py` (dead, "REPLACE by Harvester" per plan); `persistence/db.py` itself is NOT a candidate (still read by 4 live research drivers) |
| `scripts/backtest.py`, `train_models.py`, `tune.py`, `dashboard.py`, `backfill.py`, `replay_all.py`, `replay_backtest.py`, `_profile_replay.py` | **HIGH** | Not referenced by any `run_*.ps1`/`.sh` in `scinance2-impl/handoff_local/`, not referenced by current `start.bat` |
| `scripts/setup_local.sh` | **MED** | References a `scripts/run_backtest.py` that does not exist in the repo — itself stale; not called by any `.ps1` automation |
| `src/bybit_edge/replay_backtester.py`, `replay_all.py`, and the 4 forensic test files | **LOW** (i.e. do NOT archive without explicit sign-off) | Explicitly retained as forensic/audit tooling protecting prior empirical verdicts (`WAVE1_FINAL_REPORT.md` §5, project charter "Schutzgüter") even though nothing currently *runs* them operationally |
| `edge_research_framework/`, `edge-reconciliation/`, `edge-research-v3/`, `implementation_framework/` | **HIGH** (docs, not code) | Zero `.py` files; zero references from any `.ps1`/`.bat`/`pyproject.toml`; pure historical multi-agent-session artifacts that produced `FINAL_PRD.md` — safe to archive as documentation, not code |

**Not a candidate** (despite superficially looking legacy): `src/bybit_edge/persistence/db.py`
— still actively read by 4 KEEP RESEARCH-V2 drivers (`c01_ofi_sign`, `c07_pe`,
`c17_c41_lead_lag`, `c31_cfar`) for historical `trades`/`kline_1min` data. Migrating those
drivers off the frozen `bybit_edge.duckdb` onto the harvester path is a prerequisite
(tracked as unfinished TODO-8/TODO-14 in `CLEANUP_PLAN.md`) before this module can move.
