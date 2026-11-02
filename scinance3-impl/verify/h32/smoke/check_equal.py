import sys, time, math
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f")
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f/src")
import numpy as np
from tests.unit import h32_fixtures as F
from bybit_edge.research.h32_fm8 import constants as C, weekly as wkl, permutation as P, fm8, panel_cut
from bybit_edge.research.wp13_xsec import ic

panel = F.make_panel(seed=3, signal=0.08)
cut, rep = panel_cut.cut_panel_days(panel, C.CUT_TEST)
wk = wkl.build_weekly(cut, C.CUT_TEST)
for wn in ("W1", "W2"):
    win = wkl.make_window(wk, wn)
    k8 = wkl.k_fm8_series(win)
    res = fm8.window_ic(win, "mom1")
    kk = np.array(res["k_weekly"])
    print(wn, "k equal", bool((k8 == kk).all()), "alive K min", wkl.k_alive_series(win).min(), "w_judged", win.w_judged)
    # identity permutation
    rows = np.arange(1, win.n_weeks)
    out = P.permuted_week_ic({v: win.chars[v] for v in C.VARIANTS}, win.returns, win.alive, win.beta8, rows,
                             rank_cache=P._build_rank_cache({v: win.chars[v] for v in C.VARIANTS}, win.alive))
    for v in C.VARIANTS:
        ref = np.array(fm8.window_ic(win, v)["ic_weekly"])
        print(wn, v, "identity-perm bitwise equal:", bool(np.array_equal(ref, out[v], equal_nan=True)), "maxdiff", float(np.nanmax(np.abs(ref - out[v]))))
