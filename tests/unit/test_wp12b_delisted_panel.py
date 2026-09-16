"""Unit tests for WP-12b (delisted ``panel_1d_delisted`` tree + delisting-
aware PIT union census, PRD 4.1 B3, DEC-67 Entscheidung 5, DEC-70).

Covers (per the task brief):
  (a) ``delisted_panel.fetch_delisted_panel`` -- DEC-39 trio:
      POSITIVE (full history fetched -> DONE partitions, delisting_dates
      .json written with sha256), NULL (a symbol with zero kline history
      -> NO_HISTORY recorded loudly, never silently dropped), and resume
      (a second run skips without any network call).
  (b) ``panel_load.load_panel_union`` -- DEC-39 trio continued: POSITIVE
      (symbols sorted globally across both trees, last_alive_day correct)
      and ADVERSARIAL (a symbol present in BOTH trees is a loud error).
  (c) ``panel_load.weekly_returns_and_mask_union`` -- the delisting-week
      convention: the alive mask ends at the week containing the
      delisting date, and the delisting week's OWN return is the REAL
      observed last-price return, never an imputed -100% (contrasted
      directly against ``pit_universe.naive_delisting_overlay``, the
      module's own deliberately-wrong reference estimator).
  (d) ``delisted_symbols_with_history`` excludes NO_HISTORY-only symbols
      from the "usable" delisted set, so a NO_HISTORY symbol never trips
      ``load_panel``'s PARTIAL/FAILED loud-fail gate on a real census run.
  (e) ``scripts/wp7_universe_census.py --include-delisted``: determinism
      (same seed -> byte-identical report JSON) and survivors-only
      byte-identity when the flag is absent (with and without the
      ``include_delisted`` attribute even being set on the namespace, the
      pre-WP-12b test-file shape).
  (f) a monkeypatched end-to-end ``--fetch-delisted-panel`` CLI run.

No network anywhere in this file (the sandbox egress proxy blocks the
real Bybit API, CLAUDE.md) -- every REST call is monkeypatched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp7_universe import bybit_rest, panel_load, panel_store, pit_universe
from bybit_edge.research.wp12_delisting import announcements, delisted_panel

ROOT = Path(__file__).resolve().parents[2]
_EPOCH = date(1970, 1, 1)
_DAY_MS = 86_400_000


def _load_script(name: str):
    p = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", "_driver"), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


WP12 = _load_script("wp12_delisting.py")
CENSUS = _load_script("wp7_universe_census.py")


# ============================================================================
# helpers
# ============================================================================

def _day_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _kline_rows(start: date, end: date, *, base: float = 100.0, seed: int = 0) -> list[dict]:
    days = _day_range(start, end)
    rng = np.random.default_rng(seed)
    logret = rng.normal(0.0001, 0.01, size=len(days))
    closes = base * np.exp(np.cumsum(logret))
    rows = []
    for d, c in zip(days, closes):
        ms = (d - _EPOCH).days * _DAY_MS
        rows.append({"start_ms": ms, "open": float(c), "high": float(c), "low": float(c),
                     "close": float(c), "volume": 1.0, "turnover": 1_000_000.0})
    return rows


def _fake_kline_fetcher(rows_by_symbol: dict[str, list[dict]]):
    def fetch_kline_symbol(symbol, start_ms, end_ms, *, category="linear", **kw):
        rows = rows_by_symbol.get(symbol, [])
        sel = [r for r in rows if start_ms <= r["start_ms"] <= end_ms]
        return {"symbol": symbol, "category": category, "rows": sel, "n_rows": len(sel),
                "n_pages": 1, "raw_sha256": ["fake"]}
    return fetch_kline_symbol


def _fake_funding_empty():
    def fetch_funding_history(symbol, start_ms, end_ms, *, category="linear", **kw):
        return {"symbol": symbol, "category": category, "rows": [], "n_rows": 0,
                "n_pages": 1, "raw_sha256": ["fake"]}
    return fetch_funding_history


def _fake_kline_raises():
    def fetch_kline_symbol(symbol, start_ms, end_ms, **kw):
        raise AssertionError(f"unexpected network call for {symbol} -- resume must skip it")
    return fetch_kline_symbol


def _register_row(symbol: str, *, delist_iso: str | None = None,
                   publish_ms: int = 1700000000000, ann_id: str | None = None) -> dict:
    ann_id = ann_id or f"ann-{symbol.lower()}"
    delisting_ms = None
    if delist_iso:
        d = date.fromisoformat(delist_iso)
        delisting_ms = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
    return {"announcement_id": ann_id, "url": f"https://announcements.bybit.com/en/article/{ann_id}",
            "title": f"Bybit will delist {symbol}", "publish_ms": publish_ms,
            "symbols": [symbol], "category": "linear", "delisting_ms": delisting_ms,
            "raw_snippet": None}


def _write_full_history(base_dir, manifest, symbol: str, day_closes: list[tuple[str, float]], *,
                         as_of_date: date, listing_date: date | None = None) -> None:
    """Write every year-partition a symbol needs directly (no REST), all
    frozen, ``as_of_date`` uniform across years -- the SAME convention
    ``delisted_panel.fetch_delisted_panel`` uses (see its module
    docstring), reused here to build small deterministic fixture trees
    for both the survivors AND the delisted side."""
    if not day_closes:
        return
    if listing_date is None:
        listing_date = date.fromisoformat(day_closes[0][0])
    by_year: dict[int, list[dict]] = {}
    for d_iso, close in day_closes:
        d = date.fromisoformat(d_iso)
        ms = (d - _EPOCH).days * _DAY_MS
        by_year.setdefault(d.year, []).append(
            {"start_ms": ms, "open": close, "high": close, "low": close, "close": close,
             "volume": 1.0, "turnover": 1_000_000.0})
    for year, rows in sorted(by_year.items()):
        panel_store.write_year_partition(base_dir, manifest, symbol, year, rows,
                                          listing_date=listing_date, as_of_date=as_of_date, frozen=True)


def _closes(start: date, end: date, *, base=100.0, seed=0) -> list[tuple[str, float]]:
    days = _day_range(start, end)
    rng = np.random.default_rng(seed)
    logret = rng.normal(0.0, 0.01, size=len(days))
    closes = base * np.exp(np.cumsum(logret))
    return [(d.isoformat(), float(c)) for d, c in zip(days, closes)]


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


def _ns_census(**overrides) -> argparse.Namespace:
    base = dict(
        panel_base="", category="linear", start_year=2023, end_year=2023,
        out="", seed=53, allow_partial=False, as_of="2023-12-31",
        dates="", harvest_base="data/harvest",
        bar_cache_dir="", corr_start="", corr_end="", corr_seed=53,
        include_delisted=False, delisted_base="", delisted_manifest="",
        delisting_dates="", n_boot_survivorship=200,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


# ============================================================================
# (a) delisted_panel.fetch_delisted_panel -- DEC-39 trio
# ============================================================================

def test_fetch_delisted_panel_positive_full_history_done_and_delisting_dates_json(tmp_path, monkeypatch):
    start, delist = date(2021, 1, 1), date(2022, 6, 15)
    rows = _kline_rows(start, delist, seed=1)
    monkeypatch.setattr(bybit_rest, "fetch_kline_symbol", _fake_kline_fetcher({"OLDUSDT": rows}))
    monkeypatch.setattr(bybit_rest, "fetch_funding_history", _fake_funding_empty())

    register_rows = [_register_row("OLDUSDT", delist_iso="2022-06-15")]
    base_dir = tmp_path / "panel_1d_delisted"
    manifest = base_dir / "panel_manifest.sqlite"

    result = delisted_panel.fetch_delisted_panel(
        register_rows, base_dir=base_dir, manifest_path=manifest, start_year=2021)

    assert result["n_fetched"] == 1
    assert result["n_no_history"] == 0
    assert result["n_skipped_no_reference_date"] == 0

    row_2021 = panel_store.manifest_get(manifest, "OLDUSDT", 2021)
    row_2022 = panel_store.manifest_get(manifest, "OLDUSDT", 2022)
    assert row_2021["status"] == "DONE" and row_2021["n_rows"] == 365  # 2021 not a leap year
    assert row_2022["status"] == "DONE"
    assert row_2022["n_rows"] == row_2022["expected_days"] == 166  # Jan 1 .. Jun 15, 2022

    dd = result["delisting_dates_artifact"]
    assert Path(dd["path"]).is_file()
    assert dd["sha256"] == panel_load.sha256_file(dd["path"])
    payload = json.loads(Path(dd["path"]).read_text(encoding="utf-8"))
    assert payload["symbols"]["OLDUSDT"]["delist_date"] == "2022-06-15"
    assert payload["symbols"]["OLDUSDT"]["announcement_id"] == "ann-oldusdt"
    assert payload["symbols"]["OLDUSDT"]["source"] == "delisting_ms"


def test_fetch_delisted_panel_no_history_marks_failed_and_reported(tmp_path, monkeypatch):
    """NULL case: the kline fetch returns ZERO rows -- must be recorded
    loudly as NO_HISTORY (mark_failed), reported by name, and never
    silently dropped."""
    monkeypatch.setattr(bybit_rest, "fetch_kline_symbol", _fake_kline_fetcher({}))  # nothing for anyone
    monkeypatch.setattr(bybit_rest, "fetch_funding_history", _fake_funding_empty())

    register_rows = [_register_row("GHOSTUSDT", delist_iso="2022-03-01")]
    base_dir = tmp_path / "panel_1d_delisted"
    manifest = base_dir / "panel_manifest.sqlite"

    result = delisted_panel.fetch_delisted_panel(
        register_rows, base_dir=base_dir, manifest_path=manifest, start_year=2021)

    assert result["n_no_history"] == 1
    assert result["no_history_symbols"] == ["GHOSTUSDT"]
    row = panel_store.manifest_get(manifest, "GHOSTUSDT", 2022)
    assert row["status"] == "FAILED"
    assert row["failure_reason"] == delisted_panel.NO_HISTORY_REASON == "NO_HISTORY"
    # no parquet partition was ever written for it
    assert not panel_store.partition_path(base_dir, "GHOSTUSDT", 2022, frozen=True).is_file()

    # census-still-runs property: delisted_symbols_with_history excludes
    # a NO_HISTORY-only symbol from the "usable" set entirely.
    usable, no_history_only = panel_load.delisted_symbols_with_history(manifest)
    assert usable == []
    assert no_history_only == ["GHOSTUSDT"]


def test_fetch_delisted_panel_resume_skips_second_run_without_network(tmp_path, monkeypatch):
    start, delist = date(2023, 1, 1), date(2023, 3, 10)
    rows = _kline_rows(start, delist, seed=2)
    monkeypatch.setattr(bybit_rest, "fetch_kline_symbol", _fake_kline_fetcher({"RESUMEUSDT": rows}))
    monkeypatch.setattr(bybit_rest, "fetch_funding_history", _fake_funding_empty())

    register_rows = [_register_row("RESUMEUSDT", delist_iso="2023-03-10")]
    base_dir = tmp_path / "panel_1d_delisted"
    manifest = base_dir / "panel_manifest.sqlite"

    result1 = delisted_panel.fetch_delisted_panel(
        register_rows, base_dir=base_dir, manifest_path=manifest, start_year=2023)
    assert result1["n_fetched"] == 1

    # second run: any network call is a hard failure -- resume must SKIP.
    monkeypatch.setattr(bybit_rest, "fetch_kline_symbol", _fake_kline_raises())
    result2 = delisted_panel.fetch_delisted_panel(
        register_rows, base_dir=base_dir, manifest_path=manifest, start_year=2023)
    assert result2["n_fetched"] == 0
    assert result2["n_skipped_resume"] == 1


def test_fetch_delisted_panel_skipped_no_reference_date_is_named(tmp_path, monkeypatch):
    monkeypatch.setattr(bybit_rest, "fetch_kline_symbol", _fake_kline_raises())
    row = _register_row("NOREFUSDT")
    row["publish_ms"] = None  # neither delisting_ms nor publish_ms -> no reference date at all
    base_dir = tmp_path / "panel_1d_delisted"
    manifest = base_dir / "panel_manifest.sqlite"
    result = delisted_panel.fetch_delisted_panel([row], base_dir=base_dir, manifest_path=manifest)
    assert result["n_skipped_no_reference_date"] == 1
    assert result["skipped_no_reference_symbols"] == ["NOREFUSDT"]


# ============================================================================
# (b) panel_load.load_panel_union -- POSITIVE + ADVERSARIAL
# ============================================================================

def _build_union_fixture(tmp_path):
    """Two survivors (AAAUSDT, ZZZUSDT) alive all of 2023, one delisted
    symbol (MMMUSDT) alive 2023-01-01..2023-07-10 -- interleaved
    alphabetically with the survivors so a "sorted union" test actually
    exercises real interleaving, not just concatenation."""
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    del_base = tmp_path / "panel_1d_delisted"
    del_manifest = del_base / "panel_manifest.sqlite"

    year_end = date(2023, 12, 31)
    _write_full_history(surv_base, surv_manifest, "AAAUSDT",
                         _closes(date(2023, 1, 1), year_end, seed=10), as_of_date=year_end)
    _write_full_history(surv_base, surv_manifest, "ZZZUSDT",
                         _closes(date(2023, 1, 1), year_end, seed=11), as_of_date=year_end)

    delist_date = date(2023, 7, 10)
    _write_full_history(del_base, del_manifest, "MMMUSDT",
                         _closes(date(2023, 1, 1), delist_date, seed=12), as_of_date=delist_date)
    dd = delisted_panel.write_delisting_dates_json(del_base, {
        "MMMUSDT": {"delist_date": delist_date.isoformat(),
                    "announcement_id": "ann-mmmusdt", "source": "delisting_ms"}})

    return surv_base, surv_manifest, del_base, del_manifest, Path(dd["path"]), delist_date


def test_load_panel_union_positive_symbols_sorted_last_alive_day(tmp_path):
    surv_base, surv_manifest, del_base, del_manifest, dd_path, delist_date = _build_union_fixture(tmp_path)

    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2023, year_end=2023, as_of=date(2024, 1, 1),
        delisting_dates_path=dd_path)

    assert panel["symbols"] == ["AAAUSDT", "MMMUSDT", "ZZZUSDT"]  # real global sort, interleaved
    assert list(panel["is_delisted"]) == [False, True, False]
    assert panel["last_alive_day"] == [None, delist_date.isoformat(), None]
    assert panel["n_symbols_survivors"] == 2
    assert panel["n_symbols_delisted"] == 1
    assert panel["delisted_symbols"] == ["MMMUSDT"]


def test_load_panel_union_adversarial_symbol_in_both_trees_is_loud_error(tmp_path):
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    del_base = tmp_path / "panel_1d_delisted"
    del_manifest = del_base / "panel_manifest.sqlite"
    year_end = date(2023, 12, 31)

    _write_full_history(surv_base, surv_manifest, "DUPUSDT",
                         _closes(date(2023, 1, 1), year_end, seed=1), as_of_date=year_end)
    _write_full_history(del_base, del_manifest, "DUPUSDT",
                         _closes(date(2023, 1, 1), date(2023, 6, 1), seed=2),
                         as_of_date=date(2023, 6, 1))
    dd = delisted_panel.write_delisting_dates_json(del_base, {
        "DUPUSDT": {"delist_date": "2023-06-01", "announcement_id": "x", "source": "delisting_ms"}})

    with pytest.raises(panel_load.PanelLoadError, match="DUPUSDT"):
        panel_load.load_panel_union(
            surv_base, surv_manifest, del_base, del_manifest,
            year_start=2023, year_end=2023, as_of=date(2024, 1, 1),
            delisting_dates_path=Path(dd["path"]))


def test_load_panel_union_missing_delisted_manifest_is_loud_error(tmp_path):
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    year_end = date(2023, 12, 31)
    _write_full_history(surv_base, surv_manifest, "AUSDT",
                         _closes(date(2023, 1, 1), year_end, seed=1), as_of_date=year_end)
    with pytest.raises(panel_load.PanelLoadError, match="panel_1d_delisted"):
        panel_load.load_panel_union(
            surv_base, surv_manifest, tmp_path / "panel_1d_delisted",
            tmp_path / "panel_1d_delisted" / "panel_manifest.sqlite",
            year_start=2023, year_end=2023, as_of=date(2024, 1, 1))


# ============================================================================
# (c) weekly_returns_and_mask_union -- delisting-week convention
# ============================================================================

def test_weekly_returns_and_mask_union_alive_ends_at_delisting_week(tmp_path):
    surv_base, surv_manifest, del_base, del_manifest, dd_path, delist_date = _build_union_fixture(tmp_path)
    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2023, year_end=2023, as_of=date(2024, 1, 1), delisting_dates_path=dd_path)

    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    j = weekly["symbols"].index("MMMUSDT")
    delist_week = pit_universe.iso_week_start(delist_date).isoformat()
    t = weekly["weeks"].index(delist_week)

    assert bool(weekly["alive"][t, j]) is True          # last week alive
    if t + 1 < len(weekly["weeks"]):
        assert bool(weekly["alive"][t + 1, j]) is False  # gone the week after
    assert int(weekly["last_week"][j]) == t              # capped exactly there


def test_weekly_returns_and_mask_union_no_return_imputation_vs_naive_overlay(tmp_path):
    """The delisting week's return must be the REAL observed last-price
    return -- contrasted directly against pit_universe.naive_delisting_
    overlay (the module's own deliberately-wrong -100% reference
    estimator, never used in production)."""
    surv_base, surv_manifest, del_base, del_manifest, dd_path, delist_date = _build_union_fixture(tmp_path)
    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2023, year_end=2023, as_of=date(2024, 1, 1), delisting_dates_path=dd_path)
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    j = weekly["symbols"].index("MMMUSDT")
    delist_week = pit_universe.iso_week_start(delist_date).isoformat()
    t = weekly["weeks"].index(delist_week)

    real_return = float(weekly["returns"][t, j])
    assert real_return != pytest.approx(-1.0)   # not the naive -100% overlay's forced value
    assert np.isfinite(real_return)

    naive = pit_universe.naive_delisting_overlay(weekly["returns"], weekly["alive"])
    assert float(naive[t, j]) == pytest.approx(-1.0)         # the WRONG estimator DOES overwrite it
    assert float(naive[t, j]) != pytest.approx(real_return)  # the two must differ
    # every other cell is untouched by naive_delisting_overlay (sanity: it
    # only overwrites each symbol's OWN last alive week).
    assert np.array_equal(naive[:t], weekly["returns"][:t])


def test_weekly_returns_and_mask_union_survivors_are_alive_the_whole_year(tmp_path):
    surv_base, surv_manifest, del_base, del_manifest, dd_path, _delist_date = _build_union_fixture(tmp_path)
    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2023, year_end=2023, as_of=date(2024, 1, 1), delisting_dates_path=dd_path)
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    for sym in ("AAAUSDT", "ZZZUSDT"):
        j = weekly["symbols"].index(sym)
        # alive from MIN_WEEKS_HISTORY weeks in, through the panel's last week
        alive_weeks = np.flatnonzero(weekly["alive"][:, j])
        assert alive_weeks.size > 0
        assert alive_weeks.max() == len(weekly["weeks"]) - 1


# ============================================================================
# (e) census --include-delisted: determinism + survivors-only byte-identity
# ============================================================================

def _build_small_census_trees(tmp_path, *, with_delisted: bool):
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    year_end = date(2023, 12, 31)
    n_symbols = 20
    statuses = {}
    for i in range(n_symbols):
        sym = f"SURV{i:03d}USDT"
        _write_full_history(surv_base, surv_manifest, sym,
                             _closes(date(2023, 1, 1), year_end, seed=100 + i), as_of_date=year_end)
        statuses[sym] = "Trading"

    del_base = del_manifest = dd_path = None
    if with_delisted:
        del_base = tmp_path / "panel_1d_delisted"
        del_manifest = del_base / "panel_manifest.sqlite"
        dd_entries = {}
        for i in range(3):
            sym = f"DEL{i:03d}USDT"
            delist_date = date(2023, 4, 1 + i * 10)
            _write_full_history(del_base, del_manifest, sym,
                                 _closes(date(2023, 1, 1), delist_date, seed=200 + i),
                                 as_of_date=delist_date)
            dd_entries[sym] = {"delist_date": delist_date.isoformat(),
                                "announcement_id": f"ann-{sym.lower()}", "source": "delisting_ms"}
        dd_path = Path(delisted_panel.write_delisting_dates_json(del_base, dd_entries)["path"])
    return surv_base, surv_manifest, del_base, del_manifest, dd_path, statuses


def test_census_include_delisted_deterministic_same_seed(tmp_path, monkeypatch):
    surv_base, _sm, del_base, _dm, dd_path, statuses = _build_small_census_trees(tmp_path, with_delisted=True)
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    out = tmp_path / "out"
    reports = []
    for _ in range(2):
        a = _ns_census(panel_base=str(surv_base), out=str(out), include_delisted=True,
                        delisted_base=str(del_base), delisting_dates=str(dd_path), seed=53)
        rc = CENSUS.cmd_census(a)
        assert rc == 0
        reports.append(json.loads((out / "wp7_report.json").read_text()))
    assert reports[0] == reports[1]

    b3 = reports[0]["findings"]["b3"]
    sbias = b3["survivorship_bias"]
    assert sbias["n_with_history"] == 3
    assert sbias["bias_ic_union_minus_survivors"] is not None
    assert "KEIN PASS/FAIL" in sbias["threshold_note"]
    assert reports[0]["extra"]["delisted"]["n_with_history"] == 3


def test_census_survivors_only_byte_identical_when_include_delisted_absent(tmp_path, monkeypatch):
    """The pre-WP-12b test-file shape (a Namespace WITHOUT
    ``include_delisted`` at all) and the post-WP-12b shape
    (``include_delisted=False`` explicit) must give the EXACT SAME
    report -- the WP-12b union path must never fire when the flag is off,
    however the caller's namespace happens to be built."""
    surv_base, _sm, _db, _dmf, _dd, statuses = _build_small_census_trees(tmp_path, with_delisted=False)
    monkeypatch.setattr(bybit_rest, "fetch_instruments", _fake_instruments(statuses))
    monkeypatch.setattr(bybit_rest, "fetch_tickers", _fake_tickers())

    # old-style namespace: no include_delisted / delisted_base / etc. at all
    old_style = dict(
        panel_base=str(surv_base), category="linear", start_year=2023, end_year=2023,
        out="", seed=53, allow_partial=False, as_of="2023-12-31",
        dates="", harvest_base="data/harvest",
        bar_cache_dir="", corr_start="", corr_end="", corr_seed=53,
    )

    # SAME out dir for both runs (mirrors the repo's own determinism-test
    # pattern) -- artifact paths inside the report embed out_dir, so a
    # meaningful byte-identity check needs that held constant, not just
    # the statistics.
    out = tmp_path / "out"
    a1 = argparse.Namespace(**{**old_style, "out": str(out)})
    rc1 = CENSUS.cmd_census(a1)
    assert rc1 == 0
    r1 = json.loads((out / "wp7_report.json").read_text())

    a2 = _ns_census(panel_base=str(surv_base), out=str(out), include_delisted=False)
    rc2 = CENSUS.cmd_census(a2)
    assert rc2 == 0
    r2 = json.loads((out / "wp7_report.json").read_text())
    assert r1 == r2
    assert "delisted" not in r1["extra"]
    assert "survivorship_bias" not in r1["findings"]["b3"]


# ============================================================================
# (f) monkeypatched end-to-end --fetch-delisted-panel CLI, no network
# ============================================================================

def test_cli_fetch_delisted_panel_end_to_end_no_network(tmp_path, monkeypatch):
    start, delist = date(2023, 1, 1), date(2023, 5, 20)
    rows = _kline_rows(start, delist, seed=3)
    monkeypatch.setattr(bybit_rest, "fetch_kline_symbol", _fake_kline_fetcher({"CLIUSDT": rows}))
    monkeypatch.setattr(bybit_rest, "fetch_funding_history", _fake_funding_empty())

    register_dir = tmp_path / "delisting_register"
    delisted_base = tmp_path / "panel_1d_delisted"
    register_rows = [_register_row("CLIUSDT", delist_iso="2023-05-20")]
    announcements.write_register_parquet(register_rows, register_dir / "register.parquet")

    a = argparse.Namespace(register_base=str(register_dir), delisted_panel_base=str(delisted_base),
                            start_year=2023, category="linear")
    rc = WP12.cmd_fetch_delisted_panel(a)
    assert rc == 0

    manifest = delisted_base / "panel_manifest.sqlite"
    row = panel_store.manifest_get(manifest, "CLIUSDT", 2023)
    assert row["status"] == "DONE"
    assert (delisted_base / "delisting_dates.json").is_file()
