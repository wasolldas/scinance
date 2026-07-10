"""Pre-registered non-redundancy gate of H-17 against c12_frag/H-12.

Registry H-17 (verbatim, binding): the daily embedding-distance
fragmentation series must have |Spearman rho| < 0.6 against the c12_frag
daily lambda2/IPR series on OVERLAPPING days; |rho| >= 0.6 means H-17 is
declared REDUNDANT to H-12 and is a DROP REGARDLESS of the accuracy.

Wiring against c12_frag (source of truth:
``src/bybit_edge/research/c12_frag/driver.py``): the c12 JSON payload
(``c12_frag_results.json``) carries, per window, per day record with
``analyzed: true``, the fields ``date`` (YYYY-MM-DD), ``lambda2`` and
``ipr_v2`` — that IS the "c12_frag-Tages-lambda2/IPR-Serie" of the registry.
``extract_c12_daily_series`` reads exactly those fields over BOTH windows.
The registry names "lambda2/IPR" as ONE series-pair; conservatively the
gate statistic here is max(|rho_lambda2|, |rho_ipr_v2|) — if EITHER daily
series is |rho| >= 0.6 correlated with the embedding-distance series, H-17
is redundant (the stricter reading; both rhos are reported individually).

H-17 side of the comparison: per fold the HELD-OUT symbol's test windows
give per (day, symbol) the cosine distance between the day-mean Bybit
embedding and the day-mean Binance embedding; the daily fragmentation index
is the mean over the symbols available that day (secondary output,
"nichtlinearer Fragmentierungsindex" — itself NOT verdict-bearing, but the
non-redundancy gate computed FROM it is a binding gate component).

KAPITALFREI: pure series statistics. numpy only.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .stats import spearman_rho

#: Registered redundancy threshold (registry H-17: |rho| >= 0.6 -> DROP).
REDUNDANCY_RHO_MAX = 0.6

#: Technical evaluability floor for the overlap (NOT a registered threshold):
#: with fewer overlapping days a rank correlation is numerically meaningless.
#: Below the floor the gate is NOT evaluable -> no WEITER possible, but also
#: NOT an automatic redundancy-DROP (gate-auditor adjudicates).
MIN_OVERLAP_DAYS = 10


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """1 - cosine similarity of two embedding vectors."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na <= 0.0 or nb <= 0.0 or not (np.isfinite(na) and np.isfinite(nb)):
        return float("nan")
    return float(1.0 - np.dot(a, b) / (na * nb))


def daily_embedding_distance_series(
    embeddings: np.ndarray,
    dates: np.ndarray,
    symbols: np.ndarray,
    venues: np.ndarray,
) -> dict[str, Any]:
    """Daily cross-venue embedding-distance series from held-out embeddings.

    Per (date, symbol) with BOTH venues present: cosine distance between the
    venue-mean embeddings. Daily index = mean over the symbols available
    that day. Returns ``{"per_symbol": {sym: {date: d}}, "daily": {date: d}}``.
    """
    embeddings = np.asarray(embeddings, dtype=np.float64)
    dates = np.asarray(dates)
    symbols = np.asarray(symbols)
    venues = np.asarray(venues)
    per_symbol: dict[str, dict[str, float]] = {}
    for sym in np.unique(symbols):
        sym_sel = symbols == sym
        series: dict[str, float] = {}
        for day in np.unique(dates[sym_sel]):
            sel = sym_sel & (dates == day)
            vs = np.unique(venues[sel])
            if vs.size < 2:
                continue
            means = [embeddings[sel & (venues == v)].mean(axis=0) for v in sorted(vs)]
            d = cosine_distance(means[0], means[1])
            if np.isfinite(d):
                series[str(day)] = d
        if series:
            per_symbol[str(sym)] = series
    daily: dict[str, float] = {}
    all_days = sorted({d for s in per_symbol.values() for d in s})
    for day in all_days:
        vals = [s[day] for s in per_symbol.values() if day in s]
        daily[day] = float(np.mean(vals))
    return {"per_symbol": per_symbol, "daily": daily}


def extract_c12_daily_series(
    c12_payload: dict[str, Any],
) -> tuple[dict[str, float], dict[str, float]]:
    """Daily (lambda2, ipr_v2) series from a c12_frag JSON payload.

    Reads ``payload["windows"][*]["days"][*]`` records with
    ``analyzed == True`` (the exact structure ``c12_frag.driver.run``
    emits) and returns ``({date: lambda2}, {date: ipr_v2})``.
    """
    lam2: dict[str, float] = {}
    ipr2: dict[str, float] = {}
    for win in c12_payload.get("windows", []):
        for day in win.get("days", []):
            if not day.get("analyzed"):
                continue
            date = str(day["date"])
            lam2[date] = float(day["lambda2"])
            ipr2[date] = float(day["ipr_v2"])
    return lam2, ipr2


def redundancy_gate(
    embed_daily: dict[str, float],
    c12_payload: dict[str, Any] | None,
    *,
    rho_max: float = REDUNDANCY_RHO_MAX,
    min_overlap_days: int = MIN_OVERLAP_DAYS,
) -> dict[str, Any]:
    """Evaluate the pre-registered non-redundancy gate against c12_frag.

    Returns a gate-neutral record: rho against BOTH c12 daily series
    (lambda2 and ipr_v2) on overlapping days, the conservative gate
    statistic max(|rho|), and the flags:

      * ``evaluable``  — c12 payload present AND overlap >= floor,
      * ``redundant``  — evaluable AND max|rho| >= 0.6 (registered DROP),
      * ``passed``     — evaluable AND max|rho| < 0.6.

    Not evaluable => neither passed nor redundant (WEITER is blocked, the
    gate-auditor adjudicates; NOT an automatic redundancy-DROP).
    """
    rec: dict[str, Any] = {
        "rho_max_registered": float(rho_max),
        "min_overlap_days_technical": int(min_overlap_days),
        "c12_payload_present": c12_payload is not None,
        "n_overlap_days": 0,
        "rho_lambda2": None,
        "rho_ipr_v2": None,
        "max_abs_rho": None,
        "evaluable": False,
        "redundant": False,
        "passed": False,
        "note": (
            "Registry H-17: |Spearman rho| >= 0,6 gegen die c12_frag-Tages-"
            "lambda2/IPR-Serie an ueberlappenden Tagen = REDUNDANT zu H-12 "
            "= DROP unabhaengig von der Accuracy. Konservative Lesart: "
            "max(|rho_lambda2|, |rho_ipr_v2|) ist die Gate-Statistik."
        ),
    }
    if c12_payload is None:
        return rec
    lam2, ipr2 = extract_c12_daily_series(c12_payload)
    overlap = sorted(set(embed_daily) & set(lam2))
    rec["n_overlap_days"] = len(overlap)
    if len(overlap) < min_overlap_days:
        return rec
    e = np.array([embed_daily[d] for d in overlap], dtype=np.float64)
    l = np.array([lam2[d] for d in overlap], dtype=np.float64)
    i = np.array([ipr2[d] for d in overlap], dtype=np.float64)
    rho_l = spearman_rho(e, l)
    rho_i = spearman_rho(e, i)
    rec["rho_lambda2"] = None if np.isnan(rho_l) else float(rho_l)
    rec["rho_ipr_v2"] = None if np.isnan(rho_i) else float(rho_i)
    abs_rhos = [abs(r) for r in (rho_l, rho_i) if np.isfinite(r)]
    if not abs_rhos:
        return rec
    max_abs = float(max(abs_rhos))
    rec["max_abs_rho"] = max_abs
    rec["evaluable"] = True
    rec["redundant"] = bool(max_abs >= rho_max)
    rec["passed"] = bool(max_abs < rho_max)
    return rec


__all__ = [
    "MIN_OVERLAP_DAYS",
    "REDUNDANCY_RHO_MAX",
    "cosine_distance",
    "daily_embedding_distance_series",
    "extract_c12_daily_series",
    "redundancy_gate",
]
