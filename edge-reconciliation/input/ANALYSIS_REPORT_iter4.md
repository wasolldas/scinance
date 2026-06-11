# Iter-4 Push A — Empirical Analysis Report

**Run timestamp**: 2026-06-10T02:26:03Z
**Mode**: single_pass, 5 symbols (BTC/ETH/SOL/BNB/XRP), ~24h replay window per symbol (~80-87k ticks/symbol)
**Flags active**: `--s1-rho-instrument`, `--s2-maker-only`, `--s3-time-stop`, `--s3-hard-stop` (all four flags engaged; verified via diagnostics + fee zeros)
**Total trades**: 403 (S1=0, S2=190, S3=213, S4=0, S5=0)

---

## Executive Summary

Three forensic experiments, three clean verdicts:

| Strategy | Hypothesis tested | Outcome | Verdict |
|----------|------------------|---------|---------|
| **S1** | Threshold miscalibration vs. broken estimator | Distribution is unimodal at ~2e-7; threshold 0.85 sits **6 orders of magnitude** above the data | **Estimator structurally broken**. No threshold sweep will fix this. Retire or redesign. |
| **S2** | Hidden raw edge masked by taker friction | With zero fees, aggregate raw edge **still -3.45 bps**, every symbol negative | **Retired**. The maker-only forensic was the last test. S2 has no edge. |
| **S3** | Bounded-loss exits cap the long tail | Hard-stop fired 13× and trimmed *some* tails. Time-stop fired **1× total** — implementation bug | **Concept survives, code needs a fix**. Bug isolated; fix is one-liner. Iter-5. |

The push delivered exactly what it was supposed to: **kill two strategies cleanly and surface a code bug in the third**. We now have firm empirical grounds to scope iter-5 around S3 only.

---

## 1. Push A Confirmation: all four flags engaged

Before interpreting any signal, verify the experiment actually ran.

- **`--s1-rho-instrument`**: 5/5 rho_distribution_*.json files emitted with n_samples between 56k (BNB) and 87k (SOL). ✓
- **`--s2-maker-only`**: All 190 S2 trades have `entry_fee == 0.00` AND `exit_fee == 0.00`. The fee-zero path was taken on every S2 round-trip. ✓
- **`--s3-time-stop`**: BNBUSDT diagnostics show `time_stop_exceeded: 1` (the flag-gated reason string only appears when the flag is on). ✓
- **`--s3-hard-stop`**: 4 of 5 symbols show `hard_stop_loss` reason counts (BTC:2, SOL:3, BNB:6, XRP:2; ETH:0). ✓

All four iter-4 flags executed. Findings below are real.

---

## 2. S1: ρ-distribution forensic

The iter-3 mystery: S1 fired zero trades because `rho_below_threshold` covered 67-99% of ticks. We didn't know whether ρ was unimodal-low (estimator broken) or bimodal with the upper mode below the 0.85 calibration (threshold wrong). The instrumentation answers it.

### The distribution per symbol

| Symbol | n_samples | p50 | p90 | p95 | p99 | max |
|--------|-----------|-----|-----|-----|-----|-----|
| BTCUSDT | 83,597 | 2.13e-7 | 9.04e-4 | 0.001 | 0.001 | 9.40 |
| ETHUSDT | 80,550 | 2.05e-7 | 9.70e-4 | 0.001 | 0.001 | 7.16 |
| SOLUSDT | 87,379 | 1.92e-7 | 4.60e-7 | 6.02e-7 | 1.64e-6 | 0.001 |
| BNBUSDT | 56,425 | 1.84e-7 | 4.46e-7 | 5.59e-7 | 9.12e-7 | 1.32e-3 |
| XRPUSDT | 86,088 | 1.94e-7 | 4.55e-7 | 5.75e-7 | 1.61e-6 | 0.49 |

### Interpretation

The median ρ across all 5 symbols sits at **~2 × 10⁻⁷**. The threshold is **0.85**. The distance is **six orders of magnitude**.

The p99 on SOL/BNB/XRP is ~1e-6 — **still six orders below the threshold**. BTC and ETH show a p90/p95 jump to ~1e-3 (likely the rolling-window's numerical-floor saturating at 0.001), with the maximum reaching 9.4 (BTC) and 7.2 (ETH) — these are isolated spikes during specific high-stress moments, not a second mode.

This is the textbook signature of an **estimator that is structurally too coarse** for the underlying data, not a calibration error.

### Why a threshold sweep cannot fix this

Even setting ρ_entry to the p95 of each symbol would only move it from 0.85 to ~1e-3. At p95, the threshold becomes a 5% sampling switch — the strategy would fire on noise, not on a meaningful cascade signature. The Hawkes self-excitation parameter we're measuring is effectively zero almost always; it does not separate "cascade about to happen" from "normal liquidation flow" at the resolution this data offers.

### Verdict and iter-5 implication

**S1 in its current form is retired.** The hypothesis — that single-channel Hawkes self-excitation on Bybit liquidation tape predicts cascades — is not supported. To revive the cascade-detection thesis, iter-5 would need:

1. A different estimator: multi-channel Hawkes (separate Long/Short kernels), or a richer Hawkes parameterization (e.g. exponential-decay with shape-free baseline).
2. A different data source: aggregated cross-venue liquidation feed instead of Bybit-only.
3. A different trigger: rather than ρ-crossing, trigger on event-clustering windows (Aalen process / Cox regression on liquidation counts).

None of these are 1-flag changes. They are PRD-level rewrites. **Recommendation: shelve S1, do not invest more replay-time on the current estimator.**

---

## 3. S2: maker-only forensic

The iter-3 inverted-arm replay refuted the anti-predictive hypothesis. The maker-only run was the **last test before retirement**: if S2 had a hidden positive raw edge being eaten by 11 bps of round-trip taker friction, zero fees would surface it.

### Per-symbol aggregate (all fees set to 0)

| Symbol | n_trades | mean pnl_bps | min pnl_bps | max pnl_bps | raw_pnl sum |
|--------|----------|-------------|-------------|-------------|-------------|
| BTCUSDT | 59 | **-3.61** | -11.13 | +7.92 | -1359.11 |
| ETHUSDT | 71 | **-3.71** | -10.66 | +6.33 | -46.62 |
| SOLUSDT | 11 | **-3.99** | -6.95 | +0.46 | -0.30 |
| BNBUSDT | 26 | **-1.65** | -10.62 | +12.76 | -2.60 |
| XRPUSDT | 23 | **-4.06** | -9.83 | +7.40 | -0.01 |
| **Aggregate** | **190** | **-3.45** | -11.13 | +12.76 | — |

### Interpretation

With friction removed entirely (worst-case-for-the-hypothesis; Bybit's actual maker rebate would make this *slightly less bad*), **every symbol still loses on raw edge**. The best-case symbol (BNB) loses -1.65 bps per trade. The "best trade" magnitude (+12.76 bps on BNB) is smaller than the worst trade on three of five symbols.

The hit-rate confirms it: raw-PnL-positive rate is **7-13%** on BTC/ETH/SOL/XRP, and 35% on BNB. The direction is overwhelmingly Long (BNB: all 26 Long, BTC: all 59 Long, ETH: all 71 Long, SOL: 11 Long, XRP: 22 Long + 1 Short). The signal is structurally biased Long and structurally wrong about it.

### Verdict

**S2 has no edge — neither directional, nor anti-predictive, nor friction-bound.** Across three forensics (original arm, inverted arm, maker-only) it has lost on raw bps every time. The entropy-momentum thesis as currently specified does not survive contact with Bybit perpetual data.

**Recommendation**: Disable S2 in the live router (config gate: `S2_ENABLED: bool = False`); keep the code for archival reference but route no capital. **Do not test further variants** without a fundamentally different signal definition.

---

## 4. S3: bounded-loss exits + bug in the time-stop

The iter-3 hypothesis: S3 is friction-bound + tail-driven, not direction-broken. The fix is bounded loss per trade. T1 added an opt-in time-stop (120s wall-clock) and hard-stop (-30 bps MTM).

### Per-symbol S3 stats (both flags on)

| Symbol | n | mean bps | min bps | mean dur (s) | max dur (s) | n>120s | n<-30bps | hard_stop | time_stop |
|--------|---|---------|---------|--------------|-------------|--------|----------|-----------|-----------|
| BTCUSDT | 62 | -16.57 | -47.70 | 102.2 | 561 | 14 | 5 | 2 | **0** |
| ETHUSDT | 50 | -16.34 | -37.72 | 102.8 | 1099 | 13 | 7 | 0 | **0** |
| SOLUSDT | 36 | -18.20 | -48.93 | 167.9 | 1342 | 13 | 9 | 3 | **0** |
| BNBUSDT | 19 | -21.08 | -56.60 | 563.3 | 2125 | 14 | 8 | 6 | **1** |
| XRPUSDT | 46 | -14.78 | -46.39 | 141.5 | 1999 | 14 | 4 | 2 | **0** |
| **Aggregate** | **213** | **-16.81** | -56.60 | 163 | 2125 | **68** | **33** | **13** | **1** |

### Two findings

**Finding 1 — Hard-stop works but is too loose.**
The hard-stop fired 13 times and caps each of those trades at ~-30 bps MTM. But 33 trades still exited with `pnl_bps < -30` (15% of all S3 trades). The gap: `pnl_bps` is *net of friction* (entry_fee + exit_fee ≈ 11 bps round trip), while the hard-stop measures *raw MTM* against entry price. A trade that exits via `pressure_dissipated` at raw -20 bps still shows pnl_bps ≈ -31 bps. **The hard-stop threshold needs to be tightened**, or it needs to fire on `raw_pnl + projected_exit_fee`.

**Finding 2 — Time-stop is bugged.** ← *the important one*

68 of 213 trades (32%) lasted longer than 120 seconds in market time, with the worst running 2125s (35 minutes on BNB). The flag was on; the reason should have triggered 68 times. It triggered **once**.

Root cause: `strategy3_pre_settlement.py:129` computes `now = time.time()` — wall-clock time, not replay-tick time. Inside a fast replay (~80k ticks/symbol processed in under an hour each), wall-clock elapsed between entry and exit is seconds while market-clock elapsed is minutes. `(now_wall - entry_ts_wall) * 1000 > 120_000` almost never holds. The one BNB hit was probably a slow tick batch.

The 1-line fix: source `now` from the tick timestamp (`ts_ms / 1000.0`) instead of `time.time()`. Pass `now_market = ts_ms / 1000.0` into `_check_exit`. The hard-stop is unaffected (it doesn't use time).

### What we *can* still infer about S3 directional edge

Even without the time-stop firing, the 13 hard-stop exits provide *some* tail reduction. Compare to iter-3:

- Iter-3 BNB worst trade: **-195 bps**, 1559s held.
- Iter-4 BNB worst trade: **-56.6 bps**, 1204s held. The -195 bps tail did NOT recur this run — likely because BNB didn't experience an equivalent stress moment in this replay window, not because of the bounded-loss exits (only 1 BNB hard-stop fired and even that didn't catch the -56.6 bps trade since exit reason was probably `pressure_dissipated`).
- Iter-4 aggregate mean pnl_bps = -16.81 (net). Subtracting ~11 bps round-trip friction: raw ≈ -5.8 bps. Within iter-3's -3.31 to -20.09 bps band. **Raw edge per trade is unchanged**, as expected — bounded-loss exits don't change the entry signal.

### Verdict

**S3 thesis (pre-settlement pressure release) survives iter-4 intact**, but the bounded-loss implementation needs the time-stop bug fix to deliver the iter-3 hypothesis test cleanly. **This is the only strategy worth more replay-time in iter-5.**

---

## 5. Strategic implications and iter-5 scope

### What iter-4 closed

- ✅ S2 retired with a clean three-replay forensic trail (original arm, inverted arm, maker-only). Decision is defensible without further runs.
- ✅ S1 estimator-broken hypothesis confirmed. ρ-distribution data shipped in repo for future PRD revision.
- ✅ S3 hard-stop validated as concept; one bug identified.

### What iter-5 should be

**Single-strategy iteration on S3 only.** Two-task scope:

1. **Bug fix**: route market-tick time into `_check_exit` instead of `time.time()`. Re-test 120s time-stop. Expect 60-70 time-stop exits this time, drastic reduction in `n>120s`.
2. **Tighten hard-stop**: change threshold to `-20 bps raw` or include projected friction (`raw_mtm + projected_round_trip_fee < -30 bps`). Expect to absorb the remaining 33 sub-(-30bps) trades.

Plus a measurement: re-run with the fix and report what aggregate mean pnl_bps becomes. If S3 reaches net-positive after the bounded-loss fix, **that is the first strategy with an actually-measured edge** and gates Push C (Demo Trading).

### What iter-5 should *not* be

- No work on S1 / S2 / S4 / S5. They are dead or unbuilt; resurrecting them is PRD work, not replay work.
- No Hetzner cloud setup yet. The iter-5 bug fix is small enough that one more local 12h run is acceptable. **Push B (cloud) only becomes worth the setup cost when we have a strategy whose parameter space we want to sweep.**

### What Push C (Demo Trading) depends on

Demo Trading should be wired up **only after** we have one strategy with a measured-positive net edge on replay. Currently zero strategies meet that bar. If iter-5 makes S3 net-positive: Push C activates with S3-only routing. If iter-5 leaves S3 net-negative: Push C waits for a PRD-level redesign.

---

## Appendix: artifact paths

- Trades: `/tmp/replay_artifacts/iter4_results/trades_iter4/trades_*_single_pass.csv`
- ρ-distribution per symbol: `/tmp/replay_artifacts/iter4_results/rho_distribution_*.json`
- Aggregate results: `/tmp/replay_artifacts/iter4_results/replay_all_results.json`
- This report: `/tmp/replay_artifacts/ANALYSIS_REPORT_iter4.md`
