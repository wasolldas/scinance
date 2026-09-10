"""WP-10(B) -- L2+trade replay driving the queue-fill model (KAPITALFREI).

Reuses the WP-2/WP-4 snapshot+delta book replay
(``bybit_edge.research.c22_l2tilt.extract``: ``Book``, ``_day_records``,
``_rec_parts``, the break/discard rules, ``MAX_BREAKS_PER_DAY``) so the
book reconstruction itself is EXACTLY the machinery already pinned by the
WP-2/WP-4 tests -- never a second, silently-different implementation.

One continuous sequential pass over ``[start, end]`` (book state carries
across days, same discipline as WP-2/WP-4) builds a single growing
per-window array of touch samples -- ``(ts, bid_px, bid_sz, ask_px,
ask_sz)`` at EVERY orderbook record ("top-of-book best bid/ask
price+size snapshots per L2 update", spec wording) -- and a single
``publicTrade`` array (read via ``payload_sql`` dialect helpers, the same
ones ``bar_cache`` uses, so trade parsing never drifts between stores).
One hypothetical quote is placed on EACH side at EVERY minute boundary of
every eligible day (deterministic schedule); each is evaluated with
``queue_model.simulate_quote`` against a forward slice of the touch/trade
arrays covering ``horizon_s`` (fill) + ``adv_sel_horizon_s`` (adverse
selection).

**Own store.** Output lives under ``fillshadow_1min/`` -- a NEW path
beside (never inside) the frozen ``tilt_1min``/``spread_1min`` stores; a
WP-10(B) run must leave both byte-identical (test-pinned, mirroring the
WP-4 store-isolation test).

**Manifest-DONE gating.** On top of the WP-2/WP-4 break-budget/snapshot
discard rules (which govern whether the REPLAY itself is trustworthy), a
day is only eligible for QUOTE PLACEMENT (the actual measurement) when
the harvest manifest (``bar_cache.resolve_manifest_path`` /
``bar_cache.manifest_done_days``) marks BOTH the orderbook and the
publicTrade partition DONE for that day -- an extra safety layer specific
to WP-10(B) (a partial/live-collecting day can otherwise look plausible
but silently undercount trades). A day whose replay is discarded, or
whose manifest entry is not DONE, contributes ZERO placed quotes and is
recorded as such in the day's manifest -- never silently skipped.

KAPITALFREI: pure measurement extraction. No cost quantity of any kind.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from bybit_edge.research.bar_cache import (
    BarCacheError,
    _PX_SQL,
    _SIDE_SQL,
    _SIZE_STR_SQL,
    manifest_done_days,
)
from bybit_edge.research.c22_l2tilt.extract import (
    MAX_BREAKS_PER_DAY,
    Book,
    _day_records,
    _rec_parts,
)
from bybit_edge.research.payload_sql import cross_form_dedup_qualify, trade_rows_sql

from . import queue_model as qm

SCHEMA_VERSION = 1

MS_PER_MINUTE = 60_000
MS_PER_DAY = 86_400_000
EPOCH = date(1970, 1, 1)

#: Design parameter (labelled, like the 10s/60s horizons): our synthetic
#: quote size = this fraction of the touch's own visible size at t0 --
#: small enough that "joining the queue" never dominates the level.
DEFAULT_QUOTE_SIZE_FRACTION = 0.1

FILLSHADOW_COLUMNS = (
    "minute_idx", "side", "price", "size", "position0",
    "fifo_filled", "fifo_fill_time_ms", "fifo_latency_s", "fifo_adv_sel_bp",
    "prorata_filled", "prorata_fill_time_ms", "prorata_latency_s", "prorata_adv_sel_bp",
    "touch_moved_away", "insufficient_forward_data",
)


class ReplayError(RuntimeError):
    """Loud failure of the WP-10(B) replay."""


def _refuse_harvest(path: Path) -> None:
    if "data/harvest" in str(path).replace("\\", "/"):
        raise ReplayError(f"refusing to write WP-10(B) fillshadow store under data/harvest: {path}")


def _day_ms(day: str) -> int:
    return (date.fromisoformat(day) - EPOCH).days * MS_PER_DAY


def _days_between(start: str, end: str) -> list[str]:
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


# ----------------------------------------------------------------------------
# probe: what's actually present, no replay
# ----------------------------------------------------------------------------

def probe(base_dir: Path | str, symbol: str, start: str, end: str, *,
         exchange: str = "bybit", orderbook_stream: str = "orderbook",
         trade_stream: str = "publicTrade") -> dict[str, Any]:
    """Which days have raw partitions present, and manifest-DONE counts.

    Never raises on a missing manifest (that only matters at run time) --
    reports it as ``manifest_error`` instead so a probe always completes.
    """
    base = Path(base_dir)
    ob_dir = base / "raw" / exchange / orderbook_stream / f"symbol={symbol}"
    tr_dir = base / "raw" / exchange / trade_stream / f"symbol={symbol}"
    days = _days_between(start, end)
    ob_present = [d for d in days if list((ob_dir / f"date={d}").glob("*.parquet"))]
    tr_present = [d for d in days if list((tr_dir / f"date={d}").glob("*.parquet"))]
    result: dict[str, Any] = {
        "symbol": symbol, "exchange": exchange, "range": [start, end],
        "days_in_range": len(days),
        "orderbook_days_present": len(ob_present), "trade_days_present": len(tr_present),
        "orderbook_stream_dir_exists": ob_dir.is_dir(),
        "trade_stream_dir_exists": tr_dir.is_dir(),
    }
    try:
        done_ob = manifest_done_days(base, exchange, orderbook_stream, symbol, start, end)
        done_tr = manifest_done_days(base, exchange, trade_stream, symbol, start, end)
        result["orderbook_days_done"] = len(done_ob)
        result["trade_days_done"] = len(done_tr)
        result["days_eligible_for_placement"] = len(done_ob & done_tr)
    except BarCacheError as exc:
        result["manifest_error"] = str(exc)
    return result


# ----------------------------------------------------------------------------
# trades: one query per day, dialect-shared with bar_cache
# ----------------------------------------------------------------------------

def _trades_sql(glob: str) -> str:
    trade_rows = trade_rows_sql(
        f"(SELECT * FROM read_parquet('{glob}', hive_partitioning=0,"
        f" union_by_name=1)) AS src")
    return f"""
        SELECT ts_exchange_ms AS ts, {_SIDE_SQL} AS side,
               {_PX_SQL} AS px, TRY_CAST({_SIZE_STR_SQL} AS DOUBLE) AS sz
        FROM {trade_rows}
        WHERE ts_exchange_ms IS NOT NULL
        {cross_form_dedup_qualify()}
        ORDER BY ts
    """


def _load_trades_for_day(con: Any, trade_dir: Path, day: str) -> list[tuple[int, str, float, float]]:
    """One day's ``publicTrade`` rows, ts-ascending (query already orders
    by ``ts``). Factored out of ``_load_trades`` so the streaming driver
    can load exactly one day at a time, in lockstep with the book replay,
    without ever holding more than a few days of trades in memory."""
    rows: list[tuple[int, str, float, float]] = []
    if not list((trade_dir / f"date={day}").glob("*.parquet")):
        return rows
    glob = (trade_dir / f"date={day}" / "*.parquet").as_posix()
    cur = con.execute(_trades_sql(glob))
    while True:
        chunk = cur.fetchmany(20_000)
        if not chunk:
            break
        for ts, side, px, sz in chunk:
            if ts is None or side not in ("buy", "sell") or px is None or sz is None:
                continue
            if sz <= 0.0 or px <= 0.0:
                continue
            rows.append((int(ts), side, float(px), float(sz)))
    return rows


def _load_trades(con: Any, trade_dir: Path, days: list[str]) -> list[tuple[int, str, float, float]]:
    rows: list[tuple[int, str, float, float]] = []
    for day in days:
        rows.extend(_load_trades_for_day(con, trade_dir, day))
    rows.sort(key=lambda r: r[0])
    return rows


# ----------------------------------------------------------------------------
# orderbook replay -> global touch-sample arrays (WP-2/WP-4 machinery reused)
# ----------------------------------------------------------------------------

def _replay_one_day(
    con: Any, ob_dir: Path, day: str, book: Book, *,
    ts_a: list[int], bid_px_a: list[float], bid_sz_a: list[float],
    ask_px_a: list[float], ask_sz_a: list[float], max_breaks: int,
) -> dict[str, Any]:
    """Replay ONE day's raw orderbook records, mutating ``book`` (carries
    across days, exactly the WP-2/WP-4 discipline) and APPENDING this
    day's touch samples to the five parallel arrays (also mutated in
    place) -- the single per-day unit shared by both the legacy
    whole-window replay (``_replay_touch_samples``) and the streaming
    driver (``run_window``), so the two can never silently diverge.

    Returns this day's own ``{"status", "reason", "n_breaks",
    "n_snapshots", "reset_book"}`` -- ``reset_book`` tells the CALLER
    whether the break-budget was exceeded (the book must not be trusted
    going forward; the caller replaces it with a fresh ``Book()``, since a
    plain object cannot rebind its caller's reference)."""
    if not list((ob_dir / f"date={day}").glob("*.parquet")):
        return {"status": "no_raw", "reason": "", "n_breaks": 0, "n_snapshots": 0,
                "reset_book": False}
    n_breaks = 0
    n_snaps = 0
    any_sample = False
    for ts, rec, _u in _day_records(con, ob_dir, day):
        rtype, b, a, u = _rec_parts(rec)
        if rtype == "snapshot":
            n_snaps += 1
            if book.valid and not book.matches_snapshot(b, a):
                n_breaks += 1
            book.apply_snapshot(b, a, u)
        elif rtype == "delta":
            if book.valid and not book.apply_delta(b, a, u):
                n_breaks += 1
        else:
            continue
        if book.valid and book.bids and book.asks:
            bid_key = max(book.bids, key=lambda p: float(p))
            ask_key = min(book.asks, key=lambda p: float(p))
            bb, bsz = float(bid_key), book.bids[bid_key]
            aa, asz = float(ask_key), book.asks[ask_key]
            if bb > 0.0 and aa >= bb * 0.5 and aa > 0.0:
                ts_a.append(ts)
                bid_px_a.append(bb)
                bid_sz_a.append(bsz)
                ask_px_a.append(aa)
                ask_sz_a.append(asz)
                any_sample = True
    if n_breaks > max_breaks:
        return {"status": "discarded", "reason": f"{n_breaks} sequence breaks > {max_breaks}",
                "n_breaks": n_breaks, "n_snapshots": n_snaps, "reset_book": True}
    if n_snaps == 0 and not any_sample:
        return {"status": "discarded", "reason": "no snapshot and no valid state",
                "n_breaks": n_breaks, "n_snapshots": n_snaps, "reset_book": False}
    return {"status": "ok", "reason": "", "n_breaks": n_breaks, "n_snapshots": n_snaps,
            "reset_book": False}


def _replay_touch_samples(
    con: Any, ob_dir: Path, days: list[str], *, max_breaks: int,
) -> tuple[dict[str, dict[str, Any]], list[int], list[float], list[float], list[float], list[float]]:
    """One continuous pass (book carries across days, exactly the WP-2/WP-4
    discipline). Returns ``(day_meta, ts, bid_px, bid_sz, ask_px, ask_sz)``
    -- five parallel arrays, one entry per orderbook record where the book
    was valid with both sides non-empty (used for BOTH the quote's own
    side and, via mid, the adverse-selection lookup).

    Kept ONLY as the whole-window (non-streaming, non-resumable)
    reference path -- ``_run_window_full_replay`` below uses it, and
    nothing else does; ``run_window`` itself is the streaming driver."""
    book = Book()
    ts_a: list[int] = []
    bid_px_a: list[float] = []
    bid_sz_a: list[float] = []
    ask_px_a: list[float] = []
    ask_sz_a: list[float] = []
    day_meta: dict[str, dict[str, Any]] = {}

    for day in days:
        meta = _replay_one_day(con, ob_dir, day, book, ts_a=ts_a, bid_px_a=bid_px_a,
                               bid_sz_a=bid_sz_a, ask_px_a=ask_px_a, ask_sz_a=ask_sz_a,
                               max_breaks=max_breaks)
        if meta.pop("reset_book", False):
            book = Book()
        day_meta[day] = meta
    return day_meta, ts_a, bid_px_a, bid_sz_a, ask_px_a, ask_sz_a


# ----------------------------------------------------------------------------
# quote placement + evaluation
# ----------------------------------------------------------------------------

def _place_and_evaluate_day(
    day: str, *, ts_a: list[int], bid_px_a: list[float], bid_sz_a: list[float],
    ask_px_a: list[float], ask_sz_a: list[float],
    trades: list[tuple[int, str, float, float]], trade_ts: list[int],
    horizon_s: float, adv_sel_horizon_s: float, quote_size_fraction: float,
) -> dict[str, list[Any]]:
    """Place + evaluate one bid and one ask quote at every minute boundary
    of ``day``. Returns column arrays ready for ``FILLSHADOW_COLUMNS``."""
    out: dict[str, list[Any]] = {c: [] for c in FILLSHADOW_COLUMNS}
    if not ts_a:
        return out
    day_ms0 = _day_ms(day)
    data_end_ms = ts_a[-1]
    horizon_ms = int(round(horizon_s * 1000))
    lookahead_ms = horizon_ms + int(round(adv_sel_horizon_s * 1000))

    for minute in range(1440):
        boundary = day_ms0 + minute * MS_PER_MINUTE
        idx0 = bisect.bisect_right(ts_a, boundary) - 1
        if idx0 < 0:
            continue  # book not valid yet at this boundary
        t_end = boundary + horizon_ms
        idx_hi = bisect.bisect_right(ts_a, t_end)
        insufficient = data_end_ms < boundary + lookahead_ms

        # mids shared by both sides: (ts, mid) from the same touch samples
        mid_slice = [(ts_a[i], 0.5 * (bid_px_a[i] + ask_px_a[i]))
                    for i in range(idx0, min(idx_hi + 1, len(ts_a)))]

        t_lo = bisect.bisect_right(trade_ts, boundary)  # trades strictly after boundary
        t_hi = bisect.bisect_right(trade_ts, t_end)
        trade_slice = trades[t_lo:t_hi]

        for side, px_a, sz_a in (("buy", bid_px_a, bid_sz_a), ("sell", ask_px_a, ask_sz_a)):
            price = px_a[idx0]
            pos0 = sz_a[idx0]
            size = pos0 * quote_size_fraction
            if size <= 0.0:
                continue
            book_levels = [(boundary, pos0, price)]
            for i in range(idx0 + 1, min(idx_hi + 1, len(ts_a))):
                book_levels.append((ts_a[i], sz_a[i], px_a[i]))
            outcome = qm.simulate_quote(
                book_levels, trade_slice, mid_slice, t0_ms=boundary, side=side,
                price=price, size=size, horizon_s=horizon_s,
                adv_sel_horizon_s=adv_sel_horizon_s,
            )
            out["minute_idx"].append(minute + (day_ms0 // MS_PER_MINUTE))
            out["side"].append(side)
            out["price"].append(price)
            out["size"].append(size)
            out["position0"].append(pos0)
            out["fifo_filled"].append(outcome["fifo"]["filled"])
            out["fifo_fill_time_ms"].append(outcome["fifo"]["fill_time_ms"])
            out["fifo_latency_s"].append(outcome["fifo"]["latency_s"])
            out["fifo_adv_sel_bp"].append(outcome["fifo"]["adv_sel_bp"])
            out["prorata_filled"].append(outcome["prorata"]["filled"])
            out["prorata_fill_time_ms"].append(outcome["prorata"]["fill_time_ms"])
            out["prorata_latency_s"].append(outcome["prorata"]["latency_s"])
            out["prorata_adv_sel_bp"].append(outcome["prorata"]["adv_sel_bp"])
            out["touch_moved_away"].append(outcome["touch_moved_away"])
            out["insufficient_forward_data"].append(insufficient)
    return out


def _rows_hash(out: dict[str, list[Any]]) -> str:
    h = hashlib.sha256()
    for col in FILLSHADOW_COLUMNS:
        h.update(col.encode("ascii"))
        h.update(json.dumps(out[col], default=str, sort_keys=False).encode("utf-8"))
    return h.hexdigest()


def _write_day(out_dir: Path, exchange: str, symbol: str, day: str,
               cols: dict[str, list[Any]], *, status: str, reason: str,
               n_breaks: int, n_snapshots: int, horizon_s: float,
               adv_sel_horizon_s: float, quote_size_fraction: float) -> dict[str, Any]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    part = (out_dir / "fillshadow_1min" / f"exchange={exchange}"
            / f"symbol={symbol}" / f"date={day}")
    part.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema_version": SCHEMA_VERSION, "kind": "fillshadow_1min",
        "exchange": exchange, "symbol": symbol, "date": day,
        "status": status, "reason": reason,
        "n_quotes": len(cols["minute_idx"]), "n_seq_breaks": n_breaks,
        "n_snapshots": n_snapshots, "horizon_s": horizon_s,
        "adv_sel_horizon_s": adv_sel_horizon_s,
        "quote_size_fraction": quote_size_fraction,
        "n_fifo_filled": int(sum(1 for v in cols["fifo_filled"] if v)),
        "n_prorata_filled": int(sum(1 for v in cols["prorata_filled"] if v)),
        "sha256_values": _rows_hash(cols),
    }
    if status == "ok" and cols["minute_idx"]:
        table = pa.table({
            "minute_idx": pa.array(cols["minute_idx"], pa.int64()),
            "side": pa.array(cols["side"], pa.string()),
            "price": pa.array(cols["price"], pa.float64()),
            "size": pa.array(cols["size"], pa.float64()),
            "position0": pa.array(cols["position0"], pa.float64()),
            "fifo_filled": pa.array(cols["fifo_filled"], pa.bool_()),
            "fifo_fill_time_ms": pa.array(cols["fifo_fill_time_ms"], pa.int64()),
            "fifo_latency_s": pa.array(cols["fifo_latency_s"], pa.float64()),
            "fifo_adv_sel_bp": pa.array(cols["fifo_adv_sel_bp"], pa.float64()),
            "prorata_filled": pa.array(cols["prorata_filled"], pa.bool_()),
            "prorata_fill_time_ms": pa.array(cols["prorata_fill_time_ms"], pa.int64()),
            "prorata_latency_s": pa.array(cols["prorata_latency_s"], pa.float64()),
            "prorata_adv_sel_bp": pa.array(cols["prorata_adv_sel_bp"], pa.float64()),
            "touch_moved_away": pa.array(cols["touch_moved_away"], pa.bool_()),
            "insufficient_forward_data": pa.array(cols["insufficient_forward_data"], pa.bool_()),
        })
        pq.write_table(table, part / "fillshadow.parquet")
    (part / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


# ----------------------------------------------------------------------------
# window driver -- legacy whole-window reference path (test-only)
# ----------------------------------------------------------------------------

def _run_window_full_replay(
    base_dir: Path | str, out_dir: Path | str, symbol: str, start: str, end: str,
    *, exchange: str = "bybit", orderbook_stream: str = "orderbook",
    trade_stream: str = "publicTrade", max_breaks: int = MAX_BREAKS_PER_DAY,
    horizon_s: float = qm.DEFAULT_HORIZON_S,
    adv_sel_horizon_s: float = qm.DEFAULT_ADV_SEL_HORIZON_S,
    quote_size_fraction: float = DEFAULT_QUOTE_SIZE_FRACTION,
    require_manifest_done: bool = True, progress: Any = None,
) -> dict[str, Any]:
    """PRE-STREAMING reference implementation of ``run_window``: replays
    the ENTIRE ``[start, end]`` window (all touch samples + all trades)
    into memory BEFORE evaluating or writing a single day. Kept ONLY so
    ``test_wp10_fillshadow.py`` can assert the streaming ``run_window``
    below produces byte-identical per-day output (``sha256_values``) and
    identical summary counts on a synthetic multi-day fixture -- never
    call this from production code (the whole point of the streaming
    rewrite is to avoid exactly this memory profile)."""
    import duckdb

    base, out = Path(base_dir), Path(out_dir)
    _refuse_harvest(out)
    ob_dir = base / "raw" / exchange / orderbook_stream / f"symbol={symbol}"
    trade_dir = base / "raw" / exchange / trade_stream / f"symbol={symbol}"
    if not ob_dir.is_dir():
        raise ReplayError(f"no orderbook stream at {ob_dir}")

    days = _days_between(start, end)
    done_ob: set[str] = set()
    done_tr: set[str] = set()
    if require_manifest_done:
        done_ob = manifest_done_days(base, exchange, orderbook_stream, symbol, start, end)
        done_tr = manifest_done_days(base, exchange, trade_stream, symbol, start, end)

    con = duckdb.connect()
    try:
        day_meta, ts_a, bid_px_a, bid_sz_a, ask_px_a, ask_sz_a = \
            _replay_touch_samples(con, ob_dir, days, max_breaks=max_breaks)
        trades = _load_trades(con, trade_dir, days)
    finally:
        con.close()
    trade_ts = [t[0] for t in trades]

    counts = {"ok": 0, "discarded": 0, "no_raw": 0, "not_manifest_done": 0}
    total_quotes = 0
    total_fifo_filled = 0
    total_prorata_filled = 0
    for day in days:
        meta = day_meta.get(day, {"status": "no_raw", "reason": "", "n_breaks": 0, "n_snapshots": 0})
        status, reason = meta["status"], meta.get("reason", "")
        if status == "ok" and require_manifest_done and not (day in done_ob and day in done_tr):
            status, reason = "not_manifest_done", (
                f"orderbook DONE={day in done_ob} publicTrade DONE={day in done_tr}")

        if status == "ok":
            cols = _place_and_evaluate_day(
                day, ts_a=ts_a, bid_px_a=bid_px_a, bid_sz_a=bid_sz_a,
                ask_px_a=ask_px_a, ask_sz_a=ask_sz_a, trades=trades,
                trade_ts=trade_ts, horizon_s=horizon_s,
                adv_sel_horizon_s=adv_sel_horizon_s,
                quote_size_fraction=quote_size_fraction,
            )
        else:
            cols = {c: [] for c in FILLSHADOW_COLUMNS}

        written = _write_day(
            out, exchange, symbol, day, cols, status=status, reason=reason,
            n_breaks=meta.get("n_breaks", 0), n_snapshots=meta.get("n_snapshots", 0),
            horizon_s=horizon_s, adv_sel_horizon_s=adv_sel_horizon_s,
            quote_size_fraction=quote_size_fraction,
        )
        counts[status if status in counts else "discarded"] = \
            counts.get(status if status in counts else "discarded", 0) + 1
        total_quotes += written["n_quotes"]
        total_fifo_filled += written["n_fifo_filled"]
        total_prorata_filled += written["n_prorata_filled"]
        if progress is not None:
            progress(symbol, {"day": day, "status": status, "n_quotes": written["n_quotes"]})

    return {
        "symbol": symbol, "exchange": exchange, "range": [start, end],
        "days_in_range": len(days), **counts,
        "n_quotes_total": total_quotes,
        "n_fifo_filled_total": total_fifo_filled,
        "n_prorata_filled_total": total_prorata_filled,
        "horizon_s": horizon_s, "adv_sel_horizon_s": adv_sel_horizon_s,
        "quote_size_fraction": quote_size_fraction,
    }


# ----------------------------------------------------------------------------
# window driver -- streaming + resumable
# ----------------------------------------------------------------------------

def _resumable_meta(part_dir: Path, *, schema_version: int, horizon_s: float,
                    adv_sel_horizon_s: float, quote_size_fraction: float) -> dict[str, Any] | None:
    """The stored ``manifest.json`` at ``part_dir`` when it represents a
    COMPLETE, parameter-matching WP-10(B) day partition that ``run_window``
    may trust instead of recomputing -- ``None`` when there is nothing (or
    nothing trustworthy) there, in which case the day is recomputed, never
    silently trusted half-written.

    Loud, never silent, on a PARAMETER mismatch: a partition written with
    different ``schema_version``/``horizon_s``/``adv_sel_horizon_s``/
    ``quote_size_fraction`` raises ``ReplayError`` naming the path and the
    differing parameter -- the user picks a different ``--out`` or passes
    ``--no-resume``, never a silent stale reuse.
    """
    meta_path = part_dir / "manifest.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None  # unreadable manifest -- treat as incomplete, recompute
    for name, want in (("schema_version", schema_version), ("horizon_s", horizon_s),
                       ("adv_sel_horizon_s", adv_sel_horizon_s),
                       ("quote_size_fraction", quote_size_fraction)):
        have = meta.get(name)
        if have != want:
            raise ReplayError(
                f"WP-10(B) partition at {part_dir} was written with {name}={have!r}, "
                f"this run requested {name}={want!r} -- refusing to silently reuse a "
                f"mismatched partition (pick a different --out or pass --no-resume).")
    if meta.get("status") == "ok" and meta.get("n_quotes", 0) > 0:
        pq_path = part_dir / "fillshadow.parquet"
        if not pq_path.is_file():
            return None  # manifest present, parquet missing -- corrupt/partial, recompute
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(pq_path).to_pydict()
        except Exception:
            return None  # unreadable parquet -- corrupt, recompute
        rows = {c: table.get(c, []) for c in FILLSHADOW_COLUMNS}
        if _rows_hash(rows) != meta.get("sha256_values"):
            return None  # content hash mismatch -- corrupt/partial, recompute
    return meta


def _trim_before(day: str, ts_a: list[int], bid_px_a: list[float], bid_sz_a: list[float],
                 ask_px_a: list[float], ask_sz_a: list[float],
                 trades: list[tuple[int, str, float, float]], trade_ts: list[int]) -> None:
    """Memory bound: drop touch samples / trades older than the START of
    ``day`` (the day JUST written) from the rolling buffers, in place.
    ``day``'s own samples (>= its start) are kept as the ANCHOR the next
    day's minute-0 boundary lookup needs (the book's state carries across
    the midnight boundary without a fresh sample exactly AT midnight) --
    only samples strictly before that are provably never looked up again."""
    cutoff = _day_ms(day)
    i = bisect.bisect_left(ts_a, cutoff)
    if i > 0:
        del ts_a[:i]
        del bid_px_a[:i]
        del bid_sz_a[:i]
        del ask_px_a[:i]
        del ask_sz_a[:i]
    j = bisect.bisect_left(trade_ts, cutoff)
    if j > 0:
        del trades[:j]
        del trade_ts[:j]


def run_window(
    base_dir: Path | str, out_dir: Path | str, symbol: str, start: str, end: str,
    *, exchange: str = "bybit", orderbook_stream: str = "orderbook",
    trade_stream: str = "publicTrade", max_breaks: int = MAX_BREAKS_PER_DAY,
    horizon_s: float = qm.DEFAULT_HORIZON_S,
    adv_sel_horizon_s: float = qm.DEFAULT_ADV_SEL_HORIZON_S,
    quote_size_fraction: float = DEFAULT_QUOTE_SIZE_FRACTION,
    require_manifest_done: bool = True, resume: bool = True, progress: Any = None,
) -> dict[str, Any]:
    """One deterministic STREAMING pass over ``[start, end]``: the book
    still replays continuously day by day (WP-2/WP-4 machinery, same
    discipline -- state carries across days exactly as before), but day
    ``D`` is evaluated and WRITTEN as soon as the touch samples and trades
    covering ``D`` plus the forward lookahead (``horizon_s +
    adv_sel_horizon_s`` seconds into ``D+1``) have been replayed -- never
    the whole 80+-day window at once. The rolling sample/trade buffers are
    then trimmed to drop everything older than ``D``'s start (see
    ``_trim_before``), so peak memory is bounded by roughly one day's
    worth of L2 records, not the whole window's.

    Per-day output (columns, ``sha256_values``, every ``manifest.json``
    field) is BYTE-IDENTICAL to the old whole-window replay
    (``_run_window_full_replay``, pinned by
    ``test_replay_streaming_matches_full_replay_identity``) -- streaming
    changes ONLY memory/latency, never a single value.

    **Resume** (default ON; ``resume=False`` / CLI ``--no-resume`` forces
    full recomputation). Before evaluating day ``D``, if its output
    partition already holds a COMPLETE, parameter-matching result (see
    ``_resumable_meta``: manifest present with matching
    ``schema_version``/``horizon_s``/``adv_sel_horizon_s``/
    ``quote_size_fraction``, and -- for an "ok" day with quotes -- a
    parquet file whose ``sha256_values`` matches the manifest), that day
    is SKIPPED entirely (never replayed, counted ``resumed``) -- this is
    what makes resuming after a crash/reboot cheap: an already-written
    prefix of the window is never re-read from raw L2 at all. A manifest
    whose PARAMETERS differ from this run's raises ``ReplayError`` loudly
    (never a silent stale reuse); a manifest whose parquet is missing or
    hash-mismatched (partial/corrupt write) is treated as absent and
    recomputed.

    Skipping a day's replay means the continuously-carried book is no
    longer warm when the run resumes proper evaluation. Rather than
    replaying the whole skipped prefix (which would defeat the point of
    resuming), the run replays ONLY the single calendar day immediately
    before the first day it must actually evaluate, silently (no write,
    not counted) -- book state resyncs off that day's own snapshot(s), the
    same way it would at the cold start of any window, so by the
    following midnight the book is in the state an uninterrupted run
    would have reached. This is an approximation, not a proof, for the
    adversarial case where that warm-up day's own break budget would have
    been judged differently with the TRUE prior history than with a fresh
    ``Book()`` -- accepted here because it only ever affects whether that
    ALREADY-DISCARDED-OR-KEPT warm-up day's book gets reset, never the
    already-written days before it or the values this run itself writes.

    A day is ELIGIBLE for quote placement only when its L2 replay is
    "ok" (break budget respected, first snapshot seen) AND -- when
    ``require_manifest_done`` -- the harvest manifest marks BOTH the
    orderbook and publicTrade partitions DONE for that day. Ineligible
    days get an explicit ``status`` in their manifest and zero quotes;
    never silently skipped.

    ``progress(symbol, event)`` (when given) is called: once at the very
    start with ``{"kind": "start", "days_total": N}``; once after any
    silent warm-up replay with ``{"kind": "warmup", "day": ..., ...}``;
    and once per day (resumed or evaluated) with ``{"kind": "day", "day",
    "status", "n_quotes", "resumed", "elapsed_s"}``.
    """
    import duckdb

    base, out = Path(base_dir), Path(out_dir)
    _refuse_harvest(out)
    ob_dir = base / "raw" / exchange / orderbook_stream / f"symbol={symbol}"
    trade_dir = base / "raw" / exchange / trade_stream / f"symbol={symbol}"
    if not ob_dir.is_dir():
        raise ReplayError(f"no orderbook stream at {ob_dir}")

    days = _days_between(start, end)
    done_ob: set[str] = set()
    done_tr: set[str] = set()
    if require_manifest_done:
        done_ob = manifest_done_days(base, exchange, orderbook_stream, symbol, start, end)
        done_tr = manifest_done_days(base, exchange, trade_stream, symbol, start, end)

    lookahead_ms = int(round(horizon_s * 1000)) + int(round(adv_sel_horizon_s * 1000))
    part_root = out / "fillshadow_1min" / f"exchange={exchange}" / f"symbol={symbol}"

    t0 = time.time()
    if progress is not None:
        progress(symbol, {"kind": "start", "days_total": len(days)})

    counts = {"ok": 0, "discarded": 0, "no_raw": 0, "not_manifest_done": 0, "resumed": 0}
    total_quotes = 0
    total_fifo_filled = 0
    total_prorata_filled = 0

    con = duckdb.connect()
    try:
        book = Book()
        ts_a: list[int] = []
        bid_px_a: list[float] = []
        bid_sz_a: list[float] = []
        ask_px_a: list[float] = []
        ask_sz_a: list[float] = []
        trades: list[tuple[int, str, float, float]] = []
        trade_ts: list[int] = []
        day_meta: dict[str, dict[str, Any]] = {}
        rp_idx = 0  # index into `days` of the next day whose raw records are unreplayed

        def _replay_day_into_buffers(d: str) -> dict[str, Any]:
            nonlocal book
            meta = _replay_one_day(con, ob_dir, d, book, ts_a=ts_a, bid_px_a=bid_px_a,
                                   bid_sz_a=bid_sz_a, ask_px_a=ask_px_a, ask_sz_a=ask_sz_a,
                                   max_breaks=max_breaks)
            if meta.pop("reset_book", False):
                book = Book()
            day_trades = _load_trades_for_day(con, trade_dir, d)
            trades.extend(day_trades)
            trade_ts.extend(t[0] for t in day_trades)
            return meta

        def _ensure_replayed(upto_idx: int) -> None:
            nonlocal rp_idx
            while rp_idx <= upto_idx and rp_idx < len(days):
                day_meta[days[rp_idx]] = _replay_day_into_buffers(days[rp_idx])
                rp_idx += 1

        prev_skipped = False
        for di, day in enumerate(days):
            if resume:
                part_dir = part_root / f"date={day}"
                resumed_meta = _resumable_meta(
                    part_dir, schema_version=SCHEMA_VERSION, horizon_s=horizon_s,
                    adv_sel_horizon_s=adv_sel_horizon_s, quote_size_fraction=quote_size_fraction)
                if resumed_meta is not None:
                    counts["resumed"] += 1
                    prev_skipped = True
                    if progress is not None:
                        progress(symbol, {"kind": "day", "day": day, "status": "resumed",
                                          "n_quotes": resumed_meta.get("n_quotes", 0),
                                          "resumed": True,
                                          "elapsed_s": round(time.time() - t0, 1)})
                    continue

            if prev_skipped:
                warm_up_idx = di - 1
                if warm_up_idx >= rp_idx:  # not yet replayed via an earlier day's lookahead
                    _replay_day_into_buffers(days[warm_up_idx])  # silent: no write, not counted
                rp_idx = max(rp_idx, di)
                prev_skipped = False
                if progress is not None:
                    progress(symbol, {"kind": "warmup", "day": days[warm_up_idx],
                                      "elapsed_s": round(time.time() - t0, 1)})

            _ensure_replayed(di)
            meta = day_meta[day]
            status, reason = meta["status"], meta.get("reason", "")
            if status == "ok" and require_manifest_done and not (day in done_ob and day in done_tr):
                status, reason = "not_manifest_done", (
                    f"orderbook DONE={day in done_ob} publicTrade DONE={day in done_tr}")

            if status == "ok":
                target_ms = _day_ms(day) + MS_PER_DAY + lookahead_ms
                while (not ts_a or ts_a[-1] < target_ms) and rp_idx < len(days):
                    day_meta[days[rp_idx]] = _replay_day_into_buffers(days[rp_idx])
                    rp_idx += 1
                cols = _place_and_evaluate_day(
                    day, ts_a=ts_a, bid_px_a=bid_px_a, bid_sz_a=bid_sz_a,
                    ask_px_a=ask_px_a, ask_sz_a=ask_sz_a, trades=trades,
                    trade_ts=trade_ts, horizon_s=horizon_s,
                    adv_sel_horizon_s=adv_sel_horizon_s,
                    quote_size_fraction=quote_size_fraction,
                )
            else:
                cols = {c: [] for c in FILLSHADOW_COLUMNS}

            written = _write_day(
                out, exchange, symbol, day, cols, status=status, reason=reason,
                n_breaks=meta.get("n_breaks", 0), n_snapshots=meta.get("n_snapshots", 0),
                horizon_s=horizon_s, adv_sel_horizon_s=adv_sel_horizon_s,
                quote_size_fraction=quote_size_fraction,
            )
            counts[status if status in counts else "discarded"] = \
                counts.get(status if status in counts else "discarded", 0) + 1
            total_quotes += written["n_quotes"]
            total_fifo_filled += written["n_fifo_filled"]
            total_prorata_filled += written["n_prorata_filled"]
            if progress is not None:
                progress(symbol, {"kind": "day", "day": day, "status": status,
                                  "n_quotes": written["n_quotes"], "resumed": False,
                                  "elapsed_s": round(time.time() - t0, 1)})

            _trim_before(day, ts_a, bid_px_a, bid_sz_a, ask_px_a, ask_sz_a, trades, trade_ts)
            day_meta.pop(day, None)
    finally:
        con.close()

    return {
        "symbol": symbol, "exchange": exchange, "range": [start, end],
        "days_in_range": len(days), **counts,
        "n_quotes_total": total_quotes,
        "n_fifo_filled_total": total_fifo_filled,
        "n_prorata_filled_total": total_prorata_filled,
        "horizon_s": horizon_s, "adv_sel_horizon_s": adv_sel_horizon_s,
        "quote_size_fraction": quote_size_fraction,
    }


# ----------------------------------------------------------------------------
# read + fingerprint
# ----------------------------------------------------------------------------

def load_daily_fillshadow(out_dir: Path | str, exchange: str, symbol: str,
                          start: str, end: str) -> list[dict[str, Any]]:
    """One dict per OK day: manifest fields + the quote rows as a pydict."""
    import pyarrow.parquet as pq

    out = Path(out_dir)
    rows: list[dict[str, Any]] = []
    for day in _days_between(start, end):
        part = (out / "fillshadow_1min" / f"exchange={exchange}"
                / f"symbol={symbol}" / f"date={day}")
        meta_path = part / "manifest.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "ok" or meta.get("n_quotes", 0) == 0:
            continue
        table = pq.read_table(part / "fillshadow.parquet").to_pydict()
        rows.append({"day": day, "manifest": meta, "quotes": table})
    return rows


def fillshadow_fingerprint(out_dir: Path | str, exchange: str, symbol: str,
                           start: str, end: str) -> dict[str, Any]:
    """SHA-256 over all OK days' exact value bytes (determinism duty)."""
    out = Path(out_dir)
    h = hashlib.sha256()
    n_days = n_quotes = 0
    for day in _days_between(start, end):
        part = (out / "fillshadow_1min" / f"exchange={exchange}"
                / f"symbol={symbol}" / f"date={day}")
        meta_path = part / "manifest.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "ok":
            continue
        h.update(day.encode("ascii"))
        h.update(meta["sha256_values"].encode("ascii"))
        n_days += 1
        n_quotes += int(meta.get("n_quotes", 0))
    return {"schema_version": SCHEMA_VERSION, "exchange": exchange, "symbol": symbol,
            "range": [start, end], "n_ok_days": n_days, "n_quotes": n_quotes,
            "sha256_values": h.hexdigest()}


__all__ = [
    "ReplayError", "SCHEMA_VERSION", "DEFAULT_QUOTE_SIZE_FRACTION",
    "FILLSHADOW_COLUMNS", "probe", "run_window", "load_daily_fillshadow",
    "fillshadow_fingerprint",
]
