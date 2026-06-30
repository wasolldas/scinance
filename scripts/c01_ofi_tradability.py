#!/usr/bin/env python3
"""H-05c OFI-fade tradability driver — inverse SOL edge vs friction + latency.

Reads SOLUSDT publicTrade windows from the read-only harvester backfill
(default base ``data/harvest``) for the two pre-registered OOS windows (DEC-15:
2026-04-15 + 2026-05-15, first 300k ticks each), runs the pre-fixed OFI-fade
rule per delta in {1,5}s, confronts each round-trip's directional capture move
with the 11 bps wall + 4 bps slippage after a 300 ms latency haircut, and writes
``h05c_results.{json,md}``. Gate-neutral — gate-auditor adjudicates against H-05c.

NON-KAPITALFREI but a historical backtest with a cost model — NO live orders.

    python scripts/c01_ofi_tradability.py [--base-dir data/harvest] [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c01_ofi_sign.oos import (  # noqa: E402
    DataError,
    load_harvest_window,
)
from bybit_edge.research.c01_ofi_tradability.driver import (  # noqa: E402
    PASS_SYMBOL,
    render_markdown,
    run,
)
from bybit_edge.research.c01_ofi_tradability.fade_rule import SURVIVOR_DELTAS_S  # noqa: E402

DEFAULT_WIN_A = "2026-04-15"
DEFAULT_WIN_B = "2026-05-15"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="H-05c OFI-fade tradability gate.")
    p.add_argument("--base-dir", default="data/harvest", help="Harvester data root (read-only).")
    p.add_argument("--symbol", default=PASS_SYMBOL, help="Pass-bearing symbol (registry: SOLUSDT).")
    p.add_argument("--window-a-start", default=DEFAULT_WIN_A)
    p.add_argument("--window-b-start", default=DEFAULT_WIN_B)
    p.add_argument("--spill-days", type=int, default=1)
    p.add_argument("--max-ticks", type=int, default=300_000)
    p.add_argument("--deltas", default=",".join(str(d) for d in SURVIVOR_DELTAS_S),
                   help="Comma-separated delta seconds (registry survivors: 1,5).")
    p.add_argument("--friction-bps", type=float, default=11.0)
    p.add_argument("--latency-ms", type=float, default=300.0)
    p.add_argument("--maker-secondary", action="store_true",
                   help="Marked adverse-selection secondary case (NOT judgment-bearing).")
    p.add_argument("--n-bootstrap", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".")
    args = p.parse_args(argv)

    deltas = tuple(int(x) for x in args.deltas.split(",") if x.strip())
    base = Path(args.base_dir)
    win_starts = (args.window_a_start, args.window_b_start)
    print(f"[h05c] base-dir={base.resolve()} symbol={args.symbol} windows={list(win_starts)} "
          f"deltas={list(deltas)} latency={args.latency_ms}ms friction={args.friction_bps}bps "
          f"maker={args.maker_secondary}", file=sys.stderr, flush=True)

    windows = []
    for start in win_starts:
        try:
            windows.append(load_harvest_window(
                base, args.symbol, start, max_ticks=args.max_ticks, spill_days=args.spill_days,
            ))
        except DataError as exc:
            print(f"[h05c] FATAL: window {args.symbol}@{start}: {exc}", file=sys.stderr, flush=True)
            return 1

    source = f"{base}/raw/bybit/publicTrade/{args.symbol} (windows {win_starts[0]} + {win_starts[1]})"
    payload = run(
        windows, symbol=args.symbol, deltas_s=deltas,
        friction_bps=args.friction_bps, latency_ms=args.latency_ms,
        maker=args.maker_secondary, n_bootstrap=args.n_bootstrap, seed=args.seed,
        source=source,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "h05c_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "h05c_results.md").write_text(render_markdown(payload), encoding="utf-8")
    print(f"[h05c] wrote {out_dir/'h05c_results.json'}", file=sys.stderr, flush=True)
    print(
        f"[h05c] DONE: n_windows={payload['n_windows']} fdr_p_crit={payload['fdr_p_crit']:.4f} "
        f"any_tradable={payload['any_tradable_consistent']} "
        f"gate_valid={payload['gate_valid_assumptions']} "
        f"weiter_indication={payload['weiter_indication']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
