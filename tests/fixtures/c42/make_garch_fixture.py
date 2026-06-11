#!/usr/bin/env python3
"""Generate a synthetic GARCH(1,1) 1-minute kline fixture for the C-42 smoke.

GARCH-simulated log returns produce genuine volatility clustering, so HAR-RV
(which exploits exactly that autocorrelation in realised vol) MUST achieve a
clearly positive OOS-R^2 on this data — the pipeline's sanity floor.

Deterministic given the seed. Writes ``btc_garch_30d.csv`` with columns
ts,symbol,open,high,low,close,volume,turnover (1-min bars, 30 days).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260611
SYMBOL = "BTCUSDT"
MINUTES = 30 * 1440  # 30 days of 1-minute bars
START_TS_MS = 1_735_689_600_000  # 2025-01-01T00:00:00Z, arbitrary anchor
START_PRICE = 60_000.0

# GARCH(1,1) parameters with strong persistence (alpha+beta ~ 0.98) so vol
# clustering is pronounced and HAR-RV has real signal to fit. Unconditional
# per-minute vol = sqrt(omega/(1-alpha-beta)) ~ 0.0007 (7 bps), realistic for
# 1-min crypto returns; persistence kept high without exploding the price path.
OMEGA = 1.0e-8
ALPHA = 0.08
BETA = 0.90


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n = MINUTES
    eps = np.empty(n)
    sigma2 = np.empty(n)
    sigma2[0] = OMEGA / (1.0 - ALPHA - BETA)
    z = rng.standard_normal(n)
    eps[0] = np.sqrt(sigma2[0]) * z[0]
    # Pure GARCH recursion (no seasonality in the feedback loop, otherwise the
    # high-persistence process can run away).
    for t in range(1, n):
        sigma2[t] = OMEGA + ALPHA * eps[t - 1] ** 2 + BETA * sigma2[t - 1]
        eps[t] = np.sqrt(sigma2[t]) * z[t]

    # Apply a mild intraday seasonal multiplier (U-shape) to the OBSERVED return
    # only, so the tod_* features carry information without destabilising GARCH.
    minute_of_day = (np.arange(n) % 1440)
    seasonal = 1.0 + 0.3 * np.cos(2 * np.pi * minute_of_day / 1440.0) ** 2
    ret = eps * seasonal

    log_price = np.log(START_PRICE) + np.cumsum(ret)
    close = np.exp(log_price)
    open_ = np.concatenate([[START_PRICE], close[:-1]])
    # Intrabar high/low from a fraction of the per-bar return magnitude.
    spread = np.abs(ret) * close * 0.5 + close * 1e-5
    high = np.maximum(open_, close) + spread * rng.uniform(0.2, 1.0, n)
    low = np.minimum(open_, close) - spread * rng.uniform(0.2, 1.0, n)
    # Volume correlated with volatility (more activity in turbulent minutes).
    volume = 10.0 + 5000.0 * np.abs(ret) / np.sqrt(sigma2.mean()) + rng.gamma(2.0, 1.0, n)
    turnover = volume * close

    ts = START_TS_MS + np.arange(n) * 60_000
    return pd.DataFrame(
        {
            "ts": ts.astype(np.int64),
            "symbol": SYMBOL,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "turnover": turnover,
        }
    )


def main() -> None:
    out = Path(__file__).resolve().parent / "btc_garch_30d.csv"
    df = generate()
    df.to_csv(out, index=False)
    print(f"wrote {len(df)} rows -> {out}")


if __name__ == "__main__":
    main()
