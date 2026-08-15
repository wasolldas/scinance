"""Unit tests for the WP-0 shared 1-minute bar cache (DEC-34/35, KAPITALFREI).

The cache exists because DEC-34 established the raw-tick aggregation path is
non-deterministic. These tests pin the properties that make the cache the
Wave-6 antidote:

  (a) every bar column is an ORDER-INDEPENDENT aggregate — pinned on a
      fixture with a same-millisecond price tie (the exact ambiguity DEC-34
      suspects) and verified byte-identical across independent builds,
  (b) both payload forms are read: flat rows AND live envelopes (per-trade
      timestamps, not the packet timestamp), with cross-form dedup,
  (c) volumes are exact-decimal sums from the ORIGINAL strings (0.1 x 10
      == 1.0 exactly, no float association error), unparsable sizes are
      counted, never silently dropped,
  (d) immutability: a cached day is never rebuilt unless forced; a
      sidecar-less or version-alien partition refuses to load,
  (e) DONE-day gating: only harvest-manifest-DONE days are frozen; a
      missing manifest is a loud error, never a folder-scan fallback,
  (f) loud-fail: raw rows present but 0 parsable trades -> BarCacheError,
  (g) the range fingerprint (quoted by every Wave-6 registration) is
      sensitive to a single changed value.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.bar_cache import (
    BAR_COLUMNS,
    BarCacheError,
    SCHEMA_VERSION,
    bars_fingerprint,
    build_day,
    build_range,
    load_minute_bars,
    manifest_done_days,
)

EPOCH = date(1970, 1, 1)


def _day_ms(day_iso: str) -> int:
    return (date.fromisoformat(day_iso) - EPOCH).days * 86_400_000


def _write_partition(base: Path, symbol: str, day_iso: str,
                     ts_ms: list[int], payloads: list[str],
                     stream: str = "publicTrade", exchange: str = "bybit") -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={day_iso}"
    d.mkdir(parents=True, exist_ok=True)
    n = len(ts_ms)
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts_ms], pa.int64()),
        "ts_exchange_ms": pa.array(ts_ms, pa.int64()),
        "topic": pa.array([stream] * n, pa.string()),
        "stream": pa.array([stream] * n, pa.string()),
        "symbol": pa.array([symbol] * n, pa.string()),
        "payload_json": pa.array(payloads, pa.string()),
    }), d / "part-0.parquet")


def _write_manifest(base: Path, rows) -> None:
    mdir = base / "state"
    mdir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(mdir / "harvest_manifest.sqlite")
    try:
        con.execute("CREATE TABLE partitions "
                    "(exchange TEXT, stream TEXT, symbol TEXT, date TEXT, status TEXT)")
        con.executemany("INSERT INTO partitions VALUES (?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()


def _mixed_day(base: Path, symbol: str, day: str) -> None:
    """Flat rows with a same-ms price tie + one live envelope + a bad size."""
    ms = _day_ms(day)
    ts = [ms + 1000, ms + 1000, ms + 2000, ms + 61_000, ms + 120_500]
    payloads = [
        json.dumps({"side": "Buy", "price": "100.0", "size": "0.1"}),
        json.dumps({"side": "Sell", "price": "101.0", "size": "0.1"}),
        json.dumps({"side": "Buy", "price": "102.5", "size": "0.3"}),
        json.dumps({"side": "Sell", "price": "103.0", "size": "bad"}),
        json.dumps({"topic": f"publicTrade.{symbol}", "type": "snapshot",
                    "ts": ms + 120_500,
                    "data": [
                        {"T": ms + 120_100, "S": "Buy", "v": "0.2",
                         "p": "104.0", "i": "e1"},
                        {"T": ms + 120_200, "S": "Sell", "v": "0.1",
                         "p": "103.5", "i": "e2"},
                    ]}),
    ]
    _write_partition(base, symbol, day, ts, payloads)


@pytest.fixture()
def duck():
    import duckdb
    con = duckdb.connect()
    yield con
    con.close()


# ----------------------------------------------------------------------------
# (a) determinism: tie-break pinned, independent builds byte-identical
# ----------------------------------------------------------------------------

def test_same_millisecond_tie_break_is_pinned(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    bars = load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    m0 = 0  # first minute: 100.0/101.0 tie at +1000ms, then 102.5 at +2000ms
    assert bars["px_first"][m0] == 100.0, "arg_min((ts,px)): lower price wins the tie"
    assert bars["px_last"][m0] == 102.5
    assert bars["px_high"][m0] == 102.5 and bars["px_low"][m0] == 100.0
    # drop the later trade -> the tie IS the last ts; higher price must win
    base2, cache2 = tmp_path / "h2", tmp_path / "c2"
    ms = _day_ms("2024-01-02")
    _write_partition(base2, "TSTUSDT", "2024-01-02", [ms + 1000, ms + 1000], [
        json.dumps({"side": "Buy", "price": "100.0", "size": "0.1"}),
        json.dumps({"side": "Sell", "price": "101.0", "size": "0.1"})])
    build_day(duck, base2, cache2, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    b2 = load_minute_bars(cache2, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    assert b2["px_last"][0] == 101.0, "arg_max((ts,px)): higher price wins the tie"
    assert b2["px_first"][0] == 100.0


def test_independent_builds_are_byte_identical(tmp_path, duck):
    base = tmp_path / "h"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    fps = []
    for name in ("c1", "c2", "c3"):
        build_day(duck, base, tmp_path / name, "bybit", "publicTrade",
                  "TSTUSDT", "2024-01-02")
        fps.append(bars_fingerprint(tmp_path / name, "bybit", "TSTUSDT",
                                    "2024-01-02", "2024-01-02")["sha256_values"])
    assert len(set(fps)) == 1, f"builds must be byte-identical, got {fps}"


# ----------------------------------------------------------------------------
# (b) both payload forms, per-trade envelope timestamps, cross-form dedup
# ----------------------------------------------------------------------------

def test_envelope_expanded_on_per_trade_timestamp(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    bars = load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    assert bars["minute_idx"].size == 3
    m2 = 2  # envelope minute: T=+120100 (104.0 Buy) then T=+120200 (103.5 Sell)
    assert bars["px_first"][m2] == 104.0 and bars["px_last"][m2] == 103.5
    assert bars["n_trades"][m2] == 2
    assert bars["vol_buy"][m2] == 0.2 and bars["vol_sell"][m2] == 0.1


def test_cross_form_duplicate_counted_once(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    ms = _day_ms("2024-01-02")
    flat = json.dumps({"side": "Buy", "price": "100.0", "size": "0.5",
                       "trdMatchID": "dup-1"})
    env = json.dumps({"topic": "publicTrade.TSTUSDT", "type": "snapshot",
                      "ts": ms + 1500,
                      "data": [{"T": ms + 1000, "S": "Buy", "v": "0.5",
                                "p": "100.0", "i": "dup-1"}]})
    _write_partition(base, "TSTUSDT", "2024-01-02", [ms + 1000, ms + 1500],
                     [flat, env])
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    bars = load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    assert bars["n_trades"][0] == 1, "same trade id in both forms = ONE trade"
    assert bars["vol_total"][0] == 0.5, "signed volume must not double-count"


# ----------------------------------------------------------------------------
# (c) exact-decimal volume sums
# ----------------------------------------------------------------------------

def test_volume_sum_is_exact_decimal_not_float_association(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    ms = _day_ms("2024-01-02")
    n = 10
    _write_partition(base, "TSTUSDT", "2024-01-02",
                     [ms + 1000 + i for i in range(n)],
                     [json.dumps({"side": "Buy", "price": "100.0", "size": "0.1"})
                      for _ in range(n)])
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    bars = load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    assert bars["vol_buy"][0] == 1.0, "10 x '0.1' must sum to exactly 1.0 (decimal)"
    assert bars["n_size_unparsed"][0] == 0


def test_unparsable_size_is_counted_never_dropped(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    bars = load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    assert bars["n_size_unparsed"][1] == 1   # the "bad" size
    assert bars["n_trades"][1] == 1          # the trade itself stays counted


# ----------------------------------------------------------------------------
# (d) immutability + refusing half-written or version-alien partitions
# ----------------------------------------------------------------------------

def test_cached_day_is_immutable_unless_rebuild(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    assert build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT",
                     "2024-01-02")["status"] == "cached"
    assert build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT",
                     "2024-01-02")["status"] == "exists"
    assert build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT",
                     "2024-01-02", rebuild=True)["status"] == "cached"


def test_load_refuses_sidecarless_and_alien_partitions(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    part = (cache / "bars_1min" / "exchange=bybit" / "symbol=TSTUSDT"
            / "date=2024-01-02")
    meta = part / "manifest.json"
    saved = meta.read_text(encoding="utf-8")
    meta.unlink()
    with pytest.raises(BarCacheError, match="sidecar"):
        load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")
    alien = json.loads(saved)
    alien["schema_version"] = SCHEMA_VERSION + 1
    meta.write_text(json.dumps(alien), encoding="utf-8")
    with pytest.raises(BarCacheError, match="schema_version"):
        load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-02")


# ----------------------------------------------------------------------------
# (e) manifest-DONE gating
# ----------------------------------------------------------------------------

def test_build_range_freezes_only_manifest_done_days(tmp_path):
    base, cache = tmp_path / "h", tmp_path / "c"
    days = ["2024-01-02", "2024-01-03", "2024-01-04"]
    for d in days:
        _mixed_day(base, "TSTUSDT", d)
    _write_manifest(base, [
        ("bybit", "publicTrade", "TSTUSDT", "2024-01-02", "DONE"),
        ("bybit", "publicTrade", "TSTUSDT", "2024-01-03", "PARTIAL"),
        ("bybit", "publicTrade", "TSTUSDT", "2024-01-04", "DONE"),
    ])
    summary = build_range(base, cache, "bybit", "publicTrade", "TSTUSDT",
                          "2024-01-02", "2024-01-04")
    assert summary["cached"] == 2 and summary["days_not_done"] == 1
    bars = load_minute_bars(cache, "bybit", "TSTUSDT", "2024-01-02", "2024-01-04")
    days_present = np.unique(bars["minute_idx"] * 60_000 // 86_400_000)
    assert days_present.size == 2, "the PARTIAL day must not be frozen"


def test_missing_manifest_is_loud_never_folder_fallback(tmp_path):
    base = tmp_path / "h"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    with pytest.raises(BarCacheError, match="manifest"):
        manifest_done_days(base, "bybit", "publicTrade", "TSTUSDT",
                           "2024-01-02", "2024-01-02")
    with pytest.raises(BarCacheError, match="manifest"):
        build_range(base, tmp_path / "c", "bybit", "publicTrade", "TSTUSDT",
                    "2024-01-02", "2024-01-02")


# ----------------------------------------------------------------------------
# (f) loud-fail on parsable-trade starvation
# ----------------------------------------------------------------------------

def test_raw_rows_but_zero_parsable_trades_raises(tmp_path, duck):
    base, cache = tmp_path / "h", tmp_path / "c"
    ms = _day_ms("2024-01-02")
    _write_partition(base, "TSTUSDT", "2024-01-02", [ms + 1000, ms + 2000],
                     [json.dumps({"weird": "1"}), json.dumps({"weird": "2"})])
    with pytest.raises(BarCacheError, match="0 parsable"):
        build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT",
                  "2024-01-02")


# ----------------------------------------------------------------------------
# (g) fingerprint sensitivity
# ----------------------------------------------------------------------------

def test_fingerprint_flips_on_a_single_value(tmp_path, duck):
    import pyarrow.parquet as pq
    import pyarrow as pa
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    build_day(duck, base, cache, "bybit", "publicTrade", "TSTUSDT", "2024-01-02")
    fp0 = bars_fingerprint(cache, "bybit", "TSTUSDT",
                           "2024-01-02", "2024-01-02")["sha256_values"]
    part = (cache / "bars_1min" / "exchange=bybit" / "symbol=TSTUSDT"
            / "date=2024-01-02")
    table = pq.read_table(part / "bars.parquet")
    px = table.column("px_last").to_numpy(zero_copy_only=False).copy()
    px[0] = np.nextafter(px[0], np.inf)  # one last-bit change
    cols = {c: table.column(c) for c in table.column_names}
    cols["px_last"] = pa.array(px, pa.float64())
    pq.write_table(pa.table(cols), part / "bars.parquet")
    fp1 = bars_fingerprint(cache, "bybit", "TSTUSDT",
                           "2024-01-02", "2024-01-02")["sha256_values"]
    assert fp0 != fp1


def test_empty_range_returns_typed_empty_arrays(tmp_path):
    bars = load_minute_bars(tmp_path / "c", "bybit", "TSTUSDT",
                            "2024-01-02", "2024-01-03")
    assert set(bars) == set(BAR_COLUMNS)
    assert all(v.size == 0 for v in bars.values())
    assert bars["minute_idx"].dtype == np.int64
    assert bars["px_last"].dtype == np.float64


# ----------------------------------------------------------------------------
# (h) end-to-end CLI on a synthetic tree
# ----------------------------------------------------------------------------

def test_e2e_cli_builds_and_prints_fingerprint(tmp_path):
    import subprocess
    import sys as _sys
    base, cache = tmp_path / "h", tmp_path / "c"
    days = ["2024-01-02", "2024-01-03"]
    for d in days:
        _mixed_day(base, "TSTUSDT", d)
    _write_manifest(base, [("bybit", "publicTrade", "TSTUSDT", d, "DONE")
                           for d in days])
    repo = Path(__file__).resolve().parents[2]
    env = {"PYTHONPATH": str(repo / "src"), "PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        [_sys.executable, str(repo / "scripts" / "build_bar_cache.py"),
         "--base-dir", str(base), "--cache-dir", str(cache),
         "--symbols", "TSTUSDT", "--start", days[0], "--end", days[-1]],
        capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    s = out["summaries"][0]
    assert s["cached"] == 2 and s["fingerprint"]["n_days_present"] == 2
    # second invocation is a pure no-op with the identical fingerprint
    proc2 = subprocess.run(
        [_sys.executable, str(repo / "scripts" / "build_bar_cache.py"),
         "--base-dir", str(base), "--cache-dir", str(cache),
         "--symbols", "TSTUSDT", "--start", days[0], "--end", days[-1]],
        capture_output=True, text=True, env=env, timeout=120)
    s2 = json.loads(proc2.stdout)["summaries"][0]
    assert s2["exists"] == 2 and s2["cached"] == 0
    assert s2["fingerprint"]["sha256_values"] == s["fingerprint"]["sha256_values"]


# ----------------------------------------------------------------------------
# (i) memory discipline (DEC-36): capped connection, OOM retry, loud second OOM
# ----------------------------------------------------------------------------

def test_memory_limit_is_validated_and_applied(tmp_path):
    from bybit_edge.research.bar_cache import _connect
    with pytest.raises(ValueError, match="memory limit"):
        _connect(tmp_path, "4GB'; DROP TABLE x; --")
    con = _connect(tmp_path, "512MB")
    try:
        limit = con.execute(
            "SELECT value FROM duckdb_settings() WHERE name='memory_limit'"
        ).fetchone()[0]
        # duckdb normalises units (512MB -> "488.2 MiB"); assert the cap took
        # effect and is far below the unlimited default (~80% of RAM)
        value, unit = limit.split()
        assert unit in ("KiB", "MiB") and float(value) <= 600.0, limit
        order = con.execute(
            "SELECT value FROM duckdb_settings() WHERE name='preserve_insertion_order'"
        ).fetchone()[0]
        assert order == "false"
    finally:
        con.close()
    assert (tmp_path / "_ducktmp").is_dir(), "spill directory must exist"


def test_oom_day_gets_one_fresh_connection_retry(tmp_path, monkeypatch):
    import duckdb
    from bybit_edge.research import bar_cache as bc
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")
    real_build_day = bc.build_day
    calls = {"n": 0}

    def flaky(con, *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise duckdb.OutOfMemoryException("Out of Memory Error: simulated")
        return real_build_day(con, *a, **k)

    monkeypatch.setattr(bc, "build_day", flaky)
    summary = bc.build_range(base, cache, "bybit", "publicTrade", "TSTUSDT",
                             "2024-01-02", "2024-01-02",
                             require_manifest_done=False)
    assert summary["cached"] == 1 and calls["n"] == 2, (
        "one OOM must trigger exactly one retry on a fresh connection")


def test_second_oom_is_a_loud_barcache_error_naming_the_day(tmp_path, monkeypatch):
    import duckdb
    from bybit_edge.research import bar_cache as bc
    base, cache = tmp_path / "h", tmp_path / "c"
    _mixed_day(base, "TSTUSDT", "2024-01-02")

    def always_oom(con, *a, **k):
        raise duckdb.OutOfMemoryException("Out of Memory Error: simulated")

    monkeypatch.setattr(bc, "build_day", always_oom)
    with pytest.raises(BarCacheError, match="2024-01-02.*OOM"):
        bc.build_range(base, cache, "bybit", "publicTrade", "TSTUSDT",
                       "2024-01-02", "2024-01-02",
                       require_manifest_done=False)
