"""Unit tests for the H-13 tail-form-consistency mess-gate (c13_tailshape,
KAPITALFREI, DATA-GATED, F-TAILSHAPE).

Covers the registered H-13 requirements on synthetic fixtures only — the
hypothesis is DATA-GATED and no real-data run happens here:

  (a) xi_P recovery: POT + GPD-MLE on synthetic Pareto-tailed losses with a
      known true xi.
  (b) Hill cross-check consistency with the GPD fit on the same data.
  (c) Deribit instrument-name parser on several example strings.
  (d) SVI fit + Breeden-Litzenberger RND sanity (non-negative density, unit
      mass) on a synthetic smooth smile.
  (e) GPD-PWM recovery on a synthetic RND-excess-like sample with known xi_Q.
  (f) Deterministic D1/D2 snapshot-day selection: found + clean not-found.
  (g)/(h) Gate positive detection (consistent Delta_xi >= 0.15 both days) and
      null control (Delta_xi ~ 0).
  (i) capital_free=true + no cost-model identifiers anywhere in the module
      (AST identifier scan; narrative docstring mentions are fine).
  (j) End-to-end against a synthetic harvester tree (Bybit publicTrade +
      Deribit markprice.options): unlock found -> CLI rc=0 + full run rc=0,
      and a locked tree -> CLI + full run report a clean SKIP (rc=2).
"""
from __future__ import annotations

import ast
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import genpareto

from bybit_edge.research.c13_tailshape.driver import (
    check_unlock,
    run as driver_run,
)
from bybit_edge.research.c13_tailshape.options_loader import (
    DELTA_BAND,
    MIN_STRIKES,
    black76_delta,
    parse_instrument_name,
)
from bybit_edge.research.c13_tailshape.returns_tail import (
    MIN_EXCEEDANCES,
    POT_QUANTILE,
    fit_gpd_pot,
    hill_estimator,
)
from bybit_edge.research.c13_tailshape.snapshot_selection import (
    DayInfo,
    select_days,
)
from bybit_edge.research.c13_tailshape.stats import evaluate_gate
from bybit_edge.research.c13_tailshape.svi_rnd import (
    fit_svi,
    gpd_fit_pwm,
    rnd_from_svi,
    svi_total_variance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REPO_ROOT / "src" / "bybit_edge" / "research" / "c13_tailshape"

_MONTH_ABBR = {
    1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN",
    7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC",
}


# ----------------------------------------------------------------------------
# (a)/(b) xi_P recovery + Hill cross-check
# ----------------------------------------------------------------------------

def test_xi_p_recovery_on_known_pareto_tail():
    rng = np.random.default_rng(101)
    xi_true, beta_true = 0.25, 0.02
    # GPD is threshold-stable: exceedances of a GPD(xi, beta) sample over any
    # higher threshold are again GPD(xi, .) with the SAME shape, so a pure
    # GPD-distributed loss series lets fit_gpd_pot recover the true xi
    # directly (a clean, well-specified recovery test). quantile=0.99 (not
    # the registered 0.995 pipeline default — this test exercises the
    # generic POT/GPD-MLE machinery, not the pre-registered threshold choice)
    # with 1e6 samples gives ~10k exceedances, tight enough for a tolerant
    # +-0.05 recovery band (asymptotic SE(xi) ~ (1+xi)/sqrt(n_exc) ~ 0.0125).
    losses = genpareto.rvs(xi_true, loc=0.0, scale=beta_true, size=1_000_000, random_state=rng)
    returns = -losses
    fit = fit_gpd_pot(returns, quantile=0.99)
    assert fit.n_exceedances >= MIN_EXCEEDANCES
    assert fit.xi == pytest.approx(xi_true, abs=0.05)


def test_hill_estimator_consistent_with_gpd_on_same_data():
    rng = np.random.default_rng(101)
    xi_true, beta_true = 0.25, 0.02
    # The classical Hill estimator assumes a pure regularly-varying (power-law)
    # tail; on finite-beta GPD data it only converges to xi close to Hill's
    # asymptotic regime, i.e. at a HIGH threshold quantile (empirically
    # verified: at quantile=0.995 Hill carries a large positive bias here,
    # at quantile=0.999 with enough exceedances it tracks the GPD-MLE and the
    # true xi closely) — exactly why the registry treats Hill as a
    # NON-adjudicating cross-check, not a primary estimator.
    losses = genpareto.rvs(xi_true, loc=0.0, scale=beta_true, size=2_000_000, random_state=rng)
    returns = -losses
    fit = fit_gpd_pot(returns, quantile=0.999)
    xi_hill, k = hill_estimator(returns, quantile=0.999)
    assert k == fit.n_exceedances
    assert math.isfinite(xi_hill)
    # Hill is a genuinely different estimator (independent cross-check) —
    # both must recover the true xi, and thus be close to EACH OTHER.
    assert xi_hill == pytest.approx(xi_true, abs=0.08)
    assert abs(xi_hill - fit.xi) < 0.12


# ----------------------------------------------------------------------------
# (c) Instrument-name parser
# ----------------------------------------------------------------------------

def test_parse_instrument_name_examples():
    p = parse_instrument_name("BTC-27JUN26-70000-C")
    assert p is not None
    assert p.underlying == "BTC"
    assert p.expiry == date(2026, 6, 27)
    assert p.strike == 70000.0
    assert p.option_type == "C"

    p2 = parse_instrument_name("ETH-15AUG26-3500-P")
    assert p2 is not None
    assert p2.underlying == "ETH"
    assert p2.expiry == date(2026, 8, 15)
    assert p2.strike == 3500.0
    assert p2.option_type == "P"

    # 'd' decimal separator in the strike (documented for coin-margined names)
    p3 = parse_instrument_name("XRP_USDC-1JAN27-0d6535-P")
    assert p3 is not None
    assert p3.underlying == "XRP_USDC"
    assert p3.expiry == date(2027, 1, 1)
    assert p3.strike == pytest.approx(0.6535)
    assert p3.option_type == "P"

    # lower-case input must still parse (upper() applied internally)
    p4 = parse_instrument_name("btc-27jun26-70000-c")
    assert p4 is not None and p4.strike == 70000.0

    assert parse_instrument_name("garbage") is None
    assert parse_instrument_name("BTC-27FOO26-70000-C") is None  # bad month
    assert parse_instrument_name("BTC-27JUN26-70000-X") is None  # bad C/P


# ----------------------------------------------------------------------------
# (d) SVI fit + Breeden-Litzenberger RND sanity
# ----------------------------------------------------------------------------

def test_svi_fit_and_rnd_sanity():
    true_params = np.array([0.02, 0.15, -0.3, 0.0, 0.3])
    k = np.linspace(-0.6, 0.6, 25)
    w = svi_total_variance(true_params, k)
    fit_params, rms = fit_svi(k, w)
    assert rms < 1e-6, "exact synthetic smile must refit near-perfectly"
    # total variance must stay positive on and around the fitted smile
    assert np.all(svi_total_variance(fit_params, k) > 0)

    forward, t_years = 50_000.0, 30 / 365.0
    K, q = rnd_from_svi(fit_params, forward, t_years)
    assert np.all(np.isfinite(q))
    assert np.all(q >= 0.0), "clipped BL density must never be negative"
    mass = float(np.trapezoid(q, K))
    assert mass == pytest.approx(1.0, abs=1e-3), "RND must be re-normalised to unit mass"
    # sanity: the density should peak somewhere near the forward, not at a grid edge
    peak_idx = int(np.argmax(q))
    assert 0.2 * forward < K[peak_idx] < 4.0 * forward
    assert 0 < peak_idx < len(K) - 1


# ----------------------------------------------------------------------------
# (e) GPD-PWM recovery
# ----------------------------------------------------------------------------

def test_gpd_pwm_recovery_on_known_xi_q():
    rng = np.random.default_rng(202)
    xi_true, beta_true = 0.2, 5.0
    sample = genpareto.rvs(xi_true, loc=0.0, scale=beta_true, size=3000, random_state=rng)
    xi_est, beta_est = gpd_fit_pwm(sample)
    assert xi_est == pytest.approx(xi_true, abs=0.1)
    assert beta_est > 0


# ----------------------------------------------------------------------------
# (f) Deterministic D1/D2 selection
# ----------------------------------------------------------------------------

def test_select_days_finds_valid_pair():
    infos = [
        DayInfo(date="2026-01-01", n_strikes=15, rv_5d=0.01),
        DayInfo(date="2026-01-05", n_strikes=15, rv_5d=0.0105),  # gap too small
        DayInfo(date="2026-01-15", n_strikes=13, rv_5d=0.03),    # ratio+gap ok
    ]
    res = select_days(infos)
    assert res.found is True
    assert res.d1 == "2026-01-01"
    assert res.d2 == "2026-01-15"
    assert len(res.day_infos) == 3


def test_select_days_reports_not_found_cleanly():
    # gap too small AND ratio too small -> D1 found, no valid D2, no crash
    infos = [
        DayInfo(date="2026-01-01", n_strikes=15, rv_5d=0.01),
        DayInfo(date="2026-01-05", n_strikes=15, rv_5d=0.0105),
    ]
    res = select_days(infos)
    assert res.found is False
    assert res.d1 == "2026-01-01"
    assert res.d2 is None
    assert res.reason  # non-empty, explains why

    # no day meets the strike floor at all
    res2 = select_days([DayInfo(date="2026-01-01", n_strikes=3, rv_5d=0.01)])
    assert res2.found is False
    assert res2.d1 is None
    assert res2.d2 is None
    assert res2.reason

    # empty input -> clean not-found, never raises
    res3 = select_days([])
    assert res3.found is False


# ----------------------------------------------------------------------------
# (g)/(h) Gate positive detection + null control (evaluate_gate directly)
# ----------------------------------------------------------------------------

def test_gate_positive_detection_consistent_delta():
    cells = [
        {"symbol": "BTC", "day_label": "D1", "delta_xi": 0.22, "p_value": 0.01,
         "hill_contradiction": False},
        {"symbol": "BTC", "day_label": "D2", "delta_xi": 0.20, "p_value": 0.015,
         "hill_contradiction": False},
    ]
    gate = evaluate_gate(cells)
    assert gate["any_symbol_gate_met"] is True
    assert gate["per_symbol"]["BTC"]["symbol_gate_met"] is True
    assert gate["per_symbol"]["BTC"]["sign_consistent"] is True
    assert all(c["cell_criteria_met"] for c in cells)


def test_gate_null_control_small_delta():
    cells = [
        {"symbol": "BTC", "day_label": "D1", "delta_xi": 0.01, "p_value": 0.6,
         "hill_contradiction": False},
        {"symbol": "BTC", "day_label": "D2", "delta_xi": -0.02, "p_value": 0.7,
         "hill_contradiction": False},
    ]
    gate = evaluate_gate(cells)
    assert gate["any_symbol_gate_met"] is False
    assert gate["per_symbol"]["BTC"]["symbol_gate_met"] is False


def test_gate_hill_contradiction_blocks_positive_cell():
    # otherwise-qualifying cell, but the Hill cross-check contradicts the sign
    cells = [
        {"symbol": "BTC", "day_label": "D1", "delta_xi": 0.22, "p_value": 0.01,
         "hill_contradiction": True},
        {"symbol": "BTC", "day_label": "D2", "delta_xi": 0.20, "p_value": 0.015,
         "hill_contradiction": False},
    ]
    gate = evaluate_gate(cells)
    assert gate["any_symbol_gate_met"] is False
    assert cells[0]["cell_criteria_met"] is False


# ----------------------------------------------------------------------------
# (i) capital_free flag + no cost-model identifiers
# ----------------------------------------------------------------------------

def test_capital_free_flag_and_no_cost_identifiers(tmp_path):
    # empty tree -> immediate clean lock/SKIP; capital_free/data_gated must
    # still hold on this cheap payload path.
    payload = driver_run(tmp_path, ("BTC",))
    assert payload["capital_free"] is True
    assert payload["data_gated"] is True
    assert payload["skip"] is True
    assert payload["cells"] == []
    assert payload["gate"] is None

    forbidden = ("bps", "pnl", "sharpe", "friction", "edge_")
    for py in sorted(MODULE_DIR.glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        idents: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                idents.add(node.id)
            elif isinstance(node, ast.Attribute):
                idents.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                idents.add(node.name)
            elif isinstance(node, ast.arg):
                idents.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg:
                idents.add(node.arg)
        for ident in idents:
            low = ident.lower()
            for bad in forbidden:
                assert bad not in low, (
                    f"{py.name}: identifier {ident!r} suggests cost-model code "
                    f"(H-13 is KAPITALFREI)")


# ----------------------------------------------------------------------------
# (j) End-to-end synthetic harvester tree
# ----------------------------------------------------------------------------

def _day_ms(d: date) -> int:
    return int((d - date(1970, 1, 1)).days) * 86_400_000


def _write_parquet(d: Path, ts_list: list[int], payload_list: list[str]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        "ts_exchange_ms": pa.array(ts_list, pa.int64()),
        "payload_json": pa.array(payload_list, pa.string()),
    })
    pq.write_table(table, d / "data.parquet")


def _build_bybit_tree(
    base: Path, symbol: str, start: date, end: date, *,
    low_vol_window: tuple[date, date] | None = None,
    high_vol_window: tuple[date, date] | None = None,
    sigma_bg: float = 0.0008, sigma_low: float = 0.0003,
    sigma_high: float = 0.0020, ticks_per_day: int = 120, seed: int = 5,
) -> None:
    """Trailing 1-min tick tree (contiguous minutes per day, no cross-day glue).

    ``low_vol_window``/``high_vol_window`` let the test drive an explicit
    RV_5d ratio between two later snapshot days (each window covers the 5
    calendar days strictly before the corresponding snapshot day).
    """
    rng = np.random.default_rng(seed)
    price = 50_000.0
    d = start
    while d < end:
        if low_vol_window and low_vol_window[0] <= d <= low_vol_window[1]:
            sigma = sigma_low
        elif high_vol_window and high_vol_window[0] <= d <= high_vol_window[1]:
            sigma = sigma_high
        else:
            sigma = sigma_bg
        day_ms = _day_ms(d)
        ts_list, payloads = [], []
        for i in range(ticks_per_day):
            price *= float(np.exp(sigma * rng.standard_normal()))
            ts_list.append(day_ms + 60_000 * (i + 1))
            payloads.append(json.dumps({"price": f"{price:.6f}"}))
        part = (base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}"
                / f"date={d.isoformat()}")
        _write_parquet(part, ts_list, payloads)
        d += timedelta(days=1)


def _build_deribit_day(
    base: Path, symbol: str, snapshot_day: date, *,
    svi_params: np.ndarray, forward: float, dte: int = 30,
) -> int:
    """One markprice.options snapshot tick at 08:00 UTC with a full SVI smile.

    Returns the number of strikes surviving the tenor/delta filter (so the
    caller can assert it clears MIN_STRIKES).
    """
    t_years = dte / 365.0
    expiry = snapshot_day + timedelta(days=dte)
    mon = _MONTH_ABBR[expiry.month]
    yy = f"{expiry.year % 100:02d}"
    entries = []
    n_in_band = 0
    for m in np.linspace(-1.2, 1.2, 49):
        K = forward * math.exp(float(m))
        w = float(svi_total_variance(svi_params, np.array([m]))[0])
        if w <= 0:
            continue
        iv = math.sqrt(w / t_years)
        cp = "C" if K >= forward else "P"
        delta = black76_delta(forward, K, iv, t_years, cp)
        if not (DELTA_BAND[0] <= abs(delta) <= DELTA_BAND[1]):
            continue
        n_in_band += 1
        strike_str = str(int(round(K)))
        name = f"{symbol}-{expiry.day}{mon}{yy}-{strike_str}-{cp}"
        entries.append({
            "instrument_name": name,
            "mark_iv": iv * 100.0,
            "forward_price": forward,
        })
    ts = int(datetime(snapshot_day.year, snapshot_day.month, snapshot_day.day, 8,
                      tzinfo=timezone.utc).timestamp() * 1000)
    payload = json.dumps({
        "params": {"channel": f"markprice.options.{symbol.lower()}_usd", "data": entries},
    })
    part = (base / "raw" / "deribit" / "markprice.options" / f"symbol={symbol}"
            / f"date={snapshot_day.isoformat()}")
    _write_parquet(part, [ts], [payload])
    return n_in_band


def _cli_main():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "c13_tailshape_cli", REPO_ROOT / "scripts" / "c13_tailshape.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def test_e2e_found_case_unlock_and_full_run(tmp_path):
    base = tmp_path / "harvest"
    svi_params = np.array([0.02, 0.15, -0.3, 0.0, 0.3])
    forward = 50_000.0
    d1 = date(2026, 1, 15)
    d2 = d1 + timedelta(days=14)  # >= 10-day gap requirement

    n1 = _build_deribit_day(base, "BTC", d1, svi_params=svi_params, forward=forward)
    n2 = _build_deribit_day(base, "BTC", d2, svi_params=svi_params, forward=forward)
    assert n1 >= MIN_STRIKES and n2 >= MIN_STRIKES, "fixture must clear the strike floor"

    trailing_days = 60
    start = d1 - timedelta(days=trailing_days + 3)
    # >= 60 days of Bybit publicTrade coverage, spanning both D1's and D2's
    # trailing windows; distinct RV_5d regimes right before D1 and D2 drive
    # the >= 1.5x vol-regime-disjoint unlock condition.
    _build_bybit_tree(
        base, "BTCUSDT", start, d2,
        low_vol_window=(d1 - timedelta(days=5), d1 - timedelta(days=1)),
        high_vol_window=(d2 - timedelta(days=5), d2 - timedelta(days=1)),
    )

    unlock = check_unlock(base, ("BTC",))
    assert unlock["unlocked"] is True
    sel = unlock["selection"]["BTC"]
    assert sel["found"] is True
    assert sel["d1"] == d1.isoformat()
    assert sel["d2"] == d2.isoformat()

    main = _cli_main()
    rc = main([
        "--base-dir", str(base), "--symbols", "BTC", "--check-unlock-only",
        "--out-dir", str(tmp_path / "out1"),
    ])
    assert rc == 0
    unlock_payload = json.loads((tmp_path / "out1" / "c13_unlock_check.json").read_text())
    assert unlock_payload["unlocked"] is True

    rc2 = main([
        "--base-dir", str(base), "--symbols", "BTC", "--out-dir", str(tmp_path / "out2"),
        "--n-bootstrap", "30", "--trailing-days", str(trailing_days), "--seed", "7",
    ])
    assert rc2 == 0
    payload = json.loads((tmp_path / "out2" / "c13_tailshape_results.json").read_text())
    assert payload["hypothesis"] == "H-13"
    assert payload["capital_free"] is True
    assert payload["data_gated"] is True
    assert payload["skip"] is False
    assert len(payload["cells"]) == 2  # D1 + D2 for BTC
    labels = {c["day_label"] for c in payload["cells"]}
    assert labels == {"D1", "D2"}
    for c in payload["cells"]:
        assert math.isfinite(c["xi_p"])
        assert math.isfinite(c["xi_q"])
        assert math.isfinite(c["delta_xi"])
        assert 0.0 <= c["p_value"] <= 1.0
    assert payload["gate"] is not None
    assert "any_symbol_gate_met" in payload["gate"]
    md = (tmp_path / "out2" / "c13_tailshape_results.md").read_text()
    assert "F-TAILSHAPE" in md and "KAPITALFREI" in md


def test_e2e_locked_case_reports_clean_skip(tmp_path):
    base = tmp_path / "harvest"  # no markprice.options data anywhere -> locked
    main = _cli_main()

    rc = main([
        "--base-dir", str(base), "--symbols", "BTC,ETH", "--check-unlock-only",
        "--out-dir", str(tmp_path / "out1"),
    ])
    assert rc == 2  # RC_SKIP_LOCKED
    unlock_payload = json.loads((tmp_path / "out1" / "c13_unlock_check.json").read_text())
    assert unlock_payload["unlocked"] is False

    rc2 = main([
        "--base-dir", str(base), "--symbols", "BTC,ETH", "--out-dir", str(tmp_path / "out2"),
    ])
    assert rc2 == 2
    payload = json.loads((tmp_path / "out2" / "c13_tailshape_results.json").read_text())
    assert payload["skip"] is True
    assert payload["capital_free"] is True
    assert payload["data_gated"] is True
    assert payload["cells"] == []
    assert payload["gate"] is None
    assert "locked" in payload["skip_reason"].lower()
