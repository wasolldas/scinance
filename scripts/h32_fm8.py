#!/usr/bin/env python3
"""H-32 Runner (A3-fm8, Klasse W, kapitalfrei): Zweistufen-Treiber fuer den beta-neutralen Querschnitts-IC
(DEC-99, DEC-94, DEC-96 E3, DEC-85/87/89, DEC-53).  Additiv: Paket ``bybit_edge.research.h32_fm8``; ``wp13_xsec`` und
``wp7_universe`` werden nur importiert.

Fuenf Modi, genau EINEN waehlen.  Jeder Modus, der Realdaten liest, prueft vorher seine Sperren; das Panel wird nach der
Fingerprint-Pruefung und VOR jeder Rechnung auf das Stichtagsdatum geschnitten (Maximaldatum-Waechter).

  python scripts/h32_fm8.py --prelaunch --panel-base data/panel_1d --delisted-base data/panel_1d_delisted --out DIR
        [--cut-date 2026-06-28] [--n-reps 1000] [--p-reps R] [--n-boot 1000] [--seed 53]
        [--v5e-reference state/registered/h28_h30_v3.yaml] [--stress-rel P] [--stress-abs P]
    Vorlauf v6, outcome-frei: Fenster P / W1 / W2, faktorerhaltende Null mit 8 Beta-Vorlaufwochen (K = 4, driftfrei und Drift
    0,002), Kalibrierung je Fenster (W2 neu auf dem geschnittenen Fenster, W1 als Determinismus-Kontrolle gegen v5e, P nur
    stress und ohne Mittel), eingefrorene Konstanten (sd_week, se_mean, e_se_rule, null_mean, q95, ceiling_k4, floor_fm8,
    v_fm8, K_fm8-Reihen, m_P) und die Replikat-Fenstermittel der Null fuer p (h32_prelaunch_p_replicates.json, DEC-53; je
    Fenster/Variante die Zelle mit dem groesseren Null-Mittel; --p-reps > --n-reps = feinere p-Aufloesung, z. B. 10000).
    Berechnet NIE eine reale Charakteristik-gegen-Outcome-IC.

  python scripts/h32_fm8.py --emit-template DIR/h32_prelaunch.json OUT.yaml [--spread-census scinance3-impl/state/runs/wp7_20260921/spread_census.json]
    schreibt das Skelett von state/registered/h32_v1.yaml (kein Panel-Zugriff, keine Registrierung).

  python scripts/h32_fm8.py --pilot --registered Y.yaml --registered-sha256 SHA --panel-base ... --delisted-base ... --out DIR
        [--pilot-rerun-dec DEC-nn]
    Stufe P (Schaetzung, nicht urteilstragend): Startsperre (sha256 der YAML), Genau-ein-Pilot-Sperre (ein zweiter Lauf nur mit
    --pilot-rerun-dec nach nachgewiesenem Code-/Datenfehler per DEC; kein Force-Flag), Panel-Schnitt <= 2024-06-30, je Variante
    x_P, SE_P (P-1 (4)), t_P, 80-%-Band, Uebergaberegel U (mechanisch), mu_sel als Pflicht-Doppelausweis, DEC-53-Artefakte,
    h32_pilot.json + sha256. rc 0 auch bei "GL-012 (Pilot)" (kein Eintrag uebergeben ist ein Ergebnis); rc 1 bei jedem Abbruch.

  python scripts/h32_fm8.py --positive-control --registered Y.yaml --registered-sha256 SHA --pilot-result h32_pilot.json
        --pilot-result-sha256 SHA --panel-base ... --delisted-base ... --out DIR
    PRD 3.3.8, ALLEIN und VOR dem Test: synthetische Renditen auf der realen Wochenform von W1/W2 (nur Wochenraster, PIT-Masken,
    returns_valid; Panel <= 2026-06-28), Welt an F2_real kalibriert, Injektion auf den REALISIERTEN Effekt, Urteils-Seeds 53..252.
    rc 0 nur bei BESTANDEN, 3 bei NICHT BESTANDEN, 1 bei Abbruch.

  python scripts/h32_fm8.py --run --registered Y.yaml --registered-sha256 SHA --pilot-result h32_pilot.json --pilot-result-sha256 SHA
        --p-replicates DIR/h32_prelaunch_p_replicates.json --panel-base ... --delisted-base ... --out DIR
        [--wave-p NAME=P[,NAME=P...]]
    Stufe T, nur uebergebene Varianten: Pilot-Sperre (Uebergabe wird bitgleich nachgerechnet), Replikat-Sperre (sha256 =
    fdr.replicates_sha256), Panel-Schnitt <= 2026-06-28, Null-Nachrechnung (+-10 %), Gate als reine Funktion, bindendes p aus
    den gepinnten Null-Replikaten (Max-p ueber W1/W2); Blockpermutation (10.000) und Normalnaeherung report-only; BH (Nenner 4,
    report-only), F-WEEK (BY, m = getestete Eintraege; Doppelausweis m = 11), DEC-53-Artefakte vor dem Verdikt. rc 1 = KEIN VERDIKT.

DEC-100 (Panel-Vollstaendigkeit): der Delisted-Baum (``--delisted-base``) kommt aus dem Data-Harvest-Register und den
Backfill-Partitionen (``scripts/h32_build_delisted_tree.py``); jeder Modus, der das Panel liest, misst zusaetzlich
``data_fingerprints.delisting_register_sha256`` (sha256 der Register-Kopie ``delisting_register.csv`` im Baum) und prueft den
Baum gegen seine ``delisted_tree_fingerprint.json``; die Registrierung pinnt den Wert.

Zugangsdaten nie hier: der Panel-Bezug laeuft ueber die Harvest-Exporte (Umgebungs-Secrets), nie ueber diese Datei.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.h32_fm8 import (artifacts, checks, delisted_tree, panel_cut, pilot as pilot_mod, pnull,  # noqa: E402
                                         positive_control as pc_mod, schema, testrun, vorlauf)
from bybit_edge.research.h32_fm8 import constants as C  # noqa: E402
from bybit_edge.research.h32_fm8.errors import H32Abort  # noqa: E402
from bybit_edge.research.wp13_xsec import nulls  # noqa: E402
from bybit_edge.research.wp7_universe import panel_load, panel_store  # noqa: E402

DEFAULT_SPREAD_CENSUS = "scinance3-impl/state/runs/wp7_20260921/spread_census.json"
DEFAULT_STRESS_REL = "scinance3-impl/state/runs/stress_rel.json"
DEFAULT_STRESS_ABS = "scinance3-impl/state/runs/stress_abs.json"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------
# panel loading (the seam tests replace) and fingerprints
# ----------------------------------------------------------------------------

def data_fingerprints(a: argparse.Namespace, panel: dict, delisted_base: Path, delisting_dates_path: Path, as_of: date) -> dict:
    """The two fingerprints of the panel actually loaded (union range over the FILES, sha256 of ``delisting_dates.json``);
    measured on the files BEFORE the panel cut.  Read-only."""
    surv_syms = [sym for sym, dl in zip(panel["symbols"], panel["is_delisted"]) if not dl]
    fp = panel_load.union_range_fingerprint(a.panel_base, delisted_base, surv_syms, panel["delisted_symbols"],
                                            year_start=a.start_year, year_end=a.end_year, as_of=as_of)
    tree = delisted_tree.observed_tree_fingerprints(delisted_base)             # DEC-100; raises if the tree differs from its fingerprint file
    return {"union_range_fingerprint": fp["sha256"], "delisting_dates_sha256": panel_load.sha256_file(delisting_dates_path),
            "delisting_register_sha256": tree["delisting_register_sha256"], "delisted_tree_sha256": tree["delisted_tree_sha256"],
            "union_range_detail": {"year_range": fp["year_range"], "n_partitions": fp["n_partitions"], "n_symbols": len(fp["symbols"]),
                                   "as_of": as_of.isoformat()}}


def load_union_panel(a: argparse.Namespace):
    """Load the UNCUT daily union panel and measure its fingerprints.  Returns ``(panel, observed)`` or ``None`` after logging
    the loud fail.  This is the single seam to the data; the cut happens in the library, after the fingerprint check."""
    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    if not manifest.is_file():
        log(f"FEHLER: kein Manifest unter {manifest}")
        return None
    delisted_base = Path(a.delisted_base)
    delisted_manifest = Path(a.delisted_manifest) if a.delisted_manifest else delisted_base / "panel_manifest.sqlite"
    dd_path = Path(a.delisting_dates) if a.delisting_dates else delisted_base / "delisting_dates.json"
    if not delisted_manifest.is_file():
        log(f"FEHLER: kein delistetes Manifest unter {delisted_manifest}")
        return None
    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    log(f"Union-Panel laden (as_of={as_of.isoformat()}, allow_partial={bool(a.allow_partial)})")
    try:
        symbols = panel_load.load_panel_symbols(manifest)
        panel = panel_load.load_panel_union(a.panel_base, manifest, delisted_base, delisted_manifest, year_start=a.start_year,
                                            year_end=a.end_year, as_of=as_of, delisting_dates_path=dd_path, symbols=symbols,
                                            allow_partial=a.allow_partial)
    except (panel_store.PanelStoreError, panel_load.PanelLoadError) as exc:
        log(f"FEHLER (loud fail): {exc}")
        return None
    try:
        observed = data_fingerprints(a, panel, delisted_base, dd_path, as_of)
    except H32Abort as exc:
        log(f"FEHLER (loud fail): {exc}")
        return None
    log(f"  {len(panel['symbols'])} Symbole, {len(panel['dates'])} Tage; union_range={observed['union_range_fingerprint']}; "
        f"delisting_register={observed['delisting_register_sha256']}")
    return panel, observed


def _start_lock(a: argparse.Namespace, flag: str):
    """PP0 / P0: ``--registered`` exists and ``--registered-sha256`` equals its sha256 -- BEFORE any panel byte is read."""
    path = Path(a.registered)
    if not path.is_file():
        log(f"FEHLER: keine registrierte Datei unter {path}")
        return None
    actual = artifacts.sha256_file(path)
    if not a.registered_sha256:
        log(f"FEHLER (Startsperre): --registered-sha256 ist Pflicht fuer {flag}. sha256 der angegebenen Datei: {actual}")
        return None
    if a.registered_sha256.lower() != actual.lower():
        log(f"FEHLER (Startsperre): --registered-sha256 ({a.registered_sha256}) stimmt NICHT mit dem sha256 von {path} ({actual}) ueberein.")
        return None
    log(f"[Startsperre bestanden] {path} sha256={actual}")
    return path, actual


def _load_registered(path: Path):
    try:
        registered = schema.load_registered_yaml(path)
        schema.validate_registered(registered)
    except (H32Abort, ValueError, yaml.YAMLError) as exc:
        log(f"FEHLER (registrierte YAML): {exc}")
        return None
    return registered


def read_bounce_spread(census_path: Path) -> float:
    """DEC-89 E1: median perp spread of decile D10 (bp) / 1e4 from the WP-7 spread census."""
    data = json.loads(Path(census_path).read_text(encoding="utf-8"))
    d10 = next((d for d in (data.get("deciles") or []) if d.get("decile") == 10), None)
    bp = None if d10 is None else d10.get("perp_spread_bp_median")
    if not (isinstance(bp, (int, float)) and not isinstance(bp, bool) and bp == bp and 0.0 < float(bp) < float("inf")):
        raise ValueError(f"Spread-Zensus {census_path}: kein endlicher positiver deciles[decile=10].perp_spread_bp_median")
    return round(float(bp) / 1e4, 12)


def _resolve_repo_path(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute() or p.exists():
        return p
    return Path(__file__).resolve().parents[1] / p


# ----------------------------------------------------------------------------
# modes
# ----------------------------------------------------------------------------

def cmd_prelaunch(a: argparse.Namespace) -> int:
    try:
        panel_cut.check_cut_date(a.cut_date, limit=C.CUT_TEST)       # refuses a cut date inside the blind period BEFORE loading
    except H32Abort as exc:
        log(f"FEHLER (Panel-Schnitt): {exc}")
        return 1
    ref = None
    if a.v5e_reference:
        try:
            ref = yaml.safe_load(Path(a.v5e_reference).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            log(f"FEHLER: v5e-Referenz nicht lesbar: {exc}")
            return 1
    loaded = load_union_panel(a)
    if loaded is None:
        return 1
    panel, observed = loaded
    ck = dict(search_n_reps=a.calibration_search_n_reps, search_rel_tol=a.calibration_search_rel_tol,
              search_max_iter=a.calibration_search_max_iter, gegenprobe_n_reps=a.gegenprobe_n_reps,
              gegenprobe_rel_tol=a.gegenprobe_rel_tol, gegenprobe_z_max=a.gegenprobe_z_max,
              gegenprobe_market_check=not a.no_gegenprobe_market_check)
    try:
        if a.n_reps < C.N_REPS_MIN or a.n_boot < C.N_BOOT_MIN:
            log(f"HINWEIS: n_reps={a.n_reps} / n_boot={a.n_boot} unter den registrierbaren Mindestwerten "
                f"({C.N_REPS_MIN} / {C.N_BOOT_MIN}); die Modi --pilot/--run lehnen ein so erzeugtes Skelett ab.")
        report = vorlauf.assemble_prelaunch(
            panel, observed, cut_date=a.cut_date, n_reps=a.n_reps, n_boot=a.n_boot, seed=a.seed, calibration_kwargs=ck,
            stress_rel_path=a.stress_rel or None, stress_abs_path=a.stress_abs or None, v5e_reference=ref, log=log,
            p_reps=a.p_reps or None)
        out = vorlauf.write_prelaunch_artifacts(a.out, report)
    except (H32Abort, ValueError, nulls.FactorShareCalibrationError) as exc:
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEIN VORLAUF-ERGEBNIS.")
        return 1
    for name, art in out["artifacts"].items():
        log(f"  {name}: {art['file']} sha256={art['sha256']}")
    log(f"Vorlauf v6 geschrieben: {out['out_dir']} (result_sha256={report['result_sha256']})")
    log("KEIN VERDIKT -- der Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung.")
    return 0


def cmd_emit_template(prelaunch_json: str, out_yaml: str, spread_census: str = DEFAULT_SPREAD_CENSUS) -> int:
    src = Path(prelaunch_json)
    dst = Path(out_yaml)
    if "data/harvest" in dst.as_posix():
        log(f"FEHLER: schreibe nie unter data/harvest: {dst}")
        return 1
    if not src.is_file():
        log(f"FEHLER: kein Vorlauf-Artefakt unter {src}")
        return 1
    census = _resolve_repo_path(spread_census)
    if not census.is_file():
        log(f"FEHLER: kein Spread-Zensus unter {census} (DEC-89 E1: rules.bounce_spread kommt aus der Messung)")
        return 1
    try:
        spread = read_bounce_spread(census)
        report = json.loads(src.read_text(encoding="utf-8"))
        template = vorlauf.build_template(report, bounce_spread=spread)
        text = vorlauf.template_yaml_text(template, report, source_sha256=artifacts.sha256_file(src))
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        log(f"FEHLER (Vorlage): {exc}")
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    log(f"Quelle: {src} sha256={artifacts.sha256_file(src)}")
    log(f"Registrierungs-Vorlage geschrieben: {dst} sha256={artifacts.sha256_file(dst)}")
    log("Pruefung Pflicht: alle Werte, Uebergaberegel U und die Fingerprints vor der Registrierung bestaetigen (Registrierung nur durch den Orchestrator).")
    return 0


def cmd_pilot(a: argparse.Namespace) -> int:
    lock = _start_lock(a, "--pilot")
    if lock is None:
        return 1
    registered_path, sha = lock
    registered = _load_registered(registered_path)
    if registered is None:
        return 1
    try:
        rerun = checks.check_rerun_lock(a.out, registered, a.pilot_rerun_dec)          # PP0' -- before the panel
    except H32Abort as exc:
        log(f"FEHLER (Genau-ein-Pilot-Sperre): {exc}\nKEINE UEBERGABE.")
        return 1
    loaded = load_union_panel(a)
    if loaded is None:
        return 1
    panel, observed = loaded
    try:
        report = pilot_mod.run_pilot(panel, registered, observed, registered_sha256=sha, log=log)
        written = pilot_mod.write_pilot_artifacts(a.out, report, registered, rerun)
    except (H32Abort, ValueError) as exc:
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEINE UEBERGABE.")
        return 1
    for v in C.VARIANTS:
        s, h = report["variants"][v]["stats"], report["variants"][v]["handover"]
        log(f"  {v}: x_P={s['x_p']:.6f} SE_P={s['se_p']:.6f} t_P={s['t_p']:.2f} -> {h['status']}")
    log(f"Pilot-Status: {report['status']} (uebergeben: {report['handed']})")
    for name, h in written["artifacts"].items():
        log(f"  {name}: sha256={h}")
    log(f"Pilot-Ergebnis: {written['out_dir']}/{written['prefix']}.json sha256={written['result_json']['sha256']} "
        f"(result_sha256={report['result_sha256']})")
    log("Das Pilot-Ergebnis und die Uebergabe sind vom Orchestrator festzuhalten (DEC-/GL-Vermerk), bevor ein Testfenster gerechnet wird.")
    return 0


def _pilot_lock(a: argparse.Namespace, registered: dict, sha: str):
    if not a.pilot_result or not a.pilot_result_sha256:
        log("FEHLER (Pilot-Sperre): --pilot-result und --pilot-result-sha256 sind Pflicht.")
        return None
    try:
        return testrun.load_pilot_result(a.pilot_result, a.pilot_result_sha256, registered, sha)
    except (H32Abort, ValueError, KeyError, json.JSONDecodeError) as exc:
        log(f"FEHLER (Pilot-Sperre): {exc}\nKEIN VERDIKT.")
        return None


def cmd_positive_control(a: argparse.Namespace) -> int:
    lock = _start_lock(a, "--positive-control")
    if lock is None:
        return 1
    registered_path, sha = lock
    registered = _load_registered(registered_path)
    if registered is None:
        return 1
    pilot = _pilot_lock(a, registered, sha)
    if pilot is None:
        return 1
    if not pilot["handed"]:
        log("FEHLER: keine Variante uebergeben -- keine Positivkontrolle, kein Test (GL-012 (Pilot)).")
        return 1
    loaded = load_union_panel(a)
    if loaded is None:
        return 1
    panel, observed = loaded
    try:
        checks.check_data_fingerprints(registered, observed)
        shape, symbols, cut_report = pc_mod.build_shape(panel, registered["seal"]["panel_cut_test"])
        del panel                                     # the real returns never reach the control
        log(f"Positivkontrolle: Form W1/W2 aus {len(shape['weeks'])} Wochen x {len(symbols)} Symbolen, Tage nach dem Schnitt entfernt: "
            f"{cut_report['n_days_removed']}")
        report = pc_mod.run_positive_control(shape, symbols, registered, pilot, observed_fingerprints=observed, registered_sha256=sha,
                                             pilot_sha256=pilot["_file_sha256"], log=log)
        written = pc_mod.write_pc_artifacts(a.out, report)
    except (H32Abort, ValueError) as exc:
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEINE POSITIVKONTROLLE (kein Ergebnis).")
        return 1
    for name, art in written["artifacts"].items():
        log(f"  {name}: {art['file']} sha256={art['sha256']}")
    log(report["line"])
    return 0 if report["bestanden"] else 3


def _parse_wave_p(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for part in [p for p in (text or "").split(",") if p.strip()]:
        name, _, val = part.partition("=")
        out[name.strip()] = float(val)
    return out


def cmd_run(a: argparse.Namespace) -> int:
    lock = _start_lock(a, "--run")
    if lock is None:
        return 1
    registered_path, sha = lock
    registered = _load_registered(registered_path)
    if registered is None:
        return 1
    pilot = _pilot_lock(a, registered, sha)
    if pilot is None:
        return 1
    try:
        wave_p = _parse_wave_p(a.wave_p)
    except ValueError:
        log(f"FEHLER: --wave-p {a.wave_p!r} ist keine Liste NAME=P")
        return 1
    p_rep = None
    if pilot["handed"]:                                  # P4': the pinned v6 p replicates -- before the panel is touched
        if not a.p_replicates:
            log("FEHLER (Replikat-Sperre): --p-replicates (h32_prelaunch_p_replicates.json des Vorlaufs) ist Pflicht, sobald eine "
                "Variante uebergeben ist.\nKEIN VERDIKT.")
            return 1
        try:
            p_rep = pnull.load_replicates(a.p_replicates, registered)
        except (H32Abort, ValueError, KeyError) as exc:
            log(f"FEHLER (Replikat-Sperre): {exc}\nKEIN VERDIKT.")
            return 1
        log(f"[Replikat-Sperre bestanden] {a.p_replicates} sha256={p_rep['_file_sha256']} (R={p_rep['n_reps']})")
    panel = observed = None
    if pilot["handed"]:
        loaded = load_union_panel(a)
        if loaded is None:
            return 1
        panel, observed = loaded
    else:
        log("Kein Eintrag uebergeben: kein Test, das Panel wird nicht gelesen (GL-012 (Pilot)).")
    try:
        report = testrun.run_test(panel, registered, pilot, observed, registered_sha256=sha, wave_p=wave_p, p_replicates=p_rep, log=log)
        written = testrun.write_run_artifacts(a.out, report, registered, pilot_sha256=pilot["_file_sha256"], p_replicates=p_rep)
    except (H32Abort, ValueError) as exc:
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEIN VERDIKT.")
        return 1
    for e, res in report["results"].items():
        log(f"  {e}: {res['verdict']['verdict']} {res['verdict'].get('labels')}")
    hv = report["hypothesis_verdict"]
    log(f"  => H-32: {hv['verdict']}" + (f" ({hv['label']})" if hv.get("label") else ""))
    for name, h in written["artifacts"].items():
        log(f"  {name}: sha256={h}")
    log(f"Report geschrieben: {written['out_dir']}")
    return 0


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="H-32 (A3-fm8) Zweistufen-Treiber")
    ap.add_argument("--prelaunch", action="store_true", help="Vorlauf v6 (outcome-frei)")
    ap.add_argument("--pilot", action="store_true", help="Stufe P (Pilot, Schaetzung)")
    ap.add_argument("--positive-control", action="store_true", help="PRD 3.3.8 Positivkontrolle (allein, vor --run)")
    ap.add_argument("--run", action="store_true", help="Stufe T (Test der uebergebenen Varianten)")
    ap.add_argument("--emit-template", nargs=2, default=None, metavar=("PRELAUNCH_JSON", "OUT_YAML"),
                    help="Skelett von state/registered/h32_v1.yaml aus einem Vorlauf-v6-Artefakt (kein Panel-Zugriff)")
    ap.add_argument("--spread-census", default=DEFAULT_SPREAD_CENSUS, help="WP-7-Spread-Zensus fuer rules.bounce_spread (Dezil D10)")
    ap.add_argument("--registered", default="", help="Pfad zur registrierten YAML (h32_v1.yaml)")
    ap.add_argument("--registered-sha256", default="", help="sha256 der --registered-Datei (Startsperre)")
    ap.add_argument("--pilot-result", default="", help="h32_pilot.json (Pilot-Sperre fuer --run / --positive-control)")
    ap.add_argument("--pilot-result-sha256", default="", help="sha256 des Pilot-Ergebnisses")
    ap.add_argument("--pilot-rerun-dec", default=None, help="DEC-nn, die einen Pilot-Neulauf nach nachgewiesenem Fehler erlaubt (DEC-99 (3))")
    ap.add_argument("--wave-p", default="", help="weitere getestete Hypothesen der Welle fuer F-WEEK: NAME=P[,NAME=P...]")
    ap.add_argument("--p-replicates", default="", help="h32_prelaunch_p_replicates.json des Vorlaufs (sha256 = fdr.replicates_sha256; "
                                                          "Pflicht fuer --run, sobald eine Variante uebergeben ist)")
    ap.add_argument("--p-reps", type=int, default=0, help="Replikate fuer p im Vorlauf (Standard = --n-reps; groesser = feinere "
                                                          "p-Aufloesung, die ersten --n-reps sind die der Konstanten)")
    ap.add_argument("--cut-date", default=C.CUT_TEST, help="Stichtag des Panel-Schnitts im Vorlauf (Sonntag, <= 2026-06-28)")
    ap.add_argument("--v5e-reference", default="", help="YAML mit den v5e-W1-Kalibrierungswerten (W1-Determinismus-Kontrolle)")
    ap.add_argument("--panel-base", default="data/panel_1d")
    ap.add_argument("--delisted-base", default="data/panel_1d_delisted")
    ap.add_argument("--delisted-manifest", default="")
    ap.add_argument("--delisting-dates", default="")
    ap.add_argument("--start-year", type=int, default=2021)
    ap.add_argument("--end-year", type=int, default=date.today().year)
    ap.add_argument("--as-of", default="")
    ap.add_argument("--allow-partial", action="store_true", help="DEC-66: Quellen-Luecken der Bybit-Kerzen erlauben")
    ap.add_argument("--out", default="")
    ap.add_argument("--seed", type=int, default=C.SEED)
    ap.add_argument("--n-reps", type=int, default=C.N_REPS_MIN, help="Null-Replikate je Zelle (>= 1.000 fuer ein registrierbares Skelett)")
    ap.add_argument("--n-boot", type=int, default=C.N_BOOT_MIN, help="Bootstrap-Replikate der SE-Regel (>= 1.000)")
    ap.add_argument("--gegenprobe-n-reps", type=int, default=nulls.GEGENPROBE_N_REPS_DEFAULT)
    ap.add_argument("--gegenprobe-rel-tol", type=float, default=nulls.GEGENPROBE_REL_TOL)
    ap.add_argument("--gegenprobe-z-max", type=float, default=nulls.GEGENPROBE_Z_MAX)
    ap.add_argument("--no-gegenprobe-market-check", action="store_true", help="NUR fuer Tests auf kleinen synthetischen Panels")
    ap.add_argument("--calibration-search-n-reps", type=int, default=nulls.CALIBRATION_SEARCH_N_REPS_DEFAULT)
    ap.add_argument("--calibration-search-rel-tol", type=float, default=nulls.CALIBRATION_SEARCH_REL_TOL_DEFAULT)
    ap.add_argument("--calibration-search-max-iter", type=int, default=nulls.CALIBRATION_SEARCH_MAX_ITER_DEFAULT)
    ap.add_argument("--stress-rel", default=DEFAULT_STRESS_REL, help="STRESS_REL-Liste, nur mit Datumsfilter <= Stichtag gelesen")
    ap.add_argument("--stress-abs", default=DEFAULT_STRESS_ABS, help="STRESS_ABS-Liste, nur mit Datumsfilter <= Stichtag gelesen")
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.emit_template is not None:
        if a.prelaunch or a.pilot or a.run or a.positive_control:
            ap.error("--emit-template ist ein eigenstaendiger Modus")
        return cmd_emit_template(*a.emit_template, spread_census=a.spread_census)
    modes = [a.prelaunch, a.pilot, a.positive_control, a.run]
    if sum(map(bool, modes)) != 1:
        ap.error("genau EINEN Modus waehlen: --prelaunch, --pilot, --positive-control, --run oder --emit-template")
    if not a.out:
        ap.error("--out ist Pflicht")
    if a.prelaunch:
        return cmd_prelaunch(a)
    if not a.registered:
        ap.error("--registered ist mit --pilot/--positive-control/--run Pflicht (Startsperre)")
    if a.pilot:
        return cmd_pilot(a)
    if a.positive_control:
        return cmd_positive_control(a)
    return cmd_run(a)


if __name__ == "__main__":
    raise SystemExit(main())
