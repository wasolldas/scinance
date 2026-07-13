# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Strategie 5 -- Cross-Sectional Ergodicity Reversion (PRD 7.5).

Methoden: M13 (Cross-Sectional-Z) + M17 (Renyi-TE) + M9 (HMM).

Entry-Bedingung:
    |Cross-Sectional-Z| > 2.5
    AND Renyi-TE(BTC -> Alt) > 0.05 (echter Informationsfluss)
    AND HMM-State != "High-Vol-Crash"
    Direction = gegen Z (Mean-Reversion)

Exit-Bedingung:
    |Z| < 0.5
    OR Time-Stop 24h
    OR HMM-Regime-Wechsel

Edge: Statistische Mean-Reversion ueber Symbol-Panel;
Renyi-TE filtert blosse Outlier.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.config import (
    RENYI_TE_THRESHOLD,
    S5_TIME_STOP_HOURS,
    S5_Z_ENTRY,
    S5_Z_EXIT,
)
from bybit_edge.layers.l3_regime.m13_cross_sectional_z import M13CrossSectionalZ
from bybit_edge.layers.l3_regime.m9_hmm import HIGH_VOL, M9HMM
from bybit_edge.layers.l4_pattern.m17_renyi_te import M17RenyiTE

# Time-stop in seconds
_TIME_STOP_SECONDS: float = S5_TIME_STOP_HOURS * 3600.0


class Strategy5CrossSectional:
    """Cross-Sectional Ergodicity Reversion Strategy.

    Identifies symbols whose time-average deviates significantly from
    the ensemble mean and trades mean-reversion, gated by BTC->Alt
    information flow (Renyi-TE) and HMM regime filter.
    """

    def __init__(self) -> None:
        self.m13: M13CrossSectionalZ = M13CrossSectionalZ()
        self.m17: M17RenyiTE = M17RenyiTE()
        self.m9: M9HMM = M9HMM()

        self._in_trade: bool = False
        self._entry_price: float = 0.0
        self._entry_direction: int = 0
        self._entry_ts: float = 0.0
        self._entry_symbol: str = ""
        self._entry_hmm_state: int = -1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_data(
        self,
        returns: dict[str, float],
        returns_matrix: dict[str, np.ndarray],
        hmm_features: np.ndarray,
        target_symbol: str = "BTCUSDT",
        current_price: float = 0.0,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """Process cross-sectional data for mean-reversion signals.

        Parameters
        ----------
        returns : dict[str, float]
            Current period returns for all symbols.
        returns_matrix : dict[str, np.ndarray]
            Historical returns arrays for TE computation.
        hmm_features : np.ndarray
            Feature vector [realized_vol, ofi_sign, funding_rate] for HMM.
        target_symbol : str
            Symbol to evaluate for entry (default BTCUSDT).
        current_price : float
            Current price of target symbol.
        ts : float | None
            Timestamp; defaults to time.time().

        Returns
        -------
        dict with action, direction, price, strategy, symbol, modules, reason.
        """
        if ts is None:
            ts = time.time()

        # ----------------------------------------------------------
        # 1. Compute all module outputs
        # ----------------------------------------------------------
        m13_out: dict[str, Any] = self.m13.compute(returns, ts)
        m17_out: dict[str, Any] = self.m17.compute(returns_matrix, "BTCUSDT", ts)
        m9_out: dict[str, Any] = self.m9.compute(hmm_features)

        modules: dict[str, Any] = {
            "M13": m13_out,
            "M17": m17_out,
            "M9": m9_out,
        }

        # ----------------------------------------------------------
        # 2. Exit logic (checked first)
        # ----------------------------------------------------------
        if self._in_trade:
            # Get current Z for the traded symbol
            z_scores: dict[str, float] = m13_out.get("z_scores", {})
            current_z: float = z_scores.get(self._entry_symbol, 0.0)
            current_hmm_state: int = m9_out.get("state", -1)

            exit_reason: str | None = self._check_exit(
                current_z, current_hmm_state, ts
            )
            if exit_reason is not None:
                direction_was: int = self._entry_direction
                symbol_was: str = self._entry_symbol
                self._in_trade = False
                self._entry_direction = 0
                self._entry_price = 0.0
                self._entry_ts = 0.0
                self._entry_symbol = ""
                self._entry_hmm_state = -1
                return {
                    "action": "exit",
                    "direction": direction_was,
                    "price": current_price,
                    "strategy": "S5",
                    "symbol": symbol_was,
                    "modules": modules,
                    "reason": exit_reason,
                }

        # ----------------------------------------------------------
        # 3. Entry logic
        # ----------------------------------------------------------
        wait_reason: str = "already_in_trade"
        if not self._in_trade:
            entry_ok, entry_reason, direction, symbol = self._check_entry(
                m13_out, m17_out, m9_out, target_symbol
            )
            if entry_ok:
                self._in_trade = True
                self._entry_price = current_price
                self._entry_direction = direction
                self._entry_ts = ts
                self._entry_symbol = symbol
                self._entry_hmm_state = m9_out.get("state", -1)
                return {
                    "action": "enter",
                    "direction": direction,
                    "price": current_price,
                    "strategy": "S5",
                    "symbol": symbol,
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
            "price": current_price,
            "strategy": "S5",
            "symbol": target_symbol,
            "modules": modules,
            "reason": wait_reason,
        }

    # ------------------------------------------------------------------
    # Entry conditions (PRD 7.5)
    # ------------------------------------------------------------------

    def _check_entry(
        self,
        m13_out: dict[str, Any],
        m17_out: dict[str, Any],
        m9_out: dict[str, Any],
        target_symbol: str,
    ) -> tuple[bool, str, int, str]:
        """Evaluate all entry conditions from PRD 7.5.

        Returns (True, reason, direction, symbol) or (False, reason, 0, "").
        """
        z_scores: dict[str, float] = m13_out.get("z_scores", {})
        extreme_symbols: list[dict[str, Any]] = m13_out.get("extreme_symbols", [])
        te_scores: dict[str, float] = m17_out.get("te_scores", {})
        hmm_state: int = m9_out.get("state", -1)

        # Condition 3 first (cheap): HMM state != HIGH_VOL (crash)
        if hmm_state == HIGH_VOL:
            return False, "hmm_high_vol_crash", 0, ""

        # Find best extreme symbol
        best_symbol: str = ""
        best_z: float = 0.0
        best_direction: int = 0

        for ext in extreme_symbols:
            sym: str = ext["symbol"]
            z: float = ext["z"]
            d: int = ext["direction"]

            # Condition 1: |Z| > 2.5
            if abs(z) <= S5_Z_ENTRY:
                continue

            # Condition 2: Renyi-TE(BTC -> Alt) > 0.05
            te_val: float = te_scores.get(sym, 0.0)
            if te_val <= RENYI_TE_THRESHOLD:
                continue

            # This symbol qualifies; track the most extreme
            if abs(z) > abs(best_z):
                best_z = z
                best_symbol = sym
                best_direction = d

        if not best_symbol:
            # Check target_symbol directly if not in extreme_symbols
            target_z: float = z_scores.get(target_symbol, 0.0)
            target_te: float = te_scores.get(target_symbol, 0.0)
            if abs(target_z) > S5_Z_ENTRY and target_te > RENYI_TE_THRESHOLD:
                best_symbol = target_symbol
                best_z = target_z
                best_direction = -1 if target_z > 0 else 1
            else:
                return False, "no_extreme_symbol_with_te", 0, ""

        return True, "all_conditions_met", best_direction, best_symbol

    # ------------------------------------------------------------------
    # Exit conditions (PRD 7.5)
    # ------------------------------------------------------------------

    def _check_exit(
        self,
        current_z: float,
        current_hmm_state: int,
        ts: float,
    ) -> str | None:
        """Evaluate exit conditions."""
        # Exit 1: |Z| < 0.5
        if abs(current_z) < S5_Z_EXIT:
            return "z_normalized"

        # Exit 2: Time-stop 24h
        elapsed: float = ts - self._entry_ts
        if elapsed >= _TIME_STOP_SECONDS:
            return "time_stop_24h"

        # Exit 3: HMM regime change
        if self._entry_hmm_state >= 0 and current_hmm_state != self._entry_hmm_state:
            return "hmm_regime_change"

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset_position_state(self) -> None:
        """Clear any in-flight position without touching learned/model state.

        Used at walk-forward fold boundaries (TRAIN -> TEST) to discard a
        position that was still open when TRAIN warmup ended, while
        preserving the warmed-up M13/M17/M9 state that TRAIN exists to
        build. Mirrors exactly the fields cleared on a normal exit in
        ``on_data`` above.
        """
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._entry_symbol = ""
        self._entry_hmm_state = -1

    def reset(self) -> None:
        """Reset all internal state."""
        self.m13.reset()
        self.m17.reset()
        self.m9.reset()
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._entry_symbol = ""
        self._entry_hmm_state = -1

    @property
    def in_trade(self) -> bool:
        """Whether the strategy currently holds a position."""
        return self._in_trade

    @property
    def entry_direction(self) -> int:
        """Direction of current trade: 1=Long, -1=Short, 0=none."""
        return self._entry_direction
