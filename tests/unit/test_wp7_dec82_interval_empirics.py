"""DEC-82 -- V-1 empirics in the WP-7 census (descriptive, additive).

Covers ``panel_load.funding_deadzone_census`` ``by_interval_class`` (exact
hits of each class's daily mean against EVERY candidate I, plus the 5 most
frequent daily means) and ``panel_load.interval_class_switching``
``episodes_summary`` (run statistics split at the [sek] auto-switch
reference date), plus their Markdown rendering. Synthetic panels only; the
expected values are constructed by hand, never derived from the code under
test.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pytest

from bybit_edge.research.wp7_universe import panel_load
from bybit_edge.research.wp7_universe import report as report_mod

I8 = panel_load.I_PER_8H  # 0.0001 per 8h settlement


def _dates(start: date, n: int) -> list[str]:
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]


def _fill(funding_n, funding_sum, col, rows, fn, avg):
    """Set ``rows`` of column ``col`` to ``fn`` payments averaging ``avg``."""
    for r in rows:
        funding_n[r, col] = fn
        funding_sum[r, col] = fn * avg


# ----------------------------------------------------------------------------
# by_interval_class
# ----------------------------------------------------------------------------

def test_by_interval_class_diagonal_dominates_and_modal_values_exact():
    n_days = 11
    symbols = ["S8USDT", "S4USDT", "S2USDT", "S1USDT"]
    funding_n = np.full((n_days, 4), np.nan)
    funding_sum = np.full((n_days, 4), np.nan)
    # 8h: 6 days exactly at I (0.0001), then 5 distinct off-zone means
    # (6 distinct modal values in total -> top-5 truncation).
    _fill(funding_n, funding_sum, 0, range(0, 6), 3, 0.0001)
    for r, avg in zip(range(6, 11), (0.0005, 0.0006, 0.0007, 0.0008, 0.0009)):
        _fill(funding_n, funding_sum, 0, [r], 3, avg)
    # 4h: 5 days exactly at I/2 (0.00005), 3 off-zone days at 0.0003
    _fill(funding_n, funding_sum, 1, range(0, 5), 6, 0.00005)
    _fill(funding_n, funding_sum, 1, range(5, 8), 6, 0.0003)
    # 2h: 5 days exactly at I/4 (0.000025)
    _fill(funding_n, funding_sum, 2, range(0, 5), 12, 0.000025)
    # 1h: 4 days exactly at I/8 (0.0000125), 3 off-zone days at 0.0002
    _fill(funding_n, funding_sum, 3, range(0, 4), 24, 0.0000125)
    _fill(funding_n, funding_sum, 3, range(4, 7), 24, 0.0002)

    panel = {"symbols": symbols, "dates": _dates(date(2025, 11, 1), n_days),
             "funding_n": funding_n, "funding_sum": funding_sum}
    res = panel_load.funding_deadzone_census(panel, n_deciles=2)
    bic = res["by_interval_class"]

    assert list(bic) == ["60min", "120min", "240min", "480min"]
    expected_n = {"60min": 7, "120min": 5, "240min": 8, "480min": 11}
    expected_diag = {"60min": 4, "120min": 5, "240min": 5, "480min": 6}
    for label, n in expected_n.items():
        c = bic[label]
        assert c["n_symbol_days"] == n
        assert c["n_mean_nan"] == 0
        assert list(c["exact_hits_vs_candidate_I"]) == [
            "I_60min", "I_120min", "I_240min", "I_480min"]
        for cand, hit in c["exact_hits_vs_candidate_I"].items():
            if cand == f"I_{label}":
                assert hit["n"] == expected_diag[label]
                assert hit["share"] == pytest.approx(expected_diag[label] / n)
            else:  # off-diagonal: exactly zero, as constructed
                assert hit["n"] == 0
                assert hit["share"] == 0.0

    # diagonal total == the existing DEC-59 deadzone count (same rule, same tol)
    assert sum(expected_diag.values()) == res["n_deadzone_symbol_days"] == 20
    assert res["interval_class_counts"] == {"480min": 11, "240min": 8, "120min": 5, "60min": 7}

    def top(label):
        return [(t["value"], t["n"], t["share"]) for t in bic[label]["top5_daily_means"]]

    t480 = top("480min")
    assert len(t480) == 5  # 6 distinct means -> truncated to 5, ties by ascending value
    assert t480[0][0] == pytest.approx(0.0001, abs=1e-12) and t480[0][1] == 6
    assert t480[0][2] == pytest.approx(6 / 11)
    assert [round(v, 10) for v, n, _ in t480[1:]] == [0.0005, 0.0006, 0.0007, 0.0008]
    assert all(n == 1 for _, n, _ in t480[1:])

    t240 = top("240min")
    assert [(round(v, 10), n) for v, n, _ in t240] == [(0.00005, 5), (0.0003, 3)]
    t120 = top("120min")
    assert [(round(v, 10), n) for v, n, _ in t120] == [(0.000025, 5)]
    t60 = top("60min")
    assert [(round(v, 10), n) for v, n, _ in t60] == [(0.0000125, 4), (0.0002, 3)]
    assert t60[0][2] == pytest.approx(4 / 7)


def test_by_interval_class_unscaled_4h_mean_hits_480_candidate_not_240():
    """Counter-example: 4h days (funding_n=6) whose mean is the UNSCALED
    0.0001 hit the I_480min column and never I_240min; the existing
    (scaled) deadzone rule correspondingly reports none."""
    n_days = 6
    funding_n = np.full((n_days, 1), np.nan)
    funding_sum = np.full((n_days, 1), np.nan)
    _fill(funding_n, funding_sum, 0, range(n_days), 6, 0.0001)
    panel = {"symbols": ["FOURHUSDT"], "dates": _dates(date(2025, 11, 1), n_days),
             "funding_n": funding_n, "funding_sum": funding_sum}
    res = panel_load.funding_deadzone_census(panel, n_deciles=2)
    c = res["by_interval_class"]["240min"]
    hits = c["exact_hits_vs_candidate_I"]
    assert c["n_symbol_days"] == n_days
    assert hits["I_480min"] == {"n": n_days, "share": 1.0}
    assert hits["I_240min"] == {"n": 0, "share": 0.0}
    assert hits["I_120min"]["n"] == 0 and hits["I_60min"]["n"] == 0
    assert [(round(t["value"], 10), t["n"]) for t in c["top5_daily_means"]] == [(0.0001, n_days)]
    assert res["n_deadzone_symbol_days"] == 0  # existing scaled rule untouched


def test_by_interval_class_without_funding_is_empty_but_well_formed():
    panel = {"symbols": ["NOFUNDUSDT"], "dates": _dates(date(2025, 11, 1), 3),
             "funding_n": np.full((3, 1), np.nan), "funding_sum": np.full((3, 1), np.nan)}
    res = panel_load.funding_deadzone_census(panel, n_deciles=2)
    for label in ("60min", "120min", "240min", "480min"):
        c = res["by_interval_class"][label]
        assert c["n_symbol_days"] == 0 and c["top5_daily_means"] == []
        assert all(h == {"n": 0, "share": None}
                   for h in c["exact_hits_vs_candidate_I"].values())
    json.dumps(res)  # no NaN-only structure problems, JSON-serialisable


# ----------------------------------------------------------------------------
# episodes_summary
# ----------------------------------------------------------------------------

def _episode_panel():
    """42 days 2025-10-20..2025-11-30; reference date 2025-10-30 is row 10."""
    start = date(2025, 10, 20)
    n_days = 42
    symbols = ["XUSDT", "YUSDT", "ZUSDT", "WUSDT", "VUSDT", "UUSDT"]
    funding_n = np.full((n_days, len(symbols)), np.nan)

    def rows(a: str, b: str) -> range:
        return range((date.fromisoformat(a) - start).days,
                     (date.fromisoformat(b) - start).days + 1)

    def seg(col, a, b, fn):
        for r in rows(a, b):
            funding_n[r, col] = fn

    # X: 480 -> 60 (starts BEFORE the reference date, runs across it) -> 480
    #    -> 60 with a funding_n=0 day mid-run -> 480 (open at panel end)
    seg(0, "2025-10-20", "2025-10-27", 3)
    seg(0, "2025-10-28", "2025-11-02", 24)
    seg(0, "2025-11-03", "2025-11-10", 3)
    seg(0, "2025-11-11", "2025-11-14", 24)
    funding_n[(date(2025, 11, 12) - start).days, 0] = 0.0
    seg(0, "2025-11-15", "2025-11-30", 3)
    # Y: 240 throughout (open)
    seg(1, "2025-10-20", "2025-11-30", 6)
    # Z: 480 until 2025-11-05, then no data (delisted): closed by data end
    seg(2, "2025-10-20", "2025-11-05", 3)
    # W: 480 until 2025-11-19, then 60 until the end (open)
    seg(3, "2025-10-20", "2025-11-19", 3)
    seg(3, "2025-11-20", "2025-11-30", 24)
    # V: 480 with two UNCLASSIFIED days (funding_n=5) mid-run -> still one run
    seg(4, "2025-10-20", "2025-11-30", 3)
    seg(4, "2025-10-26", "2025-10-27", 5)
    # U: 480 until 2025-10-29, 60 FROM exactly the reference date (open)
    seg(5, "2025-10-20", "2025-10-29", 3)
    seg(5, "2025-10-30", "2025-11-30", 24)
    return {"symbols": symbols, "dates": _dates(start, n_days), "funding_n": funding_n}


def test_episodes_summary_counts_durations_transitions_and_open_runs():
    res = panel_load.interval_class_switching(_episode_panel())
    es = res["episodes_summary"]

    assert panel_load.AUTO_SWITCH_REFERENCE_DATE == date(2025, 10, 30)
    assert es["reference_date"] == "2025-10-30"
    assert "per_symbol" not in es and "per_symbol" not in json.dumps(es)  # aggregates only
    bc = es["by_class"]

    # 480min before: X(10-20..27)=8d, W(10-20..11-19)=31d, U(10-20..10-29)=10d;
    # Z(10-20..11-05) closed by data end (delisting) is right-censored and NOT a
    # duration; V open (unclassified days skipped).
    b480 = bc["480min"]["before"]
    assert (b480["n_runs"], b480["n_open_at_end"], b480["n_closed_by_data_end"]) == (5, 1, 1)
    d = b480["duration_days"]
    assert d["n"] == 3
    assert d["median"] == pytest.approx(10.0)
    assert d["q10"] == pytest.approx(8.4)
    assert d["q25"] == pytest.approx(9.0)
    assert d["q75"] == pytest.approx(20.5)
    assert d["q90"] == pytest.approx(26.8)
    assert d["max"] == pytest.approx(31.0)

    # 480min from: X(11-03..10)=8d closed, X(11-15..) open
    f480 = bc["480min"]["from"]
    assert (f480["n_runs"], f480["n_open_at_end"], f480["n_closed_by_data_end"]) == (2, 1, 0)
    assert f480["duration_days"]["n"] == 1 and f480["duration_days"]["median"] == 8.0
    assert f480["duration_days"]["max"] == 8.0

    # 60min before: only X(10-28..11-02)=6d (starts before the date, crosses it)
    b60 = bc["60min"]["before"]
    assert (b60["n_runs"], b60["n_open_at_end"]) == (1, 0)
    assert b60["duration_days"]["n"] == 1 and b60["duration_days"]["median"] == 6.0
    # 60min from: X(11-11..14) = 4 calendar days incl. the funding_n=0 gap day
    # (the gap does NOT interrupt the run); W and U open (U starts ON the date).
    f60 = bc["60min"]["from"]
    assert (f60["n_runs"], f60["n_open_at_end"], f60["n_closed_by_data_end"]) == (3, 2, 0)
    assert f60["duration_days"]["n"] == 1 and f60["duration_days"]["median"] == 4.0

    # 240min: Y alone, open -> counted, but no duration entry
    b240 = bc["240min"]["before"]
    assert (b240["n_runs"], b240["n_open_at_end"]) == (1, 1)
    assert b240["duration_days"] == {"n": 0, "median": None, "q10": None, "q25": None,
                                      "q75": None, "q90": None, "max": None}
    assert bc["240min"]["from"]["n_runs"] == 0
    assert bc["120min"]["before"]["n_runs"] == 0 and bc["120min"]["from"]["n_runs"] == 0

    # transitions, split by the date the NEW run starts
    assert es["transitions"]["before"] == {"480min->60min": 1}
    assert es["transitions"]["from"] == {"480min->60min": 3, "60min->480min": 2}
    assert es["n_symbols_with_60min_run"] == {"before": 1, "from": 3}

    # the pre-existing switching fields are unchanged (X: 4 switches, V: none -
    # unclassified days are neither an edge nor a break)
    per = {r["symbol"]: r for r in res["per_symbol"]}
    assert per["XUSDT"]["n_switches"] == 4 and per["VUSDT"]["n_switches"] == 0
    assert res["n_switch_distribution"] == {"0": 3, "1": 2, "2-5": 1, ">5": 0}
    assert res["descriptive_only"] is True
    json.dumps(res)


def test_episodes_summary_empty_panel_is_well_formed():
    panel = {"symbols": ["NONEUSDT"], "dates": _dates(date(2025, 11, 1), 3),
             "funding_n": np.full((3, 1), np.nan)}
    es = panel_load.interval_class_switching(panel)["episodes_summary"]
    for m in ("60min", "120min", "240min", "480min"):
        for p in ("before", "from"):
            assert es["by_class"][m][p]["n_runs"] == 0
            assert es["by_class"][m][p]["duration_days"]["n"] == 0
    assert es["transitions"] == {"before": {}, "from": {}}
    assert es["n_symbols_with_60min_run"] == {"before": 0, "from": 0}


# ----------------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------------

def test_markdown_sections_for_dec82_are_present_and_ascii():
    n_days = 6
    funding_n = np.full((n_days, 1), np.nan)
    funding_sum = np.full((n_days, 1), np.nan)
    _fill(funding_n, funding_sum, 0, range(n_days), 6, 0.0001)
    panel = {"symbols": ["FOURHUSDT"], "dates": _dates(date(2025, 11, 1), n_days),
             "funding_n": funding_n, "funding_sum": funding_sum}
    extra = {
        "deadzone_census_dec59": panel_load.funding_deadzone_census(panel, n_deciles=2),
        "interval_switching": {"label": "Intervallklassen-Wechsel je Symbol (deskriptiv, kein Urteil)",
                                **panel_load.interval_class_switching(panel)},
    }
    text = "\n".join(report_mod._extra_sections_markdown(extra))
    text.encode("ascii")  # raises on any non-ASCII character
    assert "## DEC-82: Totzone je Intervallklasse gegen Kandidaten-I" in text
    assert "## DEC-82: Intervallklassen-Episoden, getrennt vor/ab 2025-10-30" in text
    assert "I_480min=6 (1.0000)" in text
    assert "0.0001 n=6 (1.0000)" in text
    assert "- 240min ab: laeufe=1 offen_am_ende=1" in text
    # existing sections still rendered
    assert "## DEC-59: Totzonen-/Bindungs-Zensus" in text
    assert "Intervallklassen-Wechsel je Symbol" in text
