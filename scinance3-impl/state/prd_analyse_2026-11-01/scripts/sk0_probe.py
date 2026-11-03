# SK0-Inhaltsproben: nur Parquet-Metadaten (Schema, Zeilenzahl, Row-Groups) je eines Stichtags; keine Werte, kein Listing.
import sys, pandas as pd, pyarrow.parquet as pq
sys.path.insert(0, "/home/user/scinance_work/harvest_client")
import harvest_data as hd
hd.configure(cache_dir="/home/user/scinance_work/hcache")
cat = pd.read_parquet("/home/user/scinance_work/hcache/catalog/partitions.parquet", columns=["exchange","stream","symbol","date","status","rows","files","bytes"])
c = hd._c()
def probe(ex, st, sy, date_max, date_min=None):
    g = cat[(cat.exchange==ex)&(cat.stream==st)&(cat.symbol==sy)&(cat.status=="DONE")&(cat.date<=date_max)]
    if date_min: g = g[g.date>=date_min]
    g = g.sort_values("date")
    if g.empty: print(ex, st, sy, "keine Partition"); return
    r = g.iloc[-1]; key = r["files"][0]
    pf = pq.ParquetFile(c.fs.open_input_file(f"{c.bucket}/{key}"))
    md = pf.metadata
    print(f"== {ex}/{st}/{sy} Stichtag {r['date']} | Partitionen bis {date_max}: {len(g)} | Katalog rows {r['rows']} bytes {r['bytes']} | Parquet rows {md.num_rows}, row_groups {md.num_row_groups}, Spalten {md.num_columns}")
    print("   Schema:", ", ".join(f"{f.name}:{f.type}" for f in pf.schema_arrow)[:900])
probe("tardis", "options_chain", "OPTIONS", "2026-06-01")
probe("deribit", "publicTrade", "BTC", "2026-06-30")
probe("deribit", "publicTrade", "ETH", "2026-06-30")
probe("bybit", "allLiquidation", "BTCUSDT", "2026-10-31")
probe("bybit", "rest.deliveryPrice", "ALL", "2026-09-25")
# IK-12 SK0: Zeilen je Tag allLiquidation (Katalog), Quantile
g = cat[(cat.exchange=="bybit")&(cat.stream=="allLiquidation")&(cat.status=="DONE")]
for sy, gg in g.groupby("symbol"):
    q = gg["rows"].describe(percentiles=[.1,.5,.9])
    print(f"IK-12 SK0 {sy}: Tage {int(q['count'])}, Zeilen/Tag q10 {q['10%']:.0f} q50 {q['50%']:.0f} q90 {q['90%']:.0f} max {q['max']:.0f}, Summe {int(gg['rows'].sum())}")
