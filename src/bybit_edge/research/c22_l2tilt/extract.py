"""WP-2 — one-pass L2 tilt extraction via snapshot+delta book replay (H-22).

Registered pre-work for H-22 (registry 2026-08-15; census verdict DEC-36):
the bybit ``orderbook`` stream is snapshot(+~2/day)+delta over the whole
history, so the near-touch tilt requires an actual BOOK RECONSTRUCTION —
never a snapshot read. This module is that one pass ("L2-Ein-Pass"): it
replays each registered window sequentially and writes per-day minute-
sampled tilt series, hash-pinned per day exactly like the WP-0 bar cache.

Replay rules (registered, binding):

  * records of a day are applied in ``(ts_exchange_ms, u)`` order;
    ``type=snapshot`` replaces the book, ``type=delta`` upserts levels
    (size "0" deletes),
  * update-id continuity: a delta whose ``u`` is not ``prev_u + 1`` counts
    one SEQUENCE BREAK (the delta is still applied — with ~2 snapshots/day
    "wait for resync" would discard half a day),
  * VALIDATION at every full snapshot: the replayed book is compared to the
    snapshot content; a mismatch counts one break and the book is reset to
    the snapshot (resync),
  * a day with > 10 breaks, or a window-start day before the first snapshot
    arrives, is LOUDLY discarded (``status="discarded"`` sidecar, counted —
    never silent),
  * tilt sample at each minute boundary m: state after all records with
    ``ts <= m``; T = (B - A) / (B + A) with B/A = summed bid/ask sizes
    within +-25 bps of mid. Day coverage = fraction of the day's 1440
    minutes with a defined sample.

Book state carries ACROSS days within one window pass (snapshots are too
rare for day-independent processing); the whole window is one deterministic
sequential pass, so a re-run reproduces it bit-identically (pinned by test).

Output layout (new path, never inside the harvester tree):
    <out>/tilt_1min/exchange=<x>/symbol=<s>/date=<d>/tilt.parquet
                                            .../manifest.json (sha256 etc.)
plus ``tilt_fingerprint()`` over a window — quoted by the H-22 run report.

KAPITALFREI: pure measurement extraction. No cost quantity of any kind.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = 1

#: Registered feature constants (registry H-22).
BAND_BP = 25.0
MAX_BREAKS_PER_DAY = 10

MS_PER_MINUTE = 60_000
MS_PER_DAY = 86_400_000

TILT_COLUMNS = ("minute_idx", "tilt", "mid")


class L2ExtractError(RuntimeError):
    """Loud failure of the tilt extraction."""


# ----------------------------------------------------------------------------
# order book
# ----------------------------------------------------------------------------

class Book:
    """Minimal price-level book with exact-string price keys."""

    __slots__ = ("bids", "asks", "u", "valid")

    def __init__(self) -> None:
        self.bids: dict[str, float] = {}
        self.asks: dict[str, float] = {}
        self.u: int | None = None
        self.valid = False

    def apply_snapshot(self, b: list, a: list, u: int | None) -> None:
        self.bids = {px: float(sz) for px, sz in b if float(sz) > 0.0}
        self.asks = {px: float(sz) for px, sz in a if float(sz) > 0.0}
        self.u = u
        self.valid = True

    def apply_delta(self, b: list, a: list, u: int | None) -> bool:
        """Apply one delta; returns False when the update id is non-contiguous."""
        contiguous = (self.u is None or u is None or u == self.u + 1)
        for side, updates in ((self.bids, b), (self.asks, a)):
            for px, sz in updates:
                if float(sz) == 0.0:
                    side.pop(px, None)
                else:
                    side[px] = float(sz)
        self.u = u
        return contiguous

    def matches_snapshot(self, b: list, a: list) -> bool:
        snap_b = {px: float(sz) for px, sz in b if float(sz) > 0.0}
        snap_a = {px: float(sz) for px, sz in a if float(sz) > 0.0}
        return self.bids == snap_b and self.asks == snap_a

    def tilt(self, band_bp: float = BAND_BP) -> tuple[float, float] | None:
        """(tilt, mid) within +-``band_bp`` of mid; None when undefined."""
        if not self.valid or not self.bids or not self.asks:
            return None
        best_bid = max(float(p) for p in self.bids)
        best_ask = min(float(p) for p in self.asks)
        if best_ask <= 0 or best_bid <= 0 or best_ask < best_bid * 0.5:
            return None
        mid = 0.5 * (best_bid + best_ask)
        lo, hi = mid * (1 - band_bp / 1e4), mid * (1 + band_bp / 1e4)
        b_sum = sum(sz for px, sz in self.bids.items() if float(px) >= lo)
        a_sum = sum(sz for px, sz in self.asks.items() if float(px) <= hi)
        if b_sum + a_sum <= 0.0:
            return None
        return (b_sum - a_sum) / (b_sum + a_sum), mid


# ----------------------------------------------------------------------------
# record iteration
# ----------------------------------------------------------------------------

def _day_records(con: Any, raw_dir: Path, day: str):
    """Yield (ts_ms, payload dict) for one day, (ts, u)-ordered, chunked."""
    glob = (raw_dir / f"date={day}" / "*.parquet").as_posix()
    cur = con.execute(f"""
        SELECT ts_exchange_ms,
               payload_json,
               COALESCE(TRY_CAST(json_extract_string(payload_json,'$.data.u') AS BIGINT),
                        TRY_CAST(json_extract_string(payload_json,'$.u') AS BIGINT)) AS u
        FROM read_parquet('{glob}', union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL
        ORDER BY ts_exchange_ms, u
    """)
    while True:
        chunk = cur.fetchmany(20_000)
        if not chunk:
            break
        for ts, payload, u in chunk:
            try:
                rec = json.loads(payload)
            except (TypeError, ValueError):
                continue
            yield int(ts), rec, u


def _rec_parts(rec: dict) -> tuple[str, list, list, int | None]:
    rtype = rec.get("type", "")
    data = rec.get("data", rec)
    b = data.get("b") or []
    a = data.get("a") or []
    u = data.get("u")
    return rtype, b, a, (int(u) if u is not None else None)


# ----------------------------------------------------------------------------
# window extraction (one sequential deterministic pass)
# ----------------------------------------------------------------------------

def _tilt_hash(arrays: dict[str, np.ndarray]) -> str:
    h = hashlib.sha256()
    for col in TILT_COLUMNS:
        h.update(col.encode("ascii"))
        h.update(np.ascontiguousarray(arrays[col]).tobytes())
    return h.hexdigest()


def _write_day(out_dir: Path, exchange: str, symbol: str, day: str,
               minute_idx: list[int], tilt: list[float], mid: list[float],
               *, n_breaks: int, n_snapshots: int, status: str,
               reason: str = "") -> dict[str, Any]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    part = (out_dir / "tilt_1min" / f"exchange={exchange}"
            / f"symbol={symbol}" / f"date={day}")
    part.mkdir(parents=True, exist_ok=True)
    arrays = {"minute_idx": np.asarray(minute_idx, dtype=np.int64),
              "tilt": np.asarray(tilt, dtype=np.float64),
              "mid": np.asarray(mid, dtype=np.float64)}
    meta = {
        "schema_version": SCHEMA_VERSION, "exchange": exchange,
        "symbol": symbol, "date": day, "status": status, "reason": reason,
        "band_bp": BAND_BP, "n_samples": len(minute_idx),
        "coverage": len(minute_idx) / 1440.0,
        "n_seq_breaks": n_breaks, "n_snapshots": n_snapshots,
        "sha256_values": _tilt_hash(arrays),
    }
    if status == "ok":
        pq.write_table(pa.table({
            "minute_idx": pa.array(arrays["minute_idx"], pa.int64()),
            "tilt": pa.array(arrays["tilt"], pa.float64()),
            "mid": pa.array(arrays["mid"], pa.float64()),
        }), part / "tilt.parquet")
    (part / "manifest.json").write_text(json.dumps(meta, indent=2),
                                        encoding="utf-8")
    return meta


def extract_window(
    base_dir: Path | str,
    out_dir: Path | str,
    symbol: str,
    start: str,
    end: str,
    *,
    exchange: str = "bybit",
    stream: str = "orderbook",
    band_bp: float = BAND_BP,
    max_breaks: int = MAX_BREAKS_PER_DAY,
    progress: Any = None,
) -> dict[str, Any]:
    """One deterministic sequential pass over ``[start, end]``.

    Returns a summary with per-status day counts and total breaks. Days with
    no raw partition are counted ``no_raw`` (they simply reduce coverage —
    the census documented the holes). The pass carries book state across
    days; the FIRST day starts invalid until its first snapshot.
    """
    import duckdb

    base, out = Path(base_dir), Path(out_dir)
    raw_dir = base / "raw" / exchange / stream / f"symbol={symbol}"
    if not raw_dir.is_dir():
        raise L2ExtractError(f"no orderbook stream at {raw_dir}")

    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    days = [(d0 + timedelta(days=i)).isoformat()
            for i in range((d1 - d0).days + 1)]

    con = duckdb.connect()
    book = Book()
    counts = {"ok": 0, "discarded": 0, "no_raw": 0}
    total_breaks = 0
    try:
        for day in days:
            if not list((raw_dir / f"date={day}").glob("*.parquet")):
                counts["no_raw"] += 1
                if progress is not None:
                    progress(symbol, {"day": day, "status": "no_raw"})
                continue
            day_ms0 = (date.fromisoformat(day) - date(1970, 1, 1)).days * MS_PER_DAY
            next_boundary = day_ms0 + MS_PER_MINUTE
            minute_idx: list[int] = []
            tilts: list[float] = []
            mids: list[float] = []
            n_breaks = 0
            n_snaps = 0

            def _sample_upto(ts_limit: int) -> None:
                nonlocal next_boundary
                while next_boundary <= ts_limit:
                    t = book.tilt(band_bp)
                    if t is not None:
                        minute_idx.append(next_boundary // MS_PER_MINUTE - 1)
                        tilts.append(t[0])
                        mids.append(t[1])
                    next_boundary += MS_PER_MINUTE

            for ts, rec, _u in _day_records(con, raw_dir, day):
                _sample_upto(ts)
                rtype, b, a, u = _rec_parts(rec)
                if rtype == "snapshot":
                    n_snaps += 1
                    if book.valid and not book.matches_snapshot(b, a):
                        n_breaks += 1          # replay drifted -> resync
                    book.apply_snapshot(b, a, u)
                elif rtype == "delta":
                    if book.valid and not book.apply_delta(b, a, u):
                        n_breaks += 1
            _sample_upto(day_ms0 + MS_PER_DAY)   # tail of the day

            total_breaks += n_breaks
            if n_breaks > max_breaks:
                meta = _write_day(out, exchange, symbol, day, [], [], [],
                                  n_breaks=n_breaks, n_snapshots=n_snaps,
                                  status="discarded",
                                  reason=f"{n_breaks} sequence breaks > {max_breaks}")
                book = Book()                    # do not trust the state
                counts["discarded"] += 1
            elif n_snaps == 0 and not minute_idx:
                meta = _write_day(out, exchange, symbol, day, [], [], [],
                                  n_breaks=n_breaks, n_snapshots=0,
                                  status="discarded",
                                  reason="no snapshot and no valid state")
                counts["discarded"] += 1
            else:
                meta = _write_day(out, exchange, symbol, day, minute_idx,
                                  tilts, mids, n_breaks=n_breaks,
                                  n_snapshots=n_snaps, status="ok")
                counts["ok"] += 1
            if progress is not None:
                progress(symbol, {"day": day, "status": meta["status"],
                                  "n_samples": meta["n_samples"],
                                  "n_seq_breaks": n_breaks})
    finally:
        con.close()
    return {"symbol": symbol, "exchange": exchange, "stream": stream,
            "range": [start, end], "days_in_range": len(days), **counts,
            "total_seq_breaks": total_breaks}


# ----------------------------------------------------------------------------
# read + fingerprint + coverage
# ----------------------------------------------------------------------------

def load_daily_tilt(out_dir: Path | str, exchange: str, symbol: str,
                    start: str, end: str) -> dict[str, np.ndarray]:
    """(day_idx, tilt_median, coverage) for the OK days of ``[start, end]``."""
    import pyarrow.parquet as pq

    out = Path(out_dir)
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    day_idx, med, cov = [], [], []
    for i in range((d1 - d0).days + 1):
        day = (d0 + timedelta(days=i)).isoformat()
        part = (out / "tilt_1min" / f"exchange={exchange}"
                / f"symbol={symbol}" / f"date={day}")
        meta_path = part / "manifest.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "ok" or meta.get("n_samples", 0) == 0:
            continue
        table = pq.read_table(part / "tilt.parquet", columns=["tilt"])
        t = table.column("tilt").to_numpy(zero_copy_only=False)
        day_idx.append((date.fromisoformat(day) - date(1970, 1, 1)).days)
        med.append(float(np.median(t)))
        cov.append(float(meta["coverage"]))
    return {"day_idx": np.asarray(day_idx, dtype=np.int64),
            "tilt_median": np.asarray(med, dtype=np.float64),
            "coverage": np.asarray(cov, dtype=np.float64)}


def tilt_fingerprint(out_dir: Path | str, exchange: str, symbol: str,
                     start: str, end: str) -> dict[str, Any]:
    """SHA-256 over all OK days' exact value bytes (H-22 report duty)."""
    import pyarrow.parquet as pq

    out = Path(out_dir)
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    h = hashlib.sha256()
    n_days = n_samples = 0
    for i in range((d1 - d0).days + 1):
        day = (d0 + timedelta(days=i)).isoformat()
        part = (out / "tilt_1min" / f"exchange={exchange}"
                / f"symbol={symbol}" / f"date={day}")
        if not (part / "manifest.json").is_file():
            continue
        meta = json.loads((part / "manifest.json").read_text(encoding="utf-8"))
        if meta.get("status") != "ok":
            continue
        table = pq.read_table(part / "tilt.parquet", columns=list(TILT_COLUMNS))
        arrays = {c: table.column(c).to_numpy(zero_copy_only=False)
                  for c in TILT_COLUMNS}
        h.update(day.encode("ascii"))
        h.update(_tilt_hash(arrays).encode("ascii"))
        n_days += 1
        n_samples += int(arrays["minute_idx"].size)
    return {"schema_version": SCHEMA_VERSION, "exchange": exchange,
            "symbol": symbol, "range": [start, end],
            "n_ok_days": n_days, "n_samples": n_samples,
            "sha256_values": h.hexdigest()}


__all__ = [
    "BAND_BP",
    "Book",
    "L2ExtractError",
    "MAX_BREAKS_PER_DAY",
    "extract_window",
    "load_daily_tilt",
    "tilt_fingerprint",
]
