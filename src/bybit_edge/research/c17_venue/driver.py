"""Orchestration + gate-neutral payload for the H-17 venue-fingerprint gate.

Runs the registered measurement (registry H-17, Welle 5):

  * 10 nodes = 5 symbols x {bybit, binance}, publicTrade only, 5-minute
    event windows with 4 per-day-quantile-normalised channels (features.py),
  * Leave-One-Symbol-Out, 5 folds: train on the 8 nodes of the other 4
    symbols, test on the held-out symbol restricted to the LAST 3 WEEKS of
    its available window dates (registry: Test-Zeitraum je Fold = letzte
    3 Wochen des ausgelassenen Symbols),
  * per fold: fresh InfoNCE contrastive training (positives = same node,
    negatives = full batch, batch >= 2048), frozen linear probe for the
    venue label, held-out BALANCED accuracy,
  * NULL (verdict-bearing): within-symbol-within-day permutation of the
    TRAIN venue labels, then FULL RETRAINING of encoder + probe per
    replicate (20 retrainings per fold — registry: KEIN Frozen-Model-
    Shuffling; the permuted venue labels also re-define the node identity
    used for the contrastive positives, so the whole representation is
    retrained under the null). Held-out accuracy is always measured
    against the TRUE test labels; fold p = add-one empirical p of the
    observed accuracy against the 20 null accuracies,
  * ONE F-VENUE BH-FDR family over the 5 fold p-values (alpha = 0.10),
  * secondary (NOT verdict-bearing as a series, but input to a binding
    gate): daily cross-venue embedding-distance series from the held-out
    test embeddings (redundancy.py),
  * PRE-REGISTERED NON-REDUNDANCY GATE against c12_frag/H-12:
    |Spearman rho| < 0.6 vs. the c12 daily lambda2/IPR series on
    overlapping days; |rho| >= 0.6 = REDUNDANT = DROP regardless of
    accuracy (redundancy.redundancy_gate),
  * COMPUTE GATE (binding): a full run WITHOUT a real CUDA device is NEVER
    verdict-bearing — the payload carries ``compute.verdict_bearing`` and
    ``weiter_indication`` is forced False (with reason) when it is not.

Checkpoint/resume (c16_arrow pattern — added BEFORE the first successful
H-17 run; H-16 burned ~36 GPU-h before its checkpoint retrofit): with
``ckpt_dir`` set (CLI default ``<out-dir>/c17_venue_ckpt``; runner: STABLE
``results\\h17_checkpoints``), EVERY completed single training —
(fold_symbol, kind, index) with kind in {main, null}; main = the fold's
one InfoNCE training + frozen probe, null = one permutation RETRAINING —
is written IMMEDIATELY as one JSON (atomic tmp+os.replace,
:func:`_write_training_checkpoint`); a re-run with the SAME ``ckpt_dir``
loads finished trainings back and only trains what is missing, so an
interrupt loses at most the training in flight. Every checkpoint carries a
fingerprint over ALL result-relevant run parameters
(:func:`make_run_fingerprint`); ANY mismatch raises
:class:`CheckpointMismatchError` (a hard ``ValueError`` — NEVER degraded
to a sentinel/skipped fold). A run assembled from checkpoints produces the
IDENTICAL payload as an uninterrupted run (gate/verdict logic untouched);
see the RNG-identity audit note at the checkpoint section below.

GATE-NEUTRAL payload (c12_frag/H-04b convention): every criterion is
reported individually plus a ``weiter_indication`` flag — the driver
renders NO overall verdict; the gate-auditor adjudicates against H-17.

KAPITALFREI: pure structure/existence question, ``capital_free: true``;
no friction, bps, PnL, Sharpe field anywhere. A trading consequence would
be a NEW H-17b, NOT implied.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .contrastive import (
    BATCH_SIZE_MIN,
    DEFAULT_LR,
    DEFAULT_STEPS,
    STEPS_MIN,
    TEMPERATURE,
    probe_predict,
    train_linear_probe,
)
from .encoder import EMBED_DIM, PROJ_DIM, NumpyFallbackEncoder
from .features import N_CHANNELS, NodeWindows
from .redundancy import (
    REDUNDANCY_RHO_MAX,
    daily_embedding_distance_series,
    redundancy_gate,
)
from .stats import (
    FDR_ALPHA,
    balanced_accuracy,
    benjamini_hochberg,
    empirical_p_ge,
    permute_within_groups,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-17"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-VENUE"

#: Registered gate thresholds (registry H-17, verbatim):
BALANCED_ACC_MIN = 0.60        # per-fold held-out balanced accuracy floor
MIN_PASSING_FOLDS = 4          # >= 4 of 5 LOSO folds
N_FOLDS = 5
POOLED_ACC_MIN = 0.55          # hard DROP below (pooled over all test windows)
N_PERMUTATIONS = 20            # retrainings per fold (registered null)
TEST_WEEKS = 3                 # last 3 weeks of the held-out symbol
TEST_DAYS = TEST_WEEKS * 7

COMPUTE_NOTE = (
    "Compute-Gate (verbindlich): Batch >= 2048 ist Teil der registrierten "
    "Methode; ein voller Lauf ohne echtes CUDA-Device ist NIEMALS "
    "verdikt-tragend (Pipeline-Smoke), weiter_indication wird dann "
    "erzwungen False."
)


# ---------------------------------------------------------------------------
# Panel stacking + LOSO folds
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Panel:
    """All node windows stacked: parallel arrays over windows."""

    x: np.ndarray          # (N, 4, L) float32
    mask: np.ndarray       # (N, L) bool
    dates: np.ndarray      # (N,) object 'YYYY-MM-DD'
    symbols: np.ndarray    # (N,) object
    venues: np.ndarray     # (N,) object (exchange)


def stack_nodes(nodes: list[NodeWindows]) -> Panel:
    """Stack per-node window sets into one panel."""
    if not nodes:
        raise ValueError("empty node list")
    x = np.concatenate([n.x for n in nodes], axis=0)
    mask = np.concatenate([n.mask for n in nodes], axis=0)
    dates = np.concatenate([n.dates for n in nodes], axis=0)
    symbols = np.concatenate(
        [np.array([n.symbol] * n.x.shape[0], dtype=object) for n in nodes], axis=0)
    venues = np.concatenate(
        [np.array([n.exchange] * n.x.shape[0], dtype=object) for n in nodes], axis=0)
    return Panel(x=x, mask=mask, dates=dates, symbols=symbols, venues=venues)


@dataclass(slots=True)
class Fold:
    """One Leave-One-Symbol-Out fold."""

    held_out_symbol: str
    train_idx: np.ndarray
    test_idx: np.ndarray
    test_start_date: str
    test_end_date: str
    #: ALL windows of the held-out symbol (H-23 full-panel inference,
    #: registry Nachtrag 2026-08-18 (1)). Fully determined by the panel and
    #: the held-out symbol, both already pinned by the run fingerprint.
    holdout_idx: np.ndarray = None  # type: ignore[assignment]


def _iso_to_date(s: str) -> datetime:
    return datetime.strptime(str(s), "%Y-%m-%d").replace(tzinfo=timezone.utc)


def build_loso_folds(panel: Panel, symbols: tuple[str, ...]) -> list[Fold]:
    """Leave-One-Symbol-Out folds (registry H-17, 5 folds).

    Train = ALL windows of the other symbols (both venues). Test = windows
    of the held-out symbol whose date lies in the LAST ``TEST_DAYS`` days of
    that symbol's available dates (both venues). Windows of the held-out
    symbol BEFORE its test period are used NOWHERE (strict symbol
    exclusion — no leak of the held-out symbol into training).
    """
    folds: list[Fold] = []
    for sym in symbols:
        sym_sel = panel.symbols == sym
        if not np.any(sym_sel):
            raise ValueError(f"no windows for symbol {sym!r}")
        sym_dates = panel.dates[sym_sel]
        max_d = max(_iso_to_date(d) for d in np.unique(sym_dates))
        cutoff = max_d - timedelta(days=TEST_DAYS - 1)
        in_test = np.array(
            [_iso_to_date(d) >= cutoff for d in panel.dates], dtype=bool)
        train_idx = np.nonzero(~sym_sel)[0]
        test_idx = np.nonzero(sym_sel & in_test)[0]
        if test_idx.size == 0:
            raise ValueError(f"empty test period for held-out symbol {sym!r}")
        folds.append(Fold(
            held_out_symbol=str(sym),
            train_idx=train_idx,
            test_idx=test_idx,
            test_start_date=cutoff.strftime("%Y-%m-%d"),
            test_end_date=max_d.strftime("%Y-%m-%d"),
            holdout_idx=np.nonzero(sym_sel)[0],
        ))
    return folds


# ---------------------------------------------------------------------------
# One fold: real training + registered permutation null (full retraining)
# ---------------------------------------------------------------------------

def _venue_to_int(venues: np.ndarray, venue_order: tuple[str, ...]) -> np.ndarray:
    lut = {v: i for i, v in enumerate(venue_order)}
    return np.array([lut[str(v)] for v in venues], dtype=np.int64)


def _node_ids(venues: np.ndarray, symbols: np.ndarray) -> np.ndarray:
    return np.array([f"{v}:{s}" for v, s in zip(venues, symbols)], dtype=object)


# ---------------------------------------------------------------------------
# Checkpoint/resume (per completed single training; c16_arrow pattern)
#
# CHANGELOG (2026-07, added BEFORE the first successful H-17 run): H-16
# demonstrated the failure mode this section prevents — ~36 GPU-h were lost
# to reboot/timeout because results were only written at the very end of the
# multi-day plan. H-17 is the same shape (~105 GPU trainings, ~35h+, one
# JSON at the end), so the c16_arrow checkpoint discipline is applied here
# from day 1: one small JSON per completed single training (atomic
# tmp+os.replace), a fingerprint over ALL result-relevant parameters, and a
# HARD abort (CheckpointMismatchError, a ValueError) on any staleness —
# stale checkpoints are NEVER silently mixed and never degraded to a
# sentinel/skipped fold.
#
# RNG-IDENTITY AUDIT (requirement for resume == uninterrupted run): every
# training ALREADY derives its RNG deterministically and INDEPENDENTLY from
# (base seed, fold_index, kind, index) — the encoder seed is
# ``seed*1000 + fold_index`` for the main training and
# ``seed*1000 + fold_index*100 + r + 1`` for null retraining r (see
# _encoder_seed; values UNCHANGED vs. the pre-checkpoint inline
# derivation), the permutation DATA rng is
# ``np.random.default_rng((seed, fold_index, r))`` per replicate
# (unchanged), and the probe seed is the base ``seed`` (unchanged). NO
# global/consecutive RNG stream is consumed across trainings, so skipping
# already-checkpointed trainings cannot shift any later training's
# randomness: a resumed run is result-identical to an uninterrupted one.
# The seed derivation did NOT need to change.
# ---------------------------------------------------------------------------

#: Checkpoint file schema version (bump on incompatible layout changes).
CKPT_SCHEMA_VERSION = 1

#: The two training kinds of one LOSO fold, in execution order: ``main`` =
#: the fold's one real InfoNCE training + frozen probe (index 0), ``null`` =
#: one FULL permutation retraining (index 0..n_perm-1).
TRAINING_KINDS: tuple[str, ...] = ("main", "null")


class CheckpointMismatchError(ValueError):
    """A checkpoint's fingerprint/task identity contradicts the CURRENT run.

    Raised (hard abort, NEVER silently mixed or degraded to a sentinel/
    skipped fold) when a checkpoint under ``ckpt_dir`` was written by a run
    with different result-relevant parameters — e.g. another data window,
    other seed values, another encoder class/compute provenance, or other
    training hyperparameters. Same discipline as c16_arrow (c14/c15 round-2
    staleness findings). ``run()`` deliberately re-raises this — a poisoned
    checkpoint directory must be resolved by the operator, never papered
    over.
    """


def _encoder_seed(seed: int, fold_index: int, kind: str, index: int) -> int:
    """THE per-training encoder seed (deterministic, no global stream).

    Identical to the pre-checkpoint inline derivation (behaviour-neutral):
    ``seed*1000 + fold_index`` for the main training,
    ``seed*1000 + fold_index*100 + index + 1`` for null retraining
    ``index`` (assumes n_perm <= 98; registered size is 20).
    """
    if kind == "main":
        if index != 0:
            raise ValueError(f"main training has exactly one index (0), got {index}")
        return int(seed) * 1000 + int(fold_index)
    if kind == "null":
        return int(seed) * 1000 + int(fold_index) * 100 + int(index) + 1
    raise ValueError(f"unknown training kind {kind!r} (want {TRAINING_KINDS})")


def _json_stable(v: Any) -> Any:
    """Coerce to JSON-round-trip-stable types (fingerprint invariant:
    ``json.loads(json.dumps(fp)) == fp``)."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_json_stable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _json_stable(x) for k, x in v.items()}
    return str(v)


def make_run_fingerprint(
    *,
    symbols: tuple[str, ...] | list[str],
    venues: tuple[str, ...] | list[str],
    start_date: str,
    end_date: str,
    folds: list[Fold],
    n_windows_total: int,
    seed: int,
    n_perm: int,
    batch_size: int,
    fit_kwargs: dict[str, Any],
    cuda_used: bool,
    torch_available: bool,
    encoder_class: str,
) -> dict[str, Any]:
    """Fingerprint over ALL result-relevant H-17 run parameters.

    Stored in every checkpoint and compared VERBATIM on load (JSON-stable
    types only). Covers — c16/c15 round-2 lesson, binding list: compute
    provenance (``cuda_used`` / ``encoder_class``: a numpy-fallback smoke
    run's checkpoints must never be adopted by a real torch/CUDA run), the
    symbol universe IN ORDER (``fold_index`` enters every encoder seed),
    the venue order (defines the probe's integer labels), the data window
    (start/end resp. Cutoff), the DERIVED fold definitions (held-out
    symbol, test period = last :data:`TEST_DAYS` days of that symbol's
    dates, train/test window counts), the panel size, seed COUNTS and the
    fully derived per-training seed VALUES, the permutation-data seed
    scheme, batch size, the effective contrastive training config
    (steps/lr/temperature via ``fit_kwargs`` + module defaults), the
    encoder architecture constants and the frozen-probe config.
    """
    fold_defs = [
        {
            "fold_index": int(i),
            "held_out_symbol": str(f.held_out_symbol),
            "test_start_date": str(f.test_start_date),
            "test_end_date": str(f.test_end_date),
            "n_train_windows": int(f.train_idx.size),
            "n_test_windows": int(f.test_idx.size),
        }
        for i, f in enumerate(folds)
    ]
    return {
        "ckpt_schema_version": CKPT_SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        # compute provenance (numpy-smoke checkpoints never feed a GPU run):
        "cuda_used": bool(cuda_used),
        "torch_available": bool(torch_available),
        "encoder_class": str(encoder_class),
        "symbols": [str(s) for s in symbols],
        "venues": [str(v) for v in venues],
        "start_date": str(start_date),
        "end_date": str(end_date),
        "test_days": int(TEST_DAYS),
        "folds": fold_defs,
        "n_windows_total": int(n_windows_total),
        "seed": int(seed),
        "n_null_retrainings": int(n_perm),
        # fully derived per-training seed VALUES (not just the base seed):
        "training_seeds": {
            f.held_out_symbol: {
                "main": [_encoder_seed(seed, i, "main", 0)],
                "null": [
                    _encoder_seed(seed, i, "null", r) for r in range(n_perm)
                ],
            }
            for i, f in enumerate(folds)
        },
        "perm_data_seed_scheme": (
            "np.random.default_rng((seed, fold_index, r)) je Replikat; "
            "Within-Symbol-Within-Day-Permutation (permute_within_groups)"
        ),
        "probe_seed": int(seed),
        "probe_config": (
            "train_linear_probe: numpy logistic regression, class-balanced, "
            "standardised features, l2=1e-3, iters=400, lr=0.5"
        ),
        # contrastive training config (a change here changes every result):
        "batch_size": int(batch_size),
        "batch_size_registered_min": int(BATCH_SIZE_MIN),
        "fit_kwargs": _json_stable(dict(fit_kwargs)),
        "temperature_default": float(TEMPERATURE),
        "steps_default": int(DEFAULT_STEPS),
        "lr_default": float(DEFAULT_LR),
        # encoder architecture constants:
        "architecture": (
            "TemporalCNN dilatiert (k=5, dil 1/2/4/8, hidden 128) + "
            "Masked-Mean-Pool + Projection-Head; Probe auf Pre-Projection-"
            "Embedding"
        ),
        "n_channels": int(N_CHANNELS),
        "embed_dim": int(EMBED_DIM),
        "proj_dim": int(PROJ_DIM),
    }


def _training_ckpt_path(ckpt_dir: Path, fold_symbol: str, kind: str, index: int) -> Path:
    return Path(ckpt_dir) / fold_symbol / f"{kind}_{int(index):03d}.json"


def _write_training_checkpoint(
    path: Path,
    *,
    fingerprint: dict[str, Any],
    task: dict[str, Any],
    result: dict[str, Any],
    wall_seconds: float,
) -> None:
    """Atomic tmp+os.replace write of ONE finished training (c16 pattern).

    Deliberately NO NaN->null cleaning here (unlike the final payload's
    ``_dumps``): the main checkpoint carries the held-out embedding matrix
    and predictions, which must survive the JSON round trip BIT-exactly for
    the resume==uninterrupted-run guarantee (Python json round-trips floats
    exactly, incl. NaN/Infinity tokens).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    payload = {
        "ckpt_schema_version": CKPT_SCHEMA_VERSION,
        "task": task,
        "fingerprint": fingerprint,
        "wall_seconds": round(float(wall_seconds), 3),
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result": result,
    }
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


#: Result keys a checkpoint must carry to be resumable, per training kind.
#: ``fit_info`` is REQUIRED for both kinds: the round-2 compute-gate fields
#: ``min_steps`` / ``min_effective_batch_size`` are aggregated over the
#: main fit AND every null retraining, so they must be reconstructable from
#: checkpoints alone.
_REQUIRED_RESULT_KEYS = {
    "main": ("balanced_accuracy", "fit_info", "y_pred", "emb_test"),
    # H-23 full-panel main training: same payload PLUS the held-out symbol's
    # complete embedding matrix. A checkpoint missing it must be retrained,
    # never adopted (it could not serve the full-panel distance series).
    "main_full": ("balanced_accuracy", "fit_info", "y_pred", "emb_test",
                  "emb_holdout"),
    "null": ("balanced_accuracy", "fit_info"),
}


def _load_training_checkpoint(
    path: Path,
    *,
    fingerprint: dict[str, Any],
    task: dict[str, Any],
    expected_n_test: int | None = None,
    expected_n_holdout: int | None = None,
) -> dict[str, Any] | None:
    """Load one training checkpoint; ``None`` = retrain, mismatch = ABORT.

    Semantics (deliberately asymmetric, c16/c14/c15 round-2 discipline):
      * missing file / unreadable / corrupt JSON / result lacking the
        required fields or shapes -> ``None`` (the training is redone);
      * fingerprint OR task identity (fold symbol/index, kind, index,
        seeds) mismatch -> :class:`CheckpointMismatchError` (HARD abort,
        re-raised by ``run()``): a checkpoint written under different
        result-relevant parameters in the same ``ckpt_dir`` must never be
        mixed into this run. Use a separate --ckpt-dir per configuration
        (smoke runs MUST NOT share the production checkpoint dir) or
        delete the directory to retrain everything.
    """
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or "result" not in payload or "fingerprint" not in payload:
        return None
    stored_fp = payload.get("fingerprint")
    if stored_fp != fingerprint:
        diff_keys = sorted(
            k for k in (set(fingerprint) | set(stored_fp if isinstance(stored_fp, dict) else {}))
            if not isinstance(stored_fp, dict) or stored_fp.get(k) != fingerprint.get(k)
        )
        raise CheckpointMismatchError(
            f"H-17 checkpoint-staleness violation: {path} was written by a run "
            f"with DIFFERENT result-relevant parameters (mismatching fingerprint "
            f"keys: {diff_keys}). Stale checkpoints are NEVER silently mixed "
            f"(c16/c14/c15 round-2 discipline). Fix: use a separate --ckpt-dir "
            f"per configuration (smoke/CPU runs must not share the production "
            f"checkpoint dir), or delete the checkpoint directory to retrain "
            f"everything under the current parameters."
        )
    stored_task = payload.get("task")
    if stored_task != task:
        raise CheckpointMismatchError(
            f"H-17 checkpoint-identity violation: {path} carries task "
            f"{stored_task!r} but this run expects {task!r} (file "
            f"renamed/copied, or the seed derivation changed). Delete/clear "
            f"the checkpoint directory — never mix mismatched checkpoints."
        )
    result = payload["result"]
    if not isinstance(result, dict):
        return None
    kind = task.get("kind")
    if kind not in _REQUIRED_RESULT_KEYS:
        raise ValueError(
            f"unknown checkpoint task kind {kind!r} — add it to "
            "_REQUIRED_RESULT_KEYS before using it (a new kind without an "
            "entry would silently skip the completeness check)")
    for key in _REQUIRED_RESULT_KEYS[kind]:
        if key not in result:
            return None
    acc = result.get("balanced_accuracy")
    if isinstance(acc, bool) or not isinstance(acc, (int, float)):
        return None  # NaN round-trips, but null/garbage -> retrain honestly
    if not isinstance(result.get("fit_info"), dict):
        return None
    if expected_n_test is not None:
        y_pred = result.get("y_pred")
        emb = result.get("emb_test")
        if not isinstance(y_pred, list) or len(y_pred) != expected_n_test:
            return None
        if not isinstance(emb, list) or len(emb) != expected_n_test:
            return None
    if expected_n_holdout is not None:
        emb_ho = result.get("emb_holdout")
        if not isinstance(emb_ho, list) or len(emb_ho) != expected_n_holdout:
            return None
    return result


def count_existing_checkpoints(
    ckpt_dir: Path | str,
    fold_symbols: list[str] | tuple[str, ...],
    *,
    n_perm: int,
) -> tuple[int, int]:
    """(present, total) checkpoint files over the run's full training plan.

    Existence-only pre-count for the start-of-run log — the binding
    fingerprint/identity check still happens on every actual load.
    """
    ckpt = Path(ckpt_dir)
    n_have = 0
    n_total = 0
    for fold_symbol in fold_symbols:
        for kind, count in (("main", 1), ("null", n_perm)):
            for index in range(count):
                n_total += 1
                if _training_ckpt_path(ckpt, fold_symbol, kind, index).exists():
                    n_have += 1
    return n_have, n_total


def run_fold(
    panel: Panel,
    fold: Fold,
    *,
    encoder_factory: Callable[[int], Any],
    venue_order: tuple[str, ...],
    fit_kwargs: dict[str, Any] | None = None,
    n_perm: int = N_PERMUTATIONS,
    seed: int = 42,
    fold_index: int = 0,
    ckpt_dir: Path | str | None = None,
    fingerprint: dict[str, Any] | None = None,
    full_panel_distance: bool = False,
) -> dict[str, Any]:
    """Run one LOSO fold: real training + n_perm FULL null retrainings.

    Null semantics (registered, binding): per replicate the TRAIN venue
    labels are permuted within each (symbol, UTC day) cell; the permuted
    venue labels re-define BOTH the contrastive node identities AND the
    probe targets; encoder + probe are retrained FROM SCRATCH (fresh
    encoder from the factory — no frozen-model shuffling); the held-out
    balanced accuracy is measured against the TRUE test labels.

    Checkpoint/resume: with ``ckpt_dir`` set (requires ``fingerprint``),
    every completed training is immediately persisted to
    ``<ckpt_dir>/<fold_symbol>/<kind>_<index>.json`` (atomic
    tmp+os.replace) and a later call with the SAME ``ckpt_dir`` resumes it
    instead of retraining. Permutation DATA generation is skipped entirely
    for resumed null trainings — safe because each replicate derives its
    rng independently (see the RNG-identity audit note above). Per-training
    encoder seeds come from :func:`_encoder_seed` (identical values to the
    pre-checkpoint inline derivation), so a resumed run is result-identical
    to an uninterrupted one. A stale checkpoint raises
    :class:`CheckpointMismatchError` (never silently mixed).
    """
    fit_kwargs = dict(fit_kwargs or {})
    ckpt = Path(ckpt_dir) if ckpt_dir is not None else None
    if ckpt is not None and fingerprint is None:
        raise ValueError("run_fold: ckpt_dir set but fingerprint missing")
    tr, te = fold.train_idx, fold.test_idx
    # H-23 (registry Nachtrag 2026-08-18 (1)): embed EVERY window of the
    # held-out symbol, not only its test slice. The encoder never saw this
    # symbol at all, so symbol exclusion holds for every embedded window;
    # and since ``train_idx`` carries NO date filter, the encoder's exposure
    # to dates is identical for early and late held-out windows.
    ho = (fold.holdout_idx if (full_panel_distance
                               and fold.holdout_idx is not None) else te)
    x_tr, m_tr = panel.x[tr], panel.mask[tr]
    x_te, m_te = panel.x[te], panel.mask[te]
    x_ho, m_ho = (panel.x[ho], panel.mask[ho])
    y_tr = _venue_to_int(panel.venues[tr], venue_order)
    y_te = _venue_to_int(panel.venues[te], venue_order)
    # Audit finding H-2: a LOSO test period can degenerate to a SINGLE venue
    # class (e.g. one venue's backfill for the held-out symbol stops weeks
    # before the other's) -- balanced_accuracy then collapses to plain
    # single-class recall, trivially reachable by a venue-biased probe. Such
    # a fold is NOT AUSWERTBAR and must never be scored as "passed", however
    # high the recall or however low the resulting p-value looks.
    evaluable = bool(np.unique(y_te).size >= 2)
    groups_tr = np.array(
        [f"{s}|{d}" for s, d in zip(panel.symbols[tr], panel.dates[tr])],
        dtype=object)

    # --- real training ----------------------------------------------------
    # Encoder seed via _encoder_seed (== seed*1000 + fold_index, the exact
    # pre-checkpoint inline value — behaviour-neutral).
    main_seed = _encoder_seed(seed, fold_index, "main", 0)
    # H-23 checkpoint boundary (registry Nachtrag 2026-08-18 (2)): the GLOBAL
    # fingerprint stays untouched so the 100 null retrainings remain
    # resumable; only the MAIN trainings are invalidated, via a distinct
    # ``kind`` (own path) plus ``n_holdout_windows`` in the task identity.
    main_kind = "main_full" if full_panel_distance else "main"
    main_task = {
        "fold_symbol": fold.held_out_symbol, "fold_index": int(fold_index),
        "kind": main_kind, "index": 0,
        "encoder_seed": int(main_seed), "probe_seed": int(seed),
    }
    if full_panel_distance:
        main_task["n_holdout_windows"] = int(ho.size)
    main_path = None
    cached_main = None
    if ckpt is not None:
        main_path = _training_ckpt_path(ckpt, fold.held_out_symbol, main_kind, 0)
        cached_main = _load_training_checkpoint(
            main_path, fingerprint=fingerprint, task=main_task,
            expected_n_test=int(te.size),
            expected_n_holdout=int(ho.size) if full_panel_distance else None)
    if cached_main is not None:
        acc = float(cached_main["balanced_accuracy"])
        fit_info = cached_main["fit_info"]
        pred_te = np.asarray(cached_main["y_pred"], dtype=np.int64)
        emb_te = np.asarray(cached_main["emb_test"], dtype=np.float64)
        emb_ho = (np.asarray(cached_main["emb_holdout"], dtype=np.float64)
                  if full_panel_distance else emb_te)
        print(f"[c17_venue] fold {fold.held_out_symbol}: main training RESUMED "
              f"from checkpoint ({main_path})", file=sys.stderr, flush=True)
    else:
        t0 = time.time()
        enc = encoder_factory(main_seed)
        fit_info = enc.fit(x_tr, m_tr, _node_ids(panel.venues[tr], panel.symbols[tr]),
                           **fit_kwargs)
        emb_tr = enc.embed(x_tr, m_tr)
        emb_te = enc.embed(x_te, m_te)
        emb_ho = enc.embed(x_ho, m_ho) if full_panel_distance else emb_te
        probe = train_linear_probe(emb_tr, y_tr, seed=seed)
        pred_te = probe_predict(emb_te, probe)
        acc = balanced_accuracy(y_te, pred_te)
        if main_path is not None:
            # The main checkpoint persists everything the payload consumes
            # downstream of this training: the fold accuracy + fit_info AND
            # the held-out predictions/embeddings (pooled accuracy + daily
            # cross-venue distance series) — bit-exact via JSON round trip.
            _write_training_checkpoint(
                main_path, fingerprint=fingerprint, task=main_task,
                result={
                    "balanced_accuracy": float(acc),
                    "fit_info": fit_info,
                    "y_pred": [int(v) for v in pred_te],
                    "emb_test": [[float(v) for v in row] for row in emb_te],
                    **({"emb_holdout":
                        [[float(v) for v in row] for row in emb_ho]}
                       if full_panel_distance else {}),
                },
                wall_seconds=time.time() - t0,
            )

    # --- registered permutation null (FULL retraining per replicate) ------
    null_accs: list[float] = []
    null_fit_infos: list[dict[str, Any]] = []
    for r in range(n_perm):
        null_seed = _encoder_seed(seed, fold_index, "null", r)
        null_task = {
            "fold_symbol": fold.held_out_symbol, "fold_index": int(fold_index),
            "kind": "null", "index": int(r),
            "encoder_seed": int(null_seed), "probe_seed": int(seed),
        }
        null_path = None
        if ckpt is not None:
            null_path = _training_ckpt_path(ckpt, fold.held_out_symbol, "null", r)
            cached = _load_training_checkpoint(
                null_path, fingerprint=fingerprint, task=null_task)
            if cached is not None:
                null_accs.append(float(cached["balanced_accuracy"]))
                null_fit_infos.append(cached["fit_info"])
                print(f"[c17_venue] fold {fold.held_out_symbol}: null retraining "
                      f"{r + 1}/{n_perm} RESUMED from checkpoint ({null_path})",
                      file=sys.stderr, flush=True)
                continue
        t0 = time.time()
        rng = np.random.default_rng((seed, fold_index, r))
        y_perm = permute_within_groups(y_tr, groups_tr, rng)
        venues_perm = np.array([venue_order[int(v)] for v in y_perm], dtype=object)
        enc_r = encoder_factory(null_seed)
        fit_info_r = enc_r.fit(x_tr, m_tr, _node_ids(venues_perm, panel.symbols[tr]),
                               **fit_kwargs)
        null_fit_infos.append(fit_info_r)
        emb_tr_r = enc_r.embed(x_tr, m_tr)
        emb_te_r = enc_r.embed(x_te, m_te)
        probe_r = train_linear_probe(emb_tr_r, y_perm, seed=seed)
        pred_r = probe_predict(emb_te_r, probe_r)
        null_accs.append(balanced_accuracy(y_te, pred_r))
        if null_path is not None:
            _write_training_checkpoint(
                null_path, fingerprint=fingerprint, task=null_task,
                result={
                    "balanced_accuracy": float(null_accs[-1]),
                    "fit_info": fit_info_r,
                },
                wall_seconds=time.time() - t0,
            )
        print(f"[c17_venue] fold {fold.held_out_symbol}: null retraining "
              f"{r + 1}/{n_perm} acc={null_accs[-1]:.4f}",
              file=sys.stderr, flush=True)

    p_value = empirical_p_ge(np.array(null_accs), acc)
    # Audit finding M-1: the compute gate must see the ACHIEVED batch size
    # (eff_batch = min(requested, n) per training), not only the CLI-
    # requested value — aggregate the minimum over the main fit AND every
    # null retraining in this fold, so a thin fold can never silently hide
    # under the registered BATCH_SIZE_MIN.
    all_fit_infos = [fit_info, *null_fit_infos]
    achieved_batches = [
        int(fi["batch_size"]) for fi in all_fit_infos if "batch_size" in fi
    ]
    min_effective_batch_size = min(achieved_batches) if achieved_batches else None
    # Audit finding CRIT-1: the compute gate must see the ACHIEVED optimizer
    # step count too, not just report it -- aggregate the minimum over the
    # main fit AND every null retraining in this fold (same pattern as
    # min_effective_batch_size above), so `--steps 0` can never silently
    # produce a "trained: True" verdict-bearing payload.
    achieved_steps = [int(fi["steps"]) for fi in all_fit_infos if "steps" in fi]
    min_steps = min(achieved_steps) if achieved_steps else None
    return {
        "held_out_symbol": fold.held_out_symbol,
        "test_start_date": fold.test_start_date,
        "test_end_date": fold.test_end_date,
        "n_train_windows": int(tr.size),
        "n_test_windows": int(te.size),
        "evaluable": evaluable,
        "balanced_accuracy": float(acc),
        "acc_threshold": BALANCED_ACC_MIN,
        "acc_threshold_met": bool(acc >= BALANCED_ACC_MIN),
        "null_accuracies": [float(a) for a in null_accs],
        "n_null_retrainings": int(n_perm),
        "null_semantics": (
            "Within-Symbol-Within-Day-Permutation der TRAIN-Venue-Labels; "
            "Encoder+Probe je Replikat VOLL neu trainiert (kein Frozen-"
            "Model-Shuffling); Accuracy stets gegen die WAHREN Test-Labels."
        ),
        "p_value": float(p_value),
        "fit_info": fit_info,
        "min_effective_batch_size": min_effective_batch_size,
        "min_steps": min_steps,
        # carried for pooled accuracy + daily distance series (stripped
        # from the JSON payload by run()):
        "_y_true": y_te,
        "_y_pred": pred_te,
        "_emb_test": emb_te,
        "_test_idx": te,
        # H-23: embeddings + indices actually feeding the distance series
        # (== the test slice when full_panel_distance is off).
        "_emb_dist": emb_ho,
        "_dist_idx": ho,
        "n_holdout_windows": int(ho.size),
    }


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------

def run(
    nodes: list[NodeWindows],
    *,
    encoder_factory: Callable[[int], Any] | None = None,
    fit_kwargs: dict[str, Any] | None = None,
    n_perm: int = N_PERMUTATIONS,
    seed: int = 42,
    c12_payload: dict[str, Any] | None = None,
    cuda_used: bool = False,
    torch_available: bool = False,
    batch_size: int = BATCH_SIZE_MIN,
    source: str = "",
    start_date: str = "",
    end_date: str = "",
    ckpt_dir: Path | str | None = None,
    full_panel_distance: bool = False,
    hypothesis_id: str = HYPOTHESIS_ID,
) -> dict[str, Any]:
    """Run the full H-17 measurement; returns the gate-neutral payload.

    ``encoder_factory(seed) -> encoder`` must yield a FRESH encoder with
    ``fit(x, mask, node_ids, **fit_kwargs)`` and ``embed(x, mask)`` (the
    real torch VenueEncoder or the sandbox NumpyFallbackEncoder). Compute
    gating: ``cuda_used`` must reflect a REAL CUDA device; otherwise the
    payload is marked non-verdict-bearing and ``weiter_indication`` is
    forced False.

    ``ckpt_dir``: if given, EVERY completed single training — per fold 1
    main (InfoNCE + probe) + ``n_perm`` null retrainings — is immediately
    checkpointed (atomic tmp+os.replace) to
    ``<ckpt_dir>/<fold_symbol>/<kind>_<index>.json`` and a re-run with the
    SAME ``ckpt_dir`` resumes finished trainings instead of retraining —
    an interrupt (timeout, reboot, closed window) loses at most the single
    training in flight, never the ~35h+ plan. ``start_date``/``end_date``
    (the requested data window / Cutoff) enter the checkpoint fingerprint
    (:func:`make_run_fingerprint`); a fingerprint mismatch raises
    :class:`CheckpointMismatchError` — a hard ``ValueError`` that is
    deliberately NOT caught here (never degraded to a sentinel/skipped
    fold): silently continuing over a poisoned checkpoint directory would
    corrupt every later resume. A run assembled from checkpoints produces
    the identical payload as an uninterrupted run; the gate/verdict logic
    (compute gate, evaluable-fold rule, non-redundancy gate, BH-FDR) is
    untouched by resuming.
    """
    if encoder_factory is None:
        encoder_factory = lambda s: NumpyFallbackEncoder(seed=s)  # noqa: E731

    panel = stack_nodes(nodes)
    symbols = tuple(sorted({str(n.symbol) for n in nodes}))
    venue_order = tuple(sorted({str(n.exchange) for n in nodes}))
    if len(venue_order) != 2:
        raise ValueError(f"H-17 needs exactly 2 venues, got {venue_order}")
    if len(symbols) != N_FOLDS:
        print(f"[c17_venue] WARNING: {len(symbols)} symbols != registered "
              f"{N_FOLDS} — fold count follows the data (dev/smoke runs only; "
              f"a verdict-bearing run needs the registered 5-symbol panel)",
              file=sys.stderr, flush=True)
    folds = build_loso_folds(panel, symbols)

    # probe encoder verdict capability (fallback encoders are never capable)
    probe_enc = encoder_factory(seed)
    encoder_verdict_capable = bool(getattr(probe_enc, "verdict_bearing", False))
    encoder_class = type(probe_enc).__name__
    del probe_enc

    # Checkpoint/resume setup: fingerprint over the DERIVED fold plan (the
    # fold_index enters every encoder seed) and all result-relevant params.
    ckpt = Path(ckpt_dir) if ckpt_dir is not None else None
    ckpt_fingerprint: dict[str, Any] | None = None
    if ckpt is not None:
        ckpt_fingerprint = make_run_fingerprint(
            symbols=symbols, venues=venue_order,
            start_date=start_date, end_date=end_date, folds=folds,
            n_windows_total=int(panel.x.shape[0]), seed=seed, n_perm=n_perm,
            batch_size=batch_size, fit_kwargs=dict(fit_kwargs or {}),
            cuda_used=cuda_used, torch_available=torch_available,
            encoder_class=encoder_class,
        )
        n_have, n_total = count_existing_checkpoints(
            ckpt, [f.held_out_symbol for f in folds], n_perm=n_perm)
        print(f"[c17_venue] Checkpoint/Resume aktiv: {ckpt} — {n_have}/{n_total} "
              f"Trainings bereits als Checkpoint vorhanden, {n_total - n_have} "
              f"noch offen (Fingerprint wird bei jedem Laden geprueft).",
              file=sys.stderr, flush=True)
    else:
        print("[c17_venue] Checkpointing DEAKTIVIERT — ein Abbruch verliert den "
              "GESAMTEN Fortschritt dieses Laufs.", file=sys.stderr, flush=True)

    # NOTE: deliberately NO try/except around the fold loop — in particular
    # a CheckpointMismatchError (stale --ckpt-dir) must propagate out of
    # run() as a hard ValueError and is NEVER degraded to a sentinel or a
    # skipped fold (c16 round-2 staleness discipline).
    fold_records = [
        run_fold(panel, fold, encoder_factory=encoder_factory,
                 venue_order=venue_order, fit_kwargs=fit_kwargs,
                 n_perm=n_perm, seed=seed, fold_index=fi,
                 ckpt_dir=ckpt, fingerprint=ckpt_fingerprint,
                 full_panel_distance=full_panel_distance)
        for fi, fold in enumerate(folds)
    ]

    # ONE F-VENUE BH-FDR family over the fold p-values.
    p_values = [r["p_value"] for r in fold_records]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for r, rej in zip(fold_records, rejected):
        r["fdr_significant"] = bool(rej)
        # Audit finding H-2: a fold whose test period degenerated to a
        # single venue class is NEVER counted as passed, however high its
        # (degenerate) balanced accuracy or however low its p-value.
        r["passed"] = bool(r["acc_threshold_met"] and rej and r["evaluable"])

    # pooled balanced accuracy over ALL held-out test windows.
    y_true_all = np.concatenate([r["_y_true"] for r in fold_records])
    y_pred_all = np.concatenate([r["_y_pred"] for r in fold_records])
    pooled_acc = balanced_accuracy(y_true_all, y_pred_all)

    # secondary: daily cross-venue embedding-distance series. H-17 builds it
    # from the held-out TEST windows only; H-23 (full_panel_distance) builds
    # it from ALL windows of each held-out symbol — same encoder-assignment
    # rule, ~85 instead of ~2 overlap days for the redundancy gate.
    emb_all = np.concatenate([r["_emb_dist"] for r in fold_records], axis=0)
    idx_all = np.concatenate([r["_dist_idx"] for r in fold_records])
    distance = daily_embedding_distance_series(
        emb_all, panel.dates[idx_all], panel.symbols[idx_all],
        panel.venues[idx_all])

    # pre-registered non-redundancy gate against c12_frag/H-12.
    redundancy = redundancy_gate(distance["daily"], c12_payload)

    # H-23 diagnostic (registry Nachtrag 2026-08-18, NOT judgment-bearing):
    # the same gate restricted to the ORIGINAL test-period days. A wide gap
    # to the full-series correlation is a warning flag for the adjudication;
    # only the full-series result carries the verdict.
    redundancy_test_days_only = None
    if full_panel_distance:
        test_days = {str(d) for r in fold_records
                     for d in panel.dates[r["_test_idx"]]}
        sub = {d: v for d, v in distance["daily"].items()
               if str(d) in test_days}
        redundancy_test_days_only = redundancy_gate(sub, c12_payload)
        redundancy_test_days_only["judgment_bearing"] = False

    # gate arithmetic (gate-neutral — the gate-auditor adjudicates).
    n_folds_passed = sum(1 for r in fold_records if r["passed"])
    folds_ok = bool(n_folds_passed >= MIN_PASSING_FOLDS)
    pooled_ok = bool(pooled_acc >= POOLED_ACC_MIN)
    redundancy_ok = bool(redundancy["passed"])

    # compute gate (binding): no real CUDA => never verdict-bearing.
    verdict_bearing = bool(cuda_used and encoder_verdict_capable
                           and batch_size >= BATCH_SIZE_MIN)
    blocked_reasons: list[str] = []
    if not cuda_used:
        blocked_reasons.append("kein echtes CUDA-Device")
    if not encoder_verdict_capable:
        blocked_reasons.append("Nicht-Torch-Fallback-Encoder (Pipeline-Smoke)")
    if batch_size < BATCH_SIZE_MIN:
        blocked_reasons.append(
            f"Batch {batch_size} < registriertes Minimum {BATCH_SIZE_MIN}")
    # Audit finding M-1: also enforce the ACHIEVED batch size, not only the
    # requested one -- a thin fold's train set can silently push
    # eff_batch=min(batch_size, n) below BATCH_SIZE_MIN even when the CLI
    # request was >= 2048.
    achieved_batch_sizes = [
        r["min_effective_batch_size"] for r in fold_records
        if r.get("min_effective_batch_size") is not None
    ]
    min_achieved_batch_size = min(achieved_batch_sizes) if achieved_batch_sizes else None
    if achieved_batch_sizes and min_achieved_batch_size < BATCH_SIZE_MIN:
        verdict_bearing = False
        blocked_reasons.append(
            f"tatsaechlich erreichter Batch {min_achieved_batch_size} < "
            f"registriertes Minimum {BATCH_SIZE_MIN} (mind. ein Fold/"
            f"Retraining unterschritt das Minimum trotz angefordertem "
            f"Batch {batch_size})")
    # Audit finding CRIT-1: the compute gate never inspected the ACHIEVED
    # optimizer step count -- `--steps 0` (argparse has no lower bound)
    # trained NOTHING (a randomly-initialised encoder) yet reported
    # `trained: True` with a compliant batch size, so a real-CUDA run could
    # reach a genuine `weiter_indication=True` with literally zero GPU
    # compute. Aggregate the minimum achieved steps over every fold/
    # retraining (same pattern as the batch-size check above) and force
    # non-verdict-bearing if any of them trained zero steps.
    achieved_steps_all = [
        r["min_steps"] for r in fold_records if r.get("min_steps") is not None
    ]
    min_achieved_steps = min(achieved_steps_all) if achieved_steps_all else None
    if achieved_steps_all and min_achieved_steps < STEPS_MIN:
        verdict_bearing = False
        blocked_reasons.append(
            f"tatsaechlich erreichte Optimizer-Schritte {min_achieved_steps} < "
            f"technische Untergrenze {STEPS_MIN} (mind. ein Fold/Retraining "
            f"trainierte null Schritte -- randominitialisierter Encoder, "
            f"kein echtes Training)")
    if len(symbols) != N_FOLDS:
        verdict_bearing = False
        blocked_reasons.append(
            f"{len(symbols)} Symbole statt registrierter {N_FOLDS}")

    weiter_indication = bool(verdict_bearing and folds_ok and pooled_ok
                             and redundancy_ok)

    for r in fold_records:  # strip non-JSON internals
        for k in ("_y_true", "_y_pred", "_emb_test", "_test_idx"):
            r.pop(k, None)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": hypothesis_id,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "venues": list(venue_order),
        "n_windows_total": int(panel.x.shape[0]),
        "seed": int(seed),
        # Audit trail only — deliberately NO resumed/trained counters here:
        # a checkpoint-assembled run must produce the IDENTICAL payload as
        # an uninterrupted run (checkpointing is result-neutral).
        "checkpointing": {
            "enabled": ckpt is not None,
            "ckpt_dir": str(ckpt) if ckpt is not None else None,
        },
        "method": {
            "panel": "10 Nodes = 5 Symbole x {Bybit, Binance}, publicTrade "
                     "only, 5-Min-Event-Fenster, 4 Kanaele (Inter-Trade-"
                     "Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction)",
            "normalisation": "Pro-Tag-Quantil-Normalisierung je Kanal/Node "
                             "(Rang -> Uniform) — zerstoert triviale Venue-"
                             "Tells (Tick-Size, Fee-Size-Clustering, "
                             "Aktivitaetslevel); Diagnostik-Test in "
                             "tests/unit/test_c17_venue.py",
            "encoder": "Temporal-CNN (dilatiert) + Masked-Mean-Pool "
                       "(count-invariant) + Projection-Head",
            "training": "InfoNCE (Positive = Fenster desselben Nodes zu "
                        "anderen Zeiten, Negative = voller Batch, "
                        f"Batch >= {BATCH_SIZE_MIN}), Frozen-Linear-Probe "
                        "fuer Venue-Identitaet",
            "folds": f"Leave-One-Symbol-Out, {N_FOLDS} Folds, Test = letzte "
                     f"{TEST_WEEKS} Wochen des ausgelassenen Symbols",
            "null": f"Within-Symbol-Within-Day-Label-Permutation, {n_perm} "
                    "VOLLE Retrainings je Fold (kein Frozen-Model-Shuffling)",
        },
        "compute": {
            "torch_available": bool(torch_available),
            "cuda_used": bool(cuda_used),
            "encoder_verdict_capable": encoder_verdict_capable,
            "batch_size": int(batch_size),
            "batch_size_registered_min": BATCH_SIZE_MIN,
            "min_achieved_steps": min_achieved_steps,
            "steps_technical_min": STEPS_MIN,
            "verdict_bearing": verdict_bearing,
            "blocked_reasons": blocked_reasons,
            "note": COMPUTE_NOTE,
        },
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "fdr_family_size": len(p_values),
        "fdr_p_crit": float(p_crit),
        "n_fdr_significant": sum(1 for r in fold_records if r["fdr_significant"]),
        "gate_thresholds": {
            "balanced_acc_min": BALANCED_ACC_MIN,
            "min_passing_folds": MIN_PASSING_FOLDS,
            "n_folds": N_FOLDS,
            "pooled_acc_min": POOLED_ACC_MIN,
            "n_permutations": N_PERMUTATIONS,
            "redundancy_rho_max": REDUNDANCY_RHO_MAX,
        },
        "folds": fold_records,
        "n_folds_passed": int(n_folds_passed),
        "n_folds_evaluable": int(sum(1 for r in fold_records if r["evaluable"])),
        "folds_criterion_met": folds_ok,
        "pooled_balanced_accuracy": float(pooled_acc),
        "pooled_acc_ok": pooled_ok,
        "embedding_distance": distance,
        "distance_scope": ("full_panel (H-23: every window of each held-out "
                           "symbol, embedded by the fold that excluded it)"
                           if full_panel_distance else
                           "test_windows_only (H-17 registered scope)"),
        "redundancy_test_days_only": redundancy_test_days_only,
        "redundancy_gate": redundancy,
        # Gate-neutral observation flag (the gate-auditor adjudicates):
        "weiter_indication": weiter_indication,
    }


# ---------------------------------------------------------------------------
# Report (Deutsch)
# ---------------------------------------------------------------------------

def _fmt(v: Any, nd: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — folds, null, redundancy gate, compute gate."""
    L: list[str] = []
    L.append("# H-17 · Venue-Fingerprint Mess-Gate (Contrastive-Embedding, "
             "F-VENUE, KAPITALFREI, GPU)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — "
             f"`{payload['hypothesis_registry']}` (Welle 5)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}`")
    m = payload["method"]
    L.append(f"- **Panel:** {m['panel']}")
    L.append(f"- **Normalisierung:** {m['normalisation']}")
    L.append(f"- **Encoder/Training:** {m['encoder']} · {m['training']}")
    L.append(f"- **Folds:** {m['folds']}")
    L.append(f"- **Null:** {m['null']} · Seed: {payload['seed']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} "
             f"({payload['fdr_family_size']} Fold-Tests) · BH-FDR alpha "
             f"{payload['fdr_alpha']} · p_crit {_fmt(payload['fdr_p_crit'])} · "
             f"FDR-signifikant: {payload['n_fdr_significant']}")
    L.append("- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage. "
             "Eine Handelsfolge waere NEUE H-17b, NICHT impliziert.")
    c = payload["compute"]
    L.append(f"- **Compute-Gate:** torch={_fmt(c['torch_available'])} · "
             f"CUDA={_fmt(c['cuda_used'])} · Batch {c['batch_size']} "
             f"(Min {c['batch_size_registered_min']}) · "
             f"erreichte Schritte (Min) {_fmt(c.get('min_achieved_steps'), 0)} "
             f"(techn. Min {c['steps_technical_min']}) · "
             f"**verdikt-tragend: {_fmt(c['verdict_bearing'])}**"
             + (f" · blockiert: {'; '.join(c['blocked_reasons'])}"
                if c["blocked_reasons"] else ""))
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-17. WEITER "
             "verlangt: Held-out-Balanced-Accuracy >= 0,60 in >= 4/5 "
             "Leave-One-Symbol-Out-Folds gegen die 20-Retrainings-"
             "Permutations-Null nach BH-FDR alpha=0,10 ueber F-VENUE UND "
             "Non-Redundanz-Gate |Spearman rho| < 0,6 gegen die c12_frag-"
             "Tages-lambda2/IPR-Serie. DROP: Pooled-Accuracy < 0,55 ODER "
             "< 4/5 Folds ODER |rho| >= 0,6 (REDUNDANT zu H-12, DROP "
             "unabhaengig von der Accuracy). Kein Graubereich.")
    L.append("")
    L.append(f"**WEITER-Indikation:** {_fmt(payload['weiter_indication'])} · "
             f"Folds bestanden: {payload['n_folds_passed']}/{payload['fdr_family_size']} "
             f"({_fmt(payload['folds_criterion_met'])}) · "
             f"Folds auswertbar: {payload['n_folds_evaluable']}/{payload['fdr_family_size']} · "
             f"Pooled-Balanced-Accuracy: {_fmt(payload['pooled_balanced_accuracy'])} "
             f"(>= {payload['gate_thresholds']['pooled_acc_min']}: "
             f"{_fmt(payload['pooled_acc_ok'])})")
    L.append("")
    L.append("## Folds (Gate-Kern)")
    L.append("")
    L.append("| Fold (Symbol out) | Test-Zeitraum | Train/Test-Fenster | "
             "Balanced Acc (>= 0,60) | Null (min..max) | p | FDR-sig | auswertbar | bestanden |")
    L.append("|---|---|---:|---:|---|---:|:---:|:---:|:---:|")
    for r in payload["folds"]:
        nulls = r["null_accuracies"]
        nul = f"{min(nulls):.3f}..{max(nulls):.3f}" if nulls else "n/a"
        L.append(
            f"| {r['held_out_symbol']} | {r['test_start_date']}.."
            f"{r['test_end_date']} | {r['n_train_windows']}/{r['n_test_windows']} "
            f"| {_fmt(r['balanced_accuracy'])} ({_fmt(r['acc_threshold_met'])}) "
            f"| {nul} | {_fmt(r['p_value'])} | {_fmt(r['fdr_significant'])} "
            f"| {_fmt(r['evaluable'])} | {_fmt(r['passed'])} |"
        )
    L.append("")
    L.append("## Non-Redundanz-Gate gegen c12_frag/H-12 (vorregistriert, bindend)")
    L.append("")
    rg = payload["redundancy_gate"]
    L.append(f"- c12-Payload vorhanden: {_fmt(rg['c12_payload_present'])} · "
             f"ueberlappende Tage: {rg['n_overlap_days']} "
             f"(techn. Floor {rg['min_overlap_days_technical']})")
    L.append(f"- Spearman rho vs. lambda2: {_fmt(rg['rho_lambda2'])} · "
             f"vs. IPR(v2): {_fmt(rg['rho_ipr_v2'])} · "
             f"max|rho|: {_fmt(rg['max_abs_rho'])} "
             f"(Schwelle {rg['rho_max_registered']})")
    L.append(f"- auswertbar: {_fmt(rg['evaluable'])} · "
             f"**REDUNDANT (DROP): {_fmt(rg['redundant'])}** · "
             f"bestanden: {_fmt(rg['passed'])}")
    L.append("")
    L.append("## Taegliche Cross-Venue-Embedding-Distance-Serie "
             "(sekundaer, nicht-urteilstragend)")
    L.append("")
    daily = payload["embedding_distance"]["daily"]
    L.append(f"- Tage: {len(daily)}")
    if daily:
        vals = list(daily.values())
        L.append(f"- Median: {_fmt(float(np.median(vals)))} · "
                 f"Min: {_fmt(min(vals))} · Max: {_fmt(max(vals))}")
    L.append("")
    L.append("*Erzeugt von `scripts/c17_venue.py` (Welle 5, read-only "
             "Harvester). capital_free=true. Endgueltiges Gate-Urteil: "
             "gate-auditor gegen H-17.*")
    L.append("")
    return "\n".join(L)


__all__ = [
    "BALANCED_ACC_MIN",
    "CKPT_SCHEMA_VERSION",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_PASSING_FOLDS",
    "N_FOLDS",
    "N_PERMUTATIONS",
    "POOLED_ACC_MIN",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "TEST_DAYS",
    "TEST_WEEKS",
    "TRAINING_KINDS",
    "CheckpointMismatchError",
    "Fold",
    "Panel",
    "build_loso_folds",
    "count_existing_checkpoints",
    "make_run_fingerprint",
    "render_markdown",
    "run",
    "run_fold",
    "stack_nodes",
]
