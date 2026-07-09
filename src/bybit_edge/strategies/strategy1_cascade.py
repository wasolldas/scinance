# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Strategie 1 -- Seismischer Cascade Detector (PRD 7.1).

Methoden: M14 (Hawkes rho) + M15 (GR/Omori) + M26 (SIR) + M25 (Kyle Lambda fuer Sizing).

Entry-Bedingung:
    rho(Phi) > 0.85 (steigend, d_rho/dt > 0)
    AND b-Wert < b_bar_30d - 2*sigma  (grossbeben-prone)
    AND Omori-Aftershock-Phase aktiv (Mainshock < 30 min)
    AND SIR-R0 > 1.0
    Direction = entgegengesetzt zur Liquidations-Seite
                (Long-Liqs -> Long nach Klimax)

Exit-Bedingung:
    rho(Phi) < 0.5
    OR Omori-Decay-Phase (t > 5*c)
    OR OI-Recovery > 95% des Pre-Cascade-Niveaus

Edge: Mean-Reversion nach Liquidations-Klimax.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

from bybit_edge.config import (
    S1_B_ZSCORE,
    S1_OMORI_DECAY_FACTOR,
    S1_RHO_ENTRY,
    S1_RHO_EXIT,
    SIR_R0_CASCADE_THRESHOLD,
)
from bybit_edge.layers.l4_pattern.m14_hawkes import M14HawkesSingleChannel
from bybit_edge.layers.l4_pattern.m15_gr_omori import M15GROmori
from bybit_edge.layers.l5_risk.m25_kyle_lambda import M25KyleLambda
from bybit_edge.layers.l5_risk.m26_sir import M26SIR

# Rolling b-value history for z-score calculation (30d at ~1/min ~ 43200)
_B_HISTORY_MAXLEN: int = 43_200

# Minimum b-value samples for z-score
_MIN_B_SAMPLES: int = 50


class Strategy1CascadeDetector:
    """Seismischer Cascade Detector.

    Combines Hawkes spectral radius, GR/Omori aftershock statistics,
    and SIR contagion to detect and trade mean-reversion after
    liquidation cascades.
    """

    def __init__(self) -> None:
        self.m14: M14HawkesSingleChannel = M14HawkesSingleChannel()
        self.m15: M15GROmori = M15GROmori()
        self.m25: M25KyleLambda = M25KyleLambda()
        self.m26: M26SIR = M26SIR()

        self._in_trade: bool = False
        self._entry_price: float = 0.0
        self._entry_direction: int = 0
        self._entry_ts: float = 0.0
        self._pre_cascade_oi: float = 0.0

        # rho history for d_rho/dt
        self._rho_history: deque[float] = deque(maxlen=10)

        # b-value history for z-score
        self._b_history: deque[float] = deque(maxlen=_B_HISTORY_MAXLEN)

        # Iter-4 Push A T2: opt-in rho-distribution instrumentation.
        # Lazily allocated on the first _check_entry call when the flag is
        # ON. Stays None when the flag is OFF -> zero overhead.
        self._rho_samples: deque[float] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_data(
        self,
        liq_events: list[dict[str, Any]],
        event_times: np.ndarray,
        open_interest: float,
        trades: list[dict[str, Any]],
        current_ts: float,
        liq_side: str = "Long",
    ) -> dict[str, Any]:
        """Process liquidation and trade data to generate cascade signals.

        Parameters
        ----------
        liq_events : list[dict]
            Liquidation events with timestamp_ms, usd_value, side, volume.
        event_times : np.ndarray
            Array of liquidation event timestamps in seconds.
        open_interest : float
            Current open interest.
        trades : list[dict]
            Recent trades for Kyle's Lambda (price, volume, side, timestamp_ms).
        current_ts : float
            Current timestamp (seconds).
        liq_side : str
            Dominant liquidation side ("Long" or "Short").

        Returns
        -------
        dict with action, direction, price, strategy, modules, reason.
        """
        # ----------------------------------------------------------
        # 1. Compute all module outputs
        # ----------------------------------------------------------
        m14_out: dict[str, Any] = self.m14.compute(event_times, current_ts)
        m15_out: dict[str, Any] = self.m15.compute(liq_events, current_ts)
        m25_out: dict[str, Any] = self.m25.compute(trades)
        m26_out: dict[str, Any] = self.m26.compute(
            liq_events, open_interest, current_ts
        )

        modules: dict[str, Any] = {
            "M14": m14_out,
            "M15": m15_out,
            "M25": m25_out,
            "M26": m26_out,
        }

        rho: float = m14_out["branching_ratio"]

        # Track rho for derivative
        self._rho_history.append(rho)

        # Track b-value for z-score
        if m15_out["b_value"] is not None:
            self._b_history.append(m15_out["b_value"])

        # ----------------------------------------------------------
        # 2. Exit logic (checked first)
        # ----------------------------------------------------------
        if self._in_trade:
            exit_reason: str | None = self._check_exit(
                m14_out, m15_out, open_interest, current_ts
            )
            if exit_reason is not None:
                direction_was: int = self._entry_direction
                self._in_trade = False
                self._entry_direction = 0
                self._entry_price = 0.0
                self._entry_ts = 0.0
                return {
                    "action": "exit",
                    "direction": direction_was,
                    "price": 0.0,
                    "strategy": "S1",
                    "modules": modules,
                    "reason": exit_reason,
                }

        # ----------------------------------------------------------
        # 3. Entry logic
        # ----------------------------------------------------------
        wait_reason: str = "already_in_trade"
        if not self._in_trade:
            entry_ok, entry_reason = self._check_entry(
                m14_out, m15_out, m26_out
            )
            if entry_ok:
                # Direction: opposite to liquidation side
                # Long liquidations -> market crashed -> go Long (reversion)
                # Short liquidations -> market pumped -> go Short (reversion)
                direction: int = 1 if liq_side == "Long" else -1
                self._in_trade = True
                self._entry_direction = direction
                # Event time, not wall clock: in replay this is the simulated
                # tick time; live it equals time.time() (behaviour-neutral).
                self._entry_ts = current_ts
                self._pre_cascade_oi = open_interest
                return {
                    "action": "enter",
                    "direction": direction,
                    "price": 0.0,
                    "strategy": "S1",
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
            "price": 0.0,
            "strategy": "S1",
            "modules": modules,
            "reason": wait_reason,
        }

    # ------------------------------------------------------------------
    # Entry conditions (PRD 7.1)
    # ------------------------------------------------------------------

    def _check_entry(
        self,
        m14_out: dict[str, Any],
        m15_out: dict[str, Any],
        m26_out: dict[str, Any],
    ) -> tuple[bool, str]:
        """Evaluate all four entry conditions from PRD 7.1."""
        rho: float = m14_out["branching_ratio"]

        # Iter-4 Push A T2: opt-in rho-distribution instrumentation.
        # Captured BEFORE the short-circuit below so the sample population
        # includes the (typically dominant) rho_below_threshold ticks.
        # Lazy config import + lazy buffer alloc keep the flag-off path
        # bit-identical to iter-3.
        from bybit_edge import config as _cfg
        if _cfg.S1_RHO_INSTRUMENT_ENABLED:
            if self._rho_samples is None:
                self._rho_samples = deque(
                    maxlen=_cfg.S1_RHO_INSTRUMENT_MAXLEN
                )
            self._rho_samples.append(float(rho))

        # Condition 1: rho > 0.85 AND rising (d_rho/dt > 0)
        if rho <= S1_RHO_ENTRY:
            return False, "rho_below_threshold"

        if len(self._rho_history) >= 2:
            d_rho = self._rho_history[-1] - self._rho_history[-2]
            if d_rho <= 0:
                return False, "rho_not_rising"

        # Condition 2: b-value < b_bar_30d - 2*sigma
        b_val = m15_out.get("b_value")
        if b_val is None:
            return False, "b_value_unavailable"

        if not self._is_b_value_extreme(b_val):
            return False, "b_value_not_extreme"

        # Condition 3: Omori aftershock phase active
        if not m15_out["omori_active"]:
            return False, "omori_not_active"

        # Condition 4: SIR R0 > 1.0
        r0: float = m26_out["r0"]
        if r0 <= SIR_R0_CASCADE_THRESHOLD:
            return False, "r0_below_threshold"

        return True, "all_conditions_met"

    def _is_b_value_extreme(self, b_val: float) -> bool:
        """Check if b-value is below mean - 2*sigma (large events dominant)."""
        if len(self._b_history) < _MIN_B_SAMPLES:
            return False
        b_arr = np.array(list(self._b_history), dtype=np.float64)
        b_mean: float = float(np.mean(b_arr))
        b_std: float = float(np.std(b_arr))
        if b_std < 1e-12:
            return False
        return b_val < b_mean - S1_B_ZSCORE * b_std

    # ------------------------------------------------------------------
    # Exit conditions (PRD 7.1)
    # ------------------------------------------------------------------

    def _check_exit(
        self,
        m14_out: dict[str, Any],
        m15_out: dict[str, Any],
        open_interest: float,
        current_ts: float,
    ) -> str | None:
        """Evaluate exit conditions.

        ``current_ts`` is the CURRENT EVENT TIME (seconds) as passed to
        ``on_data`` — the simulation clock in replay, wall clock live.
        """
        rho: float = m14_out["branching_ratio"]

        # Exit 1: rho < 0.5
        if rho < S1_RHO_EXIT:
            return "rho_decay"

        # Exit 2: Omori decay phase (t > 5*c)
        #
        # BUGFIX (2026-07-09, CRITICAL_REVIEW causality-wallclock-in-replay):
        # elapsed was previously computed as ``time.time() - mainshock_ts``.
        # In historical replays ``mainshock_ts`` is event time weeks/months in
        # the past while ``time.time()`` is the real wall clock, so elapsed was
        # always huge (~1e5..1e7 s) and every replayed S1 position was force-
        # closed on the very first in-trade tick ("omori_decay"). Using the
        # caller-supplied ``current_ts`` is correct in BOTH contexts: replay
        # (simulation time) and live (current_ts ~= time.time()).
        omori_params = m15_out.get("omori_params")
        if omori_params is not None and m15_out.get("mainshock_ts") is not None:
            c_val: float = omori_params.get("c", 1.0)
            elapsed: float = current_ts - m15_out["mainshock_ts"]
            if elapsed > S1_OMORI_DECAY_FACTOR * c_val:
                return "omori_decay"

        # Exit 3: OI recovery > 95%
        if self._pre_cascade_oi > 0 and open_interest > 0:
            recovery_pct: float = open_interest / self._pre_cascade_oi
            if recovery_pct > 0.95:
                return "oi_recovery"

        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all internal state."""
        self.m14 = M14HawkesSingleChannel()
        self.m15.reset()
        self.m25.reset()
        self.m26.reset()
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0
        self._entry_ts = 0.0
        self._pre_cascade_oi = 0.0
        self._rho_history.clear()
        self._b_history.clear()
        # Iter-4 Push A T2: drop any collected instrumentation samples so a
        # post-reset replay does not commingle samples across runs.
        if self._rho_samples is not None:
            self._rho_samples.clear()

    def dump_rho_distribution(
        self, symbol: str, out_dir: Path
    ) -> Path | None:
        """Write the captured rho-sample distribution as JSON.

        Iter-4 Push A T2 instrumentation flush. Returns the written path or
        ``None`` if no samples were collected (flag was off, or strategy
        was never driven). Output file:
        ``out_dir / f"rho_distribution_{symbol}.json"``.
        """
        if self._rho_samples is None or len(self._rho_samples) == 0:
            return None
        arr = np.asarray(list(self._rho_samples), dtype=np.float64)
        quantiles = {
            "min": float(arr.min()),
            "p10": float(np.quantile(arr, 0.10)),
            "p25": float(np.quantile(arr, 0.25)),
            "p50": float(np.quantile(arr, 0.50)),
            "p75": float(np.quantile(arr, 0.75)),
            "p90": float(np.quantile(arr, 0.90)),
            "p95": float(np.quantile(arr, 0.95)),
            "p99": float(np.quantile(arr, 0.99)),
            "max": float(arr.max()),
        }
        payload: dict[str, Any] = {
            "symbol": symbol,
            "n_samples": int(arr.size),
            "threshold": float(S1_RHO_ENTRY),
            "quantiles": quantiles,
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"rho_distribution_{symbol}.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out_path

    @property
    def in_trade(self) -> bool:
        """Whether the strategy currently holds a position."""
        return self._in_trade

    @property
    def entry_direction(self) -> int:
        """Direction of current trade: 1=Long, -1=Short, 0=none."""
        return self._entry_direction
