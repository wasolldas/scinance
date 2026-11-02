"""Formation-side exploration only (no outcome): panel meta, fingerprint, K, funding coverage."""
import sys, pickle, time
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
import numpy as np
import a1_common as C
t0 = time.time()
d = C.load()
print("load s", round(time.time() - t0, 1))
print(d["panel_meta"]); print(d["fingerprint"])
(C.WORK / "cache").mkdir(exist_ok=True)
with open(C.WORK / "cache" / "a1_data.pkl", "wb") as fh:
    pickle.dump(d, fh, protocol=pickle.HIGHEST_PROTOCOL)
weeks = d["weeks"]
# funding coverage: symbols with ANY funding ever, delisted vs survivors
anyf = (d["n_days_with_funding"] > 0).any(axis=0)
print("symbols with any funding:", int(anyf.sum()), "delisted with funding:", int((anyf & d["is_delisted"]).sum()),
      "delisted total:", int(d["is_delisted"].sum()))
for t in range(0, len(weeks), 13):
    if t + 1 >= len(weeks): break
    m = C.universe_mask(d, t)
    mf = m & (d["n_days_with_funding"][t] > 0)
    print(weeks[t], "U", int(m.sum()), "U_with_funding", int(mf.sum()), "full7", int((m & (d["n_days_with_funding"][t] == 7)).sum()))
