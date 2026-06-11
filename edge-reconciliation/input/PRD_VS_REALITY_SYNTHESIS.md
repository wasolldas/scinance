# PRD vs Reality — Synthesis Report

**Scope.** Maps the initial `FINAL_PRD.md` hypotheses against three replay iterations (iter-3 baseline; iter-3 inverted mirror; iter-4 three-flag forensic) and the code-only iter-5 push whose empirical validation is still pending. Purpose is to scope future research, not to recap any single run.

**Status keys used in this report.**

| Verdict | Meaning |
|---|---|
| PROMISING | Concept supported by data; implementation refinement only. |
| MODIFY | Concept may work but PRD specification must change in named places. |
| ABANDON | Empirically and forensically refuted; specify the forensics that ruled it out. |
| UNTESTED | Not enough data yet; specify what would unlock a verdict. |

**Friction baseline.** Bybit taker model: ~5.5 bps/side, ~11 bps round-trip. Confirmed on every symbol in every iter. All references to "the friction wall" below mean this 11 bps figure.

---

## 1. Per-strategy verdicts

### S1 — Seismischer Cascade Detector (M14 + M15 + M26)

**PRD hypothesis.** PRD §7.1 stakes a mean-reversion-after-cascade thesis grounded in the seismology analogue: liquidations self-excite (Hawkes ρ(Φ) → 1, M14), follow a Gutenberg-Richter magnitude law and Omori aftershock-decay (M15), and propagate through a leveraged-trader population SIR-style (M26, R₀ > 1). Entry is taken *opposite the liquidation side* once ρ(Φ) > 0.85 (rising), b-value < b̄_30d − 2σ, Omori aftershock-rate active, and SIR R₀ > 1.

**What we tested.**

- iter-3 (original arm, single_pass, 5 symbols): no flag changes; observed wait-reasons only.
- iter-3 (inverted arm): irrelevant — S1 never fired, no direction to invert.
- iter-4 Push A: `--s1-rho-instrument` flag emitted the empirical ρ distribution per symbol (56k–87k samples each).

**What we observed.**

- iter-3: 0 trades on all 5 symbols. Dominant gate: `rho_below_threshold` = 67–99 % of ticks; `liquidations_below_min_events` only meaningful on BNB (33 %). The min-events floor is essentially non-binding on BTC/ETH/SOL/XRP — data supply is fine.
- iter-4 ρ-distribution per symbol (medians and tails):

| Symbol | n_samples | p50 | p95 | p99 | max |
|---|---|---|---|---|---|
| BTC | 83,597 | 2.13e-7 | 0.001 | 0.001 | 9.40 |
| ETH | 80,550 | 2.05e-7 | 0.001 | 0.001 | 7.16 |
| SOL | 87,379 | 1.92e-7 | 6.02e-7 | 1.64e-6 | 0.001 |
| BNB | 56,425 | 1.84e-7 | 5.59e-7 | 9.12e-7 | 1.32e-3 |
| XRP | 86,088 | 1.94e-7 | 5.75e-7 | 1.61e-6 | 0.49 |

The PRD's 0.85 threshold sits **six orders of magnitude** above the measured median ρ. The p95 on three of five symbols is still ~1e-6. BTC/ETH show a small numerical-floor cluster at 1e-3 plus a few isolated spikes to single-digit values (likely an internal saturation artifact or a stress moment, not a "second mode").

**Mechanism.** This is not a "we set the threshold too high" problem; it is a "the estimator we ship is the wrong instrument" problem. A single-channel Hawkes MLE fit on aggregated Bybit liquidation tape collapses to near-zero almost always. Even shifting the threshold to the empirical p95 turns ρ-crossing into a 5 % random sampler — there is no separating power between "cascade-imminent" and "normal flow" at this resolution.

**Verdict: ABANDON (as currently implemented). The cascade *concept* survives, but the M14 implementation does not.** Three forensic facts kill it: (1) liquidation supply is plentiful — not data-bound; (2) the empirical ρ distribution is unimodal-low with no fat right tail at any usable separating quantile; (3) p99 is ~1e-6, not "almost-1" — there is no critical-state signature being detected. M15 and M26 are downstream of M14 in S1's entry rule and inherit the same blocker.

**Open research questions.**

- Is the structural gap in M14 the single-channel reduction (PRD's 6-D scheme assumed separate MO+/MO−/LO+/LO−/CX+/CX− plus exogenous Long-Liq/Short-Liq)? Would a 2-channel split already lift the upper-tail of ρ into a usable range?
- Was the 0.85 threshold imported from Bacry-Mastromatteo-Muzy without anchoring on Bybit liquidation density? If the right number on Bybit is ~0.3, does the rest of the cascade thesis survive?
- Is "ρ-crossing" the wrong trigger geometry entirely — should it be a clustering-window trigger (Aalen/Cox intensity ratio over 60 s vs 1 h baseline)?
- Does M14 fail equally on known historical cascades (Mar 2020, Oct 2025 19B-liq)? Replaying ρ over those windows is the cheapest way to separate "estimator broken" from "no cascades in this 24 h sample."
- Do M15 (b-value, Omori) and M26 (SIR R₀) actually agree with M14 on the same critical moments, or do they trigger on different events? The PRD's "three orthogonal confirmations" claim has never been tested.

---

### S2 — Entropie-Momentum (M6 + M2 + M22 + M7)

**PRD hypothesis.** PRD §7.2: Shannon-entropy collapse on the L2 book (M6) signals institutional synchronisation; OFI (M2) reveals which side the institutional aggression sits on; funding-pressure (M22) confirms that the same side is also macro-stressed; PE (M7) gates the whole thing as a Greenlight. The trade *follows* the OFI direction. PRD's literal description in §7.2: "institutionelle Aggression sichtbar in OFI + Order-Book-Strukturzusammenbruch."

**What we tested.**

- iter-3 original arm: baseline 5-symbol replay.
- iter-3 inverted arm: every entry flipped Long↔Short.
- iter-4 Push A: `--s2-maker-only` flag set entry+exit fees to zero — the "is there a hidden raw edge masked by friction?" forensic.

**What we observed.**

| Test | n | mean raw_bps (agg) | raw hit-rate | direction skew |
|---|---|---|---|---|
| iter-3 original | 190 | −3.45 | 12.1 % | 189/190 Long |
| iter-3 inverted | 190 | −4.55 | 5.8 % | 1/190 Long |
| iter-4 maker-only (fees=0) | 190 | −3.45 (raw=net) | ~12 % | 189/190 Long |

Mean dur on S2 was 6.1 s (max 88 s) — these are sub-minute scalps.

**Mechanism.** Three forensics, each kills a different escape hypothesis:

1. **Original arm → "anti-predictive direction" hypothesis.** Raw hit-rate 6.8 % on BTC (n=59) and 8.5 % on ETH (n=71) read like a confident wrong-sign signal.
2. **Inverted mirror → refutes hypothesis (1).** A genuine sign-flip would push hit-rates to ~85–93 %; instead they fell to 5.1 %–8.7 % on BTC/ETH and the aggregate raw worsened from −3.45 to −4.55 bps. The original and inverted hit-rates summed to **0.18**, not the ~1.0 a true direction-flip would produce. The 8 bps trade-by-trade RMS of `(raw_o + raw_i)` is the diagnostic for an **execution/microstructure tax** that hits whichever side the strategy picks — not a directional signal at all.
3. **Maker-only → refutes "hidden raw edge bound by friction".** With fees identically zero on every trade, the raw aggregate stays at −3.45 bps; every symbol still loses on raw alone. The best-case symbol (BNB) is −1.65 bps/trade; worst (XRP) is −4.06 bps.

The signal has no directional edge in either sense and no hidden friction-bound edge. It is, mechanically, an entry-time microstructure cost ("queue-jump tax" on sub-10-second positions where M2's OFI is computed on the same book that immediately consumes the entry).

**Verdict: ABANDON.** Three independent forensics — direction, mirror, friction — all returned negative. The PRD's "follow institutional aggression" framing fails because the OFI-marked "aggression" on Bybit at this timescale is not informed flow; it is the side about to be faded by MM replenishment, and entering with the OFI sign systematically pays the queue-jump cost. This is not a sign-tweak away from working; it is a wrong-signal-definition problem.

**Open research questions.** (Conceptual threads, not S2-rescue tickets.)

- Is the *entropy-collapse premise* (M6) salvageable as a **regime gate** for another strategy, even though it has no edge as an entry signal? PRD already lists Shannon-L2 as a Layer-3 Greenlight; iter-3/4 never tested it in that lighter role.
- Is M2's OFI sign convention mis-labelling MM replenishment as informed flow? That would implicate M2 as a *module* (feeding M9 and M14) with cascade effects far beyond S2.
- Does the entropy + OFI + funding-pressure combination work at a longer holding horizon (minutes-to-hours)? S2's mean dur is 6 s — the friction-to-edge ratio is fatal at that horizon regardless of signal quality.
- Is *low entropy → momentum* the wrong inference even conceptually? An alternative read is *low entropy → consumed-book → mean-reversion*. The maker-only test rules out "wrong direction" — but a fade-the-book re-derivation of the same trade timestamps has not been run.

---

### S3 — Pre-Settlement Pressure-Release (M22 + M23 + M24 + M8)

**PRD hypothesis.** PRD §7.3: the funding-clamp mechanic is deterministic — Bybit caps F at ±0.05 %, so when the true premium exceeds the cap, undischarged pressure builds and releases mechanically in the settlement window. PRD describes the edge as *"timing-präzise, nicht direktional-prognostisch"*: the trader is not predicting which way price will move, only that movement releases the bottled pressure in the side-of-pressure direction. M23 (basis) and M24 (Kalman premium) confirm direction; M8 (BOCPD) vetoes during concurrent OI break.

**What we tested.**

- iter-3 original: baseline.
- iter-3 inverted: mirror.
- iter-4 Push A: `--s3-time-stop` (120 s wall-clock cap) and `--s3-hard-stop` (−30 bps MTM) both engaged.
- iter-5 (code shipped, validation pending): T1 fixes the wall-clock-vs-market-clock bug in the time-stop; T2 reframes the hard-stop as friction-aware projected-net.

**What we observed.**

| Test | n | mean raw_bps (agg) | direction skew | tail signature |
|---|---|---|---|---|
| iter-3 original | 204 | −6.27 (net) ≈ +4.7 raw after stripping 11 bps fees | 100 % Long | worst-3 dur ratio 1.7×–3.0× across 5 symbols |
| iter-3 inverted | 204 | −1.73 net; BNB flips +12.10 | 100 % Short | tail still present on BTC/ETH/SOL |
| iter-4 (both stops on) | 213 | −16.81 net | dominantly Long | 68 trades >120 s; 33 trades < −30 bps; hard-stop fired 13×; time-stop fired **1×** |

The iter-3 BNB tail (−195 bps / 1559 s) mirrored cleanly to +187 bps in the inverted arm — confirming that *the worst BNB trade was directional, not random noise*. Aggregate iter-3 mirror ratio on the other four symbols was −0.28 — predominantly symmetric noise around the friction wall.

**Mechanism — two-part finding.**

1. **The entry side roughly matches the PRD claim.** Cross-symbol raw is small-negative-near-zero (consistent with "timing-präzise, nicht direktional-prognostisch"). The signal is *not* anti-predictive — the iter-3 mirror only weakly reverses (−0.28 ratio); most P&L is fee-driven symmetric noise. BNB is the one symbol showing a real directional pocket atop the same noise.
2. **The exit side kills it.** The cross-symbol tail signature (worst-3 dur ratio 1.7–3.0×) says long-held trades are the losers. PRD's mechanism-based exits ("Settlement-Tick + 10 min OR funding band reset") do not bound loss when the mechanism fails to fire. iter-4 retrofitted both a 120 s wall-clock cap and a −30 bps hard-stop, and surfaced two bugs: the time-stop used `time.time()` (wall-clock) inside a fast replay so 68 trades crossed 120 s in market time but only 1 triggered (**iter-5 T1 fix**); the hard-stop measured raw MTM but `pnl_bps` is net of friction so 33 trades exited below −30 bps net via `pressure_dissipated` before the raw hard-stop fired (**iter-5 T2 fix**).

**Verdict: PROMISING. Pending iter-5 empirical validation. Most likely to become MODIFY after that run.**

The only strategy in the portfolio where the entry concept survived two forensic challenges (original raw ≈ small-negative, mirror weak — friction-bound, not anti-predictive), the failure mode is mechanically diagnosed, and the fix is code-only with no change to the signal definition. iter-5 tells us whether the time-stop now fires 60–70× (expected from the iter-4 dur distribution), whether the friction-aware hard-stop catches the 33 sub-(−30 bps) tails, and whether net mean_pnl_bps crosses zero on any symbol.

**If iter-5 shows S3 net-positive on ≥ 2 symbols, this becomes the first PRD-validated edge.** If it remains net-negative, the verdict shifts to MODIFY — at that point the PRD's implicit "post-settlement reversion always arrives" assumption is what has to change, not the entry signal.

**Open research questions.**

- After iter-5: does S3 net-clear the friction wall, and on which symbol set? Is BNB still the carrier (consistent with the directional-pocket evidence from the iter-3 mirror), or does it spread?
- What is the empirical distribution of the M22 pressure quantity? Does the PRD's "|Pressure| > Q90 (rolling 30d)" threshold actually trigger on this data, or is the current entry rule over-triggering on sub-Q90 noise and underweighting the actual settlement window?
- Does M8 BOCPD veto any losing trades? PRD §7.3 places BOCPD as the regime veto; iter-3/4 never separated veto-survived from veto-bypassed entries.
- Is the symmetric-noise reading (mirror ratio −0.28 ex-BNB) compatible with the PRD's "timing-präzise" claim, or is the timing itself coin-flip and BNB's small alpha a different mechanism?
- 24 h windows yield 3 settlements per symbol; is that enough to falsify a settlement-mechanic claim, or is a 7-day window (21 settlements) the minimum statistical floor? (See §2.4.)

---

### S4 — Pattern × Foundation Ensemble (M5 + M16 + M20 + M18)

**PRD hypothesis.** PRD §7.4 builds a variance-reduction ensemble: M16 (TFSAX + Smith-Waterman), M18 (PatchTST), and M20 (MOMENT) carry idiosyncratic forecast noise; trade only when ≥ 2 of 3 agree with directional Pearson > 0.6 AND TFSAX match-score > 0.75. M5 (FFD) preprocesses everything. PRD positions this as Phase-3, ML-infra-heavy.

**What we tested.** Nothing. All three iters: 0 trades on all 5 symbols. Dominant wait-reason on every symbol: `insufficient_models` = 96–99.99 % of ticks. `insufficient_price_history` is 2–10 ticks (irrelevant).

**Mechanism.** Architecture-bound: the model artifacts are missing, unloaded, or mis-keyed at startup. None of M18 / M20 / M16 produced a single live forecast in any iter. We have not observed an ensemble disagreement, let alone a consensus.

**Verdict: UNTESTED.** This is the cleanest UNTESTED of the five — not even the components ran, so there is nothing the PRD claim could be falsified against. The PRD thesis (variance reduction via orthogonal forecasters) is also a well-established ML principle that iter-3/4 data could not have contradicted in either direction.

**Open research questions.**

- *Cheapest unblock*: which of (a) artifact missing, (b) loader not wired, (c) symbol key mismatch is the cause? 30-min triage answers this with 0 replay-budget.
- *Independence before ensemble*: the PRD's variance-reduction argument presumes M16/M18/M20 are each individually weak-but-positive. That assumption is itself untested. Does PatchTST alone produce direction-accuracy > 50 % at any horizon?
- *Infrastructure cost vs expected value*: S4 is the highest-infra-cost strategy in the PRD. It should remain deferred until S3 (and possibly a redesigned S1) are net-positive — building three forecasters into an ensemble is wasted if the market lacks the underlying forecastability.
- Is the *TFSAX library prerequisite* (M16: "5 y Bybit-Historie") even compatible with Bybit's listing turnover? Many alts have <2 y of clean tape; does S4 reduce to a BTC-ETH-only strategy by data availability alone?

---

### S5 — Cross-Sectional Ergodicity Reversion (M13 + M17 + M9)

**PRD hypothesis.** PRD §7.5: in an ergodic system, time-average and ensemble-average converge; a single symbol's recent time-average wandering far from the contemporaneous ensemble mean (|z| > 2.5) is statistically over-extended and mean-reverts. M17 (Rényi-TE) filters for genuine reversion candidates (BTC actively transmitting information into the alt); M9 (HMM) vetoes during crash regimes.

**What we tested.** Nothing. All three iters: 0 trades. Dominant wait-reason: `single_symbol_replay_unsupported` = 100 % of ticks.

**Mechanism.** Harness-bound, *not* strategy-bound. The replay infrastructure runs symbol-by-symbol; S5 needs a synchronised multi-symbol panel. The strategy code was never asked a question it could answer.

**Verdict: UNTESTED.** The most aggressive UNTESTED of the five — the obstruction is one level deeper (replay harness) than S4 (model loader).

**Open research questions.**

- Infrastructure prerequisite: panel replayer feeding synchronised returns across ≥ 5 symbols. Without that all of M13/M17/M9 stays dormant.
- *Before the full strategy*: on the iter-3 panel, is unconditional |z| > 2.5 → forward-reversion present at all? On a 5-symbol BTC-dominated universe cross-sectional reversion may have no statistical power; this is the cheapest litmus for whether the "ergodicity reversion" framing translates to Bybit.
- PRD's Top-20-perp universe (M13) is materially larger than the iter-3 5-symbol set. Does 5→20 change the conclusion? Five BTC-correlated symbols may be too tightly constrained to ever produce |z| > 2.5.
- M17 (Rényi-TE) is conceptually independent of the harness blocker. Could it be tested standalone as a feature for some other strategy?

---

## 2. Cross-cutting findings

### 2.1 Friction model

PRD §8 specifies Bybit Taker 0.055 % / Maker 0.02 %; confirmed exactly in every iter (~11 bps round-trip). **What the PRD did not internalise** is the friction-vs-holding-horizon interaction: S2 mean dur 6.1 s makes the friction-to-edge ratio fatal; S3 mean dur 163 s (iter-4, tails to 2125 s) keeps friction a large fraction of raw edge. PRD's per-strategy validation criteria (M2: Sharpe ≥ 1.0 after 2 bps fees; M22: Sharpe ≥ 1.5) implicitly assume horizons where 11 bps amortises into a small fraction of P&L — iter-3/4 prove the friction wall is the dominant signal for short-holding strategies.

**PRD revision the data calls for**: every §7 strategy spec should carry an explicit "minimum raw edge ≥ 2× round-trip friction (~22 bps)" gate, OR a "minimum holding time" floor, OR a maker-only stipulation with documented queue-position model. The PRD has none of these.

### 2.2 Module-level estimators

The S1 ρ-distribution forensic is the most consequential cross-cutting finding because it implicates **M14 itself**, not just S1's wrapper. M14 also appears in any future cascade-detection routing.

Other modules with empirical reasons to be suspect:

- **M2 (OFI Cont-Kukanov-Stoikov)** is implicated by S2's failure across three forensics. Friction is ruled out by maker-only; direction by the mirror; what is left is that M2 mis-labels MM replenishment as informed flow. M2 also feeds M9 (HMM features) and M14 (Hawkes event extractor) — contagion potential is large.
- **M22 (Funding-Clamp Pressure)** has not been directly distribution-checked. The |Pressure| > 2σ entry rule may be over-triggering on sub-Q90 noise (S3 fires 50–60 trades per symbol in 24 h vs only 3 settlements — far more entries than the "settlement-window" framing implies).
- **M8 (BOCPD)** veto rate in S3 has never been instrumented.
- **M16/M18/M20** are UNTESTED at the level S4 needs them.

Unifying point: the PRD specifies module-level validation criteria (M2: R² ≥ 0.05; M8: detection latency ≤ 2 min) but the replay harness has never exercised these as standalone tests. Strategies are integration tests over multiple modules at once; failures cannot be cleanly attributed to specific modules.

### 2.3 Direction biases

- **S2 traded ~100 % Long across 190 trades.** The entry rule explicitly conditions on `sign(Funding-Pressure) == sign(OFI)` — but in iter-3/4 those signs are co-incidentally Long on every symbol. The strategy never had occasion to fire Short.
- **S3 traded 100 % Long in the original arm.** The PRD's premium-index → direction mapping (M23: `Basis > 0.0008 → Short Perp`, etc.) was either never triggering the Short branch, or the basis sign across this 24 h window was uniformly one-sided.
- **The 100 % Long bias is symbol- and window-specific, not necessarily strategy-specific.** A bull-skewed 24 h window would naturally produce one-sided signals from any premium / basis / OI-pressure mechanic. We cannot tell from current iters whether the PRD's direction mapping is *correct* or *partial-but-window-dependent*.

**PRD revision: explicit conditioning.** PRD §7.2 and §7.3 should specify a *symmetric-coverage test* — over a sufficiently long replay window, what fraction of fires are Long vs Short? If a strategy fires 100 % Long for 24 h on 5 symbols, that is either expected (bull window) or a symptom of an entry rule that cannot fire Short — the PRD does not currently distinguish.

### 2.4 Time-frame mismatch between PRD and replay

PRD horizons span sub-second OFI through 24h+ pattern matching. The replay window is ~24h per symbol.

- **Sub-minute claims are well-covered** (S2 failure robust; S1 ρ well-sampled at 56k–87k snapshots).
- **Settlement-window claims (S3) are borderline.** 24h = 3 settlement events × 5 symbols = 15 events; iter-3/4 fired 50–60 S3 trades per symbol — far more than the settlement-window framing implies. Either the entry rule is not gated tightly to settlements, or the |Pressure| > Q90 threshold over-triggers in non-settlement segments.
- **Cascade claims (S1) need historical cascade episodes.** A 24h window may not contain a cascade large enough to fire ρ > 0.85 regardless of estimator quality. Replaying ρ over Mar 2020 / Oct 2025 cascades is the only way to separate "estimator broken" from "no cascade in this window."
- **S4 and S5 are infrastructure-blocked separately**, so horizon is academic for them.

PRD §4 validation criteria like M14's "ρ steigt ≥ 0.7 ≥30 s vor 80 % der historischen Kaskaden" implicitly require a *cascade-bearing* sample. The 24h replay protocol is not a falsification ground for those claims — only for the always-on signals.

### 2.5 Bounded-loss exits

The PRD specifies exits per-strategy, mechanism-based (S1: ρ < 0.5 or Omori decay; S3: settlement-tick + 10 min; S5: |Z| < 0.5 or 24h time-stop). **No strategy in the PRD specifies a hard loss-based stop.**

iter-4 retrofitted both a wall-clock time-stop and a hard-MTM stop on S3. Both were necessary; both surfaced implementation bugs; iter-5 ships fixes. The general lesson: every mechanism-based exit in the PRD is conditional on the mechanism firing — when it does not, there is no fallback.

**PRD revision: lift bounded-loss into a system-level policy.** Each trade should carry a (max-loss, max-duration) tuple as a non-negotiable system-level guarantee, with mechanism-based exits as the desirable-case path inheriting the guarantee. No reason to think the other strategies are immune to the failure mode S3 surfaced.

---

## 3. Action matrix

| Item | Verdict | Required input to advance | Estimated effort | Blocker for what? |
|---|---|---|---|---|
| **S1 — cascade detector** | ABANDON (current M14 form) | (a) ρ distribution on known historical cascades (Mar 2020, Oct 2025) to confirm estimator failure vs no-cascade sampling; (b) decision on whether to rewrite M14 as 2-channel (Long-Liq / Short-Liq) or move to clustering-window trigger | Forensic: 1 historical replay (1 week of 2020 data). Estimator rewrite: 2–4 weeks. | Any cascade-detection routing; any L4 trigger that consumes M14 |
| **S2 — entropy-momentum** | ABANDON | None for ABANDON verdict. To resurrect: re-derive S2 as fade-the-book on the *same* iter-3/4 trade timestamps and re-check raw hit-rate; investigate whether M2 OFI sign convention itself is mis-labelled | Re-derive: 1–2 days code, no new replay. M2 audit: 2–3 days. | Any strategy reusing M2 (M9 features, M14 event-extractor); resolves a Layer-1 confidence question |
| **S3 — pre-settlement pressure** | PROMISING (pending iter-5 validation) | iter-5 overnight run with T1+T2 fixes; per-symbol net-pnl_bps, time-stop fire count, hard-stop fire count, trade count diff vs iter-4 | iter-5 replay already ready; analysis ~2 h | Push C Demo Trading (PRD §8 Phase 4); first PRD-validated edge |
| **S4 — pattern ensemble** | UNTESTED | 30-min triage of model loader (artifact / wiring / key); standalone forecast quality test on at least one of M18/M20 before discussing the ensemble | Triage: <1 day. Standalone forecast eval: 1–2 weeks. | All of Phase 3 PRD work; any decision on retiring the ML-forecast layer |
| **S5 — cross-sectional reversion** | UNTESTED | Panel replayer infra (synchronised multi-symbol on_data); standalone test of |z| > 2.5 → forward-reversion on iter-3 panel before lighting up full rule | Panel harness: 1–2 weeks. Z-test alone: 2–3 days once harness exists. | Phase 4 PRD work; final-iteration portfolio diversification claim |
| **Friction model in PRD** | MODIFY | Add per-strategy "minimum raw edge ≥ 2× friction" OR "minimum holding time" gate to PRD §7; document maker-only rebate path | PRD doc revision: 1 day | Resolves the "short-holding strategy" failure mode at spec level |
| **M14 module-level** | ABANDON in current form | See S1 row | See S1 row | See S1 row |
| **M2 module-level** | SUSPECT (audit needed) | Re-check OFI sign convention; standalone R² ≥ 0.05 validation (PRD M2 criterion) on iter-4 raw orderbook tape | 2–3 days | S2 resurrection; HMM (M9), Hawkes (M14) event extractor cleanliness |
| **M22 module-level** | NEEDS INSTRUMENTATION | Distribution forensic on `|Pressure_t|` per symbol; verify Q90 threshold (PRD M22) maps to reasonable trigger rate | 1 day instrumentation + 1 replay | S3 entry-rule confidence; understanding why 50+ trades/24 h vs 3 settlements |
| **M8 module-level (BOCPD veto)** | NEEDS INSTRUMENTATION | Log P(Change-Point) per S3 entry decision; report fraction of entries vetoed | <1 day instrumentation | S3 conceptual clarity (does the veto matter or is it decoration?) |
| **Direction bias** | NEEDS LONGER REPLAY | 7-day replay window per symbol to surface symbol-window-symmetric vs strategy-asymmetric fires | 1 replay × ~7d wall-clock | S2/S3 directional-correctness claim; falsifiability of premium → direction mapping |
| **Time-frame mismatch** | MODIFY (PRD spec) | Specify which PRD claims are testable on 24 h vs require 7d/30d; identify cascade-bearing historical windows for S1 forensics | PRD doc revision: 1 day | S1 verdict finalisation; honest scoping of S3 over 21+ settlements |
| **Bounded-loss as system-level policy** | MODIFY (PRD spec) | Lift the (max-loss, max-duration) tuple from S3's retrofit into PRD §8 as a system-level policy applying to all strategies | PRD doc revision: 1 day | All future strategy specs; consistent risk-of-ruin floor |
| **Module-level standalone tests** | MISSING | The PRD specifies M-level validation criteria but no harness exercises them standalone; needs a per-module test fixture | 1–2 weeks scaffolding | Attribution of any strategy failure to specific module-level cause |

---

## 4. Closing read

Three iterations plus the pending iter-5 reduce the PRD's "diversified microstructure portfolio" to a narrower picture:

- **One strategy survives forensic scrutiny on entry concept** (S3), conditional on iter-5.
- **One strategy is dead across three forensic replays** (S2) with no remaining escape hypothesis.
- **One strategy is structurally blocked by an estimator six orders of magnitude off** (S1 via M14); the cascade concept may survive a PRD-level M14 redesign.
- **Two strategies are dormant infrastructure projects** (S4 model loader; S5 panel replayer), each gating a much larger downstream PRD section.

The single most important PRD revision is **lifting the friction-vs-holding-horizon constraint and the bounded-loss policy into the spec itself**. The single most valuable next replay-window is **iter-5 validation of S3** — the one question whose answer determines whether "first edge ships to Demo Trading" or "no strategy meets the threshold, portfolio reverts to PRD redesign" is the next mode.
