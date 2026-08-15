#!/usr/bin/env python3
"""WP-0 bar-cache builder CLI — one tick pass, immutable 1-min bars (DEC-34/35).

Builds the shared deterministic 1-minute bar cache for Wave 6 from the
read-only harvester tree. Incremental and resumable: already-cached days are
skipped, only harvest-manifest-DONE days are frozen, and every day partition
carries a value-hash sidecar. At the end the range fingerprint per symbol is
printed — the hash every Wave-6 registration must quote.

    python scripts/build_bar_cache.py [--base-dir data/harvest]
        [--cache-dir data/barcache] [--symbols BTCUSDT,ETHUSDT,...]
        [--start 2020-03-25] [--end 2026-07-31]

Exit codes: 0 = OK · 1 = error (incl. any loud-fail day).
No write access to the harvester tree; the cache is a NEW path.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.bar_cache import (  # noqa: E402
    BarCacheError,
    build_range,
    bars_fingerprint,
)

#: Full bybit perp universe of the data inventory (DATA_INVENTORY_2026-08-10).
DEFAULT_SYMBOLS = "BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,BNBUSDT"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="WP-0 deterministic 1-min bar cache (KAPITALFREI infra).")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only). Default data/harvest.")
    p.add_argument("--cache-dir", default="data/barcache",
                   help="Cache root (NEW path, never inside the harvester tree).")
    p.add_argument("--exchange", default="bybit")
    p.add_argument("--stream", default="publicTrade")
    p.add_argument("--symbols", default=DEFAULT_SYMBOLS,
                   help=f"Comma-separated. Default {DEFAULT_SYMBOLS}.")
    p.add_argument("--start", default="2020-03-25",
                   help="Range start (inventory: earliest BTC day 2020-03-25).")
    p.add_argument("--end", default="2026-07-31",
                   help="Range end. Default 2026-07-31 (before the moving edge).")
    p.add_argument("--rebuild", action="store_true",
                   help="Force rebuild of already-cached days (rarely needed).")
    p.add_argument("--progress-every", type=int, default=50,
                   help="Print a heartbeat every N processed days.")
    p.add_argument("--memory-limit",
                   default=os.environ.get("BARCACHE_MEMORY_LIMIT", "4GB"),
                   help="DuckDB memory cap per connection (spills to disk "
                        "above it). Default 4GB / env BARCACHE_MEMORY_LIMIT. "
                        "The 2026-08-14 run OOM-crashed without a cap (DEC-36).")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    base, cache = Path(args.base_dir), Path(args.cache_dir)
    harvester_root = (base / "raw").resolve()
    if cache.resolve().is_relative_to(harvester_root):
        print("[barcache] FATAL: cache dir lies inside the harvester tree "
              "(Schutzgut) — choose a new path.", file=sys.stderr)
        return 1

    print(f"[barcache] base={base.resolve()} cache={cache.resolve()} "
          f"{args.exchange}/{args.stream} symbols={list(symbols)} "
          f"range={args.start}..{args.end} memory_limit={args.memory_limit}",
          file=sys.stderr, flush=True)

    ok = True
    summaries = []
    for sym in symbols:
        t0 = time.time()
        state = {"n": 0}

        def _progress(symbol: str, res: dict) -> None:
            state["n"] += 1
            if state["n"] % args.progress_every == 0:
                print(f"[barcache] {symbol}: {state['n']} days processed "
                      f"(last {res['day']} -> {res['status']})",
                      file=sys.stderr, flush=True)

        try:
            summary = build_range(
                base, cache, args.exchange, args.stream, sym,
                args.start, args.end, rebuild=args.rebuild, progress=_progress,
                memory_limit=args.memory_limit)
        except BarCacheError as exc:
            print(f"[barcache] FATAL {sym}: {exc}", file=sys.stderr, flush=True)
            ok = False
            continue
        summary["seconds"] = round(time.time() - t0, 1)
        fp = bars_fingerprint(cache, args.exchange, sym, args.start, args.end)
        summary["fingerprint"] = fp
        summaries.append(summary)
        print(f"[barcache] {sym}: cached={summary['cached']} "
              f"exists={summary['exists']} no_raw={summary['no_raw']} "
              f"not_done={summary['days_not_done']} in {summary['seconds']}s "
              f"| fp {fp['sha256_values'][:16]}... ({fp['n_days_present']} days, "
              f"{fp['n_minutes']} minutes)", file=sys.stderr, flush=True)

    print(json.dumps({"summaries": summaries}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
