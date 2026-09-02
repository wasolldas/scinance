"""
M1 — SpikeWavformer Event-Driven Ingestion [L1] [Moonshot]

Spiking Neural Network mit Leaky Integrate-and-Fire (LIF) Neuronen.

Pipeline:
    1. 3 Input-Channels (oi_delta, liq_volume, imbalance).
    2. Online z-Score-Normalisierung über rolling Window.
    3. Optional DWT-Preprocessing (sym6, Level 4) via PyWavelets, wenn ein
       Burst-Window verfügbar ist (online-Schritt nutzt nur den Skalar).
    4. PyTorch-LIF-Layer-Stack (3 Layers, ~1 M Parameter) mit
       Surrogate-Gradient (Straight-Through Estimator) für Training.
    5. System-Spike: mindestens 2 von 3 Channels feuern gleichzeitig.

Interface-Garantien (unverändert ggü. der numpy-Vorgänger-Stub):
    * compute(oi_delta, liq_volume, imbalance, ts) -> dict mit Keys:
        spike, channel_spikes, membrane_potentials, signal,
        method_id, confidence, ts.
    * Member ``_membrane_potentials``, ``_spike_history``,
      ``_rolling_values`` bleiben in Form/Verhalten erhalten — die
      bestehenden Tests greifen direkt darauf zu.

PyTorch ist optional: ohne torch läuft das Online-Verhalten exakt wie
die numpy-Stub. ``snnTorch`` ist optional bessere LIF-Implementierung;
wenn fehlend, eigene LIF + Surrogate.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

from bybit_edge._legacy_v1.layers.base import BaseModule

_CHANNELS: tuple[str, ...] = ("oi_delta", "liq_volume", "imbalance")
_SPIKE_HISTORY_MAXLEN: int = 1000
_ROLLING_STATS_MAXLEN: int = 500
_MIN_SAMPLES_NORM: int = 10
_SPIKE_QUORUM: int = 2

_LOG = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

try:
    import snntorch as snn  # type: ignore[import-not-found]
    from snntorch import surrogate  # type: ignore[import-not-found]

    _SNNTORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    snn = None  # type: ignore[assignment]
    surrogate = None  # type: ignore[assignment]
    _SNNTORCH_AVAILABLE = False

try:
    import pywt  # type: ignore[import-not-found]

    _PYWT_AVAILABLE = True
except Exception:  # pragma: no cover
    pywt = None  # type: ignore[assignment]
    _PYWT_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Surrogate-Gradient + PyTorch-LIF
# ══════════════════════════════════════════════════════════════════════


if _TORCH_AVAILABLE:

    class _SurrogateSpike(torch.autograd.Function):
        """Surrogate-Gradient (sigmoid-derivative) für die Heaviside-Spike.

        Forward: 1 if V >= V_th else 0
        Backward: dV ≈ sigmoid'(V - V_th)
        """

        @staticmethod
        def forward(ctx, v: torch.Tensor, v_th: float) -> torch.Tensor:
            ctx.save_for_backward(v)
            ctx.v_th = v_th
            return (v >= v_th).float()

        @staticmethod
        def backward(ctx, grad_output: torch.Tensor):  # type: ignore[override]
            (v,) = ctx.saved_tensors
            v_th = ctx.v_th
            sig = torch.sigmoid(4.0 * (v - v_th))
            grad = 4.0 * sig * (1.0 - sig) * grad_output
            return grad, None

    class _LIFLayer(nn.Module):
        """LIF-Layer mit gelerntem Linear-Input + Surrogate-Gradient.

        Zeitdiskret:
            V_m(t+1) = alpha * V_m(t) * (1 - s(t)) + W * x(t) + b
        """

        def __init__(
            self,
            in_features: int,
            out_features: int,
            alpha: float = 0.9,
            v_threshold: float = 1.0,
        ) -> None:
            super().__init__()
            self.alpha = alpha
            self.v_threshold = v_threshold
            self.linear = nn.Linear(in_features, out_features)

        def init_state(
            self, batch_size: int, device: torch.device
        ) -> torch.Tensor:
            return torch.zeros(batch_size, self.linear.out_features, device=device)

        def forward(
            self, x: torch.Tensor, v_prev: torch.Tensor
        ) -> tuple[torch.Tensor, torch.Tensor]:
            i = self.linear(x)
            v = self.alpha * v_prev + i
            spike = _SurrogateSpike.apply(v, self.v_threshold)
            v_next = v * (1.0 - spike)  # Reset wenn Spike
            return spike, v_next

    class SpikeWavformerNet(nn.Module):
        """3-Layer-LIF-Encoder + Spike/No-Spike-Klassifikationskopf.

        Parameter-Budget (Default):
            Layer1: 3 -> 256 + bias = 1024
            Layer2: 256 -> 512      = 131,584
            Layer3: 512 -> 1024     = 525,312
            Head:   1024 -> 2       = 2050
            => ~660k Params. Mit ``hidden=(512,1024,1024)`` ~1 M.
        """

        def __init__(
            self,
            in_features: int = 3,
            hidden: tuple[int, ...] = (256, 512, 1024),
            n_classes: int = 2,
            alpha: float = 0.9,
            v_threshold: float = 1.0,
            n_steps: int = 8,
        ) -> None:
            super().__init__()
            sizes = (in_features,) + hidden
            self.layers = nn.ModuleList(
                [
                    _LIFLayer(sizes[i], sizes[i + 1], alpha=alpha, v_threshold=v_threshold)
                    for i in range(len(sizes) - 1)
                ]
            )
            self.head = nn.Linear(hidden[-1], n_classes)
            self.n_steps = n_steps

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Forward über n_steps Time-Steps.

            x : (B, in_features)  — wird über n_steps wiederholt.
            return : (B, n_classes) — Mean über die n_steps.
            """
            B = x.shape[0]
            device = x.device
            v_states = [layer.init_state(B, device) for layer in self.layers]
            logits_acc = torch.zeros(B, self.head.out_features, device=device)
            for _t in range(self.n_steps):
                h = x
                for i, layer in enumerate(self.layers):
                    h, v_states[i] = layer(h, v_states[i])
                logits_acc = logits_acc + self.head(h)
            return logits_acc / self.n_steps


# ══════════════════════════════════════════════════════════════════════
# Modul-Wrapper
# ══════════════════════════════════════════════════════════════════════


class M1SpikeWavformer(BaseModule):
    """SpikeWavformer mit echtem PyTorch-LIF-Netz + DWT-Preprocessing.

    Im Online-Schritt (``compute``) bleibt das Verhalten exakt wie die
    numpy-Stub: simples LIF pro Channel, Quorum von 2-aus-3. Das PyTorch-
    Netz wird beim Training und beim Burst-Forward (``forward_window``)
    verwendet.
    """

    def __init__(
        self,
        alpha: float = 0.9,
        v_threshold: float = 1.0,
        v_reset: float = 0.0,
        hidden: tuple[int, ...] = (256, 512, 1024),
        n_steps: int = 8,
        device: str = "auto",
        seed: int = 42,
    ) -> None:
        self._alpha: float = alpha
        self._v_threshold: float = v_threshold
        self._v_reset: float = v_reset
        self.hidden = hidden
        self.n_steps = n_steps
        self.seed = seed

        # Online-State (Test-Vertrag!)
        self._membrane_potentials: dict[str, float] = {ch: 0.0 for ch in _CHANNELS}
        self._spike_history: deque[tuple[float, dict[str, bool], bool]] = deque(
            maxlen=_SPIKE_HISTORY_MAXLEN
        )
        self._rolling_values: dict[str, deque[float]] = {
            ch: deque(maxlen=_ROLLING_STATS_MAXLEN) for ch in _CHANNELS
        }

        # PyTorch-Netz (für Burst-Forward + Training)
        self._device = self._resolve_device(device)
        self._fitted: bool = False
        if _TORCH_AVAILABLE:
            torch.manual_seed(seed)
            self._net: Any = SpikeWavformerNet(
                in_features=len(_CHANNELS),
                hidden=hidden,
                n_classes=2,
                alpha=alpha,
                v_threshold=v_threshold,
                n_steps=n_steps,
            ).to(self._device)
        else:
            self._net = None
            _LOG.warning("torch fehlt — M1 läuft im numpy-only-Modus.")

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
        if self._net is None:
            return 0
        return int(sum(p.numel() for p in self._net.parameters() if p.requires_grad))

    # ------------------------------------------------------------------
    # LIF online (Test-Vertrag — unverändert)
    # ------------------------------------------------------------------

    def _lif_step(self, channel: str, input_current: float) -> bool:
        v_m = self._alpha * self._membrane_potentials[channel] + input_current
        self._membrane_potentials[channel] = v_m
        if v_m >= self._v_threshold:
            self._membrane_potentials[channel] = self._v_reset
            return True
        return False

    def _normalize_input(self, value: float, channel: str) -> float:
        self._rolling_values[channel].append(value)
        if len(self._rolling_values[channel]) < _MIN_SAMPLES_NORM:
            return value
        vals = list(self._rolling_values[channel])
        n = len(vals)
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        std = var ** 0.5
        if std < 1e-12:
            return 0.0
        return (value - mean) / std

    # ------------------------------------------------------------------
    # Optional: DWT-Preprocessing für Burst-Windows
    # ------------------------------------------------------------------

    @staticmethod
    def dwt_features(window: Any, wavelet: str = "sym6", level: int = 4) -> Any:
        """Liefert konkatenierte DWT-Detail-Koeffizienten.

        Parameters
        ----------
        window : 1D array-like (per channel)
        """
        if not _PYWT_AVAILABLE:
            import numpy as np

            return np.asarray(window, dtype=float)
        import numpy as np

        arr = np.asarray(window, dtype=float)
        max_lvl = pywt.dwt_max_level(len(arr), pywt.Wavelet(wavelet).dec_len)
        eff_lvl = max(1, min(level, max_lvl))
        coeffs = pywt.wavedec(arr, wavelet, level=eff_lvl)
        return np.concatenate([c.ravel() for c in coeffs])

    # ------------------------------------------------------------------
    # PyTorch-Burst-Forward + Training
    # ------------------------------------------------------------------

    def forward_window(self, x: Any) -> Any:
        """PyTorch-Forward auf einem Batch von Window-Features.

        Parameters
        ----------
        x : np.ndarray oder torch.Tensor, shape (B, in_features)
        """
        if self._net is None:
            raise RuntimeError("torch fehlt — forward_window unmöglich.")
        import numpy as np

        if isinstance(x, np.ndarray):
            x_t = torch.from_numpy(np.asarray(x, dtype=np.float32))
        else:
            x_t = x.float()
        x_t = x_t.to(self._device)
        self._net.eval()
        with torch.no_grad():
            out = self._net(x_t)
        return out.cpu().numpy()

    def fit(
        self,
        features: Any,
        labels: Any,
        epochs: int = 5,
        batch_size: int = 64,
        lr: float = 1e-3,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Train Spike/No-Spike-Klassifikation mit CrossEntropy + Adam.

        Parameters
        ----------
        features : (N, in_features) — z.B. normalisierte Channel-Werte
                   oder DWT-Features (in_features muss matchen).
        labels   : (N,)             — 0/1 (No-Spike/Spike).
        """
        if not _TORCH_AVAILABLE or self._net is None:
            _LOG.warning("torch fehlt — fit() no-op.")
            return {"train_loss": float("inf"), "epochs": 0}

        import numpy as np
        from torch.utils.data import DataLoader, TensorDataset

        X = torch.from_numpy(np.asarray(features, dtype=np.float32))
        Y = torch.from_numpy(np.asarray(labels, dtype=np.int64))

        ds = TensorDataset(X, Y)
        loader = DataLoader(ds, batch_size=batch_size, shuffle=True)
        optim = torch.optim.Adam(self._net.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss()

        history: list[float] = []
        best = float("inf")
        for ep in range(epochs):
            self._net.train()
            losses: list[float] = []
            for xb, yb in loader:
                xb = xb.to(self._device)
                yb = yb.to(self._device)
                optim.zero_grad()
                logits = self._net(xb)
                loss = loss_fn(logits, yb)
                loss.backward()
                optim.step()
                losses.append(float(loss.item()))
            ep_loss = float(sum(losses) / max(1, len(losses)))
            history.append(ep_loss)
            if ep_loss < best:
                best = ep_loss
            if verbose:
                _LOG.info("M1 ep=%d loss=%.6f", ep, ep_loss)

        self._fitted = True
        return {"train_loss": best, "epochs": epochs, "history": history}

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        if self._net is None or not _TORCH_AVAILABLE:
            raise RuntimeError("torch fehlt — save unmöglich.")
        torch.save(
            {
                "state_dict": self._net.state_dict(),
                "config": {
                    "hidden": list(self.hidden),
                    "alpha": self._alpha,
                    "v_threshold": self._v_threshold,
                    "n_steps": self.n_steps,
                },
                "fitted": self._fitted,
            },
            path,
        )

    def load(self, path: str) -> bool:
        if self._net is None or not _TORCH_AVAILABLE:
            return False
        try:
            ckpt = torch.load(path, map_location=self._device, weights_only=False)
            self._net.load_state_dict(ckpt["state_dict"])
            self._fitted = bool(ckpt.get("fitted", True))
            return True
        except Exception as exc:  # pragma: no cover
            _LOG.warning("M1 load failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Compute (online, Test-Vertrag)
    # ------------------------------------------------------------------

    def compute(  # type: ignore[override]
        self,
        oi_delta: float = 0.0,
        liq_volume: float = 0.0,
        imbalance: float = 0.0,
        ts: float | None = None,
    ) -> dict[str, Any]:
        if ts is None:
            ts = time.time()
        raw_inputs: dict[str, float] = {
            "oi_delta": oi_delta,
            "liq_volume": liq_volume,
            "imbalance": imbalance,
        }
        channel_spikes: dict[str, bool] = {}
        for ch in _CHANNELS:
            normalized = self._normalize_input(raw_inputs[ch], ch)
            channel_spikes[ch] = self._lif_step(ch, normalized)
        n_firing = sum(1 for v in channel_spikes.values() if v)
        spike = n_firing >= _SPIKE_QUORUM
        self._spike_history.append((ts, dict(channel_spikes), spike))
        confidence = n_firing / len(_CHANNELS)
        signal: int = 1 if spike else 0
        return {
            "spike": spike,
            "channel_spikes": channel_spikes,
            "membrane_potentials": dict(self._membrane_potentials),
            "signal": signal,
            "method_id": "M1",
            "confidence": confidence,
            "ts": ts,
        }

    def validate(self) -> bool:
        return (
            0.0 < self._alpha < 1.0
            and self._v_threshold > 0.0
            and self._v_reset < self._v_threshold
        )

    def reset(self) -> None:
        for ch in _CHANNELS:
            self._membrane_potentials[ch] = 0.0
            self._rolling_values[ch].clear()
        self._spike_history.clear()
        self._fitted = False
        if _TORCH_AVAILABLE and self._net is not None:
            torch.manual_seed(self.seed)
            self._net = SpikeWavformerNet(
                in_features=len(_CHANNELS),
                hidden=self.hidden,
                n_classes=2,
                alpha=self._alpha,
                v_threshold=self._v_threshold,
                n_steps=self.n_steps,
            ).to(self._device)
