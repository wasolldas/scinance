"""Fast variant of extract_a2.py: pre-warm the local cache with 8 parallel readers over disjoint date ranges,
then build the same sealed extracts. Same seals: calendar fields only (no prices), funding timestamps only."""
import sys, hashlib, warnings, json, datetime as dt
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/user/scinance_work/harvest_client")
import harvest_data as hd, polars as pl
hd.configure(cache_dir="/home/user/scinance_work/hcache")
OUT = "/home/user/scinance_work/hf_data/raw/"
log = {}
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def month_ranges(a, b):
    out = []; cur = a
    while cur <= b:
        nxt = (cur.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
        out.append((cur, min(nxt - dt.timedelta(days=1), b))); cur = nxt
    return out
def warm(stream, symbols, a, b, exchange):
    def one(rng):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try: hd.load(stream, symbols, rng[0], rng[1], exchange=exchange, columns=["symbol"])
            except Exception as e: return f"{rng}: {type(e).__name__}"
        return None
    with ThreadPoolExecutor(8) as ex: errs = [e for e in ex.map(one, month_ranges(a, b)) if e]
    return errs
log["warm_settlements_errors"] = warm("rest.settlements", ["BTC", "ETH"], dt.date(2017, 5, 25), dt.date(2026, 6, 30), "deribit")
log["warm_funding_errors"] = warm("rest.fundingRate", ["BTCUSDT", "ETHUSDT"], dt.date(2025, 7, 1), dt.date(2026, 6, 28), "bybit")
# settlements calendar (4 fields)
cat = hd.catalog()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    s = hd.load("rest.settlements", ["BTC", "ETH"], "2017-05-25", "2026-06-30", exchange="deribit")
    log["settle_warnings"] = [str(x.message)[:200] for x in w]
exp_rows = cat.filter((pl.col("exchange") == "deribit") & (pl.col("stream") == "rest.settlements") & pl.col("symbol").is_in(["BTC", "ETH"]) & (pl.col("date") >= "2017-05-25") & (pl.col("date") <= "2026-06-30"))["rows"].sum()
log["settlements_rows_loaded_vs_catalog"] = [s.height, int(exp_rows)]
s = hd.extract(s, {"type": "$.type", "instrument_name": "$.instrument_name", "timestamp": "$.timestamp", "position": "$.position"})
s = s.select(pl.col("symbol").alias("ccy"), "type", "instrument_name", pl.col("timestamp").cast(pl.Int64), pl.col("position").cast(pl.Float64)).unique(maintain_order=True).sort(["ccy", "timestamp", "instrument_name"])
assert s["timestamp"].max() < 1782864000000, "settlement seal: timestamp after 2026-06-30"  # 2026-07-01T00:00Z
p = OUT + "deribit_settlements_CALENDAR_fields4_2017-05-25_2026-06-30.parquet"; s.write_parquet(p)
log["settlements"] = {"rows": s.height, "types": s.group_by("type").len().rows(), "sha256": sha(p)}
# funding timestamps
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    f = hd.load("rest.fundingRate", ["BTCUSDT", "ETHUSDT"], "2025-07-01", "2026-06-28", exchange="bybit")
    log["funding_warnings"] = [str(x.message)[:200] for x in w]
f = hd.extract(f, {"fts": "$.fundingRateTimestamp"})
f = f.select(pl.col("symbol"), pl.col("fts").cast(pl.Int64)).unique(maintain_order=True).sort(["symbol", "fts"])
p = OUT + "bybit_funding_timestamps_BTCUSDT_ETHUSDT_2025-07-01_2026-06-28.parquet"; f.write_parquet(p)
log["funding"] = {"rows": f.height, "per_symbol": f.group_by("symbol").len().sort("symbol").rows(), "sha256": sha(p)}
# kline file already written and verified by the orchestrator (1165 days x 1440 rows per symbol)
kp = OUT + "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet"
log["kline"] = {"sha256": sha(kp), "note": "written by extract_a2.py; verified 1165 days x 1440 rows per symbol, 2021-03-24..2024-05-31"}
json.dump(log, open(OUT + "EXTRACT_LOG.json", "w"), indent=1, default=str)
print(json.dumps(log, indent=1, default=str))
