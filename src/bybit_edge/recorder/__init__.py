"""
Recording-Engine F0 (C-36) — additive, capped recording of the new
Scinance-2.0 data streams.

This package is *strictly additive* (DEC-06): it runs NEXT TO the existing
``BybitWSCollector`` / ``PersistenceLayer`` and never touches them. It owns

* its own WebSocket client (:mod:`recording_engine`),
* its own Parquet writers and ring-buffer storage cap (:mod:`storage`),
* its own per-stream pyarrow schemas (:mod:`storage` / :data:`STREAM_SCHEMAS`),
* its own Parquet output root ``data/parquet/recording_f0/`` — the existing
  ``data/parquet/`` cold storage stays read-only and untouched,
* its own Sunset-Review logic (:mod:`sunset`).

The new streams (FINAL_PRD §3, Pilot 3):

* ``orderbook.rpi.{symbol}``  — RPI orderbook (100 ms), linear category
* ``insurance.USDT``          — insurance pool (1 s), symbol-less topic
* ``adlAlert``                — auto-deleveraging alerts (1 s), symbol-less
* premium-index kline         — REST poll (no WS topic), 1-min interval
* ``tickers.{symbol}``        — option IV/greeks tickers on the OPTION WS URL
"""
from __future__ import annotations

from bybit_edge.recorder.recording_engine import (
    RecordingEngine,
    RecordedMessage,
    StreamSpec,
)
from bybit_edge.recorder.storage import (
    STREAM_SCHEMAS,
    ParquetStreamWriter,
    StorageCap,
    RECORDING_ROOT,
)
from bybit_edge.recorder.sunset import (
    SUNSET_PERIOD_DAYS,
    SunsetReviewer,
)

__all__ = [
    "RecordingEngine",
    "RecordedMessage",
    "StreamSpec",
    "STREAM_SCHEMAS",
    "ParquetStreamWriter",
    "StorageCap",
    "RECORDING_ROOT",
    "SUNSET_PERIOD_DAYS",
    "SunsetReviewer",
]
