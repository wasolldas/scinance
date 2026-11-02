import json, math, sys
d = json.load(open(sys.argv[1]))
for wn in ("W1", "W2"):
    w = d["windows"][wn]
    dec = w["beta_control_decision"]; mb = dec["null_mean_bound"]
    st = w["beta_control_method_study"]
    print(f"=== {wn} bound {mb:.5f}")
    for cal in ("measured", "stress"):
        for m in st["methods"]:
            vs = st["calibrations"][cal]["methods"][m]["variants"]
            row = []
            for v in st["variants"]:
                x = vs[v]; se = x["mean_ic_draws_sd"]/math.sqrt(x["n_reps_finite"])
                z = (abs(x["mean_ic_draws_mean"]) - mb)/se
                row.append(f"{v}:{x['mean_ic_draws_mean']:+.5f}({z:+.1f})")
            print(f" {cal:8s} {m:16s} " + " ".join(row))
