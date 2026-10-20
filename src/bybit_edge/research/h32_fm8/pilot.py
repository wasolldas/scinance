"""Stage P -- the pilot (``--pilot``, B-2, ERSTFASSUNG 1.7, 1.8, 2 "Pilot-Modus"): estimation, NOT judging.

Gates in this order, each a loud fail before the next step (rc 1, NO HAND-OVER for any variant):

  PP0  start lock: sha256 of the registered YAML (CLI, before the panel is touched);
  PP0' exactly-one-pilot lock (``checks.check_rerun_lock``, CLI, before the panel is touched);
  PP1  schema (``schema.validate_registered``);
  PP2  data fingerprints of the loaded panel == YAML;
  PP2' panel cut <= ``seal.panel_cut_pilot`` (2024-06-30) BEFORE weekly returns, characteristics or betas, with the
       maximum-date guard;
  PP3  pins (w_pilot 114, block 4, n_boot >= 1.000, seed 53, K_fm8 series == the one the v6 constants were frozen on);
  PP4  seal guard: the outcome weeks of the pilot window are 2022-04-25..2024-06-24 and nothing else (``fm8.window_ic``);
       no raw IC, no lag profile, no beta-calibration IC exist;
  PP5  DEC-53 artifacts written and verified by a round trip BEFORE the hand-over is published (``write_pilot_artifacts``).

Per variant: mean fm8 IC in direction (x_P), SD, SE_P by rule P-1 (4), t_P, 80 % band, F2_real / c_real, hand-over rule U
(``handover.evaluate_handover``), regime P-1 and A3 practice, the selection-adjusted ``mu_sel`` with the joint power at it
(mandatory double statement, DEC-99 (3)), end power after F-WEEK for the number of handed-over variants and for m = 11.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import artifacts, checks, fm8, handover, labels, panel_cut, schema
from . import constants as C
from . import estimators as est
from . import weekly as wkl
from .errors import ArtifactError, H32Abort

__all__ = ["run_pilot", "write_pilot_artifacts", "verify_pilot_artifacts", "render_pilot_markdown", "PILOT_LABELS"]

PILOT_LABELS = [
    "Pilot, nicht urteilstragend; Screening, nie Konfirmation (C.17/C.18)",
    "zugelassen nur durch DEC-99 (Pilot-Prior)",
    "fm8-Skala (Daempfung ~25 %): ein beta-unabhaengiges Signal erscheint zu ~75 %",
    "Pilot aus anderem Marktregime (2022-2024, Aera-Uebergang ~Mitte 2024)",
    "Pilotabschnitt nach der Uebergabe fuer jede korrelierte Statistik verbraucht (DEC-99 (5))",
]


def _boot_rules(registered: dict[str, Any]) -> tuple[float, int, int]:
    r = registered["rules"]
    return float(r["mean_block"]), int(r["n_boot"]), int(r["seed"])


def run_pilot(panel: dict[str, Any], registered: dict[str, Any], observed_fingerprints: dict[str, Any] | None, *,
              registered_sha256: str | None = None, log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """The pilot on an UNCUT daily union panel (the cut happens here, after the fingerprint check).  Returns the report
    (``result_sha256`` over everything that is a pilot result; ``_series`` carries the weekly series for the artifacts)."""
    say = log or (lambda _m: None)
    schema.validate_registered(registered)                                           # PP1
    checks.check_data_fingerprints(registered, observed_fingerprints)               # PP2
    cut_date = registered["seal"]["panel_cut_pilot"]
    cut, cut_report = panel_cut.cut_panel_days(panel, cut_date, limit=C.CUT_PILOT)  # PP2'
    mx = panel_cut.assert_panel_max_date(cut, cut_date)
    say(f"panel cut at {cut_date}: {cut_report['n_days_removed']} days removed, max date {mx}")
    wk = wkl.build_weekly(cut, cut_date, with_turnover=True)
    pw = registered["pilot_window"]
    win = wkl.make_window(wk, "P", pw["start"], pw["end"])
    checks.check_window_pins(win, registered)                                        # PP3
    mean_block, n_boot, seed = _boot_rules(registered)
    k_sum = wkl.k_summary(wkl.k_alive_series(win))
    say(f"pilot window {win.weeks[0]}..{win.weeks[-1]}: w_judged {win.w_judged}, K {k_sum}")

    variants: dict[str, Any] = {}
    series: dict[str, Any] = {}
    handed: list[str] = []
    not_handed: dict[str, str] = {}
    for v in C.VARIANTS:
        sign = C.SIGN[C.DIRECTION[v]]
        res = fm8.window_ic(win, v)                                                  # PP4 inside
        ic_w, k_w = res["ic_weekly"], res["k_weekly"]
        n_fin = int(np.isfinite(np.asarray(ic_w)).sum())
        if n_fin != win.w_judged:
            raise H32Abort(f"variant {v}: {n_fin} finite pilot weeks, expected {win.w_judged} -- NO HAND-OVER")
        stats = est.pilot_statistics(ic_w, k_w, sign, mean_block=mean_block, n_boot=n_boot, seed=seed)
        consts = handover.handover_constants(registered, v)
        ho = handover.evaluate_handover(stats, consts)
        liq = labels.liquidity_means(win, v, sign) if win.turnover_trail is not None else None
        variants[v] = {"entry": C.ENTRY[v], "direction": C.DIRECTION[v], "sign": sign, "stats": stats, "handover": ho,
                       "liquidity_report_only": liq, "ic_weekly_sha256": est.series_sha256(ic_w), "n_finite_weeks": n_fin}
        series[v] = {"ic": ic_w, "k": k_w}
        (handed if ho["handed_over"] else []).append(v)
        if not ho["handed_over"]:
            not_handed[v] = ho["reason"]
        say(f"  {v}: x_P {stats['x_p']:.5f} SE_P {stats['se_p']:.5f} t_P {stats['t_p']:.2f} -> {ho['status']}")

    end_power: dict[str, Any] = {}
    n_h = len(handed)
    for v in handed:
        ho = variants[v]["handover"]
        wins = {wn: {"se_t": ho["per_window"][wn]["se_t"], "sd_t": ho["per_window"][wn]["sd_t"],
                     "null_mean": ho["per_window"][wn]["null_mean"]} for wn in handover.WINDOW_NAMES}
        end_power[v] = {"at_pilot_point": {"m_tested": est.end_power(ho["pi_v"], n_h, wins),
                                           "m_old_count_report_only": est.end_power(ho["pi_v"], C.FWEEK_DOUBLE_M, wins)}}
        if ho["mu_sel"] is not None:
            end_power[v]["at_mu_sel"] = {"m_tested": est.end_power(ho["mu_sel"], n_h, wins),
                                         "m_old_count_report_only": est.end_power(ho["mu_sel"], C.FWEEK_DOUBLE_M, wins)}
    core: dict[str, Any] = {
        "schema": C.PILOT_SCHEMA, "mode": "pilot", "registered_sha256": registered_sha256,
        "data_fingerprints": observed_fingerprints,
        "panel": {"cut_date": cut_date, **cut_report, "max_date": mx, "last_week": wk.weeks[-1], "n_weeks": len(wk.weeks),
                  "n_symbols": len(wk.symbols)},
        "window": {**wkl.window_geometry_report(win), "w_pilot": win.w_judged, "k": k_sum,
                   "k_fm8_series_sha256": wkl.int_series_sha256(wkl.k_fm8_series(win))},
        "parameters": {"mean_block": mean_block, "n_boot": n_boot, "seed": seed, "z_krit": C.Z_KRIT, "z_power": C.Z_POWER,
                       "t_min": C.T_MIN, "band_z": C.BAND_Z, "handover_version": C.HANDOVER_VERSION},
        "variants": variants, "handed": handed, "not_handed": not_handed, "end_power": end_power,
        "status": C.PILOT_HANDED if handed else C.PILOT_GL012, "labels": list(PILOT_LABELS),
    }
    core["result_sha256"] = artifacts.canonical_sha256(core)
    core["_series"] = series
    return core


# ----------------------------------------------------------------------------
# artifacts (DEC-53), round trip (T7), markdown
# ----------------------------------------------------------------------------

def verify_pilot_artifacts(out_dir: Path | str, prefix: str, report: dict[str, Any], registered: dict[str, Any]) -> dict[str, Any]:
    """T7 round trip: the series files and the seed reproduce x_P, SE_P, t_P, F2_real, c_real and the hand-over of every
    variant BIT FOR BIT; anything missing or different is :class:`ArtifactError` (NO HAND-OVER)."""
    out = Path(out_dir)
    fp_path = out / f"{prefix}_fingerprint.json"
    if not fp_path.is_file():
        raise ArtifactError("NO HAND-OVER: mandatory artifact " + fp_path.name + " missing")
    import json
    fp = json.loads(fp_path.read_text(encoding="utf-8"))
    for key in ("seed", "code", "parameters", "variants", "result_sha256"):
        if key not in fp:
            raise ArtifactError(f"NO HAND-OVER: generator fingerprint without field {key!r}")
    if fp["result_sha256"] != report["result_sha256"]:
        raise ArtifactError("NO HAND-OVER: result_sha256 of the fingerprint differs from the report")
    mean_block, n_boot, seed = _boot_rules(registered)
    n_checked = 0
    for v in C.VARIANTS:
        path = out / f"{prefix}_{v}_P_ic_weekly.csv"
        if not path.is_file():
            raise ArtifactError(f"NO HAND-OVER: mandatory artifact {path.name} (weekly fm8 IC series) missing")
        ic_w, k_w = artifacts.read_series_csv(path)
        if k_w is None:
            raise ArtifactError(f"NO HAND-OVER: {path.name} carries no K column")
        if artifacts.sha256_file(path) != fp["variants"][v]["series_file_sha256"]:
            raise ArtifactError(f"NO HAND-OVER: {path.name} differs from the fingerprint")
        stats = est.pilot_statistics(ic_w, k_w, C.SIGN[C.DIRECTION[v]], mean_block=mean_block, n_boot=n_boot, seed=seed)
        rep = report["variants"][v]["stats"]
        for key in ("x_p", "sd_p", "se_p", "t_p", "f2_real", "c_real", "bootstrap_means_sha256", "w_p"):
            if stats[key] != rep[key]:
                raise ArtifactError(f"NO HAND-OVER: {path.name} does not reproduce {key} ({stats[key]!r} != {rep[key]!r})")
        ho = handover.evaluate_handover(stats, handover.handover_constants(registered, v))
        if ho != report["variants"][v]["handover"]:
            raise ArtifactError(f"NO HAND-OVER: the hand-over of {v} is not reproduced by the artifacts")
        n_checked += 1
    return {"n_variants_checked": n_checked, "result_sha256": fp["result_sha256"]}


def render_pilot_markdown(report: dict[str, Any]) -> str:
    f = lambda x, nd=5: ("-" if x is None else ("nan" if x != x else f"{float(x):.{nd}f}"))   # noqa: E731
    lines = ["# H-32 Pilot (Stufe P) -- Schaetzung, nicht urteilstragend", "",
             f"- Status: **{report['status']}** (uebergeben: {', '.join(report['handed']) or '-'})",
             f"- result_sha256: `{report['result_sha256']}`", f"- registrierte Datei sha256: `{report.get('registered_sha256')}`",
             f"- Panel-Schnitt {report['panel']['cut_date']} (letzte Woche {report['panel']['last_week']}), "
             f"Fenster {report['window']['first_formation_week']}..{report['window']['last_outcome_week']}, "
             f"w_pilot {report['window']['w_pilot']}, K {report['window']['k']}",
             "", "## Je Variante", "",
             "| Variante | x_P | SD_P | SE_P | t_P | 80-%-Band | F2_real | c_real | m* | MDE80* | (i) | (ii) | (iii) | Status |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in C.VARIANTS:
        s, h = report["variants"][v]["stats"], report["variants"][v]["handover"]
        lines.append(f"| {v} | {f(s['x_p'])} | {f(s['sd_p'])} | {f(s['se_p'])} | {f(s['t_p'], 2)} | "
                     f"[{f(s['band80_normal'][0])}, {f(s['band80_normal'][1])}] | {f(s['f2_real'], 6)} | {f(s['c_real'], 3)} | "
                     f"{f(h['m_star'])} | {f(h['mde80_star'])} | {h['conditions']['i']} | {h['conditions']['ii']} | "
                     f"{h['conditions']['iii']} | {h['status']} |")
    lines += ["", "## Pflicht-Doppelausweis (DEC-99 (3)) und Zuordnung (nur uebergebene Varianten)", "",
              "| Variante | Regime P-1 | Regime A3-Praxis | mu_sel | gemeinsame Power am Punkt | gemeinsame Power an mu_sel |",
              "|---|---|---|---|---|---|"]
    for v in report["handed"]:
        h = report["variants"][v]["handover"]
        lines.append(f"| {v} | {h['regime_p1']['regime']} | {h['regime_a3_practice']['regime']}"
                     f"{' (' + h['label_only_dec94'] + ')' if h['label_only_dec94'] else ''} | {f(h['mu_sel'])} | "
                     f"{f(h['regime_p1']['window_power_joint_product'], 3)} | "
                     f"{f((h['power_at_mu_sel'] or {}).get('joint'), 3)} ({(h['power_at_mu_sel'] or {}).get('regime_p1')} / "
                     f"{(h['power_at_mu_sel'] or {}).get('regime_a3_practice')}) |")
    if not report["handed"]:
        lines.append("| (keine Variante uebergeben) | | | | | |")
    lines += ["", "## Nicht uebergebene Varianten", ""]
    for v, why in report["not_handed"].items():
        lines.append(f"- {v}: {why} (p = 1 im BH-Nenner 4; nicht in m von F-WEEK)")
    if not report["not_handed"]:
        lines.append("- (alle vier uebergeben)")
    lines += ["", "## Etiketten", ""] + [f"- {x}" for x in report["labels"]]
    lines += ["", "Die Uebergabe und `result_sha256` sind vom Orchestrator festzuhalten (DEC-/GL-Vermerk), bevor ein Testfenster "
              "gerechnet wird.", ""]
    return "\n".join(lines)


def write_pilot_artifacts(out_dir: Path | str, report: dict[str, Any], registered: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    """DEC-53 artifacts in this order: weekly fm8 IC series per variant (CSV with K), generator fingerprint, round-trip
    verification (:func:`verify_pilot_artifacts`; an error means NO HAND-OVER and no result file), then ``<prefix>.json``,
    ``<prefix>.md`` and ``<prefix>.sha256``.  ``lock`` is the :func:`checks.check_rerun_lock` result; the lock is re-checked
    right before writing and nothing earlier is overwritten."""
    out = Path(out_dir)
    artifacts.refuse_unsafe_path(out / "x", writing=True)
    checks.check_rerun_lock(out, registered, lock.get("rerun_dec"))                 # belt and braces
    prefix = lock["prefix"]
    out.mkdir(parents=True, exist_ok=True)
    arts: dict[str, Any] = {}
    series = report["_series"]
    fp_variants: dict[str, Any] = {}
    for v in C.VARIANTS:
        art = artifacts.write_series_csv(out / f"{prefix}_{v}_P_ic_weekly.csv", series[v]["ic"], series[v]["k"])
        arts[art["file"]] = art["sha256"]
        fp_variants[v] = {"series_file_sha256": art["sha256"], "series_float_sha256": est.series_sha256(series[v]["ic"]),
                          "bootstrap_means_sha256": report["variants"][v]["stats"]["bootstrap_means_sha256"]}
    public = {k: v for k, v in report.items() if k != "_series"}
    fp = {"schema": "H-32 pilot generator fingerprint (DEC-53)", "seed": report["parameters"]["seed"],
          "parameters": report["parameters"], "code": artifacts.code_fingerprint(), "git_commit": artifacts.git_commit(),
          "data_fingerprints": report["data_fingerprints"], "registered_sha256": report["registered_sha256"],
          "panel_cut": report["panel"]["cut_date"], "variants": fp_variants, "result_sha256": report["result_sha256"],
          "rerun_dec": lock.get("rerun_dec")}
    art = artifacts.write_json(out / f"{prefix}_fingerprint.json", fp)
    arts[art["file"]] = art["sha256"]
    verify_pilot_artifacts(out, prefix, public, registered)                           # may raise: NO HAND-OVER
    main = dict(public)
    main["artifacts"] = dict(arts)
    main["code"] = artifacts.code_fingerprint()
    main["rerun"] = {"rerun_dec": lock.get("rerun_dec"), "earlier_files": lock.get("earlier"),
                     "registered_pilot_result_sha256": lock.get("registered_pilot_result_sha256")} if lock.get("rerun") else None
    j = artifacts.write_json(out / f"{prefix}.json", main)
    md = out / f"{prefix}.md"
    md.write_text(render_pilot_markdown(public), encoding="utf-8")
    sha_path = out / f"{prefix}.sha256"
    sha_path.write_text(f"{j['sha256']}  {prefix}.json\n", encoding="utf-8")
    return {"out_dir": str(out), "prefix": prefix, "result_json": j, "artifacts": arts, "md": artifacts.sha256_file(md)}
