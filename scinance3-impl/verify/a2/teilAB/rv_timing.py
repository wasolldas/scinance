"""Seconds of option delivery timestamps after 08:00:00 UTC (calendar extract, <= 2026-06-30)."""
import re
import numpy as np
import pyarrow.parquet as pq
CAL = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw/deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet"
OPT = re.compile(r"^(BTC|ETH)-\d{1,2}[A-Z]{3}\d{2}-[0-9d.]+-[CP]$")
t = pq.read_table(CAL, columns=["type", "instrument_name", "timestamp_ms"]).to_pydict()
ms = np.array([m for ty, nm, m in zip(t["type"], t["instrument_name"], t["timestamp_ms"]) if ty == "delivery" and OPT.match(nm)])
day = ms // 86_400_000
lo = (np.datetime64("2020-03-25") - np.datetime64("1970-01-01")).astype(int)
hi = (np.datetime64("2026-06-30") - np.datetime64("1970-01-01")).astype(int)
nlo = (np.datetime64("2021-03-24") - np.datetime64("1970-01-01")).astype(int)
nhi = (np.datetime64("2024-05-31") - np.datetime64("1970-01-01")).astype(int)
for lab, m in (("2020-03-25..2026-06-30", (day >= lo) & (day <= hi)), ("2021-03-24..2024-05-31", (day >= nlo) & (day <= nhi))):
    s = (ms[m] % 86_400_000) / 1000.0 - 28800.0
    print(lab, "n", m.sum(), "q50 %.3f q99 %.3f q999 %.3f max %.1f" % tuple(np.quantile(s, [0.5, 0.99, 0.999, 1.0])),
          "before0800", int((s < 0).sum()), ">60s", int((s > 60).sum()), "hour-of-day set", sorted(set((ms[m] % 86_400_000) // 3_600_000)))
