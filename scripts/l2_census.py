#!/usr/bin/env python3
"""WP-1 L2 pre-flight census — READ-ONLY discovery, no extraction (Welle 6 §3).

Hard precondition for registering L2-TILT (H-22 candidate): the data
inventory found bybit L2 history far deeper than documented (BTC 961 days,
74 % coverage) but with a suspected format break (historic ``orderbook.500``
SNAPSHOT vs. live ``orderbook.1000`` DELTA). Lane C's byte arithmetic says
pure 500-level snapshots would mean ~17 TB for BTC alone — implausible — so
the likely reality is snapshot+delta. THE RULE (synthesis §3): if this census
comes back against the delta reading, L2-TILT is NOT registered. Not one
byte of feature extraction happens before this census.

What it measures, per symbol on a day sample (every Nth day + first/last):

  * which ``orderbook*`` stream directories exist at all (discovery, not
    assumption),
  * per day: row count, payload bytes, topic distribution, ``$.type``
    distribution (snapshot/delta/...),
  * book depth: min/median/max of ``len($.data.b)`` and ``len($.data.a)``
    per (topic, type) — the actual level count, not the topic's label,
  * sequence integrity: per (topic) the count of non-increasing update-id
    steps (``$.data.u``, fallback ``$.u``) in exchange-ts order — a delta
    stream is only usable if update ids are near-gapless,
  * the regime timeline: first/last sampled day of every (topic, type)
    combination, so the 500->1000 break date is bracketed.

Output: JSON + Markdown into --out-dir. Every per-day step is wrapped in
try/except — a corrupt day is reported, never fatal (T-runner rule).

KAPITALFREI read-only diagnostics. No write access to the harvester tree.
Exit codes: 0 = census written · 1 = fatal error · 2 = no orderbook data.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

DEPTH_B = ("COALESCE(json_array_length(payload_json,'$.data.b'),"
           " json_array_length(payload_json,'$.b'))")
DEPTH_A = ("COALESCE(json_array_length(payload_json,'$.data.a'),"
           " json_array_length(payload_json,'$.a'))")
UPD_ID = ("COALESCE(TRY_CAST(json_extract_string(payload_json,'$.data.u') AS BIGINT),"
          " TRY_CAST(json_extract_string(payload_json,'$.u') AS BIGINT))")
TOPIC = ("COALESCE(json_extract_string(payload_json,'$.topic'), topic,"
         " '<none>')")
RTYPE = "COALESCE(json_extract_string(payload_json,'$.type'), '<none>')"


def _census_day_sql(glob: str) -> str:
    return f"""
        SELECT {TOPIC} AS topic,
               {RTYPE} AS rtype,
               count(*)                            AS n_rows,
               sum(strlen(payload_json))           AS payload_bytes,
               min({DEPTH_B})                      AS depth_b_min,
               CAST(median({DEPTH_B}) AS BIGINT)   AS depth_b_med,
               max({DEPTH_B})                      AS depth_b_max,
               min({DEPTH_A})                      AS depth_a_min,
               CAST(median({DEPTH_A}) AS BIGINT)   AS depth_a_med,
               max({DEPTH_A})                      AS depth_a_max,
               count(*) FILTER (WHERE {UPD_ID} IS NOT NULL) AS n_with_update_id
        FROM read_parquet('{glob}', union_by_name=1)
        GROUP BY 1, 2
        ORDER BY 1, 2
    """


def _seq_breaks_sql(glob: str) -> str:
    return f"""
        WITH u AS (
            SELECT {TOPIC} AS topic, ts_exchange_ms AS ts, {UPD_ID} AS uid
            FROM read_parquet('{glob}', union_by_name=1)
            WHERE {UPD_ID} IS NOT NULL
        )
        SELECT topic,
               count(*) AS n,
               count(*) FILTER (WHERE uid <= lag_uid) AS n_non_increasing
        FROM (SELECT topic, uid,
                     lag(uid) OVER (PARTITION BY topic ORDER BY ts, uid) AS lag_uid
              FROM u)
        GROUP BY 1
    """


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="WP-1 L2 pre-flight census (read-only, KAPITALFREI).")
    p.add_argument("--base-dir", default="data/harvest")
    p.add_argument("--exchange", default="bybit")
    p.add_argument("--symbols", default="BTCUSDT,ETHUSDT",
                   help="Inventory: only BTC/ETH have deep L2 history.")
    p.add_argument("--sample-every", type=int, default=14,
                   help="Sample every Nth date partition (plus first/last).")
    p.add_argument("--out-dir", default=".")
    args = p.parse_args(argv)

    base = Path(args.base_dir)
    symbols = tuple(s.strip() for s in args.symbols.split(",") if s.strip())
    raw = base / "raw" / args.exchange
    streams = sorted(d.name for d in raw.glob("orderbook*") if d.is_dir())
    if not streams:
        print(f"[l2census] no orderbook* stream under {raw} — nothing to census.",
              file=sys.stderr, flush=True)
        return 2
    print(f"[l2census] streams discovered: {streams}", file=sys.stderr, flush=True)

    import duckdb
    con = duckdb.connect()
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_dir": str(base), "exchange": args.exchange,
        "sample_every": args.sample_every,
        "streams_discovered": streams, "symbols": {},
    }

    for sym in symbols:
        sym_out: dict = {"streams": {}}
        for stream in streams:
            sdir = raw / stream / f"symbol={sym}"
            days = sorted(d.name.split("=", 1)[1] for d in sdir.glob("date=*"))
            if not days:
                continue
            idx = sorted({0, len(days) - 1,
                          *range(0, len(days), max(1, args.sample_every))})
            sampled = [days[i] for i in idx]
            day_rows, errors = [], []
            t0 = time.time()
            for day in sampled:
                glob = (sdir / f"date={day}" / "*.parquet").as_posix()
                try:
                    groups = con.execute(_census_day_sql(glob)).fetchall()
                    seq = {r[0]: {"n": r[1], "n_non_increasing": r[2]}
                           for r in con.execute(_seq_breaks_sql(glob)).fetchall()}
                except Exception as exc:  # noqa: BLE001 — census must survive
                    errors.append({"day": day, "error": str(exc)[:300]})
                    continue
                for g in groups:
                    day_rows.append({
                        "day": day, "topic": g[0], "type": g[1],
                        "n_rows": g[2], "payload_bytes": int(g[3] or 0),
                        "depth_b": [g[4], g[5], g[6]],
                        "depth_a": [g[7], g[8], g[9]],
                        "n_with_update_id": g[10],
                        "seq": seq.get(g[0]),
                    })
            # regime timeline per (topic, type)
            regimes: dict = {}
            for r in day_rows:
                key = f"{r['topic']} - {r['type']}"  # no '|': key lands in MD table cells
                reg = regimes.setdefault(key, {
                    "first_sampled_day": r["day"], "last_sampled_day": r["day"],
                    "days_sampled": 0, "rows": 0, "bytes": 0,
                    "depth_b_min": None, "depth_b_max": None,
                    "seq_non_increasing_total": 0, "seq_checked_total": 0})
                reg["last_sampled_day"] = max(reg["last_sampled_day"], r["day"])
                reg["first_sampled_day"] = min(reg["first_sampled_day"], r["day"])
                reg["days_sampled"] += 1
                reg["rows"] += r["n_rows"]
                reg["bytes"] += r["payload_bytes"]
                if r["depth_b"][0] is not None:
                    reg["depth_b_min"] = (r["depth_b"][0] if reg["depth_b_min"] is None
                                          else min(reg["depth_b_min"], r["depth_b"][0]))
                    reg["depth_b_max"] = (r["depth_b"][2] if reg["depth_b_max"] is None
                                          else max(reg["depth_b_max"], r["depth_b"][2]))
                if r["seq"]:
                    reg["seq_non_increasing_total"] += r["seq"]["n_non_increasing"]
                    reg["seq_checked_total"] += r["seq"]["n"]
            sym_out["streams"][stream] = {
                "days_total": len(days), "first_day": days[0], "last_day": days[-1],
                "days_sampled": len(sampled), "seconds": round(time.time() - t0, 1),
                "regimes": regimes, "day_rows": day_rows, "errors": errors,
            }
            print(f"[l2census] {sym}/{stream}: {len(days)} days, "
                  f"{len(sampled)} sampled, {len(errors)} errors, "
                  f"regimes={list(regimes)}", file=sys.stderr, flush=True)
        report["symbols"][sym] = sym_out

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "l2_census.json").write_text(json.dumps(report, indent=2),
                                        encoding="utf-8")
    md = _render_md(report)
    (out / "l2_census.md").write_text(md, encoding="utf-8")
    print(f"[l2census] wrote {out / 'l2_census.json'}", file=sys.stderr, flush=True)
    return 0


def _render_md(report: dict) -> str:
    L = ["# WP-1 · L2-Pre-Flight-Zensus (read-only, KAPITALFREI)", "",
         f"- **Erzeugt:** {report['generated_at']} (UTC)",
         f"- **Streams entdeckt:** {', '.join(report['streams_discovered'])}",
         f"- **Sampling:** jeder {report['sample_every']}. Tag + erster/letzter", "",
         "> Entscheidungsregel (Synthese §3): Faellt der Zensus gegen die "
         "Snapshot+Delta-Lesart aus, wird L2-TILT NICHT registriert.", ""]
    for sym, s in report["symbols"].items():
        L.append(f"## {sym}")
        L.append("")
        if not s["streams"]:
            L.append("*keine orderbook-Partitionen*")
            L.append("")
            continue
        for stream, st in s["streams"].items():
            L.append(f"### `{stream}` — {st['days_total']} Tage "
                     f"({st['first_day']}..{st['last_day']}), "
                     f"{st['days_sampled']} gesampelt, {len(st['errors'])} Fehler")
            L.append("")
            L.append("| Regime (topic · type) | Tage (gesampelt) | erster..letzter | Zeilen | MB | Tiefe b min..max | Seq-Brueche / geprueft |")
            L.append("|---|---:|---|---:|---:|---|---:|")
            for key, r in st["regimes"].items():
                L.append(f"| `{key}` | {r['days_sampled']} | "
                         f"{r['first_sampled_day']}..{r['last_sampled_day']} | "
                         f"{r['rows']} | {r['bytes'] / 1e6:.1f} | "
                         f"{r['depth_b_min']}..{r['depth_b_max']} | "
                         f"{r['seq_non_increasing_total']} / {r['seq_checked_total']} |")
            L.append("")
            if st["errors"]:
                L.append("**Fehlertage (nicht fatal):** "
                         + ", ".join(e["day"] for e in st["errors"]))
                L.append("")
    L.append("*Erzeugt von `scripts/l2_census.py`. Kein Byte Extraktion — nur "
             "Zaehlung/Discovery. Die L2-TILT-Registrierungsentscheidung faellt "
             "der Orchestrator gegen dieses Dokument.*")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
