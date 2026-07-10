#!/usr/bin/env python3
"""
H-18 · GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit (Welle 5).

**AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** Re-Execution der byte-
identischen, bereits adjudizierten F-LEADLAG-Pipeline aus GL-006 (H-04,
WEITER kapitalfrei) mit GENAU EINER vorab deklarierten Aenderung:
n_surrogates 200 -> 100.000 (500x), als GPU-Tensor-Batches erzeugt. Das
GL-006-Verdikt bleibt append-only unveraendert stehen; dieses Skript
schreibt NICHT gate_log.md — es produziert nur den Payload/Report, aus dem
SPAETER ein eigener, neuer GL-Eintrag (GL-014ff.) manuell erstellt wird.

KAPITALFREI: identisch GL-006 — reine Mess-Existenz-Frage, KEINE bps/Edge/
PnL/Friction-Metrik.

**Compute-Gating-Pflicht:** ein voller 100k-Surrogat-Lauf ist NUR auf einem
echten CUDA-Device verdikt-tragend (``verdict_carrying`` im Payload). Ohne
torch/CUDA degradiert das Skript ehrlich auf numpy und markiert JEDEN Lauf
als nicht-verdikt-tragend.

Aufruf::

    python scripts/c18_leadlag_audit.py --check-gpu-only
    python scripts/c18_leadlag_audit.py --self-test
    python scripts/c18_leadlag_audit.py --db data/duckdb/bybit.db --pair BTCUSDT,ETHUSDT \\
        --windows 2 --surrogates 100000 --backend cuda

Exit-Codes: 0 = ausgewertet (unabhaengig von verdict_carrying),
1 = Datendefekt/fehlende Eingabe, 2 = fehlende Dependency,
3 = --check-gpu-only meldet kein nutzbares CUDA-Device (informativ, kein Fehler).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def _parse_lags(s: str) -> tuple[int, ...]:
    out = tuple(int(x) for x in s.replace(" ", "").split(",") if x)
    if not out or any(v < 1 for v in out):
        raise argparse.ArgumentTypeError(f"invalid --lags '{s}' (positive ints, comma-separated)")
    return out


def _parse_pair(s: str) -> tuple[str, str]:
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"--pair needs exactly two symbols, got '{s}'")
    return parts[0], parts[1]


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "scinance2-impl" / "state"


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "H-18 GL-006/H-04 lead-lag high-N surrogate resolution audit "
            "(read-only, KAPITALFREI, AUFLOESUNGS-AUDIT KEINE NEU-ADJUDIKATION)."
        )
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--check-gpu-only", action="store_true",
        help="Nur GPU/CUDA-Status ehrlich melden (kein Lauf), exit 0=CUDA da, 3=kein CUDA.",
    )
    mode.add_argument(
        "--self-test", action="store_true",
        help="Methodik-Aequivalenz-Test gegen die ORIGINALE c17_c41_lead_lag-Pipeline "
             "bei kleinem N auf synthetischem Input (KEIN Aufloesungs-Audit, kein Datenzugriff).",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--db", type=Path, help="DuckDB-Datei mit trades-Tabelle (read-only)")
    src.add_argument("--file-a", type=Path, help="CSV/Parquet mit ts+price fuer Symbol A (mit --file-b)")
    p.add_argument("--file-b", type=Path, help="CSV/Parquet mit ts+price fuer Symbol B")
    p.add_argument(
        "--pair", type=_parse_pair, default=("BTCUSDT", "ETHUSDT"),
        help="Symbol-Paar A,B fuer den DuckDB-Pfad (Default BTCUSDT,ETHUSDT, identisch GL-006)",
    )
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (RW-Lock-Umgehung).",
    )
    p.add_argument("--windows", type=int, default=2, help="Anzahl disjunkter Fenster (>= 2, identisch GL-006)")
    p.add_argument(
        "--surrogates", type=int, default=100_000,
        help="Surrogate-N (registrierte Aufloesung: 100000; Default hier 100000).",
    )
    p.add_argument("--lags", type=_parse_lags, default=None, help="Lag-Universum in Bars (Default 1,2,3,5,10, identisch GL-006)")
    p.add_argument("--seed", type=int, default=42, help="RNG-Seed (identisch GL-006: 42)")
    p.add_argument("--grid-ms", type=float, default=None, help="Resample-Raster in ms (Default 1000, identisch GL-006)")
    p.add_argument("--n-bins", type=int, default=None, help="Quantil-Bins fuer TE-Diskretisierung (Default 3, identisch GL-006)")
    p.add_argument(
        "--max-ticks-per-window", type=int, default=None,
        help="Deterministische Tick-Obergrenze je Fenster je Symbol (Default 150000, identisch GL-006).",
    )
    p.add_argument(
        "--backend", choices=["auto", "cuda", "cpu", "numpy"], default="auto",
        help="Compute-Backend: auto (bestes verfuegbares, ehrlich degradiert), "
             "cuda (verlangt echtes CUDA-Device), cpu (torch-cpu), numpy (kein torch).",
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default: {DEFAULT_OUT})")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        import numpy  # noqa: F401
    except Exception as exc:  # pragma: no cover - dependency guard
        print(f"C18-LEADLAG-AUDIT DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    try:
        from bybit_edge.research.c18_leadlag_audit.driver import (
            DEFAULT_GRID_MS,
            DataError,
            WINDOW_MAX_TICKS,
            gpu_status,
            render_selftest_markdown,
            run,
            run_equivalence_selftest,
            write_outputs,
        )
        from bybit_edge.research.c17_c41_lead_lag.driver import (
            DEFAULT_LAGS,
            load_pair_duckdb,
            load_trades_file,
        )
        from bybit_edge.research.c17_c41_lead_lag.transfer_entropy import DEFAULT_N_BINS
    except Exception as exc:  # pragma: no cover - import guard
        print(f"C18-LEADLAG-AUDIT DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    if args.check_gpu_only:
        status = gpu_status(args.backend)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        print(
            f"C18-LEADLAG-AUDIT --check-gpu-only | cuda_available={status['cuda_available']} "
            f"resolved_backend={status['resolved_backend']} | {status['honest_note']}",
        )
        return 0 if status["cuda_available"] else 3

    if args.self_test:
        result = run_equivalence_selftest(
            n_surrogates=min(args.surrogates, 500) if args.surrogates else 200,
            seed=args.seed,
            backend=args.backend,
        )
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "c18_leadlag_audit_selftest.json"
        md_path = out_dir / "c18_leadlag_audit_selftest.md"
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(render_selftest_markdown(result), encoding="utf-8")
        print(
            f"C18-LEADLAG-AUDIT --self-test | equivalence_holds={result['equivalence_holds']} "
            f"backend={result['backend']} n_surrogates={result['n_surrogates']} -> {json_path}, {md_path}"
        )
        return 0 if result["equivalence_holds"] else 1

    lags = args.lags if args.lags is not None else DEFAULT_LAGS
    grid_ms = args.grid_ms if args.grid_ms is not None else DEFAULT_GRID_MS
    n_bins = args.n_bins if args.n_bins is not None else DEFAULT_N_BINS
    max_ticks = args.max_ticks_per_window if args.max_ticks_per_window is not None else WINDOW_MAX_TICKS

    if args.db is None and args.file_a is None:
        print("C18-LEADLAG-AUDIT: --db ODER --file-a/--file-b (oder --check-gpu-only/--self-test) benoetigt", file=sys.stderr)
        return 1

    try:
        if args.db is not None:
            sym_a, sym_b = args.pair
            (a, b) = load_pair_duckdb(args.db, sym_a, sym_b, db_copy=args.db_copy)
            source = f"{args.db}::trades"
        else:
            if args.file_b is None:
                print("C18-LEADLAG-AUDIT DATENDEFEKT: --file-a benoetigt --file-b", file=sys.stderr)
                return 1
            a = load_trades_file(args.file_a)
            b = load_trades_file(args.file_b)
            sym_a, sym_b = args.pair
            source = f"{args.file_a} / {args.file_b}"

        payload = run(
            a, b,
            symbol_a=sym_a, symbol_b=sym_b,
            n_windows=args.windows,
            lags=lags,
            n_bins=n_bins,
            grid_ms=grid_ms,
            n_surrogates=args.surrogates,
            seed=args.seed,
            max_ticks_per_window=max_ticks,
            backend=args.backend,
            source=source,
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"C18-LEADLAG-AUDIT DATENDEFEKT: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"C18-LEADLAG-AUDIT BACKEND-FEHLER: {exc}", file=sys.stderr)
        return 2

    print(
        f"C18-LEADLAG-AUDIT H-18 | pair={payload['symbol_a']}/{payload['symbol_b']} "
        f"windows={payload['n_windows']} n_surrogates={payload['n_surrogates']} "
        f"backend={payload['backend']['resolved']} mode={payload['mode']} "
        f"verdict_carrying={payload['verdict_carrying']} "
        f"t1_holds={payload['t1_partial_claim'].get('t1_holds')} "
        f"t2_holds={payload['t2_partial_claim'].get('t2_holds')} "
        f"-> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
