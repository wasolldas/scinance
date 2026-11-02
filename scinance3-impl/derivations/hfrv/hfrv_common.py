"""HF-RV nuisance (Option 3, DEC-98) -- shared rules, loaders and guards.

PRE-FIXED RULES (written BEFORE any statistic of the HF data was computed; deviations only with
reason and fork direction, pattern DEC-93 H-1):

R-1  Sample: IV days t in [2021-03-24, 2024-05-01]; RV days s <= 2024-05-31.  The kline extracts
     must not contain any UTC day after 2024-05-31 (loud fail at load time, before any return).
     DVOL: IV only for t <= 2024-05-01 (``assert_dvol_level_day`` on every IV day).
R-2  Day completeness: a UTC day is complete iff it has exactly 1,440 distinct minute starts (all on
     a full minute, all inside the day) and no conflicting duplicate.  Exact duplicates (same
     start_ms, same OHLCV) are dropped and counted; conflicting duplicates make the day
     incomplete.  No threshold below 1,440.  Incomplete day -> RV_day missing, never filled.
R-3  Intraday returns: the price at a grid point tau is the close of the 1-min candle that ENDS at
     tau; the day anchor (00:00) is the close of the 23:59 candle of the previous UTC day, so the
     intraday log returns of every variant telescope to the close-to-close daily return (vi).
     RV_day(s) needs day s complete and the 23:59 candle of day s-1 present.
R-4  Variants: (i) 1-min (1,440 returns); (ii) 5-min grid 00:00, 00:05, .., 24:00 (288);
     (iii) 5-min subsampled = mean over phases p = 0..4 of the RV on the grid {0, p, p+5, ..,
     1435+p, 1440} (edge partial returns keep every phase on the full day; p = 0 is (ii));
     (iv) 15-min (96); (v) 30-min (48); (vi) close-to-close r_s^2, r_s = ln(C_s,23:59 / C_s-1,23:59).
R-5  RV_fwd30(t) = sqrt((365/30) * sum_{k=1..30} RV_day(t+k)); missing if any of the 30 days is
     missing; premium P(t) in S1 / S2 / S3 exactly as H-27 (h27_series.premium_frame); missing if
     IV(t) or RV_fwd30(t) is missing; never filled.
R-6  IV(t) = close / 100 of the DVOL hourly candle whose payload ``timestamp`` is 23:00 UTC of day t
     (h27_series convention); extra check ts_exchange_ms == payload timestamp; duplicate -> fail.
R-7  Statistics: ``nuisance.describe`` (copied unchanged from the H-27 derivation; longest
     gap-free run, P-3 rule, bootstrap 2,000 reps, seed 27).  kappa = E[x^2]/E[x_s x_{s+L}] on
     RV_day exactly as the H-27 review (``noise_share.py``: L in {2, 3, 5}, days from 2021-03-25);
     additionally L 2..5.  Consensus c = tapered ACF sum (Tukey taper lags 60..90) exactly as the
     review's ``mc_rule_bias`` c_true_longrun.
R-8  SE / power: SE_nuis(n) = SD * sqrt(c / n); SE_null(n) = SE_null_365 of the H-27 file (unit,
     symbol; calibrated on the close-to-close world) * sqrt(365 / n); binding SE = max.  The HF null
     SE is UNBELEGT (would be smaller) and is NOT recalibrated.  Priors from the H-27 file
     (BTC S1 pi-2 central 9.47, band 7.00 / 13.72, pi-1 10.48).  Days per window by bisection with
     ``power_p1`` (solver copied from the programme balance); full date = 2026-07-01 + 2 ceil(n) - 1
     + 30 days.
R-9  Check against the UNBELEGT assumption SD 15.1: "bestaetigt" iff the BTC S1 SD of the
     recommended variant lies in [14.1, 16.1] (+-1 VP); below: "nicht bestaetigt (guenstiger)",
     above: "nicht bestaetigt (unguenstiger)".
R-10 Recommendation rule (fixed now, NOT chosen by SD): preference order (iii) 5-min subsampled >
     (ii) 5-min > (iv) 15-min > (v) 30-min; a variant qualifies iff its signature ratio
     rms(RV_fwd30 variant) / rms(RV_fwd30 30-min) lies in [0.95, 1.05] for BTC AND ETH (micro-
     structure level bias).  (i) 1-min and (vi) cc are reported, never recommended.  SD and kappa
     are reported only (no selection on SD -> direction neutral).
R-11 Leg: BTC binding; ETH, daily BTC/ETH average and conjunction are report (ETH prior UNBELEGT).
R-12 Every output dict passes ``h27_common.no_mean`` and ``guard_keys`` (extra guard); LABEL in
     every file.  Deterministic (bootstrap seed 27).
R-13 Extra consistency check: last 1-min close of each day vs. the local union panel 1D close
     (panel read only for years 2021..2024, rows after 2024-05-31 dropped at read time); output
     counts and the maximal relative deviation only.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/scinance/src")
from h27_common import (LABEL as H27_LABEL, NUISANCE_FIRST_IV_DAY, NUISANCE_LAST_IV_DAY,  # noqa: E402
                        RV_LAST_PRICE_DAY, assert_dvol_level_day, assert_rv_day, no_mean,
                        truncate_prices)

SCRATCH = HERE.parent
D = SCRATCH / "hf_data" / "raw"
OUT_DIR = Path("/home/user/scinance/scinance3-impl/state/herleitung_hfrv")
H27_FJ = Path("/home/user/scinance/scinance3-impl/state/herleitung_h27/feasibility.json")
PANEL = SCRATCH / "panel" / "panel_1d"

KLINE = {"BTC": D / "bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet",
         "ETH": D / "bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet"}
DVOL = D / "deribit_dvol_raw_2021-03-24_2024-05-31.parquet"
PSYM = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
ANN, H = 365.0, 30
MIN_PER_DAY = 1440
MS_DAY = 86_400_000
MS_MIN = 60_000
FIRST_KLINE_DAY = "2021-03-24"
VARIANTS = ("v1_1min", "v2_5min", "v3_5min_sub", "v4_15min", "v5_30min", "v6_cc")
VARIANT_TXT = {"v1_1min": "(i) 1-min roh", "v2_5min": "(ii) 5-min Gitter",
               "v3_5min_sub": "(iii) 5-min subsample-gemittelt (5 Phasen)", "v4_15min": "(iv) 15-min",
               "v5_30min": "(v) 30-min", "v6_cc": "(vi) close-to-close (letzter 1-min-close)"}

LABEL = ("HF-RV-Nuisance 2021-03-24..2024-05-31 (IV-Tage bis 2024-05-01, 1-min-Kerzen bis 2024-05-31): "
         "nur Streuungs-, Autokorrelations-, Verhaeltnis- und RV-Niveaugroessen; der Mittelwert der "
         "Praemie (jede Einheit), ihr Vorzeichen und das DVOL-Mittel werden weder ausgegeben noch "
         "gespeichert. | H-27-Etikett: " + H27_LABEL)

# extra key guard (on top of h27_common.no_mean): refuses any key naming a mean / median / level of
# the premium, of IV or of DVOL, and any generic mean/median key.
_BAD = re.compile(r"(^|_)(mean|avg|median|mittel)(_|$)|prem.*(mean|mittel|level|sign|vorzeichen)|"
                  r"dvol.*(mean|level|mittel)|(^|_)iv_(mean|level|rms)|sign_of|vorzeichen", re.I)


def guard_keys(d, path: str = ""):
    if isinstance(d, dict):
        for k, v in d.items():
            if _BAD.search(str(k)):
                raise RuntimeError(f"blindness guard: key {path}/{k!r} refused")
            guard_keys(v, f"{path}/{k}")
    elif isinstance(d, (list, tuple)):
        for v in d:
            guard_keys(v, path)
    return d


def check_out(d):
    """Both guards on every output dict (R-12)."""
    no_mean(d)
    guard_keys(d)
    return d


def day_str(day_idx: int) -> str:
    return (date(1970, 1, 1) + timedelta(days=int(day_idx))).isoformat()


def day_idx(s: str) -> int:
    return (date.fromisoformat(s) - date(1970, 1, 1)).days


def days_range(lo: str, hi: str) -> list[str]:
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(a + timedelta(i)).isoformat() for i in range((b - a).days + 1)]


# ----------------------------------------------------------------------------------------------
# kline loader (R-1, R-2) -- returns a calendar-indexed close matrix, no statistic
# ----------------------------------------------------------------------------------------------

def load_kline(sym: str) -> dict:
    path = KLINE[sym]
    df = pl.read_parquet(path, columns=["symbol", "start_ms", "open", "high", "low", "close",
                                        "volume", "turnover", "column_symbol", "category", "interval"])
    # R-1: no day after 2024-05-31 (assert BEFORE anything else is formed)
    max_ms = int(df["start_ms"].max())
    min_ms = int(df["start_ms"].min())
    last_day = day_str(max_ms // MS_DAY)
    first_day = day_str(min_ms // MS_DAY)
    assert last_day <= RV_LAST_PRICE_DAY, f"kline extract {sym} contains {last_day} > {RV_LAST_PRICE_DAY}"
    assert first_day >= FIRST_KLINE_DAY, f"kline extract {sym} starts {first_day} < {FIRST_KLINE_DAY}"
    assert_rv_day(last_day)
    meta = {"rows": df.height, "first_day": first_day, "last_day": last_day,
            "symbols": sorted(set(df["symbol"].to_list())),
            "column_symbols": sorted(set(df["column_symbol"].to_list())),
            "categories": sorted(str(c) for c in set(df["category"].to_list())),
            "intervals": sorted(str(c) for c in set(df["interval"].to_list()))}
    if meta["symbols"] != [PSYM[sym]]:
        raise RuntimeError(f"unexpected symbol content {meta['symbols']}")
    misaligned = int((df["start_ms"] % MS_MIN != 0).sum())
    meta["start_ms_not_on_full_minute"] = misaligned
    if misaligned:
        df = df.filter(pl.col("start_ms") % MS_MIN == 0)
    # R-2 duplicates
    n_before = df.height
    exact = df.unique(subset=["start_ms", "open", "high", "low", "close", "volume"], keep="first")
    n_exact_dups = n_before - exact.height
    per_ms = exact.group_by("start_ms").len()
    conflicting_ms = per_ms.filter(pl.col("len") > 1)["start_ms"].to_list()
    meta["exact_duplicates_dropped"] = int(n_exact_dups)
    meta["conflicting_duplicate_minutes"] = len(conflicting_ms)
    bad_days = sorted({int(ms) // MS_DAY for ms in conflicting_ms})
    df = exact.unique(subset=["start_ms"], keep="first").sort("start_ms")
    ms = df["start_ms"].to_numpy().astype(np.int64)
    d_idx = ms // MS_DAY
    m_idx = (ms % MS_DAY) // MS_MIN
    d0 = day_idx(FIRST_KLINE_DAY)
    d1 = day_idx(last_day)
    nd = d1 - d0 + 1
    closes = np.full((nd, MIN_PER_DAY), np.nan)
    opens = np.full((nd, MIN_PER_DAY), np.nan)
    closes[d_idx - d0, m_idx] = df["close"].to_numpy()
    opens[d_idx - d0, m_idx] = df["open"].to_numpy()
    rows_per_day = np.isfinite(closes).sum(axis=1)
    complete = rows_per_day == MIN_PER_DAY
    for b in bad_days:
        if d0 <= b <= d1:
            complete[b - d0] = False
    # non-positive closes are data errors -> day incomplete (count)
    nonpos = np.nansum(closes <= 0, axis=1) > 0
    meta["days_with_nonpositive_close"] = int(nonpos.sum())
    complete &= ~nonpos
    days = [day_str(d0 + i) for i in range(nd)]
    incomplete = [(days[i], int(rows_per_day[i])) for i in range(nd) if not complete[i]]
    meta["n_days"] = nd
    meta["n_complete_days"] = int(complete.sum())
    meta["incomplete_days"] = incomplete
    meta["rows_per_day_hist"] = {str(k): int(v) for k, v in zip(*np.unique(rows_per_day, return_counts=True))}
    meta["conflicting_duplicate_days"] = [day_str(b) for b in bad_days]
    return {"days": days, "closes": closes, "opens": opens, "complete": complete, "meta": meta}


# ----------------------------------------------------------------------------------------------
# RV per variant (R-3, R-4)
# ----------------------------------------------------------------------------------------------

def _grid_rv(lp: np.ndarray, step: int, phase: int) -> np.ndarray:
    """lp: (n_days, 1441) log prices at minute boundaries 0..1440 (0 = anchor).  Grid points
    {0, phase, phase+step, ..., <=1440, 1440}; returns the RV per day."""
    pts = list(range(phase, MIN_PER_DAY + 1, step))
    if pts[0] != 0:
        pts = [0] + pts
    if pts[-1] != MIN_PER_DAY:
        pts = pts + [MIN_PER_DAY]
    g = lp[:, pts]
    r = np.diff(g, axis=1)
    return np.sum(r * r, axis=1)


def rv_day_variants(k: dict) -> dict:
    """Daily realized variance per variant on the calendar days of the extract (NaN if R-3 fails)."""
    closes, complete, days = k["closes"], k["complete"], k["days"]
    nd = closes.shape[0]
    anchor = np.full(nd, np.nan)
    anchor[1:] = closes[:-1, MIN_PER_DAY - 1]
    ok = complete & np.isfinite(anchor)
    for i in np.flatnonzero(ok):
        assert_rv_day(days[i])
    P = np.concatenate([anchor[:, None], closes], axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        lp = np.log(P)
    out = {}
    out["v1_1min"] = _grid_rv(lp, 1, 0)
    out["v2_5min"] = _grid_rv(lp, 5, 0)
    out["v3_5min_sub"] = np.mean([_grid_rv(lp, 5, p) for p in range(5)], axis=0)
    out["v4_15min"] = _grid_rv(lp, 15, 0)
    out["v5_30min"] = _grid_rv(lp, 30, 0)
    out["v6_cc"] = (lp[:, MIN_PER_DAY] - lp[:, 0]) ** 2
    for v in out:
        out[v] = np.where(ok, out[v], np.nan)
    diag = {"n_rv_days": int(ok.sum()),
            "rv_days_missing_in_2021-03-25..2024-05-31": [days[i] for i in range(1, nd) if not ok[i]]}
    # microstructure diagnostic: lag-1 autocorrelation of 1-min / 5-min returns pooled over days
    r1 = np.diff(lp[ok], axis=1)
    a = r1[:, 1:].ravel(); b = r1[:, :-1].ravel()
    diag["acf1_intraday_1min_returns"] = float(np.corrcoef(a, b)[0, 1])
    g5 = lp[ok][:, ::5]
    r5 = np.diff(g5, axis=1)
    diag["acf1_intraday_5min_returns"] = float(np.corrcoef(r5[:, 1:].ravel(), r5[:, :-1].ravel())[0, 1])
    # open of the 00:00 candle vs previous 23:59 close (anchor convention check)
    o0 = k["opens"][:, 0]
    both = np.isfinite(o0) & np.isfinite(anchor)
    diag["open0000_eq_prev_close2359"] = {"n": int(both.sum()),
                                          "equal": int(np.sum(o0[both] == anchor[both]))}
    return {"rv": out, "ok": ok, "diag": diag}


def rv_fwd30(rv_day: np.ndarray, kdays: list[str], t_days: list[str]) -> np.ndarray:
    """RV_fwd30(t) (decimal) from daily RV on the calendar index kdays; NaN if any day missing."""
    pos = {d: i for i, d in enumerate(kdays)}
    out = np.full(len(t_days), np.nan)
    for j, t in enumerate(t_days):
        i = pos.get(t)
        if i is None or i + H >= len(rv_day):
            continue
        seg = rv_day[i + 1:i + 1 + H]
        assert_rv_day(kdays[i + H])
        if seg.size == H and np.all(np.isfinite(seg)):
            out[j] = np.sqrt(ANN / H * np.sum(seg))
    return out


# ----------------------------------------------------------------------------------------------
# DVOL (R-6)
# ----------------------------------------------------------------------------------------------

def load_iv() -> tuple[dict[str, dict[str, float]], dict]:
    df = pl.read_parquet(DVOL, columns=["symbol", "ts_exchange_ms", "payload_json"])
    iv: dict[str, dict[str, float]] = {"BTC": {}, "ETH": {}}
    meta = {"rows": df.height, "symbols": sorted(set(df["symbol"].to_list())), "payload_keysets": {},
            "ts_exchange_ms_eq_payload_timestamp": 0, "ts_exchange_ms_ne_payload_timestamp": 0,
            "not_on_full_hour": 0, "rows_per_day_hist": {}}
    per_day: dict[tuple[str, str], int] = {}
    for sym, ts, pj in zip(df["symbol"].to_list(), df["ts_exchange_ms"].to_list(), df["payload_json"].to_list()):
        o = json.loads(pj)
        ks = ",".join(sorted(o.keys()))
        meta["payload_keysets"][ks] = meta["payload_keysets"].get(ks, 0) + 1
        pts = int(o["timestamp"])
        if int(ts) == pts:
            meta["ts_exchange_ms_eq_payload_timestamp"] += 1
        else:
            meta["ts_exchange_ms_ne_payload_timestamp"] += 1
        dt = datetime.fromtimestamp(pts / 1000, tz=timezone.utc)
        if (dt.minute, dt.second) != (0, 0):
            meta["not_on_full_hour"] += 1
        d = dt.date().isoformat()
        per_day[(sym, d)] = per_day.get((sym, d), 0) + 1
        if dt.hour == 23 and NUISANCE_FIRST_IV_DAY <= d <= NUISANCE_LAST_IV_DAY:
            assert_dvol_level_day(d)
            if d in iv[sym]:
                raise RuntimeError(f"duplicate 23h DVOL candle {sym} {d}")
            iv[sym][d] = float(o["close"]) / 100.0
    hist: dict[str, dict[str, int]] = {}
    for (sym, d), n in per_day.items():
        hist.setdefault(sym, {}).setdefault(str(n), 0)
        hist[sym][str(n)] += 1
    meta["rows_per_day_hist"] = hist
    t_days = days_range(NUISANCE_FIRST_IV_DAY, NUISANCE_LAST_IV_DAY)
    meta["iv_days_missing"] = {s: [t for t in t_days if t not in iv[s]] for s in iv}
    return iv, meta


# ----------------------------------------------------------------------------------------------
# panel cross-check (R-13): counts only
# ----------------------------------------------------------------------------------------------

def panel_closes_truncated(sym: str) -> dict[str, float]:
    rows: dict[str, float] = {}
    for state in ("frozen", "open"):
        base = PANEL / state / "source=bybit" / "category=linear" / f"symbol={PSYM[sym]}"
        for yr in ("2021", "2022", "2023", "2024"):
            f = base / f"year={yr}" / "part.parquet"
            if not f.exists():
                continue
            t = pq.ParquetFile(f).read(columns=["start_ms", "close"]).to_pydict()
            for ms, c in zip(t["start_ms"], t["close"]):
                d = day_str(int(ms) // MS_DAY)
                if d > RV_LAST_PRICE_DAY:
                    continue          # dropped at read time, before anything is compared
                rows[d] = float(c)
    if rows and max(rows) > RV_LAST_PRICE_DAY:
        raise RuntimeError("panel truncation failed")
    days = sorted(rows)
    days_t, vals = truncate_prices(days, [rows[d] for d in days])
    return dict(zip(days_t, vals))
