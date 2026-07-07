#!/usr/bin/env python3
"""C-10 pointer mess-gate driver — H-10 cross-stream pointer days + pre-drift.

Reads the read-only harvester Hive tree (default base ``data/harvest``) over
the registry-fixed daily grid 2026-03-27..2026-07-04 (21-day burn-in, windows
W1 = 2026-04-17..2026-05-25 and W2 = 2026-05-26..2026-07-04), builds the
pre-fixed 30-series detection panel (5 symbols x {bybit, binance} x {RV,
funding, dlog-OI}), loads the HELD-OUT Deribit dvol target (BTC + ETH), runs
the two-stage pointer gate with BH-FDR over F-POINTER, and writes
``c10_pointer_results.{json,md}``. Gate-neutral — the gate-auditor
adjudicates. KAPITALFREI.

    python scripts/c10_pointer.py [--base-dir data/harvest] [--out-dir DIR]
                                  [--n-surrogates 1000] [--seed 42]

No write access to the harvester tree. Mirrors the c06_xmr CLI conventions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c10_pointer.driver import (  # noqa: E402
    DEFAULT_BURN_IN_DAYS,
    DEFAULT_DATA_END,
    DEFAULT_DATA_START,
    DEFAULT_WINDOWS,
    render_markdown,
    run,
)
from bybit_edge.research.c10_pointer.loaders import (  # noqa: E402
    DEFAULT_SYMBOLS,
    DataError,
    build_detection_panel,
    daily_grid,
    load_daily_dvol,
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
        description="C-10 cross-stream pointer-day mess-gate (H-10, F-POINTER)."
    )
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated perp symbols. Default 5-perp panel.")
    p.add_argument("--data-start", default=DEFAULT_DATA_START,
                   help="Daily-grid start (registry: 2026-03-27, incl. burn-in).")
    p.add_argument("--data-end", default=DEFAULT_DATA_END,
                   help="Daily-grid end (registry: 2026-07-04).")
    p.add_argument("--burn-in-days", type=int, default=DEFAULT_BURN_IN_DAYS,
                   help="Burn-in days before the usable range (registry: 21).")
    p.add_argument("--w1-start", default=DEFAULT_WINDOWS[0][1])
    p.add_argument("--w1-end", default=DEFAULT_WINDOWS[0][2])
    p.add_argument("--w2-start", default=DEFAULT_WINDOWS[1][1])
    p.add_argument("--w2-end", default=DEFAULT_WINDOWS[1][2])
    p.add_argument("--n-surrogates", type=int, default=1000,
                   help="Stage-1 circular surrogates per series (registry: 1000).")
    p.add_argument("--n-permutations", type=int, default=1000,
                   help="Stage-2 permutation draws (registry: 1000).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    windows = (
        ("W1", args.w1_start, args.w1_end),
        ("W2", args.w2_start, args.w2_end),
    )
    base = Path(args.base_dir)
    days = daily_grid(args.data_start, args.data_end)
    print(f"[c10_pointer] base-dir={base.resolve()} symbols={list(symbols)} "
          f"grid={args.data_start}..{args.data_end} ({len(days)} days) "
          f"windows={[(w[1], w[2]) for w in windows]} burn_in={args.burn_in_days}",
          file=sys.stderr, flush=True)

    try:
        names, panel = build_detection_panel(base, days, symbols=symbols)
    except DataError as exc:
        print(f"[c10_pointer] FATAL: detection panel not loadable: {exc}",
              file=sys.stderr, flush=True)
        return 1
    n_nonempty = sum(1 for j in range(panel.shape[1])
                     if bool((panel[:, j] == panel[:, j]).any()))
    print(f"[c10_pointer] detection panel: {panel.shape[0]} days x "
          f"{panel.shape[1]} series ({n_nonempty} non-empty)",
          file=sys.stderr, flush=True)

    try:
        dvol_btc = load_daily_dvol(base, "BTC", days)
        dvol_eth = load_daily_dvol(base, "ETH", days)
    except DataError as exc:
        print(f"[c10_pointer] FATAL: held-out dvol target not loadable: {exc}",
              file=sys.stderr, flush=True)
        return 1
    print(f"[c10_pointer] dvol hold-out: BTC {int((dvol_btc == dvol_btc).sum())} / "
          f"ETH {int((dvol_eth == dvol_eth).sum())} days with data",
          file=sys.stderr, flush=True)

    source = (f"{base}/raw (bybit+binance publicTrade/rest.fundingRate/"
              f"rest.openInterest; deribit dvol hold-out)")
    try:
        payload = run(
            days, names, panel, dvol_btc, dvol_eth,
            windows=windows, burn_in_days=args.burn_in_days,
            n_surrogates=args.n_surrogates, n_permutations=args.n_permutations,
            seed=args.seed, source=source,
        )
    except ValueError as exc:
        print(f"[c10_pointer] FATAL: {exc}", file=sys.stderr, flush=True)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c10_pointer_results.json"
    md_path = out_dir / "c10_pointer_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c10_pointer] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c10_pointer] wrote {md_path}", file=sys.stderr, flush=True)

    s1 = [c for c in payload["cells"] if c["stage"] == 1]
    print(
        f"[c10_pointer] DONE: hypothesis={payload['hypothesis']} "
        f"n_pointer={[c['n_pointer'] for c in s1]} "
        f"fdr_p_crit={payload['fdr_p_crit']} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"all_four_cells_pass={payload['all_four_cells_pass']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
