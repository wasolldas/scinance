#!/usr/bin/env python3
"""WP-5: Zeitreihe der Options-Quote-Breite aus gesammelten Snapshots.

Liest den Baum, den ``handoff_local/snap_bybit_optchain.ps1`` schreibt

    <root>/<COIN>/<COIN>_<yyyyMMdd_HHmmss>Z.json

und erzeugt EINE Zeile je (Snapshot, Coin) mit der Quote-Breite im
Strangle-Bein-Band, dem ATM-IV-Niveau und dem Basiswert.

Damit ist die Frage beantwortbar, die ein einzelner Snapshot prinzipiell
nicht beantworten kann: **verbreitert sich die Quote genau dann, wenn eine
Vol-Strategie handeln will** -- also wenn das IV-Niveau springt oder der
Basiswert sich schnell bewegt.

Wichtig: DTE wird gegen den ZEITSTEMPEL DES SNAPSHOTS gerechnet, nicht
gegen heute.  Sonst wandert das Bein-Band durch die Historie.

Beispiel:
    python scripts/wp5_snap_timeseries.py \
        --root data/optchain_snaps --out data/optchain_snaps/timeseries.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp5_optchain.census import (  # noqa: E402
    load_snapshot, quantile,
)

STAMP = re.compile(r"_(\d{8})_(\d{6})Z?\.json$")

FIELDS = [
    "ts_utc", "coin", "n_symbols", "underlying", "atm_mark_iv",
    "n_legs", "leg_w_p25", "leg_w_p50", "leg_w_p75",
    "leg_rel_p50", "leg_oi_p50", "leg_bidsz_p50",
    "atm_n", "atm_w_p50", "front_dte",
]


def parse_stamp(path: Path) -> datetime | None:
    m = STAMP.search(path.name)
    if not m:
        return None
    return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").replace(
        tzinfo=timezone.utc)


def snapshot_row(path: Path, coin: str, horizon: tuple[int, int],
                 leg_delta: tuple[float, float]) -> dict | None:
    ts = parse_stamp(path)
    if ts is None:
        return None
    rows = load_snapshot(path, ts.date())
    if not rows:
        return None
    hz = [r for r in rows if horizon[0] <= r["dte"] <= horizon[1]]
    legs = [r for r in hz if r["quoted_iv"] and r.get("delta") is not None
            and leg_delta[0] <= abs(r["delta"]) <= leg_delta[1]]
    atm = [r for r in hz if r["quoted_iv"] and r.get("delta") is not None
           and 0.35 <= abs(r["delta"]) <= 0.65]
    lw = [r["iv_width_pts"] for r in legs]
    fut = [r["dte"] for r in rows if r["dte"] >= 0]

    def qq(xs, p, nd=4):
        v = quantile(xs, p)
        return None if v is None else round(v, nd)

    return {
        "ts_utc": ts.isoformat(),
        "coin": coin,
        "n_symbols": len(rows),
        "underlying": qq([r["under"] for r in rows if r.get("under")], .5, 2),
        # ATM-Mark-IV als Vol-Niveau-Proxy: markIv ist quotenunabhaengig und
        # damit KEIN Zirkelschluss mit der gemessenen Breite.
        "atm_mark_iv": qq([r["mark_iv"] for r in atm if r.get("mark_iv")], .5),
        "n_legs": len(legs),
        "leg_w_p25": qq(lw, .25), "leg_w_p50": qq(lw, .50),
        "leg_w_p75": qq(lw, .75),
        "leg_rel_p50": qq([r["rel_spread"] for r in legs
                           if r.get("rel_spread") is not None], .50),
        "leg_oi_p50": qq([r["oi"] for r in legs], .50, 2),
        "leg_bidsz_p50": qq([r["bid_sz"] for r in legs], .50, 2),
        "atm_n": len(atm),
        "atm_w_p50": qq([r["iv_width_pts"] for r in atm], .50),
        "front_dte": min(fut) if fut else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--horizon-dte", default="7,14")
    ap.add_argument("--leg-delta", default="0.15,0.30")
    a = ap.parse_args()

    hz = tuple(int(x) for x in a.horizon_dte.split(","))
    ld = tuple(float(x) for x in a.leg_delta.split(","))

    root = Path(a.root)
    if not root.is_dir():
        print(f"ERROR: {root} ist kein Verzeichnis", file=sys.stderr)
        return 2

    rows, skipped = [], 0
    for coin_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for f in sorted(coin_dir.glob("*.json")):
            try:
                r = snapshot_row(f, coin_dir.name, hz, ld)
            except Exception as exc:            # ein kaputter Snapshot
                print(f"WARN: {f.name}: {exc}", file=sys.stderr)
                skipped += 1
                continue
            if r is None:
                skipped += 1
                continue
            rows.append(r)

    if not rows:
        print("ERROR: kein einziger auswertbarer Snapshot gefunden",
              file=sys.stderr)
        return 2

    rows.sort(key=lambda r: (r["ts_utc"], r["coin"]))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    per = {}
    for r in rows:
        per.setdefault(r["coin"], []).append(r)
    print(f"{len(rows)} Zeilen -> {out}"
          + (f"  ({skipped} uebersprungen)" if skipped else ""))
    for coin, rs in per.items():
        ws = [r["leg_w_p50"] for r in rs if r["leg_w_p50"] is not None]
        print(f"  {coin}: {len(rs)} Snapshots  {rs[0]['ts_utc']} .. "
              f"{rs[-1]['ts_utc']}  Bein-Breite p50 median={quantile(ws,.5)} "
              f"p90={quantile(ws,.9)}")
    if len(rows) < 100:
        print("\nHINWEIS: unter ~100 Snapshots je Coin traegt die "
              "Stress-Frage noch kein Urteil. Weiter sammeln.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
