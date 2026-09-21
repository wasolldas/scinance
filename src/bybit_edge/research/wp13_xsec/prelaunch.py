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
    "write_prelaunch_artifacts",
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
    for name, arr in zip(("returns", "alive", "vol_rv", "turnover_trail")[:len(arrays)], arrays):
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
    pnull = nulls.persistence_null(window["returns"], window["alive"], window["weeks"],
                                    variants=variants, convention=convention,
                                    n_sims=n_sims, seed=seed)
    thresholds = {
        v: nulls.ic_threshold(floor["e_floor"], pnull["variants"][v]["c_rho"], floor["n_weeks"])
        for v in variants
    }
    return {"floor": floor, "persistence_null": pnull, "ic_min_per_variant": thresholds}


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
    """DEC-74 (h): ``Kante = 3.51 * IC_prior * sigma_xs(L)`` (bp/week);
    ``Drag_rest`` after vol-weighting, ``Drag_rest/Kante``.

    **``Drag_rest`` computation, spelled out exactly (task brief
    requirement).** ``ic.vol_weighted_outcome_with_drag`` scales every
    symbol-week's exposure by ``target_vol/vol_j`` (``target_vol`` =
    cross-sectional MEDIAN of the L-window's realized weekly vol,
    ``vol_rv``) so every leg contributes the SAME target variance; the
    per-leg vol-drag term ``sigma^2/2`` (PRD 5.3, verbatim) THEN COLLAPSES
    to the SAME constant ``target_vol^2/2`` for every leg (since every
    leg's realised vol is now ``target_vol`` by construction), replacing
    the heterogeneous raw ``sigma_j^2/2``. ``Drag_rest`` is that constant,
    reported in bp/week (``0.5 * target_vol^2 * 1e4``); the RAW (pre-
    weighting) per-decile drag table is reported alongside it for
    comparison (PRD 5.3 (iii): "Permutations-Null auf identisch
    vol-geschichteten Zufallsportfolios" needs the raw table too, even
    though the null itself is not computed in --prelaunch).
    """
    sigma_xs = stats.sigma_xs_summary(window_l["returns"], window_l["alive"])
    sigma_xs_median = sigma_xs["median"] or 0.0
    kante_bps = f * ic_prior * sigma_xs_median * 10_000.0

    vol_rv, alive, weeks = window_l["vol_rv"], window_l["alive"], window_l["weeks"]
    vw = ic.vol_weighted_outcome_with_drag(window_l["returns"], vol_rv)
    drag_rest_bps = float(vw["target_vol"] ** 2 * 0.5 * 10_000.0)

    by_decile: dict[int, list[float]] = {d: [] for d in range(1, 11)}
    for t in range(len(weeks)):
        mask = alive[t]
        buckets = characteristics.decile_bucket(vol_rv[t], mask)
        drag_raw_t = 0.5 * vol_rv[t] ** 2 * 10_000.0
        for d in range(1, 11):
            vals = drag_raw_t[(buckets == d) & ~np.isnan(drag_raw_t)]
            by_decile[d].extend(float(v) for v in vals)
    decile_table = [
        {"decile": d, "median_drag_raw_bps": (float(np.median(v)) if v else None), "n_symbol_weeks": len(v)}
        for d, v in by_decile.items()
    ]

    ratio = (drag_rest_bps / kante_bps) if kante_bps else float("nan")
    return {
        "sigma_xs_l": sigma_xs, "ic_prior": ic_prior, "decile_factor": f,
        "kante_bps_per_week": kante_bps, "target_vol": vw["target_vol"],
        "drag_rest_bps_per_week": drag_rest_bps, "drag_rest_over_kante": ratio,
        "feasible": (ratio <= 0.5) if not math.isnan(ratio) else None,
        "decile_drag_table_raw_bps": decile_table,
        "note": "Drag_rest = 0.5*target_vol^2 (bp/Woche); target_vol = Median von vol_rv(L) -- "
                "siehe h30_feasibility Docstring fuer die exakte Herleitung.",
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
    window's K series and W")."""
    n_weeks = alive_window.shape[0]
    ics: list[float] = []
    for t in range(n_weeks):
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
# assembly
# ----------------------------------------------------------------------------

def assemble_prelaunch_report(
    panel: dict[str, Any], weekly: dict[str, Any], *,
    delisted_manifest_path: Path | str | None = None,
    delisting_dates_path: Path | str | None = None,
    stress_rel_path: Path | str | None = None,
    stress_abs_path: Path | str | None = None,
    n_sims: int = nulls.PERSISTENCE_NULL_N_SIMS_DEFAULT,
    seed: int = nulls.PERSISTENCE_NULL_SEED,
    convention: ic.Convention = "close_at_last",
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
    """
    weeks = weekly["weeks"]
    returns, alive = weekly["returns"], weekly["alive"]
    vol_rv = characteristics.realized_vol_characteristic(panel, weeks)
    turnover_weekly = characteristics.weekly_turnover(panel, weeks)
    turnover_trail = characteristics.trailing_median_turnover(turnover_weekly)

    windows_out: dict[str, Any] = {}
    for name, (start, end) in WINDOWS.items():
        try:
            window = slice_window(weeks, start, end, returns, alive, vol_rv, turnover_trail)
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
            entry["noise_floor_and_threshold"] = window_noise_floor_and_threshold(
                window, convention=convention, n_sims=n_sims, seed=seed)
            e_floor = entry["noise_floor_and_threshold"]["floor"]["e_floor"]
            entry["selection_ceiling_analytic"] = analytic_selection_ceiling(e_floor, len(window["weeks"]))
            entry["selection_ceiling_measured"] = measured_selection_ceiling(window["alive"], seed=seed)
        if stress_rel_path is not None:
            entry["stress_rel"] = stress_coverage(stress_rel_path, start, end)
        if stress_abs_path is not None:
            entry["stress_abs"] = stress_coverage(stress_abs_path, start, end)
        windows_out[name] = entry

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
        "seed": seed, "n_sims": n_sims, "convention": convention, "variants": list(characteristics.VARIANT_NAMES),
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
            lines.append(f"- H-30 Kante = {h['kante_bps_per_week']:.2f} bp/Woche, "
                          f"Drag_rest = {h['drag_rest_bps_per_week']:.2f} bp/Woche, "
                          f"Drag_rest/Kante = {h['drag_rest_over_kante']:.3f} "
                          f"(feasibel <= 0,5: {h['feasible']})")
        else:
            nf = w["noise_floor_and_threshold"]
            lines.append(f"- E_t[1/sqrt(K_t-1)] = {nf['floor']['e_floor']:.5f} "
                         f"(K min/median/max siehe Artefakt)")
            for v in report["variants"]:
                thr = nf["ic_min_per_variant"][v]
                c_rho = nf["persistence_null"]["variants"][v]["c_rho"]
                lines.append(f"  - {v}: IC_min = {thr:.5f} (c_rho={c_rho:.4f})")
            sc_a = w["selection_ceiling_analytic"]
            sc_m = w["selection_ceiling_measured"]
            lines.append(f"- Selektions-Decke K=7 analytisch = {sc_a['ceiling_ic']:.5f}, "
                         f"gemessen = {sc_m['ceiling_ic_mean']:.5f} (n_replicates={sc_m['n_replicates']})")
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
