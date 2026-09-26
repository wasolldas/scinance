"""Scinance Autopilot -- fuehrt Auftraege aus dem Git-Branch unbeaufsichtigt aus.

Laeuft auf der Nutzer-Maschine als geplante Aufgabe "Scinance Autopilot"
(alle 15 Minuten, ``pythonw.exe`` -> kein Konsolenfenster; Installation:
``install_autopilot.ps1``). Je Durchlauf:

1. Laeuft bereits ein ``nacht.ps1`` (Sperrdatei mit lebender PID): nichts tun.
2. Unveroeffentlichte lokale Commits (z. B. ein frueherer Push schlug fehl):
   nachschieben.
3. ``git fetch``; liegt auf ``origin/<Branch>`` ein Auftrag
   ``scinance3-impl/state/queue/auftrag.json`` mit neuer ID (kein
   Erledigt-Marker im Branch, kein lokaler Start-Marker), dann:
   ``git pull``, Start-Marker committen und pushen, ``nacht.ps1`` mit den
   Aufgaben des Auftrags starten (versteckt), am Ende schreibt und pusht
   ``nacht.ps1`` Ergebnisse plus Erledigt-Marker.

Sicherheit: Der Auftrag ist DATEN, kein Code. Erlaubt sind nur die
Aufgabennamen aus ``ALLOWED_TASKS`` und wenige, streng gepruefte Parameter;
alles andere wird abgelehnt (laut, im Log). Ausgefuehrt wird nur Code aus
dem eigenen Branch, auf den nur der Eigentuemer (und seine Claude-Sitzung)
pushen kann. Jede Auftrags-ID laeuft je Maschine hoechstens einmal.
Nie ein Schreibzugriff unter ``data/harvest``; keine Keys, keine Orders.

Protokoll: ``data/autopilot/autopilot.log`` (nicht versioniert).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

BRANCH = "claude/subagent-prd-development-T16fE"
QUEUE_REL = "scinance3-impl/state/queue/auftrag.json"
DONE_DIR_REL = "scinance3-impl/state/queue/erledigt"
STARTED_DIR_REL = "scinance3-impl/state/queue/gestartet"
LOCK_REL = "scinance3-impl/state/nacht.lock"
NACHT_REL = "scinance3-impl/handoff_local/nacht.ps1"
ALLOWED_TASKS = frozenset({"wp13a", "wp10b", "wp7", "wp10a2", "wp12", "wp13run", "diag"})
MAX_TASKS = 10

_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_REL_PATH_RE = re.compile(r"^[A-Za-z0-9_./-]{1,200}$")
_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


class AuftragError(ValueError):
    """Ein Auftrag verletzt das erlaubte Schema (laut, nie still ausgefuehrt)."""


def parse_auftrag(text: str) -> dict[str, Any]:
    """Validate the queue file; returns a normalised dict or raises AuftragError."""
    try:
        raw = json.loads(text)
    except ValueError as exc:
        raise AuftragError(f"auftrag.json ist kein gueltiges JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise AuftragError("auftrag.json muss ein JSON-Objekt sein")
    allowed_keys = {"id", "tasks", "registered", "registered_sha256", "wp10b_resume",
                    "skip_if_done_since", "zweck"}
    unknown = set(raw) - allowed_keys
    if unknown:
        raise AuftragError(f"unbekannte Felder: {sorted(unknown)}")
    job_id = raw.get("id")
    if not isinstance(job_id, str) or not _ID_RE.match(job_id):
        raise AuftragError(f"ungueltige id: {job_id!r}")
    tasks = raw.get("tasks")
    if not isinstance(tasks, list) or not tasks or len(tasks) > MAX_TASKS:
        raise AuftragError("tasks muss eine nicht-leere Liste (max. 10) sein")
    for t in tasks:
        if t not in ALLOWED_TASKS:
            raise AuftragError(f"Aufgabe nicht erlaubt: {t!r} (erlaubt: {sorted(ALLOWED_TASKS)})")
    out: dict[str, Any] = {"id": job_id, "tasks": list(tasks), "registered": None,
                           "registered_sha256": None, "wp10b_resume": False,
                           "skip_if_done_since": None}
    reg = raw.get("registered")
    if reg is not None:
        if (not isinstance(reg, str) or not _REL_PATH_RE.match(reg) or ".." in reg
                or reg.startswith("/") or "harvest" in reg):
            raise AuftragError(f"registered muss ein relativer Repo-Pfad sein: {reg!r}")
        out["registered"] = reg
    sha = raw.get("registered_sha256")
    if sha is not None:
        if not isinstance(sha, str) or not _HEX64_RE.match(sha):
            raise AuftragError("registered_sha256 muss 64 Hex-Zeichen haben")
        out["registered_sha256"] = sha
    if "wp13run" in tasks and (out["registered"] is None or out["registered_sha256"] is None):
        raise AuftragError("wp13run braucht registered und registered_sha256")
    res = raw.get("wp10b_resume", False)
    if not isinstance(res, bool):
        raise AuftragError("wp10b_resume muss true/false sein")
    out["wp10b_resume"] = res
    since = raw.get("skip_if_done_since")
    if since is not None:
        if not isinstance(since, str) or not _SHA_RE.match(since):
            raise AuftragError("skip_if_done_since muss ein Commit-Hash sein")
        out["skip_if_done_since"] = since
    return out


def done_tasks_from_subjects(subjects: Iterable[str], tasks: Iterable[str]) -> set[str]:
    """Tasks that a ``results(nacht ...)`` commit already reports with rc=0."""
    done: set[str] = set()
    wanted = set(tasks)
    for subj in subjects:
        if not subj.startswith("results(") or "):" not in subj:
            continue
        body = subj.split("):", 1)[1].split("[auftrag", 1)[0]
        for part in body.split(";"):
            words = part.split()
            if len(words) >= 2 and words[0] in wanted and words[1] == "rc=0":
                done.add(words[0])
    return done


def nacht_arguments(job: dict[str, Any], tasks: list[str]) -> list[str]:
    """PowerShell argument vector for nacht.ps1 (never a free-form string)."""
    args = ["-Tasks", ",".join(tasks), "-AuftragId", job["id"]]
    if job.get("registered"):
        args += ["-Registered", job["registered"].replace("/", "\\")]
    if job.get("registered_sha256"):
        args += ["-RegisteredSha256", job["registered_sha256"]]
    if job.get("wp10b_resume"):
        args.append("-Wp10bResume")
    return args


# ----------------------------------------------------------------------------
# side-effecting helpers (Windows user PC)
# ----------------------------------------------------------------------------

def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _log(root: Path, msg: str) -> None:
    d = root / "data" / "autopilot"
    d.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(d / "autopilot.log", "a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {msg}\n")


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                          check=check, creationflags=_CREATE_NO_WINDOW)


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                           text=True, creationflags=_CREATE_NO_WINDOW)
        return str(pid) in r.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _lock_alive(root: Path) -> bool:
    lock = root / LOCK_REL
    if not lock.is_file():
        return False
    txt = lock.read_text(encoding="utf-8", errors="replace").strip()
    return txt.isdigit() and _pid_alive(int(txt))


def _push_pending(root: Path) -> None:
    ahead = _git(root, "rev-list", "--count", f"origin/{BRANCH}..HEAD", check=False).stdout.strip()
    if ahead.isdigit() and int(ahead) > 0:
        _git(root, "pull", "--rebase", "--autostash", "origin", BRANCH, check=False)
        r = _git(root, "push", "origin", BRANCH, check=False)
        _log(root, f"Nachschub-Push ({ahead} Commits): rc={r.returncode}")


def main() -> int:
    root = _root()
    if _lock_alive(root):
        _log(root, "nacht.ps1 laeuft bereits - warte")
        return 0
    _git(root, "fetch", "-q", "origin", BRANCH, check=False)
    _push_pending(root)
    show = _git(root, "show", f"origin/{BRANCH}:{QUEUE_REL}", check=False)
    if show.returncode != 0:
        return 0  # kein Auftrag
    try:
        job = parse_auftrag(show.stdout)
    except AuftragError as exc:
        marker = root / "data" / "autopilot" / "abgelehnt.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)
        if not marker.is_file() or marker.read_text(encoding="utf-8") != show.stdout:
            _log(root, f"AUFTRAG ABGELEHNT: {exc}")
            marker.write_text(show.stdout, encoding="utf-8")
        return 1
    done_on_branch = _git(root, "cat-file", "-e", f"origin/{BRANCH}:{DONE_DIR_REL}/{job['id']}.json",
                          check=False).returncode == 0
    local_started = root / "data" / "autopilot" / f"gestartet_{job['id']}"
    if done_on_branch or local_started.is_file():
        return 0
    tasks = list(job["tasks"])
    if job["skip_if_done_since"]:
        subj = _git(root, "log", "--format=%s", f"{job['skip_if_done_since']}..origin/{BRANCH}",
                    check=False).stdout.splitlines()
        already = done_tasks_from_subjects(subj, tasks)
        if already:
            _log(root, f"Auftrag {job['id']}: bereits erledigt seit {job['skip_if_done_since']}: {sorted(already)}")
        tasks = [t for t in tasks if t not in already]

    _git(root, "pull", "-q", "--rebase", "--autostash", "origin", BRANCH, check=False)
    local_started.parent.mkdir(parents=True, exist_ok=True)
    local_started.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    started = root / STARTED_DIR_REL / f"{job['id']}.json"
    started.parent.mkdir(parents=True, exist_ok=True)
    started.write_text(json.dumps({"id": job["id"], "tasks": tasks,
                                   "gestartet": datetime.now(timezone.utc).isoformat(),
                                   "rechner": os.environ.get("COMPUTERNAME", "")}, indent=1),
                       encoding="ascii")
    _git(root, "add", str(started.relative_to(root)).replace("\\", "/"), check=False)
    _git(root, "commit", "-q", "-m", f"autopilot: Auftrag {job['id']} gestartet ({','.join(tasks) or '-'})",
         check=False)
    _git(root, "push", "-q", "origin", BRANCH, check=False)
    _log(root, f"Auftrag {job['id']} gestartet: {tasks}")

    if not tasks:
        done = root / DONE_DIR_REL / f"{job['id']}.json"
        done.parent.mkdir(parents=True, exist_ok=True)
        done.write_text(json.dumps({"id": job["id"], "ergebnisse": ["nichts zu tun (bereits erledigt)"]},
                                   indent=1), encoding="ascii")
        _git(root, "add", str(done.relative_to(root)).replace("\\", "/"), check=False)
        _git(root, "commit", "-q", "-m", f"results(autopilot): Auftrag {job['id']} nichts zu tun", check=False)
        _push_pending(root)
        return 0

    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
           str(root / NACHT_REL), "-RepoRoot", str(root)] + nacht_arguments(job, tasks)
    rc = subprocess.run(cmd, cwd=root, creationflags=_CREATE_NO_WINDOW).returncode
    _log(root, f"Auftrag {job['id']} beendet: nacht.ps1 rc={rc}")
    _git(root, "fetch", "-q", "origin", BRANCH, check=False)
    _push_pending(root)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 -- pythonw has no console; never die silently
        try:
            _log(_root(), f"AUSNAHME: {exc!r}")
        finally:
            sys.exit(3)
