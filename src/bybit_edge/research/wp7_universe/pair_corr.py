"""WP-7 -- ``rho(BTC,ETH)`` on 30-minute returns from the WP-0 bar cache.

PRD 4.1 section 1 / "Zusaetzlich, aus dem WP-0-Bar-Cache": the 30-minute
return correlation between BTC and ETH is MEASURED here (input to the A2
power line, previously an unmeasured [sek] 0.8 guess). Reads ONLY the
existing WP-0 minute-bar cache (``bybit_edge.research.bar_cache``,
immutable, manifest-DONE-gated) via ``load_minute_bars`` -- never touches
``data/harvest``, never writes to the bar cache.

Deterministic aggregation to 30-minute closes: ``minute_idx // 30`` buckets
the (already order-independent) 1-minute bars, the bucket's close is
``px_last`` of its LAST minute (max ``minute_idx`` in the bucket) -- a
scan-order-independent aggregate, same discipline ``bar_cache.py`` itself
uses. Log returns are taken only across CONSECUTIVE buckets (a gap never
manufactures a return across missing data); BTC and ETH are then aligned
on their COMMON bucket index before any statistic is computed.

Pearson and Spearman correlation are reported together with a block
bootstrap CI -- block = 1 UTC day = 48 consecutive 30-minute buckets
(spec: "Block = 1 Tag"; the block partitions the ALIGNED return series by
position, not by wall-clock day boundary, since gaps can shift the
alignment -- a documented simplification, immaterial once the aligned
series is materially gap-free). The bootstrap seed is a MANDATORY output
artifact (DEC-53 style, same discipline as ``null_ic.py``): no seed, no
citable CI.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .pit_universe import spearman_rank_ic

__all__ = [
    "BUCKET_MINUTES", "BLOCK_BUCKETS", "N_BOOTSTRAP_DEFAULT",
    "bucket_closes", "log_returns", "align_pair", "pearson_corr",
    "block_bootstrap_ci", "compute_pair_correlation", "write_artifacts",
    "read_artifacts",
]

#: 30-minute buckets (spec: "30-Minuten-Renditen").
BUCKET_MINUTES = 30

#: "Block = 1 Tag" = 24h / 30min = 48 consecutive buckets.
BLOCK_BUCKETS = 48

N_BOOTSTRAP_DEFAULT = 1000


def bucket_closes(bars: dict[str, np.ndarray]) -> dict[int, float]:
    """1-minute bars (``bar_cache.load_minute_bars`` output) -> ``{bucket:
    close}``, one close per 30-minute UTC bucket -- ``px_last`` of the
    LAST minute present in that bucket (order-independent: iterating in
    ascending ``minute_idx`` and letting the last write win is equivalent
    to an explicit ``arg_max`` on ``minute_idx`` within the bucket)."""
    mi = bars["minute_idx"]
    if mi.size == 0:
        return {}
    order = np.argsort(mi, kind="mergesort")
    mi_sorted = mi[order]
    px_sorted = bars["px_last"][order]
    buckets = mi_sorted // BUCKET_MINUTES
    out: dict[int, float] = {}
    for b, p in zip(buckets.tolist(), px_sorted.tolist()):
        out[int(b)] = float(p)  # ascending order -> last write is the bucket's last price
    return out


def log_returns(closes: dict[int, float]) -> dict[int, float]:
    """``{bucket: close}`` -> ``{bucket: log return}`` for CONSECUTIVE
    buckets only (``bucket - previous_bucket == 1``) -- a gap in the
    underlying cache (a day the harvester/bar-cache never built) drops the
    return spanning it instead of manufacturing one across missing time."""
    keys = sorted(closes)
    out: dict[int, float] = {}
    for i in range(1, len(keys)):
        b0, b1 = keys[i - 1], keys[i]
        if b1 - b0 != 1:
            continue
        c0, c1 = closes[b0], closes[b1]
        if c0 <= 0 or c1 <= 0:
            continue
        out[b1] = math.log(c1 / c0)
    return out


def align_pair(returns_a: dict[int, float], returns_b: dict[int, float]
               ) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Inner-join two return series on their common bucket index (sorted,
    deterministic)."""
    common = sorted(set(returns_a) & set(returns_b))
    a = np.array([returns_a[b] for b in common], dtype=np.float64)
    b = np.array([returns_b[b] for b in common], dtype=np.float64)
    return a, b, common


def pearson_corr(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation, no scipy dependency (repo convention)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) < 2:
        return 0.0
    xc, yc = x - x.mean(), y - y.mean()
    denom = math.sqrt(float((xc * xc).sum()) * float((yc * yc).sum()))
    if denom == 0.0:
        return 0.0
    return float((xc * yc).sum() / denom)


def block_bootstrap_ci(
    x: np.ndarray, y: np.ndarray, *, statistic: str = "pearson",
    block_size: int = BLOCK_BUCKETS, n_boot: int = N_BOOTSTRAP_DEFAULT,
    seed: int, ci: float = 0.95,
) -> dict[str, Any]:
    """Non-overlapping moving-block bootstrap CI of ``statistic``
    ("pearson" or "spearman") on the ALIGNED pair ``(x, y)``.

    Blocks of ``block_size`` CONSECUTIVE positions are drawn with
    replacement (a fresh random starting block each draw, i.e. a moving
    block bootstrap -- preserves the day-scale autocorrelation the plain
    iid bootstrap would destroy) until the resample reaches at least the
    original length, then truncated to it; ``n_boot`` such resamples give
    the empirical percentile CI. Deterministic given ``seed`` (a single
    ``numpy.random.default_rng(seed)`` drawn sequentially).
    """
    n = len(x)
    fn = pearson_corr if statistic == "pearson" else spearman_rank_ic
    if n < block_size + 1:
        point = fn(x, y) if n >= 2 else 0.0
        return {"statistic": statistic, "point": point, "ci_lo": point, "ci_hi": point,
                "n": n, "n_boot": 0, "seed": int(seed), "block_size": block_size,
                "note": "series shorter than one block -- CI degenerates to the point estimate"}

    rng = np.random.default_rng(seed)
    n_blocks_needed = math.ceil(n / block_size)
    max_start = n - block_size
    draws = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks_needed)
        idx = np.concatenate([np.arange(s, s + block_size) for s in starts])[:n]
        draws[i] = fn(x[idx], y[idx])
    alpha = 1.0 - ci
    lo = float(np.quantile(draws, alpha / 2))
    hi = float(np.quantile(draws, 1.0 - alpha / 2))
    return {"statistic": statistic, "point": fn(x, y), "ci_lo": lo, "ci_hi": hi,
            "n": n, "n_boot": n_boot, "seed": int(seed), "block_size": block_size}


def compute_pair_correlation(
    cache_dir: Path | str, exchange: str, symbol_a: str, symbol_b: str,
    start: str, end: str, *, seed: int, n_boot: int = N_BOOTSTRAP_DEFAULT,
) -> dict[str, Any]:
    """End-to-end: bar cache -> 30-min log returns -> aligned pair ->
    Pearson + Spearman with block-bootstrap CIs. ``symbol_a``/``symbol_b``
    default use is BTC/ETH (spec), but the function is symbol-agnostic.
    """
    from ..bar_cache import load_minute_bars

    bars_a = load_minute_bars(cache_dir, exchange, symbol_a, start, end)
    bars_b = load_minute_bars(cache_dir, exchange, symbol_b, start, end)
    ret_a = log_returns(bucket_closes(bars_a))
    ret_b = log_returns(bucket_closes(bars_b))
    x, y, common_buckets = align_pair(ret_a, ret_b)

    pearson = block_bootstrap_ci(x, y, statistic="pearson", seed=seed, n_boot=n_boot)
    spearman = block_bootstrap_ci(x, y, statistic="spearman", seed=seed, n_boot=n_boot)
    return {
        "exchange": exchange, "symbol_a": symbol_a, "symbol_b": symbol_b,
        "range": [start, end], "bucket_minutes": BUCKET_MINUTES,
        "n_aligned_buckets": len(common_buckets), "seed": int(seed),
        "pearson": pearson, "spearman": spearman,
    }


def _fingerprint(result: dict[str, Any]) -> str:
    h = hashlib.sha256()
    h.update(str(result["seed"]).encode("ascii"))
    h.update(str(result["n_aligned_buckets"]).encode("ascii"))
    for key in ("pearson", "spearman"):
        h.update(key.encode("ascii"))
        h.update(repr(round(result[key]["point"], 12)).encode("ascii"))
        h.update(repr(round(result[key]["ci_lo"], 12)).encode("ascii"))
        h.update(repr(round(result[key]["ci_hi"], 12)).encode("ascii"))
    return h.hexdigest()


def write_artifacts(out_dir: Path | str, result: dict[str, Any]) -> dict[str, Any]:
    """Write the DEC-53-style mandatory artifact (seed + point + CI for
    both statistics) to ``<out_dir>/pair_corr_<A>_<B>.json``."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write pair_corr artifacts under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = _fingerprint(result)
    payload = {**result, "sha256": fp}
    path = out_dir / f"pair_corr_{result['symbol_a']}_{result['symbol_b']}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return {"path": str(path), "sha256": fp}


def read_artifacts(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    recomputed = _fingerprint(payload)
    if recomputed != payload.get("sha256"):
        raise ValueError(
            f"{path}: stored sha256 {payload.get('sha256')!r} does not match "
            f"recomputed {recomputed!r} -- artifact corrupted or hand-edited")
    return payload
