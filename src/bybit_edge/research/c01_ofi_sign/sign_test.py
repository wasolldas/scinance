"""Sign / correlation / hit-rate statistics + permutation surrogate + BH-FDR for
the C-01 OFI-sign mess-gate (Welle-2 WP, H-05, KAPITALFREI).

Per pre-fixed lag delta the test reports, for the aligned ``(OFI_t,
ret_{t+delta})`` pairs (built strictly causally in ``ofi.py``):

* ``corr``         = Pearson correlation corr(OFI_t, ret_{t+delta}),
* ``sign_direction`` = sign of that correlation (+ / - / 0),
* ``abs_corr``     = |corr|,
* ``hit_rate``     = conditional fraction where sign(OFI) == sign(ret),
* ``surrogate_p``  = permutation p-value (the OFI series is independently
                     permuted against the return series, destroying the coupling
                     while preserving each marginal). N >= 200, consistent with
                     WP-1 / Welle-1.

The registry H-05 gate combines these PER WINDOW PER CRITERION; the inverse
(significant negative) direction is NOT an H-05 pass — it is the trigger for a
separate H-05b (MM-replenishment reading). This module therefore reports the
sign NEUTRALLY and exposes ``inverse_significant`` so the gate-auditor can
distinguish an H-05 pass from an H-05b trigger. It NEVER returns a "passed"
verdict.

BH-FDR (Benjamini-Hochberg, alpha = 0.10) is applied across the whole F-OFI
family (all delta lags x symbols — registry H-05). Identical FDR contract to the
C-31 / C-17 implementations (registry §8.2 convention).

KAPITALFREI: pure sign / correlation measurement. There is NO friction, edge,
bps, PnL or Sharpe logic anywhere here — a bps column would be a gate violation.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: BH-FDR level for the F-OFI family (registry H-05).
FDR_ALPHA = 0.10

#: Registered magnitude floors (registry H-05, conservative from claims_register
#: C-01). These are GATE thresholds — reported, not adjudicated, here.
ABS_CORR_FLOOR = 0.05
HIT_RATE_FLOOR = 0.53
SURROGATE_P_MAX = 0.05


@dataclass(slots=True)
class SignTestResult:
    """Outcome of the OFI-sign test for one (delta) variant in one window."""

    delta_s: float
    n_pairs: int
    corr: float
    sign_direction: int          # +1 / -1 / 0  (sign of corr)
    abs_corr: float
    hit_rate: float
    surrogate_p: float
    n_surrogates: int
    surrogate_corr_mean: float

    def as_dict(self) -> dict[str, object]:
        return {
            "delta_s": float(self.delta_s),
            "n_pairs": int(self.n_pairs),
            "corr": float(self.corr),
            "sign_direction": int(self.sign_direction),
            "abs_corr": float(self.abs_corr),
            "hit_rate": float(self.hit_rate),
            "surrogate_p": float(self.surrogate_p),
            "n_surrogates": int(self.n_surrogates),
            "surrogate_corr_mean": float(self.surrogate_corr_mean),
        }


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation; 0.0 if either side has no variance / too few points."""
    if x.size < 3:
        return 0.0
    xs = x - x.mean()
    ys = y - y.mean()
    denom = float(np.sqrt(np.sum(xs * xs) * np.sum(ys * ys)))
    if denom == 0.0 or not np.isfinite(denom):
        return 0.0
    r = float(np.sum(xs * ys) / denom)
    if not np.isfinite(r):
        return 0.0
    return max(-1.0, min(1.0, r))


def _sign(v: float, eps: float = 1e-12) -> int:
    if v > eps:
        return 1
    if v < -eps:
        return -1
    return 0


def conditional_hit_rate(ofi: np.ndarray, ret: np.ndarray) -> float:
    """Fraction of non-flat pairs where ``sign(OFI) == sign(ret)``.

    Pairs where either OFI or the forward return is exactly flat are excluded
    from the denominator (they carry no directional information). Returns 0.5
    (chance) when there are no directional pairs.
    """
    so = np.sign(ofi)
    sr = np.sign(ret)
    mask = (so != 0) & (sr != 0)
    n = int(np.sum(mask))
    if n == 0:
        return 0.5
    return float(np.sum(so[mask] == sr[mask]) / n)


def permutation_surrogate_p(
    ofi: np.ndarray,
    ret: np.ndarray,
    observed_corr: float,
    *,
    n_surrogates: int = 200,
    seed: int = 42,
) -> tuple[float, float]:
    """Two-sided permutation p for corr(OFI, ret) under independent shuffling.

    The OFI series is randomly permuted against the (fixed) return series each
    surrogate, destroying any OFI->ret coupling while preserving both marginals.
    The statistic is ``|corr|`` so the test detects a coupling of EITHER sign
    (the registry needs the inverse/MM-replenishment direction to be detectable
    too, not just the aggression-follow direction). Empirical
    ``p = (#{|surrogate_corr| >= |observed_corr|} + 1) / (N + 1)``.

    Returns ``(p_value, surrogate_corr_mean)``.
    """
    n = min(ofi.size, ret.size)
    if n < 3 or n_surrogates < 1:
        return 1.0, 0.0
    ofi = np.asarray(ofi[:n], dtype=np.float64)
    ret = np.asarray(ret[:n], dtype=np.float64)
    obs = abs(observed_corr)
    rng = np.random.default_rng(seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    for k in range(n_surrogates):
        perm = rng.permutation(n)
        stats[k] = abs(_pearson(ofi[perm], ret))
    n_ge = int(np.sum(stats >= obs))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    return p_value, float(np.mean(stats))


def sign_test(
    ofi: np.ndarray,
    ret: np.ndarray,
    delta_s: float,
    *,
    n_surrogates: int = 200,
    seed: int = 42,
) -> SignTestResult:
    """Run the full OFI-sign test for one delta on aligned causal pairs."""
    ofi = np.asarray(ofi, dtype=np.float64)
    ret = np.asarray(ret, dtype=np.float64)
    n = int(min(ofi.size, ret.size))
    if n < 3:
        return SignTestResult(
            delta_s=delta_s, n_pairs=n, corr=0.0, sign_direction=0,
            abs_corr=0.0, hit_rate=0.5, surrogate_p=1.0,
            n_surrogates=0, surrogate_corr_mean=0.0,
        )
    ofi, ret = ofi[:n], ret[:n]
    corr = _pearson(ofi, ret)
    hit = conditional_hit_rate(ofi, ret)
    p_value, surr_mean = permutation_surrogate_p(
        ofi, ret, corr, n_surrogates=n_surrogates, seed=seed,
    )
    return SignTestResult(
        delta_s=delta_s,
        n_pairs=n,
        corr=corr,
        sign_direction=_sign(corr),
        abs_corr=abs(corr),
        hit_rate=hit,
        surrogate_p=p_value,
        n_surrogates=n_surrogates,
        surrogate_corr_mean=surr_mean,
    )


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i`` is
    significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. Identical contract to the C-31 / C-17
    implementations (registry §8.2 convention; each research package keeps its
    own copy — no cross-import between research packages).
    """
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit = 0.0
    k_max = -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max = rank
            p_crit = p_values[idx]
    rejected = [False] * m
    if k_max >= 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= k_max:
                rejected[idx] = True
    return rejected, p_crit
