"""ResNet-18 forward-vs-reversed scalogram classifier for H-16 (torch-optional).

Architecture (registry H-16: "ResNet-18 oder kompaktes ConvNeXt" — fixed
here to ResNet-18, He et al. 2016, single-channel input, 1 logit): standard
BasicBlock stack [2, 2, 2, 2] with channels 64/128/256/512, 7x7 stem,
adaptive average pool, linear head. Input images are (B, 1, 64, 512)
standardised log-power scalograms computed ON DEVICE per batch from the raw
1 s windows (storing ~135k precomputed scalograms per symbol would need
~18 GB; the raw windows need ~0.3 GB).

Label construction (binding, registry H-16): each raw window yields BOTH
classes — label 1 = FORWARD (window as recorded), label 0 = TIME-REVERSED
(the RAW window flipped along time BEFORE the CWT, see
``scalogram.scalogram_pair``). The flip happens on the raw series inside
:func:`_batch_images`; the finished image is never flipped.

torch is OPTIONAL (m18_patchtst convention): the module imports without it
and every entry point degrades honestly by raising :class:`ComputeError`
with a clear message — no silent numpy "training" stub, because a fake
training run must never look like a real one (compute-gating duty).
:func:`gpu_status` reports the truth for ``--check-gpu-only``.

KAPITALFREI: pure classification power measurement, no cost/return code.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .scalogram import WINDOW_S, cwt_logpower_batch_torch, torch_filter_bank
from .stats import mann_whitney_auc, paired_sign_test_p

_LOG = logging.getLogger(__name__)

try:  # torch optional (sandbox has none; the RTX machine does)
    import torch
    import torch.nn as nn

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only without torch installed
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

#: Training defaults (fixed before the run; documented in README_H16).
EPOCHS_DEFAULT = 6
BATCH_SIZE_DEFAULT = 64
LR_DEFAULT = 1e-3
WEIGHT_DECAY_DEFAULT = 1e-4


class ComputeError(RuntimeError):
    """Raised when the compute gate (torch / CUDA) is not satisfied."""


def gpu_status() -> dict[str, Any]:
    """Honest compute-gate report for ``--check-gpu-only``.

    ``verdict_capable`` is True ONLY with torch AND a real CUDA device —
    the registered surrogate null (~20 full retrainings per symbol) is not
    honestly executable otherwise, and a CPU run may NEVER carry a verdict.
    """
    if not _TORCH_AVAILABLE:
        return {
            "torch_available": False,
            "torch_version": None,
            "cuda_available": False,
            "device_count": 0,
            "device_name": None,
            "verdict_capable": False,
        }
    cuda = bool(torch.cuda.is_available())
    return {
        "torch_available": True,
        "torch_version": str(torch.__version__),
        "cuda_available": cuda,
        "device_count": int(torch.cuda.device_count()) if cuda else 0,
        "device_name": torch.cuda.get_device_name(0) if cuda else None,
        "verdict_capable": cuda,
    }


def require_torch(context: str) -> None:
    """Raise a clear ComputeError when torch is missing (honest degradation)."""
    if not _TORCH_AVAILABLE:
        raise ComputeError(
            f"{context}: torch is not installed in this environment — the "
            "H-16 CNN pipeline cannot run here. Only the numpy-testable "
            "pipeline pieces (CWT, IAAFT, stats) are available. Run on the "
            "local RTX machine (see handoff_local/run_h16.*)."
        )


# ----------------------------------------------------------------------------
# ResNet-18 (defined only when torch is importable)
# ----------------------------------------------------------------------------

if _TORCH_AVAILABLE:

    class _BasicBlock(nn.Module):
        expansion = 1

        def __init__(self, in_ch: int, out_ch: int, stride: int = 1) -> None:
            super().__init__()
            self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False)
            self.bn1 = nn.BatchNorm2d(out_ch)
            self.conv2 = nn.Conv2d(out_ch, out_ch, 3, stride=1, padding=1, bias=False)
            self.bn2 = nn.BatchNorm2d(out_ch)
            self.relu = nn.ReLU(inplace=True)
            self.down: nn.Module | None = None
            if stride != 1 or in_ch != out_ch:
                self.down = nn.Sequential(
                    nn.Conv2d(in_ch, out_ch, 1, stride=stride, bias=False),
                    nn.BatchNorm2d(out_ch),
                )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            identity = x if self.down is None else self.down(x)
            out = self.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            return self.relu(out + identity)

    class ArrowResNet18(nn.Module):
        """ResNet-18, single-channel scalogram input, single logit output."""

        def __init__(self) -> None:
            super().__init__()
            self.stem = nn.Sequential(
                nn.Conv2d(1, 64, 7, stride=2, padding=3, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(3, stride=2, padding=1),
            )
            self.layer1 = self._make_layer(64, 64, 2, stride=1)
            self.layer2 = self._make_layer(64, 128, 2, stride=2)
            self.layer3 = self._make_layer(128, 256, 2, stride=2)
            self.layer4 = self._make_layer(256, 512, 2, stride=2)
            self.pool = nn.AdaptiveAvgPool2d(1)
            self.head = nn.Linear(512, 1)

        @staticmethod
        def _make_layer(in_ch: int, out_ch: int, blocks: int, stride: int) -> "nn.Sequential":
            layers: list[nn.Module] = [_BasicBlock(in_ch, out_ch, stride)]
            for _ in range(blocks - 1):
                layers.append(_BasicBlock(out_ch, out_ch, 1))
            return nn.Sequential(*layers)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            x = self.stem(x)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            x = self.pool(x).flatten(1)
            return self.head(x).squeeze(-1)


# ----------------------------------------------------------------------------
# Training / evaluation
# ----------------------------------------------------------------------------


def _batch_images(
    windows: "torch.Tensor",
    labels: "torch.Tensor",
    bank: "torch.Tensor",
) -> "torch.Tensor":
    """Scalogram images for a raw-window batch; label 0 => flip RAW series.

    THE reversal point of the torch pipeline: ``torch.flip`` acts on the raw
    1 s windows BEFORE ``cwt_logpower_batch_torch`` (registry H-16: reversal
    on the raw series before the CWT, never on the finished image).
    """
    x = windows.clone()
    rev = labels == 0
    if bool(rev.any()):
        x[rev] = torch.flip(x[rev], dims=[-1])
    return cwt_logpower_batch_torch(x, bank).unsqueeze(1)  # (B, 1, S, T)


def train_forward_reverse_classifier(
    train_windows: np.ndarray,
    test_windows: np.ndarray,
    *,
    seed: int,
    device: str,
    epochs: int = EPOCHS_DEFAULT,
    batch_size: int = BATCH_SIZE_DEFAULT,
    lr: float = LR_DEFAULT,
    weight_decay: float = WEIGHT_DECAY_DEFAULT,
) -> dict[str, Any]:
    """One full C2ST training: fit on train days, score held-out day windows.

    Each raw window (shape ``(WINDOW_S,)``) contributes one FORWARD (label 1)
    and one TIME-REVERSED (label 0) sample — classes exactly balanced by
    construction. Returns the held-out AUC (gate statistic), the exact
    paired-sign-test p-value inputs, and training diagnostics.
    """
    require_torch("train_forward_reverse_classifier")
    if train_windows.ndim != 2 or train_windows.shape[1] != WINDOW_S:
        raise ValueError(f"train_windows must be (N, {WINDOW_S}), got {train_windows.shape}")
    if test_windows.ndim != 2 or test_windows.shape[1] != WINDOW_S:
        raise ValueError(f"test_windows must be (N, {WINDOW_S}), got {test_windows.shape}")
    if train_windows.shape[0] == 0 or test_windows.shape[0] == 0:
        raise ValueError("empty train or test window set")

    torch.manual_seed(seed)
    if device.startswith("cuda"):
        torch.cuda.manual_seed_all(seed)

    dev = torch.device(device)
    bank = torch_filter_bank(WINDOW_S, device=device)
    model = ArrowResNet18().to(dev)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=max(1, epochs))
    loss_fn = nn.BCEWithLogitsLoss()

    xtr = torch.as_tensor(np.ascontiguousarray(train_windows, dtype=np.float32))
    n_tr = xtr.shape[0]
    # duplicated index + label vectors: window i appears as (i, 1) and (i, 0)
    idx_all = torch.arange(n_tr).repeat(2)
    lab_all = torch.cat([torch.ones(n_tr), torch.zeros(n_tr)])

    gen = torch.Generator().manual_seed(seed)
    history: list[float] = []
    model.train()
    for ep in range(epochs):
        perm = torch.randperm(idx_all.shape[0], generator=gen)
        ep_losses: list[float] = []
        for k in range(0, perm.shape[0], batch_size):
            sel = perm[k:k + batch_size]
            wb = xtr[idx_all[sel]].to(dev, non_blocking=True)
            yb = lab_all[sel].to(dev, non_blocking=True)
            imgs = _batch_images(wb, yb, bank)
            optim.zero_grad()
            logits = model(imgs)
            loss = loss_fn(logits, yb)
            loss.backward()
            optim.step()
            ep_losses.append(float(loss.item()))
        sched.step()
        ep_loss = float(np.mean(ep_losses)) if ep_losses else float("nan")
        history.append(ep_loss)
        _LOG.info("c16 ep=%d/%d train_bce=%.5f", ep + 1, epochs, ep_loss)

    # Held-out scoring: paired forward/reversed scores per test window.
    model.eval()
    xte = torch.as_tensor(np.ascontiguousarray(test_windows, dtype=np.float32))
    n_te = xte.shape[0]
    fwd_scores = np.empty(n_te, dtype=np.float64)
    rev_scores = np.empty(n_te, dtype=np.float64)
    with torch.no_grad():
        for k in range(0, n_te, batch_size):
            wb = xte[k:k + batch_size].to(dev, non_blocking=True)
            ones = torch.ones(wb.shape[0])
            zeros = torch.zeros(wb.shape[0])
            fwd_scores[k:k + wb.shape[0]] = (
                model(_batch_images(wb, ones, bank)).float().cpu().numpy()
            )
            rev_scores[k:k + wb.shape[0]] = (
                model(_batch_images(wb, zeros, bank)).float().cpu().numpy()
            )

    auc = mann_whitney_auc(fwd_scores, rev_scores)
    p_value, sign_counts = paired_sign_test_p(fwd_scores, rev_scores)
    return {
        "auc": float(auc),
        "p_value_sign_test": float(p_value),
        "sign_counts": sign_counts,
        "n_train_windows": int(n_tr),
        "n_test_windows": int(n_te),
        "epochs": int(epochs),
        "batch_size": int(batch_size),
        "lr": float(lr),
        "seed": int(seed),
        "train_bce_history": history,
        "device": str(device),
    }


__all__ = [
    "BATCH_SIZE_DEFAULT",
    "ComputeError",
    "EPOCHS_DEFAULT",
    "LR_DEFAULT",
    "gpu_status",
    "require_torch",
    "train_forward_reverse_classifier",
]
