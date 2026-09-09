#!/usr/bin/env python3
"""WP-10 Teil A Runner: Praemien-Kohaerenz im Stress (deskriptiv, KEIN Gate).

Three modes -- ALWAYS probe first:

  # 1) Probe: which series/fields are available, coverage.
  python scripts/wp10_coherence.py --probe --base data/harvest --cache-dir data/barcache

  # 2) Stress-Kanon: write both STRESS_REL (DEC-55) and STRESS_ABS
  #    (DEC-56) fixtures from the WP-0 bar cache (append-only if a fixture
  #    already exists at --stress-canon-out).
  python scripts/wp10_coherence.py --stress-canon --cache-dir data/barcache --start ... --end ...

  # 3) Run: build the premium-proxy series, load/build the stress canon,
  #    compute the Spearman coherence matrix + portfolio-null table, write
  #    JSON + Markdown + DEC-53 artefacts.
  python scripts/wp10_coherence.py --run --base data/harvest --cache-dir data/barcache

``--source {harvest,backfill}`` (default harvest, DEC-62/WP-10(A2)):
backfill mode replaces the funding/IV-RV loaders with the nachgeladenen
Tagesserien (WP-7 panel_1d.funding_sum or direct public REST; REST-DVOL
minus WP-0 bar-cache RV) so the coherence matrix can reach the STRESS_ABS
canon start (2020-05) -- basis-proxy stays harvest-only. Every backfill
series is compared against its harvest-tree counterpart on the shared
overlap ("Bestand vs. Backfill", DEC-60 lesson) -- see ``--panel-base``/
``--dvol-rest-dir``. ``--source harvest`` (default) is UNCHANGED from the
original WP-10(A) driver -- existing runs stay byte-identical.

NEVER writes under data/harvest (every writer in this package refuses,
loudly). rc != 0 on a probe failure or a missing DEC-53 artefact
(``report.ReportError`` -> "KEIN VERDIKT").
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp9_dvol import harvest_close as hc  # noqa: E402
from bybit_edge.research.wp9_dvol import rest_client as dvrc  # noqa: E402
from bybit_edge.research.wp9_dvol.harvest_close import (  # noqa: E402
    discover_dvol_symbol, discover_harvest_days, list_dvol_symbol_dirs)
from bybit_edge.research.wp10_coherence import coherence as co  # noqa: E402
from bybit_edge.research.wp10_coherence import comparison as cmp  # noqa: E402
from bybit_edge.research.wp10_coherence import portfolio_null as pn  # noqa: E402
from bybit_edge.research.wp10_coherence import report as rp  # noqa: E402
from bybit_edge.research.wp10_coherence import rv as _rv  # noqa: E402
from bybit_edge.research.wp10_coherence import series as sr  # noqa: E402
from bybit_edge.research.wp10_coherence import stress_canon as sc  # noqa: E402

FUNDING_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT")
IVRV_CURRENCIES = ("BTC", "ETH")
BASIS_SYMBOLS = ("BTCUSDT", "ETHUSDT")
BAR_SYMBOLS = ("BTCUSDT", "ETHUSDT")
BAR_EXCHANGE = "bybit"


def _now_utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def connect_duckdb():
    import duckdb
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    return con


def _bar_symbol_for_currency(cur: str) -> str:
    return f"{cur}USDT"


def _discover_cache_range(cache_dir: str, exchange: str, symbols: list[str]) -> tuple[str, str] | None:
    """Min/max cached day across ``symbols`` -- used to default --start/--end
    to "whatever the WP-0 bar cache actually covers" when not given."""
    days: set[str] = set()
    for s in symbols:
        root = Path(cache_dir) / "bars_1min" / f"exchange={exchange}" / f"symbol={s}"
        if root.is_dir():
            days |= {p.name[len("date="):] for p in root.glob("date=*") if p.is_dir()}
    return (min(days), max(days)) if days else None


def _resolve_range(a: argparse.Namespace) -> tuple[str, str] | None:
    if a.start and a.end:
        return a.start, a.end
    discovered = _discover_cache_range(a.cache_dir, BAR_EXCHANGE, list(BAR_SYMBOLS))
    if discovered is None:
        return None
    start, end = discovered
    return a.start or start, a.end or end


def _dvol_symbol_for_currency(a: argparse.Namespace, cur: str) -> str:
    """The dvol harvest partition symbol for ``cur``: an explicit
    ``--dvol-symbol-template`` override when given, else auto-discovered
    from ``raw/deribit/dvol/symbol=*`` on disk (``{cur}_DVOL`` was a
    [sek] guess that turned out wrong against a real harvest tree --
    never assumed any more). Raises ``ValueError`` (caller decides how to
    react) when discovery finds zero or more than one match."""
    if a.dvol_symbol_template:
        return a.dvol_symbol_template.format(cur=cur)
    return discover_dvol_symbol(a.base, cur)


# ---------------------------------------------------------------- --probe

def cmd_probe_backfill(a: argparse.Namespace) -> int:
    """``--source backfill`` probe (DEC-62/WP-10(A2)): dvol_rest parquet +
    WP-0 bar-cache presence (Pflicht, no fallback -- flips rc) and
    panel_1d presence (informational only -- funding ALWAYS has a working
    fallback, the direct public REST fetch, so a missing panel_1d never
    fails the probe, only names which source a later --run will use)."""
    con = connect_duckdb()
    ok = True
    try:
        print("=== Funding Backfill (panel_1d.funding_sum bevorzugt, sonst direkter REST-Abruf) ===")
        panel_root = Path(a.panel_base) if a.panel_base else None
        panel_present = bool(panel_root and panel_root.is_dir())
        for sym in a.funding_symbols.split(","):
            src = "panel_1d (falls Partitionen fuer den Jahresbereich vollstaendig sind)" \
                if panel_present else "direkter oeffentlicher REST-Abruf (funding/history, gedrosselt)"
            print(f"  {sym}: panel_base={a.panel_base!r} vorhanden={panel_present} -> Quelle: {src}")
        print("=== IV-RV Backfill (REST-DVOL-Parquet DEC-61 + WP-0-Bar-Cache) [Pflicht] ===")
        for cur in a.ivrv_currencies.split(","):
            rest_path = Path(a.dvol_rest_dir) / f"{cur}_1D.parquet"
            present = rest_path.is_file()
            print(f"  {cur}: dvol_rest_path={rest_path} vorhanden={present}")
            if not present:
                print(f"    -> fehlt; erst scripts/wp9_dvol_backfill.py --fetch ausfuehren")
                ok = False
            bar_symbol = _bar_symbol_for_currency(cur)
            bars_probe = Path(a.cache_dir) / "bars_1min" / f"exchange={BAR_EXCHANGE}" / f"symbol={bar_symbol}"
            n_bar_days = len(list(bars_probe.glob("date=*"))) if bars_probe.is_dir() else 0
            print(f"    bar_symbol={bar_symbol}, cached_bar_days={n_bar_days}")
            if n_bar_days == 0:
                print(f"    -> kein WP-0-Bar-Cache fuer {bar_symbol} unter {a.cache_dir}")
                ok = False

        print("=== Perp-Basis-Proxy (bybit/tickers, optional, bleibt Harvest-only) ===")
        for sym in a.basis_symbols.split(","):
            p = sr.probe_perp_basis(con, a.base, sym)
            print(f"  {sym}: {p}")
            if p["status"] != "OK":
                print(f"    -> optionale Serie uebersprungen (soweit vorhanden): {p['status']}")
    finally:
        con.close()

    if not ok:
        print("PROBE FEHLGESCHLAGEN -- kein --stress-canon/--run ohne bestandene Pflichtserien-Probe "
              "(REST-DVOL/DEC-61 + WP-0-Bar-Cache). Fehlendes panel_1d wirkt sich NIE auf den rc aus "
              "(Funding faellt automatisch auf den direkten REST-Abruf zurueck). Die optionale "
              "Perp-Basis-Probe wirkt sich ebenfalls NIE auf den rc aus.")
    return 0 if ok else 1


def cmd_probe(a: argparse.Namespace) -> int:
    if a.source == "backfill":
        return cmd_probe_backfill(a)
    con = connect_duckdb()
    ok = True  # Pflicht series only (funding, dvol/IV-RV) -- basis is optional, see below.
    try:
        print("=== Funding (rest.fundingRate) [Pflicht] ===")
        for sym in a.funding_symbols.split(","):
            p = sr.probe_funding(con, a.base, sym)
            print(f"  {sym}: {p}")
            if p["status"] == "UNREADABLE" or p.get("n_missing_fields", 0) > 0:
                ok = False

        print("=== IV-RV (deribit/dvol + WP-0 bar cache) [Pflicht] ===")
        dvol_dirs = list_dvol_symbol_dirs(a.base)
        print(f"  raw/deribit/dvol/symbol=* gefunden unter {a.base}: {dvol_dirs}")
        for cur in a.ivrv_currencies.split(","):
            try:
                dvol_symbol = _dvol_symbol_for_currency(a, cur)
            except ValueError as exc:
                print(f"  {cur}: {exc}")
                ok = False
                continue
            days = discover_harvest_days(a.base, dvol_symbol)
            print(f"  {cur}: dvol_symbol={dvol_symbol}, harvest_days={len(days)}")
            if not days:
                print(f"    -> keine Harvest-Tage fuer {dvol_symbol} "
                      f"(gefundene symbol=* Verzeichnisse: {dvol_dirs})")
                ok = False
            bar_symbol = _bar_symbol_for_currency(cur)
            bars_probe = Path(a.cache_dir) / "bars_1min" / f"exchange={BAR_EXCHANGE}" / f"symbol={bar_symbol}"
            n_bar_days = len(list(bars_probe.glob("date=*"))) if bars_probe.is_dir() else 0
            print(f"    bar_symbol={bar_symbol}, cached_bar_days={n_bar_days}")
            if n_bar_days == 0:
                print(f"    -> kein WP-0-Bar-Cache fuer {bar_symbol} unter {a.cache_dir}")
                ok = False

        print("=== Perp-Basis-Proxy (bybit/tickers, optional) ===")
        for sym in a.basis_symbols.split(","):
            p = sr.probe_perp_basis(con, a.base, sym)
            print(f"  {sym}: {p}")
            if p["status"] != "OK":
                # Optional series: NEVER flips rc, even on UNREADABLE -- a
                # broken/absent OPTIONAL proxy stream must not block
                # --stress-canon/--run, only the two Pflicht series above do.
                print(f"    -> optionale Serie uebersprungen (soweit vorhanden): {p['status']}")
    finally:
        con.close()

    if not ok:
        print("PROBE FEHLGESCHLAGEN -- kein --stress-canon/--run ohne bestandene Pflichtserien-Probe "
              "(Funding, IV-RV/dvol). Die optionale Perp-Basis-Probe wirkt sich NIE auf den rc aus.")
    return 0 if ok else 1


# ---------------------------------------------------------- --stress-canon

def cmd_stress_canon(a: argparse.Namespace) -> int:
    rng = _resolve_range(a)
    if rng is None:
        print(f"KEIN WP-0-Bar-Cache unter {a.cache_dir} fuer {BAR_SYMBOLS} gefunden -- "
              "Stress-Kanon kann nicht gebaut werden.", file=sys.stderr)
        return 1
    start, end = rng
    panel = sc.rv_panel(a.cache_dir, BAR_EXCHANGE, list(BAR_SYMBOLS), start, end)
    n_total = sum(len(v) for v in panel.values())
    if n_total == 0:
        print("KEIN Bar-Cache-RV gefunden -- Stress-Kanon kann nicht gebaut werden "
              f"(cache_dir={a.cache_dir}, symbols={BAR_SYMBOLS}, {start}..{end}).",
              file=sys.stderr)
        return 1

    out_dir = Path(a.stress_canon_out)
    abs_fixture = sc.build_stress_abs(panel)
    rel_fixture = sc.build_stress_rel(panel)
    try:
        written_abs = sc.write_fixture(abs_fixture, out_dir / "stress_abs.json")
        written_rel = sc.write_fixture(rel_fixture, out_dir / "stress_rel.json")
    except sc.AppendOnlyViolationError as exc:
        print(f"STRESS-KANON APPEND-ONLY-VERLETZUNG -- {exc}", file=sys.stderr)
        return 1

    print(f"STRESS_ABS: n_days={written_abs['n_days']}, n_episodes={written_abs['n_episodes']}, "
          f"sha256={written_abs['sha256']} -> {out_dir / 'stress_abs.json'}")
    print(f"STRESS_REL: n_days={written_rel['n_days']}, n_episodes={written_rel['n_episodes']}, "
          f"sha256={written_rel['sha256']} -> {out_dir / 'stress_rel.json'}")
    for name in sc.STRESS_ABS_NAMED_DATES:
        present = name in written_abs["days"]
        print(f"  Referenz-Tag {name} in STRESS_ABS: {'ja' if present else 'NEIN -- unerwartet'}")
        if not present:
            return 1
    return 0


# ---------------------------------------------------------------- --run

def cmd_run_backfill(a: argparse.Namespace, con: Any,
                     eff_start: str, eff_end: str) -> tuple[list[dict], list[dict]]:
    """``--source backfill`` (DEC-62/WP-10(A2)): funding + IV-RV loaded
    from the nachgeladenen Tagesserien, basis-proxy unchanged (harvest-
    only). Every backfill series also loads its harvest-tree counterpart
    and produces a "Bestand vs. Backfill" comparison row (DEC-60 lesson)
    -- absent/short Bestand is reported, never raised."""
    series_list: list[dict] = []
    comparison: list[dict] = []

    for sym in a.funding_symbols.split(","):
        s = sr.funding_daily_cashflow_backfill(sym, eff_start, eff_end, panel_base=a.panel_base)
        series_list.append(s)
        print(f"funding_backfill {sym}: status={s['status']} coverage={s['coverage']} "
              f"source={s['provenance'].get('source')}")
        hs = sr.funding_daily_cashflow(con, a.base, sym, start=a.start, end=a.end)
        print(f"  Bestand {sym}: status={hs['status']} coverage={hs['coverage']}")
        comparison.append(cmp.compare_value_series(f"funding_{sym}", s, hs))

    for cur in a.ivrv_currencies.split(","):
        rest_path = Path(a.dvol_rest_dir) / f"{cur}_1D.parquet"
        if not rest_path.is_file():
            print(f"{cur}: REST-DVOL-Parquet fehlt (DEC-61) -- {rest_path} "
                  "(erst scripts/wp9_dvol_backfill.py --fetch ausfuehren)", file=sys.stderr)
            continue
        rest_rows = dvrc.read_rest_parquet(rest_path)
        days = [r["date"] for r in rest_rows if eff_start <= r["date"] <= eff_end]
        s = sr.iv_rv_diff_series_backfill(
            a.cache_dir, currency=cur, bar_exchange=BAR_EXCHANGE,
            bar_symbol=_bar_symbol_for_currency(cur), dvol_rest_dir=a.dvol_rest_dir, days=days)
        series_list.append(s)
        print(f"iv_rv_backfill {cur}: status={s['status']} coverage={s['coverage']}")

        backfill_dvol_by_day = {r["date"]: r["close"] for r in rest_rows}
        harvest_dvol_by_day: dict[str, float] = {}
        try:
            dvol_symbol = _dvol_symbol_for_currency(a, cur)
            hdays = [d for d in discover_harvest_days(a.base, dvol_symbol) if d in set(days)]
            if hdays:
                harvest_rows = hc.daily_close(con, a.base, dvol_symbol, hdays)
                harvest_dvol_by_day = {r["date"]: r["close"] for r in harvest_rows if "close" in r}
        except ValueError as exc:
            print(f"{cur}: Bestands-DVOL fuer den Vergleich nicht auffindbar -- {exc}",
                  file=sys.stderr)
        comparison.append(cmp.compare_dvol_close(f"ivrv_{cur}", backfill_dvol_by_day,
                                                  harvest_dvol_by_day))

    for sym in a.basis_symbols.split(","):
        s = sr.perp_basis_proxy_series(con, a.base, sym, start=a.start, end=a.end)
        series_list.append(s)
        print(f"basis {sym} (Harvest-only, im Backfill-Modus unveraendert): "
              f"status={s['status']} coverage={s['coverage']}")

    return series_list, comparison


def cmd_run(a: argparse.Namespace) -> int:
    comparison: list[dict] | None = None
    if a.source == "backfill":
        bar_rng_early = _resolve_range(a)
        eff_start = a.start or (bar_rng_early[0] if bar_rng_early else None)
        eff_end = a.end or (bar_rng_early[1] if bar_rng_early else None)
        if eff_start is None or eff_end is None:
            print("KEIN --start/--end und kein Bar-Cache zum Ableiten des Backfill-Zeitraums -- "
                  "erst --stress-canon ausfuehren (fuellt den Bar-Cache-Bereich) oder --start/--end "
                  "explizit angeben.", file=sys.stderr)
            return 1

    con = connect_duckdb()
    try:
        if a.source == "backfill":
            series_list, comparison = cmd_run_backfill(a, con, eff_start, eff_end)
        else:
            series_list = []
            for sym in a.funding_symbols.split(","):
                s = sr.funding_daily_cashflow(con, a.base, sym, start=a.start, end=a.end)
                series_list.append(s)
                print(f"funding {sym}: status={s['status']} coverage={s['coverage']}")

            # day list for IV-RV: whatever dvol harvest days are on disk, bounded by --start/--end.
            for cur in a.ivrv_currencies.split(","):
                try:
                    dvol_symbol = _dvol_symbol_for_currency(a, cur)
                except ValueError as exc:
                    print(f"{cur}: {exc}", file=sys.stderr)
                    print(f"  raw/deribit/dvol/symbol=* gefunden unter {a.base}: "
                          f"{list_dvol_symbol_dirs(a.base)}", file=sys.stderr)
                    continue
                days = [d for d in discover_harvest_days(a.base, dvol_symbol)
                        if (not a.start or d >= a.start) and (not a.end or d <= a.end)]
                s = sr.iv_rv_diff_series(con, a.base, a.cache_dir, dvol_symbol=dvol_symbol,
                                         bar_exchange=BAR_EXCHANGE, bar_symbol=_bar_symbol_for_currency(cur),
                                         days=days)
                series_list.append(s)
                print(f"iv_rv {cur}: status={s['status']} coverage={s['coverage']}")

            for sym in a.basis_symbols.split(","):
                s = sr.perp_basis_proxy_series(con, a.base, sym, start=a.start, end=a.end)
                series_list.append(s)
                print(f"basis {sym}: status={s['status']} coverage={s['coverage']}")
    finally:
        con.close()

    usable = [s for s in series_list if s["status"] == "OK" and s["coverage"]["n_days"] > 0]
    if len(usable) < 2:
        print(f"Zu wenige nutzbare Serien ({len(usable)}) fuer eine Kohaerenz-Matrix.",
              file=sys.stderr)
        return 1

    stress_canon_dir = Path(a.stress_canon_out)
    abs_path = stress_canon_dir / "stress_abs.json"
    bar_rng = _resolve_range(a)
    if abs_path.is_file():
        abs_fixture = sc.read_fixture(abs_path)
    elif bar_rng is not None:
        panel = sc.rv_panel(a.cache_dir, BAR_EXCHANGE, list(BAR_SYMBOLS), *bar_rng)
        abs_fixture = sc.finalize_fixture(sc.build_stress_abs(panel))
    else:
        print(f"KEIN Stress-Kanon vorhanden ({abs_path}) und kein Bar-Cache zum Neubauen -- "
              "erst --stress-canon ausfuehren.", file=sys.stderr)
        return 1
    stress_days = set(abs_fixture["days"])

    coherence_result = co.correlation_matrix(usable, stress_days, abs_fixture["episodes"],
                                             n_bootstrap=a.n_bootstrap, seed=a.seed)

    returns = (_rv.panel_returns(a.cache_dir, BAR_EXCHANGE, list(BAR_SYMBOLS), *bar_rng)
              if bar_rng is not None else np.empty(0))
    try:
        pnull_table = pn.portfolio_null_table(returns, n_bootstrap=a.n_bootstrap, seed=a.seed)
        pnull_selection = pn.selection_ceiling(returns, seed=a.seed)
    except pn.PortfolioNullError as exc:
        print(f"Portfolio-Nulleffekt uebersprungen (zu wenig Return-Historie): {exc}",
              file=sys.stderr)
        pnull_table = {"ks": [], "seed": a.seed, "results": {}}
        pnull_selection = None
    pnull = {"table": pnull_table, "selection_ceiling": pnull_selection}

    default_dir_name = f"wp10a2_{_now_utc_date()}" if a.source == "backfill" else f"wp10a_{_now_utc_date()}"
    out_dir = Path(a.out) if a.out else Path("scinance3-impl/state") / default_dir_name
    try:
        result = rp.build_report(
            series_list=usable, coherence_result=coherence_result,
            stress_canon={"STRESS_ABS": abs_fixture}, portfolio_null=pnull,
            out_dir=out_dir, seed=a.seed,
            source=(a.source if a.source == "backfill" else None),
            comparison=comparison)
    except rp.ReportError as exc:
        print(f"KEIN VERDIKT -- {exc}", file=sys.stderr)
        return 1

    print(f"-> {result['summary_path']}\n-> {result['markdown_path']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="data/harvest", help="Harvest-Wurzel (read-only, NIE beschrieben)")
    ap.add_argument("--cache-dir", default="data/barcache", help="WP-0-Bar-Cache-Wurzel")
    ap.add_argument("--funding-symbols", default=",".join(FUNDING_SYMBOLS))
    ap.add_argument("--ivrv-currencies", default=",".join(IVRV_CURRENCIES))
    ap.add_argument("--dvol-symbol-template", default=None,
                    help="Expliziter Override fuer den dvol-Harvest-Symbolnamen "
                         "je Waehrung (z.B. '{cur}_DVOL'). OHNE diese Option "
                         "wird der Symbolname automatisch unter "
                         "raw/deribit/dvol/symbol=* entdeckt (discover_dvol_symbol).")
    ap.add_argument("--basis-symbols", default=",".join(BASIS_SYMBOLS))
    ap.add_argument("--source", choices=["harvest", "backfill"], default="harvest",
                    help="harvest (Default, unveraendert): Serien nur aus dem Harvest-Baum. "
                         "backfill (DEC-62/WP-10(A2)): Funding aus panel_1d.funding_sum/direktem "
                         "REST-Abruf, IV-RV aus dem REST-DVOL-Backfill (DEC-61) minus WP-0-Bar-Cache-"
                         "RV; Basis-Proxy bleibt Harvest-only. Fuegt eine Bestand-vs-Backfill-"
                         "Vergleichszeile hinzu (DEC-60-Lehre).")
    ap.add_argument("--panel-base", default="data/panel_1d",
                    help="WP-7 panel_1d-Wurzel (nur --source backfill; bevorzugte Funding-Quelle, "
                         "wenn die Jahres-Partitionen vollstaendig sind)")
    ap.add_argument("--dvol-rest-dir", default="data/dvol_rest",
                    help="WP-9 REST-DVOL-Parquet-Verzeichnis (nur --source backfill; DEC-61)")
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--seed", type=int, default=pn.DEFAULT_SEED)
    ap.add_argument("--n-bootstrap", type=int, default=pn.N_BOOTSTRAP)
    ap.add_argument("--stress-canon-out", default="scinance3-impl/state/wp10_stress_canon")
    ap.add_argument("--out", help="Zielverzeichnis fuer --run (Default scinance3-impl/state/wp10a_<heute>)")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--stress-canon", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()

    modes = [a.probe, a.stress_canon, a.run]
    if sum(bool(m) for m in modes) != 1:
        ap.error("genau EINER von --probe/--stress-canon/--run ist Pflicht")
    if a.probe:
        return cmd_probe(a)
    if a.stress_canon:
        return cmd_stress_canon(a)
    return cmd_run(a)


if __name__ == "__main__":
    raise SystemExit(main())
