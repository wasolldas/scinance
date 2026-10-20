"""p convention of DEC-99 (binding): p from the v6 replicates of the factor-preserving null.

``p_W,v = (1 + #{replicate window means >= observed window mean, registered direction}) / (1 + R)``

The replicates are the window means (``y = s * mean fm8 IC`` over the judged weeks) of the signal-free, factor-preserving
null of the Vorlauf v6 (stress calibration, 8 beta lead weeks, real missingness): per window and variant the cell with the
LARGER null mean of the two drift cells (driftfree / drift 0.002) -- the stricter reading.  They are written once by
``--prelaunch`` as a DEC-53 artifact (``h32_prelaunch_p_replicates.json``), pinned in the registration
(``fdr.replicates_sha256``, ``fdr.n_reps``) and re-read by the test run, never re-simulated for the p.  A replicate without
a finite value counts as an exceedance (stricter reading).  The max-p over W1 / W2 goes into F-WEEK; the block permutation
of the real outcome rows and the normal approximation stay report-only (market persistence contaminates permutation nulls,
DEC-76/77).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from . import artifacts
from . import constants as C
from . import estimators as est
from .errors import ReplicatesError

__all__ = ["binding_cells", "replicate_pvalue", "build_payload", "load_replicates", "draws_for", "P_WINDOWS"]

P_WINDOWS = ("W1", "W2")
_NULL_MEAN_REL_TOL = 1e-9


def binding_cells(null_mean_driftfree: dict[str, float], null_mean_drifting: dict[str, float]) -> dict[str, str]:
    """Per variant the drift cell with the larger null mean (a tie, or a cell without a finite mean, goes to the cell with a
    finite mean / to ``driftfree``)."""
    out: dict[str, str] = {}
    for v in C.VARIANTS:
        a, b = float(null_mean_driftfree[v]), float(null_mean_drifting[v])
        if not math.isfinite(a) and not math.isfinite(b):
            raise ReplicatesError(f"{v}: neither null cell has a finite mean -- no p replicates")
        out[v] = "drifting" if (not math.isfinite(a) or (math.isfinite(b) and b > a)) else "driftfree"
    return out


def replicate_pvalue(y_obs: float, draws: np.ndarray | list[float]) -> dict[str, Any]:
    """One-sided exceedance p ``(1 + count) / (1 + R)`` with ``R`` the number of replicates; NaN replicates count as
    exceedances.  NaN ``y_obs`` gives NaN (the caller treats it as p = 1)."""
    d = np.asarray(draws, dtype=np.float64)
    n = int(d.size)
    if n == 0 or not math.isfinite(float(y_obs)):
        return {"p_value": float("nan"), "n_reps": n, "count_ge": None, "n_nan": int(np.isnan(d).sum()),
                "draws_sha256": est.series_sha256(d)}
    count = int(np.count_nonzero(~(d < float(y_obs))))                      # d >= y, and NaN (unordered) as an exceedance
    fin = d[np.isfinite(d)]
    return {"p_value": (1 + count) / (1 + n), "n_reps": n, "count_ge": count, "n_nan": int(n - fin.size),
            "draws_mean": float(fin.mean()) if fin.size else float("nan"),
            "draws_sd": float(fin.std(ddof=1)) if fin.size > 1 else float("nan"), "draws_sha256": est.series_sha256(d)}


def build_payload(windows: dict[str, dict[str, Any]], *, cut_date: str, n_reps: int, n_reps_constants: int, seed: int) -> dict[str, Any]:
    """The artifact: ``windows[W]`` = ``{"cell": {variant: cell name}, "draws": {variant: ndarray of R values}}`` for W1 / W2."""
    out_w: dict[str, Any] = {}
    for wn in P_WINDOWS:
        w = windows[wn]
        out_w[wn] = {"cell": {v: str(w["cell"][v]) for v in C.VARIANTS},
                     "variants": {v: [float(x) for x in np.asarray(w["draws"][v], dtype=np.float64)] for v in C.VARIANTS}}
        for v in C.VARIANTS:
            if len(out_w[wn]["variants"][v]) != int(n_reps):
                raise ReplicatesError(f"{wn}/{v}: {len(out_w[wn]['variants'][v])} replicates, expected {int(n_reps)}")
    return {"schema": C.P_REPLICATES_SCHEMA, "p_source": C.P_SOURCE,
            "p_formula": "p = (1 + #{y_rep >= y_obs}) / (1 + R); a non-finite replicate counts as an exceedance",
            "unit": "y = s * mean weekly fm8 IC over the judged weeks of the window (registered direction; s = +1 mom, -1 rev_gap)",
            "null": "factor-preserving null of the Vorlauf v6 (stress calibration, 8 beta lead weeks); per window and variant the "
                    "drift cell (driftfree / drift 0.002) with the larger null mean",
            "n_reps": int(n_reps), "n_reps_constants": int(n_reps_constants), "seed": int(seed), "cut_date": cut_date,
            "windows": out_w}


def draws_for(payload: dict[str, Any], wn: str, variant: str) -> np.ndarray:
    return np.asarray(payload["windows"][wn]["variants"][variant], dtype=np.float64)


def load_replicates(path: Path | str, registered: dict[str, Any]) -> dict[str, Any]:
    """P4 for the p replicates: the file hashes to ``fdr.replicates_sha256``; schema, ``n_reps`` (= ``fdr.n_reps``), seed and
    cut date match the registration; every window / variant holds ``n_reps`` values; and the first ``rules.n_reps`` finite
    values of the binding cell reproduce the frozen ``null_mean`` of the same window and variant (the file belongs to
    THESE frozen constants).  Returns the parsed payload with ``_file_sha256``."""
    p = Path(path)
    artifacts.refuse_unsafe_path(p)
    if not p.is_file():
        raise ReplicatesError(f"p replicates {p.name} not found -- no test without the pinned v6 replicates")
    fdr = registered["fdr"]
    actual = artifacts.sha256_file(p)
    if str(fdr["replicates_sha256"]).lower() != actual:
        raise ReplicatesError(f"{p.name}: sha256 {actual} differs from the registered fdr.replicates_sha256 -- NO VERDICT")
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReplicatesError(f"{p.name}: not valid JSON ({exc})") from exc
    if payload.get("schema") != C.P_REPLICATES_SCHEMA or payload.get("p_source") != C.P_SOURCE:
        raise ReplicatesError(f"{p.name} is not an H-32 p replicates artifact")
    if int(payload.get("n_reps", -1)) != int(fdr["n_reps"]):
        raise ReplicatesError(f"{p.name}: n_reps {payload.get('n_reps')} differs from the registered fdr.n_reps {fdr['n_reps']}")
    if int(payload.get("n_reps_constants", -1)) != int(registered["rules"]["n_reps"]) or int(payload.get("seed", -1)) != int(registered["rules"]["seed"]):
        raise ReplicatesError(f"{p.name}: n_reps_constants / seed differ from rules.n_reps / rules.seed")
    if payload.get("cut_date") != registered["seal"]["panel_cut_test"]:
        raise ReplicatesError(f"{p.name}: cut date {payload.get('cut_date')} differs from seal.panel_cut_test")
    n_const = int(registered["rules"]["n_reps"])
    for wn in P_WINDOWS:
        w = (payload.get("windows") or {}).get(wn)
        if not isinstance(w, dict):
            raise ReplicatesError(f"{p.name}: window {wn} missing")
        fz = registered["windows"][wn]["frozen_v6"]
        for v in C.VARIANTS:
            vals = (w.get("variants") or {}).get(v)
            if not isinstance(vals, list) or len(vals) != int(fdr["n_reps"]):
                raise ReplicatesError(f"{p.name}: {wn}/{v} does not hold {fdr['n_reps']} replicates")
            if w["cell"].get(v) not in ("driftfree", "drifting"):
                raise ReplicatesError(f"{p.name}: {wn}/{v} without a binding cell name")
            first = np.asarray(vals[:n_const], dtype=np.float64)
            fin = first[np.isfinite(first)]
            if fin.size == 0:
                raise ReplicatesError(f"{p.name}: {wn}/{v} has no finite replicate among the first {n_const}")
            frozen = float(fz["null_mean"][v])
            if abs(float(fin.mean()) - frozen) > _NULL_MEAN_REL_TOL * max(abs(frozen), 1e-12):
                raise ReplicatesError(f"{p.name}: the first {n_const} replicates of {wn}/{v} (mean {float(fin.mean()):.10f}) do not "
                                      f"reproduce the frozen null_mean {frozen:.10f} -- the file belongs to other constants")
    payload["_file_sha256"] = actual
    return payload
