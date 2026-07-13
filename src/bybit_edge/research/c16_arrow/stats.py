"""AUC, exact-null p-values, BH-FDR and gate rollup for H-16 (F-ARROW).

Main null (registry H-16, exact): for a TIME-REVERSIBLE process the joint
law of a window and its reversal is exchangeable, so the Bayes-optimal
classifier AUC is EXACTLY 0.5 (Lopez-Paz & Oquab 2017, classifier two-sample
test) — no resampling is needed for the main null. The per-symbol p-value is
computed from the exact paired sign test: each held-out window contributes a
(forward score, reversed score) pair; under H0 the sign of the difference is
a fair coin independently per window, so #(fwd > rev) ~ Binomial(n, 1/2)
(ties dropped — documented operationalisation, fixed before any run;
respects the pairing, which a naive Mann-Whitney variance would ignore).

KNOWN LIMITATION (documented, NOT fixed in code — fixing it would change the
registered p-value/threshold procedure post-hoc, which the registry
forbids; see :func:`paired_sign_test_p`): the independence assumption above
is VIOLATED in practice. At ``stride_s=64`` and ``window_s=512`` (registry
H-16 constants, see ``scalogram.py``) consecutive held-out windows share
87.5% of their raw seconds, so consecutive (fwd>rev) signs are strongly
positively correlated; the effective independent sample size is closer to
``n/8`` than to ``n``. ``Binomial(n, 1/2)`` therefore understates the true
variance of the sign-test statistic and the resulting p-values are
ANTI-CONSERVATIVE (too small) relative to the true dependence structure —
this feeds directly into the BH-FDR alpha=0.10 gate over F-ARROW. This is a
STATISTICAL CAVEAT on the registered, pre-fixed operationalisation, not a
bug in the exact-binomial arithmetic itself; per the registry's "no
post-hoc threshold changes" rule (H-16, gate constants verbatim/non-
negotiable) this is documented here and in ``README_H16.md`` rather than
silently patched with an ad-hoc effective-n correction.

Gate constants (registry H-16, verbatim, non-negotiable): held-out AUC
>= 0.60 WITH IAAFT-surrogate-null 95th percentile < 0.53, at >= 4/5 symbols
after BH-FDR alpha = 0.10 over F-ARROW, AND the phase-randomised leak
control stays <= 0.52 — otherwise METHODICALLY INVALID, NO VERDICT (a
distinct state, explicitly NOT a DROP: the payload carries
``status = "METHOD_INVALID_NO_VERDICT"`` and the gate-auditor adjudicates).

Family discipline: F-ARROW is FIXED at 5 symbols. Unmeasured symbols are
padded with p = 1.0 sentinel cells so BH never runs over a silently
shrunken (anti-conservative) family — same convention as c13 (audit_h13
Bug 1). Own Benjamini-Hochberg copy (repo convention: research families
keep an independent copy so GL-bearing modules stay untouched).

KAPITALFREI: no cost/return quantity anywhere.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

#: BH-FDR level for the F-ARROW family (registry H-16).
FDR_ALPHA = 0.10
#: Registered fixed family size (5 Bybit perp symbols).
FAMILY_SIZE = 5
#: Registered held-out AUC floor for WEITER.
AUC_MIN = 0.60
#: Registered ceiling for the IAAFT surrogate-null 95th percentile.
SURROGATE_P95_MAX = 0.53
#: Registered leak-control ceiling (mean surrogate held-out AUC).
LEAK_AUC_MAX = 0.52
#: Registered symbol quorum for WEITER.
N_SYMBOLS_MIN = 4

#: Distinct payload states (registry: leak failure is NOT a DROP).
STATUS_MEASURED = "MEASURED_GATE_NEUTRAL"
STATUS_METHOD_INVALID = "METHOD_INVALID_NO_VERDICT"


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``; ``rejected[i]`` is True iff hypothesis
    ``i`` survives at FDR ``alpha``; ``p_crit`` is the largest passing
    p-value (0.0 if none). Input order preserved. (Copy of the c31_cfar /
    c13_tailshape convention — own copy per research family.)
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


def mann_whitney_auc(pos_scores: np.ndarray, neg_scores: np.ndarray) -> float:
    """AUC = P(score_pos > score_neg) + 0.5 P(=) (Mann-Whitney identity).

    Ranks-based, tie-aware, O(n log n). Positive class = FORWARD windows.
    """
    pos = np.asarray(pos_scores, dtype=np.float64)
    neg = np.asarray(neg_scores, dtype=np.float64)
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    both = np.concatenate([pos, neg])
    order = np.argsort(both, kind="mergesort")
    ranks = np.empty(both.size, dtype=np.float64)
    ranks[order] = np.arange(1, both.size + 1, dtype=np.float64)
    # average ranks over ties
    sorted_vals = both[order]
    i = 0
    while i < sorted_vals.size:
        j = i
        while j + 1 < sorted_vals.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        if j > i:
            avg = 0.5 * (i + 1 + j + 1)
            ranks[order[i:j + 1]] = avg
        i = j + 1
    r_pos = float(ranks[: pos.size].sum())
    u = r_pos - pos.size * (pos.size + 1) / 2.0
    return float(u / (pos.size * neg.size))


def paired_sign_test_p(fwd_scores: np.ndarray, rev_scores: np.ndarray) -> tuple[float, dict[str, int]]:
    """Exact one-sided paired sign test against the Bayes null AUC = 0.5.

    H0 (time-reversible process): P(score_fwd > score_rev) = 0.5 per window
    pair, independent across held-out windows. Ties are dropped (standard
    sign test). Returns ``(p, counts)`` with p = P(Bin(n_eff, 0.5) >= k)
    computed via the regularised incomplete beta function (exact, no scipy
    dependency); counts = {n_pairs, n_greater, n_ties}.

    KNOWN LIMITATION (documented, deliberately NOT changed — see module
    docstring): the "independent across held-out windows" premise does not
    hold at the registered ``stride_s=64`` / ``window_s=512`` — consecutive
    windows overlap 87.5% of their raw seconds, so consecutive signs are
    strongly positively correlated and the true effective sample size is
    roughly ``n/8``. ``Binomial(n, 1/2)`` (n = n_eff here) therefore
    UNDERSTATES the true variance and this p-value is anti-conservative.
    Changing the operationalisation (e.g. subsampling every 8th window for
    the sign test) would alter the pre-registered, gate-relevant p-value
    procedure post-hoc — not permitted without a registry update — so this
    is a documented statistical caveat, not a code fix.
    """
    f = np.asarray(fwd_scores, dtype=np.float64)
    r = np.asarray(rev_scores, dtype=np.float64)
    if f.shape != r.shape:
        raise ValueError(f"paired scores shape mismatch: {f.shape} vs {r.shape}")
    n_pairs = int(f.size)
    n_greater = int(np.sum(f > r))
    n_ties = int(np.sum(f == r))
    n_eff = n_pairs - n_ties
    counts = {"n_pairs": n_pairs, "n_greater": n_greater, "n_ties": n_ties}
    if n_eff <= 0:
        return 1.0, counts
    p = _binom_sf_half(n_greater, n_eff)
    return float(min(max(p, 0.0), 1.0)), counts


def _binom_sf_half(k: int, n: int) -> float:
    """P(Bin(n, 1/2) >= k), exact via a numerically stable log-sum.

    Small n: direct summation in log space. Large n (> 10_000): normal
    approximation with continuity correction (error negligible at the p
    resolutions that matter for BH alpha = 0.10).
    """
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if n > 10_000:
        mu = 0.5 * n
        sd = 0.5 * math.sqrt(n)
        z = (k - 0.5 - mu) / sd
        return 0.5 * math.erfc(z / math.sqrt(2.0))
    log_half_n = n * math.log(0.5)
    total = -math.inf
    for i in range(k, n + 1):
        term = math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + log_half_n
        total = term if total == -math.inf else max(total, term) + math.log1p(
            math.exp(min(total, term) - max(total, term))
        )
    return math.exp(total)


def surrogate_percentile_95(surrogate_aucs: list[float]) -> float:
    """95th percentile of the surrogate-null AUCs (linear interpolation).

    numpy default ``linear`` interpolation, documented operationalisation
    (registered draw count is 20 -> the p95 sits between the 19th and 20th
    order statistic).
    """
    arr = np.asarray([a for a in surrogate_aucs if math.isfinite(a)], dtype=np.float64)
    if arr.size == 0:
        return float("nan")
    return float(np.percentile(arr, 95.0, method="linear"))


def sentinel_cell(symbol: str, reason: str) -> dict[str, Any]:
    """Conservative p = 1.0 sentinel keeping F-ARROW at its registered size.

    A symbol whose measurement failed (data missing, cell error) must still
    occupy its BH slot — otherwise the family shrinks and the BH thresholds
    become MORE lenient than registered (anti-conservative; c13/audit_h13
    Bug 1 convention). A sentinel can never be rejected itself.
    """
    return {
        "symbol": symbol,
        "measured": False,
        "sentinel_reason": reason,
        "auc": float("nan"),
        "auc_seeds": [],
        "p_value": 1.0,
        "surrogate_aucs": [],
        "surrogate_p95": float("nan"),
        "leak_auc": float("nan"),
        "ablation_auc_unsigned": float("nan"),
    }


def evaluate_gate(
    cells: list[dict[str, Any]],
    *,
    alpha: float = FDR_ALPHA,
    auc_min: float = AUC_MIN,
    surrogate_p95_max: float = SURROGATE_P95_MAX,
    leak_auc_max: float = LEAK_AUC_MAX,
    n_symbols_min: int = N_SYMBOLS_MIN,
) -> dict[str, Any]:
    """BH-FDR over F-ARROW + registered per-symbol flags + validity state.

    Each cell needs ``symbol``, ``auc``, ``p_value``, ``surrogate_p95``,
    ``leak_auc`` (+ optional ``measured``, default True). Mutates cells with
    the per-criterion flags. Gate-neutral: the WEITER/DROP verdict belongs
    to the gate-auditor; this only precomputes the registered criteria.

    Validity state (registry, binding): if the leak control of ANY measured
    symbol exceeds ``leak_auc_max`` the run is METHODICALLY INVALID —
    ``status = "METHOD_INVALID_NO_VERDICT"`` — which is a DISTINCT state,
    NOT a DROP: no verdict may be derived from such a run, in either
    direction. The flags are still reported for the audit trail.
    """
    p_values = [float(c["p_value"]) for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, alpha)
    for c, rej in zip(cells, rejected):
        measured = bool(c.get("measured", True))
        auc = float(c["auc"]) if c.get("auc") is not None else float("nan")
        p95 = float(c["surrogate_p95"]) if c.get("surrogate_p95") is not None else float("nan")
        leak = float(c["leak_auc"]) if c.get("leak_auc") is not None else float("nan")
        c["fdr_significant"] = bool(rej and measured)
        c["auc_floor_met"] = bool(measured and math.isfinite(auc) and auc >= auc_min)
        c["surrogate_p95_ok"] = bool(measured and math.isfinite(p95) and p95 < surrogate_p95_max)
        # leak_ok requires a FINITE measured leak value — an unmeasured leak
        # control can never count as passed.
        c["leak_ok"] = bool(measured and math.isfinite(leak) and leak <= leak_auc_max)
        c["method_invalid"] = bool(measured and math.isfinite(leak) and leak > leak_auc_max)
        c["symbol_gate_met"] = bool(
            c["fdr_significant"]
            and c["auc_floor_met"]
            and c["surrogate_p95_ok"]
            and c["leak_ok"]
        )

    measured_cells = [c for c in cells if c.get("measured", True)]
    invalid_symbols = [c["symbol"] for c in measured_cells if c["method_invalid"]]
    leak_all_ok = bool(measured_cells) and all(c["leak_ok"] for c in measured_cells)
    n_gate_met = sum(1 for c in cells if c["symbol_gate_met"])
    method_invalid = len(invalid_symbols) > 0

    return {
        "fdr_family": "F-ARROW",
        "fdr_alpha": alpha,
        "fdr_p_crit": float(p_crit),
        "family_size": len(cells),
        "n_cells_measured": len(measured_cells),
        "n_cells_sentinel": len(cells) - len(measured_cells),
        "n_fdr_significant": int(sum(1 for c in cells if c["fdr_significant"])),
        "auc_min": auc_min,
        "surrogate_p95_max": surrogate_p95_max,
        "leak_auc_max": leak_auc_max,
        "n_symbols_min": n_symbols_min,
        "n_symbols_gate_met": int(n_gate_met),
        "leak_control_passed": leak_all_ok,
        "method_invalid_symbols": invalid_symbols,
        "method_invalid": method_invalid,
        # Distinct validity state — NOT a verdict and NOT a DROP:
        "status": STATUS_METHOD_INVALID if method_invalid else STATUS_MEASURED,
        "status_note": (
            "Leak-Kontrolle > {:.2f} auf IAAFT-Surrogaten -> Lauf METHODISCH "
            "INVALIDE, KEIN VERDIKT (weder WEITER noch DROP ableitbar; "
            "gate-auditor entscheidet ueber Konsequenz).".format(leak_auc_max)
            if method_invalid
            else "gate-neutral: WEITER/DROP urteilt ausschliesslich der "
                 "gate-auditor gegen die Registry (H-16)."
        ),
        # Registered quorum precomputation (only meaningful when valid):
        "gate_quorum_met": bool(
            not method_invalid and leak_all_ok and n_gate_met >= n_symbols_min
        ),
    }


__all__ = [
    "AUC_MIN",
    "FAMILY_SIZE",
    "FDR_ALPHA",
    "LEAK_AUC_MAX",
    "N_SYMBOLS_MIN",
    "STATUS_MEASURED",
    "STATUS_METHOD_INVALID",
    "SURROGATE_P95_MAX",
    "benjamini_hochberg",
    "evaluate_gate",
    "mann_whitney_auc",
    "paired_sign_test_p",
    "sentinel_cell",
    "surrogate_percentile_95",
]
