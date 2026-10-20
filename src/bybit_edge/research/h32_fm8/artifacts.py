"""DEC-53 artifact helpers: series CSVs (``repr`` round trip), sha256, canonical result fingerprints, the code fingerprint.

Nothing here writes under ``data/harvest`` and nothing opens a path that matches a sealed file name of the programme.
"""
from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ..wp7_universe import panel_load
from . import constants as C
from .errors import ArtifactError, SealError

__all__ = ["canonical_sha256", "sha256_file", "write_series_csv", "read_series_csv", "write_json", "refuse_unsafe_path",
           "code_fingerprint", "git_commit", "series_float_sha256", "json_bytes", "json_file_sha256"]


def refuse_unsafe_path(path: Path | str, *, writing: bool = False) -> None:
    """Loud fail for a path under ``data/harvest`` (writing) or one that names a sealed file (reading or writing)."""
    p = Path(path)
    if writing and "data/harvest" in p.as_posix():
        raise ValueError(f"refusing to write under data/harvest: {p}")
    for pat in C.SEALED_PATTERNS:
        if fnmatch.fnmatch(p.name, pat):
            raise SealError(f"refusing to touch the sealed file {p.name}")


def canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, allow_nan=True).encode("utf-8")).hexdigest()


def sha256_file(path: Path | str) -> str:
    return panel_load.sha256_file(path)


def series_float_sha256(series: Sequence[float] | np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.asarray(series, dtype="<f8")).tobytes()).hexdigest()


def write_series_csv(path: Path, series: Sequence[float], k: Sequence[int] | None = None, *, value_name: str = "ic") -> dict[str, str]:
    """``t,<value_name>[,k]`` -- ``repr`` round-trips a float exactly (NaN -> 'nan')."""
    refuse_unsafe_path(path, writing=True)
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t", value_name] + (["k"] if k is not None else []))
        for t, v in enumerate(series):
            w.writerow([t, repr(float(v))] + ([int(k[t])] if k is not None else []))
    return {"file": Path(path).name, "sha256": sha256_file(path)}


def read_series_csv(path: Path | str, *, value_name: str = "ic") -> tuple[list[float], list[int] | None]:
    refuse_unsafe_path(path)
    with Path(path).open("r", newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows or rows[0][:2] != ["t", value_name]:
        raise ArtifactError(f"{Path(path).name}: no valid header ['t', '{value_name}'] -- KEIN VERDIKT")
    has_k = len(rows[0]) == 3 and rows[0][2] == "k"
    vals = [float(r[1]) for r in rows[1:]]
    ks = [int(r[2]) for r in rows[1:]] if has_k else None
    return vals, ks


def json_bytes(obj: Any) -> bytes:
    """The exact bytes :func:`write_json` writes (UTF-8, ``\\n`` newlines on every platform)."""
    return json.dumps(obj, indent=1, sort_keys=True, default=str, allow_nan=True).encode("utf-8")


def json_file_sha256(obj: Any) -> str:
    """sha256 of the file :func:`write_json` would write -- known before the file exists (the registration pins it)."""
    return hashlib.sha256(json_bytes(obj)).hexdigest()


def write_json(path: Path, obj: Any) -> dict[str, str]:
    refuse_unsafe_path(path, writing=True)
    Path(path).write_bytes(json_bytes(obj))
    return {"file": Path(path).name, "sha256": sha256_file(path)}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def git_commit() -> str | None:
    """Best-effort repository commit (``None`` without git).  Only used in the separate fingerprint file."""
    try:
        out = subprocess.run(["git", "-C", str(_repo_root()), "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=10, check=False)
        if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", out.stdout.strip() or ""):
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def code_fingerprint() -> dict[str, Any]:
    """sha256 of every ``*.py`` of ``h32_fm8``, of the imported ``wp13_xsec`` / ``wp7_universe`` packages and of
    ``power_p1.py`` (+ ``scripts/h32_fm8.py`` if present), per file and aggregated; python / numpy versions and the bit
    generator.  Deterministic for one checkout."""
    pkg = Path(__file__).resolve().parent
    research = pkg.parent
    files: dict[str, str] = {}
    for base, label in ((pkg, "h32_fm8"), (research / "wp13_xsec", "wp13_xsec"), (research / "wp7_universe", "wp7_universe")):
        for f in sorted(base.glob("*.py")):
            files[f"{label}/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()
    pp = research / "power_p1.py"
    if pp.is_file():
        files["power_p1.py"] = hashlib.sha256(pp.read_bytes()).hexdigest()
    script = _repo_root() / "scripts" / "h32_fm8.py"
    if script.is_file():
        files["scripts/h32_fm8.py"] = hashlib.sha256(script.read_bytes()).hexdigest()
    h = hashlib.sha256()
    for name in sorted(files):
        h.update(name.encode("utf-8"))
        h.update(files[name].encode("ascii"))
    return {"code_sha256": h.hexdigest(), "files": files, "python": sys.version.split()[0], "numpy": np.__version__,
            "bit_generator": type(np.random.default_rng(0).bit_generator).__name__}
