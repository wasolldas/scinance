"""H-24 driver — does minute net flow LEAD the following 30-minute move?

Pre-registered measurement gate (registry 2026-08-18 + Nachtrag same day,
Welle 7, KAPITALFREI).

NAMING (DEC-39, corrected BEFORE any run): the registered judgment quantity
tests CONTINUATION, not "persistence". A permanent impact already sits in
the impact minute's price, so its forward move is independent of the flow
(IC30 ~ 0); only continuation gives a positive forward IC, pure reversal a
negative one. Synthetic controls: reversal -0.22, half-transient -0.10,
permanent +0.01, continuation +0.13. The gate is unchanged — only the claim
it tests is now named correctly, and the originally intended persistence
question survives as the non-judgment-bearing ``impact_reading``.

Reads EXCLUSIVELY the WP-0 deterministic bar cache (DEC-34); the five
registered fingerprints are verified before any measurement.

Per symbol and UTC day two rank correlations over the day's minutes:

  * ``ic_contemp`` = Spearman(F_m, r_m) — net flow against the SAME minute's
    return. This is the POSITIVE CONTROL (registered, binding, GL-020
    pattern): a machinery that cannot even see contemporaneous impact says
    nothing about what follows. Pooled mean must reach +0.10 per judgment
    window, else the run is METHODICALLY INVALID (no verdict, NOT drop).
  * ``ic_p30`` = Spearman(F_m, forward log move from the minute close m to
    the last bar at or before m+30min) — THE registered judgment quantity.
    The forward window starts at the NEXT minute close, so the impact minute
    itself is excluded (bounce cannot leak in).

``F_m = vol_buy - vol_sell`` comes straight from the cache's exact-decimal
sums. Horizons 5 and 120 minutes are computed and reported but are
explicitly NOT judgment-bearing (one registered horizon, no search).

REZENZ-KLAUSEL (DEC-38, first application): only the two most recent
half-years are judgment-bearing; the eight older half-years run as a
descriptive ERA PROFILE. They answer whether the effect USED to differ,
never whether it exists.

Gate (adjudicated by the gate-auditor; the payload is gate-neutral):
WEITER iff in BOTH recency windows pooled mean(ic_p30) >= 0.02 AND
day-clustered bootstrap p <= 0.05 after BH-FDR alpha=0.10 over F-IMP.
Hard one-window DROP, no Graubereich.

Boundary to the exhausted OFI cluster (registered citation duty): H-05
tested TICK-OFI SIGNS into the next ticks (DROP; inverse measurement
existence GL-010, capital PARK). H-24 measures the forward-lead structure of
the MINUTE AGGREGATE flow — different scale, different object. No H-24
result rehabilitates C-01 signals or their tradability.

KAPITALFREI: pure measurement. No cost quantity of any kind.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from typing import Any

import numpy as np

from ..bar_cache import bars_fingerprint, load_minute_bars

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-24"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-IMP"
FDR_ALPHA = 0.10

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "BNBUSDT")

#: Registered judgment windows (REZENZ-KLAUSEL, DEC-38): the two most
#: recent half-years of the cache range.
JUDGMENT_WINDOWS = (
    ("W-R1", "2025-08-01", "2026-01-31"),
    ("W-R2", "2026-02-01", "2026-07-31"),
)

#: Descriptive era profile — NEVER judgment-bearing (registered).
ERA_WINDOWS = (
    ("E-2021H2", "2021-07-01", "2021-12-31"),
    ("E-2022H1", "2022-01-01", "2022-06-30"),
    ("E-2022H2", "2022-07-01", "2022-12-31"),
    ("E-2023H1", "2023-01-01", "2023-06-30"),
    ("E-2023H2", "2023-07-01", "2023-12-31"),
    ("E-2024H1", "2024-01-01", "2024-06-30"),
    ("E-2024H2", "2024-07-01", "2024-12-31"),
    ("E-2025H1", "2025-01-01", "2025-07-31"),
)

#: Registered gate constants.
HORIZON_MIN = 30                 # THE registered horizon
REPORT_HORIZONS = (5, 120)       # reported, never judgment-bearing
IC_MIN = 0.02
BOOT_P_MAX = 0.05
CONTROL_IC_MIN = 0.10            # positive control floor (binding)
MIN_MINUTES_PER_DAY = 300
BOUNDARY_TOLERANCE_MIN = 5
N_DAYS_FLOOR = 100               # per window, pooled
N_BOOTSTRAP = 1000
SEED = 42

#: Registered WP-0 cache fingerprints (OWN copy per registry §8.2).
CACHE_RANGE = ("2020-03-25", "2026-07-31")
REGISTERED_FINGERPRINTS: dict[str, str] = {
    "BTCUSDT": "3be122e350df98118b26eaa16471cc070375e7593c17524753069441681dd8b6",
    "ETHUSDT": "848ff87d3903cc59132e1653c915d79150288f424aa8d0eafe00c299ac54b098",
    "XRPUSDT": "101284bf547ca534e02f901af54415e8185c525825c13b90d691667fd5ee47c3",
    "SOLUSDT": "30d3705a316a262c0ad5e69b1ec946739a551863f7dbf4deb84c17b9d09726b6",
    "BNBUSDT": "6f7b36259332de0b126e9d968c6ba9d0a5ffa9676bb400e627ee5358c117230a",
}

MS_PER_MINUTE = 60_000
MIN_PER_DAY = 1_440


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


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 3:
        return float("nan")
    rx, ry = _rank(x), _rank(y)
    sx, sy = float(np.std(rx)), float(np.std(ry))
    if sx == 0.0 or sy == 0.0:
        return float("nan")
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


def forward_move(minute_idx: np.ndarray, log_px: np.ndarray,
                 horizon: int) -> np.ndarray:
    """Log move from each minute's close to the last bar <= m + horizon.

    NaN where the horizon end has no bar within ``BOUNDARY_TOLERANCE_MIN``
    of its nominal boundary (registered data-quality rule).
    """
    target = minute_idx + horizon
    j = np.searchsorted(minute_idx, target, side="right") - 1
    ok = (j >= 0) & (target - minute_idx[np.clip(j, 0, minute_idx.size - 1)]
                     <= BOUNDARY_TOLERANCE_MIN) & (j > np.arange(minute_idx.size))
    out = np.full(minute_idx.size, np.nan)
    idx = np.flatnonzero(ok)
    out[idx] = log_px[j[idx]] - log_px[idx]
    return out


def day_metrics(minute_idx: np.ndarray, px_last: np.ndarray,
                vol_buy: np.ndarray, vol_sell: np.ndarray,
                *, horizons: tuple[int, ...]) -> dict[str, float] | None:
    """Contemporaneous + forward ICs for ONE day, or None below the floor."""
    if minute_idx.size < MIN_MINUTES_PER_DAY + 1:
        return None
    log_px = np.log(px_last)
    flow = vol_buy - vol_sell
    # contemporaneous return of minute m: close(m) - close(m-1), consecutive
    r = np.full(minute_idx.size, np.nan)
    consec = np.diff(minute_idx) == 1
    r[1:][consec] = np.diff(log_px)[consec]
    out: dict[str, float] = {}
    m = np.isfinite(r) & np.isfinite(flow)
    if int(m.sum()) < MIN_MINUTES_PER_DAY:
        return None
    out["ic_contemp"] = spearman(flow[m], r[m])
    out["n_minutes"] = float(int(m.sum()))
    for h in horizons:
        fwd = forward_move(minute_idx, log_px, h)
        mh = np.isfinite(fwd) & np.isfinite(flow)
        out[f"ic_p{h}"] = (spearman(flow[mh], fwd[mh])
                           if int(mh.sum()) >= MIN_MINUTES_PER_DAY
                           else float("nan"))
    return out


def day_clustered_boot_p(values: np.ndarray, days: np.ndarray,
                         *, n_bootstrap: int = N_BOOTSTRAP,
                         seed: int = SEED) -> float:
    """One-sided p for H0: mean <= 0, resampling whole UTC days."""
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    d = np.asarray(days)[np.isfinite(np.asarray(values, dtype=np.float64))]
    if v.size < 2:
        return 1.0
    mean_obs = float(np.mean(v))
    uniq = np.unique(d)
    if uniq.size < 2:
        return 1.0
    by_day = {int(u): v[d == u] - mean_obs for u in uniq}
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_bootstrap):
        draw = rng.integers(0, uniq.size, size=uniq.size)
        sample = np.concatenate([by_day[int(uniq[j])] for j in draw])
        if float(np.mean(sample)) >= mean_obs:
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


def impact_reading(mean_ic30: float | None,
                   threshold: float = IC_MIN) -> str | None:
    """Sign classification of the forward IC — NON-judgment-bearing (DEC-39).

    Registered Nachtrag 2026-08-18: a PERMANENT impact already sits in the
    impact minute's price, so its forward move is independent of the flow
    (IC30 ~ 0). Only CONTINUATION produces a positive forward IC, and pure
    REVERSAL produces a negative one. The registered gate asks the
    continuation question; this classification answers the originally
    intended persistence question descriptively. It reads into NO gate flag.
    """
    if mean_ic30 is None:
        return None
    if mean_ic30 <= -threshold:
        return "reversal"
    if mean_ic30 >= threshold:
        return "continuation"
    return "permanent"


def _epoch_day(day_iso: str) -> int:
    return (date.fromisoformat(day_iso) - date(1970, 1, 1)).days


def collect_daily(cache_dir: Any, exchange: str, symbol: str,
                  start: str, end: str, *, horizons: tuple[int, ...]
                  ) -> dict[str, np.ndarray]:
    """Per-day metrics for one symbol over ``[start, end]``."""
    bars = load_minute_bars(cache_dir, exchange, symbol, start, end)
    mi = bars["minute_idx"]
    keys = ("day", "ic_contemp", "n_minutes") + tuple(f"ic_p{h}" for h in horizons)
    rows: dict[str, list[float]] = {k: [] for k in keys}
    if mi.size == 0:
        return {k: np.empty(0) for k in keys}
    day = mi * MS_PER_MINUTE // 86_400_000
    for d in np.unique(day):
        m = day == d
        met = day_metrics(mi[m], bars["px_last"][m], bars["vol_buy"][m],
                          bars["vol_sell"][m], horizons=horizons)
        if met is None:
            continue
        rows["day"].append(float(d))
        for k in keys[1:]:
            rows[k].append(met.get(k, float("nan")))
    return {k: np.asarray(v, dtype=np.float64) for k, v in rows.items()}


def run(
    cache_dir: Any,
    *,
    exchange: str = "bybit",
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    judgment_windows: tuple = JUDGMENT_WINDOWS,
    era_windows: tuple = ERA_WINDOWS,
    skip_fingerprint_check: bool = False,
    expected_fingerprints: dict[str, str] | None = None,
    source: str = "",
) -> dict[str, Any]:
    """Run the registered H-24 gate (gate-neutral payload)."""
    expected = (REGISTERED_FINGERPRINTS if expected_fingerprints is None
                else expected_fingerprints)
    fingerprints: dict[str, Any] = {}
    fp_ok = True
    for sym in symbols:
        fp = bars_fingerprint(cache_dir, exchange, sym, *CACHE_RANGE)
        ref = expected.get(sym)
        match = bool(ref) and fp["sha256_values"] == ref
        fingerprints[sym] = {"observed": fp["sha256_values"], "registered": ref,
                             "matches": match}
        fp_ok &= match
    gate_valid = fp_ok or skip_fingerprint_check

    horizons = (HORIZON_MIN,) + REPORT_HORIZONS
    all_windows = tuple(judgment_windows) + tuple(era_windows)
    if not all_windows:
        raise ValueError("no windows configured")
    span_start = min(w[1] for w in all_windows)
    span_end = max(w[2] for w in all_windows)

    per_symbol = {}
    for sym in symbols:
        per_symbol[sym] = collect_daily(cache_dir, exchange, sym,
                                        span_start, span_end,
                                        horizons=horizons)
        print(f"[c24] {sym}: {per_symbol[sym]['day'].size} valid days",
              file=sys.stderr, flush=True)

    def _cell(label: str, start: str, end: str, judgment: bool) -> dict[str, Any]:
        d0, d1 = _epoch_day(start), _epoch_day(end)
        ic30, ctrl, days = [], [], []
        extra = {h: [] for h in REPORT_HORIZONS}
        for sym in symbols:
            p = per_symbol[sym]
            if p["day"].size == 0:
                continue
            m = (p["day"] >= d0) & (p["day"] <= d1)
            ic30.append(p[f"ic_p{HORIZON_MIN}"][m])
            ctrl.append(p["ic_contemp"][m])
            days.append(p["day"][m])
            for h in REPORT_HORIZONS:
                extra[h].append(p[f"ic_p{h}"][m])
        v = np.concatenate(ic30) if ic30 else np.empty(0)
        c = np.concatenate(ctrl) if ctrl else np.empty(0)
        dd = np.concatenate(days) if days else np.empty(0)
        n_days = int(np.unique(dd).size)
        n_obs = int(np.isfinite(v).sum())
        mean_ic = float(np.nanmean(v)) if n_obs else None
        mean_ctrl = (float(np.nanmean(c)) if int(np.isfinite(c).sum()) else None)
        p_boot = day_clustered_boot_p(v, dd) if n_obs else 1.0
        cell = {
            "window": label, "window_range": [start, end],
            "judgment_bearing": judgment,
            "n_symbol_days": n_obs, "n_distinct_days": n_days,
            "n_days_floor": N_DAYS_FLOOR,
            "floor_met": bool(n_days >= N_DAYS_FLOOR),
            "mean_ic_p30": mean_ic,
            "median_ic_p30": float(np.nanmedian(v)) if n_obs else None,
            "mean_ic_contemp": mean_ctrl,
            "control_min": CONTROL_IC_MIN,
            "control_passed": bool(mean_ctrl is not None
                                   and mean_ctrl >= CONTROL_IC_MIN),
            "ic_ge_min": bool(mean_ic is not None and mean_ic >= IC_MIN),
            "bootstrap_p": float(p_boot),
        }
        for h in REPORT_HORIZONS:
            arr = np.concatenate(extra[h]) if extra[h] else np.empty(0)
            cell[f"mean_ic_p{h}_report_only"] = (
                float(np.nanmean(arr)) if int(np.isfinite(arr).sum()) else None)
        cell["impact_reading"] = impact_reading(mean_ic)
        print(f"[c24] {label}: n={n_obs} days={n_days} "
              f"IC30={mean_ic if mean_ic is None else round(mean_ic, 5)} "
              f"ctrl={mean_ctrl if mean_ctrl is None else round(mean_ctrl, 4)} "
              f"p={p_boot:.4f}", file=sys.stderr, flush=True)
        return cell

    cells = [_cell(l, s, e, True) for l, s, e in judgment_windows]
    era = [_cell(l, s, e, False) for l, s, e in era_windows]

    rejected, p_crit = benjamini_hochberg([c["bootstrap_p"] for c in cells],
                                          FDR_ALPHA)
    for c, rej in zip(cells, rejected):
        c["fdr_significant"] = bool(rej)
        c["boot_p_le_max"] = bool(c["bootstrap_p"] <= BOOT_P_MAX)
        c["cell_pass"] = bool(c["floor_met"] and c["ic_ge_min"]
                              and c["boot_p_le_max"] and c["fdr_significant"])
    control_ok = all(c["control_passed"] for c in cells)
    floors_ok = all(c["floor_met"] for c in cells)
    verdict_evaluable = bool(control_ok and floors_ok)
    both_pass = bool(cells) and all(c["cell_pass"] for c in cells)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "status": "RUN",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "exchange": exchange,
        "symbols": list(symbols),
        "cache_fingerprints": fingerprints,
        "gate_valid": bool(gate_valid),
        "method": {
            "flow": "F_m = vol_buy - vol_sell (exact decimal sums, WP-0 cache)",
            "judgment_quantity": (f"daily Spearman(F_m, forward log move to "
                                  f"m+{HORIZON_MIN}min), forward window starts "
                                  "at the NEXT minute close (bounce excluded); "
                                  "tests CONTINUATION (DEC-39), not persistence"),
            "impact_reading": ("non-judgment-bearing sign classification of "
                               "mean IC30: reversal / permanent / continuation "
                               "— answers the persistence question descriptively"),
            "positive_control": (f"daily Spearman(F_m, r_m); pooled mean must "
                                 f">= {CONTROL_IC_MIN} per judgment window, "
                                 "else METHODICALLY INVALID (no verdict)"),
            "report_only_horizons": list(REPORT_HORIZONS),
            "recency_clause": ("DEC-38: only the two most recent half-years are "
                               "judgment-bearing; older windows are a descriptive "
                               "era profile"),
            "statistic": (f"pooled over symbols; day-clustered bootstrap "
                          f"({N_BOOTSTRAP} reps, seed {SEED}), H0: mean <= 0"),
            "boundary": ("H-05/GL-007/GL-010 cluster: tick-OFI signs on tick "
                         "scale — different object; no rehabilitation implied"),
        },
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "fdr_p_crit": float(p_crit),
        "gate_thresholds": {"ic_min": IC_MIN, "boot_p_max": BOOT_P_MAX,
                            "control_ic_min": CONTROL_IC_MIN,
                            "n_days_floor": N_DAYS_FLOOR},
        "cells": cells,
        "era_profile": era,
        "control_passed": bool(control_ok),
        "verdict_evaluable": verdict_evaluable,
        "both_windows_pass": both_pass,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# H-24 — Fuehrt der Minuten-Nettofluss die folgende 30-Minuten-Bewegung? (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC) · Status: {payload['status']}")
    L.append(f"- **Datenbindung:** WP-0-Bar-Cache · `gate_valid="
             f"{str(payload['gate_valid']).lower()}`")
    m = payload["method"]
    L.append(f"- **Urteilsgroesse:** {m['judgment_quantity']}")
    L.append(f"- **Positivkontrolle (bindend):** {m['positive_control']}")
    L.append(f"- **Rezenz-Klausel:** {m['recency_clause']}")
    g = payload["gate_thresholds"]
    L.append(f"- **Gate:** BEIDE Rezenz-Fenster mean(IC30) >= {g['ic_min']} UND "
             f"p <= {g['boot_p_max']} nach BH-FDR alpha={payload['fdr_alpha']} "
             f"ueber {payload['fdr_family']}. Hartes Ein-Fenster-DROP.")
    L.append(f"- **Abgrenzung:** {m['boundary']}")
    L.append("")
    L.append("## Urteilstragende Zellen (Rezenz-Fenster)")
    L.append("")
    L.append("| Fenster | Symbol-Tage | Tage | Floor | **mean IC30** | Lesart | median | >= 0,02 | Kontrolle IC_gleichzeitig | Kontrolle ok | boot-p | FDR | Zelle |")
    L.append("|---|---:|---:|:---:|---:|---|---:|:---:|---:|:---:|---:|:---:|:---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['window']} | {c['n_symbol_days']} | {c['n_distinct_days']} | "
            f"{'ok' if c['floor_met'] else '**RISS**'} | "
            f"**{_fmt(c['mean_ic_p30'])}** | {c.get('impact_reading') or '—'} | "
            f"{_fmt(c['median_ic_p30'])} | "
            f"{'ja' if c['ic_ge_min'] else 'nein'} | {_fmt(c['mean_ic_contemp'])} | "
            f"{'ok' if c['control_passed'] else '**GESCHEITERT**'} | "
            f"{c['bootstrap_p']:.4f} | {_yn(c.get('fdr_significant'))} | "
            f"{_yn(c.get('cell_pass'), 'PASS')} |")
    L.append("")
    L.append(f"**Beide Fenster PASS:** {'ja' if payload['both_windows_pass'] else 'nein'} · "
             f"**Positivkontrolle:** {'bestanden' if payload['control_passed'] else '**GESCHEITERT**'} · "
             f"**Verdikt auswertbar:** "
             f"{'ja' if payload['verdict_evaluable'] else 'NEIN — methodisch invalide, kein Verdikt'}")
    L.append("")
    L.append("## Aera-Profil (deskriptiv, NICHT urteilstragend — Rezenz-Klausel)")
    L.append("")
    L.append("| Fenster | Symbol-Tage | mean IC30 | Lesart | mean IC gleichzeitig | mean IC5 | mean IC120 |")
    L.append("|---|---:|---:|---|---:|---:|---:|")
    for c in payload["era_profile"]:
        L.append(f"| {c['window']} | {c['n_symbol_days']} | "
                 f"{_fmt(c['mean_ic_p30'])} | {c.get('impact_reading') or '—'} | "
                 f"{_fmt(c['mean_ic_contemp'])} | "
                 f"{_fmt(c.get('mean_ic_p5_report_only'))} | "
                 f"{_fmt(c.get('mean_ic_p120_report_only'))} |")
    L.append("")
    L.append("*Lesart (DEC-39, NICHT urteilstragend): `reversal` = transienter "
             "Impact (Liquiditaets-Reversion), `permanent` = Impact bleibt im "
             "Preis (Forward-IC ~ 0), `continuation` = Fluss fuehrt weitere "
             "Bewegung. Das GATE prueft ausschliesslich `continuation`.*")
    L.append("")
    L.append("*Erzeugt von `c24_impact/driver.py` — liest AUSSCHLIESSLICH den "
             "WP-0-Bar-Cache. capital_free=true. Gate-Urteil: gate-auditor "
             "gegen H-24.*")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    return "—" if v is None else f"{float(v):+.5f}"


def _yn(v: Any, yes: str = "ja") -> str:
    if v is None:
        return "—"
    return yes if v else "nein"


__all__ = [
    "CONTROL_IC_MIN",
    "DEFAULT_SYMBOLS",
    "ERA_WINDOWS",
    "FDR_FAMILY",
    "HORIZON_MIN",
    "HYPOTHESIS_ID",
    "IC_MIN",
    "JUDGMENT_WINDOWS",
    "REGISTERED_FINGERPRINTS",
    "collect_daily",
    "day_clustered_boot_p",
    "day_metrics",
    "forward_move",
    "impact_reading",
    "render_markdown",
    "run",
    "spearman",
]
