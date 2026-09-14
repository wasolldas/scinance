"""WP-12 -- ``wp12_report.md``/``wp12_summary.json`` assembly (task brief
item 4): register size, symbols extracted, kline availability table, bias
measurement + CI + mode label, DEC-53 artifacts (register parquet sha256,
per-week IC series with/without CSV, bootstrap seed). Descriptive labels
throughout -- no PASS/FAIL, no threshold comparison (PRD 4.1 B3 threshold
is not yet registered, see ``survivorship_fixture.THRESHOLD_NOT_REGISTERED_NOTE``).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["assemble_summary", "write_report"]


def _fmt(x: Any, nd: int = 4) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float):
        if x != x:  # NaN
            return "NaN"
        return f"{x:.{nd}f}"
    return str(x)


def assemble_summary(
    *, mode: str, register: dict[str, Any] | None, kline_probe: dict[str, Any] | None,
    fixture: dict[str, Any] | None, artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the ``wp12_summary.json`` payload out of whichever stages
    actually ran (``--mode probe`` never has ``fixture``; ``--mode
    fixture`` carries all three when the register/probe steps were also
    run, or only ``fixture`` + reused artifacts when they were skipped)."""
    summary: dict[str, Any] = {"mode": mode, "artifacts": artifacts}
    if register is not None:
        summary["register"] = {
            "n_announcements": register.get("n_rows"),
            "n_symbols_extracted": register.get("n_symbols_extracted"),
            "n_symbols_linear": register.get("n_symbols_linear"),
            "param_used": register.get("param_used"),
            "sha256": register.get("sha256"),
        }
    if kline_probe is not None:
        summary["kline_probe"] = {
            "window_days": kline_probe.get("window_days"),
            "n_symbols_probed": kline_probe.get("n_symbols_probed"),
            "n_available": kline_probe.get("n_available"),
            "n_unavailable": kline_probe.get("n_unavailable"),
            "n_skipped_no_reference_date": kline_probe.get("n_skipped_no_reference_date"),
        }
    if fixture is not None:
        summary["fixture"] = {
            "mode_label": fixture.get("mode_label"),
            "rho_with": fixture.get("rho_with"),
            "rho_without": fixture.get("rho_without"),
            "bias_point": fixture.get("bias_point"),
            "bootstrap": fixture.get("bootstrap"),
            "n_symbols_with": fixture.get("n_symbols_with"),
            "n_symbols_without": fixture.get("n_symbols_without"),
            "n_symbols_delisted_added": fixture.get("n_symbols_delisted_added"),
            "threshold_note": fixture.get("threshold_note"),
        }
    return summary


def _to_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = ["# WP-12 -- Delisting-Register + Survivorship-Fixture",
                          f"Modus: `{summary.get('mode')}`", ""]

    if "register" in summary:
        r = summary["register"]
        lines += ["## 1. Delisting-Register (Bybit public announcements)",
                    f"- Announcements im Register: {_fmt(r.get('n_announcements'), 0)}",
                    f"- Distinkte extrahierte Symbole: {_fmt(r.get('n_symbols_extracted'), 0)}",
                    f"- davon linear (USDT-Suffix): {_fmt(r.get('n_symbols_linear'), 0)}",
                    f"- Anfrage-Parameter: {r.get('param_used')}",
                    f"- register.parquet sha256: {r.get('sha256')}", ""]

    if "kline_probe" in summary:
        k = summary["kline_probe"]
        lines += ["## 2. Kline-Verfuegbarkeits-Probe (delistete lineare Symbole)",
                    f"- Fenster: {_fmt(k.get('window_days'), 0)} Tage vor Delisting/Announcement",
                    "| Kennzahl | Wert |", "|---|---|",
                    f"| Symbole probiert | {_fmt(k.get('n_symbols_probed'), 0)} |",
                    f"| Historie verfuegbar | {_fmt(k.get('n_available'), 0)} |",
                    f"| Historie NICHT verfuegbar | {_fmt(k.get('n_unavailable'), 0)} |",
                    f"| uebersprungen (kein Referenzdatum) | {_fmt(k.get('n_skipped_no_reference_date'), 0)} |",
                    "",
                    "Feasibility-Aussage: verfuegbare Historie delisteter Symbole "
                    "koennte (spaetere Aufgabe, hier NICHT gebaut) als separater "
                    "`source=bybit_delisted`-Baum an `panel_1d` angefuegt werden.", ""]

    if "fixture" in summary:
        f = summary["fixture"]
        b = f.get("bootstrap") or {}
        lines += ["## 3. Survivorship-Fixture -- Momentum-IC-Verzerrung",
                    f"- Modus-Etikett: **{f.get('mode_label')}**",
                    f"- IC (mit delisteten Symbolen): {_fmt(f.get('rho_with'))}",
                    f"- IC (ohne delistete Symbole): {_fmt(f.get('rho_without'))}",
                    f"- **Gemessene Verzerrung (bias = IC_with - IC_without): "
                    f"{_fmt(f.get('bias_point'))}**",
                    f"- Cluster-Bootstrap-CI ({_fmt(b.get('ci'), 2)}, "
                    f"n_boot={_fmt(b.get('n_boot'), 0)}, seed={b.get('seed')}, "
                    f"n_wochen_cluster={_fmt(b.get('n_weeks'), 0)}): "
                    f"[{_fmt(b.get('ci_lo'))}; {_fmt(b.get('ci_hi'))}]",
                    f"- Symbole mit/ohne: {_fmt(f.get('n_symbols_with'), 0)} / "
                    f"{_fmt(f.get('n_symbols_without'), 0)} "
                    f"(+{_fmt(f.get('n_symbols_delisted_added'), 0)} delistet)",
                    "", f"> {f.get('threshold_note')}", ""]

    if summary.get("artifacts"):
        lines += ["## DEC-53-Artefakte"]
        for name, art in summary["artifacts"].items():
            if isinstance(art, dict) and "sha256" in art:
                lines.append(f"- {name}: `{art.get('path')}` (sha256={art['sha256']})")
            elif isinstance(art, dict):
                for sub_name, sub in art.items():
                    if isinstance(sub, dict) and "sha256" in sub:
                        lines.append(f"- {name}.{sub_name}: `{sub.get('path')}` (sha256={sub['sha256']})")
        lines.append("")

    return "\n".join(lines) + "\n"


def write_report(out_dir: Path | str, summary: dict[str, Any]) -> dict[str, str]:
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write WP-12 report under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "wp12_summary.json"
    md_path = out_dir / "wp12_report.md"
    json_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    md_path.write_text(_to_markdown(summary), encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path)}
