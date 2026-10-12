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

    hypotheses:                    # DEC-87 (J): ein Eintrag je VARIANTE, H-28_mom1 ... H-30_vol_beta
      H-28_mom1: {hypothesis: H-28, variant: mom1, direction: positive}
      H-30_vol_rv: {hypothesis: H-30, variant: vol_rv, direction: negative, outcome: vol_weighted}
      H-30_vol_beta: {hypothesis: H-30, variant: vol_beta, direction: negative, outcome: vol_weighted,
                      status: gl012_pre_run, reason: "<Grund>"}   # gesperrt: wird nicht gerechnet, p = 1
    windows:
      W1: {start: <ISO-Datum>, end: <ISO-Datum>,
           ic_min_capped: {<variant>: <float>, ...},   # DEC-74 (a)+(d)/DEC-75 (8)
           w_judged: <int>,                             # DEC-75 Entscheidung 1 (1); DEC-89: gelesen, verwendet, gepinnt
           bounce_sigma_true: <float>                   # DEC-89 E1: Median-Wochen-Vol der Symbole des Fensters (gemessen)
           survivorship: {mom1_diff_in_ic_min_units: <float>, rev_gap_diff_in_ic_min_units: <float>}   # DEC-89 E3 (2)
           calibration:                                 # DEC-87 (D): JE FENSTER (DEC-86), stress PFLICHT
             measured: {rho_f, beta_sd_calibrated, target_factor_share}
             stress:   {rho_f, beta_sd_calibrated, target_factor_share}
             zero:     {rho_f, beta_sd_calibrated, target_factor_share}
           ceiling_method_stress: <float>               # DEC-87 (A): bindende GL-012-Decke (Methode, stress, driftfrei)
           res_quantile_driftfree: {<variant>: <float>} # DEC-87 (E): 99,36-%-Quantil, Drift 0
           res_quantile_drifting: {<variant>: <float>}} # DEC-87 (E): 99,36-%-Quantil, Drift 0,002/Woche
      W2: {...}
      L: {start: <ISO-Datum>, end: <ISO-Datum>}          # optional, descriptive/sealed only
    beta_control:
      method: <einer der 9 ic.BETA_CONTROL_METHODS-Namen>   # DEC-77 Entscheidung 2, PFLICHT, nicht leer
      beta_window_weeks: <int|null>                          # muss zu 'method' passen, sonst loud fail
    data_fingerprints:                                       # DEC-87 V9: gegen das geladene Panel geprueft
      union_range_fingerprint: <sha256>
      delisting_dates_sha256: <sha256>
    rules:
      seed: 53
      n_reps: 1000            # Faktor-Null-Replikate, >= 1000 und gleich n_reps_beta_control_winner des Vorlaufs
      block_len: 4            # DEC-89 E3 (5): GELESEN und verwendet, gegen nulls.BLOCK_SIZE_WEEKS gepinnt (Abweichung = laut)
      level: 0.9936           # DEC-89 E3 (5): GELESEN und verwendet (CI + Null-Quantil), gegen den Code gepinnt
      bh_alpha: 0.10           # report-only BH-FDR alpha (DEC-75 Entscheidung 1 (6)); Nenner fest 7
      bounce_spread: <float>  # DEC-89 E1: Median-Perp-Spread Dezil D10 des WP-7-Spread-Zensus als Bruchteil (36,21 bp -> 0,003621)

  * ``ceiling_method_stress`` / ``res_quantile_driftfree`` / ``res_quantile_drifting`` sind die EINGEFRORENEN
    Null-Konstanten (DEC-87 (A)/(E)): ``--run`` RECHNET sie auf der realen K-Reihe/``W_judged`` nach
    (``nulls.run_configuration_null``: registrierte Methode, ``windows.<W>.calibration.stress``, Seed 53,
    ``rules.n_reps``, driftfrei UND 0,002/Woche) und bricht laut ab, wenn eine mehr als +-10 % abweicht
    ("Null-Kalibrierung weicht ab", KEIN VERDIKT fuer keine Hypothese) -- ``run.assert_null_calibration``.
    Bindend fuer die Beta-Kontrolle ist je Variante/Fenster das in Hypothesenrichtung extremere der beiden
    Quantile. Der alte Schluessel ``ceiling_driftfree_res`` (TS-Residualisierung) und ein globaler
    ``calibration``-Block werden abgewiesen (C.14).

  python scripts/wp13_xsec.py --emit-registered-template \
      scinance3-impl/state/wp13a_YYYYMMDD/wp13a_prelaunch.json \
      scinance3-impl/state/wp13a_YYYYMMDD/registered_template.yaml \
      [--spread-census scinance3-impl/state/runs/wp7_20260921/spread_census.json]

liest EINEN ``--prelaunch``-Artefakt (Vorlauf v5e / DEC-87 oder spaeter) und schreibt das obige YAML-Skelett:
je Fenster ``ic_min_capped``, ``w_judged``, ``calibration.{measured,stress,zero}`` aus dem
``beta_control_method_study`` DES FENSTERS, ``ceiling_method_stress`` und beide Quantil-Mengen aus
``frozen_null_constants`` (Gewinner-Bestaetigung), ``beta_control.method`` aus der BESTAETIGTEN Empfehlung
(``beta_control_confirmation``; keine bestaetigt -> leer), sieben Eintraege ``H-28_mom1`` ... ``H-30_vol_beta``
(``vol_beta`` vorab ``gl012_pre_run`` nach DEC-87 (H); alle H-30-Eintraege ``gl012_pre_run``, wenn die
H-30-Feasibility in Wocheneinheiten verfehlt ist, DEC-87 (G)), ``data_fingerprints`` und ``rules``. Die
Zuordnung C.10/GL-012 nach Power (DEC-87 (F)) wird hier NICHT vorgenommen -- sie ist Sache des Orchestrators,
mechanisch auf diesen Zahlen. Die Drittfassung zitiert den sha256 dieser Ausgabedatei (geloggt) als ihren
``--registered-sha256``-Wert.

**DEC-89 E1/E3 (2):** zusaetzlich ``rules.bounce_spread`` (aus ``--spread-census``, Median-Perp-Spread des Dezils D10,
bp/1e4; Default der WP-7-Zensus ``scinance3-impl/state/runs/wp7_20260921/spread_census.json``, relativ zum Repo-Wurzel-
verzeichnis aufgeloest), je Fenster ``bounce_sigma_true`` (Vorlauf ``factor_preserving_null.driftfree.
sigma_e_median_symbol_weekly``) und ``survivorship`` (Vorlauf ``survivorship_fixture``: ``mom1_diff_in_ic_min_units``,
``rev_gap_diff_in_ic_min_units``). Fehlt ein Fenster-Datum im Vorlauf-Artefakt, steht ``null`` im YAML (und eine
WARNUNG im Kopf); ``--run`` und ``--positive-control`` weisen ein ``null`` laut ab. Eine fehlende oder unlesbare
Zensus-Datei ist ein Fehler (rc 1).

  python scripts/wp13_xsec.py --positive-control \
      --registered path/to/drittfassung.yaml --registered-sha256 <sha256> \
      --panel-base data/panel_1d --delisted-base data/panel_1d_delisted \
      --out scinance3-impl/state/wp13_positivkontrolle_YYYYMMDD [--seeds 53,54,55]

DEC-89 E2 / PRD 3.3.8: die Positivkontrolle in Produktionskonfiguration, ALLEIN und ZUERST (vor ``--run``). Gleiche
STARTSPERRE wie ``--run`` (sha256 der ``--registered``-Datei, Schema-Preflight mit allen eingefrorenen Konstanten) und
gleiche Panel-Argumente (das Panel liefert NUR Wochenraster, PIT-Alive-Masken, K_t und die Fingerprint-Pruefung --
reale Renditen werden nie als Outcome benutzt, ``positive_control.run_positive_control`` hat kein ``returns``-Argument).
Je Seed (Default 53,54,55) und Fenster entstehen synthetische Wochenrenditen auf der Fensterform (Faktorstruktur der
kalibrierten Null mit der stress-Kalibrierung des Fensters + PRD-Positiv-Fixture, injizierte IC 0,06 fuer ``mom1``
positiv / ``rev_gap`` negativ); die komplette Gate-Auswertung des Laufs rechnet gegen die EINGEFRORENEN Konstanten der
YAML, OHNE Neuberechnung der Nullen (Laufzeit niedrig). Negativkontrolle: identisch, injiziertes Signal 0.
Ausgabe nach ``--out``: ``wp13_positive_control.json`` und ``wp13_positive_control.md`` und die Zeile
``Positivkontrolle BESTANDEN`` / ``Positivkontrolle NICHT BESTANDEN`` (DEC-89 E2: ``H-28_mom1`` und ``H-29_rev_gap``
in allen drei Seeds PASS UND Negativkontrolle in allen drei Seeds kein PASS; gesperrte Varianten uebersprungen).
Exit-Code: 0 NUR bei BESTANDEN; 3 bei NICHT BESTANDEN; 1 bei jedem Abbruch (Startsperre, Schema, Fingerprint, Panel).
Bei NICHT BESTANDEN kein Lauf: Ursachenanalyse und neue DEC.
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
from bybit_edge.research.wp13_xsec import characteristics, ic, nulls, prelaunch, run as run_mod  # noqa: E402
from bybit_edge.research.wp13_xsec import positive_control as pc_mod  # noqa: E402

#: DEC-89 E1: the WP-7 spread census whose decile-D10 median perp spread is the registered bounce spread.
DEFAULT_SPREAD_CENSUS = "scinance3-impl/state/runs/wp7_20260921/spread_census.json"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def data_fingerprints(a: argparse.Namespace, panel: dict, delisted_base: Path,
                      delisting_dates_path: Path, as_of: date) -> dict:
    """DEC-87 (V9): the two fingerprints of the panel actually loaded -- the UNION range fingerprint
    (``panel_load.union_range_fingerprint``: survivors tree + delisted tree + symbol set, for the year range and
    ``as_of`` of the load) and the sha256 of ``delisting_dates.json``. ``--prelaunch`` reports them, ``--run``
    checks them against the registered YAML's ``data_fingerprints``. Read-only."""
    surv_syms = [sym for sym, dl in zip(panel["symbols"], panel["is_delisted"]) if not dl]
    fp = panel_load.union_range_fingerprint(
        a.panel_base, delisted_base, surv_syms, panel["delisted_symbols"],
        year_start=a.start_year, year_end=a.end_year, as_of=as_of)
    return {
        "union_range_fingerprint": fp["sha256"],
        "delisting_dates_sha256": panel_load.sha256_file(delisting_dates_path),
        "union_range_detail": {"year_range": fp["year_range"], "n_partitions": fp["n_partitions"],
                               "survivors_fingerprint": fp["survivors_fingerprint"],
                               "delisted_fingerprint": fp["delisted_fingerprint"],
                               "n_symbols": len(fp["symbols"]), "as_of": as_of.isoformat()},
    }


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
    fingerprints = data_fingerprints(a, panel, delisted_base, delisting_dates_path, as_of)
    log(f"  Daten-Fingerprints (DEC-87 V9): union_range={fingerprints['union_range_fingerprint']} "
        f"delisting_dates={fingerprints['delisting_dates_sha256']}")

    log(f"[3/4] Vorlauf-Report zusammenstellen (n_sims={a.n_sims}, seed={a.seed}, "
        f"convention={a.convention}) -- KEINE reale Signal-Outcome-IC")
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=delisted_manifest,
        delisting_dates_path=delisting_dates_path,
        stress_rel_path=a.stress_rel, stress_abs_path=a.stress_abs,
        n_sims=a.n_sims, n_reps_factor_null=a.n_reps_factor_null,
        n_reps_beta_control_study=a.n_reps_beta_control_study,
        n_reps_beta_control_winner=a.n_reps_beta_control_winner,
        seed=a.seed, convention=a.convention,
        gegenprobe_n_reps=a.gegenprobe_n_reps, gegenprobe_rel_tol=a.gegenprobe_rel_tol,
        gegenprobe_z_max=a.gegenprobe_z_max,
        gegenprobe_market_check=not a.no_gegenprobe_market_check,
        calibration_search_n_reps=a.calibration_search_n_reps,
        calibration_search_rel_tol=a.calibration_search_rel_tol,
        calibration_search_max_iter=a.calibration_search_max_iter,
        data_fingerprints=fingerprints)

    for name in ("W1", "W2", "L"):
        w = report["windows"].get(name, {})
        if not w.get("available"):
            log(f"  Fenster {name}: nicht verfuegbar ({w.get('note')})")
            continue
        log(f"  Fenster {name}: {w['n_weeks']} Wochen, Delisting-Symbol-Wochen="
            f"{w['delisting']['n_symbol_weeks_delisting']}, Gate(5) erreichbar="
            f"{w['gate5_reachability']['gate5_reachable']}")

    conf = report.get("beta_control_confirmation") or {}
    log(f"  Gewinner-Bestaetigung (DEC-87): {conf.get('note')}")
    log("[4/4] DEC-53-Artefakte schreiben")
    out_dir = Path(a.out)
    artifacts = prelaunch.write_prelaunch_artifacts(out_dir, report)
    for name, art in artifacts["artifacts"].items():
        log(f"  {name}: {art['path']} sha256={art['sha256']}")
    log(f"Report geschrieben: {out_dir}")
    log("KEIN VERDIKT -- Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung "
        "(DEC-74 Entscheidung 3).")
    return 0


def _start_lock(a: argparse.Namespace, flag: str) -> tuple[Path, str] | None:
    """DEC-75 Entscheidung 2 START LOCK, shared by ``--run`` and ``--positive-control`` (DEC-89 E2: "Startsperre wie
    --run"): ``--registered`` must exist and ``--registered-sha256`` must equal its sha256 -- checked BEFORE a single
    byte of the real panel is loaded. Returns ``(path, sha256)`` or ``None`` after logging the refusal (rc=1)."""
    registered_path = Path(a.registered)
    if not registered_path.is_file():
        log(f"FEHLER: keine registrierte Datei unter {registered_path}")
        return None
    actual_sha256 = run_mod.sha256_of_file(registered_path)
    if not a.registered_sha256:
        log(f"FEHLER (Startsperre, DEC-75 Entscheidung 2): --registered-sha256 ist Pflicht "
            f"fuer {flag}. sha256 der angegebenen Datei ist {actual_sha256} -- diesen Wert in "
            "die Drittfassung eintragen und hier exakt uebergeben.")
        return None
    if a.registered_sha256.lower() != actual_sha256.lower():
        log(f"FEHLER (Startsperre): --registered-sha256 ({a.registered_sha256}) stimmt NICHT mit "
            f"dem tatsaechlichen sha256 von {registered_path} ({actual_sha256}) ueberein. "
            "Kein Lauf gegen eine nicht-registrierte Schwellen-Datei.")
        return None
    log(f"[Startsperre bestanden] {registered_path} sha256={actual_sha256}")
    return registered_path, actual_sha256


def _panel_paths(a: argparse.Namespace) -> tuple[Path, Path, Path, Path] | None:
    """``(manifest, delisted_base, delisted_manifest, delisting_dates_path)`` of the union panel, or ``None`` after
    logging a missing manifest."""
    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    if not manifest.is_file():
        log(f"FEHLER: kein Manifest unter {manifest} -- WP-7 --fetch zuerst ausfuehren.")
        return None
    delisted_base = Path(a.delisted_base)
    delisted_manifest = (Path(a.delisted_manifest) if a.delisted_manifest
                          else delisted_base / "panel_manifest.sqlite")
    delisting_dates_path = (Path(a.delisting_dates) if a.delisting_dates
                             else delisted_base / "delisting_dates.json")
    if not delisted_manifest.is_file():
        log(f"FEHLER: kein delistetes Manifest unter {delisted_manifest}.")
        return None
    return manifest, delisted_base, delisted_manifest, delisting_dates_path


def _load_registered_preflight(registered_path: Path) -> dict | None:
    """DEC-87 pre-flight (C.14): schema errors surface before a single panel byte is read. DEC-89: the mandatory
    constants (frozen nulls, bounce parameters, survivorship, w_judged, block_len, level) are part of it."""
    try:
        registered = run_mod.load_registered_yaml(registered_path)
        run_mod.validate_registered(registered, require_frozen_constants=True)
    except (ValueError, yaml.YAMLError) as exc:           # RegisteredSchemaError is a ValueError
        log(f"FEHLER (registered YAML, DEC-87/DEC-89): {exc}\nKEIN VERDIKT.")
        return None
    return registered


def _load_union_weekly(a: argparse.Namespace, paths: tuple[Path, Path, Path, Path]):
    """Union panel + weekly returns/mask + the V9 data fingerprints, shared by ``--run`` and ``--positive-control``.
    Returns ``(panel, weekly, observed)`` or ``None`` after logging the loud fail."""
    manifest, delisted_base, delisted_manifest, delisting_dates_path = paths
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
        return None
    log(f"  {len(panel['symbols'])} Symbole, {len(panel['dates'])} Tage.")

    log("[2/4] Woechentliche Renditen + PIT-Alive-Maske (Union), Daten-Fingerprints")
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    log(f"  {len(weekly['weeks'])} Wochen ({weekly['weeks'][0]}..{weekly['weeks'][-1]})")
    observed = data_fingerprints(a, panel, delisted_base, delisting_dates_path, as_of)
    log(f"  union_range={observed['union_range_fingerprint']} delisting_dates={observed['delisting_dates_sha256']}")
    return panel, weekly, observed


def cmd_run(a: argparse.Namespace) -> int:
    """DEC-75 Entscheidung 2, letzter Satz: Lauf-Modus mit STARTSPERRE.
    Refuses (rc=1, loud, C.14) unless ``--registered-sha256`` matches the
    sha256 of the ``--registered`` YAML -- this check happens BEFORE a
    single byte of the real panel is loaded, so a mismatched/omitted hash
    can NEVER reach a real characteristic-vs-real-outcome computation.

    DEC-87: after the lock the registered YAML is validated against the schema (per-window calibration, renamed
    ceiling, locked entries; C.14) BEFORE the panel is read; the loaded panel's union-range fingerprint and
    ``delisting_dates.json`` sha256 are checked against ``data_fingerprints`` (V9); the artifacts (raw AND
    residualised weekly IC series, replicate/generator fingerprints) are written and verified BEFORE any verdict
    is logged or written -- every :class:`run.RunAbort` (null calibration drifted, fingerprint mismatch, missing
    mandatory artifact) ends the run with rc=1 and KEIN VERDIKT.

    DEC-89: the schema pre-flight also demands the bounce parameters, the survivorship numbers, ``w_judged``,
    ``rules.block_len`` and ``rules.level`` (a missing one is refused loudly, rc=1); the run writes ``wp13_run.md``
    next to the JSON. The positive control (``--positive-control``) is run ALONE and FIRST; this mode does not
    run it."""
    lock = _start_lock(a, "--run")
    if lock is None:
        return 1
    registered_path, actual_sha256 = lock
    paths = _panel_paths(a)
    if paths is None:
        return 1
    registered = _load_registered_preflight(registered_path)
    if registered is None:
        return 1
    loaded = _load_union_weekly(a, paths)
    if loaded is None:
        return 1
    panel, weekly, observed = loaded

    log("[3/4] Registrierte Schwellen-Datei geladen und validiert (siehe oben)")

    log("[4/4] Lauf-Pipeline (DEC-75 Entscheidung 1 (1)-(7), DEC-87, DEC-89)")
    out_dir = Path(a.out)
    try:
        report = run_mod.run_full(panel, weekly, registered, convention=a.convention,
                                  observed_fingerprints=observed, registered_sha256=actual_sha256)
        # DEC-53: artifacts FIRST (and verified) -- no verdict is logged or written without them.
        artifacts = run_mod.write_run_artifacts(out_dir, report, require_data_fingerprints=True)
    except (run_mod.RunAbort, ValueError) as exc:     # ValueError: C.14 loud fails (beta_control, schema)
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEIN VERDIKT.")
        return 1
    for entry_id, res in report["results"].items():
        log(f"  {entry_id} ({res['variant']}): {res['verdict']['verdict']} labels={res['verdict']['labels']}")
    for hyp, hv in report["hypothesis_verdicts"].items():
        log(f"  => {hyp}: {hv['verdict']} (Varianten PASS: {hv['variants_pass']}; gesperrt: {hv['variants_locked']})")
        if hv.get("label") and hv["verdict"] == run_mod.GL012_PRE_RUN_VERDICT:
            log(f"     {hv['label']}")
    for name, art in artifacts["artifacts"].items():
        log(f"  {name}: {art['path']} sha256={art['sha256']}")
    log(f"Report geschrieben: {out_dir}")
    return 0


def cmd_positive_control(a: argparse.Namespace) -> int:
    """DEC-89 E2 / PRD 3.3.8: the positive control in production configuration, ALONE and FIRST (see the module
    docstring and ``positive_control.py``). START LOCK as ``--run`` (sha256 of ``--registered``, BEFORE any panel byte
    is read), schema pre-flight incl. every frozen constant (rc=1), then the union panel is loaded exactly like
    ``--run`` -- but ONLY its week grid, PIT alive masks, ``returns_valid`` mask, symbol order and the V9
    fingerprints are used (checked against the YAML); the real weekly returns are dropped before the control starts and
    never serve as an outcome. Writes ``wp13_positive_control.json`` / ``.md`` to ``--out``. Exit code: 0 ONLY if the
    control is BESTANDEN, 3 if NICHT BESTANDEN, 1 on any abort (lock, schema, fingerprint, panel, pin)."""
    lock = _start_lock(a, "--positive-control")
    if lock is None:
        return 1
    registered_path, actual_sha256 = lock
    try:
        seeds = tuple(int(s) for s in str(getattr(a, "seeds", "") or ",".join(map(str, pc_mod.PC_SEEDS))).split(",") if s.strip())
    except ValueError:
        log(f"FEHLER: --seeds={getattr(a, 'seeds', None)!r} ist keine Komma-Liste ganzer Zahlen.")
        return 1
    if not seeds:
        log("FEHLER: --seeds ist leer.")
        return 1
    paths = _panel_paths(a)
    if paths is None:
        return 1
    registered = _load_registered_preflight(registered_path)
    if registered is None:
        return 1
    loaded = _load_union_weekly(a, paths)
    if loaded is None:
        return 1
    panel, weekly, observed = loaded
    if "returns_valid" not in weekly:
        log("FEHLER: weekly ohne returns_valid (DEC-85 (iii)) -- Positivkontrolle nicht moeglich.")
        return 1
    # Shape only: the real returns are dropped here and never reach the control (it has no `returns` parameter).
    shape = {"weeks": list(weekly["weeks"]), "alive": weekly["alive"], "returns_valid": weekly["returns_valid"]}
    symbols = list(panel["symbols"])
    del panel, weekly

    log(f"[3/4] Positivkontrolle (DEC-89 E2): Seeds {list(seeds)}, injizierte IC {pc_mod.INJECTED_IC}, "
        "synthetische Renditen auf der realen Fensterform, eingefrorene Konstanten, keine Null-Neuberechnung")
    out_dir = Path(a.out)
    try:
        report = pc_mod.run_positive_control(
            shape, symbols, registered, seeds=seeds, convention=a.convention,
            observed_fingerprints=observed, registered_sha256=actual_sha256, log=log)
        artifacts = pc_mod.write_positive_control_artifacts(out_dir, report)
    except (run_mod.RunAbort, ValueError) as exc:
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEINE POSITIVKONTROLLE (kein Ergebnis).")
        return 1
    log("[4/4] Ergebnis")
    crit = report["criteria"]
    log(f"  Positivkontrolle alle PASS: {crit['positive_all_pass']}; Negativkontrolle kein PASS: {crit['negative_no_pass']}")
    for name, art in artifacts["artifacts"].items():
        log(f"  {name}: {art['path']} sha256={art['sha256']}")
    log(f"Report geschrieben: {out_dir} (Laufzeit {report['runtime_seconds']} s, result_sha256={report['result_sha256']})")
    log(report["line"])
    return 0 if report["bestanden"] else 3


#: DEC-87 (H): vol_beta is locked BEFORE the run -- the registered fm_neutral beta control regresses the
#: outcome on exactly this beta, the residual is linearly orthogonal to the characteristic.
VOL_BETA_LOCK_REASON = ("strukturell durch die registrierte Beta-Kontrolle neutralisiert (C.4; DEC-87 (H)): "
                        "fm_neutral_8w regressiert das Outcome auf genau dieses Beta")

#: PRD 5.3 defaults (hypothesis, direction, outcome) of the seven F-XSEC1 entries, DEC-87 (J).
ENTRY_DEFAULTS: tuple[tuple[str, str, str, str, str | None], ...] = (
    ("H-28_mom1", "H-28", "mom1", "positive", None),
    ("H-28_mom2", "H-28", "mom2", "positive", None),
    ("H-28_mom4", "H-28", "mom4", "positive", None),
    ("H-29_rev_gap", "H-29", "rev_gap", "negative", None),
    ("H-30_vol_rv", "H-30", "vol_rv", "negative", "vol_weighted"),
    ("H-30_vol_max", "H-30", "vol_max", "negative", "vol_weighted"),
    ("H-30_vol_beta", "H-30", "vol_beta", "negative", "vol_weighted"),
)


def _resolve_repo_path(path_str: str) -> Path:
    """A relative path is taken from the working directory if it exists there, else from the repository root (the
    parent of ``scripts/``) -- so the default ``DEFAULT_SPREAD_CENSUS`` resolves from any cwd."""
    p = Path(path_str)
    if p.is_absolute() or p.exists():
        return p
    return Path(__file__).resolve().parents[1] / p


def read_bounce_spread(census_path: Path) -> float:
    """DEC-89 E1: the registered bounce spread = the median perp spread of decile D10 (the least liquid decile, the
    strictest choice = the largest bounce) of the WP-7 spread census, in bp, divided by 1e4 (36.21 bp -> 0.003621;
    rounded to 12 digits so no float noise enters the registered file). ``ValueError`` if the census has no finite
    positive D10 value."""
    data = json.loads(Path(census_path).read_text(encoding="utf-8"))
    d10 = next((d for d in (data.get("deciles") or []) if d.get("decile") == 10), None)
    bp = None if d10 is None else d10.get("perp_spread_bp_median")
    if not (isinstance(bp, (int, float)) and not isinstance(bp, bool) and bp == bp and 0.0 < float(bp) < float("inf")):
        raise ValueError(f"Spread-Zensus {census_path}: kein endlicher positiver deciles[decile=10].perp_spread_bp_median")
    return round(float(bp) / 1e4, 12)


def cmd_emit_registered_template(prelaunch_json_path: str, out_yaml_path: str,
                                 spread_census_path: str = DEFAULT_SPREAD_CENSUS) -> int:
    """DEC-76 Task A item 4, reworked by DEC-87 (D)/(A)/(E)/(J): reads a ``--prelaunch`` artifact (Vorlauf v5e or
    later) and writes the registered-YAML SKELETON (``run.REGISTERED_SCHEMA_HINT``'s shape), per window W1/W2:

      * ``ic_min_capped``/``w_judged`` from ``noise_floor_and_threshold``;
      * ``calibration.{measured, stress, zero}`` = ``{rho_f, beta_sd_calibrated, target_factor_share}`` from THAT
        window's own ``beta_control_method_study.calibrations`` (DEC-86 / DEC-87 (D) -- the pre-DEC-87 global
        W1-sourced block is gone), the artifact's own bisection result, never re-derived here;
      * ``ceiling_method_stress``, ``res_quantile_driftfree``, ``res_quantile_drifting`` from the window's
        ``frozen_null_constants`` (the Vorlauf's winner section, produced by ``nulls.run_configuration_null`` --
        the very configuration ``--run`` recomputes), ``None`` placeholders if no method was confirmed.

    ``beta_control.method``/``beta_window_weeks`` are filled from the artifact's CONFIRMED recommendation
    (``beta_control_confirmation``, DEC-87 V1 Bindung) -- left empty if none was confirmed (the run then loud-fails
    on the empty method). Seven entries ``H-28_mom1`` ... ``H-30_vol_beta`` (DEC-87 (J)); ``vol_beta`` is written as
    ``status: gl012_pre_run`` (H), and all three H-30 entries are when the Vorlauf's H-30 feasibility in weekly
    units is violated (``h30_feasibility_weekly_units``: Spread/Kante or SE/Kante > 0.5, DEC-74 (h)/DEC-87 (G)).
    ``data_fingerprints`` and ``rules.n_reps`` (= the winner replicates that froze the constants) are copied from
    the artifact. Never registers anything itself (no sha256 check here) -- the Orchestrator reviews the written
    file (incl. the power assignment (F), NOT done here), then cites ITS sha256 (logged below) in the Drittfassung.

    **DEC-89 (E1, E3 (2)), additive:** ``rules.bounce_spread`` from the WP-7 spread census ``spread_census_path``
    (median perp spread of decile D10 in bp / 1e4, :func:`read_bounce_spread`; an unreadable census is a loud fail,
    rc=1); per window ``bounce_sigma_true`` = the Vorlauf's ``factor_preserving_null.driftfree.
    sigma_e_median_symbol_weekly`` and ``survivorship`` = ``{mom1_diff_in_ic_min_units, rev_gap_diff_in_ic_min_units}`` of
    its ``survivorship_fixture`` (``None`` placeholders + a WARNUNG header line where the artifact lacks them -- the
    ``--run``/``--positive-control`` pre-flight refuses those)."""
    in_path = Path(prelaunch_json_path)
    out_path_check = Path(out_yaml_path)
    if "data/harvest" in out_path_check.as_posix():
        log(f"FEHLER: schreibe nie unter data/harvest: {out_path_check}")
        return 1
    if not in_path.is_file():
        log(f"FEHLER: kein Vorlauf-Artefakt unter {in_path}")
        return 1
    census_path = _resolve_repo_path(spread_census_path)
    if not census_path.is_file():
        log(f"FEHLER: kein Spread-Zensus unter {census_path} (DEC-89 E1: rules.bounce_spread kommt aus der Messung; "
            "--spread-census angeben).")
        return 1
    try:
        bounce_spread = read_bounce_spread(census_path)
    except (ValueError, json.JSONDecodeError) as exc:
        log(f"FEHLER (Spread-Zensus, DEC-89 E1): {exc}")
        return 1
    report = json.loads(in_path.read_text(encoding="utf-8"))
    variants = report.get("variants", list(characteristics.VARIANT_NAMES))

    windows_out: dict[str, dict] = {}
    missing_dec89: list[str] = []
    for wname in ("W1", "W2"):
        w = report.get("windows", {}).get(wname)
        if not w or not w.get("available"):
            log(f"  Fenster {wname}: nicht verfuegbar im Vorlauf-Artefakt -- uebersprungen.")
            continue
        nf = w.get("noise_floor_and_threshold", {})
        fz = w.get("frozen_null_constants") or {}
        cals = (w.get("beta_control_method_study") or {}).get("calibrations", {})

        def _cal_block(c: dict) -> dict:
            return {"rho_f": c.get("rho_f"), "beta_sd_calibrated": c.get("beta_sd_calibrated"),
                    "target_factor_share": c.get("target_factor_share")}

        # DEC-89 E1: the window's measured median weekly symbol vol = the bounce fixture's true weekly vol.
        sigma_true = ((w.get("factor_preserving_null") or {}).get("driftfree") or {}).get("sigma_e_median_symbol_weekly")
        # DEC-89 E3 (2): the survivorship-fixture differences (discarded minus closed-at-last), in IC_min units.
        sf = w.get("survivorship_fixture") or {}
        def _finite_num(x) -> bool:
            return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x and abs(x) != float("inf")

        if not _finite_num(sigma_true):
            sigma_true = None
            missing_dec89.append(f"{wname}.bounce_sigma_true (factor_preserving_null.driftfree.sigma_e_median_symbol_weekly)")
        surv_block = {k: sf.get(k) if _finite_num(sf.get(k)) else None
                      for k in ("mom1_diff_in_ic_min_units", "rev_gap_diff_in_ic_min_units")}
        if any(v is None for v in surv_block.values()):
            missing_dec89.append(f"{wname}.survivorship (survivorship_fixture)")

        # DEC-89 E2 (Nachtrag): the calibrated null world's own scales (the study's measured sigma_f and
        # idiosyncratic sigma_e_used) -- the positive control simulates exactly this world.
        study_w = w.get("beta_control_method_study") or {}
        null_scales = {"sigma_f": study_w.get("sigma_f"), "sigma_e_used": study_w.get("sigma_e_used")}
        if not all(_finite_num(v) and v > 0 for v in null_scales.values()):
            missing_dec89.append(f"{wname}.null_scales (beta_control_method_study.sigma_f/sigma_e_used)")
        windows_out[wname] = {
            "start": w["start"], "end": w["end"],
            "null_scales": null_scales,
            "ic_min_capped": nf.get("ic_min_capped_per_variant", {}),
            "w_judged": nf.get("w_judged"),
            "bounce_sigma_true": sigma_true,
            "survivorship": surv_block,
            "calibration": {cal: _cal_block(cals[cal]) for cal in ("measured", "stress", "zero") if cal in cals},
            "ceiling_method_stress": fz.get("ceiling_method_stress"),
            "res_quantile_driftfree": fz.get("res_quantile_driftfree") or {v: None for v in variants},
            "res_quantile_drifting": fz.get("res_quantile_drifting") or {v: None for v in variants},
        }
    wl = report.get("windows", {}).get("L") or {}
    if wl.get("available"):
        # the open JSON replaces the L window by a pointer to its sealed file (no start/end), so the
        # descriptive L entry takes the registered L calendar (prelaunch.WINDOWS) -- never judged, no IC here.
        windows_out["L"] = {"start": wl.get("start", prelaunch.WINDOWS["L"][0]),
                            "end": wl.get("end", prelaunch.WINDOWS["L"][1])}

    conf = report.get("beta_control_confirmation") or {}
    confirmed = conf.get("confirmed_method")
    beta_control = ({"method": confirmed, "beta_window_weeks": ic.beta_control_trail_weeks(confirmed)}
                    if confirmed else {"method": "", "beta_window_weeks": None})

    h30 = report.get("h30_feasibility_weekly_units")
    h30_lock_reason = None
    if h30:
        rs, rse = h30.get("spread_d10_minus_d1_over_kante"), h30.get("se_drag_over_kante")
        finite = all(isinstance(x, (int, float)) and x == x for x in (rs, rse))
        if finite and (rs > 0.5 or rse > 0.5):
            h30_lock_reason = (f"H-30-Feasibility in Wocheneinheiten verfehlt: Spread(D10-D1)/Kante={rs:.3f}, "
                               f"SE(sigma_w^2/2)/Kante={rse:.3f}, Grenze 0,5 (DEC-74 (h), DEC-87 (G)); K bleibt 7")
    hypotheses: dict[str, dict] = {}
    for entry_id, hyp, variant, direction, outcome in ENTRY_DEFAULTS:
        entry: dict = {"hypothesis": hyp, "variant": variant, "direction": direction}
        if outcome:
            entry["outcome"] = outcome
        reasons = []
        if variant == "vol_beta":
            reasons.append(VOL_BETA_LOCK_REASON)
        if hyp == "H-30" and h30_lock_reason:
            reasons.append(h30_lock_reason)
        if reasons:
            entry["status"] = "gl012_pre_run"
            entry["reason"] = "; ".join(reasons)
        hypotheses[entry_id] = entry

    template: dict = {
        "hypotheses": hypotheses,
        "windows": windows_out,
        "beta_control": beta_control,
        "rules": {"seed": 53, "n_reps": int(report.get("n_reps_beta_control_winner") or 1000),
                  "block_len": 4, "level": 0.9936, "bh_alpha": 0.10,
                  "bounce_spread": bounce_spread},          # DEC-89 E1: measured (WP-7 census, D10), not a code constant
    }
    fps = report.get("data_fingerprints")
    if isinstance(fps, dict) and "union_range_fingerprint" in fps and "delisting_dates_sha256" in fps:
        template["data_fingerprints"] = {"union_range_fingerprint": fps["union_range_fingerprint"],
                                         "delisting_dates_sha256": fps["delisting_dates_sha256"]}

    out_path = Path(out_yaml_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = ["# DEC-76 Task A item 4 / DEC-87: automatisch aus einem --prelaunch-Artefakt erzeugtes Skelett.",
              "# Kalibrierung JE FENSTER (DEC-87 (D)); Konstanten aus dem Gewinner-Abschnitt des Vorlaufs (DEC-87 (A)/(E)).",
              "# hypotheses: sieben Eintraege (J). NICHT automatisch geprueft -- Orchestrator bestaetigt, ordnet C.10/GL-012 "
              "nach Power zu (F) und registriert."]
    if confirmed:
        header.append(f"# beta_control.method aus der BESTAETIGTEN Empfehlung ({confirmed!r}, DEC-87 V1 Bindung): {conf.get('note')}")
    else:
        header.append("# WARNUNG: KEINE Methode bestaetigt (" + str(conf.get("note", "Artefakt ohne Bestaetigung"))
                      + ") -- beta_control.method bleibt leer, run.py schlaegt laut fehl (DEC-77 E1 (c)).")
    if h30_lock_reason:
        header.append("# H-30 mechanisch gesperrt: " + h30_lock_reason)
    elif not h30:
        header.append("# HINWEIS: Artefakt ohne h30_feasibility_weekly_units -- H-30-Sperre (G) nicht beurteilt.")
    if "data_fingerprints" not in template:
        header.append("# WARNUNG: Artefakt ohne data_fingerprints (DEC-87 V9) -- ohne diesen Block lehnt --run ab.")
    if template["rules"]["n_reps"] < 1000:
        header.append(f"# WARNUNG: rules.n_reps={template['rules']['n_reps']} < 1000 (Vorlauf mit weniger Replikaten).")
    header.append(f"# DEC-89 E1: rules.bounce_spread={bounce_spread} = Median-Perp-Spread Dezil D10 aus {census_path.name} "
                  "(bp/1e4); bounce_sigma_true = gemessene Median-Wochen-Vol je Fenster; survivorship = Vorlauf-Differenzen "
                  "in IC_min-Einheiten (report-only Etikett).")
    if missing_dec89:
        header.append("# WARNUNG: Vorlauf-Artefakt ohne " + "; ".join(missing_dec89)
                      + " (DEC-89) -- null im YAML, --run/--positive-control weisen es laut ab.")
    out_path.write_text("\n".join(header) + "\n" + yaml.safe_dump(template, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
    log(f"Quelle: {in_path} sha256={panel_load.sha256_file(in_path)}")
    log(f"Registrierungs-Vorlage geschrieben: {out_path} sha256={panel_load.sha256_file(out_path)}")
    log("Pruefung Pflicht: hypotheses-Zuordnung (inkl. Power-Zuordnung F), beta_control und alle Werte vor der "
        "Registrierung bestaetigen.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelaunch", action="store_true",
                     help="Vorlauf-Modus (DEC-74 Entscheidung 3): Vorlauf-Report ohne reale IC.")
    ap.add_argument("--run", action="store_true",
                     help="Lauf-Modus (DEC-75 Entscheidung 2, Startsperre): braucht --registered "
                          "und --registered-sha256.")
    ap.add_argument("--positive-control", action="store_true",
                     help="DEC-89 E2 / PRD 3.3.8: Positivkontrolle in Produktionskonfiguration (ALLEIN und ZUERST, vor "
                          "--run): braucht --registered und --registered-sha256 (Startsperre wie --run), "
                          "die Panel-Argumente und --out; rc 0 nur bei BESTANDEN.")
    ap.add_argument("--seeds", default="53,54,55",
                     help="DEC-89 E2: Seeds der Positivkontrolle (Default 53,54,55 = die registrierten; andere "
                          "Seeds koennen nie BESTANDEN ergeben).")
    ap.add_argument("--spread-census", default=DEFAULT_SPREAD_CENSUS,
                     help="DEC-89 E1: WP-7-Spread-Zensus, aus dem --emit-registered-template rules.bounce_spread "
                          "(Median-Perp-Spread Dezil D10, bp/1e4) liest.")
    ap.add_argument("--emit-registered-template", nargs=2, default=None,
                     metavar=("PRELAUNCH_JSON", "OUT_YAML"),
                     help="DEC-76 Task A item 4 / DEC-87 / DEC-89: liest einen --prelaunch-Artefakt und schreibt das "
                          "Registrierungs-YAML-Skelett (ic_min_capped, w_judged, calibration je Fenster, "
                          "ceiling_method_stress, res_quantile_driftfree/-drifting, bounce_sigma_true, survivorship, "
                          "beta_control aus der bestaetigten Empfehlung, sieben Eintraege, data_fingerprints, rules "
                          "inkl. bounce_spread aus --spread-census) nach OUT_YAML "
                          "-- kein Panel-Zugriff, kein Lauf.")
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
                          "Methoden-Rasters (3 Kalibrierungen x 6 Methoden x 7 Varianten) -- "
                          ">= 500 akzeptabel; Default 100, weil ein VOR DEC-81 gemessenes "
                          "Mikro-Benchmark (siehe prelaunch.assemble_prelaunch_report's "
                          "Docstring) 300 Replikate auf K~1138/W~52 auf ~2,6 h/Fenster "
                          "hochrechnete. Seit DEC-81 ist beta_characteristic vektorisiert "
                          "(bitgleich, ~36x schneller); der Runner-PC-Wrapper "
                          "(run_wp13_prelaunch.ps1) nimmt deshalb 300.")
    ap.add_argument("--n-reps-beta-control-winner", type=int, default=1000,
                     help="DEC-77 Entscheidung 1 (b): Replikate fuer den erneuten Lauf der "
                          "EMPFOHLENEN Methode allein (measured/stress), fuer die finale "
                          "Tabelle -- >= 1.000.")
    ap.add_argument("--gegenprobe-n-reps", type=int, default=nulls.GEGENPROBE_N_REPS_DEFAULT,
                     help="DEC-78 Entscheidung 1/Nachtrag, DEC-81: Replikate je Gegenprobe-Aufruf "
                          "(eine je Kalibrierung, unabhaengiger Seed) -- Default 400 (der "
                          "Schaetzfehler des Median-R^2 faellt wie 1/sqrt(n): ~8,5 Prozent bei 30-40, "
                          "~3 Prozent bei 400).")
    ap.add_argument("--gegenprobe-rel-tol", type=float, default=nulls.GEGENPROBE_REL_TOL,
                     help="DEC-81: groesste aufloesbare Abweichung der Gegenprobe (Power-Bedingung: "
                          "z_max * se_diff <= rel_tol * Ziel, sonst 'unterpowert') -- Default 0,25. "
                          "NUR fuer Tests auf kleinen synthetischen Panels lockern; ein echter Lauf "
                          "soll den strikten Default behalten.")
    ap.add_argument("--gegenprobe-z-max", type=float, default=nulls.GEGENPROBE_Z_MAX,
                     help="DEC-81: groesstes zulaessiges |simuliert - Ziel| / se_diff der Gegenprobe "
                          "(se_diff aus Gegenprobe- und Suchfehler) -- Default 3,0. NUR fuer Tests "
                          "auf kleinen synthetischen Panels lockern.")
    ap.add_argument("--no-gegenprobe-market-check", action="store_true",
                     help="DEC-85 (ii): schaltet die Marktspalten-Pruefung der Gegenprobe (gemessenes "
                          "sigma_f/rho_f im 95-%%-Band der simulierten Marktspalte) ab -- NUR fuer Tests "
                          "auf kleinen synthetischen Panels; ein echter Lauf laeuft immer mit Pruefung.")
    ap.add_argument("--calibration-search-n-reps", type=int, default=nulls.CALIBRATION_SEARCH_N_REPS_DEFAULT,
                     help="DEC-78 Nachtrag, DEC-81: Replikate je Bisektions-Iteration der beta_sd-Suche "
                          "(gemeinsame Zufallszahlen in allen Iterationen) -- Default 400.")
    ap.add_argument("--calibration-search-rel-tol", type=float, default=nulls.CALIBRATION_SEARCH_REL_TOL_DEFAULT,
                     help="DEC-78 Nachtrag, DEC-81: Praezision der Nullstelle der beta_sd-Suche auf der "
                          "deterministischen Stichprobenfunktion -- Default 0,01. Eine nicht "
                          "konvergierte Suche bricht den Lauf laut ab.")
    ap.add_argument("--calibration-search-max-iter", type=int, default=nulls.CALIBRATION_SEARCH_MAX_ITER_DEFAULT,
                     help="DEC-78 Nachtrag: maximale Bisektions-Iterationen der beta_sd-Suche "
                          "-- Default 25.")
    ap.add_argument("--convention", default="close_at_last", choices=["drop", "close_at_last"],
                     help="Delisting-Konvention (DEC-74 (i): close_at_last ist urteilstragend).")
    ap.add_argument("--allow-partial", action="store_true")
    ap.add_argument("--stress-rel", default="scinance3-impl/state/wp10_stress_canon/stress_rel.json")
    ap.add_argument("--stress-abs", default="scinance3-impl/state/wp10_stress_canon/stress_abs.json")
    a = ap.parse_args()

    if a.emit_registered_template is not None:
        if a.prelaunch or a.run or a.positive_control:
            ap.error("--emit-registered-template ist ein eigenstaendiger Modus, nicht mit "
                      "--prelaunch/--run/--positive-control kombinierbar")
        return cmd_emit_registered_template(*a.emit_registered_template, spread_census_path=a.spread_census)

    if sum(map(bool, (a.prelaunch, a.run, a.positive_control))) > 1:
        ap.error("genau EINEN Modus waehlen: --prelaunch ODER --run ODER --positive-control, nicht mehrere")
    if not a.prelaunch and not a.run and not a.positive_control:
        ap.error("genau EINEN Modus waehlen: --prelaunch, --run oder --positive-control (DEC-75 Entscheidung 2, DEC-89)")
    if not a.out:
        ap.error("--out ist Pflicht")
    if a.prelaunch:
        return cmd_prelaunch(a)
    if not a.registered:
        ap.error("--registered ist mit --run/--positive-control Pflicht (Startsperre, DEC-75 Entscheidung 2)")
    if a.positive_control:
        return cmd_positive_control(a)
    return cmd_run(a)


if __name__ == "__main__":
    raise SystemExit(main())
