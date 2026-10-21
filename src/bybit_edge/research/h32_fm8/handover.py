"""Hand-over rule U (ERSTFASSUNG 1.8, DEC-99 (6), DEC-94): pure, mechanical, fixed in advance.

For every variant ``v`` the pilot result and the frozen v6 constants give

    SE_W,Pilot = sqrt(c_real) * sqrt(v_fm8_W + F2_real) / sqrt(w_judged_W)         W in {W1, W2}
    SE_T,W     = max(e_se_rule_W,v, SE_W,Pilot)          (threshold SE)
    SD_T,W     = max(se_mean_W,v,   SE_W,Pilot)          (spread)
    m*         = max(0, m_P,v, null_mean_W1,v, null_mean_W2,v)                      (in direction)
    MDE80*_v   = max_W (z_krit * SE_T,W + 0.8416 * SD_T,W)

The variant is HANDED OVER iff (i) ``x_P > 0``, (ii) ``x_P - m* >= MDE80*_v`` and (iii) ``t_P >= 2.0``.  Prior of the
assignment ``pi_v = x_P`` (reading A); regime ``power_p1.assign_regime`` with the null-mean credit per window, double
statement ``power_p1.assign_regime_a3_practice``; mandatory double statement ``mu_sel`` and the joint power at it.
DEC-101 E6: if the root lies at the bracket edge ``x_P - 40 SE_P`` there is no solution -- ``mu_sel`` is ``None``,
``mu_sel_solved`` False and the note reads "keine Loesung (Platzhalter, report-only)".

``evaluate_handover`` is a pure function of ``(inputs, consts)``: the same payload gives the identical dict (T4), and the
test run re-derives the hand-over from the pilot JSON with it, bit for bit (P0').
"""
from __future__ import annotations

import math
from typing import Any

from .. import power_p1
from . import constants as C
from . import estimators as est

__all__ = ["evaluate_handover", "handover_constants", "se_t_sd_t"]

WINDOW_NAMES = ("W1", "W2")


def se_t_sd_t(consts: dict[str, Any], inputs: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Per window ``SE_W,Pilot``, ``SE_T,W``, ``SD_T,W`` and the frozen null mean (rule U, first three lines)."""
    out: dict[str, dict[str, float]] = {}
    for wn in WINDOW_NAMES:
        w = consts["windows"][wn]
        se_pilot = math.sqrt(inputs["c_real"]) * math.sqrt(w["v_fm8"] + inputs["f2_real"]) / math.sqrt(w["w_judged"])
        out[wn] = {"se_w_pilot": se_pilot, "se_t": max(w["e_se_rule"], se_pilot), "sd_t": max(w["se_mean"], se_pilot),
                   "null_mean": w["null_mean"], "w_judged": w["w_judged"], "q95": float(w["q95"])}
    return out


def handover_constants(registered: dict[str, Any], variant: str) -> dict[str, Any]:
    """The constants rule U reads from the registered YAML for ``variant``."""
    wins = {}
    for wn in WINDOW_NAMES:
        w = registered["windows"][wn]
        fz = w["frozen_v6"]
        wins[wn] = {"v_fm8": float(fz["v_fm8"]), "e_se_rule": float(fz["e_se_rule"][variant]),
                    "se_mean": float(fz["se_mean"][variant]), "null_mean": float(fz["null_mean"][variant]),
                    "q95": float(fz["q95"][variant]), "w_judged": int(w["w_judged"])}
    return {"windows": wins, "m_p": float(registered["pilot_window"]["frozen_v6"]["m_P"][variant]),
            "z_krit": float(C.Z_KRIT), "z_power": float(C.Z_POWER), "t_min": float(registered["handover_rule"]["t_min"])}


def evaluate_handover(inputs: dict[str, Any], consts: dict[str, Any]) -> dict[str, Any]:
    """Rule U (version U-3, DEC-101 Teil 2) for one variant.  ``inputs``: ``x_p``, ``se_p``, ``f2_real``, ``c_real``;
    ``consts`` as in :func:`handover_constants`.  Condition (ii): ``x_P >= max(m* + max_W(z_krit SE_T,W + z_80 SD_T,W),
    max_W(q95_W,v + z_80 SD_T,W))`` -- the MDE80 of both gate conditions (1b with credit, 1c).  Pure."""
    x_p, se_p = float(inputs["x_p"]), float(inputs["se_p"])
    t_p = x_p / se_p
    z, zp = float(consts["z_krit"]), float(consts["z_power"])
    per_w = se_t_sd_t(consts, inputs)
    nm = {wn: per_w[wn]["null_mean"] for wn in WINDOW_NAMES}
    m_star = max(0.0, float(consts["m_p"]), *nm.values())
    comp = {wn: z * per_w[wn]["se_t"] + zp * per_w[wn]["sd_t"] for wn in WINDOW_NAMES}
    mde80_star = max(comp.values())
    threshold_u = mde80_star + m_star
    # DEC-101 Teil 2 (U-3, Review A-4): condition (ii) also covers gate condition (1c) -- MDE80 of (1c) = frozen q95 + z_80 SD_T;
    # the threshold on the pilot point is the maximum of both (it can only rise; strictness, fixed before any pilot number).
    comp_1c = {wn: per_w[wn]["q95"] + zp * per_w[wn]["sd_t"] for wn in WINDOW_NAMES}
    threshold_1c = max(comp_1c.values())
    c_v = max(threshold_u, threshold_1c)
    cond_i = bool(x_p > 0.0)
    cond_ii = bool(x_p >= c_v)
    cond_iii = bool(t_p >= float(consts["t_min"]))
    handed = cond_i and cond_ii and cond_iii

    ses = [per_w[wn]["se_t"] for wn in WINDOW_NAMES]
    sds = [per_w[wn]["sd_t"] for wn in WINDOW_NAMES]
    priors = [x_p - max(0.0, nm[wn]) for wn in WINDOW_NAMES]
    regime_p1 = power_p1.assign_regime(priors, ses, sds=sds)
    regime_a3 = power_p1.assign_regime_a3_practice(priors, ses, sds)
    out: dict[str, Any] = {
        "x_p": x_p, "se_p": se_p, "t_p": t_p, "f2_real": float(inputs["f2_real"]), "c_real": float(inputs["c_real"]),
        "per_window": per_w, "m_p": float(consts["m_p"]), "m_star": m_star, "mde80_star_components": comp,
        "mde80_star": mde80_star, "threshold_u": threshold_u, "threshold_1c_components": comp_1c, "threshold_1c": threshold_1c,
        "threshold_on_point": c_v, "threshold_binding": "1c" if threshold_1c > threshold_u else "U",
        "rule_version": C.HANDOVER_VERSION,
        "conditions": {"i": cond_i, "ii": cond_ii, "iii": cond_iii}, "handed_over": handed,
        "pi_v": x_p, "regime_p1": regime_p1, "regime_a3_practice": regime_a3,
        "regime_p1_consistent": (regime_p1["regime"] == power_p1.REGIME_C10) if cond_ii else None,
        "label_only_dec94": regime_a3["label"] if regime_a3.get("zugelassen_nur_durch_dec94") else None,
        "mu_sel": None, "mu_sel_solved": None, "mu_sel_note": None, "power_at_mu_sel": None,
    }
    if handed:
        det = est.mu_sel_detail(x_p, se_p, c_v)
        mu = det["mu_sel"]
        out["mu_sel"] = mu
        # DEC-101 E6 (B-9.5): at the bracket edge there is no solution -- a placeholder, report-only, never an estimate
        out["mu_sel_solved"] = det["solved"]
        out["mu_sel_note"] = det["note"]
        if mu is not None:
            pri_sel = [mu - max(0.0, nm[wn]) for wn in WINDOW_NAMES]
            r_sel = power_p1.assign_regime(pri_sel, ses, sds=sds)
            r_sel_a3 = power_p1.assign_regime_a3_practice(pri_sel, ses, sds)
            out["power_at_mu_sel"] = {"window_power": dict(zip(WINDOW_NAMES, r_sel["window_power"])),
                                      "joint": r_sel["window_power_joint_product"], "regime_p1": r_sel["regime"],
                                      "regime_a3_practice": r_sel_a3["regime"],
                                      "window_power_a3_practice": dict(zip(WINDOW_NAMES, r_sel_a3["window_power"])),
                                      "note": "Pflicht-Doppelausweis (DEC-99 (3)), keine Entscheidungswirkung"}
    out["status"] = C.PILOT_HANDED if handed else C.PILOT_GL012
    out["reason"] = None if handed else _reason(out)
    return out


def _reason(h: dict[str, Any]) -> str:
    miss = [k for k, v in h["conditions"].items() if not v]
    return ("GL-012 (Pilot): verfehlte Bedingung(en) " + ",".join(f"({k})" for k in miss)
            + f"; x_P={h['x_p']:.6f}, SE_P={h['se_p']:.6f}, t_P={h['t_p']:.3f}, MDE80*={h['mde80_star']:.6f}, "
              f"m*={h['m_star']:.6f}")
