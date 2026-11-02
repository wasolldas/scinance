"""Sealed A2 extracts from the Data-Harvest archive (orchestrator, 2026-10-31).
Returns only in the pre-period 2021-03-24..2024-05-31 (BTCUSDT/ETHUSDT 1-min closes);
settlement calendar fields (type, instrument_name, timestamp, position) <= 2026-06-30 - no price fields;
funding timestamps BTCUSDT/ETHUSDT 2025-07-01..2026-06-28 - no rates.
No mean or sign of any return is computed here."""
import sys, hashlib, warnings, json
sys.path.insert(0, "/home/user/scinance_work/harvest_client")
import harvest_data as hd, polars as pl
hd.configure(cache_dir="/home/user/scinance_work/hcache")
OUT = "/home/user/scinance_work/hf_data/raw/"
log = {}

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

# 1) 1-min klines, pre-period only
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    df = hd.load("rest.kline1m", ["BTCUSDT", "ETHUSDT"], "2021-03-24", "2024-05-31", exchange="bybit")
    log["kline_warnings"] = [str(x.message)[:200] for x in w]
k = hd.extract(df, {"start_ms": "$.startTime", "open": "$.openPrice", "high": "$.highPrice", "low": "$.lowPrice",
                    "close": "$.closePrice", "volume": "$.volume", "turnover": "$.turnover", "psym": "$.symbol"})
k = k.select(pl.col("symbol"), pl.col("psym"), pl.col("start_ms").cast(pl.Int64),
             *[pl.col(c).cast(pl.Float64) for c in ("open", "high", "low", "close", "volume", "turnover")])
assert (k["symbol"] == k["psym"]).all(), "symbol mismatch"
k = k.drop("psym").unique(subset=["symbol", "start_ms"], maintain_order=True).sort(["symbol", "start_ms"])
END_MS = 1717200000000  # 2024-06-01T00:00:00Z exclusive
START_MS = 1616544000000  # 2021-03-24T00:00:00Z
assert k["start_ms"].max() < END_MS and k["start_ms"].min() >= START_MS, "pre-period seal violated"
p = OUT + "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet"; k.write_parquet(p)
log["kline"] = {"rows": k.height, "per_symbol": k.group_by("symbol").len().sort("symbol").rows(), "sha256": sha(p)}

# 2) settlement calendar <= 2026-06-30, four fields only
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    s = hd.load("rest.settlements", ["BTC", "ETH"], "2017-05-25", "2026-06-30", exchange="deribit")
    log["settle_warnings"] = len(w)
s = hd.extract(s, {"type": "$.type", "instrument_name": "$.instrument_name", "timestamp": "$.timestamp",
                   "position": "$.position"})
s = s.select(pl.col("symbol").alias("ccy"), "type", "instrument_name", pl.col("timestamp").cast(pl.Int64),
             pl.col("position").cast(pl.Float64)).unique(maintain_order=True).sort(["ccy", "timestamp", "instrument_name"])
assert s["timestamp"].max() < 1782864000000, "settlement seal: timestamp after 2026-06-30"  # 2026-07-01T00:00Z  # 2026-07-01T00:00Z
p = OUT + "deribit_settlements_CALENDAR_fields4_2017-05-25_2026-06-30.parquet"; s.write_parquet(p)
log["settlements"] = {"rows": s.height, "types": s.group_by("type").len().rows(), "sha256": sha(p)}

# 3) funding timestamps W2 only (no rates)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    f = hd.load("rest.fundingRate", ["BTCUSDT", "ETHUSDT"], "2025-07-01", "2026-06-28", exchange="bybit")
    log["funding_warnings"] = [str(x.message)[:200] for x in w]
f = hd.extract(f, {"fts": "$.fundingRateTimestamp", "psym": "$.symbol"})
f = f.select(pl.col("symbol"), pl.col("fts").cast(pl.Int64)).unique(maintain_order=True).sort(["symbol", "fts"])
p = OUT + "bybit_funding_timestamps_BTCUSDT_ETHUSDT_2025-07-01_2026-06-28.parquet"; f.write_parquet(p)
log["funding"] = {"rows": f.height, "per_symbol": f.group_by("symbol").len().sort("symbol").rows(), "sha256": sha(p)}
json.dump(log, open(OUT + "EXTRACT_LOG.json", "w"), indent=1, default=str)
print(json.dumps(log, indent=1, default=str))
