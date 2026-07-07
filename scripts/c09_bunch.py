#!/usr/bin/env python3
"""H-09 Risk-Limit-Tier-Bunching driver — excess-mass at the tier-1 kink.

Reads the read-only harvester Hive tree (default base ``data/harvest``) for
the two pre-registered calendar windows (registry H-09: W1 =
2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04), aggregates publicTrade
records into taker orders (same symbol/side/ts_exchange_ms merged), runs the
registered Chetty-excess-mass estimator (90 bins, degree-7 counterfactual,
residual bootstrap 500 reps, placebos 0.50/0.75*K_s) per symbol x window,
applies BH-FDR alpha=0.10 over F-BUNCH, and writes
``c09_bunch_results.{json,md}``. Gate-neutral — the gate-auditor adjudicates
against H-09. KAPITALFREI.

    python scripts/c09_bunch.py [--base-dir data/harvest] [--out-dir DIR]

WARNUNG: K_s fuer ETH/SOL/BNB/XRP sind PLATZHALTER — vor echtem Lauf gegen die
aktuelle Bybit-Risk-Limit-Tabelle verifizieren (append-only Nachtrag,
DEC-09-Muster). No write access to the harvester tree.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c09_bunch.driver import (  # noqa: E402
    DEFAULT_WINDOW_A,
    DEFAULT_WINDOW_B,
    WINDOW_MAX_TICKS,
    DataError,
    load_harvest_window,
    run,
    write_outputs,
)
from bybit_edge.research.c09_bunch.kinks import (  # noqa: E402
    KINK_PLACEHOLDER_NOTE,
    N_BOOTSTRAP,
)

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")


def _span_days(start: str, end: str) -> int:
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    if d1 < d0:
        raise SystemExit(f"window end {end} before start {start}")
    return (d1 - d0).days


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="H-09 risk-limit tier-bunching mess-gate (F-BUNCH).")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated symbols. Default 5-perp universe.")
    p.add_argument("--window-a-start", default=DEFAULT_WINDOW_A[0],
                   help="W1 start date (registry: 2026-03-27).")
    p.add_argument("--window-a-end", default=DEFAULT_WINDOW_A[1],
                   help="W1 end date, inclusive (registry: 2026-05-15).")
    p.add_argument("--window-b-start", default=DEFAULT_WINDOW_B[0],
                   help="W2 start date (registry: 2026-05-16).")
    p.add_argument("--window-b-end", default=DEFAULT_WINDOW_B[1],
                   help="W2 end date, inclusive (registry: 2026-07-04).")
    p.add_argument("--max-ticks", type=int, default=WINDOW_MAX_TICKS,
                   help="Per-window raw-record cap (operational memory bound).")
    p.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP,
                   help="Residual-bootstrap reps (registered: 500).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    windows = (
        (args.window_a_start, args.window_a_end),
        (args.window_b_start, args.window_b_end),
    )
    window_labels = tuple(f"W{i + 1}@{w[0]}..{w[1]}" for i, w in enumerate(windows))

    base = Path(args.base_dir)
    print(f"[h09] base-dir={base.resolve()} symbols={list(symbols)} "
          f"windows={list(window_labels)} max_ticks={args.max_ticks} "
          f"bootstrap={args.n_bootstrap} seed={args.seed}",
          file=sys.stderr, flush=True)
    print(f"[h09] {KINK_PLACEHOLDER_NOTE}", file=sys.stderr, flush=True)

    symbol_windows: dict[str, list] = {}
    for sym in symbols:
        wins = []
        ok = True
        for start, end in windows:
            try:
                wins.append(load_harvest_window(
                    base, sym, start,
                    max_ticks=args.max_ticks,
                    spill_days=_span_days(start, end),
                ))
            except DataError as exc:
                print(f"[h09] SKIP {sym} window @{start}..{end}: {exc}",
                      file=sys.stderr, flush=True)
                ok = False
                break
        if ok and len(wins) >= 2:
            symbol_windows[sym] = wins
        else:
            print(f"[h09] symbol {sym} dropped (could not load both windows)",
                  file=sys.stderr, flush=True)

    if not symbol_windows:
        print("[h09] FATAL: no symbol loaded both windows — check junction/coverage.",
              file=sys.stderr, flush=True)
        return 1

    source = (
        f"{base}/raw/bybit/publicTrade "
        f"(W1 {windows[0][0]}..{windows[0][1]} + W2 {windows[1][0]}..{windows[1][1]})"
    )
    payload = run(
        symbol_windows,
        window_labels=window_labels,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        source=source,
    )

    json_path, md_path = write_outputs(payload, Path(args.out_dir))
    print(f"[h09] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[h09] wrote {md_path}", file=sys.stderr, flush=True)
    print(
        f"[h09] DONE: symbols={len(symbol_windows)} fdr_p_crit={payload['fdr_p_crit']:.4f} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"any_symbol_passed_both={payload['any_symbol_passed_both_windows']} "
        f"weiter_indication={payload['weiter_indication']} "
        f"gate_valid_assumptions={payload['gate_valid_assumptions']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
