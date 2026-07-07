#!/usr/bin/env python3
"""H-11 AnEn-vol-regime mess-gate driver — DATA-GATED, KAPITALFREI.

Runs the pre-registered H-11 gate (AnEn k=20 vs. HAR-RV, 3-day horizon,
CRPS = |forecast - obs|, F-ANEN BH-FDR alpha=0.10) against the read-only
harvester Hive tree (default base ``data/harvest``). Gate-neutral output —
the gate-auditor adjudicates. Mirrors the c06_xmr/H-05b CLI conventions.

H-11 is GESPERRT (data-gated): the unlock condition (gapless bybit
publicTrade + rest.fundingRate coverage, BTC+ETH, 2024-03-27..2026-03-26,
>= 730 days) is checked programmatically BEFORE any data run. If unmet the
run reports a clean SKIP (exit code 2), never a crash.

    python scripts/c11_anen.py [--base-dir data/harvest] [--out-dir DIR]
    python scripts/c11_anen.py --check-unlock-only      # only the unlock check

Exit codes: 0 = run OK / unlocked · 1 = error · 2 = locked (SKIP).
No write access to the harvester tree.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c11_anen.analog import EMBARGO_DAYS, K_ANALOGS, WEIGHT_GRID  # noqa: E402
from bybit_edge.research.c11_anen.driver import (  # noqa: E402
    DEFAULT_SYMBOLS,
    TUNE_RANGE,
    UNLOCK_MIN_DAYS,
    UNLOCK_RANGE,
    W1_RANGE,
    W2_RANGE,
    check_unlock,
    render_markdown,
    run,
)
from bybit_edge.research.c11_anen.features import DataError  # noqa: E402
from bybit_edge.research.c11_anen.stats import BLOCK_LEN_DAYS, N_BOOTSTRAP  # noqa: E402

RC_OK = 0
RC_FAIL = 1
RC_LOCKED = 2


def _dumps(payload) -> str:
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
        description="H-11 AnEn vol-regime mess-gate (data-gated, KAPITALFREI).")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated symbols. Default BTCUSDT,ETHUSDT (registry H-11).")
    p.add_argument("--check-unlock-only", action="store_true",
                   help="ONLY check the H-11 unlock condition and exit "
                        "(0 = unlocked, 2 = locked). No data run.")
    p.add_argument("--tune-start", default=TUNE_RANGE[0], help="Region L start (LOO tuning).")
    p.add_argument("--tune-end", default=TUNE_RANGE[1], help="Region L end.")
    p.add_argument("--w1-start", default=W1_RANGE[0], help="Window W1 start.")
    p.add_argument("--w1-end", default=W1_RANGE[1], help="Window W1 end.")
    p.add_argument("--w2-start", default=W2_RANGE[0], help="Window W2 start.")
    p.add_argument("--w2-end", default=W2_RANGE[1], help="Window W2 end.")
    p.add_argument("--unlock-start", default=UNLOCK_RANGE[0], help="Unlock coverage start.")
    p.add_argument("--unlock-end", default=UNLOCK_RANGE[1], help="Unlock coverage end.")
    p.add_argument("--min-unlock-days", type=int, default=UNLOCK_MIN_DAYS,
                   help="Minimum gapless coverage days (registry: 730).")
    p.add_argument("--k", type=int, default=K_ANALOGS, help="Analog ensemble size (registry: 20).")
    p.add_argument("--embargo-days", type=int, default=EMBARGO_DAYS,
                   help="Analog candidate embargo in days (registry: 30).")
    p.add_argument("--weight-grid", default=",".join(str(g) for g in WEIGHT_GRID),
                   help="Comma-separated per-feature weight grid "
                        "(registry: 0,0.5,1,1.5,2 — frozen; override only for fixtures).")
    p.add_argument("--block-len", type=int, default=BLOCK_LEN_DAYS,
                   help="Bootstrap block length in days (registry: 5).")
    p.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP,
                   help="Bootstrap replications (registry: 1000).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    weight_grid = tuple(float(x) for x in args.weight_grid.split(",") if x.strip())
    base = Path(args.base_dir)

    if args.check_unlock_only:
        unlock = check_unlock(
            base, symbols=symbols,
            start=args.unlock_start, end=args.unlock_end,
            min_days=args.min_unlock_days,
        )
        print(_dumps(unlock))
        if unlock["unlocked"]:
            print("[c11_anen] UNLOCKED: Entsperr-Bedingung erfuellt — H-11 lauffaehig.",
                  file=sys.stderr, flush=True)
            return RC_OK
        print("[c11_anen] LOCKED: H-11 gesperrt — Manifest-Coverage <"
              f"{args.min_unlock_days} Tage lueckenlos, Entsperr-Bedingung nicht erfuellt.",
              file=sys.stderr, flush=True)
        return RC_LOCKED

    print(f"[c11_anen] base-dir={base.resolve()} symbols={list(symbols)} "
          f"L={args.tune_start}..{args.tune_end} W1={args.w1_start}..{args.w1_end} "
          f"W2={args.w2_start}..{args.w2_end} k={args.k} embargo={args.embargo_days}d",
          file=sys.stderr, flush=True)

    source = f"{base}/raw/bybit/{{publicTrade,rest.fundingRate}}"
    try:
        payload = run(
            base,
            symbols=symbols,
            tune_range=(args.tune_start, args.tune_end),
            w1_range=(args.w1_start, args.w1_end),
            w2_range=(args.w2_start, args.w2_end),
            unlock_range=(args.unlock_start, args.unlock_end),
            unlock_min_days=args.min_unlock_days,
            k=args.k,
            embargo=args.embargo_days,
            weight_grid=weight_grid,
            block_len=args.block_len,
            n_bootstrap=args.n_bootstrap,
            seed=args.seed,
            source=source,
        )
    except DataError as exc:
        print(f"[c11_anen] FATAL DataError: {exc}", file=sys.stderr, flush=True)
        return RC_FAIL

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c11_anen_results.json"
    md_path = out_dir / "c11_anen_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c11_anen] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c11_anen] wrote {md_path}", file=sys.stderr, flush=True)

    if payload["status"] == "SKIP":
        print("[c11_anen] SKIP: H-11 gesperrt — Manifest-Coverage <"
              f"{args.min_unlock_days} Tage lueckenlos, Entsperr-Bedingung nicht erfuellt.",
              file=sys.stderr, flush=True)
        return RC_LOCKED

    print(
        f"[c11_anen] DONE: hypothesis={payload['hypothesis']} "
        f"cells={len(payload['cells'])} fdr_p_crit={payload['fdr_p_crit']} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"any_symbol_both_windows_pass={payload['any_symbol_both_windows_pass']}",
        file=sys.stderr, flush=True,
    )
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
