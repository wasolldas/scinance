"""Orchestrator's independent null check for DEC-103 E4 (label permutation Friday <-> Mon-Thu within ISO week).
Pre-period 1-min klines only. The contrast is NEVER evaluated on the real labels: the function refuses a label
vector equal to the real one. Output: SD and upper quantiles of the permutation null (bp), per 12-month window and pooled."""
import numpy as np, polars as pl, datetime as dt, hashlib, json
k = pl.read_parquet("/home/user/scinance_work/hf_data/raw/bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet")
assert k["start_ms"].max() < 1717200000000
k = k.with_columns((pl.col("start_ms") // 86_400_000).alias("day"), ((pl.col("start_ms") % 86_400_000) // 60_000).alias("minute"))
pre = k.filter(pl.col("minute").is_in([449, 479])).pivot(on="minute", index=["symbol", "day"], values="close").rename({"449": "c0729", "479": "c0759"})
pre = pre.with_columns((1e4 * (pl.col("c0759") / pl.col("c0729")).log()).alias("r")).drop_nulls()
x = pre.pivot(on="symbol", index="day", values="r").drop_nulls().with_columns(((pl.col("BTCUSDT") + pl.col("ETHUSDT")) / 2).alias("x")).sort("day")
days = x["day"].to_numpy(); xv = x["x"].to_numpy()
dates = np.array([dt.date(1970, 1, 1) + dt.timedelta(days=int(d)) for d in days])
wd = np.array([d.weekday() for d in dates]); iso = np.array([d.isocalendar()[0] * 100 + d.isocalendar()[1] for d in dates])
keep = wd <= 4  # Mon..Fri only (no weekend)
xv, wd, iso, dates = xv[keep], wd[keep], iso[keep], dates[keep]
real = (wd == 4).astype(np.int8); real_hash = hashlib.sha256(real.tobytes()).hexdigest()
def contrast(labels):
    assert hashlib.sha256(labels.astype(np.int8).tobytes()).hexdigest() != real_hash, "refuse real labels"
    return xv[labels == 1].mean() - xv[labels == 0].mean()
rng = np.random.default_rng(2026)
weeks = np.unique(iso); idx_by_week = [np.flatnonzero(iso == w) for w in weeks]
def draw():
    lab = np.zeros(len(xv), np.int8)
    for ix in idx_by_week:
        lab[ix[rng.integers(len(ix))]] = 1
    return lab
def null_stats(mask, R=4000):
    sub_weeks = [ix for ix in idx_by_week if mask[ix].all()]
    vals = np.empty(R)
    for r in range(R):
        lab = np.zeros(len(xv), np.int8)
        for ix in sub_weeks: lab[ix[rng.integers(len(ix))]] = 1
        lab_m = lab[mask]; xs = xv[mask]
        assert hashlib.sha256(lab.astype(np.int8).tobytes()).hexdigest() != real_hash
        vals[r] = xs[lab_m == 1].mean() - xs[lab_m == 0].mean()
    nF = sum(1 for _ in sub_weeks); nP = int(mask.sum()) - nF
    return {"n_weeks": nF, "n_placebo": nP, "sd": float(vals.std(ddof=1)), "q95": float(np.quantile(vals, 0.95)), "q99": float(np.quantile(vals, 0.99)), "abs_q95": float(np.quantile(np.abs(vals), 0.95))}
out = {}
for name, a, b in (("2021-06..2022-05", dt.date(2021, 6, 1), dt.date(2022, 5, 31)), ("2022-06..2023-05", dt.date(2022, 6, 1), dt.date(2023, 5, 31)), ("2023-06..2024-05", dt.date(2023, 6, 1), dt.date(2024, 5, 31)), ("pooled", dt.date(2021, 3, 24), dt.date(2024, 5, 31))):
    mask = np.array([(a <= d <= b) for d in dates])
    out[name] = null_stats(mask)
    # analytical comparison: SD of x in window (all weekdays) / sqrt(1/nF + 1/nP)
    s = xv[mask].std(ddof=1); nF, nP = out[name]["n_weeks"], out[name]["n_placebo"]
    out[name]["se_analytic_iid_pooledSD"] = float(s * np.sqrt(1 / nF + 1 / nP)); out[name]["sd_x_weekdays"] = float(s)
print(json.dumps(out, indent=1))
