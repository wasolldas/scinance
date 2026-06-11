"""Purged walk-forward splitter for the C-42 vol repro (WP-4).

Implements the H-02 test design (``hypothesis_registry.md`` H-02):

- chronological walk-forward folds (no shuffling, no random CV);
- >= 2 disjoint OOS windows;
- a *purge* gap around every train/test boundary equal to the target horizon
  (60 bars) PLUS a parametric *embargo* (default 1 day = 1440 bars), so that
  no training row's forward 60-min target window can overlap an OOS row, and
  no OOS row sits inside the embargo shadow of a training row;
- deterministic, chronological window placement — "keine diskretionäre
  Fensterwahl" (H-02). Given (n_rows, n_folds, embargo) the fold boundaries
  are fully determined.

This is the antithesis of ``src/bybit_edge/training/dataset.py``'s plain
60/20/20 chronological split (which does NOT purge) — that module is the
negative reference called out in the workplan.

The splitter operates on a positional index (row positions 0..n-1 of an
already-cleaned, ts-sorted feature/target frame). The caller is responsible
for passing rows in chronological order with NaN feature/target rows removed.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .target import HORIZON_BARS

#: Default embargo in 1-minute bars (1 trading day) — parametric per H-02.
DEFAULT_EMBARGO_BARS = 1440

#: Purge always includes the target horizon so a train row's forward label
#: window cannot reach into the test fold.
PURGE_HORIZON_BARS = HORIZON_BARS


@dataclass(frozen=True)
class Fold:
    """One purged walk-forward fold (positional indices into the cleaned frame)."""

    fold_id: int
    train_idx: np.ndarray  # int positions, train block
    test_idx: np.ndarray   # int positions, OOS block
    train_span: tuple[int, int]  # (first, last) train position, inclusive
    test_span: tuple[int, int]   # (first, last) test position, inclusive
    purge_bars: int              # gap removed between train end and test start


def purged_walk_forward(
    n_rows: int,
    n_folds: int = 2,
    embargo_bars: int = DEFAULT_EMBARGO_BARS,
    min_train_bars: int = HORIZON_BARS * 2,
    min_test_bars: int = HORIZON_BARS,
) -> list[Fold]:
    """Build chronological purged walk-forward folds.

    Expanding-window scheme: fold ``k`` trains on everything up to the start of
    OOS block ``k`` (minus the purge+embargo gap) and tests on OOS block ``k``.
    The data after an initial training warm-up is partitioned into ``n_folds``
    contiguous, disjoint OOS blocks placed back-to-back in time.

    Parameters
    ----------
    n_rows:
        Number of cleaned, chronologically ordered rows.
    n_folds:
        Number of disjoint OOS windows (>= 2 per H-02).
    embargo_bars:
        Extra bars purged between the train block and the OOS block, on top of
        the target horizon (PURGE_HORIZON_BARS). Total gap = horizon + embargo.
    min_train_bars, min_test_bars:
        Sanity floors; a configuration that cannot satisfy them raises.

    Returns
    -------
    list[Fold]: exactly ``n_folds`` folds, OOS blocks strictly disjoint and
    chronologically increasing.

    Raises
    ------
    ValueError: if n_folds < 2, or the data is too short for the requested
        folds + purge + embargo.
    """
    if n_folds < 2:
        raise ValueError("H-02 requires >= 2 disjoint OOS windows (n_folds >= 2)")
    if embargo_bars < 0:
        raise ValueError("embargo_bars must be >= 0")
    gap = PURGE_HORIZON_BARS + embargo_bars

    # Reserve an initial warm-up training region, then split the remainder into
    # n_folds equal OOS blocks. The first fold's train block is the warm-up;
    # later folds expand to include earlier OOS blocks (minus the gap).
    warmup = max(min_train_bars + gap, n_rows // (n_folds + 1))
    oos_total = n_rows - warmup
    if oos_total < n_folds * (min_test_bars + gap):
        raise ValueError(
            f"too few rows ({n_rows}) for {n_folds} purged folds "
            f"(need >= warmup {warmup} + {n_folds}*(test {min_test_bars}+gap {gap}))"
        )
    block = oos_total // n_folds

    folds: list[Fold] = []
    for k in range(n_folds):
        test_start = warmup + k * block
        test_end = warmup + (k + 1) * block - 1 if k < n_folds - 1 else n_rows - 1
        # Train: everything from 0 up to (test_start - gap - 1), inclusive.
        train_end = test_start - gap - 1
        train_start = 0
        if train_end - train_start + 1 < min_train_bars:
            raise ValueError(
                f"fold {k}: train block too short after purge "
                f"({train_end - train_start + 1} < {min_train_bars})"
            )
        train_idx = np.arange(train_start, train_end + 1, dtype=np.int64)
        test_idx = np.arange(test_start, test_end + 1, dtype=np.int64)
        folds.append(
            Fold(
                fold_id=k,
                train_idx=train_idx,
                test_idx=test_idx,
                train_span=(train_start, train_end),
                test_span=(test_start, test_end),
                purge_bars=gap,
            )
        )
    return folds


def assert_disjoint_and_purged(folds: list[Fold]) -> None:
    """Defensive check used by the smoke test: folds disjoint + gap respected.

    Verifies, for every fold, that ``max(train_idx) + gap < min(test_idx)``
    (purge+embargo gap honoured) and that OOS blocks of different folds do not
    overlap. Raises ``AssertionError`` on violation.
    """
    for f in folds:
        if f.train_idx.size and f.test_idx.size:
            gap_observed = int(f.test_idx.min()) - int(f.train_idx.max())
            assert gap_observed > f.purge_bars, (
                f"fold {f.fold_id}: train/test gap {gap_observed} "
                f"<= required purge {f.purge_bars}"
            )
    test_blocks = sorted((f.test_span for f in folds), key=lambda s: s[0])
    for (a_lo, a_hi), (b_lo, b_hi) in zip(test_blocks, test_blocks[1:]):
        assert a_hi < b_lo, f"OOS blocks overlap: ({a_lo},{a_hi}) vs ({b_lo},{b_hi})"
