"""DEC-101 tests of the H-32 driver (H-32 registration, part 1): the universe filter (E1), the scaled null of the test run (E2),
the technical exactly-one-pilot lock (E3), the pins (E4: delisted tree, runner, universe, null scaling, pilot directory), the
q95 rule and the power line (E5) and the PP3 dry run / mu_sel placeholder (E6).

Pure parts are tested with hand calculations and Monte Carlo (with a tolerance); the mode-level parts run on the fixture
panels of ``tests/unit/h32_fixtures.py`` (nothing real is read).  The existing tests were adapted where DEC-101 changes the
behaviour (``universe``, ``null_scaling``, ``runner``, ``pilot_window.out_dir`` and the delisted-tree pin are mandatory
registration fields; the frozen ``q95`` is ``max(q95_1000, q95_10000)``; ``Spy`` replaces ``read_union_panel``)."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

from bybit_edge.research import power_p1 as pp
from bybit_edge.research.h32_fm8 import (checks, estimators as est, gate, handover, panel_cut, pilot as pilot_mod, pnull, pp3,
                                         powerline, schema, testrun, universe, vorlauf, weekly as wkl)
from bybit_edge.research.h32_fm8 import constants as C
from bybit_edge.research.h32_fm8.errors import (ArtifactError, DataFingerprintError, PilotLockError, PinError, RunnerPinError,
                                                SchemaError, UniverseError)
from bybit_edge.research.wp13_xsec import ic

from tests.unit import h32_fixtures as F
from tests.unit.h32_fixtures import REGISTERED_SHA, shrunk  # noqa: F401  (pytest fixture)

FP = dict(F.FAKE_FINGERPRINTS)
_N = NormalDist()


@pytest.fixture(scope="module")
def sig():
    return F.get_bundle("signal")


@pytest.fixture(scope="module")
def nul():
    return F.get_bundle("null")


# ============================================================================
# E1: the universe filter
# ============================================================================

@pytest.mark.parametrize("symbol, linear, cls", [
    ("BTCUSDT", True, "other"), ("1000PEPEUSDT", True, "other"), ("ICXUSDT#delisted", True, "other"),
    ("BTCPERP", False, "usdc_perp"), ("1000PEPEPERP", False, "usdc_perp"), ("BTCUSDT-25DEC26", False, "dated_future"),
    ("ETHUSDT-26MAR27", False, "dated_future"), ("BTC-25DEC26", False, "dated_future"), ("XYZUSDC", False, "other"),
    ("BTCUSD", False, "other"), ("BTC-USDT", False, "dated_future"),
])
def test_dec101_e1_classification(symbol, linear, cls):
    assert universe.is_linear_usdt_perpetual(symbol) is linear
    if not linear:
        assert universe.classify_excluded(symbol) == cls


def _k_series(panel):
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    wk = wkl.build_weekly(cut, C.CUT_TEST, with_turnover=False)
    return wk.alive.sum(axis=1)


def test_dec101_e1_twin_and_dated_future_are_removed_k_shrinks_and_the_report_is_exact():
    base = F.make_panel(seed=3, signal=0.0)
    twin = F.add_twins(base)
    assert twin["symbols"][-2:] == ["S002PERP", "S002USDT-25DEC26"]
    filtered, rep = universe.apply_universe(twin)
    assert rep == {"rule": "linear_usdt_perpetual", "n_before": len(base["symbols"]) + 2, "n_after": len(base["symbols"]),
                   "excluded": {"usdc_perp": 1, "dated_future": 1, "other": 0}, "excluded_symbols": ["S002PERP", "S002USDT-25DEC26"],
                   "excluded_sha256": hashlib.sha256("S002PERP\nS002USDT-25DEC26".encode()).hexdigest()}
    assert filtered["symbols"] == base["symbols"]
    for k in ("close", "turnover", "funding_n", "funding_sum"):
        assert np.array_equal(filtered[k], base[k], equal_nan=True)
    assert np.array_equal(filtered["is_delisted"], base["is_delisted"]) and filtered["last_alive_day"] == base["last_alive_day"]
    assert filtered["delisted_symbols"] == base["delisted_symbols"]
    assert (filtered["n_symbols_survivors"], filtered["n_symbols_delisted"]) == (base["n_symbols_survivors"], base["n_symbols_delisted"])
    k_base, k_twin, k_filt = _k_series(base), _k_series(twin), _k_series(filtered)
    assert (k_twin >= k_base).all() and (k_twin - k_base).max() == 2 and (k_twin > k_base).any()     # twins inflate K
    assert np.array_equal(k_filt, k_base)                                                           # K sinks back
    # idempotent; the input is not modified
    again, rep2 = universe.apply_universe(filtered)
    assert rep2["excluded"] == {"usdc_perp": 0, "dated_future": 0, "other": 0} and rep2["excluded_symbols"] == []
    assert rep2["excluded_sha256"] == hashlib.sha256(b"").hexdigest() and again["symbols"] == filtered["symbols"]
    assert twin["symbols"][-1] == "S002USDT-25DEC26" and twin["close"].shape[1] == len(base["symbols"]) + 2


def test_dec101_e1_other_class_relisting_episode_and_bookkeeping_dicts():
    base = F.make_panel(seed=3, signal=0.0)
    p = F.add_twins(base)
    j = p["symbols"].index("S001USDT")                                           # a delisted symbol of the fixture
    syms = list(p["symbols"])
    syms[j] = "S001USDT#delisted"                                                 # the earlier episode of a relisted symbol
    syms[-1] = "XYZUSDC"                                                          # neither a USDT perp, nor a twin, nor dated
    p["symbols"] = syms
    p["relisted_gaps"] = {"S001USDT": {"delist_date": "2023-01-02", "relist_first_day": "2023-02-01"},
                          "S002PERP": {"delist_date": "2023-01-02", "relist_first_day": "2023-02-01"}}
    p["relisted_symbols"] = ["S001USDT", "S002PERP"]
    p["delisted_symbols"] = ["S001USDT#delisted"]
    out, rep = universe.apply_universe(p)
    assert "S001USDT#delisted" in out["symbols"] and "S002PERP" not in out["symbols"] and "XYZUSDC" not in out["symbols"]
    assert rep["excluded"] == {"usdc_perp": 1, "dated_future": 0, "other": 1} and rep["excluded_symbols"] == ["S002PERP", "XYZUSDC"]
    assert list(out["relisted_gaps"]) == ["S001USDT"] and out["relisted_symbols"] == ["S001USDT"]
    assert out["delisted_symbols"] == ["S001USDT#delisted"]
    assert len(out["symbols"]) == out["close"].shape[1] == len(out["is_delisted"]) == len(out["last_alive_day"])


def test_dec101_e1_guard_and_ensure_universe():
    twin = F.add_twins(F.make_panel(seed=3, signal=0.0))
    with pytest.raises(UniverseError, match="S002PERP"):
        universe.assert_universe(twin)
    filtered, rep = universe.apply_universe(twin)
    universe.assert_universe(filtered)
    # without a report the filter is applied; with a report the panel must already be restricted
    f2, r2 = universe.ensure_universe(twin)
    assert r2["excluded"]["usdc_perp"] == 1 and f2["symbols"] == filtered["symbols"]
    with pytest.raises(UniverseError):
        universe.ensure_universe(twin, rep)
    assert universe.ensure_universe(filtered, rep)[1] is rep
    with pytest.raises(UniverseError, match="rule"):
        universe.ensure_universe(filtered, {**rep, "rule": "category_linear"})
    assert "linear_usdt_perpetual" in universe.universe_log_line(rep) and "DEC-101 E1" in universe.universe_log_line(rep)


# ============================================================================
# E1 / E2 / E3 / E4 / E5: the registration blocks and their pins
# ============================================================================

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
    # E1: universe
    (_drop(("universe",)), SchemaError), (_set(("universe", "rule"), "category_linear"), PinError), (_drop(("universe", "rule")), PinError),
    (_drop(("universe", "label")), SchemaError), (_drop(("universe", "excluded_at_prelaunch")), SchemaError),
    (_drop(("universe", "excluded_at_prelaunch", "dated_future")), SchemaError), (_set(("universe", "excluded_at_prelaunch", "other"), -1), SchemaError),
    # E2: null scaling
    (_drop(("null_scaling",)), SchemaError), (_set(("null_scaling", "enabled"), False), PinError), (_set(("null_scaling", "rule"), "k = 1"), PinError),
    (_set(("null_scaling", "direction"), "testability"), PinError), (_set(("null_scaling", "ref"), "DEC-99"), PinError),
    # E3: the pilot directory
    (_drop(("pilot_window", "out_dir")), SchemaError), (_set(("pilot_window", "out_dir"), "/tmp/h32_pilot"), SchemaError),
    (_set(("pilot_window", "out_dir"), "scinance3-impl/state/runs/../x"), SchemaError), (_set(("pilot_window", "out_dir"), "data/harvest/h32"), SchemaError),
    (_set(("pilot_window", "out_dir"), "scinance3-impl/state/runs"), SchemaError), (_set(("pilot_window", "out_dir"), "elsewhere/h32_pilot_v1"), SchemaError),
    # E4: runner and the delisted-tree pin
    (_drop(("runner",)), SchemaError), (_set(("runner", "as_of"), "28.09.2026"), SchemaError), (_set(("runner", "allow_partial"), 1), SchemaError),
    (_set(("runner", "end_year"), 2020), SchemaError), (_drop(("runner", "start_year")), SchemaError),
    (_drop(("data_fingerprints", "delisted_tree_sha256")), SchemaError), (_set(("data_fingerprints", "delisted_tree_sha256"), None), SchemaError),
    # E5: the q95 rule
    (_drop(("windows", "W1", "frozen_v6", "q95_1000")), SchemaError), (_drop(("windows", "W2", "frozen_v6", "q95_10000")), SchemaError),
    (_set(("windows", "W1", "frozen_v6", "q95", "mom1"), 123.0), PinError),
])
def test_dec101_registration_blocks_are_mandatory_and_pinned(nul, shrunk, mutate, exc):
    reg = copy.deepcopy(nul["registered"])
    mutate(reg)
    with pytest.raises(exc):
        schema.validate_registered(reg)


def test_dec101_registration_carries_the_blocks_the_template_emits(nul, shrunk):
    reg = nul["registered"]
    schema.validate_registered(reg)
    rep = nul["report"]
    assert reg["universe"]["rule"] == C.UNIVERSE_RULE and reg["universe"]["label"] == C.UNIVERSE_LABEL
    assert reg["universe"]["excluded_at_prelaunch"] == rep["universe"]["excluded"] == {"usdc_perp": 0, "dated_future": 0, "other": 0}
    assert reg["null_scaling"] == {"enabled": True, "rule": C.NULL_SCALING_RULE, "direction": "strictness", "ref": "DEC-101 E2"}
    assert reg["runner"] == F.RUNNER and reg["pilot_window"]["out_dir"] == C.PILOT_OUT_DIR == "scinance3-impl/state/runs/h32_pilot_v1"
    assert reg["data_fingerprints"]["delisted_tree_sha256"] == FP["delisted_tree_sha256"]
    assert reg["data_fingerprints"]["delisting_register_sha256"] == FP["delisting_register_sha256"]
    for wn in ("W1", "W2"):
        fz = reg["windows"][wn]["frozen_v6"]
        assert {"q95_1000", "q95_10000"} <= set(fz) and all(fz["q95"][v] == max(fz["q95_1000"][v], fz["q95_10000"][v]) for v in C.VARIANTS)
    pins = schema.frozen_pin_table(reg)
    assert pins["universe_rule"] == C.UNIVERSE_RULE and pins["runner"]["as_of"] == "2026-09-28" and pins["out_dir"] == C.PILOT_OUT_DIR
    assert pins["delisted_tree_sha256"] == FP["delisted_tree_sha256"] and pins["null_scaling_enabled"] is True
    assert pins["W1"]["q95_1000"] == reg["windows"]["W1"]["frozen_v6"]["q95_1000"]
    # the header states the W1 control note and the universe label
    text = vorlauf.template_yaml_text(vorlauf.build_template({k: v for k, v in rep.items() if k != "_p_payload"}, bounce_spread=0.003621), rep)
    assert "# " + C.W1_CONTROL_NOTE in text and "entfaellt (DEC-100 N1)" in text and "PP3-Trockenprobe" in text
    assert C.UNIVERSE_LABEL in text and "nicht angefordert" not in text


def test_dec101_template_refuses_an_artifact_without_the_universe_or_the_runner(nul, shrunk):
    rep = {k: v for k, v in nul["report"].items() if k != "_p_payload"}
    for key in ("universe", "runner"):
        bad = dict(rep)
        bad[key] = None
        with pytest.raises(ValueError, match="re-run --prelaunch"):
            vorlauf.build_template(bad, bounce_spread=0.003621)


def test_dec101_e4_runner_pins_are_checked_with_both_values():
    reg = {"runner": {"as_of": "2026-09-28", "start_year": 2021, "end_year": 2026, "allow_partial": True}}
    good = {"as_of": "2026-09-28", "start_year": 2021, "end_year": 2026, "allow_partial": True}
    checks.check_runner_pins(reg, good)
    checks.check_runner_pins({"runner": {**reg["runner"], "as_of": __import__("datetime").date(2026, 9, 28)}}, good)    # a YAML date
    for key, bad in (("as_of", "2026-10-21"), ("as_of", ""), ("start_year", 2022), ("end_year", 2027), ("allow_partial", False)):
        with pytest.raises(RunnerPinError) as ei:
            checks.check_runner_pins(reg, {**good, key: bad})
        msg = str(ei.value)
        assert key in msg and "registered" in msg and "CLI" in msg
        assert repr(reg["runner"][key]) in msg and (repr(bad) in msg or key == "as_of" and bad == "")
    with pytest.raises(RunnerPinError, match="as_of.*start_year"):
        checks.check_runner_pins(reg, {**good, "as_of": "2026-01-01", "start_year": 2020})
    with pytest.raises(RunnerPinError, match="without a runner block"):
        checks.check_runner_pins({}, good)


def test_dec101_e1_universe_pin_rule_and_counts(nul):
    reg = nul["registered"]
    rep = {"rule": C.UNIVERSE_RULE, "excluded": {"usdc_perp": 0, "dated_future": 0, "other": 0}}
    checks.check_universe_pin(reg, rep)
    with pytest.raises(UniverseError, match="rule"):
        checks.check_universe_pin(reg, {**rep, "rule": "category_linear"})
    with pytest.raises(UniverseError, match="usdc_perp"):
        checks.check_universe_pin(reg, {**rep, "excluded": {**rep["excluded"], "usdc_perp": 5}})
    with pytest.raises(UniverseError, match="no universe report"):
        checks.check_universe_pin(reg, None)
    with pytest.raises(UniverseError, match="without a universe block"):
        checks.check_universe_pin({}, rep)


def test_dec101_data_fingerprints_pin_the_delisted_tree_in_every_mode(sig):
    reg = sig["registered"]
    checks.check_data_fingerprints(reg, FP)
    with pytest.raises(DataFingerprintError, match="delisted_tree_sha256"):
        checks.check_data_fingerprints(reg, {**FP, "delisted_tree_sha256": "00" * 32})
    with pytest.raises(DataFingerprintError, match="delisted_tree_sha256"):
        checks.check_data_fingerprints(reg, {k: v for k, v in FP.items() if k != "delisted_tree_sha256"})
    no_pin = copy.deepcopy(reg)
    del no_pin["data_fingerprints"]["delisted_tree_sha256"]                    # B-5: absent in the YAML is no longer silently accepted
    with pytest.raises(DataFingerprintError):
        checks.check_data_fingerprints(no_pin, FP)


# ============================================================================
# E1 in the modes: the filter runs before the cut and any calculation
# ============================================================================

def test_dec101_e1_pilot_on_a_twin_panel_equals_the_pilot_on_the_clean_panel_and_pins_the_counts(sig, shrunk):
    reg = copy.deepcopy(sig["registered"])
    twin = F.add_twins(sig["panel"])
    with pytest.raises(UniverseError, match="usdc_perp"):                           # the pin says 0 twins, the panel has 1
        pilot_mod.run_pilot(twin, reg, FP, registered_sha256=REGISTERED_SHA)
    reg["universe"]["excluded_at_prelaunch"] = {"usdc_perp": 1, "dated_future": 1, "other": 0}
    pr = pilot_mod.run_pilot(twin, reg, FP, registered_sha256=REGISTERED_SHA)
    assert pr["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0} and pr["universe"]["rule"] == C.UNIVERSE_RULE
    for v in C.VARIANTS:
        assert pr["variants"][v]["stats"] == sig["pilot_report"]["variants"][v]["stats"]           # the twins changed nothing
    assert pr["panel"]["n_symbols"] == sig["pilot_report"]["panel"]["n_symbols"]
    # a report from the driver is accepted only for a panel that is already restricted
    _, urep = universe.apply_universe(twin)
    with pytest.raises(UniverseError):
        pilot_mod.run_pilot(twin, reg, FP, registered_sha256=REGISTERED_SHA, universe_report=urep)
    wrong = copy.deepcopy(reg)
    wrong["universe"]["rule"] = "category_linear"
    with pytest.raises(PinError):
        pilot_mod.run_pilot(sig["panel"], wrong, FP)
    assert "Universum linear_usdt_perpetual" in pilot_mod.render_pilot_markdown({k: v for k, v in pr.items() if k != "_series"})


def test_dec101_e1_vorlauf_and_run_and_pp3_and_control_restrict_the_panel_and_carry_the_report(sig, shrunk):
    twin = F.add_twins(sig["panel"])
    reg = copy.deepcopy(sig["registered"])
    reg["universe"]["excluded_at_prelaunch"] = {"usdc_perp": 1, "dated_future": 1, "other": 0}
    with pytest.raises(UniverseError):
        testrun.run_test(twin, sig["registered"], sig["pilot"], FP, registered_sha256=REGISTERED_SHA, p_replicates=sig["p_rep"])
    with pytest.raises(UniverseError):
        pp3.run_pp3_dry_run(twin, sig["registered"], FP, registered_sha256=REGISTERED_SHA)
    rep = pp3.run_pp3_dry_run(twin, reg, FP, registered_sha256=REGISTERED_SHA)
    assert rep["ok"] and rep["universe"]["excluded"]["usdc_perp"] == 1
    from bybit_edge.research.h32_fm8 import positive_control as pc
    shape, symbols, _ = pc.build_shape(sig["panel"], C.CUT_TEST)
    assert all(universe.is_linear_usdt_perpetual(s) for s in symbols)
    with pytest.raises(UniverseError):
        pc.build_shape(twin, C.CUT_TEST)                                            # the shape is the shape of the universe panel
    out = vorlauf.assemble_prelaunch(twin, dict(FP), cut_date=C.CUT_TEST, n_reps=C.N_REPS_MIN, n_boot=C.N_BOOT_MIN,
                                     calibration_kwargs=F.calibration_kwargs(), runner=dict(F.RUNNER))
    assert out["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0} and out["cut"]["n_symbols"] <= len(sig["panel"]["symbols"])
    assert out["result_sha256"] == sig["report"]["result_sha256"] or out["universe"] != sig["report"]["universe"]


# ============================================================================
# E2: the scaled null
# ============================================================================

def test_dec101_e2_k_one_reproduces_the_old_behaviour_for_m_nonnegative():
    q, m = 0.0127, 0.0011
    assert est.q95_effective(m, 1.0, q) == pytest.approx(q, abs=1e-15)
    d = np.random.default_rng(1).normal(0.001, 0.007, 500)
    assert np.allclose(est.scaled_replicates(d, m, 1.0), d, atol=1e-15)
    assert np.allclose(est.scaled_replicates(d, 0.0, 1.0), d, atol=1e-15)
    y = 0.012
    a, b = pnull.replicate_pvalue(y, est.scaled_replicates(d, m, 1.0)), pnull.replicate_pvalue(y, d)
    assert (a["p_value"], a["count_ge"], a["n_reps"]) == (b["p_value"], b["count_ge"], b["n_reps"])
    assert est.scale_factor(0.04, 0.05) == 1.0 and est.scale_factor(0.05, 0.05) == 1.0         # never below 1: no credit for a lower SD


def test_dec101_e2_negative_null_mean_gives_no_credit():
    q, m = 0.0086, -0.0011                                                          # rev_gap-like binding cell
    assert est.q95_effective(m, 1.0, q) == pytest.approx(q + 0.0011, abs=1e-15) and est.q95_effective(m, 1.0, q) >= q
    assert est.q95_effective(m, 1.3, q) == pytest.approx(1.3 * (q + 0.0011)) and est.q95_effective(m, 1.3, q) > q
    d = np.random.default_rng(2).normal(m, 0.005, 2000)
    dp = est.scaled_replicates(d, m, 1.0)
    assert np.allclose(dp, d + 0.0011, atol=1e-15)                                  # the centre moves from m to 0: shifted up by |m|
    for y in (0.0, 0.004, 0.008):
        assert pnull.replicate_pvalue(y, dp)["p_value"] >= pnull.replicate_pvalue(y, d)["p_value"]


def test_dec101_e2_inflated_real_sd_gives_higher_q95_eff_and_larger_p():
    m, q = 0.0012, 0.0118
    d = np.random.default_rng(3).normal(m, 0.0065, 4000)
    k1, k2 = est.scale_factor(0.0431, 0.0431), est.scale_factor(0.0431 * 1.13, 0.0431)
    assert k1 == 1.0 and k2 == pytest.approx(1.13)
    assert est.q95_effective(m, k2, q) == pytest.approx(m + 1.13 * (q - m))
    assert est.q95_effective(m, k2, q) > est.q95_effective(m, k1, q)
    ps = [pnull.replicate_pvalue(0.0135, est.scaled_replicates(d, m, k))["p_value"] for k in (1.0, 1.1, 1.3, 1.6, 2.5)]
    assert all(a <= b for a, b in zip(ps, ps[1:])) and ps[-1] > ps[0]                # y > m: p is non-decreasing in k
    # the fixed point: a y exactly at the centre is neutral to the scaling (m >= 0)
    assert est.q95_effective(m, 5.0, m) == pytest.approx(m)
    # fails closed
    assert math.isnan(est.scale_factor(float("nan"), 0.04)) and math.isnan(est.scale_factor(0.04, 0.0)) and math.isnan(est.scale_factor(0.04, float("nan")))
    assert math.isnan(est.q95_effective(m, float("nan"), q)) and np.isnan(est.scaled_replicates(d, m, float("nan"))).all()
    assert pnull.replicate_pvalue(0.02, est.scaled_replicates(d, m, float("nan")))["p_value"] == 1.0


def test_dec101_e2_the_gate_derives_k_and_q95_eff_from_the_payload_alone():
    def pay(y1, sd_real):
        ns = {"sd_real": sd_real, "sd_week": 0.05, "m": 0.001, "q95_frozen": 0.017}
        w = {"y": y1, "mean_ic": y1, "se_w": 0.010, "q95": 0.017, "ceiling_k4": 0.005, "threshold_frozen": 0.0175, "bounce_ic": None,
             "w_judged": 52, "null_scaling": dict(ns)}
        return {"entry": "H-32_mom1", "variant": "mom1", "direction": "positive", "z_krit": C.Z_KRIT, "windows": {"W1": w, "W2": copy.deepcopy(w)}}
    ok = gate.evaluate(pay(0.021, 0.05))                                          # k = 1: q95_eff = 0.017
    assert ok["verdict"] == "PASS" and ok["per_window"]["W1"]["k"] == 1.0 and ok["per_window"]["W1"]["q95_effective"] == pytest.approx(0.017)
    inflated = gate.evaluate(pay(0.019, 0.06))                                    # k = 1.2: q95_eff = 0.001 + 1.2 * 0.016 = 0.0202 > 0.019 > 0.017
    assert inflated["per_window"]["W1"]["q95_effective"] == pytest.approx(0.0202) and inflated["per_window"]["W1"]["k"] == pytest.approx(1.2)
    assert inflated["verdict"] == "DROP" and not inflated["per_window"]["W1"]["c_null_quantile"] and inflated["per_window"]["W1"]["b_magnitude"]
    assert any("(1c) y >= q95_eff" in lab and "k=1.2" in lab for lab in inflated["labels"])
    assert gate.evaluate(pay(0.019, 0.05))["verdict"] == "PASS"                   # the frozen q95 alone would have passed it
    assert gate.evaluate(copy.deepcopy(pay(0.019, 0.06))) == inflated             # pure
    # without a null_scaling block the gate uses the frozen q95 as before (k = 1)
    old = {"entry": "e", "variant": "mom1", "direction": "positive", "z_krit": C.Z_KRIT,
           "windows": {"W1": {"y": 0.02, "se_w": 0.01, "q95": 0.017, "ceiling_k4": 0.005, "threshold_frozen": 0.0175}}}
    assert gate.evaluate(old)["per_window"]["W1"]["k"] == 1.0 and gate.evaluate(old)["per_window"]["W1"]["q95_effective"] == 0.017
    nan_sd = pay(0.05, float("nan"))
    assert gate.evaluate(nan_sd)["verdict"] == "DROP"                              # fails closed


@pytest.fixture(scope="module")
def run_sig(sig):
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        mp.setattr(testrun, "_null_recheck", lambda win, registered, log: {"within_tolerance": True, "rows": {}, "n_reps": 0, "seed": 53})
        return testrun.run_test(sig["panel"], sig["registered"], sig["pilot"], FP, registered_sha256=REGISTERED_SHA, p_replicates=sig["p_rep"])


def _run_with(sig, factor):
    reg = copy.deepcopy(sig["registered"])
    for wn in ("W1", "W2"):
        for v in C.VARIANTS:
            reg["windows"][wn]["frozen_v6"]["sd_week"][v] *= factor
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        mp.setattr(testrun, "_null_recheck", lambda win, registered, log: {"within_tolerance": True, "rows": {}, "n_reps": 0, "seed": 53})
        return testrun.run_test(sig["panel"], reg, sig["pilot"], FP, registered_sha256=REGISTERED_SHA, p_replicates=sig["p_rep"])


def test_dec101_e2_run_payload_carries_the_scaling_and_t4_arithmetic_holds(run_sig, sig, shrunk):
    reg = sig["registered"]
    assert run_sig["null_scaling"]["rule"] == C.NULL_SCALING_RULE and run_sig["universe"]["rule"] == C.UNIVERSE_RULE
    for e in ("H-32_mom1", "H-32_rev_gap"):
        res = run_sig["results"][e]
        v = res["variant"]
        assert res["payload"]["constants"]["null_scaling"]["enabled"] is True
        for wn in ("W1", "W2"):
            w, det = res["payload"]["windows"][wn], res["details"][wn]
            fz = reg["windows"][wn]["frozen_v6"]
            ns = w["null_scaling"]
            assert ns["sd_week"] == fz["sd_week"][v] and ns["m"] == fz["null_mean"][v] and ns["q95_frozen"] == fz["q95"][v] == w["q95"]
            assert ns["sd_real"] == det["se_detail"]["sd_ic"]
            k = max(1.0, ns["sd_real"] / ns["sd_week"])
            assert ns["k"] == k and ns["q95_eff"] == pytest.approx(max(0.0, ns["m"]) + k * (ns["q95_frozen"] - ns["m"]), abs=1e-15)
            sc = det["p_null"]["scaling"]
            assert (sc["k"], sc["sd_real"], sc["sd_week"], sc["m"], sc["q95_frozen"], sc["q95_eff"]) == (
                ns["k"], ns["sd_real"], ns["sd_week"], ns["m"], ns["q95_frozen"], ns["q95_eff"]) and sc["p"] == det["p_null"]["p_value"]
            # the binding p comes from the transformed replicates d' = max(0, m) + k (d - m)
            d = pnull.draws_for(sig["p_rep"], wn, v)
            dprime = max(0.0, ns["m"]) + k * (d - ns["m"])
            assert pnull.replicate_pvalue(w["y"], dprime)["p_value"] == det["p_null"]["p_value"]
            assert pnull.replicate_pvalue(w["y"], d)["p_value"] == det["p_null"]["p_value_unscaled_report_only"]
            # (1c) of the gate uses q95_eff
            assert res["verdict"]["per_window"][wn]["q95_effective"] == ns["q95_eff"] and res["verdict"]["per_window"][wn]["k"] == k
            assert res["verdict"]["per_window"][wn]["c_null_quantile"] == (w["y"] >= ns["q95_eff"])
        assert res["p_max"] == max(res["details"][wn]["p_null"]["p_value"] for wn in ("W1", "W2"))
        assert any(lab.startswith("skalierte Null W1 (DEC-101 E2)") for lab in res["verdict"]["labels"])
        assert "unskaliert" in " ".join(res["verdict"]["labels"]) and "unscaled_null_max_p" in res["p_report_only"]
    md = testrun.render_run_markdown({k: v for k, v in run_sig.items() if k != "_series"})
    assert "Skalierte Null (DEC-101 E2)" in md and "->" in md and "q95 eingefroren -> effektiv" in md and md.isascii()
    assert "Universum linear_usdt_perpetual" in md


def test_dec101_e2_k_one_run_equals_the_frozen_null_run_for_m_nonnegative_and_is_stricter_for_m_negative(sig, shrunk):
    big = _run_with(sig, 100.0)                                                       # sd_week huge: k = 1 everywhere
    for e in ("H-32_mom1", "H-32_rev_gap"):
        res = big["results"][e]
        for wn in ("W1", "W2"):
            sc = res["details"][wn]["p_null"]["scaling"]
            assert sc["k"] == 1.0
            p, p0 = res["details"][wn]["p_null"]["p_value"], res["details"][wn]["p_null"]["p_value_unscaled_report_only"]
            if sc["m"] >= 0.0:
                assert p == p0 and sc["q95_eff"] == pytest.approx(sc["q95_frozen"], abs=1e-15)      # the old behaviour
            else:
                assert p >= p0 and sc["q95_eff"] >= sc["q95_frozen"]                                 # no credit for a negative null mean


def test_dec101_e2_inflated_real_sd_raises_q95_eff_and_p_and_flows_into_f_week(run_sig, sig, shrunk):
    inflated = _run_with(sig, 0.5)                                                    # real SD / frozen SD at least doubles
    for e in ("H-32_mom1", "H-32_rev_gap"):
        base, inf = run_sig["results"][e], inflated["results"][e]
        for wn in ("W1", "W2"):
            sb, si = base["details"][wn]["p_null"]["scaling"], inf["details"][wn]["p_null"]["scaling"]
            assert si["k"] > 1.0 and si["k"] >= sb["k"] and si["k"] == pytest.approx(max(1.0, si["sd_real"] / si["sd_week"]))
            assert si["sd_week"] == pytest.approx(0.5 * sb["sd_week"])
            assert si["q95_eff"] > sb["q95_eff"] and inf["details"][wn]["p_null"]["p_value"] >= base["details"][wn]["p_null"]["p_value"]
            assert inf["details"][wn]["p_null"]["p_value"] <= 1.0
        # F-WEEK works on the scaled p (BY gets exactly the scaled p_max)
        assert inf["verdict"]["fweek"]["p_max"] == inf["p_max"] == max(inf["details"][wn]["p_null"]["p_value"] for wn in ("W1", "W2"))
    by_p = {k: p for k, p in inflated["fweek"]["by"]["p_sorted"]}
    assert by_p["H-32_mom1"] == inflated["results"]["H-32_mom1"]["p_max"] and by_p["H-32_rev_gap"] == inflated["results"]["H-32_rev_gap"]["p_max"]
    ruin = _run_with(sig, 0.02)                                                       # k ~ 50: q95_eff far above any realised statistic
    for e in ("H-32_mom1", "H-32_rev_gap"):
        assert ruin["results"][e]["verdict"]["verdict"] == "DROP" and not ruin["results"][e]["verdict"]["per_window"]["W1"]["c_null_quantile"]
    assert ruin["hypothesis_verdict"]["verdict"] == "DROP"


def test_dec101_e2_artifact_round_trip_re_derives_the_scaled_null(run_sig, sig, shrunk, tmp_path):
    reg = sig["registered"]
    out = tmp_path / "run"
    testrun.write_run_artifacts(out, run_sig, reg, pilot_sha256=sig["pilot_sha"], p_replicates=sig["p_rep"])
    pub = {k: v for k, v in run_sig.items() if k != "_series"}
    assert testrun.verify_run_artifacts(out, pub, reg, p_replicates=sig["p_rep"])["n_entry_windows_checked"] == 4
    for path, bump in ((("payload", "windows", "W1", "null_scaling", "sd_real"), 1e-6), (("payload", "windows", "W2", "null_scaling", "q95_eff"), 1e-6),
                       (("payload", "windows", "W1", "null_scaling", "k"), 0.5)):
        bad = copy.deepcopy(pub)
        cur = bad["results"]["H-32_mom1"]
        for key in path[:-1]:
            cur = cur[key]
        cur[path[-1]] += bump
        with pytest.raises(ArtifactError, match="scaled null"):
            testrun.verify_run_artifacts(out, bad, reg, p_replicates=sig["p_rep"])
    bad = copy.deepcopy(pub)
    bad["results"]["H-32_mom1"]["details"]["W1"]["p_null"]["p_value"] = 0.5
    with pytest.raises(ArtifactError, match="pinned null replicates"):
        testrun.verify_run_artifacts(out, bad, reg, p_replicates=sig["p_rep"])


# ============================================================================
# E3: exactly one pilot, technically
# ============================================================================

def _fake_repo(tmp_path, reg):
    repo = tmp_path / "repo"
    runs = repo / C.RUNS_REL
    runs.mkdir(parents=True)
    return repo, runs, repo / reg["pilot_window"]["out_dir"]


def _pilot_json(path: Path, sha: str, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": C.PILOT_SCHEMA, "mode": "pilot", "registered_sha256": sha, **extra}), encoding="utf-8")


def test_dec101_e3_only_the_pinned_out_dir_is_accepted(nul, tmp_path):
    reg = nul["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    assert checks.pilot_dir(reg, repo) == pinned.resolve()
    assert checks.check_pilot_out_dir(pinned, reg, repo) == pinned.resolve()
    assert checks.check_pilot_out_dir(str(pinned) + "/", reg, repo) == pinned.resolve()
    assert checks.check_pilot_out_dir(runs / "x" / ".." / "h32_pilot_v1", reg, repo) == pinned.resolve()              # resolved paths are compared
    for bad in (runs / "h32_pilot_v2", runs, tmp_path / "other", pinned / "sub", Path("data/harvest/h32_pilot_v1")):
        with pytest.raises(PilotLockError, match="pilot directory pinned"):
            checks.check_pilot_out_dir(bad, reg, repo)
    with pytest.raises(PilotLockError, match="pilot directory pinned"):
        checks.check_rerun_lock(runs / "elsewhere", reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    with pytest.raises(PilotLockError, match="pilot directory pinned"):                                                # also with a DEC reference
        checks.check_rerun_lock(runs / "elsewhere", reg, "DEC-102", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    assert checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)["rerun"] is False


def test_dec101_e3_an_earlier_pilot_result_anywhere_below_runs_blocks_a_new_directory(nul, tmp_path):
    reg = nul["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    _pilot_json(runs / "somewhere" / "deep" / "h32_pilot.json", "ab" * 32)                       # another registration: no hit
    _pilot_json(runs / "somewhere" / "h32_other.json", REGISTERED_SHA)                           # not the pilot name pattern: no hit
    assert checks.find_pilot_results(runs, REGISTERED_SHA) == []
    lock = checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    assert lock["rerun"] is False and lock["prefix"] == "h32_pilot" and lock["scope"]["found"] == []
    _pilot_json(runs / "h32_pilot_old_attempt" / "h32_pilot.json", REGISTERED_SHA.upper())      # a pilot of THIS registration elsewhere
    assert checks.find_pilot_results(runs, REGISTERED_SHA) == ["h32_pilot_old_attempt/h32_pilot.json"]
    with pytest.raises(PilotLockError, match=r"already exists.*h32_pilot_old_attempt/h32_pilot\.json.*exactly one pilot run"):
        checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    with pytest.raises(PilotLockError, match="not a DEC"):
        checks.check_rerun_lock(pinned, reg, "because", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    lock2 = checks.check_rerun_lock(pinned, reg, "DEC-102", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    assert lock2["rerun"] is True and lock2["prefix"] == "h32_pilot_rerun_DEC-102" and lock2["earlier_found"] == ["h32_pilot_old_attempt/h32_pilot.json"]
    # a DEC without any earlier result is refused, a further re-run under the same DEC too
    with pytest.raises(PilotLockError, match="no earlier pilot"):
        checks.check_rerun_lock(pinned, reg, "DEC-102", registered_sha256="cd" * 32, runs_root=runs, repo_root=repo)
    _pilot_json(pinned / "h32_pilot_rerun_DEC-102.json", REGISTERED_SHA)
    with pytest.raises(PilotLockError, match="needs its own DEC"):
        checks.check_rerun_lock(pinned, reg, "DEC-102", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    # without runs_root / registered_sha256 the lock is the DEC-99 lock (this directory only)
    assert checks.check_rerun_lock(tmp_path / "unrelated", reg, None) == {"rerun": False, "prefix": "h32_pilot"}


def test_dec101_e3_search_matches_the_fingerprint_file_and_refuses_unreadable_pilot_files_and_opens_no_sealed_file(nul, tmp_path, monkeypatch):
    reg = nul["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    _pilot_json(runs / "a" / "h32_pilot_fingerprint.json", REGISTERED_SHA)                      # the fingerprint file names the registration too
    assert checks.find_pilot_results(runs, REGISTERED_SHA) == ["a/h32_pilot_fingerprint.json"]
    sealed = [runs / "a" / "w1_L_window_sealed.json", runs / "b" / "weekly_ic_series.csv", runs / "c" / "ic_series_x_UNION_REAL.csv"]
    for s in sealed:
        s.parent.mkdir(parents=True, exist_ok=True)
        s.write_text("not json {", encoding="utf-8")
    opened = []
    orig = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: (opened.append(self.name), orig(self, *a, **k))[1])
    assert checks.find_pilot_results(runs, REGISTERED_SHA) == ["a/h32_pilot_fingerprint.json"]
    assert opened == ["h32_pilot_fingerprint.json"]                                              # only the pilot name pattern is ever opened
    (runs / "d").mkdir()
    (runs / "d" / "h32_pilot_broken.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(PilotLockError, match="cannot be read"):
        checks.find_pilot_results(runs, REGISTERED_SHA)
    assert checks.find_pilot_results(tmp_path / "no_such_dir", REGISTERED_SHA) == []


def test_dec101_e3_writer_rechecks_the_technical_lock(sig, shrunk, tmp_path):
    reg = sig["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    lock = checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    _pilot_json(runs / "raced" / "h32_pilot.json", REGISTERED_SHA)                               # another process wrote a pilot in between
    with pytest.raises(PilotLockError, match="exactly one pilot run"):
        pilot_mod.write_pilot_artifacts(pinned, sig["pilot_report"], reg, lock)
    assert not pinned.exists() or not any(pinned.iterdir())
    wrong_dir = tmp_path / "repo" / C.RUNS_REL / "h32_other"
    with pytest.raises(PilotLockError, match="pilot directory pinned"):
        pilot_mod.write_pilot_artifacts(wrong_dir, sig["pilot_report"], reg, lock)


# ============================================================================
# E5: the q95 rule and the power line
# ============================================================================

def test_dec101_e5_frozen_q95_is_the_larger_of_the_two_quantiles_and_both_are_reported():
    d = np.random.default_rng(1).normal(0.001, 0.007, 10_000)
    r = est.frozen_q95(0.0100, d)
    assert r["q95_10000"] == float(np.quantile(d, 0.95)) and r["q95_1000"] == 0.0100 and r["q95"] == max(0.0100, r["q95_10000"])
    assert r["q95"] == r["q95_10000"] > 0.0100 and r["n_p_replicates"] == 10_000 and "linear" in r["method"]
    assert est.frozen_q95(1.0, d)["q95"] == 1.0                                                 # the 1,000-replicate value binds when larger
    dn = d.copy()
    dn[:50] = np.nan
    assert est.frozen_q95(0.0, dn)["q95_10000"] == float(np.quantile(dn[np.isfinite(dn)], 0.95)) and est.frozen_q95(0.0, dn)["n_p_replicates"] == 9950
    assert est.frozen_q95(0.02, np.full(5, np.nan))["q95"] == 0.02 and math.isnan(est.frozen_q95(0.02, np.full(5, np.nan))["q95_10000"])


def test_dec101_e5_vorlauf_freezes_the_q95_rule_per_window_and_variant(sig, shrunk):
    rep, reg = sig["report"], sig["registered"]
    pay = rep["_p_payload"]
    assert rep["parameters"]["q95_rule"].startswith("q95 = max(q95_1000, q95_10000)") and "linear" in rep["parameters"]["q95_method"]
    for wn in ("W1", "W2"):
        fz = rep["windows"][wn]["frozen_v6"]
        cells = rep["windows"][wn]["null"]["frozen"]
        for v in C.VARIANTS:
            draws = np.asarray(pay["windows"][wn]["variants"][v], dtype=np.float64)
            assert fz["q95_10000"][v] == float(np.quantile(draws[np.isfinite(draws)], 0.95))
            assert fz["q95_1000"][v] == cells["q95"][v] == max(cells["q95_driftfree"][v], cells["q95_drifting"][v])
            assert fz["q95"][v] == max(fz["q95_1000"][v], fz["q95_10000"][v])
            assert reg["windows"][wn]["frozen_v6"]["q95"][v] == fz["q95"][v]
        assert set(rep["windows"][wn]["q95_rule"]["binding"].values()) <= {"q95_1000", "q95_10000"}
    md = vorlauf.render_prelaunch_markdown(rep)
    assert "q95_1000" in md and "q95_10000" in md and "Power-Zeile (DEC-101 E5, report-only)" in md and md.isascii()
    assert "Universum linear_usdt_perpetual" in md and "Runner (DEC-101 E4)" in md and "entfaellt (DEC-100 N1)" in md


def test_dec101_e5_null_recheck_compares_the_recomputed_q95_with_q95_1000(sig, shrunk, monkeypatch):
    seen = {}
    real = testrun.assert_null_value

    def spy(recomputed, frozen, *, label):
        seen[label] = frozen
        return real(recomputed, frozen, label=label)

    monkeypatch.setattr(testrun, "assert_null_value", spy)
    cut, _ = panel_cut.cut_panel_days(sig["panel"], C.CUT_TEST)
    win = wkl.make_window(wkl.build_weekly(cut, C.CUT_TEST), "W1")
    testrun._null_recheck(win, sig["registered"], lambda _m: None)
    fz = sig["registered"]["windows"]["W1"]["frozen_v6"]
    assert seen["q95_1000[W1][mom1]"] == fz["q95_1000"]["mom1"] and "q95[W1][mom1]" not in seen


def _synthetic_frozen(rng):
    frozen, draws = {}, {}
    for wn, scale in (("W1", 1.0), ("W2", 0.9)):
        frozen[wn] = {k: {} for k in ("se_mean", "e_se_rule", "null_mean", "q95")}
        draws[wn] = {}
        for i, v in enumerate(C.VARIANTS):
            mu = (0.0011, 0.0013, 0.0018, -0.0008)[i] * scale
            s = (0.0070, 0.0077, 0.0094, 0.0071)[i] * scale
            d = rng.normal(mu, s, 20_000)
            draws[wn][v] = d
            frozen[wn]["se_mean"][v], frozen[wn]["e_se_rule"][v] = s, s * 1.03
            frozen[wn]["null_mean"][v], frozen[wn]["q95"][v] = mu, float(np.quantile(d, 0.95))
    return frozen, draws


def test_dec101_e5_power_line_matches_the_hand_calculation():
    frozen, draws = _synthetic_frozen(np.random.default_rng(11))
    m_p = {"mom1": 0.0021, "mom2": 0.0032, "mom4": 0.0043, "rev_gap": -0.0025}
    pl = powerline.build_power_line(frozen, m_p, draws)
    z, zp = C.Z_KRIT, C.Z_POWER
    assert zp == pp.Z_POWER and abs(zp - 0.8416) > 1e-6 and pl["z_power"] == pp.Z_POWER           # the exact value, never the rounded 0.8416
    for v in C.VARIANTS:
        x = pl["variants"][v]
        per = {}
        for wn in ("W1", "W2"):
            se, sd, nm, q = (frozen[wn][k][v] for k in ("e_se_rule", "se_mean", "null_mean", "q95"))
            b, c = z * se + zp * sd + max(0.0, nm), q + zp * sd
            assert x["windows"][wn]["mde80_1b"] == pytest.approx(b, abs=1e-15) and x["windows"][wn]["mde80_1c"] == pytest.approx(c, abs=1e-15)
            assert x["windows"][wn]["mde80_w"] == max(b, c)
            per[wn] = (b, c, z * se + zp * sd, nm, se, sd, q)
        assert x["mde80_star"] == max(max(p[0], p[1]) for p in per.values())
        m_star = max(0.0, m_p[v], per["W1"][3], per["W2"][3])
        u = max(p[2] for p in per.values())
        assert x["m_star"] == m_star and x["mde80_star_u"] == pytest.approx(u)
        assert x["handover_threshold_u"] == pytest.approx(u + m_star)
        assert x["handover_threshold_on_point"] == pytest.approx(max(u + m_star, max(p[1] for p in per.values())))   # U-3
        margin = (u + m_star) - max(p[1] for p in per.values())
        assert x["rule_u_covers_1c"]["margin"] == pytest.approx(margin) and x["rule_u_covers_1c"]["covers"] is (margin >= 0.0)
        assert x["margin_against_gate_mde80_star"] == pytest.approx(x["handover_threshold_on_point"] - x["mde80_star"])
        assert "Regel U deckt (1c)" in x["rule_u_covers_1c"]["line"] and ("ja" if margin >= 0 else "nein") in x["rule_u_covers_1c"]["line"]
        for m in C.POWER_M_GRID:
            bound = 0.10 / (m * sum(1.0 / i for i in range(1, m + 1)))
            z_eff = max(z, _N.inv_cdf(1.0 - bound))
            joint = 1.0
            for wn in ("W1", "W2"):
                b, c, _u, nm, se, sd, q = per[wn]
                thr = max(z_eff * se + max(0.0, nm), float(np.quantile(draws[wn][v], 1.0 - bound)), q)
                joint *= _N.cdf((u + m_star - thr) / sd)
            assert x["end_power_after_f_week_replicates"][str(m)]["joint"] == pytest.approx(joint, abs=1e-12)
            assert x["end_power_after_f_week_replicates"][str(m)]["z_eff"] == pytest.approx(z_eff)
    assert pl["m_grid"] == [1, 2, 3, 4, 11] and "report-only" in pl["label"]
    # more tested entries can only lower the end power
    for v in C.VARIANTS:
        j = [pl["variants"][v]["end_power_after_f_week_replicates"][str(m)]["joint"] for m in (1, 2, 3, 4, 11)]
        assert all(a >= b - 1e-12 for a, b in zip(j, j[1:]))


def test_dec101_e5_rule_u_covers_1c_flag_turns_false_when_the_null_quantile_dominates():
    frozen, draws = _synthetic_frozen(np.random.default_rng(12))
    m_p = {v: 0.0 for v in C.VARIANTS}
    ok = powerline.build_power_line(frozen, m_p, draws)["variants"]["mom1"]["rule_u_covers_1c"]
    bad_frozen = copy.deepcopy(frozen)
    bad_frozen["W1"]["q95"]["mom1"] += 0.02                                                      # a wide null: (1c) dominates the hand-over threshold
    bad = powerline.build_power_line(bad_frozen, m_p, draws)["variants"]["mom1"]["rule_u_covers_1c"]
    assert bad["covers"] is False and bad["margin"] < 0.0 and "nein" in bad["line"] and bad["margin"] < ok["margin"]


def test_dec101_e5_end_power_replicates_vs_hand_calculation_vs_monte_carlo_and_vs_the_normal_approximation():
    rng = np.random.default_rng(5)
    win = {}
    for wn, (mu, s, se_t, sd_t) in {"W1": (0.0011, 0.0070, 0.0072, 0.0070), "W2": (0.0012, 0.0064, 0.0064, 0.0064)}.items():
        d = rng.normal(mu, s, 40_000)
        win[wn] = {"se_t": se_t, "sd_t": sd_t, "null_mean": mu, "q95": float(np.quantile(d, 0.95)), "draws": d}
    pi = 0.0205
    for m in (1, 2, 4, 11):
        ep = est.end_power_replicates(pi, m, win)
        bound = 0.10 / (m * est.harmonic_number(m))
        assert ep["by_threshold_p"] == pytest.approx(bound) and ep["z_eff"] == pytest.approx(max(C.Z_KRIT, _N.inv_cdf(1 - bound)))
        joint_hand, joint_mc = 1.0, 1.0
        for wn, w in win.items():
            thr = max(ep["z_eff"] * w["se_t"] + max(0.0, w["null_mean"]), float(np.quantile(w["draws"], 1 - bound)), w["q95"])
            assert ep["window_detail"][wn]["threshold"] == pytest.approx(thr, abs=1e-15)
            joint_hand *= _N.cdf((pi - thr) / w["sd_t"])
            y = np.random.default_rng(100 + m).normal(pi, w["sd_t"], 400_000)
            joint_mc *= float((y >= thr).mean())
        assert ep["joint"] == pytest.approx(joint_hand, abs=1e-12)
        assert ep["joint"] == pytest.approx(joint_mc, abs=0.006)                                  # Monte Carlo, tolerance
        # normal replicates and SE = SD: the replicate version approximates the normal approximation of the old end_power
        na = est.end_power(pi, m, {wn: {k: w[k] for k in ("se_t", "sd_t", "null_mean")} for wn, w in win.items()})
        assert na["method"].startswith("Normalnaeherung") and ep["method"].startswith("replicate")
        assert ep["joint"] == pytest.approx(na["joint"], abs=0.03)
    # (1c) binds at m = 1 (bound 0.10 > 0.05): the q95 term lowers the power below the old formula's
    ep1 = est.end_power_replicates(pi, 1, win)
    assert all(d["threshold"] >= d["q95"] - 1e-15 for d in ep1["window_detail"].values())
    with pytest.raises(ValueError, match="no finite replicate"):
        est.end_power_replicates(pi, 2, {"W1": {**win["W1"], "draws": np.full(4, np.nan)}})


def test_dec101_e5_vorlauf_report_carries_the_power_line(sig, shrunk):
    pl = sig["report"]["power_line"]
    reg = sig["registered"]
    assert set(pl["variants"]) == set(C.VARIANTS) and pl["m_grid"] == [1, 2, 3, 4, 11] and pl["z_power"] == C.Z_POWER
    for v in C.VARIANTS:
        x = pl["variants"][v]
        for wn in ("W1", "W2"):
            fz = reg["windows"][wn]["frozen_v6"]
            assert x["windows"][wn]["mde80_1c"] == pytest.approx(fz["q95"][v] + C.Z_POWER * fz["se_mean"][v], abs=1e-15)
            assert x["windows"][wn]["mde80_1b"] == pytest.approx(C.Z_KRIT * fz["e_se_rule"][v] + C.Z_POWER * fz["se_mean"][v] + max(0.0, fz["null_mean"][v]), abs=1e-15)
        assert x["m_star"] == max(0.0, reg["pilot_window"]["frozen_v6"]["m_P"][v], reg["windows"]["W1"]["frozen_v6"]["null_mean"][v],
                                  reg["windows"]["W2"]["frozen_v6"]["null_mean"][v])
        assert x["handover_threshold_on_point"] == pytest.approx(max(x["mde80_star_u"] + x["m_star"], max(x["windows"][wn]["mde80_1c"] for wn in ("W1", "W2"))))
        assert set(x["end_power_after_f_week_replicates"]) == {"1", "2", "3", "4", "11"}
    assert "power_line" not in reg                                                                  # report-only: not a registered field


# ============================================================================
# E6: mu_sel placeholder and the PP3 dry run
# ============================================================================

def test_dec101_e6_mu_sel_at_the_bracket_edge_is_no_solution():
    se, c = 0.00709, 0.0206171
    for dx in (1e-4, 1e-6, 1e-9):                                                    # barely above the threshold: the root is far below the bracket
        d = est.mu_sel_detail(c + dx, se, c)
        assert d["mu_sel"] is None and d["solved"] is False and d["note"] == "keine Loesung (Platzhalter, report-only)"
        assert d["bracket_lo"] == pytest.approx(c + dx - 40.0 * se) and est.mu_sel(c + dx, se, c) is None
    ok = est.mu_sel_detail(c + 0.1 * se, se, c)
    assert ok["solved"] is True and ok["note"] is None and ok["mu_sel"] == est.mu_sel(c + 0.1 * se, se, c) and ok["mu_sel"] > ok["bracket_lo"]
    nh = est.mu_sel_detail(c - 0.1 * se, se, c)                                      # not handed over: not applicable, not "unsolved"
    assert nh["mu_sel"] is None and nh["solved"] is None
    # the boundary sits where the root crosses the bracket: x_P - c ~ ln 2 / 40 SE
    assert est.mu_sel(c + 0.015 * se, se, c) is None and est.mu_sel(c + 0.05 * se, se, c) is not None


def test_dec101_e6_handover_and_pilot_markdown_mark_the_placeholder(sig, shrunk):
    consts = handover.handover_constants(sig["registered"], "mom1")
    probe = handover.evaluate_handover({"x_p": 0.5, "se_p": 0.01, "f2_real": 0.0, "c_real": 1.0}, consts)
    c_v = probe["threshold_on_point"]
    edge = handover.evaluate_handover({"x_p": c_v + 1e-7, "se_p": 0.01, "f2_real": 0.0, "c_real": 1.0}, consts)
    assert edge["handed_over"] and edge["mu_sel"] is None and edge["mu_sel_solved"] is False and edge["power_at_mu_sel"] is None
    assert edge["mu_sel_note"] == "keine Loesung (Platzhalter, report-only)"
    assert probe["mu_sel_solved"] is True and probe["mu_sel_note"] is None
    rep = copy.deepcopy({k: v for k, v in sig["pilot_report"].items() if k != "_series"})
    v = rep["handed"][0]
    rep["variants"][v]["handover"] = {**rep["variants"][v]["handover"], "mu_sel": None, "mu_sel_solved": False,
                                      "mu_sel_note": "keine Loesung (Platzhalter, report-only)", "power_at_mu_sel": None}
    assert "keine Loesung (Platzhalter, report-only)" in pilot_mod.render_pilot_markdown(rep)
    assert "keine Loesung" not in pilot_mod.render_pilot_markdown({k: v_ for k, v_ in sig["pilot_report"].items() if k != "_series"})


def _forbid_ic(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("an IC function was called in the PP3 dry run")
    for name in ("weekly_ic_series", "apply_beta_control", "fm_neutralize_outcome"):
        monkeypatch.setattr(ic, name, boom)
    from bybit_edge.research.h32_fm8 import fm8, labels
    monkeypatch.setattr(fm8, "window_ic", boom)
    monkeypatch.setattr(fm8, "fm8_weekly_ic", boom)
    monkeypatch.setattr(labels, "liquidity_means", boom)


def test_dec101_e6_pp3_dry_run_checks_the_pins_without_any_ic(sig, shrunk, monkeypatch):
    _forbid_ic(monkeypatch)
    rep = pp3.run_pp3_dry_run(sig["panel"], sig["registered"], FP, registered_sha256=REGISTERED_SHA, log=lambda _m: None)
    reg = sig["registered"]
    assert rep["ok"] is True and rep["schema"] == C.PP3_SCHEMA and set(rep["windows"]) == {"P", "W1", "W2"}
    assert rep["windows"]["P"]["pinned_k_fm8_series_sha256"] == reg["pilot_window"]["frozen_v6"]["k_fm8_series_sha256"]
    for wn in ("W1", "W2"):
        assert rep["windows"][wn]["pinned_k_fm8_series_sha256"] == reg["windows"][wn]["frozen_v6"]["k_fm8_series_sha256"]
    assert all(r["k_fm8_series_ok"] and r["window_pins_ok"] and r["ok"] and r["error"] is None for r in rep["windows"].values())
    assert rep["cuts"]["pilot"]["cut_date"] == C.CUT_PILOT and rep["cuts"]["pilot"]["max_date"] <= C.CUT_PILOT
    assert rep["cuts"]["test"]["cut_date"] == C.CUT_TEST and rep["cuts"]["test"]["max_date"] == C.CUT_TEST
    assert rep["universe"]["rule"] == C.UNIVERSE_RULE and rep["runner"] == F.RUNNER
    assert {"ic", "raw_ic", "lag_profile", "beta_calibration_ic"} <= set(rep["not_computed"])
    # the pilot K_fm8 series equals the one of the Vorlauf (the whole point of the dry run)
    assert rep["windows"]["P"]["k_fm8_series_sha256"] == sig["report"]["windows"]["P"]["k_fm8_series_sha256"]


def test_dec101_e6_pp3_dry_run_reports_every_deviating_pin(sig, shrunk):
    for path, wn in ((("pilot_window", "frozen_v6", "k_fm8_series_sha256"), "P"), (("windows", "W1", "frozen_v6", "k_fm8_series_sha256"), "W1"),
                     (("windows", "W2", "frozen_v6", "k_fm8_series_sha256"), "W2")):
        reg = copy.deepcopy(sig["registered"])
        cur = reg
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = "11" * 32
        rep = pp3.run_pp3_dry_run(sig["panel"], reg, FP, registered_sha256=REGISTERED_SHA)
        assert rep["ok"] is False and rep["windows"][wn]["ok"] is False and rep["windows"][wn]["k_fm8_series_ok"] is False
        assert rep["windows"][wn]["window_pins_ok"] is False and "PinError" in rep["windows"][wn]["error"]
        assert all(r["ok"] for k, r in rep["windows"].items() if k != wn)
    with pytest.raises(DataFingerprintError):
        pp3.run_pp3_dry_run(sig["panel"], sig["registered"], {**FP, "delisted_tree_sha256": "00" * 32})
    bad = copy.deepcopy(sig["registered"])
    bad["pilot_window"]["w_pilot"] = 115
    with pytest.raises(PinError):
        pp3.run_pp3_dry_run(sig["panel"], bad, FP)


def test_dec101_e6_pp3_module_imports_no_ic_function_and_writes_a_small_json(sig, shrunk, tmp_path):
    tree = ast.parse(Path(pp3.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported |= {a.name for a in node.names} | ({node.module} if node.module else set())
        elif isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
    assert not ({"ic", "fm8", "labels", "permutation", "nullsim", "calibration", "weekly_ic_series", "apply_beta_control"} & imported)
    assert not any(m and m.endswith(("wp13_xsec.ic", "h32_fm8.fm8")) for m in imported)
    rep = pp3.run_pp3_dry_run(F.add_twins(sig["panel"]) if False else sig["panel"], sig["registered"], FP, registered_sha256=REGISTERED_SHA)
    out = pp3.write_pp3_artifact(tmp_path / "pp3", rep)
    files = sorted(p.name for p in (tmp_path / "pp3").iterdir())
    assert files == [C.PP3_FILE] and not any(n.startswith("h32_pilot") for n in files)           # never counts as a pilot result (E3)
    data = json.loads((tmp_path / "pp3" / C.PP3_FILE).read_text(encoding="utf-8"))
    assert data["ok"] is True and "excluded_symbols" not in data["universe"] and data["result_sha256"] == out["result_sha256"]
    assert (tmp_path / "pp3" / C.PP3_FILE).stat().st_size < 20_000
    with pytest.raises(ValueError, match="data/harvest"):
        pp3.write_pp3_artifact("data/harvest/pp3_never", rep)
