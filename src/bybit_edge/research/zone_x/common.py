"""Zone X programme 1 -- shared pieces: zone guard, panel loader, panel arithmetic, output schema.

What lives here
  * the zone guard (no day after 2024-06-30, no day before 2021-01-01) -- applied to the requested window BEFORE the
    data client is touched, and again to every loaded candle;
  * the loader for the daily panel (stream ``rest.kline1d``, symbol ``ALL``) through the Harvest client, the same
    way the repository's extract scripts use it (``hd.configure`` -> ``hd.load`` -> ``hd.extract`` on the JSON
    payload).  The client itself is NOT part of the repository: its directory comes from ``--client-dir`` or the
    environment variable ``HARVEST_CLIENT_DIR``; credentials are read by the client from the environment secrets;
  * the dense panel (calendar days x symbols), log returns without any interpolation, the equal-weighted market
    factor and the market residuals;
  * the output schema guard: the output may only carry keys of a closed vocabulary, short lists and finite numbers.
    There is no key for a mean or a sign of a return and no way to emit a series (see ``validate_output``).

Conventions
  * r_{i,t} = ln(C_{i,t} / C_{i,t-1}) exists only if BOTH closes are observed; a missing day removes the return of that
    day and of the next day (a multi-day return is never bridged, a missing day is never filled).
  * r_M,t = equal-weighted mean of r_{i,t} over the symbols present on day t (only on days with at least
    ``MIN_CROSS_SECTION`` symbols).  beta_i = centred OLS slope of r_i on r_M over the common days of the window;
    e_{i,t} = r_{i,t} - beta_i r_{M,t}.  r_M, beta and e are internal values and never leave the process.
  * Universe rule: linear USDT perpetuals = symbol ends on ``USDT`` and contains no ``-`` (dated futures and
    USDC contracts are counted and dropped).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import os
import sys
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

__all__ = [
    "ALLOWED_KEYS", "EPOCH", "MIN_CROSS_SECTION", "STREAM", "ZONE", "ZONE_END", "ZONE_START",
    "HarvestClientError", "MarketModel", "OutputSchemaError", "Panel", "PanelError", "ZoneGuardError", "ZoneXError",
    "build_panel", "check_day_numbers", "check_window", "code_fingerprint", "cross_section_sd", "daily_log_returns",
    "day_number", "dumps_canonical", "import_harvest_client", "is_linear_usdt", "jsonable", "load_daily_panel",
    "market_model", "parse_day", "refuse_unsafe_out_path", "validate_output",
]

# ----------------------------------------------------------------------------
# constants
# ----------------------------------------------------------------------------

ZONE = "X"
#: DEC-104 E4 (a): Zone X = everything before 2024-07-01; the daily panel stream starts on 2021-01-01.
ZONE_START = date(2021, 1, 1)
ZONE_END = date(2024, 6, 30)
EPOCH = date(1970, 1, 1)
DAY_MS = 86_400_000
STREAM = "rest.kline1d"
EXCHANGE = "bybit"
UNIVERSE_RULE = "linear USDT perpetual: symbol ends on USDT and has no '-'"
#: A day needs at least this many symbols before a market factor or a cross-sectional dispersion exists.
MIN_CROSS_SECTION = 10
#: Names of the sealed files of the programme: never a valid output name.
SEALED_NAME_PATTERNS: tuple[str, ...] = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")
#: The modules whose hashes go into the output (order fixed).
CODE_FILES: tuple[str, ...] = ("common.py", "ik05_rmt.py", "ik04_moments.py", "run_zone_x_1.py")


class ZoneXError(Exception):
    """Base class of all loud failures of the programme."""


class ZoneGuardError(ZoneXError, ValueError):
    """A date outside Zone X (before 2021-01-01 or after 2024-06-30) was requested or found."""


class PanelError(ZoneXError, ValueError):
    """The loaded data does not follow the expected layout."""


class OutputSchemaError(ZoneXError, ValueError):
    """The output would carry a key, a list or a value outside the allowed vocabulary."""


class HarvestClientError(ZoneXError, RuntimeError):
    """The Harvest client cannot be imported."""


# ----------------------------------------------------------------------------
# dates and the zone guard
# ----------------------------------------------------------------------------

def parse_day(value: str | date, what: str = "date") -> date:
    """ISO date text or ``date`` -> ``date`` (loud on anything else)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ZoneGuardError(f"{what}: not an ISO date: {value!r}") from exc


def day_number(d: date) -> int:
    """Days since 1970-01-01 (the number that ``start_ms // 86_400_000`` gives)."""
    return (d - EPOCH).days


def check_window(start: str | date, end: str | date) -> tuple[date, date]:
    """Zone guard for a REQUESTED window: start >= 2021-01-01, end <= 2024-06-30, start <= end (loud)."""
    s = parse_day(start, "start")
    e = parse_day(end, "end")
    if s < ZONE_START:
        raise ZoneGuardError(f"start {s} is before the start of Zone X ({ZONE_START})")
    if e > ZONE_END:
        raise ZoneGuardError(f"end {e} is after the end of Zone X ({ZONE_END}); no data from 2024-07-01 on")
    if s > e:
        raise ZoneGuardError(f"start {s} is after end {e}")
    return s, e


def check_day_numbers(days: np.ndarray, start: date, end: date) -> None:
    """Zone guard for LOADED candles: every day must lie in Zone X and in the requested window (loud)."""
    d = np.asarray(days, dtype=np.int64)
    if d.size == 0:
        return
    lo, hi = int(d.min()), int(d.max())
    if hi > day_number(ZONE_END):
        n = int((d > day_number(ZONE_END)).sum())
        raise ZoneGuardError(f"{n} candle(s) lie after {ZONE_END} (Zone X ends there); nothing is computed")
    if lo < day_number(ZONE_START):
        n = int((d < day_number(ZONE_START)).sum())
        raise ZoneGuardError(f"{n} candle(s) lie before {ZONE_START}; nothing is computed")
    if lo < day_number(start) or hi > day_number(end):
        raise PanelError(f"candles outside the requested window {start}..{end} were delivered")


# ----------------------------------------------------------------------------
# dense panel
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class Panel:
    """Dense daily panel: ``close`` / ``turnover`` are (n_days, n_symbols), NaN where no usable candle exists.

    ``days`` are consecutive epoch-day numbers from the window start to the window end (every calendar day).
    ``stats`` are integer counts of what the builder saw and dropped (they go into the output)."""
    symbols: tuple[str, ...]
    days: np.ndarray
    close: np.ndarray
    turnover: np.ndarray
    stats: dict[str, int]


def is_linear_usdt(symbol: str) -> bool:
    """Universe rule: ends on ``USDT`` and has no ``-`` (same rule as the H-32 universe)."""
    return symbol.endswith("USDT") and "-" not in symbol


def build_panel(symbol: Sequence[str], day: Any, close: Any, turnover: Any,
                start: str | date, end: str | date) -> Panel:
    """Rows (symbol, epoch day, close, turnover) -> dense ``Panel`` over ``start..end``.

    Order of the checks: (1) zone guard on ALL rows (also rows of dropped symbols), (2) universe rule, (3) invalid
    closes (non-finite or <= 0) become missing, (4) exact duplicates collapse (counted), duplicates with different
    values raise.  Nothing is interpolated."""
    s, e = check_window(start, end)
    sym = np.asarray(list(symbol), dtype=str)
    dn = np.asarray(day, dtype=np.int64)
    cl = np.asarray(close, dtype=np.float64)
    tu = np.asarray(turnover, dtype=np.float64)
    if not (sym.size == dn.size == cl.size == tu.size):
        raise PanelError("symbol / day / close / turnover differ in length")
    if sym.size == 0:
        raise PanelError("no rows")
    check_day_numbers(dn, s, e)
    n_rows = int(sym.size)

    is_usdt = np.char.endswith(sym, "USDT") & (np.char.find(sym, "-") < 0)
    n_non_usdt = int((~is_usdt).sum())
    sym, dn, cl, tu = sym[is_usdt], dn[is_usdt], cl[is_usdt], tu[is_usdt]
    if sym.size == 0:
        raise PanelError("no linear USDT perpetual rows")

    uniq, code = np.unique(sym, return_inverse=True)
    n_sym = int(uniq.size)
    n_days = day_number(e) - day_number(s) + 1
    didx = dn - day_number(s)
    key = didx * n_sym + code
    order = np.argsort(key, kind="stable")
    ks = key[order]
    dup = np.concatenate(([False], ks[1:] == ks[:-1]))
    n_dup = int(dup.sum())
    if n_dup:
        prev, cur = order[np.flatnonzero(dup) - 1], order[dup]
        same_c = (cl[prev] == cl[cur]) | (np.isnan(cl[prev]) & np.isnan(cl[cur]))
        same_t = (tu[prev] == tu[cur]) | (np.isnan(tu[prev]) & np.isnan(tu[cur]))
        if not (same_c & same_t).all():
            raise PanelError(f"{int((~(same_c & same_t)).sum())} candle(s) occur twice with DIFFERENT values")
    keep = order[~dup]

    close_d = np.full((n_days, n_sym), np.nan)
    turn_d = np.full((n_days, n_sym), np.nan)
    c_keep, t_keep = cl[keep], tu[keep]
    bad_c = ~(np.isfinite(c_keep) & (c_keep > 0.0))
    bad_t = ~(np.isfinite(t_keep) & (t_keep >= 0.0))
    c_keep = np.where(bad_c, np.nan, c_keep)
    t_keep = np.where(bad_t, np.nan, t_keep)
    close_d[didx[keep], code[keep]] = c_keep
    turn_d[didx[keep], code[keep]] = t_keep
    days = np.arange(day_number(s), day_number(e) + 1, dtype=np.int64)
    stats = {
        "n_rows": n_rows,
        "n_rows_non_usdt": n_non_usdt,
        "n_rows_identical_duplicates": n_dup,
        "n_invalid_close": int(bad_c.sum()),
        "n_invalid_turnover": int(bad_t.sum()),
        "n_symbols_loaded": n_sym,
        "n_calendar_days": int(n_days),
    }
    return Panel(tuple(str(x) for x in uniq), days, close_d, turn_d, stats)


def daily_log_returns(panel: Panel) -> np.ndarray:
    """(n_days - 1, n_symbols) log returns; NaN unless both closes of the pair of days are observed.

    Row ``t`` belongs to calendar day ``panel.days[t + 1]``.  A gap is never bridged."""
    c = panel.close
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(c[1:] / c[:-1])
    r[~np.isfinite(r)] = np.nan
    return r


# ----------------------------------------------------------------------------
# market factor and residuals (internal values, never output)
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketModel:
    """``rm`` (n_days,) market factor (NaN on days below the minimum cross-section); ``beta`` (n_symbols,);
    ``resid`` (n_days, n_symbols) market residuals (NaN where r_i or r_M is missing); ``n_xs`` (n_days,) counts."""
    rm: np.ndarray
    beta: np.ndarray
    resid: np.ndarray
    n_xs: np.ndarray


def market_model(r: np.ndarray, min_cross_section: int = MIN_CROSS_SECTION) -> MarketModel:
    """Equal-weighted market factor, centred OLS betas over the whole window, residuals e = r - beta r_M."""
    valid_r = np.isfinite(r)
    n_xs = valid_r.sum(axis=1)
    safe = np.maximum(n_xs, 1)
    rm = np.where(valid_r, r, 0.0).sum(axis=1) / safe
    rm = np.where(n_xs >= min_cross_section, rm, np.nan)

    both = valid_r & np.isfinite(rm)[:, None]
    cnt = np.maximum(both.sum(axis=0), 1)
    x = np.where(both, rm[:, None], 0.0)
    y = np.where(both, r, 0.0)
    dx = np.where(both, rm[:, None] - x.sum(axis=0) / cnt, 0.0)
    dy = np.where(both, r - y.sum(axis=0) / cnt, 0.0)
    sxx = (dx * dx).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        beta = np.where(sxx > 0.0, (dx * dy).sum(axis=0) / np.where(sxx > 0.0, sxx, 1.0), np.nan)
    resid = r - beta[None, :] * rm[:, None]
    return MarketModel(rm, beta, resid, n_xs)


def cross_section_sd(r: np.ndarray, min_cross_section: int = MIN_CROSS_SECTION) -> np.ndarray:
    """Cross-sectional SD (ddof 1) of the returns of each day; NaN on days below the minimum cross-section."""
    valid = np.isfinite(r)
    n = valid.sum(axis=1)
    mean = np.where(valid, r, 0.0).sum(axis=1) / np.maximum(n, 1)
    dev = np.where(valid, r - mean[:, None], 0.0)
    var = (dev * dev).sum(axis=1) / np.maximum(n - 1, 1)
    return np.where(n >= min_cross_section, np.sqrt(var), np.nan)


# ----------------------------------------------------------------------------
# Harvest client and loader
# ----------------------------------------------------------------------------

def import_harvest_client(client_dir: str | Path | None = None) -> Any:
    """Import the Harvest client module ``harvest_data`` (not part of the repository).

    ``client_dir`` (CLI ``--client-dir``) or the environment variable ``HARVEST_CLIENT_DIR`` is put on ``sys.path``;
    without either the module must already be importable."""
    directory = client_dir or os.environ.get("HARVEST_CLIENT_DIR")
    if directory and str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    try:
        import harvest_data  # type: ignore[import-not-found]
    except ImportError as exc:
        raise HarvestClientError(
            "cannot import harvest_data: pass --client-dir or set HARVEST_CLIENT_DIR to the client directory") from exc
    return harvest_data


def load_daily_panel(start: str | date, end: str | date, *, client_dir: str | Path | None = None,
                     cache_dir: str | Path | None = None, client: Any = None) -> tuple[Panel, dict[str, Any]]:
    """Daily panel ``start..end`` of ``rest.kline1d`` (symbol ``ALL``) through the Harvest client.

    The zone guard runs on the requested window BEFORE the client is imported or configured; every loaded candle is
    guarded again in ``build_panel``.  ``client`` lets tests inject a stand-in for ``harvest_data``.
    Returns ``(panel, load_info)``; ``load_info`` carries the number of client warnings (gaps are reported by the
    client as warnings, never filled) and the first three texts, truncated."""
    s, e = check_window(start, end)
    if cache_dir is not None and "data/harvest" in Path(cache_dir).as_posix():
        raise ZoneXError(f"refusing a client cache below data/harvest: {cache_dir}")
    hd = client if client is not None else import_harvest_client(client_dir)
    import polars as pl

    hd.configure(cache_dir=cache_dir)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df = hd.load(STREAM, ["ALL"], s.isoformat(), e.isoformat(), exchange=EXCHANGE,
                     columns=["symbol", "payload_json"])
    texts = [str(w.message)[:200].encode("ascii", "replace").decode("ascii") for w in caught]
    if df.height == 0:
        raise PanelError(f"{STREAM} returned no rows for {s}..{e}")
    k = hd.extract(df, {"start_ms": "$.startTime", "close": "$.closePrice", "turnover": "$.turnover",
                        "psym": "$.symbol"})
    if k["start_ms"].null_count():
        raise PanelError("candle rows without a start time")
    mismatch = int(((k["psym"].is_not_null()) & (k["psym"] != k["symbol"])).sum())
    if mismatch:
        raise PanelError(f"{mismatch} row(s) whose payload symbol differs from the column symbol")
    try:
        start_ms = k["start_ms"].cast(pl.Int64).to_numpy()
    except pl.exceptions.PolarsError as exc:
        raise PanelError("candle start time is not an integer") from exc
    if (start_ms % DAY_MS != 0).any():
        raise PanelError("candle start time is not on a UTC day boundary")
    close = k["close"].cast(pl.Float64, strict=False).fill_null(float("nan")).to_numpy()
    turnover = k["turnover"].cast(pl.Float64, strict=False).fill_null(float("nan")).to_numpy()
    panel = build_panel(k["symbol"].to_list(), start_ms // DAY_MS, close, turnover, s, e)
    return panel, {"n_load_warnings": len(texts), "load_warnings": texts[:3]}


# ----------------------------------------------------------------------------
# hashing and safe output paths
# ----------------------------------------------------------------------------

def code_fingerprint() -> dict[str, str]:
    """sha256 of each module file of the programme plus a combined hash (names and hashes in fixed order)."""
    here = Path(__file__).resolve().parent
    out: dict[str, str] = {}
    for name in CODE_FILES:
        out[name[:-3]] = hashlib.sha256((here / name).read_bytes()).hexdigest()
    text = "\n".join(f"{n}:{out[n[:-3]]}" for n in CODE_FILES)
    out["combined"] = hashlib.sha256(text.encode("ascii")).hexdigest()
    return out


def refuse_unsafe_out_path(path: str | Path) -> Path:
    """Loud fail for an output below ``data/harvest`` or one that carries the name of a sealed file."""
    p = Path(path)
    if "data/harvest" in p.as_posix():
        raise ZoneXError(f"refusing to write under data/harvest: {p}")
    for pat in SEALED_NAME_PATTERNS:
        if fnmatch.fnmatch(p.name, pat):
            raise ZoneXError(f"refusing to use the name of a sealed file: {p.name}")
    return p


# ----------------------------------------------------------------------------
# output schema guard
# ----------------------------------------------------------------------------

#: Substrings that no key may contain: nothing that says mean, sign, drift, path or series of a return.
FORBIDDEN_KEY_TOKENS: tuple[str, ...] = (
    "mean", "avg", "average", "sign", "positive", "negative", "drift", "cumul", "series", "path", "beta",
    "alpha", "intercept", "pnl", "timeseries", "per_day", "by_day", "per_symbol", "by_symbol")

#: Closed vocabulary of output keys.  Anything else (a symbol name, a date, a new field) fails loudly; a new field
#: needs a deliberate edit here.  Digit keys are autocorrelation lags.
ALLOWED_KEYS: frozenset[str] = frozenset({
    # top level and shared
    "program", "zone", "window", "params", "inputs", "code_sha256", "ik05", "ik04", "report",
    "start", "end", "n_calendar_days", "n_return_days",
    # params
    "min_days", "coverage_min", "min_cross_section", "acf_max_lag", "n_eff_window_days", "lambda_needed",
    "subwindows", "sub1", "sub2", "sub3", "moment_min_obs",
    # inputs
    "stream", "exchange", "universe_rule", "n_rows", "n_rows_non_usdt", "n_rows_identical_duplicates",
    "n_invalid_close", "n_invalid_turnover", "n_symbols_loaded", "n_symbols_excluded_min_days",
    "n_symbols_analysed", "n_days_below_min_cross_section", "n_load_warnings", "load_warnings",
    # code hashes
    "common", "ik05_rmt", "ik04_moments", "run_zone_x_1", "combined",
    # ik05
    "method", "full", "sub_windows", "status", "reason", "n_eligible_days", "n_symbols_in_window",
    "n_symbols_covered", "k_symbols", "t_days", "q_ratio", "mp_edge", "n_zero_variance_dropped",
    "pearson", "spearman", "residual", "raw", "top_eigenvalues", "n_above_edge", "explained_share_above_edge",
    "n_ge_lambda_needed",
    # ik04
    "moments", "r_daily", "e_market_resid", "all", "t1_low", "t2_mid", "t3_high", "n_symbols",
    "excess_kurtosis", "skewness", "n_symbols_without_turnover", "xs_dispersion", "n_days", "level_over_days",
    "quantiles", "acf", "abs_r_market", "c_hat", "n_eff_365", "n_eff_by_max_lag", "c_overlap", "abs_r_symbol_acf",
    "missing_days", "n_symbols_with_gaps", "share", "n",
    # quantile labels and lags
    "q10", "q25", "q50", "q75", "q90", "max", "1", "2", "3", "4", "5", "10", "20", "40",
    # DEC-105 report row
    "n_eff", "selection_k", "estimate", "se", "ci95", "upper_limit95", "shrinkage_note", "note",
})

MAX_LIST_LEN = 20
MAX_DEPTH = 8
MAX_LEAVES = 3000
MAX_STRING = 300


def _check_vocabulary() -> None:
    for key in sorted(ALLOWED_KEYS):
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in key:
                raise OutputSchemaError(f"allowed key {key!r} contains the forbidden token {tok!r}")


_check_vocabulary()


def _round12(x: float) -> float:
    return float(f"{x:.12g}")


def jsonable(obj: Any) -> Any:
    """Plain-JSON copy: numpy scalars -> Python, NaN / inf -> None, floats rounded to 12 significant digits."""
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [jsonable(v) for v in obj.tolist()]
    if isinstance(obj, np.generic):
        return jsonable(obj.item())
    if isinstance(obj, bool) or obj is None or isinstance(obj, (int, str)):
        return obj
    if isinstance(obj, float):
        return _round12(obj) if math.isfinite(obj) else None
    raise OutputSchemaError(f"value of type {type(obj).__name__} cannot be serialised")


def validate_output(obj: Any) -> None:
    """Schema guard of the output (loud).  Passes only if

      * every dict key is in ``ALLOWED_KEYS`` (so no symbol name, no date, no new field);
      * every list has at most ``MAX_LIST_LEN`` entries, all plain numbers or short strings (so no series);
      * every leaf is None, bool, int, a finite float or a short string; depth and leaf count are bounded.
    """
    if not isinstance(obj, dict):
        raise OutputSchemaError("the output must be a JSON object")
    leaves = [0]
    _walk(obj, "$", 0, leaves)
    if leaves[0] > MAX_LEAVES:
        raise OutputSchemaError(f"too many values in the output ({leaves[0]} > {MAX_LEAVES})")


def _leaf(v: Any, path: str, leaves: list[int]) -> None:
    leaves[0] += 1
    if v is None or isinstance(v, (bool, int)):
        return
    if isinstance(v, float):
        if not math.isfinite(v):
            raise OutputSchemaError(f"{path}: non-finite number")
        return
    if isinstance(v, str):
        if len(v) > MAX_STRING:
            raise OutputSchemaError(f"{path}: string longer than {MAX_STRING}")
        return
    raise OutputSchemaError(f"{path}: value of type {type(v).__name__} is not allowed")


def _walk(node: Any, path: str, depth: int, leaves: list[int]) -> None:
    if depth > MAX_DEPTH:
        raise OutputSchemaError(f"{path}: nesting deeper than {MAX_DEPTH}")
    if isinstance(node, dict):
        for k, v in node.items():
            if not isinstance(k, str) or k not in ALLOWED_KEYS:
                raise OutputSchemaError(f"{path}: key {k!r} is not in the allowed output vocabulary")
            _walk(v, f"{path}/{k}", depth + 1, leaves)
    elif isinstance(node, list):
        if len(node) > MAX_LIST_LEN:
            raise OutputSchemaError(
                f"{path}: list of {len(node)} entries (limit {MAX_LIST_LEN}); a series is forbidden")
        for v in node:
            if isinstance(v, (dict, list)):
                raise OutputSchemaError(f"{path}: containers inside a list are not allowed")
            _leaf(v, path, leaves)
    else:
        _leaf(node, path, leaves)


def dumps_canonical(obj: Any) -> str:
    """Deterministic JSON text (sorted keys, ASCII, no NaN) of an already validated output."""
    return json.dumps(jsonable(obj), sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n"
