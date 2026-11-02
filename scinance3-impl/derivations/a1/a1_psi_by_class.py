"""Formation-side: within-week persistence psi of the Mon-Wed D1 split by whether the member had a
1h funding day in Mon-Wed (W2, W1 and nuisance base). Only data inside the formation week."""
import sys, pickle, json
from datetime import date
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
import numpy as np
import a1_common as C
import a1_formation_sensitivity as FS
d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
weeks, key = d["weeks"], d["key"]
exc, has, rows = FS.daily_excess_by_week(d)
fn = d["panel"]["funding_n"]
sets = {wn: C.judged_formation_weeks(weeks, a, b) for wn, (a, b) in C.WINDOWS.items()}
sets["nuisance_K_ge_117"] = [t for t in C.nuisance_formation_weeks(weeks) if C.universe_mask(d, t).sum() >= 117]
out = {}
for name, ts in sets.items():
    acc = {"1h": [0.0, 0.0, 0], "other": [0.0, 0.0, 0]}
    for t in ts:
        rr = rows[t]
        if len(rr) != 7: continue
        m = C.universe_mask(d, t)
        first = exc[rr[:3]].sum(axis=0); later = exc[rr[3:]].sum(axis=0)
        d1 = C.d1_members(first, m); u = np.flatnonzero(m)
        is1h = (np.round(np.nan_to_num(fn[rr[:3]])) == 24).any(axis=0)
        for lab, sel in (("1h", d1[is1h[d1]]), ("other", d1[~is1h[d1]])):
            if sel.size == 0: continue
            acc[lab][0] += (later[u].mean() - later[sel].mean()) / 4.0 * sel.size
            acc[lab][1] += (first[u].mean() - first[sel].mean()) / 3.0 * sel.size
            acc[lab][2] += sel.size
    out[name] = {k: {"psi": v[0] / v[1] if v[1] else None, "n_member_weeks": v[2]} for k, v in acc.items()}
    print(name, out[name])
(C.WORK / f"psi_by_class{C.SUFFIX}.json").write_text(json.dumps(out, indent=1))
