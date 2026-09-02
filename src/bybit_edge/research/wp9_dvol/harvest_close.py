"""WP-9 -- Deribit DVOL harvest daily close (KAPITALFREI, read-only).

Reads ``data/harvest/raw/deribit/dvol/symbol=*/date=YYYY-MM-DD/*.parquet``
(schema: ts_local_ns, ts_exchange_ms, topic, stream, symbol, payload_json)
and computes ONE deterministic daily close per (symbol, UTC day): the LAST
frame by the composite ordering key ``(ts_exchange_ms, payload_json)`` via
DuckDB ``arg_max`` -- byte-identical convention to
``wp6_optstress.extract``/``bar_cache`` (never a raw-scan-order pick).

FIELD LAYOUT [sek]: the volatility value is expected under a
``volatility`` key, either directly on the payload or nested one level
under ``data``/``params.data`` (JSON-RPC subscription envelope) --
wrapper-tolerant the same way as ``wp6_optstress.extract.unwrap_payload``,
extended with the ``params.data`` shape the WS subscription API for
Deribit uses. This has NOT been confirmed against a live frame in this
sandbox (read-only harvest tree access here is also fixture-only in
tests): ``daily_close`` raises ``DvolFieldLayoutError`` loudly -- never
silently returns ``None`` -- the moment a resolved arg_max frame does not
carry the field under any known shape, naming the raw payload head (300
chars) and the keys actually seen.

Manifest-DONE days are PREFERRED (``bar_cache.resolve_manifest_path`` /
``manifest_done_days``) but not required to read: a live stream may be
mid-day, and the spec (section 3) only asks that non-DONE days carry a
label, not that they be excluded. When the harvest manifest itself is
unreadable/missing, every row's ``manifest_done`` is ``None`` (unknown)
rather than a hard failure -- this module measures the read-only harvest
tree, it does not gate on the harvester's own bookkeeping.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "VOLATILITY_FIELD_ALIASES", "DvolFieldLayoutError",
    "unwrap_dvol_payload", "extract_volatility", "day_glob",
    "discover_harvest_days", "probe_day", "daily_close",
]

#: [sek] -- expected volatility field name(s), unverified in this sandbox.
VOLATILITY_FIELD_ALIASES: tuple[str, ...] = ("volatility",)


class DvolFieldLayoutError(RuntimeError):
    """Loud failure: a harvested DVOL frame does not match [sek] expectations."""


def unwrap_dvol_payload(payload_json: str) -> dict[str, Any] | None:
    """DVOL ticker dict from a raw frame, wrapper-tolerant.

    Candidate shapes tried, in order: the bare payload; ``payload["data"]``
    (dict, or a one-element list of dicts -- the wp6_optstress convention);
    ``payload["params"]["data"]`` (the JSON-RPC WS subscription envelope
    Deribit uses, e.g. ``{"method": "subscription", "params": {"channel":
    ..., "data": {...}}}``). Returns the FIRST candidate that actually
    carries one of ``VOLATILITY_FIELD_ALIASES``; ``None`` when nothing
    recognisable is found (the caller decides how to react -- probing
    reports it, ``daily_close`` raises).
    """
    try:
        obj = json.loads(payload_json)
    except (TypeError, ValueError):
        return None
    if not isinstance(obj, dict):
        return None
    candidates: list[dict[str, Any]] = [obj]
    data = obj.get("data")
    if isinstance(data, dict):
        candidates.append(data)
    elif isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
        candidates.append(data[0])
    params = obj.get("params")
    if isinstance(params, dict):
        pdata = params.get("data")
        if isinstance(pdata, dict):
            candidates.append(pdata)
    for c in candidates:
        if any(name in c for name in VOLATILITY_FIELD_ALIASES):
            return c
    return None


def extract_volatility(tick: dict[str, Any]) -> float | None:
    """The volatility number under the first present alias, else None."""
    for name in VOLATILITY_FIELD_ALIASES:
        if name in tick:
            try:
                return float(tick[name])
            except (TypeError, ValueError):
                return None
    return None


def day_glob(base: Path | str, symbol: str, day: str) -> str:
    return str(Path(base) / "raw" / "deribit" / "dvol" / f"symbol={symbol}"
               / f"date={day}" / "*.parquet")


def discover_harvest_days(base: Path | str, symbol: str) -> list[str]:
    """ISO dates with an on-disk partition for ``symbol`` (sorted, no I/O
    into the parquet files themselves -- a directory listing only)."""
    root = Path(base) / "raw" / "deribit" / "dvol" / f"symbol={symbol}"
    if not root.is_dir():
        return []
    days = [p.name[len("date="):] for p in root.iterdir()
            if p.is_dir() and p.name.startswith("date=")]
    return sorted(days)


def probe_day(con: Any, base: Path | str, symbol: str, day: str) -> dict[str, Any]:
    """Probe ONE (symbol, day): frame count + resolved field layout.

    Never raises on a layout problem -- returns a status dict instead, so
    ``--probe`` (and ``daily_close`` internally) can decide loud-fail vs.
    "no data this day" without duplicating the DuckDB query.
    """
    part_dir = Path(base) / "raw" / "deribit" / "dvol" / f"symbol={symbol}" / f"date={day}"
    if not part_dir.is_dir() or not any(part_dir.glob("*.parquet")):
        # No partition at all -- distinct from UNREADABLE (files present but
        # broken): DuckDB's read_parquet raises IOException on a glob that
        # resolves to zero files, which would otherwise be indistinguishable
        # from a genuine read error.
        return {"symbol": symbol, "date": day, "status": "NO_FRAMES"}
    g = day_glob(base, symbol, day)
    try:
        row = con.execute(
            "SELECT count(*) AS n, "
            "  arg_max(payload_json, (ts_exchange_ms, payload_json)) AS pj, "
            "  arg_max(ts_exchange_ms, (ts_exchange_ms, payload_json)) AS ts "
            "FROM read_parquet(?)", [g]).fetchone()
    except Exception as exc:  # noqa: BLE001 -- glob may match nothing readable
        return {"symbol": symbol, "date": day, "status": "UNREADABLE",
                "detail": str(exc)}
    n, pj, ts = row
    if not n:
        return {"symbol": symbol, "date": day, "status": "NO_FRAMES"}
    tick = unwrap_dvol_payload(pj)
    if tick is None:
        return {"symbol": symbol, "date": day, "status": "UNPARSEABLE",
                "raw_head": pj[:300]}
    vol = extract_volatility(tick)
    if vol is None:
        return {"symbol": symbol, "date": day, "status": "FIELD_MISSING",
                "keys": sorted(tick.keys()), "raw_head": pj[:300]}
    return {"symbol": symbol, "date": day, "status": "OK", "n_frames": int(n),
            "ts_exchange_ms": int(ts), "close": vol, "raw_head": pj[:300]}


def _manifest_done_days_safe(
    base: Path | str, exchange: str, stream: str, symbol: str,
    start: str, end: str,
) -> set[str] | None:
    """``bar_cache.manifest_done_days`` -- ``None`` (unknown) instead of a
    hard failure when the manifest is missing/unreadable (harvest-tree
    reads must not be gated on the harvester's own bookkeeping)."""
    from bybit_edge.research.bar_cache import BarCacheError, manifest_done_days
    try:
        return manifest_done_days(base, exchange, stream, symbol, start, end)
    except BarCacheError:
        return None


def daily_close(con: Any, base: Path | str, symbol: str, days: list[str]) -> list[dict[str, Any]]:
    """One deterministic daily close per day in ``days``.

    Raises ``DvolFieldLayoutError`` the moment any day WITH frames fails
    to parse under the [sek] layout (loud-fail, never a silently dropped
    day). Days with no on-disk frames or an unreadable partition are kept
    in the output with ``status`` set instead of ``close`` -- the caller
    (crossval) filters those before computing differences. Every OK row
    carries ``manifest_done`` (``True``/``False``/``None`` if the manifest
    itself could not be resolved) per spec section 3 ("Nicht-DONE-Tage nur
    mit Etikett").
    """
    base = Path(base)
    done = (_manifest_done_days_safe(base, "deribit", "dvol", symbol,
                                      days[0], days[-1])
            if days else set())
    out: list[dict[str, Any]] = []
    for day in days:
        p = probe_day(con, base, symbol, day)
        if p["status"] in ("UNREADABLE", "NO_FRAMES"):
            out.append({**p, "manifest_done": None if done is None else day in done})
            continue
        if p["status"] != "OK":
            raise DvolFieldLayoutError(
                f"{symbol} {day}: {p['status']} -- payload does not match the "
                f"expected [sek] volatility field layout (alias(es) "
                f"{VOLATILITY_FIELD_ALIASES}). Raw (300 ch): "
                f"{p.get('raw_head', '')!r} keys={p.get('keys')}")
        out.append({
            "symbol": symbol, "date": day, "ts_exchange_ms": p["ts_exchange_ms"],
            "close": p["close"], "n_frames": p["n_frames"],
            "manifest_done": None if done is None else day in done,
        })
    return out
