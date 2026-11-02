"""T0 tests of the feasibility calculator (``bybit_edge.research.feasibility31``, programme step F3).

No network, no market data, no sealed file: every number is a nuisance number or a formula result of the dossier, quoted
with its source next to the assertion.  Reference outputs: ``state/prd_analyse_2026-11-01/scripts/orch_oc_check.out`` and
``orch_review_check.out`` (orchestrator re-computations), ``OC_VERFASSUNG31_2026-11-02.md``, DEC-104 / DEC-105.
Tolerances are stated per test (default 1 % relative, Monte Carlo 2..5 % with the sizes used here).
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import math
from pathlib import Path

import pytest
import yaml

from bybit_edge.research.feasibility31 import cli, conjunction as cj, gsd, report as rp, rules as R, schema as sc, sesoi as se

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "bybit_edge" / "research" / "feasibility31"
CASES = ROOT / "scinance3-impl" / "state" / "feasibility"
SMALL = dict(mc_reps=2000, gsd_paths=20000, conjunction_mc=60000)     # sizes of the module-scoped report fixtures


def close(actual: float, expected: float, rel: float = 0.01, abs_: float = 0.0) -> bool:
    return abs(actual - expected) <= max(rel * abs(expected), abs_)


# ---------------------------------------------------------------------------------------------------------------------
# a minimal valid candidate (dict) that the loud-failure tests modify
# ---------------------------------------------------------------------------------------------------------------------
SRC = {"file": "scinance3-impl/state/herleitung_a1/FEASIBILITY.md", "field": "test", "sha256": "0" * 64}


def srcd(v):
    return {"value": v, "source": dict(SRC)}


def base_candidate() -> dict:
    return {
        "schema_version": 1, "candidate_id": "T1", "title": "unit test candidate",
        "statistic": {"name": "test statistic", "unit": "bp", "direction": "positive"},
        "nuisance": {"cluster_unit": "week", "units_per_year": 52, "c_overlap": srcd(1.0),
                     "sd_per_unit": {"central": srcd(100.0), "stress": srcd(120.0)}},
        "sesoi": {"mode": "direct", "unit": "bp", "label": "test SESOI", "value": srcd(10.0)},
        "prior": {"label": "primaer", "median": srcd(12.0), "band": [6.0, 18.0]},
        "data": {"knowledge_class": "panel_crosssection", "cohort_date": "2027-01-01", "selection_k": 0, "v_blind_confirmed": True,
                 "zones": {"X": {"start": "2022-04-18", "end": "2024-06-24", "units": 114},
                           "V": {"start": "2024-07-01", "end": "2026-06-28", "months": 24},
                           "K": {"start": "2026-07-01"}}},
        "design_menu": {"window_months": [6, 9, 12], "looks": [1, 2, 3, 4]},
    }


def make(**mods) -> sc.Candidate:
    obj = base_candidate()
    for path, val in mods.items():
        cur = obj
        parts = path.split("__")
        for p in parts[:-1]:
            cur = cur[p]
        if val is _DEL:
            del cur[parts[-1]]
        else:
            cur[parts[-1]] = val
    return sc.candidate_from_obj(obj)


_DEL = object()


# ---------------------------------------------------------------------------------------------------------------------
# module fixtures: the four regression cases, evaluated once
# ---------------------------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def cases():
    out = {}
    for name in ("A1", "H27", "A2", "KLASSE_W"):
        cand = sc.load_candidate(CASES / f"{name}.yaml")
        out[name] = (cand, rp.evaluate(cand, **SMALL))
    return out


# =====================================================================================================================
# 1. constants and primitive formulas (orch_review_check.out)
# =====================================================================================================================
def test_mde_factors():
    assert close(R.C80, 2.4865, 1e-4) and close(R.MU_FIX, 3.6487, 1e-4)
    assert close(R.Z_POOL, 2.8070, 1e-4) and close(R.Z_POWER, 0.8416, 1e-4)


@pytest.mark.parametrize("rho,expected", [(0.82, 0.858), (0.91, 0.870), (0.999999, 0.900)])
def test_exact_joint_power_against_product(rho, expected):
    """orch_review_check.out: two conditions of power 0.90: exact 0.858 / 0.87 / 0.9 against the product 0.810."""
    assert close(cj.exact_joint_power_equal(0.90, rho), expected, 0.002)
    assert close(cj.product_power_equal(0.90, 2), 0.81, 1e-9)


def test_data_factors_c10_pooled():
    """orch_review_check.out section (8): 1.356 / 1.077 / 1.259."""
    r1, r2, r3 = R.C10Windows(False), R.C10Windows(True), R.Pooled()
    assert close(R.data_factor(r2, r1, 24.0), 1.356, 0.002)
    assert close(R.data_factor(r3, r1, 24.0), 1.077, 0.002)
    assert close(R.data_factor(r2, r3, 24.0), 1.259, 0.002)


def test_sr_eff_needed_c10():
    """DEC-105 erratum 2: 2.49 / 1.76 / 1.44 at 1 / 2 / 3 years per window."""
    got = [R.sr_eff_needed_c10(L) for L in (1, 2, 3)]
    assert [round(g, 2) for g in got] == [2.49, 1.76, 1.44]


def test_ppv_and_false_pass_reference():
    """orch_review_check.out (7): PPV 0.966 / 0.988 (C.10 today, 0.64), 0.973 / 0.991 (pooled 0.0025, 0.80), 0.640 / 0.842 (one window)."""
    assert close(R.ppv(0.64, 0.0025, 0.10), 0.966, 0.001) and close(R.ppv(0.64, 0.0025, 0.25), 0.988, 0.001)
    assert close(R.ppv(0.80, 0.0025, 0.10), 0.973, 0.001) and close(R.ppv(0.80, 0.0025, 0.25), 0.991, 0.001)
    assert close(R.ppv(0.80, 0.05, 0.10), 0.640, 0.001) and close(R.ppv(0.80, 0.05, 0.25), 0.842, 0.001)
    assert close(R.ppv(0.80, 0.01, 0.10), 0.899, 0.001)


# =====================================================================================================================
# 2. rule menu against orch_oc_check.out (R4, R5) and the OC derivation
# =====================================================================================================================
# (alpha_s, r): alpha_eff, MDE in SE_12, "Daten vs gepoolt ohne Screen", "(MDE/MDE_C10)^2", floor      [orch_oc_check.out]
ORCH_OC = {
    (0.05, 2): (0.001933, 2.7603, 1.1446, 1.2324, 2.4865), (0.05, 3): (0.001424, 2.5588, 1.4755, 1.0591, 2.4865),
    (0.05, 4): (0.001144, 2.5025, 1.8816, 1.0129, 2.4865),
    (0.10, 2): (0.002235, 2.6533, 1.0576, 1.1387, 2.1232), (0.10, 3): (0.001825, 2.3437, 1.2378, 0.8885, 2.1232),
    (0.10, 4): (0.001552, 2.2133, 1.4719, 0.7924, 2.1232),
    (0.20, 2): (0.002421, 2.5992, 1.0149, 1.0927, 1.6832), (0.20, 3): (0.002184, 2.1992, 1.0899, 0.7823, 1.6832),
    (0.20, 4): (0.001978, 1.9953, 1.1962, 0.6440, 1.6832),
    (0.50, 2): (0.002497, 2.5806, 1.0005, 1.0772, 0.8416), (0.50, 3): (0.002462, 2.1154, 1.0084, 0.7238, 0.8416),
    (0.50, 4): (0.002405, 1.8477, 1.0258, 0.5522, 0.8416),
}


@pytest.mark.parametrize("key", sorted(ORCH_OC))
def test_r4_screen_against_orchestrator_check(key):
    a_s, k = key
    t = 12.0 * k                       # r = 1/k of the data is the youngest 12-month window
    a_eff, mde, vs_pool, vs_c10, floor = ORCH_OC[key]
    rule = R.PooledScreen(a_s)
    assert close(rule.alpha_eff(t), a_eff, 0.002)
    d = rule.mde80(t)
    assert close(d, mde, 0.001)
    assert close((d / R.Pooled().mde80(t)) ** 2, vs_pool, 0.002)
    assert close((d / R.C80) ** 2, vs_c10, 0.002)
    assert close(rule.floor(), floor, 0.001)


def test_r4_data_factor_oc_definition():
    """OC derivation (a): data against C.10 per window for the same MDE: r 1/3 -> 1.5886, r 1/4 -> 2.0258 (alpha_s 0.05)."""
    rule, r1 = R.PooledScreen(0.05), R.C10Windows(False)
    assert close(R.data_factor(rule, r1, 24.0), 1.2324, 0.002)
    assert close(R.data_factor(rule, r1, 36.0), 1.5886, 0.002)
    assert close(R.data_factor(rule, r1, 48.0), 2.0258, 0.002)


@pytest.mark.parametrize("k,mde,vs_c10", [(2, 2.6942, 1.1741), (3, 2.1998, 0.7827), (4, 1.9051, 0.5870)])
def test_r5_p6_reading(k, mde, vs_c10):
    """orch_oc_check.out P-6 reading: MDE 2.6942 / 2.1998 / 1.9051 SE_12, alpha 0.002375, data against pooled 1.0905, no floor."""
    rule = R.PooledStability()
    t = 12.0 * k
    assert close(rule.mde80(t), mde, 0.001)
    assert close(rule.alpha_eff(t), 0.002375, 1e-6)
    assert close(R.data_factor(rule, R.Pooled(), t), 1.0905, 0.001)
    assert close((rule.mde80(t) / R.C80) ** 2, vs_c10, 0.002)
    assert rule.floor() == 0.0
    assert rule.t_required(rule.mde80(t)) == pytest.approx(t, rel=1e-9)


def test_r4_floor_makes_sesoi_unreachable():
    rule = R.PooledScreen(0.05)
    assert rule.t_required(rule.floor() * (1 - 1e-6)) == math.inf     # below the floor: never
    t = rule.t_required(2.9)
    assert math.isfinite(t) and rule.mde80(t) == pytest.approx(2.9, rel=1e-6)


@pytest.mark.parametrize("df,lo,hi", [(9, 1.25, 1.32), (14, 1.15, 1.19), (51, 1.03, 1.05), (1000, 1.0, 1.005)])
def test_t_limit_mde_factor(df, lo, hi):
    """OC derivation (e): t limits at alpha 0.0025 raise the MDE by 1.14 .. 1.38 for 7 .. 15 degrees of freedom; vanish for large n."""
    f = R.t_mde_factor(0.0025, df)
    assert lo < f["factor"] < hi and f["t_crit"] > f["z_crit"]
    assert R.t_mde_factor(0.0025, 10 ** 6)["factor"] == 1.0
    assert R.t_mde_factor(0.0025, 0.5)["factor"] is None and R.t_mde_factor(0.0025, 20, gate=0.7)["factor"] is None


def test_gate_makes_unreachable_target_inf():
    assert R.target_quantile(0.8, 0.7) == math.inf
    assert R.Pooled().mde80(24.0, 0.7) == math.inf
    assert R.PooledScreen(0.05).mde80(24.0, 0.7) == math.inf


@pytest.mark.parametrize("rule", [R.C10Windows(False), R.C10Windows(True), R.Pooled(), R.PooledScreen(0.2), R.PooledStability()])
def test_power_at_mde_and_t_required_roundtrip(rule):
    for t in (18.0, 36.0):
        d = rule.mde80(t)
        want = 0.64 if (isinstance(rule, R.C10Windows) and not rule.joint_target) else 0.80
        assert rule.power(d, t) == pytest.approx(want, abs=1e-6)
        assert rule.t_required(d) == pytest.approx(t, rel=1e-6)


# =====================================================================================================================
# 3. group-sequential engines (OC derivation (b); orch_review_check.out (6))
# =====================================================================================================================
@pytest.mark.parametrize("alpha,r_max,en_h1", [(0.05, 1.035, 0.814), (0.0025, 1.007, 0.871)])
def test_obf_four_looks(alpha, r_max, en_h1):
    d = gsd.grid_design(alpha, 4)
    assert close(d.r_max, r_max, 0.005) and close(d.en_h1, en_h1, 0.005)
    assert close(d.alpha_eff, alpha, 0.01)


def test_obf_boundaries_alpha_0025():
    """OC document (b): z boundaries 5.664 / 4.0051 / 3.2701 / 2.832 for alpha 0.0025."""
    z = gsd.grid_design(0.0025, 4).z_bounds
    for got, want in zip(z, (5.664, 4.0051, 3.2701, 2.832)):
        assert close(got, want, 0.003)


def test_gsd_futility_variant():
    """OC document (b) table: futility Z<0 at looks 1-3, alpha 0.0025: Max 1.0327, E[N|H1] 0.8627, E[N|H0] 0.5651."""
    d = gsd.grid_design(0.0025, 4, 0.8, True)
    assert close(d.r_max, 1.0327, 0.01) and close(d.en_h1, 0.8627, 0.01) and close(d.en_h0, 0.5651, 0.01)


def test_gsd_with_screen_monte_carlo():
    """OC document (b): GSD + recency screen at every stop, r 1/2: Max 1.0695, E[N|H1] 0.9125, alpha_eff 0.00217 (MC 1e6)."""
    d = gsd.mc_design(0.0025, 4, 0.8, 0.05, 0.5, False, 100_000)
    assert close(d.r_max, 1.0695, 0.02) and close(d.en_h1, 0.9125, 0.02)
    assert 0.0015 < d.alpha_eff < 0.0030


def test_report_exposes_gsd_maximum_and_expected_information(cases):
    """Spec rule R6: OBF 4 looks 0.0025: Maximum 1.007, E[N|H1] 0.871 (also with screen: 1.07 / 0.91 at r 1/2)."""
    _, rep = cases["KLASSE_W"]
    d = rep["rules"]["R6_K4"]["gsd_design_at_t_ref"]
    assert close(d["r_max"], 1.007, 0.005) and close(d["en_h1"], 0.871, 0.005) and d["looks"] == 4
    ds = rep["rules"]["R6_K4_screen"]["gsd_design_at_t_ref"]
    assert close(ds["r_max"], 1.0695, 0.03) and close(ds["en_h1"], 0.9125, 0.03) and ds["screen_alpha"] == 0.05
    assert close(d["expected_months_h1"], 24.0 / d["r_max"] * d["en_h1"], 1e-9)


def test_gsd_rule_interface():
    rule = R.GroupSequential(4, None, False, 20000)
    d = rule.mde80(24.0)
    assert close(d, R.Pooled().mde80(24.0) * math.sqrt(1.0074), 0.003)
    assert rule.power(d, 24.0) == pytest.approx(0.80, abs=2e-4)
    assert rule.floor() == 0.0


# =====================================================================================================================
# 4. SESOI curves (DEC-105 erratum 8; METHODEN_SWEEP; orch_review_check.out (5))
# =====================================================================================================================
@pytest.mark.parametrize("phi,rate,maker,taker,total", [(0.0, 0.500, 0.0096, 0.0263, 0.0359), (0.5, 0.333, 0.0064, 0.0175, 0.0239),
                                                       (0.8, 0.205, 0.0039, 0.0108, 0.0147)])
def test_single_position_persistence_ic_min(phi, rate, maker, taker, total):
    assert close(se.sign_change_rate(phi), rate, 0.002)
    assert close(se.ic_min_single_position(4, 262, phi=phi), maker, 0.01)
    assert close(se.ic_min_single_position(11, 262, phi=phi), taker, 0.003)
    assert close(se.ic_min_single_position(15, 262, phi=phi), total, 0.003)


def test_decile_frame_reference():
    """Taker 11 bp, sigma_xs 370 bp, full turnover (phi = -1): 0.0169; Maker 4 bp: 0.0062 (METHODEN_SWEEP, orch_sweep_check.py)."""
    assert close(se.ic_min_decile(11, 370, turnover=1.0), 0.0169, 0.005)      # references are rounded to 4 decimals
    assert close(se.ic_min_decile(4, 370, phi=-1.0), 0.0062, 0.01)
    assert close(se.ic_min_decile(11, 370, phi=0.0), se.ic_min_decile(11, 370, turnover=1.0) * 0.5, 1e-12)   # arccos(0)/pi = 0.5


def test_rank_ic_option_and_edge_factor():
    p = se.ic_min_single_position(11, 262, phi=0.0)
    r = se.ic_min_single_position(11, 262, phi=0.0, rank=True)
    assert r == pytest.approx(6.0 / math.pi * math.asin(p / 2.0)) and se.pearson_from_rank(r) == pytest.approx(p)
    assert se.EDGE_FACTOR == 0.798 and se.DECILE_FACTOR == 3.51


def test_sesoi_curve_over_horizon_scales_sigma_with_sqrt_time():
    rows = se.sesoi_curve("single_position", {"taker": 11.0}, None, 262.0, (0.0,), (1.0, 4.0))
    assert close(rows[0]["ic_min"] / rows[1]["ic_min"], 2.0, 1e-9)


def test_sesoi_input_errors():
    with pytest.raises(sc.FeasibilityInputError):
        se.sign_change_rate(1.5)
    with pytest.raises(sc.FeasibilityInputError):
        se.ic_min_decile(-1.0, 370.0, phi=0.0)
    with pytest.raises(sc.FeasibilityInputError):
        se.ic_min_single_position(11.0, 262.0)


# =====================================================================================================================
# 5. regression cases: the YAML files reproduce the dossier (every number is in the file with its source)
# =====================================================================================================================
@pytest.mark.parametrize("name", ["A1", "H27", "A2", "KLASSE_W"])
def test_regression_expected_values(cases, name):
    cand, rep = cases[name]
    rows = rp.compare_expected(rep, cand.expected)
    assert rows, "a regression case without expected values"
    bad = [r for r in rows if not r["ok"]]
    assert not bad, bad


@pytest.mark.parametrize("name", ["A1", "H27", "A2", "KLASSE_W"])
def test_regression_sources_are_complete(name):
    obj = yaml.safe_load((CASES / f"{name}.yaml").read_text(encoding="utf-8"))
    cand = sc.candidate_from_obj(obj)
    assert cand.nuisance.c_source.sha256 or cand.nuisance.c_source.derivation
    for e in cand.expected:
        assert e.source.sha256 and len(e.source.sha256) == 64 and e.source.file.startswith("scinance3-impl/")
    locs = list(sc._iter_sources(cand))
    assert locs and all((s.sha256 or s.derivation) for _, s in locs)


def test_a1_gl033(cases):
    """GL-033: A1 MDE80 129 bp against 36 bp: 12.8 years per window, SR_eff 1.95 < 2.49; structurally not testable for every rule."""
    _, rep = cases["A1"]
    assert close(rep["rules"]["R1"]["by_T"]["24"]["mde80"]["central"], 128.6, 0.005)
    assert close(rep["rules"]["R1"]["at_sesoi"]["central"]["years_per_window"], 12.8, 0.005)
    assert close(rep["prior"]["points"]["span_high"]["sr_eff"], 1.95, 0.005)
    assert rep["prior"]["label"] == "UNBELEGT" and "span_low" in rep["prior"]["points"]
    assert all(v["central"]["verdict"] != "testbar" for v in rep["verdict"]["by_rule"].values())
    assert rep["rules"]["R4_a05"]["at_sesoi"]["central"]["floor_blocks"] is True


def test_h27_gl034(cases):
    """GL-034 / DEC-105 erratum 6: SE12 5.17 VP; prior 7.14 -> 1183 days per window, 9.47 -> 673 (band 549 .. 6040)."""
    cand, rep = cases["H27"]
    assert close(rep["inputs"]["se12"]["central"], 5.17, 0.002)
    pts = rep["prior"]["points"]
    assert close(pts["median"]["r1"]["window_days"], 1183, 0.002)
    assert close(pts["pi2_old_central"]["r1"]["window_days"], 673, 0.002)
    assert close(pts["band_high"]["r1"]["window_days"], 549, 0.002) and close(pts["band_low"]["r1"]["window_days"], 6040, 0.002)
    # orch_review_check.out rows: SR_eff 1.832 / 1.381 / 2.027 / 0.611 and years per window 1.843 / 3.242 / 1.505 / 16.549
    for name, sr, yrs in (("pi2_old_central", 1.832, 1.843), ("median", 1.381, 3.242), ("band_high", 2.027, 1.505), ("band_low", 0.611, 16.549)):
        assert close(pts[name]["sr_eff"], sr, 0.002) and close(pts[name]["r1"]["window_years"], yrs, 0.003)
    assert all(v["central"]["verdict"] == "strukturell nicht testbar" for v in rep["verdict"]["by_rule"].values())
    assert rep["confirmation"]["V"]["usable"] is False


def test_a2_floor_double_statement_and_chain(cases):
    """DEC-105 erratum 7 and DEC-104 Nachtrag 2 (3): chain 18.8 -> 32.1 (quotient 1.707), 3.1 chain 28.06 / 1.355, floor 24.30 bp."""
    cand, rep = cases["A2"]
    assert close(rep["rules"]["R4_a05"]["floor"]["stress"], 24.30, 0.002)
    assert rep["rules"]["R4_a05"]["floor"]["stress"] > rep["sesoi"]["value"] > rep["rules"]["R4_a05"]["floor"]["central"]
    assert rep["rules"]["R4_a05"]["at_sesoi"]["stress"]["reachable"] is False
    ch = rep["strictness"]["chains"]
    assert close(ch["window_c10"]["quotient"], 1.707, 0.005) and ch["window_c10"]["needs_user_template"] is True
    assert close(ch["pooled_31"]["quotient"], 1.355, 0.002) and ch["pooled_31"]["needs_user_template"] is True
    assert close(ch["pooled_31"]["steps"]["q6"]["mde80"], 28.06, 0.001)
    f = [s["factor_vs_previous"] for s in ch["window_c10"]["steps"].values()][1:]
    assert math.prod(f) == pytest.approx(ch["window_c10"]["quotient"], rel=1e-9)        # decomposition is exact
    v = rep["conjunction"]["variants"]["three_plus_null"]
    for win, prod, pair in (("W1", 23.43, 22.93), ("W2", 24.36, 23.77)):
        c = v[win]["central"]["unscaled"]
        assert close(c["product"], prod, 0.005) and close(c["pair"], pair, 0.005)
        assert c["joint"] < c["pair"] < c["product"]                                     # exact is less strict than the product
    assert close(rep["conjunction"]["two_conditions_power_0_90"]["exact"], 0.858, 0.002)
    assert close(rep["pilot_handover"]["p_handover"]["16p5"], 7.1e-5, 0.01)
    assert rep["conjunction"]["inflation_vs_primary"]["central"]["product"] > 1.2
    assert any("primary statistic only" in w for w in rep["warnings"])


def test_a2_zone_rules(cases):
    cand, rep = cases["A2"]
    k = rep["confirmation"]["K"]
    assert k["effective_start"] == "2026-10-01"                      # BTC/ETH aggregates: first pure K date (FENSTERREGISTER section 6)
    assert rep["confirmation"]["V"]["usable"] is True                # A2 exception, discipline label
    assert any("moved to 2026-10-01" in w for w in rep["warnings"])


def test_klasse_w_floor_and_weeks(cases):
    """orch_oc_check.out: floors 0.0310 / 0.0448, pooled weeks 67.4 / 140.6; OC document: P-6 reading reaches 0.13 SD in 2027-07."""
    _, rep = cases["KLASSE_W"]
    r4 = rep["rules"]["R4_a05"]
    assert close(r4["floor"]["central"], 0.0310, 0.002) and close(r4["floor"]["stress"], 0.0448, 0.002)
    assert r4["at_sesoi"]["central"]["reachable"] and not r4["at_sesoi"]["stress"]["reachable"]
    assert close(rep["rules"]["R3"]["at_sesoi"]["central"]["n_units"], 67.4, 0.002)
    assert close(rep["rules"]["R3"]["at_sesoi"]["stress"]["n_units"], 140.6, 0.002)
    assert rep["rules"]["R5"]["at_sesoi"]["stress"]["decision_date"] == "2027-07-01"
    assert rep["rules"]["R4_a05"]["at_sesoi"]["central"]["decision_date"] == "2027-01-01"      # data exist at the cohort date
    # OC document (h): P-2 (a) fixed 67.84 weeks for SD 0.09
    assert close(r4["at_sesoi"]["central"]["n_units"], 67.84, 0.005)


def test_heavy_tail_block(cases):
    _, rep = cases["KLASSE_W"]
    h = rep["heavy_tail"]["per_rule"]
    assert h["R3"]["n_units_test"] == pytest.approx(rep["rules"]["R3"]["at_sesoi"]["central"]["n_units"])
    assert h["R3"]["factor"] > 1.0 and h["R3"]["t_crit"] > h["R3"]["z_crit"]       # 67 weekly clusters: t limit matters
    assert h["R6_K4"]["first_look_units"] == pytest.approx(h["R6_K4"]["t_months"] / 12 * 52 / 4)
    assert isinstance(h["R6_K4"]["meets_min_clusters_first_look"], bool)


def test_window_menu_present(cases):
    _, rep = cases["A1"]
    assert set(rep["design_menu"]["by_window"]) == {"6", "9", "12"}
    assert rep["design_menu"]["by_window"]["12"]["T_months"] == 24.0


# =====================================================================================================================
# 6. mandatory output rows (spec outputs 1-8)
# =====================================================================================================================
def test_report_has_all_mandatory_rows(cases):
    _, rep = cases["A2"]
    for key in ("rules", "exploration", "confirmation", "sr_equivalent", "conjunction", "strictness", "oc", "verdict",
                "reporting_rows", "design_menu", "sesoi", "inputs"):
        assert key in rep, key
    assert {"R1", "R2", "R3", "R4_a05", "R4_a10", "R4_a20", "R4_a50", "R5", "R6_K4", "R6_K4_screen"} <= set(rep["rules"])
    e = rep["exploration"]
    assert e["available"] and e["resolution_mde80"]["central"] > e["exclusion_limit_if_null"]["central"] > 0
    assert set(rep["confirmation"]) == {"V", "K"}
    assert set(rep["sr_equivalent"]["needed"]) == {"1y_per_window", "2y_per_window", "3y_per_window"}
    for set_name in ("at_t_required", "at_t_ref"):
        for k, row in rep["oc"][set_name].items():
            assert set(row["effects"]) >= {"zero", "sesoi"}, k
            assert all(e_["mc_within_4se"] for e_ in row["effects"].values()), (set_name, k, row["effects"])
    allowed = {"testbar", "nur Exploration", "strukturell nicht testbar"}
    assert {v[ln]["verdict"] for v in rep["verdict"]["by_rule"].values() for ln in ("central", "stress")} <= allowed


def test_reporting_rows_carry_dec105_fields(cases):
    _, rep = cases["A1"]
    need = {"zone", "estimate", "se", "ci95", "upper_limit95", "n_eff", "c_overlap", "selection_k", "shrinkage_note"}
    assert rep["reporting_rows"] and all(need <= set(r) for r in rep["reporting_rows"])
    r = rep["reporting_rows"][0]
    assert r["zone"] == "X" and r["estimate"].startswith("PLACEHOLDER") and "1.6449" in r["upper_limit95"]
    assert close(r["upper_limit95_if_estimate_zero"], 1.6449 * r["se"], 1e-4)
    assert {x["zone"] for x in rep["reporting_rows"]} >= {"X", "K"}


def test_oc_row_values(cases):
    _, rep = cases["KLASSE_W"]
    row = rep["oc"]["at_t_required"]["R3"]["effects"]
    assert row["zero"]["analytic"] == pytest.approx(0.0025, abs=1e-6)
    assert row["sesoi"]["analytic"] == pytest.approx(0.80, abs=1e-6)
    r1 = rep["oc"]["at_t_required"]["R1"]["effects"]["sesoi"]["analytic"]
    assert r1 == pytest.approx(0.64, abs=1e-6)                       # C.10: 0.80 per window = 0.64 joint
    assert rep["oc"]["mc_reps"] >= 1000
    r4 = rep["oc"]["at_t_required"]["R4_a05"]["effects"]
    assert 0.0 < r4["zero"]["analytic"] < 0.0025                      # effective alpha below the nominal 0.0025
    assert rep["oc"]["at_t_required"]["R3"]["ppv"]["base_rate_10pct"] == pytest.approx(R.ppv(0.8, 0.0025, 0.10), abs=1e-6)


def test_markdown_contains_mandatory_sections(cases):
    _, rep = cases["A2"]
    md = rp.to_markdown(rep)
    for head in ("## 1. MDE80", "## 2. Exploration", "## 3. SR-Aequivalent", "## 4. Konjunktionen", "## 5. Strenge-Quotient",
                 "## 6. OC-Zeile", "## 7. Verdikt", "## 8. Pflicht-Berichtszeilen"):
        assert head in md, head
    assert md.isascii() and "R4_a05" in md and "upper_limit95" in md and "exakt Paar" in md


def test_json_is_valid_ascii_and_has_no_nan(cases):
    _, rep = cases["H27"]
    text = rp.to_json(rep)
    assert text.isascii()
    back = json.loads(text)
    assert back["candidate"]["id"] == "H27"


def test_get_path_and_compare_expected():
    rep = {"a": {"b": [10, {"c": 2.0}]}}
    assert rp.get_path(rep, "a.b.1.c") == 2.0
    with pytest.raises(KeyError):
        rp.get_path(rep, "a.x")
    exp = (sc.Expected("a.b.1.c", 2.01, 0.01, sc.Source(derivation="t")), sc.Expected("a.b.1.c", 3.0, 0.01, sc.Source(derivation="t")),
           sc.Expected("a.q", 1.0, 0.01, sc.Source(derivation="t")))
    ok = [r["ok"] for r in rp.compare_expected(rep, exp)]
    assert ok == [True, False, False]


# =====================================================================================================================
# 7. determinism (T2)
# =====================================================================================================================
def test_two_runs_are_bit_identical():
    cand = sc.load_candidate(CASES / "KLASSE_W.yaml")
    a = rp.to_json(rp.evaluate(cand, mc_reps=1500, gsd_paths=10000, conjunction_mc=20000))
    b = rp.to_json(rp.evaluate(cand, mc_reps=1500, gsd_paths=10000, conjunction_mc=20000))
    assert a == b
    assert rp.to_markdown(json.loads(a)) == rp.to_markdown(json.loads(b))


def test_conjunction_monte_carlo_is_seeded():
    obj = yaml.safe_load((CASES / "A2.yaml").read_text(encoding="utf-8"))
    cand = sc.candidate_from_obj(obj)
    conj = cand.conjunction
    spec = rp._spec(conj, "W2", "central", False, ["P2", "P3fix", "P3all", "null_test"], 1.0)
    a = spec.mde80("joint", n=30000)
    b = spec.mde80("joint", n=30000)
    assert a == b and close(a, 22.3, 0.01)


# =====================================================================================================================
# 8. loud failures (C.14)
# =====================================================================================================================
@pytest.mark.parametrize("path", ["statistic", "nuisance", "sesoi", "data", "design_menu", "candidate_id", "title"])
def test_missing_top_level_field_fails(path):
    obj = base_candidate()
    del obj[path]
    with pytest.raises(sc.FeasibilityInputError, match="missing field"):
        sc.candidate_from_obj(obj)


@pytest.mark.parametrize("mod", [
    ("nuisance", "units_per_year"), ("nuisance", "cluster_unit"), ("nuisance", "c_overlap"),
    ("sesoi", "value"), ("sesoi", "label"), ("sesoi", "unit"), ("statistic", "unit"), ("statistic", "direction"),
    ("data", "cohort_date"), ("data", "selection_k"), ("data", "zones"), ("design_menu", "window_months"),
])
def test_missing_nested_field_fails(mod):
    obj = base_candidate()
    del obj[mod[0]][mod[1]]
    with pytest.raises(sc.FeasibilityInputError, match="missing field"):
        sc.candidate_from_obj(obj)


def test_missing_source_fails():
    obj = base_candidate()
    del obj["nuisance"]["sd_per_unit"]["central"]["source"]
    with pytest.raises(sc.FeasibilityInputError, match="source"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["nuisance"]["sd_per_unit"]["central"]["source"] = {"file": "x.md", "field": "f"}
    with pytest.raises(sc.FeasibilityInputError, match="sha256"):
        sc.candidate_from_obj(obj)


def test_unknown_field_fails():
    obj = base_candidate()
    obj["nuisance"]["se_12"] = 1.0
    with pytest.raises(sc.FeasibilityInputError, match="unknown field"):
        sc.candidate_from_obj(obj)


@pytest.mark.parametrize("c", [0.99, 0.0, -1.0])
def test_c_below_one_fails(c):
    obj = base_candidate()
    obj["nuisance"]["c_overlap"] = srcd(c)
    with pytest.raises(sc.FeasibilityInputError, match="c must be >= 1"):
        sc.candidate_from_obj(obj)
    assert make().nuisance.c_overlap == 1.0


@pytest.mark.parametrize("bad", [0.0, -3.0])
def test_nonpositive_se_or_sd_fails(bad):
    obj = base_candidate()
    obj["nuisance"]["sd_per_unit"]["central"] = srcd(bad)
    with pytest.raises(sc.FeasibilityInputError, match="must be > 0"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    del obj["nuisance"]["sd_per_unit"]
    obj["nuisance"]["se12"] = {"central": srcd(bad)}
    with pytest.raises(sc.FeasibilityInputError, match="must be > 0"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["nuisance"]["sd_per_unit"]["stress"] = srcd(bad)
    with pytest.raises(sc.FeasibilityInputError, match="must be > 0"):
        sc.candidate_from_obj(obj)


def test_se_and_sd_both_or_neither_fails():
    obj = base_candidate()
    obj["nuisance"]["se12"] = {"central": srcd(5.0)}
    with pytest.raises(sc.FeasibilityInputError, match="exactly one"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    del obj["nuisance"]["sd_per_unit"]
    with pytest.raises(sc.FeasibilityInputError, match="exactly one"):
        sc.candidate_from_obj(obj)


@pytest.mark.parametrize("start", ["2026-06-30", "2026-01-01", "2024-07-01"])
def test_zone_k_before_2026_07_01_fails(start):
    obj = base_candidate()
    obj["data"]["zones"]["K"]["start"] = start
    with pytest.raises(sc.FeasibilityInputError, match="zone K"):
        sc.candidate_from_obj(obj)


def test_zone_k_on_or_after_seal_is_accepted():
    obj = base_candidate()
    obj["data"]["zones"]["K"]["start"] = "2026-07-01"
    assert sc.candidate_from_obj(obj).data.k_start == dt.date(2026, 7, 1)


def test_unbelegt_without_span_fails():
    obj = base_candidate()
    obj["prior"] = {"label": "UNBELEGT"}
    with pytest.raises(sc.FeasibilityInputError, match="sensitivity span"):
        sc.candidate_from_obj(obj)
    obj["prior"] = {"label": "UNBELEGT", "median": srcd(5.0)}                 # a median alone is not a span
    with pytest.raises(sc.FeasibilityInputError, match="sensitivity span"):
        sc.candidate_from_obj(obj)
    obj["prior"] = {"label": "UNBELEGT", "sensitivity_span": [3.0, 9.0]}
    cand = sc.candidate_from_obj(obj)
    rep = rp.evaluate(cand, **SMALL)
    assert set(rep["prior"]["points"]) == {"span_low", "span_high"}              # symmetric: both ends, no worst-case default
    assert any("UNBELEGT" in w for w in rep["warnings"])


def test_unbelegt_span_must_be_ordered():
    obj = base_candidate()
    obj["prior"] = {"label": "UNBELEGT", "sensitivity_span": [9.0, 3.0]}
    with pytest.raises(sc.FeasibilityInputError, match="low must be < high"):
        sc.candidate_from_obj(obj)


def test_prior_other_label_needs_median_and_known_label():
    obj = base_candidate()
    obj["prior"] = {"label": "primaer"}
    with pytest.raises(sc.FeasibilityInputError, match="median"):
        sc.candidate_from_obj(obj)
    obj["prior"] = {"label": "made up", "median": srcd(1.0)}
    with pytest.raises(sc.FeasibilityInputError, match="prior.label"):
        sc.candidate_from_obj(obj)


def test_other_loud_failures():
    obj = base_candidate()
    obj["schema_version"] = 2
    with pytest.raises(sc.FeasibilityInputError, match="schema version"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["sesoi"]["unit"] = "IC"
    with pytest.raises(sc.FeasibilityInputError, match="must equal the statistic unit"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["data"]["knowledge_class"] = "everything"
    with pytest.raises(sc.FeasibilityInputError, match="knowledge_class"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["design_menu"]["mc_reps"] = 999
    with pytest.raises(sc.FeasibilityInputError, match=">= 1000"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["design_menu"]["window_months"] = [7]
    with pytest.raises(sc.FeasibilityInputError, match="window_months"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["data"]["zones"]["X"]["end"] = "2024-08-01"
    with pytest.raises(sc.FeasibilityInputError, match="zone X"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["data"]["zones"]["V"]["end"] = "2026-07-02"                           # zone V must end before the seal
    with pytest.raises(sc.FeasibilityInputError, match="zone V"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["data"]["zones"]["V"]["units"] = 100                                   # both months and units
    with pytest.raises(sc.FeasibilityInputError, match="exactly one of"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["nuisance"]["units_per_year"] = True
    with pytest.raises(sc.FeasibilityInputError, match="number"):
        sc.candidate_from_obj(obj)
    obj = base_candidate()
    obj["sesoi"] = {"mode": "decile", "unit": "bp", "label": "x"}
    with pytest.raises(sc.FeasibilityInputError, match="missing"):
        sc.candidate_from_obj(obj)


def test_evaluate_rejects_small_monte_carlo():
    cand = make()
    with pytest.raises(sc.FeasibilityInputError, match=">= 1000"):
        rp.evaluate(cand, mc_reps=999, gsd_paths=20000, conjunction_mc=20000)
    with pytest.raises(ValueError):
        R.simulate_rule(R.Pooled(), 1.0, 24.0, 1.0, 999, 1)


def test_computed_chain_without_conjunction_fails():
    obj = base_candidate()
    obj["chains"] = [{"id": "c", "label": "x", "kind": "computed", "steps": [{"id": "a", "label": "a"}, {"id": "b", "label": "b"}]}]
    with pytest.raises(sc.FeasibilityInputError, match="conjunction"):
        sc.candidate_from_obj(obj)


def test_vorwissen_v_zone_rule():
    cand = make(data__knowledge_class="btc_eth_aggregate")
    ok, note = cand.data.v_usable()
    assert ok is False and "not allowed" in note
    assert make(data__knowledge_class="btc_eth_aggregate", data__a2_exception=True).data.v_usable()[0] is True
    assert make(data__v_blind_confirmed=False).data.v_usable()[0] is False
    assert make().data.k_effective_start() == dt.date(2026, 7, 1)
    assert make(data__knowledge_class="btc_eth_aggregate").data.k_effective_start() == dt.date(2026, 10, 1)


# =====================================================================================================================
# 9. loading, path guard, sources, CLI
# =====================================================================================================================
def test_path_guard_refuses_protected_locations(tmp_path):
    run_dir = tmp_path / "state" / "runs"
    run_dir.mkdir(parents=True)
    f = run_dir / "cand.yaml"
    f.write_text("schema_version: 1\n", encoding="utf-8")
    with pytest.raises(sc.FeasibilityInputError, match="protected directory"):
        sc.load_candidate(f)
    harvest = tmp_path / "data" / "harvest"
    harvest.mkdir(parents=True)
    with pytest.raises(sc.FeasibilityInputError, match="protected directory"):
        sc.guard_path(harvest / "x.json")
    sealed = tmp_path / ("a_L_window" + "_sealed.json")
    with pytest.raises(sc.FeasibilityInputError, match="sealed"):
        sc.guard_path(sealed)
    with pytest.raises(sc.FeasibilityInputError, match="not found"):
        sc.load_candidate(tmp_path / "nothing.yaml")
    bad = tmp_path / "x.txt"
    bad.write_text("x", encoding="utf-8")
    with pytest.raises(sc.FeasibilityInputError, match="use .yaml"):
        sc.load_candidate(bad)


def test_json_candidate_roundtrip(tmp_path):
    p = tmp_path / "t1.json"
    p.write_text(json.dumps(base_candidate()), encoding="utf-8")
    cand = sc.load_candidate(p)
    assert cand.candidate_id == "T1" and cand.nuisance.se12_of("central") == pytest.approx(100.0 / math.sqrt(52.0))
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(sc.FeasibilityInputError, match="invalid JSON"):
        sc.load_candidate(p)


def test_verify_sources_reports_ok_drift_missing(tmp_path):
    doc = tmp_path / "scinance3-impl" / "x.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("hello", encoding="utf-8")
    good = sc.sha256_of_file(doc)
    obj = base_candidate()
    obj["nuisance"]["sd_per_unit"]["central"]["source"] = {"file": "scinance3-impl/x.md", "field": "f", "sha256": good}
    obj["nuisance"]["sd_per_unit"]["stress"]["source"] = {"file": "scinance3-impl/gone.md", "field": "f", "sha256": "1" * 64}
    obj["sesoi"]["value"]["source"] = {"file": "scinance3-impl/x.md", "field": "f", "sha256": "2" * 64}
    cand = sc.candidate_from_obj(obj)
    status = {(r["file"], r["status"]) for r in sc.verify_sources(cand, tmp_path)}
    assert ("scinance3-impl/x.md", "ok") in status and ("scinance3-impl/x.md", "drift") in status and ("scinance3-impl/gone.md", "missing") in status


def test_cli_end_to_end(capsys, tmp_path):
    rc = cli.main([str(CASES / "A1.yaml"), "--format", "json", "--mc-reps", "1500", "--gsd-paths", "10000", "--check-expected"])
    out = capsys.readouterr()
    assert rc == 0 and json.loads(out.out)["candidate"]["id"] == "A1" and "ok " in out.err
    rc = cli.main([str(CASES / "A1.yaml"), "--format", "md", "--mc-reps", "1500", "--gsd-paths", "10000"])
    assert rc == 0 and "# Feasibility 3.1: A1" in capsys.readouterr().out
    rc = cli.main([str(CASES / "A1.yaml"), "--out-dir", str(tmp_path / "o"), "--mc-reps", "1500", "--gsd-paths", "10000"])
    assert rc == 0 and (tmp_path / "o" / "A1.json").is_file() and (tmp_path / "o" / "A1.md").is_file()


def test_cli_exit_codes(capsys, tmp_path):
    bad = base_candidate()
    bad["nuisance"]["c_overlap"] = srcd(0.5)
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    assert cli.main([str(p)]) == 2
    assert "INPUT ERROR" in capsys.readouterr().err
    wrong = base_candidate()
    wrong["expected"] = [{"key": "inputs.se12.central", "value": 999.0, "source": dict(SRC)}]
    p2 = tmp_path / "wrong.json"
    p2.write_text(json.dumps(wrong), encoding="utf-8")
    assert cli.main([str(p2), "--format", "json", "--check-expected", "--mc-reps", "1000", "--gsd-paths", "1000", "--conjunction-mc", "1000"]) == 3
    assert cli.main([str(tmp_path / "missing.yaml")]) == 2
    assert cli.main([str(CASES / "A1.yaml"), "--out-dir", str(tmp_path / "state" / "runs" / "x")]) == 2


# =====================================================================================================================
# 10. hygiene: no network, no market data, no sealed files, no model names, ASCII (spec "Tests")
# =====================================================================================================================
STDLIB_OK = {"__future__", "ast", "argparse", "dataclasses", "datetime", "functools", "hashlib", "json", "math", "pathlib", "re",
             "sys", "typing"}
THIRD_OK = {"numpy", "scipy", "yaml"}
FORBIDDEN = {"socket", "ssl", "http", "urllib", "requests", "aiohttp", "websockets", "ftplib", "smtplib", "subprocess", "boto3", "s3fs",
             "duckdb", "polars", "pandas", "harvest_data", "asyncio", "os", "shutil", "tempfile", "glob", "pickle"}


def _imports(path: Path) -> set[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found.add((a.name, 0))
        elif isinstance(node, ast.ImportFrom):
            found.add((node.module or "", node.level))
    return found


def test_package_import_list_is_closed():
    files = sorted(PKG.glob("*.py"))
    assert {f.name for f in files} >= {"__init__.py", "rules.py", "sesoi.py", "report.py", "cli.py", "schema.py", "conjunction.py", "gsd.py"}
    for f in files:
        for mod, level in _imports(f):
            top = mod.split(".")[0]
            if level:                                              # relative import inside the package
                assert (f.parent / (mod.split(".")[0] + ".py")).is_file() or mod == "", (f.name, mod)
                continue
            assert top not in FORBIDDEN, (f.name, mod)
            assert top in STDLIB_OK | THIRD_OK, (f.name, mod)


def test_package_source_hygiene():
    banned_paths = ("state/" + "runs", "data/" + "harvest", "HARVEST" + "_S3", "weekly_ic" + "_series")
    banned_models = ("clau" + "de", "gpt", "opus", "sonnet", "haiku", "fable", "gemini", "llama")
    for f in sorted(PKG.glob("*.py")):
        text = f.read_text(encoding="utf-8")
        assert text.isascii(), f.name
        low = text.lower()
        for b in banned_paths:
            assert b.lower() not in low, (f.name, b)
        for b in banned_models:
            assert b not in low, (f.name, b)
    for f in sorted(CASES.glob("*.yaml")):
        t = f.read_text(encoding="utf-8")
        assert t.isascii() and "state/" + "runs" not in t, f.name


def test_cases_cite_no_sealed_or_forbidden_files():
    for f in sorted(CASES.glob("*.yaml")):
        cand = sc.load_candidate(f)
        for loc, src in sc._iter_sources(cand):
            if src.file:
                sc.guard_path(ROOT / src.file)                      # raises for protected locations / sealed names


def test_no_network_during_evaluation(monkeypatch):
    import socket

    def boom(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    cand = sc.load_candidate(CASES / "A1.yaml")
    rep = rp.evaluate(cand, mc_reps=1000, gsd_paths=2000, conjunction_mc=2000)
    assert rep["candidate"]["id"] == "A1"


def test_exploration_block_ts_reference():
    """orch_review_check.out (4): daily series N 2400: MDE80 0.0508, exclusion limit 0.0336 (SD 1, c 1)."""
    obj = base_candidate()
    obj["nuisance"] = {"cluster_unit": "day", "units_per_year": 365, "c_overlap": srcd(1.0), "sd_per_unit": {"central": srcd(1.0)}}
    obj["sesoi"] = {"mode": "direct", "unit": "bp", "label": "t", "value": srcd(0.03)}
    obj["data"]["zones"]["X"] = {"start": "2017-01-01", "end": "2024-05-31", "units": 2400}
    rep = rp.evaluate(sc.candidate_from_obj(obj), **SMALL)
    assert close(rep["exploration"]["resolution_mde80"]["central"], 0.0508, 0.002)
    assert close(rep["exploration"]["exclusion_limit_if_null"]["central"], 0.0336, 0.002)


@pytest.mark.parametrize("k,n,expected", [(600, 365, 0.0133), (600, 730, 0.0094), (600, 2130, 0.0055), (500, 365, 0.0146),
                                          (500, 2130, 0.0060), (300, 365, 0.0188), (300, 2130, 0.0078)])
def test_f1_cross_section_mde_reference(k, n, expected):
    """orch_review_check.out (3): MDE80 per window with SD(IC_t) = 2.5 / sqrt(K - 1) over N days."""
    obj = base_candidate()
    obj["nuisance"] = {"cluster_unit": "day", "units_per_year": 365,
                       "c_overlap": srcd(1.0), "sd_per_unit": {"central": srcd(2.5 / math.sqrt(k - 1))}}
    cand = sc.candidate_from_obj(obj)
    se12 = cand.nuisance.se12_of("central")
    t_window = 12.0 * n / 365.0
    assert close(R.C10Windows(False).mde80(2.0 * t_window) * se12, expected, 0.006)
