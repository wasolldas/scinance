"""Unit tests for WP-12 (Delisting-Register + Survivorship-Fixture, PRD
4.1 B3, DEC-67 Entscheidung 5).

Covers (per the build brief):
  (a) announcements: parsing of a canned announcements page -- POSITIVE
      (symbols + delisting date extracted), NULL (a page without
      delistings -> empty register, no crash), ADVERSARIAL ("USDT
      margin" -- a non-symbol context -- extracts no false symbol).
  (b) schema-drift loud fail (missing ``result.list``).
  (c) symbol-regex edge cases (``1000PEPEUSDT``, ``BTCPERP``).
  (d) survivorship_fixture on synthetic data: the adversarial (-30%
      terminal drawdown) set shows a NEGATIVE bias; a neutral
      (signal-free) set's bias CI covers 0.
  (e) determinism (N=3 identical runs, same seed -> byte-identical
      bootstrap CI/point).
  (f) a monkeypatched end-to-end ``--mode probe`` run, no network.

No network anywhere in this file (the sandbox egress proxy blocks the
real Bybit API, CLAUDE.md) -- every REST call is monkeypatched to a
fixture fetcher.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp7_universe import bybit_rest, pit_universe
from bybit_edge.research.wp12_delisting import announcements, kline_probe, survivorship_fixture as sf

ROOT = Path(__file__).resolve().parents[2]


def _load_wp12_script():
    p = ROOT / "scripts" / "wp12_delisting.py"
    spec = importlib.util.spec_from_file_location("wp12_delisting_driver", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


WP12 = _load_wp12_script()


# ============================================================================
# (a)/(b)/(c) -- announcements: DEC-39 trio + schema drift + regex edges
# ============================================================================

def _announcement_page(rows: list[dict], *, next_empty: bool = True) -> dict:
    return {"retCode": 0, "retMsg": "OK", "result": {"list": rows}}


def test_announcements_positive_extracts_symbols_and_delisting_date():
    row = {
        "title": "Bybit will delist BTCOLDUSDT",
        "description": "Trading of BTCOLDUSDT will be delisted at 2024-03-15 08:00 UTC.",
        "url": "https://announcements.bybit.com/en/article/btcolde-delist-x123",
        "dateTimestamp": 1700000000000,
    }
    parsed = announcements.parse_announcement_row(row)
    assert parsed["symbols"] == ["BTCOLDUSDT"]
    assert parsed["category"] == "linear"
    assert parsed["delisting_ms"] is not None
    import datetime
    dt = datetime.datetime.fromtimestamp(parsed["delisting_ms"] / 1000, tz=datetime.timezone.utc)
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute) == (2024, 3, 15, 8, 0)
    assert parsed["raw_snippet"] is None
    assert parsed["publish_ms"] == 1700000000000
    assert parsed["url"].endswith("btcolde-delist-x123")
    assert parsed["announcement_id"] == "btcolde-delist-x123"


def test_announcements_null_page_without_delistings_is_empty_no_crash():
    fetcher = bybit_rest.fixture_fetcher([_announcement_page([])])
    fetched = announcements.fetch_delisting_announcements(fetcher=fetcher)
    rows = announcements.build_register_rows(fetched["rows"])
    assert rows == []


def test_announcements_adversarial_usdt_margin_extracts_no_false_symbol():
    row = {"title": "Adjustment of USDT margin requirements",
           "description": "This note concerns USDT margin only, no delisting."}
    parsed = announcements.parse_announcement_row(row)
    assert parsed["symbols"] == []
    assert parsed["category"] == "unknown"


def test_announcements_schema_drift_missing_result_list_loud_fails():
    body = {"retCode": 0, "retMsg": "OK", "result": {"total": 5}}  # no "list" key at all
    result = bybit_rest.unwrap_result(body)
    with pytest.raises(announcements.AnnouncementFieldLayoutError, match="result.list"):
        announcements.parse_announcement_rows(result)


def test_announcements_schema_drift_missing_title_loud_fails():
    body = {"retCode": 0, "result": {"list": [{"url": "https://x/y", "dateTimestamp": 1}]}}
    result = bybit_rest.unwrap_result(body)
    with pytest.raises(announcements.AnnouncementFieldLayoutError, match="title"):
        announcements.parse_announcement_rows(result)


@pytest.mark.parametrize("token,expected", [
    ("1000PEPEUSDT", ["1000PEPEUSDT"]),
    ("BTCPERP", ["BTCPERP"]),
    ("BTCUSDT", ["BTCUSDT"]),
    ("USDT", []),  # bare suffix, no prefix -- must NOT match (adversarial edge)
    ("USD", []),
])
def test_symbol_regex_edge_cases(token, expected):
    assert announcements.extract_symbols(f"Bybit will delist {token} soon") == expected


def test_symbol_regex_dedup_preserves_first_seen_order():
    text = "BTCUSDT delisting; also ETHUSDT and BTCUSDT again"
    assert announcements.extract_symbols(text) == ["BTCUSDT", "ETHUSDT"]


# ============================================================================
# (d) survivorship_fixture -- adversarial negative bias, neutral CI covers 0
# ============================================================================

def _neutral_base_panel(n_weeks: int, n_symbols: int, seed: int, vol: float = 0.05):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0, vol, size=(n_weeks, n_symbols))
    alive = np.ones((n_weeks, n_symbols), dtype=bool)
    return returns, alive


def test_survivorship_fixture_adversarial_synthetic_shows_negative_bias():
    n_weeks = 40
    base_returns, base_alive = _neutral_base_panel(n_weeks, 25, seed=7)
    dd = sf.make_synthetic_delisted_panel(n_weeks, n_symbols=20, seed=1, min_life_weeks=10)
    result = sf.run_fixture_measurement(
        base_returns, base_alive, dd["returns"], dd["alive"],
        seed=42, n_boot=200, mode_label=sf.SYNTHETIC_SYMBOL_PREFIX)
    assert result["bias_point"] < 0.0, (
        "SYNTHETIC adversarial set (-30% terminal drawdown, task brief item 3) must show a "
        f"NEGATIVE bias -- got {result['bias_point']}")
    assert result["mode_label"] == "SYNTHETIC"
    assert sf.THRESHOLD_NOT_REGISTERED_NOTE in result["threshold_note"]
    assert "KEIN PASS/FAIL" in result["threshold_note"]  # never a verdict, PRD 4.1 B3


def test_survivorship_fixture_neutral_synthetic_bias_ci_covers_zero():
    n_weeks = 40
    base_returns, base_alive = _neutral_base_panel(n_weeks, 25, seed=7)
    dd = sf.make_synthetic_delisted_panel(
        n_weeks, n_symbols=20, seed=1, min_life_weeks=10, terminal_drawdown=0.0)
    result = sf.run_fixture_measurement(
        base_returns, base_alive, dd["returns"], dd["alive"],
        seed=42, n_boot=200, mode_label="NEUTRAL")
    b = result["bootstrap"]
    assert b["ci_lo"] <= 0.0 <= b["ci_hi"], (
        f"neutral (signal-free, terminal_drawdown=0.0) set's bias CI must cover 0 -- "
        f"got [{b['ci_lo']}, {b['ci_hi']}]")


def test_synthetic_delisted_panel_symbols_are_clearly_labelled():
    dd = sf.make_synthetic_delisted_panel(20, n_symbols=5, seed=1, min_life_weeks=8)
    assert all(s.startswith(sf.SYNTHETIC_SYMBOL_PREFIX) for s in dd["symbols"])


def test_synthetic_delisted_panel_terminal_drawdown_is_exact():
    n_weeks = 20
    dd = sf.make_synthetic_delisted_panel(
        n_weeks, n_symbols=8, seed=3, min_life_weeks=10, terminal_drawdown=-0.30,
        drawdown_weeks=8)
    for j, delist_week in enumerate(dd["delist_weeks"]):
        dd_lo = delist_week - 8 + 1
        total_log_return = float(dd["returns"][dd_lo:delist_week + 1, j].sum())
        assert total_log_return == pytest.approx(np.log(0.70), abs=1e-9)


def test_synthetic_delisted_panel_every_symbol_delists_before_panel_end():
    n_weeks = 30
    dd = sf.make_synthetic_delisted_panel(n_weeks, n_symbols=10, seed=2, min_life_weeks=10)
    assert all(w < n_weeks - 1 for w in dd["delist_weeks"])
    for j, w in enumerate(dd["delist_weeks"]):
        assert dd["alive"][w, j]
        assert not dd["alive"][w + 1, j]


def test_pooled_rho_of_full_pairs_matches_pit_universe_momentum_ic_series():
    """weekly_signal_outcome_pairs()/pooled_rho() must reproduce
    pit_universe.momentum_ic_series()'s pooled rho bit-for-bit on the SAME
    input (both implement the identical trailing-signal/pooling rule) --
    this is what makes the cluster bootstrap trustworthy."""
    n_weeks = 30
    returns, alive = _neutral_base_panel(n_weeks, 15, seed=4)
    pairs = sf.weekly_signal_outcome_pairs(returns, alive)
    own_rho = sf.pooled_rho(pairs)
    lib = pit_universe.momentum_ic_series(returns, alive)
    assert own_rho == pytest.approx(lib["rho"], abs=1e-12)


# ============================================================================
# (e) determinism -- N=3 identical runs, same seed
# ============================================================================

def test_cluster_bootstrap_bias_is_deterministic_n3():
    n_weeks = 30
    base_returns, base_alive = _neutral_base_panel(n_weeks, 20, seed=9)
    dd = sf.make_synthetic_delisted_panel(n_weeks, n_symbols=10, seed=2, min_life_weeks=8)

    results = []
    for _ in range(3):
        r = sf.run_fixture_measurement(
            base_returns, base_alive, dd["returns"], dd["alive"],
            seed=123, n_boot=150, mode_label="SYNTHETIC")
        results.append(r)

    fps = {sf.artifact_fingerprint(r) for r in results}
    assert len(fps) == 1, "same seed must give a byte-identical bootstrap fingerprint across N=3 runs"
    for r in results[1:]:
        assert r["bias_point"] == results[0]["bias_point"]
        assert r["bootstrap"]["ci_lo"] == results[0]["bootstrap"]["ci_lo"]
        assert r["bootstrap"]["ci_hi"] == results[0]["bootstrap"]["ci_hi"]


def test_extract_delisting_ms_is_deterministic():
    text = "Delisting effective 2024-03-15 08:00 UTC."
    a = announcements.extract_delisting_ms(text)
    b = announcements.extract_delisting_ms(text)
    assert a == b


# ============================================================================
# (f) monkeypatched end-to-end ``--mode probe``, no network
# ============================================================================

def _fixture_fetcher_dispatch(monkeypatch):
    """Monkeypatch ``bybit_rest._default_fetcher`` (shared by both
    ``announcements.py`` and ``kline_probe.py``, read at call time) with a
    dispatcher that serves canned announcements pages and kline pages by
    inspecting the request URL -- no real network anywhere."""
    ann_pages = iter([
        _announcement_page([
            {"title": "Bybit will delist OLDCOINUSDT",
             "description": "Trading of OLDCOINUSDT ends 2024-01-10 08:00 UTC.",
             "url": "https://announcements.bybit.com/en/article/oldcoin-delist",
             "dateTimestamp": 1700000000000},
        ]),
        _announcement_page([]),  # page 2: empty -> pagination stops
    ])
    kline_rows = [[str(1699000000000 + i * 86_400_000), "1.0", "1.1", "0.9", "1.0",
                   "1000", "1000"] for i in range(5)]
    kline_page = {"retCode": 0, "retMsg": "OK",
                  "result": {"category": "linear", "symbol": "OLDCOINUSDT", "list": kline_rows}}

    def dispatch(url: str) -> bytes:
        if "announcements" in url:
            page = next(ann_pages, None)
            body = page if page is not None else {"retCode": 0, "result": {"list": []}}
        elif "kline" in url:
            body = kline_page
        else:
            raise AssertionError(f"unexpected URL in monkeypatched fetcher: {url}")
        return json.dumps(body).encode("utf-8")

    monkeypatch.setattr(bybit_rest, "_default_fetcher", dispatch)


def _ns(**overrides) -> argparse.Namespace:
    base = dict(
        register_base="", locale=announcements.DEFAULT_LOCALE, type=announcements.DEFAULT_TYPE,
        tag=announcements.FALLBACK_TAG, page_limit=50,
        window_days=kline_probe.PROBE_WINDOW_DAYS, max_symbols=None,
        panel_base="data/panel_1d", manifest="data/panel_1d/panel_manifest.sqlite",
        start_year=2021, end_year=2026, as_of="", allow_partial=False,
        seed=53, n_boot=200, n_synthetic=10, out="", mode="probe",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_end_to_end_mode_probe_no_network(tmp_path, monkeypatch):
    _fixture_fetcher_dispatch(monkeypatch)
    register_base = tmp_path / "delisting_register"
    out_dir = tmp_path / "wp12_out"

    a = _ns(register_base=str(register_base), out=str(out_dir), mode="probe")
    rc1 = WP12.cmd_announce(a)
    assert rc1 == 0
    assert (register_base / "register.parquet").is_file()
    manifest = json.loads((register_base / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["n_register_rows"] == 1
    assert manifest["n_symbols_linear"] == 1

    rc2 = WP12.cmd_probe_klines(a)
    assert rc2 == 0
    assert (register_base / "klines" / "kline_probe_summary.json").is_file()

    rc3 = WP12.cmd_report(a)
    assert rc3 == 0
    summary_path = out_dir / "wp12_summary.json"
    report_path = out_dir / "wp12_report.md"
    assert summary_path.is_file() and report_path.is_file()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["mode"] == "probe"
    assert "register" in summary and summary["register"]["n_announcements"] == 1
    assert "kline_probe" in summary
    assert summary["kline_probe"]["n_available"] == 1
    assert "fixture" not in summary  # --mode probe never measures a bias
    md = report_path.read_text(encoding="utf-8")
    assert "Survivorship-Fixture" in md
    assert "PASS" not in md and "FAIL" not in md
