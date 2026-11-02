import sys
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f")
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f/src")
import numpy as np
from tests.unit import test_h32_modes as T
from tests.unit import h32_fixtures as F
from bybit_edge.research.h32_fm8 import constants as C, nullsim, weekly as wkl, estimators as est, gate, positive_control as pc
from bybit_edge.research.wp13_xsec import ic, nulls, characteristics

class MP:
    def setattr(self, obj, name, val):
        setattr(obj, name, val)
F.shrink_constants(MP())
win = T._synthetic_window()
floor, _ = wkl.floor_and_v(np.full(52, 150))
n_ext, n_sym = win.alive_ext.shape
m_idx = win.symbols.index("BTCUSDT")
for sf, se_ in ((0.05, 0.05), (0.08, 0.04), (0.08, 0.03)):
    frozen = nullsim.window_null_constants(win, rho_f=0.2, beta_sd=0.45, sigma_f=sf, sigma_e=se_, n_reps=60, seed=53, floor_fm8=floor, n_boot=40, variants=("mom1",))["frozen"]
    print("sf", sf, "se", se_, "q95", frozen["q95"], "null_mean", frozen["null_mean"], "e_se", frozen["e_se_rule"])
    raws, ys, ps = [], [], 0
    for seed in range(10, 20):
        rng = np.random.default_rng(seed)
        sim = nulls.simulate_factor_panel(n_ext, n_sym, sigma_f=sf, sigma_e=se_, rho_f=0.2, drift_f=0.002, rng=rng, market_index=m_idx)
        r = sim["returns"]
        raw = ic.weekly_ic_series(characteristics.momentum_characteristic(r, trail_win=1)[8:], r[8:], win.alive, convention="close_at_last")["mean_ic"]
        series = pc.eval_world({"returns": r, "returns_est": r}, win.alive_ext, win.symbols, "mom1")
        y = float(np.nanmean(series)); sev = est.se_rule(series, floor, 52, n_boot=40, seed=53)["se"]
        c = gate.window_conditions({"y": y, "se_w": sev, "q95": frozen["q95"]["mom1"]}, C.Z_KRIT)
        raws.append(raw); ys.append(y); ps += c["window_pass"]
    print(" raw", np.round(raws, 3), "mean", np.mean(raws)); print(" y", np.round(ys, 3), "mean", np.mean(ys), "passes", ps)
