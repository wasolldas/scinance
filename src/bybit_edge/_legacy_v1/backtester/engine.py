# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Event-time backtester with walk-forward cross-validation.

PRD requirements:
- Event-time indexing (no lookahead)
- Walk-forward: 30 d train / 7 d test (sliding)
- Embargo: 30 min between train and test
- Fees: taker 0.055 %, maker 0.02 %
- Slippage model: calibratable (default 2 bps)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Generator, Optional

import numpy as np

try:
    import polars as pl
except ImportError:
    pl = None  # type: ignore[assignment]

from bybit_edge.config import (
    FEE_TAKER,
    FEE_MAKER,
    WF_TRAIN_DAYS,
    WF_TEST_DAYS,
    WF_EMBARGO_MINUTES,
    RANDOM_SEED,
)

logger = logging.getLogger(__name__)

# Milliseconds per day / minute for timestamp arithmetic
_MS_PER_DAY = 24 * 3600 * 1000
_MS_PER_MIN = 60 * 1000


# ═════════════════════════════════════════════════════════════════════
# Data classes
# ═════════════════════════════════════════════════════════════════════

@dataclass
class Trade:
    """A single round-trip trade produced by the backtester.

    ``pnl`` is the *net* P&L (post-fee, post-slippage). The new
    ``raw_pnl`` / ``entry_fee`` / ``exit_fee`` fields are widened-in with
    ``0.0`` defaults so existing constructor calls and serialisers remain
    valid; the replay backtester's ``_make_trade`` populates them, enabling
    a friction-vs-direction decomposition without re-running the replay.
    Slippage is folded into ``entry_price`` / ``exit_price`` (they are the
    *slipped* prices), so the identity ``pnl == raw_pnl - entry_fee -
    exit_fee`` holds up to float tolerance.
    """

    symbol: str
    entry_ts: int              # ms
    exit_ts: int               # ms
    side: str                  # "Long" or "Short"
    entry_price: float         # slipped entry price
    exit_price: float          # slipped exit price
    quantity: float
    fee_type: str              # "taker" or "maker"
    pnl: float = 0.0           # net P&L in quote currency (raw_pnl - fees)
    pnl_bps: float = 0.0       # net P&L in basis points
    raw_pnl: float = 0.0       # pre-friction P&L: (slip_exit - slip_entry) * qty * sign
    entry_fee: float = 0.0     # taker/maker fee on the entry leg
    exit_fee: float = 0.0      # taker/maker fee on the exit leg


@dataclass
class BacktestResult:
    """Aggregate result of a backtest run."""

    trades: list[Trade]
    sharpe: float
    max_drawdown: float
    win_rate: float
    total_return: float
    n_trades: int
    equity_curve: np.ndarray


# ═════════════════════════════════════════════════════════════════════
# Walk-Forward Splitter
# ═════════════════════════════════════════════════════════════════════

class WalkForwardSplitter:
    """Generate train / test splits with an embargo gap.

    The ``ts`` column in *df* must contain Unix millisecond timestamps.
    The splitter slides a window across the data:

    ::

        |--- train_days ---|-- embargo --|--- test_days ---|
        ^                  ^             ^                 ^
        train_start     train_end   test_start         test_end

    Then the window advances by ``test_days`` and repeats.
    """

    def __init__(
        self,
        df: "pl.DataFrame",
        train_days: int = WF_TRAIN_DAYS,
        test_days: int = WF_TEST_DAYS,
        embargo_minutes: int = WF_EMBARGO_MINUTES,
    ) -> None:
        self.df = df
        self.train_days = train_days
        self.test_days = test_days
        self.embargo_minutes = embargo_minutes

        # Precompute timestamp bounds
        ts_col = df["ts"]
        self._min_ts: int = int(ts_col.min())  # type: ignore[arg-type]
        self._max_ts: int = int(ts_col.max())  # type: ignore[arg-type]

    def splits(
        self,
    ) -> Generator[tuple["pl.DataFrame", "pl.DataFrame"], None, None]:
        """Yield ``(train_df, test_df)`` pairs with embargo gap.

        Guarantees: ``test_start > train_end + embargo`` (no lookahead).
        """
        train_ms = self.train_days * _MS_PER_DAY
        test_ms = self.test_days * _MS_PER_DAY
        embargo_ms = self.embargo_minutes * _MS_PER_MIN

        cursor = self._min_ts

        while True:
            train_start = cursor
            train_end = train_start + train_ms
            test_start = train_end + embargo_ms
            test_end = test_start + test_ms

            if test_end > self._max_ts:
                break

            train_df = self.df.filter(
                (pl.col("ts") >= train_start) & (pl.col("ts") < train_end)
            )
            test_df = self.df.filter(
                (pl.col("ts") >= test_start) & (pl.col("ts") < test_end)
            )

            if len(train_df) > 0 and len(test_df) > 0:
                yield (train_df, test_df)

            # Slide by test_days
            cursor += test_ms


# ═════════════════════════════════════════════════════════════════════
# Backtest Engine
# ═════════════════════════════════════════════════════════════════════

class BacktestEngine:
    """Event-time backtester with fee and slippage modelling.

    The engine does *not* implement a strategy.  Instead, it accepts a
    ``strategy_fn`` callback that is trained on the *train* split and
    returns a *signal* function that is called bar-by-bar on the *test*
    split.

    ``strategy_fn(train_df) -> signal_fn``

    ``signal_fn(row_dict) -> Optional[dict]``
        * Returns ``None`` for no action.
        * Returns ``{"side": "Long"|"Short", "qty": float}`` for entry.
        * Returns ``{"action": "close"}`` to close the current position.
    """

    def __init__(
        self,
        fee_taker: float = FEE_TAKER,
        fee_maker: float = FEE_MAKER,
        slippage_bps: float = 2.0,
        random_seed: int = RANDOM_SEED,
    ) -> None:
        self.fee_taker = fee_taker
        self.fee_maker = fee_maker
        self.slippage_bps = slippage_bps
        self.rng = np.random.default_rng(random_seed)

    # ------------------------------------------------------------------
    # Fee / slippage helpers
    # ------------------------------------------------------------------

    def _apply_fee(self, price: float, qty: float, fee_type: str) -> float:
        """Return fee amount (positive = cost)."""
        rate = self.fee_taker if fee_type == "taker" else self.fee_maker
        return price * qty * rate

    def _slipped_price(self, price: float, side: str) -> float:
        """Return price adjusted for slippage (always adverse)."""
        slip_frac = self.slippage_bps / 10_000.0
        if side == "Long":
            return price * (1.0 + slip_frac)
        return price * (1.0 - slip_frac)

    # ------------------------------------------------------------------
    # Core: walk-forward
    # ------------------------------------------------------------------

    def run_walkforward(
        self,
        strategy_fn: Callable,
        data: "pl.DataFrame",
        symbol: str = "BTCUSDT",
    ) -> BacktestResult:
        """Run a full walk-forward backtest.

        Parameters
        ----------
        strategy_fn
            ``strategy_fn(train_df) -> signal_fn`` where
            ``signal_fn(row_dict) -> Optional[dict]``.
        data
            Polars DataFrame with at least columns ``ts``, ``close``.
        symbol
            Symbol label for ``Trade`` records.

        Returns
        -------
        BacktestResult
        """
        splitter = WalkForwardSplitter(data)
        all_trades: list[Trade] = []

        for train_df, test_df in splitter.splits():
            signal_fn = strategy_fn(train_df)
            fold_trades = self._run_fold(signal_fn, test_df, symbol)
            all_trades.extend(fold_trades)

        return self.compute_metrics(all_trades)

    def _run_fold(
        self,
        signal_fn: Callable,
        test_df: "pl.DataFrame",
        symbol: str,
    ) -> list[Trade]:
        """Process a single test fold bar-by-bar (strict event-time)."""
        trades: list[Trade] = []
        position: Optional[dict] = None  # {"side", "entry_price", "entry_ts", "qty"}

        rows = test_df.to_dicts()
        for row in rows:
            ts = int(row["ts"])
            close = float(row.get("close", 0))
            signal = signal_fn(row)
            if signal is None:
                continue

            action = signal.get("action", "")

            if action == "close" and position is not None:
                # Close existing position
                exit_price = self._slipped_price(close, "Short" if position["side"] == "Long" else "Long")
                fee = self._apply_fee(exit_price, position["qty"], "taker")
                entry_fee = self._apply_fee(position["entry_price"], position["qty"], "taker")

                if position["side"] == "Long":
                    raw_pnl = (exit_price - position["entry_price"]) * position["qty"]
                else:
                    raw_pnl = (position["entry_price"] - exit_price) * position["qty"]

                net_pnl = raw_pnl - fee - entry_fee
                pnl_bps = (net_pnl / (position["entry_price"] * position["qty"])) * 10_000

                trade = Trade(
                    symbol=symbol,
                    entry_ts=position["entry_ts"],
                    exit_ts=ts,
                    side=position["side"],
                    entry_price=position["entry_price"],
                    exit_price=exit_price,
                    quantity=position["qty"],
                    fee_type="taker",
                    pnl=net_pnl,
                    pnl_bps=pnl_bps,
                )
                trades.append(trade)
                position = None

            elif action != "close" and position is None:
                # Open new position
                side = signal.get("side", "Long")
                qty = float(signal.get("qty", 1.0))
                entry_price = self._slipped_price(close, side)
                position = {
                    "side": side,
                    "entry_price": entry_price,
                    "entry_ts": ts,
                    "qty": qty,
                }

        # Force-close any open position at the end of the fold
        if position is not None and len(rows) > 0:
            last_row = rows[-1]
            close = float(last_row.get("close", 0))
            exit_price = self._slipped_price(close, "Short" if position["side"] == "Long" else "Long")
            fee = self._apply_fee(exit_price, position["qty"], "taker")
            entry_fee = self._apply_fee(position["entry_price"], position["qty"], "taker")
            if position["side"] == "Long":
                raw_pnl = (exit_price - position["entry_price"]) * position["qty"]
            else:
                raw_pnl = (position["entry_price"] - exit_price) * position["qty"]
            net_pnl = raw_pnl - fee - entry_fee
            pnl_bps = (net_pnl / (position["entry_price"] * position["qty"])) * 10_000 if position["entry_price"] > 0 else 0.0
            trades.append(Trade(
                symbol=symbol,
                entry_ts=position["entry_ts"],
                exit_ts=int(last_row["ts"]),
                side=position["side"],
                entry_price=position["entry_price"],
                exit_price=exit_price,
                quantity=position["qty"],
                fee_type="taker",
                pnl=net_pnl,
                pnl_bps=pnl_bps,
            ))

        return trades

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def compute_metrics(self, trades: list[Trade]) -> BacktestResult:
        """Compute aggregate performance metrics from a list of trades.

        Metrics: Sharpe ratio (annualised, assuming 365 trading days),
        max drawdown, win rate, total return.
        """
        n = len(trades)
        if n == 0:
            return BacktestResult(
                trades=[],
                sharpe=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_return=0.0,
                n_trades=0,
                equity_curve=np.array([0.0]),
            )

        pnls = np.array([t.pnl for t in trades], dtype=np.float64)
        equity = np.cumsum(pnls)
        equity_with_start = np.concatenate([[0.0], equity])

        # Win rate
        wins = np.sum(pnls > 0)
        win_rate = float(wins / n)

        # Total return (sum of P&L)
        total_return = float(equity[-1])

        # Max drawdown
        running_max = np.maximum.accumulate(equity_with_start)
        drawdowns = running_max - equity_with_start
        max_drawdown = float(np.max(drawdowns))

        # Sharpe ratio (annualised)
        mean_pnl = float(np.mean(pnls))
        std_pnl = float(np.std(pnls, ddof=1)) if n > 1 else 1.0
        if std_pnl == 0:
            sharpe = 0.0
        else:
            # Annualise: assume ~1 trade per bar, ~365 * 24 * 60 bars/year
            # But since trade frequency varies, we use sqrt(n_trades_per_year)
            # Simple approach: Sharpe = mean / std * sqrt(252)
            sharpe = (mean_pnl / std_pnl) * np.sqrt(252)

        return BacktestResult(
            trades=trades,
            sharpe=float(sharpe),
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_return=total_return,
            n_trades=n,
            equity_curve=equity_with_start,
        )
