"""Report rendering for the E-15 evaluation (JSON + Markdown).

Both artifacts carry the H-01 registry reference and a UTC timestamp so the
gate-auditor can match them against
``scinance2-impl/state/hypothesis_registry.md`` (no post-hoc goalposts).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-01"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"

JSON_FILENAME = "e15_evaluation.json"
MD_FILENAME = "e15_evaluation.md"


def build_payload(
    metrics: dict[str, Any],
    gate: dict[str, Any],
    e17: dict[str, Any],
    inputs: dict[str, Optional[str]],
) -> dict[str, Any]:
    """Assemble the machine-readable evaluation payload."""
    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": inputs,
        "gate_verdict": gate["gate_verdict"],
        "gate_details": gate["gate_details"],
        "fix_effectiveness_pass": gate["fix_effectiveness_pass"],
        "e17_resolved": e17["resolved"],
        "e17_reasoning": e17["reasoning"],
        "e17_details": e17["details"],
        "metrics": metrics,
    }


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the human-readable Markdown report (German, repo convention)."""
    m = payload["metrics"]
    agg = m["aggregate"]
    lines: list[str] = []
    lines.append("# E-15-Auswertung (H-01 · S3 Pre-Settlement, iter-5)")
    lines.append("")
    lines.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    lines.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    for key, value in payload["inputs"].items():
        lines.append(f"- **Input `{key}`:** `{value}`")
    lines.append("")
    lines.append(f"## Gate-Urteil: **{payload['gate_verdict']}**")
    lines.append("")
    lines.append(
        "> Maschinelles Urteil exakt gegen die vorregistrierten H-01-Tore. "
        "Verbindlich wird es erst nach gate-auditor-Pruefung (T2 auf Echtdaten)."
    )
    lines.append("")
    lines.append("| Kriterium | Registry-Text (woertlich) | Operationalisierung | Messwert | Bestanden |")
    lines.append("|---|---|---|---|---|")
    for d in payload["gate_details"]:
        lines.append(
            f"| `{d['id']}` | {d['registry_text']} | {d['operationalisation']} "
            f"| {_fmt(d['measured'])} | {_fmt(d['passed'])} |"
        )
    lines.append("")
    lines.append(
        f"**Fix-Wirksamkeit gesamt:** {_fmt(payload['fix_effectiveness_pass'])} "
        "(informativ — nicht urteils-tragend, s. Operationalisierung)"
    )
    lines.append("")
    lines.append("## S3-Metriken (netto = inkl. Fees, raw = Fees zurueckgerechnet)")
    lines.append("")
    header = (
        "| Symbol | n | mean bps (netto) | median bps (netto) | mean bps (raw) "
        "| n>120s | n<-30bps | time_stop | hard_stop | max Dauer (s) | worst trade (bps) |"
    )
    lines.append(header)
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    def _row(name: str, s: dict[str, Any]) -> str:
        return (
            f"| {name} | {s['n_trades']} | {_fmt(s['mean_pnl_bps_net'])} "
            f"| {_fmt(s['median_pnl_bps_net'])} | {_fmt(s['mean_raw_edge_bps'])} "
            f"| {s['n_over_120s']} | {s['n_below_minus_30bps']} "
            f"| {_fmt(s['time_stop_exceeded_count'])} "
            f"| {_fmt(s['hard_stop_loss_count'])} "
            f"| {_fmt(s['max_duration_seconds'], 1)} "
            f"| {_fmt(s['worst_trade']['pnl_bps'])} |"
        )

    for symbol, stats in m["per_symbol"].items():
        lines.append(_row(symbol, stats))
    lines.append(_row("**Aggregat**", agg))
    lines.append("")
    worst = agg["worst_trade"]
    lines.append(
        f"Worst Trade gesamt: {worst['symbol']} {_fmt(worst['pnl_bps'])} bps "
        f"({_fmt(worst['pnl_net'])} USD, {_fmt(worst['duration_seconds'], 1)} s, "
        f"entry_ts={worst['entry_ts']})"
    )
    lines.append("")
    lines.append(f"## E-17-Klaerung: `{_fmt(payload['e17_resolved'])}`")
    lines.append("")
    lines.append(payload["e17_reasoning"])
    e17d = payload["e17_details"]
    if "trades_ratio" in e17d:
        lines.append("")
        lines.append(
            f"- n_trades-Ratio (aktuell/Baseline): {_fmt(e17d['trades_ratio'])}"
        )
        lines.append(
            f"- |total_return|-Ratio: {_fmt(e17d['return_ratio_abs'])}"
        )
        lines.append(
            f"- total_return-Gap: {_fmt(e17d['total_return_gap'])} USD"
        )
        top = e17d.get("top_gap_symbol") or {}
        if top.get("symbol"):
            lines.append(
                f"- Groesster Symbol-Anteil am Gap: {top['symbol']} "
                f"({_fmt(top['share_of_abs_gap'] * 100, 0)} %)"
            )
    lines.append("")
    if m["warnings"]:
        lines.append("## Warnungen")
        lines.append("")
        for w in m["warnings"]:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("---")
    lines.append(
        "*Erzeugt von `scripts/evaluate_e15.py` (WP-1, rein lesend auf den "
        "Replay-Artefakten). Endgueltiges Gate-Urteil: gate-auditor gegen "
        f"{HYPOTHESIS_ID}.*"
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``e15_evaluation.json`` and ``e15_evaluation.md`` to ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / JSON_FILENAME
    md_path = out_dir / MD_FILENAME
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
