"""
M15 — Gutenberg-Richter b-Wert + Omori Aftershock Decay [L4] [Quick Win]

Seismologische Methoden angewandt auf Liquidations-Events.

Formeln (PRD):
    GR:    log10 N(>=M) = a - b*M
    b-Wert MLE (Aki 1965): b_hat = log10(e) / (M_bar - M_min)

    Omori: lambda(t) = K / (t - t_main + c)^p
    Mainshock: v_USD > Q99(rolling 24h)

Signal = 1 wenn Mainshock + Omori aktiv (Kaskaden-Risiko).
"""

from __future__ import annotations

import time
import warnings
from collections import deque
from typing import Any

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit

from bybit_edge.config import (
    GR_MAINSHOCK_QUANTILE,
    GR_MIN_EVENTS,
    OMORI_FORECAST_MINUTES,
)
from bybit_edge.layers.base import BaseModule

# Buffer for rolling 24h events (at ~1 event/s max, 86400 per day)
_EVENT_BUFFER_MAXLEN: int = 100_000

# Minimum aftershocks to attempt Omori fit
_MIN_AFTERSHOCKS_FOR_FIT: int = 5


class M15GROmori(BaseModule):
    """Gutenberg-Richter b-value + Omori aftershock decay on liquidation events.

    Applies seismological frequency-magnitude and aftershock-decay models
    to Bybit allLiquidation events to detect cascade risk.
    """

    def __init__(
        self,
        mainshock_quantile: float = GR_MAINSHOCK_QUANTILE,
        min_events: int = GR_MIN_EVENTS,
        omori_forecast_minutes: int = OMORI_FORECAST_MINUTES,
    ) -> None:
        self._mainshock_quantile: float = mainshock_quantile
        self._min_events: int = min_events
        self._omori_forecast_minutes: int = omori_forecast_minutes

        # Rolling event buffer: (timestamp_ms, usd_value)
        self._event_buffer: deque[tuple[int, float]] = deque(
            maxlen=_EVENT_BUFFER_MAXLEN
        )

        # Mainshock state
        self._mainshock_ts: float | None = None
        self._mainshock_usd: float = 0.0
        self._omori_params: dict[str, float] | None = None

    # ------------------------------------------------------------------
    # GR: Aki (1965) MLE b-value
    # ------------------------------------------------------------------

    @staticmethod
    def _aki_b_value(magnitudes: np.ndarray) -> float:
        """Compute the b-value via Aki (1965) maximum-likelihood estimator.

        b = log10(e) / (M_bar - M_min)

        Returns 1.0 as fallback when M_bar == M_min (degenerate case).
        """
        m_bar: float = float(np.mean(magnitudes))
        m_min: float = float(np.min(magnitudes))
        if m_bar <= m_min:
            return 1.0
        return np.log10(np.e) / (m_bar - m_min)

    # ------------------------------------------------------------------
    # Omori law
    # ------------------------------------------------------------------

    @staticmethod
    def _omori_fn(t: np.ndarray, K: float, c: float, p: float) -> np.ndarray:
        """Modified Omori law: lambda(t) = K / (t + c)^p."""
        return K / (t + c) ** p

    def _fit_omori(
        self, event_times_s: np.ndarray, mainshock_time_s: float
    ) -> dict[str, float] | None:
        """Fit Omori (K, c, p) to aftershock event times via curve_fit.

        Parameters
        ----------
        event_times_s : np.ndarray
            Timestamps of aftershocks in seconds.
        mainshock_time_s : float
            Timestamp of the mainshock in seconds.

        Returns
        -------
        dict with K, c, p or None if fit fails.
        """
        dt = event_times_s - mainshock_time_s
        dt = dt[dt > 0]  # only events after mainshock

        if len(dt) < _MIN_AFTERSHOCKS_FOR_FIT:
            return None

        # Build empirical rate: count events in 1-second bins
        dt_sorted = np.sort(dt)
        max_t = dt_sorted[-1]
        if max_t < 1.0:
            return None

        # Create bin edges and count
        n_bins = max(int(max_t), 1)
        bin_edges = np.arange(0, n_bins + 1, dtype=np.float64)
        counts, _ = np.histogram(dt_sorted, bins=bin_edges)

        # Use bin centers as time values, filter out zero-count bins
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        mask = counts > 0
        if mask.sum() < 3:
            return None

        t_data = bin_centers[mask]
        rate_data = counts[mask].astype(np.float64)

        try:
            # The Omori fit is valid even when scipy cannot estimate the
            # parameter covariance; suppress only that harmless OptimizeWarning
            # so it does not flood diagnostic output. Fit logic is unchanged.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", OptimizeWarning)
                popt, _ = curve_fit(
                    self._omori_fn,
                    t_data,
                    rate_data,
                    p0=[rate_data[0], 1.0, 1.0],
                    bounds=([0.0, 0.001, 0.5], [np.inf, np.inf, 2.5]),
                    maxfev=2000,
                )
            return {"K": float(popt[0]), "c": float(popt[1]), "p": float(popt[2])}
        except (RuntimeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self, liq_events: list[dict[str, Any]], current_ts: float
    ) -> dict[str, Any]:
        """Process liquidation events and compute GR + Omori analysis.

        Parameters
        ----------
        liq_events : list[dict]
            New liquidation events, each with keys:
            ``timestamp_ms`` (int), ``usd_value`` (float), ``side`` (str).
        current_ts : float
            Current timestamp in seconds (time.time()-compatible).

        Returns
        -------
        dict with b_value, b_low, mainshock, mainshock_ts, omori_active,
        aftershock_rate, omori_params, signal, method_id, confidence, ts.
        """
        # ----------------------------------------------------------
        # 1. Ingest new events
        # ----------------------------------------------------------
        for ev in liq_events:
            ts_ms: int = int(ev["timestamp_ms"])
            usd: float = float(ev["usd_value"])
            self._event_buffer.append((ts_ms, usd))

        # ----------------------------------------------------------
        # 2. Filter to last 24h
        # ----------------------------------------------------------
        # Vectorised single-pass over the buffer instead of repeatedly
        # rebuilding Python lists/arrays per compute() call. The buffer is a
        # bounded deque (maxlen 100k) and ``compute`` historically scanned it
        # several times per tick (one listcomp for ``recent`` plus two more to
        # build the usd arrays, plus a third for the aftershock times). On a
        # liquidation cascade S1 calls this every cadence tick, so those scans
        # dominated the per-tick cost. We materialise the (ts, usd) buffer into
        # two parallel ``float64`` arrays ONCE and slice with boolean masks; the
        # numeric results are bit-identical to the previous list-based path.
        cutoff_ms: int = int((current_ts - 86400) * 1000)
        if self._event_buffer:
            buf_ts = np.fromiter(
                (ts for ts, _ in self._event_buffer),
                dtype=np.int64,
                count=len(self._event_buffer),
            )
            buf_usd = np.fromiter(
                (usd for _, usd in self._event_buffer),
                dtype=np.float64,
                count=len(self._event_buffer),
            )
            recent_mask = buf_ts >= cutoff_ms
            recent_ts = buf_ts[recent_mask]
            recent_usd = buf_usd[recent_mask]
        else:
            recent_ts = np.empty(0, dtype=np.int64)
            recent_usd = np.empty(0, dtype=np.float64)

        n_recent: int = int(recent_ts.size)

        # ----------------------------------------------------------
        # 3. Compute magnitudes: M = log10(usd_value)
        # ----------------------------------------------------------
        b_value: float | None = None
        b_low: bool = False

        if n_recent >= self._min_events:
            usd_values = recent_usd[recent_usd > 0]  # safety: avoid log10(0)
            if len(usd_values) >= self._min_events:
                magnitudes = np.log10(usd_values)
                b_value = self._aki_b_value(magnitudes)
                # b < 1 indicates higher frequency of large events
                b_low = b_value < 1.0

        # ----------------------------------------------------------
        # 4. Mainshock detection: max_usd > Q99 of last 24h
        # ----------------------------------------------------------
        mainshock: bool = False

        if n_recent >= self._min_events:
            # Reuse the recent-usd array directly (the unfiltered values, to
            # match the previous behaviour where the Q99 quantile was computed
            # over ALL recent usd values, including any non-positive ones).
            q99 = float(np.quantile(recent_usd, self._mainshock_quantile))

            # Check new events only (from liq_events)
            for ev in liq_events:
                ev_usd = float(ev["usd_value"])
                if ev_usd > q99:
                    mainshock = True
                    ev_ts_s = int(ev["timestamp_ms"]) / 1000.0
                    # Update mainshock state if this is a larger one
                    if self._mainshock_ts is None or ev_usd > self._mainshock_usd:
                        self._mainshock_ts = ev_ts_s
                        self._mainshock_usd = ev_usd
                        self._omori_params = None  # will refit below

        # ----------------------------------------------------------
        # 5. Omori fit if mainshock active and within forecast window
        # ----------------------------------------------------------
        omori_active: bool = False
        aftershock_rate: float = 0.0

        if self._mainshock_ts is not None:
            elapsed_min = (current_ts - self._mainshock_ts) / 60.0

            if 0.0 < elapsed_min <= self._omori_forecast_minutes:
                # Attempt Omori fit on aftershock times. Vectorised mask over
                # the already-materialised recent arrays; identical to the prior
                # ``[ts/1000 for ts,_ in recent if ts/1000 > mainshock_ts]``.
                recent_ts_s = recent_ts / 1000.0
                aftershock_times = recent_ts_s[recent_ts_s > self._mainshock_ts]

                if len(aftershock_times) >= _MIN_AFTERSHOCKS_FOR_FIT:
                    fit = self._fit_omori(aftershock_times, self._mainshock_ts)
                    if fit is not None:
                        self._omori_params = fit
                        omori_active = True
                        # Predict rate at current time
                        dt_now = current_ts - self._mainshock_ts
                        aftershock_rate = self._omori_fn(
                            np.array([dt_now]),
                            fit["K"],
                            fit["c"],
                            fit["p"],
                        )[0]
            elif elapsed_min > self._omori_forecast_minutes:
                # Timeout: mainshock too old
                self._mainshock_ts = None
                self._mainshock_usd = 0.0
                self._omori_params = None

        # ----------------------------------------------------------
        # 6. Signal
        # ----------------------------------------------------------
        signal: int = 1 if (mainshock and omori_active) else 0
        confidence: float = 0.0
        if signal == 1 and self._omori_params is not None:
            # Higher p means faster decay, lower cascade risk —
            # confidence inversely scales with p
            p_val = self._omori_params.get("p", 1.0)
            confidence = min(max(1.0 / p_val, 0.0), 1.0)

        return {
            "b_value": b_value,
            "b_low": b_low,
            "mainshock": mainshock,
            "mainshock_ts": self._mainshock_ts,
            "omori_active": omori_active,
            "aftershock_rate": float(aftershock_rate),
            "omori_params": self._omori_params,
            "signal": signal,
            "method_id": "M15",
            "confidence": confidence,
            "ts": time.time(),
        }

    def validate(self) -> bool:
        """Check parameters are sane."""
        return (
            0.0 < self._mainshock_quantile < 1.0
            and self._min_events > 0
            and self._omori_forecast_minutes > 0
        )

    def reset(self) -> None:
        """Reset mainshock state and Omori fit."""
        self._mainshock_ts = None
        self._mainshock_usd = 0.0
        self._omori_params = None
        self._event_buffer.clear()
