"""Unit tests for WP-13 RUN MODE (DEC-75 Entscheidung 1/2, task brief TASK B).

Covers:
  - START LOCK: ``scripts/wp13_xsec.py --run`` refuses (rc=1) without a
    matching ``--registered-sha256``, and BEFORE touching any panel path.
  - ``gates.evaluate`` pure-function T4 test (same payload -> identical
    verdict, twice).
  - The four required synthetic scenarios: positive fixture -> PASS, null
    -> DROP, adversarial beta-correlated fixture -> DROP, bounce fixture
    -> label (verdict unaffected).
  - The per-component pure functions (SE, moving-block bootstrap CI,
    Max-p, liquidity-decile sensitivity, lag profile, BH) on small
    synthetic arrays.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp7_universe import panel_load
from bybit_edge.research.wp12_delisting import delisted_panel
from bybit_edge.research.wp13_xsec import characteristics, gates, ic, nulls
from bybit_edge.research.wp13_xsec import run as run_mod

from tests.unit.test_wp12b_delisted_panel import _closes, _load_script, _write_full_history

WP13 = _load_script("wp13_xsec.py")

#: DEC-89 E1: the registered bounce-fixture parameters the hand-built test files carry -- the production values
#: (``rules.bounce_spread`` = WP-7 spread census, median perp spread of decile D10 = 36.21 bp / 1e4;
#: ``windows.<W>.bounce_sigma_true`` = the Vorlauf's median weekly symbol vol, W1 0.17186 / W2 0.13311). The run has
#: no defaults for them any more (a missing value is a loud fail), so every file that computes a rev_gap entry has them.
BOUNCE_SPREAD = 0.003621
BOUNCE_SIGMA = {"W1": 0.17186, "W2": 0.13311}


# ============================================================================
# START LOCK
# ============================================================================

def _minimal_registered_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "registered.yaml"
    p.write_text(
        "hypotheses:\n  H-28: {variant: mom1, direction: positive}\n"
        "windows:\n  W1: {start: '2024-07-01', end: '2025-06-30', ic_min_capped: {mom1: 0.02}}\n"
        "  W2: {start: '2025-07-01', end: '2026-06-30', ic_min_capped: {mom1: 0.02}}\n"
        "rules: {seed: 53}\n", encoding="utf-8")
    return p


def test_run_refuses_without_registered_sha256(tmp_path):
    reg = _minimal_registered_yaml(tmp_path)
    ns = WP13.argparse.Namespace(
        run=True, prelaunch=False, registered=str(reg), registered_sha256="",
        panel_base=str(tmp_path / "nonexistent_panel"), delisted_base=str(tmp_path / "nonexistent_del"),
        delisted_manifest="", delisting_dates="", start_year=2021, end_year=2026, as_of="2027-01-01",
        out=str(tmp_path / "out"), seed=53, convention="close_at_last", allow_partial=False)
    rc = WP13.cmd_run(ns)
    assert rc == 1
    assert not (tmp_path / "out").exists()          # never got anywhere near writing output


def test_run_refuses_with_wrong_registered_sha256(tmp_path):
    reg = _minimal_registered_yaml(tmp_path)
    ns = WP13.argparse.Namespace(
        run=True, prelaunch=False, registered=str(reg), registered_sha256="0" * 64,
        panel_base=str(tmp_path / "nonexistent_panel"), delisted_base=str(tmp_path / "nonexistent_del"),
        delisted_manifest="", delisting_dates="", start_year=2021, end_year=2026, as_of="2027-01-01",
        out=str(tmp_path / "out"), seed=53, convention="close_at_last", allow_partial=False)
    rc = WP13.cmd_run(ns)
    assert rc == 1
    assert not (tmp_path / "out").exists()


def test_run_proceeds_past_lock_with_correct_sha256_then_fails_on_missing_panel(tmp_path):
    """The lock passes (correct hash) but the run STILL cannot reach a
    real panel that does not exist -- proves the lock check happens
    strictly BEFORE any panel I/O, not that the whole pipeline is a
    no-op."""
    reg = _minimal_registered_yaml(tmp_path)
    correct_sha = run_mod.sha256_of_file(reg)
    ns = WP13.argparse.Namespace(
        run=True, prelaunch=False, registered=str(reg), registered_sha256=correct_sha,
        panel_base=str(tmp_path / "nonexistent_panel"), delisted_base=str(tmp_path / "nonexistent_del"),
        delisted_manifest="", delisting_dates="", start_year=2021, end_year=2026, as_of="2027-01-01",
        out=str(tmp_path / "out"), seed=53, convention="close_at_last", allow_partial=False)
    rc = WP13.cmd_run(ns)
    assert rc == 1                                   # fails for a DIFFERENT reason (no panel)
    assert not (tmp_path / "out").exists()


def test_cli_main_requires_exactly_one_mode(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py"])
    with pytest.raises(SystemExit):
        WP13.main()


def test_cli_main_run_mode_requires_registered_flag(monkeypatch):
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py", "--run", "--out", "/tmp/x"])
    with pytest.raises(SystemExit):
        WP13.main()


# ============================================================================
# gates.evaluate -- T4 (pure, conserved payload)
# ============================================================================

def _conserved_payload():
    return {
        "hypothesis": "H-28", "variant": "mom1", "direction": "positive",
        "windows": {
            # DEC-76 Entscheidung 1 (b): res_quantile_drifting is the FROZEN drifting-null
            # residualized-mean-IC quantile -- both windows' residualized_mean_ic clears it
            # here (0.045 > 0.03, 0.035 > 0.025), so the T4 baseline still PASSes.
            "W1": {"mean_ic": 0.05, "se": 0.01, "ci_bound_toward_sign": 0.02, "ic_min_capped": 0.02,
                   "residualized_mean_ic": 0.045, "res_quantile_drifting": 0.03,
                   "selection_ceiling_mean_of_max": 0.01},
            "W2": {"mean_ic": 0.04, "se": 0.01, "ci_bound_toward_sign": 0.015, "ic_min_capped": 0.018,
                   "residualized_mean_ic": 0.035, "res_quantile_drifting": 0.025,
                   "selection_ceiling_mean_of_max": 0.01},
        },
        "persistence_null_pass": True, "bh_fdr_pass": True,
        "liquidity_ic_without_d1": None, "bounce_ic": None,
    }


def test_t4_gate_arithmetic_pure_on_conserved_payload():
    payload = _conserved_payload()
    v1 = gates.evaluate(payload)
    v2 = gates.evaluate(payload)
    assert v1 == v2
    assert payload == _conserved_payload()           # evaluate() never mutates its input
    assert v1["verdict"] == "PASS"


def test_gl012_kill_forces_drop_before_pass_logic():
    payload = _conserved_payload()
    payload["windows"]["W1"]["selection_ceiling_mean_of_max"] = 0.03   # >= ic_min_capped 0.02
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP"
    assert v["gl012_kill"] is True
    assert any("GL-012" in l for l in v["labels"])


def test_c10_hard_one_window_failing_drops_whole_hypothesis():
    payload = _conserved_payload()
    payload["windows"]["W2"]["mean_ic"] = 0.001   # too small in W2
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP"
    assert v["per_window"]["W1"]["window_pass"] is True
    assert v["per_window"]["W2"]["window_pass"] is False


def test_beta_control_failure_drops_even_with_strong_raw_ic():
    payload = _conserved_payload()
    payload["windows"]["W1"]["residualized_mean_ic"] = 0.0001   # beta-control fails
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP"


def test_report_only_components_never_change_verdict():
    payload = _conserved_payload()
    payload["persistence_null_pass"] = False
    payload["bh_fdr_pass"] = False
    v = gates.evaluate(payload)
    assert v["verdict"] == "PASS"                     # report-only, DEC-75 Entscheidung 1 (6)
    assert any("report-only" in l for l in v["labels"])


def test_beta_control_quantile_failure_drops_even_with_ic_min_satisfied():
    """DEC-76 Entscheidung 1 (b), additive: a residualized IC that clears
    the OLD ``|IC_res| >= IC_min`` bar can still fail the NEW requirement
    of lying beyond the drifting null's own residualized quantile -- this
    is the exact gap DEC-76 closes (a residualized IC that is "big enough"
    in absolute terms but still within what the null itself can produce)."""
    payload = _conserved_payload()
    payload["windows"]["W1"]["res_quantile_drifting"] = 0.05   # > residualized_mean_ic (0.045)
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP"
    assert v["per_window"]["W1"]["beta_control_magnitude_ok"] is True    # old check still passes
    assert v["per_window"]["W1"]["beta_control_beyond_drifting_null_ok"] is False  # new check fails
    assert v["per_window"]["W1"]["window_pass"] is False


def test_beta_control_quantile_absent_is_backward_compatible():
    """A payload WITHOUT ``res_quantile_drifting`` (pre-DEC-76 shape) must
    behave exactly as before -- the new component is additive, never
    retroactively stricter."""
    payload = _conserved_payload()
    for w in payload["windows"].values():
        del w["res_quantile_drifting"]
    v = gates.evaluate(payload)
    assert v["verdict"] == "PASS"
    assert v["per_window"]["W1"]["beta_control_beyond_drifting_null_ok"] is True


def test_liquidity_label_does_not_change_verdict_but_bounce_does():
    """DEC-87 (I) (formerly ``test_liquidity_and_bounce_labels_do_not_change_verdict``, which pinned the
    pre-DEC-87 behaviour): (1) the Liquiditaets-Etikett is verdict-neutral and fires when ``IC_ohne_D1,W``
    is NOT beyond half of that window's IC_min (for a negative registration ``> -0.5*IC_min``) in at least one
    window; (2) the bounce rule is a KILL again (DEC-75 (5): "Etikett Artefakt, KEIN PASS"): ``|IC_bounce,W| >=
    |IC_W|`` in any window -> no PASS."""
    payload = _conserved_payload()                      # positive registration, PASS baseline
    # positive direction: IC_ohne_D1 below +0.5*IC_min in W1 -> the effect did not survive -> label, verdict stays
    payload["liquidity_ic_without_d1"] = {"W1": 0.5 * payload["windows"]["W1"]["ic_min_capped"] - 0.001,
                                          "W2": 0.04}
    v = gates.evaluate(payload)
    assert v["verdict"] == "PASS" and v["liquidity_label"] is True and v["liquidity_windows"] == ["W1"]
    assert any("Illiquiditaets-Artefakt" in l for l in v["labels"])
    # an effect that survives in both windows -> no label
    payload["liquidity_ic_without_d1"] = {"W1": 0.04, "W2": 0.04}
    assert gates.evaluate(payload)["liquidity_label"] is False
    # bounce: |IC_bounce,W2| >= |IC_W2| -> not PASS although W1's bounce is harmless
    payload = _conserved_payload()
    payload["bounce_ic"] = {"W1": 0.001, "W2": payload["windows"]["W2"]["mean_ic"] + 0.01}
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP" and v["bounce_kill"] is True and v["bounce_windows"] == ["W2"]
    assert any("Artefakt Bounce in W2" in l and "KEIN PASS" in l for l in v["labels"])
    assert all(r["window_pass"] for r in v["per_window"].values())      # every other component still passes


def test_liquidity_and_bounce_labels_do_not_change_verdict():
    """DEC-87: kept under its old id (it pinned the pre-DEC-87 "labels only" behaviour for BOTH rules). The contract
    changed: the liquidity label still leaves the verdict alone, the bounce rule is a KEIN-PASS again -- see
    :func:`test_liquidity_label_does_not_change_verdict_but_bounce_does`, which this id now delegates to."""
    test_liquidity_label_does_not_change_verdict_but_bounce_does()


def test_liquidity_label_direction_negative_and_old_inverted_condition_is_gone():
    """DEC-87 (I): for H-29 (negative) the label fires at ``IC_ohne_D1 > -0.5*IC_min`` -- the pre-DEC-87
    code labelled exactly the OPPOSITE case (``<= -0.5*IC_min``, i.e. the effect surviving) and only in W1."""
    payload = _conserved_payload()
    payload["hypothesis"], payload["variant"], payload["direction"] = "H-29", "rev_gap", "negative"
    for w in payload["windows"].values():
        for k in ("mean_ic", "ci_bound_toward_sign", "residualized_mean_ic", "res_quantile_drifting"):
            w[k] = -w[k]
    survives = {wn: -0.5 * w["ic_min_capped"] - 0.001 for wn, w in payload["windows"].items()}
    payload["liquidity_ic_without_d1"] = survives
    assert gates.evaluate(payload)["liquidity_label"] is False           # old code labelled this case
    payload["liquidity_ic_without_d1"] = {"W1": survives["W1"], "W2": -0.5 * payload["windows"]["W2"]["ic_min_capped"] + 0.001}
    v = gates.evaluate(payload)
    assert v["liquidity_label"] is True and v["liquidity_windows"] == ["W2"]   # W2 only: not a W1-only rule
    assert v["verdict"] == "PASS"


def test_gate5_component_blocks_pass_and_fails_closed_on_nan():
    """DEC-87 Gate (5): ``gate5_median_spearman`` must be < 0.60 in each window; absent = not applicable; NaN
    fails closed."""
    payload = _conserved_payload()
    assert gates.evaluate(payload)["verdict"] == "PASS"                    # absent -> not applicable
    payload["windows"]["W1"]["gate5_median_spearman"] = 0.15
    payload["windows"]["W2"]["gate5_median_spearman"] = 0.142
    assert gates.evaluate(payload)["verdict"] == "PASS"
    payload["windows"]["W2"]["gate5_median_spearman"] = 0.61
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP" and v["per_window"]["W2"]["gate5_ok"] is False
    assert any("Gate (5) verfehlt in W2" in l for l in v["labels"])
    payload["windows"]["W2"]["gate5_median_spearman"] = float("nan")
    assert gates.evaluate(payload)["per_window"]["W2"]["gate5_ok"] is False


def test_binding_quantile_is_the_more_extreme_of_driftfree_and_drifting():
    """DEC-87 (E): the gate judges against ``res_quantile_binding`` (more extreme in the hypothesis direction);
    the pre-DEC-87 key ``res_quantile_drifting`` alone is still honoured (backward compatible)."""
    assert nulls.binding_quantile(0.020, 0.025, "positive") == 0.025
    assert nulls.binding_quantile(0.020, 0.015, "positive") == 0.020
    assert nulls.binding_quantile(-0.020, -0.025, "negative") == -0.025
    assert nulls.binding_quantile(-0.020, -0.015, "negative") == -0.020
    assert nulls.binding_quantile(None, 0.02, "positive") == 0.02 and nulls.binding_quantile(None, None, "negative") is None
    payload = _conserved_payload()                                       # residualized 0.045 / 0.035
    payload["windows"]["W1"]["res_quantile_binding"] = 0.05             # stricter than the 0.03 drifting value
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP" and v["per_window"]["W1"]["beta_control_beyond_drifting_null_ok"] is False
    payload["windows"]["W1"]["res_quantile_binding"] = 0.04             # binding wins over the (looser) legacy key
    assert gates.evaluate(payload)["verdict"] == "PASS"


# ============================================================================
# per-component pure functions
# ============================================================================

def test_se_of_mean_ic_uses_max_of_floor_and_sd():
    ic_weekly = np.array([0.0, 0.5, -0.5, 0.0, 0.3, -0.3])
    info_low_floor = run_mod.se_of_mean_ic(ic_weekly, floor=0.001, w_judged=5)
    assert info_low_floor["dispersion_used"] == pytest.approx(info_low_floor["sd_ic"])
    info_high_floor = run_mod.se_of_mean_ic(ic_weekly, floor=10.0, w_judged=5)
    assert info_high_floor["dispersion_used"] == 10.0


def test_moving_block_bootstrap_ci_bound_direction():
    rng = np.random.default_rng(0)
    ic_weekly = rng.normal(0.05, 0.02, size=60)
    pos = run_mod.moving_block_bootstrap_ci(ic_weekly, direction="positive", n_reps=300, seed=53)
    assert pos["ci_bound_toward_sign"] < ic_weekly.mean()   # lower bound below the sample mean
    neg = run_mod.moving_block_bootstrap_ci(-ic_weekly, direction="negative", n_reps=300, seed=53)
    assert neg["ci_bound_toward_sign"] > (-ic_weekly).mean()


def test_max_p_over_windows_takes_the_worse_pvalue():
    assert run_mod.max_p_over_windows({"W1": 0.01, "W2": 0.20}) == pytest.approx(0.20)
    assert math.isnan(run_mod.max_p_over_windows({"W1": float("nan")}))


def test_liquidity_decile_sensitivity_excludes_d1_only():
    w, k = 30, 60
    rng = np.random.default_rng(2)
    returns = rng.normal(0, 0.03, size=(w, k))
    characteristic = rng.normal(0, 1, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    turnover = np.tile(np.arange(1, k + 1, dtype=np.float64), (w, 1))   # symbol j always in decile ~ j
    res = run_mod.liquidity_decile_sensitivity(characteristic, returns, alive, turnover)
    assert math.isfinite(res["mean_ic_without_d1"])
    assert res["n_weeks_used"] <= w - 1


def test_lag_profile_only_registered_lag_shows_alignment():
    w, k = 30, 40
    rng = np.random.default_rng(11)
    returns = rng.normal(0, 1, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    ranks = np.array([np.argsort(np.argsort(returns[t])) for t in range(w)], dtype=np.float64)
    char = np.full((w, k), np.nan)
    char[:-1] = ranks[1:]                        # char[t] == exact rank of returns[t+1] (lag=0, registered)
    profile = run_mod.lag_profile(char, returns, alive, min_universe=5)
    assert profile[0] == pytest.approx(1.0, abs=1e-9)
    for lag in (-1, 1, 2):
        assert abs(profile[lag]) < 0.3


def test_benjamini_hochberg_report_only_rejects_small_pvalues():
    p = {"mom1": 0.001, "mom2": 0.5, "mom4": 0.6, "rev_gap": 0.7, "vol_rv": 0.8, "vol_max": 0.9, "vol_beta": 0.95}
    res = run_mod.benjamini_hochberg(p, alpha=0.10)
    assert res["reject"]["mom1"] is True
    assert res["reject"]["vol_beta"] is False


def test_variant_window_payload_reports_drop_convention_lag_profile_beta_calibration():
    seed, k, w = 5, 60, 40
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    alive = np.ones((w, k_full), dtype=bool)
    beta_8w = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    payload = run_mod.variant_window_payload(
        characteristic, returns, alive, symbols, variant="mom1", direction="positive",
        ic_min_capped=0.02, w_judged=w - 1, floor=0.05, selection_ceiling_mean_of_max=0.01,
        beta_8w_pit=beta_8w, n_reps_bootstrap=30, n_reps_permutation=30, seed=53)
    assert payload["mean_ic_drop_convention"] is not None and math.isfinite(payload["mean_ic_drop_convention"])
    assert payload["lag_profile"] is not None and set(payload["lag_profile"]) == {-1, 0, 1, 2}
    assert payload["beta_calibration_mean_ic"] is not None and math.isfinite(payload["beta_calibration_mean_ic"])


def test_bounce_fixture_ic_is_deterministic_and_finite():
    r1 = run_mod.bounce_fixture_ic(40, 30, spread=BOUNCE_SPREAD, sigma_true=BOUNCE_SIGMA["W1"], seed=53)
    r2 = run_mod.bounce_fixture_ic(40, 30, spread=BOUNCE_SPREAD, sigma_true=BOUNCE_SIGMA["W1"], seed=53)
    assert r1 == r2
    assert math.isfinite(r1["ic_bounce"])
    assert r1["spread"] == BOUNCE_SPREAD and r1["sigma_true"] == BOUNCE_SIGMA["W1"]      # DEC-89 E1: echoed


# ============================================================================
# end-to-end run_hypothesis: the four required scenarios
# ============================================================================

def _floor_and_symbols(alive, w):
    floor = nulls.analytic_permutation_floor(alive, [str(i) for i in range(w)])
    return floor["e_floor"], floor["w_judged"]


def _drifting_res_quantile(returns, alive, symbols, variant, *, seed=53, n_reps=60):
    """DEC-76 Entscheidung 1 (b), test helper: the SAME recomputation
    ``run_full`` does per window -- the drifting factor null's own
    residualized-mean-IC quantile, sized to THIS fixture's real K
    series/W. Used by the four end-to-end scenarios below to exercise the
    new beta-control component with a genuine (not hand-picked) value."""
    fp = nulls.factor_preserving_null(returns, alive, symbols, variants=(variant,),
                                       n_reps=n_reps, seed=seed, drift_f=nulls.DRIFT_F_DRIFTING)
    return fp["variants"][variant]["quantile_one_sided_residualized"]


def test_positive_fixture_end_to_end_pass():
    seed, k, w = 0, 120, 52
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    # DEC-76 (b): the beta-control PASS component must ALSO clear the drifting null's own
    # residualized-mean-IC quantile (report-only under DEC-75, now a real gate input) -- a
    # stronger injected signal than the pre-DEC-76 target_rho=0.08 is needed for that,
    # since (as DEC-76's "Anlass" finding shows) even RESIDUALIZED noise has real spread at
    # this K/W once heterogeneous beta hedging is imperfect.
    target_rho = 0.30
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    a = target_rho / math.sqrt(max(1 - target_rho ** 2, 1e-9))
    returns[1:] += a * 0.03 * characteristic[:-1]
    alive = np.ones((w, k_full), dtype=bool)
    beta_8w = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    e_floor, w_judged = _floor_and_symbols(alive, w)
    rqd = _drifting_res_quantile(returns, alive, symbols, "mom1", n_reps=300)   # DEC-76 (b)

    res = run_mod.run_hypothesis(
        "H-POS", "mom1", "positive",
        {"W1": characteristic, "W2": characteristic}, {"W1": returns, "W2": returns},
        {"W1": alive, "W2": alive}, symbols,
        {"W1": 0.02, "W2": 0.02}, {"W1": w_judged, "W2": w_judged},
        {"W1": e_floor, "W2": e_floor}, {"W1": 0.005, "W2": 0.005},
        beta_8w_pit_by_window={"W1": beta_8w, "W2": beta_8w},
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53,
        res_quantile_drifting_by_window={"W1": rqd, "W2": rqd})
    assert res["verdict"]["verdict"] == "PASS"                      # real signal clears the null quantile too
    assert res["payload"]["windows"]["W1"]["res_quantile_drifting"] == pytest.approx(rqd)


def test_null_fixture_end_to_end_drop():
    seed, k, w = 1, 120, 52
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    alive = np.ones((w, k_full), dtype=bool)
    beta_8w = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    e_floor, w_judged = _floor_and_symbols(alive, w)
    rqd = _drifting_res_quantile(returns, alive, symbols, "mom1")   # DEC-76 (b)

    res = run_mod.run_hypothesis(
        "H-NULL", "mom1", "positive",
        {"W1": characteristic, "W2": characteristic}, {"W1": returns, "W2": returns},
        {"W1": alive, "W2": alive}, symbols,
        {"W1": 0.02, "W2": 0.02}, {"W1": w_judged, "W2": w_judged},
        {"W1": e_floor, "W2": e_floor}, {"W1": 0.005, "W2": 0.005},
        beta_8w_pit_by_window={"W1": beta_8w, "W2": beta_8w},
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53,
        res_quantile_drifting_by_window={"W1": rqd, "W2": rqd})
    assert res["verdict"]["verdict"] == "DROP"


def test_adversarial_beta_fixture_end_to_end_drop():
    """DEC-75 Entscheidung 1 (3) adversarial fixture: AR(1) market factor
    (rho=0.2, drift), betas 0.5..2.0, NO true cross-sectional
    predictability -- raw mom1 IC may look non-zero (market-timing
    artifact), but the beta-control (residualised IC) fails, so the gate
    MUST drop."""
    seed, k, w = 7, 150, 104
    rng = np.random.default_rng(seed)
    rho_f, drift_f, sigma_f = 0.2, 0.002, 0.05
    beta_true = rng.uniform(0.5, 2.0, size=k)
    f = np.empty(w)
    f[0] = drift_f / (1.0 - rho_f) + sigma_f * rng.standard_normal()
    for t in range(1, w):
        f[t] = drift_f + rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    idio = rng.normal(0.0, sigma_f, size=(w, k))
    returns = beta_true[None, :] * f[:, None] + idio
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, f[:, None]], axis=1)
    alive = np.ones((w, k + 1), dtype=bool)
    mom1 = characteristics.momentum_characteristic(returns_full, trail_win=1)
    beta_8w = characteristics.beta_characteristic(returns_full, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    e_floor, w_judged = _floor_and_symbols(alive, w)
    # DEC-76 (b): the SAME drifting-null quantile a real run would recompute for this window --
    # the adversarial fixture's own residualized IC must fail to clear it (Anlass, verbatim).
    rqd = _drifting_res_quantile(returns_full, alive, symbols, "mom1", n_reps=100)

    res = run_mod.run_hypothesis(
        "H-ADV", "mom1", "positive",
        {"W1": mom1, "W2": mom1}, {"W1": returns_full, "W2": returns_full},
        {"W1": alive, "W2": alive}, symbols,
        {"W1": 0.02, "W2": 0.02}, {"W1": w_judged, "W2": w_judged},
        {"W1": e_floor, "W2": e_floor}, {"W1": 0.005, "W2": 0.005},
        beta_8w_pit_by_window={"W1": beta_8w, "W2": beta_8w},
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53,
        res_quantile_drifting_by_window={"W1": rqd, "W2": rqd})
    assert res["verdict"]["verdict"] == "DROP"
    w1 = res["payload"]["windows"]["W1"]
    assert abs(w1["residualized_mean_ic"]) < abs(w1["mean_ic"]) or abs(w1["residualized_mean_ic"]) < w1["ic_min_capped"]
    assert w1["res_quantile_drifting"] == pytest.approx(rqd)
    assert v_beta_control_ok(w1) is False


def v_beta_control_ok(w1_payload: dict) -> bool:
    """Small local re-derivation of ``gates._window_pass``'s beta-control-
    beyond-null component, for a direct assertion without reaching into
    ``gates``'s private function."""
    resid_ic, quantile = w1_payload["residualized_mean_ic"], w1_payload["res_quantile_drifting"]
    if resid_ic is None or quantile is None:
        return False
    return resid_ic > quantile   # H-ADV is registered "positive"


def test_bounce_fixture_end_to_end_bounce_is_no_pass():
    """DEC-87 (I) (formerly ``test_bounce_fixture_end_to_end_label_not_verdict_change``, which pinned that a bounce
    only produced a label): directly exercises ``gates.evaluate``'s bounce rule on a hypothesis that otherwise
    PASSes -- ``|IC_bounce,W| >= |IC_W|`` is a KEIN-PASS (DEC-75 (5), reinstated), the verdict is DROP with the
    ``Artefakt Bounce`` label; a harmless bounce leaves the PASS alone."""
    payload = _conserved_payload()
    payload["hypothesis"], payload["variant"], payload["direction"] = "H-29", "rev_gap", "negative"
    for w in payload["windows"].values():
        w["mean_ic"] = -w["mean_ic"]
        w["ci_bound_toward_sign"] = -w["ci_bound_toward_sign"]
        w["residualized_mean_ic"] = -w["residualized_mean_ic"]
        w["res_quantile_drifting"] = -w["res_quantile_drifting"]   # DEC-76 (b): negative-direction quantile
    bounce = run_mod.bounce_fixture_ic(60, 60, spread=BOUNCE_SPREAD, sigma_true=BOUNCE_SIGMA["W1"], seed=53)
    harmless = {wn: abs(bounce["ic_bounce"]) for wn in payload["windows"]}
    assert all(harmless[wn] < abs(payload["windows"][wn]["mean_ic"]) for wn in harmless)
    payload["bounce_ic"] = harmless
    assert gates.evaluate(payload)["verdict"] == "PASS"
    payload["bounce_ic"] = {"W1": max(abs(bounce["ic_bounce"]), abs(payload["windows"]["W1"]["mean_ic"]) + 0.05),
                            "W2": harmless["W2"]}
    v = gates.evaluate(payload)
    assert v["verdict"] == "DROP" and v["bounce_kill"] is True
    assert any("Bounce" in l for l in v["labels"])


def test_bounce_fixture_end_to_end_label_not_verdict_change():
    """DEC-87: kept under its old id (it pinned that a bounce only produced a LABEL). The contract changed (DEC-75 (5)
    reinstated by DEC-87 (I)): see :func:`test_bounce_fixture_end_to_end_bounce_is_no_pass`, which this id delegates to."""
    test_bounce_fixture_end_to_end_bounce_is_no_pass()


# ============================================================================
# run_full orchestrator, end-to-end on a synthetic union panel
# ============================================================================

from datetime import date  # noqa: E402


def _build_run_fixture_tree(tmp_path: Path):
    """Reuses the SAME WP-12b fixture builders ``test_wp13_xsec.py``'s
    prelaunch end-to-end test does -- a small union panel spanning
    L/W1/W2, one delisted symbol, one BTCUSDT column."""
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    del_base = tmp_path / "panel_1d_delisted"
    del_manifest = del_base / "panel_manifest.sqlite"

    full_start, full_end = date(2021, 1, 1), date(2026, 6, 30)
    for i, sym in enumerate(["AAAUSDT", "BTCUSDT", "ZZZUSDT", "QQQUSDT"]):
        _write_full_history(surv_base, surv_manifest, sym,
                             _closes(full_start, full_end, seed=i + 1), as_of_date=full_end)
    delist_date = date(2025, 2, 10)
    _write_full_history(del_base, del_manifest, "MMMUSDT",
                         _closes(full_start, delist_date, seed=9), as_of_date=delist_date)
    dd = delisted_panel.write_delisting_dates_json(del_base, {
        "MMMUSDT": {"delist_date": delist_date.isoformat(), "announcement_id": "ann-mmmusdt",
                    "source": "delisting_ms"}})

    as_of = date(2027, 1, 1)
    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2021, year_end=2026, as_of=as_of, delisting_dates_path=Path(dd["path"]))
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    return panel, weekly


def _window_calibration(rho_f: float, beta_sd: float) -> dict:
    """DEC-87 (D): a per-window ``calibration`` block (``stress`` is required by the schema; the numbers are
    arbitrary small-panel values -- the run reads them DIRECTLY, no search)."""
    block = lambda r, b, share: {"rho_f": r, "beta_sd_calibrated": b, "target_factor_share": share}   # noqa: E731
    return {"measured": block(rho_f / 2, beta_sd * 0.7, 0.02), "stress": block(rho_f, beta_sd, 0.04),
            "zero": block(0.0, beta_sd * 0.7, 0.02)}


def _registered_for_fixture() -> dict:
    ic_min_all = {v: 0.02 for v in characteristics.VARIANT_NAMES}
    return {
        "hypotheses": {"H-28": {"variant": "mom1", "direction": "positive"},
                       "H-29": {"variant": "rev_gap", "direction": "negative"},
                       "H-30": {"variant": "vol_rv", "direction": "negative", "outcome": "vol_weighted"}},
        "windows": {
            "W1": {"start": "2024-07-01", "end": "2025-06-30", "ic_min_capped": ic_min_all,
                   "bounce_sigma_true": BOUNCE_SIGMA["W1"], "calibration": _window_calibration(0.05, 0.50)},
            "W2": {"start": "2025-07-01", "end": "2026-06-30", "ic_min_capped": ic_min_all,
                   "bounce_sigma_true": BOUNCE_SIGMA["W2"], "calibration": _window_calibration(0.06, 0.45)},
            "L": {"start": "2021-03-01", "end": "2024-06-30"},
        },
        "beta_control": {"method": "ts_resid_8w", "beta_window_weeks": 8},   # DEC-77 Entscheidung 2
        "rules": {"seed": 53, "n_reps_bootstrap": 20, "n_reps_permutation": 20, "n_reps_factor_null": 20,
                  "n_sims_persistence": 20, "bounce_spread": BOUNCE_SPREAD},
    }


def test_run_full_orchestrator_end_to_end_on_synthetic_union_panel(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    report = run_mod.run_full(panel, weekly, registered)

    assert set(report["results"].keys()) == {"H-28", "H-29", "H-30"}
    for hyp, res in report["results"].items():
        assert res["verdict"]["verdict"] in ("PASS", "DROP")
        assert "W1" in res["payload"]["windows"] and "W2" in res["payload"]["windows"]
    assert report["results"]["H-29"]["payload"]["liquidity_ic_without_d1"] is not None
    assert report["results"]["H-29"]["payload"]["bounce_ic"] is not None
    assert "L" in report["windows_meta"]                   # L present (descriptive/sealed), never judged

    artifacts = run_mod.write_run_artifacts(tmp_path / "out", report)
    assert Path(artifacts["artifacts"]["wp13_run_json"]["path"]).is_file()
    for name, art in artifacts["artifacts"].items():
        assert Path(art["path"]).is_file()
        assert art["sha256"] == panel_load.sha256_file(art["path"])


def test_run_full_h30_uses_vol_weighted_outcome_not_raw_returns():
    """DEC-75 Entscheidung 1 (4) (DEC-87 (G): weekly sigma_w, ``h30_outcome_for_window`` now needs the
    ``day_count``): a hypothesis registered with
    ``outcome: vol_weighted`` must be judged on ``ic.vol_weighted_outcome_
    with_drag``'s output, not the raw next-week return -- verified by
    checking the ACTUAL array ``variant_window_payload`` receives differs
    from the raw return panel (a monkeypatch-style capture, mirroring the
    prelaunch SEAL tests' technique)."""
    seed, k, w = 3, 60, 60
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    returns = rng.normal(0, 0.03, size=(w, k_full))
    alive = np.ones((w, k_full), dtype=bool)
    vol_rv = np.abs(rng.normal(0.03, 0.01, size=(w, k_full))) + 1e-3

    day_count = np.full(returns.shape, 7, dtype=np.int64)     # DEC-87 (G): n_t valid daily returns per week
    weighted = run_mod.h30_outcome_for_window(returns, vol_rv, day_count)
    assert weighted.shape == returns.shape
    assert not np.allclose(weighted[1:-1], returns[1:-1], equal_nan=True)
    assert np.isnan(weighted[0]).all()               # no formation week -1


# ============================================================================
# DEC-76 Entscheidung 1 (b)/(c) / Task A item 3: null-calibration assertion
# ============================================================================

def _build_run_fixture_tree_large(tmp_path: Path):
    """Like :func:`_build_run_fixture_tree`, but with >= 10 SURVIVOR
    symbols (plus BTCUSDT) so every week clears ``ic.weekly_ic_series``'s
    ``min_universe=10`` floor and the DEC-76 null constants come out
    FINITE (the small 4-survivor fixture above is too thin for that --
    every week is NaN there, which is realistic for that fixture's OWN
    purpose but useless for a calibration-value comparison)."""
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    del_base = tmp_path / "panel_1d_delisted"
    del_manifest = del_base / "panel_manifest.sqlite"

    full_start, full_end = date(2021, 1, 1), date(2026, 6, 30)
    symbols = ["BTCUSDT"] + [f"SYM{i:02d}USDT" for i in range(11)]
    for i, sym in enumerate(symbols):
        _write_full_history(surv_base, surv_manifest, sym,
                             _closes(full_start, full_end, seed=i + 1), as_of_date=full_end)
    delist_date = date(2025, 2, 10)
    _write_full_history(del_base, del_manifest, "MMMUSDT",
                         _closes(full_start, delist_date, seed=99), as_of_date=delist_date)
    dd = delisted_panel.write_delisting_dates_json(del_base, {
        "MMMUSDT": {"delist_date": delist_date.isoformat(), "announcement_id": "ann-mmmusdt",
                    "source": "delisting_ms"}})

    as_of = date(2027, 1, 1)
    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2021, year_end=2026, as_of=as_of, delisting_dates_path=Path(dd["path"]))
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    return panel, weekly


def _registered_for_large_fixture() -> dict:
    ic_min_all = {v: 0.02 for v in characteristics.VARIANT_NAMES}
    return {
        "hypotheses": {"H-28": {"variant": "mom1", "direction": "positive"}},
        "windows": {
            "W1": {"start": "2024-07-01", "end": "2025-06-30", "ic_min_capped": ic_min_all,
                   "bounce_sigma_true": BOUNCE_SIGMA["W1"], "calibration": _window_calibration(0.05, 0.50)},
            "W2": {"start": "2025-07-01", "end": "2026-06-30", "ic_min_capped": ic_min_all,
                   "bounce_sigma_true": BOUNCE_SIGMA["W2"], "calibration": _window_calibration(0.06, 0.45)},
        },
        "beta_control": {"method": "ts_resid_8w", "beta_window_weeks": 8},   # DEC-77 Entscheidung 2
        "rules": {"seed": 53, "n_reps_bootstrap": 20, "n_reps_permutation": 20, "n_reps_factor_null": 30,
                  "n_sims_persistence": 20, "bounce_spread": BOUNCE_SPREAD},
    }


def test_run_full_null_calibration_report_present_and_matches_recomputation(tmp_path):
    """No frozen constants in the registered YAML (hand-built unit-test file, backward compatible): ``run_full``
    falls back to its OWN recomputed DEC-87 null constants (no assertion, flagged ``frozen_constants_complete:
    False``) and reports them under ``report["null_calibration"]``.

    DEC-87: the keys are ``ceiling_method_stress_*`` (A) and ``res_quantile_driftfree_*``/
    ``res_quantile_drifting_*`` (E) -- the latter now REALLY is the drift-0.002 null (until v5d the key
    ``res_quantile_drifting`` held the driftfree one)."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    report = run_mod.run_full(panel, weekly, registered)

    nc = report["null_calibration"]
    assert set(nc.keys()) == {"W1", "W2"}
    assert report["frozen_constants_complete"] is False
    for wn in ("W1", "W2"):
        assert nc[wn]["ceiling_method_stress_registered"] is None
        assert math.isfinite(nc[wn]["ceiling_method_stress_recomputed"])
        for v in characteristics.VARIANT_NAMES:
            assert math.isfinite(nc[wn]["res_quantile_drifting_recomputed"][v])
            assert math.isfinite(nc[wn]["res_quantile_driftfree_recomputed"][v])
    # the FALLBACK (no registered value) means the payload's own quantiles are exactly the recomputed
    # values (no frozen constant to prefer instead); the gate judges against the more extreme (E).
    h28 = report["results"]["H-28"]["payload"]["windows"]["W1"]
    q_free = nc["W1"]["res_quantile_driftfree_recomputed"]["mom1"]
    q_drift = nc["W1"]["res_quantile_drifting_recomputed"]["mom1"]
    assert h28["res_quantile_drifting"] == pytest.approx(q_drift)
    assert h28["res_quantile_driftfree"] == pytest.approx(q_free)
    assert h28["res_quantile_binding"] == pytest.approx(max(q_free, q_drift))      # positive: the larger one
    assert h28["selection_ceiling_mean_of_max"] == pytest.approx(nc["W1"]["ceiling_method_stress_recomputed"])


def test_run_full_calibration_block_derives_stress_null(tmp_path, monkeypatch):
    """DEC-87 (D) (was: a single global ``calibration`` block, DEC-78 Nachtrag): each window's
    ``windows.<W>.calibration.stress`` supplies THAT window's ``rho_f``/``beta_sd_calibrated`` to the null,
    READ DIRECTLY (no re-search) -- W1 and W2 carry different pairs here and the null of each window receives its
    own; echoed in the report's ``calibration_used_for_stress_null[W]``."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    registered["windows"]["W1"]["calibration"] = _window_calibration(0.10, 0.135)
    registered["windows"]["W2"]["calibration"] = _window_calibration(0.08, 0.20)
    seen: list[tuple] = []
    orig = nulls.beta_controlled_factor_null

    def spy(window_returns, *a, **kw):
        seen.append((kw["rho_f"], kw["beta_sd"], kw["drift_f"]))
        return orig(window_returns, *a, **kw)

    monkeypatch.setattr(nulls, "beta_controlled_factor_null", spy)
    report = run_mod.run_full(panel, weekly, registered)
    used = report["calibration_used_for_stress_null"]
    assert used["W1"]["rho_f"] == pytest.approx(0.10) and used["W1"]["beta_sd_calibrated"] == pytest.approx(0.135)
    assert used["W2"]["rho_f"] == pytest.approx(0.08) and used["W2"]["beta_sd_calibrated"] == pytest.approx(0.20)
    assert "registered.windows.W1.calibration.stress" in used["W1"]["source"]
    # two null cells per window (E): driftfree then drifting, each with the window's own pair
    assert seen == [(0.10, 0.135, 0.0), (0.10, 0.135, 0.002), (0.08, 0.20, 0.0), (0.08, 0.20, 0.002)]


def test_run_full_without_window_calibration_is_loud_fail(tmp_path):
    """DEC-87 (D) (formerly ``test_run_full_without_calibration_block_falls_back_to_old_stress_null``, which
    pinned the silent fallback to the refuted hardcoded stress null ``rho_f=0.2``, beta ~ U(0.5, 2.0)): a window
    without ``calibration.stress`` is a loud fail (C.14) -- no fallback, no verdict."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    del registered["windows"]["W2"]["calibration"]
    with pytest.raises(run_mod.RegisteredSchemaError, match="calibration.stress"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_without_calibration_block_falls_back_to_old_stress_null(tmp_path):
    """DEC-87: kept under its old id (it pinned the silent fallback to the refuted hardcoded stress null). The contract
    changed (DEC-87 (D)): no fallback, a loud fail -- see :func:`test_run_full_without_window_calibration_is_loud_fail`,
    which this id delegates to."""
    test_run_full_without_window_calibration_is_loud_fail(tmp_path)


def test_run_full_refuses_the_old_global_calibration_block_loudly(tmp_path):
    """DEC-87 (D)/C.14: the pre-DEC-87 GLOBAL ``calibration`` block (W1-sourced, applied to both windows) is
    refused with a message naming the per-window form, even when the per-window blocks are present."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    registered["calibration"] = {"sigma_f": 0.06, "stress": {"rho_f": 0.10, "beta_sd_calibrated": 0.135}}
    with pytest.raises(run_mod.RegisteredSchemaError, match="GLOBALEN 'calibration'"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_refuses_the_pre_dec87_ceiling_key_loudly(tmp_path):
    """DEC-87 (A): ``ceiling_driftfree_res`` (TS-residualisation ceiling, historical) is no longer a schema key;
    a stale file must not be silently read as "no frozen ceiling"."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    registered["windows"]["W1"]["ceiling_driftfree_res"] = 0.0496
    with pytest.raises(run_mod.RegisteredSchemaError, match="ceiling_method_stress"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_uses_frozen_registered_null_constants_within_tolerance(tmp_path):
    """A registered YAML that DOES carry ``ceiling_method_stress`` / ``res_quantile_driftfree`` /
    ``res_quantile_drifting`` (values within tolerance of what the run's own recomputation gets, deterministically
    -- same seed/panel/rules): ``run_full`` must NOT raise, and every payload must carry the FROZEN (registered)
    values, never the recomputed ones, even though here they happen to be numerically identical (DEC-87 (A)/(E);
    T5: the numbers that flow into the gate ARE the YAML's)."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    baseline = run_mod.run_full(panel, weekly, _registered_for_large_fixture())
    nc = baseline["null_calibration"]

    registered = _registered_for_large_fixture()
    for wn in ("W1", "W2"):
        registered["windows"][wn]["ceiling_method_stress"] = nc[wn]["ceiling_method_stress_recomputed"] * 1.05
        registered["windows"][wn]["res_quantile_driftfree"] = {
            v: q * 0.95 for v, q in nc[wn]["res_quantile_driftfree_recomputed"].items()}
        registered["windows"][wn]["res_quantile_drifting"] = {
            v: q * 1.05 for v, q in nc[wn]["res_quantile_drifting_recomputed"].items()}

    report = run_mod.run_full(panel, weekly, registered)      # +-5 % is inside +-10 %: must not raise
    assert report["frozen_constants_complete"] is True
    pin = run_mod.registered_constants_pin(registered)
    for wn in ("W1", "W2"):
        w = report["results"]["H-28"]["payload"]["windows"][wn]
        assert w["selection_ceiling_mean_of_max"] == pin[wn]["ceiling_method_stress"]       # bit-exact: frozen, not recomputed
        assert w["res_quantile_driftfree"] == pin[wn]["res_quantile_driftfree"]["mom1"]
        assert w["res_quantile_drifting"] == pin[wn]["res_quantile_drifting"]["mom1"]
        assert w["ic_min_capped"] == pin[wn]["ic_min_capped"]["mom1"]
        assert w["res_quantile_binding"] == max(w["res_quantile_driftfree"], w["res_quantile_drifting"])


def test_run_full_raises_null_calibration_error_when_registered_has_drifted(tmp_path):
    """A registered constant that has drifted far (>10%) from what the
    run's own recomputation gets is a LOUD FAIL (C.14): the whole run
    aborts with ``NullCalibrationError``, BEFORE any hypothesis gets a
    verdict -- DEC-76 Task A item 3, verbatim (DEC-87 (A): the frozen
    ceiling is ``ceiling_method_stress``)."""
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["windows"]["W1"]["ceiling_method_stress"] = 999.0    # wildly stale
    with pytest.raises(run_mod.NullCalibrationError, match="Null-Kalibrierung weicht ab"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_raises_null_calibration_error_on_stale_per_variant_quantile(tmp_path):
    """DEC-87 (E): BOTH frozen quantile sets are re-checked at +-10 % -- the driftfree and the drifting one."""
    panel, weekly = _build_run_fixture_tree(tmp_path)
    for key in ("res_quantile_drifting", "res_quantile_driftfree"):
        registered = _registered_for_fixture()
        registered["windows"]["W1"][key] = {v: 999.0 for v in characteristics.VARIANT_NAMES}
        with pytest.raises(run_mod.NullCalibrationError, match=f"{key}"):
            run_mod.run_full(panel, weekly, registered)


def test_assert_null_calibration_pure_function():
    run_mod.assert_null_calibration(0.05, None, label="no-op")            # registered absent -> no-op
    run_mod.assert_null_calibration(0.05, 0.052, label="within tol")      # ~4% off, within +/-10%
    with pytest.raises(run_mod.NullCalibrationError):
        run_mod.assert_null_calibration(0.05, 0.10, label="drifted")      # 100% off
    run_mod.assert_null_calibration(1e-6, 0.0, label="zero, abs tol")     # registered==0 -> absolute tolerance
    with pytest.raises(run_mod.NullCalibrationError):
        run_mod.assert_null_calibration(0.01, 0.0, label="zero, too far")


# ============================================================================
# DEC-76 Task A item 4: --emit-registered-template
# ============================================================================

def _tiny_prelaunch_artifact(tmp_path):
    """A real (tiny) ``--prelaunch`` artifact on the >= 10-survivor fixture tree; the probes are kept small and
    the Gegenprobe knobs relaxed exactly as the CLI e2e test in ``test_wp13_xsec.py`` does (statistically
    underpowered fixture -- the wiring is under test, not the calibration quality)."""
    from bybit_edge.research.wp13_xsec import prelaunch as prelaunch_mod
    from tests.unit.test_wp13_xsec import _build_prelaunch_fixture_tree

    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    fp = {"union_range_fingerprint": "ab" * 32, "delisting_dates_sha256": "cd" * 32}
    prelaunch_report = prelaunch_mod.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_sims=5, n_reps_factor_null=5, n_reps_beta_control_study=5, n_reps_beta_control_winner=5, seed=53,
        gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9, gegenprobe_market_check=False,
        calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=8,
        data_fingerprints=fp)
    artifacts = prelaunch_mod.write_prelaunch_artifacts(tmp_path / "prelaunch_out", prelaunch_report)
    return prelaunch_report, artifacts["artifacts"]["wp13a_prelaunch_json"]["path"], fp


def test_cli_emit_registered_template_writes_yaml_skeleton_from_prelaunch_artifact(tmp_path):
    """DEC-87 contract of the emitted skeleton (was the DEC-76/78 one with a GLOBAL W1 ``calibration`` block, one
    entry per hypothesis, ``ceiling_driftfree_res``/``res_quantile_drifting`` from the TS-driftfree null and
    ``rules.n_reps >= 1000``): per-window ``calibration.{measured,stress,zero}`` taken from THAT window's study,
    ``ceiling_method_stress``/``res_quantile_driftfree``/``res_quantile_drifting`` from the winner section, seven
    ``H-xx_<variant>`` entries (``vol_beta`` locked), ``beta_control.method`` filled ONLY from a confirmed
    recommendation, ``data_fingerprints``, and ``rules.n_reps`` = the replicates that froze the constants."""
    prelaunch_report, prelaunch_json, fp = _tiny_prelaunch_artifact(tmp_path)

    out_yaml = tmp_path / "registered_template.yaml"
    rc = WP13.cmd_emit_registered_template(prelaunch_json, str(out_yaml))
    assert rc == 0
    assert out_yaml.is_file()

    loaded = run_mod.load_registered_yaml(out_yaml)     # round-trips through the real YAML loader
    hyps = loaded["hypotheses"]
    assert list(hyps) == ["H-28_mom1", "H-28_mom2", "H-28_mom4", "H-29_rev_gap",
                          "H-30_vol_rv", "H-30_vol_max", "H-30_vol_beta"]          # DEC-87 (J)
    assert {run_mod.hypothesis_group(k, v) for k, v in hyps.items()} == {"H-28", "H-29", "H-30"}
    assert all(hyps[k]["outcome"] == "vol_weighted" for k in hyps if k.startswith("H-30"))
    assert hyps["H-30_vol_beta"]["status"] == "gl012_pre_run" and "C.4" in hyps["H-30_vol_beta"]["reason"]   # (H)
    for wn in ("W1", "W2"):
        wcfg = loaded["windows"][wn]
        assert set(wcfg["ic_min_capped"].keys()) == set(characteristics.VARIANT_NAMES)
        assert set(wcfg["calibration"]) == {"measured", "stress", "zero"}                 # DEC-87 (D), per window
        study = prelaunch_report["windows"][wn]["beta_control_method_study"]["calibrations"]
        for cal in ("measured", "stress", "zero"):
            blk = wcfg["calibration"][cal]
            assert set(blk) == {"rho_f", "beta_sd_calibrated", "target_factor_share"}
            assert blk["rho_f"] == study[cal]["rho_f"] and blk["beta_sd_calibrated"] == study[cal]["beta_sd_calibrated"]
        assert "ceiling_driftfree_res" not in wcfg and "ceiling_method_stress" in wcfg
        assert set(wcfg["res_quantile_driftfree"]) == set(characteristics.VARIANT_NAMES) == set(wcfg["res_quantile_drifting"])
    assert loaded["rules"]["seed"] == 53
    assert loaded["rules"]["n_reps"] == prelaunch_report["n_reps_beta_control_winner"] == 5      # the freezing replicates
    assert loaded["data_fingerprints"] == fp
    # DEC-89 E1/E3 (2): the real prelaunch sections flow into the template (spread from the WP-7 census, D10 / 1e4)
    assert loaded["rules"]["bounce_spread"] == 0.003621 and loaded["rules"]["block_len"] == 4 and loaded["rules"]["level"] == 0.9936
    for wn in ("W1", "W2"):
        pre = prelaunch_report["windows"][wn]
        assert loaded["windows"][wn]["bounce_sigma_true"] == pre["factor_preserving_null"]["driftfree"]["sigma_e_median_symbol_weekly"]
        assert loaded["windows"][wn]["survivorship"] == {
            k: pre["survivorship_fixture"][k] for k in ("mom1_diff_in_ic_min_units", "rev_gap_diff_in_ic_min_units")}
        # DEC-89 E2 Nachtrag: the calibrated null world's scales (study sigma_f / sigma_e_used) for the positive control
        assert loaded["windows"][wn]["null_scales"] == {
            "sigma_f": pre["beta_control_method_study"]["sigma_f"],
            "sigma_e_used": pre["beta_control_method_study"]["sigma_e_used"]}
    # the emitted file passes the schema check (modulo a possibly empty method on this tiny fixture) ...
    run_mod.validate_registered(loaded)
    # ... and beta_control comes from the CONFIRMED recommendation only (empty if none was confirmed)
    conf = prelaunch_report["beta_control_confirmation"]
    if conf["confirmed_method"]:
        assert loaded["beta_control"] == {"method": conf["confirmed_method"],
                                          "beta_window_weeks": ic.beta_control_trail_weeks(conf["confirmed_method"])}
        for wn in ("W1", "W2"):
            fz = prelaunch_report["windows"][wn]["frozen_null_constants"]
            assert loaded["windows"][wn]["ceiling_method_stress"] == fz["ceiling_method_stress"]
            assert loaded["windows"][wn]["res_quantile_driftfree"] == fz["res_quantile_driftfree"]
            assert loaded["windows"][wn]["res_quantile_drifting"] == fz["res_quantile_drifting"]
    else:
        assert loaded["beta_control"] == {"method": "", "beta_window_weeks": None}
        with pytest.raises(ValueError, match="beta_control"):
            run_mod.run_full({"symbols": []}, {"weeks": [], "returns": None, "alive": None}, loaded)


def test_cli_emit_registered_template_beta_control_filled_from_confirmed_method_only(tmp_path):
    """DEC-87: ``--emit-registered-template`` fills ``beta_control.method`` from the artifact's
    ``beta_control_confirmation`` and leaves it empty when "keine Methode bestaetigt" (hand-built artifact so both
    branches are exercised deterministically); the frozen constants flow from ``frozen_null_constants``."""
    base = {
        "variants": list(characteristics.VARIANT_NAMES), "n_reps_beta_control_winner": 1000,
        "data_fingerprints": {"union_range_fingerprint": "11" * 32, "delisting_dates_sha256": "22" * 32},
        "windows": {wn: {
            "available": True, "start": s0, "end": e0,
            "noise_floor_and_threshold": {"ic_min_capped_per_variant": {v: 0.02 for v in characteristics.VARIANT_NAMES},
                                          "w_judged": 52},
            "beta_control_method_study": {"calibrations": {
                cal: {"rho_f": 0.05 * k, "beta_sd_calibrated": 0.5 * k, "target_factor_share": 0.03 * k}
                for cal, k in (("measured", 1), ("stress", 2), ("zero", 1))}},
            "frozen_null_constants": {
                "ceiling_method_stress": 0.0081,
                "res_quantile_driftfree": {v: 0.02 for v in characteristics.VARIANT_NAMES},
                "res_quantile_drifting": {v: 0.021 for v in characteristics.VARIANT_NAMES}},
            # DEC-89 E1/E3 (2): the Vorlauf sections the template copies the bounce sigma and the survivorship label from
            "factor_preserving_null": {"driftfree": {"sigma_e_median_symbol_weekly": BOUNCE_SIGMA[wn]}},
            "survivorship_fixture": {"mom1_diff_in_ic_min_units": -0.198 if wn == "W1" else -0.438,
                                     "rev_gap_diff_in_ic_min_units": -0.189 if wn == "W1" else -0.579},
        } for wn, s0, e0 in (("W1", "2024-07-01", "2025-06-30"), ("W2", "2025-07-01", "2026-06-30"))},
        "h30_feasibility_weekly_units": {"spread_d10_minus_d1_over_kante": 2.8, "se_drag_over_kante": 0.18, "feasible": False},
    }
    confirmed = dict(base, beta_control_confirmation={"confirmed_method": "fm_neutral_8w", "note": "bestaetigt"})
    p1 = tmp_path / "confirmed.json"
    p1.write_text(__import__("json").dumps(confirmed), encoding="utf-8")
    assert WP13.cmd_emit_registered_template(str(p1), str(tmp_path / "t1.yaml")) == 0
    y1 = run_mod.load_registered_yaml(tmp_path / "t1.yaml")
    assert y1["beta_control"] == {"method": "fm_neutral_8w", "beta_window_weeks": 8}
    assert y1["windows"]["W1"]["ceiling_method_stress"] == 0.0081
    assert y1["windows"]["W2"]["res_quantile_drifting"]["vol_rv"] == 0.021
    assert y1["windows"]["W1"]["calibration"]["stress"]["rho_f"] == 0.1
    # DEC-89 E1/E3 (2): bounce spread from the WP-7 census (D10 36.21 bp -> 0.003621), sigma_true + survivorship per window
    assert y1["rules"]["bounce_spread"] == BOUNCE_SPREAD
    assert y1["windows"]["W1"]["bounce_sigma_true"] == BOUNCE_SIGMA["W1"] and y1["windows"]["W2"]["bounce_sigma_true"] == BOUNCE_SIGMA["W2"]
    assert y1["windows"]["W2"]["survivorship"] == {"mom1_diff_in_ic_min_units": -0.438, "rev_gap_diff_in_ic_min_units": -0.579}
    # (G) mechanical H-30 lock: Spread/Kante 2.8 > 0.5 -> all three H-30 entries gl012_pre_run, H-28/H-29 untouched
    for k, h in y1["hypotheses"].items():
        assert (h.get("status") == "gl012_pre_run") == k.startswith("H-30")
    assert "Wocheneinheiten" in y1["hypotheses"]["H-30_vol_rv"]["reason"]
    run_mod.validate_registered(y1)

    none_confirmed = dict(base, beta_control_confirmation={"confirmed_method": None, "note": "keine Methode bestaetigt: x"})
    p2 = tmp_path / "none.json"
    p2.write_text(__import__("json").dumps(none_confirmed), encoding="utf-8")
    assert WP13.cmd_emit_registered_template(str(p2), str(tmp_path / "t2.yaml")) == 0
    y2 = run_mod.load_registered_yaml(tmp_path / "t2.yaml")
    assert y2["beta_control"] == {"method": "", "beta_window_weeks": None}
    assert "WARNUNG: KEINE Methode bestaetigt" in (tmp_path / "t2.yaml").read_text(encoding="utf-8")


def test_cli_emit_registered_template_missing_input_file_is_loud_fail(tmp_path):
    rc = WP13.cmd_emit_registered_template(str(tmp_path / "nonexistent.json"), str(tmp_path / "out.yaml"))
    assert rc == 1
    assert not (tmp_path / "out.yaml").exists()


def test_run_full_never_writes_under_data_harvest(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    report = run_mod.run_full(panel, weekly, registered)
    with pytest.raises(ValueError):
        run_mod.write_run_artifacts(Path("data/harvest/wp13_run_should_not_write_here"), report)


# ============================================================================
# DEC-77 Entscheidung 2 -- Vorlauf v4: registered beta_control (run.py)
# ============================================================================

def test_run_full_missing_beta_control_is_loud_fail(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    del registered["beta_control"]
    with pytest.raises(ValueError, match="beta_control"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_empty_beta_control_method_is_loud_fail(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["beta_control"] = {"method": "", "beta_window_weeks": None}
    with pytest.raises(ValueError, match="beta_control"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_unknown_beta_control_method_is_loud_fail(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["beta_control"] = {"method": "not_a_real_method", "beta_window_weeks": 8}
    with pytest.raises(ValueError):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_mismatched_beta_window_weeks_is_loud_fail(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["beta_control"] = {"method": "ts_resid_8w", "beta_window_weeks": 13}   # mismatch
    with pytest.raises(ValueError, match="beta_window_weeks"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_none_beta_control_method_needs_no_window(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["beta_control"] = {"method": "none", "beta_window_weeks": None}
    report = run_mod.run_full(panel, weekly, registered)     # must not raise
    assert report["beta_control"] == {"method": "none", "beta_window_weeks": None}
    for hyp, res in report["results"].items():
        for wn in ("W1", "W2"):
            assert res["payload"]["windows"][wn]["beta_control_method"] == "none"
            assert res["payload"]["windows"][wn]["residualized_mean_ic"] is None


def test_run_full_uses_registered_beta_control_method_end_to_end(tmp_path):
    """DEC-77 Entscheidung 2: run_full applies EXACTLY the registered
    method -- the payload carries it, and a non-'none' method reports a
    finite coverage fraction on the large (>= 10 survivor) fixture."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    registered["beta_control"] = {"method": "fm_neutral_13w", "beta_window_weeks": 13}
    report = run_mod.run_full(panel, weekly, registered)
    assert report["beta_control"] == {"method": "fm_neutral_13w", "beta_window_weeks": 13}
    w1 = report["results"]["H-28"]["payload"]["windows"]["W1"]
    assert w1["beta_control_method"] == "fm_neutral_13w"
    if w1["beta_control_coverage"] is not None:
        assert 0.0 <= w1["beta_control_coverage"]["coverage_fraction"] <= 1.0


def test_dec85_run_full_requires_returns_valid_loud(tmp_path):
    """DEC-85 (iii): the run mode needs ``weekly["returns_valid"]`` (real PIT betas and the
    null's sigma_f/sigma_e are estimated on ``returns_est``) -- a weekly dict without it is a
    loud ValueError, never a silent fall back to the zero-filled array."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    weekly_old = {k: v for k, v in weekly.items() if k != "returns_valid"}
    with pytest.raises(ValueError, match="returns_valid"):
        run_mod.run_full(panel, weekly_old, _registered_for_large_fixture())


def test_dec85_run_full_estimates_real_betas_and_null_scalars_on_returns_est(tmp_path, monkeypatch):
    """DEC-85 (iii), run mode: the real PIT beta handed to ``ic.apply_beta_control`` and the
    ``returns`` array the null's sigma_f/sigma_e are measured on are built from
    ``returns_est`` (NaN where a symbol did not trade); the IC outcome array stays the
    zero-filled ``returns``. One alive symbol is made silent for 30 weeks of W1."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    returns, valid = weekly["returns"].copy(), weekly["returns_valid"].copy()
    j_silent = panel["symbols"].index("SYM03USDT")
    lo_w1 = weekly["weeks"].index("2024-07-01")
    gap = slice(lo_w1 + 5, lo_w1 + 35)
    assert weekly["alive"][gap, j_silent].all() and valid[gap, j_silent].all()
    valid[gap, j_silent] = False
    returns[gap, j_silent] = 0.0
    weekly_mod = dict(weekly, returns=returns, returns_valid=valid)
    returns_est = np.where(valid, returns, np.nan)

    seen_hyp: list[dict] = []
    seen_null: list[np.ndarray] = []
    orig_hyp, orig_null = run_mod.run_hypothesis, nulls.beta_controlled_factor_null

    def spy_hyp(*a, **kw):
        seen_hyp.append({"returns_by_window": a[4], "beta_pit": kw["beta_control_pit_by_window"]})
        return orig_hyp(*a, **kw)

    def spy_null(window_returns, *a, **kw):
        seen_null.append(window_returns)
        return orig_null(window_returns, *a, **kw)

    monkeypatch.setattr(run_mod, "run_hypothesis", spy_hyp)
    monkeypatch.setattr(nulls, "beta_controlled_factor_null", spy_null)
    registered = _registered_for_large_fixture()
    registered["beta_control"] = {"method": "fm_neutral_13w", "beta_window_weeks": 13}
    run_mod.run_full(panel, weekly_mod, registered)

    beta_est = characteristics.beta_characteristic(returns_est, panel["symbols"], trail_win=13, min_weeks=13)
    beta_zero = characteristics.beta_characteristic(returns, panel["symbols"], trail_win=13, min_weeks=13)
    # DEC-87 (E): two null cells (driftfree + drifting) per window -> W1, W1, W2, W2
    assert len(seen_hyp) == 1 and len(seen_null) == 4
    lo, hi = lo_w1, lo_w1 + len(seen_hyp[0]["beta_pit"]["W1"])
    assert np.array_equal(seen_hyp[0]["beta_pit"]["W1"], beta_est[lo:hi], equal_nan=True)
    assert np.isnan(seen_hyp[0]["beta_pit"]["W1"][5:35 + 12, j_silent]).all()   # window + 12 following weeks
    assert np.isfinite(beta_zero[lo + 17:lo + 40, j_silent]).all()               # zero-filled would be finite
    assert np.array_equal(seen_null[0], returns_est[lo:hi], equal_nan=True)
    assert np.array_equal(seen_null[1], returns_est[lo:hi], equal_nan=True)
    # the IC outcome array is untouched (zero fill, no NaN for the silent symbol)
    assert np.array_equal(seen_hyp[0]["returns_by_window"]["W1"], returns[lo:hi])


# ============================================================================
# DEC-77 Entscheidung 2 -- Vorlauf v4: variant_window_payload's beta_control
# dispatch (backward-compatible default None)
# ============================================================================

def test_variant_window_payload_beta_control_method_explicit_dispatch():
    seed, k, w = 5, 60, 40
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    alive = np.ones((w, k_full), dtype=bool)
    beta_13w = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT",
                                                     trail_win=13, min_weeks=13)
    payload = run_mod.variant_window_payload(
        characteristic, returns, alive, symbols, variant="mom1", direction="positive",
        ic_min_capped=0.02, w_judged=w - 1, floor=0.05, selection_ceiling_mean_of_max=0.01,
        n_reps_bootstrap=20, n_reps_permutation=20, seed=53,
        beta_control_method="ts_resid_13w", beta_control_pit=beta_13w)
    assert payload["beta_control_method"] == "ts_resid_13w"
    assert payload["residualized_mean_ic"] is not None and math.isfinite(payload["residualized_mean_ic"])
    assert payload["beta_control_coverage"] is not None


def test_variant_window_payload_beta_control_method_none_disables_residualization():
    seed, k, w = 5, 40, 30
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    alive = np.ones((w, k_full), dtype=bool)
    payload = run_mod.variant_window_payload(
        characteristic, returns, alive, symbols, variant="mom1", direction="positive",
        ic_min_capped=0.02, w_judged=w - 1, floor=0.05, selection_ceiling_mean_of_max=0.01,
        n_reps_bootstrap=20, n_reps_permutation=20, seed=53, beta_control_method="none")
    assert payload["residualized_mean_ic"] is None
    assert payload["beta_control_coverage"] is None


def test_variant_window_payload_default_none_method_is_backward_compatible():
    """Leaving beta_control_method at its default None must give EXACTLY
    the pre-DEC-77 behaviour: residualisation via beta_8w_pit +
    ic.residualize_outcome directly."""
    seed, k, w = 5, 60, 40
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    alive = np.ones((w, k_full), dtype=bool)
    beta_8w = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    payload = run_mod.variant_window_payload(
        characteristic, returns, alive, symbols, variant="mom1", direction="positive",
        ic_min_capped=0.02, w_judged=w - 1, floor=0.05, selection_ceiling_mean_of_max=0.01,
        beta_8w_pit=beta_8w, n_reps_bootstrap=20, n_reps_permutation=20, seed=53)
    r_btc = returns[:, symbols.index("BTCUSDT")]
    expected_resid = ic.residualize_outcome(returns, beta_8w, r_btc)
    expected_mean_ic = ic.weekly_ic_series(characteristic, expected_resid, alive,
                                            convention="close_at_last")["mean_ic"]
    assert payload["residualized_mean_ic"] == pytest.approx(expected_mean_ic, nan_ok=True)
    assert payload["beta_control_method"] is None
    assert payload["beta_control_coverage"] is None


# ============================================================================
# DEC-87 (Drittfassung H-28..H-30): run mode -- entries, locks, BH, fingerprints, Gate (5), T1-T7
# ============================================================================

import copy  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

import yaml  # noqa: E402

from bybit_edge.research.wp13_xsec import prelaunch as prelaunch_module  # noqa: E402
from tests.unit.test_wp13_xsec import _build_prelaunch_fixture_tree, _ns_prelaunch, _weekly_daily_panel  # noqa: E402


def _registered_dec87_large() -> dict:
    """The seven-entry DEC-87 shape on the >= 10-survivor fixture: computed entries (mom1, rev_gap, vol_rv), two
    locked ones (mom2: power, vol_beta: C.4), registered method ``fm_neutral_8w`` (the Drittfassung's), small reps."""
    reg = _registered_for_large_fixture()
    reg["hypotheses"] = {
        "H-28_mom1": {"hypothesis": "H-28", "variant": "mom1", "direction": "positive"},
        "H-28_mom2": {"hypothesis": "H-28", "variant": "mom2", "direction": "positive",
                      "status": "gl012_pre_run", "reason": "MDE80 > IC_prior (Test, DEC-87 (F))"},
        "H-29_rev_gap": {"hypothesis": "H-29", "variant": "rev_gap", "direction": "negative"},
        "H-30_vol_rv": {"hypothesis": "H-30", "variant": "vol_rv", "direction": "negative", "outcome": "vol_weighted"},
        "H-30_vol_beta": {"hypothesis": "H-30", "variant": "vol_beta", "direction": "negative",
                          "outcome": "vol_weighted", "status": "gl012_pre_run",
                          "reason": "strukturell durch die registrierte Beta-Kontrolle neutralisiert (C.4)"},
    }
    reg["windows"]["L"] = {"start": "2021-03-01", "end": "2024-06-30"}        # descriptive/sealed, never judged
    reg["beta_control"] = {"method": "fm_neutral_8w", "beta_window_weeks": 8}
    reg["rules"] = {"seed": 53, "n_reps": 12, "n_reps_bootstrap": 20, "n_reps_permutation": 20,
                    "n_sims_persistence": 20, "bounce_spread": BOUNCE_SPREAD}
    return reg


@pytest.fixture(scope="module")
def dec87_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dec87_large")
    panel, weekly = _build_run_fixture_tree_large(tmp)
    registered = _registered_dec87_large()
    report = run_mod.run_full(panel, weekly, registered, observed_fingerprints=None)
    return panel, weekly, registered, report


# ---- entries, locks, aggregation, BH -------------------------------------------

def test_dec87_entries_locked_variants_are_not_computed_and_count_with_p_one(dec87_run):
    """DEC-87 (J): seven-variant family; a ``status: gl012_pre_run`` entry is NOT computed (no payload), carries the
    GL-012 label with the registered reason, and counts with p = 1 in a BH family whose denominator stays 7."""
    _panel, _weekly, registered, report = dec87_run
    assert set(report["results"]) == set(registered["hypotheses"])
    for entry_id in ("H-28_mom2", "H-30_vol_beta"):
        res = report["results"][entry_id]
        assert res["computed"] is False and res["payload"] is None
        assert res["verdict"]["verdict"] == "DROP" and res["verdict"]["gl012_pre_run"] is True
        assert "GL-012 vorab" in res["verdict"]["labels"][0] and registered["hypotheses"][entry_id]["reason"] in res["verdict"]["labels"][0]
    for entry_id in ("H-28_mom1", "H-29_rev_gap", "H-30_vol_rv"):
        assert report["results"][entry_id]["computed"] is True and report["results"][entry_id]["payload"] is not None
    assert report["bh"]["m"] == 7                                            # fixed denominator, 2 locked + 2 never registered
    hv = report["hypothesis_verdicts"]
    assert hv["H-28"]["variants_locked"] == ["mom2"] and hv["H-30"]["variants_locked"] == ["vol_beta"]
    assert set(hv) == {"H-28", "H-29", "H-30"} and hv["H-28"]["entries"] == ["H-28_mom1", "H-28_mom2"]
    # the payload and the verdict of a computed entry name the HYPOTHESIS, not the entry id
    assert report["results"]["H-28_mom1"]["payload"]["hypothesis"] == "H-28"


def test_dec87_benjamini_hochberg_denominator_is_fixed_at_seven():
    """DEC-87 (J): BH ``m`` is the family size K = 7 even when only some variants are computed -- the missing ones
    (locked / never run) count with p = 1, so a lone small p-value must clear ``rank/7 * alpha``, not ``rank/1 * alpha``."""
    p = {"mom1": 0.02}                                           # one computed variant, six more at p = 1
    res = run_mod.benjamini_hochberg(p, alpha=0.10)
    assert res["m"] == 7 and res["reject"]["mom1"] is False        # 0.02 > 1/7 * 0.10 = 0.0143
    assert run_mod.benjamini_hochberg({"mom1": 0.01}, alpha=0.10)["reject"]["mom1"] is True
    # the pre-DEC-87 behaviour (m = number of finite items) would have rejected: pinned for contrast
    assert run_mod.benjamini_hochberg(p, alpha=0.10, m_total=1)["reject"]["mom1"] is True
    nan_p = run_mod.benjamini_hochberg({"mom1": 0.001, "mom2": float("nan")}, alpha=0.10)
    assert nan_p["m"] == 7 and nan_p["reject"] == {"mom1": True, "mom2": False}


def test_dec87_hypothesis_is_pass_iff_at_least_one_variant_passes():
    """DEC-87 (J): aggregation by hypothesis; every variant remains individually reported."""
    def res(group, variant, verdict, computed=True, reason=None):
        return {"hypothesis": group, "variant": variant, "computed": computed, "verdict": {"verdict": verdict},
                "reason": reason}
    agg = run_mod.aggregate_hypotheses({
        "H-28_mom1": res("H-28", "mom1", "DROP"), "H-28_mom2": res("H-28", "mom2", "PASS"),
        "H-28_mom4": res("H-28", "mom4", "DROP", computed=False, reason="MDE80 > IC_prior"),
        "H-29_rev_gap": res("H-29", "rev_gap", "DROP"),
        "H-30_vol_rv": res("H-30", "vol_rv", "DROP", computed=False, reason="Feasibility")})
    assert agg["H-28"]["verdict"] == "PASS" and agg["H-28"]["variants_pass"] == ["mom2"]
    assert agg["H-28"]["variants_locked"] == ["mom4"] and agg["H-28"]["label"].startswith("vorlaeufig bis F-WEEK")
    assert agg["H-29"]["verdict"] == "DROP" and agg["H-29"]["label"] is None
    # DEC-89 (E3 (3)): a hypothesis whose variants are ALL locked is "GL-012 vor dem Lauf" with the reasons, not "DROP"
    assert agg["H-30"]["variants_locked"] == ["vol_rv"]
    assert agg["H-30"]["verdict"] == run_mod.GL012_PRE_RUN_VERDICT == "GL-012 vor dem Lauf"
    assert agg["H-30"]["reasons"] == {"vol_rv": "Feasibility"} and "Feasibility" in agg["H-30"]["label"]


def test_dec87_hypothesis_group_from_id_prefix_explicit_field_or_legacy_id():
    assert run_mod.hypothesis_group("H-28_mom1", {}) == "H-28"
    assert run_mod.hypothesis_group("H-30_vol_beta", {"hypothesis": "H-30"}) == "H-30"
    assert run_mod.hypothesis_group("H-29", {}) == "H-29"                 # pre-DEC-87 one-entry shape
    assert run_mod.hypothesis_group("custom", {"hypothesis": "H-99"}) == "H-99"


@pytest.mark.parametrize("mutate, message", [
    (lambda r: r["hypotheses"]["H-28_mom1"].update(variant="momX"), "unbekannt"),
    (lambda r: r["hypotheses"]["H-28_mom1"].update(direction="up"), "direction"),
    (lambda r: r["hypotheses"]["H-28_mom1"].update(status="dropped"), "status"),
    (lambda r: r["hypotheses"]["H-28_mom2"].pop("reason"), "ohne 'reason'"),
    (lambda r: r["hypotheses"]["H-30_vol_rv"].pop("outcome"), "vol_weighted"),
    (lambda r: r["hypotheses"].update({"H-28_mom1b": {"hypothesis": "H-28", "variant": "mom1", "direction": "positive"}}),
     "doppelt"),
    (lambda r: r["windows"]["W2"]["ic_min_capped"].pop("mom1"), "ic_min_capped"),
    (lambda r: r["windows"]["W1"]["calibration"]["stress"].update(beta_sd_calibrated=float("nan")), "calibration.stress"),
    (lambda r: r["windows"].pop("W2"), "windows.W2"),
])
def test_dec87_validate_registered_loud_failures(mutate, message):
    """DEC-87 (C.14): the registered schema is validated before any panel arithmetic."""
    reg = _registered_dec87_large()
    run_mod.validate_registered(reg)                              # the baseline is valid
    mutate(reg)
    with pytest.raises(run_mod.RegisteredSchemaError, match=message):
        run_mod.validate_registered(reg)


def test_dec87_validate_registered_can_require_the_frozen_constants():
    """DEC-87 (A)/(E) + C.14: a REGISTERED run (the CLI) demands the three frozen null constants of every judged window
    -- finite ceiling and finite driftfree/drifting quantiles for all seven variants; hand-built unit-test files may
    omit them (the run then recomputes and says ``frozen_constants_complete: False``)."""
    reg = _registered_dec87_large()
    run_mod.validate_registered(reg)                                           # lenient default
    # DEC-89: a registered run additionally demands w_judged, the survivorship pair, block_len and level (tested on their
    # own in test_dec89_strict_preflight_*); they are complete here so this test stays about the frozen null constants
    reg["rules"].update(block_len=4, level=0.9936)
    for wn in ("W1", "W2"):
        reg["windows"][wn].update(w_judged=52, survivorship={"mom1_diff_in_ic_min_units": -0.2,
                                                             "rev_gap_diff_in_ic_min_units": -0.19})
    with pytest.raises(run_mod.RegisteredSchemaError, match="ceiling_method_stress"):
        run_mod.validate_registered(reg, require_frozen_constants=True)
    for wn in ("W1", "W2"):
        reg["windows"][wn]["ceiling_method_stress"] = 0.008
        reg["windows"][wn]["res_quantile_driftfree"] = {v: 0.02 for v in characteristics.VARIANT_NAMES}
        reg["windows"][wn]["res_quantile_drifting"] = {v: 0.021 for v in characteristics.VARIANT_NAMES}
    run_mod.validate_registered(reg, require_frozen_constants=True)            # complete -> fine
    reg["windows"]["W2"]["res_quantile_drifting"]["vol_max"] = None            # placeholder of an unconfirmed template
    with pytest.raises(run_mod.RegisteredSchemaError, match=r"res_quantile_drifting.*vol_max"):
        run_mod.validate_registered(reg, require_frozen_constants=True)
    reg["windows"]["W2"]["res_quantile_drifting"]["vol_max"] = float("nan")
    with pytest.raises(run_mod.RegisteredSchemaError, match="nicht endlich"):
        run_mod.validate_registered(reg, require_frozen_constants=True)
    run_mod.validate_registered(reg)                                           # NaN is not checked in lenient mode


# ---- Data fingerprints (V9) ----------------------------------------------------

def test_dec87_check_data_fingerprints_match_mismatch_and_missing():
    reg = {"data_fingerprints": {"union_range_fingerprint": "u" * 64, "delisting_dates_sha256": "d" * 64}}
    good = {"union_range_fingerprint": "u" * 64, "delisting_dates_sha256": "d" * 64, "union_range_detail": {}}
    run_mod.check_data_fingerprints(reg, good)                                      # match -> silent
    with pytest.raises(run_mod.DataFingerprintError, match="union_range_fingerprint weicht ab"):
        run_mod.check_data_fingerprints(reg, {**good, "union_range_fingerprint": "x" * 64})
    with pytest.raises(run_mod.DataFingerprintError, match="delisting_dates_sha256 weicht ab"):
        run_mod.check_data_fingerprints(reg, {**good, "delisting_dates_sha256": "x" * 64})
    with pytest.raises(run_mod.DataFingerprintError, match="fehlt data_fingerprints"):
        run_mod.check_data_fingerprints({}, good)
    with pytest.raises(run_mod.DataFingerprintError, match="nicht pruefbar"):
        run_mod.check_data_fingerprints(reg, None)
    with pytest.raises(run_mod.DataFingerprintError, match="data_fingerprints.delisting_dates_sha256 fehlt"):
        run_mod.check_data_fingerprints({"data_fingerprints": {"union_range_fingerprint": "u" * 64}}, good)


def test_dec87_run_full_checks_fingerprints_before_any_computation(tmp_path, monkeypatch):
    """DEC-87 V9: a fingerprint mismatch aborts BEFORE the null is simulated (no verdict, no compute)."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_dec87_large()
    registered["data_fingerprints"] = {"union_range_fingerprint": "u" * 64, "delisting_dates_sha256": "d" * 64}
    called = []
    monkeypatch.setattr(nulls, "run_configuration_null", lambda *a, **k: called.append(1))
    with pytest.raises(run_mod.DataFingerprintError):
        run_mod.run_full(panel, weekly, registered,
                         observed_fingerprints={"union_range_fingerprint": "z" * 64, "delisting_dates_sha256": "d" * 64})
    with pytest.raises(run_mod.DataFingerprintError, match="nicht pruefbar"):         # YAML has them, caller gave none
        run_mod.run_full(panel, weekly, registered)
    assert called == []


# ---- Gate (5) inside run_full for H-30 ------------------------------------------

def test_dec87_run_full_feeds_gate5_for_h30_only(dec87_run):
    """DEC-87 (V5): an H-30 entry carries the per-window Gate (5) median Spearman in its payload (finite on the
    >= 10-survivor fixture), other hypotheses do not."""
    _panel, _weekly, _registered, report = dec87_run
    h30 = report["results"]["H-30_vol_rv"]
    for wn in ("W1", "W2"):
        g5 = h30["payload"]["windows"][wn]["gate5_median_spearman"]
        assert isinstance(g5, float) and math.isfinite(g5)
        assert h30["verdict"]["per_window"][wn]["gate5_ok"] == (g5 < characteristics.GATE5_SPEARMAN_MAX)
        assert report["results"]["H-28_mom1"]["payload"]["windows"][wn]["gate5_median_spearman"] is None


def test_dec87_run_full_h29_gets_bounce_and_liquidity_in_every_window(dec87_run):
    """DEC-87 (I): the bounce fixture and the D1-exclusion sensitivity are computed in BOTH judged windows (until
    v5d: W1 only), as ``{window: value}`` dicts the gate reads per window."""
    _panel, _weekly, _registered, report = dec87_run
    p = report["results"]["H-29_rev_gap"]["payload"]
    assert set(p["bounce_ic"]) == {"W1", "W2"} and set(p["liquidity_ic_without_d1"]) == {"W1", "W2"}
    assert all(math.isfinite(v) for v in p["bounce_ic"].values())
    assert report["results"]["H-28_mom1"]["payload"]["bounce_ic"] is None


# ---- DEC-53 artifacts / fingerprint / T2 / T3 / T5 / T6 / T7 --------------------

def test_dec87_artifacts_contain_raw_and_residualized_series_and_generator_fingerprint(dec87_run, tmp_path):
    """DEC-53 / DEC-87 (V7): per computed entry and window the raw AND the residualised weekly IC series (CSV, sha256),
    bootstrap/permutation replicate fingerprints + seed, and a generator fingerprint (code hash, python/numpy,
    data fingerprints, parameters); locked entries have no series; the result carries every mandatory artifact."""
    _panel, _weekly, _registered, report = dec87_run
    obs = {"union_range_fingerprint": "u" * 64, "delisting_dates_sha256": "d" * 64}
    report = dict(copy.deepcopy(report), observed_fingerprints=obs, registered_sha256="r" * 64)
    out = tmp_path / "run_out"
    arts = run_mod.write_run_artifacts(out, report, require_data_fingerprints=True)["artifacts"]
    for eid in ("H-28_mom1", "H-29_rev_gap", "H-30_vol_rv"):
        for wn in ("W1", "W2"):
            assert f"wp13_run_{eid}_{wn}_ic_weekly.csv" in arts
            assert f"wp13_run_{eid}_{wn}_ic_weekly_residualized.csv" in arts          # the (3b) series, DEC-53 Pflicht
    assert not [n for n in arts if "mom2" in n or "vol_beta" in n]                       # locked: no series
    assert {"wp13_run_json", "wp13_run_fingerprint_json", "l_window_sealed_json"} <= set(arts)
    for art in arts.values():
        assert art["sha256"] == panel_load.sha256_file(art["path"])
    fp = json.loads(Path(arts["wp13_run_fingerprint_json"]["path"]).read_text(encoding="utf-8"))
    assert fp["seed"] == 53 and fp["code"]["bit_generator"] == "PCG64" and len(fp["code"]["code_sha256"]) == 64
    assert fp["data_fingerprints"] == obs and fp["registered_sha256"] == "r" * 64
    assert any(k.startswith("wp13_xsec/run.py") for k in fp["code"]["files"]) and "wp7_universe/panel_load.py" in " ".join(fp["code"]["files"])
    d = fp["draws"]["H-28_mom1/W1"]
    assert d["bootstrap_seed"] == 53 and d["permutation_seed"] == 53 and len(d["bootstrap_means_sha256"]) == 64
    assert len(d["permutation_draws_sha256"]) == 64 and d["bootstrap_n_reps"] == 20
    assert fp["parameters"]["rules"]["n_reps"] == 12 and fp["beta_control"]["method"] == "fm_neutral_8w"
    main = json.loads(Path(arts["wp13_run_json"]["path"]).read_text(encoding="utf-8"))
    assert main["hypothesis_verdicts"]["H-28"]["variants_locked"] == ["mom2"] and "_l_window_sealed" not in main
    # require_data_fingerprints is a hard requirement when asked for
    with pytest.raises(run_mod.RunArtifactError, match="ohne Daten-Fingerprints"):
        run_mod.write_run_artifacts(tmp_path / "run_out2", copy.deepcopy(dec87_run[3]), require_data_fingerprints=True)
    assert not (tmp_path / "run_out2" / "wp13_run.json").exists()                        # and then NO verdict file


def test_dec87_t2_determinism_n3_with_fingerprint(dec87_run, tmp_path):
    """T2: the full run is deterministic -- three runs on the same inputs give the same result fingerprint
    (sha256 of every payload/verdict/null re-computation) and byte-identical generator-fingerprint files
    (N >= 3; the first run is the module fixture's)."""
    panel, weekly, registered, report1 = dec87_run
    reports = [report1] + [run_mod.run_full(panel, weekly, copy.deepcopy(registered)) for _ in range(2)]
    fps = [run_mod.result_fingerprint(r) for r in reports]
    assert len(set(fps)) == 1 and len(fps[0]) == 64
    blobs = []
    for i, r in enumerate(reports):
        art = run_mod.write_run_artifacts(tmp_path / f"r{i}", copy.deepcopy(r))["artifacts"]
        blobs.append(Path(art["wp13_run_fingerprint_json"]["path"]).read_bytes())
    assert blobs[0] == blobs[1] == blobs[2]
    # a different seed gives a different fingerprint (the fingerprint has teeth)
    other = copy.deepcopy(registered)
    other["rules"]["seed"] = 54
    assert run_mod.result_fingerprint(run_mod.run_full(panel, weekly, other)) != fps[0]


def test_dec87_t3_no_checkpoints_artifact_round_trip_documented(dec87_run, tmp_path):
    """T3 (DEC-75 (7) 'Checkpoint-Round-Trip'): the run is a single pass that has NO checkpoint/resume state -- there is
    no API to round-trip (documented, DEC-87 V7). What persists is the artifact set, whose round trip is T7: reading it
    back reproduces the gate estimators. This test pins both statements, so adding a checkpoint later forces a real T3."""
    assert not [n for n in dir(run_mod) if "checkpoint" in n.lower() or "resume" in n.lower()]
    assert not [n for n in dir(WP13) if "checkpoint" in n.lower() or "resume" in n.lower()]
    out = tmp_path / "t3"
    run_mod.write_run_artifacts(out, copy.deepcopy(dec87_run[3]))
    info = run_mod.verify_run_artifacts(out, dec87_run[3])
    assert info["n_entry_windows_checked"] == 6 and info["result_sha256"] == run_mod.result_fingerprint(dec87_run[3])


def test_dec87_t5_constants_pin_the_yaml_values_flow_into_every_payload(tmp_path):
    """T5: the frozen constants ARE the registered YAML's -- IC_min, the ceiling, both quantile sets and the stress
    calibration pair, per window; the file's sha256 (the Startsperre pin) changes with any of them."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    reg = _registered_dec87_large()
    base = run_mod.run_full(panel, weekly, reg)
    nc = base["null_calibration"]
    for wn in ("W1", "W2"):
        reg["windows"][wn]["ceiling_method_stress"] = nc[wn]["ceiling_method_stress_recomputed"] * 1.03
        reg["windows"][wn]["res_quantile_driftfree"] = {v: q * 0.97 for v, q in nc[wn]["res_quantile_driftfree_recomputed"].items()}
        reg["windows"][wn]["res_quantile_drifting"] = {v: q * 1.03 for v, q in nc[wn]["res_quantile_drifting_recomputed"].items()}
    path = tmp_path / "registered.yaml"
    path.write_text(yaml.safe_dump(reg, sort_keys=False), encoding="utf-8")
    sha = run_mod.sha256_of_file(path)
    loaded = run_mod.load_registered_yaml(path)
    assert loaded == reg                                                # YAML round trip is exact for these numbers
    pin = run_mod.registered_constants_pin(loaded)
    report = run_mod.run_full(panel, weekly, loaded)
    assert report["frozen_constants_complete"] is True
    for eid in ("H-28_mom1", "H-29_rev_gap", "H-30_vol_rv"):
        v = report["results"][eid]["variant"]
        for wn in ("W1", "W2"):
            w = report["results"][eid]["payload"]["windows"][wn]
            assert w["ic_min_capped"] == pin[wn]["ic_min_capped"][v]
            assert w["selection_ceiling_mean_of_max"] == pin[wn]["ceiling_method_stress"]
            assert w["res_quantile_driftfree"] == pin[wn]["res_quantile_driftfree"][v]
            assert w["res_quantile_drifting"] == pin[wn]["res_quantile_drifting"][v]
            assert report["calibration_used_for_stress_null"][wn]["rho_f"] == pin[wn]["calibration_stress"]["rho_f"]
            assert report["calibration_used_for_stress_null"][wn]["beta_sd_calibrated"] == pin[wn]["calibration_stress"]["beta_sd_calibrated"]
    # any change of a pinned constant changes the file hash the run is locked to
    loaded["windows"]["W1"]["res_quantile_drifting"]["mom1"] += 1e-6
    path2 = tmp_path / "registered2.yaml"
    path2.write_text(yaml.safe_dump(loaded, sort_keys=False), encoding="utf-8")
    assert run_mod.sha256_of_file(path2) != sha


def test_dec87_t6_wp13_xsec_never_imports_the_legacy_package():
    """T6 legacy-import lock for ``wp13_xsec`` (DEC-75 (7), Verfassung): neither the package modules nor the runner
    script import ``_legacy_v1`` (statically, by AST, or dynamically via importlib strings), and importing the
    package pulls no ``_legacy_v1`` module into ``sys.modules`` (fresh interpreter)."""
    import ast
    pkg_dir = Path(run_mod.__file__).resolve().parent
    files = sorted(pkg_dir.glob("*.py")) + [Path(WP13.__file__).resolve()]
    assert len(files) >= 8
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
    src_root = Path(run_mod.__file__).resolve().parents[3]
    code = ("import sys; sys.path.insert(0, %r); import bybit_edge.research.wp13_xsec.run, "
            "bybit_edge.research.wp13_xsec.prelaunch; "
            "print(any('_legacy_v1' in m for m in sys.modules))" % str(src_root))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False"


def _corrupt_first_value(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i in range(1, len(lines)):
        cols = lines[i].split(",")
        if cols[1] != "nan":
            lines[i] = f"{cols[0]},{float(cols[1]) + 0.125!r}"
            break
    else:
        raise AssertionError(f"no finite value to corrupt in {path}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_dec87_t7_artifact_round_trip_reproduces_the_gate_estimators_bitwise(dec87_run, tmp_path):
    """T7: the written artifacts alone re-derive the gate estimators bit for bit -- mean IC, SE, the moving-block
    bootstrap bound AND replicate fingerprint, IC_res -- and ``verify_run_artifacts`` says so; every kind of damage
    (changed series, missing residualised series, missing fingerprint file, wrong result hash) is KEIN VERDIKT."""
    report = dec87_run[3]
    out = tmp_path / "t7"
    arts = run_mod.write_run_artifacts(out, copy.deepcopy(report))["artifacts"]
    for eid in ("H-28_mom1", "H-29_rev_gap", "H-30_vol_rv"):
        for wn in ("W1", "W2"):
            w = report["results"][eid]["payload"]["windows"][wn]
            raw = np.array(run_mod._read_series_csv(out / f"wp13_run_{eid}_{wn}_ic_weekly.csv"))
            assert np.array_equal(raw, np.array(w["ic_weekly"]), equal_nan=True)
            fin = raw[~np.isnan(raw)]
            assert float(fin.mean()) == w["mean_ic"]
            assert run_mod.se_of_mean_ic(raw, w["se_detail"]["floor"], w["se_detail"]["w_judged"])["se"] == w["se"]
            cd = w["ci_detail"]
            ci = run_mod.moving_block_bootstrap_ci(raw, direction=cd["direction"], block_size=4, n_reps=cd["n_reps"],
                                                    seed=cd["seed"], level=cd["level"])
            assert ci["ci_bound_toward_sign"] == w["ci_bound_toward_sign"] and ci["means_sha256"] == cd["means_sha256"]
            res = np.array(run_mod._read_series_csv(out / f"wp13_run_{eid}_{wn}_ic_weekly_residualized.csv"))
            assert float(res[~np.isnan(res)].mean()) == w["residualized_mean_ic"]
    assert run_mod.verify_run_artifacts(out, report)["n_entry_windows_checked"] == 6

    raw_csv = out / "wp13_run_H-28_mom1_W1_ic_weekly.csv"
    original = raw_csv.read_text(encoding="utf-8")
    _corrupt_first_value(raw_csv)
    with pytest.raises(run_mod.RunArtifactError, match="KEIN VERDIKT"):
        run_mod.verify_run_artifacts(out, report)
    raw_csv.write_text(original, encoding="utf-8")
    res_csv = out / "wp13_run_H-29_rev_gap_W2_ic_weekly_residualized.csv"
    res_text = res_csv.read_text(encoding="utf-8")
    res_csv.unlink()
    with pytest.raises(run_mod.RunArtifactError, match="residualisierte Wochenserie"):
        run_mod.verify_run_artifacts(out, report)
    res_csv.write_text(res_text, encoding="utf-8")
    _corrupt_first_value(res_csv)
    with pytest.raises(run_mod.RunArtifactError, match="KEIN VERDIKT"):
        run_mod.verify_run_artifacts(out, report)
    res_csv.write_text(res_text, encoding="utf-8")
    fp_path = out / "wp13_run_fingerprint.json"
    fp = json.loads(fp_path.read_text(encoding="utf-8"))
    fp["result_sha256"] = "0" * 64
    fp_path.write_text(json.dumps(fp), encoding="utf-8")
    with pytest.raises(run_mod.RunArtifactError, match="result_sha256"):
        run_mod.verify_run_artifacts(out, report)
    fp_path.unlink()
    with pytest.raises(run_mod.RunArtifactError, match="Generator-Fingerprint"):
        run_mod.verify_run_artifacts(out, report)


def test_dec87_missing_mandatory_artifact_means_no_verdict_file(dec87_run, tmp_path, monkeypatch):
    """DEC-87 (V7): if a mandatory artifact cannot be written/verified the run aborts loudly and NO verdict file
    (``wp13_run.json``) exists -- KEIN VERDIKT. Here the residualised series is silently not written."""
    orig = run_mod._write_series_csv

    def skipping(path, series):
        if path.name.endswith("_residualized.csv"):
            return {"path": str(path), "sha256": "0" * 64}
        return orig(path, series)

    monkeypatch.setattr(run_mod, "_write_series_csv", skipping)
    out = tmp_path / "abort"
    with pytest.raises(run_mod.RunArtifactError, match="KEIN VERDIKT"):
        run_mod.write_run_artifacts(out, copy.deepcopy(dec87_run[3]))
    assert not (out / "wp13_run.json").exists() and not (out / "wp13_run_L_window_sealed.json").exists()


# ---- T1 fixtures with the registered method fm_neutral_8w ----------------------------

def _fm8_constants(returns, alive, symbols, *, n_reps_null=80, rho_f=0.05, beta_sd=0.5):
    """The DEC-87 constants of a fixture window, computed by ``nulls.run_configuration_null`` -- the registered method
    ``fm_neutral_8w`` under a stress calibration (``rho_f``/``beta_sd``), driftfree and drifting -- exactly what the
    Vorlauf freezes and ``run_full`` recomputes -- plus the analytic floor and IC_min."""
    e_floor, w_judged = _floor_and_symbols(alive, returns.shape[0])
    cfg = nulls.run_configuration_null(returns, alive, symbols, method="fm_neutral_8w", rho_f=rho_f, beta_sd=beta_sd,
                                       n_reps=n_reps_null, seed=53)
    return {"e_floor": e_floor, "w_judged": w_judged, "ic_min": nulls.ic_threshold(e_floor, 1.0, w_judged),
            **cfg["constants"]}


def _fm8_gate(variant, direction, characteristic, returns, alive, symbols, consts, *, bounce=None, outcome=None,
              gate5=None):
    """``run_hypothesis`` for both windows (the same arrays in W1 and W2) with the registered method
    ``fm_neutral_8w`` and the FROZEN ``consts`` (from :func:`_fm8_constants`)."""
    pit = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT", trail_win=8, min_weeks=8)
    both = lambda x: {"W1": x, "W2": x}                                                  # noqa: E731
    return run_mod.run_hypothesis(
        "H-X", variant, direction, both(characteristic), both(returns if outcome is None else outcome), both(alive),
        symbols, both(consts["ic_min"]), both(consts["w_judged"]), both(consts["e_floor"]),
        both(consts["ceiling_method_stress"]), bounce_ic=bounce, gate5_by_window=gate5,
        beta_control_method="fm_neutral_8w", beta_control_pit_by_window=both(pit),
        res_quantile_driftfree_by_window=both(consts["res_quantile_driftfree"][variant]),
        res_quantile_drifting_by_window=both(consts["res_quantile_drifting"][variant]),
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53)


def _fm8_hypothesis_run(variant, direction, characteristic, returns, alive, symbols, *, bounce=None,
                        n_reps_null=80, rho_f=0.05, beta_sd=0.5, outcome=None, gate5=None):
    consts = _fm8_constants(returns, alive, symbols, n_reps_null=n_reps_null, rho_f=rho_f, beta_sd=beta_sd)
    return (_fm8_gate(variant, direction, characteristic, returns, alive, symbols, consts, bounce=bounce,
                      outcome=outcome, gate5=gate5), consts, consts["ic_min"])


def test_dec87_t1_fm8_positive_fixture_passes():
    """T1 positive with the registered method: an injected cross-sectional signal (rho 0.30) clears every component --
    raw IC, bootstrap, IC_min, the fm_neutral_8w-neutralised IC and the (more extreme) binding null quantile."""
    rng = np.random.default_rng(0)
    k, w = 120, 52
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns = rng.normal(0, 0.03, size=(w, k + 1))
    characteristic = rng.normal(0, 1, size=(w, k + 1))
    a = 0.30 / math.sqrt(1 - 0.30 ** 2)
    returns[1:] += a * 0.03 * characteristic[:-1]
    alive = np.ones((w, k + 1), dtype=bool)
    res, c, ic_min = _fm8_hypothesis_run("mom1", "positive", characteristic, returns, alive, symbols)
    assert res["verdict"]["verdict"] == "PASS", res["verdict"]["labels"]
    w1 = res["payload"]["windows"]["W1"]
    assert w1["res_quantile_binding"] == max(c["res_quantile_driftfree"]["mom1"], c["res_quantile_drifting"]["mom1"])
    assert w1["residualized_mean_ic"] > w1["res_quantile_binding"] and w1["selection_ceiling_mean_of_max"] < ic_min


def test_dec87_t1_fm8_null_fixture_drops():
    """T1 null (permuted characteristic, i.e. no information at all) with ``fm_neutral_8w``: no PASS."""
    rng = np.random.default_rng(1)
    k, w = 120, 52
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns = rng.normal(0, 0.03, size=(w, k + 1))
    characteristic = rng.normal(0, 1, size=(w, k + 1))
    alive = np.ones((w, k + 1), dtype=bool)
    res, _c, _ic_min = _fm8_hypothesis_run("mom1", "positive", characteristic, returns, alive, symbols)
    assert res["verdict"]["verdict"] == "DROP"


def _adversarial_beta_panel(seed: int, k: int = 150, w: int = 104):
    """PRD 5.3 adversarial fixture: an AR(1) market factor (rho 0.2) with drift 0.002, betas U(0.5, 2.0), NO cross-sectional
    predictability -- the momentum characteristic is only mechanically tied to beta (market-timing artifact)."""
    rng = np.random.default_rng(seed)
    rho_f, drift_f, sigma_f = 0.2, 0.002, 0.05
    beta_true = rng.uniform(0.5, 2.0, size=k)
    f = np.empty(w)
    f[0] = drift_f / (1.0 - rho_f) + sigma_f * rng.standard_normal()
    for t in range(1, w):
        f[t] = drift_f + rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    idio = rng.normal(0.0, sigma_f, size=(w, k))
    returns_full = np.concatenate([beta_true[None, :] * f[:, None] + idio, f[:, None]], axis=1)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    alive = np.ones((w, k + 1), dtype=bool)
    return returns_full, symbols, alive, characteristics.momentum_characteristic(returns_full, trail_win=1)


def test_dec87_t1_fm8_adversarial_beta_fixture_drops_where_the_raw_gate_would_fire():
    """T1 adversarial with ``fm_neutral_8w`` and the DEC-87 binding null quantile (max of driftfree/drifting). The null
    is calibrated to the adversary's own world (stress rho_f 0.2, beta_sd 0.45 ~ the U(0.5, 2) dispersion; the v5d
    calibrations are rho_f 0.05-0.09, i.e. an easier world), frozen ONCE from one panel (as the Vorlauf freezes it) and
    applied to several independent draws of the fixture. Teeth: in every draw the RAW mean IC is the market-timing
    artifact (positive, above IC_min, sign/IC_min components pass); the beta-control component is what stops it -- the
    neutralised IC does not clear the binding quantile -- and the verdict is DROP in all of them."""
    seeds = (8, 9, 10, 12)
    returns_full, symbols, alive, mom1 = _adversarial_beta_panel(seeds[0])
    consts = _fm8_constants(returns_full, alive, symbols, n_reps_null=150, rho_f=0.2, beta_sd=0.45)
    for seed in seeds:
        returns_full, symbols, alive, mom1 = _adversarial_beta_panel(seed)
        res = _fm8_gate("mom1", "positive", mom1, returns_full, alive, symbols, consts)
        assert res["verdict"]["verdict"] == "DROP", (seed, res["verdict"]["labels"])
        for wn in ("W1", "W2"):
            w = res["payload"]["windows"][wn]
            pw = res["verdict"]["per_window"][wn]
            assert w["mean_ic"] > w["ic_min_capped"] and pw["sign_ok"] and pw["ic_min_ok"], (seed, w["mean_ic"])   # artifact
            assert w["residualized_mean_ic"] < w["mean_ic"]                                                        # fm8 removes most of it
            assert not pw["beta_control_beyond_drifting_null_ok"] and not pw["window_pass"], (seed, w["residualized_mean_ic"])
            assert w["res_quantile_binding"] == max(w["res_quantile_driftfree"], w["res_quantile_drifting"])


def test_dec87_t1_h29_bounce_fixture_fires_no_pass():
    """T1 H-29: a bounce at least as large as the real |IC| in a window is no PASS even though every other component
    holds (a strong Lag-2 reversal injected: r[t] = e[t] - c * z(r[t-2]), i.e. rev_gap vs the next week is negative)."""
    rng = np.random.default_rng(2)
    k, w = 120, 52
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    e = rng.normal(0, 0.03, size=(w, k + 1))
    c = 0.30 / math.sqrt(1 - 0.30 ** 2) * 0.03
    returns = e.copy()
    for t in range(2, w):
        prev = returns[t - 2]
        returns[t] = e[t] - c * (prev - prev.mean()) / prev.std(ddof=1)
    alive = np.ones((w, k + 1), dtype=bool)
    rev = characteristics.reversal_gap_characteristic(returns)
    consts = _fm8_constants(returns, alive, symbols, n_reps_null=80)
    clean = _fm8_gate("rev_gap", "negative", rev, returns, alive, symbols, consts, bounce={"W1": 0.0005, "W2": 0.0005})
    assert clean["verdict"]["verdict"] == "PASS", clean["verdict"]["labels"]
    ic_real = abs(clean["payload"]["windows"]["W2"]["mean_ic"])
    hit = _fm8_gate("rev_gap", "negative", rev, returns, alive, symbols, consts,
                    bounce={"W1": 0.0005, "W2": ic_real + 0.001})
    assert hit["verdict"]["verdict"] == "DROP" and hit["verdict"]["bounce_windows"] == ["W2"]
    assert hit["verdict"]["bounce_kill"] and any("Artefakt Bounce" in l for l in hit["verdict"]["labels"])
    assert all(r["window_pass"] for r in hit["verdict"]["per_window"].values())      # only the bounce rule fires


def test_dec87_t1_a3v_fixture_same_vol_dispersion_no_relation_fires_no_gate():
    """T1 A3-V (PRD 5.3 adversarial fixture for H-30, DEC-87 (G)): wide vol DISPERSION across symbols, NO relation between
    vol and return, daily log returns with E[r_log] = mu - sigma^2/2 (mu = 0: every symbol has the same ARITHMETIC
    mean). With the weekly sigma_w and the ADDED drag the vol-weighted, adjusted outcome has no negative relation to vol
    (a small POSITIVE offset remains: the drag adjustment uses the NOISY estimate sigma_w-hat, whose regression to the
    mean over-corrects high estimates -- against the registered negative direction, i.e. conservative); no component in
    the hypothesis direction fires and the verdict is DROP. The same data under the pre-DEC-87 formula (daily drag
    SUBTRACTED from the weekly log outcome) and under the right units with the wrong sign give clearly lower ICs -- the
    mechanical advantage in the registered direction this fixture exists to catch."""
    k, n_weeks = 150, 70
    rng = np.random.default_rng(31)
    daily_sd = np.exp(np.log(0.055) + 0.5 * rng.standard_normal(k + 1))         # wide dispersion, incl. the BTC column
    panel, weeks, returns = _weekly_daily_panel(k=k + 1, n_weeks=n_weeks, seed=32, daily_sd=daily_sd)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    alive = np.ones((len(weeks), k + 1), dtype=bool)
    vol_rv = characteristics.realized_vol_characteristic(panel, weeks)
    day_count = characteristics.weekly_valid_day_count(panel, weeks)
    new_outcome = run_mod.h30_outcome_for_window(returns, vol_rv, day_count)
    new_ic = ic.weekly_ic_series(vol_rv, new_outcome, alive, convention="close_at_last")["mean_ic"]

    def ic_of(pre_aligned):
        return ic.weekly_ic_series(vol_rv, run_mod.prealigned_outcome_to_returns_like(pre_aligned), alive,
                                   convention="close_at_last")["mean_ic"]

    target_d = float(np.median(vol_rv[~np.isnan(vol_rv)]))
    old_pre = np.full_like(returns, np.nan)
    old_pre[:-1] = (returns[1:] - 0.5 * vol_rv[:-1] ** 2) * (target_d / vol_rv[:-1])          # the pre-DEC-87 formula
    sigma_w = np.sqrt(day_count) * vol_rv
    wrong_sign = np.full_like(returns, np.nan)
    wrong_sign[:-1] = (returns[1:] - 0.5 * sigma_w[:-1] ** 2) * (np.nanmedian(sigma_w) / sigma_w[:-1])   # weekly units, drag subtracted
    old_ic, wrong_ic = ic_of(old_pre), ic_of(wrong_sign)

    se_ref = 1.0 / math.sqrt(k) / math.sqrt(len(weeks) - 1)
    assert -2.0 * se_ref < new_ic < 3.5 * se_ref, (new_ic, se_ref)               # no advantage in the negative direction
    assert new_ic - old_ic > 2.0 * se_ref, (new_ic, old_ic, se_ref)              # the old formula tilts negative
    assert wrong_ic < -3.5 * se_ref, (wrong_ic, se_ref)                          # the sign error is a strong artifact

    g5 = {"W1": 0.1, "W2": 0.1}
    res, _c, ic_min = _fm8_hypothesis_run("vol_rv", "negative", vol_rv, returns, alive, symbols, outcome=new_outcome,
                                          gate5=g5, n_reps_null=40)
    assert res["verdict"]["verdict"] == "DROP"
    for wn in ("W1", "W2"):
        assert not res["verdict"]["per_window"][wn]["window_pass"]
        assert res["payload"]["windows"][wn]["mean_ic"] > -ic_min                  # nothing in the hypothesis direction


def _prd_positive_panel(*, k=200, seed=7, ic_mom1=0.06, ic_rev=0.06, n_sectors=8, sigma_f=0.06, rho_f=0.05,
                        beta_sd=0.4, sigma_g=0.03, sigma_e=0.08):
    """The PRD 5.3 positive-control fixture (Drittfassung draft 3/6): an injected cross-sectional IC of 0.06
    (mom1 positive, rev_gap negative, i.e. a Lag-2 reversal), INDEPENDENT of beta, on a panel with a common BTC factor
    (the market column IS the factor, DEC-85 (i)), heterogeneous betas and sector blocks (a common sector shock per
    week). Union-panel-shaped dicts, no disk: ``panel`` (daily closes/turnover whose 7 daily returns sum exactly to
    the weekly return) and ``weekly``."""
    from datetime import timedelta
    rng = np.random.default_rng(seed)
    weeks_d, d0 = [], date(2024, 5, 6)
    while d0 <= date(2026, 6, 29):
        weeks_d.append(d0)
        d0 += timedelta(days=7)
    n_w, n = len(weeks_d), k + 1
    symbols = ["BTCUSDT"] + [f"S{i:03d}USDT" for i in range(k)]
    beta = np.concatenate([[1.0], 1.0 + beta_sd * rng.standard_normal(k)])
    sector = np.concatenate([[-1], np.arange(k) % n_sectors])
    f = np.empty(n_w)
    f[0] = sigma_f * rng.standard_normal()
    for t in range(1, n_w):
        f[t] = rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    g = sigma_g * rng.standard_normal((n_w, n_sectors))
    e = sigma_e * rng.standard_normal((n_w, n))
    sigma_tot = math.sqrt(sigma_e ** 2 + sigma_g ** 2 + (beta_sd * sigma_f) ** 2)
    c1 = ic_mom1 / math.sqrt(1 - ic_mom1 ** 2) * sigma_tot
    c2 = ic_rev / math.sqrt(1 - ic_rev ** 2) * sigma_tot

    def z(row):
        x = row[1:]
        sd = x.std(ddof=1)
        return np.concatenate([[0.0], (x - x.mean()) / (sd if sd > 0 else 1.0)])

    r = np.zeros((n_w, n))
    for t in range(n_w):
        row = beta * f[t] + np.where(sector >= 0, g[t, np.maximum(sector, 0)], 0.0) + e[t]
        if t >= 1:
            row = row + c1 * z(r[t - 1])
        if t >= 2:
            row = row - c2 * z(r[t - 2])
        row[0] = f[t]
        r[t] = row
    daily_noise = 0.01 * rng.standard_normal((n_w, 7, n))
    daily_noise -= daily_noise.mean(axis=1, keepdims=True)
    dates, close_rows, turnover_rows = [], [], []
    price = np.full(n, 100.0)
    for t, wd in enumerate(weeks_d):
        daily = r[t][None, :] / 7.0 + daily_noise[t]
        for day in range(7):
            price = price * np.exp(daily[day])
            dates.append((wd + timedelta(days=day)).isoformat())
            close_rows.append(price.copy())
            turnover_rows.append(1e6 * np.exp(0.5 * rng.standard_normal(n)))
    close = np.array(close_rows)
    returns = np.zeros((n_w, n))
    returns[1:] = np.log(close[6::7][1:] / close[6::7][:-1])
    valid = np.ones((n_w, n), dtype=bool)
    valid[0] = False
    panel = {"symbols": symbols, "dates": dates, "close": close, "turnover": np.array(turnover_rows)}
    weekly = {"weeks": [w.isoformat() for w in weeks_d], "returns": returns, "alive": np.ones((n_w, n), dtype=bool),
              "returns_valid": valid}
    return panel, weekly


def _prd_registered(weekly, entries, *, n_reps=60):
    reg = {"hypotheses": entries, "windows": {}, "beta_control": {"method": "fm_neutral_8w", "beta_window_weeks": 8},
           "rules": {"seed": 53, "n_reps": n_reps, "n_reps_bootstrap": 200, "n_reps_permutation": 200,
                     "n_sims_persistence": 40, "bounce_spread": BOUNCE_SPREAD}}
    from bybit_edge.research.wp13_xsec import prelaunch as prelaunch_mod
    for wn, (a, b) in {"W1": ("2024-07-01", "2025-06-30"), "W2": ("2025-07-01", "2026-06-30")}.items():
        win = prelaunch_mod.slice_window(weekly["weeks"], a, b, weekly["returns"], weekly["alive"])
        fl = nulls.analytic_permutation_floor(win["alive"], win["weeks"])
        thr = nulls.ic_threshold(fl["e_floor"], 1.0, fl["w_judged"])
        reg["windows"][wn] = {"start": a, "end": b, "ic_min_capped": {v: thr for v in characteristics.VARIANT_NAMES},
                              "w_judged": fl["w_judged"], "bounce_sigma_true": BOUNCE_SIGMA[wn],
                              "calibration": _window_calibration(0.10, 0.45)}
    return reg


def test_dec87_prd_positive_fixture_passes_end_to_end_through_run_full():
    """DEC-87 (T1/Positivkontrolle): the PRD 5.3 positive-control fixture -- injected IC 0.06 + common BTC factor/beta +
    sector blocks -- through ``run_full`` with the registered ``fm_neutral_8w`` and the DEC-87 null constants: BOTH
    injected variants (mom1 positive, rev_gap negative) PASS and their hypotheses aggregate to PASS; the H-30 entry
    (vol_rv, NO injected vol/return relation, Gate (5) satisfied since turnover is independent of vol) does not."""
    panel, weekly = _prd_positive_panel()
    entries = {"H-28_mom1": {"hypothesis": "H-28", "variant": "mom1", "direction": "positive"},
               "H-29_rev_gap": {"hypothesis": "H-29", "variant": "rev_gap", "direction": "negative"},
               "H-30_vol_rv": {"hypothesis": "H-30", "variant": "vol_rv", "direction": "negative",
                               "outcome": "vol_weighted"}}
    report = run_mod.run_full(panel, weekly, _prd_registered(weekly, entries))
    for eid in ("H-28_mom1", "H-29_rev_gap"):
        v = report["results"][eid]["verdict"]
        assert v["verdict"] == "PASS", (eid, v["labels"])
        for wn in ("W1", "W2"):
            w = report["results"][eid]["payload"]["windows"][wn]
            assert abs(w["mean_ic"]) > 0.04 and abs(w["residualized_mean_ic"]) > abs(w["res_quantile_binding"])
            assert w["selection_ceiling_mean_of_max"] < w["ic_min_capped"]
    assert report["hypothesis_verdicts"]["H-28"]["verdict"] == "PASS" == report["hypothesis_verdicts"]["H-29"]["verdict"]
    assert report["results"]["H-29_rev_gap"]["verdict"]["bounce_kill"] is False
    h30 = report["results"]["H-30_vol_rv"]
    assert h30["verdict"]["verdict"] == "DROP" and report["hypothesis_verdicts"]["H-30"]["verdict"] == "DROP"
    assert all(h30["payload"]["windows"][wn]["gate5_median_spearman"] < 0.6 for wn in ("W1", "W2"))


# ---- the synthetic end-to-end CLI run: --prelaunch + --emit-registered-template + --run -------------

def test_dec87_cli_end_to_end_prelaunch_emit_run_produces_a_verdict_with_all_dec53_artifacts(tmp_path, monkeypatch):
    """Abnahme: ``--prelaunch`` -> ``--emit-registered-template`` -> ``--run`` on the synthetic union tree. The pass
    table's tolerance factors are relaxed (12-symbol panel, 5 replicates: the strict DEC-77 bounds reject everything,
    see ``test_dec87_prelaunch_without_a_confirmed_method...``) so a method is confirmed; everything else is the real
    pipeline: confirmation, frozen constants from ``nulls.run_configuration_null``, the YAML with sha256 lock,
    per-window calibration, fingerprints measured on the loaded panel and checked, artifacts written and verified, a
    verdict for every entry and every hypothesis."""
    real = prelaunch_module.beta_control_pass_table

    def relaxed(study, **kw):
        kw.setdefault("null_mean_tol_factor", 1e6)
        kw.setdefault("ceiling_tol_factor", 1e6)
        return real(study, **kw)

    monkeypatch.setattr(prelaunch_module, "beta_control_pass_table", relaxed)
    _panel, _weekly, surv_base, _sm, del_base, _dm, _dd = _build_prelaunch_fixture_tree(tmp_path)
    pre_out = tmp_path / "prelaunch"
    ns = _ns_prelaunch(panel_base=str(surv_base), delisted_base=str(del_base), out=str(pre_out),
                       gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9,
                       no_gegenprobe_market_check=True, calibration_search_n_reps=5, calibration_search_rel_tol=10.0,
                       calibration_search_max_iter=8)
    assert WP13.cmd_prelaunch(ns) == 0
    pre = json.loads((pre_out / "wp13a_prelaunch.json").read_text(encoding="utf-8"))
    assert pre["beta_control_confirmation"]["confirmed_method"]
    fps = pre["data_fingerprints"]
    assert len(fps["union_range_fingerprint"]) == 64 and fps["delisting_dates_sha256"] == panel_load.sha256_file(del_base / "delisting_dates.json")
    md = (pre_out / "wp13a_prelaunch.md").read_text(encoding="utf-8")
    assert "## Gewinner-Bestaetigung" in md and "## Daten-Fingerprints" in md

    template = tmp_path / "registered.yaml"
    assert WP13.cmd_emit_registered_template(str(pre_out / "wp13a_prelaunch.json"), str(template)) == 0
    reg = run_mod.load_registered_yaml(template)
    assert reg["beta_control"]["method"] == pre["beta_control_confirmation"]["confirmed_method"]
    assert reg["data_fingerprints"]["union_range_fingerprint"] == fps["union_range_fingerprint"]
    assert reg["rules"]["n_reps"] == 5
    # the orchestrator-side step: the test only shrinks the bootstrap/permutation reps (not frozen constants)
    reg["rules"].update(n_reps_bootstrap=20, n_reps_permutation=20, n_sims_persistence=20)
    template.write_text(yaml.safe_dump(reg, sort_keys=False), encoding="utf-8")
    sha = run_mod.sha256_of_file(template)
    # DEC-89: the emitted template is complete for the strict pre-flight (bounce parameters, survivorship, rules, w_judged)
    run_mod.validate_registered(reg, require_frozen_constants=True)

    run_out = tmp_path / "run_out"
    ns_run = WP13.argparse.Namespace(
        run=True, prelaunch=False, registered=str(template), registered_sha256=sha,
        panel_base=str(surv_base), delisted_base=str(del_base), delisted_manifest="", delisting_dates="",
        start_year=2021, end_year=2026, as_of="2027-01-01", out=str(run_out), seed=53,
        convention="close_at_last", allow_partial=False)
    assert WP13.cmd_run(ns_run) == 0
    main = json.loads((run_out / "wp13_run.json").read_text(encoding="utf-8"))
    assert set(main["hypothesis_verdicts"]) == {"H-28", "H-29", "H-30"}
    assert set(main["results"]) == set(reg["hypotheses"])
    assert main["observed_fingerprints"]["union_range_fingerprint"] == fps["union_range_fingerprint"]
    assert main["registered_sha256"] == sha and main["frozen_constants_complete"] is True
    for eid, hcfg in reg["hypotheses"].items():
        res = main["results"][eid]
        assert res["verdict"]["verdict"] in ("PASS", "DROP")
        if hcfg.get("status") == "gl012_pre_run":
            assert res["computed"] is False
            continue
        for wn in ("W1", "W2"):
            assert (run_out / f"wp13_run_{eid}_{wn}_ic_weekly.csv").is_file()
            assert (run_out / f"wp13_run_{eid}_{wn}_ic_weekly_residualized.csv").is_file()
    assert (run_out / "wp13_run_fingerprint.json").is_file() and (run_out / "wp13_run_L_window_sealed.json").is_file()
    # DEC-89 (E3 (7)): the Markdown report with the bounce parameters and the survivorship label sits next to the JSON
    md = (run_out / "wp13_run.md").read_text(encoding="utf-8")
    assert md.isascii() and "Bounce-Fixture" in md and "0.003621" in md and "Survivorship-Etikett" in md
    assert main["registered_inputs"]["bounce_spread"] == 0.003621 == reg["rules"]["bounce_spread"]
    assert main["registered_inputs"]["bounce_sigma_true"] == {wn: reg["windows"][wn]["bounce_sigma_true"] for wn in ("W1", "W2")}
    assert main["results"]["H-28_mom1"]["verdict"]["survivorship_label"] is True
    fp = json.loads((run_out / "wp13_run_fingerprint.json").read_text(encoding="utf-8"))
    assert fp["data_fingerprints"]["delisting_dates_sha256"] == fps["delisting_dates_sha256"]
    assert fp["code"]["code_sha256"] and fp["registered_sha256"] == sha

    # a YAML pinned to a DIFFERENT panel fingerprint is refused before any verdict (V9): rc=1, no verdict file
    bad = copy.deepcopy(reg)
    bad["data_fingerprints"]["union_range_fingerprint"] = "0" * 64
    bad_path = tmp_path / "registered_bad.yaml"
    bad_path.write_text(yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
    ns_bad = WP13.argparse.Namespace(**{**vars(ns_run), "registered": str(bad_path),
                                        "registered_sha256": run_mod.sha256_of_file(bad_path),
                                        "out": str(tmp_path / "run_bad")})
    assert WP13.cmd_run(ns_bad) == 1
    assert not (tmp_path / "run_bad" / "wp13_run.json").exists()
    # the old global-calibration form is refused by the CLI pre-flight (rc=1), before the panel is read
    old = copy.deepcopy(reg)
    old["calibration"] = {"stress": {"rho_f": 0.1, "beta_sd_calibrated": 0.5}}
    old_path = tmp_path / "registered_old.yaml"
    old_path.write_text(yaml.safe_dump(old, sort_keys=False), encoding="utf-8")
    ns_old = WP13.argparse.Namespace(**{**vars(ns_run), "registered": str(old_path),
                                        "registered_sha256": run_mod.sha256_of_file(old_path),
                                        "out": str(tmp_path / "run_old")})
    assert WP13.cmd_run(ns_old) == 1 and not (tmp_path / "run_old").exists()
    # a template without frozen constants (e.g. emitted when no method was confirmed) is refused by the pre-flight
    unfrozen = copy.deepcopy(reg)
    unfrozen["windows"]["W1"]["ceiling_method_stress"] = None
    unfrozen_path = tmp_path / "registered_unfrozen.yaml"
    unfrozen_path.write_text(yaml.safe_dump(unfrozen, sort_keys=False), encoding="utf-8")
    ns_unfrozen = WP13.argparse.Namespace(**{**vars(ns_run), "registered": str(unfrozen_path),
                                             "registered_sha256": run_mod.sha256_of_file(unfrozen_path),
                                             "out": str(tmp_path / "run_unfrozen")})
    assert WP13.cmd_run(ns_unfrozen) == 1 and not (tmp_path / "run_unfrozen").exists()


# ============================================================================
# DEC-89 (before the registration): bounce parameters from the YAML, survivorship label, GL-012 label at hypothesis
# level, persistence null in both windows, T5 pins (w_judged / block_len / level), the run's Markdown report, and the
# positive control in production configuration (``--positive-control``, PRD 3.3.8)
# ============================================================================

import inspect  # noqa: E402
import re  # noqa: E402
from datetime import timedelta  # noqa: E402

from bybit_edge.research.wp13_xsec import positive_control as pc_mod  # noqa: E402

_MOM1 = {"hypothesis": "H-28", "variant": "mom1", "direction": "positive"}
_REV_GAP = {"hypothesis": "H-29", "variant": "rev_gap", "direction": "negative"}
_SURV = {"W1": {"mom1_diff_in_ic_min_units": -0.198, "rev_gap_diff_in_ic_min_units": -0.189},
         "W2": {"mom1_diff_in_ic_min_units": -0.438, "rev_gap_diff_in_ic_min_units": -0.579}}


def _registered_lean(entries: dict) -> dict:
    """The DEC-87/89 hand-built file (``fm_neutral_8w``, small reps, bounce parameters) with exactly ``entries``."""
    reg = _registered_dec87_large()
    reg["hypotheses"] = copy.deepcopy(entries)
    return reg


def _strict_registered() -> dict:
    """A registered dict that passes the CLI's STRICT pre-flight: dummy finite frozen constants (the strict check only
    demands that they exist and are finite) plus every DEC-89 mandatory field."""
    reg = _registered_lean({"H-28_mom1": _MOM1, "H-29_rev_gap": _REV_GAP})
    for wn in ("W1", "W2"):
        reg["windows"][wn].update(
            w_judged=52, ceiling_method_stress=0.008, survivorship=copy.deepcopy(_SURV[wn]),
            res_quantile_driftfree={v: 0.02 for v in characteristics.VARIANT_NAMES},
            res_quantile_drifting={v: 0.021 for v in characteristics.VARIANT_NAMES})
    reg["rules"].update(block_len=4, level=0.9936)
    return reg


def _registered_dec89_large() -> dict:
    """``_registered_dec87_large`` + the registered survivorship numbers; H-30 is locked in BOTH variants (so the
    hypothesis reads ``GL-012 vor dem Lauf``), mom2 stays locked, mom1 and rev_gap are computed."""
    reg = copy.deepcopy(_registered_dec87_large())
    reg["hypotheses"]["H-30_vol_rv"] = {
        "hypothesis": "H-30", "variant": "vol_rv", "direction": "negative", "outcome": "vol_weighted",
        "status": "gl012_pre_run", "reason": "H-30-Feasibility in Wocheneinheiten verfehlt (Test)"}
    for wn in ("W1", "W2"):
        reg["windows"][wn]["survivorship"] = copy.deepcopy(_SURV[wn])
    return reg


@pytest.fixture(scope="module")
def dec89_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dec89_large")
    panel, weekly = _build_run_fixture_tree_large(tmp)
    registered = _registered_dec89_large()
    for wn in ("W1", "W2"):                                  # the registered w_judged: what the Vorlauf froze for the window
        wk = prelaunch_module.slice_window(weekly["weeks"], registered["windows"][wn]["start"],
                                           registered["windows"][wn]["end"])["weeks"]
        registered["windows"][wn]["w_judged"] = nulls.w_judged_of(len(wk))
    report = run_mod.run_full(panel, weekly, registered, observed_fingerprints=None)
    return panel, weekly, registered, report


# ---- E1: bounce-fixture parameters come from the YAML --------------------------------------------

def test_dec89_bounce_fixture_has_no_defaults_and_rejects_bad_values():
    """DEC-89 E1: the former code constants (0.003 / 0.03, UNBELEGT in a kill condition) are gone: a call without the
    registered values is a TypeError, a non-finite / non-positive / non-numeric one a ValueError."""
    with pytest.raises(TypeError):
        run_mod.bounce_fixture_ic(40, 30, seed=53)                        # type: ignore[call-arg]
    with pytest.raises(TypeError):
        run_mod.bounce_fixture_ic(40, 30, spread=0.003, seed=53)           # type: ignore[call-arg]
    for bad in (0.0, -0.001, float("nan"), float("inf"), None, True, "0.003"):
        with pytest.raises(ValueError, match="spread"):
            run_mod.bounce_fixture_ic(40, 30, spread=bad, sigma_true=0.1)
        with pytest.raises(ValueError, match="sigma_true"):
            run_mod.bounce_fixture_ic(40, 30, spread=0.003, sigma_true=bad)
    defaults = {p.name: p.default for p in inspect.signature(run_mod.bounce_fixture_ic).parameters.values()}
    assert defaults["spread"] is inspect.Parameter.empty and defaults["sigma_true"] is inspect.Parameter.empty


def test_dec89_run_full_feeds_the_registered_bounce_parameters_to_the_fixture(tmp_path, monkeypatch):
    """DEC-89 E1: ``run_full`` hands ``rules.bounce_spread`` and each window's ``bounce_sigma_true`` (seed ``rules.seed``)
    to the fixture; the payload and the report echo exactly those parameters and the resulting ``IC_bounce``."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    calls: list[dict] = []
    orig = run_mod.bounce_fixture_ic

    def spy(*a, **kw):
        calls.append(kw)
        return orig(*a, **kw)

    monkeypatch.setattr(run_mod, "bounce_fixture_ic", spy)
    reg = _registered_lean({"H-29_rev_gap": _REV_GAP})
    reg["rules"]["bounce_spread"] = 0.0042
    reg["windows"]["W1"]["bounce_sigma_true"], reg["windows"]["W2"]["bounce_sigma_true"] = 0.111, 0.222
    report = run_mod.run_full(panel, weekly, reg)
    assert [(c["spread"], c["sigma_true"], c["seed"]) for c in calls] == [(0.0042, 0.111, 53), (0.0042, 0.222, 53)]
    payload = report["results"]["H-29_rev_gap"]["payload"]
    for wn, sig in (("W1", 0.111), ("W2", 0.222)):
        d = payload["bounce_fixture"][wn]
        assert d["spread"] == 0.0042 and d["sigma_true"] == sig and d["seed"] == 53
        assert payload["bounce_ic"][wn] == d["ic_bounce"]
    assert report["registered_inputs"]["bounce_spread"] == 0.0042
    assert report["registered_inputs"]["bounce_sigma_true"] == {"W1": 0.111, "W2": 0.222}


def test_dec89_missing_or_malformed_bounce_parameters_are_a_loud_fail_even_in_the_lenient_mode():
    """DEC-89 E1: the former defaults are gone, so even a hand-built file (lenient ``validate_registered``) that COMPUTES
    an H-29/rev_gap entry must carry both parameters; a locked rev_gap entry or a file without one does not need them."""
    base = _registered_lean({"H-28_mom1": _MOM1, "H-29_rev_gap": _REV_GAP})
    run_mod.validate_registered(base)
    no_spread = copy.deepcopy(base)
    del no_spread["rules"]["bounce_spread"]
    with pytest.raises(run_mod.RegisteredSchemaError, match="bounce_spread"):
        run_mod.validate_registered(no_spread)
    with pytest.raises(run_mod.RegisteredSchemaError, match="bounce_spread"):           # run_full refuses before any panel
        run_mod.run_full({"symbols": []}, {"weeks": [], "returns": None, "alive": None}, no_spread)
    no_sigma = copy.deepcopy(base)
    del no_sigma["windows"]["W2"]["bounce_sigma_true"]
    with pytest.raises(run_mod.RegisteredSchemaError, match=r"windows\.W2\.bounce_sigma_true"):
        run_mod.validate_registered(no_sigma)
    for key, val in (("spread", -0.003), ("spread", float("nan")), ("sigma", 0.0), ("sigma", "0.17")):
        bad = copy.deepcopy(base)
        if key == "spread":
            bad["rules"]["bounce_spread"] = val
        else:
            bad["windows"]["W1"]["bounce_sigma_true"] = val
        with pytest.raises(run_mod.RegisteredSchemaError, match="keine endliche positive Zahl"):
            run_mod.validate_registered(bad)
    locked = _registered_lean({"H-28_mom1": _MOM1, "H-29_rev_gap": dict(_REV_GAP, status="gl012_pre_run", reason="Test")})
    del locked["rules"]["bounce_spread"]
    del locked["windows"]["W1"]["bounce_sigma_true"]
    run_mod.validate_registered(locked)                                                  # no computed H-29 entry: not needed


@pytest.mark.parametrize("mutate, message", [
    (lambda r: r["rules"].pop("bounce_spread"), "rules.bounce_spread fehlt"),
    (lambda r: r["rules"].pop("block_len"), "rules.block_len fehlt"),
    (lambda r: r["rules"].pop("level"), "rules.level fehlt"),
    (lambda r: r["windows"]["W1"].pop("bounce_sigma_true"), "windows.W1.bounce_sigma_true fehlt"),
    (lambda r: r["windows"]["W2"].pop("w_judged"), "windows.W2.w_judged fehlt"),
    (lambda r: r["windows"]["W2"].pop("survivorship"), "windows.W2.survivorship fehlt"),
    (lambda r: r["windows"]["W1"]["survivorship"].pop("rev_gap_diff_in_ic_min_units"), "rev_gap_diff_in_ic_min_units fehlt"),
    (lambda r: r["windows"]["W1"]["survivorship"].update(mom1_diff_in_ic_min_units=None), "mom1_diff_in_ic_min_units fehlt"),
    (lambda r: r["windows"]["W1"]["survivorship"].update(mom1_diff_in_ic_min_units=float("nan")), "nicht endlich"),
    (lambda r: r["windows"]["W1"].update(bounce_sigma_true=-0.1), "keine endliche positive Zahl"),
    (lambda r: r["rules"].update(bounce_spread=0.0), "keine endliche positive Zahl"),
    (lambda r: r["rules"].update(block_len=4.5), "keine positive ganze Zahl"),
    (lambda r: r["rules"].update(level=1.0), "liegt nicht in (0, 1)"),
    (lambda r: r["windows"]["W1"].update(w_judged=0), "keine positive ganze Zahl"),
])
def test_dec89_strict_preflight_refuses_missing_or_malformed_constants(mutate, message):
    """DEC-89 E1/E3 (CLI pre-flight like the other mandatory constants): ``--run`` and ``--positive-control`` validate with
    ``require_frozen_constants=True``, which demands the bounce parameters, the survivorship pair, ``w_judged`` and the
    ``rules.block_len``/``rules.level`` pins -- the template's ``None`` placeholders are refused."""
    reg = _strict_registered()
    run_mod.validate_registered(reg, require_frozen_constants=True)                       # the unmutated file passes
    mutate(reg)
    with pytest.raises(run_mod.RegisteredSchemaError, match=re.escape(message)):
        run_mod.validate_registered(reg, require_frozen_constants=True)


def test_dec89_read_bounce_spread_from_the_wp7_census_and_the_registered_value(tmp_path):
    """DEC-89 E1: the registered spread = the census' median perp spread of decile D10 (36.21 bp) / 1e4 = 0.003621."""
    census = Path(WP13.__file__).resolve().parents[1] / WP13.DEFAULT_SPREAD_CENSUS
    assert census.is_file()
    assert WP13.read_bounce_spread(census) == BOUNCE_SPREAD == 0.003621
    custom = tmp_path / "census.json"
    custom.write_text(json.dumps({"deciles": [{"decile": 1, "perp_spread_bp_median": 1.0},
                                              {"decile": 10, "perp_spread_bp_median": 40.0}]}), encoding="utf-8")
    assert WP13.read_bounce_spread(custom) == 0.004
    for bad in ({"deciles": [{"decile": 1, "perp_spread_bp_median": 1.0}]},
                {"deciles": [{"decile": 10, "perp_spread_bp_median": None}]},
                {"deciles": [{"decile": 10, "perp_spread_bp_median": 0.0}]}, {}):
        custom.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError, match="Spread-Zensus"):
            WP13.read_bounce_spread(custom)


def _hand_prelaunch_artifact(tmp_path, *, with_dec89_sections=True, name="artifact.json"):
    """A hand-built ``--prelaunch`` artifact (confirmed ``fm_neutral_8w``) with or without the Vorlauf sections the DEC-89
    template fields are copied from (``factor_preserving_null.driftfree.sigma_e_median_symbol_weekly``,
    ``survivorship_fixture``)."""
    win = {}
    for wn, s0, e0 in (("W1", "2024-07-01", "2025-06-30"), ("W2", "2025-07-01", "2026-06-30")):
        w = {"available": True, "start": s0, "end": e0,
             "noise_floor_and_threshold": {"ic_min_capped_per_variant": {v: 0.02 for v in characteristics.VARIANT_NAMES},
                                           "w_judged": 52},
             "beta_control_method_study": {"calibrations": {
                 cal: {"rho_f": 0.05 * k, "beta_sd_calibrated": 0.5 * k, "target_factor_share": 0.03 * k}
                 for cal, k in (("measured", 1), ("stress", 2), ("zero", 1))}},
             "frozen_null_constants": {"ceiling_method_stress": 0.0081,
                                       "res_quantile_driftfree": {v: 0.02 for v in characteristics.VARIANT_NAMES},
                                       "res_quantile_drifting": {v: 0.021 for v in characteristics.VARIANT_NAMES}}}
        if with_dec89_sections:
            w["factor_preserving_null"] = {"driftfree": {"sigma_e_median_symbol_weekly": BOUNCE_SIGMA[wn]}}
            w["survivorship_fixture"] = dict(_SURV[wn], k=419, n_weeks=53)
        win[wn] = w
    art = {"variants": list(characteristics.VARIANT_NAMES), "n_reps_beta_control_winner": 1000,
           "data_fingerprints": {"union_range_fingerprint": "11" * 32, "delisting_dates_sha256": "22" * 32},
           "windows": win,
           "h30_feasibility_weekly_units": {"spread_d10_minus_d1_over_kante": 2.8, "se_drag_over_kante": 0.18},
           "beta_control_confirmation": {"confirmed_method": "fm_neutral_8w", "note": "bestaetigt"}}
    path = tmp_path / name
    path.write_text(json.dumps(art), encoding="utf-8")
    return path


def test_dec89_emit_template_spread_census_option_and_loud_failures(tmp_path, monkeypatch):
    """DEC-89 E1: ``--emit-registered-template`` reads ``rules.bounce_spread`` from ``--spread-census`` (default: the WP-7
    census), an unreadable census is rc=1 and writes nothing; a missing Vorlauf section gives ``None`` placeholders + a
    WARNUNG that the strict pre-flight refuses; ``main()`` wires the option."""
    art = _hand_prelaunch_artifact(tmp_path)
    out_default = tmp_path / "t_default.yaml"
    assert WP13.cmd_emit_registered_template(str(art), str(out_default)) == 0
    y = run_mod.load_registered_yaml(out_default)
    assert y["rules"]["bounce_spread"] == 0.003621
    run_mod.validate_registered(y, require_frozen_constants=True)                       # complete for the strict pre-flight
    custom = tmp_path / "census.json"
    custom.write_text(json.dumps({"deciles": [{"decile": 10, "perp_spread_bp_median": 40.0}]}), encoding="utf-8")
    out_custom = tmp_path / "t_custom.yaml"
    assert WP13.cmd_emit_registered_template(str(art), str(out_custom), spread_census_path=str(custom)) == 0
    assert run_mod.load_registered_yaml(out_custom)["rules"]["bounce_spread"] == 0.004
    # via main(): --spread-census is honoured
    out_main = tmp_path / "t_main.yaml"
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py", "--emit-registered-template", str(art), str(out_main),
                                     "--spread-census", str(custom)])
    assert WP13.main() == 0 and run_mod.load_registered_yaml(out_main)["rules"]["bounce_spread"] == 0.004
    # an unreadable / incomplete census: rc=1, nothing written
    for i, content in enumerate(("not json", json.dumps({"deciles": []}), json.dumps({"deciles": [{"decile": 10}]}))):
        bad = tmp_path / f"bad{i}.json"
        bad.write_text(content, encoding="utf-8")
        out_bad = tmp_path / f"t_bad{i}.yaml"
        assert WP13.cmd_emit_registered_template(str(art), str(out_bad), spread_census_path=str(bad)) == 1
        assert not out_bad.exists()
    assert WP13.cmd_emit_registered_template(str(art), str(tmp_path / "t_none.yaml"),
                                             spread_census_path=str(tmp_path / "missing.json")) == 1
    # an artifact without the Vorlauf sections: placeholders, WARNUNG, and the strict pre-flight refuses them
    art2 = _hand_prelaunch_artifact(tmp_path, with_dec89_sections=False, name="artifact2.json")
    out2 = tmp_path / "t_missing.yaml"
    assert WP13.cmd_emit_registered_template(str(art2), str(out2)) == 0
    text = out2.read_text(encoding="utf-8")
    assert "WARNUNG: Vorlauf-Artefakt ohne" in text and "bounce_sigma_true" in text and "survivorship" in text
    y2 = run_mod.load_registered_yaml(out2)
    assert y2["windows"]["W1"]["bounce_sigma_true"] is None
    assert y2["windows"]["W1"]["survivorship"] == {"mom1_diff_in_ic_min_units": None, "rev_gap_diff_in_ic_min_units": None}
    with pytest.raises(run_mod.RegisteredSchemaError, match="bounce_sigma_true"):
        run_mod.validate_registered(y2)                                                  # lenient: rev_gap is computed
    with pytest.raises(run_mod.RegisteredSchemaError):
        run_mod.validate_registered(y2, require_frozen_constants=True)


# ---- E3 (2): survivorship label ----------------------------------------------------------------

def test_dec89_gates_survivorship_label_is_report_only():
    """DEC-89 E3 (2): the registered survivorship numbers are attached as a LABEL; the verdict and every gate flag are
    exactly those of the same payload without them (never a gate input)."""
    payload = _conserved_payload()
    base = gates.evaluate(payload)
    assert base["survivorship_label"] is False and not [l for l in base["labels"] if "Survivorship" in l]
    payload["survivorship_ic_min_units"] = {"W1": -0.198, "W2": -0.438}
    v = gates.evaluate(payload)
    assert v["verdict"] == base["verdict"] == "PASS" and v["per_window"] == base["per_window"]
    assert v["survivorship_label"] is True and v["survivorship_ic_min_units"] == {"W1": -0.198, "W2": -0.438}
    assert any("Survivorship-Etikett" in l and "W1=-0.198" in l and "W2=-0.438" in l and "report-only" in l for l in v["labels"])
    huge = _conserved_payload()
    huge["survivorship_ic_min_units"] = 50.0                                             # a float applies to every window
    assert gates.evaluate(huge)["verdict"] == "PASS"
    drop = _conserved_payload()
    drop["windows"]["W2"]["mean_ic"] = 0.001
    drop["survivorship_ic_min_units"] = {"W1": -3.0, "W2": -3.0}
    assert gates.evaluate(drop)["verdict"] == "DROP"                                      # and never rescues or kills a verdict


def test_dec89_run_attaches_the_registered_survivorship_label_to_mom1_and_rev_gap_only(dec89_run, dec87_run):
    _panel, _weekly, registered, report = dec89_run
    for eid, key in (("H-28_mom1", "mom1_diff_in_ic_min_units"), ("H-29_rev_gap", "rev_gap_diff_in_ic_min_units")):
        v = report["results"][eid]["verdict"]
        assert v["survivorship_label"] is True
        assert v["survivorship_ic_min_units"] == {wn: registered["windows"][wn]["survivorship"][key] for wn in ("W1", "W2")}
        assert any("Survivorship-Etikett" in l for l in v["labels"])
        assert report["results"][eid]["payload"]["survivorship_ic_min_units"] == v["survivorship_ic_min_units"]
        # report-only: the verdict and the gate flags equal those of the run WITHOUT the registered numbers
        ref = dec87_run[3]["results"][eid]["verdict"]
        assert v["verdict"] == ref["verdict"] and v["per_window"] == ref["per_window"]
        assert not ref.get("survivorship_label")
    for eid in ("H-28_mom2", "H-30_vol_rv"):                                              # locked entries carry none
        assert report["results"][eid]["verdict"]["survivorship_label"] is False


# ---- E3 (3): GL-012 label at hypothesis level ---------------------------------------------------

def test_dec89_hypothesis_with_all_variants_locked_reads_gl012_vor_dem_lauf(dec89_run):
    _panel, _weekly, registered, report = dec89_run
    hv = report["hypothesis_verdicts"]
    assert hv["H-30"]["verdict"] == "GL-012 vor dem Lauf" == run_mod.GL012_PRE_RUN_VERDICT
    assert hv["H-30"]["reasons"] == {"vol_rv": registered["hypotheses"]["H-30_vol_rv"]["reason"],
                                     "vol_beta": registered["hypotheses"]["H-30_vol_beta"]["reason"]}
    assert all(r in hv["H-30"]["label"] for r in hv["H-30"]["reasons"].values()) and hv["H-30"]["variants_pass"] == []
    assert sorted(hv["H-30"]["variants_locked"]) == ["vol_beta", "vol_rv"]
    # a hypothesis with a computed variant keeps PASS/DROP even if another variant is locked (H-28: mom1 computed, mom2 locked)
    assert hv["H-28"]["verdict"] in ("PASS", "DROP") and hv["H-28"]["variants_locked"] == ["mom2"]
    assert hv["H-28"]["reasons"] == {"mom2": registered["hypotheses"]["H-28_mom2"]["reason"]}
    assert hv["H-29"]["verdict"] in ("PASS", "DROP") and hv["H-29"]["reasons"] == {}
    # the ENTRY verdicts stay DROP with the GL-012 label (DEC-87 (J)), only the hypothesis level reads GL-012
    assert report["results"]["H-30_vol_rv"]["verdict"]["verdict"] == "DROP"


# ---- E3 (4): persistence null, both windows, 1.000 simulations ---------------------------------

def test_dec89_persistence_null_runs_in_both_windows(dec89_run):
    _panel, _weekly, _registered, report = dec89_run
    for eid in ("H-28_mom1", "H-29_rev_gap"):
        payload = report["results"][eid]["payload"]
        pn = payload["persistence_null"]
        assert set(pn) == {"W1", "W2"} and all(d["n_sims"] == 20 and d["seed"] == 53 for d in pn.values())
        assert payload["persistence_null_pass"] == all(d["pass"] for d in pn.values())      # conjunction over both windows
        assert math.isfinite(pn["W2"]["quantile95_registered_direction"]) and math.isfinite(pn["W2"]["real_mean_ic"])


def test_dec89_persistence_null_default_is_1000_simulations_in_each_window(tmp_path, monkeypatch):
    assert run_mod.PERSISTENCE_NULL_N_SIMS == 1000 == run_mod.resolve_rules({})["n_sims_persistence"]
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    calls: list[tuple] = []

    def stub(returns, alive, weeks, *, variants, convention, n_sims, seed):
        calls.append((weeks[0], n_sims, tuple(variants), seed))
        return {"variants": {v: {"quantile95_registered_direction": 0.0} for v in variants}}

    monkeypatch.setattr(nulls, "persistence_null", stub)
    reg = _registered_lean({"H-28_mom1": _MOM1})
    del reg["rules"]["n_sims_persistence"]
    run_mod.run_full(panel, weekly, reg)
    assert [c[1:] for c in calls] == [(1000, ("mom1",), 53), (1000, ("mom1",), 53)]       # one call per window, 1.000 sims
    assert calls[0][0] == "2024-07-01" and calls[1][0] >= "2025-07-01"                   # W1 then W2 (pre-DEC-89: W1 only, 200)


# ---- E3 (5): w_judged / block_len / level are read, used and pinned (T5) -----------------------

def test_dec89_t5_rules_are_pinned_against_the_code_constants(monkeypatch):
    rr = run_mod.resolve_rules({"rules": {}})
    assert rr["block_len"] == nulls.BLOCK_SIZE_WEEKS == 4 and rr["level"] == nulls.SELECTION_CEILING_ONE_SIDED_QUANTILE
    assert rr["bounce_spread"] is None and rr["seed"] == 53 and rr["bh_alpha"] == 0.10
    assert run_mod.resolve_rules({"rules": {"block_len": 4, "level": 0.9936, "bounce_spread": 0.003621}})["bounce_spread"] == 0.003621
    with pytest.raises(run_mod.ConstantPinError, match="block_len"):
        run_mod.resolve_rules({"rules": {"block_len": 5}})
    with pytest.raises(run_mod.ConstantPinError, match="level"):
        run_mod.resolve_rules({"rules": {"level": 0.99}})
    assert issubclass(run_mod.ConstantPinError, run_mod.RunAbort)                        # the CLI turns it into rc=1
    # the pin follows the code constant (looked up at call time), it is not a copy
    monkeypatch.setattr(nulls, "BLOCK_SIZE_WEEKS", 5)
    with pytest.raises(run_mod.ConstantPinError):
        run_mod.resolve_rules({"rules": {"block_len": 4}})
    assert run_mod.resolve_rules({"rules": {"block_len": 5}})["block_len"] == 5


def test_dec89_run_full_uses_block_len_and_level_and_refuses_a_yaml_that_moved_alone(tmp_path, monkeypatch):
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    reg = _registered_lean({"H-28_mom1": _MOM1})
    reg["rules"].update(block_len=5, level=0.99)
    with pytest.raises(run_mod.ConstantPinError):                                         # YAML moved, code did not
        run_mod.run_full({"symbols": []}, {"weeks": [], "returns": None, "alive": None}, reg)
    monkeypatch.setattr(nulls, "BLOCK_SIZE_WEEKS", 5)
    monkeypatch.setattr(nulls, "SELECTION_CEILING_ONE_SIDED_QUANTILE", 0.99)
    report = run_mod.run_full(panel, weekly, reg)                                         # both moved together: USED
    w = report["results"]["H-28_mom1"]["payload"]["windows"]["W1"]
    assert w["ci_detail"]["block_size"] == 5 and w["ci_detail"]["level"] == 0.99
    assert w["block_permutation_detail"]["block_size"] == 5
    assert report["parameters"]["block_size"] == 5 and report["parameters"]["null_quantile_level"] == 0.99
    assert report["registered_inputs"]["block_len"] == 5 and report["registered_inputs"]["level"] == 0.99


def test_dec89_w_judged_is_read_used_and_pinned(dec89_run):
    panel, weekly, registered, report = dec89_run
    for wn in ("W1", "W2"):
        reg_wj = registered["windows"][wn]["w_judged"]
        assert report["registered_inputs"]["w_judged"][wn] == reg_wj
        for eid in ("H-28_mom1", "H-29_rev_gap"):
            assert report["results"][eid]["payload"]["windows"][wn]["se_detail"]["w_judged"] == reg_wj   # the SE denominator
    wrong = copy.deepcopy(registered)
    wrong["windows"]["W1"]["w_judged"] += 1
    with pytest.raises(run_mod.ConstantPinError, match=r"windows\.W1\.w_judged"):
        run_mod.run_full(panel, weekly, wrong)
    alive, weeks = np.ones((10, 12), dtype=bool), [str(i) for i in range(10)]
    reg = {"windows": {"W1": {"w_judged": 9}}}
    c = run_mod.registered_window_constants(reg, "W1", alive, weeks)
    assert c["w_judged"] == 9 == c["w_judged_window"] and c["ceiling"] is None and c["q_driftfree"] == {}
    assert run_mod.registered_window_constants({"windows": {"W1": {}}}, "W1", alive, weeks)["w_judged"] == 9
    with pytest.raises(run_mod.ConstantPinError):
        run_mod.registered_window_constants({"windows": {"W1": {"w_judged": 8}}}, "W1", alive, weeks)


def test_dec89_t5_constants_pin_lists_the_new_fields():
    pin = run_mod.registered_constants_pin(_strict_registered())
    assert pin["rules"] == {"bounce_spread": BOUNCE_SPREAD, "block_len": 4, "level": 0.9936}
    for wn in ("W1", "W2"):
        assert pin[wn]["bounce_sigma_true"] == BOUNCE_SIGMA[wn] and pin[wn]["survivorship"] == _SURV[wn]
        assert pin[wn]["w_judged"] == 52


# ---- E3 (7): the run's Markdown report ---------------------------------------------------------

def test_dec89_run_markdown_reports_bounce_parameters_survivorship_and_the_gl012_hypothesis(dec89_run, tmp_path):
    _panel, _weekly, registered, report = dec89_run
    arts = run_mod.write_run_artifacts(tmp_path / "out", copy.deepcopy(report))["artifacts"]
    assert "wp13_run_md" in arts and arts["wp13_run_md"]["sha256"] == panel_load.sha256_file(arts["wp13_run_md"]["path"])
    md = Path(arts["wp13_run_md"]["path"]).read_text(encoding="utf-8")
    assert md.isascii() and md == run_mod.render_run_markdown({k: v for k, v in report.items() if k != "_l_window_sealed"})
    assert "## Bounce-Fixture" in md and "0.003621" in md                                 # the registered spread
    for wn in ("W1", "W2"):
        assert f"{wn}: {BOUNCE_SIGMA[wn]:.6f}" in md                                      # the registered sigma_true per window
    assert "| H-29_rev_gap | W1 |" in md and "IC_bounce" in md
    assert "## Survivorship-Etikett" in md and "-0.198" in md and "-0.579" in md
    assert "GL-012 vor dem Lauf" in md and registered["hypotheses"]["H-30_vol_rv"]["reason"] in md
    assert "## Persistenz-Null" in md and "wp13_run_L_window_sealed" not in md           # the sealed L window is not in the report


# ============================================================================
# DEC-89 E2: the positive control in production configuration (PRD 3.3.8)
# ============================================================================

_PC_AS_OF = date(2027, 1, 1)


def _build_pc_union_tree(tmp_path: Path, k: int = 400):
    """An on-disk survivors + delisted tree in the shape of the real union panel: BTCUSDT and ``k`` survivors (every
    fifth lists late, between 2024 and 2025), eight symbols delisted between 2024-09 and 2026-03 (so K_t varies and
    delisting weeks occur inside W1 and W2), built with the same WP-12b fixture writers the other CLI end-to-end tests
    use. Returns ``(surv_base, del_base, delisting_dates_path)``."""
    surv_base, del_base = tmp_path / "panel_1d", tmp_path / "panel_1d_delisted"
    surv_manifest, del_manifest = surv_base / "panel_manifest.sqlite", del_base / "panel_manifest.sqlite"
    full_start, full_end = date(2021, 1, 1), date(2026, 6, 30)
    for i, sym in enumerate(["BTCUSDT"] + [f"SYM{j:03d}USDT" for j in range(k)]):
        start = date(2024, 1, 1) + timedelta(days=(i * 11) % 600) if i % 5 == 3 else full_start
        _write_full_history(surv_base, surv_manifest, sym, _closes(start, full_end, seed=i + 1), as_of_date=full_end)
    delisted = {}
    for n in range(8):
        d = date(2024, 9, 2) + timedelta(days=80 * n)
        _write_full_history(del_base, del_manifest, f"DEL{n}USDT", _closes(full_start, d, seed=500 + n), as_of_date=d)
        delisted[f"DEL{n}USDT"] = {"delist_date": d.isoformat(), "announcement_id": f"ann-del{n}", "source": "delisting_ms"}
    dd = delisted_panel.write_delisting_dates_json(del_base, delisted)
    return surv_base, del_base, Path(dd["path"])


def _pc_registered(shape, symbols, *, n_reps_null: int = 40, rho_f: float = 0.09, beta_sd: float = 0.6) -> dict:
    """A registered YAML for the control with FROZEN constants produced by ``nulls.run_configuration_null`` (the Vorlauf
    function) on a signal-free factor panel of the window's shape -- exactly what the Vorlauf freezes -- plus IC_min from
    the window's real K_t series, the bounce parameters and the survivorship numbers. Normalised to plain JSON types."""
    entries = {
        "H-28_mom1": dict(_MOM1),
        "H-28_mom2": {"hypothesis": "H-28", "variant": "mom2", "direction": "positive", "status": "gl012_pre_run",
                      "reason": "MDE80 > IC_prior (Test)"},
        "H-29_rev_gap": dict(_REV_GAP),
        "H-30_vol_rv": {"hypothesis": "H-30", "variant": "vol_rv", "direction": "negative", "outcome": "vol_weighted",
                        "status": "gl012_pre_run", "reason": "H-30-Feasibility (Test)"},
    }
    reg = {"hypotheses": entries, "windows": {}, "beta_control": {"method": "fm_neutral_8w", "beta_window_weeks": 8},
           "rules": {"seed": 53, "n_reps": n_reps_null, "n_reps_bootstrap": 200, "n_reps_permutation": 200,
                     "block_len": 4, "level": 0.9936, "bounce_spread": BOUNCE_SPREAD}}
    rng = np.random.default_rng(1)
    for wn, (a, b) in {"W1": ("2024-07-01", "2025-06-30"), "W2": ("2025-07-01", "2026-06-30")}.items():
        sl = prelaunch_module.slice_window(shape["weeks"], a, b, shape["alive"], shape["alive"])    # ("returns", "alive")
        fl = nulls.analytic_permutation_floor(sl["alive"], sl["weeks"])
        thr = nulls.ic_threshold(fl["e_floor"], 1.0, fl["w_judged"])
        noise = nulls.simulate_factor_panel(len(sl["weeks"]), len(symbols), sigma_f=0.06, sigma_e=0.12, rho_f=0.0,
                                            drift_f=0.0, rng=rng, beta_sd=beta_sd,
                                            market_index=symbols.index("BTCUSDT"))["returns"]
        c = nulls.run_configuration_null(noise, sl["alive"], symbols, method="fm_neutral_8w", rho_f=rho_f,
                                         beta_sd=beta_sd, n_reps=n_reps_null, seed=53)["constants"]
        reg["windows"][wn] = {
            "start": a, "end": b, "ic_min_capped": {v: thr for v in characteristics.VARIANT_NAMES},
            "w_judged": fl["w_judged"], "bounce_sigma_true": BOUNCE_SIGMA[wn], "survivorship": copy.deepcopy(_SURV[wn]),
            "calibration": _window_calibration(rho_f, beta_sd),
            # DEC-89 E2 Nachtrag: the scales of the null world the constants above were simulated in
            "null_scales": {"sigma_f": 0.06, "sigma_e_used": 0.12},
            "ceiling_method_stress": c["ceiling_method_stress"],
            "res_quantile_driftfree": c["res_quantile_driftfree"], "res_quantile_drifting": c["res_quantile_drifting"]}
    return json.loads(json.dumps(reg))


@pytest.fixture(scope="module")
def pc_tree(tmp_path_factory):
    """The on-disk union tree, its real loader output reduced to the SHAPE the control reads (week grid, PIT alive mask,
    ``returns_valid``, symbol order), the registered YAML (without data fingerprints) and the panel's V9 fingerprints."""
    tmp = tmp_path_factory.mktemp("pc_tree")
    surv_base, del_base, dd_path = _build_pc_union_tree(tmp)
    panel = panel_load.load_panel_union(
        surv_base, surv_base / "panel_manifest.sqlite", del_base, del_base / "panel_manifest.sqlite",
        year_start=2021, year_end=2026, as_of=_PC_AS_OF, delisting_dates_path=dd_path)
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    shape = {"weeks": list(weekly["weeks"]), "alive": weekly["alive"], "returns_valid": weekly["returns_valid"]}
    symbols = list(panel["symbols"])
    fps = WP13.data_fingerprints(_pc_ns(tmp, panel_base=str(surv_base), delisted_base=str(del_base)), panel, del_base,
                                 dd_path, _PC_AS_OF)
    return {"tmp": tmp, "surv_base": surv_base, "del_base": del_base, "shape": shape, "symbols": symbols,
            "registered": _pc_registered(shape, symbols), "fps": fps}


@pytest.fixture(scope="module")
def pc_setup(pc_tree):
    return pc_tree["shape"], pc_tree["symbols"], pc_tree["registered"]


@pytest.fixture(scope="module")
def pc_report(pc_setup):
    """The control over the three registered seeds, with EVERY null function patched to explode: the control uses only
    the frozen constants of the YAML (no factor-null replicates, no persistence null, no permutation null)."""
    shape, symbols, registered = pc_setup

    def boom(*_a, **_k):
        raise AssertionError("the positive control recomputed a null (it must use the frozen YAML constants only)")

    with pytest.MonkeyPatch.context() as mp:
        for name in ("run_configuration_null", "beta_controlled_factor_null", "factor_preserving_null",
                     "persistence_null", "block_permutation_pvalue", "block_permutation_null_draws"):
            mp.setattr(nulls, name, boom)
        return pc_mod.run_positive_control(shape, symbols, registered, registered_sha256="r" * 64)


def test_dec89_pc_passes_on_a_production_shaped_fixture_panel(pc_report, pc_setup):
    """DEC-89 E2: on the real-shaped panel the control is BESTANDEN -- H-28_mom1 and H-29_rev_gap PASS in all three seeds
    (injected IC 0.06 through the complete gate evaluation against the FROZEN constants), the negative control (injected
    signal 0, otherwise identical) gives no PASS in any seed; locked entries are skipped."""
    _shape, _symbols, registered = pc_setup
    r = pc_report
    assert r["bestanden"] is True and r["line"] == "Positivkontrolle BESTANDEN"
    assert r["seeds"] == [53, 54, 55] and r["injected_ic"] == 0.06
    c = r["criteria"]
    assert c["positive_all_pass"] and c["negative_no_pass"] and c["seeds_registered"] and not c["missing_or_locked_required_entries"]
    assert set(r["skipped"]) == {"H-28_mom2", "H-30_vol_rv"} and r["uncovered"] == []
    assert "persistence_null" in " ".join(r["not_computed"]) and r["registered_sha256"] == "r" * 64
    for seed in ("53", "54", "55"):
        for eid, direction in (("H-28_mom1", "positive"), ("H-29_rev_gap", "negative")):
            pos, neg = r["runs"][seed]["positive"][eid], r["runs"][seed]["negative"][eid]
            assert pos["verdict"] == "PASS", (seed, eid, pos["labels"])
            assert neg["verdict"] != "PASS", (seed, eid, neg["labels"])
            for wn in ("W1", "W2"):
                p, n = pos["windows"][wn], neg["windows"][wn]
                sign = 1.0 if direction == "positive" else -1.0
                assert 0.035 < sign * p["mean_ic"] < 0.09 and abs(n["mean_ic"]) < 0.03 < sign * p["mean_ic"]
                assert p["gates"]["window_pass"] and not n["gates"]["window_pass"]
                # the FROZEN constants of the YAML are what the gate judged against (nothing recomputed)
                wcfg = registered["windows"][wn]
                v = "mom1" if eid == "H-28_mom1" else "rev_gap"
                q = [wcfg["res_quantile_driftfree"][v], wcfg["res_quantile_drifting"][v]]
                assert p["res_quantile_binding"] == (max(q) if direction == "positive" else min(q))
                assert p["selection_ceiling_mean_of_max"] == wcfg["ceiling_method_stress"] < p["ic_min_capped"] == wcfg["ic_min_capped"][v]
                assert p["residualized_mean_ic"] * sign > sign * p["res_quantile_binding"]    # the beta-controlled IC clears it
    # labels: the registered survivorship numbers ride along, and the bounce parameters are the registered ones
    rev = r["runs"]["53"]["positive"]["H-29_rev_gap"]
    assert rev["survivorship_label"] is True and rev["survivorship_ic_min_units"] == {
        wn: _SURV[wn]["rev_gap_diff_in_ic_min_units"] for wn in ("W1", "W2")}
    shape = pc_setup[0]
    for wn in ("W1", "W2"):
        sl = prelaunch_module.slice_window(shape["weeks"], registered["windows"][wn]["start"], registered["windows"][wn]["end"])
        alive_w = shape["alive"][sl["lo"]:sl["hi"]]
        bf = run_mod.bounce_fixture_ic(alive_w.shape[0], max(int(np.median(alive_w.sum(axis=1))), 10),
                                       spread=BOUNCE_SPREAD, sigma_true=BOUNCE_SIGMA[wn], seed=53)
        assert rev["windows"][wn]["bounce_ic"] == bf["ic_bounce"]


def test_dec89_pc_takes_no_real_returns(pc_setup):
    """DEC-89 E2: nothing real is an outcome -- the control has no ``returns`` (nor ``weekly``/``panel``) parameter, and
    the shape it needs holds only labels and booleans."""
    params = inspect.signature(pc_mod.run_positive_control).parameters
    assert not {"returns", "weekly", "panel"} & set(params) and list(params)[:3] == ["shape", "symbols", "registered"]
    shape, symbols, _reg = pc_setup
    assert set(shape) == {"weeks", "alive", "returns_valid"} and shape["alive"].dtype == bool
    sig = inspect.signature(pc_mod.synthesize_window_returns)
    assert "returns" not in sig.parameters and "real" not in " ".join(sig.parameters)


def test_dec89_pc_world_scale_parameters_come_only_from_the_registered_yaml(pc_setup):
    """DEC-89 E2 Nachtrag: the synthetic world uses the registered null scales (``null_scales``)."""
    _shape, _symbols, registered = pc_setup
    for wn in ("W1", "W2"):
        w = pc_mod.window_world(registered, wn)
        st = registered["windows"][wn]["calibration"]["stress"]
        assert w["rho_f"] == st["rho_f"] and w["beta_sd"] == st["beta_sd_calibrated"] and w["drift_f"] == 0.0
        # DEC-89 E2 Nachtrag: the world's scales ARE the calibrated null's (measured sigma_f, idiosyncratic sigma_e_used),
        # not a share inversion from the bounce vol (that gave a weaker factor world than the stress null)
        assert w["sigma_e"] == registered["windows"][wn]["null_scales"]["sigma_e_used"]
        assert w["sigma_f"] == registered["windows"][wn]["null_scales"]["sigma_f"]
        assert w["sigma_g"] == pytest.approx(pc_mod.SECTOR_SHOCK_REL * w["sigma_e"])
        assert w["sigma_tot"] == pytest.approx(math.sqrt(w["sigma_e"] ** 2 + w["sigma_g"] ** 2 + (w["beta_sd"] * w["sigma_f"]) ** 2))
    bad = copy.deepcopy(registered)
    del bad["windows"]["W1"]["calibration"]["stress"]["target_factor_share"]
    with pytest.raises(run_mod.RegisteredSchemaError, match="target_factor_share"):
        pc_mod.window_world(bad, "W1")
    bad = copy.deepcopy(registered)
    bad["windows"]["W2"]["null_scales"]["sigma_e_used"] = None
    with pytest.raises(run_mod.RegisteredSchemaError, match="null_scales"):
        pc_mod.window_world(bad, "W2")
    bad = copy.deepcopy(registered)
    del bad["windows"]["W1"]["null_scales"]
    with pytest.raises(run_mod.RegisteredSchemaError, match="null_scales"):
        pc_mod.window_world(bad, "W1")


def test_dec89_pc_synthetic_world_carries_the_injected_signal_and_the_negative_control_differs_only_by_it(pc_setup):
    shape, symbols, registered = pc_setup
    alive, valid = shape["alive"], shape["returns_valid"]
    world = pc_mod.window_world(registered, "W1")
    pos = pc_mod.synthesize_window_returns(alive, valid, symbols, world, seed=53, window_index=0, signal_ic=0.06)
    neg = pc_mod.synthesize_window_returns(alive, valid, symbols, world, seed=53, window_index=0, signal_ic=0.0)
    m = symbols.index("BTCUSDT")
    assert np.array_equal(pos["factor"], neg["factor"]) and np.array_equal(pos["beta"], neg["beta"])   # same stream, same base
    assert pos["coefficient"] > 0.0 and neg["coefficient"] == 0.0
    assert np.array_equal(pos["returns"][:, m], neg["returns"][:, m]) and np.array_equal(pos["returns"][0], neg["returns"][0])
    t_inj = int(np.argmax((alive & valid).sum(axis=1) >= 10)) + 3         # a week with >= 10 members and two weeks of history
    assert not np.array_equal(pos["returns"][t_inj], neg["returns"][t_inj])                            # the injection acts
    # the real masks shape the synthetic arrays: zero where no return is computable, NaN in the estimation array there
    for syn in (pos, neg):
        assert np.all(syn["returns"][~valid] == 0.0) and np.array_equal(np.isnan(syn["returns_est"]), ~valid)
        assert np.array_equal(syn["returns_est"][valid], syn["returns"][valid])
    assert pos["beta"][m] == 1.0 and np.allclose(pos["returns"][1:, m], pos["factor"][1:])             # market column := factor
    # realised cross-sectional ICs on the full grid: mom1 ~ +0.06, rev_gap ~ -0.06 (the PRD fixture), none without the injection
    def mean_ic(char, ret):
        return ic.weekly_ic_series(char, ret, alive, convention="close_at_last")["mean_ic"]

    mom_pos = mean_ic(characteristics.momentum_characteristic(pos["returns"], trail_win=1), pos["returns"])
    rev_pos = mean_ic(characteristics.reversal_gap_characteristic(pos["returns"]), pos["returns"])
    mom_neg = mean_ic(characteristics.momentum_characteristic(neg["returns"], trail_win=1), neg["returns"])
    rev_neg = mean_ic(characteristics.reversal_gap_characteristic(neg["returns"]), neg["returns"])
    assert 0.04 < mom_pos < 0.08 and -0.08 < rev_pos < -0.04, (mom_pos, rev_pos)
    assert abs(mom_neg) < 0.025 and abs(rev_neg) < 0.025, (mom_neg, rev_neg)
    # deterministic, and another seed gives another world
    again = pc_mod.synthesize_window_returns(alive, valid, symbols, world, seed=53, window_index=0, signal_ic=0.06)
    other = pc_mod.synthesize_window_returns(alive, valid, symbols, world, seed=54, window_index=0, signal_ic=0.06)
    assert np.array_equal(again["returns"], pos["returns"]) and not np.array_equal(other["returns"], pos["returns"])
    # the synthetic turnover is independent of the returns' stream and zero off the alive mask
    t1 = pc_mod.synthetic_turnover_trail(alive, seed=53, window_index=0)
    assert np.array_equal(t1, pc_mod.synthetic_turnover_trail(alive, seed=53, window_index=0)) and t1.shape == alive.shape


def test_dec89_pc_fails_when_the_injected_signal_is_too_weak(pc_setup):
    """DEC-89 E2 teeth: a signal far below IC_min is not found -> NICHT BESTANDEN (the positive control can fail)."""
    shape, symbols, registered = pc_setup
    r = pc_mod.run_positive_control(shape, symbols, registered, seeds=(53,), signal_ic=0.004)
    assert r["criteria"]["positive_all_pass"] is False and r["bestanden"] is False
    assert r["line"] == "Positivkontrolle NICHT BESTANDEN"
    assert r["runs"]["53"]["positive"]["H-28_mom1"]["verdict"] == "DROP"


def test_dec89_pc_fails_with_a_broken_gate(pc_setup, monkeypatch):
    """DEC-89 E2 teeth: (a) a frozen ceiling above IC_min (the GL-012 pre-verdict kill) makes the positive control
    unpassable; (b) a gate that says PASS to everything makes the NEGATIVE control fail -- either way NICHT BESTANDEN."""
    shape, symbols, registered = pc_setup
    broken = copy.deepcopy(registered)
    for wn in ("W1", "W2"):
        broken["windows"][wn]["ceiling_method_stress"] = 1.0
    r = pc_mod.run_positive_control(shape, symbols, broken, seeds=(53,))
    assert r["criteria"]["positive_all_pass"] is False and r["bestanden"] is False
    assert any("GL-012" in l for l in r["runs"]["53"]["positive"]["H-28_mom1"]["labels"])
    orig = gates.evaluate
    monkeypatch.setattr(gates, "evaluate", lambda payload: dict(orig(payload), verdict="PASS"))
    r2 = pc_mod.run_positive_control(shape, symbols, registered, seeds=(53,))
    assert r2["criteria"]["positive_all_pass"] is True and r2["criteria"]["negative_no_pass"] is False
    assert r2["bestanden"] is False and r2["line"] == "Positivkontrolle NICHT BESTANDEN"


def test_dec89_pc_requires_the_registered_entries_and_the_registered_seeds(pc_setup):
    shape, symbols, registered = pc_setup
    locked = copy.deepcopy(registered)
    locked["hypotheses"]["H-28_mom1"].update(status="gl012_pre_run", reason="Test: gesperrt")
    r = pc_mod.run_positive_control(shape, symbols, locked, seeds=(53,))
    assert r["criteria"]["missing_or_locked_required_entries"] == ["H-28_mom1"] and r["bestanden"] is False
    assert "H-28_mom1" in r["skipped"] and set(r["runs"]["53"]["positive"]) == {"H-29_rev_gap"}
    wrong_dir = copy.deepcopy(registered)
    wrong_dir["hypotheses"]["H-29_rev_gap"]["direction"] = "positive"
    assert pc_mod.run_positive_control(shape, symbols, wrong_dir, seeds=(53,))["criteria"]["missing_or_locked_required_entries"] == ["H-29_rev_gap"]
    # a control over other seeds than 53, 54, 55 is an exploration, never BESTANDEN -- even if every verdict is right
    r2 = pc_mod.run_positive_control(shape, symbols, registered, seeds=(53,))
    assert r2["criteria"]["positive_all_pass"] and r2["criteria"]["negative_no_pass"]
    assert r2["criteria"]["seeds_registered"] is False and r2["bestanden"] is False and "weichen" in r2["criteria"]["note"]
    # another computed entry (mom2 unlocked) cannot be injected: listed as not covered
    more = copy.deepcopy(registered)
    del more["hypotheses"]["H-28_mom2"]["status"], more["hypotheses"]["H-28_mom2"]["reason"]
    assert pc_mod.run_positive_control(shape, symbols, more, seeds=(53,))["uncovered"] == ["H-28_mom2"]


def test_dec89_pc_refuses_incomplete_or_mismatching_registrations_loudly(pc_setup):
    shape, symbols, registered = pc_setup
    no_ceiling = copy.deepcopy(registered)
    no_ceiling["windows"]["W1"]["ceiling_method_stress"] = None
    with pytest.raises(run_mod.RegisteredSchemaError, match="ceiling_method_stress"):
        pc_mod.run_positive_control(shape, symbols, no_ceiling)
    no_spread = copy.deepcopy(registered)
    del no_spread["rules"]["bounce_spread"]
    with pytest.raises(run_mod.RegisteredSchemaError, match="bounce_spread"):
        pc_mod.run_positive_control(shape, symbols, no_spread)
    wrong_wj = copy.deepcopy(registered)
    wrong_wj["windows"]["W2"]["w_judged"] += 1
    with pytest.raises(run_mod.ConstantPinError, match="w_judged"):
        pc_mod.run_positive_control(shape, symbols, wrong_wj)
    wrong_block = copy.deepcopy(registered)
    wrong_block["rules"]["block_len"] = 6
    with pytest.raises(run_mod.ConstantPinError, match="block_len"):
        pc_mod.run_positive_control(shape, symbols, wrong_block)
    fp = copy.deepcopy(registered)
    fp["data_fingerprints"] = {"union_range_fingerprint": "ab" * 32, "delisting_dates_sha256": "cd" * 32}
    with pytest.raises(run_mod.DataFingerprintError):
        pc_mod.run_positive_control(shape, symbols, fp, observed_fingerprints={
            "union_range_fingerprint": "00" * 32, "delisting_dates_sha256": "cd" * 32})
    with pytest.raises(ValueError, match="shape inkonsistent"):
        pc_mod.run_positive_control({**shape, "alive": shape["alive"][:, :-1]}, symbols, registered)
    with pytest.raises(ValueError, match="BTCUSDT"):
        pc_mod.run_positive_control(shape, ["XUSDT" if s == "BTCUSDT" else s for s in symbols], registered)


def test_dec89_pc_is_deterministic_and_the_artifacts_round_trip(pc_setup, pc_report, tmp_path):
    shape, symbols, registered = pc_setup
    a = pc_mod.run_positive_control(shape, symbols, registered, seeds=(53,))
    b = pc_mod.run_positive_control(shape, symbols, registered, seeds=(53,))
    assert a["result_sha256"] == b["result_sha256"] and len(a["result_sha256"]) == 64
    assert a["runs"]["53"] == pc_report["runs"]["53"]                      # seed 53 is the same world in the 3-seed run
    arts = pc_mod.write_positive_control_artifacts(tmp_path / "pc_out", pc_report)["artifacts"]
    loaded = json.loads(Path(arts["wp13_positive_control_json"]["path"]).read_text(encoding="utf-8"))
    assert loaded["bestanden"] is True and loaded["line"] == "Positivkontrolle BESTANDEN"
    md = Path(arts["wp13_positive_control_md"]["path"]).read_text(encoding="utf-8")
    assert md.isascii() and md.splitlines()[0] == "Positivkontrolle BESTANDEN" and md.rstrip().splitlines()[-1] == "Positivkontrolle BESTANDEN"
    assert "| H-28_mom1 | positiv |" in md and "| H-29_rev_gap | negativ |" in md and "Synthetische Welten" in md
    for art in arts.values():
        assert art["sha256"] == panel_load.sha256_file(art["path"])
    with pytest.raises(ValueError, match="data/harvest"):
        pc_mod.write_positive_control_artifacts(Path("data/harvest/pc_should_not_write_here"), pc_report)


# ---- the CLI: START LOCK, pre-flight, panel loading, exit codes ---------------------------------

def _pc_ns(tmp_path, **over):
    base = dict(positive_control=True, run=False, prelaunch=False, registered="", registered_sha256="",
                panel_base=str(tmp_path / "panel_1d"), delisted_base=str(tmp_path / "panel_1d_delisted"),
                delisted_manifest="", delisting_dates="", start_year=2021, end_year=2026, as_of="2027-01-01",
                out=str(tmp_path / "pc_out"), seed=53, convention="close_at_last", allow_partial=False, seeds="53,54,55")
    base.update(over)
    return WP13.argparse.Namespace(**base)


def test_dec89_cli_positive_control_has_the_same_start_lock_as_run(tmp_path):
    reg = _minimal_registered_yaml(tmp_path)
    sha = run_mod.sha256_of_file(reg)
    for given in ("", "0" * 64):                                             # omitted / wrong hash: refused
        assert WP13.cmd_positive_control(_pc_ns(tmp_path, registered=str(reg), registered_sha256=given)) == 1
    assert WP13.cmd_positive_control(_pc_ns(tmp_path, registered=str(tmp_path / "none.yaml"), registered_sha256=sha)) == 1
    # the right hash passes the lock but there is no panel: rc=1 for a different reason, still no output directory
    assert WP13.cmd_positive_control(_pc_ns(tmp_path, registered=str(reg), registered_sha256=sha)) == 1
    assert not (tmp_path / "pc_out").exists()
    assert WP13.cmd_positive_control(_pc_ns(tmp_path, registered=str(reg), registered_sha256=sha, seeds="53,x")) == 1


def test_dec89_cli_main_positive_control_mode_flags(monkeypatch, tmp_path):
    reg = _minimal_registered_yaml(tmp_path)
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py", "--positive-control", "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit):                                          # --registered is mandatory
        WP13.main()
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py", "--positive-control", "--run", "--registered", str(reg),
                                     "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit):                                          # exactly one mode
        WP13.main()
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py", "--positive-control", "--emit-registered-template", "a", "b"])
    with pytest.raises(SystemExit):
        WP13.main()
    monkeypatch.setattr("sys.argv", ["wp13_xsec.py", "--positive-control", "--registered", str(reg), "--out", str(tmp_path / "o")])
    assert WP13.main() == 1                                                  # no --registered-sha256: the lock refuses (rc=1)
    assert not (tmp_path / "o").exists()


_REAL_LOADERS = (panel_load.load_panel_symbols, panel_load.load_panel_union, panel_load.weekly_returns_and_mask_union)


class _NoRealReturns(dict):
    """A ``weekly`` dict whose real ``returns`` explode on access: proof the control never reads them."""

    def __getitem__(self, key):
        if key == "returns":
            raise AssertionError("the positive control read the REAL weekly returns")
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key == "returns":
            raise AssertionError("the positive control read the REAL weekly returns")
        return super().get(key, default)


def _pc_cli_env(tmp_path, monkeypatch, pc_tree, *, mutate=None, fingerprints=None):
    """Registered YAML on disk (+ its sha256, with the panel's V9 fingerprints unless ``fingerprints`` overrides them) and
    spies around the REAL panel loaders of the on-disk tree; the real weekly ``returns`` the loader computes are wrapped so
    that any access explodes. Returns ``(namespace, loader_calls)``."""
    reg = copy.deepcopy(pc_tree["registered"])
    fps = pc_tree["fps"] if fingerprints is None else fingerprints
    reg["data_fingerprints"] = {k: fps[k] for k in ("union_range_fingerprint", "delisting_dates_sha256")}
    if mutate is not None:
        mutate(reg)
    path = tmp_path / "registered.yaml"
    path.write_text(yaml.safe_dump(reg, sort_keys=False), encoding="utf-8")
    calls: list[str] = []
    real_symbols, real_union, real_weekly = _REAL_LOADERS
    monkeypatch.setattr(panel_load, "load_panel_symbols", lambda *a, **k: calls.append("symbols") or real_symbols(*a, **k))
    monkeypatch.setattr(panel_load, "load_panel_union", lambda *a, **k: calls.append("union") or real_union(*a, **k))
    monkeypatch.setattr(panel_load, "weekly_returns_and_mask_union",
                        lambda *a, **k: calls.append("weekly") or _NoRealReturns(real_weekly(*a, **k)))
    ns = _pc_ns(tmp_path, registered=str(path), registered_sha256=run_mod.sha256_of_file(path),
                panel_base=str(pc_tree["surv_base"]), delisted_base=str(pc_tree["del_base"]), as_of=_PC_AS_OF.isoformat())
    return ns, calls


def test_dec89_cli_positive_control_end_to_end_bestanden_rc0(tmp_path, monkeypatch, pc_tree):
    """DEC-89 E2 CLI: lock -> pre-flight -> the REAL union-panel loader on the on-disk tree (its week grid, PIT alive mask
    and fingerprints only; the real weekly returns are wrapped to explode on access) -> V9 fingerprints checked against the
    YAML -> control -> ``wp13_positive_control.json/.md`` and the verdict line; rc 0 only because it is BESTANDEN."""
    ns, calls = _pc_cli_env(tmp_path, monkeypatch, pc_tree)
    assert WP13.cmd_positive_control(ns) == 0
    assert calls == ["symbols", "union", "weekly"]
    out = tmp_path / "pc_out"
    rep = json.loads((out / "wp13_positive_control.json").read_text(encoding="utf-8"))
    assert rep["bestanden"] is True and rep["line"] == "Positivkontrolle BESTANDEN" and rep["seeds"] == [53, 54, 55]
    assert rep["registered_sha256"] == ns.registered_sha256
    assert rep["data_fingerprints"]["union_range_fingerprint"] == pc_tree["fps"]["union_range_fingerprint"]
    assert rep["data_fingerprints"]["delisting_dates_sha256"] == pc_tree["fps"]["delisting_dates_sha256"]
    assert (out / "wp13_positive_control.md").read_text(encoding="utf-8").startswith("Positivkontrolle BESTANDEN")
    assert not list(out.glob("*L_window_sealed*")) and not list(out.glob("wp13_run*"))      # no run artifacts, nothing sealed
    # the loaded panel IS the fixture's shape: the window K_t the control used are the real alive counts
    shape = pc_tree["shape"]
    assert rep["criteria"]["bestanden"] and shape["alive"].shape[1] == len(pc_tree["symbols"]) > 400


def test_dec89_cli_positive_control_not_passed_is_rc3_and_still_reports(tmp_path, monkeypatch, pc_tree):
    def break_ceiling(reg):
        for wn in ("W1", "W2"):
            reg["windows"][wn]["ceiling_method_stress"] = 1.0

    ns, _calls = _pc_cli_env(tmp_path, monkeypatch, pc_tree, mutate=break_ceiling)
    ns.seeds = "53"                                                                   # fewer seeds: faster; verdict is a FAIL anyway
    assert WP13.cmd_positive_control(ns) == 3
    rep = json.loads((tmp_path / "pc_out" / "wp13_positive_control.json").read_text(encoding="utf-8"))
    assert rep["bestanden"] is False and rep["line"] == "Positivkontrolle NICHT BESTANDEN"
    assert (tmp_path / "pc_out" / "wp13_positive_control.md").read_text(encoding="utf-8").startswith("Positivkontrolle NICHT BESTANDEN")


def test_dec89_cli_positive_control_and_run_refuse_before_reading_the_panel(tmp_path, monkeypatch, pc_tree):
    """The mandatory-constant pre-flight (bounce spread, ...) refuses with rc=1 BEFORE a single panel call -- for
    ``--positive-control`` and ``--run`` alike -- and a fingerprint of another panel is rc=1 without output."""
    def no_spread(reg):
        del reg["rules"]["bounce_spread"]

    ns, calls = _pc_cli_env(tmp_path, monkeypatch, pc_tree, mutate=no_spread)
    assert WP13.cmd_positive_control(ns) == 1 and calls == [] and not (tmp_path / "pc_out").exists()
    ns_run = WP13.argparse.Namespace(**{**vars(ns), "run": True, "positive_control": False, "out": str(tmp_path / "run_out")})
    assert WP13.cmd_run(ns_run) == 1 and calls == [] and not (tmp_path / "run_out").exists()
    tmp2 = tmp_path / "second"
    tmp2.mkdir()
    ns2, calls2 = _pc_cli_env(tmp2, monkeypatch, pc_tree, fingerprints={"union_range_fingerprint": "00" * 32,
                                                                         "delisting_dates_sha256": pc_tree["fps"]["delisting_dates_sha256"]})
    assert WP13.cmd_positive_control(ns2) == 1
    assert calls2 == ["symbols", "union", "weekly"] and not (tmp2 / "pc_out").exists()
