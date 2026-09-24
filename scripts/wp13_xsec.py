#!/usr/bin/env python3
"""WP-13 Runner: F-XSEC1 (H-28/H-29/H-30), Klasse W (PRD 5.3, DEC-73/74/75/76).

**Zwei Modi (DEC-75 Entscheidung 2), plus ein Hilfsbefehl (DEC-76 Task A
item 4):**

  python scripts/wp13_xsec.py --prelaunch \
      --panel-base data/panel_1d --delisted-base data/panel_1d_delisted \
      --out scinance3-impl/state/wp13a_YYYYMMDD

liefert AUSSCHLIESSLICH DEC-74 Entscheidung 2 (a) (Rauschboden-
Formel je Fenster), (b)/(c) (Persistenz-Null + c_rho + IC_min),
(g) (Gate-(5)-Erreichbarkeit, KEIN Outcome), (h) (H-30-Feasibility auf L),
die Delisting-Symbol-Wochen-Zaehlung + NO_HISTORY-Symbole aus (i),
STRESS_REL/STRESS_ABS-Abdeckung, die Selektions-Decke (analytisch +
gemessen) und (DEC-76 Vorlauf v3, Entscheidung 2) die faktorerhaltende
Null in ZWEI Konfigurationen (drifting/driftfree, roh + residualisiert).
**Berechnet NIEMALS eine reale Charakteristik-gegen-reale-Folgewochen-
rendite-IC** (Siegel-Test, DEC-74 Entscheidung 3).

  python scripts/wp13_xsec.py --run \
      --registered path/to/drittfassung.yaml --registered-sha256 <sha256> \
      --panel-base data/panel_1d --delisted-base data/panel_1d_delisted \
      --out scinance3-impl/state/wp13_run_YYYYMMDD

der eigentliche H-28/H-29/H-30-Lauf (DEC-75 Entscheidung 1/2, DEC-76
Entscheidung 1), mit STARTSPERRE (siehe ``cmd_run``'s Docstring). Die
``--registered``-YAML (die Drittfassung) MUSS folgende Schluessel tragen
(``run.REGISTERED_SCHEMA_HINT``, verbatim hier gespiegelt):

    hypotheses:
      H-xx: {variant: <einer der 7 F-XSEC1-Namen>, direction: positive|negative,
             outcome?: vol_weighted}          # nur H-30
    windows:
      W1: {start: <ISO-Datum>, end: <ISO-Datum>,
           ic_min_capped: {<variant>: <float>, ...},   # DEC-74 (a)+(d)/DEC-75 (8)
           w_judged: <int>,                             # DEC-75 Entscheidung 1 (1)
           res_quantile_drifting: {<variant>: <float>, ...},  # DEC-76 (b), optional*
           ceiling_driftfree_res: <float>}              # DEC-76 (c), optional*
      W2: {...}
      L: {start: <ISO-Datum>, end: <ISO-Datum>}          # optional, descriptive/sealed only
    beta_control:
      method: <einer der 9 ic.BETA_CONTROL_METHODS-Namen>   # DEC-77 Entscheidung 2, PFLICHT, nicht leer
      beta_window_weeks: <int|null>                          # muss zu 'method' passen, sonst loud fail
    rules:
      seed: 53
      n_reps: 1000            # bootstrap/permutation/factor-null reps, >= 1000 (DEC-75/76)
      block_len: 4            # FIXED DEC-75 constant, recorded for audit only (code hardcodes 4)
      level: 0.9936           # one-sided CI/quantile level (1 - 0.0064)
      bh_alpha: 0.10           # report-only BH-FDR alpha (DEC-75 Entscheidung 1 (6))

  * ``res_quantile_drifting``/``ceiling_driftfree_res`` are the DEC-76
    Entscheidung 1 (b)/(c) FROZEN null constants -- ``--run`` RECOMPUTES
    both on the real K series/``W_judged`` (seed 53, ``rules.n_reps``
    reps) and asserts each is within +/-10% of these frozen values
    (``run.assert_null_calibration``), else loud fail ("Null-Kalibrierung
    weicht ab", no verdict for ANY hypothesis in the run) -- see
    ``run.py``'s module docstring. Omitting them (a pre-DEC-76 registered
    file) skips the assertion and falls back to the recomputed value,
    documented, not a registered Drittfassung run.

  python scripts/wp13_xsec.py --emit-registered-template \
      scinance3-impl/state/wp13a_YYYYMMDD/wp13a_prelaunch.json \
      scinance3-impl/state/wp13a_YYYYMMDD/registered_template.yaml

liest EINEN ``--prelaunch``-Artefakt (DEC-76 Vorlauf v3 oder spaeter) und
schreibt genau das obige YAML-Skelett (``ic_min_capped``, ``w_judged``,
``res_quantile_drifting`` aus ``factor_preserving_null.drifting``,
``ceiling_driftfree_res`` aus ``factor_preserving_null.driftfree``, plus
``rules``) fuer W1/W2 -- die Drittfassung zitiert den sha256 dieser
Ausgabedatei (geloggt) als ihren ``--registered-sha256``-Wert. Die
``hypotheses``-Zuordnung (welche Variante zu H-28/H-29/H-30 gehoert) ist
NICHT im Vorlauf enthalten und wird als PRD-5.3-Standardbelegung
(H-28=mom1 positiv, H-29=rev_gap negativ, H-30=vol_rv negativ/
vol_weighted) vorbelegt -- vom Orchestrator vor der Registrierung zu
pruefen/anzupassen, nie automatisch scharf geschaltet.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp7_universe import panel_load, panel_store  # noqa: E402
from bybit_edge.research.wp13_xsec import characteristics, prelaunch, run as run_mod  # noqa: E402


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def cmd_prelaunch(a: argparse.Namespace) -> int:
    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    if not manifest.is_file():
        log(f"FEHLER: kein Manifest unter {manifest} -- WP-7 --fetch zuerst ausfuehren.")
        return 1
    delisted_base = Path(a.delisted_base)
    delisted_manifest = (Path(a.delisted_manifest) if a.delisted_manifest
                          else delisted_base / "panel_manifest.sqlite")
    delisting_dates_path = (Path(a.delisting_dates) if a.delisting_dates
                             else delisted_base / "delisting_dates.json")
    if not delisted_manifest.is_file():
        log(f"FEHLER: kein delistetes Manifest unter {delisted_manifest} -- "
            "WP-12b --fetch-delisted-panel zuerst ausfuehren (WP-13 laeuft auf der Union, DEC-73).")
        return 1

    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    log(f"[1/4] Union-Panel laden (panel_1d + panel_1d_delisted, as_of={as_of.isoformat()})")
    symbols = panel_load.load_panel_symbols(manifest)
    try:
        panel = panel_load.load_panel_union(
            a.panel_base, manifest, delisted_base, delisted_manifest,
            year_start=a.start_year, year_end=a.end_year, as_of=as_of,
            delisting_dates_path=delisting_dates_path, symbols=symbols,
            allow_partial=a.allow_partial)
    except (panel_store.PanelStoreError, panel_load.PanelLoadError) as exc:
        log(f"FEHLER (loud fail): {exc}")
        return 1
    log(f"  {len(panel['symbols'])} Symbole ({panel['n_symbols_survivors']} Ueberlebende + "
        f"{panel['n_symbols_delisted']} delistet), {len(panel['dates'])} Tage.")

    log("[2/4] Woechentliche Renditen + PIT-Alive-Maske (Union)")
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    log(f"  {len(weekly['weeks'])} Wochen ({weekly['weeks'][0]}..{weekly['weeks'][-1]})")

    log(f"[3/4] Vorlauf-Report zusammenstellen (n_sims={a.n_sims}, seed={a.seed}, "
        f"convention={a.convention}) -- KEINE reale Signal-Outcome-IC")
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=delisted_manifest,
        delisting_dates_path=delisting_dates_path,
        stress_rel_path=a.stress_rel, stress_abs_path=a.stress_abs,
        n_sims=a.n_sims, n_reps_factor_null=a.n_reps_factor_null,
        n_reps_beta_control_study=a.n_reps_beta_control_study,
        n_reps_beta_control_winner=a.n_reps_beta_control_winner,
        seed=a.seed, convention=a.convention)

    for name in ("W1", "W2", "L"):
        w = report["windows"].get(name, {})
        if not w.get("available"):
            log(f"  Fenster {name}: nicht verfuegbar ({w.get('note')})")
            continue
        log(f"  Fenster {name}: {w['n_weeks']} Wochen, Delisting-Symbol-Wochen="
            f"{w['delisting']['n_symbol_weeks_delisting']}, Gate(5) erreichbar="
            f"{w['gate5_reachability']['gate5_reachable']}")

    log("[4/4] DEC-53-Artefakte schreiben")
    out_dir = Path(a.out)
    artifacts = prelaunch.write_prelaunch_artifacts(out_dir, report)
    for name, art in artifacts["artifacts"].items():
        log(f"  {name}: {art['path']} sha256={art['sha256']}")
    log(f"Report geschrieben: {out_dir}")
    log("KEIN VERDIKT -- Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung "
        "(DEC-74 Entscheidung 3).")
    return 0


def cmd_run(a: argparse.Namespace) -> int:
    """DEC-75 Entscheidung 2, letzter Satz: Lauf-Modus mit STARTSPERRE.
    Refuses (rc=1, loud, C.14) unless ``--registered-sha256`` matches the
    sha256 of the ``--registered`` YAML -- this check happens BEFORE a
    single byte of the real panel is loaded, so a mismatched/omitted hash
    can NEVER reach a real characteristic-vs-real-outcome computation."""
    registered_path = Path(a.registered)
    if not registered_path.is_file():
        log(f"FEHLER: keine registrierte Datei unter {registered_path}")
        return 1
    actual_sha256 = run_mod.sha256_of_file(registered_path)
    if not a.registered_sha256:
        log("FEHLER (Startsperre, DEC-75 Entscheidung 2): --registered-sha256 ist Pflicht "
            f"fuer --run. sha256 der angegebenen Datei ist {actual_sha256} -- diesen Wert in "
            "die Drittfassung eintragen und hier exakt uebergeben.")
        return 1
    if a.registered_sha256.lower() != actual_sha256.lower():
        log(f"FEHLER (Startsperre): --registered-sha256 ({a.registered_sha256}) stimmt NICHT mit "
            f"dem tatsaechlichen sha256 von {registered_path} ({actual_sha256}) ueberein. "
            "Kein Lauf gegen eine nicht-registrierte Schwellen-Datei.")
        return 1
    log(f"[Startsperre bestanden] {registered_path} sha256={actual_sha256}")

    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    if not manifest.is_file():
        log(f"FEHLER: kein Manifest unter {manifest} -- WP-7 --fetch zuerst ausfuehren.")
        return 1
    delisted_base = Path(a.delisted_base)
    delisted_manifest = (Path(a.delisted_manifest) if a.delisted_manifest
                          else delisted_base / "panel_manifest.sqlite")
    delisting_dates_path = (Path(a.delisting_dates) if a.delisting_dates
                             else delisted_base / "delisting_dates.json")
    if not delisted_manifest.is_file():
        log(f"FEHLER: kein delistetes Manifest unter {delisted_manifest}.")
        return 1

    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    log(f"[1/4] Union-Panel laden (as_of={as_of.isoformat()})")
    symbols = panel_load.load_panel_symbols(manifest)
    try:
        panel = panel_load.load_panel_union(
            a.panel_base, manifest, delisted_base, delisted_manifest,
            year_start=a.start_year, year_end=a.end_year, as_of=as_of,
            delisting_dates_path=delisting_dates_path, symbols=symbols,
            allow_partial=a.allow_partial)
    except (panel_store.PanelStoreError, panel_load.PanelLoadError) as exc:
        log(f"FEHLER (loud fail): {exc}")
        return 1
    log(f"  {len(panel['symbols'])} Symbole, {len(panel['dates'])} Tage.")

    log("[2/4] Woechentliche Renditen + PIT-Alive-Maske (Union)")
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    log(f"  {len(weekly['weeks'])} Wochen ({weekly['weeks'][0]}..{weekly['weeks'][-1]})")

    log("[3/4] Registrierte Schwellen-Datei laden")
    registered = run_mod.load_registered_yaml(registered_path)

    log("[4/4] Lauf-Pipeline (DEC-75 Entscheidung 1 (1)-(7))")
    report = run_mod.run_full(panel, weekly, registered, convention=a.convention)
    for hyp, res in report["results"].items():
        log(f"  {hyp} ({res['payload']['variant']}): {res['verdict']['verdict']} "
            f"labels={res['verdict']['labels']}")

    out_dir = Path(a.out)
    artifacts = run_mod.write_run_artifacts(out_dir, report)
    for name, art in artifacts["artifacts"].items():
        log(f"  {name}: {art['path']} sha256={art['sha256']}")
    log(f"Report geschrieben: {out_dir}")
    return 0


def cmd_emit_registered_template(prelaunch_json_path: str, out_yaml_path: str) -> int:
    """DEC-76 Task A item 4: reads a ``--prelaunch`` artifact (DEC-76
    Vorlauf v3 or later -- needs ``factor_preserving_null.{drifting,
    driftfree}``) and writes the registered-YAML SKELETON
    (``run.REGISTERED_SCHEMA_HINT``'s shape) -- ``ic_min_capped``/
    ``w_judged`` from ``noise_floor_and_threshold``, ``res_quantile_
    drifting`` from ``factor_preserving_null.drifting.variants.<v>.
    quantile_one_sided_residualized``, ``ceiling_driftfree_res`` from
    ``factor_preserving_null.driftfree.selection_ceiling_mean_of_max_
    residualized`` -- for W1/W2. Never registers anything itself (no
    sha256 check here) -- the Orchestrator reviews the written file, then
    cites ITS sha256 (logged below) in the Drittfassung."""
    in_path = Path(prelaunch_json_path)
    out_path_check = Path(out_yaml_path)
    if "data/harvest" in out_path_check.as_posix():
        log(f"FEHLER: schreibe nie unter data/harvest: {out_path_check}")
        return 1
    if not in_path.is_file():
        log(f"FEHLER: kein Vorlauf-Artefakt unter {in_path}")
        return 1
    report = json.loads(in_path.read_text(encoding="utf-8"))
    variants = report.get("variants", list(characteristics.VARIANT_NAMES))

    windows_out: dict[str, dict] = {}
    for wname in ("W1", "W2"):
        w = report.get("windows", {}).get(wname)
        if not w or not w.get("available"):
            log(f"  Fenster {wname}: nicht verfuegbar im Vorlauf-Artefakt -- uebersprungen.")
            continue
        nf = w.get("noise_floor_and_threshold", {})
        fp = w.get("factor_preserving_null", {})
        drifting, driftfree = fp.get("drifting", {}), fp.get("driftfree", {})
        res_quantile_drifting = {
            v: drifting.get("variants", {}).get(v, {}).get("quantile_one_sided_residualized")
            for v in variants
        }
        windows_out[wname] = {
            "start": w["start"], "end": w["end"],
            "ic_min_capped": nf.get("ic_min_capped_per_variant", {}),
            "w_judged": nf.get("w_judged"),
            "res_quantile_drifting": res_quantile_drifting,
            "ceiling_driftfree_res": driftfree.get("selection_ceiling_mean_of_max_residualized"),
        }
    if "L" in report.get("windows", {}):
        wl = report["windows"]["L"]
        if wl.get("available") and "start" in wl and "end" in wl:
            windows_out["L"] = {"start": wl["start"], "end": wl["end"]}

    # DEC-77 Entscheidung 2: beta_control.method/beta_window_weeks are EMPTY (never
    # auto-filled from the prelaunch artifact's own recommendation) -- the orchestrator
    # must read the artifact's beta_control_recommendation and fill these in deliberately;
    # run.run_full loud-fails if either is still empty at --run time.
    rec = report.get("beta_control_recommendation", {})
    recommended = rec.get("recommended_method")
    template = {
        "hypotheses": {
            "H-28": {"variant": "mom1", "direction": "positive"},
            "H-29": {"variant": "rev_gap", "direction": "negative"},
            "H-30": {"variant": "vol_rv", "direction": "negative", "outcome": "vol_weighted"},
        },
        "windows": windows_out,
        "beta_control": {"method": "", "beta_window_weeks": None},
        "rules": {"seed": 53, "n_reps": 1000, "block_len": 4, "level": 0.9936, "bh_alpha": 0.10},
    }

    out_path = Path(out_yaml_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rec_comment = (f"# DEC-77 Hinweis (kein Auto-Fuellen): Vorlauf-Empfehlung war {recommended!r} "
                   f"(beta_window_weeks={rec.get('beta_window_weeks')!r}).\n"
                   if recommended else
                   "# DEC-77 Hinweis: der Vorlauf hat KEINE Methode empfohlen (siehe Artefakt) -- "
                   "beta_control.method bleibt leer, kein Lauf ohne Orchestrator-Entscheidung.\n")
    out_path.write_text(
        "# DEC-76 Task A item 4: automatisch aus einem --prelaunch-Artefakt erzeugtes Skelett.\n"
        "# hypotheses: NICHT automatisch geprueft -- Orchestrator bestaetigt vor der Registrierung.\n"
        "# beta_control.method/beta_window_weeks: LEER, Orchestrator-Pflicht vor der Registrierung "
        "(DEC-77 Entscheidung 2) -- run.py schlaegt laut fehl, wenn method beim --run leer ist.\n"
        + rec_comment
        + yaml.safe_dump(template, sort_keys=False, allow_unicode=True),
        encoding="utf-8")
    log(f"Quelle: {in_path} sha256={panel_load.sha256_file(in_path)}")
    log(f"Registrierungs-Vorlage geschrieben: {out_path} sha256={panel_load.sha256_file(out_path)}")
    log("Pruefung Pflicht: hypotheses-Zuordnung, beta_control und alle Werte vor der Registrierung bestaetigen.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelaunch", action="store_true",
                     help="Vorlauf-Modus (DEC-74 Entscheidung 3): Vorlauf-Report ohne reale IC.")
    ap.add_argument("--run", action="store_true",
                     help="Lauf-Modus (DEC-75 Entscheidung 2, Startsperre): braucht --registered "
                          "und --registered-sha256.")
    ap.add_argument("--emit-registered-template", nargs=2, default=None,
                     metavar=("PRELAUNCH_JSON", "OUT_YAML"),
                     help="DEC-76 Task A item 4: liest einen --prelaunch-Artefakt und schreibt das "
                          "Registrierungs-YAML-Skelett (ic_min_capped, w_judged, res_quantile_drifting, "
                          "ceiling_driftfree_res, rules) nach OUT_YAML -- kein Panel-Zugriff, kein Lauf.")
    ap.add_argument("--registered", default="",
                     help="Pfad zur registrierten Schwellen-YAML (Drittfassung).")
    ap.add_argument("--registered-sha256", default="",
                     help="sha256 der --registered-Datei, wie in der Drittfassung eingetragen -- "
                          "Pflicht fuer --run, sonst kein Lauf (Startsperre).")
    ap.add_argument("--panel-base", default="data/panel_1d")
    ap.add_argument("--delisted-base", default="data/panel_1d_delisted")
    ap.add_argument("--delisted-manifest", default="")
    ap.add_argument("--delisting-dates", default="")
    ap.add_argument("--start-year", type=int, default=2021)
    ap.add_argument("--end-year", type=int, default=date.today().year)
    ap.add_argument("--as-of", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--seed", type=int, default=53)
    ap.add_argument("--n-sims", type=int, default=1000,
                     help="Persistenz-Null-Simulationen je Variante (DEC-74 (c): 1.000; "
                          "500 mit Hinweis, falls zu langsam).")
    ap.add_argument("--n-reps-factor-null", type=int, default=1000,
                     help="Faktorerhaltende-Null-Replikate je Variante (DEC-75 Entscheidung 1 "
                          "(2)/(3): >= 1.000).")
    ap.add_argument("--n-reps-beta-control-study", type=int, default=100,
                     help="DEC-77 Entscheidung 1 (b): Replikate je Zelle des Beta-Kontroll-"
                          "Methoden-Rasters (3 Kalibrierungen x 9 Methoden x 7 Varianten) -- "
                          ">= 500 akzeptabel; Default 100, NICHT 300, weil ein gemessenes "
                          "Mikro-Benchmark (siehe prelaunch.assemble_prelaunch_report's "
                          "Docstring) 300 Replikate auf K~1138/W~52 auf ~2,6 h/Fenster "
                          "hochrechnet (ueber der 2-h-Vorgabe) -- vom Orchestrator gegen die "
                          "tatsaechliche Runner-PC-Geschwindigkeit zu erhoehen.")
    ap.add_argument("--n-reps-beta-control-winner", type=int, default=1000,
                     help="DEC-77 Entscheidung 1 (b): Replikate fuer den erneuten Lauf der "
                          "EMPFOHLENEN Methode allein (measured/stress), fuer die finale "
                          "Tabelle -- >= 1.000.")
    ap.add_argument("--convention", default="close_at_last", choices=["drop", "close_at_last"],
                     help="Delisting-Konvention (DEC-74 (i): close_at_last ist urteilstragend).")
    ap.add_argument("--allow-partial", action="store_true")
    ap.add_argument("--stress-rel", default="scinance3-impl/state/wp10_stress_canon/stress_rel.json")
    ap.add_argument("--stress-abs", default="scinance3-impl/state/wp10_stress_canon/stress_abs.json")
    a = ap.parse_args()

    if a.emit_registered_template is not None:
        if a.prelaunch or a.run:
            ap.error("--emit-registered-template ist ein eigenstaendiger Modus, nicht mit "
                      "--prelaunch/--run kombinierbar")
        return cmd_emit_registered_template(*a.emit_registered_template)

    if a.prelaunch and a.run:
        ap.error("genau EINEN Modus waehlen: --prelaunch ODER --run, nicht beide")
    if not a.prelaunch and not a.run:
        ap.error("genau EINEN Modus waehlen: --prelaunch oder --run (DEC-75 Entscheidung 2)")
    if not a.out:
        ap.error("--out ist Pflicht")
    if a.prelaunch:
        return cmd_prelaunch(a)
    if not a.registered:
        ap.error("--registered ist mit --run Pflicht (Startsperre, DEC-75 Entscheidung 2)")
    return cmd_run(a)


if __name__ == "__main__":
    raise SystemExit(main())
