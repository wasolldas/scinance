"""Machine evaluation of the pre-registered H-01 gate (E-15 / S3 iter-5).

Gate posts, LITERALLY from ``scinance2-impl/state/hypothesis_registry.md``
(H-01, registered 2026-06-10, frozen — no post-hoc adjustment):

- time_stop_exceeded-Count: 1 -> erwartet ~60-70 (Fix-Wirksamkeit)
- n>120s-Trades: 68 -> erwartet ~0
- n<-30bps-Trades: 33 -> erwartet ~0
- WEITER:      aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert
- DROP:        aggregierte Netto-Edge <= -10 bps
- GRAUBEREICH: dazwischen -> ein (1) weiteres vorregistriertes Fenster

Operationalisation choices made by the builder (documented per criterion in
``gate_details`` and in the report):

- "~60-70" is checked as the closed interval [54, 77] (= 60/70 +- 10%).
- "~0" is checked as count <= 2 (tick-granularity grace: a working 120 s
  time-stop exits on the FIRST tick after the limit, so a handful of trades
  may measure marginally above 120 s).
- The three fix-effectiveness expectations are reported as pass/fail but do
  NOT flip the verdict — the registered WEITER/DROP/GRAUBEREICH thresholds
  reference only the aggregate net edge and the E-17 clarification.
- "E-17 geklaert" counts as satisfied only when the E-17 check returns
  ``resolved is True`` (``False``/``inconclusive`` both block WEITER).
"""
from __future__ import annotations

from typing import Any, Optional

VERDICT_WEITER = "WEITER"
VERDICT_DROP = "DROP"
VERDICT_GRAUBEREICH = "GRAUBEREICH"

#: Registered thresholds (H-01, literal).
WEITER_NET_EDGE_MIN_BPS = -5.0
DROP_NET_EDGE_MAX_BPS = -10.0
TIME_STOP_EXPECTED_RANGE = (60, 70)

#: Builder operationalisation of "~" / "~0" (see module docstring).
TIME_STOP_TILDE_TOLERANCE = 0.10
TIME_STOP_PASS_RANGE = (
    int(TIME_STOP_EXPECTED_RANGE[0] * (1.0 - TIME_STOP_TILDE_TOLERANCE)),  # 54
    int(TIME_STOP_EXPECTED_RANGE[1] * (1.0 + TIME_STOP_TILDE_TOLERANCE)),  # 77
)
APPROX_ZERO_MAX_COUNT = 2


def _criterion(
    criterion_id: str,
    registry_text: str,
    operationalisation: str,
    measured: Any,
    passed: Optional[bool],
) -> dict[str, Any]:
    return {
        "id": criterion_id,
        "registry_text": registry_text,
        "operationalisation": operationalisation,
        "measured": measured,
        "passed": passed,
    }


def evaluate_h01_gate(
    aggregate: dict[str, Any], e17_resolved: Any
) -> dict[str, Any]:
    """Evaluate the aggregate S3 metrics against the H-01 gate.

    Parameters
    ----------
    aggregate:
        The ``aggregate`` block from :func:`metrics.compute_e15_metrics`.
    e17_resolved:
        ``True`` / ``False`` / ``"inconclusive"`` from :func:`e17.check_e17`.

    Returns a dict with ``gate_verdict`` (WEITER | DROP | GRAUBEREICH) and
    ``gate_details`` (one entry per registered criterion).
    """
    net_edge: float = float(aggregate["mean_pnl_bps_net"])
    ts_count: Optional[int] = aggregate.get("time_stop_exceeded_count")
    n_over_120s: int = int(aggregate["n_over_120s"])
    n_tail: int = int(aggregate["n_below_minus_30bps"])
    e17_ok = e17_resolved is True

    details: list[dict[str, Any]] = []

    # --- Fix-effectiveness expectations (reported, non-verdict-flipping) ----
    details.append(
        _criterion(
            "fix_time_stop_count",
            "time_stop_exceeded-Count: 1 -> erwartet ~60-70 (Fix-Wirksamkeit)",
            f"pass wenn Count in [{TIME_STOP_PASS_RANGE[0]}, "
            f"{TIME_STOP_PASS_RANGE[1]}] (= 60-70 +-10% fuer '~'); "
            "None wenn diagnostics fehlen",
            ts_count,
            None
            if ts_count is None
            else (TIME_STOP_PASS_RANGE[0] <= ts_count <= TIME_STOP_PASS_RANGE[1]),
        )
    )
    details.append(
        _criterion(
            "fix_n_over_120s",
            "n>120s-Trades: 68 -> erwartet ~0",
            f"pass wenn Count <= {APPROX_ZERO_MAX_COUNT} ('~0' mit "
            "Tick-Granularitaets-Toleranz: Time-Stop feuert erst auf dem "
            "ersten Tick NACH 120s)",
            n_over_120s,
            n_over_120s <= APPROX_ZERO_MAX_COUNT,
        )
    )
    details.append(
        _criterion(
            "fix_n_below_minus_30bps",
            "n<-30bps-Trades: 33 -> erwartet ~0",
            f"pass wenn Count <= {APPROX_ZERO_MAX_COUNT} ('~0')",
            n_tail,
            n_tail <= APPROX_ZERO_MAX_COUNT,
        )
    )

    fix_passes = [d["passed"] for d in details]
    fix_effectiveness_pass: Optional[bool] = (
        None if any(p is None for p in fix_passes) else all(fix_passes)
    )

    # --- Verdict-bearing criteria -------------------------------------------
    weiter_edge_ok = net_edge >= WEITER_NET_EDGE_MIN_BPS
    drop_edge = net_edge <= DROP_NET_EDGE_MAX_BPS
    details.append(
        _criterion(
            "weiter_net_edge",
            "WEITER: aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert",
            "Teilkriterium 1: mean pnl_bps (netto, trade-gewichtet ueber alle "
            f"S3-Trades) >= {WEITER_NET_EDGE_MIN_BPS}",
            net_edge,
            weiter_edge_ok,
        )
    )
    details.append(
        _criterion(
            "weiter_e17_resolved",
            "WEITER: aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert",
            "Teilkriterium 2: E-17-Check resolved == true (false/inconclusive "
            "blockieren WEITER)",
            e17_resolved if isinstance(e17_resolved, str) else bool(e17_resolved),
            e17_ok,
        )
    )
    details.append(
        _criterion(
            "drop_net_edge",
            "DROP: aggregierte Netto-Edge <= -10 bps",
            f"DROP wenn mean pnl_bps (netto) <= {DROP_NET_EDGE_MAX_BPS}",
            net_edge,
            drop_edge,  # passed == True means the DROP condition fires
        )
    )

    if drop_edge:
        verdict = VERDICT_DROP
    elif weiter_edge_ok and e17_ok:
        verdict = VERDICT_WEITER
    else:
        # Between the posts, or net edge fine but E-17 not clarified:
        # registered fallback is GRAUBEREICH (one further pre-registered
        # window, then final — registry rule 7).
        verdict = VERDICT_GRAUBEREICH

    return {
        "gate_verdict": verdict,
        "gate_details": details,
        "fix_effectiveness_pass": fix_effectiveness_pass,
        "aggregate_net_edge_bps": net_edge,
    }
