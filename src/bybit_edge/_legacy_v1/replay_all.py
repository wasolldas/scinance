"""
Multi-Symbol Replay Aggregator — runs the :class:`ReplayBacktester` over every
symbol persisted in DuckDB and aggregates per-strategy edge metrics across the
whole universe.

The motivation is honest: BTCUSDT is mature and dominated by HFT noise — many
of the novel edges (especially S1 Liquidations-Cascade and S3 Pre-Settlement
on small caps) only become visible when measured on multiple coins
simultaneously. The single-symbol replay only ever scored BTC; this module
fans out across whichever symbols were collected by the LiveRunner and rolls
up the per-strategy edge metrics so the user can spot where each strategy
actually works.

The module is import-light (only ``ReplayBacktester`` and ``PersistenceLayer``)
and contains no Streamlit / CLI code — :mod:`scripts.replay_all` builds the CLI
on top of these helpers.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from bybit_edge._legacy_v1.backtester.engine import BacktestResult
from bybit_edge.config import DB_PATH, MULTI_SYMBOL_UNIVERSE
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge._legacy_v1.replay_backtester import ReplayBacktester

logger = logging.getLogger(__name__)


# Status thresholds — match the dashboard renderer (``_replay_status``):
# 0 trades → "no-trades", 1-4 → "data-limited", >= 5 → "OK".
_STATUS_OK_MIN_TRADES: int = 5

# Strategy ids in their canonical order — keeps output stable.
_STRATEGY_IDS: tuple[str, ...] = ("S1", "S2", "S3", "S4", "S5")


# --------------------------------------------------------------------------
# Symbol discovery
# --------------------------------------------------------------------------

def discover_symbols(db_path: Optional[Path] = None) -> list[str]:
    """Return the distinct ``symbol`` values present in the ``tickers`` table.

    Falls back to :data:`bybit_edge.config.MULTI_SYMBOL_UNIVERSE` when:

    * the DuckDB file does not exist,
    * the ``tickers`` table is empty,
    * or any DuckDB error occurs while querying.

    The fallback is intentional — the user wants the *replay* to keep working
    even when they ran the LiveRunner with persistence off and have no
    persisted tickers. In that case the per-symbol replay will simply log
    "skipped" for every symbol and produce empty aggregates.
    """
    resolved = db_path if db_path is not None else DB_PATH
    if str(resolved) != ":memory:" and not Path(resolved).exists():
        logger.info(
            "DuckDB %s does not exist — falling back to MULTI_SYMBOL_UNIVERSE",
            resolved,
        )
        return list(MULTI_SYMBOL_UNIVERSE)

    try:
        persist = PersistenceLayer(db_path=resolved, read_only=True)
    except Exception:  # noqa: BLE001 — fall back gracefully
        logger.exception(
            "Failed to open DuckDB for symbol discovery — falling back to universe"
        )
        return list(MULTI_SYMBOL_UNIVERSE)

    try:
        rows = persist.conn.execute(
            "SELECT DISTINCT symbol FROM tickers ORDER BY symbol"
        ).fetchall()
    except Exception:  # noqa: BLE001 — table may not exist in stripped DBs
        logger.exception(
            "Symbol discovery query failed — falling back to universe"
        )
        return list(MULTI_SYMBOL_UNIVERSE)
    finally:
        persist.close()

    symbols = [str(r[0]) for r in rows if r and r[0]]
    if not symbols:
        logger.info(
            "tickers table is empty — falling back to MULTI_SYMBOL_UNIVERSE"
        )
        return list(MULTI_SYMBOL_UNIVERSE)
    return symbols


# --------------------------------------------------------------------------
# Status classification
# --------------------------------------------------------------------------

def classify_status(n_trades: int) -> str:
    """Return the per-symbol-strategy status label.

    * ``"no-trades"``   — strategy never opened a position (n_trades == 0)
    * ``"data-limited"`` — strategy opened but on too small a sample to be
      statistically meaningful (1 ≤ n_trades < 5)
    * ``"OK"``          — n_trades >= 5

    The thresholds match what the dashboard's strategy-performance tab
    already uses, so the labels stay consistent across CLI and UI.
    """
    if n_trades <= 0:
        return "no-trades"
    if n_trades < _STATUS_OK_MIN_TRADES:
        return "data-limited"
    return "OK"


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------

def _trade_weighted_mean(values: list[tuple[float, int]]) -> float:
    """Weighted mean of ``(value, n_trades)`` pairs; ignores n==0 entries.

    Returns ``0.0`` when no entry has a positive weight — a Sharpe / win-rate
    is meaningless without at least one trade, so reporting 0.0 instead of
    NaN keeps downstream JSON / dashboard consumers simple.
    """
    num = 0.0
    den = 0
    for v, n in values:
        if n <= 0:
            continue
        num += float(v) * int(n)
        den += int(n)
    return num / den if den > 0 else 0.0


def aggregate_per_strategy(
    per_symbol: dict[str, dict[str, BacktestResult]],
) -> dict[str, dict[str, Any]]:
    """Aggregate per-strategy metrics across all symbols.

    Parameters
    ----------
    per_symbol
        ``{symbol: {strategy_id: BacktestResult}}`` — exactly what the
        :class:`ReplayBacktester` produces, but keyed by symbol.

    Returns
    -------
    dict[str, dict]
        ``{strategy_id: {total_trades, weighted_sharpe, mean_win_rate,
        total_return, worst_max_dd, best_symbol, data_limited_symbols}}``.

    Notes
    -----
    * ``weighted_sharpe`` and ``mean_win_rate`` are trade-weighted means that
      ignore symbols with zero trades — averaging a 0.0 Sharpe of an idle
      strategy into the score would falsely deflate the verdict.
    * ``total_return`` is a *sum* — the per-symbol returns are in USDT-per-
      unit terms and not directly comparable across coins, but the sign and
      relative size are still informative. The CLI flags this explicitly.
    * ``worst_max_dd`` reports the deepest drawdown observed on any single
      symbol — a risk-side aggregate (max, not mean), which is the honest
      reading.
    * ``best_symbol`` is the symbol with the highest Sharpe for this
      strategy (only counting n_trades > 0; ``None`` if no symbol traded).
    * ``data_limited_symbols`` lists every symbol whose status was either
      ``"no-trades"`` or ``"data-limited"`` for this strategy.
    """
    # Build the strategy id set from data (rather than hard-coding) so that
    # we degrade gracefully if a future strategy is added.
    strategy_ids: list[str] = []
    seen: set[str] = set()
    for sym_results in per_symbol.values():
        for sid in sym_results:
            if sid not in seen:
                seen.add(sid)
                strategy_ids.append(sid)
    # Keep canonical order where possible — append unknown ids at the end.
    ordered = [s for s in _STRATEGY_IDS if s in seen] + [
        s for s in strategy_ids if s not in _STRATEGY_IDS
    ]

    out: dict[str, dict[str, Any]] = {}
    for sid in ordered:
        sharpe_pairs: list[tuple[float, int]] = []
        wr_pairs: list[tuple[float, int]] = []
        total_trades = 0
        total_return = 0.0
        worst_dd = 0.0
        best_sharpe = float("-inf")
        best_symbol: Optional[str] = None
        data_limited_symbols: list[str] = []

        for sym in sorted(per_symbol.keys()):
            sym_results = per_symbol[sym]
            res = sym_results.get(sid)
            if res is None:
                # Symbol was skipped (e.g. no events) — count as data-limited
                # for this strategy.
                data_limited_symbols.append(sym)
                continue
            n = int(res.n_trades)
            total_trades += n
            total_return += float(res.total_return)
            worst_dd = max(worst_dd, float(res.max_drawdown))
            sharpe_pairs.append((float(res.sharpe), n))
            wr_pairs.append((float(res.win_rate), n))
            if classify_status(n) != "OK":
                data_limited_symbols.append(sym)
            elif float(res.sharpe) > best_sharpe:
                best_sharpe = float(res.sharpe)
                best_symbol = sym

        out[sid] = {
            "total_trades": total_trades,
            "weighted_sharpe": round(_trade_weighted_mean(sharpe_pairs), 4),
            "mean_win_rate": round(_trade_weighted_mean(wr_pairs), 4),
            "total_return": round(total_return, 4),
            "worst_max_dd": round(worst_dd, 4),
            "best_symbol": best_symbol,
            "data_limited_symbols": data_limited_symbols,
        }
    return out


def build_per_symbol_payload(
    per_symbol: dict[str, dict[str, BacktestResult]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Convert ``{symbol: {sid: BacktestResult}}`` into a JSON-friendly nested
    dict carrying the per-symbol metrics + status label.
    """
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for sym, sym_results in per_symbol.items():
        sym_out: dict[str, dict[str, Any]] = {}
        for sid, res in sym_results.items():
            n = int(res.n_trades)
            sym_out[sid] = {
                "sharpe": round(float(res.sharpe), 4),
                "win_rate": round(float(res.win_rate), 4),
                "max_drawdown": round(float(res.max_drawdown), 4),
                "total_return": round(float(res.total_return), 4),
                "n_trades": n,
                "status": classify_status(n),
            }
        out[sym] = sym_out
    return out


def top_n_edges(
    per_symbol_payload: dict[str, dict[str, dict[str, Any]]],
    n: int = 3,
    min_trades: int = _STATUS_OK_MIN_TRADES,
) -> list[dict[str, Any]]:
    """Return the top-``n`` (symbol, strategy, sharpe) entries by Sharpe.

    Filters to ``n_trades >= min_trades`` — a 17-Sharpe on a single trade is
    almost certainly noise and would mislead the user. Sorted descending by
    Sharpe; ties broken by ``n_trades`` descending.
    """
    candidates: list[dict[str, Any]] = []
    for sym in per_symbol_payload:
        for sid, m in per_symbol_payload[sym].items():
            if int(m.get("n_trades", 0)) < int(min_trades):
                continue
            candidates.append(
                {
                    "symbol": sym,
                    "strategy": sid,
                    "sharpe": float(m.get("sharpe", 0.0)),
                    "n_trades": int(m.get("n_trades", 0)),
                    "win_rate": float(m.get("win_rate", 0.0)),
                }
            )
    candidates.sort(
        key=lambda c: (c["sharpe"], c["n_trades"]),
        reverse=True,
    )
    return candidates[: max(int(n), 0)]


# --------------------------------------------------------------------------
# Per-symbol driver
# --------------------------------------------------------------------------

def run_symbol(
    symbol: str,
    *,
    db_path: Optional[Path],
    walkforward: bool,
    pipeline_interval_seconds: float,
    train_days: int,
    test_days: int,
    embargo_minutes: int,
) -> Optional[dict[str, BacktestResult]]:
    """Run the :class:`ReplayBacktester` for a single symbol.

    Returns ``None`` when the symbol has zero persisted events (so the caller
    can log a "skipped" message and continue with the next symbol).

    Walk-forward folds that don't fit into the symbol's data window simply
    return zero-trade results for every strategy — that is the honest signal
    and matches the single-symbol replay's behaviour.
    """
    bt = ReplayBacktester(symbol=symbol, db_path=db_path)
    try:
        n_events = bt.load_events()
        if n_events == 0:
            return None
        if walkforward:
            return bt.run_walkforward(
                pipeline_interval_seconds=pipeline_interval_seconds,
                train_days=train_days,
                test_days=test_days,
                embargo_minutes=embargo_minutes,
            )
        return bt.run(pipeline_interval_seconds=pipeline_interval_seconds)
    finally:
        bt.close()


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def replay_all(
    symbols: list[str],
    *,
    db_path: Optional[Path] = None,
    walkforward: bool = False,
    pipeline_interval_seconds: float = 1.0,
    train_days: int = 7,
    test_days: int = 1,
    embargo_minutes: int = 30,
) -> dict[str, Any]:
    """Replay every symbol and return the full aggregated payload dict.

    The returned dict matches the on-disk JSON schema documented in the
    task description (``mode``, ``symbols``, ``generated_at``,
    ``per_strategy_aggregate``, ``per_symbol``).

    Symbols with no persisted events are logged at INFO level and listed in
    ``skipped_symbols`` — neither the per-symbol section nor the aggregates
    include them (they would be counted as data-limited for every strategy
    which is not what the user wants for a fully-missing symbol).
    """
    per_symbol_results: dict[str, dict[str, BacktestResult]] = {}
    skipped: list[str] = []

    for sym in symbols:
        try:
            res = run_symbol(
                sym,
                db_path=db_path,
                walkforward=walkforward,
                pipeline_interval_seconds=pipeline_interval_seconds,
                train_days=train_days,
                test_days=test_days,
                embargo_minutes=embargo_minutes,
            )
        except Exception:  # noqa: BLE001 — one bad symbol must not kill the run
            logger.exception("Replay failed for %s — skipping", sym)
            skipped.append(sym)
            continue
        if res is None:
            logger.info("Skipping %s — no persisted events", sym)
            skipped.append(sym)
            continue
        per_symbol_results[sym] = res

    per_symbol_payload = build_per_symbol_payload(per_symbol_results)
    per_strategy_agg = aggregate_per_strategy(per_symbol_results)

    return {
        "mode": "walkforward" if walkforward else "single_pass",
        "symbols": sorted(per_symbol_results.keys()),
        "skipped_symbols": sorted(skipped),
        "generated_at": (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "per_strategy_aggregate": per_strategy_agg,
        "per_symbol": per_symbol_payload,
        "top_edges": top_n_edges(per_symbol_payload, n=3),
    }


# --------------------------------------------------------------------------
# Legacy-shape conversion (for the old dashboard JSON path)
# --------------------------------------------------------------------------

def to_legacy_single_symbol_payload(
    aggregate_payload: dict[str, Any],
) -> dict[str, Any]:
    """Project the multi-symbol payload into the old single-symbol shape.

    The dashboard's existing ``load_replay_results()`` already understands
    ``{"results": [...]}`` with per-strategy rows. We expose the *aggregate*
    Sharpe / win-rate / DD numbers in that shape so a user who never updates
    their dashboard still sees something useful in the legacy
    ``replay_backtest_results.json`` path.

    ``symbol`` is set to a comma-joined summary so the dashboard caption
    truthfully reflects that this is a multi-symbol roll-up, not a BTC-only
    result that happens to live in the legacy filename.
    """
    agg = aggregate_payload.get("per_strategy_aggregate", {})
    rows: list[dict[str, Any]] = []
    for sid, m in agg.items():
        rows.append(
            {
                "strategy": sid,
                "sharpe": round(float(m.get("weighted_sharpe", 0.0)), 3),
                "win_rate": round(float(m.get("mean_win_rate", 0.0)), 3),
                "max_dd": round(float(m.get("worst_max_dd", 0.0)), 4),
                "total_return": round(float(m.get("total_return", 0.0)), 4),
                "n_trades": int(m.get("total_trades", 0)),
                "data_limited": (
                    int(m.get("total_trades", 0)) < _STATUS_OK_MIN_TRADES
                ),
            }
        )
    rows.sort(key=lambda r: r["sharpe"], reverse=True)
    symbols = aggregate_payload.get("symbols", [])
    return {
        "symbol": ",".join(symbols) if symbols else "",
        "interval_seconds": None,
        "n_events": 0,
        "mode": aggregate_payload.get("mode", "single_pass"),
        "results": rows,
        "notes": {
            "real_testable": ["S1", "S3"],
            "data_limited": ["S2", "S4", "S5"],
            "reason": (
                "Aggregate ueber alle Symbole — pro Strategie trade-gewichtete "
                "Sharpe/WinRate, summierter Return, schlechtester MaxDD."
            ),
        },
    }
