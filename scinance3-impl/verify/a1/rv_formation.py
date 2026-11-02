"""Review A1 -- FORMATION-SIDE only (allowed on W1/W2): K, D1, formation spread (mean, SD),
key time-series autocorrelation per symbol with several estimators incl. the literal WP-7 function.
No holding-week quantity of any sorted set is computed."""
import sys, pickle, json
from datetime import date, timedelta
sys.path.insert(0, "/home/user/scinance/src")
import numpy as np
from bybit_edge.research.wp7_universe import panel_load

SP = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_review"
d = pickle.load(open(SP + "/cache/rv_data.pkl", "rb"))
weeks, key, alive = d["weeks"], d["key"], d["alive"]
nW = len(weeks)
def nxt(w): return (date.fromisoformat(w) + timedelta(days=7)).isoformat()
def judged(a, b): return [t for t, w in enumerate(weeks) if a <= w <= b and nxt(w) <= b]
def umask(t, excl1h=False):
    if t + 1 < nW:
        st = alive[t + 1]
    else:
        we = (date.fromisoformat(weeks[t]) + timedelta(days=6)).isoformat()
        st = np.array([(x is None) or (x > we) for x in d["last_alive_day"]])
    m = alive[t] & st
    if excl1h:
        m = m & ~(d["h1"][t] > 0)
    return m
def d1(row, m):
    idx = np.flatnonzero(m); k = max(1, idx.size // 10)
    return idx[np.argsort(row[idx], kind="stable")[:k]]
WIN = {"W1": ("2024-07-01", "2025-06-30"), "W2": ("2025-07-01", "2026-06-30")}
out = {}
def ts_ac(K, M, minw, mode):
    vals = []
    for j in range(K.shape[1]):
        m = M[:, j]
        if m.sum() < minw: continue
        if mode == "pairs":
            pr = m[:-1] & m[1:]
            if pr.sum() < minw - 1: continue
            a, b = K[:-1, j][pr], K[1:, j][pr]
        else:  # compressed series of member weeks (WP-7 style s = series[valid])
            s = K[m, j]; a, b = s[:-1], s[1:]
        if a.std() == 0 or b.std() == 0: continue
        vals.append(np.corrcoef(a, b)[0, 1])
    return float(np.median(vals)), len(vals)
for excl in (False, True):
    for wn, (a, b) in WIN.items():
        ts = judged(a, b)
        sp, K, n1 = [], [], []
        M = np.zeros_like(alive)
        for t in ts:
            m = umask(t, excl); M[t] = m
            u = np.flatnonzero(m); dd = d1(key[t], m)
            sp.append((key[t, u].mean() - key[t, dd].mean()) * 1e4); K.append(u.size); n1.append(dd.size)
        lo, hi = min(ts), max(ts) + 1
        r = {"n_weeks": len(ts), "K_min_med_max": [int(min(K)), float(np.median(K)), int(max(K))],
             "spread_mean_bp": float(np.mean(sp)), "spread_median_bp": float(np.median(sp)),
             "spread_sd_bp": float(np.std(sp, ddof=1)), "n_d1_mean": float(np.mean(n1))}
        for minw in (8, 12):
            for mode in ("pairs", "compressed"):
                r[f"key_ac_{mode}_min{minw}"] = ts_ac(key[lo:hi], M[lo:hi], minw, mode)
                r[f"rawF_ac_{mode}_min{minw}"] = ts_ac(d["fsum"][lo:hi], M[lo:hi], minw, mode)
        # alive-only membership (no still-trading / 1h condition), weeks with >=1 funding day
        Ma = alive[lo:hi] & (d["nday"][lo:hi] > 0)
        r["key_ac_pairs_min12_alive_and_funding"] = ts_ac(key[lo:hi], Ma, 12, "pairs")
        if not excl:
            # literal WP-7 function on the window's days (panel restricted to formation-week days)
            days = [i for i, ds in enumerate(d["dates"]) if weeks[lo] <= ds <= (date.fromisoformat(weeks[hi - 1]) + timedelta(days=6)).isoformat()]
            pan = {"symbols": d["symbols"], "dates": [d["dates"][i] for i in days],
                   "funding_sum": d["funding_sum_daily"][days, :]}
            fa = panel_load.funding_autocorrelation(pan, max_lag=1, min_weeks=12)
            r["WP7_literal_function_rawF_lag1"] = [fa["median_autocorr"]["lag1"], fa["n_symbols_used"]]
            # same, but weeks without any funding day treated as missing (no zero-fill)
            fsn = d["fsum_nan"][lo:hi]
            vals = []
            for j in range(fsn.shape[1]):
                s = fsn[:, j]; v = ~np.isnan(s)
                if v.sum() < 12: continue
                s = s[v]
                if s.std() == 0: continue
                a_, b_ = s[:-1], s[1:]
                if a_.std() == 0 or b_.std() == 0: continue
                vals.append(np.corrcoef(a_, b_)[0, 1])
            r["WP7_style_rawF_no_zero_fill_lag1"] = [float(np.median(vals)), len(vals)]
        out[("B_" if excl else "A_") + wn] = r
print(json.dumps(out, indent=1))
json.dump(out, open(SP + "/rv_formation.json", "w"), indent=1)
