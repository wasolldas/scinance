"""H-22 driver — L2-TILT: daily near-touch book tilt vs next-day return.

Pre-registered measurement gate (registry 2026-08-15 + Nachtrag 2026-08-17,
Welle 6, KAPITALFREI). Reads TWO immutable stores, both fingerprint-pinned:

  * the WP-2 tilt store (``data/l2tilt``, one deterministic pass per window,
    DEC-36/DEC-38) — daily tilt = median of the day's minute samples,
  * the WP-0 bar cache — next-day log return from the UTC day closes.

Registered gate: WEITER iff BTC in BOTH L2 windows: Spearman rank IC
(tilt_d, r_{d+1}) >= 0.10 AND block-bootstrap p <= 0.05 (5-day blocks, 1000
reps, seed 42, H0: IC <= 0) after BH-FDR alpha=0.10 over F-L2 (2 cells).
Hard one-window DROP, no Graubereich, band/sampling/aggregate frozen. The
85% day-coverage floor per judgment window is enforced HERE (below it the
run is a SKIP, no verdict). ETH: one window, report-only, never judgment-
bearing. A-priori (registered, Lane C verbatim): DROP erwartet.

KAPITALFREI: measurement only; the 1.7-2x economic note stays decoupled.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from typing import Any

import numpy as np

from ..bar_cache import bars_fingerprint, load_minute_bars
from .extract import load_daily_tilt, tilt_fingerprint

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-22"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-L2"
FDR_ALPHA = 0.10

IC_MIN = 0.10
BOOT_P_MAX = 0.05
COVERAGE_FLOOR = 0.85
BOOT_BLOCK_DAYS = 5
N_BOOTSTRAP = 1000
SEED = 42

#: Registered windows: BTC judgment-bearing, ETH report-only.
WINDOWS = (
    ("BTCUSDT", "W-L2-1", "2023-07-01", "2024-06-30", True),
    ("BTCUSDT", "W-L2-2", "2024-07-01", "2025-06-30", True),
    ("ETHUSDT", "W-ETH", "2023-04-01", "2024-04-30", False),
)

#: WP-2 tilt-store fingerprints (run 2026-08-17, registry Nachtrag — the
#: tilt store is immutable, bit-identity is the correct precondition).
REGISTERED_TILT_FINGERPRINTS: dict[tuple[str, str], str] = {
    ("BTCUSDT", "W-L2-1"): "bfaaf08b9c763ff404033cf7cd05052856de39dab53ea25015035dfe3f6131f6",
    ("BTCUSDT", "W-L2-2"): "f22eba9eb698e1f4b5333ebb82824a46fcbf8798a90e08e5a90d9d9a5a9577b0",
    ("ETHUSDT", "W-ETH"): "7f18970ee329ea51fbd2498f3fb1afb3385f52fb23fa88db96e21ee193b2c330",
}

#: WP-0 cache fingerprints (OWN copy per registry §8.2 convention).
CACHE_RANGE = ("2020-03-25", "2026-07-31")
REGISTERED_BAR_FINGERPRINTS: dict[str, str] = {
    "BTCUSDT": "3be122e350df98118b26eaa16471cc070375e7593c17524753069441681dd8b6",
    "ETHUSDT": "848ff87d3903cc59132e1653c915d79150288f424aa8d0eafe00c299ac54b098",
}

MS_PER_MINUTE = 60_000


def _rank(x: np.ndarray) -> np.ndarray:
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


def spearman_ic(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = _rank(x), _rank(y)
    sx, sy = float(np.std(rx)), float(np.std(ry))
    if sx == 0.0 or sy == 0.0 or x.size < 3:
        return float("nan")
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


def block_bootstrap_p(x: np.ndarray, y: np.ndarray, ic_obs: float,
                      *, block: int = BOOT_BLOCK_DAYS,
                      n_bootstrap: int = N_BOOTSTRAP,
                      seed: int = SEED) -> float:
    """One-sided p for H0: IC <= 0 via circular block resampling of PAIRS
    against independently block-resampled y (breaking the pairing under H0
    while preserving each series' autocorrelation)."""
    n = x.size
    if n < 2 * block or not np.isfinite(ic_obs):
        return 1.0
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    offsets = np.arange(block)
    count = 0
    for _ in range(n_bootstrap):
        sx = ((rng.integers(0, n, size=n_blocks)[:, None]
               + offsets[None, :]) % n).reshape(-1)[:n]
        sy = ((rng.integers(0, n, size=n_blocks)[:, None]
               + offsets[None, :]) % n).reshape(-1)[:n]
        ic = spearman_ic(x[sx], y[sy])
        if np.isfinite(ic) and ic >= ic_obs:
            count += 1
    return (count + 1) / (n_bootstrap + 1)


def benjamini_hochberg(p_values: list[float], alpha: float) -> tuple[list[bool], float]:
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


def daily_closes(cache_dir: Any, exchange: str, symbol: str,
                 start: str, end: str) -> dict[int, float]:
    """UTC-day log closes from the WP-0 bar cache."""
    bars = load_minute_bars(cache_dir, exchange, symbol, start, end)
    mi, px = bars["minute_idx"], bars["px_last"]
    out: dict[int, float] = {}
    if mi.size == 0:
        return out
    day = mi * MS_PER_MINUTE // 86_400_000
    for d in np.unique(day):
        m = day == d
        out[int(d)] = float(np.log(px[m][-1]))
    return out


def run(
    tilt_dir: Any,
    cache_dir: Any,
    *,
    exchange: str = "bybit",
    skip_fingerprint_check: bool = False,
    expected_tilt_fps: dict[tuple[str, str], str] | None = None,
    expected_bar_fps: dict[str, str] | None = None,
    windows: tuple = WINDOWS,
    coverage_floor: float = COVERAGE_FLOOR,
    source: str = "",
) -> dict[str, Any]:
    """Run the registered H-22 gate (gate-neutral payload)."""
    from datetime import timedelta

    exp_tilt = (REGISTERED_TILT_FINGERPRINTS if expected_tilt_fps is None
                else expected_tilt_fps)
    exp_bar = (REGISTERED_BAR_FINGERPRINTS if expected_bar_fps is None
               else expected_bar_fps)

    fp_ok = True
    fps: dict[str, Any] = {"tilt": {}, "bars": {}}
    for sym, label, start, end, _ in windows:
        fp = tilt_fingerprint(tilt_dir, exchange, sym, start, end)
        ref = exp_tilt.get((sym, label))
        match = bool(ref) and fp["sha256_values"] == ref
        fps["tilt"][f"{sym}/{label}"] = {"observed": fp["sha256_values"],
                                         "registered": ref, "matches": match}
        fp_ok &= match
    for sym in sorted({w[0] for w in windows}):
        if sym not in exp_bar and skip_fingerprint_check:
            continue
        fp = bars_fingerprint(cache_dir, exchange, sym, *CACHE_RANGE)
        ref = exp_bar.get(sym)
        match = bool(ref) and fp["sha256_values"] == ref
        fps["bars"][sym] = {"observed": fp["sha256_values"],
                            "registered": ref, "matches": match}
        fp_ok &= match
    gate_valid = fp_ok or skip_fingerprint_check

    cells: list[dict[str, Any]] = []
    for sym, label, start, end, judgment in windows:
        daily = load_daily_tilt(tilt_dir, exchange, sym, start, end)
        d0 = (date.fromisoformat(start) - date(1970, 1, 1)).days
        d1 = (date.fromisoformat(end) - date(1970, 1, 1)).days
        n_range = d1 - d0 + 1
        coverage = daily["day_idx"].size / n_range
        # next-day close needs one spill day beyond the window end
        end_spill = (date.fromisoformat(end) + timedelta(days=1)).isoformat()
        closes = daily_closes(cache_dir, exchange, sym, start, end_spill)
        x, y = [], []
        for di, tv in zip(daily["day_idx"], daily["tilt_median"]):
            c0, c1 = closes.get(int(di)), closes.get(int(di) + 1)
            if c0 is not None and c1 is not None:
                x.append(float(tv))
                y.append(c1 - c0)
        x_arr, y_arr = np.asarray(x), np.asarray(y)
        n = int(x_arr.size)
        ic = spearman_ic(x_arr, y_arr) if n >= 30 else float("nan")
        p = block_bootstrap_p(x_arr, y_arr, ic) if n >= 30 else 1.0
        cells.append({
            "symbol": sym, "window": label, "window_range": [start, end],
            "judgment_bearing": judgment,
            "n_tilt_days": int(daily["day_idx"].size),
            "coverage": round(float(coverage), 4),
            "coverage_floor": coverage_floor,
            "floor_met": bool(coverage >= coverage_floor),
            "n_pairs": n,
            "ic": None if not np.isfinite(ic) else float(ic),
            "ic_ge_min": bool(np.isfinite(ic) and ic >= IC_MIN),
            "boot_p": float(p),
        })
        print(f"[c22] {sym} {label}: n={n} coverage={coverage:.1%} "
              f"IC={ic if not np.isfinite(ic) else round(ic, 4)} p={p:.4f}",
              file=sys.stderr, flush=True)

    judgment_cells = [c for c in cells if c["judgment_bearing"]]
    rejected, p_crit = benjamini_hochberg(
        [c["boot_p"] for c in judgment_cells], FDR_ALPHA)
    for c, rej in zip(judgment_cells, rejected):
        c["fdr_significant"] = bool(rej)
        c["boot_p_le_max"] = bool(c["boot_p"] <= BOOT_P_MAX)
        c["cell_pass"] = bool(c["floor_met"] and c["ic_ge_min"]
                              and c["boot_p_le_max"] and c["fdr_significant"])
    coverage_ok = all(c["floor_met"] for c in judgment_cells)
    both_pass = bool(judgment_cells) and all(c["cell_pass"]
                                             for c in judgment_cells)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "status": "RUN" if coverage_ok else "SKIP_COVERAGE",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "fingerprints": fps,
        "gate_valid": bool(gate_valid),
        "method": {
            "feature": ("daily tilt = median of minute-sampled (B-A)/(B+A) "
                        "within +-25 bp of mid (WP-2 store, frozen)"),
            "target": "next-day log return from WP-0 day closes",
            "ic": "Spearman rank IC per window",
            "null": (f"block bootstrap ({BOOT_BLOCK_DAYS}-day blocks, "
                     f"{N_BOOTSTRAP} reps, seed {SEED}), H0: IC <= 0, "
                     "pairing broken under H0 with autocorrelation preserved"),
        },
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "fdr_p_crit": float(p_crit),
        "gate_thresholds": {"ic_min": IC_MIN, "boot_p_max": BOOT_P_MAX,
                            "coverage_floor": coverage_floor},
        "cells": cells,
        "coverage_ok": bool(coverage_ok),
        "both_btc_windows_pass": bool(both_pass),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# H-22 — L2-TILT: Tages-Buchneigung vs. Folgetags-Rendite (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC) · Status: {payload['status']}")
    L.append(f"- **Datenbindung:** WP-2-Tilt-Store + WP-0-Bar-Cache · "
             f"`gate_valid={str(payload['gate_valid']).lower()}`")
    L.append(f"- **Feature:** {payload['method']['feature']}")
    L.append(f"- **Null:** {payload['method']['null']}")
    g = payload["gate_thresholds"]
    L.append(f"- **Gate:** BTC in BEIDEN L2-Fenstern IC >= {g['ic_min']} UND "
             f"p <= {g['boot_p_max']} nach BH-FDR alpha={payload['fdr_alpha']} "
             f"ueber {payload['fdr_family']}; Abdeckungs-Floor {g['coverage_floor']:.0%}. "
             "Hartes Ein-Fenster-DROP. A-priori: DROP erwartet.")
    L.append("")
    L.append("| Symbol | Fenster | urteilstragend | Tilt-Tage | Abdeckung | Floor | Paare | **IC** | >= 0,10 | boot-p | FDR | Zelle |")
    L.append("|---|---|:---:|---:|---:|:---:|---:|---:|:---:|---:|:---:|:---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['symbol']} | {c['window']} | "
            f"{'ja' if c['judgment_bearing'] else 'nein'} | {c['n_tilt_days']} | "
            f"{c['coverage']:.1%} | {'ok' if c['floor_met'] else '**RISS**'} | "
            f"{c['n_pairs']} | {_fmt(c['ic'])} | "
            f"{'ja' if c['ic_ge_min'] else 'nein'} | {c['boot_p']:.4f} | "
            f"{_yn(c.get('fdr_significant'))} | {_yn(c.get('cell_pass'), 'PASS')} |")
    L.append("")
    L.append(f"**BTC beide Fenster PASS:** "
             f"{'ja' if payload['both_btc_windows_pass'] else 'nein'} · "
             f"**Abdeckung ok:** {'ja' if payload['coverage_ok'] else 'NEIN — SKIP'}")
    L.append("")
    L.append("*Erzeugt von `c22_l2tilt/driver.py`. capital_free=true — die "
             "1,7–2x-Notiz bleibt entkoppelt. Gate-Urteil: gate-auditor gegen H-22.*")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    return "—" if v is None else f"{float(v):+.4f}"


def _yn(v: Any, yes: str = "ja") -> str:
    if v is None:
        return "—"
    return yes if v else "nein"


__all__ = [
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "IC_MIN",
    "REGISTERED_BAR_FINGERPRINTS",
    "REGISTERED_TILT_FINGERPRINTS",
    "WINDOWS",
    "block_bootstrap_p",
    "daily_closes",
    "render_markdown",
    "run",
    "spearman_ic",
]
