"""Unit tests for WP-10(B) -- Maker-Fill-Schattenmessung (KAPITALFREI).

  (a) ``queue_model`` mechanics: FIFO vs pro-rata bounds, touch departure,
      adverse selection sign/scale.
  (b) THE DEC-39 TRIO (mandatory) -- POSITIVE (known queue + trades ->
      known fills, both conventions; pro-rata bound >= FIFO bound), NULL
      (book without trades -> p_fill 0 both conventions), ADVERSARIAL
      (quote placed the instant the touch moves away -> no fill, no false
      positive; AND a book whose visible size shrinks with zero trades ->
      FIFO says no fill, pro-rata may fill -- the two bounds must diverge
      exactly there).
  (c) ``positive_control`` -- the PRD 3.3.8 pre-run reproduces its known
      fixture outcomes through the real ``simulate_quote`` entry point.
  (d) ``replay`` on a synthetic harvest tree (style of
      ``test_c22_extract.py``): determinism, store isolation (tilt_1min/
      spread_1min byte-identical after a WP-10(B) run, mirroring the
      WP-4 test), manifest-DONE gating, refuse-``data/harvest`` writes.
  (e) ``report`` -- fill-rate curve/adv_sel grouping, DEC-53 artefact
      round-trip (CSV + bootstrap fingerprint, SHA-256), loud "KEIN
      VERDIKT" when artefacts are withheld.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from bybit_edge.research.wp10_fillshadow import queue_model as qm
from bybit_edge.research.wp10_fillshadow import replay as rp
from bybit_edge.research.wp10_fillshadow import report as rpt
from bybit_edge.research.wp10_fillshadow.positive_control import (
    PositiveControlError,
    assert_positive_control,
    build_fixture,
    run_positive_control,
)

EPOCH = date(1970, 1, 1)
T0 = 1_700_000_000_000  # arbitrary fixed epoch ms


# ----------------------------------------------------------------------------
# (a) queue_model mechanics
# ----------------------------------------------------------------------------

def test_side_and_price_validation():
    with pytest.raises(qm.QueueModelError):
        qm.simulate_quote([(T0, 5.0, 100.0)], [], [], t0_ms=T0, side="bogus",
                          price=100.0, size=1.0)
    with pytest.raises(qm.QueueModelError):
        qm.simulate_quote([(T0, 5.0, 100.0)], [], [], t0_ms=T0, side="buy",
                          price=99.0, size=1.0)   # touch != quoted price at t0
    with pytest.raises(qm.QueueModelError):
        qm.simulate_quote([(T0, 5.0, 100.0)], [], [], t0_ms=T0, side="buy",
                          price=100.0, size=0.0)  # size must be > 0


def test_nearest_mid_at_or_after():
    mids = [(T0, 100.0), (T0 + 1000, 101.0), (T0 + 5000, 99.0)]
    assert qm.nearest_mid_at_or_after(mids, T0 + 500) == 101.0
    assert qm.nearest_mid_at_or_after(mids, T0 + 5000) == 99.0
    assert qm.nearest_mid_at_or_after(mids, T0 + 6000) is None


def test_adverse_selection_sign_both_sides():
    # buy fill, mid drops afterward -> adverse (positive adv_sel)
    book = [(T0, 5.0, 100.0), (T0 + 1000, 0.0, 100.0)]
    trades = [(T0 + 1000, "sell", 100.0, 6.0)]
    mids = [(T0, 100.0), (T0 + 61_000, 98.0)]
    out = qm.simulate_quote(book, trades, mids, t0_ms=T0, side="buy", price=100.0,
                            size=1.0, horizon_s=10.0)
    assert out["fifo"]["filled"]
    assert out["fifo"]["adv_sel_bp"] == pytest.approx(200.0)  # (100-98)/100*1e4

    # sell fill, mid rises afterward -> adverse (positive adv_sel)
    book2 = [(T0, 5.0, 100.0), (T0 + 1000, 0.0, 100.0)]
    trades2 = [(T0 + 1000, "buy", 100.0, 6.0)]
    mids2 = [(T0, 100.0), (T0 + 61_000, 102.0)]
    out2 = qm.simulate_quote(book2, trades2, mids2, t0_ms=T0, side="sell", price=100.0,
                             size=1.0, horizon_s=10.0)
    assert out2["fifo"]["filled"]
    assert out2["fifo"]["adv_sel_bp"] == pytest.approx(200.0)


def test_horizon_boundary_excludes_late_trade():
    book = [(T0, 5.0, 100.0), (T0 + 20_000, 5.0, 100.0)]
    trades = [(T0 + 15_000, "sell", 100.0, 6.0)]  # outside 10s horizon
    out = qm.simulate_quote(book, trades, [], t0_ms=T0, side="buy", price=100.0,
                            size=1.0, horizon_s=10.0)
    assert not out["fifo"]["filled"] and not out["prorata"]["filled"]


# ----------------------------------------------------------------------------
# (b) THE DEC-39 TRIO
# ----------------------------------------------------------------------------

def test_dec39_positive_known_queue_and_trades_yield_known_fills():
    """Known queue (pos0=10) + known trades exactly explain every
    decrease -> both conventions must reproduce the SAME exact fill time,
    and pro-rata's bound must never be BEHIND (later than) FIFO's."""
    book = [
        (T0, 10.0, 100.0),
        (T0 + 4_000, 6.0, 100.0),
        (T0 + 9_000, 0.0, 100.0),
        (T0 + 9_500, 5.0, 100.0),
        (T0 + 15_000, 2.0, 100.0),
    ]
    trades = [
        (T0 + 4_000, "sell", 100.0, 4.0),
        (T0 + 9_000, "sell", 100.0, 6.0),
        (T0 + 15_000, "sell", 100.0, 3.0),
    ]
    out = qm.simulate_quote(book, trades, [(T0, 100.0)], t0_ms=T0, side="buy",
                            price=100.0, size=3.0, horizon_s=20.0)
    assert out["fifo"]["filled"] and out["fifo"]["fill_time_ms"] == T0 + 15_000
    assert out["prorata"]["filled"] and out["prorata"]["fill_time_ms"] == T0 + 15_000
    # pro-rata bound is never LATER than FIFO (upper bound on fill probability)
    assert out["prorata"]["fill_time_ms"] <= out["fifo"]["fill_time_ms"]


def test_dec39_null_book_without_trades_gives_zero_fill_probability():
    book = [(T0, 8.0, 200.0), (T0 + 10_000, 8.0, 200.0), (T0 + 60_000, 8.0, 200.0)]
    out = qm.simulate_quote(book, [], [], t0_ms=T0, side="sell", price=200.0,
                            size=5.0, horizon_s=60.0)
    assert out["fifo"]["filled"] is False
    assert out["prorata"]["filled"] is False


def test_dec39_adversarial_touch_moves_away_instantly_no_false_positive():
    """Quote placed the exact instant the touch subsequently walks away
    (no trades at all): neither bound may report a fill."""
    book = [(T0, 10.0, 100.0), (T0 + 200, 0.0, 99.9)]
    out = qm.simulate_quote(book, [], [], t0_ms=T0, side="buy", price=100.0,
                            size=2.0, horizon_s=60.0)
    assert out["touch_moved_away"] is True
    assert out["fifo"]["filled"] is False
    assert out["prorata"]["filled"] is False


def test_dec39_adversarial_zero_trade_shrinkage_diverges_fifo_vs_prorata():
    """Visible size shrinks to zero, refills, shrinks to zero again -- NO
    trades anywhere. FIFO (trade-only) must show NO fill; pro-rata (which
    treats unexplained decreases as possible cancellations/hidden fills
    ahead of us) MAY fill. This is the exact scenario where the two
    bounds are required to diverge."""
    book = [
        (T0, 2.0, 100.0),
        (T0 + 1_000, 0.0, 100.0),   # unexplained decrease of 2
        (T0 + 2_000, 1.0, 100.0),   # refill (increase, never counted as reduction)
        (T0 + 3_000, 0.0, 100.0),   # unexplained decrease of 1 -> cum=3 >= pos0+q=3
    ]
    out = qm.simulate_quote(book, [], [], t0_ms=T0, side="buy", price=100.0,
                            size=1.0, horizon_s=60.0)
    assert out["fifo"]["filled"] is False, "FIFO must ignore cancellation-only shrinkage"
    assert out["prorata"]["filled"] is True, "pro-rata must fill from unexplained shrinkage"
    assert out["prorata"]["fill_time_ms"] == T0 + 3_000


# ----------------------------------------------------------------------------
# (c) positive_control (PRD 3.3.8)
# ----------------------------------------------------------------------------

def test_positive_control_fixture_passes_through_real_simulate_quote():
    result = run_positive_control()
    assert result["ok"] is True
    assert all(c["passed"] for c in result["checks"])
    assert_positive_control()  # must not raise


def test_positive_control_detects_a_broken_model(monkeypatch):
    """If the real fill machinery breaks, the positive control must say so
    loudly (never silently pass)."""
    import bybit_edge.research.wp10_fillshadow.positive_control as pc_mod

    def _always_no_fill(*args, **kwargs):
        return {"t0_ms": kwargs["t0_ms"], "side": kwargs["side"], "price": kwargs["price"],
                "size": kwargs["size"], "position0": 0.0, "horizon_s": kwargs.get("horizon_s"),
                "touch_moved_away": False,
                "fifo": {"filled": False, "fill_time_ms": None, "fill_price": None,
                        "latency_s": None, "adv_sel_bp": None},
                "prorata": {"filled": False, "fill_time_ms": None, "fill_price": None,
                           "latency_s": None, "adv_sel_bp": None}}

    monkeypatch.setattr(pc_mod.qm, "simulate_quote", _always_no_fill)
    result = pc_mod.run_positive_control()
    assert result["ok"] is False
    with pytest.raises(PositiveControlError):
        pc_mod.assert_positive_control()


def test_positive_control_fixture_is_deterministic():
    a, b = build_fixture(), build_fixture()
    assert a == b


# ----------------------------------------------------------------------------
# (d) replay -- synthetic harvest-tree fixture (style of test_c22_extract.py)
# ----------------------------------------------------------------------------

def _day_ms(day: str) -> int:
    return (date.fromisoformat(day) - EPOCH).days * 86_400_000


def _write_ob_day(base: Path, symbol: str, day: str, records: list[dict]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "bybit" / "orderbook" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    ts = [r["ts"] for r in records]
    payloads = [json.dumps(r) for r in records]
    n = len(records)
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 10**6 for t in ts], pa.int64()),
        "ts_exchange_ms": pa.array(ts, pa.int64()),
        "topic": pa.array(["orderbook"] * n), "stream": pa.array(["orderbook"] * n),
        "symbol": pa.array([symbol] * n), "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _snap(ts: int, u: int, bid: float, ask: float, bsz: float = 10.0, asz: float = 10.0) -> dict:
    return {"topic": "orderbook.500.TST", "type": "snapshot", "ts": ts,
            "data": {"s": "TST", "b": [[f"{bid}", f"{bsz}"]],
                     "a": [[f"{ask}", f"{asz}"]], "u": u}}


def _delta(ts: int, u: int, b: list, a: list) -> dict:
    return {"topic": "orderbook.500.TST", "type": "delta", "ts": ts,
            "data": {"s": "TST", "b": b, "a": a, "u": u}}


def _write_trade_day(base: Path, symbol: str, day: str, trades: list[dict]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={day}"
    d.mkdir(parents=True, exist_ok=True)
    n = len(trades)
    payloads = [json.dumps(t) for t in trades]
    ts = [t["timestamp"] for t in trades]
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 10**6 for t in ts], pa.int64()),
        "ts_exchange_ms": pa.array(ts, pa.int64()),
        "topic": pa.array(["publicTrade"] * n), "stream": pa.array(["publicTrade"] * n),
        "symbol": pa.array([symbol] * n), "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _trade(ts: int, side: str, price: float, size: float) -> dict:
    return {"timestamp": ts, "symbol": "TSTUSDT", "side": side,
            "size": str(size), "price": str(price)}


def _write_manifest(base: Path, entries: list[tuple[str, str, str, str, str]]) -> None:
    p = base / "state" / "harvest_manifest.backup.sqlite"
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE partitions (exchange TEXT, stream TEXT, symbol TEXT, "
               "date TEXT, status TEXT)")
    con.executemany("INSERT INTO partitions VALUES (?,?,?,?,?)", entries)
    con.commit()
    con.close()


def _build_day_fixture(base: Path, day: str, *, done: bool = True) -> None:
    """A day with an active book across the first two minutes and one
    matching trade, so at least a few quotes have full forward data."""
    ms = _day_ms(day)
    _write_ob_day(base, "TSTUSDT", day, [
        _snap(ms + 500, 1, 99.9, 100.1, bsz=10.0, asz=10.0),
        _delta(ms + 90_000, 2, [["99.9", "4.0"]], []),   # bid depleted (trade)
        _delta(ms + 200_000, 3, [["99.9", "4.0"]], [["100.1", "10.0"]]),
    ])
    _write_trade_day(base, "TSTUSDT", day, [
        _trade(ms + 90_000, "Sell", 99.9, 6.0),
    ])
    if done:
        _write_manifest(base, [
            ("bybit", "orderbook", "TSTUSDT", day, "DONE"),
            ("bybit", "publicTrade", "TSTUSDT", day, "DONE"),
        ])


def test_replay_end_to_end_and_determinism(tmp_path):
    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1)

    out1 = tmp_path / "o1"
    s1 = rp.run_window(base, out1, "TSTUSDT", d1, d1, horizon_s=60.0, adv_sel_horizon_s=60.0)
    assert s1["ok"] == 1 and s1["discarded"] == 0 and s1["not_manifest_done"] == 0
    assert s1["n_quotes_total"] > 0

    out2 = tmp_path / "o2"
    rp.run_window(base, out2, "TSTUSDT", d1, d1, horizon_s=60.0, adv_sel_horizon_s=60.0)
    fp1 = rp.fillshadow_fingerprint(out1, "bybit", "TSTUSDT", d1, d1)
    fp2 = rp.fillshadow_fingerprint(out2, "bybit", "TSTUSDT", d1, d1)
    assert fp1["sha256_values"] == fp2["sha256_values"]
    assert fp1["n_ok_days"] == 1

    # at least one quote near the fixture's active window has full
    # forward data and reflects the known trade-driven depletion
    daily = rp.load_daily_fillshadow(out1, "bybit", "TSTUSDT", d1, d1)
    assert len(daily) == 1
    quotes = daily[0]["quotes"]
    assert len(quotes["minute_idx"]) > 0
    assert any(not v for v in quotes["insufficient_forward_data"])


def test_replay_store_isolation_from_frozen_tilt_and_spread(tmp_path):
    """Mirrors the WP-4 store-isolation test: a WP-10(B) run must leave
    the WP-2 tilt_1min and WP-4 spread_1min stores byte-identical."""
    from bybit_edge.research.c22_l2tilt.extract import (
        extract_spread_window,
        extract_window,
        tilt_fingerprint,
    )
    from bybit_edge.research.c22_l2tilt.extract import (
        load_daily_spread as _load_spread,
    )

    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1)

    out = tmp_path / "o"
    extract_window(base, out, "TSTUSDT", d1, d1)
    extract_spread_window(base, out, "TSTUSDT", d1, d1)
    fp_tilt_before = tilt_fingerprint(out, "bybit", "TSTUSDT", d1, d1)
    spread_before = _load_spread(out, "bybit", "TSTUSDT", d1, d1)

    rp.run_window(base, out, "TSTUSDT", d1, d1)

    fp_tilt_after = tilt_fingerprint(out, "bybit", "TSTUSDT", d1, d1)
    spread_after = _load_spread(out, "bybit", "TSTUSDT", d1, d1)
    assert fp_tilt_before["sha256_values"] == fp_tilt_after["sha256_values"]
    assert spread_before["spread_median_bp"].tolist() == spread_after["spread_median_bp"].tolist()
    assert {p.name for p in out.iterdir()} == {"tilt_1min", "spread_1min", "fillshadow_1min"}


def test_replay_manifest_done_gating_excludes_undone_day(tmp_path):
    base = tmp_path / "h"
    d1, d2 = "2026-06-22", "2026-06-23"
    _build_day_fixture(base, d1, done=False)
    _build_day_fixture(base, d2, done=False)
    _write_manifest(base, [
        ("bybit", "orderbook", "TSTUSDT", d1, "DONE"),
        ("bybit", "publicTrade", "TSTUSDT", d1, "DONE"),
        ("bybit", "orderbook", "TSTUSDT", d2, "PARTIAL"),   # day 2 not DONE
        ("bybit", "publicTrade", "TSTUSDT", d2, "DONE"),
    ])
    out = tmp_path / "o"
    s = rp.run_window(base, out, "TSTUSDT", d1, d2, require_manifest_done=True)
    assert s["ok"] == 1 and s["not_manifest_done"] == 1

    meta2 = json.loads((out / "fillshadow_1min" / "exchange=bybit" / "symbol=TSTUSDT"
                        / f"date={d2}" / "manifest.json").read_text())
    assert meta2["status"] == "not_manifest_done"
    assert meta2["n_quotes"] == 0

    # without the gate, day 2's replay itself is fine and quotes get placed
    out_ungated = tmp_path / "o_ungated"
    s_ungated = rp.run_window(base, out_ungated, "TSTUSDT", d1, d2, require_manifest_done=False)
    assert s_ungated["ok"] == 2 and s_ungated["not_manifest_done"] == 0


def test_replay_missing_manifest_raises(tmp_path):
    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1, done=False)   # no manifest written at all
    out = tmp_path / "o"
    from bybit_edge.research.bar_cache import BarCacheError
    with pytest.raises(BarCacheError):
        rp.run_window(base, out, "TSTUSDT", d1, d1, require_manifest_done=True)


def test_replay_refuses_data_harvest_output(tmp_path):
    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1)
    bad_out = base / "data" / "harvest" / "fillshadow_out"
    with pytest.raises(rp.ReplayError):
        rp.run_window(base, bad_out, "TSTUSDT", d1, d1)


def test_probe_reports_presence_and_manifest_done_counts(tmp_path):
    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1)
    p = rp.probe(base, "TSTUSDT", d1, d1)
    assert p["orderbook_days_present"] == 1
    assert p["trade_days_present"] == 1
    assert p["days_eligible_for_placement"] == 1


def test_probe_reports_manifest_error_without_raising(tmp_path):
    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1, done=False)  # no manifest file at all
    p = rp.probe(base, "TSTUSDT", d1, d1)
    assert "manifest_error" in p


# ----------------------------------------------------------------------------
# (e) report -- artefact round-trip + DEC-53 duty
# ----------------------------------------------------------------------------

def _big_fixture_rows() -> list[dict]:
    """Enough synthetic quote rows, across two days, to exercise grouping
    and the day-cluster bootstrap without touching real data."""
    rows = []
    for day, hour, filled_frac, adv in (("2026-06-22", 9, True, 1.0),
                                        ("2026-06-22", 14, False, None),
                                        ("2026-06-23", 9, True, 2.0),
                                        ("2026-06-23", 20, True, 0.5)):
        for i in range(5):
            rows.append({
                "symbol": "TSTUSDT", "day": day, "hour": hour, "side": "buy",
                "regime": "stress" if day == "2026-06-22" else "quiet",
                "fifo_filled": filled_frac, "fifo_latency_s": 5.0 if filled_frac else None,
                "fifo_adv_sel_bp": adv if filled_frac else None,
                "prorata_filled": filled_frac, "prorata_latency_s": 4.0 if filled_frac else None,
                "prorata_adv_sel_bp": adv if filled_frac else None,
                "insufficient_forward_data": False,
            })
    return rows


def test_hour_of_day_wraps_epoch_minutes():
    assert rpt.hour_of_day(0) == 0
    assert rpt.hour_of_day(59) == 0
    assert rpt.hour_of_day(60) == 1
    assert rpt.hour_of_day(1440 * 3 + 125) == 2


def test_p_fill_curve_and_adv_sel_stats_and_label():
    rows = _big_fixture_rows()
    curve = rpt.p_fill_curve(rows, convention="fifo", group_by=("symbol", "side"))
    assert len(curve) == 1
    assert curve[0]["n"] == 20
    assert curve[0]["p_fill_60s"] == pytest.approx(15 / 20)

    stats = rpt.adv_sel_stats(rows, convention="fifo", group_by=("symbol", "side"))
    assert stats[0]["n_filled"] == 15
    assert stats[0]["label"] == rpt.maker_vantage_label(stats[0]["mean_bp"])


def test_maker_vantage_label_threshold():
    assert rpt.maker_vantage_label(1.75) == "Maker-Vorteil traegt"
    assert rpt.maker_vantage_label(1.749999) == "Maker-Vorteil traegt"
    assert rpt.maker_vantage_label(1.750001) == "Maker-Vorteil traegt nicht"


def test_insufficient_forward_data_excluded_from_curves():
    rows = [{"symbol": "X", "day": "2026-06-22", "hour": 0, "side": "buy", "regime": None,
            "fifo_filled": True, "fifo_latency_s": 1.0, "fifo_adv_sel_bp": 0.5,
            "prorata_filled": True, "prorata_latency_s": 1.0, "prorata_adv_sel_bp": 0.5,
            "insufficient_forward_data": True}]
    curve = rpt.p_fill_curve(rows, convention="fifo")
    assert curve == []


def test_cluster_bootstrap_ci_is_seed_reproducible():
    rows = _big_fixture_rows()
    a = rpt.cluster_bootstrap_ci(rows, metric="p_fill", seed=7, n_bootstrap=200)
    b = rpt.cluster_bootstrap_ci(rows, metric="p_fill", seed=7, n_bootstrap=200)
    assert a == b
    assert a[0]["n_days"] == 2


def test_report_artifact_round_trip_and_dec53(tmp_path):
    rows = _big_fixture_rows()
    result = rpt.build_report(rows=rows, out_dir=tmp_path / "report", seed=11, n_bootstrap=50)
    summary = json.loads(Path(result["summary_path"]).read_text())
    assert summary["artifacts"]["quote_outcomes"]["n_rows"] == len(rows)

    csv_path = Path(summary["artifacts"]["quote_outcomes"]["path"])
    import hashlib
    assert hashlib.sha256(csv_path.read_bytes()).hexdigest() == \
        summary["artifacts"]["quote_outcomes"]["sha256"]

    fp_path = Path(summary["artifacts"]["bootstrap_fingerprint"]["path"])
    fp = json.loads(fp_path.read_text())
    assert fp["generator"] == "numpy.random.default_rng"
    assert len(fp["entries"]) > 0
    assert Path(result["markdown_path"]).is_file()


def test_report_kein_verdikt_when_artifacts_withheld():
    with pytest.raises(rpt.ReportError, match="KEIN VERDIKT"):
        rpt.check_dec53({"quote_outcomes": None, "bootstrap_fingerprint": {"path": "x"}})
    with pytest.raises(rpt.ReportError, match="KEIN VERDIKT"):
        rpt.check_dec53({})


def test_report_refuses_data_harvest_output(tmp_path):
    rows = _big_fixture_rows()
    bad_out = tmp_path / "data" / "harvest" / "report_out"
    with pytest.raises(ValueError, match="data/harvest"):
        rpt.write_quote_outcomes_csv(rows, bad_out)
    with pytest.raises(ValueError, match="data/harvest"):
        rpt.write_bootstrap_fingerprint([], bad_out)


def test_load_quote_rows_tags_stress_regime(tmp_path):
    base = tmp_path / "h"
    d1 = "2026-06-22"
    _build_day_fixture(base, d1)
    out = tmp_path / "o"
    rp.run_window(base, out, "TSTUSDT", d1, d1)
    rows = rpt.load_quote_rows(out, "bybit", ["TSTUSDT"], d1, d1, stress_days={d1})
    assert rows and all(r["regime"] == "stress" for r in rows)
    rows_quiet = rpt.load_quote_rows(out, "bybit", ["TSTUSDT"], d1, d1, stress_days=set())
    assert rows_quiet and all(r["regime"] == "quiet" for r in rows_quiet)
    rows_none = rpt.load_quote_rows(out, "bybit", ["TSTUSDT"], d1, d1)
    assert rows_none and all(r["regime"] is None for r in rows_none)
