#!/usr/bin/env python3
"""WP-11 RELAX runner -- activity relaxation rate after H-20 shock hours
(KAPITALFREI, deskriptiv, PRD_SCINANCE3.md 11.3).

Reads EXCLUSIVELY the WP-0 bar cache. Optionally reads an already-written
STRESS_ABS fixture (``wp10_coherence.stress_canon``, DEC-56) to add the
STRESS_ABS-vs-other split; without ``--stress-abs`` that split is skipped
(reported, not silently omitted).

    python scripts/wp11_relax.py [--cache-dir data/barcache] \\
        [--stress-abs scinance3-impl/state/wp10_stress_canon/stress_abs.json] \\
        [--out-dir DIR] [--seed 42]

Writes wp11_summary.json + wp11_report.md + DEC-53 artefacts (per-event
CSV, bootstrap fingerprint) under --out-dir. NEVER writes under
data/harvest (loud refusal in report.py). Exit codes: 0 = OK (RUN or
KEIN BEFUND, both are valid deskriptiv outcomes) - 1 = error -
3 = fingerprint mismatch (gate_valid=false, results still written).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.bar_cache import BarCacheError  # noqa: E402
from bybit_edge.research.wp10_coherence import stress_canon as sc  # noqa: E402
from bybit_edge.research.wp11_relax import report as rp  # noqa: E402
from bybit_edge.research.wp11_relax.measure import (  # noqa: E402
    DEFAULT_SYMBOLS,
    SEED,
    run,
)

RC_OK = 0
RC_FAIL = 1
RC_NO_FP = 3


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="WP-11 RELAX measurement (KAPITALFREI, deskriptiv).")
    p.add_argument("--cache-dir", default="data/barcache")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    p.add_argument("--stress-abs", default="",
                   help="Pfad zu einem geschriebenen STRESS_ABS-Fixture (wp10_coherence.stress_canon)")
    p.add_argument("--out-dir", default=".")
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    cache = Path(args.cache_dir)

    stress_abs_days: frozenset[str] | None = None
    if args.stress_abs:
        fixture = sc.read_fixture(args.stress_abs)
        stress_abs_days = frozenset(fixture["days"])
        print(f"[wp11] STRESS_ABS geladen: {len(stress_abs_days)} Tage aus {args.stress_abs}",
             file=sys.stderr, flush=True)
    else:
        print("[wp11] KEIN --stress-abs uebergeben -- Regime-Split (STRESS_ABS vs. other) "
             "wird ausgelassen.", file=sys.stderr, flush=True)

    print(f"[wp11] cache={cache.resolve()} symbols={list(symbols)} seed={args.seed}",
         file=sys.stderr, flush=True)
    try:
        payload = run(cache, symbols=symbols, stress_abs_days=stress_abs_days,
                     seed=args.seed, source=f"{cache}/bars_1min (WP-0, read-only)")
    except BarCacheError as exc:
        print(f"[wp11] FATAL BarCacheError: {exc}", file=sys.stderr, flush=True)
        return RC_FAIL

    out = Path(args.out_dir)
    try:
        written = rp.build_report(payload, out)
    except rp.ReportError as exc:
        print(f"[wp11] {exc}", file=sys.stderr, flush=True)
        return RC_FAIL
    except ValueError as exc:   # data/harvest refusal
        print(f"[wp11] FATAL: {exc}", file=sys.stderr, flush=True)
        return RC_FAIL

    print(f"[wp11] wrote {written['summary_path']}", file=sys.stderr, flush=True)
    print(f"[wp11] DONE: status={payload['status']} gate_valid={payload['gate_valid']} "
         f"n_events_real={payload['n_events_real']} "
         f"n_event_clusters_total={payload['n_event_clusters_total']}",
         file=sys.stderr, flush=True)
    if not payload["gate_valid"]:
        print("[wp11] LOUD: Cache-Fingerabdruecke stimmen nicht mit der Registrierung "
             "ueberein -- Lauf NICHT urteilstragend.", file=sys.stderr, flush=True)
        return RC_NO_FP
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
