"""Decision-rule menu of the feasibility calculator (Constitution 3.1, DEC-104 E2/E6, OC derivation 2026-11-02).

Since DEC-107 (2026-11-04) the decided rule for 3.1 registrations is ``R5`` (variant (c)); the other rules stay in the
menu for the side-by-side report (DEC-104 E5 design menu, OC comparisons):

* ``R1``  C.10 per window: two windows, one-sided 0.05 each, power 0.80 per window (joint 0.64 at the MDE).
* ``R2``  C.10 joint: same decision, power 0.80 for the JOINT decision (per window sqrt(0.80)).
* ``R3``  pooled one-sided 0.0025 over all confirmation data, no screen.
* ``R4``  pooled 0.0025 plus RECENCY screen on the youngest 12-month window at alpha_s (0.05 / 0.10 / 0.20 / 0.50);
          correlation pooled/screen is ``sqrt(r)`` with ``r`` the data share of the youngest window; joint power 0.80;
          structural FLOOR ``(z_s + Phi^-1(0.8 / g)) SE_12``.
* ``R5``  DECIDED (DEC-107 (1), user 2026-11-04; derivation DEC-104 N4): pooled 0.0025 plus the registered STABILITY
          test "youngest part does not drop" (Welch-t, one-sided 0.05, independent of the pooled mean at equal
          variances); joint power 0.80, hence pooled power 0.80/q with the cost ratio q = 1 - alpha_stab = 0.95; the
          test is VOID with at most 12 months of confirmation data (q = 1 there); no floor.
* ``R6``  group-sequential O'Brien-Fleming, K looks, alpha 0.0025, power 0.80, with and without screen.

Units: every ``d`` is an effect in units of ``SE_12`` (the standard error of one 12-month confirmation window,
``c`` already inside); ``T`` is the amount of confirmation data in months; ``SE(T) = SE_12 sqrt(12 / T)``.  ``gate``
(``g`` in (0, 1]) multiplies the power of every decision (extra pass condition independent of the effect, e.g. the
Gate-(4) factor 0.9025 of the A2 chain).  Pure functions and small classes; no data, no network.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import optimize
from scipy.stats import multivariate_normal, nct, norm, t as student_t

from . import gsd

__all__ = [
    "ALPHA_POOL", "ALPHA_WINDOW", "C80", "MU_FIX", "POWER", "T_CAP_MONTHS", "Z_POOL", "Z_POWER", "Z_WINDOW",
    "Rule", "C10Windows", "Pooled", "PooledScreen", "PooledStability", "GroupSequential", "build_menu",
    "screen_pass_probability", "target_quantile", "data_factor", "sr_eff_needed_c10", "simulate_rule", "ppv", "t_mde_factor",
    "MIN_CLUSTERS_FIRST_LOOK",
]

ALPHA_WINDOW = 0.05          # DEC-51 (1): one window, one-sided
ALPHA_POOL = 0.0025          # DEC-104 E2: pooled test, fixed per test
POWER = 0.80                 # DEC-51 (2) / DEC-104 E2
Z_WINDOW = float(norm.isf(ALPHA_WINDOW))      # 1.6449
Z_POOL = float(norm.isf(ALPHA_POOL))          # 2.8070
Z_POWER = float(norm.ppf(POWER))              # 0.8416
C80 = Z_WINDOW + Z_POWER                      # 2.4865 MDE factor, one window 0.05 / 0.80
MU_FIX = Z_POOL + Z_POWER                     # 3.6487 MDE factor, pooled 0.0025 / 0.80
T_CAP_MONTHS = 12000.0                        # search cap for required data (1000 years: "never" beyond)
_MONTHS = 12.0
#: OC derivation (e): a first group-sequential look with t boundaries is practically worthless below ~26 clusters
MIN_CLUSTERS_FIRST_LOOK = 26


def _capped(t: float) -> float:
    """Required data beyond the search cap counts as "never" (``inf``), consistently for closed forms and root finding."""
    return t if t <= T_CAP_MONTHS else math.inf


def target_quantile(power_target: float, gate: float = 1.0) -> float:
    """``Phi^-1(power_target / gate)``; ``+inf`` if the gate makes the target unreachable (target/gate >= 1)."""
    q = power_target / gate
    if q >= 1.0:
        return math.inf
    return float(norm.ppf(q))


def screen_pass_probability(d: float, r: float, z_screen: float, z_pool: float = Z_POOL) -> float:
    """P(Z_pool > z_pool and Z_rec > z_screen) at effect ``d`` (SE_12 units), youngest-window data share ``r``.

    ``Z_rec ~ N(d, 1)``, ``Z_pool ~ N(d / sqrt(r), 1)``, correlation ``sqrt(r)``.  Exact bivariate normal orthant
    probability through ``scipy.stats.multivariate_normal`` (quadrature, deterministic in 2 dimensions).
    """
    if not 0.0 < r <= 1.0:
        raise ValueError("r must be in (0, 1]")
    rho = math.sqrt(r)
    a = d / rho - z_pool
    b = d - z_screen
    if rho >= 1.0 - 1e-12:
        return float(norm.cdf(min(a, b)))
    return float(multivariate_normal.cdf([a, b], mean=[0.0, 0.0], cov=[[1.0, rho], [rho, 1.0]]))


class Rule:
    """Common interface.  Subclasses implement ``alpha_eff``, ``power``, ``mde80`` (+ ``floor``, ``t_required``)."""

    key = ""
    label = ""
    #: True for rules whose decision uses two separate windows (C.10)
    two_windows = False

    def alpha_eff(self, t: float, gate: float = 1.0) -> float:
        return self.power(0.0, t, gate)

    def power(self, d: float, t: float, gate: float = 1.0) -> float:  # pragma: no cover - interface
        raise NotImplementedError

    def mde80(self, t: float, gate: float = 1.0) -> float:  # pragma: no cover - interface
        raise NotImplementedError

    def floor(self, gate: float = 1.0) -> float:
        """Smallest effect (SE_12 units) the rule can ever reach with power 0.80 as data grows without bound."""
        return 0.0

    def t_required(self, d: float, gate: float = 1.0) -> float:
        """Months of data until ``mde80 <= d``; ``inf`` if never (below the floor or beyond ``T_CAP_MONTHS``)."""
        if not d > 0.0:
            return math.inf
        if not math.isfinite(self.mde80(1.0, gate)):
            return math.inf
        if d <= self.floor(gate) * (1.0 + 1e-12):
            return math.inf
        lo, hi = 0.25, T_CAP_MONTHS
        if self.mde80(lo, gate) <= d:
            return lo
        if self.mde80(hi, gate) > d:
            return math.inf
        f = lambda lt: self.mde80(math.exp(lt), gate) - d
        return float(math.exp(optimize.brentq(f, math.log(lo), math.log(hi), xtol=1e-10, rtol=1e-12)))

    def describe(self) -> dict:
        return {"key": self.key, "label": self.label}


@dataclass(frozen=True)
class C10Windows(Rule):
    """R1 (``joint_target`` False: power 0.80 per window) and R2 (power 0.80 for the joint decision)."""

    joint_target: bool = False
    key: str = "R1"
    label: str = "C.10 per window 0.05 / 0.80"
    two_windows = True

    def _factor(self, gate: float) -> float:
        p = math.sqrt(POWER) if self.joint_target else POWER
        return Z_WINDOW + target_quantile(p, gate)

    def window_months(self, t: float) -> float:
        return t / 2.0

    def power(self, d: float, t: float, gate: float = 1.0) -> float:
        p_w = gate * float(norm.sf(Z_WINDOW - d * math.sqrt(t / (2.0 * _MONTHS))))
        return p_w * p_w

    def mde80(self, t: float, gate: float = 1.0) -> float:
        return self._factor(gate) * math.sqrt(2.0 * _MONTHS / t)

    def t_required(self, d: float, gate: float = 1.0) -> float:
        c = self._factor(gate)
        if not math.isfinite(c) or not d > 0.0:
            return math.inf
        return _capped(2.0 * _MONTHS * (c / d) ** 2)

    def describe(self) -> dict:
        return {"key": self.key, "label": self.label, "alpha_per_window": ALPHA_WINDOW,
                "power_target": "0.80 per window (joint 0.64)" if not self.joint_target else "0.80 joint (per window 0.894)"}


@dataclass(frozen=True)
class Pooled(Rule):
    """R3: pooled one-sided test at alpha 0.0025, no screen."""

    key: str = "R3"
    label: str = "pooled 0.0025, no screen"

    def power(self, d: float, t: float, gate: float = 1.0) -> float:
        return gate * float(norm.sf(Z_POOL - d * math.sqrt(t / _MONTHS)))

    def mde80(self, t: float, gate: float = 1.0) -> float:
        return (Z_POOL + target_quantile(POWER, gate)) * math.sqrt(_MONTHS / t)

    def t_required(self, d: float, gate: float = 1.0) -> float:
        c = Z_POOL + target_quantile(POWER, gate)
        if not math.isfinite(c) or not d > 0.0:
            return math.inf
        return _capped(_MONTHS * (c / d) ** 2)


@dataclass(frozen=True)
class PooledScreen(Rule):
    """R4: pooled 0.0025 plus recency screen on the youngest 12-month window at ``alpha_s``."""

    alpha_s: float = 0.05
    key: str = "R4"
    label: str = "pooled 0.0025 + recency screen"

    @property
    def z_s(self) -> float:
        return float(norm.isf(self.alpha_s))

    @staticmethod
    def r_of(t: float) -> float:
        return min(1.0, _MONTHS / t)

    def power(self, d: float, t: float, gate: float = 1.0) -> float:
        return gate * screen_pass_probability(d, self.r_of(t), self.z_s)

    def mde80(self, t: float, gate: float = 1.0) -> float:
        p = POWER / gate
        if p >= 1.0:
            return math.inf
        r = self.r_of(t)
        return float(optimize.brentq(lambda d: screen_pass_probability(d, r, self.z_s) - p, 1e-9, 60.0,
                                     xtol=1e-12, rtol=1e-12))

    def floor(self, gate: float = 1.0) -> float:
        return self.z_s + target_quantile(POWER, gate)

    def describe(self) -> dict:
        return {"key": self.key, "label": self.label, "alpha_pool": ALPHA_POOL, "alpha_screen": self.alpha_s,
                "correlation": "sqrt(r), r = 12 / T"}


@dataclass(frozen=True)
class PooledStability(Rule):
    """R5 (decided, DEC-107 (1)): pooled 0.0025 plus the registered stability test (DEC-104 N4).

    Without a drop the stability test passes with probability ``q = 1 - alpha_stab`` (cost ratio, not a "power"), and
    at equal variances its statistic is independent of the pooled mean, so the joint power is ``q`` times the pooled
    power.  With at most ``void_below_months`` (12) months of confirmation data the test is void (no older part), so
    ``q = 1`` there and R5 equals R3 (DEC-104 N4 (1), DEC-107 (1) (b)).
    """

    alpha_stab: float = 0.05
    key: str = "R5"
    label: str = "pooled 0.0025 + registered stability test (variant c, decided DEC-107)"
    void_below_months: float = 12.0

    @property
    def p_stab(self) -> float:
        return 1.0 - self.alpha_stab

    def q(self, t: float) -> float:
        """Cost ratio of the stability test at ``t`` months of confirmation data (1 while the test is void)."""
        return 1.0 if t <= self.void_below_months else self.p_stab

    def power(self, d: float, t: float, gate: float = 1.0) -> float:
        return gate * self.q(t) * float(norm.sf(Z_POOL - d * math.sqrt(t / _MONTHS)))

    def mde80(self, t: float, gate: float = 1.0) -> float:
        return (Z_POOL + target_quantile(POWER, gate * self.q(t))) * math.sqrt(_MONTHS / t)

    def t_required(self, d: float, gate: float = 1.0) -> float:
        if not d > 0.0:
            return math.inf
        c_void = Z_POOL + target_quantile(POWER, gate)              # test void: pooled alone
        if math.isfinite(c_void):
            t_void = _MONTHS * (c_void / d) ** 2
            if t_void <= self.void_below_months:
                return t_void
        c = Z_POOL + target_quantile(POWER, gate * self.p_stab)      # beyond 12 months the test costs q
        if not math.isfinite(c):
            return math.inf
        return _capped(max(_MONTHS * (c / d) ** 2, self.void_below_months * (1.0 + 1e-12)))

    def describe(self) -> dict:
        return {"key": self.key, "label": self.label, "alpha_pool": ALPHA_POOL, "alpha_stab": self.alpha_stab,
                "cost_ratio_q": self.p_stab, "void_below_months": self.void_below_months,
                "decided": "DEC-107 (1); derivation DEC-104 N4"}


@dataclass(frozen=True)
class GroupSequential(Rule):
    """R6: O'Brien-Fleming, ``looks`` equally spaced looks, alpha 0.0025; ``t`` is the MAXIMUM data in months."""

    looks: int = 4
    screen_alpha: float | None = None
    futility: bool = False
    n_paths: int = 200_000
    key: str = "R6"
    label: str = "GSD O'Brien-Fleming"

    def design(self, t: float, gate: float = 1.0) -> gsd.GsdDesign:
        p = POWER / gate
        if p >= 1.0:
            raise ValueError("gate makes power 0.80 unreachable")
        if self.screen_alpha is None:
            return gsd.grid_design(ALPHA_POOL, self.looks, round(p, 12), self.futility)
        return gsd.screen_design_at_r(ALPHA_POOL, self.looks, round(p, 12), self.screen_alpha,
                                      min(1.0, _MONTHS / t), self.futility, self.n_paths)

    def power(self, d: float, t: float, gate: float = 1.0) -> float:
        theta = d * math.sqrt(t / _MONTHS)
        c_b = gsd.obf_constant(ALPHA_POOL, self.looks)
        if self.screen_alpha is None:
            return gate * gsd.grid_oc(c_b, theta, self.looks, self.futility)[0]
        node = min(gsd.R_NODES, key=lambda x: abs(x - min(1.0, _MONTHS / t)))
        des = gsd.mc_design(ALPHA_POOL, self.looks, POWER, self.screen_alpha, node, self.futility, self.n_paths)
        return gate * gsd.mc_pass_probability(des, theta, self.n_paths)[0]

    def mde80(self, t: float, gate: float = 1.0) -> float:
        if POWER / gate >= 1.0:
            return math.inf
        return self.design(t, gate).theta * math.sqrt(_MONTHS / t)

    def floor(self, gate: float = 1.0) -> float:
        if self.screen_alpha is None:
            return 0.0
        return float(norm.isf(self.screen_alpha)) + target_quantile(POWER, gate)

    def describe(self) -> dict:
        return {"key": self.key, "label": self.label, "alpha_pool": ALPHA_POOL, "looks": self.looks,
                "screen_alpha": self.screen_alpha, "futility": self.futility}


def build_menu(screen_alphas: tuple[float, ...] = (0.05, 0.10, 0.20, 0.50), looks: tuple[int, ...] = (1, 2, 3, 4),
               gsd_paths: int = 200_000, alpha_stab: float = 0.05, gsd_screen_alpha: float = 0.05,
               futility: bool = False) -> list[Rule]:
    """Ordered rule menu R1..R6.  GSD without screen for every K > 1 in ``looks`` (deterministic grid); GSD with
    screen only for the largest K (Monte Carlo, fixed seed)."""
    menu: list[Rule] = [
        C10Windows(False, "R1", "C.10 per window 0.05 / 0.80 (power 0.80 each, joint 0.64)"),
        C10Windows(True, "R2", "C.10 joint 0.80 (power sqrt(0.80) per window)"),
        Pooled(),
    ]
    for a in screen_alphas:
        menu.append(PooledScreen(a, f"R4_a{int(round(a * 100)):02d}", f"pooled 0.0025 + recency screen alpha_s {a:.2f}, joint power 0.80"))
    menu.append(PooledStability(alpha_stab, "R5", "pooled 0.0025 + registered stability test (variant c, decided DEC-107), joint power 0.80"))
    kmax = max(looks)
    for k in sorted(set(looks)):
        if k >= 2:
            menu.append(GroupSequential(k, None, futility, gsd_paths, f"R6_K{k}", f"GSD OBF {k} looks 0.0025, no screen"))
    if kmax >= 2:
        menu.append(GroupSequential(kmax, gsd_screen_alpha, futility, gsd_paths, f"R6_K{kmax}_screen",
                                    f"GSD OBF {kmax} looks 0.0025 + recency screen {gsd_screen_alpha:.2f} at every stop"))
    return menu


def data_factor(rule: Rule, reference: Rule, t: float, gate: float = 1.0, gate_ref: float = 1.0) -> float:
    """Data needed by ``rule`` relative to ``reference`` for the same MDE: ``T / T_ref(mde80_rule(T))``.

    Equals the squared ratio of the MDE factors for rules without a screen (1.0766 for R3 vs R1, 1.2593 for R2 vs R3
    with a factor 2 for the window split included).
    """
    d = rule.mde80(t, gate)
    t_ref = reference.t_required(d, gate_ref)
    return t / t_ref if math.isfinite(t_ref) and t_ref > 0 else math.inf


def t_mde_factor(alpha: float, df: float, power: float = POWER, gate: float = 1.0) -> dict:
    """MDE inflation of a test with ESTIMATED SE (Student-t critical value, noncentral-t power) against the normal theory.

    ``df`` is the degrees of freedom of the SE estimate (clusters - 1).  Returns the t critical value, the normal critical
    value and ``factor = ncp / (z_alpha + z_power)`` (>= 1; OC derivation (e): 1.14 .. 1.38 for 7 .. 15 df at alpha 0.0025).
    A sensitivity quantity, not a rule: the registered tests use the larger of the normal and the t boundary.
    """
    q = power / gate
    if df < 1.0 or q >= 1.0:
        return {"df": df, "t_crit": None, "z_crit": float(norm.isf(alpha)), "factor": None}
    z_crit = float(norm.isf(alpha))
    if df > 20000.0:
        return {"df": df, "t_crit": z_crit, "z_crit": z_crit, "factor": 1.0}
    t_crit = float(student_t.isf(alpha, df))
    ncp = float(optimize.brentq(lambda m: nct.sf(t_crit, df, m) - q, 0.0, 200.0, xtol=1e-10))
    return {"df": df, "t_crit": t_crit, "z_crit": z_crit, "factor": ncp / (z_crit + float(norm.ppf(q)))}


def ppv(power: float, alpha: float, base_rate: float) -> float:
    """Positive predictive value of a PASS: ``power * pi / (power * pi + alpha * (1 - pi))`` at base rate ``pi``."""
    if not (0.0 < base_rate < 1.0):
        raise ValueError("base_rate must be in (0, 1)")
    return power * base_rate / (power * base_rate + alpha * (1.0 - base_rate))


def sr_eff_needed_c10(window_years: float, gate: float = 1.0) -> float:
    """SR_eff (effect / SE_12) a C.10 window of ``window_years`` needs for power 0.80: 2.49 / 1.76 / 1.44 at 1/2/3."""
    return (Z_WINDOW + target_quantile(POWER, gate)) / math.sqrt(window_years)


def simulate_rule(rule: Rule, d: float, t: float, gate: float, n: int, seed: int) -> dict:
    """Monte Carlo estimate of P(PASS) of the whole decision rule (>= 1000 replicates, fixed seed).

    Independent of the analytic ``power``: simulates the sufficient statistics of the decision (window Z values,
    the youngest/older split, the Brownian path of the group-sequential rule) and the gate as a Bernoulli draw.
    """
    if n < 1000:
        raise ValueError("Monte Carlo needs >= 1000 replicates (DEC-104 E8 (a))")
    rng = np.random.default_rng(seed)
    if isinstance(rule, C10Windows):
        mu = d * math.sqrt(t / (2.0 * _MONTHS))
        z = rng.standard_normal((n, 2)) + mu
        g = rng.random((n, 2)) < gate
        ok = np.all((z > Z_WINDOW) & g, axis=1)
    elif isinstance(rule, Pooled):
        z = rng.standard_normal(n) + d * math.sqrt(t / _MONTHS)
        ok = (z > Z_POOL) & (rng.random(n) < gate)
    elif isinstance(rule, PooledScreen):
        r = rule.r_of(t)
        z_rec = rng.standard_normal(n) + d
        if r >= 1.0:
            z_pool = z_rec
        else:
            z_old = rng.standard_normal(n) + d * math.sqrt((1.0 - r) / r)
            z_pool = math.sqrt(r) * z_rec + math.sqrt(1.0 - r) * z_old
        ok = (z_pool > Z_POOL) & (z_rec > rule.z_s) & (rng.random(n) < gate)
    elif isinstance(rule, PooledStability):
        z = rng.standard_normal(n) + d * math.sqrt(t / _MONTHS)
        ok = (z > Z_POOL) & (rng.random(n) < rule.p_stab) & (rng.random(n) < gate)
    elif isinstance(rule, GroupSequential):
        bank = gsd._Bank(n, seed)
        c_b = gsd.obf_constant(ALPHA_POOL, rule.looks)
        z_s = None if rule.screen_alpha is None else float(norm.isf(rule.screen_alpha))
        node = None
        if z_s is not None:
            node = min(gsd.R_NODES, key=lambda x: abs(x - min(1.0, _MONTHS / t)))
        p, e_t = bank.run(d * math.sqrt(t / _MONTHS), c_b, rule.looks, node, z_s, rule.futility)
        p *= gate
        return {"p": p, "se": math.sqrt(max(p * (1.0 - p), 0.0) / n), "n": n, "e_t_fraction": e_t}
    else:  # pragma: no cover - unknown rule type
        raise TypeError(type(rule).__name__)
    p = float(np.mean(ok))
    return {"p": p, "se": math.sqrt(max(p * (1.0 - p), 0.0) / n), "n": n}
