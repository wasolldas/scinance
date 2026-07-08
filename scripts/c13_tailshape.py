#!/usr/bin/env python3
"""C-13 tail-shape consistency mess-gate driver (H-13, F-TAILSHAPE, data-gated).

Reads the read-only harvester Hive tree (default base ``data/harvest``):
Bybit ``publicTrade`` for the trailing 1-min return tails (xi_P) and the
Deribit ``markprice.options`` snapshots for the risk-neutral tail (xi_Q).
Performs the PROGRAMMATIC, deterministic D1/D2 unlock search first (registry
H-13 unlock condition); without a valid pair the run is a clean SKIP.

    python scripts/c13_tailshape.py [--base-dir data/harvest] [--symbols BTC,ETH]
                                    [--check-unlock-only] [--n-bootstrap 500]
                                    [--seed 42] [--out-dir DIR]

Exit codes: 0 = OK (unlock met / full run done), 2 = SKIP (H-13 still locked),
1 = error. ``--check-unlock-only`` performs ONLY the D1/D2 search (no fits)
and writes ``c13_unlock_check.json``. Gate-neutral — the gate-auditor
adjudicates. KAPITALFREI. No write access to the harvester tree.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c13_tailshape.driver import (  # noqa: E402
    HYPOTHESIS_ID,
    check_unlock,
    render_markdown,
    run,
)

RC_OK = 0
RC_ERROR = 1
RC_SKIP_LOCKED = 2


def _dumps(payload) -> str:
    def clean(v):
        if isinstance(v, float) and not math.isfinite(v):
            return None
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        return v

    return json.dumps(clean(payload), indent=2)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="C-13 tail-shape consistency mess-gate (H-13, data-gated)."
    )
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default="BTC,ETH",
                   help="Comma-separated Deribit underlyings. Default BTC,ETH.")
    p.add_argument("--check-unlock-only", action="store_true",
                   help="Only run the deterministic D1/D2 unlock search (no fits).")
    p.add_argument("--n-bootstrap", type=int, default=500,
                   help="Bootstrap repetitions per side (registered default 500).")
    p.add_argument("--trailing-days", type=int, default=60,
                   help="Trailing return window in days (registered default 60).")
    p.add_argument("--snapshot-hour", type=int, default=8,
                   help="Snapshot hour UTC (registered default 08:00).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip().upper() for s in args.symbols.split(",") if s.strip())
    base = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[c13] base-dir={base.resolve()} symbols={list(symbols)} "
          f"check_unlock_only={args.check_unlock_only} "
          f"n_bootstrap={args.n_bootstrap} seed={args.seed}",
          file=sys.stderr, flush=True)

    if args.check_unlock_only:
        unlock = check_unlock(base, symbols, snapshot_hour=args.snapshot_hour)
        unlock.pop("_selections", None)
        unlock["hypothesis"] = HYPOTHESIS_ID
        unlock["capital_free"] = True
        unlock["data_gated"] = True
        out = out_dir / "c13_unlock_check.json"
        out.write_text(_dumps(unlock), encoding="utf-8")
        print(f"[c13] wrote {out}", file=sys.stderr, flush=True)
        if unlock["unlocked"]:
            found = {s: (v["d1"], v["d2"]) for s, v in unlock["selection"].items()
                     if v["found"]}
            print(f"[c13] UNLOCK MET: {found}", file=sys.stderr, flush=True)
            return RC_OK
        print("[c13] UNLOCK NOT MET — H-13 stays locked "
              "(no 2 vol-regime-disjoint snapshot days).", file=sys.stderr, flush=True)
        return RC_SKIP_LOCKED

    source = (f"{base}/raw/bybit/publicTrade + "
              f"{base}/raw/deribit/markprice.options")
    payload = run(
        base, symbols,
        n_bootstrap=args.n_bootstrap, seed=args.seed,
        trailing_days=args.trailing_days, snapshot_hour=args.snapshot_hour,
        source=source,
    )

    json_path = out_dir / "c13_tailshape_results.json"
    md_path = out_dir / "c13_tailshape_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c13] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c13] wrote {md_path}", file=sys.stderr, flush=True)

    if payload.get("skip"):
        print(f"[c13] SKIP: {payload['skip_reason']}", file=sys.stderr, flush=True)
        return RC_SKIP_LOCKED
    gate = payload.get("gate") or {}
    print(
        f"[c13] DONE: hypothesis={payload['hypothesis']} cells={len(payload['cells'])} "
        f"fdr_p_crit={gate.get('fdr_p_crit')} "
        f"n_fdr_sig={gate.get('n_fdr_significant')} "
        f"any_symbol_gate_met={gate.get('any_symbol_gate_met')}",
        file=sys.stderr, flush=True,
    )
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
