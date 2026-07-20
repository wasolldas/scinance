"""Fold construction, seasonality-preserving null and FDR for H-15 (numpy).

Registry H-15 (pre-fixed, binding):
  * Fenster: purged walk-forward, 4 folds over ~100 days, 1-day embargo per
    fold, 3 seeds per fold. ONE registered window (no W1/W2 split — the
    4-fold walk-forward structure itself is the robustness design).
  * Null: >= 200 seasonality-preserving surrogates via WITHIN-hour-of-day
    block shuffle (block length 256 events); null of the
    (Markov-CE minus Transformer-CE) gap distribution.
  * Gate: WEITER if OOS token-level transformer CE is >= 2% RELATIVELY lower
    than the best Markov-k (k<=4) baseline for >= 4/5 symbols AND the CE gap
    exceeds the 95th percentile of the surrogate gap distribution, after
    BH-FDR alpha=0.10 over F-GRAMMAR (5 symbols).

``benjamini_hochberg`` is an OWN copy (registry §8.2 convention: each
research package keeps its own; no cross-import between research packages).

KAPITALFREI: pure statistics. numpy only — no torch anywhere here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

#: BH-FDR level for the F-GRAMMAR family (registry H-15).
FDR_ALPHA = 0.10

#: FDR family name (registry H-15: 5 symbols).
FDR_FAMILY = "F-GRAMMAR"

#: Registered relative OOS-CE improvement threshold (>= 2% lower CE).
REL_CE_GAP_MIN = 0.02

#: Registered surrogate percentile the observed gap must exceed.
SURROGATE_PERCENTILE = 95.0

#: Registered minimum surrogate count.
N_SURROGATES_DEFAULT = 200

#: Registered within-hour-of-day shuffle block length (events).
BLOCK_LEN_EVENTS = 256

#: Registered walk-forward design.
N_FOLDS = 4
EMBARGO_DAYS = 1
N_SEEDS = 3

#: Registered symbol-pass floor (>= 4 of 5 symbols).
SYMBOLS_PASS_MIN = 4
FAMILY_SIZE = 5


class FoldError(ValueError):
    """Raised on invalid walk-forward fold construction."""


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i``
    is significant at FDR ``alpha`` and ``p_crit`` the largest passing
    p-value (0.0 if none). Input order preserved. OWN copy (registry §8.2
    convention — no cross-import between research packages).
    """
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit = 0.0
    k_max = -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max = rank
            p_crit = p_values[idx]
    rejected = [False] * m
    if k_max >= 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= k_max:
                rejected[idx] = True
    return rejected, p_crit


# ----------------------------------------------------------------------------
# Purged walk-forward folds (4 folds, 1-day embargo)
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class Fold:
    """One purged walk-forward fold over calendar days (ISO strings).

    ``train_days`` and ``test_days`` are contiguous, disjoint, and separated
    by exactly ``embargo_days`` calendar days that belong to NEITHER side
    (``embargo``): max(train) < every embargo day < min(test).
    """

    index: int
    train_days: tuple[str, ...]
    embargo: tuple[str, ...]
    test_days: tuple[str, ...]


def _iso_to_date(d: str) -> date:
    y, m, dd = (int(x) for x in d.split("-"))
    return date(y, m, dd)


def walk_forward_folds(
    days: list[str],
    *,
    n_folds: int = N_FOLDS,
    embargo_days: int = EMBARGO_DAYS,
) -> list[Fold]:
    """Purged expanding walk-forward folds over a sorted daily grid.

    The grid is split into ``n_folds + 1`` (near-)equal contiguous segments.
    Fold i (i = 0..n_folds-1):
      * train = segments 0..i (EXPANDING window — strictly past data),
      * embargo = the FIRST ``embargo_days`` days of segment i+1 (dropped
        from both sides — the registered 1-day embargo),
      * test = the remainder of segment i+1.
    Guarantees (asserted): train/test disjoint, max(train) < min(test), and
    the calendar gap between the last train day and the first test day is
    ``embargo_days + 1`` days (i.e. ``embargo_days`` full days lie between).
    """
    if len(days) != len(set(days)):
        raise FoldError("duplicate days in grid")
    if sorted(days) != list(days):
        raise FoldError("days must be sorted ascending")
    n = len(days)
    n_seg = n_folds + 1
    if n < n_seg * (embargo_days + 2):
        raise FoldError(
            f"grid too short ({n} days) for {n_folds} folds with "
            f"{embargo_days}-day embargo"
        )
    bounds = [round(i * n / n_seg) for i in range(n_seg + 1)]
    folds: list[Fold] = []
    for i in range(n_folds):
        train = tuple(days[: bounds[i + 1]])
        seg = days[bounds[i + 1]: bounds[i + 2]]
        embargo = tuple(seg[:embargo_days])
        test = tuple(seg[embargo_days:])
        if not train or not test:
            raise FoldError(f"fold {i}: empty train or test segment")
        # hard causality/embargo assertions (defence in depth)
        last_train = _iso_to_date(train[-1])
        first_test = _iso_to_date(test[0])
        if first_test <= last_train:
            raise FoldError(f"fold {i}: test not strictly after train")
        gap = (first_test - last_train).days
        if gap < embargo_days + 1:
            raise FoldError(
                f"fold {i}: calendar gap {gap} < embargo {embargo_days} + 1"
            )
        if set(train) & set(test):
            raise FoldError(f"fold {i}: train/test overlap")
        folds.append(Fold(index=i, train_days=train, embargo=embargo,
                          test_days=test))
    return folds


# ----------------------------------------------------------------------------
# Seasonality-preserving null: within-hour-of-day block shuffle
# ----------------------------------------------------------------------------

def hour_block_shuffle(
    tokens: np.ndarray,
    hours: np.ndarray,
    *,
    block_len: int = BLOCK_LEN_EVENTS,
    rng: np.random.Generator,
) -> np.ndarray:
    """One seasonality-preserving surrogate of a token stream.

    Registered null (registry H-15): WITHIN-hour-of-day block shuffle with
    block length 256 events. For each hour-of-day h in 0..23, the events at
    positions with hour h (in stream order) are partitioned into consecutive
    blocks of ``block_len`` events (a shorter trailing block is kept as its
    own block), the BLOCK ORDER is permuted uniformly, and the concatenation
    is written back onto exactly those positions.

    Invariants (tested): the surrogate is a permutation of the original
    within every hour-of-day group, so the per-hour marginal token
    distribution (and therefore intraday seasonality of the marginals) is
    preserved EXACTLY, while sequence structure beyond ``block_len`` events
    is destroyed. Local (< block_len) structure inside blocks is preserved —
    the null therefore tests structure BEYOND short-range order, as
    registered. A group with <= block_len events has a single block and is
    left unchanged (degenerate case, exact identity).

    Dtype: the surrogate keeps the INPUT token dtype (a pure permutation
    never changes values, so int16 in -> int16 out is bit-identical in
    content while avoiding a full int64 copy of a ~30M-token test stream
    per surrogate — 200+ such copies per fold otherwise).

    Implementation note (performance refactor, zero methodology change):
    the shuffle is expressed as ``tokens[hour_block_shuffle_perm(...)]`` —
    the SOURCE-INDEX permutation is built by exactly the loop that used to
    move the tokens themselves, with the identical single
    ``rng.permutation(n_blocks)`` draw per >1-block hour group in hour
    order, so RNG CONSUMPTION and the resulting surrogate stream are
    bit-identical to the pre-refactor version. Exposing the permutation
    lets the driver's surrogate scoring reuse per-position log-probs of
    the ORIGINAL stream for every position whose whole Markov context maps
    contiguously (see ``markov_baseline.surrogate_cross_entropy``).
    """
    tokens = np.asarray(tokens)
    hours = np.asarray(hours)
    if tokens.shape != hours.shape:
        raise FoldError("tokens and hours must share shape")
    src = hour_block_shuffle_perm(hours, block_len=block_len, rng=rng)
    return tokens[src]


def hour_block_shuffle_perm(
    hours: np.ndarray,
    *,
    block_len: int = BLOCK_LEN_EVENTS,
    rng: np.random.Generator,
) -> np.ndarray:
    """Source-index permutation of one within-hour-of-day block shuffle.

    Returns ``src`` (int64, len(hours)) such that ``tokens[src]`` is the
    registered surrogate stream: ``surrogate[t] = original[src[t]]``. RNG
    consumption is EXACTLY one ``rng.permutation(n_blocks)`` per hour-of-day
    group with more than one block, iterated in hour order 0..23 — identical
    to the historical token-moving implementation (the registered
    deterministic seed discipline therefore reproduces the same 200
    surrogates bit-for-bit). Groups with ``<= block_len`` events are the
    identity (single block), exactly as before.
    """
    hours = np.asarray(hours)
    if block_len < 1:
        raise FoldError("block_len must be >= 1")
    if hours.size and (hours.min() < 0 or hours.max() > 23):
        raise FoldError("hours must be 0..23")
    src = np.arange(hours.size, dtype=np.int64)
    for h in range(24):
        idx = np.nonzero(hours == h)[0]
        m = idx.size
        if m <= block_len:
            continue  # single block -> identity
        n_blocks = int(np.ceil(m / block_len))
        starts = [b * block_len for b in range(n_blocks)]
        perm = rng.permutation(n_blocks)
        order = np.concatenate(
            [np.arange(starts[b], min(starts[b] + block_len, m)) for b in perm]
        )
        src[idx] = idx[order]
    return src


# ----------------------------------------------------------------------------
# Gap p-value + gate arithmetic (gate-neutral measurements)
# ----------------------------------------------------------------------------

def surrogate_gap_p(observed_gap: float, surrogate_gaps: np.ndarray) -> float:
    """One-sided empirical p for the CE gap vs. the surrogate null.

    p = (#{gap_surr >= gap_obs} + 1) / (n + 1). NaN inputs give NaN
    (the driver maps that to a failing 1.0 for BH — gate-neutral).
    """
    g = np.asarray(surrogate_gaps, dtype=np.float64)
    g = g[np.isfinite(g)]
    if g.size == 0 or not np.isfinite(observed_gap):
        return float("nan")
    n_ge = int(np.sum(g >= observed_gap))
    return (n_ge + 1) / (g.size + 1)


def relative_ce_gap(markov_ce: float, transformer_ce: float) -> float:
    """Relative OOS CE improvement (markov - transformer) / markov."""
    if not (np.isfinite(markov_ce) and np.isfinite(transformer_ce)) or markov_ce <= 0:
        return float("nan")
    return (markov_ce - transformer_ce) / markov_ce


__all__ = [
    "BLOCK_LEN_EVENTS",
    "EMBARGO_DAYS",
    "FAMILY_SIZE",
    "FDR_ALPHA",
    "FDR_FAMILY",
    "Fold",
    "FoldError",
    "N_FOLDS",
    "N_SEEDS",
    "N_SURROGATES_DEFAULT",
    "REL_CE_GAP_MIN",
    "SURROGATE_PERCENTILE",
    "SYMBOLS_PASS_MIN",
    "benjamini_hochberg",
    "hour_block_shuffle",
    "hour_block_shuffle_perm",
    "relative_ce_gap",
    "surrogate_gap_p",
    "walk_forward_folds",
]
