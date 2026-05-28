"""
Backtest-Driver — Walk-Forward-Vergleich backtestbarer Strategien.

Lädt historische Klines + Funding-History via Bybit REST (öffentlich, kein
Key nötig), baut einen Feature-DataFrame und vergleicht mehrere Strategien
über Walk-Forward-Cross-Validation.

EHRLICHE EINORDNUNG — was geht und was nicht:
    Backtestbar aus öffentlicher REST-Historie:
        * Funding-/Settlement-Reversion (Kern von Strategie 3)
        * Preis-Action-Baselines (Momentum, Buy&Hold) als Referenz
        * Regime-gegatetes Momentum (nutzt echtes M7 Permutation Entropy)
    NICHT backtestbar aus REST-Historie (brauchen selbst gesammelte Tickdaten):
        * S1 Cascade (Liquidations-Stream historisch nicht verfügbar)
        * S2 Entropie-Momentum (Orderbook-Tiefe historisch nicht verfügbar)
        * S4/S5 (Multi-Symbol-Tick + Foundation-Modelle)

Aufruf:
    python scripts/backtest.py --symbol BTCUSDT --interval 5 --months 6
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import polars as pl

from bybit_edge.backtester.engine import BacktestEngine
from bybit_edge.config import (
    DATA_DIR,
    FUNDING_SETTLEMENT_HOURS_UTC,
    rest_base_url,
)
from bybit_edge.layers.l3_regime.m7_permutation_entropy import M7PermutationEntropy

_MS_DAY = 24 * 3600 * 1000


# ══════════════════════════════════════════════════════════════════════
# REST-Backfill (öffentlich, kein Key)
# ══════════════════════════════════════════════════════════════════════

def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{rest_base_url()}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


def backfill_klines(symbol: str, interval: str, months: int) -> pl.DataFrame:
    """Lädt Klines (paginiert, rückwärts) und cached sie als Parquet."""
    cache = DATA_DIR / "parquet" / f"{symbol}_{interval}m_{months}mo.parquet"
    if cache.exists():
        print(f"  Cache-Treffer: {cache.name}")
        return pl.read_parquet(cache)

    target_start = int(time.time() * 1000) - months * 30 * _MS_DAY
    end = int(time.time() * 1000)
    rows: list[list[Any]] = []
    print(f"  Lade {months} Monate {interval}m-Klines für {symbol} …")
    while True:
        body = _get("/v5/market/kline", {
            "category": "linear", "symbol": symbol,
            "interval": interval, "end": end, "limit": 1000,
        })
        lst = body.get("result", {}).get("list", [])
        if not lst:
            break
        rows.extend(lst)
        oldest = int(lst[-1][0])
        if oldest <= target_start or len(lst) < 1000:
            break
        end = oldest - 1
        time.sleep(0.25)

    if not rows:
        raise RuntimeError("Keine Kline-Daten erhalten.")

    df = pl.DataFrame(
        {
            "ts": [int(r[0]) for r in rows],
            "open": [float(r[1]) for r in rows],
            "high": [float(r[2]) for r in rows],
            "low": [float(r[3]) for r in rows],
            "close": [float(r[4]) for r in rows],
            "volume": [float(r[5]) for r in rows],
        }
    ).unique(subset=["ts"]).sort("ts").filter(pl.col("ts") >= target_start)

    cache.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(cache)
    print(f"  {len(df)} Bars geladen, gecached -> {cache.name}")
    return df


def backfill_funding(symbol: str, months: int) -> pl.DataFrame:
    """Lädt Funding-Rate-History (paginiert, rückwärts)."""
    target_start = int(time.time() * 1000) - months * 30 * _MS_DAY
    end = int(time.time() * 1000)
    recs: list[tuple[int, float]] = []
    print(f"  Lade Funding-History für {symbol} …")
    while True:
        body = _get("/v5/market/funding/history", {
            "category": "linear", "symbol": symbol,
            "endTime": end, "limit": 200,
        })
        lst = body.get("result", {}).get("list", [])
        if not lst:
            break
        for item in lst:
            recs.append((int(item["fundingRateTimestamp"]), float(item["fundingRate"])))
        oldest = int(lst[-1]["fundingRateTimestamp"])
        if oldest <= target_start or len(lst) < 200:
            break
        end = oldest - 1
        time.sleep(0.25)

    if not recs:
        # Funding optional — leere Spalte ist ok
        return pl.DataFrame({"ts": [], "funding_rate": []}, schema={"ts": pl.Int64, "funding_rate": pl.Float64})

    return pl.DataFrame(
        {"ts": [r[0] for r in recs], "funding_rate": [r[1] for r in recs]}
    ).unique(subset=["ts"]).sort("ts")


def _seconds_to_settlement(ts_ms: int) -> float:
    """Sekunden bis zum nächsten Funding-Settlement (00/08/16 UTC)."""
    sec = ts_ms / 1000.0
    day_sec = sec % 86400.0
    hour = day_sec / 3600.0
    nexts = [h for h in FUNDING_SETTLEMENT_HOURS_UTC if h > hour]
    next_h = nexts[0] if nexts else FUNDING_SETTLEMENT_HOURS_UTC[0] + 24
    return next_h * 3600.0 - day_sec


def build_features(klines: pl.DataFrame, funding: pl.DataFrame) -> pl.DataFrame:
    """Joint Funding (as-of) und berechnet seconds_to_settlement."""
    df = klines
    if len(funding) > 0:
        df = df.join_asof(funding, on="ts", strategy="backward")
    else:
        df = df.with_columns(pl.lit(0.0).alias("funding_rate"))
    df = df.with_columns(pl.col("funding_rate").fill_null(0.0))
    stt = [_seconds_to_settlement(int(t)) for t in df["ts"]]
    return df.with_columns(pl.Series("seconds_to_settlement", stt))


# ══════════════════════════════════════════════════════════════════════
# Strategie-Adapter  (strategy_fn(train_df) -> signal_fn(row) -> dict|None)
# ══════════════════════════════════════════════════════════════════════

def strat_buy_hold() -> Callable:
    def strategy_fn(train_df: pl.DataFrame) -> Callable:
        opened = {"v": False}

        def signal_fn(row: dict) -> Optional[dict]:
            if not opened["v"]:
                opened["v"] = True
                return {"side": "Long", "qty": 1.0}
            return None
        return signal_fn
    return strategy_fn


def strat_momentum(window: int = 20, band: float = 0.001) -> Callable:
    def strategy_fn(train_df: pl.DataFrame) -> Callable:
        closes: deque[float] = deque(maxlen=window)

        def signal_fn(row: dict) -> Optional[dict]:
            c = float(row["close"])
            closes.append(c)
            if len(closes) < window:
                return None
            sma = sum(closes) / len(closes)
            if c > sma * (1 + band):
                return {"side": "Long", "qty": 1.0}
            if c < sma * (1 - band):
                return {"action": "close"}
            return None
        return signal_fn
    return strategy_fn


def strat_funding_reversion(window_min: int = 30, thr: float = 0.0003) -> Callable:
    """S3-Proxy: extremes Funding vor Settlement -> Mean-Reversion-Trade.

    Hinweis: Dies testet die Funding-MAGNITUDE-Reversion, nicht das volle
    M22-Clamp-Pressure (dessen Premium-Index historisch nicht verfügbar ist).
    """
    def strategy_fn(train_df: pl.DataFrame) -> Callable:
        def signal_fn(row: dict) -> Optional[dict]:
            f = float(row.get("funding_rate", 0.0))
            stt = float(row.get("seconds_to_settlement", 9e9))
            in_window = 0 < stt < window_min * 60
            if in_window and abs(f) > thr:
                # Positives Funding -> Longs zahlen -> Perp tendenziell überhitzt
                # -> Short-Reversion; negatives Funding -> Long-Reversion.
                return {"side": "Short" if f > 0 else "Long", "qty": 1.0}
            if not in_window:
                return {"action": "close"}
            return None
        return signal_fn
    return strategy_fn


def strat_pe_gated_momentum(window: int = 20, band: float = 0.001) -> Callable:
    """Momentum, aber nur wenn M7 Permutation Entropy Greenlight gibt."""
    def strategy_fn(train_df: pl.DataFrame) -> Callable:
        closes: deque[float] = deque(maxlen=window)
        pe = M7PermutationEntropy()

        def signal_fn(row: dict) -> Optional[dict]:
            c = float(row["close"])
            closes.append(c)
            gl = pe.update(c).get("greenlight", False)
            if len(closes) < window:
                return None
            sma = sum(closes) / len(closes)
            if gl and c > sma * (1 + band):
                return {"side": "Long", "qty": 1.0}
            if c < sma * (1 - band):
                return {"action": "close"}
            return None
        return signal_fn
    return strategy_fn


STRATEGIES: dict[str, Callable] = {
    "buy_hold (Ref)": strat_buy_hold(),
    "momentum (Ref)": strat_momentum(),
    "funding_reversion (S3-proxy)": strat_funding_reversion(),
    "pe_gated_momentum (M7)": strat_pe_gated_momentum(),
}


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Bybit Edge Backtest-Driver")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="5", help="Kline-Intervall in Minuten")
    parser.add_argument("--months", type=int, default=6)
    args = parser.parse_args()

    print("=" * 70)
    print(f"  BACKTEST — {args.symbol} — {args.interval}m — {args.months} Monate")
    print("=" * 70)

    klines = backfill_klines(args.symbol, args.interval, args.months)
    funding = backfill_funding(args.symbol, args.months)
    df = build_features(klines, funding)
    print(f"  Feature-DataFrame: {len(df)} Bars, "
          f"{(df['ts'].max() - df['ts'].min()) / _MS_DAY:.0f} Tage\n")

    engine = BacktestEngine()
    results: list[dict[str, Any]] = []
    for name, strat in STRATEGIES.items():
        res = engine.run_walkforward(strat, df, symbol=args.symbol)
        results.append({
            "strategy": name,
            "sharpe": round(res.sharpe, 3),
            "win_rate": round(res.win_rate, 3),
            "max_dd": round(res.max_drawdown, 2),
            "total_return": round(res.total_return, 2),
            "n_trades": res.n_trades,
        })

    results.sort(key=lambda r: r["sharpe"], reverse=True)

    print(f"{'Strategie':<32}{'Sharpe':>8}{'Hit':>7}{'MaxDD':>10}{'Return':>10}{'Trades':>8}")
    print("-" * 75)
    for r in results:
        print(f"{r['strategy']:<32}{r['sharpe']:>8.2f}{r['win_rate']:>7.2f}"
              f"{r['max_dd']:>10.1f}{r['total_return']:>10.1f}{r['n_trades']:>8}")

    out = DATA_DIR.parent / "edge_research_framework" / "results" / "backtest_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nErgebnisse gespeichert: {out}")
    print("\nHinweis: S1/S2/S4/S5 brauchen selbst gesammelte Tick-/Orderbook-Daten")
    print("und sind aus reiner REST-Historie nicht backtestbar (siehe Doc im Skript).")


if __name__ == "__main__":
    main()
