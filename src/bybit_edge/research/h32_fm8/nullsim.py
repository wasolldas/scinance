"""Factor-preserving null of the third version with 8 beta lead weeks (Vorlauf v6, ERSTFASSUNG 1.6, Review B-7/B-8).

Per replicate a signal-free panel ``returns = beta_i f_t + e_it`` is simulated over **8 lead weeks + the window**
(``nulls.simulate_factor_panel``: market column := factor, AR(1) factor with the window's stress ``rho_f`` / ``beta_sd``,
drift 0 or 0.002); the 8-week PIT betas are estimated on the simulated panel with the REAL missingness pattern
(``returns_valid`` of the lead weeks and the window: DEC-85 (iii)); the beta control is the registered fm_neutral_8w
(``ic.fm_neutralize_outcome``, identical to ``ic.apply_beta_control``) and the weekly IC of the four proxy
characteristics is ``ic.weekly_ic_series`` on the REAL alive masks.  The window mean runs over the ``w_judged`` judged
weeks (52 / 50 / 114), all of them with a beta -- the v5e simulation lost the first 8 weeks (45 / 44).

Frozen per window and variant (in the registered direction ``y = s * IC``):

  * ``se_mean``   -- SD of the window mean over the replicates;
  * ``e_se_rule`` -- expectation over the replicates of the SE by rule P-1 (4) (floor, SD, stationary bootstrap as in the
                     run, Review B-7);
  * ``sd_week``   -- pooled SD of the weekly IC;
  * ``null_mean`` -- mean of the window mean (``m`` of the power line; ``m_P`` for the pilot period);
  * ``q95``       -- 95 % quantile of the window mean;
  * ``ceiling_k4``-- mean over the replicates of the maximum over the 4 variants of the signed window means (driftfree).

``se_mean``, ``e_se_rule``, ``sd_week``, ``null_mean`` and ``q95`` are the more extreme (larger) of the driftfree and
the drift 0.002 cell (stricter reading); both cells are reported.
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np

from ..wp13_xsec import characteristics, ic, nulls
from . import constants as C
from . import estimators as est
from .weekly import Window

__all__ = ["simulate_fm8_cell", "window_null_constants", "DRIFTS"]

DRIFTS: dict[str, float] = {"driftfree": nulls.DRIFT_F_DRIFTFREE, "drifting": nulls.DRIFT_F_DRIFTING}


def simulate_fm8_cell(
    win: Window, *, rho_f: float, beta_sd: float, drift_f: float, sigma_f: float, sigma_e: float, n_reps: int,
    seed: int = C.SEED, floor_fm8: float | None = None, n_boot: int = C.N_BOOT_MIN, mean_block: float = C.MEAN_BLOCK,
    boot_seed: int = C.SEED, variants: tuple[str, ...] = C.VARIANTS,
    progress: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    """One null cell (one ``rho_f`` / ``beta_sd`` / drift configuration), ``n_reps`` replicates, all ``variants``.
    ``floor_fm8`` ``None`` skips the SE-rule expectation (``e_se_rule`` is then NaN)."""
    symbols = win.symbols
    n_sym = len(symbols)
    lead = win.alive_ext.shape[0] - win.n_weeks
    n_ext = win.alive_ext.shape[0]
    if lead != C.LEAD_WEEKS:
        raise ValueError(f"window {win.name}: expected {C.LEAD_WEEKS} lead weeks, got {lead}")
    if C.MARKET_SYMBOL not in symbols:
        raise ValueError(f"{C.MARKET_SYMBOL} missing from the symbols (the market column is the factor, DEC-85 (i))")
    m_idx = symbols.index(C.MARKET_SYMBOL)
    w_j = win.w_judged
    rng = np.random.default_rng(seed)
    raw_means: dict[str, list[float]] = {v: [] for v in variants}
    se_vals: dict[str, list[float]] = {v: [] for v in variants}
    pool: dict[str, list[np.ndarray]] = {v: [] for v in variants}
    for rep in range(int(n_reps)):
        sim = nulls.simulate_factor_panel(n_ext, n_sym, sigma_f=sigma_f, sigma_e=sigma_e, rho_f=rho_f, drift_f=drift_f,
                                          rng=rng, beta_sd=beta_sd, market_index=m_idx)
        r = sim["returns"]
        est_r = np.where(win.valid_ext, r, np.nan)                       # DEC-85 (iii): real missingness for the betas
        beta = characteristics.beta_characteristic(est_r, symbols, market_symbol=C.MARKET_SYMBOL,
                                                   trail_win=C.BETA_WINDOW_WEEKS, min_weeks=C.BETA_WINDOW_WEEKS)
        resid = ic.fm_neutralize_outcome(r[lead:], beta[lead:], win.alive)
        for v in variants:
            char = characteristics.weekly_only_proxy_characteristic(v, r)[lead:]
            res = ic.weekly_ic_series(char, resid, win.alive, convention=C.CONVENTION)
            ics = np.array([w["ic"] for w in res["weekly"]], dtype=np.float64)
            fin = ics[np.isfinite(ics)]
            raw_means[v].append(float(fin.mean()) if fin.size else float("nan"))
            pool[v].append(fin)
            if floor_fm8 is not None:
                se_vals[v].append(est.se_rule(ics, floor_fm8, w_j, mean_block=mean_block, n_boot=n_boot,
                                              seed=boot_seed)["se"])
        if progress is not None:
            progress(rep)
    out_v: dict[str, Any] = {}
    for v in variants:
        s = float(C.SIGN[C.DIRECTION[v]])
        y = s * np.asarray(raw_means[v], dtype=np.float64)
        yf = y[np.isfinite(y)]
        pooled = np.concatenate(pool[v]) if pool[v] else np.empty(0)
        se_arr = np.asarray(se_vals[v], dtype=np.float64) if floor_fm8 is not None else np.empty(0)
        out_v[v] = {
            "se_mean": float(yf.std(ddof=1)) if yf.size > 1 else float("nan"),
            "e_se_rule": float(np.nanmean(se_arr)) if se_arr.size and np.isfinite(se_arr).any() else float("nan"),
            "sd_week": float(pooled.std(ddof=1)) if pooled.size > 1 else float("nan"),
            "null_mean": float(yf.mean()) if yf.size else float("nan"),
            "q95": float(np.quantile(yf, C.NULL_LEVEL)) if yf.size else float("nan"),
            "n_reps_finite": int(yf.size), "n_ic_pooled": int(pooled.size),
            "draws_sha256": est.series_sha256(y),
        }
    ceiling = est.signed_selection_ceiling({v: raw_means[v] for v in variants}, {v: C.SIGN[C.DIRECTION[v]] for v in variants})
    return {"variants": out_v, "ceiling_k4": ceiling, "rho_f": float(rho_f), "beta_sd": float(beta_sd),
            "drift_f": float(drift_f), "sigma_f": float(sigma_f), "sigma_e": float(sigma_e), "n_reps": int(n_reps),
            "seed": int(seed), "n_boot": int(n_boot), "mean_block": float(mean_block), "w_judged": int(w_j),
            "n_weeks": int(win.n_weeks), "lead_weeks": int(lead), "floor_fm8": floor_fm8}


def window_null_constants(
    win: Window, *, rho_f: float, beta_sd: float, sigma_f: float, sigma_e: float, n_reps: int, seed: int = C.SEED,
    floor_fm8: float | None, n_boot: int = C.N_BOOT_MIN, mean_block: float = C.MEAN_BLOCK, boot_seed: int = C.SEED,
    variants: tuple[str, ...] = C.VARIANTS, progress: Callable[[str, int], None] | None = None,
) -> dict[str, Any]:
    """Both cells (driftfree, drift 0.002) of a window and the frozen constants derived from them.  Pure function of the
    window arrays and the numbers passed in (the run re-computes with exactly this, P6)."""
    cells = {}
    for name, drift in DRIFTS.items():
        cells[name] = simulate_fm8_cell(
            win, rho_f=rho_f, beta_sd=beta_sd, drift_f=drift, sigma_f=sigma_f, sigma_e=sigma_e, n_reps=n_reps, seed=seed,
            floor_fm8=floor_fm8, n_boot=n_boot, mean_block=mean_block, boot_seed=boot_seed, variants=variants,
            progress=None if progress is None else (lambda i, nm=name: progress(nm, i)))
    free, drifting = cells["driftfree"]["variants"], cells["drifting"]["variants"]

    def worse(key: str, v: str) -> float:
        a, b = free[v][key], drifting[v][key]
        vals = [x for x in (a, b) if np.isfinite(x)]
        return float(max(vals)) if vals else float("nan")

    frozen: dict[str, Any] = {k: {v: worse(k, v) for v in variants} for k in ("se_mean", "e_se_rule", "sd_week", "null_mean", "q95")}
    frozen["q95_driftfree"] = {v: free[v]["q95"] for v in variants}
    frozen["q95_drifting"] = {v: drifting[v]["q95"] for v in variants}
    frozen["null_mean_driftfree"] = {v: free[v]["null_mean"] for v in variants}
    frozen["null_mean_drifting"] = {v: drifting[v]["null_mean"] for v in variants}
    frozen["ceiling_k4"] = cells["driftfree"]["ceiling_k4"]
    frozen["ceiling_k4_drifting_report_only"] = cells["drifting"]["ceiling_k4"]
    return {"cells": cells, "frozen": frozen}
