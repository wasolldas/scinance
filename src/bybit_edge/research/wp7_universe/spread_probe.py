"""WP-7 -- ``PERP_SPREAD_BP`` je Symbol-Dezil: Inhaltsprobe zuerst.

PRD 4.1: **"Zuerst: Inhaltsprobe (C.8) auf den vorhandenen `bybit/tickers`-
Strom"** -- checks whether the harvester's existing ``raw/bybit/tickers``
stream already carries ``bid1Price``/``ask1Price``/``openInterest``/
``fundingRate``. If the probe finds them, the spread census runs on
BESTANDSDATEN in minutes and nothing new is collected; only if the probe
fails does this module fall back to ONE ``GET /v5/market/tickers`` call
(``bybit_rest.fetch_tickers``).

Reads ``data/harvest`` READ-ONLY (never writes there -- Schutzgut, same
discipline as ``wp6_optstress.extract``, whose ``unwrap_payload`` this
module reuses verbatim for the envelope-unwrapping step rather than
reimplementing it).
"""
from __future__ import annotations

import re
from typing import Any, Callable

from bybit_edge.research.wp6_optstress.extract import unwrap_payload

from . import bybit_rest

__all__ = [
    "REQUIRED_FIELDS", "PERP_FIELD_ALIASES", "is_option_symbol",
    "probe_harvest_tickers", "perp_snapshot_from_harvest",
    "perp_snapshot_from_rest", "decile_spread_census",
]

#: PRD 4.1 -- the four fields the content probe checks for (canonical REST
#: names; ``PERP_FIELD_ALIASES`` also accepts the WS-stream dialect, same
#: two-dialect situation ``wp6_optstress`` documented for options tickers).
REQUIRED_FIELDS: tuple[str, ...] = (
    "bid1Price", "ask1Price", "openInterest", "fundingRate")

PERP_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "bid1Price": ("bid1Price", "bidPrice"),
    "ask1Price": ("ask1Price", "askPrice"),
    "openInterest": ("openInterest",),
    "fundingRate": ("fundingRate",),
    "turnover24h": ("turnover24h", "turnover_24h"),
}

#: Reuses wp6_optstress's own option-symbol pattern to EXCLUDE options from
#: a perp spread census (the two streams share one harvest topic).
_OPTION_SYMBOL_RE = re.compile(
    r"^(BTC|ETH|SOL)-\d{1,2}[A-Z]{3}\d{2}-\d+(\.\d+)?-[CP](-[A-Z]+)?$")


def is_option_symbol(symbol: str) -> bool:
    return bool(_OPTION_SYMBOL_RE.match(symbol))


def _get_field(tick: dict[str, Any], key: str) -> Any:
    for name in PERP_FIELD_ALIASES.get(key, (key,)):
        if name in tick:
            return tick[name]
    return None


def _day_glob(base, day: str) -> str:
    from pathlib import Path
    return str(Path(base) / "raw" / "bybit" / "tickers" / "symbol=*"
               / f"date={day}" / "*.parquet")


def probe_harvest_tickers(base_dir, days: list[str]) -> dict[str, Any]:
    """Content probe: for each day, the LAST frame of the busiest perp
    symbol -- required-field presence, loud (never silently "probably
    fine"). ``ok=False`` if ANY day yields no readable perp frame, or the
    sampled frame is missing a required field.
    """
    import duckdb

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    per_day: dict[str, Any] = {}
    ok = True
    for day in days:
        glob = _day_glob(base_dir, day)
        try:
            rows = con.execute(
                "SELECT symbol, count(*) AS n, "
                "  arg_max(payload_json, (ts_exchange_ms, payload_json)) AS pj "
                "FROM read_parquet(?) GROUP BY symbol", [glob]).fetchall()
        except Exception as exc:  # noqa: BLE001 -- surfaced loudly below
            per_day[day] = {"status": "UNREADABLE", "error": str(exc)}
            ok = False
            continue
        perps = [(s, n, pj) for s, n, pj in rows if not is_option_symbol(s)]
        if not perps:
            per_day[day] = {"status": "NO_PERP_FRAMES"}
            ok = False
            continue
        symbol, n, pj = max(perps, key=lambda r: r[1])
        tick = unwrap_payload(pj)
        if tick is None:
            per_day[day] = {"status": "UNPARSEABLE", "sample_symbol": symbol,
                             "raw_head": pj[:300]}
            ok = False
            continue
        have = {f: (_get_field(tick, f) is not None) for f in REQUIRED_FIELDS}
        missing = [f for f, present in have.items() if not present]
        per_day[day] = {"status": "OK" if not missing else "FIELDS_MISSING",
                         "sample_symbol": symbol, "n_frames": n,
                         "fields_present": have, "fields_missing": missing,
                         "n_perp_symbols": len(perps)}
        if missing:
            ok = False
    return {"days": per_day, "ok": ok}


def perp_snapshot_from_harvest(base_dir, day: str) -> list[dict[str, Any]]:
    """Last frame per perp symbol on ``day`` -> ``{symbol, bid, ask,
    open_interest, funding_rate, turnover24h}`` rows for the decile
    census. Skips a symbol whose last frame is unparseable or missing
    bid/ask (counted, never silently invented)."""
    import duckdb

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    rows = con.execute(
        "SELECT symbol, arg_max(payload_json, (ts_exchange_ms, payload_json)) "
        "FROM read_parquet(?) GROUP BY symbol", [_day_glob(base_dir, day)]
    ).fetchall()
    out: list[dict[str, Any]] = []
    for symbol, pj in rows:
        if is_option_symbol(symbol):
            continue
        tick = unwrap_payload(pj)
        if tick is None:
            continue
        bid, ask = _get_field(tick, "bid1Price"), _get_field(tick, "ask1Price")
        try:
            bid_f, ask_f = float(bid), float(ask)
        except (TypeError, ValueError):
            continue
        if bid_f <= 0 or ask_f <= 0:
            continue
        turnover = _get_field(tick, "turnover24h")
        out.append({
            "symbol": symbol, "bid": bid_f, "ask": ask_f,
            "open_interest": _get_field(tick, "openInterest"),
            "funding_rate": _get_field(tick, "fundingRate"),
            "turnover24h": float(turnover) if turnover is not None else None,
        })
    return out


def perp_snapshot_from_rest(*, category: str = "linear",
                             fetcher: Callable[[str], bytes] | None = None) -> list[dict[str, Any]]:
    """REST fallback (spec: "sonst ein REST-Tickers-Call")."""
    result = bybit_rest.fetch_tickers(category=category, fetcher=fetcher)
    out: list[dict[str, Any]] = []
    for row in result["rows"]:
        if is_option_symbol(str(row.get("symbol", ""))):
            continue
        try:
            bid_f, ask_f = float(row["bid1Price"]), float(row["ask1Price"])
        except (KeyError, TypeError, ValueError):
            continue
        if bid_f <= 0 or ask_f <= 0:
            continue
        turnover = row.get("turnover24h")
        out.append({
            "symbol": row["symbol"], "bid": bid_f, "ask": ask_f,
            "open_interest": row.get("openInterest"),
            "funding_rate": row.get("fundingRate"),
            "turnover24h": float(turnover) if turnover is not None else None,
        })
    return out


def decile_spread_census(snapshot: list[dict[str, Any]], *, n_deciles: int = 10) -> dict[str, Any]:
    """``PERP_SPREAD_BP`` je Umsatzdezil: sort the snapshot by
    ``turnover24h`` (descending -- decile 1 = highest turnover / majors),
    split into ``n_deciles`` roughly-equal groups, report the MEDIAN
    relative spread in bp per decile. Rows without a turnover figure are
    excluded from the ranking (counted separately, never mixed into a
    decile they can't be correctly ranked into).
    """
    ranked = [r for r in snapshot if r.get("turnover24h") is not None]
    unranked = len(snapshot) - len(ranked)
    ranked.sort(key=lambda r: r["turnover24h"], reverse=True)
    n = len(ranked)
    deciles: list[dict[str, Any]] = []
    if n == 0:
        return {"n_symbols": len(snapshot), "n_ranked": 0,
                "n_unranked_no_turnover": unranked, "deciles": deciles}
    for d in range(n_deciles):
        lo = (n * d) // n_deciles
        hi = (n * (d + 1)) // n_deciles
        group = ranked[lo:hi]
        if not group:
            continue
        spreads_bp = sorted(
            (r["ask"] - r["bid"]) / (0.5 * (r["ask"] + r["bid"])) * 10_000.0
            for r in group)
        mid = len(spreads_bp) // 2
        median = (spreads_bp[mid] if len(spreads_bp) % 2
                  else 0.5 * (spreads_bp[mid - 1] + spreads_bp[mid]))
        deciles.append({"decile": d + 1, "n_symbols": len(group),
                         "perp_spread_bp_median": round(median, 4)})
    return {"n_symbols": len(snapshot), "n_ranked": n,
            "n_unranked_no_turnover": unranked, "deciles": deciles}
