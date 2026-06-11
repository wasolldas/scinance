"""E-17 divergence check: current run vs. a baseline result set.

Background (registered context of H-01): the S3 ``total_return`` diverged
~3.2x between iter-3 (-2113.26 USD, 204 trades) and iter-4 (-6857.56 USD,
213 trades) although trade counts were nearly identical — unexplained as of
registration (FINAL_PRD.md Pilot 1; ANALYSIS_REPORT_iter3/iter4.md). H-01
requires this divergence to be "geklärt" before a WEITER verdict.

This module DELIVERS the data for that clarification: ratios, per-symbol
attribution and tail-trade quantification between the current (iter-5) run and
a baseline run (typically iter-4, optionally iter-3 raw-PnL export). The final
E-17 ruling is made by the gate-auditor against the registry — the heuristic
``resolved`` flag here is decision support, not the ruling itself.
"""
from __future__ import annotations

from typing import Any, Optional

from .metrics import STRATEGY_S3, Trade

#: Registered E-17 reference numbers (source: ANALYSIS_REPORT_iter3.md S3 "All"
#: row and iter-4 replay_all_results.json per_strategy_aggregate.S3).
ITER3_S3_TOTAL_RETURN_USD = -2113.26
ITER4_S3_TOTAL_RETURN_USD = -6857.555675
KNOWN_DIVERGENCE_RATIO = 3.24  # |iter4| / |iter3|, the unexplained ~3.2x gap

#: Heuristic bands (builder operationalisation, documented in the report):
#: trade counts within +-25% count as "similar"; total returns within a factor
#: of 2 count as "consistent scale".
TRADES_SIMILAR_BAND = (0.80, 1.25)
RETURN_SIMILAR_BAND = (0.50, 2.00)
#: A single symbol / the tail-trade set "explains" the gap when it covers at
#: least this share of the absolute total_return difference.
EXPLAINED_SHARE_THRESHOLD = 0.80
#: Number of largest-loss trades inspected for tail attribution.
TAIL_TOP_N = 5

_AUDITOR_NOTE = (
    "Endgueltiges E-17-Urteil faellt der gate-auditor gegen die Registry; "
    "dieser Check liefert die Datenbasis."
)


def _s3_aggregate(results: dict[str, Any], strategy: str) -> tuple[Optional[float], Optional[int]]:
    """Extract (total_return, n_trades) for ``strategy`` from a results JSON."""
    agg = results.get("per_strategy_aggregate", {}).get(strategy, {})
    total_return = agg.get("total_return")
    n_trades = agg.get("total_trades")
    if total_return is None or n_trades is None:
        # Fall back to summing the per-symbol block (older/partial schema).
        per_symbol = results.get("per_symbol", {})
        rets, ns = [], []
        for sym_block in per_symbol.values():
            s = sym_block.get(strategy, {})
            if "total_return" in s:
                rets.append(float(s["total_return"]))
            if "n_trades" in s:
                ns.append(int(s["n_trades"]))
        total_return = sum(rets) if rets else None
        n_trades = sum(ns) if ns else None
    return (
        float(total_return) if total_return is not None else None,
        int(n_trades) if n_trades is not None else None,
    )


def _per_symbol_returns(results: dict[str, Any], strategy: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for symbol, block in results.get("per_symbol", {}).items():
        s = block.get(strategy, {})
        if "total_return" in s:
            out[symbol] = float(s["total_return"])
    return out


def _tail_trades(trades: list[Trade], top_n: int = TAIL_TOP_N) -> list[dict[str, Any]]:
    """The ``top_n`` largest-loss trades (by net PnL, ascending)."""
    worst = sorted(trades, key=lambda t: t.pnl_net)[:top_n]
    return [
        {
            "symbol": t.symbol,
            "entry_ts": t.entry_ts,
            "exit_ts": t.exit_ts,
            "duration_seconds": t.duration_seconds,
            "pnl_net": t.pnl_net,
            "pnl_bps": t.pnl_bps,
        }
        for t in worst
    ]


def _in_band(value: float, band: tuple[float, float]) -> bool:
    return band[0] <= value <= band[1]


def check_e17(
    results: dict[str, Any],
    trades: list[Trade],
    baseline_results: Optional[dict[str, Any]] = None,
    baseline_trades: Optional[list[Trade]] = None,
    strategy: str = STRATEGY_S3,
) -> dict[str, Any]:
    """Run the E-17 divergence check against an optional baseline run.

    Returns a JSON-serialisable dict with:

    - ``resolved``: ``True`` / ``False`` / ``"inconclusive"`` (heuristic only),
    - ``reasoning``: human-readable justification (German, report language),
    - ``details``: every number the gate-auditor needs for the final ruling.
    """
    cur_ret, cur_n = _s3_aggregate(results, strategy)
    tail = _tail_trades(trades)
    tail_sum = sum(t["pnl_net"] for t in tail)
    total_net = sum(t.pnl_net for t in trades)

    details: dict[str, Any] = {
        "registered_divergence": {
            "iter3_total_return_usd": ITER3_S3_TOTAL_RETURN_USD,
            "iter4_total_return_usd": ITER4_S3_TOTAL_RETURN_USD,
            "ratio": KNOWN_DIVERGENCE_RATIO,
        },
        "current": {"total_return": cur_ret, "n_trades": cur_n},
        "current_tail_trades_top5": tail,
        "current_tail_share_of_total_net": (
            tail_sum / total_net if total_net not in (0, 0.0) else None
        ),
        "heuristics": {
            "trades_similar_band": list(TRADES_SIMILAR_BAND),
            "return_similar_band": list(RETURN_SIMILAR_BAND),
            "explained_share_threshold": EXPLAINED_SHARE_THRESHOLD,
        },
    }

    if baseline_results is None:
        return {
            "resolved": "inconclusive",
            "reasoning": (
                "Kein Baseline-Result-Satz uebergeben (--baseline-results) — "
                "der iter-3/iter-4-Vergleich kann nicht gerechnet werden. "
                + _AUDITOR_NOTE
            ),
            "details": details,
        }

    base_ret, base_n = _s3_aggregate(baseline_results, strategy)
    details["baseline"] = {"total_return": base_ret, "n_trades": base_n}

    if cur_ret is None or base_ret is None or not cur_n or not base_n:
        return {
            "resolved": "inconclusive",
            "reasoning": (
                "Baseline oder aktueller Lauf liefert keine auswertbaren "
                f"{strategy}-Aggregate (total_return/n_trades fehlen). "
                + _AUDITOR_NOTE
            ),
            "details": details,
        }

    trades_ratio = cur_n / base_n
    abs_base = abs(base_ret)
    return_ratio = abs(cur_ret) / abs_base if abs_base > 1e-9 else float("inf")
    gap = cur_ret - base_ret
    details["trades_ratio"] = trades_ratio
    details["return_ratio_abs"] = return_ratio
    details["total_return_gap"] = gap
    details["mean_return_per_trade"] = {
        "current": cur_ret / cur_n,
        "baseline": base_ret / base_n,
    }

    # Per-symbol attribution of the gap (both result JSONs carry per_symbol).
    cur_sym = _per_symbol_returns(results, strategy)
    base_sym = _per_symbol_returns(baseline_results, strategy)
    sym_gaps = {
        s: cur_sym.get(s, 0.0) - base_sym.get(s, 0.0)
        for s in sorted(set(cur_sym) | set(base_sym))
    }
    details["per_symbol_return_gap"] = sym_gaps
    abs_gap_total = sum(abs(g) for g in sym_gaps.values())
    top_symbol, top_share = None, 0.0
    if abs_gap_total > 1e-9:
        top_symbol = max(sym_gaps, key=lambda s: abs(sym_gaps[s]))
        top_share = abs(sym_gaps[top_symbol]) / abs_gap_total
    details["top_gap_symbol"] = {"symbol": top_symbol, "share_of_abs_gap": top_share}

    # Tail attribution: how much of the gap do the largest losses move?
    tail_gap_share: Optional[float] = None
    if baseline_trades:
        base_tail = _tail_trades(baseline_trades)
        details["baseline_tail_trades_top5"] = base_tail
        tail_gap = tail_sum - sum(t["pnl_net"] for t in base_tail)
        tail_gap_share = abs(tail_gap) / abs(gap) if abs(gap) > 1e-9 else None
        details["tail_gap_share"] = tail_gap_share

    trades_similar = _in_band(trades_ratio, TRADES_SIMILAR_BAND)
    returns_similar = _in_band(return_ratio, RETURN_SIMILAR_BAND)

    if trades_similar and returns_similar:
        return {
            "resolved": True,
            "reasoning": (
                f"Aktueller Lauf und Baseline sind konsistent: n_trades-Ratio "
                f"{trades_ratio:.2f} (Band {TRADES_SIMILAR_BAND}), "
                f"|total_return|-Ratio {return_ratio:.2f} (Band "
                f"{RETURN_SIMILAR_BAND}). Die registrierte ~3.2x-Divergenz "
                f"reproduziert sich nicht. " + _AUDITOR_NOTE
            ),
            "details": details,
        }

    if trades_similar:
        # Same trade count, divergent return — the E-17 pattern. Try to
        # attribute it: single-symbol concentration or tail trades.
        if top_symbol is not None and top_share >= EXPLAINED_SHARE_THRESHOLD:
            return {
                "resolved": True,
                "reasoning": (
                    f"Return-Divergenz (Ratio {return_ratio:.2f}) bei "
                    f"aehnlicher Trade-Zahl (Ratio {trades_ratio:.2f}) ist zu "
                    f"{top_share:.0%} auf {top_symbol} konzentriert "
                    f"(Gap {sym_gaps[top_symbol]:+.2f} USD von {gap:+.2f} USD "
                    f"gesamt) — d.h. Notional-/Symbol-Skalierung, kein "
                    f"breiter Edge-Unterschied. " + _AUDITOR_NOTE
                ),
                "details": details,
            }
        if tail_gap_share is not None and tail_gap_share >= EXPLAINED_SHARE_THRESHOLD:
            return {
                "resolved": True,
                "reasoning": (
                    f"Return-Divergenz (Ratio {return_ratio:.2f}) bei "
                    f"aehnlicher Trade-Zahl wird zu {tail_gap_share:.0%} durch "
                    f"die Top-{TAIL_TOP_N}-Tail-Trades beider Laeufe erklaert "
                    f"(siehe details.current/baseline_tail_trades_top5). "
                    + _AUDITOR_NOTE
                ),
                "details": details,
            }
        return {
            "resolved": False,
            "reasoning": (
                f"Return-Divergenz (Ratio {return_ratio:.2f}) bei aehnlicher "
                f"Trade-Zahl (Ratio {trades_ratio:.2f}) ist weder durch "
                f"Symbol-Konzentration (Top-Anteil {top_share:.0%} < "
                f"{EXPLAINED_SHARE_THRESHOLD:.0%}) noch durch Tail-Trades "
                f"erklaerbar — E-17-Muster reproduziert und ungeklaert. "
                + _AUDITOR_NOTE
            ),
            "details": details,
        }

    # Trade counts differ materially: check whether per-trade economics match.
    mean_cur = cur_ret / cur_n
    mean_base = base_ret / base_n
    mean_ratio = (
        abs(mean_cur) / abs(mean_base) if abs(mean_base) > 1e-9 else float("inf")
    )
    details["mean_return_per_trade_ratio_abs"] = mean_ratio
    if _in_band(mean_ratio, RETURN_SIMILAR_BAND):
        return {
            "resolved": True,
            "reasoning": (
                f"Trade-Zahlen unterscheiden sich (Ratio {trades_ratio:.2f}), "
                f"aber der mittlere Return pro Trade ist konsistent (Ratio "
                f"{mean_ratio:.2f}) — Divergenz im total_return ist durch die "
                f"Trade-Zahl erklaert. " + _AUDITOR_NOTE
            ),
            "details": details,
        }
    return {
        "resolved": False,
        "reasoning": (
            f"Sowohl Trade-Zahl (Ratio {trades_ratio:.2f}) als auch Return "
            f"pro Trade (Ratio {mean_ratio:.2f}) divergieren — nicht durch "
            f"einfache Skalierung erklaerbar. " + _AUDITOR_NOTE
        ),
        "details": details,
    }
