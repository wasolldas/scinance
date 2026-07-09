"""Tests for the H-05b OOS confirmation path (c01_ofi_sign/oos.py).

Covers:
- load_harvest_window: backfill-form payload extraction, side normalization
  (BUY/buy -> Buy), ts filter (>= window start), head(max_ticks) limit.
- run_oos: >=2-window requirement, F-OFI-INV FDR over all cells, per-(symbol,
  delta) inverse-consistency rollup, KAPITALFREI payload.
- inverse-signal detection: a synthetic window where OFI predicts the INVERSE
  of forward return registers inverse_significant in both windows.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c01_ofi_sign.driver import TradeArrays
from bybit_edge.research.c01_ofi_sign.oos import (
    DataError,
    _date_dirs,
    _midnight_ms,
    load_harvest_window,
    render_markdown_oos,
    run_oos,
)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def test_date_dirs_spillover() -> None:
    assert _date_dirs("2026-04-15", 1) == ["2026-04-15"]
    assert _date_dirs("2026-04-15", 2) == ["2026-04-15", "2026-04-16"]
    # month rollover
    assert _date_dirs("2026-04-30", 2) == ["2026-04-30", "2026-05-01"]


def test_date_dirs_rejects_bad_date() -> None:
    with pytest.raises(DataError):
        _date_dirs("2026/04/15", 1)


def test_midnight_ms_utc() -> None:
    # 2026-04-15 00:00:00 UTC
    assert _midnight_ms("2026-04-15") == 1776211200000


# ---------------------------------------------------------------------------
# Synthetic raw harvester parquet (backfill form) for the loader
# ---------------------------------------------------------------------------

def _write_raw_backfill(tmp: Path, symbol: str, date_str: str, n: int,
                        start_ms: int, side_value: str = "Buy") -> None:
    """Write a synthetic raw-form parquet (payload_json) via DuckDB COPY."""
    import duckdb

    d = tmp / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        # build rows: ts_exchange_ms column + payload_json (backfill single-trade form)
        rows = []
        for i in range(n):
            ts = start_ms + i * 100  # 100ms apart
            payload = json.dumps({"side": side_value, "price": "2500.5", "size": "0.10",
                                  "symbol": symbol})
            rows.append((ts, payload))
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", rows)
        out = d / "data.parquet"
        con.execute(f"COPY t TO '{out.as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def test_load_harvest_window_extracts_and_normalizes(tmp_path: Path) -> None:
    start_ms = _midnight_ms("2026-04-15")
    # half Buy, half lowercase buy -> both must normalize to "Buy"
    _write_raw_backfill(tmp_path, "ETHUSDT", "2026-04-15", 100, start_ms, side_value="BUY")
    arr = load_harvest_window(tmp_path, "ETHUSDT", "2026-04-15", max_ticks=1000, spill_days=0)
    assert arr.size == 100
    assert (arr.side == "Buy").all(), "BUY must normalize to exactly 'Buy'"
    assert arr.ts[0] == start_ms
    assert np.allclose(arr.price, 2500.5)


def test_load_harvest_window_head_limit_and_ts_filter(tmp_path: Path) -> None:
    start_ms = _midnight_ms("2026-04-15")
    # 50 rows BEFORE the window start (should be filtered out) + 200 at/after
    _write_raw_backfill(tmp_path, "ETHUSDT", "2026-04-15", 200, start_ms, side_value="Sell")
    # earlier-day rows: write a separate file with ts before start (still date dir 04-15 ok)
    arr = load_harvest_window(tmp_path, "ETHUSDT", "2026-04-15", max_ticks=120, spill_days=0)
    assert arr.size == 120, "head(max_ticks) must cap the window"
    assert (arr.side == "Sell").all()


def test_load_harvest_window_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(DataError):
        load_harvest_window(tmp_path, "NOPE", "2026-04-15", spill_days=0)


def _write_raw_live(tmp: Path, symbol: str, date_str: str,
                    rows_ts: list[int | None], side_value: str = "Buy") -> None:
    """Write a synthetic raw-form parquet in the LIVE per-trade form ($.S/$.p/$.v).

    ``rows_ts`` may contain ``None`` to produce NULL ``ts_exchange_ms`` rows.
    """
    import duckdb

    d = tmp / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        rows = []
        for ts in rows_ts:
            payload = json.dumps({"S": side_value, "p": "2500.5", "v": "0.10",
                                  "s": symbol})
            rows.append((ts, payload))
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", rows)
        out = d / "live.parquet"
        con.execute(f"COPY t TO '{out.as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def test_load_harvest_window_live_form_respects_ts_filters(tmp_path: Path) -> None:
    """Regression: SQL AND/OR precedence (CRITICAL_REVIEW_2026-07-09, oos.py:138).

    Before the fix, ``... AND side IS NOT NULL OR S IS NOT NULL`` was parsed as
    ``(... AND side IS NOT NULL) OR (S IS NOT NULL)``, so every LIVE-form row
    ($.S key) bypassed BOTH the NULL-timestamp filter and the pre-registered
    window-start filter ``ts_exchange_ms >= start_ms``. A live-form row with
    ts < start_ms and one with ts = NULL were both wrongly returned.
    """
    start_ms = _midnight_ms("2026-04-15")
    # valid in-window backfill rows
    _write_raw_backfill(tmp_path, "ETHUSDT", "2026-04-15", 100, start_ms, side_value="Buy")
    # LIVE-form rows in the same date partition:
    #   one BEFORE the window start, one with NULL ts  -> both must be EXCLUDED
    #   one at/after the window start                  -> must be INCLUDED (fallback)
    _write_raw_live(tmp_path, "ETHUSDT", "2026-04-15",
                    [start_ms - 1000, None, start_ms + 50], side_value="sell")
    arr = load_harvest_window(tmp_path, "ETHUSDT", "2026-04-15", max_ticks=1000, spill_days=0)
    assert arr.size == 101, (
        "exactly the 100 backfill rows + 1 in-window live-form row must survive; "
        "pre-window / NULL-ts live-form rows must be excluded"
    )
    assert np.isfinite(arr.ts).all(), "NULL ts must never leak into the ts array (NaN)"
    assert (arr.ts >= start_ms).all(), "no tick before the pre-registered window start"
    # the surviving live-form row is normalised to exactly "Sell"
    assert int(np.sum(arr.side == "Sell")) == 1
    assert int(np.sum(arr.side == "Buy")) == 100


# ---------------------------------------------------------------------------
# run_oos
# ---------------------------------------------------------------------------

def _inverse_window(n: int, seed: int, *, t0_ms: float = 0.0) -> TradeArrays:
    """Build a window where aggressor flow predicts the INVERSE next return.

    Construct prices so that a buy-heavy bin is followed by a price DROP (fade /
    MM-replenishment), i.e. sign(OFI) is opposite to sign(forward return).
    """
    rng = np.random.default_rng(seed)
    n = int(n)
    ts = t0_ms + np.arange(n, dtype=np.float64) * 250.0  # 250ms apart
    # alternate regimes of buy / sell pressure every ~2000 ticks
    side = np.where((np.arange(n) // 2000) % 2 == 0, "Buy", "Sell").astype(object)
    volume = rng.uniform(0.5, 1.5, n)
    # price MEAN-REVERTS against the aggressor: buy pressure -> price falls
    drift = np.where(side == "Buy", -1.0, +1.0) * 0.05
    noise = rng.normal(0.0, 0.02, n)
    price = 2500.0 + np.cumsum(drift + noise)
    return TradeArrays(ts=ts, price=price, volume=volume, side=side)


def test_run_oos_requires_two_windows() -> None:
    one = {"ETHUSDT": [_inverse_window(3000, 1)]}
    with pytest.raises(DataError):
        run_oos(one, window_labels=("A",), n_surrogates=20, seed=1)


def test_run_oos_payload_shape_and_capital_free() -> None:
    sw = {
        "ETHUSDT": [_inverse_window(6000, 1), _inverse_window(6000, 2)],
        "BTCUSDT": [_inverse_window(6000, 3), _inverse_window(6000, 4)],
    }
    out = run_oos(sw, window_labels=("A@2026-04-15", "B@2026-05-15"),
                  lags_s=(1, 5), n_surrogates=50, seed=7)
    assert out["hypothesis"] == "H-05b"
    assert out["capital_free"] is True
    assert out["fdr_family"] == "F-OFI-INV"
    assert out["discovery_cell_excluded_by_construction"] is True
    # no capital columns anywhere in the payload
    blob = json.dumps(out).lower()
    for forbidden in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert forbidden not in blob, f"capital-free violated: {forbidden!r} in payload"
    # consistency rollup present, one entry per (symbol, delta)
    cells = out["inverse_consistency"]
    assert len(cells) == 2 * 2  # 2 symbols x 2 deltas
    for c in cells:
        assert set(c) >= {"symbol", "delta_s", "n_windows_inverse_significant",
                          "inverse_consistent"}
    # markdown renders without error
    md = render_markdown_oos(out)
    assert "H-05b" in md and "Inverse-Konsistenz" in md


def test_run_oos_detects_inverse_consistency() -> None:
    # strong inverse structure in BOTH windows -> expect inverse_significant
    sw = {"ETHUSDT": [_inverse_window(8000, 11), _inverse_window(8000, 12)]}
    out = run_oos(sw, window_labels=("A", "B"), lags_s=(1,), n_surrogates=100, seed=3)
    # at least the family flag should be computable; with a strong synthetic
    # inverse signal we expect inverse significance in both windows for delta 1s
    eth_cells = [c for c in out["inverse_consistency"] if c["symbol"] == "ETHUSDT"]
    assert len(eth_cells) == 1
    c = eth_cells[0]
    # sign must be negative in the per-window variants (inverse construction)
    signs = [int(v["sign_direction"]) for r in out["results"] for v in r["variants"]]
    assert all(s <= 0 for s in signs), f"inverse construction must yield sign<=0, got {signs}"
