"""Deribit ``markprice.options`` loader for H-13 (NEW — no prior loader exists).

Reads the read-only harvester Hive tree
``data/harvest/raw/deribit/markprice.options/symbol=<UNDERLYING>/date=<d>/*.parquet``
(same ``ts_exchange_ms`` + ``payload_json`` column convention as the Bybit
streams). Payload form per tick (DATASET.md):

    {"params": {"channel": "markprice.options.btc_usd",
                "data": [{"instrument_name": "BTC-27JUN26-70000-C",
                          "mark_iv": 55.1, "iv": 55.0, ...}, ...]}}

i.e. the mark IV of ALL active strikes per tick. For robustness the loader
also accepts a payload that is directly the ``params`` object, directly the
``data`` list, or a single per-instrument entry dict.

Documented assumptions (see README_H13.md):
  * **IV units:** ``mark_iv``/``iv`` values > 3 are treated as PERCENT and
    divided by 100 (Deribit quotes IV in percent, e.g. 55.0).
  * **Snapshot definition:** all ticks within +/- ``window_min`` minutes of
    08:00 UTC, last mark per instrument wins; if the window is empty, the
    single tick closest to 08:00 UTC of that day is used.
  * **Forward price:** preferred from an explicit ``forward_price`` /
    ``underlying_price`` / ``index_price`` field if present in any entry;
    otherwise estimated from put-call parity in inverse (coin-denominated)
    units: C_coin - P_coin ~= 1 - K/F, so F is the zero-crossing of the
    per-strike (C - P) mark-price differences (linear interpolation).
  * **Delta:** taken from an explicit ``delta`` field if present, otherwise
    approximated via Black-76 from the mark IV with r = 0:
    d1 = (ln(F/K) + 0.5*iv^2*T) / (iv*sqrt(T)); call delta = N(d1),
    put delta = N(d1) - 1.
  * **Smile construction:** tenor band 20-45 DTE (calendar days, ACT/365);
    among qualifying expiries the one with the MOST strikes inside the delta
    band 0.01 <= |delta| <= 0.5 is chosen (tie: nearest 30 DTE, then earliest
    expiry). Per strike the OTM side's IV is used (K >= F: call, K < F: put;
    fallback to the other side if the OTM quote is missing).
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import norm

#: Pre-registered tenor band in calendar days to expiry (registry H-13).
TENOR_DTE = (20, 45)
#: Pre-registered |delta| band (registry H-13).
DELTA_BAND = (0.01, 0.5)
#: Pre-registered per-day/symbol strike floor (unlock condition (iii)).
MIN_STRIKES = 12
#: Snapshot definition: 08:00 UTC +/- this many minutes.
SNAPSHOT_HOUR_UTC = 8
SNAPSHOT_WINDOW_MIN = 30

_MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
#: Deribit standard instrument name, e.g. ``BTC-27JUN26-70000-C``.
#: Strike may carry a ``d`` decimal separator (e.g. ``XRP_USDC-...-0d6535-P``).
INSTRUMENT_RE = re.compile(
    r"^(?P<underlying>[A-Z0-9_]+)-"
    r"(?P<day>\d{1,2})(?P<mon>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
    r"(?P<year>\d{2})-"
    r"(?P<strike>\d+(?:[.dD]\d+)?)-"
    r"(?P<cp>[CP])$"
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_]+$")


class OptionsDataError(RuntimeError):
    """Raised when the options snapshot cannot be loaded/constructed."""


@dataclass(slots=True, frozen=True)
class ParsedInstrument:
    """Expiry/strike/type parsed from a Deribit instrument name."""

    underlying: str
    expiry: date
    strike: float
    option_type: str  # "C" | "P"


def parse_instrument_name(name: str) -> ParsedInstrument | None:
    """Parse ``<UND>-<DDMMMYY>-<STRIKE>-<C|P>``; None if it does not match."""
    m = INSTRUMENT_RE.match(str(name).strip().upper())
    if not m:
        return None
    try:
        expiry = date(2000 + int(m["year"]), _MONTHS[m["mon"]], int(m["day"]))
    except ValueError:
        return None
    strike = float(m["strike"].replace("d", ".").replace("D", "."))
    return ParsedInstrument(
        underlying=m["underlying"], expiry=expiry,
        strike=strike, option_type=m["cp"],
    )


def _norm_iv(v: Any) -> float:
    """Normalise an IV field: values > 3 are percent (Deribit convention)."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return float("nan")
    if not math.isfinite(x) or x <= 0.0:
        return float("nan")
    return x / 100.0 if x > 3.0 else x


def _extract_entries(payload: Any) -> list[dict[str, Any]]:
    """Entries from any accepted payload form (see module docstring)."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            return []
    if isinstance(payload, dict):
        if "params" in payload and isinstance(payload["params"], dict):
            data = payload["params"].get("data")
            return [e for e in data if isinstance(e, dict)] if isinstance(data, list) else []
        if isinstance(payload.get("data"), list):
            return [e for e in payload["data"] if isinstance(e, dict)]
        if "instrument_name" in payload:
            return [payload]
        return []
    if isinstance(payload, list):
        return [e for e in payload if isinstance(e, dict)]
    return []


# ----------------------------------------------------------------------------
# Snapshot loading (read-only harvester tree)
# ----------------------------------------------------------------------------

def list_snapshot_dates(
    base_dir: Path | str,
    symbol: str,
    *,
    exchange: str = "deribit",
    stream: str = "markprice.options",
) -> list[str]:
    """Sorted ``YYYY-MM-DD`` dates with parquet data for ``symbol``."""
    if not _SYMBOL_RE.match(symbol):
        raise OptionsDataError(f"invalid symbol: {symbol!r}")
    root = Path(base_dir) / "raw" / exchange / stream / f"symbol={symbol}"
    if not root.is_dir():
        return []
    out = []
    for d in root.iterdir():
        if d.is_dir() and d.name.startswith("date="):
            ds = d.name[len("date="):]
            if _DATE_RE.match(ds) and list(d.glob("*.parquet")):
                out.append(ds)
    return sorted(out)


def load_snapshot_entries(
    base_dir: Path | str,
    symbol: str,
    date_str: str,
    *,
    snapshot_hour: int = SNAPSHOT_HOUR_UTC,
    window_min: int = SNAPSHOT_WINDOW_MIN,
    exchange: str = "deribit",
    stream: str = "markprice.options",
) -> dict[str, dict[str, Any]]:
    """Last mark per instrument around the 08:00 UTC snapshot of one day.

    Returns ``{instrument_name: entry_dict}``. Ticks within +/- ``window_min``
    of the snapshot time are used; if none exist, the single closest tick of
    the day is used (documented fallback). Read-only.
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise OptionsDataError(f"invalid symbol: {symbol!r}")
    if not _DATE_RE.match(date_str):
        raise OptionsDataError(f"invalid date: {date_str!r}")
    d = Path(base_dir) / "raw" / exchange / stream / f"symbol={symbol}" / f"date={date_str}"
    if not (d.is_dir() and list(d.glob("*.parquet"))):
        raise OptionsDataError(f"no parquet for {exchange}/{stream}/{symbol}@{date_str}")
    y, m, dd = (int(x) for x in date_str.split("-"))
    target_ms = int(datetime(y, m, dd, snapshot_hour, tzinfo=timezone.utc).timestamp() * 1000)
    glob = str(d / "*.parquet").replace("'", "''")
    con = duckdb.connect()
    try:
        rows = con.execute(
            f"SELECT ts_exchange_ms, payload_json FROM read_parquet('{glob}', "
            f"hive_partitioning=1, union_by_name=1) "
            f"WHERE ts_exchange_ms IS NOT NULL ORDER BY ts_exchange_ms"
        ).fetchall()
    finally:
        con.close()
    if not rows:
        raise OptionsDataError(f"{symbol}@{date_str}: 0 markprice rows")
    lo, hi = target_ms - window_min * 60_000, target_ms + window_min * 60_000
    in_win = [(ts, pj) for ts, pj in rows if lo <= ts <= hi]
    if not in_win:
        closest_ts = min(rows, key=lambda r: abs(r[0] - target_ms))[0]
        in_win = [(ts, pj) for ts, pj in rows if ts == closest_ts]
    by_instrument: dict[str, dict[str, Any]] = {}
    for ts, pj in in_win:  # ascending ts -> last mark per instrument wins
        for e in _extract_entries(pj):
            name = str(e.get("instrument_name", "")).strip()
            if name:
                by_instrument[name] = e
    if not by_instrument:
        raise OptionsDataError(f"{symbol}@{date_str}: no instrument entries in snapshot")
    return by_instrument


# ----------------------------------------------------------------------------
# Forward / delta / smile construction
# ----------------------------------------------------------------------------

def black76_delta(forward: float, strike: float, iv: float, t_years: float,
                  option_type: str) -> float:
    """Black-76 delta approximation from IV (r = 0, documented assumption)."""
    if not (forward > 0 and strike > 0 and iv > 0 and t_years > 0):
        return float("nan")
    sig_sqrt_t = iv * math.sqrt(t_years)
    d1 = (math.log(forward / strike) + 0.5 * iv * iv * t_years) / sig_sqrt_t
    nd1 = float(norm.cdf(d1))
    return nd1 if option_type == "C" else nd1 - 1.0


def estimate_forward(
    entries: dict[str, dict[str, Any]],
    parsed: dict[str, ParsedInstrument],
    expiry: date,
) -> float:
    """Forward for one expiry: explicit field, else inverse put-call parity.

    1. Median of any ``forward_price`` / ``underlying_price`` / ``index_price``
       field among the expiry's entries.
    2. Otherwise: for strikes with BOTH a call and a put ``mark_price`` (in
       coin units), C - P ~= 1 - K/F is decreasing in K; F is the linear
       zero-crossing of the (K, C-P) pairs.
    """
    explicit: list[float] = []
    cp: dict[float, dict[str, float]] = {}
    for name, e in entries.items():
        p = parsed.get(name)
        if p is None or p.expiry != expiry:
            continue
        for fld in ("forward_price", "underlying_price", "index_price"):
            try:
                v = float(e.get(fld))
                if math.isfinite(v) and v > 0:
                    explicit.append(v)
                    break
            except (TypeError, ValueError):
                pass
        try:
            mp = float(e.get("mark_price"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(mp):
            cp.setdefault(p.strike, {})[p.option_type] = mp
    if explicit:
        return float(np.median(explicit))
    ks = sorted(k for k, v in cp.items() if "C" in v and "P" in v)
    if len(ks) >= 2:
        diffs = [cp[k]["C"] - cp[k]["P"] for k in ks]
        for i in range(len(ks) - 1):
            a, b = diffs[i], diffs[i + 1]
            if a >= 0.0 >= b and a != b:
                return float(ks[i] + (ks[i + 1] - ks[i]) * a / (a - b))
    return float("nan")


@dataclass(slots=True)
class SmileSlice:
    """One filtered IV smile (single expiry) at a snapshot day."""

    symbol: str
    snapshot_date: str
    expiry: str
    dte: int
    t_years: float
    forward: float
    strikes: np.ndarray
    ivs: np.ndarray
    deltas: np.ndarray

    @property
    def n_strikes(self) -> int:
        return int(self.strikes.size)

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "snapshot_date": self.snapshot_date,
            "expiry": self.expiry,
            "dte": int(self.dte),
            "t_years": float(self.t_years),
            "forward": float(self.forward),
            "n_strikes": self.n_strikes,
            "strike_min": float(self.strikes.min()) if self.n_strikes else None,
            "strike_max": float(self.strikes.max()) if self.n_strikes else None,
        }


def build_smile(
    entries: dict[str, dict[str, Any]],
    symbol: str,
    snapshot_date: str,
    *,
    tenor_dte: tuple[int, int] = TENOR_DTE,
    delta_band: tuple[float, float] = DELTA_BAND,
) -> SmileSlice | None:
    """Tenor/delta-filtered single-expiry smile from snapshot entries.

    Returns None (never raises) if no expiry inside the tenor band yields at
    least one strike inside the delta band — callers use ``n_strikes`` against
    :data:`MIN_STRIKES` for the unlock condition.
    """
    snap = date(*(int(x) for x in snapshot_date.split("-")))
    parsed = {n: p for n in entries if (p := parse_instrument_name(n)) is not None}
    expiries = sorted({
        p.expiry for p in parsed.values()
        if tenor_dte[0] <= (p.expiry - snap).days <= tenor_dte[1]
    })
    candidates: list[SmileSlice] = []
    for expiry in expiries:
        dte = (expiry - snap).days
        t_years = dte / 365.0
        fwd = estimate_forward(entries, parsed, expiry)
        if not (math.isfinite(fwd) and fwd > 0):
            continue
        per_strike: dict[float, dict[str, tuple[float, float]]] = {}
        for name, p in parsed.items():
            if p.expiry != expiry:
                continue
            e = entries[name]
            iv = _norm_iv(e.get("mark_iv", e.get("iv")))
            if not math.isfinite(iv):
                continue
            try:
                delta = float(e["delta"])
            except (KeyError, TypeError, ValueError):
                delta = black76_delta(fwd, p.strike, iv, t_years, p.option_type)
            if not math.isfinite(delta):
                continue
            if not (delta_band[0] <= abs(delta) <= delta_band[1]):
                continue
            per_strike.setdefault(p.strike, {})[p.option_type] = (iv, delta)
        strikes, ivs, deltas = [], [], []
        for k in sorted(per_strike):
            sides = per_strike[k]
            otm = "C" if k >= fwd else "P"
            iv, delta = sides.get(otm, sides.get("C" if otm == "P" else "P"))
            strikes.append(k)
            ivs.append(iv)
            deltas.append(delta)
        if strikes:
            candidates.append(SmileSlice(
                symbol=symbol, snapshot_date=snapshot_date,
                expiry=expiry.isoformat(), dte=dte, t_years=t_years, forward=fwd,
                strikes=np.asarray(strikes, dtype=np.float64),
                ivs=np.asarray(ivs, dtype=np.float64),
                deltas=np.asarray(deltas, dtype=np.float64),
            ))
    if not candidates:
        return None
    # deterministic choice: most strikes, then nearest 30 DTE, then earliest.
    candidates.sort(key=lambda s: (-s.n_strikes, abs(s.dte - 30), s.expiry))
    return candidates[0]


def load_smile(
    base_dir: Path | str,
    symbol: str,
    date_str: str,
    *,
    snapshot_hour: int = SNAPSHOT_HOUR_UTC,
    tenor_dte: tuple[int, int] = TENOR_DTE,
    delta_band: tuple[float, float] = DELTA_BAND,
) -> SmileSlice | None:
    """Convenience: load snapshot entries and build the filtered smile."""
    try:
        entries = load_snapshot_entries(
            base_dir, symbol, date_str, snapshot_hour=snapshot_hour,
        )
    except OptionsDataError as exc:
        print(f"[h13] options {symbol}@{date_str}: {exc}", file=sys.stderr, flush=True)
        return None
    return build_smile(
        entries, symbol, date_str, tenor_dte=tenor_dte, delta_band=delta_band,
    )
