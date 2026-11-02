"""Conjunctions of correlated one-sided conditions: product of single powers versus the exact joint power.

DEC-105 (7) double statement: the PRODUCT of the single powers treats the conditions as independent and overstates
the strictness when they share a term (A2: exact 22.93 / 23.77 bp against product 23.43 / 24.36 bp; two conditions of
power 0.90 each and correlation 0.82 / 0.91 have joint power 0.858 / 0.870, not 0.81).  This module computes

* ``product``  gate * prod_i P(T_i > thr_i)                       (independence, conservative lower bound),
* ``pair``     one named pair exact (bivariate normal quadrature), the remaining conditions as a product,
* ``joint``    all conditions exact, Monte Carlo with common random numbers and a FIXED seed (the shared term is the
               covariance of the conditions; the draws are generated once and reused for every effect).

``shared_term_spec`` builds the covariance of the contrast model of the A2 dossier: conditions ``D_j = E - P_j``
(event class minus placebo class ``j``) with a shared event term ``E``, mutually uncorrelated placebo means and an
optional null-distribution condition ``Y`` that is a projection on the first contrast (corr(Y, D_1) given).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from scipy import optimize
from scipy.stats import multivariate_normal, norm

from .schema import FeasibilityInputError

__all__ = ["ConjunctionSpec", "exact_joint_power_equal", "product_power_equal", "shared_term_spec", "MODES", "MC_SEED"]

MODES = ("product", "pair", "joint")
#: fixed seed of the shared standard-normal draws of the exact (joint) mode
MC_SEED = 31007


@lru_cache(maxsize=16)
def _draws(n: int, dim: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal((n, dim))


class ConjunctionSpec:
    """Conditions ``T_i ~ N(mean_factor_i * effect, cov_ii)`` passing when ``T_i > thr_i``; PASS needs all of them."""

    def __init__(self, names, cov, thresholds, mean_factors, gate: float = 1.0):
        self.names = tuple(names)
        m = len(self.names)
        self.cov = np.asarray(cov, dtype=float).reshape(m, m)
        self.thr = np.asarray(thresholds, dtype=float).reshape(m)
        self.mf = np.asarray(mean_factors, dtype=float).reshape(m)
        self.gate = float(gate)
        if m < 1:
            raise FeasibilityInputError("conjunction needs at least one condition")
        if not np.allclose(self.cov, self.cov.T, rtol=1e-9, atol=1e-12):
            raise FeasibilityInputError("conjunction covariance must be symmetric")
        if np.any(np.diag(self.cov) <= 0.0):
            raise FeasibilityInputError("conjunction variances must be > 0")
        if not 0.0 < self.gate <= 1.0:
            raise FeasibilityInputError("gate must be in (0, 1]")
        self.sd = np.sqrt(np.diag(self.cov))
        self.corr = self.cov / np.outer(self.sd, self.sd)

    # -- single and product ---------------------------------------------------------------------------------------
    def single_powers(self, effect: float) -> np.ndarray:
        return norm.sf((self.thr - self.mf * effect) / self.sd)

    def product_power(self, effect: float) -> float:
        return self.gate * float(np.prod(self.single_powers(effect)))

    # -- one pair exact ---------------------------------------------------------------------------------------------
    def pair_power(self, effect: float, pair: tuple[str, str]) -> float:
        ia, ib = (self.names.index(pair[0]), self.names.index(pair[1])) if all(p in self.names for p in pair) else (-1, -1)
        singles = self.single_powers(effect)
        if ia < 0:
            return self.product_power(effect)
        rest = [i for i in range(len(self.names)) if i not in (ia, ib)]
        a = (self.mf[ia] * effect - self.thr[ia]) / self.sd[ia]
        b = (self.mf[ib] * effect - self.thr[ib]) / self.sd[ib]
        rho = float(self.corr[ia, ib])
        if abs(rho) >= 1.0 - 1e-12:
            p_pair = float(norm.cdf(min(a, b))) if rho > 0 else max(0.0, float(norm.cdf(a) + norm.cdf(b) - 1.0))
        else:
            p_pair = float(multivariate_normal.cdf([a, b], mean=[0.0, 0.0], cov=[[1.0, rho], [rho, 1.0]]))
        return self.gate * p_pair * float(np.prod(singles[rest])) if rest else self.gate * p_pair

    # -- all exact (Monte Carlo, fixed seed, common random numbers) ----------------------------------------------
    def _centred_draws(self, n: int, seed: int) -> np.ndarray:
        chol = np.linalg.cholesky(self.cov + 1e-12 * np.eye(len(self.names)))
        return _draws(n, len(self.names), seed) @ chol.T

    def joint_power(self, effect: float, n: int = 400_000, seed: int = MC_SEED) -> float:
        y = self._centred_draws(n, seed)
        ok = np.all(y + self.mf * effect > self.thr, axis=1)
        return self.gate * float(np.mean(ok))

    def power(self, mode: str, effect: float, pair: tuple[str, str] | None = None, n: int = 400_000,
              seed: int = MC_SEED) -> float:
        if mode == "product":
            return self.product_power(effect)
        if mode == "pair":
            if pair is None:
                raise FeasibilityInputError("mode 'pair' needs the pair of condition names")
            return self.pair_power(effect, pair)
        if mode == "joint":
            return self.joint_power(effect, n, seed)
        raise FeasibilityInputError(f"unknown conjunction mode {mode!r}; allowed: {MODES}")

    def mde80(self, mode: str, pair: tuple[str, str] | None = None, target: float = 0.80, n: int = 400_000,
              seed: int = MC_SEED, hi: float = 1.0e4) -> float:
        """Effect with joint power ``target``; ``inf`` if the gate or a structural bound makes it unreachable."""
        if target / self.gate >= 1.0:
            return math.inf
        if mode == "joint":
            y = self._centred_draws(n, seed)
            f = lambda e: self.gate * float(np.mean(np.all(y + self.mf * e > self.thr, axis=1))) - target
            tol = 1e-6 * max(1.0, float(np.max(self.sd)))
        else:
            f = lambda e: self.power(mode, e, pair) - target
            tol = 1e-10
        lo = 0.0
        if f(hi) < 0.0:
            return math.inf
        return float(optimize.brentq(f, lo, hi, xtol=tol, rtol=1e-12, maxiter=200))


def product_power_equal(p_each: float, k: int) -> float:
    """Product of ``k`` equal single powers (independence)."""
    return p_each ** k


def exact_joint_power_equal(p_each: float, rho: float, k: int = 2) -> float:
    """Exact joint power of two conditions with single power ``p_each`` and correlation ``rho`` (k = 2 only)."""
    if k != 2:
        raise FeasibilityInputError("closed form implemented for two conditions")
    h = float(norm.ppf(p_each))
    if abs(rho) >= 1.0 - 1e-12:
        return p_each
    return float(multivariate_normal.cdf([h, h], mean=[0.0, 0.0], cov=[[1.0, rho], [rho, 1.0]]))


def shared_term_spec(*, event: dict, conditions: dict, null: dict | None, kappa: float, tau95: float,
                     z_alpha: float, scaled_null: bool, active: list[str], gate: float = 1.0) -> ConjunctionSpec:
    """Covariance model of the A2 contrasts for ONE window and ONE nuisance line (all numbers are plain floats).

    ``event``       ``{"sd", "c", "n"}``: class SD, variance factor ``c`` and number of event clusters.
    ``conditions``  ordered ``{name: {"sd", "c", "n", "se"}}``: placebo class SD, ``c``, count and the SE of the
                    contrast ``D_j = E - P_j`` (binding SE).  The first entry is the primary condition.
    ``null_test``   ``{"sd", "d95", "centre_sd"}`` or ``None``; active when ``"null_test"`` is in ``active``.
    ``kappa``       mean factor of the null condition (share of the effect that survives the centring).
    ``tau95``       scaled-null tail factor (threshold = ``tau95 * SE_primary`` if ``scaled_null``).
    """
    names = list(conditions)
    var_e = event["sd"] ** 2 * event["c"] / event["n"]
    var_p = {j: conditions[j]["sd"] ** 2 * conditions[j]["c"] / conditions[j]["n"] for j in names}
    c_ep = {j: 0.5 * (var_e + var_p[j] - conditions[j]["se"] ** 2) for j in names}
    m = len(names)
    s3 = np.zeros((m, m))
    for a, i in enumerate(names):
        for b, j in enumerate(names):
            s3[a, b] = conditions[i]["se"] ** 2 if a == b else var_e - c_ep[i] - c_ep[j]
    se1 = conditions[names[0]]["se"]
    full_names = names + (["null_test"] if null is not None else [])
    dim = len(full_names)
    cov = np.zeros((dim, dim))
    cov[:m, :m] = s3
    thr = [z_alpha * conditions[j]["se"] for j in names]
    mf = [1.0] * m
    if null is not None:
        if scaled_null:
            rho = math.sqrt(max(0.0, 1.0 - (null["centre_sd"] / se1) ** 2))
            s_y = se1
            thr_null = tau95 * se1
        else:
            rho = null["sd"] / se1
            s_y = null["sd"]
            thr_null = null["d95"]
        cov_y = rho * s_y * s3[0, :] / se1
        cov[m, :m] = cov_y
        cov[:m, m] = cov_y
        cov[m, m] = s_y ** 2
        thr.append(thr_null)
        mf.append(kappa)
    keep = [i for i, nm in enumerate(full_names) if nm in active]
    if not keep:
        raise FeasibilityInputError("no active condition in a conjunction step")
    cov_k = cov[np.ix_(keep, keep)]
    return ConjunctionSpec([full_names[i] for i in keep], cov_k, [thr[i] for i in keep], [mf[i] for i in keep], gate)
