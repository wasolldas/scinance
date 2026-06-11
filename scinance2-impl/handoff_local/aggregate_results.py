#!/usr/bin/env python3
"""Aggregate one handoff run directory into ``SUMMARY_<date>.md`` (WP-5 / T3).

Reads ``steps.tsv`` (written by run_short/run_overnight: one tab-separated
line per step: name, status, rc, duration_s, detail) plus the known pilot
artefacts under the run directory:

* ``c42_*/c42_results.json``       (H-02, one per symbol)
* ``c31_*/c31_cfar_results.json``  (H-03, one per symbol)
* ``e15/e15_evaluation.json``      (H-01, if the iter-5 results were present)
* ``recording_check.json``         (C-36 recorder verification)

and writes a machine- AND human-readable ``SUMMARY_<yyyy-mm-dd>.md`` into the
results root — the gate-auditor's morning input (judged against
``scinance2-impl/state/hypothesis_registry.md`` H-01/H-02/H-03).

Never raises out of main(); aggregation must not kill the night run.
Exit code is always 0 unless the run dir itself is missing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _steps(run_dir: Path) -> list[dict]:
    out = []
    tsv = run_dir / "steps.tsv"
    if not tsv.is_file():
        return out
    for line in tsv.read_text(encoding="utf-8").splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 5:
            out.append({"name": parts[0], "status": parts[1], "rc": parts[2],
                        "dur": parts[3], "detail": parts[4]})
    return out


def _fmt(x, nd=4):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "n/a"


def build_summary(run_dir: Path, label: str, date: str) -> str:
    L: list[str] = []
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    L.append(f"# SUMMARY {date} — handoff_local {label}-Lauf")
    L.append("")
    L.append(f"- Erzeugt: {now} UTC")
    L.append(f"- Run-Verzeichnis: `{run_dir}`")
    L.append("- Morgen-Auswertung: **gate-auditor** urteilt gegen "
             "`scinance2-impl/state/hypothesis_registry.md` (H-01/H-02/H-03). "
             "Diese Datei genuegt fuer das Urteil; Roh-JSONs liegen im Run-Verzeichnis.")
    L.append("")

    # ── Block status table ────────────────────────────────────────────
    L.append("## Block-Status")
    L.append("")
    L.append("| Block | Status | RC | Dauer [s] | Detail |")
    L.append("|---|---|---|---|---|")
    steps = _steps(run_dir)
    if steps:
        for s in steps:
            L.append(f"| {s['name']} | {s['status']} | {s['rc']} | {s['dur']} | {s['detail']} |")
    else:
        L.append("| (keine steps.tsv gefunden) | ERROR | - | - | Runner-Protokoll fehlt |")
    L.append("")

    # ── H-02 · C-42 ───────────────────────────────────────────────────
    c42_files = sorted(run_dir.glob("c42_*/c42_results.json"))
    L.append("## H-02 · C-42 Voll-WF (Gate: OOS-R² ≥ 0.15 UND QLIKE < HAR-RV in ALLEN Fenstern)")
    L.append("")
    if c42_files:
        L.append("| Symbol | Modell | Folds | min OOS-R² | R² ≥ 0.15 alle Fenster | QLIKE<HAR alle Fenster | Pre-Check |")
        L.append("|---|---|---|---|---|---|---|")
        for f in c42_files:
            d = _load(f)
            if d is None:
                L.append(f"| {f.parent.name} | ERROR | - | - | - | - | JSON unlesbar |")
                continue
            folds = d.get("folds") or []
            r2s = [x.get("model_r2") for x in folds if x.get("model_r2") is not None]
            min_r2 = _fmt(min(r2s)) if r2s else "n/a"
            L.append(
                f"| {d.get('symbol', f.parent.name)} | {d.get('model', '?')} "
                f"| {d.get('n_folds', len(folds))} | {min_r2} "
                f"| {d.get('all_folds_r2_pass')} | {d.get('all_folds_qlike_beats_har')} "
                f"| {d.get('precheck_verdict', '?')} |"
            )
    else:
        L.append("Keine `c42_results.json` im Lauf (Block FAIL/SKIP — siehe Block-Status).")
    L.append("")

    # ── H-03 · C-31 ───────────────────────────────────────────────────
    c31_files = sorted(run_dir.glob("c31_*/c31_cfar_results.json"))
    L.append("## H-03 · C-31 CFAR (Gate: Surrogate p ≤ 0.05 UND Lead > 50 ms UND Edge > 11 bps, je Fenster; EIN Fenster verfehlt → DROP)")
    L.append("")
    if c31_files:
        L.append("| Symbol | Fenster | Fenster bestanden | alle Fenster | Surrogates | Seed |")
        L.append("|---|---|---|---|---|---|")
        for f in c31_files:
            d = _load(f)
            if d is None:
                L.append(f"| {f.parent.name} | - | - | ERROR | - | - |")
                continue
            per_win = d.get("per_window_pass") or []
            L.append(
                f"| {d.get('symbol') or f.parent.name.replace('c31_', '')} "
                f"| {d.get('n_windows', len(per_win))} "
                f"| {sum(1 for x in per_win if x)}/{len(per_win)} "
                f"| {d.get('all_windows_pass')} | {d.get('n_surrogates', '?')} "
                f"| {d.get('seed', '?')} |"
            )
    else:
        L.append("Keine `c31_cfar_results.json` im Lauf (Block FAIL/SKIP — siehe Block-Status).")
    L.append("")

    # ── H-01 · E-15 ───────────────────────────────────────────────────
    L.append("## H-01 · E-15 (iter-5 vs. iter-4, Gate: Netto ≥ -5 bps UND E-17 geklaert)")
    L.append("")
    e15 = None
    for cand in [run_dir / "e15" / "e15_evaluation.json", *run_dir.glob("**/e15_evaluation.json")]:
        if cand.is_file():
            e15 = _load(cand)
            break
    if e15:
        agg = (e15.get("metrics") or {}).get("aggregate") or {}
        L.append(f"- Gate-Urteil (maschinell): **{e15.get('gate_verdict', '?')}**")
        L.append(f"- Netto-Edge: {_fmt(agg.get('mean_pnl_bps_net'), 2)} bps "
                 f"(raw {_fmt(agg.get('mean_raw_edge_bps'), 2)} bps), "
                 f"n_trades={agg.get('n_trades', '?')}")
        L.append(f"- n>120s={agg.get('n_over_120s', '?')}, "
                 f"n<-30bps={agg.get('n_below_minus_30bps', '?')}, "
                 f"time_stop_exceeded={agg.get('time_stop_exceeded_count', '?')}")
        L.append(f"- E-17 geklaert: {e15.get('e17_resolved', '?')} — {e15.get('e17_reasoning', '')}")
    else:
        L.append("Keine `e15_evaluation.json` im Lauf — iter-5-Replay-Ergebnisse fehlten "
                 "oder die Auswertung lief im run_short. Falls noch nicht geschehen: "
                 "`scripts/replay_all.py` separat starten (12h-Replays, bewusst NICHT "
                 "automatisch durch die Runner).")
    L.append("")

    # ── Recording ─────────────────────────────────────────────────────
    L.append("## C-36 Recording (Dauertest / Smoke)")
    L.append("")
    rec = _load(run_dir / "recording_check.json") if (run_dir / "recording_check.json").is_file() else None
    if rec:
        L.append(f"- Gesamt: **{'PASS' if rec.get('pass') else 'FAIL'}** "
                 f"(erwartete schema_version {rec.get('expected_schema_version')})")
        L.append("")
        L.append("| Stream | Pflicht | Segmente | Rows | schema_version | Status |")
        L.append("|---|---|---|---|---|---|")
        for s in rec.get("streams", []):
            L.append(f"| {s.get('stream')} | {s.get('required')} | {s.get('n_files')} "
                     f"| {s.get('n_rows')} | {','.join(s.get('schema_versions') or []) or '-'} "
                     f"| {s.get('status')} |")
        cap = rec.get("cap")
        if cap:
            L.append("")
            L.append(f"- Storage-Deckel: used {cap.get('used_gb')} GB / cap {cap.get('cap_gb')} GB "
                     f"→ {'OK' if cap.get('ok') else 'FAIL (Deckel verletzt!)'}")
    else:
        L.append("Keine `recording_check.json` im Lauf (Recorder-Block FAIL/SKIP — siehe Block-Status).")
    L.append("")

    # ── Raw artefacts ─────────────────────────────────────────────────
    L.append("## Roh-Artefakte (fuer Detail-Pruefung)")
    L.append("")
    for f in sorted(run_dir.rglob("*.json")):
        L.append(f"- `{f.relative_to(run_dir)}`")
    L.append("")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Aggregate a handoff run dir into SUMMARY_<date>.md")
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="Default: parent of --run-dir (= handoff_local/results/)")
    ap.add_argument("--label", default="overnight")
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    args = ap.parse_args(argv)

    if not args.run_dir.is_dir():
        print(f"AGGREGATE FAIL: run dir missing: {args.run_dir}", file=sys.stderr)
        return 1
    out_dir = args.out_dir or args.run_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"SUMMARY_{args.date}.md"
    if out_path.exists():  # second run same day -> keep both, never overwrite
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%H%M%S")
        out_path = out_dir / f"SUMMARY_{args.date}_{stamp}.md"

    try:
        out_path.write_text(build_summary(args.run_dir, args.label, args.date),
                            encoding="utf-8")
    except Exception as exc:  # aggregation must never kill the run
        print(f"AGGREGATE ERROR: {exc}", file=sys.stderr)
        return 0
    print(f"SUMMARY geschrieben: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
