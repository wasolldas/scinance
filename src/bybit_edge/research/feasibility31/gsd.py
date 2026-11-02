"""Group-sequential O'Brien-Fleming designs on the Brownian-motion (B) scale.

Own implementation (numpy/scipy only, no data, no network).  Two engines:

* ``grid_*``: exact density propagation on a fixed grid (deterministic, no random numbers).  Used for the plain
  design without a recency screen.  Efficacy is ``B(t_k) >= C`` (constant boundary on the B scale = O'Brien-Fleming),
  optional non-binding futility ``B(t_k) < 0`` at looks 1..K-1 (the efficacy constant is calibrated without it).
* ``mc_*``: Monte Carlo with a fixed seed and common random numbers over an ``N_SUB``-step Brownian bank.  Used for
  the design with the recency screen, because the screen reads the increment over the youngest ``r`` information
  fraction, which makes the decision path dependent.

Conventions (DEC-104 E4 (e), OC derivation of 2026-11-02): ``K`` equally spaced looks in information, final look at
``t = 1``; the drift ``theta`` is the mean of the final-look Z statistic; ``R`` (maximum information relative to the
fixed-sample test of the same alpha and power) is ``(theta / (z_alpha + z_power))^2``; the expected information under
H1 is ``R * E[t_stop]``.  The recency screen is applied at every efficacy stop and reads the youngest ``r`` of the
MAXIMUM information (or all data seen so far, if less than ``r`` has accrued).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy import optimize, signal
from scipy.stats import norm

__all__ = [
    "GRID_STEP", "N_SUB", "R_NODES", "GsdDesign", "obf_constant", "grid_oc", "grid_design", "mc_design",
    "mc_pass_probability", "screen_design_at_r",
]

#: grid step of the exact engine (B scale)
GRID_STEP = 0.0025
#: sub-steps of the Monte Carlo Brownian bank; looks must divide it (K in 1, 2, 3, 4, 6, 8, 12, 24)
N_SUB = 24
#: information shares r of the youngest window for which the screened design is computed; others are interpolated
R_NODES = (1.0 / 12.0, 1.0 / 8.0, 1.0 / 6.0, 1.0 / 4.0, 1.0 / 3.0, 1.0 / 2.0, 2.0 / 3.0, 3.0 / 4.0, 1.0)
#: fixed seed of the screened design bank (documented, never drawn from the clock)
SEED_BANK = 31002


@dataclass(frozen=True)
class GsdDesign:
    """Result of a design calculation (all information quantities relative to the fixed test, same alpha/power)."""

    looks: int
    alpha: float
    target_power: float
    futility: bool
    screen_alpha: float | None
    screen_r: float | None
    engine: str                    # "grid" | "mc"
    c_b: float                     # efficacy constant on the B scale
    z_bounds: tuple[float, ...]    # nominal z boundary per look = c_b / sqrt(t_k)
    theta: float                   # final-look drift giving the target power
    r_max: float                   # maximum information / fixed information
    alpha_eff: float               # P(PASS | effect 0) of the whole rule (incl. screen, futility)
    en_h1: float                   # expected information at the design effect / fixed information
    en_h0: float                   # expected information at effect 0 / fixed information
    n_paths: int | None

    def as_dict(self) -> dict:
        return {
            "looks": self.looks, "alpha": self.alpha, "target_power": self.target_power, "futility": self.futility,
            "screen_alpha": self.screen_alpha, "screen_r": self.screen_r, "engine": self.engine, "c_b": self.c_b,
            "z_bounds": list(self.z_bounds), "theta": self.theta, "r_max": self.r_max, "alpha_eff": self.alpha_eff,
            "en_h1": self.en_h1, "en_h0": self.en_h0, "n_paths": self.n_paths,
        }


# ------------------------------------------------------------------------------------------------------------------
# exact grid engine
# ------------------------------------------------------------------------------------------------------------------
def grid_oc(c_b: float, theta: float, looks: int, futility: bool = False, step: float = GRID_STEP) -> tuple[float, float]:
    """Return ``(P(PASS), E[t_stop])`` for the efficacy constant ``c_b`` at final-look drift ``theta``.

    Density propagation of ``B(t_k) = W(t_k) + theta t_k`` between looks; mass on the boundary cell is split
    linearly so that the result is a smooth function of ``c_b``.
    """
    if looks < 1:
        raise ValueError("looks must be >= 1")
    dt = 1.0 / looks
    sd = math.sqrt(dt)
    lo = -10.0
    hi = 10.0 + max(theta, 0.0)
    n = int(round((hi - lo) / step)) + 1
    grid = lo + step * np.arange(n)
    m = int(math.ceil(8.0 * sd / step))
    kern = norm.pdf(step * np.arange(-m, m + 1), loc=theta * dt, scale=sd) * step
    p_rej = 0.0
    e_t = 0.0
    dens = None
    for i in range(looks):
        if i == 0:
            d = norm.pdf(grid, loc=theta * dt, scale=sd)
        else:
            d = np.maximum(signal.fftconvolve(dens, kern, mode="same"), 0.0)
        w_rej = np.clip((grid - c_b) / step + 0.5, 0.0, 1.0)
        rej_mass = float(np.sum(d * w_rej) * step)
        p_rej += rej_mass
        if i < looks - 1:
            if futility:
                w_fut = np.clip(0.5 - grid / step, 0.0, 1.0) * (1.0 - w_rej)
            else:
                w_fut = np.zeros_like(grid)
            stop_mass = rej_mass + float(np.sum(d * w_fut) * step)
            e_t += (i + 1) * dt * stop_mass
            dens = d * (1.0 - w_rej - w_fut)
        else:
            e_t += 1.0 * float(np.sum(d) * step)
    return p_rej, e_t


@lru_cache(maxsize=None)
def obf_constant(alpha: float, looks: int, step: float = GRID_STEP) -> float:
    """O'Brien-Fleming constant on the B scale: P_0(any B(t_k) >= C) = alpha (efficacy only)."""
    return float(optimize.brentq(lambda c: grid_oc(c, 0.0, looks, False, step)[0] - alpha, 1.0, 7.0, xtol=1e-10))


@lru_cache(maxsize=None)
def grid_design(alpha: float, looks: int, target_power: float = 0.80, futility: bool = False) -> GsdDesign:
    """Plain O'Brien-Fleming design (no screen), deterministic."""
    c_b = obf_constant(alpha, looks)
    th_fix = float(norm.isf(alpha) + norm.ppf(target_power))
    th = float(optimize.brentq(lambda t: grid_oc(c_b, t, looks, futility)[0] - target_power,
                               0.8 * th_fix, 2.0 * th_fix, xtol=1e-9))
    r_max = (th / th_fix) ** 2
    _, e1 = grid_oc(c_b, th, looks, futility)
    a0, e0 = grid_oc(c_b, 0.0, looks, futility)
    zb = tuple(c_b / math.sqrt((k + 1) / looks) for k in range(looks))
    return GsdDesign(looks, alpha, target_power, futility, None, None, "grid", c_b, zb, th, r_max, a0,
                     r_max * e1, r_max * e0, None)


# ------------------------------------------------------------------------------------------------------------------
# Monte Carlo engine (recency screen at every efficacy stop)
# ------------------------------------------------------------------------------------------------------------------
class _Bank:
    """Brownian bank: ``W`` on ``N_SUB`` equal sub-steps, drawn once from a fixed seed (common random numbers)."""

    def __init__(self, n_paths: int, seed: int):
        rng = np.random.default_rng(seed)
        inc = rng.standard_normal((n_paths, N_SUB)) * math.sqrt(1.0 / N_SUB)
        self.w = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(inc, axis=1)], axis=1)
        self.n = n_paths

    def run(self, theta: float, c_b: float, looks: int, r: float | None, z_screen: float | None,
            futility: bool) -> tuple[float, float]:
        """Return ``(P(PASS), E[t_stop])``; the screen needs ``r`` and ``z_screen``."""
        if N_SUB % looks:
            raise ValueError(f"looks={looks} must divide N_SUB={N_SUB}")
        step = N_SUB // looks
        r_sub = None
        if r is not None:
            r_sub = int(round(r * N_SUB))
            if r_sub < 1 or abs(r_sub - r * N_SUB) > 1e-6:
                raise ValueError("r must be a multiple of 1/N_SUB")
        n = self.n
        stop = np.zeros(n, dtype=bool)
        passed = np.zeros(n, dtype=bool)
        t_stop = np.ones(n)

        def b_at(j: int) -> np.ndarray:
            return self.w[:, j] + theta * (j / N_SUB)

        for k in range(1, looks + 1):
            j = k * step
            tk = j / N_SUB
            bj = b_at(j)
            eff = bj >= c_b
            if z_screen is not None and r_sub is not None:
                jr = j - r_sub
                if jr >= 0:
                    zrec = (bj - b_at(jr)) / math.sqrt(r_sub / N_SUB)
                else:
                    zrec = bj / math.sqrt(tk)
                eff = eff & (zrec > z_screen)
            if k < looks:
                fut = (bj < 0.0) if futility else np.zeros(n, dtype=bool)
                new_pass = ~stop & eff
                new_stop = ~stop & (eff | fut)
            else:
                new_pass = ~stop & eff
                new_stop = ~stop
            passed |= new_pass
            t_stop[new_stop] = tk
            stop |= new_stop
        return float(passed.mean()), float(t_stop.mean())


@lru_cache(maxsize=3)
def _bank(n_paths: int, seed: int) -> _Bank:
    return _Bank(n_paths, seed)


def mc_pass_probability(design: GsdDesign, theta: float, n_paths: int, seed: int = SEED_BANK) -> tuple[float, float]:
    """P(PASS) and E[t_stop] of an already built MC design at drift ``theta`` (same bank as the design)."""
    z_s = None if design.screen_alpha is None else float(norm.isf(design.screen_alpha))
    return _bank(n_paths, seed).run(theta, design.c_b, design.looks, design.screen_r, z_s, design.futility)


@lru_cache(maxsize=None)
def mc_design(alpha: float, looks: int, target_power: float, screen_alpha: float, r: float, futility: bool,
              n_paths: int, seed: int = SEED_BANK) -> GsdDesign:
    """O'Brien-Fleming design with the recency screen at every efficacy stop, by Monte Carlo (fixed seed)."""
    if n_paths < 1000:
        raise ValueError("n_paths must be >= 1000")
    bank = _bank(n_paths, seed)
    c_b = obf_constant(alpha, looks)
    z_s = float(norm.isf(screen_alpha))
    th_fix = float(norm.isf(alpha) + norm.ppf(target_power))

    def gap(t: float) -> float:
        return bank.run(t, c_b, looks, r, z_s, futility)[0] - target_power

    lo, hi = 0.9 * th_fix, 3.0 * th_fix
    if gap(hi) < 0:
        raise ValueError("target power not reachable inside the search bracket (screen too strict)")
    th = float(optimize.brentq(gap, lo, hi, xtol=2e-4))
    r_max = (th / th_fix) ** 2
    _, e1 = bank.run(th, c_b, looks, r, z_s, futility)
    a0, e0 = bank.run(0.0, c_b, looks, r, z_s, futility)
    zb = tuple(c_b / math.sqrt((k + 1) / looks) for k in range(looks))
    return GsdDesign(looks, alpha, target_power, futility, screen_alpha, r, "mc", c_b, zb, th, r_max, a0,
                     r_max * e1, r_max * e0, n_paths)


def screen_design_at_r(alpha: float, looks: int, target_power: float, screen_alpha: float, r: float, futility: bool,
                       n_paths: int, seed: int = SEED_BANK) -> GsdDesign:
    """Screened design for an arbitrary ``r`` in (0, 1]: exact nodes, linear interpolation in ``r`` between them.

    ``r`` below the smallest node uses that node (documented approximation; the floor of the screen dominates there).
    """
    r = float(min(max(r, R_NODES[0]), 1.0))
    for node in R_NODES:
        if abs(r - node) < 1e-9:
            return mc_design(alpha, looks, target_power, screen_alpha, node, futility, n_paths, seed)
    lo = max(x for x in R_NODES if x < r)
    hi = min(x for x in R_NODES if x > r)
    a = mc_design(alpha, looks, target_power, screen_alpha, lo, futility, n_paths, seed)
    b = mc_design(alpha, looks, target_power, screen_alpha, hi, futility, n_paths, seed)
    w = (r - lo) / (hi - lo)

    def mix(x: float, y: float) -> float:
        return (1.0 - w) * x + w * y

    return GsdDesign(looks, alpha, target_power, futility, screen_alpha, r, "mc", a.c_b, a.z_bounds,
                     mix(a.theta, b.theta), mix(a.r_max, b.r_max), mix(a.alpha_eff, b.alpha_eff),
                     mix(a.en_h1, b.en_h1), mix(a.en_h0, b.en_h0), n_paths)
