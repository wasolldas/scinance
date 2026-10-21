"""PP3 dry run (``--pp3-dry-run``, DEC-101 E6, Review A-5 / B-9.5): the registration pins (PP3 / P4) are checked BEFORE the
pilot is spent, without computing a single IC.

Why: a difference between the K_fm8 series of the pilot period on the panel cut at 2026-06-28 (Vorlauf v6) and on the panel
cut at 2024-06-30 (pilot) would show only at PP3 of the pilot -- after the registration, and the pilot is exactly-one.  The dry
run does what the pilot does up to the pins and stops:

  start lock (CLI) -> schema -> data fingerprints -> universe filter and pin (DEC-101 E1) -> panel cut at
  ``seal.panel_cut_pilot`` -> weekly arrays -> window P: the K_fm8 series is computed and its sha256 compared with
  ``pilot_window.frozen_v6.k_fm8_series_sha256``, window pins (:func:`checks.check_window_pins`) -> panel cut at
  ``seal.panel_cut_test`` -> weekly arrays -> windows W1 / W2: K_fm8 series against their pins, window pins.

**No IC.**  This module imports no IC function (neither ``fm8`` nor ``ic``); the weekly arrays, the characteristics and the
PIT betas are built exactly as in the modes (``weekly.build_weekly``) but nothing is set against an outcome.  A unit test
monkeypatches ``ic.weekly_ic_series`` / ``ic.apply_beta_control`` / ``ic.fm_neutralize_outcome`` to raise and runs the mode.

Output: log + a small JSON (:func:`write_pp3_artifact` -> ``h32_pp3_dry_run.json``: hashes and ok flags), return code 0 iff
every check holds.
"""
from __future__ import annotations

from typing import Any, Callable

from . import artifacts, checks, panel_cut, schema, universe
from . import constants as C
from . import weekly as wkl
from .errors import H32Abort

__all__ = ["run_pp3_dry_run", "write_pp3_artifact"]


def _window_check(win: wkl.Window, registered: dict[str, Any]) -> dict[str, Any]:
    """K_fm8 series of one window against its pin; collects the result instead of raising so that the file states every flag."""
    pinned = (registered["pilot_window"]["frozen_v6"] if win.name == "P" else registered["windows"][win.name]["frozen_v6"])["k_fm8_series_sha256"]
    got = wkl.int_series_sha256(wkl.k_fm8_series(win))
    row: dict[str, Any] = {"window": win.name, "w_judged": win.w_judged, "k_fm8_series_sha256": got, "pinned_k_fm8_series_sha256": pinned,
                           "k_fm8_series_ok": got == pinned, "k_alive": wkl.k_summary(wkl.k_alive_series(win)),
                           "first_formation_week": win.weeks[0], "last_formation_week": win.weeks[win.w_judged - 1]}
    try:
        checks.check_window_pins(win, registered)
        row["window_pins_ok"] = True
        row["error"] = None
    except H32Abort as exc:                                  # PinError / KMinError: reported, the mode fails at the end
        row["window_pins_ok"] = False
        row["error"] = f"{type(exc).__name__}: {exc}"
    row["ok"] = bool(row["k_fm8_series_ok"] and row["window_pins_ok"])
    return row


def run_pp3_dry_run(panel: dict[str, Any], registered: dict[str, Any], observed_fingerprints: dict[str, Any] | None, *,
                    registered_sha256: str | None = None, universe_report: dict[str, Any] | None = None,
                    log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """The dry run on an UNCUT daily union panel.  Loud fails (raise) before any pin comparison: schema, data fingerprints,
    universe, panel cut.  The pin comparisons themselves are collected in ``windows`` and ``ok``."""
    say = log or (lambda _m: None)
    schema.validate_registered(registered)
    checks.check_data_fingerprints(registered, observed_fingerprints)
    panel, universe_report = universe.ensure_universe(panel, universe_report)               # DEC-101 E1: before any cut
    checks.check_universe_pin(registered, universe_report)
    rows: dict[str, Any] = {}
    cuts: dict[str, Any] = {}
    # pilot cut: window P
    cut_p = registered["seal"]["panel_cut_pilot"]
    cut, rep = panel_cut.cut_panel_days(panel, cut_p, limit=C.CUT_PILOT)
    mx = panel_cut.assert_panel_max_date(cut, cut_p)
    say(f"panel cut at {cut_p}: {rep['n_days_removed']} days removed, max date {mx}")
    wk = wkl.build_weekly(cut, cut_p, with_turnover=False)
    pw = registered["pilot_window"]
    rows["P"] = _window_check(wkl.make_window(wk, "P", pw["start"], pw["end"]), registered)
    cuts["pilot"] = {"cut_date": cut_p, "n_days_removed": rep["n_days_removed"], "max_date": mx, "last_week": wk.weeks[-1],
                     "n_weeks": len(wk.weeks), "n_symbols": len(wk.symbols)}
    say(f"  window P: K_fm8 series {rows['P']['k_fm8_series_sha256'][:12]}... pinned {rows['P']['pinned_k_fm8_series_sha256'][:12]}... "
        f"-> {'ok' if rows['P']['ok'] else 'DIFFERS'}")
    # test cut: windows W1 / W2
    cut_t = registered["seal"]["panel_cut_test"]
    cut, rep = panel_cut.cut_panel_days(panel, cut_t, limit=C.CUT_TEST)
    mx = panel_cut.assert_panel_max_date(cut, cut_t)
    say(f"panel cut at {cut_t}: {rep['n_days_removed']} days removed, max date {mx}")
    wk = wkl.build_weekly(cut, cut_t, with_turnover=False)
    for wn in ("W1", "W2"):
        rows[wn] = _window_check(wkl.make_window(wk, wn), registered)
        say(f"  window {wn}: K_fm8 series {rows[wn]['k_fm8_series_sha256'][:12]}... pinned "
            f"{rows[wn]['pinned_k_fm8_series_sha256'][:12]}... -> {'ok' if rows[wn]['ok'] else 'DIFFERS'}")
    cuts["test"] = {"cut_date": cut_t, "n_days_removed": rep["n_days_removed"], "max_date": mx, "last_week": wk.weeks[-1],
                    "n_weeks": len(wk.weeks), "n_symbols": len(wk.symbols)}
    ok = all(r["ok"] for r in rows.values())
    return {"schema": C.PP3_SCHEMA, "mode": "pp3_dry_run", "registered_sha256": registered_sha256,
            "data_fingerprints": observed_fingerprints, "universe": universe_report,
            "runner": {k: str(v) if k == "as_of" else v for k, v in registered["runner"].items()},
            "cuts": cuts, "windows": rows, "ok": bool(ok),
            "not_computed": ["ic", "raw_ic", "lag_profile", "beta_calibration_ic"],
            "note": "no IC was computed: weekly arrays, characteristics and PIT betas only (DEC-101 E6)"}


def write_pp3_artifact(out_dir, report: dict[str, Any]) -> dict[str, Any]:
    """``h32_pp3_dry_run.json`` (hashes and ok flags; the universe report without its symbol list) and nothing else.  The file
    name does not match ``h32_pilot*``: a dry run never counts as a pilot result (DEC-101 E3)."""
    from pathlib import Path
    out = Path(out_dir)
    artifacts.refuse_unsafe_path(out / "x", writing=True)
    out.mkdir(parents=True, exist_ok=True)
    small = dict(report)
    uni = dict(small.get("universe") or {})
    uni.pop("excluded_symbols", None)                                                      # the list is in the Vorlauf artifact
    small["universe"] = uni
    small["result_sha256"] = artifacts.canonical_sha256(small)
    j = artifacts.write_json(out / C.PP3_FILE, small)
    return {"out_dir": str(out), "json": j, "result_sha256": small["result_sha256"]}
