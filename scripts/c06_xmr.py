#!/usr/bin/env python3
"""C-06 XMR mess-gate driver — cross-sectional ergodic MR on harvester backfill.

Reads the read-only harvester Hive tree (default base ``data/harvest``) for the
two pre-registered DEC-15 calendar windows (2026-04-15 + 2026-05-15, 2 calendar
days each), builds the contemporaneously-synchronised 5-symbol 5-min last-price
bar panel, runs the H-07 amplification gate over horizons {1,3,6} bars, applies
BH-FDR over F-XMR, and writes ``c06_xmr_results.{json,md}``. Gate-neutral — the
gate-auditor adjudicates against H-07. KAPITALFREI.

    python scripts/c06_xmr.py [--base-dir data/harvest] [--out-dir DIR]

No write access to the harvester tree. Mirrors the H-05b CLI conventions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c06_xmr.driver import run, render_markdown  # noqa: E402
from bybit_edge.research.c06_xmr.panel import (  # noqa: E402
    DEFAULT_SYMBOLS,
    DataError,
    load_panel_window,
)

# DEC-15 pre-registered calendar windows (deterministic, mid-month, clean backfill).
DEFAULT_WIN_A = "2026-04-15"
DEFAULT_WIN_B = "2026-05-15"


def _nan_safe(o):
    """json default: NaN/inf are written as null (gate-neutral, no bps)."""
    return None


def _dumps(payload) -> str:
    import math

    def clean(v):
        if isinstance(v, float) and not math.isfinite(v):
            return None
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, list):
            return [clean(x) for x in v]
        return v

    return json.dumps(clean(payload), indent=2)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="H-07 C-06 cross-sectional MR mess-gate.")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated symbols. Default 5-perp panel.")
    p.add_argument("--window-a-start", default=DEFAULT_WIN_A, help="DEC-15 window A start date.")
    p.add_argument("--window-b-start", default=DEFAULT_WIN_B, help="DEC-15 window B start date.")
    p.add_argument("--calendar-days", type=int, default=2, help="Calendar days per window.")
    p.add_argument("--bar-min", type=int, default=5, help="Bar length in minutes.")
    p.add_argument("--lookback-bars", type=int, default=12, help="Time-mean lookback L (bars).")
    p.add_argument("--z-thresh", type=float, default=2.5, help="Over-stretch |z| threshold.")
    p.add_argument("--crash-decile", type=float, default=0.9, help="Axis B top-decile cutoff.")
    p.add_argument("--horizons", default="1,3,6", help="Comma-separated forward horizons (bars).")
    p.add_argument("--n-surrogates", type=int, default=200)
    p.add_argument("--n-bootstrap", type=int, default=1000)
    p.add_argument("--n-floor", type=int, default=30)
    p.add_argument("--max-ticks", type=int, default=5_000_000,
                   help="Tick cap per symbol per window (large: whole calendar window).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    horizons = tuple(int(x) for x in args.horizons.split(",") if x.strip())
    win_starts = (args.window_a_start, args.window_b_start)
    win_labels = (f"A@{args.window_a_start}", f"B@{args.window_b_start}")

    base = Path(args.base_dir)
    print(f"[c06_xmr] base-dir={base.resolve()} symbols={list(symbols)} "
          f"windows={list(win_starts)} bar_min={args.bar_min} "
          f"calendar_days={args.calendar_days}", file=sys.stderr, flush=True)

    panels = []
    for start, label in zip(win_starts, win_labels):
        try:
            panel = load_panel_window(
                base, symbols, start,
                calendar_days=args.calendar_days, bar_min=args.bar_min,
                max_ticks=args.max_ticks, window_label=label,
            )
        except DataError as exc:
            print(f"[c06_xmr] SKIP window {label}: {exc}", file=sys.stderr, flush=True)
            continue
        print(f"[c06_xmr] window {label}: {panel.n_bars} synchronised bars "
              f"x {panel.n_symbols} symbols", file=sys.stderr, flush=True)
        panels.append(panel)

    if len(panels) < 2:
        print("[c06_xmr] FATAL: fewer than 2 windows loaded — check junction/coverage.",
              file=sys.stderr, flush=True)
        return 1

    source = f"{base}/raw/bybit/publicTrade (windows {win_starts[0]} + {win_starts[1]})"
    payload = run(
        panels, window_labels=win_labels,
        lookback_bars=args.lookback_bars, z_thresh=args.z_thresh,
        crash_decile=args.crash_decile, horizons=horizons,
        n_surrogates=args.n_surrogates, n_bootstrap=args.n_bootstrap,
        n_floor=args.n_floor, seed=args.seed, source=source,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c06_xmr_results.json"
    md_path = out_dir / "c06_xmr_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[c06_xmr] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c06_xmr] wrote {md_path}", file=sys.stderr, flush=True)
    print(
        f"[c06_xmr] DONE: windows={len(panels)} fdr_p_crit={payload['fdr_p_crit']} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"any_amplified_consistent={payload['any_amplified_consistent']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
