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

The second half of this file (from "ENVELOPE (live) payload form") pins the
OTHER structural shape -- the multi-trade live envelope -- for all five
trade loaders (c12/c14 price bars, c15/c16/c17 event and flow series):
per-trade timestamps, side/size out of the nested element, the Deribit
JSON-RPC variant, the cross-form de-duplication, and the bit-identity of
the flat pass-through.
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


# ===========================================================================
# ENVELOPE (live) payload form -- ``$.data[*]`` / ``$.params.data[*]``
#
# The harvester stores TWO shapes for publicTrade (DATASET.md §6): the flat
# backfill row (one trade per parquet row, tested above) and the LIVE
# ENVELOPE, which nests MANY trades in ONE row. All loaders below used to
# read top-level keys only, so envelope rows produced NULL and vanished --
# bybit from 2026-07-17, deribit from ~2026-06-16 delivered 0 trades, which
# flipped 19/50 W2 days of the H-12 run to panel_valid=False.
#
# The decisive property pinned here is the PER-TRADE timestamp: an envelope
# carries one packet ``ts`` plus a per-trade ``T`` (bybit) / ``timestamp``
# (deribit). Every envelope fixture below deliberately spreads its trades
# over SEVERAL bars while the packet ``ts`` sits in the FIRST bar, so a
# loader that (wrongly) used the packet timestamp would collapse them into
# one bar and fail the assertions.
# ===========================================================================

from bybit_edge.research.c12_frag.panel import (  # noqa: E402
    DataError as C12DataError,
    load_minute_last_price,
)
from bybit_edge.research.c15_grammar.driver import load_trade_events  # noqa: E402
from bybit_edge.research.c16_arrow.driver import load_day_imbalance  # noqa: E402

MINUTE_MS = 60_000


def _bybit_envelope(trades: list[tuple[int, str, float, float, str]], *,
                    envelope_ts: int, symbol: str = "BTCUSDT") -> str:
    """Bybit V5 live ``publicTrade`` envelope (verified shape).

    ``trades`` = [(trade_ts_ms, side, size, price, trade_id), ...].
    """
    return json.dumps({
        "topic": f"publicTrade.{symbol}", "type": "snapshot", "ts": envelope_ts,
        "data": [
            {"T": int(t_ms), "s": symbol, "S": side, "v": f"{size}", "p": f"{price}",
             "L": "PlusTick", "i": tid, "BT": False}
            for t_ms, side, size, price, tid in trades
        ],
    })


def _deribit_envelope(trades: list[tuple[int, str, float, float, str]], *,
                      envelope_ts: int, jsonrpc: bool = False,
                      instrument: str = "BTC-PERPETUAL") -> str:
    """Deribit live envelope -- plain ``$.data[]`` or JSON-RPC ``$.params.data[]``.

    The PLAIN form is VERIFIED against a real stored file (harvester
    partition deribit/BTC-PERPETUAL/date=2026-06-30, sampled 2026-08-08):
    ``{"channel":"trades.BTC-PERPETUAL.100ms","data":[{"timestamp":...,
    "price":...,"amount":...,"direction":"buy","trade_id":"..."}, ...]}``
    -- see ``test_c12_real_deribit_live_payload_verbatim`` which pins that
    exact byte shape. The JSON-RPC variant has NOT been observed in stored
    data; it is kept as a defensive path (Deribit documents it for
    subscription notifications) and pinned here so it cannot rot.
    ``trades`` = [(trade_ts_ms, direction, amount, price, trade_id), ...].
    """
    data = [
        {"trade_seq": i, "trade_id": tid, "timestamp": int(t_ms), "tick_direction": 1,
         "price": float(price), "mark_price": float(price),
         "instrument_name": instrument, "direction": direction, "amount": float(amount)}
        for i, (t_ms, direction, amount, price, tid) in enumerate(trades)
    ]
    channel = f"trades.{instrument}.raw"
    if jsonrpc:
        return json.dumps({"jsonrpc": "2.0", "method": "subscription",
                           "params": {"channel": channel, "data": data}})
    return json.dumps({"channel": channel, "ts": envelope_ts, "data": data})


def _bybit_flat_with_id(price: float, size: float, side: str, trade_id: str) -> str:
    """Flat bybit backfill row INCLUDING its exchange trade id."""
    return json.dumps({"timestamp": "1750000000.0", "symbol": "BTCUSDT", "side": side,
                       "size": f"{size}", "price": f"{price}", "tickDirection": "PlusTick",
                       "trdMatchID": trade_id})


# ---------------------------------------------------------------------------
# (a) c12_frag load_minute_last_price -- flat / envelope / mixed
# ---------------------------------------------------------------------------

def test_c12_minute_last_price_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.0, 0.1, "Buy")),
        (DAY_MS + 59_000, _bybit_payload(101.0, 0.2, "Sell")),   # last in minute 0
        (DAY_MS + 5 * MINUTE_MS + 10, _bybit_payload(99.0, 0.3, "Buy")),
    ])
    out = load_minute_last_price(base, "bybit", "BTCUSDT", [DAY])
    assert out.shape == (1440,)
    assert out[0] == 101.0
    assert out[5] == 99.0
    assert np.isnan(out[1]) and np.isnan(out[4])
    assert int(np.sum(np.isfinite(out))) == 2


def test_c12_minute_last_price_envelope_only_spreads_over_minutes(tmp_path: Path) -> None:
    # ONE parquet row, three trades, packet ts in minute 0 -- the trades must
    # land in minutes 0 and 2 by their per-trade $.T, not all in minute 0.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 500, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 0.010, 100.0, "e1"),
            (DAY_MS + 59_000, "Sell", 0.020, 101.0, "e2"),          # last in minute 0
            (DAY_MS + 2 * MINUTE_MS + 5_000, "Buy", 0.030, 102.0, "e3"),
        ], envelope_ts=DAY_MS + 500)),
    ])
    out = load_minute_last_price(base, "bybit", "BTCUSDT", [DAY])
    assert out[0] == 101.0
    assert out[2] == 102.0
    assert np.isnan(out[1])
    assert int(np.sum(np.isfinite(out))) == 2


def test_c12_minute_last_price_mixed_forms(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.0, 0.1, "Buy")),        # flat, minute 0
        (DAY_MS + 500, _bybit_envelope([
            (DAY_MS + 30_000, "Sell", 0.02, 101.0, "e1"),           # envelope, minute 0
            (DAY_MS + 3 * MINUTE_MS, "Buy", 0.03, 103.0, "e2"),     # envelope, minute 3
        ], envelope_ts=DAY_MS + 500)),
        (DAY_MS + 7 * MINUTE_MS, _bybit_payload(107.0, 0.4, "Buy")),  # flat, minute 7
    ])
    out = load_minute_last_price(base, "bybit", "BTCUSDT", [DAY])
    assert out[0] == 101.0   # envelope trade at +30s is the LAST of minute 0
    assert out[3] == 103.0
    assert out[7] == 107.0
    assert int(np.sum(np.isfinite(out))) == 3


def test_c12_minute_last_price_deribit_envelope_plain(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "BTC-PERPETUAL", DAY, [
        (DAY_MS + 100, _deribit_envelope([
            (DAY_MS + 1_000, "buy", 10.0, 74192.0, "d1"),
            (DAY_MS + 4 * MINUTE_MS, "sell", 20.0, 74180.5, "d2"),
        ], envelope_ts=DAY_MS + 100)),
    ])
    out = load_minute_last_price(base, "deribit", "BTC-PERPETUAL", [DAY])
    assert out[0] == 74192.0
    assert out[4] == 74180.5
    assert int(np.sum(np.isfinite(out))) == 2


def test_c12_minute_last_price_deribit_envelope_jsonrpc(tmp_path: Path) -> None:
    # (e) JSON-RPC subscription-notification variant: $.params.data[*]
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "ETH-PERPETUAL", DAY, [
        (DAY_MS + 100, _deribit_envelope([
            (DAY_MS + 2_000, "buy", 10.0, 2321.0, "d1"),
            (DAY_MS + 6 * MINUTE_MS, "sell", 20.0, 2319.75, "d2"),
        ], envelope_ts=DAY_MS + 100, jsonrpc=True, instrument="ETH-PERPETUAL")),
    ])
    out = load_minute_last_price(base, "deribit", "ETH-PERPETUAL", [DAY])
    assert out[0] == 2321.0
    assert out[6] == 2319.75
    assert int(np.sum(np.isfinite(out))) == 2


def test_c12_loud_fail_on_unknown_payload_format(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_unknown_dialect(base, "bybit", "BTCUSDT")
    with pytest.raises(C12DataError, match="0 usable minute bars"):
        load_minute_last_price(base, "bybit", "BTCUSDT", [DAY])


# ---------------------------------------------------------------------------
# (a') c14 1s series: envelope + JSON-RPC variant (same technique)
# ---------------------------------------------------------------------------

def test_c14_price_series_envelope_spreads_over_seconds(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 10, _bybit_envelope([
            (DAY_MS + 100, "Buy", 0.01, 100.0, "e1"),
            (DAY_MS + 900, "Sell", 0.02, 101.25, "e2"),   # last of second 0
            (DAY_MS + 5_000, "Buy", 0.03, 99.75, "e3"),
        ], envelope_ts=DAY_MS + 10)),
    ])
    out = load_seconds_last_price(base, "bybit", "BTCUSDT", [DAY])
    assert out[0] == 101.25
    assert out[5] == 99.75
    assert np.isnan(out[1]) and np.isnan(out[6])


def test_c14_price_series_deribit_jsonrpc_envelope(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "BTC-PERPETUAL", DAY, [
        (DAY_MS + 10, _deribit_envelope([
            (DAY_MS + 200, "buy", 10.0, 74192.0, "d1"),
            (DAY_MS + 9_400, "sell", 20.0, 74180.25, "d2"),
        ], envelope_ts=DAY_MS + 10, jsonrpc=True)),
    ])
    out = load_seconds_last_price(base, "deribit", "BTC-PERPETUAL", [DAY])
    assert out[0] == 74192.0
    assert out[9] == 74180.25


# ---------------------------------------------------------------------------
# (b) c16 load_day_imbalance -- signed size out of the envelope + dedup
# ---------------------------------------------------------------------------

def test_c16_day_imbalance_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.0, 1.00, "Buy")),
        (DAY_MS + 1_500, _bybit_payload(100.1, 0.25, "Sell")),
        (DAY_MS + 60_000, _bybit_payload(100.2, 2.00, "Buy")),
    ])
    series, n_active, n_trades = load_day_imbalance(base, "BTCUSDT", DAY)
    assert series.shape == (86_400,)
    assert series[1] == pytest.approx(0.75)
    assert series[60] == pytest.approx(2.00)
    assert (n_active, n_trades) == (2, 3)


def test_c16_day_imbalance_envelope_only_sides_and_seconds(tmp_path: Path) -> None:
    # S='Sell' must enter NEGATIVE; the two trades must land in the seconds
    # of their per-trade $.T (1 and 61), not both in the packet's second.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 1_000, "Sell", 0.010, 100.0, "e1"),
            (DAY_MS + 1_200, "Buy", 0.030, 100.1, "e2"),
            (DAY_MS + 61_000, "Buy", 0.020, 100.2, "e3"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    series, n_active, n_trades = load_day_imbalance(base, "BTCUSDT", DAY)
    assert series[1] == pytest.approx(0.020)   # 0.030 buy - 0.010 sell
    assert series[61] == pytest.approx(0.020)
    assert series[0] == 0.0                     # packet second stays empty
    assert (n_active, n_trades) == (2, 3)


def test_c16_day_imbalance_cross_form_dedup(tmp_path: Path) -> None:
    # Mixed backfill+live day (DATASET.md §9 caveat 4): trade 'X1' is stored
    # BOTH flat and inside the envelope. Summing signed size double-counts
    # it unless the cross-form dedup drops the envelope copy.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 1.0, "Buy", "X1")),
        (DAY_MS + 900, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 1.0, 100.0, "X1"),    # SAME trade
            (DAY_MS + 1_100, "Sell", 0.5, 100.1, "X2"),   # live-only trade
        ], envelope_ts=DAY_MS + 900)),
    ])
    series, n_active, n_trades = load_day_imbalance(base, "BTCUSDT", DAY)
    assert series[1] == pytest.approx(0.5)      # 1.0 buy - 0.5 sell, ONCE
    assert (n_active, n_trades) == (1, 2)
    raw, _, raw_trades = load_day_imbalance(base, "BTCUSDT", DAY,
                                            dedup_cross_form=False)
    assert raw[1] == pytest.approx(1.5)          # duplicate counted twice
    assert raw_trades == 3


def test_c16_day_imbalance_dedup_is_noop_on_flat_only(tmp_path: Path) -> None:
    # Bit-identity: on a backfill-only partition the dedup clause cannot
    # remove anything (there are no envelope rows to drop).
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 1.0, "Buy", "A1")),
        (DAY_MS + 1_500, _bybit_flat_with_id(100.1, 0.25, "Sell", "A2")),
        (DAY_MS + 2_000, _bybit_flat_with_id(100.2, 2.0, "Buy", "A3")),
    ])
    on = load_day_imbalance(base, "BTCUSDT", DAY)
    off = load_day_imbalance(base, "BTCUSDT", DAY, dedup_cross_form=False)
    assert np.array_equal(on[0], off[0])
    assert on[1:] == off[1:] == (2, 3)


# ---------------------------------------------------------------------------
# (b') c17 load_node_trades -- ts/price/size/sign out of the envelope + dedup
# ---------------------------------------------------------------------------

def test_c17_load_node_trades_bybit_envelope(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 0.10, 100.5, "e1"),
            (DAY_MS + 2_000, "Sell", 0.25, 100.6, "e2"),
            (DAY_MS + 3_000, "Buy", 1.50, 100.4, "e3"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    ts, price, size, sign = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY)
    assert ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000, DAY_MS + 3_000]
    assert price.tolist() == [100.5, 100.6, 100.4]
    assert size.tolist() == [0.10, 0.25, 1.50]
    assert sign.tolist() == [1.0, -1.0, 1.0]


def test_c17_load_node_trades_deribit_jsonrpc_envelope(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "BTC-PERPETUAL", DAY, [
        (DAY_MS + 10, _deribit_envelope([
            (DAY_MS + 1_000, "buy", 10.0, 74192.0, "d1"),
            (DAY_MS + 2_000, "sell", 250.0, 74191.5, "d2"),
        ], envelope_ts=DAY_MS + 10, jsonrpc=True)),
    ])
    ts, price, size, sign = load_node_trades(base, "deribit", "BTC-PERPETUAL", DAY, DAY)
    assert ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000]
    assert price.tolist() == [74192.0, 74191.5]
    assert size.tolist() == [10.0, 250.0]
    assert sign.tolist() == [1.0, -1.0]


def test_c17_load_node_trades_mixed_forms_dedup(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 1.0, "Buy", "X1")),
        (DAY_MS + 900, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 1.0, 100.0, "X1"),     # SAME trade
            (DAY_MS + 2_000, "Sell", 0.5, 100.1, "X2"),
        ], envelope_ts=DAY_MS + 900)),
    ])
    ts, price, size, sign = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY)
    assert ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000]
    assert sign.tolist() == [1.0, -1.0]
    assert size.tolist() == [1.0, 0.5]
    ts_raw, _, _, _ = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY,
                                       dedup_cross_form=False)
    assert ts_raw.size == 3   # duplicate present without the dedup


def test_c17_load_node_trades_dedup_is_noop_on_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.5, 0.10, "Buy", "A1")),
        (DAY_MS + 2_000, _bybit_flat_with_id(100.6, 0.25, "Sell", "A2")),
        (DAY_MS + 3_000, _bybit_flat_with_id(100.4, 1.50, "Buy", "A3")),
    ])
    on = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY)
    off = load_node_trades(base, "bybit", "BTCUSDT", DAY, DAY, dedup_cross_form=False)
    for a, b in zip(on, off):
        assert np.array_equal(a, b)
    assert on[0].tolist() == [DAY_MS + 1_000, DAY_MS + 2_000, DAY_MS + 3_000]


# ---------------------------------------------------------------------------
# (b'') c15 load_trade_events -- event stream out of the envelope + dedup
# ---------------------------------------------------------------------------

def test_c15_trade_events_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.5, 0.10, "Buy", "A1")),
        (DAY_MS + 2_000, _bybit_flat_with_id(100.6, 0.25, "Sell", "A2")),
    ])
    ev = load_trade_events(base, "BTCUSDT", [DAY])
    assert ev.ts_ms.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000]
    assert ev.price.tolist() == [100.5, 100.6]
    assert ev.size.tolist() == [0.10, 0.25]
    assert ev.side.tolist() == [1, 0]   # 1 = Buy, 0 = Sell


def test_c15_trade_events_envelope_uses_per_trade_timestamps(tmp_path: Path) -> None:
    # If the packet ts were used, every inter-arrival time would be 0 ms and
    # the whole IAT token axis would be corrupt -- pinned by distinct ts.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 0.10, 100.5, "e1"),
            (DAY_MS + 2_500, "Sell", 0.25, 100.6, "e2"),
            (DAY_MS + 9_000, "Buy", 1.50, 100.4, "e3"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    ev = load_trade_events(base, "BTCUSDT", [DAY])
    assert ev.ts_ms.tolist() == [DAY_MS + 1_000, DAY_MS + 2_500, DAY_MS + 9_000]
    assert ev.price.tolist() == [100.5, 100.6, 100.4]
    assert ev.size.tolist() == [0.10, 0.25, 1.50]
    assert ev.side.tolist() == [1, 0, 1]


def test_c15_trade_events_cross_form_dedup(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 1.0, "Buy", "X1")),
        (DAY_MS + 900, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 1.0, 100.0, "X1"),     # SAME trade
            (DAY_MS + 2_000, "Sell", 0.5, 100.1, "X2"),
        ], envelope_ts=DAY_MS + 900)),
    ])
    ev = load_trade_events(base, "BTCUSDT", [DAY])
    assert ev.ts_ms.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000]
    raw = load_trade_events(base, "BTCUSDT", [DAY], dedup_cross_form=False)
    assert raw.ts_ms.size == 3


def test_c15_trade_events_dedup_is_noop_on_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.5, 0.10, "Buy", "A1")),
        (DAY_MS + 2_000, _bybit_flat_with_id(100.6, 0.25, "Sell", "A2")),
        (DAY_MS + 3_000, _bybit_flat_with_id(100.4, 1.50, "Buy", "A3")),
    ])
    on = load_trade_events(base, "BTCUSDT", [DAY])
    off = load_trade_events(base, "BTCUSDT", [DAY], dedup_cross_form=False)
    assert np.array_equal(on.ts_ms, off.ts_ms)
    assert np.array_equal(on.price, off.price)
    assert np.array_equal(on.size, off.size)
    assert np.array_equal(on.side, off.side)


# ---------------------------------------------------------------------------
# (c) flat-form regression: envelope support must not touch the flat path
# ---------------------------------------------------------------------------

def test_flat_rows_are_passed_through_unchanged(tmp_path: Path) -> None:
    """The flat branch must hand the parquet row on byte-for-byte.

    Pins the bit-identity guarantee the registered verdicts rest on: same
    ``ts_exchange_ms``, same ``payload_json`` string, exactly one row out per
    row in -- for every flat dialect, including one that carries a ``data``
    key that is NOT a trade container (scalar -> stays flat).
    """
    import duckdb

    from bybit_edge.research.payload_sql import trade_rows_sql

    rows = [
        (DAY_MS + 1, _bybit_payload(100.5, 0.1, "Buy")),
        (DAY_MS + 2, _binance_backfill_payload(2321.16, 0.014, True)),
        (DAY_MS + 3, _deribit_backfill_payload(74192.0, 10.0, "buy", DAY_MS + 3)),
        (DAY_MS + 4, json.dumps({"foo": 1})),
        (DAY_MS + 5, json.dumps({"price": "1.0", "data": 7})),   # scalar $.data
        (DAY_MS + 6, None),
    ]
    _write_partition(tmp_path / "h", "bybit", "BTCUSDT", DAY, rows)
    f = (tmp_path / "h" / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT"
         / f"date={DAY}" / "data.parquet").as_posix()
    src = trade_rows_sql(f"read_parquet('{f}', union_by_name=1)")
    con = duckdb.connect()
    try:
        got = con.execute(
            f"SELECT ts_exchange_ms, payload_json, is_envelope FROM {src} "
            f"ORDER BY ts_exchange_ms"
        ).fetchall()
    finally:
        con.close()
    assert [(t, p) for t, p, _ in got] == rows
    assert all(not env for _, _, env in got)


def test_envelope_expansion_never_touches_flat_rows_in_mixed_file(tmp_path: Path) -> None:
    import duckdb

    from bybit_edge.research.payload_sql import trade_rows_sql

    flat = _bybit_payload(100.5, 0.1, "Buy")
    _write_partition(tmp_path / "h", "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1, flat),
        (DAY_MS + 2, _bybit_envelope([(DAY_MS + 7, "Sell", 0.2, 101.0, "e1")],
                                     envelope_ts=DAY_MS + 2)),
    ])
    f = (tmp_path / "h" / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT"
         / f"date={DAY}" / "data.parquet").as_posix()
    src = trade_rows_sql(f"read_parquet('{f}', union_by_name=1)")
    con = duckdb.connect()
    try:
        got = con.execute(
            f"SELECT ts_exchange_ms, payload_json, is_envelope FROM {src} "
            f"ORDER BY ts_exchange_ms"
        ).fetchall()
    finally:
        con.close()
    assert got[0] == (DAY_MS + 1, flat, False)
    assert got[1][0] == DAY_MS + 7 and got[1][2] is True
    assert json.loads(got[1][1])["p"] == "101.0"


def test_empty_envelope_array_yields_no_trades(tmp_path: Path) -> None:
    import duckdb

    from bybit_edge.research.payload_sql import trade_rows_sql

    _write_partition(tmp_path / "h", "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1, json.dumps({"topic": "publicTrade.BTCUSDT", "ts": DAY_MS + 1,
                                 "data": []})),
    ])
    f = (tmp_path / "h" / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT"
         / f"date={DAY}" / "data.parquet").as_posix()
    src = trade_rows_sql(f"read_parquet('{f}', union_by_name=1)")
    con = duckdb.connect()
    try:
        assert con.execute(f"SELECT count(*) FROM {src}").fetchone()[0] == 0
    finally:
        con.close()


def test_c12_real_deribit_live_payload_verbatim(tmp_path: Path) -> None:
    """The EXACT stored Deribit live payload (harvester file, sampled
    2026-08-08 from deribit/BTC-PERPETUAL/date=2026-06-30) must parse.

    This is the shape that silently produced ZERO trades before the
    envelope support and flipped 19/50 W2 days of the H-12 run to
    panel_valid=False. Pinned verbatim (only the two trade timestamps are
    moved into the test day, so the minute assignment is checkable) so a
    future refactor cannot re-break the real-world format.
    """
    day = "2026-06-30"
    midnight = int(datetime(2026, 6, 30, tzinfo=timezone.utc).timestamp() * 1000)
    t_a, t_b = midnight + 30_000, midnight + 90_000  # minute 0 and minute 1
    payload = (
        '{"channel":"trades.BTC-PERPETUAL.100ms","data":['
        '{"timestamp":' + str(t_a) + ',"price":60156.5,"amount":745630.0,'
        '"direction":"buy","index_price":60141.59,'
        '"instrument_name":"BTC-PERPETUAL","trade_seq":293343065,'
        '"mark_price":60152.38,"tick_direction":0,"contracts":74563.0,'
        '"trade_id":"436180169"},'
        '{"timestamp":' + str(t_b) + ',"price":60164.5,"amount":21910.0,'
        '"direction":"buy","index_price":60141.59,'
        '"instrument_name":"BTC-PERPETUAL","trade_seq":293343099,'
        '"mark_price":60152.38,"tick_direction":1,"contracts":2770.0,'
        '"trade_id":"436180241"}]}'
    )
    _write_partition(tmp_path, "deribit", "BTC-PERPETUAL", day, [(t_a, payload)])

    series = load_minute_last_price(tmp_path, "deribit", "BTC-PERPETUAL", [day])

    assert np.isfinite(series).sum() == 2, "both nested trades must be read"
    # per-trade timestamps -> two DIFFERENT minutes (the envelope packet
    # timestamp would have collapsed both into minute 0)
    assert series[0] == pytest.approx(60156.5)
    assert series[1] == pytest.approx(60164.5)


# ===========================================================================
# ENVELOPE form for the REMAINING five trade loaders
# (c01 OOS ticks, c09 order notionals, c10 daily RV, c11 daily RV,
#  c13 trailing 1-min returns)
#
# Same structure as the sections above, per loader:
#   (a) flat-only == the pre-envelope behaviour (legacy SQL / closed-form
#       expectation) -- the bit-identity the registered verdicts rest on
#       (GL-007/010/011 for c01, GL-016/017 for c09+c10),
#   (b) an envelope-only partition is read at all,
#   (c) a MIXED partition (flat + envelope rows in one file) is correct,
#   (d) the de-duplication DECISION is pinned: c01/c09 sum sizes/notionals
#       and therefore de-duplicate; c10/c11/c13 aggregate to price bars,
#       where a cross-form duplicate is inert and must stay a no-op.
# ===========================================================================

import math  # noqa: E402

from bybit_edge.research.c01_ofi_sign.oos import (  # noqa: E402
    DataError as C01DataError,
    load_harvest_window,
)
from bybit_edge.research.c09_bunch.driver import load_window_orders  # noqa: E402
from bybit_edge.research.c10_pointer.loaders import (  # noqa: E402
    DataError as C10DataError,
    load_daily_rv as load_daily_rv_c10,
)
from bybit_edge.research.c11_anen.features import (  # noqa: E402
    load_daily_rv as load_daily_rv_c11,
)

DAY2 = "2031-01-02"
DAY2_MS = DAY_MS + 86_400_000


def _parquet_path(base: Path, exchange: str, symbol: str, day: str) -> str:
    return (base / "raw" / exchange / "publicTrade" / f"symbol={symbol}"
            / f"date={day}" / "data.parquet").as_posix()


# ---------------------------------------------------------------------------
# (d) c01 load_harvest_window -- OOS tick window (GL-007/GL-010/GL-011)
# ---------------------------------------------------------------------------

def _c01_legacy_rows(base: Path, symbol: str, day: str,
                     max_ticks: int = 300_000) -> list[tuple]:
    """The PRE-ENVELOPE c01 SQL verbatim, straight on the parquet scan.

    Reference for the bit-identity regression: on a flat-only partition the
    new ``trade_rows_sql`` read path must return exactly these rows.
    """
    import duckdb

    f = _parquet_path(base, "bybit", symbol, day)
    start_ms = int(datetime.strptime(day, "%Y-%m-%d")
                   .replace(tzinfo=timezone.utc).timestamp() * 1000)
    sql = f"""
        SELECT ts_exchange_ms AS ts,
               CASE
                 WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                     json_extract_string(payload_json,'$.S'))) = 'buy'  THEN 'Buy'
                 WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                     json_extract_string(payload_json,'$.S'))) = 'sell' THEN 'Sell'
                 ELSE COALESCE(json_extract_string(payload_json,'$.side'),
                               json_extract_string(payload_json,'$.S'))
               END AS side,
               CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                             json_extract_string(payload_json,'$.p')) AS DOUBLE) AS price,
               CAST(COALESCE(json_extract_string(payload_json,'$.size'),
                             json_extract_string(payload_json,'$.v')) AS DOUBLE) AS volume
        FROM read_parquet('{f}', hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL AND ts_exchange_ms >= {start_ms}
          AND (json_extract_string(payload_json,'$.side') IS NOT NULL
               OR json_extract_string(payload_json,'$.S') IS NOT NULL)
        ORDER BY ts_exchange_ms
        LIMIT {int(max_ticks)}
    """
    con = duckdb.connect()
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_c01_harvest_window_flat_matches_legacy_sql(tmp_path: Path) -> None:
    # BIT-IDENTITY regression: flat-only partition, new read path vs the
    # verbatim pre-envelope SQL (the H-05b verdicts GL-007/010/011 rest on
    # exactly these numbers).
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.5, 0.10, "Buy")),
        (DAY_MS + 2_000, _bybit_payload(100.6, 0.25, "Sell")),
        (DAY_MS + 3_000, _bybit_payload(100.4, 1.50, "Buy")),
        (DAY_MS + 4_000, json.dumps({"foo": 1})),          # no side -> filtered
    ])
    w = load_harvest_window(base, "BTCUSDT", DAY)
    legacy = _c01_legacy_rows(base, "BTCUSDT", DAY)
    assert w.ts.tolist() == [float(r[0]) for r in legacy]
    assert list(w.side) == [r[1] for r in legacy]
    assert w.price.tolist() == [r[2] for r in legacy]
    assert w.volume.tolist() == [r[3] for r in legacy]
    assert w.ts.size == 3


def test_c01_harvest_window_envelope_uses_per_trade_timestamps(tmp_path: Path) -> None:
    # ONE parquet row, three trades; packet ts far before them. Per-trade $.T
    # must reach the OFI grid -- the packet ts would give all three the same
    # millisecond.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 0.10, 100.5, "e1"),
            (DAY_MS + 2_000, "Sell", 0.25, 100.6, "e2"),
            (DAY_MS + 3_000, "Buy", 1.50, 100.4, "e3"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    w = load_harvest_window(base, "BTCUSDT", DAY)
    assert w.ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000, DAY_MS + 3_000]
    assert list(w.side) == ["Buy", "Sell", "Buy"]
    assert w.price.tolist() == [100.5, 100.6, 100.4]
    assert w.volume.tolist() == [0.10, 0.25, 1.50]


def test_c01_harvest_window_mixed_forms(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(100.5, 0.10, "Buy")),        # flat
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 2_000, "Sell", 0.25, 100.6, "e1"),
            (DAY_MS + 4_000, "Buy", 1.50, 100.4, "e2"),
        ], envelope_ts=DAY_MS + 50)),
        (DAY_MS + 3_000, _bybit_payload(100.7, 0.75, "Sell")),       # flat
    ])
    w = load_harvest_window(base, "BTCUSDT", DAY)
    assert w.ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000,
                             DAY_MS + 3_000, DAY_MS + 4_000]
    assert list(w.side) == ["Buy", "Sell", "Sell", "Buy"]
    assert w.volume.tolist() == [0.10, 0.25, 0.75, 1.50]


def test_c01_harvest_window_cross_form_dedup(tmp_path: Path) -> None:
    # The OFI estimator SUMS signed sizes, so the flat/envelope copy of the
    # SAME trade 'X1' must be collapsed (dedup ON by default).
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 1.0, "Buy", "X1")),
        (DAY_MS + 900, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 1.0, 100.0, "X1"),    # SAME trade
            (DAY_MS + 2_000, "Sell", 0.5, 100.1, "X2"),   # live-only trade
        ], envelope_ts=DAY_MS + 900)),
    ])
    w = load_harvest_window(base, "BTCUSDT", DAY)
    assert w.ts.tolist() == [DAY_MS + 1_000, DAY_MS + 2_000]
    assert w.volume.tolist() == [1.0, 0.5]
    raw = load_harvest_window(base, "BTCUSDT", DAY, dedup_cross_form=False)
    assert raw.ts.size == 3   # duplicate survives without the dedup


def test_c01_harvest_window_dedup_is_noop_on_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.5, 0.10, "Buy", "A1")),
        (DAY_MS + 2_000, _bybit_flat_with_id(100.6, 0.25, "Sell", "A2")),
        (DAY_MS + 3_000, _bybit_flat_with_id(100.4, 1.50, "Buy", "A3")),
    ])
    on = load_harvest_window(base, "BTCUSDT", DAY)
    off = load_harvest_window(base, "BTCUSDT", DAY, dedup_cross_form=False)
    assert np.array_equal(on.ts, off.ts)
    assert np.array_equal(on.price, off.price)
    assert np.array_equal(on.volume, off.volume)
    assert list(on.side) == list(off.side)


def test_c01_missing_files_error_unchanged(tmp_path: Path) -> None:
    with pytest.raises(C01DataError, match="no parquet"):
        load_harvest_window(tmp_path / "empty", "BTCUSDT", DAY)


# ---------------------------------------------------------------------------
# (e) c09 load_window_orders -- ORDER notionals (GL-016/GL-017)
# ---------------------------------------------------------------------------

#: kink for the fixtures below: retention band is
#: [(0.20-0.005)*kink, (1.30+0.005)*kink] = [195, 1305] USDT.
C09_KINK = 1_000.0


def _c09_order_payload(price: float, size: float, side: str) -> str:
    return _bybit_payload(price, size, side)


def _c09_legacy_orders(base: Path, symbol: str, day: str) -> list[tuple]:
    """The PRE-ENVELOPE c09 order aggregation verbatim (bit-identity ref)."""
    import duckdb

    f = _parquet_path(base, "bybit", symbol, day)
    start_ms = int(datetime.strptime(day, "%Y-%m-%d")
                   .replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = start_ms + 86_400_000
    sql = f"""
        SELECT ts_exchange_ms AS ts,
               SUM(price * size) AS notional,
               COUNT(*) AS n_fills
        FROM (
            SELECT ts_exchange_ms,
                   lower(COALESCE(json_extract_string(payload_json, '$.side'),
                                  json_extract_string(payload_json, '$.S'))) AS side,
                   TRY_CAST(COALESCE(json_extract_string(payload_json, '$.price'),
                                     json_extract_string(payload_json, '$.p')) AS DOUBLE) AS price,
                   TRY_CAST(COALESCE(json_extract_string(payload_json, '$.size'),
                                     json_extract_string(payload_json, '$.v')) AS DOUBLE) AS size
            FROM read_parquet('{f}', hive_partitioning=1, union_by_name=1)
            WHERE ts_exchange_ms IS NOT NULL
              AND ts_exchange_ms >= {start_ms} AND ts_exchange_ms < {end_ms}
              AND (json_extract_string(payload_json, '$.side') IS NOT NULL
                   OR json_extract_string(payload_json, '$.S') IS NOT NULL)
        )
        WHERE price IS NOT NULL AND size IS NOT NULL
        GROUP BY ts_exchange_ms, side
    """
    con = duckdb.connect()
    try:
        return sorted(con.execute(sql).fetchall())
    finally:
        con.close()


def test_c09_window_orders_flat_matches_legacy_sql(tmp_path: Path) -> None:
    # BIT-IDENTITY regression on a flat-only window (H-09 GL-016/GL-017).
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _c09_order_payload(100.0, 5.0, "Buy")),    # 500
        (DAY_MS + 1_000, _c09_order_payload(100.0, 3.0, "Buy")),    # same order
        (DAY_MS + 2_000, _c09_order_payload(100.0, 9.0, "Sell")),   # 900
    ])
    wo = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK)
    legacy = _c09_legacy_orders(base, "BTCUSDT", DAY)
    assert wo.n_records_raw == sum(int(r[2]) for r in legacy) == 3
    assert wo.n_orders_total == len(legacy) == 2
    assert sorted(wo.notionals.tolist()) == sorted(
        float(r[1]) for r in legacy if 195.0 <= float(r[1]) <= 1305.0
    ) == [800.0, 900.0]


def test_c09_window_orders_envelope_groups_by_per_trade_timestamp(tmp_path: Path) -> None:
    # Three envelope trades at three DIFFERENT $.T -> three orders. With the
    # packet ts they would collapse into ONE phantom order of 2400 USDT.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 5.0, 100.0, "e1"),
            (DAY_MS + 2_000, "Buy", 8.0, 100.0, "e2"),
            (DAY_MS + 3_000, "Sell", 11.0, 100.0, "e3"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    wo = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK)
    assert wo.n_records_raw == 3
    assert wo.n_orders_total == 3
    assert sorted(wo.notionals.tolist()) == [500.0, 800.0, 1100.0]


def test_c09_window_orders_mixed_forms(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _c09_order_payload(100.0, 5.0, "Buy")),
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 3.0, 100.0, "e1"),   # SAME (ts, side) order
            (DAY_MS + 2_000, "Sell", 9.0, 100.0, "e2"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    wo = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK)
    assert wo.n_records_raw == 3
    assert wo.n_orders_total == 2
    assert sorted(wo.notionals.tolist()) == [800.0, 900.0]


def test_c09_window_orders_cross_form_dedup(tmp_path: Path) -> None:
    # An order notional is a SUM over fills, so a trade stored in BOTH forms
    # would double that order's notional -- dedup ON by default.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 5.0, "Buy", "X1")),
        (DAY_MS + 900, _bybit_envelope([
            (DAY_MS + 1_000, "Buy", 5.0, 100.0, "X1"),    # SAME trade
            (DAY_MS + 2_000, "Sell", 9.0, 100.0, "X2"),
        ], envelope_ts=DAY_MS + 900)),
    ])
    wo = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK)
    assert wo.n_records_raw == 2
    assert sorted(wo.notionals.tolist()) == [500.0, 900.0]
    raw = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK,
                             dedup_cross_form=False)
    assert raw.n_records_raw == 3
    assert sorted(raw.notionals.tolist()) == [900.0, 1000.0]  # X1 counted twice


def test_c09_window_orders_dedup_is_noop_on_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_flat_with_id(100.0, 5.0, "Buy", "A1")),
        (DAY_MS + 2_000, _bybit_flat_with_id(100.0, 9.0, "Sell", "A2")),
        (DAY_MS + 3_000, _bybit_flat_with_id(100.0, 7.0, "Buy", "A3")),
    ])
    on = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK)
    off = load_window_orders(base, "BTCUSDT", DAY, DAY, kink=C09_KINK,
                             dedup_cross_form=False)
    assert sorted(on.notionals.tolist()) == sorted(off.notionals.tolist())
    assert (on.n_records_raw, on.n_orders_total) == (off.n_records_raw,
                                                     off.n_orders_total)


# ---------------------------------------------------------------------------
# (f) c10 load_daily_rv -- daily RV over 1-min bars (GL-016/GL-017)
# ---------------------------------------------------------------------------

#: Three 1-min bars (100 -> 101 -> 102) shared by the c10/c11 fixtures.
_RV_PRICES = (100.0, 101.0, 102.0)
_RV_R1 = math.log(_RV_PRICES[1] / _RV_PRICES[0])
_RV_R2 = math.log(_RV_PRICES[2] / _RV_PRICES[1])
_RV_SSQ = _RV_R1 * _RV_R1 + _RV_R2 * _RV_R2


def _rv_flat_rows(day_ms: int, prices=_RV_PRICES) -> list[tuple[int, str]]:
    """One flat trade in each of the first ``len(prices)`` minutes of a day."""
    return [(day_ms + i * MINUTE_MS + 1_000, _bybit_payload(p, 0.1, "Buy"))
            for i, p in enumerate(prices)]


def test_c10_daily_rv_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, _rv_flat_rows(DAY_MS))
    out = load_daily_rv_c10(base, "bybit", "BTCUSDT", [DAY], min_bars_per_day=3)
    assert out.shape == (1,)
    assert out[0] == pytest.approx(math.log(_RV_SSQ))


def test_c10_daily_rv_flat_two_days_matches_legacy_group_by_date(tmp_path: Path) -> None:
    """Per-partition query == the previous single query's ``GROUP BY "date"``.

    The day grouping used to come from the hive ``date`` column; the expanded
    trade source no longer carries it, so the query now runs per date
    partition. This pins that both give the same per-day RV AND that no
    return crosses midnight (day 2 alone would otherwise leak into day 1).
    """
    import duckdb

    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, _rv_flat_rows(DAY_MS))
    _write_partition(base, "bybit", "BTCUSDT", DAY2,
                     _rv_flat_rows(DAY2_MS, (200.0, 202.0, 204.0)))
    files = [_parquet_path(base, "bybit", "BTCUSDT", d) for d in (DAY, DAY2)]
    file_list = "[" + ", ".join(f"'{f}'" for f in files) + "]"
    legacy_sql = f"""
        WITH bars AS (
            SELECT day, minute_idx, max_by(px, ts) AS px
            FROM (
                SELECT "date" AS day,
                       ts_exchange_ms AS ts,
                       CAST(ts_exchange_ms // 60000 AS BIGINT) AS minute_idx,
                       CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                                     json_extract_string(payload_json,'$.p')) AS DOUBLE) AS px
                FROM read_parquet({file_list}, hive_partitioning=1, union_by_name=1)
            )
            WHERE px IS NOT NULL AND isfinite(px) AND px > 0 AND ts IS NOT NULL
            GROUP BY day, minute_idx
        ),
        rets AS (
            SELECT day,
                   ln(px) - lag(ln(px)) OVER (PARTITION BY day ORDER BY minute_idx) AS r
            FROM bars
        )
        SELECT day, sum(r * r) AS ssq, count(r) AS n_rets
        FROM rets
        WHERE r IS NOT NULL AND isfinite(r)
        GROUP BY day
    """
    con = duckdb.connect()
    try:
        legacy = {str(d): math.log(float(s)) for d, s, _ in con.execute(legacy_sql).fetchall()}
    finally:
        con.close()
    out = load_daily_rv_c10(base, "bybit", "BTCUSDT", [DAY, DAY2], min_bars_per_day=3)
    assert out[0] == pytest.approx(legacy[DAY])
    assert out[1] == pytest.approx(legacy[DAY2])


def test_c10_daily_rv_envelope_only(tmp_path: Path) -> None:
    # All three trades in ONE envelope row with the packet ts in minute 0:
    # the per-trade $.T must spread them over three minute bars, otherwise
    # there is exactly one bar, no return, and the day would be NaN.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, p, f"e{i}")
            for i, p in enumerate(_RV_PRICES)
        ], envelope_ts=DAY_MS + 50)),
    ])
    out = load_daily_rv_c10(base, "bybit", "BTCUSDT", [DAY], min_bars_per_day=3)
    assert out[0] == pytest.approx(math.log(_RV_SSQ))


def test_c10_daily_rv_mixed_forms(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(_RV_PRICES[0], 0.1, "Buy")),   # flat
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + MINUTE_MS + 1_000, "Buy", 0.1, _RV_PRICES[1], "e1"),
            (DAY_MS + 2 * MINUTE_MS + 1_000, "Sell", 0.1, _RV_PRICES[2], "e2"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    out = load_daily_rv_c10(base, "bybit", "BTCUSDT", [DAY], min_bars_per_day=3)
    assert out[0] == pytest.approx(math.log(_RV_SSQ))


def test_c10_daily_rv_cross_form_duplicate_is_inert(tmp_path: Path) -> None:
    """NO de-duplication here, and none needed: the duplicate is inert.

    The RV is built from 1-min LAST-price bars, so the same trade appearing
    in both forms carries the same price at the same timestamp and cannot
    move a bar -- pinned by comparing against the duplicate-free partition.
    """
    base_dup = tmp_path / "dup"
    _write_partition(base_dup, "bybit", "BTCUSDT", DAY, [
        *[(DAY_MS + i * MINUTE_MS + 1_000,
           _bybit_flat_with_id(p, 0.1, "Buy", f"X{i}"))
          for i, p in enumerate(_RV_PRICES)],
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, p, f"X{i}")
            for i, p in enumerate(_RV_PRICES)          # every trade duplicated
        ], envelope_ts=DAY_MS + 50)),
    ])
    base_clean = tmp_path / "clean"
    _write_partition(base_clean, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + i * MINUTE_MS + 1_000, _bybit_flat_with_id(p, 0.1, "Buy", f"X{i}"))
        for i, p in enumerate(_RV_PRICES)
    ])
    dup = load_daily_rv_c10(base_dup, "bybit", "BTCUSDT", [DAY], min_bars_per_day=3)
    clean = load_daily_rv_c10(base_clean, "bybit", "BTCUSDT", [DAY], min_bars_per_day=3)
    assert dup[0] == pytest.approx(clean[0])
    assert dup[0] == pytest.approx(math.log(_RV_SSQ))


def test_c10_daily_rv_missing_files_error_unchanged(tmp_path: Path) -> None:
    with pytest.raises(C10DataError, match="no parquet"):
        load_daily_rv_c10(tmp_path / "empty", "bybit", "BTCUSDT", [DAY])


def test_c10_daily_rv_deribit_jsonrpc_envelope(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "deribit", "BTC-PERPETUAL", DAY, [
        (DAY_MS + 10, _deribit_envelope([
            (DAY_MS + i * MINUTE_MS + 1_000, "buy", 10.0, p, f"d{i}")
            for i, p in enumerate(_RV_PRICES)
        ], envelope_ts=DAY_MS + 10, jsonrpc=True)),
    ])
    out = load_daily_rv_c10(base, "deribit", "BTC-PERPETUAL", [DAY],
                            min_bars_per_day=3)
    assert out[0] == pytest.approx(math.log(_RV_SSQ))


# ---------------------------------------------------------------------------
# (g) c11 load_daily_rv -- daily RV = sqrt(sum r_1min^2), date-window filtered
# ---------------------------------------------------------------------------

def test_c11_daily_rv_flat_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, _rv_flat_rows(DAY_MS))
    out = load_daily_rv_c11(base, "BTCUSDT", DAY, DAY)
    assert set(out) == {DAY}
    assert out[DAY] == pytest.approx(math.sqrt(_RV_SSQ))


def test_c11_daily_rv_envelope_only(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, p, f"e{i}")
            for i, p in enumerate(_RV_PRICES)
        ], envelope_ts=DAY_MS + 50)),
    ])
    out = load_daily_rv_c11(base, "BTCUSDT", DAY, DAY)
    assert out[DAY] == pytest.approx(math.sqrt(_RV_SSQ))


def test_c11_daily_rv_mixed_forms(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 1_000, _bybit_payload(_RV_PRICES[0], 0.1, "Buy")),
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + MINUTE_MS + 1_000, "Buy", 0.1, _RV_PRICES[1], "e1"),
            (DAY_MS + 2 * MINUTE_MS + 1_000, "Sell", 0.1, _RV_PRICES[2], "e2"),
        ], envelope_ts=DAY_MS + 50)),
    ])
    out = load_daily_rv_c11(base, "BTCUSDT", DAY, DAY)
    assert out[DAY] == pytest.approx(math.sqrt(_RV_SSQ))


def test_c11_daily_rv_date_window_filter_still_applies(tmp_path: Path) -> None:
    # The hive ``date`` filter moved INTO the scanned source (the expanded
    # trade source has no ``date`` column) -- it must still exclude DAY2,
    # for envelope rows exactly as for flat ones.
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, _rv_flat_rows(DAY_MS))
    _write_partition(base, "bybit", "BTCUSDT", DAY2, [
        (DAY2_MS + 50, _bybit_envelope([
            (DAY2_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, p, f"e{i}")
            for i, p in enumerate((200.0, 202.0, 204.0))
        ], envelope_ts=DAY2_MS + 50)),
    ])
    both = load_daily_rv_c11(base, "BTCUSDT", DAY, DAY2)
    assert set(both) == {DAY, DAY2}
    only_first = load_daily_rv_c11(base, "BTCUSDT", DAY, DAY)
    assert set(only_first) == {DAY}
    assert only_first[DAY] == pytest.approx(both[DAY])


def test_c11_daily_rv_cross_form_duplicate_is_inert(tmp_path: Path) -> None:
    # Same reasoning as c10: last-price bars, so no de-duplication is needed.
    base_dup = tmp_path / "dup"
    _write_partition(base_dup, "bybit", "BTCUSDT", DAY, [
        *[(DAY_MS + i * MINUTE_MS + 1_000,
           _bybit_flat_with_id(p, 0.1, "Buy", f"X{i}"))
          for i, p in enumerate(_RV_PRICES)],
        (DAY_MS + 50, _bybit_envelope([
            (DAY_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, p, f"X{i}")
            for i, p in enumerate(_RV_PRICES)
        ], envelope_ts=DAY_MS + 50)),
    ])
    dup = load_daily_rv_c11(base_dup, "BTCUSDT", DAY, DAY)
    assert dup[DAY] == pytest.approx(math.sqrt(_RV_SSQ))


# ---------------------------------------------------------------------------
# (h) c13 load_returns_window -- trailing 1-min log-returns (data-gated cell)
# ---------------------------------------------------------------------------

#: c13 needs >= 2 * BLOCK_LEN_MIN = 120 one-minute returns, i.e. 121 bars.
_C13_N_BARS = 121
_C13_PRICES = tuple(100.0 + (i % 7) * 0.5 for i in range(_C13_N_BARS))
_C13_SNAPSHOT = DAY2  # trailing window = the day BEFORE the snapshot


def _c13_loader():
    """Import the c13 loader lazily (its module imports scipy at import time)."""
    pytest.importorskip("scipy")
    from bybit_edge.research.c13_tailshape.returns_tail import load_returns_window

    return load_returns_window


def _c13_expected_returns() -> np.ndarray:
    return np.diff(np.log(np.asarray(_C13_PRICES, dtype=np.float64)))


def test_c13_returns_window_flat_only(tmp_path: Path) -> None:
    load_returns_window = _c13_loader()
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + i * MINUTE_MS + 1_000, _bybit_payload(p, 0.1, "Buy"))
        for i, p in enumerate(_C13_PRICES)
    ])
    r, meta = load_returns_window(base, "BTCUSDT", _C13_SNAPSHOT,
                                  n_days=2, min_days=1)
    assert r.size == _C13_N_BARS - 1
    assert np.allclose(r, _c13_expected_returns())
    assert meta["n_days_present"] == 1


def test_c13_returns_window_envelope_only(tmp_path: Path) -> None:
    # ALL 121 trades in ONE envelope row: with the packet timestamp there
    # would be a single minute bar and ZERO returns (DataError), so this
    # pins the per-trade $.T end to end.
    load_returns_window = _c13_loader()
    base = tmp_path / "harvest"
    _write_partition(base, "bybit", "BTCUSDT", DAY, [
        (DAY_MS + 10, _bybit_envelope([
            (DAY_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, p, f"e{i}")
            for i, p in enumerate(_C13_PRICES)
        ], envelope_ts=DAY_MS + 10)),
    ])
    r, _ = load_returns_window(base, "BTCUSDT", _C13_SNAPSHOT,
                               n_days=2, min_days=1)
    assert r.size == _C13_N_BARS - 1
    assert np.allclose(r, _c13_expected_returns())


def test_c13_returns_window_mixed_forms(tmp_path: Path) -> None:
    load_returns_window = _c13_loader()
    base = tmp_path / "harvest"
    split = 61
    rows: list[tuple[int, str]] = [
        (DAY_MS + i * MINUTE_MS + 1_000, _bybit_payload(p, 0.1, "Buy"))
        for i, p in enumerate(_C13_PRICES[:split])
    ]
    rows.append((DAY_MS + 10, _bybit_envelope([
        (DAY_MS + i * MINUTE_MS + 1_000, "Sell", 0.1, _C13_PRICES[i], f"e{i}")
        for i in range(split, _C13_N_BARS)
    ], envelope_ts=DAY_MS + 10)))
    _write_partition(base, "bybit", "BTCUSDT", DAY, rows)
    r, _ = load_returns_window(base, "BTCUSDT", _C13_SNAPSHOT,
                               n_days=2, min_days=1)
    assert r.size == _C13_N_BARS - 1
    assert np.allclose(r, _c13_expected_returns())


def test_c13_returns_window_cross_form_duplicate_is_inert(tmp_path: Path) -> None:
    """NO de-duplication here either: the tick series is reduced to the LAST
    price per minute before any statistic, so a cross-form duplicate (same
    price, same ms) cannot change a single 1-min return."""
    load_returns_window = _c13_loader()
    base = tmp_path / "harvest"
    rows: list[tuple[int, str]] = [
        (DAY_MS + i * MINUTE_MS + 1_000, _bybit_flat_with_id(p, 0.1, "Buy", f"X{i}"))
        for i, p in enumerate(_C13_PRICES)
    ]
    # every second trade additionally delivered in the live envelope
    rows.append((DAY_MS + 10, _bybit_envelope([
        (DAY_MS + i * MINUTE_MS + 1_000, "Buy", 0.1, _C13_PRICES[i], f"X{i}")
        for i in range(0, _C13_N_BARS, 2)
    ], envelope_ts=DAY_MS + 10)))
    _write_partition(base, "bybit", "BTCUSDT", DAY, rows)
    r, _ = load_returns_window(base, "BTCUSDT", _C13_SNAPSHOT,
                               n_days=2, min_days=1)
    assert r.size == _C13_N_BARS - 1
    assert np.allclose(r, _c13_expected_returns())
