#!/usr/bin/env python3
"""H-24 gate CLI — does minute net flow lead the next 30 min? (KAPITALFREI).

Runs the registered H-24 measurement against the WP-0 bar cache. NO raw-tick
access. The registered cache fingerprints are verified first; a mismatch
sets gate_valid=false (results written, not verdict-bearing, exit 3).

    python scripts/c24_impact.py [--cache-dir data/barcache] [--out-dir DIR]

Exit codes: 0 = OK · 1 = error · 3 = fingerprint mismatch (gate invalid).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.bar_cache import BarCacheError  # noqa: E402
from bybit_edge.research.c24_impact.driver import (  # noqa: E402
    DEFAULT_SYMBOLS,
    render_markdown,
    run,
)

RC_OK = 0
RC_FAIL = 1
RC_NO_FP = 3


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
        description="H-24 minute-flow forward-lead gate (KAPITALFREI).")
    p.add_argument("--cache-dir", default="data/barcache",
                   help="WP-0 bar cache root. Default data/barcache.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    p.add_argument("--out-dir", default=".")
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    cache = Path(args.cache_dir)
    print(f"[c24] cache={cache.resolve()} symbols={list(symbols)}",
          file=sys.stderr, flush=True)
    try:
        payload = run(cache, symbols=symbols,
                      source=f"{cache}/bars_1min (WP-0, read-only)")
    except BarCacheError as exc:
        print(f"[c24] FATAL BarCacheError: {exc}", file=sys.stderr, flush=True)
        return RC_FAIL

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "c24_impact_results.json").write_text(_dumps(payload),
                                                 encoding="utf-8")
    (out / "c24_impact_results.md").write_text(render_markdown(payload),
                                               encoding="utf-8")
    print(f"[c24] wrote {out / 'c24_impact_results.json'}", file=sys.stderr,
          flush=True)
    print(f"[c24] DONE: both_windows_pass={payload['both_windows_pass']} "
          f"control_passed={payload['control_passed']} "
          f"verdict_evaluable={payload['verdict_evaluable']} "
          f"gate_valid={payload['gate_valid']}", file=sys.stderr, flush=True)
    if not payload["gate_valid"]:
        print("[c24] LOUD FAIL: Cache-Fingerabdruecke stimmen nicht mit der "
              "Registrierung ueberein — Lauf NICHT urteilstragend.",
              file=sys.stderr, flush=True)
        return RC_NO_FP
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
