"""WP-12 -- kline availability probe for delisted symbols (the decisive
feasibility question, task brief item 2).

For every delisted LINEAR symbol in the register, probes whether Bybit's
public ``GET /v5/market/kline`` still serves daily history for the 90
days before its delisting date (or its announcement date if no delisting
date was parseable). Reuses ``wp7_universe.bybit_rest.fetch_kline_symbol``
UNCHANGED (read-only import, task brief) -- this module adds no new REST
call shape of its own, only the symbol/window selection and the
availability verdict.

This is a PROBE, not a panel build: results are stored under
``data/delisting_register/klines/`` (NOT under ``data/harvest``, NOT
``data/panel_1d`` -- a separate ``source=bybit_delisted`` panel tree is
explicitly OUT OF SCOPE for this task, per the task brief: "just probed
and reported").
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from ..wp7_universe import bybit_rest

__all__ = [
    "PROBE_WINDOW_DAYS", "delisted_linear_symbols", "reference_ms_for_symbol",
    "probe_symbol_availability", "probe_register", "write_klines_parquet",
    "write_probe_summary",
]

#: Task brief: "90 days before its delisting date (or the announcement
#: date)".
PROBE_WINDOW_DAYS = 90
_DAY_MS = 86_400_000


def delisted_linear_symbols(register_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicated (by symbol, first occurrence wins) linear-category
    symbols out of the register, each carrying the announcement's
    ``delisting_ms``/``publish_ms`` it was first seen with -- the
    reference point ``reference_ms_for_symbol`` probes around."""
    by_symbol: dict[str, dict[str, Any]] = {}
    for row in register_rows:
        if row.get("category") != "linear":
            continue
        for sym in row.get("symbols") or []:
            if not sym.endswith("USDT"):
                continue  # category=="linear" guess already filters this in practice
            by_symbol.setdefault(sym, {
                "symbol": sym, "delisting_ms": row.get("delisting_ms"),
                "publish_ms": row.get("publish_ms"),
                "announcement_id": row.get("announcement_id"),
            })
    return sorted(by_symbol.values(), key=lambda r: r["symbol"])


def reference_ms_for_symbol(entry: dict[str, Any]) -> int | None:
    """``delisting_ms`` if parseable, else ``publish_ms``, else ``None``
    (a symbol with neither is reported as ``skipped_no_reference_date``,
    never silently probed against an invented window)."""
    if entry.get("delisting_ms") is not None:
        return int(entry["delisting_ms"])
    if entry.get("publish_ms") is not None:
        return int(entry["publish_ms"])
    return None


def probe_symbol_availability(
    symbol: str, reference_ms: int, *, category: str = "linear",
    window_days: int = PROBE_WINDOW_DAYS,
    fetcher: Callable[[str], bytes] | None = None,
) -> dict[str, Any]:
    """ONE ``fetch_kline_symbol`` call over ``[reference_ms -
    window_days*_DAY_MS, reference_ms]`` -- ``n_rows``, first/last observed
    date, and ``available`` (``n_rows > 0``)."""
    start_ms = reference_ms - window_days * _DAY_MS
    result = bybit_rest.fetch_kline_symbol(
        symbol, start_ms, reference_ms, category=category, interval="D",
        fetcher=fetcher)
    rows = result["rows"]
    first_ms = rows[0]["start_ms"] if rows else None
    last_ms = rows[-1]["start_ms"] if rows else None
    return {
        "symbol": symbol, "reference_ms": reference_ms,
        "window_start_ms": start_ms, "window_end_ms": reference_ms,
        "n_rows": result["n_rows"], "available": result["n_rows"] > 0,
        "first_ms": first_ms, "last_ms": last_ms,
        "raw_sha256": result["raw_sha256"], "rows": rows,
    }


def probe_register(
    register_rows: list[dict[str, Any]], *, window_days: int = PROBE_WINDOW_DAYS,
    fetcher: Callable[[str], bytes] | None = None, max_symbols: int | None = None,
) -> dict[str, Any]:
    """Probe every deduplicated delisted linear symbol in the register.
    Returns per-symbol results plus the availability-table summary counts
    (task brief item 4: "n available / n not")."""
    entries = delisted_linear_symbols(register_rows)
    if max_symbols is not None:
        entries = entries[:max_symbols]
    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    for entry in entries:
        ref = reference_ms_for_symbol(entry)
        if ref is None:
            skipped.append(entry["symbol"])
            continue
        probe = probe_symbol_availability(
            entry["symbol"], ref, window_days=window_days, fetcher=fetcher)
        probe["reference_source"] = "delisting_ms" if entry.get("delisting_ms") is not None else "publish_ms"
        results.append(probe)
    n_available = sum(1 for r in results if r["available"])
    n_unavailable = len(results) - n_available
    return {
        "window_days": window_days, "n_symbols_probed": len(results),
        "n_available": n_available, "n_unavailable": n_unavailable,
        "n_skipped_no_reference_date": len(skipped),
        "skipped_symbols": skipped, "results": results,
    }


def write_klines_parquet(out_dir: Path | str, probe_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One ``<symbol>.parquet`` per probed symbol WITH available history,
    under ``data/delisting_register/klines/`` (allowed -- not
    ``data/harvest``, not ``data/panel_1d``). Returns per-symbol
    ``{symbol, path, sha256, n_rows}``."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write delisted klines under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[dict[str, Any]] = []
    for r in probe_results:
        if not r["available"]:
            continue
        rows = r["rows"]
        cols = {
            "start_ms": [row["start_ms"] for row in rows],
            "open": [row["open"] for row in rows],
            "high": [row["high"] for row in rows],
            "low": [row["low"] for row in rows],
            "close": [row["close"] for row in rows],
            "volume": [row["volume"] for row in rows],
            "turnover": [row["turnover"] for row in rows],
        }
        table = pa.table(cols)
        path = out_dir / f"{r['symbol']}.parquet"
        pq.write_table(table, path)
        written.append({"symbol": r["symbol"], "path": str(path),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "n_rows": len(rows)})
    return written


def write_probe_summary(out_dir: Path | str, summary: dict[str, Any]) -> dict[str, str]:
    """Write the probe summary (WITHOUT the bulky per-row ``rows`` arrays --
    those live in the per-symbol parquet files) as JSON. Never under
    ``data/harvest``."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write kline probe summary under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    lean = dict(summary)
    lean["results"] = [{k: v for k, v in r.items() if k != "rows"} for r in summary.get("results", [])]
    path = out_dir / "kline_probe_summary.json"
    path.write_text(json.dumps(lean, indent=1), encoding="utf-8")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
