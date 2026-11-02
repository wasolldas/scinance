"""Orchestrator's independent recomputation of the decisive A1 feasibility numbers.
Reads raw parquet directly (no repo loader). Outcome side only before 2024-07-01: prints
dispersion (SD, rho1) and the funding-leg persistence ratio, never a return mean."""
import sys, glob, os, re
from datetime import date, timedelta
import numpy as np, pandas as pd, pyarrow.parquet as pq

base, dbase = sys.argv[1], sys.argv[2]
LAST = pd.Timestamp("2026-06-28")
cols = {}
for tree, root in (("s", base), ("d", dbase)):
    for f in glob.glob(os.path.join(root, "*", "source=bybit", "category=linear", "symbol=*", "year=*", "part.parquet")):
        sym = re.search(r"symbol=([^/]+)", f).group(1)
        t = pq.read_table(f, columns=["start_ms", "close", "funding_n", "funding_sum"]).to_pandas()
        if t.empty:
            continue
        t["col"] = sym + ("#d" if tree == "d" else "")
        cols.setdefault(t["col"].iat[0], []).append(t)
frames = [pd.concat(v) for v in cols.values()]
df = pd.concat(frames, ignore_index=True)
df["day"] = pd.to_datetime(df["start_ms"], unit="ms").dt.normalize()
df = df[df["day"] <= LAST].drop_duplicates(["col", "day"])
df["wk"] = df["day"] - pd.to_timedelta(df["day"].dt.weekday, unit="D")
hasf = (df["funding_n"].fillna(0) > 0) & df["funding_sum"].notna()
df["ex"] = np.where(hasf, df["funding_sum"].fillna(0) - 0.0003, 0.0)
df["fs"] = np.where(hasf, df["funding_sum"].fillna(0), 0.0)
first = df.groupby("col")["day"].min(); last = df.groupby("col")["day"].max()
key = df.pivot_table(index="wk", columns="col", values="ex", aggfunc="sum").fillna(0.0)
fsum = df.pivot_table(index="wk", columns="col", values="fs", aggfunc="sum").fillna(0.0)
dfs = df.sort_values("day")
wclose = dfs.groupby(["wk", "col"])["close"].last().unstack()
weeks = key.index
key = key.reindex(columns=wclose.columns, fill_value=0.0); fsum = fsum.reindex(columns=wclose.columns, fill_value=0.0)
F = first.reindex(wclose.columns); L = last.reindex(wclose.columns)
print("columns", len(wclose.columns), "weeks", len(weeks))

def universe(t):
    w = weeks[t]
    return ((F <= w - pd.Timedelta(days=56)) & (L >= min(w + pd.Timedelta(days=7), LAST)) & wclose.loc[w].notna()).values

def d1(krow, m):
    idx = np.flatnonzero(m); k = max(1, idx.size // 10)
    return idx[np.argsort(krow[idx], kind="mergesort")[:k]]

def spread(t):
    m = universe(t); kr = key.iloc[t].values
    D = d1(kr, m)
    return kr[m].mean() - kr[D].mean(), m.sum()

for name, a, b in (("W1", "2024-07-01", "2025-06-30"), ("W2", "2025-07-01", "2026-06-30")):
    ts = [t for t, w in enumerate(weeks) if pd.Timestamp(a) <= w and w + pd.Timedelta(days=7) <= pd.Timestamp(b)]
    sp = [spread(t) for t in ts]
    s = np.array([x[0] for x in sp]) * 1e4; K = np.array([x[1] for x in sp])
    print(name, "n", len(ts), "spread mean/median bp", round(s.mean(), 1), round(np.median(s), 1), "K min/med/max", K.min(), int(np.median(K)), K.max())

# nuisance: formation 2022-04-18..2024-06-17, K>=117, holding week ends <= 2024-06-30
xs, gs, ss, ps = [], [], [], []
for t in range(len(weeks) - 1):
    w = weeks[t]
    if not (pd.Timestamp("2022-04-18") <= w and weeks[t + 1] + pd.Timedelta(days=6) <= pd.Timestamp("2024-06-30")):
        continue
    m = universe(t)
    if m.sum() < 117:
        continue
    kr = key.iloc[t].values; D = d1(kr, m)
    c0 = wclose.iloc[t].values
    # holding-week close: last close in week t+1 (delisted inside the week -> its last close)
    c1 = wclose.iloc[t + 1].values
    R = c1 / c0 - 1.0
    Rm = np.where(np.isnan(R), 0.0, R)  # members always have a bar in t+1 by construction
    fl = fsum.iloc[t + 1].values
    p = Rm[D].mean() - Rm[m].mean(); g = fl[m].mean() - fl[D].mean()
    xs.append(p + g); gs.append(g); ss.append(kr[m].mean() - kr[D].mean()); ps.append(p)
x = np.array(xs) * 1e4
r1 = np.corrcoef(x[:-1], x[1:])[0, 1]
print("nuisance weeks", len(x), "SD x bp", round(x.std(ddof=1), 1), "SD p", round(np.std(np.array(ps) * 1e4, ddof=1), 1),
      "SD g", round(np.std(np.array(gs) * 1e4, ddof=1), 1), "rho1 x", round(r1, 3), "phi", round(sum(gs) / sum(ss), 3))
