#!/usr/bin/env python3
"""H-22 L2-TILT gate CLI — KAPITALFREI (Welle 6).

Runs the registered H-22 gate against the WP-2 tilt store and the WP-0 bar
cache. Both stores are fingerprint-pinned; a mismatch -> gate_valid=false,
exit 3. A judgment window under the 85% coverage floor -> SKIP, exit 2.

    python scripts/c22_l2tilt.py [--tilt-dir data/l2tilt]
        [--cache-dir data/barcache] [--out-dir DIR]

Exit codes: 0 = OK · 1 = error · 2 = coverage SKIP · 3 = fingerprint mismatch.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.bar_cache import BarCacheError  # noqa: E402
from bybit_edge.research.c22_l2tilt.driver import render_markdown, run  # noqa: E402
from bybit_edge.research.c22_l2tilt.extract import L2ExtractError  # noqa: E402

RC_OK, RC_FAIL, RC_SKIP, RC_NO_FP = 0, 1, 2, 3


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
    p = argparse.ArgumentParser(description="H-22 L2-TILT gate (KAPITALFREI).")
    p.add_argument("--tilt-dir", default="data/l2tilt")
    p.add_argument("--cache-dir", default="data/barcache")
    p.add_argument("--out-dir", default=".")
    args = p.parse_args(argv)

    try:
        payload = run(Path(args.tilt_dir), Path(args.cache_dir),
                      source=f"{args.tilt_dir} (WP-2) + {args.cache_dir} (WP-0)")
    except (BarCacheError, L2ExtractError) as exc:
        print(f"[c22] FATAL: {exc}", file=sys.stderr, flush=True)
        return RC_FAIL

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "c22_l2tilt_results.json").write_text(_dumps(payload),
                                                 encoding="utf-8")
    (out / "c22_l2tilt_results.md").write_text(render_markdown(payload),
                                               encoding="utf-8")
    print(f"[c22] wrote {out / 'c22_l2tilt_results.json'}", file=sys.stderr,
          flush=True)
    print(f"[c22] DONE: both_btc_windows_pass={payload['both_btc_windows_pass']} "
          f"coverage_ok={payload['coverage_ok']} "
          f"gate_valid={payload['gate_valid']}", file=sys.stderr, flush=True)
    if not payload["gate_valid"]:
        print("[c22] LOUD FAIL: Store-Fingerabdruecke stimmen nicht mit der "
              "Registrierung ueberein.", file=sys.stderr, flush=True)
        return RC_NO_FP
    if not payload["coverage_ok"]:
        print("[c22] SKIP: Abdeckungs-Floor in einem urteilstragenden Fenster "
              "verfehlt — kein Verdikt.", file=sys.stderr, flush=True)
        return RC_SKIP
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
