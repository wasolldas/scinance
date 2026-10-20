"""Calibration of the factor null PER WINDOW (DEC-86 / DEC-87 (D), ERSTFASSUNG 1.6) -- descriptive scalars of the real
window only: the market column's SD and lag-1 autocorrelation (``sigma_f``, ``rho_f``), the median cross-sectional R^2
of the return on the 26-week PIT beta (factor share), the idiosyncratic / total symbol vol; then the bisection-calibrated
``beta_sd`` for the three calibrations ``measured`` / ``stress`` (2 x rho_f, 2 x share) / ``zero`` with the loud
Gegenprobe of DEC-78/81/85.  THE SEAL's allowed category (single series and returns-vs-beta); no characteristic, no IC.

**Pilot period (Review B-8):** the calibration of P only delivers dispersion, autocorrelation and factor share for the
stress null that yields ``m_P``; the guard :func:`assert_no_mean_keys` refuses any key that would carry a mean of a real
series ("Waechter kein Mittel", DEC-94 (5) (i)).  The beta-dispersion block (whose mean is a beta, not a return) and the
analytic "mechanical momentum" line of the third version are NOT reproduced here.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..wp13_xsec import nulls, prelaunch
from . import constants as C
from .errors import SealError
from .weekly import Window

__all__ = ["CAL_NAMES", "calibrate_window", "assert_no_mean_keys", "survivorship_report", "FORBIDDEN_KEY_PARTS"]

CAL_NAMES: tuple[str, ...] = ("measured", "stress", "zero")
#: key fragments that would indicate a mean (or a drift) of a real series.
FORBIDDEN_KEY_PARTS: tuple[str, ...] = ("mean", "drift", "average", "avg")


def assert_no_mean_keys(obj: Any, path: str = "") -> None:
    """Guard 'kein Mittel' (DEC-94 (5) (i), Review B-8): no key of the pilot-period calibration block names a mean of a
    real series.  Raises :class:`SealError`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            ks = str(k).lower()
            if any(part in ks for part in FORBIDDEN_KEY_PARTS):
                raise SealError(f"pilot-period calibration carries a key that names a mean/drift of a real series: {path}/{k}")
            assert_no_mean_keys(v, f"{path}/{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_no_mean_keys(v, f"{path}[{i}]")


def _gp_summary(gp: dict[str, Any]) -> dict[str, Any]:
    keys = ("ok", "z", "z_max", "power_ok", "simulated_factor_share", "target_factor_share", "rel_diff", "se_diff",
            "market_sd_ok", "market_rho_ok", "n_reps")
    return {k: gp.get(k) for k in keys}


def calibrate_window(
    win: Window, beta_prev_26w: np.ndarray, *, names: tuple[str, ...] = CAL_NAMES, seed: int = C.SEED,
    search_n_reps: int = nulls.CALIBRATION_SEARCH_N_REPS_DEFAULT, search_rel_tol: float = nulls.CALIBRATION_SEARCH_REL_TOL_DEFAULT,
    search_max_iter: int = nulls.CALIBRATION_SEARCH_MAX_ITER_DEFAULT, gegenprobe_n_reps: int = nulls.GEGENPROBE_N_REPS_DEFAULT,
    gegenprobe_rel_tol: float = nulls.GEGENPROBE_REL_TOL, gegenprobe_z_max: float = nulls.GEGENPROBE_Z_MAX,
    gegenprobe_market_check: bool = True,
) -> dict[str, Any]:
    """Per-window calibration (see module docstring).  ``beta_prev_26w`` is the window slice of the 26-week PIT beta that
    strictly excludes the current week (``nulls.trailing_pit_beta_excluding_current_week``, built on the whole cut
    panel).  Loud fails: a search that does not converge and a failed Gegenprobe raise
    ``nulls.FactorShareCalibrationError`` (never caught here)."""
    est_r, alive, symbols = win.returns_est, win.alive, win.symbols
    n_weeks, n_sym = est_r.shape
    report = nulls.factor_calibration_report(est_r, alive, symbols, beta_prev_26w, market_symbol=C.MARKET_SYMBOL)
    rho_meas = report["market_factor"]["rho_f_measured"]
    share_meas = report["factor_share"]["factor_share_median"]
    sig = nulls.window_sigma_f_sigma_e(est_r, symbols, market_symbol=C.MARKET_SYMBOL)
    sigma_f, sigma_e_used = sig["sigma_f"], sig["sigma_e_used"]
    mask = alive & ~np.isnan(beta_prev_26w) & ~np.isnan(est_r)
    targets = {"measured": (rho_meas, share_meas), "stress": (nulls.STRESS_MULTIPLIER * rho_meas, nulls.STRESS_MULTIPLIER * share_meas),
               "zero": (0.0, share_meas)}
    check_market = gegenprobe_market_check and C.MARKET_SYMBOL in symbols
    cal: dict[str, Any] = {}
    for name in names:
        rho_cal, share_target = targets[name]
        search = nulls.calibrate_beta_sd_to_observed_share(
            share_target, rho_f=rho_cal, sigma_f=sigma_f, sigma_e=sigma_e_used, n_weeks=n_weeks, n_symbols=n_sym,
            symbols=symbols, market_symbol=C.MARKET_SYMBOL, seed=seed, n_reps=search_n_reps, rel_tol=search_rel_tol,
            max_iter=search_max_iter, mask=mask)
        if search["converged"] is False:
            raise nulls.FactorShareCalibrationError(
                f"calibration search '{name}' of window {win.name} did not converge (DEC-81): target share {share_target!r}, "
                f"rho_f={rho_cal!r}, n_iter={search['n_iter']}/{search_max_iter}")
        gp = nulls.factor_share_gegenprobe(
            n_weeks, n_sym, symbols, sigma_f=sigma_f, sigma_e=sigma_e_used, rho_f=rho_cal,
            beta_sd=search["beta_sd_calibrated"], target_share=share_target, market_symbol=C.MARKET_SYMBOL,
            n_reps=gegenprobe_n_reps, seed=seed + nulls.GEGENPROBE_SEED_OFFSET, rel_tol=gegenprobe_rel_tol,
            search_se=search["achieved_share_se"], mask=mask, z_max=gegenprobe_z_max,
            target_sigma_f=sigma_f if check_market else None, target_rho_f=rho_cal if check_market else None)
        cal[name] = {"rho_f": float(rho_cal), "beta_sd_calibrated": float(search["beta_sd_calibrated"]),
                     "target_factor_share": float(share_target), "converged": bool(search["converged"]),
                     "n_iter": int(search["n_iter"]), "achieved_share": float(search["achieved_share"]),
                     "gegenprobe": _gp_summary(gp)}
    return {
        "window": win.name, "n_weeks": int(n_weeks),
        "rho_f_measured": float(rho_meas), "sigma_f": float(sigma_f), "factor_share_median": float(share_meas),
        "n_weeks_share": int(report["factor_share"]["n_weeks_used"]),
        "sigma_e_used": float(sigma_e_used), "sigma_e_total": float(sig["sigma_e_total"]),
        "sigma_e_idiosyncratic": float(sig["sigma_e_idiosyncratic"]),
        "calibration": cal,
        "null_scales": {"sigma_f": float(sigma_f), "sigma_e_used": float(sigma_e_used)},
        "bounce_sigma_true": float(sig["sigma_e_total"]),
    }


def survivorship_report(win: Window, t_mom1: float, t_rev_gap: float, *, seed: int = C.SEED) -> dict[str, float]:
    """Report-only survivorship label (DEC-89 E3 (2)): the difference 'observation dropped' minus 'closed at the last
    price' on the signal-free drawdown fixture of the third version, in units of the frozen threshold ``T_W,v`` of the
    variant (the H-32 analogue of ``IC_min``; the difference itself is in ``*_diff``)."""
    res = prelaunch.survivorship_drawdown_fixture(
        {"alive": win.alive, "returns_est": win.returns_est}, ic_min_mom1=t_mom1, ic_min_rev_gap=t_rev_gap, seed=seed)
    out = {k: float(res[k]) for k in ("mom1_diff", "rev_gap_diff", "mom1_diff_in_ic_min_units", "rev_gap_diff_in_ic_min_units")}
    if not all(math.isfinite(v) for v in out.values()):
        raise ValueError("survivorship fixture returned a non-finite number")
    return out
