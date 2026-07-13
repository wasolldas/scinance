"""Event-window feature extraction for the H-17 venue-fingerprint gate.

Per node (= exchange x symbol, 10 nodes: 5 symbols x {bybit, binance},
publicTrade only) the raw trade stream is turned into 5-minute EVENT windows
with the four pre-registered channels (registry H-17, verbatim):

  1. inter-trade duration   (ms between consecutive trades of the node)
  2. log trade size         (log of the trade size)
  3. aggressor sign         (+1 taker buy, -1 taker sell)
  4. tick direction         (tick rule with zero-tick carry: +1/-1/0)

PER-DAY QUANTILE NORMALISATION (verdict-critical, registry H-17): every
channel is rank-transformed WITHIN (node, UTC day) to average-rank quantiles
u = rank / (n + 1) in (0, 1). This deliberately DESTROYS the trivial venue
tells the registry names — tick size (price/size grid granularity),
fee-driven size clustering (round-size atoms collapse to their rank mass),
and activity level (the absolute duration scale collapses to within-day
ranks) — leaving only the temporal dependency SHAPE of the flow.
``trivial_tell_probe_features`` + ``simple_probe_accuracy`` provide the
builder-diagnostic the registry demands: a simple per-window summary-stat
classifier must NOT be able to separate venues on injected trivial tells
after normalisation (test: tests/unit/test_c17_venue.py).

Window construction: events are bucketed into 5-minute wall-clock buckets
per node; a window is kept iff it has >= MIN_EVENTS_PER_WINDOW events, is
truncated to the FIRST SEQ_LEN events and zero-padded with a validity mask.
The downstream encoder pools with a MASKED MEAN (count-invariant by
construction) so the pad count itself is not an activity side-channel; the
per-venue valid-length distribution is still reported as a diagnostic.

Loader: read-only DuckDB over the harvester Hive tree, exchange-agnostic
payload extraction — Bybit backfill (``side``/``price``/``size``), Bybit
live short form (``S``/``p``/``v``) and Binance aggTrades (``p``/``q``/``m``,
``m`` = buyer-is-maker -> aggressor sell). No write access (Schutzgut).

KAPITALFREI: pure feature extraction. numpy (+ duckdb read-only) only.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

#: Program-standard 5-symbol panel (registry H-17: 5 Symbole).
DEFAULT_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")

#: The two pre-registered venues (registry H-17: Bybit vs. Binance).
DEFAULT_EXCHANGES: tuple[str, ...] = ("bybit", "binance")

#: Pre-registered data window (registry H-17: Basis-Bestand 2026-03-27..Cutoff).
DEFAULT_START_DATE = "2026-03-27"
DEFAULT_END_DATE = "2026-07-04"

#: 5-minute event windows (registry H-17, verbatim).
WINDOW_MINUTES = 5

#: Fixed event-sequence length per window (registry compute note: ~512 events).
SEQ_LEN = 512

#: Technical floor: windows with fewer events are dropped (too little shape).
#: NOT a registered threshold — degeneracy guard for near-empty buckets.
MIN_EVENTS_PER_WINDOW = 64

#: The four pre-registered channels, in fixed order.
CHANNELS: tuple[str, ...] = (
    "inter_trade_duration",
    "log_trade_size",
    "aggressor_sign",
    "tick_direction",
)
N_CHANNELS = len(CHANNELS)

MS_PER_MINUTE = 60_000
MS_PER_DAY = 24 * 3600_000

_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class DataError(RuntimeError):
    """Raised when a harvester window cannot be loaded."""


# ---------------------------------------------------------------------------
# Quantile normalisation (per node, per UTC day, per channel)
# ---------------------------------------------------------------------------

def rankdata_average(v: np.ndarray) -> np.ndarray:
    """Average ranks (1..n, ties share the mean rank) — own numpy copy."""
    v = np.asarray(v, dtype=np.float64)
    n = v.size
    if n == 0:
        return np.empty(0, dtype=np.float64)
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    inv = np.empty(n, dtype=np.int64)
    inv[order] = np.arange(n)
    obs = np.concatenate(([True], sv[1:] != sv[:-1]))
    dense = np.cumsum(obs)[inv]                      # 1-based tie-group id
    bounds = np.concatenate((np.nonzero(obs)[0], [n]))
    # average rank of tie group g = (first_idx + last_idx)/2 + 1 (0-based idx)
    return 0.5 * (bounds[dense - 1] + bounds[dense] + 1).astype(np.float64)


def quantile_normalize(v: np.ndarray) -> np.ndarray:
    """Rank -> uniform quantile transform u = rank/(n+1) in (0, 1).

    Destroys the marginal distribution (level, grid, clustering) of the
    channel while preserving its within-group temporal ORDER structure.
    """
    v = np.asarray(v, dtype=np.float64)
    if v.size == 0:
        return v.copy()
    return rankdata_average(v) / (v.size + 1.0)


def per_day_quantile_normalize(
    channels: np.ndarray, day_index: np.ndarray
) -> np.ndarray:
    """Apply ``quantile_normalize`` per (UTC day, channel) of ONE node.

    ``channels`` is (n_events, N_CHANNELS) raw channel values, ``day_index``
    (n_events,) integer day ids. Returns the normalised copy. This is the
    registered trivial-tell destroyer (registry H-17: Pro-Tag-Quantil-
    Normalisierung je Kanal/Node).
    """
    ch = np.asarray(channels, dtype=np.float64)
    day_index = np.asarray(day_index)
    out = np.empty_like(ch)
    for day in np.unique(day_index):
        sel = day_index == day
        for c in range(ch.shape[1]):
            out[sel, c] = quantile_normalize(ch[sel, c])
    return out


# ---------------------------------------------------------------------------
# Raw channel extraction
# ---------------------------------------------------------------------------

def tick_direction(price: np.ndarray) -> np.ndarray:
    """Tick rule with zero-tick carry: sign of the last non-zero price change.

    First event (no predecessor) and leading unchanged prices get 0.
    """
    p = np.asarray(price, dtype=np.float64)
    n = p.size
    out = np.zeros(n, dtype=np.float64)
    last = 0.0
    for i in range(1, n):
        d = p[i] - p[i - 1]
        if d > 0:
            last = 1.0
        elif d < 0:
            last = -1.0
        out[i] = last
    return out


def extract_raw_channels(
    ts_ms: np.ndarray, price: np.ndarray, size: np.ndarray, sign: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Raw per-event channel matrix for one node's chronological trade stream.

    Returns ``(ts_kept, channels, day_index)``:
      * ``ts_kept``   (n,)  event timestamps (ms) — first event of the stream
        is dropped (its inter-trade duration is undefined),
      * ``channels``  (n, 4) raw channel values in ``CHANNELS`` order,
      * ``day_index`` (n,)  UTC day id (epoch-days) per kept event.
    """
    ts_ms = np.asarray(ts_ms, dtype=np.int64)
    price = np.asarray(price, dtype=np.float64)
    size = np.asarray(size, dtype=np.float64)
    sign = np.asarray(sign, dtype=np.float64)
    if not (ts_ms.size == price.size == size.size == sign.size):
        raise ValueError("ts/price/size/sign length mismatch")
    if ts_ms.size < 2:
        raise DataError("need >= 2 trades for inter-trade durations")
    if np.any(np.diff(ts_ms) < 0):
        order = np.argsort(ts_ms, kind="mergesort")
        ts_ms, price, size, sign = ts_ms[order], price[order], size[order], sign[order]

    dur = np.diff(ts_ms).astype(np.float64)          # (n-1,)
    tick = tick_direction(price)[1:]
    log_size = np.log(np.maximum(size[1:], 1e-12))
    agg = sign[1:]
    channels = np.column_stack([dur, log_size, agg, tick])
    ts_kept = ts_ms[1:]
    day_index = (ts_kept // MS_PER_DAY).astype(np.int64)
    return ts_kept, channels, day_index


# ---------------------------------------------------------------------------
# Window construction
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class NodeWindows:
    """5-minute event windows of ONE node after per-day quantile normalisation.

    ``x``     (n_windows, N_CHANNELS, SEQ_LEN) float32, zero-padded.
    ``mask``  (n_windows, SEQ_LEN) bool, True = real event.
    ``dates`` (n_windows,) object array of YYYY-MM-DD (UTC) strings.
    ``n_events`` (n_windows,) valid event count per window (pre-truncation
                 count capped at SEQ_LEN).
    """

    exchange: str
    symbol: str
    x: np.ndarray
    mask: np.ndarray
    dates: np.ndarray
    n_events: np.ndarray


def _epoch_day_to_iso(day: int) -> str:
    return (datetime(1970, 1, 1, tzinfo=timezone.utc)
            + timedelta(days=int(day))).strftime("%Y-%m-%d")


def build_node_windows(
    ts_ms: np.ndarray,
    price: np.ndarray,
    size: np.ndarray,
    sign: np.ndarray,
    *,
    exchange: str,
    symbol: str,
    seq_len: int = SEQ_LEN,
    min_events: int = MIN_EVENTS_PER_WINDOW,
    window_minutes: int = WINDOW_MINUTES,
    normalize: bool = True,
) -> NodeWindows:
    """Full per-node pipeline: raw channels -> per-day quantile norm -> windows.

    Chronological 5-minute wall-clock buckets; a bucket becomes a window iff
    it has >= ``min_events`` events; truncated to the FIRST ``seq_len``
    events, zero-padded with a mask.

    ``normalize=False`` is a TEST-ONLY diagnostic escape hatch (registry
    H-17 builder-diagnostic duty): it skips the per-day quantile
    normalisation so the raw-channel windows can be compared against the
    normalised ones (see ``trivial_tell_probe_features`` +
    ``tests/unit/test_c17_venue.py``). The real gate pipeline always uses
    the default ``normalize=True``.
    """
    ts_kept, raw, day_index = extract_raw_channels(ts_ms, price, size, sign)
    norm = per_day_quantile_normalize(raw, day_index) if normalize else raw
    bucket = ts_kept // (window_minutes * MS_PER_MINUTE)

    xs: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    dates: list[str] = []
    counts: list[int] = []
    # buckets are contiguous runs in the chronological stream
    uniq, starts = np.unique(bucket, return_index=True)
    order = np.argsort(starts)
    uniq, starts = uniq[order], starts[order]
    ends = np.append(starts[1:], bucket.size)
    for b, s, e in zip(uniq, starts, ends):
        n_ev = int(e - s)
        if n_ev < min_events:
            continue
        take = min(n_ev, seq_len)
        w = np.zeros((N_CHANNELS, seq_len), dtype=np.float32)
        m = np.zeros(seq_len, dtype=bool)
        w[:, :take] = norm[s:s + take, :].T
        m[:take] = True
        xs.append(w)
        masks.append(m)
        dates.append(_epoch_day_to_iso(int(day_index[s])))
        counts.append(take)

    if not xs:
        raise DataError(
            f"{exchange}:{symbol}: no window with >= {min_events} events"
        )
    return NodeWindows(
        exchange=exchange,
        symbol=symbol,
        x=np.stack(xs),
        mask=np.stack(masks),
        dates=np.array(dates, dtype=object),
        n_events=np.array(counts, dtype=np.int64),
    )


# ---------------------------------------------------------------------------
# Trivial-tell diagnostic (registry builder duty)
# ---------------------------------------------------------------------------

def trivial_tell_probe_features(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Per-window per-channel masked mean + std summary features (n, 8).

    Deliberately COUNT-FREE (no event-count / pad-fraction feature): the
    encoder pools with a masked mean, so the honest diagnostic asks whether
    the VALUE distributions still carry the trivial tells. Used by the
    mandated builder diagnostic: before per-day quantile normalisation a
    simple classifier on these features separates venues that differ only in
    tick size / size clustering / activity level; after normalisation it
    must not.
    """
    x = np.asarray(x, dtype=np.float64)
    m = np.asarray(mask, dtype=np.float64)[:, None, :]     # (n, 1, L)
    cnt = np.maximum(m.sum(axis=2), 1.0)                   # (n, 1)
    mean = (x * m).sum(axis=2) / cnt                       # (n, C)
    var = ((x - mean[:, :, None]) ** 2 * m).sum(axis=2) / cnt
    return np.concatenate([mean, np.sqrt(var)], axis=1)


def simple_probe_accuracy(
    feats: np.ndarray, y: np.ndarray, *, seed: int = 42, train_frac: float = 0.7
) -> float:
    """Held-out accuracy of a simple linear probe on summary features.

    The diagnostic classifier of the trivial-tell check: numpy logistic
    regression on standardised features, deterministic split. ~0.5 = the
    tells are gone; >> 0.5 = a trivial tell survives.
    """
    from .contrastive import probe_predict, train_linear_probe  # own package

    feats = np.asarray(feats, dtype=np.float64)
    y = np.asarray(y, dtype=np.int64)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(feats.shape[0])
    n_tr = int(round(train_frac * feats.shape[0]))
    tr, te = idx[:n_tr], idx[n_tr:]
    model = train_linear_probe(feats[tr], y[tr], seed=seed)
    pred = probe_predict(feats[te], model)
    return float(np.mean(pred == y[te]))


# ---------------------------------------------------------------------------
# Read-only harvester loader (DuckDB)
# ---------------------------------------------------------------------------

def _date_list(start_date: str, end_date: str) -> list[str]:
    for s in (start_date, end_date):
        if not _DATE_RE.match(s):
            raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    a = datetime.strptime(start_date, "%Y-%m-%d")
    b = datetime.strptime(end_date, "%Y-%m-%d")
    if b < a:
        raise DataError(f"end_date {end_date} before start_date {start_date}")
    return [(a + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range((b - a).days + 1)]


def load_node_trades(
    base_dir: Path | str,
    exchange: str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    stream: str = "publicTrade",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load (ts_ms, price, size, sign) for one node from the harvester tree.

    Reads ``<base>/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet``
    read-only. Aggressor sign is extracted exchange-agnostically:
    ``side``/``S`` = 'buy'/'sell' (Bybit backfill/live short form) or the
    Binance aggTrade maker flag ``m`` (buyer-is-maker true -> aggressor
    SELL -> -1; false -> aggressor BUY -> +1). Rows without a resolvable
    price/size/sign are dropped loudly (counted), never silently defaulted.

    DAY-BATCHED (audit finding: resource-exhaustion) -- the ~100-day
    registered window is never fetched in ONE ``fetchall()`` call: one
    DuckDB query PER CALENDAR DAY (only that day's parquet partition),
    read via ``fetchnumpy()`` (columnar numpy arrays straight out of
    DuckDB, no per-row Python tuple/int/float boxing) instead of
    ``fetchall()`` + Python list comprehensions. This bounds peak Python
    memory to roughly ONE day's trade volume instead of the full
    registered window's (analogous to the per-day-bounded aggregation
    pattern in c12_frag/panel.py and c14_panellag/panel.py, adapted here
    to event-level data since the downstream per-day quantile
    normalisation — features.py — is itself computed per (node, UTC day)
    and needs no cross-day event data).
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    dates = _date_list(start_date, end_date)
    base = Path(base_dir)
    date_globs = {
        d: str(base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={d}" / "*.parquet")
        for d in dates
    }
    present_dates = [d for d in dates if list(Path(date_globs[d]).parent.glob("*.parquet"))]
    if not present_dates:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in "
            f"{dates[0]}..{dates[-1]} under {base}"
        )
    # SAME overall [start_ms, end_ms) bound as the original single-query
    # implementation -- applied per-day-query below so the UNION of the
    # per-day filtered results is numerically identical to the original
    # combined-file query's result.
    start_ms = int(datetime.strptime(dates[0], "%Y-%m-%d")
                   .replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(datetime.strptime(dates[-1], "%Y-%m-%d")
                 .replace(tzinfo=timezone.utc).timestamp() * 1000) + MS_PER_DAY
    sql_tmpl = """
        SELECT ts_exchange_ms,
               CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                             json_extract_string(payload_json,'$.p')) AS DOUBLE) AS price,
               CAST(COALESCE(json_extract_string(payload_json,'$.size'),
                             json_extract_string(payload_json,'$.v'),
                             json_extract_string(payload_json,'$.q')) AS DOUBLE) AS size,
               CASE
                 WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                     json_extract_string(payload_json,'$.S'))) = 'buy'  THEN 1
                 WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                     json_extract_string(payload_json,'$.S'))) = 'sell' THEN -1
                 WHEN lower(json_extract_string(payload_json,'$.m')) = 'true'  THEN -1
                 WHEN lower(json_extract_string(payload_json,'$.m')) = 'false' THEN 1
                 ELSE 0
               END AS sign
        FROM read_parquet({file}, hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL
          AND ts_exchange_ms >= {start_ms} AND ts_exchange_ms < {end_ms}
        ORDER BY ts_exchange_ms
    """
    def _col_f64(col: Any) -> np.ndarray:
        # fetchnumpy() returns a numpy.ma.MaskedArray (NOT a plain array
        # with NaN) for a nullable column with NULLs present -- plain
        # np.asarray() on a MaskedArray silently exposes the UNDERLYING
        # (garbage) fill data instead of NaN, which would corrupt the
        # good-row mask below. Must go through .filled(nan) explicitly.
        if isinstance(col, np.ma.MaskedArray):
            return col.filled(np.nan).astype(np.float64)
        return np.asarray(col, dtype=np.float64)

    ts_parts: list[np.ndarray] = []
    price_parts: list[np.ndarray] = []
    size_parts: list[np.ndarray] = []
    sign_parts: list[np.ndarray] = []
    n_days_used = 0
    con = duckdb.connect()
    try:
        for d in present_dates:
            file_expr = "'" + date_globs[d].replace("'", "''") + "'"
            sql = sql_tmpl.format(file=file_expr, start_ms=start_ms, end_ms=end_ms)
            cols = con.execute(sql).fetchnumpy()
            n = int(cols["ts_exchange_ms"].size)
            if n == 0:
                continue
            n_days_used += 1
            # ts_exchange_ms is filtered IS NOT NULL in SQL -> plain int64
            # ndarray from fetchnumpy(), never a MaskedArray.
            ts_parts.append(np.asarray(cols["ts_exchange_ms"], dtype=np.int64))
            price_parts.append(_col_f64(cols["price"]))
            size_parts.append(_col_f64(cols["size"]))
            sign_parts.append(_col_f64(cols["sign"]))
    finally:
        con.close()
    if not ts_parts:
        raise DataError(f"{exchange}/{symbol}: 0 rows in {dates[0]}..{dates[-1]}")
    ts = np.concatenate(ts_parts)
    price = np.concatenate(price_parts)
    size = np.concatenate(size_parts)
    sign = np.concatenate(sign_parts)
    good = (np.isfinite(price) & (price > 0.0)
            & np.isfinite(size) & (size > 0.0) & (sign != 0.0))
    n_drop = int(np.sum(~good))
    if n_drop:
        print(f"[c17_venue] {exchange}:{symbol}: dropped {n_drop}/{ts.size} "
              f"rows without resolvable price/size/sign", file=sys.stderr, flush=True)
    ts, price, size, sign = ts[good], price[good], size[good], sign[good]
    if ts.size < 2:
        raise DataError(f"{exchange}/{symbol}: < 2 usable trades")
    print(f"[c17_venue] {exchange}:{symbol} {dates[0]}..{dates[-1]}: "
          f"{ts.size} usable trades ({n_days_used} day-batched queries)",
          file=sys.stderr, flush=True)
    return ts, price, size, sign


def load_panel(
    base_dir: Path | str,
    symbols: tuple[str, ...],
    start_date: str,
    end_date: str,
    *,
    exchanges: tuple[str, ...] = DEFAULT_EXCHANGES,
    seq_len: int = SEQ_LEN,
    min_events: int = MIN_EVENTS_PER_WINDOW,
) -> list[NodeWindows]:
    """Load + window all 10 nodes (read-only). Raises DataError per node."""
    nodes: list[NodeWindows] = []
    for ex in exchanges:
        for sym in symbols:
            ts, price, size, sign = load_node_trades(base_dir, ex, sym, start_date, end_date)
            nodes.append(build_node_windows(
                ts, price, size, sign, exchange=ex, symbol=sym,
                seq_len=seq_len, min_events=min_events,
            ))
    return nodes


__all__ = [
    "CHANNELS",
    "DEFAULT_END_DATE",
    "DEFAULT_EXCHANGES",
    "DEFAULT_START_DATE",
    "DEFAULT_SYMBOLS",
    "MIN_EVENTS_PER_WINDOW",
    "N_CHANNELS",
    "SEQ_LEN",
    "WINDOW_MINUTES",
    "DataError",
    "NodeWindows",
    "build_node_windows",
    "extract_raw_channels",
    "load_node_trades",
    "load_panel",
    "per_day_quantile_normalize",
    "quantile_normalize",
    "rankdata_average",
    "simple_probe_accuracy",
    "tick_direction",
    "trivial_tell_probe_features",
]
