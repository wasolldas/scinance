"""Kill (4) robustness (formation-side): per-symbol lag-1 autocorrelation of the key on W1/W2 --
symbol-bootstrap CI of the median and min_weeks sensitivity."""
import sys, pickle, json
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
import numpy as np
import a1_common as C
d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
weeks, key = d["weeks"], d["key"]
out = {}
for wn, (a, b) in C.WINDOWS.items():
    ts = C.judged_formation_weeks(weeks, a, b)
    member = np.zeros_like(d["alive"])
    for t in ts:
        member[t] = C.universe_mask(d, t)
    lo, hi = min(ts), max(ts) + 1
    K, Mm = key[lo:hi], member[lo:hi]
    res = {}
    for mw in (8, 12, 26, 40):
        vals = []
        for j in range(K.shape[1]):
            m = Mm[:, j]
            if m.sum() < mw: continue
            pair = m[:-1] & m[1:]
            if pair.sum() < mw - 1: continue
            x, y = K[:-1, j][pair], K[1:, j][pair]
            if x.std() == 0 or y.std() == 0: continue
            vals.append(np.corrcoef(x, y)[0, 1])
        vals = np.array(vals)
        rng = np.random.default_rng(53)
        bs = np.array([np.median(vals[rng.integers(0, vals.size, vals.size)]) for _ in range(2000)])
        res[f"min_weeks_{mw}"] = {"median": float(np.median(vals)), "n": int(vals.size),
                                  "ci90": [float(np.quantile(bs, 0.05)), float(np.quantile(bs, 0.95))],
                                  "p_boot_median_lt_030": float(np.mean(bs < 0.30))}
    out[wn] = res
    print(wn, json.dumps(res))
(C.WORK / "kill4_ci.json").write_text(json.dumps(out, indent=1))
