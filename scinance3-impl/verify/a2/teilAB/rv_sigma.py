"""Independent review recomputation (A2 preparatory work): sigma30 / rho / ACF / c of r_pre on the
local 1-min extracts.  DISPERSION ONLY.  No mean, median or sign of any slot return or difference is
output, stored or printed (centering happens only inside SD / correlation / ACF).

Own implementation (does not import the derivation's modules).  Rules:
  * assert on start_ms (read alone, before any price column): no UTC day > 2024-05-31;
  * day classes from the weekday / last-Friday rule (DEC-98 N5 class rule), independent code;
  * r_pre = ln(C[07:59] / C[07:29]) (close of the candle starting 07:59 vs. 07:29), bp;
  * output dict passes a key guard (mean/median/avg/sign/... refused).
"""
from __future__ import annotations

import calendar
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq
from scipy import stats

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1  # noqa: E402

D = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw")
F = {"BTC": D / "bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet",
     "ETH": D / "bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet"}
OUT = Path(__file__).resolve().parent / "rv_sigma.json"
LAST = date(2024, 5, 31)
FIRST = date(2021, 3, 24)
MS_DAY, MS_MIN = 86_400_000, 60_000
BP = 1e4
SEED = 4711          # deliberately different from the derivation (27): band plausibility, not replay
NREP = 2000

_BAD = re.compile(r"mean|median|avg|average|mittel|sign|vorzeichen|drift|effect|delta|loc\b|center|centre", re.I)


def guard(d, path=""):
    if isinstance(d, dict):
        for k, v in d.items():
            if _BAD.search(str(k)):
                raise RuntimeError(f"review guard: key {path}/{k} refused")
            guard(v, f"{path}/{k}")
    elif isinstance(d, (list, tuple)):
        for v in d:
            guard(v, path)
    return d


def load(sym: str):
    ms_only = pq.read_table(F[sym], columns=["start_ms"]).column("start_ms")
    mx = pc.max(ms_only).as_py()
    mn = pc.min(ms_only).as_py()
    last_day = datetime.fromtimestamp(mx / 1000, tz=timezone.utc).date()
    first_day = datetime.fromtimestamp(mn / 1000, tz=timezone.utc).date()
    assert last_day <= LAST, f"{sym}: day {last_day} > {LAST} -- refused before any price is read"
    assert first_day >= FIRST
    t = pq.read_table(F[sym], columns=["start_ms", "open", "close"])
    ms = t.column("start_ms").to_numpy()
    assert (ms % MS_MIN == 0).all()
    d0 = (date(2021, 3, 24) - date(1970, 1, 1)).days
    di = ms // MS_DAY - d0
    mi = (ms % MS_DAY) // MS_MIN
    nd = (last_day - FIRST).days + 1
    close = np.full((nd, 1440), np.nan)
    opn = np.full((nd, 1440), np.nan)
    # duplicate minutes would overwrite silently -> count them
    key = di * 1440 + mi
    n_dup = int(key.size - np.unique(key).size)
    close[di, mi] = t.column("close").to_numpy()
    opn[di, mi] = t.column("open").to_numpy()
    complete = np.isfinite(close).all(axis=1) & (close > 0).all(axis=1)
    days = [FIRST + timedelta(i) for i in range(nd)]
    return days, close, opn, complete, {"rows": int(ms.size), "dup_minutes": n_dup,
                                         "first_day": str(first_day), "last_day": str(last_day),
                                         "complete_days": int(complete.sum()), "days": nd}


def last_friday(y, m):
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() != 4:
        d -= timedelta(1)
    return d


def fine_class(d: date) -> str:
    if d.weekday() == 4:
        if d == last_friday(d.year, d.month):
            return "FRI_Q" if d.month % 3 == 0 else "FRI_M"
        return "FRI_W"
    return "WE" if d.weekday() >= 5 else "MODO"


SETS = {"FRI": {"FRI_W", "FRI_M", "FRI_Q"}, "FRI_W": {"FRI_W"}, "FRI_M": {"FRI_M"}, "FRI_Q": {"FRI_Q"},
        "FRI_MQ": {"FRI_M", "FRI_Q"}, "MODO": {"MODO"}, "WE": {"WE"}, "NONFRI": {"MODO", "WE"},
        "ALL": {"FRI_W", "FRI_M", "FRI_Q", "MODO", "WE"}}


def slot(close, complete, a, b):
    """bp log return over [a, b) minutes-of-day: close of candle b-1 over close of candle a-1."""
    if a == 0:
        p0 = np.r_[np.nan, close[:-1, 1439]]
        ok0 = np.r_[False, complete[:-1]]
    else:
        p0 = close[:, a - 1]
        ok0 = np.ones(close.shape[0], bool)
    r = BP * np.log(close[:, b - 1] / p0)
    r[~(complete & ok0)] = np.nan
    return r


def acf(x, k):
    d = x - x.mean()          # internal centering only
    return float(d[k:] @ d[:-k] / (d @ d))


def bartlett_c(x, B):
    d = x - x.mean()
    n = x.size
    g0 = d @ d / n
    lrv = g0 + sum(2 * (1 - k / (B + 1)) * (d[k:] @ d[:-k]) / n for k in range(1, B + 1))
    return float(lrv / g0)


def bm_c(x, L):
    m = x.size // L
    blocks = x[: m * L].reshape(m, L).sum(axis=1) / L
    return float(L * np.var(blocks, ddof=1) / np.var(x, ddof=1))


def main():
    days, cl, op, comp = {}, {}, {}, {}
    meta = {}
    for s in ("BTC", "ETH"):
        days[s], cl[s], op[s], comp[s], meta[s] = load(s)
    assert days["BTC"] == days["ETH"]
    dl = days["BTC"]
    fine = np.array([fine_class(d) for d in dl])
    yr = np.array([d.year for d in dl])
    mask = {k: np.isin(fine, list(v)) for k, v in SETS.items()}
    r = {}
    for s in ("BTC", "ETH"):
        r[s] = {"pre": slot(cl[s], comp[s], 450, 480), "fix1530": slot(cl[s], comp[s], 930, 960),
                "pre_oc": BP * np.log(cl[s][:, 479] / op[s][:, 450])}
        prof = np.vstack([slot(cl[s], comp[s], 30 * j, 30 * j + 30) for j in range(48)]).T
        keep = [j for j in range(48) if j not in (14, 15, 16, 17)]
        r[s]["p3all"] = prof[:, keep].sum(axis=1) / len(keep)
    clu = {k: 0.5 * (r["BTC"][k] + r["ETH"][k]) for k in r["BTC"]}
    clu["pairdiff"] = clu["pre"] - clu["fix1530"]

    out = {"meta": meta, "class_days": {k: int(m.sum()) for k, m in mask.items()}}
    disp = {}
    for k, m in mask.items():
        b, e, x = r["BTC"]["pre"][m], r["ETH"]["pre"][m], clu["pre"][m]
        ok = np.isfinite(b) & np.isfinite(e)
        b, e, x = b[ok], e[ok], x[ok]
        sb, se_ = float(np.std(b, ddof=1)), float(np.std(e, ddof=1))
        cell = {"n": int(b.size), "sd_btc": sb, "sd_eth": se_, "sd_pooled": float(np.sqrt((sb**2 + se_**2) / 2)),
                "sd_cluster": float(np.std(x, ddof=1)), "rho_pearson": float(np.corrcoef(b, e)[0, 1]),
                "rho_spearman": float(stats.spearmanr(b, e).statistic),
                "kurt_excess_btc": float(stats.kurtosis(b, fisher=True, bias=True)),
                "acf_cluster": [acf(x, j) for j in range(1, 11)],
                "c_bartlett_own": {B: bartlett_c(x, B) for B in (4, 8, 13) if x.size >= B + 2},
                "c_bartlett_power_p1": {B: power_p1.variance_factor(x, B).c_hat for B in (4, 8, 13) if x.size >= B + 2},
                "c_bm": {L: bm_c(x, L) for L in (4, 8, 13) if x.size // L >= 8}}
        cands = list(cell["c_bartlett_own"].values()) + list(cell["c_bm"].values())
        cell["c_bind"] = max(1.0, *cands)
        cell["sd_cluster_by_year"] = {int(y): float(np.std(clu["pre"][m & (yr == y) & np.isfinite(clu["pre"])], ddof=1))
                                      for y in (2021, 2022, 2023, 2024)}
        disp[k] = cell
    out["pre"] = disp
    # other series (cluster)
    oth = {}
    for name, ser, cls in (("fix1530", clu["fix1530"], ("ALL", "MODO", "FRI")),
                           ("p3all", clu["p3all"], ("ALL",)),
                           ("pairdiff_pre_minus_1530", clu["pairdiff"], ("FRI",)),
                           ("pre_oc", clu["pre_oc"], ("ALL",))):
        cc = {}
        for k in cls:
            x = ser[mask[k] & np.isfinite(ser)]
            cands = [bartlett_c(x, B) for B in (4, 8, 13)] + [bm_c(x, L) for L in (4, 8, 13) if x.size // L >= 8]
            cc[k] = {"n": int(x.size), "sd_cluster": float(np.std(x, ddof=1)), "c_bind": max(1.0, *cands)}
        oth[name] = cc
    out["other_series"] = oth
    # week-block bootstrap of pooled SD ratios (own seed)
    wk = np.array([d.isocalendar()[0] * 100 + d.isocalendar()[1] for d in dl])
    uw, widx = np.unique(wk, return_inverse=True)
    W = uw.size
    rng = np.random.default_rng(SEED)
    cnt = rng.multinomial(W, np.full(W, 1 / W), size=NREP).astype(float)

    def sd_reps(x, m):
        ok = m & np.isfinite(x)
        xv = np.where(ok, x, 0.0)
        agg = lambda v: np.bincount(widx, weights=v, minlength=W)
        n = cnt @ agg(ok.astype(float))
        s1 = cnt @ agg(xv)
        s2 = cnt @ agg(xv * xv)
        return np.sqrt((s2 - s1 * s1 / n) / (n - 1))

    def pooled_reps(cls):
        return np.sqrt((sd_reps(r["BTC"]["pre"], mask[cls]) ** 2 + sd_reps(r["ETH"]["pre"], mask[cls]) ** 2) / 2)

    bands = {}
    for a, b in (("FRI", "MODO"), ("FRI_MQ", "FRI_W"), ("WE", "MODO"), ("FRI_W", "MODO")):
        rep = pooled_reps(a) / pooled_reps(b)
        bands[f"{a}/{b}"] = {"point": disp[a]["sd_pooled"] / disp[b]["sd_pooled"],
                             "q025": float(np.quantile(rep, 0.025)), "q975": float(np.quantile(rep, 0.975))}
    out["pooled_ratio_bands_seed4711"] = bands
    out["corr_pre_cc_oc_cluster"] = float(np.corrcoef(clu["pre"][np.isfinite(clu["pre"])],
                                                      clu["pre_oc"][np.isfinite(clu["pre"])])[0, 1])
    guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == "__main__":
    o = main()
    print("written", OUT)
