"""Shared pre-checks of the modes: data fingerprints (PP2 / P3), the stage-P lock files, window pins (PP3 / P4), and the
DEC-101 pins: runner arguments (E4), universe (E1), the one pilot directory and the pilot search (E3)."""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from . import artifacts
from . import constants as C
from . import weekly as wkl
from .errors import DataFingerprintError, PilotLockError, PinError, RunnerPinError, UniverseError

__all__ = ["check_data_fingerprints", "check_window_pins", "check_rerun_lock", "pilot_prefix", "DEC_PATTERN",
           "check_runner_pins", "check_universe_pin", "check_pilot_out_dir", "find_pilot_results", "pilot_dir",
           "attempt_marker_path", "write_attempt_marker"]

DEC_PATTERN = re.compile(r"^DEC-\d+$")


def check_data_fingerprints(registered: dict[str, Any], observed: dict[str, Any] | None) -> None:
    """The loaded panel's fingerprints (union range, ``delisting_dates.json``, the Data-Harvest delisting register of DEC-100
    and -- DEC-101 E4 (A-3) -- the file-level sha256 of the delisted tree, now a MANDATORY pin) must equal the registered ones
    (PP2 / P3).  ``observed`` ``None`` (not checkable) is a loud fail as well."""
    reg = registered.get("data_fingerprints")
    if not isinstance(reg, dict):
        raise DataFingerprintError("registered YAML without data_fingerprints")
    if observed is None:
        raise DataFingerprintError("data fingerprints of the loaded panel were not supplied -- not checkable")
    keys = ["union_range_fingerprint", "delisting_dates_sha256", "delisting_register_sha256", "delisted_tree_sha256"]
    if reg.get("delisted_tree_sha256") is None:                       # DEC-101 E4: no pin is no longer "not compared"
        raise DataFingerprintError("data_fingerprints.delisted_tree_sha256 is not pinned in the registration (DEC-101 E4)")
    for key in keys:
        if str(observed.get(key)).lower() != str(reg.get(key)).lower():
            raise DataFingerprintError(f"data fingerprint {key} differs: panel {observed.get(key)!r} vs registered {reg.get(key)!r}")


def check_window_pins(win: wkl.Window, registered: dict[str, Any]) -> None:
    """PP3 (pilot) / P4 (test): ``w_judged`` of the loaded window equals the registered / frozen number, the K_fm8 series
    equals the one the v6 constants were frozen on (same panel, same cut), and the K minimum holds."""
    if win.name == "P":
        pw = registered["pilot_window"]
        if win.w_judged != int(pw["w_pilot"]) or win.w_judged != C.W_PILOT:
            raise PinError(f"pilot window: w_pilot {pw['w_pilot']} vs loaded {win.w_judged} vs frozen {C.W_PILOT}")
        if win.weeks[0] != pw["first_formation_week"] or win.weeks[win.w_judged - 1] != pw["last_formation_week"]:
            raise PinError(f"pilot formation weeks {win.weeks[0]}..{win.weeks[win.w_judged - 1]} differ from the registration")
        sha = pw["frozen_v6"]["k_fm8_series_sha256"]
        k_min = int(pw["k_min_rule"])
    else:
        w = registered["windows"][win.name]
        if win.w_judged != int(w["w_judged"]) or win.w_judged != C.W_JUDGED[win.name]:
            raise PinError(f"window {win.name}: w_judged {w['w_judged']} vs loaded {win.w_judged} vs frozen {C.W_JUDGED[win.name]}")
        sha = w["frozen_v6"]["k_fm8_series_sha256"]
        k_min = C.K_MIN[win.name]
    wkl.check_k_min(win, k_min)
    got = wkl.int_series_sha256(wkl.k_fm8_series(win))
    if got != sha:
        raise PinError(f"window {win.name}: the K_fm8 series ({got[:12]}...) differs from the one the v6 constants were frozen on "
                       f"({sha[:12]}...) -- other panel or other cut")


def _norm_runner_value(key: str, value: Any) -> Any:
    if key == "as_of":
        if isinstance(value, date) and not hasattr(value, "hour"):
            return value.isoformat()
        return None if value in (None, "") else str(value)
    if key == "allow_partial":
        return bool(value)
    return value if value is None else int(value)


def check_runner_pins(registered: dict[str, Any], cli: dict[str, Any]) -> None:
    """DEC-101 E4 (A-3, B-9.6): the CLI arguments of the mode (``as_of``, ``start_year``, ``end_year``, ``allow_partial``) must
    equal the registered ``runner`` pins -- they determine the union-range fingerprint.  Checked BEFORE the panel is loaded; a
    loud fail names both values of every differing argument (an omitted ``--as-of`` is today's date, not the pin)."""
    pin = registered.get("runner")
    if not isinstance(pin, dict):
        raise RunnerPinError("registered YAML without a runner block (DEC-101 E4)")
    bad = []
    for key in ("as_of", "start_year", "end_year", "allow_partial"):
        want, got = _norm_runner_value(key, pin.get(key)), _norm_runner_value(key, cli.get(key))
        if want != got:
            bad.append(f"{key}: registered {want!r} vs CLI {got!r}")
    if bad:
        raise RunnerPinError("CLI arguments differ from the registered runner pins (DEC-101 E4; they determine the union-range "
                             "fingerprint): " + "; ".join(bad))


def check_universe_pin(registered: dict[str, Any], report: dict[str, Any] | None) -> None:
    """DEC-101 E1: the universe report of the loaded panel must be of the registered rule (``universe.rule``) and must report the
    excluded counts that were frozen at the Vorlauf (``universe.excluded_at_prelaunch``: the files are fingerprint-pinned, so
    the counts cannot differ)."""
    pin = registered.get("universe")
    if not isinstance(pin, dict):
        raise UniverseError("registered YAML without a universe block (DEC-101 E1)")
    if not isinstance(report, dict):
        raise UniverseError("no universe report: the panel was not restricted to the registered universe (DEC-101 E1)")
    if report.get("rule") != pin.get("rule"):
        raise UniverseError(f"universe rule differs: registered {pin.get('rule')!r} vs applied {report.get('rule')!r}")
    for cls in C.UNIVERSE_CLASSES:
        want, got = pin["excluded_at_prelaunch"].get(cls), (report.get("excluded") or {}).get(cls)
        if want != got:
            raise UniverseError(f"universe.excluded_at_prelaunch[{cls}]: registered {want!r} vs observed {got!r} -- other panel")


def pilot_dir(registered: dict[str, Any], repo_root: Path | str) -> Path:
    """The pinned pilot directory (``pilot_window.out_dir``) resolved against the repository root (DEC-101 E3)."""
    return (Path(repo_root) / registered["pilot_window"]["out_dir"]).resolve()


def check_pilot_out_dir(out_dir: Path | str, registered: dict[str, Any], repo_root: Path | str) -> Path:
    """DEC-101 E3 (A-2): ``--pilot`` refuses every ``--out`` other than the YAML's ``pilot_window.out_dir`` (comparison of the
    RESOLVED paths, the pinned one relative to the repository root, ``--out`` as the file system sees it).  Applies to a
    DEC-referenced re-run as well (its files carry the DEC in their name, next to the first result)."""
    want = pilot_dir(registered, repo_root)
    got = Path(out_dir).resolve()
    if got != want:
        raise PilotLockError(f"--out {str(out_dir)!r} (resolved {got}) is not the pilot directory pinned in the registration "
                             f"(pilot_window.out_dir {registered['pilot_window']['out_dir']!r} -> {want}): exactly one pilot "
                             "directory (DEC-101 E3)")
    return want


def find_pilot_results(runs_root: Path | str, registered_sha256: str, *, exclude: tuple[Path, ...] = ()) -> list[str]:
    """DEC-101 E3 (A-2): every ``h32_pilot*.json`` below ``runs_root`` (recursive) whose ``registered_sha256`` equals the given
    registration hash -- earlier pilot results of THIS registration, wherever they lie.  Sorted, relative to ``runs_root``.
    Only files with this name pattern are opened (never a sealed file); a file of that pattern that cannot be parsed cannot be
    excluded as an earlier pilot and is a loud fail (stricter reading).

    DEC-101 Teil 2 (N-4): the attempt marker ``<prefix>_attempt.json`` (:func:`write_attempt_marker`) matches the pattern and carries
    the ``registered_sha256`` -- an aborted attempt is found like a result.  ``exclude``: resolved paths that do not count (the
    writer's own marker of the running attempt)."""
    root = Path(runs_root)
    if not root.is_dir():
        return []
    want = str(registered_sha256).lower()
    skip = {Path(x).resolve() for x in exclude}
    hits: list[str] = []
    for p in sorted(root.rglob(C.PILOT_FILE_GLOB)):
        if not p.is_file() or p.resolve() in skip:
            continue
        artifacts.refuse_unsafe_path(p)
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PilotLockError(f"{p}: a file of the pilot name pattern that cannot be read ({exc}) -- it cannot be excluded as an "
                                 "earlier pilot result of this registration (DEC-101 E3)") from exc
        if isinstance(payload, dict) and str(payload.get("registered_sha256")).lower() == want:
            hits.append(p.relative_to(root).as_posix())
    return hits


def pilot_prefix(rerun_dec: str | None) -> str:
    return "h32_pilot" if not rerun_dec else f"h32_pilot_rerun_{rerun_dec}"


def attempt_marker_path(out_dir: Path | str, prefix: str) -> Path:
    """DEC-101 Teil 2 (N-4): the attempt marker of the pilot run with this ``prefix`` (``h32_pilot_attempt.json`` for the first run,
    ``h32_pilot_rerun_DEC-nn_attempt.json`` for a DEC-referenced re-run) -- inside the pinned pilot directory, matching ``h32_pilot*``."""
    return Path(out_dir) / f"{prefix}{C.PILOT_ATTEMPT_SUFFIX}.json"


def write_attempt_marker(out_dir: Path | str, registered_sha256: str, lock: dict[str, Any], *, mode: str = "pilot",
                         now: datetime | None = None) -> dict[str, Any]:
    """DEC-101 Teil 2 (N-4): write ``<prefix>_attempt.json`` (``registered_sha256``, UTC time stamp, mode, prefix, re-run DEC) into
    the pinned pilot directory BEFORE the panel is loaded.  The marker counts as a pilot attempt for the exactly-one-pilot lock
    whether or not a result file follows: an attempt that dies after the first variant (pilot values are logged before any result
    file exists) leaves a trace, and the next run is refused without ``--pilot-rerun-dec``.  Created exclusively (``x``): an
    existing marker of the same prefix is a loud fail, never overwritten.  Carries no pilot number.  ``lock`` is the
    :func:`check_rerun_lock` result."""
    sha = str(registered_sha256).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError(f"registered_sha256 {registered_sha256!r} is not a sha256")
    out = Path(out_dir)
    path = attempt_marker_path(out, lock["prefix"])
    artifacts.refuse_unsafe_path(path, writing=True)
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {"schema": C.PILOT_ATTEMPT_SCHEMA, "ref": C.PILOT_ATTEMPT_REF, "mode": mode, "registered_sha256": sha,
               "attempt_utc": stamp, "prefix": lock["prefix"], "rerun_dec": lock.get("rerun_dec"),
               "note": "written before the panel is loaded; counts as a pilot attempt for the exactly-one-pilot lock (a further run "
                       "needs --pilot-rerun-dec DEC-nn) whether or not a result file follows; no pilot number in this file"}
    out.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as fh:
            fh.write(artifacts.json_bytes(payload))
            fh.flush()
            os.fsync(fh.fileno())
    except FileExistsError as exc:
        raise PilotLockError(f"attempt marker {path.name} already exists (an earlier attempt under this prefix): "
                             "a further run needs its own --pilot-rerun-dec (DEC-101 Teil 2 (N-4))") from exc
    return {"file": str(path), "name": path.name, "sha256": artifacts.sha256_file(path), "attempt_utc": stamp, "prefix": lock["prefix"]}


def check_rerun_lock(out_dir: Path | str, registered: dict[str, Any], rerun_dec: str | None, *,
                     registered_sha256: str | None = None, runs_root: Path | str | None = None,
                     repo_root: Path | str | None = None, own_attempt_prefix: str | None = None) -> dict[str, Any]:
    """Exactly-one-pilot lock (PP0', DEC-99 (3), DEC-101 E3): refuse a second pilot run if the output directory already holds a
    pilot artifact or the registration carries a ``pilot_result_sha256`` -- unless ``--pilot-rerun-dec DEC-nn`` names the DEC
    that allows a re-run after a proven code or data error.  There is no force flag.  A re-run never overwrites: its files
    carry the DEC in their name and both results stay disclosed.

    DEC-101 E3 (A-2) makes the lock technical, not only per directory: with ``repo_root`` the ``--out`` directory must be the
    pinned ``pilot_window.out_dir`` (:func:`check_pilot_out_dir`), and with ``runs_root`` + ``registered_sha256`` every
    ``h32_pilot*.json`` below ``runs_root`` (recursive) with the same ``registered_sha256`` counts as an earlier pilot result
    -- a new directory does not open a second pilot.  Without these arguments the lock behaves as in DEC-99.

    DEC-101 Teil 2 (N-4): the attempt marker (``h32_pilot*_attempt.json``, :func:`write_attempt_marker`) counts like a result: a run that
    was aborted after its marker blocks a second run without ``--pilot-rerun-dec``; an aborted RE-RUN (marker ``<prefix>_attempt.json``
    without result) blocks a further re-run under the same DEC.  ``own_attempt_prefix``: the writer of a running attempt passes its own
    prefix so that its own marker is not counted as an earlier attempt."""
    out = Path(out_dir)
    scope: dict[str, Any] = {}
    if repo_root is not None:
        check_pilot_out_dir(out, registered, repo_root)
        scope["repo_root"] = str(repo_root)
    own = (attempt_marker_path(out, own_attempt_prefix).resolve(),) if own_attempt_prefix else ()
    existing = sorted(p.name for p in out.glob("h32_pilot*") if p.resolve() not in own) if out.is_dir() else []
    found: list[str] = []
    if runs_root is not None and registered_sha256:
        found = find_pilot_results(runs_root, registered_sha256, exclude=own)
        scope.update({"runs_root": str(runs_root), "registered_sha256": str(registered_sha256).lower(), "found": found})
    reg_sha = (registered.get("pilot_window") or {}).get("pilot_result_sha256")
    earlier = bool(existing or reg_sha or found)
    if rerun_dec is None:
        if earlier:
            what = "registered pilot_result_sha256" if reg_sha else (existing[0] if existing else f"{found[0]} (below {runs_root})")
            raise PilotLockError(f"a pilot result already exists for this registration ({what}): exactly one pilot run "
                                 "(DEC-99 (3), DEC-101 E3); a re-run needs --pilot-rerun-dec <DEC-nn> after a proven code or "
                                 "data error")
        out_lock: dict[str, Any] = {"rerun": False, "prefix": pilot_prefix(None)}
        if scope:
            out_lock["scope"] = scope
        return out_lock
    if not DEC_PATTERN.match(str(rerun_dec)):
        raise PilotLockError(f"--pilot-rerun-dec {rerun_dec!r} is not a DEC reference (DEC-nn)")
    if not earlier:
        raise PilotLockError("--pilot-rerun-dec given but no earlier pilot result exists")
    prefix = pilot_prefix(rerun_dec)
    names = {f"{prefix}.json", f"{prefix}{C.PILOT_ATTEMPT_SUFFIX}.json"}           # N-4: an aborted re-run (marker only) counts as well
    if any(n in existing for n in names) or any(Path(f).name in names for f in found):
        raise PilotLockError(f"a re-run under {rerun_dec} already exists or was attempted ({sorted(names)}): a further re-run needs its own DEC")
    res: dict[str, Any] = {"rerun": True, "rerun_dec": rerun_dec, "prefix": prefix, "earlier": existing,
                           "registered_pilot_result_sha256": reg_sha}
    if scope:
        res["scope"] = scope
        res["earlier_found"] = found
    return res
