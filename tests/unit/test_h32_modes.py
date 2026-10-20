"""Tests of the H-32 modes on fixture panels (``tests/unit/h32_fixtures.py``): Vorlauf v6 / null, pilot, test run and positive
control -- DEC-39 trio (T1 positive / null / adversarial), T2 determinism (N >= 3 with fingerprint), T3 / T7 artifact round trip,
T4 arithmetic on conserved payloads, T5 pins, and every guard (panel cut, seal, pilot lock, exactly-one-pilot lock, start data).

The replicate counts / seeds / criteria of the registration are shrunk by ``h32_fixtures.shrink_constants`` (the YAML pins keep
comparing with the same patched constants); with the real constants the pins are exercised in ``test_h32_core.py``."""
from __future__ import annotations

import copy
import inspect
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research import power_p1 as pp
from bybit_edge.research.h32_fm8 import (artifacts, checks, estimators as est, fm8, handover, nullsim, panel_cut, permutation, pilot as pilot_mod,
                                         positive_control as pc, schema, testrun, vorlauf, weekly as wkl)
from bybit_edge.research.h32_fm8 import constants as C
from bybit_edge.research.h32_fm8.errors import (ArtifactError, DataFingerprintError, H32Abort, KMinError, NullCalibrationError, PanelCutError,
                                                PilotLockError, PinError, PositiveControlAbort, SealError)
from bybit_edge.research.wp13_xsec import characteristics, ic, nulls

from tests.unit import h32_fixtures as F
from tests.unit.h32_fixtures import REGISTERED_SHA, shrunk  # noqa: F401  (pytest fixture)

FP = dict(F.FAKE_FINGERPRINTS)


@pytest.fixture(scope="module")
def sig():
    return F.get_bundle("signal")


@pytest.fixture(scope="module")
def nul():
    return F.get_bundle("null")


@pytest.fixture(scope="module")
def win_w1(sig):
    cut, _ = panel_cut.cut_panel_days(sig["panel"], C.CUT_TEST)
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        wk = wkl.build_weekly(cut, C.CUT_TEST)
        return wkl.make_window(wk, "W1")


# ============================================================================
# Vorlauf v6 / null
# ============================================================================

def test_vorlauf_v6_freezes_the_constants_per_window_and_variant(sig, shrunk):
    rep, reg = sig["report"], sig["registered"]
    assert rep["schema"] == C.PRELAUNCH_SCHEMA and set(rep["windows"]) == {"P", "W1", "W2"}
    assert rep["cut"]["cut_date"] == C.CUT_TEST and rep["cut"]["max_date"] == C.CUT_TEST and rep["cut"]["n_days_removed"] == 91
    for wn in ("W1", "W2"):
        fz = rep["windows"][wn]["frozen_v6"]
        w = rep["windows"][wn]
        assert w["geometry"]["w_judged"] == C.W_JUDGED[wn] and w["k"]["min"] >= C.K_MIN[wn]
        for key in schema.FROZEN_VARIANT_KEYS:
            assert set(fz[key]) == set(C.VARIANTS) and all(math.isfinite(fz[key][v]) for v in C.VARIANTS)
        assert fz["floor_fm8"] > 0 and fz["v_fm8"] > 0 and fz["floor_fm8"] ** 2 <= fz["v_fm8"] + 1e-12      # Jensen: floor^2 <= mean 1/(K-1)
        assert all(fz["e_se_rule"][v] >= fz["floor_fm8"] / math.sqrt(C.W_JUDGED[wn]) - 1e-12 for v in C.VARIANTS)
        assert fz["q95"] == {v: max(fz["q95_driftfree"][v], fz["q95_drifting"][v]) for v in C.VARIANTS}      # extremer of the two cells
        assert fz["null_mean"] == {v: max(fz["null_mean_driftfree"][v], fz["null_mean_drifting"][v]) for v in C.VARIANTS}
        assert w["bounce_sigma_true"] > 0 and set(w["survivorship"]) >= {"mom1_diff_in_ic_min_units", "rev_gap_diff_in_ic_min_units"}
        # three calibrations per judged window, each with its Gegenprobe record
        assert set(w["calibration_report"]["calibration"]) == {"measured", "stress", "zero"}
    p = rep["windows"]["P"]
    assert p["geometry"]["w_judged"] == 114 and p["k"]["min"] >= 117 and set(p["m_P"]) == set(C.VARIANTS)
    assert set(p["calibration_report"]["calibration"]) == {"stress"}                                         # P: stress only, no mean
    assert p["k_fm8_series_sha256"] == reg["pilot_window"]["frozen_v6"]["k_fm8_series_sha256"]
    assert p["m_P"] == p["null"]["frozen"]["null_mean"]
    # outcome-free: no IC of real returns anywhere in the report
    blob = json.dumps(rep, default=str)
    for bad in ("raw_ic", "lag_profile", "beta_calibration", "ic_weekly"):
        assert bad not in blob


def test_vorlauf_k_fm8_series_is_the_cross_section_of_the_ic(sig, shrunk, win_w1):
    k8 = wkl.k_fm8_series(win_w1)
    assert wkl.int_series_sha256(k8) == sig["registered"]["windows"]["W1"]["frozen_v6"]["k_fm8_series_sha256"]
    res = fm8.window_ic(win_w1, "mom2")
    assert np.array_equal(k8, np.array(res["k_weekly"]))


def test_vorlauf_null_has_all_judged_weeks_thanks_to_the_eight_beta_lead_weeks(win_w1, shrunk):
    """v5e lost the first 8 weeks of the simulation (45 / 44 weeks); with the lead the window mean runs over all 52."""
    cell = nullsim.simulate_fm8_cell(win_w1, rho_f=0.05, beta_sd=0.3, drift_f=0.0, sigma_f=0.06, sigma_e=0.09, n_reps=3, seed=53,
                                     floor_fm8=0.08, n_boot=30)
    assert cell["lead_weeks"] == 8 and cell["w_judged"] == 52
    assert all(v["n_ic_pooled"] == 3 * 52 and v["n_reps_finite"] == 3 for v in cell["variants"].values())
    # the generic dispatcher of the third version reproduces the null's fm8 pipeline
    rng = np.random.default_rng(53)
    sim = nulls.simulate_factor_panel(win_w1.alive_ext.shape[0], len(win_w1.symbols), sigma_f=0.06, sigma_e=0.09, rho_f=0.05, drift_f=0.0,
                                      rng=rng, beta_sd=0.3, market_index=win_w1.symbols.index("BTCUSDT"))
    r = sim["returns"]
    est_r = np.where(win_w1.valid_ext, r, np.nan)
    beta = characteristics.beta_characteristic(est_r, win_w1.symbols, market_symbol="BTCUSDT", trail_win=8, min_weeks=8)
    char = characteristics.weekly_only_proxy_characteristic("mom1", r)[8:]
    applied = ic.apply_beta_control("fm_neutral_8w", char, r[8:], win_w1.alive, beta_pit=beta[8:], symbols=win_w1.symbols)
    res = ic.weekly_ic_series(char, applied["returns"], win_w1.alive, convention="close_at_last")
    assert len(res["weekly"]) == 52 and all(math.isfinite(w["ic"]) for w in res["weekly"])
    cell1 = nullsim.simulate_fm8_cell(win_w1, rho_f=0.05, beta_sd=0.3, drift_f=0.0, sigma_f=0.06, sigma_e=0.09, n_reps=1, seed=53,
                                      floor_fm8=0.08, n_boot=30, variants=("mom1",))
    assert cell1["variants"]["mom1"]["draws_sha256"] == est.series_sha256([res["mean_ic"]])


def test_vorlauf_e_se_rule_is_the_expectation_of_the_se_rule_over_the_replicates(win_w1, shrunk):
    """Review B-7: e_se_rule = E[SE by rule P-1 (4)] over the replicates (floor, SD, stationary bootstrap), not the SD of the means."""
    floor, n_rep = 0.075, 6
    cell = nullsim.simulate_fm8_cell(win_w1, rho_f=0.0, beta_sd=0.3, drift_f=0.0, sigma_f=0.06, sigma_e=0.09, n_reps=n_rep, seed=7,
                                     floor_fm8=floor, n_boot=40, variants=("mom1",))
    rng = np.random.default_rng(7)
    ses = []
    for _ in range(n_rep):
        sim = nulls.simulate_factor_panel(win_w1.alive_ext.shape[0], len(win_w1.symbols), sigma_f=0.06, sigma_e=0.09, rho_f=0.0, drift_f=0.0,
                                          rng=rng, beta_sd=0.3, market_index=win_w1.symbols.index("BTCUSDT"))
        r = sim["returns"]
        beta = characteristics.beta_characteristic(np.where(win_w1.valid_ext, r, np.nan), win_w1.symbols, market_symbol="BTCUSDT",
                                                   trail_win=8, min_weeks=8)
        resid = ic.fm_neutralize_outcome(r[8:], beta[8:], win_w1.alive)
        char = characteristics.weekly_only_proxy_characteristic("mom1", r)[8:]
        series = [w["ic"] for w in ic.weekly_ic_series(char, resid, win_w1.alive, convention="close_at_last")["weekly"]]
        ses.append(est.se_rule(series, floor, 52, n_boot=40, seed=53)["se"])
    assert cell["variants"]["mom1"]["e_se_rule"] == pytest.approx(float(np.mean(ses)), rel=1e-12)
    assert cell["variants"]["mom1"]["e_se_rule"] >= floor / math.sqrt(52)


def test_t2_null_cell_and_window_constants_are_deterministic_n3_with_fingerprint(win_w1, shrunk):
    kw = dict(rho_f=0.04, beta_sd=0.3, sigma_f=0.06, sigma_e=0.09, n_reps=4, seed=53, floor_fm8=0.08, n_boot=30)
    runs = [nullsim.window_null_constants(win_w1, **kw) for _ in range(3)]
    fps = [artifacts.canonical_sha256(r) for r in runs]
    assert fps[0] == fps[1] == fps[2]
    assert nullsim.window_null_constants(win_w1, **{**kw, "seed": 54})["frozen"]["null_mean"] != runs[0]["frozen"]["null_mean"]
    assert set(runs[0]["cells"]) == {"driftfree", "drifting"}
    assert runs[0]["cells"]["driftfree"]["drift_f"] == 0.0 and runs[0]["cells"]["drifting"]["drift_f"] == 0.002


def test_vorlauf_t2_full_report_is_deterministic(nul, shrunk):
    again = F.prelaunch_report(nul["panel"])
    assert again["result_sha256"] == nul["report"]["result_sha256"]
    third = F.prelaunch_report(nul["panel"])
    assert third["result_sha256"] == again["result_sha256"]


def test_vorlauf_refuses_a_cut_date_in_the_blind_period_and_a_non_sunday(sig, shrunk):
    with pytest.raises(PanelCutError, match="limit"):
        vorlauf.assemble_prelaunch(sig["panel"], FP, cut_date="2026-07-05", n_reps=2, n_boot=20)
    with pytest.raises(PanelCutError, match="Sunday"):
        vorlauf.assemble_prelaunch(sig["panel"], FP, cut_date="2026-06-26", n_reps=2, n_boot=20)


def test_vorlauf_w1_determinism_control_against_a_v5e_reference(sig, shrunk):
    w1 = sig["report"]["windows"]["W1"]["calibration_report"]
    ref = {"windows": {"W1": {"null_scales": dict(w1["null_scales"]),
                             "calibration": {k: {kk: v[kk] for kk in ("rho_f", "beta_sd_calibrated", "target_factor_share")}
                                             for k, v in w1["calibration"].items()}}}}
    assert vorlauf.w1_determinism_control(w1, ref)["ok"] is True
    bad = copy.deepcopy(ref)
    bad["windows"]["W1"]["null_scales"]["sigma_f"] *= 1.001
    ctl = vorlauf.w1_determinism_control(w1, bad)
    assert ctl["ok"] is False and ctl["rows"]["sigma_f"]["ok"] is False
    bad2 = copy.deepcopy(ref)
    bad2["windows"]["W1"]["calibration"]["stress"]["beta_sd_calibrated"] *= 1.05
    assert vorlauf.w1_determinism_control(w1, bad2)["ok"] is False
    assert vorlauf.w1_determinism_control(w1, {"windows": {}})["ok"] is False


def test_vorlauf_template_text_carries_the_header_and_the_fingerprints(sig, shrunk):
    tpl = vorlauf.build_template(sig["report"], bounce_spread=0.003621)
    text = vorlauf.template_yaml_text(tpl, sig["report"], source_sha256="ab" * 32)
    assert text.startswith("# H-32") and "NICHT registriert" in text and sig["report"]["result_sha256"] in text
    assert tpl["data_fingerprints"] == FP and tpl["rules"]["bounce_spread"] == 0.003621 and tpl["pilot_window"]["pilot_result_sha256"] is None
    assert tpl["pilot_window"]["frozen_v6"]["calibration"]["note"].startswith("nur Streuung")
    md = vorlauf.render_prelaunch_markdown(sig["report"])
    assert md.isascii() and "KEIN VERDIKT" in md and "m_P" in md


# ============================================================================
# pilot (stage P)
# ============================================================================

def test_t1_pilot_positive_hands_over_the_injected_variants_with_the_double_statement(sig, shrunk):
    pr = sig["pilot_report"]
    assert pr["status"] == "UEBERGEBEN" and pr["handed"] == ["mom1", "rev_gap"] and set(pr["not_handed"]) == {"mom2", "mom4"}
    for v in pr["handed"]:
        h = pr["variants"][v]["handover"]
        assert h["conditions"] == {"i": True, "ii": True, "iii": True} and h["regime_p1"]["regime"] == "C10" and h["pi_v"] == h["x_p"]
        assert h["mu_sel"] is not None and h["mu_sel"] <= h["x_p"] + 1e-9 and h["power_at_mu_sel"]["joint"] <= h["regime_p1"]["window_power_joint_product"] + 1e-9
        assert "regime_a3_practice" in h and "regime_a3_practice" in h["power_at_mu_sel"]
        ep = pr["end_power"][v]["at_pilot_point"]
        assert ep["m_tested"]["m"] == 2 and ep["m_old_count_report_only"]["m"] == 11 and ep["m_tested"]["joint"] > ep["m_old_count_report_only"]["joint"]
        s = pr["variants"][v]["stats"]
        assert s["x_p"] > 0.05 and s["t_p"] > 5 and s["w_p"] == 114 and s["band80_normal"][0] < s["x_p"] < s["band80_normal"][1]
    for v in pr["not_handed"]:
        assert pr["variants"][v]["handover"]["status"] == "GL-012 (Pilot)" and pr["variants"][v]["handover"]["mu_sel"] is None
    assert pr["window"]["first_outcome_week"] == C.PILOT_OUTCOME_FIRST and pr["window"]["last_outcome_week"] == C.PILOT_OUTCOME_LAST
    assert pr["panel"]["cut_date"] == C.CUT_PILOT and pr["panel"]["max_date"] == C.CUT_PILOT and pr["window"]["w_pilot"] == 114
    assert any("Screening, nie Konfirmation" in lab for lab in pr["labels"])
    for key in ("raw_ic", "lag_profile", "beta_calibration"):
        assert key not in json.dumps(pr["variants"], default=str)


def test_t1_pilot_null_panel_hands_over_nothing_gl012(nul, shrunk):
    pr = nul["pilot_report"]
    assert pr["status"] == "GL-012 (Pilot)" and pr["handed"] == [] and set(pr["not_handed"]) == set(C.VARIANTS)
    assert all(pr["variants"][v]["handover"]["reason"].startswith("GL-012 (Pilot): verfehlte Bedingung") for v in C.VARIANTS)
    assert pr["end_power"] == {}


def test_t1_pilot_null_handover_rate_in_signal_free_worlds_is_at_most_one_percent(sig, shrunk):
    """Hand-over rate of the signal-free stress world (P window shape, W1 world): <= 0.01 + MC tolerance."""
    reg = sig["registered"]
    cut, _ = panel_cut.cut_panel_days(sig["panel"], C.CUT_PILOT, limit=C.CUT_PILOT)
    wk = wkl.build_weekly(cut, C.CUT_PILOT)
    win = wkl.make_window(wk, "P")
    world = pc.world_params(reg, "W1")
    geom = {"alive_ext": win.alive_ext, "valid_ext": win.valid_ext}
    n, hits = 40, 0
    for seed in range(n):
        w = pc.synthesize_world(geom["alive_ext"], geom["valid_ext"], win.symbols, world, seed=500 + seed, window_index=0, variant="mom1",
                                signal_ic=0.0, sigma_g=0.0)
        series = pc.eval_world(w, geom["alive_ext"], win.symbols, "mom1")
        k = [int(x) for x in wkl.k_alive_series(win)]
        s = est.pilot_statistics(series, k, 1, n_boot=60, seed=53)
        hits += int(handover.evaluate_handover(s, handover.handover_constants(reg, "mom1"))["handed_over"])
    assert hits / n <= 0.05                                                            # <= 0.01 + tolerance for n = 40


def _synthetic_window(n_weeks: int = 53, k: int = 150) -> wkl.Window:
    lead = C.LEAD_WEEKS
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    ones = np.ones((lead + n_weeks, k + 1), dtype=bool)
    z = np.zeros((n_weeks, k + 1))
    return wkl.Window(name="W1", start="2024-07-01", end="2025-06-30", lo=lead, hi=lead + n_weeks, weeks=[f"w{i}" for i in range(n_weeks)],
                      symbols=symbols, alive=ones[lead:], returns=z, returns_est=z, valid=ones[lead:], beta8=z, chars={}, turnover_trail=None,
                      alive_ext=ones, valid_ext=ones)


def test_t1_adversarial_dominant_drifting_market_fires_the_raw_ic_but_not_the_fm8_gate(shrunk):
    """PRD 5.3 adversarial fixture with the registered statistic fm_neutral_8w as primary: an AR(1) market (rho 0.2) with drift
    0.002, betas U(0.5, 2.0), no cross-sectional predictability -- mom1 is only mechanically tied to beta.  The null (v6
    configuration, the adversary's own stress world, driftfree and drifting) is frozen once and applied to independent draws.
    Teeth: the RAW mean IC is the market-timing artifact; the fm8 statistic does not clear the frozen threshold in (almost) any
    draw and certainly not in both windows' worth of draws."""
    from bybit_edge.research.h32_fm8 import gate
    win = _synthetic_window()
    floor, _v = wkl.floor_and_v(np.full(52, 150))
    n_ext, n_sym = win.alive_ext.shape
    m_idx = win.symbols.index("BTCUSDT")
    frozen = nullsim.window_null_constants(win, rho_f=0.2, beta_sd=0.45, sigma_f=0.08, sigma_e=0.04, n_reps=60, seed=53,
                                           floor_fm8=floor, n_boot=40, variants=("mom1",))["frozen"]
    n_pass = 0
    raw_means, y_means = [], []
    for seed in range(10, 20):
        rng = np.random.default_rng(seed)
        sim = nulls.simulate_factor_panel(n_ext, n_sym, sigma_f=0.08, sigma_e=0.04, rho_f=0.2, drift_f=0.002, rng=rng, market_index=m_idx)
        r = sim["returns"]
        raw = ic.weekly_ic_series(characteristics.momentum_characteristic(r, trail_win=1)[8:], r[8:], win.alive,
                                  convention="close_at_last")["mean_ic"]
        series = pc.eval_world({"returns": r, "returns_est": r}, win.alive_ext, win.symbols, "mom1")
        y = float(np.nanmean(series))
        se = est.se_rule(series, floor, 52, n_boot=40, seed=53)["se"]
        cond = gate.window_conditions({"y": y, "se_w": se, "q95": frozen["q95"]["mom1"]}, C.Z_KRIT)
        n_pass += int(cond["window_pass"])
        raw_means.append(raw)
        y_means.append(y)
    assert np.mean(raw_means) > 0.05                                                 # the fixture is adversarial for the raw statistic
    assert np.mean(y_means) < np.mean(raw_means) / 2                                 # fm8 removes most of it
    assert n_pass <= 1                                                               # <= alpha-ish false PASS; the raw gate would fire in all


def test_t1_pilot_leak_aborts_when_the_cut_is_bypassed(sig, shrunk, monkeypatch):
    monkeypatch.setattr(panel_cut, "cut_panel_days", lambda panel, cut_date, **kw: (panel, {"cut_date": cut_date, "n_days_removed": 0}))
    with pytest.raises(PanelCutError, match="not cut"):
        pilot_mod.run_pilot(sig["panel"], sig["registered"], FP, registered_sha256=REGISTERED_SHA)


def test_t1_pilot_panel_cut_makes_the_result_independent_of_everything_after_the_cut(sig, shrunk):
    n_cut = sum(1 for d in sig["panel"]["dates"] if d <= C.CUT_PILOT)
    shortened = dict(sig["panel"])
    for k in ("close", "turnover", "funding_n", "funding_sum"):
        shortened[k] = sig["panel"][k][:n_cut]
    shortened["dates"], shortened["day_index"] = sig["panel"]["dates"][:n_cut], sig["panel"]["day_index"][:n_cut]
    shortened["last_alive_day"] = [d if (d is not None and d <= C.CUT_PILOT) else None for d in sig["panel"]["last_alive_day"]]
    def core(r):                                       # the results (the cut report counts what was removed, which differs by construction)
        return artifacts.canonical_sha256({k: r[k] for k in ("variants", "window", "handed", "not_handed", "end_power", "status")})

    a = pilot_mod.run_pilot(sig["panel"], sig["registered"], FP, registered_sha256=REGISTERED_SHA)
    b = pilot_mod.run_pilot(shortened, sig["registered"], FP, registered_sha256=REGISTERED_SHA)
    assert a["result_sha256"] == sig["pilot_report"]["result_sha256"] and core(a) == core(b)
    assert a["panel"]["n_days_removed"] == 819 and b["panel"]["n_days_removed"] == 0
    # a pilot panel in which the future is violently different gives the same answer
    wild = F.relabel_prices(sig["panel"], 5)
    wild["close"] = wild["close"].copy()
    keep = np.array([d <= C.CUT_PILOT for d in sig["panel"]["dates"]])
    wild["close"][keep] = sig["panel"]["close"][keep]
    c = pilot_mod.run_pilot(wild, sig["registered"], FP, registered_sha256=REGISTERED_SHA)
    assert core(c) == core(a)


def test_t1_pilot_seal_watcher_sees_only_fm8_calls_on_the_pilot_window(sig, shrunk, monkeypatch):
    """Monkeypatch watcher on ``ic.weekly_ic_series`` (PP4): every call is a fm8 residual outcome of exactly the 115 pilot weeks,
    never the raw return matrix of the window (no raw IC), never a shifted one (no lag profile), never beta as characteristic."""
    cut, _ = panel_cut.cut_panel_days(sig["panel"], C.CUT_PILOT, limit=C.CUT_PILOT)
    wk = wkl.build_weekly(cut, C.CUT_PILOT)
    win = wkl.make_window(wk, "P")
    seen = []
    real = ic.weekly_ic_series

    def spy(characteristic, returns, alive, **kw):
        seen.append({"rows": returns.shape[0], "raw": bool(np.array_equal(returns, win.returns)),
                     "beta": bool(np.array_equal(characteristic, win.beta8, equal_nan=True)),
                     "char_is_variant": any(np.array_equal(characteristic, win.chars[v], equal_nan=True) for v in C.VARIANTS),
                     "abs_max": float(np.nanmax(np.abs(returns))), "convention": kw.get("convention")})
        return real(characteristic, returns, alive, **kw)

    monkeypatch.setattr(ic, "weekly_ic_series", spy)
    pilot_mod.run_pilot(sig["panel"], sig["registered"], FP, registered_sha256=REGISTERED_SHA)
    assert seen and all(c["rows"] == 115 and not c["raw"] and not c["beta"] and c["char_is_variant"] and c["convention"] == "close_at_last" for c in seen)
    assert max(c["abs_max"] for c in seen) < 1.5                                           # nothing of the shocks after the cut
    assert len(seen) == 4 + 4 * 2                                                          # 4 variants + liquidity masks (2 per variant)


def test_t5_pilot_pins_data_fingerprints_window_k_and_k_minimum(sig, shrunk):
    reg = sig["registered"]
    with pytest.raises(DataFingerprintError):
        pilot_mod.run_pilot(sig["panel"], reg, {**FP, "union_range_fingerprint": "00" * 32})
    with pytest.raises(DataFingerprintError):
        pilot_mod.run_pilot(sig["panel"], reg, None)
    bad = copy.deepcopy(reg)
    bad["pilot_window"]["frozen_v6"]["k_fm8_series_sha256"] = "11" * 32
    with pytest.raises(PinError, match="K_fm8"):
        pilot_mod.run_pilot(sig["panel"], bad, FP)
    small = F.make_panel(seed=1, k=60, n_late=0, delist_weeks=())
    with pytest.raises(KMinError):
        pilot_mod.run_pilot(small, reg, FP)
    bad2 = copy.deepcopy(reg)
    bad2["pilot_window"]["w_pilot"] = 115
    with pytest.raises(PinError):
        pilot_mod.run_pilot(sig["panel"], bad2, FP)


def test_t3_exactly_one_pilot_lock_and_the_dec_referenced_rerun(sig, shrunk, tmp_path):
    reg = sig["registered"]
    out = tmp_path / "pilot_out"
    lock = checks.check_rerun_lock(out, reg, None)
    assert lock == {"rerun": False, "prefix": "h32_pilot"}
    assert "force" not in inspect.signature(checks.check_rerun_lock).parameters and "force" not in inspect.signature(pilot_mod.write_pilot_artifacts).parameters
    w = pilot_mod.write_pilot_artifacts(out, sig["pilot_report"], reg, lock)
    assert (out / "h32_pilot.json").is_file() and (out / "h32_pilot.sha256").read_text().split()[0] == w["result_json"]["sha256"]
    with pytest.raises(PilotLockError, match="exactly one pilot run"):
        checks.check_rerun_lock(out, reg, None)
    with pytest.raises(PilotLockError, match="exactly one pilot run"):
        pilot_mod.write_pilot_artifacts(out, sig["pilot_report"], reg, lock)                  # the writer re-checks the lock
    with pytest.raises(PilotLockError, match="not a DEC"):
        checks.check_rerun_lock(out, reg, "because")
    with pytest.raises(PilotLockError, match="no earlier pilot"):
        checks.check_rerun_lock(tmp_path / "empty", reg, "DEC-101")
    reg_locked = copy.deepcopy(reg)
    reg_locked["pilot_window"]["pilot_result_sha256"] = "ab" * 32
    with pytest.raises(PilotLockError):
        checks.check_rerun_lock(tmp_path / "other", reg_locked, None)                          # a registered pilot_result_sha256 blocks a new run
    before = {p.name: artifacts.sha256_file(p) for p in out.iterdir()}
    lock2 = checks.check_rerun_lock(out, reg, "DEC-101")
    assert lock2["rerun"] and lock2["prefix"] == "h32_pilot_rerun_DEC-101"
    pilot_mod.write_pilot_artifacts(out, sig["pilot_report"], reg, lock2)
    assert (out / "h32_pilot_rerun_DEC-101.json").is_file()
    assert before == {k: artifacts.sha256_file(out / k) for k in before}                      # both results disclosed, nothing overwritten
    rr = json.loads((out / "h32_pilot_rerun_DEC-101.json").read_text(encoding="utf-8"))
    assert rr["rerun"]["rerun_dec"] == "DEC-101"
    with pytest.raises(PilotLockError, match="needs its own DEC"):
        checks.check_rerun_lock(out, reg, "DEC-101")


def test_t7_pilot_artifact_round_trip_reproduces_the_estimators_and_detects_tampering(sig, shrunk, tmp_path):
    reg = sig["registered"]
    out = tmp_path / "p"
    shutil.copytree(sig["tmp"] / "pilot", out)
    pub = {k: v for k, v in sig["pilot_report"].items() if k != "_series"}
    assert pilot_mod.verify_pilot_artifacts(out, "h32_pilot", pub, reg)["n_variants_checked"] == 4
    csv = out / "h32_pilot_mom1_P_ic_weekly.csv"
    orig = csv.read_bytes()
    lines = orig.split(b"\r\n")
    lines[5] = b"4,0.5,150"
    csv.write_bytes(b"\r\n".join(lines))
    with pytest.raises(ArtifactError):
        pilot_mod.verify_pilot_artifacts(out, "h32_pilot", pub, reg)
    csv.write_bytes(orig)
    pilot_mod.verify_pilot_artifacts(out, "h32_pilot", pub, reg)
    (out / "h32_pilot_rev_gap_P_ic_weekly.csv").unlink()
    with pytest.raises(ArtifactError, match="missing"):
        pilot_mod.verify_pilot_artifacts(out, "h32_pilot", pub, reg)
    (out / "h32_pilot_fingerprint.json").unlink()
    with pytest.raises(ArtifactError, match="missing"):
        pilot_mod.verify_pilot_artifacts(out, "h32_pilot", pub, reg)
    # a writer whose verification fails publishes NO result file
    broken = copy.deepcopy(pub)
    broken["variants"]["mom1"]["stats"]["x_p"] += 1e-9
    broken["_series"] = sig["pilot_report"]["_series"]
    out2 = tmp_path / "q"
    with pytest.raises(ArtifactError):
        pilot_mod.write_pilot_artifacts(out2, broken, reg, checks.check_rerun_lock(out2, reg, None))
    assert not (out2 / "h32_pilot.json").exists()


def test_t2_pilot_is_deterministic_n3_with_fingerprint_and_the_file_hash(sig, shrunk, tmp_path):
    reg = sig["registered"]
    results, files = [], []
    for i in range(3):
        pr = pilot_mod.run_pilot(sig["panel"], reg, FP, registered_sha256=REGISTERED_SHA)
        out = tmp_path / f"run{i}"
        w = pilot_mod.write_pilot_artifacts(out, pr, reg, checks.check_rerun_lock(out, reg, None))
        results.append(pr["result_sha256"])
        files.append(w["result_json"]["sha256"])
    assert len(set(results)) == 1 and len(set(files)) == 1 and files[0] == sig["pilot_sha"]
    fps = [json.loads((tmp_path / f"run{i}" / "h32_pilot_fingerprint.json").read_text())["variants"]["mom1"]["bootstrap_means_sha256"] for i in range(3)]
    assert len(set(fps)) == 1


def test_t4_pilot_lock_rederives_the_handover_bit_for_bit_and_refuses_tampering(sig, shrunk, tmp_path):
    reg, pj = sig["registered"], sig["pilot_json"]
    good = testrun.load_pilot_result(pj, sig["pilot_sha"], reg, REGISTERED_SHA)
    assert good["handed"] == ["mom1", "rev_gap"] and good["_file_sha256"] == sig["pilot_sha"]
    with pytest.raises(PilotLockError, match="sha256"):
        testrun.load_pilot_result(pj, "00" * 32, reg, REGISTERED_SHA)
    with pytest.raises(PilotLockError, match="sha256"):
        testrun.load_pilot_result(pj, "", reg, REGISTERED_SHA)
    with pytest.raises(PilotLockError, match="different registered YAML"):
        testrun.load_pilot_result(pj, sig["pilot_sha"], reg, "1" * 64)
    with pytest.raises(PilotLockError, match="not found"):
        testrun.load_pilot_result(tmp_path / "none.json", sig["pilot_sha"], reg, REGISTERED_SHA)
    doc = json.loads(pj.read_text(encoding="utf-8"))

    def write_variant(mutate, rehash: bool) -> Path:
        d = copy.deepcopy(doc)
        mutate(d)
        if rehash:
            d["result_sha256"] = testrun.pilot_core_hash(d)
        p = tmp_path / ("t_%d.json" % len(list(tmp_path.glob("t_*.json"))))
        p.write_text(json.dumps(d, sort_keys=True), encoding="utf-8")
        return p

    p1 = write_variant(lambda d: d["variants"]["mom2"]["stats"].__setitem__("x_p", 0.2), rehash=False)
    with pytest.raises(PilotLockError, match="self-consistent"):
        testrun.load_pilot_result(p1, artifacts.sha256_file(p1), reg, REGISTERED_SHA)
    p2 = write_variant(lambda d: d["variants"]["mom2"]["stats"].__setitem__("x_p", 0.2), rehash=True)       # consistent hash, wrong hand-over
    with pytest.raises(PilotLockError, match="not reproduced"):
        testrun.load_pilot_result(p2, artifacts.sha256_file(p2), reg, REGISTERED_SHA)
    p3 = write_variant(lambda d: d.__setitem__("handed", ["mom1"]), rehash=True)
    with pytest.raises(PilotLockError, match="re-derived"):
        testrun.load_pilot_result(p3, artifacts.sha256_file(p3), reg, REGISTERED_SHA)
    reg_other = copy.deepcopy(reg)
    reg_other["pilot_window"]["pilot_result_sha256"] = "cd" * 32
    with pytest.raises(PilotLockError, match="different pilot_result_sha256"):
        testrun.load_pilot_result(pj, sig["pilot_sha"], reg_other, REGISTERED_SHA)
    # a pilot of another registration whose constants differ re-derives differently
    reg_c = copy.deepcopy(reg)
    reg_c["pilot_window"]["frozen_v6"]["m_P"]["mom1"] = 0.5
    with pytest.raises(PilotLockError, match="not reproduced"):
        testrun.load_pilot_result(pj, sig["pilot_sha"], reg_c, REGISTERED_SHA)


# ============================================================================
# test run (stage T)
# ============================================================================

@pytest.fixture(scope="module")
def run_sig(sig):
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        return testrun.run_test(sig["panel"], sig["registered"], sig["pilot"], FP, registered_sha256=REGISTERED_SHA)


def test_run_signal_panel_tests_only_the_handed_variants_and_the_gate_passes(run_sig, sig, shrunk):
    r = run_sig
    assert r["handed"] == ["mom1", "rev_gap"] and r["panel"]["cut_date"] == C.CUT_TEST and r["panel"]["max_date"] == C.CUT_TEST
    assert {e: res["computed"] for e, res in r["results"].items()} == {"H-32_mom1": True, "H-32_mom2": False, "H-32_mom4": False, "H-32_rev_gap": True}
    for e in ("H-32_mom2", "H-32_mom4"):
        res = r["results"][e]
        assert res["verdict"]["verdict"] == "GL-012 (Pilot)" and res["p_max"] == 1.0 and "payload" not in res
    for e in ("H-32_mom1", "H-32_rev_gap"):
        res = r["results"][e]
        assert res["verdict"]["verdict"] == "PASS" and res["verdict"]["fweek"]["m"] == 2
        for wn in ("W1", "W2"):
            w = res["payload"]["windows"][wn]
            assert w["y"] > w["q95"] and w["y"] >= C.Z_KRIT * w["se_w"] and w["w_judged"] == C.W_JUDGED[wn]
            assert res["details"][wn]["permutation"]["n_perm"] == C.N_PERM and res["details"][wn]["permutation"]["p_normal_approx_report_only"] < 0.01
    assert r["hypothesis_verdict"]["verdict"] == "PASS" and r["hypothesis_verdict"]["variants_pass"] == ["mom1", "rev_gap"]
    assert r["fweek"]["by"]["m"] == 2 and r["fweek"]["by_double_statement"]["m"] == 11                      # DEC-99 (7) and the old count
    assert r["bh"]["m"] == 4 and set(r["bh"]["reject"]) == set(C.VARIANTS)
    assert all(res["verdict"]["fweek_double_statement"]["m"] == 11 for e, res in r["results"].items() if res["computed"])
    for e in ("H-32_mom1", "H-32_rev_gap"):
        res = r["results"][e]
        assert res["end_power"]["at_pilot_point_m_tested"]["m"] == 2 and res["end_power"]["at_pilot_point_m_old_count_report_only"]["m"] == 11
        assert any(lab.startswith("Survivorship-Etikett") for lab in res["verdict"]["labels"])
        assert "zugelassen nur durch DEC-99 (Pilot-Prior)" in res["verdict"]["labels"]
    assert r["results"]["H-32_rev_gap"]["payload"]["windows"]["W1"]["bounce_ic"] is not None                   # (4b) only for rev_gap
    assert r["results"]["H-32_mom1"]["payload"]["windows"]["W1"]["bounce_ic"] is None
    assert set(r["not_computed"]) >= {"raw_ic", "lag_profile", "beta_calibration_ic", "persistence_null"}


def test_t4_run_gate_and_fweek_arithmetic_on_the_conserved_test_payload(run_sig, shrunk):
    from bybit_edge.research.h32_fm8 import fweek, gate
    for e in ("H-32_mom1", "H-32_rev_gap"):
        payload = run_sig["results"][e]["payload"]
        v1, v2 = gate.evaluate(payload), gate.evaluate(copy.deepcopy(payload))
        assert v1 == v2 and v1["verdict"] == "PASS"
        for wn in ("W1", "W2"):
            w = payload["windows"][wn]
            assert w["threshold_frozen"] == pytest.approx(schema.threshold_frozen(F.get_bundle("signal")["registered"], wn, payload["variant"]))
    p = {e: run_sig["results"][e]["p_max"] for e in ("H-32_mom1", "H-32_rev_gap")}
    verdicts = {e: gate.evaluate(run_sig["results"][e]["payload"]) for e in p}
    again = fweek.apply_fweek(verdicts, p)
    assert again["by"]["reject"] == run_sig["fweek"]["by"]["reject"] and again["demoted"] == []
    # monotonicity of the F-WEEK stage in m: more tested hypotheses can only remove a PASS
    more = fweek.apply_fweek({e: gate.evaluate(run_sig["results"][e]["payload"]) for e in p}, p, wave_p={f"w{i}": 0.5 for i in range(6)})
    assert more["by"]["single_bound"] < again["by"]["single_bound"]


def test_t5_run_payload_carries_the_registered_constants(run_sig, sig, shrunk):
    reg = sig["registered"]
    pins = schema.frozen_pin_table(reg)
    for e in ("H-32_mom1", "H-32_rev_gap"):
        c = run_sig["results"][e]["payload"]["constants"]
        assert c["n_perm"] == pins["n_perm"] == C.N_PERM and c["seed"] == pins["seed"] == 53 and c["mean_block"] == 4 and c["n_boot"] == pins["n_boot"]
        assert c["w_judged"] == {"W1": 52, "W2": 50} and c["panel_cut_test"] == pins["panel_cut_test"] and c["block_len"] == 4
        v = run_sig["results"][e]["variant"]
        for wn in ("W1", "W2"):
            fz = c["frozen"][wn]
            assert fz["e_se_rule"] == pins[wn]["e_se_rule"][v] and fz["null_mean"] == pins[wn]["null_mean"][v]
            assert fz["q95"] == pins[wn]["q95"][v] and fz["ceiling_k4"] == pins[wn]["ceiling_k4"] and fz["floor_fm8"] == pins[wn]["floor_fm8"]
        assert run_sig["results"][e]["payload"]["z_krit"] == C.Z_KRIT
    assert run_sig["parameters"]["z_krit"] == C.Z_KRIT and run_sig["parameters"]["alpha"] == 0.05
    for wn in ("W1", "W2"):
        assert run_sig["null_calibration"][wn]["within_tolerance"] and run_sig["null_calibration"][wn]["n_reps"] == reg["rules"]["n_reps"]


def test_run_signal_free_pilot_runs_no_test_and_reads_no_panel(nul, shrunk):
    r = testrun.run_test(None, nul["registered"], nul["pilot"], None, registered_sha256=REGISTERED_SHA)
    assert r["handed"] == [] and r["hypothesis_verdict"]["verdict"] == "GL-012 (Pilot)" and r["fweek"] is None
    assert all(not res["computed"] and res["p_max"] == 1.0 for res in r["results"].values()) and r["bh"]["m"] == 4
    assert not any(res["computed"] for res in r["results"].values())


def test_run_guards_leak_data_fingerprints_and_null_deviation(sig, shrunk, monkeypatch):
    reg = sig["registered"]
    with pytest.raises(DataFingerprintError):
        testrun.run_test(sig["panel"], reg, sig["pilot"], {**FP, "delisting_dates_sha256": "00" * 32}, registered_sha256=REGISTERED_SHA)
    monkeypatch.setattr(panel_cut, "cut_panel_days", lambda panel, cut_date, **kw: (panel, {"cut_date": cut_date, "n_days_removed": 0}))
    with pytest.raises(PanelCutError, match="not cut"):
        testrun.run_test(sig["panel"], reg, sig["pilot"], FP, registered_sha256=REGISTERED_SHA)


def test_run_p6_null_recomputation_deviation_is_a_loud_fail_and_the_tolerance_arithmetic(sig, shrunk):
    testrun.assert_null_value(1.05, 1.0, label="a")
    testrun.assert_null_value(0.91, 1.0, label="b")
    testrun.assert_null_value(0.00005, 0.0, label="abs")                                         # ~0: absolute 1e-4
    for rec, frz in ((1.2, 1.0), (0.8, 1.0), (0.001, 0.0), (float("nan"), 1.0), (1.0, float("nan"))):
        with pytest.raises(NullCalibrationError):
            testrun.assert_null_value(rec if frz != 0.0 else rec, frz, label="x")
    bad = copy.deepcopy(sig["registered"])
    bad["windows"]["W2"]["frozen_v6"]["ceiling_k4"] *= 1.5
    with pytest.raises(NullCalibrationError, match="ceiling_k4"):
        testrun.run_test(sig["panel"], bad, sig["pilot"], FP, registered_sha256=REGISTERED_SHA)


def test_t7_run_artifacts_round_trip_and_tampering(run_sig, sig, shrunk, tmp_path):
    reg = sig["registered"]
    out = tmp_path / "run"
    w = testrun.write_run_artifacts(out, run_sig, reg, pilot_sha256=sig["pilot_sha"])
    names = {p.name for p in out.iterdir()}
    assert {"h32_run.json", "h32_run.md", "h32_run_fingerprint.json"} <= names
    for e in ("H-32_mom1", "H-32_rev_gap"):
        for wn in ("W1", "W2"):
            assert f"h32_run_{e}_{wn}_ic_weekly.csv" in names and f"h32_run_{e}_{wn}_perm_draws.csv" in names
    assert not any("sealed" in n for n in names)
    pub = {k: v for k, v in run_sig.items() if k != "_series"}
    assert testrun.verify_run_artifacts(out, pub, reg)["n_entry_windows_checked"] == 4
    fp = json.loads((out / "h32_run_fingerprint.json").read_text(encoding="utf-8"))
    assert fp["seed"] == 53 and fp["code"]["bit_generator"] == "PCG64" and fp["panel_cut"] == C.CUT_TEST and fp["pilot_sha256"] == sig["pilot_sha"]
    assert fp["data_fingerprints"] == FP and fp["registered_sha256"] == REGISTERED_SHA and fp["code"]["code_sha256"]
    main = json.loads((out / "h32_run.json").read_text(encoding="utf-8"))
    assert main["hypothesis_verdict"]["verdict"] == "PASS" and main["artifacts"] and (out / "h32_run.md").read_text().isascii()
    # tamper: weekly series, permutation draws, missing artifact, wrong fingerprint
    f = out / "h32_run_H-32_mom1_W1_ic_weekly.csv"
    orig = f.read_bytes()
    lines = orig.split(b"\r\n")
    lines[3] = b"2,0.01"
    f.write_bytes(b"\r\n".join(lines))
    with pytest.raises(ArtifactError):
        testrun.verify_run_artifacts(out, pub, reg)
    f.write_bytes(orig)
    d = out / "h32_run_H-32_rev_gap_W2_perm_draws.csv"
    dorig = d.read_bytes()
    dl = dorig.split(b"\r\n")
    dl[2] = b"1,9.0"
    d.write_bytes(b"\r\n".join(dl))
    with pytest.raises(ArtifactError):
        testrun.verify_run_artifacts(out, pub, reg)
    d.write_bytes(dorig)
    testrun.verify_run_artifacts(out, pub, reg)
    d.unlink()
    with pytest.raises(ArtifactError, match="missing"):
        testrun.verify_run_artifacts(out, pub, reg)
    # a writer with a broken artifact publishes no verdict file
    out2 = tmp_path / "run2"
    broken = copy.deepcopy(pub)
    broken["results"]["H-32_mom1"]["payload"]["windows"]["W1"]["se_w"] += 1e-9
    broken["_series"] = run_sig["_series"]
    with pytest.raises(ArtifactError):
        testrun.write_run_artifacts(out2, broken, reg, pilot_sha256=sig["pilot_sha"])
    assert not (out2 / "h32_run.json").exists()


def test_t2_run_is_deterministic_n3_with_fingerprint(sig, shrunk, monkeypatch):
    monkeypatch.setattr(testrun, "_null_recheck", lambda win, registered, log: {"within_tolerance": True, "rows": {}, "n_reps": 0, "seed": 53})
    shas = [testrun.run_test(sig["panel"], sig["registered"], sig["pilot"], FP, registered_sha256=REGISTERED_SHA)["result_sha256"] for _ in range(3)]
    assert len(set(shas)) == 1


# ============================================================================
# positive control
# ============================================================================

@pytest.fixture(scope="module")
def pc_report(sig):
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        shape, symbols, _ = pc.build_shape(sig["panel"], sig["registered"]["seal"]["panel_cut_test"])
        return pc.run_positive_control(shape, symbols, sig["registered"], sig["pilot"], observed_fingerprints=FP,
                                       registered_sha256=REGISTERED_SHA, pilot_sha256=sig["pilot_sha"])


def test_t1_pc_positive_control_realised_effect_world_and_criteria(pc_report, sig, shrunk):
    r = pc_report
    assert r["bestanden"] is True and r["line"] == "Positivkontrolle BESTANDEN" and r["handed"] == ["mom1", "rev_gap"]
    for v, x in r["variants"].items():
        ho = sig["pilot"]["variants"][v]["handover"]
        tw = {wn: C.Z_KRIT * ho["per_window"][wn]["se_t"] + C.Z_POWER * ho["per_window"][wn]["sd_t"] for wn in ("W1", "W2")}
        assert x["binding_window"] == max(tw, key=tw.get) and x["target_effect"] == pytest.approx(tw[x["binding_window"]])
        inj = x["injection"]
        assert abs(inj["rel_error"]) <= C.PC_INJECT_TOL and inj["realized_effect"] == pytest.approx(x["target_effect"], rel=C.PC_INJECT_TOL)
        assert inj["signal_ic"] > x["target_effect"]                                         # calibrated on the REALISED effect, not the nominal one (fm8 damping)
        assert 0.6 < inj["realized_effect"] / inj["signal_ic"] < 0.95
        f2_null = {wn: x["f2_null"][wn] for wn in ("W1", "W2")}
        for wn in ("W1", "W2"):
            sg = x["sigma_g"][wn]
            if x["f2_real"] <= f2_null[wn]:
                assert sg["sigma_g"] == 0.0                                                   # Null-SD is the lower bound
            else:
                assert sg["sigma_g"] > 0.0 and abs(sg["rel_error"]) <= C.PC_WORLD_SD_TOL     # sigma_g found on the weekly SD
            assert x["weekly_sd_power_line"][wn] == pytest.approx(math.sqrt(sig["registered"]["windows"][wn]["frozen_v6"]["v_fm8"]
                                                                              + max(f2_null[wn], x["f2_real"])))
        c = x["criteria"]
        assert c["passed"] and all(c["a_sd_ratio"].values()) and c["b_pass_share"] and all(c["c_false_pass"].values()) and c["d_injection"]
        assert x["judgement"]["n_seeds"] == len(C.PC_SEEDS_JUDGE) == 16
        assert set(x["prd_sector_world_report_only"]["summary"]) >= {"pass_share_binding", "joint_c10_share_positive", "sd_ratio"}
        assert x["prd_sector_world_report_only"]["sigma_g_rel_sigma_e"] == 0.375
    assert "Gabelung" in r["label"] and r["not_computed"][0].startswith("real returns")
    assert r["criteria_constants"]["pass_share_min"] == C.PC_PASS_SHARE_MIN


def test_t1_pc_null_world_false_pass_rate_and_pass_share_semantics(pc_report, shrunk):
    for v, x in pc_report["variants"].items():
        j = x["judgement"]
        assert all(rate <= C.PC_NEG_PASS_MAX for rate in j["false_pass_rate_by_window"].values())
        assert j["pass_share_binding"] >= C.PC_PASS_SHARE_MIN and j["weekly_sd_world"]["W1"] > 0
        assert 0.0 <= j["joint_c10_share_positive"] <= min(j["pass_share_by_window"].values()) + 1e-12


def test_pc_not_bestanden_when_a_criterion_fails(sig, pc_report, shrunk, monkeypatch):
    shape, symbols, _ = pc.build_shape(sig["panel"], C.CUT_TEST)
    monkeypatch.setattr(C, "PC_PASS_SHARE_MIN", 1.01)                                          # (b) cannot be met
    with pytest.raises(Exception):
        schema.validate_registered(sig["registered"])                                            # the YAML pins the criteria: re-emit it
    reg = copy.deepcopy(sig["registered"])
    reg["positive_control"]["criteria"]["pass_share_min"] = 1.01
    r = pc.run_positive_control(shape, symbols, reg, sig["pilot"], observed_fingerprints=FP, registered_sha256=REGISTERED_SHA)
    assert r["bestanden"] is False and r["line"] == "Positivkontrolle NICHT BESTANDEN"
    assert all(not x["criteria"]["b_pass_share"] for x in r["variants"].values())
    assert pc.render_pc_markdown(r).startswith("Positivkontrolle NICHT BESTANDEN")


def test_pc_runs_only_with_a_handed_variant_and_has_no_returns_parameter(nul, sig, shrunk):
    shape, symbols, _ = pc.build_shape(nul["panel"], C.CUT_TEST)
    with pytest.raises(PositiveControlAbort, match="no variant was handed over"):
        pc.run_positive_control(shape, symbols, nul["registered"], nul["pilot"], observed_fingerprints=FP)
    assert "returns" not in inspect.signature(pc.run_positive_control).parameters
    assert not any("return" in p for p in inspect.signature(pc.run_positive_control).parameters)
    with pytest.raises(DataFingerprintError):
        pc.run_positive_control(shape, symbols, sig["registered"], sig["pilot"], observed_fingerprints={**FP, "union_range_fingerprint": "00" * 32})
    bad_shape = {**shape, "alive": shape["alive"][:, :-1]}
    with pytest.raises(ValueError, match="inconsistent"):
        pc.run_positive_control(bad_shape, symbols, sig["registered"], sig["pilot"], observed_fingerprints=FP)


def test_pc_never_sees_real_returns_same_masks_other_prices_give_the_identical_report(sig, pc_report, shrunk):
    other = F.relabel_prices(sig["panel"], 99)
    shape, symbols, _ = pc.build_shape(other, C.CUT_TEST)
    r = pc.run_positive_control(shape, symbols, sig["registered"], sig["pilot"], observed_fingerprints=FP, registered_sha256=REGISTERED_SHA,
                                pilot_sha256=sig["pilot_sha"])
    assert r["result_sha256"] == pc_report["result_sha256"]


def test_t2_pc_is_deterministic_n3_and_world_scales_come_only_from_the_yaml(sig, pc_report, shrunk):
    shape, symbols, _ = pc.build_shape(sig["panel"], C.CUT_TEST)
    again = [pc.run_positive_control(shape, symbols, sig["registered"], sig["pilot"], observed_fingerprints=FP, registered_sha256=REGISTERED_SHA,
                                     pilot_sha256=sig["pilot_sha"])["result_sha256"] for _ in range(2)]
    assert again[0] == again[1] == pc_report["result_sha256"]                                  # N = 3 with the module fixture
    reg = copy.deepcopy(sig["registered"])
    reg["windows"]["W1"]["null_scales"]["sigma_e_used"] *= 1.2
    r = pc.run_positive_control(shape, symbols, reg, sig["pilot"], observed_fingerprints=FP, registered_sha256=REGISTERED_SHA)
    assert r["result_sha256"] != pc_report["result_sha256"] and r["worlds"]["W1"]["sigma_e"] == pytest.approx(reg["windows"]["W1"]["null_scales"]["sigma_e_used"])
    w = pc.world_params(sig["registered"], "W2")
    assert set(w) == {"rho_f", "beta_sd", "sigma_f", "sigma_e", "target_factor_share", "drift_f"} and w["drift_f"] == 0.0


def test_pc_synthetic_world_injection_signal_negative_control_differs_only_by_the_injection(sig, shrunk, win_w1):
    world = pc.world_params(sig["registered"], "W1")
    kw = dict(alive_ext=win_w1.alive_ext, valid_ext=win_w1.valid_ext, symbols=win_w1.symbols, world=world, seed=5, window_index=0, sigma_g=0.03)
    pos = pc.synthesize_world(variant="mom1", signal_ic=0.1, **kw)
    neg = pc.synthesize_world(variant="mom1", signal_ic=0.0, **kw)
    neg2 = pc.synthesize_world(variant="mom1", signal_ic=0.0, **kw)
    assert np.array_equal(neg["returns"], neg2["returns"]) and pos["coefficient"] > 0 and neg["coefficient"] == 0.0
    assert not np.array_equal(pos["returns"], neg["returns"])
    # the first week (before any injection) is identical: common random numbers
    assert np.array_equal(pos["returns"][0], neg["returns"][0])
    m = win_w1.symbols.index("BTCUSDT")
    assert np.array_equal(pos["returns"][:, m], neg["returns"][:, m])                      # the market column is the factor in both
    p_series = pc.eval_world(pos, win_w1.alive_ext, win_w1.symbols, "mom1")
    n_series = pc.eval_world(neg, win_w1.alive_ext, win_w1.symbols, "mom1")
    assert np.nanmean(p_series) > np.nanmean(n_series) + 0.03
    rev = pc.synthesize_world(variant="rev_gap", signal_ic=0.1, **kw)
    assert np.nanmean(pc.eval_world(rev, win_w1.alive_ext, win_w1.symbols, "rev_gap")) < -0.03          # rev_gap is registered negative
