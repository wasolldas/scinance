"""Unit tests fuer WP-6 (Options-Quote-Breite aus dem Harvest-Baum).

Deckt ab:
  (a) unwrap_payload: alle drei Wrapper-Formen + lautes None fuer Muell,
  (b) frame_record: Optionen erkannt, Perps verworfen, DTE gegen das
      FRAME-Datum verankert, bid1Iv=0 ist fehlende Quote,
  (c) minute_stats auf konstruierten Minuten,
  (d) DEC-39-Pflicht Ende-zu-Ende auf einem synthetischen Harvest-Baum:
      ein Ruhe-Tag (enge Beine) und ein Stress-Tag (weite Beine) muessen
      im Summary unterscheidbar herauskommen; Perp-Frames im selben Strom
      duerfen nichts verfaelschen,
  (e) die Probe erkennt einen Baum ohne Optionen und einen ohne bid/ask.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from bybit_edge.research.wp6_optstress.extract import (
    OPTION_SYMBOL_RE,
    frame_record,
    minute_stats,
    unwrap_payload,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wp6_optstress_census.py"
DAY = date(2026, 8, 19)


def _tick(sym, biv, aiv, delta, under=77_900.0, bid=600.0, ask=605.0):
    return {"symbol": sym, "bid1Price": str(bid), "ask1Price": str(ask),
            "bid1Iv": str(biv), "ask1Iv": str(aiv), "delta": str(delta),
            "markPrice": "602", "markIv": str(0.5 * (biv + aiv)),
            "underlyingPrice": str(under), "openInterest": "10"}


# ---------------------------------------------------------------- (a) wrapper

def test_unwrap_all_three_wrapper_forms():
    t = _tick("BTC-4SEP26-73000-P", 0.40, 0.42, -0.2)
    bare = json.dumps(t)
    topic = json.dumps({"topic": "tickers.BTC-4SEP26-73000-P", "type":
                        "snapshot", "ts": 1, "data": t})
    lst = json.dumps({"data": [t]})
    for pj in (bare, topic, lst):
        got = unwrap_payload(pj)
        assert got is not None and got["bid1Iv"] == "0.4"


def test_unwrap_rejects_garbage_loudly():
    assert unwrap_payload("not json") is None
    assert unwrap_payload(json.dumps([1, 2])) is None
    assert unwrap_payload(json.dumps({"data": [1, 2]})) is None
    assert unwrap_payload(json.dumps({"data": {"noSymbol": 1}})) is None


def test_unwrap_symbol_fallback_from_envelope():
    pj = json.dumps({"symbol": "BTC-4SEP26-73000-P",
                     "data": {"bid1Iv": "0.4"}})
    assert unwrap_payload(pj)["symbol"] == "BTC-4SEP26-73000-P"


# ---------------------------------------------------------- (b) frame_record

def test_frame_record_option_vs_perp():
    assert frame_record("BTCUSDT", _tick("BTCUSDT", 0.4, 0.5, 0.2), DAY) is None
    r = frame_record("BTC-4SEP26-73000-P",
                     _tick("BTC-4SEP26-73000-P", 0.40, 0.42, -0.2), DAY)
    assert r["dte"] == 16 and r["iv_width_pts"] == pytest.approx(2.0)
    # Settlement-Suffix-Variante (REST-Form) ebenfalls akzeptiert
    assert OPTION_SYMBOL_RE.match("ETH-25AUG26-2250-P-USDT")


def test_frame_record_dte_is_anchored_to_frame_date():
    r1 = frame_record("BTC-4SEP26-73000-P",
                      _tick("BTC-4SEP26-73000-P", .4, .42, -.2), date(2026, 8, 24))
    r2 = frame_record("BTC-4SEP26-73000-P",
                      _tick("BTC-4SEP26-73000-P", .4, .42, -.2), date(2026, 8, 19))
    assert (r1["dte"], r2["dte"]) == (11, 16)


def test_zero_bid_iv_is_missing_quote():
    r = frame_record("BTC-4SEP26-73000-P",
                     _tick("BTC-4SEP26-73000-P", 0.0, 0.42, -0.2), DAY)
    assert r["two_sided"] is True and r["quoted_iv"] is False


# ---------------------------------------------------------- (c) minute_stats

def test_minute_stats_legband_and_atm():
    recs = [frame_record(f"BTC-4SEP26-{k}-P",
                         _tick(f"BTC-4SEP26-{k}-P", 0.40, 0.40 + w, d),
                         date(2026, 8, 26))
            for k, w, d in ((73000, 0.002, -0.18), (74000, 0.004, -0.25),
                            (75000, 0.006, -0.32), (78000, 0.010, -0.50))]
    st = minute_stats(recs)
    assert st["n_legs"] == 2 and st["leg_w_p50"] == pytest.approx(0.3)
    assert st["atm_mark_iv"] is not None
    assert st["n_unquoted_legband"] == 0


# --------------------------------------------------- (d)/(e) end-to-end tree

def _write_day(base: Path, day: str, frames: list[tuple[str, int, str]]):
    """frames: (symbol, ts_ms, payload_json) -- ein Parquet je Symbol/Tag."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    by_sym: dict[str, list[tuple[int, str]]] = {}
    for sym, ts, pj in frames:
        by_sym.setdefault(sym, []).append((ts, pj))
    for sym, rows in by_sym.items():
        d = base / "raw" / "bybit" / "tickers" / f"symbol={sym}" / f"date={day}"
        d.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table({
            "ts_local_ns": pa.array([t * 1_000_000 for t, _ in rows], pa.int64()),
            "ts_exchange_ms": pa.array([t for t, _ in rows], pa.int64()),
            "topic": pa.array([f"tickers.{sym}"] * len(rows)),
            "stream": pa.array(["tickers"] * len(rows)),
            "symbol": pa.array([sym] * len(rows)),
            "payload_json": pa.array([p for _, p in rows]),
        }), d / "part-0.parquet")


def _day_frames(day_iso: str, width: float) -> list[tuple[str, int, str]]:
    ms0 = (date.fromisoformat(day_iso) - date(1970, 1, 1)).days * 86_400_000
    out = []
    for m in range(0, 3):          # drei Minuten reichen
        ts = ms0 + m * 60_000 + 30_000
        for k, d in ((84000, 0.20), (86000, 0.25)):
            sym = f"BTC-4SEP26-{k}-C"
            out.append((sym, ts, json.dumps(
                {"topic": f"tickers.{sym}", "data":
                 _tick(sym, 0.40, 0.40 + width / 100.0, d)})))
        # Perp-Frame im selben Strom -- darf nichts verfaelschen
        out.append(("BTCUSDT", ts, json.dumps(_tick("BTCUSDT", .4, .5, .2))))
    return out


@pytest.mark.filterwarnings("ignore")
def test_e2e_quiet_vs_stress_day(tmp_path):
    pytest.importorskip("duckdb")
    base = tmp_path / "harvest"
    _write_day(base, "2026-08-18", _day_frames("2026-08-18", 0.14))  # Ruhe
    _write_day(base, "2026-08-19", _day_frames("2026-08-19", 4.00))  # Stress
    out = tmp_path / "out"
    rc = subprocess.run(
        [sys.executable, str(SCRIPT), "--base", str(base),
         "--dates", "2026-08-18..2026-08-19", "--out", str(out),
         "--horizon-dte", "7,21"],
        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stderr + rc.stdout
    summary = json.loads((out / "wp6_summary.json").read_text())
    quiet = summary["days"]["2026-08-18"]
    stress = summary["days"]["2026-08-19"]
    assert quiet["BTC_leg_w_p50_of_minutes"] == pytest.approx(0.14, abs=1e-6)
    assert stress["BTC_leg_w_p50_of_minutes"] == pytest.approx(4.0, abs=1e-6)
    assert summary["unparseable_frames"] == 0


@pytest.mark.filterwarnings("ignore")
def test_probe_flags_missing_options_and_missing_bidask(tmp_path):
    pytest.importorskip("duckdb")
    # Baum 1: nur Perps -> Probe muss rc!=0 geben
    b1 = tmp_path / "h1"
    ms = (date(2026, 8, 19) - date(1970, 1, 1)).days * 86_400_000
    _write_day(b1, "2026-08-19",
               [("BTCUSDT", ms, json.dumps(_tick("BTCUSDT", .4, .5, .2)))])
    r1 = subprocess.run([sys.executable, str(SCRIPT), "--base", str(b1),
                         "--dates", "2026-08-19", "--probe"],
                        capture_output=True, text=True)
    assert r1.returncode == 1 and "KEINE Optionen" in r1.stdout
    # Baum 2: Option ohne bid/ask (das alte Scinance-Schema) -> rc!=0
    b2 = tmp_path / "h2"
    naked = {"symbol": "BTC-4SEP26-84000-C", "markIv": "0.45",
             "delta": "0.2"}
    _write_day(b2, "2026-08-19",
               [("BTC-4SEP26-84000-C", ms, json.dumps({"data": naked}))])
    r2 = subprocess.run([sys.executable, str(SCRIPT), "--base", str(b2),
                         "--dates", "2026-08-19", "--probe"],
                        capture_output=True, text=True)
    assert r2.returncode == 1 and "PFLICHTFELDER FEHLEN" in r2.stdout
    # Baum 3 (Gegenprobe): vollstaendige Option -> rc==0
    b3 = tmp_path / "h3"
    _write_day(b3, "2026-08-19", _day_frames("2026-08-19", 0.14))
    r3 = subprocess.run([sys.executable, str(SCRIPT), "--base", str(b3),
                         "--dates", "2026-08-19", "--probe"],
                        capture_output=True, text=True)
    assert r3.returncode == 0, r3.stdout
    assert "'ask_iv': 'ask1Iv'" in r3.stdout


# ------------------------------------------------- WS-Dialekt (DEC-46-Probe)

def _ws_tick(sym, biv, aiv, delta, under=77_900.0):
    """Feldnamen exakt wie im Probe-Lauf 2026-08-19 am Bestand gesehen."""
    return {"symbol": sym, "bidPrice": "600", "askPrice": "605",
            "bidSize": "2", "askSize": "3",
            "bidIv": str(biv), "askIv": str(aiv), "delta": str(delta),
            "markPrice": "602", "markPriceIv": str(0.5 * (biv + aiv)),
            "underlyingPrice": str(under), "indexPrice": str(under),
            "lastPrice": "601", "gamma": "0", "vega": "40", "theta": "-1",
            "openInterest": "10", "totalVolume": "1", "turnover24h": "0",
            "highPrice24h": "0", "lowPrice24h": "0", "change24h": "0",
            "predictedDeliveryPrice": "0", "totalTurnover": "0",
            "volume24h": "0"}


def test_ws_dialect_fields_are_read():
    r = frame_record("BTC-20AUG26-65000-C-USDT",
                     _ws_tick("BTC-20AUG26-65000-C-USDT", 0.40, 0.42, 0.22),
                     date(2026, 8, 19))
    assert r is not None and r["quoted_iv"] is True
    assert r["iv_width_pts"] == pytest.approx(2.0)
    assert r["mark_iv"] == pytest.approx(0.41)
    assert r["dte"] == 1


def test_rest_dialect_takes_precedence_when_both_present():
    t = _ws_tick("BTC-4SEP26-73000-P", 0.10, 0.99, -0.2)
    t["bid1Iv"], t["ask1Iv"] = "0.40", "0.42"   # REST-Namen zuerst im Alias
    r = frame_record("BTC-4SEP26-73000-P", t, DAY)
    assert r["iv_width_pts"] == pytest.approx(2.0)


@pytest.mark.filterwarnings("ignore")
def test_probe_accepts_ws_dialect(tmp_path):
    pytest.importorskip("duckdb")
    b = tmp_path / "h"
    ms = (date(2026, 8, 19) - date(1970, 1, 1)).days * 86_400_000
    sym = "BTC-20AUG26-65000-C-USDT"
    _write_day(b, "2026-08-19",
               [(sym, ms, json.dumps({"topic": f"tickers.{sym}",
                                      "data": _ws_tick(sym, .4, .42, .22)}))])
    r = subprocess.run([sys.executable, str(SCRIPT), "--base", str(b),
                        "--dates", "2026-08-19", "--probe"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert "bidIv" in r.stdout
