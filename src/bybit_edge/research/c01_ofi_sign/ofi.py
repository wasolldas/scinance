"""Own narrow OFI estimator + causal forward-return aligner for the C-01
OFI-sign mess-gate (Welle-2 WP, H-05, KAPITALFREI).

H-05 tests one thing only: the *sign* of the conditional relation
``sign(OFI_t) -> sign(forward_return_{t+delta})`` on the existing ``trades``
stream — does aggressive order flow LEAD price in the same direction
(aggression-follows reading, PRD-v1 / CS-02) or the inverse direction (the
MM-replenishment reading that the S2 implementation produced, INC-02 anchor,
E-04 hit_sum 0.179)? This module builds the estimator; ``sign_test.py`` runs
the per-delta sign / correlation / hit-rate statistics; the GATE VERDICT is the
gate-auditor's call.

Why an OWN estimator and NOT the existing ``l1_ingestion/m2_ofi.py`` (DEC-11):
the bestand ``M2OFI`` is a *book-update* OFI (Cont-Kukanov-Stoikov ``e_n`` from
best-bid/ask price+size changes), it carries the known C-01/C-02 swap
(Survey §2.1), it is stateful/streaming (rolling deque, Q90 signal) and consumes
orderbook BBO updates, not the persisted ``trades`` table. Reusing it would
(a) couple this falsification test to the very implementation under suspicion
and (b) require an orderbook stream this gate does not use. Instead we build a
reproducible, documented, batch trade-flow OFI directly from the ``trades``
aggressor side, so the H-05 verdict does not hinge on the suspect module. The
bestand ``m2_ofi.py`` is read-only and left completely untouched.

OFI definition used here (trade-flow / aggressor-signed volume imbalance):

    signed_qty_i = +volume_i  if side_i == "Buy"   (taker hit the ask)
                   -volume_i  if side_i == "Sell"  (taker hit the bid)
    OFI_t        = sum of signed_qty_i over all trades with ts in bin t

The Bybit V5 ``publicTrade`` ``side`` field (persisted as ``trades.side``,
mirrored by ``TradeEvent.signed_volume``) marks the AGGRESSOR / taker side, so
this is exactly the aggressive-flow imbalance the registry asks for
(Survey §2.1: "taker_buy/Aggressor-Markierung").

Strict causality (NO look-ahead): OFI_t is built ONLY from trades inside bin
``[t, t+grid)``. The forward return for bin t is the log mid/last-price change
over the FORWARD horizon ``(t_end_of_bin, t_end_of_bin + delta]`` — it uses only
prices at or after the bin closes, so OFI_t and ret_{t+delta} never share a
trade and the return window never reaches back into the bin that produced OFI_t.
"""
from __future__ import annotations

import numpy as np

#: Default OFI bin width in milliseconds (DEC-11). 1000 ms bars from the
#: publicTrade stream — fine enough for the 1-5 s short-interval scale of the
#: C-01 claim, coarse enough for a stable per-bin OFI aggregate. CLI ``--grid-ms``.
DEFAULT_GRID_MS = 1000.0

#: Default forward-return lags (seconds), pre-fixed per registry H-05:
#: delta in {1s, 5s, 15s, 60s, 300s} (claims_register C-01). Each delta counts
#: individually in the F-OFI family.
DEFAULT_LAGS_S: tuple[int, ...] = (1, 5, 15, 60, 300)


def signed_volume(volume: np.ndarray, side: np.ndarray) -> np.ndarray:
    """Aggressor-signed trade volume: +vol for ``Buy`` takers, -vol for ``Sell``.

    Mirrors ``TradeEvent.signed_volume`` (state/trade_buffer.py). ``side`` is the
    Bybit ``publicTrade`` taker side. Anything that is not exactly ``"Buy"`` is
    treated as a sell (matching the bestand convention ``vol if side=="Buy"``).
    """
    volume = np.asarray(volume, dtype=np.float64)
    side = np.asarray(side)
    sign = np.where(side == "Buy", 1.0, -1.0)
    return sign * volume


def bin_ofi(
    ts_ms: np.ndarray,
    signed_qty: np.ndarray,
    grid_ms: float,
    *,
    t0_ms: float | None = None,
    t1_ms: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Aggregate signed trade volume into fixed-width time bins.

    Returns ``(bin_end_ms, ofi)`` where ``bin_end_ms[t]`` is the right edge
    (exclusive upper bound) of bin ``t`` and ``ofi[t]`` the summed signed volume
    of all trades with ``ts in [bin_start, bin_end)``. Empty bins yield OFI 0.0
    (no trades = no aggressive flow), keeping the time axis regular so the causal
    forward-return alignment is well defined.
    """
    ts_ms = np.asarray(ts_ms, dtype=np.float64)
    signed_qty = np.asarray(signed_qty, dtype=np.float64)
    if ts_ms.size == 0:
        return np.zeros(0), np.zeros(0)
    if grid_ms <= 0:
        raise ValueError(f"grid_ms must be > 0, got {grid_ms}")
    lo = float(ts_ms[0]) if t0_ms is None else float(t0_ms)
    hi = float(ts_ms[-1]) if t1_ms is None else float(t1_ms)
    if hi <= lo:
        return np.zeros(0), np.zeros(0)
    n_bins = int(np.floor((hi - lo) / grid_ms)) + 1
    if n_bins < 1:
        return np.zeros(0), np.zeros(0)
    idx = np.floor((ts_ms - lo) / grid_ms).astype(np.int64)
    in_range = (idx >= 0) & (idx < n_bins)
    idx = idx[in_range]
    sq = signed_qty[in_range]
    ofi = np.zeros(n_bins, dtype=np.float64)
    if idx.size:
        np.add.at(ofi, idx, sq)
    # Right edge (exclusive) of each bin = lo + (k+1)*grid_ms.
    bin_end = lo + (np.arange(n_bins, dtype=np.float64) + 1.0) * grid_ms
    return bin_end, ofi


def last_price_at(
    ts_ms: np.ndarray,
    price: np.ndarray,
    query_ms: np.ndarray,
) -> np.ndarray:
    """Last observed trade price AT-OR-BEFORE each query time (step / causal).

    For each ``query_ms[i]`` returns the price of the most recent trade with
    ``ts <= query_ms[i]`` (zero-order-hold). Used to read mid/last price at bin
    edges for the forward return. ``ts_ms`` must be sorted ascending. Queries
    before the first trade yield NaN.
    """
    ts_ms = np.asarray(ts_ms, dtype=np.float64)
    price = np.asarray(price, dtype=np.float64)
    query_ms = np.asarray(query_ms, dtype=np.float64)
    # searchsorted 'right' gives count of ts <= query; index-1 is the last <=.
    pos = np.searchsorted(ts_ms, query_ms, side="right") - 1
    out = np.full(query_ms.shape, np.nan, dtype=np.float64)
    valid = pos >= 0
    out[valid] = price[pos[valid]]
    return out


def ofi_and_forward_return(
    ts_ms: np.ndarray,
    price: np.ndarray,
    volume: np.ndarray,
    side: np.ndarray,
    grid_ms: float,
    delta_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Build aligned ``(OFI_t, forward_log_return_{t+delta})`` pairs (causal).

    * ``OFI_t`` = aggressor-signed volume summed over bin ``[t, t+grid)``.
    * ``forward_return`` = ``log( P(t_end + delta) / P(t_end) )`` where
      ``t_end`` is the bin's right edge and ``P(.)`` is the last trade price at
      or before that time. The return window ``(t_end, t_end+delta]`` lies
      strictly AFTER the bin, so it shares no trade with OFI_t (no look-ahead).

    Bins whose forward window runs past the last trade (price would be NaN) are
    dropped. Returns ``(ofi, fwd_ret)`` of equal length, ready for the sign test.
    """
    ts_ms = np.asarray(ts_ms, dtype=np.float64)
    price = np.asarray(price, dtype=np.float64)
    if ts_ms.size < 2:
        return np.zeros(0), np.zeros(0)
    signed_qty = signed_volume(volume, side)
    bin_end, ofi = bin_ofi(ts_ms, signed_qty, grid_ms)
    if ofi.size == 0:
        return np.zeros(0), np.zeros(0)
    delta_ms = float(delta_s) * 1000.0
    p_now = last_price_at(ts_ms, price, bin_end)
    p_fwd = last_price_at(ts_ms, price, bin_end + delta_ms)
    # Forward window must stay within the observed series: require a real trade
    # at or before (bin_end + delta) that is also strictly after bin_end, i.e.
    # the forward query time does not exceed the last trade timestamp.
    last_ts = float(ts_ms[-1])
    within = (bin_end + delta_ms) <= last_ts
    valid = within & np.isfinite(p_now) & np.isfinite(p_fwd) & (p_now > 0) & (p_fwd > 0)
    ofi_v = ofi[valid]
    with np.errstate(divide="ignore", invalid="ignore"):
        fwd = np.log(p_fwd[valid] / p_now[valid])
    finite = np.isfinite(fwd)
    return ofi_v[finite], fwd[finite]
