"""H-27 review: independent loaders and blindness guards (own code, not the derivation's).

Guards (loud fail):
  * prices: every panel row with UTC day > 2024-05-31 is dropped at READ time, before any
    return, range or volatility is formed (assert afterwards);
  * DVOL: only IV days 2021-03-24..2024-05-01 are requested from the client (hd.load range);
  * outputs: ``guard_out`` refuses any key that names a mean/median/level of the premium or of
    DVOL (pre-period RV levels are allowed, they are not outcome information).
Independent choices vs. the derivation: DVOL hour taken from ``ts_exchange_ms`` (not the payload
timestamp), returns and sums via calendar-indexed arrays and cumulative sums.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent / "panel" / "panel_1d"
PRICE_LAST = "2024-05-31"
IV_FIRST, IV_LAST = "2021-03-24", "2024-05-01"
ANN, H = 365.0, 30
PSYM = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
LABEL = ("Review-Nuisance 2021-03-24..2024-05-31 (IV-Tage bis 2024-05-01, Preise bis 2024-05-31): "
         "nur Streuung, Autokorrelation, Verhaeltnisse; kein Praemienmittel, kein DVOL-Mittel.")

_BAD = re.compile(r"(^|_)(mean|avg|median|mittel)(_|$)|prem.*(mean|mittel)|dvol.*(mean|level)|iv_(mean|level)",
                  re.I)


def guard_out(d):
    if isinstance(d, dict):
        for k, v in d.items():
            if _BAD.search(str(k)):
                raise RuntimeError(f"blindness guard: key {k!r} refused")
            guard_out(v)
    elif isinstance(d, (list, tuple)):
        for v in d:
            guard_out(v)
    return d


def days(lo: str, hi: str) -> list[str]:
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(a + timedelta(i)).isoformat() for i in range((b - a).days + 1)]


def _catalog_rows(exchange: str, stream: str, sym: str, lo: str, hi: str) -> pl.DataFrame:
    """Catalog rows only (the catalog copy of the derivation's single 2026-10-17 download)."""
    cat = pl.read_parquet(HERE / "hcache" / "catalog" / "partitions.parquet")
    return cat.filter((pl.col("exchange") == exchange) & (pl.col("stream") == stream)
                      & (pl.col("symbol") == sym) & (pl.col("date") >= lo)
                      & (pl.col("date") <= hi)).sort("date")


def read_cached(exchange: str, stream: str, sym: str, lo: str, hi: str, columns: list[str]) -> pl.DataFrame:
    """Offline equivalent of hd.load(cache=True): reads the session-cache copies of the catalog
    keys; NO network request (the backfill rows are not flagged compacted, hd.load would issue one
    HEAD request per partition on the shared endpoint).  Missing local file or size -> loud fail;
    days without a catalog row are reported by the caller (never filled)."""
    rows = _catalog_rows(exchange, stream, sym, lo, hi)
    frames = []
    for r in rows.iter_rows(named=True):
        for key, size in zip(r["files"], r["sizes"]):
            f = HERE / "hcache" / key
            if not f.exists() or f.stat().st_size != size:
                raise FileNotFoundError(f"not in review cache: {key}")
            frames.append(pl.from_arrow(pq.ParquetFile(f).read(columns=columns)))
    return pl.concat(frames, how="vertical_relaxed")


_IV_CACHE: dict[str, dict[str, float]] = {}


def dvol_close(sym: str) -> dict[str, float]:
    """IV(t) (decimal) = close of the hourly candle starting 23:00 UTC of day t, t <= 2024-05-01."""
    if sym in _IV_CACHE:
        return _IV_CACHE[sym]
    df = read_cached("deribit", "dvol", sym, IV_FIRST, IV_LAST, ["ts_exchange_ms", "payload_json"])
    out: dict[str, float] = {}
    for ms, pj in zip(df["ts_exchange_ms"].to_list(), df["payload_json"].to_list()):
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        d = dt.date().isoformat()
        if d > IV_LAST:
            raise RuntimeError("blindness: DVOL day beyond IV_LAST")
        if dt.hour == 23:
            if d in out:
                raise RuntimeError(f"duplicate 23h candle {sym} {d}")
            out[d] = float(json.loads(pj)["close"]) / 100.0
    _IV_CACHE[sym] = out
    return out


def panel_ohlc(sym: str) -> dict[str, tuple[float, float, float, float]]:
    """Bybit 1D candles (open, high, low, close) by UTC day, truncated at READ time."""
    rows: dict[str, tuple[float, float, float, float]] = {}
    for state in ("frozen", "open"):
        base = PANEL / state / "source=bybit" / "category=linear" / f"symbol={PSYM[sym]}"
        for yr in ("2021", "2022", "2023", "2024"):
            f = base / f"year={yr}" / "part.parquet"
            if not f.exists():
                continue
            t = pq.ParquetFile(f).read(columns=["start_ms", "open", "high", "low", "close"]).to_pydict()
            for i, ms in enumerate(t["start_ms"]):
                d = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()
                if d > PRICE_LAST:
                    continue                       # dropped before anything is computed
                rows[d] = (t["open"][i], t["high"][i], t["low"][i], t["close"][i])
    if max(rows) > PRICE_LAST:
        raise RuntimeError("truncation failed")
    return rows


def daily_vars(sym: str) -> tuple[list[str], dict[str, np.ndarray]]:
    """Per calendar day s (from the first panel day to 2024-05-31): daily variance proxies
    cc = ln(C_s/C_{s-1})^2, pk = ln(H/L)^2/(4 ln 2), gk = 0.5 ln(H/L)^2 - (2 ln2 - 1) ln(C/O)^2,
    rs = ln(H/C) ln(H/O) + ln(L/C) ln(L/O); NaN where a candle is missing (never bridged)."""
    px = panel_ohlc(sym)
    ds = days(min(px), PRICE_LAST)
    n = len(ds)
    out = {k: np.full(n, np.nan) for k in ("cc", "pk", "gk", "rs", "r", "co_gap")}
    for i, d in enumerate(ds):
        if d not in px:
            continue
        o, h, l, c = px[d]
        hl, co = np.log(h / l), np.log(c / o)
        out["pk"][i] = hl * hl / (4 * np.log(2))
        out["gk"][i] = 0.5 * hl * hl - (2 * np.log(2) - 1) * co * co
        out["rs"][i] = np.log(h / c) * np.log(h / o) + np.log(l / c) * np.log(l / o)
        if i > 0 and ds[i - 1] in px:
            cprev = px[ds[i - 1]][3]
            out["r"][i] = np.log(c / cprev)
            out["cc"][i] = out["r"][i] ** 2
            out["co_gap"][i] = np.log(o / cprev)   # open vs previous close (24/7: ~0)
    return ds, out


def rv_fwd(ds: list[str], v: np.ndarray, t_days: list[str]) -> np.ndarray:
    """RV_fwd30(t) = sqrt(ANN/H * sum_{s=t+1..t+30} v_s); NaN if any v_s missing."""
    pos = {d: i for i, d in enumerate(ds)}
    ok = np.isfinite(v)
    cs = np.concatenate([[0.0], np.cumsum(np.where(ok, v, 0.0))])
    cn = np.concatenate([[0], np.cumsum(ok.astype(int))])
    out = np.full(len(t_days), np.nan)
    for j, t in enumerate(t_days):
        i = pos.get(t)
        if i is None or i + H >= len(v):
            continue
        if ds[i + H] > PRICE_LAST:
            raise RuntimeError("blindness: RV target beyond PRICE_LAST")
        if cn[i + H + 1] - cn[i + 1] == H:
            out[j] = np.sqrt(ANN / H * (cs[i + H + 1] - cs[i + 1]))
    return out


def premium(sym: str, est: str = "cc") -> dict[str, np.ndarray]:
    """In-memory premium series (never written); est = RV estimator of the daily variance."""
    t = days(IV_FIRST, IV_LAST)
    ivd = dvol_close(sym)
    iv = np.array([ivd.get(d, np.nan) for d in t])
    ds, dv = daily_vars(sym)
    rv = rv_fwd(ds, dv[est], t)
    return {"t": t, "iv": iv, "rv": rv, "S1": 100 * (iv - rv), "S2": 100 * (iv ** 2 - rv ** 2),
            "S3": np.log(iv / rv)}
