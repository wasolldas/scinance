"""WP-10(A) -- portfolio-null CONSTANTS (KAPITALFREI, KEIN Gate).

Spec (WP10_SPEZIFIKATION.md Teil A, Nachtrag/Korrektur -- see the
addendum at the bottom of that file): TWO separate, reported constants,
both calibration input for a later portfolio gate (R4 6.2a), never a
threshold:

**(1) ``portfolio_null_table``** -- for k in {2,3,4,5}, the NULL
DISTRIBUTION (1.000 seeded draws) of the annualized SAMPLE Sharpe of the
EQUAL-WEIGHTED combination of k pure-noise signals: P&L_t =
mean_i(signal_i,t) (the k signals' P&L averaged INTO ONE combined path),
THEN the Sharpe of THAT combined path is taken -- never a sum of k
separate per-signal Sharpes (an earlier version of this module did that;
it was wrong, see below). Reports mean/sd/p95/p99 of this Sharpe across
the 1.000 draws, per k.

**(2) ``selection_ceiling``** -- from the SAME per-signal Sharpe draws
(single, INDEPENDENT noise signals, NOT combined), the expected MAXIMUM
Sharpe over K independent variants for K in {5,10,20,50,100}: both an
EMPIRICAL estimate (the mean of the max within each disjoint group of K
draws, drawn from one shared pool) and the Bailey & Lopez de Prado (2014,
"The Deflated Sharpe Ratio") closed-form approximation
``sigma_SR * ((1-gamma)*Phi^-1(1-1/K) + gamma*Phi^-1(1-1/(K*e)))``
(``gamma`` = 0.5772156649... the Euler-Mascheroni constant, ``Phi^-1``
the standard-normal inverse CDF) as a plausibility cross-check.

**Why these are two DIFFERENT statistics with opposite k/K-behaviour --
and why the previous sqrt(k)-growth claim for (1) was wrong.** Sharpe is
scale-invariant: ``Sharpe(c*R) == Sharpe(R)`` for any per-observation
constant c>0. Under the null every individual signal has POPULATION
Sharpe 0 (zero true information coefficient, IC), so the EQUAL-WEIGHTED
combined portfolio's population Sharpe is ALSO exactly 0, for every k --
diversifying k independent zero-IC bets never manufactures information
that wasn't there. What survives is only the SAMPLING NOISE of the
Sharpe ESTIMATOR, which (Lo 2002, cited in this repo's own constitution)
is governed primarily by the number of independent TIME observations T,
not by how many independent zero-mean signals were blended into one
path. So under this null: ``E[SR] ~ 0`` and ``SD(SR)`` stays roughly
CONSTANT as k grows from 2 to 5 (diversification neither manufactures
edge nor materially changes the estimator's T-driven sampling noise).
``sqrt(k)`` growth is a real phenomenon ONLY when the k signals share a
genuine, non-zero IC that averaging can concentrate toward (a completely
different, non-null quantity from what is measured here) -- it does
NOT apply to a pure-noise null, and this module no longer claims it does.

(2) is a fundamentally different, NONLINEAR (order-statistic) operation:
even though each individual Sharpe is unbiased around 0, the EXPECTED
MAXIMUM of K of them grows with K (the textbook Bailey/Lopez de Prado
"backtest overfitting" ceiling, roughly ``sigma_SR * sqrt(2*ln(K))`` for
large K) -- THIS is the genuine selection/data-mining growth a later
portfolio gate should be calibrated against, kept strictly separate from
the flat k=2..5 diversification statistic in (1).

**How ONE pure-noise signal is built** (``_signal_pnl``, unchanged from
the previous version): an independent Rademacher (+-1) sign sequence,
held constant within ``block_len``-day blocks (block-permuted: the
repo's standard 5-day block convention, ``c17_venue.stats``/
``c11_anen.stats``/``wp9_dvol.crossval``), applied to the REAL daily
return panel (``rv.panel_returns`` -- "auf diesem Bestand"). ``E[sign *
return] = 0`` by construction, so this is a genuine pure-noise signal
that nonetheless inherits the panel's real autocorrelation/vol-
clustering structure.

``_norm_ppf`` is an own numpy-only rational approximation of the
standard-normal inverse CDF (Acklam's algorithm, ~1e-9 relative
accuracy) -- this sandbox's declared toolset is numpy/duckdb/pyarrow, so
no scipy dependency is introduced for the one closed-form Bailey/LdP term.

KAPITALFREI: pure statistics, no PASS/FAIL, no PnL used as judgment.
"""
from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "PortfolioNullError", "K_VALUES", "SELECTION_K_VALUES", "BLOCK_LEN_DAYS",
    "N_BOOTSTRAP", "SELECTION_POOL_SIZE", "DEFAULT_SEED", "EULER_MASCHERONI",
    "ANNUALIZATION_DAYS_PER_YEAR", "expected_combo_sharpe_distribution",
    "portfolio_null_table", "selection_ceiling",
]

#: Repo block-bootstrap convention (5-day blocks, 1000 replicates).
BLOCK_LEN_DAYS = 5
N_BOOTSTRAP = 1000
DEFAULT_SEED = 53
K_VALUES: tuple[int, ...] = (2, 3, 4, 5)
SELECTION_K_VALUES: tuple[int, ...] = (5, 10, 20, 50, 100)
#: Shared pool size for `selection_ceiling`'s empirical grouping --
#: >= max(SELECTION_K_VALUES), and large enough for a stable groups-mean
#: even at K=100 (50 disjoint groups).
SELECTION_POOL_SIZE = 5_000
ANNUALIZATION_DAYS_PER_YEAR = 365.0
#: Euler-Mascheroni constant (Bailey/Lopez de Prado's `gamma`).
EULER_MASCHERONI = 0.5772156649015329


class PortfolioNullError(RuntimeError):
    """Loud failure: not enough return history / an invalid parameter."""


def _check_returns(returns: np.ndarray, block_len: int) -> np.ndarray:
    returns = np.asarray(returns, dtype=np.float64)
    returns = returns[np.isfinite(returns)]
    if returns.size < 2 * block_len:
        raise PortfolioNullError(
            f"need >= {2 * block_len} finite daily returns for block_len={block_len}, "
            f"got {returns.size}")
    return returns


def _signal_pnl(returns: np.ndarray, rng: np.random.Generator, *, block_len: int) -> np.ndarray:
    """ONE pure-noise signal's P&L path on ``returns`` (see module docstring)."""
    n = returns.size
    n_blocks = int(np.ceil(n / block_len))
    block_signs = rng.integers(0, 2, size=n_blocks) * 2 - 1
    signs = np.repeat(block_signs, block_len)[:n]
    return signs * returns


def _sharpe(pnl: np.ndarray) -> float:
    """Annualized sample Sharpe of ONE P&L path. 0.0 for a degenerate
    (constant/non-finite-SD) path -- never a fabricated large ratio."""
    sd = float(np.std(pnl, ddof=1))
    if sd <= 0.0 or not np.isfinite(sd):
        return 0.0
    return float(np.mean(pnl) / sd * np.sqrt(ANNUALIZATION_DAYS_PER_YEAR))


def _signal_sharpe(returns: np.ndarray, rng: np.random.Generator, *, block_len: int) -> float:
    """ONE pure-noise signal's OWN Sharpe (not combined with any other)."""
    return _sharpe(_signal_pnl(returns, rng, block_len=block_len))


def expected_combo_sharpe_distribution(
    returns: np.ndarray, k: int, *, n_bootstrap: int = N_BOOTSTRAP,
    seed: int = DEFAULT_SEED, block_len: int = BLOCK_LEN_DAYS,
) -> dict[str, Any]:
    """NULL distribution (``n_bootstrap`` draws) of the annualized sample
    Sharpe of the EQUAL-WEIGHTED combination of ``k`` pure-noise signals:
    each draw averages k fresh, independent signal P&L paths into ONE
    combined path (P&L_t = mean_i(signal_i,t)) and takes THAT path's
    Sharpe (never a sum of per-signal Sharpes -- see module docstring).
    Deterministic for a given ``(seed, k)``.
    """
    if k < 1:
        raise PortfolioNullError(f"k must be >= 1, got {k}")
    returns = _check_returns(returns, block_len)
    rng = np.random.default_rng((int(seed), int(k)))
    draws = np.empty(n_bootstrap, dtype=np.float64)
    for d in range(n_bootstrap):
        combined = np.mean(
            [_signal_pnl(returns, rng, block_len=block_len) for _ in range(k)], axis=0)
        draws[d] = _sharpe(combined)
    return {
        "k": int(k), "mean": float(np.mean(draws)), "sd": float(np.std(draws, ddof=1)),
        "p95": float(np.quantile(draws, 0.95)), "p99": float(np.quantile(draws, 0.99)),
        "n_bootstrap": int(n_bootstrap), "seed": int(seed), "block_len": int(block_len),
        "n_returns": int(returns.size),
    }


def portfolio_null_table(returns: np.ndarray, *, ks: tuple[int, ...] = K_VALUES,
                         n_bootstrap: int = N_BOOTSTRAP, seed: int = DEFAULT_SEED,
                         block_len: int = BLOCK_LEN_DAYS) -> dict[str, Any]:
    """The full k=2..5 table (spec: "je 1.000 Ziehungen"). No threshold --
    reported constants (mean/sd/p95/p99) per k, calibration input only
    (R4 6.2a)."""
    return {
        "ks": list(ks), "seed": int(seed), "block_len": int(block_len),
        "n_bootstrap": int(n_bootstrap),
        "results": {
            k: expected_combo_sharpe_distribution(returns, k, n_bootstrap=n_bootstrap, seed=seed,
                                                  block_len=block_len)
            for k in ks
        },
    }


# ------------------------------------------------------- selection_ceiling

def _norm_ppf(p: float) -> float:
    """Standard-normal inverse CDF (probit), Peter Acklam's rational
    approximation (~1.15e-9 max relative error) -- numpy-only, no scipy
    dependency for this one closed-form use (see module docstring)."""
    if not (0.0 < p < 1.0):
        raise PortfolioNullError(f"_norm_ppf needs 0 < p < 1, got {p}")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
        1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
        6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
        -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
        3.754408661907416e+00)
    p_low = 0.02425
    p_high = 1.0 - p_low
    if p < p_low:
        q = np.sqrt(-2.0 * np.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    else:
        q = np.sqrt(-2.0 * np.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    return float(x)


def _expected_max_bailey_lopez_de_prado(sigma_sr: float, k: int) -> float:
    """Bailey & Lopez de Prado (2014) closed-form E[max Sharpe over k
    independent trials] approximation (see module docstring)."""
    if k < 2:
        raise PortfolioNullError(f"k must be >= 2 for the E[max] approximation, got {k}")
    term1 = (1.0 - EULER_MASCHERONI) * _norm_ppf(1.0 - 1.0 / k)
    term2 = EULER_MASCHERONI * _norm_ppf(1.0 - 1.0 / (k * np.e))
    return float(sigma_sr * (term1 + term2))


def _signal_sharpe_pool(returns: np.ndarray, *, pool_size: int, seed: int,
                        block_len: int) -> np.ndarray:
    """A large, INDEPENDENT pool of single pure-noise-signal Sharpes -- the
    shared draw source for ``selection_ceiling``'s empirical grouping. Own
    RNG stream (tagged with a sentinel that can never collide with a real
    k/K value, apart from ``portfolio_null_table``'s ``(seed, k)``
    streams) so the two never silently share randomness. (numpy's
    ``SeedSequence`` only accepts non-negative integers, so the sentinel
    must be one too.)
    """
    _POOL_TAG = 999_999_999
    rng = np.random.default_rng((int(seed), _POOL_TAG))
    return np.asarray(
        [_signal_sharpe(returns, rng, block_len=block_len) for _ in range(pool_size)],
        dtype=np.float64)


def selection_ceiling(returns: np.ndarray, *, k_values: tuple[int, ...] = SELECTION_K_VALUES,
                      pool_size: int = SELECTION_POOL_SIZE, seed: int = DEFAULT_SEED,
                      block_len: int = BLOCK_LEN_DAYS) -> dict[str, Any]:
    """Expected MAXIMUM Sharpe over K independent pure-noise variants, for
    each K in ``k_values``, from ONE shared pool of independent per-signal
    Sharpe draws: an EMPIRICAL estimate (mean of the max within each
    disjoint group of K draws) alongside the Bailey/Lopez de Prado
    analytic approximation as a plausibility cross-check. No threshold --
    calibration input only (see module docstring).
    """
    if not k_values:
        raise PortfolioNullError("k_values must be non-empty")
    max_k = max(k_values)
    if pool_size < max_k:
        raise PortfolioNullError(f"pool_size={pool_size} must be >= max(k_values)={max_k}")
    returns = _check_returns(returns, block_len)
    pool = _signal_sharpe_pool(returns, pool_size=pool_size, seed=seed, block_len=block_len)
    sigma_sr = float(np.std(pool, ddof=1))

    results: dict[int, dict[str, Any]] = {}
    for k in k_values:
        n_groups = pool_size // k
        groups = pool[:n_groups * k].reshape(n_groups, k)
        empirical = float(np.mean(groups.max(axis=1)))
        analytic = _expected_max_bailey_lopez_de_prado(sigma_sr, k)
        results[k] = {"K": int(k), "empirical_expected_max": empirical,
                     "analytic_expected_max": analytic, "n_groups": int(n_groups)}
    return {
        "K_values": list(k_values), "seed": int(seed), "block_len": int(block_len),
        "pool_size": int(pool_size), "sigma_sr": sigma_sr, "n_returns": int(returns.size),
        "results": results,
    }
