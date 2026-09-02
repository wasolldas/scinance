"""WP-7 -- Befund B1..B5 mit vorab fixierter Konsequenz (PRD 4.1, woertlich).

Every consequence string below is copied VERBATIM from the PRD 4.1
Befund-Tabelle -- this module decides only WHICH row applies, never what
it says. JSON + Markdown output, no verdict beyond what the table already
fixes (a binary finding, per section 1 of the spec: "kein Alpha-Gate,
binaerer Befund").
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import stats

__all__ = [
    "B1_CONSEQUENCE", "B2_CONSEQUENCE", "B3_CONSEQUENCE", "B4_CONSEQUENCE",
    "B5_CONSEQUENCE", "K_MIN_PER_WINDOW", "K_MIN_POOLED", "N_EFF_LABEL",
    "evaluate_b1_b2", "evaluate_b3", "evaluate_b4", "evaluate_b5",
    "assemble_report", "write_report",
]

#: Notwendige (nicht hinreichende) Breitenbedingungen (PRD 4.1).
K_MIN_PER_WINDOW = 134
K_MIN_POOLED = 117

#: Every report that carries an N_eff figure MUST use this exact label
#: (coordinator Abnahme-Nacharbeit): it is a Ledoit-Wolf-SHRUNK, DESCRIPTIVE
#: estimate (see ``stats.n_eff`` / ``stats._ledoit_wolf_identity_corr``) --
#: never a gate, never a verdict, and the label says so at every surface
#: a human reads it (JSON key AND Markdown heading), not just in a docstring.
N_EFF_LABEL = "N_eff (Ledoit-Wolf-geschrumpft, deskriptiv, kein Urteil)"

B1_CONSEQUENCE = (
    "Klasse W ist statistisch nicht testbar. Keine Registrierung von A3 "
    "und keine Registrierung des Querschnitts-Arms von A1. Nie auf N=5 "
    "zurueckskalieren - das waere D.7/H-07 zum zweiten Mal. Rein "
    "statistischer Ausloeser, keine Kostenzahl (C.2).")

B2_CONSEQUENCE = (
    "Klasse W testbar. A3-Registrierung erlaubt; welches Fenster-Regime "
    "gilt, entscheidet die gerechnete Per-Fenster-Power nach der in 5.3 "
    "vorab fixierten Zuordnungsregel.")

B3_CONSEQUENCE = (
    "Kein Survivorship-freies Universum aus Bybit-Bordmitteln. Konsequenz "
    "vorab: Klasse W laeuft nur, wenn das Survivorship-Fixture eine "
    "Verzerrung kleiner als die halbe registrierte Schwelle zeigt; sonst "
    "nicht registrierbar. Externes Delisting-Register (Announcement-"
    "Scraping) ist keine Welle-1-Aufgabe.")

B4_CONSEQUENCE = (
    "Konsequenz ausschliesslich: alle Klasse-W-Kandidaten tragen das "
    "Etikett unter_wand. Keine Streichung, kein DROP, keine Aenderung "
    "einer PASS-Bedingung (C.2, Review PRD3 2.1(iii)). Der Befund ist "
    "eine Tradability-Information, kein Mess-Verdikt.")

B5_CONSEQUENCE = (
    "Ergebnis wird als DEC registriert, bevor ein Kandidat davon "
    "profitiert (Review R1-R4 3.6). Bis dahin RAISED tradability3.perp "
    "(Par. 6). Klarstellung (Review PRD3 W-8): 15 bps ist die Gesamtwand "
    "(11 bp Gebuehr + ~4 bp Slippage), nicht eine 'Majors-Slippage-"
    "Konstante'; eine Spread-Messung korrigiert die Konstante um "
    "hoechstens ~27% und kann sie nie unter 11 bps Taker druecken "
    "(Review R1-R4 1-R3-K-35, woertlich). Ein Schwellenwert fuer "
    "'Alt-Spread zu breit' wird deshalb nicht gesetzt - der v1-Faktor 3x "
    "war unhergeleitet und ist gestrichen.")


def evaluate_b1_b2(sd_null_per_window: float, sd_null_pooled: float,
                    k_available: int) -> dict[str, Any]:
    """B1 (nicht testbar) vs. B2 (testbar) -- both branches evaluated
    against the SAME measured ``K``/``SD_null``; B1 fires only if NEITHER
    regime clears its bar."""
    per_window_ok = (k_available >= K_MIN_PER_WINDOW
                      and sd_null_per_window <= stats.sd_null_threshold(pooled=False))
    pooled_ok = (k_available >= K_MIN_POOLED
                 and sd_null_pooled <= stats.sd_null_threshold(pooled=True))
    testable = per_window_ok or pooled_ok
    return {
        "finding": "B2" if testable else "B1",
        "consequence": B2_CONSEQUENCE if testable else B1_CONSEQUENCE,
        "per_window_feasible": per_window_ok, "pooled_feasible": pooled_ok,
        "k_available": k_available,
        "sd_null_per_window": sd_null_per_window,
        "sd_null_threshold_per_window": stats.sd_null_threshold(pooled=False),
        "sd_null_pooled": sd_null_pooled,
        "sd_null_threshold_pooled": stats.sd_null_threshold(pooled=True),
    }


def evaluate_b3(instruments_statuses: list[str], delisted_symbols_with_kline: int,
                 delisted_symbols_checked: int) -> dict[str, Any]:
    """B3 fires if ``instruments-info`` returns no non-Trading row, OR
    every checked delisted symbol comes back with zero kline history."""
    no_non_trading = all(s == "Trading" for s in instruments_statuses)
    no_delisted_history = (delisted_symbols_checked > 0
                            and delisted_symbols_with_kline == 0)
    triggered = no_non_trading or no_delisted_history
    return {"finding": "B3" if triggered else None,
            "triggered": triggered,
            "consequence": B3_CONSEQUENCE if triggered else None,
            "no_non_trading_rows": no_non_trading,
            "no_delisted_kline_history": no_delisted_history,
            "delisted_symbols_checked": delisted_symbols_checked,
            "delisted_symbols_with_kline": delisted_symbols_with_kline}


def evaluate_b4(sigma_xs_measured_bps: float, *, cost_bps: float,
                 f: float = stats.DECILE_FACTOR,
                 ic_prior: float = stats.IC_PRIOR) -> dict[str, Any]:
    threshold = stats.sigma_xs_min_bps(cost_bps, f=f, ic_prior=ic_prior)
    triggered = sigma_xs_measured_bps < threshold
    return {"finding": "B4" if triggered else None, "triggered": triggered,
            "consequence": B4_CONSEQUENCE if triggered else None,
            "sigma_xs_measured_bps": sigma_xs_measured_bps,
            "sigma_xs_min_bps": threshold, "cost_bps": cost_bps, "f": f}


def evaluate_b5(perp_spread_deciles: list[dict[str, Any]]) -> dict[str, Any]:
    """B5 is unconditional once the census ran: measuring
    ``PERP_SPREAD_BP`` per decile IS the finding (informational DEC)."""
    return {"finding": "B5", "consequence": B5_CONSEQUENCE,
            "deciles": perp_spread_deciles}


def assemble_report(*, b1_b2: dict[str, Any], b3: dict[str, Any],
                     b4: dict[str, Any], b5: dict[str, Any],
                     n_eff: dict[str, Any] | None = None,
                     pair_corr_btc_eth: dict[str, Any] | None = None,
                     extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assemble the JSON report. ``n_eff`` (optional, from ``stats.n_eff``)
    is always stored under the exact ``N_EFF_LABEL`` -- coordinator
    Abnahme-Nacharbeit: the shrinkage + "descriptive, no verdict" caveat
    must be visible at the report surface, not just in code comments.
    ``pair_corr_btc_eth`` (optional, from ``pair_corr.compute_pair_correlation``)
    carries the measured 30-minute rho(BTC,ETH) (PRD 4.1 section 1)."""
    payload: dict[str, Any] = {
        "wp": "WP-7", "findings": {"b1_b2": b1_b2, "b3": b3, "b4": b4, "b5": b5},
        "extra": extra or {},
    }
    if n_eff is not None:
        payload["n_eff"] = {"label": N_EFF_LABEL, **n_eff}
    if pair_corr_btc_eth is not None:
        payload["pair_corr_btc_eth"] = pair_corr_btc_eth
    return payload


def _to_markdown(report: dict[str, Any]) -> str:
    b12, b3, b4, b5 = (report["findings"][k] for k in ("b1_b2", "b3", "b4", "b5"))
    lines = ["# WP-7 -- Universums-Zensus: Befund", "",
             f"## {b12['finding']}", b12["consequence"], "",
             "SD_null-Schranke = IC_prior * sqrt(W) / z (DEC-51/52):", "",
             f"- SD_null je Fenster: {b12['sd_null_per_window']:.5f} "
             f"(Schranke {b12['sd_null_threshold_per_window']:.5f}, "
             f"aus IC_prior={stats.IC_PRIOR} * sqrt(W={stats.W_PER_WINDOW}) / "
             f"z={stats.Z_PER_WINDOW})",
             f"- SD_null gepoolt: {b12['sd_null_pooled']:.5f} "
             f"(Schranke {b12['sd_null_threshold_pooled']:.5f}, "
             f"aus IC_prior={stats.IC_PRIOR} * sqrt(W={stats.W_POOLED}) / "
             f"z={stats.Z_POOLED})",
             f"- K verfuegbar: {b12['k_available']}", ""]
    lines += ["## B3" if b3["triggered"] else "## B3 (nicht ausgeloest)",
              b3["consequence"] or "kein Befund -- Survivorship-freies Universum vorhanden.", ""]
    lines += ["## B4" if b4["triggered"] else "## B4 (nicht ausgeloest)",
              b4["consequence"] or "kein Befund -- sigma_xs erreicht sigma_xs_min.", ""]
    lines += ["## B5", b5["consequence"], ""]
    for d in b5["deciles"]:
        lines.append(f"- Dezil {d['decile']}: n={d['n_symbols']} "
                      f"PERP_SPREAD_BP median={d['perp_spread_bp_median']}")
    lines.append("")
    if "n_eff" in report:
        ne = report["n_eff"]
        lines += [f"## {ne['label']}",
                  f"- Wert: {ne['n_eff']:.2f} "
                  f"(n_symbols_balanced={ne.get('n_symbols_balanced')})", ""]
    if "pair_corr_btc_eth" in report:
        pc = report["pair_corr_btc_eth"]
        lines += ["## rho(BTC,ETH), 30-Minuten-Renditen",
                  f"- Pearson: {pc['pearson']['point']:.4f} "
                  f"[{pc['pearson']['ci_lo']:.4f}, {pc['pearson']['ci_hi']:.4f}] "
                  f"(seed={pc['seed']})",
                  f"- Spearman: {pc['spearman']['point']:.4f} "
                  f"[{pc['spearman']['ci_lo']:.4f}, {pc['spearman']['ci_hi']:.4f}]",
                  f"- n_aligned_buckets: {pc['n_aligned_buckets']}", ""]
    return "\n".join(lines) + "\n"


def write_report(out_dir: Path | str, report: dict[str, Any]) -> dict[str, str]:
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write report under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "wp7_report.json"
    md_path = out_dir / "wp7_report.md"
    json_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    md_path.write_text(_to_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path)}
