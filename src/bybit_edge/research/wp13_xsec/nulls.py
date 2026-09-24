"""WP-13 -- noise floors for F-XSEC1 (DEC-74 (a)/(b)/(c)/(d)), PURE.

**(a) Analytic permutation floor, per week: ``1/sqrt(K_t-1)``, exact --
no tie correction needed (document the formula).** ``wp7_universe.
null_ic.permutation_null_sd`` permutes a FIXED sequence ``0..K-1`` (no
ties) against the REAL (possibly tied) outcome. For a Pearson correlation
``r`` between a uniformly randomly permuted fixed vector ``a`` (any
values, no ties needed) and an ARBITRARY fixed vector ``b`` (any values,
ties allowed -- e.g. ``close_at_last``'s repeated ``0.0`` outcomes for a
week's delisted symbols), the classic finite-population permutation
identity gives ``E[r] = 0`` and ``Var[r] = 1/(K-1)`` EXACTLY, independent
of the actual values (or tie structure) in EITHER vector -- a standard
result (Kendall & Stuart, *The Advanced Theory of Statistics* vol 2,
permutation distribution of the correlation coefficient). Spearman's rho
is just Pearson correlation of the two RANK vectors, and ranking a
tie-free permutation of ``0..K-1`` changes nothing (it is already its own
rank vector) -- so the identity applies directly to ``spearman_rank_ic``
with ``a`` permuted and ``b`` (with or without ties) fixed. **The "tie
correction" for THIS estimator is therefore that none is needed** -- the
formula ``E_t[1/sqrt(K_t-1)]`` is exact whether or not the outcome carries
ties, which is exactly why ``state/REVIEW_H28_H30_v1.md`` found the
measured ``sd_null`` (from real, occasionally-tied return data) matches
the analytic ``E_t[1/sqrt(K_t-1)]`` to 5 significant figures ("Identitaet
bestaetigt: 0,0411229 vs. 0,0411160"). A general tie-adjustment formula
(for the DIFFERENT case where the PERMUTED side itself carries ties) is
documented in :func:`analytic_permutation_floor`'s docstring for
completeness, but is not the formula this estimator needs.

**(b)/(c) Persistence null (DEC-74 Entscheidung 2(c), verbatim).** Per
symbol, an AR(1) is fit on the window's weekly returns (``phi``, ``sigma``,
forced mean 0 -- see :func:`fit_ar1_per_symbol`); 1000 simulations (seed
53) run the FULL pipeline per variant (the characteristic built from the
simulated returns, then :func:`wp13_xsec.ic.weekly_ic_series` on the
REAL window's ``alive`` mask) to get the null distribution of the
window's mean IC; the PASS threshold is the one-sided 95% quantile in the
REGISTERED direction (:data:`REGISTERED_DIRECTION`, PRD 5.3: A3-M
positive, A3-R negative, A3-V negative); ``rho_k`` (lag 1..4
autocorrelation of the SIMULATED per-week IC series, median over sims)
feeds ``c_rho`` (DEC-74 (b)).

**Vol-variant deviation (see ``characteristics.weekly_only_proxy_
characteristic``'s docstring).** The AR(1) simulation only produces
WEEKLY returns (no intraweek daily path, no designated BTC column) --
``vol_rv``/``vol_max`` use an ``abs(return)`` proxy and ``vol_beta``
regresses against the simulated panel's own cross-sectional mean each
week. This is a genuine simplification of the real (daily-refined)
construction, needed because the null has no daily granularity to
simulate; it is used ONLY to calibrate the null quantile/``c_rho``, never
to report a "vol IC".

**Runtime.** ``persistence_null`` reuses (does not reimplement)
``characteristics.weekly_only_proxy_characteristic`` and
``ic.weekly_ic_series`` unchanged, looping ``n_sims`` times per variant --
correctness/reuse over raw speed (see ``scripts/wp13_xsec.py``'s
``--n-sims`` flag, DEC-74 Entscheidung 3's "1.000 Simulationen ... falls
zu langsam, 500 Simulationen mit Flag und Hinweis").

**DEC-75 Entscheidung 1 (1)/(8), Vorlauf v2 additions (task brief items
1/2/3).**

  (1) ``W_judged`` = ``n_weeks - 1`` (the number of weeks that actually
      enter a t -> t+1 judgement -- the same range
      ``ic.weekly_ic_series``/``_pure_noise_window_mean_ic`` already loop
      over). Every per-window quantity that divides by ``sqrt(W)`` -- the
      floor mean, ``c_rho``'s ``W`` denominator, ``ic_threshold`` -- now
      uses ``W_judged``, not the window's raw week count.
      :func:`analytic_permutation_floor` therefore averages ``K_t`` over
      ``t in [0, n_weeks-2]`` (dropping the final, judgement-free week)
      and reports ``w_judged`` explicitly alongside the legacy
      ``n_weeks``/``n_weeks_valid`` fields (kept for backward
      compatibility with callers that only read ``e_floor``).
  (2) ``c_rho`` bias correction (Review B-2, verbatim: "c_rho < 1 ist
      Schaetzerbias (-1/W je Lag)"). **Chosen correction (documented, task
      brief: "choose one, document"): additive ``+1/W_judged`` per lag** --
      ``rho_k_corrected = rho_k_raw + 1/W_judged`` for each of the 4 lags,
      then ``c_rho_corrected = c_rho_from_lag_autocorr(rho_corrected,
      w=W_judged)``. This is the simplest closed-form correction for the
      standard OLS/Kendall small-sample downward bias of a lag-``k``
      autocorrelation estimate (``E[rho_hat] ~= rho - 1/W`` for a
      mean-zero series of length ``W``, Kendall & Stuart vol 3 Sec 48.1 --
      NOT scaled by lag ``k``, since the bias is dominated by the
      denominator's degrees-of-freedom loss, not by the lag itself). Both
      ``c_rho_raw`` (unchanged DEC-74 (b) value) and ``c_rho_corrected``
      are stored in :func:`persistence_null`'s per-variant output;
      :func:`ic_threshold` takes the value the caller passes for its
      ``c_rho`` argument (the caller -- ``prelaunch.py`` -- always passes
      ``c_rho_corrected``, per DEC-75 (8)).
  (3) ``max(1, c_rho)`` capping (DEC-75 (8): "Deckelung `max(1, c_rho)` als
      registrierte Abweichung von DEC-74 (b)") is now a first-class,
      DEFAULT-ON keyword of :func:`ic_threshold` (``cap_c_rho=True``) --
      the registered deviation from DEC-74 (b), cited DEC-75
      Entscheidung 1 (8). ``ic_threshold(..., cap_c_rho=False)`` returns
      the UNCAPPED value (``ic_min_raw``, may be smaller than the capped
      value when ``c_rho_corrected < 1``) so both can be written to the
      artifact side by side (task brief item 2).

**DEC-76 Entscheidung 1/2 -- roles of the nulls, Vorlauf v3 (additive).**
The Vorlauf v2 finding (DEC-76 "Anlass"): the DRIFTING factor-preserving
null's RAW mean-IC is NOT centered at 0 -- with drift and AR(1)
persistence in the market factor, a heterogeneous beta (0.5..2.0) IS a
genuine cross-sectional predictor of next week's return (pure
market-timing, no idiosyncratic signal anywhere). Using that null's raw
quantile as a PASS threshold would be a false-DROP path (real momentum
buried under a stricter-than-necessary bar); ignoring it without the beta
control is the false-PASS path DEC-75 Entscheidung 1 (3) already guards
against. DEC-76 Entscheidung 1 therefore fixes each null's ROLE:

  (a) The RAW mean IC's threshold stays exactly DEC-75 (1)'s ``SE =
      max(floor, SD(IC_t real))/sqrt(W_judged)`` (``run.se_of_mean_ic``,
      unchanged) -- the REAL series carries its own factor variance, no
      simulated factor SD enters this threshold.
  (b) The BETA CONTROL (market-residualised outcome, DEC-75 (3)) gets a
      SECOND PASS requirement on top of ``|IC_res| >= IC_min``: the
      residualised mean IC must lie BEYOND the drifting null's OWN
      residualised-mean-IC quantile (``quantile_one_sided_residualized``
      below) -- under residualisation the drifting null's mean IS 0 (the
      whole point of removing beta first), so this quantile is a genuine
      noise bound, unlike the raw one.
  (c) The GL-012 selection ceiling uses the DRIFTFREE factor null (``rho_f``
      stays 0.2, ``drift_f=0``) -- with no drift a heterogeneous beta
      carries no directional information, so BOTH its raw and residualised
      mean-of-max are genuine noise ceilings; RAW and RESIDUALIZED are
      reported side by side, but the binding GL-012 kill uses the
      RESIDUALIZED driftfree ceiling (the same beta-controlled comparison
      basis as (b)).
  (d) Block-permutation p-values (DEC-75 (2), ``block_permutation_pvalue``)
      stay unchanged, report-only.
  (e) The simulation's ``sigma_e`` is now the MEDIAN IDIOSYNCRATIC weekly
      vol (:func:`idiosyncratic_vol_from_beta_regression` -- SD of each
      symbol's OLS residual after regressing its weekly return on BTC's
      weekly return over the window, median across symbols), not the
      window's TOTAL per-symbol vol (the DEC-75 v2 value, which double-
      counts the factor's own contribution -- DEC-76 "Anlass", verbatim:
      "sigma_e ist zudem die Gesamt- statt die idiosynkratische Vol"). Both
      are reported (``sigma_e_median_symbol_weekly`` = total,
      ``sigma_e_median_symbol_weekly_idiosyncratic`` = the new value
      actually fed to the simulation, ``sigma_e_used_in_simulation`` makes
      the choice explicit even if a future caller changes the fallback).

**"Simulated BTC column" convention (task brief: "document how the market
column is chosen").** :func:`factor_preserving_null` simulates ONE column
per REAL symbol (``n_symbols = len(symbols)``, same order); the "simulated
BTC column" used for both the idiosyncratic-vol regression and the
per-replicate beta-residualisation is simply ``sim_returns[:,
symbols.index(market_symbol)]`` -- the simulated draw that LANDS at
BTCUSDT's own real position in the symbol list, never a separately
re-derived series. This mirrors :func:`ic.residualize_outcome`'s own
``r_btc = returns[:, symbols.index(market_symbol)]`` convention exactly,
just applied to the simulated panel instead of the real one.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from . import characteristics, ic

__all__ = [
    "Z_PER_WINDOW", "PERSISTENCE_NULL_SEED", "PERSISTENCE_NULL_N_SIMS_DEFAULT",
    "REGISTERED_DIRECTION", "analytic_permutation_floor", "fit_ar1_per_symbol",
    "simulate_ar1_panel", "persistence_null", "c_rho_from_lag_autocorr",
    "ic_threshold", "w_judged_of", "bias_correct_rho_by_lag",
    "FACTOR_NULL_SEED", "FACTOR_NULL_N_REPS_DEFAULT", "BLOCK_SIZE_WEEKS",
    "SELECTION_CEILING_ONE_SIDED_QUANTILE", "simulate_factor_panel",
    "factor_preserving_null", "block_permute_week_index", "block_permutation_null_draws",
    "block_permutation_pvalue", "idiosyncratic_vol_from_beta_regression",
    "DRIFT_F_DRIFTING", "DRIFT_F_DRIFTFREE",
    "window_sigma_f_sigma_e", "CALIBRATION_BETA_TRAIL_WEEKS", "measure_market_factor",
    "factor_share_from_trailing_beta", "beta_dispersion_from_trailing_beta", "pooled_finite_beta",
    "factor_calibration_report", "FACTOR_NULL_CALIBRATIONS", "beta_controlled_factor_null",
    "beta_control_method_study",
]

#: DEC-51/DEC-74 (d): per-window critical value (alpha 0.05 one-sided).
Z_PER_WINDOW = 2.4865

#: DEC-74 (c), verbatim.
PERSISTENCE_NULL_SEED = 53
PERSISTENCE_NULL_N_SIMS_DEFAULT = 1000

#: PRD 5.3, verbatim: "Richtung je Faktor registriert (A3-M positiv, A3-R
#: negativ auf der Formationsrendite, A3-V negativ auf dem Vol-Rang)".
REGISTERED_DIRECTION: dict[str, str] = {
    "mom1": "positive", "mom2": "positive", "mom4": "positive",
    "rev_gap": "negative",
    "vol_rv": "negative", "vol_max": "negative", "vol_beta": "negative",
}


# ----------------------------------------------------------------------------
# (a) analytic permutation floor
# ----------------------------------------------------------------------------

def w_judged_of(n_weeks: int) -> int:
    """DEC-75 Entscheidung 1 (1): ``W_judged = n_weeks - 1`` -- the number
    of weeks that carry a ``t -> t+1`` judgement (the final week of any
    window has no ``t+1`` outcome inside the window and is never judged).
    ``max(0, n_weeks - 1)`` guards a degenerate 0/1-week window."""
    return max(0, n_weeks - 1)


def analytic_permutation_floor(alive_window: np.ndarray, weeks: list[str]) -> dict[str, Any]:
    """``E_t[1/sqrt(K_t-1)]`` over the window's JUDGED weeks (DEC-75
    Entscheidung 1 (1): ``t in [0, n_weeks-2]``, i.e. ``W_judged =
    n_weeks-1`` weeks -- the final week's ``K_t`` never contributes,
    because it has no ``t+1`` outcome to be judged against, exactly the
    range ``ic.weekly_ic_series``/``_pure_noise_window_mean_ic`` already
    loop over). ``K_t = alive_window[t].sum()`` (matches ``state/runs/
    .../decile_degeneration_weekly.csv``'s ``n_symbols`` column, the
    source DEC-74 cites for its confirmed K figures). A week with ``K_t <
    2`` contributes no value (undefined floor). Returns the full
    judged-week series (DEC-53 artifact material) plus the window mean and
    ``w_judged``.

    **General tie-adjustment formula, for completeness (not what this
    estimator needs -- see module docstring):** if the PERMUTED side
    itself carried ``g`` tie groups of size ``t_1..t_g``, the exact
    variance would be ``Var[r] = 1/(K-1) * (K^3-K-sum(t_i^3-t_i)) /
    (K^3-K)`` -- a strictly smaller number, i.e. ties in the permuted side
    would make the floor a TIGHTER (smaller) bound, never wider. Since
    this module's permuted side is always the tie-free sequence
    ``0..K-1``, the correction factor is exactly 1 and drops out.
    """
    n_weeks = len(weeks)
    w_judged = w_judged_of(n_weeks)
    k_t_full = alive_window.sum(axis=1).astype(np.int64)
    k_t = k_t_full[:w_judged]                      # DEC-75 (1): drop the final, un-judged week
    judged_weeks = weeks[:w_judged]
    floor_per_week = np.full(w_judged, np.nan, dtype=np.float64)
    valid = k_t >= 2
    floor_per_week[valid] = 1.0 / np.sqrt((k_t[valid] - 1).astype(np.float64))
    finite = floor_per_week[valid]
    e_floor = float(finite.mean()) if finite.size else float("nan")
    return {
        "weeks": judged_weeks, "k_series": k_t.tolist(),
        "floor_per_week": [None if math.isnan(v) else float(v) for v in floor_per_week],
        "e_floor": e_floor, "w_judged": w_judged,
        "n_weeks": n_weeks, "n_weeks_valid": int(valid.sum()),
    }


# ----------------------------------------------------------------------------
# (b)/(c) persistence null
# ----------------------------------------------------------------------------

def fit_ar1_per_symbol(returns: np.ndarray, alive: np.ndarray, *,
                        phi_clip: float = 0.98) -> dict[str, Any]:
    """Per-symbol AR(1) (``phi``, ``sigma``, forced mean 0 -- DEC-74 (c)):
    each symbol's OWN alive-week returns are demeaned first (mean 0 by
    construction), then ``phi`` is the OLS slope of ``d[t]`` on ``d[t-1]``
    restricted to CONSECUTIVE alive weeks (``alive[t-1] & alive[t]``,
    exactly the pair discipline every other estimator in this package
    uses), ``sigma`` the residual SD. ``phi`` is clipped to
    ``[-phi_clip, +phi_clip]`` (documented stability guard -- an OLS fit
    on a short, noisy window can exceed 1 and make the simulated process
    explosive; DEC-74 does not fix a clip value, this is an
    implementation necessity, not a registered constant). A symbol with
    fewer than 2 consecutive alive pairs gets ``phi=0``; fewer than 2
    alive observations at all gets ``sigma=0`` too (a flat, zero-variance
    simulated series for that symbol -- reported via ``n_pairs``/
    ``n_obs`` so a caller can see how many symbols this affected, never
    silently).
    """
    n_weeks, n_symbols = returns.shape
    phi = np.zeros(n_symbols, dtype=np.float64)
    sigma = np.zeros(n_symbols, dtype=np.float64)
    n_pairs = np.zeros(n_symbols, dtype=np.int64)
    n_obs = np.zeros(n_symbols, dtype=np.int64)
    for j in range(n_symbols):
        idx = alive[:, j]
        obs = returns[idx, j]
        n_obs[j] = obs.size
        if obs.size < 2:
            continue
        mu = float(obs.mean())
        d = returns[:, j] - mu
        pair_mask = idx[:-1] & idx[1:]
        x, y = d[:-1][pair_mask], d[1:][pair_mask]
        n_pairs[j] = x.size
        if x.size >= 2 and float(np.dot(x, x)) > 0.0:
            phi_j = float(np.dot(x, y) / np.dot(x, x))
            phi[j] = float(np.clip(phi_j, -phi_clip, phi_clip))
        resid = y - phi[j] * x if x.size else np.array([], dtype=np.float64)
        if resid.size > 1:
            sigma[j] = float(resid.std(ddof=1))
        elif obs.size > 1:
            sigma[j] = float(d[idx].std(ddof=1))
    return {"phi": phi, "sigma": sigma, "n_pairs": n_pairs.tolist(), "n_obs": n_obs.tolist(),
            "phi_clip": phi_clip}


def simulate_ar1_panel(phi: np.ndarray, sigma: np.ndarray, n_weeks: int, *,
                        rng: np.random.Generator) -> np.ndarray:
    """One ``[n_weeks, n_symbols]`` AR(1) panel: week 0 drawn from the
    process's stationary SD (``sigma/sqrt(1-phi^2)``, or ``sigma`` itself
    if ``|phi|`` is at/above the near-unit-root guard), every later week
    ``phi*prev + sigma*N(0,1)``. ``rng`` is drawn from SEQUENTIALLY
    (caller-owned, same discipline as ``null_ic.permutation_null_sd`` --
    determinism (T2) needs one RNG advanced in a fixed order across every
    simulation draw)."""
    n_symbols = phi.shape[0]
    stationary_sd = np.where(np.abs(phi) < 0.999, sigma / np.sqrt(np.maximum(1.0 - phi ** 2, 1e-6)), sigma)
    sim = np.zeros((n_weeks, n_symbols), dtype=np.float64)
    sim[0] = rng.standard_normal(n_symbols) * stationary_sd
    for t in range(1, n_weeks):
        sim[t] = phi * sim[t - 1] + sigma * rng.standard_normal(n_symbols)
    return sim


def _lag_autocorr(series: np.ndarray, lag: int) -> float | None:
    """Pearson correlation of ``series`` against its ``lag``-shift, using
    only positions where BOTH are finite; ``None`` if fewer than 5 such
    pairs (an under-powered lag estimate is worse than an honest gap)."""
    if series.size <= lag:
        return None
    a, b = series[:-lag], series[lag:]
    valid = ~np.isnan(a) & ~np.isnan(b)
    if int(valid.sum()) < 5:
        return None
    a, b = a[valid], b[valid]
    if a.std() == 0.0 or b.std() == 0.0:
        return None
    r = float(np.corrcoef(a, b)[0, 1])
    return None if math.isnan(r) else r


def c_rho_from_lag_autocorr(rho_by_lag: dict[int, float], *, w: int) -> float:
    """DEC-74 (b), verbatim: ``c_rho = sqrt(1 + 2*sum_{k=1..4}
    (1-k/W)*rho_k)``. A missing lag (``None``, too few valid sim pairs)
    contributes 0 -- documented, conservative (never inflates ``c_rho``
    beyond what the available lags support). ``w`` is ``W_judged`` (DEC-75
    Entscheidung 1 (1)), not the raw week count."""
    total = 0.0
    for k in range(1, 5):
        rho_k = rho_by_lag.get(k)
        if rho_k is None:
            continue
        total += (1.0 - k / w) * rho_k
    inside = 1.0 + 2.0 * total
    return math.sqrt(inside) if inside > 0.0 else 0.0


def bias_correct_rho_by_lag(rho_by_lag: dict[int, float], *, w_judged: int) -> dict[int, float]:
    """DEC-75 Entscheidung 1 (2)/Review B-2: additive small-sample bias
    correction, ``rho_k_corrected = rho_k_raw + 1/W_judged`` for every lag
    present in ``rho_by_lag`` (see module docstring for the "which
    correction, and why" writeup). Missing lags stay missing (never
    invented)."""
    if w_judged <= 0:
        return dict(rho_by_lag)
    return {k: v + 1.0 / w_judged for k, v in rho_by_lag.items()}


def persistence_null(
    returns: np.ndarray, alive: np.ndarray, weeks: list[str], *,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    convention: ic.Convention = "close_at_last", n_sims: int = PERSISTENCE_NULL_N_SIMS_DEFAULT,
    seed: int = PERSISTENCE_NULL_SEED,
) -> dict[str, Any]:
    """DEC-74 (b)/(c): per variant, the null distribution of the window
    mean IC under the AR(1) persistence null, its registered-direction
    95% quantile, and ``c_rho`` from the simulated IC series' lag1..4
    autocorrelation (median over sims). **Reuses**
    ``characteristics.weekly_only_proxy_characteristic`` and
    ``ic.weekly_ic_series`` UNCHANGED for every simulated draw -- this
    function only owns the AR(1) fit/simulate loop and the
    quantile/autocorrelation aggregation, never a parallel IC
    implementation.
    """
    ar1 = fit_ar1_per_symbol(returns, alive)
    phi, sigma = np.array(ar1["phi"]), np.array(ar1["sigma"])
    n_weeks = returns.shape[0]
    w_judged = w_judged_of(len(weeks))              # DEC-75 (1): c_rho's W is W_judged, not len(weeks)
    rng = np.random.default_rng(seed)

    per_variant: dict[str, Any] = {}
    for variant in variants:
        mean_ic_draws = np.full(n_sims, np.nan, dtype=np.float64)
        ic_series_draws: list[np.ndarray] = []
        for sim_i in range(n_sims):
            sim_returns = simulate_ar1_panel(phi, sigma, n_weeks, rng=rng)
            char = characteristics.weekly_only_proxy_characteristic(variant, sim_returns)
            res = ic.weekly_ic_series(char, sim_returns, alive, convention=convention)
            mean_ic_draws[sim_i] = res["mean_ic"]
            ic_series_draws.append(np.array([wk["ic"] for wk in res["weekly"]], dtype=np.float64))

        finite = mean_ic_draws[~np.isnan(mean_ic_draws)]
        direction = REGISTERED_DIRECTION[variant]
        if finite.size == 0:
            quantile95 = float("nan")
        elif direction == "positive":
            quantile95 = float(np.quantile(finite, 0.95))
        else:
            quantile95 = float(np.quantile(finite, 0.05))

        rho_by_lag: dict[int, float] = {}
        for lag in range(1, 5):
            vals = [r for r in (_lag_autocorr(series, lag) for series in ic_series_draws) if r is not None]
            if vals:
                rho_by_lag[lag] = float(np.median(vals))
        c_rho_raw = c_rho_from_lag_autocorr(rho_by_lag, w=w_judged)
        rho_by_lag_corrected = bias_correct_rho_by_lag(rho_by_lag, w_judged=w_judged)
        c_rho_corrected = c_rho_from_lag_autocorr(rho_by_lag_corrected, w=w_judged)

        per_variant[variant] = {
            "direction": direction, "n_sims": n_sims, "seed": seed, "convention": convention,
            "quantile95_registered_direction": quantile95,
            "mean_ic_draws_mean": float(finite.mean()) if finite.size else float("nan"),
            "mean_ic_draws_sd": float(finite.std(ddof=1)) if finite.size > 1 else float("nan"),
            "n_sims_finite": int(finite.size),
            "rho_by_lag": {str(k): v for k, v in rho_by_lag.items()},
            "rho_by_lag_corrected": {str(k): v for k, v in rho_by_lag_corrected.items()},
            # DEC-75 (2)/(8): c_rho is the CORRECTED value (what ic_threshold's cap_c_rho
            # is meant to cap); c_rho_raw is the pre-correction DEC-74 (b) value, kept for
            # reporting. Both share the same W_judged denominator.
            "c_rho_raw": c_rho_raw, "c_rho_corrected": c_rho_corrected, "c_rho": c_rho_corrected,
        }
    return {"variants": per_variant, "ar1": {"phi": phi.tolist(), "sigma": sigma.tolist(),
            "n_pairs": ar1["n_pairs"], "n_obs": ar1["n_obs"], "phi_clip": ar1["phi_clip"]},
            "seed": seed, "n_sims": n_sims, "w": w_judged, "w_judged": w_judged}


# ----------------------------------------------------------------------------
# (a)+(d) threshold arithmetic
# ----------------------------------------------------------------------------

def ic_threshold(e_floor: float, c_rho: float, w: int, *, z: float = Z_PER_WINDOW,
                  cap_c_rho: bool = True) -> float:
    """DEC-74 (a), verbatim: ``IC_min(W) = 2.4865 * E_t[1/sqrt(K_t-1)] *
    c_rho / sqrt(W)``. ``w`` MUST be ``W_judged`` (DEC-75 Entscheidung 1
    (1)), not the window's raw week count -- callers get this from
    :func:`analytic_permutation_floor`'s ``w_judged`` field.

    **DEC-75 Entscheidung 1 (8), registered deviation from DEC-74 (b):**
    ``cap_c_rho=True`` (the default) applies ``max(1, c_rho)`` before
    multiplying -- ``c_rho < 1`` is estimator bias (Review B-2), never a
    genuine noise-REDUCING negative autocorrelation the threshold should
    get to exploit. ``cap_c_rho=False`` returns the uncapped value
    (``ic_min_raw``, task brief item 2: "write it in the artifact next to
    the raw value") -- ``prelaunch.py`` calls this twice per variant, once
    with each setting, and reports both."""
    factor = max(1.0, c_rho) if cap_c_rho else c_rho
    return z * e_floor * factor / math.sqrt(w)


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (2)/task brief item 3: factor-preserving null
# (prelaunch: SIMULATED factor panel, signal-free by construction) +
# item 3's block-permutation p-value (run mode only, not called in
# --prelaunch).
# ----------------------------------------------------------------------------

#: Task brief item 3: >= 1000 replicates.
FACTOR_NULL_SEED = 53
FACTOR_NULL_N_REPS_DEFAULT = 1000
#: DEC-75 Entscheidung 1 (2)/(3): block permutation over weeks, block 4.
BLOCK_SIZE_WEEKS = 4
#: DEC-75 Entscheidung 1 (1): registered one-sided level 1 - 0.0064 = 0.9936.
SELECTION_CEILING_ONE_SIDED_QUANTILE = 1.0 - 0.0064

#: DEC-76 Entscheidung 2 (Vorlauf v3): the two factor-null configurations,
#: rho_f=0.2 in BOTH (AR(1) persistence kept), drift_f differs.
DRIFT_F_DRIFTING = 0.002
DRIFT_F_DRIFTFREE = 0.0


def simulate_factor_panel(
    n_weeks: int, n_symbols: int, *, sigma_f: float, sigma_e: float,
    rho_f: float = 0.2, drift_f: float = 0.002, rng: np.random.Generator,
    beta_pool: np.ndarray | None = None,
) -> dict[str, Any]:
    """Task brief item 3, verbatim construction: ``returns = beta_i * f_t +
    e_it`` -- ``beta_i ~ U(0.5, 2.0)`` drawn ONCE (fixed per symbol for
    this draw of ``rng``, i.e. identical across every week of this ONE
    panel -- the caller redraws ``beta`` too if it wants a fresh draw per
    replicate; :func:`factor_preserving_null` deliberately draws it ONCE
    for the whole window, not once per replicate, per the task brief:
    "beta_i ~ U(0.5, 2.0) (fixed per symbol, seed)").

    **DEC-77 Entscheidung 1 (a), additive:** ``beta_pool`` (default
    ``None``, unchanged ``U(0.5, 2.0)`` draw) -- when given a non-empty
    1-D array of REAL, measured PIT-beta values (:func:`pooled_finite_beta`
    resamples them WITH replacement, one draw per simulated symbol
    (``rng.choice(beta_pool, size=n_symbols, replace=True)``) instead of
    the uniform draw -- the "measured"/"zero" factor-null calibrations'
    "betas drawn from the measured PIT-beta distribution" (DEC-77 task
    brief item 1). ``f_t`` an AR(1) with
    drift (``f[0]`` starts at the stationary mean ``drift_f/(1-rho_f)``,
    ``f[t] = drift_f + rho_f*f[t-1] + sigma_f*eps_t`` for ``t >= 1`` --
    standard AR(1)-with-intercept, unconditional mean ``drift_f/(1-rho_f)``
    the innovation SD is exactly ``sigma_f`` (matched to the window's BTC
    weekly vol by the caller), ``e_it ~ N(0, sigma_e)`` iid per
    symbol-week (``sigma_e`` matched to the window's MEDIAN symbol vol by
    the caller). Signal-free by construction: no term here carries any
    cross-sectional RANK information beyond the (heterogeneous, but
    time-INVARIANT) beta loading -- exactly the review's B-1 adversarial
    case, deliberately reproduced as the null itself.

    Returns ``{"returns", "beta", "f"}`` -- ``returns`` is ``[n_weeks,
    n_symbols]``, ``beta`` is ``[n_symbols]``, ``f`` is ``[n_weeks]``.
    """
    if beta_pool is not None and beta_pool.size > 0:
        beta = rng.choice(beta_pool, size=n_symbols, replace=True)
    else:
        beta = rng.uniform(0.5, 2.0, size=n_symbols)
    f = np.empty(n_weeks, dtype=np.float64)
    stationary_mean = drift_f / (1.0 - rho_f) if abs(1.0 - rho_f) > 1e-9 else 0.0
    f[0] = stationary_mean + sigma_f * rng.standard_normal()
    for t in range(1, n_weeks):
        f[t] = drift_f + rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    e_it = sigma_e * rng.standard_normal(size=(n_weeks, n_symbols))
    returns = beta[None, :] * f[:, None] + e_it
    return {"returns": returns, "beta": beta, "f": f}


def idiosyncratic_vol_from_beta_regression(
    window_returns: np.ndarray, symbols: list[str], *, market_symbol: str = "BTCUSDT",
) -> dict[str, Any]:
    """DEC-76 Entscheidung 1 (e): the simulation's ``sigma_e`` is the MEDIAN
    IDIOSYNCRATIC weekly vol, not the total one. For every symbol OTHER
    THAN ``market_symbol``, ONE static OLS is fit over the WHOLE window
    (``symbol_return[t] = alpha + beta*btc_return[t] + resid[t]``, both
    demeaned so ``alpha`` drops out, exactly ``fit_ar1_per_symbol``'s
    "demean, then OLS slope" discipline applied cross-sectionally instead
    of across lags) and the residual SD (``ddof=1``) is recorded; the
    reported ``sigma_e_idiosyncratic`` is the MEDIAN of those per-symbol
    residual SDs. Purely descriptive (a dispersion statistic of the REAL
    window, same discipline as ``prelaunch.h30_feasibility``'s
    ``sigma_xs`` -- never an IC, never touches an outcome ranking).

    ``market_symbol`` itself is EXCLUDED from the median: regressing BTC's
    own return on itself is a perfect fit by construction (beta=1,
    residual identically 0), which would mechanically pull the median
    down -- a documented, deliberate exclusion, not an oversight.

    Returns ``{"sigma_e_idiosyncratic", "per_symbol_residual_sd",
    "market_symbol", "n_symbols_used"}``; ``sigma_e_idiosyncratic`` is
    ``NaN`` if ``market_symbol`` is absent from ``symbols`` or fewer than
    one other symbol has >= 3 valid weeks paired with the market -- the
    caller (:func:`factor_preserving_null`) falls back to the TOTAL vol in
    that case, documented at the call site.
    """
    if market_symbol not in symbols:
        return {"sigma_e_idiosyncratic": float("nan"), "per_symbol_residual_sd": {},
                "market_symbol": market_symbol, "n_symbols_used": 0}
    m = symbols.index(market_symbol)
    mkt = window_returns[:, m]
    valid_m = ~np.isnan(mkt)
    residual_sds: dict[str, float] = {}
    for j, sym in enumerate(symbols):
        if j == m:
            continue
        y = window_returns[:, j]
        valid = valid_m & ~np.isnan(y)
        if int(valid.sum()) < 3:
            continue
        x, yy = mkt[valid], y[valid]
        var_x = float(np.var(x, ddof=1))
        if var_x <= 0.0:
            continue
        x_c, y_c = x - x.mean(), yy - yy.mean()
        beta_j = float(np.dot(x_c, y_c) / np.dot(x_c, x_c))
        resid = y_c - beta_j * x_c
        if resid.size > 1:
            residual_sds[sym] = float(resid.std(ddof=1))
    finite = np.array(list(residual_sds.values()), dtype=np.float64)
    sigma_e_idio = float(np.median(finite)) if finite.size else float("nan")
    return {"sigma_e_idiosyncratic": sigma_e_idio, "per_symbol_residual_sd": residual_sds,
            "market_symbol": market_symbol, "n_symbols_used": int(finite.size)}


def _mean_of_max(draws: dict[str, list[float]], variants: tuple[str, ...], n_reps: int) -> float:
    """Shared helper (:func:`factor_preserving_null`/
    :func:`beta_controlled_factor_null`): mean, over replicates, of that
    replicate's MAX window-mean-IC across ``variants`` -- a direct
    Monte-Carlo selection-ceiling estimate. Pulled out to module scope so
    both callers share ONE implementation (never two parallel copies)."""
    max_per_rep = np.full(n_reps, np.nan, dtype=np.float64)
    for rep_i in range(n_reps):
        vals = [draws[v][rep_i] for v in variants if not math.isnan(draws[v][rep_i])]
        if vals:
            max_per_rep[rep_i] = max(vals)
    finite_max = max_per_rep[~np.isnan(max_per_rep)]
    return float(finite_max.mean()) if finite_max.size else float("nan")


def window_sigma_f_sigma_e(
    window_returns: np.ndarray, symbols: list[str], *, market_symbol: str = "BTCUSDT",
) -> dict[str, Any]:
    """Shared descriptive-scalar helper (:func:`factor_preserving_null`/
    :func:`beta_controlled_factor_null`): ``sigma_f`` (the window's REAL
    market-symbol weekly-return SD, or -- if ``market_symbol`` is absent --
    the median per-symbol SD as a fallback) and ``sigma_e_used`` (DEC-76
    Entscheidung 1 (e): the median IDIOSYNCRATIC weekly vol via
    :func:`idiosyncratic_vol_from_beta_regression`, falling back to the
    TOTAL median per-symbol vol if the idiosyncratic estimate is not
    finite). Pulled out to module scope so both simulation entry points
    compute these REAL-data descriptive scalars IDENTICALLY, never two
    subtly different re-derivations."""
    n_weeks, n_symbols = window_returns.shape
    if market_symbol in symbols:
        btc_col = window_returns[:, symbols.index(market_symbol)]
        sigma_f = float(np.nanstd(btc_col[~np.isnan(btc_col)], ddof=1)) if np.isfinite(btc_col).sum() > 1 else 0.05
    else:
        per_symbol_sd = np.nanstd(window_returns, axis=0, ddof=1)
        sigma_f = float(np.nanmedian(per_symbol_sd[np.isfinite(per_symbol_sd)])) if np.isfinite(per_symbol_sd).any() else 0.05
    per_symbol_sd = np.array([
        np.nanstd(window_returns[:, j][~np.isnan(window_returns[:, j])], ddof=1)
        if int((~np.isnan(window_returns[:, j])).sum()) > 1 else np.nan
        for j in range(n_symbols)
    ])
    finite_sd = per_symbol_sd[~np.isnan(per_symbol_sd)]
    sigma_e_total = float(np.median(finite_sd)) if finite_sd.size else 0.03
    idio_report = idiosyncratic_vol_from_beta_regression(window_returns, symbols, market_symbol=market_symbol)
    sigma_e_idio = idio_report["sigma_e_idiosyncratic"]
    sigma_e_used = sigma_e_idio if math.isfinite(sigma_e_idio) else sigma_e_total
    return {"sigma_f": sigma_f, "sigma_e_total": sigma_e_total, "sigma_e_idiosyncratic": sigma_e_idio,
            "sigma_e_used": sigma_e_used}


def factor_preserving_null(
    window_returns: np.ndarray, window_alive: np.ndarray, symbols: list[str], *,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    convention: ic.Convention = "close_at_last",
    n_reps: int = FACTOR_NULL_N_REPS_DEFAULT, seed: int = FACTOR_NULL_SEED,
    quantile: float = SELECTION_CEILING_ONE_SIDED_QUANTILE,
    market_symbol: str = "BTCUSDT", rho_f: float = 0.2, drift_f: float = DRIFT_F_DRIFTING,
    beta_trail_win: int = characteristics.VOL_BETA_TRAIL_WEEKS,
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (2) / DEC-76 Entscheidung 1/2 / task brief item
    3: the factor-preserving null, sized to the window (``K`` from
    ``window_alive``, ``W`` from ``window_returns``). Only ever reads
    ``window_returns`` for descriptive volatility scalars (``sigma_f`` =
    the window's BTC weekly return SD, ``sigma_e`` = DEC-76 Entscheidung 1
    (e)'s idiosyncratic vol, :func:`idiosyncratic_vol_from_beta_regression`
    -- falls back to the OLD total per-symbol-vol median, reported as
    ``sigma_e_median_symbol_weekly``, if the idiosyncratic value is not
    finite, e.g. ``market_symbol`` absent) -- the SAME "real returns feed a
    descriptive dispersion statistic, never an IC" discipline
    ``prelaunch.h30_feasibility`` already uses for ``sigma_xs``; every
    simulated IC in this function is SIMULATED-characteristic-vs-SIMULATED-
    outcome, per THE SEAL.

    ONE call = ONE configuration (``rho_f``/``drift_f`` pair) -- DEC-76
    Entscheidung 2's two Vorlauf v3 configurations (``drift_f=0.002``
    "drifting", the default, and ``drift_f=0.0`` "driftfree") are two
    SEPARATE calls (``prelaunch.factor_preserving_report`` makes both).

    For ``n_reps`` replicates (``beta`` redrawn once per replicate, ``f``/
    ``e_it`` redrawn every replicate -- see :func:`simulate_factor_panel`),
    runs the FULL per-variant pipeline TWICE per replicate:
      - RAW: ``characteristics.weekly_only_proxy_characteristic`` ->
        ``ic.weekly_ic_series(char, sim_returns, window_alive, ...)`` --
        UNCHANGED from DEC-75, all field names below unchanged (``factor_sd``,
        ``quantile_one_sided``, ``selection_ceiling_mean_of_max``, etc.).
      - RESIDUALIZED (DEC-76 (b)/(c), additive): the simulated panel's OWN
        trailing-``beta_trail_win``-week PIT beta to the "simulated BTC
        column" (see module docstring for that convention) via
        ``characteristics.beta_characteristic``, then
        ``ic.residualize_outcome`` (both reused unchanged) before the SAME
        ``ic.weekly_ic_series`` call -- every RAW field gets an
        ``..._residualized`` sibling (``factor_sd_residualized``,
        ``quantile_one_sided_residualized``,
        ``selection_ceiling_mean_of_max_residualized``, etc.). ``None``
        (never computed) if ``market_symbol`` is absent from ``symbols``.

    Per variant:
      (a) ``factor_sd`` / ``factor_sd_residualized`` -- SD of the per-week
          IC, pooled over ALL weeks of ALL replicates.
      (c) ``quantile_one_sided`` / ``quantile_one_sided_residualized`` --
          the registered-direction one-sided ``quantile`` (default 0.9936)
          of the window-mean-IC draws.
    Once (not per variant):
      (b) ``selection_ceiling_mean_of_max`` / ``..._residualized`` -- mean,
          over replicates, of that replicate's MAX window-mean-IC across
          the 7 variants.
    """
    n_weeks, n_symbols = window_returns.shape
    sigmas = window_sigma_f_sigma_e(window_returns, symbols, market_symbol=market_symbol)
    sigma_f, sigma_e_total, sigma_e_idio, sigma_e_used = (
        sigmas["sigma_f"], sigmas["sigma_e_total"], sigmas["sigma_e_idiosyncratic"], sigmas["sigma_e_used"])

    has_market = market_symbol in symbols
    market_idx = symbols.index(market_symbol) if has_market else None

    rng = np.random.default_rng(seed)
    per_week_ic_pool: dict[str, list[float]] = {v: [] for v in variants}
    mean_ic_draws: dict[str, list[float]] = {v: [] for v in variants}
    per_week_ic_pool_res: dict[str, list[float]] = {v: [] for v in variants}
    mean_ic_draws_res: dict[str, list[float]] = {v: [] for v in variants}

    for _rep in range(n_reps):
        sim = simulate_factor_panel(n_weeks, n_symbols, sigma_f=sigma_f, sigma_e=sigma_e_used,
                                     rho_f=rho_f, drift_f=drift_f, rng=rng)
        sim_returns = sim["returns"]
        resid_returns = None
        if has_market:
            # DEC-76 (b)/(c): the simulated panel's OWN trailing PIT beta to the
            # "simulated BTC column" (module docstring's convention) -- the SAME
            # beta_characteristic/residualize_outcome pair run.py uses on real data.
            beta_sim = characteristics.beta_characteristic(
                sim_returns, symbols, market_symbol=market_symbol, trail_win=beta_trail_win)
            r_btc_sim = sim_returns[:, market_idx]
            resid_returns = ic.residualize_outcome(sim_returns, beta_sim, r_btc_sim)
        for variant in variants:
            char = characteristics.weekly_only_proxy_characteristic(variant, sim_returns)
            res = ic.weekly_ic_series(char, sim_returns, window_alive, convention=convention)
            mean_ic_draws[variant].append(res["mean_ic"])
            per_week_ic_pool[variant].extend(w["ic"] for w in res["weekly"] if not math.isnan(w["ic"]))
            if resid_returns is not None:
                res_r = ic.weekly_ic_series(char, resid_returns, window_alive, convention=convention)
                mean_ic_draws_res[variant].append(res_r["mean_ic"])
                per_week_ic_pool_res[variant].extend(w["ic"] for w in res_r["weekly"] if not math.isnan(w["ic"]))
            else:
                mean_ic_draws_res[variant].append(float("nan"))

    selection_ceiling_mean_of_max = _mean_of_max(mean_ic_draws, variants, n_reps)
    selection_ceiling_mean_of_max_residualized = (
        _mean_of_max(mean_ic_draws_res, variants, n_reps) if has_market else None)

    def _variant_stats(pool: list[float], draws_list: list[float], direction: str) -> dict[str, Any]:
        pool_arr = np.array(pool, dtype=np.float64)
        factor_sd = float(pool_arr.std(ddof=1)) if pool_arr.size > 1 else float("nan")
        draws = np.array([d for d in draws_list if not math.isnan(d)], dtype=np.float64)
        if draws.size == 0:
            q = float("nan")
        elif direction == "positive":
            q = float(np.quantile(draws, quantile))
        else:
            q = float(np.quantile(draws, 1.0 - quantile))
        return {"factor_sd": factor_sd, "n_ic_pooled": int(pool_arr.size),
                "quantile_one_sided": q, "quantile_level": quantile,
                "mean_ic_draws_mean": float(draws.mean()) if draws.size else float("nan"),
                "mean_ic_draws_sd": float(draws.std(ddof=1)) if draws.size > 1 else float("nan"),
                "n_reps_finite": int(draws.size)}

    per_variant: dict[str, Any] = {}
    for variant in variants:
        direction = REGISTERED_DIRECTION[variant]
        raw_stats = _variant_stats(per_week_ic_pool[variant], mean_ic_draws[variant], direction)
        entry = {"direction": direction, **raw_stats}
        if has_market:
            res_stats = _variant_stats(per_week_ic_pool_res[variant], mean_ic_draws_res[variant], direction)
        else:
            # No market column at all -- nothing to residualise against. ``None`` (not NaN) is
            # deliberate: a NaN would make two otherwise-identical reports compare unequal
            # (float('nan') != float('nan')), breaking T2 determinism-style equality checks for
            # no real reason; ``None`` is also the honest "never computed" sentinel (docstring).
            res_stats = {"factor_sd": None, "n_ic_pooled": None, "quantile_one_sided": None,
                         "quantile_level": quantile, "mean_ic_draws_mean": None,
                         "mean_ic_draws_sd": None, "n_reps_finite": None}
        entry.update({f"{k}_residualized": v for k, v in res_stats.items()})
        per_variant[variant] = entry

    return {
        "variants": per_variant, "n_reps": n_reps, "seed": seed, "convention": convention,
        "sigma_f_btc_weekly": sigma_f,
        "sigma_e_median_symbol_weekly": sigma_e_total,                       # DEC-75 v2 value, kept (total vol)
        "sigma_e_median_symbol_weekly_idiosyncratic": sigma_e_idio,          # DEC-76 (e), new
        "sigma_e_used_in_simulation": sigma_e_used,                          # documents which one was fed in
        "rho_f": rho_f, "drift_f": drift_f, "market_symbol": market_symbol,
        "selection_ceiling_mean_of_max": selection_ceiling_mean_of_max,
        "selection_ceiling_mean_of_max_residualized": selection_ceiling_mean_of_max_residualized,
        "n_weeks": n_weeks, "n_symbols": n_symbols,
        "market_column_convention": (
            "Simulierte BTC-Spalte = sim_returns[:, symbols.index(market_symbol)] -- dieselbe "
            "Position wie das echte BTCUSDT in der Symbolliste, nie eine separat hergeleitete Serie "
            "(siehe nulls.py Modul-Docstring)."),
        "label": ("faktorerhaltende Null (DEC-75 (2)/DEC-76 (1)/(2)): returns = beta_i*f_t + e_it, "
                  f"signalfrei; rho_f={rho_f}, drift_f={drift_f} "
                  f"({'drifting' if drift_f != 0.0 else 'driftfree'})."),
    }


# ----------------------------------------------------------------------------
# DEC-77 Entscheidung 1 -- Vorlauf v4: calibrate the factor null from
# descriptive real quantities (THE SEAL: single-series + returns-vs-beta
# relations only, NEVER a characteristic-vs-outcome relation), then run the
# beta-control METHOD study (ic.BETA_CONTROL_METHODS) inside the simulation
# for three rho_f/beta-draw calibrations.
# ----------------------------------------------------------------------------

#: DEC-77 Entscheidung 1 (a): the trailing PIT-beta window the factor-share/
#: beta-dispersion CALIBRATION measurement uses -- deliberately DIFFERENT
#: from ``characteristics.VOL_BETA_TRAIL_WEEKS`` (8, the A3-V characteristic's
#: own window): 26 weeks gives a materially less noisy beta estimate for a
#: purely DESCRIPTIVE dispersion/R^2 statistic, never fed to a judged IC.
CALIBRATION_BETA_TRAIL_WEEKS = 26


def measure_market_factor(window_returns: np.ndarray, symbols: list[str], *,
                           market_symbol: str = "BTCUSDT") -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (a)(a): ``rho_f_measured`` (lag-1 autocorrelation
    of ``market_symbol``'s OWN weekly log returns within the window,
    :func:`_lag_autocorr` reused unchanged) and ``sigma_f`` (its SD) --
    THE SEAL's explicitly allowed "single series" category: no
    characteristic, no outcome pairing, just one real column's own
    descriptive statistics. ``NaN``/``None`` (never a fabricated 0) if
    ``market_symbol`` is absent or the window is too short for a lag-1
    estimate (:func:`_lag_autocorr`'s own >= 5-pairs floor)."""
    if market_symbol not in symbols:
        return {"rho_f_measured": float("nan"), "sigma_f": float("nan"), "n_weeks_used": 0,
                "market_symbol": market_symbol}
    btc = window_returns[:, symbols.index(market_symbol)]
    finite = btc[~np.isnan(btc)]
    sigma_f = float(finite.std(ddof=1)) if finite.size > 1 else float("nan")
    rho1 = _lag_autocorr(btc, 1)
    return {"rho_f_measured": rho1 if rho1 is not None else float("nan"), "sigma_f": sigma_f,
            "n_weeks_used": int(finite.size), "market_symbol": market_symbol}


def trailing_pit_beta_excluding_current_week(
    returns: np.ndarray, symbols: list[str], *, market_symbol: str = "BTCUSDT",
    trail_win: int = CALIBRATION_BETA_TRAIL_WEEKS,
) -> np.ndarray:
    """DEC-77 Entscheidung 1 (a)(b), "beta estimated over the PREVIOUS
    ``trail_win`` weeks": :func:`characteristics.beta_characteristic`'s own
    trailing window ENDS AT (and includes) week ``t`` -- fine for a PIT
    signal meant to predict week ``t+1``, but circular for measuring
    ``factor_share[t]`` = R^2 of week ``t``'s OWN return on its beta
    (regressing a week's return against a beta partly estimated FROM that
    same week's return would mechanically inflate R^2). This shifts
    :func:`characteristics.beta_characteristic`'s output forward by one
    week (``out[t] = beta_all[t-1]``, ``out[0] = NaN``) so ``out[t]`` uses
    ONLY weeks strictly before ``t`` -- built on the FULL panel (DEC-75
    (8) discipline), sliced afterward by the caller, exactly like every
    other characteristic in this package."""
    beta_all = characteristics.beta_characteristic(
        returns, symbols, market_symbol=market_symbol, trail_win=trail_win, min_weeks=trail_win)
    out = np.full_like(beta_all, np.nan)
    out[1:] = beta_all[:-1]
    return out


def factor_share_from_trailing_beta(
    window_returns: np.ndarray, window_alive: np.ndarray, beta_prev: np.ndarray, *,
    min_universe: int = 10,
) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (a)(b): per week ``t``, the cross-sectional R^2
    of ``window_returns[t]`` on ``beta_prev[t]`` (a simple-OLS R^2 equals
    the squared Pearson correlation for a single predictor) -- a
    returns-vs-beta relation, THE SEAL's explicitly allowed category
    (never a characteristic-vs-outcome IC: no ``t -> t+1`` lookup here,
    same week on both sides). ``factor_share_median`` is the median over
    weeks with >= ``min_universe`` valid (alive, finite beta, finite
    return) symbols."""
    n_weeks = window_returns.shape[0]
    per_week: list[dict[str, Any]] = []
    for t in range(n_weeks):
        mask = window_alive[t] & ~np.isnan(beta_prev[t]) & ~np.isnan(window_returns[t])
        k = int(mask.sum())
        if k < min_universe:
            per_week.append({"t": t, "r2": None, "k": k})
            continue
        x, y = beta_prev[t, mask], window_returns[t, mask]
        if x.std() == 0.0 or y.std() == 0.0:
            per_week.append({"t": t, "r2": None, "k": k})
            continue
        r = float(np.corrcoef(x, y)[0, 1])
        per_week.append({"t": t, "r2": (r * r) if not math.isnan(r) else None, "k": k})
    finite = np.array([w["r2"] for w in per_week if w["r2"] is not None], dtype=np.float64)
    return {"per_week": per_week, "factor_share_median": float(np.median(finite)) if finite.size else float("nan"),
            "n_weeks_used": int(finite.size)}


def beta_dispersion_from_trailing_beta(beta_prev: np.ndarray, window_alive: np.ndarray) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (a)(c): cross-sectional dispersion of the
    (alive, finite) pooled ``beta_prev`` values -- mean/SD/quantiles, a
    plain descriptive summary of one array (THE SEAL's "single series"
    category), never touching an outcome. Reports summary statistics only
    (the raw pooled array a caller needs for RESAMPLING -- DEC-77's
    "measured" calibration -- comes from :func:`pooled_finite_beta`
    instead, kept OUT of this JSON-bound summary so the artifact does not
    balloon with one float per alive symbol-week)."""
    pooled = pooled_finite_beta(beta_prev, window_alive)
    if pooled.size == 0:
        return {"n_pooled": 0, "mean": float("nan"), "sd": float("nan"), "quantiles": {}}
    quantiles = {str(q): float(np.quantile(pooled, q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)}
    return {"n_pooled": int(pooled.size), "mean": float(pooled.mean()),
            "sd": float(pooled.std(ddof=1)) if pooled.size > 1 else float("nan"),
            "quantiles": quantiles}


def pooled_finite_beta(beta_prev: np.ndarray, window_alive: np.ndarray) -> np.ndarray:
    """The flat array of every (alive, finite) ``beta_prev`` entry in the
    window -- the empirical distribution :func:`simulate_factor_panel`'s
    ``beta_pool`` resamples from for the "measured"/"zero" calibrations
    (DEC-77 Entscheidung 1 (1): "betas drawn from the measured PIT-beta
    distribution -- resample the real betas")."""
    mask = window_alive & ~np.isnan(beta_prev)
    return beta_prev[mask].astype(np.float64)


def factor_calibration_report(
    window_returns: np.ndarray, window_alive: np.ndarray, symbols: list[str], beta_prev: np.ndarray, *,
    market_symbol: str = "BTCUSDT", min_universe: int = 10,
) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (a), assembled: :func:`measure_market_factor`
    + :func:`factor_share_from_trailing_beta` +
    :func:`beta_dispersion_from_trailing_beta`, plus DEC-77 task brief item
    4's ANALYTIC PLAUSIBILITY line (label says so, explicitly NOT a
    verdict-bearing number): the mechanical cross-sectional momentum the
    measured market persistence alone implies, ``(2/pi)*arcsin(rho_f) *
    factor_share`` (DEC-77 "Anlass", verbatim: "IC_t ~ sign(f_t*f_t+1) *
    Faktoranteil, E[sign] = (2/pi)*arcsin(rho_f)")."""
    mkt = measure_market_factor(window_returns, symbols, market_symbol=market_symbol)
    share = factor_share_from_trailing_beta(window_returns, window_alive, beta_prev, min_universe=min_universe)
    disp = beta_dispersion_from_trailing_beta(beta_prev, window_alive)
    rho_f, fshare = mkt["rho_f_measured"], share["factor_share_median"]
    # math.asin's domain is [-1, 1]; a Pearson correlation is mathematically bounded there but
    # floating-point rounding can push a near-perfect-correlation estimate a hair past +/-1 --
    # clip defensively (never a real-data phenomenon, just an IEEE-754 rounding guard).
    rho_f_clipped = max(-1.0, min(1.0, rho_f)) if not math.isnan(rho_f) else float("nan")
    analytic_mom = ((2.0 / math.pi) * math.asin(rho_f_clipped) * fshare
                    if not (math.isnan(rho_f_clipped) or math.isnan(fshare)) else float("nan"))
    return {
        "market_factor": mkt, "factor_share": share, "beta_dispersion": disp,
        "beta_trail_weeks": CALIBRATION_BETA_TRAIL_WEEKS,
        "analytic_mechanical_momentum": {
            "value": analytic_mom,
            "formula": "(2/pi)*arcsin(rho_f_measured) * factor_share_median",
            "label": "Analytische Approximation (Plausibilitaetszeile, DEC-77 item 4) -- KEIN Verdikt.",
        },
    }


# ----------------------------------------------------------------------------
# DEC-77 Entscheidung 1 (b)/(c): the beta-control METHOD study, three rho_f/
# beta-draw calibrations x ic.BETA_CONTROL_METHODS x the 7 F-XSEC1 variants.
# ----------------------------------------------------------------------------

#: DEC-77 Entscheidung 1 (1): the three factor-null calibrations. sigma_f is
#: the SAME measured window value in all three (never itself a calibration
#: axis) -- only rho_f and the beta-draw source vary. drift_f is ALWAYS
#: DRIFT_F_DRIFTFREE (0.0): DEC-77's own "Anlass" finding is that rho_f
#: (AR(1) persistence) alone, with NO drift, already produces the mechanical
#: momentum artifact -- drift plays no role in this study.
FACTOR_NULL_CALIBRATIONS: tuple[str, ...] = ("measured", "stress", "zero")


def beta_controlled_factor_null(
    window_returns: np.ndarray, window_alive: np.ndarray, symbols: list[str], *, method: str,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    convention: ic.Convention = "close_at_last",
    n_reps: int = FACTOR_NULL_N_REPS_DEFAULT, seed: int = FACTOR_NULL_SEED,
    quantile: float = SELECTION_CEILING_ONE_SIDED_QUANTILE, market_symbol: str = "BTCUSDT",
    rho_f: float = 0.2, drift_f: float = DRIFT_F_DRIFTFREE, beta_pool: np.ndarray | None = None,
) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (b)/Entscheidung 2: the factor-preserving null
    under ONE ``(rho_f, beta_pool)`` configuration, with the REGISTERED
    beta-control ``method`` (:data:`ic.BETA_CONTROL_METHODS`) applied
    INSIDE the simulation via :func:`ic.apply_beta_control` -- this is what
    BOTH :func:`beta_control_method_study` (the calibration grid) AND
    ``run.py``'s real-run null-calibration recomputation call (ONE method,
    the registered one, DEC-77 Entscheidung 2) share, so a method behaves
    IDENTICALLY in the calibration study and in a real run. C.14 loud fail
    on an unrecognised ``method`` (:func:`ic.beta_control_trail_weeks`
    raises before any simulation runs).

    Per replicate: :func:`simulate_factor_panel` draws a fresh panel (this
    call's ``rho_f``/``drift_f``/``beta_pool``), the SIMULATED beta at
    ``method``'s trailing window is estimated from the SIMULATED panel's
    OWN "BTC column" (never the real one -- THE SEAL), with
    ``min_weeks = trail_win`` (DEC-77 item 2(i)'s "exclude symbols with
    fewer than the window's weeks"), then ``method`` is applied per
    variant. Reports the SAME per-variant shape as
    :func:`factor_preserving_null` (``factor_sd``, ``quantile_one_sided``,
    ``mean_ic_draws_mean``/``_sd``) plus ``ceiling_mean_of_max`` (mean,
    over replicates, of the max mean-IC across ``variants`` -- the GL-012
    selection ceiling under this method/calibration) and ``coverage_mean``
    (mean, over replicates and variants, of
    :func:`ic.trailing_beta_coverage`'s fraction -- ``None`` for
    ``"none"``, which has no beta at all)."""
    n_weeks, n_symbols = window_returns.shape
    trail_win = ic.beta_control_trail_weeks(method)     # raises on an unknown method, BEFORE any simulation
    sigmas = window_sigma_f_sigma_e(window_returns, symbols, market_symbol=market_symbol)
    sigma_f, sigma_e_used = sigmas["sigma_f"], sigmas["sigma_e_used"]

    rng = np.random.default_rng(seed)
    per_week_ic_pool: dict[str, list[float]] = {v: [] for v in variants}
    mean_ic_draws: dict[str, list[float]] = {v: [] for v in variants}
    coverage_fractions: list[float] = []

    for _rep in range(n_reps):
        sim = simulate_factor_panel(n_weeks, n_symbols, sigma_f=sigma_f, sigma_e=sigma_e_used,
                                     rho_f=rho_f, drift_f=drift_f, rng=rng, beta_pool=beta_pool)
        sim_returns = sim["returns"]
        beta_pit = None
        if trail_win is not None:
            beta_pit = characteristics.beta_characteristic(
                sim_returns, symbols, market_symbol=market_symbol, trail_win=trail_win, min_weeks=trail_win)
        for variant in variants:
            char = characteristics.weekly_only_proxy_characteristic(variant, sim_returns)
            applied = ic.apply_beta_control(method, char, sim_returns, window_alive, beta_pit=beta_pit,
                                             symbols=symbols, market_symbol=market_symbol)
            res = ic.weekly_ic_series(applied["characteristic"], applied["returns"], window_alive,
                                       convention=convention)
            mean_ic_draws[variant].append(res["mean_ic"])
            per_week_ic_pool[variant].extend(w["ic"] for w in res["weekly"] if not math.isnan(w["ic"]))
            if applied["coverage"] is not None:
                coverage_fractions.append(applied["coverage"]["coverage_fraction"])

    ceiling_mean_of_max = _mean_of_max(mean_ic_draws, variants, n_reps)
    coverage_mean = float(np.mean(coverage_fractions)) if coverage_fractions else None

    per_variant: dict[str, Any] = {}
    for variant in variants:
        direction = REGISTERED_DIRECTION[variant]
        pool_arr = np.array(per_week_ic_pool[variant], dtype=np.float64)
        factor_sd = float(pool_arr.std(ddof=1)) if pool_arr.size > 1 else float("nan")
        draws = np.array([d for d in mean_ic_draws[variant] if not math.isnan(d)], dtype=np.float64)
        if draws.size == 0:
            q = float("nan")
        elif direction == "positive":
            q = float(np.quantile(draws, quantile))
        else:
            q = float(np.quantile(draws, 1.0 - quantile))
        per_variant[variant] = {
            "direction": direction, "factor_sd": factor_sd, "n_ic_pooled": int(pool_arr.size),
            "quantile_one_sided": q, "quantile_level": quantile,
            "mean_ic_draws_mean": float(draws.mean()) if draws.size else float("nan"),
            "mean_ic_draws_sd": float(draws.std(ddof=1)) if draws.size > 1 else float("nan"),
            "n_reps_finite": int(draws.size),
        }

    return {
        "variants": per_variant, "ceiling_mean_of_max": ceiling_mean_of_max,
        "coverage_mean": coverage_mean, "method": method, "beta_window_weeks": trail_win,
        "rho_f": rho_f, "drift_f": drift_f, "sigma_f": sigma_f, "sigma_e_used": sigma_e_used,
        "n_reps": n_reps, "seed": seed, "convention": convention, "market_symbol": market_symbol,
        "n_weeks": n_weeks, "n_symbols": n_symbols,
    }


def beta_control_method_study(
    window_returns: np.ndarray, window_alive: np.ndarray, symbols: list[str], *,
    rho_f_measured: float, beta_pool_measured: np.ndarray,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    methods: tuple[str, ...] = ic.BETA_CONTROL_METHODS,
    convention: ic.Convention = "close_at_last", market_symbol: str = "BTCUSDT",
    n_reps: int = 300, seed: int = FACTOR_NULL_SEED,
    quantile: float = SELECTION_CEILING_ONE_SIDED_QUANTILE,
) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (b): the full grid -- :data:`FACTOR_NULL_
    CALIBRATIONS` (3) x ``methods`` (9, :data:`ic.BETA_CONTROL_METHODS`) x
    ``variants`` (7) -- each cell one :func:`beta_controlled_factor_null`
    call. ``n_reps`` DEFAULTS to 300 (task brief: ">= 500 reps/cell is
    acceptable for the grid, document; use >= 1000 for the recommended
    method in the final table" -- the CALLER passes a higher ``n_reps`` for
    a single re-run of the winning method once :func:`
    beta_control_pass_table`/the recommendation have picked it, this
    function itself always runs the SAME ``n_reps`` across the whole grid).
    ``rho_f_measured``/``beta_pool_measured`` come from
    :func:`factor_calibration_report`/:func:`pooled_finite_beta` (the
    caller's job -- keeps this function's signature independent of the
    calibration-measurement machinery)."""
    calibrations: dict[str, dict[str, float | np.ndarray | None]] = {
        "measured": {"rho_f": rho_f_measured, "beta_pool": beta_pool_measured},
        "stress": {"rho_f": 0.2, "beta_pool": None},
        "zero": {"rho_f": 0.0, "beta_pool": beta_pool_measured},
    }
    out: dict[str, Any] = {}
    for cal_name in FACTOR_NULL_CALIBRATIONS:
        cfg = calibrations[cal_name]
        methods_out: dict[str, Any] = {}
        for method in methods:
            methods_out[method] = beta_controlled_factor_null(
                window_returns, window_alive, symbols, method=method, variants=variants,
                convention=convention, n_reps=n_reps, seed=seed, quantile=quantile,
                market_symbol=market_symbol, rho_f=cfg["rho_f"], drift_f=DRIFT_F_DRIFTFREE,
                beta_pool=cfg["beta_pool"])
        out[cal_name] = {"rho_f": cfg["rho_f"], "uses_measured_betas": cfg["beta_pool"] is not None,
                          "methods": methods_out}
    return {
        "calibrations": out, "n_reps": n_reps, "seed": seed, "quantile_level": quantile,
        "methods": list(methods), "variants": list(variants),
        "label": ("DEC-77 Entscheidung 1 (b): 3 Kalibrierungen (measured/stress/zero) x "
                  f"{len(methods)} Beta-Kontroll-Methoden x {len(variants)} Varianten, driftfrei "
                  "(rho_f allein erzeugt den Artefakt, DEC-77 Anlass)."),
    }


def block_permute_week_index(n_weeks: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """The index permutation :func:`block_permutation_null_draws` applies
    to the OUTCOME panel: partition ``0..n_weeks-1`` into consecutive
    blocks of ``block_size`` weeks (the final block shorter if
    ``n_weeks`` does not divide evenly), shuffle the BLOCK ORDER (never
    the within-block order -- the point of a block permutation is to keep
    short-range time dependence intact while destroying the ``t <->
    outcome`` alignment), and concatenate. DEC-75 Entscheidung 1 (2):
    "Wochenlabel-/Block-Permutation des Outcome-Panels ueber die Zeit,
    Querschnitt intakt" -- the cross-section within any single week is
    never touched, only which week's row lands at which position."""
    n_blocks = math.ceil(n_weeks / block_size)
    blocks = [np.arange(b * block_size, min((b + 1) * block_size, n_weeks)) for b in range(n_blocks)]
    order = rng.permutation(n_blocks)
    return np.concatenate([blocks[b] for b in order])


def block_permutation_null_draws(
    characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, *,
    convention: ic.Convention = "close_at_last", block_size: int = BLOCK_SIZE_WEEKS,
    n_reps: int = 1000, seed: int = 53,
) -> np.ndarray:
    """DEC-75 Entscheidung 1 (2): ``n_reps`` window-mean-IC draws under the
    block-permuted-outcome null -- the CHARACTERISTIC stays pinned to its
    real week index ``t`` (real predictive information, if any, stays put);
    only the OUTCOME rows (``returns``/``alive`` together, so a symbol's
    delisting-week bookkeeping stays internally consistent) are
    block-permuted via :func:`block_permute_week_index`. Run-mode-only
    (never called from ``--prelaunch``, per the task brief) -- this is the
    selection-ceiling/permutation-p null re-measured on the REAL K series
    once a run exists."""
    n_weeks = returns.shape[0]
    rng = np.random.default_rng(seed)
    draws = np.full(n_reps, np.nan, dtype=np.float64)
    for i in range(n_reps):
        perm_idx = block_permute_week_index(n_weeks, block_size, rng)
        res = ic.weekly_ic_series(characteristic, returns[perm_idx], alive[perm_idx], convention=convention)
        draws[i] = res["mean_ic"]
    return draws


def block_permutation_pvalue(
    ic_real: float, characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, *,
    direction: str, convention: ic.Convention = "close_at_last",
    block_size: int = BLOCK_SIZE_WEEKS, n_reps: int = 1000, seed: int = 53,
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (2), run-mode permutation p-value: one-sided,
    registered-``direction``, WITH the standard ``(1+count)/(1+n_reps)``
    continuity correction (a permutation p-value is never exactly 0,
    however extreme the real statistic -- Davison & Hinkley 1997 Sec
    4.2). ``direction`` is ``"positive"``/``"negative"`` (matches
    :data:`REGISTERED_DIRECTION`'s values)."""
    if direction not in ("positive", "negative"):
        raise ValueError(f"direction must be 'positive' or 'negative', got {direction!r}")
    draws = block_permutation_null_draws(
        characteristic, returns, alive, convention=convention, block_size=block_size,
        n_reps=n_reps, seed=seed)
    finite = draws[~np.isnan(draws)]
    if finite.size == 0:
        return {"p_value": float("nan"), "n_reps": n_reps, "n_reps_finite": 0,
                "draws_mean": float("nan"), "draws_sd": float("nan"),
                "direction": direction, "block_size": block_size, "ic_real": ic_real}
    if direction == "positive":
        count = int((finite >= ic_real).sum())
    else:
        count = int((finite <= ic_real).sum())
    p_value = (1 + count) / (1 + finite.size)
    return {
        "p_value": p_value, "n_reps": n_reps, "n_reps_finite": int(finite.size),
        "draws_mean": float(finite.mean()), "draws_sd": float(finite.std(ddof=1)) if finite.size > 1 else float("nan"),
        "direction": direction, "block_size": block_size, "ic_real": ic_real,
    }
