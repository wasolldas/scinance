"""WP-6 -- Options-Quote-Breite aus dem Harvest-Baum (KAPITALFREI).

Der Harvester zeichnet Bybit-Options-Ticker seit WP-12/DEC-08 (Harvest-Projekt)
im Strom ``raw/bybit/tickers/`` NEBEN den Perp-Tickern auf -- nicht in einem
eigenen ``option_tickers``-Strom.  Genau deshalb hat die DEC-43-Inventur sie
uebersehen (Korrektur: DEC-46).  Dieses Modul liest diese Frames und macht die
Quote-Breite als ZEITREIHE messbar -- insbesondere ueber das Stress-Fenster
um den 2026-08-19, das der REST-Sampler (Start 2026-08-24) nicht abdeckt.

Zwei bewusst getrennte Schritte:

1. **Probe** (``unwrap_payload`` + Treiber ``--probe``): VOR jeder Messung
   wird geprueft, was tatsaechlich in ``payload_json`` steht -- ob die Frames
   bid1Price/ask1Price/bid1Iv/ask1Iv fuehren, und unter welchem Wrapper.
   Die WS-Feldliste ist bis dahin eine Erwartung, keine Tatsache (die
   REST-Seite ist per WP-5 verifiziert, die WS-Seite nicht).
2. **Zensus**: je (Symbol, Minute) der LETZTE Frame (deterministisch ueber
   den zusammengesetzten Schluessel (ts, payload)), daraus je Minute die
   Breite im Strangle-Bein-Band und das ATM-markIv-Niveau.

DTE wird gegen das FRAME-Datum gerechnet, nie gegen "heute" (WP-5-Lehre,
per Test gepinnt).  Kein Verdikt, keine Schwellen: Messung.
"""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from bybit_edge.research.wp5_optchain.census import parse_symbol, quantile

__all__ = [
    "FIELD_ALIASES", "OPTION_SYMBOL_RE", "unwrap_payload", "frame_record",
    "minute_stats",
]

# BTC-4SEP26-73000-P oder BTC-25AUG26-76500-C-USDT (REST fuehrt das
# Settlement-Suffix, der WS-Strom je nach Quelle nicht -- beide zulassen).
OPTION_SYMBOL_RE = re.compile(
    r"^(BTC|ETH|SOL)-\d{1,2}[A-Z]{3}\d{2}-\d+(\.\d+)?-[CP](-[A-Z]+)?$")


def unwrap_payload(payload_json: str) -> dict[str, Any] | None:
    """Ticker-Dict aus einem Roh-Frame, tolerant gegen den Wrapper.

    Akzeptiert: das nackte Ticker-Objekt; ``{"topic": ..., "data": {...}}``;
    ``{"data": [{...}]}`` (Ein-Element-Liste).  Alles andere -> None, damit
    der Aufrufer zaehlen kann, wie viel er NICHT versteht (lautes Scheitern
    statt stiller Luecken).
    """
    try:
        obj = json.loads(payload_json)
    except (TypeError, ValueError):
        return None
    if not isinstance(obj, dict):
        return None
    data = obj.get("data", obj)
    if isinstance(data, list):
        if len(data) != 1 or not isinstance(data[0], dict):
            return None
        data = data[0]
    if not isinstance(data, dict):
        return None
    # Ein Ticker-Objekt muss sich mindestens selbst benennen koennen.
    if "symbol" not in data and "symbol" not in obj:
        return None
    if "symbol" not in data:
        data = dict(data)
        data["symbol"] = obj["symbol"]
    return data


def _f(x: Any) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# REST- und WS-Dialekt derselben Groessen. Der WP-6-Probe-Lauf am Bestand
# (2026-08-19, DEC-46) hat gezeigt: der Harvester speichert die WS-Frames
# mit bidPrice/askPrice/bidIv/askIv/markPriceIv — dieselben Groessen, andere
# Namen als der per WP-5 vermessene REST-Ticker.
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "bid": ("bid1Price", "bidPrice"),
    "ask": ("ask1Price", "askPrice"),
    "bid_iv": ("bid1Iv", "bidIv"),
    "ask_iv": ("ask1Iv", "askIv"),
    "mark_iv": ("markIv", "markPriceIv"),
    "bid_size": ("bid1Size", "bidSize"),
    "ask_size": ("ask1Size", "askSize"),
}


def _get(tick: dict[str, Any], key: str) -> float | None:
    """Wert unter dem ersten vorhandenen Alias (None statt raten)."""
    for name in FIELD_ALIASES[key]:
        if name in tick:
            return _f(tick[name])
    return None


def frame_record(symbol: str, tick: dict[str, Any],
                 frame_date: date) -> dict[str, Any] | None:
    """Ein Ticker-Frame -> Zensus-Record (None fuer Nicht-Optionen)."""
    if not OPTION_SYMBOL_RE.match(symbol):
        return None
    meta = parse_symbol(symbol)
    if meta is None:
        return None
    bid, ask = _get(tick, "bid"), _get(tick, "ask")
    biv, aiv = _get(tick, "bid_iv"), _get(tick, "ask_iv")
    two_sided = bool(bid and ask and bid > 0 and ask > 0)
    quoted_iv = bool(two_sided and biv is not None and aiv is not None
                     and biv > 0.0 and aiv > biv)
    return {
        "symbol": symbol,
        "dte": (meta["expiry"] - frame_date).days,
        "delta": _f(tick.get("delta")),
        "mark_iv": _get(tick, "mark_iv"),
        "under": _f(tick.get("underlyingPrice")),
        "two_sided": two_sided,
        "quoted_iv": quoted_iv,
        "iv_width_pts": (aiv - biv) * 100.0 if quoted_iv else None,
        "rel_spread": ((ask - bid) / (0.5 * (bid + ask)))
        if two_sided and (bid + ask) > 0 else None,
    }


def minute_stats(records: list[dict[str, Any]], *,
                 horizon: tuple[int, int] = (7, 14),
                 leg_delta: tuple[float, float] = (0.15, 0.30),
                 ) -> dict[str, Any]:
    """Eine Minuten-Zeile aus den Records aller Symbole dieser Minute."""
    hz = [r for r in records if horizon[0] <= r["dte"] <= horizon[1]]
    legs = [r for r in hz if r["quoted_iv"] and r["delta"] is not None
            and leg_delta[0] <= abs(r["delta"]) <= leg_delta[1]]
    atm = [r for r in hz if r["delta"] is not None
           and 0.35 <= abs(r["delta"]) <= 0.65]
    lw = [r["iv_width_pts"] for r in legs]

    def q(xs, p, nd=4):
        v = quantile(xs, p)
        return None if v is None else round(v, nd)

    return {
        "n_frames": len(records),
        "n_horizon": len(hz),
        "n_legs": len(legs),
        "leg_w_p50": q(lw, .50),
        "leg_w_p75": q(lw, .75),
        "leg_w_max": q(lw, 1.0),
        "leg_rel_p50": q([r["rel_spread"] for r in legs
                          if r["rel_spread"] is not None], .50),
        "atm_mark_iv": q([r["mark_iv"] for r in atm
                          if r["mark_iv"] is not None], .50),
        "under": q([r["under"] for r in records
                    if r["under"] is not None], .50, 2),
        "n_unquoted_legband": sum(
            1 for r in hz if not r["quoted_iv"] and r["delta"] is not None
            and leg_delta[0] <= abs(r["delta"]) <= leg_delta[1]),
    }
