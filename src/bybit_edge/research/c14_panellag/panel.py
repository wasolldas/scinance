"""12-node cross-venue 1s-panel construction for the H-14 PANEL-LAG gate.

Builds, per pre-registered calendar window (registry H-14, Welle 5), the
12-node 1-second last-price panel and its log-return matrix:

  * Nodes (registry H-14, verbatim): BTC/ETH x {Bybit, Binance,
    Deribit-PERPETUAL} + SOL/BNB/XRP x {Bybit, Binance} = 12 nodes,
    ``publicTrade`` resampled to the standard 1s grid.
  * 1s bars: LAST trade price per ``[t, t+1s)``, forward-fill capped at
    ``FFILL_CAP_SECONDS`` (builder-fixed BEFORE any run; beyond the cap the
    second stays NaN and every sample whose input window or target horizon
    touches it is dropped for ALL nodes — the panel model needs all 12).
  * Deribit storage notation is ``BTC-PERPETUAL``/``ETH-PERPETUAL``
    (DATASET.md SRC-10/11); own copy of the mapping — research packages do
    not cross-import (registry paragraph 8.2 convention).

Loader style follows the read-only DuckDB Hive pattern of ``c12_frag.panel``
(price-only, exchange-agnostic ``COALESCE($.price, $.p)`` extraction,
aggregation INSIDE DuckDB so tick windows never enter Python memory), but on
the 1s grid instead of minutes. No write access to the harvester tree
(Schutzgut).

Causality helpers (``valid_sample_indices``, ``target_sign_labels``) define
the SINGLE source of truth for the no-lookahead window/target construction:
a sample anchored at grid index t uses returns ``r[t-lookback+1 .. t]`` as
input (only data <= t) and the sign of the summed log-return over
``r[t+1 .. t+horizon]`` (strictly after t) as target.

KAPITALFREI: pure price resampling / synchronisation. No friction, bps,
PnL, Sharpe logic anywhere. numpy + duckdb (read-only) only.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

#: Registered 12-node panel (registry H-14): (exchange, internal Bybit-notation
#: symbol). Symbol-major order following the registry text.
DEFAULT_NODES: tuple[tuple[str, str], ...] = (
    ("bybit", "BTCUSDT"),
    ("binance", "BTCUSDT"),
    ("deribit", "BTCUSDT"),
    ("bybit", "ETHUSDT"),
    ("binance", "ETHUSDT"),
    ("deribit", "ETHUSDT"),
    ("bybit", "SOLUSDT"),
    ("binance", "SOLUSDT"),
    ("bybit", "XRPUSDT"),
    ("binance", "XRPUSDT"),
    ("bybit", "BNBUSDT"),
    ("binance", "BNBUSDT"),
)

#: Deribit perp instrument notation (own copy — no cross-package import).
DERIBIT_SYMBOL_MAP: dict[str, str] = {
    "BTCUSDT": "BTC-PERPETUAL",
    "ETHUSDT": "ETH-PERPETUAL",
}

#: Registered grid (registry H-14: publicTrade auf 1s-Grid resampled).
GRID_SECONDS = 1
SECONDS_PER_DAY = 86_400
MS_PER_SECOND = 1_000
MS_PER_DAY = 24 * 3_600_000

#: Builder-fixed BEFORE any run (registry is silent; documented README_H14):
#: max forward-fill gap on the 1s grid. Beyond it the second stays NaN.
FFILL_CAP_SECONDS = 60

#: Registered target horizon (registry H-14: Vorzeichen der naechsten
#: 10s-Rendite).
TARGET_HORIZON_SECONDS = 10

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: Storage symbols may contain a hyphen (Deribit ``BTC-PERPETUAL``).
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


class DataError(RuntimeError):
    """Raised when a harvester window cannot be loaded."""


def map_exchange_symbol(exchange: str, symbol: str) -> str:
    """Storage-partition symbol for (exchange, internal Bybit-notation symbol).

    Bybit/Binance share the USDT-perp notation; Deribit uses
    ``<BASE>-PERPETUAL``. Own copy of the c12_frag mapping (no cross-import
    between research packages — repo convention).
    """
    if exchange == "deribit":
        mapped = DERIBIT_SYMBOL_MAP.get(symbol)
        if mapped is None:
            base = symbol[:-4] if symbol.endswith("USDT") else symbol
            mapped = f"{base}-PERPETUAL"
        return mapped
    return symbol


def node_base(symbol: str) -> str:
    """Base asset of an internal symbol (``BTCUSDT`` -> ``BTC``).

    Also accepts the Deribit storage form (``BTC-PERPETUAL`` -> ``BTC``).
    """
    if symbol.endswith("USDT"):
        return symbol[:-4]
    if symbol.endswith("-PERPETUAL"):
        return symbol[: -len("-PERPETUAL")]
    return symbol


def _midnight_ms(day: str) -> int:
    y, m, d = (int(x) for x in day.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _date_list(start_date: str, end_date: str) -> list[str]:
    """Inclusive ``YYYY-MM-DD`` list from ``start_date`` to ``end_date``."""
    for s in (start_date, end_date):
        if not _DATE_RE.match(s):
            raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    y0, m0, d0 = (int(x) for x in start_date.split("-"))
    y1, m1, d1 = (int(x) for x in end_date.split("-"))
    a, b = date(y0, m0, d0), date(y1, m1, d1)
    if b < a:
        raise DataError(f"end_date {end_date} before start_date {start_date}")
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def load_seconds_last_price(
    base_dir: Path | str,
    exchange: str,
    storage_symbol: str,
    dates: list[str],
    *,
    stream: str = "publicTrade",
) -> np.ndarray:
    """1s last-price series over the date list (read-only harvester tree).

    Reads ``<base>/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet``
    and aggregates INSIDE DuckDB to the last trade price per ``[t, t+1s)``
    second (``max_by(price, ts_exchange_ms)``). Price extraction is
    exchange-agnostic via ``COALESCE($.price, $.p)`` — covers the Bybit
    backfill (``price``), Binance aggTrades (``p``) and Deribit (``price``)
    payload forms (same rationale/limits as ``c12_frag.panel``, incl. the
    documented Bybit LIVE multi-trade-envelope non-coverage: such rows fail
    the ``IS NOT NULL`` filter loudly instead of being silently wrong).

    Returns a ``(len(dates) * 86400,)`` float64 array of last prices, NaN
    where the second has no trade. Read-only — never writes into the tree.
    """
    import duckdb

    if not _SYMBOL_RE.match(storage_symbol):
        raise DataError(f"invalid symbol: {storage_symbol!r}")
    if not dates:
        raise DataError("empty date list")
    base = Path(base_dir)
    globs = [
        str(base / "raw" / exchange / stream / f"symbol={storage_symbol}" / f"date={d}" / "*.parquet")
        for d in dates
    ]
    present = [g for g in globs if list(Path(g).parent.glob("*.parquet"))]
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{storage_symbol} in "
            f"{dates[0]}..{dates[-1]} under {base}"
        )
    start_ms = _midnight_ms(dates[0])
    end_ms = _midnight_ms(dates[-1]) + MS_PER_DAY
    second0 = start_ms // MS_PER_SECOND
    n_seconds = len(dates) * SECONDS_PER_DAY
    file_list = "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in present) + "]"
    sql = f"""
        SELECT CAST(ts_exchange_ms // {MS_PER_SECOND} AS BIGINT) AS second_idx,
               max_by(
                 CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                               json_extract_string(payload_json,'$.p')) AS DOUBLE),
                 ts_exchange_ms) AS last_price
        FROM read_parquet({file_list}, hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL
          AND ts_exchange_ms >= {start_ms} AND ts_exchange_ms < {end_ms}
          AND COALESCE(json_extract_string(payload_json,'$.price'),
                       json_extract_string(payload_json,'$.p')) IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    out = np.full(n_seconds, np.nan, dtype=np.float64)
    n_used = 0
    for second_idx, price in rows:
        off = int(second_idx) - second0
        if 0 <= off < n_seconds and price is not None and np.isfinite(price) and price > 0.0:
            out[off] = float(price)
            n_used += 1
    if n_used == 0:
        raise DataError(
            f"{exchange}/{storage_symbol} {dates[0]}..{dates[-1]}: 0 usable 1s bars"
        )
    print(
        f"[c14_panellag] {exchange}/{storage_symbol} {dates[0]}..{dates[-1]}: "
        f"{n_used}/{n_seconds} seconds with trades",
        file=sys.stderr, flush=True,
    )
    return out


def ffill_seconds_capped(col: np.ndarray, max_gap: int = FFILL_CAP_SECONDS) -> np.ndarray:
    """Forward-fill NaN seconds by at most ``max_gap`` consecutive seconds.

    Vectorised (windows are millions of seconds long). A gap longer than the
    cap stays NaN beyond the cap. Leading NaNs stay NaN.
    """
    x = np.asarray(col, dtype=np.float64)
    n = x.size
    if n == 0:
        return x.copy()
    valid = np.isfinite(x)
    # index of the most recent valid observation at or before each position
    idx = np.where(valid, np.arange(n), -1)
    idx = np.maximum.accumulate(idx)
    out = np.full(n, np.nan, dtype=np.float64)
    has_src = idx >= 0
    gap = np.arange(n) - idx  # 0 at a valid second, k for the k-th NaN after
    take = has_src & (gap <= max_gap)
    out[take] = x[idx[take]]
    return out


def log_returns(prices: np.ndarray) -> np.ndarray:
    """1s log-returns; index t holds ``log p[t] - log p[t-1]``; r[0] = NaN."""
    p = np.asarray(prices, dtype=np.float64)
    r = np.full(p.shape, np.nan, dtype=np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        lp = np.log(p)
    r[1:] = lp[1:] - lp[:-1]
    return r


@dataclass(slots=True)
class PanelWindow:
    """One pre-registered calendar window of the 12-node 1s panel.

    ``returns``      : (N, T) float32 1s log-returns; NaN = invalid second.
    ``node_labels``  : e.g. ``bybit:BTCUSDT`` .. ``deribit:ETH-PERPETUAL``
                       (storage notation in the label, like c12_frag).
    ``node_bases``   : base asset per node (``BTC``/``ETH``/``SOL``/...).
    ``coverage``     : (N,) share of finite return seconds per node.
    """

    label: str
    start_date: str
    end_date: str
    node_labels: tuple[str, ...]
    node_exchanges: tuple[str, ...]
    node_bases: tuple[str, ...]
    returns: np.ndarray
    coverage: tuple[float, ...]

    @property
    def n_nodes(self) -> int:
        return len(self.node_labels)

    @property
    def n_seconds(self) -> int:
        return int(self.returns.shape[1])


def build_window(
    base_dir: Path | str,
    start_date: str,
    end_date: str,
    *,
    nodes: tuple[tuple[str, str], ...] = DEFAULT_NODES,
    label: str = "",
    ffill_cap: int = FFILL_CAP_SECONDS,
) -> PanelWindow:
    """Load + synchronise one pre-registered calendar window (read-only).

    Raises ``DataError`` if ANY node cannot be loaded (the cross-attention
    panel needs all 12 nodes).
    """
    dates = _date_list(start_date, end_date)
    n_seconds = len(dates) * SECONDS_PER_DAY
    node_labels: list[str] = []
    node_exchanges: list[str] = []
    node_bases: list[str] = []
    ret = np.full((len(nodes), n_seconds), np.nan, dtype=np.float32)
    coverage: list[float] = []
    for j, (ex, sym) in enumerate(nodes):
        storage = map_exchange_symbol(ex, sym)
        prices = load_seconds_last_price(base_dir, ex, storage, dates)
        prices = ffill_seconds_capped(prices, ffill_cap)
        r = log_returns(prices)
        ret[j, :] = r.astype(np.float32)
        node_labels.append(f"{ex}:{storage}")
        node_exchanges.append(ex)
        node_bases.append(node_base(sym))
        coverage.append(float(np.mean(np.isfinite(r))))
    return PanelWindow(
        label=label or f"{start_date}..{end_date}",
        start_date=start_date,
        end_date=end_date,
        node_labels=tuple(node_labels),
        node_exchanges=tuple(node_exchanges),
        node_bases=tuple(node_bases),
        returns=ret,
        coverage=tuple(coverage),
    )


# ---------------------------------------------------------------------------
# Causal window/target construction (single source of truth, no lookahead)
# ---------------------------------------------------------------------------

def valid_sample_indices(
    returns: np.ndarray,
    lookback: int,
    horizon: int,
    *,
    sample_stride: int = 1,
    t_start: int | None = None,
    t_end: int | None = None,
) -> np.ndarray:
    """Anchor indices t with a fully finite input window AND target horizon.

    A sample anchored at t uses ``returns[:, t-lookback+1 .. t]`` as input
    (inclusive of t, nothing after t) and ``returns[:, t+1 .. t+horizon]``
    for the target — for EVERY node (the panel model consumes all 12).
    Candidates are ``t = t_start + k*sample_stride`` inside
    ``[max(t_start, lookback-1), min(t_end, T-horizon-1)]``.
    """
    r = np.asarray(returns)
    n_nodes, t_total = r.shape
    lo = max(lookback - 1, 0 if t_start is None else int(t_start))
    hi = min(t_total - horizon - 1, t_total - 1 if t_end is None else int(t_end))
    if hi < lo:
        return np.zeros(0, dtype=np.int64)
    cand = np.arange(lo, hi + 1, max(1, int(sample_stride)), dtype=np.int64)
    finite = np.isfinite(r).all(axis=0)  # (T,) all nodes finite at second t
    # prefix sums for O(1) "all finite in [a, b]" queries
    csum = np.concatenate([[0], np.cumsum(finite.astype(np.int64))])

    def _all_finite(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return (csum[b + 1] - csum[a]) == (b - a + 1)

    ok_in = _all_finite(cand - lookback + 1, cand)
    ok_tg = _all_finite(cand + 1, cand + horizon)
    return cand[ok_in & ok_tg]


def target_sign_labels(
    returns: np.ndarray, anchors: np.ndarray, horizon: int
) -> tuple[np.ndarray, np.ndarray]:
    """Binary sign targets of the next-``horizon``-seconds log-return.

    Returns ``(labels, mask)``, each ``(n_samples, n_nodes)``:
    ``labels[k, i] = 1`` iff ``sum(returns[i, t+1 .. t+horizon]) > 0`` for
    anchor ``t = anchors[k]``; exactly-zero forward returns are masked out
    (``mask = 0``) instead of being forced into a class (builder-fixed,
    documented — sign of zero carries no direction information).
    Uses ONLY data strictly after the anchor (no lookahead).
    """
    r = np.asarray(returns, dtype=np.float64)
    csum = np.concatenate(
        [np.zeros((r.shape[0], 1)), np.nancumsum(r, axis=1)], axis=1
    )
    a = np.asarray(anchors, dtype=np.int64)
    fwd = (csum[:, a + horizon + 1] - csum[:, a + 1]).T  # (n_samples, n_nodes)
    labels = (fwd > 0.0).astype(np.float32)
    mask = (fwd != 0.0).astype(np.float32)
    return labels, mask


def train_oos_split(
    n_anchors_range: tuple[int, int],
    *,
    train_frac: float = 0.7,
    embargo: int = 0,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Chronological train/OOS split of a grid-index range with an embargo.

    ``n_anchors_range = (t_lo, t_hi)`` inclusive grid-index bounds. Returns
    ``((train_lo, train_hi), (oos_lo, oos_hi))`` with an ``embargo``-second
    gap between train end and OOS start (prevents input/target overlap
    between the two segments — no leakage).
    """
    t_lo, t_hi = int(n_anchors_range[0]), int(n_anchors_range[1])
    span = t_hi - t_lo + 1
    cut = t_lo + int(span * train_frac) - 1
    return (t_lo, cut), (min(cut + 1 + int(embargo), t_hi + 1), t_hi)


def circular_shift_rows(
    returns: np.ndarray, shifts: dict[int, int]
) -> np.ndarray:
    """Copy of ``returns`` with row j circularly shifted by ``shifts[j]``.

    Circular shift preserves each node's marginal distribution and
    autocorrelation but destroys its temporal alignment with all OTHER
    nodes (registry H-14 surrogate). Targets are later computed from the
    SHIFTED series, so each node's own feature->target alignment stays
    intact — only cross-node information is destroyed.
    """
    out = np.array(returns, copy=True)
    for j, s in shifts.items():
        out[j, :] = np.roll(returns[j, :], int(s))
    return out


__all__ = [
    "DEFAULT_NODES",
    "DERIBIT_SYMBOL_MAP",
    "FFILL_CAP_SECONDS",
    "GRID_SECONDS",
    "SECONDS_PER_DAY",
    "TARGET_HORIZON_SECONDS",
    "DataError",
    "PanelWindow",
    "build_window",
    "circular_shift_rows",
    "ffill_seconds_capped",
    "load_seconds_last_price",
    "log_returns",
    "map_exchange_symbol",
    "node_base",
    "target_sign_labels",
    "train_oos_split",
    "valid_sample_indices",
]
