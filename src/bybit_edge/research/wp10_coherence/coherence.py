"""WP-10(A) -- Spearman coherence of premium-proxy series, STRESS_ABS vs.
quiet (KAPITALFREI, deskriptiv, KEIN Gate, kein rho-Schwellenwert).

Own Spearman-rho copy (repo convention: no cross-import between research
packages, ``c17_venue.stats``/``c22_l2tilt.driver`` each keep their own
too). ``cluster_bootstrap_rho_ci`` implements DEC-... "Cluster =
Kalendertag": since every series here is ALREADY one value per calendar
day, the calendar-day cluster bootstrap degenerates to the ordinary i.i.d.
resample of (x, y) PAIRS -- documented explicitly below, not left implicit.
``bonett_wright_se`` (1.06/sqrt(n-3)) is reported purely as a plausibility
ANCHOR alongside the bootstrap CI (spec), never used to decide anything.

**Fixed detrending transform (pinned, no parameter).** Before any pair's
Spearman rho is computed, both series are FIRST-DIFFERENCED over their
overlap (``_first_difference`` / ``differenced_pair_overlap``): raw
LEVELS of two otherwise-independent series that merely share a common
deterministic trend (e.g. a shared slow drift/ramp) would give Spearman a
spuriously high rho purely from the shared monotonic ordering, even with
fully independent innovations. Differencing removes any such shared
level/trend while leaving genuine co-movement in the INNOVATIONS intact.
The difference is taken over CONSECUTIVE AVAILABLE overlap days (not
necessarily calendar-consecutive -- same convention as
``rv.daily_close_log_returns``); the differenced observation is labelled
by the LATER of its two source days (so STRESS_ABS/quiet regime
membership of a differenced value follows the day the change lands on).
This is a fixed, always-on transform -- there is no "raw levels" mode.

KAPITALFREI: pure statistics. No cost quantity, no PASS/FAIL.
"""
from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "CoherenceError", "spearman_rho", "pair_overlap", "differenced_pair_overlap",
    "bonett_wright_se", "cluster_bootstrap_rho_ci", "effective_n",
    "pairwise_regime_result", "correlation_matrix",
]


class CoherenceError(RuntimeError):
    """Loud failure: cannot support a Spearman bootstrap CI on this input."""


def _rankdata_average(v: np.ndarray) -> np.ndarray:
    """Average ranks for ties (own copy, repo §8.2 convention)."""
    v = np.asarray(v, dtype=np.float64)
    n = v.size
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    inv = np.empty(n, dtype=np.int64)
    inv[order] = np.arange(n)
    obs = np.concatenate(([True], sv[1:] != sv[:-1]))
    dense = np.cumsum(obs)[inv]
    bounds = np.concatenate((np.nonzero(obs)[0], [n]))
    return 0.5 * (bounds[dense - 1] + bounds[dense] + 1).astype(np.float64)


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (average ranks + Pearson on ranks).
    NaN if degenerate (constant series or < 2 points)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size != y.size or x.size < 2:
        return float("nan")
    rx = _rankdata_average(x) - _rankdata_average(x).mean()
    ry = _rankdata_average(y) - _rankdata_average(y).mean()
    denom = float(np.sqrt(np.sum(rx ** 2) * np.sum(ry ** 2)))
    if denom <= 0.0 or not np.isfinite(denom):
        return float("nan")
    return float(np.sum(rx * ry) / denom)


def pair_overlap(series_a: dict[str, Any], series_b: dict[str, Any]
                 ) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Aligned ``(days, x, y)`` over the date INTERSECTION of two series."""
    da = dict(zip(series_a["days"], series_a["values"]))
    db = dict(zip(series_b["days"], series_b["values"]))
    days = sorted(set(da) & set(db))
    x = np.asarray([da[d] for d in days], dtype=np.float64)
    y = np.asarray([db[d] for d in days], dtype=np.float64)
    return days, x, y


def _first_difference(x: np.ndarray) -> np.ndarray:
    """The module's fixed, pinned detrending transform (see module
    docstring): a plain first difference, always applied, no parameter."""
    return np.diff(np.asarray(x, dtype=np.float64))


def differenced_pair_overlap(series_a: dict[str, Any], series_b: dict[str, Any]
                             ) -> tuple[list[str], np.ndarray, np.ndarray]:
    """``pair_overlap`` plus the fixed first-difference detrend -- what
    ``pairwise_regime_result`` actually correlates. Returned days align
    with the LATER day of each consecutive-available-observation pair
    (``n - 1`` entries; empty for an overlap shorter than 2 days)."""
    days, x, y = pair_overlap(series_a, series_b)
    if len(days) < 2:
        return [], np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)
    return days[1:], _first_difference(x), _first_difference(y)


def bonett_wright_se(n: int) -> float:
    """Bonett/Wright (2000) Spearman-rho SE: 1.06/sqrt(n-3). NaN for n<=3."""
    if n <= 3:
        return float("nan")
    return float(1.06 / np.sqrt(n - 3))


def cluster_bootstrap_rho_ci(x: np.ndarray, y: np.ndarray, *,
                             n_bootstrap: int = 1000, seed: int,
                             alpha: float = 0.05) -> dict[str, Any]:
    """Cluster (= calendar day) bootstrap CI of Spearman rho.

    Cluster unit IS the observation unit here (each series already carries
    ONE value per calendar day), so the cluster bootstrap degenerates to
    the ordinary i.i.d. resample of (x, y) PAIRS with replacement -- this
    is the cluster bootstrap correctly applied to daily-granularity data,
    not a simplification of it.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = x.size
    if n < 4:
        raise CoherenceError(f"cannot bootstrap a Spearman CI from n={n} day(s) (<4)")
    rng = np.random.default_rng(seed)
    observed = spearman_rho(x, y)
    reps = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        reps[i] = spearman_rho(x[idx], y[idx])
    finite = reps[np.isfinite(reps)]
    if finite.size == 0:
        lo = hi = float("nan")
    else:
        lo, hi = (float(v) for v in np.quantile(finite, [alpha / 2, 1 - alpha / 2]))
    return {"rho": observed, "ci_lo": lo, "ci_hi": hi, "n": int(n),
            "n_bootstrap": int(n_bootstrap), "seed": int(seed), "alpha": alpha,
            "bonett_wright_se": bonett_wright_se(n)}


def effective_n(days: list[str], episodes: list[list[str]] | None) -> dict[str, Any]:
    """Effective N per regime (spec: "Anzahl Cluster, bei Episoden:
    Episodenzahl"). ``episodes`` (STRESS_ABS episodes) counts only those
    that intersect ``days`` (the regime's overlap subset)."""
    out: dict[str, Any] = {"n_days": len(days)}
    if episodes is None:
        out["n_episodes"] = None
    else:
        present = set(days)
        out["n_episodes"] = sum(1 for ep in episodes if present & set(ep))
    return out


def pairwise_regime_result(series_a: dict[str, Any], series_b: dict[str, Any],
                           stress_days: set[str], episodes: list[list[str]] | None, *,
                           n_bootstrap: int = 1000, seed: int) -> dict[str, Any]:
    """One pair's STRESS_ABS-vs-quiet split: correlation + bootstrap CI +
    Bonett/Wright anchor + effective N, on each regime's OVERLAP subset --
    computed on the FIRST-DIFFERENCED series (see module docstring)."""
    days, x, y = differenced_pair_overlap(series_a, series_b)
    stress_mask = np.asarray([d in stress_days for d in days], dtype=bool)
    out: dict[str, Any] = {"pair": [series_a["name"], series_b["name"]], "n_overlap": len(days)}
    for regime, mask in (("stress", stress_mask), ("quiet", ~stress_mask)):
        dsub = [d for d, m in zip(days, mask) if m]
        xsub, ysub = x[mask], y[mask]
        eff = effective_n(dsub, episodes if regime == "stress" else None)
        if xsub.size < 4:
            out[regime] = {**eff, "status": "TOO_FEW", "rho": None}
            continue
        boot = cluster_bootstrap_rho_ci(xsub, ysub, n_bootstrap=n_bootstrap, seed=seed)
        out[regime] = {**eff, "status": "OK", **boot}
    return out


def correlation_matrix(series_list: list[dict[str, Any]], stress_days: set[str],
                       episodes: list[list[str]] | None, *,
                       n_bootstrap: int = 1000, seed: int) -> dict[str, Any]:
    """All pairwise STRESS_ABS-vs-quiet Spearman results over ``series_list``."""
    names = [s["name"] for s in series_list]
    pairs = [
        pairwise_regime_result(series_list[i], series_list[j], stress_days, episodes,
                               n_bootstrap=n_bootstrap, seed=seed)
        for i in range(len(series_list)) for j in range(i + 1, len(series_list))
    ]
    return {"names": names, "n_series": len(series_list), "pairs": pairs}
