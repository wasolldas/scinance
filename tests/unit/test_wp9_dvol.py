"""Unit tests fuer WP-9 (Deribit-DVOL-Backfill und Quellen-Kreuzvalidierung).

Deckt ab (WP9_SPEZIFIKATION.md Abschnitt 4):
  (a) REST-Parser gegen Fixture-Antwort, inkl. falscher Feldnamen -> loud
      fail (``rest_client.parse_rows``/``unwrap_result``/``probe_call``),
  (b) Harvest-Tagesschluss auf synthetischem Baum (2 Tage, Wrapper-
      Varianten inkl. JSON-RPC-``params.data``), Probe-Status,
  (c) Crossval mit DEC-39-Fixturepaar: POSITIV (identische Quellen ->
      Befund a), NULL/ADVERSARIAL (um +0.5 verschobene Quelle -> Befund b;
      sehr kleines n mit grosser SD -> "nicht entscheidbar bei n"),
  (d) Determinismus: zweimal rechnen, identischer Fingerprint,
  (e) DEC-53-Artefakte: Tagesdifferenz-Serie + Bootstrap-Seed im Output,
  (f) Ende-zu-Ende: der Treiber-Skript-Dreischritt (--probe/--fetch/
      --crossval) gegen Fixture-REST-Seiten und einen synthetischen
      Harvest-Baum, NIE unter data/harvest schreibend.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from bybit_edge.research.wp9_dvol import crossval as cv
from bybit_edge.research.wp9_dvol import harvest_close as hc
from bybit_edge.research.wp9_dvol import rest_client as rc

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wp9_dvol_backfill.py"


# =============================================================== (a) REST

def test_parse_rows_ok():
    data = [[1_000, "10.0", "12.0", "9.0", "11.0"], [61_000, 11.0, 13.0, 10.0, 12.0]]
    rows = rc.parse_rows(data)
    assert rows == [
        {"ts_ms": 1_000, "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0},
        {"ts_ms": 61_000, "open": 11.0, "high": 13.0, "low": 10.0, "close": 12.0},
    ]


def test_parse_rows_wrong_field_count_is_loud():
    with pytest.raises(rc.DvolFieldLayoutError, match="positional fields"):
        rc.parse_rows([[1_000, 10.0, 12.0, 9.0]])  # 4 statt 5 Felder


def test_parse_rows_non_numeric_is_loud():
    with pytest.raises(rc.DvolFieldLayoutError, match="non-numeric"):
        rc.parse_rows([[1_000, "n/a", 12.0, 9.0, 11.0]])


def test_parse_rows_rejects_non_list_data():
    with pytest.raises(rc.DvolFieldLayoutError, match="expected result.data"):
        rc.parse_rows({"unexpected": "shape"})


def test_unwrap_result_shapes():
    full = {"jsonrpc": "2.0", "result": {"data": [[1, 1, 1, 1, 1]], "continuation": None}}
    bare_data = {"data": [[1, 1, 1, 1, 1]]}
    bare_list = [[1, 1, 1, 1, 1]]
    for body in (full, bare_data, bare_list):
        assert rc.unwrap_result(body) == [[1, 1, 1, 1, 1]]
    assert rc.unwrap_result({"nothing": "recognisable"}) is None


def test_probe_call_field_layout_fixture():
    page = {"jsonrpc": "2.0", "result": {"data": [
        [1_700_000_000_000, 40.0, 42.0, 39.0, 41.0]]}}
    fetcher = rc.fixture_fetcher([page])
    res = rc.probe_call("BTC", 0, 2_000_000_000_000, fetcher=fetcher)
    assert res["rows"] == [{"ts_ms": 1_700_000_000_000, "open": 40.0,
                            "high": 42.0, "low": 39.0, "close": 41.0}]
    assert res["raw_head"].startswith('{"jsonrpc"')
    assert len(res["raw_sha256"]) == 64


def test_probe_call_wrong_field_names_loud_fail():
    # Deliberately WRONG layout: named-object rows instead of the expected
    # [sek] positional 5-tuple -- exactly the drift --probe must catch.
    page = {"result": {"data": [{"timestamp": 1, "close": 41.0}]}}
    fetcher = rc.fixture_fetcher([page])
    with pytest.raises(rc.DvolFieldLayoutError):
        rc.probe_call("BTC", 0, 1, fetcher=fetcher)


def test_probe_call_rejects_bad_currency():
    with pytest.raises(ValueError):
        rc.probe_call("XRP", 0, 1, fetcher=rc.fixture_fetcher([]))


def test_probe_call_reports_deribit_error_loudly():
    page = {"jsonrpc": "2.0", "error": {"code": -1, "message": "boom"}}
    fetcher = rc.fixture_fetcher([page])
    with pytest.raises(rc.DvolFieldLayoutError, match="Deribit JSON-RPC error"):
        rc.probe_call("BTC", 0, 1, fetcher=fetcher)


def _dvol_row(ts_ms: int, close: float) -> list:
    return [ts_ms, close, close, close, close]


def test_fetch_paginates_backwards_and_dedups():
    day = 86_400_000
    page1 = {"result": {"data": [_dvol_row(10 * day, 40.0), _dvol_row(9 * day, 39.0)]}}
    page2 = {"result": {"data": [_dvol_row(9 * day, 39.0), _dvol_row(8 * day, 38.0)]}}
    page3 = {"result": {"data": []}}
    fetcher = rc.fixture_fetcher([page1, page2, page3])
    out = rc.fetch_volatility_index("BTC", 8 * day, 10 * day, fetcher=fetcher,
                                    max_req_per_sec=0)
    assert [r["ts_ms"] for r in out["rows"]] == [8 * day, 9 * day, 10 * day]
    assert out["n_pages"] == 2  # stops once oldest (8*day) <= start_ms
    assert len(out["raw_sha256"]) == 2


def test_fetch_stops_on_empty_page():
    fetcher = rc.fixture_fetcher([])  # first call already exhausted -> empty page
    out = rc.fetch_volatility_index("ETH", 0, 1_000, fetcher=fetcher, max_req_per_sec=0)
    assert out["rows"] == [] and out["n_pages"] == 1


def test_fetch_rejects_bad_currency_and_bad_range():
    with pytest.raises(ValueError):
        rc.fetch_volatility_index("DOGE", 0, 1, fetcher=rc.fixture_fetcher([]))
    with pytest.raises(ValueError):
        rc.fetch_volatility_index("BTC", 10, 1, fetcher=rc.fixture_fetcher([]))


def test_rows_to_daily_keeps_last_per_date():
    ts0, _ = rc.day_bounds_ms("2026-01-01")
    rows = [{"ts_ms": ts0, "close": 10.0}, {"ts_ms": ts0 + 1000, "close": 11.0}]
    daily = rc.rows_to_daily(rows)
    assert daily == [{"date": "2026-01-01", "ts_ms": ts0 + 1000, "close": 11.0}]


def test_write_rest_parquet_refuses_harvest_tree(tmp_path):
    with pytest.raises(ValueError, match="data/harvest"):
        rc.write_rest_parquet([], tmp_path / "data" / "harvest" / "x.parquet")


def test_write_and_read_rest_parquet_roundtrip(tmp_path):
    ts0, _ = rc.day_bounds_ms("2026-01-01")
    rows = [{"ts_ms": ts0, "open": 1.0, "high": 1.0, "low": 1.0, "close": 40.0}]
    out_path = tmp_path / "dvol_rest" / "BTC_1D.parquet"
    written = rc.write_rest_parquet(rows, out_path)
    assert written["n_rows"] == 1 and len(written["sha256_bytes"]) == 64
    back = rc.read_rest_parquet(out_path)
    assert back == [{"date": "2026-01-01", "ts_ms": ts0, "close": 40.0}]


# =========================================================== (b) harvest

def _write_dvol_day(base: Path, symbol: str, day: str, frames: list[tuple[int, str]]):
    """One deribit/dvol parquet partition, mirroring the wp6 tree writer."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    d = base / "raw" / "deribit" / "dvol" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t, _ in frames], pa.int64()),
        "ts_exchange_ms": pa.array([t for t, _ in frames], pa.int64()),
        "topic": pa.array([f"deribit_volatility_index.{symbol}"] * len(frames)),
        "stream": pa.array(["dvol"] * len(frames)),
        "symbol": pa.array([symbol] * len(frames)),
        "payload_json": pa.array([p for _, p in frames]),
    }), d / "part-0.parquet")


def test_unwrap_dvol_payload_all_shapes():
    bare = json.dumps({"volatility": 41.0, "timestamp": 1})
    data_dict = json.dumps({"data": {"volatility": 41.0}})
    params_data = json.dumps({"method": "subscription",
                              "params": {"channel": "x", "data": {"volatility": 41.0}}})
    for pj in (bare, data_dict, params_data):
        tick = hc.unwrap_dvol_payload(pj)
        assert tick is not None and hc.extract_volatility(tick) == 41.0


def test_unwrap_dvol_payload_rejects_garbage():
    assert hc.unwrap_dvol_payload("not json") is None
    assert hc.unwrap_dvol_payload(json.dumps({"nothing": "useful"})) is None
    assert hc.unwrap_dvol_payload(json.dumps([1, 2])) is None


@pytest.mark.filterwarnings("ignore")
def test_daily_close_two_days_wrapper_variants(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    ms0 = (date(2026, 1, 1) - date(1970, 1, 1)).days * 86_400_000
    ms1 = (date(2026, 1, 2) - date(1970, 1, 1)).days * 86_400_000
    # Tag 1: bare payload, zwei Frames -- der SPAETERE (ts groesser) muss gewinnen.
    _write_dvol_day(base, "BTC_DVOL", "2026-01-01", [
        (ms0 + 1_000, json.dumps({"volatility": 40.0})),
        (ms0 + 2_000, json.dumps({"volatility": 40.5})),
    ])
    # Tag 2: JSON-RPC-Envelope (params.data).
    _write_dvol_day(base, "BTC_DVOL", "2026-01-02", [
        (ms1 + 500, json.dumps({"params": {"data": {"volatility": 41.2}}})),
    ])
    con = duckdb.connect()
    rows = hc.daily_close(con, base, "BTC_DVOL", ["2026-01-01", "2026-01-02"])
    con.close()
    by_date = {r["date"]: r for r in rows}
    assert by_date["2026-01-01"]["close"] == pytest.approx(40.5)
    assert by_date["2026-01-01"]["n_frames"] == 2
    assert by_date["2026-01-02"]["close"] == pytest.approx(41.2)
    assert by_date["2026-01-01"]["manifest_done"] is None  # kein Manifest im Fixture-Baum


@pytest.mark.filterwarnings("ignore")
def test_daily_close_raises_on_field_missing(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    ms0 = (date(2026, 1, 1) - date(1970, 1, 1)).days * 86_400_000
    _write_dvol_day(base, "BTC_DVOL", "2026-01-01", [
        (ms0, json.dumps({"someOtherField": 1.0})),
    ])
    con = duckdb.connect()
    try:
        with pytest.raises(hc.DvolFieldLayoutError, match="volatility field layout"):
            hc.daily_close(con, base, "BTC_DVOL", ["2026-01-01"])
    finally:
        con.close()


@pytest.mark.filterwarnings("ignore")
def test_daily_close_no_frames_and_discover_days(tmp_path):
    pytest.importorskip("duckdb")
    import duckdb
    base = tmp_path / "harvest"
    ms0 = (date(2026, 1, 1) - date(1970, 1, 1)).days * 86_400_000
    _write_dvol_day(base, "BTC_DVOL", "2026-01-01", [(ms0, json.dumps({"volatility": 40.0}))])
    assert hc.discover_harvest_days(base, "BTC_DVOL") == ["2026-01-01"]
    assert hc.discover_harvest_days(base, "ETH_DVOL") == []
    con = duckdb.connect()
    rows = hc.daily_close(con, base, "BTC_DVOL", ["2026-01-01", "2026-01-02"])
    con.close()
    by_date = {r["date"]: r for r in rows}
    assert by_date["2026-01-02"]["status"] == "NO_FRAMES"
    assert "close" not in by_date["2026-01-02"]


# ============================================================ (c)-(e) crossval

def _series(n: int, start: str = "2026-01-01", base_val: float = 40.0,
            wobble: float = 0.05) -> list[dict]:
    d0 = date.fromisoformat(start)
    return [{"date": (d0 + timedelta(days=i)).isoformat(),
             "close": base_val + (0.3 if i % 7 == 0 else 0.0) + wobble * ((-1) ** i)}
            for i in range(n)]


def test_dec39_positive_identical_sources_gives_verdict_a():
    rest = _series(60)
    harvest = [{"date": r["date"], "close": r["close"]} for r in rest]
    out = cv.evaluate(rest, harvest, seed=53)
    assert out["verdict"] == "a"
    assert out["reachable"] is True
    assert abs(out["bootstrap"]["mean"]) < 0.05


def test_dec39_adversarial_shifted_source_gives_verdict_b():
    rest = _series(60)
    harvest = [{"date": r["date"], "close": r["close"] - 0.5} for r in rest]
    out = cv.evaluate(rest, harvest, seed=53)
    assert out["verdict"] == "b"
    assert out["bootstrap"]["mean"] == pytest.approx(0.5, abs=0.1)


def test_dec39_small_n_large_sd_is_undecidable_not_verdict_b():
    # Sehr kleines n (4 Tage) MIT grosser Streuung: das CI kann bei diesem n
    # nicht ins Band passen, egal wo das wahre Mittel liegt -- Befund MUSS
    # "nicht entscheidbar bei n" sein, NIE (b).
    rest = [{"date": f"2026-01-0{i+1}", "close": 40.0 + v}
            for i, v in enumerate([0.0, 5.0, -5.0, 6.0])]
    harvest = [{"date": r["date"], "close": 40.0} for r in rest]
    out = cv.evaluate(rest, harvest, seed=53)
    assert out["verdict"] == "nicht entscheidbar bei n"
    assert out["reachable"] is False


def test_crossval_reachability_reported_before_verdict_fields_present():
    rest = _series(30)
    harvest = [{"date": r["date"], "close": r["close"]} for r in rest]
    out = cv.evaluate(rest, harvest, seed=53)
    dist = out["distribution"]
    assert all(k in dist for k in ("n", "p5", "p50", "p95", "sd", "autocorr_lag1"))
    assert dist["n"] == 30


def test_crossval_empty_overlap_is_undecidable():
    out = cv.evaluate(_series(5), [{"date": "1999-01-01", "close": 1.0}], seed=53)
    assert out["n_overlap_days"] == 0
    assert out["verdict"] == "nicht entscheidbar bei n"


def test_determinism_identical_fingerprint_across_two_runs():
    rest = _series(45)
    harvest = [{"date": r["date"], "close": r["close"] - 0.5} for r in rest]
    out1 = cv.evaluate(rest, harvest, seed=53)
    out2 = cv.evaluate(rest, harvest, seed=53)
    fp1 = hashlib.sha256(json.dumps(
        {"boot": out1["bootstrap"], "diffs": out1["daily_differences"],
         "verdict": out1["verdict"]}, sort_keys=True).encode()).hexdigest()
    fp2 = hashlib.sha256(json.dumps(
        {"boot": out2["bootstrap"], "diffs": out2["daily_differences"],
         "verdict": out2["verdict"]}, sort_keys=True).encode()).hexdigest()
    assert fp1 == fp2
    assert out1["bootstrap"]["ci_lo"] == out2["bootstrap"]["ci_lo"]
    assert out1["bootstrap"]["ci_hi"] == out2["bootstrap"]["ci_hi"]


def test_different_seed_changes_replicates_but_not_the_stored_seed_field():
    rest = _series(45)
    harvest = [{"date": r["date"], "close": r["close"]} for r in rest]
    out_a = cv.evaluate(rest, harvest, seed=1)
    out_b = cv.evaluate(rest, harvest, seed=2)
    assert out_a["bootstrap"]["seed"] == 1
    assert out_b["bootstrap"]["seed"] == 2
    # different seeds may (not must) shift the empirical CI edges slightly
    assert isinstance(out_a["bootstrap"]["ci_lo"], float)


def test_dec53_artifacts_present_in_output():
    rest = _series(20)
    harvest = [{"date": r["date"], "close": r["close"]} for r in rest]
    out = cv.evaluate(rest, harvest, seed=53)
    assert len(out["daily_differences"]) == 20
    assert {"date", "rest_close", "harvest_close", "diff"} <= out["daily_differences"][0].keys()
    b = out["bootstrap"]
    assert b["seed"] == 53 and b["block_len"] == cv.BLOCK_LEN_DAYS
    assert b["n_bootstrap"] == cv.N_BOOTSTRAP


def test_stationary_block_bootstrap_ci_rejects_degenerate_input():
    with pytest.raises(cv.CrossvalError):
        cv.stationary_block_bootstrap_mean_ci([1.0])


# ==================================================================== (f) e2e

def _rest_page(days: list[str], base_val: float = 40.0) -> dict:
    rows = []
    for i, day in enumerate(days):
        ts0, _ = rc.day_bounds_ms(day)
        v = base_val + 0.1 * i
        rows.append([ts0, v, v, v, v])
    return {"jsonrpc": "2.0", "result": {"data": rows}}


@pytest.mark.filterwarnings("ignore")
def test_e2e_probe_fetch_crossval_pipeline(tmp_path):
    pytest.importorskip("duckdb")
    pytest.importorskip("pyarrow")
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(19, -1, -1)]  # 20 Tage

    fixture = {cur: [_rest_page(days, base_val=40.0 if cur == "BTC" else 25.0)]
              for cur in ("BTC", "ETH")}
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    rest_dir = tmp_path / "dvol_rest"
    harvest_base = tmp_path / "harvest"
    out_dir = tmp_path / "out"

    # -- Schritt 1: Probe --
    p1 = subprocess.run(
        [sys.executable, str(SCRIPT), "--probe", "--fixture", str(fixture_path)],
        capture_output=True, text=True, cwd=ROOT)
    assert p1.returncode == 0, p1.stdout + p1.stderr
    assert "raw[:300]" in p1.stdout

    # -- Schritt 2: Fetch --
    p2 = subprocess.run(
        [sys.executable, str(SCRIPT), "--fetch", "--fixture", str(fixture_path),
         "--rest-dir", str(rest_dir)],
        capture_output=True, text=True, cwd=ROOT)
    assert p2.returncode == 0, p2.stdout + p2.stderr
    assert (rest_dir / "BTC_1D.parquet").is_file()
    manifest = json.loads((rest_dir / "BTC_1D.manifest.json").read_text())
    assert manifest["n_rows"] == 20 and len(manifest["sha256_parquet"]) == 64
    assert manifest["field_layout_note"].startswith("[sek]")

    # -- Harvest-Baum: gleiche Werte fuer 15 der 20 Tage (Ueberlappung) --
    for cur, base_val, symbol in (("BTC", 40.0, "BTC_DVOL"), ("ETH", 25.0, "ETH_DVOL")):
        for i, day in enumerate(days[:15]):
            ts0, _ = rc.day_bounds_ms(day)
            v = base_val + 0.1 * i
            _write_dvol_day(harvest_base, symbol, day,
                            [(ts0 + 1000, json.dumps({"volatility": v}))])

    # -- Schritt 3: Crossval --
    p3 = subprocess.run(
        [sys.executable, str(SCRIPT), "--crossval",
         "--base", str(harvest_base), "--rest-dir", str(rest_dir), "--out", str(out_dir)],
        capture_output=True, text=True, cwd=ROOT)
    assert p3.returncode == 0, p3.stdout + p3.stderr

    summary = json.loads((out_dir / "wp9_summary.json").read_text())
    assert summary["seed"] == cv.DEFAULT_SEED
    for cur in ("BTC", "ETH"):
        r = summary["results"][cur]
        assert r["status"] == "OK"
        assert r["n_overlap_days"] == 15
        assert r["verdict"] == "a"  # identische Quellen konstruiert
        assert Path(r["diff_series_csv"]).is_file()
    assert (out_dir / "wp9_report.md").read_text().startswith("# WP-9")

    # -- NIE unter data/harvest geschrieben --
    written_under_harvest = list(harvest_base.rglob("*"))
    allowed_suffixes = {".parquet"}
    for p in written_under_harvest:
        if p.is_file():
            assert p.suffix in allowed_suffixes, f"unerwartete Datei im Harvest-Baum: {p}"
    assert not (harvest_base / "dvol_rest").exists()


@pytest.mark.filterwarnings("ignore")
def test_e2e_probe_field_layout_drift_is_loud_rc1(tmp_path):
    bad_page = {"result": {"data": [{"not": "the expected [sek] shape"}]}}
    fixture = {"BTC": [bad_page], "ETH": [bad_page]}
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--probe", "--fixture", str(fixture_path)],
        capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 1
    assert "LAUT GESCHEITERT" in p.stdout
