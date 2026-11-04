"""Assembly of the feasibility report (DEC-104 E8, DEC-105): JSON and Markdown, deterministic.

``evaluate`` returns one dictionary with the mandatory rows:

1. ``rules``       MDE80 per decision rule R1..R6 (central and stress line, with c), alpha_eff, power at MDE, structural
                   floor, required data and earliest decision date at the SESOI, data factors against R1.
2. ``exploration`` / ``confirmation``  zone X (resolution, exclusion limit) against zone V (one look) and zone K
                   (prospective, from the cohort date), per rule.
3. ``sr_equivalent`` needed SR_eff = MDE/SE_12 for 1 / 2 / 3 years per window (C.10) and the 3.1 counterparts.
4. ``conjunction`` product / exact pair / exact joint MDE80 per placebo-set variant (double statement, DEC-105 (7)).
5. ``strictness``  strictness quotient with decomposition per commitment (chains) and rule-level (stress, gate).
6. ``oc``          P(PASS) at effect 0 / SESOI / prior points, analytic and Monte Carlo, per rule.
7. ``verdict``     binary per rule: testable (with date) / structurally not testable / exploration only.
8. ``reporting_rows``  the mandatory DEC-105 row: estimate placeholder, se, ci95, upper_limit95, n_eff, c_overlap,
                   selection_k, shrinkage_note, zone.

Also: ``design_menu`` (window lengths 6/9/12 months, looks 1..4), ``heavy_tail`` (t-limit sensitivity, first-look cluster
count), ``pilot_handover``, ``prior`` (SR_eff and C.10 window days at the prior points), ``warnings``.

Scope note: the rule rows evaluate the PRIMARY statistic with its SE (central and stress line) and the gate factor.  A
conjunction of several conditions (A2: placebo conditions, null condition) is reported separately in ``conjunction`` and
``strictness.chains``; ``conjunction.inflation_vs_primary`` quantifies what the rule rows leave out.

Everything is computed from the candidate file; nothing is read from data.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
from typing import Any

import numpy as np
from scipy.stats import norm

from . import SCHEMA_VERSION, __version__
from . import conjunction as cj
from . import rules as R
from .schema import (KNOWLEDGE_CLASSES, Candidate, Chain, FeasibilityInputError, Expected)
from .sesoi import resolve_sesoi

__all__ = ["evaluate", "to_json", "to_markdown", "compare_expected", "get_path", "T_REF_MONTHS", "add_months"]

T_REF_MONTHS = 24.0                      # two 12-month windows: the C.10 reference amount of data
T_GRID_BASE = (12.0, 18.0, 24.0, 36.0, 48.0, 60.0)
STRICTNESS_USER_THRESHOLD = 1.3          # DEC-104 E8 (b): from here a user template before registration
SEED_OC = 31010                          # fixed base seed of the OC Monte Carlo
DEC96_WINDOW_LIMIT_MONTHS = 12.0         # DEC-96 E2: a C.10 window is at most 12 months
OC_T_CAP_MONTHS = 1200.0


def POWER_OK(gate: float) -> bool:
    """True if the gate leaves power 0.80 reachable (target / gate < 1)."""
    return R.POWER / gate < 1.0


# ------------------------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------------------------
def add_months(d: _dt.date, months: int) -> _dt.date:
    tot = d.year * 12 + (d.month - 1) + int(months)
    return _dt.date(tot // 12, tot % 12 + 1, 1)


def _months_between(a: _dt.date, b: _dt.date) -> float:
    return max(0.0, ((b - a).days) / 30.4375)


def _fin(x: float | None) -> float | None:
    return x if x is not None and math.isfinite(x) else None


def _tkey(t: float) -> str:
    return str(int(round(t))) if abs(t - round(t)) < 1e-9 else f"{t:g}"


def _clean(x: Any) -> Any:
    """Recursively make JSON-safe: numpy -> python, inf/nan -> None, dates -> ISO, 10 significant digits."""
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return float(f"{v:.10g}") if math.isfinite(v) else None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, (_dt.date, _dt.datetime)):
        return x.isoformat()
    return x


def _lines(c: Candidate) -> tuple[str, ...]:
    return c.nuisance.lines()


def _tgrid(c: Candidate, extra: tuple[float, ...] = ()) -> list[float]:
    ts = set(T_GRID_BASE) | {2.0 * w for w in c.design_menu.window_months} | set(extra)
    return sorted(ts)


# ------------------------------------------------------------------------------------------------------------------
# conjunction models
# ------------------------------------------------------------------------------------------------------------------
def _spec(conj: dict, window: str, line: str, scaled: bool, active: list[str], gate: float) -> cj.ConjunctionSpec:
    w = conj["windows"][window]

    def pick(d: dict) -> float:
        if line not in d:
            raise FeasibilityInputError(f"conjunction window {window}: nuisance line {line!r} missing")
        return d[line].value

    conds = {n: {"n": p["n"], "c": p["c"], "sd": pick(p["sd"]), "se": pick(p["se"])} for n, p in w["conditions"].items()}
    ev = {"n": w["event"]["n"], "c": w["event"]["c"], "sd": pick(w["event"]["sd"])}
    nl = None
    if w["null_test"] is not None:
        nl = {"sd": pick(w["null_test"]["sd"]), "d95": pick(w["null_test"]["d95"]), "centre_sd": pick(w["null_test"]["centre_sd"])}
    if "null_test" in active and nl is None:
        raise FeasibilityInputError(f"conjunction window {window}: condition 'null' requested but no null block")
    return cj.shared_term_spec(event=ev, conditions=conds, null=nl, kappa=w["kappa"], tau95=conj["tau95"],
                               z_alpha=conj["z_alpha"], scaled_null=scaled, active=active, gate=gate)


def _conj_lines(conj: dict) -> list[str]:
    out = []
    for ln in ("central", "stress"):
        ok = True
        for w in conj["windows"].values():
            parts = [w["event"]["sd"]] + [p[k] for p in w["conditions"].values() for k in ("sd", "se")]
            if w["null_test"] is not None:
                parts += list(w["null_test"].values())
            ok = ok and all(ln in d for d in parts)
        if ok:
            out.append(ln)
    return out


def _conjunction_block(c: Candidate, mc_n: int) -> dict | None:
    conj = c.conjunction
    if conj is None:
        return None
    variants = dict(c.design_menu.placebo_set_variants)
    first = next(iter(conj["windows"].values()))
    if not variants:
        variants = {"all": tuple(first["conditions"]) + (("null_test",) if first["null_test"] is not None else ())}
    gate = c.gate_factor
    out: dict[str, Any] = {"pair": list(conj["pair"]) if conj["pair"] else None, "tau95": conj["tau95"],
                           "gate_factor": gate, "mc_draws": mc_n, "mc_seed": cj.MC_SEED, "variants": {}, "se_by_window": {}}
    lines = _conj_lines(conj)
    for win, wd_ in conj["windows"].items():
        out["se_by_window"][win] = {ln: {cn: cp["se"][ln].value for cn, cp in wd_["conditions"].items()} for ln in lines}
    for vname, active in variants.items():
        has_null = "null_test" in active
        v: dict[str, Any] = {"conditions": list(active)}
        for win in conj["windows"]:
            if has_null and conj["windows"][win]["null_test"] is None:
                continue
            wd: dict[str, Any] = {}
            for ln in lines:
                ld: dict[str, Any] = {}
                for scaled in ((False, True) if has_null else (False,)):
                    sd: dict[str, Any] = {}
                    spec = _spec(conj, win, ln, scaled, list(active), 1.0)
                    pair = conj["pair"] if (conj["pair"] and all(p in active for p in conj["pair"])) else None
                    sd["product"] = spec.mde80("product", None, n=mc_n)
                    sd["pair"] = spec.mde80("pair", pair, n=mc_n) if pair else None
                    sd["joint"] = spec.mde80("joint", None, n=mc_n)
                    if gate < 1.0:
                        specg = _spec(conj, win, ln, scaled, list(active), gate)
                        sd["with_gate"] = {"product": specg.mde80("product", None, n=mc_n),
                                           "pair": specg.mde80("pair", pair, n=mc_n) if pair else None,
                                           "joint": specg.mde80("joint", None, n=mc_n)}
                    sd["exact_to_product_ratio"] = {"pair": (sd["pair"] / sd["product"]) if sd["pair"] else None,
                                                    "joint": sd["joint"] / sd["product"]}
                    ld["scaled" if scaled else "unscaled"] = sd
                wd[ln] = ld
            v[win] = wd
        out["variants"][vname] = v
    ref = conj["reference_window"]
    prim = next(iter(first["conditions"]))
    big = max(variants, key=lambda k: len(variants[k]))
    infl: dict[str, Any] = {}
    for ln in lines:
        entry = out["variants"][big].get(ref, {}).get(ln, {}).get("unscaled")
        if entry is None:
            continue
        base = _spec(conj, ref, ln, False, [prim], 1.0).mde80("product", None, n=mc_n)
        infl[ln] = {"variant": big, "reference_window": ref, "primary_only_mde80": base, "product": entry["product"] / base,
                    "pair": (entry["pair"] / base) if entry["pair"] else None, "joint": entry["joint"] / base}
    out["inflation_vs_primary"] = infl
    return out


# ------------------------------------------------------------------------------------------------------------------
# chains and strictness
# ------------------------------------------------------------------------------------------------------------------
def _chain_block(c: Candidate, ch: Chain, mc_n: int) -> dict:
    rows: list[dict] = []
    if ch.kind == "computed":
        conj = c.conjunction
        win = ch.reference_window or conj["reference_window"]
        if win not in conj["windows"]:
            raise FeasibilityInputError(f"chain {ch.id}: unknown reference window {win!r}")
        for s in ch.steps:
            active = list(s.conditions) if s.conditions else [next(iter(conj["windows"][win]["conditions"]))]
            spec = _spec(conj, win, s.line, s.null_scaled, active, s.gate)
            pair = conj["pair"] if (conj["pair"] and all(p in active for p in conj["pair"])) else None
            mde = spec.mde80(s.mode, pair, n=mc_n)
            rows.append({"id": s.id, "label": s.label, "mde80": mde, "source": "computed", "mode": s.mode, "line": s.line,
                         "conditions": active, "null_scaled": s.null_scaled, "gate": s.gate})
    else:
        for s in ch.steps:
            rows.append({"id": s.id, "label": s.label, "mde80": s.mde80, "source": s.source.as_dict() if s.source else None,
                         "mode": "declared"})
    base_idx = 0
    if ch.base_step is not None:
        base_idx = [r["id"] for r in rows].index(ch.base_step)
    base = rows[base_idx]["mde80"]
    prev = None
    steps: dict[str, Any] = {}
    for i, r in enumerate(rows):
        if i < base_idx:
            r["factor_vs_previous"] = None
            r["increment"] = None
            r["cumulative_quotient"] = None
        else:
            r["factor_vs_previous"] = (r["mde80"] / prev) if prev else None
            r["increment"] = (r["mde80"] - prev) if prev else None
            r["cumulative_quotient"] = r["mde80"] / base
            prev = r["mde80"]
        steps[r["id"]] = r
    final = rows[-1]["mde80"]
    q = final / base
    return {"label": ch.label, "kind": ch.kind, "reference_window": ch.reference_window, "base_step": rows[base_idx]["id"],
            "steps": steps, "base_mde80": base, "final_mde80": final, "quotient": q,
            "needs_user_template": bool(q >= STRICTNESS_USER_THRESHOLD)}


def _rule_chain(c: Candidate, rule: R.Rule, t: float, se_c: float, se_s: float | None) -> dict | None:
    """Rule-level chain: base (central, no gate) -> stress -> gate.  ``None`` if the rule reaches no finite MDE."""
    gate = c.gate_factor
    seq: list[tuple[str, float, float]] = [("base_central", se_c, 1.0)]
    if se_s is not None:
        seq.append(("stress_se", se_s, 1.0))
    if gate < 1.0:
        seq.append(("gate_factor", se_s if se_s is not None else se_c, gate))
    out: dict[str, Any] = {}
    prev = None
    base = None
    for sid, se, g in seq:
        d = rule.mde80(t, g)
        if not math.isfinite(d):
            return None
        mde = d * se
        if base is None:
            base = mde
        out[sid] = {"mde80": mde, "factor_vs_previous": (mde / prev) if prev else None,
                    "increment": (mde - prev) if prev else None, "cumulative_quotient": mde / base}
        prev = mde
    q = prev / base
    return {"steps": out, "quotient": q, "needs_user_template": bool(q >= STRICTNESS_USER_THRESHOLD)}


# ------------------------------------------------------------------------------------------------------------------
# main evaluation
# ------------------------------------------------------------------------------------------------------------------
def evaluate(c: Candidate, *, mc_reps: int | None = None, gsd_paths: int | None = None,
             conjunction_mc: int | None = None) -> dict:
    """Full feasibility report for one candidate (deterministic; seeds fixed)."""
    menu_cfg = c.design_menu
    mc_n = menu_cfg.mc_reps if mc_reps is None else int(mc_reps)
    gp = menu_cfg.gsd_paths if gsd_paths is None else int(gsd_paths)
    cm = menu_cfg.conjunction_mc if conjunction_mc is None else int(conjunction_mc)
    if mc_n < 1000 or gp < 1000 or cm < 1000:
        raise FeasibilityInputError("Monte Carlo sizes must be >= 1000")
    gate = c.gate_factor
    lines = _lines(c)
    se = {ln: c.nuisance.se12_of(ln) for ln in lines}
    se_c, se_s = se["central"], se.get("stress")
    ses = resolve_sesoi(c.sesoi)
    sesoi = ses.value
    menu = R.build_menu(menu_cfg.screen_alphas, menu_cfg.looks, gp)
    by_key = {r.key: r for r in menu}
    r1 = by_key["R1"]
    upy = c.nuisance.units_per_year
    warnings: list[str] = []

    # ---- data zones ----------------------------------------------------------------------------------------------
    d = c.data
    kcls = KNOWLEDGE_CLASSES[d.knowledge_class]
    k_eff = d.k_effective_start()
    if k_eff > d.k_start:
        warnings.append(f"zone K start {d.k_start.isoformat()} moved to {k_eff.isoformat()} (first pure K date of knowledge "
                        f"class {d.knowledge_class}, FENSTERREGISTER section 6)")
    v_ok, v_note = d.v_usable()
    months_v = (d.v.units / upy * 12.0) if (d.v is not None and v_ok) else 0.0
    months_x = (d.x.units / upy * 12.0) if d.x is not None else 0.0
    avail_at_cohort = months_v + _months_between(k_eff, d.cohort_date)
    horizon_end = add_months(d.cohort_date, int(round(menu_cfg.horizon_limit_months)))
    if c.prior is not None and c.prior.label == "UNBELEGT":
        warnings.append("prior label UNBELEGT: no prior median is used; prior-dependent rows are evaluated at both ends of the "
                        "sensitivity span (DEC-104 E3 (d)), never at a worst-case default")
    if c.nuisance.c_overlap == 1.0:
        warnings.append("c_overlap = 1.0: no autocorrelation/overlap inflation is applied (check the dossier source)")

    # ---- rules: grid, floor, required data -------------------------------------------------------------------------
    t_grid = _tgrid(c, (months_v,) if months_v >= 6 else ())
    rules_out: dict[str, Any] = {}
    for rule in menu:
        rd: dict[str, Any] = {"label": rule.label, "params": rule.describe()}
        floor_d = rule.floor(gate)
        rd["floor"] = {"central": _fin(floor_d * se_c) if math.isfinite(floor_d) else None,
                       "stress": _fin(floor_d * se_s) if (se_s is not None and math.isfinite(floor_d)) else None,
                       "se12_units": _fin(floor_d), "exists": bool(floor_d > 0.0)}
        bt: dict[str, Any] = {}
        for t in t_grid:
            dd = rule.mde80(t, gate)
            e: dict[str, Any] = {"mde80_se12": _fin(dd), "r": min(1.0, 12.0 / t) if t > 0 else None,
                                 "mde80": {"central": _fin(dd * se_c), "stress": _fin(dd * se_s) if se_s is not None else None}}
            if math.isfinite(dd):
                e["alpha_eff"] = rule.alpha_eff(t, gate)
                e["power_at_mde"] = rule.power(dd, t, gate)
                if rule is not r1:
                    e["data_factor_vs_R1"] = _fin(R.data_factor(rule, r1, t, gate, gate))
                else:
                    e["data_factor_vs_R1"] = 1.0
                e["mde_sq_ratio_vs_R1_at_12m_window"] = (dd / R.C80) ** 2
            e["meets_sesoi"] = {"central": bool(math.isfinite(dd) and dd * se_c <= sesoi),
                                "stress": (bool(math.isfinite(dd) and dd * se_s <= sesoi) if se_s is not None else None)}
            bt[_tkey(t)] = e
        rd["by_T"] = bt
        rd["c_overlap"] = c.nuisance.c_overlap
        if isinstance(rule, R.GroupSequential) and POWER_OK(gate):
            dsg = rule.design(T_REF_MONTHS, gate)
            rd["gsd_design_at_t_ref"] = {**dsg.as_dict(), "t_max_months": T_REF_MONTHS,
                                         "expected_months_h1": T_REF_MONTHS / dsg.r_max * dsg.en_h1,
                                         "expected_months_h0": T_REF_MONTHS / dsg.r_max * dsg.en_h0}
        rules_out[rule.key] = rd

    def required(rule: R.Rule, line: str) -> dict:
        dline = sesoi / se[line]
        t_req = rule.t_required(dline, gate)
        res: dict[str, Any] = {"reachable": bool(math.isfinite(t_req)), "t_required_months": _fin(t_req)}
        if math.isfinite(t_req):
            res["n_units"] = t_req / 12.0 * upy
            res["years"] = t_req / 12.0
            if rule.two_windows:
                res["window_months"] = t_req / 2.0
                res["years_per_window"] = t_req / 24.0
                res["window_units"] = t_req / 24.0 * upy
                res["exceeds_dec96_window_limit"] = bool(t_req / 2.0 > DEC96_WINDOW_LIMIT_MONTHS + 1e-9)
            if isinstance(rule, R.GroupSequential):
                dsg = rule.design(t_req, gate)
                res["expected_months_h1"] = t_req / dsg.r_max * dsg.en_h1
                res["maximum_over_fixed"] = dsg.r_max
            k_needed = max(0.0, t_req - months_v)
            if t_req <= avail_at_cohort + 1e-9:
                dec = d.cohort_date
                res["data_available_at_cohort"] = True
            else:
                dec = max(d.cohort_date, add_months(k_eff, int(math.ceil(k_needed - 1e-9))))
                res["data_available_at_cohort"] = False
            res["k_months_needed"] = k_needed
            res["decision_date"] = dec
            res["within_horizon"] = bool(dec <= horizon_end)
        else:
            res["floor_blocks"] = bool(rule.floor(gate) * se[line] >= sesoi - 1e-12 and rule.floor(gate) > 0.0)
            res["within_horizon"] = False
        return res

    for rule in menu:
        rules_out[rule.key]["at_sesoi"] = {ln: required(rule, ln) for ln in lines}

    # ---- exploration (zone X) --------------------------------------------------------------------------------------
    exploration: dict[str, Any] = {"zone": "X", "available": d.x is not None}
    if d.x is not None:
        se_x = {}
        for ln in lines:
            if ln == "central" and d.x.se is not None:
                se_x[ln] = d.x.se.value
            else:
                se_x[ln] = se[ln] * math.sqrt(12.0 / months_x)
        exploration.update({
            "n_units": d.x.units, "months": months_x, "se": se_x,
            "resolution_mde80": {ln: R.C80 * se_x[ln] for ln in lines},
            "exclusion_limit_if_null": {ln: R.Z_WINDOW * se_x[ln] for ln in lines},
            "resolves_sesoi": {ln: bool(R.C80 * se_x[ln] <= sesoi) for ln in lines},
            "excludes_sesoi_if_null": {ln: bool(R.Z_WINDOW * se_x[ln] <= sesoi) for ln in lines},
            "label": "exploration: never a verdict; ledger entry required (state/KONTO_ZONE_X.md)",
            "se_source": "measured zone SE (zone data)" if d.x.se is not None else "SE_12 scaled by sqrt(12 / months)"})

    # ---- confirmation: zone V (one look) and zone K (prospective) -------------------------------------------------
    conf_v: dict[str, Any] = {"zone": "V", "usable": bool(v_ok), "note": v_note, "months": months_v if v_ok else None,
                              "n_units": (d.v.units if (d.v is not None and v_ok) else None)}
    if v_ok:
        per_rule = {}
        for rule in menu:
            if isinstance(rule, R.GroupSequential):
                per_rule[rule.key] = {"applicable": False, "note": "one look in zone V; see R3 / R4"}
                continue
            dd = rule.mde80(months_v, gate)
            per_rule[rule.key] = {"applicable": True, "mde80": {ln: _fin(dd * se[ln]) for ln in lines},
                                  "testable": {ln: bool(math.isfinite(dd) and dd * se[ln] <= sesoi) for ln in lines},
                                  "power_at_sesoi_central": rule.power(sesoi / se_c, months_v, gate)}
        conf_v["per_rule"] = per_rule
    conf_k: dict[str, Any] = {"zone": "K", "start": d.k_start, "effective_start": k_eff, "cohort_date": d.cohort_date,
                              "months_available_at_cohort": avail_at_cohort, "horizon_end": horizon_end,
                              "reading": "B (DEC-104 Nachtrag 2 (8)): zone V (if usable) plus pure K quarters",
                              "per_rule": {r.key: rules_out[r.key]["at_sesoi"] for r in menu}}
    confirmation = {"V": conf_v, "K": conf_k}

    # ---- prior points -----------------------------------------------------------------------------------------------
    prior_out: dict[str, Any] | None = None
    if c.prior is not None:
        pts = c.prior.points()
        prior_out = {"label": c.prior.label, "note": c.prior.note, "points": {}}
        for name, val in pts.items():
            e: dict[str, Any] = {"effect": val, "sr_eff": val / se_c, "sr_eff_over_sesoi": val / sesoi}
            if val > 0.0:
                dline = val / se_c
                t1 = r1.t_required(dline, gate)
                e["r1"] = {"t_required_months": _fin(t1), "window_years": _fin(t1 / 24.0), "window_days": _fin(t1 / 24.0 * 365.0),
                           "window_units": _fin(t1 / 24.0 * upy)}
                e["t_required_months"] = {r.key: _fin(r.t_required(dline, gate)) for r in menu}
            prior_out["points"][name] = e

    # ---- SR equivalent ---------------------------------------------------------------------------------------------
    sr: dict[str, Any] = {"definition": "SR_eff = effect / SE_12 (effect in units of the SE of one 12-month window)",
                          "candidate": {"sesoi": sesoi / se_c, "prior": {k: v["sr_eff"] for k, v in (prior_out or {"points": {}})["points"].items()}},
                          "needed": {}}
    for L in (1, 2, 3):
        row = {}
        for rule in menu:
            dd = rule.mde80(24.0 * L, gate)
            row[rule.key] = _fin(dd)
        sr["needed"][f"{L}y_per_window"] = row
    sr["c10_check_gate1"] = {f"{L}y": R.sr_eff_needed_c10(L) for L in (1, 2, 3)}

    # ---- conjunction ------------------------------------------------------------------------------------------------
    conj_block = _conjunction_block(c, cm)
    if c.nuisance.condition_correlation is not None:
        rho = c.nuisance.condition_correlation.value
        conj_block = conj_block or {}
        conj_block["two_conditions_power_0_90"] = {
            "rho": rho, "product": cj.product_power_equal(0.90, 2), "exact": cj.exact_joint_power_equal(0.90, rho)}

    if conj_block and conj_block.get("inflation_vs_primary"):
        inf0 = conj_block["inflation_vs_primary"].get("central")
        if inf0:
            warnings.append("rule rows evaluate the primary statistic only; the conjunction '" + inf0["variant"] + "' inflates MDE80 by "
                            f"x{inf0['product']:.3f} (product) / x{inf0['joint']:.3f} (exact joint) on the central line of window "
                            f"{inf0['reference_window']} (conjunction.inflation_vs_primary) - not included in the rule rows")

    # ---- design menu (window lengths) --------------------------------------------------------------------------------
    design_menu_out: dict[str, Any] = {"looks": list(menu_cfg.looks), "window_months": list(menu_cfg.window_months), "by_window": {}}
    for wl in menu_cfg.window_months:
        tt = _tkey(2.0 * wl)
        design_menu_out["by_window"][str(wl)] = {
            "T_months": 2.0 * wl,
            "per_rule": {r.key: {"mde80": rules_out[r.key]["by_T"][tt]["mde80"], "meets_sesoi": rules_out[r.key]["by_T"][tt]["meets_sesoi"]}
                         for r in menu}}

    # ---- heavy tails / small cluster counts (sensitivity, DEC-104 Nachtrag 2 (7)) ----------------------------------------
    heavy: dict[str, Any] = {
        "note": "sensitivity, not a rule: an SE estimated from few clusters needs Student-t critical values; the MDE inflation "
                "factor is noncentral-t power against normal theory (first order for the data factor: factor squared)",
        "min_clusters_first_look": R.MIN_CLUSTERS_FIRST_LOOK, "per_rule": {}}
    for key in ("R1", "R3"):
        req = rules_out[key]["at_sesoi"]["central"]
        t_use = req["t_required_months"] if req["reachable"] else T_REF_MONTHS
        n_total = t_use / 12.0 * upy
        n_test = n_total / 2.0 if key == "R1" else n_total
        tm = R.t_mde_factor(R.ALPHA_WINDOW if key == "R1" else R.ALPHA_POOL, n_test - 1.0, R.POWER, gate)
        tm.update({"t_months": t_use, "n_units_test": n_test, "t_months_is_reference": not req["reachable"],
                   "data_factor_first_order": (tm["factor"] ** 2) if tm["factor"] else None})
        heavy["per_rule"][key] = tm
    for rule in menu:
        if isinstance(rule, R.GroupSequential):
            req = rules_out[rule.key]["at_sesoi"]["central"]
            t_use = req["t_required_months"] if req["reachable"] else T_REF_MONTHS
            first = t_use / 12.0 * upy / rule.looks
            heavy["per_rule"][rule.key] = {"t_months": t_use, "first_look_units": first, "looks": rule.looks,
                                           "meets_min_clusters_first_look": bool(first >= R.MIN_CLUSTERS_FIRST_LOOK)}

    # ---- strictness -------------------------------------------------------------------------------------------------
    strict: dict[str, Any] = {"threshold_user_template": STRICTNESS_USER_THRESHOLD, "chains": {}, "rules": {}}
    for ch in c.chains:
        strict["chains"][ch.id] = _chain_block(c, ch, cm)
    for rule in menu:
        rc = _rule_chain(c, rule, T_REF_MONTHS, se_c, se_s)
        strict["rules"][rule.key] = rc

    # ---- OC ---------------------------------------------------------------------------------------------------------
    oc: dict[str, Any] = {"mc_reps": mc_n, "seed": SEED_OC, "effects_units": ses.unit, "at_t_required": {}, "at_t_ref": {}}
    eff_points: dict[str, float] = {"zero": 0.0, "sesoi": sesoi}
    if c.prior is not None:
        eff_points.update({f"prior_{k}": v for k, v in c.prior.points().items() if k in ("median", "span_low", "span_high")})
    for i_rule, rule in enumerate(menu):
        req = rules_out[rule.key]["at_sesoi"]["central"]
        for set_name, t_oc in (("at_t_required", req["t_required_months"] if req["reachable"] and req["t_required_months"] <= OC_T_CAP_MONTHS
                                else menu_cfg.horizon_limit_months), ("at_t_ref", T_REF_MONTHS)):
            row: dict[str, Any] = {"T_months": t_oc,
                                   "t_is_horizon_cap": bool(set_name == "at_t_required" and not (req["reachable"] and req["t_required_months"] <= OC_T_CAP_MONTHS)),
                                   "effects": {}}
            for i_eff, (en, ev) in enumerate(eff_points.items()):
                dd = ev / se_c
                an = rule.power(dd, t_oc, gate)
                mc = R.simulate_rule(rule, dd, t_oc, gate, mc_n, SEED_OC + 1000 * i_rule + 10 * i_eff + (0 if set_name == "at_t_required" else 7))
                row["effects"][en] = {"effect": ev, "analytic": an, "mc": mc["p"], "mc_se": mc["se"],
                                      "mc_within_4se": bool(abs(mc["p"] - an) <= 4.0 * mc["se"] + 2e-3)}
            e0, e1 = row["effects"]["zero"]["analytic"], row["effects"]["sesoi"]["analytic"]
            row["ppv"] = {"base_rate_10pct": R.ppv(e1, e0, 0.10) if e0 > 0 else None, "base_rate_25pct": R.ppv(e1, e0, 0.25) if e0 > 0 else None}
            row["expected_false_pass_10_null_tests"] = 10.0 * e0
            oc[set_name][rule.key] = row

    # ---- pilot hand-over -------------------------------------------------------------------------------------------
    pilot_out = None
    if c.pilot is not None:
        pilot_out = {"se": c.pilot.se.value, "threshold": c.pilot.threshold.value,
                     "p_handover": {f"{mu:g}".replace(".", "p"): float(norm.sf((c.pilot.threshold.value - mu) / c.pilot.se.value)) for mu in c.pilot.true_effects}}

    # ---- verdict ----------------------------------------------------------------------------------------------------
    verdict: dict[str, Any] = {"rule": "testable if MDE80 <= SESOI is reached in confirmation within the horizon limit; "
                                       "exploration only if zone X resolves the SESOI but confirmation cannot; "
                                       "else structurally not testable",
                               "horizon_limit_months": menu_cfg.horizon_limit_months, "by_rule": {}}
    for rule in menu:
        vr: dict[str, Any] = {}
        for ln in lines:
            req = rules_out[rule.key]["at_sesoi"][ln]
            conf_ok = bool(req["reachable"] and req.get("within_horizon"))
            expl_ok = bool(exploration.get("resolves_sesoi", {}).get(ln, False))
            if conf_ok:
                label = "testbar"
                cons = f"testbar: Entscheidung fruehestens {req['decision_date'].isoformat()}"
            elif expl_ok:
                label = "nur Exploration"
                cons = "nur Exploration: Zone X loest die SESOI auf, Konfirmation im Horizont nicht erreichbar"
            else:
                label = "strukturell nicht testbar"
                if req["reachable"]:
                    cons = (f"strukturell nicht testbar: Datenbedarf {req['years']:.2f} Jahre, Entscheidung "
                            f"{req['decision_date'].isoformat()} jenseits des Horizonts")
                else:
                    cons = ("strukturell nicht testbar: Boden " + (f"{rules_out[rule.key]['floor'][ln]:.6g}" if rules_out[rule.key]['floor'][ln] is not None else "n/a")
                            + f" >= SESOI {sesoi:.6g}" if req.get("floor_blocks") else "strukturell nicht testbar: Datenbedarf jenseits der Suchgrenze")
            vr[ln] = {"verdict": label, "consequence": cons}
        verdict["by_rule"][rule.key] = vr
    summary: dict[str, Any] = {}
    for ln in lines:
        by_label: dict[str, list[str]] = {}
        for k, v in verdict["by_rule"].items():
            by_label.setdefault(v[ln]["verdict"], []).append(k)
        summary[ln] = by_label
    verdict["summary_by_label"] = summary
    verdict["note"] = "no rule is the rule until the user decides P-2; the verdict is reported per rule"

    # ---- reporting rows (DEC-105) ----------------------------------------------------------------------------------
    rows: list[dict[str, Any]] = []

    def row(zone: str, rule_key: str | None, n_units: float, se_val: float, note: str) -> dict:
        return {"zone": zone, "rule": rule_key, "estimate": "PLACEHOLDER (filled by the run)", "se": se_val,
                "ci95": "estimate +/- 1.9600 * se", "ci95_halfwidth": norm.isf(0.025) * se_val,
                "upper_limit95": "estimate + 1.6449 * se", "upper_limit95_if_estimate_zero": R.Z_WINDOW * se_val,
                "n_eff": n_units, "n_eff_independent": n_units / c.nuisance.c_overlap, "c_overlap": c.nuisance.c_overlap,
                "selection_k": d.selection_k, "shrinkage_note": note, "unit": ses.unit}

    if d.x is not None:
        rows.append(row("X", None, d.x.units, exploration["se"]["central"],
                        "exploration estimate; conditionally median-unbiased value required if used as prior (DEC-99 (3))"))
    if v_ok:
        rows.append(row("V", None, d.v.units, se_c * math.sqrt(12.0 / months_v), "one registered look; no selection beyond K"))
    for rule in menu:
        req = rules_out[rule.key]["at_sesoi"]["central"]
        t_use = req["t_required_months"] if req["reachable"] else None
        if t_use is None:
            continue
        rows.append(row("K", rule.key, t_use / 12.0 * upy, se_c * math.sqrt(12.0 / t_use), "planned data at power 0.80 for the SESOI"))

    return _clean({
        "schema": f"feasibility31/{SCHEMA_VERSION}", "version": __version__,
        "candidate": {"id": c.candidate_id, "title": c.title, "statistic": {"name": c.statistic.name, "unit": c.statistic.unit,
                                                                        "direction": c.statistic.direction, "test": "one-sided"},
                      "knowledge_class": d.knowledge_class, "cohort_date": d.cohort_date, "selection_k": d.selection_k},
        "inputs": {"se12": se, "c_overlap": c.nuisance.c_overlap, "cluster_unit": c.nuisance.cluster_unit, "units_per_year": upy,
                   "gate_factor": gate, "null_scale_k": {ln: c.nuisance.null_scale_k(ln) for ln in lines},
                   "z_pool": R.Z_POOL, "z_window": R.Z_WINDOW, "c80": R.C80, "mu_fix": R.MU_FIX},
        "sesoi": ses.as_dict(),
        "prior": prior_out,
        "rules": rules_out,
        "exploration": exploration,
        "confirmation": confirmation,
        "design_menu": design_menu_out,
        "heavy_tail": heavy,
        "sr_equivalent": sr,
        "conjunction": conj_block,
        "strictness": strict,
        "oc": oc,
        "pilot_handover": pilot_out,
        "verdict": verdict,
        "reporting_rows": rows,
        "warnings": warnings,
    })


# ------------------------------------------------------------------------------------------------------------------
# JSON, expected values
# ------------------------------------------------------------------------------------------------------------------
def to_json(report: dict) -> str:
    return json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def get_path(report: dict, dotted: str) -> Any:
    """Resolve ``a.b.0.c`` into nested dicts/lists.  Raises ``KeyError`` with the failing prefix."""
    cur: Any = report
    done = []
    for part in dotted.split("."):
        done.append(part)
        if isinstance(cur, dict):
            if part not in cur:
                raise KeyError(".".join(done))
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError) as exc:
                raise KeyError(".".join(done)) from exc
        else:
            raise KeyError(".".join(done))
    return cur


def compare_expected(report: dict, expected: tuple[Expected, ...]) -> list[dict]:
    out = []
    for e in expected:
        try:
            actual = get_path(report, e.key)
        except KeyError as exc:
            out.append({"key": e.key, "expected": e.value, "actual": None, "rel_err": None, "ok": False, "error": f"missing path {exc}"})
            continue
        if actual is None or isinstance(actual, (dict, list, str)):
            out.append({"key": e.key, "expected": e.value, "actual": actual, "rel_err": None, "ok": False, "error": "not a number"})
            continue
        rel = abs(actual - e.value) / abs(e.value) if e.value != 0 else abs(actual)
        out.append({"key": e.key, "expected": e.value, "actual": actual, "rel_err": rel, "ok": bool(rel <= e.rel_tol), "tol": e.rel_tol})
    return out


# ------------------------------------------------------------------------------------------------------------------
# Markdown (German, ASCII)
# ------------------------------------------------------------------------------------------------------------------
def _f(x: Any, nd: int = 4, none: str = "nie") -> str:
    if x is None:
        return none
    if isinstance(x, bool):
        return "ja" if x else "nein"
    if isinstance(x, (int, float)):
        if x != 0 and (abs(x) < 10 ** (-nd) or abs(x) >= 1e6):
            return f"{x:.3g}"
        txt = f"{x:.{nd}f}" if abs(x) < 1000 else f"{x:.1f}"
        return txt.rstrip("0").rstrip(".") if "." in txt else txt
    return str(x)


def _table(head: list[str], body: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in body:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines)


def to_markdown(rep: dict) -> str:
    cand = rep["candidate"]
    inp = rep["inputs"]
    ses = rep["sesoi"]
    lines_ = [ln for ln in ("central", "stress") if ln in inp["se12"]]
    out: list[str] = []
    out.append(f"# Feasibility 3.1: {cand['id']} - {cand['title']}")
    out.append("")
    out.append(f"Statistik: {cand['statistic']['name']} [{cand['statistic']['unit']}], einseitig, Richtung {cand['statistic']['direction']}.  "
               f"Wissensklasse {cand['knowledge_class']}, Kohorten-Stichtag {cand['cohort_date']}, Selektions-K {cand['selection_k']}.")
    out.append("")
    out.append(f"SESOI = **{_f(ses['value'], 6)} {ses['unit']}** ({ses['mode']}; {ses['label']}).  "
               f"SE_12 zentral {_f(inp['se12']['central'], 6)}" + (f", Stress {_f(inp['se12']['stress'], 6)}" if "stress" in inp["se12"] else "")
               + f", c = {_f(inp['c_overlap'], 3)}, Gate-Faktor {_f(inp['gate_factor'], 4)}.")
    if rep["prior"]:
        pts = ", ".join(f"{k} {_f(v['effect'], 5)} (SR_eff {_f(v['sr_eff'], 3)})" for k, v in rep["prior"]["points"].items())
        out.append(f"Prior-Etikett {rep['prior']['label']}: {pts}.")
    out.append("")
    # table 1: MDE per rule
    out.append("## 1. MDE80 je Entscheidungsregel (T = 24 Monate Konfirmationsdaten)")
    out.append("")
    head = ["Regel", "alpha_eff", "Power bei MDE", "MDE80 zentral"] + (["MDE80 Stress"] if "stress" in lines_ else []) + \
           ["<= SESOI z/s", "Boden z/s", "Daten x R1"]
    body = []
    for k, r in rep["rules"].items():
        e = r["by_T"]["24"]
        fl = r["floor"]
        body.append([k, _f(e.get("alpha_eff"), 6), _f(e.get("power_at_mde"), 3), _f(e["mde80"]["central"], 6)]
                    + ([_f(e["mde80"].get("stress"), 6)] if "stress" in lines_ else [])
                    + [f"{_f(e['meets_sesoi']['central'])}/{_f(e['meets_sesoi'].get('stress'))}",
                       (f"{_f(fl['central'], 6)}/{_f(fl.get('stress'), 6)}" if fl["exists"] else "kein"), _f(e.get("data_factor_vs_R1"), 3)])
    out.append(_table(head, body))
    out.append("")
    if inp["gate_factor"] < 1.0:
        out.append(f"Der Gate-Faktor {_f(inp['gate_factor'], 4)} ist in alle Zeilen und beide Linien eingerechnet (Power je Entscheidung mal g).")
        out.append("")
    out.append("Regeln: R1 C.10 je Fenster 0,05/0,80; R2 C.10 gemeinsam 0,80; R3 gepoolt 0,0025; R4_aXX gepoolt 0,0025 + REZENZ-Screen alpha_s 0,XX "
               "(Korrelation sqrt(r)); R5 gepoolt 0,0025 + registrierter Stabilitaetstest (Variante c, beschlossen DEC-107; Kostenquote q 0,95, entfaellt <= 12 Monate); R6 GSD O'Brien-Fleming (mit/ohne Screen).")
    out.append("")
    # table 2: exploration vs confirmation
    out.append("## 2. Exploration (Zone X) und Konfirmation (Zone V / Zone K)")
    out.append("")
    ex = rep["exploration"]
    if ex["available"]:
        out.append(f"**Exploration Zone X** ({_f(ex['n_units'], 1)} Einheiten, {_f(ex['months'], 1)} Monate): Aufloesung (MDE80, 0,05) "
                   + ", ".join(f"{ln} {_f(ex['resolution_mde80'][ln], 6)}" for ln in lines_)
                   + "; Ausschlussgrenze (95 %, einseitig, Schaetzer 0) "
                   + ", ".join(f"{ln} {_f(ex['exclusion_limit_if_null'][ln], 6)}" for ln in lines_)
                   + f".  Loest SESOI auf: {_f(ex['resolves_sesoi']['central'])}; schliesst SESOI aus bei Nullschaetzer: {_f(ex['excludes_sesoi_if_null']['central'])}.")
    else:
        out.append("**Exploration Zone X:** keine X-Daten angegeben.")
    cv = rep["confirmation"]["V"]
    out.append("")
    out.append(f"**Konfirmation Zone V:** {'nutzbar' if cv['usable'] else 'nicht nutzbar'} - {cv['note']}")
    ck = rep["confirmation"]["K"]
    out.append(f"**Konfirmation Zone K:** Start {ck['start']} (wirksam {ck['effective_start']}), Lesart B, verfuegbar zum Stichtag "
               f"{_f(ck['months_available_at_cohort'], 1)} Monate, Horizont-Ende {ck['horizon_end']}.")
    out.append("")
    head = ["Regel", "Daten T zentral [Mon]", "Einheiten", "Jahre/Fenster", "Entscheidung ab", "E[Mon] H1", "im Horizont"]
    if "stress" in lines_:
        head += ["Daten T Stress [Mon]", "Entscheidung Stress"]
    body = []
    for k, r in rep["rules"].items():
        a = r["at_sesoi"]["central"]
        row_ = [k, _f(a["t_required_months"], 2), _f(a.get("n_units"), 1), _f(a.get("years_per_window"), 2) if "years_per_window" in a else "-",
                a.get("decision_date") or "nie", _f(a.get("expected_months_h1"), 1) if "expected_months_h1" in a else "-", _f(a.get("within_horizon"))]
        if "stress" in lines_:
            s = r["at_sesoi"]["stress"]
            row_ += [_f(s["t_required_months"], 2), s.get("decision_date") or "nie"]
        body.append(row_)
    out.append(_table(head, body))
    out.append("")
    if cv["usable"]:
        out.append("Zone V (ein Blick), MDE80 gegen SESOI:")
        out.append("")
        body = []
        for k, v in cv["per_rule"].items():
            if not v["applicable"]:
                continue
            body.append([k] + [f"{_f(v['mde80'][ln], 6)} ({_f(v['testable'][ln])})" for ln in lines_] + [_f(v["power_at_sesoi_central"], 3)])
        out.append(_table(["Regel"] + [f"MDE80 {ln} (testbar)" for ln in lines_] + ["Power an SESOI"], body))
        out.append("")
    dmenu = rep["design_menu"]
    out.append("Design-Menue Fensterlaenge (je Fenster L Monate, zwei Fenster = T 2L), MDE80 zentral / ok gegen SESOI:")
    out.append("")
    wins = list(dmenu["by_window"])
    out.append(_table(["Regel"] + [f"L {w} (T {_f(dmenu['by_window'][w]['T_months'], 0)})" for w in wins],
                      [[k] + [f"{_f(dmenu['by_window'][w]['per_rule'][k]['mde80']['central'], 5)} / {_f(dmenu['by_window'][w]['per_rule'][k]['meets_sesoi']['central'])}"
                              for w in wins] for k in rep["rules"]]))
    out.append("")
    # table 3: SR equivalent
    out.append("## 3. SR-Aequivalent (SR_eff = Effekt / SE_12) je Fensterlaenge")
    out.append("")
    sr = rep["sr_equivalent"]
    out.append(f"Kandidat: SESOI SR_eff {_f(sr['candidate']['sesoi'], 3)}; Prior " + (", ".join(f"{k} {_f(v, 3)}" for k, v in sr['candidate']['prior'].items()) or "-")
               + ".  C.10-Referenz (Gate 1): " + ", ".join(f"{k} {_f(v, 3)}" for k, v in sr["c10_check_gate1"].items()) + ".")
    out.append("")
    keys = list(rep["rules"])
    out.append(_table(["noetig je Fenster"] + keys, [[k] + [_f(v.get(r), 3) for r in keys] for k, v in sr["needed"].items()]))
    out.append("")
    # conjunction
    cjb = rep["conjunction"]
    if cjb and cjb.get("variants"):
        out.append("## 4. Konjunktionen: Produkt neben exakter gemeinsamer Power (Doppelausweis, DEC-105 (7))")
        out.append("")
        body = []
        for vn, v in cjb["variants"].items():
            for win, wd in v.items():
                if win == "conditions":
                    continue
                for ln, ld in wd.items():
                    for sc, sd in ld.items():
                        body.append([vn, win, ln, sc, _f(sd["product"], 3), _f(sd["pair"], 3, "-"), _f(sd["joint"], 3)])
        out.append(_table(["Placebosatz", "Fenster", "Linie", "Null", "Produkt", "exakt Paar", "exakt gemeinsam"], body))
        out.append("")
    if cjb and cjb.get("two_conditions_power_0_90"):
        t2 = cjb["two_conditions_power_0_90"]
        out.append(f"Zwei Bedingungen je Power 0,90, Korrelation {_f(t2['rho'], 2)}: exakt {_f(t2['exact'], 3)} gegen Produkt {_f(t2['product'], 3)}.")
        out.append("")
    # strictness
    out.append("## 5. Strenge-Quotient MDE80(alle Festlegungen) / MDE80(Grundfassung)")
    out.append("")
    for cid, ch in rep["strictness"]["chains"].items():
        out.append(f"**Kette {cid}** ({ch['label']}, {ch['kind']}): Quotient **{_f(ch['quotient'], 3)}**"
                   + (" - ab 1,3: Nutzer-Vorlage vor der Registrierung (E8 (b))" if ch["needs_user_template"] else "") + ".")
        out.append("")
        out.append(_table(["Schritt", "MDE80", "Faktor", "Zuwachs", "kumuliert"],
                          [[s["label"], _f(s["mde80"], 3), _f(s["factor_vs_previous"], 4, "-"), _f(s["increment"], 3, "-"), _f(s["cumulative_quotient"], 4, "-")]
                           for s in ch["steps"].values()]))
        out.append("")
    body = []
    for k, rc in rep["strictness"]["rules"].items():
        if rc is None:
            body.append([k, "nie", "-"])
            continue
        body.append([k, _f(rc["quotient"], 3), " -> ".join(f"{sid} {_f(s['mde80'], 5)}" for sid, s in rc["steps"].items())])
    out.append("Regelebene (Stress und Gate bei T = 24 Monate):")
    out.append("")
    out.append(_table(["Regel", "Quotient", "Zerlegung"], body))
    out.append("")
    # OC
    out.append("## 6. OC-Zeile: P(PASS) bei Effekt 0 / SESOI / Prior (analytisch / Monte Carlo)")
    out.append("")
    for sec, title in (("at_t_required", "bei den Daten, die die Regel fuer Power 0,80 an der SESOI braucht"), ("at_t_ref", "bei T = 24 Monaten")):
        out.append(f"{title} (MC {rep['oc']['mc_reps']} Wiederholungen, Seed {rep['oc']['seed']}):")
        out.append("")
        eff_names = list(next(iter(rep["oc"][sec].values()))["effects"])
        body = []
        for k, r in rep["oc"][sec].items():
            body.append([k, _f(r["T_months"], 1) + ("*" if r["t_is_horizon_cap"] else "")] +
                        [f"{_f(r['effects'][e]['analytic'], 4)} / {_f(r['effects'][e]['mc'], 4)}" for e in eff_names] +
                        [_f(r["ppv"]["base_rate_10pct"], 3, "-"), _f(r["expected_false_pass_10_null_tests"], 4)])
        out.append(_table(["Regel", "T [Mon]"] + eff_names + ["PPV (Basisrate 0,10)", "Falsch-PASS je 10 Nulltests"], body))
        out.append("")
    out.append("(* Daten bis zur Horizontgrenze, weil die Regel die SESOI nie erreicht.)")
    out.append("")
    if rep["pilot_handover"]:
        ph = rep["pilot_handover"]
        out.append(f"Pilot-Uebergabe: P(Pilotschaetzer >= {_f(ph['threshold'], 3)}) bei SE {_f(ph['se'], 3)}: "
                   + ", ".join(f"wahrer Effekt {k.replace('p', '.')}: {v:.3g}" for k, v in ph["p_handover"].items()) + ".")
        out.append("")
    # verdict
    out.append("## 7. Verdikt der Feasibility (binaer, je Regel)")
    out.append("")
    vd = rep["verdict"]
    out.append(f"Horizont {_f(vd['horizon_limit_months'], 0)} Monate ab Stichtag.  Keine Regel ist die Regel, bis der Nutzer P-2 entscheidet.")
    out.append("")
    out.append(_table(["Regel"] + [f"Verdikt {ln}" for ln in lines_] + ["Folge (zentral)"],
                      [[k] + [v[ln]["verdict"] for ln in lines_] + [v["central"]["consequence"]] for k, v in vd["by_rule"].items()]))
    out.append("")
    ht = rep["heavy_tail"]
    out.append("Schwere Raender und kleine Clusterzahl (Sensitivitaet, nicht bindend; t-Grenzen mit df = Cluster - 1):")
    out.append("")
    body = []
    for k, v in ht["per_rule"].items():
        if "factor" in v:
            body.append([k, _f(v["n_units_test"], 1), _f(v["df"], 1), _f(v["t_crit"], 3, "-"), _f(v["z_crit"], 3), _f(v["factor"], 4, "-"),
                         _f(v["data_factor_first_order"], 4, "-")])
        else:
            body.append([k, _f(v["first_look_units"], 1) + " (erster Blick)", "-", "-", "-", "-", f"erster Blick >= {ht['min_clusters_first_look']} Cluster: {_f(v['meets_min_clusters_first_look'])}"])
    out.append(_table(["Regel", "Cluster im Test", "df", "t-Grenze", "z-Grenze", "MDE-Faktor t/normal", "Datenfaktor (1. Ordnung)"], body))
    out.append("")
    # reporting rows
    out.append("## 8. Pflicht-Berichtszeilen (DEC-104 E1, DEC-105)")
    out.append("")
    out.append(_table(["Zone", "Regel", "estimate", "se", "upper_limit95", "u95 bei Schaetzer 0", "n_eff", "c_overlap", "selection_k"],
                      [[r["zone"], r["rule"] or "-", "Platzhalter", _f(r["se"], 6), r["upper_limit95"], _f(r["upper_limit95_if_estimate_zero"], 6),
                        _f(r["n_eff"], 1), _f(r["c_overlap"], 3), r["selection_k"]] for r in rep["reporting_rows"]]))
    out.append("")
    if rep["warnings"]:
        out.append("## Hinweise")
        out.append("")
        out.extend(f"- {w}" for w in rep["warnings"])
        out.append("")
    return "\n".join(out) + "\n"
