# Scinance 2.0 — Repo-Aufräumplan & Komponenten-Inventar

**Stand:** 2026-06-23
**Branch:** `scinance2-wave2` (Welle 2 inhaltlich DONE, Welle 3 noch nicht abgezweigt)
**Sprache:** Deutsch · alle Pfade absolut
**Grundannahme:** Ein paralleler Bybit-Datenharvester (separater Prozess, validiert mit 2.85M ETHUSDT-Trades, Schema-kompatibel, Side erhalten) liefert ab sofort die kompletten Bybit-Daten (publicTrade, orderbook L2, funding, OI, tickers, liquidations) plus Binance + Deribit-Options-IV. Einzige Bybit-Streams, die der Harvester (noch) NICHT abdeckt: `rpi_orderbook`, `insurance_pool`, `premium_index_kline`, `option_tickers`, `adl_alerts` — diese kommen weiter aus der C-36-Recording-Engine (`/home/user/scinance/src/bybit_edge/recorder/`).

**Schutzgut #1 (CLAUDE.md):** Die C-36-Recording-Engine darf nicht gestoppt werden. Sunset-Review-Uhr läuft seit ~2026-06-11; erster Review ca. 2026-09-11 (Quelle: `/home/user/scinance/scinance2-impl/state/wave3_survey.md` §3).

---

## 0. TL;DR-Tabelle (Welten-Karte)

Drei klar abgegrenzte Welten im selben Repo:

| Welt | Wurzel | LoC ca. | Zweck | Verdikt |
|---|---|---|---|---|
| Scinance 1.0 Legacy | `/home/user/scinance/src/bybit_edge/` (alles außer `recorder/` + `research/`) | ~13 300 LoC + ~14 000 LoC Layers + ~6 000 LoC Tests | Strategien S1-S5 + Layers L1-L5 + Live-Pipeline + Collector + Persistenz + Execution-Router | empirisch erledigt (Quelle: `/home/user/scinance/scinance2-impl/state/WAVE1_FINAL_REPORT.md` §4) |
| Scinance 2.0 Welle 1 | `/home/user/scinance/src/bybit_edge/recorder/`, `/home/user/scinance/src/bybit_edge/research/c31_cfar/`, `/home/user/scinance/src/bybit_edge/research/c42_rv/`, `/home/user/scinance/src/bybit_edge/research/e15_eval/` | ~5 000 LoC | C-36-Recording (LÄUFT), C-42-Repro DROP, C-31-CFAR DROP, E-15-Eval DROP | Welle 1 DONE — Recording bleibt LIVE, Code bleibt als Audit-Trail |
| Scinance 2.0 Welle 2 | `/home/user/scinance/src/bybit_edge/research/c01_ofi_sign/`, `/c07_pe/`, `/c17_c41_lead_lag/`, `/c17_c41_tradability/` + `/home/user/scinance/scinance2-impl/handoff_local/aggregate_wave2_fdr.py` | ~6 200 LoC | H-04 WEITER kapitalfrei, H-04b PARK, H-05 DROP, H-06 DROP | Welle 2 DONE; Module bleiben gate-neutral für H-05b-OOS und Welle-3-Pattern-Wiederverwendung |

---

## 1. Entry-Points — was startet was?

### 1.1 `/home/user/scinance/start.bat` — 8-Menü-Optionen

| Option | Befehl | Was passiert | Verdikt |
|---|---|---|---|
| 1 | `pytest tests/unit/ -v --tb=short` | Voll-Tests (in Sandbox aktuell 55 Collection-Fehler wg. fehlender Deps; Live-Maschine: 908 grün laut `/home/user/scinance/scinance2-impl/state/WAVE2_FINAL_REPORT.md` §7) | KEEP — schützt Forensik + Welle-1/2 |
| 2 | `python -m bybit_edge` | startet `bybit_edge/__main__.py` → `MultiSymbolRunner` (5 Symbole) bzw. `LiveRunner` — Collector + Pipeline + S1-S5 + optional Execution | **REPLACE durch Harvester + Recorder** |
| 3 | `python -m bybit_edge.monitor --interval 10` | Position/PnL/Equity-Anzeige (read-only, liest `bybit_edge.duckdb`) | DEPRECATE — nur sinnvoll mit Option 2 |
| 4 | `python scripts/backtest.py --symbol BTCUSDT --interval 5 --months 6` | Strategie-Vergleich auf Historie (S1-S5) | DEPRECATE — alle Strategien sind DROP |
| 5 | `python -c "from bybit_edge.pipeline import Pipeline; ..."` | Import-Smoke der Live-Pipeline | DEPRECATE — folgt Option 2 |
| 6 | `python` (REPL) | interaktive Shell | KEEP — generisch nützlich |
| 7 | `python scripts/dashboard.py` | Streamlit-Dashboard (liest `bybit_edge.duckdb`) | DEPRECATE — Datenquelle (`bybit_edge.duckdb`) wird gestoppt |
| 8 | exit | — | KEEP |

**Befund:** 5 von 8 Optionen (2, 3, 4, 5, 7) hängen am Scinance-1.0-Live-Stack. Mit Harvester-Übergang verlieren sie ihren Zweck. Empfehlung: `start.bat` durch eine 3-Menü-Version ersetzen (Tests / Recorder-Status / Wave-Runner) — siehe TODO-7.

### 1.2 `/home/user/scinance/src/bybit_edge/__main__.py`

Schaltet zwischen `MultiSymbolRunner` (Standard, 5 Symbole) und `LiveRunner` (Single-Symbol). Beide ziehen:
- `/home/user/scinance/src/bybit_edge/multi_runner.py` (154 LoC)
- `/home/user/scinance/src/bybit_edge/live_runner.py` (830 LoC)
- `/home/user/scinance/src/bybit_edge/collector/ws_collector.py` (321 LoC)
- `/home/user/scinance/src/bybit_edge/persistence/db.py` (824 LoC) — öffnet `data/bybit_edge.duckdb`
- `/home/user/scinance/src/bybit_edge/pipeline.py` (319 LoC) → `decision_aggregator.py` (154 LoC) → `strategies/*` (5 Stück, ~1 700 LoC zusammen)
- optional `/home/user/scinance/src/bybit_edge/execution/bybit_executor.py` (275 LoC)
- alle 5 State-Engines aus `/home/user/scinance/src/bybit_edge/state/` (511 LoC)
- alle 26 Layer-Module aus `/home/user/scinance/src/bybit_edge/layers/`

Output: `data/bybit_edge.duckdb` (tickers, trades, liquidations, kline_1min) + heartbeat-Files + Dashboard-Snapshots.

### 1.3 `/home/user/scinance/src/bybit_edge/recorder/__main__.py` — C-36 Recording

`python -m bybit_edge.recorder [--streams ...] [--cap-gb 50] [--duration N]`. Schreibt nach `data/parquet/recording_f0/`. Streams: `rpi_orderbook`, `insurance_pool`, `adl_alerts` (phantom seit DEC-08), `premium_index_kline`, `option_tickers` (NO_DATA seit GL-004). Output: Audit-Trail laufend seit ~2026-06-11 (Quelle: `/home/user/scinance/scinance2-impl/state/WAVE1_FINAL_REPORT.md` §3). **Darf nicht gestoppt werden.**

### 1.4 `/home/user/scinance/scripts/*.py` — Welle-1/2-Driver-Scripts + Legacy

| Script | LoC | Zweck | Welt | Verdikt |
|---|---|---|---|---|
| `/home/user/scinance/scripts/c01_ofi_sign.py` | 158 | Driver-Wrapper Welle 2 H-05 | Welle 2 | KEEP (wird für H-05b-OOS-Lauf gebraucht) |
| `/home/user/scinance/scripts/c07_pe.py` | 168 | Driver-Wrapper Welle 2 H-06 | Welle 2 | KEEP (Audit) |
| `/home/user/scinance/scripts/c17_c41_lead_lag.py` | 162 | Driver Welle 2 H-04 | Welle 2 | KEEP (Audit) |
| `/home/user/scinance/scripts/c17_c41_tradability.py` | 197 | Driver Welle 2 H-04b | Welle 2 | KEEP (Pattern-Quelle für Welle 3) |
| `/home/user/scinance/scripts/c31_cfar.py` | 118 | Driver Welle 1 H-03 | Welle 1 | KEEP (Audit) |
| `/home/user/scinance/scripts/c42_repro.py` | 270 | Driver Welle 1 H-02 | Welle 1 | KEEP (Audit) |
| `/home/user/scinance/scripts/evaluate_e15.py` | 139 | Driver Welle 1 E-15-Eval | Welle 1 | KEEP (Audit) |
| `/home/user/scinance/scripts/backtest.py` | 315 | Legacy-Backtest S1-S5 | 1.0 | DEPRECATE |
| `/home/user/scinance/scripts/backfill.py` | 158 | REST-Kline-Backfill in `bybit_edge.duckdb` | 1.0 | REPLACE (Harvester macht das) |
| `/home/user/scinance/scripts/dashboard.py` | 57 | Streamlit-Launcher | 1.0 | DEPRECATE |
| `/home/user/scinance/scripts/train_models.py` | 310 | Trainings-Pipeline für L4-Pattern-Modelle (PatchTST/TimesNet/Moment) | 1.0 | DEPRECATE |
| `/home/user/scinance/scripts/tune.py` | 221 | Optuna-Hyper-Tuning für S1-S5 | 1.0 | DEPRECATE |
| `/home/user/scinance/scripts/replay_all.py` | 1 044 | Voll-Replay aller Strategien (Welle-1-Forensik-Werkzeug, iter-5-Lauf) | 1.0/Werkzeug | DEPRECATE (Audit-Trail reicht; Forensik-Tests bleiben separat) |
| `/home/user/scinance/scripts/replay_backtest.py` | 475 | Replay-CLI dünnerer Variante | 1.0/Werkzeug | DEPRECATE |
| `/home/user/scinance/scripts/_profile_replay.py` | 206 | Profiler für Replay | Werkzeug | DEPRECATE |

### 1.5 `/home/user/scinance/scinance2-impl/handoff_local/*` — T2/T3-Runner

| Datei | Zweck | Verdikt |
|---|---|---|
| `run_overnight.{sh,ps1}` | Welle-1-Overnight (E-15+C-42+C-31+Recorder-Dauerlauf) | KEEP (Audit + Pattern) |
| `run_short.{sh,ps1}` | T2-Smoke (Collector 5 min + Mini-Replay + C-42 Quick) | DEPRECATE — Collector-Anteil obsolet |
| `run_cfar_only.{sh,ps1}` | C-31-CFAR-Standalone-Lauf | KEEP (Audit) |
| `run_wave2.{ps1,sh}` | Welle-2-Voll-Lauf (c01+c07+c17 lead-lag + Aggregator) | KEEP — Vorlage für H-05b-OOS |
| `run_h04b.{ps1,sh}` | H-04b-Tradability-Lauf | KEEP (Audit + Pattern) |
| `aggregate_wave2_fdr.py` | 551 LoC zweistufige F-WAVE2-FDR | KEEP — Wiederverwendung für Welle 3 |
| `aggregate_results.py` | 218 LoC Welle-1-Aggregator | KEEP (Audit) |
| `check_recording.py` | 164 LoC Recording-Audit-Snapshot | KEEP — Schutzgut-Werkzeug |

---

## 2. Datenpfade — wer schreibt, wer liest, was bleibt

| Pfad | Schreiber | Leser | Status |
|---|---|---|---|
| `/home/user/scinance/data/bybit_edge.duckdb` | `collector/ws_collector.py` via `persistence/db.py` (Live-Collector aus Option 2) | Welle-1/2-Driver-Scripts (read-only auf `trades`, `kline_1min`), Dashboard, Monitor, Replay | **wird mit Harvester-Übergang stillgelegt** — Audit-Trail einfrieren, nicht löschen (Forensik-Tests + Welle-1/2-Reproduzierbarkeit) |
| `/home/user/scinance/data/parquet/recording_f0/` | `recorder/recording_engine.py` (C-36 Schutzgut) | Welle-2-Driver-Scripts (lesend), künftige Welle-3-Pilots (C-29, C-27/C-28, C-39) | **LÄUFT WEITER, Schutzgut #1** |
| Harvester-Baum (separater Prozess, außerhalb dieses Repos) | externer Harvester | künftig: Welle-3-Driver-Scripts, Re-Runs von Welle-1/2-Drivern auf neuen OOS-Fenstern | **neue einzige Bybit-Daten-Quelle für die nicht-C-36-Streams** |
| `/home/user/scinance/scinance2-impl/handoff_local/results/` | T3-Runner | gate-auditor, Reports | committet (8 Lauf-Verzeichnisse seit 2026-06-11), KEEP |
| `/home/user/scinance/scinance2-impl/state/*.md` | Orchestrator + Subagenten | Mensch + zukünftige Agenten | KEEP |

---

## 3. Modul-Hierarchie — Komponenten-Inventar mit Verdikt

### 3.1 Scinance 1.0 Live-Pipeline — `/home/user/scinance/src/bybit_edge/`

| Komponente | Pfad | LoC | Welt | Was leistet sie noch? | Empfehlung | Risiko bei Stopp |
|---|---|---|---|---|---|---|
| Entry | `__main__.py` | 156 | 1.0 | startet Multi-/LiveRunner | DEPRECATE | keins (Welle-1/2-Driver laufen autonom) |
| LiveRunner | `live_runner.py` | 830 | 1.0 | Live-Schleife S1-S5 + Order-Eval + Persistenz-Flush | **DEPRECATE** | keins — alle Strategien sind DROP (WAVE1_FINAL_REPORT §4) |
| MultiRunner | `multi_runner.py` | 154 | 1.0 | 5-Symbol-Parallelisierung des LiveRunners | DEPRECATE | keins |
| Pipeline | `pipeline.py` | 319 | 1.0 | Glue State-Engines → Layer → Strategie → Decision | DEPRECATE | keins |
| DecisionAggregator | `decision_aggregator.py` | 154 | 1.0 | gewichtet S1-S5-Signale | DEPRECATE | keins |
| Collector | `collector/ws_collector.py` | 321 | 1.0 | Bybit-WS-Collector (tickers/publicTrade/orderbook/liquidations) | **REPLACE durch Harvester** | keins — Harvester deckt alles ab, was hier gesammelt wird |
| Persistenz | `persistence/db.py` | 824 | 1.0 | DuckDB-Layer hot+cold + Backfill | **REPLACE** (Audit-Trail einfrieren) | mittel — Welle-1/2-Driver lesen aktuell direkt von `bybit_edge.duckdb`; Driver auf Harvester-Pfad umstellen (siehe TODO-12) |
| Backfill | `persistence/backfill.py` | 471 | 1.0 | REST-Kline-Backfill | REPLACE (Harvester) | keins |
| Executor | `execution/bybit_executor.py` | 275 | 1.0 | REST-Order-Routing | **REMOVE** | keins — wir bauen explizit keinen Live-Handel (CLAUDE.md §4, PRD §6) |
| Monitor | `monitor.py` | 116 | 1.0 | TUI für PnL/Equity | DEPRECATE | keins |
| Scheduler | `scheduler.py` | 130 | 1.0 | Risiko-Reset-Uhr für Live | DEPRECATE | keins |
| Dashboard | `dashboard/app.py` (679) + `dashboard/data.py` (794) | 1473 | 1.0 | Streamlit-Frontend für Live-Pipeline | DEPRECATE | keins (Audit über `state/*.md` reicht) |
| Risiko-Budget | `risk/budget.py` | 373 | 1.0 | Tages-Loss-Cap für Live-Execution | REMOVE (mit Executor) | keins |
| State-Engines | `state/{trade_buffer, orderbook_state, ticker_state, liquidation_buffer}.py` | 511 | 1.0 | Online-Aggregatoren für Live-Pipeline | DEPRECATE | keins |
| Replay-Backtester | `replay_backtester.py` | 1 743 | 1.0/Werkzeug | Forensik-Werkzeug — geschützt durch `test_replay_backtester_maker_only.py` etc. | **KEEP als Forensik-Bestand** | hoch — Welle-1-Forensik-Reproduzierbarkeit hängt daran; Tests sind "unangetastet" laut WAVE1_FINAL_REPORT §5 |
| Replay-All | `replay_all.py` | 440 | 1.0/Werkzeug | Voll-Replay-Loop | DEPRECATE (Audit-Trail reicht) | gering |
| Backtester-Engine | `backtester/engine.py` | 388 | 1.0 | Klassischer Backtester | DEPRECATE | keins |
| Training | `training/dataset.py` | 295 | 1.0 | Trainings-Dataset-Builder für L4-Pattern | DEPRECATE | keins |
| Tuning | `tuning/{optuna_tuner,params,spaces}.py` | 496 | 1.0 | Hyper-Tuning S1-S5 | DEPRECATE | keins |

### 3.2 Scinance 1.0 Strategien — `/home/user/scinance/src/bybit_edge/strategies/`

| Datei | LoC | Empirisches Verdikt | Empfehlung |
|---|---|---|---|
| `strategy1_cascade.py` | 368 | C-14-REFUTED, E-01 ρ ≈ 2e-7 (Schwelle 0.85) — DROP (WAVE1_FINAL_REPORT §4) | DEPRECATE (Forensik-Test `test_strategy1_rho_instrument.py` 119 LoC bleibt) |
| `strategy2_entropy_momentum.py` | 302 | drei Forensiken (E-03/E-04/E-16) widerlegen Richtungsthese | DEPRECATE (Forensik-Test `test_strategy_direction_inversion.py` 271 LoC bleibt) |
| `strategy3_pre_settlement.py` | 432 | H-01 DROP nach bounded-loss iter-5, RAW-Edge auf 5/5 Symbolen negativ (GL-004) | DEPRECATE (Forensik-Test `test_strategy3_bounded_exits.py` 496 LoC bleibt) |
| `strategy4_pattern_ensemble.py` | 337 | E-13 Loader/Harness-Lücken, nie tragfähig | DEPRECATE |
| `strategy5_cross_sectional.py` | 294 | E-14 nie tragfähig | DEPRECATE |

**Befund:** Alle 5 Strategien sind empirisch erledigt. Die Forensik-Tests (3 Stück, ~886 LoC zusammen) sind das Schutzgut und bleiben in jeder Aufräumvariante unberührt.

### 3.3 Scinance 1.0 Layers (L1-L5, 26 Module) — `/home/user/scinance/src/bybit_edge/layers/`

| Layer | Module | LoC | Wem dient es? | Empfehlung |
|---|---|---|---|---|
| L1 Ingestion | `m1_spikewavformer.py` (480), `m2_ofi.py` (189), `m3_iceberg.py` (204) | 873 | S1-S5 (alle DROP) + Welle-2-Verweis: `m2_ofi.py` ist via DEC-11 in Welle 2 NICHT verwendet (eigener Aggressor-OFI in `research/c01_ofi_sign/`) | DEPRECATE |
| L2 Denoising | `m4_wavelet.py` (255), `m5_ffd.py` (233) | 488 | S1-S5 | DEPRECATE |
| L3 Regime | `m6_entropy.py` (153), `m7_permutation_entropy.py` (184), `m8_bocpd.py` (273), `m9_hmm.py` (339), `m10_mfdfa.py` (228), `m11_tda.py` (231), `m12_rqa.py` (293), `m13_cross_sectional_z.py` (180) | 1881 | S1-S5; m7 hat eigene Welle-2-Reimplementierung in `research/c07_pe/perm_entropy.py` | DEPRECATE — `m8_bocpd.py` siehe TODO-3 (Bug nicht fixen, wenn live_runner DEPRECATE) |
| L4 Pattern | `m14_hawkes.py` (281), `m15_gr_omori.py` (415), `m16_tfsax_sw.py` (338), `m17_renyi_te.py` (331), `m18_patchtst.py` (522), `m19_timesnet.py` (442), `m20_moment.py` (307), `m21_ls_ratio.py` (119) | 2755 | S4 (DROP). `m20_moment.py` wäre für künftiges C-20-MOMENT-Zero-Shot wiederverwendbar (Welle 3 evtl.) | DEPRECATE (m20: PARK statt DEPRECATE, falls Welle 3 H-08 nimmt) |
| L5 Risk | `m22_funding_pressure.py` (143), `m23_basis_convergence.py` (104), `m24_kalman_premium.py` (177), `m25_kyle_lambda.py` (177), `m26_sir.py` (286) | 887 | S3/S5 (DROP). `m25_kyle_lambda.py` ist Kandidat für C-25 — aber C-25 ist "zirkulär gated" (braucht positive Basis-Strategie, existiert nicht) | DEPRECATE |

**Gesamt Layer-LoC:** ~6 884 LoC für 26 Module, die alle für DROP'd Strategien gebaut wurden. Tests dazu: ~3 600 LoC in `tests/unit/test_m*.py`.

### 3.4 Scinance 2.0 Welle 1 — Recorder + Research

| Komponente | Pfad | LoC | Status | Empfehlung |
|---|---|---|---|---|
| Recording-Engine | `recorder/recording_engine.py` (709) + `recorder/storage.py` (358) + `recorder/sunset.py` (201) + `recorder/__main__.py` (150) + `recorder/__init__.py` (51) | 1 469 | LÄUFT (Schutzgut #1, ~7.4 Mio rpi_orderbook-Zeilen hochgerechnet 2026-06-18) | **KEEP — nie stoppen** |
| C-42 RV | `research/c42_rv/{features,metrics,models,pipeline,splits,target}.py` | 1 196 | H-02 DROP (GL-001, 5/5 Symbole, 0/36 FDR-Survivor) | KEEP (Audit + ggf. H-02b in fernerer Zukunft) |
| C-31 CFAR | `research/c31_cfar/{cfar_detector,cyclic_spectrum,driver,lead_edge,surrogate}.py` | 1 482 | H-03 DROP (GL-005, p ∈ [0.801; 1.000]) | KEEP (Audit) |
| E-15 Eval | `research/e15_eval/{e17,gate,metrics,report}.py` | 731 | Welle-1-Auswertungs-Stack | KEEP (Audit) |

### 3.5 Scinance 2.0 Welle 2 — Research-Module

| Komponente | Pfad | LoC | Status | Empfehlung |
|---|---|---|---|---|
| C-01 OFI Sign | `research/c01_ofi_sign/{driver,ofi,sign_test}.py` | 1 058 | H-05 DROP (GL-007); H-05b OOS-pending — Code steht | KEEP (H-05b-Lauf nutzt diesen Code unverändert; Quelle: `/home/user/scinance/scinance2-impl/state/wave3_survey.md` §2.1) |
| C-07 PE | `research/c07_pe/{driver,info_test,perm_entropy,pre_gate}.py` | 1 389 | H-06 DROP (GL-008) | KEEP (Audit + PE-Pattern für künftige Mess-Gates) |
| C-17/C-41 Lead-Lag | `research/c17_c41_lead_lag/{driver,surrogate,transfer_entropy}.py` | 1 252 | H-04 WEITER kapitalfrei (GL-006) | KEEP (Mess-Gate-Modul-Konvention, importbar) |
| C-17/C-41 Tradability | `research/c17_c41_tradability/{costs,driver,net_edge,trading_rule}.py` | 1 120 | H-04b PARK (GL-009) | KEEP (Tradability-Pattern + Anti-Gaming-Klausel `gate_valid_assumptions`) |
| Aggregator | `scinance2-impl/handoff_local/aggregate_wave2_fdr.py` | 551 | F-WAVE2 zweistufige BH-FDR | KEEP (Pattern für Welle 3) |

### 3.6 Tests — `/home/user/scinance/tests/unit/`

| Kategorie | Dateien | Test-Anzahl (`def test_`) | LoC | Verdikt |
|---|---|---|---|---|
| Forensik-Schutzgut | `test_replay_backtester_maker_only.py`, `test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`, `test_strategy1_rho_instrument.py` | 4+12+6+4 = 26 | 996 | **KEEP unangetastet** (PRD §6 + WAVE1_FINAL_REPORT §5) |
| Welle 2 (research/c0x/c17) | `test_c01_ofi_sign.py`, `test_c07_pe.py`, `test_c17_c41_lead_lag.py`, `test_c17_c41_tradability.py`, `test_aggregate_wave2_fdr.py` | 25+31+22+19+19 = 116 | 3 090 | KEEP |
| Welle 1 (research/c31/c42/e15) | `test_c31_cfar.py`, `test_c42_rv.py`, `test_e15_eval.py` | 32+26+23 = 81 | 2 138 | KEEP |
| Recorder | `test_recorder_engine.py`, `test_recorder_storage.py`, `test_recorder_sunset.py` | 14+16+11 = 41 | 1 275 | KEEP — Schutzgut |
| Replay-Backtester | `test_replay_backtester.py`, `test_replay_all.py`, `test_replay_backtest_cli.py`, `test_backtest_driver.py` | 45+18+4+6 = 73 | 2 625 | KEEP für Forensik (Tests prüfen Replay-Engine, nicht Strategie-Code) |
| Strategien S1-S5 (Verhaltensvalidierung) | `test_strategies.py`, `test_strategy3.py` | 18+18 = 36 | 1 396 | DEPRECATE (Strategien sind DROP) — kann entfallen, wenn die Strategie-Module entfernt werden; aktuell empfohlen: belassen bis Strategie-Module entfernt |
| Layer-Module m1-m26 | `test_m1*.py` bis `test_m26*.py` | ~290 | ~3 950 | DEPRECATE im Tandem mit Layer-Modulen (siehe TODO-9) |
| Live-Pipeline | `test_pipeline.py`, `test_multi_runner.py`, `test_execution_live.py`, `test_risk_budget.py`, `test_training.py`, `test_tuning.py`, `test_dashboard.py`, `test_backfill.py` | 6+13+27+15+5+11+33+10 = 120 | 3 760 | DEPRECATE im Tandem mit Live-Stack |
| Infrastruktur | `test_infrastructure.py` | 52 | 942 | KEEP (Modi/Config/Endpunkte) |
| m8 BOCPD | `test_m8_bocpd.py` | 10 | 226 | DEPRECATE (zusammen mit `m8_bocpd.py`) |

**Total laut Grep:** 834 `def test_` über 56 Dateien. (Bestätigt: 908 grün laut WAVE2_FINAL_REPORT §7; in Sandbox aktuell nicht ausführbar wegen fehlender Deps.)

---

## 4. Live-Bug-Kontext und Behandlungs-Empfehlung

### 4.1 Symptom: `PersistenceLayer init failed: Zugriff verweigert` auf `data/bybit_edge.duckdb`

**Diagnose:** DuckDB-Datei-Lock — ein zweiter Prozess (mit hoher Wahrscheinlichkeit ein zombiehafter `live_runner`/`multi_runner` aus früherer Session, oder das Streamlit-Dashboard) hält die Datei offen. `persistence/db.py` öffnet via `duckdb.connect(DB_PATH, read_only=False)` — DuckDB serialisiert Schreib-Connections nur in-process. Cross-process steht eine OS-Datei-Sperre an, und wenn der zombie-Prozess die Datei noch hält, schlägt der Connect mit "Zugriff verweigert" fehl.

**Empfehlung:** **NICHT FIXEN** — der Bug verschwindet, sobald `live_runner` DEPRECATE und der Live-Collector gestoppt ist (siehe TODO-1, TODO-2). Bis dahin: Zombie-Prozess identifizieren und beenden (siehe TODO-1).

### 4.2 Symptom: `m8_bocpd.py` ValueError shapes (161586,) (161585,)

**Diagnose bestätigt:** `m8_bocpd.py` Zeile 183 setzt `self._R = new_R_unnorm / evidence` mit `n = len(self._R)+1`. Zeilen 189-192 allokieren `np.empty(n, ...)` — schlägt diese Allokation unter Memory-Druck fehl (n wächst unbegrenzt, kein Runlength-Cap), ist `_R` schon ge-updatet, `_mu/_kappa/_alpha/_beta` aber noch auf der alten Länge. Beim nächsten Call: Broadcast `(n,) vs (n-1,)` → ValueError. Selbst-verfestigend.

**Empfehlung:** **NICHT FIXEN, wenn live_runner DEPRECATE wird.** `m8_bocpd.py` ist Teil von L3 Regime und dient ausschließlich der Live-Pipeline → DROP'd Strategien. Wenn aus irgendeinem Grund ein minimaler Patch nötig ist (z.B. weil Welle 3 BOCPD wieder verwenden würde, was laut wave3_survey.md §1 NICHT vorgesehen ist — "C-08 BOCPD blockiert / tote Spur"), wäre die atomare Variante: (a) Runlength-Cap einführen (`MAX_RL = 10_000`, dann `_R = _R[:MAX_RL]`), (b) alle 5 State-Arrays in einem einzigen try/except gemeinsam neu allokieren und nur am Ende der Funktion atomar zuweisen.

---

## 5. KEEP / DEPRECATE / REMOVE / REPLACE — konsolidierte Übersicht

### Zählung
- **KEEP:** 19 Komponenten (Welle 1+2 Research + Recorder + Forensik-Tests + Welle-1/2-Driver-Scripts + Runner + Aggregator)
- **DEPRECATE:** 21 Komponenten (Live-Stack, Strategien S1-S5, Layers L1-L5, Backtester, Dashboard, Monitor, Training, Tuning, m-Tests)
- **REMOVE:** 2 Komponenten (`execution/bybit_executor.py`, `risk/budget.py` — niemals re-aktiviert, kein Live-Handel)
- **REPLACE:** 3 Komponenten (`collector/ws_collector.py`, `persistence/db.py`, `persistence/backfill.py` — durch Harvester; alte Variante bleibt als read-only Audit-Bestand bis Welle-1/2-Driver auf Harvester-Pfad umgestellt sind)

Klarstellung "DEPRECATE":
- Code bleibt im Repo (Audit-Trail).
- Code wird nicht mehr gestartet (entfernt aus `start.bat`, aus `__main__.py`-Default).
- Tests bleiben, solange das Modul referenziert wird; entfallen, wenn das Modul wirklich entfernt wird.
- Reversibel über `git revert` auf den Cleanup-Commit.

---

## 6. Priorisierte TODO-Liste

Reihenfolge-Logik:
- (A) Zuerst alles, was den Live-Bug-Druck nimmt, ohne Datenverlust-Risiko.
- (B) Dann Audit-Trail-Konservierung und Driver-Umstellung auf Harvester (sequenziell, Reihenfolge wichtig).
- (C) Erst dann Repo-Aufräumen (DEPRECATE-Markierungen, kosmetisch).
- (D) Welle-3-Vorbereitung am Ende.

**Akteur-Legende:** `[U]` = Nutzer auf Windows-Maschine; `[C]` = Claude-Orchestrator (kann remote tun); `[U+C]` = Hand-in-Hand.

### Sofort machbar — keine Harvester-Coverage nötig

**TODO-1 — [U] Zombie-Prozess finden, killen, DuckDB-Lock freigeben.**
- Was: PowerShell `Get-Process python | Where-Object {$_.CommandLine -like "*bybit_edge*"}`, danach `Stop-Process -Id <pid>` für alle zombies. Auch `streamlit` killen. Danach `del data\bybit_edge.duckdb.wal` falls vorhanden.
- Warum: Macht Option 2 wieder startbar; Voraussetzung für jeden weiteren Diagnostik-Schritt am Live-Stack (wenn überhaupt nötig).
- Risiko: keiner (Persistenz ist append-only, Recorder läuft eigene Datei `data/parquet/recording_f0/*`).
- Aufwand: 5 min.
- Reihenfolge: ZUERST (Voraussetzung für TODO-2).

**TODO-2 — [U] Live-Pipeline STOPPEN und nicht mehr starten.**
- Was: Option 2 in `start.bat` nicht mehr nutzen. Falls ein Live-Prozess noch läuft: Ctrl+C, dann TODO-1.
- Warum: Der Live-Stack (LiveRunner + S1-S5) hat keinen empirischen Zweck mehr (alle 5 Strategien sind DROP). Außerdem konkurriert sein DuckDB-Schreiben mit allem anderen.
- Risiko: keiner — der Recorder läuft separat und schreibt nach `data/parquet/recording_f0/`.
- Aufwand: 1 min (Entscheidung). Konsequente Durchsetzung: bis `start.bat` umgebaut ist (TODO-7).
- Reihenfolge: direkt nach TODO-1.

**TODO-3 — [C] Entscheidung dokumentieren: `m8_bocpd.py` NICHT fixen.**
- Was: Eintrag in `state/decisions.md` als DEC-14: "BOCPD-Live-Bug bleibt unfixed, Modul folgt der LiveRunner-DEPRECATE-Entscheidung."
- Warum: Verhindert dass künftige Agenten in den BOCPD-Patch laufen; macht den Aufräum-Pfad explizit.
- Risiko: minimal (reversibel über neuen DEC-Eintrag).
- Aufwand: 10 min.
- Reihenfolge: zusammen mit TODO-2.

**TODO-4 — [C] Schutzgut-Check: bestätigen dass der Recorder noch läuft.**
- Was: Run `python scinance2-impl/handoff_local/check_recording.py`, schreibt aktuelles `recording_check.json` mit row-counts und Schema-Drift-Bericht.
- Warum: Vor jedem weiteren Aufräum-Schritt muss bestätigt sein, dass Schutzgut #1 lebt.
- Risiko: nur read-only.
- Aufwand: 2 min.
- Reihenfolge: vor TODO-5.

**TODO-5 — [C] CLEANUP_PLAN.md committen.**
- Was: diese Datei + DEC-14 + state.md-Eintrag committen auf `scinance2-wave2` (oder neuem Branch `repo-cleanup`).
- Warum: Festschreiben der Aufräum-Konvention, bevor wir Code anfassen.
- Risiko: keiner.
- Aufwand: 5 min.
- Reihenfolge: nach TODO-4.

### Audit-Trail einfrieren — keine Harvester-Coverage nötig

**TODO-6 — [U+C] DuckDB-Datei einfrieren als Audit-Bestand.**
- Was: nachdem TODO-2 sichergestellt hat, dass nichts mehr schreibt: Kopie `data/bybit_edge.duckdb` → `data/audit/bybit_edge_frozen_20260623.duckdb` mit Hash-Datei `.sha256` daneben. Die Original-Datei umbenennen in `bybit_edge.duckdb.frozen` (oder read-only chmod), damit kein Driver mehr versehentlich schreibt.
- Warum: Die Welle-1/2-Gate-Verdikte basieren auf dem aktuellen Inhalt (z.B. GL-006/007/008 auf `trades` + `kline_1min`). Falls je einer der Audits reproduziert werden muss, ist diese Datei der Beweis.
- Risiko: keiner (Kopie, nichts gelöscht).
- Aufwand: 15 min.
- Reihenfolge: nach TODO-2 und TODO-4.

**TODO-7 — [C] `start.bat` auf 3-Menü-Version umbauen.**
- Was: neue Optionen — (1) Tests, (2) Recorder-Status (`check_recording.py`), (3) Wave-Lauf (`run_wave2.ps1` mit Parameter-Abfrage). Optionen 2-5 + 7 entfernen.
- Warum: macht die Live-Pipeline mechanisch unzugänglich → kein versehentliches Wiederanstarten von LiveRunner.
- Risiko: gering (alte Version bleibt im git-history).
- Aufwand: 30 min.
- Reihenfolge: parallel zu TODO-6.

### Welle-3-Vorbereitung — braucht Harvester-Coverage

**TODO-8 — [C] Schreibweise der Welle-1/2-Driver auf Harvester-Datenpfad analysieren.**
- Was: Bestandsaufnahme: Welche der KEEP-Driver (c01/c07/c17/c31/c42/e15) lesen aktuell direkt aus `data/bybit_edge.duckdb`? Welche aus Parquet? Pro Driver: Quellzeilen identifizieren, Harvester-Pfad-Mapping skizzieren.
- Warum: Voraussetzung für H-05b-OOS-Lauf — der braucht Harvester-Daten aus dem OOS-Fenster.
- Risiko: nur Analyse, kein Code-Touch.
- Aufwand: 1-2 h.
- Reihenfolge: kann parallel zu TODO-6/7 starten.

**TODO-9 — [C] Tests-Ausdünnung planen (NICHT ausführen vor Welle-3-Branch).**
- Was: Liste der Layer-Tests (`test_m1*..test_m26*`, ~290 Tests, ~3 950 LoC) und der Strategie-Tests (`test_strategies.py`, `test_strategy3.py` zusammen 36 Tests, 1 396 LoC) erfassen. Empfehlung: erst zusammen mit dem zugehörigen Modul-Entfernen, nicht vorab. Forensik-Tests (26 Tests, 996 LoC) ABSOLUT unberührt.
- Warum: Reduziert Test-Laufzeit erheblich, sobald die Module weg sind. Aber: solange Module da sind, schützen die Tests vor unbeabsichtigten Side-Effects.
- Risiko: hoch wenn voreilig; gering wenn an Modul-Entfernen gekoppelt.
- Aufwand: 1 h Planung, 0 h Ausführung jetzt.
- Reihenfolge: VOR TODO-13/14, aber nach Welle-3-Branch-Eröffnung.

**TODO-10 — [C/U] Pre-Registration für H-05b-OOS-Lauf finalisieren.**
- Was: `hypothesis_registry.md` §H-05b ist bereits registriert (2026-06-17). Vor dem OOS-Lauf: Fenster-Cutoff bestätigen (Tick > 1 780 619 066 816 ms), Symbol-Zellen-Ausschluss (ETHUSDT w0 δ1s) im Driver-Konfig festlegen.
- Warum: H-05b ist der einzige unmittelbare Welle-3-Lauf, der "billig" ist (Code steht, Hypothese registriert).
- Risiko: keiner (Pre-Reg ist registry-disziplinär).
- Aufwand: 30 min.
- Reihenfolge: parallel; ausführbar ab ca. 2026-06-23, konservativ ab 2026-06-30.

**TODO-11 — [U] H-05b-OOS-Lauf via `run_wave2.ps1` mit anders parametriertem Driver.**
- Was: Kopie von `run_wave2.ps1` als `run_h05b_oos.ps1` mit nur `c01_ofi_sign.py`-Aufruf, FDR-Familie F-OFI-INV statt F-OFI.
- Warum: Liefert das erste Welle-3-Verdikt GL-010.
- Risiko: gering (Driver unverändert, nur Konfig).
- Aufwand: 2 h Skript, 1-3 h Laufzeit.
- Reihenfolge: nach TODO-10, frühestens ab ca. 2026-06-23 (Harvester-OOS-Daten reif).

### Repo-Strukturkosmetik — am Ende

**TODO-12 — [C] DEPRECATE-Marker im Code anbringen.**
- Was: Header-Kommentar `# DEPRECATED (2026-06-23): see scinance2-impl/state/CLEANUP_PLAN.md` in: `live_runner.py`, `multi_runner.py`, `pipeline.py`, `decision_aggregator.py`, alle 5 `strategy*.py`, `monitor.py`, `scheduler.py`, `dashboard/app.py`, `backtester/engine.py`, `training/dataset.py`, `tuning/*.py`, `collector/ws_collector.py`, `persistence/db.py`, `execution/bybit_executor.py`, `risk/budget.py`.
- Warum: Macht für jeden zukünftigen Agenten (oder Mensch) sichtbar, dass der Code nicht mehr Programm-Werkzeug ist. Keine Tests brechen.
- Risiko: keiner (Kommentar-only).
- Aufwand: 1 h.
- Reihenfolge: nach TODO-7.

**TODO-13 — [C] Modul-Entfernung Live-Stack (späteste Stufe, optional).**
- Was: `live_runner.py`, `multi_runner.py`, `execution/`, `risk/budget.py`, `monitor.py`, `scheduler.py`, `dashboard/`, `backtester/`, `training/`, `tuning/`, alle 5 `strategy*.py`, alle 26 `layers/m*.py`, sowie zugehörige Tests entfernen. NICHT entfernen: `replay_backtester.py` (Forensik-Werkzeug), `__main__.py` (auf Recorder-Default umstellen).
- Warum: Reduziert Repo-Last drastisch (~10 000-15 000 LoC). Aber: nur sinnvoll, wenn TODO-12 lange genug gestanden hat und niemand widersprochen hat. Reversibel über git, aber Test-Brüche schwerer rückbaubar.
- Risiko: mittel. Empfehlung: ERST ausführen, wenn Welle 3 mindestens ihr erstes Verdikt (GL-010, H-05b) abgeschlossen hat.
- Aufwand: 2-3 h Code-Entfernen + Test-Anpassen + Re-Run pytest.
- Reihenfolge: NACH TODO-11, NACH ausführlicher Wartezeit (mind. 1-2 Wochen Beobachtung).

**TODO-14 — [C] `bybit_edge.duckdb` aus dem operativen Pfad nehmen.**
- Was: Nachdem alle KEEP-Driver auf Harvester umgestellt sind (TODO-8 + Folge-Build): `data/bybit_edge.duckdb` ausschließlich als read-only Audit-Datei führen (`data/audit/`). `DB_PATH` in `config.py` umstellen / deprecaten.
- Warum: Vereinheitlicht Daten-Provenance auf Harvester + Recorder.
- Risiko: mittel — alle Welle-1/2-Driver, die noch über `db.py` lesen, müssen umgestellt sein.
- Aufwand: 4-6 h.
- Reihenfolge: nach TODO-8 Build-Phase.

### Welle-3-Reife abwarten

**TODO-15 — [C] Welle-3-Branch `scinance2-wave3` abzweigen.**
- Was: nach TODO-5 und (idealerweise) nach TODO-11. Branch von HEAD `scinance2-wave2`, neuer `wave3_state.md`.
- Warum: Welle-2-Branch ist inhaltlich abgeschlossen; Repo-Cleanup verdient eigene Branches; Welle 3 ihre eigene.
- Risiko: keiner.
- Aufwand: 10 min.
- Reihenfolge: nach TODO-11, vor TODO-13.

**TODO-16 — [C] Welle-3-Hypothesen-Arbeit WP-0 (parallel zu allem).**
- Was: Forschungs-Notizen zu C-06 NICHT-triviale-MR vorbereiten (Variante A/B, max 2-3 vorab fixierte Konditionierungs-Achsen). Quelle: `wave3_survey.md` §5 Stufe A.
- Warum: Ehrlich registrierbare H-09 oder Verzicht auf C-06 als Welle-3-Pilot.
- Risiko: keiner.
- Aufwand: mehrere Tage Notizen-Arbeit.
- Reihenfolge: parallel zu allem ab sofort.

---

## 7. Kurzfassung

- **KEEP:** 19 Komponenten — gesamtes Welle-1/2-Research, Recorder (Schutzgut #1), Welle-1/2-Driver, Runner, Forensik-Tests, Aggregator.
- **DEPRECATE:** 21 Komponenten — Live-Stack (LiveRunner, MultiRunner, Pipeline, DecisionAggregator), alle 5 Strategien S1-S5, alle 26 Layer-Module (L1-L5), Monitor, Scheduler, Dashboard, Backtester, Training, Tuning, Replay-All, zugehörige ~370 Tests.
- **REMOVE:** 2 Komponenten — `execution/bybit_executor.py` (275 LoC), `risk/budget.py` (373 LoC). Beide haben keinen weiteren Zweck im Falsifikationsprogramm (PRD §6 + CLAUDE.md §4).
- **REPLACE:** 3 Komponenten — `collector/ws_collector.py`, `persistence/db.py`, `persistence/backfill.py` werden durch den externen Harvester ersetzt. Alte Variante bleibt read-only Audit-Bestand.

### Die 5 wichtigsten TODOs
1. **TODO-1 + TODO-2 [U]**: Zombie-Prozesse killen, Live-Pipeline endgültig stoppen — entriegelt DuckDB sofort, beendet beide Live-Bugs ohne Code-Touch.
2. **TODO-4 [C]**: `check_recording.py` ausführen — Recorder als Schutzgut #1 lebt-Bestätigung.
3. **TODO-6 [U+C]**: `bybit_edge.duckdb` als read-only Audit-Kopie einfrieren — Welle-1/2-Verdikte reproduzierbar.
4. **TODO-8 [C]**: Welle-1/2-Driver-Datenquellen kartieren — Voraussetzung für Harvester-Umstellung und H-05b-OOS-Lauf.
5. **TODO-12 [C]**: DEPRECATE-Marker im Code anbringen — macht den Cleanup-Pfad für künftige Agenten lesbar, bevor Modul-Entfernen (TODO-13) startet.

### Kernfrage 1: Brauchen wir `live_runner.py` noch?
**Nein. DEPRECATE.** Alle 5 Strategien S1-S5 sind empirisch widerlegt (`WAVE1_FINAL_REPORT.md` §4: "Der letzte Eintrag des Original-PRDs ist gefallen."); der LiveRunner ist eine Strategie-Ausführungsschleife ohne weitere Aufgabe. Schutz-Tests (Forensik-Tests S1/S3/Direction-Inversion) bleiben unberührt; sie validieren Replay-Logik, nicht die Live-Schleife.

### Kernfrage 2: Brauchen wir `bybit_edge.duckdb` + Collector noch?
**Nein. REPLACE durch Harvester.** Der Harvester deckt alle Bybit-Streams ab, die der Collector sammelt (publicTrade, orderbook L2, funding, OI, tickers, liquidations). Die `bybit_edge.duckdb`-Datei wird als read-only Audit-Bestand eingefroren (Welle-1/2-Gate-Verdikte basieren auf ihrem Inhalt), aber nicht mehr beschrieben. Die nicht-vom-Harvester-abgedeckten Streams (rpi_orderbook, insurance_pool, premium_index_kline, option_tickers, adl_alerts) bleiben Aufgabe der C-36-Recording-Engine (Schutzgut #1) — diese läuft unverändert weiter nach `data/parquet/recording_f0/`.
