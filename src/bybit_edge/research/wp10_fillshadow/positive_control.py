"""WP-10(B) -- positive-control pre-run (PRD 3.3.8).

Before the real 86-window replay, a synthetic quote with a KNOWN queue
position placed against a KNOWN synthetic book and KNOWN trades MUST
reproduce a KNOWN fill outcome (both bounding conventions, exact fill
time, exact adverse-selection number) through the real
``queue_model.simulate_quote`` entry point -- the same function the
replay driver calls. The real CLI runner (``scripts/wp10_fillshadow.py
--run``) executes this FIRST and ABORTS (rc != 0) if it fails: a
positive control that fails means the fill machinery itself is broken,
and any subsequent fill-rate measurement built on top of it would be
worthless (DEC-57: "Wirksames Instrument bleibt die Positivkontroll-
Vorschaltung").

Two independent quotes:

  * ``clean_fill`` -- a bid, filled by three trades exactly explaining
    every level-size decrease (no cancellations at all), so FIFO and
    pro-rata agree bit-for-bit on the fill time -- the simplest possible
    non-trivial positive check.
  * ``no_fill`` -- an ask with matching-side trade activity but never
    enough to reach its queue target within the horizon -- guards
    against a machinery that trivially "fills everything".

KAPITALFREI: synthetic self-check only, no live data, no cost quantity.
"""
from __future__ import annotations

from typing import Any

from . import queue_model as qm

__all__ = ["PositiveControlError", "build_fixture", "run_positive_control",
           "assert_positive_control"]


class PositiveControlError(RuntimeError):
    """The positive control did not reproduce its known outcome -- loud abort."""


def build_fixture() -> dict[str, Any]:
    """One synthetic hour (well within it): two independent quotes with
    fully worked-out, hand-checked expected outcomes."""
    t0 = 1_700_000_000_000  # arbitrary fixed epoch ms, deterministic

    clean_fill = {
        "t0_ms": t0, "side": "buy", "price": 100.0, "size": 3.0,
        "horizon_s": 20.0, "adv_sel_horizon_s": 60.0,
        # pos0 = 10 -> target = 13; every decrease is trade-explained.
        "book_levels": [
            (t0, 10.0, 100.0),
            (t0 + 4_000, 6.0, 100.0),     # -4, trade -4 -> unexplained 0
            (t0 + 9_000, 0.0, 100.0),     # -6, trade -6 -> unexplained 0, cum=10
            (t0 + 9_500, 5.0, 100.0),     # refill (new orders join behind us)
            (t0 + 15_000, 2.0, 100.0),    # -3, trade -3 -> unexplained 0, cum=13=target
        ],
        "trades": [
            (t0 + 4_000, "sell", 100.0, 4.0),
            (t0 + 9_000, "sell", 100.0, 6.0),
            (t0 + 15_000, "sell", 100.0, 3.0),
        ],
        "mids": [(t0, 100.0), (t0 + 75_000, 99.5)],  # mid drops 0.5 after fill+60s
        "expect": {
            "fifo_filled": True, "fifo_fill_time_ms": t0 + 15_000,
            "prorata_filled": True, "prorata_fill_time_ms": t0 + 15_000,
            "adv_sel_bp_approx": 50.0,   # (100.0-99.5)/100.0 * 1e4, buy side adverse
        },
    }

    no_fill = {
        "t0_ms": t0, "side": "sell", "price": 200.0, "size": 5.0,
        "horizon_s": 60.0, "adv_sel_horizon_s": 60.0,
        # pos0 = 8 -> target = 13; only 5 units of matching trade volume ever arrive.
        "book_levels": [
            (t0, 8.0, 200.0),
            (t0 + 10_000, 3.0, 200.0),   # -5, trade -5 -> unexplained 0
            (t0 + 40_000, 3.0, 200.0),   # unchanged
        ],
        "trades": [(t0 + 10_000, "buy", 200.0, 5.0)],
        "mids": [(t0, 200.0)],
        "expect": {
            "fifo_filled": False, "fifo_fill_time_ms": None,
            "prorata_filled": False, "prorata_fill_time_ms": None,
        },
    }

    return {"quotes": {"clean_fill": clean_fill, "no_fill": no_fill}}


def run_positive_control() -> dict[str, Any]:
    """Run every fixture quote through the real ``simulate_quote`` and
    compare against its hand-checked expectation. Never raises -- returns
    ``{"ok": bool, "checks": [...]}`` so a caller can decide how loudly
    to fail."""
    fixture = build_fixture()
    checks: list[dict[str, Any]] = []
    ok = True
    for name, spec in fixture["quotes"].items():
        out = qm.simulate_quote(
            spec["book_levels"], spec["trades"], spec["mids"],
            t0_ms=spec["t0_ms"], side=spec["side"], price=spec["price"],
            size=spec["size"], horizon_s=spec["horizon_s"],
            adv_sel_horizon_s=spec["adv_sel_horizon_s"],
        )
        exp = spec["expect"]
        got = {
            "fifo_filled": out["fifo"]["filled"],
            "fifo_fill_time_ms": out["fifo"]["fill_time_ms"],
            "prorata_filled": out["prorata"]["filled"],
            "prorata_fill_time_ms": out["prorata"]["fill_time_ms"],
        }
        passed = (got["fifo_filled"] == exp["fifo_filled"]
                 and got["fifo_fill_time_ms"] == exp["fifo_fill_time_ms"]
                 and got["prorata_filled"] == exp["prorata_filled"]
                 and got["prorata_fill_time_ms"] == exp["prorata_fill_time_ms"])
        if "adv_sel_bp_approx" in exp:
            got["fifo_adv_sel_bp"] = out["fifo"]["adv_sel_bp"]
            passed = (passed and got["fifo_adv_sel_bp"] is not None
                     and abs(got["fifo_adv_sel_bp"] - exp["adv_sel_bp_approx"]) < 1e-6)
        ok = ok and passed
        checks.append({"name": name, "expect": exp, "got": got, "passed": passed})
    return {"ok": ok, "checks": checks}


def assert_positive_control() -> dict[str, Any]:
    """Same as ``run_positive_control`` but raises ``PositiveControlError``
    (loud abort) when any check fails -- the form the CLI runner uses."""
    result = run_positive_control()
    if not result["ok"]:
        failed = [c["name"] for c in result["checks"] if not c["passed"]]
        raise PositiveControlError(
            f"WP-10(B) positive control FAILED for {failed} -- fill "
            f"machinery is broken, real run ABORTED. Details: {result['checks']}")
    return result
