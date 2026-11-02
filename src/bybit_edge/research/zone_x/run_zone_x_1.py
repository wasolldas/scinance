"""Zone X programme 1: command line for IK-05 (RMT factor count) and IK-04 (moments for the null world).

  python -m bybit_edge.research.zone_x.run_zone_x_1 --out OUT.json [--start 2021-01-01 --end 2024-06-30]
        [--min-days 250] [--coverage-min 0.9] [--client-dir DIR] [--cache-dir DIR]

Reads the daily panel (``rest.kline1d``) of Zone X through the Harvest client (``common.load_daily_panel``), computes
both measurements and writes ONE JSON file (created exclusively: an existing file is never overwritten).  The output
carries counts, eigenvalues and quantiles of shape and dependence statistics only; ``common.validate_output`` refuses
any key or list outside the closed vocabulary (no mean or sign of a return, no series).

Zone guard: the window must lie in 2021-01-01..2024-06-30; it is checked before the client is touched and again for
every loaded candle.  Exit codes: 0 = written, 1 = failure, 2 = zone guard / argument refusal.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Callable
from datetime import date
from typing import Any

import numpy as np

from . import common, ik04_moments, ik05_rmt

__all__ = ["build_output", "build_parser", "main"]

PROGRAM = "zone_x_1"
SHRINKAGE_NOTE = ("descriptive second-moment census on Zone X; no estimate under test and no selection step; "
                  "the sampling error of eigenvalues, kurtosis and autocorrelations is not part of this output")
REPORT_NOTE = ("DEC-105 row: estimate / se / ci95 / upper_limit95 not applicable (counts and shape statistics); "
               "n_eff = effective clusters of a 365-day window from the autocorrelation of |r_M|")


def build_output(panel: common.Panel, load_info: dict[str, Any] | None = None, *,
                 min_days: int = 250, coverage_min: float = 0.9,
                 subwindows: tuple[tuple[str, str, str], ...] = ik05_rmt.SUBWINDOWS) -> dict[str, Any]:
    """Both measurements on ``panel`` -> the validated output object (plain JSON types)."""
    r_all = common.daily_log_returns(panel)
    return_days = panel.days[1:]
    n_obs = np.isfinite(r_all).sum(axis=0)
    keep = np.flatnonzero(n_obs >= min_days)
    n_excluded = int(panel.close.shape[1] - keep.size)
    if keep.size < common.MIN_CROSS_SECTION:
        raise common.PanelError(
            f"only {keep.size} symbol(s) have {min_days} or more return days (need {common.MIN_CROSS_SECTION})")
    symbols = [panel.symbols[i] for i in keep]
    r = r_all[:, keep]

    ik05 = ik05_rmt.run_ik05(r, return_days, coverage_min=coverage_min, subwindows=subwindows)
    ik04 = ik04_moments.run_ik04(r, panel.close[:, keep], panel.turnover[:, keep], symbols)

    inputs: dict[str, Any] = {
        "stream": common.STREAM,
        "exchange": common.EXCHANGE,
        "universe_rule": common.UNIVERSE_RULE,
        **{k: v for k, v in panel.stats.items() if k != "n_calendar_days"},
        "n_symbols_excluded_min_days": n_excluded,
        "n_symbols_analysed": int(keep.size),
        "n_days_below_min_cross_section": ik04["n_days_below_min_cross_section"],
    }
    inputs.update(load_info or {})
    out: dict[str, Any] = {
        "program": PROGRAM,
        "zone": common.ZONE,
        "window": {
            "start": _iso(int(panel.days[0])),
            "end": _iso(int(panel.days[-1])),
            "n_calendar_days": int(panel.days.size),
            "n_return_days": int(return_days.size),
        },
        "params": {
            "min_days": int(min_days),
            "coverage_min": float(coverage_min),
            "min_cross_section": common.MIN_CROSS_SECTION,
            "acf_max_lag": ik04_moments.ACF_LAGS,
            "n_eff_window_days": ik04_moments.N_EFF_WINDOW,
            "lambda_needed": ik05_rmt.LAMBDA_NEEDED,
            "subwindows": {name: {"start": s, "end": e} for name, s, e in subwindows},
        },
        "inputs": inputs,
        "code_sha256": common.code_fingerprint(),
        "ik05": ik05,
        "ik04": ik04,
        "report": {
            "zone": common.ZONE,
            "n_eff": ik04["abs_r_market"]["n_eff_365"],
            "c_overlap": 1.0,
            "selection_k": 1,
            "estimate": None,
            "se": None,
            "ci95": None,
            "upper_limit95": None,
            "shrinkage_note": SHRINKAGE_NOTE,
            "note": REPORT_NOTE,
        },
    }
    out = common.jsonable(out)
    common.validate_output(out)
    return out


def _iso(day_num: int) -> str:
    return date.fromordinal(common.EPOCH.toordinal() + day_num).isoformat()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Zone X programme 1: IK-05 RMT factor count and IK-04 null-world moments")
    ap.add_argument("--out", required=True, help="output JSON (must not exist yet)")
    ap.add_argument("--start", default=common.ZONE_START.isoformat(), help="first day (>= 2021-01-01)")
    ap.add_argument("--end", default=common.ZONE_END.isoformat(), help="last day (<= 2024-06-30)")
    ap.add_argument("--min-days", type=int, default=250, help="symbols with fewer return days are excluded and counted")
    ap.add_argument("--coverage-min", type=float, default=0.9, help="IK-05: minimum coverage of a symbol on the days")
    ap.add_argument("--client-dir", default=None, help="directory of harvest_data.py (or env HARVEST_CLIENT_DIR)")
    ap.add_argument("--cache-dir", default=None, help="local cache directory of the client (never under data/harvest)")
    return ap


def _say(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main(argv: list[str] | None = None, *, panel_loader: Callable[..., Any] | None = None) -> int:
    """Run the programme.  ``panel_loader`` replaces ``common.load_daily_panel`` (tests)."""
    a = build_parser().parse_args(argv)
    try:
        common.check_window(a.start, a.end)
        out_path = common.refuse_unsafe_out_path(a.out)
        if out_path.exists():
            raise common.ZoneXError(f"{out_path} exists already; it is never overwritten")
        if not 0.0 < a.coverage_min <= 1.0 or a.min_days < 2:
            raise common.ZoneGuardError("coverage-min must be in (0, 1] and min-days at least 2")
    except common.ZoneGuardError as exc:
        _say(f"REFUSED ({type(exc).__name__}): {exc}")
        return 2
    except common.ZoneXError as exc:
        _say(f"FAILED ({type(exc).__name__}): {exc}")
        return 1
    try:
        loader = panel_loader or common.load_daily_panel
        panel, load_info = loader(a.start, a.end, client_dir=a.client_dir, cache_dir=a.cache_dir)
        out = build_output(panel, load_info, min_days=a.min_days, coverage_min=a.coverage_min)
        text = common.dumps_canonical(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("x", encoding="ascii", newline="\n") as fh:
            fh.write(text)
    except common.ZoneGuardError as exc:
        _say(f"REFUSED ({type(exc).__name__}): {exc}")
        return 2
    except (common.ZoneXError, OSError) as exc:
        _say(f"FAILED ({type(exc).__name__}): {exc}")
        return 1
    full = out["ik05"]["full"]
    _say(f"written {out_path} sha256 {hashlib.sha256(text.encode('ascii')).hexdigest()} "
         f"(symbols {out['inputs']['n_symbols_analysed']}, K {full.get('k_symbols')}, T {full.get('t_days')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
