"""Extend the sealed A2 kline extract by June 2024 (zone X, last month before W1): 1-min klines BTCUSDT/ETHUSDT
2024-06-01..2024-06-30 from the archive. Output: a separate raw parquet (same columns as the 2021-03-24..2024-05-31 file)
plus an EXTRACT_LOG entry. Prints only counts and sha256 (SK0); no price is printed."""
import sys, hashlib, warnings, json
sys.path.insert(0, "/home/user/scinance_work/harvest_client")
import harvest_data as hd, polars as pl
hd.configure(cache_dir="/home/user/scinance_work/hcache")
OUT = "/home/user/scinance_work/hf_data/raw/"
REF = OUT + "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet"
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
ref_cols = pl.read_parquet_schema(REF)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    df = hd.load("rest.kline1m", ["BTCUSDT", "ETHUSDT"], "2024-06-01", "2024-06-30", exchange="bybit")
warn = [str(x.message)[:200] for x in w]
print("columns loaded:", df.columns)
print("ref columns:", list(ref_cols.keys()))
k = hd.extract(df, {"start_ms": "$.startTime", "open": "$.openPrice", "high": "$.highPrice", "low": "$.lowPrice",
                    "close": "$.closePrice", "volume": "$.volume", "turnover": "$.turnover", "psym": "$.symbol"})
k = k.select(pl.col("symbol"), pl.col("psym"), pl.col("start_ms").cast(pl.Int64),
             *[pl.col(c).cast(pl.Float64) for c in ("open", "high", "low", "close", "volume", "turnover")])
assert (k["symbol"] == k["psym"]).all(), "symbol mismatch"
k = k.drop("psym").unique(subset=["symbol", "start_ms"], maintain_order=True).sort(["symbol", "start_ms"])
START_MS, END_MS = 1717200000000, 1719792000000   # 2024-06-01T00:00Z inclusive .. 2024-07-01T00:00Z exclusive (zone X ends 2024-06-30)
assert k["start_ms"].min() >= START_MS and k["start_ms"].max() < END_MS, "window seal violated"
missing = [c for c in ref_cols.keys() if c not in k.columns]
p = OUT + "bybit_kline1m_BTCUSDT_ETHUSDT_2024-06-01_2024-06-30.parquet"
k.write_parquet(p)
per = k.group_by("symbol").len().sort("symbol").rows()
log = json.load(open(OUT + "EXTRACT_LOG.json"))
log["kline_juni2024"] = {"rows": k.height, "per_symbol": per, "sha256": sha(p), "missing_cols": missing, "warnings": warn,
                         "note": "DEC-107 BE-04 / DEC-108: Vorfenster 2023-07-01..2024-06-30, Juni 2024 nachgeladen; zone X"}
json.dump(log, open(OUT + "EXTRACT_LOG.json", "w"), indent=1, default=str)
print(json.dumps({k2: v for k2, v in log["kline_juni2024"].items()}, indent=1, default=str))
