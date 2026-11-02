"""H-27 series builders (pre-period only): DVOL daily close and Bybit daily closes, RV_fwd30.

Conventions (DATENPROBE.md A.1/A.2): IV(t) = close of the DVOL hourly candle starting 23:00 UTC of
day t; C_s = close of the Bybit 1D candle of UTC day s (last trade before 00:00 UTC of s+1);
RV_fwd30(t) = sqrt((365/30) * sum_{k=1..30} r_{t+k}^2), r_s = ln(C_s / C_{s-1}); one annualisation
constant 365.  Guards from h27_common: prices truncated at 2024-05-31, DVOL levels only <= 2024-06-30.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from h27_common import (NUISANCE_FIRST_IV_DAY, NUISANCE_LAST_IV_DAY, RV_LAST_PRICE_DAY,
                        assert_dvol_level_day, harvest, truncate_prices)

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent / "panel" / "panel_1d"
ANN = 365.0
H = 30
SYM_PANEL = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}


def _days(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)]


def dvol_daily_close(sym: str, lo: str = NUISANCE_FIRST_IV_DAY,
                     hi: str = NUISANCE_LAST_IV_DAY) -> dict[str, float]:
    """IV(t) in decimal (DVOL / 100) for t in [lo, hi]; refuses days after the DVOL level rule."""
    assert_dvol_level_day(hi)
    hd = harvest()
    df = hd.load("dvol", [sym], lo, hi, exchange="deribit", columns=["payload_json"])
    out: dict[str, float] = {}
    for pj in df["payload_json"].to_list():
        o = json.loads(pj)
        dt = datetime.fromtimestamp(int(o["timestamp"]) / 1000, tz=timezone.utc)
        d = dt.date().isoformat()
        if dt.hour == 23 and lo <= d <= hi:
            assert_dvol_level_day(d)
            out[d] = float(o["close"]) / 100.0
    return out


def panel_closes(sym: str) -> tuple[list[str], np.ndarray]:
    """Daily closes of the Bybit perp, truncated at RV_LAST_PRICE_DAY BEFORE any return."""
    rows: list[tuple[str, float]] = []
    psym = SYM_PANEL[sym]
    for state in ("frozen", "open"):
        base = PANEL / state / "source=bybit" / "category=linear" / f"symbol={psym}"
        if not base.is_dir():
            continue
        for f in sorted(base.glob("year=*/part.parquet")):
            t = pq.ParquetFile(f).read(columns=["start_ms", "close"])
            for ms, c in zip(t.column("start_ms").to_pylist(), t.column("close").to_pylist()):
                rows.append((datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat(),
                             float(c)))
    rows.sort()
    days, closes = truncate_prices([d for d, _ in rows], [c for _, c in rows])
    if max(days) > RV_LAST_PRICE_DAY:
        raise RuntimeError("truncation failed")
    return days, np.asarray(closes, dtype=np.float64)


def daily_log_returns(sym: str) -> tuple[list[str], np.ndarray]:
    """r_s for consecutive calendar days s (gap -> NaN, never bridged), s <= 2024-05-31."""
    days, c = panel_closes(sym)
    idx = {d: i for i, d in enumerate(days)}
    all_days = _days(days[0], days[-1])
    r = np.full(len(all_days), np.nan)
    for j, d in enumerate(all_days[1:], start=1):
        p = all_days[j - 1]
        if d in idx and p in idx:
            r[j] = np.log(c[idx[d]] / c[idx[p]])
    return all_days, r


def rv_fwd30(sym: str, t_days: list[str]) -> np.ndarray:
    """RV_fwd30(t) (decimal) for each t; NaN if any of the 30 target returns is missing."""
    days, r = daily_log_returns(sym)
    pos = {d: i for i, d in enumerate(days)}
    out = np.full(len(t_days), np.nan)
    for j, t in enumerate(t_days):
        i = pos.get(t)
        if i is None or i + H >= len(r):
            continue
        seg = r[i + 1:i + 1 + H]
        if seg.size == H and np.all(np.isfinite(seg)):
            out[j] = np.sqrt(ANN / H * np.sum(seg * seg))
    return out


def premium_frame(sym: str) -> dict[str, np.ndarray]:
    """In-memory premium series of the pre-period (never written to disk)."""
    t_days = _days(NUISANCE_FIRST_IV_DAY, NUISANCE_LAST_IV_DAY)
    ivd = dvol_daily_close(sym)
    iv = np.array([ivd.get(t, np.nan) for t in t_days])
    rv = rv_fwd30(sym, t_days)
    return {"days": np.array(t_days), "iv": iv, "rv": rv,
            "S1": 100.0 * (iv - rv), "S2": 100.0 * (iv * iv - rv * rv), "S3": np.log(iv / rv)}
