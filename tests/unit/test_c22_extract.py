"""Unit tests for WP-2 — L2 snapshot+delta book replay + tilt (KAPITALFREI).

  (a) book mechanics: snapshot replace, delta upsert, size "0" delete,
  (b) tilt math on a hand-built book (band membership, sign, mid),
  (c) sequence-break accounting: non-contiguous u counts a break but the
      delta is still applied; snapshot mismatch counts a break AND resyncs,
  (d) day discard: > 10 breaks discards LOUDLY; first day before any
      snapshot is discarded, later days inherit carried state,
  (e) minute sampling reflects the state AT the boundary,
  (f) determinism: two full window passes are hash-identical,
  (g) daily median + coverage load path.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c22_l2tilt.extract import (
    Book,
    extract_window,
    load_daily_tilt,
    tilt_fingerprint,
)

EPOCH = date(1970, 1, 1)


# ----------------------------------------------------------------------------
# (a)/(b)/(c) book mechanics + tilt
# ----------------------------------------------------------------------------

def test_book_snapshot_delta_and_delete():
    bk = Book()
    bk.apply_snapshot([["100.0", "2"], ["99.5", "1"]],
                      [["100.5", "1"], ["101.0", "3"]], u=10)
    assert bk.apply_delta([["100.0", "5"]], [], u=11) is True     # update level
    assert bk.bids["100.0"] == 5.0
    assert bk.apply_delta([], [["100.5", "0"]], u=12) is True     # delete level
    assert "100.5" not in bk.asks
    assert bk.apply_delta([["99.0", "4"]], [], u=14) is False     # gap: 12 -> 14
    assert bk.bids["99.0"] == 4.0, "delta must still be applied on a gap"


def test_tilt_band_and_sign():
    bk = Book()
    # mid = 100.0; +-25bp band = [99.75, 100.25]
    bk.apply_snapshot(
        [["99.9", "3"], ["99.8", "2"], ["99.0", "50"]],     # 99.0 outside band
        [["100.1", "1"], ["100.2", "1"], ["101.0", "50"]],  # 101.0 outside
        u=1)
    tilt, mid = bk.tilt()
    assert mid == pytest.approx(100.0)
    assert tilt == pytest.approx((5.0 - 2.0) / (5.0 + 2.0))
    bk2 = Book()
    bk2.apply_snapshot([["99.9", "1"]], [["100.1", "4"]], u=1)
    t2, _ = bk2.tilt()
    assert t2 == pytest.approx((1 - 4) / 5.0), "ask-heavy book => negative tilt"


def test_snapshot_mismatch_detection():
    bk = Book()
    bk.apply_snapshot([["100.0", "2"]], [["100.5", "1"]], u=1)
    assert bk.matches_snapshot([["100.0", "2"]], [["100.5", "1"]])
    assert not bk.matches_snapshot([["100.0", "3"]], [["100.5", "1"]])


# ----------------------------------------------------------------------------
# fixture: synthetic orderbook partitions
# ----------------------------------------------------------------------------

def _write_day(base: Path, symbol: str, day: str, records: list[dict]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = (base / "raw" / "bybit" / "orderbook" / f"symbol={symbol}"
         / f"date={day}")
    d.mkdir(parents=True, exist_ok=True)
    ts = [r["ts"] for r in records]
    payloads = [json.dumps(r) for r in records]
    n = len(records)
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 10**6 for t in ts], pa.int64()),
        "ts_exchange_ms": pa.array(ts, pa.int64()),
        "topic": pa.array(["orderbook"] * n), "stream": pa.array(["orderbook"] * n),
        "symbol": pa.array([symbol] * n), "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _snap(ts: int, u: int, bid: float, ask: float, bsz: float = 2.0,
          asz: float = 2.0) -> dict:
    return {"topic": "orderbook.500.TST", "type": "snapshot", "ts": ts,
            "data": {"s": "TST", "b": [[f"{bid}", f"{bsz}"]],
                     "a": [[f"{ask}", f"{asz}"]], "u": u}}


def _delta(ts: int, u: int, b: list, a: list) -> dict:
    return {"topic": "orderbook.500.TST", "type": "delta", "ts": ts,
            "data": {"s": "TST", "b": b, "a": a, "u": u}}


def _day_ms(day: str) -> int:
    return (date.fromisoformat(day) - EPOCH).days * 86_400_000


# ----------------------------------------------------------------------------
# (d)/(e)/(f)/(g) window extraction
# ----------------------------------------------------------------------------

def test_extraction_samples_carries_state_and_is_deterministic(tmp_path):
    base = tmp_path / "h"
    d1, d2 = "2023-07-01", "2023-07-02"
    ms1, ms2 = _day_ms(d1), _day_ms(d2)
    # day 1: snapshot at 00:00:30, one delta at 00:02:30 flips the tilt
    _write_day(base, "TSTUSDT", d1, [
        _snap(ms1 + 30_000, 1, 99.9, 100.1, bsz=3.0, asz=1.0),
        _delta(ms1 + 150_000, 2, [["99.9", "1"]], [["100.1", "3"]]),
    ])
    # day 2: NO snapshot — must inherit carried state and still be ok
    _write_day(base, "TSTUSDT", d2, [
        _delta(ms2 + 60_500, 3, [["99.9", "5"]], []),
    ])
    out = tmp_path / "o"
    s = extract_window(base, out, "TSTUSDT", d1, d2)
    assert s["ok"] == 2 and s["discarded"] == 0 and s["total_seq_breaks"] == 0

    daily = load_daily_tilt(out, "bybit", "TSTUSDT", d1, d2)
    assert daily["day_idx"].size == 2
    # day 1: minute 0 has no valid book yet (snapshot at 00:00:30 => first
    # sample at boundary 00:01 reflects the snapshot: tilt=(3-1)/4=+0.5;
    # minute boundary 00:03 reflects the delta: (1-3)/4=-0.5
    import pyarrow.parquet as pq
    part = out / "tilt_1min" / "exchange=bybit" / "symbol=TSTUSDT" / f"date={d1}"
    t = pq.read_table(part / "tilt.parquet").to_pydict()
    assert t["minute_idx"][0] == ms1 // 60_000, "first sample at minute 1 boundary"
    assert t["tilt"][0] == pytest.approx(0.5)
    assert t["tilt"][2] == pytest.approx(-0.5)
    # snapshot at 00:00:30 precedes the FIRST boundary (00:01) -> the
    # minute-0 closing sample exists and the day is complete
    assert len(t["tilt"]) == 1440
    # day 2 inherits: 1440 samples, tilt after its delta = (5-3)/8
    part2 = out / "tilt_1min" / "exchange=bybit" / "symbol=TSTUSDT" / f"date={d2}"
    t2 = pq.read_table(part2 / "tilt.parquet").to_pydict()
    assert len(t2["tilt"]) == 1440
    assert t2["tilt"][-1] == pytest.approx((5 - 3) / 8.0)

    # determinism: a second full pass into a fresh dir is hash-identical
    out2 = tmp_path / "o2"
    extract_window(base, out2, "TSTUSDT", d1, d2)
    fp1 = tilt_fingerprint(out, "bybit", "TSTUSDT", d1, d2)
    fp2 = tilt_fingerprint(out2, "bybit", "TSTUSDT", d1, d2)
    assert fp1["sha256_values"] == fp2["sha256_values"]
    assert fp1["n_ok_days"] == 2


def test_first_day_without_snapshot_is_discarded_loudly(tmp_path):
    base = tmp_path / "h"
    d1 = "2023-07-01"
    _write_day(base, "TSTUSDT", d1, [
        _delta(_day_ms(d1) + 1000, 5, [["99.9", "1"]], [["100.1", "1"]]),
    ])
    out = tmp_path / "o"
    s = extract_window(base, out, "TSTUSDT", d1, d1)
    assert s["discarded"] == 1 and s["ok"] == 0
    meta = json.loads((out / "tilt_1min" / "exchange=bybit" / "symbol=TSTUSDT"
                       / f"date={d1}" / "manifest.json").read_text())
    assert meta["status"] == "discarded" and "no snapshot" in meta["reason"]


def test_break_budget_discards_day_and_resets_book(tmp_path):
    base = tmp_path / "h"
    d1 = "2023-07-01"
    ms = _day_ms(d1)
    records = [_snap(ms + 1000, 1, 99.9, 100.1)]
    u = 1
    for k in range(12):                     # 12 gapped deltas -> 12 breaks
        u += 2
        records.append(_delta(ms + 2000 + k * 1000, u,
                              [["99.9", "2"]], []))
    _write_day(base, "TSTUSDT", d1, records)
    out = tmp_path / "o"
    s = extract_window(base, out, "TSTUSDT", d1, d1)
    assert s["discarded"] == 1 and s["total_seq_breaks"] == 12
    meta = json.loads((out / "tilt_1min" / "exchange=bybit" / "symbol=TSTUSDT"
                       / f"date={d1}" / "manifest.json").read_text())
    assert "sequence breaks" in meta["reason"]


def test_snapshot_mismatch_counts_break_and_resyncs(tmp_path):
    base = tmp_path / "h"
    d1 = "2023-07-01"
    ms = _day_ms(d1)
    _write_day(base, "TSTUSDT", d1, [
        _snap(ms + 1000, 1, 99.9, 100.1, bsz=3.0, asz=1.0),
        # second snapshot deviates from the replayed state (no delta between)
        _snap(ms + 120_000, 5, 99.9, 100.1, bsz=1.0, asz=3.0),
    ])
    out = tmp_path / "o"
    s = extract_window(base, out, "TSTUSDT", d1, d1)
    assert s["ok"] == 1 and s["total_seq_breaks"] == 1
    daily = load_daily_tilt(out, "bybit", "TSTUSDT", d1, d1)
    # after resync the book is ask-heavy: median over the day is negative
    assert daily["tilt_median"][0] < 0


def test_no_raw_days_reduce_coverage_only(tmp_path):
    base = tmp_path / "h"
    d1, d3 = "2023-07-01", "2023-07-03"
    _write_day(base, "TSTUSDT", d1, [_snap(_day_ms(d1) + 1000, 1, 99.9, 100.1)])
    _write_day(base, "TSTUSDT", d3, [_snap(_day_ms(d3) + 1000, 9, 99.9, 100.1)])
    out = tmp_path / "o"
    s = extract_window(base, out, "TSTUSDT", d1, d3)
    assert s["ok"] == 2 and s["no_raw"] == 1


# ----------------------------------------------------------------------------
# WP-4: spread census (DEC-40)
# ----------------------------------------------------------------------------

def test_spread_extraction_samples_correct_bp(tmp_path):
    from bybit_edge.research.c22_l2tilt.extract import (
        extract_spread_window, load_daily_spread)
    base = tmp_path / "h"
    d1 = "2026-07-01"
    ms = _day_ms(d1)
    # best bid 99.9, best ask 100.1 -> mid 100.0, spread 0.2 -> 20 bp;
    # a delta later tightens to 99.95/100.05 -> 10 bp
    _write_day(base, "TSTUSDT", d1, [
        _snap(ms + 1000, 1, 99.9, 100.1),
        _delta(ms + 300_000, 2, [["99.95", "1"]], [["100.05", "1"]]),
    ])
    out = tmp_path / "o"
    s = extract_spread_window(base, out, "TSTUSDT", d1, d1)
    assert s["ok"] == 1 and s["total_seq_breaks"] == 0
    daily = load_daily_spread(out, "bybit", "TSTUSDT", d1, d1)
    assert daily["day_idx"].size == 1
    import pyarrow.parquet as pq
    part = (out / "spread_1min" / "exchange=bybit" / "symbol=TSTUSDT"
            / f"date={d1}")
    t = pq.read_table(part / "spread.parquet").to_pydict()
    assert t["spread_bp"][0] == pytest.approx(20.0, rel=1e-9)
    assert t["spread_bp"][-1] == pytest.approx(10.0, rel=1e-9)
    # the daily median mixes 5 minutes at 20bp and the rest at 10bp
    assert daily["spread_median_bp"][0] == pytest.approx(10.0, rel=1e-9)
    assert daily["spread_p90_bp"][0] <= 20.0 + 1e-9


def test_spread_store_is_separate_from_frozen_tilt_store(tmp_path):
    from bybit_edge.research.c22_l2tilt.extract import extract_spread_window
    base = tmp_path / "h"
    d1 = "2026-07-01"
    _write_day(base, "TSTUSDT", d1, [_snap(_day_ms(d1) + 1000, 1, 99.9, 100.1)])
    out = tmp_path / "o"
    extract_window(base, out, "TSTUSDT", d1, d1)          # WP-2 tilt store
    fp_before = tilt_fingerprint(out, "bybit", "TSTUSDT", d1, d1)
    extract_spread_window(base, out, "TSTUSDT", d1, d1)   # WP-4 spread store
    fp_after = tilt_fingerprint(out, "bybit", "TSTUSDT", d1, d1)
    assert fp_before["sha256_values"] == fp_after["sha256_values"], (
        "the WP-4 pass must never touch the frozen WP-2 tilt store")
    assert (out / "spread_1min").is_dir() and (out / "tilt_1min").is_dir()


def test_spread_extraction_is_deterministic(tmp_path):
    from bybit_edge.research.c22_l2tilt.extract import (
        extract_spread_window, load_daily_spread)
    base = tmp_path / "h"
    d1, d2 = "2026-07-01", "2026-07-02"
    _write_day(base, "TSTUSDT", d1, [
        _snap(_day_ms(d1) + 1000, 1, 99.9, 100.1),
        _delta(_day_ms(d1) + 400_000, 2, [["99.8", "2"]], []),
    ])
    _write_day(base, "TSTUSDT", d2, [
        _delta(_day_ms(d2) + 60_500, 3, [], [["100.2", "1"]]),
    ])
    r1, r2 = tmp_path / "o1", tmp_path / "o2"
    extract_spread_window(base, r1, "TSTUSDT", d1, d2)
    extract_spread_window(base, r2, "TSTUSDT", d1, d2)
    a = load_daily_spread(r1, "bybit", "TSTUSDT", d1, d2)
    b = load_daily_spread(r2, "bybit", "TSTUSDT", d1, d2)
    assert np.array_equal(a["spread_median_bp"], b["spread_median_bp"])
    assert a["day_idx"].size == 2, "day 2 inherits carried state"
