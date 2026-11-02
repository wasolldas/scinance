"""H-27 RV definition: panel daily close (Bybit 1D kline) vs last publicTrade before 00:00 UTC.

Only days before 2024-06-01 (Rule 1 / blind seal).  Prints per day: equality, relative deviation,
seconds before midnight of the last trade.  No return or volatility is computed.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from h27_common import harvest, assert_rv_day  # noqa: E402

PANEL = HERE.parent / "panel" / "panel_1d"
DAYS = ["2021-06-15", "2022-11-09", "2023-03-15", "2023-09-15", "2023-12-15", "2024-03-15"]


def panel_close(sym: str, day: str) -> float:
    year = day[:4]
    for state in ("frozen", "open"):
        f = PANEL / state / "source=bybit" / "category=linear" / f"symbol={sym}" / f"year={year}" / "part.parquet"
        if f.exists():
            t = pq.ParquetFile(f).read(columns=["start_ms", "close"])
            for ms, c in zip(t.column("start_ms").to_pylist(), t.column("close").to_pylist()):
                if datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat() == day:
                    return float(c)
    raise KeyError((sym, day))


def main() -> None:
    hd = harvest()
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        for day in DAYS:
            assert_rv_day(day)
            df = hd.load("publicTrade", [sym], day, day, exchange="bybit",
                         columns=["ts_local_ns", "payload_json"])
            best_ts, best_px, n_at_best = None, None, 0
            for pj in df["payload_json"].to_list():
                o = json.loads(pj)
                ts = float(o["timestamp"])
                if best_ts is None or ts > best_ts:
                    best_ts, best_px, n_at_best = ts, float(o["price"]), 1
                elif ts == best_ts:
                    best_px, n_at_best = float(o["price"]), n_at_best + 1   # file order breaks ties
            pc = panel_close(sym, day)
            midnight = datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() + 86400
            out[f"{sym} {day}"] = {"equal": pc == best_px, "rel_dev": pc / best_px - 1.0,
                                   "last_trade_s_before_midnight": round(midnight - best_ts, 4),
                                   "trades_at_last_ts": n_at_best, "n_trades": df.height}
            print(sym, day, out[f"{sym} {day}"], flush=True)
    (HERE / "conv_check.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
