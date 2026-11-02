"""Market factor dispersion check on the windows (allowed: Faktor-SDs des Marktes). Prints only
absolute values / robust spreads, no signed mean."""
import sys, pickle
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
import numpy as np
import a1_common as C, a1_model as M
d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
fac = M.market_factors(d); weeks = d["weeks"]
r = M.returns_est(d)
for wn, (a, b) in C.WINDOWS.items():
    ts = C.judged_formation_weeks(weeks, a, b)
    hold = [t + 1 for t in ts if t + 1 < len(weeks)]
    for k in ("ew", "btc"):
        v = fac[k][hold]
        iqr = np.subtract(*np.percentile(v, [75, 25]))
        print(wn, k, "sd", round(float(np.std(v, ddof=1)), 4), "iqr/1.349", round(float(iqr / 1.349), 4),
              "top5 |f|", np.round(np.sort(np.abs(v))[-5:], 3))
    # EW of trimmed (5%..95%) cross-section, to see whether outlier symbols drive the EW SD
    tr = []
    for t in hold:
        m = d["alive"][t] & ~np.isnan(r[t])
        x = np.sort(r[t, m]); n = x.size; lo, hi = int(0.05 * n), int(0.95 * n)
        tr.append(x[lo:hi].mean())
    print(wn, "trimmed-EW sd", round(float(np.std(tr, ddof=1)), 4))
