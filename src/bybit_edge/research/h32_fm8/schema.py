"""Registered YAML ``state/registered/h32_v1.yaml`` -- schema (ERSTFASSUNG 11), pre-flight and T5 pins.

``validate_registered`` is the pre-flight of ``--pilot`` / ``--positive-control`` / ``--run`` (PP1 / P1): a missing or
invalid field is a loud fail BEFORE any panel byte is read.  Every constant the run checks against the YAML is pinned to
a code constant of ``constants.py`` (T5): the YAML may repeat a frozen number, never change it.  The frozen v6 constants
(per window and variant) are the only numbers that come from the registration alone.

DEC-101 adds mandatory blocks: ``universe`` (E1: rule ``linear_usdt_perpetual`` + the excluded counts at the Vorlauf),
``null_scaling`` (E2: enabled, the rule text, direction strictness), ``pilot_window.out_dir`` (E3: the one pilot directory),
``runner`` (E4: the CLI arguments that determine the union-range fingerprint), ``data_fingerprints.delisted_tree_sha256``
(E4) and ``q95_1000`` / ``q95_10000`` next to the frozen ``q95`` (E5).

DEC-101 Teil 2 (Nachpruefung N-1..N-5) adds mandatory pins: ``positive_control.null_scaling`` (N-1: enabled, rule and ref texts),
``positive_control.inject_target`` / ``inject_target_label`` / ``inject_target_ref`` (N-2: the injection target F), the frozen
``null_mean_driftfree`` per window and variant (N-2: ``m_df``), the texts of rule U-4 (``handover_rule.version`` ``U-4``, the
condition (ii) text and ``k_pred``, N-3), ``fdr.p_formula`` (N-5: names the scaling) and the documentation fields
``code_commit_prelaunch`` / ``code_commit_registration`` (N-5).  No frozen v6 NUMBER changes.
"""
from __future__ import annotations

import math
import re
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from . import constants as C
from .errors import PinError, SchemaError

__all__ = ["load_registered_yaml", "validate_registered", "frozen_pin_table", "FROZEN_VARIANT_KEYS",
           "FROZEN_SCALAR_KEYS", "is_hex64", "threshold_frozen", "window_constants"]

#: per-variant frozen constants of a judged window (ERSTFASSUNG 1.6).  DEC-101 Teil 2 (N-2): ``null_mean_driftfree`` (the null mean of
#: the DRIFTFREE cell, ``m_df`` of the positive control's injection target F) is a mandatory pin; the Vorlauf artifact carries it in
#: ``frozen_v6`` already (the re-emit of the template takes it from there, no new calculation).
FROZEN_VARIANT_KEYS: tuple[str, ...] = ("se_mean", "e_se_rule", "sd_week", "null_mean", "q95", "q95_driftfree",
                                        "q95_drifting", "q95_1000", "q95_10000", "null_mean_driftfree")
#: scalar frozen constants of a judged window.
FROZEN_SCALAR_KEYS: tuple[str, ...] = ("ceiling_k4", "floor_fm8", "v_fm8")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


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


def _iso_date(x: Any) -> str | None:
    """Canonical ISO date string of a YAML date / string, ``None`` if it is neither."""
    if isinstance(x, date) and not hasattr(x, "hour"):
        return x.isoformat()
    if isinstance(x, str):
        try:
            return date.fromisoformat(x).isoformat() if date.fromisoformat(x).isoformat() == x else None
        except ValueError:
            return None
    return None


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def validate_out_dir(out_dir: Any) -> str:
    """DEC-101 E3: ``pilot_window.out_dir`` is a repository-relative POSIX path strictly below ``scinance3-impl/state/runs``
    (no ``..``, not absolute, not under ``data/harvest``).  Returns the normalised string."""
    _need(isinstance(out_dir, str) and bool(out_dir.strip()), "pilot_window.out_dir must be a non-empty string (DEC-101 E3)")
    pp = PurePosixPath(out_dir)
    root = PurePosixPath(C.RUNS_REL)
    _need(not pp.is_absolute() and ".." not in pp.parts and "\\" not in out_dir and pp.as_posix() == out_dir
          and "data/harvest" not in out_dir, f"pilot_window.out_dir {out_dir!r} must be a normalised repository-relative path (DEC-101 E3)")
    _need(pp.parts[:len(root.parts)] == root.parts and len(pp.parts) > len(root.parts),
          f"pilot_window.out_dir {out_dir!r} must lie strictly below {C.RUNS_REL} (DEC-101 E3)")
    return out_dir


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
    # --- DEC-101 E1: the universe (rule pinned, counts frozen at the Vorlauf)
    uni = _get(reg, "universe")
    _need(isinstance(uni, dict), "universe must be a mapping (DEC-101 E1)")
    _pin(uni.get("rule") == C.UNIVERSE_RULE, f"universe.rule must be {C.UNIVERSE_RULE!r} (DEC-101 E1), got {uni.get('rule')!r}")
    _need(isinstance(uni.get("label"), str) and bool(uni["label"].strip()), "universe.label missing (mandatory label, DEC-101 E1)")
    exc = uni.get("excluded_at_prelaunch")
    _need(isinstance(exc, dict) and set(exc) == set(C.UNIVERSE_CLASSES) and all(_is_int(exc[c]) and exc[c] >= 0 for c in exc),
          f"universe.excluded_at_prelaunch must hold a non-negative integer for each of {list(C.UNIVERSE_CLASSES)}")
    # --- DEC-101 E2: scaled null
    ns = _get(reg, "null_scaling")
    _need(isinstance(ns, dict), "null_scaling must be a mapping (DEC-101 E2)")
    _pin(ns.get("enabled") is True, "null_scaling.enabled must be true (DEC-101 E2)")
    _pin(ns.get("rule") == C.NULL_SCALING_RULE, f"null_scaling.rule must be {C.NULL_SCALING_RULE!r}")
    _pin(ns.get("direction") == C.NULL_SCALING_DIRECTION and ns.get("ref") == C.NULL_SCALING_REF,
         f"null_scaling must carry direction {C.NULL_SCALING_DIRECTION!r} and ref {C.NULL_SCALING_REF!r}")
    # --- DEC-101 E4: runner pins
    rn = _get(reg, "runner")
    _need(isinstance(rn, dict) and _iso_date(rn.get("as_of")) is not None and _is_int(rn.get("start_year"))
          and _is_int(rn.get("end_year")) and rn["end_year"] >= rn["start_year"] and isinstance(rn.get("allow_partial"), bool),
          "runner must be {as_of: ISO date, start_year: int, end_year: int >= start_year, allow_partial: bool} (DEC-101 E4)")
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
    _pin(fdr.get("p_formula") == C.P_FORMULA,
         f"fdr.p_formula must be the code text naming the scaling of the replicates (DEC-101 E2, Teil 2 (N-5)): {C.P_FORMULA!r}")
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
    validate_out_dir(pw.get("out_dir"))                                                                   # DEC-101 E3
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
    cond_ii = next((c for c in (hr.get("conditions") or []) if isinstance(c, dict) and c.get("id") == "ii"), None)
    _pin(isinstance(cond_ii, dict) and cond_ii.get("text") == C.HANDOVER_COND_II,                     # DEC-101 Teil 2 (N-3): YAML text = code constant
         f"handover_rule.conditions[ii].text must be the code text of rule {C.HANDOVER_VERSION}: {C.HANDOVER_COND_II!r}")
    _pin(hr.get("k_pred") == C.HANDOVER_K_PRED, f"handover_rule.k_pred must be the code text {C.HANDOVER_K_PRED!r} (DEC-101 Teil 2 (N-3))")
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
        for v in C.VARIANTS:                                                                               # DEC-101 E5: the q95 rule
            _pin(float(fz["q95"][v]) == max(float(fz["q95_1000"][v]), float(fz["q95_10000"][v])),
                 f"windows.{wn}.frozen_v6.q95[{v}] must equal max(q95_1000, q95_10000) (DEC-101 E5)")
            # DEC-101 Teil 2 (N-2): null_mean is the larger of the two drift cells, so it is never below the driftfree cell's mean
            _pin(float(fz["null_mean"][v]) >= float(fz["null_mean_driftfree"][v]),
                 f"windows.{wn}.frozen_v6.null_mean[{v}] must be >= null_mean_driftfree (the frozen null mean is the larger cell, N-2)")
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
    # DEC-101 Teil 2 (N-1): the control's gate chain uses the scaled null (mandatory, enabled); (N-2): the injection target F and its label
    pcn = _get(pc, "null_scaling")
    _need(isinstance(pcn, dict), "positive_control.null_scaling must be a mapping (DEC-101 Teil 2 (N-1))")
    _pin(pcn.get("enabled") is True, "positive_control.null_scaling.enabled must be true (DEC-101 Teil 2 (N-1))")
    _pin(pcn.get("rule") == C.PC_NULL_SCALING_RULE and pcn.get("ref") == C.PC_NULL_SCALING_REF,
         f"positive_control.null_scaling must carry rule {C.PC_NULL_SCALING_RULE!r} and ref {C.PC_NULL_SCALING_REF!r}")
    _pin(pc.get("inject_target") == C.PC_INJECT_TARGET,
         f"positive_control.inject_target must be the code text of the injection target F (DEC-101 Teil 2 (N-2)): {C.PC_INJECT_TARGET!r}")
    _pin(pc.get("inject_target_label") == C.PC_INJECT_LABEL and pc.get("inject_target_ref") == C.PC_INJECT_REF,
         f"positive_control.inject_target_label / _ref must be {C.PC_INJECT_LABEL!r} / {C.PC_INJECT_REF!r} (DEC-101 Teil 2 (N-2))")
    # DEC-101 Teil 2 (N-5): the code commit of the Vorlauf and the registration commit are documented SEPARATELY
    for key, unset in (("code_commit_prelaunch", C.CODE_COMMIT_PRELAUNCH_UNSET),
                       ("code_commit_registration", C.CODE_COMMIT_REGISTRATION_PLACEHOLDER)):
        val = _get(reg, key)
        _need(isinstance(val, str) and (bool(_COMMIT.match(val)) or val == unset),
              f"{key} must be a git commit hash (7..40 hex characters, quoted in YAML) or {unset!r} (DEC-101 Teil 2 (N-5)), got {val!r}")
    # --- data fingerprints
    fp = _get(reg, "data_fingerprints")
    _need(is_hex64(fp.get("union_range_fingerprint")) and is_hex64(fp.get("delisting_dates_sha256"))
          and is_hex64(fp.get("delisting_register_sha256")) and is_hex64(fp.get("delisted_tree_sha256")),
          "data_fingerprints.{union_range_fingerprint, delisting_dates_sha256, delisting_register_sha256, delisted_tree_sha256} "
          "must be sha256 strings (DEC-100: fingerprint over the Data-Harvest delisting register; DEC-101 E4: the delisted tree is "
          "a mandatory pin)")


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
        "universe_rule": reg["universe"]["rule"], "excluded_at_prelaunch": dict(reg["universe"]["excluded_at_prelaunch"]),
        "null_scaling_rule": reg["null_scaling"]["rule"], "null_scaling_enabled": reg["null_scaling"]["enabled"],
        "runner": {"as_of": _iso_date(reg["runner"]["as_of"]), "start_year": reg["runner"]["start_year"],
                   "end_year": reg["runner"]["end_year"], "allow_partial": reg["runner"]["allow_partial"]},
        "out_dir": reg["pilot_window"]["out_dir"], "delisted_tree_sha256": reg["data_fingerprints"]["delisted_tree_sha256"],
        "pc_null_scaling_enabled": reg["positive_control"]["null_scaling"]["enabled"],        # DEC-101 Teil 2 (N-1)
        "pc_inject_target": reg["positive_control"]["inject_target"],                          # DEC-101 Teil 2 (N-2)
        "handover_version": reg["handover_rule"]["version"],                                   # DEC-101 Teil 2 (N-3)
    }
    for wn in ("W1", "W2"):
        w = reg["windows"][wn]
        out[wn] = {"w_judged": w["w_judged"], **{k: w["frozen_v6"][k] for k in (*FROZEN_VARIANT_KEYS, *FROZEN_SCALAR_KEYS,
                                                                                "k_fm8_series_sha256")}}
    return out
