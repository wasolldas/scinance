"""DEC-101 Teil 2 tests (H-32 registration, Nachpruefung N-1..N-5): positive control in production configuration with the scaled null
(N-1), the injection target F (N-2), rule U-4 with ``k_pred`` (N-3), the pilot attempt marker (N-4; the CLI end-to-end of the marker is in
``test_h32_cli.py``) and the documentation fields / the forbidden unscaled gate fallback (N-5).

Pure parts are tested with hand calculations (T4 on conserved numbers); the mode-level parts run on the fixture panels of
``tests/unit/h32_fixtures.py`` (nothing real is read).  The expected PASS share of the control (N-2) is tested in a world that is
calibrated EXACTLY: the frozen constants of the test world are measured on its own negative control (300 seeds, other than the judgement
seeds), so the expected share is known from the target construction and not from a fitted tolerance."""
from __future__ import annotations

import copy
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

from bybit_edge.research import power_p1 as pp
from bybit_edge.research.h32_fm8 import (checks, estimators as est, gate, handover, pilot as pilot_mod, positive_control as pc,
                                         powerline, schema, vorlauf)
from bybit_edge.research.h32_fm8 import constants as C
from bybit_edge.research.h32_fm8.errors import GateError, PilotLockError, PinError, PositiveControlAbort, SchemaError
from bybit_edge.research.wp13_xsec import prelaunch

from tests.unit import h32_fixtures as F
from tests.unit.h32_fixtures import REGISTERED_SHA, shrunk  # noqa: F401  (pytest fixture)

FP = dict(F.FAKE_FINGERPRINTS)
_N = NormalDist()
Z, ZP = C.Z_KRIT, C.Z_POWER


@pytest.fixture(scope="module")
def sig():
    return F.get_bundle("signal")


@pytest.fixture(scope="module")
def nul():
    return F.get_bundle("null")


# ============================================================================
# N-3: rule U-4 (handover.py) -- the (1c) term with k_pred
# ============================================================================

def _consts(m_p=0.0005, null_mean=(0.0009, 0.0005), e_se=(0.0079, 0.0064), se_mean=(0.0079, 0.0064), v_fm8=(0.0025, 0.0020),
            q95=(0.0110, 0.0095), sd_week=(10.0, 10.0)):
    """Rule U constants of one variant; the default ``sd_week`` is huge, i.e. ``k_pred = 1`` (the U-3 case)."""
    wins = {wn: {"v_fm8": v_fm8[i], "e_se_rule": e_se[i], "se_mean": se_mean[i], "null_mean": null_mean[i], "w_judged": (52, 50)[i],
                 "q95": q95[i], "sd_week": sd_week[i]}
            for i, wn in enumerate(("W1", "W2"))}
    return {"windows": wins, "m_p": m_p, "z_krit": Z, "z_power": ZP, "t_min": 2.0}


def _inputs(x_p=0.04, se_p=0.0071, f2=0.00026, c=1.08):
    return {"x_p": x_p, "se_p": se_p, "f2_real": f2, "c_real": c}


def _u3_threshold(ho):
    """The rule U-3 value from the pilot output alone: ``max(m* + MDE80*_U, max_W(q95_W + z_80 SD_T,W))``."""
    return max(ho["threshold_u"], max(ho["per_window"][wn]["q95"] + ZP * ho["per_window"][wn]["sd_t"] for wn in ("W1", "W2")))


def test_n3_u4_equals_u3_bit_for_bit_at_k_pred_one_and_a_nonnegative_null_mean():
    """DEC-101 Teil 2 (N-3): at ``k_pred = 1`` and ``m >= 0`` no number of rule U changes against U-3 (exact equality, not approx)."""
    for q95 in ((0.0110, 0.0095), (0.0300, 0.0280), (0.0204, 0.0191)):               # U binds / (1c) binds / in between
        for f2 in (0.0, 0.00026, 0.0009):
            consts = _consts(q95=q95)
            ho = handover.evaluate_handover(_inputs(f2=f2), consts)
            assert ho["k_pred"] == {"W1": 1.0, "W2": 1.0} and ho["rule_version"] == "U-4"
            for wn in ("W1", "W2"):
                assert ho["threshold_1c_components"][wn] == q95[0 if wn == "W1" else 1] + ZP * ho["per_window"][wn]["sd_t"]       # == the U-3 term
            assert ho["threshold_on_point"] == _u3_threshold(ho)
            assert ho["threshold_binding"] == ("1c" if ho["threshold_1c"] > ho["threshold_u"] else "U")
    # the estimator identity behind it
    assert est.q95_effective(0.0012, 1.0, 0.0198) == 0.0198 and est.q95_effective(0.0, 1.0, 0.0198) == 0.0198
    d = np.random.default_rng(4).normal(0.001, 0.007, 300)
    assert np.array_equal(est.scaled_replicates(d, 0.0012, 1.0), d) and np.array_equal(est.scaled_replicates(d, 0.0, 1.0), d)


def test_n3_negative_null_mean_term_is_q95_plus_abs_m_and_scales_with_k_pred():
    """rev_gap-like cell: ``max(0, m) = 0``, so the (1c) term is ``k_pred (q95 + |m|) + z_80 SD_T`` -- no credit for a negative null mean."""
    q95, nm = (0.0140, 0.0132), (-0.0012, -0.0008)
    ho1 = handover.evaluate_handover(_inputs(), _consts(null_mean=nm, q95=q95))                       # k_pred = 1
    for i, wn in enumerate(("W1", "W2")):
        assert ho1["threshold_1c_components"][wn] == pytest.approx(q95[i] + abs(nm[i]) + ZP * ho1["per_window"][wn]["sd_t"], abs=1e-15)
        assert ho1["threshold_1c_components"][wn] > q95[i] + ZP * ho1["per_window"][wn]["sd_t"]      # strictly above the U-3 value
    sdw = (0.04, 0.045)                                                                                # k_pred > 1
    ho = handover.evaluate_handover(_inputs(), _consts(null_mean=nm, q95=q95, sd_week=sdw))
    for i, wn in enumerate(("W1", "W2")):
        k = max(1.0, math.sqrt((0.0025, 0.0020)[i] + 0.00026) / sdw[i])
        assert k > 1.0 and ho["k_pred"][wn] == pytest.approx(k)
        assert ho["threshold_1c_components"][wn] == pytest.approx(k * (q95[i] + abs(nm[i])) + ZP * ho["per_window"][wn]["sd_t"], abs=1e-15)


def test_n3_t4_hand_calculation_of_the_threshold_on_one_conserved_payload():
    """T4: rule U-4 on fixed numbers, every term written out; the output is pure."""
    consts = _consts(m_p=0.0007, null_mean=(0.0015, 0.0010), e_se=(0.0100, 0.0090), se_mean=(0.0105, 0.0095), v_fm8=(0.0066, 0.0065),
                     q95=(0.0200, 0.0185), sd_week=(0.0760, 0.0750))
    inp = _inputs(x_p=0.06, se_p=0.012, f2=0.0005, c=1.2)
    ho = handover.evaluate_handover(inp, consts)
    assert ho == handover.evaluate_handover(copy.deepcopy(inp), copy.deepcopy(consts))
    exp_1c, exp_1b = {}, {}
    for i, wn in enumerate(("W1", "W2")):
        v, w_j = (0.0066, 0.0065)[i], (52, 50)[i]
        se_pilot = math.sqrt(1.2) * math.sqrt(v + 0.0005) / math.sqrt(w_j)
        se_t, sd_t = max((0.0100, 0.0090)[i], se_pilot), max((0.0105, 0.0095)[i], se_pilot)
        k = max(1.0, math.sqrt(v + 0.0005) / (0.0760, 0.0750)[i])
        m, q = (0.0015, 0.0010)[i], (0.0200, 0.0185)[i]
        assert ho["per_window"][wn]["se_t"] == pytest.approx(se_t) and ho["per_window"][wn]["sd_t"] == pytest.approx(sd_t)
        assert ho["k_pred"][wn] == pytest.approx(k) and k > 1.0
        exp_1c[wn] = max(0.0, m) + k * (q - m) + ZP * sd_t
        exp_1b[wn] = Z * se_t + ZP * sd_t
        assert ho["threshold_1c_components"][wn] == pytest.approx(exp_1c[wn], abs=1e-15)
    m_star = max(0.0, 0.0007, 0.0015, 0.0010)
    assert ho["m_star"] == m_star and ho["mde80_star"] == pytest.approx(max(exp_1b.values()))
    assert ho["threshold_u"] == pytest.approx(m_star + max(exp_1b.values()))
    assert ho["threshold_1c"] == pytest.approx(max(exp_1c.values()))
    assert ho["threshold_on_point"] == pytest.approx(max(m_star + max(exp_1b.values()), max(exp_1c.values())))
    # the boundary of (ii): just above hands over (when (i) and (iii) hold), just below does not
    thr = ho["threshold_on_point"]
    assert handover.evaluate_handover(_inputs(x_p=thr + 1e-9, se_p=0.012, f2=0.0005, c=1.2), consts)["conditions"]["ii"] is True
    assert handover.evaluate_handover(_inputs(x_p=thr - 1e-9, se_p=0.012, f2=0.0005, c=1.2), consts)["conditions"]["ii"] is False


def test_n3_threshold_rises_with_f2_real_and_is_never_below_u3():
    """Monotone in F2_real (SE_T, SD_T and k_pred only grow) and, because ``k_pred >= 1`` and ``q95 >= m``, never below the U-3 value."""
    consts = _consts(sd_week=(0.05, 0.05), q95=(0.0180, 0.0170))
    f2s = [0.0, 0.0001, 0.0003, 0.0006, 0.0012, 0.0030, 0.0080]
    hos = [handover.evaluate_handover(_inputs(f2=f2), consts) for f2 in f2s]
    thr = [h["threshold_on_point"] for h in hos]
    assert all(a <= b for a, b in zip(thr, thr[1:])) and thr[-1] > thr[0]
    ks = [h["k_pred"]["W1"] for h in hos]
    assert ks[0] >= 1.0 and all(a <= b for a, b in zip(ks, ks[1:])) and ks[-1] > 1.0
    for h in hos:
        assert h["threshold_on_point"] >= _u3_threshold(h) - 1e-15
        assert h["threshold_1c"] >= max(h["per_window"][wn]["q95"] + ZP * h["per_window"][wn]["sd_t"] for wn in ("W1", "W2")) - 1e-15
    # a pilot point that cleared U-3 but not U-4 exists once k_pred > 1 and (1c) binds
    h = hos[-1]
    assert h["threshold_binding"] == "1c" and h["threshold_on_point"] > _u3_threshold(h) + 1e-4
    k_big = handover.evaluate_handover(_inputs(f2=0.0030), _consts(sd_week=(0.05, 0.05), q95=(0.0300, 0.0280)))
    assert k_big["threshold_binding"] == "1c" and k_big["threshold_on_point"] > _u3_threshold(k_big) + 1e-4
    x_between = 0.5 * (_u3_threshold(k_big) + k_big["threshold_on_point"])
    between = handover.evaluate_handover(_inputs(x_p=x_between, f2=0.0030), _consts(sd_week=(0.05, 0.05), q95=(0.0300, 0.0280)))
    assert x_between >= _u3_threshold(between) and between["conditions"]["ii"] is False and not between["handed_over"]


@pytest.mark.parametrize("k_scale", [1.0, 1.15, 1.4])
def test_n3_the_threshold_covers_the_scaled_gate_condition_1c_at_power_80(k_scale):
    """At the hand-over threshold the window power of the scaled (1c) condition is >= 0.80 in BOTH windows: with
    ``Y ~ N(x_P, SD_T)``, ``P(Y >= q95_eff(k_pred)) = Phi((x_P - q95_eff) / SD_T) >= Phi(z_80) = 0.80``.  U-3 failed this for
    ``k_pred > 1`` (review N-3: 0.797 .. 0.790)."""
    sdw = (0.0525 / k_scale, 0.0475 / k_scale)
    consts = _consts(q95=(0.0300, 0.0280), sd_week=sdw)
    ho = handover.evaluate_handover(_inputs(), consts)
    assert ho["threshold_binding"] == "1c"
    for wn in ("W1", "W2"):
        q_eff = est.q95_effective(ho["per_window"][wn]["null_mean"], ho["k_pred"][wn], ho["per_window"][wn]["q95"])
        power = pp.condition_power(ho["threshold_on_point"], q_eff, ho["per_window"][wn]["sd_t"])
        assert power >= 0.80 - 1e-12
    if k_scale > 1.0:
        u3 = _u3_threshold(ho)
        wn = "W1"
        q_eff = est.q95_effective(ho["per_window"][wn]["null_mean"], ho["k_pred"][wn], ho["per_window"][wn]["q95"])
        assert pp.condition_power(u3, q_eff, ho["per_window"][wn]["sd_t"]) < 0.80                  # the U-3 threshold would fall short


def test_n3_nonfinite_inputs_fail_closed():
    ho = handover.evaluate_handover(_inputs(x_p=0.5), _consts(sd_week=(0.0, 10.0)))             # sd_week 0: k_pred is NaN
    assert math.isnan(ho["k_pred"]["W1"]) and math.isnan(ho["threshold_on_point"]) and ho["threshold_binding"] == "invalid"
    assert ho["conditions"]["ii"] is False and ho["handed_over"] is False and ho["status"] == C.PILOT_GL012
    assert math.isnan(est.k_pred(0.0066, float("nan"), 0.07)) and math.isnan(est.k_pred(-1.0, 0.0, 0.07))
    assert est.k_pred(0.0066, 0.0, 10.0) == 1.0 and est.k_pred(0.0066, 0.0005, 0.05) == pytest.approx(math.sqrt(0.0071) / 0.05)


def test_n3_yaml_texts_are_the_code_constants_and_are_pinned(nul, shrunk):
    reg = nul["registered"]
    hr = reg["handover_rule"]
    assert hr["version"] == C.HANDOVER_VERSION == "U-4" and hr["k_pred"] == C.HANDOVER_K_PRED
    assert next(c for c in hr["conditions"] if c["id"] == "ii")["text"] == C.HANDOVER_COND_II
    assert "k_pred,W" in C.HANDOVER_COND_II and "max(0, m_W)" in C.HANDOVER_COND_II and hr["mu_sel"].endswith(C.HANDOVER_C_V)
    for mutate, exc in (
            (lambda r: next(c for c in r["handover_rule"]["conditions"] if c["id"] == "ii").__setitem__("text", "x_P >= max(m* + MDE80*, max_W(q95_W,v + z_80 * SD_T,W))"), PinError),
            (lambda r: r["handover_rule"].__setitem__("version", "U-3"), PinError),
            (lambda r: r["handover_rule"].__setitem__("k_pred", "k_pred = 1"), PinError),
            (lambda r: r["handover_rule"].pop("k_pred"), PinError),
            (lambda r: r["handover_rule"].__setitem__("conditions", [c for c in r["handover_rule"]["conditions"] if c["id"] != "ii"]), PinError)):
        bad = copy.deepcopy(reg)
        mutate(bad)
        with pytest.raises(exc):
            schema.validate_registered(bad)


def test_n3_pilot_output_carries_k_pred_threshold_components_and_binding(sig, shrunk):
    pr = sig["pilot_report"]
    for v in C.VARIANTS:
        ho = pr["variants"][v]["handover"]
        assert set(ho["k_pred"]) == {"W1", "W2"} and set(ho["threshold_1c_components"]) == {"W1", "W2"} and ho["threshold_binding"] in ("U", "1c")
        assert ho["rule_version"] == "U-4" and pr["parameters"]["handover_version"] == "U-4"
        for wn in ("W1", "W2"):
            fz = sig["registered"]["windows"][wn]["frozen_v6"]
            k = max(1.0, math.sqrt(fz["v_fm8"] + ho["f2_real"]) / fz["sd_week"][v])
            assert ho["k_pred"][wn] == pytest.approx(k) and ho["per_window"][wn]["k_pred"] == ho["k_pred"][wn]
            assert ho["threshold_1c_components"][wn] == pytest.approx(
                est.q95_effective(fz["null_mean"][v], k, fz["q95"][v]) + ZP * ho["per_window"][wn]["sd_t"], abs=1e-15)
    md = pilot_mod.render_pilot_markdown({k: v for k, v in pr.items() if k != "_series"})
    assert "Uebergaberegel U-4" in md and C.HANDOVER_COND_II in md and md.isascii()


def test_n3_power_line_uses_k_pred_one_and_matches_u3_where_the_null_mean_is_nonnegative():
    rng = np.random.default_rng(5)
    frozen, draws = {}, {}
    for wn in ("W1", "W2"):
        frozen[wn] = {"se_mean": {v: 0.0105 for v in C.VARIANTS}, "e_se_rule": {v: 0.0100 for v in C.VARIANTS},
                      "null_mean": {"mom1": 0.0012, "mom2": 0.0016, "mom4": 0.0020, "rev_gap": -0.0012},
                      "q95": {"mom1": 0.0190, "mom2": 0.0196, "mom4": 0.0210, "rev_gap": 0.0150}}
        draws[wn] = {v: rng.normal(frozen[wn]["null_mean"][v], 0.0105, 400) for v in C.VARIANTS}
    pl = powerline.build_power_line(frozen, {v: 0.0 for v in C.VARIANTS}, draws)["variants"]
    for v in C.VARIANTS:
        for wn in ("W1", "W2"):
            q, nm = frozen[wn]["q95"][v], frozen[wn]["null_mean"][v]
            exp = (q if nm >= 0 else q - nm) + ZP * 0.0105
            assert pl[v]["windows"][wn]["mde80_1c"] == exp or pl[v]["windows"][wn]["mde80_1c"] == pytest.approx(exp, abs=1e-15)
            if nm >= 0:
                assert pl[v]["windows"][wn]["mde80_1c"] == q + ZP * 0.0105                          # the U-3 number, bit for bit
    assert "U-4" in pl["rev_gap"]["rule_u_covers_1c"]["line"]


# ============================================================================
# N-1: the positive control in production configuration (scaled null)
# ============================================================================

@pytest.fixture(scope="module")
def pc_report(sig):
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        shape, symbols, _ = pc.build_shape(sig["panel"], sig["registered"]["seal"]["panel_cut_test"])
        return pc.run_positive_control(shape, symbols, sig["registered"], sig["pilot"], observed_fingerprints=FP, registered_sha256=REGISTERED_SHA,
                                       pilot_sha256=sig["pilot_sha"])


def _inflated_pilot(sig, f2):
    """The pilot with an inflated F2_real (and the rule-U SE_T / SD_T re-derived for it): the control world SD rises above ``sd_week``."""
    pil = copy.deepcopy(sig["pilot"])
    for v in pil["handed"]:
        ho = pil["variants"][v]["handover"]
        ho["f2_real"] = f2
        ho["per_window"] = handover.se_t_sd_t(handover.handover_constants(sig["registered"], v), {"c_real": ho["c_real"], "f2_real": f2})
    return pil


@pytest.fixture(scope="module")
def pc_inflated(sig):
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        shape, symbols, _ = pc.build_shape(sig["panel"], sig["registered"]["seal"]["panel_cut_test"])
        return pc.run_positive_control(shape, symbols, sig["registered"], _inflated_pilot(sig, 0.0030), observed_fingerprints=FP,
                                       registered_sha256=REGISTERED_SHA, pilot_sha256=sig["pilot_sha"])


def test_n1_the_report_names_the_scaled_null_and_carries_k_per_seed(pc_report, sig, shrunk):
    r = pc_report
    assert r["null_scaling"] == {"enabled": True, "rule": C.PC_NULL_SCALING_RULE, "ref": "DEC-101 Teil 2 (N-1)"}
    assert C.PC_NULL_SCALING_RULE.startswith("wie Testlauf (DEC-101 E2)") and "sd_week" in C.PC_NULL_SCALING_RULE
    n = len(C.PC_SEEDS_JUDGE)
    for v, x in r["variants"].items():
        for cond in ("neg", "pos"):
            for wn in ("W1", "W2"):
                ks = x["judgement"]["k_scaling"][cond][wn]
                assert ks["n"] == n and ks["n_finite"] == n and ks["min"] >= 1.0                         # k = max(1, ...): never below 1
                assert ks["min"] <= ks["q05"] <= ks["q25"] <= ks["median"] <= ks["q75"] <= ks["q95"] <= ks["max"]
                assert 0.0 <= ks["share_gt_1"] <= 1.0
    # the mom1 world is calibrated to sqrt(v_fm8 + F2_real) > sd_week (the fixture's null SD is below sqrt(v_fm8)): k is above 1
    m1 = r["variants"]["mom1"]["judgement"]["k_scaling"]
    assert m1["neg"]["W1"]["median"] > 1.03 and m1["pos"]["W1"]["median"] > 1.03 and m1["neg"]["W1"]["share_gt_1"] > 0.8
    md = pc.render_pc_markdown(r)
    assert "Skalierte Null je Seed" in md and "unskaliert" in md and md.isascii()


def test_n1_t4_payload_arithmetic_of_the_gate_chain(pc_report, sig, shrunk):
    """T4: the stored payload of the first judgement seed reproduces ``k``, ``q95_eff`` and the window verdict by hand, and the pure gate
    function gives the identical conditions from the payload alone -- in the negative AND the positive control."""
    reg = sig["registered"]
    for v, x in pc_report["variants"].items():
        for cond in ("neg", "pos"):
            for wn in ("W1", "W2"):
                ex = x["judgement"]["payload_example"][cond][wn]
                p, c = ex["payload"], ex["conditions"]
                ns = p["null_scaling"]
                fz = reg["windows"][wn]["frozen_v6"]
                assert ns["sd_week"] == fz["sd_week"][v] and ns["m"] == fz["null_mean"][v] and ns["q95_frozen"] == fz["q95"][v] == p["q95"]
                k = max(1.0, ns["sd_real"] / ns["sd_week"])
                q_eff = max(0.0, ns["m"]) + k * (ns["q95_frozen"] - ns["m"])
                assert c["k"] == k and c["q95_effective"] == pytest.approx(q_eff, abs=1e-15)
                a, b, cc = p["y"] > 0.0, p["y"] >= Z * p["se_w"], p["y"] >= c["q95_effective"]
                assert (c["a_sign"], c["b_magnitude"], c["c_null_quantile"]) == (a, b, cc) and c["window_pass"] == (a and b and cc)
                assert c["threshold_t"] == pytest.approx(max(Z * p["se_w"], c["q95_effective"]))
                again = gate.window_conditions(copy.deepcopy(p), Z)
                assert {k_: again[k_] for k_ in c} == c


def test_n1_inflated_world_sd_gives_k_above_one_and_a_stricter_gate_than_without_scaling(pc_inflated, pc_report, sig, shrunk):
    """With an inflated F2_real the control world SD, hence k, rises: the scaled gate is stricter than the old unscaled chain (the share of
    the unscaled chain, reported for comparison only, is higher), and the scaled chain is more demanding than in the base fixture."""
    gap = []
    for v, x in pc_inflated["variants"].items():
        j = x["judgement"]
        assert x["f2_real"] == pytest.approx(0.0030)
        for wn in ("W1", "W2"):
            assert j["k_scaling"]["neg"][wn]["median"] > 1.2 and j["k_scaling"]["pos"][wn]["median"] > 1.2
            # scaled pass implies unscaled pass (q95_eff >= q95): the shares are ordered
            assert j["pass_share_by_window"][wn] <= j["pass_share_by_window_unscaled_report_only"][wn] + 1e-12
            assert j["false_pass_rate_by_window"][wn] <= j["false_pass_rate_by_window_unscaled_report_only"][wn] + 1e-12
            gap.append(j["pass_share_by_window_unscaled_report_only"][wn] - j["pass_share_by_window"][wn])
            gap.append(j["false_pass_rate_by_window_unscaled_report_only"][wn] - j["false_pass_rate_by_window"][wn])
        k_base = pc_report["variants"][v]["judgement"]["k_scaling"]["neg"]["W1"]["median"]
        assert j["k_scaling"]["neg"]["W1"]["median"] > k_base
    assert max(gap) > 0.0                                                                            # the quota FALLS with the scaling somewhere
    for v, x in pc_inflated["variants"].items():                                                     # the target F follows k_pred
        for wn, t in x["target_components"].items():
            assert t["k_pred"] > 1.2 and t["q95_eff_pred"] >= t["q95"]


def test_n1_scaled_pass_share_never_exceeds_the_unscaled_one_in_the_base_fixture(pc_report, shrunk):
    for x in pc_report["variants"].values():
        j = x["judgement"]
        for wn in ("W1", "W2"):
            assert j["pass_share_by_window"][wn] <= j["pass_share_by_window_unscaled_report_only"][wn] + 1e-12
            assert j["false_pass_rate_by_window"][wn] <= j["false_pass_rate_by_window_unscaled_report_only"][wn] + 1e-12


def test_n1_yaml_block_positive_control_null_scaling_is_mandatory_and_pinned(nul, shrunk):
    reg = nul["registered"]
    assert reg["positive_control"]["null_scaling"] == {"enabled": True, "rule": C.PC_NULL_SCALING_RULE, "ref": C.PC_NULL_SCALING_REF}
    schema.validate_registered(reg)
    for mutate, exc in (
            (lambda r: r["positive_control"].pop("null_scaling"), SchemaError),
            (lambda r: r["positive_control"]["null_scaling"].__setitem__("enabled", False), PinError),
            (lambda r: r["positive_control"]["null_scaling"].__setitem__("rule", "ohne Skalierung"), PinError),
            (lambda r: r["positive_control"]["null_scaling"].__setitem__("ref", "DEC-101 E2"), PinError)):
        bad = copy.deepcopy(reg)
        mutate(bad)
        with pytest.raises(exc):
            schema.validate_registered(bad)


# ============================================================================
# N-2: the injection target F
# ============================================================================

def test_n2_t4_hand_calculation_of_the_target_1c_binding_and_1b_binding_and_negative_m_df():
    # (1c) binds (mom4-like): k_pred 1.1
    t = pc.injection_target_components(se_t=0.0100, sd_t=0.0105, m_df=0.0019, m=0.0021, q95=0.0198, k_pred=1.1)
    q_eff = 0.0021 + 1.1 * (0.0198 - 0.0021)
    assert t["q95_eff_pred"] == pytest.approx(q_eff, abs=1e-15)
    assert t["term_1b"] == pytest.approx(Z * 0.0100 + ZP * 0.0105, abs=1e-15)                        # m_df >= 0: no correction
    assert t["term_1c"] == pytest.approx(q_eff - 0.0019 + ZP * 0.0105, abs=1e-15)
    assert t["target"] == t["term_1c"] > t["term_1b"] and t["binding_condition"] == "1c"
    # (1b) binds: a small q95
    t2 = pc.injection_target_components(se_t=0.0120, sd_t=0.0105, m_df=0.0012, m=0.0013, q95=0.0150, k_pred=1.0)
    assert t2["target"] == t2["term_1b"] == pytest.approx(Z * 0.0120 + ZP * 0.0105) and t2["binding_condition"] == "1b"
    assert t2["term_1c"] == pytest.approx(0.0150 - 0.0012 + ZP * 0.0105)                              # k_pred = 1, m >= 0: q95_eff = q95
    # rev_gap-like: m_df < 0 costs |m_df| in (1b); q95_eff = q95 + |m| (k_pred = 1), m = m_df here
    t3 = pc.injection_target_components(se_t=0.0100, sd_t=0.0100, m_df=-0.0012, m=-0.0012, q95=0.0140, k_pred=1.0)
    assert t3["term_1b"] == pytest.approx(Z * 0.0100 + ZP * 0.0100 + 0.0012, abs=1e-15)
    assert t3["q95_eff_pred"] == pytest.approx(0.0140 + 0.0012, abs=1e-15)
    assert t3["term_1c"] == pytest.approx(0.0140 + 0.0012 + 0.0012 + ZP * 0.0100, abs=1e-15)
    assert t3["target"] == max(t3["term_1b"], t3["term_1c"])
    # the literal ERSTFASSUNG 4 target z SE_T + z_80 SD_T lies below the F target for (1c)-binding cells (the review's finding)
    assert t["target"] > Z * 0.0100 + ZP * 0.0105 and t3["target"] > Z * 0.0100 + ZP * 0.0100
    # monotone in k_pred (q95 > m), loud on non-finite input
    ts = [pc.injection_target_components(se_t=0.0100, sd_t=0.0105, m_df=0.0019, m=0.0021, q95=0.0198, k_pred=k)["target"] for k in (1.0, 1.1, 1.3, 1.6)]
    assert ts == sorted(ts) and ts[-1] > ts[0]
    with pytest.raises(PositiveControlAbort, match="non-finite"):
        pc.injection_target_components(se_t=0.0100, sd_t=float("nan"), m_df=0.0019, m=0.0021, q95=0.0198, k_pred=1.0)


def test_n2_the_run_aims_at_the_argmax_window_target_and_reports_the_label(pc_report, sig, shrunk):
    reg, r = sig["registered"], pc_report
    assert r["inject_target_label"] == "Injektionsziel F: Korrektur nach DEC-94 (3) (Review B-4/A-4, Nachpruefung N-2), vor jeder Pilot-Zahl"
    assert r["inject_target"] == C.PC_INJECT_TARGET == reg["positive_control"]["inject_target"] and r["inject_target_ref"] == "DEC-101 Teil 2 (N-2)"
    assert reg["positive_control"]["inject_target_label"] == r["inject_target_label"]
    assert "argmax_W" in C.PC_INJECT_TARGET and "m_df,W" in C.PC_INJECT_TARGET and "k_pred,W" in C.PC_INJECT_TARGET
    for v, x in r["variants"].items():
        ho = sig["pilot"]["variants"][v]["handover"]
        per = {}
        for wn in ("W1", "W2"):
            fz = reg["windows"][wn]["frozen_v6"]
            k = max(1.0, math.sqrt(fz["v_fm8"] + ho["f2_real"]) / fz["sd_week"][v])
            m_df, m, q = fz["null_mean_driftfree"][v], fz["null_mean"][v], fz["q95"][v]
            sd_t, se_t = ho["per_window"][wn]["sd_t"], ho["per_window"][wn]["se_t"]
            per[wn] = max(Z * se_t + ZP * sd_t - min(0.0, m_df), max(0.0, m) + k * (q - m) - m_df + ZP * sd_t)
        bw = max(per, key=per.get)
        assert x["binding_window"] == bw and x["target_effect"] == pytest.approx(per[bw], abs=1e-15)
        assert x["injection"]["target_effect"] == pytest.approx(per[bw], abs=1e-15) and x["binding_condition"] in ("1b", "1c")
        assert abs(x["injection"]["rel_error"]) <= C.PC_INJECT_TOL                                    # the REALISED effect hits the target
    md = pc.render_pc_markdown(r)
    assert "Injektionsziel F" in md and "Nachpruefung N-2" in md and md.isascii()


def test_n2_null_mean_driftfree_is_a_mandatory_pin_taken_from_the_vorlauf_artifact(sig, nul, shrunk):
    assert "null_mean_driftfree" in schema.FROZEN_VARIANT_KEYS
    for bundle in (sig, nul):
        for wn in ("W1", "W2"):
            fz_y, fz_r = bundle["registered"]["windows"][wn]["frozen_v6"], bundle["report"]["windows"][wn]["frozen_v6"]
            assert fz_y["null_mean_driftfree"] == fz_r["null_mean_driftfree"]                       # copied, not recomputed
            for v in C.VARIANTS:
                assert fz_y["null_mean"][v] >= fz_y["null_mean_driftfree"][v]
    pins = schema.frozen_pin_table(sig["registered"])
    assert set(pins["W1"]["null_mean_driftfree"]) == set(C.VARIANTS)
    for mutate, exc in (
            (lambda r: r["windows"]["W1"]["frozen_v6"].pop("null_mean_driftfree"), SchemaError),
            (lambda r: r["windows"]["W2"]["frozen_v6"]["null_mean_driftfree"].__setitem__("mom1", None), SchemaError),
            (lambda r: r["windows"]["W1"]["frozen_v6"]["null_mean_driftfree"].__setitem__("mom4", r["windows"]["W1"]["frozen_v6"]["null_mean"]["mom4"] + 0.01), PinError),
            (lambda r: r["positive_control"].__setitem__("inject_target", "realisiert: z_krit * SE_T,W + 0.8416 * SD_T,W im bindenden Fenster"), PinError),
            (lambda r: r["positive_control"].__setitem__("inject_target_label", "Injektionsziel"), PinError),
            (lambda r: r["positive_control"].pop("inject_target_label"), PinError)):
        bad = copy.deepcopy(sig["registered"])
        mutate(bad)
        with pytest.raises(exc):
            schema.validate_registered(bad)


# ---- the exactly calibrated control world: expected PASS share 0.80 ---------------------------------

def _shrink_registration_only(mp) -> None:
    """The registered replicate counts of a fixture YAML (24 / 60 / 80) -- but the REAL control seeds and criteria (200 / 50 / 50)."""
    mp.setattr(C, "N_REPS_MIN", 24)
    mp.setattr(C, "N_BOOT_MIN", 60)
    mp.setattr(C, "N_PERM", 80)


def _exact_world(sig):
    """Frozen constants measured on the control world's own negative control (300 seeds 9000..9299), a (1b)-binding variant (mom1, natural
    q95) and a (1c)-binding variant (mom4, q95 set so that the (1c) term exceeds the (1b) term by 0.3 SD).  No injection yet.  Returns
    ``(shape, symbols, registered, pilot)``."""
    panel = F.make_panel(seed=21, k=48, n_late=4, signal=0.0, delist_weeks=(60, 100))
    shape, symbols, _ = pc.build_shape(panel, C.CUT_TEST)
    reg = copy.deepcopy(sig["registered"])
    reg["positive_control"]["criteria"] = {"sd_ratio_max": C.PC_SD_RATIO_MAX, "pass_share_min": C.PC_PASS_SHARE_MIN, "neg_pass_max": C.PC_NEG_PASS_MAX,
                                           "injection_tolerance": C.PC_INJECT_JUDGE_TOL}
    reg["positive_control"]["seeds"] = [min(C.PC_SEEDS_JUDGE), max(C.PC_SEEDS_JUDGE)]
    reg["positive_control"]["calibration_seeds_injection"] = [min(C.PC_SEEDS_INJECT), max(C.PC_SEEDS_INJECT)]
    reg["positive_control"]["calibration_seeds_world"] = [min(C.PC_SEEDS_SIGMA_G), max(C.PC_SEEDS_SIGMA_G)]
    lead, rules = C.LEAD_WEEKS, reg["rules"]
    stats: dict[str, dict[str, dict[str, float]]] = {wn: {} for wn in ("W1", "W2")}
    for widx, wn in enumerate(("W1", "W2")):
        sl = prelaunch.slice_window(shape["weeks"], reg["windows"][wn]["start"], reg["windows"][wn]["end"])
        alive, valid = shape["alive"][sl["lo"] - lead:sl["hi"]], shape["returns_valid"][sl["lo"] - lead:sl["hi"]]
        world = pc.world_params(reg, wn)
        w_j, floor = int(reg["windows"][wn]["w_judged"]), float(reg["windows"][wn]["frozen_v6"]["floor_fm8"])
        for v in ("mom1", "mom4"):
            ys, ses, pool = [], [], []
            for seed in range(9000, 9300):
                w = pc.synthesize_world(alive, valid, symbols, world, seed=seed, window_index=widx, variant=v, signal_ic=0.0, sigma_g=0.0)
                ics = np.asarray(pc.eval_world(w, alive, symbols, v))
                fin = ics[np.isfinite(ics)]                                                         # as the judgement does
                ys.append(float(fin.mean()))
                pool.append(fin)
                ses.append(est.se_rule(ics, floor, w_j, mean_block=float(rules["mean_block"]), n_boot=int(rules["n_boot"]), seed=int(rules["seed"]))["se"])
            y = np.asarray(ys)
            stats[wn][v] = {"m_df": float(y.mean()), "se_mean": float(y.std(ddof=1)), "e_se": float(np.mean(ses)),
                            "sd_week": float(np.concatenate(pool).std(ddof=1)), "q95_nat": float(np.quantile(y, 0.95))}
    for wn in ("W1", "W2"):
        fz = reg["windows"][wn]["frozen_v6"]
        fz["v_fm8"] = 0.5 * min(stats[wn][v]["sd_week"] ** 2 for v in ("mom1", "mom4"))                 # F2_null > 0, k_pred = 1 at F2_real = 0
        for v in ("mom1", "mom4"):
            s = stats[wn][v]
            if v == "mom1":
                q95 = s["q95_nat"]
            else:                                                                                       # (1c) term = (1b) term + 0.3 SD
                q_eff = Z * s["e_se"] + max(0.0, s["m_df"]) + 0.3 * s["se_mean"]
                q95 = q_eff if s["m_df"] >= 0.0 else q_eff + s["m_df"]
            for key, val in (("sd_week", s["sd_week"]), ("se_mean", s["se_mean"]), ("e_se_rule", s["e_se"]), ("null_mean", s["m_df"]),
                             ("null_mean_driftfree", s["m_df"]), ("q95", q95), ("q95_1000", q95), ("q95_10000", q95), ("q95_driftfree", q95),
                             ("q95_drifting", q95)):
                fz[key][v] = val
    pil: dict = {"variants": {v: {"handover": {"handed_over": False}} for v in C.VARIANTS}}
    for v in ("mom1", "mom4"):
        consts = handover.handover_constants(reg, v)
        pil["variants"][v]["handover"] = {"handed_over": True, "f2_real": 0.0,
                                          "per_window": handover.se_t_sd_t(consts, {"c_real": 0.01, "f2_real": 0.0})}
    schema.validate_registered(reg)
    return shape, symbols, reg, pil, stats


def test_n2_expected_pass_share_is_080_in_an_exactly_calibrated_world_for_1b_and_1c_binding_variants(sig):
    """DEC-101 Teil 2 (N-2): the expected PASS share in the binding window is Phi(z_80) = 0.80 where (1c) binds (the realised effect puts
    the window mean z_80 SD above ``q95_eff``) and Phi(z_80 + max(0, m_df)/SD_T) where (1b) binds (the null mean itself is the credit,
    ERSTFASSUNG 4 'ohne Gutschrift'); 200 judgement seeds, tolerance +-0.06.  The literal ERSTFASSUNG 4 target would give a clearly
    lower share for the (1c)-binding cell -- the review's finding (mom4 0.72 against the 0.734 line)."""
    with pytest.MonkeyPatch.context() as mp:
        _shrink_registration_only(mp)
        shape, symbols, reg, pil, stats = _exact_world(sig)
        rep = pc.run_positive_control(shape, symbols, reg, pil, observed_fingerprints=FP, registered_sha256=REGISTERED_SHA)
    assert len(C.PC_SEEDS_JUDGE) == 200
    seen = set()
    for v in ("mom1", "mom4"):
        x = rep["variants"][v]
        bw = x["binding_window"]
        comp = x["target_components"][bw]
        seen.add(comp["binding_condition"])
        assert x["target_effect"] == pytest.approx(comp["target"]) and comp["k_pred"] == 1.0
        assert abs(x["injection"]["rel_error"]) <= C.PC_INJECT_TOL and abs(x["judgement"]["effect_rel_error"]) <= C.PC_INJECT_JUDGE_TOL
        expected = _N.cdf(ZP + (max(0.0, comp["m_df"]) / comp["sd_t"] if comp["binding_condition"] == "1b" else 0.0))
        got = x["judgement"]["pass_share_binding"]
        assert abs(got - expected) <= 0.06, (v, bw, comp["binding_condition"], got, expected)
        assert x["criteria"]["b_pass_share"] and x["criteria"]["a_sd_ratio"] == {"W1": True, "W2": True}
        assert all(rate <= C.PC_NEG_PASS_MAX for rate in x["judgement"]["false_pass_rate_by_window"].values())
    assert seen == {"1b", "1c"}                                                                       # one variant of each kind was tested
    # the old literal target (z SE_T + z_80 SD_T) is below the (1c) requirement of the 1c-binding cell
    c4 = rep["variants"]["mom4"]["target_components"][rep["variants"]["mom4"]["binding_window"]]
    assert c4["binding_condition"] == "1c" and c4["term_1c"] - (Z * c4["se_t"] + ZP * c4["sd_t"]) > 0.2 * c4["sd_t"]


# ============================================================================
# N-4: the pilot attempt marker (unit level; the CLI end-to-end is in test_h32_cli.py)
# ============================================================================

def _fake_repo(tmp_path: Path, reg: dict) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    runs = repo / C.RUNS_REL
    pinned = repo / reg["pilot_window"]["out_dir"]
    runs.mkdir(parents=True)
    return repo, runs, pinned


def test_n4_the_marker_is_written_exclusively_with_sha_utc_mode_and_prefix_and_no_pilot_number(nul, tmp_path):
    reg = nul["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    lock = checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    when = datetime(2026, 10, 22, 8, 15, 30, tzinfo=timezone.utc)
    m = checks.write_attempt_marker(pinned, REGISTERED_SHA, lock, mode="pilot", now=when)
    path = pinned / "h32_pilot_attempt.json"
    assert path.is_file() and m["name"] == "h32_pilot_attempt.json" and m["attempt_utc"] == "2026-10-22T08:15:30Z"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered_sha256"] == REGISTERED_SHA and payload["attempt_utc"] == "2026-10-22T08:15:30Z" and payload["mode"] == "pilot"
    assert payload["prefix"] == "h32_pilot" and payload["rerun_dec"] is None and payload["schema"] == C.PILOT_ATTEMPT_SCHEMA
    blob = json.dumps(payload)
    for forbidden in ("x_p", "se_p", "t_p", "f2_real", "ic_weekly", "handed"):
        assert forbidden not in blob                                                                  # the marker holds no pilot number
    assert checks.attempt_marker_path(pinned, "h32_pilot_rerun_DEC-103") == pinned / "h32_pilot_rerun_DEC-103_attempt.json"
    with pytest.raises(PilotLockError, match="already exists"):                                       # never overwritten
        checks.write_attempt_marker(pinned, REGISTERED_SHA, lock, mode="pilot", now=when)
    assert json.loads(path.read_text(encoding="utf-8"))["attempt_utc"] == "2026-10-22T08:15:30Z"
    with pytest.raises(ValueError, match="sha256"):
        checks.write_attempt_marker(pinned, "xyz", lock)
    with pytest.raises(ValueError, match="data/harvest"):
        checks.write_attempt_marker(tmp_path / "data" / "harvest" / "x", REGISTERED_SHA, lock)


def test_n4_glob_and_find_pilot_results_capture_the_marker_and_it_blocks_a_second_run(nul, tmp_path):
    reg = nul["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    lock = checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    checks.write_attempt_marker(pinned, REGISTERED_SHA, lock)
    assert [p.name for p in pinned.glob("h32_pilot*")] == ["h32_pilot_attempt.json"]                  # the lock's glob
    rel = pinned.relative_to(runs).as_posix() + "/h32_pilot_attempt.json"
    assert checks.find_pilot_results(runs, REGISTERED_SHA) == [rel]                                    # the recursive search (registered_sha256 in the file)
    assert checks.find_pilot_results(runs, "cd" * 32) == []                                            # another registration: no hit
    with pytest.raises(PilotLockError, match=r"already exists.*h32_pilot_attempt.*exactly one pilot run"):
        checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    # the running attempt's own marker is not an earlier attempt (the writer's re-check)
    own = checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo, own_attempt_prefix="h32_pilot")
    assert own["rerun"] is False and own["scope"]["found"] == []
    # a re-run needs a DEC; the re-run's own marker carries its prefix and blocks a further re-run under the same DEC
    with pytest.raises(PilotLockError, match="not a DEC"):
        checks.check_rerun_lock(pinned, reg, "because", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    lock2 = checks.check_rerun_lock(pinned, reg, "DEC-103", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    assert lock2["rerun"] is True and lock2["prefix"] == "h32_pilot_rerun_DEC-103" and lock2["earlier_found"] == [rel]
    checks.write_attempt_marker(pinned, REGISTERED_SHA, lock2)
    assert (pinned / "h32_pilot_rerun_DEC-103_attempt.json").is_file()
    with pytest.raises(PilotLockError, match="needs its own DEC"):
        checks.check_rerun_lock(pinned, reg, "DEC-103", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    again = checks.check_rerun_lock(pinned, reg, "DEC-103", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo, own_attempt_prefix="h32_pilot_rerun_DEC-103")
    assert again["rerun"] is True                                                                       # its own marker alone does not block its writer
    assert checks.check_rerun_lock(pinned, reg, "DEC-104", registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)["prefix"] == "h32_pilot_rerun_DEC-104"


def test_n4_the_writer_ignores_its_own_marker_and_an_aborted_attempt_is_not_overwritten(sig, shrunk, tmp_path):
    reg = sig["registered"]
    repo, runs, pinned = _fake_repo(tmp_path, reg)
    lock = checks.check_rerun_lock(pinned, reg, None, registered_sha256=REGISTERED_SHA, runs_root=runs, repo_root=repo)
    checks.write_attempt_marker(pinned, REGISTERED_SHA, lock)
    w = pilot_mod.write_pilot_artifacts(pinned, sig["pilot_report"], reg, lock)                        # own marker present: the writer still writes
    assert (pinned / "h32_pilot.json").is_file() and w["prefix"] == "h32_pilot"
    assert {p.name for p in pinned.glob("h32_pilot*")} >= {"h32_pilot.json", "h32_pilot_attempt.json", "h32_pilot_fingerprint.json"}
    with pytest.raises(PilotLockError, match="exactly one pilot run"):
        pilot_mod.write_pilot_artifacts(pinned, sig["pilot_report"], reg, lock)                        # the second writer is refused as before


# ============================================================================
# N-5: no unscaled gate fallback; documentation fields; p formula
# ============================================================================

def _payload(with_block=True, **block):
    ns = {"sd_real": 0.05, "sd_week": 0.05, "m": 0.0011, "q95_frozen": 0.0170}
    ns.update(block)
    w = {"y": 0.021, "mean_ic": 0.021, "se_w": 0.010, "q95": 0.0170, "ceiling_k4": 0.005, "threshold_frozen": 0.0175, "bounce_ic": None, "w_judged": 52}
    if with_block:
        w["null_scaling"] = ns
    return {"entry": "H-32_mom1", "variant": "mom1", "direction": "positive", "z_krit": Z, "windows": {"W1": dict(w), "W2": copy.deepcopy(w)}}


def test_n5_the_gate_refuses_a_window_without_a_complete_null_scaling_block():
    assert gate.evaluate(_payload())["verdict"] == "PASS"
    with pytest.raises(GateError, match="null_scaling"):
        gate.evaluate(_payload(with_block=False))                                                     # the k = 1 fallback is gone
    with pytest.raises(GateError, match="null_scaling"):
        gate.window_conditions({"y": 0.021, "se_w": 0.010, "q95": 0.0170}, Z)
    p = _payload()
    del p["windows"]["W2"]["null_scaling"]["m"]
    with pytest.raises(GateError, match="complete null_scaling"):
        gate.evaluate(p)                                                                             # one incomplete window is enough
    with pytest.raises(GateError):
        gate.effective_q95({"null_scaling": "yes"})
    # non-finite VALUES in a complete block are not an error: k is NaN and the gate fails closed (as before)
    nan_block = gate.evaluate(_payload(sd_real=float("nan")))
    assert nan_block["verdict"] == "DROP" and not nan_block["per_window"]["W1"]["c_null_quantile"]


@pytest.fixture(scope="module")
def run_sig(sig):
    from bybit_edge.research.h32_fm8 import testrun
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        mp.setattr(testrun, "_null_recheck", lambda win, registered, log: {"within_tolerance": True, "rows": {}, "n_reps": 0, "seed": 53})
        return testrun.run_test(sig["panel"], sig["registered"], sig["pilot"], FP, registered_sha256=REGISTERED_SHA, p_replicates=sig["p_rep"])


def test_n5_the_run_supplies_the_block_and_the_round_trip_is_loud_without_it(run_sig, sig, shrunk, tmp_path):
    """The test run builds the block for every computed window; an artifact whose payload lost it fails the round trip (NO VERDICT) and
    the pure gate refuses the payload -- there is no silent k = 1."""
    from bybit_edge.research.h32_fm8 import testrun
    from bybit_edge.research.h32_fm8.errors import ArtifactError
    computed = [r for r in run_sig["results"].values() if r.get("computed")]
    assert computed
    for res in computed:
        for w in res["payload"]["windows"].values():
            assert set(w["null_scaling"]) >= set(gate.NULL_SCALING_KEYS)
        stripped = copy.deepcopy(res["payload"])
        del stripped["windows"]["W1"]["null_scaling"]
        with pytest.raises(GateError):
            gate.evaluate(stripped)
    out = tmp_path / "run"
    testrun.write_run_artifacts(out, run_sig, sig["registered"], pilot_sha256=sig["pilot_sha"], p_replicates=sig["p_rep"])
    pub = {k: v for k, v in run_sig.items() if k != "_series"}
    assert testrun.verify_run_artifacts(out, pub, sig["registered"], p_replicates=sig["p_rep"])["n_entry_windows_checked"] == 4
    tampered = copy.deepcopy(pub)
    entry = next(e for e, r in tampered["results"].items() if r.get("computed"))
    del tampered["results"][entry]["payload"]["windows"]["W1"]["null_scaling"]
    with pytest.raises(ArtifactError, match="scaled null"):
        testrun.verify_run_artifacts(out, tampered, sig["registered"], p_replicates=sig["p_rep"])


def test_n5_template_documents_the_commits_the_p_formula_and_the_header(sig, shrunk):
    tpl = vorlauf.build_template(sig["report"], bounce_spread=0.003621, code_commit_prelaunch="6e4b447")
    assert tpl["code_commit_prelaunch"] == "6e4b447" and tpl["code_commit_registration"] == "<wird vom Orchestrator gesetzt>"
    assert list(tpl)[:2] == ["code_commit_prelaunch", "code_commit_registration"]
    text = vorlauf.template_yaml_text(tpl, sig["report"], source_sha256="ab" * 32)
    head = text.split("hypotheses:")[0]
    assert "# Quelle (Vorlauf-JSON) sha256: " + "ab" * 32 in head                                      # the full prelaunch sha256 stays in the header
    assert "code_commit_prelaunch): 6e4b447" in head and "code_commit_registration): <wird vom Orchestrator gesetzt>" in head and C.CODE_COMMIT_NOTE in head
    assert tpl["fdr"]["p_formula"] == C.P_FORMULA and "d' = max(0, m) + k * (d - m)" in C.P_FORMULA and "DEC-101 E2" in C.P_FORMULA
    unset = vorlauf.build_template(sig["report"], bounce_spread=0.003621)
    assert unset["code_commit_prelaunch"] == C.CODE_COMMIT_PRELAUNCH_UNSET
    for bad in ("zzz", "6e4b44", "6E4B447;rm", "x" * 41):
        with pytest.raises(ValueError, match="commit hash"):
            vorlauf.build_template(sig["report"], bounce_spread=0.003621, code_commit_prelaunch=bad)
    import yaml
    reg = yaml.safe_load(text)
    schema.validate_registered({**sig["registered"], "code_commit_prelaunch": reg["code_commit_prelaunch"]})
    base = copy.deepcopy(sig["registered"])
    for key, val, exc in (("code_commit_prelaunch", None, SchemaError), ("code_commit_registration", 1234567, SchemaError),
                          ("code_commit_registration", "not a hash", SchemaError), ("code_commit_prelaunch", "6e4b447", None),
                          ("code_commit_registration", "f7dd4711a0c3be7e8a92cd1ee5b22ee8d6c7e1de", None)):
        bad = copy.deepcopy(base)
        bad[key] = val
        if exc is None:
            schema.validate_registered(bad)
        else:
            with pytest.raises(exc):
                schema.validate_registered(bad)
    for mutate in (lambda r: r["fdr"].__setitem__("p_formula", "p = (1 + #{null replicate window means >= observed window mean, registered direction}) / (1 + R)"),
                   lambda r: r["fdr"].pop("p_formula"), lambda r: r.pop("code_commit_registration")):
        bad = copy.deepcopy(base)
        mutate(bad)
        with pytest.raises((PinError, SchemaError)):
            schema.validate_registered(bad)
