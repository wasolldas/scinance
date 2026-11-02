"""List non-Friday futures delivery dates (calendar extract; names and counts only)."""
import calendar, re
from collections import Counter
from datetime import date
import pyarrow.parquet as pq
CAL = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw/deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet"
MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")
t = pq.read_table(CAL, columns=["type", "instrument_name"]).to_pydict()
c = Counter(); wk = Counter()
for ty, nm in zip(t["type"], t["instrument_name"]):
    m = FUT.match(nm)
    if ty != "delivery" or not m:
        continue
    d = date(2000 + int(m.group(4)), MON[m.group(3)], int(m.group(2)))
    if not ("2020-03-25" <= str(d) <= "2026-06-30"):
        continue
    wk[d.weekday()] += 1
    if d.weekday() != 4:
        c[(str(d)[:7], d.strftime("%a"))] += 1
print("weekday histogram of futures deliveries (0=Mon):", dict(sorted(wk.items())))
print("non-Friday futures deliveries by month:", sorted(c.items())[:40], "... total", sum(c.values()))
first = {}
for ty, nm in zip(t["type"], t["instrument_name"]):
    m = FUT.match(nm)
    if ty != "delivery" or not m:
        continue
    d = date(2000 + int(m.group(4)), MON[m.group(3)], int(m.group(2)))
    if d.weekday() != 4 and str(d) <= "2026-06-30":
        k = m.group(1)
        first[k] = min(first.get(k, d), d)
print("first non-Friday futures delivery <= 2026-06-30:", {k: str(v) for k, v in first.items()})
# per day count in June 2026 window end (W2 ends 2026-06-28)
fd = {}
for ty, nm in zip(t["type"], t["instrument_name"]):
    m = FUT.match(nm)
    if ty == "delivery" and m:
        d = date(2000 + int(m.group(4)), MON[m.group(3)], int(m.group(2)))
        fd.setdefault(d, set()).add(m.group(1))
from datetime import timedelta
a, b = date(2025, 7, 1), date(2026, 6, 28)
modo = [a + timedelta(i) for i in range((b - a).days + 1) if (a + timedelta(i)).weekday() < 4]
both = [d for d in modo if fd.get(d) == {"BTC", "ETH"}]
print("W2 Mo-Do days", len(modo), "with BTC+ETH futures delivery", len(both), "first", min(both) if both else None, "last", max(both) if both else None)
anyf = [d for d in modo if fd.get(d)]
print("W2 Mo-Do days with any futures delivery", len(anyf), "W1 Mo-Do with any:", sum(1 for i in range(365) if (date(2024,7,1)+timedelta(i)).weekday()<4 and fd.get(date(2024,7,1)+timedelta(i))))
