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
                                 [--check-gpu-only] [--allow-cpu-fallback]
                                 [--ckpt-dir DIR] [--no-ckpt]

Checkpoint/resume (default ON — c16_arrow pattern; the full plan is ~105
GPU trainings / ~35h+ and realistically NEVER survives one uninterrupted
invocation): every completed single training — per fold 1 main (InfoNCE +
frozen probe) + 20 permutation retrainings — is immediately persisted to
``--ckpt-dir`` (default ``<out-dir>/c17_venue_ckpt``; the runner passes a
STABLE, non-timestamped directory) and re-running with the SAME --ckpt-dir
resumes — an interrupt loses at most the training in flight. At startup
the driver logs 'X/Y Trainings bereits als Checkpoint vorhanden, Z noch
offen'. Checkpoints are fingerprinted over all result-relevant parameters
(incl. data window/Cutoff, seeds, batch/steps, encoder class); a mismatch
aborts hard (rc 1) instead of silently mixing stale results. ``--no-ckpt``
opts out (then ANY interrupt loses everything — smoke runs only).

COMPUTE GATING (verbindlich, SAME rc=2 "SKIP: no compute" convention as the
sibling Welle-5 CLIs c14_panellag.py/c15_grammar.py/c16_arrow.py):
  * ``--check-gpu-only`` reports torch/CUDA availability and exits WITHOUT
    running anything else — use it first on the target machine.
  * A full run WITHOUT a real CUDA device (or without torch) is NEVER
    verdict-bearing (registry H-17: the >= 2048 batch regime is part of the
    method) -- WITHOUT the explicit ``--allow-cpu-fallback`` escape hatch it
    now aborts BEFORE any data loading/training with exit code
    ``RC_SKIP_NO_COMPUTE`` (2), instead of silently completing a multi-hour
    numpy pipeline-smoke run and exiting 0 indistinguishably from a real
    verdict-bearing run. With ``--allow-cpu-fallback`` the run proceeds on
    the numpy fallback encoder but the JSON payload is still clearly marked
    ``compute.verdict_bearing: false``.

Exit codes: 0 = OK, 1 = error, 2 = compute gate SKIP (no torch/CUDA and
--allow-cpu-fallback not passed, or --check-gpu-only reports not capable).

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
    STEPS_MIN,
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
from bybit_edge.research.c17_venue.redundancy import (  # noqa: E402
    validate_c12_payload_shape,
)

RC_OK = 0
RC_ERROR = 1
RC_SKIP_NO_COMPUTE = 2


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
                   help="InfoNCE optimizer steps per (re)training "
                        f"(technical floor {STEPS_MIN}; use --allow-zero-steps "
                        "for a non-verdict-bearing --steps 0 smoke).")
    p.add_argument("--allow-zero-steps", action="store_true",
                   help="Dev/smoke override for --steps < technical floor "
                        f"({STEPS_MIN}) -- forces non-verdict-bearing. Without "
                        "this flag --steps 0 is rejected at startup instead "
                        "of silently 'training' for zero optimizer iterations.")
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
    p.add_argument("--ckpt-dir", default=None,
                   help="Checkpoint directory for resume (default: "
                        "<out-dir>/c17_venue_ckpt). Keep STABLE across "
                        "restarts — same path = resume; a different "
                        "configuration under the same path aborts hard "
                        "(fingerprint check).")
    p.add_argument("--no-ckpt", action="store_true",
                   help="Disable checkpoint/resume (any interrupt then loses "
                        "ALL progress of the ~35h+ plan — smoke runs only).")
    p.add_argument("--check-gpu-only", action="store_true",
                   help="Report torch/CUDA availability and exit (no run). "
                        "Compute-gating requirement (registry H-17).")
    p.add_argument("--h23-full-panel", action="store_true",
                   help="H-23 (registry 2026-08-18): define the daily "
                        "embedding-distance series over ALL panel windows of "
                        "each held-out symbol instead of only its test slice "
                        "(~85 instead of ~2 redundancy-overlap days). Writes "
                        "hypothesis=H-23; the 5 MAIN trainings rerun (own "
                        "checkpoint kind), the 100 null retrainings resume.")
    p.add_argument("--allow-cpu-fallback", action="store_true",
                   help="TEST-ONLY escape hatch: run the full pipeline "
                        "without a real CUDA device anyway (numpy pipeline-"
                        "smoke encoder). Result is NEVER verdict-bearing. "
                        "Without this flag a full run without CUDA aborts "
                        "immediately with RC_SKIP_NO_COMPUTE (2).")
    args = p.parse_args(argv)

    if args.steps < STEPS_MIN and not args.allow_zero_steps:
        print(f"[c17_venue] FATAL: --steps {args.steps} < technische "
              f"Untergrenze {STEPS_MIN} — null Optimizer-Schritte ist kein "
              f"Training (Audit-Fund: --steps 0 darf niemals als "
              f"'trained: True' erscheinen). Fuer einen NICHT-verdikt-"
              f"tragenden Test-/Pipeline-Lauf --allow-zero-steps setzen.",
              file=sys.stderr, flush=True)
        return RC_ERROR

    if args.check_gpu_only:
        rep = gpu_report()
        print(json.dumps(rep, indent=2))
        print(f"[c17_venue] check-gpu-only: verdict_capable={rep['verdict_capable']}",
              file=sys.stderr, flush=True)
        return RC_OK if rep["verdict_capable"] else RC_SKIP_NO_COMPUTE

    # COMPUTE GATE (audit finding: consistency with c14/c15/c16 sibling
    # CLIs): checked BEFORE any data loading/training. Without a real CUDA
    # device a full run is NEVER verdict-bearing (registry H-17); without
    # the explicit --allow-cpu-fallback opt-in this must SKIP with a
    # dedicated exit code, never silently complete a numpy pipeline-smoke
    # run and exit 0 indistinguishably from a real GPU verdict.
    cuda_used = bool(args.device != "cpu" and cuda_available())
    use_torch = bool(TORCH_AVAILABLE and args.device != "cpu")
    gpu_ready = bool(use_torch and cuda_used)
    if not gpu_ready and not args.allow_cpu_fallback:
        print(
            "[c17_venue] SKIP: kein echtes CUDA-Device (torch/CUDA fehlt "
            "oder --device cpu) und --allow-cpu-fallback nicht gesetzt. Ein "
            "voller Lauf ohne CUDA ist NIEMALS verdikt-tragend (Registry "
            "H-17: Batch >= 2048 ist Teil der Methode). Fuer einen NICHT-"
            "verdikt-tragenden Test-/Pipeline-Lauf --allow-cpu-fallback "
            "setzen.", file=sys.stderr, flush=True,
        )
        return RC_SKIP_NO_COMPUTE
    if not use_torch:
        print("[c17_venue] WARNING: torch/CUDA nicht verfuegbar oder "
              "--device cpu erzwungen — numpy Pipeline-Smoke-Encoder, "
              "Lauf ist NICHT verdikt-tragend (--allow-cpu-fallback gesetzt).",
              file=sys.stderr, flush=True)

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    exchanges = tuple(e.strip() for e in args.exchanges.split(",") if e.strip())
    base = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    if args.no_ckpt:
        ckpt_dir = None
    else:
        ckpt_dir = Path(args.ckpt_dir) if args.ckpt_dir else out_dir / "c17_venue_ckpt"
    print(f"[c17_venue] base-dir={base.resolve()} symbols={list(symbols)} "
          f"exchanges={list(exchanges)} window={args.start_date}..{args.end_date} "
          f"n_perm={args.n_perm} batch_size={args.batch_size} "
          f"gpu_ready={gpu_ready} allow_cpu_fallback={args.allow_cpu_fallback} "
          f"ckpt_dir={ckpt_dir if ckpt_dir is not None else 'DISABLED (--no-ckpt)'}",
          file=sys.stderr, flush=True)

    c12_payload = None
    if args.c12_results:
        c12_path = Path(args.c12_results)
        try:
            c12_payload = json.loads(c12_path.read_text(encoding="utf-8"))
        except OSError as exc:
            print(f"[c17_venue] WARNING: c12-results nicht lesbar "
                  f"({c12_path}): {exc} — Redundanz-Gate bleibt nicht "
                  f"auswertbar.", file=sys.stderr, flush=True)
        else:
            # Audit finding (late-failure-total-compute-loss): validate the
            # c12 payload SHAPE right here, in milliseconds, BEFORE the
            # 1-2 GPU-day run below -- not only after all folds finished,
            # deep inside redundancy_gate.
            try:
                validate_c12_payload_shape(c12_payload)
            except ValueError as exc:
                print(f"[c17_venue] FATAL: c12-results ({c12_path}) hat ein "
                      f"unerwartetes Schema: {exc}", file=sys.stderr, flush=True)
                return RC_ERROR

    try:
        nodes = load_panel(base, symbols, args.start_date, args.end_date,
                           exchanges=exchanges)
    except DataError as exc:
        print(f"[c17_venue] FATAL: panel not loadable: {exc}",
              file=sys.stderr, flush=True)
        return RC_ERROR
    print(f"[c17_venue] loaded {len(nodes)} nodes, "
          f"{sum(n.x.shape[0] for n in nodes)} windows total",
          file=sys.stderr, flush=True)

    encoder_factory = make_encoder_factory(
        use_torch=use_torch, device=args.device, seed=args.seed)

    fit_kwargs: dict = {}
    if use_torch:
        fit_kwargs = dict(batch_size=args.batch_size, steps=args.steps,
                          seed=args.seed, allow_small_batch=args.allow_small_batch,
                          allow_zero_steps=args.allow_zero_steps)

    source = f"{base}/raw/{{{','.join(exchanges)}}}/publicTrade ({args.start_date}..{args.end_date})"
    try:
        payload = run(
            nodes, encoder_factory=encoder_factory, fit_kwargs=fit_kwargs,
            n_perm=args.n_perm, seed=args.seed, c12_payload=c12_payload,
            cuda_used=cuda_used, torch_available=TORCH_AVAILABLE,
            batch_size=args.batch_size, source=source,
            start_date=args.start_date, end_date=args.end_date,
            ckpt_dir=ckpt_dir,
            full_panel_distance=args.h23_full_panel,
            hypothesis_id="H-23" if args.h23_full_panel else "H-17",
        )
    except ValueError as exc:
        # Incl. CheckpointMismatchError (stale --ckpt-dir): a HARD rc=1 —
        # never silently mixed, never degraded; the message carries the fix.
        print(f"[c17_venue] FATAL: {exc}", file=sys.stderr, flush=True)
        return RC_ERROR

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "c23_venue_full_results" if args.h23_full_panel else "c17_venue_results"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
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
    return RC_OK


if __name__ == "__main__":
    raise SystemExit(main())
