"""Combined bootstrap p-values, BH-FDR and gate evaluation for H-13 (F-TAILSHAPE).

Null hypothesis (registry H-13): GPD form equality H0: xi_P = xi_Q per
symbol x snapshot day; Delta_xi = xi_P - xi_Q. The p-value comes from the
COMBINED bootstrap distribution (block bootstrap of xi_P crossed with the
strike bootstrap of xi_Q), shifted to the null.

BH-FDR alpha = 0.10 over the F-TAILSHAPE family. The registry fixes the
family at 2 symbols x 2 snapshot days = 4 cells; the driver pads unmeasured
(symbol, day) slots with p = 1.0 sentinel cells (``measured=False``) so the
BH family NEVER shrinks below the registered size (audit_h13 Bug 1 —
a smaller family would be anti-conservative). Own copy of the
Benjamini-Hochberg helper (repo convention: research families keep an
independent copy so the GL-bearing modules stay untouched).
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

#: BH-FDR level for the F-TAILSHAPE family (registry H-13).
FDR_ALPHA = 0.10
#: Pre-registered minimum |Delta_xi| (non-negotiable, registry H-13).
DELTA_XI_FLOOR = 0.15
#: Pre-registered bootstrap-p ceiling (before BH-FDR).
BOOTSTRAP_P_MAX = 0.05


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)`` where ``rejected[i]`` is True if hypothesis
    ``i`` is significant at FDR ``alpha`` and ``p_crit`` is the largest p-value
    that passes (0.0 if none). Order of the input list is preserved in the
    output mask. (Copy of the c31_cfar convention.)
    """
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit = 0.0
    k_max = -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max = rank
            p_crit = p_values[idx]
    rejected = [False] * m
    if k_max >= 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= k_max:
                rejected[idx] = True
    return rejected, p_crit


def combined_bootstrap_p(
    xi_p_boot: np.ndarray,
    xi_q_boot: np.ndarray,
    delta_obs: float,
) -> tuple[float, int]:
    """Two-sided p for H0: xi_P = xi_Q from the combined bootstrap distribution.

    Crosses every block-bootstrap replicate of xi_P with every strike-bootstrap
    replicate of xi_Q (outer product) to build the bootstrap distribution of
    Delta_xi* = xi_P* - xi_Q*, shifts it to the null (subtract the observed
    Delta_xi), and reports the add-one-corrected two-sided tail fraction

        p = (#{|Delta_xi* - Delta_obs| >= |Delta_obs|} + 1) / (N + 1).

    Non-finite replicates (failed refits) are dropped. Returns ``(p, N)``;
    if either side has no valid replicates, p = 1.0 (maximally conservative).
    """
    xp = np.asarray(xi_p_boot, dtype=np.float64)
    xq = np.asarray(xi_q_boot, dtype=np.float64)
    xp = xp[np.isfinite(xp)]
    xq = xq[np.isfinite(xq)]
    if xp.size == 0 or xq.size == 0 or not math.isfinite(delta_obs):
        return 1.0, 0
    deltas = (xp[:, None] - xq[None, :]).ravel()
    centered = deltas - delta_obs
    n = centered.size
    n_ge = int(np.sum(np.abs(centered) >= abs(delta_obs)))
    return float((n_ge + 1) / (n + 1)), n


def hill_contradicts(delta_obs: float, xi_hill: float, xi_q: float) -> bool:
    """True iff the Hill cross-check CONTRADICTS the GPD divergence sign.

    Registry H-13: "Hill-Gegenprobe widerspricht dem GPD-Vorzeichen nicht".
    Operationalisation (fixed here, documented in README_H13): a contradiction
    exists iff sign(xi_Hill - xi_Q) is STRICTLY OPPOSITE to
    sign(Delta_xi) = sign(xi_P - xi_Q). A non-finite Hill estimate or an
    exactly-zero difference is neutral (no contradiction, no support).
    """
    if not (math.isfinite(delta_obs) and math.isfinite(xi_hill) and math.isfinite(xi_q)):
        return False
    dh = xi_hill - xi_q
    if dh == 0.0 or delta_obs == 0.0:
        return False
    return bool(np.sign(dh) == -np.sign(delta_obs))


def evaluate_gate(
    cells: list[dict[str, Any]],
    *,
    alpha: float = FDR_ALPHA,
    delta_floor: float = DELTA_XI_FLOOR,
    p_max: float = BOOTSTRAP_P_MAX,
) -> dict[str, Any]:
    """Apply BH-FDR over the F-TAILSHAPE family and evaluate the H-13 gate.

    Each cell needs: ``symbol``, ``day_label`` ("D1"/"D2"), ``delta_xi``,
    ``p_value``, ``hill_contradiction`` (bool); an optional ``measured``
    flag (default True) marks p = 1.0 sentinel cells padded in by the driver
    to keep the family at the registered fixed size (2 symbols x 2 days = 4).
    BH runs over ALL cells (sentinels included — that is the point of the
    padding); per-symbol day/sign bookkeeping only counts MEASURED cells.
    Mutates each cell with ``fdr_significant`` and the per-criterion flags.
    Gate (registry, verbatim criteria): WEITER iff for >= 1 symbol at BOTH
    snapshot days: sign(Delta_xi) identical AND |Delta_xi| >= 0.15 AND
    bootstrap-p <= 0.05 after BH-FDR alpha = 0.10 over F-TAILSHAPE AND the
    Hill cross-check does not contradict the GPD sign. The payload stays
    gate-neutral — the gate-auditor adjudicates; this only precomputes the
    registered flags.
    """
    p_values = [float(c["p_value"]) for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, alpha)
    for c, rej in zip(cells, rejected):
        d = float(c["delta_xi"])
        c["fdr_significant"] = bool(rej and float(c["p_value"]) <= p_max)
        c["delta_floor_met"] = bool(math.isfinite(d) and abs(d) >= delta_floor)
        c["sign"] = int(np.sign(d)) if math.isfinite(d) else 0
        c["cell_criteria_met"] = bool(
            c["fdr_significant"]
            and c["delta_floor_met"]
            and c["sign"] != 0
            and not bool(c.get("hill_contradiction", False))
        )

    per_symbol: dict[str, dict[str, Any]] = {}
    for sym in sorted({c["symbol"] for c in cells}):
        sym_cells = [c for c in cells if c["symbol"] == sym]
        meas = [c for c in sym_cells if c.get("measured", True)]
        days = {c["day_label"] for c in meas}
        both_days = {"D1", "D2"} <= days
        signs = {c["sign"] for c in meas}
        sign_consistent = both_days and len(signs) == 1 and 0 not in signs
        all_met = both_days and all(c["cell_criteria_met"] for c in meas)
        per_symbol[sym] = {
            "n_cells": len(sym_cells),
            "n_cells_measured": len(meas),
            "both_days_measured": bool(both_days),
            "sign_consistent": bool(sign_consistent),
            "all_cell_criteria_met": bool(all_met),
            "symbol_gate_met": bool(sign_consistent and all_met),
        }

    n_measured = sum(1 for c in cells if c.get("measured", True))
    return {
        "fdr_alpha": alpha,
        "fdr_p_crit": float(p_crit),
        # Fixed registered family size (sentinels included) vs. measured cells:
        "family_size": len(cells),
        "n_cells_measured": int(n_measured),
        "n_cells_sentinel": int(len(cells) - n_measured),
        "n_fdr_significant": int(sum(1 for c in cells if c["fdr_significant"])),
        "delta_xi_floor": delta_floor,
        "bootstrap_p_max": p_max,
        "per_symbol": per_symbol,
        # Gate-neutral observation flag (gate-auditor adjudicates WEITER/DROP):
        "any_symbol_gate_met": bool(any(v["symbol_gate_met"] for v in per_symbol.values())),
    }
