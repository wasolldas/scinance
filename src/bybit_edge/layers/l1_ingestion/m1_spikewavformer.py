"""
M1 — SpikeWavformer Event-Driven Ingestion [L1] [Moonshot]

CPU-basiertes Leaky Integrate-and-Fire (LIF) Neuron-Modell.

Drei Channels (oi_delta, liq_volume, imbalance) werden jeweils durch ein
LIF-Neuron verarbeitet. Ein System-Spike (Anomalie-Trigger) wird ausgeloest
wenn mindestens 2 von 3 Channels gleichzeitig feuern.

Formeln:
    V_m(t+1) = alpha * V_m(t) + I(t)
    Spike wenn V_m >= V_th, dann V_m := V_reset
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from bybit_edge.layers.base import BaseModule

_CHANNELS: tuple[str, ...] = ("oi_delta", "liq_volume", "imbalance")
_SPIKE_HISTORY_MAXLEN: int = 1000
_ROLLING_STATS_MAXLEN: int = 500
_MIN_SAMPLES_NORM: int = 10
_SPIKE_QUORUM: int = 2  # mindestens 2 von 3 Channels muessen feuern


class M1SpikeWavformer(BaseModule):
    """Leaky Integrate-and-Fire Neuron-Netzwerk fuer Anomalie-Detektion.

    Drei unabhaengige LIF-Neuronen ueberwachen OI-Delta, Liquidations-Volumen
    und Order-Imbalance. Ein gleichzeitiges Feuern von mindestens 2 Channels
    signalisiert eine potenzielle Marktanomalie.
    """

    def __init__(
        self,
        alpha: float = 0.9,
        v_threshold: float = 1.0,
        v_reset: float = 0.0,
    ) -> None:
        self._alpha: float = alpha
        self._v_threshold: float = v_threshold
        self._v_reset: float = v_reset

        # Membranpotentiale pro Channel
        self._membrane_potentials: dict[str, float] = {ch: 0.0 for ch in _CHANNELS}

        # Spike-History: (ts, channel_spikes_dict, system_spike_bool)
        self._spike_history: deque[tuple[float, dict[str, bool], bool]] = deque(
            maxlen=_SPIKE_HISTORY_MAXLEN
        )

        # Rolling Stats fuer z-Score-Normalisierung pro Channel
        self._rolling_values: dict[str, deque[float]] = {
            ch: deque(maxlen=_ROLLING_STATS_MAXLEN) for ch in _CHANNELS
        }

    # ------------------------------------------------------------------
    # LIF Step
    # ------------------------------------------------------------------

    def _lif_step(self, channel: str, input_current: float) -> bool:
        """Fuehrt einen LIF-Zeitschritt fuer den angegebenen Channel aus.

        Returns True wenn das Neuron feuert (Spike).
        """
        v_m = self._alpha * self._membrane_potentials[channel] + input_current
        self._membrane_potentials[channel] = v_m

        if v_m >= self._v_threshold:
            self._membrane_potentials[channel] = self._v_reset
            return True
        return False

    # ------------------------------------------------------------------
    # Normalisierung
    # ------------------------------------------------------------------

    def _normalize_input(self, value: float, channel: str) -> float:
        """z-Score-Normalisierung gegen rolling Statistiken.

        Gibt den z-Score zurueck, oder den Rohwert falls zu wenig History.
        """
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
    # Hauptberechnung
    # ------------------------------------------------------------------

    def compute(  # type: ignore[override]
        self,
        oi_delta: float = 0.0,
        liq_volume: float = 0.0,
        imbalance: float = 0.0,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """Verarbeite neue Marktdaten durch die 3 LIF-Neuronen.

        Parameters
        ----------
        oi_delta : float
            Aenderung im Open Interest.
        liq_volume : float
            Liquidationsvolumen.
        imbalance : float
            Orderbook-Imbalance.
        ts : float | None
            Zeitstempel; falls None wird time.time() verwendet.

        Returns
        -------
        dict mit spike, channel_spikes, membrane_potentials, signal,
        method_id, confidence, ts.
        """
        if ts is None:
            ts = time.time()

        raw_inputs: dict[str, float] = {
            "oi_delta": oi_delta,
            "liq_volume": liq_volume,
            "imbalance": imbalance,
        }

        # Normalisierung + LIF-Step pro Channel
        channel_spikes: dict[str, bool] = {}
        for ch in _CHANNELS:
            normalized = self._normalize_input(raw_inputs[ch], ch)
            channel_spikes[ch] = self._lif_step(ch, normalized)

        # System-Spike: mindestens 2 von 3 Channels feuern
        n_firing = sum(1 for v in channel_spikes.values() if v)
        spike = n_firing >= _SPIKE_QUORUM

        # History speichern
        self._spike_history.append((ts, dict(channel_spikes), spike))

        # Confidence: proportional zur Anzahl feuernder Channels
        confidence = n_firing / len(_CHANNELS)

        # Signal: 1 bei Anomalie, 0 sonst
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

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Prueft LIF-Parameter auf Plausibilitaet."""
        return (
            0.0 < self._alpha < 1.0
            and self._v_threshold > 0.0
            and self._v_reset < self._v_threshold
        )

    def reset(self) -> None:
        """Setzt internen State vollstaendig zurueck."""
        for ch in _CHANNELS:
            self._membrane_potentials[ch] = 0.0
            self._rolling_values[ch].clear()
        self._spike_history.clear()
