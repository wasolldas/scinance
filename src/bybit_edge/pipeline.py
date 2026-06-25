# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Asynchrone 5-Layer-Pipeline (PRD Section 5).

L1 (Ingestion) -> trigger -> L2 (Denoising wenn Spike)
L3 (Regime, permanent) -> Greenlight -> L4 (Pattern)
L5 (Risk, vor jeder Execution) -> Decision Aggregator -> Signal

Verarbeitet Ticker-Daten und produziert finale Handelssignale.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.decision_aggregator import DecisionAggregator

# --- L1: Ingestion ---
from bybit_edge.layers.l1_ingestion.m2_ofi import M2OFI

# --- L2: Denoising ---
from bybit_edge.layers.l2_denoising.m4_wavelet import M4WaveletDenoiser
from bybit_edge.layers.l2_denoising.m5_ffd import M5FFD

# --- L3: Regime ---
from bybit_edge.layers.l3_regime.m6_entropy import M6ShannonEntropy
from bybit_edge.layers.l3_regime.m7_permutation_entropy import M7PermutationEntropy
from bybit_edge.layers.l3_regime.m8_bocpd import M8BOCPD
from bybit_edge.layers.l3_regime.m9_hmm import M9HMM

# --- L4: Pattern ---
from bybit_edge.layers.l4_pattern.m14_hawkes import M14HawkesSingleChannel
from bybit_edge.layers.l4_pattern.m15_gr_omori import M15GROmori

# --- L5: Risk ---
from bybit_edge.layers.l5_risk.m22_funding_pressure import M22FundingPressure
from bybit_edge.layers.l5_risk.m23_basis_convergence import M23BasisConvergence
from bybit_edge.layers.l5_risk.m24_kalman_premium import M24KalmanPremium
from bybit_edge.layers.l5_risk.m25_kyle_lambda import M25KyleLambda
from bybit_edge.layers.l5_risk.m26_sir import M26SIR

# --- Strategies ---
from bybit_edge.strategies.strategy1_cascade import Strategy1CascadeDetector
from bybit_edge.strategies.strategy2_entropy_momentum import Strategy2EntropyMomentum
from bybit_edge.strategies.strategy3_pre_settlement import Strategy3PreSettlement
from bybit_edge.strategies.strategy4_pattern_ensemble import Strategy4PatternEnsemble
from bybit_edge.strategies.strategy5_cross_sectional import Strategy5CrossSectional


class Pipeline:
    """5-Layer pipeline orchestrator.

    Instantiates all modules and strategies, processes ticker data
    through the cascade, and produces final trading decisions via
    the Decision Aggregator.
    """

    def __init__(self, symbol: str = "BTCUSDT") -> None:
        self.symbol: str = symbol

        # ----- L1: Ingestion -----
        self.m2: M2OFI = M2OFI()

        # ----- L2: Denoising -----
        self.m4: M4WaveletDenoiser = M4WaveletDenoiser()
        self.m5: M5FFD = M5FFD()

        # ----- L3: Regime -----
        self.m6: M6ShannonEntropy = M6ShannonEntropy()
        self.m7: M7PermutationEntropy = M7PermutationEntropy()
        self.m8: M8BOCPD = M8BOCPD()
        self.m9: M9HMM = M9HMM()

        # ----- L4: Pattern -----
        self.m14: M14HawkesSingleChannel = M14HawkesSingleChannel()
        self.m15: M15GROmori = M15GROmori()

        # ----- L5: Risk -----
        self.m22: M22FundingPressure = M22FundingPressure()
        self.m23: M23BasisConvergence = M23BasisConvergence()
        self.m24: M24KalmanPremium = M24KalmanPremium()
        self.m25: M25KyleLambda = M25KyleLambda()
        self.m26: M26SIR = M26SIR()

        # ----- Strategies -----
        self.strategy1: Strategy1CascadeDetector = Strategy1CascadeDetector()
        self.strategy2: Strategy2EntropyMomentum = Strategy2EntropyMomentum()
        self.strategy3: Strategy3PreSettlement = Strategy3PreSettlement()
        self.strategy4: Strategy4PatternEnsemble = Strategy4PatternEnsemble()
        self.strategy5: Strategy5CrossSectional = Strategy5CrossSectional()

        # ----- Aggregator -----
        self.aggregator: DecisionAggregator = DecisionAggregator()

    async def process_ticker(self, ticker_data: dict[str, Any]) -> dict[str, Any] | None:
        """Process a ticker update through the full pipeline.

        Parameters
        ----------
        ticker_data : dict
            Must contain at minimum:
            - last_price, mark_price, index_price
            - premium_index, funding_rate
            - open_interest
            - seconds_to_settlement
            - bid_sizes (np.ndarray), ask_sizes (np.ndarray)
            - best_bid (tuple), best_ask (tuple)
            Optional:
            - liq_events (list), event_times (np.ndarray)
            - trades (list)
            - price_series (np.ndarray)
            - returns (dict), returns_matrix (dict)

        Returns
        -------
        dict | None
            Final aggregated decision, or None if no signal.
        """
        ts: float = ticker_data.get("ts", time.time())
        price: float = float(ticker_data.get("last_price", 0.0))
        open_interest: float = float(ticker_data.get("open_interest", 0.0))
        seconds_to_settlement: float = float(
            ticker_data.get("seconds_to_settlement", 3600.0)
        )

        # Defaults for optional fields
        bid_sizes: np.ndarray = np.asarray(
            ticker_data.get("bid_sizes", np.ones(20)), dtype=np.float64
        )
        ask_sizes: np.ndarray = np.asarray(
            ticker_data.get("ask_sizes", np.ones(20)), dtype=np.float64
        )
        best_bid: tuple[float, float] = ticker_data.get("best_bid", (price - 1.0, 1.0))
        best_ask: tuple[float, float] = ticker_data.get("best_ask", (price + 1.0, 1.0))
        liq_events: list[dict[str, Any]] = ticker_data.get("liq_events", [])
        event_times: np.ndarray = np.asarray(
            ticker_data.get("event_times", np.array([])), dtype=np.float64
        )
        trades: list[dict[str, Any]] = ticker_data.get("trades", [])
        price_series: np.ndarray = np.asarray(
            ticker_data.get("price_series", np.array([price])), dtype=np.float64
        )

        # ==============================================================
        # L3: Regime Ensemble (always runs)
        # ==============================================================
        l3_entropy: dict[str, Any] = self.m6.compute(bid_sizes, ask_sizes)
        l3_pe: dict[str, Any] = self.m7.update(price)
        l3_bocpd: dict[str, Any] = self.m8.compute(open_interest)
        l3_hmm: dict[str, Any] = self.m9.compute(
            np.array([0.02, 0.0, float(ticker_data.get("funding_rate", 0.0))])
        )

        # Greenlight: entropy collapse OR PE greenlight
        greenlight: bool = l3_entropy.get("greenlight", False) or l3_pe.get("greenlight", False)

        l3_regime: dict[str, Any] = {
            "greenlight": greenlight,
            "entropy": l3_entropy,
            "pe": l3_pe,
            "bocpd": l3_bocpd,
            "hmm": l3_hmm,
        }

        # ==============================================================
        # L4: Pattern (gated by L3 greenlight)
        # ==============================================================
        l4_pattern: dict[str, Any] = {"greenlight_active": greenlight}
        if greenlight:
            l4_hawkes: dict[str, Any] = self.m14.compute(event_times, ts)
            l4_gr_omori: dict[str, Any] = self.m15.compute(liq_events, ts)
            l4_pattern["hawkes"] = l4_hawkes
            l4_pattern["gr_omori"] = l4_gr_omori

        # ==============================================================
        # L5: Risk (always runs before execution)
        # ==============================================================
        l5_m22: dict[str, Any] = self.m22.compute(ticker_data, seconds_to_settlement)
        l5_m23: dict[str, Any] = self.m23.compute(ticker_data, seconds_to_settlement)
        l5_m24: dict[str, Any] = self.m24.compute(ticker_data)
        l5_m25: dict[str, Any] = self.m25.compute(trades)
        l5_m26: dict[str, Any] = self.m26.compute(liq_events, open_interest, ts)

        l5_risk: dict[str, Any] = {
            "M22": l5_m22,
            "M23": l5_m23,
            "M24": l5_m24,
            "M25": l5_m25,
            "M26": l5_m26,
        }

        # ==============================================================
        # Strategy Evaluation
        # ==============================================================
        strategy_signals: list[dict[str, Any]] = []

        # S1: Cascade Detector (always active when liq_events present)
        if liq_events:
            s1_signal: dict[str, Any] = self.strategy1.on_data(
                liq_events=liq_events,
                event_times=event_times,
                open_interest=open_interest,
                trades=trades,
                current_ts=ts,
            )
            # Add confidence from modules
            s1_confidence = max(
                l4_pattern.get("hawkes", {}).get("confidence", 0.0),
                l5_m26.get("confidence", 0.0),
            )
            s1_signal["confidence"] = s1_confidence
            strategy_signals.append(s1_signal)

        # S2: Entropy Momentum (needs greenlight)
        if greenlight:
            s2_signal: dict[str, Any] = self.strategy2.on_ticker(
                bid_sizes=bid_sizes,
                ask_sizes=ask_sizes,
                best_bid=best_bid,
                best_ask=best_ask,
                ticker_data=ticker_data,
                seconds_to_settlement=seconds_to_settlement,
                price=price,
                ts=ts,
            )
            s2_conf = max(
                l3_entropy.get("confidence", 0.0),
                l3_pe.get("confidence", 0.0),
            )
            s2_signal.setdefault("confidence", s2_conf)
            strategy_signals.append(s2_signal)

        # S3: Pre-Settlement (always active)
        s3_signal: dict[str, Any] = self.strategy3.on_ticker(
            ticker_data=ticker_data,
            seconds_to_settlement=seconds_to_settlement,
            open_interest=open_interest,
            ts=ts,
        )
        s3_signal.setdefault("confidence", l5_m22.get("confidence", 0.0))
        strategy_signals.append(s3_signal)

        # S4: Pattern Ensemble (needs greenlight + price_series)
        if greenlight and len(price_series) > 10:
            s4_signal: dict[str, Any] = self.strategy4.on_data(
                price_series=price_series,
                library=ticker_data.get("tfsax_library"),
                current_price=price,
                ts=ts,
            )
            s4_signal.setdefault("confidence", 0.0)
            strategy_signals.append(s4_signal)

        # S5: Cross-Sectional (needs multi-symbol data)
        returns: dict[str, float] = ticker_data.get("returns", {})
        returns_matrix: dict[str, np.ndarray] = ticker_data.get("returns_matrix", {})
        if returns and returns_matrix:
            hmm_features: np.ndarray = np.array([
                0.02,
                0.0,
                float(ticker_data.get("funding_rate", 0.0)),
            ])
            s5_signal: dict[str, Any] = self.strategy5.on_data(
                returns=returns,
                returns_matrix=returns_matrix,
                hmm_features=hmm_features,
                target_symbol=self.symbol,
                current_price=price,
                ts=ts,
            )
            s5_signal.setdefault("confidence", 0.0)
            strategy_signals.append(s5_signal)

        # ==============================================================
        # Decision Aggregator
        # ==============================================================
        if not strategy_signals:
            return None

        decision: dict[str, Any] = self.aggregator.aggregate(
            strategy_signals=strategy_signals,
            kyle_lambda=l5_m25,
            sir=l5_m26,
        )

        # Enrich output
        decision["ts"] = ts
        decision["symbol"] = self.symbol
        decision["regime"] = l3_regime
        decision["risk"] = l5_risk

        if decision.get("action") == "wait":
            return None

        return decision

    def reset(self) -> None:
        """Reset all modules and strategies."""
        self.m2.reset()
        self.m4.reset()
        self.m5.reset()
        self.m6.reset()
        self.m7.reset()
        self.m8.reset()
        self.m9.reset()
        self.m14.reset()
        self.m15.reset()
        self.m22.reset()
        self.m23.reset()
        self.m24.reset()
        self.m25.reset()
        self.m26.reset()
        self.strategy1.reset()
        self.strategy2.reset()
        self.strategy3.reset()
        self.strategy4.reset()
        self.strategy5.reset()
