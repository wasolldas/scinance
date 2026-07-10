"""Temporal-CNN encoder for the H-17 venue-fingerprint gate (torch-optional).

Verdict-bearing path (registry H-17): a temporal CNN encoder over the four
quantile-normalised event channels (B, 4, SEQ_LEN) with a MASKED MEAN pool
(deliberately count-invariant — the pad fraction of a 5-minute window must
not act as an activity side-channel, see features.py) and a projection head
for InfoNCE training (contrastive.py). The linear probe reads the
PRE-projection embedding (standard SimCLR/SupCon practice).

PyTorch is optional (m18_patchtst pattern): without torch the module stays
importable and ``TORCH_AVAILABLE``/``cuda_available()`` report honestly.
``NumpyFallbackEncoder`` is a deterministic, UNTRAINED summary-statistic
featurizer used ONLY to exercise the fold/null/gate statistics pipeline in
the sandbox — it is flagged ``verdict_bearing = False`` and the driver
propagates that flag into the payload: a run without a real CUDA device is
NEVER verdict-bearing (registry H-17 compute requirement: the >= 2048 batch
regime is part of the method).

KAPITALFREI: pure representation learning. No friction, bps, PnL, Sharpe.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .features import N_CHANNELS

_LOG = logging.getLogger(__name__)

try:  # PyTorch optional (m18_patchtst pattern)
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - sandbox has no torch
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    TORCH_AVAILABLE = False

#: Pre-fixed architecture constants (registry H-17: Temporal-CNN/Transformer).
EMBED_DIM = 128
PROJ_DIM = 64


def cuda_available() -> bool:
    """Honest CUDA report: True only with torch AND a visible CUDA device."""
    return bool(TORCH_AVAILABLE and torch.cuda.is_available())


def gpu_report() -> dict[str, Any]:
    """Honest GPU/compute capability report (CLI ``--check-gpu-only``)."""
    rep: dict[str, Any] = {
        "torch_available": bool(TORCH_AVAILABLE),
        "torch_version": (str(torch.__version__) if TORCH_AVAILABLE else None),
        "cuda_available": False,
        "device_count": 0,
        "device_name": None,
        "verdict_capable": False,
        "note": (
            "Ein voller H-17-Lauf ist NUR mit echtem CUDA-Device "
            "verdikt-faehig (Batch >= 2048 ist Teil der registrierten "
            "Methode); ohne CUDA sind Laeufe reine Pipeline-Smokes."
        ),
    }
    if TORCH_AVAILABLE and torch.cuda.is_available():
        rep["cuda_available"] = True
        rep["device_count"] = int(torch.cuda.device_count())
        try:
            rep["device_name"] = str(torch.cuda.get_device_name(0))
        except Exception:  # pragma: no cover
            rep["device_name"] = "unknown"
        rep["verdict_capable"] = True
    return rep


# ---------------------------------------------------------------------------
# Torch encoder (defined only when torch is available)
# ---------------------------------------------------------------------------

if TORCH_AVAILABLE:

    class TemporalCNN(nn.Module):
        """Dilated temporal CNN + masked mean pool + projection head.

        forward(x (B, 4, L), mask (B, L)) -> (embedding (B, EMBED_DIM),
        projection (B, PROJ_DIM)). The projection is used by InfoNCE, the
        embedding by the frozen linear probe.
        """

        def __init__(
            self,
            n_channels: int = N_CHANNELS,
            embed_dim: int = EMBED_DIM,
            proj_dim: int = PROJ_DIM,
            hidden: int = 128,
        ) -> None:
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv1d(n_channels, hidden, kernel_size=5, padding=2, dilation=1),
                nn.GELU(),
                nn.Conv1d(hidden, hidden, kernel_size=5, padding=4, dilation=2),
                nn.GELU(),
                nn.Conv1d(hidden, hidden, kernel_size=5, padding=8, dilation=4),
                nn.GELU(),
                nn.Conv1d(hidden, embed_dim, kernel_size=5, padding=16, dilation=8),
                nn.GELU(),
            )
            self.head = nn.Sequential(
                nn.Linear(embed_dim, embed_dim),
                nn.GELU(),
                nn.Linear(embed_dim, proj_dim),
            )

        def forward(self, x: "torch.Tensor", mask: "torch.Tensor"):
            h = self.conv(x)                                   # (B, D, L)
            m = mask.unsqueeze(1).to(h.dtype)                  # (B, 1, L)
            cnt = m.sum(dim=2).clamp_min(1.0)                  # (B, 1)
            emb = (h * m).sum(dim=2) / cnt                     # masked mean
            proj = self.head(emb)
            return emb, proj


class VenueEncoder:
    """Torch encoder wrapper: deterministic init, batched numpy embed().

    ``fit`` is delegated to ``contrastive.train_contrastive_encoder`` (the
    driver calls that trainer); this wrapper owns model/device/inference.
    """

    verdict_bearing = True

    def __init__(self, *, device: str = "auto", seed: int = 42) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "torch nicht verfuegbar — VenueEncoder braucht torch; fuer "
                "Sandbox-Pipeline-Tests NumpyFallbackEncoder verwenden."
            )
        self.seed = int(seed)
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        torch.manual_seed(self.seed)
        self.model = TemporalCNN().to(self.device)

    def num_parameters(self) -> int:
        return int(sum(p.numel() for p in self.model.parameters() if p.requires_grad))

    def embed(
        self, x: np.ndarray, mask: np.ndarray, *, batch_size: int = 1024
    ) -> np.ndarray:
        """Pre-projection embeddings (n, EMBED_DIM) as float64 numpy."""
        self.model.eval()
        outs: list[np.ndarray] = []
        with torch.no_grad():
            for i in range(0, x.shape[0], batch_size):
                xb = torch.from_numpy(np.asarray(x[i:i + batch_size], dtype=np.float32)).to(self.device)
                mb = torch.from_numpy(np.asarray(mask[i:i + batch_size], dtype=bool)).to(self.device)
                emb, _ = self.model(xb, mb)
                outs.append(emb.cpu().numpy().astype(np.float64))
        return np.concatenate(outs, axis=0)

    def save(self, path: str) -> None:
        torch.save({"state_dict": self.model.state_dict(), "seed": self.seed}, path)


# ---------------------------------------------------------------------------
# Numpy fallback (sandbox pipeline testing ONLY — never verdict-bearing)
# ---------------------------------------------------------------------------

class NumpyFallbackEncoder:
    """Deterministic untrained summary-statistic featurizer (NO torch).

    Purpose: exercise the fold construction, permutation-null RETRAINING
    semantics (``fit`` is called once per permutation replicate, matching
    the real path's full-retraining contract) and gate statistics in the
    sandbox. It computes per-channel masked mean/std/lag-1-autocorrelation/
    mean-abs-diff and a fixed random projection. It does NOT learn a
    contrastive representation — any payload produced through it is marked
    ``verdict_bearing = False`` by the driver.
    """

    verdict_bearing = False

    def __init__(self, *, device: str = "cpu", seed: int = 42, out_dim: int = 32) -> None:
        self.device = "cpu"
        self.seed = int(seed)
        self.out_dim = int(out_dim)
        self.n_fit_calls = 0
        rng = np.random.default_rng(self.seed)
        self._proj = rng.standard_normal((4 * N_CHANNELS, self.out_dim)) / np.sqrt(4 * N_CHANNELS)

    def fit(self, x: np.ndarray, mask: np.ndarray, node_ids: np.ndarray, **_: Any) -> dict[str, Any]:
        """No-op 'training' (counts calls so tests can assert retraining)."""
        self.n_fit_calls += 1
        return {"trained": False, "note": "numpy fallback — no contrastive training"}

    @staticmethod
    def _summary_features(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float64)
        m = np.asarray(mask, dtype=np.float64)[:, None, :]
        cnt = np.maximum(m.sum(axis=2), 2.0)
        mean = (x * m).sum(axis=2) / cnt
        cent = (x - mean[:, :, None]) * m
        var = (cent ** 2).sum(axis=2) / cnt
        sd = np.sqrt(np.maximum(var, 1e-12))
        # masked lag-1 autocorrelation per channel
        pair = m[:, :, 1:] * m[:, :, :-1]
        n_pair = np.maximum(pair.sum(axis=2), 1.0)
        ac1 = ((cent[:, :, 1:] * cent[:, :, :-1] * pair).sum(axis=2)
               / (n_pair * np.maximum(var, 1e-12)))
        # masked mean absolute first difference per channel
        mad = (np.abs(x[:, :, 1:] - x[:, :, :-1]) * pair).sum(axis=2) / n_pair
        return np.concatenate([mean, sd, ac1, mad], axis=1)

    def embed(self, x: np.ndarray, mask: np.ndarray, *, batch_size: int = 0) -> np.ndarray:
        return self._summary_features(x, mask) @ self._proj


def make_encoder_factory(
    *, use_torch: bool, device: str = "auto", seed: int = 42
):
    """Encoder factory for the driver: fresh encoder per (re)training.

    The permutation null REQUIRES a fresh, fully retrained encoder per
    replicate (registry H-17: 20 Retrainings je Fold, KEIN Frozen-Model-
    Shuffling) — hence a factory, never a shared instance.
    """
    if use_torch:
        if not TORCH_AVAILABLE:
            raise RuntimeError("torch nicht verfuegbar — use_torch=True unmoeglich")

        def factory(rep_seed: int):
            return VenueEncoder(device=device, seed=rep_seed)
    else:
        def factory(rep_seed: int):
            return NumpyFallbackEncoder(seed=rep_seed)
    return factory


__all__ = [
    "EMBED_DIM",
    "PROJ_DIM",
    "TORCH_AVAILABLE",
    "NumpyFallbackEncoder",
    "VenueEncoder",
    "cuda_available",
    "gpu_report",
    "make_encoder_factory",
]
