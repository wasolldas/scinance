"""Training plan, circular-shift surrogates and checkpoint/resume for H-14.

Per pre-registered window the plan is EXACTLY the registered workload
(registry H-14: 1 + 12 + ~100 trainings x 2 windows ~= 226):

  * ``full``        — 1 training on the untouched 12-node panel,
  * ``ablate/<j>``  — 12 trainings, node j replaced by a circular-shift
                      surrogate (retrain ablation, NOT frozen shuffle),
  * ``null/<k>``    — ~100 trainings with COMPLETELY surrogate cross-node
                      inputs: every node independently circularly shifted.

Targets are always computed from the (possibly shifted) series itself, so a
shifted node keeps its own feature->target alignment — only CROSS-node
information is destroyed (see ``panel.circular_shift_rows``). Shifts are
drawn deterministically per task from a seeded RNG, bounded away from 0 by
``MIN_SHIFT_SECONDS`` so alignment is genuinely destroyed.

Checkpoint/resume (registry self-kill clause: the runner MUST persist
intermediate state — a power failure after day 2 of a ~2-3 GPU-day run must
not restart from zero): every completed training writes ONE JSON checkpoint
``<ckpt_dir>/<window>/<task_id>.json`` (atomic tmp+rename). On restart,
tasks with an existing checkpoint are loaded and skipped. The checkpoint
directory is therefore STABLE across runner restarts (not timestamped).

The training function is injectable (``train_fn``) so the sandbox tests can
verify the full plan/statistics pipeline with a deterministic fake model —
the real torch path lives in ``make_torch_train_fn`` and is compute-gated.

KAPITALFREI: no friction, bps, PnL, Sharpe logic anywhere.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .encoder import DEFAULT_MODEL_PARAMS, DEFAULT_TRAIN_PARAMS, PanelLagNet
from .panel import (
    PanelWindow,
    circular_shift_rows,
    train_oos_split,
    valid_sample_indices,
)

#: Registered null size (registry H-14: ~100 Retrainings je Fenster).
DEFAULT_N_NULL = 100

#: Minimum circular shift (seconds) — far beyond lookback+horizon so the
#: surrogate genuinely destroys cross-node alignment (builder-fixed).
MIN_SHIFT_SECONDS = 3600

#: A training result must carry per-node OOS log-losses under this key.
RESULT_LOSS_KEY = "per_node_log_loss"

TrainFn = Callable[[np.ndarray, dict[str, Any]], dict[str, Any]]


@dataclass(slots=True)
class TrainTask:
    """One training of the ~226-training plan."""

    task_id: str          # e.g. "full", "ablate/03", "null/017"
    kind: str             # "full" | "ablate" | "null"
    window_label: str
    ablate_node: int | None = None   # node index for kind == "ablate"
    null_index: int | None = None    # k for kind == "null"
    seed: int = 0                    # deterministic per-task seed
    shift_nodes: tuple[int, ...] = field(default_factory=tuple)


def build_task_plan(
    window_label: str,
    n_nodes: int,
    *,
    n_null: int = DEFAULT_N_NULL,
    seed: int = 42,
) -> list[TrainTask]:
    """Deterministic task list: 1 full + n_nodes ablations + n_null nulls."""
    tasks: list[TrainTask] = [
        TrainTask(task_id="full", kind="full", window_label=window_label,
                  seed=_task_seed(seed, window_label, "full", 0))
    ]
    for j in range(n_nodes):
        tasks.append(TrainTask(
            task_id=f"ablate/{j:02d}", kind="ablate", window_label=window_label,
            ablate_node=j, shift_nodes=(j,),
            seed=_task_seed(seed, window_label, "ablate", j),
        ))
    for k in range(n_null):
        tasks.append(TrainTask(
            task_id=f"null/{k:03d}", kind="null", window_label=window_label,
            null_index=k, shift_nodes=tuple(range(n_nodes)),
            seed=_task_seed(seed, window_label, "null", k),
        ))
    return tasks


def _task_seed(seed: int, window_label: str, kind: str, index: int) -> int:
    """Deterministic, collision-resistant per-task seed."""
    h = 2166136261
    for ch in f"{seed}|{window_label}|{kind}|{index}":
        h = (h ^ ord(ch)) * 16777619 % (2**32)
    return int(h)


def draw_shifts(task: TrainTask, t_total: int) -> dict[int, int]:
    """Deterministic circular shifts for the task's surrogate nodes.

    Uniform in ``[MIN_SHIFT_SECONDS, t_total - MIN_SHIFT_SECONDS]`` (each
    node independent), so alignment is destroyed in both directions. Raises
    if the window is too short to shift meaningfully.
    """
    if not task.shift_nodes:
        return {}
    lo, hi = MIN_SHIFT_SECONDS, t_total - MIN_SHIFT_SECONDS
    if hi <= lo:
        # tiny synthetic/test windows: fall back to the largest safe band
        lo = max(1, t_total // 4)
        hi = max(lo + 1, t_total - lo)
    rng = np.random.default_rng(task.seed)
    return {j: int(rng.integers(lo, hi)) for j in task.shift_nodes}


# ---------------------------------------------------------------------------
# Checkpointing (atomic write, resume by skip)
# ---------------------------------------------------------------------------

def _ckpt_path(ckpt_dir: Path, window_label: str, task_id: str) -> Path:
    safe = task_id.replace("/", "_")
    return ckpt_dir / window_label / f"{safe}.json"


def _write_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")

    def clean(v: Any) -> Any:
        if isinstance(v, float) and not math.isfinite(v):
            return None
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        return v

    tmp.write_text(json.dumps(clean(payload), indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if RESULT_LOSS_KEY not in payload:
        return None
    return payload


# ---------------------------------------------------------------------------
# Plan execution
# ---------------------------------------------------------------------------

def run_window_plan(
    window: PanelWindow,
    tasks: list[TrainTask],
    ckpt_dir: Path | str,
    train_fn: TrainFn,
    *,
    lookback: int = int(DEFAULT_MODEL_PARAMS["lookback"]),
    horizon: int = int(DEFAULT_TRAIN_PARAMS["horizon"]),
    sample_stride: int = int(DEFAULT_TRAIN_PARAMS["sample_stride"]),
    train_frac: float = float(DEFAULT_TRAIN_PARAMS["train_frac"]),
    log: bool = True,
) -> dict[str, dict[str, Any]]:
    """Execute (or resume) one window's training plan.

    For each task: skip if a valid checkpoint exists; else apply the task's
    circular shifts, build the chronological train/OOS anchor sets (embargo =
    lookback + horizon between the segments — no leakage) and call
    ``train_fn(shifted_returns, meta)``. ``meta`` carries the split anchors,
    horizon and task identity; the returned dict MUST contain
    ``per_node_log_loss`` (OOS, natural log) and is checkpointed verbatim
    (plus bookkeeping). Returns ``{task_id: result}``.
    """
    ckpt = Path(ckpt_dir)
    t_total = window.n_seconds
    (tr_lo, tr_hi), (oo_lo, oo_hi) = train_oos_split(
        (0, t_total - 1), train_frac=train_frac, embargo=lookback + horizon
    )
    results: dict[str, dict[str, Any]] = {}
    n_done_before = 0
    for task in tasks:
        path = _ckpt_path(ckpt, window.label, task.task_id)
        cached = _load_checkpoint(path)
        if cached is not None:
            results[task.task_id] = cached
            n_done_before += 1
            continue
        t0 = time.time()
        shifts = draw_shifts(task, t_total)
        shifted = circular_shift_rows(window.returns, shifts) if shifts else window.returns
        train_anchors = valid_sample_indices(
            shifted, lookback, horizon, sample_stride=sample_stride,
            t_start=tr_lo, t_end=tr_hi,
        )
        oos_anchors = valid_sample_indices(
            shifted, lookback, horizon, sample_stride=sample_stride,
            t_start=oo_lo, t_end=oo_hi,
        )
        meta = {
            "task_id": task.task_id,
            "kind": task.kind,
            "window_label": window.label,
            "ablate_node": task.ablate_node,
            "null_index": task.null_index,
            "seed": task.seed,
            "shifts": {str(k): int(v) for k, v in shifts.items()},
            "lookback": lookback,
            "horizon": horizon,
            "sample_stride": sample_stride,
            "train_anchors": train_anchors,
            "oos_anchors": oos_anchors,
        }
        result = train_fn(shifted, meta)
        if RESULT_LOSS_KEY not in result:
            raise ValueError(
                f"train_fn result for {task.task_id} lacks '{RESULT_LOSS_KEY}'"
            )
        result = {
            **result,
            "task_id": task.task_id,
            "kind": task.kind,
            "window_label": window.label,
            "ablate_node": task.ablate_node,
            "null_index": task.null_index,
            "seed": task.seed,
            "shifts": meta["shifts"],
            "n_train_anchors": int(train_anchors.size),
            "n_oos_anchors": int(oos_anchors.size),
            "wall_seconds": round(time.time() - t0, 3),
        }
        _write_checkpoint(path, result)
        results[task.task_id] = result
        if log:
            print(
                f"[c14_panellag] {window.label} {task.task_id}: done "
                f"({result['wall_seconds']}s, train={train_anchors.size} "
                f"oos={oos_anchors.size} anchors)",
                file=sys.stderr, flush=True,
            )
    if log:
        print(
            f"[c14_panellag] {window.label}: {n_done_before}/{len(tasks)} tasks "
            f"resumed from checkpoints, {len(tasks) - n_done_before} trained now",
            file=sys.stderr, flush=True,
        )
    return results


# ---------------------------------------------------------------------------
# Real torch training function (compute-gated)
# ---------------------------------------------------------------------------

def make_torch_train_fn(
    n_nodes: int,
    *,
    device: str = "auto",
    model_params: dict[str, Any] | None = None,
    train_params: dict[str, Any] | None = None,
) -> TrainFn:
    """Real training function: fresh ``PanelLagNet`` per task, OOS eval.

    Raises ``encoder.ComputeGateError`` on call when torch is missing —
    a full run without the required compute never yields numbers.
    """
    mp = {**DEFAULT_MODEL_PARAMS, **(model_params or {})}
    tp = {**DEFAULT_TRAIN_PARAMS, **(train_params or {})}

    def _train(returns: np.ndarray, meta: dict[str, Any]) -> dict[str, Any]:
        net = PanelLagNet(n_nodes, device=device, seed=int(meta["seed"]), **mp)
        fit_info = net.fit_panel(
            returns, meta["train_anchors"],
            horizon=int(meta["horizon"]),
            epochs=int(tp["epochs"]),
            batch_size=int(tp["batch_size"]),
            lr=float(tp["lr"]),
        )
        ev = net.eval_log_loss_panel(
            returns, meta["oos_anchors"], horizon=int(meta["horizon"])
        )
        return {
            RESULT_LOSS_KEY: ev[RESULT_LOSS_KEY],
            "per_node_n_masked": ev["per_node_n_masked"],
            "n_oos_samples": ev["n_oos_samples"],
            "train_log_loss": fit_info["train_log_loss"],
            "epochs": fit_info["epochs"],
            "device": fit_info["device"],
            "n_parameters": fit_info["n_parameters"],
        }

    return _train


# ---------------------------------------------------------------------------
# Dummy training function (CLI --allow-cpu-fallback / sandbox pipeline tests)
# ---------------------------------------------------------------------------

def make_dummy_train_fn(n_nodes: int, *, base_loss: float = 0.693) -> TrainFn:
    """Deterministic FAKE loss function — NOT a model.

    Exercises the plan/checkpoint/edge-statistics/BH-FDR pipeline end to end
    without torch. Per-node loss is a deterministic function of the task's
    seed and the realised OOS return spread (NOT a fit, NOT a prediction).
    Used by ``scripts/c14_panellag.py --allow-cpu-fallback`` (explicit test
    mode) and directly by unit tests that need to probe the STATISTICS
    pipeline in isolation from real training. The resulting run is NEVER
    verdict-bearing (``driver.make_compute_info`` marks
    ``synthetic_train_fn_used=True`` -> ``gate_valid=False``).
    """

    def _train(returns: np.ndarray, meta: dict[str, Any]) -> dict[str, Any]:
        rng = np.random.default_rng(int(meta["seed"]))
        oos = np.asarray(meta["oos_anchors"], dtype=np.int64)
        losses: list[float] = []
        for i in range(n_nodes):
            if oos.size:
                vals = returns[i, oos]
                spread = float(np.nanstd(vals)) if np.isfinite(vals).any() else 0.0
            else:
                spread = 0.0
            noise = float(rng.normal(0.0, 1e-4))
            losses.append(base_loss + 10.0 * spread + noise)
        return {
            RESULT_LOSS_KEY: losses,
            "per_node_n_masked": [float(oos.size)] * n_nodes,
            "n_oos_samples": int(oos.size),
            "train_log_loss": float(np.mean(losses)),
            "epochs": 0,
            "device": "cpu-dummy",
            "n_parameters": 0,
        }

    return _train


__all__ = [
    "DEFAULT_N_NULL",
    "MIN_SHIFT_SECONDS",
    "RESULT_LOSS_KEY",
    "TrainTask",
    "build_task_plan",
    "draw_shifts",
    "make_dummy_train_fn",
    "make_torch_train_fn",
    "run_window_plan",
]
