"""
M20 — MOMENT Foundation Model (Zero-Shot) [L4]

Echte momentfm-Integration als Optional:
    * Wenn ``momentfm`` installiert ist: lädt ``AutonLab/MOMENT-1-base|large``
      via ``MOMENTPipeline.from_pretrained`` und nutzt es als Forecaster.
    * Wenn ``peft`` installiert ist: LoRA-Fine-Tune möglich.
    * Sonst: RevIN + EMA-Drift-Fallback (wie bisher).

Interface-Garantien (unverändert ggü. der numpy-Stub):
    * compute(series) -> dict mit Keys forecast, forecast_direction,
      is_zero_shot, model_loaded, signal, method_id, confidence, ts.
    * load_pretrained(model_path) -> bool: laden via np.load (Test-Vertrag).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import numpy as np

from bybit_edge._legacy_v1.layers.base import BaseModule

_EPS: float = 1e-12
_LOG = logging.getLogger(__name__)

try:
    import torch

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

try:
    from momentfm import MOMENTPipeline  # type: ignore[import-not-found]

    _MOMENTFM_AVAILABLE = True
except Exception:  # pragma: no cover - nur wenn momentfm installiert ist
    MOMENTPipeline = None  # type: ignore[assignment]
    _MOMENTFM_AVAILABLE = False

try:
    from peft import LoraConfig, get_peft_model  # type: ignore[import-not-found]

    _PEFT_AVAILABLE = True
except Exception:  # pragma: no cover
    LoraConfig = None  # type: ignore[assignment]
    get_peft_model = None  # type: ignore[assignment]
    _PEFT_AVAILABLE = False


class M20MOMENT(BaseModule):
    """MOMENT Foundation Model Wrapper mit RevIN + EMA-Fallback."""

    def __init__(
        self,
        forecast_horizon: int = 12,
        patch_length: int = 16,
        ema_span: int = 20,
        device: str = "auto",
    ) -> None:
        self.forecast_horizon: int = forecast_horizon
        self.patch_length: int = patch_length
        self.ema_span: int = ema_span

        self._fitted: bool = False
        self._model_loaded: bool = False
        self._weights: dict[str, np.ndarray] = {}
        self._device = self._resolve_device(device)

        # Echtes MOMENT-Modell (falls geladen)
        self._moment_model: Any = None
        self._moment_size: str | None = None
        # LoRA-Adapter-Tag
        self._use_lora: bool = False

    @staticmethod
    def _resolve_device(device: str) -> str:
        if not _TORCH_AVAILABLE:
            return "cpu"
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    # ------------------------------------------------------------------
    # RevIN
    # ------------------------------------------------------------------

    @staticmethod
    def _revin_normalize(x: np.ndarray) -> tuple[np.ndarray, float, float]:
        mu = float(np.mean(x))
        sigma = float(np.std(x) + _EPS)
        return (x - mu) / sigma, mu, sigma

    @staticmethod
    def _revin_denormalize(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
        return x * sigma + mu

    # ------------------------------------------------------------------
    # Fallback-Forecast (EMA + Drift)
    # ------------------------------------------------------------------

    def _fallback_forecast(self, series: np.ndarray, horizon: int) -> np.ndarray:
        alpha = 2.0 / (self.ema_span + 1)
        ema = series[0]
        for val in series[1:]:
            ema = alpha * val + (1.0 - alpha) * ema
        n_drift = min(10, len(series) - 1)
        if n_drift < 1:
            drift = 0.0
        else:
            returns = np.diff(series[-n_drift - 1 :])
            drift = float(np.mean(returns))
        return np.array([ema + drift * (i + 1) for i in range(horizon)])

    # ------------------------------------------------------------------
    # Pretrained-Loading (Test-Vertrag: np.load auf .npz)
    # ------------------------------------------------------------------

    def load_pretrained(
        self,
        model_path: str,
        model_size: str = "base",
    ) -> bool:
        """Lädt Pretrained-Weights.

        Zwei Modi:
            (a) Wenn ``model_path`` eine existierende .npz-Datei ist
                (Test-Vertrag der numpy-Stub), wird sie via ``np.load``
                gelesen.
            (b) Wenn ``momentfm`` installiert ist und ``model_path`` ein
                HF-Repo (z. B. ``AutonLab/MOMENT-1-base``) ist, wird das
                echte MOMENT geladen.

        Parameters
        ----------
        model_size : "base" | "large"
            Steuert die Größe des MOMENT-Modells. "large" ist auf 16 GB
            VRAM nur in FP16-Inferenz nutzbar — warnen.
        """
        # (a) Lokaler .npz-Pfad — bewahrt das Test-Verhalten
        if os.path.isfile(model_path):
            try:
                data = np.load(model_path, allow_pickle=True)
                self._weights = {k: data[k] for k in data.files}
                self._fitted = True
                self._model_loaded = True
                return True
            except Exception as exc:
                _LOG.warning("M20 npz-load failed: %s", exc)
                return False

        # (b) momentfm + HuggingFace-Repo
        if not _MOMENTFM_AVAILABLE:
            _LOG.warning(
                "M20: weder .npz vorhanden noch momentfm installiert "
                "(%s).",
                model_path,
            )
            return False

        if model_size == "large":
            _LOG.warning(
                "M20: MOMENT-1-large (~341M Params) ist auf 16 GB VRAM "
                "NICHT trainierbar — Inferenz nur mit FP16 möglich."
            )

        try:
            model_kwargs = {
                "task_name": "forecasting",
                "forecast_horizon": self.forecast_horizon,
            }
            self._moment_model = MOMENTPipeline.from_pretrained(
                model_path, model_kwargs=model_kwargs
            )
            if _TORCH_AVAILABLE:
                self._moment_model.to(self._device)
            self._moment_size = model_size
            self._fitted = True
            self._model_loaded = True
            return True
        except Exception as exc:  # pragma: no cover - braucht echtes HF-Modell
            _LOG.warning("M20 momentfm load failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # LoRA Fine-Tune (optional)
    # ------------------------------------------------------------------

    def enable_lora(
        self,
        r: int = 8,
        lora_alpha: int = 16,
        target_modules: list[str] | None = None,
    ) -> bool:
        """Aktiviere LoRA-Adapter auf dem echten MOMENT-Modell.

        Returns
        -------
        True wenn LoRA erfolgreich angeschaltet wurde, sonst False.
        """
        if self._moment_model is None:
            _LOG.warning("M20: kein MOMENT-Modell geladen — enable_lora skipped.")
            return False
        if not _PEFT_AVAILABLE:
            _LOG.warning("M20: peft fehlt — LoRA übersprungen.")
            return False
        try:
            cfg = LoraConfig(
                r=r,
                lora_alpha=lora_alpha,
                target_modules=target_modules or ["q_proj", "v_proj"],
                bias="none",
            )
            self._moment_model = get_peft_model(self._moment_model, cfg)
            self._use_lora = True
            return True
        except Exception as exc:  # pragma: no cover
            _LOG.warning("M20 LoRA setup failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Save / Load des State-Dict (für trainierte Adapter)
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        if self._moment_model is None or not _TORCH_AVAILABLE:
            raise RuntimeError("M20: kein torch-Modell aktiv — save unmöglich.")
        torch.save(
            {
                "state_dict": self._moment_model.state_dict(),
                "model_size": self._moment_size,
                "use_lora": self._use_lora,
                "forecast_horizon": self.forecast_horizon,
            },
            path,
        )

    # ------------------------------------------------------------------
    # MOMENT-Inferenz (echtes Modell)
    # ------------------------------------------------------------------

    def _moment_forecast(self, series: np.ndarray) -> np.ndarray:
        """Echte MOMENT-Inferenz, wenn das Modell geladen ist."""
        if self._moment_model is None or not _TORCH_AVAILABLE:
            return self._fallback_forecast(series, self.forecast_horizon)

        # MOMENT erwartet (B, C, L)
        x = torch.from_numpy(np.asarray(series, dtype=np.float32))
        x = x.unsqueeze(0).unsqueeze(0).to(self._device)  # (1,1,L)
        self._moment_model.eval()
        with torch.no_grad():
            out = self._moment_model(x_enc=x)
            # MOMENTPipeline.forward liefert ein Output-Objekt mit .forecast
            if hasattr(out, "forecast"):
                fc = out.forecast.squeeze().cpu().numpy().astype(np.float64)
            else:
                fc = np.asarray(out).squeeze().astype(np.float64)
        # Sicherstellen dass forecast_horizon-Länge
        fc = fc.reshape(-1)[: self.forecast_horizon]
        if len(fc) < self.forecast_horizon:
            pad = np.repeat(fc[-1] if len(fc) else 0.0, self.forecast_horizon - len(fc))
            fc = np.concatenate([fc, pad])
        return fc

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def compute(self, series: np.ndarray) -> dict[str, Any]:
        series = np.asarray(series, dtype=np.float64)
        x_norm, mu, sigma = self._revin_normalize(series)

        if self._fitted and self._model_loaded and self._moment_model is not None:
            forecast_norm = self._moment_forecast(x_norm)
            is_zero_shot = not self._use_lora
        else:
            forecast_norm = self._fallback_forecast(x_norm, self.forecast_horizon)
            is_zero_shot = True

        forecast = self._revin_denormalize(forecast_norm, mu, sigma)
        direction = int(np.sign(forecast[-1] - series[-1]))
        std = float(np.std(series)) + _EPS
        confidence = float(np.clip(np.abs(forecast[-1] - series[-1]) / std, 0.0, 1.0))

        return {
            "forecast": forecast,
            "forecast_direction": direction,
            "is_zero_shot": is_zero_shot,
            "model_loaded": self._model_loaded,
            "signal": direction,
            "method_id": "M20",
            "confidence": confidence,
            "ts": time.time(),
        }

    def reset(self) -> None:
        self._fitted = False
        self._model_loaded = False
        self._weights.clear()
        self._moment_model = None
        self._moment_size = None
        self._use_lora = False
