"""H-27 RV source: completeness of the union panel BTCUSDT/ETHUSDT daily candles (coverage only).

Reports per symbol: first/last day, missing UTC days in 2021-03-01..2026-07-31, duplicate days,
start_ms alignment to 00:00 UTC, null/non-positive closes (count only).  No return, no price
level, no volatility is computed or printed (result blindness: KONTAMINATION.md 5).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pyarrow.parquet as pq

PANEL = Path(__file__).resolve().parent.parent / "panel" / "panel_1d"
LO, HI = "2021-03-01", "2026-07-31"


def load(sym: str) -> list[tuple[int, float]]:
    rows = []
    for state in ("frozen", "open"):
        base = PANEL / state / "source=bybit" / "category=linear" / f"symbol={sym}"
        if not base.is_dir():
            continue
        for f in sorted(base.glob("year=*/part.parquet")):
            t = pq.ParquetFile(f).read(columns=["start_ms", "close"])
            rows += list(zip(t.column("start_ms").to_pylist(), t.column("close").to_pylist()))
    return rows


def main() -> None:
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        rows = load(sym)
        days = [datetime.fromtimestamp(ms / 1000, tz=timezone.utc) for ms, _ in rows]
        iso = [d.date().isoformat() for d in days]
        misaligned = sum(1 for d in days if (d.hour, d.minute, d.second) != (0, 0, 0))
        bad_close = sum(1 for _, c in rows if c is None or not (c > 0))
        d0, d1 = date.fromisoformat(LO), date.fromisoformat(HI)
        want = [(d0 + timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)]
        have = set(iso)
        missing = [d for d in want if d not in have]
        out[sym] = {"n_rows": len(rows), "first_day": min(iso), "last_day": max(iso),
                    "duplicate_days": len(iso) - len(have), "start_ms_not_midnight": misaligned,
                    "nonpositive_or_null_close": bad_close,
                    "missing_days_in_range": len(missing), "missing_head": missing[:20]}
    print(json.dumps(out, indent=1))
    (Path(__file__).resolve().parent / "panel_coverage.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
