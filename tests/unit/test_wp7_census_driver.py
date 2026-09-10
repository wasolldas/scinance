"""End-to-end tests for the real ``--census`` driver
(``scripts/wp7_universe_census.py::cmd_census``), built on synthetic
``panel_1d`` trees via ``panel_store.write_year_partition`` (see
``scinance3-impl/WP7_SPEZIFIKATION.md`` section 3, task item 6).

No network: ``bybit_rest.fetch_instruments``/``fetch_tickers`` are
monkeypatched to fixture responses in every test that runs the CLI driver
(the sandbox egress proxy blocks the real Bybit API -- CLAUDE.md).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp7_universe import bybit_rest, panel_load, panel_store, pit_universe

ROOT = Path(__file__).resolve().parents[2]
_EPOCH = date(1970, 1, 1)


def _load_census_script():
    p = ROOT / "scripts" / "wp7_universe_census.py"
    spec = importlib.util.spec_from_file_location("wp7_universe_census_driver", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CENSUS = _load_census_script()


def _ns(**overrides) -> argparse.Namespace:
    base = dict(
        panel_base="", category="linear", start_year=2023, end_year=2025,
        out="", seed=53, allow_partial=False, as_of="2025-12-31",
        dates="", harvest_base="data/harvest",
        bar_cache_dir="", corr_start="", corr_end="", corr_seed=53,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _fake_instruments(statuses_by_symbol: dict[str, str]):
    def fetch_instruments(category="linear", **kw):
        rows = [{"symbol": s, "status": st, "launchTime": "1600000000000"}
                for s, st in statuses_by_symbol.items()]
        return {"category": category, "rows": rows, "n_rows": len(rows),
                "n_pages": 1, "raw_sha256": ["fake"],
                "statuses": sorted(set(statuses_by_symbol.values()))}
    return fetch_instruments


def _fake_tickers():
    def fetch_tickers(category="linear", **kw):
        rows = [{"symbol": f"TICK{i}USDT", "bid1Price": "100.0", "ask1Price": "100.1",
                 "openInterest": "1000", "fundingRate": "0.0001",
                 "turnover24h": str(1_000_000 - i * 1000)} for i in range(5)]
        return {"category": category, "rows": rows, "n_rows": len(rows),
                "raw_sha256": "fake", "raw_head": "fake"}
    return fetch_tickers


def _write_symbol(base, manifest, symbol, day_closes: list[tuple[str, float]], *,
                   funding: dict[str, tuple[int, float]] | None = None) -> None:
    """Write every year-partition a symbol needs, DONE by construction: each
    year's ``as_of_date`` is pinned to that YEAR's own last observed day
    (mirrors a listing/delisting-aware fetch). A real ``--fetch`` run uses
    one GLOBAL as-of for every symbol and would instead show the
    delisting year as PARTIAL -- a known, documented production gap
    (``expected_days_in_year`` has no delisting-date concept), deliberately
    NOT reproduced here so these tests isolate the driver's OWN logic
    (PIT masking, B3, DEC-59 census) from that separate data-layer gap.
    """
    if not day_closes:
        return
    by_year: dict[int, list[dict]] = {}
    for d_iso, close in day_closes:
        d = date.fromisoformat(d_iso)
        ms = int((d - _EPOCH).days) * 86_400_000
        row = {"start_ms": ms, "open": close, "high": close, "low": close,
               "close": close, "volume": 1.0, "turnover": 1_000_000.0}
        if funding and d_iso in funding:
            fn, fs = funding[d_iso]
            row["funding_n"], row["funding_sum"] = fn, fs
        by_year.setdefault(d.year, []).append(row)
    listing_date = date.fromisoformat(day_closes[0][0])
    for year, rows in sorted(by_year.items()):
        last_day = max(date.fromisoformat(d) for d, _ in day_closes if date.fromisoformat(d).year == year)
        as_of_census = date.fromisoformat(day_closes[-1][0])
        frozen = year < as_of_census.year
        panel_store.write_year_partition(
            base, manifest, symbol, year, rows,
            listing_date=listing_date, as_of_date=last_day, frozen=frozen)


def _weekly_calendar(d0: date, d1: date) -> tuple[list[date], list[date], dict]:
    """All calendar days ``[d0, d1]`` + their sorted distinct ISO-week
    starts + a ``{week_start: n_days_in_range}`` count (for spreading a
    weekly return evenly across its days)."""
    days = [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]
    week_of_day = [pit_universe.iso_week_start(d) for d in days]
    weeks = sorted(set(week_of_day))
    counts: dict[date, int] = {}
    for w in week_of_day:
        counts[w] = counts.get(w, 0) + 1
    return days, weeks, counts


def _momentum_panel(tmp_path, *, k_symbols: int, seed: int, momentum_loading: float,
                     start=date(2023, 1, 1), end=date(2025, 12, 31), sigma=0.05,
                     trail_win: int = 4):
    """Build a synthetic panel with a GENUINE trailing-return momentum
    process: ``returns[t] = momentum_loading * sum(returns[t-trail_win:t])
    + idio[t]``. ``momentum_loading=0`` gives a pure random-walk (NULL)
    panel. Daily closes are constructed so each ISO week's realised return
    (last-close/first-close ratio) reproduces the generated weekly return
    exactly (additive log returns spread evenly across that week's days).
    """
    days, weeks, counts = _weekly_calendar(start, end)
    n_weeks, n_days = len(weeks), len(days)
    week_idx = {w: i for i, w in enumerate(weeks)}

    rng = np.random.default_rng(seed)
    returns = np.zeros((n_weeks, k_symbols))
    idio = rng.normal(0, sigma, size=(n_weeks, k_symbols))
    returns[0] = idio[0]
    for t in range(1, n_weeks):
        lo = max(0, t - trail_win)
        trail = returns[lo:t].sum(axis=0)
        returns[t] = momentum_loading * trail + idio[t]

    daily_logret = np.zeros((n_days, k_symbols))
    for i, d in enumerate(days):
        w = week_idx[pit_universe.iso_week_start(d)]
        daily_logret[i] = returns[w] / counts[pit_universe.iso_week_start(d)]
    log_close = np.cumsum(daily_logret, axis=0)
    closes = 100.0 * np.exp(log_close)

    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    symbols = [f"MOM{j:04d}USDT" for j in range(k_symbols)]
    for j, sym in enumerate(symbols):
        day_closes = [(d.isoformat(), float(closes[i, j])) for i, d in enumerate(days)]
        _write_symbol(base, manifest, sym, day_closes)
    return base, manifest, symbols, weeks, returns


# ============================================================================
# positive / null / adversarial (task item 6, DEC-39-style trio for the
# real census DRIVER, not just the pure pit_universe functions)
# ============================================================================

def test_census_positive_momentum_gives_b2_and_nontrivial_ic(tmp_path, monkeypatch):
    base, _manifest, symbols, _weeks, _ = _momentum_panel(
        tmp_path, k_symbols=200, seed=0, momentum_loading=0.22)

    statuses = {s: "Trading" for s in symbols}
    statuses["DEADCOINUSDT"] = "Closed"  # a non-trading row NOT in the panel -> B3 stays off
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out"
    a = _ns(panel_base=str(base), out=str(out))
    rc = CENSUS.cmd_census(a)
    assert rc == 0

    report = json.loads((out / "wp7_report.json").read_text())
    assert report["findings"]["b1_b2"]["finding"] == "B2"
    assert report["findings"]["b1_b2"]["consequence"].startswith("Klasse W testbar")

    ic_rows = (out / "weekly_ic_series.csv").read_text().splitlines()[1:]
    ics = [float(r.split(",")[1]) for r in ic_rows if r.split(",")[1] != ""]
    assert len(ics) > 50
    assert float(np.mean(ics)) > 0.02  # comfortably positive, not a rounding coincidence


def test_census_null_panel_b1_or_b2_purely_by_sd_null_ic_near_zero(tmp_path, monkeypatch):
    base, _manifest, symbols, _weeks, _ = _momentum_panel(
        tmp_path, k_symbols=30, seed=1, momentum_loading=0.0)  # signal-free, K below both floors

    statuses = {s: "Trading" for s in symbols}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out"
    a = _ns(panel_base=str(base), out=str(out))
    rc = CENSUS.cmd_census(a)
    assert rc == 0

    report = json.loads((out / "wp7_report.json").read_text())
    b12 = report["findings"]["b1_b2"]
    # K=30 is under BOTH K_MIN floors (134/117) -> B1 is the only possible
    # finding here, REGARDLESS of SD_null -- exactly the "purely by
    # SD_null/K, not by injected signal" property under test.
    assert b12["finding"] == "B1"
    assert b12["per_window_feasible"] is False and b12["pooled_feasible"] is False

    ic_rows = (out / "weekly_ic_series.csv").read_text().splitlines()[1:]
    ics = [float(r.split(",")[1]) for r in ic_rows if r.split(",")[1] != ""]
    assert len(ics) > 20
    assert abs(float(np.mean(ics))) < 0.05  # no momentum injected -> mean IC near zero


def test_census_adversarial_delisting_excluded_from_pit_and_b3_reflects_kline(tmp_path, monkeypatch):
    """Half the symbols are delisted mid-window. The PIT alive mask must
    drop them after their last bar (checked directly via panel_load, the
    same machinery the driver uses); B3 must report exactly how many
    delisted symbols were checked and how many carry kline history."""
    start, end = date(2023, 1, 1), date(2025, 12, 31)
    days, weeks, _counts = _weekly_calendar(start, end)
    n_days = len(days)
    K, seed = 160, 2
    rng = np.random.default_rng(seed)
    n_doomed = K // 2
    doomed = set(rng.choice(K, size=n_doomed, replace=False).tolist())

    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    symbols = [f"ADV{j:04d}USDT" for j in range(K)]
    log_close = np.cumsum(rng.normal(0, 0.05, size=(n_days, K)), axis=0)
    closes = 100.0 * np.exp(log_close)
    last_day_by_symbol: dict[str, date] = {}
    for j, sym in enumerate(symbols):
        if j in doomed:
            delist_day_idx = int(rng.integers(200, n_days - 30))
            day_closes = [(days[i].isoformat(), float(closes[i, j])) for i in range(delist_day_idx + 1)]
        else:
            day_closes = [(d.isoformat(), float(closes[i, j])) for i, d in enumerate(days)]
        last_day_by_symbol[sym] = date.fromisoformat(day_closes[-1][0])
        _write_symbol(base, manifest, sym, day_closes)

    doomed_symbols = {symbols[j] for j in doomed}
    statuses = {s: ("Closed" if s in doomed_symbols else "Trading") for s in symbols}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out"
    a = _ns(panel_base=str(base), out=str(out))
    rc = CENSUS.cmd_census(a)
    assert rc == 0
    report = json.loads((out / "wp7_report.json").read_text())
    b3 = report["findings"]["b3"]
    assert b3["delisted_symbols_checked"] == n_doomed
    assert b3["delisted_symbols_with_kline"] == n_doomed  # every doomed symbol HAS kline history
    assert b3["triggered"] is False  # kline history exists -> B3 not triggered

    cohorts = report["extra"]["delisting_cohorts_dec58g"]
    assert sum(c["n_delisted"] for c in cohorts) == n_doomed

    # PIT mask directly: doomed symbols must be alive through their last
    # week and absent (never retroactively removed, never present after).
    panel = panel_load.load_panel(base, manifest, year_start=2023, year_end=2025,
                                   as_of=date(2025, 12, 31), symbols=symbols)
    weekly = panel_load.weekly_returns_and_mask(panel)
    sym_pos = {s: i for i, s in enumerate(weekly["symbols"])}
    for sym in doomed_symbols:
        j = sym_pos[sym]
        last_w = weekly["last_week"][j]
        assert weekly["alive"][last_w, j]           # present through its true last week
        if last_w + 1 < len(weekly["weeks"]):
            assert not weekly["alive"][last_w + 1, j]  # gone the week after, not before


# ============================================================================
# DEC-59 deadzone census: symbols exactly at I every interval -> share 1.0
# ============================================================================

def test_funding_deadzone_census_share_one_for_exact_interest_symbols():
    dates = [(date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(8)]
    symbols = ["DEADZONEUSDT", "NOISYUSDT"]
    n_days = len(dates)
    funding_n = np.full((n_days, 2), 3.0)  # 8h class (480 min) for both
    funding_sum = np.zeros((n_days, 2))
    i_settlement = panel_load.I_PER_8H  # 8h class -> normalisation factor is 1.0
    funding_sum[:, 0] = 3 * i_settlement          # symbol 0: EXACTLY at I every day
    funding_sum[:, 1] = 3 * (i_settlement * 5.0)  # symbol 1: far from I every day

    panel = {"symbols": symbols, "dates": dates, "funding_n": funding_n, "funding_sum": funding_sum}
    result = panel_load.funding_deadzone_census(panel, n_deciles=2)

    assert result["descriptive_only"] is True
    assert result["interval_class_counts"] == {"480min": n_days * 2}
    by_decile = {d["decile"]: d for d in result["by_decile"]}
    # symbol 1 has the LARGER weekly funding sum -> ranked into decile 1;
    # symbol 0 (the deadzone symbol) is smaller -> decile 2.
    assert by_decile[2]["deadzone_share"] == pytest.approx(1.0)
    assert by_decile[1]["deadzone_share"] == pytest.approx(0.0)
    assert result["overall_share"] == pytest.approx(0.5)


# ============================================================================
# determinism (task item 6): same seed -> byte-identical report JSON
# ============================================================================

def test_census_determinism_same_seed_identical_report(tmp_path, monkeypatch):
    base, _manifest, symbols, _weeks, _ = _momentum_panel(
        tmp_path, k_symbols=40, seed=3, momentum_loading=0.1,
        start=date(2023, 1, 1), end=date(2024, 12, 31))
    statuses = {s: "Trading" for s in symbols}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    reports = []
    out = tmp_path / "out"  # SAME out dir both runs -- artifact paths must match too
    for _ in range(2):
        a = _ns(panel_base=str(base), out=str(out), as_of="2024-12-31",
                start_year=2023, end_year=2024, seed=53)
        rc = CENSUS.cmd_census(a)
        assert rc == 0
        reports.append(json.loads((out / "wp7_report.json").read_text()))

    assert reports[0] == reports[1]


# ============================================================================
# loud-fail: PARTIAL manifest without --allow-partial
# ============================================================================

def test_census_loud_fail_on_partial_manifest_without_allow_partial(tmp_path, monkeypatch):
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    year = 2023
    # DONE symbol: full year
    full_days = [(date(year, 1, 1) + timedelta(days=i)).isoformat() for i in range(365)]
    _write_symbol(base, manifest, "OKUSDT", [(d, 100.0 + i * 0.01) for i, d in enumerate(full_days)])
    # PARTIAL symbol: deliberately short of expected_days for the year (a gap)
    rows = []
    for i in range(300):
        d = date(year, 1, 1) + timedelta(days=i)
        ms = int((d - _EPOCH).days) * 86_400_000
        rows.append({"start_ms": ms, "open": 1.0, "high": 1.0, "low": 1.0,
                     "close": 1.0, "volume": 1.0, "turnover": 1.0})
    panel_store.write_year_partition(
        base, manifest, "GAPUSDT", year, rows,
        listing_date=date(year, 1, 1), as_of_date=date(year, 12, 31), frozen=True)
    counts = panel_store.manifest_status_counts(manifest)
    assert counts.get("PARTIAL") == 1

    statuses = {"OKUSDT": "Trading", "GAPUSDT": "Trading"}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out_refused"
    a = _ns(panel_base=str(base), out=str(out), as_of=f"{year}-12-31",
            start_year=year, end_year=year)
    rc = CENSUS.cmd_census(a)
    assert rc != 0
    assert not (out / "wp7_report.json").is_file()

    out2 = tmp_path / "out_allowed"
    a2 = _ns(panel_base=str(base), out=str(out2), as_of=f"{year}-12-31",
             start_year=year, end_year=year, allow_partial=True)
    rc2 = CENSUS.cmd_census(a2)
    assert rc2 == 0
    report = json.loads((out2 / "wp7_report.json").read_text())
    assert report["extra"]["judgement_bearing"] is False
    assert "nicht urteilstragend" in report["extra"]["label"]
