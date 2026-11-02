"""Funding timestamps BTCUSDT/ETHUSDT for the pre-period and W1 from bybit/rest.fundingRateAll (timestamps only, no rates).
Parallel cache warm-up, then one load."""
import sys, hashlib, warnings, json, datetime as dt
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/user/scinance_work/harvest_client")
import harvest_data as hd, polars as pl
hd.configure(cache_dir="/home/user/scinance_work/hcache")
OUT = "/home/user/scinance_work/hf_data/raw/"
a, b = dt.date(2021, 3, 24), dt.date(2025, 6, 30)
def month_ranges(a, b):
    out = []; cur = a
    while cur <= b:
        nxt = (cur.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
        out.append((cur, min(nxt - dt.timedelta(days=1), b))); cur = nxt
    return out
def one(rng):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try: hd.load("rest.fundingRateAll", ["ALL"], rng[0], rng[1], exchange="bybit", columns=["symbol"])
        except Exception as e: return f"{rng}: {type(e).__name__}: {str(e)[:80]}"
with ThreadPoolExecutor(8) as ex: errs = [e for e in ex.map(one, month_ranges(a, b)) if e]
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    f = hd.load("rest.fundingRateAll", ["ALL"], a, b, exchange="bybit")
    warn = [str(x.message)[:200] for x in w]
f = hd.extract(f, {"psym": "$.symbol", "fts": "$.fundingRateTimestamp"})
f = f.filter(pl.col("psym").is_in(["BTCUSDT", "ETHUSDT"])).select(pl.col("psym").alias("symbol"), pl.col("fts").cast(pl.Int64)).unique(maintain_order=True).sort(["symbol", "fts"])
assert f["fts"].min() >= 1616544000000 and f["fts"].max() < 1751328000000 + 86_400_000  # <= 2025-07-01
p = OUT + "bybit_funding_timestamps_BTCUSDT_ETHUSDT_2021-03-24_2025-06-30.parquet"; f.write_parquet(p)
sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
log = json.load(open(OUT + "EXTRACT_LOG.json"))
log["funding_pre_w1"] = {"rows": f.height, "per_symbol": f.group_by("symbol").len().sort("symbol").rows(), "sha256": sha, "warm_errors": errs[:5], "warnings": warn[:3]}
json.dump(log, open(OUT + "EXTRACT_LOG.json", "w"), indent=1, default=str)
print(json.dumps(log["funding_pre_w1"], indent=1, default=str))
