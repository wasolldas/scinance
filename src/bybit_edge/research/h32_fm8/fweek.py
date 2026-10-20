"""Over-family F-WEEK (Benjamini-Yekutieli, alpha 0.10, binding at the wave close) and the report-only BH inside F-H32
(DEC-74 (e), DEC-99 (7), ERSTFASSUNG 1.10).

Counting rule (DEC-99 (7)): ``m`` = the number of entries for which a p value was actually computed -- for H-32 the
handed-over ones (1..4), plus other tested hypotheses of the wave (``wave_p``); GL-012 / not handed-over entries have
p = 1 per decision and are NOT in ``m``.  Mandatory double statement: the old count ``m = 11`` (including p = 1 entries),
report-only.

BY single-rejection bound ``alpha / (m H_m)``; the step-up procedure uses the bound ``k alpha / (m H_m)`` at rank k.
"""
from __future__ import annotations

import math
from typing import Any

from . import constants as C
from . import estimators as est
from ..wp13_xsec import run as wp13_run

__all__ = ["by_adjust", "apply_fweek", "bh_report"]


def by_adjust(p_values: dict[str, float], *, alpha: float = C.BY_ALPHA, m: int | None = None) -> dict[str, Any]:
    """Benjamini-Yekutieli step-up over ``p_values`` (``m`` defaults to their number).  NaN p never rejects (counts as 1)."""
    m = len(p_values) if m is None else int(m)
    if m < len(p_values):
        raise ValueError("m must be at least the number of p values")
    h = est.harmonic_number(m)
    items = sorted(((k, 1.0 if (p is None or not math.isfinite(p)) else float(p)) for k, p in p_values.items()), key=lambda kp: kp[1])
    largest = 0
    for rank, (_k, p) in enumerate(items, start=1):
        if p <= rank * alpha / (m * h):
            largest = rank
    reject = {k: False for k in p_values}
    for rank, (k, _p) in enumerate(items, start=1):
        if rank <= largest:
            reject[k] = True
    return {"alpha": alpha, "m": m, "harmonic_number": h, "single_bound": alpha / (m * h), "reject": reject,
            "largest_rejected_rank": largest or None, "p_sorted": [[k, p] for k, p in items]}


def bh_report(p_by_variant: dict[str, float]) -> dict[str, Any]:
    """BH inside F-H32, report-only: alpha 0.10, FIXED denominator 4, not handed-over variants with p = 1."""
    full = {v: 1.0 for v in C.VARIANTS}
    full.update({v: p for v, p in p_by_variant.items() if p is not None and math.isfinite(p)})
    return wp13_run.benjamini_hochberg(full, alpha=C.BH_ALPHA, m_total=C.BH_DENOMINATOR)


def apply_fweek(verdicts: dict[str, dict[str, Any]], p_max: dict[str, float], *, wave_p: dict[str, float] | None = None,
                double_m: int = C.FWEEK_DOUBLE_M) -> dict[str, Any]:
    """BY over the tested entries (``p_max`` of the entries in ``verdicts``) and the other tested hypotheses ``wave_p``.
    Returns ``{"by", "by_double_statement", "demoted"}``; ``verdicts`` entries that are a provisional PASS and not rejected
    by BY are demoted IN PLACE to DROP with the label "F-WEEK-BY nicht bestanden"; every verdict gets
    ``fweek_double_statement`` (old count m = 11: rejected yes / no, report-only)."""
    wave_p = dict(wave_p or {})
    tested = {e: p_max[e] for e in verdicts if e in p_max}
    combined = {**tested, **{f"wave:{k}": v for k, v in wave_p.items()}}
    by = by_adjust(combined) if combined else None
    old = dict(combined)
    n_pad = max(0, int(double_m) - len(old))
    for i in range(n_pad):
        old[f"p1_entry_{i + 1}"] = 1.0
    by_old = by_adjust(old, m=len(old)) if old else None
    demoted: list[str] = []
    for e, v in verdicts.items():
        if e not in tested:
            continue
        v["fweek_double_statement"] = {"m": by_old["m"], "rejected": bool(by_old["reject"][e]), "report_only": True}
        v["fweek"] = {"m": by["m"], "rejected": bool(by["reject"][e]), "p_max": tested[e], "single_bound": by["single_bound"]}
        if v["verdict"] == "PASS":
            if not by["reject"][e]:
                v["verdict"] = "DROP"
                v["labels"] = [lab for lab in v["labels"] if not lab.startswith("vorlaeufig bis F-WEEK")]
                v["labels"].append("F-WEEK-BY nicht bestanden")
                demoted.append(e)
            else:
                v["labels"] = [lab for lab in v["labels"] if not lab.startswith("vorlaeufig bis F-WEEK")]
                v["labels"].append("F-WEEK-BY abgelehnt (PASS bestaetigt, am Wellenschluss mit den uebrigen Eintraegen der Welle)")
    return {"by": by, "by_double_statement": by_old, "demoted": demoted}
