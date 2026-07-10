#!/usr/bin/env python3
"""C-16 Time-Arrow-CNN mess-gate driver (H-16, F-ARROW, KAPITALFREI, GPU).

Reads the read-only harvester Hive tree (default base ``data/harvest``):
Bybit ``publicTrade`` for the 1 s signed trade-imbalance series (5 symbols).
Classifier two-sample test (Lopez-Paz & Oquab 2017): a ResNet-18 classifies
FORWARD vs. TIME-REVERSED complex-Morlet-CWT log-power scalograms (reversal
on the raw series BEFORE the CWT). Bayes-optimal AUC = 0.5 for a
time-reversible process is the EXACT main null. Two mandatory controls:
(a) pipeline-leak control on IAAFT phase-randomised surrogates (must stay
<= 0.52, else METHODICALLY INVALID — no verdict, not a DROP), (b)
volatility-asymmetry ablation on |imbalance| (report-only).

    python scripts/c16_arrow.py [--base-dir data/harvest]
                                [--symbols BTCUSDT,ETHUSDT,...]
                                [--check-gpu-only] [--allow-cpu]
                                [--n-seeds 5] [--n-surrogates 20]
                                [--ablation-seeds 3] [--seed 42]
                                [--start-date 2026-03-27] [--end-date ...]
                                [--max-days N] [--out-dir DIR]

Exit codes: 0 = OK (full run written, gate-neutral payload — gate-auditor
adjudicates), 2 = SKIP (compute gate failed: no torch / no CUDA and
--allow-cpu not passed — a full run may NEVER be verdict-bearing on CPU),
1 = error. ``--check-gpu-only`` performs ONLY the honest compute report (no
data access, no training) and writes ``c16_gpu_check.json``.

DIFFERENTIATION (registry-mandated): this is NOT a duplicate of the locked
information-theory / nonlinear-dynamics cluster — see
``bybit_edge.research.c16_arrow.driver.DIFFERENTIATION_NOTE`` (also printed
in every rendered report).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c16_arrow.cnn import ComputeError  # noqa: E402
from bybit_edge.research.c16_arrow.driver import (  # noqa: E402
    HYPOTHESIS_ID,
    SYMBOLS_DEFAULT,
    BASE_START_DATE,
    check_gpu,
    render_markdown,
    run,
)

RC_OK = 0
RC_ERROR = 1
RC_SKIP_NO_COMPUTE = 2


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
        description="C-16 Time-Arrow-CNN mess-gate (H-16, GPU zwingend)."
    )
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(SYMBOLS_DEFAULT),
                   help="Comma-separated Bybit perp symbols (registered default: 5 symbols).")
    p.add_argument("--check-gpu-only", action="store_true",
                   help="Only report the honest torch/CUDA compute status (no data access).")
    p.add_argument("--allow-cpu", action="store_true",
                   help="Explicit escape hatch for a NON-verdict-bearing CPU smoke run.")
    p.add_argument("--start-date", default=BASE_START_DATE,
                   help="Registered data-binding start (default 2026-03-27).")
    p.add_argument("--end-date", default=None,
                   help="Data-binding end (Cutoff). Required for a full run.")
    p.add_argument("--n-seeds", type=int, default=5,
                   help="Full C2ST trainings per symbol (registered default 5).")
    p.add_argument("--n-surrogates", type=int, default=20,
                   help="IAAFT surrogate retrainings per symbol (registered default 20).")
    p.add_argument("--ablation-seeds", type=int, default=3,
                   help="Volatility-asymmetry ablation trainings per symbol (default 3).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu"],
                   help="Torch device (default cuda; cpu only valid with --allow-cpu).")
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--max-days", type=int, default=None,
                   help="SMOKE ONLY: cap valid days per symbol (forces verdict_bearing=False).")
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    args = p.parse_args(argv)

    symbols = tuple(s.strip().upper() for s in args.symbols.split(",") if s.strip())
    base = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[c16] base-dir={base.resolve()} symbols={list(symbols)} "
          f"check_gpu_only={args.check_gpu_only} allow_cpu={args.allow_cpu} "
          f"n_seeds={args.n_seeds} n_surrogates={args.n_surrogates} seed={args.seed}",
          file=sys.stderr, flush=True)

    if args.check_gpu_only:
        status = check_gpu()
        out = out_dir / "c16_gpu_check.json"
        out.write_text(_dumps(status), encoding="utf-8")
        print(f"[c16] wrote {out}", file=sys.stderr, flush=True)
        print(f"[c16] GPU-CHECK: torch={status['torch_available']} "
              f"cuda={status['cuda_available']} "
              f"verdict_capable={status['verdict_capable']}",
              file=sys.stderr, flush=True)
        return RC_OK if status["verdict_capable"] else RC_SKIP_NO_COMPUTE

    status = check_gpu()
    if not status["verdict_capable"] and not args.allow_cpu:
        print("[c16] SKIP: kein verdikt-taugliches Compute (torch/CUDA fehlt) "
              "und --allow-cpu nicht gesetzt. Voller Lauf ohne echtes CUDA-Device "
              "ist NIEMALS verdikt-tragend (Registry H-16).",
              file=sys.stderr, flush=True)
        return RC_SKIP_NO_COMPUTE
    if not status["torch_available"]:
        print("[c16] SKIP: torch nicht installiert.", file=sys.stderr, flush=True)
        return RC_SKIP_NO_COMPUTE

    if args.end_date is None:
        print("[c16] ERROR: --end-date (Cutoff) fehlt.", file=sys.stderr, flush=True)
        return RC_ERROR

    device = args.device if status["cuda_available"] else "cpu"
    source = f"{base}/raw/bybit/publicTrade"
    try:
        payload = run(
            base, symbols,
            start_date=args.start_date, end_date=args.end_date,
            n_seeds=args.n_seeds, n_surrogates=args.n_surrogates,
            ablation_seeds=args.ablation_seeds, seed=args.seed,
            device=device, allow_cpu=args.allow_cpu,
            epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
            max_days=args.max_days, source=source,
        )
    except ComputeError as exc:
        print(f"[c16] SKIP (ComputeError): {exc}", file=sys.stderr, flush=True)
        return RC_SKIP_NO_COMPUTE

    json_path = out_dir / "c16_arrow_results.json"
    md_path = out_dir / "c16_arrow_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c16] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c16] wrote {md_path}", file=sys.stderr, flush=True)

    gate = payload.get("gate") or {}
    print(
        f"[c16] DONE: hypothesis={payload['hypothesis']} cells={len(payload['cells'])} "
        f"verdict_bearing={payload['verdict_bearing']} status={gate.get('status')} "
        f"n_symbols_gate_met={gate.get('n_symbols_gate_met')} "
        f"leak_control_passed={gate.get('leak_control_passed')}",
        file=sys.stderr, flush=True,
    )
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
