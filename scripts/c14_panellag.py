#!/usr/bin/env python3
"""C-14-PANELLAG driver — H-14 conditional cross-venue lead-lag graph (GPU).

Reads the read-only harvester Hive tree (default base ``data/harvest``) for
the two pre-registered calendar windows (registry H-14, identical H-09/H-12
convention: W1 = 2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04),
builds the 12-node 1s-panel per window (``panel.build_window``), runs the
node-ablation cross-attention lead-lag gate (``driver.run``: 1 full + 12
ablations + ~100 all-surrogate null retrainings per window, checkpointed/
resumable, ONE F-PANELLAG BH-FDR family over both windows), and writes
``c14_panellag_results.{json,md}``. Gate-neutral — the gate-auditor
adjudicates. KAPITALFREI.

    python scripts/c14_panellag.py [--base-dir data/harvest] [--out-dir DIR]
                                    [--ckpt-dir DIR] [--n-null 100] [--seed 42]
                                    [--check-gpu-only] [--allow-cpu-fallback]

COMPUTE GATING (registry H-14: GPU zwingend — analog to the H-11/H-13 data
gating, but for compute):
  * ``--check-gpu-only`` reports torch/CUDA availability honestly WITHOUT
    attempting any run (writes ``c14_gpu_check.json``, no training).
  * A full run WITHOUT real CUDA training NEVER produces a verdict-bearing
    result: without ``--allow-cpu-fallback`` it aborts cleanly BEFORE any
    training with a "GPU erforderlich, torch.cuda.is_available()=False"
    message (exit 2). With the explicit test-only
    ``--allow-cpu-fallback`` flag, the run proceeds on CPU (real torch if
    installed, else the pipeline-only dummy loss function — never a
    numpy training substitute for the registered retrain-null) but the
    JSON payload is clearly marked ``gpu_required: true`` /
    ``ran_on_gpu: false`` / ``gate_valid: false`` and
    ``weiter_indication`` is emitted as ``null`` (non-verdict-bearing).

Exit codes: 0 = OK, 1 = error (incl. missing harvester data — the T3 runner
pre-checks harvester paths itself and records its own SKIP before ever
invoking this CLI, mirroring run_h12.sh/run_h16.sh), 2 = compute gate failed
(no torch / no CUDA and --allow-cpu-fallback not passed — a full run may
NEVER be verdict-bearing on CPU; SAME rc=2 "SKIP: no compute" convention as
the sibling Welle-5 CLIs c15_grammar.py/c16_arrow.py/c17_venue.py).

No write access to the harvester tree. Mirrors the c12_frag/c13_tailshape
CLI conventions (data) and the c15_grammar/c16_arrow/c17_venue conventions
(GPU compute gating).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c14_panellag.ablation import (  # noqa: E402
    DEFAULT_N_NULL,
    make_dummy_train_fn,
    make_torch_train_fn,
)
from bybit_edge.research.c14_panellag.driver import (  # noqa: E402
    DEFAULT_WINDOW_A,
    DEFAULT_WINDOW_B,
    make_compute_info,
    render_markdown,
    run,
)
from bybit_edge.research.c14_panellag.encoder import (  # noqa: E402
    ComputeGateError,
    check_gpu,
)
from bybit_edge.research.c14_panellag.panel import (  # noqa: E402
    DEFAULT_NODES,
    DataError,
    build_window,
)

RC_OK = 0
RC_ERROR = 1
RC_SKIP_NO_COMPUTE = 2
#: Alias of RC_ERROR for the missing-harvester-data path (same exit code,
#: kept as its own name for readability at the call site).
RC_DATA_MISSING = RC_ERROR


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


def _nodes_present(base: Path) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for ex, sym in DEFAULT_NODES:
        from bybit_edge.research.c14_panellag.panel import map_exchange_symbol

        storage = map_exchange_symbol(ex, sym)
        p = base / "raw" / ex / "publicTrade" / f"symbol={storage}"
        if not p.is_dir():
            missing.append(f"{ex}:{storage}")
    return (len(missing) == 0, missing)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="C-14-PANELLAG conditional cross-venue lead-lag graph "
                    "(H-14, node-ablation cross-attention, F-PANELLAG, GPU-gated)."
    )
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--window-a-start", default=DEFAULT_WINDOW_A[0])
    p.add_argument("--window-a-end", default=DEFAULT_WINDOW_A[1])
    p.add_argument("--window-b-start", default=DEFAULT_WINDOW_B[0])
    p.add_argument("--window-b-end", default=DEFAULT_WINDOW_B[1])
    p.add_argument("--n-null", type=int, default=DEFAULT_N_NULL,
                   help="All-surrogate null retrainings per window (registry: ~100).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--device", default="auto", help="torch device (auto/cuda/cpu).")
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    p.add_argument("--ckpt-dir", default=None,
                   help="Checkpoint directory (resume-capable, STABLE across "
                        "restarts). Default <out-dir>/c14_checkpoints.")
    p.add_argument("--check-gpu-only", action="store_true",
                   help="Report torch/CUDA availability only, no run "
                        "(writes c14_gpu_check.json).")
    p.add_argument("--allow-cpu-fallback", action="store_true",
                   help="TEST-ONLY: run without real CUDA training anyway. "
                        "Result is NEVER verdict-bearing "
                        "(gate_valid=false, weiter_indication=null).")
    args = p.parse_args(argv)

    base = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.check_gpu_only:
        gpu = check_gpu()
        gpu["hypothesis"] = "H-14"
        gpu["capital_free"] = True
        gpu["compute_gated"] = True
        out = out_dir / "c14_gpu_check.json"
        out.write_text(_dumps(gpu), encoding="utf-8")
        print(f"[c14_panellag] wrote {out}", file=sys.stderr, flush=True)
        print(
            f"[c14_panellag] torch_available={gpu['torch_available']} "
            f"cuda_available={gpu['cuda_available']} "
            f"device_name={gpu['device_name']} gpu_ready={gpu['gpu_ready']}",
            file=sys.stderr, flush=True,
        )
        return RC_OK if gpu["gpu_ready"] else RC_SKIP_NO_COMPUTE

    gpu = check_gpu()
    print(
        f"[c14_panellag] base-dir={base.resolve()} n_nodes={len(DEFAULT_NODES)} "
        f"windows=[({args.window_a_start},{args.window_a_end}), "
        f"({args.window_b_start},{args.window_b_end})] n_null={args.n_null} "
        f"torch_available={gpu['torch_available']} cuda_available={gpu['cuda_available']} "
        f"allow_cpu_fallback={args.allow_cpu_fallback}",
        file=sys.stderr, flush=True,
    )

    if not gpu["gpu_ready"] and not args.allow_cpu_fallback:
        print(
            "[c14_panellag] FATAL: GPU erforderlich, "
            "torch.cuda.is_available()=False (Registry H-14: GPU zwingend). "
            "Kein Lauf ohne echtes CUDA-Training — verdikt-tragende Ergebnisse "
            "wuerden sonst die registrierte ~226-Trainings-Retrain-Null durch "
            "CPU-Training ersetzen. Fuer einen NICHT-verdikt-tragenden "
            "Test-/Pipeline-Lauf --allow-cpu-fallback setzen.",
            file=sys.stderr, flush=True,
        )
        return RC_SKIP_NO_COMPUTE

    data_ok, missing = _nodes_present(base)
    if not data_ok:
        print(
            f"[c14_panellag] SKIP: Harvester-Pfade fehlen fuer {missing} "
            f"unter {base}", file=sys.stderr, flush=True,
        )
        return RC_DATA_MISSING

    win_specs = (
        ("W1", args.window_a_start, args.window_a_end),
        ("W2", args.window_b_start, args.window_b_end),
    )
    windows = []
    for label, start, end in win_specs:
        try:
            win = build_window(base, start, end, label=label)
        except DataError as exc:
            print(f"[c14_panellag] FATAL: window {label} ({start}..{end}) not "
                  f"loadable: {exc}", file=sys.stderr, flush=True)
            return RC_ERROR
        print(f"[c14_panellag] window {win.label}: {win.n_seconds} seconds, "
              f"{win.n_nodes} nodes, mean coverage "
              f"{sum(win.coverage) / len(win.coverage):.3f}",
              file=sys.stderr, flush=True)
        windows.append(win)

    ckpt_dir = Path(args.ckpt_dir) if args.ckpt_dir else (out_dir / "c14_checkpoints")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    print(f"[c14_panellag] checkpoint dir (resume-capable): {ckpt_dir}",
          file=sys.stderr, flush=True)

    synthetic = False
    if gpu["gpu_ready"]:
        train_fn = make_torch_train_fn(len(DEFAULT_NODES), device=args.device)
        compute_info = make_compute_info(ran_on_gpu=True)
    elif gpu["torch_available"]:
        # --allow-cpu-fallback with torch installed but no CUDA: real torch
        # training on CPU (test-only; NEVER verdict-bearing).
        train_fn = make_torch_train_fn(len(DEFAULT_NODES), device="cpu")
        compute_info = make_compute_info(ran_on_gpu=False, cpu_fallback_used=True)
    else:
        # --allow-cpu-fallback without torch at all (sandbox): pipeline-only
        # dummy loss function. NEVER verdict-bearing, NEVER a null substitute.
        synthetic = True
        train_fn = make_dummy_train_fn(len(DEFAULT_NODES))
        compute_info = make_compute_info(
            ran_on_gpu=False, synthetic_train_fn_used=True,
        )

    source = f"{base}/raw/{{bybit,binance,deribit}}/publicTrade (12-node panel, 1s grid)"
    try:
        payload = run(
            windows, ckpt_dir, n_null=args.n_null, seed=args.seed, source=source,
            train_fn=train_fn, compute_info=compute_info, device=args.device,
        )
    except ComputeGateError as exc:
        print(f"[c14_panellag] FATAL: {exc}", file=sys.stderr, flush=True)
        return RC_SKIP_NO_COMPUTE
    except ValueError as exc:
        print(f"[c14_panellag] FATAL: {exc}", file=sys.stderr, flush=True)
        return RC_ERROR

    json_path = out_dir / "c14_panellag_results.json"
    md_path = out_dir / "c14_panellag_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c14_panellag] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c14_panellag] wrote {md_path}", file=sys.stderr, flush=True)

    if synthetic:
        print(
            "[c14_panellag] ACHTUNG: synthetisches train_fn (kein torch) — "
            "Ergebnis ist NICHT verdikt-tragend (nur Pipeline-Test).",
            file=sys.stderr, flush=True,
        )

    print(
        f"[c14_panellag] DONE: hypothesis={payload['hypothesis']} "
        f"validity_status={payload['validity_status']} "
        f"gate_valid={payload['compute_gating']['gate_valid']} "
        f"fdr_p_crit={payload['fdr_p_crit']} "
        f"n_fdr_sig={payload['n_fdr_significant']} "
        f"weiter_indication={payload['weiter_indication']}",
        file=sys.stderr, flush=True,
    )
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
