"""DEC-101 E1 (V-1 (a)): the H-32 universe = the linear USDT perpetuals.

The survivors tree of the Data-Harvest export (``instruments-info?category=linear``) carries, next to the linear USDT
perpetuals, 68 USDC perpetuals (``*PERP``, each with a USDT twin of the same base asset) and 48 dated USDT futures
(``*-DDMMMYY``); the delisted tree selects ``quoteCoin USDT`` only.  Twins have almost identical ranks in characteristic and
fm8 outcome while the factor-preserving null simulates every column independently, so the null SD of the weekly IC is too
small (Review B-1).  DEC-101 E1 fixes the universe symmetrically to the delisted-tree selection: a symbol is in the
universe iff it ends on ``USDT`` and contains no ``-``.

The filter is **additive**, runs in the driver AFTER the fingerprints were measured on the files (the fingerprints stay
file-based) and BEFORE the panel cut and any calculation, in ALL modes.  Label (mandatory): "Bereinigung (Strenge),
beschlossen nach Kenntnis der v6-Nuisance, vor jeder Pilot-Zahl" -- the direction is strictness (the null SD does not grow
through twins, K shrinks).

Relisting episodes: the union panel names the earlier episode of a relisted symbol ``<symbol>#delisted`` (DEC-72); the rule
looks at the name in front of the suffix, so that an episode column of a linear USDT perpetual is not dropped by accident.
"""
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from . import constants as C
from .errors import UniverseError

__all__ = ["is_linear_usdt_perpetual", "classify_excluded", "apply_universe", "assert_universe", "ensure_universe",
           "excluded_sha256", "universe_log_line"]

#: arrays of the union panel whose second axis is the symbol axis (``panel_cut`` treats the same keys).
_SYMBOL_ARRAY_KEYS = ("close", "turnover", "funding_n", "funding_sum")
#: lists of symbol names in the union panel.
_SYMBOL_NAME_LISTS = ("delisted_symbols", "relisted_symbols", "fresh_delisted_symbols")


def _contract_name(symbol: str) -> str:
    """The contract name in front of the relisting-episode suffix."""
    return str(symbol).split("#", 1)[0]


def is_linear_usdt_perpetual(symbol: str) -> bool:
    """DEC-101 E1: ``True`` iff the contract name ends on ``USDT`` and contains no ``-``."""
    name = _contract_name(symbol)
    return name.endswith("USDT") and "-" not in name


def classify_excluded(symbol: str) -> str:
    """Class of a symbol that is NOT in the universe: ``"usdc_perp"`` (``*PERP``), ``"dated_future"`` (a ``-`` in the name,
    ``*-DDMMMYY``) or ``"other"``.  Total function; a universe symbol is reported as ``"other"`` (the caller asks
    :func:`is_linear_usdt_perpetual` first)."""
    name = _contract_name(symbol)
    if name.endswith("PERP"):
        return "usdc_perp"
    if "-" in name:
        return "dated_future"
    return "other"


def excluded_sha256(excluded_symbols: list[str]) -> str:
    """sha256 of the sorted excluded symbols joined by ``\\n`` (UTF-8, no trailing newline); the empty list hashes ``""``."""
    return hashlib.sha256("\n".join(sorted(excluded_symbols)).encode("utf-8")).hexdigest()


def apply_universe(panel: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove every column outside the universe from the union panel dict (the same keys ``panel_cut.cut_panel_days``
    treats: ``symbols``, ``close``, ``turnover``, ``funding_n``, ``funding_sum``, ``is_delisted``, ``last_alive_day``,
    ``delisted_symbols``, ``n_symbols_survivors`` / ``n_symbols_delisted``, and the relisting bookkeeping).  Idempotent.

    Returns ``(panel, report)`` with ``report = {"rule", "n_before", "n_after", "excluded": {"usdc_perp", "dated_future",
    "other"}, "excluded_symbols" (sorted), "excluded_sha256"}``.  The day axis, ``status_counts`` and ``n_partitions_used``
    (facts about the files read) are not touched."""
    symbols = [str(s) for s in panel["symbols"]]
    keep = [j for j, s in enumerate(symbols) if is_linear_usdt_perpetual(s)]
    kept = {symbols[j] for j in keep}
    excluded = sorted(s for s in symbols if s not in kept)
    counts = {k: 0 for k in C.UNIVERSE_CLASSES}
    for s in excluded:
        counts[classify_excluded(s)] += 1
    out: dict[str, Any] = dict(panel)
    if len(keep) != len(symbols):
        cols = np.asarray(keep, dtype=np.int64)
        for k in _SYMBOL_ARRAY_KEYS:
            if k in panel:
                out[k] = np.ascontiguousarray(np.asarray(panel[k])[:, cols])
        out["symbols"] = [symbols[j] for j in keep]
        if "is_delisted" in panel:
            out["is_delisted"] = np.asarray(panel["is_delisted"])[cols]
        if "last_alive_day" in panel:
            out["last_alive_day"] = [panel["last_alive_day"][j] for j in keep]
        for k in _SYMBOL_NAME_LISTS:
            if k in panel:
                out[k] = [s for s in panel[k] if is_linear_usdt_perpetual(s)]
        if "relisted_gaps" in panel:
            out["relisted_gaps"] = {s: g for s, g in (panel.get("relisted_gaps") or {}).items() if is_linear_usdt_perpetual(s)}
        if "is_delisted" in out and "n_symbols_survivors" in out:
            n_del = int(np.asarray(out["is_delisted"]).sum())
            out["n_symbols_delisted"] = n_del
            out["n_symbols_survivors"] = len(out["symbols"]) - n_del
    report = {"rule": C.UNIVERSE_RULE, "n_before": len(symbols), "n_after": len(keep), "excluded": counts,
              "excluded_symbols": excluded, "excluded_sha256": excluded_sha256(excluded)}
    return out, report


def assert_universe(panel: dict[str, Any]) -> None:
    """Guard (loud fail): no column outside the universe is present.  A mode that receives a panel that was not filtered
    must not calculate on it (DEC-101 E1)."""
    bad = [str(s) for s in panel["symbols"] if not is_linear_usdt_perpetual(s)]
    if bad:
        raise UniverseError(f"panel not restricted to the universe {C.UNIVERSE_RULE} (DEC-101 E1): {len(bad)} column(s) outside, "
                            f"e.g. {sorted(bad)[:5]} -- no calculation on this panel")


def ensure_universe(panel: dict[str, Any], report: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Entry gate of every library mode.  Without a ``report`` the filter is applied here (idempotent); with the report of
    the driver the panel must already be restricted (guard) and the report must be one of the registered rule."""
    if report is None:
        return apply_universe(panel)
    if report.get("rule") != C.UNIVERSE_RULE:
        raise UniverseError(f"universe report of rule {report.get('rule')!r}, expected {C.UNIVERSE_RULE!r} (DEC-101 E1)")
    assert_universe(panel)
    return panel, report


def universe_log_line(report: dict[str, Any]) -> str:
    """One log line with the numbers (DEC-101 E1)."""
    ex = report["excluded"]
    return (f"Universum {report['rule']} (DEC-101 E1): {report['n_before']} -> {report['n_after']} Symbole; ausgeschlossen: "
            f"usdc_perp {ex['usdc_perp']}, dated_future {ex['dated_future']}, other {ex['other']} "
            f"(excluded_sha256 {report['excluded_sha256']})")
