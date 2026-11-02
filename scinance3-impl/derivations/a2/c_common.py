"""A2 preparatory work, part C (EXP-CLOCK, DEC-103): null simulation E4, binding SE, funding interval W2,
pilot hand-over rule (template).  Shared rules, loaders and guards.  NO VERDICT, NO MEAN, NOTHING REGISTERED.

PRE-FIXED RULES (written BEFORE any number of this part was computed; a deviation only with reason and fork
direction, pattern DEC-93 H-1):

R-C1  Time limits.  Returns only from the 1-min kline extract BTCUSDT/ETHUSDT 2021-03-24..2024-05-31: the
      ``start_ms`` and ``symbol`` columns are read ALONE first and asserted (first UTC day >= 2021-03-24, last
      UTC day <= 2024-05-31) BEFORE any price column is read (``assert_kline_dates``); a second assert on
      the day grid before every price array is formed.  Settlement calendar: only rows with UTC day
      <= 2026-06-30 (assert), only the fields ccy / type / instrument_name / timestamp (no position needed,
      no price field exists or is read; assert on the column set).  Funding timestamps: only symbol / fts,
      only UTC days 2025-07-01..2026-06-28 (assert).  No sealed file, no harvest client, no network, nothing
      under data/harvest.
R-C2  Hash check.  Every input file is hashed (sha256) and compared with EXTRACT_LOG.json before use.
R-C3  Day classes (DEC-98 N5 (3), DEC-103 E1/E3): Friday weekly / monthly (last Friday of the month) /
      quarterly (last Friday of Mar/Jun/Sep/Dec), no holiday shift; every analysed day must carry option
      deliveries of BTC AND ETH (checked from the instrument names, expiry date = name date; currency = name
      prefix BTC-/ETH-, the column ccy carries the instrument name - note of 2026-10-31); outlier days
      = any option delivery booked > 60 s after 08:00:00 UTC (expected 2020-08-27, 2024-08-19; checked);
      futures day = a future delivery (name CCY-DDMMMYY) of BTC or ETH on that UTC day.
R-C4  Sets per window (DEC-103): E = all Fridays (W+M+Q) without outlier days; P2'' = Mon-Thu without outlier
      days and without futures days (in the pre-period: all Mon-Thu); P3fix = slot [15:30, 16:00) on Mon-Fri
      without month-end Fridays and without outlier days; P3all = per day (1/n_s) x sum of the n_s half-hour
      slots outside [07:00, 09:00) on Mon-Fri (n_s = 44; on month-end Fridays additionally without
      [14:00, 16:00) -> n_s = 40, CME reference windows GMT/BST, DEC-103 E6).  Weekend in no set.
      r_pre = ln(C[07:59]/C[07:29]), r_1530 = ln(C[15:59]/C[15:29]), half-hour slot s = ln(C[30s+29]/C[30s-1])
      with C[-1] = close 23:59 of the previous UTC day (missing on the first day of the extract -> that
      day has no P3all value).  Cluster x = (r_BTC + r_ETH)/2 in bp (1e4 x log return).
R-C5  Null J-(i) (DEC-103 E4): within each ISO week (restricted to the window) the Friday label is given to
      exactly one day of U_w = {Friday} u {P2'' days of the week}, uniformly; the other days of U_w are
      placebo; P2'' days in weeks without an event Friday stay placebo (fixed), Fridays of weeks without a
      P2'' day stay event (fixed); counts preserved.  R_REP = 20,000 replicates, seed 103 per window
      (window offset added).  The statistic of a replicate is the contrast event mean minus P2'' mean; ONLY
      its CENTRED value T(J) - E_perm[T] is ever formed and output (the centre E_perm[T] is a weighted sum of
      week-mean returns, i.e. a location: computed implicitly as week centring, never output, stored or
      printed).  Output: SD, distances of the quantiles from the centre d95/d99 in the registered direction
      (negative: d = -q_{0.05}(centred), -q_{0.01}) and in the other direction, excess kurtosis, skewness;
      exact SD / kurtosis / skewness from the cumulants of the uniform within-week draws (label-invariant)
      as a check of the Monte Carlo.
R-C6  Guard (Siegel).  The only function that forms a contrast from labels (``PermNull.centred_replicates``)
      derives the REAL label vector itself from the day dates (weekday == Friday), hashes it (sha256 of the
      uint8 bytes) and refuses (``RealLabelError``) any label row whose hash equals it - before any return
      value is touched; it also refuses rows that do not give exactly one event label per permutable week.
      The real contrast is never formed, also not in a test (tests use synthetic returns).  A pure P3 null
      under J-(i) is not simulated: T_P3(J) - E = N_P/(N_P + W) x (T_P2(J) - E) holds exactly (algebra, test on
      synthetic data); the P3 centre (time-of-day location) is never computed.
R-C7  Analytic SE (DEC-94 (3)/(4)/(5) (i), as Teil B R-9): SE(contrast) = sqrt(SE_E^2 + SE_P^2 - 2 Cov) with
      SE_k = SD_k sqrt(c_k / N_k); Cov from the measured same-day correlation of event slot and placebo slot on
      common days, used ONLY if it raises the SE (no credit).  c = c_bind of the pooled pre-period series by
      the P-3 rule (max(1, Bartlett 4/8/13, batch means 4/8/13 with n/L >= 8)); c = 1 as report.  Per
      pre-period window: class SDs of that window; for the test windows W1 (2024-07-01..2025-06-30) and W2
      (2025-07-01..2026-06-28): class SDs of the whole pre-period (central) and of the window with the
      largest SD (stress, report), N from the calendar.
R-C8  Binding SE (DEC-94 (5)): SE_bind = max(analytic central SE, null SD) per condition and window; the null
      SD for W1/W2 is transferred from the pre-period (pooled within-week variance sigma_w^2 x calendar
      structure of the test window: SD = (1/W + 1/N_P) sqrt(sigma_w^2 sum_w (n_w - 1)/n_w)); the null tail
      factor tau = d / SD_null is the largest of the three 12-month pre-period windows (strictness).
R-C9  Threshold (PRD 5.2 / DEC-103 E4): T = max(q95 of the null in registered direction; z_krit x SE_bind),
      z_krit = 1.6449 (P-1).  Power with power_p1 only; MDE80 single = max over the conditions of
      (T + 0.8416 SD) (DEC-94 (3)), product against {P2'', P3fix, P3all} with the null condition of P2'' as
      its own factor (product of single powers, N7 (4a)/DEC-103 E3); joint power (Monte Carlo) report only.
      Prior grid 5 / 8 / 12 / 16.5 / 25 bp, contrast scale and event scale (OI factor 0.842 on P2'').
R-C10 Funding (C-2): per symbol and UTC day of W2 the number and the UTC times of the funding timestamps;
      8h day = exactly {00:00, 08:00, 16:00}; counts per month; share of Fridays / Mon-Thu with a funding
      timestamp at 08:00:00 and of days with a timestamp in [07:00, 08:00).  No funding rate exists or is read.
R-C11 Pilot rule (C-3): no pilot number is computed (no mean); only thresholds, powers and error rates from
      nuisance quantities.
R-C12 Output: every output dict passes ``guard_keys`` (refuses mean / avg / mittel / median / q50 / sign /
      vorzeichen / effect / delta / drift / bias / centre / center / zentrum / loc / location / observed /
      beobachtet / real-contrast keys); ``print`` only sha256 and counts; deterministic (fixed seeds, sorted
      JSON, no time stamps; two runs bit-identical); ASCII only.
FASSUNG 2 (2026-10-31, after REVIEW_A2_TEILC.md; written before any new number):
R-C12a No dispersion of a UNION of two output classes of the same values, and no quantity from which it follows with
      calendar knowledge (review B-1: sd(E u P2'') next to sd(E), sd(P2''), n gives |contrast| by the variance
      decomposition).  Every class dispersion is output as {series, n, sd}; ``scan_variance_channels`` refuses the
      output if, within a block or across windows of the same series and class, n_k = n_i + n_j (or a sum of more
      classes) with all sd present; the union of E and P2'' is never formed for a dispersion.  The null-shift SD uses
      the pooled within-week SD (sigma_within, label-invariant; the union SD does not follow from it without the
      between-week sum of squares, which is not output).
R-C13 Test null scaling (orchestrator decision (b), DEC-101 E2 analogue): the test gate uses
      q95_eff = max(0, m) + k (q95 - m), k = max(1, SE_run / SD_null); in the power line k_W = max(1, SE_T,W / SD_null,W)
      and the tested centred statistic has SD k SD_null = SE_T (scaled-null logic); the pilot rule uses the same
      k_pred,W (U-4 literal: predicted real SE of the test window over its frozen null SD).
R-C14 Stress calibration binds (orchestrator decision (c), DEC-94 (5), precedent GL-032): class SDs and sigma_within of
      the 12-month pre-period window with the largest within-week SD (V1 2021-06..2022-05); central line = report.
R-C15 Gate (4) (orchestrator decision (f), provisional until negative-panel data): one factor 0.95 per negative symbol
      (XRP, BNB) in the product, i.e. 0.9025; label "vorlaeufig, bis Negativ-Panel-Daten" (UNBELEGT).
R-C16 Positive-control criterion (b) (orchestrator decision (e)): expected PASS share at the injection target (joint
      power of the test conditions, Monte Carlo, times the Gate-(4) factor) minus 2.3263 x binomial SE at 200 seeds.
R-C17 Exact bivariate P2'' condition (y >= z SE and y - max(0, m) >= k d95) is report only (orchestrator decision (a)).
R-C18 Funding (orchestrator decision (g)): the second funding extract (2021-03-24..2025-06-30, log key funding_pre_w1,
      only symbol / fts) is counted like R-C10 for the pre-period (pilot) and W1; the protective rule G-C8 is applied to
      pilot and test sets (count of affected days reported).
"""
from __future__ import annotations

import calendar
import hashlib
import importlib.util
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
RAW = Path("/home/user/scinance_work/hf_data/raw")
F_KLINE = RAW / "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet"
F_CAL = RAW / "deribit_settlements_CALENDAR_fields4_2017-05-25_2026-06-30.parquet"
F_FUND = RAW / "bybit_funding_timestamps_BTCUSDT_ETHUSDT_2025-07-01_2026-06-28.parquet"
F_FUND_PRE = RAW / "bybit_funding_timestamps_BTCUSDT_ETHUSDT_2021-03-24_2025-06-30.parquet"
F_LOG = RAW / "EXTRACT_LOG.json"
OUT_DIR = Path("/home/user/scinance/scinance3-impl/state/herleitung_a2")
POWER_P1 = Path("/home/user/scinance/src/bybit_edge/research/power_p1.py")
A2_VORARBEIT = OUT_DIR / "a2_vorarbeit.json"
A2_VORARBEIT_SHA = "9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052"

FIRST_RETURN_DAY = "2021-03-24"
LAST_RETURN_DAY = "2024-05-31"
LAST_CAL_DAY = "2026-06-30"
W2_FUND_FIRST, W2_FUND_LAST = "2025-07-01", "2026-06-28"
BP = 1e4
SEED_NULL = 103
R_REP = 20_000
SEED_MC = 1031
N_MC = 400_000

PRE_WINDOWS = {  # 12-month windows of the pre-period and the pooled pre-period (C-1)
    "V1_2021-06..2022-05": ("2021-06-01", "2022-05-31"),
    "V2_2022-06..2023-05": ("2022-06-01", "2023-05-31"),
    "V3_2023-06..2024-05": ("2023-06-01", "2024-05-31"),
    "VP_2021-03-24..2024-05-31": ("2021-03-24", "2024-05-31"),
}
TEST_WINDOWS = {"W1": ("2024-07-01", "2025-06-30"), "W2": ("2025-07-01", "2026-06-28")}

LABEL = ("A2-Vorarbeit Teil C (EXP-CLOCK, DEC-103): Null-Simulation J-(i), bindende SE, Funding-Intervall W2, "
         "Pilot-Uebergaberegel (Vorlage). Renditen nur 2021-03-24..2024-05-31 (1-min-Kerzen), Kalender nur "
         "<= 2026-06-30 (ohne Preisfelder), Funding-Zeitstempel nur W2 (ohne Rate). Ausgegeben werden nur "
         "Streuung, Quantil-Abstaende vom Null-Zentrum, Kurtosis, Zaehlungen, Schwellen und Powers; kein Mittel, "
         "kein Median, kein Vorzeichen irgendeiner Verfallstag-Rendite; der Kontrast mit den realen Labels wird "
         "nie gebildet (Waechter R-C6). Kein Verdikt, nichts registriert.")

MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
RE_OPT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})-([0-9d.]+)-([CP])$")
RE_FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")


# ------------------------------------------------------------------------------------------------ guards
class RealLabelError(RuntimeError):
    """R-C6: a label row equal to the real label vector (or malformed) reached the contrast function."""


_BAD_KEY = re.compile(
    r"(^|_)(mean|means|avg|average|mittel|mittelwert|median|q50|drift|bias|effect|effekt|delta|sign|signed|"
    r"vorzeichen|centre|center|zentrum|loc|location|observed|beobachtet|real_contrast|x_p|r_pre_mean)(_|$)",
    re.I)


def guard_keys(obj, path: str = "") -> None:
    """R-C12: refuse location-type keys anywhere in an output structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            ks = str(k)
            if _BAD_KEY.search(ks):
                raise ValueError(f"guard_keys: forbidden key {path}/{ks}")
            guard_keys(v, f"{path}/{ks}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            guard_keys(v, f"{path}[{i}]")


def _selftest_guard() -> None:
    for bad in ("mean", "r_pre_mean", "null_center", "q50", "median_x", "vorzeichen", "delta_bp", "sign"):
        try:
            guard_keys({bad: 1})
        except ValueError:
            continue
        raise AssertionError(f"guard_keys let {bad!r} pass")
    guard_keys({"null_sd": 1, "d95_reg": 2, "se_bind": 3, "n_placebo": 4, "power_product": 5})


_selftest_guard()


def label_hash(row: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(row, dtype=np.uint8).tobytes()).hexdigest()


class PermNull:
    """J-(i) null of one window (R-C5/R-C6).

    ``days``: sorted dates of U = E u P2'' of the window; ``is_event``: real event flag per day (must equal
    weekday == Friday - asserted).  Weeks = ISO weeks restricted to the window.  A week is permutable iff it
    holds an event Friday and at least one P2'' day.
    """

    def __init__(self, days: list[date], is_event: np.ndarray):
        self.days = list(days)
        self.n = len(self.days)
        ev = np.asarray(is_event, dtype=bool)
        fri = np.array([d.weekday() == 4 for d in self.days])
        if not np.array_equal(ev, fri):
            raise ValueError("event set must be exactly the Fridays of U")
        self._real_hash = label_hash(fri.astype(np.uint8))      # derived HERE from the dates, not passed in
        wk = [d.isocalendar()[:2] for d in self.days]
        keys = sorted(set(wk))
        self.week_of = np.array([keys.index(k) for k in wk])
        self.n_weeks_all = len(keys)
        self.event_weeks = sorted({self.week_of[i] for i in range(self.n) if fri[i]})
        self.W = int(fri.sum())                                   # number of event labels (preserved)
        self.N_P = self.n - self.W
        self.perm_weeks = [w for w in self.event_weeks if int((self.week_of == w).sum()) >= 2]
        self.fixed_event_weeks = [w for w in self.event_weeks if w not in self.perm_weeks]
        self.idx_of_week = {w: np.flatnonzero(self.week_of == w) for w in range(self.n_weeks_all)}
        self.n_w = np.array([len(self.idx_of_week[w]) for w in self.perm_weeks])
        self.a = 1.0 / self.W + 1.0 / self.N_P
        self.fixed_placebo_days = int(sum(len(self.idx_of_week[w]) for w in range(self.n_weeks_all)
                                          if w not in self.event_weeks))
        self._fri = fri

    # -------------------------------------------------------------- labels
    def draw_labels(self, n_rep: int, seed: int) -> np.ndarray:
        """Uniform within-week label draws (positions independent of which day is the real Friday)."""
        rng = np.random.default_rng(seed)
        L = np.zeros((n_rep, self.n), dtype=np.uint8)
        for w in self.fixed_event_weeks:
            L[:, self.idx_of_week[w]] = 1                        # Friday alone in its week: fixed event
        u = rng.random((n_rep, len(self.perm_weeks)))
        for j, w in enumerate(self.perm_weeks):
            ids = self.idx_of_week[w]
            pos = np.minimum((u[:, j] * len(ids)).astype(np.int64), len(ids) - 1)
            L[np.arange(n_rep), ids[pos]] = 1
        return L

    def check_labels(self, L: np.ndarray) -> None:
        """R-C6: refuse real rows and malformed rows BEFORE any return is touched."""
        L = np.asarray(L)
        if L.ndim != 2 or L.shape[1] != self.n:
            raise RealLabelError("label matrix has the wrong shape")
        if not np.all((L == 0) | (L == 1)):
            raise RealLabelError("labels must be 0/1")
        if not np.all(L.sum(axis=1) == self.W):
            raise RealLabelError("number of event labels not preserved")
        for w in self.event_weeks:
            if not np.all(L[:, self.idx_of_week[w]].sum(axis=1) == 1):
                raise RealLabelError("not exactly one event label in an event week")
        for w in range(self.n_weeks_all):
            if w not in self.event_weeks and np.any(L[:, self.idx_of_week[w]] != 0):
                raise RealLabelError("event label in a week without event Friday")
        for r in range(L.shape[0]):
            if label_hash(L[r]) == self._real_hash:
                raise RealLabelError(f"label row {r} equals the real label vector (hash) - refused")

    def _within_week_dev(self, x: np.ndarray) -> np.ndarray:
        """Deviation from the week mean in permutable weeks (internal centring, never output), 0 elsewhere."""
        dev = np.zeros(self.n)
        for w in self.perm_weeks:
            ids = self.idx_of_week[w]
            dev[ids] = x[ids] - x[ids].mean()
        return dev

    def centred_replicates(self, x: np.ndarray, L: np.ndarray) -> np.ndarray:
        """The ONLY contrast function: T(L) - E_perm[T] = a * sum_w (x_{w,J_w} - xbar_w).  Guard first."""
        self.check_labels(L)
        x = np.asarray(x, dtype=np.float64)
        if x.shape != (self.n,) or not np.all(np.isfinite(x)):
            raise ValueError("x must be finite with one value per day of U")
        return self.a * (L.astype(np.float64) @ self._within_week_dev(x))

    def exact_cumulants(self, x: np.ndarray) -> dict:
        """Label-invariant exact SD / skewness / excess kurtosis of the centred null (sum of independent
        uniform within-week draws)."""
        dev = self._within_week_dev(np.asarray(x, dtype=np.float64))
        k2 = k3 = k4 = 0.0
        for w in self.perm_weeks:
            d = dev[self.idx_of_week[w]]
            m2, m3, m4 = float(np.mean(d ** 2)), float(np.mean(d ** 3)), float(np.mean(d ** 4))
            k2 += m2
            k3 += m3
            k4 += m4 - 3.0 * m2 * m2
        a = self.a
        return {"sd": a * math.sqrt(k2), "skew": (k3 / k2 ** 1.5) if k2 > 0 else float("nan"),
                "excess_kurtosis": (k4 / k2 ** 2) if k2 > 0 else float("nan"),
                "sum_within_var_pop": k2}


def _collect_classes(obj, path=""):
    """All class-dispersion entries {series, n, sd} with their block path."""
    out = []
    if isinstance(obj, dict):
        if {"series", "n", "sd"} <= set(obj.keys()):
            out.append((path.rsplit("/", 1)[0], path.rsplit("/", 1)[-1], obj["series"], int(obj["n"]), obj["sd"]))
        for k, v in obj.items():
            out += _collect_classes(v, f"{path}/{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out += _collect_classes(v, f"{path}[{i}]")
    return out


def scan_variance_channels(obj, max_parts: int = 3) -> dict:
    """R-C12a: search the output for variance-decomposition channels.  Within every block (and across blocks for the
    same series and class name) look for n_k = sum of 2..max_parts other n of the SAME series with sd present.
    Different series with coinciding counts are listed (no decomposition between different variables)."""
    from itertools import combinations
    cls = _collect_classes(obj)
    viol, coinc = [], []
    blocks = {}
    for b, name, ser, n, sd in cls:
        blocks.setdefault(b, []).append((name, ser, n, sd))
    groups = {"block:" + b: v for b, v in blocks.items()}
    by_sc = {}
    for b, name, ser, n, sd in cls:
        by_sc.setdefault((ser, name), []).append((b + "/" + name, ser, n, sd))
    groups.update({f"series_class:{k[0]}|{k[1]}": v for k, v in by_sc.items()})
    for g, items in groups.items():
        uniq = {}
        for it in items:
            uniq.setdefault((it[1], it[2], round(float(it[3]), 9)), it)
        items = list(uniq.values())
        for k_it in items:
            others = [o for o in items if o is not k_it]
            for r in range(2, max_parts + 1):
                for comb in combinations(others, r):
                    if sum(o[2] for o in comb) == k_it[2]:
                        same = all(o[1] == k_it[1] for o in comb)
                        rec = {"group": g, "parent": k_it[0], "parts": [o[0] for o in comb],
                               "series": sorted({k_it[1], *(o[1] for o in comb)})}
                        (viol if same else coinc).append(rec)
    return {"class_entries": len(cls), "groups_scanned": len(groups), "violations": viol,
            "count_coincidences_different_series": coinc}


def assert_no_variance_channel(obj) -> dict:
    rep = scan_variance_channels(obj)
    if rep["violations"]:
        raise ValueError(f"R-C12a: variance-decomposition channel(s): {rep['violations'][:3]}")
    return rep


# ------------------------------------------------------------------------------------------------ io
def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _round(o):
    if isinstance(o, float):
        if not math.isfinite(o):
            return None
        return float(f"{o:.12g}")
    if isinstance(o, dict):
        return {str(k): _round(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_round(v) for v in o]
    if isinstance(o, (np.floating,)):
        return _round(float(o))
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def dump(obj, path: Path) -> str:
    guard_keys(obj)
    assert_no_variance_channel(obj)
    txt = json.dumps(_round(obj), sort_keys=True, indent=1, ensure_ascii=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt + "\n", encoding="ascii")
    return sha256(path)


def load_power_p1():
    spec = importlib.util.spec_from_file_location("power_p1_c", POWER_P1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LOG_KEY = {F_KLINE.name: "kline", F_CAL.name: "settlements", F_FUND.name: "funding", F_FUND_PRE.name: "funding_pre_w1"}


def check_inputs(names: list[str]) -> dict:
    """R-C2: sha256 of each input file must equal EXTRACT_LOG.json[<key>]["sha256"] (keys kline / settlements /
    funding); the log's row counts are reported alongside."""
    if not F_LOG.exists():
        raise RuntimeError("EXTRACT_LOG.json missing - inputs not released")
    log = json.loads(F_LOG.read_text(encoding="utf-8"))
    out = {}
    for nm in names:
        key = LOG_KEY[nm]
        h = sha256(RAW / nm)
        if log[key]["sha256"] != h:
            raise RuntimeError(f"sha256 of {nm} != EXTRACT_LOG.json[{key}]")
        out[nm] = {"sha256": h, "extract_log_key": key, "abgleich": "gleich",
                   "rows_log": log[key].get("rows")}
    return out


# ------------------------------------------------------------------------------------------------ calendar helpers
def last_friday(y: int, m: int) -> date:
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def cal_class(d: date) -> str:
    """DEC-98 N5 (3): weekday class without holiday shift."""
    if d.weekday() >= 5:
        return "WE"
    if d.weekday() != 4:
        return "MODO"
    if d != last_friday(d.year, d.month):
        return "FRI_W"
    return "FRI_Q" if d.month in (3, 6, 9, 12) else "FRI_M"


def is_month_end_friday(d: date) -> bool:
    return cal_class(d) in ("FRI_M", "FRI_Q")


def days_range(lo: str, hi: str) -> list[date]:
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    return [a + timedelta(i) for i in range((b - a).days + 1)]


def utc_day(ms: int) -> date:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date()


# ------------------------------------------------------------------------------------------------ kline
def assert_kline_dates(path=F_KLINE) -> dict:
    """R-C1: read ONLY symbol and start_ms; assert the day range before any price column is read."""
    t = pq.read_table(path, columns=["symbol", "start_ms"])
    mn, mx = pc.min(t.column("start_ms")).as_py(), pc.max(t.column("start_ms")).as_py()
    first, last = utc_day(mn).isoformat(), utc_day(mx).isoformat()
    if last > LAST_RETURN_DAY or first < FIRST_RETURN_DAY:
        raise RuntimeError(f"kline extract spans {first}..{last}, outside {FIRST_RETURN_DAY}..{LAST_RETURN_DAY}")
    syms = sorted(set(t.column("symbol").to_pylist()))
    if syms != ["BTCUSDT", "ETHUSDT"]:
        raise RuntimeError(f"unexpected symbols {syms}")
    return {"first_day": first, "last_day": last, "rows": t.num_rows}


def load_closes() -> tuple[list[date], dict[str, np.ndarray], dict]:
    """Close grid (n_days x 1440) per symbol; completeness checked; dates asserted first (R-C1)."""
    meta = assert_kline_dates()
    t = pq.read_table(F_KLINE, columns=["symbol", "start_ms", "close"])
    sym = np.asarray(t.column("symbol").to_pylist())
    ms = t.column("start_ms").to_numpy()
    cl = t.column("close").to_numpy()
    d0 = date.fromisoformat(FIRST_RETURN_DAY)
    days = days_range(FIRST_RETURN_DAY, meta["last_day"])
    assert days[-1].isoformat() <= LAST_RETURN_DAY
    nd = len(days)
    base = int(datetime(d0.year, d0.month, d0.day, tzinfo=timezone.utc).timestamp() * 1000)
    out, chk = {}, {}
    for s in ("BTCUSDT", "ETHUSDT"):
        m = sym == s
        k = (ms[m] - base) // 60000
        if np.any((ms[m] - base) % 60000 != 0):
            raise RuntimeError("start_ms off the minute grid")
        if k.min() < 0 or k.max() >= nd * 1440:
            raise RuntimeError("start_ms outside the day grid")
        grid = np.full(nd * 1440, np.nan)
        if np.unique(k).size != k.size:
            raise RuntimeError("duplicate minutes")
        grid[k] = cl[m]
        if not np.all(np.isfinite(grid)) or np.any(grid <= 0):
            raise RuntimeError(f"{s}: incomplete or non-positive closes")
        out[s] = grid.reshape(nd, 1440)
        chk[s] = {"rows": int(m.sum()), "days": nd}
    meta["per_symbol"] = chk
    return days, out, meta


def slot_returns(closes: np.ndarray) -> dict[str, np.ndarray]:
    """R-C4 returns per day in bp: pre, fix1530, half-hour profile (nd x 48; slot 0 of day 0 = NaN)."""
    nd = closes.shape[0]
    prev = np.full(nd, np.nan)
    prev[1:] = closes[:-1, 1439]
    prof = np.empty((nd, 48))
    for s in range(48):
        p0 = prev if s == 0 else closes[:, 30 * s - 1]
        prof[:, s] = BP * np.log(closes[:, 30 * s + 29] / p0)
    return {"pre": prof[:, 15], "fix1530": prof[:, 31], "profile": prof}


def p3all_value(prof: np.ndarray, month_end_friday: np.ndarray) -> np.ndarray:
    """R-C4: mean over the allowed half-hour slots of each day (a per-day dispersion input, never output)."""
    allowed = np.ones(48, bool)
    allowed[14:18] = False                                   # [07:00, 09:00)
    cme = allowed.copy()
    cme[28:32] = False                                       # [14:00, 16:00) on month-end Fridays
    v = np.where(month_end_friday, (prof[:, cme]).sum(axis=1) / cme.sum(), (prof[:, allowed]).sum(axis=1) / allowed.sum())
    return v


# ------------------------------------------------------------------------------------------------ c rule
def batch_means_c(x: np.ndarray, L: int) -> float:
    m = x.size // L
    bm = x[: m * L].reshape(m, L).mean(axis=1)
    return float(L * np.var(bm, ddof=1) / np.var(x, ddof=1))


def c_bind(x: np.ndarray, power_p1) -> dict:
    """P-3 rule as Teil B R-8: c_bind = max(1, Bartlett 4/8/13, batch means 4/8/13 with n/L >= 8)."""
    x = x[np.isfinite(x)]
    n = x.size
    bart = {str(b): power_p1.variance_factor(x, b).c_hat for b in (4, 8, 13) if n >= b + 2}
    bm = {str(L): batch_means_c(x, L) for L in (4, 8, 13) if n // L >= 8}
    return {"n": int(n), "c_bartlett": bart, "c_batch": bm,
            "c_bind": float(max(1.0, *bart.values(), *bm.values()))}


# ------------------------------------------------------------------------------------------------ settlement calendar
CAL_COLUMNS = {"ccy", "type", "instrument_name", "timestamp", "position"}
CAL_READ = ["ccy", "type", "instrument_name", "timestamp"]


def _ms(v: np.ndarray) -> np.ndarray:
    """Timestamp column to ms (accepts s / ms / us / ns by magnitude)."""
    v = np.asarray(v, dtype=np.int64)
    mx = int(np.max(v))
    if mx > 10 ** 17:
        return v // 1_000_000
    if mx > 10 ** 14:
        return v // 1_000
    if mx > 10 ** 11:
        return v
    return v * 1000


def load_calendar_flags() -> tuple[dict[date, dict], dict]:
    """R-C1/R-C3: per UTC day <= 2026-06-30: BTC/ETH option delivery present, outlier (option delivery
    > 60 s after 08:00:00), futures delivery per currency.  Only ccy/type/instrument_name/timestamp read."""
    schema_cols = set(pq.ParquetFile(F_CAL).schema_arrow.names)
    if schema_cols != CAL_COLUMNS:
        raise RuntimeError(f"calendar columns {sorted(schema_cols)} != {sorted(CAL_COLUMNS)}")
    t = pq.read_table(F_CAL, columns=CAL_READ)
    ts = t.column("timestamp")
    if pa_is_timestamp(ts.type):
        raw = np.asarray(ts.cast("int64").to_numpy(), dtype=np.int64)
        unit = ts.type.unit
        ms = raw * 1000 if unit == "s" else raw if unit == "ms" else raw // 1000 if unit == "us" else raw // 1_000_000
    else:
        ms = _ms(ts.to_numpy())
    last = utc_day(int(ms.max()))
    if last.isoformat() > LAST_CAL_DAY:
        raise RuntimeError(f"calendar contains {last} > {LAST_CAL_DAY}")
    ccy = t.column("ccy").to_pylist()
    typ = t.column("type").to_pylist()
    name = t.column("instrument_name").to_pylist()
    # orchestrator note 2026-10-31: column ccy carries the instrument name, not the currency; the currency is
    # derived from the name prefix (BTC-... / ETH-...) via RE_OPT / RE_FUT; ccy is only checked for identity
    n_ccy_eq_name = sum(1 for a, b in zip(ccy, name) if a == b)
    flags: dict[date, dict] = {}
    n_opt = n_fut = n_name_mismatch = 0
    types = {}
    for c, ty, nm, m in zip(ccy, typ, name, ms.tolist()):
        types[ty] = types.get(ty, 0) + 1
        if ty != "delivery":
            continue
        d = utc_day(m)
        f = flags.setdefault(d, {"opt_BTC": False, "opt_ETH": False, "fut_BTC": False, "fut_ETH": False,
                                 "max_delay_s": 0.0})
        mo, mf = RE_OPT.match(nm or ""), RE_FUT.match(nm or "")
        if mo:
            exp = date(2000 + int(mo.group(4)), MON[mo.group(3)], int(mo.group(2)))
            if exp != d:
                n_name_mismatch += 1
            f[f"opt_{mo.group(1)}"] = True
            day0 = int(datetime(d.year, d.month, d.day, 8, tzinfo=timezone.utc).timestamp() * 1000)
            f["max_delay_s"] = max(f["max_delay_s"], (m - day0) / 1000.0)
            n_opt += 1
        elif mf:
            exp = date(2000 + int(mf.group(4)), MON[mf.group(3)], int(mf.group(2)))
            if exp != d:
                n_name_mismatch += 1
            f[f"fut_{mf.group(1)}"] = True
            n_fut += 1
    meta = {"rows": t.num_rows, "ccy_equals_instrument_name_rows": n_ccy_eq_name,
            "currency_source": "Namenspraefix BTC-/ETH- (Spalte ccy = Instrumentname, nicht benutzt)",
            "rows_by_type": types, "option_deliveries": n_opt, "future_deliveries": n_fut,
            "name_date_mismatch": n_name_mismatch, "last_day": last.isoformat(),
            "first_day": min(flags).isoformat() if flags else None}
    return flags, meta


def pa_is_timestamp(tp) -> bool:
    import pyarrow as pa
    return pa.types.is_timestamp(tp)


def day_flags(d: date, flags: dict) -> dict:
    f = flags.get(d)
    if f is None:
        return {"opt_both": False, "outlier": False, "fut_any": False}
    return {"opt_both": f["opt_BTC"] and f["opt_ETH"], "outlier": f["max_delay_s"] > 60.0,
            "fut_any": f["fut_BTC"] or f["fut_ETH"]}


def window_sets(lo: str, hi: str, flags: dict) -> dict[str, list[date]]:
    """R-C4 sets of a window from the calendar (no returns)."""
    E, P2, P3fix, P3all, bad = [], [], [], [], []
    for d in days_range(lo, hi):
        if d.weekday() >= 5:
            continue
        fl = day_flags(d, flags)
        if not fl["opt_both"]:
            bad.append(d)
            continue
        if fl["outlier"]:
            continue
        P3all.append(d)
        if not is_month_end_friday(d):
            P3fix.append(d)
        if d.weekday() == 4:
            E.append(d)
        elif not fl["fut_any"]:
            P2.append(d)
    if bad:
        raise RuntimeError(f"days without BTC+ETH option delivery: {bad[:5]}")
    return {"E": E, "P2ss": P2, "P3fix": P3fix, "P3all": P3all}
