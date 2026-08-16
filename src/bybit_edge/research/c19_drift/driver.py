"""H-19 driver — DRIFT: tape-structure stationarity over calendar time.

Pre-registered META/AUDIT measurement (registry 2026-08-15, Welle 6; the
H-18 pattern: BOTH branches are informative, there is no WEITER/DROP).

Reads EXCLUSIVELY the WP-0 deterministic bar cache (DEC-34: no raw-tick
access — a fresh tick pass would resurrect the non-deterministic read path
this wave exists to retire). The cache fingerprints registered on 2026-08-15
are verified per symbol over the FULL registered range before any cell is
computed; a mismatch sets ``gate_valid=false`` and the run carries no
finding. Bit-identity is the CORRECT precondition here — the cache is
immutable by design (unlike the live harvest store, DEC-32).

Per registered day descriptors (all deterministic functions of the bars):

  D1  lag-1 autocorrelation of the day's 1-minute log returns (only pairs
      of CONSECUTIVE present minutes; >= 300 return observations required,
      else the day is NaN),
  D2  variance signature VR = RV(5-min) / RV(1-min) of the day (5-minute
      returns aggregated from the same bars; microstructure-noise proxy),
  D3  normalised Herfindahl concentration of per-minute ``vol_total``
      (H* = (H - 1/n) / (1 - 1/n); activity clumping).

Measurement per descriptor x symbol x window: PARTIAL Spearman rank
correlation rho_p(descriptor, day index | log RV_day, log volume_day) via
the rank-residual method — the drift question is "does the descriptor move
with calendar time beyond what the vol/activity level explains".

Finding rule (magnitude-driven, pre-registered): DRIFT-BEFUND for a cell
iff |rho_p| >= 0.30 in BOTH OOS windows with the SAME sign. p-values are
deliberately NOT judgment-bearing (at N ~ 550 any p-gate is overpowered —
the mirrored H-07 lesson); a rotation-null p (circular time shift, which
preserves the descriptor's own autocorrelation) and a block-bootstrap CI
are reported per cell, with BH-FDR alpha=0.10 over F-DRIFT (15 cells) as a
report-only diagnostic.

Binding consequence rule (registry): every DRIFT-BEFUND cell obliges all
SUBSEQUENT Wave-6 evaluations using that structure to regime-split their
reporting at the OOS-1/OOS-2 boundary.

KAPITALFREI: pure measurement. No cost quantity of any kind.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np

from ..bar_cache import bars_fingerprint, load_minute_bars

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-19"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-DRIFT"
FDR_ALPHA = 0.10

#: Registered symbol universe (registry H-19: all five cache symbols).
DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "BNBUSDT")

#: Registered windows. L is DESCRIPTIVE only; OOS-1/OOS-2 carry the finding.
L_RANGE = ("2021-06-29", "2022-12-31")
OOS1_RANGE = ("2023-01-01", "2024-06-30")
OOS2_RANGE = ("2024-07-01", "2025-12-31")
WINDOWS = (("L", L_RANGE), ("OOS1", OOS1_RANGE), ("OOS2", OOS2_RANGE))
JUDGMENT_WINDOWS = ("OOS1", "OOS2")

#: Registered magnitude threshold (|rho_p| in BOTH OOS windows, same sign).
RHO_MIN = 0.30

#: Day-quality floors (registered).
MIN_RETURNS_PER_DAY = 300   # D1/D2: minimum 1-min return observations
MIN_VOL_BARS_PER_DAY = 60   # D3: minimum bars with volume > 0

DESCRIPTORS = ("D1_lag1_ac", "D2_variance_signature", "D3_herfindahl")

#: Registered WP-0 cache fingerprints (registry 2026-08-15, DEC-34 point 4)
#: over the FULL cache range 2020-03-25..2026-07-31. The cache is immutable,
#: so bit-identity is the correct continuity precondition here.
CACHE_RANGE = ("2020-03-25", "2026-07-31")
REGISTERED_FINGERPRINTS: dict[str, str] = {
    "BTCUSDT": "3be122e350df98118b26eaa16471cc070375e7593c17524753069441681dd8b6",
    "ETHUSDT": "848ff87d3903cc59132e1653c915d79150288f424aa8d0eafe00c299ac54b098",
    "XRPUSDT": "101284bf547ca534e02f901af54415e8185c525825c13b90d691667fd5ee47c3",
    "SOLUSDT": "30d3705a316a262c0ad5e69b1ec946739a551863f7dbf4deb84c17b9d09726b6",
    "BNBUSDT": "6f7b36259332de0b126e9d968c6ba9d0a5ffa9676bb400e627ee5358c117230a",
}

N_NULL_ROTATIONS = 1000
BOOT_BLOCK_DAYS = 5
N_BOOTSTRAP = 1000
SEED = 42

MS_PER_MINUTE = 60_000
MINUTES_PER_DAY = 1_440


# ----------------------------------------------------------------------------
# daily descriptors from minute bars
# ----------------------------------------------------------------------------

def day_descriptors(minute_idx: np.ndarray, px_last: np.ndarray,
                    vol_total: np.ndarray) -> dict[str, float]:
    """Registered D1/D2/D3 + conditioners for ONE UTC day of minute bars.

    All inputs are the bars of a single day, ascending ``minute_idx``.
    Returns NaN for a descriptor whose registered floor is not met.
    """
    out = {k: float("nan") for k in
           ("D1_lag1_ac", "D2_variance_signature", "D3_herfindahl",
            "log_rv", "log_volume")}
    if minute_idx.size < 2:
        return out
    logpx = np.log(px_last)
    gap = np.diff(minute_idx)
    r = np.diff(logpx)[gap == 1]          # 1-min returns, consecutive minutes only
    if r.size >= MIN_RETURNS_PER_DAY:
        rv1 = float(np.sum(r * r))
        if rv1 > 0.0:
            out["log_rv"] = float(np.log(np.sqrt(rv1)))
            # D1: lag-1 AC over consecutive return pairs (triples of minutes)
            consec = (gap[:-1] == 1) & (gap[1:] == 1)
            a, b = np.diff(logpx)[:-1][consec], np.diff(logpx)[1:][consec]
            if a.size >= MIN_RETURNS_PER_DAY:
                sa, sb = float(np.std(a)), float(np.std(b))
                if sa > 0.0 and sb > 0.0:
                    out["D1_lag1_ac"] = float(
                        np.mean((a - a.mean()) * (b - b.mean())) / (sa * sb))
            # D2: RV(5min)/RV(1min); 5-min buckets = minute_idx // 5, last px
            bucket = minute_idx // 5
            last_in_bucket = np.r_[bucket[1:] != bucket[:-1], True]
            b_idx, b_px = bucket[last_in_bucket], logpx[last_in_bucket]
            r5 = np.diff(b_px)[np.diff(b_idx) == 1]
            if r5.size >= MIN_RETURNS_PER_DAY // 5:
                out["D2_variance_signature"] = float(np.sum(r5 * r5) / rv1)
    vol = vol_total[vol_total > 0.0]
    if vol.size >= MIN_VOL_BARS_PER_DAY:
        w = vol / vol.sum()
        h = float(np.sum(w * w))
        n = vol.size
        out["D3_herfindahl"] = (h - 1.0 / n) / (1.0 - 1.0 / n)
        out["log_volume"] = float(np.log(vol.sum()))
    return out


def build_daily_panel(cache_dir: Any, exchange: str, symbol: str,
                      start: str, end: str) -> dict[str, np.ndarray]:
    """Per-day descriptor panel for ``[start, end]`` from the bar cache."""
    bars = load_minute_bars(cache_dir, exchange, symbol, start, end)
    mi = bars["minute_idx"]
    if mi.size == 0:
        return {"day_idx": np.empty(0, dtype=np.int64),
                **{k: np.empty(0) for k in
                   ("D1_lag1_ac", "D2_variance_signature", "D3_herfindahl",
                    "log_rv", "log_volume")}}
    day = mi * MS_PER_MINUTE // 86_400_000
    days = np.unique(day)
    cols: dict[str, list[float]] = {k: [] for k in
                                    ("D1_lag1_ac", "D2_variance_signature",
                                     "D3_herfindahl", "log_rv", "log_volume")}
    for d in days:
        m = day == d
        desc = day_descriptors(mi[m], bars["px_last"][m], bars["vol_total"][m])
        for k in cols:
            cols[k].append(desc[k])
    return {"day_idx": days.astype(np.int64),
            **{k: np.asarray(v, dtype=np.float64) for k, v in cols.items()}}


# ----------------------------------------------------------------------------
# partial Spearman + rotation null + block bootstrap
# ----------------------------------------------------------------------------

def _rank(x: np.ndarray) -> np.ndarray:
    """Average ranks (scipy-free)."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=np.float64)
    sx = x[order]
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def _residual(y: np.ndarray, controls: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(y.size), controls])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return y - design @ beta


def partial_spearman(desc: np.ndarray, time_idx: np.ndarray,
                     controls: np.ndarray) -> float:
    """rho_p(desc, time | controls) via the rank-residual method."""
    rd = _residual(_rank(desc), np.column_stack([_rank(c) for c in controls.T]))
    rt = _residual(_rank(time_idx.astype(np.float64)),
                   np.column_stack([_rank(c) for c in controls.T]))
    sd, st = float(np.std(rd)), float(np.std(rt))
    if sd == 0.0 or st == 0.0:
        return float("nan")
    return float(np.mean((rd - rd.mean()) * (rt - rt.mean())) / (sd * st))


def rotation_null_p(desc: np.ndarray, time_idx: np.ndarray,
                    controls: np.ndarray, rho_obs: float,
                    *, n_rotations: int = N_NULL_ROTATIONS,
                    seed: int = SEED) -> float:
    """Two-sided p under the circular-rotation null (report-only).

    Rotating the descriptor+control block against the time axis preserves the
    descriptor's own autocorrelation and its tie to the conditioners while
    destroying any calendar alignment — the appropriate null for "drift".
    """
    if not np.isfinite(rho_obs):
        return 1.0
    n = desc.size
    rng = np.random.default_rng(seed)
    shifts = rng.integers(1, n, size=n_rotations)
    count = 0
    for s in shifts:
        rho = partial_spearman(np.roll(desc, int(s)), time_idx,
                               np.roll(controls, int(s), axis=0))
        if np.isfinite(rho) and abs(rho) >= abs(rho_obs):
            count += 1
    return (count + 1) / (n_rotations + 1)


def block_bootstrap_ci(desc: np.ndarray, time_idx: np.ndarray,
                       controls: np.ndarray,
                       *, block: int = BOOT_BLOCK_DAYS,
                       n_bootstrap: int = N_BOOTSTRAP,
                       seed: int = SEED) -> tuple[float, float]:
    """Central 90% circular-block-bootstrap CI for rho_p (report-only)."""
    n = desc.size
    if n < 2 * block:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    offsets = np.arange(block)
    stats = []
    for _ in range(n_bootstrap):
        starts = rng.integers(0, n, size=n_blocks)
        idx = ((starts[:, None] + offsets[None, :]) % n).reshape(-1)[:n]
        rho = partial_spearman(desc[idx], time_idx, controls[idx])
        if np.isfinite(rho):
            stats.append(rho)
    if not stats:
        return float("nan"), float("nan")
    return (float(np.quantile(stats, 0.05)), float(np.quantile(stats, 0.95)))


def benjamini_hochberg(p_values: list[float], alpha: float) -> tuple[list[bool], float]:
    """BH-FDR (OWN copy per registry §8.2 convention; report-only here)."""
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit, k_max = 0.0, -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max, p_crit = rank, p_values[idx]
    rejected = [False] * m
    for rank, idx in enumerate(order, start=1):
        if rank <= k_max:
            rejected[idx] = True
    return rejected, p_crit


# ----------------------------------------------------------------------------
# run
# ----------------------------------------------------------------------------

def _epoch_day(day_iso: str) -> int:
    from datetime import date
    return (date.fromisoformat(day_iso) - date(1970, 1, 1)).days


def run(
    cache_dir: Any,
    *,
    exchange: str = "bybit",
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    rho_min: float = RHO_MIN,
    skip_fingerprint_check: bool = False,
    expected_fingerprints: dict[str, str] | None = None,
    source: str = "",
) -> dict[str, Any]:
    """Run the registered H-19 measurement (gate-neutral payload).

    ``skip_fingerprint_check`` / ``expected_fingerprints`` exist ONLY for
    synthetic-fixture tests; a registered run uses the module constants.
    """
    expected = (REGISTERED_FINGERPRINTS if expected_fingerprints is None
                else expected_fingerprints)

    fingerprints: dict[str, Any] = {}
    fp_ok = True
    for sym in symbols:
        fp = bars_fingerprint(cache_dir, exchange, sym, *CACHE_RANGE)
        ref = expected.get(sym)
        match = bool(ref) and fp["sha256_values"] == ref
        fingerprints[sym] = {"observed": fp["sha256_values"],
                             "registered": ref,
                             "n_days_present": fp["n_days_present"],
                             "matches": match}
        fp_ok &= match
        print(f"[c19] {sym}: cache fingerprint "
              f"{'OK' if match else 'MISMATCH'} ({fp['n_days_present']} days)",
              file=sys.stderr, flush=True)
    gate_valid = fp_ok or skip_fingerprint_check

    cells: list[dict[str, Any]] = []
    for sym in symbols:
        panel = build_daily_panel(cache_dir, exchange, sym,
                                  L_RANGE[0], OOS2_RANGE[1])
        for w_label, (w_start, w_end) in WINDOWS:
            d0, d1 = _epoch_day(w_start), _epoch_day(w_end)
            in_w = (panel["day_idx"] >= d0) & (panel["day_idx"] <= d1)
            for desc_name in DESCRIPTORS:
                d = panel[desc_name][in_w]
                t = panel["day_idx"][in_w]
                c = np.column_stack([panel["log_rv"][in_w],
                                     panel["log_volume"][in_w]])
                ok = np.isfinite(d) & np.all(np.isfinite(c), axis=1)
                d, t, c = d[ok], t[ok], c[ok]
                n = int(d.size)
                if n >= 60:
                    rho = partial_spearman(d, t, c)
                    p = rotation_null_p(d, t, c, rho)
                    ci = block_bootstrap_ci(d, t, c)
                else:
                    rho, p, ci = float("nan"), 1.0, (float("nan"), float("nan"))
                cells.append({
                    "symbol": sym, "descriptor": desc_name, "window": w_label,
                    "window_range": [w_start, w_end], "n_days": n,
                    "rho_partial": None if not np.isfinite(rho) else float(rho),
                    "abs_ge_min": bool(np.isfinite(rho) and abs(rho) >= rho_min),
                    "rotation_p": float(p),
                    "boot_ci90": [None if not np.isfinite(x) else float(x)
                                  for x in ci],
                })
        print(f"[c19] {sym}: {len(DESCRIPTORS) * len(WINDOWS)} cells measured",
              file=sys.stderr, flush=True)

    # finding per descriptor x symbol: BOTH OOS windows, |rho|>=min, same sign
    findings: list[dict[str, Any]] = []
    for sym in symbols:
        for desc_name in DESCRIPTORS:
            oos = {c["window"]: c for c in cells
                   if c["symbol"] == sym and c["descriptor"] == desc_name
                   and c["window"] in JUDGMENT_WINDOWS}
            rhos = [oos[w]["rho_partial"] for w in JUDGMENT_WINDOWS
                    if w in oos and oos[w]["rho_partial"] is not None]
            both = (len(rhos) == len(JUDGMENT_WINDOWS)
                    and all(abs(r) >= rho_min for r in rhos)
                    and len({r > 0 for r in rhos}) == 1)
            findings.append({
                "symbol": sym, "descriptor": desc_name,
                "rho_oos1": oos.get("OOS1", {}).get("rho_partial"),
                "rho_oos2": oos.get("OOS2", {}).get("rho_partial"),
                "drift_befund": bool(both),
            })

    # report-only BH-FDR over the 15 OOS-pooled rotation-p (min of both
    # windows would be anti-conservative; registered: per-cell p over the
    # 30 OOS cells is the family — 15 cells x 2 windows)
    oos_cells = [c for c in cells if c["window"] in JUDGMENT_WINDOWS]
    rejected, p_crit = benjamini_hochberg(
        [c["rotation_p"] for c in oos_cells], FDR_ALPHA)
    for c, rej in zip(oos_cells, rejected):
        c["fdr_report_significant"] = bool(rej)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "status": "RUN",
        "verdict_semantics": ("META/AUDIT (H-18-Muster): kein WEITER/DROP; "
                              "DRIFT-BEFUND je Zelle loest die registrierte "
                              "Regime-Splitting-Auflage aus"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "exchange": exchange,
        "symbols": list(symbols),
        "cache_fingerprints": fingerprints,
        "gate_valid": bool(gate_valid),
        "windows": {k: list(v) for k, v in WINDOWS},
        "judgment_windows": list(JUDGMENT_WINDOWS),
        "method": {
            "descriptors": list(DESCRIPTORS),
            "min_returns_per_day": MIN_RETURNS_PER_DAY,
            "min_vol_bars_per_day": MIN_VOL_BARS_PER_DAY,
            "measure": ("partial Spearman rho_p(descriptor, day index | "
                        "log RV_day, log volume_day), rank-residual method"),
            "finding_rule": (f"|rho_p| >= {RHO_MIN} in BOTH OOS windows, "
                             "same sign (magnitude-driven; p report-only)"),
            "rotation_null": N_NULL_ROTATIONS,
            "boot_block_days": BOOT_BLOCK_DAYS,
            "n_bootstrap": N_BOOTSTRAP,
            "seed": SEED,
        },
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "fdr_report_p_crit": float(p_crit),
        "rho_min": float(rho_min),
        "cells": cells,
        "findings": findings,
        "n_drift_befunde": int(sum(f["drift_befund"] for f in findings)),
    }


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------

def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# H-19 — DRIFT: Stationaritaet der Tape-Struktur (META/AUDIT, KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC) · Status: {payload['status']}")
    L.append(f"- **Semantik:** {payload['verdict_semantics']}")
    L.append(f"- **Datenbindung:** WP-0-Bar-Cache, Fingerabdruecke "
             f"{'OK' if payload['gate_valid'] else '**MISMATCH — kein Befund tragfaehig**'} "
             f"· `gate_valid={str(payload['gate_valid']).lower()}`")
    w = payload["windows"]
    L.append(f"- **Fenster:** L={w['L'][0]}..{w['L'][1]} (deskriptiv) | "
             f"OOS1={w['OOS1'][0]}..{w['OOS1'][1]} | OOS2={w['OOS2'][0]}..{w['OOS2'][1]}")
    L.append(f"- **Befund-Regel:** {payload['method']['finding_rule']}")
    L.append("")
    L.append("## Befunde (3 Deskriptoren x 5 Symbole)")
    L.append("")
    L.append("| Symbol | Deskriptor | rho_p OOS1 | rho_p OOS2 | **DRIFT-BEFUND** |")
    L.append("|---|---|---:|---:|:---:|")
    for f in payload["findings"]:
        L.append(f"| {f['symbol']} | {f['descriptor']} | {_fmt(f['rho_oos1'])} | "
                 f"{_fmt(f['rho_oos2'])} | "
                 f"{'**JA**' if f['drift_befund'] else 'nein'} |")
    L.append("")
    L.append(f"**DRIFT-Befunde gesamt: {payload['n_drift_befunde']} von "
             f"{len(payload['findings'])}.** Jeder Befund loest die registrierte "
             "Regime-Splitting-Auflage fuer nachfolgende Welle-6-Auswertungen aus.")
    L.append("")
    L.append("## Zellen (alle Fenster; p/KI nicht urteilstragend)")
    L.append("")
    L.append("| Symbol | Deskriptor | Fenster | n | rho_p | >=0,30 | Rotations-p | KI90 | FDR-Report |")
    L.append("|---|---|---|---:|---:|:---:|---:|---|:---:|")
    for c in payload["cells"]:
        ci = c["boot_ci90"]
        ci_s = ("—" if ci[0] is None else f"[{ci[0]:+.3f}, {ci[1]:+.3f}]")
        fdr = c.get("fdr_report_significant")
        L.append(f"| {c['symbol']} | {c['descriptor']} | {c['window']} | "
                 f"{c['n_days']} | {_fmt(c['rho_partial'])} | "
                 f"{'ja' if c['abs_ge_min'] else 'nein'} | "
                 f"{c['rotation_p']:.4f} | {ci_s} | "
                 f"{'—' if fdr is None else ('ja' if fdr else 'nein')} |")
    L.append("")
    L.append("*Erzeugt von `c19_drift/driver.py` — liest AUSSCHLIESSLICH den "
             "WP-0-Bar-Cache. capital_free=true. META/AUDIT: der gate-auditor "
             "protokolliert den Befund; es gibt kein WEITER/DROP.*")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    return "—" if v is None else f"{float(v):+.4f}"


__all__ = [
    "DEFAULT_SYMBOLS",
    "DESCRIPTORS",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "REGISTERED_FINGERPRINTS",
    "RHO_MIN",
    "build_daily_panel",
    "day_descriptors",
    "partial_spearman",
    "render_markdown",
    "rotation_null_p",
    "run",
]
