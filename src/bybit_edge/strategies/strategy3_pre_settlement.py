"""
Strategie 3 — Pre-Settlement Pressure-Release (erste live-paper-testbare Kombination).

Methoden: M22 (Funding-Clamp) + M23 (Mark-Index-Basis) + M24 (Kalman) + M8 (BOCPD).

Entry-Bedingung (PRD 7.3):
    T_settlement - t < 30 min
    AND |Funding-Pressure| > Q90 (rolling 30d)
    AND Mark-Index-Basis * sign(Pressure) > 0  (gleiche Richtung)
    AND BOCPD-Run-Length stabil (kein concurrent Change-Point in OI)

Exit-Bedingung:
    Settlement-Tick + 10 min
    OR Funding rastet zurück innerhalb [-0.01%, +0.01%]

Edge-Quelle: Mechanische Pressure-Release; Edge ist timing-präzise,
nicht direktional-prognostisch.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    PRESSURE_ENTRY_WINDOW_MINUTES,
    PRESSURE_EXIT_MINUTES_POST_SETTLEMENT,
    S3_EXIT_FUNDING_BAND,
    S3_PRESSURE_QUANTILE,
)
from bybit_edge.layers.l3_regime.m8_bocpd import M8BOCPD
from bybit_edge.layers.l5_risk.m22_funding_pressure import M22FundingPressure
from bybit_edge.layers.l5_risk.m23_basis_convergence import M23BasisConvergence
from bybit_edge.layers.l5_risk.m24_kalman_premium import M24KalmanPremium

# Rolling window for pressure quantile estimation (30d at ~1 per 100ms is huge;
# we keep 50_000 samples which covers ~1.4h at 100ms — the M22 module itself
# keeps the same buffer; we maintain a separate one here for Q90 calculation
# because M22's internal Q90 uses z-score, but PRD 7.3 requires quantile).
_PRESSURE_Q_MAXLEN: int = 50_000

# Minimum samples before we can compute a meaningful Q90
_MIN_SAMPLES_FOR_QUANTILE: int = 100


# Live-config accessors. These were previously cached as module-level
# constants (``_EXIT_SECONDS_POST_SETTLEMENT``, ``_ENTRY_WINDOW_SECONDS``,
# ``_EXIT_BAND_LOW`` / ``_EXIT_BAND_HIGH``) computed once at import time.
# Re-reading them on every call lets :class:`bybit_edge.tuning.ParameterContext`
# tune the underlying config values without forcing a module reload. The
# overhead is one attribute lookup per call — negligible vs. the work the
# strategy already performs and bit-identical to the cached behaviour when
# no override is active.
def _entry_window_seconds() -> float:
    return PRESSURE_ENTRY_WINDOW_MINUTES * 60.0


def _exit_seconds_post_settlement() -> float:
    return PRESSURE_EXIT_MINUTES_POST_SETTLEMENT * 60.0


def _exit_band() -> tuple[float, float]:
    return S3_EXIT_FUNDING_BAND[0], S3_EXIT_FUNDING_BAND[1]


# Back-compat module constants. Kept for downstream callers / tests that
# imported these symbols directly. The live strategy code reads via the
# accessors above; these eagerly-evaluated copies reflect the defaults at
# import time and are NOT used inside the class itself.
_ENTRY_WINDOW_SECONDS: float = _entry_window_seconds()
_EXIT_SECONDS_POST_SETTLEMENT: float = _exit_seconds_post_settlement()
_EXIT_BAND_LOW: float = _exit_band()[0]
_EXIT_BAND_HIGH: float = _exit_band()[1]


class Strategy3PreSettlement:
    """Pre-Settlement Pressure-Release strategy.

    Orchestrates M22 + M23 + M24 + M8 to exploit the deterministic
    funding-settlement mechanic on Bybit perpetual futures.
    """

    def __init__(self) -> None:
        self.m22: M22FundingPressure = M22FundingPressure()
        self.m23: M23BasisConvergence = M23BasisConvergence()
        self.m24: M24KalmanPremium = M24KalmanPremium()
        self.m8: M8BOCPD = M8BOCPD()

        self._in_trade: bool = False
        self._entry_price: float = 0.0
        self._entry_direction: int = 0
        self._entry_ts: float = 0.0
        self._settlement_ts: float = 0.0

        # Independent pressure-history for Q90 quantile gate
        self._pressure_history: deque[float] = deque(maxlen=_PRESSURE_Q_MAXLEN)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_ticker(
        self,
        ticker_data: dict[str, Any],
        seconds_to_settlement: float,
        open_interest: float,
    ) -> dict[str, Any]:
        """Process a ticker update and return an action signal.

        Parameters
        ----------
        ticker_data : dict
            Must contain: ``last_price``, ``mark_price``, ``index_price``,
            ``funding_rate``, ``premium_index``.
        seconds_to_settlement : float
            Seconds until the next 00/08/16 UTC settlement.
            Positive means settlement is in the future; negative means
            we are past settlement (useful for exit timing).
        open_interest : float
            Current open interest value for BOCPD regime detection.

        Returns
        -------
        dict with keys: action, direction, price, strategy, modules, reason.
        """
        now: float = time.time()

        # ----------------------------------------------------------
        # 1. Compute all module outputs
        # ----------------------------------------------------------
        m22_out: dict[str, Any] = self.m22.compute(
            ticker_data, seconds_to_settlement
        )
        m23_out: dict[str, Any] = self.m23.compute(
            ticker_data, seconds_to_settlement
        )
        m24_out: dict[str, Any] = self.m24.compute(ticker_data)
        m8_out: dict[str, Any] = self.m8.compute(open_interest)

        modules: dict[str, Any] = {
            "M22": m22_out,
            "M23": m23_out,
            "M24": m24_out,
            "M8": m8_out,
        }

        price: float = float(ticker_data.get("last_price", 0.0))
        pressure: float = m22_out["pressure"]

        # Track pressure for Q90 quantile
        self._pressure_history.append(abs(pressure))

        # ----------------------------------------------------------
        # 2. Exit logic (checked first — exit takes priority)
        # ----------------------------------------------------------
        if self._in_trade:
            exit_reason: str | None = self._check_exit(
                seconds_to_settlement, pressure, now
            )
            if exit_reason is not None:
                self._in_trade = False
                direction_was: int = self._entry_direction
                self._entry_direction = 0
                self._entry_price = 0.0
                self._entry_ts = 0.0
                self._settlement_ts = 0.0
                return {
                    "action": "exit",
                    "direction": direction_was,
                    "price": price,
                    "strategy": "S3",
                    "modules": modules,
                    "reason": exit_reason,
                }

        # ----------------------------------------------------------
        # 3. Entry logic (only when not in a trade)
        # ----------------------------------------------------------
        wait_reason: str = "already_in_trade"
        if not self._in_trade:
            entry_ok, entry_reason = self._check_entry(
                m22_out, m23_out, m8_out, seconds_to_settlement
            )
            if entry_ok:
                # Direction from M22 (PRD 7.3/M22): positive pressure
                # (negative Premium) -> Long (+1); negative pressure -> Short (-1)
                direction: int = self._direction_from_pressure(pressure)
                self._in_trade = True
                self._entry_price = price
                self._entry_direction = direction
                self._entry_ts = now
                # Store expected settlement timestamp for exit timing
                self._settlement_ts = now + seconds_to_settlement
                return {
                    "action": "enter",
                    "direction": direction,
                    "price": price,
                    "strategy": "S3",
                    "modules": modules,
                    "reason": entry_reason,
                }
            wait_reason = entry_reason

        # ----------------------------------------------------------
        # 4. No action
        # ----------------------------------------------------------
        return {
            "action": "wait",
            "direction": 0,
            "price": price,
            "strategy": "S3",
            "modules": modules,
            "reason": wait_reason,
        }

    # ------------------------------------------------------------------
    # Internal: Direction
    # ------------------------------------------------------------------

    @staticmethod
    def _direction_from_pressure(pressure: float) -> int:
        """Map funding pressure to the mean-reversion trade direction.

        PRD 7.3 / M22: positive pressure stems from a negative Premium
        (perp underpriced) -> Long-reversion (+1); negative pressure from a
        positive Premium (perp overpriced) -> Short-reversion (-1).

        When ``config.S3_INVERT_DIRECTION`` is True (debug/research flag),
        the resulting sign is flipped. The flag is read at call time so
        :class:`bybit_edge.tuning.ParameterContext` patches take effect.
        """
        from bybit_edge import config as _cfg
        base = 1 if pressure > 0 else -1
        return -base if _cfg.S3_INVERT_DIRECTION else base

    # ------------------------------------------------------------------
    # Internal: Entry conditions
    # ------------------------------------------------------------------

    def _check_entry(
        self,
        m22_out: dict[str, Any],
        m23_out: dict[str, Any],
        m8_out: dict[str, Any],
        seconds_to_settlement: float,
    ) -> tuple[bool, str]:
        """Evaluate all four entry conditions from PRD 7.3.

        Returns (True, reason) if all pass, (False, reason) otherwise.
        """
        pressure: float = m22_out["pressure"]
        basis: float = m23_out["basis"]

        # Condition 1: T_settlement - t < 30 min (and > 0)
        in_window: bool = 0 < seconds_to_settlement < _entry_window_seconds()
        if not in_window:
            return False, "outside_settlement_window"

        # Condition 2: |Funding-Pressure| > Q90 (rolling)
        pressure_extreme: bool = self._is_pressure_above_q90(abs(pressure))
        if not pressure_extreme:
            return False, "pressure_below_q90"

        # Condition 3: Basis must confirm the intended mean-reversion direction
        # (PRD 7.3 "gleiche Richtung"). The intended trade direction equals
        # sign(Pressure) (PRD M22, see _direction_from_pressure):
        #   Pressure > 0 (negative Premium, perp underpriced) -> Long  (+1)
        #   Pressure < 0 (positive Premium, perp overpriced)   -> Short (-1)
        # "Gleiche Richtung" means the basis must CONFIRM that reversion:
        # a Long requires a negative basis (perp below index), a Short a
        # positive basis. Hence basis and the trade direction have OPPOSITE
        # signs -> basis * direction < 0. Because Pressure is the clamp
        # residual of (I - P), sign(Pressure) is always opposite to sign(basis)
        # by construction, so the literal "basis * sign(Pressure) > 0" gate was
        # never satisfiable (PRD-bug). This is the economically correct gate.
        if pressure == 0.0:
            return False, "pressure_zero"
        direction: int = self._direction_from_pressure(pressure)
        basis_aligned: bool = basis * direction < 0
        if not basis_aligned:
            return False, "basis_wrong_direction"

        # Condition 4: BOCPD run-length stable (no concurrent changepoint in OI)
        bocpd_stable: bool = not m8_out["changepoint"]
        if not bocpd_stable:
            return False, "bocpd_changepoint_detected"

        return True, "all_conditions_met"

    def _is_pressure_above_q90(self, abs_pressure: float) -> bool:
        """Check if absolute pressure exceeds the rolling Q90 quantile."""
        if len(self._pressure_history) < _MIN_SAMPLES_FOR_QUANTILE:
            return False
        q90: float = float(
            np.quantile(list(self._pressure_history), S3_PRESSURE_QUANTILE)
        )
        return abs_pressure > q90

    # ------------------------------------------------------------------
    # Internal: Exit conditions
    # ------------------------------------------------------------------

    def _check_exit(
        self,
        seconds_to_settlement: float,
        pressure: float,
        now: float,
    ) -> str | None:
        """Evaluate exit conditions.

        Returns a reason string if exit should happen, None otherwise.
        """
        # Exit condition 1: Settlement-Tick + 10 min
        # We detect this by checking if we have passed the settlement
        # point by more than EXIT_SECONDS.
        # seconds_to_settlement < 0 means we are past settlement.
        # The magnitude tells us how far past.
        exit_secs = _exit_seconds_post_settlement()
        if seconds_to_settlement < -exit_secs:
            return "settlement_plus_10min"

        # Also detect via stored settlement timestamp as fallback
        if self._settlement_ts > 0 and now > self._settlement_ts + exit_secs:
            return "settlement_plus_10min_ts"

        # Exit condition 2: Funding pressure dissipated back into [-0.01%, +0.01%]
        band_low, band_high = _exit_band()
        if band_low <= pressure <= band_high:
            return "pressure_dissipated"

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all internal state for backtester reuse."""
        self.m22.reset()
        self.m23.reset()
        self.m24.reset()
        self.m8.reset()
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._settlement_ts = 0.0
        self._pressure_history.clear()

    @property
    def in_trade(self) -> bool:
        """Whether the strategy currently holds a position."""
        return self._in_trade

    @property
    def entry_direction(self) -> int:
        """Direction of current trade: 1=Long, -1=Short, 0=none."""
        return self._entry_direction

    @property
    def entry_price(self) -> float:
        """Entry price of current trade (0.0 if not in trade)."""
        return self._entry_price
