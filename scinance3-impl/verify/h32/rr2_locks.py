"""Gate audit H-32 follow-up: probe the DEC-101 locks with temporary files only (no panel, no outcome).

A-2: pilot lock with a NEW directory, with the pinned directory, with an earlier result elsewhere below runs_root.
A-3: fingerprint check with a wrong tree hash / without the tree pin; runner pins.
Gate: (1c) with and without the null_scaling block; NaN k.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research.h32_fm8 import checks, gate, schema, constants as C  # noqa: E402
from bybit_edge.research.h32_fm8.errors import H32Abort  # noqa: E402

TPL = Path("/home/user/scinance/scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml")
reg = yaml.safe_load(TPL.read_text())
schema.validate_registered(reg)
SHA = "ab" * 32
out = {}


def tryit(name, fn):
    try:
        r = fn()
        out[name] = {"raised": False, "result": str(r)[:160]}
    except H32Abort as exc:
        out[name] = {"raised": True, "error": type(exc).__name__, "msg": str(exc)[:200]}


with tempfile.TemporaryDirectory(dir="/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/h32_reg_review2") as td:
    repo = Path(td) / "repo"
    runs = repo / "scinance3-impl/state/runs"
    pinned = repo / reg["pilot_window"]["out_dir"]
    runs.mkdir(parents=True)
    # 1) fresh repo, pinned dir, no earlier pilot -> allowed
    tryit("fresh_pinned_dir", lambda: checks.check_rerun_lock(pinned, reg, None, registered_sha256=SHA, runs_root=runs, repo_root=repo))
    # 2) other --out -> refused
    tryit("other_out_dir", lambda: checks.check_rerun_lock(runs / "elsewhere", reg, None, registered_sha256=SHA, runs_root=runs, repo_root=repo))
    # 3) earlier pilot result of THIS registration in another directory below runs_root -> refused even in the pinned dir
    (runs / "old_try").mkdir()
    (runs / "old_try" / "h32_pilot.json").write_text(json.dumps({"registered_sha256": SHA}))
    tryit("earlier_result_elsewhere", lambda: checks.check_rerun_lock(pinned, reg, None, registered_sha256=SHA, runs_root=runs, repo_root=repo))
    # 4) earlier result of ANOTHER registration -> allowed
    (runs / "old_try" / "h32_pilot.json").write_text(json.dumps({"registered_sha256": "cd" * 32}))
    tryit("earlier_result_other_registration", lambda: checks.check_rerun_lock(pinned, reg, None, registered_sha256=SHA, runs_root=runs, repo_root=repo))
    # 5) unreadable file of the pattern -> refused (stricter reading)
    (runs / "old_try" / "h32_pilot_x.json").write_text("{not json")
    tryit("unreadable_pattern_file", lambda: checks.check_rerun_lock(pinned, reg, None, registered_sha256=SHA, runs_root=runs, repo_root=repo))
    (runs / "old_try" / "h32_pilot_x.json").unlink()
    # 6) a marker-like file written before computing (does the glob catch a 'started' marker?)
    (pinned).mkdir(parents=True, exist_ok=True)
    (pinned / "h32_pilot_attempt.json").write_text(json.dumps({"registered_sha256": SHA}))
    tryit("attempt_marker_in_pinned_dir", lambda: checks.check_rerun_lock(pinned, reg, None, registered_sha256=SHA, runs_root=runs, repo_root=repo))
    # 7) the legacy call without scope (as tests / library) -> behaves as DEC-99 per directory
    tryit("legacy_call_new_dir_no_scope", lambda: checks.check_rerun_lock(Path(td) / "new", reg, None))

obs = dict(reg["data_fingerprints"])
tryit("fingerprints_equal", lambda: checks.check_data_fingerprints(reg, obs))
bad = dict(obs, delisted_tree_sha256="0" * 64)
tryit("fingerprint_tree_differs", lambda: checks.check_data_fingerprints(reg, bad))
reg2 = copy.deepcopy(reg)
reg2["data_fingerprints"].pop("delisted_tree_sha256")
tryit("yaml_without_tree_pin", lambda: checks.check_data_fingerprints(reg2, obs))
tryit("schema_without_tree_pin", lambda: schema.validate_registered(reg2))
tryit("runner_ok", lambda: checks.check_runner_pins(reg, {"as_of": "2026-09-28", "start_year": 2021, "end_year": 2026, "allow_partial": True}))
tryit("runner_as_of_today", lambda: checks.check_runner_pins(reg, {"as_of": "2026-10-21", "start_year": 2021, "end_year": 2026, "allow_partial": True}))
tryit("runner_no_partial", lambda: checks.check_runner_pins(reg, {"as_of": "2026-09-28", "start_year": 2021, "end_year": 2026, "allow_partial": False}))

# gate: scaled vs unscaled (1c); NaN k fails closed
base = {"y": 0.0175, "se_w": 0.009, "q95": 0.0170}
out["gate_unscaled"] = gate.window_conditions(base, C.Z_KRIT)
out["gate_scaled_k12"] = gate.window_conditions(dict(base, null_scaling={"sd_real": 0.066, "sd_week": 0.055, "m": 0.002, "q95_frozen": 0.0170}), C.Z_KRIT)
out["gate_scaled_nan"] = gate.window_conditions(dict(base, null_scaling={"sd_real": float("nan"), "sd_week": 0.055, "m": 0.002, "q95_frozen": 0.0170}), C.Z_KRIT)
Path(__file__).with_name("rr2_locks.json").write_text(json.dumps(out, indent=1, default=str))
for k, v in out.items():
    print(k, v if not isinstance(v, dict) or "raised" in v else {kk: v[kk] for kk in ("c_null_quantile", "window_pass", "k", "q95_effective")})
