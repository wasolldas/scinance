"""Orchestrator spot check: P3fix series in the DEC-103 form (slot [15:30,16:00), Mon-Fri, excluding month-end Fridays),
pre-period 2021-03-24..2024-05-31. Only SD, N, Bartlett-type variance factor and the same-day correlation with r_pre on
week-Fridays (dependence measure). No mean of any return is printed."""
import numpy as np, polars as pl, datetime as dt, calendar
k = pl.read_parquet("/home/user/scinance_work/hf_data/raw/bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet")
assert k["start_ms"].max() < 1717200000000
k = k.with_columns((pl.col("start_ms") // 86_400_000).alias("day"), ((pl.col("start_ms") % 86_400_000) // 60_000).alias("minute"))
def slot(m0, m1, name):
    s = k.filter(pl.col("minute").is_in([m0 - 1, m1 - 1])).pivot(on="minute", index=["symbol", "day"], values="close")
    s = s.with_columns((1e4 * (pl.col(str(m1 - 1)) / pl.col(str(m0 - 1))).log()).alias(name)).drop_nulls()
    return s.pivot(on="symbol", index="day", values=name).drop_nulls().with_columns(((pl.col("BTCUSDT") + pl.col("ETHUSDT")) / 2).alias(name)).select("day", name)
pre = slot(450, 480, "r_pre")      # [07:30, 08:00): closes at minute 449 and 479
fix = slot(930, 960, "r_fix")      # [15:30, 16:00): closes at minute 929 and 959
df = pre.join(fix, on="day").sort("day")
dates = [dt.date(1970, 1, 1) + dt.timedelta(days=int(d)) for d in df["day"]]
wd = np.array([d.weekday() for d in dates])
def last_friday(d):
    last = calendar.monthrange(d.year, d.month)[1]
    for dd in range(last, last - 7, -1):
        if dt.date(d.year, d.month, dd).weekday() == 4: return dt.date(d.year, d.month, dd)
monthend_fri = np.array([d == last_friday(d) for d in dates])
m = (wd <= 4) & ~monthend_fri
rf = df["r_fix"].to_numpy()[m]
print("P3fix (Mo-Fr ohne Monatsend-Freitage): N", int(m.sum()), "SD", round(rf.std(ddof=1), 2))
rf_all = df["r_fix"].to_numpy(); print("P3fix alle Tage: N", len(rf_all), "SD", round(rf_all.std(ddof=1), 2))
# variance factor via batch means (block 13) on the Mo-Fr series, max over alignments
def c_batch(x, b=13):
    best = 0.0
    for off in range(b):
        y = x[off:]; n = (len(y) // b) * b
        if n < 2 * b: continue
        bm = y[:n].reshape(-1, b).mean(axis=1)
        c = b * bm.var(ddof=1) / y[:n].var(ddof=1); best = max(best, c)
    return best
print("c_batch(13) P3fix:", round(c_batch(rf), 3))
# same-day correlation r_pre vs r_fix on week-Fridays (Fridays that are not month-end)
wf = (wd == 4) & ~monthend_fri
print("rho(r_pre, r_fix) Wochen-Freitage:", round(np.corrcoef(df["r_pre"].to_numpy()[wf], df["r_fix"].to_numpy()[wf])[0, 1], 3), "n", int(wf.sum()))
# SE P3fix for W1 structure: N_E 52, N_P3fix 248; SD_E 43.83, c_E 1.149; SD_P 61.4, c_P 1.168
se_E = 43.83 * np.sqrt(1.149 / 52); se_P = rf.std(ddof=1) * np.sqrt(max(1.0, c_batch(rf)) / 248)
rho = np.corrcoef(df["r_pre"].to_numpy()[wf], df["r_fix"].to_numpy()[wf])[0, 1]
cov_term = -2 * rho * se_E * se_P * (40 / 52) * (40 / 248) * (52 * 248) / (52 * 248)  # rough: shared-day covariance share
print("SE_E", round(se_E, 3), "SE_P3fix", round(se_P, 3), "SE contrast ohne Kovarianz", round(np.hypot(se_E, se_P), 3))
