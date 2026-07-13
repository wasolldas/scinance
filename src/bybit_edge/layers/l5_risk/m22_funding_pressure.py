"""
M22 — Funding-Rate-Clamp Pressure-Release [L5] [Quick Win — TOP PRIORITÄT]

Formeln (PRD):
    F_t = P_t + clamp(I_t - P_t, -0.05%, +0.05%)
    Pressure_t = (I_t - P_t) - clamp(I_t - P_t, ±0.05%)
    Signal: |Pressure_t| > 2σ(Pressure_24h) AND T_settlement - t < 30 min

Richtung (PRD 7.3 / M22, S.682): "Long-Mean-Reversion-Trade ... wenn
aufgestaute Negative-Premium-Pressure die Clamp-Grenze überschritten hatte
(Shorts haben zu wenig gezahlt → Reversion kommt)."

Negative Premium (P < 0 → Perp unterbewertet) → Long-Reversion nach oben.
Da Pressure der Clamp-Rest von (I - P) ist, gilt bei negativer Premium
diff = I - P > 0 → Pressure > 0. Also:
    Pressure > 0  → Long  (+1)   (negative Premium, Shorts zu wenig gezahlt)
    Pressure < 0  → Short (-1)   (positive Premium, Longs zu wenig gezahlt)
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    FUNDING_CLAMP_LOWER,
    FUNDING_CLAMP_UPPER,
    FUNDING_INTEREST_RATE,
    PRESSURE_ENTRY_WINDOW_MINUTES,
    PRESSURE_EXIT_MINUTES_POST_SETTLEMENT,
    PRESSURE_ZSCORE_THRESHOLD,
)
from bybit_edge.layers.base import BaseModule

# Referenzfenster für sigma: ECHTE 24h Wall-Clock-Zeit, nicht eine feste
# Sample-Zahl. Ein count-basiertes Cap (früher: 50_000 Samples) deckt bei
# realistischer Live-Ticker-Kadenz deutlich WENIGER als 24h ab, wodurch
# `_24h_sigma` z.B. nur das ruhige Inter-Settlement-Rauschen sieht statt der
# echten 24h-Tail-Verteilung (siehe CRITICAL_REVIEW_2 M22-Finding).
_PRESSURE_HISTORY_WINDOW_SECONDS: float = 24.0 * 60.0 * 60.0

# Reiner Speicher-Schutz (Backstop), unabhängig vom Zeitfenster — greift nur
# bei pathologisch hoher Tick-Rate; das eigentliche Fenster ist zeitbasiert.
_PRESSURE_HISTORY_MAXLEN: int = 2_000_000

# Mindest-Samples bevor wir sigma sinnvoll schätzen
_MIN_SAMPLES_FOR_SIGMA: int = 100


class M22FundingPressure(BaseModule):
    """Funding-Rate-Clamp Pressure-Release Module.

    Berechnet den gestauten Pressure jenseits der Bybit Funding-Clamp-Grenzen
    und erzeugt ein Mean-Reversion-Signal im Settlement-Window.
    """

    def __init__(self) -> None:
        # (timestamp, pressure) pairs so the reference window can be pruned
        # by actual elapsed wall-clock time instead of sample count.
        self._pressure_history: deque[tuple[float, float]] = deque(
            maxlen=_PRESSURE_HISTORY_MAXLEN
        )
        self._24h_sigma: float = 0.0

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self, ticker_data: dict[str, Any], seconds_to_settlement: float
    ) -> dict[str, Any]:
        """Berechne Funding-Pressure-Signal.

        Parameters
        ----------
        ticker_data : dict
            Muss enthalten: ``premium_index``, ``funding_rate``.
            Optional: ``mark_price``, ``index_price``, ``last_price``, ``ts``
            (epoch seconds — used as "now" for the 24h window; falls back to
            wall-clock ``time.time()`` only if absent).
        seconds_to_settlement : float
            Sekunden bis zum nächsten Settlement (>0).

        Returns
        -------
        dict mit signal, pressure, pressure_zscore, funding_rate,
        seconds_to_settlement, in_window, method_id, confidence, ts.
        """
        P_t: float = float(ticker_data.get("premium_index", 0.0))
        I_t: float = FUNDING_INTEREST_RATE

        diff = I_t - P_t
        clamped = float(np.clip(diff, FUNDING_CLAMP_LOWER, FUNDING_CLAMP_UPPER))
        F_t: float = P_t + clamped
        pressure: float = diff - clamped

        # "now" MUST come from ticker_data["ts"], not wall-clock time.time():
        # this module also runs inside ReplayBacktester, which feeds ticks at
        # CPU speed while ticker_data["ts"] carries the SIMULATED/event time
        # (see replay_backtester._build_ticker_data). Using real wall-clock
        # time here would prune/keep pressure_history by backtest-loop
        # processing speed instead of actual elapsed market time, silently
        # defeating the 24h-window fix. live_runner._build_ticker_data sets
        # ts=time.time(), so live behaviour is unchanged.
        now = float(ticker_data.get("ts") or time.time())

        # Prune samples older than the 24h reference window — time-based,
        # not count-based (see module-level comment on
        # _PRESSURE_HISTORY_WINDOW_SECONDS).
        while (
            self._pressure_history
            and (now - self._pressure_history[0][0]) > _PRESSURE_HISTORY_WINDOW_SECONDS
        ):
            self._pressure_history.popleft()

        # Sigma-Update from the PRIOR history only (nur bei genug Samples).
        # The current tick is deliberately NOT yet included — it must be
        # evaluated against a reference distribution it is not itself part
        # of, otherwise it inflates its own sigma (self-reference bias).
        if len(self._pressure_history) >= _MIN_SAMPLES_FOR_SIGMA:
            self._24h_sigma = float(
                np.std([p for _, p in self._pressure_history])
            )

        # History-Update (AFTER computing sigma so the current tick is
        # excluded from its own reference distribution).
        self._pressure_history.append((now, pressure))

        # Window-Check
        in_window: bool = (
            0 < seconds_to_settlement
            < PRESSURE_ENTRY_WINDOW_MINUTES * 60
        )

        # Z-Score (Division-by-Zero sicher)
        if self._24h_sigma > 0:
            pressure_zscore: float = pressure / self._24h_sigma
        else:
            pressure_zscore = 0.0

        # Signal-Bestimmung
        pressure_extreme: bool = (
            self._24h_sigma > 0
            and abs(pressure) > PRESSURE_ZSCORE_THRESHOLD * self._24h_sigma
        )

        signal: int = 0
        if in_window and pressure_extreme:
            # PRD 7.3/M22: negative Premium (P<0) → diff=(I-P)>0 → Pressure>0
            # → Long-Reversion (+1); positive Premium → Pressure<0 → Short (-1).
            signal = 1 if pressure > 0 else -1

        # Confidence: skaliert mit abs(zscore), gedeckelt bei 1.0
        confidence: float = min(abs(pressure_zscore) / 4.0, 1.0) if signal != 0 else 0.0

        return {
            "signal": signal,
            "pressure": pressure,
            "pressure_zscore": pressure_zscore,
            "funding_rate": F_t,
            "seconds_to_settlement": seconds_to_settlement,
            "in_window": in_window,
            "method_id": "M22",
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prüft ob Clamp-Parameter sinnvoll konfiguriert sind."""
        return (
            FUNDING_CLAMP_UPPER > 0
            and FUNDING_CLAMP_LOWER < 0
            and PRESSURE_ZSCORE_THRESHOLD > 0
        )

    def reset(self) -> None:
        """Leert die Pressure-History und setzt sigma zurück."""
        self._pressure_history.clear()
        self._24h_sigma = 0.0
