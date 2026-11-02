"""Independent check of the daily-close convention on the six pre-2024-06 days (cached files only):
panel close vs last trade before 00:00 UTC; ties at the last timestamp (distinct prices?).
No return or volatility is computed."""
import sys
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rv_common import read_cached, panel_ohlc, PRICE_LAST
DAYS = ["2021-06-15", "2022-11-09", "2023-03-15", "2023-09-15", "2023-12-15", "2024-03-15"]
for sym, psym in (("BTC", "BTCUSDT"), ("ETH", "ETHUSDT")):
    px = panel_ohlc(sym)
    for d in DAYS:
        assert d <= PRICE_LAST
        df = read_cached("bybit", "publicTrade", psym, d, d, ["payload_json"])
        t = df.select(pl.col("payload_json").str.json_path_match("$.timestamp").cast(pl.Float64).alias("ts"),
                      pl.col("payload_json").str.json_path_match("$.price").cast(pl.Float64).alias("px")).with_row_index("pos")
        last_ts = t["ts"].max()
        tie = t.filter(pl.col("ts") == last_ts)
        last_by_pos = tie.sort("pos")["px"][-1]
        print(psym, d, "panel==last(file order):", px[d][3] == last_by_pos,
              "n_tied:", tie.height, "distinct tied prices:", tie["px"].n_unique(),
              "panel high==max:", px[d][1] == t["px"].max(), "panel low==min:", px[d][2] == t["px"].min())
