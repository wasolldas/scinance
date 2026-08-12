#!/usr/bin/env python3
"""H-11c mess-gate driver — AnEn vs. dispersion-matched HAR, KAPITALFREI.

Runs the pre-registered H-11c gate (registry 2026-08-12, follow-up obligation
from GL-022): the AnEn side is reproduced BIT-IDENTICALLY from the GL-022 run
(frozen weights, no re-tuning), the HAR baseline keeps its point forecast but
is dressed with a k-member quantile sample of its own in-fit residuals, and
BOTH sides are scored with the SAME registered ensemble CRPS. F-ANEN-C,
BH-FDR alpha=0.10. Gate-neutral output — the gate-auditor adjudicates.

    python scripts/c11c_dressed.py [--base-dir data/harvest] [--out-dir DIR]

Runs in minutes (no LOO weight grid), CPU only.

Exit codes: 0 = run OK · 1 = error · 2 = locked (SKIP) ·
            3 = AnEn side did NOT reproduce GL-022 (results written, gate invalid).
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

from bybit_edge.research.c11_anen.analog import EMBARGO_DAYS, K_ANALOGS  # noqa: E402
from bybit_edge.research.c11_anen.driver import (  # noqa: E402
    DEFAULT_SYMBOLS,
    TUNE_RANGE,
    UNLOCK_MIN_DAYS,
    UNLOCK_RANGE,
    W1_RANGE,
    W2_RANGE,
)
from bybit_edge.research.c11_anen.driver_c import render_markdown, run  # noqa: E402
from bybit_edge.research.c11_anen.features import DataError  # noqa: E402
from bybit_edge.research.c11_anen.stats import BLOCK_LEN_DAYS, N_BOOTSTRAP  # noqa: E402

RC_OK = 0
RC_FAIL = 1
RC_LOCKED = 2
RC_NO_REPRO = 3


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
        description="H-11c AnEn vs. Dressed-HAR mess-gate (KAPITALFREI).")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated symbols. Default BTCUSDT,ETHUSDT.")
    p.add_argument("--w1-start", default=W1_RANGE[0])
    p.add_argument("--w1-end", default=W1_RANGE[1])
    p.add_argument("--w2-start", default=W2_RANGE[0])
    p.add_argument("--w2-end", default=W2_RANGE[1])
    p.add_argument("--unlock-start", default=UNLOCK_RANGE[0])
    p.add_argument("--unlock-end", default=UNLOCK_RANGE[1])
    p.add_argument("--min-unlock-days", type=int, default=UNLOCK_MIN_DAYS)
    p.add_argument("--k", type=int, default=K_ANALOGS)
    p.add_argument("--embargo-days", type=int, default=EMBARGO_DAYS)
    p.add_argument("--block-len", type=int, default=BLOCK_LEN_DAYS)
    p.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    base = Path(args.base_dir)

    print(f"[c11c] base-dir={base.resolve()} symbols={list(symbols)} "
          f"W1={args.w1_start}..{args.w1_end} W2={args.w2_start}..{args.w2_end} "
          f"k={args.k} embargo={args.embargo_days}d — FROZEN weights, no re-tuning",
          file=sys.stderr, flush=True)

    source = f"{base}/raw/bybit/{{publicTrade,rest.fundingRate}}"
    try:
        payload = run(
            base,
            symbols=symbols,
            tune_range=TUNE_RANGE,
            w1_range=(args.w1_start, args.w1_end),
            w2_range=(args.w2_start, args.w2_end),
            unlock_range=(args.unlock_start, args.unlock_end),
            unlock_min_days=args.min_unlock_days,
            k=args.k,
            embargo=args.embargo_days,
            block_len=args.block_len,
            n_bootstrap=args.n_bootstrap,
            seed=args.seed,
            source=source,
        )
    except DataError as exc:
        print(f"[c11c] FATAL DataError: {exc}", file=sys.stderr, flush=True)
        return RC_FAIL

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c11c_dressed_results.json"
    md_path = out_dir / "c11c_dressed_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c11c] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c11c] wrote {md_path}", file=sys.stderr, flush=True)

    if payload["status"] == "SKIP":
        print("[c11c] SKIP: Entsperr-Bedingung unerfuellt.", file=sys.stderr, flush=True)
        return RC_LOCKED

    print(
        f"[c11c] DONE: hypothesis={payload['hypothesis']} "
        f"cells={len(payload['cells'])} fdr_p_crit={payload['fdr_p_crit']} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"any_symbol_both_windows_pass={payload['any_symbol_both_windows_pass']} "
        f"anen_reproduces_gl022={payload['anen_side_reproduces_gl022']}",
        file=sys.stderr, flush=True,
    )
    if not payload["anen_side_reproduces_gl022"]:
        print("[c11c] LOUD FAIL: die AnEn-Seite reproduziert die GL-022-Summen NICHT — "
              "das Gate ist UNGUELTIG (gate_valid=false). Ergebnisse sind geschrieben, "
              "aber nicht urteilstragend. Ursache klaeren (Datenstand? Gewichte? k?).",
              file=sys.stderr, flush=True)
        return RC_NO_REPRO
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
