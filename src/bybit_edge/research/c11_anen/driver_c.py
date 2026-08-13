"""H-11c driver — AnEn vs. dispersion-matched HAR (Dressed-HAR), KAPITALFREI.

Registered follow-up obligation from GL-022 (registry H-11c, 2026-08-12).
GL-022 adjudicated H-11 as WEITER under its registered wording but attached
binding restriction labels: the registered rule scores a DIRAC baseline
against a 20-member DISTRIBUTION, which alone yields CRPSS ~0.21-0.29 for an
information-free forecaster, i.e. the H-11 threshold of 0.05 sits a factor
~4-5 BELOW the structural floor of its own metric. H-11c re-runs the identical
comparison with that term removed:

  * AnEn side: bit-identical to the GL-022 run — same features, same k=20,
    same 30-day embargo, same FROZEN weights (no re-tuning: the weights are
    constants here, taken from the registered GL-022 payload). Reproduction of
    the archived ``sum_crps_anen`` per cell is VERIFIED and reported; a
    mismatch marks the run invalid instead of quietly scoring something else.
  * Baseline side: HAR-RV point forecast UNCHANGED, dressed with a k=20
    quantile sample of the empirical in-fit residuals of the same monthly
    refit (``dressed.har_forecast_series_dressed``) — no look-ahead, no
    distributional assumption, no RNG.
  * Both sides scored with the SAME registered ensemble CRPS
    (1/k)sum|x_i-y| - (1/(2k^2))sum sum|x_i-x_j|.

Gate (registry H-11c, verbatim): WEITER if for at least one symbol in
{BTC,ETH} in BOTH windows CRPSS_dressed >= 0.05 AND block-bootstrap p <= 0.05
after BH-FDR alpha=0.10 over **F-ANEN-C**. Hard one-window DROP, no
Graubereich, no re-tuning of anything.

Mandatory diagnostics, pre-registered as NON-judgment-bearing so they must be
reported honestly without being able to move the gate: (a) MAE of the ensemble
MEDIAN vs. HAR MAE with a two-sided block-bootstrap DM test — this closes the
functional gap disclosed in GL-022; (b) dispersion calibration (ensemble
spread vs. realised error spread) for both sides; (c) PIT rank histograms of
both sides with a chi^2 test against uniformity.

The payload is GATE-NEUTRAL; the gate-auditor adjudicates. KAPITALFREI: no
bps, no PnL, no friction quantity of any kind (the H-11 25-75x friction note
is explicitly DECOUPLED per GL-022 label E5).
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

import numpy as np

from .analog import EMBARGO_DAYS, K_ANALOGS, analog_forecast
from .driver import (
    DEFAULT_SYMBOLS,
    REGISTRY_PATH,
    TUNE_RANGE,
    UNLOCK_MIN_DAYS,
    UNLOCK_RANGE,
    W1_RANGE,
    W2_RANGE,
    WINDOW_LABELS,
    _window_indices,
    check_unlock,
)
from .dressed import (
    block_bootstrap_p_two_sided,
    chi2_uniform_pvalue,
    har_forecast_series_dressed,
)
from .features import (
    TARGET_HORIZON_DAYS,
    build_daily_panel,
    compute_feature_matrix,
    compute_target,
)
from .stats import (
    BLOCK_LEN_DAYS,
    BOOTSTRAP_P_MAX,
    CRPSS_MIN,
    FDR_ALPHA,
    N_BOOTSTRAP,
    benjamini_hochberg,
    block_bootstrap_p,
    crps_ensemble,
    crps_point,
    crpss,
    pit_ranks,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-11c"
FDR_FAMILY = "F-ANEN-C"

#: Weights FROZEN on region L by the GL-022 run — constants here by
#: registration ("kein Re-Tuning"). Order: logRV1d, logRV5d, logRV20d,
#: funding daily mean, funding 5d trend.
FROZEN_WEIGHTS: dict[str, tuple[float, ...]] = {
    "BTCUSDT": (2.0, 2.0, 0.5, 0.0, 0.0),
    "ETHUSDT": (2.0, 0.5, 0.0, 0.0, 0.0),
}

#: Archived AnEn CRPS sums of the GL-022 run (state/h11_20260811_135839/
#: c11_anen_results.json). Reproducing these proves the AnEn side is
#: untouched — the registered precondition of H-11c.
GL022_SUM_CRPS_ANEN: dict[tuple[str, str], float] = {
    ("BTCUSDT", "W1"): 26.623978231118215,
    ("BTCUSDT", "W2"): 12.442607195621484,
    ("ETHUSDT", "W1"): 29.21240040285064,
    ("ETHUSDT", "W2"): 15.00517644955954,
}

#: Archived H-11 CRPSS of the GL-022 run (same payload). Recomputing it under
#: the OLD Dirac rule from today's data is the second half of the continuity
#: proof: it shows the whole H-11 measurement, not just one intermediate sum,
#: still lands where it landed.
GL022_CRPSS_POINT_RULE: dict[tuple[str, str], float] = {
    ("BTCUSDT", "W1"): 0.29174000628983676,
    ("BTCUSDT", "W2"): 0.24007684034644505,
    ("ETHUSDT", "W1"): 0.24754487974580774,
    ("ETHUSDT", "W2"): 0.26145678565358554,
}

#: MATERIALITY bound for the continuity check (registry H-11c Nachtrag 2
#: 2026-08-12, DEC-32). NOT a bit-identity tolerance: the harvest store is
#: LIVE — the harvester may rewrite, dedup or compact historical partitions
#: between two runs, so byte-identity against an archive taken on another day
#: is structurally unachievable and the original 1e-9 precondition was a
#: design error. The bound is derived from the GATE ARITHMETIC, not from any
#: observed deviation: a relative perturbation eps on the CRPS sums moves
#: CRPSS by at most ~2*eps, so eps <= 1e-4 caps the induced CRPSS error at
#: 2e-4 — 250x smaller than the 0.05 threshold itself.
MATERIALITY_RTOL = 1e-4


def _repro_check(symbol: str, window: str, sum_anen: float | None,
                 crpss_point_rule: float | None) -> dict[str, Any]:
    """Continuity of the AnEn side against the archived GL-022 run.

    Two independent quantities must both stay inside ``MATERIALITY_RTOL``:
    the AnEn CRPS sum (the ensemble itself) and the reproduced H-11 CRPSS
    under the old Dirac rule (the whole measurement). The raw relative
    deviations are ALWAYS reported, whether or not they pass — a drifting
    data snapshot must stay visible, not be swallowed by a tolerance.
    """
    ref_sum = GL022_SUM_CRPS_ANEN.get((symbol, window))
    ref_skill = GL022_CRPSS_POINT_RULE.get((symbol, window))

    def _rel(ref: float | None, obs: float | None) -> float | None:
        if ref is None or obs is None or not ref:
            return None
        return abs(obs - ref) / abs(ref)

    rel_sum = _rel(ref_sum, sum_anen)
    rel_skill = _rel(ref_skill, crpss_point_rule)
    ok = (rel_sum is not None and rel_sum <= MATERIALITY_RTOL
          and rel_skill is not None and rel_skill <= MATERIALITY_RTOL)
    return {
        "reference": None if ref_sum is None else float(ref_sum),
        "observed": None if sum_anen is None else float(sum_anen),
        "rel_diff": rel_sum,
        "reference_crpss_point_rule": None if ref_skill is None else float(ref_skill),
        "observed_crpss_point_rule": None if crpss_point_rule is None else float(crpss_point_rule),
        "rel_diff_crpss_point_rule": rel_skill,
        "materiality_rtol": MATERIALITY_RTOL,
        "matches": bool(ok),
    }


def _panel_fingerprint(rv: Any, funding: Any, dates: list[str]) -> dict[str, Any]:
    """SHA-256 over the exact float bytes of the daily panel.

    Recorded so that a future run can PROVE whether the harvest snapshot moved
    underneath it (live store: backfill/dedup/compaction may rewrite historical
    partitions) instead of leaving the question open, as it was after the
    2026-08-12 H-11c run. Purely forensic; reads into no gate flag.
    """
    import hashlib

    h_rv = hashlib.sha256(np.ascontiguousarray(rv, dtype=np.float64).tobytes())
    h_fd = hashlib.sha256(np.ascontiguousarray(funding, dtype=np.float64).tobytes())
    h_dt = hashlib.sha256("|".join(dates).encode("utf-8"))
    return {"n_days": len(dates), "first_day": dates[0] if dates else None,
            "last_day": dates[-1] if dates else None,
            "sha256_rv_daily": h_rv.hexdigest(),
            "sha256_funding_daily": h_fd.hexdigest(),
            "sha256_dates": h_dt.hexdigest()}


def run(
    base_dir: str,
    *,
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    tune_range: tuple[str, str] = TUNE_RANGE,
    w1_range: tuple[str, str] = W1_RANGE,
    w2_range: tuple[str, str] = W2_RANGE,
    unlock_range: tuple[str, str] = UNLOCK_RANGE,
    unlock_min_days: int = UNLOCK_MIN_DAYS,
    k: int = K_ANALOGS,
    embargo: int = EMBARGO_DAYS,
    block_len: int = BLOCK_LEN_DAYS,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    weights_override: dict[str, tuple[float, ...]] | None = None,
    skip_unlock_check: bool = False,
    skip_repro_check: bool = False,
    source: str = "",
) -> dict[str, Any]:
    """Run the pre-registered H-11c gate (gate-neutral payload).

    ``weights_override`` / ``skip_repro_check`` exist ONLY for synthetic
    fixture tests (a fixture cannot reproduce the GL-022 sums); a registered
    run uses neither.
    """
    unlock = check_unlock(
        base_dir, symbols=symbols,
        start=unlock_range[0], end=unlock_range[1], min_days=unlock_min_days,
    )
    if not unlock["unlocked"] and not skip_unlock_check:
        print(f"[c11c] SKIP: {HYPOTHESIS_ID} data-gated — unlock condition unmet",
              file=sys.stderr, flush=True)
        return {
            "schema_version": SCHEMA_VERSION, "hypothesis": HYPOTHESIS_ID,
            "hypothesis_registry": REGISTRY_PATH, "capital_free": True,
            "data_gated": True, "status": "SKIP",
            "reason": "Entsperr-Bedingung (H-11) unerfuellt — kein Lauf.",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": source, "symbols": list(symbols), "unlock_check": unlock,
            "gate_valid": False, "cells": [],
        }

    weights_map = dict(FROZEN_WEIGHTS)
    if weights_override:
        weights_map.update(weights_override)

    panel_start = tune_range[0]
    panel_end = (date.fromisoformat(w2_range[1])
                 + timedelta(days=TARGET_HORIZON_DAYS)).isoformat()

    cells: list[dict[str, Any]] = []
    fingerprints: dict[str, Any] = {}
    for sym in symbols:
        if sym not in weights_map:
            raise ValueError(f"no frozen weights registered for {sym}")
        weights = np.asarray(weights_map[sym], dtype=np.float64)
        print(f"[c11c] {sym}: panel {panel_start}..{panel_end}, frozen weights "
              f"{list(weights)} (NO re-tuning)", file=sys.stderr, flush=True)
        panel = build_daily_panel(base_dir, sym, panel_start, panel_end)
        feats, log_rv22 = compute_feature_matrix(panel.rv_daily, panel.funding_daily)
        targets = compute_target(panel.rv_daily, TARGET_HORIZON_DAYS)
        dates = panel.dates
        fingerprints[sym] = _panel_fingerprint(
            panel.rv_daily, panel.funding_daily, dates)

        for w_label, (w_start, w_end) in zip(WINDOW_LABELS, (w1_range, w2_range)):
            w_idx = _window_indices(dates, w_start, w_end)
            anen_members: list[np.ndarray] = []
            har_days: list[int] = []
            for t in w_idx:
                t = int(t)
                if not np.isfinite(targets[t]):
                    continue
                members, _sel = analog_forecast(
                    feats, targets, t, weights, k=k, embargo=embargo)
                if members.size:
                    anen_members.append(members)
                    har_days.append(t)
            har_idx = np.asarray(har_days, dtype=np.int64)
            if har_idx.size:
                har_fc, n_refits, dressed = har_forecast_series_dressed(
                    feats[:, 0], feats[:, 1], log_rv22, targets, dates, har_idx,
                    k=k, embargo=embargo,
                )
            else:
                har_fc = np.empty(0, dtype=np.float64)
                dressed = np.empty((0, k), dtype=np.float64)
                n_refits = 0
            members_mat = (np.vstack(anen_members) if anen_members
                           else np.empty((0, k), dtype=np.float64))
            paired = np.isfinite(har_fc)
            obs = targets[har_idx][paired]
            n_days = int(paired.sum())

            c_anen = crps_ensemble(members_mat[paired], obs)
            c_dressed = crps_ensemble(dressed[paired], obs)
            # reported for continuity with GL-022 only — NOT the H-11c gate:
            c_point = crps_point(har_fc[paired], obs)

            skill = crpss(c_anen, c_dressed) if n_days else float("nan")
            d = c_dressed - c_anen  # H0: mean(Dressed - AnEn) <= 0
            p_boot = block_bootstrap_p(d, block_len=block_len,
                                       n_bootstrap=n_bootstrap, seed=seed)

            # --- non-judgment-bearing diagnostics (registry H-11c) ----------
            if n_days:
                med = np.median(members_mat[paired], axis=1)
                ae_med = np.abs(med - obs)
                ae_har = np.abs(har_fc[paired] - obs)
                d_point = ae_har - ae_med       # >0 => AnEn median better
                p_point = block_bootstrap_p_two_sided(
                    d_point, block_len=block_len, n_bootstrap=n_bootstrap, seed=seed)
                disp_anen = float(np.mean(np.std(members_mat[paired], axis=1, ddof=1)))
                disp_dressed = float(np.mean(np.std(dressed[paired], axis=1, ddof=1)))
                err_sd_anen = float(np.std(med - obs, ddof=1)) if n_days > 1 else float("nan")
                err_sd_har = float(np.std(har_fc[paired] - obs, ddof=1)) if n_days > 1 else float("nan")
                pit_anen = np.bincount(pit_ranks(members_mat[paired], obs),
                                       minlength=k + 1)[: k + 1]
                pit_dressed = np.bincount(pit_ranks(dressed[paired], obs),
                                          minlength=k + 1)[: k + 1]
                chi_a, p_chi_a = chi2_uniform_pvalue(pit_anen)
                chi_d, p_chi_d = chi2_uniform_pvalue(pit_dressed)
                diagnostics = {
                    "note": "NON-judgment-bearing (registry H-11c); reads into no gate flag",
                    "mae_ensemble_median": float(np.mean(ae_med)),
                    "mae_har_point": float(np.mean(ae_har)),
                    "mae_diff_har_minus_median": float(np.mean(d_point)),
                    "mae_diff_two_sided_boot_p": float(p_point),
                    "mean_ensemble_sd_anen": disp_anen,
                    "mean_ensemble_sd_dressed": disp_dressed,
                    "error_sd_anen_median": err_sd_anen,
                    "error_sd_har_point": err_sd_har,
                    "dispersion_ratio_anen": (disp_anen / err_sd_anen
                                              if err_sd_anen and np.isfinite(err_sd_anen)
                                              else None),
                    "dispersion_ratio_dressed": (disp_dressed / err_sd_har
                                                 if err_sd_har and np.isfinite(err_sd_har)
                                                 else None),
                    "pit_hist_anen": [int(x) for x in pit_anen],
                    "pit_hist_dressed": [int(x) for x in pit_dressed],
                    "pit_chi2_anen": float(chi_a), "pit_chi2_p_anen": float(p_chi_a),
                    "pit_chi2_dressed": float(chi_d), "pit_chi2_p_dressed": float(p_chi_d),
                }
            else:
                diagnostics = {"note": "no paired days"}

            skill_point_rule = (float(crpss(c_anen, c_point)) if n_days else None)
            repro = _repro_check(sym, w_label,
                                 float(np.sum(c_anen)) if n_days else None,
                                 skill_point_rule)
            cells.append({
                "symbol": sym,
                "window": w_label,
                "window_range": [w_start, w_end],
                "n_forecast_days": n_days,
                "n_har_refits": int(n_refits),
                "sum_crps_anen": float(np.sum(c_anen)) if n_days else None,
                "sum_crps_dressed_har": float(np.sum(c_dressed)) if n_days else None,
                "mean_crps_anen": float(np.mean(c_anen)) if n_days else None,
                "mean_crps_dressed_har": float(np.mean(c_dressed)) if n_days else None,
                # GL-022 continuity only (the Dirac rule H-11c replaces):
                "mean_crps_har_point_gl022_rule": float(np.mean(c_point)) if n_days else None,
                "crpss_vs_point_gl022_rule": skill_point_rule,
                "crpss": float(skill) if np.isfinite(skill) else None,
                "crpss_ge_min": bool(np.isfinite(skill) and skill >= CRPSS_MIN),
                "mean_crps_diff_dressed_minus_anen": float(np.mean(d)) if n_days else None,
                "bootstrap_p": float(p_boot),
                "anen_reproduction": repro,
                "diagnostics": diagnostics,
            })
            print(f"[c11c] {sym} {w_label}: n={n_days} CRPSS_dressed="
                  f"{skill if np.isfinite(skill) else float('nan'):.4f} "
                  f"p={p_boot:.4f} repro={'ok' if repro['matches'] else 'MISMATCH'}",
                  file=sys.stderr, flush=True)

    p_values = [c["bootstrap_p"] for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for c, rej in zip(cells, rejected):
        c["fdr_significant"] = bool(rej)
        c["boot_p_le_max"] = bool(c["bootstrap_p"] <= BOOTSTRAP_P_MAX)
        c["cell_pass"] = bool(c["crpss_ge_min"] and c["boot_p_le_max"]
                              and c["fdr_significant"])

    rollup: list[dict[str, Any]] = []
    for sym in symbols:
        sym_cells = [c for c in cells if c["symbol"] == sym]
        rollup.append({
            "symbol": sym,
            "windows_measured": len(sym_cells),
            "windows_pass": sum(1 for c in sym_cells if c["cell_pass"]),
            "both_windows_pass": bool(sym_cells
                                      and all(c["cell_pass"] for c in sym_cells)
                                      and len(sym_cells) >= 2),
        })
    repro_ok = all(c["anen_reproduction"]["matches"] for c in cells) if cells else False
    gate_valid = bool(cells) and (repro_ok or skip_repro_check)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "data_gated": True,
        "status": "RUN",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "unlock_check": unlock,
        "windows": {"tune_L": list(tune_range), "W1": list(w1_range),
                    "W2": list(w2_range)},
        "method": {
            "k_analogs": int(k),
            "embargo_days": int(embargo),
            "weights_frozen": {s: list(map(float, w)) for s, w in weights_map.items()},
            "re_tuning": "NONE (registry H-11c: weights frozen from the GL-022 run)",
            "target_horizon_days": TARGET_HORIZON_DAYS,
            "baseline": ("HAR-RV point forecast UNCHANGED, dressed with a k-member "
                         "quantile sample of the empirical IN-FIT residuals of the "
                         "same monthly refit (plotting positions (j-0.5)/k, "
                         "mean-centred); no look-ahead, no distributional "
                         "assumption, no RNG"),
            "crps": ("BOTH sides scored with the SAME registered ensemble CRPS "
                     "(1/k)sum|x_i-y| - (1/(2k^2))sum sum|x_i-x_j|"),
            "block_len_days": int(block_len),
            "n_bootstrap": int(n_bootstrap),
            "seed": int(seed),
        },
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "fdr_p_crit": float(p_crit),
        "n_fdr_significant": int(sum(rejected)),
        "gate_thresholds": {"crpss_min": CRPSS_MIN,
                            "bootstrap_p_max": BOOTSTRAP_P_MAX},
        "anen_side_reproduces_gl022": bool(repro_ok),
        "materiality_rtol": MATERIALITY_RTOL,
        "panel_fingerprints": fingerprints,
        "gate_valid": gate_valid,
        "cells": cells,
        "any_symbol_both_windows_pass": bool(any(r["both_windows_pass"] for r in rollup)),
        "per_symbol_rollup": rollup,
    }


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------

def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# H-11c — AnEn gegen dispersions-gematchte HAR (Dressed-HAR), KAPITALFREI")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}` "
             f"(Folge-Auflage aus GL-022)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC) · Status: {payload['status']}")
    if payload["status"] == "SKIP":
        L.append("")
        L.append(f"> **SKIP:** {payload['reason']}")
        return "\n".join(L)
    m = payload["method"]
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    L.append(f"- **Gewichte (eingefroren, KEIN Re-Tuning):** "
             + " · ".join(f"{s}={w}" for s, w in m["weights_frozen"].items()))
    L.append(f"- **Baseline:** {m['baseline']}")
    L.append(f"- **Bewertung:** {m['crps']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} · BH-FDR alpha={payload['fdr_alpha']} "
             f"· p_crit={payload['fdr_p_crit']:.6f}")
    L.append(f"- **AnEn-Seite reproduziert GL-022:** "
             f"{'JA' if payload['anen_side_reproduces_gl022'] else '**NEIN — Lauf ungueltig**'} "
             f"· `gate_valid={str(payload['gate_valid']).lower()}`")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-11c. WEITER verlangt: fuer >=1 "
             "Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS_dressed>=0.05 UND Bootstrap-p<=0.05 "
             "nach BH-FDR alpha=0.10 ueber F-ANEN-C. Hartes Ein-Fenster-DROP, kein "
             "GRAUBEREICH, keine Nachsuche. A-priori: DROP erwartet.")
    L.append("")
    L.append("## Zellen (F-ANEN-C: Symbol x Fenster)")
    L.append("")
    L.append("| Symbol | Fenster | n | CRPS AnEn | CRPS Dressed-HAR | **CRPSS_dressed** | >=0.05 | boot-p | FDR-sig | Zelle | (CRPSS alte Dirac-Regel) |")
    L.append("|---|---|---:|---:|---:|---:|:---:|---:|:---:|:---:|---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['symbol']} | {c['window']} | {c['n_forecast_days']} | "
            f"{_fmt(c['mean_crps_anen'])} | {_fmt(c['mean_crps_dressed_har'])} | "
            f"**{_fmt(c['crpss'])}** | {'ja' if c['crpss_ge_min'] else 'nein'} | "
            f"{c['bootstrap_p']:.4f} | {'ja' if c['fdr_significant'] else 'nein'} | "
            f"{'PASS' if c['cell_pass'] else 'nein'} | "
            f"{_fmt(c['crpss_vs_point_gl022_rule'])} |")
    L.append("")
    L.append("## Kontinuitaets-Nachweis der AnEn-Seite (Vorbedingung)")
    L.append("")
    L.append(f"*Materialitaets-Schranke {payload['materiality_rtol']:.0e} (registry H-11c "
             "Nachtrag 2 / DEC-32) — aus der GATE-ARITHMETIK hergeleitet, nicht aus einer "
             "Beobachtung: eine relative Stoerung eps auf den CRPS-Summen bewegt den CRPSS "
             "um hoechstens ~2*eps, also <=2e-4 bei eps<=1e-4 — das 250-Fache unter der "
             "0,05-Schwelle. KEINE Bit-Identitaet: der Harvest-Speicher ist LIVE und darf "
             "historische Partitionen neu schreiben.*")
    L.append("")
    L.append("| Symbol | Fenster | Summe CRPS AnEn (GL-022) | beobachtet | rel. Abw. | H-11-CRPSS (GL-022) | beobachtet | rel. Abw. | im Rahmen |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|:---:|")
    for c in payload["cells"]:
        r = c["anen_reproduction"]
        rd = "—" if r["rel_diff"] is None else f"{r['rel_diff']:.2e}"
        rs = ("—" if r["rel_diff_crpss_point_rule"] is None
              else f"{r['rel_diff_crpss_point_rule']:.2e}")
        L.append(f"| {c['symbol']} | {c['window']} | {_fmt6(r['reference'])} | "
                 f"{_fmt6(r['observed'])} | {rd} | "
                 f"{_fmt6(r['reference_crpss_point_rule'])} | "
                 f"{_fmt6(r['observed_crpss_point_rule'])} | {rs} | "
                 f"{'JA' if r['matches'] else 'NEIN'} |")
    L.append("")
    L.append("### Panel-Fingerabdruck (forensisch, nicht urteilstragend)")
    L.append("")
    L.append("*SHA-256 ueber die exakten Float-Bytes des Tagespanels. Weicht er zwischen "
             "zwei Laeufen ab, hat sich der Harvest-Schnappschuss bewegt — die Frage, die "
             "nach dem 2026-08-12-Lauf offenblieb, ist damit kuenftig beantwortbar.*")
    L.append("")
    L.append("| Symbol | Tage | von | bis | sha256(rv_daily) | sha256(funding_daily) |")
    L.append("|---|---:|---|---|---|---|")
    for sym, fp in payload.get("panel_fingerprints", {}).items():
        L.append(f"| {sym} | {fp['n_days']} | {fp['first_day']} | {fp['last_day']} | "
                 f"`{fp['sha256_rv_daily'][:16]}…` | `{fp['sha256_funding_daily'][:16]}…` |")
    L.append("")
    L.append("## Pflicht-Diagnostik (NICHT urteilstragend)")
    L.append("")
    L.append("*Registriert als nicht-urteilstragend, damit sie ehrlich berichtet werden muss, "
             "ohne das Gate bewegen zu koennen. (a) schliesst die in GL-022 offengelegte "
             "Funktional-Luecke: MAE wird vom MEDIAN minimiert, nicht vom Mittel.*")
    L.append("")
    L.append("| Symbol | Fenster | MAE AnEn-Median | MAE HAR-Punkt | Diff (HAR-Median) | 2-seitig p | Disp.-Ratio AnEn | Disp.-Ratio Dressed | PIT chi2 AnEn (p) | PIT chi2 Dressed (p) |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for c in payload["cells"]:
        d = c["diagnostics"]
        if "mae_ensemble_median" not in d:
            continue
        L.append(
            f"| {c['symbol']} | {c['window']} | {_fmt(d['mae_ensemble_median'])} | "
            f"{_fmt(d['mae_har_point'])} | {d['mae_diff_har_minus_median']:+.5f} | "
            f"{d['mae_diff_two_sided_boot_p']:.4f} | "
            f"{_fmt(d['dispersion_ratio_anen'])} | {_fmt(d['dispersion_ratio_dressed'])} | "
            f"{d['pit_chi2_anen']:.2f} ({d['pit_chi2_p_anen']:.4f}) | "
            f"{d['pit_chi2_dressed']:.2f} ({d['pit_chi2_p_dressed']:.4f}) |")
    L.append("")
    L.append("## Symbol-Rollup (Gate-Kern, gate-neutral)")
    L.append("")
    L.append("| Symbol | Fenster gemessen | Fenster PASS | BEIDE Fenster PASS |")
    L.append("|---|---:|---:|:---:|")
    for r in payload["per_symbol_rollup"]:
        L.append(f"| {r['symbol']} | {r['windows_measured']} | {r['windows_pass']} | "
                 f"{'JA' if r['both_windows_pass'] else 'nein'} |")
    L.append("")
    L.append(f"**Mindestens ein Symbol mit beiden Fenstern PASS:** "
             f"{'ja' if payload['any_symbol_both_windows_pass'] else 'nein'}")
    L.append("")
    L.append("*Erzeugt von `c11_anen/driver_c.py` (read-only Harvester-Baum). "
             "capital_free=true — die 25-75x-Friktionsnotiz aus H-11 bleibt nach GL-022 E5 "
             "ENTKOPPELT. Endgueltiges Gate-Urteil: gate-auditor gegen H-11c.*")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    return "—" if v is None else f"{float(v):.4f}"


def _fmt6(v: Any) -> str:
    return "—" if v is None else f"{float(v):.6f}"


__all__ = [
    "FDR_FAMILY",
    "FROZEN_WEIGHTS",
    "GL022_SUM_CRPS_ANEN",
    "HYPOTHESIS_ID",
    "render_markdown",
    "run",
]
