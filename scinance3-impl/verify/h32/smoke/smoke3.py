import sys, time, json, pickle
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f")
sys.path.insert(0, "/home/user/scinance/.claude/worktrees/agent-a08096a12f7c3fc8f/src")
from pathlib import Path
from tests.unit import h32_fixtures as F
from bybit_edge.research.h32_fm8 import constants as C, pilot, schema, testrun, positive_control as pc, checks, artifacts

class MP:
    def setattr(self, obj, name, val):
        setattr(obj, name, val)
F.shrink_constants(MP())
base = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h32_smoke")
panel, rep, reg = pickle.load(open(base / "state.pkl", "rb"))
pj = base / "out_pilot" / "h32_pilot.json"
sha = artifacts.sha256_file(pj)
pil = testrun.load_pilot_result(pj, sha, reg, "r" * 64)
print("handed", pil["handed"])
t0 = time.time()
shape, symbols, crep = pc.build_shape(panel, reg["seal"]["panel_cut_test"])
r = pc.run_positive_control(shape, symbols, reg, pil, observed_fingerprints=dict(F.FAKE_FINGERPRINTS), registered_sha256="r" * 64,
                            pilot_sha256=sha, log=print)
print("pc", time.time() - t0, r["line"])
for v, x in r["variants"].items():
    print(v, x["binding_window"], x["target_effect"], x["injection"], x["judgement"]["pass_share_binding"], x["judgement"]["false_pass_rate_by_window"], x["judgement"]["sd_ratio"], x["criteria"])
t0 = time.time()
rr = testrun.run_test(panel, reg, pil, dict(F.FAKE_FINGERPRINTS), registered_sha256="r" * 64, log=print)
print("run", time.time() - t0, rr["hypothesis_verdict"])
for e, res in rr["results"].items():
    print(e, res["verdict"]["verdict"], res["verdict"]["labels"][:4], res.get("p_max"))
out = base / "out_run"
import shutil
shutil.rmtree(out, ignore_errors=True)
w = testrun.write_run_artifacts(out, rr, reg, pilot_sha256=sha)
print(sorted(p.name for p in out.iterdir()))
