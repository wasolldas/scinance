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
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import duckdb

from bybit_edge.backtester.engine import BacktestResult
from bybit_edge.config import (
    DB_PATH,
    MULTI_SYMBOL_UNIVERSE,
    OMORI_REFIT_SECONDS,
    WF_EMBARGO_MINUTES,
    WF_TEST_DAYS,
    WF_TRAIN_DAYS,
)
from bybit_edge.replay_backtester import ReplayBacktester

# See ``scripts/replay_backtest.py`` for the identical sentinel/resolver pattern.
_FAST_OMORI_DEFAULT_SENTINEL: object = object()


def _resolve_fast_omori(fast_omori: Any) -> float:
    """Resolve the ``--fast-omori`` argparse value to a refit-seconds float."""
    if fast_omori is None:
        return 0.0
    if fast_omori is _FAST_OMORI_DEFAULT_SENTINEL:
        return float(OMORI_REFIT_SECONDS)
    return float(fast_omori)


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
    progress: bool = False,
    m15_refit_seconds: float = 0.0,
    s1_rho_instrument_dir: Optional[Path] = None,
) -> Optional[tuple[dict[str, BacktestResult], int, int, dict[str, Any]]]:
    """Run the replay for a single symbol.

    Returns ``(results, n_events, n_folds, diagnostics)`` on success or
    ``None`` when the symbol has no events / cannot be replayed. ``n_folds``
    is 0 in single-pass mode. ``diagnostics`` is the per-strategy wait-reason /
    gate-counter dict (empty when ``diagnose`` is False).
    """
    # Only pass collect_diagnostics / m15_refit_seconds when actually opted-in,
    # so the default path keeps the exact pre-diagnostics constructor signature
    # (relevant for fakes/stubs that monkey-patch ReplayBacktester without the
    # new kwargs).
    bt_kwargs: dict[str, Any] = {}
    if diagnose:
        bt_kwargs["collect_diagnostics"] = True
    if m15_refit_seconds > 0.0:
        bt_kwargs["m15_refit_seconds"] = m15_refit_seconds
    bt = ReplayBacktester(symbol=symbol, db_path=db_path, **bt_kwargs)
    # Only forward ``progress`` when enabled, so fakes/stubs that monkey-patch
    # ReplayBacktester with the pre-progress run()/run_walkforward() signature
    # keep working on the default (progress-off in tests) path.
    progress_kw: dict[str, Any] = {"progress": True} if progress else {}
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
                **progress_kw,
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
        results = bt.run(pipeline_interval_seconds=interval, **progress_kw)
        diagnostics = bt.get_diagnostics() if diagnose else {}
        return results, n_events, 0, diagnostics
    finally:
        # Iter-4 Push A T2: flush S1 rho-distribution before close().
        if s1_rho_instrument_dir is not None:
            s1 = bt.get_strategy("S1")
            if s1 is not None:
                s1.dump_rho_distribution(symbol, s1_rho_instrument_dir)
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
    inverted_strategies: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Assemble the JSON payload written to ``replay_all_results.json``."""
    payload: dict[str, Any] = {
        "mode": mode,
        "symbols": list(symbols),
        "skipped_symbols": list(skipped),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interval_seconds": float(interval_seconds),
        "inverted_strategies": (
            sorted(list(inverted_strategies)) if inverted_strategies else []
        ),
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
    progress: bool = False,
    m15_refit_seconds: float = 0.0,
    export_trades_dir: Optional[Path] = None,
    s1_rho_instrument_dir: Optional[Path] = None,
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

    When ``export_trades_dir`` is set, after each symbol completes its replay
    a ``trades_{symbol}_{mode}.csv`` is written into that directory, and a
    concatenated ``trades_all.csv`` is written once at the end. Default
    ``None`` -> no file writes (bit-identical).
    """
    per_symbol: dict[str, dict[str, dict[str, Any]]] = {}
    skipped: list[str] = []
    wf_folds_per_symbol: dict[str, int] = {}
    n_events_per_symbol: dict[str, int] = {}
    diagnostics_per_symbol: dict[str, dict[str, Any]] = (
        diagnostics_sink if diagnostics_sink is not None else {}
    )

    mode_tag: str = "walkforward" if walkforward else "single_pass"
    # Per-(symbol, strategy) trade lists, only populated when exporting.
    exported_csv_paths: list[Path] = []

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
                progress=progress,
                m15_refit_seconds=m15_refit_seconds,
                s1_rho_instrument_dir=s1_rho_instrument_dir,
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

        # Opt-in per-symbol trade-CSV export. Default off -> bit-identical.
        if export_trades_dir is not None:
            trades_by_strategy = {sid: res.trades for sid, res in results.items()}
            csv_path = _ReplayBT_Real.export_trades_csv(
                trades_by_strategy=trades_by_strategy,
                path=export_trades_dir,
                symbol=sym,
                mode=mode_tag,
            )
            exported_csv_paths.append(csv_path)
            print(f"    trades CSV: {csv_path}")

    # Optional aggregated trades_all.csv across all per-symbol CSVs.
    if export_trades_dir is not None and exported_csv_paths:
        _concatenate_trade_csvs(exported_csv_paths, export_trades_dir / "trades_all.csv")

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


def _concatenate_trade_csvs(per_symbol_csvs: list[Path], out_path: Path) -> Path:
    """Concatenate per-symbol trade CSVs into ``trades_all.csv``.

    Header is taken from the first input file; subsequent files contribute
    their data rows only. Uses stdlib :mod:`csv` to preserve quoting; each
    input CSV is read once and its rows passed through unchanged so the
    aggregated file is byte-for-byte the union of its inputs (modulo the
    duplicated header). The output directory is created if missing.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        header_written: bool = False
        for in_csv in per_symbol_csvs:
            with in_csv.open("r", newline="", encoding="utf-8") as fin:
                reader = csv.reader(fin)
                try:
                    header = next(reader)
                except StopIteration:
                    continue
                if not header_written:
                    writer.writerow(header)
                    header_written = True
                for row in reader:
                    writer.writerow(row)
    return out_path


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
    parser.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        default=True,
        help=(
            "Fortschritts-Logging pro Symbol (Default AN): alle ~250k Events "
            "bzw. ~10s eine Zeile mit Prozent + ETA, am Symbol-Ende eine "
            "'fertig in Xs'-Zeile. Kein Einfluss auf Trades."
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
        "--s3-time-stop",
        dest="s3_time_stop",
        action="store_true",
        default=False,
        help=(
            "Iter-4 Push A T1: enable S3's wall-clock time-stop "
            "(default 120 s, see S3_TIME_STOP_MS). Default off -> "
            "bit-identical to iter-3 behaviour."
        ),
    )
    parser.add_argument(
        "--s3-hard-stop",
        dest="s3_hard_stop",
        action="store_true",
        default=False,
        help=(
            "Iter-4 Push A T1: enable S3's mark-to-market hard-stop-loss "
            "(default -30 bps, see S3_HARD_STOP_BPS). Default off -> "
            "bit-identical to iter-3 behaviour."
        ),
    )
    parser.add_argument(
        "--s1-rho-instrument",
        dest="s1_rho_instrument",
        action="store_true",
        default=False,
        help=(
            "Iter-4 Push A T2: opt-in S1 rho-distribution instrumentation. "
            "Captures every rho value seen at the _check_entry call site "
            "and writes one 'rho_distribution_{symbol}.json' per symbol "
            "with quantiles to edge_research_framework/results/. Default "
            "off -> bit-identical."
        ),
    )
    parser.add_argument(
        "--s2-maker-only",
        dest="s2_maker_only",
        action="store_true",
        default=False,
        help=(
            "Iter-4 Push A T3: opt-in maker-only fill model for S2 only. "
            "Sets both S2 trade legs to 0.0 fees (worst-case-for-our-"
            "hypothesis vs. the ~-2.5 bps Bybit maker rebate). S3 and other "
            "strategies are unaffected. Default off -> bit-identical."
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
            "das Verhalten bit-identisch zur Live-Pipeline. Typischer Speedup "
            "~5-10x auf cascade-lastigen Daten; Trade-Liste in Grenzfaellen "
            "(Aftershock-Decay im Refit-Fenster) leicht abweichend."
        ),
    )
    parser.add_argument(
        "--export-trades",
        dest="export_trades",
        default=None,
        type=str,
        help=(
            "Opt-in per-trade CSV export. Path to a writeable directory. "
            "When set, writes one 'trades_{symbol}_{mode}.csv' per symbol "
            "plus an aggregated 'trades_all.csv' across symbols, with one "
            "row per round-trip trade (columns: symbol, strategy, entry_ts, "
            "exit_ts, side, entry_price, exit_price, quantity, raw_pnl, "
            "entry_fee, exit_fee, pnl_net, pnl_bps). Enables friction-vs-"
            "direction decomposition from a single replay run. Default off "
            "(no file writes) -> bit-identical to current behaviour."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    db_path = Path(args.db) if args.db else DB_PATH
    m15_refit_seconds = _resolve_fast_omori(args.fast_omori)

    # Apply direction-inversion flags BEFORE running any backtester so the
    # strategy instances see the flipped sign at trade-entry time.
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

    # Iter-4 Push A T1: opt-in bounded-loss exits for S3.
    if args.s3_time_stop:
        _cfg.S3_TIME_STOP_ENABLED = True
    if args.s3_hard_stop:
        _cfg.S3_HARD_STOP_ENABLED = True
    # Iter-4 Push A T2: opt-in S1 rho-distribution instrumentation.
    if args.s1_rho_instrument:
        _cfg.S1_RHO_INSTRUMENT_ENABLED = True
    # Iter-4 Push A T3: opt-in S2 maker-only fee model.
    if args.s2_maker_only:
        _cfg.S2_MAKER_ONLY = True

    # Surface the per-symbol progress lines (logging.INFO on the backtester
    # logger) when running interactively with progress enabled.
    if args.progress:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
        )

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
    if m15_refit_seconds > 0.0:
        print(
            f"  Performance-Modus: --fast-omori (M15 Omori-Refit alle "
            f"{m15_refit_seconds:g}s, kann Ergebnisse leicht abweichen)"
        )
    if inverts:
        print(f"  [INVERT] Inverted directions: {', '.join(sorted(inverts))}")
    if args.s3_time_stop:
        print(f"  [S3-TIME-STOP] enabled at {_cfg.S3_TIME_STOP_MS} ms")
    if args.s3_hard_stop:
        print(f"  [S3-HARD-STOP] enabled at {_cfg.S3_HARD_STOP_BPS} bps")
    if args.s1_rho_instrument:
        print("  [S1-RHO-INSTRUMENT] enabled (will dump rho_distribution_*.json)")
    if args.s2_maker_only:
        print("  [S2-MAKER-ONLY] enabled (S2 fees set to 0.0; S3 unaffected)")
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
    export_trades_dir: Optional[Path] = (
        Path(args.export_trades) if args.export_trades else None
    )
    # Iter-4 Push A T2: where rho_distribution_{symbol}.json files land
    # when --s1-rho-instrument is set. Mirrors the run-output directory.
    s1_rho_dir: Optional[Path] = None
    if args.s1_rho_instrument:
        s1_rho_dir = (
            Path(__file__).resolve().parent.parent
            / "edge_research_framework"
            / "results"
        )
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
        progress=args.progress,
        m15_refit_seconds=m15_refit_seconds,
        export_trades_dir=export_trades_dir,
        s1_rho_instrument_dir=s1_rho_dir,
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
        inverted_strategies=sorted(list(inverts)),
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
