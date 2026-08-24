#!/usr/bin/env python3
"""WP-5 runner: Bybit option-chain quote-spread census.

Usage:
    python scripts/wp5_option_chain_census.py \
        --snapshot BTC=state/wp5_20260824/bybit_btc_option_chain_20260824.json \
        --snapshot ETH=state/wp5_20260824/bybit_eth_option_chain_20260824.json \
        --asof 2026-08-24 --out state/wp5_20260824/wp5_optchain_census.json

The snapshot is whatever ``/v5/market/tickers?category=option&baseCoin=BTC``
returned; a bare ``result.list`` array is accepted, as is the full envelope,
with or without a PowerShell BOM.  Public endpoint, read-only, no keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp5_optchain.census import (  # noqa: E402
    census, load_snapshot,
)


def _fp(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", action="append", required=True,
                    metavar="LABEL=PATH")
    ap.add_argument("--asof", required=True, help="YYYY-MM-DD snapshot date")
    ap.add_argument("--horizon-dte", default="7,14",
                    help="lo,hi day-to-expiry band of the traded horizon")
    ap.add_argument("--leg-delta", default="0.15,0.30",
                    help="lo,hi |delta| band of the strangle legs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    asof = date.fromisoformat(a.asof)
    hz = tuple(int(x) for x in a.horizon_dte.split(","))
    ld = tuple(float(x) for x in a.leg_delta.split(","))

    payload: dict = {
        "wp": "WP-5", "asof": a.asof, "capital_free_core": True,
        "horizon_dte": list(hz), "leg_delta": list(ld),
        "source": "bybit v5 /v5/market/tickers?category=option (public)",
        "symbols": {},
    }
    for spec in a.snapshot:
        label, _, p = spec.partition("=")
        path = Path(p)
        rows = load_snapshot(path, asof)
        if not rows:
            print(f"ERROR: no parseable option rows in {path}", file=sys.stderr)
            return 2
        payload["symbols"][label] = {
            "snapshot_path": str(path),
            "snapshot_sha256": _fp(path),
            **census(rows, horizon=hz, leg_delta=ld),
        }
        print(f"{label}: {len(rows)} symbols parsed from {path}")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
