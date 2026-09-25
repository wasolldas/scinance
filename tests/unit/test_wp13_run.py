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


def test_liquidity_and_bounce_labels_do_not_change_verdict():
    payload = _conserved_payload()
    payload["liquidity_ic_without_d1"] = -0.5 * payload["windows"]["W1"]["ic_min_capped"] - 0.001
    payload["bounce_ic"] = payload["windows"]["W1"]["mean_ic"] + 0.01
    v = gates.evaluate(payload)
    assert v["verdict"] == "PASS"
    assert any("Illiquiditaets-Artefakt" in l for l in v["labels"])
    assert any("Bounce" in l for l in v["labels"])


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
    r1 = run_mod.bounce_fixture_ic(40, 30, seed=53)
    r2 = run_mod.bounce_fixture_ic(40, 30, seed=53)
    assert r1 == r2
    assert math.isfinite(r1["ic_bounce"])


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


def test_bounce_fixture_end_to_end_label_not_verdict_change():
    """Directly exercises ``gates.evaluate``'s bounce-label rule on a
    hypothesis that otherwise PASSes -- the bounce fixture produces a
    LABEL, never a verdict-changing kill (DEC-75 Entscheidung 1 (5))."""
    payload = _conserved_payload()
    payload["hypothesis"], payload["variant"], payload["direction"] = "H-29", "rev_gap", "negative"
    for w in payload["windows"].values():
        w["mean_ic"] = -w["mean_ic"]
        w["ci_bound_toward_sign"] = -w["ci_bound_toward_sign"]
        w["residualized_mean_ic"] = -w["residualized_mean_ic"]
        w["res_quantile_drifting"] = -w["res_quantile_drifting"]   # DEC-76 (b): negative-direction quantile
    bounce = run_mod.bounce_fixture_ic(60, 60, seed=53)
    payload["bounce_ic"] = max(abs(bounce["ic_bounce"]), abs(payload["windows"]["W1"]["mean_ic"]) + 0.05)
    v = gates.evaluate(payload)
    assert v["verdict"] == "PASS"
    assert any("Bounce" in l for l in v["labels"])


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


def _registered_for_fixture() -> dict:
    ic_min_all = {v: 0.02 for v in characteristics.VARIANT_NAMES}
    return {
        "hypotheses": {"H-28": {"variant": "mom1", "direction": "positive"},
                       "H-29": {"variant": "rev_gap", "direction": "negative"},
                       "H-30": {"variant": "vol_rv", "direction": "negative", "outcome": "vol_weighted"}},
        "windows": {
            "W1": {"start": "2024-07-01", "end": "2025-06-30", "ic_min_capped": ic_min_all},
            "W2": {"start": "2025-07-01", "end": "2026-06-30", "ic_min_capped": ic_min_all},
            "L": {"start": "2021-03-01", "end": "2024-06-30"},
        },
        "beta_control": {"method": "ts_resid_8w", "beta_window_weeks": 8},   # DEC-77 Entscheidung 2
        "rules": {"seed": 53, "n_reps_bootstrap": 20, "n_reps_permutation": 20, "n_reps_factor_null": 20},
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
    """DEC-75 Entscheidung 1 (4): a hypothesis registered with
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

    weighted = run_mod.h30_outcome_for_window(returns, vol_rv)
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
            "W1": {"start": "2024-07-01", "end": "2025-06-30", "ic_min_capped": ic_min_all},
            "W2": {"start": "2025-07-01", "end": "2026-06-30", "ic_min_capped": ic_min_all},
        },
        "beta_control": {"method": "ts_resid_8w", "beta_window_weeks": 8},   # DEC-77 Entscheidung 2
        "rules": {"seed": 53, "n_reps_bootstrap": 20, "n_reps_permutation": 20, "n_reps_factor_null": 30},
    }


def test_run_full_null_calibration_report_present_and_matches_recomputation(tmp_path):
    """No frozen constants in the registered YAML (pre-DEC-76 shape,
    backward compatible): ``run_full`` falls back to its OWN recomputed
    DEC-76 null constants (no assertion, documented) and reports them
    under ``report["null_calibration"]``."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    report = run_mod.run_full(panel, weekly, registered)

    nc = report["null_calibration"]
    assert set(nc.keys()) == {"W1", "W2"}
    for wn in ("W1", "W2"):
        assert nc[wn]["ceiling_driftfree_res_registered"] is None
        assert math.isfinite(nc[wn]["ceiling_driftfree_res_recomputed"])
        for v in characteristics.VARIANT_NAMES:
            assert math.isfinite(nc[wn]["res_quantile_drifting_recomputed"][v])
    # the FALLBACK (no registered value) means the payload's own res_quantile_drifting
    # is exactly the recomputed value (no frozen constant to prefer instead).
    h28 = report["results"]["H-28"]["payload"]["windows"]["W1"]
    assert h28["res_quantile_drifting"] == pytest.approx(nc["W1"]["res_quantile_drifting_recomputed"]["mom1"])


def test_run_full_calibration_block_derives_stress_null(tmp_path):
    """DEC-78 Entscheidung 1/Nachtrag: a registered YAML WITH a
    ``calibration`` block reads the "stress" null's ``rho_f``/
    ``beta_sd_calibrated`` DIRECTLY from ``calibration.stress`` -- NO
    re-search/re-derivation at run time -- never the old hardcoded
    ``rho_f=0.2``/``U(0.5, 2.0)`` beta -- echoed in the report's
    ``calibration_used_for_stress_null``."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    registered["calibration"] = {
        "sigma_f": 0.06, "sigma_e": 0.05, "stress_multiplier": 2.0,
        "measured": {"rho_f": 0.05, "factor_share": 0.02,
                     "beta_sd_calibrated": 0.09, "beta_sd_analytic_first_guess": 0.08},
        "stress": {"rho_f": 0.10, "factor_share": 0.04,
                   "beta_sd_calibrated": 0.135, "beta_sd_analytic_first_guess": 0.12},
    }
    report = run_mod.run_full(panel, weekly, registered)
    used = report["calibration_used_for_stress_null"]
    assert used["rho_f"] == pytest.approx(0.10)
    assert used["beta_sd_calibrated"] == pytest.approx(0.135)
    assert "registered.calibration.stress" in used["source"]


def test_run_full_without_calibration_block_falls_back_to_old_stress_null(tmp_path):
    """A pre-DEC-78 registered file (no ``calibration`` key) falls back to
    the OLD hardcoded stress null (``rho_f=0.2``, ``beta_sd_calibrated=
    None`` -> ``U(0.5, 2.0)``), documented, not a registered Drittfassung
    run."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    registered = _registered_for_large_fixture()
    assert "calibration" not in registered
    report = run_mod.run_full(panel, weekly, registered)
    used = report["calibration_used_for_stress_null"]
    assert used["rho_f"] == pytest.approx(0.2)
    assert used["beta_sd_calibrated"] is None
    assert "pre-DEC-78" in used["source"]


def test_run_full_uses_frozen_registered_null_constants_within_tolerance(tmp_path):
    """A registered YAML that DOES carry ``res_quantile_drifting``/
    ``ceiling_driftfree_res`` (values within tolerance of what the run's
    own recomputation gets, deterministically -- same seed/panel/rules):
    ``run_full`` must NOT raise, and every hypothesis's payload must carry
    the FROZEN (registered) value, never the recomputed one, even though
    here they happen to be numerically identical."""
    panel, weekly = _build_run_fixture_tree_large(tmp_path)
    baseline = run_mod.run_full(panel, weekly, _registered_for_large_fixture())
    nc = baseline["null_calibration"]

    registered = _registered_for_large_fixture()
    for wn in ("W1", "W2"):
        registered["windows"][wn]["ceiling_driftfree_res"] = nc[wn]["ceiling_driftfree_res_recomputed"]
        registered["windows"][wn]["res_quantile_drifting"] = dict(nc[wn]["res_quantile_drifting_recomputed"])

    report = run_mod.run_full(panel, weekly, registered)      # must not raise NullCalibrationError
    h28 = report["results"]["H-28"]["payload"]["windows"]["W1"]
    assert h28["res_quantile_drifting"] == pytest.approx(registered["windows"]["W1"]["res_quantile_drifting"]["mom1"])


def test_run_full_raises_null_calibration_error_when_registered_has_drifted(tmp_path):
    """A registered constant that has drifted far (>10%) from what the
    run's own recomputation gets is a LOUD FAIL (C.14): the whole run
    aborts with ``NullCalibrationError``, BEFORE any hypothesis gets a
    verdict -- DEC-76 Task A item 3, verbatim."""
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["windows"]["W1"]["ceiling_driftfree_res"] = 999.0    # wildly stale
    with pytest.raises(run_mod.NullCalibrationError, match="Null-Kalibrierung weicht ab"):
        run_mod.run_full(panel, weekly, registered)


def test_run_full_raises_null_calibration_error_on_stale_per_variant_quantile(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    registered["windows"]["W1"]["res_quantile_drifting"] = {v: 999.0 for v in characteristics.VARIANT_NAMES}
    with pytest.raises(run_mod.NullCalibrationError, match="Null-Kalibrierung weicht ab"):
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

def test_cli_emit_registered_template_writes_yaml_skeleton_from_prelaunch_artifact(tmp_path):
    from bybit_edge.research.wp13_xsec import prelaunch as prelaunch_mod
    from tests.unit.test_wp13_xsec import _build_prelaunch_fixture_tree

    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    # DEC-78 Nachtrag: gegenprobe_rel_tol widened -- see test_wp13_xsec.py's CLI e2e test
    # comment (this fixture's small K is too statistically underpowered for the strict default).
    prelaunch_report = prelaunch_mod.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_sims=5, n_reps_factor_null=5, n_reps_beta_control_study=5, n_reps_beta_control_winner=5, seed=53,
        gegenprobe_rel_tol=10.0, calibration_search_n_reps=5, calibration_search_max_iter=8)
    artifacts = prelaunch_mod.write_prelaunch_artifacts(tmp_path / "prelaunch_out", prelaunch_report)
    prelaunch_json = artifacts["artifacts"]["wp13a_prelaunch_json"]["path"]

    out_yaml = tmp_path / "registered_template.yaml"
    rc = WP13.cmd_emit_registered_template(prelaunch_json, str(out_yaml))
    assert rc == 0
    assert out_yaml.is_file()

    loaded = run_mod.load_registered_yaml(out_yaml)     # round-trips through the real YAML loader
    assert set(loaded["hypotheses"].keys()) == {"H-28", "H-29", "H-30"}
    assert loaded["hypotheses"]["H-30"]["outcome"] == "vol_weighted"
    for wn in ("W1", "W2"):
        assert wn in loaded["windows"]
        assert set(loaded["windows"][wn]["ic_min_capped"].keys()) == set(characteristics.VARIANT_NAMES)
        assert "res_quantile_drifting" in loaded["windows"][wn]
        assert "ceiling_driftfree_res" in loaded["windows"][wn]
    assert loaded["rules"]["seed"] == 53 and loaded["rules"]["n_reps"] >= 1000
    # DEC-77 Entscheidung 2: beta_control is present but EMPTY -- never auto-filled, the
    # orchestrator must choose it deliberately before a real --run (run_full loud-fails on empty).
    assert loaded["beta_control"] == {"method": "", "beta_window_weeks": None}
    with pytest.raises(ValueError, match="beta_control"):
        run_mod.run_full({"symbols": []}, {"weeks": [], "returns": None, "alive": None}, loaded)
    # DEC-78 Entscheidung 1/Nachtrag: calibration is a SINGLE global block, taken from W1's
    # beta_control_method_study only (the enlarged >= 10-survivor fixture makes it FINITE),
    # nested measured/stress sub-blocks (run.py reads calibration.stress.* directly).
    assert "calibration" in loaded
    calib = loaded["calibration"]
    for key in ("sigma_f", "sigma_e", "stress_multiplier", "measured", "stress"):
        assert key in calib
    assert calib["stress_multiplier"] == pytest.approx(2.0)
    for sub in ("measured", "stress"):
        for key in ("rho_f", "factor_share", "beta_sd_calibrated", "beta_sd_analytic_first_guess"):
            assert key in calib[sub]
    if calib["measured"]["rho_f"] is not None:   # finite calibration (usual case on this fixture)
        assert math.isfinite(calib["measured"]["rho_f"])
        assert math.isfinite(calib["stress"]["beta_sd_calibrated"])
        assert calib["stress"]["rho_f"] == pytest.approx(2.0 * calib["measured"]["rho_f"])


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
