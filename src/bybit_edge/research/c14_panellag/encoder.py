"""Per-node PatchTST-style encoders + cross-node attention for H-14 (GPU).

Architecture (registry H-14, pre-fixed — NOT tuned on the test windows):

    input (B, N=12, L) 1s log-returns
      -> per-node PatchTST-style encoder (one encoder PER node, own weights;
         patch projection + positional embedding + Transformer encoder +
         mean-pool — adapted from ``bybit_edge.layers.l4_pattern.m18_patchtst``,
         the registry-named scaffolding this module reuses)
      -> node-embedding table + ONE cross-node multi-head-attention block
         (12-token sequence, residual + LayerNorm + FFN)
      -> per-node linear head -> logit for sign(next 10s return) per node.

Loss: masked BCE-with-logits (exactly-zero forward returns are masked).
Edge information flows ONLY through the cross-node attention block — the
retrain ablation of a source node j (circular-shift surrogate) therefore
measures exactly the cross-node contribution the registry defines.

PyTorch is OPTIONAL and follows the m18_patchtst pattern verbatim:
``_TORCH_AVAILABLE`` flag, ``device="auto"`` resolution, fit/save/load.
WITHOUT torch this module stays importable; ``check_gpu()`` reports the
truth and every training entry point raises ``ComputeGateError`` instead of
silently producing numbers. The m18 numpy fallback exists for INFERENCE
convenience there — it is deliberately NOT replicated for training here:
the registered ~226-retrain null is GPU-gated (registry H-14 Rechenaufwand)
and MUST NOT be quietly replaced by a CPU/numpy imitation.

KAPITALFREI: pure sign-forecast log-loss machinery; no friction, bps, PnL,
Sharpe logic anywhere.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

_LOG = logging.getLogger(__name__)

try:  # PyTorch optional (m18_patchtst pattern)
    import torch
    import torch.nn as nn
    import torch.utils.data  # noqa: F401  (Dataset/DataLoader below)

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - sandbox has no torch
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False


class ComputeGateError(RuntimeError):
    """Raised when a training entry point is hit without the required compute."""


def check_gpu() -> dict[str, Any]:
    """Honest torch/CUDA availability report (NO training attempt).

    Used by the CLI ``--check-gpu-only`` compute-gating mode (analog of the
    H-11/H-13 data-gating check, but for compute).
    """
    info: dict[str, Any] = {
        "torch_available": bool(_TORCH_AVAILABLE),
        "torch_version": None,
        "cuda_available": False,
        "cuda_device_count": 0,
        "device_name": None,
        "gpu_ready": False,
    }
    if _TORCH_AVAILABLE:
        info["torch_version"] = str(torch.__version__)
        try:
            info["cuda_available"] = bool(torch.cuda.is_available())
            if info["cuda_available"]:
                info["cuda_device_count"] = int(torch.cuda.device_count())
                info["device_name"] = str(torch.cuda.get_device_name(0))
        except Exception as exc:  # pragma: no cover - driver-level CUDA quirks
            info["cuda_error"] = str(exc)
    info["gpu_ready"] = bool(info["torch_available"] and info["cuda_available"])
    return info


# ---------------------------------------------------------------------------
# Pre-fixed hyperparameters (builder-fixed BEFORE any run; README_H14 table).
# NOT exposed as CLI knobs — the registry self-kill clause forbids tuning the
# architecture/hyperparameter grid on the test windows.
# ---------------------------------------------------------------------------
DEFAULT_MODEL_PARAMS: dict[str, Any] = {
    "lookback": 120,       # 120 s input window per node (1s grid)
    "patch_length": 16,
    "patch_stride": 8,
    "d_model": 64,
    "n_heads": 4,
    "n_layers": 2,
    "cross_heads": 4,
    "dropout": 0.1,
}
DEFAULT_TRAIN_PARAMS: dict[str, Any] = {
    "epochs": 4,
    "batch_size": 512,
    "lr": 1e-3,
    "sample_stride": 10,   # anchor every 10 s (one per target horizon)
    "train_frac": 0.7,
    "horizon": 10,         # registered: sign of the NEXT 10s return
}


# ══════════════════════════════════════════════════════════════════════
# PyTorch modules (only defined when torch is available — m18 pattern)
# ══════════════════════════════════════════════════════════════════════

if _TORCH_AVAILABLE:

    class _NodeEncoder(nn.Module):
        """PatchTST-style encoder for ONE node's 1D return window.

        Patch projection + learned positional embedding + Transformer
        encoder + mean-pool (adapted from m18 ``_PatchTSTBackbone``; no RevIN
        — inputs are returns, and the target is a SIGN, so instance
        de-meaning would leak nothing but also help nothing).
        """

        def __init__(
            self,
            lookback: int,
            patch_length: int,
            patch_stride: int,
            d_model: int,
            n_heads: int,
            n_layers: int,
            dropout: float,
        ) -> None:
            super().__init__()
            self.patch_length = patch_length
            self.patch_stride = patch_stride
            self.n_patches = max(1, (lookback - patch_length) // patch_stride + 1)
            self.patch_proj = nn.Linear(patch_length, d_model)
            self.pos_emb = nn.Parameter(torch.zeros(1, self.n_patches, d_model))
            nn.init.trunc_normal_(self.pos_emb, std=0.02)
            layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=n_heads,
                dim_feedforward=d_model * 4,
                dropout=dropout,
                batch_first=True,
                activation="gelu",
                norm_first=True,
            )
            self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (B, L) -> patches (B, P, patch_length)
            patches = x.unfold(-1, self.patch_length, self.patch_stride)
            tokens = self.patch_proj(patches)
            n_actual = tokens.shape[1]
            if n_actual <= self.pos_emb.shape[1]:
                tokens = tokens + self.pos_emb[:, :n_actual, :]
            enc = self.encoder(tokens)  # (B, P, d)
            return enc.mean(dim=1)  # (B, d)

    class PanelLagModel(nn.Module):
        """12-node panel model: per-node encoders + cross-node attention."""

        def __init__(self, n_nodes: int, **mp: Any) -> None:
            super().__init__()
            p = {**DEFAULT_MODEL_PARAMS, **mp}
            self.n_nodes = n_nodes
            d = int(p["d_model"])
            self.encoders = nn.ModuleList(
                _NodeEncoder(
                    lookback=int(p["lookback"]),
                    patch_length=int(p["patch_length"]),
                    patch_stride=int(p["patch_stride"]),
                    d_model=d,
                    n_heads=int(p["n_heads"]),
                    n_layers=int(p["n_layers"]),
                    dropout=float(p["dropout"]),
                )
                for _ in range(n_nodes)
            )
            self.node_emb = nn.Parameter(torch.zeros(1, n_nodes, d))
            nn.init.trunc_normal_(self.node_emb, std=0.02)
            self.cross_attn = nn.MultiheadAttention(
                d, int(p["cross_heads"]), dropout=float(p["dropout"]),
                batch_first=True,
            )
            self.norm1 = nn.LayerNorm(d)
            self.norm2 = nn.LayerNorm(d)
            self.ffn = nn.Sequential(
                nn.Linear(d, d * 4), nn.GELU(),
                nn.Dropout(float(p["dropout"])), nn.Linear(d * 4, d),
            )
            self.heads = nn.ModuleList(nn.Linear(d, 1) for _ in range(n_nodes))

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (B, N, L) -> logits (B, N)
            feats = torch.stack(
                [enc(x[:, j, :]) for j, enc in enumerate(self.encoders)], dim=1
            )  # (B, N, d)
            h = feats + self.node_emb
            attn_out, _ = self.cross_attn(self.norm1(h), self.norm1(h), self.norm1(h))
            h = h + attn_out
            h = h + self.ffn(self.norm2(h))
            logits = torch.cat(
                [head(h[:, j, :]) for j, head in enumerate(self.heads)], dim=1
            )  # (B, N)
            return logits

    class _PanelSampleDataset(torch.utils.data.Dataset):
        """Lazy (features, labels, mask) slices from the (N, T) return matrix.

        Materialising all samples of a ~50-day window would need GBs; this
        slices on the fly. NaNs outside valid anchors never enter a batch
        (anchors are pre-filtered via ``panel.valid_sample_indices``).
        """

        def __init__(
            self,
            returns: np.ndarray,
            anchors: np.ndarray,
            labels: np.ndarray,
            mask: np.ndarray,
            lookback: int,
        ) -> None:
            self.returns = returns
            self.anchors = anchors
            self.labels = labels
            self.mask = mask
            self.lookback = lookback

        def __len__(self) -> int:
            return int(self.anchors.shape[0])

        def __getitem__(self, k: int):
            t = int(self.anchors[k])
            x = self.returns[:, t - self.lookback + 1: t + 1]
            return (
                torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)),
                torch.from_numpy(self.labels[k]),
                torch.from_numpy(self.mask[k]),
            )


# ══════════════════════════════════════════════════════════════════════
# Wrapper (m18-style: device="auto", fit / evaluate / save / load)
# ══════════════════════════════════════════════════════════════════════


class PanelLagNet:
    """Torch-optional wrapper around ``PanelLagModel`` (m18_patchtst style)."""

    def __init__(
        self,
        n_nodes: int,
        *,
        device: str = "auto",
        seed: int = 42,
        **model_params: Any,
    ) -> None:
        self.n_nodes = int(n_nodes)
        self.seed = int(seed)
        self.model_params = {**DEFAULT_MODEL_PARAMS, **model_params}
        self.lookback = int(self.model_params["lookback"])
        self._fitted = False
        self._device = self._resolve_device(device)
        if _TORCH_AVAILABLE:
            torch.manual_seed(seed)
            self._model: Any = PanelLagModel(
                self.n_nodes, **self.model_params
            ).to(self._device)
        else:
            self._model = None
            _LOG.warning(
                "torch nicht verfuegbar — PanelLagNet ist compute-gated "
                "(kein Training moeglich)."
            )

    @staticmethod
    def _resolve_device(device: str) -> str:
        if not _TORCH_AVAILABLE:
            return "cpu"
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    @property
    def device(self) -> str:
        return self._device

    def num_parameters(self) -> int:
        if self._model is None:
            return 0
        return int(sum(p.numel() for p in self._model.parameters() if p.requires_grad))

    # ------------------------------------------------------------------
    # Training / evaluation on a (N, T) return matrix
    # ------------------------------------------------------------------

    def _require_torch(self) -> None:
        if not _TORCH_AVAILABLE or self._model is None:
            raise ComputeGateError(
                "GPU/torch erforderlich: torch ist nicht installiert — "
                "H-14-Training ist compute-gated (Registry: GPU zwingend). "
                "Kein numpy-Ersatztraining."
            )

    def _prep(
        self, returns: np.ndarray, anchors: np.ndarray, horizon: int
    ) -> "torch.utils.data.Dataset":
        from .panel import target_sign_labels

        labels, mask = target_sign_labels(returns, anchors, horizon)
        return _PanelSampleDataset(
            np.asarray(returns, dtype=np.float32),
            np.asarray(anchors, dtype=np.int64),
            labels.astype(np.float32),
            mask.astype(np.float32),
            self.lookback,
        )

    def fit_panel(
        self,
        returns: np.ndarray,
        train_anchors: np.ndarray,
        *,
        horizon: int,
        epochs: int = 4,
        batch_size: int = 512,
        lr: float = 1e-3,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Train with masked BCE over all nodes (Adam + cosine schedule)."""
        self._require_torch()
        ds = self._prep(returns, train_anchors, horizon)
        _pin = self._device == "cuda"
        g = torch.Generator()
        g.manual_seed(self.seed)
        loader = torch.utils.data.DataLoader(
            ds, batch_size=batch_size, shuffle=True, drop_last=False,
            pin_memory=_pin, generator=g,
        )
        optim = torch.optim.Adam(self._model.parameters(), lr=lr)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=max(1, epochs))
        loss_fn = nn.BCEWithLogitsLoss(reduction="none")
        history: list[float] = []
        for ep in range(epochs):
            self._model.train()
            ep_loss, ep_n = 0.0, 0.0
            for xb, yb, mb in loader:
                xb = xb.to(self._device, non_blocking=_pin)
                yb = yb.to(self._device, non_blocking=_pin)
                mb = mb.to(self._device, non_blocking=_pin)
                optim.zero_grad()
                raw = loss_fn(self._model(xb), yb) * mb
                denom = mb.sum().clamp_min(1.0)
                loss = raw.sum() / denom
                loss.backward()
                optim.step()
                ep_loss += float(raw.sum().item())
                ep_n += float(denom.item())
            sched.step()
            ep_mean = ep_loss / max(ep_n, 1.0)
            history.append(ep_mean)
            if verbose:
                _LOG.info("PanelLagNet ep=%d train_log_loss=%.6f", ep, ep_mean)
        self._fitted = True
        return {
            "train_log_loss": history[-1] if history else float("inf"),
            "epochs": epochs,
            "history": history,
            "n_train_samples": len(ds),
            "device": self._device,
            "n_parameters": self.num_parameters(),
        }

    def eval_log_loss_panel(
        self,
        returns: np.ndarray,
        anchors: np.ndarray,
        *,
        horizon: int,
        batch_size: int = 1024,
    ) -> dict[str, Any]:
        """Per-node OOS log-loss (natural log, masked mean) — the T(j->i) base."""
        self._require_torch()
        ds = self._prep(returns, anchors, horizon)
        loader = torch.utils.data.DataLoader(
            ds, batch_size=batch_size, shuffle=False, drop_last=False,
        )
        loss_fn = nn.BCEWithLogitsLoss(reduction="none")
        tot = torch.zeros(self.n_nodes, dtype=torch.float64)
        cnt = torch.zeros(self.n_nodes, dtype=torch.float64)
        self._model.eval()
        with torch.no_grad():
            for xb, yb, mb in loader:
                xb = xb.to(self._device)
                yb = yb.to(self._device)
                mb = mb.to(self._device)
                raw = loss_fn(self._model(xb), yb) * mb
                tot += raw.sum(dim=0).double().cpu()
                cnt += mb.sum(dim=0).double().cpu()
        per_node = (tot / cnt.clamp_min(1.0)).numpy()
        return {
            "per_node_log_loss": [float(v) for v in per_node],
            "per_node_n_masked": [float(v) for v in cnt.numpy()],
            "n_oos_samples": len(ds),
        }

    # ------------------------------------------------------------------
    # Save / Load (m18 pattern)
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        self._require_torch()
        torch.save(
            {
                "state_dict": self._model.state_dict(),
                "config": {"n_nodes": self.n_nodes, **self.model_params},
                "fitted": self._fitted,
            },
            path,
        )

    def load(self, path: str) -> bool:
        if not _TORCH_AVAILABLE or self._model is None:
            return False
        try:
            ckpt = torch.load(path, map_location=self._device, weights_only=False)
            self._model.load_state_dict(ckpt["state_dict"])
            self._fitted = bool(ckpt.get("fitted", True))
            return True
        except Exception as exc:  # pragma: no cover
            _LOG.warning("PanelLagNet load failed: %s", exc)
            return False


__all__ = [
    "DEFAULT_MODEL_PARAMS",
    "DEFAULT_TRAIN_PARAMS",
    "ComputeGateError",
    "PanelLagNet",
    "check_gpu",
]
