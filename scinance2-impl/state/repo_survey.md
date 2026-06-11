# Repo-Survey — Scinance 1.0 → 2.0 Welle 1

**Erstellt von:** repo-analyst · **Datum:** 2026-06-11 · **Branch:** `scinance2-wave1` · **Phase:** 1 (SURVEY)
**Methode:** Read-only-Analyse; keine Code-Änderung. Alle Pfade absolut ab Repo-Root `/home/user/scinance/`.

---

## 1. Ist-Architektur

### 1.1 Überblick

Scinance 1.0 ist eine 5-Layer-Pipeline (L1 Ingestion → L2 Denoising → L3 Regime → L4 Pattern → L5 Risk)
mit 26 Modulen (M1–M26), 5 Strategien (S1–S5), Replay-Harness, DuckDB+Parquet-Persistence,
Live-Runner und Streamlit-Dashboard. Paket: `src/bybit_edge/` (src-Layout, `pyproject.toml`).

### 1.2 Test-Suite-Stand

```
python -m pytest tests/unit/ --collect-only -q | tail -3
→ 616 tests collected in 107.39s (0:01:47)
```

- **616 Unit-Tests** kollektiert, 0 Collection-Errors (deutlich über den "88+" aus PRD §7 — die Suite ist seither gewachsen).
- Gesundheits-Stichprobe: die drei Forensik-Dateien (`test_replay_backtester_maker_only.py`,
  `test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`) → **25 passed in 4.33 s**.
- `tests/integration/` und `tests/backtests/` existieren, sind aber leer (nur `__init__.py`).

### 1.3 Verzeichnisbaum `src/bybit_edge/`

```
src/bybit_edge/
├── __init__.py / __main__.py / config.py        # zentrale Config (alle Pfade, Universe, Limits)
├── collector/ws_collector.py                    # ★ SCHUTZGUT: Bybit-V5-WS-Collector
├── state/                                       # In-Memory-State
│   ├── orderbook_state.py  ├── ticker_state.py
│   ├── trade_buffer.py     └── liquidation_buffer.py
├── persistence/
│   ├── db.py                                    # ★ SCHUTZGUT: DuckDB hot (30d) + Parquet cold
│   └── backfill.py                              # REST-Backfill (Klines, Funding, OI, L/S)
├── layers/
│   ├── base.py                                  # BaseModule-ABC: compute() → {signal, confidence, method_id, ts}
│   ├── l1_ingestion/   m1_spikewavformer, m2_ofi, m3_iceberg
│   ├── l2_denoising/   m4_wavelet, m5_ffd
│   ├── l3_regime/      m6_entropy, m7_permutation_entropy, m8_bocpd, m9_hmm,
│   │                   m10_mfdfa, m11_tda, m12_rqa, m13_cross_sectional_z
│   ├── l4_pattern/     m14_hawkes, m15_gr_omori, m16_tfsax_sw, m17_renyi_te,
│   │                   m18_patchtst, m19_timesnet, m20_moment, m21_ls_ratio
│   └── l5_risk/        m22_funding_pressure, m23_basis_convergence,
│                       m24_kalman_premium, m25_kyle_lambda, m26_sir
├── pipeline.py                                  # Pipeline: instanziiert M-xx, process_ticker()
├── decision_aggregator.py
├── strategies/         strategy1_cascade … strategy5_cross_sectional
├── replay_backtester.py                         # ★ Falsifikations-Maschine (Single-Symbol)
├── replay_all.py                                # Multi-Symbol-Replay-Aggregator (Lib-Teil)
├── backtester/engine.py                         # Kline-Backtester (OHLCV)
├── live_runner.py / multi_runner.py             # ★ SCHUTZGUT: Live-Ingestion + Persistenz-Wiring
├── execution/bybit_executor.py                  # Live-Execution (wird in 2.0 NICHT ausgebaut)
├── risk/budget.py · monitor.py · scheduler.py
├── dashboard/ (app.py, data.py)
├── training/dataset.py · tuning/ (optuna)
```

### 1.4 `scripts/` und `tests/`

```
scripts/                                tests/
├── replay_all.py      # CLI Multi-Replay├── unit/  (47 Dateien, 616 Tests, conftest.py)
├── replay_backtest.py # CLI Single      │   ├── test_replay_backtester*.py  ★ Forensik
├── backfill.py        # Kline-Backfill  │   ├── test_strategy3_bounded_exits.py ★
├── backtest.py        # Kline-Backtest  │   ├── test_strategy_direction_inversion.py ★
├── train_models.py / tune.py            │   ├── test_m1..m26*.py (je Modul)
├── dashboard.py                         │   └── test_pipeline/replay_all/multi_runner…
├── _profile_replay.py                   ├── integration/  (leer)
└── setup_local.sh                       └── backtests/    (leer)
```

Start auf der User-Maschine: `start.bat` (Windows, venv + .env + Menü). Default-Datenpfad:
`config.py: DATA_DIR = Path(os.getenv("BYBIT_DATA_DIR", "data"))`, `DB_PATH = data/bybit_edge.duckdb`,
`PARQUET_DIR = data/parquet`, `MODELS_DIR = data/models`, `DASHBOARD_SNAPSHOT_DIR = data/dashboard`.

### 1.5 Replay-Harness (Falsifikations-Maschine)

- `src/bybit_edge/replay_backtester.py` — spielt persistierte Ticks (DuckDB-Tabellen
  `tickers`/`trades`/`liquidations`) streng in `ts`-Reihenfolge durch die ECHTEN Strategien.
  Kein Lookahead (dokumentiert + getestet). Friction-Modell + Maker-Only-Modus eingebaut.
  Trade-Export: `trades_{symbol}_{mode}.csv` (Z. 1685–1692).
- `src/bybit_edge/replay_all.py` + `scripts/replay_all.py` — Multi-Symbol-Fan-out,
  Symbol-Discovery aus DuckDB (`discover_symbols`), Fallback `MULTI_SYMBOL_UNIVERSE`.
- Diagnostik/Funnel: `reason_counts` in den Results (PRD §7 verlangt Beibehaltung).

---

## 2. Integrationspunkte je Welle-1-Pilot

### P1 — E-15-Auswertung (CS-03 / C-22)

| Was | Wo |
|---|---|
| Replay-Driver (Multi-Symbol, iter-5-Lauf) | `scripts/replay_all.py` (CLI) → `src/bybit_edge/replay_all.py` (Lib) |
| Replay-Driver (Single-Symbol) | `scripts/replay_backtest.py` → `src/bybit_edge/replay_backtester.py` |
| **JSON-Export-Pfad (Default)** | `edge_research_framework/results/replay_all_results.json` + Legacy `replay_backtest_results.json` (scripts/replay_all.py Z. 694–695, 1003–1007) |
| **Trades-CSVs** | `--export-trades-dir` → `trades_{symbol}_{mode}.csv` je Symbol + aggregiert `trades_all.csv` (scripts/replay_all.py Z. 548–549, 638–640) |
| S3-Strategie + iter-5-Fixes | `src/bybit_edge/strategies/strategy3_pre_settlement.py` — iter-5 T1: Markt-Tick-Zeit statt Wall-Clock in `on_ticker(…, ts)` (Z. 105–151); iter-4/5 Exits: `time_stop_exceeded` (Z. 369–373), friction-aware `hard_stop_loss` (Z. 375–398) |
| C-22-Modul (Entry) | `src/bybit_edge/layers/l5_risk/m22_funding_pressure.py` (+ `test_m22_funding_pressure.py`) |
| Forensik-Tests (Tafelsilber) | `tests/unit/test_replay_backtester_maker_only.py`, `test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py` |

**Andockpunkt Auswertungs-Skript:** Neues Skript (z.B. `scripts/evaluate_e15.py` oder
`scinance2-impl/`-eigenes Tooling) liest `replay_all_results.json` + `trades_all.csv` und prüft
gegen die §3-Tore (time_stop 1→60–70, n>120s 68→~0, n<-30bps 33→~0, mean pnl_bps netto ≥ -5).
**Wichtig:** Die iter-5-Ergebnisdateien existieren in der Sandbox NICHT —
`edge_research_framework/results/` enthält nur `infra_requirements.json`/`task_graph.json`.
Der iter-5-Lauf läuft auf der User-Maschine; das Auswertungs-Skript muss auf einen
Ergebnis-Pfad parametrisierbar sein (Default = obiger Pfad) und gehört in den T2/T3-Handoff.
Roh-PnL-Export beider Runs (iter-3/iter-4, E-17-Widerspruch) ist ebenfalls nur lokal möglich.

### P2 — C-42-Repro (LightGBM/HAR-RV)

| Frage | Befund |
|---|---|
| LightGBM/Feature-Code im Repo? | **NEIN.** Kein `lightgbm`-Import in `src/`, `scripts/`, `tests/`. `lightgbm` ist in der Sandbox nicht installiert. |
| Wo lebt C-42 heute? | Nur als **Beschreibung** in `edge-reconciliation/input/research_notes.md` (Kestrel-v1.4: Module `kestrel.training.lightgbm_baseline`, `kestrel.features.*` — **Code NICHT in diesem Repo**). Test-R² 0.249 ist Selbstauskunft (L1). |
| Historische Daten (Klines)? | **Sandbox: keine.** `data/parquet/` ist leer (0 Dateien), `data/bybit_edge.duckdb` existiert nicht. Auf der User-Maschine: DuckDB-Tabelle `kline_1min` + Parquet-Cold-Storage `data/parquet/{table}_{date}.parquet` (zstd). Backfill-Weg vorhanden: `src/bybit_edge/persistence/backfill.py` (`/v5/market/kline`, Funding, OI, L/S-Ratio) + `scripts/backfill.py`. |
| Was fehlt für purged Walk-Forward? | ALLES an Pipeline-Code: (1) Feature-Engineering (36 Features, HAR-RV-Baseline), (2) purged-WF-Splitter (≥L2, ≥2 disjunkte OOS-Fenster), (3) FDR-Korrektur (BH α=0.10), (4) QLIKE-Metrik, (5) LightGBM-Abhängigkeit (pyproject erweitern). Einziger verwandter Baustein: `src/bybit_edge/training/dataset.py` (chronologischer Split, kein Purging). |

**Andockpunkt:** Neues Paket z.B. `src/bybit_edge/research/c42_rv/` (oder `vol/`) + CLI-Skript
in `scripts/`; Datenzugriff über `PersistenceLayer.query_kline` bzw. REST-Backfill.
Klines-Backfill via öffentliche API ist der Datenweg — in der Sandbox aber netzgesperrt (s. §5),
daher: Fixtures aus eingecheckten Mini-Beständen bauen, Voll-Fit = T2/T3 lokal.

### P3 — C-36-Recording

**Bestehender Collector:** `src/bybit_edge/collector/ws_collector.py`
- Streams heute (Z. 46–51): `tickers.{symbol}`, `publicTrade.{symbol}`, `orderbook.50.{symbol}`, `allLiquidation.{symbol}`.
- Architektur: ein WS pro Symbol, `STREAMS`-Dict → per-Stream `asyncio.Queue(10_000)` + Pub/Sub-Handler
  (`add_handler`), Auto-Reconnect mit Backoff, REST-Snapshot-Resync, `WSMessage`-Envelope
  mit `schema_version=1`, `recv_ts`, `msg_type`, `envelope_ts`.
- Persistenz-Wiring: `src/bybit_edge/live_runner.py` (Handler → `PersistenceLayer`-Batch-Writes,
  Flush-Intervall `PERSIST_FLUSH_SECONDS`, L2-Snapshots opt-in via `PERSIST_ORDERBOOK`).
  Multi-Symbol: `multi_runner.py` (shared `PersistenceLayer`).
- Schema: `src/bybit_edge/persistence/db.py` `_init_schema` (Z. 95 ff.) — Tabellen `tickers`,
  `trades`, `liquidations`, `kline_1min`, `open_interest`, `long_short_ratio`,
  `funding_history`, `orderbook_snapshots`; Archivierung `archive_old_data()` (Z. 789 ff.):
  älter als `HOT_RETENTION_DAYS` → `data/parquet/{table}_{date}.parquet` (zstd).

**Andockpunkte für neue Streams (ADDITIV, Collector unangetastet lassen):**
1. `STREAMS`-Dict ist erweiterbar (`orderbook.rpi`, `insurance.USDT` ist symbol-los → braucht
   Sonderbehandlung im Topic-Matching `_dispatch` Z. 207–216!), `adlAlert` ebenso.
2. **Empfehlung (reversibelste Option):** neue Recording-Engine als EIGENE Klasse/Datei
   (z.B. `src/bybit_edge/collector/recording_engine.py` oder `recorder/`), die `BybitWSCollector`
   wiederverwendet oder parallel eine zweite WS-Verbindung aufmacht — statt `STREAMS`/`_dispatch`
   im Bestand umzubauen. Insurance/ADL/Options-Tickers sind andere Endpoints
   (Options = eigene WS-URL `wss://stream.bybit.com/v5/public/option`) und passen ohnehin
   nicht 1:1 in das `{symbol}`-Template des Bestands-Collectors.
3. Neue Daten in NEUE Tabellen/Parquet-Partitionen (Schutzgut 3): eigene Tabellen
   (`rpi_orderbook`, `insurance_pool`, `adl_alerts`, `premium_index_kline`, `option_tickers`)
   bzw. eigener Parquet-Unterpfad `data/parquet/recording_f0/…` + Storage-Deckel (Ringpuffer/Rotation, PRD §3 Pilot 3).
4. Premium-Index-Kline: REST `premium-index-price-kline` → Erweiterung in
   `persistence/backfill.py`-Stil (neue Methode, kein Umbau bestehender).

### P4 — C-31 CFAR

- **Modul-Heimat:** `src/bybit_edge/layers/` — aber C-31 ist ein Standalone-Analysemodul, KEIN
  Pipeline-Glied. Interface-Pattern: `layers/base.py` `BaseModule.compute() → {signal, confidence,
  method_id, ts}`; Pipeline-Integration via `pipeline.py` (`process_ticker`), Strategien via
  `on_ticker(ticker_data, seconds_to_settlement, ts)` (siehe strategy3).
- **Datenquelle:** publicTrade-Inter-Arrivals. Live-State: `src/bybit_edge/state/trade_buffer.py`
  (`TradeBuffer.recent_timestamps(n)` liefert genau die Timestamps für Inter-Arrival-Berechnung).
  Historisch: DuckDB-Tabelle `trades` (`ts`-Spalte) via `replay_backtester` bzw. direkt
  `PersistenceLayer`. Kein Inter-Arrival-Code existiert bisher (`grep inter.arrival` = 0 Treffer).
- **Natürlicher Platz:** neues Modul z.B. `src/bybit_edge/layers/l4_pattern/m27_cfar_cyclo.py`
  (folgt M-xx-Konvention) ODER — reversibler, da kein Pipeline-Umbau nötig — eigenes
  Analysepaket `src/bybit_edge/research/c31_cfar/` mit drei Bausteinen:
  Cyclic-Spectrum-Schätzer, CFAR-Peak-Detektor, Surrogate-Test (geshuffelte Inter-Arrivals).
  Replay-Anbindung: read-only über die `trades`-Tabelle (eigener kleiner Driver, NICHT
  `replay_backtester` umbauen — der ist Strategie-zentriert); Tests nach
  `tests/unit/test_m27_cfar*.py`-Muster.
- Entscheidung Modul-Pfad vs. research-Pfad = DEC-xx-Kandidat für den architect.

---

## 3. Schutzgüter — konkrete Pfade (NICHT anfassen / nur additiv)

| Schutzgut | Pfad(e) | Bruch-Erkennung |
|---|---|---|
| Collector/Ingestion | `src/bybit_edge/collector/ws_collector.py`, `src/bybit_edge/live_runner.py`, `src/bybit_edge/multi_runner.py` | `tests/unit/test_infrastructure.py`, `test_multi_runner.py`; Collector-Smoke (60–120 s Live-Ingestion) — in Sandbox NICHT möglich (s. §5), nur Code-Level + T2 lokal |
| Persistence/Parquet-Writer | `src/bybit_edge/persistence/db.py` (Schema Z. 95–232, Archivierung Z. 789 ff.) | Schema-Tests in `test_infrastructure.py`; Schema-Vergleich vor/nach |
| Parquet-/DuckDB-Bestände | User-Maschine: `data/bybit_edge.duckdb`, `data/parquet/*.parquet`. **Sandbox: leer** (`du -sh data` = 24K; `data/parquet/` = 0 Dateien; nur `data/trades_journal.csv`, 15 KB) | read-only-Disziplin; neue Daten in neue Tabellen/Pfade |
| Replay-Harness | `src/bybit_edge/replay_backtester.py`, `src/bybit_edge/replay_all.py`, `scripts/replay_all.py`, `scripts/replay_backtest.py` | `test_replay_backtester.py`, `test_replay_all.py`, `test_replay_backtest_cli.py` |
| Forensik-Tests (unantastbar) | `tests/unit/test_replay_backtester_maker_only.py`, `tests/unit/test_strategy3_bounded_exits.py`, `tests/unit/test_strategy_direction_inversion.py` | müssen IMMER grün bleiben (aktuell 25/25 in 4.3 s) |
| Test-Suite gesamt | `tests/unit/` — 616 Tests | Anzahl darf nie sinken; `--collect-only`-Zählung je Commit |

Regeln: Recording-Engine ERWEITERT (neue Dateien/Tabellen), ersetzt nichts. Kein Edit an
`ws_collector.py`/`db.py`-Bestandstabellen ohne Collector-Smoke-Test (T2, User-Maschine).
S1/S2-Retirement (PRD §7) erfolgt in Config/Strategie-Registry, NICHT durch Löschen.

---

## 4. PRD-Annahmen vs. Repo-Realität

1. **C-01/C-02-Vertauschung (PRD §7, bestätigt):** `edge-reconciliation/results/repo_map.md` Z. 33–34
   mappt `m1_spikewavformer.py`→C-01 und `m2_ofi.py`→C-02; das kanonische
   `edge-reconciliation/results/claims_register.md` sagt C-01=OFI (`m2_ofi.py`),
   C-02=SpikeWavformer (`m1_spikewavformer.py`). **Das Register gilt.** Code-seitig irrelevant
   (Module heißen M1/M2), aber jede C-xx-Referenz in Doku/Registry muss dem Register folgen.
2. **"88+ Tests" (PRD §7) ist veraltet:** real 616 Unit-Tests. Positiv-Abweichung; Schutzregel
   "nie reduzieren" bezieht sich auf den Ist-Stand 616.
3. **C-42 lebt NICHT im Repo:** PRD §7 sagt korrekt "außerhalb des src/bybit_edge-Baums
   (separates Kestrel-v1.4-Notebook)". Realität noch härter: der Kestrel-Code ist in DIESEM
   Repo überhaupt nicht vorhanden (nur Beschreibung in `edge-reconciliation/input/research_notes.md`).
   C-42-"Repro" = Neu-Implementation nach Beschreibung, nicht Code-Portierung. `lightgbm` fehlt
   als Dependency (pyproject + Sandbox).
4. **Kein laufender Collector, keine Daten in der Sandbox:** `ps aux` zeigt keinen
   Collector/LiveRunner-Prozess; `data/` enthält nur leeres `parquet/` und `trades_journal.csv`;
   Repo gesamt 6.4 MB. **Dies ist eine reine Code-Sandbox.** Der echte Collector + DuckDB/Parquet-
   Bestände laufen/liegen auf der User-Maschine (Windows, `start.bat`).
   **Konsequenz:** Collector-Smoke-Tests in der Sandbox = Code-Level (pytest, Mock-WS) —
   die im CLAUDE.md vorgesehene "60–120 s Live-Ingestion gegen die öffentliche API" ist in
   DIESER Sandbox zusätzlich netzgesperrt (s. §5); Dauerbetrieb und echter Smoke bleiben beim User (T2).
5. **E-15/iter-5-Ergebnisse liegen nicht im Repo:** `edge_research_framework/results/` enthält
   kein `replay_all_results.json` und keine trades-CSVs. Der "bereits laufende" iter-5-Run
   (PRD §3 Pilot 1) läuft auf der User-Maschine. P1-Auswertung ist baubar (Skript + Tests auf
   synthetischen Fixtures), aber erst mit lokal eingespielten Ergebnissen ausführbar (T2-Handoff).
6. **PRD §3 Pilot 3 nennt `insurance.USDT`/`adlAlert`:** beides sind symbol-lose bzw.
   anders-strukturierte Topics — das bestehende `STREAMS`-Template (`{symbol}`-basiert,
   exaktes Topic-Matching in `_dispatch`) kann sie NICHT ohne Erweiterung aufnehmen.
   Bestätigt die Architektur-Entscheidung "eigene Recording-Engine statt Collector-Umbau".
7. **`tests/integration/`, `tests/backtests/` sind leer** — die Testpyramide T1 (Kurz-Replay)
   hat noch kein Zuhause im Test-Baum; Fixtures müssen neu gebaut werden (synthetisch, da
   keine echten Tickdaten in der Sandbox und kein API-Zugriff).
8. **Default-Output von `scripts/replay_all.py`** geht nach `edge_research_framework/results/` —
   ein Doku-/Framework-Verzeichnis. Für Scinance-2.0-Gate-Läufe sollte der Output-Pfad explizit
   gesetzt werden (CLI-Flag existiert), DEC-xx-Kandidat.

---

## 5. Sandbox-Fähigkeiten

**Netzwerk-Check:**
```
curl -s -m 5 "https://api.bybit.com/v5/market/time"  →  "Host not in allowlist"
```
**Die öffentliche Bybit-API ist aus dieser Sandbox NICHT erreichbar.** Die in CLAUDE.md
vorgesehenen Live-Stichproben (T1-Fixture-Bau, Collector-Smoke 60–120 s) entfallen hier ersatzlos
und wandern in den T2-Handoff. Fixtures müssen synthetisch bzw. aus Schema-Wissen gebaut werden.

| Fähigkeit | Sandbox | Beleg |
|---|---|---|
| pytest (T0), volle Unit-Suite | JA | 616 Tests kollektieren; Forensik-Subset 25/25 grün |
| Kurz-Replays auf Fixtures (T1) | JA (nur synthetische Fixtures) | duckdb/websockets/aiohttp installiert; `PersistenceLayer(":memory:")` möglich |
| Bybit-REST/WS-Stichproben | **NEIN** | Host-Allowlist blockiert api.bybit.com |
| LightGBM-Fit | NEIN (Paket fehlt) → Dependency ergänzen, dann ggf. Sandbox-Fit auf Fixtures | `import lightgbm` → ModuleNotFoundError |
| Collector-Smoke live | NEIN → T2 lokal (`run_short`) | kein Netz, kein laufender Prozess |
| iter-5-/E-15-Auswertung ausführen | NEIN (Ergebnisdaten fehlen) → T2 | `edge_research_framework/results/` ohne Replay-JSONs |
| Volle Walk-Forward-Läufe, Multi-Symbol-Replays, Recording-Dauertest, GPU-Training | NEIN → T3 (`run_overnight`) | keine Daten, kein Netz, Laufzeit |

**T2 (lokal, 10–20 min):** Collector-Smoke (5 min live inkl. neuer Streams), Mini-Replay echter
DuckDB-Daten, C-42-Quick-Fit 1 Symbol, E-15-Auswertungs-Skript auf echten iter-Ergebnissen.
**T3 (lokal, über Nacht):** C-42 purged Walk-Forward multi-symbol, C-31-Surrogate auf echten
Tick-Beständen (≥2 disjunkte Fenster), Recording-Dauertest mit Storage-Deckel, iter-3/4-Roh-PnL-Export.

---
*Ende repo_survey.md — read-only erstellt, nichts committet.*
