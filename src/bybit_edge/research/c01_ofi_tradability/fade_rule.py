"""Pre-fixed OFI-FADE trading rule for the C-01 tradability-gate (H-05c).

NON-KAPITALFREI (registry H-05c, ``capital_free=false``): unlike the H-05b
mess-gate (``c01_ofi_sign``, ``capital_free=true``) this module DOES confront the
friction wall and a latency haircut. It is nonetheless a *historical backtest
with a cost model* on the read-only harvester ``trades`` backfill — NO live-order
code, NO real capital (CLAUDE.md §4).

The trading rule is fixed VOR run-start (registry H-05c, DEC-16):

* the **sign of ``OFI_t``** (aggressor-signed volume in the grid bin ending at
  ``t``) predicts the INVERSE sign of the SOL return over ``[t, t+delta]``
  (MM-replenishment / fade — the GL-010 finding);
* on a non-flat signal, take a **fade** position ``-sign(OFI_t)`` at ``t`` and
  unwind it after ``horizon = delta`` (DEC-16), i.e. at ``t + delta`` seconds;
* ``delta`` is restricted to the GL-010 survivor set {1 s, 5 s} (the only
  >=2-window inverse-consistent H-05b cells on SOL); other deltas are NOT
  pass-bearing (anti-gaming clause).

THE LATENCY HAIRCUT (the crux, registry H-05c, DEC-16) lives in
:func:`captured_sol_move`: the move the trader can actually capture is ONLY the
part AFTER ``t + latency_ms`` — ``ret_SOL`` over ``[t + latency_ms, t + delta]``,
NOT the full move over ``[t, ...]``. Strictly causal (last trade price
at-or-before each boundary via ``searchsorted``, no interpolation, no look-ahead).
At ``delta = 1 s`` a 300 ms haircut removes ~30 % of the window — deliberately strict.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bybit_edge.research.c01_ofi_sign.ofi import signed_volume

#: GL-010 survivor delta set (the only >=2-window inverse-consistent SOL cells).
SURVIVOR_DELTAS_S: tuple[int, ...] = (1, 5)


@dataclass(slots=True)
class RoundTrip:
    """One signalled fade round-trip (enter SOL at t against OFI, unwind at t+delta).

    All returns are signed *directional* log-returns already multiplied by the
    FADE position sign, i.e. ``sol_move_captured`` is the gross PnL of the trade
    in log-return units BEFORE friction/slippage (positive = the fade was right).
    """

    t_ms: float
    ofi: float                   # aggressor-signed volume in the bin ending at t
    position_sign: int           # -sign(OFI): the fade direction (0 -> no trade)
    sol_move_full: float         # directional SOL move over [t, t+delta] (no haircut)
    sol_move_captured: float     # directional SOL move over [t+latency, t+delta]


def _price_at_or_before(ts_sorted: np.ndarray, px: np.ndarray, t_query: float) -> float:
    """Last trade price at-or-before ``t_query`` (strictly backward-looking)."""
    if ts_sorted.size == 0:
        return float("nan")
    idx = int(np.searchsorted(ts_sorted, t_query, side="right")) - 1
    if idx < 0:
        return float("nan")
    return float(px[idx])


def _log_ret(p0: float, p1: float) -> float:
    if not (np.isfinite(p0) and np.isfinite(p1)) or p0 <= 0.0 or p1 <= 0.0:
        return float("nan")
    return float(np.log(p1 / p0))


def captured_sol_move(
    ts: np.ndarray,
    px: np.ndarray,
    t_ms: float,
    *,
    delta_s: int,
    grid_ms: float,
    latency_ms: float,
) -> tuple[float, float]:
    """Directional SOL log-move over the FULL and the LATENCY-HAIRCUT windows.

    Returns ``(full_move, captured_move)`` where the prediction/capture window
    ends at ``t + delta_s * 1000 ms`` (horizon = delta, DEC-16):

    * ``full_move``     = ``log(P[t + delta] / P[t])`` (diagnostic, NEVER the pass quantity),
    * ``captured_move`` = ``log(P[t + delta] / P[t + latency_ms])`` (the haircut move).

    ``grid_ms`` is unused for the capture boundaries (delta is in seconds) but is
    accepted for signature symmetry with the lead-lag rule. ``nan`` for a leg
    whose boundary has no tick at-or-before it.
    """
    t_exit = t_ms + delta_s * 1000.0
    p_entry_full = _price_at_or_before(ts, px, t_ms)
    p_entry_hc = _price_at_or_before(ts, px, t_ms + latency_ms)
    p_exit = _price_at_or_before(ts, px, t_exit)
    return _log_ret(p_entry_full, p_exit), _log_ret(p_entry_hc, p_exit)


def _bin_ofi(
    ts: np.ndarray, signed_vol: np.ndarray, t0: float, grid_ms: float, n_bins: int
) -> np.ndarray:
    """Aggregate aggressor-signed volume into ``n_bins`` fixed-width bins from t0."""
    ofi = np.zeros(n_bins, dtype=np.float64)
    if ts.size == 0:
        return ofi
    idx = np.floor((ts - t0) / grid_ms).astype(np.int64)
    m = (idx >= 0) & (idx < n_bins)
    np.add.at(ofi, idx[m], signed_vol[m])
    return ofi


def generate_round_trips(
    ts: np.ndarray,
    px: np.ndarray,
    volume: np.ndarray,
    side: np.ndarray,
    *,
    delta_s: int,
    grid_ms: float,
    latency_ms: float,
    signal_eps: float = 0.0,
) -> list[RoundTrip]:
    """Run the pre-fixed OFI-fade rule over a window and return its round-trips.

    OFI is the aggressor-signed volume in each ``grid_ms`` bin. A bin ending at
    ``t`` with ``|OFI| > signal_eps`` yields one round-trip: the FADE position
    ``-sign(OFI)`` enters SOL at ``t`` and unwinds at ``t + delta_s`` seconds; the
    captured move is taken DIRECTIONALLY (× fade sign) over the latency-haircut
    window ``[t + latency_ms, t + delta_s]``.

    Strictly causal: OFI uses only trades up to ``t``; the capture window starts
    at ``t + latency_ms`` (>= t) and ends at ``t + delta``.
    """
    ts = np.asarray(ts, dtype=np.float64)
    px = np.asarray(px, dtype=np.float64)
    volume = np.asarray(volume, dtype=np.float64)
    side = np.asarray(side)
    if ts.size < 2:
        return []

    t0 = float(ts[0])
    t1 = float(ts[-1])
    span_ms = delta_s * 1000.0
    # need: a full bin [t-grid, t] before each signal, and a capture window
    # [t, t+delta] after -> last signal time t such that t+delta <= t1.
    last_t = t1 - span_ms
    if last_t <= t0 + grid_ms:
        return []

    sv = signed_volume(volume, side)
    n_bins = int(np.floor((last_t - t0) / grid_ms)) + 1
    if n_bins < 1:
        return []
    ofi = _bin_ofi(ts, sv, t0, grid_ms, n_bins)

    trips: list[RoundTrip] = []
    for k in range(n_bins):
        t = t0 + (k + 1) * grid_ms  # bin END = signal time
        o = float(ofi[k])
        if not np.isfinite(o) or abs(o) <= signal_eps:
            continue
        pos = -1 if o > 0.0 else 1  # FADE: opposite to aggressor flow
        full, captured = captured_sol_move(
            ts, px, float(t), delta_s=delta_s, grid_ms=grid_ms, latency_ms=latency_ms,
        )
        if not np.isfinite(captured) or not np.isfinite(full):
            continue
        trips.append(
            RoundTrip(
                t_ms=float(t),
                ofi=o,
                position_sign=pos,
                sol_move_full=float(pos * full),
                sol_move_captured=float(pos * captured),
            )
        )
    return trips
