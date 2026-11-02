"""Orchestrator spot check: SD (bp) of r_pre = ln(C[07:59]/C[07:29]) by day class, BTC/ETH/pooled, 2021-03-24..2024-05-31.
NO MEAN is printed."""
import datetime as dt, numpy as np, polars as pl
S = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad"
E = dt.date(1970, 1, 1)
def rpre(sym):
    kl = pl.read_parquet(f"{S}/hf_data/raw/bybit_rest_kline1m_{sym}_2021-03-24_2024-05-31.parquet").select(["start_ms", "close"]).unique("start_ms").sort("start_ms")
    ms = kl["start_ms"].to_numpy(); c = kl["close"].to_numpy()
    assert dt.datetime.utcfromtimestamp(ms.max() / 1000).date() <= dt.date(2024, 5, 31)
    minute = (ms // 60_000) % 1440; day = ms // 86_400_000
    a = {int(d): float(x) for d, m, x in zip(day, minute, c) if m == 7 * 60 + 29}
    b = {int(d): float(x) for d, m, x in zip(day, minute, c) if m == 7 * 60 + 59}
    return {d: 1e4 * np.log(b[d] / a[d]) for d in a if d in b}
r = {s: rpre(s) for s in ("BTCUSDT", "ETHUSDT")}
days = sorted(set(r["BTCUSDT"]) & set(r["ETHUSDT"]))
excl = {(dt.date.fromisoformat(x) - E).days for x in ("2020-08-27", "2024-08-19")}
days = [d for d in days if d not in excl]
def cls(d):
    wd = (E + dt.timedelta(d)).weekday()
    return "Fri" if wd == 4 else ("MoDo" if wd < 4 else "WE")
for name in ("Fri", "MoDo", "WE", "all"):
    sel = [d for d in days if name == "all" or cls(d) == name]
    bt = np.array([r["BTCUSDT"][d] for d in sel]); et = np.array([r["ETHUSDT"][d] for d in sel]); po = (bt + et) / 2
    rho = np.corrcoef(bt, et)[0, 1]
    print(f"{name}: n={len(sel)} SD_bp BTC={bt.std(ddof=1):.1f} ETH={et.std(ddof=1):.1f} pooled={po.std(ddof=1):.1f} rho={rho:.2f}")
