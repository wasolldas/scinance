"""
Replay-Backtest-Driver — spielt persistierte Ticks (DuckDB) durch die echten
Microstructure-Strategien und vergleicht sie pro Strategie.

Im Gegensatz zu ``scripts/backtest.py`` (nur OHLCV) testet dieser Treiber die
novel Edges, die Tickdaten brauchen:

    Real testbar (aus persistierten Ticks):
        * S1 Cascade        — Liquidations-Stream + Hawkes/GR-Omori/SIR
        * S3 Pre-Settlement — M22/M23/M24-Familie inkl. live Premium-Index
    Datenlimitiert (mit dem persistierten Datensatz NICHT validierbar):
        * S2 Entropie-Momentum — braucht volle L2-Tiefe (nur Top-of-Book da)
        * S4 Pattern-Ensemble  — braucht Foundation-Modelle + lange Serien
        * S5 Cross-Sectional   — braucht Multi-Symbol-Panel

Aufruf:
    python scripts/replay_backtest.py --symbol BTCUSDT --interval 1.0
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from bybit_edge.config import (
    DB_PATH,
    OMORI_REFIT_SECONDS,
    WF_EMBARGO_MINUTES,
    WF_TEST_DAYS,
    WF_TRAIN_DAYS,
)
from bybit_edge.replay_backtester import ReplayBacktester

# Sentinel returned by argparse when ``--fast-omori`` is passed *without* an
# explicit value (``nargs="?"``). We use a sentinel object (not ``None`` and not
# a float) so we can disambiguate "flag absent" (default ``None``), "flag with
# no value → use config default" (``_FAST_OMORI_DEFAULT_SENTINEL``) and "flag
# with value" (a plain ``float``). Kept module-private; the CLI translates it
# to :data:`OMORI_REFIT_SECONDS` before passing to :class:`ReplayBacktester`.
_FAST_OMORI_DEFAULT_SENTINEL: object = object()


def _resolve_fast_omori(fast_omori: Any) -> float:
    """Resolve the ``--fast-omori`` argparse value to a refit-seconds float.

    * ``None``                            → 0.0 (flag absent / default off).
    * :data:`_FAST_OMORI_DEFAULT_SENTINEL` → :data:`OMORI_REFIT_SECONDS`.
    * any other value                     → ``float(value)``.
    """
    if fast_omori is None:
        return 0.0
    if fast_omori is _FAST_OMORI_DEFAULT_SENTINEL:
        return float(OMORI_REFIT_SECONDS)
    return float(fast_omori)


def _format_reason_counts(reason_counts: dict[str, Any], top: int = 8) -> str:
    """Render a reason->count map as ``reason=count`` pairs, most frequent first."""
    if not reason_counts:
        return "(keine)"
    items = sorted(
        reason_counts.items(), key=lambda kv: kv[1], reverse=True
    )[:top]
    return ", ".join(f"{r}={n}" for r, n in items)


def print_diagnostics(symbol: str, diagnostics: dict[str, dict[str, Any]]) -> None:
    """Print the per-strategy wait-reason diagnose section for one symbol."""
    if not diagnostics:
        return
    print(f"\n=== DIAGNOSE {symbol} ===")
    s3 = diagnostics.get("S3")
    if s3 is not None:
        print(
            f"S3: {s3.get('n_ticks_total', 0)} ticks | "
            f"in_window: {s3.get('n_in_window', 0)} | "
            f"pressure>Q90: {s3.get('n_pressure_extreme', 0)} | "
            f"basis_aligned: {s3.get('n_basis_aligned', 0)} | "
            f"all_gates: {s3.get('n_all_gates_passed', 0)}"
        )
        print(
            "    wait_reasons: "
            f"{_format_reason_counts(s3.get('reason_counts', {}))}"
        )
    for sid in sorted(diagnostics.keys()):
        if sid == "S3":
            continue
        rc = diagnostics[sid].get("reason_counts", {})
        print(f"{sid}: reasons: {_format_reason_counts(rc)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bybit Edge Replay-Backtest-Driver")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument(
        "--db",
        default=None,
        help="Pfad zur DuckDB-Datei (Default: config.DB_PATH)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Pipeline-Throttle in Sekunden (wie im LiveRunner)",
    )
    parser.add_argument(
        "--walkforward",
        action="store_true",
        help=(
            "Walk-Forward-Modus: Train (Warmup, Trades verworfen) -> Embargo "
            "-> Test (Trades gezaehlt) pro Fold. Misst Out-of-Sample-Robustheit."
        ),
    )
    parser.add_argument(
        "--train-days",
        type=int,
        default=WF_TRAIN_DAYS,
        help=f"Walk-Forward Trainings-Fenster in Tagen (Default: {WF_TRAIN_DAYS})",
    )
    parser.add_argument(
        "--test-days",
        type=int,
        default=WF_TEST_DAYS,
        help=f"Walk-Forward Test-Fenster in Tagen (Default: {WF_TEST_DAYS})",
    )
    parser.add_argument(
        "--embargo-minutes",
        type=int,
        default=WF_EMBARGO_MINUTES,
        help=(
            f"Embargo zwischen Train- und Test-Slice in Minuten "
            f"(Default: {WF_EMBARGO_MINUTES})"
        ),
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help=(
            "Diagnose-Modus: zaehlt pro Strategie wie oft welcher wait_reason "
            "auftrat und (fuer S3) Verteilungs-Zaehler der Entry-Gates "
            "(in_window / pressure>Q90 / basis_aligned / all_gates). Zeigt "
            "schwarz auf weiss WELCHES Gate blockiert. Kein Einfluss auf Trades."
        ),
    )
    parser.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        default=True,
        help=(
            "Fortschritts-Logging (Default AN): alle ~250k Events bzw. ~10s "
            "eine Zeile auf den Logger mit Prozent + ETA. Kein Einfluss auf "
            "Trades."
        ),
    )
    parser.add_argument(
        "--no-progress",
        dest="progress",
        action="store_false",
        help="Fortschritts-Logging abschalten.",
    )
    parser.add_argument(
        "--invert-strategies",
        type=str,
        default="",
        help=(
            "Comma-separated list of strategy IDs to invert direction for, "
            "e.g. 'S2,S3'. Tests whether direction-sign is wrong. Default off."
        ),
    )
    parser.add_argument(
        "--fast-omori",
        dest="fast_omori",
        nargs="?",
        const=_FAST_OMORI_DEFAULT_SENTINEL,
        default=None,
        type=float,
        help=(
            "Opt-in Performance-Modus: drosselt den teuren M15 Omori-curve_fit "
            "auf alle N Sekunden Event-Zeit (Default ohne Wert: "
            f"OMORI_REFIT_SECONDS={OMORI_REFIT_SECONDS}s). Ohne das Flag ist "
            "das Verhalten bit-identisch zur Live-Pipeline. Mit dem Flag ist "
            "die Trade-Liste in Grenzfaellen (Aftershock-Decay im Refit-"
            "Fenster) nicht mehr bit-identisch, typischer Speedup ~5-10x auf "
            "cascade-lastigen Daten."
        ),
    )
    args = parser.parse_args()
    m15_refit_seconds = _resolve_fast_omori(args.fast_omori)

    # Apply direction-inversion flags BEFORE constructing the backtester so
    # the strategy instances see the flipped sign at trade-entry time.
    from bybit_edge import config as _cfg
    inverts = {
        t.strip().upper()
        for t in args.invert_strategies.split(",")
        if t.strip()
    }
    unknown = inverts - {"S2", "S3"}
    if unknown:
        raise SystemExit(
            f"--invert-strategies: unknown {sorted(unknown)}; allowed: S2,S3"
        )
    if "S2" in inverts:
        _cfg.S2_INVERT_DIRECTION = True
    if "S3" in inverts:
        _cfg.S3_INVERT_DIRECTION = True

    # Ensure the progress lines (logging.INFO on the backtester logger) are
    # actually surfaced when running interactively.
    if args.progress:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
        )

    db_path = Path(args.db) if args.db else DB_PATH

    mode_label = "WALK-FORWARD REPLAY-BACKTEST" if args.walkforward else "REPLAY-BACKTEST"
    print("=" * 75)
    print(f"  {mode_label} — {args.symbol} — interval={args.interval}s")
    if args.walkforward:
        print(
            f"  Fold: train={args.train_days}d / embargo={args.embargo_minutes}min"
            f" / test={args.test_days}d (sliding by test_days)"
        )
    print(f"  DuckDB: {db_path}")
    print(
        "  DuckDB wird READ-ONLY geoeffnet — kann parallel zum laufenden "
        "Live-System genutzt werden."
    )
    if m15_refit_seconds > 0.0:
        print(
            f"  Performance-Modus: --fast-omori (M15 Omori-Refit alle "
            f"{m15_refit_seconds:g}s, kann Ergebnisse leicht abweichen)"
        )
    if inverts:
        print(f"  [INVERT] Inverted directions: {', '.join(sorted(inverts))}")
    print("=" * 75)

    if str(db_path) != ":memory:" and not Path(db_path).exists():
        print(
            "\nKeine DuckDB-Datei gefunden. Erst Daten sammeln mit "
            "PERSIST_ENABLED=true\n(LiveRunner laufen lassen, dann erneut "
            "ausfuehren)."
        )
        return

    # Only forward ``m15_refit_seconds`` when the throttle is actually opt-in
    # ON. The default path keeps the pre-throttle constructor signature so
    # fakes/stubs that monkey-patch ReplayBacktester without the new kwarg keep
    # working.
    bt_kwargs: dict[str, Any] = {}
    if m15_refit_seconds > 0.0:
        bt_kwargs["m15_refit_seconds"] = m15_refit_seconds
    bt = ReplayBacktester(
        symbol=args.symbol,
        db_path=db_path,
        collect_diagnostics=args.diagnose,
        **bt_kwargs,
    )
    n_folds: int = 0
    try:
        n_events = bt.load_events()
        print(f"  Geladene Events: {n_events}")
        if n_events == 0:
            print(
                "\nDuckDB ist leer (keine Ticks fuer dieses Symbol). "
                "Erst Daten sammeln mit PERSIST_ENABLED=true."
            )
            return

        if args.walkforward:
            results = bt.run_walkforward(
                pipeline_interval_seconds=args.interval,
                train_days=args.train_days,
                test_days=args.test_days,
                embargo_minutes=args.embargo_minutes,
                progress=args.progress,
            )
            n_folds = bt.last_walkforward_folds
            print(f"  Folds executed: {n_folds}")
        else:
            results = bt.run(
                pipeline_interval_seconds=args.interval,
                progress=args.progress,
            )
        diagnostics = bt.get_diagnostics()
    finally:
        bt.close()

    rows: list[dict[str, Any]] = []
    for sid, res in results.items():
        rows.append({
            "strategy": sid,
            "sharpe": round(res.sharpe, 3),
            "win_rate": round(res.win_rate, 3),
            "max_dd": round(res.max_drawdown, 4),
            "total_return": round(res.total_return, 4),
            "n_trades": res.n_trades,
            "data_limited": ReplayBacktester.is_data_limited(sid),
        })

    rows.sort(key=lambda r: r["sharpe"], reverse=True)

    print(
        f"\n{'Strategie':<12}{'Sharpe':>9}{'Hit':>7}{'MaxDD':>11}"
        f"{'Return':>11}{'Trades':>8}  Hinweis"
    )
    print("-" * 75)
    for r in rows:
        note = "datenlimitiert" if r["data_limited"] else "real testbar"
        print(
            f"{r['strategy']:<12}{r['sharpe']:>9.2f}{r['win_rate']:>7.2f}"
            f"{r['max_dd']:>11.4f}{r['total_return']:>11.4f}{r['n_trades']:>8}"
            f"  {note}"
        )

    if args.diagnose:
        print_diagnostics(args.symbol, diagnostics)

    out_name = (
        "walkforward_results.json" if args.walkforward else "replay_backtest_results.json"
    )
    out = (
        Path(__file__).resolve().parent.parent
        / "edge_research_framework"
        / "results"
        / out_name
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "symbol": args.symbol,
        "interval_seconds": args.interval,
        "n_events": n_events,
        "results": rows,
        "notes": {
            "real_testable": ["S1", "S3"],
            "data_limited": ["S2", "S4", "S5"],
            "reason": (
                "Nur Top-of-Book (bid1/ask1) persistiert; keine volle L2-Tiefe "
                "(M6 Shannon-Entropie nicht testbar -> S2). S4 braucht "
                "Foundation-Modelle + lange Serien, S5 ein Multi-Symbol-Panel."
            ),
        },
    }
    if args.walkforward:
        payload["mode"] = "walkforward"
        payload["walkforward"] = {
            "train_days": args.train_days,
            "test_days": args.test_days,
            "embargo_minutes": args.embargo_minutes,
            "n_folds_executed": n_folds,
        }
    else:
        payload["mode"] = "single_pass"
    if args.diagnose:
        payload["diagnostics"] = diagnostics
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nErgebnisse gespeichert: {out}")
    print(
        "\nHinweis: S2/S4/S5 sind datenlimitiert (Top-of-Book / Single-Symbol). "
        "Real validierbar sind S1 (Cascade) und S3 (Pre-Settlement)."
    )


if __name__ == "__main__":
    main()
