"""Orchestrator spot check of review B-7: non-Friday Deribit futures deliveries (calendar extract, <= 2026-06-30).
Names/types/dates only; no prices."""
import calendar, re
from datetime import date, timedelta
import pyarrow.parquet as pq
CAL = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw/deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet"
t = pq.read_table(CAL, columns=["type", "instrument_name"]).to_pydict()
MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")
days = {}
for ty, nm in zip(t["type"], t["instrument_name"]):
    m = FUT.match(nm)
    if ty != "delivery" or not m:
        continue
    d = date(2000 + int(m.group(4)), MON[m.group(3)], int(m.group(2)))
    if str(d) > "2026-06-30":
        continue
    days.setdefault(d, set()).add(m.group(1))
nonfri = sorted(d for d in days if d.weekday() != 4 and str(d) >= "2020-03-25")
print("first non-Friday futures delivery per ccy:",
      {c: str(min(d for d in nonfri if c in days[d])) for c in ("BTC", "ETH")})
print("non-Friday futures delivery days 2020-03-25..2026-06-30:", len(nonfri),
      "deliveries:", sum(len(days[d]) for d in nonfri))
def modo(a, b):
    return [a + timedelta(i) for i in range((b - a).days + 1) if (a + timedelta(i)).weekday() < 4]
for name, a, b in (("W1", date(2024, 7, 1), date(2025, 6, 30)), ("W2", date(2025, 7, 1), date(2026, 6, 28))):
    md = modo(a, b)
    anyf = [d for d in md if d in days]
    both = [d for d in md if days.get(d) == {"BTC", "ETH"}]
    print(name, "Mo-Do days", len(md), "with any futures delivery", len(anyf), "both ccy", len(both),
          "first", str(min(anyf)) if anyf else None)
