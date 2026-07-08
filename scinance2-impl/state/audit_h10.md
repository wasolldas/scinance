# Audit H-10 (F-POINTER, `c10_pointer`) — adversarial code audit

- **Auditor:** independent adversarial auditor (did not write this code)
- **Datum:** 2026-07-08
- **Gepruefte Artefakte:** `src/bybit_edge/research/c10_pointer/{__init__,loaders,cropper,stats,driver}.py`,
  `scripts/c10_pointer.py`, `scinance2-impl/handoff_local/run_h10.{ps1,sh}`,
  `scinance2-impl/handoff_local/README_H10.md`, `tests/unit/test_c10_pointer.py`
- **Ground truth:** `edge-research-v3/results/deep_validation/hardened_hypotheses.md` (H-10-Abschnitt, Z. 37–53),
  `scinance2-impl/state/hypothesis_registry.md` (Welle-4-Eintrag H-10, Z. 241–256), `edge-research-v3/CLAUDE.md` §2.

---

## Verdict: **FAIL**

One judgment-bearing pre-registration violation (BUG-1: the RV detection-series definition deviates
from the registered spec, and is rationalized in code/README by a registry quote that **does not exist
in either ground-truth document**). Under CLAUDE.md §2 rule 4 ("Pre-Registration, keine
Torpfosten-Verschiebung — in KEINE Richtung") a run with this code would be non-adjudicable against
the H-10 registry entry; the gate-auditor would have to void it. Everything else is solid to very
good — after fixing BUG-1 (and ideally BUG-2/3/4) this would be PASS-WITH-NOTES.

Pytest was run by the auditor: **16 passed, 0 failed, 3.5 s** (`PYTHONPATH=src python3 -m pytest tests/unit/test_c10_pointer.py -q`).

---

## Spec-fidelity check

| Constant / rule | Registered value (registry + hardened doc) | Code value | Match? |
|---|---|---|---|
| Detection series | 30 = 5 Symbole × {bybit, binance} × {RV, Funding, ΔlogOI} | `DEFAULT_SYMBOLS`(5) × `DEFAULT_EXCHANGES`(2) × `DETECTION_METRICS`(3), deterministic order | YES |
| Hold-out target | Deribit dvol BTC+ETH, never in detection | loaded separately (`load_daily_dvol`, symbols `BTC`/`ETH`); not in panel; test asserts | YES |
| **RV series definition** | **RV = log Σ r²(1-min-Last-Price) je Tag** (hardened doc Z. 45; registry silent) | **(Δlog daily-close price)² — daily bar instead of 1-min bars, and NO outer log** | **NO — BUG-1** |
| Funding series | Tagesmittel | daily `avg(fundingRate)` | YES |
| ΔlogOI series | log-Tagesänderung (Tagesschluss) | `arg_max(openInterest, ts)` day close, then dlog | YES |
| Daily grid | 2026-03-27..2026-07-04 UTC | `DEFAULT_DATA_START/END` identical | YES |
| Burn-in | 21 Tage, nutzbar ab 2026-04-17 | `DEFAULT_BURN_IN_DAYS=21`; test asserts `DAYS[21]=="2026-04-17"` | YES |
| W1 / W2 | 2026-04-17..05-25 (39 d) / 2026-05-26..07-04 (40 d) | `DEFAULT_WINDOWS` identical; runner passes same values | YES |
| Detrending | trailing 63-Tage-Median, min_periods=21, kein Lookahead | `DETREND_WINDOW=63`, `DETREND_MIN_PERIODS=21`, trailing (t-62..t) | YES |
| Cropper window | 11 Tage zentriert | `CROPPER_HALF_WINDOW=5` → 11 centred | YES |
| Anomaly threshold | \|C\| ≥ 1.5 | `C_THRESH=1.5` | YES |
| Pointer-day share | ≥ 0.60 | `SHARE_FLOOR=0.60` (+1e-12 boundary guard; 18/30 boundary test passes) | YES |
| Availability floor | n_avail ≥ 18, sonst Tag ausgeschlossen | `N_AVAIL_FLOOR=18` | YES |
| Stage-1 null | 1.000 zirkuläre Surrogate je Serie, uniform Offset, auf der C-Zeitreihe | 1000 circular rolls of the score columns; offsets `1..T_u-1` (0 excluded — minor unregistered detail) | YES (note N-3) |
| Stage-2 null | 1.000 Permutations-Ziehungen gleich großer Tagesmengen, ≥6 Tage Abstand zu JEDEM Pointer-Tag, Nicht-Pointer-Tage des Fensters | `n_draws=1000`, `MIN_NULL_GAP_DAYS=6`, in-window pool, gap to ALL pointer days (both windows), without replacement | YES |
| Stage-2 statistic | S = Mittel Δpre über Pointer-Tage; Δpre = Mittel(D,[t−5,t−1]) − Mittel(D,[t−15,t−6]); p zweiseitig | `PRE_NEAR=(5,1)`, `PRE_FAR=(15,6)`, slices verified strictly pre-event; two-sided `min(1, 2·min(p_lo,p_hi))` | YES |
| **dvol index D_t** | hardened: **Mittel der z-standardisierten Tagesschlüsse** (z je Serie, dann Mittel; über den NUTZBAREN Zeitraum); registry (terser): "z-standardisiertes Mittel" | z(mean(levels)) — mean first, then one global z; input is the daily **MEAN** of dvol, not the Tagesschluss; z over the FULL grid incl. burn-in | **PARTIAL — BUG-2** |
| N-floor | N_pointer ≥ 3 je Fenster, NICHT absenkbar | `N_POINTER_FLOOR=3`; `n_pointer_floor_lowerable:false` in payload; enforced in `cell_pass` | YES |
| Gate p-threshold | p ≤ 0.05 je Zelle | `SURROGATE_P_MAX=0.05` | YES |
| FDR family | F-POINTER, 4 Zellen (2 Stufen × 2 Fenster), BH α=0.10 | `FDR_FAMILY="F-POINTER"`, 4 cells built, `FDR_ALPHA=0.10`, OWN BH copy in `stats.py` (no cross-import) | YES |
| Seeds / determinism | not registered | seed 42 (stage 1), 1042/1043 (stage 2), fixed in runner; reproducibility test passes | YES (OK) |
| Neuwirth crosscheck | "wird mitberichtet, nicht-urteilstragend" (hardened Z. 45; registry: "nicht-urteilstragend") | **not implemented, not reported anywhere** | NO — BUG-6 (non-judgment-bearing) |
| Compute tag | CPU, Sekunden | numpy/DuckDB CPU only; e2e test runs in seconds | YES |
| Gate-neutrality | gate-auditor adjudicates | payload has per-cell flags + `all_four_cells_pass`, no `verdict` field (test asserts) | YES |

---

## Bugs found

### BUG-1 — HIGH (pre-registration violation, judgment-bearing) — RV series is not the registered RV
- **Files:** `src/bybit_edge/research/c10_pointer/loaders.py:9-14, 270-285`; `scinance2-impl/handoff_local/README_H10.md:56-59`
- The hardened spec (the only ground-truth document that defines the series) registers
  **RV = log Σ r²(1-min-Last-Price) je Tag** — the log of the sum of squared 1-minute last-price
  log-returns per day. The code computes ONE daily-bar last price (`arg_max(price, ts)` per date
  partition) and uses the **single squared daily log-return, without the outer log**
  (`rv_from_daily_last_price`). Two independent deviations: (a) daily instead of 1-min sampling —
  a completely different (far noisier) volatility measurement; (b) missing log transform — the raw
  squared return is extremely heavy-tailed, which changes which days the Cropper score flags as
  anomalies. 10 of the 30 detection series are affected, so the stage-1 pointer-day set itself is
  not the registered one.
- **Aggravating:** both `loaders.py` and `README_H10.md` justify this with the alleged registry
  wording *"Last-Price je Tages-Bar, log-Return-Quadrate summiert"*. That phrase appears **nowhere**
  in `hypothesis_registry.md` or `hardened_hypotheses.md` (grep verified — it exists only in the
  builder's own README/docstrings). This is a goalpost shift disguised as spec fidelity; no DEC-xx
  entry in `state/decisions.md` covers it.
- **Fix:** build 1-min last-price bars per day from `publicTrade` (same DuckDB pattern as the 5-min
  bars in c07/c08: `arg_max(price, ts)` per 60 s bucket), compute `rv_day = log(Σ (Δlog p_1min)²)`
  (NaN if the day has too few bars — pick and document a floor), keep everything downstream
  unchanged. Remove the fabricated quote from README/docstrings. Estimated effort: small (one SQL
  bucketing change + one function).

### BUG-2 — MEDIUM (spec fidelity, held-out target) — dvol index construction deviates from the hardened spec
- **Files:** `src/bybit_edge/research/c10_pointer/loaders.py:227-263` (`load_daily_dvol`), `stats.py:143-167` (`dvol_index`), `driver.py:133`
- Three deviations: (a) hardened spec says **Tagesschlüsse** (daily closes) — code aggregates the
  daily **mean** of dvol; (b) hardened spec z-standardizes EACH series first, THEN averages
  ("Mittel der z-standardisierten … Tagesschlüsse") — code averages the raw levels first, then
  applies one global z (`z(mean)` instead of `mean(z)`; not equivalent when BTC/ETH dvol scales
  differ, which they do). The registry's terser wording ("z-standardisiertes Mittel") happens to
  read like the code, i.e. the two ground-truth documents disagree — the code silently picked the
  weaker reading without a DEC entry; (c) standardization runs over the FULL grid incl. burn-in
  instead of "über den nutzbaren Zeitraum" (this one is p-invariant — affine transforms cancel in
  Δpre differences and in the permutation p — but the reported S value differs).
- **Fix:** use `arg_max(v, ts)` (day close) in `load_daily_dvol`; compute
  `D = nanmean(z(btc_close[usable]), z(eth_close[usable]))`; record the interpretation as a DEC.

### BUG-3 — MEDIUM (unattended-run safety) — silent all-NULL extraction when Binance payload field names are wrong
- **Files:** `src/bybit_edge/research/c10_pointer/loaders.py:159-182, 300-349`
- `DataError` (and the panel-level WARN) fires only when partition DIRECTORIES are missing. If the
  files exist but the JSON field guess is wrong, `WHERE v IS NOT NULL` filters every row and the
  series comes back **all-NaN with no warning at all**. This is realistic: DATASET.md §6 says
  Binance funding/OI payloads are **"ccxt-normalisierte Dicts"** — ccxt's unified open-interest
  structure uses top-level `openInterestAmount`/`openInterestValue` (the raw `sumOpenInterest`
  lives NESTED under `info`, which `$.sumOpenInterest` does not reach). So the 5 Binance ΔlogOI
  series plausibly load as all-NaN in the real run, shrinking the effective panel to 25 with zero
  trace in the JSON payload (no per-series coverage stats are emitted). A missing exchange/stream
  is then indistinguishable from a genuine power-DROP in the results.
- **Fix:** (i) add `$.openInterestAmount` and `$.info.sumOpenInterest` to the COALESCE candidates
  (same for funding: `$.info.fundingRate` as a third fallback); (ii) in `build_detection_panel`,
  WARN whenever a stream's partitions exist but parse to 0 finite days; (iii) add per-series
  `finite_days` counts to the JSON payload so the gate-auditor can audit coverage post hoc.

### BUG-4 — MEDIUM (unattended-run safety) — dvol first-numeric-field fallback can silently pick a timestamp
- **File:** `src/bybit_edge/research/c10_pointer/loaders.py:185-224` (`parse_dvol_value`)
- If none of the candidates (`dvol,value,index_value,close,price`) is present, the parser takes the
  FIRST numeric top-level field in dict order. Deribit-style payloads commonly carry a leading
  epoch `timestamp` field; a payload like `{"timestamp": 1750..., "volatility": "55.2"}` would make
  the "dvol index" a near-monotonic time ramp (note `volatility` is NOT in the candidate list).
  Only a single stderr WARN is emitted — nobody reads stderr during a 2-week unattended run, and
  the resulting stage-2 numbers would look superficially plausible. This is the closest thing in
  the module to fabricated data.
- **Fix:** add `volatility` (and `mark_iv`) to `DVOL_FIELD_CANDIDATES`; in the fallback, skip keys
  matching `time|ts|stamp|date|seq|id` and reject values > 1e6 (dvol is a percent-scale index);
  surface the fallback in the JSON payload (e.g. `dvol_parse_mode` field), not only stderr.

### BUG-5 — MEDIUM (unattended-run safety) — CLI does not fail when the held-out target has zero usable days
- **File:** `scripts/c10_pointer.py:110-119`
- `load_daily_dvol` raises only when partitions are absent. If partitions exist but every row
  parses to NaN (BUG-4 family), the CLI prints "BTC 0 / ETH 0 days with data" to stderr and
  **continues with rc=0**; stage-2 p becomes undefined → mapped to 1.0 for BH → the run emits a
  complete-looking DROP payload manufactured from unparseable data. Same class of issue for a
  detection panel that loads with < 18 non-empty series (structurally zero pointer days).
- **Fix:** return rc=1 (or a distinct rc) when `finite(dvol_btc)+finite(dvol_eth)` usable days < a
  floor (e.g. 30) or when `n_nonempty < N_AVAIL_FLOOR`; the runner then reports FAIL instead of a
  pseudo-result. Relatedly, `run_h10.ps1/.sh` pre-check only `raw/bybit/publicTrade` and
  `raw/deribit/dvol` — Binance and the funding/OI streams are unchecked (add them to the SKIP check).

### BUG-6 — LOW (registered co-report missing) — Neuwirth window crosscheck not implemented
- **Files:** whole module
- Hardened spec: "der Neuwirth-Fenster-Crosscheck wird mitberichtet, ist aber nicht-urteilstragend
  (schließt Method-Shopping aus)". Nothing in the module computes or reports it. Non-judgment-
  bearing, but it is part of the registered anti-method-shopping evidence and should appear in the
  payload/markdown as a secondary diagnostic.

### Notes (no fix required, documented for the record)
- N-1: Stage-1 surrogate offsets are drawn from `1..T_u-1` (0 excluded). Spec says "uniform
  zufälliger Offset"; exclusion of 0 is unregistered but numerically negligible (30 independent
  offsets; +1-corrected empirical p).
- N-2: Unregistered robustness parameters, all documented in docstrings and reasonable:
  `CROPPER_MIN_FINITE=6` (of 11), `delta_pre` min-finite 3/5 near and 6/10 far. They only ADD NaN
  handling; they cannot flip a defined value.
- N-3: `run_h10.sh` falls back to NO timeout when the `timeout` binary is absent (rare on target
  systems; the ps1 side always enforces 2400 s).
- N-4: IC-DEND-2 (time-axis integrity Bybit/Binance/Deribit) is a registered SHOULD-precondition
  ("Vorbedingung, kein Gate-Bestandteil") and is not run by the runner — acceptable per registry
  wording, but worth executing before the 2-week window.
- N-5: `c01_ofi_sign/oos.py` (out of scope, pre-existing) has an SQL `AND/OR` precedence smell in
  its WHERE clause; the new c10 loaders do NOT inherit it.

---

## Test coverage assessment

`PYTHONPATH=src python3 -m pytest tests/unit/test_c10_pointer.py -q` → **16 passed, 3.5 s** (run by this auditor, not taken from a stale claim).

Present and adequate:
- Registered gate arithmetic exercised directly: 18-of-30 = 0.60 boundary INCLUSIVE, n_avail 17 → no
  pointer, direction sign, N-floor=3 hard path (2 pointer days per window never pass even with tiny p),
  `n_pointer_floor_lowerable=false` asserted.
- NULL control (30 independent series → 0 pointer days, p > 0.05, no pass) and POSITIVE detection
  (synchronized spikes on 3 days/window + correlated dvol pre-drift → all 4 F-POINTER cells pass,
  `n_fdr_significant == 4`) — both real statistical controls, not smoke tests.
- Seed reproducibility test; burn-in window rejection test; own-BH unit test; Δpre strictly-pre-event
  test; Cropper closed-form mini-example (C = 10/√11).
- capital_free: `capital_free is True` + token scan (bps/pnl/sharpe/friction/slippage/edge) over the
  full JSON blob; hold-out declared and absent from the 30 detection names.
- End-to-end CLI subprocess run against a synthetic Hive tree with the harvester layout
  (`raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet`, `ts_exchange_ms` + `payload_json`
  columns) covering ALL 4 streams and two different dvol field spellings; asserts rc=0, valid JSON,
  4 cells, no `verdict` field, German gate-neutral markdown.

Gaps (all consequences of the bugs above):
- No test pins the RV series to the REGISTERED 1-min definition — the synthetic tree writes only 2
  trades/day, so the daily-bar shortcut (BUG-1) is invisible to the suite.
- No negative test for silent all-NULL extraction when a stream's field names mismatch (BUG-3), and
  no test that the dvol fallback refuses timestamp-like fields (BUG-4).
- No test that the CLI fails on a zero-usable-dvol tree (BUG-5).
- Runner scripts have a dry-run mode but no test drives it (other waves have the same convention;
  low priority).

## capital_free check result

**PASS.** `grep -rniE '\bbps\b|pnl|sharpe|friction|edge_|slippage|fee'` over the module, CLI and both
runners: zero hits (only the `bybit_edge` package namespace, which never enters the payload).
Payload sets `capital_free: true`; no capital-metric key exists in `run()`'s output construction;
the unit test re-checks the serialized JSON on every run. Friction arithmetic from the registry
entry appears nowhere in code (correct — that is H-10b material).

## T2 runner check result

**PASS (with the SKIP-precheck gap noted in BUG-5).** Checked against all known runner bug classes:
- Script path IS the first CmdArg, before all `--flags` (run_h05c bug class avoided; explicit comment at `run_h10.ps1:143`, `run_h10.sh:74`).
- `$null = $p.Handle` handle-cache present (`run_h10.ps1:96`) plus the `ExitCode -eq $null → rc=-2` quirk guard.
- BelowNormal priority on both the runner process and the child (`:55`, `:97`).
- Encoding: `file` reports pure ASCII; PS 5.1-compatible constructs only; no here-strings with smart quotes.
- Never blocks interactively: no `Read-Host`/`pause`; `-NoNewWindow` + redirected stdout/stderr.
- Timeout: 2400 s via `WaitForExit(ms)` + kill (ps1) and `timeout(1)` (sh; falls back to unbounded only if the binary is missing — note N-3).
- Writes `SUMMARY_<date>.md` (UTC-datestamped) plus `steps.tsv` and per-step logs under `results/h10_<timestamp>/`.
- Deterministic exit codes 0/1/2 (OK/FAIL/SKIP) in both scripts; dry-run mode (`HANDOFF_DRY_RUN`, `HANDOFF_DRY_RC`) present.
- All registry constants passed explicitly to the CLI and printed into the SUMMARY header (grid, windows, 1000/1000, seed 42, FDR a=0.10, N-floor 3).

## Loader-fallback-safety check result

**PASS on the critical criterion, with MEDIUM caveats.** There is **no mock/synthetic data fallback
anywhere**: missing partitions raise `DataError`; the CLI exits 1 when the whole panel or the dvol
tree is unloadable; the runner SKIPs (exit 2) when the junction/hold-out paths are absent. Missing
individual series become all-NaN with a stderr WARN and are absorbed by the registered n_avail≥18
floor — spec-conformant. The residual risks are silent-degradation, not fabrication: field-name
mismatches parse to all-NULL without any warning (BUG-3), the dvol first-numeric fallback can latch
onto a timestamp (BUG-4), and the CLI keeps rc=0 with a zero-day hold-out (BUG-5). None of these
invents data, but during a 2-week unattended run each could convert a data-plumbing failure into a
plausible-looking DROP payload. Fix BUG-3/4/5 before the run.

---

*Audit basis: full read of all listed files; grep verification of every quoted spec constant against
both ground-truth documents; pytest executed live (16 passed). Verdict FAIL rests on BUG-1 alone;
BUG-2..5 are strongly recommended pre-run fixes, BUG-6 and the notes are hardening.*
