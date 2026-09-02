"""WP-10(B) -- fill-rate curves, adverse selection, "Maker-Vorteil" LABEL
(no PASS/FAIL), DEC-53 artefacts.

``adv_sel <= 1,75 bp`` (PRD 3.0 B.3: ``(FEE_TAKER-FEE_MAKER)/2`` -- factor
2 over the maker/taker break-even, consistent with every other
Break-even-mal-2 threshold in the programme) is applied as a LABEL,
"Maker-Vorteil traegt" / "traegt nicht" -- never PASS/FAIL, and
``p_fill`` itself carries NO threshold at all (spec: "Keine Schwelle fuer
p_fill"), only a reported curve.

DEC-53: every 3.0 run stores (a) the judgment-bearing series on cluster
(here: PER-QUOTE, the finest granularity available) level, as CSV with
SHA-256, and (b) the bootstrap seed + generator fingerprint every CI in
this report is reproducible from (same convention as
``wp10_coherence.report`` / ``wp9_dvol.crossval``: store seed + params,
not the raw replicate array). A run without BOTH is "KEIN VERDIKT" --
loud.

KAPITALFREI: report plumbing only. No cost quantity, no PASS/FAIL logic.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from . import queue_model as qm
from . import replay as rp

__all__ = [
    "ReportError", "ADV_SEL_LABEL_THRESHOLD_BP", "hour_of_day",
    "load_quote_rows", "p_fill_curve", "adv_sel_stats", "maker_vantage_label",
    "cluster_bootstrap_ci", "write_quote_outcomes_csv",
    "write_bootstrap_fingerprint", "check_dec53", "build_report",
    "render_markdown",
]

#: PRD 3.0 B.3 / WP10_SPEZIFIKATION.md Teil B: (FEE_TAKER-FEE_MAKER)/2 =
#: (5.5-2.0)/2 = 1.75 bp -- factor 2 over the maker/taker break-even.
ADV_SEL_LABEL_THRESHOLD_BP = 1.75


class ReportError(RuntimeError):
    """DEC-53: required result artefacts are missing -- KEIN VERDIKT."""


def _refuse_harvest(path: Path) -> None:
    if "data/harvest" in str(path).replace("\\", "/"):
        raise ValueError(f"refusing to write WP-10(B) artefact under data/harvest: {path}")


def hour_of_day(minute_idx: int) -> int:
    """Hour-of-day (UTC) of an epoch-minute index (spec: "je Stunde des Tages")."""
    return (int(minute_idx) % 1440) // 60


def load_quote_rows(
    out_dir: Path | str, exchange: str, symbols: Sequence[str], start: str, end: str,
    *, stress_days: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Flatten every OK day's quote rows across ``symbols`` into one list,
    each row tagged with ``hour`` and (if ``stress_days`` given, the
    STRESS_ABS/DEC-56 fixture's ``days`` set) ``regime`` in
    ``{"stress","quiet"}`` -- ``None`` when no stress canon was supplied
    (report renders a single ungrouped regime bucket in that case, never
    silently drops the field)."""
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        for entry in rp.load_daily_fillshadow(out_dir, exchange, symbol, start, end):
            day, q = entry["day"], entry["quotes"]
            regime = None
            if stress_days is not None:
                regime = "stress" if day in stress_days else "quiet"
            for i in range(len(q["minute_idx"])):
                rows.append({
                    "symbol": symbol, "day": day,
                    "hour": hour_of_day(q["minute_idx"][i]),
                    "side": q["side"][i], "regime": regime,
                    "fifo_filled": q["fifo_filled"][i],
                    "fifo_latency_s": q["fifo_latency_s"][i],
                    "fifo_adv_sel_bp": q["fifo_adv_sel_bp"][i],
                    "prorata_filled": q["prorata_filled"][i],
                    "prorata_latency_s": q["prorata_latency_s"][i],
                    "prorata_adv_sel_bp": q["prorata_adv_sel_bp"][i],
                    "insufficient_forward_data": q["insufficient_forward_data"][i],
                })
    return rows


def _grouped(rows: Sequence[dict[str, Any]], group_by: Sequence[str]):
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["insufficient_forward_data"]:
            continue
        groups[tuple(r[k] for k in group_by)].append(r)
    return groups


def p_fill_curve(
    rows: Sequence[dict[str, Any]], *, convention: str = "fifo",
    group_by: Sequence[str] = ("symbol", "side"),
    horizons_s: Sequence[float] = qm.REPORT_HORIZONS_S,
) -> list[dict[str, Any]]:
    """``p_fill(t)`` for each ``t`` in ``horizons_s`` per group. Quotes
    flagged ``insufficient_forward_data`` (the horizon ran past the end
    of the loaded window) are EXCLUDED -- an honest denominator, never a
    silently right-censored one counted as "not filled"."""
    filled_key, lat_key = f"{convention}_filled", f"{convention}_latency_s"
    out = []
    for key, grp in sorted(_grouped(rows, group_by).items()):
        n = len(grp)
        row = {**dict(zip(group_by, key)), "convention": convention, "n": n}
        for t in horizons_s:
            nf = sum(1 for r in grp if r[filled_key] and r[lat_key] is not None and r[lat_key] <= t)
            row[f"p_fill_{int(t)}s"] = (nf / n) if n else None
            row[f"n_filled_{int(t)}s"] = nf
        out.append(row)
    return out


def adv_sel_stats(
    rows: Sequence[dict[str, Any]], *, convention: str = "fifo",
    group_by: Sequence[str] = ("symbol", "side"),
) -> list[dict[str, Any]]:
    """Distribution of ``adv_sel_bp`` over FILLED quotes per group, plus
    the "Maker-Vorteil traegt" / "traegt nicht" LABEL (never PASS/FAIL)."""
    filled_key, adv_key = f"{convention}_filled", f"{convention}_adv_sel_bp"
    out = []
    for key, grp in sorted(_grouped(rows, group_by).items()):
        vals = [r[adv_key] for r in grp if r[filled_key] and r[adv_key] is not None]
        arr = np.asarray(vals, dtype=np.float64)
        row = {**dict(zip(group_by, key)), "convention": convention, "n_filled": int(arr.size)}
        if arr.size:
            mean = float(np.mean(arr))
            row.update(mean_bp=mean, median_bp=float(np.median(arr)),
                      p10_bp=float(np.quantile(arr, 0.10)),
                      p90_bp=float(np.quantile(arr, 0.90)),
                      label=maker_vantage_label(mean))
        else:
            row.update(mean_bp=None, median_bp=None, p10_bp=None, p90_bp=None,
                      label="KEIN VERDIKT (0 Fills in dieser Gruppe)")
        out.append(row)
    return out


def maker_vantage_label(adv_sel_mean_bp: float) -> str:
    return ("Maker-Vorteil traegt" if adv_sel_mean_bp <= ADV_SEL_LABEL_THRESHOLD_BP
            else "Maker-Vorteil traegt nicht")


def cluster_bootstrap_ci(
    rows: Sequence[dict[str, Any]], *, metric: str, convention: str = "fifo",
    group_by: Sequence[str] = ("symbol", "side"), horizon_s: float = 60.0,
    n_bootstrap: int = 1000, seed: int = 53,
) -> list[dict[str, Any]]:
    """95%-CI via a CALENDAR-DAY cluster bootstrap (DEC-53's cluster unit,
    same as WP-10(A)): resample days with replacement, recompute the
    group mean each draw. ``metric`` is ``"p_fill"`` (fraction filled by
    ``horizon_s``) or ``"adv_sel"`` (mean ``adv_sel_bp`` over fills)."""
    if metric not in ("p_fill", "adv_sel"):
        raise ValueError(f"metric must be 'p_fill' or 'adv_sel', got {metric!r}")
    filled_key = f"{convention}_filled"
    lat_key = f"{convention}_latency_s"
    adv_key = f"{convention}_adv_sel_bp"

    by_group_day: dict[tuple, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["insufficient_forward_data"]:
            continue
        by_group_day[tuple(r[k] for k in group_by)][r["day"]].append(r)

    out = []
    for key, by_day in sorted(by_group_day.items()):
        days = sorted(by_day)
        day_vals = []
        for d in days:
            grp = by_day[d]
            if metric == "p_fill":
                n = len(grp)
                nf = sum(1 for r in grp if r[filled_key] and r[lat_key] is not None and r[lat_key] <= horizon_s)
                day_vals.append(nf / n if n else np.nan)
            else:
                vals = [r[adv_key] for r in grp if r[filled_key] and r[adv_key] is not None]
                day_vals.append(float(np.mean(vals)) if vals else np.nan)
        day_arr = np.asarray(day_vals, dtype=np.float64)
        valid = day_arr[~np.isnan(day_arr)]
        row = {**dict(zip(group_by, key)), "metric": metric, "convention": convention,
              "n_days": int(valid.size), "seed": seed, "n_bootstrap": n_bootstrap}
        if valid.size == 0:
            row.update(estimate=None, ci_lo=None, ci_hi=None)
        else:
            rng = np.random.default_rng(seed)
            boots = np.array([float(np.mean(rng.choice(valid, size=valid.size, replace=True)))
                              for _ in range(n_bootstrap)])
            row.update(estimate=float(np.mean(valid)),
                      ci_lo=float(np.quantile(boots, 0.025)),
                      ci_hi=float(np.quantile(boots, 0.975)))
        out.append(row)
    return out


# ----------------------------------------------------------------------------
# DEC-53 artefacts
# ----------------------------------------------------------------------------

def write_quote_outcomes_csv(rows: Sequence[dict[str, Any]], out_dir: Path | str) -> dict[str, Any]:
    """DEC-53 (a): the per-quote outcome series -- the finest cluster unit
    this report has (one row per placed hypothetical quote)."""
    out_dir = Path(out_dir)
    _refuse_harvest(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "wp10b_quote_outcomes.csv"
    fields = ["symbol", "day", "hour", "side", "regime",
             "fifo_filled", "fifo_latency_s", "fifo_adv_sel_bp",
             "prorata_filled", "prorata_latency_s", "prorata_adv_sel_bp",
             "insufficient_forward_data"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_rows": len(rows)}


def write_bootstrap_fingerprint(entries: list[dict[str, Any]], out_dir: Path | str) -> dict[str, Any]:
    """DEC-53 (b): seed + generator fingerprint for every bootstrap CI in
    this report -- sufficient to reproduce all replicates bit-identically."""
    out_dir = Path(out_dir)
    _refuse_harvest(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "wp10b_bootstrap_fingerprint.json"
    fp = {"generator": "numpy.random.default_rng", "entries": entries}
    path.write_text(json.dumps(fp, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_entries": len(entries)}


def check_dec53(artifacts: dict[str, Any]) -> None:
    missing = [k for k in ("quote_outcomes", "bootstrap_fingerprint") if not artifacts.get(k)]
    if missing:
        raise ReportError(f"KEIN VERDIKT -- DEC-53-Artefakte fehlen: {missing}")


# ----------------------------------------------------------------------------
# assembly
# ----------------------------------------------------------------------------

def build_report(*, rows: list[dict[str, Any]], out_dir: Path | str, seed: int = 53,
                 n_bootstrap: int = 1000) -> dict[str, Any]:
    """Assemble JSON + Markdown, write DEC-53 artefacts FIRST, then raise
    (``ReportError``, "KEIN VERDIKT") if the contract isn't met -- never
    write a summary that claims artefacts it doesn't actually have."""
    out_dir = Path(out_dir)
    conventions = ("fifo", "prorata")
    p_fill = {c: p_fill_curve(rows, convention=c, group_by=("symbol", "side")) for c in conventions}
    p_fill_by_hour = {c: p_fill_curve(rows, convention=c, group_by=("symbol", "side", "hour")) for c in conventions}
    p_fill_by_regime = {c: p_fill_curve(rows, convention=c, group_by=("symbol", "side", "regime")) for c in conventions}
    adv_sel = {c: adv_sel_stats(rows, convention=c, group_by=("symbol", "side")) for c in conventions}
    adv_sel_by_regime = {c: adv_sel_stats(rows, convention=c, group_by=("symbol", "side", "regime")) for c in conventions}
    ci_p_fill = cluster_bootstrap_ci(rows, metric="p_fill", convention="fifo",
                                     group_by=("symbol", "side"), seed=seed, n_bootstrap=n_bootstrap)
    ci_adv_sel = cluster_bootstrap_ci(rows, metric="adv_sel", convention="fifo",
                                      group_by=("symbol", "side"), seed=seed, n_bootstrap=n_bootstrap)

    artifacts: dict[str, Any] = {}
    artifacts["quote_outcomes"] = write_quote_outcomes_csv(rows, out_dir)
    boot_entries = [{"group": {k: r[k] for k in ("symbol", "side")}, "metric": r["metric"],
                     "convention": r["convention"], "seed": r["seed"],
                     "n_bootstrap": r["n_bootstrap"], "n_days": r["n_days"]}
                    for r in ci_p_fill + ci_adv_sel]
    artifacts["bootstrap_fingerprint"] = write_bootstrap_fingerprint(boot_entries, out_dir)
    check_dec53(artifacts)

    summary = {
        "wp": "WP-10B", "seed": seed, "n_quotes_total": len(rows),
        "horizons_s": list(qm.REPORT_HORIZONS_S),
        "adv_sel_horizon_s": qm.DEFAULT_ADV_SEL_HORIZON_S,
        "label_threshold_bp": ADV_SEL_LABEL_THRESHOLD_BP,
        "p_fill": p_fill, "p_fill_by_hour": p_fill_by_hour, "p_fill_by_regime": p_fill_by_regime,
        "adv_sel": adv_sel, "adv_sel_by_regime": adv_sel_by_regime,
        "bootstrap_ci": {"p_fill_fifo": ci_p_fill, "adv_sel_fifo": ci_adv_sel},
        "artifacts": artifacts,
    }
    json_path = out_dir / "wp10b_summary.json"
    json_path.write_text(json.dumps(summary, indent=1, sort_keys=True, default=str), encoding="utf-8")
    md_path = out_dir / "wp10b_report.md"
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    return {"summary_path": str(json_path), "markdown_path": str(md_path),
            "artifacts": artifacts, "summary": summary}


def render_markdown(summary: dict[str, Any]) -> str:
    lines = ["# WP-10(B) - Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate)", "",
            f"Quotes gesamt: {summary['n_quotes_total']} | Horizonte (Design-Parameter): "
            f"{summary['horizons_s']} s | adv_sel-Horizont: {summary['adv_sel_horizon_s']} s | "
            f"Etikett-Schwelle: {summary['label_threshold_bp']} bp"]
    lines.append("")
    lines.append("## Fill-Rate-Kurve p_fill(t) (FIFO-conservative / pro-rata-cancel)")
    for conv in ("fifo", "prorata"):
        lines.append(f"### {conv}")
        for r in summary["p_fill"][conv]:
            p10 = r.get("p_fill_10s")
            p60 = r.get("p_fill_60s")
            lines.append(f"- {r['symbol']} {r['side']} (n={r['n']}): "
                         f"p_fill(10s)={'n/a' if p10 is None else f'{p10:.3f}'}, "
                         f"p_fill(60s)={'n/a' if p60 is None else f'{p60:.3f}'}")
    lines.append("")
    lines.append("## Adverse Selektion (mittlere Mid-Bewegung gegen die Quote, bp) + Etikett")
    for conv in ("fifo", "prorata"):
        lines.append(f"### {conv}")
        for r in summary["adv_sel"][conv]:
            if r["n_filled"] == 0:
                lines.append(f"- {r['symbol']} {r['side']}: {r['label']}")
                continue
            lines.append(f"- {r['symbol']} {r['side']} (n_filled={r['n_filled']}): "
                         f"mean={r['mean_bp']:.3f} bp, median={r['median_bp']:.3f} bp -> {r['label']}")
    lines.append("")
    lines.append("## Bootstrap-CI (95%, Kalendertag-Cluster, FIFO)")
    for r in summary["bootstrap_ci"]["p_fill_fifo"]:
        est = r["estimate"]
        lines.append(f"- p_fill(60s) {r['symbol']} {r['side']} (n_days={r['n_days']}): "
                     + ("n/a" if est is None else f"{est:.3f} [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]")
                     + f" (seed={r['seed']}, n_bootstrap={r['n_bootstrap']})")
    for r in summary["bootstrap_ci"]["adv_sel_fifo"]:
        est = r["estimate"]
        lines.append(f"- adv_sel {r['symbol']} {r['side']} (n_days={r['n_days']}): "
                     + ("n/a" if est is None else f"{est:.3f} bp [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]")
                     + f" (seed={r['seed']}, n_bootstrap={r['n_bootstrap']})")
    lines.append("")
    lines.append("## DEC-53-Artefakte")
    qo = summary["artifacts"]["quote_outcomes"]
    lines.append(f"- Quote-Outcomes: {qo['path']} (n={qo['n_rows']}, sha256={qo['sha256'][:16]}...)")
    bf = summary["artifacts"]["bootstrap_fingerprint"]
    lines.append(f"- Bootstrap-Fingerprint: {bf['path']} ({bf['n_entries']} Eintraege, "
                 f"sha256={bf['sha256'][:16]}...)")
    lines.append("")
    lines.append("(Kein PASS/FAIL. p_fill traegt keine Schwelle; adv_sel <= "
                 f"{summary['label_threshold_bp']} bp ist ein ETIKETT "
                 "\"Maker-Vorteil traegt\"/\"traegt nicht\", je Gruppe und Konvention "
                 "getrennt berichtet -- FIFO ist die untere, pro-rata die obere Schranke.)")
    return "\n".join(lines) + "\n"
