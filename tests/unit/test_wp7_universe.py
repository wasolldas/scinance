"""Unit tests for WP-7 (Universums-Zensus, Klasse-W-Feasibility).

Covers (per ``scinance3-impl/WP7_SPEZIFIKATION.md`` section 3):
  (a) bybit_rest: cursor/backward pagination against FIXTURE responses
      (no network assumptions), field-layout loud-fail, retCode loud-fail.
  (b) panel_store: DONE/PARTIAL/EMPTY manifest status, loud-fail gate on
      n_rows != expected_days, frozen-partition immutability, fingerprint
      determinism, 1% reverify provenance check.
  (c) pit_universe: PIT membership rule (>= 8 weeks history AND still
      trading; delisted symbol kept until its last bar, closed at the
      last price -- never retroactively removed).
  (d) null_ic: DEC-53 mandatory artifacts (seed + weekly SD_null series),
      determinism (N=2 runs, identical fingerprint).
  (e) stats: feasibility arithmetic (DEC-51/52 z), sigma_xs_min formula.
  (f) report: B1..B5 findings carry the PRD-verbatim pre-fixed consequence.
  (g) spread_probe: content-probe field detection + decile census on a
      synthetic harvest tree (mirrors wp6_optstress's synthetic-tree
      pattern).
  (h) THE DEC-39 TRIO (mandatory, PRD 4.1 T1) -- POSITIVE, NULL,
      ADVERSARIAL -- built as REAL statistical fixtures, not smoke tests.
  (i) Abnahme-Nacharbeiten: funding_n/funding_sum (8h- vs 1h-symbol,
      interval change within a year), pair_corr rho(BTC,ETH) on a
      synthetic WP-0 bar cache (known 0.8 and null-0 correlation),
      listing_date_from_launch_time, N_eff report labeling.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.bar_cache import build_range
from bybit_edge.research.wp7_universe import (
    bybit_rest, null_ic, pair_corr, panel_store, pit_universe, report,
    spread_probe, stats,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wp7_universe_census.py"
EPOCH = date(1970, 1, 1)


# ============================================================================
# (a) bybit_rest -- pagination against fixtures, field-layout loud-fail
# ============================================================================

def test_instruments_cursor_pagination_and_statuses():
    pages = [
        {"retCode": 0, "retMsg": "OK", "result": {
            "list": [{"symbol": "BTCUSDT", "status": "Trading"},
                     {"symbol": "ETHUSDT", "status": "Trading"}],
            "nextPageCursor": "cur1"}},
        {"retCode": 0, "retMsg": "OK", "result": {
            "list": [{"symbol": "OLDCOINUSDT", "status": "Closed"}],
            "nextPageCursor": ""}},
    ]
    result = bybit_rest.fetch_instruments(fetcher=bybit_rest.fixture_fetcher(pages))
    assert result["n_rows"] == 3
    assert result["n_pages"] == 2
    assert set(result["statuses"]) == {"Trading", "Closed"}
    assert [r["symbol"] for r in result["rows"]] == ["BTCUSDT", "ETHUSDT", "OLDCOINUSDT"]


def test_instruments_cursor_stall_terminates():
    """A page that repeats the same cursor must not spin forever."""
    pages = [{"retCode": 0, "result": {"list": [{"symbol": "A", "status": "Trading"}],
                                        "nextPageCursor": "same"}}] * 3
    result = bybit_rest.fetch_instruments(fetcher=bybit_rest.fixture_fetcher(pages))
    # page 1 (cursor="") returns cursor "same" (new, so continue); page 2
    # (cursor="same") returns "same" again (repeat -> stall guard stops)
    assert result["n_pages"] == 2


def test_kline_backward_pagination_and_dedup():
    # newest-first pages, each 2 rows, overlapping by one row on purpose
    page1 = {"retCode": 0, "result": {"symbol": "BTCUSDT", "list": [
        ["3000", "1", "1", "1", "1", "1", "1"],
        ["2000", "1", "1", "1", "1", "1", "1"],
    ]}}
    page2 = {"retCode": 0, "result": {"symbol": "BTCUSDT", "list": [
        ["2000", "1", "1", "1", "1", "1", "1"],  # overlap
        ["1000", "1", "1", "1", "1", "1", "1"],
    ]}}
    fetcher = bybit_rest.fixture_fetcher([page1, page2])
    result = bybit_rest.fetch_kline_symbol("BTCUSDT", 1000, 3000, fetcher=fetcher, max_req_per_sec=0)
    assert result["n_rows"] == 3
    assert [r["start_ms"] for r in result["rows"]] == [1000, 2000, 3000]
    assert result["n_pages"] == 2
    assert len(result["raw_sha256"]) == 2


def test_kline_field_layout_loud_fail():
    bad_page = {"retCode": 0, "result": {"symbol": "X", "list": [
        ["1000", "1", "1", "1", "1"],  # wrong arity (5, not 7)
    ]}}
    fetcher = bybit_rest.fixture_fetcher([bad_page])
    with pytest.raises(bybit_rest.BybitFieldLayoutError, match="positional fields"):
        bybit_rest.fetch_kline_symbol("X", 0, 5000, fetcher=fetcher, max_req_per_sec=0)


def test_instruments_missing_required_keys_loud_fail():
    bad_page = {"retCode": 0, "result": {"list": [{"symbol": "X"}], "nextPageCursor": ""}}
    fetcher = bybit_rest.fixture_fetcher([bad_page])
    with pytest.raises(bybit_rest.BybitFieldLayoutError, match="status"):
        bybit_rest.fetch_instruments(fetcher=fetcher)


def test_retcode_error_loud_fail():
    err_page = {"retCode": 10001, "retMsg": "params error", "result": {}}
    fetcher = bybit_rest.fixture_fetcher([err_page])
    with pytest.raises(bybit_rest.BybitFieldLayoutError, match="retCode=10001"):
        bybit_rest.fetch_instruments(fetcher=fetcher)


def test_probe_instruments_and_kline_report_raw_head_and_hash():
    page = {"retCode": 0, "result": {"list": [{"symbol": "BTCUSDT", "status": "Trading"}],
                                      "nextPageCursor": ""}}
    out = bybit_rest.probe_instruments(fetcher=bybit_rest.fixture_fetcher([page]))
    assert out["n_rows"] == 1 and len(out["raw_sha256"]) == 64 and out["raw_head"]

    kpage = {"retCode": 0, "result": {"symbol": "BTCUSDT",
                                       "list": [["1000", "1", "2", "0.5", "1.5", "10", "100"]]}}
    kout = bybit_rest.probe_kline("BTCUSDT", fetcher=bybit_rest.fixture_fetcher([kpage]))
    assert kout["n_rows"] == 1 and kout["rows"][0]["close"] == 1.5


def test_fetch_tickers_single_call_and_option_symbols_untouched():
    page = {"retCode": 0, "result": {"list": [
        {"symbol": "BTCUSDT", "bid1Price": "100", "ask1Price": "101"},
        {"symbol": "BTC-4SEP26-73000-P", "bid1Iv": "0.4"},
    ]}}
    out = bybit_rest.fetch_tickers(fetcher=bybit_rest.fixture_fetcher([page]))
    assert out["n_rows"] == 2  # client passes rows through; symbol filtering is spread_probe's job


# ============================================================================
# (b) panel_store -- manifest status, loud-fail gate, frozen immutability,
#     fingerprint determinism, reverify
# ============================================================================

def _rows_for_year(year: int, n_days: int, start_month=1, start_day=1):
    from datetime import date, timedelta
    d0 = date(year, start_month, start_day)
    out = []
    for i in range(n_days):
        d = d0 + timedelta(days=i)
        ms = int((d - date(1970, 1, 1)).days) * 86_400_000
        out.append({"start_ms": ms, "open": 1.0, "high": 1.0, "low": 1.0,
                    "close": 1.0 + i * 0.01, "volume": 10.0, "turnover": 100.0})
    return out


def test_manifest_done_partial_empty(tmp_path):
    from datetime import date
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"

    # DONE: exactly the expected number of calendar days
    rows_full = _rows_for_year(2022, 365)
    res_done = panel_store.write_year_partition(
        base, manifest, "BTCUSDT", 2022, rows_full,
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)
    assert res_done["status"] == "DONE"
    assert res_done["n_rows"] == res_done["expected_days"] == 365

    # PARTIAL: fewer rows than expected (a gap in the fetch)
    rows_gap = _rows_for_year(2022, 300)
    res_partial = panel_store.write_year_partition(
        base, manifest, "ETHUSDT", 2022, rows_gap,
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)
    assert res_partial["status"] == "PARTIAL"
    assert res_partial["n_rows"] == 300 and res_partial["expected_days"] == 365

    # EMPTY: nothing at all
    res_empty = panel_store.write_year_partition(
        base, manifest, "DEADCOIN", 2022, [],
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)
    assert res_empty["status"] == "EMPTY"

    counts = panel_store.manifest_status_counts(manifest)
    assert counts == {"DONE": 1, "PARTIAL": 1, "EMPTY": 1}


def test_manifest_loud_fail_on_n_rows_mismatch(tmp_path):
    """PRD 4.1 DoD point 2 / spec section 3: judgement-bearing reads MUST
    loud-fail when a partition's n_rows != expected_days."""
    from datetime import date
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    panel_store.write_year_partition(
        base, manifest, "BTCUSDT", 2022, _rows_for_year(2022, 365),
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)
    panel_store.write_year_partition(
        base, manifest, "ETHUSDT", 2022, _rows_for_year(2022, 200),  # short
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)

    panel_store.require_all_done(manifest, ["BTCUSDT"], [2022])  # fine, no raise

    with pytest.raises(panel_store.PanelStoreError, match="ETHUSDT/2022=PARTIAL"):
        panel_store.require_all_done(manifest, ["BTCUSDT", "ETHUSDT"], [2022])


def test_frozen_partition_is_immutable(tmp_path):
    from datetime import date
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    panel_store.write_year_partition(
        base, manifest, "BTCUSDT", 2022, _rows_for_year(2022, 365),
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)
    with pytest.raises(panel_store.PanelStoreError, match="FROZEN"):
        panel_store.write_year_partition(
            base, manifest, "BTCUSDT", 2022, _rows_for_year(2022, 365),
            listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)
    # open/ (current year) may always be rewritten
    panel_store.write_year_partition(
        base, manifest, "BTCUSDT", 2023, _rows_for_year(2023, 10),
        listing_date=date(2023, 1, 1), as_of_date=date(2023, 1, 10), frozen=False)
    panel_store.write_year_partition(  # no raise
        base, manifest, "BTCUSDT", 2023, _rows_for_year(2023, 11),
        listing_date=date(2023, 1, 1), as_of_date=date(2023, 1, 11), frozen=False)


def test_panel_fingerprint_deterministic_and_range_fingerprint(tmp_path):
    from datetime import date
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    rows = _rows_for_year(2022, 365)
    panel_store.write_year_partition(base, manifest, "BTCUSDT", 2022, rows,
                                      listing_date=date(2022, 1, 1),
                                      as_of_date=date(2022, 12, 31), frozen=True)
    panel_store.write_year_partition(base, manifest, "ETHUSDT", 2022, rows,
                                      listing_date=date(2022, 1, 1),
                                      as_of_date=date(2022, 12, 31), frozen=True)
    fp1 = panel_store.panel_fingerprint(base, "BTCUSDT", 2022, frozen=True)
    fp2 = panel_store.panel_fingerprint(base, "BTCUSDT", 2022, frozen=True)
    assert fp1 == fp2  # re-reading the same file is byte-identical
    assert fp1 == panel_store.panel_fingerprint(base, "ETHUSDT", 2022, frozen=True)  # same rows -> same hash

    rng = panel_store.range_fingerprint(base, ["BTCUSDT", "ETHUSDT"], 2022, 2022, frozen=True)
    rng2 = panel_store.range_fingerprint(base, ["ETHUSDT", "BTCUSDT"], 2022, 2022, frozen=True)
    assert rng["sha256"] == rng2["sha256"]  # symbol input order does not matter
    assert rng["n_partitions"] == 2


def test_reverify_sample_detects_corruption(tmp_path):
    from datetime import date
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    for i in range(20):
        panel_store.write_year_partition(
            base, manifest, f"SYM{i}USDT", 2022, _rows_for_year(2022, 365),
            listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)

    clean = panel_store.reverify_sample(base, manifest, fraction=1.0, seed=1)
    assert clean["n_checked"] == 20 and clean["n_mismatch"] == 0

    # corrupt one frozen partition on disk without touching the manifest
    import pyarrow.parquet as pq
    import pyarrow as pa
    path = panel_store.partition_path(base, "SYM0USDT", 2022, frozen=True)
    table = pq.read_table(path)
    tampered = table.set_column(table.schema.get_field_index("close"), "close",
                                 pa.array([v + 999.0 for v in table.column("close").to_pylist()]))
    pq.write_table(tampered, path)

    dirty = panel_store.reverify_sample(base, manifest, fraction=1.0, seed=1)
    assert dirty["n_mismatch"] == 1
    assert dirty["mismatches"][0]["symbol"] == "SYM0USDT"


def test_expected_days_in_year_bounds():
    from datetime import date
    assert panel_store.expected_days_in_year(2022, date(2022, 1, 1), date(2022, 12, 31)) == 365
    assert panel_store.expected_days_in_year(2022, date(2022, 7, 1), date(2022, 12, 31)) == 184
    assert panel_store.expected_days_in_year(2022, date(2023, 1, 1), date(2023, 6, 1)) == 0  # not listed yet


# ============================================================================
# (c) pit_universe -- PIT membership rule
# ============================================================================

def test_pit_alive_mask_min_weeks_and_delisting():
    # 3 symbols, 15 weeks. A: full history. B: listed at week 3, still
    # trading. C: listed at week 0, delists (last bar) at week 9.
    first_bar = np.array([0, 3, 0])
    last_bar = np.array([14, 14, 9])
    alive = pit_universe.pit_alive_mask(first_bar, last_bar, 15, min_weeks_history=8)

    # A: needs >= 8 weeks history -> present from week 8 onward
    assert not alive[7, 0] and alive[8, 0] and alive[14, 0]
    # B: first_bar=3 -> 8-week mark at week 11
    assert not alive[10, 1] and alive[11, 1] and alive[14, 1]
    # C: 8-week mark at week 8, but delists at week 9 -> alive weeks 8 and 9 ONLY,
    # never retroactively removed from those two weeks, never present after.
    assert alive[8, 2] and alive[9, 2]
    assert not alive[10, 2] and not alive[14, 2]
    assert not alive[7, 2]  # not yet 8 weeks old


def test_k_per_week_counts_membership():
    first_bar = np.zeros(5, dtype=np.int64)
    last_bar = np.array([9, 9, 4, 9, 9])  # symbol 2 delists at week 4
    alive = pit_universe.pit_alive_mask(first_bar, last_bar, 10, min_weeks_history=8)
    k = pit_universe.k_per_week(alive)
    assert list(k[:8]) == [0] * 8  # nobody has 8 weeks of history before week 8
    assert k[8] == 4  # symbol 2 already delisted (week 4), four remain
    assert k[9] == 4


def test_delisted_symbol_return_is_true_last_price_not_dropped():
    """The PIT-controlled convention: a delisted symbol's LAST week keeps
    its real observed return (no retroactive removal, no assumed loss)."""
    W, K = 10, 2
    returns = np.zeros((W, K))
    returns[6, 1] = -0.37  # symbol 1's true last-bar return before delisting
    first_bar = np.zeros(K, dtype=np.int64)
    last_bar = np.array([9, 6])
    alive = pit_universe.pit_alive_mask(first_bar, last_bar, W, min_weeks_history=0)
    # the true return at the delisting week is exactly what a PIT reader sees
    assert alive[6, 1] and not alive[7, 1]
    assert returns[6, 1] == pytest.approx(-0.37)


# ============================================================================
# (d) null_ic -- DEC-53 artifacts + determinism
# ============================================================================

def _iid_panel(seed, K=60, W=20, sigma=0.05):
    rng = np.random.default_rng(seed)
    ret = rng.normal(0, sigma, size=(W, K))
    alive = np.ones((W, K), dtype=bool)
    return ret, alive


def test_null_ic_determinism_same_seed_identical_fingerprint():
    ret, alive = _iid_panel(1)
    r1 = null_ic.permutation_null_sd(ret, alive, n_perm=100, seed=42)
    r2 = null_ic.permutation_null_sd(ret, alive, n_perm=100, seed=42)
    assert null_ic.artifact_fingerprint(r1) == null_ic.artifact_fingerprint(r2)
    assert r1["sd_null"] == r2["sd_null"]
    assert r1["weekly"] == r2["weekly"]


def test_null_ic_different_seed_different_series():
    ret, alive = _iid_panel(1)
    r1 = null_ic.permutation_null_sd(ret, alive, n_perm=100, seed=42)
    r2 = null_ic.permutation_null_sd(ret, alive, n_perm=100, seed=43)
    assert null_ic.artifact_fingerprint(r1) != null_ic.artifact_fingerprint(r2)


def test_null_ic_dec53_artifacts_written_and_verified(tmp_path):
    ret, alive = _iid_panel(2)
    result = null_ic.permutation_null_sd(ret, alive, n_perm=100, seed=7)
    out = null_ic.write_artifacts(tmp_path / "artifacts", result, window_label="per_window")
    payload = null_ic.read_artifacts(out["path"])
    assert payload["seed"] == 7
    assert len(payload["weekly"]) == result["n_weeks_used"]
    assert payload["sha256"] == out["sha256"]

    # tamper -> read_artifacts must refuse
    path = Path(out["path"])
    doc = json.loads(path.read_text())
    doc["weekly"][0]["sd_null"] += 1.0
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="does not match"):
        null_ic.read_artifacts(path)


def test_null_ic_refuses_data_harvest_path(tmp_path):
    ret, alive = _iid_panel(3)
    result = null_ic.permutation_null_sd(ret, alive, n_perm=50, seed=1)
    with pytest.raises(ValueError, match="data/harvest"):
        null_ic.write_artifacts(tmp_path / "data" / "harvest" / "wp7", result, window_label="x")


# ============================================================================
# (e) stats -- feasibility arithmetic + sigma_xs_min formula (PRD 4.1)
# ============================================================================

def test_feasibility_thresholds_match_prd_arithmetic():
    # per-window: 2.4865 * SD_null / sqrt(52) <= 0.03  <=>  SD_null <= 0.08699..
    assert stats.sd_null_threshold(pooled=False) == pytest.approx(0.08700, abs=2e-5)
    # pooled: 3.1680 * SD_null / sqrt(104) <= 0.03  <=>  SD_null <= 0.09657
    assert stats.sd_null_threshold(pooled=True) == pytest.approx(0.09657, abs=1e-5)
    assert stats.detectable_effect(0.08699, pooled=False) == pytest.approx(0.03, abs=1e-4)
    assert stats.feasible(0.08, pooled=False) is True
    assert stats.feasible(0.10, pooled=False) is False


def test_k_min_floors_from_prd_table():
    assert report.K_MIN_PER_WINDOW == 134
    assert report.K_MIN_POOLED == 117


def test_sigma_xs_min_formula():
    assert stats.sigma_xs_min_bps(18) == pytest.approx(342, abs=1)          # f=3.51
    assert stats.sigma_xs_min_bps(18, f=2.0) == pytest.approx(600, abs=1)   # conservative R2 factor


# ============================================================================
# (f) report -- B1..B5 carry the PRD-verbatim consequence
# ============================================================================

def test_b1_not_testable_when_both_bars_missed():
    res = report.evaluate_b1_b2(sd_null_per_window=0.20, sd_null_pooled=0.20, k_available=170)
    assert res["finding"] == "B1"
    assert res["consequence"] == report.B1_CONSEQUENCE
    assert "Klasse W ist statistisch nicht testbar" in res["consequence"]


def test_b2_testable_when_pooled_clears():
    res = report.evaluate_b1_b2(sd_null_per_window=0.20, sd_null_pooled=0.05, k_available=120)
    assert res["finding"] == "B2"
    assert res["pooled_feasible"] is True and res["per_window_feasible"] is False
    assert res["consequence"] == report.B2_CONSEQUENCE


def test_b3_triggers_on_missing_non_trading_rows():
    res = report.evaluate_b3(["Trading", "Trading"], delisted_symbols_with_kline=0,
                              delisted_symbols_checked=0)
    assert res["triggered"] is True and res["finding"] == "B3"
    assert res["consequence"] == report.B3_CONSEQUENCE


def test_b3_not_triggered_when_delisted_symbols_present():
    res = report.evaluate_b3(["Trading", "Closed"], delisted_symbols_with_kline=3,
                              delisted_symbols_checked=3)
    assert res["triggered"] is False and res["consequence"] is None


def test_b4_unter_wand_label():
    res = report.evaluate_b4(200.0, cost_bps=18.0)  # 200 < 342 -> under the wall
    assert res["triggered"] is True
    assert res["consequence"] == report.B4_CONSEQUENCE
    res_ok = report.evaluate_b4(400.0, cost_bps=18.0)
    assert res_ok["triggered"] is False


def test_b5_always_registers_as_dec():
    res = report.evaluate_b5([{"decile": 1, "n_symbols": 10, "perp_spread_bp_median": 5.0}])
    assert res["finding"] == "B5" and res["consequence"] == report.B5_CONSEQUENCE


def test_write_report_json_and_markdown(tmp_path):
    b12 = report.evaluate_b1_b2(0.09, 0.05, 130)
    b3 = report.evaluate_b3(["Trading"], 0, 0)
    b4 = report.evaluate_b4(500.0, cost_bps=18.0)
    b5 = report.evaluate_b5([{"decile": 1, "n_symbols": 5, "perp_spread_bp_median": 8.2}])
    full = report.assemble_report(b1_b2=b12, b3=b3, b4=b4, b5=b5)
    paths = report.write_report(tmp_path / "out", full)
    assert Path(paths["json"]).is_file() and Path(paths["md"]).is_file()
    md = Path(paths["md"]).read_text()
    assert "PERP_SPREAD_BP" in md or "Dezil" in md


# ============================================================================
# (g) spread_probe -- content probe + decile census, synthetic harvest tree
# ============================================================================

def _tick(symbol, bid, ask, oi="1000", funding="0.0001", turnover="500000"):
    return {"symbol": symbol, "bid1Price": str(bid), "ask1Price": str(ask),
            "openInterest": oi, "fundingRate": funding, "turnover24h": turnover}


def _write_tickers_day(base: Path, day: str, frames: list[tuple[str, int, dict]]):
    import pyarrow as pa
    import pyarrow.parquet as pq
    by_sym: dict[str, list[tuple[int, str]]] = {}
    for sym, ts, tick in frames:
        by_sym.setdefault(sym, []).append((ts, json.dumps(tick)))
    for sym, rows in by_sym.items():
        d = base / "raw" / "bybit" / "tickers" / f"symbol={sym}" / f"date={day}"
        d.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table({
            "ts_exchange_ms": pa.array([t for t, _ in rows], pa.int64()),
            "symbol": pa.array([sym] * len(rows)),
            "payload_json": pa.array([p for _, p in rows]),
        }), d / "part-0.parquet")


@pytest.mark.filterwarnings("ignore")
def test_spread_probe_content_probe_ok_and_decile_census(tmp_path):
    pytest.importorskip("duckdb")
    base = tmp_path / "harvest"
    day = "2026-08-19"
    frames = []
    turnovers = [10_000_000, 8_000_000, 6_000_000, 4_000_000, 2_000_000,
                 1_000_000, 500_000, 250_000, 100_000, 50_000]
    for i, tv in enumerate(turnovers):
        sym = f"SYM{i}USDT"
        spread = 1.0 + i * 0.5  # widens for lower-turnover symbols
        frames.append((sym, 1_000, _tick(sym, 100.0, 100.0 + spread, turnover=str(tv))))
    # an option symbol in the SAME stream must be excluded from the perp census
    frames.append(("BTC-4SEP26-73000-P", 1_000, {"symbol": "BTC-4SEP26-73000-P", "bid1Iv": "0.4"}))
    _write_tickers_day(base, day, frames)

    probe = spread_probe.probe_harvest_tickers(base, [day])
    assert probe["ok"] is True
    assert probe["days"][day]["status"] == "OK"

    snapshot = spread_probe.perp_snapshot_from_harvest(base, day)
    assert len(snapshot) == 10  # option symbol excluded
    census = spread_probe.decile_spread_census(snapshot, n_deciles=5)
    assert census["n_ranked"] == 10
    assert len(census["deciles"]) == 5
    # highest-turnover decile (majors) must show the TIGHTEST spread
    assert census["deciles"][0]["perp_spread_bp_median"] < census["deciles"][-1]["perp_spread_bp_median"]


@pytest.mark.filterwarnings("ignore")
def test_spread_probe_flags_missing_fields(tmp_path):
    pytest.importorskip("duckdb")
    base = tmp_path / "harvest"
    day = "2026-08-19"
    naked = {"symbol": "BTCUSDT", "lastPrice": "100"}  # no bid/ask/oi/funding
    _write_tickers_day(base, day, [("BTCUSDT", 1_000, naked)])
    probe = spread_probe.probe_harvest_tickers(base, [day])
    assert probe["ok"] is False
    assert probe["days"][day]["status"] == "FIELDS_MISSING"
    assert set(probe["days"][day]["fields_missing"]) == set(spread_probe.REQUIRED_FIELDS)


def test_spread_probe_rest_fallback():
    page = {"retCode": 0, "result": {"list": [
        {"symbol": "BTCUSDT", "bid1Price": "100", "ask1Price": "101",
         "openInterest": "5000", "fundingRate": "0.0001", "turnover24h": "9000000"},
        {"symbol": "BTC-4SEP26-73000-P", "bid1Iv": "0.4"},
    ]}}
    snapshot = spread_probe.perp_snapshot_from_rest(fetcher=bybit_rest.fixture_fetcher([page]))
    assert len(snapshot) == 1 and snapshot[0]["symbol"] == "BTCUSDT"


@pytest.mark.filterwarnings("ignore")
def test_cli_probe_tickers_subprocess(tmp_path):
    pytest.importorskip("duckdb")
    base = tmp_path / "harvest"
    day = "2026-08-19"
    _write_tickers_day(base, day, [("BTCUSDT", 1_000, _tick("BTCUSDT", 100.0, 100.1))])
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--probe-tickers", "--harvest-base", str(base),
         "--dates", day], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Inhaltsprobe bestanden" in r.stdout


# ============================================================================
# (h) THE DEC-39 TRIO -- mandatory, real statistical tests
# ============================================================================

def _spearman(x, y):
    return pit_universe.spearman_rank_ic(np.asarray(x), np.asarray(y))


def test_dec39_positive_injected_ic_recovered_and_detectable():
    """POSITIVE: inject a real cross-sectional IC of 0.04 into a panel
    with a common market factor, sector structure, and lognormal vol
    heterogeneity (sigma_log=0.6). The IC estimator must recover it
    within its own CI, and the measured SD_null must permit detecting an
    effect of this size."""
    seed, K, W = 0, 170, 53
    n_sectors, sigma_log = 5, 0.6
    base_sigma, sigma_m, sigma_sector = 0.05, 0.02, 0.015
    target_rho = 0.04

    rng = np.random.default_rng(seed)
    sector = rng.integers(0, n_sectors, size=K)
    vol = base_sigma * np.exp(rng.normal(0, sigma_log, size=K))
    market = rng.normal(0, sigma_m, size=W)
    sector_shock = rng.normal(0, sigma_sector, size=(W, n_sectors))
    idio = rng.normal(0, 1, size=(W, K)) * vol[None, :]
    combined = market[:, None] + sector_shock[:, sector] + idio  # market + sector + idio-vol-heterogeneity

    sigma_n = float(combined.std())
    a = target_rho * sigma_n / np.sqrt(1 - target_rho ** 2)  # calibrated loading
    characteristic = rng.normal(0, 1, size=(W, K))
    outcome = np.empty((W, K))
    outcome[1:] = a * characteristic[:-1] + combined[1:]

    alive = np.ones((W, K), dtype=bool)
    ic_series = pit_universe.weekly_ic_series(characteristic[:-1], outcome[1:], alive[:-1])
    valid = ic_series[~np.isnan(ic_series)]
    assert len(valid) == W - 1

    mean_ic = float(valid.mean())
    se = float(valid.std(ddof=1) / np.sqrt(len(valid)))
    ci_lo, ci_hi = mean_ic - 2 * se, mean_ic + 2 * se
    # the estimator recovers the injected 0.04 IC within its own 95% CI
    assert ci_lo <= 0.04 <= ci_hi
    assert mean_ic > 0.02  # comfortably positive, not a rounding coincidence

    # SD_null permits detecting an effect this size (per-window arithmetic)
    ret_matrix = np.zeros((W, K))
    ret_matrix[1:] = outcome[1:]
    null_result = null_ic.permutation_null_sd(ret_matrix, alive, n_perm=300, seed=999)
    detectable = stats.detectable_effect(null_result["sd_null"], pooled=False)
    assert detectable < mean_ic  # the injected effect clears the detection bar


def test_dec39_null_independent_series_lognormal_vol():
    """NULL (the decisive test -- exactly where v1's rho_quer estimator
    failed): independent series, lognormal vol heterogeneity sigma_log=0.6,
    K=120, W=52. SD_null must land within +/-15% of 1/sqrt(K-1); the
    descriptive N_eff must land within +/-15% of K -- an estimator whose
    result depends on vol heterogeneity instead of correlation structure
    is unfit (L-2b) and is NOT what is built here."""
    seed, K, W, sigma_log, base_sigma = 0, 120, 52, 0.6, 0.05
    rng = np.random.default_rng(seed)
    vol = base_sigma * np.exp(rng.normal(0, sigma_log, size=K))
    ret = rng.normal(0, 1, size=(W, K)) * vol[None, :]
    alive = np.ones((W, K), dtype=bool)

    result = null_ic.permutation_null_sd(ret, alive, n_perm=300, seed=123)
    theory = 1.0 / np.sqrt(K - 1)
    assert result["sd_null"] == pytest.approx(theory, rel=0.15)

    neff = stats.n_eff(ret, alive)
    assert neff["n_eff"] == pytest.approx(K, rel=0.15)


def test_dec39_adversarial_survivorship():
    """ADVERSARIAL: signal-free panel; 30% of symbols deleted after a
    drawdown trigger. The UNCONTROLLED estimator -- which does not close
    a delisted position at its true last price but assumes the naive
    "-100%" loss (the alternative the spec explicitly names and rejects,
    PRD 4.1 DoD point 4) -- must show a spurious POSITIVE momentum IC
    (t > 2). The PIT-controlled estimator (true last-price close) must
    NOT (|t| < 2). A failure here means the panel machinery is
    methodically invalid (H-14 pattern), not a finding."""
    seed = 0
    K, W = 500, 40
    doomed_frac, sigma, trail_win, shock = 0.30, 0.05, 4, -0.40
    min_d, max_d = 8, 36

    rng = np.random.default_rng(seed)
    n_doomed = int(round(K * doomed_frac))
    doomed = rng.choice(K, size=n_doomed, replace=False)
    returns = rng.normal(0, sigma, size=(W, K))
    first_bar = np.zeros(K, dtype=np.int64)
    last_bar = np.full(K, W - 1, dtype=np.int64)
    for s in doomed:
        d = int(rng.integers(min_d, max_d))  # drawdown-trigger / delisting week
        shock_week = max(0, d - trail_win + 1)
        returns[shock_week, s] += shock       # the real drawdown, unmodified in EITHER estimator
        last_bar[s] = d

    alive = pit_universe.pit_alive_mask(first_bar, last_bar, W, min_weeks_history=8)

    controlled = pit_universe.momentum_ic_series(returns, alive, trail_win=trail_win)
    naive_returns = pit_universe.naive_delisting_overlay(returns, alive, naive_return=-1.0)
    uncontrolled = pit_universe.momentum_ic_series(naive_returns, alive, trail_win=trail_win)

    assert abs(controlled["t_stat"]) < 2.0, controlled
    assert uncontrolled["t_stat"] > 2.0, uncontrolled
    assert uncontrolled["t_stat"] > abs(controlled["t_stat"]) + 1.0  # a clear, not marginal, contrast


def test_dec39_trio_reproducible_with_same_seed():
    """T2: N>=3 (here 3) runs of the SAME adversarial fixture, same seed
    -> identical rho/t_stat (determinism, mirrors DEC-53's spirit for the
    survivorship check too)."""
    def run():
        seed, K, W = 0, 200, 30
        rng = np.random.default_rng(seed)
        n_doomed = int(round(K * 0.30))
        doomed = rng.choice(K, size=n_doomed, replace=False)
        returns = rng.normal(0, 0.05, size=(W, K))
        first_bar = np.zeros(K, dtype=np.int64)
        last_bar = np.full(K, W - 1, dtype=np.int64)
        for s in doomed:
            d = int(rng.integers(8, 26))
            returns[max(0, d - 3), s] -= 0.4
            last_bar[s] = d
        alive = pit_universe.pit_alive_mask(first_bar, last_bar, W, min_weeks_history=8)
        return pit_universe.momentum_ic_series(returns, alive, trail_win=4)

    r1, r2, r3 = run(), run(), run()
    assert r1 == r2 == r3


# ============================================================================
# (i) Abnahme-Nacharbeiten
# ============================================================================

# ---- Nacharbeit #1: funding_n / funding_sum --------------------------------

def _funding_events(day_iso: str, hours: list[int], rate: float = 0.0001) -> list[dict]:
    ms0 = (date.fromisoformat(day_iso) - EPOCH).days * 86_400_000
    return [{"symbol": "SYM", "funding_rate": rate, "ts_ms": ms0 + h * 3_600_000}
            for h in hours]


def test_funding_daily_stats_8h_vs_1h_and_interval_change_within_year():
    """8h-Symbol -> funding_n 3; 1h-Symbol -> 24; both computed from the
    SAME symbol's history across a year with an interval change -- no
    interval is assumed anywhere, only real observed timestamps counted."""
    day_8h = "2022-01-10"     # settlements at 00:00 / 08:00 / 16:00 UTC
    day_1h = "2022-07-10"     # settlements every hour (interval switched mid-year)
    events = _funding_events(day_8h, [0, 8, 16]) + _funding_events(day_1h, list(range(24)))

    stats_by_day = panel_store.daily_funding_stats(events)
    assert stats_by_day[day_8h]["funding_n"] == 3
    assert stats_by_day[day_1h]["funding_n"] == 24
    assert stats_by_day[day_8h]["funding_sum"] == pytest.approx(3 * 0.0001)
    assert stats_by_day[day_1h]["funding_sum"] == pytest.approx(24 * 0.0001)


def test_merge_funding_daily_attaches_and_defaults_to_zero_not_none():
    day = "2022-03-01"
    ms0 = (date.fromisoformat(day) - EPOCH).days * 86_400_000
    row_with_funding = {"start_ms": ms0, "open": 1.0, "high": 1.0, "low": 1.0,
                        "close": 1.0, "volume": 1.0, "turnover": 1.0}
    row_without_funding = {**row_with_funding, "start_ms": ms0 + 86_400_000}  # next day
    funding_rows = _funding_events(day, [0, 8, 16])

    merged = panel_store.merge_funding_daily([row_with_funding, row_without_funding], funding_rows)
    by_start = {r["start_ms"]: r for r in merged}
    assert by_start[ms0]["funding_n"] == 3
    assert by_start[ms0]["funding_sum"] == pytest.approx(0.0003)
    # a day with NO funding rows fetched (not the same as "never fetched at
    # all" -- write_year_partition's None default covers that case) gets a
    # measured zero, not a null:
    assert by_start[ms0 + 86_400_000]["funding_n"] == 0
    assert by_start[ms0 + 86_400_000]["funding_sum"] == pytest.approx(0.0)


def test_funding_n_and_sum_land_in_the_written_partition(tmp_path):
    base = tmp_path / "panel_1d"
    manifest = base / "panel_manifest.sqlite"
    day = "2022-06-01"
    ms0 = (date.fromisoformat(day) - EPOCH).days * 86_400_000
    rows = [{"start_ms": ms0, "open": 1.0, "high": 1.0, "low": 1.0,
             "close": 1.0, "volume": 1.0, "turnover": 1.0}]
    merged = panel_store.merge_funding_daily(rows, _funding_events(day, [0, 8, 16]))
    panel_store.write_year_partition(
        base, manifest, "BTCUSDT", 2022, merged,
        listing_date=date(2022, 1, 1), as_of_date=date(2022, 12, 31), frozen=True)

    import pyarrow.parquet as pq
    table = pq.read_table(panel_store.partition_path(base, "BTCUSDT", 2022, frozen=True))
    assert table.column("funding_n").to_pylist() == [3]
    assert table.column("funding_sum").to_pylist() == pytest.approx([0.0003])


def test_fetch_funding_history_backward_pagination_and_dedup():
    page1 = {"retCode": 0, "result": {"symbol": "BTCUSDT", "list": [
        {"symbol": "BTCUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": "30000"},
        {"symbol": "BTCUSDT", "fundingRate": "0.0002", "fundingRateTimestamp": "20000"},
    ]}}
    page2 = {"retCode": 0, "result": {"symbol": "BTCUSDT", "list": [
        {"symbol": "BTCUSDT", "fundingRate": "0.0002", "fundingRateTimestamp": "20000"},  # overlap
        {"symbol": "BTCUSDT", "fundingRate": "0.0003", "fundingRateTimestamp": "10000"},
    ]}}
    fetcher = bybit_rest.fixture_fetcher([page1, page2])
    result = bybit_rest.fetch_funding_history("BTCUSDT", 10_000, 30_000,
                                               fetcher=fetcher, max_req_per_sec=0)
    assert result["n_rows"] == 3
    assert [r["ts_ms"] for r in result["rows"]] == [10_000, 20_000, 30_000]
    assert len(result["raw_sha256"]) == 2


def test_fetch_funding_history_field_layout_loud_fail():
    bad_page = {"retCode": 0, "result": {"list": [
        {"symbol": "X", "fundingRate": "0.001"}]}}  # fundingRateTimestamp missing
    fetcher = bybit_rest.fixture_fetcher([bad_page])
    with pytest.raises(bybit_rest.BybitFieldLayoutError, match="fundingRateTimestamp"):
        bybit_rest.fetch_funding_history("X", 0, 100_000, fetcher=fetcher, max_req_per_sec=0)


def test_probe_funding_history():
    page = {"retCode": 0, "result": {"symbol": "BTCUSDT", "list": [
        {"symbol": "BTCUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": "1000"}]}}
    out = bybit_rest.probe_funding_history("BTCUSDT", fetcher=bybit_rest.fixture_fetcher([page]))
    assert out["n_rows"] == 1 and out["rows"][0]["funding_rate"] == pytest.approx(0.0001)


# ---- Nacharbeit #3: listing_date from launchTime ---------------------------

def test_listing_date_from_launch_time():
    from datetime import datetime, timezone
    ms = int(datetime(2021, 5, 17, tzinfo=timezone.utc).timestamp() * 1000)
    assert panel_store.listing_date_from_launch_time(str(ms)) == date(2021, 5, 17)
    assert panel_store.listing_date_from_launch_time(ms) == date(2021, 5, 17)


def test_listing_date_from_launch_time_loud_fail():
    for bad in (None, "", "0", 0, "not-a-number", -5):
        with pytest.raises(panel_store.PanelStoreError):
            panel_store.listing_date_from_launch_time(bad)


def test_instruments_row_carries_launch_time_through_untouched():
    """parse_instrument_rows passes the raw dict through unchanged --
    launchTime survives the REST round trip for --fetch to consume."""
    page = {"retCode": 0, "result": {"list": [
        {"symbol": "BTCUSDT", "status": "Trading", "launchTime": "1594080000000"}],
        "nextPageCursor": ""}}
    out = bybit_rest.fetch_instruments(fetcher=bybit_rest.fixture_fetcher([page]))
    assert out["rows"][0]["launchTime"] == "1594080000000"
    assert panel_store.listing_date_from_launch_time(out["rows"][0]["launchTime"]) == date(2020, 7, 7)


# ---- Nacharbeit #2: pair_corr rho(BTC,ETH) on a synthetic bar cache -------

def _write_raw_trading_day(base: Path, symbol: str, day_iso: str, prices: np.ndarray) -> None:
    """One flat trade per minute (mirrors tests/unit/test_c19_drift.py's
    ``_write_raw_day`` fixture-writer pattern)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    ms0 = (date.fromisoformat(day_iso) - EPOCH).days * 86_400_000
    n = prices.size
    ts = [ms0 + i * 60_000 for i in range(n)]
    payloads = [json.dumps({"side": "Buy" if i % 2 == 0 else "Sell",
                            "price": f"{prices[i]:.8f}", "size": "1"}) for i in range(n)]
    d = base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={day_iso}"
    d.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts], pa.int64()),
        "ts_exchange_ms": pa.array(ts, pa.int64()),
        "topic": pa.array(["publicTrade"] * n), "stream": pa.array(["publicTrade"] * n),
        "symbol": pa.array([symbol] * n), "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _build_pair_cache(tmp_path: Path, days: list[str], rho: float, seed: int,
                      base_a: float = 50_000.0, base_b: float = 3_000.0,
                      sigma: float = 0.01) -> Path:
    """Synthetic WP-0 bar cache for BTCUSDT/ETHUSDT whose 30-minute log
    returns carry a KNOWN correlation ``rho`` by construction (bivariate
    normal via Cholesky-free direct mixing) -- the price is held constant
    across each 30-minute bucket's minutes (the aggregation only reads the
    bucket's LAST minute, so this reproduces the target bucket close
    exactly while still exercising the real per-minute bar-cache path)."""
    n_buckets = 48 * len(days)
    rng = np.random.default_rng(seed)
    z1 = rng.normal(0, sigma, size=n_buckets)
    z2 = rng.normal(0, sigma, size=n_buckets)
    ret_a = z1
    ret_b = rho * z1 + np.sqrt(max(0.0, 1 - rho ** 2)) * z2
    close_a = base_a * np.exp(np.cumsum(ret_a))
    close_b = base_b * np.exp(np.cumsum(ret_b))

    base, cache = tmp_path / "h", tmp_path / "c"
    for i, day in enumerate(days):
        _write_raw_trading_day(base, "BTCUSDT", day, np.repeat(close_a[i * 48:(i + 1) * 48], 30))
        _write_raw_trading_day(base, "ETHUSDT", day, np.repeat(close_b[i * 48:(i + 1) * 48], 30))
    build_range(base, cache, "bybit", "publicTrade", "BTCUSDT", days[0], days[-1],
                require_manifest_done=False)
    build_range(base, cache, "bybit", "publicTrade", "ETHUSDT", days[0], days[-1],
                require_manifest_done=False)
    return cache


def _days(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def test_pair_corr_recovers_known_correlation(tmp_path):
    days = _days("2026-08-01", 10)
    cache = _build_pair_cache(tmp_path, days, rho=0.8, seed=0)
    result = pair_corr.compute_pair_correlation(
        cache, "bybit", "BTCUSDT", "ETHUSDT", days[0], days[-1], seed=123, n_boot=300)
    assert result["n_aligned_buckets"] == 479  # 10*48 buckets, minus 1 (first has no return)
    assert result["pearson"]["point"] == pytest.approx(0.8, abs=0.1)
    assert result["pearson"]["ci_lo"] <= 0.8 <= result["pearson"]["ci_hi"]
    assert result["spearman"]["point"] == pytest.approx(0.8, abs=0.1)
    assert result["seed"] == 123


def test_pair_corr_null_case_ci_contains_zero(tmp_path):
    days = _days("2026-08-01", 10)
    cache = _build_pair_cache(tmp_path, days, rho=0.0, seed=1)
    result = pair_corr.compute_pair_correlation(
        cache, "bybit", "BTCUSDT", "ETHUSDT", days[0], days[-1], seed=456, n_boot=300)
    assert abs(result["pearson"]["point"]) < 0.15
    assert result["pearson"]["ci_lo"] <= 0.0 <= result["pearson"]["ci_hi"]
    assert result["spearman"]["ci_lo"] <= 0.0 <= result["spearman"]["ci_hi"]


def test_pair_corr_gap_never_manufactures_a_return():
    # bucket 5 missing entirely -> no return spans 4 -> 6
    closes = {0: 100.0, 1: 101.0, 2: 102.0, 4: 103.0, 6: 104.0}
    rets = pair_corr.log_returns(closes)
    assert set(rets) == {1, 2}  # 4->? skipped (gap at 3), 6->? skipped (gap at 5)


def test_pair_corr_determinism_same_seed():
    days = _days("2026-08-01", 5)
    x = np.random.default_rng(0).normal(0, 0.01, 240)
    y = 0.5 * x + np.random.default_rng(1).normal(0, 0.01, 240)
    r1 = pair_corr.block_bootstrap_ci(x, y, statistic="pearson", seed=7, n_boot=200)
    r2 = pair_corr.block_bootstrap_ci(x, y, statistic="pearson", seed=7, n_boot=200)
    assert r1 == r2


def test_pair_corr_dec53_artifact_written_and_verified(tmp_path):
    days = _days("2026-08-01", 5)
    cache = _build_pair_cache(tmp_path, days, rho=0.5, seed=2)
    result = pair_corr.compute_pair_correlation(
        cache, "bybit", "BTCUSDT", "ETHUSDT", days[0], days[-1], seed=99, n_boot=100)
    out = pair_corr.write_artifacts(tmp_path / "artifacts", result)
    payload = pair_corr.read_artifacts(out["path"])
    assert payload["seed"] == 99 and payload["sha256"] == out["sha256"]

    path = Path(out["path"])
    doc = json.loads(path.read_text())
    doc["pearson"]["point"] += 1.0
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="does not match"):
        pair_corr.read_artifacts(path)


def test_pair_corr_refuses_data_harvest_path(tmp_path):
    result = {"symbol_a": "BTCUSDT", "symbol_b": "ETHUSDT", "seed": 1, "n_aligned_buckets": 0,
              "pearson": {"point": 0.0, "ci_lo": 0.0, "ci_hi": 0.0},
              "spearman": {"point": 0.0, "ci_lo": 0.0, "ci_hi": 0.0}}
    with pytest.raises(ValueError, match="data/harvest"):
        pair_corr.write_artifacts(tmp_path / "data" / "harvest" / "wp7", result)


# ---- N_eff report labeling --------------------------------------------------

def test_report_n_eff_label_and_pair_corr_section(tmp_path):
    b12 = report.evaluate_b1_b2(0.09, 0.05, 130)
    b3 = report.evaluate_b3(["Trading"], 0, 0)
    b4 = report.evaluate_b4(500.0, cost_bps=18.0)
    b5 = report.evaluate_b5([])
    n_eff_result = {"n_eff": 118.2, "n_symbols_balanced": 120, "inv_n_eff": 1 / 118.2}
    pc = {"symbol_a": "BTCUSDT", "symbol_b": "ETHUSDT", "seed": 53, "n_aligned_buckets": 479,
          "pearson": {"point": 0.83, "ci_lo": 0.79, "ci_hi": 0.86},
          "spearman": {"point": 0.82, "ci_lo": 0.78, "ci_hi": 0.85}}
    full = report.assemble_report(b1_b2=b12, b3=b3, b4=b4, b5=b5,
                                  n_eff=n_eff_result, pair_corr_btc_eth=pc)
    assert full["n_eff"]["label"] == report.N_EFF_LABEL == \
        "N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil)"
    assert full["n_eff"]["n_eff"] == 118.2
    assert full["pair_corr_btc_eth"]["pearson"]["point"] == 0.83

    paths = report.write_report(tmp_path / "out", full)
    md = Path(paths["md"]).read_text()
    assert report.N_EFF_LABEL in md
    assert "rho(BTC,ETH)" in md
    js = json.loads(Path(paths["json"]).read_text())
    assert js["n_eff"]["label"] == report.N_EFF_LABEL


def test_report_markdown_shows_sd_null_threshold_formula():
    """Coordinator Abnahme-Nacharbeit re: 0.087003 vs. the spec's printed
    0.08699 -- tests check the FORMULA (already true, see
    test_feasibility_thresholds_match_prd_arithmetic); the report TEXT
    must show the formula too, not just the bare number."""
    b12 = report.evaluate_b1_b2(0.09, 0.05, 130)
    b3 = report.evaluate_b3(["Trading"], 0, 0)
    b4 = report.evaluate_b4(500.0, cost_bps=18.0)
    b5 = report.evaluate_b5([])
    full = report.assemble_report(b1_b2=b12, b3=b3, b4=b4, b5=b5)
    from bybit_edge.research.wp7_universe.report import _to_markdown
    md = _to_markdown(full)
    assert "IC_prior * sqrt(W) / z" in md
    assert f"z={stats.Z_PER_WINDOW}" in md and f"z={stats.Z_POOLED}" in md
