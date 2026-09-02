"""Unit tests fuer WP-10 Teil A (Praemien-Kohaerenz im Stress, deskriptiv).

Deckt ab (WP10_SPEZIFIKATION.md Teil A, DEC-53/55/56):
  (a) ``rv``: realized-vol/return-panel Primitiven auf synthetischem
      Bar-Cache (exakte, konstruierte RV-Werte),
  (b) ``series``: Funding-Cashflow (loud-fail auf [sek]-Feldlayout,
      SKIPPED_NO_DATA), IV-RV-Differenz (Deribit-Harvest x Bar-Cache),
      Perp-Basis-Proxy (probe-first, loud SKIP wenn Felder fehlen),
  (c) ``stress_canon``: STRESS_ABS/STRESS_REL Determinismus, die zwei
      benannten Referenz-Tage stets enthalten, Episoden-Luecken-Regel,
      Append-only-Verletzung + erfolgreiches Merge, Fixture-SHA-256-
      Rundreise, Schreib-Verweigerung unter data/harvest,
  (d) ``coherence``: DEC-39-Trio -- POSITIV (Serie mit bekannt hoeherer
      Korrelation im Stress wird mit CI um die Wahrheit wiedergefunden),
      NULL (unabhaengige Serien: CI umfasst 0, |rho| < 2*SE), ADVERSARIAL
      (gemeinsamer deterministischer Trend, unabhaengige Innovationen:
      nach der gepinnten Differenzierung verschwindet die Scheinkorrelation),
  (e) ``portfolio_null`` (korrigiert -- Summen-Konstruktion entfernt):
      ``portfolio_null_table`` (k=2..5, Gleichgewichtungs-Sharpe-Null):
      mean nahe 0, sd waechst NICHT mit k (+-25%), p95 > 0, reproduzierbar
      bei gleichem Seed; ``selection_ceiling`` (K=5..100): waechst
      monoton mit K, trifft die Bailey/Lopez-de-Prado-Formel (+-30%),
      reproduzierbar,
  (f) ``report``: DEC-53-Artefakt-Rundreise (Cluster-Serien-CSV + SHA-256,
      Bootstrap-Fingerprint), KEIN-VERDIKT bei fehlenden Artefakten,
      Schreib-Verweigerung unter data/harvest,
  (g) Ende-zu-Ende: der Treiber-Skript-Dreischritt (--probe/--stress-canon/
      --run), NIE unter data/harvest schreibend.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp10_coherence import coherence as co
from bybit_edge.research.wp10_coherence import portfolio_null as pn
from bybit_edge.research.wp10_coherence import report as rp
from bybit_edge.research.wp10_coherence import rv as _rv
from bybit_edge.research.wp10_coherence import series as sr
from bybit_edge.research.wp10_coherence import stress_canon as sc

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wp10_coherence.py"
EPOCH = date(1970, 1, 1)


# =============================================================== helpers

def _iso(i: int, start: str = "2026-01-01") -> str:
    return (date.fromisoformat(start) + timedelta(days=i)).isoformat()


def _write_bar_day(cache_dir: Path, exchange: str, symbol: str, day: str,
                   closes: list[float]) -> None:
    """Write ONE synthetic WP-0 bar-cache day partition directly (bypasses
    ``build_day``) so tests control exact per-minute closes -- and thus
    exact RV -- deterministically."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    from bybit_edge.research.bar_cache import BAR_COLUMNS, SCHEMA_VERSION, _day_partition

    part = _day_partition(Path(cache_dir), exchange, symbol, day)
    part.mkdir(parents=True, exist_ok=True)
    n = len(closes)
    minute_idx0 = (date.fromisoformat(day) - EPOCH).days * 1_440
    cols = {
        "minute_idx": list(range(minute_idx0, minute_idx0 + n)),
        "px_first": closes, "px_last": closes, "px_high": closes, "px_low": closes,
        "vol_buy": [1.0] * n, "vol_sell": [1.0] * n, "vol_total": [2.0] * n,
        "n_trades": [2] * n, "n_buy": [1] * n, "n_sell": [1] * n, "n_size_unparsed": [0] * n,
    }
    table = pa.table({
        col: pa.array(cols[col], pa.int64() if (col == "minute_idx" or col.startswith("n_"))
                      else pa.float64())
        for col in BAR_COLUMNS
    })
    pq.write_table(table, part / "bars.parquet")
    (part / "manifest.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION}), encoding="utf-8")


def _write_rv_day(cache_dir: Path, exchange: str, symbol: str, day: str,
                  rv_target: float, base_price: float = 100.0, n_bars: int = 61) -> None:
    """A day whose realized vol is EXACTLY ``rv_target`` (constant per-
    minute log-step, so sum(step^2 * (n-1)) = rv_target^2 by construction)."""
    n = n_bars
    step = rv_target / np.sqrt(n - 1)
    log_px = np.cumsum([0.0] + [step] * (n - 1))
    closes = list(base_price * np.exp(log_px))
    _write_bar_day(cache_dir, exchange, symbol, day, closes)


def _write_dvol_day(base: Path, symbol: str, day: str, close: float) -> None:
    """One ``deribit/dvol`` harvest partition (mirrors ``test_wp9_dvol``'s
    writer, own local copy -- no cross-import between test modules)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "deribit" / "dvol" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    ts_ms = (date.fromisoformat(day) - EPOCH).days * 86_400_000 + 1_000
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([ts_ms * 1_000_000], pa.int64()),
        "ts_exchange_ms": pa.array([ts_ms], pa.int64()),
        "topic": pa.array([f"deribit_volatility_index.{symbol}"]),
        "stream": pa.array(["dvol"]),
        "symbol": pa.array([symbol]),
        "payload_json": pa.array([json.dumps({"volatility": close})]),
    }), d / "part-0.parquet")


def _write_funding_day(base: Path, symbol: str, day: str,
                       events: list[tuple[int, float]], *, drop_field: str | None = None) -> None:
    """One ``bybit/rest.fundingRate`` harvest partition. ``events`` is a
    list of ``(ts_ms, rate)``; ``drop_field`` deliberately omits a [sek]
    field on every event (loud-fail fixture)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "bybit" / "rest.fundingRate" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    payloads = []
    for ts_ms, rate in events:
        obj = {"fundingRate": str(rate), "fundingRateTimestamp": str(ts_ms), "symbol": symbol}
        if drop_field:
            obj.pop(drop_field, None)
        payloads.append(json.dumps(obj))
    ts_list = [e[0] for e in events]
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts_list], pa.int64()),
        "ts_exchange_ms": pa.array(ts_list, pa.int64()),
        "topic": pa.array([f"rest.fundingRate.{symbol}"] * len(events)),
        "stream": pa.array(["rest.fundingRate"] * len(events)),
        "symbol": pa.array([symbol] * len(events)),
        "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _write_tickers_day(base: Path, symbol: str, day: str,
                       events: list[tuple[int, float, float]] | None,
                       *, fields_absent: bool = False) -> None:
    """One ``bybit/tickers`` harvest partition. ``events`` is
    ``(ts_ms, markPrice, indexPrice)``; ``fields_absent`` writes rows
    without those fields (probe-first SKIP fixture)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "bybit" / "tickers" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    if fields_absent:
        events = events or [(1, 0.0, 0.0)]
        payloads = [json.dumps({"symbol": symbol, "lastPrice": "1.0"}) for _ in events]
    else:
        payloads = [json.dumps({"symbol": symbol, "markPrice": str(m), "indexPrice": str(i)})
                   for _, m, i in events]
    ts_list = [e[0] for e in events]
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts_list], pa.int64()),
        "ts_exchange_ms": pa.array(ts_list, pa.int64()),
        "topic": pa.array([f"tickers.{symbol}"] * len(events)),
        "stream": pa.array(["tickers"] * len(events)),
        "symbol": pa.array([symbol] * len(events)),
        "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _mk_series(name: str, days: list[str], values: list[float]) -> dict:
    return {"name": name, "kind": "synthetic", "symbol": name, "provenance": {},
            "days": list(days), "values": list(values),
            "coverage": {"n_days": len(days)}, "status": "OK", "reason": None}


# ==================================================================== rv

@pytest.mark.filterwarnings("ignore")
def test_rv_daily_realized_vol_exact_and_deterministic(tmp_path):
    pytest.importorskip("pyarrow")
    _write_rv_day(tmp_path, "bybit", "BTCUSDT", "2026-01-01", rv_target=0.05)
    from bybit_edge.research.bar_cache import load_minute_bars
    bars = load_minute_bars(tmp_path, "bybit", "BTCUSDT", "2026-01-01", "2026-01-01")
    out1 = _rv.daily_realized_vol(bars)
    out2 = _rv.daily_realized_vol(bars)
    assert out1 == out2
    assert out1["2026-01-01"] == pytest.approx(0.05, abs=1e-9)


@pytest.mark.filterwarnings("ignore")
def test_rv_min_bars_per_day_floor_drops_sparse_day(tmp_path):
    pytest.importorskip("pyarrow")
    _write_bar_day(tmp_path, "bybit", "BTCUSDT", "2026-01-01", [100.0, 100.1, 100.2])
    from bybit_edge.research.bar_cache import load_minute_bars
    bars = load_minute_bars(tmp_path, "bybit", "BTCUSDT", "2026-01-01", "2026-01-01")
    assert _rv.daily_realized_vol(bars) == {}


def test_rv_annualize_pct_scaling():
    out = _rv.annualize_pct({"2026-01-01": 0.02})
    expected = 0.02 * np.sqrt(_rv.ANNUALIZATION_DAYS_PER_YEAR) * 100.0
    assert out["2026-01-01"] == pytest.approx(expected)


@pytest.mark.filterwarnings("ignore")
def test_rv_daily_close_log_returns_only_consecutive_days(tmp_path):
    pytest.importorskip("pyarrow")
    _write_bar_day(tmp_path, "bybit", "BTCUSDT", "2026-01-01", [100.0] * 61)
    _write_bar_day(tmp_path, "bybit", "BTCUSDT", "2026-01-02", [110.0] * 61)
    _write_bar_day(tmp_path, "bybit", "BTCUSDT", "2026-01-05", [200.0] * 61)  # gap
    from bybit_edge.research.bar_cache import load_minute_bars
    bars = load_minute_bars(tmp_path, "bybit", "BTCUSDT", "2026-01-01", "2026-01-05")
    rets = _rv.daily_close_log_returns(bars)
    assert set(rets) == {"2026-01-02"}  # 01-05 has no consecutive predecessor
    assert rets["2026-01-02"] == pytest.approx(np.log(110.0 / 100.0))


# ============================================================= series (a)

@pytest.mark.filterwarnings("ignore")
def test_funding_probe_no_partitions_is_skipped_not_raised(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    con = duckdb.connect()
    try:
        out = sr.funding_daily_cashflow(con, tmp_path, "BTCUSDT")
    finally:
        con.close()
    assert out["status"] == "SKIPPED_NO_DATA"
    assert out["days"] == []


@pytest.mark.filterwarnings("ignore")
def test_funding_daily_cashflow_sums_events_per_day(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    ts0 = (date(2026, 1, 1) - EPOCH).days * 86_400_000
    _write_funding_day(base, "BTCUSDT", "2026-01-01", [
        (ts0 + 1_000, 0.0001), (ts0 + 2_000, 0.0002), (ts0 + 3_000, -0.00005),
    ])
    con = duckdb.connect()
    try:
        out = sr.funding_daily_cashflow(con, base, "BTCUSDT")
    finally:
        con.close()
    assert out["status"] == "OK"
    assert out["days"] == ["2026-01-01"]
    assert out["values"][0] == pytest.approx(0.0001 + 0.0002 - 0.00005)


@pytest.mark.filterwarnings("ignore")
def test_funding_missing_field_is_loud_fail(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    ts0 = (date(2026, 1, 1) - EPOCH).days * 86_400_000
    _write_funding_day(base, "BTCUSDT", "2026-01-01", [(ts0 + 1_000, 0.0001)],
                       drop_field="fundingRateTimestamp")
    con = duckdb.connect()
    try:
        with pytest.raises(sr.SeriesError, match="fundingRateTimestamp"):
            sr.funding_daily_cashflow(con, base, "BTCUSDT")
    finally:
        con.close()


@pytest.mark.filterwarnings("ignore")
def test_iv_rv_diff_series_computes_overlap_only(tmp_path):
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    import duckdb
    harvest_base = tmp_path / "harvest"
    cache_dir = tmp_path / "barcache"
    days = [_iso(i) for i in range(5)]
    for d in days:
        _write_dvol_day(harvest_base, "BTC_DVOL", d, close=50.0)
    for d in days[:3]:  # bar cache only covers first 3 days -> overlap = 3
        _write_rv_day(cache_dir, "bybit", "BTCUSDT", d, rv_target=0.01)
    con = duckdb.connect()
    try:
        out = sr.iv_rv_diff_series(con, harvest_base, cache_dir, dvol_symbol="BTC_DVOL",
                                   bar_exchange="bybit", bar_symbol="BTCUSDT", days=days)
    finally:
        con.close()
    assert out["status"] == "OK"
    assert out["days"] == days[:3]
    rv_pct = 0.01 * np.sqrt(_rv.ANNUALIZATION_DAYS_PER_YEAR) * 100.0
    assert out["values"][0] == pytest.approx(50.0 - rv_pct)


def test_iv_rv_diff_series_empty_days_is_skipped():
    out = sr.iv_rv_diff_series(None, "unused", "unused", dvol_symbol="BTC_DVOL",
                               bar_exchange="bybit", bar_symbol="BTCUSDT", days=[])
    assert out["status"] == "SKIPPED_NO_DATA"


@pytest.mark.filterwarnings("ignore")
def test_perp_basis_probe_first_skips_loudly_when_fields_absent(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    _write_tickers_day(base, "BTCUSDT", "2026-01-01", None, fields_absent=True)
    con = duckdb.connect()
    try:
        out = sr.perp_basis_proxy_series(con, base, "BTCUSDT")
    finally:
        con.close()
    assert out["status"] == "SKIPPED_FIELDS_ABSENT"
    assert out["days"] == []
    assert out["provenance"]["probe"]["status"] == "FIELDS_ABSENT"


@pytest.mark.filterwarnings("ignore")
def test_perp_basis_computes_daily_mean_relative_basis(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    ts0 = (date(2026, 1, 1) - EPOCH).days * 86_400_000
    _write_tickers_day(base, "BTCUSDT", "2026-01-01",
                       [(ts0, 101.0, 100.0), (ts0 + 60_000, 99.0, 100.0)])
    con = duckdb.connect()
    try:
        out = sr.perp_basis_proxy_series(con, base, "BTCUSDT")
    finally:
        con.close()
    assert out["status"] == "OK"
    assert out["values"][0] == pytest.approx(0.0, abs=1e-9)  # (0.01 + -0.01)/2


# ========================================================== stress_canon (c)

def test_stress_canon_determinism_and_named_dates_present():
    panel = {"BTCUSDT": {_iso(i): 0.01 for i in range(100)}}
    f1 = sc.build_stress_abs(panel)
    f2 = sc.build_stress_abs(panel)
    assert f1 == f2  # bit-identical, same input
    for named in sc.STRESS_ABS_NAMED_DATES:
        assert named in f1["days"]
    r1 = sc.build_stress_rel(panel)
    r2 = sc.build_stress_rel(panel)
    assert r1 == r2
    for named in sc.STRESS_REL_NAMED_DATES:
        assert named in r1["days"]


def test_stress_abs_flags_extreme_days_over_p99():
    days = [_iso(i) for i in range(150)]
    rv_by_day = {d: 0.01 for d in days}
    rv_by_day[days[10]] = 5.0  # extreme spike
    rv_by_day[days[80]] = 5.0
    panel = {"BTCUSDT": rv_by_day}
    fixture = sc.build_stress_abs(panel, named_dates=())
    assert days[10] in fixture["days"]
    assert days[80] in fixture["days"]
    # the constant-0.01 days should NOT be flagged (well under p99 of a
    # panel dominated by 0.01 with two spikes).
    assert days[0] not in fixture["days"]


def test_stress_abs_union_across_symbols_and_or_semantics():
    days = [_iso(i) for i in range(120)]
    btc = {d: 0.01 for d in days}
    eth = {d: 0.01 for d in days}
    btc[days[5]] = 9.0   # only BTC spikes
    eth[days[50]] = 9.0  # only ETH spikes
    fixture = sc.build_stress_abs({"BTCUSDT": btc, "ETHUSDT": eth}, named_dates=())
    assert days[5] in fixture["days"] and days[50] in fixture["days"]


def test_group_episodes_gap_rule():
    days = ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-10"]
    episodes = sc.group_episodes(days, gap_max_days=1)
    # 01-01..01-02 contiguous; 01-04 has a 1-day gap after 01-02 (01-03
    # missing) -> still same episode; 01-10 has a 5-day gap -> new episode.
    assert episodes == [["2026-01-01", "2026-01-02", "2026-01-04"], ["2026-01-10"]]


def test_group_episodes_empty():
    assert sc.group_episodes([], gap_max_days=1) == []


def test_fixture_sha256_roundtrip_stable():
    panel = {"BTCUSDT": {_iso(i): 0.01 for i in range(30)}}
    fixture = sc.build_stress_abs(panel)
    finalized = sc.finalize_fixture(fixture)
    # re-hashing the finalized fixture (which now carries its own sha256
    # key) must reproduce the SAME hash it was finalized with.
    assert sc.fixture_sha256(finalized) == finalized["sha256"]
    assert len(finalized["sha256"]) == 64


def test_merge_append_only_accepts_pure_extension():
    old_panel = {_iso(i): (9.0 if i == 0 else 0.01) for i in range(60)}
    old = sc.finalize_fixture(sc.build_stress_abs({"BTCUSDT": old_panel}, named_dates=()))
    new_panel = {_iso(i): (9.0 if i in (0, 100) else 0.01) for i in range(120)}
    new = sc.build_stress_abs({"BTCUSDT": new_panel}, named_dates=())
    merged = sc.merge_append_only(old, new)
    assert set(old["days"]) <= set(merged["days"])
    assert _iso(100) in merged["days"]


def test_merge_append_only_tolerates_natural_recompute_disagreement():
    # A day flagged in `old` but NOT re-flagged by a fresh, larger-sample
    # recompute (`new`) is NOT a violation -- the union just keeps it,
    # exactly DEC-55's "alte Eintraege aendern sich nicht" contract.
    old = {"canon": "STRESS_ABS", "days": [_iso(0), _iso(1)], "gap_max_days": 1, "pctl": 99.0}
    new = {"canon": "STRESS_ABS", "days": [_iso(1)], "gap_max_days": 1, "pctl": 99.0}
    merged = sc.merge_append_only(old, new)
    assert _iso(0) in merged["days"] and _iso(1) in merged["days"]


def test_merge_append_only_rejects_pinned_parameter_drift():
    old = {"canon": "STRESS_ABS", "days": [_iso(0)], "gap_max_days": 1, "pctl": 99.0}
    new = {"canon": "STRESS_ABS", "days": [_iso(0)], "gap_max_days": 1, "pctl": 97.5}
    with pytest.raises(sc.AppendOnlyViolationError, match="pctl"):
        sc.merge_append_only(old, new)


def test_merge_append_only_rejects_canon_mismatch():
    old = {"canon": "STRESS_ABS", "days": []}
    new = {"canon": "STRESS_REL", "days": []}
    with pytest.raises(sc.AppendOnlyViolationError):
        sc.merge_append_only(old, new)


def test_write_fixture_refuses_data_harvest(tmp_path):
    fixture = sc.build_stress_abs({"BTCUSDT": {_iso(0): 0.01}})
    with pytest.raises(ValueError, match="data/harvest"):
        sc.write_fixture(fixture, tmp_path / "data" / "harvest" / "stress_abs.json")


def test_write_fixture_then_merge_on_disk(tmp_path):
    path = tmp_path / "stress_abs.json"
    panel1 = {"BTCUSDT": {_iso(i): (9.0 if i == 0 else 0.01) for i in range(60)}}
    w1 = sc.write_fixture(sc.build_stress_abs(panel1, named_dates=()), path)
    assert _iso(0) in w1["days"]
    panel2 = {"BTCUSDT": {_iso(i): (9.0 if i in (0, 100) else 0.01) for i in range(120)}}
    w2 = sc.write_fixture(sc.build_stress_abs(panel2, named_dates=()), path)
    assert _iso(0) in w2["days"] and _iso(100) in w2["days"]
    on_disk = sc.read_fixture(path)
    assert on_disk == w2


# ============================================================= coherence (d)

def test_dec39_positive_stress_correlation_recovered_with_ci():
    rng = np.random.default_rng(1)
    n = 120
    days = [_iso(i) for i in range(n)]
    stress_set = set(days[:30])
    x = rng.normal(0.0, 1.0, n)
    y = np.empty(n)
    for i in range(n):
        y[i] = (x[i] + rng.normal(0.0, 0.05)) if days[i] in stress_set else rng.normal(0.0, 1.0)
    a, b = _mk_series("A", days, x), _mk_series("B", days, y)
    result = co.pairwise_regime_result(a, b, stress_set, episodes=None, n_bootstrap=400, seed=53)
    assert result["stress"]["status"] == "OK"
    # CI excludes 0 -- the known strong stress-day relationship is recovered.
    assert result["stress"]["ci_lo"] > 0.3
    assert result["stress"]["rho"] > 0.6
    assert result["stress"]["n_episodes"] is None  # no episode list supplied


def test_dec39_null_independent_series_ci_covers_zero():
    rng = np.random.default_rng(2)
    n = 80
    days = [_iso(i) for i in range(n)]
    x = rng.normal(0.0, 1.0, n)
    y = rng.normal(0.0, 1.0, n)
    a, b = _mk_series("A", days, x), _mk_series("B", days, y)
    result = co.pairwise_regime_result(a, b, set(), episodes=None, n_bootstrap=400, seed=53)
    quiet = result["quiet"]
    assert quiet["status"] == "OK"
    assert quiet["ci_lo"] < 0.0 < quiet["ci_hi"]
    assert abs(quiet["rho"]) < 2.0 * quiet["bonett_wright_se"]


def test_dec39_adversarial_common_trend_spurious_correlation_vanishes_after_differencing():
    rng = np.random.default_rng(3)
    n = 150
    days = [_iso(i) for i in range(n)]
    trend = 2.0 * np.arange(n)  # LINEAR shared trend -> constant after first-differencing
    x = trend + rng.normal(0.0, 1.0, n)
    y = trend + rng.normal(0.0, 1.0, n)
    a, b = _mk_series("A", days, x), _mk_series("B", days, y)

    raw_days, raw_x, raw_y = co.pair_overlap(a, b)
    raw_rho = co.spearman_rho(raw_x, raw_y)
    assert raw_rho > 0.95  # shared trend dominates -> spurious near-perfect rho on LEVELS

    diff_days, diff_x, diff_y = co.differenced_pair_overlap(a, b)
    diff_rho = co.spearman_rho(diff_x, diff_y)
    assert abs(diff_rho) < 0.3  # innovations are independent -> vanishes after differencing

    result = co.pairwise_regime_result(a, b, set(), episodes=None, n_bootstrap=400, seed=53)
    assert result["quiet"]["ci_lo"] < 0.0 < result["quiet"]["ci_hi"]


def test_bonett_wright_se_formula():
    assert co.bonett_wright_se(103) == pytest.approx(1.06 / np.sqrt(100))
    assert np.isnan(co.bonett_wright_se(3))


def test_cluster_bootstrap_rejects_too_few_days():
    with pytest.raises(co.CoherenceError):
        co.cluster_bootstrap_rho_ci(np.array([1.0, 2.0]), np.array([1.0, 2.0]), seed=1)


def test_effective_n_counts_only_intersecting_episodes():
    episodes = [["2026-01-01", "2026-01-02"], ["2026-02-01"]]
    out = co.effective_n(["2026-01-01"], episodes)
    assert out == {"n_days": 1, "n_episodes": 1}
    out2 = co.effective_n(["2026-03-01"], episodes)
    assert out2["n_episodes"] == 0


# ======================================================== portfolio_null (e)

def _synthetic_returns(n: int = 300, seed: int = 7) -> np.ndarray:
    return np.random.default_rng(seed).normal(0.0, 0.02, n)


def test_portfolio_null_table_reproducible_with_same_seed():
    returns = _synthetic_returns()
    r1 = pn.expected_combo_sharpe_distribution(returns, k=3, n_bootstrap=200, seed=53)
    r2 = pn.expected_combo_sharpe_distribution(returns, k=3, n_bootstrap=200, seed=53)
    assert r1 == r2


def test_portfolio_null_table_different_seed_changes_draws():
    returns = _synthetic_returns()
    r1 = pn.expected_combo_sharpe_distribution(returns, k=3, n_bootstrap=200, seed=1)
    r2 = pn.expected_combo_sharpe_distribution(returns, k=3, n_bootstrap=200, seed=2)
    assert r1["mean"] != r2["mean"]


def test_portfolio_null_table_mean_near_zero():
    # Under the pure-noise null E[SR] ~ 0: |mean| must stay within the
    # bootstrap MEAN's own standard error (sd/sqrt(n_bootstrap)) times 2.
    returns = _synthetic_returns(n=400, seed=11)
    n_bootstrap = 1000
    for k in (2, 5):
        r = pn.expected_combo_sharpe_distribution(returns, k=k, n_bootstrap=n_bootstrap, seed=53)
        se_of_mean = r["sd"] / np.sqrt(n_bootstrap)
        assert abs(r["mean"]) < 2.0 * se_of_mean, (k, r["mean"], se_of_mean)


def test_portfolio_null_table_sd_does_not_grow_with_k():
    # Corrected sanity check (the earlier sqrt(k)-growth claim was wrong
    # for this null -- see module docstring): sd(k=5) stays within +-25%
    # of sd(k=2), it does NOT grow like sqrt(k).
    returns = _synthetic_returns(n=400, seed=11)
    r2 = pn.expected_combo_sharpe_distribution(returns, k=2, n_bootstrap=1500, seed=53)
    r5 = pn.expected_combo_sharpe_distribution(returns, k=5, n_bootstrap=1500, seed=53)
    ratio = r5["sd"] / r2["sd"]
    assert 0.75 < ratio < 1.25, (r2["sd"], r5["sd"], ratio)


def test_portfolio_null_table_p95_positive():
    returns = _synthetic_returns()
    r = pn.expected_combo_sharpe_distribution(returns, k=3, n_bootstrap=500, seed=53)
    assert r["p95"] > 0.0
    assert r["p99"] >= r["p95"]


def test_portfolio_null_table_rejects_too_little_history():
    with pytest.raises(pn.PortfolioNullError):
        pn.expected_combo_sharpe_distribution(np.array([0.01, -0.01]), k=2, seed=1)


def test_portfolio_null_table_covers_k_2_to_5():
    returns = _synthetic_returns()
    table = pn.portfolio_null_table(returns, n_bootstrap=100, seed=53)
    assert set(table["results"]) == {2, 3, 4, 5}
    for k, r in table["results"].items():
        assert r["k"] == k
        assert {"mean", "sd", "p95", "p99"} <= set(r)


def test_selection_ceiling_grows_monotonically_and_matches_bailey_ldp():
    returns = _synthetic_returns(n=400, seed=11)
    sel = pn.selection_ceiling(returns, seed=53)
    values = [sel["results"][K]["empirical_expected_max"] for K in pn.SELECTION_K_VALUES]
    assert all(a < b for a, b in zip(values, values[1:])), values  # strictly increasing in K
    for K, r in sel["results"].items():
        emp, ana = r["empirical_expected_max"], r["analytic_expected_max"]
        assert ana > 0.0
        assert 0.7 * ana < emp < 1.3 * ana, (K, emp, ana)


def test_selection_ceiling_reproducible_with_same_seed():
    returns = _synthetic_returns()
    r1 = pn.selection_ceiling(returns, seed=53, pool_size=600, k_values=(5, 10))
    r2 = pn.selection_ceiling(returns, seed=53, pool_size=600, k_values=(5, 10))
    assert r1 == r2


def test_selection_ceiling_rejects_pool_smaller_than_max_k():
    returns = _synthetic_returns()
    with pytest.raises(pn.PortfolioNullError):
        pn.selection_ceiling(returns, pool_size=10, k_values=(5, 100))


def test_selection_ceiling_rejects_too_little_history():
    with pytest.raises(pn.PortfolioNullError):
        pn.selection_ceiling(np.array([0.01, -0.01]), seed=1)


# ================================================================ report (f)

def _report_fixture(tmp_path):
    days = [_iso(i) for i in range(60)]
    a = _mk_series("A", days, list(np.linspace(0, 1, 60)))
    b = _mk_series("B", days, list(np.linspace(0, 1, 60) + 0.1))
    stress_set = set(days[:10])
    coherence_result = co.correlation_matrix([a, b], stress_set, None, n_bootstrap=100, seed=53)
    returns = _synthetic_returns()
    portfolio_null = {
        "table": pn.portfolio_null_table(returns, n_bootstrap=100, seed=53),
        "selection_ceiling": pn.selection_ceiling(returns, seed=53, pool_size=600),
    }
    stress_canon = {"STRESS_ABS": sc.finalize_fixture(
        sc.build_stress_abs({"BTCUSDT": {d: 0.01 for d in days}}, named_dates=()))}
    return [a, b], coherence_result, stress_canon, portfolio_null


def test_report_dec53_artifact_roundtrip(tmp_path):
    series_list, coherence_result, stress_canon, portfolio_null = _report_fixture(tmp_path)
    out_dir = tmp_path / "out"
    result = rp.build_report(series_list=series_list, coherence_result=coherence_result,
                             stress_canon=stress_canon, portfolio_null=portfolio_null,
                             out_dir=out_dir, seed=53)
    summary = json.loads(Path(result["summary_path"]).read_text())
    assert summary["wp"] == "WP-10A"
    for name, art in result["artifacts"]["cluster_series"].items():
        path = Path(art["path"])
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == art["sha256"]
    bf = result["artifacts"]["bootstrap_fingerprint"]
    fp = json.loads(Path(bf["path"]).read_text())
    assert fp["generator"] == "numpy.random.default_rng"
    assert len(fp["entries"]) > 0
    assert Path(result["markdown_path"]).read_text().startswith("# WP-10(A)")


def test_report_kein_verdikt_when_artifacts_missing():
    with pytest.raises(rp.ReportError, match="KEIN VERDIKT"):
        rp.check_dec53({"cluster_series": {}, "bootstrap_fingerprint": None})


def test_report_refuses_data_harvest(tmp_path):
    series_list, *_ = _report_fixture(tmp_path)
    with pytest.raises(ValueError, match="data/harvest"):
        rp.write_cluster_series_csv(series_list[0], tmp_path / "data" / "harvest" / "out")


# ==================================================================== e2e (g)

@pytest.mark.filterwarnings("ignore")
def test_e2e_stress_canon_and_run_never_write_under_data_harvest(tmp_path):
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    harvest_base = tmp_path / "harvest"
    cache_dir = tmp_path / "barcache"
    stress_canon_out = tmp_path / "stress_canon"
    out_dir = tmp_path / "out"
    days = [_iso(i) for i in range(40)]

    for d in days:
        _write_rv_day(cache_dir, "bybit", "BTCUSDT", d, rv_target=0.01)
        _write_rv_day(cache_dir, "bybit", "ETHUSDT", d, rv_target=0.01)
        _write_dvol_day(harvest_base, "BTC_DVOL", d, close=50.0)
        _write_dvol_day(harvest_base, "ETH_DVOL", d, close=40.0)
    ts0 = (date.fromisoformat(days[0]) - EPOCH).days * 86_400_000
    for i, d in enumerate(days):
        _write_funding_day(harvest_base, "BTCUSDT", d, [(ts0 + i * 86_400_000 + 1_000, 0.0001)])
        _write_funding_day(harvest_base, "ETHUSDT", d, [(ts0 + i * 86_400_000 + 1_000, 0.0002)])

    p_canon = subprocess.run(
        [sys.executable, str(SCRIPT), "--stress-canon", "--cache-dir", str(cache_dir),
         "--stress-canon-out", str(stress_canon_out)],
        capture_output=True, text=True, cwd=ROOT)
    assert p_canon.returncode == 0, p_canon.stdout + p_canon.stderr
    assert (stress_canon_out / "stress_abs.json").is_file()
    assert (stress_canon_out / "stress_rel.json").is_file()

    p_run = subprocess.run(
        [sys.executable, str(SCRIPT), "--run", "--base", str(harvest_base),
         "--cache-dir", str(cache_dir), "--stress-canon-out", str(stress_canon_out),
         "--basis-symbols", "BTCUSDT",  # no tickers fixture -> exercises the optional skip
         "--out", str(out_dir)],
        capture_output=True, text=True, cwd=ROOT)
    assert p_run.returncode == 0, p_run.stdout + p_run.stderr
    assert (out_dir / "wp10a_summary.json").is_file()
    assert (out_dir / "wp10a_report.md").is_file()

    written_under_harvest = [p for p in harvest_base.rglob("*") if p.is_file()]
    assert all(p.suffix == ".parquet" for p in written_under_harvest), (
        f"unerwartete Datei im Harvest-Baum: "
        f"{[p for p in written_under_harvest if p.suffix != '.parquet']}")


@pytest.mark.filterwarnings("ignore")
def test_e2e_probe_reports_missing_sources_rc1(tmp_path):
    harvest_base = tmp_path / "harvest"
    cache_dir = tmp_path / "barcache"
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--probe", "--base", str(harvest_base),
         "--cache-dir", str(cache_dir)],
        capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 1
    assert "PROBE FEHLGESCHLAGEN" in p.stdout
