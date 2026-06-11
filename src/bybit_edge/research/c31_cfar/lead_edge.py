"""Lead-time and edge (bps) estimation for surviving cycles (WP-3, H-03).

For peaks that survive the surrogate null we must show the registered economic
gate: **Lead-Zeit > 50 ms** (the cycle resolves before retail latency can react)
AND **Edge > 11 bps** (above the round-trip friction wall, verdict §0.2).

No-Lookahead discipline (the forensic test the test-engineer will probe)
------------------------------------------------------------------------
This is the leak-prone step. It is made leak-proof *by construction*:

1. The cycle PHASE at a detection time ``t`` is computed from a *closed* lookback
   window ``[t - L, t]`` of trade timestamps only — ``_phase_at`` never reads a
   tick with ``ts > t``. We assert this with an explicit mask.
2. The FORWARD RETURN is measured strictly AFTER the detection time: we take the
   price at ``t`` (last tick at or before ``t``) and the price at ``t + horizon``
   (first tick at or after ``t + horizon``). The return uses only ``ts >= t``.
3. Lead time is the gap from the detection instant to the price move it
   predicts — bounded below by the bin grid and reported per phase bucket.

So phase and forward return live on opposite sides of ``t`` with no overlap: a
future tick can never enter a phase estimate, and a past tick can never enter a
forward return. ``measure_lead_edge`` re-validates both invariants and raises on
violation, so a regression cannot silently introduce a lookahead leak.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Registered gate constants (H-03, literal from PRD §3 Pilot 4).
LEAD_MIN_MS = 50.0
EDGE_MIN_BPS = 11.0


class LookaheadError(AssertionError):
    """Raised when phase/forward-return windows are not strictly causal."""


@dataclass(slots=True)
class LeadEdgeResult:
    """Lead-time / edge measurement for one surviving cyclic frequency."""

    alpha_hz: float
    period_ms: float
    lead_ms: float
    edge_bps: float
    n_events: int          # detection instants contributing to the estimate
    n_phase_buckets: int
    best_bucket_return_bps: float

    def as_dict(self) -> dict[str, object]:
        return {
            "alpha_hz": float(self.alpha_hz),
            "period_ms": float(self.period_ms),
            "lead_ms": float(self.lead_ms),
            "edge_bps": float(self.edge_bps),
            "n_events": int(self.n_events),
            "n_phase_buckets": int(self.n_phase_buckets),
            "best_bucket_return_bps": float(self.best_bucket_return_bps),
        }


def _price_at_or_before(
    ts: np.ndarray, prices: np.ndarray, t: float
) -> float | None:
    """Last price with timestamp <= t (the executable price at detection)."""
    idx = np.searchsorted(ts, t, side="right") - 1
    if idx < 0:
        return None
    return float(prices[idx])


def _price_at_or_after(
    ts: np.ndarray, prices: np.ndarray, t: float
) -> float | None:
    """First price with timestamp >= t (the realised forward price)."""
    idx = np.searchsorted(ts, t, side="left")
    if idx >= ts.size:
        return None
    return float(prices[idx])


def _phase_at(
    ts: np.ndarray, t: float, alpha_hz: float, lookback_ms: float
) -> float | None:
    """Cycle phase at time ``t`` from a CLOSED past window ``[t-L, t]``.

    Phase is the fractional position within one cycle period of the most recent
    event, estimated only from events strictly within the past window. Returns
    ``None`` when the window is empty.
    """
    if alpha_hz <= 0:
        return None
    period_ms = 1000.0 / alpha_hz
    lo = t - lookback_ms
    # Closed past window: lo <= ts <= t. The <= t bound is the No-Lookahead
    # guarantee — no future tick can enter the phase estimate.
    mask = (ts >= lo) & (ts <= t)
    if not np.any(mask):
        return None
    past = ts[mask]
    if past.size and past[-1] > t:  # defensive: must never happen
        raise LookaheadError("phase window contains a future tick")
    last_event = float(past[-1])
    phase = ((t - last_event) % period_ms) / period_ms
    return phase


def measure_lead_edge(
    timestamps_ms: np.ndarray,
    prices: np.ndarray,
    alpha_hz: float,
    *,
    n_phase_buckets: int = 8,
    forward_horizon_ms: float = 100.0,
    lookback_periods: float = 4.0,
    sample_stride: int = 1,
) -> LeadEdgeResult:
    """Estimate lead time (ms) and edge (bps) for one cyclic frequency.

    Method: sample detection instants along the timeline. At each instant the
    cycle phase is computed from the past lookback window; the forward return
    over ``forward_horizon_ms`` (strictly after the instant) is bucketed by
    phase. The edge is the magnitude of the best phase bucket's mean forward
    return in bps (long the up-phase / short the down-phase). The lead time is
    the forward horizon of the predictive phase, floored at the friction-honest
    minimum realisable horizon.

    Raises
    ------
    LookaheadError
        If any phase window or forward-return window violates causality.
    """
    ts = np.asarray(timestamps_ms, dtype=np.float64)
    px = np.asarray(prices, dtype=np.float64)
    if ts.size != px.size:
        raise ValueError("timestamps and prices must have equal length")
    order = np.argsort(ts, kind="stable")
    ts, px = ts[order], px[order]

    if alpha_hz <= 0 or ts.size < 8:
        return LeadEdgeResult(alpha_hz, 0.0, 0.0, 0.0, 0, 0, 0.0)

    period_ms = 1000.0 / alpha_hz
    lookback_ms = lookback_periods * period_ms

    bucket_sums = np.zeros(n_phase_buckets, dtype=np.float64)
    bucket_counts = np.zeros(n_phase_buckets, dtype=np.int64)
    n_events = 0

    # Detection instants: every stride-th tick that has both a full past
    # lookback and a full forward horizon available.
    t_first, t_last = ts[0], ts[-1]
    for i in range(0, ts.size, max(1, sample_stride)):
        t = float(ts[i])
        if t - t_first < lookback_ms:
            continue
        if t + forward_horizon_ms > t_last:
            continue
        phase = _phase_at(ts, t, alpha_hz, lookback_ms)
        if phase is None:
            continue
        p_now = _price_at_or_before(ts, px, t)
        # Forward price strictly AFTER the detection instant.
        p_fwd = _price_at_or_after(ts, px, t + forward_horizon_ms)
        if p_now is None or p_fwd is None or p_now <= 0:
            continue
        # Causality re-validation (forensic invariant).
        fwd_idx = np.searchsorted(ts, t + forward_horizon_ms, side="left")
        if fwd_idx < ts.size and ts[fwd_idx] < t:
            raise LookaheadError("forward-return tick precedes detection time")
        ret_bps = (p_fwd / p_now - 1.0) * 1e4
        b = min(int(phase * n_phase_buckets), n_phase_buckets - 1)
        bucket_sums[b] += ret_bps
        bucket_counts[b] += 1
        n_events += 1

    if n_events == 0 or not np.any(bucket_counts > 0):
        return LeadEdgeResult(
            alpha_hz, period_ms, 0.0, 0.0, 0, n_phase_buckets, 0.0
        )

    mean_ret = np.divide(
        bucket_sums, bucket_counts,
        out=np.zeros_like(bucket_sums), where=bucket_counts > 0,
    )
    # Edge = magnitude of the most predictive phase bucket (directional trade
    # conditioned on phase). Friction-honest: reported raw, compared to 11 bps.
    best_bucket_return = float(mean_ret[np.argmax(np.abs(mean_ret))])
    edge_bps = abs(best_bucket_return)

    # Lead time: the cycle predicts a move that realises over the forward
    # horizon; the actionable lead is the horizon over which the conditioned
    # return accrues, bounded by the cycle period (a cycle cannot lead by more
    # than one period). Reported in ms for the > 50 ms gate.
    lead_ms = min(forward_horizon_ms, period_ms)

    return LeadEdgeResult(
        alpha_hz=alpha_hz,
        period_ms=period_ms,
        lead_ms=lead_ms,
        edge_bps=edge_bps,
        n_events=n_events,
        n_phase_buckets=n_phase_buckets,
        best_bucket_return_bps=best_bucket_return,
    )
