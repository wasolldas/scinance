"""WP-10(A2) -- Bestand-vs-Backfill Vergleichszeile (DEC-62, DEC-60-Lehre).

In ``--source backfill`` mode every series is loaded a second time, over
the SAME date window and symbol, from the HARVEST tree -- and the two are
compared on their shared overlap. This is the DEC-60 "Pseudo-Null-
Vergleichszeile" lesson applied here: never trust the new (backfill)
number alone, always show it next to the old (harvest/Bestand) number on
the days both exist.

Two comparison shapes (spec: funding gets an exact-equality check, IV-RV
gets the WP-9 materiality band):

  * ``compare_value_series`` -- two ``series.py``-shaped dicts with
    IDENTICAL semantics (funding daily cashflow, harvest vs. backfill):
    n_overlap, max |diff|, and how many overlap days exceed
    ``diff_threshold`` (default ``1e-9`` -- funding cashflow from the SAME
    underlying settlements should be numerically identical on the
    overlap, not merely close).
  * ``compare_dvol_close`` -- the raw DVOL daily CLOSE (harvest stream vs.
    REST backfill), judged against the WP-9 (DEC-61) materiality band
    (default 0.3 vol pts) -- NOT the full IV-RV difference series, which
    differs by construction whenever the RV side's bar-cache window
    differs between the two calls.

Both NEVER raise on an absent/short/status-not-OK counterpart -- a status
field says so instead (spec: "wenn die Bestandsserie fehlt, sagen, nie
abstuerzen").

KAPITALFREI: pure comparison arithmetic. No cost quantity, no PASS/FAIL.
"""
from __future__ import annotations

from typing import Any

__all__ = ["compare_value_series", "compare_dvol_close"]


def _absent_result(name: str, reason: str) -> dict[str, Any]:
    return {"name": name, "status": "BESTAND_FEHLT", "reason": reason,
            "n_overlap": 0, "max_abs_diff": None, "n_days_diff": 0, "diff_days": []}


def compare_value_series(name: str, backfill_series: dict[str, Any],
                          harvest_series: dict[str, Any] | None, *,
                          diff_threshold: float = 1e-9) -> dict[str, Any]:
    """Compare two ``series.py``-shaped dicts (same symbol, same kind) on
    their date-intersection: ``n_overlap``, ``max_abs_diff``, and how many
    overlap days exceed ``diff_threshold``. ``harvest_series`` is the
    Bestand (harvest-tree) counterpart -- ``None`` or a non-OK/empty
    status is reported as ``BESTAND_FEHLT``, never raised.
    """
    if harvest_series is None:
        return _absent_result(name, "keine Bestandsserie fuer diesen Namen registriert")
    if harvest_series.get("status") != "OK" or not harvest_series.get("days"):
        return _absent_result(
            name, f"Bestandsserie status={harvest_series.get('status')}, "
            f"n_days={harvest_series.get('coverage', {}).get('n_days', 0)}")
    hb = dict(zip(harvest_series["days"], harvest_series["values"]))
    bb = dict(zip(backfill_series["days"], backfill_series["values"]))
    common = sorted(set(hb) & set(bb))
    if not common:
        return _absent_result(name, "keine gemeinsamen Tage in der Ueberlappung")
    diffs = {d: abs(bb[d] - hb[d]) for d in common}
    diff_days = sorted(d for d, v in diffs.items() if v > diff_threshold)
    return {"name": name, "status": "OK", "reason": None,
            "n_overlap": len(common), "max_abs_diff": max(diffs.values()),
            "diff_threshold": diff_threshold, "n_days_diff": len(diff_days),
            "diff_days": diff_days}


def compare_dvol_close(name: str, backfill_dvol_by_day: dict[str, float],
                        harvest_dvol_by_day: dict[str, float] | None, *,
                        materiality_band_volpts: float = 0.3) -> dict[str, Any]:
    """Compare the raw daily DVOL CLOSE, harvest stream vs. REST backfill,
    against the WP-9 (DEC-61) materiality band. ``harvest_dvol_by_day``
    missing/empty is reported as ``BESTAND_FEHLT``, never raised.
    """
    if not harvest_dvol_by_day:
        return _absent_result(name, "keine Bestands-DVOL-Serie vorhanden")
    if not backfill_dvol_by_day:
        return _absent_result(name, "keine Backfill-DVOL-Serie vorhanden")
    common = sorted(set(harvest_dvol_by_day) & set(backfill_dvol_by_day))
    if not common:
        return _absent_result(name, "keine gemeinsamen Tage in der Ueberlappung")
    diffs = {d: abs(backfill_dvol_by_day[d] - harvest_dvol_by_day[d]) for d in common}
    max_diff = max(diffs.values())
    diff_days = sorted(d for d, v in diffs.items() if v > materiality_band_volpts)
    return {"name": name, "status": "OK", "reason": None,
            "n_overlap": len(common), "max_abs_diff": max_diff,
            "materiality_band_volpts": materiality_band_volpts,
            "n_days_diff": len(diff_days), "diff_days": diff_days,
            "within_band": max_diff <= materiality_band_volpts}
