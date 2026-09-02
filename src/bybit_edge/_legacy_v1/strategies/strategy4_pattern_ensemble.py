# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Strategie 4 -- Pattern x Foundation Ensemble (PRD 7.4).

Methoden: M5 (FFD) + M16 (TFSAX+SW) + M18 (PatchTST) + M20 (MOMENT).

Entry-Bedingung:
    >= 2 von 3 Modellen (PatchTST, MOMENT, TFSAX) gleichgerichtet > 0.5%
    AND Pairwise-Forecast-Pearson > 0.6
    AND |TFSAX-Match-Score| > 0.75

Exit-Bedingung:
    Time-Stop bei forecast horizon
    OR Forecast-Update flippt Vorzeichen

Edge: Multi-Model-Konsens senkt idiosyncratic Forecast-Noise.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.config import (
    S4_CONSENSUS_MIN_MODELS,
    S4_FORECAST_PEARSON_MIN,
    S4_FORECAST_RETURN_MIN,
    TFSAX_MATCH_SCORE_THRESHOLD,
)
from bybit_edge._legacy_v1.layers.l2_denoising.m5_ffd import M5FFD
from bybit_edge._legacy_v1.layers.l4_pattern.m16_tfsax_sw import M16TFSAXSW
from bybit_edge._legacy_v1.layers.l4_pattern.m18_patchtst import M18PatchTST
from bybit_edge._legacy_v1.layers.l4_pattern.m20_moment import M20MOMENT

# Default forecast horizon for time-stop (in ticks/updates)
_DEFAULT_HORIZON_TICKS: int = 60


class Strategy4PatternEnsemble:
    """Pattern x Foundation Ensemble Strategy.

    Combines three orthogonal pattern-recognition engines and only trades
    when at least 2 of 3 agree on direction and magnitude, pairwise
    forecast correlation exceeds 0.6, and TFSAX match score is strong.
    """

    def __init__(self, horizon_ticks: int = _DEFAULT_HORIZON_TICKS) -> None:
        self.m5: M5FFD = M5FFD()
        self.m16: M16TFSAXSW = M16TFSAXSW()
        self.m18: M18PatchTST = M18PatchTST()
        self.m20: M20MOMENT = M20MOMENT()

        self._in_trade: bool = False
        self._entry_price: float = 0.0
        self._entry_direction: int = 0
        self._entry_ts: float = 0.0
        self._ticks_since_entry: int = 0
        self._horizon_ticks: int = horizon_ticks

        # Store last forecast directions for exit flip detection
        self._last_consensus_direction: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_data(
        self,
        price_series: np.ndarray,
        library: list[dict[str, Any]] | None = None,
        current_price: float | None = None,
        ts: float | None = None,
    ) -> dict[str, Any]:
        """Process price data through all pattern models.

        Parameters
        ----------
        price_series : np.ndarray
            Recent close prices (e.g. 512+ bars).
        library : list[dict] | None
            Historical TFSAX library segments.
        current_price : float | None
            Current price; if None, uses last element of price_series.
        ts : float | None
            Timestamp; defaults to time.time().

        Returns
        -------
        dict with action, direction, price, strategy, modules, reason.
        """
        if ts is None:
            ts = time.time()
        if current_price is None:
            current_price = float(price_series[-1]) if len(price_series) > 0 else 0.0

        # ----------------------------------------------------------
        # 1. FFD preprocessing
        # ----------------------------------------------------------
        m5_out: dict[str, Any] = self.m5.compute(price_series)

        # ----------------------------------------------------------
        # 2. Compute all pattern model outputs
        # ----------------------------------------------------------
        m16_out: dict[str, Any] = self.m16.compute(
            query_series=price_series, library=library, ts=ts
        )
        m18_out: dict[str, Any] = self.m18.compute(price_series)
        m20_out: dict[str, Any] = self.m20.compute(price_series)

        modules: dict[str, Any] = {
            "M5": m5_out,
            "M16": m16_out,
            "M18": m18_out,
            "M20": m20_out,
        }

        # Extract forecast directions and magnitudes
        patchtst_dir: int = m18_out.get("forecast_direction", 0)
        moment_dir: int = m20_out.get("forecast_direction", 0)
        tfsax_dir: int = m16_out.get("signal", 0)
        tfsax_score: float = m16_out.get("match_score", 0.0)

        patchtst_mag: float = m18_out.get("forecast_magnitude", 0.0)
        moment_mag: float = m20_out.get("confidence", 0.0)

        # Build forecasts for pairwise correlation
        patchtst_forecast: np.ndarray = np.asarray(
            m18_out.get("forecast", np.array([])), dtype=np.float64
        )
        moment_forecast: np.ndarray = np.asarray(
            m20_out.get("forecast", np.array([])), dtype=np.float64
        )

        # ----------------------------------------------------------
        # Track ticks for time-stop
        # ----------------------------------------------------------
        if self._in_trade:
            self._ticks_since_entry += 1

        # ----------------------------------------------------------
        # 2. Exit logic (checked first)
        # ----------------------------------------------------------
        if self._in_trade:
            exit_reason: str | None = self._check_exit(
                patchtst_dir, moment_dir, tfsax_dir
            )
            if exit_reason is not None:
                direction_was: int = self._entry_direction
                self._in_trade = False
                self._entry_direction = 0
                self._entry_price = 0.0
                self._entry_ts = 0.0
                self._ticks_since_entry = 0
                self._last_consensus_direction = 0
                return {
                    "action": "exit",
                    "direction": direction_was,
                    "price": current_price,
                    "strategy": "S4",
                    "modules": modules,
                    "reason": exit_reason,
                }

        # ----------------------------------------------------------
        # 3. Entry logic
        # ----------------------------------------------------------
        wait_reason: str = "already_in_trade"
        if not self._in_trade:
            entry_ok, entry_reason, direction = self._check_entry(
                patchtst_dir, moment_dir, tfsax_dir,
                patchtst_mag, moment_mag,
                tfsax_score,
                patchtst_forecast, moment_forecast,
            )
            if entry_ok:
                self._in_trade = True
                self._entry_price = current_price
                self._entry_direction = direction
                self._entry_ts = ts
                self._ticks_since_entry = 0
                self._last_consensus_direction = direction
                return {
                    "action": "enter",
                    "direction": direction,
                    "price": current_price,
                    "strategy": "S4",
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
            "strategy": "S4",
            "modules": modules,
            "reason": wait_reason,
        }

    # ------------------------------------------------------------------
    # Entry conditions (PRD 7.4)
    # ------------------------------------------------------------------

    def _check_entry(
        self,
        patchtst_dir: int,
        moment_dir: int,
        tfsax_dir: int,
        patchtst_mag: float,
        moment_mag: float,
        tfsax_score: float,
        patchtst_forecast: np.ndarray,
        moment_forecast: np.ndarray,
    ) -> tuple[bool, str, int]:
        """Evaluate all entry conditions from PRD 7.4.

        Returns (True, reason, direction) or (False, reason, 0).
        """
        # Model directions (only count those with sufficient magnitude)
        models = []
        if patchtst_dir != 0 and patchtst_mag >= S4_FORECAST_RETURN_MIN:
            models.append(patchtst_dir)
        if moment_dir != 0 and moment_mag >= S4_FORECAST_RETURN_MIN:
            models.append(moment_dir)
        if tfsax_dir != 0:
            models.append(tfsax_dir)

        # Condition 1: >= 2 of 3 models agree on direction
        if len(models) < S4_CONSENSUS_MIN_MODELS:
            return False, "insufficient_models", 0

        direction_sum: int = sum(models)
        # Count how many agree with majority
        if direction_sum > 0:
            consensus_dir: int = 1
        elif direction_sum < 0:
            consensus_dir = -1
        else:
            return False, "no_consensus_direction", 0

        agree_count: int = sum(1 for m in models if m == consensus_dir)
        if agree_count < S4_CONSENSUS_MIN_MODELS:
            return False, "consensus_below_minimum", 0

        # Condition 2: Pairwise forecast Pearson > 0.6
        pearson_ok = self._check_pairwise_pearson(
            patchtst_forecast, moment_forecast
        )
        if not pearson_ok:
            return False, "pearson_below_threshold", 0

        # Condition 3: |TFSAX match score| > 0.75
        if tfsax_score < TFSAX_MATCH_SCORE_THRESHOLD:
            return False, "tfsax_score_below_threshold", 0

        return True, "all_conditions_met", consensus_dir

    @staticmethod
    def _check_pairwise_pearson(
        forecast_a: np.ndarray, forecast_b: np.ndarray
    ) -> bool:
        """Check if pairwise Pearson correlation exceeds threshold."""
        min_len: int = min(len(forecast_a), len(forecast_b))
        if min_len < 3:
            return False

        a = forecast_a[:min_len]
        b = forecast_b[:min_len]

        std_a: float = float(np.std(a))
        std_b: float = float(np.std(b))
        if std_a < 1e-12 or std_b < 1e-12:
            return False

        corr: float = float(np.corrcoef(a, b)[0, 1])
        if np.isnan(corr):
            return False

        return corr > S4_FORECAST_PEARSON_MIN

    # ------------------------------------------------------------------
    # Exit conditions (PRD 7.4)
    # ------------------------------------------------------------------

    def _check_exit(
        self,
        patchtst_dir: int,
        moment_dir: int,
        tfsax_dir: int,
    ) -> str | None:
        """Evaluate exit conditions."""
        # Exit 1: Time-stop at forecast horizon
        if self._ticks_since_entry >= self._horizon_ticks:
            return "time_stop"

        # Exit 2: Forecast update flips sign
        current_dirs = [d for d in [patchtst_dir, moment_dir, tfsax_dir] if d != 0]
        if current_dirs and self._last_consensus_direction != 0:
            dir_sum = sum(current_dirs)
            new_consensus: int = 1 if dir_sum > 0 else (-1 if dir_sum < 0 else 0)
            if new_consensus != 0 and new_consensus != self._last_consensus_direction:
                return "forecast_flip"

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset_position_state(self) -> None:
        """Clear any in-flight position without touching learned/model state.

        Used at walk-forward fold boundaries (TRAIN -> TEST) to discard a
        position that was still open when TRAIN warmup ended, while
        preserving the warmed-up M5/M16/M18/M20 state that TRAIN exists to
        build. Mirrors exactly the fields cleared on a normal exit in
        ``on_data`` above.
        """
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._ticks_since_entry = 0
        self._last_consensus_direction = 0

    def reset(self) -> None:
        """Reset all internal state."""
        self.m5 = M5FFD()
        self.m16 = M16TFSAXSW()
        self.m18.reset()
        self.m20.reset()
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._ticks_since_entry = 0
        self._last_consensus_direction = 0
        self._horizon_ticks = _DEFAULT_HORIZON_TICKS

    @property
    def in_trade(self) -> bool:
        """Whether the strategy currently holds a position."""
        return self._in_trade

    @property
    def entry_direction(self) -> int:
        """Direction of current trade: 1=Long, -1=Short, 0=none."""
        return self._entry_direction
