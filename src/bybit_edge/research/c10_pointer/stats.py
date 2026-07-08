"""Stage-1/Stage-2 null statistics + BH-FDR for the H-10 pointer gate.

  * Stage 1 (``stage1_surrogate_p``): 1,000 CIRCULAR surrogates per series —
    each replicate independently circularly shifts every score column over the
    usable range (preserving each series' marginal score distribution and
    autocorrelation, destroying CROSS-series alignment) and recounts pointer
    days per window. One-sided empirical p:
        p = (#{N_surr >= N_obs} + 1) / (n_surrogates + 1).
  * Stage 2 (``dvol_index`` / ``delta_pre`` / ``stage2_permutation_p``): the
    HELD-OUT dvol index D_t = mean of the PER-SERIES z-scored BTC+ETH dvol
    daily closes, z-parameters over the usable (non-burn-in) period
    (hardened_hypotheses.md H-10; DEC-21);
    pre-event drift Delta_pre(t) = mean(D, [t-5, t-1]) - mean(D, [t-15, t-6]);
    statistic S = mean of Delta_pre over the window's pointer days. Null:
    1,000 permutation draws of equally-sized random day sets from the window,
    each candidate day >= 6 days away from EVERY pointer day; TWO-sided
    empirical p = min(1, 2 * min(p_low, p_high)).
  * ``benjamini_hochberg`` — OWN copy (registry §8.2 convention: each research
    package keeps its own; no cross-import between research packages).

Gate-neutral: all functions return measurements; no verdict logic here.
KAPITALFREI: pure statistics. numpy only.
"""
from __future__ import annotations

import numpy as np

from .cropper import C_THRESH, N_AVAIL_FLOOR, SHARE_FLOOR, detect_pointer_days

#: BH-FDR level for the F-POINTER family (registry H-10).
FDR_ALPHA = 0.10

#: FDR family name (registry H-10: 4 cells = 2 stages x 2 windows).
FDR_FAMILY = "F-POINTER"

#: Stage-1/Stage-2 p threshold (registry H-10: p <= 0.05).
SURROGATE_P_MAX = 0.05

#: Hard pointer-day floor per window (registry H-10: >= 3, NOT lowerable).
N_POINTER_FLOOR = 3

#: Minimum distance (days) of a stage-2 null day to EVERY pointer day.
MIN_NULL_GAP_DAYS = 6

#: Pre-event near window [t-5, t-1] and far window [t-15, t-6] (registry).
PRE_NEAR = (5, 1)
PRE_FAR = (15, 6)


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i`` is
    significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. OWN copy (registry §8.2 convention —
    each research package keeps its own; no cross-import between packages).
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


# ----------------------------------------------------------------------------
# Stage 1 — circular-surrogate null for the pointer-day count
# ----------------------------------------------------------------------------

def stage1_surrogate_p(
    scores_usable: np.ndarray,
    window_masks: list[np.ndarray],
    *,
    n_surrogates: int = 1000,
    seed: int = 42,
    c_thresh: float = C_THRESH,
    share_floor: float = SHARE_FLOOR,
    n_avail_floor: int = N_AVAIL_FLOOR,
) -> list[dict[str, float]]:
    """Circular-surrogate p per window for the observed pointer-day count.

    ``scores_usable`` is the (T_u x N) Cropper-score matrix restricted to the
    USABLE range (burn-in already removed — circular shifts then move only
    genuinely usable score positions, so the per-series marginal availability
    is preserved exactly). ``window_masks[w]`` is a (T_u,) boolean mask.

    Each replicate draws one independent circular offset in ``1..T_u-1`` per
    series (never 0 — the observed alignment is excluded), rolls every column,
    and recounts pointer days per window. Returns per window a dict with
    ``n_pointer_observed``, ``surrogate_p``, ``surrogate_mean`` and
    ``surrogate_max``.
    """
    C = np.asarray(scores_usable, dtype=np.float64)
    t_u, n_series = C.shape
    obs = detect_pointer_days(
        C, c_thresh=c_thresh, share_floor=share_floor, n_avail_floor=n_avail_floor,
    )
    n_obs = [int(np.sum(obs.is_pointer & m)) for m in window_masks]

    rng = np.random.default_rng(seed)
    counts = np.zeros((n_surrogates, len(window_masks)), dtype=np.int64)
    Cs = np.empty_like(C)
    for k in range(n_surrogates):
        if t_u > 1:
            shifts = rng.integers(1, t_u, size=n_series)
        else:  # degenerate single-day range
            shifts = np.zeros(n_series, dtype=np.int64)
        for j in range(n_series):
            Cs[:, j] = np.roll(C[:, j], int(shifts[j]))
        surr = detect_pointer_days(
            Cs, c_thresh=c_thresh, share_floor=share_floor, n_avail_floor=n_avail_floor,
        )
        for w, m in enumerate(window_masks):
            counts[k, w] = int(np.sum(surr.is_pointer & m))

    out: list[dict[str, float]] = []
    for w in range(len(window_masks)):
        n_ge = int(np.sum(counts[:, w] >= n_obs[w]))
        p = (n_ge + 1) / (n_surrogates + 1)
        out.append({
            "n_pointer_observed": float(n_obs[w]),
            "surrogate_p": float(p),
            "surrogate_mean": float(np.mean(counts[:, w])) if n_surrogates else float("nan"),
            "surrogate_max": float(np.max(counts[:, w])) if n_surrogates else float("nan"),
        })
    return out


# ----------------------------------------------------------------------------
# Stage 2 — held-out dvol pre-event drift vs. permutation null
# ----------------------------------------------------------------------------

def dvol_index(dvol_btc: np.ndarray, dvol_eth: np.ndarray,
               usable_mask: np.ndarray | None = None) -> np.ndarray:
    """Held-out dvol index D_t = mean of the per-series z-scored daily closes.

    Hardened spec (hardened_hypotheses.md, H-10 "Zielgröße Stufe 2", followed
    per DEC-21 in state/decisions.md): "D_t = Mittel der (über den nutzbaren
    Zeitraum z-standardisierten) BTC- und ETH-dvol-Tagesschlüsse" — z-score
    EACH series FIRST (mu/sd with ddof=1, estimated over the USABLE
    non-burn-in days given by ``usable_mask``; None = all days), THEN average
    the two z-series per day. NOT equivalent to z(mean(levels)) when the
    BTC/ETH dvol scales differ (audit_h10 BUG-2b). The affine z-transform is
    applied to the FULL grid (so Delta_pre look-back windows that reach into
    the burn-in stay defined), while its parameters come from the usable
    period only (BUG-2c). Per-day nan-tolerant mean: if one symbol is missing
    on a day the other carries the index (availability robustness,
    documented). A series with fewer than 2 usable finite days or zero
    usable-period variance contributes NaN.
    """
    b = np.asarray(dvol_btc, dtype=np.float64)
    e = np.asarray(dvol_eth, dtype=np.float64)
    if b.shape != e.shape:
        raise ValueError("dvol series must share the daily grid")
    if usable_mask is None:
        usable = np.ones(b.size, dtype=bool)
    else:
        usable = np.asarray(usable_mask, dtype=bool)
        if usable.shape != b.shape:
            raise ValueError("usable_mask must share the daily grid")

    def _z(x: np.ndarray) -> np.ndarray:
        z = np.full(x.size, np.nan, dtype=np.float64)
        fit = usable & np.isfinite(x)
        if int(fit.sum()) < 2:
            return z
        mu = float(np.mean(x[fit]))
        sd = float(np.std(x[fit], ddof=1))
        if sd <= 0.0 or not np.isfinite(sd):
            return z
        finite = np.isfinite(x)
        z[finite] = (x[finite] - mu) / sd
        return z

    stacked = np.vstack([_z(b), _z(e)])
    with np.errstate(invalid="ignore"):
        out = np.nanmean(stacked, axis=0)
    return out


def delta_pre(
    d_index: np.ndarray,
    *,
    min_finite_near: int = 3,
    min_finite_far: int = 6,
) -> np.ndarray:
    """Pre-event drift Delta_pre(t) = mean(D,[t-5,t-1]) - mean(D,[t-15,t-6]).

    Strictly uses days BEFORE t. NaN where t < 15 or too few finite values in
    a sub-window (>= 3 of 5 near, >= 6 of 10 far — gap robustness, documented).
    """
    D = np.asarray(d_index, dtype=np.float64)
    n = D.size
    out = np.full(n, np.nan, dtype=np.float64)
    near_hi, near_lo_off = PRE_NEAR  # offsets 5..1
    far_hi, far_lo_off = PRE_FAR     # offsets 15..6
    for t in range(far_hi, n):
        near = D[t - near_hi: t - near_lo_off + 1]
        far = D[t - far_hi: t - far_lo_off + 1]
        near = near[np.isfinite(near)]
        far = far[np.isfinite(far)]
        if near.size >= min_finite_near and far.size >= min_finite_far:
            out[t] = float(np.mean(near)) - float(np.mean(far))
    return out


def stage2_permutation_p(
    dpre: np.ndarray,
    pointer_idx_all: np.ndarray,
    window_idx: np.ndarray,
    *,
    n_draws: int = 1000,
    min_gap_days: int = MIN_NULL_GAP_DAYS,
    seed: int = 42,
) -> dict[str, float]:
    """Two-sided permutation p for S = mean(Delta_pre over window pointer days).

    ``dpre`` on the FULL daily grid; ``pointer_idx_all`` = GLOBAL indices of
    ALL pointer days (both windows — every candidate null day must keep
    >= ``min_gap_days`` distance to EVERY pointer day, registry wording);
    ``window_idx`` = global indices of the window's days. The null draws
    ``n_draws`` random day sets WITHOUT replacement, each the same size as the
    observed (finite-Delta_pre) pointer set, from the eligible in-window pool.
    Two-sided empirical p = min(1, 2 * min(p_low, p_high)). If the statistic
    or the pool is undefined/too small, returns p = NaN with a reason flag
    (the driver maps that to a failing, gate-neutral 1.0 for BH).
    """
    dpre = np.asarray(dpre, dtype=np.float64)
    pointer_idx_all = np.asarray(pointer_idx_all, dtype=np.int64)
    window_idx = np.asarray(window_idx, dtype=np.int64)

    pointer_set = set(pointer_idx_all.tolist())
    pts = np.array([i for i in window_idx if int(i) in pointer_set], dtype=np.int64)
    pts_finite = pts[np.isfinite(dpre[pts])] if pts.size else pts
    n_pointer_used = int(pts_finite.size)
    s_obs = float(np.mean(dpre[pts_finite])) if n_pointer_used > 0 else float("nan")

    # Eligible null pool: in-window, finite Delta_pre, >= min_gap to EVERY pointer day.
    if pointer_idx_all.size:
        gaps = np.min(np.abs(window_idx[:, None] - pointer_idx_all[None, :]), axis=1)
    else:
        gaps = np.full(window_idx.size, np.inf)
    eligible = window_idx[(gaps >= min_gap_days) & np.isfinite(dpre[window_idx])]

    base = {
        "n_pointer_in_window": float(pts.size),
        "n_pointer_used": float(n_pointer_used),
        "s_observed": s_obs,
        "n_eligible_null_days": float(eligible.size),
        "n_draws": float(n_draws),
    }
    if n_pointer_used < 1 or not np.isfinite(s_obs):
        return {**base, "permutation_p_two_sided": float("nan"),
                "p_undefined_reason": 1.0}  # 1.0 = no usable pointer days
    if eligible.size < n_pointer_used:
        return {**base, "permutation_p_two_sided": float("nan"),
                "p_undefined_reason": 2.0}  # 2.0 = null pool too small

    rng = np.random.default_rng(seed)
    stats = np.empty(n_draws, dtype=np.float64)
    for k in range(n_draws):
        pick = rng.choice(eligible, size=n_pointer_used, replace=False)
        stats[k] = float(np.mean(dpre[pick]))
    p_low = (int(np.sum(stats <= s_obs)) + 1) / (n_draws + 1)
    p_high = (int(np.sum(stats >= s_obs)) + 1) / (n_draws + 1)
    p_two = min(1.0, 2.0 * min(p_low, p_high))
    return {**base, "permutation_p_two_sided": float(p_two),
            "null_mean": float(np.mean(stats)), "p_undefined_reason": 0.0}


__all__ = [
    "FDR_ALPHA",
    "FDR_FAMILY",
    "MIN_NULL_GAP_DAYS",
    "N_POINTER_FLOOR",
    "PRE_FAR",
    "PRE_NEAR",
    "SURROGATE_P_MAX",
    "benjamini_hochberg",
    "delta_pre",
    "dvol_index",
    "stage1_surrogate_p",
    "stage2_permutation_p",
]
