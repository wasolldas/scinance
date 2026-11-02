"""Synthetic only: weekly SD of the fm8 mom1 IC in the PC world (W1 stress) with and without PRD sector blocks."""
import math, sys
import numpy as np, yaml
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research.wp13_xsec import characteristics, ic, positive_control as pc
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/registered/h28_h30_v3.yaml"))
K, BURN, WJ = 419, 8, 52; NW = BURN + WJ + 1
symbols = ["BTCUSDT"] + [f"SYN{i:04d}" for i in range(K - 1)]
alive = np.ones((NW, K), bool); valid = np.ones((NW, K), bool)
for rel in (0.0, 0.375):
    world = dict(pc.window_world(reg, "W1")); world["sigma_g"] = rel * world["sigma_e"]
    world["sigma_tot"] = math.sqrt(world["sigma_e"]**2 + world["sigma_g"]**2 + (world["beta_sd"] * world["sigma_f"])**2)
    pooled = []; means = []
    for k in range(40):
        sim = pc.synthesize_window_returns(alive, valid, symbols, world, seed=9100 + k, window_index=1, signal_ic=0.0)
        r, re = sim["returns"], sim["returns_est"]
        beta = characteristics.beta_characteristic(re, symbols, market_symbol="BTCUSDT", trail_win=8, min_weeks=8)
        ch = characteristics.momentum_characteristic(r, trail_win=1); sl = slice(BURN, NW)
        a = ic.apply_beta_control("fm_neutral_8w", ch[sl], r[sl], alive[sl], beta_pit=beta[sl], symbols=symbols, market_symbol="BTCUSDT")
        x = np.array([w["ic"] for w in ic.weekly_ic_series(a["characteristic"], a["returns"], alive[sl], convention="close_at_last")["weekly"]], float)
        x = x[~np.isnan(x)]; pooled += x.tolist(); means.append(x.mean())
    print("sector_rel", rel, "weekly SD %.4f" % np.std(pooled, ddof=1), "SD of means %.5f" % np.std(means, ddof=1))
