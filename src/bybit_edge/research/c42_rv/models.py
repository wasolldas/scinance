"""Vol-model adapter layer for the C-42 repro (WP-4, DEC-04).

A thin ``VolModel`` protocol (fit/predict) keeps the estimator swappable, so
the pipeline runs in three regimes:

- ``HARRVBaseline``  — classical HAR-RV (Corsi 2009) via numpy/stdlib OLS.
  Has NO third-party model dependency and runs ALWAYS, including in the
  code-only sandbox. This is the baseline that H-02's QLIKE test must beat.
- ``HistGBMVolModel`` — sklearn ``HistGradientBoostingRegressor`` fallback
  (DEC-04a escape hatch). Import-guarded: a missing scikit-learn raises a
  clean ImportError pointing at ``pip install -e .[vol]``.
- ``LightGBMVolModel`` — the original Kestrel estimator (DEC-04). Import-guarded
  the same way; lightgbm is absent from the sandbox by design, so the import
  error must be actionable, never a bare ModuleNotFoundError at fit time.

Reproduction fidelity (DEC-04): LightGBM is the reproduction-faithful model;
HistGBM and HAR are the always-available substitutes the gate-auditor must be
told about when LightGBM could not be built locally.

All randomised estimators take an explicit ``seed`` (default 42) — no implicit
RNG state.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

import numpy as np

DEFAULT_SEED = 42

_VOL_EXTRA_HINT = (
    "install the optional vol stack: `pip install -e .[vol]` "
    "(adds lightgbm>=4.0 + scikit-learn>=1.4)"
)


@runtime_checkable
class VolModel(Protocol):
    """Minimal estimator contract used by the pipeline."""

    name: str

    def fit(self, X: np.ndarray, y: np.ndarray) -> "VolModel":
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        ...

    def feature_importance(self) -> Optional[np.ndarray]:
        """Per-feature importance (gain) or ``None`` if not applicable."""
        ...


class HARRVBaseline:
    """Classical HAR-RV baseline (Corsi 2009) — numpy OLS, always available.

    Regresses the target ``log(realised_vol_60m)`` on three HAR regressors built
    from the feature matrix: a "daily", "weekly" and "monthly" realised-vol
    aggregate. To stay self-contained the regressors are taken directly from the
    feature columns the pipeline passes in (see ``har_feature_indices``); when
    those indices are not supplied it falls back to the first three columns.

    OLS with intercept via the normal equations / lstsq. No external model dep.
    """

    name = "har"

    def __init__(self, har_feature_indices: Optional[tuple[int, ...]] = None) -> None:
        self.har_feature_indices = har_feature_indices
        self._beta: Optional[np.ndarray] = None
        self._idx: Optional[tuple[int, ...]] = None

    def _design(self, X: np.ndarray) -> np.ndarray:
        if self._idx is None:
            k = min(3, X.shape[1])
            self._idx = tuple(range(k)) if self.har_feature_indices is None \
                else self.har_feature_indices
        cols = X[:, list(self._idx)]
        # log-transform the (positive) RV regressors to match the log target
        # scale; guard non-positive values from synthetic flats.
        cols = np.log(np.clip(cols, 1e-12, None))
        intercept = np.ones((X.shape[0], 1))
        return np.hstack([intercept, cols])

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HARRVBaseline":
        A = self._design(X)
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        self._beta = beta
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._beta is None:
            raise RuntimeError("HARRVBaseline.predict called before fit")
        return self._design(X) @ self._beta

    def feature_importance(self) -> Optional[np.ndarray]:
        return None  # HAR is the baseline; importance/FDR runs on the GBM model


class HistGBMVolModel:
    """sklearn HistGradientBoostingRegressor adapter (DEC-04a fallback)."""

    name = "histgbm"

    def __init__(self, seed: int = DEFAULT_SEED, **kwargs: object) -> None:
        try:
            from sklearn.ensemble import HistGradientBoostingRegressor
        except ImportError as exc:  # pragma: no cover - exercised by guard test
            raise ImportError(
                f"HistGBMVolModel needs scikit-learn; {_VOL_EXTRA_HINT}"
            ) from exc
        self.seed = seed
        params: dict[str, object] = dict(
            max_iter=300,
            learning_rate=0.05,
            max_depth=6,
            l2_regularization=1.0,
            random_state=seed,
        )
        params.update(kwargs)
        self._model = HistGradientBoostingRegressor(**params)
        self._importance: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HistGBMVolModel":
        self._model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def feature_importance(self) -> Optional[np.ndarray]:
        # HistGBM has no native gain importance; the pipeline uses
        # permutation importance (metrics.permutation_importance) instead.
        return None


class LightGBMVolModel:
    """LightGBM regressor adapter — reproduction-faithful estimator (DEC-04)."""

    name = "lightgbm"

    def __init__(self, seed: int = DEFAULT_SEED, **kwargs: object) -> None:
        try:
            import lightgbm as lgb
        except ImportError as exc:  # pragma: no cover - lightgbm absent in sandbox
            raise ImportError(
                "LightGBMVolModel needs lightgbm (the reproduction-faithful "
                f"estimator per DEC-04); {_VOL_EXTRA_HINT}"
            ) from exc
        self._lgb = lgb
        self.seed = seed
        params: dict[str, object] = dict(
            objective="regression",
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=63,
            max_depth=-1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=seed,
            n_jobs=-1,
            verbosity=-1,
        )
        params.update(kwargs)
        self._model = lgb.LGBMRegressor(**params)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LightGBMVolModel":
        self._model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X)

    def feature_importance(self) -> Optional[np.ndarray]:
        # Native gain importance — matches research_notes' "35.8% gain" ranking.
        return np.asarray(self._model.booster_.feature_importance(importance_type="gain"),
                          dtype=float)


#: Registry consumed by the CLI ``--model`` flag.
MODEL_REGISTRY: dict[str, type] = {
    "har": HARRVBaseline,
    "histgbm": HistGBMVolModel,
    "lightgbm": LightGBMVolModel,
}


def build_model(name: str, seed: int = DEFAULT_SEED) -> VolModel:
    """Instantiate a model by name; raises ImportError with the [vol] hint."""
    if name not in MODEL_REGISTRY:
        raise ValueError(f"unknown model '{name}'; choose from {sorted(MODEL_REGISTRY)}")
    cls = MODEL_REGISTRY[name]
    if name == "har":
        return cls()  # type: ignore[return-value]
    return cls(seed=seed)  # type: ignore[return-value]
