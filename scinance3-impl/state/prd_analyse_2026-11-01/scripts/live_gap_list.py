# S0: Tagesabdeckung der Live-Stroeme aus dem gecachten Katalog (partitions.parquet, Stand 2026-11-01 18:46 UTC).
# Nur Zaehlungen und Datumsangaben; keine Marktwerte, keine Pfade, kein Hostname.
import pandas as pd
cat = pd.read_parquet("/home/user/scinance_work/hcache/catalog/partitions.parquet",
                      columns=["exchange", "stream", "symbol", "date", "status", "rows", "n_files"])
cat["date"] = pd.to_datetime(cat["date"])
print("Katalog: Zeilen", len(cat), "Datum max", cat["date"].max().date(), "Status-Werte", sorted(cat["status"].fillna("NA").unique()))
live = cat[cat["date"] >= "2026-06-01"]
grp = live.groupby(["exchange", "stream", "symbol"])
rows = []
for (ex, st, sy), g in grp:
    done = g[g["status"] == "DONE"]
    if done.empty: continue
    dmin, dmax = done["date"].min(), done["date"].max()
    full = pd.date_range(dmin, dmax, freq="D")
    missing = sorted(set(full.date) - set(done["date"].dt.date))
    rows.append((ex, st, sy, dmin.date(), dmax.date(), len(full), len(done), len(missing), missing))
df = pd.DataFrame(rows, columns=["exchange", "stream", "symbol", "first", "last", "span_days", "done_days", "missing", "missing_dates"])
# Nur Stroeme mit Luecken oder Live-Charakter ausgeben
show = df[(df["missing"] > 0) & (~df["symbol"].str.contains("-"))].sort_values(["exchange", "stream", "symbol"])
opt = df[df["symbol"].str.contains("-")]
print("Options-Ticker-Instrumente (Symbole mit Laufzeit/Strike) gesondert:", len(opt), "Instrumente, davon mit Luecken", int((opt["missing"]>0).sum()))
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(show.drop(columns=["missing_dates"]).to_string(index=False))
print("\n=== Fehltage je Strom (ab 2026-06-01) ===")
for _, r in show.iterrows():
    print(f"{r.exchange}/{r.stream}/{r.symbol}: {len(r.missing_dates)} Fehltage: {', '.join(str(d) for d in r.missing_dates)}")
# Gemeinsame Ausfalltage ueber alle Live-Stroeme
from collections import Counter
cnt = Counter(d for md in show["missing_dates"] for d in md)
print("\n=== Ausfalltage, die >= 5 Stroeme gemeinsam treffen ===")
for d, n in sorted(cnt.items()):
    if n >= 5: print(d, n)
print("\n=== Stroeme ohne Luecke ab 2026-06-01 (Anzahl):", int((df["missing"] == 0).sum()))
df.drop(columns=["missing_dates"]).to_csv("h21/live_coverage_2026-06-01_onwards.csv", index=False)

print("\n=== H-21 Entsperr-Bedingung: lueckenlose done_days bybit allLiquidation UND publicTrade, BTC+ETH, W1 2026-07-01..2026-09-28, W2 2026-09-29..2026-12-27 ===")
for st in ("allLiquidation", "publicTrade"):
    for sy in ("BTCUSDT", "ETHUSDT"):
        g = cat[(cat["exchange"] == "bybit") & (cat["stream"] == st) & (cat["symbol"] == sy) & (cat["status"] == "DONE")]
        have = set(g["date"].dt.date)
        for wn, (a, b) in {"W1": ("2026-07-01", "2026-09-28"), "W2": ("2026-09-29", "2026-12-27")}.items():
            full = pd.date_range(a, min(pd.Timestamp(b), cat["date"].max()), freq="D")
            miss = sorted(set(full.date) - have)
            print(f"{st}/{sy}/{wn}: Tage bis Katalogende {len(full)}, vorhanden {len(full)-len(miss)}, fehlend {len(miss)}: {', '.join(str(d) for d in miss)}")
