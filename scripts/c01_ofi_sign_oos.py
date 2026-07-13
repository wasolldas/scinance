#!/usr/bin/env python3
"""H-05b OOS confirmation driver — inverse OFI-sign on harvester backfill.

Reads the read-only harvester Hive tree (default base ``data/harvest``) for the
two pre-registered OOS windows (DEC-15: 2026-04-15 + 2026-05-15, first 300k
ticks per symbol each), runs the inverse OFI-sign gate over all 5 symbols x
delta {1,5,15,60,300}s, applies BH-FDR over F-OFI-INV, and writes
``h05b_oos_results.{json,md}``. Gate-neutral — the gate-auditor adjudicates
against H-05b. KAPITALFREI.

    python scripts/c01_ofi_sign_oos.py [--base-dir data/harvest] [--out-dir DIR]

No write access to the harvester tree. Mirrors the H-05 CLI conventions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c01_ofi_sign.oos import (  # noqa: E402
    DataError,
    WINDOW_MAX_TICKS,
    load_harvest_window,
    render_markdown_oos,
    run_oos,
)

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")
# DEC-15 pre-registered OOS windows (deterministic, mid-month, clean backfill).
DEFAULT_WIN_A = "2026-04-15"
DEFAULT_WIN_B = "2026-05-15"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="H-05b OOS inverse OFI-sign confirmation.")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated symbols. Default 5-perp universe.")
    p.add_argument("--window-a-start", default=DEFAULT_WIN_A, help="DEC-15 window A start date.")
    p.add_argument("--window-b-start", default=DEFAULT_WIN_B, help="DEC-15 window B start date.")
    p.add_argument("--spill-days", type=int, default=1,
                   help="Extra day(s) read past each window start to guarantee >= max-ticks.")
    p.add_argument("--max-ticks", type=int, default=WINDOW_MAX_TICKS, help="Ticks per window.")
    p.add_argument("--grid-ms", type=float, default=None, help="OFI bin grid ms (default module).")
    p.add_argument("--lags", default=None, help="Comma-separated delta seconds (default 1,5,15,60,300).")
    p.add_argument("--n-surrogates", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    win_starts = (args.window_a_start, args.window_b_start)
    win_labels = (f"A@{args.window_a_start}", f"B@{args.window_b_start}")

    kwargs: dict = {"n_surrogates": args.n_surrogates, "seed": args.seed,
                    "max_ticks_per_window": args.max_ticks}
    if args.grid_ms is not None:
        kwargs["grid_ms"] = args.grid_ms
    if args.lags is not None:
        kwargs["lags_s"] = tuple(int(x) for x in args.lags.split(",") if x.strip())

    base = Path(args.base_dir)
    print(f"[h05b] base-dir={base.resolve()} symbols={list(symbols)} "
          f"windows={list(win_starts)} max_ticks={args.max_ticks}", file=sys.stderr, flush=True)

    symbol_windows: dict[str, list] = {}
    missing_symbols: list[str] = []
    for sym in symbols:
        wins = []
        ok = True
        for start in win_starts:
            try:
                wins.append(load_harvest_window(
                    base, sym, start, max_ticks=args.max_ticks, spill_days=args.spill_days,
                ))
            except DataError as exc:
                print(f"[h05b] SKIP {sym} window @{start}: {exc}", file=sys.stderr, flush=True)
                ok = False
                break
        if ok and len(wins) >= 2:
            symbol_windows[sym] = wins
        else:
            # Bug fix (silent-fdr-family-shrinkage, CRITICAL_REVIEW_2_2026-07-13.md):
            # a symbol that fails to load both windows must NOT just vanish from
            # the run — it is padded into F-OFI-INV as a p=1.0 sentinel so BH-FDR
            # never runs on a silently shrunken registered 5-symbol family (mirrors
            # c09_bunch.py / c13_tailshape.py's established sentinel-padding CLI
            # convention).
            print(f"[h05b] symbol {sym} dropped (could not load both windows) "
                  f"— padded into F-OFI-INV as a p=1.0 sentinel (family size stays "
                  f"fixed at the registered 5-symbol universe)",
                  file=sys.stderr, flush=True)
            missing_symbols.append(sym)

    if not symbol_windows:
        print("[h05b] FATAL: no symbol loaded both OOS windows — check junction/coverage.",
              file=sys.stderr, flush=True)
        return 1

    source = f"{base}/raw/bybit/publicTrade (windows {win_starts[0]} + {win_starts[1]})"
    payload = run_oos(
        symbol_windows, window_labels=win_labels, source=source,
        missing_symbols=tuple(missing_symbols), **kwargs,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "h05b_oos_results.json"
    md_path = out_dir / "h05b_oos_results.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_oos(payload), encoding="utf-8")

    print(f"[h05b] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[h05b] wrote {md_path}", file=sys.stderr, flush=True)
    print(
        f"[h05b] DONE: symbols={len(symbol_windows)} missing_symbols={missing_symbols} "
        f"family_size_deviation={payload['family_size_deviation']} "
        f"fdr_p_crit={payload['fdr_p_crit']:.4f} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"inverse_consistent_cells={payload['n_inverse_consistent_cells']} "
        f"any_inverse_consistent={payload['any_inverse_consistent']}",
        file=sys.stderr, flush=True,
    )
    # Ein fehlendes Symbol darf NIE lautlos verschwinden: statt die Familie
    # zu schrumpfen, füllen wir sie mit p=1.0-Sentinels auf (siehe run_oos())
    # und setzen ``family_size_deviation`` im Payload — der gate-auditor
    # bzw. Automatisierung liest dieses Flag, nicht den Exit-Code (mirrors
    # c09_bunch.py / c13_tailshape.py: rc=0 bleibt auch bei Sentinels, die
    # Partial-Run-Info lebt explizit im Payload statt implizit im rc).
    if payload["family_size_deviation"]:
        print(
            f"[h05b] WARNING: family_size_deviation=True — partial run "
            f"({len(missing_symbols)} symbol(s) missing: {missing_symbols}). "
            f"rc=0 nonetheless (see payload['family_size_deviation'] / "
            f"payload['missing_symbols'] for automation gating).",
            file=sys.stderr, flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
