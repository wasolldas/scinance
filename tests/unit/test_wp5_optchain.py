"""Unit tests for the WP-5 Bybit option-chain spread census.

Covers:
  (a) symbol parsing, including the malformed/non-option rejects,
  (b) the PowerShell BOM that every user-side ``Out-File`` snapshot carries,
  (c) THE KEY TEST: the deep-ITM pooling artifact.  A chain whose OTM
      strikes are quoted one tick wide but whose deep-ITM strikes carry
      numerically degenerate bid1Iv/ask1Iv must show a LARGE pooled IV
      width and a SMALL OTM-bucket width -- otherwise the |delta| axis
      would be decoration and the census would report the artifact,
  (d) DEC-39 duty, both directions on fixtures: a "tight" chain where the
      leg width is far below a 3-vol-point edge, and a "wide" chain where
      it is far above,
  (e) the scale-free identity: vega/S and the break-even fee are invariant
      under a change of the underlying's price scale,
  (f) breakeven_fee_bp / cost_volpts are exact inverses,
  (g) the module carries no threshold, verdict or PnL vocabulary.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from bybit_edge.research.wp5_optchain.census import (
    breakeven_fee_bp,
    census,
    cost_volpts,
    load_snapshot,
    parse_symbol,
    quantile,
    vega_over_index,
)

ASOF = date(2026, 8, 24)


# ---------------------------------------------------------------------------
# (a) symbol parsing
# ---------------------------------------------------------------------------

def test_parse_symbol_roundtrip():
    m = parse_symbol("BTC-25AUG26-76500-C-USDT")
    assert m == {"base": "BTC", "expiry": date(2026, 8, 25),
                 "strike": 76500.0, "cp": "C"}
    assert parse_symbol("ETH-4SEP26-2250-P-USDT")["expiry"] == date(2026, 9, 4)


@pytest.mark.parametrize("sym", [
    "BTCUSDT",                    # perp, not an option
    "BTC-25AUG26-76500",          # missing right
    "BTC-25XXX26-76500-C-USDT",   # bad month
    "BTC-25AUG26-abc-C-USDT",     # bad strike
    "BTC-25AUG26-76500-X-USDT",   # bad right
])
def test_parse_symbol_rejects(sym):
    assert parse_symbol(sym) is None


# ---------------------------------------------------------------------------
# fixture chain builders
# ---------------------------------------------------------------------------

def _leg(sym, bid, ask, biv, aiv, delta, vega, under, oi=100.0, v24=10.0):
    return {"symbol": sym, "bid1Price": str(bid), "ask1Price": str(ask),
            "bid1Iv": str(biv), "ask1Iv": str(aiv), "delta": str(delta),
            "vega": str(vega), "underlyingPrice": str(under),
            "markPrice": str(0.5 * (bid + ask)), "markIv": str(0.5*(biv+aiv)),
            "openInterest": str(oi), "volume24h": str(v24),
            "bid1Size": "1.0", "ask1Size": "1.0"}


def _chain(otm_iv_width: float, under: float = 77_900.0,
           vega: float = 41.15) -> list[dict]:
    """11-DTE chain: 6 OTM strikes at a given IV width + degenerate ITM.

    The ITM strikes carry a one-tick PRICE width but a bid1Iv/ask1Iv pair
    that is numerically meaningless (vega ~ 0), which is exactly the corner
    that poisons a pooled statistic.
    """
    rows = []
    for i, d in enumerate((0.16, 0.20, 0.24, -0.17, -0.22, -0.28)):
        b = 0.40
        rows.append(_leg(f"BTC-4SEP26-{80000 + 1000*i}-"
                         f"{'C' if d > 0 else 'P'}-USDT",
                         600 + 10 * i, 605 + 10 * i,
                         b, b + otm_iv_width / 100.0, d, vega, under))
    for i, d in enumerate((0.88, 0.92, 0.96)):
        rows.append(_leg(f"BTC-4SEP26-{50000 + 1000*i}-C-USDT",
                         20_000 + 10 * i, 20_005 + 10 * i,
                         0.30, 0.30 + 0.40, d, 0.4, under, oi=2.0, v24=0.0))
    return rows


def _write(tmp_path: Path, rows: list[dict], bom: bool) -> Path:
    p = tmp_path / "chain.json"
    text = json.dumps(rows)
    p.write_text(text, encoding="utf-8-sig" if bom else "utf-8")
    return p


# ---------------------------------------------------------------------------
# (b) BOM
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bom", [True, False])
def test_powershell_bom_is_tolerated(tmp_path, bom):
    rows = load_snapshot(_write(tmp_path, _chain(0.14), bom), ASOF)
    assert len(rows) == 9
    assert rows[0]["dte"] == 11


def test_full_envelope_is_accepted(tmp_path):
    p = tmp_path / "env.json"
    p.write_text(json.dumps({"retCode": 0,
                             "result": {"list": _chain(0.14)}}),
                 encoding="utf-8")
    assert len(load_snapshot(p, ASOF)) == 9


def test_zero_bid_iv_is_not_counted_as_quoted(tmp_path):
    rows = _chain(0.14)
    rows[0]["bid1Iv"] = "0"
    parsed = load_snapshot(_write(tmp_path, rows, False), ASOF)
    bad = [r for r in parsed if r["symbol"] == rows[0]["symbol"]][0]
    assert bad["two_sided"] is True
    assert bad["quoted_iv"] is False, (
        "a zero bid IV is a missing quote, not a 40-vol-point spread")


# ---------------------------------------------------------------------------
# (c) the pooling artifact -- the reason the |delta| axis exists
# ---------------------------------------------------------------------------

def test_deep_itm_poisons_the_pooled_iv_width_but_not_the_otm_bucket(tmp_path):
    rows = load_snapshot(_write(tmp_path, _chain(0.14), False), ASOF)
    c = census(rows, horizon=(7, 14), leg_delta=(0.15, 0.30))
    pooled = c["by_dte"]["8-21"]["iv_width_pts"]["p75"]
    otm = c["horizon"]["by_delta"]["|d| 0.10-0.20"]["iv_width_pts"]["p50"]
    itm = c["horizon"]["by_delta"]["|d| 0.65-1.00 ITM"]["iv_width_pts"]["p50"]
    assert itm > 30.0, "fixture must contain the degenerate corner"
    assert otm == pytest.approx(0.14, abs=1e-9)
    assert pooled > 10.0, (
        "pooling over all strikes must inherit the degenerate corner -- "
        "this is the artifact the delta axis is there to expose")


# ---------------------------------------------------------------------------
# (d) DEC-39 duty: a regime that shows it, and one that does not
# ---------------------------------------------------------------------------

EDGE_VOLPTS = 3.0


def test_tight_chain_leaves_the_edge_intact(tmp_path):
    rows = load_snapshot(_write(tmp_path, _chain(0.14), False), ASOF)
    c = census(rows, horizon=(7, 14), leg_delta=(0.15, 0.30))
    assert c["legs"]["n"] == 6
    rt = c["economics"]["spread_cost_2legs_roundtrip_volpts"]
    assert rt == pytest.approx(0.28, abs=1e-9)
    assert rt < 0.2 * EDGE_VOLPTS, "tight regime: spread is a minor tax"


def test_wide_chain_consumes_the_edge(tmp_path):
    rows = load_snapshot(_write(tmp_path, _chain(4.0), False), ASOF)
    c = census(rows, horizon=(7, 14), leg_delta=(0.15, 0.30))
    rt = c["economics"]["spread_cost_2legs_roundtrip_volpts"]
    assert rt == pytest.approx(8.0, abs=1e-9)
    assert rt > 2.0 * EDGE_VOLPTS, "wide regime: spread alone kills it"


# ---------------------------------------------------------------------------
# (e)/(f) scale-freedom and the fee arithmetic
# ---------------------------------------------------------------------------

def test_vega_over_index_is_scale_free(tmp_path):
    """Same option economics at a 30x smaller underlying -> same bp/volpt."""
    da, db = tmp_path / "a", tmp_path / "b"
    da.mkdir()
    db.mkdir()
    a = load_snapshot(
        _write(da, _chain(0.14, under=77_900.0, vega=41.15), False), ASOF)
    b = load_snapshot(
        _write(db, _chain(0.14, under=2_490.0,
                          vega=41.15 * 2_490.0 / 77_900.0), False), ASOF)
    va, vb = vega_over_index(a), vega_over_index(b)
    assert va == pytest.approx(vb, rel=1e-9)
    assert breakeven_fee_bp(3.0, 4, va) == pytest.approx(
        breakeven_fee_bp(3.0, 4, vb), rel=1e-9)


def test_breakeven_and_cost_are_exact_inverses():
    vs = 5.2823627
    for edge in (1.0, 3.0, 7.5):
        for fills in (1, 2, 4):
            f = breakeven_fee_bp(edge, fills, vs)
            assert cost_volpts(f, fills, vs) == pytest.approx(edge, rel=1e-12)


def test_quantile_edges():
    assert quantile([], 0.5) is None
    assert quantile([7.0], 0.9) == 7.0
    assert quantile([0.0, 1.0], 0.5) == pytest.approx(0.5)
    assert quantile([0.0, 1.0, 2.0, 3.0], 0.75) == pytest.approx(2.25)


# ---------------------------------------------------------------------------
# (g) no thresholds / no verdicts / no PnL in the measurement module
# ---------------------------------------------------------------------------

def test_module_states_no_verdict():
    import ast
    src = (Path(__file__).resolve().parents[2] / "src" / "bybit_edge"
           / "research" / "wp5_optchain" / "census.py").read_text("utf-8")
    tree = ast.parse(src)
    code = src
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                code = code.replace(doc, "")
    lowered = "\n".join(l for l in code.splitlines()
                        if not l.lstrip().startswith("#")).lower()
    for term in ("pnl", "sharpe", "verdikt", "befund", "threshold",
                 "fee_taker", "fee_maker"):
        assert term not in lowered, term


def test_single_object_snapshot_is_wrapped(tmp_path):
    """PowerShell ConvertTo-Json unwraps a one-element array into an object."""
    p = tmp_path / "one.json"
    p.write_text(json.dumps(_chain(0.14)[0]), encoding="utf-8")
    rows = load_snapshot(p, ASOF)
    assert len(rows) == 1 and rows[0]["quoted_iv"] is True
