"""H-13 orchestration: unlock check, per-cell xi_P/xi_Q, F-TAILSHAPE rollup.

Gate-neutral by construction: the payload carries every registered criterion
as a precomputed flag plus a ``data_gated`` flag, but the WEITER/DROP verdict
belongs to the gate-auditor (registry H-13). KAPITALFREI: pure
measurement/consistency question — no cost or return accounting anywhere
(a tail/skew trading consequence would be a NEW H-13b, explicitly NOT implied
by this module; crypto option quote widths make that a separate registered
question in any case).

Symbol convention: gate symbols are the Deribit underlyings (``BTC``/``ETH``);
the returns side maps them to the Bybit perps (``BTCUSDT``/``ETHUSDT``).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .options_loader import DELTA_BAND, MIN_STRIKES, TENOR_DTE, load_smile
from .returns_tail import (
    BLOCK_LEN_MIN,
    DataError,
    POT_QUANTILE,
    TRAILING_DAYS,
    estimate_xi_p,
    load_returns_window,
)
from .snapshot_selection import (
    LOG_RV_RATIO_MIN,
    MIN_GAP_DAYS,
    RV_WINDOW_DAYS,
    SelectionResult,
    scan_and_select,
)
from .stats import (
    BOOTSTRAP_P_MAX,
    DELTA_XI_FLOOR,
    FDR_ALPHA,
    combined_bootstrap_p,
    evaluate_gate,
    hill_contradicts,
)
from .svi_rnd import TAIL_ALPHA, RndError, estimate_xi_q

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-13"
FDR_FAMILY = "F-TAILSHAPE"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"

#: Deribit underlying -> Bybit perp symbol for the returns side.
PERP_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}

UNLOCK_CONDITION = (
    "2 vol-regime-disjoint live IV snapshot days D1<D2: "
    "|log(RV_5d(D1)/RV_5d(D2))| >= log(1.5), >= 10 calendar days apart, "
    f">= {MIN_STRIKES} strikes with {DELTA_BAND[0]} <= |delta| <= {DELTA_BAND[1]} "
    f"in the {TENOR_DTE[0]}-{TENOR_DTE[1]} DTE tenor per day/symbol"
)


def _perp_for(symbol: str) -> str:
    return PERP_MAP.get(symbol, f"{symbol}USDT")


def check_unlock(
    base_dir: Path | str,
    symbols: tuple[str, ...] = ("BTC", "ETH"),
    *,
    snapshot_hour: int = 8,
) -> dict[str, Any]:
    """Programmatic D1/D2 search per symbol (the H-13 unlock condition).

    ``unlocked`` is True iff AT LEAST ONE symbol has a valid (D1, D2) pair —
    the registered gate itself only requires >= 1 symbol in {BTC, ETH};
    symbols without a valid pair are simply not measured (their cells are
    absent from the F-TAILSHAPE family).
    """
    selections: dict[str, SelectionResult] = {}
    for sym in symbols:
        selections[sym] = scan_and_select(
            base_dir, sym, _perp_for(sym), snapshot_hour=snapshot_hour,
        )
        s = selections[sym]
        print(
            f"[h13] unlock {sym}: found={s.found} d1={s.d1} d2={s.d2}"
            + (f" reason={s.reason}" if not s.found else ""),
            file=sys.stderr, flush=True,
        )
    return {
        "unlocked": bool(any(s.found for s in selections.values())),
        "unlock_condition": UNLOCK_CONDITION,
        "selection": {sym: s.as_dict() for sym, s in selections.items()},
        "_selections": selections,  # internal, stripped before serialisation
    }


def _measure_cell(
    base_dir: Path | str,
    symbol: str,
    day_label: str,
    date_str: str,
    *,
    n_bootstrap: int,
    seed: int,
    trailing_days: int,
    snapshot_hour: int,
) -> dict[str, Any]:
    """One F-TAILSHAPE cell: xi_P vs xi_Q at (symbol, snapshot day)."""
    returns, r_meta = load_returns_window(
        base_dir, _perp_for(symbol), date_str, n_days=trailing_days,
    )
    xi_p = estimate_xi_p(returns, n_bootstrap=n_bootstrap, seed=seed)
    smile = load_smile(base_dir, symbol, date_str, snapshot_hour=snapshot_hour)
    if smile is None or smile.n_strikes < MIN_STRIKES:
        n = 0 if smile is None else smile.n_strikes
        raise DataError(
            f"{symbol}@{date_str}: smile has {n} strikes (< {MIN_STRIKES}) "
            f"despite passing selection — data changed underfoot?"
        )
    xi_q = estimate_xi_q(
        smile.strikes, smile.ivs, smile.forward, smile.t_years,
        n_bootstrap=n_bootstrap, seed=seed + 1,
    )
    delta_xi = float(xi_p.xi - xi_q.xi)
    p_value, n_comb = combined_bootstrap_p(xi_p.xi_boot, xi_q.xi_boot, delta_xi)
    return {
        "symbol": symbol,
        "day_label": day_label,
        "snapshot_date": date_str,
        "xi_p": float(xi_p.xi),
        "xi_q": float(xi_q.xi),
        "delta_xi": delta_xi,
        "p_value": float(p_value),
        "n_combined_bootstrap": int(n_comb),
        "hill_contradiction": hill_contradicts(delta_xi, xi_p.xi_hill, xi_q.xi),
        "returns_side": {**xi_p.as_dict(), **r_meta},
        "options_side": {**xi_q.as_dict(), **smile.as_dict()},
    }


def run(
    base_dir: Path | str,
    symbols: tuple[str, ...] = ("BTC", "ETH"),
    *,
    n_bootstrap: int = 500,
    seed: int = 42,
    trailing_days: int = TRAILING_DAYS,
    snapshot_hour: int = 8,
    source: str = "",
) -> dict[str, Any]:
    """Full H-13 run: unlock search, per-cell measurement, F-TAILSHAPE rollup.

    Gate-neutral payload. If the unlock condition fails for ALL symbols the
    payload carries ``skip=True`` (the hypothesis stays LOCKED, nothing is
    measured — the T2 runner reports a clean SKIP).
    """
    unlock = check_unlock(base_dir, symbols, snapshot_hour=snapshot_hour)
    selections: dict[str, SelectionResult] = unlock.pop("_selections")

    base_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "data_gated": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "n_bootstrap": int(n_bootstrap),
        "seed": int(seed),
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "unlock": unlock,
        "methodology": {
            "pot_quantile": POT_QUANTILE,
            "trailing_days": int(trailing_days),
            "block_len_min": BLOCK_LEN_MIN,
            "tenor_dte": list(TENOR_DTE),
            "delta_band": list(DELTA_BAND),
            "rnd_tail_alpha": TAIL_ALPHA,
            "min_strikes": MIN_STRIKES,
            "min_gap_days": MIN_GAP_DAYS,
            "log_rv_ratio_min": LOG_RV_RATIO_MIN,
            "rv_window_days": RV_WINDOW_DAYS,
            "delta_xi_floor": DELTA_XI_FLOOR,
            "bootstrap_p_max": BOOTSTRAP_P_MAX,
        },
    }

    if not unlock["unlocked"]:
        return {
            **base_payload,
            "skip": True,
            "skip_reason": (
                "H-13 locked — no 2 vol-regime-disjoint snapshot days found "
                "in the live window (unlock condition unmet for all symbols)"
            ),
            "cells": [],
            "gate": None,
        }

    cells: list[dict[str, Any]] = []
    cell_errors: list[dict[str, str]] = []
    for sym in symbols:
        sel = selections[sym]
        if not sel.found:
            continue
        for day_label, date_str in (("D1", sel.d1), ("D2", sel.d2)):
            try:
                cells.append(_measure_cell(
                    base_dir, sym, day_label, date_str,
                    n_bootstrap=n_bootstrap, seed=seed,
                    trailing_days=trailing_days, snapshot_hour=snapshot_hour,
                ))
            except (DataError, RndError) as exc:
                print(f"[h13] cell {sym}/{day_label}@{date_str} failed: {exc}",
                      file=sys.stderr, flush=True)
                cell_errors.append({
                    "symbol": sym, "day_label": day_label,
                    "snapshot_date": str(date_str), "error": str(exc),
                })

    gate = evaluate_gate(cells) if cells else None
    return {
        **base_payload,
        "skip": False,
        "cells": cells,
        "cell_errors": cell_errors,
        "gate": gate,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    """German gate-neutral report (repo convention: reports in German)."""
    L: list[str] = []
    L.append("# C-13 Tail-Form-Konsistenz xi_P vs. xi_Q — H-13 Mess-Gate (KAPITALFREI, data-gated)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    m = payload["methodology"]
    L.append(f"- **Methodik (vorregistriert):** POT u_P = {m['pot_quantile']:.3%}-Quantil der "
             f"1-min-Verluste ueber trailing {m['trailing_days']} Tage, GPD-MLE, "
             f"Block-Bootstrap ({m['block_len_min']}-min-Bloecke, {payload['n_bootstrap']} Reps), "
             f"Hill-Gegenprobe; xi_Q: SVI -> Breeden-Litzenberger-RND -> GPD-PWM unterhalb "
             f"{m['rnd_tail_alpha']:.0%}-RND-Quantil, Strike-Bootstrap; Tenor "
             f"{m['tenor_dte'][0]}-{m['tenor_dte'][1]} DTE, Delta-Band "
             f"{m['delta_band'][0]}-{m['delta_band'][1]}; Seed {payload['seed']}.")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} · BH-FDR alpha = {payload['fdr_alpha']}")
    L.append("- **KAPITALFREI:** ja — reine Mess-/Konsistenzfrage, keine Kosten-/Ertragsrechnung.")
    L.append(f"- **DATA-GATED:** ja — Entsperr-Bedingung: {payload['unlock']['unlock_condition']}")
    L.append("")
    L.append("## Entsperr-Pruefung (deterministische D1/D2-Suche)")
    L.append("")
    L.append("| Symbol | gefunden | D1 | D2 | Grund (falls nicht) |")
    L.append("|---|---|---|---|---|")
    for sym, sel in payload["unlock"]["selection"].items():
        L.append(f"| {sym} | {'JA' if sel['found'] else 'nein'} | {sel['d1'] or '—'} | "
                 f"{sel['d2'] or '—'} | {sel['reason'] or '—'} |")
    L.append("")
    if payload.get("skip"):
        L.append(f"**SKIP:** {payload['skip_reason']}")
        L.append("")
        L.append("*H-13 bleibt GESPERRT; kein Fit, kein Gate-Urteil. "
                 "Schwelle waechst mit Kalenderzeit, wird NICHT gesenkt.*")
        return "\n".join(L)
    L.append("## F-TAILSHAPE-Zellen (Symbol x Snapshot-Tag)")
    L.append("")
    L.append("| Symbol | Tag | Datum | xi_P | xi_Q | Delta_xi | p (komb. Bootstrap) | "
             "FDR-sig | \\|Delta\\|>=0.15 | Hill-Widerspruch | Zelle ok |")
    L.append("|---|---|---|---:|---:|---:|---:|:---:|:---:|:---:|:---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['symbol']} | {c['day_label']} | {c['snapshot_date']} | "
            f"{c['xi_p']:+.4f} | {c['xi_q']:+.4f} | {c['delta_xi']:+.4f} | "
            f"{c['p_value']:.4f} | {'ja' if c.get('fdr_significant') else 'nein'} | "
            f"{'ja' if c.get('delta_floor_met') else 'nein'} | "
            f"{'JA' if c.get('hill_contradiction') else 'nein'} | "
            f"{'JA' if c.get('cell_criteria_met') else 'nein'} |"
        )
    g = payload.get("gate") or {}
    L.append("")
    L.append("## Gate-Kern je Symbol (gate-neutral — gate-auditor urteilt)")
    L.append("")
    L.append("| Symbol | beide Tage | sign konsistent | alle Zell-Kriterien | Symbol-Gate |")
    L.append("|---|:---:|:---:|:---:|:---:|")
    for sym, v in (g.get("per_symbol") or {}).items():
        L.append(f"| {sym} | {'ja' if v['both_days_measured'] else 'nein'} | "
                 f"{'ja' if v['sign_consistent'] else 'nein'} | "
                 f"{'ja' if v['all_cell_criteria_met'] else 'nein'} | "
                 f"{'JA' if v['symbol_gate_met'] else 'nein'} |")
    L.append("")
    L.append(f"**p_crit (BH-FDR):** {g.get('fdr_p_crit', 0.0):.4f} · "
             f"**FDR-signifikante Zellen:** {g.get('n_fdr_significant', 0)} · "
             f"**mind. ein Symbol-Gate erfuellt:** "
             f"{'ja' if g.get('any_symbol_gate_met') else 'nein'}")
    if payload.get("cell_errors"):
        L.append("")
        L.append("## Zell-Fehler")
        for e in payload["cell_errors"]:
            L.append(f"- {e['symbol']}/{e['day_label']}@{e['snapshot_date']}: {e['error']}")
    L.append("")
    L.append("*Erzeugt von `c13_tailshape/driver.py` (read-only Harvester-Baum). "
             "capital_free=true, data_gated=true. WEITER verlangt (registriert, woertlich): "
             "fuer >=1 Symbol an BEIDEN Tagen sign(Delta_xi) identisch UND |Delta_xi|>=0.15 "
             "UND Bootstrap-p<=0.05 nach BH-FDR alpha=0.10 ueber F-TAILSHAPE UND "
             "Hill-Gegenprobe widerspricht nicht. Hartes Ein-Fenster-/Ein-Tag-DROP sonst. "
             "Endgueltiges Urteil: gate-auditor gegen H-13.*")
    return "\n".join(L)
