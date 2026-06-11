"""
CLI entry point for the F0 Recording-Engine (C-36).

    python -m bybit_edge.recorder [--streams ...] [--cap-gb N] [--duration S]

Flags
-----
--streams      Comma-separated subset of streams to record. Default: all
               (rpi_orderbook, insurance_pool, adl_alerts, premium_index_kline,
               option_tickers).
--cap-gb       Hard ring-buffer storage ceiling in GB. Default: DEFAULT_CAP_GB
               (see storage.py — PRD §3 requires a fixed cap, value documented).
--duration     Stop after this many seconds (for T2 smoke tests). Default:
               unbounded (continuous recording, the only always-on component).
--symbols      Comma-separated linear symbols for rpi_orderbook / premium index.
--options      Comma-separated option underlyings for option_tickers (BTC,ETH).
--sunset-start ISO date the recording started; if given, a Sunset-Review report
               is written before recording starts (no-op unless --duration ends
               or used standalone).

The engine wires a real aiohttp-based REST poller for the premium-index kline
and the production ``websockets.connect`` transport. In the netless sandbox
this will simply fail to connect and retry with backoff — the real run is T2.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from bybit_edge.config import (
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    LOG_LEVEL,
    rest_base_url,
)
from bybit_edge.recorder.recording_engine import RecordingEngine, _default_ws_connect
from bybit_edge.recorder.storage import DEFAULT_CAP_GB, STREAM_SCHEMAS
from bybit_edge.recorder.sunset import SunsetReviewer

logger = logging.getLogger("bybit_edge.recorder")


async def _aiohttp_rest_poll(path: str, params: dict) -> dict:
    """Production REST poller for the premium-index kline (public endpoint)."""
    import aiohttp

    url = f"{rest_base_url()}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, params=params, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"REST {path} HTTP {resp.status}")
            return await resp.json()


def _parse_csv(raw: Optional[str]) -> Optional[list[str]]:
    if not raw:
        return None
    out = [tok.strip() for tok in raw.split(",") if tok.strip()]
    return out or None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m bybit_edge.recorder",
        description="F0 Recording-Engine (C-36) — capped recorder for the new streams.",
    )
    p.add_argument(
        "--streams",
        default=None,
        help=f"Comma-separated subset. Default = all: {','.join(STREAM_SCHEMAS)}",
    )
    p.add_argument(
        "--cap-gb",
        type=float,
        default=DEFAULT_CAP_GB,
        help=f"Hard storage ceiling in GB (ring buffer). Default {DEFAULT_CAP_GB}.",
    )
    p.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Stop after N seconds (smoke test). Default: unbounded.",
    )
    p.add_argument(
        "--symbols",
        default="BTCUSDT",
        help="Comma-separated linear symbols. Default BTCUSDT.",
    )
    p.add_argument(
        "--options",
        default="BTC,ETH",
        help="Comma-separated option underlyings. Default BTC,ETH.",
    )
    p.add_argument(
        "--sunset-start",
        default=None,
        help="ISO date of recording start; if set, write a Sunset-Review report first.",
    )
    return p


async def _run(args: argparse.Namespace) -> int:
    streams = _parse_csv(args.streams)
    symbols = _parse_csv(args.symbols) or ["BTCUSDT"]
    options = _parse_csv(args.options) or ["BTC", "ETH"]

    if args.sunset_start:
        try:
            start = datetime.fromisoformat(args.sunset_start)
            reviewer = SunsetReviewer(start)
            path = reviewer.write_report()
            logger.info("Sunset-Review written: %s", path)
        except ValueError:
            logger.error("Invalid --sunset-start date: %s", args.sunset_start)

    engine = RecordingEngine(
        linear_symbols=symbols,
        option_underlyings=options,
        enabled_streams=streams,
        cap_gb=args.cap_gb,
        ws_connect=_default_ws_connect,
        rest_poll=_aiohttp_rest_poll,
    )
    logger.info(
        "Starting RecordingEngine: streams=%s symbols=%s options=%s cap=%.1f GB duration=%s",
        [s.stream for s in engine.specs], symbols, options, args.cap_gb, args.duration,
    )
    await engine.run(duration=args.duration)
    logger.info("RecordingEngine finished. Telemetry: %s", json.dumps(engine.cap.usage_report()))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down.")
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
