"""Synthetic only (no real data): realized share of an injected beta-independent mom1 signal in the fm8 IC,
(a) as registered (8-week beta t-7..t, includes the formation week) and (b) with the beta lagged one week
(t-8..t-1). Same PC world as the derivation's sector_check (W1 stress, no sectors), CRN pos/neg."""
import math, sys, time
import numpy as np, yaml
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research.wp13_xsec import characteristics, ic, positive_control as pc
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/registered/h28_h30_v3.yaml"))
K, BURN, WJ = 419, 9, 52
NW = BURN + WJ + 1
symbols = ["BTCUSDT"] + [f"SYN{i:04d}" for i in range(K - 1)]
alive = np.ones((NW, K), bool); valid = np.ones((NW, K), bool)
world = dict(pc.window_world(reg, "W1")); world["sigma_g"] = 0.0
if len(sys.argv) > 2 and sys.argv[2] == "measured":
    world["beta_sd"], world["rho_f"] = 0.5736662871596756, 0.0462406062845375
print("world", {k: round(v, 5) for k, v in world.items()})
world["sigma_tot"] = math.sqrt(world["sigma_e"]**2 + (world["beta_sd"] * world["sigma_f"])**2)
def stat(seed, sig, var, lag):
    sim = pc.synthesize_window_returns(alive, valid, symbols, world, seed=seed, window_index=1, signal_ic=sig)
    r, re = sim["returns"], sim["returns_est"]
    beta = characteristics.beta_characteristic(re, symbols, market_symbol="BTCUSDT", trail_win=8, min_weeks=8)
    if lag:
        beta = np.vstack([np.full((1, K), np.nan), beta[:-1]])
    if var == "mom1":
        ch = characteristics.momentum_characteristic(r, trail_win=1)
    else:
        ch = characteristics.momentum_characteristic(r, trail_win=4)
    sl = slice(BURN, NW)
    a = ic.apply_beta_control("fm_neutral_8w", ch[sl], r[sl], alive[sl], beta_pit=beta[sl], symbols=symbols, market_symbol="BTCUSDT")
    res = ic.weekly_ic_series(a["characteristic"], a["returns"], alive[sl], convention="close_at_last")
    x = np.array([w["ic"] for w in res["weekly"]], float); x = x[~np.isnan(x)]
    return x.mean(), x.std(ddof=1), x.size
n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
SIG = 0.0206
t0 = time.time()
for var in ("mom1",):
    for lag in (False, True):
        d = []; sds = []
        for k in range(n):
            p = stat(7000 + k, SIG, var, lag); q = stat(7000 + k, 0.0, var, lag)
            d.append(p[0] - q[0]); sds.append(q[1])
        d = np.array(d)
        print(var, "beta lagged" if lag else "beta t-7..t (registered)", "realized injection %.5f +- %.5f  share %.3f  weekly SD null %.4f  weeks %d" %
              (d.mean(), d.std(ddof=1)/math.sqrt(n), d.mean()/SIG, np.mean(sds), q[2]), "%.0fs" % (time.time()-t0))
