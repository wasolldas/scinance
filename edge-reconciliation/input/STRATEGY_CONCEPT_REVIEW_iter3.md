# Strategy Concept Review — Iter-3

**Scope:** Conceptual review of S1–S5 against the original PRD theses, using the iter-3 original-arm analysis as ground truth. Inverted-arm replay is still running; any verdict relying on a sign-flip is flagged.

**Sources:** `FINAL_PRD.md` §§7.1–7.5 and §4 method catalog; `ANALYSIS_REPORT_iter3.md` Sections 1–6; strategy docstrings in `src/bybit_edge/strategies/`.

---

## S1 — Seismischer Cascade Detector

### 1. The original thesis
PRD §7.1 framed S1 as a mean-reversion trade *after* a liquidation cascade has burned itself out. The economic mechanism is borrowed from seismology: liquidations are forced, fair-value-blind sellers; their selling self-excites (Hawkes ρ → 1) until the leveraged trader population is exhausted (SIR R₀ collapses, Omori aftershock-decay sets in). At that exhaustion point, the price has overshot fundamentals and the supply of forced sellers is empty — mean-reversion is mechanical. The trade direction is explicitly *opposite* the liquidation side ("Long-Liqs → Long-Entry nach Klimax").

### 2. What the data says
Zero trades on every one of the five symbols (Section 1, S1 block). The binding gate is `rho_below_threshold` (67–99% of ticks); `liquidations_below_min_events` matters only on BNB. The strategy *sees* plenty of liquidations on BTC/ETH/SOL/XRP — it just never observes ρ(Φ) above 0.85. We have no observed trades, no observed PnL, no hit-rate.

### 3. Does the thesis hold?
**Verdict: thesis untestable from current data.** The cascade-mean-reversion hypothesis is intellectually clean and the supporting machinery (Hawkes, GR/Omori, SIR) is intact, but with zero firings we cannot adjudicate the economic claim at all. What we *can* say is that the calibration assumption — "ρ > 0.85 marks a true critical state on Bybit perps" — does not match the empirical distribution of the ρ we are actually computing. Either the single-channel Hawkes estimator is shrinking ρ relative to a 6-D ground truth, or 0.85 was a literature number imported without re-anchoring on Bybit liquidation density. The Section-1 diagnostic that liquidation counts *are* sufficient (the "min_events" gate is mostly non-binding) is the important news: this is a threshold problem, not a data-availability problem.

### 4. Conceptual adjustment
The first move is *instrumentation*, not parametrization. Before deciding whether the cascade thesis is right, we need to see the *empirical distribution* of ρ on each symbol — is it bimodal (regime-like, consistent with theory) or unimodal-and-low (suggesting our 1-D Hawkes simply cannot reach the 6-D criticality the PRD assumed)? If the distribution is bimodal but its upper mode sits at, say, 0.6 not 0.9, the cascade thesis survives but the calibration constant was imported from a different microstructure regime and needs re-anchoring. If the distribution is unimodal-low with no fat right tail, the *measurement instrument* — single-channel Hawkes on aggregated liquidations — is too coarse to detect criticality, and the conceptual experiment shifts from "tune ρ" to "build a richer event-process before we can even ask the cascade question." Either way, the next conceptual experiment is "what does ρ actually look like on Bybit in a known cascade episode (e.g. the historical mainshocks the PRD references)?" — that is the minimum data needed to keep or kill the thesis.

---

## S2 — Entropie-Momentum

### 1. The original thesis
PRD §7.2 frames S2 as a microstructure *momentum* trade. The chain of inferences: a Shannon-entropy collapse on the L2 book means liquidity is concentrating into a few large levels — read as institutional synchronisation; OFI then reveals *which* side that institutional aggression sits on; funding-pressure confirms that the same side is also under macroscopic stress. The trade follows the institutional aggression. The implicit economic claim: when retail-style randomness drops out of the book, the residual flow is informed flow and one should *go with it*.

### 2. What the data says
190 trades total, 189 of them Long (Section 1, S2 block). Raw edge is negative on every symbol (−1.65 to −4.06 bps), well inside the ±11 bps friction wall. The damning number is the raw hit-rate (Section 4): 6.8% on BTC (n=59) and 8.5% on ETH (n=71). That is not noise. A random signal would print ~50%; a fee-bound but directionally-correct signal would print >50% with a small magnitude. We are seeing a signal that systematically enters *against* the realised 5-second direction.

### 3. Does the thesis hold?
**Verdict: thesis broken.** The PRD's framing — "follow the entropy-collapse + OFI consensus" — is exactly inverted relative to what BTC and ETH did over 130 trades. A 6–8% hit-rate is a high-confidence anti-signal, not a coin-flip we can rescue with tighter thresholds. There is a real signal in the entropy collapse, but the *direction* attached to it by §7.2 is wrong. **Note: the final confirmation that this is "inverted-direction" rather than "uncorrelated noise dressed up as anti-signal" is inverted-arm-dependent** — if the inverted run shows raw_bps near zero on BTC/ETH, the signal is noise; if it mirrors at +3 to +4 bps, the signal is real-but-misdirected. The analysis report's expected mirror is the relevant test.

### 4. Conceptual adjustment
The conceptual reframe is the punchline: entropy collapse on Bybit perps at this timescale is not a momentum signal, it is a *mean-reversion* signal. Liquidity concentrating onto a few levels is *consumed* by the next aggression rather than amplifying it — the levels are a wall, not a launchpad, and OFI marks the side that is about to be faded rather than the side that wins. The PRD's underlying premise that "low entropy = informed flow detectable from the book" survives; what dies is the directional rule "go with OFI." The conceptual experiment for iter-4 is to re-derive S2 as a fade-the-book strategy: when entropy collapses and OFI says Long, take Short. There is also a contradiction to flag explicitly between PRD/docstring ("institutional aggression in OFI") and observed behaviour: either the OFI we are computing labels MM-replenishment as "aggression" (a sign-convention bug masquerading as a signal bug), or the institutional read of OFI is simply wrong for this venue. Investigating *which* of those two is true is a more important next step than re-tuning the entropy z-score.

---

## S3 — Pre-Settlement Pressure-Release

### 1. The original thesis
PRD §7.3 stakes its claim on the funding-clamp mechanic: Bybit caps funding at ±0.05%, so when the *true* premium exceeds the cap, real pressure builds up undischarged and releases mechanically in the settlement window. The edge is described as "timing-präzise, nicht direktional-prognostisch" — the trader is not predicting which way price will go, only that *something* will move when the dam breaks, in the direction the pressure was bottled up in. M23 (basis) and M24 (Kalman) are supposed to confirm direction; M8 (BOCPD) is a veto filter against concurrent regime breaks.

### 2. What the data says
204 trades, 100% Long, raw edge negative on every symbol (−3.31 to −20.09 bps; the −20 bps on BNB is one trade of −195 bps — Section 3). Ex-BNB-outlier, edge-to-friction ratios sit in the friction band (−0.30 to −0.64). The unambiguous cross-symbol signature is in Section 3: worst-3 trades are 1.7×–3.0× longer-held than the average trade on every symbol. The losing trades are *the long-held trades*.

### 3. Does the thesis hold?
**Verdict: thesis confirmed (but execution broken).** The entry side of the PRD claim is essentially fine: ex-outlier, BNB joins the friction-bound cluster and the modal trade is small-negative-near-zero raw, exactly what one would expect of a deterministic-timing thesis with no directional alpha but a roughly-symmetric raw outcome. The thesis's own self-description — "timing-präzise, nicht direktional-prognostisch" — is consistent with the small-magnitude raw distribution. What kills the strategy in iter-3 is the *exit* side: there is no time-stop and no hard stop-loss, so a small fraction of mistimed entries develop into long-held losers that consume the entire P&L. The PRD's exit rule ("Settlement-Tick + 10 min OR funding band reset") is mechanism-based; the data shows that mechanism failing to fire often enough on the bad trades. The binding execution constraint is *bounded loss per trade*, not signal quality.

### 4. Conceptual adjustment
Stay at concept altitude: the missing concept is *risk-of-ruin management*, not signal redesign. The PRD treated S3 as a clean mechanical bet on a calendar event and inherited an implicit assumption that the post-settlement reversion would always arrive on schedule — sometimes it does not, and when it does not, the strategy is trapped in a position with no plan. The conceptual fix is to attach a fixed-budget rule to every settlement bet: each entry is allowed to consume at most a known fraction of capital and a known wall-clock window before being closed unconditionally. That is the same concept that turns a positive-expectation casino bet into a survivable strategy. It does not require revisiting whether the entry is right; it requires accepting that the entry will be wrong some non-negligible fraction of the time and pre-committing to the exit. **One caveat: confirmation that S3 is symmetric-around-zero rather than directionally wrong is inverted-arm-dependent** — if inverted-S3 also prints negative raw, the entry concept dies too. Until that returns, treat the "execution-broken" verdict as the most likely but not yet final reading.

---

## S4 — Pattern × Foundation Ensemble

### 1. The original thesis
PRD §7.4 builds an *ensemble* edge: each of TFSAX (M16), PatchTST (M18), and MOMENT (M20) carries idiosyncratic forecast noise; only when at least two of them agree on direction *and* their pairwise correlation is high should we conclude that there is a non-idiosyncratic pattern in the price. The economic mechanism is variance reduction over orthogonal forecasters, not a single causal story about microstructure. The PRD positions this as a Phase-3 strategy that requires substantial ML infrastructure (5-year SAX library, fine-tuned transformer, foundation-model loader).

### 2. What the data says
Zero trades on every symbol. The dominant wait-reason is `insufficient_models` covering 96–99.99% of ticks (Section 1, S4 block). The analysis report flags this as architecture-bound: the model artifacts are either missing, unloaded, or mis-keyed. We have not observed a single ensemble forecast, let alone a forecast disagreement we could learn from.

### 3. Does the thesis hold?
**Verdict: thesis untestable from current data.** This is the cleanest "untestable" of the five — not even the components are running, so there is nothing to evaluate at the strategy level. The PRD thesis (variance reduction via orthogonal forecasters) is a well-established principle in ML and not something iter-3 data can falsify in either direction. What iter-3 *does* tell us is that S4 is the highest-infrastructure-cost strategy in the portfolio: it depends on three independent ML pipelines being live, plus a Phase-3 SAX library that takes weeks to build. The cost-of-test is large.

### 4. Conceptual adjustment
The minimum infrastructure that unblocks the test is, in order: (1) confirm at least one of the three forecasters is producing real predictions on a live tick stream, (2) measure the standalone forecast quality of that single model before assembling the ensemble. The PRD's variance-reduction argument is only meaningful if each component is independently better than random — if PatchTST alone has near-zero directional accuracy on Bybit perps, no amount of pairwise correlation gating saves the ensemble. The conceptual experiment is therefore not "wire up all three"; it is "prove one of them is forecasting *anything* useful, then talk about the ensemble." This is a deliberate downscoping of the PRD thesis: §7.4 implicitly assumes the components are individually weak-but-positive; that assumption itself is untested.

---

## S5 — Cross-Sectional Ergodicity Reversion

### 1. The original thesis
PRD §7.5 leans on a deep statistical-physics premise: in an ergodic system, time-average and ensemble-average converge; when a single symbol's recent time-average wanders far from the contemporaneous ensemble mean (|z| > 2.5), it is *statistically* over-extended and should mean-revert. M17 (Rényi-TE) is supposed to filter the candidates: a high-z symbol is a real reversion candidate only if BTC is actively transmitting information into it (the move is BTC-driven, not idiosyncratic). M9 (HMM) vetoes during crash regimes where ergodicity assumptions break down.

### 2. What the data says
Zero trades on every symbol. 100% of ticks rejected with `single_symbol_replay_unsupported` (Section 1, S5 block). The replay harness itself cannot exercise S5: the strategy requires a multi-symbol panel and the iter-3 replay ran symbol-by-symbol. No statement about the thesis is possible from this data.

### 3. Does the thesis hold?
**Verdict: thesis untestable from current data.** This is the most aggressive "untestable" of the five because the obstruction is architectural at the *harness* level, not the strategy level — even the components were never asked a question they could answer.

### 4. Conceptual adjustment
The infrastructure prerequisite is a panel replayer that feeds synchronised returns across at least 5–10 symbols into S5's `on_data` interface. Without that, the strategy is dormant code. Once the harness exists, the *first* test of the thesis is not the full S5 trade rule — it is the simpler intermediate question: across the iter-3 universe, is the |z| > 2.5 → reversion empirically present at all? If the cross-sectional Z-score has no predictive power on these five symbols (which is a real possibility on a small, BTC-dominated universe), the Rényi-TE filter and HMM veto are decorations on a non-existent edge. The conceptual experiment is "measure the unconditional cross-sectional reversion strength on the panel before lighting up the full strategy." That is also a useful diagnostic for whether the PRD's choice of "ergodicity reversion" framing — borrowed from physics — actually translates to a market with only ~5 reliably-quotable symbols.

---

## Portfolio-level read

The PRD's framing was a *diversified* microstructure portfolio: liquidation seismology (S1), book-microstructure momentum (S2), settlement-mechanics timing (S3), ML-pattern forecasting (S4), and cross-sectional reversion (S5). Iter-3 reveals that this is no longer the right description. Three of the five (S1, S4, S5) did not run at all and are blocked on prerequisites — they are not part of a "portfolio" yet, they are three separate infrastructure projects sitting behind the same shell. Of the two that did run, S2 fired in the wrong direction and S3 fired in roughly the right direction but without exit discipline. So in practice we have *one* viable strategy (S3, conditional on inverted-arm confirmation), *one* candidate for inversion (S2), and *three* dormant concepts.

The strategy most likely to produce a real edge in iter-4 is **S3** — the thesis is intact, the fix is a single bounded-loss rule, and the data signature (worst-3 duration ratio 1.7–3.0× across all five symbols) is unambiguous. The second-most-likely is **S2-inverted**: if the inverted arm confirms a mirror, we recover ~+3 to +4 bps raw on a real signal, which is still below the 11 bps friction wall but opens a maker-only or larger-edge variant as a follow-up. **S4 should be retired in its current "ensemble" form** until a single forecaster proves it can forecast — the PRD's variance-reduction story is dependent on assumptions iter-3 cannot validate, and the infrastructure cost to keep it nominally alive is the largest in the portfolio. **S1 stays alive only as an instrumentation experiment**, not as a tradable strategy. **S5 is parked** until a panel harness exists.

The PRD's "diversified microstructure" frame has been forced into a tighter one: *settlement mechanics is the edge that survives iter-3*, with book-microstructure (S2) as a secondary if the sign-flip lands. That is a re-framing worth naming explicitly before iter-4 begins.

---

### Executive summary

- **S3 is the one survivor with a clear iter-4 path**: thesis intact, missing concept is risk-of-ruin / bounded-loss management, not signal redesign.
- **S2's signal is real but its direction is inverted** (6–8% hit-rate on n=130 BTC+ETH is decisive); pending inverted-arm confirmation, reframe from momentum-follow to fade-the-book.
- **S1, S4, S5 are not yet falsifiable** — each is blocked on a different prerequisite (rho instrumentation, model-loader triage, panel replayer); S4 in particular should be considered for retirement unless a single component forecaster can be shown to work standalone.
