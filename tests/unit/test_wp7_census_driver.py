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
import math
import re
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


# ============================================================================
# DEC-67 Entscheidung 6 -- census correction: driver wiring (task item 7e/f)
# ============================================================================

_FORBIDDEN_KEY_RE = re.compile(r"(real_ic|ic_a1|a1_ic)", re.IGNORECASE)


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def test_census_report_carries_dec67_correction_keys_and_artifacts(tmp_path, monkeypatch):
    """Task item 7(e): the driver's JSON carries the four new ``extra``
    sections (n_eff_windows, a1_key_null, decile_degeneration,
    interval_switching) with sane values, and every existing value/section
    (K, SD_null, B1..B5, n_eff full-history) is untouched."""
    base, _manifest, symbols, _weeks, _ = _momentum_panel(
        tmp_path, k_symbols=150, seed=5, momentum_loading=0.1,
        start=date(2021, 1, 1), end=date(2025, 12, 31))
    statuses = {s: "Trading" for s in symbols}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out"
    a = _ns(panel_base=str(base), out=str(out), as_of="2025-12-31", start_year=2021, end_year=2025)
    rc = CENSUS.cmd_census(a)
    assert rc == 0
    report = json.loads((out / "wp7_report.json").read_text())
    extra = report["extra"]

    for key in ("n_eff_windows", "a1_key_null", "decile_degeneration", "interval_switching"):
        assert key in extra, key

    # old sections/values untouched by the additive correction.
    assert "n_eff_full" in extra and "n_eff_stress_abs_weeks" in extra
    assert report["n_eff"]["label"] == "N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil)"
    assert math.isnan(report["n_eff"]["n_eff"])  # full-history line legitimately n/a (ramp-up weeks)
    assert report["findings"]["b1_b2"]["finding"] in ("B1", "B2")

    nw = extra["n_eff_windows"]
    assert nw["label"] == report["n_eff"]["label"]
    assert nw["w52"]["window_weeks"] == 52 and nw["w104"]["window_weeks"] == 104
    # 5 years of a STABLE symbol set -> both judgement windows are balanced
    # and finite -- this is the bug fix under test.
    assert not math.isnan(nw["w52"]["n_eff"])
    assert nw["w52"]["n_symbols_balanced"] == len(symbols)
    assert not math.isnan(nw["w104"]["n_eff"])
    assert nw["w104"]["n_symbols_balanced"] == len(symbols)
    assert "note" in nw["stress_abs_last104"]  # no STRESS_ABS fixture in this sandbox -> n/a, labelled

    an = extra["a1_key_null"]
    assert an["sd_null_per_window"] >= 0.0
    assert an["sd_null_pooled"] >= 0.0
    assert an["sd_null_per_window_w_eff_adjusted"] == pytest.approx(
        an["sd_null_per_window"] * math.sqrt(1.0 / 0.41), rel=1e-9)
    assert an["sd_null_pooled_w_eff_adjusted"] == pytest.approx(
        an["sd_null_pooled"] * math.sqrt(1.0 / 0.41), rel=1e-9)
    assert an["w_eff_factor"] == 0.41
    assert an["threshold_per_window"] == pytest.approx(0.08699, abs=1e-4)
    assert an["threshold_pooled"] == pytest.approx(0.09657, abs=1e-4)

    dd = extra["decile_degeneration"]
    assert dd["last_52"]["n_weeks"] <= 52
    assert dd["previous_52"]["n_weeks"] <= 52

    isw = extra["interval_switching"]
    assert isw["n_symbols"] == len(symbols)
    assert sum(isw["n_switch_distribution"].values()) == len(symbols)
    assert isw["days_per_class_total"] == {}  # _momentum_panel attaches no funding data at all

    arts = extra["artifacts"]
    for name in ("a1_key_null_per_window", "a1_key_null_pooled"):
        assert name in arts, name
        p = Path(arts[name]["path"])
        assert p.is_file()
        # DEC-53 artifact: sha256 is over the content fields (null_ic.
        # artifact_fingerprint), not the raw file bytes -- read_artifacts
        # recomputes and raises loudly on any mismatch/corruption.
        from bybit_edge.research.wp7_universe import null_ic
        verified = null_ic.read_artifacts(p)
        assert verified["sha256"] == arts[name]["sha256"]

    dd_csv = arts["decile_degeneration_weekly_csv"]
    p = Path(dd_csv["path"])
    assert p.is_file()
    assert dd_csv["sha256"] == panel_load.sha256_file(p)

    md = (out / "wp7_report.md").read_text()
    for label in ("N_eff (Ledoit-Wolf-geschrumpft", "A1-Schluessel Permutations-Null",
                  "Dezil-Degeneration des A1-Schluessels", "Intervallklassen-Wechsel"):
        assert label in md


def test_census_report_seals_a1_real_ic_never_computed_or_named(tmp_path, monkeypatch):
    """Task item 7(f): no key named like real_ic/ic_a1/a1_ic anywhere in
    the report, and the a1_key_null section carries ONLY permutation-null
    figures -- never a real Spearman IC of the actual A1 key."""
    base, _manifest, symbols, _weeks, _ = _momentum_panel(
        tmp_path, k_symbols=140, seed=6, momentum_loading=0.15,
        start=date(2022, 1, 1), end=date(2024, 12, 31))
    statuses = {s: "Trading" for s in symbols}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out"
    a = _ns(panel_base=str(base), out=str(out), as_of="2024-12-31", start_year=2022, end_year=2024)
    rc = CENSUS.cmd_census(a)
    assert rc == 0

    report = json.loads((out / "wp7_report.json").read_text())
    offending_keys = sorted({k for k in _walk_keys(report) if _FORBIDDEN_KEY_RE.search(k)})
    assert offending_keys == []

    md_text = (out / "wp7_report.md").read_text()
    assert not _FORBIDDEN_KEY_RE.search(md_text)

    an = report["extra"]["a1_key_null"]
    assert set(an) == {
        "label", "sd_null_per_window", "sd_null_pooled", "threshold_per_window",
        "threshold_pooled", "sd_null_per_window_w_eff_adjusted",
        "sd_null_pooled_w_eff_adjusted", "w_eff_factor", "feasible_per_window",
        "feasible_pooled", "seed", "note",
    }


def test_a1_key_null_deterministic_same_seed(tmp_path, monkeypatch):
    """Task item 7(f), determinism: same seed -> byte-identical a1_key_null
    (and decile_degeneration) section across two independent runs."""
    base, _manifest, symbols, _weeks, _ = _momentum_panel(
        tmp_path, k_symbols=50, seed=9, momentum_loading=0.05,
        start=date(2023, 1, 1), end=date(2024, 12, 31))
    statuses = {s: "Trading" for s in symbols}
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    a1_results, deg_results = [], []
    out = tmp_path / "out"
    for _ in range(2):
        a = _ns(panel_base=str(base), out=str(out), as_of="2024-12-31",
                start_year=2023, end_year=2024, seed=53)
        rc = CENSUS.cmd_census(a)
        assert rc == 0
        report = json.loads((out / "wp7_report.json").read_text())
        a1_results.append(report["extra"]["a1_key_null"])
        deg_results.append(report["extra"]["decile_degeneration"])
    assert a1_results[0] == a1_results[1]
    assert deg_results[0] == deg_results[1]
