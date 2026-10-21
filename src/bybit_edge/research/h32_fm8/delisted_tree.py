"""DEC-100: the ``panel_1d_delisted`` tree from the Data-Harvest backfill partitions and the Data-Harvest delisting register.

The union panel of the first build lacked 45 delisted linear USDT perps (survivorship bias of ~5 % of the symbols in W2).
Data-Harvest delivers (a) the register ``state/data_harvest_delisting_register_*.csv`` (symbol, category, contractType,
baseCoin, quoteCoin, settleCoin, launch_day, last_trading_day [, announcement_day]) and (b) backfill partitions of the
streams ``rest.kline1d`` and ``rest.fundingRateAll`` (one partition per day, ``symbol=ALL``, container schema with the
columns ``symbol`` and ``payload_json``: the Bybit API row as strings -- kline either positional ``[startTime, open, high,
low, close, volume, turnover]`` or, as the Data-Harvest REST partitions store it, NAMED ``{symbol, category, interval,
startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover}``; funding ``{symbol, fundingRate,
fundingRateTimestamp}``).  This module reads those partitions from a LOCAL
directory (the orchestrator loads them with the Harvest client; nothing here touches the network or ``data/harvest``) and
writes a tree in exactly the layout of ``wp7_universe.panel_store`` (``frozen/source=bybit/category=linear/symbol=S/year=Y/
part.parquet`` + ``panel_manifest.sqlite``) that replaces the old ``--delisted-base``, plus ``delisting_dates.json``
(``delist_date`` = ``last_trading_day``, ``source`` = ``data_harvest_register``).  ``panel_load.load_panel_union`` is used
UNCHANGED to read it.

Rules (no value is ever interpolated or filled):

  * symbol list: ``category == linear``, ``quoteCoin == USDT``, ``last_trading_day <= cut``;
  * the partial candle of the last trading day is kept as it is; rows after ``last_trading_day`` (a relisting under the same
    name) and rows before ``start_year`` are dropped and NAMED; a symbol without any usable row is ``NO_HISTORY`` (no
    parquet, a FAILED manifest row -- the same marker as ``delisted_panel``) and named;
  * funding per day exactly as ``panel_store.merge_funding_daily`` (settlements counted from the real timestamps); a symbol
    without any funding row keeps ``funding_n`` / ``funding_sum`` ``None`` (never 0) and is named;
  * ``expected_days`` = calendar days from the listing anchor (register ``launch_day`` by default, or the first observed
    candle) to ``last_trading_day``: a missing day makes the year PARTIAL (the union loader then needs ``--allow-partial``), a
    year without any row although days are expected is FAILED (``GAP_NO_ROWS``); every such partition is listed with its
    missing days in the report;
  * identical duplicate rows are counted, differing duplicates are a loud error.

``delisted_tree_fingerprint.json`` carries the sha256 of the register CSV, of every written parquet and of the whole tree;
the register is copied verbatim to ``delisting_register.csv`` (its sha256 is the pin ``data_fingerprints.delisting_register_sha256``
of the registration).  :func:`verify_tree` recomputes everything; the modes call :func:`observed_tree_fingerprints`.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from ..wp12_delisting import delisted_panel
from ..wp7_universe import bybit_rest, panel_store
from . import artifacts
from .errors import DelistedTreeError

__all__ = ["STREAM_KLINE", "STREAM_FUNDING", "REGISTER_COPY", "FINGERPRINT_FILE", "DELISTING_DATES_FILE", "MANIFEST_FILE",
           "read_register", "select_symbols", "read_klines", "read_funding", "build_tree", "tree_files", "tree_fingerprint",
           "verify_tree", "observed_tree_fingerprints", "REQUIRED_REGISTER_COLUMNS", "FINGERPRINT_SCHEMA"]

STREAM_KLINE = "rest.kline1d"
STREAM_FUNDING = "rest.fundingRateAll"
REGISTER_COPY = "delisting_register.csv"
FINGERPRINT_FILE = "delisted_tree_fingerprint.json"
DELISTING_DATES_FILE = "delisting_dates.json"
MANIFEST_FILE = "panel_manifest.sqlite"
FINGERPRINT_SCHEMA = "H-32 delisted tree fingerprint (DEC-100)"
REQUIRED_REGISTER_COLUMNS = ("symbol", "category", "contractType", "baseCoin", "quoteCoin", "settleCoin", "launch_day",
                             "last_trading_day")
SOURCE_LABEL = "data_harvest_register"
GAP_REASON = "GAP_NO_ROWS"
LISTING_ANCHORS = ("register", "observed")
_DAY_MS = 86_400_000
_NOT_ATTRIBUTABLE = ("", "ALL", "all", None)
_MAX_LIST = 10


def _say(log: Callable[[str], None] | None, msg: str) -> None:
    if log is not None:
        log(msg)


def _day_of_ms(ms: int) -> date:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date()


def _iso(text: str, what: str) -> date:
    try:
        return date.fromisoformat(str(text).strip())
    except ValueError as exc:
        raise DelistedTreeError(f"{what}: {text!r} is not an ISO date") from exc


# ----------------------------------------------------------------------------
# register
# ----------------------------------------------------------------------------

def read_register(path: Path | str) -> list[dict[str, Any]]:
    """The Data-Harvest delisting register as dicts (``launch`` / ``last`` parsed as dates, ``announcement_day`` kept as a
    label if the column exists and is filled).  Missing columns, unparsable dates, ``last < launch`` and duplicate symbols are
    loud errors."""
    p = Path(path)
    artifacts.refuse_unsafe_path(p)
    if not p.is_file():
        raise DelistedTreeError(f"register {p} not found")
    with p.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip() for h in (reader.fieldnames or [])]
        miss = [c for c in REQUIRED_REGISTER_COLUMNS if c not in header]
        if miss:
            raise DelistedTreeError(f"register {p.name}: columns missing: {miss}")
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for i, raw in enumerate(reader, start=2):
            r = {k.strip(): (v or "").strip() for k, v in raw.items() if k is not None}
            if not r["symbol"]:
                raise DelistedTreeError(f"register {p.name} line {i}: empty symbol")
            if r["symbol"] in seen:
                raise DelistedTreeError(f"register {p.name}: symbol {r['symbol']} twice")
            seen.add(r["symbol"])
            r["launch"] = _iso(r["launch_day"], f"register {p.name} line {i} launch_day")
            r["last"] = _iso(r["last_trading_day"], f"register {p.name} line {i} last_trading_day")
            if r["last"] < r["launch"]:
                raise DelistedTreeError(f"register {p.name}: {r['symbol']} last_trading_day {r['last']} before launch_day {r['launch']}")
            r["announcement_day"] = r.get("announcement_day") or None
            rows.append(r)
    if not rows:
        raise DelistedTreeError(f"register {p.name} holds no rows")
    return rows


def select_symbols(rows: list[dict[str, Any]], cut: str) -> list[dict[str, Any]]:
    """``category == linear``, ``quoteCoin == USDT``, ``last_trading_day <= cut`` (sorted by symbol)."""
    cut_d = _iso(cut, "cut")
    return sorted((r for r in rows if r["category"] == "linear" and r["quoteCoin"] == "USDT" and r["last"] <= cut_d),
                  key=lambda r: r["symbol"])


# ----------------------------------------------------------------------------
# reading the Kestrel partitions
# ----------------------------------------------------------------------------

def _stream_files(root: Path | str, stream: str) -> list[Path]:
    """Every ``*.parquet`` whose path has a directory called ``stream`` (or ``stream=<stream>``) below ``root`` -- or ``root``
    itself is called so (the Harvest layout ``<exchange>/<stream>/symbol=ALL/date=<d>/*.parquet``)."""
    r = Path(root)
    artifacts.refuse_unsafe_path(r)
    if not r.is_dir():
        raise DelistedTreeError(f"partitions directory {r} not found")
    files = sorted(f for f in r.rglob("*.parquet") if stream in f.parts or f"stream={stream}" in f.parts)
    if not files:
        raise DelistedTreeError(f"no partitions of the stream {stream} below {r}")
    return files


def _read_symbol_payload(path: Path) -> list[tuple[str | None, str]]:
    import pyarrow.parquet as pq
    try:
        table = pq.read_table(path, columns=["symbol", "payload_json"])
    except Exception as exc:                                       # noqa: BLE001 -- pyarrow raises several types
        raise DelistedTreeError(f"{path}: cannot read the columns symbol / payload_json ({exc})") from exc
    cols = table.to_pydict()
    return list(zip(cols["symbol"], cols["payload_json"]))


#: NAMED kline fields of the Data-Harvest REST partitions (``bybit/rest.kline1d``), in the positional order of
#: ``bybit_rest.KLINE_ROW_FIELDS`` ([sek] Bybit v5 ``GET /v5/market/kline`` field semantics; the partition writer names them).
KLINE_NAMED_FIELDS: tuple[str, ...] = ("startTime", "openPrice", "highPrice", "lowPrice", "closePrice", "volume", "turnover")


def _kline_payload_as_row(obj: Any, sym: str | None, path: Path) -> list[Any]:
    """A kline payload as the positional row ``parse_kline_rows`` expects: a list is passed through; a dict with the NAMED
    fields is reordered (its ``symbol`` field, when present, must equal the column symbol -- loud otherwise)."""
    if isinstance(obj, dict):
        name = obj.get("symbol")
        if name not in (None, "") and name != sym:
            raise DelistedTreeError(f"{path}: kline row of column symbol {sym} carries the payload symbol {name}")
        missing = [f for f in KLINE_NAMED_FIELDS if f not in obj]
        if missing:
            raise DelistedTreeError(f"{path}: kline row of {sym} lacks the named fields {missing}")
        return [obj[f] for f in KLINE_NAMED_FIELDS]
    return obj


def read_klines(root: Path | str, wanted: Iterable[str]) -> tuple[dict[str, dict[int, dict[str, Any]]], dict[str, Any]]:
    """``{symbol: {start_ms: {start_ms, open, high, low, close, volume, turnover}}}`` of the ``wanted`` symbols from the
    ``rest.kline1d`` partitions below ``root``, plus read statistics.  Rows of other symbols are only counted."""
    want = set(wanted)
    files = _stream_files(root, STREAM_KLINE)
    out: dict[str, dict[int, dict[str, Any]]] = {}
    skipped: Counter[str] = Counter()
    n_rows = n_dup = 0
    conflicts: list[str] = []
    for path in files:
        for sym, payload in _read_symbol_payload(path):
            n_rows += 1
            if sym in _NOT_ATTRIBUTABLE:
                raise DelistedTreeError(f"{path}: a kline row carries symbol {sym!r} -- not attributable to a contract")
            if sym not in want:
                skipped[sym] += 1
                continue
            try:
                rec = bybit_rest.parse_kline_rows([_kline_payload_as_row(json.loads(payload), sym, path)])[0]
            except (json.JSONDecodeError, TypeError, bybit_rest.BybitFieldLayoutError) as exc:
                raise DelistedTreeError(f"{path}: kline row of {sym} does not follow the Bybit layout ({exc})") from exc
            if rec["start_ms"] % _DAY_MS != 0:
                raise DelistedTreeError(f"{path}: kline row of {sym} starts at {rec['start_ms']}, not at a UTC day boundary")
            have = out.setdefault(sym, {}).get(rec["start_ms"])
            if have is None:
                out[sym][rec["start_ms"]] = rec
            elif have == rec:
                n_dup += 1
            else:
                conflicts.append(f"{sym}@{_day_of_ms(rec['start_ms']).isoformat()}")
    if conflicts:
        raise DelistedTreeError(f"{len(conflicts)} kline row(s) occur twice with DIFFERENT values: {conflicts[:_MAX_LIST]}")
    return out, {"n_files": len(files), "n_rows": n_rows, "n_identical_duplicates": n_dup,
                 "skipped_symbols": {k: int(v) for k, v in sorted(skipped.items())}, "files": files}


def read_funding(root: Path | str, wanted: Iterable[str]) -> tuple[dict[str, dict[int, float]], dict[str, Any]]:
    """``{symbol: {ts_ms: funding_rate}}`` of the ``wanted`` symbols from the ``rest.fundingRateAll`` partitions below
    ``root`` (the symbol of a row is its ``symbol`` column; a row whose column is ``ALL`` / empty takes the symbol of its
    payload; both given and different is an error), plus read statistics."""
    want = set(wanted)
    files = _stream_files(root, STREAM_FUNDING)
    out: dict[str, dict[int, float]] = {}
    skipped: Counter[str] = Counter()
    n_rows = n_dup = 0
    conflicts: list[str] = []
    for path in files:
        for sym, payload in _read_symbol_payload(path):
            n_rows += 1
            if sym not in _NOT_ATTRIBUTABLE and sym not in want:
                skipped[sym] += 1
                continue
            try:
                rec = bybit_rest.parse_funding_rows([json.loads(payload)])[0]
            except (json.JSONDecodeError, TypeError, bybit_rest.BybitFieldLayoutError) as exc:
                raise DelistedTreeError(f"{path}: funding row does not follow the Bybit layout ({exc})") from exc
            name = rec["symbol"]
            if sym in _NOT_ATTRIBUTABLE:
                sym = name
            elif name not in (None, sym):
                raise DelistedTreeError(f"{path}: funding row of column symbol {sym} carries the payload symbol {name}")
            if sym in _NOT_ATTRIBUTABLE:
                raise DelistedTreeError(f"{path}: a funding row names no symbol (neither column nor payload)")
            if sym not in want:
                skipped[sym] += 1
                continue
            have = out.setdefault(sym, {}).get(rec["ts_ms"])
            if have is None:
                out[sym][rec["ts_ms"]] = rec["funding_rate"]
            elif have == rec["funding_rate"]:
                n_dup += 1
            else:
                conflicts.append(f"{sym}@{rec['ts_ms']}")
    if conflicts:
        raise DelistedTreeError(f"{len(conflicts)} funding row(s) occur twice with DIFFERENT rates: {conflicts[:_MAX_LIST]}")
    return out, {"n_files": len(files), "n_rows": n_rows, "n_identical_duplicates": n_dup,
                 "skipped_symbols": {k: int(v) for k, v in sorted(skipped.items())}, "files": files}


def _inputs_fingerprint(files: list[Path], root: Path) -> dict[str, Any]:
    h = hashlib.sha256()
    for f in sorted(files):
        try:
            rel = f.relative_to(root).as_posix()
        except ValueError:
            rel = f.as_posix()
        h.update(f"{rel}:{artifacts.sha256_file(f)}\n".encode("utf-8"))
    return {"n_files": len(files), "files_sha256": h.hexdigest()}


# ----------------------------------------------------------------------------
# fingerprints
# ----------------------------------------------------------------------------

def tree_files(base: Path | str) -> dict[str, str]:
    """``{relative posix path: sha256}`` of every ``part.parquet`` below ``base``."""
    b = Path(base)
    return {p.relative_to(b).as_posix(): artifacts.sha256_file(p) for p in sorted(b.rglob("part.parquet"))}


def tree_fingerprint(base: Path | str) -> dict[str, Any]:
    """sha256 over the register copy and every written parquet (path and file hash, sorted)."""
    b = Path(base)
    reg = b / REGISTER_COPY
    if not reg.is_file():
        raise DelistedTreeError(f"{b}: no {REGISTER_COPY} (not a tree built by h32_build_delisted_tree)")
    files = tree_files(b)
    reg_sha = artifacts.sha256_file(reg)
    h = hashlib.sha256()
    h.update(f"register:{reg_sha}".encode("ascii"))
    for rel in sorted(files):
        h.update(f"\n{rel}:{files[rel]}".encode("utf-8"))
    return {"register_sha256": reg_sha, "tree_sha256": h.hexdigest(), "files": files}


def verify_tree(base: Path | str) -> dict[str, Any]:
    """Recompute the fingerprint of the tree on disk and compare it with ``delisted_tree_fingerprint.json``: register copy,
    set of parquet files and every file hash.  A difference is :class:`DelistedTreeError`."""
    b = Path(base)
    fp_path = b / FINGERPRINT_FILE
    if not fp_path.is_file():
        raise DelistedTreeError(f"{b}: no {FINGERPRINT_FILE}")
    stored = json.loads(fp_path.read_text(encoding="utf-8"))
    if stored.get("schema") != FINGERPRINT_SCHEMA:
        raise DelistedTreeError(f"{fp_path.name}: unknown schema {stored.get('schema')!r}")
    now = tree_fingerprint(b)
    problems: list[str] = []
    if now["register_sha256"] != stored["register"]["sha256"]:
        problems.append("register copy differs")
    old_files = stored["files"]
    for rel in sorted(set(old_files) | set(now["files"])):
        if rel not in now["files"]:
            problems.append(f"missing: {rel}")
        elif rel not in old_files:
            problems.append(f"extra: {rel}")
        elif old_files[rel] != now["files"][rel]:
            problems.append(f"changed: {rel}")
    if now["tree_sha256"] != stored["tree_sha256"]:
        problems.append("tree_sha256 differs")
    if problems:
        raise DelistedTreeError(f"delisted tree {b} differs from its fingerprint file: {problems[:_MAX_LIST]}"
                                f"{' (+more)' if len(problems) > _MAX_LIST else ''}")
    return {"tree_sha256": now["tree_sha256"], "register_sha256": now["register_sha256"], "n_files": len(now["files"])}


def observed_tree_fingerprints(base: Path | str) -> dict[str, str | None]:
    """The two data fingerprints a mode quotes for the delisted tree: ``delisting_register_sha256`` (sha256 of the register
    copy; ``None`` without one) and ``delisted_tree_sha256`` (verified against the fingerprint file; ``None`` without one).
    A tree that differs from its fingerprint file is a loud :class:`DelistedTreeError`."""
    b = Path(base)
    reg = b / REGISTER_COPY
    out: dict[str, str | None] = {"delisting_register_sha256": artifacts.sha256_file(reg) if reg.is_file() else None,
                                  "delisted_tree_sha256": None}
    if (b / FINGERPRINT_FILE).is_file():
        out["delisted_tree_sha256"] = verify_tree(b)["tree_sha256"]
    return out


# ----------------------------------------------------------------------------
# build
# ----------------------------------------------------------------------------

def _expected_day_set(year: int, anchor: date, last: date) -> set[date]:
    lo, hi = max(date(year, 1, 1), anchor), min(date(year, 12, 31), last)
    return {lo + timedelta(days=i) for i in range((hi - lo).days + 1)} if hi >= lo else set()


def build_tree(register_path: Path | str, partitions_dir: Path | str, out_dir: Path | str, *, cut: str,
               start_year: int = delisted_panel.DEFAULT_START_YEAR, listing_anchor: str = "register",
               log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Build the delisted tree below ``out_dir`` (must not exist or be empty) from the register and the partitions below
    ``partitions_dir``; returns the report (also written as ``delisted_tree_fingerprint.json`` together with the file hashes)."""
    if listing_anchor not in LISTING_ANCHORS:
        raise DelistedTreeError(f"listing_anchor must be one of {LISTING_ANCHORS}")
    out = Path(out_dir)
    artifacts.refuse_unsafe_path(out / "x", writing=True)
    if out.exists() and any(out.iterdir()):
        raise DelistedTreeError(f"{out} is not empty -- a tree is never overwritten (build into a new directory)")
    reg_rows = read_register(register_path)
    sel = select_symbols(reg_rows, cut)
    if not sel:
        raise DelistedTreeError(f"no register row with category linear, quoteCoin USDT and last_trading_day <= {cut}")
    symbols = [r["symbol"] for r in sel]
    _say(log, f"register: {len(reg_rows)} rows, {len(sel)} selected (linear USDT, last_trading_day <= {cut})")
    pdir = Path(partitions_dir)
    klines, kstat = read_klines(pdir, symbols)
    funding, fstat = read_funding(pdir, symbols)
    _say(log, f"kline1d: {kstat['n_files']} files, {kstat['n_rows']} rows; fundingRateAll: {fstat['n_files']} files, {fstat['n_rows']} rows")

    out.mkdir(parents=True, exist_ok=True)
    manifest = out / MANIFEST_FILE
    entries: dict[str, dict[str, Any]] = {}
    no_history: dict[str, str] = {}
    funding_missing: list[str] = []
    dropped_after: dict[str, dict[str, Any]] = {}
    dropped_before: dict[str, int] = {}
    not_done: list[dict[str, Any]] = []
    first_last: dict[str, dict[str, str]] = {}
    n_partitions = 0
    for r in sel:
        sym, launch, last = r["symbol"], r["launch"], r["last"]
        entry = {"delist_date": last.isoformat(), "announcement_id": None, "source": SOURCE_LABEL,
                 "launch_day": launch.isoformat()}
        if r["announcement_day"]:
            entry["announcement_day"] = r["announcement_day"]
        entries[sym] = entry
        rows_all = sorted(klines.get(sym, {}).values(), key=lambda x: x["start_ms"])
        after = [x for x in rows_all if _day_of_ms(x["start_ms"]) > last]
        before = [x for x in rows_all if _day_of_ms(x["start_ms"]).year < start_year]
        within = [x for x in rows_all if _day_of_ms(x["start_ms"]).year >= start_year and _day_of_ms(x["start_ms"]) <= last]
        if after:
            dropped_after[sym] = {"n_rows": len(after), "first": _day_of_ms(after[0]["start_ms"]).isoformat(),
                                  "last": _day_of_ms(after[-1]["start_ms"]).isoformat()}
        if before:
            dropped_before[sym] = len(before)
        if not within:
            why = "no_api_rows" if not rows_all else "no_row_between_start_year_and_last_trading_day"
            no_history[sym] = why
            panel_store.mark_failed(manifest, sym, last.year, delisted_panel.NO_HISTORY_REASON)
            continue
        fund = [{"symbol": sym, "funding_rate": rate, "ts_ms": ts} for ts, rate in sorted(funding.get(sym, {}).items())
                if start_year <= _day_of_ms(ts).year and _day_of_ms(ts) <= last]
        if fund:
            within = panel_store.merge_funding_daily(within, fund)
        else:
            funding_missing.append(sym)
        first_obs = _day_of_ms(within[0]["start_ms"])
        anchor = launch if listing_anchor == "register" else first_obs
        first_last[sym] = {"first_candle": first_obs.isoformat(), "last_candle": _day_of_ms(within[-1]["start_ms"]).isoformat()}
        by_year: dict[int, list[dict[str, Any]]] = {}
        for x in within:
            by_year.setdefault(_day_of_ms(x["start_ms"]).year, []).append(x)
        for y in range(max(start_year, min(anchor.year, first_obs.year)), last.year + 1):
            expected = _expected_day_set(y, anchor, last)
            rows_y = by_year.get(y, [])
            if not rows_y:
                if expected:
                    panel_store.mark_failed(manifest, sym, y, GAP_REASON)
                    not_done.append({"symbol": sym, "year": y, "status": "FAILED", "reason": GAP_REASON, "n_rows": 0,
                                     "expected_days": len(expected), "missing_days": len(expected),
                                     "missing_head": [d.isoformat() for d in sorted(expected)[:_MAX_LIST]]})
                continue
            res = panel_store.write_year_partition(out, manifest, sym, y, rows_y, listing_date=anchor, as_of_date=last, frozen=True)
            n_partitions += 1
            if res["status"] != "DONE":
                seen = {_day_of_ms(x["start_ms"]) for x in rows_y}
                miss = sorted(expected - seen)
                not_done.append({"symbol": sym, "year": y, "status": res["status"], "n_rows": res["n_rows"],
                                 "expected_days": res["expected_days"], "missing_days": len(miss),
                                 "missing_head": [d.isoformat() for d in miss[:_MAX_LIST]],
                                 "extra_rows": len(seen - expected)})

    dd = delisted_panel.write_delisting_dates_json(out, entries)
    shutil.copyfile(register_path, out / REGISTER_COPY)
    fp = tree_fingerprint(out)
    counts = panel_store.manifest_status_counts(manifest)
    report: dict[str, Any] = {
        "schema": FINGERPRINT_SCHEMA,
        "register": {"file": REGISTER_COPY, "sha256": fp["register_sha256"], "n_rows": len(reg_rows), "n_selected": len(sel)},
        "selection": {"category": "linear", "quoteCoin": "USDT", "last_trading_day_max": cut, "start_year": int(start_year),
                      "listing_anchor": listing_anchor},
        "tree_sha256": fp["tree_sha256"], "files": fp["files"], "delisting_dates": dd,
        "n_symbols": len(sel), "n_symbols_with_history": len(sel) - len(no_history), "n_partitions": n_partitions,
        "status_counts": counts, "symbols": symbols,
        "no_history_symbols": dict(sorted(no_history.items())), "funding_missing_symbols": sorted(funding_missing),
        "dropped_after_last_trading_day": dict(sorted(dropped_after.items())),
        "dropped_before_start_year": dict(sorted(dropped_before.items())), "not_done_partitions": not_done,
        "first_last_candle": dict(sorted(first_last.items())),
        "inputs": {STREAM_KLINE: {**_inputs_fingerprint(kstat["files"], pdir), "n_rows": kstat["n_rows"],
                                  "n_identical_duplicates": kstat["n_identical_duplicates"]},
                   STREAM_FUNDING: {**_inputs_fingerprint(fstat["files"], pdir), "n_rows": fstat["n_rows"],
                                    "n_identical_duplicates": fstat["n_identical_duplicates"]}},
        "rows_of_symbols_not_in_the_selection": {STREAM_KLINE: sum(kstat["skipped_symbols"].values()),
                                                 STREAM_FUNDING: sum(fstat["skipped_symbols"].values())},
        "code": artifacts.code_fingerprint(),
    }
    artifacts.write_json(out / FINGERPRINT_FILE, report)
    return report
