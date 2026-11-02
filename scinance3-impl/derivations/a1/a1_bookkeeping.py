"""Formation-side bookkeeping counts (W1/W2, config A): switch days (funding_n not in {3,6,12,24}),
days with funding_n below the class count (partial), exact-zero funding days of D1 members."""
import sys, pickle, json
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
import numpy as np
import a1_common as C
d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
weeks, key = d["weeks"], d["key"]
out = {}
for wn, (a, b) in C.WINDOWS.items():
    ts = C.judged_formation_weeks(weeks, a, b)
    sw_d1 = sw_u = days_d1 = days_u = z_d1 = 0
    wk_sw_d1 = 0
    for t in ts:
        m = C.universe_mask(d, t); u = np.flatnonzero(m); d1 = C.d1_members(key[t], m)
        sw_d1 += int(d["cls_days"]["other"][t, d1].sum()); sw_u += int(d["cls_days"]["other"][t, u].sum())
        wk_sw_d1 += int((d["cls_days"]["other"][t, d1] > 0).sum())
        days_d1 += int(d["n_days_with_funding"][t, d1].sum()); days_u += int(d["n_days_with_funding"][t, u].sum())
        z_d1 += int(d["zero_days_w"][t, d1].sum())
    out[wn] = {"switch_days_share_d1": sw_d1 / days_d1, "switch_days_share_u": sw_u / days_u,
               "d1_symbol_weeks_with_switch_day": wk_sw_d1, "exact_zero_days_share_d1": z_d1 / days_d1}
    print(wn, out[wn])
(C.WORK / "bookkeeping.json").write_text(json.dumps(out, indent=1))
