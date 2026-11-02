"""Empirical exceedance of the frozen q95 (1c) in the 10,000 p replicates of the binding cell (MC precision of the 1,000-replicate constant)."""
import json
import numpy as np
import yaml
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"))
rep = json.load(open("/home/user/scinance/scinance3-impl/state/runs/h32_20261021_v6/h32_prelaunch_p_replicates.json"))
out = {}
for wn in ("W1", "W2"):
    for v in ("mom1", "mom2", "mom4", "rev_gap"):
        d = np.asarray(rep["windows"][wn]["variants"][v])
        q = reg["windows"][wn]["frozen_v6"]["q95"][v]
        out[f"{wn}_{v}"] = {"q95_frozen": q, "q95_10k": float(np.quantile(d, 0.95)), "exceed_frozen_10k": float((d >= q).mean()),
                            "exceed_frozen_first1k": float((d[:1000] >= q).mean()), "exceed_frozen_last9k": float((d[1000:] >= q).mean())}
        print(wn, v, {k: round(x, 5) for k, x in out[f"{wn}_{v}"].items()})
json.dump(out, open("rr_q95_mc.json", "w"), indent=1)
