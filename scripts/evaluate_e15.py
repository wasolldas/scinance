#!/usr/bin/env python3
"""
E-15-Auswertung (WP-1): wertet einen S3-iter-5-Replay-Lauf maschinell gegen
das vorregistrierte H-01-Gate aus (scinance2-impl/state/hypothesis_registry.md).

Liest rein lesend die Artefakte von ``scripts/replay_all.py``
(``replay_all_results.json`` + ``trades_all.csv``), berechnet die S3-Metriken
(Netto-/Raw-Edge in bps, time_stop_exceeded/hard_stop_loss-Counts,
n>120s-/n<-30bps-Tails), prueft den E-17-Divergenz-Check gegen einen optionalen
Baseline-Lauf (iter-3/iter-4) und faellt WEITER / DROP / GRAUBEREICH.

Pfad-parametrisiert gemaess DEC-02 — die Bestands-CLI (`replay_all.py`) bleibt
unangetastet; T2/T3-Runner setzen die Pfade explizit auf
``handoff_local/results/``.

Aufruf::

    python scripts/evaluate_e15.py
    python scripts/evaluate_e15.py \
        --results-path handoff_local/results/replay_all_results.json \
        --trades-path handoff_local/results/trades_all.csv \
        --baseline-results edge-reconciliation/input/iter4_raw/replay_all_results.json \
        --baseline-trades edge-reconciliation/input/iter4_raw/trades_all.csv \
        --out scinance2-impl/state

Exit-Codes: 0 = ausgewertet (unabhaengig vom Urteil), 1 = Datendefekt/fehlende
Eingabe.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from bybit_edge.research.e15_eval import (
    DataError,
    build_payload,
    check_e17,
    compute_e15_metrics,
    evaluate_h01_gate,
    load_results,
    load_trades,
    write_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RESULTS = REPO_ROOT / "edge_research_framework" / "results" / "replay_all_results.json"
DEFAULT_TRADES = REPO_ROOT / "edge_research_framework" / "results" / "trades_all.csv"
DEFAULT_OUT = REPO_ROOT / "scinance2-impl" / "state"


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E-15/H-01 gate evaluation over replay_all artifacts (read-only)."
    )
    parser.add_argument(
        "--results-path",
        type=Path,
        default=DEFAULT_RESULTS,
        help=f"Pfad zu replay_all_results.json (Default: {DEFAULT_RESULTS})",
    )
    parser.add_argument(
        "--trades-path",
        type=Path,
        default=DEFAULT_TRADES,
        help=f"Pfad zur Trades-CSV (Default: {DEFAULT_TRADES})",
    )
    parser.add_argument(
        "--baseline-results",
        type=Path,
        default=None,
        help="Optional: Baseline-replay_all_results.json (z.B. iter-4) fuer den E-17-Vergleich",
    )
    parser.add_argument(
        "--baseline-trades",
        type=Path,
        default=None,
        help="Optional: Baseline-Trades-CSV fuer die Tail-Trade-Attribution im E-17-Check",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output-Verzeichnis fuer e15_evaluation.json/.md (Default: {DEFAULT_OUT})",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        results = load_results(args.results_path)
        trades = load_trades(args.trades_path)
        metrics = compute_e15_metrics(trades, results)

        baseline_results = (
            load_results(args.baseline_results) if args.baseline_results else None
        )
        baseline_trades = (
            load_trades(args.baseline_trades) if args.baseline_trades else None
        )
        e17 = check_e17(results, trades, baseline_results, baseline_trades)
        gate = evaluate_h01_gate(metrics["aggregate"], e17["resolved"])

        payload = build_payload(
            metrics,
            gate,
            e17,
            inputs={
                "results_path": str(args.results_path),
                "trades_path": str(args.trades_path),
                "baseline_results": (
                    str(args.baseline_results) if args.baseline_results else None
                ),
                "baseline_trades": (
                    str(args.baseline_trades) if args.baseline_trades else None
                ),
            },
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"E15-EVAL DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    agg = metrics["aggregate"]
    print(
        f"E15-EVAL {gate['gate_verdict']} | H-01 | n_trades={agg['n_trades']} "
        f"net={agg['mean_pnl_bps_net']:.2f}bps raw={agg['mean_raw_edge_bps']:.2f}bps "
        f"n>120s={agg['n_over_120s']} n<-30bps={agg['n_below_minus_30bps']} "
        f"time_stop={agg['time_stop_exceeded_count']} "
        f"e17={e17['resolved']} -> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
