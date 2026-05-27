"""
Tests fuer M17 -- Renyi-Transfer-Entropy Lead-Lag.

Testet:
- TE bei unabhaengigen Serien -> TE ~ 0
- TE bei verschobener Kopie -> TE > 0
- TE asymmetrisch bei unidirektionalem Fluss
- Diskretisierung in 3 Bins
- Lead-Lag-Edges bei korrelierten Serien
- Keine Edges bei unabhaengigen Serien
- Leere Returns -> kein Crash
- Reset
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l4_pattern.m17_renyi_te import M17RenyiTE


class TestM17RenyiTE:
    """Tests fuer das M17RenyiTE Modul."""

    def test_te_independent_series(self) -> None:
        """Unabhaengige Serien -> TE ~ 0."""
        rng = np.random.default_rng(42)
        mod = M17RenyiTE(n_bins=3, te_threshold=0.05)

        n = 500
        source = rng.standard_normal(n)
        target = rng.standard_normal(n)

        te = mod._transfer_entropy(
            mod._discretize(source),
            mod._discretize(target),
        )
        # TE sollte bei unabhaengigen Serien nahe 0 sein
        assert te < 0.05

    def test_te_lagged_copy(self) -> None:
        """Y = X shifted um 1 -> TE(X -> Y) > 0."""
        rng = np.random.default_rng(42)
        mod = M17RenyiTE(n_bins=3, te_threshold=0.05)

        n = 1000
        source = rng.choice([-1.0, 0.0, 1.0], size=n)
        # Target ist verschobene Kopie der Quelle
        target = np.zeros(n)
        target[1:] = source[:-1]

        te = mod._transfer_entropy(
            mod._discretize(source),
            mod._discretize(target),
        )
        # TE sollte signifikant > 0 sein
        assert te > 0.1

    def test_te_asymmetric(self) -> None:
        """TE(X -> Y) != TE(Y -> X) bei unidirektionalem Fluss."""
        rng = np.random.default_rng(42)
        mod = M17RenyiTE(n_bins=3, te_threshold=0.05)

        n = 1000
        source = rng.choice([-1.0, 0.0, 1.0], size=n)
        target = np.zeros(n)
        target[1:] = source[:-1]  # Target folgt Source

        src_d = mod._discretize(source)
        tgt_d = mod._discretize(target)

        te_forward = mod._transfer_entropy(src_d, tgt_d)  # X -> Y
        te_backward = mod._transfer_entropy(tgt_d, src_d)  # Y -> X

        # Forward TE sollte deutlich groesser sein
        assert te_forward > te_backward

    def test_discretize_three_bins(self) -> None:
        """Diskretisierung erzeugt genau 3 verschiedene Bins."""
        mod = M17RenyiTE(n_bins=3)
        series = np.array([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
        disc = mod._discretize(series, n_bins=3)

        assert disc.dtype == np.int64
        unique_bins = np.unique(disc)
        assert len(unique_bins) == 3

    def test_lead_lag_edges_detected(self) -> None:
        """Korrelierte Serien -> Lead-Lag-Edges erkannt."""
        rng = np.random.default_rng(42)
        mod = M17RenyiTE(n_bins=3, te_threshold=0.02)

        n = 1000
        btc = rng.choice([-1.0, 0.0, 1.0], size=n)
        eth = np.zeros(n)
        eth[1:] = btc[:-1]  # ETH folgt BTC

        # SOL unabhaengig
        sol = rng.standard_normal(n)

        result = mod.compute(
            returns_matrix={
                "BTCUSDT": btc,
                "ETHUSDT": eth,
                "SOLUSDT": sol,
            },
            reference="BTCUSDT",
            current_ts=1000.0,
        )

        assert result["signal"] == 1
        assert result["method_id"] == "M17"

        # ETH sollte starke Edge haben
        edges = result["lead_lag_edges"]
        assert len(edges) >= 1
        edge_targets = [e["target"] for e in edges]
        assert "ETHUSDT" in edge_targets

    def test_no_edges_independent(self) -> None:
        """Unabhaengige Serien -> keine Lead-Lag-Edges."""
        rng = np.random.default_rng(42)
        mod = M17RenyiTE(n_bins=3, te_threshold=0.05)

        n = 500
        result = mod.compute(
            returns_matrix={
                "BTCUSDT": rng.standard_normal(n),
                "ETHUSDT": rng.standard_normal(n),
                "SOLUSDT": rng.standard_normal(n),
            },
            reference="BTCUSDT",
            current_ts=1000.0,
        )

        assert result["signal"] == 0
        assert len(result["lead_lag_edges"]) == 0

    def test_empty_returns_no_crash(self) -> None:
        """Leere Returns-Matrix -> kein Crash, signal = 0."""
        mod = M17RenyiTE()

        # Referenz nicht vorhanden
        result = mod.compute(
            returns_matrix={},
            reference="BTCUSDT",
            current_ts=1000.0,
        )
        assert result["signal"] == 0
        assert result["te_scores"] == {}
        assert result["method_id"] == "M17"

        # Referenz vorhanden aber zu kurz
        result2 = mod.compute(
            returns_matrix={"BTCUSDT": np.array([0.01, 0.02])},
            reference="BTCUSDT",
            current_ts=1000.0,
        )
        assert result2["signal"] == 0

    def test_reset(self) -> None:
        """Reset wirft keinen Fehler (M17 ist stateless)."""
        mod = M17RenyiTE()
        rng = np.random.default_rng(42)

        mod.compute(
            returns_matrix={
                "BTCUSDT": rng.standard_normal(100),
                "ETHUSDT": rng.standard_normal(100),
            },
            reference="BTCUSDT",
            current_ts=1000.0,
        )

        mod.reset()

        # Nach Reset funktioniert alles weiterhin
        result = mod.compute(
            returns_matrix={
                "BTCUSDT": rng.standard_normal(100),
                "ETHUSDT": rng.standard_normal(100),
            },
            reference="BTCUSDT",
            current_ts=1000.0,
        )
        assert result["method_id"] == "M17"
