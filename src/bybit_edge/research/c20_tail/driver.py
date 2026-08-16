"""H-20 driver — TAIL-AFTERMATH: reversal-signed move after 3.5-sigma hours.

Pre-registered measurement gate (registry 2026-08-15, Welle 6, KAPITALFREI).

Reads EXCLUSIVELY the WP-0 deterministic bar cache (DEC-34); the registered
cache fingerprints are verified before any measurement (bit-identity is
correct here — the cache is immutable, DEC-32 scoped its lesson to LIVE
stores). All price-move quantities are measurement magnitudes in basis
points of log return — no cost, fee or PnL notion exists in this module.

Registered pipeline:

  * hourly log return r_h per UTC calendar hour, close-to-close between
    CONSECUTIVE hours; an hour qualifies as event CANDIDATE only with
    >= 45 present minute bars,
  * causal robust scale sigma_h = 1.4826 x rolling MAD of the PREVIOUS
    up-to-720 defined hourly returns (>= 360 required) — the event hour
    NEVER contributes to its own scale,
  * event: |r_h| >= 3.5 sigma_h; non-overlap: per symbol only the FIRST
    event within any 24 h window counts (ascending scan, deterministic),
  * outcome y = -sign(r_event) x [log P(t0+24h) - log P(t0+2h)], P = last
    cached bar price at or before the boundary; the 2 h gap excludes
    bounce/short-horizon microstructure from the measurement window.
    Implementation floor (data quality, documented in the payload): the
    aftermath window must contain >= 660 of its 1320 minutes and the
    boundary bars must lie within 30 min of their nominal boundary,
    otherwise the event is dropped and counted as ``n_dropped_data``.
  * pooled across the 5 symbols per window; judgment-bearing statistics on
    OOS-1/OOS-2 (L descriptive): day-clustered circular-free bootstrap
    (cluster = UTC event day, 1000 reps, seed 42) for H0: E[y] <= 0.

Registered gate (adjudicated by the gate-auditor, payload is gate-neutral):
WEITER iff in BOTH OOS windows pooled: mean(y) >= +10 bp AND cluster-p
<= 0.05 after BH-FDR alpha=0.10 over F-TAIL (2 cells). Hard one-window
DROP. N-floor: >= 100 event DAYS per window pooled, else NO VERDICT
(``verdict_evaluable=false`` — not DROP; GL-017 lesson, floor not
lowerable). Per-symbol cells are reported, never judgment-bearing.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from typing import Any

import numpy as np

from ..bar_cache import bars_fingerprint, load_minute_bars

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-20"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-TAIL"
FDR_ALPHA = 0.10

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "BNBUSDT")

L_RANGE = ("2021-06-29", "2022-12-31")
OOS1_RANGE = ("2023-01-01", "2024-06-30")
OOS2_RANGE = ("2024-07-01", "2025-12-31")
WINDOWS = (("L", L_RANGE), ("OOS1", OOS1_RANGE), ("OOS2", OOS2_RANGE))
JUDGMENT_WINDOWS = ("OOS1", "OOS2")

#: Registered event/gate constants.
SIGMA_MULT = 3.5
SCALE_WINDOW_HOURS = 720
SCALE_MIN_HOURS = 360
MIN_BARS_PER_HOUR = 45
GAP_HOURS = 2
HORIZON_HOURS = 24
MEAN_MIN_BP = 10.0
BOOT_P_MAX = 0.05
N_EVENT_DAYS_FLOOR = 100
N_BOOTSTRAP = 1000
SEED = 42

#: Implementation data-quality floors for the aftermath window (documented
#: in the payload; drops are counted, never silent).
AFTERMATH_MIN_MINUTES = 660
BOUNDARY_TOLERANCE_MIN = 30

#: Registered WP-0 cache fingerprints (OWN copy per registry §8.2 — no
#: cross-import between research packages), range 2020-03-25..2026-07-31.
CACHE_RANGE = ("2020-03-25", "2026-07-31")
REGISTERED_FINGERPRINTS: dict[str, str] = {
    "BTCUSDT": "3be122e350df98118b26eaa16471cc070375e7593c17524753069441681dd8b6",
    "ETHUSDT": "848ff87d3903cc59132e1653c915d79150288f424aa8d0eafe00c299ac54b098",
    "XRPUSDT": "101284bf547ca534e02f901af54415e8185c525825c13b90d691667fd5ee47c3",
    "SOLUSDT": "30d3705a316a262c0ad5e69b1ec946739a551863f7dbf4deb84c17b9d09726b6",
    "BNBUSDT": "6f7b36259332de0b126e9d968c6ba9d0a5ffa9676bb400e627ee5358c117230a",
}

MS_PER_MINUTE = 60_000
MIN_PER_HOUR = 60
MIN_PER_DAY = 1_440


# ----------------------------------------------------------------------------
# hourly series, causal scale, events, aftermath
# ----------------------------------------------------------------------------

def hourly_series(minute_idx: np.ndarray, px_last: np.ndarray
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(hour_idx, r_h, candidate) — close-to-close between CONSECUTIVE hours.

    ``r_h[i]`` is defined only when hour ``hour_idx[i] - 1`` is also present
    (NaN otherwise). ``candidate[i]`` is True iff the hour has >= 45 minute
    bars (registered candidate condition; the return may exist regardless).
    """
    hour = minute_idx // MIN_PER_HOUR
    hours, first = np.unique(hour, return_index=True)
    # last bar of each hour = element before the next hour's first element
    last = np.r_[first[1:], minute_idx.size] - 1
    close = np.log(px_last[last])
    counts = np.r_[first[1:], minute_idx.size] - first
    r = np.full(hours.size, np.nan)
    consec = np.diff(hours) == 1
    r[1:][consec] = np.diff(close)[consec]
    return hours, r, counts >= MIN_BARS_PER_HOUR


def causal_mad_scale(r: np.ndarray, *, window: int = SCALE_WINDOW_HOURS,
                     min_obs: int = SCALE_MIN_HOURS) -> np.ndarray:
    """sigma_h = 1.4826 x MAD of the previous <=``window`` DEFINED returns.

    Strictly causal: position i uses defined returns at positions < i only.
    NaN where fewer than ``min_obs`` are available.
    """
    out = np.full(r.size, np.nan)
    defined_idx = np.flatnonzero(np.isfinite(r))
    defined_vals = r[defined_idx]
    # k = number of defined returns strictly before each position
    k = np.searchsorted(defined_idx, np.arange(r.size), side="left")
    for i in range(r.size):
        n_prev = k[i]
        if n_prev < min_obs:
            continue
        w = defined_vals[max(0, n_prev - window):n_prev]
        med = np.median(w)
        out[i] = 1.4826 * float(np.median(np.abs(w - med)))
    return out


def find_events(hours: np.ndarray, r: np.ndarray, candidate: np.ndarray,
                sigma: np.ndarray) -> np.ndarray:
    """Indices of registered events with the deterministic non-overlap rule."""
    raw = np.flatnonzero(candidate & np.isfinite(r) & np.isfinite(sigma)
                         & (sigma > 0) & (np.abs(r) >= SIGMA_MULT * sigma))
    kept: list[int] = []
    last_hour = None
    for i in raw:
        h = int(hours[i])
        if last_hour is None or h - last_hour >= HORIZON_HOURS:
            kept.append(int(i))
            last_hour = h
    return np.asarray(kept, dtype=np.int64)


def aftermath_bp(minute_idx: np.ndarray, px_last: np.ndarray,
                 event_hour: int, event_sign: float) -> float | None:
    """y in basis points for one event; None if data-quality floors fail."""
    t0 = (event_hour + 1) * MIN_PER_HOUR            # end of the event hour
    m_start = t0 + GAP_HOURS * MIN_PER_HOUR
    m_end = t0 + HORIZON_HOURS * MIN_PER_HOUR
    i_start = int(np.searchsorted(minute_idx, m_start, side="right")) - 1
    i_end = int(np.searchsorted(minute_idx, m_end, side="right")) - 1
    if i_start < 0 or i_end <= i_start:
        return None
    if (m_start - minute_idx[i_start] > BOUNDARY_TOLERANCE_MIN
            or m_end - minute_idx[i_end] > BOUNDARY_TOLERANCE_MIN):
        return None
    in_window = np.count_nonzero((minute_idx > m_start) & (minute_idx <= m_end))
    if in_window < AFTERMATH_MIN_MINUTES:
        return None
    move = float(np.log(px_last[i_end]) - np.log(px_last[i_start]))
    return -event_sign * move * 1e4


def day_clustered_boot_p(y: np.ndarray, days: np.ndarray,
                         *, n_bootstrap: int = N_BOOTSTRAP,
                         seed: int = SEED) -> float:
    """One-sided p for H0: E[y] <= 0, resampling whole event DAYS.

    The observed mean is subtracted (imposing the H0 boundary), clusters are
    drawn with replacement, and p = (#{mean* >= mean_obs} + 1) / (B + 1) —
    the c11 add-one convention.
    """
    y = np.asarray(y, dtype=np.float64)
    if y.size < 2:
        return 1.0
    mean_obs = float(np.mean(y))
    uniq = np.unique(days)
    if uniq.size < 2:
        return 1.0
    centered_by_day = {int(d): y[days == d] - mean_obs for d in uniq}
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_bootstrap):
        draw = rng.integers(0, uniq.size, size=uniq.size)
        sample = np.concatenate([centered_by_day[int(uniq[j])] for j in draw])
        if float(np.mean(sample)) >= mean_obs:
            count += 1
    return (count + 1) / (n_bootstrap + 1)


def benjamini_hochberg(p_values: list[float], alpha: float) -> tuple[list[bool], float]:
    """BH-FDR (OWN copy per registry §8.2 convention)."""
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
    return (date.fromisoformat(day_iso) - date(1970, 1, 1)).days


def collect_events(cache_dir: Any, exchange: str, symbol: str
                   ) -> dict[str, np.ndarray]:
    """All registered events of one symbol over the full L..OOS2 span."""
    bars = load_minute_bars(cache_dir, exchange, symbol,
                            L_RANGE[0], OOS2_RANGE[1])
    mi, px = bars["minute_idx"], bars["px_last"]
    empty = {k: np.empty(0) for k in
             ("event_hour", "event_day", "r_event", "sigma", "y_bp")}
    if mi.size == 0:
        return {k: v.astype(np.float64) for k, v in empty.items()}
    hours, r, cand = hourly_series(mi, px)
    sigma = causal_mad_scale(r)
    ev = find_events(hours, r, cand, sigma)
    rows = {k: [] for k in empty}
    n_dropped = 0
    for i in ev:
        y = aftermath_bp(mi, px, int(hours[i]), float(np.sign(r[i])))
        if y is None:
            n_dropped += 1
            continue
        rows["event_hour"].append(float(hours[i]))
        rows["event_day"].append(float(hours[i] // 24))
        rows["r_event"].append(float(r[i]))
        rows["sigma"].append(float(sigma[i]))
        rows["y_bp"].append(float(y))
    out = {k: np.asarray(v, dtype=np.float64) for k, v in rows.items()}
    out["n_dropped_data"] = np.asarray([n_dropped], dtype=np.int64)
    return out


def run(
    cache_dir: Any,
    *,
    exchange: str = "bybit",
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    skip_fingerprint_check: bool = False,
    expected_fingerprints: dict[str, str] | None = None,
    source: str = "",
) -> dict[str, Any]:
    """Run the registered H-20 measurement (gate-neutral payload)."""
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

    per_symbol = {}
    n_dropped_total = 0
    for sym in symbols:
        ev = collect_events(cache_dir, exchange, sym)
        n_dropped_total += int(ev.get("n_dropped_data", [0])[0])
        per_symbol[sym] = ev
        print(f"[c20] {sym}: {ev['y_bp'].size} events "
              f"({int(ev.get('n_dropped_data', [0])[0])} dropped for data quality)",
              file=sys.stderr, flush=True)

    cells: list[dict[str, Any]] = []
    symbol_report: list[dict[str, Any]] = []
    for w_label, (w_start, w_end) in WINDOWS:
        d0, d1 = _epoch_day(w_start), _epoch_day(w_end)
        ys, ds = [], []
        for sym in symbols:
            ev = per_symbol[sym]
            in_w = (ev["event_day"] >= d0) & (ev["event_day"] <= d1)
            ys.append(ev["y_bp"][in_w])
            ds.append(ev["event_day"][in_w])
            if w_label in JUDGMENT_WINDOWS:
                yy = ev["y_bp"][in_w]
                symbol_report.append({
                    "symbol": sym, "window": w_label, "n_events": int(yy.size),
                    "mean_bp": float(np.mean(yy)) if yy.size else None,
                    "judgment_bearing": False,
                })
        y = np.concatenate(ys) if ys else np.empty(0)
        d = np.concatenate(ds) if ds else np.empty(0)
        n_event_days = int(np.unique(d).size)
        n_events = int(y.size)
        mean_bp = float(np.mean(y)) if n_events else None
        p = day_clustered_boot_p(y, d) if n_events else 1.0
        cells.append({
            "window": w_label, "window_range": [w_start, w_end],
            "judgment_bearing": w_label in JUDGMENT_WINDOWS,
            "n_events": n_events, "n_event_days": n_event_days,
            "n_days_floor": N_EVENT_DAYS_FLOOR,
            "floor_met": bool(n_event_days >= N_EVENT_DAYS_FLOOR),
            "mean_aftermath_bp": mean_bp,
            "median_aftermath_bp": float(np.median(y)) if n_events else None,
            "mean_ge_min": bool(mean_bp is not None and mean_bp >= MEAN_MIN_BP),
            "cluster_boot_p": float(p),
        })
        print(f"[c20] {w_label}: n_events={n_events} days={n_event_days} "
              f"mean={mean_bp if mean_bp is None else round(mean_bp, 2)}bp "
              f"p={p:.4f}", file=sys.stderr, flush=True)

    judgment = [c for c in cells if c["judgment_bearing"]]
    rejected, p_crit = benjamini_hochberg(
        [c["cluster_boot_p"] for c in judgment], FDR_ALPHA)
    for c, rej in zip(judgment, rejected):
        c["fdr_significant"] = bool(rej)
        c["boot_p_le_max"] = bool(c["cluster_boot_p"] <= BOOT_P_MAX)
        c["cell_pass"] = bool(c["floor_met"] and c["mean_ge_min"]
                              and c["boot_p_le_max"] and c["fdr_significant"])
    verdict_evaluable = all(c["floor_met"] for c in judgment)
    both_pass = bool(judgment) and all(c["cell_pass"] for c in judgment)

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
        "windows": {k: list(v) for k, v in WINDOWS},
        "method": {
            "event": (f"|r_hour| >= {SIGMA_MULT} x sigma; sigma = 1.4826 x "
                      f"rolling MAD of previous <= {SCALE_WINDOW_HOURS} hourly "
                      f"returns (>= {SCALE_MIN_HOURS}), strictly causal; hour "
                      f"candidate needs >= {MIN_BARS_PER_HOUR} minute bars; "
                      f"non-overlap {HORIZON_HOURS} h, first event wins"),
            "aftermath": (f"y = -sign(r_event) x logmove(t0+{GAP_HOURS}h -> "
                          f"t0+{HORIZON_HOURS}h) in bp; data-quality floors: "
                          f">= {AFTERMATH_MIN_MINUTES} minutes present, "
                          f"boundary bars within {BOUNDARY_TOLERANCE_MIN} min"),
            "statistic": ("pooled over symbols; day-clustered bootstrap "
                          f"(cluster = UTC event day, {N_BOOTSTRAP} reps, "
                          f"seed {SEED}) for H0: E[y] <= 0"),
        },
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "fdr_p_crit": float(p_crit),
        "gate_thresholds": {"mean_min_bp": MEAN_MIN_BP,
                            "boot_p_max": BOOT_P_MAX,
                            "n_event_days_floor": N_EVENT_DAYS_FLOOR},
        "n_events_dropped_data_quality": int(n_dropped_total),
        "cells": cells,
        "per_symbol_report": symbol_report,
        "verdict_evaluable": bool(verdict_evaluable),
        "both_windows_pass": bool(both_pass),
    }


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------

def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# H-20 — TAIL-AFTERMATH: Nachbewegung nach 3,5-sigma-Stunden (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC) · Status: {payload['status']}")
    L.append(f"- **Datenbindung:** WP-0-Bar-Cache · `gate_valid="
             f"{str(payload['gate_valid']).lower()}`")
    L.append(f"- **Event:** {payload['method']['event']}")
    L.append(f"- **Outcome:** {payload['method']['aftermath']}")
    L.append(f"- **Statistik:** {payload['method']['statistic']}")
    g = payload["gate_thresholds"]
    L.append(f"- **Gate:** BEIDE OOS-Fenster gepoolt: mean >= +{g['mean_min_bp']:.0f} bp "
             f"UND p <= {g['boot_p_max']} nach BH-FDR alpha={payload['fdr_alpha']} "
             f"ueber {payload['fdr_family']}; N-Floor {g['n_event_days_floor']} "
             f"Event-Tage/Fenster (darunter KEIN VERDIKT). Hartes Ein-Fenster-DROP.")
    L.append("")
    L.append("> A-priori (registriert): offen, ~30-40 % WEITER. bp-Groessen sind "
             "Preisbewegungs-Messgroessen; Monetarisierung waere NEUE H-20b.")
    L.append("")
    L.append("## Gepoolte Zellen")
    L.append("")
    L.append("| Fenster | urteilstragend | Events | Event-Tage | Floor | mean bp | median bp | >= +10 | boot-p | FDR | Zelle |")
    L.append("|---|:---:|---:|---:|:---:|---:|---:|:---:|---:|:---:|:---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['window']} | {'ja' if c['judgment_bearing'] else 'nein'} | "
            f"{c['n_events']} | {c['n_event_days']} | "
            f"{'ok' if c['floor_met'] else '**RISS**'} | "
            f"{_fmt(c['mean_aftermath_bp'])} | {_fmt(c['median_aftermath_bp'])} | "
            f"{'ja' if c['mean_ge_min'] else 'nein'} | {c['cluster_boot_p']:.4f} | "
            f"{_yn(c.get('fdr_significant'))} | {_yn(c.get('cell_pass'), 'PASS')} |")
    L.append("")
    L.append(f"**Beide urteilstragenden Fenster PASS:** "
             f"{'ja' if payload['both_windows_pass'] else 'nein'} · "
             f"**Verdikt auswertbar (N-Floor):** "
             f"{'ja' if payload['verdict_evaluable'] else 'NEIN — kein Verdikt'} · "
             f"Datenqualitaets-Drops: {payload['n_events_dropped_data_quality']}")
    L.append("")
    L.append("## Per-Symbol (mitberichtet, NICHT urteilstragend)")
    L.append("")
    L.append("| Symbol | Fenster | Events | mean bp |")
    L.append("|---|---|---:|---:|")
    for r in payload["per_symbol_report"]:
        L.append(f"| {r['symbol']} | {r['window']} | {r['n_events']} | "
                 f"{_fmt(r['mean_bp'])} |")
    L.append("")
    L.append("*Erzeugt von `c20_tail/driver.py` — liest AUSSCHLIESSLICH den "
             "WP-0-Bar-Cache. capital_free=true. Gate-Urteil: gate-auditor "
             "gegen H-20.*")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    return "—" if v is None else f"{float(v):+.2f}"


def _yn(v: Any, yes: str = "ja") -> str:
    if v is None:
        return "—"
    return yes if v else "nein"


__all__ = [
    "DEFAULT_SYMBOLS",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "REGISTERED_FINGERPRINTS",
    "aftermath_bp",
    "causal_mad_scale",
    "collect_events",
    "day_clustered_boot_p",
    "find_events",
    "hourly_series",
    "render_markdown",
    "run",
]
