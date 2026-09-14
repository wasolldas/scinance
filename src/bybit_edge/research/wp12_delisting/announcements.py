"""WP-12 -- Bybit v5 public announcements client (delisting register),
KAPITALFREI, keyfrei.

Wraps ONE public endpoint, no auth, no order/account endpoint anywhere
near this module:

  * ``GET /v5/announcements/index`` -- paginated announcement index,
    filterable by ``locale``/``type``/``tag``. [sek] -- unverified in this
    sandbox (the egress proxy blocks ``api.bybit.com`` entirely, same
    constraint documented in ``wp7_universe.bybit_rest``); the parameter
    names and response envelope below are carried over from memory of
    Bybit's published v5 docs, not read live here. Both are therefore
    CLI-overridable (``--locale``, ``--type``, ``--tag``) so a human can
    correct them on the user's machine (real network) without a code
    change, and every parsing step loud-fails on a genuinely different
    shape instead of guessing.

    Expected request: ``?locale=en-US&type=delistings&page=1&limit=50``.
    ``type=delistings`` is the primary filter this module registers with;
    if the FIRST page comes back with a non-zero ``retCode`` (an API-side
    rejection of the ``type`` value, not a field-layout question --
    ``bybit_rest.unwrap_result`` raises for exactly this), the fetch is
    retried ONCE with ``tag=Delistings`` in place of ``type`` (task
    brief's named fallback) before giving up loudly.

    Expected response envelope (as for every Bybit v5 endpoint):
        {"retCode": 0, "retMsg": "OK", "result": {
            "list": [{"title": ..., "description": ...,
                      "url"/"articleUrl": ...,
                      "dateTimestamp"/"publishTime"/"startDateTimestamp":
                          <ms epoch>, ...}, ...],
            "total": <int, optional>}, "time": ...}

Schema-drift loud fail (task brief, verbatim requirement): a page whose
unwrapped ``result`` is not a dict, OR is a dict but has NO ``list`` key
AT ALL, raises ``AnnouncementFieldLayoutError`` -- this is distinct from
(and never confused with) an EMPTY ``list``, which is the normal
"no more pages" pagination terminator.

Throttle: no standalone reusable throttle helper exists in
``wp7_universe.bybit_rest`` to import (each of its ``fetch_*`` functions
inlines the same "sleep until 1/max_req_per_sec has elapsed" pattern) --
this module replicates that exact pattern locally at the same default
(5 Req/s). ``bybit_rest.fixture_fetcher``/``unwrap_result`` ARE reusable
(generic envelope helpers, no wp7-specific assumptions) and are imported
read-only, per the build brief.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..wp7_universe import bybit_rest

__all__ = [
    "BYBIT_BASE_URL", "ANNOUNCEMENTS_ENDPOINT", "MAX_REQ_PER_SEC",
    "DEFAULT_LOCALE", "DEFAULT_TYPE", "FALLBACK_TAG",
    "SYMBOL_RE", "DELIST_DATETIME_RE",
    "AnnouncementFieldLayoutError",
    "extract_symbols", "guess_category", "extract_delisting_ms",
    "parse_announcement_rows", "parse_announcement_row",
    "fetch_delisting_announcements", "build_register_rows",
    "REGISTER_COLUMNS", "write_register_parquet", "write_raw_pages",
]

#: [sek] -- unverified in this sandbox (no egress to Bybit at all), see
#: module docstring.
BYBIT_BASE_URL = "https://api.bybit.com"
ANNOUNCEMENTS_ENDPOINT = "/v5/announcements/index"

#: Same self-throttle discipline as ``wp7_universe.bybit_rest``
#: (``MAX_REQ_PER_SEC = 5.0``) -- identical default, CLI-overridable.
MAX_REQ_PER_SEC = 5.0

DEFAULT_LOCALE = "en-US"
DEFAULT_TYPE = "delistings"
#: Task brief's named fallback filter, tried once if ``type`` errors.
FALLBACK_TAG = "Delistings"

#: Symbol tokens: an uppercase/digit run of at least one character,
#: followed immediately by one of the three known suffixes, on a word
#: boundary at both ends. Deliberately requires >= 1 PREFIX character
#: before the suffix literal -- this is what keeps a bare "USDT" (as in
#: the adversarial phrase "USDT margin") from matching: there is no room
#: left for the mandatory prefix once the 4-char suffix literal has
#: consumed the whole word. Alternation order (USDT before USD) does not
#: itself matter for correctness here (regex backtracking already finds
#: the longest well-formed split, e.g. "BTC"+"USDT" over "BTCUS"+"DT"),
#: but is kept in the documented, more-specific-first order for clarity.
SYMBOL_RE = re.compile(r"\b[A-Z0-9]+(?:USDT|PERP|USD)\b")

#: A delisting timestamp inside free text, e.g. "2024-03-15 08:00 UTC" or
#: "2024-03-15T08:00:00 UTC". Seconds optional; UTC required (this
#: register never guesses a non-UTC offset).
DELIST_DATETIME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?\s*UTC", re.IGNORECASE)

#: Column order of ``register.parquet`` -- also the fingerprint/CSV order.
REGISTER_COLUMNS: tuple[str, ...] = (
    "announcement_id", "url", "title", "publish_ms", "symbols", "category",
    "delisting_ms", "raw_snippet",
)

#: publish-timestamp field aliases, first-present wins ([sek] layout --
#: several Bybit v5 announcement shapes have been observed historically
#: to use different names for "when this was published"; tolerated as
#: aliases rather than picked as a single guaranteed field).
_PUBLISH_MS_ALIASES: tuple[str, ...] = (
    "dateTimestamp", "publishTime", "startDateTimestamp", "date",
)
_URL_ALIASES: tuple[str, ...] = ("url", "articleUrl", "link")


class AnnouncementFieldLayoutError(RuntimeError):
    """Loud failure: an announcements response does not match the [sek]
    field layout, or Bybit reported a non-zero retCode on BOTH the
    ``type`` and the ``tag``-fallback attempt."""


# ----------------------------------------------------------------------------
# parsing (pure, offline)
# ----------------------------------------------------------------------------

def extract_symbols(text: str) -> list[str]:
    """All distinct symbol-shaped tokens in ``text``, in first-seen order.

    Deliberately case-sensitive (Bybit ticker symbols are always upper
    case in announcement titles) -- this is itself part of what rejects
    the adversarial "USDT margin" case: a plain, unqualified "USDT" is
    never matched at all (see ``SYMBOL_RE`` docstring), regardless of case.
    """
    seen: dict[str, None] = {}
    for m in SYMBOL_RE.finditer(text or ""):
        seen.setdefault(m.group(0), None)
    return list(seen)


def guess_category(symbols: list[str], text: str) -> str:
    """Best-effort category guess (linear/inverse/spot/unknown) from the
    extracted symbols' suffixes plus a spot keyword check on the raw text.

    Deliberately conservative: ``PERP``-suffixed symbols are legacy/
    ambiguous naming [sek, uncertain] and are never guessed as
    linear/inverse -- they fall to "unknown" unless another symbol in the
    same announcement disambiguates the category.
    """
    has_usdt = any(s.endswith("USDT") for s in symbols)
    has_usd_only = any(s.endswith("USD") and not s.endswith("USDT") for s in symbols)
    if has_usdt and not has_usd_only:
        return "linear"
    if has_usd_only and not has_usdt:
        return "inverse"
    if "spot" in (text or "").lower():
        return "spot"
    return "unknown"


def extract_delisting_ms(text: str) -> tuple[int | None, str | None]:
    """First UTC date/time found in ``text`` -> epoch ms, else
    ``(None, raw_snippet)`` where ``raw_snippet`` is the first 200 chars of
    ``text`` so a human can see what the parser had to work with."""
    m = DELIST_DATETIME_RE.search(text or "")
    if m is None:
        snippet = (text or "")[:200]
        return None, (snippet or None)
    y, mo, d = m.group(1).split("-")
    hh, mm = m.group(2), m.group(3)
    ss = m.group(4) or "00"
    dt = datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss), tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000), None


def parse_announcement_rows(result: Any) -> list[dict[str, Any]]:
    """``result`` (already unwrapped by ``bybit_rest.unwrap_result``) ->
    validated raw announcement dicts. Loud-fails
    (``AnnouncementFieldLayoutError``) if ``result`` is not a dict, or is a
    dict WITHOUT a ``list`` key at all -- schema drift, task-brief
    requirement, never silently treated as an empty page. An empty
    ``list`` (key present, zero rows) is the normal end-of-pagination
    signal and passes through as ``[]``.
    """
    if not isinstance(result, dict):
        raise AnnouncementFieldLayoutError(
            f"expected result as a dict, got {type(result).__name__}: {result!r:.300}")
    if "list" not in result:
        raise AnnouncementFieldLayoutError(
            "announcements response missing 'result.list' -- schema drift "
            f"([sek] layout, unverified in this sandbox), got keys {sorted(result)!r}")
    rows = result["list"]
    if not isinstance(rows, list):
        raise AnnouncementFieldLayoutError(
            f"expected result.list as a list, got {type(rows).__name__}: {rows!r:.300}")
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or "title" not in row:
            raise AnnouncementFieldLayoutError(
                f"announcement row {i}: expected a dict with at least 'title' "
                f"([sek] layout, unverified in this sandbox) -- got {row!r}")
        out.append(dict(row))
    return out


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return None


def parse_announcement_row(row: dict[str, Any]) -> dict[str, Any]:
    """One raw announcement dict -> a ``REGISTER_COLUMNS``-shaped row.

    Never raises on a missing publish timestamp or URL (both are treated
    as soft/optional fields, see module docstring's alias list) -- only
    ``parse_announcement_rows`` (missing ``title`` or a non-dict row)
    raises. ``announcement_id`` is the URL's last path segment when a URL
    is present, else a stable sha256 prefix of the title (deterministic,
    never random).
    """
    title = str(row["title"])
    url = _first_present(row, _URL_ALIASES)
    url = str(url) if url is not None else None
    publish_raw = _first_present(row, _PUBLISH_MS_ALIASES)
    publish_ms = int(publish_raw) if publish_raw is not None else None

    if url:
        tail = urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        announcement_id = tail or hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    else:
        announcement_id = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]

    text = title + " " + str(row.get("description") or "")
    symbols = extract_symbols(text)
    category = guess_category(symbols, text)
    delisting_ms, raw_snippet = extract_delisting_ms(text)

    return {
        "announcement_id": announcement_id, "url": url, "title": title,
        "publish_ms": publish_ms, "symbols": symbols, "category": category,
        "delisting_ms": delisting_ms, "raw_snippet": raw_snippet,
    }


# ----------------------------------------------------------------------------
# paginated fetch (network, or ``fixture_fetcher`` in tests -- same
# injectable-fetcher discipline as ``wp7_universe.bybit_rest``)
# ----------------------------------------------------------------------------

def _get(url: str, params: dict[str, Any], fetcher: Callable[[str], bytes]) -> tuple[bytes, str]:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    raw = fetcher(full)
    return raw, raw.decode("utf-8", errors="replace")


def fetch_delisting_announcements(
    *, locale: str = DEFAULT_LOCALE, type_param: str | None = DEFAULT_TYPE,
    tag_fallback: str | None = FALLBACK_TAG, page_start: int = 1, limit: int = 50,
    fetcher: Callable[[str], bytes] | None = None,
    max_req_per_sec: float = MAX_REQ_PER_SEC, max_pages: int = 200,
) -> dict[str, Any]:
    """Page-paginate ``/v5/announcements/index`` to exhaustion.

    Tries ``type=type_param`` first; if the FIRST page's envelope carries a
    non-zero ``retCode`` (``bybit_rest.unwrap_result`` raises
    ``BybitFieldLayoutError`` for exactly that -- an API-side rejection,
    not a field-layout question), retries ONCE from ``page_start`` with
    ``tag=tag_fallback`` in place of ``type``. Any OTHER failure (a
    field-layout loud-fail past the first page, or the fallback ALSO
    failing) propagates loudly -- never silently swallowed.

    Returns raw (unparsed via ``parse_announcement_row``) rows plus every
    raw page's bytes (for ``write_raw_pages``) and which param the
    successful run used.
    """
    fetch = fetcher or bybit_rest._default_fetcher  # noqa: SLF001 (shared network primitive)
    url = f"{BYBIT_BASE_URL}{ANNOUNCEMENTS_ENDPOINT}"
    min_interval = 1.0 / max_req_per_sec if max_req_per_sec > 0 else 0.0

    def _run(param_name: str, param_value: str) -> tuple[list[dict[str, Any]], list[bytes]]:
        rows: list[dict[str, Any]] = []
        raw_pages: list[bytes] = []
        last_call: float | None = None
        page = page_start
        pages_fetched = 0
        while pages_fetched < max_pages:
            params: dict[str, Any] = {"locale": locale, param_name: param_value,
                                       "page": page, "limit": limit}
            if last_call is not None and min_interval > 0:
                wait = min_interval - (time.monotonic() - last_call)
                if wait > 0:
                    time.sleep(wait)
            raw, raw_text = _get(url, params, fetch)
            last_call = time.monotonic()
            pages_fetched += 1
            raw_pages.append(raw)
            body = json.loads(raw_text) if raw_text.strip() else {}
            result = bybit_rest.unwrap_result(body)
            page_rows = parse_announcement_rows(result)
            if not page_rows:
                break
            rows.extend(page_rows)
            page += 1
        return rows, raw_pages

    if type_param is not None:
        try:
            rows, raw_pages = _run("type", type_param)
            return {"rows": rows, "raw_pages": raw_pages, "param_used": ("type", type_param)}
        except bybit_rest.BybitFieldLayoutError as exc:
            if "retCode" not in str(exc) or tag_fallback is None:
                raise
            # fall through to the tag fallback below
    if tag_fallback is None:
        raise AnnouncementFieldLayoutError(
            "announcements fetch failed on 'type' and no 'tag' fallback was given")
    rows, raw_pages = _run("tag", tag_fallback)
    return {"rows": rows, "raw_pages": raw_pages, "param_used": ("tag", tag_fallback)}


# ----------------------------------------------------------------------------
# register assembly + artifact writers
# ----------------------------------------------------------------------------

def build_register_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Raw announcement dicts -> parsed, DEDUPLICATED (by
    ``announcement_id``, first occurrence wins) ``REGISTER_COLUMNS`` rows,
    sorted by ``publish_ms`` ascending (``None`` sorts first, i.e. oldest/
    unknown-dated first -- deterministic, never insertion-order-dependent).
    """
    by_id: dict[str, dict[str, Any]] = {}
    for raw in raw_rows:
        parsed = parse_announcement_row(raw)
        by_id.setdefault(parsed["announcement_id"], parsed)
    return sorted(by_id.values(),
                  key=lambda r: (r["publish_ms"] is None, r["publish_ms"] or 0, r["announcement_id"]))


def write_raw_pages(out_dir: Path | str, raw_pages: list[bytes]) -> list[dict[str, str]]:
    """Write every raw page under ``out_dir`` named by its sha256 -- never
    under ``data/harvest`` (checked loudly, repo-wide discipline)."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write raw announcement pages under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, str]] = []
    for raw in raw_pages:
        sha = hashlib.sha256(raw).hexdigest()
        path = out_dir / f"{sha}.json"
        if not path.is_file():
            path.write_bytes(raw)
        out.append({"path": str(path), "sha256": sha})
    return out


def write_register_parquet(rows: list[dict[str, Any]], path: Path | str) -> dict[str, str]:
    """Write ``register.parquet`` (schema per ``REGISTER_COLUMNS``) and
    return its path + sha256 (DEC-53 artifact). Never under
    ``data/harvest``."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = Path(path)
    if "data/harvest" in path.as_posix():
        raise ValueError(f"refusing to write register.parquet under data/harvest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)

    schema = pa.schema([
        ("announcement_id", pa.string()), ("url", pa.string()),
        ("title", pa.string()), ("publish_ms", pa.int64()),
        ("symbols", pa.list_(pa.string())), ("category", pa.string()),
        ("delisting_ms", pa.int64()), ("raw_snippet", pa.string()),
    ])
    cols = {c: [r.get(c) for r in rows] for c in REGISTER_COLUMNS}
    table = pa.table(cols, schema=schema)
    pq.write_table(table, path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "sha256": sha, "n_rows": len(rows)}
