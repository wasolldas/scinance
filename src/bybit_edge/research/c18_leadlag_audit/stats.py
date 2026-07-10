"""GL-006 baseline + pre-registered partial claims T1/T2 for the H-18 audit.

The baseline constants below are transcribed at FULL float precision from the
archived, adjudicated GL-006 result
``scinance2-impl/handoff_local/results/wave2_20260617_090618/h04/c17_c41_results.json``
(gate log entry GL-006, 2026-06-17). They are used ONLY to (a) pin the audit
re-execution to the archived windows F0/F1, (b) verify the data binding
(observed statistics must reproduce), and (c) evaluate the pre-registered
partial claims:

* **T1** — all 12 GL-006 Stage-1 FDR survivors re-measure at p <= 1e-3 AND
  stay significant under the freshly computed per-window BH step-up.
* **T2** — the two Lesart decision cells (ETH->BTC, window F0, lag 1 and
  lag 2) resolve to ONE side of the window's p_crit by > 5 MC standard
  errors (instead of today's < 1 MC-SE undecidability at N = 200).

NICHT-VERDIKT-KLAUSEL (registry H-18, verbindlich): any drifting result
marks the GL-006 Messungen-WEITER as "aufloesungsbedingt fragil" — it NEVER
changes any GL-006 field anywhere, and nothing in this package writes
``gate_log.md``. The BH-FDR itself is imported from the ORIGINAL module so
the two pipelines cannot drift apart.

KAPITALFREI: identical to GL-006 — no tradability logic.
"""
from __future__ import annotations

import math
from typing import Any

# Byte-identical FDR machinery: imported from the original H-04 module.
from bybit_edge.research.c17_c41_lead_lag.surrogate import (  # noqa: F401
    FDR_ALPHA,
    benjamini_hochberg,
)

#: Registered T1 threshold: >= 5x below the old p floor of 1/201 ~ 0.005.
T1_P_MAX = 1e-3
#: Registered T2 threshold: > 5 MC standard errors away from p_crit.
T2_MIN_SE_DISTANCE = 5.0

#: Archived GL-006 per-window baseline (full precision, source see docstring).
GL006_BASELINE: dict[str, Any] = {
    "source": (
        "scinance2-impl/handoff_local/results/wave2_20260617_090618/"
        "h04/c17_c41_results.json"
    ),
    "gate_log_entry": "GL-006",
    "hypothesis": "H-04",
    "verdict": "WEITER (Mess-Existenz; Kapital-Status PARK) — append-only, "
               "wird durch H-18 NIEMALS geaendert",
    "n_surrogates": 200,
    "seed": 42,
    "grid_ms": 1000.0,
    "n_bins": 3,
    "lags": [1, 2, 3, 5, 10],
    "max_ticks_per_window": 150000,
    "symbol_a": "BTCUSDT",
    "symbol_b": "ETHUSDT",
    "windows": [
        {
            "index": 0,
            "n_bars": 3874,
            "t0_ms": 1780611314526.0,
            "t1_ms": 1780615189170.0,
            "p_crit": 0.06965174129353234,
            "n_fdr_significant": 8,
            "variants": {
                "TE_BTCUSDT->ETHUSDT_lag1": {"observed_stat": 0.005352066511254873, "p_value": 0.024875621890547265, "fdr_significant": True},
                "TE_ETHUSDT->BTCUSDT_lag1": {"observed_stat": 0.004010215775156639, "p_value": 0.06467661691542288, "fdr_significant": True},
                "TE_BTCUSDT->ETHUSDT_lag2": {"observed_stat": 0.0073759784005824865, "p_value": 0.009950248756218905, "fdr_significant": True},
                "TE_ETHUSDT->BTCUSDT_lag2": {"observed_stat": 0.0046206080057756786, "p_value": 0.06965174129353234, "fdr_significant": True},
                "TE_BTCUSDT->ETHUSDT_lag3": {"observed_stat": 0.005918610995342056, "p_value": 0.014925373134328358, "fdr_significant": True},
                "TE_ETHUSDT->BTCUSDT_lag3": {"observed_stat": 0.004602632024732765, "p_value": 0.01990049751243781, "fdr_significant": True},
                "TE_BTCUSDT->ETHUSDT_lag5": {"observed_stat": 0.004830775154381544, "p_value": 0.04477611940298507, "fdr_significant": True},
                "TE_ETHUSDT->BTCUSDT_lag5": {"observed_stat": 0.0028742818994913877, "p_value": 0.27860696517412936, "fdr_significant": False},
                "TE_BTCUSDT->ETHUSDT_lag10": {"observed_stat": 0.0037237754028206286, "p_value": 0.15920398009950248, "fdr_significant": False},
                "TE_ETHUSDT->BTCUSDT_lag10": {"observed_stat": 0.002195442047904226, "p_value": 0.5124378109452736, "fdr_significant": False},
                "WCOH_BTCUSDT/ETHUSDT": {"observed_stat": 0.9027600484768014, "p_value": 0.004975124378109453, "fdr_significant": True},
            },
        },
        {
            "index": 1,
            "n_bars": 3875,
            "t0_ms": 1780615190990.0,
            "t1_ms": 1780619066816.0,
            "p_crit": 0.01990049751243781,
            "n_fdr_significant": 4,
            "variants": {
                "TE_BTCUSDT->ETHUSDT_lag1": {"observed_stat": 0.008670776197228948, "p_value": 0.004975124378109453, "fdr_significant": True},
                "TE_ETHUSDT->BTCUSDT_lag1": {"observed_stat": 0.005449744415419377, "p_value": 0.004975124378109453, "fdr_significant": True},
                "TE_BTCUSDT->ETHUSDT_lag2": {"observed_stat": 0.004910517495546089, "p_value": 0.01990049751243781, "fdr_significant": True},
                "TE_ETHUSDT->BTCUSDT_lag2": {"observed_stat": 0.002762708826512116, "p_value": 0.21393034825870647, "fdr_significant": False},
                "TE_BTCUSDT->ETHUSDT_lag3": {"observed_stat": 0.0016881458768887582, "p_value": 0.7213930348258707, "fdr_significant": False},
                "TE_ETHUSDT->BTCUSDT_lag3": {"observed_stat": 0.0035744042344439594, "p_value": 0.07462686567164178, "fdr_significant": False},
                "TE_BTCUSDT->ETHUSDT_lag5": {"observed_stat": 0.003727742177347618, "p_value": 0.07960199004975124, "fdr_significant": False},
                "TE_ETHUSDT->BTCUSDT_lag5": {"observed_stat": 0.0023904999783567196, "p_value": 0.46766169154228854, "fdr_significant": False},
                "TE_BTCUSDT->ETHUSDT_lag10": {"observed_stat": 0.0012108577200937504, "p_value": 0.9104477611940298, "fdr_significant": False},
                "TE_ETHUSDT->BTCUSDT_lag10": {"observed_stat": 0.0008914856172989821, "p_value": 0.9701492537313433, "fdr_significant": False},
                "WCOH_BTCUSDT/ETHUSDT": {"observed_stat": 0.9076279140092568, "p_value": 0.004975124378109453, "fdr_significant": True},
            },
        },
    ],
}

#: The 12 GL-006 Stage-1 FDR survivors: (window_index, variant_label).
#: 8 in F0 + 4 in F1 = 12 (gate log GL-006: "12 von 22 Varianten ueberleben").
STAGE1_SURVIVORS: tuple[tuple[int, str], ...] = tuple(
    (w["index"], label)
    for w in GL006_BASELINE["windows"]
    for label, v in w["variants"].items()
    if v["fdr_significant"]
)
assert len(STAGE1_SURVIVORS) == 12, "GL-006 baseline must yield exactly 12 survivors"

#: T2 Lesart decision cells: ETH->BTC in window F0 at lag 1 and lag 2
#: (registry H-18: today < 1 MC-SE from p_crit — undecidable at N = 200).
T2_CELLS: tuple[tuple[int, str], ...] = (
    (0, "TE_ETHUSDT->BTCUSDT_lag1"),
    (0, "TE_ETHUSDT->BTCUSDT_lag2"),
)


def mc_standard_error(p: float, n_surrogates: int) -> float:
    """Monte-Carlo standard error of an empirical p-value: sqrt(p(1-p)/N)."""
    if n_surrogates <= 0:
        return float("inf")
    p = min(max(float(p), 0.0), 1.0)
    return math.sqrt(p * (1.0 - p) / n_surrogates)


def _index_variants(windows: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    """(window_index, label) -> variant entry, from a run() windows payload."""
    out: dict[tuple[int, str], dict[str, Any]] = {}
    for w in windows:
        for v in w["variants"]:
            out[(int(w["index"]), str(v["label"]))] = v
    return out


def evaluate_t1(windows: list[dict[str, Any]], n_surrogates: int) -> dict[str, Any]:
    """Pre-registered claim T1 over a finished audit ``windows`` payload.

    T1 holds iff EVERY one of the 12 GL-006 Stage-1 FDR survivors (a) has a
    new p-value <= 1e-3 and (b) is significant under the freshly computed
    per-window BH step-up of THIS run. Each drifting survivor is listed —
    it marks the GL-006 Messungen-WEITER as "aufloesungsbedingt fragil" and
    NEVER changes the GL-006 verdict (Nicht-Verdikt-Klausel).
    """
    by_key = _index_variants(windows)
    base_vars = {
        (w["index"], label): v
        for w in GL006_BASELINE["windows"]
        for label, v in w["variants"].items()
    }
    cells: list[dict[str, Any]] = []
    drifting: list[str] = []
    for widx, label in STAGE1_SURVIVORS:
        v = by_key.get((widx, label))
        if v is None:
            cell = {
                "window": widx, "label": label, "measured": False,
                "p_gl006": base_vars[(widx, label)]["p_value"],
                "p_new": None, "p_le_threshold": False,
                "fdr_significant_new": False, "holds": False,
            }
        else:
            p_new = float(v["surrogate"]["p_value"])
            fdr_new = bool(v["fdr_significant"])
            p_ok = p_new <= T1_P_MAX
            cell = {
                "window": widx, "label": label, "measured": True,
                "p_gl006": base_vars[(widx, label)]["p_value"],
                "p_new": p_new,
                "mc_se_new": mc_standard_error(p_new, n_surrogates),
                "p_le_threshold": bool(p_ok),
                "fdr_significant_new": fdr_new,
                "holds": bool(p_ok and fdr_new),
            }
        cells.append(cell)
        if not cell["holds"]:
            drifting.append(f"w{widx}:{label}")
    return {
        "claim": (
            "T1: alle 12 GL-006-Stage-1-FDR-Survivor messen bei p <= 1e-3 neu "
            "und bleiben unter dem neu berechneten BH-Step-up signifikant"
        ),
        "p_threshold": T1_P_MAX,
        "n_survivors": len(STAGE1_SURVIVORS),
        "n_holding": sum(1 for c in cells if c["holds"]),
        "drifting_survivors": drifting,
        "t1_holds": len(drifting) == 0,
        "cells": cells,
        "non_verdict_clause": (
            "Jeder abdriftende Survivor falsifiziert NICHT das GL-006-Verdikt "
            "selbst — er markiert das stehende Messungen-WEITER als "
            "aufloesungsbedingt fragil (Audit-Finding). KEIN Goalpost-Move, "
            "KEINE Ruecknahme von GL-006."
        ),
    }


def evaluate_t2(windows: list[dict[str, Any]], n_surrogates: int) -> dict[str, Any]:
    """Pre-registered claim T2: the two Lesart decision cells resolve.

    A cell is RESOLVED when its new p-value sits > 5 MC-SE away from the
    freshly computed p_crit of its window (on either side; the side is
    reported). T2 holds iff BOTH cells resolve.
    """
    by_key = _index_variants(windows)
    p_crits = {int(w["index"]): float(w["criteria"]["fdr_p_crit"]) for w in windows}
    cells: list[dict[str, Any]] = []
    for widx, label in T2_CELLS:
        v = by_key.get((widx, label))
        if v is None:
            cells.append({
                "window": widx, "label": label, "measured": False,
                "resolved": False,
            })
            continue
        p_new = float(v["surrogate"]["p_value"])
        p_crit = p_crits.get(widx, 0.0)
        se = mc_standard_error(p_new, n_surrogates)
        dist = abs(p_new - p_crit) / se if se > 0 else float("inf")
        significant = bool(v["fdr_significant"])
        cells.append({
            "window": widx, "label": label, "measured": True,
            "p_new": p_new,
            "p_crit_new": p_crit,
            "mc_se": se,
            "distance_se": dist,
            "side": "signifikant" if significant else "nicht-signifikant",
            "resolved": bool(dist > T2_MIN_SE_DISTANCE),
        })
    return {
        "claim": (
            "T2: die zwei Lesart-Entscheidungszellen ETH->BTC F0 Lag1/Lag2 "
            "loesen sich mit > 5 MC-SE Abstand von p_crit auf eine Seite auf"
        ),
        "min_se_distance": T2_MIN_SE_DISTANCE,
        "cells": cells,
        "t2_holds": bool(cells) and all(c.get("resolved", False) for c in cells),
    }


def compare_windows_to_baseline(
    windows: list[dict[str, Any]],
    *,
    stat_rtol: float = 1e-6,
    stat_atol: float = 1e-9,
) -> dict[str, Any]:
    """Data-binding check: do the re-executed windows reproduce GL-006?

    Compares per-window bar counts / tick spans and the OBSERVED statistics
    (which do not depend on ``n_surrogates``) of every one of the 22 variant
    cells against the archived baseline. A mismatch does NOT abort the run —
    it is flagged honestly so the gate-auditor sees whether the audit really
    ran on the archived windows.
    """
    base_by_idx = {w["index"]: w for w in GL006_BASELINE["windows"]}
    per_window: list[dict[str, Any]] = []
    max_dev = 0.0
    all_match = True
    for w in windows:
        bw = base_by_idx.get(int(w["index"]))
        if bw is None:
            per_window.append({"index": w["index"], "in_baseline": False, "matches": False})
            all_match = False
            continue
        span_match = (
            float(w["t0_ms"]) == float(bw["t0_ms"])
            and float(w["t1_ms"]) == float(bw["t1_ms"])
            and int(w["n_bars"]) == int(bw["n_bars"])
        )
        stat_devs: dict[str, float] = {}
        stats_match = True
        for v in w["variants"]:
            b = bw["variants"].get(v["label"])
            if b is None:
                stats_match = False
                continue
            obs_new = float(v["surrogate"]["observed_stat"])
            obs_old = float(b["observed_stat"])
            dev = abs(obs_new - obs_old)
            stat_devs[v["label"]] = dev
            max_dev = max(max_dev, dev)
            if dev > stat_atol + stat_rtol * abs(obs_old):
                stats_match = False
        matches = bool(span_match and stats_match)
        all_match = all_match and matches
        per_window.append({
            "index": int(w["index"]),
            "in_baseline": True,
            "span_match": bool(span_match),
            "n_bars": {"new": int(w["n_bars"]), "gl006": int(bw["n_bars"])},
            "t0_ms": {"new": float(w["t0_ms"]), "gl006": float(bw["t0_ms"])},
            "t1_ms": {"new": float(w["t1_ms"]), "gl006": float(bw["t1_ms"])},
            "observed_stats_match": bool(stats_match),
            "max_observed_stat_deviation": max(stat_devs.values()) if stat_devs else None,
            "matches": matches,
        })
    return {
        "purpose": (
            "Datenbindung: identisch GL-006 (archivierte Fenster F0/F1). "
            "Observed-Statistiken haengen NICHT von n_surrogates ab und "
            "muessen daher exakt reproduzieren, wenn die Fenster stimmen."
        ),
        "windows": per_window,
        "max_observed_stat_deviation": max_dev,
        "all_windows_match_gl006": bool(all_match),
    }
