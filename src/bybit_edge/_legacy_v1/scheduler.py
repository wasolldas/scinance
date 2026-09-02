# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Deterministic funding-settlement scheduler.

BTCUSDT settles at 00:00, 08:00, 16:00 UTC (configurable per symbol).
Provides seconds_to_next_settlement(), register_callback(), and an
async run() loop that fires callbacks at each settlement boundary.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Callable, Awaitable, Union

from bybit_edge.config import FUNDING_SETTLEMENT_HOURS_UTC

logger = logging.getLogger(__name__)

# Type alias: callbacks can be sync (returning None) or async coroutines.
CallbackType = Union[Callable[[], None], Callable[[], Awaitable[None]]]


class FundingScheduler:
    """Fires registered callbacks at each funding settlement time."""

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        settlement_hours: tuple[int, ...] | None = None,
    ) -> None:
        self.symbol = symbol
        self._settlement_hours: tuple[int, ...] = (
            settlement_hours if settlement_hours is not None
            else FUNDING_SETTLEMENT_HOURS_UTC
        )
        self._callbacks: list[CallbackType] = []

    # ------------------------------------------------------------------
    # Time calculation
    # ------------------------------------------------------------------

    def seconds_to_next_settlement(
        self, now_utc: datetime | None = None,
    ) -> float:
        """Return the number of seconds until the next settlement.

        Always positive and strictly less than the settlement interval
        (i.e., < 8 h for the default 3-slot schedule).

        Parameters
        ----------
        now_utc
            Override the current time (useful for deterministic tests).
            Must be timezone-aware (UTC).
        """
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        hours = sorted(self._settlement_hours)

        # Current fractional hour (hour + minutes/60 + seconds/3600)
        current_frac = (
            now_utc.hour
            + now_utc.minute / 60.0
            + now_utc.second / 3600.0
            + now_utc.microsecond / 3_600_000_000.0
        )

        # Find the next settlement hour that is strictly after the current time
        next_hour: int | None = None
        for h in hours:
            if h > current_frac:
                next_hour = h
                break

        if next_hour is not None:
            # Next settlement is today
            target = now_utc.replace(
                hour=next_hour, minute=0, second=0, microsecond=0
            )
        else:
            # Next settlement is the first slot tomorrow
            tomorrow = now_utc.date() + timedelta(days=1)
            target = datetime(
                tomorrow.year,
                tomorrow.month,
                tomorrow.day,
                hours[0],
                0,
                0,
                tzinfo=timezone.utc,
            )

        delta = (target - now_utc).total_seconds()
        return delta

    # ------------------------------------------------------------------
    # Callback management
    # ------------------------------------------------------------------

    def register_callback(self, fn: CallbackType) -> None:
        """Register a function to be called at each settlement."""
        self._callbacks.append(fn)

    # ------------------------------------------------------------------
    # Async run loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Wait for the next settlement, fire all callbacks, repeat forever.

        Designed to be launched as an ``asyncio.Task`` and cancelled on
        shutdown.
        """
        while True:
            wait_sec = self.seconds_to_next_settlement()
            logger.info(
                "[%s] Next funding settlement in %.1f s", self.symbol, wait_sec,
            )
            await asyncio.sleep(wait_sec)

            logger.info("[%s] Funding settlement — firing %d callbacks",
                        self.symbol, len(self._callbacks))
            for fn in self._callbacks:
                try:
                    result = fn()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    logger.exception("Callback error during settlement")
