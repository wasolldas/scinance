"""Formation-side: WP-7 funding autocorrelation estimator on the full (truncated) union panel,
literal (np.nansum zero-fills weeks without funding) vs. weeks without funding treated as missing."""
import sys, pickle
sys.path.insert(0, "/home/user/scinance/src")
import numpy as np
from bybit_edge.research.wp7_universe import panel_load
SP = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_review"
d = pickle.load(open(SP + "/cache/rv_data.pkl", "rb"))
pan = {"symbols": d["symbols"], "dates": d["dates"], "funding_sum": d["funding_sum_daily"]}
fa = panel_load.funding_autocorrelation(pan, max_lag=1, min_weeks=12)
print("literal WP-7 (zero-filled), full history to 2026-06-28:", fa["median_autocorr"]["lag1"], fa["n_symbols_used"])
fsn = d["fsum_nan"]; vals = []
for j in range(fsn.shape[1]):
    s = fsn[:, j]; v = ~np.isnan(s)
    if v.sum() < 12: continue
    s = s[v]
    if s.std() == 0 or s[:-1].std() == 0 or s[1:].std() == 0: continue
    vals.append(np.corrcoef(s[:-1], s[1:])[0, 1])
print("no zero-fill (weeks with >=1 funding day only):", float(np.median(vals)), len(vals))
