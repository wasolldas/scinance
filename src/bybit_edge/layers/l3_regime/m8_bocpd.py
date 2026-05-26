"""
M8 — Bayesian Online Changepoint Detection (BOCPD) auf openInterest [L3] [Quick Win]

Implementiert Adams & MacKay 2007 vollständig ohne externe Libraries.

Formeln (PRD):
    P(r_t | x_{1:t}) ∝ Σ_{r_{t-1}} P(r_t | r_{t-1}) · P(x_t | r_{t-1}, x) · P(r_{t-1} | x_{1:t-1})
    Hazard h(r) = 1/λ  (konstante geometrische Run-Length-Verteilung)
    Predictive: P(x_t | r_{t-1}, x) = Student-t (für unbekannte Varianz)

Changepoint wird detektiert wenn P(r_t = 0) > threshold (0.5).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.special import gammaln

from bybit_edge.config import (
    BOCPD_CHANGE_POINT_THRESHOLD,
    BOCPD_HAZARD_LAMBDA,
)
from bybit_edge.layers.base import BaseModule


class M8BOCPD(BaseModule):
    """Bayesian Online Changepoint Detection nach Adams & MacKay (2007).

    Erkennt Strukturbrüche in openInterest-Zeitreihen über einen
    Online-Bayes-Algorithmus mit Student-t Predictive Distribution.
    """

    def __init__(
        self,
        hazard_lambda: float = BOCPD_HAZARD_LAMBDA,
        prior_mean: float = 0.0,
        prior_var: float = 1.0,
        threshold: float = BOCPD_CHANGE_POINT_THRESHOLD,
    ) -> None:
        self._hazard_lambda: float = hazard_lambda
        self._threshold: float = threshold

        # Prior hyperparameters for Normal-Inverse-Gamma conjugate
        self._prior_mu: float = prior_mean
        self._prior_kappa: float = 1.0  # pseudo-observations for mean
        self._prior_alpha: float = 1.0  # shape (nu/2)
        self._prior_beta: float = prior_var  # scale

        # Run-length posterior: R[i] = P(r_t = i | x_{1:t})
        self._R: np.ndarray = np.array([1.0])

        # Sufficient statistics for each run-length hypothesis
        # Each index corresponds to a run-length r = 0, 1, 2, ...
        self._mu: np.ndarray = np.array([self._prior_mu])
        self._kappa: np.ndarray = np.array([self._prior_kappa])
        self._alpha: np.ndarray = np.array([self._prior_alpha])
        self._beta: np.ndarray = np.array([self._prior_beta])

        self._t: int = 0

    # ------------------------------------------------------------------
    # Internal: Hazard function
    # ------------------------------------------------------------------

    def _hazard(self, r: np.ndarray) -> np.ndarray:
        """Constant hazard function: H(r) = 1/lambda for all r."""
        return np.full_like(r, 1.0 / self._hazard_lambda, dtype=np.float64)

    # ------------------------------------------------------------------
    # Internal: Student-t predictive PDF
    # ------------------------------------------------------------------

    @staticmethod
    def _student_t_logpdf(
        x: float, mu: np.ndarray, var: np.ndarray, nu: np.ndarray
    ) -> np.ndarray:
        """Log-PDF of the Student-t predictive distribution.

        Parameters
        ----------
        x : float
            Observed data point.
        mu : np.ndarray
            Location parameters (one per run-length hypothesis).
        var : np.ndarray
            Scale parameters (sigma^2, one per run-length).
        nu : np.ndarray
            Degrees of freedom (2 * alpha, one per run-length).
        """
        # Student-t: p(x|mu,var,nu) with variance var*(nu/(nu-2))
        # Using scipy.special.gammaln for numerical stability
        nu_safe = np.maximum(nu, 1e-8)
        var_safe = np.maximum(var, 1e-300)

        log_num = gammaln((nu_safe + 1.0) / 2.0)
        log_den = (
            gammaln(nu_safe / 2.0)
            + 0.5 * np.log(nu_safe * np.pi * var_safe)
        )
        log_body = -(nu_safe + 1.0) / 2.0 * np.log(
            1.0 + (x - mu) ** 2 / (nu_safe * var_safe)
        )
        return log_num - log_den + log_body

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, x: float) -> dict[str, Any]:
        """Process one observation and return changepoint analysis.

        Parameters
        ----------
        x : float
            New data point (e.g., delta-openInterest or OI value).

        Returns
        -------
        dict with changepoint, changepoint_prob, run_length_map,
        signal, method_id, confidence, ts.
        """
        self._t += 1

        # ----------------------------------------------------------
        # 1. Predictive probabilities under each run-length
        # ----------------------------------------------------------
        nu = 2.0 * self._alpha  # degrees of freedom
        var = self._beta * (self._kappa + 1.0) / (self._kappa * self._alpha)

        log_pred = self._student_t_logpdf(x, self._mu, var, nu)
        pred_probs = np.exp(log_pred)

        # ----------------------------------------------------------
        # 2. Hazard for each current run-length
        # ----------------------------------------------------------
        r_vals = np.arange(len(self._R), dtype=np.float64)
        H = self._hazard(r_vals)

        # ----------------------------------------------------------
        # 3. Growth and changepoint probabilities
        # ----------------------------------------------------------
        growth_probs = self._R * pred_probs * (1.0 - H)
        cp_prob = np.sum(self._R * pred_probs * H)

        # ----------------------------------------------------------
        # 4. Build new run-length distribution
        # ----------------------------------------------------------
        new_R = np.empty(len(self._R) + 1, dtype=np.float64)
        new_R[0] = cp_prob           # changepoint: r_t = 0
        new_R[1:] = growth_probs     # growth: r_t = r_{t-1} + 1

        # Normalize
        evidence = new_R.sum()
        if evidence > 0:
            new_R /= evidence

        self._R = new_R

        # ----------------------------------------------------------
        # 5. Update sufficient statistics (Normal-Inverse-Gamma)
        # ----------------------------------------------------------
        new_mu = np.empty(len(self._R), dtype=np.float64)
        new_kappa = np.empty(len(self._R), dtype=np.float64)
        new_alpha = np.empty(len(self._R), dtype=np.float64)
        new_beta = np.empty(len(self._R), dtype=np.float64)

        # r = 0 (changepoint): reset to prior
        new_mu[0] = self._prior_mu
        new_kappa[0] = self._prior_kappa
        new_alpha[0] = self._prior_alpha
        new_beta[0] = self._prior_beta

        # r > 0 (growth): Bayesian update of NIG parameters
        old_mu = self._mu
        old_kappa = self._kappa
        old_alpha = self._alpha
        old_beta = self._beta

        new_kappa[1:] = old_kappa + 1.0
        new_mu[1:] = (old_kappa * old_mu + x) / new_kappa[1:]
        new_alpha[1:] = old_alpha + 0.5
        new_beta[1:] = (
            old_beta
            + 0.5 * old_kappa * (x - old_mu) ** 2 / new_kappa[1:]
        )

        self._mu = new_mu
        self._kappa = new_kappa
        self._alpha = new_alpha
        self._beta = new_beta

        # ----------------------------------------------------------
        # 6. Extract results
        # ----------------------------------------------------------
        changepoint_prob: float = float(self._R[0])
        changepoint: bool = changepoint_prob > self._threshold
        run_length_map: int = int(np.argmax(self._R))
        signal: int = 1 if changepoint else 0
        confidence: float = min(changepoint_prob, 1.0) if changepoint else 0.0

        return {
            "changepoint": changepoint,
            "changepoint_prob": changepoint_prob,
            "run_length_map": run_length_map,
            "signal": signal,
            "method_id": "M8",
            "confidence": confidence,
            "ts": time.time(),
        }

    def validate(self) -> bool:
        """Check that hazard lambda is positive."""
        return self._hazard_lambda > 0 and self._threshold > 0

    def reset(self) -> None:
        """Reset run-length distribution and sufficient statistics to priors."""
        self._R = np.array([1.0])
        self._mu = np.array([self._prior_mu])
        self._kappa = np.array([self._prior_kappa])
        self._alpha = np.array([self._prior_alpha])
        self._beta = np.array([self._prior_beta])
        self._t = 0
