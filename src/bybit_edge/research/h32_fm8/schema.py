"""Registered YAML ``state/registered/h32_v1.yaml`` -- schema (ERSTFASSUNG 11), pre-flight and T5 pins.

``validate_registered`` is the pre-flight of ``--pilot`` / ``--positive-control`` / ``--run`` (PP1 / P1): a missing or
invalid field is a loud fail BEFORE any panel byte is read.  Every constant the run checks against the YAML is pinned to
a code constant of ``constants.py`` (T5): the YAML may repeat a frozen number, never change it.  The frozen v6 constants
(per window and variant) are the only numbers that come from the registration alone.
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import yaml

from . import constants as C
from .errors import PinError, SchemaError

__all__ = ["load_registered_yaml", "validate_registered", "frozen_pin_table", "FROZEN_VARIANT_KEYS",
           "FROZEN_SCALAR_KEYS", "is_hex64", "threshold_frozen", "window_constants"]

#: per-variant frozen constants of a judged window (ERSTFASSUNG 1.6).
FROZEN_VARIANT_KEYS: tuple[str, ...] = ("se_mean", "e_se_rule", "sd_week", "null_mean", "q95", "q95_driftfree",
                                        "q95_drifting")
#: scalar frozen constants of a judged window.
FROZEN_SCALAR_KEYS: tuple[str, ...] = ("ceiling_k4", "floor_fm8", "v_fm8")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def is_hex64(x: Any) -> bool:
    return isinstance(x, str) and bool(_HEX64.match(x.lower()))


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise SchemaError(msg)


def _pin(cond: bool, msg: str) -> None:
    if not cond:
        raise PinError(msg)


def load_registered_yaml(path: Path | str) -> dict[str, Any]:
    """Plain YAML load.  The caller has passed the start lock (sha256 of the file) before."""
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SchemaError(f"{path}: the registered YAML is not a mapping")
    return payload


def _get(d: Any, *keys: str) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            raise SchemaError("registered YAML: field '" + ".".join(keys) + "' missing")
        cur = cur[k]
    return cur


def validate_registered(reg: dict[str, Any]) -> None:
    """PP1 / P1 (+ the YAML-only part of PP3 / P4): schema and pins.  Raises ``SchemaError`` for a missing or malformed
    field, ``PinError`` for a field that differs from its frozen code constant."""
    _need(isinstance(reg, dict), "registered YAML is not a mapping")
    # --- hypotheses: one entry per variant, registered direction, no lock status (the lock is the hand-over rule)
    hyps = _get(reg, "hypotheses")
    _need(isinstance(hyps, dict) and set(hyps) == set(C.ENTRY.values()),
          f"hypotheses must be exactly {sorted(C.ENTRY.values())} (K = 4, ERSTFASSUNG 1.1)")
    for v in C.VARIANTS:
        h = hyps[C.ENTRY[v]]
        _need(isinstance(h, dict) and h.get("variant") == v and h.get("hypothesis") == C.HYPOTHESIS
              and h.get("direction") == C.DIRECTION[v] and not h.get("status"),
              f"hypotheses[{C.ENTRY[v]}] must be {{hypothesis: H-32, variant: {v}, direction: {C.DIRECTION[v]}}}")
    _pin(_get(reg, "primary_statistic") == C.PRIMARY_STATISTIC, f"primary_statistic must be {C.PRIMARY_STATISTIC}")
    _pin(_num(_get(reg, "alpha")) and float(reg["alpha"]) == C.ALPHA, f"alpha must be {C.ALPHA}")
    zk = _get(reg, "z_krit")
    _pin(_num(zk) and abs(float(zk) - C.Z_KRIT) <= 5e-7, f"z_krit must be the number {C.Z_KRIT:.7f} (DEC-94 (1)/(2))")
    _pin(_num(_get(reg, "mde_faktor")) and float(reg["mde_faktor"]) == C.MDE_FAKTOR, f"mde_faktor must be {C.MDE_FAKTOR}")
    # --- seal
    seal = _get(reg, "seal")
    _pin(seal.get("panel_cut_test") == C.CUT_TEST, f"seal.panel_cut_test must be {C.CUT_TEST}")
    _pin(seal.get("panel_cut_pilot") == C.CUT_PILOT, f"seal.panel_cut_pilot must be {C.CUT_PILOT}")
    _pin(seal.get("stress_list_date_filter") is True, "seal.stress_list_date_filter must be true")
    # --- fdr
    fdr = _get(reg, "fdr")
    _pin(fdr.get("p_source") == C.P_SOURCE, f"fdr.p_source must be {C.P_SOURCE!r} (DEC-99 p convention: the binding p comes "
         "from the v6 replicates of the factor-preserving null)")
    _need(fdr.get("p_statistic") == C.P_STATISTIC and fdr.get("sided") == "one" and fdr.get("combine") == "max_p",
          f"fdr: p_statistic must be {C.P_STATISTIC!r}, sided one, combine max_p")
    _pin(list(fdr.get("report_only") or []) == list(C.P_REPORT_ONLY),
         f"fdr.report_only must be {list(C.P_REPORT_ONLY)} (block permutation and normal approximation are report-only)")
    _pin(isinstance(fdr.get("n_reps"), int) and not isinstance(fdr.get("n_reps"), bool) and fdr["n_reps"] >= C.N_REPS_MIN
         and isinstance(reg.get("rules"), dict) and isinstance(reg["rules"].get("n_reps"), int) and fdr["n_reps"] >= reg["rules"]["n_reps"],
         f"fdr.n_reps must be an integer >= max({C.N_REPS_MIN}, rules.n_reps) (number of p replicates)")
    _need(is_hex64(fdr.get("replicates_sha256")), "fdr.replicates_sha256 must be a sha256 (the v6 p replicates artifact)")
    _pin(fdr.get("block_len") == C.PERM_BLOCK, f"fdr.block_len must be {C.PERM_BLOCK}")
    _pin(fdr.get("n_perm") == C.N_PERM and isinstance(fdr.get("n_perm"), int), f"fdr.n_perm must be {C.N_PERM}")
    _pin(fdr.get("seed") == C.SEED, f"fdr.seed must be {C.SEED}")
    fam = fdr.get("family") or {}
    _pin(fam.get("name") == "F-H32" and fam.get("method") == "BH" and fam.get("alpha") == C.BH_ALPHA
         and fam.get("denominator") == C.BH_DENOMINATOR and fam.get("report_only") is True,
         "fdr.family must be F-H32, BH, alpha 0.10, denominator 4, report_only")
    over = fdr.get("over_family") or {}
    _pin(over.get("name") == "F-WEEK" and over.get("method") == "BY" and over.get("alpha") == C.BY_ALPHA
         and over.get("binding") is True and over.get("double_statement_m") == C.FWEEK_DOUBLE_M,
         "fdr.over_family must be F-WEEK, BY, alpha 0.10, binding, double_statement_m 11")
    fc = _get(reg, "fweek_counting")
    _pin(fc.get("in_m") == "tested_only" and fc.get("method") == "BY" and fc.get("alpha") == C.BY_ALPHA
         and fc.get("double_statement_m") == C.FWEEK_DOUBLE_M, "fweek_counting must be {in_m: tested_only, method: BY, alpha: 0.10, double_statement_m: 11}")
    sel = _get(reg, "selection")
    _pin(sel.get("K") == C.K_FAMILY and sel.get("ceiling") == "ceiling_k4", "selection must be {K: 4, ceiling: ceiling_k4}")
    # --- beta control, rules
    bc = _get(reg, "beta_control")
    _pin(bc.get("method") == C.PRIMARY_STATISTIC and bc.get("beta_window_weeks") == C.BETA_WINDOW_WEEKS,
         "beta_control must be fm_neutral_8w / 8")
    rules = _get(reg, "rules")
    _pin(rules.get("seed") == C.SEED, f"rules.seed must be {C.SEED}")
    _pin(rules.get("mean_block") == C.MEAN_BLOCK, f"rules.mean_block must be {C.MEAN_BLOCK}")
    _pin(isinstance(rules.get("n_boot"), int) and rules["n_boot"] >= C.N_BOOT_MIN,
         f"rules.n_boot must be an integer >= {C.N_BOOT_MIN}")
    _pin(isinstance(rules.get("n_reps"), int) and rules["n_reps"] >= C.N_REPS_MIN,
         f"rules.n_reps must be an integer >= {C.N_REPS_MIN}")
    _pin(_num(rules.get("null_level")) and abs(float(rules["null_level"]) - C.NULL_LEVEL) <= 1e-12,
         f"rules.null_level must be {C.NULL_LEVEL}")
    _need(_num(rules.get("bounce_spread")) and float(rules["bounce_spread"]) > 0.0,
          "rules.bounce_spread must be a finite positive number (DEC-89 E1: measured, no default)")
    # --- pilot window
    pw = _get(reg, "pilot_window")
    _pin(pw.get("start") == C.WINDOWS["P"][0] and pw.get("end") == C.CUT_PILOT, "pilot_window.start/end mismatch")
    _pin(pw.get("first_formation_week") == C.PILOT_FIRST_FORMATION and pw.get("last_formation_week") == C.PILOT_LAST_FORMATION
         and pw.get("last_outcome_day") == C.CUT_PILOT, "pilot_window formation / outcome range mismatch")
    _pin(pw.get("w_pilot") == C.W_PILOT, f"pilot_window.w_pilot must be {C.W_PILOT}")
    _pin(pw.get("k_min_rule") == C.K_MIN["P"], f"pilot_window.k_min_rule must be {C.K_MIN['P']}")
    sr = pw.get("single_run") or {}
    _pin(sr.get("required") is True and sr.get("rerun_requires_dec") is True, "pilot_window.single_run must be required, rerun_requires_dec")
    prs = pw.get("pilot_result_sha256")
    _need(prs is None or is_hex64(prs), "pilot_window.pilot_result_sha256 must be null or a sha256")
    se_rule = (pw.get("se_rule") or {}).get("stationary_bootstrap") or {}
    _pin(se_rule.get("mean_block") == C.MEAN_BLOCK and isinstance(se_rule.get("n_rep"), int)
         and se_rule["n_rep"] >= C.N_BOOT_MIN and se_rule.get("seed") == C.SEED,
         "pilot_window.se_rule.stationary_bootstrap must be {mean_block 4, n_rep >= 1000, seed 53}")
    band = pw.get("band") or {}
    _pin(band.get("level") == C.BAND_LEVEL and _num(band.get("z")) and abs(float(band["z"]) - C.BAND_Z) <= 5e-5,
         "pilot_window.band must be {level 0.80, z 1.2816}")
    pfz = pw.get("frozen_v6")
    _need(isinstance(pfz, dict), "pilot_window.frozen_v6 missing")
    mp = pfz.get("m_P")
    _need(isinstance(mp, dict) and all(_num(mp.get(v)) for v in C.VARIANTS), "pilot_window.frozen_v6.m_P: finite value per variant required")
    _need(is_hex64(pfz.get("k_fm8_series_sha256")), "pilot_window.frozen_v6.k_fm8_series_sha256 must be a sha256")
    _need(isinstance(pfz.get("calibration"), dict), "pilot_window.frozen_v6.calibration missing")
    # --- hand-over rule
    hr = _get(reg, "handover_rule")
    _pin(hr.get("version") == C.HANDOVER_VERSION, f"handover_rule.version must be {C.HANDOVER_VERSION}")
    _pin(_num(hr.get("t_min")) and float(hr["t_min"]) == C.T_MIN, f"handover_rule.t_min must be {C.T_MIN}")
    _pin(hr.get("prior_reading") == "point", "handover_rule.prior_reading must be 'point' (reading A)")
    _pin((hr.get("on_fail") or {}).get("p_value") == 1.0 and (hr.get("on_fail") or {}).get("in_f_week_m") is False,
         "handover_rule.on_fail must be {p_value: 1.0, in_f_week_m: false}")
    # --- windows
    wins = _get(reg, "windows")
    _need(isinstance(wins, dict), "windows missing")
    for wn in ("W1", "W2"):
        w = wins.get(wn)
        _need(isinstance(w, dict), f"windows.{wn} missing")
        _pin(w.get("start") == C.WINDOWS[wn][0] and w.get("end") == C.WINDOWS[wn][1], f"windows.{wn}.start/end mismatch")
        _pin(w.get("w_judged") == C.W_JUDGED[wn], f"windows.{wn}.w_judged must be {C.W_JUDGED[wn]}")
        stress = ((w.get("calibration") or {}).get("stress")) or {}
        _need(_num(stress.get("rho_f")) and _num(stress.get("beta_sd_calibrated")) and float(stress["beta_sd_calibrated"]) > 0.0,
              f"windows.{wn}.calibration.stress.{{rho_f, beta_sd_calibrated}} missing or not finite")
        _need(_num(stress.get("target_factor_share")) and 0.0 < float(stress["target_factor_share"]) < 1.0,
              f"windows.{wn}.calibration.stress.target_factor_share must be in (0, 1)")
        sc = w.get("null_scales") or {}
        _need(_num(sc.get("sigma_f")) and float(sc["sigma_f"]) > 0.0 and _num(sc.get("sigma_e_used")) and float(sc["sigma_e_used"]) > 0.0,
              f"windows.{wn}.null_scales.{{sigma_f, sigma_e_used}} must be finite positive")
        _need(_num(w.get("bounce_sigma_true")) and float(w["bounce_sigma_true"]) > 0.0,
              f"windows.{wn}.bounce_sigma_true must be finite positive (DEC-89 E1)")
        sv = w.get("survivorship") or {}
        _need(_num(sv.get("mom1_diff_in_ic_min_units")) and _num(sv.get("rev_gap_diff_in_ic_min_units")),
              f"windows.{wn}.survivorship.{{mom1,rev_gap}}_diff_in_ic_min_units must be finite")
        fz = w.get("frozen_v6")
        _need(isinstance(fz, dict), f"windows.{wn}.frozen_v6 missing")
        for key in FROZEN_VARIANT_KEYS:
            d = fz.get(key)
            _need(isinstance(d, dict) and all(_num(d.get(v)) for v in C.VARIANTS),
                  f"windows.{wn}.frozen_v6.{key}: finite value for each of the 4 variants required (v6 constant)")
        for key in FROZEN_SCALAR_KEYS:
            _need(_num(fz.get(key)), f"windows.{wn}.frozen_v6.{key} missing or not finite (v6 constant)")
        _need(float(fz["floor_fm8"]) > 0.0 and float(fz["v_fm8"]) > 0.0, f"windows.{wn}.frozen_v6.floor_fm8 / v_fm8 must be > 0")
        _need(is_hex64(fz.get("k_fm8_series_sha256")), f"windows.{wn}.frozen_v6.k_fm8_series_sha256 must be a sha256")
    # --- positive control (criteria are pinned to the code constants)
    pc = _get(reg, "positive_control")
    crit = pc.get("criteria") or {}
    _pin(crit.get("sd_ratio_max") == C.PC_SD_RATIO_MAX and crit.get("pass_share_min") == C.PC_PASS_SHARE_MIN
         and crit.get("neg_pass_max") == C.PC_NEG_PASS_MAX and crit.get("injection_tolerance") == C.PC_INJECT_JUDGE_TOL,
         "positive_control.criteria must repeat the frozen criteria (1.10 / 0.734 / 0.086 / 0.10)")
    _pin(list(pc.get("seeds") or []) == [min(C.PC_SEEDS_JUDGE), max(C.PC_SEEDS_JUDGE)]
         and list(pc.get("calibration_seeds_injection") or []) == [min(C.PC_SEEDS_INJECT), max(C.PC_SEEDS_INJECT)]
         and list(pc.get("calibration_seeds_world") or []) == [min(C.PC_SEEDS_SIGMA_G), max(C.PC_SEEDS_SIGMA_G)],
         "positive_control seed ranges must be 53..252 / 1000..1049 / 2000..2049")
    # --- data fingerprints
    fp = _get(reg, "data_fingerprints")
    _need(is_hex64(fp.get("union_range_fingerprint")) and is_hex64(fp.get("delisting_dates_sha256"))
          and is_hex64(fp.get("delisting_register_sha256")),
          "data_fingerprints.{union_range_fingerprint, delisting_dates_sha256, delisting_register_sha256} must be sha256 strings "
          "(DEC-100: fingerprint over the Data-Harvest delisting register)")
    _need(fp.get("delisted_tree_sha256") is None or is_hex64(fp.get("delisted_tree_sha256")),
          "data_fingerprints.delisted_tree_sha256 must be absent or a sha256")


def window_constants(reg: dict[str, Any], wn: str) -> dict[str, Any]:
    """The frozen v6 block of window ``wn`` plus the registered ``w_judged``."""
    w = reg["windows"][wn]
    out = dict(w["frozen_v6"])
    out["w_judged"] = int(w["w_judged"])
    return out


def threshold_frozen(reg: dict[str, Any], wn: str, variant: str) -> float:
    """Frozen threshold of the pre-verdict kill (ERSTFASSUNG 1.10): ``z_krit * e_se_rule + max(0, null_mean)``."""
    fz = reg["windows"][wn]["frozen_v6"]
    return C.Z_KRIT * float(fz["e_se_rule"][variant]) + max(0.0, float(fz["null_mean"][variant]))


def frozen_pin_table(reg: dict[str, Any]) -> dict[str, Any]:
    """T5: the flat set of numbers the run reads from the registration -- compared by a test with what flows into every
    payload."""
    out: dict[str, Any] = {
        "alpha": reg["alpha"], "z_krit": reg["z_krit"], "mde_faktor": reg["mde_faktor"],
        "n_perm": reg["fdr"]["n_perm"], "block_len": reg["fdr"]["block_len"], "seed": reg["rules"]["seed"],
        "p_source": reg["fdr"]["p_source"], "n_reps_p": reg["fdr"]["n_reps"], "replicates_sha256": reg["fdr"]["replicates_sha256"],
        "mean_block": reg["rules"]["mean_block"], "n_boot": reg["rules"]["n_boot"], "n_reps": reg["rules"]["n_reps"],
        "panel_cut_test": reg["seal"]["panel_cut_test"], "panel_cut_pilot": reg["seal"]["panel_cut_pilot"],
        "w_pilot": reg["pilot_window"]["w_pilot"], "m_P": dict(reg["pilot_window"]["frozen_v6"]["m_P"]),
    }
    for wn in ("W1", "W2"):
        w = reg["windows"][wn]
        out[wn] = {"w_judged": w["w_judged"], **{k: w["frozen_v6"][k] for k in (*FROZEN_VARIANT_KEYS, *FROZEN_SCALAR_KEYS,
                                                                                "k_fm8_series_sha256")}}
    return out
