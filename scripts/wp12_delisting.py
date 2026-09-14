#!/usr/bin/env python3
"""WP-12 Runner: Delisting-Register + Survivorship-Fixture (PRD 4.1 B3,
DEC-67 Entscheidung 5).

Drei Schritte, meistens in dieser Reihenfolge (siehe
``handoff_local/run_wp12_delisting.ps1``):

  # 1) Register: PUBLIC Bybit-Announcements (keyfrei) -> Rohantworten +
  #    register.parquet + Manifest, NIE unter data/harvest:
  python scripts/wp12_delisting.py --announce \
      --register-base data/delisting_register

  # 2) Kline-Probe: fuer jedes delistete lineare Symbol im Register --
  #    liefert Bybit noch Tages-Historie in den 90 Tagen vor Delisting?
  python scripts/wp12_delisting.py --probe-klines \
      --register-base data/delisting_register

  # 3) Report -- zwei Modi:
  #    a) --mode probe: NUR Register + Kline-Probe berichten, keine IC-Messung.
  #    b) --mode fixture: zusaetzlich die Survivorship-Verzerrung messen
  #       (WP-7-panel_1d als Basis noetig -- braucht echtes Netz auf dem
  #       Nutzer-PC; laeuft NIE gegen data/harvest).
  python scripts/wp12_delisting.py --mode fixture \
      --register-base data/delisting_register --panel-base data/panel_1d \
      --out scinance3-impl/state/wp12_YYYYMMDD

KEIN PASS/FAIL: das Survivorship-Fixture berichtet ausschliesslich die
gemessene Verzerrung + CI (PRD 4.1 B3 -- die registrierte Schwelle ist
noch nicht gesetzt, A3 ist nicht registriert, DEC-67 Entscheidung 1).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.wp12_delisting import (  # noqa: E402
    announcements, kline_probe, panel_read, report, survivorship_fixture as sf,
)


def log(msg: str) -> None:
    print(msg, flush=True)


def _register_dir(a: argparse.Namespace) -> Path:
    return Path(a.register_base)


def _read_register_rows(register_dir: Path) -> list[dict]:
    import pyarrow.parquet as pq

    path = register_dir / "register.parquet"
    if not path.is_file():
        raise SystemExit(f"ERROR: {path} fehlt -- zuerst --announce laufen lassen.")
    table = pq.read_table(path)
    return table.to_pylist()


# ----------------------------------------------------------------------------
# cmd_announce
# ----------------------------------------------------------------------------

def cmd_announce(a: argparse.Namespace) -> int:
    register_dir = _register_dir(a)
    if "data/harvest" in register_dir.as_posix():
        raise SystemExit("ERROR: register-base darf niemals unter data/harvest liegen.")
    log(f"=== WP-12 Schritt 1: Delisting-Register (Bybit public announcements, "
        f"type={a.type!r} locale={a.locale!r}) ===")
    fetched = announcements.fetch_delisting_announcements(
        locale=a.locale, type_param=a.type, tag_fallback=a.tag, limit=a.page_limit)
    raw_files = announcements.write_raw_pages(register_dir / "raw", fetched["raw_pages"])
    rows = announcements.build_register_rows(fetched["rows"])
    reg_art = announcements.write_register_parquet(rows, register_dir / "register.parquet")
    n_symbols = len({s for r in rows for s in r["symbols"]})
    n_linear = len({s for r in rows for s in r["symbols"] if r["category"] == "linear"})
    manifest = {
        "fetched_at_utc": date.today().isoformat(), "param_used": fetched["param_used"],
        "n_raw_pages": len(raw_files), "n_raw_rows": len(fetched["rows"]),
        "n_register_rows": len(rows), "n_symbols_extracted": n_symbols,
        "n_symbols_linear": n_linear, "register_sha256": reg_art["sha256"],
        "raw_files": raw_files,
    }
    (register_dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log(f"  {len(rows)} Announcements ({fetched['param_used']}), "
        f"{n_symbols} distinkte Symbole ({n_linear} linear), "
        f"register.parquet sha256={reg_art['sha256']}")
    log(f"  Rohantworten: {len(raw_files)} Seiten unter {register_dir / 'raw'}")
    return 0


# ----------------------------------------------------------------------------
# cmd_probe_klines
# ----------------------------------------------------------------------------

def cmd_probe_klines(a: argparse.Namespace) -> int:
    register_dir = _register_dir(a)
    rows = _read_register_rows(register_dir)
    log(f"=== WP-12 Schritt 2: Kline-Verfuegbarkeits-Probe ({a.window_days} Tage) ===")
    probe = kline_probe.probe_register(rows, window_days=a.window_days, max_symbols=a.max_symbols)
    klines_dir = register_dir / "klines"
    written = kline_probe.write_klines_parquet(klines_dir, probe["results"])
    summ_art = kline_probe.write_probe_summary(klines_dir, probe)
    log(f"  {probe['n_symbols_probed']} Symbole probiert: "
        f"{probe['n_available']} verfuegbar / {probe['n_unavailable']} nicht verfuegbar "
        f"({probe['n_skipped_no_reference_date']} ohne Referenzdatum uebersprungen)")
    log(f"  {len(written)} Kline-Parquet-Dateien unter {klines_dir}")
    log(f"  Zusammenfassung: {summ_art['path']} (sha256={summ_art['sha256']})")
    return 0


# ----------------------------------------------------------------------------
# cmd_report (--mode probe | fixture)
# ----------------------------------------------------------------------------

def _load_register_summary(register_dir: Path) -> dict | None:
    manifest_path = register_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"n_rows": m.get("n_register_rows"), "n_symbols_extracted": m.get("n_symbols_extracted"),
            "n_symbols_linear": m.get("n_symbols_linear"), "param_used": m.get("param_used"),
            "sha256": m.get("register_sha256")}


def _load_kline_probe_summary(register_dir: Path) -> tuple[dict | None, list[dict] | None]:
    summ_path = register_dir / "klines" / "kline_probe_summary.json"
    if not summ_path.is_file():
        return None, None
    summary = json.loads(summ_path.read_text(encoding="utf-8"))
    return summary, summary.get("results")


def cmd_report(a: argparse.Namespace) -> int:
    register_dir = _register_dir(a)
    reg_summary = _load_register_summary(register_dir)
    kp_summary, kp_results = _load_kline_probe_summary(register_dir)
    artifacts: dict = {}
    if reg_summary is not None:
        artifacts["register_parquet"] = {
            "path": str(register_dir / "register.parquet"), "sha256": reg_summary["sha256"]}

    fixture_result = None
    if a.mode == "fixture":
        log("=== WP-12 Schritt 3 (fixture): Survivorship-Verzerrung messen ===")
        as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
        daily = panel_read.load_daily_closes(
            a.panel_base, a.manifest, year_start=a.start_year, year_end=a.end_year,
            as_of=as_of, allow_partial=a.allow_partial)
        weekly = panel_read.weekly_returns_and_alive(daily)
        base_returns, base_alive = weekly["returns"], weekly["alive"]
        n_weeks = base_returns.shape[0]
        log(f"  WP-7-panel_1d gelesen: {len(weekly['symbols'])} Symbole, {n_weeks} Wochen")

        real_available = [r for r in (kp_results or []) if r.get("available") and r.get("rows")]
        if real_available:
            delisted = sf.delisted_klines_to_weekly(real_available, weekly["weeks"])
            mode_label = "REAL"
            log(f"  {len(delisted['symbols'])} REALE delistete Symbole mit Historie eingebunden.")
        else:
            synth = sf.make_synthetic_delisted_panel(n_weeks, seed=a.seed, n_symbols=a.n_synthetic)
            delisted = {"returns": synth["returns"], "alive": synth["alive"]}
            mode_label = sf.SYNTHETIC_SYMBOL_PREFIX
            log(f"  KEINE reale delistete Historie verfuegbar -- SYNTHETISCHES "
                f"Adversarial-Set ({a.n_synthetic} Symbole, -30% Terminal-Drawdown) verwendet.")

        fixture_result = sf.run_fixture_measurement(
            base_returns, base_alive, delisted["returns"], delisted["alive"],
            seed=a.seed, n_boot=a.n_boot, week_labels=weekly["weeks"], mode_label=mode_label)
        b = fixture_result["bootstrap"]
        log(f"  bias = IC_with - IC_without = {fixture_result['bias_point']:.4f} "
            f"[{b['ci_lo']:.4f}; {b['ci_hi']:.4f}] (n_boot={b['n_boot']}, seed={b['seed']})")
        log(f"  {sf.THRESHOLD_NOT_REGISTERED_NOTE}")

        out_dir = Path(a.out)
        art = sf.write_artifacts(out_dir, fixture_result)
        csvs = sf.write_ic_series_csv(out_dir, fixture_result)
        artifacts["survivorship_bias"] = art
        artifacts["ic_series_csv"] = csvs

    summary = report.assemble_summary(
        mode=a.mode, register=reg_summary, kline_probe=kp_summary,
        fixture=fixture_result, artifacts=artifacts)
    out_dir = Path(a.out)
    written = report.write_report(out_dir, summary)
    log(f"Report geschrieben: {written['md']} / {written['json']}")
    return 0


# ----------------------------------------------------------------------------
# argparse
# ----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--announce", action="store_true", help="Schritt 1: Delisting-Register fetchen")
    p.add_argument("--probe-klines", action="store_true", help="Schritt 2: Kline-Verfuegbarkeit probieren")
    p.add_argument("--mode", choices=["probe", "fixture"], help="Schritt 3: Report-Modus")

    p.add_argument("--register-base", default="data/delisting_register")
    p.add_argument("--locale", default=announcements.DEFAULT_LOCALE)
    p.add_argument("--type", default=announcements.DEFAULT_TYPE)
    p.add_argument("--tag", default=announcements.FALLBACK_TAG)
    p.add_argument("--page-limit", type=int, default=50)

    p.add_argument("--window-days", type=int, default=kline_probe.PROBE_WINDOW_DAYS)
    p.add_argument("--max-symbols", type=int, default=None)

    p.add_argument("--panel-base", default="data/panel_1d")
    p.add_argument("--manifest", default="data/panel_1d/panel_manifest.sqlite")
    p.add_argument("--start-year", type=int, default=2021)
    p.add_argument("--end-year", type=int, default=date.today().year)
    p.add_argument("--as-of", default="")
    p.add_argument("--allow-partial", action="store_true")
    p.add_argument("--seed", type=int, default=53)
    p.add_argument("--n-boot", type=int, default=1000)
    p.add_argument("--n-synthetic", type=int, default=30)
    p.add_argument("--out", default=f"scinance3-impl/state/wp12_{date.today():%Y%m%d}")
    return p


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if not (a.announce or a.probe_klines or a.mode):
        raise SystemExit("ERROR: mindestens eines von --announce/--probe-klines/--mode noetig.")
    rc = 0
    if a.announce:
        rc = cmd_announce(a) or rc
    if a.probe_klines:
        rc = cmd_probe_klines(a) or rc
    if a.mode:
        rc = cmd_report(a) or rc
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
