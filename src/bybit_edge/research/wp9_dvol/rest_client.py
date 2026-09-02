"""WP-9 -- Deribit DVOL public REST client (KAPITALFREI, no keys).

Wraps ``public/get_volatility_index_data`` (Deribit's public volatility
index history, currency=BTC|ETH, resolution=1D). NO authentication, NO
order/account endpoints anywhere near this module.

SANDBOX NOTE: this build environment's egress proxy cannot reach
``api.deribit.com`` (nor ``www.deribit.com``) at all -- every function here
therefore takes an injectable ``fetcher`` callable (``dict -> bytes``, the
raw HTTP response body) so the parsing/pagination/hashing logic can be
built and tested completely offline against canned pages
(``fixture_fetcher``). ``_default_fetcher`` is the real network path; it is
correct by reading of Deribit's published API shape but has NEVER been
exercised against a live response in this sandbox. Do not attempt to run
it here -- run ``--probe`` on a machine with real network access first.

FIELD LAYOUT [sek]: per Deribit's public API docs, a
``get_volatility_index_data`` response is

    {"jsonrpc": "2.0", "result": {
        "data": [[timestamp_ms, open, high, low, close], ...],
        "continuation": <ms or null>}, ...}

i.e. ``result.data`` is a list of POSITIONAL 5-element arrays (NOT named
fields) in the fixed order ``(ts_ms, open, high, low, close)``. This is an
EXPECTATION carried over from documentation, not a fact verified against a
live response in this sandbox -- ``parse_rows`` below is the loud-fail
check: any row that is not exactly 5 numeric-castable elements raises
``DvolFieldLayoutError`` naming the row instead of silently guessing which
positions mean what. ``--probe`` (see ``scripts/wp9_dvol_backfill.py``)
prints the raw response head (300 chars) alongside the parsed fields on
every real run so a layout change is caught immediately, by a human, before
any backfill or cross-validation trusts the numbers.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

__all__ = [
    "DERIBIT_BASE_URL", "ENDPOINT", "ROW_FIELDS", "MAX_REQ_PER_SEC",
    "DvolFieldLayoutError", "unwrap_result", "parse_rows",
    "fetch_volatility_index", "probe_call", "fixture_fetcher",
    "rows_to_daily", "write_rest_parquet", "read_rest_parquet",
]

#: [sek] -- unverified in this sandbox (no egress to Deribit at all).
DERIBIT_BASE_URL = "https://www.deribit.com/api/v2"
ENDPOINT = "/public/get_volatility_index_data"

#: Positional field order of one ``result.data`` row -- [sek], see module
#: docstring. ``parse_rows`` is the loud-fail gate on this assumption.
ROW_FIELDS: tuple[str, ...] = ("ts_ms", "open", "high", "low", "close")

#: Spec section 3: "Drossel <= 5 Req/s".
MAX_REQ_PER_SEC = 5.0

_MS_PER_DAY = 86_400_000
_VALID_CURRENCIES = ("BTC", "ETH")


class DvolFieldLayoutError(RuntimeError):
    """Loud failure: a REST response does not match the [sek] field layout."""


def unwrap_result(body: Any) -> Any:
    """``result.data`` from a JSON-RPC body, tolerant of a couple of shapes.

    Accepts the real envelope ``{"result": {"data": [...]}}``; a bare
    ``{"data": [...]}`` (fixture convenience); and a body that already IS
    the data list (maximal fixture convenience). Anything else -> None, so
    the caller can distinguish "no more pages" (empty list) from
    "unrecognisable body" (None) -- unwrap alone never raises; the FIELD
    check (``parse_rows``) is where loud-fail happens, so pagination end
    detection (an empty page) is never mistaken for a layout error.
    """
    obj = body
    if isinstance(obj, dict):
        obj = obj.get("result", obj)
    if isinstance(obj, dict):
        obj = obj.get("data", obj)
    if isinstance(obj, list):
        return obj
    return None


def parse_rows(data: Any) -> list[dict[str, Any]]:
    """``result.data`` -> list of ``{ts_ms, open, high, low, close}``.

    Loud-fail (``DvolFieldLayoutError``) the moment ANY row does not match
    the expected [sek] 5-element positional layout or is not numeric --
    never silently drops or reinterprets a row.
    """
    if not isinstance(data, list):
        raise DvolFieldLayoutError(
            f"expected result.data as a list, got {type(data).__name__}: "
            f"{data!r:.300}")
    out: list[dict[str, Any]] = []
    for i, row in enumerate(data):
        if not isinstance(row, (list, tuple)) or len(row) != len(ROW_FIELDS):
            raise DvolFieldLayoutError(
                f"row {i}: expected {len(ROW_FIELDS)} positional fields "
                f"{ROW_FIELDS} ([sek] layout, unverified in this sandbox) "
                f"-- got {row!r}")
        try:
            rec = {
                "ts_ms": int(row[0]), "open": float(row[1]),
                "high": float(row[2]), "low": float(row[3]),
                "close": float(row[4]),
            }
        except (TypeError, ValueError) as exc:
            raise DvolFieldLayoutError(
                f"row {i}: non-numeric field(s) under the [sek] layout: "
                f"{row!r}") from exc
        out.append(rec)
    return out


def _default_fetcher(params: dict[str, Any]) -> bytes:
    """Real HTTP GET against Deribit's public REST -- UNREACHABLE from this
    sandbox (egress proxy blocks api.deribit.com); never exercised here."""
    url = f"{DERIBIT_BASE_URL}{ENDPOINT}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310
        return resp.read()


def fixture_fetcher(pages: list[Any]) -> Callable[[dict[str, Any]], bytes]:
    """Build a ``fetcher`` from a canned page list (offline/test use).

    Each element of ``pages`` is served, in order, one per call: a ``str``
    is used verbatim as the raw response body (including deliberately
    malformed field layouts, for loud-fail tests); anything else is
    ``json.dumps``-ed first. Once exhausted, further calls synthesise an
    empty ``result.data`` page so pagination terminates the same way a real
    "no more history" response would, rather than raising past the fixture.
    """
    it = iter(pages)

    def _fetch(_params: dict[str, Any]) -> bytes:
        page = next(it, None)
        if page is None:
            page = {"jsonrpc": "2.0", "result": {"data": []}}
        text = page if isinstance(page, str) else json.dumps(page)
        return text.encode("utf-8")

    return _fetch


def probe_call(
    currency: str, start_ms: int, end_ms: int, *,
    resolution: str = "1D", fetcher: Callable[[dict[str, Any]], bytes] | None = None,
) -> dict[str, Any]:
    """ONE REST call (no pagination) -- the ``--probe`` primitive.

    Returns the raw response head (first 300 chars, for a human to read
    against the [sek] assumption), its SHA-256, and the parsed rows.
    Raises ``DvolFieldLayoutError`` loudly on any layout mismatch or a
    Deribit-reported JSON-RPC error -- ``--probe`` is exactly the point
    where that must surface, before any backfill trusts the numbers.
    """
    if currency not in _VALID_CURRENCIES:
        raise ValueError(f"unsupported currency: {currency!r}")
    fetch = fetcher or _default_fetcher
    params = {"currency": currency, "resolution": resolution,
              "start_timestamp": start_ms, "end_timestamp": end_ms}
    raw = fetch(params)
    raw_text = raw.decode("utf-8", errors="replace")
    try:
        body = json.loads(raw_text)
    except ValueError as exc:
        raise DvolFieldLayoutError(
            f"{currency}: response is not valid JSON -- raw (300 ch): "
            f"{raw_text[:300]!r}") from exc
    if isinstance(body, dict) and body.get("error"):
        raise DvolFieldLayoutError(
            f"{currency}: Deribit JSON-RPC error response: {body['error']!r}")
    data = unwrap_result(body)
    rows = parse_rows(data) if data is not None else []
    return {"currency": currency, "raw_head": raw_text[:300],
            "raw_sha256": hashlib.sha256(raw).hexdigest(), "rows": rows}


def fetch_volatility_index(
    currency: str, start_ms: int, end_ms: int, *,
    resolution: str = "1D",
    fetcher: Callable[[dict[str, Any]], bytes] | None = None,
    max_req_per_sec: float = MAX_REQ_PER_SEC,
    max_pages: int = 2000,
) -> dict[str, Any]:
    """Paginate ``get_volatility_index_data`` BACKWARDS to ``start_ms``.

    Deterministic de-dup by ``ts_ms`` (a re-served overlap page never
    double-counts a day). Throttled to ``max_req_per_sec`` (spec: <= 5
    req/s). Stops on the first empty/exhausted page, on reaching
    ``start_ms``, or when a page adds no new timestamp (cursor stall guard)
    -- never spins past ``max_pages``. Every raw page's SHA-256 is
    collected so the manifest can prove exactly what bytes were parsed.
    """
    if currency not in _VALID_CURRENCIES:
        raise ValueError(f"unsupported currency: {currency!r}")
    if end_ms < start_ms:
        raise ValueError(f"end_ms {end_ms} before start_ms {start_ms}")
    fetch = fetcher or _default_fetcher
    min_interval = 1.0 / max_req_per_sec if max_req_per_sec > 0 else 0.0

    rows_by_ts: dict[int, dict[str, Any]] = {}
    raw_hashes: list[str] = []
    cur_end = end_ms
    pages = 0
    last_call: float | None = None

    while pages < max_pages:
        params = {"currency": currency, "resolution": resolution,
                  "start_timestamp": start_ms, "end_timestamp": cur_end}
        if last_call is not None and min_interval > 0:
            wait = min_interval - (time.monotonic() - last_call)
            if wait > 0:
                time.sleep(wait)
        raw = fetch(params)
        last_call = time.monotonic()
        raw_hashes.append(hashlib.sha256(raw).hexdigest())
        pages += 1
        try:
            body = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise DvolFieldLayoutError(
                f"{currency}: response is not valid JSON on page {pages} "
                f"-- raw (300 ch): {raw[:300]!r}") from exc
        if isinstance(body, dict) and body.get("error"):
            raise DvolFieldLayoutError(
                f"{currency}: Deribit JSON-RPC error on page {pages}: "
                f"{body['error']!r}")
        data = unwrap_result(body)
        if not data:
            break
        recs = parse_rows(data)
        if not recs:
            break
        new = 0
        for r in recs:
            if r["ts_ms"] not in rows_by_ts:
                rows_by_ts[r["ts_ms"]] = r
                new += 1
        oldest = min(r["ts_ms"] for r in recs)
        if oldest <= start_ms or new == 0:
            break
        cur_end = oldest - 1

    rows = sorted(rows_by_ts.values(), key=lambda r: r["ts_ms"])
    return {"currency": currency, "resolution": resolution,
            "start_requested_ms": start_ms, "end_requested_ms": end_ms,
            "rows": rows, "n_rows": len(rows), "n_pages": pages,
            "raw_sha256": raw_hashes}


def rows_to_daily(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """``{ts_ms, ..., close}`` rows -> ``{date, close}`` (UTC day of ts_ms).

    One row per UTC calendar day (resolution=1D bars already are that);
    de-dup keeps the LAST row seen for a given date, deterministic because
    input is expected pre-sorted by ``ts_ms`` (``fetch_volatility_index``
    guarantees this).
    """
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        d = datetime.fromtimestamp(r["ts_ms"] / 1000.0, tz=timezone.utc).date().isoformat()
        out[d] = {"date": d, "ts_ms": r["ts_ms"], "close": r["close"]}
    return [out[d] for d in sorted(out)]


def write_rest_parquet(rows: list[dict[str, Any]], out_path: Path) -> dict[str, Any]:
    """Write daily REST rows to ``out_path`` (parquet). NEVER data/harvest.

    Returns ``{n_rows, sha256_bytes}`` for the caller's manifest. Refuses
    (loud, ``ValueError``) to write inside a ``data/harvest`` tree -- the
    spec's hardest constraint on this deliverable.
    """
    if "data/harvest" in str(out_path).replace("\\", "/"):
        raise ValueError(
            f"refusing to write REST backfill output under data/harvest: {out_path}")
    import pyarrow as pa
    import pyarrow.parquet as pq

    daily = rows_to_daily(rows)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        "date": pa.array([r["date"] for r in daily]),
        "ts_ms": pa.array([r["ts_ms"] for r in daily], pa.int64()),
        "close": pa.array([r["close"] for r in daily], pa.float64()),
    })
    pq.write_table(table, out_path)
    return {"n_rows": len(daily),
            "sha256_bytes": hashlib.sha256(out_path.read_bytes()).hexdigest()}


def read_rest_parquet(path: Path) -> list[dict[str, Any]]:
    """Read a REST daily parquet back into ``{date, ts_ms, close}`` rows."""
    import pyarrow.parquet as pq

    table = pq.read_table(path, columns=["date", "ts_ms", "close"])
    cols = table.to_pydict()
    return [{"date": d, "ts_ms": t, "close": c}
            for d, t, c in zip(cols["date"], cols["ts_ms"], cols["close"])]


def day_bounds_ms(day: str) -> tuple[int, int]:
    """UTC ``[00:00:00.000, 23:59:59.999]`` millisecond bounds of an ISO day."""
    d = date.fromisoformat(day)
    start = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
    return start, start + _MS_PER_DAY - 1
