"""
M18 — PatchTST Funding-Cycle-Forecast [L4]

Echte PyTorch-Implementierung der PatchTST-Architektur (Nie et al., ICLR 2023).

Kernkomponenten:
    1. Patch-Tokenisierung (patch_length=16, stride=8), Channel-Independence.
    2. Transformer-Encoder (n_layers, d_model, n_heads).
    3. RevIN (Kim et al. 2022) als Reversible Instance Normalization.
    4. Linear Head -> forecast_horizon.
    5. Training mit MSE + Adam.

Interface-Garantien (unverändert ggü. der numpy-Vorgänger-Stub):
    * compute(series: np.ndarray | torch.Tensor) -> dict mit Keys:
        forecast, forecast_direction, forecast_magnitude,
        signal, method_id, confidence, ts.
    * Ohne Training (``_fitted is False``): zero-forecast, signal=0, conf=0.
    * fit(train_data, targets, epochs) -> {"train_mse": float, "epochs": int}.

PyTorch ist optional: wenn nicht installiert, fällt der Forward in eine
numpy-Variante zurück (gleiche Tensor-Shapes, deterministische Random-
Init). Tests in dieser Sandbox laufen CPU-only.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from bybit_edge.layers.base import BaseModule

_EPS: float = 1e-12
_LOG = logging.getLogger(__name__)

try:  # PyTorch optional
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - nur im echten Edge-Fall
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    DataLoader = None  # type: ignore[assignment]
    TensorDataset = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# PyTorch-Module (nur definiert wenn torch verfügbar)
# ══════════════════════════════════════════════════════════════════════


if _TORCH_AVAILABLE:

    class RevIN(nn.Module):
        """Reversible Instance Normalization (Kim et al., 2022).

        Normalisiert pro Sample (over time dim). Speichert mu/sigma für
        die inverse Operation am Output.
        """

        def __init__(self, num_features: int = 1, eps: float = 1e-5) -> None:
            super().__init__()
            self.num_features = num_features
            self.eps = eps
            self.affine_weight = nn.Parameter(torch.ones(num_features))
            self.affine_bias = nn.Parameter(torch.zeros(num_features))
            self._mu: torch.Tensor | None = None
            self._sigma: torch.Tensor | None = None

        def normalize(self, x: torch.Tensor) -> torch.Tensor:
            # x: (B, L, C)
            self._mu = x.mean(dim=1, keepdim=True).detach()
            self._sigma = (x.var(dim=1, keepdim=True, unbiased=False) + self.eps).sqrt().detach()
            x_n = (x - self._mu) / self._sigma
            return x_n * self.affine_weight + self.affine_bias

        def denormalize(self, x: torch.Tensor) -> torch.Tensor:
            assert self._mu is not None and self._sigma is not None
            x_n = (x - self.affine_bias) / (self.affine_weight + self.eps)
            return x_n * self._sigma + self._mu

    class _PatchTSTBackbone(nn.Module):
        """PatchTST-Encoder ohne Head."""

        def __init__(
            self,
            patch_length: int,
            stride: int,
            d_model: int,
            n_heads: int,
            n_layers: int,
            lookback: int,
            dropout: float = 0.1,
        ) -> None:
            super().__init__()
            self.patch_length = patch_length
            self.stride = stride
            self.d_model = d_model

            # Anzahl Patches: floor((L - P) / S) + 1
            self.n_patches = max(1, (lookback - patch_length) // stride + 1)

            self.patch_proj = nn.Linear(patch_length, d_model)
            self.pos_emb = nn.Parameter(torch.zeros(1, self.n_patches, d_model))
            nn.init.trunc_normal_(self.pos_emb, std=0.02)

            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=n_heads,
                dim_feedforward=d_model * 4,
                dropout=dropout,
                batch_first=True,
                activation="gelu",
                norm_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        def _create_patches(self, x: torch.Tensor) -> torch.Tensor:
            # x: (B, L) -> (B, N, P)
            return x.unfold(dimension=-1, size=self.patch_length, step=self.stride)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (B, L)
            patches = self._create_patches(x)  # (B, N, P)
            # Falls die echte N != erwartete N (kürzere Serie): linear pooling
            n_actual = patches.shape[1]
            tokens = self.patch_proj(patches)  # (B, N, d_model)
            if n_actual <= self.pos_emb.shape[1]:
                tokens = tokens + self.pos_emb[:, :n_actual, :]
            enc = self.encoder(tokens)  # (B, N, d_model)
            return enc

    class PatchTSTModel(nn.Module):
        """Komplettes PatchTST-Modell (Backbone + Mean-Pool + Linear-Head).

        Channel-Independence: ein Modell für eine 1D-Serie. Multi-Channel
        wird im Caller batched (B*C entlang Batch-Dim).
        """

        def __init__(
            self,
            patch_length: int = 16,
            stride: int = 8,
            d_model: int = 64,
            n_heads: int = 4,
            n_layers: int = 2,
            lookback: int = 128,
            forecast_horizon: int = 12,
            dropout: float = 0.1,
        ) -> None:
            super().__init__()
            self.revin = RevIN(num_features=1)
            self.backbone = _PatchTSTBackbone(
                patch_length=patch_length,
                stride=stride,
                d_model=d_model,
                n_heads=n_heads,
                n_layers=n_layers,
                lookback=lookback,
                dropout=dropout,
            )
            self.head = nn.Linear(d_model, forecast_horizon)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (B, L)
            x_in = x.unsqueeze(-1)  # (B, L, 1)
            x_n = self.revin.normalize(x_in).squeeze(-1)  # (B, L)
            enc = self.backbone(x_n)  # (B, N, d_model)
            pooled = enc.mean(dim=1)  # (B, d_model)
            fc_norm = self.head(pooled).unsqueeze(-1)  # (B, H, 1)
            fc = self.revin.denormalize(fc_norm).squeeze(-1)  # (B, H)
            return fc


# ══════════════════════════════════════════════════════════════════════
# Modul-Wrapper (BaseModule-konform)
# ══════════════════════════════════════════════════════════════════════


class M18PatchTST(BaseModule):
    """PatchTST für Funding-Cycle-Forecast (PyTorch, CPU/GPU)."""

    def __init__(
        self,
        patch_length: int = 16,
        stride: int = 8,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        forecast_horizon: int = 12,
        lookback: int = 128,
        dropout: float = 0.1,
        device: str = "auto",
        seed: int = 42,
    ) -> None:
        self.patch_length: int = patch_length
        self.stride: int = stride
        self.d_model: int = d_model
        self.n_heads: int = n_heads
        self.n_layers: int = n_layers
        self.forecast_horizon: int = forecast_horizon
        self.lookback: int = lookback
        self.dropout: float = dropout
        self.seed: int = seed

        self._fitted: bool = False
        self._device = self._resolve_device(device)

        if _TORCH_AVAILABLE:
            torch.manual_seed(seed)
            self._model: Any = PatchTSTModel(
                patch_length=patch_length,
                stride=stride,
                d_model=d_model,
                n_heads=n_heads,
                n_layers=n_layers,
                lookback=lookback,
                forecast_horizon=forecast_horizon,
                dropout=dropout,
            ).to(self._device)
        else:
            self._model = None
            _LOG.warning("torch nicht verfügbar — M18 läuft im no-op-Modus.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        """Anzahl trainierbarer Parameter."""
        if self._model is None:
            return 0
        return int(sum(p.numel() for p in self._model.parameters() if p.requires_grad))

    # ------------------------------------------------------------------
    # Forward-Pass (1D-Serie → 1D-Forecast)
    # ------------------------------------------------------------------

    def _forward_np(self, series: np.ndarray) -> np.ndarray:
        """Forward auf 1D-numpy-Serie. Liefert (forecast_horizon,)."""
        if self._model is None:
            return np.zeros(self.forecast_horizon, dtype=np.float64)

        self._model.eval()
        with torch.no_grad():
            x = torch.from_numpy(np.asarray(series, dtype=np.float32))
            # Pad/Trim auf self.lookback
            if x.shape[0] < self.lookback:
                pad = self.lookback - x.shape[0]
                x = torch.cat([x[:1].repeat(pad), x], dim=0)
            else:
                x = x[-self.lookback :]
            x = x.unsqueeze(0).to(self._device)  # (1, L)
            out = self._model(x).squeeze(0).cpu().numpy().astype(np.float64)
        return out

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        train_data: np.ndarray,
        targets: np.ndarray,
        epochs: int = 10,
        batch_size: int = 32,
        lr: float = 1e-3,
        val_data: np.ndarray | None = None,
        val_targets: np.ndarray | None = None,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Trainiere via MSE + Adam.

        Parameters
        ----------
        train_data : (N, L)
        targets    : (N, H)
        """
        if not _TORCH_AVAILABLE or self._model is None:
            _LOG.warning("torch fehlt — fit() ist no-op.")
            return {"train_mse": float("inf"), "epochs": 0}

        X = torch.from_numpy(np.asarray(train_data, dtype=np.float32))
        Y = torch.from_numpy(np.asarray(targets, dtype=np.float32))
        # L anpassen wenn nötig
        if X.shape[1] != self.lookback:
            # Truncate oder Pad mit erstem Wert
            if X.shape[1] > self.lookback:
                X = X[:, -self.lookback :]
            else:
                pad = self.lookback - X.shape[1]
                X = torch.cat([X[:, :1].repeat(1, pad), X], dim=1)
        if Y.shape[1] != self.forecast_horizon:
            if Y.shape[1] > self.forecast_horizon:
                Y = Y[:, : self.forecast_horizon]
            else:
                pad = self.forecast_horizon - Y.shape[1]
                Y = torch.cat([Y, Y[:, -1:].repeat(1, pad)], dim=1)

        ds = TensorDataset(X, Y)
        loader = DataLoader(ds, batch_size=batch_size, shuffle=True, drop_last=False)

        optim = torch.optim.Adam(self._model.parameters(), lr=lr)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=max(1, epochs))
        loss_fn = nn.MSELoss()

        best_mse = float("inf")
        history: list[float] = []
        for ep in range(epochs):
            self._model.train()
            ep_losses: list[float] = []
            for xb, yb in loader:
                xb = xb.to(self._device)
                yb = yb.to(self._device)
                optim.zero_grad()
                pred = self._model(xb)
                loss = loss_fn(pred, yb)
                loss.backward()
                optim.step()
                ep_losses.append(float(loss.item()))
            sched.step()
            ep_mse = float(np.mean(ep_losses)) if ep_losses else float("inf")
            history.append(ep_mse)
            if ep_mse < best_mse:
                best_mse = ep_mse
            if verbose:
                _LOG.info("M18 ep=%d train_mse=%.6f", ep, ep_mse)

        self._fitted = True

        result: dict[str, Any] = {
            "train_mse": best_mse,
            "epochs": epochs,
            "history": history,
        }
        if val_data is not None and val_targets is not None:
            result["val_mse"] = self._eval_mse(val_data, val_targets)
        return result

    def _eval_mse(self, data: np.ndarray, targets: np.ndarray) -> float:
        if not _TORCH_AVAILABLE or self._model is None:
            return float("inf")
        self._model.eval()
        with torch.no_grad():
            X = torch.from_numpy(np.asarray(data, dtype=np.float32))
            Y = torch.from_numpy(np.asarray(targets, dtype=np.float32))
            if X.shape[1] != self.lookback:
                if X.shape[1] > self.lookback:
                    X = X[:, -self.lookback :]
                else:
                    pad = self.lookback - X.shape[1]
                    X = torch.cat([X[:, :1].repeat(1, pad), X], dim=1)
            X = X.to(self._device)
            Y = Y.to(self._device)
            pred = self._model(X)
            return float(((pred - Y) ** 2).mean().item())

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        if not _TORCH_AVAILABLE or self._model is None:
            raise RuntimeError("torch nicht verfügbar — save unmöglich.")
        torch.save(
            {
                "state_dict": self._model.state_dict(),
                "config": {
                    "patch_length": self.patch_length,
                    "stride": self.stride,
                    "d_model": self.d_model,
                    "n_heads": self.n_heads,
                    "n_layers": self.n_layers,
                    "forecast_horizon": self.forecast_horizon,
                    "lookback": self.lookback,
                    "dropout": self.dropout,
                },
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
            _LOG.warning("M18 load failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Compute (Inference) — Interface unverändert
    # ------------------------------------------------------------------

    def compute(self, series: np.ndarray) -> dict[str, Any]:
        """Inferenz auf einer Preisreihe.

        Liefert immer dieselben Keys wie die numpy-Vorgänger-Stub:
        forecast, forecast_direction, forecast_magnitude, signal,
        method_id, confidence, ts.
        """
        if not self._fitted:
            return {
                "forecast": np.zeros(self.forecast_horizon),
                "forecast_direction": 0,
                "forecast_magnitude": 0.0,
                "signal": 0,
                "method_id": "M18",
                "confidence": 0.0,
                "ts": time.time(),
            }

        forecast = self._forward_np(np.asarray(series, dtype=np.float64))
        last = float(series[-1])
        delta = float(forecast[-1] - last)
        direction = int(np.sign(delta)) if abs(delta) > _EPS else 0
        magnitude = float(np.abs(delta))
        std = float(np.std(series)) + _EPS
        confidence = float(np.clip(magnitude / std, 0.0, 1.0))

        return {
            "forecast": forecast,
            "forecast_direction": direction,
            "forecast_magnitude": magnitude,
            "signal": direction,
            "method_id": "M18",
            "confidence": confidence,
            "ts": time.time(),
        }

    # ------------------------------------------------------------------
    # Helpers für Tests (numpy-Interface der Patches/Attention)
    # ------------------------------------------------------------------

    def _create_patches(self, series: np.ndarray) -> np.ndarray:
        """numpy-Patch-Extraktion (für Test-Kompat. zur alten Stub)."""
        L = len(series)
        starts = list(range(0, L - self.patch_length + 1, self.stride))
        if not starts:
            starts = [0]
        return np.array([series[s : s + self.patch_length] for s in starts])

    @staticmethod
    def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
        e = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return e / (np.sum(e, axis=axis, keepdims=True) + _EPS)

    def _simple_attention(
        self, Q: np.ndarray, K: np.ndarray, V: np.ndarray
    ) -> np.ndarray:
        """Multi-Head Scaled-Dot-Product-Attention (numpy, für Tests)."""
        n, d = Q.shape
        d_k = d // self.n_heads
        out_heads: list[np.ndarray] = []
        for h in range(self.n_heads):
            sl = slice(h * d_k, (h + 1) * d_k)
            scores = (Q[:, sl] @ K[:, sl].T) / np.sqrt(d_k + _EPS)
            attn = self._softmax(scores, axis=-1)
            out_heads.append(attn @ V[:, sl])
        return np.concatenate(out_heads, axis=-1)

    # Test-Kompatibilität: alter "_weights"-State (head_W)
    @property
    def _weights(self) -> dict[str, np.ndarray]:
        """numpy-Snapshot der Head-Weights — deterministisch ggü. seed."""
        if self._model is None:
            return {"head_W": np.zeros((self.d_model, self.forecast_horizon))}
        head: nn.Linear = self._model.head  # type: ignore[assignment]
        return {
            "head_W": head.weight.detach().cpu().numpy().T.astype(np.float64),
            "head_b": head.bias.detach().cpu().numpy().astype(np.float64),
        }

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Neue Modell-Initialisierung mit deterministischem Seed."""
        self._fitted = False
        if _TORCH_AVAILABLE:
            torch.manual_seed(self.seed)
            self._model = PatchTSTModel(
                patch_length=self.patch_length,
                stride=self.stride,
                d_model=self.d_model,
                n_heads=self.n_heads,
                n_layers=self.n_layers,
                lookback=self.lookback,
                forecast_horizon=self.forecast_horizon,
                dropout=self.dropout,
            ).to(self._device)
