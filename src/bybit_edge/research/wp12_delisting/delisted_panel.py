"""WP-12b -- ``panel_1d_delisted`` fetch: full daily kline (+ funding)
history for every delisted linear symbol in the delisting register, from
``--start-year`` (default 2021) through its delisting date.

Real run 2026-09-16 (task brief CONTEXT): the register holds 476
announcements / 268 distinct linear symbols; Bybit's public kline endpoint
still serves daily history for 261 of them -- PRD 4.1 B3 ("kein
Survivorship-freies Universum aus Bybit-Bordmitteln") is pre-fixed as "not
buildable" and this real evidence contradicts that (DEC-70, see
``scinance3-impl/state/decisions.md`` -- as of this build, still pending
the Orchestrator's append; this module and its caller carry the
substance of that finding regardless, per the task brief CONTEXT block).

Writes a tree laid out EXACTLY like ``wp7_universe.panel_store``'s
``panel_1d`` (``frozen/source=bybit/category=linear/symbol=<S>/year=<YYYY>/
part.parquet`` + its own ``panel_manifest.sqlite``) but rooted at a
SEPARATE base directory (``data/panel_1d_delisted/`` by convention) --
NEVER into ``data/panel_1d/`` (a delisted symbol must never collide with a
live WP-7 panel symbol; ``wp7_universe.panel_load.load_panel_union`` loud-
fails if it ever finds the same symbol in both trees). Every function here
reuses ``panel_store``'s on-disk primitives UNCHANGED (partition layout,
manifest, resume, DONE/PARTIAL/EMPTY arithmetic, frozen-immutability) --
this module adds no new storage format of its own.

**Delisting date convention (task brief item 1, verbatim):** ``delist_ms``
= the register's parsed ``delisting_ms`` if present, else the
announcement's ``publish_ms`` -- the SAME fallback
``kline_probe.reference_ms_for_symbol`` already uses (reused here, not
reimplemented) for the WP-12 kline-availability probe.

**Frozen-year / expected_days_in_year convention (task brief item 1):**
a delisted symbol never has an "open" (in-progress) year -- it is dead,
every year of its history is written to ``frozen/`` (``frozen=True``
always). ``as_of_date=delist_date`` for EVERY year of the symbol's history
(not just its delisting year): ``panel_store.expected_days_in_year``
computes ``hi = min(Dec 31, as_of_date)``, so for a year strictly before
the delisting year this is identical to passing that year's own Dec 31
(``delist_date`` is always later) -- passing the SAME ``as_of_date``
uniformly is therefore both simpler and exactly equivalent to the
per-year-correct value, and gives the delisting year itself a complete
(``n_rows == expected_days``) history -> DONE, not PARTIAL, PROVIDED the
symbol really has an unbroken daily history through its delisting date.

**``listing_date``:** unlike WP-7's ``--fetch`` (which reads the real
``launchTime`` from ``instruments-info``), a long-delisted symbol is
usually gone from ``instruments-info`` entirely -- there is no live
``launchTime`` to read. This module anchors ``listing_date`` at the
EARLIEST OBSERVED kline day the fetch itself returns (a real, measured
value, never invented) -- documented here as the load-bearing convention
every ``expected_days_in_year`` call in this module relies on.

**``NO_HISTORY`` (task brief item 1):** a symbol whose full-range kline
fetch returns ZERO rows gets NO parquet partition; instead
``panel_store.mark_failed(manifest, symbol, delist_year, "NO_HISTORY")``
records it loudly, and it is named in ``fetch_delisted_panel``'s returned
summary (``no_history_symbols``) -- never silently dropped.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..wp7_universe import bybit_rest, panel_store
from . import kline_probe

__all__ = [
    "DEFAULT_START_YEAR", "NO_HISTORY_REASON",
    "dedup_delisted_symbols", "delist_date_for_symbol",
    "write_delisting_dates_json", "read_delisting_dates_json",
    "fetch_delisted_panel",
]

_EPOCH = date(1970, 1, 1)
_DAY_MS = 86_400_000

#: Task brief item 1: starting year for the full-history fetch unless
#: ``--start-year`` overrides it.
DEFAULT_START_YEAR = 2021

#: The exact ``mark_failed`` reason string for a symbol whose kline fetch
#: returned zero rows over its whole ``[start_year-01-01, delist_date]``
#: window -- named once here so the manifest, the log line and every test
#: that asserts on it use the SAME literal.
NO_HISTORY_REASON = "NO_HISTORY"


def dedup_delisted_symbols(register_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicated (by symbol) linear delisted symbols out of the
    register -- reuses ``kline_probe.delisted_linear_symbols`` UNCHANGED
    (same dedup rule: category==linear, USDT suffix, first occurrence
    wins) rather than re-deriving it."""
    return kline_probe.delisted_linear_symbols(register_rows)


def delist_date_for_symbol(entry: dict[str, Any]) -> date | None:
    """``delisting_ms`` if parsed, else ``publish_ms`` (the announcement
    date) -- task brief item 1, verbatim; reuses
    ``kline_probe.reference_ms_for_symbol`` (the SAME fallback rule the
    kline-availability probe already applies) rather than reimplementing
    it. ``None`` if the entry carries neither (never invented)."""
    ms = kline_probe.reference_ms_for_symbol(entry)
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date()


def _year_start_ms(year: int) -> int:
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def _end_of_day_ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000) + (_DAY_MS - 1)


def write_delisting_dates_json(
    base_dir: Path | str, delisting_dates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Write ``<base_dir>/delisting_dates.json`` -- ``{symbol: {delist_date,
    announcement_id, source}}`` -- with its own sha256 (task brief item 1:
    "symbol -> delist_date, source announcement id) with sha256"). Never
    under ``data/harvest``."""
    base_dir = Path(base_dir)
    if "data/harvest" in base_dir.as_posix():
        raise ValueError(f"refusing to write delisting_dates.json under data/harvest: {base_dir}")
    base_dir.mkdir(parents=True, exist_ok=True)
    payload = {"n_symbols": len(delisting_dates),
               "symbols": dict(sorted(delisting_dates.items()))}
    path = base_dir / "delisting_dates.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "sha256": sha, "n_symbols": len(delisting_dates)}


def read_delisting_dates_json(path: Path | str) -> dict[str, dict[str, Any]]:
    """Read back ``delisting_dates.json``'s ``symbols`` map (``{symbol:
    {delist_date, announcement_id, source}}``)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"delisting_dates.json not found at {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("symbols") or {}


def fetch_delisted_panel(
    register_rows: list[dict[str, Any]], *, base_dir: Path | str, manifest_path: Path | str,
    start_year: int = DEFAULT_START_YEAR, category: str = "linear",
) -> dict[str, Any]:
    """Fetch + write the full ``panel_1d_delisted`` tree (task brief item
    1), one deduplicated register symbol at a time.

    Resume discipline (``panel_store.resume_action``, identical to WP-7's
    ``--fetch``): a symbol whose ENTIRE year range already carries
    frozen DONE/EMPTY partitions is skipped WITHOUT a network call; a
    symbol needing at least one year written/rebuilt gets exactly ONE
    ``fetch_kline_symbol`` call (the full ``[start_year-01-01,
    delist_date]`` range in one paginated fetch, not one call per year --
    ``fetch_kline_symbol``/``fetch_funding_history`` already throttle
    internally at ``bybit_rest.MAX_REQ_PER_SEC``) plus one
    ``fetch_funding_history`` call, then the result is sliced into year
    partitions and only the non-SKIP years are (re)written.
    """
    base_dir = Path(base_dir)
    manifest_path = Path(manifest_path)
    if "data/harvest" in base_dir.as_posix():
        raise ValueError(f"refusing to write panel_1d_delisted under data/harvest: {base_dir}")

    entries = dedup_delisted_symbols(register_rows)
    delisting_dates: dict[str, dict[str, Any]] = {}
    no_history: list[str] = []
    skipped_no_reference: list[str] = []
    results: list[dict[str, Any]] = []
    n_fetched = 0
    n_skipped_resume = 0

    for entry in entries:
        symbol = entry["symbol"]
        delist_date = delist_date_for_symbol(entry)
        if delist_date is None:
            skipped_no_reference.append(symbol)
            continue
        delisting_dates[symbol] = {
            "delist_date": delist_date.isoformat(),
            "announcement_id": entry.get("announcement_id"),
            "source": "delisting_ms" if entry.get("delisting_ms") is not None else "publish_ms",
        }

        years = list(range(start_year, delist_date.year + 1))
        if not years:
            # delisted before the fetch window even starts -- nothing to
            # fetch, but the symbol is still named (never silently dropped).
            no_history.append(symbol)
            panel_store.mark_failed(manifest_path, symbol, start_year, NO_HISTORY_REASON)
            results.append({"symbol": symbol, "status": "BEFORE_START_YEAR", "years": []})
            continue

        actions = {y: panel_store.resume_action(base_dir, manifest_path, symbol, y, frozen=True)
                   for y in years}
        if all(act == "SKIP" for act in actions.values()):
            n_skipped_resume += 1
            results.append({"symbol": symbol, "status": "SKIP_RESUME", "years": years})
            continue

        start_ms = _year_start_ms(start_year)
        end_ms = _end_of_day_ms(delist_date)
        kl = bybit_rest.fetch_kline_symbol(symbol, start_ms, end_ms, category=category)
        rows_all = [{"start_ms": r["start_ms"], "open": r["open"], "high": r["high"],
                     "low": r["low"], "close": r["close"], "volume": r["volume"],
                     "turnover": r["turnover"]} for r in kl["rows"]]
        if not rows_all:
            no_history.append(symbol)
            panel_store.mark_failed(manifest_path, symbol, delist_date.year, NO_HISTORY_REASON)
            results.append({"symbol": symbol, "status": "NO_HISTORY", "years": years})
            continue

        try:
            fh = bybit_rest.fetch_funding_history(symbol, start_ms, end_ms, category=category)
            rows_all = panel_store.merge_funding_daily(rows_all, fh["rows"])
        except Exception as exc:  # noqa: BLE001 -- mirrors wp7 cmd_fetch: funding is best-effort
            print(f"{symbol}: FEHLER (funding/history) {exc} -- funding_n/funding_sum bleiben "
                  "None fuer diesen Lauf", flush=True)

        earliest_day = min(r["start_ms"] for r in rows_all) // _DAY_MS
        listing_date = _EPOCH + timedelta(days=earliest_day)

        by_year: dict[int, list[dict[str, Any]]] = {}
        for r in rows_all:
            y = (_EPOCH + timedelta(days=r["start_ms"] // _DAY_MS)).year
            by_year.setdefault(y, []).append(r)

        year_results = []
        for y in years:
            if actions[y] == "SKIP":
                continue
            res = panel_store.write_year_partition(
                base_dir, manifest_path, symbol, y, by_year.get(y, []),
                listing_date=listing_date, as_of_date=delist_date, frozen=True,
                allow_overwrite=(actions[y] == "REBUILD"))
            year_results.append(res)
        n_fetched += 1
        results.append({"symbol": symbol, "status": "FETCHED", "years": year_results,
                         "listing_date": listing_date.isoformat()})

    dd_art = write_delisting_dates_json(base_dir, delisting_dates)
    return {
        "n_symbols_register": len(entries),
        "n_fetched": n_fetched, "n_skipped_resume": n_skipped_resume,
        "n_no_history": len(no_history), "no_history_symbols": sorted(no_history),
        "n_skipped_no_reference_date": len(skipped_no_reference),
        "skipped_no_reference_symbols": sorted(skipped_no_reference),
        "delisting_dates_artifact": dd_art, "results": results,
    }
