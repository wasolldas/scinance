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
    "ic_threshold",
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

def analytic_permutation_floor(alive_window: np.ndarray, weeks: list[str]) -> dict[str, Any]:
    """``E_t[1/sqrt(K_t-1)]`` over the window's weeks, ``K_t =
    alive_window[t].sum()`` (matches ``state/runs/.../decile_degeneration_
    weekly.csv``'s ``n_symbols`` column, the source DEC-74 cites for its
    confirmed K figures). A week with ``K_t < 2`` contributes no value
    (undefined floor). Returns the full per-week series (DEC-53 artifact
    material) plus the window mean.

    **General tie-adjustment formula, for completeness (not what this
    estimator needs -- see module docstring):** if the PERMUTED side
    itself carried ``g`` tie groups of size ``t_1..t_g``, the exact
    variance would be ``Var[r] = 1/(K-1) * (K^3-K-sum(t_i^3-t_i)) /
    (K^3-K)`` -- a strictly smaller number, i.e. ties in the permuted side
    would make the floor a TIGHTER (smaller) bound, never wider. Since
    this module's permuted side is always the tie-free sequence
    ``0..K-1``, the correction factor is exactly 1 and drops out.
    """
    k_t = alive_window.sum(axis=1).astype(np.int64)
    n_weeks = len(weeks)
    floor_per_week = np.full(n_weeks, np.nan, dtype=np.float64)
    valid = k_t >= 2
    floor_per_week[valid] = 1.0 / np.sqrt((k_t[valid] - 1).astype(np.float64))
    finite = floor_per_week[valid]
    e_floor = float(finite.mean()) if finite.size else float("nan")
    return {
        "weeks": weeks, "k_series": k_t.tolist(),
        "floor_per_week": [None if math.isnan(v) else float(v) for v in floor_per_week],
        "e_floor": e_floor, "n_weeks": n_weeks, "n_weeks_valid": int(valid.sum()),
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
    beyond what the available lags support)."""
    total = 0.0
    for k in range(1, 5):
        rho_k = rho_by_lag.get(k)
        if rho_k is None:
            continue
        total += (1.0 - k / w) * rho_k
    inside = 1.0 + 2.0 * total
    return math.sqrt(inside) if inside > 0.0 else 0.0


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
    w = len(weeks)
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
        c_rho = c_rho_from_lag_autocorr(rho_by_lag, w=w)

        per_variant[variant] = {
            "direction": direction, "n_sims": n_sims, "seed": seed, "convention": convention,
            "quantile95_registered_direction": quantile95,
            "mean_ic_draws_mean": float(finite.mean()) if finite.size else float("nan"),
            "mean_ic_draws_sd": float(finite.std(ddof=1)) if finite.size > 1 else float("nan"),
            "n_sims_finite": int(finite.size),
            "rho_by_lag": {str(k): v for k, v in rho_by_lag.items()},
            "c_rho": c_rho,
        }
    return {"variants": per_variant, "ar1": {"phi": phi.tolist(), "sigma": sigma.tolist(),
            "n_pairs": ar1["n_pairs"], "n_obs": ar1["n_obs"], "phi_clip": ar1["phi_clip"]},
            "seed": seed, "n_sims": n_sims, "w": w}


# ----------------------------------------------------------------------------
# (a)+(d) threshold arithmetic
# ----------------------------------------------------------------------------

def ic_threshold(e_floor: float, c_rho: float, w: int, *, z: float = Z_PER_WINDOW) -> float:
    """DEC-74 (a), verbatim: ``IC_min(W) = 2.4865 * E_t[1/sqrt(K_t-1)] *
    c_rho / sqrt(W)``."""
    return z * e_floor * c_rho / math.sqrt(w)
