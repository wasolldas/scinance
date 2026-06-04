"""
Multi-Symbol Replay-Backtest-Driver — spielt persistierte Ticks ALLER Symbole
durch die echten Strategien und aggregiert pro Strategie ueber alle Symbole.

Hintergrund:
    ``scripts/replay_backtest.py`` ist Single-Symbol (Default BTCUSDT). Der
    User sammelt aber live oft 5 oder mehr Symbole parallel (MultiSymbolRunner)
    — und gerade die Microstructure-Edges (S1 Liquidations-Kaskade, S3
    Pre-Settlement) sind auf kleineren Coins (SOL, DOGE, XRP) deutlich
    aktiver / ehrlicher testbar als auf BTC. Dieser Treiber:

    1. ermittelt die persistierten Symbole automatisch aus DuckDB (oder
       akzeptiert eine explizite Liste),
    2. fuehrt pro Symbol einen Replay (oder Walk-Forward) aus,
    3. aggregiert die Per-Strategie-Metriken ueber alle Symbole
       (Trade-gewichteter Sharpe, gewichtete Win-Rate, summe Trades, etc.),
    4. schreibt das Ergebnis in ``replay_all_results.json`` (Multi-Symbol
       Schema) UND in das Legacy-File ``replay_backtest_results.json``
       (nur die Aggregate, damit das Dashboard ohne Umbauten weiterfunktioniert).

Aufruf::

    python scripts/replay_all.py --auto
    python scripts/replay_all.py --symbols BTCUSDT,ETHUSDT,SOLUSDT --walkforward
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import duckdb

from bybit_edge.backtester.engine import BacktestResult
from bybit_edge.config import (
    DB_PATH,
    MULTI_SYMBOL_UNIVERSE,
    WF_EMBARGO_MINUTES,
    WF_TEST_DAYS,
    WF_TRAIN_DAYS,
)
from bybit_edge.replay_backtester import ReplayBacktester


# ----------------------------------------------------------------------
# Symbol discovery
# ----------------------------------------------------------------------

def discover_symbols(db_path: Path) -> list[str]:
    """Return distinct symbols present in the ``tickers`` table.

    Opens DuckDB read-only (concurrent-safe with a running LiveRunner). On
    any failure / empty result returns an empty list — the caller decides
    whether to fall back to :data:`MULTI_SYMBOL_UNIVERSE`.
    """
    if str(db_path) != ":memory:" and not Path(db_path).exists():
        return []
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
    except Exception as exc:  # noqa: BLE001
        print(
            f"\nKonnte DuckDB nicht read-only oeffnen ({type(exc).__name__}: {exc}).",
            file=sys.stderr,
        )
        return []
    try:
        rows = conn.execute(
            "SELECT DISTINCT symbol FROM tickers ORDER BY symbol"
        ).fetchall()
    except Exception:
        rows = []
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
    return [str(r[0]) for r in rows if r and r[0]]


def resolve_symbols(
    explicit: Optional[str], auto: bool, db_path: Path
) -> tuple[list[str], str]:
    """Pick the symbol list per the CLI flags.

    Priority:
    1. ``--symbols`` (comma-separated, always wins when provided).
    2. ``--auto`` (or default): SELECT DISTINCT from tickers; fallback to
       MULTI_SYMBOL_UNIVERSE when empty.

    Returns ``(symbols, source_label)`` where ``source_label`` describes
    where the list came from (purely for the CLI banner).
    """
    if explicit:
        syms = [s.strip().upper() for s in explicit.split(",") if s.strip()]
        # de-dup but preserve order
        seen: set[str] = set()
        out: list[str] = []
        for s in syms:
            if s not in seen:
                seen.add(s)
                out.append(s)
        return out, "explicit"

    if auto:
        discovered = discover_symbols(db_path)
        if discovered:
            return discovered, "auto (DuckDB tickers)"
        return list(MULTI_SYMBOL_UNIVERSE), "fallback (MULTI_SYMBOL_UNIVERSE)"

    # Neither flag set → behave like --auto (sensible default for "all").
    discovered = discover_symbols(db_path)
    if discovered:
        return discovered, "auto (DuckDB tickers)"
    return list(MULTI_SYMBOL_UNIVERSE), "fallback (MULTI_SYMBOL_UNIVERSE)"


# ----------------------------------------------------------------------
# Per-symbol runner
# ----------------------------------------------------------------------

def classify_status(n_trades: int) -> str:
    """Tri-state status used in the JSON / dashboard.

    * ``n_trades == 0``      → ``"no-trades"``
    * ``1 <= n_trades < 5``  → ``"data-limited"``
    * ``n_trades >= 5``      → ``"OK"``
    """
    if n_trades <= 0:
        return "no-trades"
    if n_trades < 5:
        return "data-limited"
    return "OK"


def run_symbol(
    symbol: str,
    db_path: Path,
    interval: float,
    walkforward: bool,
    train_days: int,
    test_days: int,
    embargo_minutes: int,
    diagnose: bool = False,
) -> Optional[tuple[dict[str, BacktestResult], int, int, dict[str, Any]]]:
    """Run the replay for a single symbol.

    Returns ``(results, n_events, n_folds, diagnostics)`` on success or
    ``None`` when the symbol has no events / cannot be replayed. ``n_folds``
    is 0 in single-pass mode. ``diagnostics`` is the per-strategy wait-reason /
    gate-counter dict (empty when ``diagnose`` is False).
    """
    # Only pass collect_diagnostics when actually diagnosing, so the default
    # path keeps the exact pre-diagnostics constructor signature (relevant for
    # fakes/stubs that monkey-patch ReplayBacktester without the new kwarg).
    if diagnose:
        bt = ReplayBacktester(
            symbol=symbol, db_path=db_path, collect_diagnostics=True
        )
    else:
        bt = ReplayBacktester(symbol=symbol, db_path=db_path)
    try:
        n_events = bt.load_events()
        if n_events == 0:
            return None
        if walkforward:
            results = bt.run_walkforward(
                pipeline_interval_seconds=interval,
                train_days=train_days,
                test_days=test_days,
                embargo_minutes=embargo_minutes,
            )
            n_folds = int(bt.last_walkforward_folds)
            # get_diagnostics() is only invoked when diagnosing so fakes/stubs
            # without that method keep working on the default path.
            diagnostics = bt.get_diagnostics() if diagnose else {}
            if n_folds == 0:
                # Not enough data for a single fold — degrade gracefully:
                # the per-strategy results are all-empty trade lists. Surface
                # that to the caller so it can flag this symbol as skipped.
                return results, n_events, 0, diagnostics
            return results, n_events, n_folds, diagnostics
        results = bt.run(pipeline_interval_seconds=interval)
        diagnostics = bt.get_diagnostics() if diagnose else {}
        return results, n_events, 0, diagnostics
    finally:
        bt.close()


# ----------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------

def _result_row(res: BacktestResult, data_limited: bool) -> dict[str, Any]:
    """One per-symbol-per-strategy row in the JSON payload."""
    n = int(res.n_trades)
    return {
        "sharpe": round(float(res.sharpe), 6),
        "win_rate": round(float(res.win_rate), 6),
        "max_drawdown": round(float(res.max_drawdown), 6),
        "total_return": round(float(res.total_return), 6),
        "n_trades": n,
        "data_limited": bool(data_limited),
        "status": classify_status(n),
    }


def aggregate_per_strategy(
    per_symbol: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    """Compute per-strategy aggregate metrics across all symbols.

    For each strategy id present in any symbol's result dict:

    * ``total_trades``       — sum of n_trades over symbols
    * ``weighted_sharpe``    — sum(sharpe * n) / sum(n), n>0 only
    * ``mean_win_rate``      — sum(win_rate * n) / sum(n), n>0 only
    * ``worst_max_dd``       — max(max_drawdown) over symbols (worst case)
    * ``total_return``       — sum(total_return) (informational, not USD-
                                comparable across symbols)
    * ``best_symbol``        — argmax(sharpe) over symbols with n>=5 trades
                                (falls back to argmax over n>0 when no
                                symbol has >=5 trades); ``None`` if every
                                symbol has 0 trades.
    * ``data_limited_symbols`` — symbols where this strategy had < 5 trades
                                  (or was marked data_limited).
    """
    # Collect the strategy id universe from all symbols
    sids: set[str] = set()
    for sym_res in per_symbol.values():
        sids.update(sym_res.keys())

    out: dict[str, dict[str, Any]] = {}
    for sid in sorted(sids):
        total_trades = 0
        weighted_sharpe_num = 0.0
        weighted_winrate_num = 0.0
        worst_max_dd = 0.0
        total_return = 0.0
        best_symbol: Optional[str] = None
        best_sharpe = float("-inf")
        best_sharpe_fallback: float = float("-inf")
        best_symbol_fallback: Optional[str] = None
        data_limited_syms: list[str] = []

        for sym, sym_res in per_symbol.items():
            row = sym_res.get(sid)
            if row is None:
                continue
            n = int(row.get("n_trades", 0) or 0)
            sharpe = float(row.get("sharpe", 0.0) or 0.0)
            wr = float(row.get("win_rate", 0.0) or 0.0)
            mdd = float(row.get("max_drawdown", 0.0) or 0.0)
            tr = float(row.get("total_return", 0.0) or 0.0)
            dl_flag = bool(row.get("data_limited", False))

            total_trades += n
            total_return += tr
            if mdd > worst_max_dd:
                worst_max_dd = mdd

            if n > 0:
                weighted_sharpe_num += sharpe * n
                weighted_winrate_num += wr * n
                # Track best_symbol with n>=5 first; fallback to n>0 otherwise.
                if n >= 5 and sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_symbol = sym
                if sharpe > best_sharpe_fallback:
                    best_sharpe_fallback = sharpe
                    best_symbol_fallback = sym

            if dl_flag or n < 5:
                data_limited_syms.append(sym)

        weighted_sharpe = (
            weighted_sharpe_num / total_trades if total_trades > 0 else 0.0
        )
        mean_win_rate = (
            weighted_winrate_num / total_trades if total_trades > 0 else 0.0
        )

        out[sid] = {
            "total_trades": int(total_trades),
            "weighted_sharpe": round(float(weighted_sharpe), 6),
            "mean_win_rate": round(float(mean_win_rate), 6),
            "worst_max_dd": round(float(worst_max_dd), 6),
            "total_return": round(float(total_return), 6),
            "best_symbol": (
                best_symbol if best_symbol is not None else best_symbol_fallback
            ),
            "data_limited_symbols": sorted(set(data_limited_syms)),
        }
    return out


def build_payload(
    *,
    mode: str,
    symbols: list[str],
    per_symbol: dict[str, dict[str, dict[str, Any]]],
    per_strategy_aggregate: dict[str, dict[str, Any]],
    skipped: list[str],
    walkforward_meta: Optional[dict[str, Any]] = None,
    interval_seconds: float = 1.0,
) -> dict[str, Any]:
    """Assemble the JSON payload written to ``replay_all_results.json``."""
    payload: dict[str, Any] = {
        "mode": mode,
        "symbols": list(symbols),
        "skipped_symbols": list(skipped),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interval_seconds": float(interval_seconds),
        "per_strategy_aggregate": per_strategy_aggregate,
        "per_symbol": per_symbol,
    }
    if walkforward_meta is not None:
        payload["walkforward"] = walkforward_meta
    return payload


def build_legacy_payload(
    *,
    mode: str,
    symbols: list[str],
    per_strategy_aggregate: dict[str, dict[str, Any]],
    interval_seconds: float,
    walkforward_meta: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the legacy ``replay_backtest_results.json`` shape from the aggregate.

    The legacy shape (consumed by :func:`dashboard.data.load_replay_results`) is::

        {"results": [{"strategy": "...", "sharpe": ..., ...}, ...],
         "symbol": "...", "n_events": ..., "mode": "..."}

    For Multi-Symbol we expose the aggregate-row per strategy here so the
    legacy dashboard path keeps working unchanged.
    """
    results: list[dict[str, Any]] = []
    for sid in sorted(per_strategy_aggregate.keys()):
        agg = per_strategy_aggregate[sid]
        n_total = int(agg.get("total_trades", 0))
        results.append({
            "strategy": sid,
            "sharpe": round(float(agg.get("weighted_sharpe", 0.0)), 3),
            "win_rate": round(float(agg.get("mean_win_rate", 0.0)), 3),
            "max_dd": round(float(agg.get("worst_max_dd", 0.0)), 4),
            "total_return": round(float(agg.get("total_return", 0.0)), 4),
            "n_trades": n_total,
            "data_limited": bool(agg.get("data_limited_symbols")) and n_total == 0,
        })
    results.sort(key=lambda r: r["sharpe"], reverse=True)

    payload: dict[str, Any] = {
        "symbol": ",".join(symbols),
        "interval_seconds": float(interval_seconds),
        "n_events": 0,  # multi-symbol — not meaningful as a single number
        "mode": mode,
        "results": results,
        "notes": {
            "multi_symbol": True,
            "aggregated_symbols": list(symbols),
            "reason": (
                "Multi-Symbol-Aggregat: Sharpe ist trade-gewichteter Mittelwert "
                "ueber alle Symbole, MaxDD ist Worst-Case ueber Symbole."
            ),
        },
    }
    if walkforward_meta is not None:
        payload["walkforward"] = walkforward_meta
    return payload


# ----------------------------------------------------------------------
# CLI rendering
# ----------------------------------------------------------------------

def _print_aggregate_table(aggregate: dict[str, dict[str, Any]]) -> None:
    rows = sorted(
        aggregate.items(),
        key=lambda kv: kv[1].get("weighted_sharpe", 0.0),
        reverse=True,
    )
    print(
        f"\n{'Strategie':<12}{'WeightedSharpe':>16}{'MeanWinRate':>13}"
        f"{'TotTrades':>11}{'WorstMaxDD':>12}{'TotalRet':>11}{'BestSym':>12}"
    )
    print("-" * 88)
    for sid, agg in rows:
        best = agg.get("best_symbol") or "-"
        print(
            f"{sid:<12}{agg['weighted_sharpe']:>16.3f}"
            f"{agg['mean_win_rate']:>13.3f}{agg['total_trades']:>11}"
            f"{agg['worst_max_dd']:>12.4f}{agg['total_return']:>11.4f}"
            f"{str(best):>12}"
        )


def _print_per_symbol_section(
    per_symbol: dict[str, dict[str, dict[str, Any]]],
) -> None:
    for sym in sorted(per_symbol.keys()):
        print(f"\n  --- {sym} ---")
        print(
            f"  {'Strategie':<10}{'Sharpe':>9}{'Hit':>7}{'MaxDD':>11}"
            f"{'Trades':>8}  Status"
        )
        rows = sorted(
            per_symbol[sym].items(),
            key=lambda kv: kv[1].get("sharpe", 0.0),
            reverse=True,
        )
        for sid, m in rows:
            print(
                f"  {sid:<10}{m['sharpe']:>9.2f}{m['win_rate']:>7.2f}"
                f"{m['max_drawdown']:>11.4f}{m['n_trades']:>8}  {m['status']}"
            )


def _format_reason_counts(reason_counts: dict[str, Any], top: int = 8) -> str:
    """Render a reason->count map as ``reason=count`` pairs, most frequent first."""
    if not reason_counts:
        return "(keine)"
    items = sorted(
        reason_counts.items(), key=lambda kv: kv[1], reverse=True
    )[:top]
    return ", ".join(f"{r}={n}" for r, n in items)


def print_diagnostics(
    symbol: str, diagnostics: dict[str, dict[str, Any]]
) -> None:
    """Print the per-strategy wait-reason diagnose section for one symbol.

    Mirrors the single-symbol ``scripts/replay_backtest.py`` layout so the
    operator sees the *same* picture regardless of which driver they ran.
    """
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


def _print_top3(per_symbol: dict[str, dict[str, dict[str, Any]]]) -> None:
    triples: list[tuple[str, str, float, int]] = []
    for sym, sym_res in per_symbol.items():
        for sid, m in sym_res.items():
            n = int(m.get("n_trades", 0))
            if n >= 5:
                triples.append((sym, sid, float(m.get("sharpe", 0.0)), n))
    triples.sort(key=lambda t: t[2], reverse=True)
    print("\n  Top-3 Edges (n_trades >= 5, absteigend nach Sharpe):")
    if not triples:
        print("  (keine Symbol/Strategie-Kombi mit >=5 Trades — alles data-limited)")
        return
    for sym, sid, sharpe, n in triples[:3]:
        print(f"  - {sym:<10} {sid:<5} Sharpe={sharpe:>7.3f}  Trades={n}")


# ----------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------

def run(
    *,
    symbols: list[str],
    db_path: Path,
    interval: float,
    walkforward: bool,
    train_days: int,
    test_days: int,
    embargo_minutes: int,
    diagnose: bool = False,
    diagnostics_sink: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[
    dict[str, dict[str, dict[str, Any]]],
    dict[str, dict[str, Any]],
    list[str],
    Optional[dict[str, Any]],
]:
    """Run every symbol, collect per_symbol + aggregate.

    Returns ``(per_symbol, per_strategy_aggregate, skipped_symbols, wf_meta)``.

    When ``diagnose`` is set and ``diagnostics_sink`` is provided, the
    per-symbol wait-reason / gate-counter diagnostics are written into that
    dict in-place (keyed by symbol). The 4-tuple return shape is preserved so
    existing callers / tests are unaffected.
    """
    per_symbol: dict[str, dict[str, dict[str, Any]]] = {}
    skipped: list[str] = []
    wf_folds_per_symbol: dict[str, int] = {}
    n_events_per_symbol: dict[str, int] = {}
    diagnostics_per_symbol: dict[str, dict[str, Any]] = (
        diagnostics_sink if diagnostics_sink is not None else {}
    )

    for sym in symbols:
        print(f"\n--- {sym} ---")
        try:
            outcome = run_symbol(
                symbol=sym,
                db_path=db_path,
                interval=interval,
                walkforward=walkforward,
                train_days=train_days,
                test_days=test_days,
                embargo_minutes=embargo_minutes,
                diagnose=diagnose,
            )
        except Exception as exc:  # noqa: BLE001 — keep going on per-symbol error
            print(f"  ! Replay fuer {sym} fehlgeschlagen: {exc}")
            skipped.append(sym)
            continue

        if outcome is None:
            print(f"  (skip) keine Events fuer {sym} in DuckDB")
            skipped.append(sym)
            continue

        results, n_events, n_folds, diagnostics = outcome
        n_events_per_symbol[sym] = n_events
        if diagnose and diagnostics:
            diagnostics_per_symbol[sym] = diagnostics
        if walkforward:
            wf_folds_per_symbol[sym] = n_folds
            if n_folds == 0:
                print(
                    f"  (skip) Walk-Forward fuer {sym}: zu wenig Daten fuer "
                    f"einen Fold (train_days={train_days}, test_days={test_days})"
                )
                skipped.append(sym)
                continue

        # Determine data-limited flags at *runtime* per strategy using the
        # backtester's static method (S2/S4/S5 by default). We import the
        # *real* ReplayBacktester from the module that owns the static set
        # so that tests which monkey-patch ``replay_all.ReplayBacktester``
        # with a fake class still get the canonical classification here.
        from bybit_edge.replay_backtester import (
            ReplayBacktester as _ReplayBT_Real,
        )
        sym_rows: dict[str, dict[str, Any]] = {}
        for sid, res in results.items():
            dl = _ReplayBT_Real.is_data_limited(sid)
            sym_rows[sid] = _result_row(res, data_limited=dl)
        per_symbol[sym] = sym_rows

        print(f"  Events: {n_events}")
        for sid in sorted(sym_rows.keys()):
            m = sym_rows[sid]
            print(
                f"    {sid}: sharpe={m['sharpe']:.2f} trades={m['n_trades']} "
                f"status={m['status']}"
            )

    aggregate = aggregate_per_strategy(per_symbol)

    wf_meta: Optional[dict[str, Any]] = None
    if walkforward:
        wf_meta = {
            "train_days": int(train_days),
            "test_days": int(test_days),
            "embargo_minutes": int(embargo_minutes),
            "folds_per_symbol": wf_folds_per_symbol,
        }
    return per_symbol, aggregate, skipped, wf_meta


def write_outputs(
    *,
    payload: dict[str, Any],
    legacy_payload: dict[str, Any],
    out_dir: Path,
) -> tuple[Path, Path]:
    """Write both JSON files; create the parent dir if needed.

    Returns the two paths so the CLI can print them.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    primary = out_dir / "replay_all_results.json"
    legacy = out_dir / "replay_backtest_results.json"
    primary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    legacy.write_text(json.dumps(legacy_payload, indent=2), encoding="utf-8")
    return primary, legacy


# ----------------------------------------------------------------------
# CLI entrypoint
# ----------------------------------------------------------------------

def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Multi-Symbol Replay-Backtest — aggregiert alle persistierten "
            "Symbole in einem Lauf."
        )
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--symbols",
        default=None,
        help=(
            "Explizite kommagetrennte Symbol-Liste, z.B. BTCUSDT,ETHUSDT. "
            "Uebersteuert --auto."
        ),
    )
    group.add_argument(
        "--auto",
        action="store_true",
        help=(
            "Auto-Discovery: liest distinct Symbols aus DuckDB tickers. "
            "Fallback auf MULTI_SYMBOL_UNIVERSE wenn leer."
        ),
    )
    parser.add_argument(
        "--walkforward",
        action="store_true",
        help="Walk-Forward statt Single-Pass (Train/Embargo/Test pro Fold).",
    )
    parser.add_argument("--train-days", type=int, default=WF_TRAIN_DAYS)
    parser.add_argument("--test-days", type=int, default=WF_TEST_DAYS)
    parser.add_argument("--embargo-minutes", type=int, default=WF_EMBARGO_MINUTES)
    parser.add_argument(
        "--db",
        default=None,
        help="Pfad zur DuckDB (Default: config.DB_PATH).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Pipeline-Throttle in Sekunden (wie LiveRunner).",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help=(
            "Diagnose-Modus: zaehlt pro Strategie + Symbol wie oft welcher "
            "wait_reason auftrat und (fuer S3) die Entry-Gate-Verteilung "
            "(in_window / pressure>Q90 / basis_aligned / all_gates). Zeigt "
            "schwarz auf weiss WELCHES Gate blockiert. Kein Einfluss auf Trades."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    db_path = Path(args.db) if args.db else DB_PATH

    symbols, source = resolve_symbols(args.symbols, args.auto, db_path)

    mode_label = (
        "MULTI-SYMBOL WALK-FORWARD REPLAY" if args.walkforward
        else "MULTI-SYMBOL REPLAY-BACKTEST"
    )
    print("=" * 80)
    print(f"  {mode_label}")
    print(f"  Symbol-Quelle: {source}")
    print(f"  Symbole ({len(symbols)}): {', '.join(symbols) if symbols else '-'}")
    if args.walkforward:
        print(
            f"  Fold: train={args.train_days}d / "
            f"embargo={args.embargo_minutes}min / test={args.test_days}d"
        )
    print(f"  DuckDB: {db_path}")
    print("  DuckDB read-only — parallel zum LiveRunner nutzbar.")
    print("=" * 80)

    if not symbols:
        print("\nKeine Symbole zu bewerten — Abbruch.")
        return 1

    if str(db_path) != ":memory:" and not Path(db_path).exists():
        print(
            "\nKeine DuckDB-Datei gefunden — erst Daten sammeln mit "
            "PERSIST_ENABLED=true und LiveRunner laufen lassen."
        )
        return 1

    diagnostics_per_symbol: dict[str, dict[str, Any]] = {}
    per_symbol, aggregate, skipped, wf_meta = run(
        symbols=symbols,
        db_path=db_path,
        interval=args.interval,
        walkforward=args.walkforward,
        train_days=args.train_days,
        test_days=args.test_days,
        embargo_minutes=args.embargo_minutes,
        diagnose=args.diagnose,
        diagnostics_sink=diagnostics_per_symbol,
    )

    mode = "walkforward" if args.walkforward else "single_pass"
    payload = build_payload(
        mode=mode,
        symbols=symbols,
        per_symbol=per_symbol,
        per_strategy_aggregate=aggregate,
        skipped=skipped,
        walkforward_meta=wf_meta,
        interval_seconds=args.interval,
    )
    if args.diagnose:
        payload["diagnostics"] = diagnostics_per_symbol
    legacy_payload = build_legacy_payload(
        mode=mode,
        symbols=symbols,
        per_strategy_aggregate=aggregate,
        interval_seconds=args.interval,
        walkforward_meta=wf_meta,
    )

    out_dir = (
        Path(__file__).resolve().parent.parent
        / "edge_research_framework"
        / "results"
    )
    primary_path, legacy_path = write_outputs(
        payload=payload, legacy_payload=legacy_payload, out_dir=out_dir
    )

    # CLI rendering
    if aggregate:
        print("\n" + "=" * 80)
        print("  AGGREGAT — Pro Strategie ueber alle Symbole")
        print("=" * 80)
        _print_aggregate_table(aggregate)

    if per_symbol:
        print("\n" + "=" * 80)
        print("  PER-SYMBOL DETAIL")
        print("=" * 80)
        _print_per_symbol_section(per_symbol)

        print("\n" + "=" * 80)
        _print_top3(per_symbol)

    if args.diagnose and diagnostics_per_symbol:
        print("\n" + "=" * 80)
        print("  DIAGNOSE — Pro Symbol: welches Entry-Gate blockiert?")
        print("=" * 80)
        for sym in sorted(diagnostics_per_symbol.keys()):
            print_diagnostics(sym, diagnostics_per_symbol[sym])

    if skipped:
        print(f"\n  Skipped Symbole: {', '.join(skipped)}")

    print(f"\nErgebnisse: {primary_path}")
    print(f"Legacy-Aggregat: {legacy_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
