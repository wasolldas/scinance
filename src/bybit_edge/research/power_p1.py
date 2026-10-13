"""Power, MDE and regime assignment under programme rule P-1 (DEC-94).

Pure functions (stdlib ``statistics.NormalDist`` + numpy), no data access.  One place for
the arithmetic of DEC-94 (1)-(9) so that registration, feasibility rows and runs use the
same numbers (DEC-94 (8)); hand calculations are a cross-check, never the source.

Vocabulary (DEC-94 (1)):
  * ``z_krit(alpha)`` = Phi^-1(1 - alpha) is the CRITICAL VALUE that appears in a gate.
  * ``mde_factor(alpha, power)`` = z_krit + Phi^-1(power) is the MDE FACTOR (2.4865 for
    alpha 0.05, power 0.80); it never appears as a threshold.
  * All priors / estimates are signed in the REGISTERED direction (positive = expected).

Regime assignment (DEC-94 (2), (6), A-2, A-3):
  * ``assign_regime`` always uses alpha 0.05 per window; a stricter registered alpha is
    only checked INSIDE the assigned branch (``check_stricter_alpha``) and can never move a
    candidate from C10 into DEC52.
  * The DEC-52 gate power is the PRODUCT of the single powers (pooled condition and one
    screen per window) -- a conservative lower bound and the only assignment basis.  The
    exact probability (Monte Carlo, seeded) is report only.
  * ``assign_regime_a3_practice`` is the double statement of DEC-94 (9).

No import from ``wp13_xsec`` / ``wp7_universe`` (A3 code hash stays untouched).
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import NormalDist
from typing import Any, NamedTuple

import numpy as np

__all__ = [
    "ALPHA_WINDOW",
    "LABEL_ONLY_DEC94",
    "N_REP_MIN_REGISTERED",
    "POWER_TARGET",
    "REGIME_C10",
    "REGIME_DEC52",
    "REGIME_GL012",
    "SCREEN_FRACTION",
    "Z_KRIT_POOLED_DEC52",
    "Z_PER_WINDOW_A3_PRACTICE",
    "Z_POOLED_A3_PRACTICE",
    "Z_POWER",
    "StricterAlphaRejected",
    "VarianceFactor",
    "assign_regime",
    "assign_regime_a3_practice",
    "check_stricter_alpha",
    "condition_power",
    "dec52_gate_power",
    "effective_z",
    "mde80",
    "mde_factor",
    "selection_z",
    "stationary_bootstrap_means",
    "stationary_bootstrap_se",
    "variance_factor",
    "window_power",
    "z_krit",
]

_N = NormalDist()

#: DEC-51 (1): alpha per window, one-sided, in the registered direction.
ALPHA_WINDOW = 0.05
#: DEC-94 (1) / A-6: pooled critical value of the DEC-52 branch (alpha_p 0.0057) so that the
#: joint rate of the branch is the 0.5 % of PRD 3.5 (with 2.3263 it would be 0.85 %).
Z_KRIT_POOLED_DEC52 = 2.5287
#: DEC-51 (2): power target.
POWER_TARGET = 0.80
#: Phi^-1(0.80) = 0.8416 (DEC-94 (3)).
Z_POWER = _N.inv_cdf(POWER_TARGET)
#: DEC-52 (ii) / DEC-94 (6): screen per window = 0.5 x pooled threshold.
SCREEN_FRACTION = 0.5
#: A3 practice (gates.Z_PER_WINDOW, DEC-74 (d)): the MDE factor used as threshold.  Kept only
#: for the double statement of DEC-94 (9); never a threshold under P-1.
Z_PER_WINDOW_A3_PRACTICE = 2.4865
Z_POOLED_A3_PRACTICE = 3.1680
#: DEC-94 (4): minimum number of bootstrap replicates of a registered run.
N_REP_MIN_REGISTERED = 1000

REGIME_C10 = "C10"
REGIME_DEC52 = "DEC52"
REGIME_GL012 = "GL012"
LABEL_ONLY_DEC94 = "zugelassen nur durch DEC-94 (Lockerung)"

_EULER_GAMMA = 0.5772156649015329
_EPS = 1e-12            # tolerance for ">= 0.80" at the exact boundary (float noise only)
_SEED_EXACT_REPORT = 94


class StricterAlphaRejected(ValueError):
    """DEC-94 (2): a stricter registered alpha loses the power target inside its branch."""


class VarianceFactor(NamedTuple):
    """``c_hat`` = long-run / naive variance, ``c = max(1, c_hat)`` (DEC-94 (4))."""
    c_hat: float
    c: float


# ----------------------------------------------------------------------------
# validation helpers (C.14: loud fail)
# ----------------------------------------------------------------------------

def _finite(name: str, v: float) -> float:
    f = float(v)
    if not math.isfinite(f):
        raise ValueError(f"{name} must be finite, got {v!r}")
    return f


def _positive(name: str, v: float) -> float:
    f = _finite(name, v)
    if f <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}")
    return f


def _vec(name: str, xs: Sequence[float], *, positive: bool = False) -> list[float]:
    out = [(_positive if positive else _finite)(f"{name}[{i}]", v) for i, v in enumerate(xs)]
    if not out:
        raise ValueError(f"{name} must not be empty")
    return out


def _windows(priors: Sequence[float], ses: Sequence[float],
             sds: Sequence[float] | None) -> tuple[list[float], list[float], list[float]]:
    pr = _vec("priors", priors)
    se = _vec("ses", ses, positive=True)
    sd = se if sds is None else _vec("sds", sds, positive=True)
    if not (len(pr) == len(se) == len(sd)):
        raise ValueError(f"priors/ses/sds length mismatch: {len(pr)}/{len(se)}/{len(sd)}")
    return pr, se, list(sd)


# ----------------------------------------------------------------------------
# (1) critical value, MDE factor, constants
# ----------------------------------------------------------------------------

def z_krit(alpha: float) -> float:
    """DEC-94 (1): critical value Phi^-1(1 - alpha), one-sided."""
    a = _finite("alpha", alpha)
    if not 0.0 < a < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha!r}")
    return _N.inv_cdf(1.0 - a)


def mde_factor(alpha: float, power: float = POWER_TARGET) -> float:
    """DEC-94 (1): MDE factor = z_krit(alpha) + Phi^-1(power) (2.4865 for 0.05 / 0.80)."""
    p = _finite("power", power)
    if not 0.0 < p < 1.0:
        raise ValueError(f"power must be in (0, 1), got {power!r}")
    return z_krit(alpha) + _N.inv_cdf(p)


# ----------------------------------------------------------------------------
# (2) condition power, window power, MDE80  (DEC-94 (3): one SE for test and power)
# ----------------------------------------------------------------------------

def condition_power(prior: float, threshold: float, sd: float) -> float:
    """DEC-94 (3): P = Phi((prior - T) / SD) for one condition ``statistic >= T``."""
    return _N.cdf((_finite("prior", prior) - _finite("threshold", threshold))
                  / _positive("sd", sd))


def window_power(prior: float, se: float, z_krit: float, sd: float | None = None) -> float:
    """DEC-94 (3): window power with T = z_krit * SE; ``sd`` defaults to ``se``
    (then P = Phi(prior / SE - z_krit))."""
    se_ = _positive("se", se)
    return condition_power(prior, _finite("z_krit", z_krit) * se_,
                           se_ if sd is None else sd)


def mde80(se: float, z_krit: float, sd: float | None = None) -> float:
    """DEC-94 (3): MDE80 = z_krit * SE + 0.8416 * SD (``sd`` defaults to ``se``)."""
    se_ = _positive("se", se)
    sd_ = se_ if sd is None else _positive("sd", sd)
    return _finite("z_krit", z_krit) * se_ + Z_POWER * sd_


# ----------------------------------------------------------------------------
# (3) DEC-52 gate power (pooled condition x one screen per window)
# ----------------------------------------------------------------------------

def _gate_exact(priors: list[float], sds: list[float], t_pooled: float, t_screen: float,
                n_draws: int, seed: int) -> tuple[float, float]:
    """P(mean(x) >= t_pooled and x_w >= t_screen for all w), x_w ~ N(prior_w, sd_w^2)
    independent.  Seeded Monte Carlo in chunks; report only (DEC-94 (6), A-3)."""
    rng = np.random.default_rng(seed)
    mu = np.asarray(priors, dtype=np.float64)
    sd = np.asarray(sds, dtype=np.float64)
    hits = 0
    done = 0
    chunk = 250_000
    while done < n_draws:
        m = min(chunk, n_draws - done)
        x = mu + sd * rng.standard_normal((m, mu.size))
        ok = (x.mean(axis=1) >= t_pooled) & np.all(x >= t_screen, axis=1)
        hits += int(ok.sum())
        done += m
    p = hits / n_draws
    return p, math.sqrt(max(p * (1.0 - p), 0.0) / n_draws)


def dec52_gate_power(priors: Sequence[float], ses: Sequence[float],
                     z_krit_pooled: float = Z_KRIT_POOLED_DEC52, *,
                     sds: Sequence[float] | None = None, exact: bool = False,
                     n_draws: int = 2_000_000, seed: int = _SEED_EXACT_REPORT) -> dict[str, Any]:
    """DEC-94 (6) / A-3: power of the full DEC-52 gate.

    Pooled mean equally weighted over the windows, ``SE_pooled = sqrt(sum SE_w^2) / n``;
    pooled condition ``mean >= z_krit_pooled * SE_pooled``; screen per window
    ``x_w >= 0.5 * z_krit_pooled * SE_pooled``.  ``power_product`` (pooled x screens) is
    BINDING for the assignment; ``power_exact`` (seeded Monte Carlo, only if ``exact``) is
    report only.  ``sds`` = SD of the tested statistics (default ``ses``).
    """
    pr, se, sd = _windows(priors, ses, sds)
    n = len(pr)
    if n < 2:
        raise ValueError("DEC-52 gate needs at least two windows")
    zp = _positive("z_krit_pooled", z_krit_pooled)
    se_p = math.sqrt(sum(s * s for s in se)) / n
    sd_p = math.sqrt(sum(s * s for s in sd)) / n
    prior_p = sum(pr) / n
    t_pooled = zp * se_p
    t_screen = SCREEN_FRACTION * t_pooled
    p_pooled = condition_power(prior_p, t_pooled, sd_p)
    p_screens = [condition_power(pi, t_screen, si) for pi, si in zip(pr, sd)]
    product = p_pooled
    for q in p_screens:
        product *= q
    mde_pooled = t_pooled + Z_POWER * sd_p
    mde_screens = [t_screen + Z_POWER * si for si in sd]
    out: dict[str, Any] = {
        "n_windows": n, "z_krit_pooled": zp, "prior_pooled": prior_p, "se_pooled": se_p,
        "threshold_pooled": t_pooled, "threshold_screen": t_screen,
        "power_pooled": p_pooled, "power_screens": p_screens, "power_product": product,
        "mde80_pooled": mde_pooled, "mde80_screens": mde_screens,
        "mde80_gate": max([mde_pooled, *mde_screens]),
        "power_exact": None, "power_exact_mc_se": None,
    }
    if exact:
        p_ex, se_mc = _gate_exact(pr, sd, t_pooled, t_screen, int(n_draws), int(seed))
        out["power_exact"], out["power_exact_mc_se"] = p_ex, se_mc
    return out


# ----------------------------------------------------------------------------
# (4) regime assignment (DEC-94 (2), (6), A-2, A-3)
# ----------------------------------------------------------------------------

def _fmt(xs: Sequence[float]) -> str:
    return "[" + ", ".join(f"{v:.3f}" for v in xs) + "]"


def assign_regime(priors: Sequence[float], ses: Sequence[float], *,
                  alpha: float = ALPHA_WINDOW, z_krit_pooled: float = Z_KRIT_POOLED_DEC52,
                  sds: Sequence[float] | None = None, exact_report: bool = False) -> dict[str, Any]:
    """DEC-94 (6): regime of a design from priors and SEs per judged window.

    All window powers >= 0.80 -> ``C10``; else ``DEC52`` if the DEC-52 gate power (PRODUCT
    of the single powers, A-3) >= 0.80; else ``GL012``.  The assignment is ALWAYS made at
    alpha 0.05 (A-2): any other ``alpha`` is rejected loudly -- a stricter registered alpha
    is checked afterwards inside the branch with ``check_stricter_alpha``.  Fewer than two
    windows cannot form a DEC-52 gate (-> ``GL012`` instead of ``C10`` when power is short).
    """
    if abs(_finite("alpha", alpha) - ALPHA_WINDOW) > 1e-12:
        raise ValueError(
            f"DEC-94 (2)/A-2: regime assignment is always made at alpha={ALPHA_WINDOW}, "
            f"got {alpha!r}; check a stricter registered alpha with check_stricter_alpha()")
    pr, se, sd = _windows(priors, ses, sds)
    n = len(pr)
    z = z_krit(ALPHA_WINDOW)
    wpow = [window_power(p, s, z, d) for p, s, d in zip(pr, se, sd)]
    wmde = [mde80(s, z, d) for s, d in zip(se, sd)]
    gate = (dec52_gate_power(pr, se, z_krit_pooled, sds=sd, exact=exact_report)
            if n >= 2 else None)
    pmin = min(wpow)
    weakest = wpow.index(pmin)
    if pmin >= POWER_TARGET - _EPS:
        regime = REGIME_C10
        reason = (f"C10: every window power >= {POWER_TARGET:.2f} at alpha {ALPHA_WINDOW} "
                  f"(powers {_fmt(wpow)})")
    elif gate is not None and gate["power_product"] >= POWER_TARGET - _EPS:
        regime = REGIME_DEC52
        reason = (f"DEC52: window {weakest} power {pmin:.3f} < {POWER_TARGET:.2f}; DEC-52 gate "
                  f"power (product) {gate['power_product']:.3f} >= {POWER_TARGET:.2f}")
    else:
        regime = REGIME_GL012
        tail = ("DEC-52 needs >= 2 windows" if gate is None else
                f"DEC-52 gate power (product) {gate['power_product']:.3f} < {POWER_TARGET:.2f}")
        reason = (f"GL012: window {weakest} power {pmin:.3f} < {POWER_TARGET:.2f}; {tail}")
    return {
        "regime": regime, "reason": reason, "alpha": ALPHA_WINDOW, "z_krit": z,
        "mde_factor": mde_factor(ALPHA_WINDOW), "power_target": POWER_TARGET,
        "priors": pr, "ses": se, "sds": sd, "window_power": wpow, "window_power_min": pmin,
        "window_power_joint_product": math.prod(wpow), "mde80": wmde, "gate": gate,
        "gate_power_product": None if gate is None else gate["power_product"],
        "gate_power_exact": None if gate is None else gate["power_exact"],
    }


def check_stricter_alpha(priors: Sequence[float], ses: Sequence[float], regime: str,
                         alpha_registered: float, *,
                         z_krit_pooled_registered: float | None = None,
                         sds: Sequence[float] | None = None) -> dict[str, Any]:
    """DEC-94 (2) / A-2: power >= 0.80 of the ASSIGNED branch at a stricter registered alpha.

    ``regime`` is the result of ``assign_regime`` (made at alpha 0.05).  C10: every window
    power at ``z_krit(alpha_registered)``.  DEC52: the stricter alpha acts through the pooled
    critical value, which the registration must state as a number
    (``z_krit_pooled_registered``, DEC-94 (2): "alpha, z_krit as numbers").  Raises
    ``StricterAlphaRejected`` if the power target is lost; ``ValueError`` for a looser alpha
    or a regime without a branch (GL012).
    """
    if regime not in (REGIME_C10, REGIME_DEC52):
        raise ValueError(f"no branch to check for regime {regime!r}")
    a = _finite("alpha_registered", alpha_registered)
    if not 0.0 < a <= ALPHA_WINDOW:
        raise ValueError(f"alpha_registered must be in (0, {ALPHA_WINDOW}] (stricter or equal), "
                         f"got {alpha_registered!r}")
    pr, se, sd = _windows(priors, ses, sds)
    z = z_krit(a)
    if regime == REGIME_C10:
        wpow = [window_power(p, s, z, d) for p, s, d in zip(pr, se, sd)]
        power = min(wpow)
        detail: dict[str, Any] = {"window_power": wpow}
        what = f"min window power {power:.3f} at z_krit {z:.4f}"
    else:
        if z_krit_pooled_registered is None:
            raise ValueError("DEC52 branch: pass the registered pooled critical value "
                             "(z_krit_pooled_registered)")
        zp = _positive("z_krit_pooled_registered", z_krit_pooled_registered)
        if zp < Z_KRIT_POOLED_DEC52 - 1e-12:
            raise ValueError(f"z_krit_pooled_registered {zp} is looser than the default "
                             f"{Z_KRIT_POOLED_DEC52}")
        gate = dec52_gate_power(pr, se, zp, sds=sd)
        power = gate["power_product"]
        detail = {"gate": gate}
        what = f"DEC-52 gate power (product) {power:.3f} at pooled z_krit {zp:.4f}"
    if power < POWER_TARGET - _EPS:
        raise StricterAlphaRejected(
            f"DEC-94 (2): alpha_registered {a} in branch {regime}: {what} < {POWER_TARGET:.2f}")
    return {"ok": True, "regime": regime, "alpha_registered": a, "z_krit": z,
            "power": power, "reason": f"{regime} keeps power at alpha {a}: {what}", **detail}


# ----------------------------------------------------------------------------
# (5) double statement under the A3 practice (DEC-94 (9))
# ----------------------------------------------------------------------------

def assign_regime_a3_practice(priors: Sequence[float], ses: Sequence[float],
                              sds: Sequence[float] | None = None, *,
                              allow_dec52: bool = False,
                              exact_report: bool = False) -> dict[str, Any]:
    """DEC-94 (9): the same design under the A3 practice (threshold factor 2.4865 per window,
    DEC-87 (F), product calculation), plus the P-1 result for comparison.

    Window power ``Phi((prior - 2.4865 * SE) / SD)``; all >= 0.80 -> ``C10``; otherwise
    ``GL012`` (DEC-87 (F): MDE80 = (2.4865 + 0.8416) SE above the prior in a window; the
    DEC-52 branch was not built for A3).  ``allow_dec52=True`` additionally admits the DEC-52
    gate at the old pooled factor 3.1680 (product).  The DEC-52 gate at that factor is always
    reported (``gate_a3``).  ``zugelassen_nur_durch_dec94`` is True when P-1 admits the design
    (C10/DEC52) and the A3 practice does not (label for registry and GL entry).
    """
    pr, se, sd = _windows(priors, ses, sds)
    n = len(pr)
    wpow = [window_power(p, s, Z_PER_WINDOW_A3_PRACTICE, d) for p, s, d in zip(pr, se, sd)]
    wmde = [mde80(s, Z_PER_WINDOW_A3_PRACTICE, d) for s, d in zip(se, sd)]
    gate = (dec52_gate_power(pr, se, Z_POOLED_A3_PRACTICE, sds=sd, exact=exact_report)
            if n >= 2 else None)
    pmin = min(wpow)
    weakest = wpow.index(pmin)
    if pmin >= POWER_TARGET - _EPS:
        regime = REGIME_C10
        reason = (f"A3 practice C10: every window power >= {POWER_TARGET:.2f} at threshold "
                  f"factor {Z_PER_WINDOW_A3_PRACTICE} (powers {_fmt(wpow)})")
    elif allow_dec52 and gate is not None and gate["power_product"] >= POWER_TARGET - _EPS:
        regime = REGIME_DEC52
        reason = (f"A3 practice DEC52: window {weakest} power {pmin:.3f} < {POWER_TARGET:.2f}; "
                  f"gate power (product, pooled factor {Z_POOLED_A3_PRACTICE}) "
                  f"{gate['power_product']:.3f}")
    else:
        regime = REGIME_GL012
        reason = (f"A3 practice GL012 (DEC-87 (F)): window {weakest} power {pmin:.3f} < "
                  f"{POWER_TARGET:.2f}, MDE80 {_fmt(wmde)} vs priors {_fmt(pr)}")
    p1 = assign_regime(pr, se, sds=sd, exact_report=exact_report)
    only = p1["regime"] != REGIME_GL012 and regime == REGIME_GL012
    return {
        "regime": regime, "reason": reason, "practice": "A3",
        "threshold_factor": Z_PER_WINDOW_A3_PRACTICE, "pooled_factor": Z_POOLED_A3_PRACTICE,
        "power_target": POWER_TARGET, "priors": pr, "ses": se, "sds": sd,
        "window_power": wpow, "window_power_min": pmin,
        "window_power_joint_product": math.prod(wpow), "mde80": wmde, "gate_a3": gate,
        "gate_power_product": None if gate is None else gate["power_product"],
        "p1": p1, "p1_regime": p1["regime"],
        "zugelassen_nur_durch_dec94": only,
        "label": LABEL_ONLY_DEC94 if only else None,
    }


# ----------------------------------------------------------------------------
# (6) autocorrelation of the test statistic (DEC-94 (4))
# ----------------------------------------------------------------------------

def _series(x: Sequence[float] | np.ndarray) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64)
    if a.ndim != 1:
        raise ValueError("x must be one-dimensional")
    if not np.all(np.isfinite(a)):
        raise ValueError("x must be finite")
    return a


def variance_factor(x: Sequence[float] | np.ndarray, mean_block: int = 4) -> VarianceFactor:
    """DEC-94 (4): ``c_hat`` = long-run variance / naive variance of the SAME statistic with
    a Bartlett kernel over ``mean_block`` lags (weights ``1 - k/(B+1)``, Newey-West), and
    ``c = max(1, c_hat)`` (no credit for negative autocorrelation).  ``c`` is a VARIANCE
    factor; the SD factor is ``sqrt(c)``.  Note the truncation bias: a short bandwidth
    understates strong persistence (AR(1) rho 0.5: 2.2 at B=4 against the true 3)."""
    b = int(mean_block)
    if b != mean_block or b < 1:
        raise ValueError(f"mean_block must be an integer >= 1, got {mean_block!r}")
    a = _series(x)
    n = a.size
    if n < b + 2:
        raise ValueError(f"series too short for bandwidth {b}: n={n}")
    d = a - a.mean()
    g0 = float(d @ d) / n
    if g0 <= 0.0:
        raise ValueError("constant series: variance factor undefined")
    lrv = g0
    for k in range(1, b + 1):
        lrv += 2.0 * (1.0 - k / (b + 1.0)) * float(d[k:] @ d[:-k]) / n
    c_hat = lrv / g0
    return VarianceFactor(c_hat=c_hat, c=max(1.0, c_hat))


def stationary_bootstrap_means(x: Sequence[float] | np.ndarray, mean_block: float = 4.0,
                               n_rep: int = N_REP_MIN_REGISTERED, *, seed: int) -> np.ndarray:
    """DEC-94 (4) / DEC-53: replicate means of the stationary bootstrap (Politis/Romano):
    geometric block lengths with mean ``mean_block``, circular wrap-around, series length
    ``n`` per replicate.  Deterministic for a given ``seed`` (numpy PCG64)."""
    mb = _finite("mean_block", mean_block)
    if mb < 1.0:
        raise ValueError(f"mean_block must be >= 1, got {mean_block!r}")
    if int(n_rep) < 2:
        raise ValueError("n_rep must be >= 2")
    a = _series(x)
    n = a.size
    if n < 2:
        raise ValueError("series too short")
    p = 1.0 / mb
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    means = np.empty(int(n_rep), dtype=np.float64)
    for r in range(int(n_rep)):
        starts = rng.integers(0, n, size=n)
        jump = rng.random(n) < p
        jump[0] = True
        first = np.maximum.accumulate(np.where(jump, t, 0))   # start position of the block
        idx = (starts[first] + (t - first)) % n
        means[r] = a[idx].mean()
    return means


def stationary_bootstrap_se(x: Sequence[float] | np.ndarray, mean_block: float = 4.0,
                            n_rep: int = N_REP_MIN_REGISTERED, *, seed: int) -> float:
    """DEC-94 (4): SE of the mean = SD (ddof 1) of the stationary-bootstrap replicate means.
    A registered run uses ``n_rep >= N_REP_MIN_REGISTERED`` and a registered seed."""
    return float(np.std(stationary_bootstrap_means(x, mean_block, n_rep, seed=seed), ddof=1))


# ----------------------------------------------------------------------------
# (7) selection ceiling (DEC-94 (7))
# ----------------------------------------------------------------------------

def selection_z(K: int) -> float:
    """Bailey / Lopez de Prado expected maximum of K standard normals:
    ``(1 - g) * Phi^-1(1 - 1/K) + g * Phi^-1(1 - 1/(K e))``, g = Euler-Mascheroni.
    ``K = 1`` has no selection (the formula diverges) and returns 0.0."""
    k = int(K)
    if k != K or k < 1:
        raise ValueError(f"K must be an integer >= 1, got {K!r}")
    if k == 1:
        return 0.0
    return ((1.0 - _EULER_GAMMA) * _N.inv_cdf(1.0 - 1.0 / k)
            + _EULER_GAMMA * _N.inv_cdf(1.0 - 1.0 / (k * math.e)))


def effective_z(alpha: float, K: int) -> float:
    """DEC-94 (7): z of the power line = max(z_krit(alpha), selection_z(K))."""
    return max(z_krit(alpha), selection_z(K))
