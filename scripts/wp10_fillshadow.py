#!/usr/bin/env python3
"""WP-10(B) -- Maker-Fill-Schattenmessung CLI (KAPITALFREI).

Three steps, always in this order (PRD 3.3.8: the positive control gates
every real run):

    python scripts/wp10_fillshadow.py --positive-control
    python scripts/wp10_fillshadow.py --probe --base data/harvest \\
        --symbols BTCUSDT,ETHUSDT --start 2026-06-22 --end 2026-06-23
    python scripts/wp10_fillshadow.py --run --base data/harvest \\
        --out data/l2tilt --symbols BTCUSDT,ETHUSDT \\
        --dates 2026-06-22..2026-06-23 --report-dir scinance3-impl/state/wp10b_<date>

``--run`` ALWAYS executes the positive control first, internally, and
ABORTS (rc=1) before touching any real data if it fails -- the shell
wrapper's separate step is defense in depth, not the only gate.

Exit codes: 0 = OK · 1 = error / positive control failed.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.wp10_fillshadow import queue_model as qm  # noqa: E402
from bybit_edge.research.wp10_fillshadow import replay as rp  # noqa: E402
from bybit_edge.research.wp10_fillshadow import report as rpt  # noqa: E402
from bybit_edge.research.wp10_fillshadow.positive_control import (  # noqa: E402
    run_positive_control,
)


def _parse_dates(spec: str) -> tuple[str, str]:
    if ".." not in spec:
        raise SystemExit(f"[wp10b] --dates must be START..END, got {spec!r}")
    a, b = spec.split("..", 1)
    return a.strip(), b.strip()


def cmd_positive_control(_: argparse.Namespace) -> int:
    print("[wp10b] Positivkontrolle (PRD 3.3.8) ...", file=sys.stderr)
    result = run_positive_control()
    for c in result["checks"]:
        status = "OK" if c["passed"] else "FEHLGESCHLAGEN"
        print(f"[wp10b]   {c['name']}: {status}", file=sys.stderr)
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        print("[wp10b] FATAL: Positivkontrolle fehlgeschlagen -- Fuellmaschinerie "
              "defekt, Lauf abgebrochen.", file=sys.stderr)
        return 1
    print("[wp10b] Positivkontrolle bestanden.", file=sys.stderr)
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    out = {}
    ok = True
    for symbol in symbols:
        p = rp.probe(args.base, symbol, args.start, args.end)
        out[symbol] = p
        eligible = p.get("days_eligible_for_placement")
        print(f"[wp10b] probe {symbol}: ob_present={p['orderbook_days_present']} "
              f"trade_present={p['trade_days_present']} "
              f"eligible_for_placement={eligible if eligible is not None else 'manifest_error: ' + p.get('manifest_error', '')}",
              file=sys.stderr)
        if p.get("orderbook_days_present", 0) == 0 or p.get("trade_days_present", 0) == 0:
            ok = False
    print(json.dumps(out, indent=2))
    return 0 if ok else 1


def cmd_run(args: argparse.Namespace) -> int:
    print("[wp10b] Schritt 0: Positivkontrolle (intern, PRD 3.3.8) ...", file=sys.stderr)
    try:
        run_positive_control_result = run_positive_control()
    except Exception as exc:  # pragma: no cover -- defensive
        print(f"[wp10b] FATAL: Positivkontrolle konnte nicht laufen: {exc}", file=sys.stderr)
        return 1
    if not run_positive_control_result["ok"]:
        print("[wp10b] FATAL: Positivkontrolle fehlgeschlagen -- Lauf abgebrochen, "
              "KEINE Daten angefasst.", file=sys.stderr)
        return 1
    print("[wp10b] Positivkontrolle bestanden -- Lauf startet.", file=sys.stderr)

    start, end = _parse_dates(args.dates)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    base, out = Path(args.base), Path(args.out)

    stress_days: set[str] | None = None
    if args.stress_canon:
        abs_path = Path(args.stress_canon) / "stress_abs.json"
        if abs_path.is_file():
            from bybit_edge.research.wp10_coherence import stress_canon as sc
            fixture = sc.read_fixture(abs_path)
            stress_days = set(fixture.get("days", []))
            print(f"[wp10b] STRESS_ABS geladen: {len(stress_days)} Tage "
                  f"({abs_path})", file=sys.stderr)
        else:
            print(f"[wp10b] WARNUNG: STRESS_ABS-Fixture nicht gefunden ({abs_path}) "
                  "-- Bericht ohne Stress/Ruhe-Trennung.", file=sys.stderr)

    ok = True
    summaries = []
    for symbol in symbols:
        t0 = time.time()
        state = {"n": 0}

        def _progress(sym: str, res: dict) -> None:
            state["n"] += 1
            if state["n"] % 10 == 0:
                print(f"[wp10b] {sym}: {state['n']} days (last {res['day']} -> "
                      f"{res['status']}, {res['n_quotes']} quotes)", file=sys.stderr, flush=True)

        try:
            summary = rp.run_window(base, out, symbol, start, end,
                                    horizon_s=args.horizon_s,
                                    adv_sel_horizon_s=args.adv_sel_horizon_s,
                                    quote_size_fraction=args.quote_size_fraction,
                                    progress=_progress)
        except rp.ReplayError as exc:
            print(f"[wp10b] FATAL {symbol}: {exc}", file=sys.stderr)
            ok = False
            continue
        summary["seconds"] = round(time.time() - t0, 1)
        summaries.append(summary)
        print(f"[wp10b] {symbol}: ok={summary['ok']} discarded={summary['discarded']} "
              f"no_raw={summary['no_raw']} not_manifest_done={summary['not_manifest_done']} "
              f"quotes={summary['n_quotes_total']} fifo_filled={summary['n_fifo_filled_total']} "
              f"prorata_filled={summary['n_prorata_filled_total']} in {summary['seconds']}s",
              file=sys.stderr)

    rows = rpt.load_quote_rows(out, "bybit", symbols, start, end, stress_days=stress_days)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        report = rpt.build_report(rows=rows, out_dir=report_dir, seed=args.seed,
                                  n_bootstrap=args.n_bootstrap)
    except rpt.ReportError as exc:
        print(f"[wp10b] FATAL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"windows": summaries, "report": {
        "summary_path": report["summary_path"], "markdown_path": report["markdown_path"]}},
        indent=2))
    print(f"[wp10b] Bericht: {report['markdown_path']}", file=sys.stderr)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="WP-10(B) Maker-Fill-Schattenmessung (KAPITALFREI).")
    p.add_argument("--positive-control", action="store_true")
    p.add_argument("--probe", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--base", default="data/harvest")
    p.add_argument("--out", default="data/l2tilt",
                   help="Store root (fillshadow_1min/ lives beside the frozen "
                        "tilt_1min/spread_1min; those files are never touched).")
    p.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    p.add_argument("--start", default="")
    p.add_argument("--end", default="")
    p.add_argument("--dates", default="", help="START..END, for --run")
    p.add_argument("--horizon-s", type=float, default=qm.DEFAULT_HORIZON_S, dest="horizon_s")
    p.add_argument("--adv-sel-horizon-s", type=float, default=qm.DEFAULT_ADV_SEL_HORIZON_S,
                   dest="adv_sel_horizon_s")
    p.add_argument("--quote-size-fraction", type=float, default=rp.DEFAULT_QUOTE_SIZE_FRACTION,
                   dest="quote_size_fraction")
    p.add_argument("--stress-canon", default="scinance3-impl/state/wp10_stress_canon",
                   help="Dir holding stress_abs.json (WP-10(A) Teil A output). "
                        "Missing -> report without stress/quiet split.")
    p.add_argument("--report-dir", default="scinance3-impl/state/wp10b_run")
    p.add_argument("--seed", type=int, default=53)
    p.add_argument("--n-bootstrap", type=int, default=1000, dest="n_bootstrap")
    args = p.parse_args(argv)

    if args.positive_control:
        return cmd_positive_control(args)
    if args.probe:
        return cmd_probe(args)
    if args.run:
        return cmd_run(args)
    p.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
