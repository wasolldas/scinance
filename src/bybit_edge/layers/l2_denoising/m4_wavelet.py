"""
M4 — Wavelet-Symlet-Denoising [L2]

Formeln (PRD):
    W_{j,k} = sum_n x[n] * psi*_{j,k}[n]
    Soft-Threshold: W'_{j,k} = sign(W_{j,k}) * max(|W_{j,k}| - lambda_j, 0)
    lambda_j = sigma_j * sqrt(2 * log(N))   (Donoho VisuShrink)
    Reconstruction: x_hat[n] = sum_{j,k} W'_{j,k} * psi_{j,k}[n]

Entrauscht Imbalance-Streams via Wavelet-Zerlegung mit Soft-Thresholding
der Detail-Koeffizienten. Verwendet PyWavelets wenn vorhanden, sonst
Fallback auf eigene Haar-DWT.
"""

from __future__ import annotations

import math
import time
from typing import Any

import numpy as np

from bybit_edge.config import WAVELET_LEVEL, WAVELET_MOTHER, WAVELET_WINDOW_TICKS
from bybit_edge.layers.base import BaseModule

# Versuche PyWavelets, Fallback auf Haar
try:
    import pywt

    _HAS_PYWT: bool = True
except ImportError:
    _HAS_PYWT = False


class M4WaveletDenoiser(BaseModule):
    """Wavelet-Symlet-Denoiser fuer Imbalance-Streams.

    Zerlegt das Signal via DWT, wendet Soft-Thresholding (VisuShrink)
    auf die Detail-Koeffizienten an und rekonstruiert das entrauschte Signal.
    """

    def __init__(
        self,
        wavelet: str = WAVELET_MOTHER,
        level: int = WAVELET_LEVEL,
    ) -> None:
        self._wavelet = wavelet
        self._level = level

    # ------------------------------------------------------------------
    # Haar-DWT Fallback
    # ------------------------------------------------------------------

    def _haar_dwt(
        self, signal: np.ndarray, level: int
    ) -> tuple[np.ndarray, list[np.ndarray]]:
        """Einfache Haar-DWT-Zerlegung als Fallback.

        Parameters
        ----------
        signal : np.ndarray
            1D-Input-Signal (Laenge sollte durch 2^level teilbar sein).
        level : int
            Zerlegungsstufen.

        Returns
        -------
        tuple[np.ndarray, list[np.ndarray]]
            (approximation_coeffs, [detail_coeffs_level_1, ..., detail_coeffs_level_n])
            Detail-Liste ist von feinster zu groebster Stufe.
        """
        details: list[np.ndarray] = []
        approx = signal.astype(np.float64).copy()

        for _ in range(level):
            n = len(approx)
            if n < 2:
                break
            # Pad auf gerade Laenge
            if n % 2 != 0:
                approx = np.append(approx, approx[-1])
                n += 1

            even = approx[0::2]
            odd = approx[1::2]
            new_approx = (even + odd) / math.sqrt(2.0)
            detail = (even - odd) / math.sqrt(2.0)
            details.append(detail)
            approx = new_approx

        return approx, details

    def _haar_idwt(
        self, approx: np.ndarray, details: list[np.ndarray]
    ) -> np.ndarray:
        """Inverse Haar-DWT Rekonstruktion.

        Parameters
        ----------
        approx : np.ndarray
            Approximations-Koeffizienten (groebste Stufe).
        details : list[np.ndarray]
            Detail-Koeffizienten von feinster zu groebster Stufe.

        Returns
        -------
        np.ndarray
            Rekonstruiertes Signal.
        """
        signal = approx.astype(np.float64).copy()

        for detail in reversed(details):
            n = len(detail)
            reconstructed = np.empty(2 * n, dtype=np.float64)
            reconstructed[0::2] = (signal[:n] + detail) / math.sqrt(2.0)
            reconstructed[1::2] = (signal[:n] - detail) / math.sqrt(2.0)
            signal = reconstructed

        return signal

    # ------------------------------------------------------------------
    # Thresholding
    # ------------------------------------------------------------------

    def _visushrink_threshold(self, detail_coeffs: np.ndarray) -> float:
        """Berechne VisuShrink Schwellwert nach Donoho.

        Parameters
        ----------
        detail_coeffs : np.ndarray
            Detail-Koeffizienten einer Zerlegungsstufe.

        Returns
        -------
        float
            Schwellwert lambda = sigma * sqrt(2 * log(N)).
        """
        n = len(detail_coeffs)
        if n == 0:
            return 0.0

        # MAD-Schaetzer: sigma = median(|d|) / 0.6745
        sigma = float(np.median(np.abs(detail_coeffs))) / 0.6745

        if sigma <= 0.0 or n <= 1:
            return 0.0

        threshold = sigma * math.sqrt(2.0 * math.log(n))
        return threshold

    def _soft_threshold(self, coeffs: np.ndarray, threshold: float) -> np.ndarray:
        """Soft-Thresholding: sign(c) * max(|c| - lambda, 0).

        Parameters
        ----------
        coeffs : np.ndarray
            Wavelet-Koeffizienten.
        threshold : float
            Schwellwert lambda.

        Returns
        -------
        np.ndarray
            Thresholded Koeffizienten.
        """
        return np.sign(coeffs) * np.maximum(np.abs(coeffs) - threshold, 0.0)

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, signal: np.ndarray) -> dict[str, Any]:
        """Entrausche ein 1D-Signal via Wavelet-Soft-Thresholding.

        Parameters
        ----------
        signal : np.ndarray
            1D-Input-Signal (z.B. Imbalance-Stream, 256 Ticks).

        Returns
        -------
        dict mit denoised, snr_improvement_db, method_id, signal, confidence, ts.
        """
        now = time.time()
        signal = np.asarray(signal, dtype=np.float64)
        original_len = len(signal)

        # Kurze Signale: keine Zerlegung moeglich
        min_length = 2 ** self._level
        if original_len < min_length:
            return {
                "denoised": signal.copy(),
                "snr_improvement_db": 0.0,
                "method_id": "M4",
                "signal": 0,
                "confidence": 0.0,
                "ts": now,
            }

        # DWT
        if _HAS_PYWT:
            coeffs = pywt.wavedec(signal, self._wavelet, level=self._level)
            # coeffs[0] = Approx, coeffs[1:] = Details (groebste zuerst)
            thresholded = [coeffs[0]]  # Approximation bleibt
            for detail in coeffs[1:]:
                lam = self._visushrink_threshold(detail)
                thresholded.append(self._soft_threshold(detail, lam))
            denoised = pywt.waverec(thresholded, self._wavelet)
            # pywt kann 1 Sample zu lang rekonstruieren
            denoised = denoised[:original_len]
        else:
            # Haar-Fallback
            effective_level = min(
                self._level,
                int(math.log2(max(original_len, 1))),
            )
            approx, details = self._haar_dwt(signal, effective_level)
            thresholded_details: list[np.ndarray] = []
            for detail in details:
                lam = self._visushrink_threshold(detail)
                thresholded_details.append(self._soft_threshold(detail, lam))
            denoised = self._haar_idwt(approx, thresholded_details)
            denoised = denoised[:original_len]

        # SNR-Verbesserung berechnen
        noise = signal - denoised
        signal_power = float(np.mean(signal ** 2))
        noise_power = float(np.mean(noise ** 2))

        if noise_power > 0.0 and signal_power > 0.0:
            snr_before = signal_power / (signal_power + noise_power)
            snr_after = signal_power / noise_power
            # dB Verbesserung
            snr_improvement_db = 10.0 * math.log10(max(snr_after / max(snr_before, 1e-12), 1e-12))
        else:
            snr_improvement_db = 0.0

        # Confidence: basiert auf SNR-Verbesserung (skaliert)
        confidence = min(max(snr_improvement_db / 20.0, 0.0), 1.0)

        return {
            "denoised": denoised,
            "snr_improvement_db": snr_improvement_db,
            "method_id": "M4",
            "signal": 0,  # Preprocessing-Modul, kein Trading-Signal
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prueft ob Wavelet-Parameter sinnvoll konfiguriert sind."""
        return self._level >= 1 and WAVELET_WINDOW_TICKS >= 2 ** self._level

    def reset(self) -> None:
        """Kein interner State — nichts zu resetten."""
