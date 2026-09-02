"""WP-7 -- Bybit v5 public REST client (KAPITALFREI, keyfrei).

Wraps three public endpoints, no auth, no order/account endpoints anywhere
near this module:

  * ``GET /v5/market/instruments-info?category=linear`` -- Universum,
    ALLE status-Werte (Trading, Settling, Closed, ...), Cursor-Paginierung.
  * ``GET /v5/market/kline?category=linear&interval=D`` -- Tages-Klines,
    rueckwaerts paginiert ueber ``end``, Drossel 5 Req/s.
  * ``GET /v5/market/funding/history?category=linear`` -- Funding-
    Abrechnungen (Nacharbeit #1: ``funding_n``/``funding_sum`` Pflicht-
    spalten), rueckwaerts paginiert ueber ``endTime``, Drossel 5 Req/s
    (identisch zu kline).

SANDBOX NOTE: this build environment's egress proxy blocks ``api.bybit.com``
entirely -- every function here therefore takes an injectable ``fetcher``
callable (``dict -> bytes``, the raw HTTP response body) so pagination,
throttling, hashing and field parsing can be built and tested completely
offline against canned pages (``fixture_fetcher``). ``_default_fetcher`` is
the real network path -- correct by reading of Bybit's published v5 API
shape, but NEVER exercised against a live response in this sandbox. Do not
attempt to run it here -- run ``--probe-tickers``/``--fetch`` on the
user's machine (real network) first, where ``probe_instruments``/
``probe_kline`` print the raw response head (300 chars) alongside the
parsed fields so a layout change is caught by a human before any census
trusts the numbers.

FIELD LAYOUT [sek]: per Bybit's published v5 docs
(``raw.githubusercontent.com/bybit-exchange/docs``, reachable only as a
doc-repo mirror in this sandbox, not the live API):

    instruments-info response:
        {"retCode": 0, "retMsg": "OK", "result": {
            "category": "linear", "list": [{"symbol": ..., "status": ...,
            "launchTime": ..., "deliveryTime": ..., ...}, ...],
            "nextPageCursor": "<cursor or empty string>"}, "time": ...}

    kline response:
        {"retCode": 0, "retMsg": "OK", "result": {
            "category": "linear", "symbol": "BTCUSDT",
            "list": [[startTime, open, high, low, close, volume, turnover],
                     ...]},  # newest-first, POSITIONAL 7-tuples (strings)
         "time": ...}

    funding/history response:
        {"retCode": 0, "retMsg": "OK", "result": {
            "category": "linear", "symbol": "BTCUSDT",
            "list": [{"symbol": "BTCUSDT", "fundingRate": "0.0001",
                      "fundingRateTimestamp": "1672041600000"}, ...]},
                     # newest-first, NAMED fields (not positional)
         "time": ...}

All three are EXPECTATIONS carried over from documentation, not facts
verified against a live response in this sandbox -- ``parse_instrument_rows``,
``parse_kline_rows`` and ``parse_funding_rows`` are the loud-fail gates on
these assumptions: any row that does not match raises
``BybitFieldLayoutError`` naming the row, instead of silently guessing
which positions/fields mean what.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from typing import Any, Callable

__all__ = [
    "BYBIT_BASE_URL", "INSTRUMENTS_ENDPOINT", "KLINE_ENDPOINT",
    "TICKERS_ENDPOINT", "FUNDING_ENDPOINT", "KLINE_ROW_FIELDS",
    "FUNDING_ROW_FIELDS", "MAX_REQ_PER_SEC",
    "BybitFieldLayoutError", "unwrap_result", "parse_instrument_rows",
    "parse_kline_rows", "parse_funding_rows", "fixture_fetcher",
    "probe_instruments", "probe_kline", "probe_funding_history",
    "fetch_instruments", "fetch_kline_symbol", "fetch_funding_history",
    "fetch_tickers",
]

#: [sek] -- unverified in this sandbox (no egress to Bybit at all).
BYBIT_BASE_URL = "https://api.bybit.com"
INSTRUMENTS_ENDPOINT = "/v5/market/instruments-info"
KLINE_ENDPOINT = "/v5/market/kline"
TICKERS_ENDPOINT = "/v5/market/tickers"
FUNDING_ENDPOINT = "/v5/market/funding/history"

#: Positional field order of one kline row -- [sek], see module docstring.
KLINE_ROW_FIELDS: tuple[str, ...] = (
    "start_ms", "open", "high", "low", "close", "volume", "turnover")

#: NAMED (not positional) fields of one funding/history row -- [sek], see
#: module docstring. ``fundingRateTimestamp`` is the settlement instant
#: (ms); ``fundingRate`` the signed rate for that settlement.
FUNDING_ROW_FIELDS: tuple[str, ...] = ("fundingRate", "fundingRateTimestamp")

#: Spec section 2 / Nacharbeit #1: "Drossel 5 Req/s" (self-throttle, 4.2%
#: of Bybit's documented 600 req/5s = 120 req/s limit [sek]) -- identical
#: throttle for kline AND funding/history.
MAX_REQ_PER_SEC = 5.0


class BybitFieldLayoutError(RuntimeError):
    """Loud failure: a REST response does not match the [sek] field layout,
    or Bybit reported a non-zero retCode."""


def unwrap_result(body: Any) -> Any:
    """``result`` from a Bybit v5 envelope, tolerant of a couple of shapes.

    Accepts the real envelope ``{"retCode": 0, "result": {...}}``; a bare
    ``{"result": {...}}`` (fixture convenience, retCode omitted); and a
    body that already IS the result dict (maximal fixture convenience).
    Raises loudly if ``retCode`` is present and non-zero -- a Bybit-side
    error must never be silently treated as "empty page". Returns ``None``
    for an unrecognisable body (distinct from "no more pages").
    """
    if isinstance(body, dict) and "retCode" in body:
        if body["retCode"] != 0:
            raise BybitFieldLayoutError(
                f"Bybit retCode={body['retCode']!r} retMsg="
                f"{body.get('retMsg')!r} -- not a field-layout question, "
                "an API-side error")
        return body.get("result")
    if isinstance(body, dict) and "result" in body:
        return body["result"]
    if isinstance(body, dict):
        return body
    return None


def parse_instrument_rows(rows: Any) -> list[dict[str, Any]]:
    """``result.list`` (instruments-info) -> validated instrument dicts.

    Loud-fail the moment any row is not a dict or is missing ``symbol``/
    ``status`` (the two fields B3's finding depends on) -- the raw dict is
    otherwise passed through UNCHANGED (this endpoint's payload is wide
    and this module does not know, or need to know, every column).
    """
    if not isinstance(rows, list):
        raise BybitFieldLayoutError(
            f"expected result.list as a list, got {type(rows).__name__}: "
            f"{rows!r:.300}")
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or "symbol" not in row or "status" not in row:
            raise BybitFieldLayoutError(
                f"instruments-info row {i}: expected a dict with at least "
                f"'symbol'/'status' ([sek] layout, unverified in this "
                f"sandbox) -- got {row!r}")
        out.append(dict(row))
    return out


def parse_kline_rows(rows: Any) -> list[dict[str, Any]]:
    """``result.list`` (kline) -> ``{start_ms, open, high, low, close,
    volume, turnover}`` dicts. Loud-fail (``BybitFieldLayoutError``) on any
    row that is not exactly the expected [sek] 7-element positional
    layout, or is not numeric-castable."""
    if not isinstance(rows, list):
        raise BybitFieldLayoutError(
            f"expected result.list as a list, got {type(rows).__name__}: "
            f"{rows!r:.300}")
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, (list, tuple)) or len(row) != len(KLINE_ROW_FIELDS):
            raise BybitFieldLayoutError(
                f"kline row {i}: expected {len(KLINE_ROW_FIELDS)} "
                f"positional fields {KLINE_ROW_FIELDS} ([sek] layout, "
                f"unverified in this sandbox) -- got {row!r}")
        try:
            rec = {"start_ms": int(row[0]), "open": float(row[1]),
                   "high": float(row[2]), "low": float(row[3]),
                   "close": float(row[4]), "volume": float(row[5]),
                   "turnover": float(row[6])}
        except (TypeError, ValueError) as exc:
            raise BybitFieldLayoutError(
                f"kline row {i}: non-numeric field(s) under the [sek] "
                f"layout: {row!r}") from exc
        out.append(rec)
    return out


def parse_funding_rows(rows: Any) -> list[dict[str, Any]]:
    """``result.list`` (funding/history) -> ``{symbol, funding_rate,
    ts_ms}`` dicts. Loud-fail (``BybitFieldLayoutError``) on any row
    missing ``fundingRate``/``fundingRateTimestamp`` ([sek] NAMED-field
    layout, see module docstring) or carrying a non-numeric value --
    Nacharbeit #1's ``funding_n``/``funding_sum`` are worthless if this
    silently drops or misreads a row."""
    if not isinstance(rows, list):
        raise BybitFieldLayoutError(
            f"expected result.list as a list, got {type(rows).__name__}: "
            f"{rows!r:.300}")
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(f not in row for f in FUNDING_ROW_FIELDS):
            raise BybitFieldLayoutError(
                f"funding/history row {i}: expected a dict with "
                f"{FUNDING_ROW_FIELDS} ([sek] layout, unverified in this "
                f"sandbox) -- got {row!r}")
        try:
            rec = {"symbol": row.get("symbol"),
                   "funding_rate": float(row["fundingRate"]),
                   "ts_ms": int(row["fundingRateTimestamp"])}
        except (TypeError, ValueError) as exc:
            raise BybitFieldLayoutError(
                f"funding/history row {i}: non-numeric field(s) under the "
                f"[sek] layout: {row!r}") from exc
        out.append(rec)
    return out


def _default_fetcher(url: str) -> bytes:
    """Real HTTP GET against Bybit's public REST -- UNREACHABLE from this
    sandbox (egress proxy blocks api.bybit.com); never exercised here."""
    with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310
        return resp.read()


def fixture_fetcher(pages: list[Any]) -> Callable[[str], bytes]:
    """Build a ``fetcher`` from a canned page list (offline/test use).

    Each element of ``pages`` is served, in order, one per call: a ``str``
    is used verbatim as the raw response body (including deliberately
    malformed layouts, for loud-fail tests); anything else is
    ``json.dumps``-ed first. Once exhausted, further calls synthesise an
    empty-list ``result`` so pagination terminates the same way a real
    "no more pages" response would, rather than raising past the fixture.
    """
    it = iter(pages)

    def _fetch(_url: str) -> bytes:
        page = next(it, None)
        if page is None:
            page = {"retCode": 0, "retMsg": "OK",
                     "result": {"list": [], "nextPageCursor": ""}}
        text = page if isinstance(page, str) else json.dumps(page)
        return text.encode("utf-8")

    return _fetch


def _get(url: str, params: dict[str, Any],
         fetcher: Callable[[str], bytes]) -> tuple[bytes, str]:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    raw = fetcher(full)
    return raw, raw.decode("utf-8", errors="replace")


def _parse_body(raw_text: str, ctx: str) -> Any:
    try:
        return json.loads(raw_text)
    except ValueError as exc:
        raise BybitFieldLayoutError(
            f"{ctx}: response is not valid JSON -- raw (300 ch): "
            f"{raw_text[:300]!r}") from exc


# ----------------------------------------------------------------------------
# probe (the --probe-tickers-adjacent, --probe-like primitive for REST)
# ----------------------------------------------------------------------------

def probe_instruments(category: str = "linear", *,
                       fetcher: Callable[[str], bytes] | None = None) -> dict[str, Any]:
    """ONE instruments-info call (no pagination) -- prints raw head + parsed
    fields for a human to check against the [sek] layout assumption."""
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{INSTRUMENTS_ENDPOINT}"
    raw, raw_text = _get(url, {"category": category}, fetch)
    body = _parse_body(raw_text, "instruments-info probe")
    result = unwrap_result(body)
    rows = parse_instrument_rows(result.get("list", [])) if isinstance(result, dict) else []
    statuses = sorted({r["status"] for r in rows})
    return {"raw_head": raw_text[:300], "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "n_rows": len(rows), "statuses": statuses, "rows": rows}


def probe_kline(symbol: str, *, category: str = "linear", interval: str = "D",
                 limit: int = 1000,
                 fetcher: Callable[[str], bytes] | None = None) -> dict[str, Any]:
    """ONE kline call (no pagination) -- raw head + parsed rows."""
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{KLINE_ENDPOINT}"
    raw, raw_text = _get(url, {"category": category, "symbol": symbol,
                                "interval": interval, "limit": limit}, fetch)
    body = _parse_body(raw_text, f"kline probe {symbol}")
    result = unwrap_result(body)
    rows = parse_kline_rows(result.get("list", [])) if isinstance(result, dict) else []
    return {"symbol": symbol, "raw_head": raw_text[:300],
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "n_rows": len(rows), "rows": rows}


def probe_funding_history(symbol: str, *, category: str = "linear", limit: int = 200,
                           fetcher: Callable[[str], bytes] | None = None) -> dict[str, Any]:
    """ONE funding/history call (no pagination) -- raw head + parsed rows."""
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{FUNDING_ENDPOINT}"
    raw, raw_text = _get(url, {"category": category, "symbol": symbol, "limit": limit}, fetch)
    body = _parse_body(raw_text, f"funding/history probe {symbol}")
    result = unwrap_result(body)
    rows = parse_funding_rows(result.get("list", [])) if isinstance(result, dict) else []
    return {"symbol": symbol, "raw_head": raw_text[:300],
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "n_rows": len(rows), "rows": rows}


# ----------------------------------------------------------------------------
# paginated fetch
# ----------------------------------------------------------------------------

def fetch_instruments(
    category: str = "linear", *,
    fetcher: Callable[[str], bytes] | None = None,
    max_req_per_sec: float = MAX_REQ_PER_SEC, max_pages: int = 500,
) -> dict[str, Any]:
    """Cursor-paginate ``instruments-info`` to exhaustion.

    Loud-fail (``BybitFieldLayoutError``) if EVERY page comes back with
    zero non-Trading rows -- B3's finding condition ("instruments-info
    liefert keine Zeilen mit status != Trading") is a CENSUS-level verdict
    (report.py), not a client-level error, so this function itself never
    raises for that case; it only raises on layout/API errors. See
    ``report.finding_b3`` for the actual B3 check.
    """
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{INSTRUMENTS_ENDPOINT}"
    min_interval = 1.0 / max_req_per_sec if max_req_per_sec > 0 else 0.0
    rows_by_symbol: dict[str, dict[str, Any]] = {}
    raw_hashes: list[str] = []
    cursor = ""
    pages = 0
    last_call: float | None = None
    while pages < max_pages:
        params: dict[str, Any] = {"category": category}
        if cursor:
            params["cursor"] = cursor
        if last_call is not None and min_interval > 0:
            wait = min_interval - (time.monotonic() - last_call)
            if wait > 0:
                time.sleep(wait)
        raw, raw_text = _get(url, params, fetch)
        last_call = time.monotonic()
        raw_hashes.append(hashlib.sha256(raw).hexdigest())
        pages += 1
        body = _parse_body(raw_text, f"instruments-info page {pages}")
        result = unwrap_result(body)
        if not isinstance(result, dict):
            break
        rows = parse_instrument_rows(result.get("list", []))
        for r in rows:
            rows_by_symbol[r["symbol"]] = r
        next_cursor = result.get("nextPageCursor") or ""
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    all_rows = sorted(rows_by_symbol.values(), key=lambda r: r["symbol"])
    return {"category": category, "rows": all_rows, "n_rows": len(all_rows),
            "n_pages": pages, "raw_sha256": raw_hashes,
            "statuses": sorted({r["status"] for r in all_rows})}


def fetch_kline_symbol(
    symbol: str, start_ms: int, end_ms: int, *,
    category: str = "linear", interval: str = "D", limit: int = 1000,
    fetcher: Callable[[str], bytes] | None = None,
    max_req_per_sec: float = MAX_REQ_PER_SEC, max_pages: int = 2000,
) -> dict[str, Any]:
    """Paginate ``kline`` BACKWARDS over ``end`` down to ``start_ms``.

    Deterministic de-dup by ``start_ms`` (a re-served overlap page never
    double-counts a day). Throttled to ``max_req_per_sec`` (spec: 5 Req/s).
    Stops on an empty/exhausted page, on reaching ``start_ms``, or when a
    page adds no new timestamp (cursor-stall guard) -- never spins past
    ``max_pages``. Every raw page's SHA-256 is collected (manifest
    provenance).
    """
    if end_ms < start_ms:
        raise ValueError(f"end_ms {end_ms} before start_ms {start_ms}")
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{KLINE_ENDPOINT}"
    min_interval = 1.0 / max_req_per_sec if max_req_per_sec > 0 else 0.0

    rows_by_ts: dict[int, dict[str, Any]] = {}
    raw_hashes: list[str] = []
    cur_end = end_ms
    pages = 0
    last_call: float | None = None
    while pages < max_pages:
        params = {"category": category, "symbol": symbol, "interval": interval,
                   "limit": limit, "end": cur_end}
        if last_call is not None and min_interval > 0:
            wait = min_interval - (time.monotonic() - last_call)
            if wait > 0:
                time.sleep(wait)
        raw, raw_text = _get(url, params, fetch)
        last_call = time.monotonic()
        raw_hashes.append(hashlib.sha256(raw).hexdigest())
        pages += 1
        body = _parse_body(raw_text, f"kline {symbol} page {pages}")
        result = unwrap_result(body)
        if not isinstance(result, dict):
            break
        recs = parse_kline_rows(result.get("list", []))
        if not recs:
            break
        new = 0
        for r in recs:
            if r["start_ms"] not in rows_by_ts:
                rows_by_ts[r["start_ms"]] = r
                new += 1
        oldest = min(r["start_ms"] for r in recs)
        if oldest <= start_ms or new == 0:
            break
        cur_end = oldest - 1

    rows = sorted((r for r in rows_by_ts.values()
                   if start_ms <= r["start_ms"] <= end_ms),
                  key=lambda r: r["start_ms"])
    return {"symbol": symbol, "category": category, "interval": interval,
            "start_requested_ms": start_ms, "end_requested_ms": end_ms,
            "rows": rows, "n_rows": len(rows), "n_pages": pages,
            "raw_sha256": raw_hashes}


def fetch_funding_history(
    symbol: str, start_ms: int, end_ms: int, *,
    category: str = "linear", limit: int = 200,
    fetcher: Callable[[str], bytes] | None = None,
    max_req_per_sec: float = MAX_REQ_PER_SEC, max_pages: int = 2000,
) -> dict[str, Any]:
    """Paginate ``funding/history`` BACKWARDS over ``endTime`` down to
    ``start_ms`` (Nacharbeit #1 -- identical shape/throttle discipline to
    ``fetch_kline_symbol``, ``limit=200`` per the spec's endpoint call).

    Deterministic de-dup by ``ts_ms`` (a re-served overlap page never
    double-counts a settlement). Throttled to ``max_req_per_sec`` (spec:
    5 Req/s, same as kline). Stops on an empty/exhausted page, on reaching
    ``start_ms``, or when a page adds no new timestamp (cursor-stall
    guard) -- never spins past ``max_pages``. Every raw page's SHA-256 is
    collected (manifest provenance, same discipline as kline).
    """
    if end_ms < start_ms:
        raise ValueError(f"end_ms {end_ms} before start_ms {start_ms}")
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{FUNDING_ENDPOINT}"
    min_interval = 1.0 / max_req_per_sec if max_req_per_sec > 0 else 0.0

    rows_by_ts: dict[int, dict[str, Any]] = {}
    raw_hashes: list[str] = []
    cur_end = end_ms
    pages = 0
    last_call: float | None = None
    while pages < max_pages:
        params = {"category": category, "symbol": symbol, "limit": limit,
                   "endTime": cur_end}
        if last_call is not None and min_interval > 0:
            wait = min_interval - (time.monotonic() - last_call)
            if wait > 0:
                time.sleep(wait)
        raw, raw_text = _get(url, params, fetch)
        last_call = time.monotonic()
        raw_hashes.append(hashlib.sha256(raw).hexdigest())
        pages += 1
        body = _parse_body(raw_text, f"funding/history {symbol} page {pages}")
        result = unwrap_result(body)
        if not isinstance(result, dict):
            break
        recs = parse_funding_rows(result.get("list", []))
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

    rows = sorted((r for r in rows_by_ts.values()
                   if start_ms <= r["ts_ms"] <= end_ms),
                  key=lambda r: r["ts_ms"])
    return {"symbol": symbol, "category": category,
            "start_requested_ms": start_ms, "end_requested_ms": end_ms,
            "rows": rows, "n_rows": len(rows), "n_pages": pages,
            "raw_sha256": raw_hashes}


def fetch_tickers(category: str = "linear", *,
                   fetcher: Callable[[str], bytes] | None = None) -> dict[str, Any]:
    """``GET /v5/market/tickers?category=...`` -- ONE request, no
    pagination (spec section 2: "ein Request je Kategorie"). REST fallback
    for ``spread_probe.py`` when the harvest content probe on
    ``bybit/tickers`` does not find the fields it needs. Passes rows
    through unchanged (dicts) -- this endpoint's payload is wide and
    ``spread_probe.py`` picks the specific fields it needs (bid1Price,
    ask1Price, openInterest, fundingRate, turnover24h).
    """
    fetch = fetcher or _default_fetcher
    url = f"{BYBIT_BASE_URL}{TICKERS_ENDPOINT}"
    raw, raw_text = _get(url, {"category": category}, fetch)
    body = _parse_body(raw_text, "tickers")
    result = unwrap_result(body)
    rows_raw = result.get("list", []) if isinstance(result, dict) else []
    if not isinstance(rows_raw, list):
        raise BybitFieldLayoutError(
            f"tickers: expected result.list as a list, got "
            f"{type(rows_raw).__name__}: {rows_raw!r:.300}")
    rows = []
    for i, row in enumerate(rows_raw):
        if not isinstance(row, dict) or "symbol" not in row:
            raise BybitFieldLayoutError(
                f"tickers row {i}: expected a dict with at least 'symbol' "
                f"([sek] layout, unverified in this sandbox) -- got {row!r}")
        rows.append(dict(row))
    return {"category": category, "rows": rows, "n_rows": len(rows),
            "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_head": raw_text[:300]}
