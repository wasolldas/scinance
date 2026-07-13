#!/usr/bin/env python3
"""C-15 trade-tape event-grammar mess-gate driver — H-15 (F-GRAMMAR).

Reads the read-only harvester Hive tree (default ``data/harvest``) over the
registry-fixed ~100-day grid 2026-03-27..2026-07-04, tokenises the Bybit
publicTrade stream per symbol (Side x Signed-Size-Quantile-8 x Log-IAT-8,
vocab 128, boundaries fitted PER FOLD on the train fold only), runs the
purged walk-forward gate (4 folds, 1-day embargo, 3 seeds) comparing a
decoder-only causal transformer against a KT-smoothed variable-order Markov
baseline (k<=4) beyond a within-hour-of-day block-shuffle null (>=200
surrogates), and writes ``c15_grammar_results.{json,md}``. Gate-neutral — the
gate-auditor adjudicates. KAPITALFREI.

    python scripts/c15_grammar.py --check-gpu-only
    python scripts/c15_grammar.py [--base-dir data/harvest] [--out-dir DIR]
                                  [--mode full|mechanics]

COMPUTE GATE (binding): ``--mode full`` (default) REFUSES to start without a
real CUDA device — this sandbox/degraded environment can only ever run
``--mode mechanics`` (pipeline mechanics only, ALWAYS ``gate_valid: false``,
never verdict-bearing). ``--check-gpu-only`` reports torch/CUDA availability
and exits WITHOUT starting any run (rc=0 always — it is a status probe, not
a gate).

No write access to the harvester tree. Mirrors the c10_pointer CLI
conventions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bybit_edge.research.c15_grammar.driver import (  # noqa: E402
    DEFAULT_DATA_END,
    DEFAULT_DATA_START,
    DEFAULT_SEEDS,
    DEFAULT_SYMBOLS,
    DataError,
    daily_grid,
    load_trade_events,
    render_markdown,
    run,
)
from bybit_edge.research.c15_grammar.stats import (  # noqa: E402
    BLOCK_LEN_EVENTS,
    EMBARGO_DAYS,
    N_FOLDS,
    N_SURROGATES_DEFAULT,
)
from bybit_edge.research.c15_grammar.transformer import (  # noqa: E402
    ComputeUnavailableError,
    GrammarTransformerConfig,
    torch_cuda_status,
)

#: Hard CLI floor on usable events per symbol (mirrors c10's DVOL floor
#: idea): below this a fold cannot possibly form a meaningful token stream
#: (the smallest fold in a 4-fold/100-day grid is ~15 days; a real Bybit
#: perp trades far more than this even on the quietest symbol). Unregistered
#: SAFETY floor (data-plumbing guard, not a gate threshold) — the run FAILS
#: (rc=1) instead of emitting a complete-looking but meaningless payload.
MIN_EVENTS_PER_SYMBOL = 5_000


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

    return json.dumps(clean(payload), indent=2)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="C-15 trade-tape event-grammar mess-gate (H-15, F-GRAMMAR)."
    )
    p.add_argument("--check-gpu-only", action="store_true",
                   help="Report torch/CUDA availability and exit (rc=0, no run).")
    p.add_argument("--base-dir", default="data/harvest",
                   help="Harvester data root (read-only junction). Default data/harvest.")
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                   help="Comma-separated perp symbols. Default 5-perp panel.")
    p.add_argument("--data-start", default=DEFAULT_DATA_START,
                   help="Daily-grid start (registry: 2026-03-27).")
    p.add_argument("--data-end", default=DEFAULT_DATA_END,
                   help="Daily-grid end (registry: 2026-07-04).")
    p.add_argument("--mode", choices=("full", "mechanics"), default="full",
                   help="full = verdict-capable (needs CUDA, registry-exact "
                        "defaults). mechanics = pipeline-mechanics only, "
                        "NEVER verdict-bearing (gate_valid always false).")
    p.add_argument("--n-folds", type=int, default=N_FOLDS,
                   help=f"Walk-forward folds (registry: {N_FOLDS}).")
    p.add_argument("--embargo-days", type=int, default=EMBARGO_DAYS,
                   help=f"Embargo days per fold (registry: {EMBARGO_DAYS}).")
    p.add_argument("--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS),
                   help="Comma-separated seeds (registry: 3 per fold).")
    p.add_argument("--n-surrogates", type=int, default=N_SURROGATES_DEFAULT,
                   help=f"Block-shuffle surrogates (registry: >= {N_SURROGATES_DEFAULT}).")
    p.add_argument("--block-len", type=int, default=BLOCK_LEN_EVENTS,
                   help=f"Surrogate shuffle block length in events (registry: {BLOCK_LEN_EVENTS}).")
    p.add_argument("--use-tick-direction", action="store_true",
                   help="Enable the optional tick-direction vocab extension (128 -> 256). "
                        "Registered BASE vocab is 128 — enabling this voids gate_valid.")
    p.add_argument("--context-len", type=int, default=1024,
                   help="Transformer context length (registry: 1024).")
    p.add_argument("--d-model", type=int, default=256)
    p.add_argument("--n-heads", type=int, default=4)
    p.add_argument("--n-layers", type=int, default=4)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--max-events-per-day", type=int, default=0,
                   help="Debug/mechanics convenience: cap events/day per symbol "
                        "(0 = no cap, registered data binding). Voids gate_valid.")
    p.add_argument("--out-dir", default=".", help="Output directory for results.")
    p.add_argument("--ckpt-dir", default=None,
                   help="Per-symbol checkpoint directory (default: "
                        "<out-dir>/c15_grammar_ckpt). Each completed symbol "
                        "is atomically checkpointed there; re-running with "
                        "the SAME --ckpt-dir (and identical registered "
                        "parameters) RESUMES by skipping already-finished "
                        "symbols instead of re-training them, so a timeout/"
                        "crash loses at most the in-flight symbol. Pass "
                        "--no-ckpt to disable.")
    p.add_argument("--no-ckpt", action="store_true",
                   help="Disable per-symbol checkpointing entirely.")
    args = p.parse_args(argv)

    if args.check_gpu_only:
        status = torch_cuda_status()
        print(json.dumps(status, indent=2))
        print(
            f"[c15_grammar] check-gpu-only: torch_available="
            f"{status['torch_available']} cuda_available={status['cuda_available']} "
            f"device={status.get('cuda_device_name')}",
            file=sys.stderr, flush=True,
        )
        return 0

    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    seeds = tuple(int(s.strip()) for s in args.seeds.split(",") if s.strip())
    base = Path(args.base_dir)
    days = daily_grid(args.data_start, args.data_end)
    print(f"[c15_grammar] base-dir={base.resolve()} symbols={list(symbols)} "
          f"grid={args.data_start}..{args.data_end} ({len(days)} days) "
          f"mode={args.mode} folds={args.n_folds} embargo={args.embargo_days} "
          f"seeds={seeds} surrogates={args.n_surrogates}",
          file=sys.stderr, flush=True)

    status = torch_cuda_status()
    if args.mode == "full" and not status["cuda_available"]:
        print(f"[c15_grammar] FATAL: --mode full requires CUDA (registry: GPU, "
              f"zwingend); torch_available={status['torch_available']} "
              f"cuda_available={status['cuda_available']}. Use --mode mechanics "
              f"or --check-gpu-only.", file=sys.stderr, flush=True)
        return 1

    symbol_events = {}
    for symbol in symbols:
        try:
            symbol_events[symbol] = load_trade_events(
                base, symbol, days,
                max_events_per_day=args.max_events_per_day,
            )
        except DataError as exc:
            print(f"[c15_grammar] FATAL: {symbol} not loadable: {exc}",
                  file=sys.stderr, flush=True)
            return 1
        if symbol_events[symbol].n_events < MIN_EVENTS_PER_SYMBOL:
            print(f"[c15_grammar] FATAL: {symbol} has only "
                  f"{symbol_events[symbol].n_events} events "
                  f"(< floor {MIN_EVENTS_PER_SYMBOL})", file=sys.stderr, flush=True)
            return 1

    cfg = GrammarTransformerConfig(
        vocab_size=256 if args.use_tick_direction else 128,
        context_len=args.context_len, d_model=args.d_model,
        n_heads=args.n_heads, n_layers=args.n_layers,
        epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
    )
    source = f"{base}/raw/bybit/publicTrade (H-15, read-only harvester tree)"
    out_dir = Path(args.out_dir)
    if args.no_ckpt:
        ckpt_dir = None
    else:
        ckpt_dir = Path(args.ckpt_dir) if args.ckpt_dir else out_dir / "c15_grammar_ckpt"
        print(f"[c15_grammar] per-symbol checkpoint dir: {ckpt_dir} "
              f"(re-run with the same --ckpt-dir to resume after a timeout/"
              f"crash)", file=sys.stderr, flush=True)
    try:
        payload = run(
            symbol_events, days,
            mode=args.mode, config=cfg,
            n_folds=args.n_folds, embargo_days=args.embargo_days,
            seeds=seeds, n_surrogates=args.n_surrogates,
            block_len=args.block_len, use_tick_direction=args.use_tick_direction,
            events_capped=bool(args.max_events_per_day),
            max_events_per_day=args.max_events_per_day,
            source=source,
            ckpt_dir=ckpt_dir,
        )
    except ComputeUnavailableError as exc:
        print(f"[c15_grammar] FATAL (compute gate): {exc}", file=sys.stderr, flush=True)
        return 1
    except (DataError, ValueError) as exc:
        print(f"[c15_grammar] FATAL: {exc}", file=sys.stderr, flush=True)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c15_grammar_results.json"
    md_path = out_dir / "c15_grammar_results.md"
    json_path.write_text(_dumps(payload), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[c15_grammar] wrote {json_path}", file=sys.stderr, flush=True)
    print(f"[c15_grammar] wrote {md_path}", file=sys.stderr, flush=True)

    print(
        f"[c15_grammar] DONE: hypothesis={payload['hypothesis']} "
        f"mode={payload['mode']} ran_on_gpu={payload['ran_on_gpu']} "
        f"gate_valid={payload['gate_valid']} "
        f"n_symbols_pass={payload['n_symbols_pass']} "
        f"family_pass_geq_4of5={payload['family_pass_geq_4of5']} "
        f"fdr_p_crit={payload['fdr_p_crit']}",
        file=sys.stderr, flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
