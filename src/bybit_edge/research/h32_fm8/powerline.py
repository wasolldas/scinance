"""DEC-101 E5 (A-4, Review B-4, B-6): the power line of the Vorlauf artifact (``power_line``, report-only).

Per window W and variant v, from the frozen v6 constants only (outcome-free; before the pilot the threshold SE is
``e_se_rule`` and the spread ``se_mean``, i.e. rule U with ``SE_W,Pilot`` not yet known):

  * ``MDE80_1b = z_krit * e_se_rule + z_80 * se_mean + max(0, null_mean)``     (condition (1b) with the null-mean credit)
  * ``MDE80_1c = q95 + z_80 * se_mean``                                         (condition (1c))
  * ``MDE80_W  = max(MDE80_1b, MDE80_1c)``;  ``MDE80* = max_W MDE80_W``          (DEC-94 (3): max over the conditions)
  * ``m* = max(0, m_P, null_mean_W1, null_mean_W2)`` (rule U), ``MDE80*_U = max_W(z_krit * SE_T + z_80 * SD_T)`` (rule U
    unchanged) and the hand-over threshold on the pilot point ``x_P``:  ``c_v = MDE80*_U + m*``;
  * the proof line "rule U covers (1c)":  ``margin = c_v - max_W MDE80_1c`` (``>= 0``: yes / no), next to the margin against
    the full gate MDE80* ;
  * the end power after F-WEEK for ``m`` in {1, 2, 3, 4, 11} at the point ``pi = c_v``:
    ``prod_W P(Y >= max(z_eff SE_T + max(0, null_mean_W), q_{1-bound}(replicates of the binding cell), q95_W))``,
    ``Y ~ N(pi, SD_T^2)``, ``bound = alpha_BY / (m H_m)``, ``z_eff = max(z_krit, Phi^-1(1 - bound))``
    (:func:`estimators.end_power_replicates`; ``power_p1.Z_POWER``, never a rounded 0.8416).  The normal approximation of the
    old ``end_power`` is stated next to it, labelled as such.

Pure: numbers (and the replicate arrays) in, a JSON-serialisable dict out.  Display only -- never an assignment basis (the
assignment is rule U at the pilot).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from . import constants as C
from . import estimators as est

__all__ = ["build_power_line", "POWER_LINE_LABEL"]

POWER_LINE_LABEL = ("report-only (DEC-101 E5): MDE80 as the maximum over (1b) with credit and (1c); hand-over threshold on x_P = "
                    "MDE80*_U + m*; proof line 'rule U covers (1c)'; end power after F-WEEK from the replicates of the binding "
                    "cell (not the normal approximation) at pi = hand-over threshold")


def build_power_line(frozen: dict[str, dict[str, Any]], m_p: dict[str, float], draws: dict[str, dict[str, Any]], *,
                     m_grid: tuple[int, ...] = C.POWER_M_GRID) -> dict[str, Any]:
    """``frozen[W]`` = the ``frozen_v6`` block of window W (``se_mean``, ``e_se_rule``, ``null_mean``, ``q95`` per variant),
    ``m_p[v]`` the pilot-period null mean, ``draws[W][v]`` the p replicates of the binding cell (registered direction)."""
    z, zp = float(C.Z_KRIT), float(C.Z_POWER)
    wnames = list(frozen)
    out_v: dict[str, Any] = {}
    for v in C.VARIANTS:
        per_w: dict[str, Any] = {}
        for wn in wnames:
            fz = frozen[wn]
            se_t, sd_t = float(fz["e_se_rule"][v]), float(fz["se_mean"][v])
            nm, q95 = float(fz["null_mean"][v]), float(fz["q95"][v])
            m1b = z * se_t + zp * sd_t + max(0.0, nm)
            m1c = q95 + zp * sd_t
            per_w[wn] = {"se_t": se_t, "sd_t": sd_t, "null_mean": nm, "q95": q95, "mde80_1b": m1b, "mde80_1c": m1c,
                         "mde80_w": max(m1b, m1c), "binding_condition": "1c" if m1c > m1b else "1b",
                         "rule_u_component": z * se_t + zp * sd_t}
        mde80_star = max(w["mde80_w"] for w in per_w.values())
        mde80_u = max(w["rule_u_component"] for w in per_w.values())
        m_star = max(0.0, float(m_p[v]), *(w["null_mean"] for w in per_w.values()))
        c_v = mde80_u + m_star
        max_1c = max(w["mde80_1c"] for w in per_w.values())
        margin_1c = c_v - max_1c
        windows_in = {wn: {"se_t": per_w[wn]["se_t"], "sd_t": per_w[wn]["sd_t"], "null_mean": per_w[wn]["null_mean"],
                           "q95": per_w[wn]["q95"], "draws": np.asarray(draws[wn][v], dtype=np.float64)} for wn in wnames}
        windows_na = {wn: {k: windows_in[wn][k] for k in ("se_t", "sd_t", "null_mean")} for wn in wnames}
        end_rep: dict[str, Any] = {}
        end_na: dict[str, Any] = {}
        for m in m_grid:
            r = est.end_power_replicates(c_v, m, windows_in)
            end_rep[str(m)] = {"joint": r["joint"], "window_power": r["window_power"], "z_eff": r["z_eff"],
                               "by_threshold_p": r["by_threshold_p"],
                               "binding": {wn: d["binding"] for wn, d in r["window_detail"].items()}}
            na = est.end_power(c_v, m, windows_na)
            end_na[str(m)] = {"joint": na["joint"], "window_power": na["window_power"]}
        out_v[v] = {
            "windows": per_w, "mde80_star": mde80_star, "mde80_star_u": mde80_u, "m_p": float(m_p[v]), "m_star": m_star,
            "handover_threshold_on_point": c_v,
            "rule_u_covers_1c": {"max_w_mde80_1c": max_1c, "margin": margin_1c, "covers": bool(margin_1c >= 0.0),
                                 "line": f"Regel U deckt (1c): Marge = Schwelle_U - max_W MDE80_1c = {margin_1c:.6f} "
                                         f"(>= 0: {'ja' if margin_1c >= 0.0 else 'nein'})"},
            "margin_against_gate_mde80_star": c_v - mde80_star,
            "end_power_after_f_week_replicates": end_rep,
            "end_power_after_f_week_normal_approximation_report_only": end_na,
        }
    return {"label": POWER_LINE_LABEL, "z_krit": z, "z_power": zp, "by_alpha": C.BY_ALPHA, "m_grid": list(m_grid),
            "pi": "hand-over threshold on x_P (c_v)", "variants": out_v}
