"""
M17 -- Renyi-Transfer-Entropy Lead-Lag [L4] [Moonshot]

Formel (PRD, Shannon-TE als Basis, Schreiber 2000):
    TE_{Y->X} = sum p(x_{n+1}, x_n^(k), y_n^(l))
                * log[ p(x_{n+1} | x_n^(k), y_n^(l)) / p(x_{n+1} | x_n^(k)) ]

Transfer-Entropy misst den gerichteten Informationsfluss von einer
Quelle (z.B. BTC) zu einem Ziel (z.B. ALT). Hohe TE(BTC->ALT) bedeutet,
dass BTC-Returns Vorhersagekraft fuer zukuenftige ALT-Returns haben
(Lead-Lag-Beziehung).

Implementierung: Eigene histogram-basierte TE-Schaetzung (~80 LOC),
ohne externe TE-Libraries (kein IDTxl/pyinform).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.config import (
    RENYI_TE_THRESHOLD,
)
from bybit_edge.layers.base import BaseModule

# Minimum an Datenpunkten fuer sinnvolle TE-Schaetzung
_MIN_SAMPLES: int = 30

# Numerische Stabilitaet
_LOG_EPSILON: float = 1e-12


class M17RenyiTE(BaseModule):
    """Renyi-Transfer-Entropy Lead-Lag Detektor.

    Berechnet Shannon-Transfer-Entropy zwischen einer Referenz (BTC)
    und allen anderen Symbolen. Starke TE-Werte signalisieren gerichtete
    Lead-Lag-Beziehungen, die fuer prädiktive Signale nutzbar sind.
    """

    def __init__(self, n_bins: int = 3, te_threshold: float = RENYI_TE_THRESHOLD) -> None:
        self._n_bins: int = n_bins
        self._te_threshold: float = te_threshold

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _discretize(self, series: np.ndarray, n_bins: int | None = None) -> np.ndarray:
        """Quantil-basierte Diskretisierung in n_bins Kategorien.

        Bins: 0 = down, 1 = flat, 2 = up (bei n_bins=3).

        Parameters
        ----------
        series : np.ndarray
            1D-Array von Returns.
        n_bins : int | None
            Anzahl Bins. Falls None, wird self._n_bins verwendet.

        Returns
        -------
        np.ndarray
            Integer-Array mit Bin-Indizes (0..n_bins-1).
        """
        if n_bins is None:
            n_bins = self._n_bins

        if series.size == 0:
            return np.array([], dtype=np.int64)

        # Quantil-Grenzen berechnen
        quantiles = np.linspace(0, 100, n_bins + 1)[1:-1]
        thresholds = np.percentile(series, quantiles)

        # Diskretisieren via np.digitize
        discretized = np.digitize(series, thresholds)

        return discretized.astype(np.int64)

    def _transfer_entropy(
        self,
        source: np.ndarray,
        target: np.ndarray,
        k: int = 1,
        l: int = 1,
    ) -> float:
        """Berechne Shannon Transfer-Entropy TE(source -> target).

        Histogram-basierte Schaetzung.

        Parameters
        ----------
        source : np.ndarray
            Diskretisierte Quell-Serie (Integer-Bins).
        target : np.ndarray
            Diskretisierte Ziel-Serie (Integer-Bins).
        k : int
            Embedding-Dimension fuer Target-History.
        l : int
            Embedding-Dimension fuer Source-History.

        Returns
        -------
        float
            Transfer-Entropy in Bits. 0.0 bei unzureichenden Daten.
        """
        n = min(len(source), len(target))
        lag = max(k, l)
        if n <= lag:
            return 0.0

        # Extrahiere Vektoren fuer die TE-Berechnung
        # x_{n+1}: target[lag:]
        # x_n^(k): target history (k steps back)
        # y_n^(l): source history (l steps back)
        effective_n = n - lag

        x_future = target[lag:lag + effective_n]
        x_past = np.column_stack([
            target[lag - i - 1:lag - i - 1 + effective_n]
            for i in range(k)
        ])
        y_past = np.column_stack([
            source[lag - i - 1:lag - i - 1 + effective_n]
            for i in range(l)
        ])

        # Erstelle zusammengesetzten State fuer Histogram-Counts
        n_bins = int(max(source.max(), target.max())) + 1 if effective_n > 0 else 3

        # Kodiere States als einzelne Integer fuer effizientes Zaehlen
        # x_past_code, y_past_code, joint_code
        x_past_flat = x_past[:, 0] if k == 1 else np.ravel_multi_index(
            x_past.T, [n_bins] * k
        )
        y_past_flat = y_past[:, 0] if l == 1 else np.ravel_multi_index(
            y_past.T, [n_bins] * l
        )

        # Joint: (x_future, x_past, y_past)
        n_xp = n_bins ** k
        n_yp = n_bins ** l

        # Zaehle Joint-Haeufigkeiten: p(x_{n+1}, x_n^(k), y_n^(l))
        joint_idx = (
            x_future * n_xp * n_yp
            + x_past_flat * n_yp
            + y_past_flat
        )
        joint_counts = np.bincount(joint_idx, minlength=n_bins * n_xp * n_yp)
        joint_probs = joint_counts / effective_n

        # Marginal: p(x_{n+1}, x_n^(k))
        marginal_xf_xp_idx = x_future * n_xp + x_past_flat
        marginal_xf_xp_counts = np.bincount(
            marginal_xf_xp_idx, minlength=n_bins * n_xp
        )
        marginal_xf_xp_probs = marginal_xf_xp_counts / effective_n

        # Marginal: p(x_n^(k), y_n^(l))
        marginal_xp_yp_idx = x_past_flat * n_yp + y_past_flat
        marginal_xp_yp_counts = np.bincount(
            marginal_xp_yp_idx, minlength=n_xp * n_yp
        )
        marginal_xp_yp_probs = marginal_xp_yp_counts / effective_n

        # Marginal: p(x_n^(k))
        marginal_xp_counts = np.bincount(x_past_flat, minlength=n_xp)
        marginal_xp_probs = marginal_xp_counts / effective_n

        # TE = sum p(x_{n+1}, x_n^(k), y_n^(l))
        #      * log2[ p(x_{n+1} | x_n^(k), y_n^(l)) / p(x_{n+1} | x_n^(k)) ]
        #
        # p(x_{n+1} | x_n^(k), y_n^(l)) = p(x_{n+1}, x_n^(k), y_n^(l)) / p(x_n^(k), y_n^(l))
        # p(x_{n+1} | x_n^(k))           = p(x_{n+1}, x_n^(k)) / p(x_n^(k))

        te: float = 0.0
        for idx in range(len(joint_probs)):
            p_joint = joint_probs[idx]
            if p_joint < _LOG_EPSILON:
                continue

            # Dekodiere Indizes
            xf = idx // (n_xp * n_yp)
            remainder = idx % (n_xp * n_yp)
            xp = remainder // n_yp
            yp = remainder % n_yp

            # p(x_n^(k), y_n^(l))
            p_xp_yp = marginal_xp_yp_probs[xp * n_yp + yp]
            if p_xp_yp < _LOG_EPSILON:
                continue

            # p(x_{n+1}, x_n^(k))
            p_xf_xp = marginal_xf_xp_probs[xf * n_xp + xp]

            # p(x_n^(k))
            p_xp = marginal_xp_probs[xp]
            if p_xp < _LOG_EPSILON:
                continue

            # Conditional probabilities
            p_cond_joint = p_joint / p_xp_yp      # p(x_{n+1} | x_n^(k), y_n^(l))
            p_cond_marginal = p_xf_xp / p_xp      # p(x_{n+1} | x_n^(k))

            if p_cond_marginal < _LOG_EPSILON:
                continue

            te += p_joint * np.log2(p_cond_joint / p_cond_marginal)

        return max(float(te), 0.0)

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self,
        returns_matrix: dict[str, np.ndarray],
        reference: str = "BTCUSDT",
        current_ts: float | None = None,
    ) -> dict[str, Any]:
        """Berechne Transfer-Entropy von Referenz zu allen anderen Symbolen.

        Parameters
        ----------
        returns_matrix : dict[str, np.ndarray]
            Returns pro Symbol, z.B.
            {"BTCUSDT": np.array([...]), "ETHUSDT": np.array([...]), ...}.
        reference : str
            Referenz-Symbol (Quelle), default "BTCUSDT".
        current_ts : float | None
            Zeitstempel. Falls None, wird time.time() verwendet.

        Returns
        -------
        dict mit te_scores, lead_lag_edges, signal, method_id,
        confidence, ts.
        """
        now = current_ts if current_ts is not None else time.time()

        # Pruefe ob Referenz vorhanden
        if reference not in returns_matrix:
            return {
                "te_scores": {},
                "lead_lag_edges": [],
                "signal": 0,
                "method_id": "M17",
                "confidence": 0.0,
                "ts": now,
            }

        ref_returns = np.asarray(returns_matrix[reference], dtype=np.float64)

        if ref_returns.size < _MIN_SAMPLES:
            return {
                "te_scores": {},
                "lead_lag_edges": [],
                "signal": 0,
                "method_id": "M17",
                "confidence": 0.0,
                "ts": now,
            }

        # Diskretisiere Referenz-Returns
        ref_disc = self._discretize(ref_returns)

        te_scores: dict[str, float] = {}
        lead_lag_edges: list[dict[str, Any]] = []

        for symbol, alt_returns in returns_matrix.items():
            if symbol == reference:
                continue

            alt_returns = np.asarray(alt_returns, dtype=np.float64)

            # Laengen angleichen
            min_len = min(len(ref_returns), len(alt_returns))
            if min_len < _MIN_SAMPLES:
                continue

            ref_slice = ref_returns[:min_len]
            alt_slice = alt_returns[:min_len]

            # Diskretisiere
            ref_d = self._discretize(ref_slice)
            alt_d = self._discretize(alt_slice)

            # TE(reference -> alt)
            te_val = self._transfer_entropy(source=ref_d, target=alt_d)
            te_scores[symbol] = te_val

            # Lead-Lag-Edge: TE > threshold
            if te_val > self._te_threshold:
                lead_lag_edges.append({
                    "source": reference,
                    "target": symbol,
                    "te": te_val,
                })

        # Sortiere Lead-Lag-Edges nach TE (staerkste zuerst)
        lead_lag_edges.sort(key=lambda x: x["te"], reverse=True)

        signal: int = 1 if len(lead_lag_edges) > 0 else 0

        # Confidence: basiert auf staerkstem TE
        confidence: float = 0.0
        if lead_lag_edges:
            max_te = lead_lag_edges[0]["te"]
            # Skalierung: TE=0.05 -> conf ~0.25, TE=0.2 -> conf ~1.0
            confidence = min(max_te / 0.2, 1.0)

        return {
            "te_scores": te_scores,
            "lead_lag_edges": lead_lag_edges,
            "signal": signal,
            "method_id": "M17",
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prueft ob Konfiguration sinnvoll ist."""
        return self._n_bins >= 2 and self._te_threshold > 0.0

    def reset(self) -> None:
        """M17 ist stateless -- nichts zurueckzusetzen."""
