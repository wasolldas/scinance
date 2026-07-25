"""Fixture tests for venue-native payload_json dialects in the read path.

The harvester stores an identical 7-column container schema everywhere, but
the payload_json CONTENTS are venue-native. These tests pin, with REAL
duckdb over synthetic mini-parquets in tmp_path, that the c14/c17 read-only
loaders parse all three backfill dialects exactly:

  * Bybit backfill (flat):   {"side":"Buy","price":"100.5","size":"0.10"}
  * Binance REST backfill:   {"id":..,"price":"..","qty":"..","quote_qty":..,
                              "time":..,"is_buyer_maker":"true"/"false"}
                             -- NO side/S, NO size/v/q; aggressor side ONLY
                             via is_buyer_maker (true -> SELL aggressor -> -1).
  * Deribit backfill:        {"trade_seq":..,"price":74192.0,"amount":10.0,
                              "direction":"buy"/"sell",...} -- price/amount
                             are NATIVE JSON NUMBERS (not strings); side is
                             called direction, size is called amount (which
                             on Deribit perps is USD notional, documented in
                             the loader).

Plus the LOUD-FAIL guard: files present, raw rows in the window, but an
unknown payload dialect (nothing parses) must raise DataError naming a file
and a sample payload -- never silently return 0 trades / all-NaN series
(the bug class that hid the 2026-07-17 envelope finding for 5 days).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c14_panellag.panel import (
    DataError as C14DataError,
    load_seconds_last_price,
)
from bybit_edge.research.c17_venue.features import (
    DataError as C17DataError,
    load_node_trades,
)

DAY = "2031-01-01"
DAY_MS = int(datetime(2031, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def _write_partition(base: Path, exchange: str, symbol: str, date_str: str,
                     rows: list[tuple[int, str]]) -> None:
    """One harvester Hive partition with literal (ts_ms, payload_json) rows."""
    import duckdb

    d = base / "raw" / exchange / "publicTrade" / f"symbol={symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)",
                        [(int(ts), payload) for ts, payload in rows])
        con.execute(f"COPY t TO '{(d / 'data.parquet').as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def _bybit_payload(price: float, size: float, side: str) -> str:
    return json.dumps({"symbol": "BTCUSDT", "side": side,
                       "price": f"{price}", "size": f"{size}"})


def _binance_backfill_payload(price: float, qty: float, is_buyer_maker: bool,
                              *, native_bool: bool = False) -> str:
    """Binance REST backfill row: all-strings by default (harvester form)."""
    flag: object = is_buyer_maker if native_bool else ("true" if is_buyer_maker else "false")
    return json.dumps({
        "id": "998877", "price": f"{price}", "qty": f"{qty}",
        "quote_qty": f"{price * qty:.8f}", "time": "1234567890123",
        "is_buyer_maker": flag,
    })


def _deribit_backfill_payload(price: float, amount: float, direction: str,
                              ts_ms: int, instrument: str = "BTC-PERPETUAL") -> str:
    """Deribit backfill row: price/amount are native JSON numbers."""
    return json.dumps({
        "trade_seq": 42, "trade_id": "BTC-1", "timestamp": ts_ms,
        "tick_direction": 1, "price": float(price), "mark_price": float(price),
        "instrument_name": instrument, "direction": direction,
        "amount": float(amount),
    })


# ---------------------------------------------------------------------------
# (a) c14 1s last-price series -- exact values for all three dialects
# ---------------------------------------------------------------------------

def test_c14_price_series_bybit_flat(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 100, _bybit_payload(100.5, 0.1, "Buy")),
        (DAY_MS + 900, _bybit_payload(101.25, 0.2, "Sell")),  # last in second 0
        (DAY_MS + 5_000, _bybit_payload(99.75, 0.3, "Buy")),
    ])
    out = load_seconds_last_price(base, "bybit", "BTCUSDT", [DAY])
    assert out.shape == (86_400,)
    assert out[0] == 101.25  # LAST trade of [0s, 1s)
    assert out[5] == 99.75
    assert np.isnan(out[1]) and np.isnan(out[6])


def test_c14_price_series_binance_backfill(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "binance", "ETHUSDT", DAY, [
        (DAY_MS + 100, _binance_backfill_payload(2321.16, 0.014, True)),
        (DAY_MS + 700, _binance_backfill_payload(2321.50, 0.020, False)),
        (DAY_MS + 3_100, _binance_backfill_payload(2320.99, 0.500, True)),
    ])
    out = load_seconds_last_price(base, "binance", "ETHUSDT", [DAY])
    assert out[0] == 2321.50
    assert out[3] == 2320.99
    assert np.isnan(out[1]) and np.isnan(out[4])


def test_c14_price_series_deribit_backfill(tmp_path: Path) -> None:
    # price is a NATIVE JSON number -- json_extract_string must still yield
    # a castable decimal string ('74192.0'), verified here, not assumed.
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "BTC-PERPETUAL", DAY, [
        (DAY_MS + 200, _deribit_backfill_payload(74192.0, 10.0, "buy", DAY_MS + 200)),
        (DAY_MS + 800, _deribit_backfill_payload(74192.5, 20.0, "sell", DAY_MS + 800)),
        (DAY_MS + 7_400, _deribit_backfill_payload(74180.25, 30.0, "buy", DAY_MS + 7_400)),
    ])
    out = load_seconds_last_price(base, "deribit", "BTC-PERPETUAL", [DAY])
    assert out[0] == 74192.5
    assert out[7] == 74180.25
    assert np.isnan(out[1]) and np.isnan(out[8])


# ---------------------------------------------------------------------------
# (b) c17 load_node_trades -- price/size/sign per dialect
# ---------------------------------------------------------------------------

def test_c17_load_node_trades_bybit_flat(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.5, 0.10, "Buy")),
        (DAY_MS + 2_000, _bybit_payload(100.6, 0.25, "Sell")),
        (DAY_MS + 3_000, _bybit_payload(100.4, 1.50, "Buy")),
    ])
    ts, price, size, sign = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY)
    assert ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000, DAY_MS + 3_000]
    assert price.tolist() == [100.5, 100.6, 100.4]
    assert size.tolist() == [0.10, 0.25, 1.50]
    assert sign.tolist() == [1.0, -1.0, 1.0]


def test_c17_load_node_trades_binance_backfill(tmp_path: Path) -> None:
    # is_buyer_maker semantics: 'true' = buyer is MAKER = SELL aggressor
    # -> sign -1 (NOT +1!); 'false' -> BUY aggressor -> +1. Size from 'qty'.
    base = tmp_path / "harvest"
    _write_partition(base, "binance", "ETHUSDT", DAY, [
        (DAY_MS + 1_000, _binance_backfill_payload(2321.16, 0.014, True)),
        (DAY_MS + 2_000, _binance_backfill_payload(2321.50, 0.020, False)),
        (DAY_MS + 3_000, _binance_backfill_payload(2322.00, 0.100, True)),
        # native JSON booleans (not the string form) must resolve identically
        (DAY_MS + 4_000, _binance_backfill_payload(2322.25, 0.200, False, native_bool=True)),
        (DAY_MS + 5_000, _binance_backfill_payload(2322.50, 0.300, True, native_bool=True)),
    ])
    ts, price, size, sign = load_node_trades(base, "binance", "ETHUSDT", DAY, DAY)
    assert ts.size == 5
    assert price.tolist() == [2321.16, 2321.50, 2322.00, 2322.25, 2322.50]
    assert size.tolist() == [0.014, 0.020, 0.100, 0.200, 0.300]
    assert sign.tolist() == [-1.0, 1.0, -1.0, 1.0, -1.0]


def test_c17_load_node_trades_deribit_backfill(tmp_path: Path) -> None:
    # direction 'buy'/'sell' -> +1/-1; size from native-number 'amount'
    # (USD notional on Deribit perps -- unit is irrelevant here, the loader
    # must simply carry the value through exactly).
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "BTC-PERPETUAL", DAY, [
        (DAY_MS + 1_000, _deribit_backfill_payload(74192.0, 10.0, "buy", DAY_MS + 1_000)),
        (DAY_MS + 2_000, _deribit_backfill_payload(74191.5, 250.0, "sell", DAY_MS + 2_000)),
        (DAY_MS + 3_000, _deribit_backfill_payload(74195.25, 30.5, "buy", DAY_MS + 3_000)),
    ])
    ts, price, size, sign = load_node_trades(base, "deribit", "BTC-PERPETUAL", DAY, DAY)
    assert ts.size == 3
    assert price.tolist() == [74192.0, 74191.5, 74195.25]
    assert size.tolist() == [10.0, 250.0, 30.5]
    assert sign.tolist() == [1.0, -1.0, 1.0]


# ---------------------------------------------------------------------------
# (c) loud-fail guard: unknown payload dialect must raise, not silently 0/NaN
# ---------------------------------------------------------------------------

def _write_unknown_dialect(base: Path, exchange: str, symbol: str) -> None:
    _write_partition(base, exchange, symbol, DAY, [
        (DAY_MS + 1_000, json.dumps({"foo": 1})),
        (DAY_MS + 2_000, json.dumps({"foo": 2})),
        (DAY_MS + 3_000, json.dumps({"foo": 3})),
    ])


def test_c14_loud_fail_on_unknown_payload_format(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_unknown_dialect(base, "binance", "BTCUSDT")
    with pytest.raises(C14DataError) as ei:
        load_seconds_last_price(base, "binance", "BTCUSDT", [DAY])
    msg = str(ei.value)
    assert "unknown payload_json format" in msg
    assert "data.parquet" in msg  # names a concrete file
    assert '"foo"' in msg  # sample payload (first 200 chars)


def test_c17_loud_fail_on_unknown_payload_format(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_unknown_dialect(base, "binance", "BTCUSDT")
    with pytest.raises(C17DataError) as ei:
        load_node_trades(base, "binance", "BTCUSDT", DAY, DAY)
    msg = str(ei.value)
    assert "unknown payload_json format" in msg
    assert "data.parquet" in msg
    assert '"foo"' in msg
    assert "3 raw rows" in msg  # raw-row count from the SAME scan


def test_c17_partial_parse_still_loads_and_drops_loudly(tmp_path: Path) -> None:
    # Guard must NOT fire when at least some rows parse: known rows load,
    # unknown rows are dropped (counted) -- pre-existing behaviour.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.5, 0.10, "Buy")),
        (DAY_MS + 2_000, json.dumps({"foo": 1})),
        (DAY_MS + 3_000, _bybit_payload(100.6, 0.20, "Sell")),
    ])
    ts, price, size, sign = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY)
    assert ts.size == 2
    assert sign.tolist() == [1.0, -1.0]


def test_c14_missing_files_error_unchanged(tmp_path: Path) -> None:
    # No parquet at all stays the pre-existing "no parquet" DataError -- the
    # loud-fail guard is specifically about EXISTING rows that do not parse.
    with pytest.raises(C14DataError, match="no parquet"):
        load_seconds_last_price(tmp_path / "empty", "bybit", "BTCUSDT", [DAY])
