import numpy as np, math
rng = np.random.default_rng(20261012)
Z = 2.4865; LEVEL = 1 - 0.0064
def one(sd, n, prior, floor, dist, nser=1500, nboot=1000, b=4):
    if dist == "normal":
        x = rng.standard_normal((nser, n))
    else:  # t df=4 scaled to unit variance
        x = rng.standard_t(4, (nser, n)) / math.sqrt(4 / 2)
    ic = prior + sd * x
    m = ic.mean(1); s = ic.std(1, ddof=1)
    se = np.maximum(floor, s) / math.sqrt(n)
    mag = m >= Z * se
    nb = math.ceil(n / b)
    ci_ok = np.empty(nser, bool)
    starts = rng.integers(0, n - b + 1, size=(nser, nboot, nb))
    offs = np.arange(b)
    for i in range(nser):
        idx = (starts[i][:, :, None] + offs).reshape(nboot, -1)[:, :n]
        means = ic[i][idx].mean(1)
        ci_ok[i] = np.quantile(means, 1 - LEVEL) > 0
    return mag.mean(), ci_ok.mean(), (mag & ci_ok).mean()
for label, sd, n, floor in [("W1 measured", 0.0901, 52, 0.04858), ("W1 stress", 0.1302, 52, 0.04858),
                            ("W2 measured", 0.0610, 51, 0.04192), ("W2 stress", 0.0817, 51, 0.04192)]:
    for dist in ("normal", "t4"):
        pm, pc, pj = one(sd, n, 0.03, floor, dist)
        print(f"{label:12s} {dist:6s} P_mag {pm:.3f}  P_CI {pc:.3f}  P_mag&CI {pj:.3f}")
# positive-control world check: realised IC ~0.05, SD ~0.135 (stress + sectors), W1
for prior in (0.045, 0.056, 0.06):
    pm, pc, pj = one(0.135, 52, prior, 0.04858, "normal")
    print(f"PC-W1 IC {prior:.3f} SD 0.135 normal  P_mag {pm:.3f} P_CI {pc:.3f} joint {pj:.3f}")
