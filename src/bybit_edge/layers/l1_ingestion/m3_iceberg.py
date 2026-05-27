"""
M3 — Iceberg Detection [L1] [Standard]

Erkennt versteckte (Iceberg-)Orders anhand wiederholter Replenishments
auf demselben Preis-Level nach Ausfuehrung von Trades.

Formeln (PRD):
    IcebergScore_p = (Sum I(Size_{p,t+delta} >= 0.8 * Size_{p,t})) / N_hits
    Detection: if IcebergScore_p > 0.7 AND N_hits > 5 -> Iceberg
"""

from __future__ import annotations

import time
from typing import Any

from bybit_edge.config import (
    ICEBERG_MIN_HITS,
    ICEBERG_REPLENISHMENT_RATIO,
    ICEBERG_SCORE_THRESHOLD,
)
from bybit_edge.layers.base import BaseModule

# Maximale Eintraege pro Level um Speicherverbrauch zu begrenzen
_MAX_HISTORY_PER_LEVEL: int = 200
# Maximale Anzahl getrackte Levels
_MAX_LEVELS: int = 500


class M3IcebergDetector(BaseModule):
    """Erkennt Iceberg-Orders durch Replenishment-Tracking.

    Trackt pro Preis-Level die Size-Historie und ob es von Trades
    getroffen wurde. Ein Level gilt als Iceberg wenn es nach mindestens
    N_hits Trades mit einer Score > 0.7 wieder aufgefuellt wird.
    """

    def __init__(self) -> None:
        # Pro Preis-Level: [(ts, size, was_hit), ...]
        self._level_history: dict[float, list[tuple[float, float, bool]]] = {}

    # ------------------------------------------------------------------
    # Event-Handlers
    # ------------------------------------------------------------------

    def on_trade(self, price: float, ts: float) -> None:
        """Markiert das betroffene Level als 'hit' (Trade ausgefuehrt).

        Sucht das naechstliegende Level innerhalb einer Toleranz und
        markiert den letzten Eintrag als getroffen.
        """
        if price in self._level_history and self._level_history[price]:
            history = self._level_history[price]
            last_ts, last_size, _ = history[-1]
            history[-1] = (last_ts, last_size, True)

    def on_orderbook_update(self, price: float, size: float, ts: float) -> None:
        """Tracked ein Orderbuch-Update (neuer Snapshot eines Levels).

        Fuegt das Update als neuen Eintrag hinzu (noch nicht getroffen).
        """
        if price not in self._level_history:
            if len(self._level_history) >= _MAX_LEVELS:
                # Aeltestes Level entfernen
                oldest_key = min(
                    self._level_history,
                    key=lambda k: (
                        self._level_history[k][-1][0]
                        if self._level_history[k]
                        else 0.0
                    ),
                )
                del self._level_history[oldest_key]
            self._level_history[price] = []

        history = self._level_history[price]
        history.append((ts, size, False))

        # Beschraenkung der Historie pro Level
        if len(history) > _MAX_HISTORY_PER_LEVEL:
            self._level_history[price] = history[-_MAX_HISTORY_PER_LEVEL:]

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _compute_iceberg_score(self, price: float) -> tuple[float, int]:
        """Berechnet IcebergScore und N_hits fuer ein Preis-Level.

        Returns (score, n_hits).
        """
        history = self._level_history.get(price, [])
        if not history:
            return 0.0, 0

        # Finde alle Hits (Trades) und pruefe Replenishment
        hit_indices: list[int] = []
        for i, (_, _, was_hit) in enumerate(history):
            if was_hit:
                hit_indices.append(i)

        n_hits = len(hit_indices)
        if n_hits == 0:
            return 0.0, 0

        replenishment_count = 0
        for k, idx in enumerate(hit_indices):
            hit_size = history[idx][1]
            # Nur bis zum naechsten Hit suchen (oder Ende der History)
            boundary = hit_indices[k + 1] if k + 1 < len(hit_indices) else len(history)
            for j in range(idx + 1, boundary):
                next_size = history[j][1]
                if next_size >= ICEBERG_REPLENISHMENT_RATIO * hit_size:
                    replenishment_count += 1
                    break

        score = replenishment_count / n_hits if n_hits > 0 else 0.0
        return score, n_hits

    # ------------------------------------------------------------------
    # Hauptberechnung
    # ------------------------------------------------------------------

    def compute(  # type: ignore[override]
        self,
        levels: dict[float, float] | None = None,
        recent_trades: list[dict[str, Any]] | None = None,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """Analysiert aktuelle Orderbuch-Levels auf Icebergs.

        Parameters
        ----------
        levels : dict[float, float] | None
            {price: size} — aktuelle Orderbuch-Levels.
        recent_trades : list[dict] | None
            Kuerzliche Trades mit 'price' und 'ts' Keys.
        ts : float | None
            Zeitstempel; falls None wird time.time() verwendet.

        Returns
        -------
        dict mit iceberg_levels, n_icebergs_detected, signal,
        method_id, confidence, ts.
        """
        if ts is None:
            ts = time.time()
        if levels is None:
            levels = {}
        if recent_trades is None:
            recent_trades = []

        # Trades verarbeiten
        for trade in recent_trades:
            self.on_trade(trade["price"], trade.get("ts", ts))

        # Orderbuch-Updates verarbeiten
        for price, size in levels.items():
            self.on_orderbook_update(price, size, ts)

        # Iceberg-Detection pro Level
        iceberg_levels: list[dict[str, Any]] = []
        for price in levels:
            score, n_hits = self._compute_iceberg_score(price)
            if score > ICEBERG_SCORE_THRESHOLD and n_hits > ICEBERG_MIN_HITS:
                iceberg_levels.append({
                    "price": price,
                    "score": score,
                    "n_hits": n_hits,
                    "size": levels[price],
                })

        n_icebergs = len(iceberg_levels)
        signal: int = 1 if n_icebergs > 0 else 0

        # Confidence: bester Score unter den Icebergs
        confidence: float = 0.0
        if iceberg_levels:
            confidence = max(entry["score"] for entry in iceberg_levels)

        return {
            "iceberg_levels": iceberg_levels,
            "n_icebergs_detected": n_icebergs,
            "signal": signal,
            "method_id": "M3",
            "confidence": confidence,
            "ts": ts,
        }

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Prueft Iceberg-Parameter auf Plausibilitaet."""
        return (
            0.0 < ICEBERG_REPLENISHMENT_RATIO <= 1.0
            and 0.0 < ICEBERG_SCORE_THRESHOLD <= 1.0
            and ICEBERG_MIN_HITS > 0
        )

    def reset(self) -> None:
        """Setzt internen State vollstaendig zurueck."""
        self._level_history.clear()
