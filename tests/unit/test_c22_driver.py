"""Unit tests for the H-22 gate driver (c22_l2tilt.driver, KAPITALFREI).

  (a) IC + block-bootstrap null behaviour (signal vs noise),
  (b) end-to-end on synthetic stores: a tilt that genuinely predicts the
      next-day return passes both windows; a null tilt does not,
  (c) coverage-floor enforcement -> SKIP_COVERAGE, no verdict flags,
  (d) fingerprint discipline for BOTH stores,
  (e) day alignment: tilt day d pairs with return d -> d+1 (spill day).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c22_l2tilt.driver import (
    block_bootstrap_p,
    run,
    spearman_ic,
)

EPOCH = date(1970, 1, 1)


def _write_tilt_day(out: Path, symbol: str, day: str, tilt_value: float,
                    n_samples: int = 1400) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq
    import hashlib

    part = (out / "tilt_1min" / "exchange=bybit" / f"symbol={symbol}"
            / f"date={day}")
    part.mkdir(parents=True, exist_ok=True)
    m0 = (date.fromisoformat(day) - EPOCH).days * 1440
    arrays = {
        "minute_idx": np.arange(m0, m0 + n_samples, dtype=np.int64),
        "tilt": np.full(n_samples, tilt_value, dtype=np.float64),
        "mid": np.full(n_samples, 100.0, dtype=np.float64),
    }
    h = hashlib.sha256()
    for col in ("minute_idx", "tilt", "mid"):
        h.update(col.encode())
        h.update(arrays[col].tobytes())
    pq.write_table(pa.table({k: pa.array(v) for k, v in arrays.items()}),
                   part / "tilt.parquet")
    (part / "manifest.json").write_text(json.dumps({
        "schema_version": 1, "status": "ok", "n_samples": n_samples,
        "coverage": n_samples / 1440.0, "sha256_values": h.hexdigest()}),
        encoding="utf-8")


def _write_bar_day(base: Path, symbol: str, day: str, close: float) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    from bybit_edge.research.bar_cache import build_day
    import duckdb
    ms = (date.fromisoformat(day) - EPOCH).days * 86_400_000
    d = (base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}"
         / f"date={day}")
    d.mkdir(parents=True, exist_ok=True)
    ts = [ms + i * 60_000 for i in range(400)]
    payloads = [json.dumps({"side": "Buy", "price": f"{close:.8f}",
                            "size": "1"}) for _ in ts]
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 10**6 for t in ts], pa.int64()),
        "ts_exchange_ms": pa.array(ts, pa.int64()),
        "topic": pa.array(["publicTrade"] * 400),
        "stream": pa.array(["publicTrade"] * 400),
        "symbol": pa.array([symbol] * 400),
        "payload_json": pa.array(payloads)}), d / "part-0.parquet")
    con = duckdb.connect()
    try:
        build_day(con, base, base.parent / "cache", "bybit", "publicTrade",
                  symbol, day)
    finally:
        con.close()


def _days(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def _build_stores(tmp_path: Path, symbol: str, days: list[str],
                  predictive: bool, seed: int) -> tuple[Path, Path]:
    """Tilt store + bar cache; if predictive, tilt_d drives r_{d+1}."""
    rng = np.random.default_rng(seed)
    tilts = np.tanh(rng.standard_normal(len(days)))
    log_close = np.log(100.0)
    closes = []
    for i in range(len(days)):
        drift = 0.02 * tilts[i - 1] if (predictive and i > 0) else 0.0
        log_close += drift + 0.005 * rng.standard_normal()
        closes.append(np.exp(log_close))
    tilt_dir, base = tmp_path / "tilt", tmp_path / "h"
    for day, tv, cl in zip(days, tilts, closes):
        _write_tilt_day(tilt_dir, symbol, day, float(tv))
        _write_bar_day(base, symbol, day, float(cl))
    return tilt_dir, base.parent / "cache"


def test_spearman_and_bootstrap_signal_vs_noise():
    rng = np.random.default_rng(4)
    n = 300
    x = rng.standard_normal(n)
    y_sig = 0.5 * x + 0.5 * rng.standard_normal(n)
    ic = spearman_ic(x, y_sig)
    assert ic > 0.3
    assert block_bootstrap_p(x, y_sig, ic) <= 0.005
    # null: pick a draw whose sample IC is genuinely small — an unlucky
    # 2-sigma draw would rightly get a small p (that is correct behaviour,
    # not a bug, so the fixture must not hand the test one)
    for seed in range(100):
        y_n = np.random.default_rng(1000 + seed).standard_normal(n)
        ic_n = spearman_ic(x, y_n)
        if abs(ic_n) < 0.03:
            break
    assert abs(ic_n) < 0.03
    assert block_bootstrap_p(x, y_n, ic_n) > 0.05


@pytest.mark.filterwarnings("ignore")
def test_e2e_predictive_tilt_passes_null_does_not(tmp_path, monkeypatch):
    from bybit_edge.research.c22_l2tilt import driver as drv
    days = _days("2023-07-01", 130)
    windows = (("PRDUSDT", "WA", days[0], days[59], True),
               ("PRDUSDT", "WB", days[60], days[-2], True))
    tilt_dir, cache = _build_stores(tmp_path / "p", "PRDUSDT", days,
                                    predictive=True, seed=1)
    p = drv.run(tilt_dir, cache, windows=windows, skip_fingerprint_check=True,
                expected_tilt_fps={}, expected_bar_fps={})
    assert p["coverage_ok"] is True
    assert p["both_btc_windows_pass"] is True, p["cells"]

    tilt_n, cache_n = _build_stores(tmp_path / "n", "NULUSDT", days,
                                    predictive=False, seed=2)
    windows_n = (("NULUSDT", "WA", days[0], days[59], True),
                 ("NULUSDT", "WB", days[60], days[-2], True))
    p_n = drv.run(tilt_n, cache_n, windows=windows_n,
                  skip_fingerprint_check=True,
                  expected_tilt_fps={}, expected_bar_fps={})
    assert p_n["both_btc_windows_pass"] is False


def test_coverage_floor_forces_skip(tmp_path):
    days = _days("2023-07-01", 60)
    tilt_dir, cache = _build_stores(tmp_path, "COVUSDT", days[:20],
                                    predictive=True, seed=3)
    windows = (("COVUSDT", "WA", days[0], days[-1], True),)  # 20/60 = 33%
    p = run(tilt_dir, cache, windows=windows, skip_fingerprint_check=True,
            expected_tilt_fps={}, expected_bar_fps={})
    assert p["status"] == "SKIP_COVERAGE"
    assert p["coverage_ok"] is False
    assert p["cells"][0]["floor_met"] is False


def test_fingerprint_mismatch_sets_gate_invalid(tmp_path):
    days = _days("2023-07-01", 40)
    tilt_dir, cache = _build_stores(tmp_path, "FPUSDT", days,
                                    predictive=False, seed=4)
    windows = (("FPUSDT", "WA", days[0], days[-2], True),)
    p = run(tilt_dir, cache, windows=windows,
            expected_tilt_fps={("FPUSDT", "WA"): "deadbeef"},
            expected_bar_fps={"FPUSDT": "deadbeef"})
    assert p["gate_valid"] is False


def test_day_alignment_uses_next_day_return(tmp_path):
    # continuous DISTINCT tilt values drive the next-day return exactly
    # monotonically -> Spearman must be exactly 1.0; a one-day misalignment
    # would destroy it. (Binary tilts would cap the IC below 1 via ties.)
    days = _days("2023-07-01", 40)
    rng = np.random.default_rng(7)
    tilts = rng.standard_normal(len(days))
    tilt_dir, base = tmp_path / "tilt", tmp_path / "h"
    log_close, closes = np.log(100.0), []
    for i in range(len(days)):
        if i > 0:
            log_close += 0.01 * tilts[i - 1]
        closes.append(np.exp(log_close))
    for day, tv, cl in zip(days, tilts, closes):
        _write_tilt_day(tilt_dir, "ALNUSDT", day, float(tv))
        _write_bar_day(base, "ALNUSDT", day, float(cl))
    windows = (("ALNUSDT", "WA", days[0], days[-2], True),)
    p = run(tilt_dir, base.parent / "cache", windows=windows,
            skip_fingerprint_check=True, expected_tilt_fps={},
            expected_bar_fps={})
    assert p["cells"][0]["ic"] == pytest.approx(1.0, abs=1e-9), (
        "perfect next-day prediction must give IC 1.0 — any misalignment "
        "breaks this")
