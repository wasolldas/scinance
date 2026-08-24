"""WP-5 -- Bybit option-chain quote-spread census (KAPITALFREI im Kern).

Reads a Bybit v5 ``/v5/market/tickers?category=option`` snapshot (the raw
``result.list``, or a bare list of the same records) and produces a
deterministic census of QUOTE WIDTH, keyed by time-to-expiry and by
|delta|.

Why the |delta| axis is not optional
------------------------------------
Bybit reports ``bid1Iv``/``ask1Iv`` for every symbol, including deep ITM
options whose price is essentially intrinsic value.  There vega -> 0, so
inverting a one-tick price width into implied volatility divides by ~0 and
yields IV widths of tens of vol points that describe NOTHING about the
option market's willingness to trade volatility.  Pooling over all strikes
therefore reports a number driven entirely by the degenerate corner.  Every
IV statistic here is reported per |delta| bucket for that reason, and the
strategy-relevant read is taken from the OTM buckets only.

The scale-free conversion
-------------------------
``vega / S`` (USD per vol point, per unit of index) is dimensionless and
lets a fee quoted as a fraction of the index be expressed in vol points:

    cost_volpts = n_fills * fee_fraction * S / vega

This module computes ``vega/S`` from the snapshot and reports the
break-even fee for a given edge.  It states no fee schedule of its own --
the fee is a caller-supplied parameter, because Bybit's option fee is NOT
a canonical repo constant (``FEE_MAKER``/``FEE_TAKER`` are perp constants).

No thresholds, no verdicts, no PnL: this module measures and reports.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

__all__ = [
    "MONTHS", "DTE_BUCKETS", "DELTA_BUCKETS",
    "parse_symbol", "load_snapshot", "quantile", "bucket_stats",
    "vega_over_index", "breakeven_fee_bp", "cost_volpts", "census",
]

MONTHS = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT",
     "NOV", "DEC"])}

DTE_BUCKETS: tuple[tuple[int, int, str], ...] = (
    (0, 7, "0-7"), (8, 21, "8-21"), (22, 45, "22-45"),
    (46, 120, "46-120"), (121, 10 ** 6, ">120"),
)

DELTA_BUCKETS: tuple[tuple[float, float, str], ...] = (
    (0.00, 0.10, "|d| 0.00-0.10"),
    (0.10, 0.20, "|d| 0.10-0.20"),
    (0.20, 0.35, "|d| 0.20-0.35"),
    (0.35, 0.65, "|d| 0.35-0.65 ATM"),
    (0.65, 1.01, "|d| 0.65-1.00 ITM"),
)


def parse_symbol(sym: str) -> dict[str, Any] | None:
    """``BTC-25AUG26-76500-C-USDT`` -> base/expiry/strike/cp, else None."""
    parts = sym.split("-")
    if len(parts) < 4:
        return None
    exp = parts[1]
    if len(exp) < 6:
        return None
    try:
        day, mon, yy = int(exp[:-5]), exp[-5:-2], int(exp[-2:])
        expiry = date(2000 + yy, MONTHS[mon], day)
        strike = float(parts[2])
    except (ValueError, KeyError):
        return None
    if parts[3] not in ("C", "P"):
        return None
    return {"base": parts[0], "expiry": expiry, "strike": strike,
            "cp": parts[3]}


def _f(x: Any, default: float | None = None) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def load_snapshot(path: str | Path, asof: date) -> list[dict[str, Any]]:
    """Parse a Bybit option tickers snapshot into census records.

    Accepts a bare list or a full ``{"result": {"list": [...]}}`` envelope,
    with or without a UTF-8 BOM (PowerShell ``Out-File`` writes one).
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if isinstance(raw, list):
        rows = raw
    elif "result" in raw:
        rows = raw["result"]["list"]
    else:
        # PowerShell's ConvertTo-Json unwraps a one-element array into a bare
        # object; accept that rather than losing the snapshot.
        rows = [raw]
    out: list[dict[str, Any]] = []
    for r in rows:
        meta = parse_symbol(r["symbol"])
        if meta is None:
            continue
        bid, ask = _f(r.get("bid1Price")), _f(r.get("ask1Price"))
        bid_iv, ask_iv = _f(r.get("bid1Iv")), _f(r.get("ask1Iv"))
        rec: dict[str, Any] = dict(meta)
        rec.update(
            symbol=r["symbol"],
            dte=(meta["expiry"] - asof).days,
            bid=bid, ask=ask, bid_iv=bid_iv, ask_iv=ask_iv,
            mark=_f(r.get("markPrice")), mark_iv=_f(r.get("markIv")),
            under=_f(r.get("underlyingPrice")),
            delta=_f(r.get("delta")), vega=_f(r.get("vega")),
            oi=_f(r.get("openInterest"), 0.0) or 0.0,
            vol24=_f(r.get("volume24h"), 0.0) or 0.0,
            bid_sz=_f(r.get("bid1Size"), 0.0) or 0.0,
            ask_sz=_f(r.get("ask1Size"), 0.0) or 0.0,
        )
        two_sided = bool(bid and ask and bid > 0 and ask > 0)
        rec["two_sided"] = two_sided
        if two_sided:
            mid = 0.5 * (bid + ask)
            rec["mid"] = mid
            rec["abs_spread"] = ask - bid
            rec["rel_spread"] = (ask - bid) / mid if mid > 0 else None
        rec["quoted_iv"] = bool(
            two_sided and bid_iv is not None and ask_iv is not None
            and bid_iv > 0.0 and ask_iv > bid_iv)
        if rec["quoted_iv"]:
            rec["iv_width_pts"] = (ask_iv - bid_iv) * 100.0
        out.append(rec)
    return out


def quantile(xs: Sequence[float], p: float) -> float | None:
    """Linear-interpolation quantile; None on an empty sample."""
    s = sorted(xs)
    if not s:
        return None
    if len(s) == 1:
        return s[0]
    i = p * (len(s) - 1)
    lo = int(i)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (i - lo) * (s[hi] - s[lo])


def bucket_stats(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Coverage + IV-width + relative-width + liquidity summary."""
    rows = list(rows)
    quoted = [r for r in rows if r["quoted_iv"]]
    ivs = [r["iv_width_pts"] for r in quoted]
    rels = [r["rel_spread"] for r in rows
            if r["two_sided"] and r.get("rel_spread") is not None]
    return {
        "n": len(rows),
        "n_two_sided": sum(1 for r in rows if r["two_sided"]),
        "n_quoted_iv": len(quoted),
        "iv_width_pts": {f"p{int(p*100)}": quantile(ivs, p)
                         for p in (0.25, 0.50, 0.75, 0.90)},
        "rel_spread": {f"p{int(p*100)}": quantile(rels, p)
                       for p in (0.50, 0.75)},
        "oi_p50": quantile([r["oi"] for r in rows], 0.50),
        "vol24_p50": quantile([r["vol24"] for r in rows], 0.50),
        "bid_size_p50": quantile([r["bid_sz"] for r in rows], 0.50),
    }


def vega_over_index(rows: Iterable[dict[str, Any]]) -> float | None:
    """Median vega/S in bp of index per vol point (scale-free)."""
    vals = [1e4 * r["vega"] / r["under"] for r in rows
            if r.get("vega") and r.get("under")]
    return quantile(vals, 0.50)


def cost_volpts(fee_bp_per_fill: float, n_fills: int,
                vega_over_s_bp: float) -> float:
    """Fee cost expressed in vol points.

    ``fee_bp_per_fill`` is bp of the INDEX (Bybit quotes option fees that
    way); ``vega_over_s_bp`` is bp of index per vol point.
    """
    return n_fills * fee_bp_per_fill / vega_over_s_bp


def breakeven_fee_bp(edge_volpts: float, n_fills: int,
                     vega_over_s_bp: float) -> float:
    """Fee per fill (bp of index) at which the edge is exactly consumed."""
    return edge_volpts * vega_over_s_bp / n_fills


def census(rows: Sequence[dict[str, Any]], *, horizon: tuple[int, int],
           leg_delta: tuple[float, float],
           edges_volpts: Sequence[float] = (1.0, 2.0, 3.0, 5.0),
           fills: Sequence[int] = (2, 4)) -> dict[str, Any]:
    """Full census payload for one symbol's snapshot."""
    unders = [r["under"] for r in rows if r.get("under")]
    by_dte = {name: bucket_stats(r for r in rows if lo <= r["dte"] <= hi)
              for lo, hi, name in DTE_BUCKETS}
    hz = [r for r in rows if horizon[0] <= r["dte"] <= horizon[1]]
    by_delta = {
        name: bucket_stats(r for r in hz if r.get("delta") is not None
                           and lo <= abs(r["delta"]) <= hi)
        for lo, hi, name in DELTA_BUCKETS}
    per_expiry = {}
    for exp in sorted({r["expiry"] for r in rows}):
        sub = [r for r in rows if r["expiry"] == exp
               and r.get("delta") is not None
               and leg_delta[0] <= abs(r["delta"]) <= leg_delta[1]]
        if sub:
            st = bucket_stats(sub)
            st["dte"] = sub[0]["dte"]
            per_expiry[exp.isoformat()] = st
    legs = [r for r in hz if r.get("delta") is not None
            and leg_delta[0] <= abs(r["delta"]) <= leg_delta[1]
            and r["quoted_iv"]]
    vs = vega_over_index(legs) if legs else None
    econ: dict[str, Any] = {"vega_over_index_bp_per_volpt": vs}
    if vs:
        econ["breakeven_fee_bp_per_fill"] = {
            f"edge{e:g}_fills{n}": breakeven_fee_bp(e, n, vs)
            for e in edges_volpts for n in fills}
        econ["fee_cost_volpts"] = {
            f"fee{f:g}bp_fills{n}": cost_volpts(f, n, vs)
            for f in (1.0, 2.0, 3.0) for n in fills}
        w = quantile([r["iv_width_pts"] for r in legs], 0.50)
        econ["leg_iv_width_p50_pts"] = w
        econ["spread_cost_2legs_roundtrip_volpts"] = 2.0 * w if w else None
    return {
        "n_symbols": len(rows),
        "underlying_p50": quantile(unders, 0.50),
        "n_two_sided": sum(1 for r in rows if r["two_sided"]),
        "n_quoted_iv": sum(1 for r in rows if r["quoted_iv"]),
        "by_dte": by_dte,
        "horizon": {"dte": list(horizon), "by_delta": by_delta},
        "legs": {"delta_band": list(leg_delta), "n": len(legs),
                 "stats": bucket_stats(legs) if legs else None,
                 "symbols": [r["symbol"] for r in
                             sorted(legs, key=lambda x: (x["dte"],
                                                         abs(x["delta"])))]},
        "per_expiry_otm": per_expiry,
        "economics": econ,
    }
