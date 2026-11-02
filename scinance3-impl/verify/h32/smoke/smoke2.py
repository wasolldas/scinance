import sys, time, json, pickle
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f")
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f/src")
from pathlib import Path
from tests.unit import h32_fixtures as F
from bybit_edge.research.h32_fm8 import constants as C, pilot, schema, testrun, positive_control as pc, checks

class MP:
    def setattr(self, obj, name, val):
        setattr(obj, name, val)
F.shrink_constants(MP())
sig = float(sys.argv[1]) if len(sys.argv) > 1 else 0.15
panel = F.make_panel(seed=7, signal=sig)
t0 = time.time()
rep = F.prelaunch_report(panel)
print("prelaunch", time.time() - t0)
reg = F.registered_from_report(rep)
reg["data_fingerprints"] = dict(F.FAKE_FINGERPRINTS)
schema.validate_registered(reg)
t0 = time.time()
pr = pilot.run_pilot(panel, reg, dict(F.FAKE_FINGERPRINTS), registered_sha256="r" * 64, log=print)
print("pilot", time.time() - t0, pr["status"], pr["handed"])
for v in C.VARIANTS:
    s = pr["variants"][v]["stats"]; h = pr["variants"][v]["handover"]
    print(v, round(s["x_p"], 5), round(s["se_p"], 5), round(s["t_p"], 2), h["status"], round(h["mde80_star"], 5), round(h["m_star"], 5), h["mu_sel"])
out = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h32_smoke/out_pilot")
import shutil
shutil.rmtree(out, ignore_errors=True)
lock = checks.check_rerun_lock(out, reg, None)
w = pilot.write_pilot_artifacts(out, pr, reg, lock)
print(w["result_json"], sorted(p.name for p in out.iterdir()))
pickle.dump((panel, rep, reg), open(out.parent / "state.pkl", "wb"))
