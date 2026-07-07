"""Excess-mass bunching estimator for H-09 (Saez 2010 / Chetty et al. 2011).

Pipeline per (symbol, window, kink) cell — every number registered (registry
H-09, DEC-19; constants in :mod:`kinks`):

1. **Order aggregation** — consecutive ``publicTrade`` records with identical
   symbol/side/``ts_exchange_ms`` are merged into one taker-order aggregate;
   its notional is ``sum(price * size)`` (symbol is fixed per loaded array).
2. **Binning** — order notionals binned relative to the kink ``K``:
   band ``[0.40*K, 1.30*K)``, 90 bins of width ``0.01*K`` (half-open
   ``[lo, hi)`` bins).
3. **Counterfactual** — polynomial of degree 7 fitted to the bin counts,
   EXCLUDING the bins covering ``[0.90*K, 1.10*K)`` (20 bins); evaluated on
   all 90 bins.
4. **Excess mass** — ``b_hat- = sum_{B-}(C_j - Chat_j) / mean_{B-}(Chat_j)``
   over the bunching window ``B- = [0.95*K, 1.00*K)`` (5 bins), and the
   analogous ``b_hat+`` over the control window ``B+ = (1.00*K, 1.05*K]``.
   Boundary fidelity for B+: mass exactly AT ``1.00*K`` is excluded and mass
   exactly AT ``1.05*K`` (which the half-open binning puts into the next bin)
   is included in the observed B+ count.
5. **Residual bootstrap** (500 reps, seed-fixed): the null is the SMOOTH
   polynomial density (registry: "Bootstrap-Null b- = 0"). Residuals from the
   included bins are resampled with replacement onto the fitted counterfactual
   for ALL 90 bins, the polynomial is re-fitted, and ``b_hat-*`` recomputed;
   ``p = (#{b* >= b_obs} + 1) / (N + 1)`` (one-sided, add-one convention as in
   the C-01/C-06/C-17 packages).
6. **Placebos** ``P1 = 0.50*K``, ``P2 = 0.75*K``: the FULL estimator re-run
   with the placebo value as pseudo-kink (band/bins scaled to it). No
   bootstrap p is needed for placebos (the gate only compares ``b_hat``).

KAPITALFREI: notional counts and dimensionless excess-mass ratios only.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .kinks import (
    BAND_HI_REL,
    BAND_LO_REL,
    BIN_WIDTH_REL,
    BUNCH_HI_REL,
    BUNCH_LO_REL,
    CF_EXPECTATION_FLOOR,
    CTRL_HI_REL,
    CTRL_LO_REL,
    EXCLUDE_HI_REL,
    EXCLUDE_LO_REL,
    N_BINS,
    N_BOOTSTRAP,
    N_FLOOR_ORDERS,
    PLACEBO_FRACTIONS,
    POLY_DEGREE,
)

# Integer bin-index geometry derived ONCE from the registered relative bounds
# (rounding guards against float artefacts; bin j covers
# [0.40 + 0.01*j, 0.40 + 0.01*(j+1)) * K).
_J_EXCL_LO = round((EXCLUDE_LO_REL - BAND_LO_REL) / BIN_WIDTH_REL)   # 50
_J_EXCL_HI = round((EXCLUDE_HI_REL - BAND_LO_REL) / BIN_WIDTH_REL)   # 70 (excl.)
_J_BUNCH_LO = round((BUNCH_LO_REL - BAND_LO_REL) / BIN_WIDTH_REL)    # 55
_J_BUNCH_HI = round((BUNCH_HI_REL - BAND_LO_REL) / BIN_WIDTH_REL)    # 60 (excl.)
_J_CTRL_LO = round((CTRL_LO_REL - BAND_LO_REL) / BIN_WIDTH_REL)      # 60
_J_CTRL_HI = round((CTRL_HI_REL - BAND_LO_REL) / BIN_WIDTH_REL)      # 65 (excl.)

EXCLUDED_BINS = np.arange(_J_EXCL_LO, _J_EXCL_HI)
BUNCH_BINS = np.arange(_J_BUNCH_LO, _J_BUNCH_HI)
CTRL_BINS = np.arange(_J_CTRL_LO, _J_CTRL_HI)
INCLUDED_MASK = np.ones(N_BINS, dtype=bool)
INCLUDED_MASK[EXCLUDED_BINS] = False

_EPS = 1e-12


def aggregate_orders(
    ts: np.ndarray, side: np.ndarray, price: np.ndarray, volume: np.ndarray
) -> np.ndarray:
    """Merge consecutive same-side/same-``ts_exchange_ms`` records into orders.

    Input arrays are one symbol's ``publicTrade`` records sorted ascending by
    ``ts_exchange_ms`` (the loader guarantees this). Returns the per-order
    NOTIONAL array ``sum(price * size)`` per aggregate — the registered
    judgement-bearing observation unit (registry H-09 Datenbindung).
    """
    ts = np.asarray(ts)
    side = np.asarray(side)
    price = np.asarray(price, dtype=np.float64)
    volume = np.asarray(volume, dtype=np.float64)
    n = ts.size
    if n == 0:
        return np.empty(0, dtype=np.float64)
    notional = price * volume
    if n == 1:
        return notional.copy()
    new_group = np.empty(n, dtype=bool)
    new_group[0] = True
    new_group[1:] = (ts[1:] != ts[:-1]) | (side[1:] != side[:-1])
    starts = np.flatnonzero(new_group)
    return np.add.reduceat(notional, starts)


def bin_centers_rel() -> np.ndarray:
    """Relative (kink = 1.0) bin centers of the 90 estimation-band bins."""
    return BAND_LO_REL + BIN_WIDTH_REL * (np.arange(N_BINS) + 0.5)


def bin_notionals(notionals: np.ndarray, kink: float) -> tuple[np.ndarray, int]:
    """Bin order notionals into the 90 half-open ``[lo, hi)`` band bins.

    Returns ``(counts, n_in_band)``. Notionals outside ``[0.40*K, 1.30*K)``
    are dropped (not part of the estimation band).
    """
    x = np.asarray(notionals, dtype=np.float64)
    if kink <= 0:
        raise ValueError(f"kink must be > 0, got {kink}")
    r = x / float(kink)
    j = np.floor((r - BAND_LO_REL) / BIN_WIDTH_REL + 1e-9).astype(np.int64)
    ok = (r >= BAND_LO_REL) & (r < BAND_HI_REL) & (j >= 0) & (j < N_BINS)
    counts = np.bincount(j[ok], minlength=N_BINS).astype(np.float64)
    return counts, int(ok.sum())


def fit_counterfactual(
    counts: np.ndarray, *, degree: int = POLY_DEGREE
) -> np.ndarray:
    """Degree-``degree`` polynomial counterfactual, excluding [0.90K, 1.10K).

    Fitted on the 70 included bin counts against scaled bin centers
    (conditioning), evaluated on all 90 bins. Fitted counts are floored at 0
    (counts cannot be negative).
    """
    counts = np.asarray(counts, dtype=np.float64)
    if counts.shape != (N_BINS,):
        raise ValueError(f"expected {N_BINS} bin counts, got shape {counts.shape}")
    centers = bin_centers_rel()
    # scale x to ~[-1, 1] for numerical conditioning of the degree-7 fit
    x = (centers - centers.mean()) / (0.5 * (centers[-1] - centers[0]))
    coeffs = np.polynomial.polynomial.polyfit(
        x[INCLUDED_MASK], counts[INCLUDED_MASK], deg=int(degree)
    )
    fitted = np.polynomial.polynomial.polyval(x, coeffs)
    return np.maximum(fitted, 0.0)


def _window_sums(
    counts: np.ndarray,
    fitted: np.ndarray,
    notionals: np.ndarray | None,
    kink: float,
) -> dict[str, float]:
    """Observed/counterfactual sums for B- and B+ (with B+ boundary fidelity)."""
    obs_minus = float(counts[BUNCH_BINS].sum())
    cf_minus = float(fitted[BUNCH_BINS].sum())
    obs_plus = float(counts[CTRL_BINS].sum())
    cf_plus = float(fitted[CTRL_BINS].sum())
    if notionals is not None and notionals.size:
        # B+ = (1.00*K, 1.05*K]: exact-kink mass sits in bin 60 under [lo, hi)
        # binning but is NOT in B+; exact 1.05*K mass sits in bin 65 but IS.
        obs_plus -= float(np.count_nonzero(notionals == kink))
        obs_plus += float(np.count_nonzero(notionals == CTRL_HI_REL * kink))
    return {
        "obs_minus": obs_minus,
        "cf_minus": cf_minus,
        "obs_plus": obs_plus,
        "cf_plus": cf_plus,
    }


def excess_mass(
    counts: np.ndarray,
    fitted: np.ndarray,
    *,
    notionals: np.ndarray | None = None,
    kink: float = 1.0,
) -> dict[str, float]:
    """Excess-mass ratios ``b_hat-`` (B-) and ``b_hat+`` (B+).

    ``b_hat = (observed - counterfactual mass in window) / (mean
    counterfactual count per bin in that window)`` — the Chetty et al. (2011)
    normalisation (b in units of "average counterfactual bins"). Degenerate
    (near-zero) counterfactual denominators yield ``b = 0.0`` with a flag.
    """
    s = _window_sums(np.asarray(counts, float), np.asarray(fitted, float),
                     None if notionals is None else np.asarray(notionals, float),
                     float(kink))
    mean_cf_minus = s["cf_minus"] / BUNCH_BINS.size
    mean_cf_plus = s["cf_plus"] / CTRL_BINS.size
    degenerate = bool(mean_cf_minus <= _EPS or mean_cf_plus <= _EPS)
    b_minus = 0.0 if mean_cf_minus <= _EPS else (s["obs_minus"] - s["cf_minus"]) / mean_cf_minus
    b_plus = 0.0 if mean_cf_plus <= _EPS else (s["obs_plus"] - s["cf_plus"]) / mean_cf_plus
    return {
        "b_minus": float(b_minus),
        "b_plus": float(b_plus),
        "cf_expectation_bminus": float(s["cf_minus"]),
        "cf_expectation_bplus": float(s["cf_plus"]),
        "obs_bminus": float(s["obs_minus"]),
        "obs_bplus": float(s["obs_plus"]),
        "degenerate_counterfactual": degenerate,
    }


def residual_bootstrap_p(
    counts: np.ndarray,
    fitted: np.ndarray,
    b_minus_obs: float,
    *,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    degree: int = POLY_DEGREE,
) -> tuple[float, float]:
    """One-sided residual-bootstrap p for ``H0: b- = 0`` (smooth density).

    Null replicates: fitted counterfactual + resampled included-bin residuals
    on ALL 90 bins (clipped at 0), polynomial re-fitted, ``b_hat-*``
    recomputed. ``p = (#{b* >= b_obs} + 1) / (N + 1)``. Also returns the
    bootstrap standard deviation of ``b_hat-*`` (diagnostic).
    """
    counts = np.asarray(counts, dtype=np.float64)
    fitted = np.asarray(fitted, dtype=np.float64)
    if n_bootstrap < 1:
        return 1.0, 0.0
    residuals = (counts - fitted)[INCLUDED_MASK]
    rng = np.random.default_rng(seed)
    b_null = np.empty(n_bootstrap, dtype=np.float64)
    for k in range(n_bootstrap):
        e = rng.choice(residuals, size=N_BINS, replace=True)
        c_star = np.maximum(fitted + e, 0.0)
        f_star = fit_counterfactual(c_star, degree=degree)
        b_null[k] = excess_mass(c_star, f_star)["b_minus"]
    n_ge = int(np.sum(b_null >= b_minus_obs))
    p = (n_ge + 1) / (n_bootstrap + 1)
    return float(p), float(np.std(b_null))


def estimate_cell(
    notionals: np.ndarray,
    kink: float,
    *,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    n_floor_orders: int = N_FLOOR_ORDERS,
    cf_expectation_floor: float = CF_EXPECTATION_FLOOR,
    with_placebos: bool = True,
) -> dict[str, Any]:
    """Full registered estimator for one (symbol, window) cell at kink ``K``.

    Returns the gate-neutral per-cell measurement dict: binning, degree-7
    counterfactual, ``b_hat-``/``b_hat+``, residual-bootstrap p, N-floor
    validity, and the two placebo re-estimations (``with_placebos=True``;
    placebos themselves are estimated WITHOUT bootstrap/placebos).
    """
    notionals = np.asarray(notionals, dtype=np.float64)
    counts, n_in_band = bin_notionals(notionals, kink)
    fitted = fit_counterfactual(counts)
    em = excess_mass(counts, fitted, notionals=notionals, kink=kink)
    p_boot, b_null_sd = residual_bootstrap_p(
        counts, fitted, em["b_minus"], n_bootstrap=n_bootstrap, seed=seed,
    )
    n_floor_met = bool(n_in_band >= n_floor_orders)
    cf_floor_met = bool(em["cf_expectation_bminus"] >= cf_expectation_floor)
    cell: dict[str, Any] = {
        "kink_usdt": float(kink),
        "n_orders_total": int(notionals.size),
        "n_orders_in_band": int(n_in_band),
        "bin_counts": [int(c) for c in counts],
        "b_minus": em["b_minus"],
        "b_plus": em["b_plus"],
        "b_asymmetry": float(em["b_minus"] - em["b_plus"]),
        "obs_bminus": em["obs_bminus"],
        "obs_bplus": em["obs_bplus"],
        "cf_expectation_bminus": em["cf_expectation_bminus"],
        "cf_expectation_bplus": em["cf_expectation_bplus"],
        "degenerate_counterfactual": em["degenerate_counterfactual"],
        "bootstrap_p": float(p_boot),
        "bootstrap_b_null_sd": float(b_null_sd),
        "n_bootstrap": int(n_bootstrap),
        "n_floor_met": n_floor_met,
        "cf_floor_met": cf_floor_met,
        "cell_valid": bool(n_floor_met and cf_floor_met),
    }
    if with_placebos:
        placebos: dict[str, Any] = {}
        for frac in PLACEBO_FRACTIONS:
            pk = float(frac) * float(kink)
            p_counts, p_n = bin_notionals(notionals, pk)
            p_fitted = fit_counterfactual(p_counts)
            p_em = excess_mass(p_counts, p_fitted, notionals=notionals, kink=pk)
            placebos[f"P_{frac:.2f}"] = {
                "placebo_kink_usdt": pk,
                "n_orders_in_band": int(p_n),
                "b_minus": p_em["b_minus"],
                "b_plus": p_em["b_plus"],
                "cf_expectation_bminus": p_em["cf_expectation_bminus"],
                "degenerate_counterfactual": p_em["degenerate_counterfactual"],
            }
        cell["placebos"] = placebos
        cell["b_placebo_max"] = float(
            max(p["b_minus"] for p in placebos.values())
        )
    return cell
