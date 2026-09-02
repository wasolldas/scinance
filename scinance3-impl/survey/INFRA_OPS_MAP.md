# scinance — Infrastructure & Operational Dependency Map

Surveyed 2026-09-02. Read-only survey of `/home/user/scinance`. This repo has **no local
`data/` tree in the sandbox checkout** — everything below about the harvest tree, the
recorder's parquet output, and the Windows scheduled tasks is inferred from code,
`.gitignore` (`data/` is untracked), and the operational logs under
`scinance2-impl/state/{decisions.md,gate_log.md}`, which record what actually runs on
the user's Windows machine.

---

## 1. Data collection — what THIS repo records, and what it only reads

### 1.1 Two separate recording systems (do not confuse them — DEC-43/DEC-46 record a
real mistake made by confusing them)

| | (a) THIS repo's recorder (`bybit_edge.recorder`) | (b) External "Data-Harvest" project |
|---|---|---|
| Location | `src/bybit_edge/recorder/` (this repo) | separate repo, NOT in this checkout |
| Writes to | `data/parquet/recording_f0/{stream}/{date}/seg-*.parquet` | `data/harvest/raw/{exchange}/{stream}/symbol=…/date=…/*.parquet` (junction on the user's machine) + `state/harvest_manifest.sqlite` / `.backup.sqlite` |
| Streams | `rpi_orderbook`, `insurance_pool`, `adl_alerts`, `premium_index_kline`, `option_tickers` (bybit only) | `publicTrade`, `orderbook`(L2), `tickers`, `rest.fundingRate`, `rest.openInterest`, `allLiquidation`, `insurance`, deribit `dvol`/`markprice.options`/`book_summary`, binance, bitmex, tardis `options_chain` |
| Read by any driver in this repo? | **No.** DEC-43: *"Kein Treiber im Repo liest den recording_f0-Pfad."* | **Yes — exclusively.** All Wave 4–8 measurements (`c01`…`c24`, WP-0/1/2/4/5/6) read only this tree. |
| Still meant to run? | **Yes — "Schutzgut #1" (protected asset).** `start.bat` option 2 starts it; Task Scheduler entry `"Scinance C-36 Recorder"` autostarts it at logon. It is deliberately left running even though nothing consumes its output yet — future option-spread work may. | Yes, this is the sole active Bybit/Binance/Deribit data source; run entirely outside this repo. |

**Why it still runs despite being unread**: DEC-06 established it as strictly additive
(new tables, new path, never touches the 1.0 collector or its parquet) and reversible
(delete the module + the path). It exists to plug a real-but-unconfirmed gap
(`option_tickers` NO_DATA, `adl_alerts` phantom topic) and as insurance against future
option-spread hypotheses (C-33/H-26b) — see §4 on `snap_bybit_optchain.ps1`, which was
built as a *stopgap* for exactly the gap this recorder was originally meant to close,
until DEC-46 discovered the harvester already covers it.

### 1.2 `src/bybit_edge/recorder/` — module map

| File | Role |
|---|---|
| `recording_engine.py` (748 lines) | `RecordingEngine`: two independent WS transports (linear public + `wss://stream.bybit.com/v5/public/option`), REST poll for premium-index kline (no WS topic exists), reconnect backoff (1s→2s→…→60s, same constants as the 1.0 collector), app-level `{"op":"ping"}` every 20s (the option WS ignores RFC-6455 pings and gets closed by the client every ~31s without it), graceful SIGINT/SIGTERM shutdown, per-stream buffer+flush. Constructor-injected `ws_connect`/`rest_poll` for testability (no network in tests). |
| `storage.py` (509 lines) | `ParquetStreamWriter` (explicit pyarrow `Schema` per stream, `schema_version` in Parquet KV metadata), `StorageCap` (hard GB ring buffer — deletes THIS engine's own oldest segments only, never the 1.0 cold storage). `RECORDING_ROOT = DATA_DIR/"parquet"/"recording_f0"`. `DEFAULT_CAP_GB=50.0`. `DEFAULT_FLUSH_ROWS=2000`, `DEFAULT_FLUSH_SECONDS=10.0`. Exponential flush-retry backoff (5s→60s) — a documented regression fix (CRITICAL_REVIEW_2_2026-07-13) for a bug where a failing flush pinned the event loop. |
| `sunset.py` (201 lines) | `SunsetReviewer`: writes a Sunset-Review report from `--sunset-start`; first review due ~2026-09-11 (90-day horizon from the 2026-06-11 recording start, per `start_recorder.ps1` header). |
| `__main__.py` | CLI: `python -m bybit_edge.recorder [--streams] [--cap-gb] [--duration] [--symbols] [--options] [--sunset-start]`. |

Per-stream pyarrow schemas (in `storage.py`) — every stream carries `ts` (exchange ms),
`recv_ts` (float seconds, reception wall-clock), and a `raw_json` fallback column, plus
typed fields. Example, `rpi_orderbook`:
`ts, symbol, update_id, seq, msg_type(snapshot|delta), side(bid|ask), level, price, size, recv_ts`.

### 1.3 Launch/autostart scripts (repo root)

| File | Purpose |
|---|---|
| `start_recorder.ps1` | Foreground launcher: single-instance guard (scans `Win32_Process` for a running `bybit_edge.recorder`, refuses a second start — Schutzgut #1 = one writer per `recording_f0`), timestamped logs under `logs\recorder\`, `BelowNormal` process priority, runs `python -m bybit_edge.recorder --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT --options BTC,ETH` unbounded. |
| `install_recorder_autostart.ps1` | Registers Windows Scheduled Task **"Scinance C-36 Recorder"**: `AtLogOn` trigger (30s delay), runs `start_recorder.ps1` hidden, `RestartCount 3` / 1-min interval, no execution time limit, user-level (no admin). Idempotent (re-run replaces the task). |
| `uninstall_recorder_autostart.ps1` | Removes that task. |
| `start.bat` | Interactive menu (Tests / Recorder start / Recorder status / Welle-2 run / Python shell / Autostart install-uninstall-status / Exit). Explicitly states in its banner: *"Scinance-1.0-Live-Pipeline ist DEPRECATED… Daten kommen aus Harvester (extern) + C-36-Recorder (lokal)."* Calls `scinance2-impl/handoff_local/check_recording.py` for read-only recorder status. |

### 1.4 What this repo assumes about the external harvest tree

**Path pattern** (identical on both projects — this repo reaches it through a Windows
directory **junction** `data\harvest` → the harvester's own `data\` root):

```
data/harvest/raw/<exchange>/<stream>/symbol=<SYM>/date=<YYYY-MM-DD>/<uuid>.parquet
data/harvest/state/harvest_manifest.sqlite            (legacy, frozen, no registrar rows)
data/harvest/state/harvest_manifest.backup.sqlite      (current truth, since DEC-49/50)
```
`<exchange>` ∈ `bybit | binance | deribit | bitmex | tardis`. `symbol=`/`date=` are Hive
partition keys. A partition may hold several parquet files (live flushes continuously;
nightly compaction folds them, content unchanged).

**Container column schema — identical across every source/stream** (the single fact the
whole research tree is built on):

| Column | Type | Meaning |
|---|---|---|
| `ts_local_ns` | int64, not null | receive/write time (ns); for backfill, derived from event time |
| `ts_exchange_ms` | int64, nullable | **exchange event time (ms)** — the backtest-authoritative clock |
| `topic` | string | raw source topic/channel |
| `stream` | string | = partition's `<stream>` |
| `symbol` | string | = partition's `<symbol>` |
| `payload_json` | string, not null | full original record as JSON (lossless) |

`date` is a 7th, Hive-partition-derived column exposed by `hive_partitioning=1`.

**`payload_json` has TWO structurally different `publicTrade` dialects** (this is the
single most consequential fact in the whole read path — see `payload_sql.py` below):

- **FLAT (backfill)**: one trade per row, top-level keys. bybit
  `{"timestamp","symbol","side","size","price","trdMatchID"}`; binance
  `{"id","price","qty","time","is_buyer_maker"}`; deribit
  `{"trade_seq","trade_id","timestamp","price","instrument_name","direction","amount"}`
  (native JSON numbers, not strings).
- **ENVELOPE (live)**: many trades nested in one row —
  `{"topic":"publicTrade.SYM","ts":…,"data":[{"T":…,"s":…,"S":"Buy","v":"…","p":"…","i":"…"}, …]}`
  (bybit V5 WS), or deribit's JSON-RPC `{"params":{"channel":…,"data":[…]}}` form.
  Reading only top-level keys silently drops every envelope row — this bit
  scinance for real: bybit from 2026-07-17 and deribit from ~2026-06-16 yielded 0
  parsable trades, flipping 19/50 W2 days of the H-12 run to `panel_valid=False`
  before `payload_sql.trade_rows_sql` fixed it (2026-08-xx).

**Manifest table schema** (`harvest_manifest(.backup).sqlite`, table `partitions`):
PK `(exchange, stream, symbol, date)`, column `status` ∈
`DONE | EMPTY | FAILED | PENDING | RUNNING`. Coverage query pattern used throughout:
`SUM(status='DONE') AS done_days`, `MIN/MAX(date) WHERE status='DONE'`, and
`done_days == (last_done − first_done + 1)` to detect gaps. **Live-only partitions
(e.g. option tickers) are NOT guaranteed manifest rows** unless the harvester's
"registrar" back-fills them (DEC-46/DEC-49 — a real, previously-missed defect: the
live ingestion path did not write manifest DONE rows at all until fixed).
`bar_cache.resolve_manifest_path()` in this repo prefers `harvest_manifest.backup.sqlite`
and falls back to the legacy name only if the backup file is absent (pinned by test).

**Every place in `src/` and `scripts/` that reads the harvest tree** (26 files touch
`base_dir="data/harvest"` defaults or read the manifest directly):

- Shared read-path: `src/bybit_edge/research/payload_sql.py` (the flat/envelope union +
  cross-form dedup — every trade loader below is built on top of it)
- `src/bybit_edge/research/bar_cache.py` (own manifest-DONE gate, `manifest_done_days`)
- Per-hypothesis drivers/loaders: `c01_ofi_sign/oos.py`, `c01_ofi_tradability/{__init__,driver,fade_rule}.py`,
  `c06_xmr/{__init__,panel}.py`, `c09_bunch/{__init__,driver}.py`, `c10_pointer/loaders.py`,
  `c11_anen/{__init__,driver,driver_c,features}.py`, `c12_frag/{__init__,panel}.py`,
  `c13_tailshape/{options_loader,returns_tail,snapshot_selection}.py`,
  `c14_panellag/{__init__,panel}.py`, `c15_grammar/driver.py`, `c16_arrow/driver.py`,
  `c17_venue/{__init__,features}.py`, `c19_drift/driver.py`, `c22_l2tilt/extract.py`
- CLI scripts (all `scripts/c*.py`, `scripts/l2_census.py`, `scripts/wp2_l2_extract.py`,
  `scripts/wp4_spread_census.py`, `scripts/wp6_optstress_census.py`,
  `scripts/build_bar_cache.py`) — each does
  `sys.path.insert(0, …/"src")` then imports the corresponding `bybit_edge.research.*`
  module; `base-dir` / `base_dir` defaults to `"data/harvest"` throughout.

**Documented caveats consumers must honor** (from `edge-research-v3/reference/DATASET.md`,
kept in this repo as read-only reference to the external project):
- Bybit L2 backfill (bycsi bulk) is empty for the 2026 window (HTTP 404) — L2 for the
  5 perps is collected **forward-only via live** `orderbook.1000`.
- `orderbook` L2 needs snapshot+delta replay — there is no ready-made depth book;
  reconstruction is the consumer's job (this is exactly what `c22_l2tilt/extract.py`
  does).
- Backfill/live overlap at boundary dates can double-count a trade (same exchange
  trade id in both a flat backfill row and a live envelope element) —
  `payload_sql.cross_form_dedup_qualify()` handles this.
- Symbol depth limits: SOL/BNB/XRP perps only exist from ~2020–2021; earlier dates are
  legitimately EMPTY, not a bug.

---

## 2. Derived stores built by THIS repo

All three share the same design discipline: new path outside the harvest tree
(never writes into the read-only harvester tree — a CLI guard refuses a cache path
inside it), immutable per-day partitions written once and read-only after, a
`manifest.json`/sidecar with `schema_version` + SHA-256 fingerprint, and a documented
loud-fail on "raw rows exist but 0 parsed" rather than silently freezing an empty day.

### 2.1 Bar cache — `src/bybit_edge/research/bar_cache.py` (496 lines)

- **Why it exists (DEC-34)**: three H-11c runs on identical code + an identical harvest
  snapshot produced *different* daily panels — raw-tick aggregation is
  non-deterministic (parallel float summation order; ties in `max_by` on a shared
  millisecond). Wave 6 hypotheses must read only this cache.
- **Layout**: `<cache_dir>/bars_1min/exchange=<x>/symbol=<s>/date=<d>/bars.parquet` +
  sidecar `manifest.json`. Default cache dir: `data/barcache` (new path — CLI refuses a
  cache path inside the harvest tree).
- **Columns** (`BAR_COLUMNS`, canonical + fingerprint order): `minute_idx, px_first,
  px_last, px_high, px_low, vol_buy, vol_sell, vol_total, n_trades, n_buy, n_sell,
  n_size_unparsed`.
- **Determinism guarantees**: `px_last`/`px_first` via `arg_max`/`arg_min` over a
  composite `(ts_exchange_ms, px)` key (order-independent tie-break); `px_high`/`px_low`
  plain max/min; volumes summed as `DECIMAL(38,12)` cast from the **original JSON
  string** (never through float) — integer-exact, commutative, only the final total
  becomes `DOUBLE`; counts are exact. `preserve_insertion_order=false` is explicitly
  safe here because every aggregate is order-independent.
- **Fingerprint**: `bars_fingerprint()` = SHA-256 over the exact value bytes of every
  column across a range, in `BAR_COLUMNS` order — "forensic only, NEVER a gate flag"
  (a single last-bit change flips it; it's a change detector, not a validity switch).
  Every Wave-6 registration must quote it (DEC-34 point 4).
- **Gate**: only manifest-`DONE` days are cached (`manifest_done_days()` — raises
  `BarCacheError` if the manifest is missing/unreadable; **no folder-scan fallback**,
  by design, so a partial day is never silently frozen).
- **Memory discipline** (DEC-36, after an OOM crash mid-build): hard `memory_limit`
  (default `4GB`) + DuckDB disk spill (`temp_directory`, `max_temp_directory_size=100GiB`);
  connection recycled every `RECYCLE_EVERY_DAYS = 200` day-queries; one retry on a
  fresh connection on `OutOfMemoryException`, a second OOM raises `BarCacheError`
  naming the day (and the CLI moves on to the next symbol rather than dying).
- **Schema version**: `SCHEMA_VERSION = 1`; `load_minute_bars()` refuses a partition
  whose sidecar version mismatches — "rebuild required, never mixed."
- **Consumers**: Wave 6 hypothesis drivers (via `load_minute_bars`); `scripts/build_bar_cache.py`
  is the build CLI (`run_wp0_barcache.ps1` runs it on the user's machine).

### 2.2 L2 tilt store + spread store — `src/bybit_edge/research/c22_l2tilt/extract.py` (554 lines)

- **Why it exists**: the bybit `orderbook` stream is snapshot(+~2/day)+delta over the
  whole history — near-touch tilt requires actual **book reconstruction**, never a
  snapshot read. This module is that one deterministic sequential pass.
- **Replay rules** (registered, binding): records applied in `(ts_exchange_ms, u)`
  order; `snapshot` replaces the book, `delta` upserts (size `"0"` deletes);
  non-contiguous `u` (`≠ prev_u+1`) counts one SEQUENCE BREAK but the delta still
  applies (waiting for resync would discard ~half a day given only ~2 snapshots/day);
  every full snapshot validates the replayed book and resyncs on mismatch (also a
  break); a day with **> `MAX_BREAKS_PER_DAY = 10`** breaks, or a window-start day
  before the first snapshot, is loudly `discarded` (counted, never silent). Book
  state carries **across days** within one window pass — the whole window is one
  deterministic pass, pinned bit-identical by test.
- **Tilt definition**: at each minute boundary, `T = (B − A) / (B + A)` with B/A summed
  bid/ask size within `±BAND_BP = 25.0` bps of mid.
- **Layout — tilt (WP-2/H-22)**: `<out>/tilt_1min/exchange=<x>/symbol=<s>/date=<d>/tilt.parquet`
  + `manifest.json`. Columns: `minute_idx, tilt, mid`.
- **Layout — spread (WP-4)**: `<out>/spread_1min/exchange=<x>/symbol=<s>/date=<d>/…`
  (same `out_dir` root, separate top-level folder — built by `extract_spread_window`,
  proven by test never to touch the `tilt_1min` files). Feeds
  `scripts/wp4_spread_census.py`, which compares the realised half-spread against
  `FEE_MAKER` (0.02%, `config.py`) to binarily kill/keep the maker-spread-capture
  candidate.
- **Fingerprint**: `tilt_fingerprint()` — same SHA-256-over-column-bytes pattern as the
  bar cache, quoted by the H-22 run report.
- **Consumers**: H-22 driver (`c22_l2tilt/driver.py`), `scripts/wp4_spread_census.py`,
  `scripts/l2_census.py`, `scripts/wp2_l2_extract.py`; run via
  `run_wp1_l2census.ps1` / `run_wp2_l2extract.ps1` / `run_wp4_spreadcensus.ps1`.

### 2.3 Option snapshots / time series — `wp5_optchain` + `wp6_optstress`

Two independent surfaces feeding the same census logic (`census.py`'s bucket
machinery — `DTE_BUCKETS`, `DELTA_BUCKETS`, `bucket_stats`, `vega_over_index`,
`breakeven_fee_bp` — is shared):

- **WP-5 REST snapshots** (`src/bybit_edge/research/wp5_optchain/census.py`, 250 lines):
  reads a raw Bybit `/v5/market/tickers?category=option` snapshot (or a bare
  `result.list`). Buckets by time-to-expiry (`DTE_BUCKETS`: 0-7/8-21/22-45/46-120/>120
  days) **and** by `|delta|` (`DELTA_BUCKETS`: 5 bands from deep-OTM to ITM) — pooling
  across strikes without the delta axis is explicitly called out as broken (deep-ITM
  vega→0 divides a one-tick price width into a meaningless tens-of-vol-point IV
  width). Reports a scale-free `vega/S` (USD per vol point per index unit) so a
  fee-fraction can be expressed in vol points via `cost_volpts`. Snapshot files are
  produced by `scinance2-impl/handoff_local/snap_bybit_optchain.ps1` (see §4) into
  `data/optchain_snaps/<COIN>/<COIN>_<yyyyMMdd_HHmmss>Z.json`, turned into a CSV time
  series by `scripts/wp5_snap_timeseries.py` (`ts_utc, coin, n_symbols, underlying,
  atm_mark_iv, n_legs, leg_w_p25/p50/p75, leg_rel_p50, leg_oi_p50, leg_bidsz_p50,
  atm_n, atm_w_p50, front_dte`). DTE is always computed against the **snapshot's own
  timestamp**, never "today" — a WP-5 lesson pinned by test.
- **WP-6 harvest-tree time series** (`src/bybit_edge/research/wp6_optstress/extract.py`,
  163 lines): reads the harvester's `raw/bybit/tickers/` stream (option frames live
  **next to** perp tickers there, not in a separate `option_tickers` stream — the
  DEC-43→DEC-46 correction). Two explicit steps: **probe** (`unwrap_payload` +
  driver `--probe`) verifies what fields the WS frames actually carry before any
  measurement is trusted (field aliases differ from REST: `bidPrice`/`bid1Price`,
  `bidIv`/`bid1Iv`, `markPriceIv`/`markIv`, etc. — `FIELD_ALIASES`), then **census**:
  per (symbol, minute) the deterministic last frame, minute-level strangle-leg-band
  width + ATM mark-IV. Built specifically to cover the 2026-08-19 stress window the
  REST sampler (started 2026-08-24) missed. Consumed via
  `scripts/wp6_optstress_census.py` / `run_wp6_stresszensus.ps1`.
- Both are read-only against the harvest tree / snapshot tree; neither writes into
  the harvester's own path.

---

## 3. Replay harness / backtester / test suite

### 3.1 What "the replay harness" is

There is no single file named "replay harness" — the term refers to the
**deterministic historical-replay pipeline** built from:

- `src/bybit_edge/replay_all.py` and `src/bybit_edge/replay_backtester.py` — the
  actual replay/backtest engines (run via `scripts/replay_all.py`,
  `scripts/replay_backtest.py`, `scripts/_profile_replay.py`).
- `src/bybit_edge/backtester/engine.py` — `WalkForwardSplitter`, `BacktestEngine`,
  `Trade`, `BacktestResult` (marked DEPRECATE per CLEANUP_PLAN/DEC — kept as
  infrastructure, not wired to any live strategy).
- `src/bybit_edge/research/e15_eval/` (`e17.py`, `gate.py`, `metrics.py`, `report.py`)
  — the E-15/E-17 evaluation layer consuming replay output, run via
  `scripts/evaluate_e15.py`.

**How it is run**: `python scripts/replay_all.py …` / `python scripts/replay_backtest.py …`
(sandbox-safe, short fixture windows) or the corresponding `run_*.ps1`/`.sh` pair
under `scinance2-impl/handoff_local/` for a full overnight/local run (e.g.
`run_h04b.ps1`, `run_overnight.ps1`). Output lands under
`scinance2-impl/handoff_local/results/<run_id>/` as JSON + Markdown
(`SUMMARY_<date>.md`).

### 3.2 `tests/backtests/` and `tests/integration/`

Both directories contain **only an empty `__init__.py`** — they are placeholders,
not populated suites. All the real replay/backtest/recorder tests live under
`tests/unit/` instead (e.g. `test_replay_all.py`, `test_replay_backtester.py`,
`test_replay_backtester_maker_only.py`, `test_replay_backtest_cli.py`,
`test_backtest_driver.py`, `test_recorder_engine.py`, `test_recorder_storage.py`,
`test_recorder_sunset.py`, `test_e15_eval.py`, `test_dashboard.py`). A restructuring
must not assume `tests/backtests`/`tests/integration` hold anything to preserve
beyond their (currently trivial) package markers — but must not silently merge or
delete them either, since the constitution explicitly names "the existing test
suite" as protected without carving out exceptions for empty directories.

### 3.3 Fixtures (`tests/fixtures/`, 10 files total)

- `tests/fixtures/c42/` — 5.5 MB: `btc_garch_30d.csv` (synthetic 30-day GARCH fixture)
  + `make_garch_fixture.py` (regenerator script) for `test_c42_rv.py`.
- `tests/fixtures/e15/` — 48 KB across three scenario subdirs `drop/`, `grau/`,
  `weiter/`, each with `replay_all_results.json` (+ `baseline_results.json` for
  `grau`/`weiter`) and `trades_all.csv` — canned E-15/E-17 gate scenarios
  (DROP/GRAUBEREICH/WEITER) for `test_e15_eval.py`.

Total fixture footprint is small (~5.6 MB) and entirely synthetic/canned — no live
credentials or real harvest data are embedded, consistent with the Schutzgut rule
that the harvest tree stays read-only-external and never gets vendored into the repo.

### 3.4 Protected per the constitution (`scinance2-impl/CLAUDE.md`)

> **SCHUTZGÜTER (dürfen nie brechen)**
> - The running data collector / continuous disk recording from Product 1.0 —
>   any data/state-layer change must pass the "Collector-Smoke-Test" first.
> - **Replay-Harness + existing test suite (88+ tests): extended, never reduced.
>   Forensics tests are untouchable.**
> - Existing Parquet data: read-only for every agent; new data goes to new paths/partitions.

A restructuring must therefore, at minimum: (a) keep every test in `tests/unit/`
passing and importable at its current module path (or update all `import
bybit_edge.…` references atomically with the move), (b) never reduce test count
without an explicit, logged decision, (c) never point any code at a write path
inside the harvest tree, and (d) keep the collector "smoke test" pattern viable —
short live-ingestion + parquet write-verify + schema comparison against the public
API — for any change touching the data/state layer.

---

## 4. Local machine couplings — every path an external scheduler or habit depends on

The user's machine root is `E:\Claude\Projects\scinance\` (this repo) with a sibling
project at `E:\Claude\Projects\Data Harvest\data-harvest\` (the harvester). **These
absolute paths appear throughout committed run logs and scripts — treat them as
load-bearing for the user's existing automation, not just documentation.**

### 4.1 Windows Scheduled Tasks (autostart / periodic)

| Task name | Script (repo-relative) | Trigger | Depends on path |
|---|---|---|---|
| **"Scinance C-36 Recorder"** | `start_recorder.ps1` (root) | `AtLogOn`, 30s delay, 3 restarts/1-min interval, no time limit | `%~dp0` (repo root) must stay the *installed* location — `install_recorder_autostart.ps1` bakes `$PSScriptRoot` as an absolute path into the registered task's `-File` argument at install time. Moving the repo silently orphans the task (it will keep pointing at the old path) until re-installed. |
| **"BybitOptChainSnap"** | `scinance2-impl/handoff_local/snap_bybit_optchain.ps1` | `-Once` + `RepetitionInterval 15 min`, registered via the `schtasks`/`Register-ScheduledTask` snippet documented in the script's own header | `-OutDir "E:\Claude\Projects\scinance\data\optchain_snaps"` — **hard-coded absolute path in the registration command itself** (not derived from `$PSScriptRoot`), so this one is registered once with a literal path baked in and does NOT self-heal on a repo move. Public REST only, no keys. ~0.5 MB/run, ~48 MB/day, ~1.4 GB/month. |
| **"Scinance Harvest Junction Guard"** (documented, registration optional) | `scinance2-impl/handoff_local/ensure_harvest_junction.ps1` | `ONLOGON`, `schtasks /Create … /TR "powershell … -File \"E:\Claude\Projects\scinance\scinance2-impl\handoff_local\ensure_harvest_junction.ps1\""` | Repairs the `data\harvest` junction if it goes dead (has happened twice: 2026-07-17, 2026-08-03/04). Target default: `env:HARVEST_JUNCTION_TARGET` else `E:\Claude\Projects\Data Harvest\data-harvest\data` — **a hard-coded sibling-project path**. Refuses to touch `data\harvest` if it is a *real* directory rather than a reparse point (safety stop, never deletes real data). |

### 4.2 The junction itself (not a scheduled task, but the single most load-bearing path)

```
E:\Claude\Projects\scinance\data\harvest  →(Windows Junction)→  E:\Claude\Projects\Data Harvest\data-harvest\data
```
Created manually (`New-Item -ItemType Junction -Path "data\harvest" -Target "E:\Claude\Projects\Data Harvest\data-harvest\data"`, per `README_H05B.md`) or auto-repaired by
the Junction Guard above. **Every research driver in `src/bybit_edge/research/`
assumes `data/harvest` resolves through this junction relative to the repo root.**
Moving either project directory breaks it silently until the guard task next runs
(or forever, if the guard isn't installed) — Read-only by policy (Schutzgut: "no
write access to the harvester tree").

### 4.3 All `.ps1`/`.bat` at repo root

`start.bat`, `start_recorder.ps1`, `install_recorder_autostart.ps1`,
`uninstall_recorder_autostart.ps1` — all four assume they live together at the repo
root (`start.bat` uses `%~dp0`, the `.ps1` files use `$PSScriptRoot`), so they are
relocatable as a group but not individually.

### 4.4 `scinance2-impl/handoff_local/` — one-command local runners

~40 `run_*.ps1` / matching `.sh` pairs (`run_h04b`…`run_h24`, `run_wave2/4/5`,
`run_wp0_barcache`…`run_wp6_stresszensus`, `run_overnight`, `run_short`,
`run_cfar_only`). Each is a documented "T2/T3" one-command runner per the
constitution's Testpyramide (§ below) — no required parameters, writes
`results/<run_id>/…` + a `SUMMARY_<date>.md`, and (per the constitution) "never
aborts on an open prompt." Several hard-code `E:\Claude\Projects\scinance` as a
`-RepoRoot`/`-HarvestBase` default (e.g. `run_wp6_stresszensus.ps1`:
`[string]$RepoRoot = "E:\Claude\Projects\scinance"`, `[string]$HarvestBase =
"E:\Claude\Projects\scinance\data\harvest"`) — these are overridable parameters,
but their *defaults* assume the canonical location.

Also here: `check_recording.py` (read-only recorder status, called by `start.bat`
option 3), `ensure_harvest_junction.ps1`, `harvest_coverage.py` (manifest coverage
query CLI), `aggregate_results.py`, `aggregate_wave2_fdr.py`, `aggregate_wave4_fdr.py`.

### 4.5 Paths that must NOT move without a coordinated update

1. `E:\Claude\Projects\scinance\data\optchain_snaps` — hard-coded in the
   `BybitOptChainSnap` scheduled task registration (not parameterized at the OS
   level; only the script's own `-OutDir` argument is a variable, but the *task's*
   stored argument string is fixed at registration time).
2. `E:\Claude\Projects\scinance` itself — baked into every registered Scheduled
   Task's `-File`/`-Argument` string, into the Junction Guard's own registration
   snippet, and into the `-RepoRoot`/`-HarvestBase` defaults of several `run_*.ps1`.
3. `E:\Claude\Projects\Data Harvest\data-harvest\data` — the junction target; the
   external harvester's own repo layout.
4. `data\harvest` (relative, inside this repo) — the junction mount point every
   Python driver's `--base-dir data/harvest` default assumes.
5. `logs\recorder\` — where `start_recorder.ps1` writes its timestamped logs;
   referenced by `start.bat`'s recorder-start menu text as the place to look.
6. `data\parquet\recording_f0\` — the recorder's own output root
   (`RECORDING_ROOT` in `storage.py`); currently unread by any driver but is the
   Schutzgut #1 output path nonetheless.

Any restructuring that changes the repo's root directory name/location, or moves
`data/harvest`, `data/optchain_snaps`, or `logs/recorder`, **must** re-run
`install_recorder_autostart.ps1` and re-register `BybitOptChainSnap` (and ideally
install the Junction Guard task if not already present) — none of these three
external OS-level registrations self-heal on their own from a plain `git mv`.

---

## 5. Environment

| Aspect | Value |
|---|---|
| Python version | `>=3.11` (`pyproject.toml` `requires-python`), pinned `python=3.11` in `environment.yml` |
| Package name | `bybit-edge` v0.1.0, "Bybit V5 algorithmic trading system with 26 quantitative methods" |
| Build backend | `setuptools>=68` + `wheel`, `[tool.setuptools.packages.find] where=["src"]` |
| Core deps | `websockets`, `aiohttp`, `duckdb>=0.10`, `polars>=0.20`, `numpy>=1.26`, `numba`, `scipy`, `statsmodels`, `pandas`, `python-dotenv`, `structlog`, `sortedcontainers`, `pykalman`, `filterpy`, `hmmlearn`, `PyWavelets` |
| Optional extras | `[gpu]` torch/torchvision/torchaudio/snntorch (2.3+/0.18+/CUDA); `[foundation]` momentfm/transformers>=4.46/peft (numpy 2.x-compatible, needed for py3.13 wheel availability, per an inline comment); `[dev]` pytest/pytest-asyncio/pytest-cov/ruff/mypy; `[dashboard]` streamlit/plotly; `[tuning]` optuna; `[vol]` lightgbm/scikit-learn |
| `environment.yml` (conda) | channels `pytorch, nvidia, conda-forge, defaults`; `python=3.11`, `pytorch::{pytorch,torchvision,torchaudio}`, `nvidia::pytorch-cuda=12.4`, `conda-forge::{duckdb,polars,numba}`, then `pip install -e ".[dev,gpu]"` |
| Test command | `pytest tests/unit/ -v --tb=short` (as invoked by `start.bat` option 1); `[tool.pytest.ini_options]` sets `testpaths=["tests"]`, `asyncio_mode="auto"` |
| Linting/typing | `ruff` (`target-version="py311"`, `line-length=100`), `mypy` (`python_version="3.11"`, `warn_return_any=true`, `warn_unused_configs=true`) — configured in `pyproject.toml` but not wired into any CI |
| CI | **None found** — no `.github/workflows/`, no other CI config in the repo. All testing is manual (`start.bat` / direct `pytest`) or via the local `run_*.ps1` handoff runners. |
| PYTHONPATH / `src` layout | Package installed editable (`pip install -e ".[dev]"` in `start.bat`'s `:install` routine and in `environment.yml`'s pip section) so `import bybit_edge` resolves normally once installed. Standalone `scripts/*.py` do **not** rely on the editable install — each does `sys.path.insert(0, str(Path(__file__).resolve().parent(s)[...] / "src"))` near its top before importing `bybit_edge.*`, so they run even without `pip install -e .` as long as they're invoked from within the repo tree. |
| `.gitignore` | `__pycache__/`, `*.pyc`, `.env`, `data/`, `*.duckdb`, `*.parquet`, `logs/`, `.pytest_cache/`, `*.egg-info/` — confirms no data, logs, or DB files are ever committed; `data/harvest` (the junction) is covered by the blanket `data/` ignore. |
| venv convention | `.venv\Scripts\activate.bat` (Windows) — `start.bat` checks for it and refuses to run without it (`:no_venv` branch tells the user to create one manually). |

---

## 6. Hardware / runtime notes

| Note | Source |
|---|---|
| Target machine: **NVIDIA GeForce RTX 5060 Ti** (Blackwell), CUDA 12.8+ / PyTorch 2.7+, **82 GB RAM**, Windows/WSL2 | `edge-research-v3/CLAUDE.md:109`, `scinance2-impl/state/wave5_state.md`, multiple `gate_log.md`/`audit_h*.md` entries; sandbox itself has no torch/no GPU — all GPU work is T3-LOCAL_LONG on this machine |
| The RTX machine described as a **"thin client"-adjacent, unattended overnight runner** — Testpyramide requires T3 runs to "never abort with an open prompt" and to log errors rather than stop, because the user is not watching | `scinance2-impl/CLAUDE.md` Testpyramide table; `audit_h16.md`: *"Der Nutzer prüft/testet 2 Wochen lang nichts"* |
| Bar cache memory limit: `RECYCLE_EVERY_DAYS = 200` day-queries per DuckDB connection, `memory_limit` default `"4GB"` with disk spill (`max_temp_directory_size=100GiB`) | `bar_cache.py` — triggered by a real 2026-08-14 OOM crash after ~4300 day-queries on one reused connection (DEC-36) |
| H-11c per-day memory: "~80 MB (1000×1440×6 float64) — unkritisch bei 82 GB RAM" | `state/audit_h12.md:171` |
| Documented run durations (verdict-relevant, quoted for planning future work) | |
| — WP-4 quote-spread census: **86 min**, rc=0 (2026-08-21) | `decisions.md:525` |
| — H-11c panel build: **90 minutes** (196M + 221M trades/symbol over 100 days), then crash — later fixed by the connection-recycle change above | `gate_log.md:1292` |
| — H-16 (c16_arrow): **~57h GPU** over 4 checkpoint/resume sessions | `gate_log.md:692` |
| — H-15 (c15_grammar): **~180h GPU** over 9 checkpoint sessions, spanning a Windows shutdown and a junction outage, reassembled bit-identically by the checkpoint system | `gate_log.md:840` |
| — H-18 (c18_leadlag_audit): **192s** total (self-test 12s + audit run), vs. ~1h estimate | `gate_log.md:642` |
| — H-14: ~226 full transformer trainings, **~2–3 GPU-days** total; H-17: ~105 trainings, ~1–2 days | `hypothesis_registry.md:350`, `:428` |
| A 3-stage checkpoint system (symbol → fold → surrogate, PCG64 RNG state + model weights) exists specifically to survive Windows restarts/timeouts across these multi-day/multi-hour unattended GPU runs | `gate_log.md:840` (commit `00a531d`), `gate_log.md:692` (commit `341d1d9`) |

---

## 7. Closing checklist — what a restructuring must preserve

**Data-layer assumptions (never violate, regardless of how src/ gets reorganized):**
- [ ] `data/harvest` stays read-only everywhere in the code — no write, no cache,
      no temp file inside that subtree (several modules assert this in comments and
      the bar-cache/tilt-store CLIs actively refuse an `--out-dir`/`cache_dir` under it).
- [ ] The 7-column harvest container schema
      (`ts_local_ns, ts_exchange_ms, topic, stream, symbol, payload_json, date`) and
      the manifest `partitions(exchange, stream, symbol, date, status)` schema are
      external contracts owned by the Data-Harvest project — do not "fix" or
      normalize them in this repo; read them defensively (as `payload_sql.py` does).
- [ ] Both `publicTrade` payload dialects (FLAT backfill vs. ENVELOPE live) must keep
      being read through `payload_sql.trade_rows_sql` / `cross_form_dedup_qualify` —
      any new trade loader that reads only top-level JSON keys reproduces the
      2026-07-17 silent-drop bug.
- [ ] `bar_cache.resolve_manifest_path()`'s preference for
      `harvest_manifest.backup.sqlite` over the legacy `harvest_manifest.sqlite` must
      survive — the legacy file is frozen and silently under-reports live-collected
      streams.
- [ ] `data/parquet/recording_f0/` keeps being written by the recorder even though
      unread — it is Schutzgut #1, not dead code to delete.

**Derived-store contracts:**
- [ ] Bar cache (`data/barcache/bars_1min/…`), L2 tilt store (`tilt_1min/…`), spread
      store (`spread_1min/…`) each keep their `SCHEMA_VERSION` + SHA-256
      fingerprint sidecar mechanism — any column/definition change must bump the
      version so old and new partitions are never silently mixed (all three modules
      enforce this by raising on mismatch).
- [ ] The "loud-fail on 0 parsed trades from N>0 raw rows" behavior (bar cache,
      L2 replay's `discarded` sidecar) must be preserved — it exists specifically
      because a silent empty day previously corrupted a registered gate verdict
      (GL-018 lesson, cited directly in `bar_cache.py`'s docstring).
- [ ] `extract_spread_window`'s guarantee of never touching the `tilt_1min` files
      it sits beside (proven by test) must survive any refactor of `c22_l2tilt/`.

**Test/replay contracts:**
- [ ] Every test currently under `tests/unit/` (100+ files) must remain importable
      and green at whatever new module path replaces `bybit_edge.*` — this satisfies
      the constitution's "extended, never reduced" rule for the "existing test
      suite (88+ tests)."
- [ ] `pytest tests/unit/ -v --tb=short` (or an equivalent single command) must keep
      working as the one-command entry point `start.bat` option 1 relies on.
- [ ] `tests/fixtures/{c42,e15}/` content and relative paths must move together with
      whatever tests reference them (`test_c42_rv.py`, `test_e15_eval.py`) — they are
      small (5.6 MB) and synthetic, safe to relocate but not to regenerate carelessly
      since `e15` fixtures encode specific DROP/GRAUBEREICH/WEITER gate scenarios.
- [ ] `tests/backtests/` and `tests/integration/` currently hold nothing but
      `__init__.py` — safe to keep, populate, or consolidate, but any restructuring
      that removes them should not be read as "reducing the test suite" since they
      hold no tests today; don't silently delete them either without a decision log
      entry (constitution requires DEC-xx logging for every non-obvious call).

**Local-machine contracts (must be re-registered, not just moved):**
- [ ] Repo root path `E:\Claude\Projects\scinance` — baked into 3 separate Windows
      Scheduled Task registrations (recorder autostart, BybitOptChainSnap, harvest
      junction guard) and into several `run_*.ps1` defaults; a repo move requires
      re-running `install_recorder_autostart.ps1` and re-registering
      `BybitOptChainSnap` with a new `-OutDir`, or those tasks keep firing against a
      now-stale path.
- [ ] `data\harvest` junction mount point and its target
      `E:\Claude\Projects\Data Harvest\data-harvest\data` — external to this repo;
      any change to either side needs `ensure_harvest_junction.ps1`'s
      `HARVEST_JUNCTION_TARGET` env var updated or the guard script edited.
- [ ] `data\optchain_snaps` — hard-coded in the `BybitOptChainSnap` task's stored
      argument string (15-min cadence); moving it silently breaks that task until
      manually re-registered.
- [ ] `logs\recorder\` — referenced by both `start_recorder.ps1` (writer) and
      `start.bat`'s menu text (documentation for the user); keep in sync if renamed.

**Environment contracts:**
- [ ] `[tool.setuptools.packages.find] where=["src"]` and the editable-install
      convention (`pip install -e ".[dev]"`) must keep resolving `import
      bybit_edge` the same way, since standalone `scripts/*.py` fall back to a
      `sys.path.insert(…, "src")` shim that assumes the package still lives under
      `src/bybit_edge/` at a fixed relative depth from each script.
- [ ] Python floor stays `>=3.11` (pinned in both `pyproject.toml` and
      `environment.yml`) — the `[foundation]` extra's numpy-2.x compatibility
      comment signals this was a deliberate, considered choice, not an oversight.
- [ ] No CI exists today — a restructuring is free to add one, but must not assume
      one is currently enforcing anything; the actual quality gate is the manual
      `pytest tests/unit/` + the local `run_*.ps1` handoff runners + the
      constitution's "Collector-Smoke-Test" for any data/state-layer touch.
