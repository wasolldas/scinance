"""Tests for the C-06 XMR cross-sectional MR mess-gate (c06_xmr, H-07).

Covers:
- Panel synchronisation: common bar axis, forward-fill <= 1 bar, row-drop on a
  > 1-bar gap in any one symbol (contemporaneous completeness).
- Cross-sectional-z correctness on a known mini example (one symbol strongly
  deviating -> large |z|).
- Reversion signing (positive-z + falling forward price -> positive rev_ret).
- Axis B crash-decile (top decile excluded).
- N-floor (N < 30 -> no pass).
- POSITIVE detection: a synthetic panel where conditioned events revert MORE
  strongly than baseline -> amplified_consistent=True in both windows, CIs
  non-overlapping.
- NULL/TRIVIAL control (critical): a panel where conditioned ~ unconditioned
  reversion (only trivial MR, no amplification) -> amplified_consistent=False
  (CIs overlap) — proving the trivial reading does NOT pass.
- capital_free=true and NO bps/pnl/sharpe/friction anywhere in the JSON.
- End-to-end: build a small synthetic harvester Hive tree (5 symbols, 2 calendar
  windows, publicTrade payload_json backfill form) and run scripts/c06_xmr.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c06_xmr.driver import run
from bybit_edge.research.c06_xmr.panel import (
    SyncedPanel,
    build_calendar_grid,
    resample_last_price,
    synchronise_panel,
)
from bybit_edge.research.c06_xmr.stats import (
    benjamini_hochberg,
    block_bootstrap_ci,
    ci_non_overlap,
)
from bybit_edge.research.c06_xmr.xsec import (
    build_event_table,
    cross_sectional_z,
    non_crash_mask,
    panel_realized_vol,
    time_mean_returns,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")


# ---------------------------------------------------------------------------
# Panel synchronisation
# ---------------------------------------------------------------------------

def test_resample_last_price_takes_last_trade_in_bar() -> None:
    bar_ms = 5 * 60_000
    grid = build_calendar_grid("2026-04-15", 1, 5).astype(np.float64)
    # trades in the first bar: prices 10, 11, 12 (last = 12); second bar: 20
    ts = np.array([grid[0] + 1000, grid[0] + 2000, grid[0] + 3000, grid[1] + 500],
                  dtype=np.float64)
    px = np.array([10.0, 11.0, 12.0, 20.0], dtype=np.float64)
    out = resample_last_price(ts, px, grid, bar_ms)
    assert out[0] == 12.0
    assert out[1] == 20.0
    assert np.isnan(out[2])  # no trade in third bar


def test_synchronise_ffill_one_bar_and_drop_on_bigger_gap() -> None:
    grid = np.arange(6, dtype=np.float64) * 1000.0
    # symbol A complete; symbol B has a 1-bar gap (bar 2) and a 2-bar gap (bars 4,5)
    a = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    b = np.array([10.0, 11.0, np.nan, 13.0, np.nan, np.nan])
    panel = synchronise_panel({"A": a, "B": b}, grid, ("A", "B"), max_ffill_bars=1)
    # bar 2 recovered by ffill (<=1); bars 4 (ffill ok) but bar5 gap>1 -> dropped.
    # after ffill: b = [10,11,11,13,13,NaN] -> bar5 dropped (both symbols).
    assert panel.n_bars == 5
    assert 5000.0 not in panel.bar_ts_ms  # last bar dropped
    # bar 2 present with ffilled B=11
    row2 = np.where(panel.bar_ts_ms == 2000.0)[0][0]
    assert panel.last_price[row2, 1] == 11.0


def test_synchronise_drops_row_when_any_symbol_missing_beyond_cap() -> None:
    grid = np.arange(4, dtype=np.float64) * 1000.0
    a = np.array([1.0, 2.0, 3.0, 4.0])
    # 2-bar gap in B at bars 1,2 -> bar1 ffilled, bar2 dropped for ALL
    b = np.array([10.0, np.nan, np.nan, 13.0])
    panel = synchronise_panel({"A": a, "B": b}, grid, ("A", "B"), max_ffill_bars=1)
    assert 2000.0 not in panel.bar_ts_ms
    assert panel.n_bars == 3


# ---------------------------------------------------------------------------
# Cross-sectional z
# ---------------------------------------------------------------------------

def test_cross_sectional_z_flags_deviating_symbol() -> None:
    # 5 time-means, symbol 0 far above the others -> large positive z_0.
    tm = np.array([[1.0, 0.0, 0.0, 0.0, 0.0]])
    z = cross_sectional_z(tm)
    assert np.isfinite(z[0, 0])
    assert z[0, 0] > 1.5  # strongly stretched
    assert (z[0, 1:] < 0).all()  # the others are below the mean


def test_time_mean_returns_trailing_window() -> None:
    # returns: row0 NaN (no prior bar), then constant per symbol
    r = np.full((5, 2), np.nan)
    r[1:, 0] = [0.1, 0.2, 0.3, 0.4]
    r[1:, 1] = [0.0, 0.0, 0.0, 0.0]
    tm = time_mean_returns(r, lookback=2)
    # at t=4, window rows 3..4 for symbol 0 = mean(0.3,0.4)=0.35
    assert tm[4, 0] == pytest.approx(0.35)
    assert tm[4, 1] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Reversion signing
# ---------------------------------------------------------------------------

def test_reversion_signing_positive_z_falling_price() -> None:
    # Reversion-signing formula: rev_ret = -sign(z) * R_{t->t+h}. A positive-z
    # event whose forward price FALLS (R < 0) must yield a POSITIVE rev_ret.
    from bybit_edge.research.c06_xmr.xsec import forward_return_h
    px = np.array([[100.0], [100.0], [90.0]])  # price falls from bar1 to bar2
    fwd = forward_return_h(px, h=1)
    r = fwd[1, 0]  # R_{1->2} = 90/100 - 1 = -0.1 (falling)
    assert r < 0
    z_pos = 2.5
    rev = -np.sign(z_pos) * r
    assert rev > 0.0  # positive-z + falling price -> positive reversion
    # symmetric check: negative-z + rising price -> also positive reversion
    px2 = np.array([[100.0], [100.0], [110.0]])
    r2 = forward_return_h(px2, h=1)[1, 0]
    assert (-np.sign(-2.5) * r2) > 0.0


def test_build_event_table_conditions_over_stretch_and_noncrash() -> None:
    # A deviating symbol produces a large |z|; verify it is flagged conditioned
    # (axis A) when non-crash (axis B) holds, and carries a finite rev_ret.
    T, N = 30, 5
    ts = np.arange(T, dtype=np.float64) * 300_000.0
    px = np.ones((T, N)) * 100.0
    for j in range(1, N):
        px[:, j] = 100.0 + 0.001 * j * np.arange(T)
    # symbol 0 drifts up strongly over the lookback (large positive time-mean)
    px[:, 0] = 100.0 * (1.02 ** np.arange(T))
    ret = np.full((T, N), np.nan)
    ret[1:, :] = px[1:, :] / px[:-1, :] - 1.0
    panel = SyncedPanel(ts, SYMBOLS, px, ret, "mini")
    evt = build_event_table(panel, lookback_bars=12, z_thresh=1.5,
                            crash_decile=1.0, panel_rv_bars=1, horizon=1)
    assert evt.is_over_stretch.any()
    # with crash_decile=1.0 nothing is a crash -> over-stretch == conditioned
    assert (evt.is_over_stretch == evt.is_conditioned).all()


# ---------------------------------------------------------------------------
# Axis B crash decile
# ---------------------------------------------------------------------------

def test_non_crash_mask_excludes_top_decile() -> None:
    rv = np.arange(1, 11, dtype=np.float64)  # 1..10
    mask = non_crash_mask(rv, crash_decile=0.9)
    # top decile (the 10) excluded; the rest pass
    assert not mask[-1]
    assert mask[:-1].sum() >= 8


def test_panel_realized_vol_forward_sum_of_squares() -> None:
    r = np.zeros((6, 2))
    r[3, 0] = 0.1  # a squared return of 0.01 lands in windows that include bar 3
    rv = panel_realized_vol(r, horizon_bars=2)
    # rv[1] covers bars 2,3 -> includes 0.01; rv[2] covers 3,4 -> includes 0.01
    assert rv[1] == pytest.approx(0.01)
    assert rv[2] == pytest.approx(0.01)
    assert rv[0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# CI helpers
# ---------------------------------------------------------------------------

def test_ci_non_overlap_requires_conditioned_above() -> None:
    assert ci_non_overlap(0.5, 0.8, 0.1, 0.4) is True   # cond above, disjoint
    assert ci_non_overlap(0.3, 0.8, 0.1, 0.4) is False  # overlap
    assert ci_non_overlap(0.0, 0.2, 0.5, 0.9) is False  # cond below
    assert ci_non_overlap(float("nan"), 0.2, 0.1, 0.4) is False


def test_benjamini_hochberg_basic() -> None:
    rej, pcrit = benjamini_hochberg([0.001, 0.5, 0.9, 0.02], alpha=0.10)
    assert rej[0] is True
    assert rej[2] is False


# ---------------------------------------------------------------------------
# Synthetic panels for the driver-level positive / null tests
# ---------------------------------------------------------------------------

def _amplified_panel(seed: int, *, amplify: bool, label: str) -> SyncedPanel:
    """Build a synchronised panel with controllable conditional amplification.

    Baseline bars carry a weak, symmetric mean-reversion (so the unconditioned
    mu_rev is slightly > 0 — a trivial MR is present). When ``amplify`` is True,
    the over-stretched (|z|>=2.5) non-crash bars additionally get a STRONG
    reversion kick, so conditioned mu_rev >> baseline. When ``amplify`` is False,
    the conditioned bars behave exactly like the baseline (trivial only).
    """
    rng = np.random.default_rng(seed)
    T, N = 600, 5
    ts = np.arange(T, dtype=np.float64) * 300_000.0

    # Base returns: independent, weak, symmetric mean reversion (a TRIVIAL MR is
    # present for every bar -> baseline mu_rev is slightly > 0). Small vol so the
    # (large, deterministic) over-stretch drift dominates z.
    ret = np.zeros((T, N))
    prev = np.zeros(N)
    for t in range(T):
        r = -0.10 * prev + rng.normal(0.0, 0.0015, N)
        ret[t, :] = r
        prev = r

    # Inject deterministic OVER-STRETCH episodes at fixed, well-separated anchor
    # bars. Each episode gives ONE symbol a single-bar impulse: a sustained level
    # shift across the lookback that stretches its 12-bar time-mean (creating a
    # large |z| at the anchor), immediately followed by a reversion spread over
    # the next 6 bars. In amplify mode the reversion is STRONG (conditioned mu_rev
    # >> baseline); in null mode NO extra reversion is injected — the only MR is
    # the weak symmetric base MR shared by every bar (conditioned ~ baseline).
    strong = 0.020 if amplify else 0.0
    anchors = list(range(30, T - 30, 40))  # ~14 episodes/window, well-separated
    for idx, a in enumerate(anchors):
        j = idx % N
        direction = 1.0 if (idx % 2 == 0) else -1.0
        # sustained level shift across the lookback so the time-mean at the
        # anchor is stretched (one impulse per lookback -> peak |z| at `a`).
        ret[a, j] += direction * 0.030
        # reversion phase over the next 6 bars (opposite to the impulse)
        for hh in range(1, 7):
            ret[a + hh, j] += -direction * strong / 6.0

    px = np.zeros((T, N))
    px[0, :] = 100.0
    for t in range(1, T):
        px[t, :] = px[t - 1, :] * (1.0 + ret[t, :])
    ret2 = np.full((T, N), np.nan)
    ret2[1:, :] = px[1:, :] / px[:-1, :] - 1.0
    return SyncedPanel(ts, SYMBOLS, px, ret2, label)


def test_positive_detection_amplified_consistent_both_windows() -> None:
    # NOTE: with population cross-sectional std over N=5 symbols, |z| is bounded
    # by sqrt(N-1) = 2.0, so the REGISTERED Z_THRESH=2.5 can never fire on a
    # 5-symbol panel (exactly the research_notes §7.5 "5 symbols too tightly
    # constrained" power-risk / N-floor DROP path). These mechanism tests use a
    # reachable z_thresh=1.8 to exercise the amplification logic; the real run
    # keeps the registered 2.5 (CLI default), where the N-floor will reap.
    panels = [_amplified_panel(1, amplify=True, label="A"),
              _amplified_panel(2, amplify=True, label="B")]
    payload = run(panels, window_labels=("A", "B"),
                  z_thresh=1.8, crash_decile=0.9, horizons=(1, 3, 6),
                  n_surrogates=100, n_bootstrap=400, n_floor=30, seed=7)
    assert payload["capital_free"] is True
    # at least one horizon amplified-consistent across both windows
    assert payload["any_amplified_consistent"] is True
    amp = [r for r in payload["horizon_rollup"] if r["amplified_consistent"]]
    assert amp, "expected >=1 amplified-consistent horizon"
    # the passing horizon must pass in >= 2 windows
    assert max(r["n_passing_windows"] for r in payload["horizon_rollup"]) >= 2
    # and for a passing cell, conditioned CI must lie above baseline CI
    passing_h = amp[0]["horizon"]
    cells = [c for c in payload["cells"]
             if c["horizon"] == passing_h and c["ci_nonoverlap_vs_baseline"]]
    assert cells
    c = cells[0]
    assert c["ci_low_conditioned"] > c["ci_high_baseline"]


def test_null_trivial_control_not_amplified() -> None:
    # conditioned behaves exactly like baseline -> only trivial MR, no boost.
    panels = [_amplified_panel(11, amplify=False, label="A"),
              _amplified_panel(12, amplify=False, label="B")]
    payload = run(panels, window_labels=("A", "B"),
                  z_thresh=1.8, crash_decile=0.9, horizons=(1, 3, 6),
                  n_surrogates=100, n_bootstrap=400, n_floor=30, seed=7)
    # CRITICAL: no amplification -> the trivial (E-04-forbidden) reading fails.
    assert payload["any_amplified_consistent"] is False
    # the CIs must overlap in every cell (no non-triviality anchor met)
    for c in payload["cells"]:
        assert c["ci_nonoverlap_vs_baseline"] is False


def test_n_floor_blocks_pass() -> None:
    # amplified panel but N-floor raised absurdly high -> cannot pass.
    panels = [_amplified_panel(1, amplify=True, label="A"),
              _amplified_panel(2, amplify=True, label="B")]
    payload = run(panels, window_labels=("A", "B"),
                  z_thresh=1.8, crash_decile=0.9, horizons=(1, 3, 6),
                  n_surrogates=50, n_bootstrap=200, n_floor=100_000, seed=7)
    assert payload["any_amplified_consistent"] is False
    for c in payload["cells"]:
        assert c["n_floor_met"] is False


def test_capital_free_and_no_forbidden_tokens() -> None:
    panels = [_amplified_panel(1, amplify=True, label="A"),
              _amplified_panel(2, amplify=True, label="B")]
    payload = run(panels, window_labels=("A", "B"),
                  n_surrogates=30, n_bootstrap=100, seed=1)
    assert payload["capital_free"] is True
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "slippage", "edge"):
        assert tok not in blob, f"forbidden capital token in payload: {tok!r}"


def test_run_requires_two_windows() -> None:
    panels = [_amplified_panel(1, amplify=True, label="A")]
    with pytest.raises(ValueError):
        run(panels, window_labels=("A",))


# ---------------------------------------------------------------------------
# End-to-end: synthetic harvester Hive tree + CLI
# ---------------------------------------------------------------------------

def _write_raw_backfill(tmp: Path, symbol: str, date_str: str, rows: list[tuple[int, float]]) -> None:
    """Write a synthetic raw-form parquet (ts_exchange_ms + payload_json)."""
    import duckdb

    d = tmp / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        recs = []
        for ts, price in rows:
            payload = json.dumps({"side": "Buy", "price": f"{price:.4f}",
                                  "size": "0.10", "symbol": symbol})
            recs.append((int(ts), payload))
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", recs)
        out = d / "data.parquet"
        con.execute(f"COPY t TO '{out.as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def _midnight_ms(date_str: str) -> int:
    from datetime import datetime, timezone
    y, m, dd = (int(x) for x in date_str.split("-"))
    return int(datetime(y, m, dd, tzinfo=timezone.utc).timestamp() * 1000)


def _write_symbol_window(tmp: Path, symbol: str, start_date: str, seed: int) -> None:
    """Write ~2 trades per 5-min bar over 2 calendar days for one symbol."""
    rng = np.random.default_rng(seed)
    start_ms = _midnight_ms(start_date)
    bar_ms = 5 * 60_000
    n_bars = 2 * 24 * 12  # 2 days of 5-min bars
    price = 100.0 + seed
    # spread trades across two date dirs (day 0 and day 1)
    from datetime import date, timedelta
    y, m, dd = (int(x) for x in start_date.split("-"))
    d0 = date(y, m, dd)
    day1 = (d0 + timedelta(days=1)).isoformat()
    rows_by_date: dict[str, list[tuple[int, float]]] = {start_date: [], day1: []}
    for b in range(n_bars):
        bar_start = start_ms + b * bar_ms
        price *= (1.0 + rng.normal(0.0, 0.002))
        for k in range(2):
            ts = bar_start + 1000 + k * 60_000
            dstr = start_date if ts < start_ms + 24 * 3600_000 else day1
            rows_by_date[dstr].append((ts, price))
    for dstr, rows in rows_by_date.items():
        if rows:
            _write_raw_backfill(tmp, symbol, dstr, rows)


def test_end_to_end_cli_produces_valid_json(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    for i, sym in enumerate(SYMBOLS):
        _write_symbol_window(base, sym, "2026-04-15", seed=100 + i)
        _write_symbol_window(base, sym, "2026-05-15", seed=200 + i)

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c06_xmr.py"
    env = {"PYTHONPATH": str(REPO_ROOT / "src")}
    import os
    env = {**os.environ, **env}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--n-surrogates", "30", "--n-bootstrap", "100", "--seed", "1"],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    json_path = out_dir / "c06_xmr_results.json"
    md_path = out_dir / "c06_xmr_results.md"
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["capital_free"] is True
    assert payload["hypothesis"] == "H-07"
    assert payload["n_windows"] == 2
    assert len(payload["cells"]) == 2 * 3  # 2 windows x 3 horizons
    # no forbidden capital tokens end-to-end
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction"):
        assert tok not in blob


# ===========================================================================
# H-08 RANK over-stretch mode (DEC-18) — ADDITIONS ONLY, existing tests above
# are unchanged (they ARE the H-07 default-path regression proof).
# ===========================================================================

from bybit_edge.research.c06_xmr.driver import render_markdown  # noqa: E402
from bybit_edge.research.c06_xmr.xsec import (  # noqa: E402
    build_event_table_rank,
    rank_over_stretch_mask,
)


# ---------------------------------------------------------------------------
# Rank-event correctness (axis A, H-08)
# ---------------------------------------------------------------------------

def test_rank_mask_picks_extreme_symbol_per_bar_and_alphabetical_tiebreak() -> None:
    # Known mini panel of time-means; SYMBOLS order is BTC,ETH,SOL,BNB,XRP.
    tm = np.array([
        [0.0, 0.0, 0.0, 0.0, 1.0],    # XRP (idx 4) clearly most extreme
        [0.0, 0.0, 1.0, -1.0, 0.0],   # |z| TIE between SOL (idx 2) and BNB (idx 3)
        [np.nan, 0.0, 0.0, 0.0, 0.5],  # NaN row -> no event at all
    ])
    z = cross_sectional_z(tm)
    mask = rank_over_stretch_mask(z, SYMBOLS)
    # exactly ONE symbol per finite bar, none on the NaN bar
    assert mask[0].sum() == 1 and mask[1].sum() == 1 and mask[2].sum() == 0
    assert mask[0, 4]  # XRPUSDT is the extreme symbol of bar 0
    # tie -> alphabetically FIRST symbol: "BNBUSDT" (idx 3) < "SOLUSDT" (idx 2)
    assert mask[1, 3] and not mask[1, 2]


def test_rank_mask_no_magnitude_threshold_fires_every_finite_bar() -> None:
    # even a nearly flat panel (tiny |z| everywhere) yields one event per bar.
    rng = np.random.default_rng(5)
    tm = rng.normal(0.0, 1e-9, size=(50, 5))
    z = cross_sectional_z(tm)
    mask = rank_over_stretch_mask(z, SYMBOLS)
    finite_rows = np.all(np.isfinite(z), axis=1)
    assert (mask.sum(axis=1)[finite_rows] == 1).all()


def test_rank_mask_symbol_count_mismatch_raises() -> None:
    z = np.zeros((3, 5))
    with pytest.raises(ValueError):
        rank_over_stretch_mask(z, ("A", "B"))


# ---------------------------------------------------------------------------
# z mode N=0 vs rank mode N>0 on the 5-symbol panel (GL-012 structural finding)
# ---------------------------------------------------------------------------

def test_z_default_25_yields_zero_events_rank_yields_positive_n() -> None:
    # On N=5 symbols max|z| = sqrt(N-1) = 2.0 < 2.5 -> the REGISTERED default
    # Z_THRESH can never fire (GL-012). The rank mode fires every bar (after
    # the axis-B filter), so the N-floor becomes satisfiable (registry H-08).
    panels = [_amplified_panel(1, amplify=True, label="A"),
              _amplified_panel(2, amplify=True, label="B")]
    # z mode, registered default threshold 2.5 -> N=0 in every cell
    pz = run(panels, window_labels=("A", "B"), z_thresh=2.5,
             n_surrogates=20, n_bootstrap=50, seed=3)
    assert pz["hypothesis"] == "H-07"
    assert all(c["n_events_conditioned"] == 0 for c in pz["cells"])
    assert all(not c["n_floor_met"] for c in pz["cells"])
    assert pz["any_amplified_consistent"] is False
    # rank mode -> N>0 everywhere and N-floor (30) reachable
    pr = run(panels, window_labels=("A", "B"), overextension="rank",
             n_surrogates=20, n_bootstrap=50, seed=3)
    assert pr["hypothesis"] == "H-08"
    assert all(c["n_events_conditioned"] > 0 for c in pr["cells"])
    assert all(c["n_floor_met"] for c in pr["cells"])  # ~1 event/bar >> 30


def test_rank_event_table_one_event_per_conditioned_bar() -> None:
    panel = _amplified_panel(1, amplify=True, label="A")
    evt = build_event_table_rank(panel, crash_decile=0.9, horizon=1)
    # rank axis A fires every finite bar -> conditioned count is large (>= floor)
    assert evt.n_conditioned >= 30
    # and is bounded by the bar count (at most one event per bar)
    assert evt.n_conditioned <= panel.n_bars


# ---------------------------------------------------------------------------
# Default-path regression: overextension="z" is the unchanged H-07 path
# ---------------------------------------------------------------------------

def test_run_without_overextension_reports_h07_and_matches_explicit_z() -> None:
    panels = [_amplified_panel(1, amplify=True, label="A"),
              _amplified_panel(2, amplify=True, label="B")]
    kw = dict(window_labels=("A", "B"), z_thresh=1.8, crash_decile=0.9,
              horizons=(1, 3, 6), n_surrogates=50, n_bootstrap=200,
              n_floor=30, seed=7)
    p_default = run(panels, **kw)
    # explicit test: run() WITHOUT the overextension argument reports H-07
    assert p_default["hypothesis"] == "H-07"
    assert p_default["fdr_family"] == "F-XMR"
    assert p_default["overextension_mode"] == "z"
    # and is numerically identical to the explicit overextension="z" call
    p_z = run(panels, overextension="z", **kw)
    for key in ("hypothesis", "fdr_family", "overextension_mode",
                "any_amplified_consistent", "n_fdr_significant", "fdr_p_crit"):
        assert p_default[key] == p_z[key]
    # cell-level bit-identity (json.dumps keeps NaN literals comparable)
    assert json.dumps(p_default["cells"]) == json.dumps(p_z["cells"])
    assert json.dumps(p_default["horizon_rollup"]) == json.dumps(p_z["horizon_rollup"])


def test_run_rejects_unknown_overextension_mode() -> None:
    panels = [_amplified_panel(1, amplify=True, label="A"),
              _amplified_panel(2, amplify=True, label="B")]
    with pytest.raises(ValueError):
        run(panels, window_labels=("A", "B"), overextension="perzentil")


# ---------------------------------------------------------------------------
# Synthetic panels for the rank-mode positive / trivial tests
# ---------------------------------------------------------------------------

def _rank_amplified_panel(seed: int, *, amplify: bool, label: str) -> SyncedPanel:
    """Panel where the per-bar RANK-1 (most extreme) symbol reverts strongly.

    At each bar t the cross-sectional-z of the previous bar (window of the last
    L=12 completed bars — exactly the event-table window for an event at t-1)
    is computed; in amplify mode the argmax-|z| symbol receives a strong
    reversion kick in bar t, so rank events revert MORE than the baseline. In
    trivial mode (amplify=False) all returns are i.i.d. noise — the rank-1
    conditioning carries no information (conditioned ~ baseline).
    """
    rng = np.random.default_rng(seed)
    T, N, L = 500, 5, 12
    ts = np.arange(T, dtype=np.float64) * 300_000.0
    kick = 0.004
    ret = np.zeros((T, N))
    for t in range(T):
        r = rng.normal(0.0, 0.002, N)
        if amplify and t >= L + 1:
            window = ret[t - L: t, :]  # rows t-12..t-1 = z window of bar t-1
            tmean = window.mean(axis=0)
            sd = tmean.std()
            if sd > 0.0:
                zrow = (tmean - tmean.mean()) / sd
                j = int(np.argmax(np.abs(zrow)))
                r[j] += -np.sign(zrow[j]) * kick  # revert the rank-1 symbol
        ret[t, :] = r
    px = np.zeros((T, N))
    px[0, :] = 100.0
    for t in range(1, T):
        px[t, :] = px[t - 1, :] * (1.0 + ret[t, :])
    ret2 = np.full((T, N), np.nan)
    ret2[1:, :] = px[1:, :] / px[:-1, :] - 1.0
    return SyncedPanel(ts, SYMBOLS, px, ret2, label)


def test_rank_positive_detection_amplified_consistent() -> None:
    # amplified reversion of the per-bar extremest symbol -> H-08 mechanism
    # detected: amplified_consistent=True (conditioned CI above baseline CI).
    panels = [_rank_amplified_panel(21, amplify=True, label="A"),
              _rank_amplified_panel(22, amplify=True, label="B")]
    payload = run(panels, window_labels=("A", "B"), overextension="rank",
                  crash_decile=0.9, horizons=(1, 3, 6),
                  n_surrogates=100, n_bootstrap=400, n_floor=30, seed=7)
    assert payload["hypothesis"] == "H-08"
    assert payload["fdr_family"] == "F-XMR-RANK"
    assert payload["any_amplified_consistent"] is True
    amp = [r for r in payload["horizon_rollup"] if r["amplified_consistent"]]
    assert amp and max(r["n_passing_windows"] for r in amp) >= 2
    passing_h = amp[0]["horizon"]
    cells = [c for c in payload["cells"]
             if c["horizon"] == passing_h and c["ci_nonoverlap_vs_baseline"]]
    assert cells
    assert cells[0]["ci_low_conditioned"] > cells[0]["ci_high_baseline"]


def test_rank_trivial_control_not_amplified() -> None:
    # conditioned ~ baseline (pure noise) -> CIs overlap -> no amplification.
    panels = [_rank_amplified_panel(31, amplify=False, label="A"),
              _rank_amplified_panel(32, amplify=False, label="B")]
    payload = run(panels, window_labels=("A", "B"), overextension="rank",
                  crash_decile=0.9, horizons=(1, 3, 6),
                  n_surrogates=100, n_bootstrap=400, n_floor=30, seed=7)
    assert payload["any_amplified_consistent"] is False
    for c in payload["cells"]:
        assert c["ci_nonoverlap_vs_baseline"] is False


def test_rank_capital_free_and_no_forbidden_tokens() -> None:
    panels = [_rank_amplified_panel(21, amplify=True, label="A"),
              _rank_amplified_panel(22, amplify=True, label="B")]
    payload = run(panels, window_labels=("A", "B"), overextension="rank",
                  n_surrogates=30, n_bootstrap=100, seed=1)
    assert payload["capital_free"] is True
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "slippage", "edge"):
        assert tok not in blob, f"forbidden capital token in payload: {tok!r}"


def test_rank_render_markdown_reports_mode_and_hypothesis() -> None:
    panels = [_rank_amplified_panel(21, amplify=True, label="A"),
              _rank_amplified_panel(22, amplify=True, label="B")]
    payload = run(panels, window_labels=("A", "B"), overextension="rank",
                  n_surrogates=20, n_bootstrap=50, seed=1)
    md = render_markdown(payload)
    assert "H-08" in md
    assert "F-XMR-RANK" in md
    assert "rank" in md
    # and the z-mode markdown still reports H-07 / F-XMR
    payload_z = run(panels, window_labels=("A", "B"),
                    n_surrogates=20, n_bootstrap=50, seed=1)
    md_z = render_markdown(payload_z)
    assert "H-07" in md_z and "H-08" not in md_z
    assert "F-XMR-RANK" not in md_z


# ---------------------------------------------------------------------------
# End-to-end: CLI with --overextension rank (H-08)
# ---------------------------------------------------------------------------

def test_end_to_end_cli_rank_mode_produces_valid_h08_json(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    for i, sym in enumerate(SYMBOLS):
        _write_symbol_window(base, sym, "2026-04-15", seed=100 + i)
        _write_symbol_window(base, sym, "2026-05-15", seed=200 + i)

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c06_xmr.py"
    import os
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--overextension", "rank",
         "--n-surrogates", "30", "--n-bootstrap", "100", "--seed", "1"],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    json_path = out_dir / "c06_xmr_results.json"
    md_path = out_dir / "c06_xmr_results.md"
    assert json_path.exists() and md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["capital_free"] is True
    assert payload["hypothesis"] == "H-08"
    assert payload["fdr_family"] == "F-XMR-RANK"
    assert payload["overextension_mode"] == "rank"
    assert payload["n_windows"] == 2
    assert len(payload["cells"]) == 2 * 3
    # rank axis A fires every bar -> conditioned N > 0 in every cell
    assert all(c["n_events_conditioned"] > 0 for c in payload["cells"])
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction"):
        assert tok not in blob
    assert "H-08" in md_path.read_text(encoding="utf-8")
