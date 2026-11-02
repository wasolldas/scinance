"""Orchestrator spot check (independent of the agent): SD and c of S1 = 100*(IV - RV_fwd30) for RV from 1-min (raw) and
close-to-close, BTC, IV days 2021-03-24..2024-05-01, prices <= 2024-05-31.  NO MEAN of the premium is printed."""
import json, datetime as dt, numpy as np, polars as pl
S = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad"
E = dt.date(1970, 1, 1)
kl = pl.read_parquet(f"{S}/hf_data/raw/bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet").select(["start_ms", "close"]).unique("start_ms").sort("start_ms")
assert E + dt.timedelta(int(kl["start_ms"].max() // 86_400_000)) <= dt.date(2024, 5, 31), "price day after 2024-05-31"
ms = kl["start_ms"].to_numpy(); c = kl["close"].to_numpy()
dnum = ms // 86_400_000
days = np.unique(dnum)
print("1-min rows", len(c), "days", len(days), "rows/day min", np.bincount((dnum - dnum.min()).astype(int)).min())
# daily RV (raw 1-min, overnight link to previous day's last close) and cc
lr = np.diff(np.log(c))                      # return of bar i (from bar i-1 close to bar i close)
day_of_ret = dnum[1:]
rv_1m = {int(d): float(np.sum(lr[day_of_ret == d] ** 2)) for d in days[1:]}
last_close = {int(d): float(c[dnum == d][-1]) for d in days}
rv_cc = {int(d): float(np.log(last_close[int(d)] / last_close[int(dp)]) ** 2) for dp, d in zip(days[:-1], days[1:])}
# IV: DVOL hourly candle starting 23:00 UTC
dv = pl.read_parquet(f"{S}/hf_data/raw/deribit_dvol_raw_2021-03-24_2024-05-31.parquet").filter(pl.col("symbol") == "BTC")
iv = {}
for p in dv["payload_json"].to_list():
    o = json.loads(p); t = dt.datetime.fromtimestamp(o["timestamp"] / 1000, tz=dt.timezone.utc)
    if t.hour == 23:
        iv[(t.date() - E).days] = float(o["close"]) / 100.0
def series(rv):
    out = []
    for d in range((dt.date(2021, 3, 24) - E).days, (dt.date(2024, 5, 1) - E).days + 1):
        fwd = [rv.get(d + k) for k in range(1, 31)]
        if d in iv and all(x is not None for x in fwd):
            out.append(100.0 * (iv[d] - np.sqrt(365.0 / 30.0 * sum(fwd))))
    return np.asarray(out)
def bartlett_c(x, B):
    x = x - x.mean(); n = len(x); g0 = np.dot(x, x) / n; s = 1.0
    for k in range(1, B + 1):
        s += 2 * (1 - k / (B + 1)) * np.dot(x[:-k], x[k:]) / n / g0
    return s
def batch_c(x, L):
    n = len(x) // L; m = x[:n * L].reshape(n, L).mean(axis=1)
    return L * m.var(ddof=1) / x.var(ddof=1)
for name, rv in [("cc", rv_cc), ("1min_raw", rv_1m)]:
    s1 = series(rv)
    acf = lambda k: np.corrcoef(s1[:-k], s1[k:])[0, 1]
    print(f"{name}: n={len(s1)} SD={s1.std(ddof=1):.3f} ACF1/30/120={acf(1):.3f}/{acf(30):.3f}/{acf(120):.3f} "
          f"Bartlett60/90/120={bartlett_c(s1,60):.1f}/{bartlett_c(s1,90):.1f}/{bartlett_c(s1,120):.1f} "
          f"BM60/90/120={batch_c(s1,60):.1f}/{batch_c(s1,90):.1f}/{batch_c(s1,120):.1f}")
print("rms RV30 (allowed level): cc", np.sqrt(np.mean([(np.sqrt(365/30*sum(rv_cc[d+k] for k in range(1,31))))**2 for d in range((dt.date(2021,3,24)-E).days,(dt.date(2024,5,1)-E).days+1) if all((d+k) in rv_cc for k in range(1,31))]))*100)
