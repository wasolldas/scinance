"""WP-13a -- ``--prelaunch`` report assembly (DEC-74 Entscheidung 2 (a),
(b)/(c), (g), (h), the delisting-week symbol-week count of (i),
STRESS_REL/STRESS_ABS coverage, and the DEC-74 (j) fixtures live in
``tests/unit/test_wp13_xsec.py``, not here).

**THE SEAL, restated for this module specifically.** Every function below
that touches the REAL union panel works EITHER on ``alive`` alone (no
outcome: delisting counts, K series, STRESS coverage) OR on a
characteristic paired against a SIMULATED/permuted outcome
(``nulls.persistence_null``, ``measured_selection_ceiling``) OR is a
outcome-free cross-sectional comparison of two CHARACTERISTICS
(``gate5_reachability``: vol-rank vs turnover-rank, no return anywhere).
Nothing in this module ever calls ``ic.weekly_ic_series`` with the real
union panel's ``returns`` array. ``scripts/wp13_xsec.py``'s SEAL test
wraps ``ic.weekly_ic_series`` for the whole ``--prelaunch`` run and
asserts this.

**Windows (PRD 5.3, DEC-74).** ``W1``/``W2`` are the two judgement-bearing
1-year windows; ``L`` is DESCRIPTIVE ONLY (never a threshold), used for
H-30's feasibility line (DEC-74 (h)) and the L-window's own K
series/reachability, kept in a SEPARATE artifact file (DEC-74 (k):
"L-Fenster in getrennter, versiegelter Datei").
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np

from ..wp7_universe import panel_load, pit_universe, stats
from . import characteristics, ic, nulls

__all__ = [
    "WINDOWS", "slice_window", "window_noise_floor_and_threshold",
    "gate5_reachability", "h30_feasibility", "delisting_counts",
    "no_history_symbols_report", "stress_coverage",
    "analytic_bailey_ldp_ceiling", "analytic_selection_ceiling",
    "measured_selection_ceiling", "assemble_prelaunch_report",
    "write_prelaunch_artifacts", "factor_preserving_report",
    "survivorship_drawdown_fixture", "beta_control_pass_table",
    "beta_control_recommendation",
]

#: PRD 5.3 / DEC-74: judgement-bearing windows W1/W2, descriptive-only L.
WINDOWS: dict[str, tuple[str, str]] = {
    "W1": ("2024-07-01", "2025-06-30"),
    "W2": ("2025-07-01", "2026-06-30"),
    "L": ("2021-03-01", "2024-06-30"),
}

#: DEC-73 Entscheidung 1 / PRD 5.3: the K=7 F-XSEC1 cohort, fixed order.
SELECTION_K = 7

#: PRD 5.3's own literal selection-ceiling scale factor (verbatim example:
#: "0,7071*(0,4228*1,0676 + 0,5772*1,6207) = 0,98"). Interpretation used
#: here (not re-derived from the PRD's terse "T = 2 a" note, which is not
#: spelled out further in the cited text): the K=7 trials are jointly
#: judged across the TWO independent 1-year windows W1/W2 (PRD 5.3's
#: "in beiden urteilstragenden Fenstern" Gate-text point (1)), so the
#: order-statistic scale (computed on a single-window z-unit) is divided
#: by ``sqrt(2)`` when converting to the two-window judgement's IC unit.
#: This factor is PRESERVED VERBATIM from the registered PRD text, not
#: re-derived by this module -- it is flagged here as an interpretation
#: for orchestrator confirmation alongside the reversal Gap-Design
#: deviation (``characteristics.py`` module docstring).
HALF_SQRT2_FACTOR = 1.0 / math.sqrt(2.0)


# ----------------------------------------------------------------------------
# window slicing
# ----------------------------------------------------------------------------

def slice_window(weeks: list[str], start_iso: str, end_iso: str,
                  *arrays: np.ndarray) -> dict[str, Any]:
    """Restrict ``weeks`` (and every ``[n_weeks, ...]`` array in
    ``arrays``, same row order) to the CLOSED range
    ``[start_iso, end_iso]`` (ISO week-start string comparison -- every
    entry in ``weeks`` is already a Monday-aligned ISO week start, so
    plain string comparison is exact and needs no date parsing).
    Raises :class:`ValueError` if the window has no overlap with
    ``weeks`` at all (a loud failure, never a silently empty window)."""
    idx = [i for i, w in enumerate(weeks) if start_iso <= w <= end_iso]
    if not idx:
        raise ValueError(f"window [{start_iso}, {end_iso}] has no overlap with the loaded "
                          f"panel's week grid ({weeks[0]}..{weeks[-1]})")
    lo, hi = idx[0], idx[-1] + 1
    out: dict[str, Any] = {"weeks": weeks[lo:hi], "lo": lo, "hi": hi,
                            "start_iso": start_iso, "end_iso": end_iso}
    names = ("returns", "alive", "vol_rv", "turnover_trail", "day_count", "beta_prev_26w")
    for name, arr in zip(names[:len(arrays)], arrays):
        out[name] = arr[lo:hi]
    return out


# ----------------------------------------------------------------------------
# (a)/(b)/(c)/(d): floor + persistence null + thresholds
# ----------------------------------------------------------------------------

def window_noise_floor_and_threshold(
    window: dict[str, Any], *, variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    convention: ic.Convention = "close_at_last", n_sims: int = nulls.PERSISTENCE_NULL_N_SIMS_DEFAULT,
    seed: int = nulls.PERSISTENCE_NULL_SEED,
) -> dict[str, Any]:
    """DEC-74 (a)+(b)/(c)+(d) for ONE window: the analytic floor, the
    persistence null per variant, and ``IC_min`` per variant. Never reads
    ``window['returns']`` as an outcome for a real characteristic -- the
    persistence null (``nulls.persistence_null``) only ever feeds it
    SIMULATED returns, and the floor only ever reads ``window['alive']``.
    """
    floor = nulls.analytic_permutation_floor(window["alive"], window["weeks"])
    w_judged = floor["w_judged"]
    pnull = nulls.persistence_null(window["returns"], window["alive"], window["weeks"],
                                    variants=variants, convention=convention,
                                    n_sims=n_sims, seed=seed)
    # DEC-75 (1)/(2)/(8): IC_min uses W_judged (not the raw week count) and the
    # BIAS-CORRECTED c_rho; both the capped (registered, "ic_min_capped") and the
    # uncapped ("ic_min_raw") value are reported side by side (task brief item 2).
    thresholds_capped = {
        v: nulls.ic_threshold(floor["e_floor"], pnull["variants"][v]["c_rho_corrected"], w_judged, cap_c_rho=True)
        for v in variants
    }
    thresholds_raw = {
        v: nulls.ic_threshold(floor["e_floor"], pnull["variants"][v]["c_rho_corrected"], w_judged, cap_c_rho=False)
        for v in variants
    }
    return {
        "floor": floor, "persistence_null": pnull, "w_judged": w_judged,
        "ic_min_per_variant": thresholds_capped,           # backward-compat name = registered (capped)
        "ic_min_capped_per_variant": thresholds_capped,
        "ic_min_raw_per_variant": thresholds_raw,
    }


# ----------------------------------------------------------------------------
# (g) Gate (5) reachability -- vol-rank vs turnover-rank, NO outcome
# ----------------------------------------------------------------------------

def gate5_reachability(window: dict[str, Any], *, min_universe: int = 10) -> dict[str, Any]:
    """DEC-74 (g): per week, Spearman(vol_rv-rank, trailing-turnover-rank)
    among that week's alive symbols -- NEVER involves an outcome/return,
    only two CHARACTERISTICS, so it is safe to compute on the real panel
    in ``--prelaunch``. A structural violation (median >= 0.60) is a
    GL-012 event BEFORE any run (DEC-74 (g)), never a gate adjustment."""
    weeks, alive = window["weeks"], window["alive"]
    vol_rv, turnover_trail = window["vol_rv"], window["turnover_trail"]
    weekly: list[dict[str, Any]] = []
    for t in range(len(weeks)):
        mask = alive[t]
        v, tn = vol_rv[t, mask], turnover_trail[t, mask]
        valid = ~np.isnan(v) & ~np.isnan(tn)
        k = int(valid.sum())
        if k < min_universe:
            weekly.append({"week": weeks[t], "spearman": None, "k": k})
            continue
        rho = pit_universe.spearman_rank_ic(v[valid], tn[valid])
        weekly.append({"week": weeks[t], "spearman": rho, "k": k})
    vals = np.array([w["spearman"] for w in weekly if w["spearman"] is not None], dtype=np.float64)
    if vals.size:
        median, q25, q75 = (float(np.quantile(vals, p)) for p in (0.5, 0.25, 0.75))
    else:
        median = q25 = q75 = None
    return {"weekly": weekly, "median": median, "q25": q25, "q75": q75,
            "n_weeks_used": int(vals.size),
            "gate5_reachable": (median is not None and median < 0.60),
            "threshold": 0.60, "label": "Spearman(vol_rv-Rang, Turnover-Rang), kein Outcome (DEC-74 (g))"}


# ----------------------------------------------------------------------------
# (h) H-30 feasibility on L
# ----------------------------------------------------------------------------

def h30_feasibility(window_l: dict[str, Any], *, ic_prior: float = stats.IC_PRIOR,
                     f: float = stats.DECILE_FACTOR) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (4) / task brief item 4, v2: ``Kante = 3.51 *
    IC_prior * sigma_xs(L)`` (bp/week, unchanged); feasibility is now TWO
    ratios against ``Kante``, both required ``<= 0.5``:

      (i)  ``spread_D10_minus_D1 / Kante`` -- the RAW (pre-weighting)
           decile drag spread (``sigma_w^2/2`` in bp, per vol decile,
           highest-vol decile minus lowest-vol decile).
      (ii) ``SE(sigma_w^2/2) / Kante`` -- the ESTIMATION-ERROR ratio
           (Review B-5: "Schaetzfehler ~60% auf sigma_w^2/2
           unquantifiziert" -- this closes that gap). ``SE`` is derived
           from ``n``, the median number of daily returns feeding a
           week's realised-vol estimate (``characteristics.
           weekly_valid_day_count``): the relative SE of a sample
           variance from ``n`` i.i.d. observations is ``1/sqrt(2*(n-1))``
           (standard chi-squared-based large-sample approximation,
           Var(s^2)/E[s^2]^2 ~= 2/(n-1)); applied to the OVERALL median
           raw drag (pooled over every symbol-week in ``L``, not just one
           decile -- the task brief: "applied to the median drag").

    Both ratios are reported with the ``0.5`` bound; ``feasible`` is
    ``True`` iff BOTH are ``<= 0.5`` (task brief item 4, verbatim).
    """
    sigma_xs = stats.sigma_xs_summary(window_l["returns"], window_l["alive"])
    sigma_xs_median = sigma_xs["median"] or 0.0
    kante_bps = f * ic_prior * sigma_xs_median * 10_000.0

    vol_rv, alive, weeks = window_l["vol_rv"], window_l["alive"], window_l["weeks"]
    target_vol = float(np.median(vol_rv[~np.isnan(vol_rv)])) if np.isfinite(vol_rv).any() else float("nan")

    by_decile: dict[int, list[float]] = {d: [] for d in range(1, 11)}
    all_drag_raw_bps: list[float] = []
    for t in range(len(weeks)):
        mask = alive[t]
        buckets = characteristics.decile_bucket(vol_rv[t], mask)
        drag_raw_t = 0.5 * vol_rv[t] ** 2 * 10_000.0
        for d in range(1, 11):
            vals = drag_raw_t[(buckets == d) & ~np.isnan(drag_raw_t)]
            by_decile[d].extend(float(v) for v in vals)
            all_drag_raw_bps.extend(float(v) for v in vals)
    decile_table = [
        {"decile": d, "median_drag_raw_bps": (float(np.median(v)) if v else None), "n_symbol_weeks": len(v)}
        for d, v in by_decile.items()
    ]
    d1_med = decile_table[0]["median_drag_raw_bps"]
    d10_med = decile_table[9]["median_drag_raw_bps"]
    spread_d10_d1_bps = (d10_med - d1_med) if (d1_med is not None and d10_med is not None) else None

    day_count = window_l.get("day_count")
    if day_count is not None:
        n_valid = day_count[alive & (day_count > 0)]
        n_median = float(np.median(n_valid)) if n_valid.size else float("nan")
    else:
        n_median = float("nan")
    overall_median_drag_bps = float(np.median(all_drag_raw_bps)) if all_drag_raw_bps else float("nan")
    relative_se = (1.0 / math.sqrt(2.0 * (n_median - 1.0))) if (n_median and n_median > 1.0) else float("nan")
    se_drag_bps = (relative_se * overall_median_drag_bps
                   if (not math.isnan(relative_se) and not math.isnan(overall_median_drag_bps)) else float("nan"))

    ratio_spread = (spread_d10_d1_bps / kante_bps) if (kante_bps and spread_d10_d1_bps is not None) else float("nan")
    ratio_se = (se_drag_bps / kante_bps) if (kante_bps and not math.isnan(se_drag_bps)) else float("nan")
    feasible = (not math.isnan(ratio_spread) and not math.isnan(ratio_se)
                and ratio_spread <= 0.5 and ratio_se <= 0.5)

    return {
        "sigma_xs_l": sigma_xs, "ic_prior": ic_prior, "decile_factor": f,
        "kante_bps_per_week": kante_bps, "target_vol": target_vol,
        "decile_drag_table_raw_bps": decile_table,
        "spread_d10_minus_d1_bps": spread_d10_d1_bps,
        "spread_d10_minus_d1_over_kante": ratio_spread,
        "n_days_median": n_median, "overall_median_drag_raw_bps": overall_median_drag_bps,
        "relative_se_drag": relative_se, "se_drag_bps": se_drag_bps,
        "se_drag_over_kante": ratio_se,
        "feasible": feasible,
        "note": "DEC-75 (4) v2: feasibel <=> spread_D10_minus_D1/Kante <= 0.5 UND "
                "SE(sigma_w^2/2)/Kante <= 0.5, beide auf L. SE(sigma_w^2/2) aus "
                "relative_se = 1/sqrt(2*(n_median-1)) (n = Median-Zahl Tagesrenditen je Woche), "
                "angewandt auf den ueber alle Symbol-Wochen gepoolten Median-Drag. "
                "Vorbehalt 'schaetzfehlerdominiert', falls se_drag_over_kante > 0.5.",
    }


# ----------------------------------------------------------------------------
# (i) delisting-week symbol-week counts + NO_HISTORY symbols
# ----------------------------------------------------------------------------

def delisting_counts(window: dict[str, Any]) -> dict[str, Any]:
    """DEC-74 (i): symbol-weeks with ``alive[t] & ~alive[t+1]`` (a symbol
    IS alive week ``t`` but NOT week ``t+1`` -- its delisting week) within
    the window -- the count both survivorship conventions in (i) need
    ("zum letzten Schlusskurs geschlossen" affects exactly these
    symbol-weeks; "Beobachtung verworfen" drops them)."""
    alive, weeks = window["alive"], window["weeks"]
    n_weeks = alive.shape[0]
    total = 0
    per_week = []
    for t in range(n_weeks - 1):
        n = int((alive[t] & ~alive[t + 1]).sum())
        total += n
        per_week.append({"week": weeks[t], "n_delisting": n})
    return {"n_symbol_weeks_delisting": total, "per_week": per_week, "n_weeks": n_weeks}


def no_history_symbols_report(delisted_manifest_path: Path | str,
                               delisting_dates_path: Path | str) -> dict[str, Any]:
    """DEC-74 (i): the NO_HISTORY-only symbols (``delisted_symbols_with_
    history``'s second return value) and their register delisting week --
    ``delisting_dates.json`` DOES carry an entry for them
    (``delisted_panel.fetch_delisted_panel`` writes the entry BEFORE the
    kline-empty check), so this needs no fallback."""
    _usable, no_history_only = panel_load.delisted_symbols_with_history(delisted_manifest_path)
    dd = panel_load.load_delisting_dates(delisting_dates_path)
    rows = []
    for s in sorted(no_history_only):
        d = dd.get(s)
        rows.append({
            "symbol": s, "delist_date": d.isoformat() if d else None,
            "delist_week": pit_universe.iso_week_start(d).isoformat() if d else None,
        })
    return {"n_no_history": len(no_history_only), "symbols": rows}


# ----------------------------------------------------------------------------
# STRESS_REL / STRESS_ABS coverage
# ----------------------------------------------------------------------------

def stress_coverage(stress_path: Path | str, start_iso: str, end_iso: str) -> dict[str, Any]:
    """Day count of a STRESS_REL/STRESS_ABS fixture (DEC-55/56) falling
    inside ``[start_iso, end_iso]``; ``{"available": False}`` (never a
    computed value) if the fixture file does not exist -- "nicht
    vorhanden", per the task brief, not a silent zero."""
    path = Path(stress_path)
    if not path.is_file():
        return {"available": False, "note": f"{path} nicht vorhanden"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    days = payload if isinstance(payload, list) else payload.get("days", [])
    in_window = [d for d in days if start_iso <= d <= end_iso]
    return {"available": True, "n_days_total": len(days), "n_days_in_window": len(in_window),
            "days_in_window": sorted(in_window)}


# ----------------------------------------------------------------------------
# selection ceiling (K=7)
# ----------------------------------------------------------------------------

def analytic_bailey_ldp_ceiling(k: int) -> float:
    """``E[max of k iid N(0,1)] ~= (1-gamma)*Phi^-1(1-1/k) +
    gamma*Phi^-1(1-1/(k*e))`` (Bailey & Lopez de Prado 2014, the exact
    closed-form PRD 5.3 cites: for k=7 this reproduces "1,0676"/"1,6207"
    to 4 d.p.). Uses ``statistics.NormalDist`` (stdlib, no scipy
    dependency -- repo convention)."""
    gamma = 0.5772156649015329
    nd = NormalDist()
    z1 = nd.inv_cdf(1.0 - 1.0 / k)
    z2 = nd.inv_cdf(1.0 - 1.0 / (k * math.e))
    return (1.0 - gamma) * z1 + gamma * z2


def analytic_selection_ceiling(e_floor: float, w: int, *, k: int = SELECTION_K) -> dict[str, Any]:
    """PRD 5.3's analytic K=7 selection ceiling IN IC UNITS: the Bailey/
    LdP expected-max-of-k z-score, scaled by ``HALF_SQRT2_FACTOR`` (PRD
    5.3's own literal factor, see module-level docstring), converted to
    IC units by the window's own per-mean-IC standard error
    (``e_floor/sqrt(w)`` -- the same ``z * SD_null/sqrt(W)`` construction
    ``stats.detectable_effect`` already uses)."""
    z_max = analytic_bailey_ldp_ceiling(k)
    z_scaled = HALF_SQRT2_FACTOR * z_max
    se_mean_ic = e_floor / math.sqrt(w)
    return {"k": k, "z_max_bailey_ldp": z_max, "half_sqrt2_scaled_z_max": z_scaled,
            "se_mean_ic": se_mean_ic, "ceiling_ic": z_scaled * se_mean_ic}


def _pure_noise_window_mean_ic(alive_window: np.ndarray, rng: np.random.Generator, *,
                                min_universe: int = 10) -> float:
    """One draw of a K=7-selection-ceiling candidate's window mean IC
    under PURE noise: for every week, an INDEPENDENT random permutation
    is used for BOTH the 'characteristic' and the 'outcome' (never the
    real returns -- this only uses ``alive_window`` for its K_t
    structure, matching the task brief's "measured ceiling ... with the
    window's K series and W"). DEC-75 (1): loops over the JUDGED weeks
    (``n_weeks - 1``), same range as ``ic.weekly_ic_series``."""
    n_weeks = alive_window.shape[0]
    w_judged = nulls.w_judged_of(n_weeks)
    ics: list[float] = []
    for t in range(w_judged):
        mask = alive_window[t]
        k = int(mask.sum())
        if k < min_universe:
            continue
        sig = rng.permutation(k).astype(np.float64)
        out = rng.permutation(k).astype(np.float64)
        ics.append(pit_universe.spearman_rank_ic(sig, out))
    return float(np.mean(ics)) if ics else float("nan")


def measured_selection_ceiling(alive_window: np.ndarray, *, k: int = SELECTION_K,
                                n_replicates: int = 300, seed: int = 53) -> dict[str, Any]:
    """The MEASURED complement to :func:`analytic_selection_ceiling`
    (PRD 5.3: "Verbindlich ist die am Null-Fixture gemessene Decke"): for
    ``n_replicates`` outer trials, draw ``k`` INDEPENDENT pure-noise
    window-mean-IC candidates (``_pure_noise_window_mean_ic``, same
    ``alive_window``/``W``) and take their max; report the mean of that
    max across trials -- a direct Monte-Carlo estimate of ``E[max_k IC]``
    under pure noise, already in IC units (no z-unit conversion needed).
    """
    rng = np.random.default_rng(seed)
    maxes: list[float] = []
    for _ in range(n_replicates):
        draws = [_pure_noise_window_mean_ic(alive_window, rng) for _ in range(k)]
        draws = [d for d in draws if not math.isnan(d)]
        if draws:
            maxes.append(max(draws))
    return {"k": k, "n_replicates": len(maxes), "seed": seed,
            "ceiling_ic_mean": (float(np.mean(maxes)) if maxes else float("nan")),
            "ceiling_ic_sd": (float(np.std(maxes, ddof=1)) if len(maxes) > 1 else float("nan"))}


# ----------------------------------------------------------------------------
# DEC-77 Entscheidung 1 (b)/(c) -- Vorlauf v4: the beta-control method
# decision rule (pre-fixed, applied by code) + the cross-window
# recommendation.
# ----------------------------------------------------------------------------

def beta_control_pass_table(
    study: dict[str, Any], *, floor: float, w_judged: int, pure_noise_ceiling: float,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    null_mean_tol_factor: float = 0.25, ceiling_tol_factor: float = 1.5,
) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (b)/(c), the PRE-FIXED decision rule, applied
    by CODE (never eyeballed): a method PASSES iff, for BOTH the
    ``"measured"`` AND ``"stress"`` calibrations, over ALL ``variants``:
    (a) the WORST (max over variants of ``|mean-of-mean-IC|``) null mean
    is ``<= 0.25 * floor / sqrt(W_judged)``, AND (b) the ceiling
    (mean-of-max over variants) is ``<= 1.5 * pure_noise_ceiling`` (the
    window's EXISTING measured pure-noise selection ceiling,
    :func:`measured_selection_ceiling`'s ``ceiling_ic_mean``). One row per
    method (:data:`ic.BETA_CONTROL_METHODS`, in ``study``'s own order);
    ``note`` is the EXACT required string (task brief, verbatim) if NO
    method passes -- a fact, never a verdict (DEC-77 Entscheidung 1 (c):
    "erfuellt keine, ist Klasse W auf diesem Panel nicht testbar (B1-analog,
    GL-012) -- dann keine Registrierung, kein Zurueckskalieren")."""
    null_mean_bound = (null_mean_tol_factor * floor / math.sqrt(w_judged)) if w_judged > 0 else float("nan")
    ceiling_bound = (ceiling_tol_factor * pure_noise_ceiling
                      if pure_noise_ceiling is not None and not math.isnan(pure_noise_ceiling) else float("nan"))
    rows: list[dict[str, Any]] = []
    passing: list[str] = []
    for method in study["methods"]:
        per_cal: dict[str, Any] = {}
        ok_all = True
        for cal in ("measured", "stress"):
            m = study["calibrations"][cal]["methods"][method]
            null_means = [m["variants"][v]["mean_ic_draws_mean"] for v in variants]
            finite_abs = [abs(x) for x in null_means if x is not None and not math.isnan(x)]
            worst = max(finite_abs) if finite_abs else float("nan")
            ceiling = m["ceiling_mean_of_max"]
            mean_ok = (not math.isnan(worst)) and (not math.isnan(null_mean_bound)) and worst <= null_mean_bound
            ceiling_ok = (ceiling is not None and not math.isnan(ceiling)
                          and not math.isnan(ceiling_bound) and ceiling <= ceiling_bound)
            per_cal[cal] = {
                "worst_abs_null_mean": worst, "null_mean_bound": null_mean_bound, "null_mean_ok": mean_ok,
                "ceiling": ceiling, "ceiling_bound": ceiling_bound, "ceiling_ok": ceiling_ok,
            }
            ok_all = ok_all and mean_ok and ceiling_ok
        rows.append({"method": method, "measured": per_cal["measured"], "stress": per_cal["stress"], "pass": ok_all})
        if ok_all:
            passing.append(method)
    return {
        "rows": rows, "passing_methods": passing, "null_mean_bound": null_mean_bound,
        "ceiling_bound": ceiling_bound,
        "note": None if passing else "KEINE METHODE ERFUELLT DIE KRITERIEN (GL-012-Kandidat)",
    }


def beta_control_recommendation(
    windows_out: dict[str, Any], *, window_names: tuple[str, ...] = ("W1", "W2"),
) -> dict[str, Any]:
    """DEC-77 Entscheidung 1 (c): among the methods that PASS
    :func:`beta_control_pass_table` in EVERY judged window with a
    decision table, the recommendation is the one with the SMALLEST
    residualised SD (``mean_ic_draws_sd`` under the ``"measured"``
    calibration, averaged over ``variants``, then averaged over windows)
    -- tie -> the SHORTER beta window (:func:`ic.beta_control_trail_weeks`;
    ``"none"`` has no window, sorts as 0, so it would win a tie against
    any beta-controlled method -- documented, never expected to matter in
    practice since ``"none"`` is the uncontrolled reference DEC-77 exists
    to move past). A number, never a hand-picked choice: no real-data
    signal enters this function, only the already-computed calibration/
    decision numbers (THE SEAL holds transitively). If no method passes
    in EVERY window, the recommendation is ``None`` -- each window's own
    ``beta_control_decision.note`` already carries the GL-012-candidate
    string, no verdict is added here either."""
    decisions = {wn: windows_out[wn]["beta_control_decision"] for wn in window_names
                 if windows_out.get(wn, {}).get("available") and "beta_control_decision" in windows_out[wn]}
    if not decisions:
        return {"recommended_method": None, "beta_window_weeks": None, "eligible_methods": [],
                "note": "keine Fenster mit Beta-Kontroll-Entscheidung verfuegbar"}
    passing_sets = [set(d["passing_methods"]) for d in decisions.values()]
    eligible = set.intersection(*passing_sets) if passing_sets else set()
    if not eligible:
        return {"recommended_method": None, "beta_window_weeks": None, "eligible_methods": [],
                "note": "KEINE METHODE ERFUELLT DIE KRITERIEN IN JEDEM FENSTER (GL-012-Kandidat)"}

    def _avg_sd(method: str) -> float:
        window_sds: list[float] = []
        for wn in decisions:
            m = windows_out[wn]["beta_control_method_study"]["calibrations"]["measured"]["methods"][method]
            variant_sds = [v["mean_ic_draws_sd"] for v in m["variants"].values()
                           if v["mean_ic_draws_sd"] is not None and not math.isnan(v["mean_ic_draws_sd"])]
            if variant_sds:
                window_sds.append(float(np.mean(variant_sds)))
        return float(np.mean(window_sds)) if window_sds else float("inf")

    ranked = sorted(eligible, key=lambda m: (_avg_sd(m), ic.beta_control_trail_weeks(m) or 0))
    best = ranked[0]
    return {
        "recommended_method": best, "beta_window_weeks": ic.beta_control_trail_weeks(best),
        "eligible_methods": sorted(eligible), "avg_residualized_sd": _avg_sd(best),
        "note": f"Empfehlung: {best} (kleinste residualisierte SD ueber Fenster gemittelt, "
                "Tie -> kuerzeres Beta-Fenster).",
    }


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (2)/(3): factor-preserving null report wrapper
# ----------------------------------------------------------------------------

def factor_preserving_report(
    window: dict[str, Any], symbols: list[str], *,
    variants: tuple[str, ...] = characteristics.VARIANT_NAMES,
    convention: ic.Convention = "close_at_last",
    n_reps: int = nulls.FACTOR_NULL_N_REPS_DEFAULT, seed: int = nulls.FACTOR_NULL_SEED,
) -> dict[str, Any]:
    """DEC-76 Entscheidung 2 (Vorlauf v3, additive): TWO calls to
    :func:`nulls.factor_preserving_null` on this window's ``returns``/
    ``alive`` (used ONLY for K/W sizing and the two descriptive vol scalars
    -- THE SEAL, see that function's docstring) -- ``"drifting"``
    (``drift_f=0.002``, DEC-75's original configuration) and
    ``"driftfree"`` (``drift_f=0.0``), ``rho_f=0.2`` in BOTH. Each carries
    its own raw AND residualized statistics (module docstring of
    ``nulls.factor_preserving_null``).

    **Binding vs. report-only (DEC-76 Entscheidung 1 (b)/(c), verbatim):**
    the GL-012 kill binds ONLY to
    ``driftfree["selection_ceiling_mean_of_max_residualized"]`` and the
    beta-control PASS quantile binds ONLY to
    ``drifting["variants"][v]["quantile_one_sided_residualized"]`` -- every
    other number here (drifting raw mean -- "Beta-Prognostizierbarkeit",
    driftfree raw ceiling, drifting residualized ceiling, driftfree
    residualized quantile) is REPORT-ONLY, labelled as such below.
    """
    drifting = nulls.factor_preserving_null(
        window["returns"], window["alive"], symbols, variants=variants,
        convention=convention, n_reps=n_reps, seed=seed, drift_f=nulls.DRIFT_F_DRIFTING)
    driftfree = nulls.factor_preserving_null(
        window["returns"], window["alive"], symbols, variants=variants,
        convention=convention, n_reps=n_reps, seed=seed, drift_f=nulls.DRIFT_F_DRIFTFREE)
    return {
        "drifting": drifting, "driftfree": driftfree,
        "binding": {
            "gl012_ceiling": "driftfree.selection_ceiling_mean_of_max_residualized",
            "beta_control_quantile_per_variant": "drifting.variants.<v>.quantile_one_sided_residualized",
        },
        "report_only": [
            "drifting.variants.<v>.mean_ic_draws_mean (Beta-Prognostizierbarkeit)",
            "drifting.selection_ceiling_mean_of_max", "drifting.selection_ceiling_mean_of_max_residualized",
            "driftfree.selection_ceiling_mean_of_max",
            "driftfree.variants.<v>.quantile_one_sided_residualized",
        ],
        "label": "DEC-76 Entscheidung 2 (Vorlauf v3): drifting (drift_f=0.002) + driftfree "
                 "(drift_f=0.0) Konfigurationen, rho_f=0.2 in beiden.",
    }


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (5) / task brief item 5: survivorship drawdown fixture
# ----------------------------------------------------------------------------

def survivorship_drawdown_fixture(
    window: dict[str, Any], *, ic_min_mom1: float, ic_min_rev_gap: float,
    seed: int = 53, drawdown_trigger: float = -0.40, drawdown_window: int = 8,
    delete_frac: float = 0.30, sigma: float = 0.05,
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (5) / PRD 4.1's Survivorship-Fixture, now also
    a PRELAUNCH REPORT LINE (task brief item 5), not just a T1 test. A
    SIGNAL-FREE synthetic panel, sized like ``window`` (``K`` = the
    window's MEDIAN weekly ``alive`` count, ``W`` = the window's week
    count), i.i.d. ``N(0, sigma)`` weekly returns -- no true
    predictability anywhere, so any apparent momentum/reversal premium the
    UNCONTROLLED estimator finds is PURELY the survivorship-bias artifact
    this fixture exists to catch.

    Delisting: for each symbol, the trailing ``drawdown_window``-week
    cumulative return (``characteristics.momentum_characteristic``,
    reused) is checked against ``drawdown_trigger``; among symbols that
    ever cross it, the ``round(delete_frac * K)`` EARLIEST-triggering
    symbols are delisted the week immediately after their trigger week
    (PRD 4.1's "nach einem simulierten Drawdown-Trigger"). If fewer than
    ``round(delete_frac*K)`` symbols ever trigger, every triggering symbol
    is delisted (documented, not silently padded).

    Two estimators on the SAME simulated returns:
      - **UNCONTROLLED** ("Beobachtung verworfen"): the delisted symbols'
        columns are dropped from the ENTIRE panel (as if they never
        existed), ``convention="drop"`` on the remaining survivors-only
        columns.
      - **CONTROLLED** ("zum letzten Schlusskurs geschlossen", PRD 4.1 DoD
        (4)): the real PIT alive mask (``pit_universe.pit_alive_mask``,
        ``min_weeks_history=0`` -- this fixture is about delisting bias,
        not the separate listing-pump cutoff), ``convention="close_at_last"``.

    Reports ``mom1``/``rev_gap`` IC under both, their DIFFERENCE
    (uncontrolled - controlled), and that difference in UNITS OF IC_min
    (task brief: "the prelaunch line reports the difference in units of
    IC_min (must be a number, no verdict)" -- no PASS/FAIL/methodisch-
    invalide label is attached here; PRD 4.1's own adversarial T1 test
    (``tests/unit/test_wp13_xsec.py``) is where the verdict-bearing
    assertion lives).
    """
    n_weeks = window["returns"].shape[0]
    k_median = int(np.median(window["alive"].sum(axis=1))) if window["alive"].size else 0
    k_median = max(k_median, 10)
    rng = np.random.default_rng(seed)
    returns_sim = rng.normal(0.0, sigma, size=(n_weeks, k_median))

    cum_trail = characteristics.momentum_characteristic(returns_sim, trail_win=drawdown_window)
    triggered: list[tuple[int, int]] = []
    for j in range(k_median):
        idx = np.flatnonzero(cum_trail[:, j] < drawdown_trigger)
        if idx.size:
            triggered.append((j, int(idx[0])))
    triggered.sort(key=lambda p: p[1])
    n_target = int(round(delete_frac * k_median))
    chosen = triggered[:n_target]

    last_bar = np.full(k_median, n_weeks - 1, dtype=np.int64)
    survivor_cols = np.ones(k_median, dtype=bool)
    for j, t_trigger in chosen:
        last_bar[j] = min(t_trigger + 1, n_weeks - 1)
        survivor_cols[j] = False

    alive_controlled = pit_universe.pit_alive_mask(
        np.zeros(k_median, dtype=np.int64), last_bar, n_weeks, min_weeks_history=0)
    alive_uncontrolled = np.ones((n_weeks, k_median), dtype=bool) & survivor_cols[None, :]

    mom1_sim = characteristics.momentum_characteristic(returns_sim, trail_win=1)
    rev_sim = characteristics.reversal_gap_characteristic(returns_sim)

    mom1_controlled = ic.weekly_ic_series(mom1_sim, returns_sim, alive_controlled, convention="close_at_last")["mean_ic"]
    rev_controlled = ic.weekly_ic_series(rev_sim, returns_sim, alive_controlled, convention="close_at_last")["mean_ic"]
    mom1_uncontrolled = ic.weekly_ic_series(mom1_sim, returns_sim, alive_uncontrolled, convention="drop")["mean_ic"]
    rev_uncontrolled = ic.weekly_ic_series(rev_sim, returns_sim, alive_uncontrolled, convention="drop")["mean_ic"]

    diff_mom1 = mom1_uncontrolled - mom1_controlled
    diff_rev = rev_uncontrolled - rev_controlled
    return {
        "k": k_median, "n_weeks": n_weeks, "seed": seed,
        "drawdown_trigger": drawdown_trigger, "drawdown_window": drawdown_window,
        "delete_frac": delete_frac, "n_triggered": len(triggered), "n_deleted": len(chosen),
        "mom1_uncontrolled": mom1_uncontrolled, "mom1_controlled": mom1_controlled,
        "mom1_diff": diff_mom1,
        "mom1_diff_in_ic_min_units": (diff_mom1 / ic_min_mom1) if ic_min_mom1 else float("nan"),
        "rev_gap_uncontrolled": rev_uncontrolled, "rev_gap_controlled": rev_controlled,
        "rev_gap_diff": diff_rev,
        "rev_gap_diff_in_ic_min_units": (diff_rev / ic_min_rev_gap) if ic_min_rev_gap else float("nan"),
        "note": "Signalfreies synthetisches Panel (PRD 4.1); Differenz in IC_min-Einheiten, "
                "OHNE Verdikt (task brief item 5).",
    }


# ----------------------------------------------------------------------------
# assembly
# ----------------------------------------------------------------------------

def assemble_prelaunch_report(
    panel: dict[str, Any], weekly: dict[str, Any], *,
    delisted_manifest_path: Path | str | None = None,
    delisting_dates_path: Path | str | None = None,
    stress_rel_path: Path | str | None = None,
    stress_abs_path: Path | str | None = None,
    n_sims: int = nulls.PERSISTENCE_NULL_N_SIMS_DEFAULT,
    n_reps_factor_null: int = nulls.FACTOR_NULL_N_REPS_DEFAULT,
    n_reps_beta_control_study: int = 100,
    n_reps_beta_control_winner: int = 1000,
    seed: int = nulls.PERSISTENCE_NULL_SEED,
    convention: ic.Convention = "close_at_last",
    gegenprobe_n_reps: int = 30, gegenprobe_rel_tol: float = nulls.GEGENPROBE_REL_TOL,
    calibration_search_n_reps: int = nulls.CALIBRATION_SEARCH_N_REPS_DEFAULT,
    calibration_search_rel_tol: float = nulls.CALIBRATION_SEARCH_REL_TOL_DEFAULT,
    calibration_search_max_iter: int = nulls.CALIBRATION_SEARCH_MAX_ITER_DEFAULT,
) -> dict[str, Any]:
    """Assemble the full ``--prelaunch`` report (DEC-74 Entscheidung 2/3),
    given an ALREADY LOADED union panel (``panel`` from
    ``panel_load.load_panel_union``) and its weekly derivation
    (``weekly`` from ``panel_load.weekly_returns_and_mask_union``) --
    this function performs NO I/O of its own (the CLI script owns
    loading), so it is directly unit-testable on a synthetic fixture.

    **THE SEAL, once more, concretely:** ``weekly['returns']`` (the real
    union panel's next-week outcome source) is passed only into
    :func:`window_noise_floor_and_threshold` (which hands it to
    ``nulls.persistence_null``, which NEVER feeds it to
    ``ic.weekly_ic_series`` -- only its OWN simulated arrays are) and into
    :func:`h30_feasibility` (which uses it only for ``stats.sigma_xs_
    summary``, a cross-sectional dispersion statistic, and
    ``ic.vol_weighted_outcome_with_drag``'s drag arithmetic -- neither
    call is an IC). ``ic.weekly_ic_series`` itself is never called from
    this module.

    **DEC-77 Entscheidung 1 (a)/(b)/(c), revised by DEC-78 Entscheidung 1
    and its Nachtrag -- Vorlauf v5, additive.** For W1/W2 (never L): the
    factor-null CALIBRATION (:func:`nulls.factor_calibration_report` --
    ``rho_f_measured``/``sigma_f`` from the real BTCUSDT weekly series,
    ``factor_share``/beta-dispersion from the real 26-week trailing PIT
    beta, plus DEC-78's ``beta_sd_true`` (now a report-only "analytic
    first guess", see that field's docstring) -- single-series and
    returns-vs-beta relations ONLY, THE SEAL's allowed category), the
    beta-control METHOD STUDY (:func:`nulls.beta_control_method_study` --
    3 calibrations (measured/stress/zero, DEC-78 Nachtrag's OBSERVABLE-
    MATCHING ``beta_sd`` construction: bisection-CALIBRATED, :func:`nulls.
    calibrate_beta_sd_to_observed_share`, each preceded by its own loud
    Gegenprobe, expected to PASS BY CONSTRUCTION) x 6 methods
    (:data:`nulls.BETA_CONTROL_METHODS_GRID`, DEC-78 Entscheidung 2: TS-
    residualisation dropped from the grid) x 7 variants, EVERY cell
    simulated-characteristic-vs-simulated-outcome), the PRE-FIXED decision
    table (:func:`beta_control_pass_table`) and, if a method passes in
    BOTH windows, a HIGH-REP (``n_reps_beta_control_winner``) re-run of
    the recommended method's ``"measured"``/``"stress"`` cells for the
    final report table. **DEC-78 Nachtrag: a Gegenprobe failure
    (:class:`nulls.FactorShareCalibrationError`) is NOT caught here** --
    it is now a REAL BUG (the calibration search should avoid this case
    by construction), so it aborts the WHOLE ``--prelaunch`` run, loud,
    exactly like every other C.14 loud fail in this package.
    ``gegenprobe_n_reps``/``gegenprobe_rel_tol``/``calibration_search_
    n_reps``/``calibration_search_rel_tol``/``calibration_search_
    max_iter`` are passed straight through to :func:`nulls.beta_
    control_method_study` (defaults match that function's own, i.e. the
    REAL, literal 25%/10% -- ``scripts/wp13_xsec.py``'s ``--prelaunch``
    CLI never overrides them, so a real run always uses the strict
    defaults; a caller such as a unit test that deliberately exercises
    this pipeline on a TINY, statistically underpowered synthetic panel
    -- where the Gegenprobe's own sampling noise, not a real calibration
    bug, would otherwise make it fail -- may widen ``gegenprobe_rel_tol``
    to isolate what it is actually testing, same discipline as this
    function's existing ``n_sims``/``n_reps_*`` knobs).

    **Runtime, measured, VOM ORCHESTRATOR ZU BESTAETIGEN (documented
    deviation from the task brief's own "300 reps" fallback number).** A
    synthetic-panel microbenchmark (``K=100``/``K=400``, ``W=52``, this
    exact code path, non-profiled) gives ~0.020s/rep-cell at ``K=100`` and
    ~0.066s/rep-cell at ``K=400``; a two-point power-law extrapolation to
    the production scale (``K~1138``, ``W~52``) gives ~0.165s per
    (calibration, method, variant) replicate. The grid is 3 calibrations x
    6 methods x 7 variants = 126 cells/replicate (DEC-78: down from
    DEC-77's 189, TS-residualisation dropped), so 300 reps/cell (the task
    brief's own stated fallback) extrapolates to ``126*300*0.165s ~=
    1.7h PER WINDOW`` (~3.5h for W1+W2 together) -- still past the task
    brief's "~2h" ceiling at 300 reps on this measured hardware.
    Profiling attributes ~68% of that cost to ``characteristics.
    beta_characteristic``'s per-week/per-symbol Python loop (called
    fresh, once per replicate, for every method that needs a beta --
    never shared across methods with the SAME trailing window within one
    replicate, a genuine, un-implemented optimisation opportunity:
    sharing the simulated panel/beta array across same-trail-window
    methods within a replicate would cut this by roughly a third). Given
    this, the DEFAULT here is 100 (not 300) -- ``126*100*0.165s ~= 35
    min/window (~1h10 both)``, safely inside the ~2h budget on hardware
    AT LEAST as fast as the measurement above; the orchestrator can raise
    it via ``--n-reps-beta-control-study`` once the ACTUAL runner PC's
    speed is known (a faster desktop may comfortably afford 300-500). The
    Gegenprobe itself (``gegenprobe_n_reps``, default 30, x 3
    calibrations) is cheap regardless -- no beta-control method involved,
    just :func:`nulls.simulate_factor_panel` + a cross-sectional R^2. The
    winner re-run (``n_reps_beta_control_winner``,
    default 1000, ONE method x 2 calibrations x 7 variants = 14 cells) is
    cheap regardless (~14*1000*0.165s ~= 39 min/window).

    **Extra cost of the DEC-78 Nachtrag's calibration SEARCH, measured.**
    :func:`nulls.calibrate_beta_sd_to_observed_share` runs TWICE per
    window ("measured" + "stress"; "zero" reuses "measured"'s search, no
    extra search), each up to ``calibration_search_max_iter`` (default
    25) bisection iterations x ``calibration_search_n_reps`` (default 40)
    simulate+measure reps -- ONE method cell's worth of work per
    iteration (:func:`nulls._measure_simulated_share`, no beta-control
    method dispatch at all, cheaper than a full grid cell). Measured on
    this exact code path at the PRODUCTION scale (``K=1138``, ``W=53``):
    ~0.34s/rep, and the "measured" search on the real W1 numbers
    (rho_f=0.046, share=0.0162) converged in 4 iterations (~54s); WORST
    CASE (25 iterations, never converging) is ``25*40*0.34s ~= 5.7 min``
    per search, so up to ``~11.4 min/window`` (~23 min for W1+W2) added
    to the grid's own runtime above -- typically much less (single-digit
    iterations observed). The subsequent Gegenprobe re-verification
    (``gegenprobe_n_reps=30``, ONE call per calibration) is the ~10s/call
    already counted above.
    """
    # DEC-75 (8) / task brief item 8: characteristics/day-counts are built on the FULL
    # panel FIRST, then sliced to windows -- the SAME path the future run mode uses
    # (see wp13_xsec.run's module docstring).
    weeks = weekly["weeks"]
    symbols = panel["symbols"]
    returns, alive = weekly["returns"], weekly["alive"]
    vol_rv = characteristics.realized_vol_characteristic(panel, weeks)
    turnover_weekly = characteristics.weekly_turnover(panel, weeks)
    turnover_trail = characteristics.trailing_median_turnover(turnover_weekly)
    day_count = characteristics.weekly_valid_day_count(panel, weeks)
    # DEC-77 Entscheidung 1 (a)(b): the calibration beta -- 26-week trailing, STRICTLY
    # excluding week t itself (module docstring of nulls.trailing_pit_beta_excluding_
    # current_week) -- built on the FULL panel first, DEC-75 (8) discipline, then sliced.
    beta_prev_26w = nulls.trailing_pit_beta_excluding_current_week(
        returns, symbols, market_symbol="BTCUSDT", trail_win=nulls.CALIBRATION_BETA_TRAIL_WEEKS)

    windows_out: dict[str, Any] = {}
    for name, (start, end) in WINDOWS.items():
        try:
            window = slice_window(weeks, start, end, returns, alive, vol_rv, turnover_trail, day_count,
                                   beta_prev_26w)
        except ValueError as exc:
            windows_out[name] = {"available": False, "note": str(exc)}
            continue
        entry: dict[str, Any] = {
            "available": True, "start": start, "end": end, "n_weeks": len(window["weeks"]),
            "week_start": window["weeks"][0], "week_end": window["weeks"][-1],
            "delisting": delisting_counts(window),
            "gate5_reachability": gate5_reachability(window),
        }
        if name == "L":
            entry["descriptive_only"] = True
            entry["h30_feasibility"] = h30_feasibility(window)
        else:
            nf = window_noise_floor_and_threshold(window, convention=convention, n_sims=n_sims, seed=seed)
            entry["noise_floor_and_threshold"] = nf
            e_floor, w_judged = nf["floor"]["e_floor"], nf["w_judged"]
            entry["selection_ceiling_analytic"] = analytic_selection_ceiling(e_floor, w_judged)
            entry["selection_ceiling_measured"] = measured_selection_ceiling(window["alive"], seed=seed)
            entry["factor_preserving_null"] = factor_preserving_report(
                window, symbols, convention=convention, n_reps=n_reps_factor_null, seed=seed)

            # DEC-77 Entscheidung 1 (a)/(b)/(c), revised by DEC-78 Entscheidung 1/Nachtrag -- Vorlauf v5.
            calib = nulls.factor_calibration_report(
                window["returns"], window["alive"], symbols, window["beta_prev_26w"],
                market_symbol="BTCUSDT")
            # DEC-78 Nachtrag (orchestrator decision): beta_sd is now BISECTION-CALIBRATED so the
            # Gegenprobe passes BY CONSTRUCTION -- its own C.14 loud fail (FactorShareCalibration
            # Error) is therefore NOT caught here any more; a failure is a real bug (a stale/
            # inconsistent search), so it aborts the WHOLE --prelaunch run, exactly like every
            # other loud fail in this package.
            study = nulls.beta_control_method_study(
                window["returns"], window["alive"], symbols,
                rho_f_measured=calib["market_factor"]["rho_f_measured"],
                factor_share_measured=calib["factor_share"]["factor_share_median"],
                convention=convention, n_reps=n_reps_beta_control_study, seed=seed,
                gegenprobe_n_reps=gegenprobe_n_reps, gegenprobe_rel_tol=gegenprobe_rel_tol,
                calibration_search_n_reps=calibration_search_n_reps,
                calibration_search_rel_tol=calibration_search_rel_tol,
                calibration_search_max_iter=calibration_search_max_iter)
            decision = beta_control_pass_table(
                study, floor=e_floor, w_judged=w_judged,
                pure_noise_ceiling=entry["selection_ceiling_measured"]["ceiling_ic_mean"])
            entry["factor_calibration"] = calib
            entry["beta_control_method_study"] = study
            entry["beta_control_decision"] = decision

            entry["survivorship_fixture"] = survivorship_drawdown_fixture(
                window, ic_min_mom1=nf["ic_min_capped_per_variant"]["mom1"],
                ic_min_rev_gap=nf["ic_min_capped_per_variant"]["rev_gap"], seed=seed)
        if stress_rel_path is not None:
            entry["stress_rel"] = stress_coverage(stress_rel_path, start, end)
        if stress_abs_path is not None:
            entry["stress_abs"] = stress_coverage(stress_abs_path, start, end)
        windows_out[name] = entry

    # DEC-77 Entscheidung 1 (c): the cross-window recommendation, THEN (if one exists) a
    # HIGH-REP re-run of just that one method's measured/stress cells for the final table
    # (task brief item 2: ">= 1000 for the recommended method in the final table").
    recommendation = beta_control_recommendation(windows_out)
    if recommendation.get("recommended_method"):
        best = recommendation["recommended_method"]
        for wn in ("W1", "W2"):
            w = windows_out.get(wn, {})
            if not w.get("available") or "beta_control_method_study" not in w:
                continue
            window = slice_window(weeks, *WINDOWS[wn], returns, alive, vol_rv, turnover_trail, day_count,
                                   beta_prev_26w)
            # DEC-78 Entscheidung 1/Nachtrag: reuse the STUDY's own (rho_f, beta_sd_calibrated)
            # per calibration -- never a fresh re-derivation/re-search -- so the winner re-run is
            # EXACTLY the same calibration the grid/decision table already validated (Gegenprobe
            # included).
            high_rep = {
                cal: nulls.beta_controlled_factor_null(
                    window["returns"], window["alive"], symbols, method=best, convention=convention,
                    n_reps=n_reps_beta_control_winner, seed=seed,
                    rho_f=study["calibrations"][cal]["rho_f"], drift_f=nulls.DRIFT_F_DRIFTFREE,
                    beta_sd=study["calibrations"][cal]["beta_sd_calibrated"])
                for cal in ("measured", "stress")
            }
            w["beta_control_recommended_high_rep"] = high_rep

    no_history: dict[str, Any] | None = None
    if delisted_manifest_path is not None and delisting_dates_path is not None:
        try:
            no_history = no_history_symbols_report(delisted_manifest_path, delisting_dates_path)
        except (panel_load.PanelLoadError, FileNotFoundError) as exc:
            no_history = {"available": False, "note": str(exc)}

    return {
        "wp": "WP-13a", "mode": "prelaunch",
        "label": "DEC-74 Entscheidung 3 -- keine reale Signal-Outcome-Verknuepfung berechnet "
                 "(Siegel-Test).",
        "windows": windows_out,
        "no_history_symbols": no_history,
        "beta_control_recommendation": recommendation,
        "seed": seed, "n_sims": n_sims, "n_reps_factor_null": n_reps_factor_null,
        "n_reps_beta_control_study": n_reps_beta_control_study,
        "n_reps_beta_control_winner": n_reps_beta_control_winner,
        "convention": convention, "variants": list(characteristics.VARIANT_NAMES),
        "reversal_gap_design_deviation": (
            "PRD 5.3 verlangt einen EIN-TAGES-Gap zwischen Formation und Halteperiode; WP-13 "
            "laeuft ausschliesslich auf dem woechentlichen panel_1d/panel_1d_delisted-Panel, "
            "der kleinste darstellbare Gap ist daher EINE WOCHE (siehe characteristics.py "
            "Modul-Docstring). Abweichung, VOM ORCHESTRATOR VOR DER ZWEITFASSUNG ZU BESTAETIGEN."),
        "selection_ceiling_scale_factor_interpretation": (
            "HALF_SQRT2_FACTOR=1/sqrt(2) ist PRD 5.3's eigener woertlicher Faktor; diese "
            "Implementierung interpretiert ihn als Kombination der ZWEI unabhaengigen Fenster "
            "W1/W2 (siehe prelaunch.py Modul-Docstring). Interpretation, VOM ORCHESTRATOR ZU "
            "BESTAETIGEN."),
    }


def _fmt5(v: float | None) -> str:
    """``:.5f`` formatting that tolerates ``None`` (DEC-76: a market-less
    window's residualized fields are ``None``, never NaN -- see
    ``nulls.factor_preserving_null``'s docstring) without crashing the
    report; ``NaN`` still renders as the literal ``"nan"`` (unchanged)."""
    return "n/a (kein Marktsymbol)" if v is None else f"{v:.5f}"


def _beta_control_calibration_markdown(w: dict[str, Any]) -> list[str]:
    """DEC-77 Entscheidung 1/task brief item 7, extended by DEC-78
    Entscheidung 1: ONE window's calibration block (``rho_f_measured``,
    ``sigma_f``, ``factor_share``, beta quantiles, the analytic
    mechanical-momentum plausibility line, DEC-78's ``beta_sd_true``) plus
    the per-calibration Gegenprobe table and the PASS/FAIL method table
    (rows = methods, columns = measured/stress null mean + ceiling +
    PASS/FAIL). ``[]`` if this window has no DEC-77/78 data (older
    artifact, or L)."""
    if "factor_calibration" not in w:
        return []
    lines: list[str] = []
    calib = w["factor_calibration"]
    mkt, share, disp = calib["market_factor"], calib["factor_share"], calib["beta_dispersion"]
    mom = calib["analytic_mechanical_momentum"]
    q = disp.get("quantiles", {})
    lines.append(f"- **DEC-77 Kalibrierung** ({calib['beta_trail_weeks']}-Wochen-PIT-Beta, 'vorherige Wochen'): "
                 f"rho_f_gemessen={mkt['rho_f_measured']:.4f}, sigma_f={mkt['sigma_f']:.5f} "
                 f"(n={mkt['n_weeks_used']} Wochen); Faktoranteil (Median Querschnitts-R^2)="
                 f"{share['factor_share_median']:.4f} (n={share['n_weeks_used']} Wochen); "
                 f"Beta-Dispersion (PIT-Pool, ueberwiegend Schaetzrauschen -- DEC-78 Befund): "
                 f"SD={disp.get('sd', float('nan')):.4f}, "
                 f"Quantile[0.05/0.25/0.5/0.75/0.95]="
                 f"[{q.get('0.05', float('nan')):.3f}/{q.get('0.25', float('nan')):.3f}/"
                 f"{q.get('0.5', float('nan')):.3f}/{q.get('0.75', float('nan')):.3f}/"
                 f"{q.get('0.95', float('nan')):.3f}] (n_gepoolt={disp.get('n_pooled', 0)})")
    lines.append(f"  - {mom['label']} {mom['formula']} = {_fmt5(mom['value'])}")
    bst = calib.get("beta_sd_true", {})
    if bst:
        lines.append(f"  - {bst['label']} {bst['formula']} = {_fmt5(bst['value'])}")

    study = w.get("beta_control_method_study")
    if study is not None and "calibrations" in study:
        lines.append("")
        lines.append("| Kalibrierung | rho_f | beta_sd (analyt. Erstschaetzung) | "
                      "beta_sd (kalibriert) | Ziel-Faktoranteil | erreichter Faktoranteil "
                      "(Suche) | wahrer Faktoranteil (Suche) | Iterationen | konvergiert | "
                      "Gegenprobe simuliert | Gegenprobe rel. Abw. | Gegenprobe |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for cal in ("measured", "stress", "zero"):
            c = study["calibrations"][cal]
            g = c["gegenprobe"]
            s = c["calibration_search"]
            lines.append(
                f"| {cal} | {_fmt5(c['rho_f'])} | {_fmt5(c['beta_sd_analytic_first_guess'])} | "
                f"{_fmt5(c['beta_sd_calibrated'])} | {_fmt5(c['target_factor_share'])} | "
                f"{_fmt5(s['achieved_share'])} | {_fmt5(s['true_share'])} | {s['n_iter']} | "
                f"{'ja' if s['converged'] else 'nein'} | "
                f"{_fmt5(g['simulated_factor_share'])} | {_fmt5(g['rel_diff'])} | "
                f"{'OK' if g['ok'] else 'FAIL'} |")
        lines.append("")

    if "beta_control_decision" in w:
        dec = w["beta_control_decision"]
        lines.append(f"- Beta-Kontroll-Kriterium: |Null-Mittel| <= {_fmt5(dec['null_mean_bound'])} UND "
                     f"Decke <= {_fmt5(dec['ceiling_bound'])} (measured UND stress)")
        lines.append("")
        lines.append("| Methode | measured Null-Mittel | measured Decke | stress Null-Mittel | "
                     "stress Decke | PASS |")
        lines.append("|---|---|---|---|---|---|")
        for row in dec["rows"]:
            m, s = row["measured"], row["stress"]
            lines.append(
                f"| {row['method']} | {_fmt5(m['worst_abs_null_mean'])} | {_fmt5(m['ceiling'])} | "
                f"{_fmt5(s['worst_abs_null_mean'])} | {_fmt5(s['ceiling'])} | "
                f"{'PASS' if row['pass'] else 'FAIL'} |")
        lines.append("")
        if dec.get("note"):
            lines.append(f"- {dec['note']}")
    hr = w.get("beta_control_recommended_high_rep")
    if hr:
        m, s = hr["measured"]["variants"], hr["stress"]["variants"]
        lines.append(f"- Gewinner-Methode, hoehere Replikatzahl (n_reps={hr['measured']['n_reps']}): "
                     f"measured Decke={_fmt5(hr['measured']['ceiling_mean_of_max'])}, "
                     f"stress Decke={_fmt5(hr['stress']['ceiling_mean_of_max'])}")
    return lines


def _to_markdown(report: dict[str, Any]) -> str:
    lines = ["# WP-13a -- Vorlauf-Befund (DEC-74 Entscheidung 3)", "", report["label"], "",
              "**KEIN VERDIKT -- keine reale Charakteristik-gegen-reale-Folgewochenrendite-IC "
              "wurde in diesem Lauf berechnet.**", ""]
    for name in ("W1", "W2", "L"):
        w = report["windows"].get(name)
        if not w or not w.get("available"):
            lines.append(f"## Fenster {name}: nicht verfuegbar ({(w or {}).get('note')})")
            continue
        lines.append(f"## Fenster {name} ({w['start']}..{w['end']}, {w['n_weeks']} Wochen, "
                      f"{w['week_start']}..{w['week_end']})")
        lines.append(f"- Delisting-Symbol-Wochen: {w['delisting']['n_symbol_weeks_delisting']}")
        g5 = w["gate5_reachability"]
        lines.append(f"- Gate (5) Erreichbarkeit: Median Spearman(vol_rv,Turnover) = {g5['median']} "
                      f"(< 0,60 = {g5['gate5_reachable']}, n={g5['n_weeks_used']} Wochen)")
        if name == "L":
            h = w["h30_feasibility"]
            lines.append(f"- H-30 (v2) Kante = {h['kante_bps_per_week']:.2f} bp/Woche, "
                          f"Spread(D10-D1)/Kante = {h['spread_d10_minus_d1_over_kante']:.3f}, "
                          f"SE(sigma_w^2/2)/Kante = {h['se_drag_over_kante']:.3f} "
                          f"(feasibel <= 0,5 beide: {h['feasible']})")
        else:
            nf = w["noise_floor_and_threshold"]
            lines.append(f"- W_geurteilt = {nf['w_judged']}, E_t[1/sqrt(K_t-1)] = "
                          f"{nf['floor']['e_floor']:.5f} (K min/median/max siehe Artefakt)")
            for v in report["variants"]:
                thr_capped = nf["ic_min_capped_per_variant"][v]
                thr_raw = nf["ic_min_raw_per_variant"][v]
                pv = nf["persistence_null"]["variants"][v]
                lines.append(f"  - {v}: IC_min_capped = {thr_capped:.5f}, IC_min_raw = {thr_raw:.5f} "
                              f"(c_rho_raw={pv['c_rho_raw']:.4f}, c_rho_corrected={pv['c_rho_corrected']:.4f})")
            sc_a = w["selection_ceiling_analytic"]
            sc_m = w["selection_ceiling_measured"]
            lines.append(f"- Selektions-Decke K=7 analytisch = {sc_a['ceiling_ic']:.5f}, "
                         f"gemessen (reine Rauschen) = {sc_m['ceiling_ic_mean']:.5f} "
                         f"(n_replicates={sc_m['n_replicates']})")
            fp = w["factor_preserving_null"]
            drifting, driftfree = fp["drifting"], fp["driftfree"]
            lines.append(f"- Faktorerhaltende Null v3 (DEC-76), n_reps={drifting['n_reps']}: "
                         f"sigma_e gesamt={drifting['sigma_e_median_symbol_weekly']:.5f}, "
                         f"sigma_e idiosynkratisch (verwendet)="
                         f"{drifting['sigma_e_median_symbol_weekly_idiosyncratic']:.5f}")
            lines.append(f"- GL-012-bindende Decke (driftfree, residualisiert) = "
                         f"{_fmt5(driftfree['selection_ceiling_mean_of_max_residualized'])} "
                         f"(driftfree roh, report-only = {_fmt5(driftfree['selection_ceiling_mean_of_max'])}; "
                         f"drifting roh, report-only = {_fmt5(drifting['selection_ceiling_mean_of_max'])}; "
                         f"drifting residualisiert, report-only = "
                         f"{_fmt5(drifting['selection_ceiling_mean_of_max_residualized'])})")
            lines.append("")
            lines.append("| Variante | E_t[1/sqrt(K-1)] | c_rho_corrected | IC_min_capped | "
                         "Decke driftfree roh (Fenster, report-only) | "
                         "Decke driftfree res (Fenster, bindend GL-012) | "
                         "Quantil drifting res (bindend Beta-Kontrolle) | "
                         "Mittel drifting roh (Beta-Prognostizierbarkeit, report-only) |")
            lines.append("|---|---|---|---|---|---|---|---|")
            ceiling_driftfree_raw = driftfree["selection_ceiling_mean_of_max"]
            ceiling_driftfree_res = driftfree["selection_ceiling_mean_of_max_residualized"]
            for v in report["variants"]:
                pv = nf["persistence_null"]["variants"][v]
                dv = drifting["variants"][v]
                lines.append(
                    f"| {v} | {nf['floor']['e_floor']:.5f} | {pv['c_rho_corrected']:.4f} | "
                    f"{nf['ic_min_capped_per_variant'][v]:.5f} | "
                    f"{_fmt5(ceiling_driftfree_raw)} | {_fmt5(ceiling_driftfree_res)} | "
                    f"{_fmt5(dv['quantile_one_sided_residualized'])} | {_fmt5(dv['mean_ic_draws_mean'])} |")
            lines.append("")
            sv = w["survivorship_fixture"]
            lines.append(f"- Survivorship-Fixture: mom1 Diff={sv['mom1_diff']:.5f} "
                         f"({sv['mom1_diff_in_ic_min_units']:.3f} IC_min-Einheiten), "
                         f"rev_gap Diff={sv['rev_gap_diff']:.5f} "
                         f"({sv['rev_gap_diff_in_ic_min_units']:.3f} IC_min-Einheiten), "
                         f"n_deleted={sv['n_deleted']}/{sv['k']} (kein Verdikt)")
            lines.append("")
            lines.extend(_beta_control_calibration_markdown(w))
        if "stress_rel" in w:
            sr = w["stress_rel"]
            lines.append(f"- STRESS_REL: {'nicht vorhanden' if not sr.get('available') else sr.get('n_days_in_window')}")
        if "stress_abs" in w:
            sa = w["stress_abs"]
            lines.append(f"- STRESS_ABS: {'nicht vorhanden' if not sa.get('available') else sa.get('n_days_in_window')}")
        lines.append("")
    nh = report.get("no_history_symbols")
    if nh:
        lines.append(f"## NO_HISTORY-Symbole ({nh.get('n_no_history')})")
        for row in nh.get("symbols", []):
            lines.append(f"- {row['symbol']}: delistet {row['delist_date']} (Woche {row['delist_week']})")
        lines.append("")
    rec = report.get("beta_control_recommendation")
    if rec:
        lines.append("## DEC-77 Beta-Kontroll-Empfehlung")
        if rec.get("recommended_method"):
            lines.append(f"- {rec['note']} (Fenster {rec['beta_window_weeks']}, "
                         f"zulaessige Methoden: {', '.join(rec['eligible_methods'])})")
        else:
            lines.append(f"- {rec['note']}")
        lines.append("")
    lines.append("## Abweichungen (zur Bestaetigung durch den Orchestrator)")
    lines.append(f"- {report['reversal_gap_design_deviation']}")
    lines.append(f"- {report['selection_ceiling_scale_factor_interpretation']}")
    lines.append("")
    lines.append("Das W1/W2-Fenster-Detail (Wochenlisten, K-Serien, Persistenz-Null-Replikate) "
                 "steht in den DEC-53-Artefakten; das L-Fenster liegt in einer separaten, "
                 "versiegelten Datei (DEC-74 (k)).")
    return "\n".join(lines)


def write_prelaunch_artifacts(out_dir: Path | str, report: dict[str, Any]) -> dict[str, Any]:
    """DEC-53 artifacts for the prelaunch report: the main JSON+MD, and
    the L window split into its OWN sealed file (DEC-74 (k): "L-Fenster in
    getrennter, versiegelter Datei") -- everything sha256'd. Never writes
    under ``data/harvest``."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    main_report = dict(report)
    main_windows = dict(report["windows"])
    l_window = main_windows.pop("L", None)
    main_report["windows"] = main_windows
    if l_window is not None:
        main_report["windows"]["L"] = {"available": l_window.get("available", True),
                                        "note": "siehe l_window_sealed_json (DEC-74 (k))"}

    main_json = out_dir / "wp13a_prelaunch.json"
    main_json.write_text(json.dumps(main_report, indent=1), encoding="utf-8")
    artifacts: dict[str, Any] = {
        "wp13a_prelaunch_json": {"path": str(main_json), "sha256": panel_load.sha256_file(main_json)}}

    if l_window is not None:
        l_path = out_dir / "wp13a_prelaunch_L_window_sealed.json"
        l_path.write_text(json.dumps(l_window, indent=1), encoding="utf-8")
        artifacts["l_window_sealed_json"] = {"path": str(l_path), "sha256": panel_load.sha256_file(l_path)}

    md_path = out_dir / "wp13a_prelaunch.md"
    md_path.write_text(_to_markdown(report), encoding="utf-8")
    artifacts["wp13a_prelaunch_md"] = {"path": str(md_path), "sha256": panel_load.sha256_file(md_path)}

    return {"out_dir": str(out_dir), "artifacts": artifacts}
