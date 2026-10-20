"""CLI end-to-end of ``scripts/h32_fm8.py`` on a FIXTURE panel (the panel seam ``load_union_panel`` is replaced; nothing real is
read): prelaunch -> template -> pilot (injected signal: hand-over; without signal: GL-012 (Pilot)) -> positive control -> run,
with every guard: start lock, panel cut, exactly-one-pilot lock, pilot lock, sealed file names, ``data/harvest``, exit codes
(positive control 0 / 3 / 1)."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from bybit_edge.research.h32_fm8 import artifacts, panel_cut, schema
from bybit_edge.research.h32_fm8 import constants as C

from tests.unit import h32_fixtures as F
from tests.unit.h32_fixtures import REGISTERED_SHA, shrunk  # noqa: F401  (pytest fixture)

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace(".py", "_driver"), ROOT / "scripts" / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H32 = _load_script("h32_fm8.py")
FP = dict(F.FAKE_FINGERPRINTS)


class Spy:
    """Replaces ``load_union_panel``: counts the calls and hands out the fixture panel."""

    def __init__(self, panel):
        self.panel, self.calls = panel, 0

    def __call__(self, a):
        self.calls += 1
        return self.panel, dict(FP)


def _prelaunch_argv(out: Path, **over) -> list[str]:
    base = {"--out": str(out), "--n-reps": "24", "--n-boot": "60", "--calibration-search-n-reps": "10", "--calibration-search-rel-tol": "10",
            "--calibration-search-max-iter": "6", "--gegenprobe-n-reps": "10", "--gegenprobe-rel-tol": "10", "--gegenprobe-z-max": "1e9",
            "--stress-rel": "", "--stress-abs": ""}
    base.update({k: str(v) for k, v in over.items()})
    argv = ["--prelaunch"] + [x for kv in base.items() for x in kv] + ["--no-gegenprobe-market-check"]
    return argv


def _write_census(tmp: Path) -> Path:
    p = tmp / "spread_census.json"
    p.write_text(json.dumps({"deciles": [{"decile": d, "perp_spread_bp_median": 3.0 + d} for d in range(1, 11)]
                             + []}).replace('"perp_spread_bp_median": 13.0', '"perp_spread_bp_median": 36.21'), encoding="utf-8")
    return p


@pytest.fixture(scope="module")
def e2e(tmp_path_factory):
    """prelaunch -> template -> pilot -> positive-control -> run through ``main`` on the signal fixture panel."""
    tmp = tmp_path_factory.mktemp("h32_cli")
    out: dict = {"tmp": tmp, "rc": {}}
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        panel = F.make_panel(seed=7, signal=0.15)
        spy = Spy(panel)
        mp.setattr(H32, "load_union_panel", spy)
        stress = tmp / "stress_rel.json"
        stress.write_text(json.dumps({"days": ["2024-08-05", "2025-04-07", "2026-06-20", "2026-07-01", "2026-08-19"]}), encoding="utf-8")
        out["rc"]["prelaunch"] = H32.main(_prelaunch_argv(tmp / "pre", **{"--stress-rel": stress}))
        out["pre_json"] = tmp / "pre" / "h32_prelaunch.json"
        out["rc"]["template"] = H32.main(["--emit-template", str(out["pre_json"]), str(tmp / "h32_v1.yaml"), "--spread-census", str(_write_census(tmp))])
        out["yaml"] = tmp / "h32_v1.yaml"
        out["sha"] = artifacts.sha256_file(out["yaml"])
        reg = ["--registered", str(out["yaml"]), "--registered-sha256", out["sha"]]
        out["reg_args"] = reg
        out["rc"]["pilot"] = H32.main(["--pilot", *reg, "--out", str(tmp / "pilot")])
        out["pilot_json"] = tmp / "pilot" / "h32_pilot.json"
        out["pilot_sha"] = artifacts.sha256_file(out["pilot_json"])
        pil = ["--pilot-result", str(out["pilot_json"]), "--pilot-result-sha256", out["pilot_sha"]]
        out["pil_args"] = pil
        out["rc"]["pc"] = H32.main(["--positive-control", *reg, *pil, "--out", str(tmp / "pc")])
        out["rc"]["run"] = H32.main(["--run", *reg, *pil, "--out", str(tmp / "run")])
        out["spy"], out["panel"] = spy, panel
    return out


def test_cli_e2e_every_mode_succeeds_and_writes_its_artifacts(e2e):
    assert e2e["rc"] == {"prelaunch": 0, "template": 0, "pilot": 0, "pc": 0, "run": 0}
    tmp = e2e["tmp"]
    assert {p.name for p in (tmp / "pre").iterdir()} >= {"h32_prelaunch.json", "h32_prelaunch.md", "h32_prelaunch_P_k_fm8.csv",
                                                         "h32_prelaunch_W1_k_fm8.csv", "h32_prelaunch_W2_k_fm8.csv"}
    pilot_files = {p.name for p in (tmp / "pilot").iterdir()}
    assert {"h32_pilot.json", "h32_pilot.md", "h32_pilot.sha256", "h32_pilot_fingerprint.json"} <= pilot_files
    assert (tmp / "pilot" / "h32_pilot.sha256").read_text().split()[0] == e2e["pilot_sha"]
    assert {"h32_positive_control.json", "h32_positive_control.md"} == {p.name for p in (tmp / "pc").iterdir()}
    run_files = {p.name for p in (tmp / "run").iterdir()}
    assert {"h32_run.json", "h32_run.md", "h32_run_fingerprint.json"} <= run_files and len(run_files) == 3 + 8
    assert not any("sealed" in n for d in ("pre", "pilot", "pc", "run") for n in {p.name for p in (tmp / d).iterdir()})
    assert e2e["spy"].calls == 4                                                        # prelaunch, pilot, positive control, run (not the template)


def test_cli_e2e_prelaunch_is_cut_and_the_stress_lists_are_date_filtered(e2e):
    pre = json.loads(e2e["pre_json"].read_text(encoding="utf-8"))
    assert pre["cut"]["cut_date"] == C.CUT_TEST and pre["cut"]["max_date"] == C.CUT_TEST and pre["cut"]["n_days_removed"] == 91
    w2 = pre["windows"]["W2"]["stress_rel"]
    assert w2["date_filter"] == C.CUT_TEST and w2["days_in_window"] == ["2026-06-20"] and w2["n_days_to_cut"] == 3
    assert "2026-07" not in json.dumps(pre["windows"]) and "2026-08-19" not in e2e["pre_json"].read_text(encoding="utf-8")
    md = (e2e["tmp"] / "pre" / "h32_prelaunch.md").read_text(encoding="utf-8")
    assert md.isascii() and "2026-07" not in md and "KEIN VERDIKT" in md


def test_cli_e2e_template_validates_and_carries_the_spread_the_fingerprints_and_the_new_blocks(e2e, shrunk):
    reg = schema.load_registered_yaml(e2e["yaml"])
    schema.validate_registered(reg)
    assert reg["rules"]["bounce_spread"] == pytest.approx(0.003621) and reg["data_fingerprints"] == FP
    text = e2e["yaml"].read_text(encoding="utf-8")
    assert text.startswith("# H-32") and "NICHT registriert" in text
    for block in ("pilot_window", "handover_rule", "fweek_counting", "fdr", "seal", "positive_control"):
        assert block in reg
    assert reg["pilot_window"]["pilot_result_sha256"] is None and reg["z_krit"] == 1.6448536 and reg["fdr"]["n_perm"] == C.N_PERM


def test_cli_e2e_pilot_hands_over_and_a_second_pilot_is_refused_without_a_dec(e2e, shrunk, monkeypatch):
    pilot = json.loads(e2e["pilot_json"].read_text(encoding="utf-8"))
    assert pilot["status"] == "UEBERGEBEN" and pilot["handed"] == ["mom1", "rev_gap"] and pilot["registered_sha256"] == e2e["sha"]
    spy = Spy(e2e["panel"])
    monkeypatch.setattr(H32, "load_union_panel", spy)
    before = sorted(p.name for p in (e2e["tmp"] / "pilot").iterdir())
    assert H32.main(["--pilot", *e2e["reg_args"], "--out", str(e2e["tmp"] / "pilot")]) == 1             # exactly one pilot run
    assert spy.calls == 0 and sorted(p.name for p in (e2e["tmp"] / "pilot").iterdir()) == before          # refused before the panel, nothing written
    assert H32.main(["--pilot", *e2e["reg_args"], "--out", str(e2e["tmp"] / "pilot"), "--pilot-rerun-dec", "x1"]) == 1
    assert H32.main(["--pilot", *e2e["reg_args"], "--out", str(e2e["tmp"] / "pilot"), "--pilot-rerun-dec", "DEC-101"]) == 0
    assert spy.calls == 1 and (e2e["tmp"] / "pilot" / "h32_pilot_rerun_DEC-101.json").is_file()
    assert artifacts.sha256_file(e2e["pilot_json"]) == e2e["pilot_sha"]                                  # the first result is untouched
    assert H32.main(["--pilot", *e2e["reg_args"], "--out", str(e2e["tmp"] / "pilot"), "--pilot-rerun-dec", "DEC-101"]) == 1
    assert "--force" not in H32.build_parser().format_help()


def test_cli_e2e_positive_control_is_bestanden_and_the_run_gives_the_verdict(e2e):
    pc = json.loads((e2e["tmp"] / "pc" / "h32_positive_control.json").read_text(encoding="utf-8"))
    assert pc["bestanden"] is True and pc["line"] == "Positivkontrolle BESTANDEN" and pc["pilot_sha256"] == e2e["pilot_sha"]
    assert (e2e["tmp"] / "pc" / "h32_positive_control.md").read_text(encoding="utf-8").startswith("Positivkontrolle BESTANDEN")
    run = json.loads((e2e["tmp"] / "run" / "h32_run.json").read_text(encoding="utf-8"))
    assert run["registered_sha256"] == e2e["sha"] and run["pilot"]["file_sha256"] == e2e["pilot_sha"] and run["handed"] == ["mom1", "rev_gap"]
    assert run["hypothesis_verdict"]["verdict"] == "PASS" and run["panel"]["max_date"] == C.CUT_TEST
    assert {e: r["computed"] for e, r in run["results"].items()} == {"H-32_mom1": True, "H-32_mom2": False, "H-32_mom4": False, "H-32_rev_gap": True}
    fp = json.loads((e2e["tmp"] / "run" / "h32_run_fingerprint.json").read_text(encoding="utf-8"))
    assert fp["pilot_sha256"] == e2e["pilot_sha"] and fp["panel_cut"] == C.CUT_TEST and fp["seed"] == 53
    md = (e2e["tmp"] / "run" / "h32_run.md").read_text(encoding="utf-8")
    assert md.isascii() and "F-WEEK" in md and "m = 11" in md


def test_cli_start_lock_refuses_before_any_panel_byte(e2e, shrunk, monkeypatch, tmp_path):
    spy = Spy(e2e["panel"])
    monkeypatch.setattr(H32, "load_union_panel", spy)
    pil = e2e["pil_args"]
    for mode in ("--pilot", "--positive-control", "--run"):
        extra = pil if mode != "--pilot" else []
        out = tmp_path / ("o" + mode.strip("-"))
        assert H32.main([mode, "--registered", str(e2e["yaml"]), *extra, "--out", str(out)]) == 1                       # sha256 omitted
        assert H32.main([mode, "--registered", str(e2e["yaml"]), "--registered-sha256", "0" * 64, *extra, "--out", str(out)]) == 1
        assert H32.main([mode, "--registered", str(tmp_path / "none.yaml"), "--registered-sha256", e2e["sha"], *extra, "--out", str(out)]) == 1
        assert not out.exists()
    assert spy.calls == 0
    bad = yaml.safe_load(e2e["yaml"].read_text(encoding="utf-8"))
    del bad["windows"]["W2"]["frozen_v6"]["e_se_rule"]
    bp = tmp_path / "bad.yaml"
    bp.write_text(yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
    sha = artifacts.sha256_file(bp)
    assert H32.main(["--pilot", "--registered", str(bp), "--registered-sha256", sha, "--out", str(tmp_path / "ob")]) == 1  # schema pre-flight, rc 1
    assert spy.calls == 0 and not (tmp_path / "ob").exists()


def test_cli_pilot_lock_for_positive_control_and_run(e2e, shrunk, monkeypatch, tmp_path):
    spy = Spy(e2e["panel"])
    monkeypatch.setattr(H32, "load_union_panel", spy)
    reg = e2e["reg_args"]
    for mode in ("--positive-control", "--run"):
        assert H32.main([mode, *reg, "--out", str(tmp_path / "a")]) == 1                                                  # no pilot result at all
        assert H32.main([mode, *reg, "--pilot-result", str(e2e["pilot_json"]), "--pilot-result-sha256", "0" * 64, "--out", str(tmp_path / "a")]) == 1
        assert H32.main([mode, *reg, "--pilot-result", str(tmp_path / "none.json"), "--pilot-result-sha256", e2e["pilot_sha"], "--out", str(tmp_path / "a")]) == 1
        sealed = tmp_path / "x_L_window_sealed.json"
        sealed.write_text("{}", encoding="utf-8")                                                                         # never opened
        assert H32.main([mode, *reg, "--pilot-result", str(sealed), "--pilot-result-sha256", "0" * 64, "--out", str(tmp_path / "a")]) == 1
        # a pilot result of ANOTHER registration (other YAML hash) is refused
        other = tmp_path / "other.yaml"
        other.write_text(e2e["yaml"].read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
        assert H32.main([mode, "--registered", str(other), "--registered-sha256", artifacts.sha256_file(other), *e2e["pil_args"],
                         "--out", str(tmp_path / "a")]) == 1
    assert spy.calls == 0 and not (tmp_path / "a").exists()


def test_cli_leak_through_a_bypassed_cut_is_a_loud_fail_without_output(e2e, shrunk, monkeypatch, tmp_path):
    monkeypatch.setattr(H32, "load_union_panel", Spy(e2e["panel"]))
    monkeypatch.setattr(panel_cut, "cut_panel_days", lambda panel, cut_date, **kw: (panel, {"cut_date": cut_date, "n_days_removed": 0}))
    assert H32.main(["--pilot", *e2e["reg_args"], "--out", str(tmp_path / "p")]) == 1
    assert H32.main(["--run", *e2e["reg_args"], *e2e["pil_args"], "--out", str(tmp_path / "r")]) == 1
    assert H32.main(["--positive-control", *e2e["reg_args"], *e2e["pil_args"], "--out", str(tmp_path / "c")]) == 1
    assert not (tmp_path / "p" / "h32_pilot.json").exists() and not (tmp_path / "r" / "h32_run.json").exists()
    assert not (tmp_path / "c" / "h32_positive_control.json").exists()


def test_cli_prelaunch_refuses_cut_dates_inside_the_blind_period_before_loading(e2e, shrunk, monkeypatch, tmp_path):
    spy = Spy(e2e["panel"])
    monkeypatch.setattr(H32, "load_union_panel", spy)
    for bad in ("2026-07-05", "2026-06-27", "2027-01-03", "nope"):
        assert H32.main(_prelaunch_argv(tmp_path / "x", **{"--cut-date": bad})) == 1
    assert spy.calls == 0 and not (tmp_path / "x").exists()


def test_cli_modes_are_exclusive_and_outputs_never_go_to_data_harvest(e2e, shrunk, monkeypatch, tmp_path, capsys):
    with pytest.raises(SystemExit):
        H32.main(["--pilot", "--run", "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit):
        H32.main([])
    with pytest.raises(SystemExit):
        H32.main(["--pilot", "--out", str(tmp_path / "o")])                                                                # --registered is mandatory
    with pytest.raises(SystemExit):
        H32.main(["--emit-template", "a", "b", "--pilot"])
    assert H32.main(["--emit-template", str(e2e["pre_json"]), "data/harvest/x.yaml", "--spread-census", str(_write_census(tmp_path))]) == 1
    monkeypatch.setattr(H32, "load_union_panel", Spy(e2e["panel"]))
    assert H32.main(["--pilot", *e2e["reg_args"], "--out", "data/harvest/h32_never"]) == 1
    assert not Path("data/harvest/h32_never").exists()
    census = tmp_path / "broken.json"
    census.write_text("{}", encoding="utf-8")
    assert H32.main(["--emit-template", str(e2e["pre_json"]), str(tmp_path / "t.yaml"), "--spread-census", str(census)]) == 1
    assert H32.main(["--emit-template", str(tmp_path / "missing.json"), str(tmp_path / "t.yaml"), "--spread-census", str(_write_census(tmp_path))]) == 1


def test_cli_signal_free_panel_pilot_is_gl012_no_positive_control_and_the_run_reads_no_panel(e2e, shrunk, monkeypatch, tmp_path):
    nul = F.get_bundle("null")
    ypath = tmp_path / "h32_v1.yaml"
    ypath.write_text(yaml.safe_dump(nul["registered"], sort_keys=False), encoding="utf-8")
    sha = artifacts.sha256_file(ypath)
    spy = Spy(nul["panel"])
    monkeypatch.setattr(H32, "load_union_panel", spy)
    reg = ["--registered", str(ypath), "--registered-sha256", sha]
    assert H32.main(["--pilot", *reg, "--out", str(tmp_path / "pilot")]) == 0                         # GL-012 (Pilot) is a result, not an abort
    pilot = json.loads((tmp_path / "pilot" / "h32_pilot.json").read_text(encoding="utf-8"))
    assert pilot["status"] == "GL-012 (Pilot)" and pilot["handed"] == []
    pil = ["--pilot-result", str(tmp_path / "pilot" / "h32_pilot.json"), "--pilot-result-sha256", artifacts.sha256_file(tmp_path / "pilot" / "h32_pilot.json")]
    assert H32.main(["--positive-control", *reg, *pil, "--out", str(tmp_path / "pc")]) == 1             # nothing handed over: no control, no test
    assert not (tmp_path / "pc").exists() and spy.calls == 1
    assert H32.main(["--run", *reg, *pil, "--out", str(tmp_path / "run")]) == 0
    assert spy.calls == 1                                                                              # the run did not read the panel
    run = json.loads((tmp_path / "run" / "h32_run.json").read_text(encoding="utf-8"))
    assert run["hypothesis_verdict"]["verdict"] == "GL-012 (Pilot)" and run["handed"] == []
    assert all(not r["computed"] and r["p_max"] == 1.0 for r in run["results"].values())
    assert sorted(p.name for p in (tmp_path / "run").iterdir()) == ["h32_run.json", "h32_run.md", "h32_run_fingerprint.json"]


def test_cli_positive_control_exit_code_3_when_not_bestanden(e2e, shrunk, monkeypatch, tmp_path):
    reg = yaml.safe_load(e2e["yaml"].read_text(encoding="utf-8"))
    reg["positive_control"]["criteria"]["pass_share_min"] = 1.01
    monkeypatch.setattr(C, "PC_PASS_SHARE_MIN", 1.01)
    p = tmp_path / "h32_v1.yaml"
    p.write_text(yaml.safe_dump(reg, sort_keys=False), encoding="utf-8")
    sha = artifacts.sha256_file(p)
    # the pilot result is bound to the registered YAML hash: re-run the pilot under the new registration
    monkeypatch.setattr(H32, "load_union_panel", Spy(e2e["panel"]))
    assert H32.main(["--pilot", "--registered", str(p), "--registered-sha256", sha, "--out", str(tmp_path / "pilot")]) == 0
    pj = tmp_path / "pilot" / "h32_pilot.json"
    rc = H32.main(["--positive-control", "--registered", str(p), "--registered-sha256", sha, "--pilot-result", str(pj),
                   "--pilot-result-sha256", artifacts.sha256_file(pj), "--out", str(tmp_path / "pc")])
    assert rc == 3
    rep = json.loads((tmp_path / "pc" / "h32_positive_control.json").read_text(encoding="utf-8"))
    assert rep["bestanden"] is False and rep["line"] == "Positivkontrolle NICHT BESTANDEN"
    assert (tmp_path / "pc" / "h32_positive_control.md").read_text(encoding="utf-8").startswith("Positivkontrolle NICHT BESTANDEN")
