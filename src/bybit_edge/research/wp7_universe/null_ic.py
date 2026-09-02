"""WP-7 -- ``SD_null(IC_t)`` permutation noise floor (PRD 4.1, the v1
``rho_quer`` estimator's registered replacement).

For every week ``t`` of the point-in-time universe, draw 1,000
permutations of an arbitrary cross-sectional signal over the symbols of
``U_t``, compute the Spearman IC of each permuted draw against the REAL
next-week return, and take the SD of that empirical distribution --
``SD_null`` for week ``t``. The window's ``SD_null(IC_t)`` is the mean of
these per-week SDs. Because Spearman correlation depends only on RANKS,
permuting any fixed signal's rank order has EXACTLY the same distribution
as permuting the plain sequence ``0..K-1`` -- so that sequence is what
this module actually permutes; no characteristic needs to be invented or
carried around (PRD 4.1: "ohne dass irgendeine Korrelation geschaetzt
werden muss").

**DEC-53 -- mandatory artifacts.** The permutation seed and the full
per-week ``SD_null`` series are NOT optional diagnostics: PRD 4.1 T7
states plainly "ohne sie KEIN VERDIKT" (no verdict without them).
``write_artifacts`` is therefore not a convenience -- any judgement-
bearing WP-7 run MUST call it and cite the returned SHA-256.

Determinism (T2): a single ``numpy.random.default_rng(seed)`` is drawn
from SEQUENTIALLY across weeks in ascending order -- same seed + same
universe + same week order => byte-identical ``sd_null_per_week`` and
identical range fingerprint across N>=3 runs.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

import numpy as np

from .pit_universe import spearman_rank_ic

__all__ = [
    "N_PERMUTATIONS_DEFAULT", "MIN_UNIVERSE",
    "permutation_null_sd", "artifact_fingerprint", "write_artifacts",
    "read_artifacts",
]

#: PRD 4.1: "1.000 Permutationen" je Woche.
N_PERMUTATIONS_DEFAULT = 1000

#: A week with fewer live symbols than this contributes no SD_null draw
#: (a cross-section of a handful of names cannot estimate a noise floor).
MIN_UNIVERSE = 10


def permutation_null_sd(
    returns: np.ndarray, alive: np.ndarray, *, week_labels: list[str] | None = None,
    n_perm: int = N_PERMUTATIONS_DEFAULT, seed: int, min_universe: int = MIN_UNIVERSE,
) -> dict[str, Any]:
    """Compute ``SD_null(IC_t)`` for the window spanned by ``returns``.

    ``returns``/``alive``: ``[n_weeks, n_symbols]`` (see ``pit_universe``
    module docstring for the convention). ``week_labels`` (optional):
    human-readable label per week row (e.g. ISO date), stored verbatim in
    the per-week series so the DEC-53 artifact is self-describing; defaults
    to the row index as a string.
    """
    n_weeks, n_symbols = returns.shape
    if week_labels is None:
        week_labels = [str(i) for i in range(n_weeks)]
    if len(week_labels) != n_weeks:
        raise ValueError("week_labels length must match returns.shape[0]")

    rng = np.random.default_rng(seed)
    weekly: list[dict[str, Any]] = []
    for t in range(n_weeks - 1):
        mask = alive[t] & alive[t + 1]
        n = int(mask.sum())
        if n < min_universe:
            continue
        outcome = returns[t + 1, mask]
        base_ranks = np.arange(n, dtype=np.float64)
        ics = np.empty(n_perm, dtype=np.float64)
        for i in range(n_perm):
            perm = rng.permutation(base_ranks)
            ics[i] = spearman_rank_ic(perm, outcome)
        sd = float(np.std(ics, ddof=0))
        weekly.append({"week": week_labels[t], "k": n, "sd_null": sd})

    sd_series = np.array([w["sd_null"] for w in weekly], dtype=np.float64)
    sd_null = float(sd_series.mean()) if len(sd_series) else float("nan")
    return {
        "seed": int(seed), "n_perm": n_perm, "min_universe": min_universe,
        "n_weeks_used": len(weekly), "weekly": weekly, "sd_null": sd_null,
    }


def artifact_fingerprint(result: dict[str, Any]) -> str:
    """SHA-256 over the seed + the exact per-week SD_null value bytes,
    canonical (ascending week) order -- mirrors ``bar_cache._bars_hash``'s
    "hash the exact value bytes" discipline so a byte-for-byte identical
    rerun is provable, not merely plausible."""
    h = hashlib.sha256()
    h.update(struct.pack("<q", int(result["seed"])))
    h.update(struct.pack("<q", int(result["n_perm"])))
    for w in result["weekly"]:
        h.update(str(w["week"]).encode("utf-8"))
        h.update(struct.pack("<q", int(w["k"])))
        h.update(struct.pack("<d", float(w["sd_null"])))
    return h.hexdigest()


def write_artifacts(out_dir: Path | str, result: dict[str, Any], *,
                     window_label: str) -> dict[str, Any]:
    """Write the DEC-53 mandatory artifact (seed + weekly SD_null series)
    to ``<out_dir>/null_ic_<window_label>.json`` and return its path +
    SHA-256. Never writes under ``data/harvest`` (checked loudly, like
    every WP-7/WP-9 output path)."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write null_ic artifacts under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = artifact_fingerprint(result)
    payload = {**result, "window_label": window_label, "sha256": fp}
    path = out_dir / f"null_ic_{window_label}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return {"path": str(path), "sha256": fp}


def read_artifacts(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    recomputed = artifact_fingerprint(payload)
    if recomputed != payload.get("sha256"):
        raise ValueError(
            f"{path}: stored sha256 {payload.get('sha256')!r} does not match "
            f"recomputed {recomputed!r} -- artifact corrupted or hand-edited")
    return payload
