#!/usr/bin/env python3
"""C-12-FRAG mess-gate driver — H-12 cross-exchange fragmentation matrix.

Reads the read-only harvester Hive tree (default base ``data/harvest``) for
the two pre-registered calendar windows (registry H-12, identical H-09:
W1 = 2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04), builds the
6-series (2 symbols x 3 exchanges: bybit, binance, deribit) minute
last-price panel per window (``panel.build_window``), runs the two-stage
RMT/MP-IPR mess-gate (``driver.run``: per-day spectrum + one-factor null +
ONE F-FRAG BH-FDR family over both windows), and writes
``c12_frag_results.{json,md}``. Gate-neutral — the gate-auditor adjudicates.
KAPITALFREI.

    python scripts/c12_frag.py [--base-dir data/harvest] [--out-dir DIR]
                                [--symbols BTCUSDT,ETHUSDT] [--n-mc 1000]
                                [--seed 42]

No write access to the harvester tree. Mirrors the c06_xmr/c10_pointer CLI
conventions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c12_frag.driver import (  # noqa: E402
    DEFAULT_WINDOW_A,
    DEFAULT_WINDOW_B,
    render_markdown,
    run,
)
from bybit_edge.research.c12_frag.panel import (  # noqa: E402
    DEFAULT_EXCHANGES,
    DEFAULT_SYMBOLS,
    DataError,
    build_window,
)


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
    p = argparse.ArgumentParser(
        description="C-12-FRAG cross-exchange fragmentation matrix mess-gate "
                    "(H-12, RMT/MP-IPR, F-FRAG)."
    )
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated internal (Bybit-notation) symbols. "
                        "Default 2-symbol BTC/ETH panel.")
    p.add_argument("--exchanges", default=",".join(DEFAULT_EXCHANGES),
                   help="Comma-separated exchanges (registry: bybit,binance,deribit).")
    p.add_argument("--window-a-start", default=DEFAULT_WINDOW_A[0])
    p.add_argument("--window-a-end", default=DEFAULT_WINDOW_A[1])
    p.add_argument("--window-b-start", default=DEFAULT_WINDOW_B[0])
    p.add_argument("--window-b-end", default=DEFAULT_WINDOW_B[1])
    p.add_argument("--n-mc", type=int, default=1000,
                   help="MC replications for both stage-a wishart and "
                        "stage-b one-factor null (registry: 1000).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    exchanges = tuple(e.strip() for e in args.exchanges.split(",") if e.strip())
    win_specs = (
        ("W1", args.window_a_start, args.window_a_end),
        ("W2", args.window_b_start, args.window_b_end),
    )
    base = Path(args.base_dir)
    print(f"[c12_frag] base-dir={base.resolve()} symbols={list(symbols)} "
          f"exchanges={list(exchanges)} "
          f"windows={[(w[1], w[2]) for w in win_specs]} n_mc={args.n_mc}",
          file=sys.stderr, flush=True)

    windows = []
    for label, start, end in win_specs:
        try:
            win = build_window(base, symbols, start, end,
                                exchanges=exchanges, label=label)
        except DataError as exc:
            print(f"[c12_frag] FATAL: window {label} ({start}..{end}) not "
                  f"loadable: {exc}", file=sys.stderr, flush=True)
            return 1
        print(f"[c12_frag] window {win.label}: {win.n_days_total} days total, "
              f"{win.n_days_valid} panel-valid, {len(win.series_labels)} series",
              file=sys.stderr, flush=True)
        windows.append(win)

    source = (f"{base}/raw/{{bybit,binance,deribit}}/publicTrade "
              f"(windows {win_specs[0][1]}..{win_specs[0][2]} + "
              f"{win_specs[1][1]}..{win_specs[1][2]})")
    try:
        payload = run(windows, n_mc=args.n_mc, seed=args.seed, source=source)
    except ValueError as exc:
        print(f"[c12_frag] FATAL: {exc}", file=sys.stderr, flush=True)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c12_frag_results.json"
    md_path = out_dir / "c12_frag_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c12_frag] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c12_frag] wrote {md_path}", file=sys.stderr, flush=True)

    print(
        f"[c12_frag] DONE: hypothesis={payload['hypothesis']} "
        f"validity_status={payload['validity_status']} "
        f"fdr_p_crit={payload['fdr_p_crit']} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"weiter_indication={payload['weiter_indication']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
