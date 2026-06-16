"""Main-Gate: conditional information PE -> ret/vol_{t+delta} + block-shift
surrogate null + BH-FDR + G1 AUC-lift for the C-07 PE mess-gate
(Welle-2 WP, H-06, KAPITALFREI).

After the PRE-Gate passes, the main gate (registry H-06) asks whether the PE
series carries conditional information about the forward target beyond a
surrogate null:

* ``mi``            = mutual information I(PE_t ; target_{t+delta}) via
                      equal-frequency quantile binning (DEC-12, ``DEFAULT_N_BINS``),
* ``surrogate_p``   = block-shift permutation p (the PE series is circularly
                      shifted against the fixed targets, destroying the coupling
                      while preserving each series' marginal AND autocorrelation;
                      N >= 200, analog H-03 / DEC-09),
* ``auc_lift``      = conditional AUC lift in G1 windows minus the 0.5 chance
                      baseline, where G1 = top vol quartile of the surrogate-null
                      distribution (registry H-06: "G1 = oberstes Vol-Quartil der
                      Surrogate-Null-Verteilung, vorab fixiert").

WEITER (registry H-06): PRE-Gate passed UND surrogate-p <= 0.05 after BH-FDR
alpha = 0.10 over F-ENTROPY (all window-length x delta x symbol conditionings)
UND existence in >= 2 disjoint windows UND conditional AUC-lift >= +0.03 in G1
windows. Hard one-window criterion (PRD §8.5). This module reports each criterion
PER VARIANT; it renders NO verdict.

KAPITALFREI: pure information measurement. No friction, edge, bps, PnL, Sharpe
logic. numpy only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: BH-FDR level for the F-ENTROPY family (registry H-06).
FDR_ALPHA = 0.10

#: Registered main-gate thresholds (registry H-06) — reported, not adjudicated.
SURROGATE_P_MAX = 0.05
AUC_LIFT_FLOOR = 0.03

#: Default MI quantile bins (DEC-12). 4 equal-frequency bins keep the joint
#: histogram small (n_bins^2 = 16) for a low-bias plug-in MI from a few thousand
#: bars; equal-frequency is robust to crypto heavy tails. CLI ``--n-bins``.
DEFAULT_N_BINS = 4

#: Minimum block-shift offset as a fraction of the series length (surrogate).
MIN_SHIFT_FRAC = 0.05


def _quantile_bin(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Equal-frequency quantile bin labels in ``[0, n_bins)`` for ``x``.

    Ties / degenerate edges collapse to fewer effective bins (handled by
    ``np.digitize`` on unique quantile edges).
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return np.zeros(0, dtype=np.int64)
    qs = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
    edges = np.unique(np.quantile(x, qs))
    if edges.size == 0:
        return np.zeros(x.size, dtype=np.int64)
    return np.digitize(x, edges).astype(np.int64)


def mutual_information(x: np.ndarray, y: np.ndarray, n_bins: int = DEFAULT_N_BINS) -> float:
    """Plug-in mutual information I(X;Y) in nats via equal-frequency binning.

    Both series are discretised into ``n_bins`` equal-frequency bins; MI is the
    plug-in estimate from the joint histogram. Returns 0.0 for < 3 finite pairs.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = min(x.size, y.size)
    if n < 3:
        return 0.0
    x, y = x[:n], y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    if int(np.sum(mask)) < 3:
        return 0.0
    xb = _quantile_bin(x[mask], n_bins)
    yb = _quantile_bin(y[mask], n_bins)
    nx = int(xb.max()) + 1
    ny = int(yb.max()) + 1
    if nx < 2 or ny < 2:
        return 0.0
    joint = np.zeros((nx, ny), dtype=np.float64)
    np.add.at(joint, (xb, yb), 1.0)
    total = joint.sum()
    if total <= 0:
        return 0.0
    pxy = joint / total
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    denom = px @ py
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where((pxy > 0) & (denom > 0), pxy / denom, 1.0)
        terms = np.where(pxy > 0, pxy * np.log(ratio), 0.0)
    mi = float(np.sum(terms))
    return max(0.0, mi)


def block_shift_surrogate_p(
    pe: np.ndarray,
    target: np.ndarray,
    observed_mi: float,
    *,
    n_bins: int = DEFAULT_N_BINS,
    n_surrogates: int = 200,
    seed: int = 42,
) -> tuple[float, float]:
    """Block-shift permutation p for MI(PE, target).

    Each surrogate circularly shifts the PE series by a random offset
    ``>= MIN_SHIFT_FRAC * n`` against the fixed target, destroying the PE->target
    coupling while preserving each series' marginal and autocorrelation. Empirical
    ``p = (#{MI_surrogate >= MI_observed} + 1) / (N + 1)``. Returns
    ``(p_value, surrogate_mi_mean)``.
    """
    pe = np.asarray(pe, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(pe.size, target.size)
    if n < 8 or n_surrogates < 1:
        return 1.0, 0.0
    pe, target = pe[:n], target[:n]
    rng = np.random.default_rng(seed)
    min_shift = max(1, int(MIN_SHIFT_FRAC * n))
    max_shift = n - min_shift
    if max_shift <= min_shift:
        return 1.0, 0.0
    stats = np.empty(n_surrogates, dtype=np.float64)
    for k in range(n_surrogates):
        shift = int(rng.integers(min_shift, max_shift + 1))
        stats[k] = mutual_information(np.roll(pe, shift), target, n_bins)
    n_ge = int(np.sum(stats >= observed_mi))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    return p_value, float(np.mean(stats))


def _auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """ROC-AUC of ``scores`` vs. binary ``labels`` via the rank (Mann-Whitney) form.

    Returns 0.5 (chance) when one class is absent or there are too few points.
    """
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels).astype(int)
    mask = np.isfinite(scores)
    scores, labels = scores[mask], labels[mask]
    n_pos = int(np.sum(labels == 1))
    n_neg = int(np.sum(labels == 0))
    if n_pos == 0 or n_neg == 0:
        return 0.5
    order = np.argsort(scores, kind="stable")
    ranks = np.empty(scores.size, dtype=np.float64)
    ranks[order] = np.arange(1, scores.size + 1, dtype=np.float64)
    # average ties
    _, inv, counts = np.unique(scores, return_inverse=True, return_counts=True)
    sums = np.zeros(counts.size, dtype=np.float64)
    np.add.at(sums, inv, ranks)
    ranks = (sums / counts)[inv]
    sum_pos = float(np.sum(ranks[labels == 1]))
    auc = (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return max(0.0, min(1.0, auc))


def g1_auc_lift(
    pe_drop_series: np.ndarray,
    forward_rv: np.ndarray,
    surrogate_rv_dist: np.ndarray,
) -> tuple[float, int]:
    """Conditional AUC-lift of PE-drop for high-vol direction in G1 windows.

    G1 (registry H-06) = the top vol quartile of the SURROGATE-NULL distribution
    (pre-fixed). Concretely: the 75th-percentile of ``surrogate_rv_dist`` defines
    the G1 threshold; the G1 bars are those whose forward RV exceeds it. On the
    G1 bars the binary label is "forward RV in the upper half of the G1 subset"
    (high-vol event) and the score is the PE-drop (a complexity collapse should
    flag the coming high-vol bar). AUC-lift = AUC(G1) - 0.5.

    Returns ``(auc_lift, n_g1)`` where ``n_g1`` is the G1 window/bar count.
    """
    pd_ = np.asarray(pe_drop_series, dtype=np.float64)
    rv = np.asarray(forward_rv, dtype=np.float64)
    surr = np.asarray(surrogate_rv_dist, dtype=np.float64)
    n = min(pd_.size, rv.size)
    pd_, rv = pd_[:n], rv[:n]
    mask = np.isfinite(pd_) & np.isfinite(rv)
    pd_, rv = pd_[mask], rv[mask]
    surr = surr[np.isfinite(surr)]
    if pd_.size < 8 or surr.size < 4:
        return 0.0, 0
    g1_thr = float(np.quantile(surr, 0.75))
    g1 = rv >= g1_thr
    n_g1 = int(np.sum(g1))
    if n_g1 < 4:
        return 0.0, n_g1
    rv_g1 = rv[g1]
    pd_g1 = pd_[g1]
    # high-vol label within G1 = upper half of the G1 RV (directional event)
    med = float(np.median(rv_g1))
    labels = (rv_g1 > med).astype(int)
    if labels.sum() == 0 or labels.sum() == labels.size:
        return 0.0, n_g1
    auc = _auc(pd_g1, labels)
    return float(auc - 0.5), n_g1


@dataclass(slots=True)
class InfoTestResult:
    """Main-gate outcome for one (delta) variant in one window."""

    delta_min: float
    n_pairs: int
    mi: float
    surrogate_p: float
    surrogate_mi_mean: float
    n_surrogates: int
    auc_lift: float
    n_g1: int

    def as_dict(self) -> dict[str, object]:
        return {
            "delta_min": float(self.delta_min),
            "n_pairs": int(self.n_pairs),
            "mi": float(self.mi),
            "surrogate_p": float(self.surrogate_p),
            "surrogate_mi_mean": float(self.surrogate_mi_mean),
            "n_surrogates": int(self.n_surrogates),
            "auc_lift": float(self.auc_lift),
            "n_g1": int(self.n_g1),
        }


def info_test(
    pe_series: np.ndarray,
    pe_drop_series: np.ndarray,
    target: np.ndarray,
    forward_rv: np.ndarray,
    delta_min: float,
    *,
    n_bins: int = DEFAULT_N_BINS,
    n_surrogates: int = 200,
    seed: int = 42,
) -> InfoTestResult:
    """Run the full main-gate test for one delta on aligned causal series.

    ``target`` is the forward target at delta (forward RV or |forward ret|);
    ``forward_rv`` is the 15-min forward RV used to build G1. The surrogate-null
    RV distribution for G1 is generated by block-shifting the PE-drop series
    against the forward RV and recording the conditional RV under each shift's
    high-PE-drop bars (so G1 = top vol quartile of the surrogate null).
    """
    pe = np.asarray(pe_series, dtype=np.float64)
    pd_ = np.asarray(pe_drop_series, dtype=np.float64)
    tg = np.asarray(target, dtype=np.float64)
    n = min(pe.size, tg.size)
    if n < 8:
        return InfoTestResult(
            delta_min=delta_min, n_pairs=n, mi=0.0, surrogate_p=1.0,
            surrogate_mi_mean=0.0, n_surrogates=0, auc_lift=0.0, n_g1=0,
        )
    pe_n, tg_n = pe[:n], tg[:n]
    fin = np.isfinite(pe_n) & np.isfinite(tg_n)
    n_pairs = int(np.sum(fin))
    mi = mutual_information(pe_n[fin], tg_n[fin], n_bins)
    p_value, surr_mean = block_shift_surrogate_p(
        pe_n[fin], tg_n[fin], mi, n_bins=n_bins,
        n_surrogates=n_surrogates, seed=seed,
    )
    # Surrogate-null RV distribution for the G1 threshold: block-shift the
    # PE-drop series against the forward RV and collect RV under each shift.
    surr_rv = _surrogate_rv_distribution(pd_, forward_rv, n_surrogates=n_surrogates, seed=seed)
    auc_lift, n_g1 = g1_auc_lift(pd_, forward_rv, surr_rv)
    return InfoTestResult(
        delta_min=delta_min,
        n_pairs=n_pairs,
        mi=mi,
        surrogate_p=p_value,
        surrogate_mi_mean=surr_mean,
        n_surrogates=n_surrogates,
        auc_lift=auc_lift,
        n_g1=n_g1,
    )


def _surrogate_rv_distribution(
    pe_drop_series: np.ndarray,
    forward_rv: np.ndarray,
    *,
    n_surrogates: int,
    seed: int,
) -> np.ndarray:
    """Surrogate-null forward-RV distribution for the G1 threshold.

    Block-shifts the PE-drop series against the (fixed) forward RV and, for each
    shift, records the forward RV at the bars the shifted PE-drop flags as a
    complexity collapse (top-quartile PE-drop). The pooled RVs form the
    surrogate-null vol distribution whose top quartile defines G1.
    """
    pd_ = np.asarray(pe_drop_series, dtype=np.float64)
    rv = np.asarray(forward_rv, dtype=np.float64)
    n = min(pd_.size, rv.size)
    pd_, rv = pd_[:n], rv[:n]
    mask = np.isfinite(pd_) & np.isfinite(rv)
    pd_, rv = pd_[mask], rv[mask]
    if pd_.size < 8:
        return rv
    rng = np.random.default_rng(seed + 99991)
    min_shift = max(1, int(MIN_SHIFT_FRAC * pd_.size))
    max_shift = pd_.size - min_shift
    if max_shift <= min_shift:
        return rv
    pool: list[np.ndarray] = []
    n_draw = max(1, min(n_surrogates, 100))
    for _ in range(n_draw):
        shift = int(rng.integers(min_shift, max_shift + 1))
        shifted = np.roll(pd_, shift)
        thr = float(np.quantile(shifted, 0.75))
        pool.append(rv[shifted >= thr])
    if not pool:
        return rv
    return np.concatenate(pool)


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i`` is
    significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. Identical contract to the C-31 / C-17 /
    C-01 implementations (registry §8.2 convention; each research package keeps
    its own copy — no cross-import between research packages).
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
