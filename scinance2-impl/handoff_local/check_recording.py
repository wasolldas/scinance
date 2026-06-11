#!/usr/bin/env python3
"""Recorder Parquet verification helper for the T2/T3 handoff runners (WP-5).

Checks, per F0 recording stream under ``data/parquet/recording_f0/``:

* Parquet segments exist (optionally only segments younger than
  ``--max-age-min`` — used by the T2 smoke so stale data never masks a dead
  recorder),
* row count > 0 per stream (``adl_alerts`` is event-driven and may be
  legitimately empty — it is reported but never fails the check),
* every segment carries the expected ``schema_version`` metadata,
* optionally (``--cap-gb``) that total usage respects the ring-buffer cap.

Read-only; never modifies recorded data. Writes a machine-readable JSON
(``--json``) for the SUMMARY aggregation in addition to stdout lines.

Exit codes: 0 = all checks pass, 1 = at least one check failed,
2 = unexpected error (missing pyarrow etc.).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "data" / "parquet" / "recording_f0"

# Streams that MUST have rows after a live run (rpi orderbook is 100 ms,
# insurance 1 s, premium-index via REST poll, option tickers continuous).
DEFAULT_REQUIRED = "rpi_orderbook,insurance_pool,premium_index_kline,option_tickers"
# Event-driven streams: presence of files/rows is reported, absence is OK.
DEFAULT_OPTIONAL = "adl_alerts"


def _expected_schema_version() -> int:
    try:
        from bybit_edge.recorder.storage import SCHEMA_VERSION  # type: ignore

        return int(SCHEMA_VERSION)
    except Exception:
        return 1  # documented default (storage.py SCHEMA_VERSION = 1)


def _segment_stats(path: Path) -> tuple[int, str]:
    """Return (num_rows, schema_version_str) for one Parquet segment."""
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(path)
    n_rows = int(pf.metadata.num_rows)
    meta = pf.metadata.metadata or {}
    version = meta.get(b"schema_version", b"?").decode("utf-8", "replace")
    return n_rows, version


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify F0 recorder Parquet output (read-only).")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help=f"Recording root (Default: {DEFAULT_ROOT})")
    ap.add_argument("--max-age-min", type=float, default=0,
                    help="Only consider segments younger than N minutes (0 = all).")
    ap.add_argument("--cap-gb", type=float, default=None,
                    help="If set: verify total recording size <= cap (ring buffer).")
    ap.add_argument("--require", default=DEFAULT_REQUIRED,
                    help="Comma list of streams that must have rows.")
    ap.add_argument("--optional", default=DEFAULT_OPTIONAL,
                    help="Comma list of streams reported but allowed to be empty.")
    ap.add_argument("--json", type=Path, default=None,
                    help="Write machine-readable result JSON to this path.")
    args = ap.parse_args(argv)

    expected_version = str(_expected_schema_version())
    required = [s.strip() for s in args.require.split(",") if s.strip()]
    optional = [s.strip() for s in args.optional.split(",") if s.strip()]
    cutoff = time.time() - args.max_age_min * 60 if args.max_age_min > 0 else None

    streams_out = []
    overall_pass = True

    if not args.root.is_dir():
        print(f"RECORDING-CHECK FAIL: root fehlt: {args.root}")
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(
                {"pass": False, "root": str(args.root), "error": "root missing",
                 "streams": [], "cap": None}, indent=2) + "\n", encoding="utf-8")
        return 1

    for stream in required + optional:
        is_required = stream in required
        files = sorted((args.root / stream).rglob("*.parquet"))
        if cutoff is not None:
            files = [f for f in files if f.stat().st_mtime >= cutoff]
        n_rows = 0
        versions: set[str] = set()
        bad_files = 0
        for f in files:
            try:
                rows, ver = _segment_stats(f)
                n_rows += rows
                versions.add(ver)
            except Exception as exc:  # corrupt segment -> count, keep going
                bad_files += 1
                print(f"  WARN {stream}: unlesbares Segment {f.name}: {exc}")

        version_ok = (not versions) or versions == {expected_version}
        if not version_ok:
            status = "SCHEMA_MISMATCH"
        elif bad_files:
            status = "CORRUPT_SEGMENTS"
        elif n_rows > 0:
            status = "OK"
        elif is_required:
            status = "NO_DATA"
        else:
            status = "EMPTY_OK"

        failed = status in ("SCHEMA_MISMATCH", "CORRUPT_SEGMENTS") or (
            is_required and status == "NO_DATA"
        )
        overall_pass = overall_pass and not failed
        streams_out.append({
            "stream": stream, "required": is_required, "n_files": len(files),
            "n_rows": n_rows, "schema_versions": sorted(versions),
            "status": status,
        })
        print(f"{stream}: {status} files={len(files)} rows={n_rows} "
              f"schema_version={','.join(sorted(versions)) or '-'} "
              f"(erwartet {expected_version})")

    cap_out = None
    if args.cap_gb is not None:
        total = sum(f.stat().st_size for f in args.root.rglob("*.parquet"))
        used_gb = total / 1024 ** 3
        cap_ok = used_gb <= args.cap_gb
        overall_pass = overall_pass and cap_ok
        cap_out = {"cap_gb": args.cap_gb, "used_gb": round(used_gb, 3), "ok": cap_ok}
        print(f"storage_cap: {'OK' if cap_ok else 'FAIL'} "
              f"used={used_gb:.2f} GB cap={args.cap_gb} GB")

    result = {
        "pass": overall_pass,
        "root": str(args.root),
        "max_age_min": args.max_age_min,
        "expected_schema_version": expected_version,
        "streams": streams_out,
        "cap": cap_out,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"RECORDING-CHECK {'PASS' if overall_pass else 'FAIL'} root={args.root}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never hang the night run with a traceback prompt
        print(f"RECORDING-CHECK ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
