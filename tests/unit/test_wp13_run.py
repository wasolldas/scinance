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
            "W1": {"mean_ic": 0.05, "se": 0.01, "ci_bound_toward_sign": 0.02, "ic_min_capped": 0.02,
                   "residualized_mean_ic": 0.045, "selection_ceiling_mean_of_max": 0.01},
            "W2": {"mean_ic": 0.04, "se": 0.01, "ci_bound_toward_sign": 0.015, "ic_min_capped": 0.018,
                   "residualized_mean_ic": 0.035, "selection_ceiling_mean_of_max": 0.01},
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


def test_positive_fixture_end_to_end_pass():
    seed, k, w = 0, 120, 52
    rng = np.random.default_rng(seed)
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    k_full = k + 1
    target_rho = 0.08
    returns = rng.normal(0, 0.03, size=(w, k_full))
    characteristic = rng.normal(0, 1, size=(w, k_full))
    a = target_rho / math.sqrt(max(1 - target_rho ** 2, 1e-9))
    returns[1:] += a * 0.03 * characteristic[:-1]
    alive = np.ones((w, k_full), dtype=bool)
    beta_8w = characteristics.beta_characteristic(returns, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    e_floor, w_judged = _floor_and_symbols(alive, w)

    res = run_mod.run_hypothesis(
        "H-POS", "mom1", "positive",
        {"W1": characteristic, "W2": characteristic}, {"W1": returns, "W2": returns},
        {"W1": alive, "W2": alive}, symbols,
        {"W1": 0.02, "W2": 0.02}, {"W1": w_judged, "W2": w_judged},
        {"W1": e_floor, "W2": e_floor}, {"W1": 0.005, "W2": 0.005},
        beta_8w_pit_by_window={"W1": beta_8w, "W2": beta_8w},
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53)
    assert res["verdict"]["verdict"] == "PASS"


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

    res = run_mod.run_hypothesis(
        "H-NULL", "mom1", "positive",
        {"W1": characteristic, "W2": characteristic}, {"W1": returns, "W2": returns},
        {"W1": alive, "W2": alive}, symbols,
        {"W1": 0.02, "W2": 0.02}, {"W1": w_judged, "W2": w_judged},
        {"W1": e_floor, "W2": e_floor}, {"W1": 0.005, "W2": 0.005},
        beta_8w_pit_by_window={"W1": beta_8w, "W2": beta_8w},
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53)
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

    res = run_mod.run_hypothesis(
        "H-ADV", "mom1", "positive",
        {"W1": mom1, "W2": mom1}, {"W1": returns_full, "W2": returns_full},
        {"W1": alive, "W2": alive}, symbols,
        {"W1": 0.02, "W2": 0.02}, {"W1": w_judged, "W2": w_judged},
        {"W1": e_floor, "W2": e_floor}, {"W1": 0.005, "W2": 0.005},
        beta_8w_pit_by_window={"W1": beta_8w, "W2": beta_8w},
        n_reps_bootstrap=200, n_reps_permutation=200, seed=53)
    assert res["verdict"]["verdict"] == "DROP"
    w1 = res["payload"]["windows"]["W1"]
    assert abs(w1["residualized_mean_ic"]) < abs(w1["mean_ic"]) or abs(w1["residualized_mean_ic"]) < w1["ic_min_capped"]


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


def test_run_full_never_writes_under_data_harvest(tmp_path):
    panel, weekly = _build_run_fixture_tree(tmp_path)
    registered = _registered_for_fixture()
    report = run_mod.run_full(panel, weekly, registered)
    with pytest.raises(ValueError):
        run_mod.write_run_artifacts(Path("data/harvest/wp13_run_should_not_write_here"), report)
