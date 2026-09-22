#!/usr/bin/env python3
"""WP-13 Runner: F-XSEC1 (H-28/H-29/H-30), Klasse W (PRD 5.3, DEC-73/74).

**Nur ein Modus existiert bisher, per DEC-74 Entscheidung 3 (Vorlauf
WP-13a):**

  python scripts/wp13_xsec.py --prelaunch \
      --panel-base data/panel_1d --delisted-base data/panel_1d_delisted \
      --out scinance3-impl/state/wp13a_YYYYMMDD

liefert AUSSCHLIESSLICH DEC-74 Entscheidung 2 (a) (Rauschboden-
Formel je Fenster), (b)/(c) (Persistenz-Null + c_rho + IC_min),
(g) (Gate-(5)-Erreichbarkeit, KEIN Outcome), (h) (H-30-Feasibility auf L),
die Delisting-Symbol-Wochen-Zaehlung + NO_HISTORY-Symbole aus (i),
STRESS_REL/STRESS_ABS-Abdeckung und die Selektions-Decke (analytisch +
gemessen). **Berechnet NIEMALS eine reale Charakteristik-gegen-reale-
Folgewochenrendite-IC** (Siegel-Test, DEC-74 Entscheidung 3) -- der
Lauf-Modus (die eigentliche H-28/H-29/H-30-Messung) wird erst gegen die
Zweitfassung der Registrierung gebaut.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp7_universe import panel_load, panel_store  # noqa: E402
from bybit_edge.research.wp13_xsec import prelaunch, run as run_mod  # noqa: E402


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
        n_sims=a.n_sims, n_reps_factor_null=a.n_reps_factor_null, seed=a.seed,
        convention=a.convention)

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelaunch", action="store_true",
                     help="Vorlauf-Modus (DEC-74 Entscheidung 3): Vorlauf-Report ohne reale IC.")
    ap.add_argument("--run", action="store_true",
                     help="Lauf-Modus (DEC-75 Entscheidung 2, Startsperre): braucht --registered "
                          "und --registered-sha256.")
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
    ap.add_argument("--convention", default="close_at_last", choices=["drop", "close_at_last"],
                     help="Delisting-Konvention (DEC-74 (i): close_at_last ist urteilstragend).")
    ap.add_argument("--allow-partial", action="store_true")
    ap.add_argument("--stress-rel", default="scinance3-impl/state/wp10_stress_canon/stress_rel.json")
    ap.add_argument("--stress-abs", default="scinance3-impl/state/wp10_stress_canon/stress_abs.json")
    a = ap.parse_args()

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
