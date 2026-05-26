"""
M9 — HMM Vola-OFI-Funding (3-State) [L3]

Eigener Forward-Algorithmus ohne hmmlearn.

Formeln (PRD):
    P(z_t | x_{1:t}) ~ Sum_{z_{t-1}} P(z_t | z_{t-1}) * P(x_t | z_t) * alpha_{t-1}(z_{t-1})
    Forward: alpha_t(z) = P(x_t | z) * Sum_{z'} P(z | z') * alpha_{t-1}(z')

States: TREND_UP=0, MEAN_REVERT=1, HIGH_VOL=2
Features: [realized_vol_5min, sign(OFI_5min), funding_rate]
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.config import (
    HMM_N_STATES,
    HMM_RETRAIN_DAYS,
    HMM_TRAIN_MONTHS,
)
from bybit_edge.layers.base import BaseModule

# State labels
TREND_UP: int = 0
MEAN_REVERT: int = 1
HIGH_VOL: int = 2

_STATE_LABELS: dict[int, str] = {
    TREND_UP: "TREND_UP",
    MEAN_REVERT: "MEAN_REVERT",
    HIGH_VOL: "HIGH_VOL",
}

# Signal mapping
_STATE_SIGNALS: dict[int, int] = {
    TREND_UP: 1,
    MEAN_REVERT: 0,
    HIGH_VOL: -1,
}

# Numerical floor for log-space stability
_LOG_EPS: float = 1e-300


class M9HMM(BaseModule):
    """Hidden Markov Model with 3 states for regime detection.

    Uses a custom forward algorithm with diagonal-covariance Gaussian
    emissions on 3 observable features: realized_vol, sign(OFI), funding_rate.

    Initialization via k-means clustering on training data, followed by
    a single Baum-Welch EM iteration for refinement.
    """

    def __init__(
        self,
        n_states: int = HMM_N_STATES,
        retrain_days: int = HMM_RETRAIN_DAYS,
        train_months: int = HMM_TRAIN_MONTHS,
    ) -> None:
        self.n_states: int = n_states
        self.retrain_days: int = retrain_days
        self.train_months: int = train_months
        self.n_features: int = 3  # vol, ofi_sign, funding

        # Transition matrix: high diagonal for state persistence
        self.transition_matrix: np.ndarray = self._default_transition()

        # Emission parameters per state: means and variances (diagonal cov)
        # Defaults: state 0 (TREND_UP): low vol, positive OFI, near-zero funding
        #           state 1 (MEAN_REVERT): medium vol, ~0 OFI, near-zero funding
        #           state 2 (HIGH_VOL): high vol, negative OFI, extreme funding
        self.emission_means: np.ndarray = np.array([
            [0.01, 0.5, 0.0001],    # TREND_UP
            [0.02, 0.0, 0.0000],    # MEAN_REVERT
            [0.05, -0.3, 0.0005],   # HIGH_VOL
        ], dtype=np.float64)

        self.emission_vars: np.ndarray = np.array([
            [0.001, 0.5, 0.0001],
            [0.001, 0.5, 0.0001],
            [0.005, 0.5, 0.0005],
        ], dtype=np.float64)

        # State prior (uniform)
        self.state_prior: np.ndarray = np.ones(n_states, dtype=np.float64) / n_states

        # Current forward vector
        self._alpha: np.ndarray = self.state_prior.copy()

        # Fitted flag
        self._fitted: bool = False

    def _default_transition(self) -> np.ndarray:
        """Create default transition matrix with high self-transition."""
        off_diag = 0.025
        diag = 1.0 - off_diag * (self.n_states - 1)
        A = np.full((self.n_states, self.n_states), off_diag, dtype=np.float64)
        np.fill_diagonal(A, diag)
        return A

    def _gaussian_emission(self, x: np.ndarray, state: int) -> float:
        """Multivariate Gaussian likelihood with diagonal covariance.

        Parameters
        ----------
        x : np.ndarray
            Observation vector of shape (n_features,).
        state : int
            State index (0, 1, or 2).

        Returns
        -------
        float
            Likelihood P(x | state).
        """
        mu = self.emission_means[state]
        var = self.emission_vars[state]
        # Clamp variance to avoid division by zero
        var = np.maximum(var, 1e-12)
        d = len(mu)
        diff = x - mu
        exponent = -0.5 * np.sum(diff**2 / var)
        norm_const = (2.0 * np.pi) ** (d / 2.0) * np.prod(np.sqrt(var))
        likelihood = np.exp(exponent) / max(norm_const, _LOG_EPS)
        return max(float(likelihood), _LOG_EPS)

    def _forward_step(self, x: np.ndarray) -> np.ndarray:
        """Single forward-algorithm step.

        alpha_t(z) = P(x|z) * Sum_{z'} P(z|z') * alpha_{t-1}(z')

        Parameters
        ----------
        x : np.ndarray
            Observation vector of shape (n_features,).

        Returns
        -------
        np.ndarray
            Normalised forward vector of shape (n_states,).
        """
        # Prediction: Sum_{z'} A[z', z] * alpha_{t-1}(z')  for each z
        predicted = self.transition_matrix.T @ self._alpha  # shape (n_states,)

        # Update: multiply by emission probability
        alpha_new = np.empty(self.n_states, dtype=np.float64)
        for z in range(self.n_states):
            alpha_new[z] = self._gaussian_emission(x, z) * predicted[z]

        # Normalise
        total = alpha_new.sum()
        if total > 0:
            alpha_new /= total
        else:
            alpha_new = np.ones(self.n_states, dtype=np.float64) / self.n_states

        self._alpha = alpha_new
        return alpha_new

    def fit(self, features: np.ndarray) -> None:
        """Fit HMM parameters using k-means initialisation + 1 EM round.

        Parameters
        ----------
        features : np.ndarray
            Training data of shape (N, 3) with columns
            [realized_vol, ofi_sign, funding_rate].
        """
        N = features.shape[0]
        if N < self.n_states:
            return

        # --- K-means initialisation (simple, max 50 iterations) ---
        rng = np.random.default_rng(42)
        # Pick initial centroids from data
        idx = rng.choice(N, size=self.n_states, replace=False)
        centroids = features[idx].copy()

        labels = np.zeros(N, dtype=np.int64)
        for _ in range(50):
            # Assign
            dists = np.array([
                np.sum((features - centroids[k]) ** 2, axis=1)
                for k in range(self.n_states)
            ])  # shape (n_states, N)
            new_labels = np.argmin(dists, axis=0)
            if np.array_equal(new_labels, labels):
                labels = new_labels
                break
            labels = new_labels
            # Update centroids
            for k in range(self.n_states):
                mask = labels == k
                if mask.sum() > 0:
                    centroids[k] = features[mask].mean(axis=0)

        # Sort states by volatility (column 0) ascending:
        # lowest vol = TREND_UP, middle = MEAN_REVERT, highest = HIGH_VOL
        vol_order = np.argsort(centroids[:, 0])
        label_map = np.empty(self.n_states, dtype=np.int64)
        for new_idx, old_idx in enumerate(vol_order):
            label_map[old_idx] = new_idx
        labels = label_map[labels]
        centroids = centroids[vol_order]

        # Emission parameters from clusters
        for k in range(self.n_states):
            mask = labels == k
            if mask.sum() > 1:
                self.emission_means[k] = features[mask].mean(axis=0)
                self.emission_vars[k] = features[mask].var(axis=0) + 1e-8
            elif mask.sum() == 1:
                self.emission_means[k] = features[mask][0]
                self.emission_vars[k] = np.full(self.n_features, 1e-4)

        # Transition matrix from label sequences
        A = np.zeros((self.n_states, self.n_states), dtype=np.float64)
        for t in range(1, N):
            A[labels[t - 1], labels[t]] += 1.0
        # Normalise rows (add small prior to avoid zeros)
        A += 1e-3
        row_sums = A.sum(axis=1, keepdims=True)
        self.transition_matrix = A / row_sums

        # --- Single Baum-Welch EM iteration for refinement ---
        # Forward pass
        alphas = np.zeros((N, self.n_states), dtype=np.float64)
        # Initialise with prior
        for z in range(self.n_states):
            alphas[0, z] = self._gaussian_emission(features[0], z) * self.state_prior[z]
        s = alphas[0].sum()
        if s > 0:
            alphas[0] /= s
        scales = np.zeros(N, dtype=np.float64)
        scales[0] = s if s > 0 else 1.0

        for t in range(1, N):
            for z in range(self.n_states):
                pred = 0.0
                for zp in range(self.n_states):
                    pred += self.transition_matrix[zp, z] * alphas[t - 1, zp]
                alphas[t, z] = self._gaussian_emission(features[t], z) * pred
            s = alphas[t].sum()
            if s > 0:
                alphas[t] /= s
            scales[t] = s if s > 0 else 1.0

        # Backward pass
        betas = np.zeros((N, self.n_states), dtype=np.float64)
        betas[N - 1] = 1.0
        for t in range(N - 2, -1, -1):
            for z in range(self.n_states):
                for zn in range(self.n_states):
                    betas[t, z] += (
                        self.transition_matrix[z, zn]
                        * self._gaussian_emission(features[t + 1], zn)
                        * betas[t + 1, zn]
                    )
            s = betas[t].sum()
            if s > 0:
                betas[t] /= s

        # Gamma (posterior state probabilities)
        gamma = alphas * betas
        gamma_sums = gamma.sum(axis=1, keepdims=True)
        gamma_sums = np.maximum(gamma_sums, _LOG_EPS)
        gamma /= gamma_sums

        # Update emission parameters
        for k in range(self.n_states):
            w = gamma[:, k]
            w_sum = w.sum()
            if w_sum > 1e-8:
                self.emission_means[k] = (w[:, None] * features).sum(axis=0) / w_sum
                diff = features - self.emission_means[k]
                self.emission_vars[k] = (w[:, None] * diff**2).sum(axis=0) / w_sum + 1e-8

        # Update transition matrix (xi)
        A_new = np.zeros((self.n_states, self.n_states), dtype=np.float64)
        for t in range(N - 1):
            for i in range(self.n_states):
                for j in range(self.n_states):
                    xi_val = (
                        alphas[t, i]
                        * self.transition_matrix[i, j]
                        * self._gaussian_emission(features[t + 1], j)
                        * betas[t + 1, j]
                    )
                    A_new[i, j] += xi_val
        # Normalise
        A_new += 1e-6
        row_sums = A_new.sum(axis=1, keepdims=True)
        self.transition_matrix = A_new / row_sums

        self._fitted = True
        # Reset alpha to prior for online inference
        self._alpha = self.state_prior.copy()

    def compute(self, features: np.ndarray) -> dict[str, Any]:
        """Compute regime state from a single observation.

        Parameters
        ----------
        features : np.ndarray
            Observation vector of shape (3,) or (1, 3):
            [realized_vol_5min, sign(OFI_5min), funding_rate].

        Returns
        -------
        dict
            Keys: state, state_label, state_probs, signal, method_id,
            confidence, ts.
        """
        if features.ndim == 2:
            features = features[0]

        alpha = self._forward_step(features)
        map_state: int = int(np.argmax(alpha))
        confidence: float = float(alpha[map_state])

        return {
            "state": map_state,
            "state_label": _STATE_LABELS[map_state],
            "state_probs": alpha.tolist(),
            "signal": _STATE_SIGNALS[map_state],
            "method_id": "M9",
            "confidence": confidence,
            "ts": time.time(),
        }

    def reset(self) -> None:
        """Reset forward vector to uniform prior."""
        self._alpha = self.state_prior.copy()
