#!/usr/bin/env python3
"""WP-9 Runner: Deribit DVOL REST backfill + harvest cross-validation.

Three modes -- ALWAYS probe first:

  # 1) Probe: field layout [sek] + depth (F1), 3 anchor days per currency.
  #    NEVER run this against the real network from THIS sandbox (egress
  #    to api.deribit.com is blocked here) -- use --fixture for an offline
  #    dry run, or run unmodified on a machine with real network access.
  python scripts/wp9_dvol_backfill.py --probe

  # 2) Fetch: full-history backfill -> data/dvol_rest/<CUR>_1D.parquet
  #    + manifest JSON with SHA-256 fingerprint. NEVER data/harvest.
  python scripts/wp9_dvol_backfill.py --fetch

  # 3) Crossval: REST vs. harvested deribit/dvol stream (F2) -> report
  #    JSON + Markdown under scinance3-impl/state/wp9_<date>/.
  python scripts/wp9_dvol_backfill.py --crossval --base data/harvest

Offline/test runs of ANY mode: pass ``--fixture <file.json>`` -- a JSON
object ``{"BTC": [<page>, ...], "ETH": [<page>, ...]}`` where each page is
either a raw response string or a dict to be serialised, consumed by
``rest_client.fixture_fetcher`` (see that module's docstring). This is how
this sandbox exercises the REST client at all.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp9_dvol import crossval as cv  # noqa: E402
from bybit_edge.research.wp9_dvol import harvest_close as hc  # noqa: E402
from bybit_edge.research.wp9_dvol import rest_client as rc  # noqa: E402

CURRENCIES = ("BTC", "ETH")

#: F1 anchor days (spec section 1): a recent day (must have data -- loud
#: fail otherwise), a mid-history day, and a day just before the ~2021-04
#: expectation [sek] (absence there is the EXPECTED, informative result,
#: never a failure -- that IS the depth measurement).
_ANCHOR_MID = "2022-06-15"
_ANCHOR_EARLY = "2021-03-01"


def _now_utc_date() -> date:
    return datetime.now(timezone.utc).date()


def connect_duckdb():
    import duckdb
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    return con


def _load_fixture_fetchers(path: str) -> dict[str, object]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return {cur: rc.fixture_fetcher(list(pages)) for cur, pages in obj.items()}


# ---------------------------------------------------------------- --probe

def cmd_probe(a: argparse.Namespace) -> int:
    fetchers = _load_fixture_fetchers(a.fixture) if a.fixture else {}
    today = _now_utc_date()
    anchors = [
        ("recent", (today.isoformat()), True),
        ("mid", _ANCHOR_MID, False),
        ("early(F1)", _ANCHOR_EARLY, False),
    ]
    ok = True
    for cur in a.currencies.split(","):
        fetcher = fetchers.get(cur)
        print(f"=== {cur} ===")
        for label, day, must_have_data in anchors:
            start_ms, end_ms = rc.day_bounds_ms(day)
            try:
                res = rc.probe_call(cur, start_ms, end_ms, fetcher=fetcher)
            except rc.DvolFieldLayoutError as exc:
                print(f"  {label} {day}: LAUT GESCHEITERT -- {exc}")
                ok = False
                continue
            except (OSError, ValueError) as exc:
                print(f"  {label} {day}: Netzwerk/Aufruf-Fehler -- {exc}")
                ok = False
                continue
            n = len(res["rows"])
            print(f"  {label} {day}: {n} Zeile(n), raw[:300]={res['raw_head']!r}")
            if n:
                print(f"    Beispiel-Felder: {res['rows'][0]}")
            if must_have_data and n == 0:
                print(f"    -> UNERWARTET LEER am {label}-Tag ({day}); "
                      "Feldlayout oder Erreichbarkeit pruefen.")
                ok = False
    if not ok:
        print("PROBE FEHLGESCHLAGEN -- kein Fetch/Crossval ohne bestandene Probe.")
    return 0 if ok else 1


# ---------------------------------------------------------------- --fetch

def cmd_fetch(a: argparse.Namespace) -> int:
    fetchers = _load_fixture_fetchers(a.fixture) if a.fixture else {}
    start_ms, _ = rc.day_bounds_ms(a.start)
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    out_dir = Path(a.rest_dir)
    ok = True
    for cur in a.currencies.split(","):
        fetcher = fetchers.get(cur)
        try:
            fetched = rc.fetch_volatility_index(cur, start_ms, end_ms, fetcher=fetcher)
        except rc.DvolFieldLayoutError as exc:
            print(f"{cur}: LAUT GESCHEITERT -- {exc}", file=sys.stderr)
            ok = False
            continue
        out_path = out_dir / f"{cur}_1D.parquet"
        written = rc.write_rest_parquet(fetched["rows"], out_path)
        daily = rc.rows_to_daily(fetched["rows"])
        manifest = {
            "currency": cur, "resolution": fetched["resolution"],
            "start_requested_ms": fetched["start_requested_ms"],
            "end_requested_ms": fetched["end_requested_ms"],
            "n_rows": written["n_rows"],
            "first_date": daily[0]["date"] if daily else None,
            "last_date": daily[-1]["date"] if daily else None,
            "n_pages": fetched["n_pages"],
            "raw_response_sha256": fetched["raw_sha256"],
            "sha256_parquet": written["sha256_bytes"],
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "field_layout_note":
                "[sek] result.data positional [ts_ms, open, high, low, close]",
        }
        manifest_path = out_dir / f"{cur}_1D.manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"{cur}: {written['n_rows']} Zeilen -> {out_path}")
        print(f"  {manifest['first_date']}..{manifest['last_date']} "
              f"(F1-Rohbefund), sha256_parquet={written['sha256_bytes'][:16]}...")
        print(f"  -> {manifest_path}")
    return 0 if ok else 1


# ------------------------------------------------------------- --crossval

def _read_manifest_first_date(rest_dir: Path, cur: str) -> str | None:
    p = rest_dir / f"{cur}_1D.manifest.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("first_date")
    except (ValueError, OSError):
        return None


def cmd_crossval(a: argparse.Namespace) -> int:
    base = Path(a.base)
    rest_dir = Path(a.rest_dir)
    out_dir = Path(a.out) if a.out else (
        Path("scinance3-impl/state") / f"wp9_{_now_utc_date().isoformat()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    con = connect_duckdb()
    results: dict[str, dict] = {}
    try:
        for cur in a.currencies.split(","):
            rest_path = rest_dir / f"{cur}_1D.parquet"
            if not rest_path.is_file():
                print(f"{cur}: REST-Parquet fehlt ({rest_path}) -- erst --fetch "
                      "ausfuehren.", file=sys.stderr)
                results[cur] = {"status": "REST_MISSING"}
                continue
            rest_rows = rc.read_rest_parquet(rest_path)
            rest_daily = rc.rows_to_daily(rest_rows)
            symbol = a.symbol_template.format(cur=cur)
            days = hc.discover_harvest_days(base, symbol)
            if not days:
                print(f"{cur}: keine Harvest-Tage unter symbol={symbol} "
                      "gefunden.", file=sys.stderr)
                results[cur] = {"status": "NO_HARVEST_DAYS", "symbol": symbol}
                continue
            try:
                harvest_rows = hc.daily_close(con, base, symbol, days)
            except hc.DvolFieldLayoutError as exc:
                print(f"{cur}: LAUT GESCHEITERT (Harvest-Feldlayout) -- {exc}",
                      file=sys.stderr)
                results[cur] = {"status": "HARVEST_FIELD_LAYOUT_ERROR",
                                "symbol": symbol, "detail": str(exc)}
                continue
            harvest_ok = [r for r in harvest_rows if "close" in r]
            verdict = cv.evaluate(rest_daily, harvest_ok, seed=a.seed)

            diff_csv = out_dir / f"wp9_{cur}_diff_series.csv"
            with diff_csv.open("w", newline="", encoding="utf-8") as fh:
                import csv
                w = csv.DictWriter(fh, fieldnames=["date", "rest_close",
                                                    "harvest_close", "diff"])
                w.writeheader()
                w.writerows(verdict["daily_differences"])

            results[cur] = {
                "status": "OK", "symbol": symbol,
                "n_harvest_days_discovered": len(days),
                "n_overlap_days": verdict["n_overlap_days"],
                "distribution": verdict["distribution"],
                "bootstrap": verdict["bootstrap"],
                "half_width": verdict["half_width"],
                "reachable": verdict["reachable"],
                "verdict": verdict["verdict"], "reason": verdict["reason"],
                "materiality_band_volpts": verdict["materiality_band_volpts"],
                "diff_series_csv": str(diff_csv),
                "f1_first_rest_date": _read_manifest_first_date(rest_dir, cur),
            }
            print(f"{cur}: n_overlap={verdict['n_overlap_days']} "
                  f"verdict={verdict['verdict']!r} -> {diff_csv}")
    finally:
        con.close()

    summary = {
        "wp": "WP-9", "materiality_band_volpts": cv.MATERIALITY_BAND_VOLPTS,
        "block_len_days": cv.BLOCK_LEN_DAYS, "n_bootstrap": cv.N_BOOTSTRAP,
        "seed": a.seed, "results": results,
    }
    summary_path = out_dir / "wp9_summary.json"
    summary_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")

    md = _render_markdown(results, a.seed)
    md_path = out_dir / "wp9_report.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"-> {summary_path}\n-> {md_path}")
    bad = [c for c, r in results.items() if r.get("status") != "OK"]
    return 1 if bad else 0


def _render_markdown(results: dict[str, dict], seed: int) -> str:
    lines = ["# WP-9 DVOL: F1-Tiefe / F2-Austauschbarkeit", ""]
    for cur, r in results.items():
        lines.append(f"## {cur}")
        if r.get("status") != "OK":
            lines.append(f"Status: {r.get('status')} -- {r.get('detail', '')}")
            lines.append("")
            continue
        lines.append(f"F1 (Tiefe, aus --fetch-Manifest): erster REST-Tag = "
                      f"{r.get('f1_first_rest_date')}")
        lines.append(f"F2 (Austauschbarkeit): Ueberlappungstage n = "
                      f"{r['n_overlap_days']}, Befund = **{r['verdict']}** "
                      f"({r['reason']})")
        d = r["distribution"]
        lines.append(f"- Tagesdifferenz p5/p50/p95: {d['p5']}/{d['p50']}/{d['p95']} "
                      f"(SD={d['sd']}, Autokorrelation(lag1)={d['autocorr_lag1']})")
        if r["bootstrap"]:
            b = r["bootstrap"]
            lines.append(f"- Bootstrap: mean={b['mean']:.4f}, 95%-CI="
                          f"[{b['ci_lo']:.4f}, {b['ci_hi']:.4f}], "
                          f"block_len={b['block_len']}, n_bootstrap={b['n_bootstrap']}, "
                          f"seed={b['seed']}")
        lines.append(f"- Materialitaets-Band: +-{r['materiality_band_volpts']} Vol-Punkte, "
                      f"erreichbar={r['reachable']}")
        lines.append(f"- Tagesdifferenz-Serie: {r['diff_series_csv']}")
        lines.append("")
    lines.append(f"(Bootstrap-Seed dieses Laufs: {seed}, DEC-53.)")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--currencies", default=",".join(CURRENCIES))
    ap.add_argument("--base", default="data/harvest",
                    help="Harvest-Wurzel (read-only, NIE beschrieben)")
    ap.add_argument("--rest-dir", default="data/dvol_rest")
    ap.add_argument("--symbol-template", default="{cur}_DVOL",
                    help="[sek] Harvest-Partitions-Symbolname je Waehrung "
                         "-- am Bestand verifizieren")
    ap.add_argument("--out", help="Zielverzeichnis fuer --crossval "
                                   "(Default scinance3-impl/state/wp9_<heute>)")
    ap.add_argument("--start", default="2019-01-01",
                    help="frueheste angeforderte REST-Grenze fuer --fetch")
    ap.add_argument("--seed", type=int, default=cv.DEFAULT_SEED)
    ap.add_argument("--fixture",
                    help="JSON-Datei mit kanonischen Antwort-Seiten je Waehrung "
                         "statt echtem HTTP-Call (Offline-/Testlauf; siehe "
                         "rest_client.fixture_fetcher). In diesem Sandbox ist "
                         "dies der EINZIGE Weg, --probe/--fetch auszufuehren.")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--crossval", action="store_true")
    a = ap.parse_args()

    modes = [a.probe, a.fetch, a.crossval]
    if sum(bool(m) for m in modes) != 1:
        ap.error("genau EINER von --probe/--fetch/--crossval ist Pflicht")
    if a.probe:
        return cmd_probe(a)
    if a.fetch:
        return cmd_fetch(a)
    return cmd_crossval(a)


if __name__ == "__main__":
    raise SystemExit(main())
