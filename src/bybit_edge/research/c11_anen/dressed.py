"""Dispersion-matched HAR baseline for the H-11c mess-gate (KAPITALFREI).

Registry H-11c (registered 2026-08-12, follow-up obligation from GL-022):
GL-022 established that the registered H-11 scoring rule compares a DIRAC
(HAR point forecast, CRPS = |f - y|) against a 20-member DISTRIBUTION (AnEn,
proper ensemble CRPS). That comparison hands an information-free forecaster a
CRPSS of ~0.21-0.29 before any skill is involved — the measured 0.24-0.29 lies
entirely inside that band, so the H-11 gate cannot separate information from
distributional geometry.

H-11c removes exactly that term: the HAR **point forecast stays byte-for-byte
unchanged** and is merely dressed with a k-member cloud drawn from the
EMPIRICAL distribution of its own in-fit residuals of the very same monthly
refit — i.e. from data <= t - embargo only, no look-ahead, no distributional
assumption, no scale estimated inside the evaluation window. Both sides are
then scored with the SAME registered ensemble CRPS.

Design points (registered, binding):
  * Dressing offsets are a deterministic quantile sample at plotting positions
    (j - 0.5) / k, j = 1..k, of the in-fit residuals (no RNG — the run is
    exactly reproducible and free of Monte-Carlo noise).
  * The offsets are mean-centred (registry Nachtrag 2026-08-12) so the dressed
    ensemble's mean equals the HAR point forecast EXACTLY: "Punktprognose
    UNVERAENDERT" is enforced, not merely approximated. OLS with intercept
    already makes the in-fit residual mean zero; centring the k-quantile
    sample removes the residual discretisation shift.
  * Offsets are frozen together with beta and reused between refits.

Honest direction of the remaining bias (registry H-11c Selbstkill-Risiko): the
in-fit residuals of an expanding OLS are narrower than its true out-of-sample
errors, which makes the dressed baseline slightly too sharp and therefore
works IN FAVOUR of the AnEn. The alternative (residuals from the evaluation
window) would be look-ahead and is rejected.

KAPITALFREI: pure forecast-scoring. numpy only.
"""
from __future__ import annotations

import numpy as np

from .baseline import FIT_EMBARGO_DAYS, MIN_FIT_SAMPLES, har_fit, har_predict


def dressing_offsets(residuals: np.ndarray, k: int) -> np.ndarray:
    """Deterministic k-point quantile sample of ``residuals``, mean-centred.

    Plotting positions (j - 0.5) / k, j = 1..k (linear interpolation between
    order statistics). Centring makes ``mean(offsets) == 0`` to machine
    precision, so dressing leaves the point forecast's location untouched.
    Returns shape (k,); raises on empty/non-finite-only input.
    """
    r = np.asarray(residuals, dtype=np.float64)
    r = r[np.isfinite(r)]
    if r.size == 0:
        raise ValueError("no finite residuals to build the dressing from")
    if k < 1:
        raise ValueError("k must be >= 1")
    pos = (np.arange(1, k + 1, dtype=np.float64) - 0.5) / float(k)
    q = np.quantile(r, pos)
    return q - float(np.mean(q))


def har_forecast_series_dressed(
    log_rv1: np.ndarray,
    log_rv5: np.ndarray,
    log_rv22: np.ndarray,
    targets: np.ndarray,
    dates: list[str],
    forecast_idx: np.ndarray,
    *,
    k: int,
    embargo: int = FIT_EMBARGO_DAYS,
    min_fit_samples: int = MIN_FIT_SAMPLES,
) -> tuple[np.ndarray, int, np.ndarray]:
    """HAR-RV forecasts PLUS the dispersion-matched k-member dressing.

    The forecast path is bit-identical to ``baseline.har_forecast_series``
    (same expanding fit ``<= t - embargo``, same monthly refit trigger, same
    ``min_fit_samples`` rule, same NaN policy) — pinned by a regression test.
    Additionally, at every refit the in-fit residuals ``y_train - X_train @
    beta`` are converted into k dressing offsets (see ``dressing_offsets``)
    and frozen alongside beta.

    Returns ``(forecasts, n_refits, members)`` with ``members`` of shape
    ``(len(forecast_idx), k)``; rows whose forecast is NaN are all-NaN.
    """
    x_all = np.column_stack([
        np.asarray(log_rv1, dtype=np.float64),
        np.asarray(log_rv5, dtype=np.float64),
        np.asarray(log_rv22, dtype=np.float64),
    ])
    y_all = np.asarray(targets, dtype=np.float64)
    row_ok = np.all(np.isfinite(x_all), axis=1)
    sample_ok = row_ok & np.isfinite(y_all)

    forecast_idx = np.asarray(forecast_idx, dtype=np.int64)
    if np.any(np.diff(forecast_idx) < 0):
        raise ValueError("forecast_idx must be ascending")

    out = np.full(forecast_idx.size, np.nan, dtype=np.float64)
    members = np.full((forecast_idx.size, int(k)), np.nan, dtype=np.float64)
    beta: np.ndarray | None = None
    offsets: np.ndarray | None = None
    fit_month: str | None = None
    n_refits = 0

    for i, t in enumerate(forecast_idx):
        t = int(t)
        month = dates[t][:7]
        if beta is None or month != fit_month:
            hi = t - embargo
            if hi >= 0:
                mask = sample_ok.copy()
                mask[hi + 1:] = False
                n_train = int(mask.sum())
                if n_train >= min_fit_samples:
                    beta = har_fit(x_all[mask], y_all[mask])
                    design = np.column_stack(
                        [np.ones(n_train, dtype=np.float64), x_all[mask]])
                    offsets = dressing_offsets(y_all[mask] - design @ beta, int(k))
                    n_refits += 1
            fit_month = month
        if beta is None or offsets is None or not row_ok[t]:
            continue
        fc = har_predict(beta, x_all[t])
        out[i] = fc
        members[i] = fc + offsets
    return out, n_refits, members


def block_bootstrap_p_two_sided(
    d: np.ndarray,
    *,
    block_len: int,
    n_bootstrap: int,
    seed: int = 42,
) -> float:
    """Two-sided circular block bootstrap p for H0: mean(d) == 0.

    Mirror of ``stats.block_bootstrap_p`` (same circular blocks, same add-one
    rule) but two-sided: p = (#{|mean(d*)| >= |mean(d_obs)|} + 1) / (B + 1).
    Used ONLY for the non-judgment-bearing median-vs-HAR point-forecast
    diagnostic registered in H-11c; it reads into no gate flag.
    """
    x = np.asarray(d, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2 or n_bootstrap < 1:
        return 1.0
    observed = abs(float(np.mean(x)))
    centered = x - float(np.mean(x))
    bs = max(1, min(int(block_len), n))
    n_blocks = int(np.ceil(n / bs))
    rng = np.random.default_rng(seed)
    offsets = np.arange(bs)
    count_ge = 0
    for _ in range(n_bootstrap):
        starts = rng.integers(0, n, size=n_blocks)
        idx = (starts[:, None] + offsets[None, :]) % n
        resample = centered[idx.reshape(-1)][:n]
        if abs(float(np.mean(resample))) >= observed:
            count_ge += 1
    return (count_ge + 1) / (n_bootstrap + 1)


def chi2_uniform_pvalue(counts: np.ndarray) -> tuple[float, float]:
    """Pearson chi^2 of a rank histogram against uniformity: (chi2, p).

    df = bins - 1; the survival function is evaluated via the regularised
    upper incomplete gamma Q(df/2, chi2/2) using ``math.gamma``-free numerics
    (scipy is NOT a dependency of this package). Returns (nan, nan) for an
    empty histogram. NON-JUDGMENT-BEARING (registry H-11c diagnostic (c)).
    """
    c = np.asarray(counts, dtype=np.float64)
    n = float(c.sum())
    bins = int(c.size)
    if n <= 0 or bins < 2:
        return float("nan"), float("nan")
    expected = n / bins
    chi2 = float(np.sum((c - expected) ** 2 / expected))
    return chi2, _chi2_sf(chi2, bins - 1)


def _chi2_sf(x: float, df: int) -> float:
    """P(X > x) for X ~ chi^2_df, via the regularised incomplete gamma Q(a, z).

    Series expansion for z < a + 1, Lentz continued fraction otherwise —
    the textbook Numerical-Recipes pair, accurate to ~1e-12 in the range used
    here (df = 20, x < 200). Pure-python; no scipy.
    """
    a, z = df / 2.0, x / 2.0
    if z < 0 or a <= 0:
        return float("nan")
    if z == 0:
        return 1.0
    import math
    log_gamma_a = math.lgamma(a)
    if z < a + 1.0:  # series for P(a, z); Q = 1 - P
        term = 1.0 / a
        total = term
        n = a
        for _ in range(10000):
            n += 1.0
            term *= z / n
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        p = total * math.exp(-z + a * math.log(z) - log_gamma_a)
        return max(0.0, min(1.0, 1.0 - p))
    tiny = 1e-300  # modified Lentz continued fraction for Q(a, z)
    b = z + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    q = math.exp(-z + a * math.log(z) - log_gamma_a) * h
    return max(0.0, min(1.0, q))


__all__ = [
    "block_bootstrap_p_two_sided",
    "chi2_uniform_pvalue",
    "dressing_offsets",
    "har_forecast_series_dressed",
]
