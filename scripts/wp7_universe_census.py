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
import math
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
    n_skipped = 0
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
            frozen = year < as_of.year
            # Resume: a repeated/interrupted --fetch must never fail on its
            # own frozen DONE partitions (they are immutable AND complete)
            # -- skip them without network; rebuild only PARTIAL/FAILED
            # frozen years (the sole sanctioned overwrite of a frozen file).
            action = panel_store.resume_action(a.panel_base, manifest, symbol, year, frozen=frozen)
            if action == "SKIP":
                n_skipped += 1
                continue
            allow_overwrite = action == "REBUILD"
            if allow_overwrite:
                print(f"{symbol}/{year}: eingefrorene Partition unvollstaendig "
                      "(PARTIAL/FAILED) -- wird neu gezogen (audited rebuild)")
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

            res = panel_store.write_year_partition(
                a.panel_base, manifest, symbol, year, rows,
                listing_date=listing, as_of_date=as_of, frozen=frozen,
                allow_overwrite=allow_overwrite)
            print(f"{symbol}/{year}: {res['status']} ({res['n_rows']}/{res['expected_days']})")
    if n_skipped:
        print(f"Resume: {n_skipped} eingefrorene DONE/EMPTY-Partitionen "
              "uebersprungen (unveraendert, kein Netz).")
    return 0


def cmd_census(a: argparse.Namespace) -> int:  # noqa: C901 -- one linear pipeline, staged prints
    from bybit_edge.config import FEE_TAKER
    from bybit_edge.research.wp7_universe import null_ic, panel_load
    from bybit_edge.research.wp7_universe import pair_corr as pair_corr_mod
    from bybit_edge.research.wp7_universe import pit_universe, report as report_mod, stats

    def log(msg: str) -> None:
        print(msg, file=sys.stderr)

    manifest = Path(a.panel_base) / "panel_manifest.sqlite"
    if not manifest.is_file():
        log(f"FEHLER: kein Manifest unter {manifest} -- --fetch zuerst ausfuehren.")
        return 1
    counts = panel_store.manifest_status_counts(manifest)
    log(f"[1/10] Manifest-Status: {counts}")
    partial_or_failed = counts.get("PARTIAL", 0) + counts.get("FAILED", 0)
    if partial_or_failed and not a.allow_partial:
        log("WARNUNG: PARTIAL/FAILED-Partitionen vorhanden -- kein urteilstragender "
            "Lauf ohne --allow-partial (siehe panel_store.require_all_done).")

    as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
    seed = a.seed if a.seed is not None else 53
    judgement_bearing = not (partial_or_failed and a.allow_partial)

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest_status.json").write_text(json.dumps(counts, indent=1))

    log("[2/10] Panel laden (panel_1d -> Tages-Arrays)")
    symbols = panel_load.load_panel_symbols(manifest)
    try:
        panel = panel_load.load_panel(
            a.panel_base, manifest, year_start=a.start_year, year_end=a.end_year,
            as_of=as_of, symbols=symbols, allow_partial=a.allow_partial)
    except (panel_store.PanelStoreError, panel_load.PanelLoadError) as exc:
        log(f"FEHLER (loud fail): {exc}")
        return 1
    log(f"  {len(panel['symbols'])} Symbole, {len(panel['dates'])} Tage, "
        f"{panel['n_partitions_used']} Partitionen gelesen.")

    range_fp = panel_load.combined_range_fingerprint(
        a.panel_base, panel["symbols"], a.start_year, a.end_year, as_of=as_of)

    log("[3/10] Woechentliche Renditen + PIT-Alive-Maske")
    weekly = panel_load.weekly_returns_and_mask(panel)
    returns, alive, weeks = weekly["returns"], weekly["alive"], weekly["weeks"]
    n_weeks = len(weeks)
    k_full = pit_universe.k_per_week(alive)
    k_summary = panel_load.k_per_week_summary(alive, weeks)
    log(f"  {n_weeks} Wochen ({weeks[0]}..{weeks[-1]}), K min/median/max = "
        f"{k_summary['min']}/{k_summary['median']}/{k_summary['max']}")
    sensitivity = {}
    for mw in pit_universe.SENSITIVITY_MIN_WEEKS:
        alive_s = pit_universe.pit_alive_mask(weekly["first_week"], weekly["last_week"],
                                               n_weeks, min_weeks_history=mw)
        sensitivity[f"min_weeks_{mw}"] = panel_load.k_per_week_summary(alive_s, weeks)

    log("[4/10] SD_null (1.000 Permutationen je Woche, Fenster W=52/W=104)")
    w_pw = min(n_weeks, stats.W_PER_WINDOW)
    w_pooled = min(n_weeks, stats.W_POOLED)
    sd_null_pw = null_ic.permutation_null_sd(
        returns[-w_pw:], alive[-w_pw:], week_labels=weeks[-w_pw:], seed=seed)
    sd_null_pooled = null_ic.permutation_null_sd(
        returns[-w_pooled:], alive[-w_pooled:], week_labels=weeks[-w_pooled:], seed=seed)
    k_available = int(k_summary["median"])
    b1_b2 = report_mod.evaluate_b1_b2(sd_null_pw["sd_null"], sd_null_pooled["sd_null"], k_available)
    log(f"  {b1_b2['finding']} (K verfuegbar={k_available}, "
        f"SD_null je Fenster={sd_null_pw['sd_null']:.5f}, gepoolt={sd_null_pooled['sd_null']:.5f})")

    log("[5/10] Momentum-IC-Wochenserie (DEC-53-Artefakt, pre-registriertes Signal)")
    signal = panel_load.momentum_signal(returns, trail_win=4)
    ic_series = pit_universe.weekly_ic_series(signal[:-1], returns[1:], alive[:-1])

    log("[6/10] Instruments-Info (B3, oeffentlicher Endpunkt)")
    inst = bybit_rest.fetch_instruments(category=a.category)
    non_trading = [r for r in inst["rows"] if r["status"] != "Trading"]
    delisted_symbols = sorted({r["symbol"] for r in non_trading})
    panel_symbol_set = set(panel["symbols"])
    checked = [s for s in delisted_symbols if s in panel_symbol_set]
    with_kline = sum(
        1 for s in checked
        if any((panel_store.manifest_get(manifest, s, y) or {}).get("n_rows", 0) > 0
               for y in range(a.start_year, a.end_year + 1)))
    b3 = report_mod.evaluate_b3(inst["statuses"], with_kline, len(checked))
    log(f"  B3 triggered={b3['triggered']} (delistet geprueft={len(checked)}, mit Kline={with_kline})")
    funding_interval_reported: dict[str, int] = {}
    for r in inst["rows"]:
        fi = r.get("fundingInterval")
        if fi is not None:
            key = f"{fi}min"
            funding_interval_reported[key] = funding_interval_reported.get(key, 0) + 1

    log("[7/10] sigma_xs / sigma_LS / B4 (Kostenkonstante bybit_edge.config.FEE_TAKER)")
    sigma_xs = stats.sigma_xs_summary(returns, alive)
    sigma_ls = stats.sigma_ls_series(returns, alive, seed=seed)
    cost_bps_rt = 2.0 * FEE_TAKER * 10_000.0  # round-trip taker fee (PRD B.3 / B.1: "11 bp Wand")
    sigma_xs_bps_median = (sigma_xs["median"] * 10_000.0 if sigma_xs["median"] is not None
                            else float("nan"))
    b4 = report_mod.evaluate_b4(sigma_xs_bps_median, cost_bps=cost_bps_rt)
    log(f"  B4 triggered={b4['triggered']} (sigma_xs={sigma_xs_bps_median:.2f} bp, "
        f"Kosten={cost_bps_rt:.2f} bp Taker-RT)")

    log("[8/10] PERP_SPREAD_BP Dezil-Zensus (Inhaltsprobe zuerst, C.8)")
    spread_dates = parse_dates(a.dates) if a.dates else []
    if spread_dates:
        probe = spread_probe.probe_harvest_tickers(Path(a.harvest_base), spread_dates)
        if probe["ok"]:
            snapshot = spread_probe.perp_snapshot_from_harvest(Path(a.harvest_base), spread_dates[-1])
            spread_source = f"Bestandsdaten (data/harvest/raw/bybit/tickers, {spread_dates[-1]})"
        else:
            log("  Inhaltsprobe NICHT bestanden -- REST-Fallback (bybit_rest.fetch_tickers).")
            snapshot = spread_probe.perp_snapshot_from_rest(category=a.category)
            spread_source = "REST-Fallback (bybit_rest.fetch_tickers, ein Call; Inhaltsprobe fehlgeschlagen)"
    else:
        log("  Kein --dates angegeben -- REST-Fallback (bybit_rest.fetch_tickers).")
        snapshot = spread_probe.perp_snapshot_from_rest(category=a.category)
        spread_source = "REST-Fallback (bybit_rest.fetch_tickers, ein Call; kein --dates)"
    spread_census = spread_probe.decile_spread_census(snapshot)
    b5 = report_mod.evaluate_b5(spread_census["deciles"])

    log("[9/10] N_eff (Ledoit-Wolf), DEC-59-Totzonen-/Intervall-Zensus, Delisting-Kohorten")
    neff_full = stats.n_eff(returns, alive)
    stress_info = panel_load.stress_weeks(
        Path("scinance3-impl/state/wp10_stress_canon/stress_abs.json"), weeks)
    if stress_info["available"] and stress_info["n_stress_weeks_in_panel"] >= 2:
        idx = stress_info["week_indices"]
        neff_stress = stats.n_eff(returns[idx], alive[idx])
    else:
        neff_stress = {"n_eff": float("nan"), "n_symbols_balanced": 0, "inv_n_eff": None}

    deadzone = panel_load.funding_deadzone_census(panel)
    funding_autocorr = panel_load.funding_autocorrelation(panel)
    cohorts = panel_load.delisting_cohorts(weekly, as_of_week=pit_universe.iso_week_start(as_of).isoformat())

    pc = None
    if a.bar_cache_dir and a.corr_start and a.corr_end:
        try:
            pc = pair_corr_mod.compute_pair_correlation(
                a.bar_cache_dir, "bybit", "BTCUSDT", "ETHUSDT",
                a.corr_start, a.corr_end, seed=a.corr_seed)
            pc_art = pair_corr_mod.write_artifacts(out_dir, pc)
            log(f"  rho(BTC,ETH) 30-min: Pearson={pc['pearson']['point']:.4f} "
                f"Spearman={pc['spearman']['point']:.4f} (n={pc['n_aligned_buckets']}, seed={a.corr_seed})")
        except Exception as exc:  # noqa: BLE001 -- bar cache may not exist yet
            pc = None
            pc_art = None
            log(f"  rho(BTC,ETH): nicht berechenbar ({exc}) -- WP-0-Bar-Cache fehlt/deckt Bereich nicht ab.")
    else:
        pc_art = None

    log("[10/10] DEC-53-Artefakte + Report schreiben")
    null_pw_art = null_ic.write_artifacts(out_dir, sd_null_pw, window_label="per_window_w52")
    null_pooled_art = null_ic.write_artifacts(out_dir, sd_null_pooled, window_label="pooled_w104")

    ic_csv = panel_load.write_csv(
        out_dir / "weekly_ic_series.csv", ["week", "ic", "k"],
        [[weeks[t], None if math.isnan(ic_series[t]) else round(float(ic_series[t]), 10), int(k_full[t])]
         for t in range(n_weeks - 1)])

    sigma_ls_weeks = [weeks[t] for t in range(n_weeks) if int(alive[t].sum()) >= 10]
    sigma_ls_map = dict(zip(sigma_ls_weeks, sigma_ls["weekly"]))
    sigma_xs_weekly = sigma_xs["weekly"]
    sigma_csv = panel_load.write_csv(
        out_dir / "weekly_sigma_xs_sigma_ls.csv", ["week", "sigma_xs", "sigma_ls"],
        [[weeks[t],
          None if math.isnan(sigma_xs_weekly[t]) else round(float(sigma_xs_weekly[t]), 10),
          None if sigma_ls_map.get(weeks[t]) is None else round(float(sigma_ls_map[weeks[t]]), 10)]
         for t in range(n_weeks)])

    deadzone_csv = panel_load.write_csv(
        out_dir / "deadzone_by_decile.csv",
        ["decile", "n_symbol_weeks", "n_symbol_days_with_funding", "n_deadzone_symbol_days", "deadzone_share"],
        [[d["decile"], d["n_symbol_weeks"], d["n_symbol_days_with_funding"],
          d["n_deadzone_symbol_days"], d["deadzone_share"]] for d in deadzone["by_decile"]])

    spread_json_path = out_dir / "spread_census.json"
    spread_json_path.write_text(json.dumps({"source": spread_source, **spread_census}, indent=1))
    spread_json_art = {"path": str(spread_json_path), "sha256": panel_load.sha256_file(spread_json_path)}

    extra: dict = {
        "judgement_bearing": judgement_bearing,
        "label": "urteilstragend" if judgement_bearing else "nicht urteilstragend (--allow-partial)",
        "as_of": as_of.isoformat(), "seed": seed, "allow_partial": a.allow_partial,
        "manifest_status_counts": counts, "n_symbols": len(panel["symbols"]),
        "n_partitions_used": panel["n_partitions_used"], "year_range": panel["year_range"],
        "range_fingerprint": range_fp,
        "k_per_week": k_summary, "k_per_week_sensitivity": sensitivity,
        "instruments": {"n_rows": inst["n_rows"], "statuses": inst["statuses"],
                         "n_non_trading": len(non_trading),
                         "funding_interval_reported_minutes": funding_interval_reported},
        "sigma_xs": {k: v for k, v in sigma_xs.items() if k != "weekly"},
        "sigma_ls": {k: v for k, v in sigma_ls.items() if k != "weekly"},
        "cost_bps_round_trip_taker": {
            "value": cost_bps_rt, "source": "bybit_edge.config.FEE_TAKER (0.055%/Bein) * 2",
            "label": "Taker-Round-Trip-Wand (PRD B.1: 11 bp)"},
        "n_eff_full": {"label": report_mod.N_EFF_LABEL, **neff_full},
        "n_eff_stress_abs_weeks": {"label": report_mod.N_EFF_LABEL + " (STRESS_ABS-Wochen)",
                                    "stress_info": {k: v for k, v in stress_info.items()
                                                    if k != "week_indices"}, **neff_stress},
        "deadzone_census_dec59": deadzone,
        "funding_autocorrelation_dec58": funding_autocorr,
        "delisting_cohorts_dec58g": cohorts,
        "spread_census_source": spread_source,
        "artifacts": {
            "weekly_ic_series_csv": ic_csv,
            "null_ic_per_window": null_pw_art, "null_ic_pooled": null_pooled_art,
            "weekly_sigma_csv": sigma_csv, "deadzone_by_decile_csv": deadzone_csv,
            "spread_census_json": spread_json_art,
            **({"pair_corr_btc_eth": pc_art} if pc_art else {}),
        },
    }

    full = report_mod.assemble_report(
        b1_b2=b1_b2, b3=b3, b4=b4, b5=b5, n_eff=neff_full,
        pair_corr_btc_eth=pc, extra=extra)
    paths = report_mod.write_report(out_dir, full)
    log(f"Report geschrieben: {paths['json']} / {paths['md']}")
    if not judgement_bearing:
        log("WARNUNG: Report ist NICHT urteilstragend (--allow-partial mit "
            "PARTIAL/FAILED-Partitionen) -- siehe extra.label.")
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
    ap.add_argument("--allow-partial", action="store_true",
                    help="Zensus trotz PARTIAL/FAILED-Partitionen zulassen -- der Report "
                         "traegt dann das Etikett 'nicht urteilstragend' statt zu abbrechen.")
    ap.add_argument("--as-of", default="",
                    help="Referenzdatum fuer frozen/open-Jahresgrenze und Delisting-Kohorten "
                         "(YYYY-MM-DD, Default: heute)")
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
