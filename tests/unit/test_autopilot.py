"""Autopilot (scinance3-impl/handoff_local/autopilot.py): Auftrags-Schema,
Erledigt-Erkennung, Argumentvektor und ein End-to-End-Durchlauf gegen ein
temporaeres Git-Origin (PowerShell-Aufruf gemockt)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scinance3-impl" / "handoff_local" / "autopilot.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"autopilot_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ap = _load(SRC)


# ---------------------------------------------------------------- schema

def test_parse_valid_minimal():
    job = ap.parse_auftrag(json.dumps({"id": "2026-09-26_wp13a", "tasks": ["wp13a"]}))
    assert job == {"id": "2026-09-26_wp13a", "tasks": ["wp13a"], "registered": None,
                   "registered_sha256": None, "wp10b_resume": False, "skip_if_done_since": None}


@pytest.mark.parametrize("payload, match", [
    ("not json", "JSON"),
    (json.dumps(["wp13a"]), "Objekt"),
    (json.dumps({"id": "x", "tasks": ["rm -rf /"]}), "nicht erlaubt"),
    (json.dumps({"id": "x; calc", "tasks": ["wp13a"]}), "id"),
    (json.dumps({"id": "x", "tasks": []}), "tasks"),
    (json.dumps({"id": "x", "tasks": ["wp13a"], "cmd": "evil"}), "unbekannte"),
    (json.dumps({"id": "x", "tasks": ["wp13run"]}), "wp13run braucht"),
    (json.dumps({"id": "x", "tasks": ["wp13run"], "registered": "../../x.yaml",
                 "registered_sha256": "a" * 64}), "relativer"),
    (json.dumps({"id": "x", "tasks": ["wp13run"], "registered": "data/harvest/x.yaml",
                 "registered_sha256": "a" * 64}), "relativer"),
    (json.dumps({"id": "x", "tasks": ["wp13run"], "registered": "r.yaml",
                 "registered_sha256": "xyz"}), "64 Hex"),
    (json.dumps({"id": "x", "tasks": ["wp10b"], "wp10b_resume": "yes"}), "true/false"),
    (json.dumps({"id": "x", "tasks": ["wp13a"], "skip_if_done_since": "HEAD~1"}), "Commit-Hash"),
])
def test_parse_rejects_loudly(payload, match):
    with pytest.raises(ap.AuftragError, match=match):
        ap.parse_auftrag(payload)


def test_done_tasks_from_subjects():
    subjects = [
        "results(nacht 20260925_1521): wp13a rc=1 dauer_min=123",
        "results(nacht 20260924_1128): diag rc=0 dauer_min=0; wp10b rc=0 dauer_min=500; wp13a rc=0 dauer_min=226",
        "feat(x): wp13a rc=0 in a normal commit does not count",
        "results(nacht 20260926_0100): wp7 rc=0 dauer_min=5 [auftrag a1]",
    ]
    assert ap.done_tasks_from_subjects(subjects[:1], ["wp13a"]) == set()
    assert ap.done_tasks_from_subjects(subjects, ["wp13a", "wp10b", "wp7", "wp12"]) == {"wp13a", "wp10b", "wp7"}
    assert ap.done_tasks_from_subjects([subjects[2]], ["wp13a"]) == set()


def test_nacht_arguments_vector():
    job = ap.parse_auftrag(json.dumps({"id": "j1", "tasks": ["wp13run", "diag"],
                                       "registered": "scinance3-impl/state/reg/h28.yaml",
                                       "registered_sha256": "b" * 64, "wp10b_resume": True}))
    args = ap.nacht_arguments(job, ["wp13run", "diag"])
    assert args == ["-Tasks", "wp13run,diag", "-AuftragId", "j1",
                    "-Registered", "scinance3-impl\\state\\reg\\h28.yaml",
                    "-RegisteredSha256", "b" * 64, "-Wp10bResume"]


# ---------------------------------------------------------------- end to end

def _run(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repos(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git fehlt")
    origin = tmp_path / "origin.git"
    _run(tmp_path, "init", "-q", "--bare", str(origin))
    seed = tmp_path / "seed"
    _run(tmp_path, "clone", "-q", str(origin), str(seed))
    _run(seed, "config", "user.email", "t@t"); _run(seed, "config", "user.name", "t")
    _run(seed, "checkout", "-q", "-b", ap.BRANCH)
    hl = seed / "scinance3-impl" / "handoff_local"
    hl.mkdir(parents=True)
    shutil.copy(SRC, hl / "autopilot.py")
    (hl / "nacht.ps1").write_text("# stub\n")
    (seed / ".gitignore").write_text("data/\n")
    _run(seed, "add", "-A"); _run(seed, "commit", "-q", "-m", "init")
    _run(seed, "push", "-q", "origin", ap.BRANCH)
    pc = tmp_path / "pc"
    _run(tmp_path, "clone", "-q", "-b", ap.BRANCH, str(origin), str(pc))
    _run(pc, "config", "user.email", "pc@t"); _run(pc, "config", "user.name", "pc")
    return seed, pc


def _queue(seed, payload):
    q = seed / "scinance3-impl" / "state" / "queue"
    q.mkdir(parents=True, exist_ok=True)
    (q / "auftrag.json").write_text(json.dumps(payload))
    _run(seed, "add", "-A"); _run(seed, "commit", "-q", "-m", "queue")
    _run(seed, "push", "-q", "origin", ap.BRANCH)


def test_end_to_end_runs_once_and_marks_started(repos, monkeypatch):
    seed, pc = repos
    mod = _load(pc / "scinance3-impl" / "handoff_local" / "autopilot.py")
    calls = []
    real_run = subprocess.run

    def fake_run(cmd, *a, **kw):
        if cmd and cmd[0] == "powershell":
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        kw.pop("creationflags", None)
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    assert mod.main() == 0 and calls == []          # no job yet
    _queue(seed, {"id": "job-1", "tasks": ["wp13a", "diag"]})
    assert mod.main() == 0
    assert len(calls) == 1
    assert calls[0][calls[0].index("-Tasks") + 1] == "wp13a,diag"
    assert calls[0][calls[0].index("-AuftragId") + 1] == "job-1"
    # started marker pushed to origin
    _run(seed, "pull", "-q", "origin", ap.BRANCH)
    assert (seed / "scinance3-impl" / "state" / "queue" / "gestartet" / "job-1.json").is_file()
    # same job never runs twice on this machine
    assert mod.main() == 0 and len(calls) == 1


def test_end_to_end_skips_tasks_done_since(repos, monkeypatch):
    seed, pc = repos
    base = _run(seed, "rev-parse", "--short", "HEAD").strip()
    (seed / "x.txt").write_text("r")
    _run(seed, "add", "-A")
    _run(seed, "commit", "-q", "-m", "results(nacht 20260926_0100): wp13a rc=0 dauer_min=200")
    _run(seed, "push", "-q", "origin", ap.BRANCH)
    _queue(seed, {"id": "job-2", "tasks": ["wp13a", "diag"], "skip_if_done_since": base})
    mod = _load(pc / "scinance3-impl" / "handoff_local" / "autopilot.py")
    calls = []
    real_run = subprocess.run

    def fake_run(cmd, *a, **kw):
        if cmd and cmd[0] == "powershell":
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        kw.pop("creationflags", None)
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.main() == 0
    assert calls[0][calls[0].index("-Tasks") + 1] == "diag"


def test_rejected_job_never_runs(repos, monkeypatch):
    seed, pc = repos
    _queue(seed, {"id": "evil", "tasks": ["wp13a"], "cmd": "del *"})
    mod = _load(pc / "scinance3-impl" / "handoff_local" / "autopilot.py")
    calls = []
    real_run = subprocess.run

    def fake_run(cmd, *a, **kw):
        if cmd and cmd[0] == "powershell":
            calls.append(cmd)
        kw.pop("creationflags", None)
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.main() == 1 and calls == []
    log = (pc / "data" / "autopilot" / "autopilot.log").read_text()
    assert "ABGELEHNT" in log
