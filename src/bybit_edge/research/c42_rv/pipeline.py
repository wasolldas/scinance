"""End-to-end C-42 vol-regression repro pipeline (WP-4).

Wires features -> target -> purged walk-forward -> model fit/predict ->
per-fold OOS-R^2 + QLIKE (model vs HAR baseline) -> permutation importance ->
BH-FDR over the 36-feature F-VOL family. Emits a machine-readable result dict
and a German Markdown report that lists the H-02 criteria one by one.

The final WEITER/DROP gate verdict is intentionally NOT decided here — that is
the gate-auditor's job against the registered H-02 entry. The pipeline reports
each criterion's measured value and a non-binding pre-check.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import pandas as pd

from .features import FEATURE_PROVENANCE, FeatureSpec, build_features, feature_names
from .metrics import (
    FDR_ALPHA,
    benjamini_hochberg,
    oos_r2,
    permutation_importance,
    qlike,
)
from .models import DEFAULT_SEED, HARRVBaseline, build_model
from .splits import DEFAULT_EMBARGO_BARS, assert_disjoint_and_purged, purged_walk_forward
from .target import HORIZON_BARS, build_target

HYPOTHESIS_ID = "H-02"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
SCHEMA_VERSION = 1

#: H-02 gate threshold (registered, literal).
OOS_R2_MIN = 0.15

#: HAR regressors: pick the 60m / 240m / weekly-ish RV columns as the HAR
#: daily/weekly/monthly proxies (rv_60m, rv_120m, rv_240m exist in features).
_HAR_PROXY_COLUMNS = ("rv_60m", "rv_120m", "rv_240m")


@dataclass(frozen=True)
class FoldResult:
    fold_id: int
    n_train: int
    n_test: int
    model_r2: float
    model_qlike: float
    har_r2: float
    har_qlike: float
    qlike_beats_har: bool
    r2_passes: bool


def _clean(features: pd.DataFrame, target: pd.Series, names: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Align features+target, drop any row with NaN in a used column or target."""
    used = features[names + ["close"]].copy()
    used["__target__"] = target
    used = used.replace([np.inf, -np.inf], np.nan).dropna(axis=0, how="any")
    y = used.pop("__target__")
    return used, y


def run_pipeline(
    klines: pd.DataFrame,
    symbol: str,
    model_name: str = "har",
    n_folds: int = 2,
    embargo_bars: int = DEFAULT_EMBARGO_BARS,
    seed: int = DEFAULT_SEED,
    perm_repeats: int = 20,
    run_fdr: bool = True,
) -> dict[str, Any]:
    """Run the full repro on one symbol's 1-minute klines and return a result dict."""
    features, specs = build_features(klines)
    names = feature_names(specs)
    target = build_target(features)
    clean, y = _clean(features, target, names)

    X_all = clean[names].to_numpy(dtype=float)
    y_all = y.to_numpy(dtype=float)
    n_rows = X_all.shape[0]

    folds = purged_walk_forward(
        n_rows=n_rows, n_folds=n_folds, embargo_bars=embargo_bars
    )
    assert_disjoint_and_purged(folds)

    # HAR proxy column indices (fall back to first 3 if names changed).
    har_idx = tuple(names.index(c) for c in _HAR_PROXY_COLUMNS if c in names)

    fold_results: list[FoldResult] = []
    # Accumulate permutation p-values across folds (mean) for the FDR family.
    p_accum: dict[str, list[float]] = {n: [] for n in names}
    imp_accum: dict[str, list[float]] = {n: [] for n in names}

    for f in folds:
        Xtr, ytr = X_all[f.train_idx], y_all[f.train_idx]
        Xte, yte = X_all[f.test_idx], y_all[f.test_idx]

        model = build_model(model_name, seed=seed)
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        m_r2 = oos_r2(yte, pred)
        m_ql = qlike(yte, pred)

        har = HARRVBaseline(har_feature_indices=har_idx)
        har.fit(Xtr, ytr)
        h_pred = har.predict(Xte)
        h_r2 = oos_r2(yte, h_pred)
        h_ql = qlike(yte, h_pred)

        fold_results.append(
            FoldResult(
                fold_id=f.fold_id,
                n_train=int(f.train_idx.size),
                n_test=int(f.test_idx.size),
                model_r2=m_r2,
                model_qlike=m_ql,
                har_r2=h_r2,
                har_qlike=h_ql,
                qlike_beats_har=bool(m_ql < h_ql),
                r2_passes=bool(m_r2 >= OOS_R2_MIN),
            )
        )

        if run_fdr and model_name != "har":
            perms = permutation_importance(
                model, Xte, yte, names, n_repeats=perm_repeats, seed=seed + f.fold_id
            )
            for pi in perms:
                p_accum[pi.feature].append(pi.p_value)
                imp_accum[pi.feature].append(pi.importance)

    # Aggregate FDR over folds (mean p-value per feature; HAR has no FDR).
    fdr_payload: Optional[dict[str, Any]] = None
    if run_fdr and model_name != "har" and any(p_accum[n] for n in names):
        mean_p = {n: float(np.mean(p_accum[n])) for n in names if p_accum[n]}
        mean_imp = {n: float(np.mean(imp_accum[n])) for n in names if imp_accum[n]}
        fdr = benjamini_hochberg(mean_p, alpha=FDR_ALPHA)
        fdr_payload = {
            "family": "F-VOL",
            "alpha": fdr.alpha,
            "n_features": fdr.n_features,
            "n_significant": fdr.n_significant,
            "threshold_p": fdr.threshold_p,
            "significant_features": fdr.significant_features,
            "p_values": mean_p,
            "importances": mean_imp,
        }

    # H-02 pre-check (non-binding; gate-auditor decides).
    all_r2_pass = all(fr.r2_passes for fr in fold_results)
    all_qlike_beats = all(fr.qlike_beats_har for fr in fold_results)
    precheck = "WEITER" if (all_r2_pass and all_qlike_beats) else "DROP/PARK"
    if model_name == "har":
        precheck = "BASELINE-ONLY"  # HAR cannot beat itself; informational run

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "symbol": symbol,
        "model": model_name,
        "seed": seed,
        "n_rows": n_rows,
        "n_folds": n_folds,
        "embargo_bars": embargo_bars,
        "purge_horizon_bars": HORIZON_BARS,
        "feature_provenance": FEATURE_PROVENANCE,
        "features": [
            {"name": s.name, "provenance": s.provenance, "description": s.description}
            for s in specs
        ],
        "folds": [vars(fr) for fr in fold_results],
        "fdr": fdr_payload,
        "gate_oos_r2_min": OOS_R2_MIN,
        "precheck_verdict": precheck,
        "all_folds_r2_pass": all_r2_pass,
        "all_folds_qlike_beats_har": all_qlike_beats,
    }


def render_markdown(result: dict[str, Any]) -> str:
    """German Markdown report listing the H-02 criteria one by one."""
    lines: list[str] = []
    lines.append(f"# C-42-Reproduktion ({result['hypothesis']} · Vol-Regression)")
    lines.append("")
    lines.append(f"- **Hypothese:** {result['hypothesis']} — `{result['hypothesis_registry']}`")
    lines.append(f"- **Erzeugt:** {result['generated_at']} (UTC)")
    lines.append(f"- **Symbol:** {result['symbol']} · **Modell:** `{result['model']}` · Seed {result['seed']}")
    lines.append(
        f"- **Daten:** {result['n_rows']} saubere Zeilen, {result['n_folds']} purged-WF-Fenster, "
        f"Purge={result['purge_horizon_bars']}+Embargo {result['embargo_bars']} Bars"
    )
    prov = result["feature_provenance"]
    lines.append(
        f"- **Features:** 36 ({prov['DOCUMENTED']} DOCUMENTED, {prov['ASSUMED']} ASSUMED)"
    )
    lines.append("")
    lines.append("## H-02-Kriterien (einzeln; Gate-Urteil faellt der gate-auditor)")
    lines.append("")
    lines.append("| Kriterium (Registry, woertlich) | Operationalisierung | Messwert | erfuellt |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| OOS-R^2 >= 0.15 in ALLEN Fenstern | min Fold-R^2 >= {result['gate_oos_r2_min']} "
        f"| {_min_field(result, 'model_r2'):.4f} (min) | {_yn(result['all_folds_r2_pass'])} |"
    )
    lines.append(
        "| QLIKE schlaegt HAR-RV in ALLEN Fenstern | model_qlike < har_qlike je Fold "
        f"| {_qlike_summary(result)} | {_yn(result['all_folds_qlike_beats_har'])} |"
    )
    lines.append(
        "| purged Walk-Forward, >=2 disjunkte OOS-Fenster | Splitter deterministisch-chronologisch "
        f"| {result['n_folds']} Fenster | {_yn(result['n_folds'] >= 2)} |"
    )
    fdr = result.get("fdr")
    if fdr:
        lines.append(
            "| FDR BH alpha=0.10 ueber 36 Features (F-VOL) | BH step-up ueber Permutations-p "
            f"| {fdr['n_significant']}/{fdr['n_features']} signifikant | n/a (Reporting) |"
        )
    lines.append("")
    lines.append(f"**Pre-Check (nicht bindend):** {result['precheck_verdict']}")
    lines.append("")
    lines.append("## Fenster-Metriken")
    lines.append("")
    lines.append("| Fold | n_train | n_test | model R^2 | HAR R^2 | model QLIKE | HAR QLIKE | QLIKE<HAR | R^2>=0.15 |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|")
    for fr in result["folds"]:
        lines.append(
            f"| {fr['fold_id']} | {fr['n_train']} | {fr['n_test']} "
            f"| {fr['model_r2']:.4f} | {fr['har_r2']:.4f} "
            f"| {fr['model_qlike']:.5f} | {fr['har_qlike']:.5f} "
            f"| {_yn(fr['qlike_beats_har'])} | {_yn(fr['r2_passes'])} |"
        )
    lines.append("")
    if fdr:
        lines.append("## FDR (F-VOL, BH alpha=0.10) — signifikante Features")
        lines.append("")
        if fdr["significant_features"]:
            for name in fdr["significant_features"]:
                lines.append(f"- `{name}` (p={fdr['p_values'][name]:.4f})")
        else:
            lines.append("- keine Features ueberleben BH alpha=0.10")
        lines.append("")
    lines.append("---")
    lines.append(
        "*Erzeugt von `scripts/c42_repro.py` (WP-4, read-only auf kline_1min). "
        f"Endgueltiges Gate-Urteil: gate-auditor gegen {result['hypothesis']}.*"
    )
    lines.append("")
    return "\n".join(lines)


def _min_field(result: dict[str, Any], key: str) -> float:
    vals = [fr[key] for fr in result["folds"]]
    return min(vals) if vals else float("nan")


def _qlike_summary(result: dict[str, Any]) -> str:
    parts = [f"{fr['model_qlike']:.4f} vs {fr['har_qlike']:.4f}" for fr in result["folds"]]
    return "; ".join(parts)


def _yn(value: Any) -> str:
    return "ja" if value else "nein"
