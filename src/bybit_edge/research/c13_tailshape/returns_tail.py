"""Physical tail side of H-13: xi_P via POT + GPD-MLE + block bootstrap + Hill.

Data source: read-only harvester Hive tree (``data/harvest/raw/bybit/
publicTrade/symbol=<SYM>/date=<d>/*.parquet``), same backfill/live JSON
payload forms as ``c01_ofi_sign.oos.load_harvest_window``. Trailing 60
trading days of 1-min log-returns per snapshot day (days strictly BEFORE the
snapshot day — no overlap with the 08:00 UTC options snapshot, no lookahead).

Methodology (pre-registered, registry H-13, non-negotiable):
  * POT threshold u_P = empirical 99.5% quantile of the 1-min LOSSES
    (loss = -log-return, left return tail) over the trailing 60 days. FIXED —
    no discretionary mean-excess choice. A mean-excess diagnostic is computed
    as NON-adjudicating secondary info only.
  * GPD-MLE via ``scipy.stats.genpareto.fit`` (loc pinned at 0 on excesses).
  * SE via block bootstrap: 60-min blocks (60 consecutive 1-min returns),
    500 reps, threshold re-estimated per replicate.
  * Hill estimator as an independent cross-check with k = number of
    exceedances over u_P.
"""
from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import genpareto

#: Pre-registered POT threshold quantile (registry H-13, fixed).
POT_QUANTILE = 0.995
#: Block length for the block bootstrap: 60 one-minute returns = 60 min.
BLOCK_LEN_MIN = 60
#: Pre-registered bootstrap repetitions.
N_BOOTSTRAP = 500
#: Trailing window length in trading days (crypto: calendar days).
TRAILING_DAYS = 60
#: Robustness floor: minimum days with data inside the trailing window.
MIN_TRAILING_DAYS = 30
#: Minimum number of POT exceedances for a GPD fit.
MIN_EXCEEDANCES = 20

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_]+$")


class DataError(RuntimeError):
    """Raised when a harvester window cannot be loaded or fitted."""


def _parse_date(s: str) -> date:
    if not _DATE_RE.match(s):
        raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def trailing_dates(snapshot_date: str, n_days: int) -> list[str]:
    """The ``n_days`` calendar dates strictly BEFORE ``snapshot_date`` (asc)."""
    d0 = _parse_date(snapshot_date)
    return [(d0 - timedelta(days=i)).isoformat() for i in range(n_days, 0, -1)]


# ----------------------------------------------------------------------------
# Harvester loader (read-only) + 1-min log-returns
# ----------------------------------------------------------------------------

def one_min_log_returns(ts_ms: np.ndarray, price: np.ndarray) -> np.ndarray:
    """1-min log-returns from a tick series (last price per minute bin).

    Bins ticks to UTC minutes, takes the LAST price of each non-empty minute
    and returns log-returns between CONSECUTIVE minutes only (minute gaps do
    not produce a return — a multi-minute gap must not masquerade as a 1-min
    move and inflate the tail).
    """
    ts = np.asarray(ts_ms, dtype=np.float64)
    px = np.asarray(price, dtype=np.float64)
    good = np.isfinite(ts) & np.isfinite(px) & (px > 0)
    ts, px = ts[good], px[good]
    if ts.size < 2:
        return np.zeros(0)
    order = np.argsort(ts, kind="stable")
    ts, px = ts[order], px[order]
    minute = (ts // 60_000).astype(np.int64)
    # last tick per minute: positions where the NEXT minute differs
    last = np.append(minute[1:] != minute[:-1], True)
    m_u = minute[last]
    p_u = px[last]
    if m_u.size < 2:
        return np.zeros(0)
    contiguous = np.diff(m_u) == 1
    r = np.diff(np.log(p_u))
    return r[contiguous]


def load_returns_window(
    base_dir: Path | str,
    symbol: str,
    snapshot_date: str,
    *,
    n_days: int = TRAILING_DAYS,
    min_days: int = MIN_TRAILING_DAYS,
    exchange: str = "bybit",
    stream: str = "publicTrade",
) -> tuple[np.ndarray, dict[str, Any]]:
    """Load trailing 1-min log-returns for one snapshot day (read-only).

    Reads ``base/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet``
    for the ``n_days`` dates strictly before ``snapshot_date`` via DuckDB
    (backfill ``price`` key with fallback to the live ``p`` key), builds the
    1-min last-price series and its log-returns. Missing dates are tolerated
    down to ``min_days`` present dates; below that a :class:`DataError` is
    raised. Returns ``(returns, meta)``.
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    base = Path(base_dir)
    dates = trailing_dates(snapshot_date, n_days)
    present: list[str] = []
    globs: list[str] = []
    for d in dates:
        p = base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={d}"
        if p.is_dir() and list(p.glob("*.parquet")):
            present.append(d)
            globs.append(str(p / "*.parquet"))
    if len(present) < min_days:
        raise DataError(
            f"trailing window {symbol}@{snapshot_date}: only {len(present)} of "
            f"{n_days} dates present (< min_days={min_days}) under {base}"
        )
    file_list = "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in globs) + "]"
    sql = f"""
        SELECT ts_exchange_ms AS ts,
               CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                             json_extract_string(payload_json,'$.p')) AS DOUBLE) AS price
        FROM read_parquet({file_list}, hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL
        ORDER BY ts_exchange_ms
    """
    con = duckdb.connect()
    try:
        ts, px = (np.asarray(c) for c in zip(*con.execute(sql).fetchall()))
    except ValueError as exc:  # zero rows -> zip(*) fails
        raise DataError(f"trailing window {symbol}@{snapshot_date}: 0 rows") from exc
    finally:
        con.close()
    r = one_min_log_returns(ts.astype(np.float64), px.astype(np.float64))
    if r.size < 2 * BLOCK_LEN_MIN:
        raise DataError(
            f"trailing window {symbol}@{snapshot_date}: only {r.size} 1-min returns"
        )
    meta = {
        "symbol": symbol,
        "snapshot_date": snapshot_date,
        "n_days_requested": n_days,
        "n_days_present": len(present),
        "first_date": present[0],
        "last_date": present[-1],
        "n_returns": int(r.size),
    }
    print(
        f"[h13] returns {symbol}@{snapshot_date}: {r.size} 1-min returns over "
        f"{len(present)}/{n_days} days ({present[0]}..{present[-1]})",
        file=sys.stderr, flush=True,
    )
    return r, meta


# ----------------------------------------------------------------------------
# POT / GPD-MLE / Hill / block bootstrap
# ----------------------------------------------------------------------------

@dataclass(slots=True)
class GpdPotFit:
    """One POT + GPD-MLE fit on 1-min losses."""

    xi: float
    beta: float
    u: float
    n_exceedances: int
    n_losses: int
    quantile: float = POT_QUANTILE

    def as_dict(self) -> dict[str, Any]:
        return {
            "xi": float(self.xi),
            "beta": float(self.beta),
            "u": float(self.u),
            "n_exceedances": int(self.n_exceedances),
            "n_losses": int(self.n_losses),
            "pot_quantile": float(self.quantile),
        }


def fit_gpd_pot(returns: np.ndarray, *, quantile: float = POT_QUANTILE) -> GpdPotFit:
    """POT + GPD-MLE on the loss tail (loss = -return, i.e. LEFT return tail).

    Threshold u = empirical ``quantile`` of the losses (pre-registered 99.5%,
    fixed). GPD fitted by MLE on the excesses with loc pinned at 0.
    """
    losses = -np.asarray(returns, dtype=np.float64)
    losses = losses[np.isfinite(losses)]
    if losses.size < 100:
        raise DataError(f"too few returns for POT fit: {losses.size}")
    u = float(np.quantile(losses, quantile))
    exc = losses[losses > u] - u
    if exc.size < MIN_EXCEEDANCES:
        raise DataError(f"too few POT exceedances: {exc.size} (u={u:g})")
    xi, _loc, beta = genpareto.fit(exc, floc=0.0)
    return GpdPotFit(
        xi=float(xi), beta=float(beta), u=u,
        n_exceedances=int(exc.size), n_losses=int(losses.size), quantile=quantile,
    )


def hill_estimator(returns: np.ndarray, *, quantile: float = POT_QUANTILE) -> tuple[float, int]:
    """Hill tail-index estimate on the losses with k = #exceedances over u_P.

    Independent cross-check (registry H-13). Uses the SAME threshold u_P (the
    99.5% loss quantile), so k is exactly the number of POT exceedances:
    xi_Hill = (1/k) * sum(log(L_i / u_P)) over the losses L_i > u_P. Requires
    u_P > 0 (heavy-loss regime); returns ``(nan, k)`` otherwise — the caller
    treats a non-finite Hill estimate as neutral (no contradiction).
    """
    losses = -np.asarray(returns, dtype=np.float64)
    losses = losses[np.isfinite(losses)]
    if losses.size < 100:
        return float("nan"), 0
    u = float(np.quantile(losses, quantile))
    tail = losses[losses > u]
    k = int(tail.size)
    if u <= 0.0 or k < MIN_EXCEEDANCES:
        return float("nan"), k
    return float(np.mean(np.log(tail / u))), k


def mean_excess_diagnostic(
    returns: np.ndarray,
    quantiles: tuple[float, ...] = (0.985, 0.99, 0.9925, 0.995, 0.9975),
) -> list[dict[str, float]]:
    """NON-adjudicating mean-excess diagnostic (secondary info only).

    The POT threshold stays the pre-registered 99.5% quantile regardless of
    this table (registry H-13: no discretionary mean-excess choice).
    """
    losses = -np.asarray(returns, dtype=np.float64)
    losses = losses[np.isfinite(losses)]
    out: list[dict[str, float]] = []
    for q in quantiles:
        u = float(np.quantile(losses, q))
        exc = losses[losses > u] - u
        out.append({
            "quantile": float(q),
            "u": u,
            "mean_excess": float(np.mean(exc)) if exc.size else float("nan"),
            "n_exceedances": int(exc.size),
        })
    return out


def block_bootstrap_xi(
    returns: np.ndarray,
    *,
    n_bootstrap: int = N_BOOTSTRAP,
    block_len: int = BLOCK_LEN_MIN,
    quantile: float = POT_QUANTILE,
    seed: int = 42,
) -> np.ndarray:
    """Block bootstrap of the POT/GPD xi (60-min blocks, threshold refit).

    Resamples non-overlapping-length blocks of ``block_len`` consecutive 1-min
    returns with replacement to the original length and refits the FULL POT
    pipeline (threshold quantile + GPD-MLE) per replicate. Failed replicates
    yield NaN (dropped downstream). Deterministic under ``seed``.
    """
    r = np.asarray(returns, dtype=np.float64)
    n = r.size
    if n < 2 * block_len:
        raise DataError(f"too few returns for block bootstrap: {n}")
    rng = np.random.default_rng(seed)
    n_blocks = int(math.ceil(n / block_len))
    out = np.full(n_bootstrap, np.nan)
    for b in range(n_bootstrap):
        starts = rng.integers(0, n - block_len + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block_len)[None, :]).ravel()[:n]
        try:
            out[b] = fit_gpd_pot(r[idx], quantile=quantile).xi
        except (DataError, ValueError):
            continue
    return out


@dataclass(slots=True)
class XiPResult:
    """xi_P estimate for one (symbol, snapshot day) cell."""

    fit: GpdPotFit
    xi_boot: np.ndarray
    xi_hill: float
    hill_k: int
    mean_excess: list[dict[str, float]] = field(default_factory=list)

    @property
    def xi(self) -> float:
        return self.fit.xi

    @property
    def xi_se(self) -> float:
        b = self.xi_boot[np.isfinite(self.xi_boot)]
        return float(np.std(b, ddof=1)) if b.size > 1 else float("nan")

    def as_dict(self) -> dict[str, Any]:
        b = self.xi_boot[np.isfinite(self.xi_boot)]
        return {
            **self.fit.as_dict(),
            "xi_se_bootstrap": self.xi_se,
            "n_bootstrap_valid": int(b.size),
            "xi_hill": float(self.xi_hill) if math.isfinite(self.xi_hill) else None,
            "hill_k": int(self.hill_k),
            "mean_excess_diagnostic_secondary": self.mean_excess,
        }


def estimate_xi_p(
    returns: np.ndarray,
    *,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    quantile: float = POT_QUANTILE,
    block_len: int = BLOCK_LEN_MIN,
) -> XiPResult:
    """Full xi_P pipeline: POT/GPD-MLE + 60-min block bootstrap + Hill."""
    fit = fit_gpd_pot(returns, quantile=quantile)
    boot = block_bootstrap_xi(
        returns, n_bootstrap=n_bootstrap, block_len=block_len,
        quantile=quantile, seed=seed,
    )
    xi_hill, k = hill_estimator(returns, quantile=quantile)
    return XiPResult(
        fit=fit, xi_boot=boot, xi_hill=xi_hill, hill_k=k,
        mean_excess=mean_excess_diagnostic(returns),
    )
