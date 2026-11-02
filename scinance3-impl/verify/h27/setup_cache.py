"""Populate the review's own harvest cache with PRE-PERIOD files only (no network, no listing).

Copies (by constructed path, date <= cutoff) from the derivation's session cache:
  catalog/partitions.parquet, raw/deribit/dvol/symbol={BTC,ETH}/date<=2024-05-01,
  raw/bybit/publicTrade (the six pre-2024-06 check days).
Blind days are never touched: the date loop stops at the cutoff.
"""
import shutil
from datetime import date, timedelta
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "h27_herleitung" / "hcache"
DST = Path(__file__).resolve().parent / "hcache"
IV_LAST = date(2024, 5, 1)

(DST / "catalog").mkdir(parents=True, exist_ok=True)
shutil.copy2(SRC / "catalog" / "partitions.parquet", DST / "catalog" / "partitions.parquet")
n = 0
for sym in ("BTC", "ETH"):
    d = date(2021, 3, 24)
    while d <= IV_LAST:
        rel = Path("raw/deribit/dvol") / f"symbol={sym}" / f"date={d.isoformat()}"
        if (SRC / rel).is_dir():
            shutil.copytree(SRC / rel, DST / rel, dirs_exist_ok=True)
            n += 1
        d += timedelta(1)
m = 0
for sym in ("BTCUSDT", "ETHUSDT"):
    for day in ("2021-06-15", "2022-11-09", "2023-03-15", "2023-09-15", "2023-12-15", "2024-03-15"):
        rel = Path("raw/bybit/publicTrade") / f"symbol={sym}" / f"date={day}"
        if (SRC / rel).is_dir():
            shutil.copytree(SRC / rel, DST / rel, dirs_exist_ok=True)
            m += 1
print("dvol files", n, "publicTrade files", m)
