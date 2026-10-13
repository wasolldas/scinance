"""T0/T2/T4 tests for ``bybit_edge.research.power_p1`` (DEC-94, programme rule P-1).

  * T0  known values, identities, input guards, selection ceiling.
  * T0  MONOTONICITY (DEC-94 (8)): with fixed SEs a rising prior never moves a design from
        {C10, DEC52} back to GL012 (all windows scaled together).
  * T4  gate arithmetic on conserved payloads (read-only): A1 feasibility
        (``herleitung_a1/feasibility.json``, GL-033) and the A3 v5e prelaunch JSON (GL-032).
        Sealed files are never opened (loader refuses their names; window "L" is not read).
  * T2  determinism of the stationary bootstrap (N >= 3, bit-identical per seed) and
        plausibility against analytic AR(1) variance factors.
"""
from __future__ import annotations

import fnmatch
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest
from scipy import integrate

from bybit_edge.research import power_p1 as pp

_N = NormalDist()
REPO = Path(__file__).resolve().parents[2]
A1_JSON = REPO / "scinance3-impl" / "state" / "herleitung_a1" / "feasibility.json"
A3_JSON = REPO / "scinance3-impl" / "state" / "runs" / "wp13a_20261012_v5e" / "wp13a_prelaunch.json"
SEALED_PATTERNS = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")
_RANK = {pp.REGIME_GL012: 0, pp.REGIME_DEC52: 1, pp.REGIME_C10: 2}


def _load_unsealed(path: Path) -> dict:
    if any(fnmatch.fnmatch(path.name, pat) for pat in SEALED_PATTERNS):
        raise AssertionError(f"refusing sealed file {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _ar1(n: int, rho: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = e[0] / math.sqrt(1.0 - rho * rho)
    for t in range(1, n):
        x[t] = rho * x[t - 1] + e[t]
    return x


# ----------------------------------------------------------------------------
# T0: known values, identities, guards
# ----------------------------------------------------------------------------

def test_t0_constants_and_known_values():
    assert pp.ALPHA_WINDOW == 0.05
    assert pp.POWER_TARGET == 0.80
    assert pp.Z_KRIT_POOLED_DEC52 == 2.5287
    assert pp.z_krit(0.05) == pytest.approx(1.6449, abs=5e-5)
    assert pp.z_krit(0.01) == pytest.approx(2.3263, abs=5e-5)
    assert pp.z_krit(0.025) == pytest.approx(1.9600, abs=5e-5)
    assert pp.z_krit(0.5) == pytest.approx(0.0, abs=1e-12)
    assert pp.Z_POWER == pytest.approx(0.8416, abs=5e-5)
    # MDE factors are NOT thresholds (DEC-94 (1)): 2.4865 / 3.1680 / 2.8016
    assert pp.mde_factor(0.05) == pytest.approx(2.4865, abs=5e-5)
    assert pp.mde_factor(0.01) == pytest.approx(3.1680, abs=5e-5)
    assert pp.mde_factor(0.025) == pytest.approx(2.8016, abs=5e-5)
    assert pp.mde_factor(0.05, power=0.5) == pytest.approx(pp.z_krit(0.05), abs=1e-12)
    # A-6: pooled 2.5287 <-> alpha_p 0.0057
    assert 1.0 - _N.cdf(pp.Z_KRIT_POOLED_DEC52) == pytest.approx(0.0057, abs=5e-5)


def test_t0_guards_loud_fail():
    for bad in (0.0, 1.0, -0.1, 1.5, float("nan")):
        with pytest.raises(ValueError):
            pp.z_krit(bad)
    with pytest.raises(ValueError):
        pp.mde_factor(0.05, power=1.0)
    with pytest.raises(ValueError):
        pp.condition_power(0.1, 0.0, 0.0)
    with pytest.raises(ValueError):
        pp.window_power(float("inf"), 1.0, 1.6)
    with pytest.raises(ValueError):
        pp.mde80(-1.0, 1.6)
    with pytest.raises(ValueError):
        pp.assign_regime([1.0, 1.0], [1.0])               # length mismatch
    with pytest.raises(ValueError):
        pp.assign_regime([], [])
    with pytest.raises(ValueError):
        pp.assign_regime([1.0, 1.0], [1.0, 0.0])           # SE must be > 0
    with pytest.raises(ValueError):
        pp.dec52_gate_power([1.0], [1.0])                  # needs two windows


def test_t0_phi_identities():
    assert pp.condition_power(1.0, 1.0, 3.0) == pytest.approx(0.5, abs=1e-15)
    for prior, thr, sd in ((0.3, 0.1, 0.2), (-1.0, 0.5, 2.0), (4.0, 1.0, 1.5)):
        # symmetry Phi(x) + Phi(-x) = 1
        assert (pp.condition_power(prior, thr, sd)
                + pp.condition_power(2 * thr - prior, thr, sd)) == pytest.approx(1.0, abs=1e-12)
    # window_power = Phi(prior/SE - z_krit) when sd = se
    for se in (0.5, 1.0, 51.7):
        for prior in (0.0, 0.7 * se, 2.0 * se):
            assert pp.window_power(prior, se, 1.6449) == pytest.approx(
                _N.cdf(prior / se - 1.6449), abs=1e-12)
    # power is exactly 0.80 at MDE80, and MDE80 = mde_factor * SE for sd = se
    z = pp.z_krit(0.05)
    assert pp.window_power(pp.mde80(2.0, z), 2.0, z) == pytest.approx(0.80, abs=1e-9)
    assert pp.mde80(2.0, z) == pytest.approx(pp.mde_factor(0.05) * 2.0, abs=1e-12)
    # separate sd (data-dependent SE rule, DEC-94 (3)): T from SE, noise from SD
    assert pp.mde80(1.0, 1.6449, sd=2.0) == pytest.approx(1.6449 + 2 * pp.Z_POWER, abs=1e-12)
    assert pp.window_power(pp.mde80(1.0, z, sd=2.0), 1.0, z, sd=2.0) == pytest.approx(
        0.80, abs=1e-9)
    # a larger SD with the same threshold lowers power above the threshold
    assert pp.window_power(3.0, 1.0, z, sd=2.0) < pp.window_power(3.0, 1.0, z, sd=1.0)


def test_t0_selection_z_and_crossing():
    assert pp.selection_z(1) == 0.0                      # no selection with one test
    assert pp.selection_z(2) == pytest.approx(0.5198, abs=1e-3)   # E[max of 2] = 0.564 (approx.)
    ks = list(range(1, 60))
    vals = [pp.selection_z(k) for k in ks]
    assert all(b > a for a, b in itertools.pairwise(vals))     # strictly increasing
    assert pp.selection_z(7) == pytest.approx(1.3868, abs=1e-3)   # PRD K = 7 ceiling
    assert pp.selection_z(12) == pytest.approx(1.6648, abs=1e-3)
    assert pp.selection_z(12) > pp.z_krit(0.05)           # binding from K >= 12 (DEC-94 (7))
    assert pp.selection_z(11) < pp.z_krit(0.05)
    k_star = next(k for k in ks if pp.selection_z(k) > pp.z_krit(0.05))
    assert k_star == 12                                   # crossing point reported in the hand-off
    assert pp.effective_z(0.05, 11) == pytest.approx(pp.z_krit(0.05))
    assert pp.effective_z(0.05, 12) == pytest.approx(pp.selection_z(12))
    assert pp.effective_z(0.05, 1) == pytest.approx(pp.z_krit(0.05))
    assert pp.effective_z(0.0057, 12) == pytest.approx(pp.z_krit(0.0057))   # stricter alpha binds
    for bad in (0, -3, 2.5):
        with pytest.raises(ValueError):
            pp.selection_z(bad)


def test_t0_dec52_joint_rate_at_pooled_z_is_half_percent():
    """A-6: with z_krit_pooled 2.5287 the null rate of the DEC-52 gate (two equal windows,
    screens 0.5 x pooled threshold) is the 0.5 % of PRD 3.5 (with 2.3263 it is 0.85 %)."""
    def joint(zp: float) -> float:
        sep = 1.0 / math.sqrt(2.0)
        tp = zp * sep
        ts = 0.5 * tp
        val, _ = integrate.quad(
            lambda x1: _N.pdf(x1) * (1.0 - _N.cdf(max(ts, 2.0 * tp - x1))),
            ts, 12.0, points=[2.0 * tp - ts], limit=400)
        return val
    assert joint(pp.Z_KRIT_POOLED_DEC52) == pytest.approx(0.005, abs=2e-5)
    assert joint(2.3263) == pytest.approx(0.0085, abs=1e-4)
    # C.10 jointly: 0.05^2 = 0.25 %
    assert pp.ALPHA_WINDOW ** 2 == pytest.approx(0.0025, abs=1e-12)


# ----------------------------------------------------------------------------
# T0: gate power and regime assignment on synthetic inputs
# ----------------------------------------------------------------------------

def test_t0_dec52_gate_power_structure():
    g = pp.dec52_gate_power([2.0, 3.0], [1.0, 1.0])
    se_p = math.sqrt(2.0) / 2.0
    assert g["se_pooled"] == pytest.approx(se_p)
    assert g["prior_pooled"] == pytest.approx(2.5)
    assert g["threshold_pooled"] == pytest.approx(pp.Z_KRIT_POOLED_DEC52 * se_p)
    assert g["threshold_screen"] == pytest.approx(0.5 * pp.Z_KRIT_POOLED_DEC52 * se_p)
    assert g["power_pooled"] == pytest.approx(
        _N.cdf((2.5 - g["threshold_pooled"]) / se_p), abs=1e-12)
    assert g["power_product"] == pytest.approx(
        g["power_pooled"] * g["power_screens"][0] * g["power_screens"][1], abs=1e-12)
    assert g["power_exact"] is None
    assert g["mde80_pooled"] == pytest.approx((pp.Z_KRIT_POOLED_DEC52 + pp.Z_POWER) * se_p)
    # power is monotone in the prior
    lo = pp.dec52_gate_power([1.0, 1.0], [1.0, 1.0])["power_product"]
    hi = pp.dec52_gate_power([2.0, 2.0], [1.0, 1.0])["power_product"]
    assert hi > lo


def test_t0_assign_regime_three_branches():
    z = pp.z_krit(0.05)
    mde = pp.mde80(1.0, z)
    # strong in both windows -> C10
    r = pp.assign_regime([1.2 * mde, 1.5 * mde], [1.0, 1.0])
    assert r["regime"] == "C10" and r["window_power_min"] >= 0.80
    # exactly at the MDE80 boundary -> C10 (>= 0.80, float noise tolerated)
    assert pp.assign_regime([mde, mde], [1.0, 1.0])["regime"] == "C10"
    # weak window 1, strong window 2 -> DEC52 (gate product >= 0.80)
    r = pp.assign_regime([2.2, 6.0], [1.0, 1.0])
    assert r["regime"] == "DEC52"
    assert r["window_power"][0] < 0.80 <= r["gate_power_product"]
    assert r["mde80"][0] == pytest.approx(mde)
    assert "DEC52" in r["reason"] and "product" in r["reason"]
    # weak everywhere -> GL012
    r = pp.assign_regime([1.0, 1.0], [1.0, 1.0])
    assert r["regime"] == "GL012" and r["gate_power_product"] < 0.80
    # a single window cannot form a DEC-52 gate
    assert pp.assign_regime([2.0], [1.0])["regime"] == "GL012"
    assert pp.assign_regime([mde], [1.0])["regime"] == "C10"
    # the returned dict carries the fixed vocabulary
    assert r["alpha"] == 0.05 and r["z_krit"] == pytest.approx(1.6449, abs=5e-5)
    assert r["mde_factor"] == pytest.approx(2.4865, abs=5e-5)


def test_t0_assignment_is_always_at_alpha_005_and_stricter_alpha_stays_in_branch():
    # A-2: any other alpha in the assignment is refused loudly
    with pytest.raises(ValueError, match="alpha"):
        pp.assign_regime([5.0, 5.0], [1.0, 1.0], alpha=0.01)
    assert pp.assign_regime([5.0, 5.0], [1.0, 1.0], alpha=0.05)["regime"] == "C10"
    # C10 candidate: stricter alpha that keeps power is accepted ...
    priors, ses = [4.2, 4.2], [1.0, 1.0]            # MDE80 at 0.05 is 2.49 -> C10
    assert pp.assign_regime(priors, ses)["regime"] == "C10"
    ok = pp.check_stricter_alpha(priors, ses, "C10", 0.0064)       # z_krit 2.4865
    assert ok["ok"] and ok["power"] >= 0.80
    # ... one that loses power is rejected loudly, and does NOT change the regime
    with pytest.raises(pp.StricterAlphaRejected):
        pp.check_stricter_alpha(priors, ses, "C10", 0.0001)
    assert pp.assign_regime(priors, ses)["regime"] == "C10"
    # DEC52 branch needs the registered pooled z as a number
    p2, s2 = [2.4, 7.0], [1.0, 1.0]
    assert pp.assign_regime(p2, s2)["regime"] == "DEC52"
    with pytest.raises(ValueError, match="pooled"):
        pp.check_stricter_alpha(p2, s2, "DEC52", 0.01)
    with pytest.raises(ValueError):
        pp.check_stricter_alpha(p2, s2, "DEC52", 0.01, z_krit_pooled_registered=2.0)  # looser
    with pytest.raises(pp.StricterAlphaRejected):
        pp.check_stricter_alpha(p2, s2, "DEC52", 0.01, z_krit_pooled_registered=6.0)
    # looser alpha and GL012 have no branch
    with pytest.raises(ValueError):
        pp.check_stricter_alpha(priors, ses, "C10", 0.10)
    with pytest.raises(ValueError):
        pp.check_stricter_alpha(priors, ses, "GL012", 0.01)


def test_t0_gate_exact_probability_report_only():
    pr, se = [100.69981543136316, 194.5319246557547], [51.713580497275814, 49.15638910562937]
    g = pp.dec52_gate_power(pr, se, exact=True)
    # independent quadrature of the same event
    sep, zp = math.sqrt(se[0] ** 2 + se[1] ** 2) / 2.0, pp.Z_KRIT_POOLED_DEC52
    tp = zp * sep
    ts = 0.5 * tp

    def f(x1: float) -> float:
        lo = max(ts, 2.0 * tp - x1)
        return _N.pdf((x1 - pr[0]) / se[0]) / se[0] * (1.0 - _N.cdf((lo - pr[1]) / se[1]))
    ref, _ = integrate.quad(f, ts, pr[0] + 10 * se[0], points=[2 * tp - ts], limit=400)
    assert abs(g["power_exact"] - ref) < 4.0 * g["power_exact_mc_se"]
    assert ref >= g["power_product"]                      # product is the conservative bound
    # deterministic per seed
    g2 = pp.dec52_gate_power(pr, se, exact=True)
    assert g2["power_exact"] == g["power_exact"]
    # the assignment never uses the exact value
    a = pp.assign_regime(pr, se, exact_report=True)
    b = pp.assign_regime(pr, se, exact_report=False)
    assert a["regime"] == b["regime"] and a["gate_power_exact"] is not None


# ----------------------------------------------------------------------------
# T0: MONOTONICITY (DEC-94 (8), mandatory)
# ----------------------------------------------------------------------------

def _assert_monotone(fn, priors0, ses, sds=None, *, step=0.004, top=40.0):
    prev = -1
    prev_theta = 0.0
    seen_admitted = False
    for i in range(int(top / step) + 1):
        theta = i * step
        reg = fn([theta * p for p in priors0], ses, sds=sds)["regime"]
        if reg != pp.REGIME_GL012:
            seen_admitted = True
        if seen_admitted:
            assert reg != pp.REGIME_GL012, f"fell back to GL012 at theta={theta} (prev {prev_theta})"
        rank = _RANK[reg]
        assert rank >= prev, f"regime rank fell from {prev} to {rank} at theta={theta}"
        prev, prev_theta = rank, theta
    return prev


@pytest.mark.parametrize("priors0,ses", [
    ([1.0, 1.0], [1.0, 1.0]),
    ([1.0, 2.0], [1.0, 1.0]),
    ([2.0, 1.0], [1.0, 1.0]),
    ([0.3, 1.0], [1.0, 1.0]),
    ([1.0, 3.0], [1.0, 1.0]),
    ([100.69981543136316, 194.5319246557547], [51.713580497275814, 49.15638910562937]),    # A1 c=1
    ([100.69981543136316, 194.5319246557547], [80.76304406988815, 76.76938207486229]),      # A1 E4
    ([0.03, 0.03], [0.018058, 0.011442]),                                                    # A3-like
    ([1.0, 1.5, 2.0], [1.0, 2.0, 0.5]),
    ([-1.0, 2.0], [1.0, 1.0]),
    ([1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]),
])
def test_t0_monotonicity_rising_prior_never_returns_to_gl012(priors0, ses):
    """Fine prior grid, all windows scaled together, SEs fixed (DEC-94 (8), review 5)."""
    final = _assert_monotone(pp.assign_regime, priors0, ses)
    final_a3 = _assert_monotone(pp.assign_regime_a3_practice, priors0, ses)
    # with every prior positive, a large enough scale reaches C10; a negative prior never does
    expected = _RANK[pp.REGIME_C10] if min(priors0) > 0 else _RANK[pp.REGIME_GL012]
    assert final == expected and final_a3 == expected


def test_t0_monotonicity_random_configurations():
    rng = np.random.default_rng(94)
    for _ in range(40):
        n = int(rng.integers(2, 5))
        ses = list(np.exp(rng.normal(0.0, 0.7, n)))
        priors0 = list(rng.uniform(0.2, 3.0, n))
        sds = list(np.array(ses) * rng.uniform(0.8, 1.6, n))
        _assert_monotone(pp.assign_regime, priors0, ses, sds=sds, step=0.01, top=6.0)
        _assert_monotone(pp.assign_regime_a3_practice, priors0, ses, sds=sds, step=0.01, top=6.0)


# ----------------------------------------------------------------------------
# T4: conserved payloads (read-only)
# ----------------------------------------------------------------------------

def test_t4_loader_refuses_sealed_names(tmp_path: Path):
    for name in ("x_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_a_UNION_REAL.csv"):
        with pytest.raises(AssertionError):
            _load_unsealed(tmp_path / name)


def _a1(c_key: str) -> tuple[list[float], list[float]]:
    d = _load_unsealed(A1_JSON)
    grid = d["configs"]["A_dec70_1h_eingeschlossen"]["power"]["grid"][f"{c_key}|theta=1.0"]
    return ([grid["W1"]["prem_bp"], grid["W2"]["prem_bp"]],
            [grid["W1"]["se_bp"], grid["W2"]["se_bp"]])


def test_t4_a1_gate_power_c1_theta1_p1_vs_a3_practice():
    """GL-033 payload, c = 1, theta = 1 (theta stays UNBELEGT -- not a matter of the function):
    window power W1 ~0.619 (< 0.80), DEC-52 gate power product ~0.812 (exact ~0.843), regime
    DEC52 under P-1; GL012 under the A3 practice -> label 'only by DEC-94'."""
    priors, ses = _a1("c1_binding")
    r = pp.assign_regime(priors, ses, exact_report=True)
    assert r["window_power"][0] == pytest.approx(0.619, abs=1e-3)
    assert r["window_power"][0] < 0.80 <= r["window_power"][1]
    assert r["window_power"][1] == pytest.approx(0.990, abs=1e-3)
    assert r["gate"]["se_pooled"] == pytest.approx(35.674, abs=1e-3)       # = JSON se_pooled_bp
    assert r["gate"]["prior_pooled"] == pytest.approx(147.616, abs=1e-3)   # = JSON prem_pooled_bp
    assert r["gate_power_product"] == pytest.approx(0.812, abs=1e-3)
    assert r["gate_power_exact"] == pytest.approx(0.843, abs=2e-3)         # 0.8426 by quadrature
    assert r["gate_power_exact"] >= r["gate_power_product"]
    assert r["regime"] == "DEC52"
    # the JSON's own window numbers agree with the function (same Phi(prior/SE - z_krit))
    grid = _load_unsealed(A1_JSON)["configs"]["A_dec70_1h_eingeschlossen"]["power"]["grid"]
    g = grid["c1_binding|theta=1.0"]
    assert r["window_power"][0] == pytest.approx(g["W1"]["P_fenster"], abs=1e-3)
    assert r["window_power"][1] == pytest.approx(g["W2"]["P_fenster"], abs=1e-3)
    assert r["mde80"][0] == pytest.approx(g["W1"]["mde80_bp"], abs=0.2)
    assert r["mde80"][1] == pytest.approx(g["W2"]["mde80_bp"], abs=0.2)
    # A3 practice (factor 2.4865 per window, DEC-87 (F), product): GL012
    a = pp.assign_regime_a3_practice(priors, ses)
    assert a["regime"] == "GL012"
    assert a["window_power"][0] == pytest.approx(g["W1"]["P_gate_threshold_2_4865"], abs=1e-3)
    assert a["window_power"][1] == pytest.approx(g["W2"]["P_gate_threshold_2_4865"], abs=1e-3)
    assert a["mde80"][0] == pytest.approx(g["W1"]["mde80_gate_threshold_2_4865_bp"], abs=0.2)
    assert a["p1_regime"] == "DEC52"
    assert a["zugelassen_nur_durch_dec94"] is True
    assert a["label"] == "zugelassen nur durch DEC-94 (Lockerung)"
    # even with the DEC-52 gate admitted at the old pooled factor 3.1680 it stays below 0.80
    b = pp.assign_regime_a3_practice(priors, ses, allow_dec52=True)
    assert b["regime"] == "GL012" and b["gate_power_product"] < 0.80


def test_t4_a1_dec67_e4_stays_gl012_under_both():
    """c = 2.439 (DEC-67 E4): GL-033 ground E1 stands (both regimes GL012)."""
    priors, ses = _a1("c_dec67_E4")
    r = pp.assign_regime(priors, ses)
    assert r["window_power"][0] == pytest.approx(0.345, abs=1e-3)
    assert r["window_power"][1] == pytest.approx(0.813, abs=1e-3)
    assert r["gate_power_product"] < 0.80
    assert r["regime"] == "GL012"
    a = pp.assign_regime_a3_practice(priors, ses)
    assert a["regime"] == "GL012" and a["zugelassen_nur_durch_dec94"] is False


def test_t4_a1_admission_threshold_in_theta_c1_vs_e4():
    """Smallest theta without GL012 (grid 0.001): c = 1 admits well below theta = 1, E4 does not."""
    def theta_min(c_key: str) -> float:
        priors, ses = _a1(c_key)
        for i in range(1, 3001):
            th = i / 1000.0
            if pp.assign_regime([th * p for p in priors], ses)["regime"] != "GL012":
                return th
        return math.inf
    t1, t4 = theta_min("c1_binding"), theta_min("c_dec67_E4")
    assert t1 < 1.0 < t4
    assert 0.9 < t1 < 1.0       # ENTWURF 4.2 lists 0.945 for L3v at z_p 2.3263 -> a bit higher here


def _a3_se(win: dict, variant: str = "mom1", cal: str = "stress") -> float:
    nf = win["noise_floor_and_threshold"]
    sd = win["beta_control_method_study"]["calibrations"][cal]["methods"]["none"]["variants"][
        variant]["factor_sd"]
    return max(nf["floor"]["e_floor"], sd) / math.sqrt(nf["w_judged"])


def test_t4_a3_v5e_mom1_stress_gl012_under_both():
    """GL-032 payload (prelaunch JSON, windows W1/W2 only): raw-IC SE under stress for mom1
    = max(e_floor, factor_sd) / sqrt(w_judged) (DEC-75 (1)); A3-practice MDE80 W1 = 0.060 against
    the prior 0.03; P-1 and A3 practice both give GL012."""
    d = _load_unsealed(A3_JSON)
    se1, se2 = _a3_se(d["windows"]["W1"]), _a3_se(d["windows"]["W2"])
    assert se1 == pytest.approx(0.01806, abs=2e-5)
    prior = 0.03          # PRD 4.1 IC_prior (registered, A3)
    a = pp.assign_regime_a3_practice([prior, prior], [se1, se2])
    assert a["mde80"][0] == pytest.approx(0.0601, abs=1e-4)               # GL-032: 0.060
    assert a["mde80"][1] == pytest.approx(0.0381, abs=1e-4)
    assert a["mde80"][0] > prior and a["mde80"][1] > prior
    assert a["regime"] == "GL012"
    p1 = a["p1"]
    assert p1["mde80"][0] == pytest.approx(0.0449, abs=1e-4)              # (a): 2.4865 * SE
    assert p1["window_power"][0] == pytest.approx(0.507, abs=2e-3)
    assert p1["window_power"][1] == pytest.approx(0.836, abs=2e-3)
    assert p1["gate"]["mde80_pooled"] > prior                              # pooled MDE80 > prior
    assert p1["gate_power_product"] < 0.80
    assert p1["regime"] == "GL012"
    assert a["zugelassen_nur_durch_dec94"] is False


def test_t4_a3_v5e_second_variant_and_measured_are_read_not_guessed():
    """Field-path sanity on all four variants: stress SE >= measured SE (stress is the
    binding, stricter calibration, DEC-77 E1 (b))."""
    d = _load_unsealed(A3_JSON)
    for w in ("W1", "W2"):
        for v in ("mom1", "mom2", "mom4", "rev_gap"):
            assert _a3_se(d["windows"][w], v, "stress") >= _a3_se(d["windows"][w], v, "measured")


# ----------------------------------------------------------------------------
# T2 + plausibility: variance factor and stationary bootstrap
# ----------------------------------------------------------------------------

def test_t2_stationary_bootstrap_deterministic_per_seed():
    x = _ar1(300, 0.4, seed=7)
    snapshot = x.copy()
    runs = [pp.stationary_bootstrap_means(x, 4, 400, seed=2026) for _ in range(3)]
    assert all(np.array_equal(runs[0], r) for r in runs[1:])             # bit-identical
    fps = {hashlib.sha256(r.tobytes()).hexdigest() for r in runs}
    assert len(fps) == 1
    ses = [pp.stationary_bootstrap_se(x, 4, 400, seed=2026) for _ in range(3)]
    assert ses[0] == ses[1] == ses[2]
    assert ses[0] == float(np.std(runs[0], ddof=1))
    assert np.array_equal(x, snapshot)                                   # input untouched
    assert pp.stationary_bootstrap_se(x, 4, 400, seed=2027) != ses[0]    # seed matters


def test_t2_bootstrap_guards():
    x = np.arange(20.0)
    with pytest.raises(TypeError):
        pp.stationary_bootstrap_se(x, 4, 100)                            # seed is mandatory
    with pytest.raises(ValueError):
        pp.stationary_bootstrap_se(x, 0.5, 100, seed=1)
    with pytest.raises(ValueError):
        pp.stationary_bootstrap_se(x, 4, 1, seed=1)
    with pytest.raises(ValueError):
        pp.stationary_bootstrap_se([1.0, float("nan"), 2.0], 4, 10, seed=1)
    assert pp.N_REP_MIN_REGISTERED == 1000


def test_plausibility_iid_variance_factor_and_bootstrap_se():
    rng = np.random.default_rng(11)
    x = rng.standard_normal(5000)
    vf = pp.variance_factor(x, mean_block=4)
    assert vf.c_hat == pytest.approx(1.0, abs=0.15)
    assert vf.c >= 1.0
    se = pp.stationary_bootstrap_se(x, 1, 600, seed=5)                    # block 1 = iid bootstrap
    assert se == pytest.approx(x.std(ddof=1) / math.sqrt(x.size), rel=0.12)


def test_variance_factor_no_credit_for_negative_autocorrelation():
    x = _ar1(20000, -0.5, seed=3)
    vf = pp.variance_factor(x, mean_block=8)
    assert vf.c_hat < 1.0                       # negative autocorrelation -> c_hat < 1 ...
    assert vf.c == 1.0                          # ... but c = max(1, c_hat) gives no credit
    with pytest.raises(ValueError):
        pp.variance_factor(np.ones(30), 4)      # constant series
    with pytest.raises(ValueError):
        pp.variance_factor(np.arange(4.0), 4)   # too short for the bandwidth
    with pytest.raises(ValueError):
        pp.variance_factor(np.arange(30.0), 2.5)


def test_plausibility_ar1_rho_half_variance_factor_near_three():
    """Known AR(1) variance factor (1 + rho) / (1 - rho): 3.0 for rho = 0.5.  The Bartlett
    estimator with B lags has the large-sample value 1 + 2 sum_k (1 - k/(B+1)) rho^k, so a
    short bandwidth is biased low (B = 4 -> 2.225); a long bandwidth approaches 3."""
    rho = 0.5
    x = _ar1(200_000, rho, seed=1)
    for b, tol in ((4, 0.06), (12, 0.12), (40, 0.25)):
        expected = 1.0 + 2.0 * sum((1.0 - k / (b + 1.0)) * rho ** k for k in range(1, b + 1))
        assert pp.variance_factor(x, mean_block=b).c_hat == pytest.approx(expected, abs=tol)
    assert pp.variance_factor(x, mean_block=40).c_hat == pytest.approx(3.0, rel=0.12)
    assert pp.variance_factor(x, mean_block=4).c == pytest.approx(2.225, abs=0.06)
    # long-run SD factor sqrt(c) -> bootstrap SE inflation against the naive SE
    n = 20_000
    y = _ar1(n, rho, seed=2)
    naive = y.std(ddof=1) / math.sqrt(n)
    se_boot = pp.stationary_bootstrap_se(y, 40, 300, seed=9)
    assert (se_boot / naive) ** 2 == pytest.approx(3.0, rel=0.25)
    assert se_boot > 1.4 * naive
