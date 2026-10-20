"""Stage T -- the test (``--run``, B-3, ERSTFASSUNG 1.9, 1.10, 2 "Test-Modus"): only the variants the pilot handed over.

Gates in this order (rc 1, NO VERDICT):

  P0   start lock: sha256 of the registered YAML (CLI, before the panel is touched);
  P0'  pilot lock (:func:`load_pilot_result`): the pilot JSON has the given sha256, belongs to this registration and its
       hand-over is re-derived with rule U from the registered constants and must be bit-identical;
  P1   schema; P3 data fingerprints; P4 pins (w_judged 52 / 50, K_fm8 series, K minimum, n_perm, seed, block, replicates);
  P0'' panel cut <= ``seal.panel_cut_test`` (2026-06-28) BEFORE anything is built, maximum-date guard;
  P6   the null constants (se_mean, e_se_rule, null_mean, q95, ceiling_k4) are re-computed per window with the v6
       configuration and must lie within +-10 % of the frozen ones (judged against the FROZEN values);
  P7   seal guard (outcome weeks 2024-07-08..2025-06-30 and 2025-07-14..2026-06-22 only, no raw IC, no lag profile, no
       beta-calibration IC); P8 DEC-53 artifacts written and verified before the verdict is published.

Per handed-over entry: fm8 weekly IC series per window, SE_W by rule P-1 (4), the pure gate (``gate.evaluate``), the
block-permutation p (max-p over the windows), BH (denominator 4, report-only), F-WEEK (BY, m = tested entries; double
statement m = 11), end power, report-only labels (bounce for rev_gap, liquidity, survivorship).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable

import numpy as np

from ..wp13_xsec import run as wp13_run
from . import artifacts, checks, fm8, fweek, gate, handover, labels, nullsim, panel_cut, permutation, schema
from . import constants as C
from . import estimators as est
from . import weekly as wkl
from .errors import ArtifactError, NullCalibrationError, PilotLockError

__all__ = ["load_pilot_result", "run_test", "write_run_artifacts", "verify_run_artifacts", "render_run_markdown",
           "assert_null_value", "pilot_core_hash"]

_PILOT_NON_CORE = ("artifacts", "code", "rerun", "_series", "result_sha256")
_NORM = NormalDist()
#: report-only flag: SD of the permuted window means above this multiple of SE_W marks a contaminated permutation null.
PERM_NULL_SD_FLAG = 1.5


def pilot_core_hash(pilot: dict[str, Any]) -> str:
    return artifacts.canonical_sha256({k: v for k, v in pilot.items() if k not in _PILOT_NON_CORE})


def load_pilot_result(path: Path | str, given_sha256: str, registered: dict[str, Any], registered_sha256: str) -> dict[str, Any]:
    """P0' pilot lock: ``path`` must hash to ``given_sha256``; the JSON must be a pilot result of THIS registration (its
    ``registered_sha256`` and data fingerprints), self-consistent (``result_sha256``), and its hand-over must be reproduced
    BIT FOR BIT by rule U from the pilot statistics and the registered constants.  Returns the parsed pilot result."""
    p = Path(path)
    artifacts.refuse_unsafe_path(p)
    if not p.is_file():
        raise PilotLockError(f"pilot result {p.name} not found")
    actual = artifacts.sha256_file(p)
    if not given_sha256 or str(given_sha256).lower() != actual:
        raise PilotLockError(f"--pilot-result-sha256 does not match the sha256 of {p.name} ({actual}) -- no test without the pilot lock")
    rp = (registered.get("pilot_window") or {}).get("pilot_result_sha256")
    if rp and str(rp).lower() != actual:
        raise PilotLockError("the registration carries a different pilot_result_sha256")
    pilot = json.loads(p.read_text(encoding="utf-8"))
    if pilot.get("schema") != C.PILOT_SCHEMA or pilot.get("mode") != "pilot":
        raise PilotLockError(f"{p.name} is not an H-32 pilot result")
    if str(pilot.get("registered_sha256")).lower() != str(registered_sha256).lower():
        raise PilotLockError("the pilot result was produced under a different registered YAML")
    if (pilot.get("data_fingerprints") or {}).get("union_range_fingerprint") != registered["data_fingerprints"]["union_range_fingerprint"]:
        raise PilotLockError("the pilot result was produced on a different panel (data fingerprints)")
    if pilot_core_hash(pilot) != pilot.get("result_sha256"):
        raise PilotLockError("the pilot result is not self-consistent (result_sha256 differs from its content)")
    handed = []
    for v in C.VARIANTS:
        stats = pilot["variants"][v]["stats"]
        ho = handover.evaluate_handover(stats, handover.handover_constants(registered, v))
        ho_json = json.loads(json.dumps(ho, default=str, allow_nan=True))
        if artifacts.canonical_sha256(ho_json) != artifacts.canonical_sha256(pilot["variants"][v]["handover"]):
            raise PilotLockError(f"hand-over of {v} is not reproduced by rule U from the registered constants -- abort")
        if ho["handed_over"]:
            handed.append(v)
    if handed != list(pilot.get("handed", [])):
        raise PilotLockError("list of handed-over variants differs from the re-derived one")
    pilot["_file_sha256"] = actual
    return pilot


def assert_null_value(recomputed: float, frozen: float, *, label: str) -> None:
    """P6: ``recomputed`` within +-10 % of ``frozen`` (absolute 1e-4 where the frozen value is ~0); NaN is not comparable."""
    if recomputed is None or frozen is None or not math.isfinite(recomputed) or not math.isfinite(frozen):
        raise NullCalibrationError(f"null recomputation not comparable ({label}): recomputed={recomputed!r}, frozen={frozen!r}")
    ok = (abs(recomputed - frozen) <= C.NULL_ABS_TOL) if abs(frozen) < 1e-12 else (abs(recomputed - frozen) <= C.NULL_REL_TOL * abs(frozen))
    if not ok:
        raise NullCalibrationError(f"null recomputation deviates ({label}): recomputed={recomputed:.6f} vs frozen={frozen:.6f} "
                                   f"(tolerance +-{C.NULL_REL_TOL:.0%}) -- NO VERDICT")


def _null_recheck(win: wkl.Window, registered: dict[str, Any], log: Callable[[str], None]) -> dict[str, Any]:
    w = registered["windows"][win.name]
    fz = w["frozen_v6"]
    r = registered["rules"]
    st = w["calibration"]["stress"]
    nul = nullsim.window_null_constants(
        win, rho_f=float(st["rho_f"]), beta_sd=float(st["beta_sd_calibrated"]), sigma_f=float(w["null_scales"]["sigma_f"]),
        sigma_e=float(w["null_scales"]["sigma_e_used"]), n_reps=int(r["n_reps"]), seed=int(r["seed"]),
        floor_fm8=float(fz["floor_fm8"]), n_boot=int(r["n_boot"]), mean_block=float(r["mean_block"]), boot_seed=int(r["seed"]))
    rec = nul["frozen"]
    rows: dict[str, Any] = {}
    for key in ("se_mean", "e_se_rule", "null_mean", "q95"):
        for v in C.VARIANTS:
            assert_null_value(rec[key][v], float(fz[key][v]), label=f"{key}[{win.name}][{v}]")
            rows[f"{key}.{v}"] = {"recomputed": rec[key][v], "frozen": float(fz[key][v])}
    assert_null_value(rec["ceiling_k4"], float(fz["ceiling_k4"]), label=f"ceiling_k4[{win.name}]")
    rows["ceiling_k4"] = {"recomputed": rec["ceiling_k4"], "frozen": float(fz["ceiling_k4"])}
    log(f"  window {win.name}: null recomputation within tolerance")
    return {"within_tolerance": True, "rows": rows, "n_reps": int(r["n_reps"]), "seed": int(r["seed"])}


def run_test(panel: dict[str, Any] | None, registered: dict[str, Any], pilot: dict[str, Any],
             observed_fingerprints: dict[str, Any] | None, *, registered_sha256: str | None = None,
             wave_p: dict[str, float] | None = None, log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """The test on an UNCUT daily union panel (the pilot lock was passed by :func:`load_pilot_result`).  ``panel`` may be
    ``None`` only if no variant was handed over (then nothing is computed and the verdict is GL-012 (Pilot))."""
    say = log or (lambda _m: None)
    schema.validate_registered(registered)
    handed = [v for v in C.VARIANTS if pilot["variants"][v]["handover"]["handed_over"]]
    base: dict[str, Any] = {
        "schema": C.RUN_SCHEMA, "mode": "run", "registered_sha256": registered_sha256, "data_fingerprints": observed_fingerprints,
        "pilot": {"result_sha256": pilot.get("result_sha256"), "file_sha256": pilot.get("_file_sha256"), "handed": handed},
        "handed": handed,
        "not_handed": {v: pilot["variants"][v]["handover"]["reason"] for v in C.VARIANTS if v not in handed},
    }
    results: dict[str, Any] = {}
    for v in C.VARIANTS:
        if v in handed:
            continue
        ho = pilot["variants"][v]["handover"]
        results[C.ENTRY[v]] = {"entry": C.ENTRY[v], "variant": v, "computed": False, "p_max": 1.0, "reason": ho["reason"],
                               "verdict": {"verdict": C.PILOT_GL012, "labels": [ho["reason"], "p = 1 im BH-Nenner 4; nicht in m von F-WEEK (DEC-99 (7))"]}}
    if not handed:
        base.update({"results": results, "bh": fweek.bh_report({}), "fweek": None,
                     "hypothesis_verdict": {"verdict": C.PILOT_GL012,
                                            "label": "kein Eintrag uebergeben: kein Test, kein Verdikt; W1/W2 bleiben blind"},
                     "labels": ["GL-012 (Pilot)"]})
        base["result_sha256"] = artifacts.canonical_sha256(base)
        base["_series"] = {}
        return base

    checks.check_data_fingerprints(registered, observed_fingerprints)                              # P3
    cut_date = registered["seal"]["panel_cut_test"]
    cut, cut_report = panel_cut.cut_panel_days(panel, cut_date, limit=C.CUT_TEST)                   # P0''
    mx = panel_cut.assert_panel_max_date(cut, cut_date)
    say(f"panel cut at {cut_date}: {cut_report['n_days_removed']} days removed, max date {mx}")
    wk = wkl.build_weekly(cut, cut_date, with_turnover=True)
    rules = registered["rules"]
    mean_block, n_boot, seed = float(rules["mean_block"]), int(rules["n_boot"]), int(rules["seed"])
    n_perm = int(registered["fdr"]["n_perm"])                                                     # pinned == C.N_PERM by the schema
    wins = {wn: wkl.make_window(wk, wn) for wn in ("W1", "W2")}
    for wn, win in wins.items():
        checks.check_window_pins(win, registered)                                                   # P4
    null_cal = {wn: _null_recheck(win, registered, say) for wn, win in wins.items()}                # P6
    bounce_spread = float(rules["bounce_spread"])

    entry_results: dict[str, Any] = {}
    series: dict[str, Any] = {}
    p_by_entry: dict[str, float] = {}
    draws_by_window: dict[str, dict[str, np.ndarray]] = {}
    for wn, win in wins.items():                                                                    # one permutation pass per window
        say(f"  permutations {wn}: {n_perm} draws for {len(handed)} variant(s)")
        draws_by_window[wn] = permutation.block_permutation_draws(
            {v: win.chars[v] for v in handed}, win.returns, win.alive, win.beta8, n_perm=n_perm, block=int(registered["fdr"]["block_len"]),
            seed=int(registered["fdr"]["seed"]))
    for v in handed:
        sign = C.SIGN[C.DIRECTION[v]]
        entry = C.ENTRY[v]
        wpay: dict[str, Any] = {}
        wdet: dict[str, Any] = {}
        series[entry] = {}
        for wn, win in wins.items():
            fz = registered["windows"][wn]["frozen_v6"]
            res = fm8.window_ic(win, v)                                                              # P7 inside
            ic_w = res["ic_weekly"]
            mean_ic = float(res["mean_ic"])
            y = sign * mean_ic if math.isfinite(mean_ic) else float("nan")
            n_fin = int(np.isfinite(np.asarray(ic_w)).sum())
            if n_fin != win.w_judged:
                raise ArtifactError(f"{entry}/{wn}: {n_fin} finite weeks, expected {win.w_judged} -- NO VERDICT")
            se = est.se_rule(ic_w, float(fz["floor_fm8"]), win.w_judged, mean_block=mean_block, n_boot=n_boot, seed=seed, with_sha=True)
            thr_frozen = schema.threshold_frozen(registered, wn, v)
            bounce = None
            if v == "rev_gap":
                k_med = int(np.median(win.alive.sum(axis=1)))
                bf = wp13_run.bounce_fixture_ic(win.n_weeks, max(k_med, 10), spread=bounce_spread,
                                                sigma_true=float(registered["windows"][wn]["bounce_sigma_true"]), seed=seed,
                                                convention=C.CONVENTION)
                bounce = float(bf["ic_bounce"])
            perm_p = permutation.permutation_pvalue(y, draws_by_window[wn][v])
            p_norm = float(_NORM.cdf(-y / se["se"])) if (math.isfinite(y) and math.isfinite(se["se"]) and se["se"] > 0.0) else float("nan")
            perm_p["p_normal_approx_report_only"] = p_norm
            perm_p["null_sd_over_se_w"] = (perm_p.get("draws_sd", float("nan")) / se["se"]) if se["se"] > 0.0 else float("nan")
            liq = labels.liquidity_means(win, v, sign)
            wpay[wn] = {"y": y, "mean_ic": mean_ic, "se_w": se["se"], "q95": float(fz["q95"][v]), "ceiling_k4": float(fz["ceiling_k4"]),
                        "threshold_frozen": thr_frozen, "bounce_ic": bounce, "w_judged": win.w_judged}
            wdet[wn] = {"se_detail": {k: se[k] for k in ("floor_term", "sd_term", "stat_term", "sd_ic", "n_finite")},
                        "bootstrap_means_sha256": se["bootstrap_means_sha256"], "permutation": perm_p, "liquidity": liq,
                        "ic_weekly_sha256": est.series_sha256(ic_w), "k": wkl.k_summary(wkl.k_alive_series(win))}
            series[entry][wn] = {"ic": ic_w, "perm_draws": draws_by_window[wn][v]}
        payload = {"entry": entry, "variant": v, "direction": C.DIRECTION[v], "z_krit": float(C.Z_KRIT), "windows": wpay,
                   "constants": {"alpha": C.ALPHA, "w_judged": {wn: wins[wn].w_judged for wn in wins}, "n_boot": n_boot,
                                 "mean_block": mean_block, "seed": seed, "n_perm": n_perm, "block_len": int(registered["fdr"]["block_len"]),
                                 "panel_cut_test": cut_date,
                                 "frozen": {wn: {"e_se_rule": float(registered["windows"][wn]["frozen_v6"]["e_se_rule"][v]),
                                                 "null_mean": float(registered["windows"][wn]["frozen_v6"]["null_mean"][v]),
                                                 "q95": float(registered["windows"][wn]["frozen_v6"]["q95"][v]),
                                                 "ceiling_k4": float(registered["windows"][wn]["frozen_v6"]["ceiling_k4"]),
                                                 "floor_fm8": float(registered["windows"][wn]["frozen_v6"]["floor_fm8"])} for wn in wins}}}
        verdict = gate.evaluate(payload)
        p_max = max((wdet[wn]["permutation"]["p_value"] for wn in wins), default=float("nan"))
        p_by_entry[entry] = 1.0 if not math.isfinite(p_max) else p_max
        # report-only labels
        lab: list[str] = []
        for wn in wins:
            ratio = wdet[wn]["permutation"]["null_sd_over_se_w"]
            if math.isfinite(ratio) and ratio > PERM_NULL_SD_FLAG:
                lab.append(f"Permutations-Null in {wn} breiter als SE_W ({ratio:.2f} x): Block-Permutation der Outcome-Wochen "
                           "paart Charakteristik und eigene Rendite (mom4 / rev_gap) -- p konservativ; Normal-p report-only: "
                           f"{wdet[wn]['permutation']['p_normal_approx_report_only']:.4f}")
        for wn in wins:
            ybx = wdet[wn]["liquidity"]["y_without_b1"]
            t_w = verdict["per_window"][wn]["threshold_t"]
            if math.isfinite(ybx) and math.isfinite(t_w) and ybx < 0.5 * t_w:
                lab.append(f"Illiquiditaets-Artefakt in {wn}: Mittel ohne Bucket 1 {ybx:.5f} nicht jenseits 0,5 x T_W ({0.5 * t_w:.5f})")
        sv_key = {"mom1": "mom1_diff_in_ic_min_units", "rev_gap": "rev_gap_diff_in_ic_min_units"}.get(v)
        surv = None
        if sv_key:
            surv = {wn: float(registered["windows"][wn]["survivorship"][sv_key]) for wn in wins}
            lab.append("Survivorship-Etikett (report-only, synthetisch): " + ", ".join(f"{wn}={x:+.3f}" for wn, x in surv.items())
                       + " Schwellen-Einheiten")
        ho = pilot["variants"][v]["handover"]
        if ho.get("label_only_dec94"):
            lab.append(ho["label_only_dec94"])
        lab += ["zugelassen nur durch DEC-99 (Pilot-Prior)", "fm8-Skala (Daempfung ~25 %)"]
        verdict["labels"].extend(lab)
        entry_results[entry] = {"entry": entry, "variant": v, "computed": True, "payload": payload, "verdict": verdict,
                                "p_max": p_by_entry[entry], "details": wdet, "survivorship": surv,
                                "pilot": {"x_p": ho["x_p"], "se_p": ho["se_p"], "mu_sel": ho["mu_sel"], "m_star": ho["m_star"],
                                          "mde80_star": ho["mde80_star"]}}
        say(f"  {entry}: {verdict['verdict']} (p_max {p_by_entry[entry]:.4f})")
    results.update(entry_results)

    bh = fweek.bh_report({entry_results[e]["variant"]: p for e, p in p_by_entry.items()})
    for e, res in entry_results.items():
        res["verdict"]["bh_report_only"] = {"rejected": bool(bh["reject"].get(res["variant"])), "m": bh["m"], "alpha": bh["alpha"]}
    verdicts = {e: res["verdict"] for e, res in entry_results.items()}
    fw = fweek.apply_fweek(verdicts, p_by_entry, wave_p=wave_p)
    # end power (display only) for the number of tested entries incl. the wave and for m = 11
    m_tested = len(entry_results) + len(wave_p or {})
    for e, res in entry_results.items():
        ho = pilot["variants"][res["variant"]]["handover"]
        wins_pw = {wn: {"se_t": ho["per_window"][wn]["se_t"], "sd_t": ho["per_window"][wn]["sd_t"], "null_mean": ho["per_window"][wn]["null_mean"]}
                   for wn in handover.WINDOW_NAMES}
        res["end_power"] = {"at_pilot_point_m_tested": est.end_power(ho["pi_v"], m_tested, wins_pw),
                            "at_pilot_point_m_old_count_report_only": est.end_power(ho["pi_v"], C.FWEEK_DOUBLE_M, wins_pw)}
        if ho["mu_sel"] is not None:
            res["end_power"]["at_mu_sel_m_tested"] = est.end_power(ho["mu_sel"], m_tested, wins_pw)
    passed = [res["variant"] for res in entry_results.values() if res["verdict"]["verdict"] == "PASS"]
    hyp = {"verdict": "PASS" if passed else "DROP", "variants_pass": passed,
           "label": ("vorlaeufig bis F-WEEK am Wellenschluss geschlossen" if passed else None)}
    base.update({
        "panel": {"cut_date": cut_date, **cut_report, "max_date": mx, "last_week": wk.weeks[-1], "n_weeks": len(wk.weeks),
                  "n_symbols": len(wk.symbols)},
        "windows": {wn: wkl.window_geometry_report(win) for wn, win in wins.items()},
        "null_calibration": null_cal, "results": results, "bh": bh, "fweek": fw, "hypothesis_verdict": hyp,
        "parameters": {"mean_block": mean_block, "n_boot": n_boot, "seed": seed, "n_perm": n_perm, "z_krit": C.Z_KRIT,
                       "alpha": C.ALPHA, "wave_p": dict(wave_p or {}), "m_tested": m_tested},
        "not_computed": ["raw_ic", "lag_profile", "beta_calibration_ic", "persistence_null"],
    })
    base["result_sha256"] = artifacts.canonical_sha256(base)
    base["_series"] = series
    return base


# ----------------------------------------------------------------------------
# artifacts (DEC-53), round trip (T7), markdown
# ----------------------------------------------------------------------------

def verify_run_artifacts(out_dir: Path | str, report: dict[str, Any], registered: dict[str, Any]) -> dict[str, Any]:
    """T7: from the written series (+ seed) re-derive, bit for bit, the window mean, SE_W (floor, SD, stationary bootstrap and
    its replicate fingerprint), the permutation p (from the stored draws) and the gate verdict of every computed entry.
    Anything missing or different is :class:`ArtifactError` (NO VERDICT)."""
    out = Path(out_dir)
    fp_path = out / "h32_run_fingerprint.json"
    if not fp_path.is_file():
        raise ArtifactError("NO VERDICT: mandatory artifact h32_run_fingerprint.json missing (generator fingerprint)")
    fp = json.loads(fp_path.read_text(encoding="utf-8"))
    for key in ("seed", "code", "parameters", "entries", "result_sha256", "data_fingerprints", "panel_cut", "pilot_sha256"):
        if key not in fp:
            raise ArtifactError(f"NO VERDICT: generator fingerprint without field {key!r}")
    if not fp["code"].get("code_sha256"):
        raise ArtifactError("NO VERDICT: generator fingerprint without code hash")
    if fp["result_sha256"] != report["result_sha256"]:
        raise ArtifactError("NO VERDICT: result_sha256 of the fingerprint differs from the report")
    n = 0
    for entry, res in report["results"].items():
        if not res.get("computed"):
            continue
        for wn, w in res["payload"]["windows"].items():
            key = f"{entry}/{wn}"
            ic_path = out / f"h32_run_{entry}_{wn}_ic_weekly.csv"
            pd_path = out / f"h32_run_{entry}_{wn}_perm_draws.csv"
            for pth in (ic_path, pd_path):
                if not pth.is_file():
                    raise ArtifactError(f"NO VERDICT: mandatory artifact {pth.name} missing")
            ic_w, _ = artifacts.read_series_csv(ic_path)
            draws, _ = artifacts.read_series_csv(pd_path, value_name="y")
            fin = np.asarray(ic_w, dtype=np.float64)
            fin = fin[np.isfinite(fin)]
            sign = C.SIGN[C.DIRECTION[res["variant"]]]
            mean_ic = float(fin.mean())
            if mean_ic != w["mean_ic"] or sign * mean_ic != w["y"]:
                raise ArtifactError(f"NO VERDICT: mean IC from {ic_path.name} does not reproduce the payload")
            consts = res["payload"]["constants"]
            se = est.se_rule(ic_w, consts["frozen"][wn]["floor_fm8"], w["w_judged"], mean_block=consts["mean_block"],
                             n_boot=consts["n_boot"], seed=consts["seed"], with_sha=True)
            if se["se"] != w["se_w"] or se["bootstrap_means_sha256"] != res["details"][wn]["bootstrap_means_sha256"]:
                raise ArtifactError(f"NO VERDICT: SE_W / bootstrap fingerprint from {ic_path.name} do not reproduce the payload")
            pp = permutation.permutation_pvalue(w["y"], np.asarray(draws))
            if pp["p_value"] != res["details"][wn]["permutation"]["p_value"] or pp["draws_sha256"] != res["details"][wn]["permutation"]["draws_sha256"]:
                raise ArtifactError(f"NO VERDICT: permutation p from {pd_path.name} does not reproduce the payload")
            if fp["entries"][key]["ic_file_sha256"] != artifacts.sha256_file(ic_path) or fp["entries"][key]["perm_file_sha256"] != artifacts.sha256_file(pd_path):
                raise ArtifactError(f"NO VERDICT: artifact fingerprint {key} differs")
            n += 1
        v2 = gate.evaluate(res["payload"])
        sv = res["verdict"]
        for k in ("per_window", "gl012_kill", "kill_windows", "bounce_kill", "bounce_windows"):
            if artifacts.canonical_sha256(v2[k]) != artifacts.canonical_sha256(sv[k]):
                raise ArtifactError(f"NO VERDICT: the gate re-evaluation of {entry} differs in {k!r}")
        demoted = v2["verdict"] == "PASS" and sv["verdict"] == "DROP" and "F-WEEK-BY nicht bestanden" in sv["labels"]
        if sv["verdict"] != v2["verdict"] and not demoted:
            raise ArtifactError(f"NO VERDICT: the gate re-evaluation of {entry} gives {v2['verdict']}, the report {sv['verdict']}")
    return {"n_entry_windows_checked": n, "result_sha256": fp["result_sha256"]}


def render_run_markdown(report: dict[str, Any]) -> str:
    f = lambda x, nd=5: ("-" if x is None else ("nan" if x != x else f"{float(x):.{nd}f}"))   # noqa: E731
    hv = report["hypothesis_verdict"]
    lines = ["# H-32 Testlauf (Stufe T)", "", f"- Verdikt H-32: **{hv['verdict']}** {('(' + hv['label'] + ')') if hv.get('label') else ''}",
             f"- result_sha256: `{report['result_sha256']}`", f"- registrierte Datei sha256: `{report.get('registered_sha256')}`",
             f"- Pilot-Ergebnis sha256: `{report['pilot'].get('file_sha256')}`; uebergeben: {', '.join(report['handed']) or '-'}", ""]
    if report["handed"]:
        pn = report["panel"]
        lines += [f"- Panel-Schnitt {pn['cut_date']}, letzte Woche {pn['last_week']}, Daten bis {pn['max_date']}", "",
                  "## Eintraege", "", "| Eintrag | Verdikt | p (Max-p) | W1: y / SE / q95 | W2: y / SE / q95 | Etiketten |", "|---|---|---|---|---|---|"]
        for e, res in report["results"].items():
            if not res.get("computed"):
                lines.append(f"| {e} | {res['verdict']['verdict']} | 1 | - | - | {res['reason']} |")
                continue
            w1, w2 = res["payload"]["windows"]["W1"], res["payload"]["windows"]["W2"]
            lines.append(f"| {e} | {res['verdict']['verdict']} | {f(res['p_max'], 4)} | {f(w1['y'])} / {f(w1['se_w'])} / {f(w1['q95'])} | "
                         f"{f(w2['y'])} / {f(w2['se_w'])} / {f(w2['q95'])} | {' / '.join(res['verdict']['labels'])} |")
        fw = report["fweek"]
        if fw and fw["by"]:
            lines += ["", "## F-WEEK (BY, alpha 0,10, bindend am Wellenschluss)", "",
                      f"- m = {fw['by']['m']} (getestete Eintraege inkl. Welle), Einzel-Schranke {f(fw['by']['single_bound'], 5)}",
                      f"- Doppelausweis alte Zaehlung m = {fw['by_double_statement']['m']}: "
                      + ", ".join(f"{e}: {'abgelehnt' if r else 'nicht abgelehnt'}" for e, r in fw['by_double_statement']['reject'].items()
                                  if not e.startswith('p1_entry')),
                      f"- BH (report-only, Nenner {report['bh']['m']}): " + ", ".join(f"{v}: {r}" for v, r in report["bh"]["reject"].items())]
        lines += ["", "## Null-Nachrechnung (P6)", ""] + [f"- {wn}: innerhalb +-10 % ({len(c['rows'])} Konstanten)" for wn, c in report["null_calibration"].items()]
    else:
        lines += ["Kein Eintrag uebergeben: kein Test, W1/W2 bleiben blind."]
    lines += ["", "Kein Verdikt ohne die DEC-53-Artefakte (`h32_run_fingerprint.json`, Wochenserien, Permutationsziehungen).", ""]
    return "\n".join(lines)


def write_run_artifacts(out_dir: Path | str, report: dict[str, Any], registered: dict[str, Any], *,
                        pilot_sha256: str | None = None) -> dict[str, Any]:
    """DEC-53 artifacts in this order: weekly fm8 IC series and permutation draws per computed entry and window,
    ``h32_run_fingerprint.json`` (seed, bit generator, code hash, data fingerprints, panel cut date, pilot sha256), the round
    trip :func:`verify_run_artifacts` (an error means NO VERDICT and no result file), then ``h32_run.json`` / ``.md``."""
    out = Path(out_dir)
    artifacts.refuse_unsafe_path(out / "x", writing=True)
    out.mkdir(parents=True, exist_ok=True)
    public = {k: v for k, v in report.items() if k != "_series"}
    arts: dict[str, Any] = {}
    entries_fp: dict[str, Any] = {}
    for entry, wins in report.get("_series", {}).items():
        for wn, s in wins.items():
            a = artifacts.write_series_csv(out / f"h32_run_{entry}_{wn}_ic_weekly.csv", s["ic"])
            b = artifacts.write_series_csv(out / f"h32_run_{entry}_{wn}_perm_draws.csv", s["perm_draws"], value_name="y")
            arts[a["file"]], arts[b["file"]] = a["sha256"], b["sha256"]
            entries_fp[f"{entry}/{wn}"] = {"ic_file_sha256": a["sha256"], "perm_file_sha256": b["sha256"]}
    fp = {"schema": "H-32 run generator fingerprint (DEC-53)", "seed": public.get("parameters", {}).get("seed"),
          "parameters": public.get("parameters"), "code": artifacts.code_fingerprint(), "git_commit": artifacts.git_commit(),
          "data_fingerprints": public.get("data_fingerprints"), "registered_sha256": public.get("registered_sha256"),
          "panel_cut": (public.get("panel") or {}).get("cut_date"), "pilot_sha256": pilot_sha256,
          "entries": entries_fp, "result_sha256": public["result_sha256"]}
    art = artifacts.write_json(out / "h32_run_fingerprint.json", fp)
    arts[art["file"]] = art["sha256"]
    if public["handed"]:
        verify_run_artifacts(out, public, registered)                                  # may raise: NO VERDICT
    main = dict(public)
    main["artifacts"] = dict(arts)
    main["code"] = artifacts.code_fingerprint()
    j = artifacts.write_json(out / "h32_run.json", main)
    md = out / "h32_run.md"
    md.write_text(render_run_markdown(public), encoding="utf-8")
    return {"out_dir": str(out), "artifacts": arts, "json": j, "md": artifacts.sha256_file(md)}
