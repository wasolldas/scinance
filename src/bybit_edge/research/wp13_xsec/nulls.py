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
    "block_permutation_pvalue",
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


def simulate_factor_panel(
    n_weeks: int, n_symbols: int, *, sigma_f: float, sigma_e: float,
    rho_f: float = 0.2, drift_f: float = 0.002, rng: np.random.Generator,
) -> dict[str, Any]:
    """Task brief item 3, verbatim construction: ``returns = beta_i * f_t +
    e_it`` -- ``beta_i ~ U(0.5, 2.0)`` drawn ONCE (fixed per symbol for
    this draw of ``rng``, i.e. identical across every week of this ONE
    panel -- the caller redraws ``beta`` too if it wants a fresh draw per
    replicate; :func:`factor_preserving_null` deliberately draws it ONCE
    for the whole window, not once per replicate, per the task brief:
    "beta_i ~ U(0.5, 2.0) (fixed per symbol, seed)"), ``f_t`` an AR(1) with
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
    beta = rng.uniform(0.5, 2.0, size=n_symbols)
    f = np.empty(n_weeks, dtype=np.float64)
    stationary_mean = drift_f / (1.0 - rho_f) if abs(1.0 - rho_f) > 1e-9 else 0.0
    f[0] = stationary_mean + sigma_f * rng.standard_normal()
    for t in range(1, n_weeks):
        f[t] = drift_f + rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    e_it = sigma_e * rng.standard_normal(size=(n_weeks, n_symbols))
    returns = beta[None, :] * f[:, None] + e_it
    return {"returns": returns, "beta": beta, "f": f}


def factor_preserving_null(
    window_returns: np.ndarray, window_alive: np.ndarray, symbols: list[str], *,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    convention: ic.Convention = "close_at_last",
    n_reps: int = FACTOR_NULL_N_REPS_DEFAULT, seed: int = FACTOR_NULL_SEED,
    quantile: float = SELECTION_CEILING_ONE_SIDED_QUANTILE,
    market_symbol: str = "BTCUSDT",
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (2) / task brief item 3: the factor-preserving
    null, sized to the window (``K`` from ``window_alive``, ``W`` from
    ``window_returns``). Only ever reads ``window_returns`` for TWO
    descriptive volatility scalars (``sigma_f`` = the window's BTC weekly
    return SD, ``sigma_e`` = the window's median per-symbol weekly return
    SD) -- the SAME "real returns feed a descriptive dispersion statistic,
    never an IC" discipline ``prelaunch.h30_feasibility`` already uses for
    ``sigma_xs``; every simulated IC in this function is
    SIMULATED-characteristic-vs-SIMULATED-outcome, per THE SEAL.

    For ``n_reps`` replicates (``beta`` redrawn once per replicate, ``f``/
    ``e_it`` redrawn every replicate -- see :func:`simulate_factor_panel`),
    runs the FULL per-variant pipeline
    (``characteristics.weekly_only_proxy_characteristic`` ->
    ``ic.weekly_ic_series`` on the window's REAL ``alive`` mask, matching
    ``persistence_null``'s reuse discipline) and reports, per variant:
      (a) ``factor_sd`` -- SD of the per-week IC, pooled over ALL weeks of
          ALL replicates (task brief: "SD(IC_t) per variant, the 'factor
          SD'").
      (b) (once, not per variant) ``selection_ceiling_mean_of_max`` --
          mean, over replicates, of that replicate's MAX window-mean-IC
          across the 7 variants (task brief: "the selection ceiling as
          mean-of-max over the 7 variants").
      (c) ``quantile_one_sided`` -- the registered-direction one-sided
          ``quantile`` (default 0.9936) of the window-mean-IC draws (task
          brief: "a per-variant one-sided 99.36% quantile of the
          window-mean IC").
    """
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
    sigma_e = float(np.median(finite_sd)) if finite_sd.size else 0.03

    rng = np.random.default_rng(seed)
    per_week_ic_pool: dict[str, list[float]] = {v: [] for v in variants}
    mean_ic_draws: dict[str, list[float]] = {v: [] for v in variants}

    for _rep in range(n_reps):
        sim = simulate_factor_panel(n_weeks, n_symbols, sigma_f=sigma_f, sigma_e=sigma_e, rng=rng)
        sim_returns = sim["returns"]
        for variant in variants:
            char = characteristics.weekly_only_proxy_characteristic(variant, sim_returns)
            res = ic.weekly_ic_series(char, sim_returns, window_alive, convention=convention)
            mean_ic_draws[variant].append(res["mean_ic"])
            per_week_ic_pool[variant].extend(w["ic"] for w in res["weekly"] if not math.isnan(w["ic"]))

    per_variant: dict[str, Any] = {}
    max_per_rep = np.full(n_reps, np.nan, dtype=np.float64)
    for rep_i in range(n_reps):
        vals = [mean_ic_draws[v][rep_i] for v in variants if not math.isnan(mean_ic_draws[v][rep_i])]
        if vals:
            max_per_rep[rep_i] = max(vals)
    finite_max = max_per_rep[~np.isnan(max_per_rep)]
    selection_ceiling_mean_of_max = float(finite_max.mean()) if finite_max.size else float("nan")

    for variant in variants:
        pool = np.array(per_week_ic_pool[variant], dtype=np.float64)
        factor_sd = float(pool.std(ddof=1)) if pool.size > 1 else float("nan")
        draws = np.array([d for d in mean_ic_draws[variant] if not math.isnan(d)], dtype=np.float64)
        direction = REGISTERED_DIRECTION[variant]
        if draws.size == 0:
            q = float("nan")
        elif direction == "positive":
            q = float(np.quantile(draws, quantile))
        else:
            q = float(np.quantile(draws, 1.0 - quantile))
        per_variant[variant] = {
            "direction": direction, "factor_sd": factor_sd, "n_ic_pooled": int(pool.size),
            "quantile_one_sided": q, "quantile_level": quantile,
            "mean_ic_draws_mean": float(draws.mean()) if draws.size else float("nan"),
            "mean_ic_draws_sd": float(draws.std(ddof=1)) if draws.size > 1 else float("nan"),
            "n_reps_finite": int(draws.size),
        }

    return {
        "variants": per_variant, "n_reps": n_reps, "seed": seed, "convention": convention,
        "sigma_f_btc_weekly": sigma_f, "sigma_e_median_symbol_weekly": sigma_e,
        "rho_f": 0.2, "drift_f": 0.002, "market_symbol": market_symbol,
        "selection_ceiling_mean_of_max": selection_ceiling_mean_of_max,
        "n_weeks": n_weeks, "n_symbols": n_symbols,
        "label": "faktorerhaltende Null (DEC-75 (2)): returns = beta_i*f_t + e_it, signalfrei.",
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
