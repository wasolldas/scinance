"""T0 / T1 (panel cut) / T4 / T5 / T6 tests of the pure parts of the H-32 driver (``bybit_edge.research.h32_fm8``):
constants, panel cut and guards, estimators (SE rule P-1 (4), pilot statistics, signed selection ceiling, ``mu_sel``, BY / end
power), hand-over rule U, the pure gate, F-WEEK / BH, the registered-YAML schema and pins, the block permutation and the
legacy-import lock.  The expensive Vorlauf / pilot / test / positive-control runs are in ``test_h32_modes.py``."""
from __future__ import annotations

import ast
import copy
import json
import math
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest
from scipy import integrate

from bybit_edge.research import power_p1 as pp
from bybit_edge.research.h32_fm8 import (artifacts, calibration, estimators as est, fm8, fweek, gate, handover, panel_cut, permutation,
                                         pnull, schema)
from bybit_edge.research.h32_fm8 import constants as C
from bybit_edge.research.h32_fm8 import vorlauf, weekly as wkl
from bybit_edge.research.h32_fm8.errors import PanelCutError, PinError, ReplicatesError, SchemaError, SealError
from bybit_edge.research.wp13_xsec import characteristics, ic, nulls
from bybit_edge.research.wp7_universe import pit_universe

from tests.unit import h32_fixtures as F
from tests.unit.h32_fixtures import shrunk  # noqa: F401  (pytest fixture)

_N = NormalDist()


@pytest.fixture(scope="module")
def panel():
    return F.make_panel(seed=3, signal=0.08)


# ============================================================================
# constants and sources
# ============================================================================

def test_t0_constants_pins_and_sources():
    assert C.Z_KRIT == pytest.approx(1.6448536, abs=1e-7) and round(C.Z_KRIT, 7) == 1.6448536
    assert C.Z_POWER == pytest.approx(0.8416, abs=5e-5) and C.MDE_FAKTOR == 2.4865
    assert C.Z_KRIT + C.Z_POWER == pytest.approx(C.MDE_FAKTOR, abs=5e-5)           # the MDE factor, never a threshold
    assert C.BAND_Z == pytest.approx(1.2816, abs=5e-5) and C.T_MIN == 2.0 and C.ALPHA == 0.05
    assert (C.SEED, C.MEAN_BLOCK, C.N_BOOT_MIN, C.N_REPS_MIN, C.N_PERM, C.PERM_BLOCK) == (53, 4, 1000, 1000, 10_000, 4)
    assert C.NULL_LEVEL == pytest.approx(0.95) and C.LEAD_WEEKS == 8 and C.W_PILOT == 114
    assert C.W_JUDGED == {"P": 114, "W1": 52, "W2": 50} and C.K_MIN == {"P": 117, "W1": 134, "W2": 134}
    assert (C.BH_DENOMINATOR, C.BH_ALPHA, C.BY_ALPHA, C.FWEEK_DOUBLE_M, C.K_FAMILY) == (4, 0.10, 0.10, 11, 4)
    assert C.VARIANTS == ("mom1", "mom2", "mom4", "rev_gap") and C.DIRECTION["rev_gap"] == "negative"
    for d in (C.CUT_TEST, C.CUT_PILOT):                                              # both cuts end a complete week (Sunday)
        from datetime import date
        assert date.fromisoformat(d).isoweekday() == 7
    assert C.CUT_TEST == "2026-06-28" and C.CUT_PILOT == "2024-06-30"
    # ERSTFASSUNG 4: the criteria are the numbers of the binomial rule at 200 seeds
    assert C.PC_PASS_SHARE_MIN == pytest.approx(0.80 - 2.326 * math.sqrt(0.16 / 200), abs=5e-4)
    assert C.PC_NEG_PASS_MAX == pytest.approx(0.05 + 2.326 * math.sqrt(0.0475 / 200), abs=5e-4)
    assert len(C.PC_SEEDS_JUDGE) == 200 and (min(C.PC_SEEDS_JUDGE), max(C.PC_SEEDS_JUDGE)) == (53, 252)
    assert (min(C.PC_SEEDS_INJECT), max(C.PC_SEEDS_INJECT), min(C.PC_SEEDS_SIGMA_G), max(C.PC_SEEDS_SIGMA_G)) == (1000, 1049, 2000, 2049)


# ============================================================================
# B-0 / T1: the panel cut
# ============================================================================

def test_t1_cut_removes_every_day_after_the_cut_and_no_later_date_survives(panel):
    cut, rep = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    assert max(cut["dates"]) == C.CUT_TEST and cut["close"].shape[0] == len(cut["dates"]) == len(cut["day_index"]) == cut["turnover"].shape[0]
    assert rep["n_days_removed"] == len(panel["dates"]) - len(cut["dates"]) == 91 and rep["max_date"] == C.CUT_TEST
    assert panel_cut.assert_panel_max_date(cut, C.CUT_TEST) == C.CUT_TEST
    blob = repr(cut["dates"]) + repr([d for d in cut["last_alive_day"] if d])
    assert "2026-07" not in blob and "2026-08" not in blob and "2026-09" not in blob
    assert len(panel["dates"]) > len(cut["dates"])                                  # the input is untouched


def test_t1_cut_date_rules_sunday_limit_and_form():
    for bad, msg in (("2026-06-27", "Sunday"), ("2026-07-05", "limit"), ("2026/06/28", "ISO"), ("nope", "ISO")):
        with pytest.raises(PanelCutError, match=msg if msg != "limit" else "limit"):
            panel_cut.check_cut_date(bad, limit=C.CUT_TEST)
    assert panel_cut.check_cut_date("2024-06-30", limit=C.CUT_PILOT).isoweekday() == 7


def test_t1_max_date_guard_and_build_weekly_refuse_an_uncut_panel(panel):
    with pytest.raises(PanelCutError, match="not cut"):
        panel_cut.assert_panel_max_date(panel, C.CUT_TEST)
    with pytest.raises(PanelCutError, match="not cut"):
        wkl.build_weekly(panel, C.CUT_TEST)                                          # independent of whoever cut (or did not cut)
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_PILOT, limit=C.CUT_PILOT)
    wk = wkl.build_weekly(cut, C.CUT_PILOT)
    assert wk.weeks[-1] == "2024-06-24"
    with pytest.raises(PanelCutError, match="after the cut date"):
        panel_cut.assert_weeks_end_by(["2024-06-24", "2024-07-01"], C.CUT_PILOT)


def test_t1_a_cut_panel_equals_a_panel_that_ends_at_the_cut(panel):
    """Betas, characteristics, masks and returns of the cut panel are IDENTICAL to those of a panel that physically ends at
    the cut date (the violent shocks after 2026-06-28 of the fixture leave no trace)."""
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    n_cut = sum(1 for d in panel["dates"] if d <= C.CUT_TEST)
    manual = dict(panel)
    for k in ("close", "turnover", "funding_n", "funding_sum"):
        manual[k] = panel[k][:n_cut]
    manual["dates"], manual["day_index"] = panel["dates"][:n_cut], panel["day_index"][:n_cut]
    a, b = wkl.build_weekly(cut, C.CUT_TEST), wkl.build_weekly(manual, C.CUT_TEST)
    assert a.weeks == b.weeks and a.symbols == b.symbols
    for name in ("returns", "returns_est", "alive", "beta8", "returns_valid"):
        assert np.array_equal(getattr(a, name), getattr(b, name), equal_nan=True), name
    for v in C.VARIANTS:
        assert np.array_equal(a.chars[v], b.chars[v], equal_nan=True)
    # without the cut the grid reaches into the blind period
    from bybit_edge.research.wp7_universe import panel_load
    full = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    assert full["weeks"][-1] > a.weeks[-1]


def test_t1_cut_drops_symbols_without_data_and_nulls_later_delisting_dates():
    n_days = 21 * 7 // 7 * 7
    dates = [(np.datetime64("2024-06-10") + np.timedelta64(i, "D")).astype(str) for i in range(30)]       # 2024-06-10 .. 2024-07-09
    close = np.full((30, 3), np.nan)
    close[:, 0] = 100.0 + np.arange(30)
    close[:, 1] = 50.0                                                                 # delisted after the cut (2024-07-03)
    close[24:, 2] = 10.0                                                               # lists on 2024-07-04, after the cut
    p = {"symbols": ["A", "B", "C"], "dates": dates, "day_index": list(range(30)), "close": close, "turnover": close.copy(),
         "funding_n": np.zeros((30, 3)), "funding_sum": np.zeros((30, 3)), "last_alive_day": [None, "2024-07-03", None],
         "is_delisted": np.array([False, True, False]), "delisted_symbols": ["B"], "relisted_gaps": {}, "n_symbols_survivors": 2,
         "n_symbols_delisted": 1}
    cut, rep = panel_cut.cut_panel_days(p, "2024-06-30")
    assert cut["symbols"] == ["A", "B"] and rep["n_symbols_dropped_without_data"] == 1 and rep["n_last_alive_day_nulled"] == 1
    assert cut["last_alive_day"] == [None, None] and cut["close"].shape == (21, 2) and max(cut["dates"]) == "2024-06-30"


# ============================================================================
# estimators: SE rule P-1 (4), pilot statistics
# ============================================================================

def _series(n=114, seed=1, mean=0.03, sd=0.07):
    rng = np.random.default_rng(seed)
    return mean + sd * rng.standard_normal(n)


def test_t0_se_rule_takes_the_largest_of_floor_sd_and_bootstrap():
    x = _series(52)
    w = 52
    r = est.se_rule(x, 0.05, w, n_boot=200, seed=53)
    assert r["floor_term"] == pytest.approx(0.05 / math.sqrt(52)) and r["sd_term"] == pytest.approx(x.std(ddof=1) / math.sqrt(52))
    assert r["stat_term"] == pp.stationary_bootstrap_se(x, 4.0, 200, seed=53)
    assert r["se"] == max(r["floor_term"], r["sd_term"], r["stat_term"])
    assert est.se_rule(x, 5.0, w, n_boot=50)["se"] == pytest.approx(5.0 / math.sqrt(52))                    # floor binds
    ar = np.sin(2 * np.pi * np.arange(52) / 26.0) * 0.05 + 0.001 * np.random.default_rng(2).standard_normal(52)    # persistent
    r2 = est.se_rule(ar, 0.0001, w, n_boot=300, seed=53)
    assert r2["stat_term"] > r2["sd_term"] and r2["se"] == r2["stat_term"]                                   # autocorrelation: bootstrap binds
    nan = est.se_rule(np.array([0.1, np.nan]), 0.05, 52)
    assert math.isnan(nan["se"])                                                                              # fails closed
    s = est.se_rule(x, 0.05, w, n_boot=40, seed=53, with_sha=True)
    assert s["bootstrap_means_sha256"] == est.bootstrap_means_sha256(pp.stationary_bootstrap_means(x, 4.0, 40, seed=53))


def test_t0_pilot_statistics_known_values_band_and_pilot_nuisance():
    ic_w = _series(114, seed=5, mean=-0.02, sd=0.075)
    ic_w[10] = np.nan                                                                    # a NaN week does not enter W_P
    k = np.linspace(120, 340, 114)
    s = est.pilot_statistics(ic_w, k, -1, n_boot=300, seed=53)
    y = -ic_w[np.isfinite(ic_w)]
    kf = k[np.isfinite(ic_w)]
    assert s["w_p"] == 113 and s["x_p"] == pytest.approx(y.mean()) and s["sd_p"] == pytest.approx(y.std(ddof=1))
    b_p = np.mean(1 / np.sqrt(kf - 1))
    v_p = np.mean(1 / (kf - 1))
    se_stat = pp.stationary_bootstrap_se(y, 4.0, 300, seed=53)
    assert s["b_p"] == pytest.approx(b_p) and s["v_p"] == pytest.approx(v_p) and s["se_stat"] == se_stat
    assert s["se_p"] == pytest.approx(max(b_p / math.sqrt(113), y.std(ddof=1) / math.sqrt(113), se_stat))
    assert s["t_p"] == pytest.approx(s["x_p"] / s["se_p"])
    assert s["band80_normal"] == [pytest.approx(s["x_p"] - 1.2815515655 * s["se_p"]), pytest.approx(s["x_p"] + 1.2815515655 * s["se_p"])]
    lo, hi = s["band80_bootstrap_percentile"]
    assert lo < s["x_p"] < hi
    assert s["f2_real"] == pytest.approx(max(0.0, y.var(ddof=1) - v_p))
    assert s["c_real"] == pytest.approx(max(1.0, 113 * se_stat ** 2 / y.var(ddof=1)))
    flip = est.pilot_statistics(ic_w, k, +1, n_boot=300, seed=53)
    assert flip["x_p"] == pytest.approx(-s["x_p"]) and flip["se_p"] == s["se_p"]                       # the direction only flips the sign
    with pytest.raises(ValueError):
        est.pilot_statistics(ic_w[:2], k[:2], 1)


def test_t0_signed_selection_ceiling_matches_monte_carlo_and_differs_from_the_raw_one():
    """B-5: sign-adjusted E[max]; the raw ``nulls._mean_of_max`` of the third version takes the raw signs."""
    mu = {"mom1": 0.004, "mom2": 0.002, "mom4": 0.001, "rev_gap": 0.006}          # raw IC means; rev_gap is registered negative
    sd = 0.01
    signs = {"mom1": 1, "mom2": 1, "mom4": 1, "rev_gap": -1}
    rng = np.random.default_rng(0)
    n = 400_000
    draws = {v: mu[v] + sd * rng.standard_normal(n) for v in mu}
    got = est.signed_selection_ceiling(draws, signs)
    m = np.array([signs[v] * mu[v] for v in mu])
    F_ = lambda x: np.prod([_N.cdf((x - mi) / sd) for mi in m])                                   # noqa: E731
    lo, hi = float(m.min() - 8 * sd), float(m.max() + 8 * sd)
    ref = lo + integrate.quad(lambda x: 1.0 - F_(x), lo, hi)[0]                                    # E[M] = lo + int (1 - F)
    assert got == pytest.approx(ref, abs=4 * sd / math.sqrt(n) * 1.5)
    raw = nulls._mean_of_max({v: list(draws[v][:20000]) for v in mu}, tuple(mu), 20000)
    assert raw > got + 0.002                                                                       # unsigned: the rev_gap sign is wrong
    assert est.signed_selection_ceiling({"a": [np.nan, 0.1], "b": [np.nan, 0.2]}, {"a": 1, "b": 1}) == pytest.approx(0.2)


def test_t0_mu_sel_known_values_of_the_truncated_normal_and_the_median_property():
    c, se = 0.0206171, 0.00709                                                         # Review B-5 table (mom1)
    for k, expected in ((0.25, 0.0042), (0.5, 0.0166), (1.0, 0.0255), (2.0, 0.0346)):
        assert est.mu_sel(c + k * se, se, c) == pytest.approx(expected, abs=6e-5)
    assert est.mu_sel(0.01, se, 0.02) is None and est.mu_sel(0.02, se, 0.02) is None  # not handed over / on the threshold
    mus = [est.mu_sel(c + k * se, se, c) for k in (0.1, 0.5, 1, 2, 4)]
    assert all(a < b for a, b in zip(mus, mus[1:]))                                    # monotone in x_P
    assert est.mu_sel(c + 6 * se, se, c) == pytest.approx(c + 6 * se, abs=2e-4)        # far above the threshold: no adjustment
    # median property by simulation: P_mu(X >= x | X >= c) = 0.5 at mu = mu_sel
    x = c + 0.7 * se
    mu = est.mu_sel(x, se, c)
    rng = np.random.default_rng(3)
    draws = mu + se * rng.standard_normal(2_000_000)
    kept = draws[draws >= c]
    assert (kept >= x).mean() == pytest.approx(0.5, abs=0.004)


def test_t0_by_threshold_harmonic_number_and_end_power_reproduce_the_herleitung():
    assert est.harmonic_number(4) == pytest.approx(25 / 12)
    for m, thr in ((1, 0.1), (2, 0.0333333), (3, 0.0181818), (4, 0.012), (11, 0.00301036)):       # power_h32.json f_week_by_end_power
        assert est.by_threshold(m) == pytest.approx(thr, abs=2e-7)
    windows = {"W1": {"se_t": 0.00794043, "sd_t": 0.00794043, "null_mean": 0.000873366},
               "W2": {"se_t": 0.00642895, "sd_t": 0.00642895, "null_mean": 0.000542959}}
    prior = 0.0206171                                                                  # MDE80 of mom1 in W1
    for m, joint, z_eff in ((1, 0.744194, 1.64485), (2, 0.669589, 1.83391), (3, 0.554072, 2.09284), (4, 0.47644, 2.25713), (11, 0.256883, 2.74665)):
        ep = est.end_power(prior, m, windows)
        assert ep["joint"] == pytest.approx(joint, abs=3e-4) and ep["z_eff"] == pytest.approx(z_eff, abs=2e-4)
    assert est.end_power(prior, 1, windows)["window_power"]["W1"] == pytest.approx(0.8, abs=2e-4)
    assert est.end_power(0.03, 4, windows)["joint"] > est.end_power(0.02, 4, windows)["joint"]
    with pytest.raises(ValueError):
        est.by_threshold(0)


# ============================================================================
# hand-over rule U (T0 each condition, T4 purity, monotonicity)
# ============================================================================

def _consts(m_p=0.0005, null_mean=(0.0009, 0.0005), e_se=(0.0079, 0.0064), se_mean=(0.0079, 0.0064), v_fm8=(0.0025, 0.0020),
            q95=(0.0110, 0.0095)):
    # q95 small enough that the U component binds in the base case (U-3, DEC-101 Teil 2: threshold = max(U + m*, q95 + z_80 SD_T))
    wins = {wn: {"v_fm8": v_fm8[i], "e_se_rule": e_se[i], "se_mean": se_mean[i], "null_mean": null_mean[i], "w_judged": (52, 50)[i],
                 "q95": q95[i]}
            for i, wn in enumerate(("W1", "W2"))}
    return {"windows": wins, "m_p": m_p, "z_krit": C.Z_KRIT, "z_power": C.Z_POWER, "t_min": 2.0}


def _inputs(x_p=0.04, se_p=0.0071, f2=0.00026, c=1.08):
    return {"x_p": x_p, "se_p": se_p, "f2_real": f2, "c_real": c}


def test_t0_handover_rule_u_each_condition_alone_and_the_numbers():
    consts = _consts()
    ok = handover.evaluate_handover(_inputs(), consts)
    assert ok["handed_over"] and ok["status"] == "UEBERGEBEN" and ok["reason"] is None
    pil = {wn: math.sqrt(1.08) * math.sqrt(consts["windows"][wn]["v_fm8"] + 0.00026) / math.sqrt(consts["windows"][wn]["w_judged"]) for wn in ("W1", "W2")}
    for wn in ("W1", "W2"):
        assert ok["per_window"][wn]["se_w_pilot"] == pytest.approx(pil[wn])
        assert ok["per_window"][wn]["se_t"] == max(consts["windows"][wn]["e_se_rule"], pil[wn])
        assert ok["per_window"][wn]["sd_t"] == max(consts["windows"][wn]["se_mean"], pil[wn])
    comp = {wn: C.Z_KRIT * ok["per_window"][wn]["se_t"] + C.Z_POWER * ok["per_window"][wn]["sd_t"] for wn in ("W1", "W2")}
    assert ok["mde80_star"] == pytest.approx(max(comp.values())) and ok["m_star"] == 0.0009
    # (i) sign: a negative point fails (i) -- and then (ii) and (iii) fail as well
    neg = handover.evaluate_handover(_inputs(x_p=-0.04), consts)
    assert not neg["conditions"]["i"] and not neg["handed_over"] and neg["status"] == "GL-012 (Pilot)" and "(i)" in neg["reason"]
    # (ii) magnitude: just below / on the threshold
    thr = ok["threshold_on_point"]
    just_below = handover.evaluate_handover(_inputs(x_p=thr - 1e-6, se_p=0.0071), consts)
    assert just_below["conditions"] == {"i": True, "ii": False, "iii": True} and not just_below["handed_over"]
    assert handover.evaluate_handover(_inputs(x_p=thr + 1e-9), consts)["conditions"]["ii"]
    # (iii) t: a large SE_P with a point above the threshold fails only (iii)
    wide = handover.evaluate_handover(_inputs(x_p=0.05, se_p=0.03), consts)
    assert wide["conditions"] == {"i": True, "ii": True, "iii": False} and not wide["handed_over"]
    # the hand-over always lies in C10 under (ii); the A3-practice double statement is reported
    assert ok["regime_p1"]["regime"] == pp.REGIME_C10 and ok["regime_p1_consistent"] is True
    assert ok["regime_a3_practice"]["practice"] == "A3" and "mu_sel" in ok and ok["mu_sel"] is not None
    assert ok["power_at_mu_sel"]["joint"] <= ok["regime_p1"]["window_power_joint_product"] + 1e-9


def test_t0_handover_m_star_takes_the_pilot_null_mean_into_account():
    base = handover.evaluate_handover(_inputs(), _consts(m_p=0.0))
    big_mp = handover.evaluate_handover(_inputs(), _consts(m_p=0.004))
    assert big_mp["m_star"] == 0.004 and base["m_star"] == 0.0009                      # max(0, m_P, m_W1, m_W2)
    assert big_mp["threshold_on_point"] == pytest.approx(big_mp["mde80_star"] + 0.004)
    assert big_mp["threshold_on_point"] > base["threshold_on_point"]
    tight = handover.evaluate_handover(_inputs(x_p=base["threshold_on_point"] + 1e-4), _consts(m_p=0.0))
    loose = handover.evaluate_handover(_inputs(x_p=base["threshold_on_point"] + 1e-4), _consts(m_p=0.004))
    assert tight["handed_over"] and not loose["handed_over"]                           # a higher pilot null only removes hand-overs
    neg_null = handover.evaluate_handover(_inputs(), _consts(m_p=-0.01, null_mean=(-0.002, -0.003)))
    assert neg_null["m_star"] == 0.0                                                    # no credit for a negative null mean


def test_t4_handover_is_pure_and_monotone():
    consts, inp = _consts(), _inputs()
    assert handover.evaluate_handover(inp, consts) == handover.evaluate_handover(copy.deepcopy(inp), copy.deepcopy(consts))
    xs = np.linspace(0.0, 0.08, 33)
    flags = [handover.evaluate_handover(_inputs(x_p=x, se_p=0.0071), consts)["handed_over"] for x in xs]
    first = flags.index(True)
    assert all(flags[first:]) and not any(flags[:first])                               # a higher x_P never flips hand-over -> GL-012
    ses = [0.0071, 0.0080, 0.0095, 0.012, 0.03]
    f1 = [handover.evaluate_handover(_inputs(x_p=0.05, se_p=s), consts)["handed_over"] for s in ses]
    assert f1 == sorted(f1, reverse=True)                                               # a larger SE_P (t_P) never flips GL-012 -> hand-over
    nuis = [0.0, 0.0003, 0.001, 0.003, 0.006, 0.01]
    f2 = [handover.evaluate_handover(_inputs(x_p=0.03, f2=f), consts)["handed_over"] for f in nuis]
    assert f2[0] and not f2[-1] and f2 == sorted(f2, reverse=True)                      # a larger pilot nuisance (SE_T, SD_T) never flips GL-012 -> hand-over
    ms = [0.0, 0.005, 0.01, 0.02, 0.03]
    f3 = [handover.evaluate_handover(_inputs(x_p=0.05), _consts(m_p=m))["handed_over"] for m in ms]
    assert f3 == sorted(f3, reverse=True)                                               # nor a larger m*


# ============================================================================
# gate (T4 on a conserved payload), F-WEEK / BH
# ============================================================================

def _payload(y1=0.040, y2=0.035, se1=0.010, se2=0.009, q1=0.017, q2=0.015, ceil=0.0085, bounce=(None, None), variant="mom1"):
    thr = lambda e_se, nm: C.Z_KRIT * e_se + max(0.0, nm)                                          # noqa: E731
    return {"entry": f"H-32_{variant}", "variant": variant, "direction": C.DIRECTION[variant], "z_krit": C.Z_KRIT,
            "windows": {"W1": {"y": y1, "mean_ic": y1 if variant != "rev_gap" else -y1, "se_w": se1, "q95": q1, "ceiling_k4": ceil,
                               "threshold_frozen": thr(0.0105, 0.0009), "bounce_ic": bounce[0], "w_judged": 52},
                        "W2": {"y": y2, "mean_ic": y2 if variant != "rev_gap" else -y2, "se_w": se2, "q95": q2, "ceiling_k4": ceil,
                               "threshold_frozen": thr(0.0085, 0.0005), "bounce_ic": bounce[1], "w_judged": 50}}}


def test_t4_gate_arithmetic_on_a_conserved_payload_is_pure():
    p = _payload()
    v1, v2 = gate.evaluate(p), gate.evaluate(copy.deepcopy(p))
    assert v1 == v2 and v1["verdict"] == "PASS" and v1["c10_hard"] is True
    assert "vorlaeufig bis F-WEEK geschlossen (DEC-99 (7))" in v1["labels"]
    for wn in ("W1", "W2"):
        pw = v1["per_window"][wn]
        assert pw["a_sign"] and pw["b_magnitude"] and pw["c_null_quantile"]
        assert pw["threshold_t"] == pytest.approx(max(C.Z_KRIT * p["windows"][wn]["se_w"], p["windows"][wn]["q95"]))


@pytest.mark.parametrize("mut, cond", [
    ({"y1": -0.001}, "a_sign"), ({"y2": 0.0}, "a_sign"), ({"y1": 0.012, "q1": 0.001}, "b_magnitude"),           # y < 1.6449 * 0.010
    ({"y2": 0.014, "se2": 0.009, "q2": 0.020}, "c_null_quantile"),
])
def test_t0_gate_each_window_condition_drops_the_whole_entry(mut, cond):
    v = gate.evaluate(_payload(**mut))
    assert v["verdict"] == "DROP"
    bad = [wn for wn, pw in v["per_window"].items() if not pw[cond]]
    assert bad and "C.10 hart: mindestens ein Fenster erfuellt (1a)-(1c) nicht" in v["labels"]


def test_t0_gate_nan_and_zero_se_fail_closed_and_equal_to_threshold_passes():
    assert gate.evaluate(_payload(se1=float("nan")))["verdict"] == "DROP"
    assert gate.evaluate(_payload(se2=0.0))["verdict"] == "DROP"
    assert gate.evaluate(_payload(y1=float("nan")))["verdict"] == "DROP"
    thr = C.Z_KRIT * 0.010
    assert gate.evaluate(_payload(y1=thr, q1=thr - 1e-9, y2=0.035))["per_window"]["W1"]["b_magnitude"] is True


def test_t0_gate_preverdict_kill_ceiling_and_bounce_only_for_rev_gap():
    kill = gate.evaluate(_payload(ceil=0.02))
    assert kill["verdict"] == "DROP" and kill["gl012_kill"] and set(kill["kill_windows"]) == {"W1", "W2"}
    assert any("GL-012" in lab for lab in kill["labels"])
    one = _payload(ceil=0.0160)                                              # W1 frozen threshold 0.0182; W2 0.0143 -> only W2 killed
    assert gate.evaluate(one)["kill_windows"] == ["W2"]
    b = gate.evaluate(_payload(variant="rev_gap", y1=0.04, y2=0.035, bounce=(0.05, 0.0)))
    assert b["verdict"] == "DROP" and b["bounce_kill"] and b["bounce_windows"] == ["W1"] and any("Artefakt Bounce" in x for x in b["labels"])
    ok = gate.evaluate(_payload(variant="rev_gap", bounce=(0.001, -0.002)))
    assert ok["verdict"] == "PASS" and not ok["bounce_kill"]
    assert gate.evaluate(_payload(variant="mom1", bounce=(0.9, 0.9)))["verdict"] == "DROP"        # bounce is read if supplied (rev_gap only supplies it)


def test_t0_by_adjust_bh_report_and_fweek_demotion_with_the_double_statement():
    p = {"a": 0.001, "b": 0.02, "c": 0.5}
    by = fweek.by_adjust(p)
    assert by["m"] == 3 and by["single_bound"] == pytest.approx(est.by_threshold(3)) and by["reject"] == {"a": True, "b": True, "c": False}
    assert fweek.by_adjust({"x": 0.1}, m=1)["reject"]["x"] is True and fweek.by_adjust({"x": 0.1001})["reject"]["x"] is False
    with pytest.raises(ValueError):
        fweek.by_adjust(p, m=2)
    bh = fweek.bh_report({"mom1": 0.001, "rev_gap": 0.2})
    assert bh["m"] == 4 and bh["reject"]["mom1"] is True and bh["reject"]["mom2"] is False                # fixed denominator 4, p = 1 otherwise
    verdicts = {"H-32_mom1": gate.evaluate(_payload()), "H-32_rev_gap": gate.evaluate(_payload(variant="rev_gap"))}
    out = fweek.apply_fweek(verdicts, {"H-32_mom1": 0.0001, "H-32_rev_gap": 0.08})
    assert out["by"]["m"] == 2 and out["demoted"] == ["H-32_rev_gap"]
    assert verdicts["H-32_mom1"]["verdict"] == "PASS" and verdicts["H-32_rev_gap"]["verdict"] == "DROP"
    assert "F-WEEK-BY nicht bestanden" in verdicts["H-32_rev_gap"]["labels"]
    assert verdicts["H-32_mom1"]["fweek_double_statement"] == {"m": 11, "rejected": True, "report_only": True}      # old count m = 11
    assert verdicts["H-32_rev_gap"]["fweek_double_statement"]["rejected"] is False
    # not-handed entries (p = 1) are not in m: one tested entry -> bound 0.10, the old count 0.003
    solo = {"H-32_mom1": gate.evaluate(_payload())}
    o2 = fweek.apply_fweek(solo, {"H-32_mom1": 0.05})
    assert o2["by"]["m"] == 1 and solo["H-32_mom1"]["verdict"] == "PASS" and solo["H-32_mom1"]["fweek_double_statement"]["rejected"] is False
    wave = fweek.apply_fweek({"H-32_mom1": gate.evaluate(_payload())}, {"H-32_mom1": 0.05}, wave_p={"H-33": 0.9})
    assert wave["by"]["m"] == 2                                                          # other tested hypotheses of the wave count


# ============================================================================
# T5 / schema: pins against the YAML
# ============================================================================

@pytest.fixture(scope="module")
def reg_bundle():
    return F.get_bundle("null")


def test_t5_emitted_template_validates_and_pins_equal_the_code_constants(reg_bundle, shrunk):
    reg = reg_bundle["registered"]
    schema.validate_registered(reg)
    pins = schema.frozen_pin_table(reg)
    assert pins["n_perm"] == C.N_PERM and pins["seed"] == 53 and pins["mean_block"] == 4 and pins["w_pilot"] == 114
    assert pins["W1"]["w_judged"] == 52 and pins["W2"]["w_judged"] == 50 and pins["panel_cut_test"] == "2026-06-28"
    assert reg["z_krit"] == round(C.Z_KRIT, 7) and reg["alpha"] == 0.05 and reg["mde_faktor"] == 2.4865
    for key in ("pilot_window", "handover_rule", "fweek_counting", "fdr", "seal", "windows", "positive_control", "beta_control", "rules"):
        assert key in reg
    assert reg["handover_rule"]["version"] == "U-3" and reg["fdr"]["n_perm"] == C.N_PERM and reg["fdr"]["over_family"]["double_statement_m"] == 11
    for wn in ("W1", "W2"):
        fz = reg["windows"][wn]["frozen_v6"]
        for key in schema.FROZEN_VARIANT_KEYS:
            assert set(fz[key]) == set(C.VARIANTS)
        assert {"ceiling_k4", "floor_fm8", "v_fm8", "k_fm8_series_sha256"} <= set(fz)
        assert schema.threshold_frozen(reg, wn, "mom1") == pytest.approx(C.Z_KRIT * fz["e_se_rule"]["mom1"] + max(0.0, fz["null_mean"]["mom1"]))
    assert set(reg["pilot_window"]["frozen_v6"]["m_P"]) == set(C.VARIANTS)


def _drop(path):
    def f(reg):
        cur = reg
        for k in path[:-1]:
            cur = cur[k]
        del cur[path[-1]]
    return f


def _set(path, value):
    def f(reg):
        cur = reg
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value
    return f


@pytest.mark.parametrize("mutate, exc", [
    (_drop(("pilot_window",)), SchemaError), (_drop(("handover_rule",)), SchemaError), (_drop(("fdr",)), SchemaError),
    (_drop(("seal",)), SchemaError), (_drop(("fweek_counting",)), SchemaError),
    (_drop(("windows", "W2", "frozen_v6", "e_se_rule")), SchemaError), (_drop(("windows", "W1", "frozen_v6", "ceiling_k4")), SchemaError),
    (_set(("windows", "W1", "frozen_v6", "se_mean", "mom1"), None), SchemaError),
    (_set(("pilot_window", "frozen_v6", "m_P", "rev_gap"), None), SchemaError),
    (_set(("windows", "W2", "frozen_v6", "k_fm8_series_sha256"), "xyz"), SchemaError),
    (_set(("rules", "bounce_spread"), None), SchemaError), (_set(("data_fingerprints", "union_range_fingerprint"), None), SchemaError),
    (_set(("z_krit",), 2.4865), PinError), (_set(("z_krit",), 1.96), PinError), (_set(("alpha",), 0.01), PinError),
    (_set(("mde_faktor",), 1.6449), PinError), (_set(("fdr", "n_perm"), 1000), PinError), (_set(("fdr", "seed"), 54), PinError),
    (_set(("rules", "seed"), 7), PinError), (_set(("rules", "mean_block"), 3), PinError), (_set(("rules", "n_boot"), 10), PinError),
    (_set(("rules", "n_reps"), 10), PinError), (_set(("rules", "null_level"), 0.9936), PinError),
    (_set(("windows", "W1", "w_judged"), 51), PinError), (_set(("windows", "W2", "w_judged"), 51), PinError),
    (_set(("windows", "W2", "end"), "2026-06-30"), PinError), (_set(("pilot_window", "w_pilot"), 117), PinError),
    (_set(("pilot_window", "end"), "2024-07-07"), PinError), (_set(("seal", "panel_cut_test"), "2026-07-05"), PinError),
    (_set(("seal", "panel_cut_pilot"), "2024-07-07"), PinError), (_set(("seal", "stress_list_date_filter"), False), PinError),
    (_set(("handover_rule", "t_min"), 1.0), PinError), (_set(("handover_rule", "prior_reading"), "lower80"), PinError),
    (_set(("handover_rule", "version"), "U-1"), PinError), (_set(("selection", "K"), 7), PinError),
    (_set(("beta_control", "method"), "ts_resid_8w"), PinError), (_set(("primary_statistic",), "raw_ic"), PinError),
    (_set(("positive_control", "criteria", "pass_share_min"), 0.5), PinError), (_set(("positive_control", "seeds"), [53, 100]), PinError),
    (_set(("fweek_counting", "double_statement_m"), 7), PinError), (_set(("fdr", "over_family", "double_statement_m"), 7), PinError),
    # DEC-99 p convention: the binding p comes from the pinned v6 replicates
    (_set(("fdr", "p_source"), "block_permutation"), PinError), (_drop(("fdr", "p_source")), PinError),
    (_set(("fdr", "p_statistic"), "block_permutation_fm8_window_mean"), SchemaError), (_set(("fdr", "n_reps"), 5), PinError),
    (_set(("fdr", "n_reps"), 1.5), PinError), (_set(("fdr", "report_only"), []), PinError),
    (_set(("fdr", "replicates_sha256"), "xyz"), SchemaError), (_drop(("fdr", "replicates_sha256")), SchemaError),
    # DEC-100: fingerprint over the Data-Harvest delisting register (and the optional file-level tree hash)
    (_set(("data_fingerprints", "delisting_register_sha256"), None), SchemaError),
    (_drop(("data_fingerprints", "delisting_register_sha256")), SchemaError),
    (_set(("data_fingerprints", "delisted_tree_sha256"), "xyz"), SchemaError),
])
def test_t5_pre_flight_refuses_missing_or_changed_constants(reg_bundle, shrunk, mutate, exc):
    reg = copy.deepcopy(reg_bundle["registered"])
    mutate(reg)
    with pytest.raises(exc):
        schema.validate_registered(reg)


def test_t5_a_hypothesis_set_other_than_the_four_variants_is_refused(reg_bundle, shrunk):
    reg = copy.deepcopy(reg_bundle["registered"])
    reg["hypotheses"]["H-32_vol_rv"] = {"hypothesis": "H-32", "variant": "vol_rv", "direction": "negative"}
    with pytest.raises(SchemaError):
        schema.validate_registered(reg)
    reg2 = copy.deepcopy(reg_bundle["registered"])
    reg2["hypotheses"]["H-32_mom2"]["direction"] = "negative"
    with pytest.raises(SchemaError):
        schema.validate_registered(reg2)
    reg3 = copy.deepcopy(reg_bundle["registered"])
    reg3["hypotheses"]["H-32_mom2"]["status"] = "gl012_pre_run"
    with pytest.raises(SchemaError):
        schema.validate_registered(reg3)


# ============================================================================
# p convention (DEC-99): exceedance share of the pinned v6 null replicates
# ============================================================================

def test_t0_p_formula_is_the_exceedance_share_with_the_plus_one_convention():
    d = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    r = pnull.replicate_pvalue(0.03, d)                                              # >= : 0.03, 0.04, 0.05
    assert r["count_ge"] == 3 and r["p_value"] == pytest.approx(4 / 6) and r["n_reps"] == 5 and r["n_nan"] == 0
    assert pnull.replicate_pvalue(0.06, d)["p_value"] == pytest.approx(1 / 6)         # nothing exceeds: the floor 1 / (1 + R)
    assert pnull.replicate_pvalue(-1.0, d)["p_value"] == 1.0                          # everything exceeds
    assert pnull.replicate_pvalue(0.05, d)["count_ge"] == 1                           # a tie counts (>=)
    nan_d = np.array([0.01, np.nan, 0.03])
    rn = pnull.replicate_pvalue(0.02, nan_d)
    assert rn["count_ge"] == 2 and rn["p_value"] == pytest.approx(3 / 4) and rn["n_nan"] == 1       # a NaN replicate is an exceedance
    assert math.isnan(pnull.replicate_pvalue(float("nan"), d)["p_value"]) and math.isnan(pnull.replicate_pvalue(0.1, np.empty(0))["p_value"])
    assert pnull.replicate_pvalue(1e9, np.arange(1000.0))["p_value"] == pytest.approx(1 / 1001)       # R = 1000: resolution 0.001
    ys = np.linspace(-0.1, 0.1, 21)
    ps = [pnull.replicate_pvalue(float(y), np.linspace(-0.05, 0.05, 101))["p_value"] for y in ys]
    assert all(a >= b for a, b in zip(ps, ps[1:]))                                    # non-increasing in the observed mean
    assert pnull.replicate_pvalue(0.03, list(d))["p_value"] == r["p_value"]           # lists are accepted, same hash of the draws
    assert pnull.replicate_pvalue(0.03, list(d))["draws_sha256"] == r["draws_sha256"]


def test_t0_binding_cell_is_the_one_with_the_larger_null_mean():
    free = {"mom1": 0.001, "mom2": 0.004, "mom4": 0.002, "rev_gap": 0.0}
    drift = {"mom1": 0.003, "mom2": 0.004, "mom4": 0.001, "rev_gap": float("nan")}
    assert pnull.binding_cells(free, drift) == {"mom1": "drifting", "mom2": "driftfree", "mom4": "driftfree", "rev_gap": "driftfree"}
    assert pnull.binding_cells({**free, "mom1": float("nan")}, drift)["mom1"] == "drifting"
    with pytest.raises(ReplicatesError):
        pnull.binding_cells({**free, "mom1": float("nan")}, {**drift, "mom1": float("nan")})


def _p_variant(bundle, tmp_path, mutate_payload=None, mutate_reg=None):
    """Write a (possibly tampered) replicates file and a registration pinned to it (or not)."""
    payload = json.loads(bundle["p_rep_path"].read_text(encoding="utf-8"))
    if mutate_payload:
        mutate_payload(payload)
    path = tmp_path / "p.json"
    artifacts.write_json(path, payload)
    reg = copy.deepcopy(bundle["registered"])
    reg["fdr"]["replicates_sha256"] = artifacts.sha256_file(path)
    if mutate_reg:
        mutate_reg(reg)
    return path, reg


def test_t5_p_replicates_load_pin_and_belong_to_the_frozen_constants(reg_bundle, shrunk, tmp_path):
    reg = reg_bundle["registered"]
    p = pnull.load_replicates(reg_bundle["p_rep_path"], reg)
    assert p["_file_sha256"] == reg["fdr"]["replicates_sha256"] and p["n_reps"] == reg["fdr"]["n_reps"] == C.N_REPS_MIN
    for wn in ("W1", "W2"):
        for v in C.VARIANTS:
            d = pnull.draws_for(p, wn, v)
            assert d.size == p["n_reps"] and p["windows"][wn]["cell"][v] in ("driftfree", "drifting")
            fin = d[:reg["rules"]["n_reps"]]
            assert float(np.nanmean(fin)) == pytest.approx(reg["windows"][wn]["frozen_v6"]["null_mean"][v], rel=1e-12)
    # the file must hash to the pinned sha256: any other byte is refused
    other = tmp_path / "other.json"
    other.write_bytes(reg_bundle["p_rep_path"].read_bytes() + b" ")
    with pytest.raises(ReplicatesError, match="sha256"):
        pnull.load_replicates(other, reg)
    with pytest.raises(ReplicatesError, match="not found"):
        pnull.load_replicates(tmp_path / "none.json", reg)
    with pytest.raises(SealError):
        pnull.load_replicates(tmp_path / "ic_series_W1_UNION_REAL.csv", reg)
    # consistent pin, but the content does not belong to this registration
    path, reg2 = _p_variant(reg_bundle, tmp_path, mutate_reg=lambda r: r["fdr"].__setitem__("n_reps", r["fdr"]["n_reps"] + 1))
    with pytest.raises(ReplicatesError, match="n_reps"):
        pnull.load_replicates(path, reg2)
    path, reg3 = _p_variant(reg_bundle, tmp_path, mutate_reg=lambda r: r["windows"]["W1"]["frozen_v6"]["null_mean"].__setitem__("mom1", 0.123))
    with pytest.raises(ReplicatesError, match="null_mean"):
        pnull.load_replicates(path, reg3)
    path, reg4 = _p_variant(reg_bundle, tmp_path, mutate_payload=lambda d: d.__setitem__("cut_date", "2026-06-21"))
    with pytest.raises(ReplicatesError, match="cut date"):
        pnull.load_replicates(path, reg4)
    path, reg5 = _p_variant(reg_bundle, tmp_path, mutate_payload=lambda d: d["windows"].pop("W2"))
    with pytest.raises(ReplicatesError, match="W2"):
        pnull.load_replicates(path, reg5)
    path, reg6 = _p_variant(reg_bundle, tmp_path, mutate_payload=lambda d: d["windows"]["W1"]["variants"]["mom2"].pop())
    with pytest.raises(ReplicatesError, match="mom2"):
        pnull.load_replicates(path, reg6)
    path, reg7 = _p_variant(reg_bundle, tmp_path, mutate_payload=lambda d: d.__setitem__("p_source", "block_permutation"))
    with pytest.raises(ReplicatesError, match="not an H-32"):
        pnull.load_replicates(path, reg7)


def test_t5_p_replicates_payload_is_deterministic_and_its_hash_is_known_before_the_file_exists(reg_bundle, shrunk, tmp_path):
    rep = reg_bundle["report"]
    assert rep["p_replicates"]["file_sha256"] == artifacts.json_file_sha256(rep["_p_payload"]) == reg_bundle["registered"]["fdr"]["replicates_sha256"]
    out = tmp_path / "o"
    out.mkdir()
    assert artifacts.write_json(out / "x.json", rep["_p_payload"])["sha256"] == rep["p_replicates"]["file_sha256"]
    with pytest.raises(ReplicatesError):
        pnull.build_payload({"W1": {"cell": dict.fromkeys(C.VARIANTS, "driftfree"), "draws": dict.fromkeys(C.VARIANTS, np.zeros(3))},
                             "W2": {"cell": dict.fromkeys(C.VARIANTS, "driftfree"), "draws": dict.fromkeys(C.VARIANTS, np.zeros(4))}},
                            cut_date=C.CUT_TEST, n_reps=3, n_reps_constants=3, seed=53)


# ============================================================================
# block permutation
# ============================================================================

def test_t0_fast_spearman_is_bit_identical_to_the_third_version_and_ranks_with_ties():
    rng = np.random.default_rng(1)
    for n in (10, 57, 300):
        x, y = rng.standard_normal(n), rng.standard_normal(n)
        y[: n // 5] = 0.0                                                          # ties (delisting weeks carry outcome 0.0)
        assert permutation._spearman(x, y) == pit_universe.spearman_rank_ic(x, y)


def test_t0_permuted_week_ic_with_the_identity_reproduces_fm8_bit_for_bit_incl_the_nan_beta_path(panel):
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    wk = wkl.build_weekly(cut, C.CUT_TEST)
    win = wkl.make_window(wk, "W1")
    chars = {v: win.chars[v] for v in C.VARIANTS}
    rows = np.arange(1, win.n_weeks)
    out = permutation.permuted_week_ic(chars, win.returns, win.alive, win.beta8, rows,
                                       rank_cache=permutation._build_rank_cache(chars, win.alive))
    for v in C.VARIANTS:
        assert np.array_equal(np.array(fm8.window_ic(win, v)["ic_weekly"]), out[v], equal_nan=True)
    # NaN betas of alive symbols (not valid for the cache fast path) and NaN characteristics: still bit-identical
    beta = win.beta8.copy()
    beta[3, :7] = np.nan
    beta[9, 20:25] = np.nan
    chars2 = {"mom1": win.chars["mom1"].copy()}
    chars2["mom1"][5, 2:4] = np.nan
    ref = fm8.fm8_weekly_ic(chars2["mom1"], win.returns, win.alive, beta, win.symbols)
    out2 = permutation.permuted_week_ic(chars2, win.returns, win.alive, beta, rows,
                                        rank_cache=permutation._build_rank_cache(chars2, win.alive))
    assert np.array_equal(np.array([w["ic"] for w in ref["weekly"]]), out2["mom1"], equal_nan=True)
    out3 = permutation.permuted_week_ic(chars2, win.returns, win.alive, beta, rows, rank_cache=None)
    assert np.array_equal(out2["mom1"], out3["mom1"], equal_nan=True)


def test_t0_block_permutation_draws_are_deterministic_and_pair_no_formation_week_with_its_own_week(panel):
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    wk = wkl.build_weekly(cut, C.CUT_TEST)
    win = wkl.make_window(wk, "W1")
    chars = {"mom1": win.chars["mom1"], "rev_gap": win.chars["rev_gap"]}
    a = permutation.block_permutation_draws(chars, win.returns, win.alive, win.beta8, n_perm=12, seed=53)
    b = permutation.block_permutation_draws(chars, win.returns, win.alive, win.beta8, n_perm=12, seed=53)
    c = permutation.block_permutation_draws(chars, win.returns, win.alive, win.beta8, n_perm=12, seed=54)
    assert all(np.array_equal(a[v], b[v]) for v in chars) and not np.array_equal(a["mom1"], c["mom1"])
    assert a["rev_gap"].shape == (12,) and np.isfinite(a["mom1"]).all()
    # the permuted objects are the w_judged OUTCOME weeks: with 52 / 50 outcome weeks no draw pairs formation week t with the
    # outcome of its own week (outcome index t - 1), which would give a rank IC ~0.9 in the null
    rng = np.random.default_rng(53)
    for n_out, may_hit_two_back in ((52, False), (50, True)):
        for _ in range(3000):
            perm = nulls.block_permute_week_index(n_out, 4, rng)
            t = np.arange(n_out)
            assert not np.any(perm == t - 1)
            if not may_hit_two_back:
                assert not np.any(perm == t - 2)
    # p value: continuity correction (1 + count) / (1 + n), one-sided, NaN draws ignored
    d = np.array([0.0, 0.01, 0.02, 0.03, np.nan])
    pv = permutation.permutation_pvalue(0.02, d)
    assert pv["p_value"] == pytest.approx((1 + 2) / (1 + 4)) and pv["n_finite"] == 4 and pv["count_ge"] == 2
    assert math.isnan(permutation.permutation_pvalue(float("nan"), d)["p_value"])
    assert permutation.permutation_pvalue(1.0, d)["p_value"] == pytest.approx(1 / 5)


# ============================================================================
# windows, K series, calibration guard, stress coverage, sealed paths
# ============================================================================

def test_t0_windows_have_the_registered_geometry_and_k_fm8_equals_the_ic_cross_section(panel):
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    wk = wkl.build_weekly(cut, C.CUT_TEST)
    geo = {}
    for wn in ("P", "W1", "W2"):
        win = wkl.make_window(wk, wn)
        geo[wn] = wkl.window_geometry_report(win)
        assert win.w_judged == C.W_JUDGED[wn] and win.alive_ext.shape[0] == win.n_weeks + 8
        k8 = wkl.k_fm8_series(win)
        res = fm8.window_ic(win, "mom1")
        assert np.array_equal(k8, np.array(res["k_weekly"]))                      # K_fm8 (from returns_valid) == the cross-section of the IC
        floor, v = wkl.floor_and_v(k8)
        assert floor == pytest.approx(np.mean(1 / np.sqrt(k8 - 1.0))) and v == pytest.approx(np.mean(1 / (k8 - 1.0)))
        assert wkl.int_series_sha256(k8) == wkl.int_series_sha256(k8.copy())
    assert geo["P"]["first_formation_week"] == "2022-04-18" and geo["P"]["last_formation_week"] == "2024-06-17"
    assert geo["P"]["first_outcome_week"] == "2022-04-25" and geo["P"]["last_outcome_week"] == "2024-06-24"
    assert geo["W1"]["first_formation_week"] == "2024-07-01" and geo["W1"]["last_formation_week"] == "2025-06-23"
    assert geo["W1"]["first_outcome_week"] == "2024-07-08" and geo["W1"]["last_outcome_week"] == "2025-06-30"
    assert geo["W2"]["first_formation_week"] == "2025-07-07" and geo["W2"]["last_formation_week"] == "2026-06-15"
    assert geo["W2"]["first_outcome_week"] == "2025-07-14" and geo["W2"]["last_outcome_week"] == "2026-06-22"
    with pytest.raises(Exception):
        wkl.make_window(wk, "W1", "2021-10-04", "2021-12-30")                       # fewer than 8 lead weeks in front of it


def test_t0_k_minimum_kill_is_loud(panel):
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    wk = wkl.build_weekly(cut, C.CUT_TEST)
    win = wkl.make_window(wk, "W1")
    assert wkl.check_k_min(win, 134)["min"] >= 134
    with pytest.raises(Exception, match="Kill"):
        wkl.check_k_min(win, 10_000)


def test_t0_seal_guard_refuses_outcome_weeks_outside_the_range():
    fm8.guard_outcome_weeks(["2022-04-18", "2022-04-25", "2024-06-24"], C.PILOT_OUTCOME_FIRST, C.PILOT_OUTCOME_LAST)
    with pytest.raises(SealError):
        fm8.guard_outcome_weeks(["2022-04-18", "2022-04-25", "2024-07-01"], C.PILOT_OUTCOME_FIRST, C.PILOT_OUTCOME_LAST)
    with pytest.raises(SealError):
        fm8.guard_outcome_weeks(["2022-04-11", "2022-04-18", "2024-06-24"], C.PILOT_OUTCOME_FIRST, C.PILOT_OUTCOME_LAST)
    assert fm8.outcome_bounds("W2") == ("2025-07-14", "2026-06-22") and fm8.outcome_bounds("W1") == ("2024-07-08", "2025-06-30")


def test_t0_pilot_period_calibration_guard_refuses_any_mean_key():
    calibration.assert_no_mean_keys({"sigma_f": 0.05, "rho_f_measured": 0.01, "calibration": {"stress": {"beta_sd_calibrated": 0.4}}})
    for bad in ({"btc_mean": 0.001}, {"x": {"weekly_mean_return": 0.1}}, {"drift_f": 0.002}, {"l": [{"avg_ret": 1}]}):
        with pytest.raises(SealError):
            calibration.assert_no_mean_keys(bad)


def test_t1_stress_lists_are_read_with_a_date_filter_only(tmp_path):
    f = tmp_path / "stress_rel.json"
    f.write_text('{"days": ["2024-08-05", "2025-04-07", "2026-06-20", "2026-07-01", "2026-08-19"]}', encoding="utf-8")
    rep = vorlauf.stress_coverage_filtered(f, "2025-07-01", "2026-06-28", C.CUT_TEST)
    assert rep == {"available": True, "date_filter": C.CUT_TEST, "n_days_to_cut": 3, "n_days_in_window": 1, "days_in_window": ["2026-06-20"]}
    assert "2026-07" not in repr(rep) and "2026-08" not in repr(rep)
    (tmp_path / "list.json").write_text('["2024-08-05", "2026-08-19"]', encoding="utf-8")
    assert vorlauf.stress_coverage_filtered(tmp_path / "list.json", "2024-07-01", "2025-06-30", C.CUT_TEST)["days_in_window"] == ["2024-08-05"]
    assert vorlauf.stress_coverage_filtered(tmp_path / "none.json", "a", "b", C.CUT_TEST)["available"] is False


def test_t0_sealed_file_names_are_never_opened_or_written(tmp_path):
    from bybit_edge.research.h32_fm8 import artifacts
    for name in ("x_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_W1_UNION_REAL.csv"):
        with pytest.raises(SealError):
            artifacts.refuse_unsafe_path(tmp_path / name)
        with pytest.raises(SealError):
            artifacts.read_series_csv(tmp_path / name)
        with pytest.raises(SealError):
            artifacts.write_series_csv(tmp_path / name, [0.1])
    with pytest.raises(SealError):
        vorlauf.stress_coverage_filtered(tmp_path / "x_L_window_sealed.json", "a", "b", C.CUT_TEST)
    with pytest.raises(ValueError, match="data/harvest"):
        artifacts.write_series_csv(Path("data/harvest/x.csv"), [0.1])
    with pytest.raises(ValueError, match="data/harvest"):
        vorlauf.write_prelaunch_artifacts(Path("data/harvest/out"), {"windows": {}, "result_sha256": "x"})


# ============================================================================
# T6: legacy import lock
# ============================================================================

def test_t6_h32_fm8_never_imports_the_legacy_package():
    pkg_dir = Path(C.__file__).resolve().parent
    script = Path(__file__).resolve().parents[2] / "scripts" / "h32_fm8.py"
    files = sorted(pkg_dir.glob("*.py")) + [script]
    assert len(files) >= 15
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not [a.name for a in node.names if "_legacy_v1" in a.name], f
            elif isinstance(node, ast.ImportFrom):
                assert "_legacy_v1" not in (node.module or ""), f
                assert not [a.name for a in node.names if "_legacy_v1" in a.name], f
            elif isinstance(node, ast.Call):
                fn = getattr(node.func, "attr", getattr(node.func, "id", ""))
                if fn in ("import_module", "__import__"):
                    assert not [a.value for a in node.args if isinstance(a, ast.Constant) and "_legacy_v1" in str(a.value)], f
    src_root = Path(pkg_dir).parents[2]
    code = ("import sys; sys.path.insert(0, %r); import bybit_edge.research.h32_fm8.testrun, bybit_edge.research.h32_fm8.vorlauf, "
            "bybit_edge.research.h32_fm8.pilot, bybit_edge.research.h32_fm8.positive_control; "
            "print(any('_legacy_v1' in m for m in sys.modules))" % str(src_root))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False"


def test_t6_the_a3_code_is_only_imported_never_changed():
    """The A3 registration pins the code hash of wp13_xsec / wp7_universe: the H-32 package imports them read-only and
    the wp13 package does not know H-32."""
    wp13_dir = Path(nulls.__file__).resolve().parent
    for f in wp13_dir.glob("*.py"):
        assert "h32" not in f.read_text(encoding="utf-8").lower(), f



def test_u3_threshold_covers_condition_1c_and_binds_when_q95_is_large():
    """DEC-101 Teil 2 (U-3, Review A-4): the hand-over threshold on x_P is max(m* + MDE80*_U, max_W(q95 + z_80 SD_T)); with a
    large frozen q95 the (1c) term binds, the pilot point below it is NOT handed over although it clears the U component."""
    base = handover.evaluate_handover(_inputs(x_p=0.04), _consts())
    assert base["rule_version"] == "U-3" and base["threshold_binding"] == "U"
    assert base["threshold_on_point"] == pytest.approx(max(base["threshold_u"], base["threshold_1c"]))
    assert base["threshold_u"] == pytest.approx(base["mde80_star"] + base["m_star"])
    big = _consts(q95=(0.030, 0.028))
    probe = handover.evaluate_handover(_inputs(x_p=0.04), big)
    exp_1c = max(0.030 + C.Z_POWER * probe["per_window"]["W1"]["sd_t"], 0.028 + C.Z_POWER * probe["per_window"]["W2"]["sd_t"])
    assert probe["threshold_1c"] == pytest.approx(exp_1c) and probe["threshold_binding"] == "1c"
    assert probe["threshold_on_point"] == pytest.approx(exp_1c) and probe["threshold_on_point"] > probe["threshold_u"]
    below = handover.evaluate_handover(_inputs(x_p=probe["threshold_on_point"] - 1e-6), big)
    above = handover.evaluate_handover(_inputs(x_p=probe["threshold_on_point"] + 1e-6), big)
    assert below["conditions"]["ii"] is False and not below["handed_over"]
    assert above["conditions"]["ii"] is True and above["handed_over"]
