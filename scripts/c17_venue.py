#!/usr/bin/env python3
"""C-17-VENUE driver — H-17 venue-fingerprint contrastive-embedding gate.

Reads the read-only harvester Hive tree (default base ``data/harvest``) for
the registered 10-node panel (5 symbols x {bybit, binance}, publicTrade
only), builds 5-minute event windows with per-day quantile-normalised
channels (``features.load_panel``), runs the Leave-One-Symbol-Out
contrastive-embedding + frozen-linear-probe gate with the registered
within-symbol-within-day permutation null (``driver.run``: 5 folds x 20
full retrainings, ONE F-VENUE BH-FDR family), evaluates the pre-registered
non-redundancy gate against an existing c12_frag results JSON, and writes
``c17_venue_results.{json,md}``. Gate-neutral — the gate-auditor
adjudicates. KAPITALFREI.

    python scripts/c17_venue.py [--base-dir data/harvest] [--out-dir DIR]
                                 [--symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT]
                                 [--exchanges bybit,binance]
                                 [--start-date 2026-03-27] [--end-date 2026-07-04]
                                 [--n-perm 20] [--steps 10000] [--batch-size 2048]
                                 [--c12-results PATH] [--device auto] [--seed 42]
                                 [--check-gpu-only]

COMPUTE GATING (verbindlich): ``--check-gpu-only`` reports torch/CUDA
availability and exits WITHOUT running anything else — use it first on the
target machine. A full run WITHOUT a real CUDA device (or without torch)
falls back to a deterministic numpy pipeline-smoke encoder and the JSON
payload is marked ``compute.verdict_bearing: false`` — such a run must
NEVER be treated as a gate verdict (registry H-17: the >= 2048 batch regime
is part of the method).

No write access to the harvester tree. Mirrors the c12_frag CLI conventions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c17_venue.contrastive import (  # noqa: E402
    BATCH_SIZE_MIN,
    DEFAULT_STEPS,
)
from bybit_edge.research.c17_venue.driver import (  # noqa: E402
    N_PERMUTATIONS,
    render_markdown,
    run,
)
from bybit_edge.research.c17_venue.encoder import (  # noqa: E402
    TORCH_AVAILABLE,
    cuda_available,
    gpu_report,
    make_encoder_factory,
)
from bybit_edge.research.c17_venue.features import (  # noqa: E402
    DEFAULT_END_DATE,
    DEFAULT_EXCHANGES,
    DEFAULT_START_DATE,
    DEFAULT_SYMBOLS,
    DataError,
    load_panel,
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

    return json.dumps(clean(payload), indent=2, default=str)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="C-17-VENUE venue-fingerprint contrastive-embedding gate "
                    "(H-17, InfoNCE + frozen linear probe, F-VENUE)."
    )
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated symbols (registry: 5 Symbole).")
    p.add_argument("--exchanges", default=",".join(DEFAULT_EXCHANGES),
                   help="Comma-separated venues (registry: bybit,binance).")
    p.add_argument("--start-date", default=DEFAULT_START_DATE)
    p.add_argument("--end-date", default=DEFAULT_END_DATE)
    p.add_argument("--n-perm", type=int, default=N_PERMUTATIONS,
                   help="Permutation-null retrainings per fold (registry: 20).")
    p.add_argument("--steps", type=int, default=DEFAULT_STEPS,
                   help="InfoNCE optimizer steps per (re)training.")
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE_MIN,
                   help=f"Contrastive batch size (registry min {BATCH_SIZE_MIN}).")
    p.add_argument("--allow-small-batch", action="store_true",
                   help="Dev/smoke override for batch-size < registered min "
                        "(forces non-verdict-bearing).")
    p.add_argument("--c12-results", default="",
                   help="Path to an existing c12_frag_results.json for the "
                        "pre-registered non-redundancy gate. Omit to leave "
                        "the redundancy gate non-evaluable.")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    p.add_argument("--check-gpu-only", action="store_true",
                   help="Report torch/CUDA availability and exit (no run). "
                        "Compute-gating requirement (registry H-17).")
    args = p.parse_args(argv)

    if args.check_gpu_only:
        rep = gpu_report()
        print(json.dumps(rep, indent=2))
        print(f"[c17_venue] check-gpu-only: verdict_capable={rep['verdict_capable']}",
              file=sys.stderr, flush=True)
        return 0 if rep["verdict_capable"] else 3

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    exchanges = tuple(e.strip() for e in args.exchanges.split(",") if e.strip())
    base = Path(args.base_dir)
    print(f"[c17_venue] base-dir={base.resolve()} symbols={list(symbols)} "
          f"exchanges={list(exchanges)} window={args.start_date}..{args.end_date} "
          f"n_perm={args.n_perm} batch_size={args.batch_size}",
          file=sys.stderr, flush=True)

    try:
        nodes = load_panel(base, symbols, args.start_date, args.end_date,
                           exchanges=exchanges)
    except DataError as exc:
        print(f"[c17_venue] FATAL: panel not loadable: {exc}",
              file=sys.stderr, flush=True)
        return 1
    print(f"[c17_venue] loaded {len(nodes)} nodes, "
          f"{sum(n.x.shape[0] for n in nodes)} windows total",
          file=sys.stderr, flush=True)

    cuda_used = bool(args.device != "cpu" and cuda_available())
    use_torch = bool(TORCH_AVAILABLE and args.device != "cpu")
    if not use_torch:
        print("[c17_venue] WARNING: torch/CUDA nicht verfuegbar oder "
              "--device cpu erzwungen — numpy Pipeline-Smoke-Encoder, "
              "Lauf ist NICHT verdikt-tragend.", file=sys.stderr, flush=True)
    encoder_factory = make_encoder_factory(
        use_torch=use_torch, device=args.device, seed=args.seed)

    c12_payload = None
    if args.c12_results:
        c12_path = Path(args.c12_results)
        try:
            c12_payload = json.loads(c12_path.read_text(encoding="utf-8"))
        except OSError as exc:
            print(f"[c17_venue] WARNING: c12-results nicht lesbar "
                  f"({c12_path}): {exc} — Redundanz-Gate bleibt nicht "
                  f"auswertbar.", file=sys.stderr, flush=True)

    fit_kwargs: dict = {}
    if use_torch:
        fit_kwargs = dict(batch_size=args.batch_size, steps=args.steps,
                          seed=args.seed, allow_small_batch=args.allow_small_batch)

    source = f"{base}/raw/{{{','.join(exchanges)}}}/publicTrade ({args.start_date}..{args.end_date})"
    try:
        payload = run(
            nodes, encoder_factory=encoder_factory, fit_kwargs=fit_kwargs,
            n_perm=args.n_perm, seed=args.seed, c12_payload=c12_payload,
            cuda_used=cuda_used, torch_available=TORCH_AVAILABLE,
            batch_size=args.batch_size, source=source,
        )
    except ValueError as exc:
        print(f"[c17_venue] FATAL: {exc}", file=sys.stderr, flush=True)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c17_venue_results.json"
    md_path = out_dir / "c17_venue_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c17_venue] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c17_venue] wrote {md_path}", file=sys.stderr, flush=True)

    print(
        f"[c17_venue] DONE: hypothesis={payload['hypothesis']} "
        f"verdict_bearing={payload['compute']['verdict_bearing']} "
        f"folds_passed={payload['n_folds_passed']}/{payload['fdr_family_size']} "
        f"pooled_acc={payload['pooled_balanced_accuracy']:.4f} "
        f"redundant={payload['redundancy_gate']['redundant']} "
        f"weiter_indication={payload['weiter_indication']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
