"""InfoNCE contrastive training + frozen linear probe for H-17 (KAPITALFREI).

Registered method (registry H-17, verbatim): InfoNCE contrastive training
of the temporal encoder, positives = windows of the SAME node at other
times, negatives = the full batch, batch size >= 2048 (the large-batch
regime is PART of the method — small-batch CPU training would measurably
degrade embedding quality and confound a null result, hence the hard
``BATCH_SIZE_MIN`` guard: smaller batches are allowed only with an explicit
dev override and the driver then marks the run NON-verdict-bearing).

Loss: multi-positive InfoNCE (SupCon-style with node identity as the label,
Khosla et al. 2020 "out" formulation) — for anchor i with positive set
P(i) = {j != i : node_j = node_i}:

    L_i = -1/|P(i)| * sum_{p in P(i)} log( exp(s_ip/tau)
                                           / sum_{a != i} exp(s_ia/tau) )

with s = cosine similarity of the projection-head outputs, tau = 0.07
(pre-fixed). With batch >= 2048 uniformly sampled over ~10 nodes every
anchor has ~200 in-batch positives, matching the registered "Positive =
Fenster desselben Nodes zu anderen Zeiten, Negative = voller Batch".

``infonce_loss_np`` is the numpy reference implementation of the SAME
formula, unit-tested in the sandbox (no torch there).

FROZEN LINEAR PROBE: numpy logistic regression (class-balanced, L2,
deterministic full-batch gradient descent) on the frozen pre-projection
embeddings. Pure numpy so the identical probe code runs in the sandbox
(fallback embeddings) and on the GPU box (real embeddings).

KAPITALFREI: pure representation learning / classification statistics.
"""
from __future__ import annotations

import sys
import time
from typing import Any

import numpy as np

from .encoder import TORCH_AVAILABLE, VenueEncoder

if TORCH_AVAILABLE:  # pragma: no cover - sandbox has no torch
    import torch
    import torch.nn.functional as F

#: Registered minimum batch size (registry H-17: Batch-Groesse >= 2048).
BATCH_SIZE_MIN = 2048

#: Technical floor on optimizer steps (NOT a registered numeric threshold,
#: analogous to BATCH_SIZE_MIN's role for batch size): ``steps < 1`` performs
#: ZERO optimizer iterations -- a randomly-initialised encoder, not a trained
#: one. Audit finding: argparse has no lower bound on ``--steps``, so
#: ``--steps 0`` on a real CUDA box used to report ``trained: True`` with a
#: compliant batch size while training nothing at all. Guarded the same way
#: as ``allow_small_batch`` (explicit dev/smoke override only).
STEPS_MIN = 1

#: Pre-fixed InfoNCE temperature.
TEMPERATURE = 0.07

#: Default optimizer steps per (re)training. The SAME step count is used for
#: the real training AND every permutation retraining (a shorter null
#: training would depress null accuracy and be anti-conservative).
DEFAULT_STEPS = 10_000

DEFAULT_LR = 1e-3


# ---------------------------------------------------------------------------
# InfoNCE — numpy reference (sandbox-testable) + torch trainer
# ---------------------------------------------------------------------------

def infonce_loss_np(
    proj: np.ndarray, node_ids: np.ndarray, temperature: float = TEMPERATURE
) -> float:
    """Numpy reference of the multi-positive InfoNCE loss (see module doc).

    ``proj`` (B, D) projection outputs, ``node_ids`` (B,) node identity per
    window. Anchors without any in-batch positive are skipped (undefined).
    """
    z = np.asarray(proj, dtype=np.float64)
    ids = np.asarray(node_ids)
    z = z / np.maximum(np.linalg.norm(z, axis=1, keepdims=True), 1e-12)
    sim = (z @ z.T) / float(temperature)
    b = z.shape[0]
    eye = np.eye(b, dtype=bool)
    # log-softmax over all a != i
    sim_masked = np.where(eye, -np.inf, sim)
    mx = np.max(sim_masked, axis=1, keepdims=True)
    logsumexp = mx[:, 0] + np.log(np.sum(np.exp(sim_masked - mx), axis=1))
    pos = (ids[:, None] == ids[None, :]) & ~eye
    losses: list[float] = []
    for i in range(b):
        p = np.nonzero(pos[i])[0]
        if p.size == 0:
            continue
        losses.append(float(np.mean(logsumexp[i] - sim[i, p])))
    if not losses:
        raise ValueError("no anchor with an in-batch positive")
    return float(np.mean(losses))


def train_contrastive_encoder(
    encoder: VenueEncoder,
    x: np.ndarray,
    mask: np.ndarray,
    node_ids: np.ndarray,
    *,
    batch_size: int = BATCH_SIZE_MIN,
    steps: int = DEFAULT_STEPS,
    lr: float = DEFAULT_LR,
    temperature: float = TEMPERATURE,
    seed: int = 42,
    allow_small_batch: bool = False,
    allow_zero_steps: bool = False,
    log_every: int = 200,
) -> dict[str, Any]:
    """Full InfoNCE training of a fresh encoder (torch; GPU-intended).

    Registered semantics: called ONCE for the real fold training and ONCE
    PER permutation replicate (full retraining — never reuse a trained
    model for the null). ``batch_size < BATCH_SIZE_MIN`` raises unless
    ``allow_small_batch`` (dev/smoke only; such runs are marked
    non-verdict-bearing by the driver). ``steps < STEPS_MIN`` (i.e. zero
    optimizer iterations — a randomly-initialised, untrained encoder) raises
    unless ``allow_zero_steps`` (dev/smoke only; same non-verdict-bearing
    contract, enforced independently by ``driver.run()``'s compute gate on
    the ACHIEVED ``fit_info["steps"]``, mirroring the batch-size guard).
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("torch nicht verfuegbar — Contrastive-Training unmoeglich")
    if batch_size < BATCH_SIZE_MIN and not allow_small_batch:
        raise ValueError(
            f"batch_size {batch_size} < registered minimum {BATCH_SIZE_MIN} "
            f"(registry H-17); use allow_small_batch only for non-verdict smokes"
        )
    if steps < STEPS_MIN and not allow_zero_steps:
        raise ValueError(
            f"steps {steps} < technical floor {STEPS_MIN} — zero optimizer "
            f"iterations is not training (audit finding: --steps 0 must never "
            f"masquerade as 'trained: True'); use allow_zero_steps only for "
            f"non-verdict smokes"
        )
    n = x.shape[0]
    ids_np = np.asarray(node_ids)
    _, ids_dense = np.unique(ids_np, return_inverse=True)
    device = encoder.device
    model = encoder.model
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, steps))
    gen = np.random.default_rng(seed)
    ids_t_all = torch.from_numpy(ids_dense.astype(np.int64))
    t0 = time.time()
    losses: list[float] = []
    eff_batch = min(batch_size, n)
    for step in range(steps):
        idx = gen.choice(n, size=eff_batch, replace=False)
        xb = torch.from_numpy(np.asarray(x[idx], dtype=np.float32)).to(device)
        mb = torch.from_numpy(np.asarray(mask[idx], dtype=bool)).to(device)
        ib = ids_t_all[idx].to(device)
        _, proj = model(xb, mb)
        z = F.normalize(proj, dim=1)
        sim = (z @ z.T) / temperature
        b = sim.shape[0]
        eye = torch.eye(b, dtype=torch.bool, device=device)
        sim_masked = sim.masked_fill(eye, float("-inf"))
        log_prob = sim - torch.logsumexp(sim_masked, dim=1, keepdim=True)
        pos = (ib[:, None] == ib[None, :]) & ~eye
        pos_cnt = pos.sum(dim=1)
        has_pos = pos_cnt > 0
        loss = -(log_prob.masked_fill(~pos, 0.0).sum(dim=1)[has_pos]
                 / pos_cnt[has_pos].clamp_min(1)).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        losses.append(float(loss.item()))
        if log_every and (step + 1) % log_every == 0:
            print(f"[c17_venue] step {step + 1}/{steps} "
                  f"loss={np.mean(losses[-log_every:]):.4f}",
                  file=sys.stderr, flush=True)
    model.eval()
    return {
        "trained": bool(steps > 0),
        "steps": int(steps),
        "steps_registered_min": STEPS_MIN,
        "zero_steps_override": bool(steps < STEPS_MIN),
        "batch_size": int(eff_batch),
        "batch_size_registered_min": BATCH_SIZE_MIN,
        "small_batch_override": bool(eff_batch < BATCH_SIZE_MIN),
        "temperature": float(temperature),
        "lr": float(lr),
        "final_loss": float(np.mean(losses[-min(100, len(losses)):])) if losses else None,
        "wall_seconds": float(time.time() - t0),
        "device": device,
    }


# Attach a fit() with the trainer so encoder factories share one interface
# with NumpyFallbackEncoder (driver calls encoder.fit(...)).
def _venue_encoder_fit(self: VenueEncoder, x, mask, node_ids, **kw) -> dict[str, Any]:
    return train_contrastive_encoder(self, x, mask, node_ids, **kw)


if TORCH_AVAILABLE:  # pragma: no cover - sandbox has no torch
    VenueEncoder.fit = _venue_encoder_fit  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Frozen linear probe (numpy logistic regression, deterministic)
# ---------------------------------------------------------------------------

def train_linear_probe(
    emb: np.ndarray,
    y: np.ndarray,
    *,
    l2: float = 1e-3,
    iters: int = 400,
    lr: float = 0.5,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    """Class-balanced logistic regression on FROZEN embeddings (binary y).

    Features are standardised internally (mu/sd stored in the model dict);
    class-balanced sample weights keep the probe honest under venue-count
    imbalance (the gate metric is BALANCED accuracy). Deterministic
    full-batch gradient descent — no torch dependency, identical behaviour
    in sandbox and on the GPU box.
    """
    X = np.asarray(emb, dtype=np.float64)
    y = np.asarray(y, dtype=np.int64)
    classes = np.unique(y)
    if classes.size != 2:
        raise ValueError(f"binary probe needs 2 classes, got {classes.tolist()}")
    t = (y == classes[1]).astype(np.float64)         # 0/1 target
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd <= 1e-12, 1.0, sd)
    Xs = (X - mu) / sd
    n = Xs.shape[0]
    n1 = float(t.sum())
    n0 = float(n - n1)
    w_sample = np.where(t == 1.0, n / (2.0 * max(n1, 1.0)), n / (2.0 * max(n0, 1.0)))
    w = np.zeros(Xs.shape[1], dtype=np.float64)
    b = 0.0
    for _ in range(iters):
        z = Xs @ w + b
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))
        g = (p - t) * w_sample
        gw = Xs.T @ g / n + l2 * w
        gb = float(np.mean(g))
        w -= lr * gw
        b -= lr * gb
    return {"w": w, "b": np.float64(b), "mu": mu, "sd": sd,
            "classes": classes.astype(np.int64)}


def probe_predict(emb: np.ndarray, model: dict[str, np.ndarray]) -> np.ndarray:
    """Predicted class labels (values from model['classes'])."""
    X = (np.asarray(emb, dtype=np.float64) - model["mu"]) / model["sd"]
    z = X @ model["w"] + float(model["b"])
    cls = model["classes"]
    return np.where(z > 0.0, cls[1], cls[0])


__all__ = [
    "BATCH_SIZE_MIN",
    "DEFAULT_LR",
    "DEFAULT_STEPS",
    "STEPS_MIN",
    "TEMPERATURE",
    "infonce_loss_np",
    "probe_predict",
    "train_contrastive_encoder",
    "train_linear_probe",
]
