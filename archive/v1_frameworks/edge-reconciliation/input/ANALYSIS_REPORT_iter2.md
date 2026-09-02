# Replay Analysis Report

Scope: validate the two replay runs in `/tmp/replay_artifacts/` (default vs `--invert-strategies S2,S3`, commit `a77a366`) against the live code at `/home/user/scinance` (branch `claude/subagent-prd-development-T16fE`).

## 1. Implementation-Mechanics Findings

### 1.1 S3 Inversion Mechanism — BROKEN (verified by code reading)

`strategy3_pre_settlement.py::_direction_from_pressure` (lines 223-237) reads `S3_INVERT_DIRECTION` at every call site. The same helper is invoked **twice** in the strategy's hot path:

1. Line 281, inside `_check_entry`, used to compute the basis-alignment gate `basis_aligned = basis * direction < 0` (line 282).
2. Line 190, inside `on_ticker`, used to assign the actual entered direction.

With `S3_INVERT_DIRECTION=True` both call sites flip, so the gate becomes `basis * (-base) < 0`, i.e. `basis * base > 0` — the **opposite** condition. Because pressure is the clamp residual of `(I-P)` and `sign(pressure)` is "always opposite to sign(basis) by construction" (per the code comment at lines 275-278), in the default direction the gate is effectively auto-satisfied (the original-run diagnostics confirm: `n_pressure_extreme == n_basis_aligned == n_all_gates_passed` for every symbol — see §2.2). Inverting the call therefore makes the basis gate **auto-fail** for the same data, which is exactly what the inverted run shows: `S3.total_trades = 0` across all five symbols, `n_trades = 0` per symbol, `data_limited = false`.

This is *not* the "consistent" behaviour the commit message claims ("S3 inversion is consistent: basis-alignment gate sees the post-inversion direction"). The gate was designed for the un-inverted direction; passing the inverted direction to it transforms it from a soft pass-through into a hard block.

### 1.2 S2 Inversion Mechanism — WORKS as intended

`strategy2_entropy_momentum.py` lines 163-166: direction is derived from OFI sign and only at the entry-emission point is it flipped under `S2_INVERT_DIRECTION`. The entry gates themselves (entropy collapse, OFI above Q90, sign(pressure)==sign(ofi), PE greenlight) do not consume `direction`, so they are untouched by the flag. Trade count must therefore be identical between runs. It is: 190 in both, and per-symbol 26/59/71/11/23 in both — confirmed in the JSONs.

### 1.3 PnL Computation Direction-Sensitivity — Confirmed sign-flipping

`replay_backtester.py::_make_trade` (lines 1530-1567): for a Long, `raw_pnl = (slip_exit - slip_entry) * qty`; for a Short the sign flips. So a true direction flip mathematically inverts `raw_pnl` to the bit. Net PnL differs from raw PnL by `entry_fee + exit_fee + slippage`, which are **direction-symmetric** costs (slippage is always adverse, fees are proportional to slipped notional). Net PnL after inversion is `-raw_pnl_original - 2·(fees + slip_cost)`. If `|raw_pnl|` per trade is small relative to friction, net PnL barely moves — which is the observation.

Friction budget at engine defaults (`SLIPPAGE_DEFAULT_BPS=2.0`, `FEE_TAKER=0.00055`):
- Slippage: 2 bps adverse per leg → ~4 bps round-trip on price.
- Taker fee: 5.5 bps × 2 legs = 11 bps on (slipped) notional.
- Round-trip friction ≈ **15 bps of entry notional**, qty=1.

## 2. Strategy-Level Diagnostics

### 2.1 S2 Entry-Gate Funnel (per symbol, original run)

| Sym | entropy_not_collapsed | ofi_below_q90 | pressure_ofi_misaligned | pe_no_greenlight | __enter__ |
|---|---:|---:|---:|---:|---:|
| BNB | 81,302 | 2,843 | 117 | 101 | 26 |
| BTC | 82,391 | 1,430 | 144 | 56 | 59 |
| ETH | 78,912 | 1,793 | 187 | 102 | 71 |
| SOL | 84,785 | 3,166 | 168 | 68 | 11 |
| XRP | 86,523 | 1,552 | 142 | 39 | 23 |

The entropy-collapse gate is the dominant filter (~97% of all ticks). OFI, PE and pressure-OFI alignment are tertiary. S2 fires 11-71 entries per symbol over ~80-90k ticks: roughly one per 1.2-7k ticks. Not "too rare" in absolute terms; the structural problem is win-rate, not entry count.

### 2.2 S3 Entry-Gate Funnel (per symbol, original run)

| Sym | n_in_window | pressure_below_q90 | n_pressure_extreme | n_basis_aligned | n_all_gates_passed | __enter__ |
|---|---:|---:|---:|---:|---:|---:|
| BNB | 6,417 | 1,772 | 16 | 16 | 16 | 16 |
| BTC | 6,720 | 2,228 | 61 | 61 | 61 | 61 |
| ETH | 6,720 | 3,543 | 50 | 50 | 50 | 50 |
| SOL | 6,874 | 2,349 | 33 | 33 | 33 | 33 |
| XRP | 6,925 | 3,199 | 44 | 44 | 44 | 44 |

`n_pressure_extreme == n_basis_aligned == n_all_gates_passed` everywhere. This is a **strong indicator the basis-alignment gate is a no-op in default mode** (every tick that passes the Q90 pressure gate also passes basis alignment and BOCPD-stability). The code comment at `strategy3_pre_settlement.py:275-278` confirms this is *expected*: pressure is the clamp residual of `(I-P)` so `sign(pressure) ≡ -sign(basis)` by construction, hence `basis * direction < 0` is auto-satisfied. The gate provides no additional information — it is decorative. (Also: BOCPD never fires a changepoint in this window.)

Implication: in the original direction, S3 is effectively a single-gate strategy (window ∩ Q90-pressure). The 9.3% aggregate win rate suggests the unconditional direction prior (`+1 if pressure>0 else -1`) is **anti-predictive** at ~9% vs. the 50% null.

### 2.3 S1/S4/S5 Structural Blockers

- **S1 (M14/M15 cascade)**: reason `rho_below_threshold` dominates (56k-87k per symbol). This is a **threshold/data-distribution** blocker: the M14 Hawkes branching ratio rarely exceeds the configured trigger. `unknown` counts (28k for BNB) suggest other code paths early-return without an emit-reason — diagnostics blind spot.
- **S4**: `insufficient_models` covers ~all ticks (~84-88k per symbol). This is **upstream-module insufficiency** — S4 needs trained model artifacts (likely M16/M17/M18) that the replay environment did not load.
- **S5**: `unknown` is essentially every tick (84-88k). Identical pattern across symbols, consistent with cross-symbol-state dependency that the single-symbol replay loop cannot satisfy. Cannot be confirmed without reading the S5 source; flagged as **data/architecture** dependency.

## 3. PnL Decomposition

### 3.1 Friction Estimate per Symbol (qty=1, ~15 bps round-trip)

Approximate spot magnitudes derived from observed loss/n_trades and the 15 bps yardstick:

| Sym | obs $/trade (orig S2) | obs $/trade (inv S2) | implied notional (orig) | rough friction at that notional |
|---|---:|---:|---:|---:|
| BNB | -0.77 | -1.05 | ~510 | ~0.77 |
| BTC | -93.4 | -98.5 | ~62,000 | ~93 |
| ETH | -2.61 | -2.72 | ~1,750 | ~2.6 |
| SOL | -0.104 | -0.104 | ~70 | ~0.10 |
| XRP | -0.0018 | -0.00178 | ~1.2 | ~0.0018 |

S3 original $/trade (for reference): BNB -1.93, BTC -104.9, ETH -2.95, SOL -0.128, XRP -0.0017 — all of the same order as the friction estimate.

### 3.2 Directional vs. Frictional Loss Share

- **S2 (original→inverted)**: aggregate total return moves from -$5,716.8 to -$6,032.8 on the same 190 trades. If raw_pnl truly flipped sign, `inv_net - orig_net = -2·orig_raw_sum`. Observed delta is -$316 → orig_raw_sum ≈ -$158 (so raw directional PnL was already slightly negative, ~-$0.83/trade). Friction contribution ≈ -$5,559 in aggregate (~-$29.3/trade) dominates by ~35×. **Friction is the loss; direction is ~noise around zero.**
- **S3**: cannot be compared because the inverted run produced 0 trades (see §1.1). Within the original run, win-rate 9.3% is strongly anti-predictive (≪ 50%), so directional contribution is **negative and not noise** — but cannot cleanly partition without raw-PnL artefacts (Open Question Q3).

Per-symbol Sharpe is uniformly strongly negative in S2 (-42 to -88) regardless of trade count or symbol. This is the signature of a process whose mean is dominated by a deterministic cost (friction) rather than a noisy edge — variance is small, so |Sharpe| inflates. **No symbol outlier**; the pattern is uniform.

## 4. Methodological Concerns

- **qty = 1.0 unit, not USD-notional**: `_make_trade` line 1539 hardcodes `qty = 1.0`. Cross-symbol aggregates (`weighted_sharpe`, `total_return`) therefore weight BTCUSDT ~50,000× more heavily than XRPUSDT in USD terms. Aggregate total_return is essentially the BTCUSDT result with rounding (BTC contributes -$5,510 of S2's -$5,717 total — 96%). Win-rate "mean" is straight mean across symbols, not trade-weighted.
- **Look-ahead / within-sample contamination**: rolling reference statistics (`_pressure_history`, `_entropy_history`, both maxlen 50,000) are appended *before* the gate check on the same tick — `strategy2:129` then `_is_entropy_collapsed`; `strategy3:154` then `_is_pressure_above_q90`. Current observation is included in the reference it is compared against. Impact ~1/50k — numerically negligible but methodologically unclean. Recent commits (`fa936b6`, `212fe51`) repaired `seconds_to_settlement` time-alignment; no obvious residual time leakage.
- **single_pass with N=11-71 trades per symbol**: Sharpe over one non-overlapping pass has very wide CIs. The headline `weighted_sharpe = -73` is a point estimate with no stability check; SE on ~190 trades is not reported. Interpreting the negative Sharpe as "edge is inverted" is **not warranted from one pass** — friction-dominance and small-sample noise are both viable explanations.

## 5. Identified Weaknesses (catalog only, no fixes)

- **W1 — S3 inversion silently disables the strategy.** `_direction_from_pressure` is called twice (gate AND entry). Flag flips both, turning the basis gate from auto-pass to auto-fail. Evidence: inverted run has 0 trades across all 5 symbols; original run has `n_basis_aligned == n_pressure_extreme` everywhere.
- **W2 — S3's basis-alignment gate carries no information in default mode.** Code comment (lines 275-278) acknowledges `sign(pressure) ≡ -sign(basis)` by construction, making the gate auto-pass. Evidence: equal counters across the funnel for every symbol.
- **W3 — Friction is comparable to or larger than directional edge for S2.** ~35× ratio of friction loss to raw-direction loss derived from the inversion delta. Net effect: S2 is statistically a friction-burning process, not a strategy test.
- **W4 — Cross-symbol aggregates are notional-incompatible.** `qty=1.0` unit-based weighting makes BTCUSDT swamp aggregate metrics. Evidence: `_make_trade` line 1539; total_return -$5,717 of which BTC contributes -$5,510 (96%).
- **W5 — Negative Sharpe is uniform across symbols and across direction for S2.** Sharpe -43 to -88 per symbol, ~zero PnL change between orig and inverted relative to friction — metric mostly tracks friction.
- **W6 — S2 win-rate is 0.5% pre-inversion and 0.0% post-inversion.** Both far below the 50% null. A symmetric flip should produce ~0.5% → ~99.5%, not ~0%. Consistent with W3: friction is large enough to convert near-coin-flip trades into losers regardless of direction.
- **W7 — `single_pass` with N≈11-71 trades per symbol gives Sharpe point estimates without dispersion.** No walk-forward folds, no bootstrap CIs.
- **W8 — Within-sample contamination in rolling reference statistics.** Current tick appended to deque before comparison against deque-derived quantile/median. Order ~1/50k impact.
- **W9 — S1 threshold-bound, S4 model-bound, S5 likely architecture-bound.** None meaningfully participate in either run.
- **W10 — `unknown` reason is highest-frequency wait reason for S1 (BNB 28k) and S5 (everything).** Diagnostics layer has blind spots that mask structural blockers.

## 6. Open Questions / Unverifiable Without More Data

- **Q1**: For S3, what is the *raw* (pre-friction) PnL distribution? No inverted-trade artefact (0 trades) → cannot back out directional vs. frictional components as for S2. Needs raw_pnl export or notional-normalised run.
- **Q2**: Are the spot price ranges I inferred (BTC ~62k, ETH ~1.75k, SOL ~70, BNB ~510, XRP ~1.2) actually those seen in the replay window? Derived from `observed loss / 0.0015` assuming friction-dominance; not cross-checked against the DuckDB data.
- **Q3**: What fraction of S3's 9.3% win-rate (vs 50% null) is attributable to wrong-direction pressure-mapping vs. friction wiping near-zero wins? Cannot disentangle without per-trade raw_pnl.
- **Q4**: Does the `unknown` reason for S1/S5 correspond to specific code branches with missing diagnostics, or genuinely-unreachable noise? Would require source-walk of `strategy1_*` / `strategy5_*` not done here.
- **Q5**: Is M6's L2 orderbook input actually present in the replay data? S2 is flagged `data_limited: true` per-symbol but still produced trades. The flag in the JSON appears to be the *static* default; `is_data_limited_runtime` promotes S2 once L2 is loaded. Worth verifying M6 is not running on a degenerate placeholder.
- **Q6**: `n_in_window ≈ 6,400-6,925` per symbol over `n_ticks ≈ 81k-88k` (~7-8%). 30-min entry window every 8 hours → ~6.25% expected. Slightly higher is consistent with the recently-fixed `seconds_to_settlement` defect; worth confirming.
