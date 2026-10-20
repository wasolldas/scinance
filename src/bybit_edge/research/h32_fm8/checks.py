"""Shared pre-checks of the modes: data fingerprints (PP2 / P3), the stage-P lock files, window pins (PP3 / P4)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import artifacts
from . import constants as C
from . import weekly as wkl
from .errors import DataFingerprintError, PilotLockError, PinError

__all__ = ["check_data_fingerprints", "check_window_pins", "check_rerun_lock", "pilot_prefix", "DEC_PATTERN"]

DEC_PATTERN = re.compile(r"^DEC-\d+$")


def check_data_fingerprints(registered: dict[str, Any], observed: dict[str, Any] | None) -> None:
    """The loaded panel's fingerprints (union range, ``delisting_dates.json``) must equal the registered ones (PP2 / P3).
    ``observed`` ``None`` (not checkable) is a loud fail as well."""
    reg = registered.get("data_fingerprints")
    if not isinstance(reg, dict):
        raise DataFingerprintError("registered YAML without data_fingerprints")
    if observed is None:
        raise DataFingerprintError("data fingerprints of the loaded panel were not supplied -- not checkable")
    for key in ("union_range_fingerprint", "delisting_dates_sha256"):
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


def pilot_prefix(rerun_dec: str | None) -> str:
    return "h32_pilot" if not rerun_dec else f"h32_pilot_rerun_{rerun_dec}"


def check_rerun_lock(out_dir: Path | str, registered: dict[str, Any], rerun_dec: str | None) -> dict[str, Any]:
    """Exactly-one-pilot lock (PP0', DEC-99 (3)): refuse a second pilot run if the output directory already holds a pilot
    artifact or the registration carries a ``pilot_result_sha256`` -- unless ``--pilot-rerun-dec DEC-nn`` names the DEC that
    allows a re-run after a proven code or data error.  There is no force flag.  A re-run never overwrites: its files carry
    the DEC in their name and both results stay disclosed."""
    out = Path(out_dir)
    existing = sorted(p.name for p in out.glob("h32_pilot*")) if out.is_dir() else []
    reg_sha = (registered.get("pilot_window") or {}).get("pilot_result_sha256")
    earlier = bool(existing or reg_sha)
    if rerun_dec is None:
        if earlier:
            raise PilotLockError("a pilot result already exists for this registration "
                                 f"({'registered pilot_result_sha256' if reg_sha else existing[0]}): exactly one pilot run "
                                 "(DEC-99 (3)); a re-run needs --pilot-rerun-dec <DEC-nn> after a proven code or data error")
        return {"rerun": False, "prefix": pilot_prefix(None)}
    if not DEC_PATTERN.match(str(rerun_dec)):
        raise PilotLockError(f"--pilot-rerun-dec {rerun_dec!r} is not a DEC reference (DEC-nn)")
    if not earlier:
        raise PilotLockError("--pilot-rerun-dec given but no earlier pilot result exists")
    prefix = pilot_prefix(rerun_dec)
    if (out / f"{prefix}.json").exists():
        raise PilotLockError(f"a re-run under {rerun_dec} already exists ({prefix}.json): a further re-run needs its own DEC")
    return {"rerun": True, "rerun_dec": rerun_dec, "prefix": prefix, "earlier": existing, "registered_pilot_result_sha256": reg_sha}
