"""
M19 — TimesNet 2D-Periodicity [L4]

Echte PyTorch-Implementierung der TimesNet-Architektur (Wu et al., ICLR 2023).

Pipeline:
    1. RevIN-Normalisierung der Input-Reihe (channel-wise).
    2. FFT zur Detektion der Top-k dominanten Perioden.
    3. Pro Periode: 1D -> 2D Reshape ``(n_periods, period_length)``.
    4. Vereinfachter Inception-Block (3 Branches: 1x1, 3x3, 5x5 Conv2d
       mit BatchNorm + GELU).
    5. Amplitude-gewichtete Summierung über Perioden (Softmax über Spectrum-
       Amplituden der Top-k-Frequenzen).
    6. Linear Head auf forecast_horizon.
    7. RevIN-Denormalisierung.

Interface-Garantien (unverändert ggü. numpy-Vorgänger):
    * compute(series) -> dict mit Keys forecast, detected_periods,
        forecast_direction, signal, method_id, confidence, ts.
    * Ohne Training: zero-forecast, signal=0, confidence=0.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from bybit_edge._legacy_v1.layers.base import BaseModule

_EPS: float = 1e-12
_LOG = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# PyTorch-Module
# ══════════════════════════════════════════════════════════════════════


if _TORCH_AVAILABLE:

    class _RevIN(nn.Module):
        def __init__(self, eps: float = 1e-5) -> None:
            super().__init__()
            self.eps = eps
            self._mu: torch.Tensor | None = None
            self._sigma: torch.Tensor | None = None

        def normalize(self, x: torch.Tensor) -> torch.Tensor:
            self._mu = x.mean(dim=1, keepdim=True).detach()
            self._sigma = (x.var(dim=1, keepdim=True, unbiased=False) + self.eps).sqrt().detach()
            return (x - self._mu) / self._sigma

        def denormalize(self, x: torch.Tensor) -> torch.Tensor:
            assert self._mu is not None and self._sigma is not None
            return x * self._sigma + self._mu

    class _InceptionBlock2D(nn.Module):
        """3-Branch-Inception-Block (1x1, 3x3, 5x5 + BatchNorm + GELU)."""

        def __init__(self, in_ch: int = 1, out_ch: int = 8) -> None:
            super().__init__()
            self.b1 = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=1, padding=0),
                nn.BatchNorm2d(out_ch),
                nn.GELU(),
            )
            self.b2 = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.GELU(),
            )
            self.b3 = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=5, padding=2),
                nn.BatchNorm2d(out_ch),
                nn.GELU(),
            )
            # Project back to in_ch so we can residual-add
            self.project = nn.Conv2d(out_ch * 3, in_ch, kernel_size=1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (B, C, H, W)
            f = torch.cat([self.b1(x), self.b2(x), self.b3(x)], dim=1)
            f = self.project(f)
            return f + x

    class TimesNetModel(nn.Module):
        """TimesNet-Forecaster.

        Top-k FFT-Perioden werden zur Laufzeit aus der Input-Reihe bestimmt.
        Pro Periode wird ein 2D-Block (Inception) appliziert; danach werden
        die Repräsentationen amplituden-gewichtet summiert.
        """

        def __init__(
            self,
            top_k: int = 3,
            lookback: int = 128,
            forecast_horizon: int = 12,
            channels: int = 8,
        ) -> None:
            super().__init__()
            self.top_k = top_k
            self.lookback = lookback
            self.forecast_horizon = forecast_horizon
            self.revin = _RevIN()
            self.inception = _InceptionBlock2D(in_ch=1, out_ch=channels)
            self.head = nn.Linear(lookback, forecast_horizon)

        @staticmethod
        def _fft_top_k(
            x: torch.Tensor, k: int
        ) -> tuple[list[int], torch.Tensor]:
            """Liefert (periods, amplitudes) für die Top-k FFT-Frequenzen.

            x: (B, L) — wir aggregieren Amplituden über Batch.
            """
            B, L = x.shape
            x0 = x - x.mean(dim=1, keepdim=True)
            spectrum = torch.abs(torch.fft.rfft(x0, dim=1))  # (B, L//2+1)
            amp = spectrum.mean(dim=0)  # (L//2+1,)
            # Skip DC
            if amp.shape[0] <= 1:
                return [max(L, 2)], torch.ones(1, device=x.device)
            usable = min(amp.shape[0], L // 2 + 1)
            amps = amp[1:usable]
            freqs = torch.arange(1, usable, device=x.device)
            k_actual = min(k, amps.shape[0])
            top_vals, top_idx = torch.topk(amps, k_actual)
            periods: list[int] = []
            keep_amps: list[float] = []
            for i in range(k_actual):
                freq = int(freqs[top_idx[i]].item())
                period = max(int(round(L / max(freq, 1))), 2)
                if period not in periods:
                    periods.append(period)
                    keep_amps.append(float(top_vals[i].item()))
            if not periods:
                periods = [max(L, 2)]
                keep_amps = [1.0]
            amp_tensor = torch.tensor(keep_amps, device=x.device, dtype=x.dtype)
            return periods, amp_tensor

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (B, L)
            x_norm = self.revin.normalize(x)
            periods, amps = self._fft_top_k(x_norm, self.top_k)
            weights = torch.softmax(amps, dim=0)

            B, L = x_norm.shape
            aggregated = torch.zeros(B, L, device=x.device, dtype=x.dtype)
            for p_idx, period in enumerate(periods):
                # In-Place 2D Reshape: pad so dass L % period == 0
                rows = (L + period - 1) // period
                pad_len = rows * period - L
                if pad_len > 0:
                    xp = torch.nn.functional.pad(x_norm, (0, pad_len))
                else:
                    xp = x_norm
                x2d = xp.view(B, 1, rows, period)  # (B,1,H,W)
                feat = self.inception(x2d)  # (B,1,H,W)
                # Zurück nach 1D, original L
                flat = feat.view(B, rows * period)[:, :L]
                aggregated = aggregated + weights[p_idx] * flat

            out_norm = self.head(aggregated)  # (B, H)
            return self.revin.denormalize(out_norm)


# ══════════════════════════════════════════════════════════════════════
# Modul-Wrapper
# ══════════════════════════════════════════════════════════════════════


class M19TimesNet(BaseModule):
    """TimesNet mit echtem PyTorch-Backend (CPU/GPU)."""

    def __init__(
        self,
        top_k: int = 3,
        forecast_horizon: int = 12,
        lookback: int = 128,
        channels: int = 8,
        device: str = "auto",
        seed: int = 42,
    ) -> None:
        self.top_k: int = top_k
        self.forecast_horizon: int = forecast_horizon
        self.lookback: int = lookback
        self.channels: int = channels
        self.seed: int = seed

        self._fitted: bool = False
        # Bewahre den Test-Vertrag der numpy-Stub: _weights ist dict mit np-Arrays
        self._weights: dict[str, np.ndarray] = {}
        self._device = self._resolve_device(device)

        if _TORCH_AVAILABLE:
            torch.manual_seed(seed)
            self._model: Any = TimesNetModel(
                top_k=top_k,
                lookback=lookback,
                forecast_horizon=forecast_horizon,
                channels=channels,
            ).to(self._device)
        else:
            self._model = None
            _LOG.warning("torch fehlt — M19 läuft im no-op-Modus.")

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
    # Klassische numpy-Helfer (Test-Kompatibilität!)
    # ------------------------------------------------------------------

    @staticmethod
    def _fft_top_k_periods(series: np.ndarray, k: int = 3) -> list[int]:
        N = len(series)
        if N < 4:
            return [max(N, 2)]
        x = series - np.mean(series)
        spectrum = np.abs(np.fft.rfft(x))
        usable = min(len(spectrum), N // 2 + 1)
        if usable <= 1:
            return [max(N, 2)]
        amps = spectrum[1:usable]
        freqs = np.arange(1, usable)
        k_actual = min(k, len(amps))
        top_indices = np.argsort(amps)[-k_actual:][::-1]
        periods: list[int] = []
        for idx in top_indices:
            freq = freqs[idx]
            period = max(int(round(N / freq)), 2)
            if period not in periods:
                periods.append(period)
        return periods if periods else [max(N, 2)]

    @staticmethod
    def _reshape_2d(series: np.ndarray, period: int) -> np.ndarray:
        period = max(period, 2)
        L = len(series)
        n_full = L // period
        if n_full < 1:
            return series.reshape(1, -1)
        used = n_full * period
        return series[-used:].reshape(n_full, period)

    # ------------------------------------------------------------------
    # Forward (1D)
    # ------------------------------------------------------------------

    def _forward_np(self, series: np.ndarray) -> np.ndarray:
        if self._model is None:
            return np.zeros(self.forecast_horizon, dtype=np.float64)
        self._model.eval()
        with torch.no_grad():
            x = torch.from_numpy(np.asarray(series, dtype=np.float32))
            if x.shape[0] < self.lookback:
                pad = self.lookback - x.shape[0]
                x = torch.cat([x[:1].repeat(pad), x], dim=0)
            else:
                x = x[-self.lookback :]
            x = x.unsqueeze(0).to(self._device)
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
        batch_size: int = 16,
        lr: float = 1e-3,
        verbose: bool = False,
    ) -> dict[str, Any]:
        if not _TORCH_AVAILABLE or self._model is None:
            _LOG.warning("torch fehlt — fit() no-op.")
            self._fitted = True  # behält das alte Verhalten (fit setzt fitted=True)
            return {"train_mse": float("inf"), "epochs": 0}

        X = torch.from_numpy(np.asarray(train_data, dtype=np.float32))
        Y = torch.from_numpy(np.asarray(targets, dtype=np.float32))
        if X.shape[1] != self.lookback:
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
        loss_fn = nn.MSELoss()

        best = float("inf")
        history: list[float] = []
        for ep in range(epochs):
            self._model.train()
            losses: list[float] = []
            for xb, yb in loader:
                xb = xb.to(self._device)
                yb = yb.to(self._device)
                optim.zero_grad()
                pred = self._model(xb)
                loss = loss_fn(pred, yb)
                loss.backward()
                optim.step()
                losses.append(float(loss.item()))
            ep_mse = float(np.mean(losses)) if losses else float("inf")
            history.append(ep_mse)
            if ep_mse < best:
                best = ep_mse
            if verbose:
                _LOG.info("M19 ep=%d train_mse=%.6f", ep, ep_mse)

        self._fitted = True
        # Marker im _weights-Dict damit Tests an _weights[...]-Zustand kommen
        self._weights["trained_mse"] = np.array([best])
        return {"train_mse": best, "epochs": epochs, "history": history}

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
                    "top_k": self.top_k,
                    "forecast_horizon": self.forecast_horizon,
                    "lookback": self.lookback,
                    "channels": self.channels,
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
            _LOG.warning("M19 load failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Compute (Inference)
    # ------------------------------------------------------------------

    def compute(self, series: np.ndarray) -> dict[str, Any]:
        series = np.asarray(series, dtype=np.float64)
        periods = self._fft_top_k_periods(series, self.top_k)

        if not self._fitted:
            return {
                "forecast": np.zeros(self.forecast_horizon),
                "detected_periods": periods,
                "forecast_direction": 0,
                "signal": 0,
                "method_id": "M19",
                "confidence": 0.0,
                "ts": time.time(),
            }

        forecast = self._forward_np(series)
        last = float(series[-1])
        delta = float(forecast[-1] - last)
        direction = int(np.sign(delta)) if abs(delta) > _EPS else 0
        std = float(np.std(series)) + _EPS
        confidence = float(np.clip(np.abs(delta) / std, 0.0, 1.0))

        return {
            "forecast": forecast,
            "detected_periods": periods,
            "forecast_direction": direction,
            "signal": direction,
            "method_id": "M19",
            "confidence": confidence,
            "ts": time.time(),
        }

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self._fitted = False
        self._weights.clear()
        if _TORCH_AVAILABLE:
            torch.manual_seed(self.seed)
            self._model = TimesNetModel(
                top_k=self.top_k,
                lookback=self.lookback,
                forecast_horizon=self.forecast_horizon,
                channels=self.channels,
            ).to(self._device)
