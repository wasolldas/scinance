"""Unit tests fuer WP-10(A2) Backfill-Modus (DEC-62, ``--source backfill``).

Deckt ab:
  (a) ``series.funding_daily_cashflow_backfill`` -- DEC-39-Trio: POSITIV
      (synthetische panel_1d-Partition mit bekanntem funding_sum -> exakte
      Tageswerte, Quelle="panel_1d"), NULL/ADVERSARIAL (funding_n=0/None
      werden ausgeschlossen, nie als gemessene Null gezaehlt), REST-
      Fallback OHNE Netzwerk (monkeypatch ``bybit_rest.fetch_funding_
      history`` -- niemals ein echter Aufruf).
  (b) ``series.iv_rv_diff_series_backfill`` -- DEC-39-Trio: POSITIV
      (synthetisches REST-DVOL-Parquet + Bar-Cache -> exakte IV-RV-
      Differenz), NULL (fehlendes Parquet / fehlende Spalten -> LAUTER
      Fehler, nie ``None``/leere Serie).
  (c) ``comparison.compare_value_series``/``compare_dvol_close`` --
      ADVERSARIAL: ein absichtlich abweichender Tag wird als n_days_diff=1
      mit dem korrekten Tag gemeldet; eine fehlende Bestandsserie stuerzt
      nie ab (Status ``BESTAND_FEHLT``).
  (d) ``report.build_report`` im Default-Aufruf (kein ``source``/
      ``comparison`` uebergeben, wie es der ``--source harvest``-Zweig des
      Treiberskripts weiterhin tut) liefert GENAU die Vor-DEC-62-Form --
      "bestehende Laeufe sind byte-identisch" (Auftrag Punkt 2).
  (e) Ende-zu-Ende: ``--source backfill`` ueber den Treiber-Dreischritt,
      volloffline (panel_1d + REST-DVOL-Parquet lokal, kein Netzwerk),
      Vergleichszeile + KEIN-PASS/FAIL-Text im Report, nie unter
      data/harvest schreibend.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp10_coherence import coherence as co
from bybit_edge.research.wp10_coherence import comparison as cmp
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


def _day_start_ms(day: str) -> int:
    return (date.fromisoformat(day) - EPOCH).days * 86_400_000


def _mk_series(name: str, days: list[str], values: list[float]) -> dict:
    return {"name": name, "kind": "synthetic", "symbol": name, "provenance": {},
            "days": list(days), "values": list(values),
            "coverage": {"n_days": len(days)}, "status": "OK", "reason": None}


def _write_panel_year(panel_base: Path, symbol: str, year: int,
                      rows: list[tuple[int, int | None, float | None]], *,
                      frozen: bool = True) -> Path:
    """A MINIMAL ``panel_1d`` year partition -- only the three columns
    ``funding_daily_cashflow_backfill`` reads (``start_ms``, ``funding_n``,
    ``funding_sum``). ``rows`` entries with ``funding_n=None`` mirror
    "never populated"; ``funding_n=0`` mirrors "measured zero settlements"
    -- both must be excluded by the reader. Own local copy of a writer
    (repo test convention: no cross-import between test modules)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    from bybit_edge.research.wp7_universe import panel_store as ps

    path = ps.partition_path(panel_base, symbol, year, frozen=frozen)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        "start_ms": pa.array([r[0] for r in rows], pa.int64()),
        "funding_n": pa.array([r[1] for r in rows], pa.int64()),
        "funding_sum": pa.array([r[2] for r in rows], pa.float64()),
    })
    pq.write_table(table, path)
    return path


def _write_bar_day(cache_dir: Path, exchange: str, symbol: str, day: str,
                   closes: list[float]) -> None:
    """Own local copy of the WP-0 bar-cache day-partition writer (mirrors
    ``test_wp10_coherence.py``'s helper -- no cross-import)."""
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
    n = n_bars
    step = rv_target / np.sqrt(n - 1)
    log_px = np.cumsum([0.0] + [step] * (n - 1))
    closes = list(base_price * np.exp(log_px))
    _write_bar_day(cache_dir, exchange, symbol, day, closes)


def _write_dvol_day(base: Path, symbol: str, day: str, close: float) -> None:
    """Own local copy (harvest ``deribit/dvol`` partition, mirrors
    ``test_wp10_coherence.py``'s helper -- no cross-import)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "deribit" / "dvol" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    ts_ms = _day_start_ms(day) + 1_000
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([ts_ms * 1_000_000], pa.int64()),
        "ts_exchange_ms": pa.array([ts_ms], pa.int64()),
        "topic": pa.array([f"deribit_volatility_index.{symbol}"]),
        "stream": pa.array(["dvol"]),
        "symbol": pa.array([symbol]),
        "payload_json": pa.array([json.dumps({"volatility": close})]),
    }), d / "part-0.parquet")


def _write_funding_day(base: Path, symbol: str, day: str, events: list[tuple[int, float]]) -> None:
    """Own local copy (harvest ``bybit/rest.fundingRate`` partition)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "bybit" / "rest.fundingRate" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    payloads = [json.dumps({"fundingRate": str(rate), "fundingRateTimestamp": str(ts), "symbol": symbol})
                for ts, rate in events]
    ts_list = [e[0] for e in events]
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts_list], pa.int64()),
        "ts_exchange_ms": pa.array(ts_list, pa.int64()),
        "topic": pa.array([f"rest.fundingRate.{symbol}"] * len(events)),
        "stream": pa.array(["rest.fundingRate"] * len(events)),
        "symbol": pa.array([symbol] * len(events)),
        "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


# ================================================ (a) funding backfill

@pytest.mark.filterwarnings("ignore")
def test_funding_backfill_panel_source_exact_values(tmp_path):
    pytest.importorskip("pyarrow")
    panel_base = tmp_path / "panel_1d"
    _write_panel_year(panel_base, "BTCUSDT", 2020, [
        (_day_start_ms("2020-05-10"), 3, 0.0006),
    ])
    out = sr.funding_daily_cashflow_backfill("BTCUSDT", "2020-05-01", "2020-12-31",
                                             panel_base=panel_base)
    assert out["status"] == "OK"
    assert out["provenance"]["source"] == "panel_1d"
    assert out["days"] == ["2020-05-10"]
    assert out["values"][0] == pytest.approx(0.0006)
    # fingerprint is deterministic and reproducible from the days/values alone.
    assert out["provenance"]["fingerprint_sha256"] == sr._fingerprint_days_values(
        dict(zip(out["days"], out["values"])))


@pytest.mark.filterwarnings("ignore")
def test_funding_backfill_excludes_funding_n_zero_and_none(tmp_path):
    # ADVERSARIAL (DEC-39): a measured-zero-settlement day (funding_n=0)
    # and a never-populated day (funding_n=None) must BOTH be excluded --
    # neither counts as a real zero cashflow day.
    pytest.importorskip("pyarrow")
    panel_base = tmp_path / "panel_1d"
    _write_panel_year(panel_base, "BTCUSDT", 2020, [
        (_day_start_ms("2020-05-10"), 3, 0.0006),
        (_day_start_ms("2020-05-11"), 0, 0.0),
        (_day_start_ms("2020-05-12"), None, None),
    ])
    out = sr.funding_daily_cashflow_backfill("BTCUSDT", "2020-05-01", "2020-05-31",
                                             panel_base=panel_base)
    assert out["days"] == ["2020-05-10"]


@pytest.mark.filterwarnings("ignore")
def test_funding_backfill_falls_back_to_direct_rest_when_panel_year_missing(tmp_path, monkeypatch):
    # panel_base given but the 2020 year partition is absent -> falls back
    # to the whole range from direct REST, never a partial per-year mix.
    # NO NETWORK: fetch_funding_history is monkeypatched (see the
    # dedicated no-network test above for why).
    pytest.importorskip("pyarrow")
    panel_base = tmp_path / "panel_1d"
    panel_base.mkdir(parents=True)

    def fake_fetch(symbol, start_ms, end_ms, *, category="linear"):
        return {"rows": [{"symbol": symbol, "funding_rate": 0.0001,
                          "ts_ms": _day_start_ms("2020-05-10") + 1_000}]}

    monkeypatch.setattr(sr._bybit_rest, "fetch_funding_history", fake_fetch)
    out = sr.funding_daily_cashflow_backfill("BTCUSDT", "2020-05-01", "2020-05-31",
                                             panel_base=panel_base)
    # no partitions at all under panel_base -- _panel_years_available is False.
    assert out["provenance"]["source"] == "rest_direct"
    assert out["days"] == ["2020-05-10"]


def test_funding_backfill_rest_fallback_no_network(monkeypatch):
    # NO NETWORK: fetch_funding_history is monkeypatched -- a real call
    # would fail in this sandbox (egress blocked), so if this test passes
    # without the patch it would prove nothing; the patch is the point.
    calls: list[tuple] = []

    def fake_fetch(symbol, start_ms, end_ms, *, category="linear"):
        calls.append((symbol, start_ms, end_ms, category))
        day_ms = _day_start_ms("2020-05-10")
        return {"rows": [
            {"symbol": symbol, "funding_rate": 0.0001, "ts_ms": day_ms + 1_000},
            {"symbol": symbol, "funding_rate": 0.0002, "ts_ms": day_ms + 2_000},
        ]}

    monkeypatch.setattr(sr._bybit_rest, "fetch_funding_history", fake_fetch)
    out = sr.funding_daily_cashflow_backfill("BTCUSDT", "2020-05-01", "2020-05-31", panel_base=None)
    assert calls, "fetch_funding_history was never called (fixture wiring broken)"
    assert out["status"] == "OK"
    assert out["provenance"]["source"] == "rest_direct"
    assert out["days"] == ["2020-05-10"]
    assert out["values"][0] == pytest.approx(0.0003)


def test_funding_backfill_rest_layout_error_propagates_loud(monkeypatch):
    # loud fail instead of silent None: a BybitFieldLayoutError from the
    # (monkeypatched) client must propagate unchanged, never be swallowed.
    from bybit_edge.research.wp7_universe.bybit_rest import BybitFieldLayoutError

    def fake_fetch(symbol, start_ms, end_ms, *, category="linear"):
        raise BybitFieldLayoutError("deliberately broken fixture")

    monkeypatch.setattr(sr._bybit_rest, "fetch_funding_history", fake_fetch)
    with pytest.raises(Exception, match="deliberately broken fixture"):
        sr.funding_daily_cashflow_backfill("BTCUSDT", "2020-05-01", "2020-05-31", panel_base=None)


# ================================================ (b) iv-rv backfill

@pytest.mark.filterwarnings("ignore")
def test_iv_rv_backfill_exact_values(tmp_path):
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    from bybit_edge.research.wp9_dvol import rest_client as dvrc

    dvol_dir = tmp_path / "dvol_rest"
    cache_dir = tmp_path / "barcache"
    days = [_iso(i) for i in range(3)]
    rows = [{"ts_ms": _day_start_ms(d) + 1_000, "close": 50.0 + i} for i, d in enumerate(days)]
    dvrc.write_rest_parquet(rows, dvol_dir / "BTC_1D.parquet")
    for d in days:
        _write_rv_day(cache_dir, "bybit", "BTCUSDT", d, rv_target=0.01)

    out = sr.iv_rv_diff_series_backfill(cache_dir, currency="BTC", bar_exchange="bybit",
                                        bar_symbol="BTCUSDT", dvol_rest_dir=dvol_dir, days=days)
    assert out["status"] == "OK"
    assert out["days"] == days
    rv_pct = 0.01 * np.sqrt(_rv.ANNUALIZATION_DAYS_PER_YEAR) * 100.0
    assert out["values"][0] == pytest.approx(50.0 - rv_pct)
    assert out["values"][2] == pytest.approx(52.0 - rv_pct)
    assert "dvol_rest_sha256" in out["provenance"]


def test_iv_rv_backfill_empty_days_is_skipped():
    out = sr.iv_rv_diff_series_backfill("unused", currency="BTC", bar_exchange="bybit",
                                        bar_symbol="BTCUSDT", dvol_rest_dir="unused", days=[])
    assert out["status"] == "SKIPPED_NO_DATA"


def test_iv_rv_backfill_missing_parquet_is_loud_fail(tmp_path):
    with pytest.raises(sr.SeriesError, match="REST-DVOL-Parquet fehlt"):
        sr.iv_rv_diff_series_backfill(tmp_path / "barcache", currency="BTC", bar_exchange="bybit",
                                      bar_symbol="BTCUSDT", dvol_rest_dir=tmp_path / "dvol_rest",
                                      days=["2020-05-10"])


@pytest.mark.filterwarnings("ignore")
def test_iv_rv_backfill_missing_columns_is_loud_fail(tmp_path):
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as pq

    dvol_dir = tmp_path / "dvol_rest"
    dvol_dir.mkdir(parents=True)
    # [sek] layout-drift fixture: no 'close' column at all.
    pq.write_table(pa.table({"date": pa.array(["2020-05-10"]), "foo": pa.array([1.0])}),
                   dvol_dir / "BTC_1D.parquet")
    with pytest.raises(sr.SeriesError, match="BTC"):
        sr.iv_rv_diff_series_backfill(tmp_path / "barcache", currency="BTC", bar_exchange="bybit",
                                      bar_symbol="BTCUSDT", dvol_rest_dir=dvol_dir,
                                      days=["2020-05-10"])


# ================================================ (c) comparison

def test_comparison_value_series_reports_single_differing_day():
    days = [_iso(i) for i in range(5)]
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    backfill = _mk_series("funding_backfill_BTCUSDT", days, values)
    harvest_values = list(values)
    harvest_values[2] = 999.0  # deliberately different day
    harvest = _mk_series("funding_BTCUSDT", days, harvest_values)
    result = cmp.compare_value_series("funding_BTCUSDT", backfill, harvest)
    assert result["status"] == "OK"
    assert result["n_overlap"] == 5
    assert result["n_days_diff"] == 1
    assert result["diff_days"] == [days[2]]
    assert result["max_abs_diff"] == pytest.approx(996.0)


def test_comparison_value_series_identical_on_overlap_reports_zero_diff():
    days = [_iso(i) for i in range(5)]
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    backfill = _mk_series("A", days, values)
    harvest = _mk_series("A", days, list(values))
    result = cmp.compare_value_series("A", backfill, harvest)
    assert result["n_days_diff"] == 0
    assert result["max_abs_diff"] == pytest.approx(0.0)


def test_comparison_value_series_absent_harvest_never_crashes():
    days = [_iso(i) for i in range(3)]
    backfill = _mk_series("x", days, [1.0, 2.0, 3.0])
    result = cmp.compare_value_series("x", backfill, None)
    assert result["status"] == "BESTAND_FEHLT"
    assert result["n_overlap"] == 0
    # a Bestandsserie with status != OK is likewise absent, never raised.
    skipped = _mk_series("x", [], [])
    skipped["status"] = "SKIPPED_NO_DATA"
    result2 = cmp.compare_value_series("x", backfill, skipped)
    assert result2["status"] == "BESTAND_FEHLT"


def test_comparison_dvol_close_within_band_and_absent():
    days = [_iso(i) for i in range(3)]
    backfill_dvol = {d: 50.0 for d in days}
    harvest_dvol = {d: 50.2 for d in days}
    result = cmp.compare_dvol_close("ivrv_BTC", backfill_dvol, harvest_dvol)
    assert result["status"] == "OK"
    assert result["within_band"] is True
    assert result["max_abs_diff"] == pytest.approx(0.2)

    over_band = {d: 51.0 for d in days}
    result2 = cmp.compare_dvol_close("ivrv_BTC", over_band, harvest_dvol)
    assert result2["within_band"] is False
    assert result2["n_days_diff"] == 3

    absent = cmp.compare_dvol_close("ivrv_BTC", backfill_dvol, {})
    assert absent["status"] == "BESTAND_FEHLT"


# ================================================ (d) report byte-identity

@pytest.mark.filterwarnings("ignore")
def test_build_report_harvest_default_has_no_backfill_keys(tmp_path):
    # The --source harvest driver branch calls build_report WITHOUT
    # source/comparison (unchanged from before DEC-62) -- summary and
    # markdown must stay exactly the pre-DEC-62 shape.
    days = [_iso(i) for i in range(20)]
    a = _mk_series("A", days, list(np.linspace(0, 1, 20)))
    b = _mk_series("B", days, list(np.linspace(0, 1, 20) + 0.1))
    stress_set = set(days[:5])
    coherence_result = co.correlation_matrix([a, b], stress_set, None, n_bootstrap=50, seed=53)
    returns = np.random.default_rng(7).normal(0.0, 0.02, 300)
    portfolio_null = {"table": pn.portfolio_null_table(returns, n_bootstrap=50, seed=53),
                      "selection_ceiling": pn.selection_ceiling(returns, seed=53, pool_size=600)}
    stress_canon = {"STRESS_ABS": sc.finalize_fixture(
        sc.build_stress_abs({"BTCUSDT": {d: 0.01 for d in days}}, named_dates=()))}
    result = rp.build_report(series_list=[a, b], coherence_result=coherence_result,
                             stress_canon=stress_canon, portfolio_null=portfolio_null,
                             out_dir=tmp_path / "out", seed=53)
    summary = json.loads(Path(result["summary_path"]).read_text())
    assert "source" not in summary
    assert "comparison" not in summary
    md = Path(result["markdown_path"]).read_text()
    assert "Bestand vs. Backfill" not in md
    assert "backfill" not in md.lower()


def test_build_report_backfill_mode_adds_source_and_comparison_keys(tmp_path):
    days = [_iso(i) for i in range(20)]
    a = _mk_series("A", days, list(np.linspace(0, 1, 20)))
    b = _mk_series("B", days, list(np.linspace(0, 1, 20) + 0.1))
    coherence_result = co.correlation_matrix([a, b], set(), None, n_bootstrap=50, seed=53)
    returns = np.random.default_rng(7).normal(0.0, 0.02, 300)
    portfolio_null = {"table": pn.portfolio_null_table(returns, n_bootstrap=50, seed=53),
                      "selection_ceiling": None}
    stress_canon = {"STRESS_ABS": sc.finalize_fixture(
        sc.build_stress_abs({"BTCUSDT": {d: 0.01 for d in days}}, named_dates=()))}
    comparison = [cmp.compare_value_series("A", a, a)]
    result = rp.build_report(series_list=[a, b], coherence_result=coherence_result,
                             stress_canon=stress_canon, portfolio_null=portfolio_null,
                             out_dir=tmp_path / "out", seed=53, source="backfill",
                             comparison=comparison)
    summary = json.loads(Path(result["summary_path"]).read_text())
    assert summary["source"] == "backfill"
    assert summary["comparison"][0]["name"] == "A"
    md = Path(result["markdown_path"]).read_text()
    assert "KEIN PASS/FAIL" in md
    assert "Bestand vs. Backfill (Ueberlappung)" in md


# ================================================ (e) e2e --source backfill

@pytest.mark.filterwarnings("ignore")
def test_e2e_source_backfill_offline_produces_comparison_never_writes_harvest(tmp_path):
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    from bybit_edge.research.wp9_dvol import rest_client as dvrc

    harvest_base = tmp_path / "harvest"
    cache_dir = tmp_path / "barcache"
    panel_base = tmp_path / "panel_1d"
    dvol_rest_dir = tmp_path / "dvol_rest"
    stress_canon_out = tmp_path / "stress_canon"
    out_dir = tmp_path / "out"
    days = [_iso(i) for i in range(40)]
    year = date.fromisoformat(days[0]).year

    for d in days:
        _write_rv_day(cache_dir, "bybit", "BTCUSDT", d, rv_target=0.01)
        _write_rv_day(cache_dir, "bybit", "ETHUSDT", d, rv_target=0.01)
        _write_dvol_day(harvest_base, "BTC_DVOL", d, close=50.0)
        _write_dvol_day(harvest_base, "ETH_DVOL", d, close=40.0)
    for i, d in enumerate(days):
        _write_funding_day(harvest_base, "BTCUSDT", d, [(_day_start_ms(d) + 1_000, 0.0001)])
        _write_funding_day(harvest_base, "ETHUSDT", d, [(_day_start_ms(d) + 1_000, 0.0002)])

    # panel_1d: identical to harvest, EXCEPT day index 5 for BTC (comparison diff row).
    btc_rows, eth_rows = [], []
    for i, d in enumerate(days):
        rate = 0.0001 if i != 5 else 0.0009
        btc_rows.append((_day_start_ms(d), 1, rate))
        eth_rows.append((_day_start_ms(d), 1, 0.0002))
    _write_panel_year(panel_base, "BTCUSDT", year, btc_rows)
    _write_panel_year(panel_base, "ETHUSDT", year, eth_rows)

    for cur, base_close in (("BTC", 50.0), ("ETH", 40.0)):
        rows = [{"ts_ms": _day_start_ms(d) + 1_000, "close": base_close} for d in days]
        dvrc.write_rest_parquet(rows, dvol_rest_dir / f"{cur}_1D.parquet")

    p_canon = subprocess.run(
        [sys.executable, str(SCRIPT), "--stress-canon", "--cache-dir", str(cache_dir),
         "--stress-canon-out", str(stress_canon_out)],
        capture_output=True, text=True, cwd=ROOT)
    assert p_canon.returncode == 0, p_canon.stdout + p_canon.stderr

    p_run = subprocess.run(
        [sys.executable, str(SCRIPT), "--run", "--source", "backfill",
         "--base", str(harvest_base), "--cache-dir", str(cache_dir),
         "--panel-base", str(panel_base), "--dvol-rest-dir", str(dvol_rest_dir),
         "--funding-symbols", "BTCUSDT,ETHUSDT", "--ivrv-currencies", "BTC,ETH",
         "--basis-symbols", "BTCUSDT",
         "--stress-canon-out", str(stress_canon_out),
         "--start", days[0], "--end", days[-1], "--out", str(out_dir)],
        capture_output=True, text=True, cwd=ROOT)
    assert p_run.returncode == 0, p_run.stdout + p_run.stderr
    # no real network anywhere: panel_1d + dvol_rest are both local fixtures,
    # so a REST-fallback attempt (which WOULD hit the blocked egress proxy)
    # never fires -- assert the printed source confirms panel_1d was used.
    assert "source=panel_1d" in p_run.stdout

    summary = json.loads((out_dir / "wp10a_summary.json").read_text())
    assert summary["source"] == "backfill"
    by_name = {c["name"]: c for c in summary["comparison"]}
    assert by_name["funding_BTCUSDT"]["status"] == "OK"
    assert by_name["funding_BTCUSDT"]["n_days_diff"] == 1
    assert by_name["funding_BTCUSDT"]["diff_days"] == [days[5]]
    assert by_name["funding_ETHUSDT"]["n_days_diff"] == 0

    md = (out_dir / "wp10a_report.md").read_text()
    assert "Bestand vs. Backfill (Ueberlappung)" in md
    assert "KEIN PASS/FAIL" in md

    written_under_harvest = [p for p in harvest_base.rglob("*") if p.is_file()]
    assert all(p.suffix == ".parquet" for p in written_under_harvest), (
        f"unerwartete Datei im Harvest-Baum: "
        f"{[p for p in written_under_harvest if p.suffix != '.parquet']}")


@pytest.mark.filterwarnings("ignore")
def test_e2e_probe_source_backfill_reports_missing_dvol_rest_rc1(tmp_path):
    pytest.importorskip("duckdb")
    harvest_base = tmp_path / "harvest"
    cache_dir = tmp_path / "barcache"
    dvol_rest_dir = tmp_path / "dvol_rest"
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--probe", "--source", "backfill",
         "--base", str(harvest_base), "--cache-dir", str(cache_dir),
         "--dvol-rest-dir", str(dvol_rest_dir),
         "--funding-symbols", "BTCUSDT", "--ivrv-currencies", "BTC",
         "--basis-symbols", "BTCUSDT"],
        capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 1
    assert "PROBE FEHLGESCHLAGEN" in p.stdout
    assert "vorhanden=False" in p.stdout


@pytest.mark.filterwarnings("ignore")
def test_e2e_probe_source_backfill_missing_panel_never_fails(tmp_path):
    # panel_1d absent must NEVER flip the probe's rc -- funding always has
    # the direct-REST fallback (spec: "muss trotzdem funktionieren").
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    from bybit_edge.research.wp9_dvol import rest_client as dvrc

    harvest_base = tmp_path / "harvest"
    cache_dir = tmp_path / "barcache"
    dvol_rest_dir = tmp_path / "dvol_rest"
    panel_base = tmp_path / "panel_1d"  # deliberately never created
    days = [_iso(i) for i in range(3)]
    for d in days:
        _write_rv_day(cache_dir, "bybit", "BTCUSDT", d, rv_target=0.01)
    rows = [{"ts_ms": _day_start_ms(d) + 1_000, "close": 50.0} for d in days]
    dvrc.write_rest_parquet(rows, dvol_rest_dir / "BTC_1D.parquet")

    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--probe", "--source", "backfill",
         "--base", str(harvest_base), "--cache-dir", str(cache_dir),
         "--panel-base", str(panel_base), "--dvol-rest-dir", str(dvol_rest_dir),
         "--funding-symbols", "BTCUSDT", "--ivrv-currencies", "BTC",
         "--basis-symbols", "BTCUSDT"],
        capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "vorhanden=False" in p.stdout  # panel_1d reported absent
    assert "PROBE FEHLGESCHLAGEN" not in p.stdout
