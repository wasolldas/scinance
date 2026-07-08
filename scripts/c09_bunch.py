#!/usr/bin/env python3
"""H-09 Risk-Limit-Tier-Bunching driver — excess-mass at the tier-1 kink.

Reads the read-only harvester Hive tree (default base ``data/harvest``) for
the two pre-registered calendar windows (registry H-09: W1 =
2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04). Order aggregation
(consecutive publicTrade records with identical symbol/side/ts_exchange_ms
merged, notional = sum(price*size)) runs INSIDE DuckDB (``GROUP BY
ts_exchange_ms, side``) via ``driver.load_window_orders`` — raw ticks never
reach Python and there is NO per-window tick cap, so silent window truncation
(audit_h09.md Bug 1) is structurally impossible, and RAM stays bounded to the
small per-window notional array (Bug 2). Runs the registered Chetty-
excess-mass estimator (90 bins, degree-7 counterfactual, residual bootstrap
500 reps, placebos 0.50/0.75*K_s) per symbol x window, applies BH-FDR
alpha=0.10 over the FULL 10-cell F-BUNCH family — padding any symbol that
fails to load with p=1.0 sentinel cells so the family never silently shrinks
(Bug 3) — and writes ``c09_bunch_results.{json,md}``. Gate-neutral — the
gate-auditor adjudicates against H-09. KAPITALFREI.

    python scripts/c09_bunch.py [--base-dir data/harvest] [--out-dir DIR]

WARNUNG: K_s fuer ETH/SOL/BNB/XRP sind PLATZHALTER — vor echtem Lauf gegen die
aktuelle Bybit-Risk-Limit-Tabelle verifizieren (append-only Nachtrag,
DEC-09-Muster). No write access to the harvester tree.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c09_bunch.driver import (  # noqa: E402
    DEFAULT_WINDOW_A,
    DEFAULT_WINDOW_B,
    DataError,
    load_window_orders,
    run,
    write_outputs,
)
from bybit_edge.research.c09_bunch.kinks import (  # noqa: E402
    KINK_PLACEHOLDER_NOTE,
    N_BOOTSTRAP,
    RISK_LIMIT_TIER1_KINK_USDT,
)

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")


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
          f"windows={list(window_labels)} bootstrap={args.n_bootstrap} "
          f"seed={args.seed} (DuckDB-side aggregation, no tick cap)",
          file=sys.stderr, flush=True)
    print(f"[h09] {KINK_PLACEHOLDER_NOTE}", file=sys.stderr, flush=True)

    symbol_windows: dict[str, list] = {}
    missing_symbols: list[str] = []
    for sym in symbols:
        kink = RISK_LIMIT_TIER1_KINK_USDT.get(sym)
        if kink is None:
            print(f"[h09] SKIP {sym}: no K_s kink registered for this symbol",
                  file=sys.stderr, flush=True)
            missing_symbols.append(sym)
            continue
        wins = []
        ok = True
        for start, end in windows:
            try:
                wins.append(load_window_orders(base, sym, start, end, kink=kink))
            except DataError as exc:
                print(f"[h09] SKIP {sym} window @{start}..{end}: {exc}",
                      file=sys.stderr, flush=True)
                ok = False
                break
        if ok and len(wins) >= 2:
            symbol_windows[sym] = wins
        else:
            print(f"[h09] symbol {sym} dropped (could not load both windows) "
                  f"— padded into F-BUNCH as a p=1.0 sentinel (family size stays "
                  f"fixed, audit_h09.md Bug 3)",
                  file=sys.stderr, flush=True)
            missing_symbols.append(sym)

    if not symbol_windows:
        print("[h09] FATAL: no symbol loaded both windows — check junction/coverage.",
              file=sys.stderr, flush=True)
        return 1

    source = (
        f"{base}/raw/bybit/publicTrade "
        f"(W1 {windows[0][0]}..{windows[0][1]} + W2 {windows[1][0]}..{windows[1][1]}, "
        f"DuckDB-side order aggregation, uncapped)"
    )
    payload = run(
        symbol_windows,
        window_labels=window_labels,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        missing_symbols=tuple(missing_symbols),
        source=source,
    )

    json_path, md_path = write_outputs(payload, Path(args.out_dir))
    print(f"[h09] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[h09] wrote {md_path}", file=sys.stderr, flush=True)
    print(
        f"[h09] DONE: symbols_loaded={len(symbol_windows)} "
        f"missing_symbols={missing_symbols} "
        f"family_size_deviation={payload['family_size_deviation']} "
        f"fdr_p_crit={payload['fdr_p_crit']:.4f} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"any_symbol_passed_both={payload['any_symbol_passed_both_windows']} "
        f"weiter_indication={payload['weiter_indication']} "
        f"gate_valid_assumptions={payload['gate_valid_assumptions']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
