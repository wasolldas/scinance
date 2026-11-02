"""Independent re-derivation of the decisive inputs (own key arithmetic from the raw daily columns,
own week bucketing, own D1 selection). Outputs: window spread means (formation-side), nuisance total
SD and persistence ratio (nuisance, dispersion/ratio only -- no mean of any return)."""
import sys, pickle
from datetime import date, timedelta
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
import numpy as np
import a1_common as C
d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
P = d["panel"]; weeks = d["weeks"]; wpos = {w: i for i, w in enumerate(weeks)}
fn, fs = P["funding_n"], P["funding_sum"]
ok = np.isfinite(fn) & (fn > 0) & np.isfinite(fs)
daily_key = np.where(ok, fs - 0.0003, 0.0)        # sum over the day's payments of (F - I) = funding_sum - 0.03 %/day
daily_F = np.where(ok, fs, 0.0)
K = np.zeros((len(weeks), fn.shape[1])); FW = np.zeros_like(K)
for i, ds in enumerate(P["dates"]):
    dd = date.fromisoformat(ds); wk = (dd - timedelta(days=dd.weekday())).isoformat()
    if wk in wpos:
        K[wpos[wk]] += daily_key[i]; FW[wpos[wk]] += daily_F[i]
print("max |key - selfkey| =", float(np.max(np.abs(K - d["key"]))))
def d1(row, m):
    idx = np.flatnonzero(m); k = idx.size // 10
    return idx[np.argsort(row[idx], kind="stable")[:k]]
for wn, (a, b) in C.WINDOWS.items():
    ts = [t for t, w in enumerate(weeks) if a <= w <= b and (date.fromisoformat(w) + timedelta(days=7)).isoformat() <= b]
    sp = []
    for t in ts:
        m = d["alive"][t] & (d["alive"][t + 1] if t + 1 < len(weeks) else np.array([(x is None) or (x > (date.fromisoformat(weeks[t]) + timedelta(days=6)).isoformat()) for x in P["last_alive_day"]]))
        sel = d1(K[t], m); u = np.flatnonzero(m)
        sp.append((K[t, u].mean() - K[t, sel].mean()) * 1e4)
    print(wn, "n", len(ts), "spread mean bp", round(float(np.mean(sp)), 2))
# nuisance (holding weeks end <= 2024-06-30), K >= 117 base
R = np.where(d["returns_valid"], np.expm1(d["returns"]), 0.0)
x, g, s = [], [], []
for t in range(len(weeks) - 1):
    if weeks[t] < "2021-03-01": continue
    end_hold = (date.fromisoformat(weeks[t + 1]) + timedelta(days=6)).isoformat()
    if end_hold > "2024-06-30": continue
    m = d["alive"][t] & d["alive"][t + 1]
    if m.sum() < 117: continue
    sel = d1(K[t], m); u = np.flatnonzero(m)
    gg = FW[t + 1, u].mean() - FW[t + 1, sel].mean()
    x.append(R[t + 1, sel].mean() - R[t + 1, u].mean() + gg); g.append(gg); s.append(K[t, u].mean() - K[t, sel].mean())
x = np.array(x)
print("nuisance n", x.size, "SD total bp", round(float(x.std(ddof=1) * 1e4), 2), "phi", round(float(np.sum(g) / np.sum(s)), 4))
