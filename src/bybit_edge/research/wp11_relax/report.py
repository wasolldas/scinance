"""WP-11 -- JSON + Markdown report and DEC-53 artefacts.

DEC-53: every 3.0 run stores (a) the judgment-bearing series on cluster
level (here: one row per event x variable, event_day = the cluster) as
CSV with SHA-256, and (b) the bootstrap seed + generator fingerprint the
replicates are reproducible from. A run without BOTH is "KEIN VERDIKT" --
loud, even though this package renders no PASS/FAIL (Arm (a) is
descriptive throughout, PRD 11.3): the artefact CONTRACT still applies.

NEVER writes under ``data/harvest`` (loud refusal, same convention as
``wp10_coherence.stress_canon``/``report``).

KAPITALFREI: report plumbing only. No cost quantity, no PASS/FAIL logic.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

__all__ = [
    "ReportError", "write_cluster_series_csv", "write_bootstrap_fingerprint",
    "check_dec53", "build_report", "render_markdown",
]


class ReportError(RuntimeError):
    """DEC-53: required result artefacts are missing -- KEIN VERDIKT."""


def _refuse_harvest(path: Path) -> None:
    if "data/harvest" in str(path).replace("\\", "/"):
        raise ValueError(f"refusing to write WP-11 artefact under data/harvest: {path}")


_CSV_COLUMNS = (
    "symbol", "event_date", "event_hour", "era", "stress_abs", "variable",
    "baseline", "phi", "lambda_per_h", "half_life_h", "r2", "n_pairs",
    "t_return_defined", "t_return_h", "censored", "shock_excess",
)


def write_cluster_series_csv(rows: list[dict[str, Any]], out_dir: Path | str, *,
                             name: str) -> dict[str, Any]:
    """DEC-53 (a): the per-event x variable cluster-level series (cluster =
    ``event_date``, DEC-51 point 3) as one CSV. NEVER under data/harvest."""
    out_dir = Path(out_dir)
    _refuse_harvest(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"wp11_{name}_events.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(_CSV_COLUMNS)
        for row in rows:
            w.writerow([row.get(c) for c in _CSV_COLUMNS])
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
           "n_rows": len(rows)}


def write_bootstrap_fingerprint(payload: dict[str, Any], out_dir: Path | str) -> dict[str, Any]:
    """DEC-53 (b): seed + generator fingerprint sufficient to reproduce
    every WP-11 bootstrap (median-lambda CI, P90-time-to-return CI) bit-
    identically via ``numpy.random.default_rng(seed)``."""
    out_dir = Path(out_dir)
    _refuse_harvest(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "wp11_bootstrap_fingerprint.json"
    fp = {"generator": "numpy.random.default_rng",
         "seed": payload["method"]["seed"],
         "n_bootstrap_reps": 1000, "min_event_clusters": payload["method"]["min_event_clusters"]}
    path.write_text(json.dumps(fp, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def check_dec53(artifacts: dict[str, Any]) -> None:
    missing = [k for k in ("cluster_series", "bootstrap_fingerprint") if not artifacts.get(k)]
    if missing:
        raise ReportError(f"KEIN VERDIKT -- DEC-53-Artefakte fehlen: {missing}")


def build_report(payload: dict[str, Any], out_dir: Path | str) -> dict[str, Any]:
    """Assemble JSON + Markdown, write DEC-53 artefacts FIRST, then raise
    (``ReportError``, "KEIN VERDIKT") if the contract isn't met -- never
    write a summary that claims artefacts it doesn't actually have.

    ``payload`` is ``measure.run()``'s return value, INCLUDING the
    private ``_real_rows``/``_pseudo_rows`` keys (consumed here, stripped
    from the written JSON summary).
    """
    out_dir = Path(out_dir)
    real_rows = payload.get("_real_rows", [])
    pseudo_rows = payload.get("_pseudo_rows", [])
    cluster_series = {
        "real": write_cluster_series_csv(real_rows, out_dir, name="real"),
        "pseudo_null": write_cluster_series_csv(pseudo_rows, out_dir, name="pseudo_null"),
    }
    bootstrap_fp = write_bootstrap_fingerprint(payload, out_dir)
    artifacts = {"cluster_series": cluster_series, "bootstrap_fingerprint": bootstrap_fp}
    check_dec53(artifacts)

    summary = {k: v for k, v in payload.items() if not k.startswith("_")}
    summary["artifacts"] = artifacts
    json_path = out_dir / "wp11_summary.json"
    json_path.write_text(json.dumps(summary, indent=1, sort_keys=True, default=str), encoding="utf-8")
    md_path = out_dir / "wp11_report.md"
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    return {"summary_path": str(json_path), "markdown_path": str(md_path),
           "artifacts": artifacts, "summary": summary}


def _fmt(v: Any, digits: int = 3) -> str:
    if v is None:
        return "-"
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return str(v)
    if fv != fv:  # NaN
        return "-"
    return f"{fv:.{digits}f}"


def render_markdown(summary: dict[str, Any]) -> str:
    L: list[str] = ["# WP-11 -- Relaxationsrate nach Schockstunden (deskriptiv, KEIN VERDIKT)", ""]
    L.append(f"- **Paket:** {summary['package']} -- `{summary['prd_ref']}`")
    L.append(f"- **Erzeugt:** {summary['generated_at']} (UTC) - Status: {summary['status']}")
    L.append(f"- **Semantik:** {summary['verdict_semantics']}")
    L.append(f"- **Datenbindung:** WP-0-Bar-Cache - `gate_valid={str(summary['gate_valid']).lower()}`")
    L.append(f"- **Ereignisse:** {summary['n_events_real']} real, "
             f"{summary['n_events_pseudo_null']} gematchter Pseudo-Null, "
             f"{summary['n_event_clusters_total']} Ereignistage gesamt")
    L.append(f"- **Event-Definition:** {summary['method']['event']}")
    L.append(f"- **Fit:** {summary['method']['fit']}")
    L.append(f"- **Time-to-Return:** {summary['method']['time_to_return']}")
    L.append("")

    L.append("## (i) Median-Halbwertszeit je Symbol (gepoolt ueber Aera/Regime)")
    L.append("")
    L.append("| Symbol | Variable | Events | Tage | KEIN BEFUND | median T_half (h) | KI90 |")
    L.append("|---|---|---:|---:|:---:|---:|---|")
    for c in summary["pre_fixed"]["median_half_life_per_symbol"]:
        if c.get("kein_befund"):
            L.append(f"| {c['symbol']} | {c['variable']} | {c.get('n_events', 0)} | "
                     f"{c.get('n_clusters', 0)} | **JA** | - | - |")
            continue
        hl = c["half_life_h"]
        ci = "-" if hl["ci_lo"] is None else f"[{_fmt(hl['ci_lo'])}, {_fmt(hl['ci_hi'])}]"
        L.append(f"| {c['symbol']} | {c['variable']} | {c['n_events']} | {c['n_clusters']} | nein | "
                 f"{_fmt(hl['point'])} | {ci} |")
    L.append("")

    L.append("## (ii) RECOVERY_H_P90 (STRESS_ABS, Kostenmodell-Konstante)")
    L.append("")
    L.append("| Variable | Events | Tage | KEIN BEFUND | P90 (h) | zensiert | KI90 |")
    L.append("|---|---:|---:|:---:|---:|:---:|---|")
    for c in summary["pre_fixed"]["recovery_h_p90"]:
        if c.get("kein_befund"):
            L.append(f"| {c['variable']} | {c.get('n_events', 0)} | {c.get('n_clusters', 0)} | "
                     f"**JA** | - | - | - |")
            continue
        p90 = c["p90_time_to_return_h"]
        ci = f"[{_fmt(p90['ci_lo'])}, {_fmt(p90['ci_hi'])}]"
        L.append(f"| {c['variable']} | {c['n_events']} | {c['n_clusters']} | nein | "
                 f"{_fmt(p90['point'])} | {'ja' if p90['censored_at_p90'] else 'nein'} | {ci} |")
    L.append("")

    L.append("## (iii) Aera-Vergleich -- \"ist der H-20-Aera-invariant?\" (deskriptiv, KEIN Gate)")
    L.append("")
    L.append("| Aera | Variable | Events | Tage | KEIN BEFUND | median T_half (h) | KI90 |")
    L.append("|---|---|---:|---:|:---:|---:|---|")
    for c in summary["pre_fixed"]["era_invariance_descriptive"]:
        if c.get("kein_befund"):
            L.append(f"| {c['era']} | {c['variable']} | {c.get('n_events', 0)} | "
                     f"{c.get('n_clusters', 0)} | **JA** | - | - |")
            continue
        hl = c["half_life_h"]
        ci = "-" if hl["ci_lo"] is None else f"[{_fmt(hl['ci_lo'])}, {_fmt(hl['ci_hi'])}]"
        L.append(f"| {c['era']} | {c['variable']} | {c['n_events']} | {c['n_clusters']} | nein | "
                 f"{_fmt(hl['point'])} | {ci} |")
    L.append("")
    L.append("*(iii) ist rein deskriptiv: KEIN PASS/FAIL, KEINE Schwelle -- Auflage PRD 11.3.*")
    L.append("")

    L.append("## Struktureller-Nulleffekt-Diagnostik (gematchter Pseudo-Zufalls-Null)")
    L.append("")
    L.append("| Symbol | Variable | n_obs | n_null | Var(lambda_obs) | Var(lambda_null) | Verhaeltnis |")
    L.append("|---|---|---:|---:|---:|---:|---:|")
    for s in summary["structural_null"]:
        L.append(f"| {s['symbol']} | {s['variable']} | {s['n_obs']} | {s['n_null']} | "
                 f"{_fmt(s['var_obs'], 5)} | {_fmt(s['var_null'], 5)} | {_fmt(s['var_ratio'], 2)} |")
    L.append("")
    L.append("*Diagnostik, KEIN Gate: ein Verhaeltnis nahe 1 spricht gegen einen "
             "Selektionsartefakt der Ereignis-Extremwertauswahl; Arm (a) faellt kein Urteil "
             "darauf (PRD 11.3, Exkurs X-OEKO-1 Arm (b) waere die getrennt zu "
             "registrierende Folgehypothese).*")
    L.append("")

    L.append("## DEC-53-Artefakte")
    for name, a in summary["artifacts"]["cluster_series"].items():
        L.append(f"- {name}: {a['path']} (n={a['n_rows']}, sha256={a['sha256'][:16]}...)")
    bf = summary["artifacts"]["bootstrap_fingerprint"]
    L.append(f"- Bootstrap-Fingerprint: {bf['path']} (sha256={bf['sha256'][:16]}...)")
    L.append("")
    L.append(f"(Seed dieses Laufs: {summary['method']['seed']}. WP-11 ist deskriptiv -- "
            "kein PASS/FAIL, keine Halbwertszeit-Schwelle.)")
    return "\n".join(L) + "\n"
