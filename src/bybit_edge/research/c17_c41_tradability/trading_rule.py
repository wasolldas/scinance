"""Pre-fixed Lead-Lag trading rule for the C-17/C-41 tradability-gate (H-04b).

NON-KAPITALFREI (registry H-04b, ``capital_free=false``): unlike the H-04
mess-gate (``c17_c41_lead_lag``, ``capital_free=true``) this module DOES confront
the friction wall and a latency haircut. It is nonetheless a *historical backtest
with a cost model* on the read-only ``trades`` stock — NO live-order code, NO
real capital (CLAUDE.md §4 / Autonomie-Protokoll §3).

The trading rule is fixed VOR run-start (registry H-04b Z.124, DEC-13):

* the **BTC return over a window up to ``t``** predicts the SIGN of the ETH
  return over ``[t + lag, t + lag + horizon]`` (in grid bars; ``horizon = lag``
  by DEC-13 default);
* on a non-flat signal, take a (sign-of-signal) position in ETH at ``t`` and
  unwind it after ``horizon``;
* ``lag`` is restricted to the H-04 survivor set {1, 2, 3} grid steps (GL-006
  FDR survivors TE-lag1/2/3; lag5/lag10 decayed and are NOT tested).

THE LATENCY HAIRCUT (the crux, registry H-04b Z.128, DEC-13c) lives here, in
:func:`captured_eth_move`: the move the trader can actually capture is ONLY the
part of the lead-move AFTER ``t + latency_ms`` — i.e. ``ret_ETH`` over
``[t + latency_ms, t + (lag + horizon) * grid_ms]``, NOT the full lead-move over
``[t, ...]``. The cut is strictly causal (last-trade price at-or-before each
boundary timestamp via ``searchsorted``, no interpolation, no look-ahead).

Everything is measured directly off the raw ``(ts_ms, price)`` ticks so the
sub-bar ``t + latency_ms`` boundary (e.g. 300 ms on a 1000 ms grid) is honoured
exactly rather than being rounded to a bar edge — a bar-rounded haircut would
silently weaken the wall and is forbidden by the anti-gaming clause.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: H-04 survivor lag set (GL-006 FDR survivors TE-lag1/2/3, grid steps). lag5/
#: lag10 decayed in H-04 and are NOT tradable territory (registry H-04b Z.124).
SURVIVOR_LAGS: tuple[int, ...] = (1, 2, 3)


@dataclass(slots=True)
class RoundTrip:
    """One signalled round-trip (enter ETH at t, unwind after horizon).

    All returns are signed *directional* log-returns already multiplied by the
    position sign, i.e. ``captured_move`` is the gross PnL of the trade in
    log-return units BEFORE friction/slippage (positive = the rule was right).
    """

    t_ms: float
    signal_btc_ret: float        # raw BTC signal return over the window up to t
    position_sign: int           # +1 / -1, sign of the BTC signal (0 -> no trade)
    eth_move_full: float         # directional ETH move over [t, t+(lag+h)] (no haircut)
    eth_move_captured: float     # directional ETH move over [t+latency, t+(lag+h)]


def _price_at_or_before(ts_sorted: np.ndarray, px: np.ndarray, t_query: float) -> float:
    """Last trade price at-or-before ``t_query`` (strictly backward-looking).

    Uses ``searchsorted`` on the sorted tick timestamps; returns ``nan`` if no
    tick exists at-or-before ``t_query`` (so the caller can drop the round-trip).
    No interpolation across the boundary -> no look-ahead.
    """
    if ts_sorted.size == 0:
        return float("nan")
    # idx = number of ticks with ts <= t_query; the last such tick is idx-1.
    idx = int(np.searchsorted(ts_sorted, t_query, side="right")) - 1
    if idx < 0:
        return float("nan")
    return float(px[idx])


def _log_ret(p0: float, p1: float) -> float:
    if not (np.isfinite(p0) and np.isfinite(p1)) or p0 <= 0.0 or p1 <= 0.0:
        return float("nan")
    return float(np.log(p1 / p0))


def captured_eth_move(
    ts_eth: np.ndarray,
    px_eth: np.ndarray,
    t_ms: float,
    *,
    lag: int,
    horizon: int,
    grid_ms: float,
    latency_ms: float,
) -> tuple[float, float]:
    """Directional ETH log-move over the FULL and the LATENCY-HAIRCUT windows.

    Returns ``(full_move, captured_move)`` where

    * ``full_move``     = ``log(P_ETH[t + (lag+horizon)*grid] / P_ETH[t])``
      (the whole lead-move, reported for diagnostics — NEVER the pass quantity),
    * ``captured_move`` = ``log(P_ETH[t + (lag+horizon)*grid] / P_ETH[t + latency])``
      (the haircut move — the ONLY part a latency-bound trader can realise).

    Both legs read the last trade price at-or-before the boundary timestamp
    (causal). The unwind boundary ``t + (lag+horizon)*grid_ms`` is identical for
    both legs; only the ENTRY boundary differs (``t`` vs ``t + latency_ms``),
    which is exactly the latency haircut. ``nan`` is returned for a leg whose
    boundary has no tick at-or-before it.
    """
    t_exit = t_ms + (lag + horizon) * grid_ms
    t_entry_full = t_ms
    t_entry_hc = t_ms + latency_ms

    p_entry_full = _price_at_or_before(ts_eth, px_eth, t_entry_full)
    p_entry_hc = _price_at_or_before(ts_eth, px_eth, t_entry_hc)
    p_exit = _price_at_or_before(ts_eth, px_eth, t_exit)

    return _log_ret(p_entry_full, p_exit), _log_ret(p_entry_hc, p_exit)


def btc_signal_return(
    ts_btc: np.ndarray,
    px_btc: np.ndarray,
    t_ms: float,
    *,
    lag: int,
    grid_ms: float,
) -> float:
    """BTC log-return over the window ``[t - lag*grid_ms, t]`` (causal signal).

    The signal window length equals ``lag`` bars, mirroring the H-04 TE
    structure (BTC's past at the tested lag predicts ETH's future). Both
    boundaries read the last trade price at-or-before them (no look-ahead beyond
    ``t``). Returns ``nan`` if either boundary has no tick.
    """
    t_start = t_ms - lag * grid_ms
    p0 = _price_at_or_before(ts_btc, px_btc, t_start)
    p1 = _price_at_or_before(ts_btc, px_btc, t_ms)
    return _log_ret(p0, p1)


def generate_round_trips(
    ts_btc: np.ndarray,
    px_btc: np.ndarray,
    ts_eth: np.ndarray,
    px_eth: np.ndarray,
    *,
    lag: int,
    horizon: int,
    grid_ms: float,
    latency_ms: float,
    signal_eps: float = 0.0,
) -> list[RoundTrip]:
    """Run the pre-fixed lead-lag rule over a window and return its round-trips.

    Signal times ``t`` are placed on a regular ``grid_ms`` raster spanning the
    overlapping tick range of both symbols, with enough head-room on each side
    for the ``lag``-bar signal window and the ``(lag+horizon)``-bar capture
    window (so no boundary falls outside the data). Each ``t`` with a non-flat
    BTC signal (``|signal| > signal_eps``) yields one round-trip; the position
    sign is ``sign(signal)`` and the captured/full ETH moves are taken
    DIRECTIONALLY (multiplied by the position sign).

    Strictly causal: the signal uses only prices up to ``t``; the capture window
    starts at ``t + latency_ms`` and ends at ``t + (lag+horizon)*grid_ms``.
    """
    ts_btc = np.asarray(ts_btc, dtype=np.float64)
    ts_eth = np.asarray(ts_eth, dtype=np.float64)
    px_btc = np.asarray(px_btc, dtype=np.float64)
    px_eth = np.asarray(px_eth, dtype=np.float64)
    if ts_btc.size < 2 or ts_eth.size < 2:
        return []

    t0 = max(float(ts_btc[0]), float(ts_eth[0]))
    t1 = min(float(ts_btc[-1]), float(ts_eth[-1]))
    if t1 <= t0:
        return []

    # Head-room: a signal at t needs a BTC tick at t-lag*grid, and the capture
    # window needs an ETH tick at t+(lag+horizon)*grid.
    span = (lag + horizon) * grid_ms
    first_t = t0 + lag * grid_ms
    last_t = t1 - span
    if last_t <= first_t:
        return []

    n_signals = int(np.floor((last_t - first_t) / grid_ms)) + 1
    if n_signals < 1:
        return []
    signal_times = first_t + grid_ms * np.arange(n_signals, dtype=np.float64)

    trips: list[RoundTrip] = []
    for t in signal_times:
        sig = btc_signal_return(ts_btc, px_btc, float(t), lag=lag, grid_ms=grid_ms)
        if not np.isfinite(sig) or abs(sig) <= signal_eps:
            continue
        pos = 1 if sig > 0.0 else -1
        full, captured = captured_eth_move(
            ts_eth, px_eth, float(t),
            lag=lag, horizon=horizon, grid_ms=grid_ms, latency_ms=latency_ms,
        )
        if not np.isfinite(captured) or not np.isfinite(full):
            continue
        trips.append(
            RoundTrip(
                t_ms=float(t),
                signal_btc_ret=float(sig),
                position_sign=pos,
                eth_move_full=float(pos * full),
                eth_move_captured=float(pos * captured),
            )
        )
    return trips
