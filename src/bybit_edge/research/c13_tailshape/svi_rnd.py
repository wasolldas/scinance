"""Risk-neutral tail side of H-13: SVI fit -> Breeden-Litzenberger RND -> GPD-PWM.

Pipeline (pre-registered, registry H-13):
  1. **SVI fit** on the filtered IV smile in raw SVI parametrisation of the
     total variance w(k) = a + b*(rho*(k - m) + sqrt((k - m)^2 + sigma^2)),
     5 parameters, least-squares calibration (deterministic multi-start).
  2. **Breeden-Litzenberger RND**: q(K) = d^2 C / dK^2 with C(K) the Black-76
     call price surface implied by the SVI fit (r = 0, discount factor 1),
     evaluated numerically on a dense log-moneyness grid, clipped at 0 and
     renormalised.
  3. **GPD fit via probability-weighted moments (PWM)** — NOT MLE; PWM
     (Hosking & Wallis 1987) is more robust for the small effective samples
     here — on the RND excess distribution BELOW the 5% RND quantile (left
     tail). The truncated tail density is converted to a deterministic
     inverse-CDF pseudo-sample of excesses X = q05 - K before the PWM fit.
  4. **SE via strike bootstrap**: resample the observed strikes with
     replacement, refit SVI + RND + PWM, 500 reps.

Numerical truncation note: the RND grid spans log-moneyness
``K_GRID_RANGE`` around the forward; tail mass beyond the lower grid edge
(~8% of forward at -2.5) is ignored. Documented in README_H13.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
# scipy.integrate.trapezoid (stable name for the whole pinned scipy>=1.12
# range) instead of a numpy spelling: np.trapezoid only exists from numpy 2.0
# and np.trapz was REMOVED in numpy 2.0, so neither numpy name is portable
# across the repo's numpy>=1.26 pin (audit_h13 Bug 8).
from scipy.integrate import trapezoid
from scipy.optimize import least_squares
from scipy.stats import norm

#: Pre-registered left-tail RND quantile (registry H-13, non-negotiable).
TAIL_ALPHA = 0.05
#: Pre-registered strike-bootstrap repetitions.
N_BOOTSTRAP = 500
#: Log-moneyness grid for the BL density (dense, fixed, deterministic).
K_GRID_RANGE = (-2.5, 1.5)
K_GRID_N = 801
#: Size of the deterministic inverse-CDF pseudo-sample for the PWM fit.
PWM_SAMPLE_N = 400
#: Minimum distinct strikes for an SVI refit inside the bootstrap.
MIN_UNIQUE_STRIKES = 5


class RndError(RuntimeError):
    """Raised when the SVI/RND/GPD pipeline cannot produce an estimate."""


# ----------------------------------------------------------------------------
# SVI
# ----------------------------------------------------------------------------

def svi_total_variance(params: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Raw SVI total variance w(k) = a + b*(rho*(k-m) + sqrt((k-m)^2 + s^2))."""
    a, b, rho, m, s = params
    km = np.asarray(k, dtype=np.float64) - m
    return a + b * (rho * km + np.sqrt(km * km + s * s))


def fit_svi(k: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, float]:
    """Least-squares raw-SVI calibration; returns (params, rms_residual).

    Deterministic: a fixed small set of starting points, best final cost wins.
    Bounds keep b >= 0, |rho| < 1, sigma > 0; positivity of w on the observed
    smile is checked after the fit.
    """
    k = np.asarray(k, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    good = np.isfinite(k) & np.isfinite(w) & (w > 0)
    k, w = k[good], w[good]
    if k.size < MIN_UNIQUE_STRIKES:
        raise RndError(f"too few smile points for SVI fit: {k.size}")
    w_min, w_max = float(w.min()), float(w.max())
    k_lo, k_hi = float(k.min()), float(k.max())
    lb = np.array([-w_max, 1e-6, -0.999, k_lo - 1.0, 1e-4])
    ub = np.array([w_max * 2.0 + 1e-6, 10.0, 0.999, k_hi + 1.0, 5.0])

    def resid(p: np.ndarray) -> np.ndarray:
        return svi_total_variance(p, k) - w

    starts = [
        np.array([0.5 * w_min, 0.1, -0.5, 0.0, 0.1]),
        np.array([0.5 * w_min, 0.5, 0.0, 0.5 * (k_lo + k_hi), 0.2]),
        np.array([0.8 * w_min, 0.05, 0.5, 0.0, 0.3]),
    ]
    best: tuple[float, np.ndarray] | None = None
    for x0 in starts:
        x0c = np.clip(x0, lb + 1e-9, ub - 1e-9)
        try:
            sol = least_squares(resid, x0c, bounds=(lb, ub), method="trf")
        except ValueError:
            continue
        if best is None or sol.cost < best[0]:
            best = (float(sol.cost), sol.x.copy())
    if best is None:
        raise RndError("SVI calibration failed for all starts")
    params = best[1]
    w_fit = svi_total_variance(params, k)
    if np.any(w_fit <= 0):
        raise RndError("SVI fit yields non-positive total variance on the smile")
    rms = float(np.sqrt(np.mean((w_fit - w) ** 2)))
    return params, rms


# ----------------------------------------------------------------------------
# Breeden-Litzenberger RND
# ----------------------------------------------------------------------------

def black76_call(forward: float, strikes: np.ndarray, iv: np.ndarray,
                 t_years: float) -> np.ndarray:
    """Undiscounted Black-76 call prices (r = 0, df = 1)."""
    K = np.asarray(strikes, dtype=np.float64)
    sig = np.asarray(iv, dtype=np.float64) * math.sqrt(t_years)
    sig = np.maximum(sig, 1e-12)
    d1 = (np.log(forward / K) + 0.5 * sig * sig) / sig
    d2 = d1 - sig
    return forward * norm.cdf(d1) - K * norm.cdf(d2)


def rnd_from_svi(
    params: np.ndarray,
    forward: float,
    t_years: float,
    *,
    k_range: tuple[float, float] = K_GRID_RANGE,
    n_grid: int = K_GRID_N,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Breeden-Litzenberger density q(K) = d^2C/dK^2 from the SVI surface.

    Numerical second derivative (``np.gradient`` twice, non-uniform-safe) of
    the SVI-implied Black-76 call prices on a dense log-moneyness grid.
    Negative density (numerical noise OR a genuine butterfly-arbitrage
    violation of the SVI fit) is clipped at 0 and the density renormalised to
    unit mass over the grid; the fraction of probability mass removed by that
    clipping is reported as a diagnostic (audit_h13 Bug 2 — partial fix: a
    full Gatheral g(k) >= 0 arbitrage reject-and-refit is NOT implemented,
    the diagnostic makes a degraded fit visible downstream instead of silent).
    Returns ``(K_grid, q, clipped_mass_fraction)``.
    """
    if not (forward > 0 and t_years > 0):
        raise RndError(f"invalid forward/t: {forward}, {t_years}")
    kg = np.linspace(k_range[0], k_range[1], n_grid)
    K = forward * np.exp(kg)
    w = svi_total_variance(np.asarray(params, dtype=np.float64), kg)
    if np.any(~np.isfinite(w)) or np.any(w <= 0):
        raise RndError("SVI total variance non-positive on the RND grid")
    iv = np.sqrt(w / t_years)
    C = black76_call(forward, K, iv, t_years)
    q_raw = np.gradient(np.gradient(C, K), K)
    q = np.clip(q_raw, 0.0, None)
    neg_mass = float(trapezoid(np.clip(-q_raw, 0.0, None), K))
    mass = float(trapezoid(q, K))
    if not (math.isfinite(mass) and mass > 1e-8):
        raise RndError("BL density has no mass")
    clipped_mass_fraction = neg_mass / (neg_mass + mass) if math.isfinite(neg_mass) else float("nan")
    return K, q / mass, clipped_mass_fraction


def rnd_quantile(K: np.ndarray, q: np.ndarray, alpha: float) -> float:
    """alpha-quantile of the (grid-normalised) RND via the trapezoid CDF."""
    dK = np.diff(K)
    inc = 0.5 * (q[1:] + q[:-1]) * dK
    cdf = np.concatenate([[0.0], np.cumsum(inc)])
    cdf /= cdf[-1]
    return float(np.interp(alpha, cdf, K))


def left_tail_excess_sample(
    K: np.ndarray,
    q: np.ndarray,
    *,
    alpha: float = TAIL_ALPHA,
    n_sample: int = PWM_SAMPLE_N,
) -> tuple[np.ndarray, float]:
    """Deterministic inverse-CDF pseudo-sample of left-tail excesses.

    Truncates the RND below its ``alpha`` quantile q_alpha, forms the excess
    variable X = q_alpha - K > 0 (distance below the tail threshold), builds
    its normalised CDF from the trapezoid mass and evaluates the inverse CDF
    at the ``n_sample`` mid-point levels (i - 0.5)/n. Returns
    ``(excess_sample, q_alpha)``.
    """
    q_alpha = rnd_quantile(K, q, alpha)
    mask = K < q_alpha
    if int(mask.sum()) < 10:
        raise RndError(f"too few grid points below the {alpha:.0%} RND quantile")
    Kt = np.concatenate([K[mask], [q_alpha]])
    qt = np.concatenate([q[mask], [float(np.interp(q_alpha, K, q))]])
    # excess X = q_alpha - K, ascending in X <=> descending in K
    X = (q_alpha - Kt)[::-1]
    dens = qt[::-1]
    dX = np.diff(X)
    inc = 0.5 * (dens[1:] + dens[:-1]) * dX
    cdf = np.concatenate([[0.0], np.cumsum(inc)])
    if cdf[-1] <= 0:
        raise RndError("left-tail RND mass is zero")
    cdf /= cdf[-1]
    levels = (np.arange(1, n_sample + 1) - 0.5) / n_sample
    sample = np.interp(levels, cdf, X)
    sample = sample[sample > 0]
    if sample.size < 10:
        raise RndError("degenerate left-tail excess sample")
    return sample, q_alpha


# ----------------------------------------------------------------------------
# GPD via probability-weighted moments (Hosking & Wallis 1987)
# ----------------------------------------------------------------------------

def gpd_fit_pwm(x: np.ndarray) -> tuple[float, float]:
    """GPD (xi, beta) via PWM; xi in the scipy ``genpareto`` sign convention.

    Hosking & Wallis (1987), GPD F(x) = 1 - (1 - k*x/a)^(1/k):
    with a0 = E[X], a1 = E[X*(1-F(X))] estimated by the unbiased
    order-statistic weights (n-j)/(n-1):
        k = a0/(a0 - 2*a1) - 2,   a = 2*a0*a1/(a0 - 2*a1),
    and scipy's shape c = xi = -k.
    """
    x = np.asarray(x, dtype=np.float64)
    x = np.sort(x[np.isfinite(x) & (x >= 0)])
    n = x.size
    if n < 10:
        raise RndError(f"too few points for PWM fit: {n}")
    a0 = float(x.mean())
    j = np.arange(1, n + 1)
    a1 = float(np.sum(((n - j) / (n - 1.0)) * x) / n)
    denom = a0 - 2.0 * a1
    if a0 <= 0 or abs(denom) < 1e-15:
        raise RndError("degenerate PWM moments")
    xi = -(a0 / denom - 2.0)
    beta = 2.0 * a0 * a1 / denom
    if not (math.isfinite(xi) and math.isfinite(beta) and beta > 0):
        raise RndError(f"invalid PWM estimate: xi={xi}, beta={beta}")
    return float(xi), float(beta)


# ----------------------------------------------------------------------------
# xi_Q pipeline + strike bootstrap
# ----------------------------------------------------------------------------

@dataclass(slots=True)
class XiQResult:
    """xi_Q estimate for one (symbol, snapshot day) cell."""

    xi: float
    beta: float
    q_alpha: float
    svi_params: np.ndarray
    svi_rms: float
    xi_boot: np.ndarray
    n_boot_failed: int
    #: Fraction of BL probability mass clipped at 0 (point estimate; Bug 2
    #: diagnostic — >~1e-3 signals a butterfly-arbitrage-violating SVI fit).
    clipped_mass_fraction: float = float("nan")

    @property
    def xi_se(self) -> float:
        b = self.xi_boot[np.isfinite(self.xi_boot)]
        return float(np.std(b, ddof=1)) if b.size > 1 else float("nan")

    def as_dict(self) -> dict[str, Any]:
        b = self.xi_boot[np.isfinite(self.xi_boot)]
        return {
            "xi": float(self.xi),
            "beta": float(self.beta),
            "rnd_tail_quantile_alpha": TAIL_ALPHA,
            "rnd_q_alpha_strike": float(self.q_alpha),
            "svi_params": {
                n: float(v) for n, v in
                zip(("a", "b", "rho", "m", "sigma"), self.svi_params)
            },
            "svi_rms": float(self.svi_rms),
            "clipped_mass_fraction": float(self.clipped_mass_fraction),
            "xi_se_bootstrap": self.xi_se,
            "n_bootstrap_valid": int(b.size),
            "n_bootstrap_failed": int(self.n_boot_failed),
        }


def _xi_q_once(strikes: np.ndarray, ivs: np.ndarray, forward: float,
               t_years: float, tail_alpha: float) -> tuple[float, float, float,
                                                           np.ndarray, float,
                                                           float]:
    k = np.log(np.asarray(strikes, dtype=np.float64) / forward)
    w = np.asarray(ivs, dtype=np.float64) ** 2 * t_years
    params, rms = fit_svi(k, w)
    K, q, clipped_frac = rnd_from_svi(params, forward, t_years)
    sample, q_alpha = left_tail_excess_sample(K, q, alpha=tail_alpha)
    xi, beta = gpd_fit_pwm(sample)
    return xi, beta, q_alpha, params, rms, clipped_frac


def estimate_xi_q(
    strikes: np.ndarray,
    ivs: np.ndarray,
    forward: float,
    t_years: float,
    *,
    tail_alpha: float = TAIL_ALPHA,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
) -> XiQResult:
    """Full xi_Q pipeline: SVI -> BL-RND -> GPD-PWM (+ strike bootstrap SE).

    Strike bootstrap: resample the observed (strike, IV) pairs with
    replacement; replicates with fewer than :data:`MIN_UNIQUE_STRIKES`
    distinct strikes or with a failed refit yield NaN and are counted in
    ``n_bootstrap_failed`` (deterministic under ``seed``).
    """
    strikes = np.asarray(strikes, dtype=np.float64)
    ivs = np.asarray(ivs, dtype=np.float64)
    xi, beta, q_alpha, params, rms, clipped_frac = _xi_q_once(
        strikes, ivs, forward, t_years, tail_alpha,
    )
    rng = np.random.default_rng(seed)
    boot = np.full(n_bootstrap, np.nan)
    n_failed = 0
    n = strikes.size
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if np.unique(strikes[idx]).size < MIN_UNIQUE_STRIKES:
            n_failed += 1
            continue
        try:
            boot[b] = _xi_q_once(
                strikes[idx], ivs[idx], forward, t_years, tail_alpha,
            )[0]
        except (RndError, ValueError):
            n_failed += 1
    return XiQResult(
        xi=xi, beta=beta, q_alpha=q_alpha, svi_params=params, svi_rms=rms,
        xi_boot=boot, n_boot_failed=n_failed,
        clipped_mass_fraction=clipped_frac,
    )
