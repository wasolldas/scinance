#!/usr/bin/env python3
"""WP-2 L2 tilt one-pass extraction CLI (H-22 pre-work, KAPITALFREI).

Replays the bybit orderbook snapshot+delta stream over the REGISTERED H-22
windows and writes hash-pinned per-day minute tilt series. One sequential
deterministic pass per symbol x window (state carries across days inside a
window; a re-run reproduces the output bit-identically). Prints the window
fingerprints the H-22 run report must quote, plus the coverage against the
registered 85% floor (informational here — the H-22 driver enforces it).

    python scripts/wp2_l2_extract.py [--base-dir data/harvest]
        [--out-dir data/l2tilt]

Exit codes: 0 = OK · 1 = error.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c22_l2tilt.extract import (  # noqa: E402
    L2ExtractError,
    extract_window,
    load_daily_tilt,
    tilt_fingerprint,
)

#: Registered H-22 windows (registry 2026-08-15): BTC judgment-bearing,
#: ETH report-only.
WINDOWS = (
    ("BTCUSDT", "W-L2-1", "2023-07-01", "2024-06-30", True),
    ("BTCUSDT", "W-L2-2", "2024-07-01", "2025-06-30", True),
    ("ETHUSDT", "W-ETH", "2023-04-01", "2024-04-30", False),
)

COVERAGE_FLOOR = 0.85


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="WP-2 L2 tilt extraction (one pass, KAPITALFREI).")
    p.add_argument("--base-dir", default="data/harvest")
    p.add_argument("--out-dir", default="data/l2tilt",
                   help="Tilt store root (NEW path). Default data/l2tilt.")
    args = p.parse_args(argv)

    base, out = Path(args.base_dir), Path(args.out_dir)
    harvester_root = (base / "raw").resolve()
    if out.resolve().is_relative_to(harvester_root):
        print("[wp2] FATAL: out dir lies inside the harvester tree.",
              file=sys.stderr)
        return 1

    ok = True
    results = []
    for symbol, label, start, end, judgment in WINDOWS:
        t0 = time.time()
        state = {"n": 0}

        def _progress(sym: str, res: dict) -> None:
            state["n"] += 1
            if state["n"] % 30 == 0:
                print(f"[wp2] {sym} {label}: {state['n']} days "
                      f"(last {res['day']} -> {res['status']})",
                      file=sys.stderr, flush=True)

        try:
            summary = extract_window(base, out, symbol, start, end,
                                     progress=_progress)
        except L2ExtractError as exc:
            print(f"[wp2] FATAL {symbol} {label}: {exc}", file=sys.stderr,
                  flush=True)
            ok = False
            continue
        fp = tilt_fingerprint(out, "bybit", symbol, start, end)
        daily = load_daily_tilt(out, "bybit", symbol, start, end)
        coverage = fp["n_ok_days"] / summary["days_in_range"]
        results.append({
            "symbol": symbol, "window": label, "range": [start, end],
            "judgment_bearing": judgment, **summary,
            "coverage_days": round(coverage, 4),
            "coverage_floor": COVERAGE_FLOOR,
            "floor_met": bool(coverage >= COVERAGE_FLOOR),
            "n_daily_medians": int(daily["day_idx"].size),
            "fingerprint": fp,
            "seconds": round(time.time() - t0, 1),
        })
        print(f"[wp2] {symbol} {label}: ok={summary['ok']} "
              f"discarded={summary['discarded']} no_raw={summary['no_raw']} "
              f"breaks={summary['total_seq_breaks']} "
              f"coverage={coverage:.1%} (floor {COVERAGE_FLOOR:.0%}: "
              f"{'MET' if coverage >= COVERAGE_FLOOR else 'MISSED'}) "
              f"| fp {fp['sha256_values'][:16]}... in {results[-1]['seconds']}s",
              file=sys.stderr, flush=True)

    print(json.dumps({"windows": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
