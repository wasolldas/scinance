# Inverted vs Original Comparison — iter-3

**Scope.** Per-trade bps comparison of S2 (190) and S3 (204) across both arms. All numbers from `trades_all.csv`; `raw_bps = raw_pnl / (entry_price * qty) * 1e4`. Trade-by-trade matching by `entry_ts`.

## Section 4 (lead): iter-4 implication

**Kill S2. Iter-4 is S3 + infra.** S2 is not anti-predictive — it is not predictive at all on either side. Inverting made every symbol slightly worse on raw bps (agg -3.45 → -4.55) and dropped hit rate from 12.1% to 5.8% (the two should sum to ~1.0 for a true sign-flip; they sum to 0.18). The losses are an **execution/microstructure tax on whichever side the signal happens to take**, not a directional edge. No code change to S2 will recover it; only a different entry mechanism would. **Remove S2 from the iter-4 portfolio entirely.** Revised plan: (1) S3 time-stop + hard stop, 1x 12h replay — stands; (2) S4 model-loader triage — unchanged; (3) S1 rho instrumentation — unchanged; (4) S5 deferred — unchanged. Iter-4 becomes a focused 1-strategy iteration (S3) plus infrastructure on S1/S4.

## Section 1: S2 verdict

| symbol | n | raw_o | raw_i | **mirror** | hit_o | hit_i | hit_sum | fee_o | fee_i |
|--------|---:|------:|------:|----------:|------:|------:|--------:|------:|------:|
| BNB    | 26 | -1.65 | -6.35 | **-3.84** | 0.346 | 0.077 | 0.42 | 11.00 | 11.00 |
| BTC    | 59 | -3.61 | -4.39 | **-1.22** | 0.068 | 0.051 | 0.12 | 11.00 | 11.00 |
| ETH    | 71 | -3.71 | -4.30 | **-1.16** | 0.085 | 0.056 | 0.14 | 11.00 | 11.00 |
| SOL    | 11 | -3.99 | -4.01 | **-1.01** | 0.091 | 0.000 | 0.09 | 11.00 | 11.00 |
| XRP    | 23 | -4.06 | -3.94 | **-0.97** | 0.130 | 0.087 | 0.22 | 11.00 | 11.00 |
| **AGG**|190| **-3.45** | **-4.55** | **-1.32** | 0.121 | 0.058 | 0.18 | 11.00 | 11.00 |

Trade-by-trade RMS of `(raw_o + raw_i)` on BTC = 8.00 bps, ETH = 8.00 bps. A perfect mirror would be 0. The 8 bps is the **double-sided slippage** that hits whichever side the strategy chose. Fees identical to 3 decimals (sanity OK).

**Verdict: abandon.** Mirror ratio is negative (worse than original) and hit-rates sum to 0.18, not 1.0. S2 is not noise either — it's an **execution-loss-bound signal**: whichever side it picks is the side that loses ~3.5 bps to entry slippage. The iter-3 "anti-predictive" framing was an artifact of conditioning on negative outcomes; the symmetric replay refutes it. The single driving number: **agg hit-rate sum = 0.179 (expected 1.000 if direction-bound)**.

## Section 2: S3 verdict

| symbol | n | raw_o | raw_i | mirror | hit_o | hit_i | hit_sum |
|--------|---:|------:|------:|------:|------:|------:|--------:|
| BNB    | 16 | -20.09 | +12.10 | **+0.60** | 0.438 | 0.438 | 0.88 |
| BTC    | 61 |  -5.12 |  -2.88 | -0.56 | 0.197 | 0.328 | 0.53 |
| ETH    | 50 |  -5.34 |  -2.66 | -0.50 | 0.240 | 0.300 | 0.54 |
| SOL    | 33 |  -7.03 |  -0.97 | -0.14 | 0.333 | 0.485 | 0.82 |
| XRP    | 44 |  -3.31 |  -4.69 | -1.42 | 0.341 | 0.295 | 0.64 |
| **AGG**|204|  -6.27 |  -1.73 | -0.28 | 0.279 | 0.348 | 0.63 |

**BNB outlier flip — confirmed.** Trade-by-trade match on the 5 worst original BNB trades:

| entry_ts | dur (ms) | raw_o | raw_i |
|---------:|---------:|------:|------:|
| 1780502221676 | 1,559,443 | **-194.99** | **+187.14** |
| 1780529401220 | 3,553,267 |  -87.53 |  +79.59 |
| 1780558976566 |   573,775 |  -53.70 |  +45.74 |
| 1780500605601 |   830,343 |  -27.51 |  +19.53 |
| 1780587738598 |   346,400 |  -25.47 |  +17.49 |

The -195 bps trade is exactly the +187 bps trade on the inverse side (delta = 2× fee_bps ≈ 22, but here trade size dominates; the gap is the bid/ask cross). BNB tail is **direction-specific AND tail-driven** — the time-stop will cap it, but inverting *only* BNB would extract real edge.

**Verdict: confirm "friction-bound + tail-driven".** Aggregate mirror ratio -0.28 — most S3 P&L is symmetric noise dominated by fees (11 bps round-trip vs ~5 bps raw signal). BNB is a real but isolated directional pocket. The time-stop + hard-stop plan is the right call; do **not** invert S3 as a whole.

## Section 3: Tail signature (S3, worst-3 dur / mean dur)

| symbol | orig ratio | orig w3_bps | inv ratio | inv w3_bps |
|--------|-----------:|------------:|----------:|-----------:|
| BNB    | 2.02 | -112.07 | 1.20 |  -35.40 |
| BTC    | **3.05** |  -29.68 | **2.63** |  -31.44 |
| ETH    | **2.45** |  -24.92 | **5.66** |  -35.12 |
| SOL    | **1.75** |  -42.96 | **2.56** |  -42.34 |
| XRP    | 2.63 |  -32.13 | 0.53 |  -26.81 |

**The tail signature is robust on BTC/ETH/SOL** — the three symbols that matter most by trade count. Time-stop will work on these. BNB ratio collapses in inverted because the long-duration trades become *winners* there (not tail losses), which actually strengthens the time-stop case (it only kills the bad-side tails). XRP is the one symbol where the tail is direction-specific noise; flag for monitoring but not blocking.

## Cheapest follow-up if S2 call is contested

Run a 1-symbol micro-replay on BNB-only S2 with a 50 ms entry delay instrumented. If raw_bps shifts toward 0 with delay, the loss is queue-jump slippage (microstructure, not signal). If it stays at -3.5 bps, signal itself is junk. Either way, S2 stays out of iter-4.

Word count: ~720.
