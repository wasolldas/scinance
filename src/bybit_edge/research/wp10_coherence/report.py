"""WP-10(A) -- JSON + Markdown report and DEC-53 artefacts.

DEC-53: every 3.0 run stores (a) the judgment-bearing series on cluster
(here: calendar-day) level, as CSV with SHA-256, and (b) the bootstrap
seed + generator fingerprint the 1.000 replicates are reproducible from
(same convention as ``wp9_dvol.crossval``: store seed + params, not the
raw replicate array, unless explicitly asked for). A run without BOTH is
"KEIN VERDIKT" -- loud, even though Teil A itself renders no PASS/FAIL:
the artefact CONTRACT still applies (spec: "obwohl A keinen Verdikt
kennt, gilt die Artefakt-Pflicht trotzdem").

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
        raise ValueError(f"refusing to write WP-10(A) artefact under data/harvest: {path}")


def write_cluster_series_csv(series: dict[str, Any], out_dir: Path | str) -> dict[str, Any]:
    """DEC-53 (a): one calendar-day cluster-series CSV per input series."""
    out_dir = Path(out_dir)
    _refuse_harvest(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"wp10a_{series['name']}_daily.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "value"])
        for d, v in zip(series["days"], series["values"]):
            w.writerow([d, v])
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_rows": len(series["days"])}


def write_bootstrap_fingerprint(entries: list[dict[str, Any]], out_dir: Path | str, *,
                                name: str) -> dict[str, Any]:
    """DEC-53 (b): seed + generator fingerprint for every bootstrap run in
    this report -- sufficient to reproduce all replicates bit-identically
    via ``numpy.random.default_rng(seed)``."""
    out_dir = Path(out_dir)
    _refuse_harvest(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"wp10a_{name}_bootstrap_fingerprint.json"
    fp = {"generator": "numpy.random.default_rng", "entries": entries}
    path.write_text(json.dumps(fp, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_entries": len(entries)}


def check_dec53(artifacts: dict[str, Any]) -> None:
    missing = [k for k in ("cluster_series", "bootstrap_fingerprint")
              if not artifacts.get(k)]
    if missing:
        raise ReportError(f"KEIN VERDIKT -- DEC-53-Artefakte fehlen: {missing}")


def _bootstrap_entries(coherence_result: dict[str, Any],
                       portfolio_null: dict[str, Any]) -> list[dict[str, Any]]:
    """``portfolio_null`` carries TWO independently-seeded sub-results
    (``table``: k=2..5 combined-Sharpe null distributions; ``selection_ceiling``:
    K=5..100 expected-max draws) -- both get their own fingerprint entries."""
    entries: list[dict[str, Any]] = []
    for pair in coherence_result.get("pairs", []):
        for regime in ("stress", "quiet"):
            r = pair.get(regime, {})
            if r.get("status") == "OK":
                entries.append({"pair": pair["pair"], "regime": regime, "seed": r["seed"],
                                "n_bootstrap": r["n_bootstrap"], "n": r["n"]})
    for k, r in portfolio_null.get("table", {}).get("results", {}).items():
        entries.append({"portfolio_null_table_k": k, "seed": r["seed"],
                        "n_bootstrap": r["n_bootstrap"], "block_len": r["block_len"]})
    sel = portfolio_null.get("selection_ceiling")
    if sel:
        entries.append({"portfolio_null_selection_ceiling": True, "seed": sel["seed"],
                        "pool_size": sel["pool_size"], "block_len": sel["block_len"]})
    return entries


def build_report(*, series_list: list[dict[str, Any]], coherence_result: dict[str, Any],
                 stress_canon: dict[str, dict[str, Any]], portfolio_null: dict[str, Any],
                 out_dir: Path | str, seed: int) -> dict[str, Any]:
    """Assemble JSON + Markdown, write DEC-53 artefacts FIRST, then raise
    (``ReportError``, "KEIN VERDIKT") if the contract isn't met -- never
    write a summary that claims artefacts it doesn't actually have.

    ``portfolio_null`` is ``{"table": portfolio_null.portfolio_null_table(...),
    "selection_ceiling": portfolio_null.selection_ceiling(...) | None}`` --
    two independently-seeded constants (see that module's docstring for
    why they are kept separate).
    """
    out_dir = Path(out_dir)
    cluster_series = {s["name"]: write_cluster_series_csv(s, out_dir) for s in series_list}
    boot_entries = _bootstrap_entries(coherence_result, portfolio_null)
    bootstrap_fp = write_bootstrap_fingerprint(boot_entries, out_dir, name="coherence")
    artifacts = {"cluster_series": cluster_series, "bootstrap_fingerprint": bootstrap_fp}
    check_dec53(artifacts)

    summary = {
        "wp": "WP-10A", "seed": seed,
        "series": [{"name": s["name"], "kind": s["kind"], "status": s["status"],
                   "coverage": s["coverage"], "reason": s.get("reason")}
                  for s in series_list],
        "stress_canon": stress_canon, "coherence": coherence_result,
        "portfolio_null": portfolio_null, "artifacts": artifacts,
    }
    json_path = out_dir / "wp10a_summary.json"
    json_path.write_text(json.dumps(summary, indent=1, sort_keys=True), encoding="utf-8")
    md_path = out_dir / "wp10a_report.md"
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    return {"summary_path": str(json_path), "markdown_path": str(md_path),
            "artifacts": artifacts, "summary": summary}


def render_markdown(summary: dict[str, Any]) -> str:
    lines = ["# WP-10(A) - Praemien-Kohaerenz im Stress (deskriptiv, KEIN VERDIKT)", ""]
    lines.append("## Serien")
    for s in summary["series"]:
        lines.append(f"- `{s['name']}` ({s['kind']}): status={s['status']}, "
                     f"coverage={s['coverage']}"
                     + (f", reason={s['reason']}" if s.get("reason") else ""))
    lines.append("")
    lines.append("## Stress-Kanon")
    for name, canon in summary["stress_canon"].items():
        if not canon:
            continue
        lines.append(f"- {name}: n_days={canon.get('n_days')}, "
                     f"n_episodes={canon.get('n_episodes')}, sha256={canon.get('sha256', '')[:16]}...")
    lines.append("")
    lines.append("## Kohaerenz (Spearman, STRESS_ABS vs. Ruhe)")
    for pair in summary["coherence"].get("pairs", []):
        s, q = pair.get("stress", {}), pair.get("quiet", {})
        lines.append(f"- {pair['pair'][0]} x {pair['pair'][1]} (n_overlap={pair['n_overlap']}):")
        for regime, r in (("stress", s), ("quiet", q)):
            if r.get("status") == "OK":
                lines.append(f"  - {regime}: rho={r['rho']:.3f}, 95%-CI=[{r['ci_lo']:.3f}, "
                             f"{r['ci_hi']:.3f}], n={r['n']} (n_episodes={r.get('n_episodes')}), "
                             f"Bonett/Wright-SE={r['bonett_wright_se']:.3f}")
            else:
                lines.append(f"  - {regime}: {r.get('status')} (n={r.get('n_days')})")
    lines.append("")
    pn = summary["portfolio_null"]
    lines.append("## Portfolio-Nulleffekt (Konstanten, keine Schwelle)")
    lines.append("### Gleichgewichtungs-Null (k=2..5, Diversifikation)")
    for k, r in pn.get("table", {}).get("results", {}).items():
        lines.append(f"- k={k}: mean_Sharpe={r['mean']:.4f}, sd={r['sd']:.4f}, "
                     f"p95={r['p95']:.4f}, p99={r['p99']:.4f}, "
                     f"n_bootstrap={r['n_bootstrap']}, seed={r['seed']}")
    sel = pn.get("selection_ceiling")
    if sel:
        lines.append("### Selektions-Obergrenze (K=5..100, Bailey/Lopez de Prado)")
        lines.append(f"- sigma_SR={sel['sigma_sr']:.4f} (Pool={sel['pool_size']}, seed={sel['seed']})")
        for K, r in sel["results"].items():
            lines.append(f"- K={K}: E[max]_empirisch={r['empirical_expected_max']:.4f}, "
                         f"E[max]_Bailey/LdP={r['analytic_expected_max']:.4f} "
                         f"(n_groups={r['n_groups']})")
    lines.append("")
    lines.append("## DEC-53-Artefakte")
    for name, a in summary["artifacts"]["cluster_series"].items():
        lines.append(f"- {name}: {a['path']} (n={a['n_rows']}, sha256={a['sha256'][:16]}...)")
    bf = summary["artifacts"]["bootstrap_fingerprint"]
    lines.append(f"- Bootstrap-Fingerprint: {bf['path']} ({bf['n_entries']} Eintraege, "
                 f"sha256={bf['sha256'][:16]}...)")
    lines.append("")
    lines.append(f"(Seed dieses Laufs: {summary['seed']}. Teil A ist deskriptiv -- "
                 "kein PASS/FAIL, keine rho-Schwelle.)")
    return "\n".join(lines) + "\n"
