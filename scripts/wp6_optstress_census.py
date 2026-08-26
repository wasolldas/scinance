#!/usr/bin/env python3
"""WP-6 Runner: Options-Quote-Breite aus dem Harvest-Baum, als Zeitreihe.

Zwei Modi -- IMMER zuerst die Probe:

  # 1) Probe: Was liegt tatsaechlich unter raw/bybit/tickers, und fuehren
  #    die Frames bid/ask?  Kein Zensus ohne bestandene Probe.
  python scripts/wp6_optstress_census.py --base data/harvest \
      --dates 2026-08-19 --probe

  # 2) Zensus ueber das Stress-Fenster (Minuten-Aufloesung):
  python scripts/wp6_optstress_census.py --base data/harvest \
      --dates 2026-08-15..2026-08-23 \
      --out scinance2-impl/state/wp6_20260826

Liest NUR raw/bybit/tickers (read-only), schreibt CSV + Summary-JSON in
--out.  Deterministisch: je (Symbol, Minute) der letzte Frame ueber den
zusammengesetzten Schluessel (ts_exchange_ms, payload_json).
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp5_optchain.census import quantile  # noqa: E402
from bybit_edge.research.wp6_optstress.extract import (  # noqa: E402
    OPTION_SYMBOL_RE, frame_record, minute_stats, unwrap_payload,
)

COINS = ("BTC", "ETH")


def parse_dates(spec: str) -> list[str]:
    if ".." in spec:
        a, b = spec.split("..", 1)
        d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
        if d1 < d0:
            raise SystemExit(f"ERROR: Datumsbereich rueckwaerts: {spec}")
        return [(d0 + timedelta(days=i)).isoformat()
                for i in range((d1 - d0).days + 1)]
    return [date.fromisoformat(spec).isoformat()]


def day_glob(base: Path, day: str) -> str:
    return str(base / "raw" / "bybit" / "tickers" / "symbol=*"
               / f"date={day}" / "*.parquet")


def connect():
    import duckdb
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    return con


def probe(base: Path, days: list[str]) -> int:
    con = connect()
    ok = True
    for day in days:
        g = day_glob(base, day)
        try:
            rows = con.execute(
                "SELECT symbol, count(*) AS n, "
                "  arg_max(payload_json, (ts_exchange_ms, payload_json)) AS pj "
                "FROM read_parquet(?) GROUP BY symbol", [g]).fetchall()
        except Exception as exc:
            print(f"{day}: KEINE DATEN lesbar ({exc})")
            ok = False
            continue
        opts = [(s, n, pj) for s, n, pj in rows if OPTION_SYMBOL_RE.match(s)]
        perps = len(rows) - len(opts)
        print(f"{day}: {len(rows)} Symbole gesamt, davon "
              f"{len(opts)} Options-Symbole, {perps} sonstige")
        if not opts:
            print("  -> Der Strom enthaelt an diesem Tag KEINE Optionen.")
            ok = False
            continue
        s, n, pj = max(opts, key=lambda r: r[1])
        tick = unwrap_payload(pj)
        if tick is None:
            print(f"  -> payload_json von {s} ist NICHT entpackbar. "
                  f"Roh (300 Z.): {pj[:300]}")
            ok = False
            continue
        keys = sorted(tick.keys())
        need = ["bid1Price", "ask1Price", "bid1Iv", "ask1Iv", "delta"]
        have = {k: (k in tick) for k in need}
        print(f"  Beispiel {s} ({n} Frames): Felder = {keys}")
        print(f"  KERNTEST bid/ask/iv/delta: {have}")
        if not all(have.values()):
            print("  -> PFLICHTFELDER FEHLEN. Zensus waere sinnlos; "
                  "erst die Aufzeichnung pruefen.")
            ok = False
    return 0 if ok else 1


def census(base: Path, days: list[str], out_dir: Path,
           horizon: tuple[int, int], leg_delta: tuple[float, float]) -> int:
    con = connect()
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = ["minute_utc", "coin", "n_frames", "n_horizon", "n_legs",
              "leg_w_p50", "leg_w_p75", "leg_w_max", "leg_rel_p50",
              "atm_mark_iv", "under", "n_unquoted_legband"]
    summary: dict = {"wp": "WP-6", "dates": days, "horizon_dte": list(horizon),
                     "leg_delta": list(leg_delta), "days": {},
                     "unparseable_frames": 0}
    csv_path = out_dir / "wp6_minute_spread.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for day in days:
            d = date.fromisoformat(day)
            try:
                rows = con.execute(
                    "SELECT symbol, ts_exchange_ms // 60000 AS minute_idx, "
                    "  arg_max(payload_json, (ts_exchange_ms, payload_json)) "
                    "FROM read_parquet(?) "
                    "WHERE regexp_matches(symbol, "
                    "  '^(BTC|ETH|SOL)-[0-9]{1,2}[A-Z]{3}[0-9]{2}-') "
                    "GROUP BY 1, 2 ORDER BY 2, 1", [day_glob(base, day)]
                ).fetchall()
            except Exception as exc:
                print(f"{day}: nicht lesbar ({exc}) -- Tag uebersprungen",
                      file=sys.stderr)
                summary["days"][day] = {"status": "UNREADABLE"}
                continue
            per_min: dict = collections.defaultdict(
                lambda: collections.defaultdict(list))
            bad = 0
            for sym, midx, pj in rows:
                tick = unwrap_payload(pj)
                rec = frame_record(sym, tick, d) if tick else None
                if rec is None:
                    bad += 1
                    continue
                per_min[midx][sym.split("-", 1)[0]].append(rec)
            summary["unparseable_frames"] += bad
            day_leg_w: dict = collections.defaultdict(list)
            n_rows = 0
            for midx in sorted(per_min):
                iso = datetime.fromtimestamp(midx * 60, tz=timezone.utc
                                             ).strftime("%Y-%m-%dT%H:%M:%SZ")
                for coin in COINS:
                    recs = per_min[midx].get(coin)
                    if not recs:
                        continue
                    st = minute_stats(recs, horizon=horizon,
                                      leg_delta=leg_delta)
                    st.update(minute_utc=iso, coin=coin)
                    w.writerow(st)
                    n_rows += 1
                    if st["leg_w_p50"] is not None:
                        day_leg_w[coin].append(st["leg_w_p50"])
            summary["days"][day] = {
                "status": "OK" if n_rows else "NO_OPTION_FRAMES",
                "minute_rows": n_rows, "unparseable": bad,
                **{f"{c}_leg_w_p50_of_minutes":
                   (round(quantile(day_leg_w[c], .5), 4)
                    if day_leg_w[c] else None) for c in COINS},
                **{f"{c}_leg_w_p95_of_minutes":
                   (round(quantile(day_leg_w[c], .95), 4)
                    if day_leg_w[c] else None) for c in COINS},
            }
            print(f"{day}: {n_rows} Minuten-Zeilen"
                  + (f", {bad} unparsebare Frames" if bad else ""))
    (out_dir / "wp6_summary.json").write_text(
        json.dumps(summary, indent=1), encoding="utf-8")
    print(f"-> {csv_path}\n-> {out_dir / 'wp6_summary.json'}")
    bad_days = [d for d, v in summary["days"].items()
                if v.get("status") != "OK"]
    if bad_days:
        print(f"WARNUNG: {len(bad_days)} Tag(e) ohne verwertbare "
              f"Options-Frames: {bad_days}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Harvest-Wurzel (data/harvest)")
    ap.add_argument("--dates", required=True,
                    help="YYYY-MM-DD oder YYYY-MM-DD..YYYY-MM-DD")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--out", help="Zielverzeichnis (Pflicht ohne --probe)")
    ap.add_argument("--horizon-dte", default="7,14")
    ap.add_argument("--leg-delta", default="0.15,0.30")
    a = ap.parse_args()
    base = Path(a.base)
    days = parse_dates(a.dates)
    if a.probe:
        return probe(base, days)
    if not a.out:
        ap.error("--out ist ohne --probe Pflicht")
    return census(base, days, Path(a.out),
                  tuple(int(x) for x in a.horizon_dte.split(",")),
                  tuple(float(x) for x in a.leg_delta.split(",")))


if __name__ == "__main__":
    raise SystemExit(main())
