"""Review A2 Teil C (adversarial, independent code).  Shared loaders and guards.

Rules of this review code (binding, written before any number):
  RV-1  Returns only from the 1-min extract 2021-03-24..2024-05-31; the day range is asserted on
        symbol/start_ms ALONE before the close column is read, and again on the day grid before any
        price array is formed.
  RV-2  Calendar: only type / instrument_name / timestamp / ccy (identity check of ccy only); the
        column `position` is never read; no row after 2026-06-30 (assert).  Currency from the name prefix.
  RV-3  Funding: only symbol / fts, only UTC days 2025-07-01..2026-06-28 (assert).
  RV-4  No mean, no median, no sign of any expiry-day return; the contrast with the real labels is
        never formed (not even as a probe).  The null is built from within-week deviations only; the
        real Friday positions are used ONLY to check that no replicate equals the real labelling.
  RV-5  Outputs pass `guard_keys`; print only sha256 and counts; fixed seeds (different from the
        derivation: null 7001+k, joint MC 9001+k); ASCII.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl

RAW = Path("/home/user/scinance_work/hf_data/raw")
KL = RAW / "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet"
CAL = RAW / "deribit_settlements_CALENDAR_fields4_2017-05-25_2026-06-30.parquet"
FUND = RAW / "bybit_funding_timestamps_BTCUSDT_ETHUSDT_2025-07-01_2026-06-28.parquet"
LOG = RAW / "EXTRACT_LOG.json"
HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
POWER_P1 = Path("/home/user/scinance/src/bybit_edge/research/power_p1.py")

D_LO, D_HI = date(2021, 3, 24), date(2024, 5, 31)
CAL_HI = date(2026, 6, 30)
W2_LO, W2_HI = date(2025, 7, 1), date(2026, 6, 28)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

_BAD = re.compile(r"(^|_)(mean|avg|mittel|median|q50|drift|bias|effect|effekt|delta|sign|vorzeichen|centre|"
                  r"center|zentrum|loc|location|observed|beobachtet|real_contrast|x_p)(_|$)", re.I)


def guard_keys(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if _BAD.search(str(k)):
                raise ValueError(f"forbidden key {p}/{k}")
            guard_keys(v, f"{p}/{k}")
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            guard_keys(v, f"{p}[{i}]")


def sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def r6(o):
    if isinstance(o, float):
        return None if not math.isfinite(o) else float(f"{o:.6g}")
    if isinstance(o, dict):
        return {str(k): r6(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [r6(v) for v in o]
    if isinstance(o, np.floating):
        return r6(float(o))
    if isinstance(o, np.integer):
        return int(o)
    return o


def dump(obj, path: Path) -> str:
    guard_keys(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(r6(obj), sort_keys=True, indent=1, ensure_ascii=True) + "\n", encoding="ascii")
    return sha(path)


def ms_day(ms: int) -> date:
    return (EPOCH + timedelta(milliseconds=int(ms))).date()


def drange(lo: date, hi: date):
    return [lo + timedelta(i) for i in range((hi - lo).days + 1)]


def last_friday(y: int, m: int) -> date:
    d = date(y + (m == 12), m % 12 + 1, 1) - timedelta(1)
    return d - timedelta((d.weekday() - 4) % 7)


def month_end_friday(d: date) -> bool:
    return d.weekday() == 4 and d == last_friday(d.year, d.month)


def check_hashes() -> dict:
    log = json.loads(LOG.read_text())
    out = {}
    for key, p in (("kline", KL), ("settlements", CAL), ("funding", FUND)):
        h = sha(p)
        assert h == log[key]["sha256"], key
        out[p.name] = h
    return out


# ------------------------------------------------------------------ kline (RV-1)
def load_cluster_series() -> dict:
    head = pl.read_parquet(KL, columns=["symbol", "start_ms"])
    lo, hi = ms_day(head["start_ms"].min()), ms_day(head["start_ms"].max())
    assert lo >= D_LO and hi <= D_HI, (lo, hi)                        # RV-1, before any price column
    assert sorted(head["symbol"].unique().to_list()) == ["BTCUSDT", "ETHUSDT"]
    days = drange(D_LO, hi)
    nd = len(days)
    assert days[-1] <= D_HI                                            # RV-1, second assert (day grid)
    base = int((datetime(D_LO.year, D_LO.month, D_LO.day, tzinfo=timezone.utc) - EPOCH).total_seconds() * 1000)
    out = {}
    for s in ("BTCUSDT", "ETHUSDT"):
        q = (pl.scan_parquet(KL).select(["symbol", "start_ms"]).filter(pl.col("symbol") == s)
             .sort("start_ms").collect())
        st = q["start_ms"].to_numpy()
        assert st.size == nd * 1440 and np.array_equal(st, base + 60000 * np.arange(nd * 1440, dtype=np.int64))
        assert ms_day(st[-1]) <= D_HI
        c = (pl.scan_parquet(KL).select(["symbol", "start_ms", "close"]).filter(pl.col("symbol") == s)
             .sort("start_ms").collect()["close"].to_numpy().reshape(nd, 1440))
        assert np.all(np.isfinite(c)) and np.all(c > 0)
        prev = np.r_[np.nan, c[:-1, 1439]]
        lc = np.log(c)
        lprev = np.log(prev)
        pre = lc[:, 479] - lc[:, 449]                                  # [07:30, 08:00)
        f1530 = lc[:, 959] - lc[:, 929]                                # [15:30, 16:00)
        ends = lc[:, 29::30]                                          # close of minute 30s+29, s = 0..47
        starts = np.column_stack([lprev, lc[:, 29:1439:30]])           # close of minute 30s-1 (prev day for s=0)
        prof = ends - starts
        out[s] = {"pre": pre, "f1530": f1530, "prof": prof}
    me = np.array([month_end_friday(d) for d in days])
    keep = np.ones(48, bool)
    keep[14:18] = False                                                # [07:00, 09:00)
    keep_me = keep.copy()
    keep_me[28:32] = False                                             # [14:00, 16:00) at month-end Fridays
    def p3(prof):
        a = prof[:, keep].mean(axis=1)                                 # per-day average of slot returns (dispersion input)
        b = prof[:, keep_me].mean(axis=1)
        return np.where(me, b, a)
    X = {"pre": 5e3 * (out["BTCUSDT"]["pre"] + out["ETHUSDT"]["pre"]),
         "f1530": 5e3 * (out["BTCUSDT"]["f1530"] + out["ETHUSDT"]["f1530"]),
         "p3all": 5e3 * (p3(out["BTCUSDT"]["prof"]) + p3(out["ETHUSDT"]["prof"]))}
    return {"days": days, "X": X, "n_rows": int(head.height)}


# ------------------------------------------------------------------ calendar (RV-2)
MONTHS = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
R_OPT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})-[0-9d.]+-[CP]$")
R_FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")


def load_calendar() -> tuple[dict, dict]:
    names = set(pl.read_parquet_schema(CAL).keys())
    assert names == {"ccy", "type", "instrument_name", "timestamp", "position"}, names
    t = pl.read_parquet(CAL, columns=["ccy", "type", "instrument_name", "timestamp"])
    ts = t["timestamp"].to_numpy().astype(np.int64)
    mx = int(ts.max())
    unit_div = 1000 if mx > 10 ** 14 else 1                            # us -> ms
    ms = ts // unit_div
    assert ms_day(int(ms.max())) <= CAL_HI
    flags = {}
    n_ccy_eq = int((t["ccy"] == t["instrument_name"]).sum())
    mism = 0
    for ty, nm, m in zip(t["type"].to_list(), t["instrument_name"].to_list(), ms.tolist()):
        if ty != "delivery":
            continue
        d = ms_day(m)
        f = flags.setdefault(d, {"oB": 0, "oE": 0, "fB": 0, "fE": 0, "late": 0})
        mo, mf = R_OPT.match(nm), R_FUT.match(nm)
        mm = mo or mf
        exp = date(2000 + int(mm.group(4)), MONTHS[mm.group(3)], int(mm.group(2)))
        mism += exp != d
        if mo:
            f["oB" if mo.group(1) == "BTC" else "oE"] += 1
            t8 = int((datetime(d.year, d.month, d.day, 8, tzinfo=timezone.utc) - EPOCH).total_seconds() * 1000)
            if m - t8 > 60_000:
                f["late"] += 1
        else:
            f["fB" if mf.group(1) == "BTC" else "fE"] += 1
    meta = {"rows": t.height, "ccy_equals_name_rows": n_ccy_eq, "name_date_mismatch": mism,
            "ts_unit_divisor_to_ms": unit_div}
    return flags, meta


def fl(flags, d):
    f = flags.get(d, {"oB": 0, "oE": 0, "fB": 0, "fE": 0, "late": 0})
    return {"opt_both": f["oB"] > 0 and f["oE"] > 0, "outlier": f["late"] > 0, "fut": f["fB"] + f["fE"] > 0}


def sets_of(lo: date, hi: date, flags) -> dict:
    S = {"E": [], "P2ss": [], "P3fix": [], "P3all": []}
    for d in drange(lo, hi):
        if d.weekday() >= 5:
            continue
        f = fl(flags, d)
        assert f["opt_both"], d
        if f["outlier"]:
            continue
        S["P3all"].append(d)
        if not month_end_friday(d):
            S["P3fix"].append(d)
        if d.weekday() == 4:
            S["E"].append(d)
        elif not f["fut"]:
            S["P2ss"].append(d)
    return S


# ------------------------------------------------------------------ null J-(i) (RV-4)
class Null:
    def __init__(self, E: list, P: list):
        self.U = sorted(E + P)
        self.W, self.NP = len(E), len(P)
        self.a = 1.0 / self.W + 1.0 / self.NP
        wk = {}
        for i, d in enumerate(self.U):
            wk.setdefault(d.isocalendar()[:2], []).append(i)
        self.perm, self.fix_ev, self.fix_pl = [], [], []
        for ids in wk.values():
            fri = [i for i in ids if self.U[i].weekday() == 4]
            assert len(fri) <= 1
            if fri and len(ids) >= 2:
                self.perm.append(np.array(ids))
            elif fri:
                self.fix_ev.append(ids)
            else:
                self.fix_pl.append(ids)
        self.nw = np.array([len(i) for i in self.perm])
        self.kappa = self.a * float(np.sum((self.nw - 1) / self.nw))
        self._fri_pos = np.array([[k for k, i in enumerate(ids) if self.U[i].weekday() == 4][0] for ids in self.perm])

    def draws(self, R: int, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed)
        J = np.column_stack([rng.integers(0, n, size=R) for n in self.nw])
        # RV-4 guard: no replicate may coincide with the real labelling in all permutable weeks
        real_rows = np.all(J == self._fri_pos[None, :], axis=1)
        if real_rows.any():
            raise RuntimeError("replicate equal to the real labelling - refused")
        return J

    def devs(self, x: np.ndarray):
        return [x[ids] - x[ids].mean() for ids in self.perm]          # within-week centring (internal only)

    def replicates(self, x: np.ndarray, J: np.ndarray) -> np.ndarray:
        dv = self.devs(x)
        v = np.zeros(J.shape[0])
        for k, d in enumerate(dv):
            v += d[J[:, k]]
        return self.a * v

    def exact(self, x: np.ndarray, h: float = 0.02) -> dict:
        dv = self.devs(x)
        k2 = sum(float(np.mean(d ** 2)) for d in dv)
        k3 = sum(float(np.mean(d ** 3)) for d in dv)
        k4 = sum(float(np.mean(d ** 4)) - 3 * float(np.mean(d ** 2)) ** 2 for d in dv)
        # exact distribution of sum_w dev_{J_w} by FFT convolution on a grid of step h (in un-scaled units)
        offs = [float(-d.min()) for d in dv]
        span = sum(float(d.max() - d.min()) for d in dv)
        n = 1
        while n < span / h + 10:
            n *= 2
        n *= 2
        acc = np.ones(n // 2 + 1, dtype=np.complex128)
        for d, o in zip(dv, offs):
            pm = np.zeros(n)
            np.add.at(pm, np.rint((d + o) / h).astype(np.int64), 1.0 / d.size)
            acc *= np.fft.rfft(pm)
        pmf = np.clip(np.fft.irfft(acc, n), 0, None)
        pmf /= pmf.sum()
        grid = (np.arange(n) * h - sum(offs)) * self.a
        cdf = np.cumsum(pmf)
        def q(p):
            return float(np.interp(p, cdf, grid))
        return {"sd": self.a * math.sqrt(k2), "skew": k3 / k2 ** 1.5, "exkurt": k4 / k2 ** 2,
                "q01": q(0.01), "q05": q(0.05), "q95": q(0.95), "q99": q(0.99), "k2": k2,
                "grid_step_scaled": h * self.a}


# ------------------------------------------------------------------ variance factor (P-3 rule, own code)
def bartlett(x: np.ndarray, B: int) -> float:
    d = x - x.mean()
    n = d.size
    g0 = float(d @ d) / n
    s = g0 + sum(2 * (1 - k / (B + 1)) * float(d[k:] @ d[:-k]) / n for k in range(1, B + 1))
    return s / g0


def batch(x: np.ndarray, L: int) -> float:
    m = x.size // L
    b = x[: m * L].reshape(m, L).mean(axis=1)
    return L * float(np.var(b, ddof=1)) / float(np.var(x, ddof=1))


def c_rule(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    cand = [bartlett(x, B) for B in (4, 8, 13)] + [batch(x, L) for L in (4, 8, 13) if x.size // L >= 8]
    return max(1.0, *cand)


def load_power_p1():
    import importlib.util
    sp = importlib.util.spec_from_file_location("power_p1_review", POWER_P1)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m
