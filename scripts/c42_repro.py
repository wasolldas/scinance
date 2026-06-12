#!/usr/bin/env python3
"""
C-42-Reproduktions-Pipeline (WP-4): reproduziert die Vol-Regression
``log(realised_vol_60m)`` (research_notes Test-R^2 0.249) unter sauberem
purged-Walk-Forward-Design und wertet sie gegen das vorregistrierte H-02-Gate
aus (scinance2-impl/state/hypothesis_registry.md).

Datenzugriff rein lesend: entweder die Bestands-DuckDB (``--db-path`` ->
``PersistenceLayer.query_kline``) ODER eine CSV-Fixture (``--csv-path``;
Spalten ts,open,high,low,close,volume,turnover). Das Bestands-Schema und der
Collector werden nicht beruehrt. Haelt der laufende 1.0-Collector den
RW-Lock, schlaegt das Open nach ``DB_OPEN_TIMEOUT_S`` mit klarer Meldung fehl;
``--db-copy`` liest stattdessen eine temporaere Kopie der .duckdb-Datei
(lock-frei, Kopie wird nach dem Lesen geloescht).

Modelle (DEC-04): ``--model lightgbm`` (reproduktions-treu; braucht
``pip install -e .[vol]``), ``histgbm`` (sklearn-Fallback, DEC-04a),
``har`` (HAR-RV-Baseline, laeuft IMMER, auch in der Sandbox).

Aufruf::

    python scripts/c42_repro.py --csv-path tests/fixtures/c42/btc_garch_30d.csv --model har
    python scripts/c42_repro.py --db-path data/bybit.duckdb --symbol BTCUSDT --model lightgbm
    python scripts/c42_repro.py --csv-path <fixture> --model histgbm --quick

Output: ``c42_results.json`` + ``c42_report.md`` ins ``--out``-Verzeichnis.
Exit-Codes: 0 = ausgewertet (unabhaengig vom Pre-Check), 1 = Datendefekt/fehlende
Eingabe, 2 = Modell-Dependency fehlt (LightGBM/sklearn nicht installiert).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from bybit_edge.research.c42_rv import render_markdown, run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "scinance2-impl" / "state"
KLINE_COLUMNS = ["ts", "open", "high", "low", "close", "volume", "turnover"]

# Hard timeout for the read-only DuckDB open. If the 1.0 collector holds the
# RW lock, ``duckdb.connect(read_only=True)`` can block indefinitely (T2 run
# 2026-06-12: 900 s hang after "[c42] opening duckdb read-only"). After this
# timeout we fail fast with a clear hint instead of eating the runner budget.
DB_OPEN_TIMEOUT_S = 30.0

DB_LOCKED_HINT = (
    "DuckDB gesperrt (laeuft der 1.0-Collector?) — Workaround: --db-copy "
    "(liest eine temporaere Kopie der .duckdb-Datei)"
)


class CLIError(RuntimeError):
    """Bad / missing input -> exit code 1."""


def _open_db_with_timeout(opener, timeout_s: float = DB_OPEN_TIMEOUT_S):
    """Run ``opener()`` (the DuckDB open) in a daemon thread with a hard timeout.

    DuckDB allows exactly one RW process; a concurrent read-only open can
    either fail with a lock error or block. Both cases are mapped to a
    ``CLIError`` carrying the --db-copy hint. The opener thread is a daemon so
    a hung open never keeps the process alive past sys.exit().
    """
    import threading

    box: dict = {}

    def _work() -> None:
        try:
            box["layer"] = opener()
        except Exception as exc:  # noqa: BLE001 - re-raised below
            box["error"] = exc

    t = threading.Thread(target=_work, name="c42-db-open", daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise CLIError(
            f"DuckDB-Open haengt seit {timeout_s:.0f}s — {DB_LOCKED_HINT}"
        )
    if "error" in box:
        exc = box["error"]
        msg = str(exc)
        if "lock" in msg.lower() or "Conflicting" in msg:
            raise CLIError(f"DuckDB-Open fehlgeschlagen ({msg}) — {DB_LOCKED_HINT}")
        raise exc
    return box["layer"]


def _load_from_csv(path: Path, symbol: str) -> pd.DataFrame:
    if not path.is_file():
        raise CLIError(f"csv fixture not found: {path}")
    df = pd.read_csv(path)
    missing = [c for c in KLINE_COLUMNS if c not in df.columns]
    if missing:
        raise CLIError(f"csv {path} missing columns: {missing}")
    if "symbol" in df.columns:
        df = df[df["symbol"] == symbol]
        if df.empty:
            raise CLIError(f"csv {path} has no rows for symbol {symbol}")
    return df[KLINE_COLUMNS].sort_values("ts").reset_index(drop=True)


def _load_from_db(
    db_path: Path,
    symbol: str,
    max_bars: Optional[int] = None,
    db_copy: bool = False,
) -> pd.DataFrame:
    if not db_path.is_file():
        raise CLIError(f"duckdb file not found: {db_path}")
    try:
        from bybit_edge.persistence.db import PersistenceLayer
    except ImportError as exc:  # pragma: no cover
        raise CLIError(f"cannot import PersistenceLayer: {exc}") from exc

    copy_dir: Optional[Path] = None
    if db_copy:
        # Lock-safe path: read a snapshot copy so a collector holding the RW
        # lock on the original can never block or be disturbed. The copy is
        # deleted again right after the (single, short) read.
        import shutil
        import tempfile

        copy_dir = Path(tempfile.mkdtemp(prefix="c42_dbcopy_"))
        copied = copy_dir / db_path.name
        print(f"[c42] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
        shutil.copy2(db_path, copied)
        wal = db_path.with_name(db_path.name + ".wal")
        if wal.is_file():
            shutil.copy2(wal, copy_dir / wal.name)
        db_path = copied

    print(f"[c42] opening duckdb read-only: {db_path}", file=sys.stderr, flush=True)
    try:
        layer = _open_db_with_timeout(
            lambda: PersistenceLayer(db_path=db_path, read_only=True)
        )
    except CLIError:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
        raise
    try:
        # Full available range; quick mode caps via tail-slice after load
        # (DuckDB lock-friendly: one short read, no per-bar round-trips).
        print(f"[c42] loading kline_1min for {symbol}...", file=sys.stderr, flush=True)
        pl_df = layer.query_kline(symbol, 0, 2**63 - 1)
        df = pl_df.to_pandas() if hasattr(pl_df, "to_pandas") else pd.DataFrame(pl_df)
        print(f"[c42] loaded {len(df)} bars", file=sys.stderr, flush=True)
        if max_bars is not None and len(df) > max_bars:
            df = df.sort_values("ts").tail(max_bars).reset_index(drop=True)
            print(f"[c42] quick-mode: capped to last {max_bars} bars", file=sys.stderr, flush=True)
    finally:
        close = getattr(layer, "close", None)
        if callable(close):
            close()
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c42] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)
    if df.empty:
        raise CLIError(f"no kline_1min rows for {symbol} in {db_path}")
    return df[KLINE_COLUMNS].sort_values("ts").reset_index(drop=True)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="C-42 vol-regression reproduction (read-only on kline_1min)."
    )
    p.add_argument("--symbol", default="BTCUSDT", help="Symbol (Default BTCUSDT).")
    p.add_argument("--db-path", type=Path, default=None, help="DuckDB-Datei (read-only).")
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (umgeht den "
             "RW-Lock des laufenden 1.0-Collectors; Kopie wird danach geloescht).",
    )
    p.add_argument("--csv-path", type=Path, default=None, help="CSV-Fixture als Daten-Alternative.")
    p.add_argument(
        "--model", choices=["lightgbm", "histgbm", "har"], default="har",
        help="Modell (DEC-04): lightgbm (treu) | histgbm (sklearn) | har (immer).",
    )
    p.add_argument(
        "--quick", action="store_true",
        help="T2-Modus: 1 Symbol, reduzierte Folds (2) + weniger Permutationen.",
    )
    p.add_argument("--n-folds", type=int, default=3, help="Anzahl disjunkter OOS-Fenster (>=2).")
    p.add_argument("--embargo-bars", type=int, default=1440, help="Embargo in Bars (Default 1 Tag).")
    p.add_argument(
        "--max-bars", type=int, default=None,
        help="Cap on bars loaded (default: 60_000 in --quick mode = ~42 days, unlimited otherwise).",
    )
    p.add_argument("--seed", type=int, default=42, help="Seed (explizit).")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default {DEFAULT_OUT}).")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    n_folds = 2 if args.quick else max(2, args.n_folds)
    perm_repeats = 8 if args.quick else 20

    # Quick mode: cap bars so the feature build does not chew through years
    # of 1-min klines. 60_000 bars ~= 42 days, plenty for >=2 OOS folds with
    # 1-day embargo and the 240-min lookback window.
    max_bars = args.max_bars
    if max_bars is None and args.quick:
        max_bars = 60_000

    try:
        if args.csv_path is not None:
            klines = _load_from_csv(args.csv_path, args.symbol)
            if max_bars is not None and len(klines) > max_bars:
                klines = klines.sort_values("ts").tail(max_bars).reset_index(drop=True)
                print(f"[c42] quick-mode: capped csv to last {max_bars} bars", file=sys.stderr, flush=True)
        elif args.db_path is not None:
            klines = _load_from_db(
                args.db_path, args.symbol, max_bars=max_bars, db_copy=args.db_copy
            )
        else:
            raise CLIError("provide either --csv-path or --db-path")
    except CLIError as exc:
        print(f"C42-REPRO DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    try:
        result = run_pipeline(
            klines,
            symbol=args.symbol,
            model_name=args.model,
            n_folds=n_folds,
            embargo_bars=args.embargo_bars,
            seed=args.seed,
            perm_repeats=perm_repeats,
        )
    except ImportError as exc:
        print(f"C42-REPRO MODELL-DEP FEHLT: {exc}", file=sys.stderr)
        return 2
    except (ValueError, AssertionError) as exc:
        print(f"C42-REPRO DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / "c42_results.json"
    md_path = args.out / "c42_report.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(result), encoding="utf-8")

    min_r2 = min((f["model_r2"] for f in result["folds"]), default=float("nan"))
    print(
        f"C42-REPRO {result['precheck_verdict']} | H-02 | symbol={result['symbol']} "
        f"model={result['model']} folds={result['n_folds']} "
        f"min_oos_r2={min_r2:.4f} r2_pass={result['all_folds_r2_pass']} "
        f"qlike<har={result['all_folds_qlike_beats_har']} -> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
