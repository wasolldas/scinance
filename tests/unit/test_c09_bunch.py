"""Unit tests for the H-09 risk-limit tier-bunching package (F-BUNCH, KAPITALFREI).

Covers (a) binning/counterfactual correctness, (b) null control (smooth
density -> no pass), (c) positive detection (synthetic bunching just below a
test kink), (d) capital_free payload hygiene, (e) the N-floor invalidity path,
and (f) end-to-end: synthetic harvester Hive tree (backfill form) ->
``scripts/c09_bunch.py`` -> rc=0 + valid JSON. All synthetic — never runs
against real user data.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c01_ofi_sign.driver import TradeArrays
from bybit_edge.research.c09_bunch import kinks
from bybit_edge.research.c09_bunch.driver import (
    DataError,
    WindowOrders,
    render_markdown,
    run,
)
from bybit_edge.research.c09_bunch.estimator import (
    BUNCH_BINS,
    CTRL_BINS,
    EXCLUDED_BINS,
    aggregate_orders,
    bin_centers_rel,
    bin_notionals,
    estimate_cell,
    excess_mass,
    fit_counterfactual,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
K_TEST = 1000.0  # synthetic test kink ("Test-Kante"), NOT a real Bybit value


def _arrays(notionals: np.ndarray, *, t0_ms: float = 0.0) -> TradeArrays:
    """One order per record: unique ts, price 1.0, volume = notional."""
    n = int(len(notionals))
    return TradeArrays(
        ts=t0_ms + np.arange(n, dtype=np.float64) * 10.0,
        price=np.ones(n, dtype=np.float64),
        volume=np.asarray(notionals, dtype=np.float64),
        side=np.full(n, "Buy", dtype=object),
    )


def _uniform_notionals(rng: np.random.Generator, n: int) -> np.ndarray:
    """Smooth (uniform) notional density over [0.35, 1.35) * K_TEST."""
    return rng.uniform(0.35 * K_TEST, 1.35 * K_TEST, size=n)


# ---------------------------------------------------------------------------
# (a) order aggregation + binning + counterfactual correctness
# ---------------------------------------------------------------------------

def test_aggregate_orders_merges_consecutive_same_ts_side() -> None:
    ts = np.array([1, 1, 1, 2, 2, 3], dtype=np.float64)
    side = np.array(["Buy", "Buy", "Sell", "Sell", "Sell", "Sell"], dtype=object)
    price = np.full(6, 10.0)
    volume = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    out = aggregate_orders(ts, side, price, volume)
    # (ts=1,Buy)=10+20, (ts=1,Sell)=30, (ts=2,Sell)=40+50, (ts=3,Sell)=60
    assert np.allclose(out, [30.0, 30.0, 90.0, 60.0])
    assert aggregate_orders(np.array([]), np.array([]), np.array([]), np.array([])).size == 0


def test_binning_band_edges_and_window_bins() -> None:
    notionals = K_TEST * np.array([0.40, 0.4099, 1.2999, 1.30, 0.3999, 0.95])
    counts, n_in_band = bin_notionals(notionals, K_TEST)
    assert n_in_band == 4  # 1.30 (excl.) and 0.3999 (below band) dropped
    assert counts[0] == 2      # 0.40 and 0.4099 -> bin 0
    assert counts[89] == 1     # 1.2999 -> last bin
    assert counts[55] == 1     # 0.95 -> first B- bin
    assert counts.sum() == 4
    # registered index geometry
    assert list(BUNCH_BINS) == [55, 56, 57, 58, 59]
    assert list(CTRL_BINS) == [60, 61, 62, 63, 64]
    assert EXCLUDED_BINS[0] == 50 and EXCLUDED_BINS[-1] == 69 and EXCLUDED_BINS.size == 20


def test_benjamini_hochberg_own_copy() -> None:
    """Direct unit test for the c09-own BH-FDR copy (audit_h09.md Bug 7):
    mirrors the pattern used in test_c10_pointer.py / test_c06_xmr.py."""
    from bybit_edge.research.c09_bunch.stats import benjamini_hochberg

    rejected, p_crit = benjamini_hochberg([0.01, 0.02, 0.9, 0.04], alpha=0.10)
    assert rejected == [True, True, False, True]
    assert p_crit == 0.04
    assert benjamini_hochberg([], 0.10) == ([], 0.0)
    # ties: both p=0.03 at ranks 1/2 of m=4, alpha=0.10 -> threshold rank2 =
    # 0.05; both survive together (step-up keeps ties together).
    rejected_ties, p_crit_ties = benjamini_hochberg([0.03, 0.03, 0.5, 0.6], alpha=0.10)
    assert rejected_ties == [True, True, False, False]
    assert p_crit_ties == 0.03
    # nothing survives -> all False, p_crit 0.0
    rejected_none, p_crit_none = benjamini_hochberg([0.5, 0.6, 0.7], alpha=0.10)
    assert rejected_none == [False, False, False]
    assert p_crit_none == 0.0


def test_counterfactual_recovers_smooth_polynomial_and_zero_excess() -> None:
    r = bin_centers_rel()
    counts = 200.0 + 100.0 * r + 50.0 * r**2  # exact low-degree polynomial
    fitted = fit_counterfactual(counts)
    # degree-7 fit on 70 included bins must reproduce the polynomial on ALL
    # 90 bins (including the excluded [0.90, 1.10) region)
    assert np.allclose(fitted, counts, rtol=1e-6, atol=1e-6)
    em = excess_mass(counts, fitted)
    assert abs(em["b_minus"]) < 1e-6
    assert abs(em["b_plus"]) < 1e-6


# ---------------------------------------------------------------------------
# (b) null control: smooth synthetic density -> no bunching pass
# ---------------------------------------------------------------------------

def test_null_smooth_density_does_not_pass() -> None:
    rng = np.random.default_rng(1234)
    sw = {"TESTUSDT": [_arrays(_uniform_notionals(rng, 30_000)),
                       _arrays(_uniform_notionals(rng, 30_000), t0_ms=1e9)]}
    out = run(sw, window_labels=("W1", "W2"), kinks={"TESTUSDT": K_TEST},
              n_bootstrap=200, seed=7)
    assert len(out["cells"]) == 2
    for c in out["cells"]:
        assert c["cell_valid"] is True  # N-floor comfortably met
        assert abs(c["b_minus"]) < 1.0, "smooth density must not show b- >= 1"
        assert c["b_minus_floor_met"] is False
        assert c["passed"] is False
    assert out["any_symbol_passed_both_windows"] is False
    assert out["weiter_indication"] is False


# ---------------------------------------------------------------------------
# (c) positive detection: bunching just below the test kink
# ---------------------------------------------------------------------------

def test_positive_bunching_below_kink_passes_all_criteria() -> None:
    rng = np.random.default_rng(99)

    def _window(t0: float) -> TradeArrays:
        base = _uniform_notionals(rng, 30_000)
        spike = rng.uniform(0.955 * K_TEST, 0.995 * K_TEST, size=3_000)
        return _arrays(np.concatenate([base, spike]), t0_ms=t0)

    sw = {"TESTUSDT": [_window(0.0), _window(1e9)]}
    # registered bootstrap count (500) -> the numeric run-params sub-flag must
    # be True. The synthetic "TESTUSDT" symbol / plain "W1"/"W2" labels are a
    # testing device and deliberately deviate from the registered 5-symbol
    # panel and registered window labels, so the FULL anti-gaming composite
    # (gate_valid_assumptions, which also covers panel/window/K_s identity —
    # audit_h09.md Bug 4) is correctly False here; see
    # test_gate_valid_assumptions_requires_registered_panel_and_windows below
    # for the identity-check path on the real registered panel.
    out = run(sw, window_labels=("W1", "W2"), kinks={"TESTUSDT": K_TEST},
              n_bootstrap=500, seed=42)
    for c in out["cells"]:
        assert c["cell_valid"] is True
        assert c["b_minus"] >= 1.0, f"expected clear excess mass, got {c['b_minus']}"
        assert c["b_minus_floor_met"] is True
        assert c["asymmetry_met"] is True, (c["b_minus"], c["b_plus"])
        assert c["placebo_dominance_met"] is True, c["b_placebo_max"]
        assert c["bootstrap_p"] <= 0.05
        assert c["fdr_significant"] is True
        assert c["passed"] is True
    assert out["gate_valid_run_params"] is True
    assert out["gate_valid_assumptions"] is False  # panel/window deviation (Bug 4)
    assert out["panel_matches_registered"] is False
    assert out["windows_match_registered"] is False
    assert out["any_symbol_passed_both_windows"] is True
    assert out["any_nonplaceholder_symbol_passed_both_windows"] is True
    # weiter_indication is void because gate_valid_assumptions is False
    assert out["weiter_indication"] is False
    per_sym = out["per_symbol"][0]
    assert per_sym["passed_both_windows"] is True
    # markdown renders
    md = render_markdown(out)
    assert "H-09" in md and "F-BUNCH" in md


def test_gate_valid_assumptions_requires_registered_panel_and_windows() -> None:
    """Bug 4 (audit_h09.md): a deviating --symbols/--window-* CLI override
    must void gate_valid_assumptions even when every numeric run parameter
    (bootstrap reps, poly degree, floors) is at its registered point."""
    from bybit_edge.research.c09_bunch.driver import DEFAULT_WINDOW_A, DEFAULT_WINDOW_B
    from bybit_edge.research.c09_bunch.kinks import REGISTERED_PANEL_SYMBOLS

    rng = np.random.default_rng(21)
    registered_labels = (
        f"W1@{DEFAULT_WINDOW_A[0]}..{DEFAULT_WINDOW_A[1]}",
        f"W2@{DEFAULT_WINDOW_B[0]}..{DEFAULT_WINDOW_B[1]}",
    )

    def _full_panel_windows() -> dict[str, list]:
        return {
            sym: [_arrays(_uniform_notionals(rng, 3_000)),
                  _arrays(_uniform_notionals(rng, 3_000), t0_ms=1e9)]
            for sym in REGISTERED_PANEL_SYMBOLS
        }

    # (a) full registered panel + registered window labels + registered K_s
    # (default kinks) + registered run params -> identity sub-flags all True.
    out_ok = run(_full_panel_windows(), window_labels=registered_labels,
                 n_bootstrap=500, seed=1)
    assert out_ok["panel_matches_registered"] is True
    assert out_ok["windows_match_registered"] is True
    assert out_ok["kinks_match_registered"] is True
    assert out_ok["family_size_deviation"] is False

    # (b) same panel, but non-registered (CLI-overridden) window labels ->
    # windows_match_registered False -> composite gate voided.
    out_bad_windows = run(_full_panel_windows(), window_labels=("W1", "W2"),
                           n_bootstrap=500, seed=1)
    assert out_bad_windows["windows_match_registered"] is False
    assert out_bad_windows["gate_valid_assumptions"] is False

    # (c) reduced panel (CLI --symbols override to a subset) -> panel
    # mismatch -> composite gate voided even with perfect run params.
    reduced = {"BTCUSDT": [_arrays(_uniform_notionals(rng, 3_000)),
                           _arrays(_uniform_notionals(rng, 3_000), t0_ms=1e9)]}
    out_reduced = run(reduced, window_labels=registered_labels, n_bootstrap=500, seed=1)
    assert out_reduced["panel_matches_registered"] is False
    assert out_reduced["gate_valid_assumptions"] is False


def test_placeholder_only_pass_does_not_drive_headline_weiter() -> None:
    """Bug 8 (audit_h09.md): weiter_indication must NOT fire on a pass driven
    only by a PLACEHOLDER K_s symbol (ETH/SOL/BNB/XRP) — only a registry-quoted
    (non-placeholder, i.e. BTCUSDT) pass may set the headline flag."""
    from bybit_edge.research.c09_bunch.driver import DEFAULT_WINDOW_A, DEFAULT_WINDOW_B
    from bybit_edge.research.c09_bunch.kinks import (
        KINK_PLACEHOLDER_SYMBOLS,
        REGISTERED_PANEL_SYMBOLS,
        RISK_LIMIT_TIER1_KINK_USDT,
    )

    rng = np.random.default_rng(31)
    registered_labels = (
        f"W1@{DEFAULT_WINDOW_A[0]}..{DEFAULT_WINDOW_A[1]}",
        f"W2@{DEFAULT_WINDOW_B[0]}..{DEFAULT_WINDOW_B[1]}",
    )
    placeholder_sym = KINK_PLACEHOLDER_SYMBOLS[0]  # ETHUSDT

    def _spiked(kink: float, t0: float) -> TradeArrays:
        base = rng.uniform(0.35 * kink, 1.35 * kink, size=30_000)
        spike = rng.uniform(0.955 * kink, 0.995 * kink, size=3_000)
        return _arrays(np.concatenate([base, spike]), t0_ms=t0)

    def _smooth(kink: float, t0: float) -> TradeArrays:
        return _arrays(rng.uniform(0.35 * kink, 1.35 * kink, size=30_000), t0_ms=t0)

    sw: dict[str, list] = {}
    for sym in REGISTERED_PANEL_SYMBOLS:
        k = RISK_LIMIT_TIER1_KINK_USDT[sym]
        if sym == placeholder_sym:
            sw[sym] = [_spiked(k, 0.0), _spiked(k, 1e9)]
        else:
            sw[sym] = [_smooth(k, 0.0), _smooth(k, 1e9)]

    out = run(sw, window_labels=registered_labels, n_bootstrap=200, seed=31)
    ph_rollup = next(s for s in out["per_symbol"] if s["symbol"] == placeholder_sym)
    assert ph_rollup["kink_is_placeholder"] is True
    assert ph_rollup["passed_both_windows"] is True, "fixture must produce a clear placeholder pass"
    assert out["any_symbol_passed_both_windows"] is True
    assert out["any_nonplaceholder_symbol_passed_both_windows"] is False
    assert out["placeholder_driven_pass_only"] is True
    assert out["weiter_indication"] is False, (
        "a placeholder-only pass must NEVER read as a headline WEITER (Bug 8)"
    )


# ---------------------------------------------------------------------------
# (d) capital_free payload hygiene
# ---------------------------------------------------------------------------

def test_payload_capital_free_and_no_capital_tokens() -> None:
    rng = np.random.default_rng(5)
    sw = {"TESTUSDT": [_arrays(_uniform_notionals(rng, 5_000)),
                       _arrays(_uniform_notionals(rng, 5_000), t0_ms=1e9)]}
    out = run(sw, window_labels=("W1", "W2"), kinks={"TESTUSDT": K_TEST},
              n_bootstrap=50, seed=3)
    assert out["capital_free"] is True
    assert out["hypothesis"] == "H-09"
    assert out["fdr_family"] == "F-BUNCH"
    blob = json.dumps(out).lower()
    for forbidden in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert forbidden not in blob, f"capital-free violated: {forbidden!r} in payload"
    # deviating from the registered 500 bootstrap reps voids the WEITER reading
    assert out["gate_valid_assumptions"] is False


# ---------------------------------------------------------------------------
# (e) N-floor: too few observations -> cell invalid, no pass
# ---------------------------------------------------------------------------

def test_n_floor_too_few_orders_invalidates_cell() -> None:
    rng = np.random.default_rng(11)

    def _tiny_window(t0: float) -> TradeArrays:
        base = _uniform_notionals(rng, 500)  # far below the 2,000 floor
        spike = rng.uniform(0.955 * K_TEST, 0.995 * K_TEST, size=200)
        return _arrays(np.concatenate([base, spike]), t0_ms=t0)

    sw = {"TESTUSDT": [_tiny_window(0.0), _tiny_window(1e9)]}
    out = run(sw, window_labels=("W1", "W2"), kinks={"TESTUSDT": K_TEST},
              n_bootstrap=50, seed=9)
    for c in out["cells"]:
        assert c["n_orders_in_band"] < kinks.N_FLOOR_ORDERS
        assert c["n_floor_met"] is False
        assert c["cell_valid"] is False
        assert c["passed"] is False, "invalid cell must NEVER pass, even with a spike"
    assert out["any_symbol_passed_both_windows"] is False
    assert out["weiter_indication"] is False
    # both windows have ALL (here: the only) cells invalid -> power-DROP flag
    assert out["all_cells_invalid_by_window"] == [True, True]


def test_cf_expectation_floor_invalidates_cell() -> None:
    rng = np.random.default_rng(12)
    cell = estimate_cell(_uniform_notionals(rng, 30_000), K_TEST,
                         n_bootstrap=10, seed=1, cf_expectation_floor=1e9)
    assert cell["n_floor_met"] is True
    assert cell["cf_floor_met"] is False
    assert cell["cell_valid"] is False


def test_run_requires_two_windows() -> None:
    rng = np.random.default_rng(13)
    sw = {"TESTUSDT": [_arrays(_uniform_notionals(rng, 3_000))]}
    with pytest.raises(DataError):
        run(sw, window_labels=("W1",), kinks={"TESTUSDT": K_TEST},
            n_bootstrap=10, seed=1)


# ---------------------------------------------------------------------------
# (g) Bug 1: window_truncated must invalidate the cell AND void the gate
# (audit_h09.md — silent truncation must become structurally impossible).
# ---------------------------------------------------------------------------

def test_window_truncated_invalidates_cell_and_voids_gate() -> None:
    rng = np.random.default_rng(17)

    def _window_orders(t0: float, *, truncated: bool) -> WindowOrders:
        base = _uniform_notionals(rng, 30_000)
        spike = rng.uniform(0.955 * K_TEST, 0.995 * K_TEST, size=3_000)
        notionals = np.concatenate([base, spike])
        n = int(notionals.size)
        return WindowOrders(
            notionals=notionals,
            n_records_raw=n,
            n_orders_total=n,
            first_ts_ms=int(t0),
            last_ts_ms=int(t0) + n,
            window_truncated=truncated,
            max_ticks=50_000_000 if truncated else None,
        )

    # window 0 hit a (legacy) tick cap and only loaded a PARTIAL pre-registered
    # window; window 1 loaded cleanly. The underlying data is otherwise
    # identical to the clear positive-detection fixture (would pass all four
    # gate criteria if not for the truncation).
    sw = {"TESTUSDT": [
        _window_orders(0.0, truncated=True),
        _window_orders(1e9, truncated=False),
    ]}
    out = run(sw, window_labels=("W1", "W2"), kinks={"TESTUSDT": K_TEST},
              n_bootstrap=200, seed=17)

    truncated_cell = next(c for c in out["cells"] if c["window_index"] == 0)
    clean_cell = next(c for c in out["cells"] if c["window_index"] == 1)
    assert truncated_cell["window_truncated"] is True
    assert truncated_cell["cell_valid"] is False, (
        "a truncated window must NEVER read as a valid cell, even with a "
        "clear synthetic bunching spike"
    )
    assert truncated_cell["invalid_reason"].startswith("window_truncated")
    assert truncated_cell["passed"] is False
    assert clean_cell["window_truncated"] is False

    assert out["any_window_truncated"] is True
    assert out["gate_valid_assumptions"] is False, (
        "any truncated window must void gate_valid_assumptions (Bug 1)"
    )
    # the untruncated window alone cannot satisfy the >=2-window WEITER rule
    assert out["weiter_indication"] is False


def test_window_orders_from_load_window_orders_reports_metadata(tmp_path: Path) -> None:
    """:func:`load_window_orders` (DuckDB-side aggregation) never truncates and
    reports full first/last-ts + raw-record metadata (Bug 1/2 structural fix:
    no tick cap exists on this path)."""
    from bybit_edge.research.c09_bunch.driver import load_window_orders

    rng = np.random.default_rng(23)
    tree = tmp_path / "harvest"
    notionals = rng.uniform(0.3 * K_TEST * 2000, 1.4 * K_TEST * 2000, size=2_500)
    _write_backfill_notionals(tree, "BTCUSDT", "2026-03-27", notionals,
                              _midnight_ms("2026-03-27"))
    wo = load_window_orders(tree, "BTCUSDT", "2026-03-27", "2026-03-27",
                            kink=2_000_000.0)
    assert wo.window_truncated is False
    assert wo.max_ticks is None
    assert wo.n_records_raw == 2_500
    assert wo.n_orders_total == 2_500  # unique ts per record -> 1 order each
    assert wo.first_ts_ms is not None and wo.last_ts_ms is not None
    assert wo.first_ts_ms <= wo.last_ts_ms


# ---------------------------------------------------------------------------
# (h) Bug 3: FDR family must stay at the registered m=10 under a partial panel
# ---------------------------------------------------------------------------

def test_partial_panel_padded_with_sentinels_keeps_family_at_registered_size() -> None:
    from bybit_edge.research.c09_bunch.kinks import REGISTERED_FAMILY_SIZE, REGISTERED_PANEL_SYMBOLS

    rng = np.random.default_rng(29)
    loaded_symbols = REGISTERED_PANEL_SYMBOLS[:4]  # one symbol (index 4) missing
    missing = (REGISTERED_PANEL_SYMBOLS[4],)
    sw = {
        sym: [_arrays(_uniform_notionals(rng, 3_000)),
              _arrays(_uniform_notionals(rng, 3_000), t0_ms=1e9)]
        for sym in loaded_symbols
    }
    out = run(sw, window_labels=("W1", "W2"), missing_symbols=missing,
              n_bootstrap=50, seed=5)

    assert len(out["cells"]) == REGISTERED_FAMILY_SIZE == 10
    sentinel_cells = [c for c in out["cells"] if c["symbol"] == missing[0]]
    assert len(sentinel_cells) == 2  # one per window
    for c in sentinel_cells:
        assert c["sentinel_missing_data"] is True
        assert c["bootstrap_p"] == 1.0
        assert c["cell_valid"] is False
        assert c["passed"] is False
    # BH-FDR ran over the FULL padded family, not a shrunk m=4*2=8
    assert out["n_sentinel_cells"] == 2
    assert out["family_size_deviation"] is True
    assert out["gate_valid_assumptions"] is False
    assert out["missing_symbols"] == list(missing)
    missing_sym_rollup = next(
        s for s in out["per_symbol"] if s["symbol"] == missing[0]
    )
    assert missing_sym_rollup["missing_data"] is True
    assert missing_sym_rollup["n_windows_measured"] == 0
    assert missing_sym_rollup["passed_both_windows"] is False


# ---------------------------------------------------------------------------
# (f) end-to-end: synthetic harvester Hive tree -> CLI -> rc=0 + valid JSON
# ---------------------------------------------------------------------------

def _midnight_ms(date_str: str) -> int:
    y, m, d = (int(x) for x in date_str.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _write_backfill_notionals(tmp: Path, symbol: str, date_str: str,
                              notionals: np.ndarray, start_ms: int) -> None:
    """Synthetic raw backfill parquet (payload_json single-trade form)."""
    import duckdb

    d = tmp / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    price = 50_000.0
    rows = []
    for i, x in enumerate(np.asarray(notionals, dtype=np.float64)):
        ts = start_ms + i * 50  # unique ts -> one order aggregate per record
        payload = json.dumps({
            "side": "Buy" if i % 2 == 0 else "Sell",
            "price": str(price),
            "size": f"{x / price:.10f}",
            "symbol": symbol,
        })
        rows.append((ts, payload))
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", rows)
        out = d / "data.parquet"
        con.execute(f"COPY t TO '{out.as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def test_cli_end_to_end_on_synthetic_hive_tree(tmp_path: Path) -> None:
    k_btc = 2_000_000.0  # module K_s for BTCUSDT (registry-quoted)
    rng = np.random.default_rng(2026)
    tree = tmp_path / "harvest"
    for date_str in ("2026-03-27", "2026-05-16"):
        notionals = rng.uniform(0.3 * k_btc, 1.4 * k_btc, size=3_000)
        _write_backfill_notionals(tree, "BTCUSDT", date_str, notionals,
                                  _midnight_ms(date_str))

    out_dir = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "c09_bunch.py"),
         "--base-dir", str(tree),
         "--symbols", "BTCUSDT",
         "--window-a-start", "2026-03-27", "--window-a-end", "2026-03-27",
         "--window-b-start", "2026-05-16", "--window-b-end", "2026-05-16",
         "--n-bootstrap", "50", "--seed", "42",
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, f"CLI failed:\n{proc.stderr}"

    json_path = out_dir / "c09_bunch_results.json"
    md_path = out_dir / "c09_bunch_results.md"
    assert json_path.exists() and md_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["hypothesis"] == "H-09"
    assert payload["capital_free"] is True
    assert payload["fdr_family"] == "F-BUNCH"
    assert payload["kinks_usdt"]["BTCUSDT"] == k_btc
    assert len(payload["cells"]) == 2  # 1 symbol x 2 windows
    for c in payload["cells"]:
        assert c["n_orders_in_band"] >= 2_000  # synthetic tree meets the floor
        assert c["cell_valid"] is True
    # 50 bootstrap reps < registered 500 -> anti-gaming flag must be false
    assert payload["gate_valid_assumptions"] is False
    blob = json.dumps(payload).lower()
    for forbidden in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert forbidden not in blob, f"capital-free violated: {forbidden!r}"
