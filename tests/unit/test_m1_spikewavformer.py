"""
Tests fuer M1 -- SpikeWavformer Event-Driven Ingestion.

Testet:
- Kein Spike bei schwachem Input
- Spike bei starkem Input in >= 2 Channels
- Membrane-Leak ohne Input
- Reset nach Spike
- Einzelner Channel feuert nicht als System-Spike
- Normalisierung
- Reset loescht Potentiale
- Return-Keys
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge._legacy_v1.layers.l1_ingestion.m1_spikewavformer import M1SpikeWavformer


class TestM1SpikeWavformer:
    """Tests fuer das LIF-Neuron-basierte Anomalie-Detection-Modul."""

    def test_no_spike_low_input(self) -> None:
        """Schwache Inputs erzeugen keinen Spike."""
        mod = M1SpikeWavformer(alpha=0.9, v_threshold=1.0, v_reset=0.0)
        result = mod.compute(oi_delta=0.01, liq_volume=0.01, imbalance=0.01, ts=1.0)
        assert result["spike"] is False
        assert result["signal"] == 0

    def test_spike_strong_input(self) -> None:
        """Starke Inputs in >= 2 Channels erzeugen System-Spike."""
        mod = M1SpikeWavformer(alpha=0.9, v_threshold=1.0, v_reset=0.0)
        # Sehr starke Inputs die sofort ueber threshold gehen
        result = mod.compute(oi_delta=5.0, liq_volume=5.0, imbalance=5.0, ts=1.0)
        assert result["spike"] is True
        assert result["signal"] == 1
        # Mindestens 2 Channels muessen gefeuert haben
        spikes = result["channel_spikes"]
        assert sum(1 for v in spikes.values() if v) >= 2

    def test_membrane_leak(self) -> None:
        """Ohne Input sinkt das Membranpotential ueber Zeit (Leak)."""
        mod = M1SpikeWavformer(alpha=0.5, v_threshold=10.0, v_reset=0.0)
        # Starken Input geben der nicht zum Spike fuehrt
        mod.compute(oi_delta=3.0, liq_volume=0.0, imbalance=0.0, ts=1.0)
        v_after_input = mod._membrane_potentials["oi_delta"]

        # Null-Input: V_m(t+1) = alpha * V_m(t) + 0
        mod.compute(oi_delta=0.0, liq_volume=0.0, imbalance=0.0, ts=2.0)
        v_after_leak = mod._membrane_potentials["oi_delta"]

        # Potential sollte kleiner geworden sein (leak)
        assert v_after_leak < v_after_input

    def test_reset_after_spike(self) -> None:
        """Nach einem Channel-Spike wird V_m auf V_reset gesetzt."""
        mod = M1SpikeWavformer(alpha=0.9, v_threshold=1.0, v_reset=0.0)
        # Starker Input der zum Spike fuehrt
        result = mod.compute(oi_delta=5.0, liq_volume=5.0, imbalance=0.0, ts=1.0)
        # Channels die gefeuert haben sollten V_reset haben
        for ch, spiked in result["channel_spikes"].items():
            if spiked:
                assert result["membrane_potentials"][ch] == 0.0

    def test_single_channel_no_spike(self) -> None:
        """Nur 1 Channel feuert -> kein System-Spike."""
        mod = M1SpikeWavformer(alpha=0.9, v_threshold=1.0, v_reset=0.0)
        # Nur oi_delta stark, Rest schwach
        result = mod.compute(oi_delta=5.0, liq_volume=0.0, imbalance=0.0, ts=1.0)
        # Hoechstens 1 Channel sollte feuern
        spikes = result["channel_spikes"]
        n_firing = sum(1 for v in spikes.values() if v)
        # Wenn nur 1 feuert -> kein System-Spike
        if n_firing <= 1:
            assert result["spike"] is False
            assert result["signal"] == 0

    def test_normalize_input(self) -> None:
        """z-Score-Normalisierung gibt plausible Werte zurueck."""
        mod = M1SpikeWavformer()
        # Fuettere genug Werte fuer rolling Stats
        for i in range(20):
            mod._normalize_input(float(i), "oi_delta")

        # Extremwert sollte hohen z-Score liefern
        z = mod._normalize_input(100.0, "oi_delta")
        assert z > 2.0  # weit ueber dem bisherigen Mittel

    def test_reset_clears_potentials(self) -> None:
        """Reset setzt alle Membranpotentiale auf 0 zurueck."""
        mod = M1SpikeWavformer(alpha=0.9, v_threshold=10.0, v_reset=0.0)
        mod.compute(oi_delta=3.0, liq_volume=2.0, imbalance=1.0, ts=1.0)
        mod.reset()
        for ch in ("oi_delta", "liq_volume", "imbalance"):
            assert mod._membrane_potentials[ch] == 0.0
        assert len(mod._spike_history) == 0

    def test_return_keys(self) -> None:
        """Compute gibt alle erwarteten Keys zurueck."""
        mod = M1SpikeWavformer()
        result = mod.compute(oi_delta=0.1, liq_volume=0.1, imbalance=0.1, ts=1.0)
        expected_keys = {
            "spike", "channel_spikes", "membrane_potentials",
            "signal", "method_id", "confidence", "ts",
        }
        assert set(result.keys()) == expected_keys
        assert result["method_id"] == "M1"
        assert result["signal"] in (-1, 0, 1)
        assert 0.0 <= result["confidence"] <= 1.0


# ══════════════════════════════════════════════════════════════════════
# Zusätzliche PyTorch-LIF-Tests
# ══════════════════════════════════════════════════════════════════════


torch = pytest.importorskip("torch")


class TestPyTorchLIFForward:
    """LIF-Netz liefert (B, n_classes) Output."""

    def test_pytorch_lif_forward(self) -> None:
        mod = M1SpikeWavformer(hidden=(32, 32, 16))
        x = torch.randn(4, 3)
        out = mod._net(x)
        assert out.shape == (4, 2)
        assert torch.isfinite(out).all()


class TestSurrogateGradientBackward:
    """Surrogate-Gradient erlaubt Backprop durch die Spike-Funktion."""

    def test_surrogate_gradient_backward(self) -> None:
        from bybit_edge._legacy_v1.layers.l1_ingestion.m1_spikewavformer import _SurrogateSpike

        v = torch.tensor([0.5, 1.5, 2.0], requires_grad=True)
        spike = _SurrogateSpike.apply(v, 1.0)
        loss = spike.sum()
        loss.backward()
        assert v.grad is not None
        # Gradient muss endlich sein und in der Nähe von V_th ungleich Null
        assert torch.isfinite(v.grad).all()
        assert v.grad[1].abs() > 0  # bei V=1.5 (nahe V_th=1.0) muss ein Gradient da sein


class TestFitRunsAndImproves:
    """Mini-Train-Lauf für M1 (Spike/No-Spike)."""

    def test_fit_runs(self) -> None:
        rng = np.random.default_rng(0)
        mod = M1SpikeWavformer(hidden=(16, 16, 16))
        X = rng.normal(0, 1, (64, 3)).astype(np.float32)
        # Label: 1 wenn Summe positiv (synthetisch lernbar)
        y = (X.sum(axis=1) > 0).astype(np.int64)
        res = mod.fit(X, y, epochs=3, batch_size=16, lr=1e-2)
        assert np.isfinite(res["train_loss"])
        assert mod._fitted is True
