# AUDIT H-09 (F-BUNCH) — Adversarial Code Audit (fresh auditor, 2026-07-08)

**Scope:** `src/bybit_edge/research/c09_bunch/{__init__,kinks,estimator,stats,driver}.py`,
`scripts/c09_bunch.py`, `scinance2-impl/handoff_local/run_h09.{ps1,sh}`, `README_H09.md`,
`tests/unit/test_c09_bunch.py` — audited against
`edge-research-v3/results/deep_validation/hardened_hypotheses.md` (H-09 section),
`scinance2-impl/state/hypothesis_registry.md` (Welle 4, H-09 entry) and
`edge-research-v3/CLAUDE.md` §2. Tests executed live in this sandbox (see below).

---

## Verdict: **FAIL** (two blocking operational defects; statistical core is spec-faithful)

The estimator, gate criteria, FDR family definition, thresholds and capital_free hygiene
are faithful to the registered H-09 entry, and the full test suite passes (10/10, run
live). The FAIL is driven by two HIGH-severity operational defects in the data path that
threaten an unsupervised 2-week local run: (1) silent truncation of the pre-registered
windows via the 50M-tick loader cap — per the program's OWN feasibility numbers
(hardened_hypotheses.md, "10⁸–10⁹ Fills … je 50-Tage-Fenster" for BTC) the cap will
almost certainly bind on exactly the one registry-quoted symbol, with no truncation flag
in the payload; and (2) all 10 windows are materialized in RAM simultaneously (~40–55 GB
peak at the cap, plus DuckDB sort memory) — realistic OOM/timeout risk on the 82-GB
target. Both fixes are small and localized. Everything else is notes.

---

## Spec-fidelity check

| Constant / threshold | Registered value (registry H-09 / hardened doc) | Code value (file) | Match? |
|---|---|---|---|
| Windows W1 / W2 | 2026-03-27..2026-05-15 / 2026-05-16..2026-07-04 | `driver.py:72-73`, CLI defaults, both runners | YES |
| Window end inclusive | ~50 days each | `scripts/c09_bunch.py:_span_days` + `spill_days` → date dirs start..end inclusive | YES |
| Panel | 5 Bybit USDT-Perps | `scripts/c09_bunch.py:44` BTC/ETH/SOL/BNB/XRP | YES |
| Observation unit | Taker-Order-Aggregat: consecutive publicTrade, same (symbol, side, ts_exchange_ms), notional = Σ(price×size) | `estimator.aggregate_orders` (76-100) | YES |
| Estimation band | [0.40·K_s, 1.30·K_s) | `kinks.py:63-64` (0.40 incl., 1.30 excl., verified `bin_notionals`) | YES |
| Bin width / count | 0.01·K_s / 90 bins | `kinks.py:65-66` | YES |
| Counterfactual | polynomial degree 7, fit excluding [0.90, 1.10)·K_s | `kinks.py:69-71`; bins 50..69 excluded (`estimator.py:60-71`, test-verified) | YES |
| B− | [0.95·K_s, 1.00·K_s) | bins 55-59 (`estimator.py:62-63`) | YES |
| B+ | (1.00·K_s, 1.05·K_s] | bins 60-64 + boundary fidelity: mass ==K excluded, ==1.05K included (`estimator.py:157-161`) | YES |
| Excess-mass formula | b̂ = Σ(obs−cf over window) / mean cf bin count in window (Chetty 2011) | `estimator.excess_mass` (170-200) | YES |
| Significance | residual bootstrap, 500 reps, null b−=0, p(b̂−>0)≤0.05 one-sided | `estimator.residual_bootstrap_p`; `N_BOOTSTRAP=500`, `BOOT_P_MAX=0.05`; add-one convention (repo standard, conservative) | YES |
| Placebos | P1=0.50·K_s, P2=0.75·K_s, same procedure, NOT in FDR family | `kinks.py:80`, `estimate_cell` re-runs full estimator at pseudo-kink; placebo p never enters `p_values` | YES |
| N-floor | ≥2,000 orders in band AND cf expectation in B− ≥50, else cell invalid | `kinks.py:92-93`, enforced in `estimate_cell` → `cell_valid` | YES |
| Power-DROP path | all 5 cells of one window invalid → DROP | reported gate-neutrally as `all_cells_invalid_by_window` (`driver.py:209-212`) | YES |
| Gate (4 conditions) | FDR-surviving p≤0.05 AND b̂−≥1.0 AND b̂−−b̂+≥0.5 AND b̂− > max(b̂_P1,b̂_P2), valid cell, ≥1 symbol in BOTH windows | `driver.py:176-214` (`passed`, `passed_both_windows`, `weiter_indication`); strict `>` for placebo dominance | YES |
| FDR family | **F-BUNCH = fixed 10 tests** (5 symbols × 2 windows, order level), BH α=0.10 | BH over *cells actually loaded* — shrinks below 10 if a symbol fails to load (Bug 3) | **PARTIAL** |
| BH-FDR | own copy, no cross-import | `stats.py` own implementation, imports only `kinks.FDR_ALPHA`; algorithm verified correct (step-up, ties, empty input) | YES |
| K_s BTCUSDT | 2,000,000 USDT (MMR 0.50%→0.56%) | `kinks.py:45` | YES |
| K_s ETH/SOL/BNB/XRP | operationalisation addendum required BEFORE run | PLACEHOLDER values, loudly flagged (see Placeholder section) | YES (flagged) |
| Fill-level robustness | "Fill-Level als nicht-urteilstragende Robustheit mitberichtet" | **not implemented anywhere** (order level only) | **NO** (Bug 6) |
| capital_free | true, no friction wall reference | `capital_free: true` in payload, zero cost columns | YES |
| Compute tag | CPU | numpy/duckdb only, no GPU | YES |
| Seed / determinism | (not registered; README: Seed 42) | seed 42 + deterministic per-cell offsets (`_stable_symbol_offset`, not `hash()`) | YES |

No unexplained numeric deviation was found in the estimator or gate constants. The two
non-matches are Bug 3 (family shrinkage) and Bug 6 (missing fill-level co-report).

---

## Bugs found

### HIGH

**Bug 1 — Silent truncation of the pre-registered windows (loader tick cap).**
`driver.py:77` (`WINDOW_MAX_TICKS = 50_000_000`), `scripts/c09_bunch.py:69,97-101`.
`load_harvest_window` returns the FIRST `max_ticks` records at/after window start
(`ORDER BY ts_exchange_ms LIMIT max_ticks`). The hypothesis's own feasibility check
(hardened_hypotheses.md H-09) estimates 10⁸–10⁹ fills per 50-day window for BTC —
i.e. the 50M cap binds with high probability on exactly the registry-quoted symbol,
so the "W1" cell would actually measure only the first ~5–25 days of W1 while the
payload labels it as the full registered window. Nothing in the payload records
`max_ticks`, first/last loaded timestamp, or a truncation flag; `gate_valid_assumptions`
stays `true`. This is a silent pre-registration violation (registered windows not
honoured) that the gate-auditor can only catch by knowing to compare `n_records_raw`
against the cap constant.
*Fix:* record `max_ticks`, first/last loaded ts and `window_truncated = (n_records_raw
== max_ticks)` per cell; a truncated cell must at minimum void `gate_valid_assumptions`
(better: mark the cell invalid). Structurally better: push the order aggregation into
DuckDB (`GROUP BY ts_exchange_ms, side` + `SUM(price*size)`) so only per-order notionals
(~10⁷ floats) ever reach Python and the cap becomes unnecessary.

**Bug 2 — All 10 windows materialized in RAM before `run()`; OOM/timeout risk.**
`scripts/c09_bunch.py:91-111` builds `symbol_windows` for all 5 symbols × 2 windows and
keeps every raw `TradeArrays` alive until `run()` finishes. At the cap, each window is
~4.2 GB retained (3 float64 arrays + object-dtype side array with ~52 B per "Buy"/"Sell"
string) → ~42 GB retained for 10 windows, plus a ~10 GB transient `fetchall()` list of
50M tuples per load, plus DuckDB's own external-sort memory over ~10⁸ rows → ~52+ GB
peak on the 82-GB target machine, unsupervised, at BelowNormal priority under a
7,200 s runner timeout. A crash (OOM) or rc=124 timeout would waste the night run and
leave no JSON.
*Fix:* aggregate each window immediately after load (`aggregate_orders` reduces a 50M-
record window to a small float64 notional array) and drop the raw arrays before loading
the next window — or do the aggregation in DuckDB (same fix as Bug 1). Only per-window
notional arrays should be passed to `run()`.

### MEDIUM

**Bug 3 — FDR family silently shrinks below the registered 10 tests.**
`scripts/c09_bunch.py:107-116` drops any symbol that fails to load both windows and
proceeds (rc=0) as long as ≥1 symbol survives; `driver.py:174-175` then runs BH with
`m = len(cells) < 10`. The registered F-BUNCH family is FIXED at 10 tests; a smaller m
makes the BH thresholds (rank/m·α) larger → anti-conservative. The comment at
`driver.py:171-173` ("the fixed family size is not shrunk") is only true for invalid
cells, not for dropped symbols. *Fix:* on a partial panel either exit nonzero, or pad
the family to m=10 with p=1.0 sentinel cells and set an explicit
`family_size_deviation` flag; at minimum void `gate_valid_assumptions`.

**Bug 4 — Anti-gaming flag does not cover panel/window identity.**
`kinks.gate_assumptions_valid` (96-124) + `driver.py:127-132` check only bootstrap
reps, poly degree and the two floors. The CLI accepts `--symbols` and `--window-*`
overrides; a run on different windows or a different panel still reports
`gate_valid_assumptions: true`. The payload does carry `window_labels`/`symbols`, so
the auditor CAN detect it, but the flag's documented semantics ("a WEITER reading is
ONLY gate-valid …") overpromise. *Fix:* also compare window labels against
`DEFAULT_WINDOW_A/B` and the panel against the registered 5 symbols inside `run()`.

**Bug 5 (medium-low, inherited) — SQL operator-precedence bug in the shared loader.**
`src/bybit_edge/research/c01_ofi_sign/oos.py:138-140` (bestand, reused read-only):
`WHERE A AND B AND C OR D` parses as `(A AND B AND C) OR D`, so LIVE-form rows
(`$.S` present) bypass both the `ts_exchange_ms IS NOT NULL` guard and the
`ts >= start_ms` window filter — out-of-window leakage bounded by the date partitions,
and a NULL-ts live row would crash the numpy conversion. For H-09's backfill windows
(`side` key present) the correct branch applies, so real impact is data-form dependent,
but window-boundary integrity should not rest on that assumption. Pre-existing bug that
also affects H-05b/H-05c; fixing it is a bestand change (own WP, Schutzgut process):
parenthesize `(side IS NOT NULL OR S IS NOT NULL)`.

### LOW

**Bug 6 — Registered fill-level robustness co-report missing.** Both ground-truth
documents register "Fill-Level als nicht-urteilstragende Robustheit mitberichtet".
The package reports order level only. Not judgement-bearing, but the registered
deliverable is incomplete; the gate-auditor should be told it is absent.

**Bug 7 — No direct unit test for the c09-own BH copy.** Every sibling package tests
its own `benjamini_hochberg` directly (test_c10_pointer.py:124, test_c42_rv.py:376,
test_c06_xmr.py:195, test_c17_c41_lead_lag.py:326); test_c09_bunch.py exercises it only
indirectly. (I hand-verified the implementation; it is correct, including ties, step-up
and empty input.)

**Bug 8 — `weiter_indication` can be driven by a placeholder-kink symbol.**
`driver.py:213-214`: the headline flag is not conditioned on `kink_is_placeholder`.
Per-cell/per-symbol placeholder flags exist, so the auditor can catch it, but a `true`
headline on an unverified K_s is a foot-gun for the morning evaluation.

**Bug 9 — Window disjointness rests on an undocumented partition assumption.** The SQL
has no upper `ts` bound (only `>= start_ms`); W1/W2 separation relies on the hive
`date=` partition equaling the UTC date of `ts_exchange_ms`. A mislabeled partition
would double-count records at the W1/W2 seam. Worth one assert/comment.

**Info (no action forced):** (a) DuckDB `ORDER BY ts_exchange_ms` is not stable —
within-millisecond Buy/Sell interleavings may be reordered between runs, slightly
changing which records are "consecutive" for aggregation (reproducibility caveat on the
registered merge definition). (b) `gate_assumptions_valid` accepts n_bootstrap>500 and
raised floors — deviations in the *stricter* direction also violate "in keine Richtung
verschiebbar" but are treated as valid (CLI only exposes n_bootstrap/seed, so exposure
is minimal).

---

## Test coverage assessment

`PYTHONPATH=src python3 -m pytest tests/unit/test_c09_bunch.py -q` executed live in
this audit: **10 passed in 3.11 s** (1 unrelated pytest config warning). Coverage of
the registered gate criteria is genuinely good — not import-and-smoke:

- **Null control:** smooth uniform density, 2 windows → b̂− < 1, `passed=False`,
  `weiter_indication=False` (test_null_smooth_density_does_not_pass).
- **Positive detection:** synthetic bunching spike in [0.955, 0.995]·K with the
  registered 500 bootstrap reps → ALL four gate criteria + FDR + `weiter_indication`
  + `gate_valid_assumptions=True` asserted (test_positive_bunching_below_kink…).
- **capital_free token scan:** payload JSON scanned for bps/pnl/sharpe/friction/edge_
  in two tests (unit + end-to-end).
- **N-floor / cf-floor invalidity:** invalid cell can NEVER pass even with a spike;
  `all_cells_invalid_by_window == [True, True]` power-DROP flag asserted.
- **End-to-end CLI:** synthetic Hive tree in the harvester backfill layout
  (`raw/bybit/publicTrade/symbol=/date=/data.parquet`, `payload_json` single-trade
  form, written via DuckDB) → subprocess run of `scripts/c09_bunch.py` → rc=0, valid
  JSON+MD, anti-gaming flag false at 50 reps.
- **Geometry:** bin edges, bin indices 55-59/60-64/50-69, degree-7 fit exactly
  recovering a smooth polynomial on the excluded region, order aggregation.

Gaps (none blocking on their own): no truncation-path test (Bug 1), no test pinning the
FDR family size at 10 under a partial panel (Bug 3), no direct BH unit test (Bug 7),
the B+ boundary-fidelity adjustment in `_window_sums` (exact-kink / exact-1.05K mass)
is untested, and the null-control test does not assert the bootstrap-p distribution
(only the b̂− magnitude and pass flags).

---

## capital_free check result: **CLEAN**

- `grep -rniE 'bps|pnl|sharpe|friction|edge_|fee|slippage|latency'` over the whole
  `c09_bunch` module + `scripts/c09_bunch.py`: **0 hits**.
- Payload construction (`driver.run`) contains only counts, dimensionless ratios,
  p-values and method metadata; `capital_free: true` is set; both the unit test and
  the end-to-end test enforce the token ban on the serialized payload.
- README/runners state KAPITALFREI and the H-09b non-implication doctrine verbatim.

## T2 runner check result: **PASS** (one operational note)

`run_h09.ps1`: script path is the FIRST CmdArg (line 140-141, with an explicit comment
referencing the run_h05c bug); `$null = $p.Handle` handle-cache present (line 98) with
the null-ExitCode fallback rc=-2; BelowNormal on both the shell (57) and the child
process (99); pure ASCII, no non-ASCII bytes (verified with `file` + byte grep); no
interactive prompt anywhere; per-step timeout 7,200 s with kill; junction pre-check →
SKIP; `SUMMARY_<date>.md` always written; deterministic exit 0/1/2; HANDOFF_DRY_RUN
/ HANDOFF_DRY_RC honoured. `run_h09.sh` mirrors all of it (timeout(1) if available,
same SUMMARY/exit contract). **Note:** the single 7,200 s budget covers the ENTIRE
10-window run; combined with Bugs 1-2 the real-data run may hit rc=124 with no partial
JSON — resolve Bugs 1-2 before relying on the budget.

## Placeholder / K_s status: **properly flagged, not silently final — but see Bug 8**

Only BTCUSDT = 2,000,000 USDT is registry-quoted; ETH (1.5M) / SOL (1.0M) / BNB (0.5M)
/ XRP (0.5M) are placeholders. Flagged consistently in: `kinks.py` (block comment +
`KINK_PLACEHOLDER_SYMBOLS` + `KINK_PLACEHOLDER_NOTE`), CLI stderr banner, both runner
headers + console + SUMMARY, README_H09.md (table + 3-step addendum procedure incl.
K_s-constancy check over W1+W2), and the JSON payload (`kink_placeholder_symbols`,
`kink_placeholder_note`, per-cell and per-symbol `kink_is_placeholder`). README
correctly states the DEC-09-pattern addendum as a precondition for a valid verdict and
that this is a scoping parameter, not a goalpost shift. It does NOT mechanically block
a run (by design), and BTC cells are meaningful today; the only weakness is Bug 8
(`weiter_indication` not conditioned on placeholder status).

---

*Audit executed 2026-07-08 by a fresh adversarial auditor session; tests run live in
the sandbox, all findings from direct code reading — no builder self-reports trusted.*
