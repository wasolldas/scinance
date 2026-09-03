"""WP-11 driver -- RELAX: activity relaxation rate after H-20 shock hours.

Nachtrag Phase 3b (PRD_SCINANCE3.md 11.3, DEC-58; Exkurs X-OEKO-1 Arm (a),
`scinance3-impl/exkurs/S2_OEKOLOGIE_KRITISCHE_UEBERGAENGE.md`; Auflagen
`scinance3-impl/exkurs/REVIEW_S1_S5.md` Zeile X-OEKO-1 Arm (a)). Rein
DESKRIPTIV -- kein PASS/FAIL, keine Schwelle. Reads EXCLUSIVELY the WP-0
bar cache (DEC-34), pooled across the 5 registered symbols.

**Event definition -- WOERTLICH aus H-20 geerbt, kein neuer Parameter.**
This module IMPORTS ``hourly_series``/``causal_mad_scale``/``find_events``
and every registered constant (``SIGMA_MULT``, ``SCALE_WINDOW_HOURS``,
``SCALE_MIN_HOURS``, ``MIN_BARS_PER_HOUR``, ``HORIZON_HOURS`` as the
24h non-overlap rule, ``CACHE_RANGE``, ``REGISTERED_FINGERPRINTS``,
``WINDOWS``/``JUDGMENT_WINDOWS`` for the era/REZENZ split) from
``c20_tail.driver`` -- it never re-implements or re-tunes the machinery.
The Renditegroesse itself (H-20's signed ``y``) is NOT reused: WP-11
measures activity, not returns, and carries no sign.

**Zustandsvariablen (pre-fixed, three, builder-scoped -- see the module
README/build report for the deviation from the Exkurs draft's A1/A2):**

  * ``activity_volume``  -- ``log1p(sum vol_total)`` per 5-min bucket,
  * ``activity_ntrades``  -- ``log1p(sum n_trades)`` per 5-min bucket,
  * ``realized_vol``      -- ``log1p(1e4 * sqrt(sum r_1min^2))`` per
    5-min bucket, ``r_1min`` = consecutive-minute ``px_last`` log returns
    strictly WITHIN the bucket (same Andersen/Bollerslev estimator as
    ``wp10_coherence.rv``, at 5-min instead of daily granularity).

**Baseline + fit.** ``baseline`` = median of a variable's 5-min buckets
over the 24h STRICTLY BEFORE the shock hour (excluding the shock hour
itself); ``excess_t = X_t - baseline`` over the 5-min buckets of
``t0..t0+24h`` (``t0`` = END of the shock hour, H-20's own aftermath
convention). The exponential-decay fit is the literature-equivalent
AR(1) coefficient of the excess (Dakos et al. 2012; van Nes & Scheffer
2007, both [sek] per the Exkurs source): ``phi`` from an ORIGIN-FORCED
OLS of ``excess_{t+1}`` on ``excess_t`` over defined-consecutive 5-min
pairs, ``lambda = -ln(phi) / dt_hours`` (``dt_hours = 5/60``),
``half_life = ln2 / lambda`` (``None``/"no decay" when ``lambda <= 0`` --
never reported as a fabricated large or negative half-life). Goodness of
fit is the through-origin R^2 of that same regression. **Read lambda only
together with R^2:** on a near-zero-SNR excess series (little true
signal, mostly noise -- e.g. an activity variable genuinely unrelated to
the shock) ``phi`` can land near 0 purely from sampling noise in the
lag-1 correlation, which the ``-ln(phi)`` transform turns into a large
NOMINAL lambda that is NOT fast relaxation -- it is estimator noise. R^2
close to 0 (or negative) on such a cell is the flag; a genuinely well-
fit decay (the POSITIVE fixture) reports R^2 close to 1.

**Time-to-return.** Post-shock buckets are averaged to 24 HOURLY excess
values; ``shock_excess`` = the first post-shock hour's excess magnitude
(the reference "how far above baseline did the shock push this
variable"). Time-to-return = the first hour whose excess magnitude is
``<= RETURN_FRACTION`` of ``shock_excess``; an event that never crosses
that line within the 24h horizon is RIGHT-CENSORED at 24h -- reported as
such (``censored=True``), never coerced into a small finite number
(NULL-fixture requirement, builder spec).

**Structural-null / selection-effect diagnostic (bindend, C.4).** Peak
selection on ``|r_hour|`` ALONE can manufacture apparent "activity
decay" purely mechanically if activity happens to correlate with the
selection variable (return magnitude) -- most acutely for
``realized_vol``, which shares its raw ingredient (squared minute
returns) with the event-detection scale. This module NEVER reports a
verdict on that risk (Arm (a) is descriptive only, PRD 11.3); instead it
ALWAYS also runs the identical baseline+fit pipeline on a MATCHED NULL of
randomly placed pseudo-shock hours (``select_pseudo_events``: same
candidate pool, same count, same 24h non-overlap rule, but chosen by a
seeded uniform draw instead of return magnitude) and reports
``Var(lambda_observed) / Var(lambda_pseudo_null)`` per symbol/variable as
a plain diagnostic number alongside the measurement -- exactly the
Exkurs's own Arm (b) calibration idea, carried here in reporting-only
form. A ratio near 1 says the observed decay structure is not an
artefact of the selection procedure on THIS bar cache; a large ratio is
a flag for a future Arm (b) registration, never a finding this module
adjudicates.

KAPITALFREI: pure measurement. No cost, fee, slippage, PnL or Sharpe
notion of any kind anywhere in this module.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

import numpy as np

from ..bar_cache import bars_fingerprint, load_minute_bars
from ..c20_tail.driver import (
    CACHE_RANGE,
    DEFAULT_SYMBOLS,
    HORIZON_HOURS,
    JUDGMENT_WINDOWS,
    REGISTERED_FINGERPRINTS,
    WINDOWS,
    causal_mad_scale,
    find_events,
    hourly_series,
)

SCHEMA_VERSION = 1
PACKAGE_ID = "WP-11"
PRD_REF = "PRD_SCINANCE3.md 11.3 (DEC-58); Exkurs X-OEKO-1 Arm (a)"

VARIABLES: tuple[str, ...] = ("activity_volume", "activity_ntrades", "realized_vol")

#: 5-minute bucketing of the post-shock and baseline windows (Exkurs:
#: "Messfenster t0..t0+24h, 5-Minuten-Aggregate").
BUCKET_MINUTES = 5
BUCKETS_PER_HOUR = 60 // BUCKET_MINUTES
POST_HORIZON_HOURS = 24
BASELINE_HOURS = 24
POST_BUCKETS = POST_HORIZON_HOURS * BUCKETS_PER_HOUR
BASELINE_BUCKETS = BASELINE_HOURS * BUCKETS_PER_HOUR

#: Data-quality floors (design parameters, NOT gates -- an event whose
#: baseline or post window is too sparse is dropped from the fit and
#: counted, mirroring c20_tail's AFTERMATH_MIN_MINUTES convention).
POST_MIN_BUCKETS = 200          # >= ~70% of 288
BASELINE_MIN_BUCKETS = 200
MIN_AR1_PAIRS = 50

#: Time-to-return threshold (builder spec: "first hour where excess
#: <= 10% of shock excess"), and the epsilon below which a shock's own
#: excess is too small to define a meaningful return threshold at all.
RETURN_FRACTION = 0.10
SHOCK_EXCESS_EPS = 1e-9

#: Cluster-bootstrap conventions (cluster = calendar day, DEC-51 point 3 /
#: builder spec: "events on the same day form one cluster").
N_BOOTSTRAP = 1000
SEED = 42
CI_ALPHA = 0.10   # central 90% CI, repo convention (c19/c20 use the same)

#: Loud "KEIN BEFUND" floor (builder spec).
MIN_EVENT_CLUSTERS = 30

MS_PER_MINUTE = 60_000
MIN_PER_HOUR = 60
MIN_PER_DAY = 1_440

__all__ = [
    "BASELINE_BUCKETS", "BUCKET_MINUTES", "BUCKETS_PER_HOUR",
    "CACHE_RANGE", "CI_ALPHA", "DEFAULT_SYMBOLS", "MIN_EVENT_CLUSTERS",
    "N_BOOTSTRAP", "POST_BUCKETS", "REGISTERED_FINGERPRINTS",
    "RETURN_FRACTION", "SEED", "VARIABLES",
    "ar1_decay_fit", "bucket_state", "collect_symbol_events",
    "day_cluster_bootstrap", "event_record", "p90_time_to_return",
    "run", "select_pseudo_events", "summarize_group",
]


# ----------------------------------------------------------------------------
# 5-minute bucket aggregation from raw minute bars
# ----------------------------------------------------------------------------

def bucket_state(minute_idx: np.ndarray, px_last: np.ndarray,
                 vol_total: np.ndarray, n_trades: np.ndarray,
                 start_min: int, n_buckets: int,
                 *, bucket_minutes: int = BUCKET_MINUTES) -> dict[str, np.ndarray]:
    """Per-5-min-bucket state variables over ``[start_min, start_min +
    n_buckets*bucket_minutes)``. ``minute_idx`` etc. are the FULL symbol
    arrays (ascending); this function slices them itself.

    A bucket with zero present bars is NaN in every variable (never a
    fabricated zero) and 0 in ``n_bars`` -- callers use ``n_bars`` as the
    shared data-quality floor for all three variables (they are null on
    exactly the same buckets by construction).
    """
    out = {v: np.full(n_buckets, np.nan) for v in VARIABLES}
    out["n_bars"] = np.zeros(n_buckets, dtype=np.int64)
    end_min = start_min + n_buckets * bucket_minutes
    i0 = int(np.searchsorted(minute_idx, start_min, side="left"))
    i1 = int(np.searchsorted(minute_idx, end_min, side="left"))
    if i1 <= i0:
        return out
    mi = minute_idx[i0:i1]
    px = px_last[i0:i1]
    vol = vol_total[i0:i1]
    nt = n_trades[i0:i1]
    bucket = ((mi - start_min) // bucket_minutes).astype(np.int64)
    valid = (bucket >= 0) & (bucket < n_buckets)
    bucket, mi, px, vol, nt = bucket[valid], mi[valid], px[valid], vol[valid], nt[valid]
    if bucket.size == 0:
        return out
    n_bars = np.bincount(bucket, minlength=n_buckets).astype(np.int64)
    vol_sum = np.bincount(bucket, weights=vol, minlength=n_buckets)
    nt_sum = np.bincount(bucket, weights=nt.astype(np.float64), minlength=n_buckets)
    # realized vol: consecutive-minute log returns strictly WITHIN one bucket
    rv_sum = np.zeros(n_buckets)
    if mi.size >= 2:
        gap = np.diff(mi)
        same_bucket = np.diff(bucket) == 0
        consec = (gap == 1) & same_bucket
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.diff(np.log(px))
        r2 = np.where(consec, r * r, 0.0)
        rv_sum = np.bincount(bucket[1:], weights=r2, minlength=n_buckets)
    present = n_bars > 0
    out["activity_volume"] = np.where(present, np.log1p(vol_sum), np.nan)
    out["activity_ntrades"] = np.where(present, np.log1p(nt_sum), np.nan)
    out["realized_vol"] = np.where(present, np.log1p(1e4 * np.sqrt(np.maximum(rv_sum, 0.0))), np.nan)
    out["n_bars"] = n_bars
    return out


# ----------------------------------------------------------------------------
# exponential-decay (AR(1)-equivalent) fit + time-to-return
# ----------------------------------------------------------------------------

def ar1_decay_fit(excess: np.ndarray, *, dt_hours: float = BUCKET_MINUTES / 60.0,
                  min_pairs: int = MIN_AR1_PAIRS) -> dict[str, Any]:
    """Origin-forced AR(1) fit of ``excess`` -> ``lambda``/``half_life``/R^2.

    ``phi = sum(e_t * e_{t+1}) / sum(e_t^2)`` over defined-consecutive
    pairs (skips NaN gaps but never bridges them); ``lambda = -ln(phi) /
    dt_hours``. ``phi <= 0`` (no valid log) or too few pairs -> NaN
    lambda ("undefined", never coerced to 0). ``lambda <= 0`` (excess
    flat or growing) -> ``half_life=None`` ("no decay within horizon"),
    matching the NULL-fixture requirement (never a fabricated negative
    or huge half-life).
    """
    e = np.asarray(excess, dtype=np.float64)
    if e.size < 2:
        return {"phi": None, "lambda_per_h": float("nan"), "half_life_h": None,
                "r2": float("nan"), "n_pairs": 0}
    mask = np.isfinite(e[:-1]) & np.isfinite(e[1:])
    e0, e1 = e[:-1][mask], e[1:][mask]
    n_pairs = int(e0.size)
    if n_pairs < min_pairs:
        return {"phi": None, "lambda_per_h": float("nan"), "half_life_h": None,
                "r2": float("nan"), "n_pairs": n_pairs}
    denom = float(np.sum(e0 * e0))
    if denom <= 0.0:
        return {"phi": None, "lambda_per_h": float("nan"), "half_life_h": None,
                "r2": float("nan"), "n_pairs": n_pairs}
    phi = float(np.sum(e0 * e1) / denom)
    r2_denom = float(np.sum(e1 * e1))
    r2 = (1.0 - float(np.sum((e1 - phi * e0) ** 2)) / r2_denom) if r2_denom > 0.0 else float("nan")
    if phi <= 0.0:
        return {"phi": phi, "lambda_per_h": float("nan"), "half_life_h": None,
                "r2": r2, "n_pairs": n_pairs}
    lam = float(-np.log(phi) / dt_hours)
    half_life = float(np.log(2.0) / lam) if lam > 0.0 else None
    return {"phi": phi, "lambda_per_h": lam, "half_life_h": half_life,
            "r2": r2, "n_pairs": n_pairs}


def hourly_from_buckets(bucket_values: np.ndarray, *,
                        buckets_per_hour: int = BUCKETS_PER_HOUR,
                        min_present: int = BUCKETS_PER_HOUR // 2) -> np.ndarray:
    """Average defined 5-min buckets into hourly values; NaN if fewer than
    ``min_present`` of the hour's buckets are defined."""
    n_hours = bucket_values.size // buckets_per_hour
    out = np.full(n_hours, np.nan)
    for h in range(n_hours):
        seg = bucket_values[h * buckets_per_hour:(h + 1) * buckets_per_hour]
        finite = seg[np.isfinite(seg)]
        if finite.size >= min_present:
            out[h] = float(np.mean(finite))
    return out


def time_to_return(hourly_excess: np.ndarray, *,
                   frac: float = RETURN_FRACTION,
                   eps: float = SHOCK_EXCESS_EPS) -> dict[str, Any]:
    """First hour (1-indexed) whose ``|excess|`` falls to <= ``frac`` of
    the FIRST post-shock hour's ``|excess|`` ("shock_excess"). Right-
    censored at the 24h horizon if never reached; ``shock_excess`` too
    small to define a threshold (``< eps``) -> ``defined=False`` (the
    event carries no measurable activity shock at all -- excluded from
    the time-to-return statistic, never silently coded as "returned at
    hour 1").
    """
    if hourly_excess.size == 0 or not np.isfinite(hourly_excess[0]):
        return {"defined": False, "shock_excess": float("nan"),
                "t_return_h": None, "censored": None}
    shock_excess = float(abs(hourly_excess[0]))
    if shock_excess < eps:
        return {"defined": False, "shock_excess": shock_excess,
                "t_return_h": None, "censored": None}
    threshold = frac * shock_excess
    for h in range(hourly_excess.size):
        v = hourly_excess[h]
        if np.isfinite(v) and abs(v) <= threshold:
            return {"defined": True, "shock_excess": shock_excess,
                    "t_return_h": h + 1, "censored": False}
    return {"defined": True, "shock_excess": shock_excess,
            "t_return_h": float(hourly_excess.size), "censored": True}


# ----------------------------------------------------------------------------
# one event -> per-variable record
# ----------------------------------------------------------------------------

def event_record(minute_idx: np.ndarray, px_last: np.ndarray,
                 vol_total: np.ndarray, n_trades: np.ndarray,
                 event_hour: int, symbol: str) -> dict[str, Any]:
    """All per-variable measurements for ONE event hour. Never raises: a
    data-quality floor miss is reported per variable, not an exception."""
    pre_start = (event_hour - BASELINE_HOURS) * MIN_PER_HOUR
    t0 = (event_hour + 1) * MIN_PER_HOUR   # end of the shock hour (H-20 convention)
    pre = bucket_state(minute_idx, px_last, vol_total, n_trades,
                       pre_start, BASELINE_BUCKETS)
    post = bucket_state(minute_idx, px_last, vol_total, n_trades,
                        t0, POST_BUCKETS)
    n_pre_present = int(np.count_nonzero(pre["n_bars"] > 0))
    n_post_present = int(np.count_nonzero(post["n_bars"] > 0))
    floor_ok = (n_pre_present >= BASELINE_MIN_BUCKETS
               and n_post_present >= POST_MIN_BUCKETS)
    rec: dict[str, Any] = {
        "symbol": symbol, "event_hour": int(event_hour),
        "event_day": int(event_hour // 24),
        "n_pre_present": n_pre_present, "n_post_present": n_post_present,
        "floor_ok": bool(floor_ok), "variables": {},
    }
    for var in VARIABLES:
        if not floor_ok:
            rec["variables"][var] = {
                "baseline": float("nan"), "fit": ar1_decay_fit(np.empty(0)),
                "return": {"defined": False, "shock_excess": float("nan"),
                          "t_return_h": None, "censored": None},
            }
            continue
        pre_vals = pre[var][pre["n_bars"] > 0]
        baseline = float(np.median(pre_vals))
        post_excess = post[var] - baseline
        fit = ar1_decay_fit(post_excess)
        hourly_excess = hourly_from_buckets(post_excess)
        ret = time_to_return(hourly_excess)
        rec["variables"][var] = {"baseline": baseline, "fit": fit, "return": ret}
    return rec


# ----------------------------------------------------------------------------
# matched null of randomly placed pseudo-shock hours (selection diagnostic)
# ----------------------------------------------------------------------------

def select_pseudo_events(hours: np.ndarray, candidate: np.ndarray, r: np.ndarray,
                         exclude_hours: set[int], n_needed: int, *,
                         seed: int, min_gap_hours: int = HORIZON_HOURS) -> np.ndarray:
    """``n_needed`` hour indices drawn UNIFORMLY at random from the same
    candidate pool H-20 events are drawn from (candidate hour + defined
    return), excluding the real event hours, respecting the SAME 24h
    non-overlap rule -- the matched null the module docstring documents:
    identical machinery, random instead of extremity-selected placement.
    """
    pool = np.flatnonzero(candidate & np.isfinite(r))
    pool = np.asarray([int(i) for i in pool if int(hours[i]) not in exclude_hours],
                      dtype=np.int64)
    if pool.size == 0 or n_needed <= 0:
        return np.empty(0, dtype=np.int64)
    rng = np.random.default_rng(seed)
    order = rng.permutation(pool.size)
    chosen_hours: list[int] = []
    chosen_idx: list[int] = []
    for k in order:
        i = int(pool[k])
        h = int(hours[i])
        if all(abs(h - ch) >= min_gap_hours for ch in chosen_hours):
            chosen_hours.append(h)
            chosen_idx.append(i)
        if len(chosen_idx) >= n_needed:
            break
    return np.asarray(sorted(chosen_idx), dtype=np.int64)


# ----------------------------------------------------------------------------
# per-symbol event collection
# ----------------------------------------------------------------------------

def collect_symbol_events(cache_dir: Any, exchange: str, symbol: str,
                          *, start: str, end: str, seed: int = SEED
                          ) -> dict[str, Any]:
    """Real H-20 events + a matched pseudo-null of the same count for ONE
    symbol over ``[start, end]``. Reads the bar cache exactly once."""
    bars = load_minute_bars(cache_dir, exchange, symbol, start, end)
    mi, px, vol, nt = (bars["minute_idx"], bars["px_last"],
                      bars["vol_total"], bars["n_trades"])
    if mi.size == 0:
        return {"real": [], "pseudo": []}
    hours, r, cand = hourly_series(mi, px)
    sigma = causal_mad_scale(r)
    ev = find_events(hours, r, cand, sigma)
    real = [event_record(mi, px, vol, nt, int(hours[i]), symbol) for i in ev]
    exclude = {int(hours[i]) for i in ev}
    pseudo_idx = select_pseudo_events(hours, cand, r, exclude, len(ev), seed=seed)
    pseudo = [event_record(mi, px, vol, nt, int(hours[i]), symbol) for i in pseudo_idx]
    return {"real": real, "pseudo": pseudo}


# ----------------------------------------------------------------------------
# cluster (=calendar day) bootstrap
# ----------------------------------------------------------------------------

def day_cluster_bootstrap(values: np.ndarray, days: np.ndarray, *,
                          n_bootstrap: int = N_BOOTSTRAP, seed: int = SEED,
                          alpha: float = CI_ALPHA) -> dict[str, Any]:
    """Central ``1-alpha`` CI of the MEDIAN of ``values`` via a cluster
    (= calendar day, DEC-51 point 3 / builder spec) bootstrap: whole days
    are resampled with replacement, so every event of a resampled day
    moves together. NaN entries in ``values`` are ignored within a
    resample (``np.nanmedian``); a resample with no finite value
    contributes no replicate.
    """
    values = np.asarray(values, dtype=np.float64)
    days = np.asarray(days)
    days_u = np.unique(days)
    finite0 = values[np.isfinite(values)]
    point = float(np.median(finite0)) if finite0.size else float("nan")
    if days_u.size == 0:
        return {"point": point, "ci_lo": float("nan"), "ci_hi": float("nan"),
               "n_bootstrap": n_bootstrap, "seed": seed, "n_finite_reps": 0}
    by_day = {d: values[days == d] for d in days_u}
    rng = np.random.default_rng(seed)
    reps = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        draw = rng.choice(days_u, size=days_u.size, replace=True)
        sample = np.concatenate([by_day[d] for d in draw])
        finite = sample[np.isfinite(sample)]
        reps[b] = float(np.median(finite)) if finite.size else float("nan")
    finite_reps = reps[np.isfinite(reps)]
    if finite_reps.size == 0:
        lo = hi = float("nan")
    else:
        lo, hi = (float(v) for v in np.quantile(finite_reps, [alpha / 2, 1 - alpha / 2]))
    return {"point": point, "ci_lo": lo, "ci_hi": hi, "n_bootstrap": n_bootstrap,
           "seed": seed, "n_finite_reps": int(finite_reps.size)}


def p90_time_to_return(t_values: np.ndarray, censored: np.ndarray, days: np.ndarray,
                       *, n_bootstrap: int = N_BOOTSTRAP, seed: int = SEED,
                       alpha: float = CI_ALPHA) -> dict[str, Any]:
    """90th-percentile time-to-return with a day-cluster bootstrap CI,
    right-censoring-aware: if the 90%-order statistic itself lands on a
    right-censored (never-returned) event, the point/replicate is
    reported as CENSORED (``None``), never as a fabricated finite number
    (builder spec, NULL-fixture requirement). ``n_finite_reps`` /
    ``n_bootstrap`` is the fraction of resamples where P90 was estimable
    at all -- reported alongside the CI as a coverage diagnostic.
    """
    t_values = np.asarray(t_values, dtype=np.float64)
    censored = np.asarray(censored, dtype=bool)
    days = np.asarray(days)

    def _p90(t: np.ndarray, c: np.ndarray) -> float:
        n = t.size
        if n == 0:
            return float("nan")
        order = np.argsort(t, kind="mergesort")
        idx = order[int(np.ceil(0.9 * n)) - 1]
        return float("nan") if c[idx] else float(t[idx])

    point = _p90(t_values, censored)
    days_u = np.unique(days)
    if days_u.size == 0:
        return {"point": point, "censored_at_p90": not np.isfinite(point),
               "ci_lo": float("nan"), "ci_hi": float("nan"),
               "n_bootstrap": n_bootstrap, "seed": seed, "n_finite_reps": 0}
    by_day_t = {d: t_values[days == d] for d in days_u}
    by_day_c = {d: censored[days == d] for d in days_u}
    rng = np.random.default_rng(seed)
    reps = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        draw = rng.choice(days_u, size=days_u.size, replace=True)
        t_sample = np.concatenate([by_day_t[d] for d in draw])
        c_sample = np.concatenate([by_day_c[d] for d in draw])
        reps[b] = _p90(t_sample, c_sample)
    finite_reps = reps[np.isfinite(reps)]
    if finite_reps.size == 0:
        lo = hi = float("nan")
    else:
        lo, hi = (float(v) for v in np.quantile(finite_reps, [alpha / 2, 1 - alpha / 2]))
    return {"point": point, "censored_at_p90": not np.isfinite(point),
           "ci_lo": lo, "ci_hi": hi, "n_bootstrap": n_bootstrap, "seed": seed,
           "n_finite_reps": int(finite_reps.size)}


# ----------------------------------------------------------------------------
# group summary (symbol x era x regime x variable cells, and the three
# pre-fixed outputs)
# ----------------------------------------------------------------------------

def summarize_group(rows: list[dict[str, Any]], *,
                    min_clusters: int = MIN_EVENT_CLUSTERS,
                    seed: int = SEED) -> dict[str, Any]:
    """One (symbol/era/regime/variable) cell (or a pooled group for the
    pre-fixed outputs) from a list of per-event-per-variable rows
    (``{"event_day": int, "lambda_per_h": float, "half_life_h": float|nan,
    "r2": float, "t_return_h": float|nan, "censored": bool|None}``).
    Loud "KEIN BEFUND" below ``min_clusters`` DISTINCT event days --
    builder spec, never silently reported as a thin-N point estimate.
    """
    n_events = len(rows)
    days = np.asarray([row["event_day"] for row in rows], dtype=np.int64)
    n_clusters = int(np.unique(days).size) if n_events else 0
    out: dict[str, Any] = {"n_events": n_events, "n_clusters": n_clusters,
                           "min_clusters": min_clusters}
    if n_clusters < min_clusters:
        out["kein_befund"] = True
        out["reason"] = (f"nur {n_clusters} Ereignistage (< {min_clusters}) -- "
                         "KEIN BEFUND (builder-Vorgabe, loud fail)")
        return out
    out["kein_befund"] = False
    lambdas = np.asarray([row["lambda_per_h"] for row in rows], dtype=np.float64)
    lam_boot = day_cluster_bootstrap(lambdas, days, seed=seed)
    out["lambda_per_h"] = lam_boot
    med_lambda = lam_boot["point"]
    if np.isfinite(med_lambda) and med_lambda > 0.0:
        out["half_life_h"] = {
            "point": float(np.log(2.0) / med_lambda),
            "ci_lo": (float(np.log(2.0) / lam_boot["ci_hi"])
                     if np.isfinite(lam_boot["ci_hi"]) and lam_boot["ci_hi"] > 0 else float("nan")),
            "ci_hi": (float(np.log(2.0) / lam_boot["ci_lo"])
                     if np.isfinite(lam_boot["ci_lo"]) and lam_boot["ci_lo"] > 0 else float("nan")),
        }
    else:
        out["half_life_h"] = {"point": None, "ci_lo": None, "ci_hi": None,
                              "note": "kein Zerfall (median lambda <= 0) -- keine Halbwertszeit"}
    r2s = np.asarray([row["r2"] for row in rows], dtype=np.float64)
    r2_finite = r2s[np.isfinite(r2s)]
    out["median_r2"] = float(np.median(r2_finite)) if r2_finite.size else None
    defined = [row for row in rows if row.get("t_return_defined")]
    out["n_return_defined"] = len(defined)
    out["n_return_undefined"] = n_events - len(defined)
    if defined:
        t_vals = np.asarray([row["t_return_h"] for row in defined], dtype=np.float64)
        cens = np.asarray([bool(row["censored"]) for row in defined], dtype=bool)
        d_days = np.asarray([row["event_day"] for row in defined], dtype=np.int64)
        out["n_censored"] = int(np.sum(cens))
        out["p90_time_to_return_h"] = p90_time_to_return(t_vals, cens, d_days, seed=seed)
    else:
        out["n_censored"] = 0
        out["p90_time_to_return_h"] = {"point": float("nan"), "censored_at_p90": True,
                                       "ci_lo": float("nan"), "ci_hi": float("nan"),
                                       "n_bootstrap": N_BOOTSTRAP, "seed": seed,
                                       "n_finite_reps": 0}
    return out


# ----------------------------------------------------------------------------
# rows: flatten event records into (symbol, era, regime, variable) rows
# ----------------------------------------------------------------------------

def _epoch_day_iso(day_idx: int) -> str:
    return (date(1970, 1, 1) + timedelta(days=int(day_idx))).isoformat()


def _era_of(event_day: int, windows: tuple[tuple[str, tuple[str, str]], ...]) -> str:
    for label, (w_start, w_end) in windows:
        d0 = (date.fromisoformat(w_start) - date(1970, 1, 1)).days
        d1 = (date.fromisoformat(w_end) - date(1970, 1, 1)).days
        if d0 <= event_day <= d1:
            return label
    return "OTHER"


def _flatten(records: list[dict[str, Any]], *,
            stress_abs_days: frozenset[str] | None,
            windows: tuple[tuple[str, tuple[str, str]], ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec in records:
        day_iso = _epoch_day_iso(rec["event_day"])
        era = _era_of(rec["event_day"], windows)
        stress = (day_iso in stress_abs_days) if stress_abs_days is not None else None
        for var in VARIABLES:
            m = rec["variables"][var]
            fit = m["fit"]
            ret = m["return"]
            rows.append({
                "symbol": rec["symbol"], "event_hour": rec["event_hour"],
                "event_day": rec["event_day"], "event_date": day_iso,
                "era": era, "stress_abs": stress, "variable": var,
                "floor_ok": rec["floor_ok"], "baseline": m["baseline"],
                "phi": fit["phi"], "lambda_per_h": fit["lambda_per_h"],
                "half_life_h": fit["half_life_h"], "r2": fit["r2"],
                "n_pairs": fit["n_pairs"],
                "t_return_defined": bool(ret["defined"]),
                "shock_excess": ret["shock_excess"],
                "t_return_h": ret["t_return_h"] if ret["t_return_h"] is not None else float("nan"),
                "censored": ret["censored"],
            })
    return rows


# ----------------------------------------------------------------------------
# run
# ----------------------------------------------------------------------------

def run(
    cache_dir: Any,
    *,
    exchange: str = "bybit",
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    skip_fingerprint_check: bool = False,
    expected_fingerprints: dict[str, str] | None = None,
    stress_abs_days: frozenset[str] | None = None,
    seed: int = SEED,
    min_clusters: int = MIN_EVENT_CLUSTERS,
    windows: tuple[tuple[str, tuple[str, str]], ...] = WINDOWS,
    source: str = "",
) -> dict[str, Any]:
    """Run the WP-11 measurement (deskriptiv, gate-neutral payload).

    ``stress_abs_days`` -- an ISO-date frozenset from the WP-10 STRESS_ABS
    fixture (``wp10_coherence.stress_canon``); ``None`` skips the
    STRESS_ABS split (regime cells report ``stress_abs: None``/"unknown").
    """
    expected = REGISTERED_FINGERPRINTS if expected_fingerprints is None else expected_fingerprints
    fingerprints: dict[str, Any] = {}
    fp_ok = True
    for sym in symbols:
        fp = bars_fingerprint(cache_dir, exchange, sym, *CACHE_RANGE)
        ref = expected.get(sym)
        match = bool(ref) and fp["sha256_values"] == ref
        fingerprints[sym] = {"observed": fp["sha256_values"], "registered": ref, "matches": match}
        fp_ok &= match
    gate_valid = fp_ok or skip_fingerprint_check

    real_rows: list[dict[str, Any]] = []
    pseudo_rows: list[dict[str, Any]] = []
    n_real, n_pseudo = 0, 0
    for sym in symbols:
        collected = collect_symbol_events(cache_dir, exchange, sym,
                                          start=CACHE_RANGE[0], end=CACHE_RANGE[1], seed=seed)
        n_real += len(collected["real"])
        n_pseudo += len(collected["pseudo"])
        real_rows += _flatten(collected["real"], stress_abs_days=stress_abs_days, windows=windows)
        pseudo_rows += _flatten(collected["pseudo"], stress_abs_days=stress_abs_days, windows=windows)
        print(f"[wp11] {sym}: {len(collected['real'])} events "
             f"({len(collected['pseudo'])} matched pseudo-null)", file=sys.stderr, flush=True)

    # (grid) per symbol x era x regime x variable
    cells: list[dict[str, Any]] = []
    regimes: tuple[Any, ...] = (True, False) if stress_abs_days is not None else (None,)
    era_labels = [w[0] for w in windows] + ["OTHER"]
    for sym in symbols:
        for era in era_labels:
            for regime in regimes:
                for var in VARIABLES:
                    sub = [r for r in real_rows if r["symbol"] == sym and r["era"] == era
                          and r["variable"] == var and r["floor_ok"]
                          and (regime is None or r["stress_abs"] == regime)]
                    summary = summarize_group(sub, min_clusters=min_clusters, seed=seed)
                    cells.append({"symbol": sym, "era": era,
                                 "stress_abs": regime, "variable": var, **summary})

    # (i) median half-life per symbol (pooled over era + regime)
    per_symbol: list[dict[str, Any]] = []
    for sym in symbols:
        for var in VARIABLES:
            sub = [r for r in real_rows if r["symbol"] == sym and r["variable"] == var and r["floor_ok"]]
            per_symbol.append({"symbol": sym, "variable": var,
                              **summarize_group(sub, min_clusters=min_clusters, seed=seed)})

    # (ii) RECOVERY_H_P90 -- STRESS_ABS days only, pooled across symbols
    recovery_h_p90: list[dict[str, Any]] = []
    if stress_abs_days is not None:
        for var in VARIABLES:
            sub = [r for r in real_rows if r["variable"] == var and r["floor_ok"] and r["stress_abs"] is True]
            recovery_h_p90.append({"variable": var, **summarize_group(sub, min_clusters=min_clusters, seed=seed)})
    else:
        recovery_h_p90 = [{"variable": var, "kein_befund": True,
                          "reason": "kein STRESS_ABS-Fixture uebergeben"} for var in VARIABLES]

    # (iii) era comparison -- "ist H-20-Aera-invariant?", pooled over symbol+regime, DESKRIPTIV
    era_invariance: list[dict[str, Any]] = []
    for era in era_labels:
        for var in VARIABLES:
            sub = [r for r in real_rows if r["era"] == era and r["variable"] == var and r["floor_ok"]]
            era_invariance.append({"era": era, "variable": var,
                                  **summarize_group(sub, min_clusters=min_clusters, seed=seed)})

    # structural-null diagnostic: Var(lambda_obs)/Var(lambda_pseudo_null) per symbol/variable
    structural_null: list[dict[str, Any]] = []
    for sym in symbols:
        for var in VARIABLES:
            obs = np.asarray([r["lambda_per_h"] for r in real_rows
                             if r["symbol"] == sym and r["variable"] == var
                             and r["floor_ok"] and np.isfinite(r["lambda_per_h"])])
            null = np.asarray([r["lambda_per_h"] for r in pseudo_rows
                              if r["symbol"] == sym and r["variable"] == var
                              and r["floor_ok"] and np.isfinite(r["lambda_per_h"])])
            var_obs = float(np.var(obs)) if obs.size >= 4 else float("nan")
            var_null = float(np.var(null)) if null.size >= 4 else float("nan")
            ratio = (var_obs / var_null) if (np.isfinite(var_obs) and np.isfinite(var_null)
                                            and var_null > 0.0) else float("nan")
            structural_null.append({
                "symbol": sym, "variable": var,
                "n_obs": int(obs.size), "n_null": int(null.size),
                "var_obs": var_obs, "var_null": var_null,
                "var_ratio": ratio,
            })

    n_event_clusters_total = int(np.unique(np.asarray([r["event_day"] for r in real_rows])).size) \
        if real_rows else 0
    kein_befund_overall = n_event_clusters_total < min_clusters

    return {
        "schema_version": SCHEMA_VERSION,
        "package": PACKAGE_ID,
        "prd_ref": PRD_REF,
        "capital_free": True,
        "status": "KEIN BEFUND" if kein_befund_overall else "RUN",
        "verdict_semantics": ("DESKRIPTIV (Arm (a), PRD 11.3): kein PASS/FAIL, "
                              "keine Schwelle -- Halbwertszeit ist Deskriptor"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "exchange": exchange,
        "symbols": list(symbols),
        "cache_fingerprints": fingerprints,
        "gate_valid": bool(gate_valid),
        "windows": {k: list(v) for k, v in windows},
        "judgment_windows": list(JUDGMENT_WINDOWS),
        "variables": list(VARIABLES),
        "method": {
            "event": "WOERTLICH aus H-20 geerbt (c20_tail.driver), kein neuer Parameter",
            "baseline": f"Median ueber {BASELINE_HOURS}h vor der Schockstunde (exklusive)",
            "fit": ("AR(1)-aequivalenter Zerfall der Ueberschussreihe (5-Min-Buckets, "
                   "24h post-shock), lambda = -ln(phi)/dt_h, half_life = ln2/lambda"),
            "time_to_return": (f"erste Stunde mit |excess| <= {RETURN_FRACTION:.0%} des "
                               "Schock-Excess; rechts-zensiert bei 24h"),
            "cluster": "Kalendertag (DEC-51 Punkt 3); Bootstrap 1000 Reps",
            "seed": seed,
            "min_event_clusters": min_clusters,
        },
        "n_events_real": n_real,
        "n_events_pseudo_null": n_pseudo,
        "n_event_clusters_total": n_event_clusters_total,
        "kein_befund_overall": bool(kein_befund_overall),
        "cells": cells,
        "pre_fixed": {
            "median_half_life_per_symbol": per_symbol,
            "recovery_h_p90": recovery_h_p90,
            "era_invariance_descriptive": era_invariance,
        },
        "structural_null": structural_null,
        "_real_rows": real_rows,       # consumed by report.py for the DEC-53 CSV
        "_pseudo_rows": pseudo_rows,
    }


__all__ += ["hourly_from_buckets", "time_to_return"]
