import sys, time, json
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f")
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f/src")
from tests.unit import h32_fixtures as F
from bybit_edge.research.h32_fm8 import constants as C

class MP:
    def setattr(self, obj, name, val):
        setattr(obj, name, val)
F.shrink_constants(MP())
t0 = time.time()
panel = F.make_panel(seed=7, signal=0.0)
print("panel", panel["close"].shape, time.time() - t0)
t0 = time.time()
rep = F.prelaunch_report(panel, n_reps=C.N_REPS_MIN, n_boot=C.N_BOOT_MIN, log=print)
print("prelaunch", time.time() - t0)
print(json.dumps(rep["windows"]["W1"]["frozen_v6"], indent=1)[:1500])
print(rep["windows"]["P"]["m_P"])
