import sys, time, math
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f")
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f/src")
import numpy as np
from statistics import NormalDist
from tests.unit import h32_fixtures as F
from bybit_edge.research.h32_fm8 import constants as C, weekly as wkl, permutation as P, fm8, panel_cut

N = NormalDist()
sig = float(sys.argv[1])
rows = []
for seed in range(1, 7):
    panel = F.make_panel(seed=seed, signal=sig)
    cut, _ = panel_cut.cut_panel_days(panel, C.CUT_TEST)
    wk = wkl.build_weekly(cut, C.CUT_TEST)
    for wn in ("W1", "W2"):
        win = wkl.make_window(wk, wn)
        draws = P.block_permutation_draws({v: win.chars[v] for v in C.VARIANTS}, win.returns, win.alive, win.beta8, n_perm=200)
        for v in C.VARIANTS:
            res = fm8.window_ic(win, v)
            s = C.SIGN[C.DIRECTION[v]]
            y = s * res["mean_ic"]
            p = P.permutation_pvalue(y, draws[v])
            ic = np.array(res["ic_weekly"])
            se = ic.std(ddof=1) / math.sqrt(len(ic))
            pn = 1 - N.cdf(y / se)
            rows.append((seed, wn, v, y, p["p_value"], pn, p["draws_mean"], p["draws_sd"]))
import collections
agg = collections.defaultdict(list)
for r in rows:
    agg[(r[1], r[2])].append(r)
for k, v in sorted(agg.items()):
    print(k, "y", np.round([x[3] for x in v], 3), "p_perm", np.round([x[4] for x in v], 3), "p_norm", np.round([x[5] for x in v], 3),
          "null mean/sd", round(np.mean([x[6] for x in v]), 4), round(np.mean([x[7] for x in v]), 4))
