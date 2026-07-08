"""Analog ensemble (AnEn) for the H-11 vol-regime mess-gate (KAPITALFREI).

Delle Monache et al. (2013)-style analog forecasting on the pre-registered
5-feature daily state vector: the k=20 nearest historical day-states under a
weighted-euclidean distance on z-standardised features form the ensemble.
The AnEn forecast is the EMPIRICAL DISTRIBUTION of the k analog targets
(registry H-11: "AnEn-Vorhersageverteilung = empirische Verteilung der
log-RV(t'+1..t'+3) der 20 Analoga"), scored with the proper ensemble CRPS
(``stats.crps_ensemble``); the degenerate point-CRPS applies ONLY to the
HAR baseline. The ensemble mean may be reported as a display statistic but
never enters the scoring.

Pre-registered construction (registry H-11):

  * z-standardisation is EXPANDING up to t-30: mean/std are computed from the
    eligible candidate library only (all days t' <= t - EMBARGO_DAYS).
  * 30-day EMBARGO between analog candidate and current state: a candidate
    day t' may only be used if t' <= t - 30 (causally safe — the candidate's
    3-day-ahead target then ends at t' + 3 <= t - 27 < t).
  * weights come from leave-one-out CRPS tuning on region L over the FIXED
    grid {0, 0.5, 1, 1.5, 2}^5 and are FROZEN afterwards (no OOS re-tuning).

KAPITALFREI: pure measurement forecasting. numpy only.
"""
from __future__ import annotations

import itertools
import sys

import numpy as np

from .stats import crps_ensemble

#: Pre-registered ensemble size (registry H-11).
K_ANALOGS = 20

#: Pre-registered candidate embargo in days (registry H-11).
EMBARGO_DAYS = 30

#: Pre-registered frozen weight grid per feature (registry H-11).
WEIGHT_GRID = (0.0, 0.5, 1.0, 1.5, 2.0)

_STD_FLOOR = 1e-12


def eligible_candidates(
    t: int, features: np.ndarray, targets: np.ndarray, embargo: int = EMBARGO_DAYS
) -> np.ndarray:
    """Indices t' usable as analog candidates for the state at day t.

    Enforces the pre-registered 30-day embargo: only t' <= t - embargo. On top,
    a candidate needs finite features (it must be comparable) and a finite
    target (it must contribute an ensemble member). Returns indices in
    ascending (deterministic) order.
    """
    hi = t - embargo  # inclusive upper bound: t' <= t - embargo
    if hi < 0:
        return np.empty(0, dtype=np.int64)
    idx = np.arange(hi + 1, dtype=np.int64)
    ok = np.all(np.isfinite(features[: hi + 1]), axis=1) & np.isfinite(targets[: hi + 1])
    return idx[ok]


def zscore_stats(features: np.ndarray, cand_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expanding standardisation stats over the candidate library only.

    Mean/std per feature are computed from ``features[cand_idx]`` — i.e. from
    day-states <= t - embargo, never from the current day or its future.
    """
    lib = features[cand_idx]
    mu = np.mean(lib, axis=0)
    sd = np.std(lib, axis=0)
    sd = np.where(sd < _STD_FLOOR, 1.0, sd)
    return mu, sd


def analog_forecast(
    features: np.ndarray,
    targets: np.ndarray,
    t: int,
    weights: np.ndarray,
    *,
    k: int = K_ANALOGS,
    embargo: int = EMBARGO_DAYS,
) -> tuple[np.ndarray, np.ndarray]:
    """AnEn ensemble forecast for day t plus the selected candidate indices.

    Distance: sqrt( sum_j w_j * (z_t[j] - z_t'[j])^2 ) on features
    z-standardised with the expanding candidate-library stats. The k nearest
    candidates (ties broken by ascending day index — deterministic) form the
    ensemble. Returns ``(members, sel)`` where ``members`` are the k analog
    targets — the EMPIRICAL FORECAST DISTRIBUTION registered for H-11, to be
    scored with ``stats.crps_ensemble`` (NOT collapsed to its mean; the mean
    is at most a display statistic).

    Returns ``(empty, empty)`` when the current state is incomplete or fewer
    than k eligible candidates exist (no partial ensembles — deterministic,
    pre-registered k).
    """
    w = np.asarray(weights, dtype=np.float64)
    if w.shape != (features.shape[1],):
        raise ValueError(f"weights must have shape ({features.shape[1]},)")
    empty = (np.empty(0, dtype=np.float64), np.empty(0, dtype=np.int64))
    if not np.all(np.isfinite(features[t])):
        return empty
    cand = eligible_candidates(t, features, targets, embargo)
    if cand.size < k:
        return empty
    mu, sd = zscore_stats(features, cand)
    z_now = (features[t] - mu) / sd
    z_lib = (features[cand] - mu) / sd
    diff = z_lib - z_now[None, :]
    dist2 = (diff * diff) @ w
    order = np.argsort(dist2, kind="stable")[:k]
    sel = cand[order]
    return targets[sel].astype(np.float64, copy=True), sel


def loo_crps_for_weights(
    features: np.ndarray,
    targets: np.ndarray,
    tune_idx: np.ndarray,
    weights: np.ndarray,
    *,
    k: int = K_ANALOGS,
    embargo: int = EMBARGO_DAYS,
) -> float:
    """Mean leave-one-out ensemble CRPS of one weight vector over tuning days.

    Scores each forecast day with the proper ensemble CRPS of the k-member
    empirical distribution (registry H-11 metric) — the same objective the
    OOS windows are scored with. "Leave-one-out" is enforced structurally by
    the embargo: forecasting day t only ever uses candidates <= t - embargo,
    so the day under evaluation (and its 30-day neighbourhood) is excluded
    from its own analog library. Days without a full ensemble or without an
    observed target are skipped. Returns inf when no tuning day is scoreable
    (so it can never win the argmin).
    """
    scores: list[float] = []
    for t in tune_idx:
        t = int(t)
        if not np.isfinite(targets[t]):
            continue
        members, _sel = analog_forecast(features, targets, t, weights, k=k, embargo=embargo)
        if members.size:
            scores.append(float(crps_ensemble(members, targets[t])[0]))
    if not scores:
        return float("inf")
    return float(np.mean(scores))


def tune_weights_loo_crps(
    features: np.ndarray,
    targets: np.ndarray,
    tune_idx: np.ndarray,
    *,
    grid: tuple[float, ...] = WEIGHT_GRID,
    k: int = K_ANALOGS,
    embargo: int = EMBARGO_DAYS,
    verbose: bool = False,
) -> tuple[np.ndarray, float]:
    """LOO-CRPS weight tuning on region L over the frozen grid (registry H-11).

    The objective is the mean leave-one-out ENSEMBLE CRPS of the k-member
    empirical distribution — identical to the OOS scoring rule (never the
    collapsed-mean point error). Evaluates every weight vector in ``grid``^5
    (default {0,0.5,1,1.5,2}^5 = 3125 combinations) over ``tune_idx`` and returns
    ``(best_weights, best_mean_crps)``. Deterministic: ties resolve to the
    FIRST combination in ``itertools.product`` order. The all-zero vector is
    excluded (degenerate distance — every candidate equidistant). After this
    call the weights are FROZEN; the OOS windows W1/W2 never re-tune.

    In the current data-gated state this function is exercised only on
    synthetic fixtures; it is the exact tuning that runs once H-11 unlocks.
    """
    n_feat = features.shape[1]
    tune_idx = np.asarray(tune_idx, dtype=np.int64)

    # Precompute per-day squared z-diff matrices once (grid-independent).
    pre: list[tuple[float, np.ndarray, np.ndarray]] = []
    for t in tune_idx:
        t = int(t)
        if not np.isfinite(targets[t]) or not np.all(np.isfinite(features[t])):
            continue
        cand = eligible_candidates(t, features, targets, embargo)
        if cand.size < k:
            continue
        mu, sd = zscore_stats(features, cand)
        diff = (features[cand] - mu) / sd - ((features[t] - mu) / sd)[None, :]
        pre.append((float(targets[t]), diff * diff, targets[cand]))
    if not pre:
        raise ValueError("no scoreable tuning day (need >= k embargoed candidates)")

    best_w: np.ndarray | None = None
    best_score = float("inf")
    n_combo = 0
    for combo in itertools.product(grid, repeat=n_feat):
        if all(c == 0.0 for c in combo):
            continue
        n_combo += 1
        w = np.asarray(combo, dtype=np.float64)
        total = 0.0
        for obs, d2, cand_tgt in pre:
            dist2 = d2 @ w
            # same deterministic selection rule as analog_forecast (stable sort)
            order = np.argsort(dist2, kind="stable")[:k]
            members = cand_tgt[order]
            # inline ensemble CRPS (== stats.crps_ensemble on one day)
            total += float(np.mean(np.abs(members - obs))
                           - 0.5 * np.mean(np.abs(members[:, None] - members[None, :])))
        score = total / len(pre)
        if score < best_score - 1e-15:
            best_score = score
            best_w = w
    if verbose:
        print(f"[c11_anen] tuned over {n_combo} weight combos, {len(pre)} LOO days, "
              f"best mean CRPS={best_score:.6f}, weights={best_w}",
              file=sys.stderr, flush=True)
    assert best_w is not None
    return best_w, best_score


__all__ = [
    "EMBARGO_DAYS",
    "K_ANALOGS",
    "WEIGHT_GRID",
    "analog_forecast",
    "eligible_candidates",
    "loo_crps_for_weights",
    "tune_weights_loo_crps",
    "zscore_stats",
]
