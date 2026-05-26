"""
M14a — Hawkes 1-D Single Channel [L4]

Eigener Hawkes-Prozess ohne hawkeslib/tick.

Formeln (PRD, 1-D Variante):
    lambda(t) = mu + alpha * Sum_i beta * exp(-beta * (t - t_i))
    n_inf = alpha / beta  (branching ratio)
    Kritikalitaet: n_inf -> 1  <=>  Kaskade

MLE-Fit via scipy.optimize (L-BFGS-B).
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np
from scipy.optimize import minimize

from bybit_edge.config import (
    HAWKES_CRITICAL_RHO,
    HAWKES_REFIT_SECONDS,
    HAWKES_WINDOW_SECONDS,
)
from bybit_edge.layers.base import BaseModule

# Numerical floor
_EPS: float = 1e-300


class M14HawkesSingleChannel(BaseModule):
    """1-D Hawkes process for event cascade detection.

    Fits mu, alpha, beta via MLE on a rolling window of event timestamps
    and computes the branching ratio n = alpha / beta as criticality measure.
    """

    def __init__(
        self,
        window_seconds: float = HAWKES_WINDOW_SECONDS,
        refit_seconds: float = HAWKES_REFIT_SECONDS,
        critical_rho: float = HAWKES_CRITICAL_RHO,
    ) -> None:
        self.window_seconds: float = float(window_seconds)
        self.refit_seconds: float = float(refit_seconds)
        self.critical_rho: float = float(critical_rho)

        # Rolling event buffer
        self._events: deque[float] = deque()

        # Current parameters
        self._mu: float = 0.1
        self._alpha: float = 0.3
        self._beta: float = 1.0

        # Timestamp of last MLE fit
        self._last_fit_ts: float = 0.0

    @staticmethod
    def _intensity(
        t: float,
        events: np.ndarray,
        mu: float,
        alpha: float,
        beta: float,
    ) -> float:
        """Compute conditional intensity at time t.

        lambda(t) = mu + alpha * Sum_{t_i < t} beta * exp(-beta * (t - t_i))

        Parameters
        ----------
        t : float
            Query time (seconds).
        events : np.ndarray
            Array of event timestamps (seconds), sorted ascending.
        mu : float
            Background intensity.
        alpha : float
            Excitation magnitude.
        beta : float
            Decay rate.

        Returns
        -------
        float
            Conditional intensity lambda(t).
        """
        causal = events[events < t]
        if len(causal) == 0:
            return mu
        dt = t - causal
        kernel_sum = np.sum(beta * np.exp(-beta * dt))
        return mu + alpha * kernel_sum

    @staticmethod
    def _log_likelihood(
        events: np.ndarray,
        mu: float,
        alpha: float,
        beta: float,
    ) -> float:
        """Log-likelihood for a 1-D Hawkes process.

        LL = Sum_i log lambda(t_i)  -  integral_0^T lambda(t) dt

        Integral: mu * T + alpha * Sum_i (1 - exp(-beta * (T - t_i)))

        Parameters
        ----------
        events : np.ndarray
            Sorted event timestamps in [0, T].
        mu, alpha, beta : float
            Hawkes parameters.

        Returns
        -------
        float
            Log-likelihood value.
        """
        if len(events) < 2:
            return -np.inf

        T = events[-1] - events[0]
        if T <= 0:
            return -np.inf

        # Shift to [0, T]
        shifted = events - events[0]

        # Sum of log-intensities at each event
        ll_sum = 0.0
        # Use recursive computation for efficiency:
        # A_i = Sum_{j<i} exp(-beta*(t_i - t_j)) = exp(-beta*dt) * (A_{i-1} + 1)
        # but A_0 = 0 (first event has no history)
        A = 0.0
        for i in range(len(shifted)):
            if i == 0:
                lam_i = mu
            else:
                dt = shifted[i] - shifted[i - 1]
                A = np.exp(-beta * dt) * (A + 1.0)
                lam_i = mu + alpha * beta * A
            if lam_i < _EPS:
                lam_i = _EPS
            ll_sum += np.log(lam_i)

        # Integral of lambda over [0, T]
        integral = mu * T + alpha * np.sum(1.0 - np.exp(-beta * (T - shifted)))

        return ll_sum - integral

    def _fit_mle(self, events: np.ndarray) -> tuple[float, float, float]:
        """Fit Hawkes parameters via MLE using L-BFGS-B.

        Parameters
        ----------
        events : np.ndarray
            Sorted event timestamps.

        Returns
        -------
        tuple[float, float, float]
            Fitted (mu, alpha, beta).
        """
        if len(events) < 3:
            return self._mu, self._alpha, self._beta

        T = events[-1] - events[0]
        if T <= 0:
            return self._mu, self._alpha, self._beta

        # Objective: negative log-likelihood
        def neg_ll(params: np.ndarray) -> float:
            mu_p, alpha_p, beta_p = params
            val = self._log_likelihood(events, mu_p, alpha_p, beta_p)
            if not np.isfinite(val):
                return 1e12
            return -val

        # Starting point
        n_events = len(events)
        x0 = np.array([n_events / T, 0.5, 1.0])

        bounds = [
            (1e-6, None),   # mu > 0
            (1e-6, None),   # alpha > 0
            (1e-3, None),   # beta > 0
        ]

        try:
            result = minimize(
                neg_ll,
                x0,
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 200, "ftol": 1e-8},
            )
            if result.success or result.fun < neg_ll(x0):
                mu_opt, alpha_opt, beta_opt = result.x
                # Sanity: branching ratio should be < some large value
                if alpha_opt / beta_opt < 10.0:
                    return float(mu_opt), float(alpha_opt), float(beta_opt)
        except Exception:
            pass

        return self._mu, self._alpha, self._beta

    def compute(
        self,
        event_times: np.ndarray,
        current_ts: float,
    ) -> dict[str, Any]:
        """Compute Hawkes intensity and branching ratio.

        Parameters
        ----------
        event_times : np.ndarray
            Array of event timestamps (seconds, epoch or relative).
        current_ts : float
            Current timestamp for intensity evaluation.

        Returns
        -------
        dict
            Keys: branching_ratio, intensity, mu, alpha, beta,
            critical, signal, method_id, confidence, ts.
        """
        # Rolling window: keep only events within window
        cutoff = current_ts - self.window_seconds
        windowed = event_times[event_times >= cutoff]
        # Also only events before current_ts (causal)
        windowed = windowed[windowed <= current_ts]
        windowed = np.sort(windowed)

        # Update internal event buffer
        self._events = deque(windowed.tolist())

        # Re-fit if enough time has elapsed
        if len(windowed) >= 3 and (current_ts - self._last_fit_ts) >= self.refit_seconds:
            self._mu, self._alpha, self._beta = self._fit_mle(windowed)
            self._last_fit_ts = current_ts

        # Compute intensity at current time
        intensity = self._intensity(
            current_ts, windowed, self._mu, self._alpha, self._beta
        )

        # Branching ratio
        branching_ratio = self._alpha / max(self._beta, _EPS)

        # Criticality
        critical = branching_ratio > self.critical_rho
        signal = 1 if critical else 0

        # Confidence: scaled branching ratio, clipped to [0, 1]
        confidence = float(np.clip(branching_ratio, 0.0, 1.0))

        return {
            "branching_ratio": float(branching_ratio),
            "intensity": float(intensity),
            "mu": float(self._mu),
            "alpha": float(self._alpha),
            "beta": float(self._beta),
            "critical": critical,
            "signal": signal,
            "method_id": "M14",
            "confidence": confidence,
            "ts": time.time(),
        }

    def reset(self) -> None:
        """Reset all internal state."""
        self._events.clear()
        self._mu = 0.1
        self._alpha = 0.3
        self._beta = 1.0
        self._last_fit_ts = 0.0
