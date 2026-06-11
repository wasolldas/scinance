"""Metrics for the C-42 vol repro (WP-4): OOS-R^2, QLIKE, FDR over 36 features.

- ``oos_r2``         — out-of-sample R^2 against the realised target.
- ``qlike``          — the QLIKE loss on the *variance* scale, the standard
  volatility-forecast loss that is robust to a noisy vol proxy
  (Patton 2011). Lower is better; H-02 requires the model's QLIKE to BEAT
  the HAR-RV baseline's QLIKE in every OOS fold.
- ``permutation_importance`` — model-agnostic feature importance + a
  permutation p-value per feature (the importance test we feed to FDR).
- ``benjamini_hochberg`` — BH step-up procedure at alpha = 0.10 over the
  36-feature family F-VOL (H-02 FDR family).

P-value choice (documented per WP-4): we use **permutation importance** with a
permutation-null p-value rather than a linear F-test, because the
reproduction-faithful model is a gradient-boosted tree (LightGBM) whose feature
effects are non-linear and an F-test would mis-state significance. The p-value
of feature j is the fraction of permutations whose degradation in OOS-R^2 is
>= the observed degradation (one-sided), with a +1/+1 add-one correction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

#: Variance floor on the QLIKE scale — guards log(0)/division on flat windows.
_VAR_FLOOR = 1e-12

#: FDR family alpha for F-VOL (H-02, BH).
FDR_ALPHA = 0.10


def oos_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Out-of-sample R^2 = 1 - SS_res/SS_tot (on the log-vol target scale)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot <= 0.0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def qlike(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> float:
    """QLIKE loss on the variance scale.

    Targets/predictions arrive as ``log(realised_vol)``; QLIKE is defined on
    variance, so we map vol = exp(log_vol), variance = vol^2:

        QLIKE = mean( sigma2_true / sigma2_pred - log(sigma2_true / sigma2_pred) - 1 )

    Lower is better; QLIKE >= 0 with equality iff perfect forecast. Robust to a
    noisy realised-vol proxy (Patton 2011).
    """
    var_true = np.exp(np.asarray(y_true_log, dtype=float)) ** 2
    var_pred = np.exp(np.asarray(y_pred_log, dtype=float)) ** 2
    var_true = np.clip(var_true, _VAR_FLOOR, None)
    var_pred = np.clip(var_pred, _VAR_FLOOR, None)
    ratio = var_true / var_pred
    return float(np.mean(ratio - np.log(ratio) - 1.0))


@dataclass(frozen=True)
class PermImportance:
    """Permutation-importance result for one feature."""

    feature: str
    importance: float  # mean OOS-R^2 drop when the column is shuffled
    p_value: float     # permutation-null one-sided p-value


def permutation_importance(
    model: "object",
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str],
    n_repeats: int = 20,
    seed: int = 42,
) -> list[PermImportance]:
    """Model-agnostic permutation importance + permutation p-value per feature.

    For each feature column we shuffle it ``n_repeats`` times and measure the
    drop in OOS-R^2 vs. the unshuffled baseline. Importance = mean drop. The
    p-value is the add-one-corrected fraction of shuffles whose drop is <= 0
    (i.e. the feature looked useless), giving a one-sided test of "this feature
    matters". Deterministic given ``seed``.
    """
    rng = np.random.default_rng(seed)
    base_pred = model.predict(X_test)  # type: ignore[attr-defined]
    base_r2 = oos_r2(y_test, base_pred)
    out: list[PermImportance] = []
    for j, name in enumerate(feature_names):
        drops = np.empty(n_repeats, dtype=float)
        for rep in range(n_repeats):
            Xp = X_test.copy()
            rng.shuffle(Xp[:, j])
            r2_perm = oos_r2(y_test, model.predict(Xp))  # type: ignore[attr-defined]
            drops[rep] = base_r2 - r2_perm
        importance = float(np.mean(drops))
        # one-sided permutation p-value: how often the feature looked irrelevant
        n_nonpos = int(np.sum(drops <= 0.0))
        p_value = (n_nonpos + 1) / (n_repeats + 1)
        out.append(PermImportance(name, importance, p_value))
    return out


@dataclass(frozen=True)
class FDRResult:
    """Benjamini-Hochberg outcome over the F-VOL feature family."""

    alpha: float
    n_features: int
    n_significant: int
    threshold_p: float  # largest p that passed BH (0.0 if none passed)
    significant_features: list[str]
    rejected: dict[str, bool]  # feature -> significant?


def benjamini_hochberg(
    p_values: dict[str, float], alpha: float = FDR_ALPHA
) -> FDRResult:
    """BH step-up FDR control at ``alpha`` over the feature family.

    Standard procedure: sort p ascending, find the largest k with
    p_(k) <= (k/m) * alpha, reject all hypotheses with p <= p_(k).
    """
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(items)
    if m == 0:
        return FDRResult(alpha, 0, 0, 0.0, [], {})
    threshold_p = 0.0
    k_max = 0
    for k, (_, p) in enumerate(items, start=1):
        if p <= (k / m) * alpha:
            threshold_p = p
            k_max = k
    rejected = {name: (p <= threshold_p and k_max > 0) for name, p in items}
    significant = [name for name, rej in rejected.items() if rej]
    return FDRResult(
        alpha=alpha,
        n_features=m,
        n_significant=len(significant),
        threshold_p=threshold_p,
        significant_features=significant,
        rejected=rejected,
    )
