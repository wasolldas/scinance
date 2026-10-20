"""Block-permutation p of the fm8 window mean (DEC-74 (e), ERSTFASSUNG 1.10, Review B-3): the OUTCOME weeks (raw returns
and their alive masks) of the window are permuted in blocks of 4 weeks, then fm8 is applied with the UNCHANGED formation
weeks -- characteristic, 8-week PIT beta and formation mask stay at their real week index.  10.000 permutations, seed 53,
one-sided in the registered direction; the p of an entry is the larger p of the two windows (max-p).

**What is permuted: the ``w_judged`` outcome weeks, not all window rows.**  The first row of a window is a formation week
and no outcome; permuting all ``n_weeks`` rows (as ``nulls.block_permutation_null_draws`` of the third version does) leaves
a one-week tail block when ``n_weeks`` is not a multiple of 4 (W1: 53 rows) and that tail shifts the following blocks by one
week, which pairs ``mom`` formation weeks with the outcome of their OWN week (rank IC ~0.9) in about every second draw -- the
null then reaches 0.07 and more and no mom entry could ever reject.  With the 52 / 50 outcome weeks of W1 / W2 the block
offsets are multiples of 4 (W1) or 0 / 2 mod 4 (W2), a same-week re-alignment is impossible, and an unmoved block keeps at
most 4 real pairs (the usual conservatism of a block permutation).

One pass over the permutations serves all handed variants (the residualised outcome does not depend on the
characteristic, and every variant used the same permutation sequence in the third version as well).  The per-week
arithmetic is that of ``ic.fm_neutralize_outcome`` + ``ic.weekly_ic_series`` (``close_at_last``, outcome demeaned,
Spearman with average ranks); with the identity permutation it reproduces ``fm8.fm8_weekly_ic`` bit for bit (tested).
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.stats import rankdata

from ..wp13_xsec import nulls
from . import constants as C
from . import estimators as est

__all__ = ["permuted_week_ic", "block_permutation_draws", "permutation_pvalue"]

_MIN_UNIVERSE = 10          # ic.weekly_ic_series default
_MIN_FM = 5                 # ic.fm_neutralize_outcome default


def _spearman_ranked(rx: np.ndarray, y: np.ndarray) -> float:
    """``pit_universe.spearman_rank_ic`` for pre-centred x ranks ``rx`` (same arithmetic, same ranks)."""
    ry = rankdata(y)
    ry = ry - ry.mean()
    denom = math.sqrt(float((rx * rx).sum()) * float((ry * ry).sum()))
    if denom == 0.0:
        return 0.0
    return float((rx * ry).sum() / denom)


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2:
        return 0.0
    rx = rankdata(x)
    rx = rx - rx.mean()
    return _spearman_ranked(rx, y)


def permuted_week_ic(chars: dict[str, np.ndarray], returns: np.ndarray, alive: np.ndarray, beta8: np.ndarray,
                     outcome_rows: np.ndarray, *, rank_cache: dict[str, list[Any]] | None = None) -> dict[str, np.ndarray]:
    """Weekly fm8 IC (raw) of every characteristic for ONE assignment of outcome rows: formation week t is set against the
    outcome row ``outcome_rows[t]`` (identity: ``t + 1``).  ``rank_cache`` = :func:`_build_rank_cache` output."""
    n_w, _ = returns.shape
    out = {v: np.full(n_w - 1, np.nan, dtype=np.float64) for v in chars}
    for t in range(n_w - 1):
        o = int(outcome_rows[t])
        form = alive[t]
        out_alive = alive[o]
        r_o = returns[o]
        sample = form & out_alive & ~np.isnan(beta8[t]) & ~np.isnan(r_o)
        resid = np.full(r_o.shape, np.nan)
        if int(sample.sum()) >= _MIN_FM:
            x = beta8[t, sample]
            y = r_o[sample]
            x_c = x - x.mean()
            var_x = float(np.dot(x_c, x_c))
            if var_x > 0.0:
                slope = float(np.dot(x_c, y - y.mean()) / var_x)
                intercept = float(y.mean() - slope * x.mean())
                resid[sample] = y - (intercept + slope * x)
        outcome_row = np.where(out_alive, resid, 0.0)
        k = int(form.sum())
        if k < _MIN_UNIVERSE:
            continue
        out_vals_all = outcome_row[form]
        out_fin = np.isfinite(out_vals_all)
        for v, char in chars.items():
            cache = None if rank_cache is None else rank_cache[v][t]
            if cache is not None and bool(out_fin.all()):
                ov = out_vals_all - out_vals_all.mean()
                out[v][t] = _spearman_ranked(cache, ov)
                continue
            cv = char[t, form]
            valid = ~np.isnan(cv) & ~np.isnan(out_vals_all)
            if int(valid.sum()) < _MIN_UNIVERSE:
                continue
            ov = out_vals_all[valid]
            ov = ov - ov.mean()
            out[v][t] = _spearman(cv[valid], ov)
    return out


def _build_rank_cache(chars: dict[str, np.ndarray], alive: np.ndarray) -> dict[str, list[Any]]:
    """Centred average ranks of the formation cross-section per week where the characteristic is finite for every
    member (the outcome side is then the only thing that varies with the permutation)."""
    cache: dict[str, list[Any]] = {}
    n_w = alive.shape[0]
    for v, char in chars.items():
        rows: list[Any] = []
        for t in range(n_w - 1):
            cv = char[t, alive[t]]
            if cv.size >= _MIN_UNIVERSE and np.isfinite(cv).all():
                r = rankdata(cv)
                rows.append(r - r.mean())
            else:
                rows.append(None)
        cache[v] = rows
    return cache


def block_permutation_draws(chars: dict[str, np.ndarray], returns: np.ndarray, alive: np.ndarray, beta8: np.ndarray, *,
                            n_perm: int | None = None, block: int = C.PERM_BLOCK, seed: int = C.SEED,
                            signs: dict[str, int] | None = None) -> dict[str, np.ndarray]:
    """``n_perm`` permuted window means per variant in the registered direction (``y = s * mean IC``; NaN where no week
    is finite).  Deterministic for a seed (numpy PCG64); every variant sees the same permutations."""
    n_perm = C.N_PERM if n_perm is None else int(n_perm)
    sg = {v: float(C.SIGN[C.DIRECTION[v]]) for v in chars} if signs is None else {v: float(s) for v, s in signs.items()}
    rng = np.random.default_rng(seed)
    n_w = returns.shape[0]
    cache = _build_rank_cache(chars, alive)
    draws = {v: np.full(n_perm, np.nan, dtype=np.float64) for v in chars}
    for i in range(n_perm):
        perm = nulls.block_permute_week_index(n_w - 1, block, rng)            # the w_judged OUTCOME weeks (rows 1 .. n_w - 1)
        ics = permuted_week_ic(chars, returns, alive, beta8, 1 + perm, rank_cache=cache)
        for v, arr in ics.items():
            fin = arr[np.isfinite(arr)]
            if fin.size:
                draws[v][i] = sg[v] * float(fin.mean())
    return draws


def permutation_pvalue(y_real: float, draws: np.ndarray) -> dict[str, Any]:
    """One-sided p with the continuity correction ``(1 + count) / (1 + n)`` (Davison & Hinkley; DEC-75 (2)): the share of
    permuted window means (y units) at least as large as the real one."""
    d = np.asarray(draws, dtype=np.float64)
    fin = d[np.isfinite(d)]
    if fin.size == 0 or not math.isfinite(y_real):
        return {"p_value": float("nan"), "n_perm": int(d.size), "n_finite": int(fin.size), "count_ge": None,
                "draws_sha256": est.series_sha256(d)}
    count = int((fin >= y_real).sum())
    return {"p_value": (1 + count) / (1 + fin.size), "n_perm": int(d.size), "n_finite": int(fin.size), "count_ge": count,
            "draws_mean": float(fin.mean()), "draws_sd": float(fin.std(ddof=1)) if fin.size > 1 else float("nan"),
            "draws_sha256": est.series_sha256(d)}
