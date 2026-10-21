"""CLI end-to-end of ``scripts/h32_fm8.py`` on a FIXTURE panel (the file seam ``read_union_panel`` is replaced; nothing real is
read): prelaunch -> template -> PP3 dry run -> pilot (injected signal: hand-over; without signal: GL-012 (Pilot)) -> positive
control -> run, with every guard: start lock, runner pins, universe filter, panel cut, exactly-one-pilot lock (pinned directory
and search below the runs root), pilot lock, sealed file names, ``data/harvest``, exit codes (positive control 0 / 3 / 1).

DEC-101 adaptations of the earlier tests: the seam is ``read_union_panel`` (``load_union_panel`` now also applies the universe
filter and returns the report); the fixture panel carries a USDC twin and a dated future (the filter must remove them in every
mode); every mode that reads the panel gets the runner arguments of the registration; ``H32.REPO_ROOT`` is a temporary
repository whose pinned pilot directory is the only accepted ``--out`` of ``--pilot``."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from bybit_edge.research.h32_fm8 import artifacts, panel_cut, pnull, schema
from bybit_edge.research.h32_fm8 import constants as C
from bybit_edge.research.h32_fm8 import estimators as est

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
P_REPS = 32                                  # more p replicates than the 24 of the shrunk constants (finer p resolution path)
#: DEC-101 E4: the runner arguments that the Vorlauf records and the template pins (``h32_fixtures.RUNNER``).
RUNNER_ARGS = ["--as-of", "2026-09-28", "--start-year", "2021", "--end-year", "2026", "--allow-partial"]


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
    argv = ["--prelaunch"] + [x for kv in base.items() for x in kv] + ["--no-gegenprobe-market-check"] + RUNNER_ARGS
    return argv


def _env(monkeypatch, panel, repo):
    """A fresh spy on the file seam and a temporary repository root; returns the spy."""
    spy = Spy(panel)
    monkeypatch.setattr(H32, "read_union_panel", spy)
    monkeypatch.setattr(H32, "REPO_ROOT", repo)
    return spy


def _pinned(repo: Path) -> Path:
    return repo / C.PILOT_OUT_DIR


def _write_census(tmp: Path) -> Path:
    p = tmp / "spread_census.json"
    p.write_text(json.dumps({"deciles": [{"decile": d, "perp_spread_bp_median": 3.0 + d} for d in range(1, 11)]
                             + []}).replace('"perp_spread_bp_median": 13.0', '"perp_spread_bp_median": 36.21'), encoding="utf-8")
    return p


@pytest.fixture(scope="module")
def e2e(tmp_path_factory):
    """prelaunch -> template -> pilot -> positive-control -> run through ``main`` on the signal fixture panel."""
    tmp = tmp_path_factory.mktemp("h32_cli")
    repo = tmp / "repo"
    out: dict = {"tmp": tmp, "rc": {}, "repo": repo, "pilot_dir": _pinned(repo)}
    with pytest.MonkeyPatch.context() as mp:
        F.shrink_constants(mp)
        panel = F.add_twins(F.make_panel(seed=7, signal=0.15))                    # DEC-101 E1: a USDC twin and a dated future
        spy = Spy(panel)
        mp.setattr(H32, "read_union_panel", spy)
        mp.setattr(H32, "REPO_ROOT", repo)
        stress = tmp / "stress_rel.json"
        stress.write_text(json.dumps({"days": ["2024-08-05", "2025-04-07", "2026-06-20", "2026-07-01", "2026-08-19"]}), encoding="utf-8")
        out["rc"]["prelaunch"] = H32.main(_prelaunch_argv(tmp / "pre", **{"--stress-rel": stress, "--p-reps": P_REPS}))
        out["pre_json"] = tmp / "pre" / "h32_prelaunch.json"
        out["p_args"] = ["--p-replicates", str(tmp / "pre" / C.P_REPLICATES_FILE)]
        out["rc"]["template"] = H32.main(["--emit-template", str(out["pre_json"]), str(tmp / "h32_v1.yaml"), "--spread-census", str(_write_census(tmp))])
        out["yaml"] = tmp / "h32_v1.yaml"
        out["sha"] = artifacts.sha256_file(out["yaml"])
        reg = ["--registered", str(out["yaml"]), "--registered-sha256", out["sha"]]
        out["reg_args"] = reg
        out["rc"]["pp3"] = H32.main(["--pp3-dry-run", *reg, *RUNNER_ARGS, "--out", str(tmp / "pp3")])        # DEC-101 E6: before the pilot
        out["rc"]["pilot"] = H32.main(["--pilot", *reg, *RUNNER_ARGS, "--out", str(out["pilot_dir"])])
        out["pilot_json"] = out["pilot_dir"] / "h32_pilot.json"
        out["pilot_sha"] = artifacts.sha256_file(out["pilot_json"])
        pil = ["--pilot-result", str(out["pilot_json"]), "--pilot-result-sha256", out["pilot_sha"]]
        out["pil_args"] = pil
        out["rc"]["pc"] = H32.main(["--positive-control", *reg, *pil, *RUNNER_ARGS, "--out", str(tmp / "pc")])
        out["rc"]["run"] = H32.main(["--run", *reg, *pil, *out["p_args"], *RUNNER_ARGS, "--out", str(tmp / "run")])
        out["spy"], out["panel"] = spy, panel
    return out


def test_cli_e2e_every_mode_succeeds_and_writes_its_artifacts(e2e):
    assert e2e["rc"] == {"prelaunch": 0, "template": 0, "pp3": 0, "pilot": 0, "pc": 0, "run": 0}
    tmp = e2e["tmp"]
    assert {p.name for p in (tmp / "pre").iterdir()} >= {"h32_prelaunch.json", "h32_prelaunch.md", "h32_prelaunch_P_k_fm8.csv",
                                                         "h32_prelaunch_W1_k_fm8.csv", "h32_prelaunch_W2_k_fm8.csv", C.P_REPLICATES_FILE}
    pilot_files = {p.name for p in e2e["pilot_dir"].iterdir()}
    assert {"h32_pilot.json", "h32_pilot.md", "h32_pilot.sha256", "h32_pilot_fingerprint.json"} <= pilot_files
    assert (e2e["pilot_dir"] / "h32_pilot.sha256").read_text().split()[0] == e2e["pilot_sha"]
    assert [p.name for p in (tmp / "pp3").iterdir()] == [C.PP3_FILE]                       # the dry run writes one small file only
    assert {"h32_positive_control.json", "h32_positive_control.md"} == {p.name for p in (tmp / "pc").iterdir()}
    run_files = {p.name for p in (tmp / "run").iterdir()}
    assert {"h32_run.json", "h32_run.md", "h32_run_fingerprint.json"} <= run_files and len(run_files) == 3 + 8
    assert not any("sealed" in n for d in ("pre", "pp3", "pc", "run") for n in {p.name for p in (tmp / d).iterdir()})
    assert e2e["spy"].calls == 5                                                        # prelaunch, pp3, pilot, positive control, run (not the template)


def test_cli_e2e_prelaunch_is_cut_and_the_stress_lists_are_date_filtered(e2e):
    pre = json.loads(e2e["pre_json"].read_text(encoding="utf-8"))
    assert pre["cut"]["cut_date"] == C.CUT_TEST and pre["cut"]["max_date"] == C.CUT_TEST and pre["cut"]["n_days_removed"] == 91
    # DEC-101 E1: the twin and the dated future never reached a calculation; E4: the runner arguments are recorded
    assert pre["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0} and pre["universe"]["rule"] == C.UNIVERSE_RULE
    assert pre["universe"]["excluded_symbols"] == ["S002PERP", "S002USDT-25DEC26"] and pre["cut"]["n_symbols"] <= len(e2e["panel"]["symbols"]) - 2
    assert pre["runner"] == F.RUNNER and pre["power_line"]["m_grid"] == [1, 2, 3, 4, 11]
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
    assert reg["universe"] == {"rule": C.UNIVERSE_RULE, "label": C.UNIVERSE_LABEL,
                               "excluded_at_prelaunch": {"usdc_perp": 1, "dated_future": 1, "other": 0}}
    assert reg["null_scaling"]["enabled"] is True and reg["runner"] == F.RUNNER and reg["pilot_window"]["out_dir"] == C.PILOT_OUT_DIR
    assert "# " + C.W1_CONTROL_NOTE in text
    assert reg["pilot_window"]["pilot_result_sha256"] is None and reg["z_krit"] == 1.6448536 and reg["fdr"]["n_perm"] == C.N_PERM
    fdr = reg["fdr"]
    assert fdr["p_source"] == "factor_preserving_null_replicates" and fdr["n_reps"] == P_REPS > reg["rules"]["n_reps"] == 24
    assert fdr["replicates_sha256"] == artifacts.sha256_file(e2e["tmp"] / "pre" / C.P_REPLICATES_FILE)
    assert fdr["report_only"] == ["block_permutation_fm8_window_mean", "normal_approximation"]


def test_cli_e2e_pilot_hands_over_and_a_second_pilot_is_refused_without_a_dec(e2e, shrunk, monkeypatch):
    pilot = json.loads(e2e["pilot_json"].read_text(encoding="utf-8"))
    assert pilot["status"] == "UEBERGEBEN" and pilot["handed"] == ["mom1", "rev_gap"] and pilot["registered_sha256"] == e2e["sha"]
    assert pilot["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0} and pilot["runner"] == F.RUNNER
    spy = _env(monkeypatch, e2e["panel"], e2e["repo"])
    out = str(e2e["pilot_dir"])
    before = sorted(p.name for p in e2e["pilot_dir"].iterdir())
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out]) == 1                       # exactly one pilot run
    assert spy.calls == 0 and sorted(p.name for p in e2e["pilot_dir"].iterdir()) == before                # refused before the panel, nothing written
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out, "--pilot-rerun-dec", "x1"]) == 1
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out, "--pilot-rerun-dec", "DEC-101"]) == 0
    assert spy.calls == 1 and (e2e["pilot_dir"] / "h32_pilot_rerun_DEC-101.json").is_file()
    assert artifacts.sha256_file(e2e["pilot_json"]) == e2e["pilot_sha"]                                  # the first result is untouched
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out, "--pilot-rerun-dec", "DEC-101"]) == 1
    assert "--force" not in H32.build_parser().format_help()


def test_cli_e2e_positive_control_is_bestanden_and_the_run_gives_the_verdict(e2e):
    pc = json.loads((e2e["tmp"] / "pc" / "h32_positive_control.json").read_text(encoding="utf-8"))
    assert pc["bestanden"] is True and pc["line"] == "Positivkontrolle BESTANDEN" and pc["pilot_sha256"] == e2e["pilot_sha"]
    assert pc["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0}                  # DEC-101 E1: the control saw the universe only
    assert (e2e["tmp"] / "pc" / "h32_positive_control.md").read_text(encoding="utf-8").startswith("Positivkontrolle BESTANDEN")
    run = json.loads((e2e["tmp"] / "run" / "h32_run.json").read_text(encoding="utf-8"))
    assert run["registered_sha256"] == e2e["sha"] and run["pilot"]["file_sha256"] == e2e["pilot_sha"] and run["handed"] == ["mom1", "rev_gap"]
    assert run["hypothesis_verdict"]["verdict"] == "PASS" and run["panel"]["max_date"] == C.CUT_TEST
    assert run["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0} and run["null_scaling"]["enabled"] is True
    assert run["panel"]["n_symbols"] <= len(e2e["panel"]["symbols"]) - 2
    assert {e: r["computed"] for e, r in run["results"].items()} == {"H-32_mom1": True, "H-32_mom2": False, "H-32_mom4": False, "H-32_rev_gap": True}
    fp = json.loads((e2e["tmp"] / "run" / "h32_run_fingerprint.json").read_text(encoding="utf-8"))
    assert fp["pilot_sha256"] == e2e["pilot_sha"] and fp["panel_cut"] == C.CUT_TEST and fp["seed"] == 53
    md = (e2e["tmp"] / "run" / "h32_run.md").read_text(encoding="utf-8")
    assert md.isascii() and "F-WEEK" in md and "m = 11" in md


def test_cli_e2e_run_reports_both_p_sources_and_the_binding_one_comes_from_the_pinned_null_replicates(e2e, shrunk):
    from bybit_edge.research.h32_fm8 import pnull
    reg = schema.load_registered_yaml(e2e["yaml"])
    rep = pnull.load_replicates(e2e["tmp"] / "pre" / C.P_REPLICATES_FILE, reg)
    run = json.loads((e2e["tmp"] / "run" / "h32_run.json").read_text(encoding="utf-8"))
    assert run["p_replicates"] == {"p_source": C.P_SOURCE, "file_sha256": reg["fdr"]["replicates_sha256"], "n_reps": P_REPS}
    fp = json.loads((e2e["tmp"] / "run" / "h32_run_fingerprint.json").read_text(encoding="utf-8"))
    assert fp["p_replicates_sha256"] == reg["fdr"]["replicates_sha256"]
    for e in ("H-32_mom1", "H-32_rev_gap"):
        res = run["results"][e]
        ps = []
        for wn in ("W1", "W2"):
            y = res["payload"]["windows"][wn]["y"]
            sc = res["details"][wn]["p_null"]["scaling"]                                                  # DEC-101 E2: the scaled null binds
            expect = pnull.replicate_pvalue(y, est.scaled_replicates(pnull.draws_for(rep, wn, res["variant"]), sc["m"], sc["k"]))
            assert res["details"][wn]["p_null"]["p_value"] == expect["p_value"] and res["details"][wn]["p_null"]["n_reps"] == P_REPS
            assert res["details"][wn]["p_null"]["p_value_unscaled_report_only"] == pnull.replicate_pvalue(y, pnull.draws_for(rep, wn, res["variant"]))["p_value"]
            assert res["details"][wn]["p_null"]["cell"] in ("driftfree", "drifting")
            assert res["details"][wn]["permutation"]["report_only"] is True
            ps.append(expect["p_value"])
        assert res["p_max"] == max(ps) and set(res["p_report_only"]) == {"block_permutation_max_p", "normal_approximation_max_p", "unscaled_null_max_p"}
        assert res["payload"]["constants"]["p_source"] == C.P_SOURCE and res["payload"]["constants"]["n_reps_p"] == P_REPS
    md = (e2e["tmp"] / "run" / "h32_run.md").read_text(encoding="utf-8")
    assert "Null-Replikate" in md and "Permutation / Normal" in md and run["results"]["H-32_mom1"]["verdict"]["bh_report_only"]["m"] == 4
    assert "Skalierte Null (DEC-101 E2)" in md and "Universum linear_usdt_perpetual" in md


def test_cli_run_refuses_missing_or_other_p_replicates_before_the_panel(e2e, shrunk, monkeypatch, tmp_path):
    spy = _env(monkeypatch, e2e["panel"], e2e["repo"])
    base = ["--run", *e2e["reg_args"], *e2e["pil_args"], *RUNNER_ARGS, "--out", str(tmp_path / "r")]
    assert H32.main(base) == 1                                                                              # replicates are mandatory
    good = (e2e["tmp"] / "pre" / C.P_REPLICATES_FILE).read_text(encoding="utf-8")
    other = tmp_path / "p_other.json"
    other.write_text(good.replace("0.", "0.0", 1), encoding="utf-8")                                         # any other byte: other sha256
    assert H32.main([*base, "--p-replicates", str(other)]) == 1
    assert H32.main([*base, "--p-replicates", str(tmp_path / "none.json")]) == 1
    assert H32.main([*base, "--p-replicates", str(tmp_path / "x_L_window_sealed.json")]) == 1
    assert spy.calls == 0 and not (tmp_path / "r").exists()


def test_cli_start_lock_refuses_before_any_panel_byte(e2e, shrunk, monkeypatch, tmp_path):
    spy = _env(monkeypatch, e2e["panel"], e2e["repo"])
    pil = e2e["pil_args"]
    for mode in ("--pilot", "--positive-control", "--run", "--pp3-dry-run"):
        extra = pil if mode in ("--positive-control", "--run") else []
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
    spy = _env(monkeypatch, e2e["panel"], e2e["repo"])
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
    repo = tmp_path / "fresh_repo"                                                                       # a new repository: the pinned pilot directory is free
    _env(monkeypatch, e2e["panel"], repo)
    monkeypatch.setattr(panel_cut, "cut_panel_days", lambda panel, cut_date, **kw: (panel, {"cut_date": cut_date, "n_days_removed": 0}))
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(_pinned(repo))]) == 1
    assert H32.main(["--run", *e2e["reg_args"], *e2e["pil_args"], *e2e["p_args"], *RUNNER_ARGS, "--out", str(tmp_path / "r")]) == 1
    assert H32.main(["--positive-control", *e2e["reg_args"], *e2e["pil_args"], *RUNNER_ARGS, "--out", str(tmp_path / "c")]) == 1
    assert H32.main(["--pp3-dry-run", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(tmp_path / "q")]) == 1
    assert not (_pinned(repo) / "h32_pilot.json").exists() and not (tmp_path / "r" / "h32_run.json").exists()
    assert not (tmp_path / "q").exists()
    assert not (tmp_path / "c" / "h32_positive_control.json").exists()


def test_cli_prelaunch_refuses_cut_dates_inside_the_blind_period_before_loading(e2e, shrunk, monkeypatch, tmp_path):
    spy = _env(monkeypatch, e2e["panel"], e2e["repo"])
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
    with pytest.raises(SystemExit):
        H32.main(["--emit-template", "a", "b", "--pp3-dry-run"])
    with pytest.raises(SystemExit):
        H32.main(["--pilot", "--pp3-dry-run", "--out", str(tmp_path / "o")])
    assert H32.main(["--emit-template", str(e2e["pre_json"]), "data/harvest/x.yaml", "--spread-census", str(_write_census(tmp_path))]) == 1
    _env(monkeypatch, e2e["panel"], e2e["repo"])
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", "data/harvest/h32_never"]) == 1
    assert H32.main(["--pp3-dry-run", *e2e["reg_args"], *RUNNER_ARGS, "--out", "data/harvest/h32_never"]) == 1
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
    repo = tmp_path / "repo"
    spy = _env(monkeypatch, nul["panel"], repo)
    pdir = _pinned(repo)
    reg = ["--registered", str(ypath), "--registered-sha256", sha]
    assert H32.main(["--pilot", *reg, *RUNNER_ARGS, "--out", str(pdir)]) == 0                         # GL-012 (Pilot) is a result, not an abort
    pilot = json.loads((pdir / "h32_pilot.json").read_text(encoding="utf-8"))
    assert pilot["status"] == "GL-012 (Pilot)" and pilot["handed"] == []
    pil = ["--pilot-result", str(pdir / "h32_pilot.json"), "--pilot-result-sha256", artifacts.sha256_file(pdir / "h32_pilot.json")]
    assert H32.main(["--positive-control", *reg, *pil, *RUNNER_ARGS, "--out", str(tmp_path / "pc")]) == 1             # nothing handed over: no control, no test
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
    repo = tmp_path / "repo"
    _env(monkeypatch, e2e["panel"], repo)
    assert H32.main(["--pilot", "--registered", str(p), "--registered-sha256", sha, *RUNNER_ARGS, "--out", str(_pinned(repo))]) == 0
    pj = _pinned(repo) / "h32_pilot.json"
    rc = H32.main(["--positive-control", "--registered", str(p), "--registered-sha256", sha, "--pilot-result", str(pj),
                   "--pilot-result-sha256", artifacts.sha256_file(pj), *RUNNER_ARGS, "--out", str(tmp_path / "pc")])
    assert rc == 3
    rep = json.loads((tmp_path / "pc" / "h32_positive_control.json").read_text(encoding="utf-8"))
    assert rep["bestanden"] is False and rep["line"] == "Positivkontrolle NICHT BESTANDEN"
    assert (tmp_path / "pc" / "h32_positive_control.md").read_text(encoding="utf-8").startswith("Positivkontrolle NICHT BESTANDEN")


# ============================================================================
# DEC-101: pinned pilot directory and search, runner pins, universe pin, PP3 dry run
# ============================================================================

def _rehashed_yaml(tmp_path: Path, e2e, mutate, name: str = "mutated.yaml"):
    reg = yaml.safe_load(e2e["yaml"].read_text(encoding="utf-8"))
    mutate(reg)
    p = tmp_path / name
    p.write_text(yaml.safe_dump(reg, sort_keys=False), encoding="utf-8")
    return ["--registered", str(p), "--registered-sha256", artifacts.sha256_file(p)]


def test_cli_dec101_pilot_refuses_every_out_other_than_the_pinned_directory(e2e, shrunk, monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    spy = _env(monkeypatch, e2e["panel"], repo)
    for bad in (tmp_path / "pilot", repo / C.RUNS_REL / "h32_pilot_v2", repo / C.RUNS_REL, _pinned(repo) / "sub", Path("data/harvest/h32_pilot_v1")):
        assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(bad)]) == 1
        assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(bad), "--pilot-rerun-dec", "DEC-102"]) == 1     # not even with a DEC
    assert spy.calls == 0 and not repo.exists() and not (tmp_path / "pilot").exists() and not Path("data/harvest/h32_pilot_v1").exists()
    # a different pin in the YAML moves the one allowed directory (the comparison is against the registration)
    moved = "scinance3-impl/state/runs/h32_pilot_moved"
    reg2 = _rehashed_yaml(tmp_path, e2e, lambda r: r["pilot_window"].__setitem__("out_dir", moved))
    assert H32.main(["--pilot", *reg2, *RUNNER_ARGS, "--out", str(_pinned(repo))]) == 1 and spy.calls == 0
    assert H32.main(["--pilot", *reg2, *RUNNER_ARGS, "--out", str(repo / moved)]) == 0 and spy.calls == 1
    assert (repo / moved / "h32_pilot.json").is_file() and not _pinned(repo).exists()


def test_cli_dec101_an_earlier_pilot_elsewhere_below_runs_blocks_a_new_directory_unless_a_dec_allows_it(e2e, shrunk, monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    spy = _env(monkeypatch, e2e["panel"], repo)
    elsewhere = repo / C.RUNS_REL / "h32_pilot_attempt_0" / "h32_pilot.json"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text(e2e["pilot_json"].read_text(encoding="utf-8"), encoding="utf-8")                # same registered_sha256
    assert json.loads(elsewhere.read_text(encoding="utf-8"))["registered_sha256"] == e2e["sha"]
    out = str(_pinned(repo))
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out]) == 1                    # new directory, earlier pilot elsewhere
    assert spy.calls == 0 and not _pinned(repo).exists()
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out, "--pilot-rerun-dec", "x1"]) == 1
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out, "--pilot-rerun-dec", "DEC-102"]) == 0   # allowed with a DEC (same prefix rule)
    assert spy.calls == 1 and (_pinned(repo) / "h32_pilot_rerun_DEC-102.json").is_file() and not (_pinned(repo) / "h32_pilot.json").exists()
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", out, "--pilot-rerun-dec", "DEC-102"]) == 1  # a further re-run needs its own DEC
    # a pilot result of ANOTHER registration below runs does not block
    repo2 = tmp_path / "repo2"
    other = repo2 / C.RUNS_REL / "x" / "h32_pilot.json"
    other.parent.mkdir(parents=True)
    other.write_text(json.dumps({"registered_sha256": "ab" * 32}), encoding="utf-8")
    monkeypatch.setattr(H32, "REPO_ROOT", repo2)
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(_pinned(repo2))]) == 0


def test_cli_dec101_runner_pins_are_checked_in_every_mode_before_the_panel(e2e, shrunk, monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    spy = _env(monkeypatch, e2e["panel"], repo)
    good = dict(zip(RUNNER_ARGS[0::2], RUNNER_ARGS[1::2]))
    variants = [["--as-of", "2026-10-21"], ["--start-year", "2022"], ["--end-year", "2027"]]
    modes = {"--pilot": ["--out", str(_pinned(repo))], "--pp3-dry-run": ["--out", str(tmp_path / "pp3")],
             "--positive-control": [*e2e["pil_args"], "--out", str(tmp_path / "pc")],
             "--run": [*e2e["pil_args"], *e2e["p_args"], "--out", str(tmp_path / "run")]}
    for mode, extra in modes.items():
        for over in variants:
            args = {**good, **{over[0]: over[1]}}
            argv = [mode, *e2e["reg_args"], *extra] + [x for kv in args.items() for x in kv] + ["--allow-partial"]
            assert H32.main(argv) == 1, (mode, over)
        # --allow-partial omitted, --as-of omitted (today's date is not the pin)
        no_partial = [mode, *e2e["reg_args"], *extra] + [x for kv in good.items() for x in kv]
        assert H32.main(no_partial) == 1
        no_as_of = [mode, *e2e["reg_args"], *extra, "--start-year", "2021", "--end-year", "2026", "--allow-partial"]
        assert H32.main(no_as_of) == 1
    assert spy.calls == 0 and not repo.exists() and not (tmp_path / "pp3").exists() and not (tmp_path / "pc").exists() and not (tmp_path / "run").exists()


def test_cli_dec101_runner_mismatch_message_names_both_values(e2e, shrunk, monkeypatch, tmp_path, capsys):
    _env(monkeypatch, e2e["panel"], tmp_path / "repo")
    assert H32.main(["--pp3-dry-run", *e2e["reg_args"], "--as-of", "2026-10-21", "--start-year", "2021", "--end-year", "2026", "--allow-partial",
                     "--out", str(tmp_path / "pp3")]) == 1
    err = capsys.readouterr().err
    assert "Runner-Pin" in err and "'2026-09-28'" in err and "'2026-10-21'" in err and "as_of" in err
    # a no-handover run does not read the panel and needs no panel arguments
    nul = F.get_bundle("null")
    ypath = tmp_path / "nul.yaml"
    ypath.write_text(yaml.safe_dump(nul["registered"], sort_keys=False), encoding="utf-8")
    sha = artifacts.sha256_file(ypath)
    repo = tmp_path / "repo_nul"
    _env(monkeypatch, nul["panel"], repo)
    reg = ["--registered", str(ypath), "--registered-sha256", sha]
    assert H32.main(["--pilot", *reg, *RUNNER_ARGS, "--out", str(_pinned(repo))]) == 0
    pj = _pinned(repo) / "h32_pilot.json"
    assert H32.main(["--run", *reg, "--pilot-result", str(pj), "--pilot-result-sha256", artifacts.sha256_file(pj), "--out", str(tmp_path / "run")]) == 0


def test_cli_dec101_universe_pin_wrong_rule_missing_block_or_other_counts_are_loud_fails(e2e, shrunk, monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    spy = _env(monkeypatch, e2e["panel"], repo)
    out = str(_pinned(repo))
    for i, mutate in enumerate((lambda r: r["universe"].__setitem__("rule", "category_linear"), lambda r: r.pop("universe"),
                                lambda r: r["null_scaling"].__setitem__("enabled", False), lambda r: r.pop("runner"),
                                lambda r: r["data_fingerprints"].pop("delisted_tree_sha256"))):
        reg = _rehashed_yaml(tmp_path, e2e, mutate, name=f"m{i}.yaml")
        assert H32.main(["--pilot", *reg, *RUNNER_ARGS, "--out", out]) == 1
        assert H32.main(["--pp3-dry-run", *reg, *RUNNER_ARGS, "--out", str(tmp_path / "pp3")]) == 1
    assert spy.calls == 0 and not repo.exists() and not (tmp_path / "pp3").exists()                    # schema pre-flight: before the panel
    # the counts frozen at the Vorlauf differ from the observed ones: other panel -> loud fail AFTER loading, no result
    reg = _rehashed_yaml(tmp_path, e2e, lambda r: r["universe"]["excluded_at_prelaunch"].__setitem__("usdc_perp", 7), name="counts.yaml")
    assert H32.main(["--pilot", *reg, *RUNNER_ARGS, "--out", out]) == 1
    assert H32.main(["--pp3-dry-run", *reg, *RUNNER_ARGS, "--out", str(tmp_path / "pp3")]) == 1
    assert spy.calls == 2 and not (_pinned(repo) / "h32_pilot.json").exists() and not (tmp_path / "pp3" / C.PP3_FILE).exists()


def test_cli_dec101_pp3_dry_run_passes_computes_no_ic_and_fails_on_a_deviating_pin(e2e, shrunk, monkeypatch, tmp_path):
    from bybit_edge.research.wp13_xsec import ic
    spy = _env(monkeypatch, e2e["panel"], tmp_path / "repo")

    def boom(*a, **k):
        raise AssertionError("an IC function was called in the PP3 dry run")
    for name in ("weekly_ic_series", "apply_beta_control", "fm_neutralize_outcome"):
        monkeypatch.setattr(ic, name, boom)
    data = json.loads((e2e["tmp"] / "pp3" / C.PP3_FILE).read_text(encoding="utf-8"))                     # the e2e run (before the pilot)
    assert data["schema"] == C.PP3_SCHEMA and data["ok"] is True and data["registered_sha256"] == e2e["sha"]
    assert all(r["ok"] and r["k_fm8_series_sha256"] == r["pinned_k_fm8_series_sha256"] for r in data["windows"].values())
    assert data["universe"]["excluded"] == {"usdc_perp": 1, "dated_future": 1, "other": 0} and "excluded_symbols" not in data["universe"]
    assert H32.main(["--pp3-dry-run", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(tmp_path / "again")]) == 0       # again, with every IC forbidden
    assert spy.calls == 1 and [p.name for p in (tmp_path / "again").iterdir()] == [C.PP3_FILE]
    reg = _rehashed_yaml(tmp_path, e2e, lambda r: r["pilot_window"]["frozen_v6"].__setitem__("k_fm8_series_sha256", "11" * 32))
    assert H32.main(["--pp3-dry-run", *reg, *RUNNER_ARGS, "--out", str(tmp_path / "bad")]) == 1
    bad = json.loads((tmp_path / "bad" / C.PP3_FILE).read_text(encoding="utf-8"))                      # the failure is documented in the small file
    assert bad["ok"] is False and bad["windows"]["P"]["ok"] is False and bad["windows"]["W1"]["ok"] and bad["windows"]["W2"]["ok"]
    reg2 = _rehashed_yaml(tmp_path, e2e, lambda r: r["windows"]["W2"]["frozen_v6"].__setitem__("k_fm8_series_sha256", "22" * 32), name="w2.yaml")
    assert H32.main(["--pp3-dry-run", *reg2, *RUNNER_ARGS, "--out", str(tmp_path / "bad2")]) == 1
    assert json.loads((tmp_path / "bad2" / C.PP3_FILE).read_text(encoding="utf-8"))["windows"]["W2"]["ok"] is False


def test_cli_dec101_a_pp3_dry_run_never_counts_as_a_pilot_result(e2e, shrunk, monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    spy = _env(monkeypatch, e2e["panel"], repo)
    assert H32.main(["--pp3-dry-run", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(_pinned(repo))]) == 0     # even into the pilot directory
    assert [p.name for p in _pinned(repo).iterdir()] == [C.PP3_FILE]
    assert H32.main(["--pilot", *e2e["reg_args"], *RUNNER_ARGS, "--out", str(_pinned(repo))]) == 0         # the one pilot is still free
    assert spy.calls == 2 and (_pinned(repo) / "h32_pilot.json").is_file() and (_pinned(repo) / C.PP3_FILE).is_file()
