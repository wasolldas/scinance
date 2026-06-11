# Iter-3 Original-Arm Analysis Report

**Scope:** 5 symbols (BNBUSDT, BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT), original direction only. 394 trades across S2 (190) and S3 (204); S1/S4/S5 have 0 trades on every symbol. Inverted arm not analyzed.

**Sources:**
- JSON: `/root/.claude/uploads/c0ea1101-77e8-5705-b300-dc953345191c/3842e44e-replay_all_results.json`
- Per-trade CSVs: `/tmp/iter3_data/original/trades_original/trades_*_single_pass.csv`

**Assumptions stated up front:**
- Notional per trade = `entry_price * quantity`. `raw_bps = raw_pnl / notional * 1e4`. `fee_bps = (entry_fee + exit_fee) / notional * 1e4` — i.e. round-trip taker fee.
- All aggregate statistics are **trade-equal-weighted**, not symbol-equal-weighted. BTC dominates because it has the largest notional; ETH+BTC together are ~60% of trades.
- Edge-to-friction ratio = `mean(raw_bps) / mean(fee_bps)`. The denominator is ~11 bps everywhere (taker fee model is flat ≈5.5 bps/side).

---

## Section 1: Per-strategy headline

### S2 — entropy/OFI/pressure scalp

**Verdict: friction-bound, with a small adverse-direction component on BTC/ETH/SOL/XRP. BNB is the cleanest case (raw is only -1.65 bps, well within noise).**

The raw edge is *negative everywhere* but the magnitude (-1.65 to -4.06 bps) is dwarfed by the 11 bps round-trip taker fee. If fees were 0, S2 would still lose money on average but the headline Sharpes (-42 to -88) would collapse toward ~zero or slightly negative. Of the 190 S2 trades, 12.1% are raw-positive and only 0.5% are net-positive. The strategy fires almost exclusively Long (189/190; one Short on XRPUSDT) — so the inverted arm will be informative on S2.

| Symbol | n | sum_raw $ | mean_raw $ | mean_raw bps | sum_fee $ | mean_fee $ | mean_fee bps | raw hit | net hit | max_loss $ | max_win $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BNBUSDT | 26 | -2.60 | -0.100 | -1.65 | 17.33 | 0.667 | 11.00 | 0.346 | 0.038 | -0.642 | +0.761 |
| BTCUSDT | 59 | -1359.11 | -23.04 | -3.61 | 4151.15 | 70.36 | 11.00 | 0.068 | 0.000 | -70.22 | +50.29 |
| ETHUSDT | 71 | -46.62 | -0.657 | -3.71 | 138.85 | 1.956 | 11.00 | 0.085 | 0.000 | -1.84 | +1.16 |
| SOLUSDT | 11 | -0.30 | -0.028 | -3.99 | 0.84 | 0.076 | 11.00 | 0.091 | 0.000 | -0.048 | +0.003 |
| XRPUSDT | 23 | -0.011 | -0.0005 | -4.06 | 0.030 | 0.0013 | 11.00 | 0.130 | 0.000 | -0.001 | +0.001 |
| **All** | **190** | **-1408.65** | **-7.41** | **-3.45** | **4308.20** | **22.67** | **11.00** | **0.121** | **0.005** | -70.22 | +50.29 |

Diagnostic that justifies the verdict: `|mean_raw_bps| / mean_fee_bps in [0.15, 0.37]` everywhere. The largest negative arm is XRP at -0.37, still inside the "friction-bound" band.

### S3 — settlement-window pressure trade

**Verdict: mixed. Direction-bound on BNB (extreme; one trade explains 60% of the loss), friction-bound on BTC / ETH / XRP, mildly direction-bound on SOL. The BNB interim report's "direction-bound + fat left tail" conclusion holds *only on BNB* and does not generalise.**

The raw edge is negative on every symbol but the magnitude varies from -3.31 bps (XRP) to -20.09 bps (BNB). BNB's number is driven almost entirely by a single -195 bps outlier; ex-outlier the BNB raw edge is roughly -0.5 bps/trade, which would actually flip BNB into the "friction-bound" bucket. All 204 trades are Long (S3 never went Short in the original arm).

| Symbol | n | sum_raw $ | mean_raw $ | mean_raw bps | sum_fee $ | mean_fee $ | mean_fee bps | raw hit | net hit | max_loss $ | max_win $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BNBUSDT | 16 | -20.28 | -1.267 | -20.09 | 10.67 | 0.667 | 10.99 | 0.438 | 0.125 | -12.35 | +2.56 |
| BTCUSDT | 61 | -2042.77 | -33.49 | -5.12 | 4354.25 | 71.38 | 11.00 | 0.197 | 0.049 | -228.75 | +226.21 |
| ETHUSDT | 50 | -48.50 | -0.970 | -5.34 | 99.18 | 1.984 | 11.00 | 0.240 | 0.060 | -4.77 | +7.29 |
| SOLUSDT | 33 | -1.70 | -0.051 | -7.03 | 2.52 | 0.076 | 11.00 | 0.333 | 0.152 | -0.360 | +0.373 |
| XRPUSDT | 44 | -0.017 | -0.0004 | -3.31 | 0.057 | 0.0013 | 11.00 | 0.341 | 0.136 | -0.006 | +0.002 |
| **All** | **204** | **-2113.26** | **-10.36** | **-6.27** | **4466.68** | **21.90** | **11.00** | **0.279** | **0.093** | -228.75 | +226.21 |

Diagnostic: edge-to-friction ratios span [-0.30, -1.83]. BNB at -1.83 is a genuine direction-edge in the *wrong* sense; the other four sit between -0.30 and -0.64 — the friction band.

### S1 — liquidation/rho trigger

**Verdict: threshold-bound (parametric).** On every symbol, `rho_below_threshold` is 56k-87k ticks (~67-99% of all ticks). `liquidations_below_min_events` is the other reason and matters only on BNB (28k = 33% of ticks). BTC/ETH/SOL/XRP have effectively unlimited liquidation events; the binding gate is the rho threshold. *Not data-bound* — the strategy sees plenty of liquidations, it just never gets rho high enough.

| Symbol | top reason 1 | top reason 2 |
|---|---|---|
| BNBUSDT | rho_below_threshold: 56,425 | liquidations_below_min_events: 28,192 |
| BTCUSDT | rho_below_threshold: 83,482 | liquidations_below_min_events: 794 |
| ETHUSDT | rho_below_threshold: 80,525 | liquidations_below_min_events: 812 |
| SOLUSDT | rho_below_threshold: 87,379 | liquidations_below_min_events: 884 |
| XRPUSDT | rho_below_threshold: 86,088 | liquidations_below_min_events: 2,319 |

### S4 — PatchTST model layer

**Verdict: architecture-bound (missing artifact / wiring).** `insufficient_models` covers 96-99.99% of all ticks on every symbol. `insufficient_price_history` is 2-10 ticks — irrelevant. The model layer is simply not producing predictions; replaying more data will not help.

### S5 — cross-sectional panel

**Verdict: architecture-bound by design.** `single_symbol_replay_unsupported` = 100% of ticks on every symbol. S5 needs the panel data loader, not a code fix in the strategy. Skip until that loader exists.

---

## Section 2: Cross-symbol consistency

**Bottom line: S2 looks identical across all 5 symbols. S3 splits — BNB is the outlier; BTC/ETH/SOL/XRP behave alike.**

### Edge-to-friction ratio (mean_raw_bps / mean_fee_bps)

| Symbol | S2 ratio | S3 ratio | S2 verdict | S3 verdict |
|---|---:|---:|---|---|
| BNBUSDT | -0.150 | **-1.828** | friction-bound | **direction-bound (wrong sign)** |
| BTCUSDT | -0.328 | -0.466 | friction-bound | friction-bound |
| ETHUSDT | -0.337 | -0.486 | friction-bound | friction-bound |
| SOLUSDT | -0.363 | -0.639 | friction-bound | ambiguous (border) |
| XRPUSDT | -0.369 | -0.301 | friction-bound | friction-bound |

S2 is the cleanest case in the run: every symbol falls inside the |ratio|<0.4 friction band. The raw edge is mildly negative but small enough that the inversion arm is unlikely to flip the sign meaningfully — expect a similar magnitude on the opposite side.

S3-on-BNB is dominated by a single -195 bps trade (see Section 3). With that one trade removed, the BNB ratio drops from -1.83 to roughly -0.07; BNB then joins the friction-bound cluster. **The BNB interim report's "S3 is direction-bound" conclusion was a 16-trade artifact of one outlier, not a robust cross-symbol pattern.** Treat S3 as friction-bound + tail-driven, not as direction-bound.

---

## Section 3: S3 tail analysis

**Bottom line: S3 has a missing time-stop. Worst trades are consistently 1.7-3.0x longer-held than the average trade across every symbol. The signature is unambiguous.**

| Symbol | n | sum_raw $ | worst#1 | worst#2 | worst#3 | worst-1 share | worst-2 share | mean dur (s) | worst-3 mean dur (s) | dur ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BNBUSDT | 16 | -20.28 | -12.35 (-195 bps) | -5.45 (-87.5 bps) | -3.24 (-53.7 bps) | 60.9% | 87.8% | 937 | 1,895 | 2.0x |
| BTCUSDT | 61 | -2042.77 | -228.75 (-35.5 bps) | -191.40 (-28.7 bps) | -159.36 (-24.8 bps) | 11.2% | 20.6% | 108 | 328 | 3.0x |
| ETHUSDT | 50 | -48.50 | -4.77 (-26.7 bps) | -4.66 (-26.2 bps) | -4.04 (-21.8 bps) | 9.8% | 19.5% | 103 | 251 | 2.4x |
| SOLUSDT | 33 | -1.70 | -0.36 (-48.4 bps) | -0.32 (-43.4 bps) | -0.26 (-37.1 bps) | 21.2% | 40.0% | 186 | 325 | 1.7x |
| XRPUSDT | 44 | -0.017 | -0.006 (-48.1 bps) | -0.003 (-27.1 bps) | -0.002 (-21.1 bps) | 32.5% | 50.6% | 149 | 392 | 2.6x |

Observations:
- The duration ratio (worst-3 mean / all-trades mean) is between 1.7x and 3.0x on every symbol. Bad trades *are* the long-held trades.
- BNB's tail is most extreme: 87.8% of total loss in 2 trades, both held for >1 hour (1559 s and 3553 s) versus a 937 s mean. A short hard time-stop would have terminated both before they fully developed.
- Per-symbol worst-trade bps loss is consistently 20-50 bps, with BNB an extreme outlier at -195 bps. A -30 bps hard stop on BTC/ETH/SOL/XRP, or -50 bps on BNB, would have caught the worst tails.

---

## Section 4: S2 entropy-gate effectiveness

**Bottom line: entropy collapse is not predictive — it is anti-predictive on BTC/ETH/SOL/XRP and possibly anti-predictive on BNB (low N). Tightening the threshold will *not* save S2; the signal itself is broken or its direction is wrong.**

Per-symbol raw hit-rate when S2 fires (target: ~50% if noise, <40% if wrong-direction, >60% if right-direction-but-fee-bound):

| Symbol | n | raw hit | mean raw bps | reading |
|---|---:|---:|---:|---|
| BNBUSDT | 26 | 34.6% | -1.65 | mildly anti-predictive; small enough to be sampling noise |
| BTCUSDT | 59 | **6.8%** | -3.61 | **strongly anti-predictive** |
| ETHUSDT | 71 | **8.5%** | -3.71 | **strongly anti-predictive** |
| SOLUSDT | 11 | 9.1% | -3.99 | anti-predictive but low-N |
| XRPUSDT | 23 | 13.0% | -4.06 | anti-predictive |

A 6-8% raw hit-rate on 59+71 = 130 trades is decisively non-random; the strategy is entering systematically against the realised direction on BTC and ETH. Magnitude per trade is small (-3 to -4 bps) and so the loss after fees is dominated by friction, but the *direction* of the signal is wrong. Crucially, S2 is essentially Long-only in this arm (1 Short out of 190): the inverted run will reveal whether flipping the Long->Short rule recovers a small positive edge, which is the most important single test in the inverted arm.

**Decision input for iter-4:** *invert S2 direction* is the highest-EV move. Tightening the entropy filter to halve trade count will not change the sign of the edge; it only shrinks the sample.

---

## Section 5: Iter-4 recommendation

**TL;DR ranked recommendation list:**

1. **S2 — wait for inverted-arm read, then likely invert direction permanently.** *No new replay needed for the decision; the inverted run is already in flight.* — confidence **high**.
2. **S3 — add a hard max-trade-duration time-stop (e.g. 120 s) + hard stop-loss at -30 bps.** *Needs a new 12 h replay to validate.* — confidence **medium-high**.
3. **S4 — triage the model-loading pipeline.** *No replay budget needed yet.* — confidence **high (on the triage call), N/A on outcome**.
4. **S1 — instrument rho distribution, then sweep threshold downward.** *Best done as instrumentation folded into another replay.* — confidence **medium**.
5. **S5 — defer.** Not a code problem at the strategy level.

### Details

**S2 — invert direction** *(don't rebuild the entropy filter)*
- Evidence: raw hit-rate 6.8% on BTC (n=59) and 8.5% on ETH (n=71) is far below 50% — the signal is anti-predictive, not noisy. Magnitude is small (~3-4 bps) so flipping it gives ~+3-4 bps raw, which is still below the 11 bps friction wall but no longer guaranteed loss.
- Action: rely on the **inverted-arm** result already running. If inverted S2 shows raw_bps ~= +3.5 (mirror of current -3.5) and net is still negative, S2 is **friction-bound from both sides** -> abandon, or move to maker-only fills (~0 bps). If inverted shows raw_bps clearly positive and exceeds fees, ship inverted direction.
- LoC: 0 to evaluate (already replaying); ~5 LoC to permanently invert if accepted.
- Replay required: 0 additional runs.
- Confidence: **high**.

**S3 — time-stop + hard stop-loss** *(direction is OK, tails are the killer)*
- Evidence: every symbol shows worst-3-trades duration 1.7-3.0x mean duration, and worst trade alone is 10-60% of total loss. BNB's interim "direction-bound" framing was a 1-trade artifact: ex-outlier, BNB sits in the friction band with the other 4 symbols. So S3 is not direction-broken; it has a tail-control problem.
- Action: add `if elapsed_ms > 120_000: exit()` and `if mark_to_market_bps < -30: exit()`. The 120 s cap fires often on BNB only (mean dur 937 s); on BTC/ETH it's ~+10% over mean -> fires only on the actual long tails. The -30 bps stop is the right magnitude given mean raw_bps is -3 to -7 and tails are -20 to -50.
- LoC: ~15-25 in `S3.update()`.
- Replay required: **yes**, 1x full 12 h replay. *Justification for the budget spend: the tail signature is consistent across 5 symbols (not noise), and the change is small.* This is the only recommendation worth the 12 h spend.
- Confidence: **medium-high**. The intervention is well-motivated; uncertainty is in the threshold calibration.

**Do NOT also invert S3 direction in the same replay.** The cross-symbol picture says S3 is not direction-bound (ratio in [-0.30, -0.64] ex-BNB); inverting will not help and will confound the tail-stop test.

**S1 — parametric, not data-bound**
- Evidence: `rho_below_threshold` is 67-99% of ticks on every symbol; `liquidations_below_min_events` matters only on BNB (33%). Liquidations are plentiful; the rho gate is too strict.
- Action: instrument S1 to log rho distribution (no behaviour change), then run one replay with a lower rho threshold as a sensitivity check.
- LoC: ~10 for instrumentation + 1 for threshold knob.
- Replay required: **maybe 1** — only after the instrumented dry-run reveals the rho distribution shape; otherwise we're guessing blind.
- Confidence: **medium**. We know it's parametric; we don't yet know which setting will trigger reasonable trade counts without producing junk.

**S4 — triage, do not fix**
- Evidence: `insufficient_models` >= 96% on every symbol — universally. The PatchTST artifact is either missing, unloaded, or mis-keyed. This is an infra question, not a strategy question.
- Action: 30-min investigation — check (a) is the model file actually shipped in the artifact directory, (b) does the model-loading code run on startup, (c) is the symbol key mismatched (e.g. "BTCUSDT" vs "BTC/USDT"). Do **not** start a new training run yet.
- LoC: 0 until triage tells us which of (a)/(b)/(c) it is.
- Replay required: 0 until fixed.
- Confidence: **high** that this is the right triage step; outcome unknown.

**S5 — defer**
- Evidence: 100% `single_symbol_replay_unsupported`. The single-symbol replayer cannot exercise cross-sectional logic by design.
- Action: nothing this iter. When the panel data loader exists, S5 is the first cross-sectional test.
- Replay required: 0.
- Confidence: **high**.

### Recommended iter-4 plan (in order of value)

1. **Wait on inverted-arm** for S2 verdict (zero cost, already running).
2. **Implement S3 time-stop + hard stop-loss**, run one 12 h replay.
3. **Triage S4 model loading** in parallel (no replay).
4. **Instrument S1 rho distribution** — fold into the same replay as #2 if feasible (instrumentation has no behavioural impact).
5. **Skip S5** this iter.

Total replay budget for iter-4: **1x 12 h**. Everything else is either no-replay or already running.

---

## Section 6: Open questions for the inverted run

What inverted-arm tells us that this report cannot:

1. **S2 sign-flip test (most important).** If raw_bps on the inverted arm is +3 to +4 bps on BTC/ETH (mirror of current -3 to -4), the entropy filter signal is real but its direction is just wrong. If inverted raw_bps is near zero or slightly negative, the entropy filter is producing noise, not anti-signal. **Expected: clean mirror with raw_bps in [+3, +4] bps; net still negative due to 11 bps fees.**
2. **S3 BNB outlier test.** Was the single -195 bps trade a "wrong-direction" loss or a "right-direction-but-blew-through-stop" loss? If inverted S3 on BNB shows an analogous +195 bps outlier, it's direction; if not, it's a one-off market event. **Expected: no symmetric outlier; the BNB blowout is one-time, not directional.**
3. **S3 cross-symbol mirror.** If inverted S3 raw_bps on BTC/ETH/SOL/XRP shows mean ~+5 to +7 bps (mirror), it confirms our "friction-bound, not direction-bound" reading. If it shows ~0 or also negative, S3's pressure signal is producing pure noise and the time-stop fix won't be enough. **Expected: mirror within +-2 bps on BTC/ETH/XRP; SOL is the symbol most likely to surprise.**
4. **S2 hit-rate sanity check.** If inverted S2 BTC hit-rate is ~93% (mirror of 6.8%), the entropy filter is high-confidence anti-predictive and inverting is a safe permanent change. **Expected: ~85-93% raw hit on inverted BTC/ETH.**

If the inverted arm fails to mirror any of the above, the underlying signal is noise rather than wrong-signed, which would push S2/S3 toward abandonment rather than inversion.
