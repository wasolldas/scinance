#!/usr/bin/env python3
"""WP-7 Runner: Universums-Zensus (Klasse-W-Feasibility).

Vier Modi, IMMER in dieser Reihenfolge:

  # 1) Inhaltsprobe auf den vorhandenen bybit/tickers-Strom (read-only,
  #    Bestandsdaten) -- kein Zensus ohne bestandene/gewuerdigte Probe:
  python scripts/wp7_universe_census.py --probe-tickers \
      --harvest-base data/harvest --dates 2026-08-19..2026-08-20

  # 2) Fetch: instruments-info + Tages-Klines + Funding-Historie ->
  #    panel_1d (NIE unter data/harvest; braucht echtes Netz -- in dieser
  #    Sandbox nicht erreichbar, siehe bybit_rest.py-Docstring). Listing-
  #    Datum kommt aus instruments-info's launchTime (Nacharbeit #3);
  #    funding_n/funding_sum aus /v5/market/funding/history (Nacharbeit #1):
  python scripts/wp7_universe_census.py --fetch \
      --panel-base data/panel_1d --start-year 2021 --end-year 2026

  # 3) Zensus: K, SD_null(IC_t), N_eff (Ledoit-Wolf, deskriptiv), sigma_xs,
  #    sigma_LS, PERP_SPREAD_BP, rho(BTC,ETH) (30-min, aus dem WP-0-Bar-
  #    Cache), Befund B1..B5 -> --out (JSON+MD):
  python scripts/wp7_universe_census.py --census \
      --panel-base data/panel_1d --bar-cache-dir data/barcache \
      --corr-start 2026-01-01 --corr-end 2026-06-30 \
      --out scinance3-impl/state/wp7_YYYYMMDD

  # 4) Provenienz: 1%-Zufallsstichprobe eingefrorener Partitionen neu
  #    gezogen und gegen die Fingerprints geprueft:
  python scripts/wp7_universe_census.py --reverify --panel-base data/panel_1d
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp7_universe import (  # noqa: E402
    bybit_rest, panel_store, spread_probe,
)


def parse_dates(spec: str) -> list[str]:
    if ".." in spec:
        a, b = spec.split("..", 1)
        d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
        if d1 < d0:
            raise SystemExit(f"ERROR: Datumsbereich rueckwaerts: {spec}")
        return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
    return [date.fromisoformat(spec).isoformat()]


def cmd_probe_tickers(a: argparse.Namespace) -> int:
    days = parse_dates(a.dates)
    result = spread_probe.probe_harvest_tickers(Path(a.harvest_base), days)
    for day, info in result["days"].items():
        print(f"{day}: {info.get('status')}", end="")
        if info.get("fields_missing"):
            print(f" -- FEHLENDE FELDER: {info['fields_missing']}")
        elif info.get("status") == "OK":
            print(f" -- Beispiel {info['sample_symbol']} ({info['n_perp_symbols']} Perp-Symbole)")
        else:
            print()
    if result["ok"]:
        print("-> Inhaltsprobe bestanden: Spread-Zensus auf Bestandsdaten moeglich, "
              "kein REST-Fallback noetig.")
    else:
        print("-> Inhaltsprobe NICHT bestanden fuer mindestens einen Tag -- "
              "REST-Fallback (bybit_rest.fetch_tickers) noetig oder Aufzeichnung pruefen.")
    return 0 if result["ok"] else 1


def cmd_fetch(a: argparse.Namespace) -> int:
    print("=== instruments-info ===")
    inst = bybit_rest.fetch_instruments(category=a.category)
    print(f"{inst['n_rows']} Symbole, status-Werte: {inst['statuses']}")
    non_trading = [r for r in inst["rows"] if r["status"] != "Trading"]
    print(f"{len(non_trading)} nicht-Trading Zeilen (B3-relevant).")
    launch_by_symbol = {r["symbol"]: r.get("launchTime") for r in inst["rows"]}

    symbols = (a.symbols.split(",") if a.symbols
               else [r["symbol"] for r in inst["rows"]])
    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    from datetime import datetime, timezone
    as_of = datetime.now(timezone.utc).date()
    for symbol in symbols:
        # Nacharbeit #3: listing_date from the real launchTime, not year
        # start -- a symbol with no usable launchTime (pre-launchTime-era
        # fixture/instrument) falls back to year-1's year start, LOUDLY.
        try:
            listing = panel_store.listing_date_from_launch_time(launch_by_symbol.get(symbol))
        except panel_store.PanelStoreError as exc:
            listing = date(a.start_year, 1, 1)
            print(f"{symbol}: kein launchTime ({exc}) -- Fallback "
                  f"listing_date={listing.isoformat()}", file=sys.stderr)

        for year in range(a.start_year, a.end_year + 1):
            y0 = date(year, 1, 1)
            y1 = min(date(year, 12, 31), as_of)
            if y1 < y0:
                continue
            start_ms = int(datetime(y0.year, y0.month, y0.day, tzinfo=timezone.utc).timestamp() * 1000)
            end_ms = int(datetime(y1.year, y1.month, y1.day, tzinfo=timezone.utc).timestamp() * 1000) + 86_399_999
            try:
                kl = bybit_rest.fetch_kline_symbol(symbol, start_ms, end_ms, category=a.category)
            except Exception as exc:  # noqa: BLE001
                print(f"{symbol}/{year}: FEHLER (kline) {exc}", file=sys.stderr)
                panel_store.mark_failed(manifest, symbol, year, str(exc))
                continue
            rows = [{"start_ms": r["start_ms"], "open": r["open"], "high": r["high"],
                     "low": r["low"], "close": r["close"], "volume": r["volume"],
                     "turnover": r["turnover"]} for r in kl["rows"]]

            # Nacharbeit #1: funding/history, same range/throttle, merged
            # into daily funding_n/funding_sum before the partition is written.
            try:
                fh = bybit_rest.fetch_funding_history(symbol, start_ms, end_ms, category=a.category)
                rows = panel_store.merge_funding_daily(rows, fh["rows"])
            except Exception as exc:  # noqa: BLE001
                print(f"{symbol}/{year}: FEHLER (funding/history) {exc} -- "
                      "funding_n/funding_sum bleiben None fuer dieses Jahr",
                      file=sys.stderr)

            frozen = year < as_of.year
            res = panel_store.write_year_partition(
                a.panel_base, manifest, symbol, year, rows,
                listing_date=listing, as_of_date=as_of, frozen=frozen)
            print(f"{symbol}/{year}: {res['status']} ({res['n_rows']}/{res['expected_days']})")
    return 0


def cmd_census(a: argparse.Namespace) -> int:
    from bybit_edge.research.wp7_universe import pair_corr as pair_corr_mod
    from bybit_edge.research.wp7_universe import report as report_mod
    counts = panel_store.manifest_status_counts(Path(a.panel_base) / "panel_manifest.sqlite")
    print(f"Manifest-Status: {counts}")
    print("Der volle K/SD_null/N_eff/sigma_xs/sigma_LS/PERP_SPREAD_BP-Zensus "
          "braucht ein gebautes panel_1d (--fetch) auf dem Nutzer-PC; siehe "
          "pit_universe.py / null_ic.py / stats.py fuer die Bausteine, die dieser "
          "Treiber hier nur noch zu einem Report zusammensetzt.")
    if counts.get("PARTIAL") or counts.get("FAILED"):
        print("WARNUNG: PARTIAL/FAILED-Partitionen vorhanden -- kein "
              "urteilstragender Lauf ohne require_all_done().", file=sys.stderr)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "manifest_status.json").write_text(json.dumps(counts, indent=1))

    # rho(BTC,ETH), 30-min -- needs ONLY the existing WP-0 bar cache (no
    # network, no panel_1d), so it is fully wired here even in a sandbox
    # without --fetch access. "--census" reports it per PRD 4.1 section 1.
    if a.bar_cache_dir and a.corr_start and a.corr_end:
        try:
            pc = pair_corr_mod.compute_pair_correlation(
                a.bar_cache_dir, "bybit", "BTCUSDT", "ETHUSDT",
                a.corr_start, a.corr_end, seed=a.corr_seed)
            pair_corr_mod.write_artifacts(a.out, pc)
            print(f"rho(BTC,ETH) 30-min: Pearson={pc['pearson']['point']:.4f} "
                  f"Spearman={pc['spearman']['point']:.4f} "
                  f"(n={pc['n_aligned_buckets']}, seed={a.corr_seed})")
        except Exception as exc:  # noqa: BLE001 -- bar cache may not exist yet
            pc = None
            print(f"rho(BTC,ETH): nicht berechenbar ({exc}) -- WP-0-Bar-Cache "
                  "fehlt oder deckt den Bereich nicht ab.", file=sys.stderr)
    else:
        pc = None

    print(f"N_eff wird, wenn berichtet, immer als '{report_mod.N_EFF_LABEL}' "
          "etikettiert (deskriptiv, kein Urteil) -- siehe report.assemble_report.")
    return 0


def cmd_reverify(a: argparse.Namespace) -> int:
    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    result = panel_store.reverify_sample(a.panel_base, manifest, seed=a.seed)
    print(json.dumps(result, indent=1))
    if result["n_mismatch"]:
        print(f"ALARM: {result['n_mismatch']} Fingerprint-Abweichung(en)!", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-tickers", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--reverify", action="store_true")
    ap.add_argument("--harvest-base", default="data/harvest")
    ap.add_argument("--dates", default="")
    ap.add_argument("--panel-base", default="data/panel_1d")
    ap.add_argument("--category", default="linear")
    ap.add_argument("--symbols", default="")
    ap.add_argument("--start-year", type=int, default=2021)
    ap.add_argument("--end-year", type=int, default=date.today().year)
    ap.add_argument("--out", default="")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--bar-cache-dir", default="data/barcache",
                    help="WP-0-Bar-Cache fuer rho(BTC,ETH) (--census)")
    ap.add_argument("--corr-start", default="")
    ap.add_argument("--corr-end", default="")
    ap.add_argument("--corr-seed", type=int, default=53)
    a = ap.parse_args()

    modes = [a.probe_tickers, a.fetch, a.census, a.reverify]
    if sum(bool(m) for m in modes) != 1:
        ap.error("genau EINEN Modus waehlen: --probe-tickers | --fetch | --census | --reverify")

    if a.probe_tickers:
        if not a.dates:
            ap.error("--dates ist mit --probe-tickers Pflicht")
        return cmd_probe_tickers(a)
    if a.fetch:
        return cmd_fetch(a)
    if a.census:
        if not a.out:
            ap.error("--out ist mit --census Pflicht")
        return cmd_census(a)
    return cmd_reverify(a)


if __name__ == "__main__":
    raise SystemExit(main())
