#!/usr/bin/env python3
"""WP-4 — quote-spread census on the bybit L2 stream (DEC-40, KAPITALFREI).

The census that decides the maker-spread-capture candidate binarily: it
measures the REALISED top-of-book spread (minute-sampled via the same
snapshot+delta replay as WP-2) and reports it against the repo's canonical
maker-fee constant. If the median half-spread sits below the maker fee per
leg, the candidate is dead without further work; if above, the number the
draft only asserted finally exists.

Windows: the RECENT era first (Rezenz-Klausel — current spreads decide a
current strategy) plus one historical reference window for context.

    python scripts/wp4_spread_census.py [--base-dir data/harvest]
        [--out-dir data/l2tilt]

Exit codes: 0 = census written · 1 = error.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np  # noqa: E402

from bybit_edge.config import FEE_MAKER, FEE_TAKER  # noqa: E402
from bybit_edge.research.c22_l2tilt.extract import (  # noqa: E402
    L2ExtractError,
    extract_spread_window,
    load_daily_spread,
)

#: Recency window first (decides), historical reference second (context).
WINDOWS = (
    ("BTCUSDT", "RECENT", "2026-06-22", "2026-08-15"),
    ("ETHUSDT", "RECENT", "2026-06-19", "2026-08-15"),
    ("BTCUSDT", "HIST-2024H1", "2024-01-01", "2024-03-31"),
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="WP-4 quote-spread census (KAPITALFREI).")
    p.add_argument("--base-dir", default="data/harvest")
    p.add_argument("--out-dir", default="data/l2tilt",
                   help="Store root (spread_1min/ lives beside the frozen "
                        "tilt_1min/; the WP-2 files are never touched).")
    p.add_argument("--report-dir", default=".")
    args = p.parse_args(argv)

    base, out = Path(args.base_dir), Path(args.out_dir)
    maker_bp = FEE_MAKER * 1e4
    taker_bp = FEE_TAKER * 1e4
    results = []
    ok = True
    for symbol, label, start, end in WINDOWS:
        t0 = time.time()
        state = {"n": 0}

        def _progress(sym: str, res: dict) -> None:
            state["n"] += 1
            if state["n"] % 10 == 0:
                print(f"[wp4] {sym} {label}: {state['n']} days "
                      f"(last {res['day']} -> {res['status']})",
                      file=sys.stderr, flush=True)

        try:
            summary = extract_spread_window(base, out, symbol, start, end,
                                            progress=_progress)
        except L2ExtractError as exc:
            print(f"[wp4] FATAL {symbol} {label}: {exc}", file=sys.stderr,
                  flush=True)
            ok = False
            continue
        daily = load_daily_spread(out, "bybit", symbol, start, end)
        med = daily["spread_median_bp"]
        row = {
            "symbol": symbol, "window": label, "range": [start, end],
            **summary,
            "n_ok_days": int(daily["day_idx"].size),
            "spread_bp_median_of_daily_medians":
                (float(np.median(med)) if med.size else None),
            "spread_bp_p10": (float(np.median(daily["spread_p10_bp"]))
                              if med.size else None),
            "spread_bp_p90": (float(np.median(daily["spread_p90_bp"]))
                              if med.size else None),
            "half_spread_bp": (float(np.median(med)) / 2.0
                               if med.size else None),
            "fee_maker_bp_per_leg": maker_bp,
            "fee_taker_bp_per_leg": taker_bp,
            # THE census verdict quantity: does one captured half-spread
            # even cover ONE maker leg at the canonical fee?
            "half_spread_covers_maker_leg":
                (bool(float(np.median(med)) / 2.0 > maker_bp)
                 if med.size else None),
            "seconds": round(time.time() - t0, 1),
        }
        results.append(row)
        hs = row["half_spread_bp"]
        print(f"[wp4] {symbol} {label}: ok_days={row['n_ok_days']} "
              f"median_spread={row['spread_bp_median_of_daily_medians']} bp "
              f"half={None if hs is None else round(hs, 4)} bp vs maker "
              f"{maker_bp:.1f} bp/leg -> covers="
              f"{row['half_spread_covers_maker_leg']}",
              file=sys.stderr, flush=True)

    report = {"windows": results,
              "fee_source": "bybit_edge.config FEE_MAKER/FEE_TAKER "
                            "(kanonische Repo-Konstanten; das reale Konto "
                            "kann abweichen — dann Zahl HIER eintragen und "
                            "neu bewerten, nie still ersetzen)"}
    rd = Path(args.report_dir)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "wp4_spread_census.json").write_text(json.dumps(report, indent=2),
                                               encoding="utf-8")
    print(f"[wp4] wrote {rd / 'wp4_spread_census.json'}", file=sys.stderr,
          flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
