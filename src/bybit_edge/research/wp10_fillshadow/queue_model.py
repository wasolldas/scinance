"""WP-10(B) -- passive-quote queue-position fill model (pure functions).

The question (WP10_SPEZIFIKATION.md Teil B): with what probability would a
HYPOTHETICAL own passive quote, joined at the touch at time ``t0`` on side
``s`` with size ``q``, have been FILLED within 10 s / 60 s (design
parameters), reconstructed from public L2 (``orderbook.1000``) and
``publicTrade`` alone?

**Queue position.** We join at the BACK of the visible touch level: our
position (size ahead of us) at ``t0`` is exactly the visible size at that
price, ``pos0``. We are filled once cumulative queue REDUCTION reaches
``pos0 + q`` -- everyone ahead of us, then us.

**The unsolvable half of the problem, made explicit.** A public L2 feed
shows aggregate visible size per price level, never per-order queue
position, and a level-size DECREASE has two indistinguishable causes: a
TRADE (observable, in ``publicTrade``) or a CANCELLATION (never reported
anywhere). We therefore report TWO bounding conventions instead of one
number:

  * **FIFO-conservative** -- only observed trade volume at this exact
    price, on the side that would hit our resting order, reduces our
    queue position. Cancellations are assumed to happen entirely BEHIND
    us (the best case for us). This is a LOWER bound on fill probability
    -- every fill it reports is a real, trade-backed fill.
  * **pro-rata-cancel** -- any level-size decrease NOT explained by
    observed trade volume (``unexplained = max(0, decrease - trade_vol)``)
    is additionally counted toward our cumulative reduction, on the
    assumption that the anonymised decrease could have consumed our own
    resting position (a real possibility: iceberg/hidden fills and
    cancellations are observationally identical from outside). This is an
    UPPER bound -- by construction ``prorata_reduction(t) >=
    fifo_reduction(t)`` pointwise, so a pro-rata fill is NEVER later than
    the FIFO fill of the same quote (when both fill).

Neither bound is "the" fill probability; the true (unobservable) value
lies between them. Both are reported, never averaged into a single
number that would hide which bound produced it.

**Touch departure.** The instant the touch price on our side no longer
equals our quoted price (``touch != price``), the observation is
CENSORED: no further reduction is counted, and an un-filled quote at that
point is "not filled" -- never silently treated as "still queued
forever". This is the ``bevor der Touch wegwandert`` clause of the spec.

**Adverse selection.** ``adv_sel = mid(t_fill + adv_sel_horizon_s) -
fill_price``, SIGNED AGAINST the quote (positive = bad for the maker):
for a bid fill (we bought), the mid dropping below our fill price is
adverse; for an ask fill (we sold), the mid rising above our fill price
is adverse. Reported in bp of the fill price.

KAPITALFREI: a pure measurement model. No cost quantity, no PASS/FAIL --
the ``adv_sel <= 1,75 bp`` LABEL lives in ``report.py``, not here.
"""
from __future__ import annotations

from typing import Any, Sequence

__all__ = [
    "QueueModelError",
    "DEFAULT_HORIZON_S",
    "DEFAULT_ADV_SEL_HORIZON_S",
    "REPORT_HORIZONS_S",
    "nearest_mid_at_or_after",
    "simulate_quote",
]

#: Design parameters (spec: "so etikettiert", never a threshold).
REPORT_HORIZONS_S: tuple[float, ...] = (10.0, 60.0)
DEFAULT_HORIZON_S = max(REPORT_HORIZONS_S)
DEFAULT_ADV_SEL_HORIZON_S = 60.0


class QueueModelError(RuntimeError):
    """Loud failure: malformed ``simulate_quote`` input."""


def _matching_trade_side(side: str) -> str:
    """The aggressor side that consumes a resting order on ``side``."""
    if side == "buy":
        return "sell"
    if side == "sell":
        return "buy"
    raise QueueModelError(f"side must be 'buy' or 'sell', got {side!r}")


def nearest_mid_at_or_after(mids: Sequence[tuple[int, float]], target_ms: int) -> float | None:
    """First ``mid`` sample at ``ts >= target_ms``; ``None`` if unavailable.

    ``mids`` must be ``ts``-sorted ascending. This is a REPORT lookup (the
    mid AFTER a fill, for adverse selection) -- never used to decide the
    fill itself, so there is no look-ahead-bias risk in its use.
    """
    for ts, mid in mids:
        if ts >= target_ms:
            return float(mid)
    return None


def _outcome(fill_ms: int | None, *, t0_ms: int, side: str, price: float,
            mids: Sequence[tuple[int, float]], adv_sel_horizon_s: float) -> dict[str, Any]:
    if fill_ms is None:
        return {"filled": False, "fill_time_ms": None, "fill_price": None,
                "latency_s": None, "adv_sel_bp": None}
    adv_bp = None
    mid_later = nearest_mid_at_or_after(mids, fill_ms + int(round(adv_sel_horizon_s * 1000)))
    if mid_later is not None and price:
        raw = mid_later - price                    # spec: mid(t_fill+H) - fill_price
        signed = -raw if side == "buy" else raw    # signed AGAINST the quote
        adv_bp = 1e4 * signed / price
    return {"filled": True, "fill_time_ms": fill_ms, "fill_price": price,
            "latency_s": (fill_ms - t0_ms) / 1000.0, "adv_sel_bp": adv_bp}


def simulate_quote(
    book_levels: Sequence[tuple[int, float, float]],
    trades: Sequence[tuple[int, str, float, float]],
    mids: Sequence[tuple[int, float]],
    *,
    t0_ms: int,
    side: str,
    price: float,
    size: float,
    horizon_s: float = DEFAULT_HORIZON_S,
    adv_sel_horizon_s: float = DEFAULT_ADV_SEL_HORIZON_S,
) -> dict[str, Any]:
    """Simulate one hypothetical passive quote under both bounding conventions.

    ``book_levels`` -- ``(ts_ms, level_size, touch_price)`` samples for
    OUR side of the book, ts ascending, starting with ``(t0_ms, pos0,
    price)`` (the placement instant: we join the back of the visible
    level, so ``pos0`` IS the level size at ``t0``, and ``touch_price``
    at ``t0`` must equal ``price`` -- a quote is placed AT the touch).
    ``level_size`` at each later sample is the CURRENT visible size at
    ``price`` on ``side``'s book side (independent of whether ``price``
    is still the touch -- ``touch_price`` carries that separately).

    ``trades`` -- ``(ts_ms, aggressor_side, price, size)`` tuples, any
    order/side/price (irrelevant ones are filtered internally). Only
    trades on the side that would hit our resting order
    (``_matching_trade_side``), at exactly ``price``, in
    ``(t0_ms, t0_ms + horizon_s*1000]``, count.

    ``mids`` -- ``(ts_ms, mid)`` samples, ts ascending, extending past
    ``horizon_s + adv_sel_horizon_s`` when a late fill's adverse
    selection is to be resolved.

    Returns ``{"t0_ms", "side", "price", "size", "position0", "horizon_s",
    "touch_moved_away", "fifo": {...}, "prorata": {...}}`` where each
    convention's dict is ``{"filled", "fill_time_ms", "fill_price",
    "latency_s", "adv_sel_bp"}``.

    Algorithm (one deterministic walk over ``book_levels``, sharing one
    sorted trade list between both conventions): at each successive
    sample ``(ts, level, touch)`` the trades that occurred in
    ``(prev_ts, ts]`` are applied to BOTH ``cum_fifo`` and ``cum_prorata``
    (a real trade is real evidence under either convention); the level's
    decrease over that interval NOT explained by those trades
    (``unexplained``) is applied ONLY to ``cum_prorata``. A convention
    fills the instant its cumulative reduction reaches ``pos0 + size``.
    The walk stops (censored, ``touch_moved_away=True``) the first
    sample where ``touch != price`` -- unless a fill already triggered in
    the SAME interval, since real trades that occurred before the touch
    left are honoured regardless of where the touch ends up.
    """
    if size <= 0:
        raise QueueModelError(f"quote size must be > 0, got {size}")
    if not book_levels:
        raise QueueModelError("book_levels must contain at least the t0 sample")
    t0_ts, pos0, t0_touch = book_levels[0]
    if int(t0_ts) != int(t0_ms):
        raise QueueModelError("book_levels[0] must be the (t0_ms, level, touch) sample AT placement")
    if t0_touch != price:
        raise QueueModelError("quote price must equal the touch price at t0 (join AT the touch)")
    pos0 = float(pos0)
    match_side = _matching_trade_side(side)
    target = pos0 + float(size)
    horizon_end_ms = t0_ms + int(round(horizon_s * 1000))

    rel_trades = sorted(
        (int(ts), float(sz)) for ts, tside, tprice, sz in trades
        if tside == match_side and tprice == price and t0_ms < ts <= horizon_end_ms
    )

    cum_fifo = 0.0
    cum_prorata = 0.0
    fifo_fill_ms: int | None = None
    prorata_fill_ms: int | None = None
    ti = 0
    prev_level = pos0
    touch_moved_away = False

    def _consume_trade(tts: int, tsz: float) -> None:
        nonlocal cum_fifo, cum_prorata, fifo_fill_ms, prorata_fill_ms
        cum_fifo += tsz
        cum_prorata += tsz
        if fifo_fill_ms is None and cum_fifo >= target:
            fifo_fill_ms = tts
        if prorata_fill_ms is None and cum_prorata >= target:
            prorata_fill_ms = tts

    for ts, level, touch in book_levels[1:]:
        ts = int(ts)
        if ts > horizon_end_ms:
            break
        interval_trade_vol = 0.0
        while ti < len(rel_trades) and rel_trades[ti][0] <= ts:
            tts, tsz = rel_trades[ti]
            interval_trade_vol += tsz
            _consume_trade(tts, tsz)
            ti += 1
        if fifo_fill_ms is not None and prorata_fill_ms is not None:
            break
        raw_decrease = max(0.0, prev_level - float(level))
        unexplained = max(0.0, raw_decrease - interval_trade_vol)
        if unexplained > 0.0:
            cum_prorata += unexplained
            if prorata_fill_ms is None and cum_prorata >= target:
                prorata_fill_ms = ts
        if fifo_fill_ms is not None and prorata_fill_ms is not None:
            break
        prev_level = float(level)
        if touch != price:
            touch_moved_away = True
            break

    if not touch_moved_away:
        # book_levels ran out before horizon_end (or never touched it) --
        # keep consuming any remaining in-horizon trades causally.
        while ti < len(rel_trades) and (fifo_fill_ms is None or prorata_fill_ms is None):
            tts, tsz = rel_trades[ti]
            _consume_trade(tts, tsz)
            ti += 1

    fifo_out = _outcome(fifo_fill_ms, t0_ms=t0_ms, side=side, price=price,
                        mids=mids, adv_sel_horizon_s=adv_sel_horizon_s)
    prorata_out = _outcome(prorata_fill_ms, t0_ms=t0_ms, side=side, price=price,
                           mids=mids, adv_sel_horizon_s=adv_sel_horizon_s)
    return {
        "t0_ms": t0_ms, "side": side, "price": price, "size": float(size),
        "position0": pos0, "horizon_s": horizon_s,
        "touch_moved_away": touch_moved_away,
        "fifo": fifo_out, "prorata": prorata_out,
    }
