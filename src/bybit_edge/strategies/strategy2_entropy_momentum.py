"""
Strategie 2 -- Entropie-Momentum (PRD 7.2).

Methoden: M6 (Shannon-Entropie L2) + M2 (OFI) + M22 (Funding-Pressure) + M7 (PE).

Entry-Bedingung:
    Shannon-Entropie_L2 < Median_24h - 2*sigma
    AND |OFI_rolling_5s| > Q90
    AND sign(Funding-Pressure) == sign(OFI)
    AND PE < Median_24h (Greenlight)

Exit-Bedingung:
    Shannon-Entropie zurueck ueber Median
    OR OFI-Vorzeichen flippt
    OR Funding-Pressure dissipiert (|P - F| < 0.01%)

Edge: Mikrostruktur-Information; institutionelle Aggression in
OFI + Orderbuch-Strukturzusammenbruch.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    S2_ENTROPY_ZSCORE,
    S2_PRESSURE_DISSIPATION,
)
from bybit_edge.layers.l1_ingestion.m2_ofi import M2OFI
from bybit_edge.layers.l3_regime.m6_entropy import M6ShannonEntropy
from bybit_edge.layers.l3_regime.m7_permutation_entropy import M7PermutationEntropy
from bybit_edge.layers.l5_risk.m22_funding_pressure import M22FundingPressure

# Entropy history for z-score calculation
_ENTROPY_HISTORY_MAXLEN: int = 50_000
_MIN_ENTROPY_SAMPLES: int = 100


class Strategy2EntropyMomentum:
    """Entropie-Momentum Strategie.

    Exploits entropy collapse (orderbook concentration) combined with
    OFI directional pressure and funding pressure alignment.
    """

    def __init__(self) -> None:
        self.m6: M6ShannonEntropy = M6ShannonEntropy()
        self.m2: M2OFI = M2OFI()
        self.m22: M22FundingPressure = M22FundingPressure()
        self.m7: M7PermutationEntropy = M7PermutationEntropy()

        self._in_trade: bool = False
        self._entry_price: float = 0.0
        self._entry_direction: int = 0
        self._entry_ts: float = 0.0
        self._entry_ofi_sign: int = 0

        # Independent entropy history for median/sigma
        self._entropy_history: deque[float] = deque(maxlen=_ENTROPY_HISTORY_MAXLEN)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_ticker(
        self,
        bid_sizes: np.ndarray,
        ask_sizes: np.ndarray,
        best_bid: tuple[float, float],
        best_ask: tuple[float, float],
        ticker_data: dict[str, Any],
        seconds_to_settlement: float,
        price: float,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """Process a ticker update and return action signal.

        Parameters
        ----------
        bid_sizes : np.ndarray
            Top-N level sizes from bid side.
        ask_sizes : np.ndarray
            Top-N level sizes from ask side.
        best_bid : tuple[float, float]
            (price, size) of best bid.
        best_ask : tuple[float, float]
            (price, size) of best ask.
        ticker_data : dict
            Must contain premium_index, funding_rate.
        seconds_to_settlement : float
            Seconds until next settlement.
        price : float
            Current last price.
        ts : float | None
            Timestamp; defaults to time.time().

        Returns
        -------
        dict with action, direction, price, strategy, modules, reason.
        """
        if ts is None:
            ts = time.time()

        # ----------------------------------------------------------
        # 1. Compute all module outputs
        # ----------------------------------------------------------
        m6_out: dict[str, Any] = self.m6.compute(bid_sizes, ask_sizes)
        m2_out: dict[str, Any] = self.m2.update(best_bid, best_ask, ts)
        m22_out: dict[str, Any] = self.m22.compute(ticker_data, seconds_to_settlement)
        m7_out: dict[str, Any] = self.m7.update(price)

        modules: dict[str, Any] = {
            "M6": m6_out,
            "M2": m2_out,
            "M22": m22_out,
            "M7": m7_out,
        }

        h_combined: float = m6_out["h_combined"]
        ofi: float = m2_out["ofi"]
        pressure: float = m22_out["pressure"]

        # Track entropy for z-score
        self._entropy_history.append(h_combined)

        # ----------------------------------------------------------
        # 2. Exit logic (checked first)
        # ----------------------------------------------------------
        if self._in_trade:
            exit_reason: str | None = self._check_exit(
                m6_out, m2_out, m22_out
            )
            if exit_reason is not None:
                direction_was: int = self._entry_direction
                self._in_trade = False
                self._entry_direction = 0
                self._entry_price = 0.0
                self._entry_ts = 0.0
                self._entry_ofi_sign = 0
                return {
                    "action": "exit",
                    "direction": direction_was,
                    "price": price,
                    "strategy": "S2",
                    "modules": modules,
                    "reason": exit_reason,
                }

        # ----------------------------------------------------------
        # 3. Entry logic
        # ----------------------------------------------------------
        wait_reason: str = "already_in_trade"
        if not self._in_trade:
            entry_ok, entry_reason = self._check_entry(
                m6_out, m2_out, m22_out, m7_out
            )
            if entry_ok:
                # Direction from OFI sign
                direction: int = 1 if ofi > 0 else -1
                self._in_trade = True
                self._entry_price = price
                self._entry_direction = direction
                self._entry_ts = ts
                self._entry_ofi_sign = 1 if ofi > 0 else -1
                return {
                    "action": "enter",
                    "direction": direction,
                    "price": price,
                    "strategy": "S2",
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
            "strategy": "S2",
            "modules": modules,
            "reason": wait_reason,
        }

    # ------------------------------------------------------------------
    # Entry conditions (PRD 7.2)
    # ------------------------------------------------------------------

    def _check_entry(
        self,
        m6_out: dict[str, Any],
        m2_out: dict[str, Any],
        m22_out: dict[str, Any],
        m7_out: dict[str, Any],
    ) -> tuple[bool, str]:
        """Evaluate all four entry conditions from PRD 7.2."""
        h_combined: float = m6_out["h_combined"]
        ofi: float = m2_out["ofi"]
        ofi_q90: float = m2_out["ofi_q90"]
        pressure: float = m22_out["pressure"]
        pe_greenlight: bool = m7_out.get("greenlight", False)

        # Condition 1: Shannon entropy < Median_24h - 2*sigma
        if not self._is_entropy_collapsed(h_combined):
            return False, "entropy_not_collapsed"

        # Condition 2: |OFI_rolling_5s| > Q90
        if ofi_q90 <= 0 or abs(ofi) <= ofi_q90:
            return False, "ofi_below_q90"

        # Condition 3: sign(Funding-Pressure) == sign(OFI)
        if ofi == 0 or pressure == 0:
            return False, "ofi_or_pressure_zero"
        if np.sign(pressure) != np.sign(ofi):
            return False, "pressure_ofi_misaligned"

        # Condition 4: PE < Median_24h (Greenlight)
        if not pe_greenlight:
            return False, "pe_no_greenlight"

        return True, "all_conditions_met"

    def _is_entropy_collapsed(self, h_combined: float) -> bool:
        """Check if entropy is below Median - 2*sigma."""
        if len(self._entropy_history) < _MIN_ENTROPY_SAMPLES:
            return False
        h_arr = np.array(list(self._entropy_history), dtype=np.float64)
        h_median: float = float(np.median(h_arr))
        h_std: float = float(np.std(h_arr))
        if h_std < 1e-12:
            return False
        return h_combined < h_median - S2_ENTROPY_ZSCORE * h_std

    # ------------------------------------------------------------------
    # Exit conditions (PRD 7.2)
    # ------------------------------------------------------------------

    def _check_exit(
        self,
        m6_out: dict[str, Any],
        m2_out: dict[str, Any],
        m22_out: dict[str, Any],
    ) -> str | None:
        """Evaluate exit conditions."""
        h_combined: float = m6_out["h_combined"]
        ofi: float = m2_out["ofi"]
        pressure: float = m22_out["pressure"]

        # Exit 1: Entropy back above median
        if len(self._entropy_history) >= _MIN_ENTROPY_SAMPLES:
            h_arr = np.array(list(self._entropy_history), dtype=np.float64)
            h_median: float = float(np.median(h_arr))
            if h_combined >= h_median:
                return "entropy_recovered"

        # Exit 2: OFI sign flip
        current_ofi_sign: int = 1 if ofi > 0 else (-1 if ofi < 0 else 0)
        if self._entry_ofi_sign != 0 and current_ofi_sign != 0:
            if current_ofi_sign != self._entry_ofi_sign:
                return "ofi_sign_flip"

        # Exit 3: Funding pressure dissipated
        if abs(pressure) < S2_PRESSURE_DISSIPATION:
            return "pressure_dissipated"

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all internal state."""
        self.m6.reset()
        self.m2.reset()
        self.m22.reset()
        self.m7.reset()
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._entry_ofi_sign = 0
        self._entropy_history.clear()

    @property
    def in_trade(self) -> bool:
        """Whether the strategy currently holds a position."""
        return self._in_trade

    @property
    def entry_direction(self) -> int:
        """Direction of current trade: 1=Long, -1=Short, 0=none."""
        return self._entry_direction
