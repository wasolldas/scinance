"""Part B-1..B-3: sigma30 nuisance of the pre-period 2021-03-24..2024-05-31 from 1-min candles -- ONLY
dispersion, correlation, autocorrelation and variance factors (R-3..R-8).  No mean, no sign.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2v_common as c  # noqa: E402
from bybit_edge.research import power_p1  # noqa: E402

BP = 1e4
CLASSES = ("FRI", "FRI_W", "FRI_M", "FRI_Q", "FRI_MQ", "MODO", "WE", "NONFRI", "ALL")
YEARS = ("2021", "2022", "2023", "2024")
SHIFTS = (-3, -2, -1, 1, 2, 3)
EXCL_P3ALL = {14, 15, 16, 17}          # [07:00, 09:00) excluded from the P3 baseline average
LAGS = list(range(1, 11))


# ---------------------------------------------------------------------------------------------- data
def load() -> dict:
    for s in ("BTC", "ETH"):
        c.assert_kline_dates(c.hc.KLINE[s])                  # R-13: start_ms only, before any price column
    kl = {s: c.hc.load_kline(s) for s in ("BTC", "ETH")}     # asserts: no day > 2024-05-31 (R-1)
    days = kl["BTC"]["days"]
    assert days == kl["ETH"]["days"]
    assert days[0] == c.FIRST_RETURN_DAY and days[-1] <= c.LAST_RETURN_DAY, (days[0], days[-1])
    c.assert_rv_day(days[-1])
    for s in ("BTC", "ETH"):
        assert kl[s]["complete"].all(), f"incomplete days {s}: {kl[s]['meta']['incomplete_days']}"
    return kl


def slot_returns(closes: np.ndarray, opens: np.ndarray, complete: np.ndarray) -> dict:
    """R-3: r = ln(C[end-1] / C[start-1]) per day (bp); start-1 = -1 -> previous day's 23:59 close."""
    nd = closes.shape[0]
    prev_last = np.full(nd, np.nan)
    prev_last[1:] = closes[:-1, 1439]
    ok_prev = np.zeros(nd, bool)
    ok_prev[1:] = complete[:-1]

    def r(start: int, end: int) -> np.ndarray:
        p1 = closes[:, end - 1]
        p0 = prev_last if start == 0 else closes[:, start - 1]
        out = BP * np.log(p1 / p0)
        bad = ~complete | ((start == 0) & ~ok_prev)
        out[bad] = np.nan
        return out

    res = {"pre": r(450, 480), "post60": r(480, 540), "fix1530": r(930, 960)}
    pre_oc = BP * np.log(closes[:, 479] / opens[:, 450])
    pre_oc[~complete] = np.nan
    res["pre_oc"] = pre_oc
    for k in SHIFTS:
        res[f"shift{k:+d}h"] = r(450 + 60 * k, 480 + 60 * k)
    prof = np.vstack([r(30 * j, 30 * j + 30) for j in range(48)]).T     # nd x 48
    res["_profile"] = prof
    return res


# ---------------------------------------------------------------------------------------------- stats
def describe(x: np.ndarray, abs_quantiles: bool = True) -> dict:
    """abs_quantiles=False for difference series (Fassung 2, A-6 / R-12): no uncentred |r| quantiles."""
    x = x[np.isfinite(x)]
    n = int(x.size)
    if n < 3:
        return {"n": n}
    d = x - np.median(x)                         # centre used internally only (MAD), never output
    mad = float(np.median(np.abs(d)))
    xc = x - x.mean()                            # centring for central moments only, never output
    m2 = float((xc ** 2).mean())
    a = np.abs(x)
    out = {"n": n, "sd": float(np.std(x, ddof=1)), "mad_x_1_4826": 1.4826 * mad,
           "excess_kurtosis": float((xc ** 4).mean() / m2 ** 2 - 3.0)}
    if abs_quantiles:
        out.update({"abs_q50": float(np.quantile(a, 0.5)), "abs_q90": float(np.quantile(a, 0.9)),
                    "abs_q95": float(np.quantile(a, 0.95)), "abs_q99": float(np.quantile(a, 0.99))})
    return out


def acf(x: np.ndarray, k: int) -> float:
    d = x - x.mean()
    return float(d[k:] @ d[:-k] / (d @ d))


def batch_means_c(x: np.ndarray, L: int) -> float:
    m = x.size // L
    bm = x[: m * L].reshape(m, L).mean(axis=1)
    return float(L * np.var(bm, ddof=1) / np.var(x, ddof=1))


def persistence(x: np.ndarray) -> dict:
    """R-8 on a chronological event series (NaN dropped)."""
    x = x[np.isfinite(x)]
    n = x.size
    out = {"n": int(n), "acf": {str(k): acf(x, k) for k in LAGS if n > k + 2}}
    sq = x * x
    out["acf_of_square"] = {str(k): acf(sq, k) for k in LAGS if n > k + 2}
    out["c_bartlett"] = {str(b): power_p1.variance_factor(x, b).c_hat for b in (4, 8, 13) if n >= b + 2}
    out["c_bm"] = {str(L): batch_means_c(x, L) for L in (4, 8, 13) if n // L >= 8}
    var = float(np.var(x, ddof=1))
    out["c_stationary_bootstrap"] = {
        str(mb): n * power_p1.stationary_bootstrap_se(x, float(mb), c.N_BOOT, seed=c.SEED) ** 2 / var
        for mb in (4, 8)}
    cands = list(out["c_bartlett"].values()) + list(out["c_bm"].values())
    out["c_rule"] = "max(1, Bartlett 4/8/13, Batch-Means 4/8/13 mit n/L >= 8)"
    out["c_bind"] = float(max(1.0, *cands))
    out["c_hat_max_candidate"] = float(max(cands))
    return out


# ---------------------------------------------------------------------------------------------- bootstrap
class WeekBoot:
    """R-6: ISO-week blocks resampled iid (all classes jointly); statistics from week aggregates."""

    def __init__(self, days: list[date]):
        wk = [d.isocalendar()[:2] for d in days]
        uniq = sorted(set(wk))
        pos = {w: i for i, w in enumerate(uniq)}
        self.week_of_day = np.array([pos[w] for w in wk])
        self.W = len(uniq)
        rng = np.random.default_rng(c.SEED)
        self.counts = rng.multinomial(self.W, np.full(self.W, 1.0 / self.W), size=c.N_BOOT).astype(float)

    def _agg(self, v: np.ndarray) -> np.ndarray:
        out = np.zeros(self.W)
        np.add.at(out, self.week_of_day, v)
        return out

    def sd_reps(self, x: np.ndarray, mask: np.ndarray) -> np.ndarray:
        ok = mask & np.isfinite(x)
        xv = np.where(ok, x, 0.0)
        n = self.counts @ self._agg(ok.astype(float))
        s1 = self.counts @ self._agg(xv)
        s2 = self.counts @ self._agg(xv * xv)
        var = (s2 - s1 * s1 / n) / (n - 1)
        return np.sqrt(var)

    def corr_reps(self, x: np.ndarray, y: np.ndarray, mask: np.ndarray) -> np.ndarray:
        ok = mask & np.isfinite(x) & np.isfinite(y)
        xv, yv = np.where(ok, x, 0.0), np.where(ok, y, 0.0)
        n = self.counts @ self._agg(ok.astype(float))
        sx, sy = self.counts @ self._agg(xv), self.counts @ self._agg(yv)
        sxx, syy = self.counts @ self._agg(xv * xv), self.counts @ self._agg(yv * yv)
        sxy = self.counts @ self._agg(xv * yv)
        cov = sxy - sx * sy / n
        return cov / np.sqrt((sxx - sx * sx / n) * (syy - sy * sy / n))


def band(reps: np.ndarray) -> dict:
    r = reps[np.isfinite(reps)]
    return {"q025": float(np.quantile(r, 0.025)), "q975": float(np.quantile(r, 0.975)),
            "q05": float(np.quantile(r, 0.05)), "q95": float(np.quantile(r, 0.95)), "n_rep": int(r.size)}


# ---------------------------------------------------------------------------------------------- main
def main() -> dict:
    kl = load()
    days_s = kl["BTC"]["days"]
    days = [date.fromisoformat(s) for s in days_s]
    fine = np.array([c.day_class(d) for d in days])
    year = np.array([s[:4] for s in days_s])
    masks = {k: np.isin(fine, v) for k, v in c.CLASS_SETS.items()}
    sr = {s: slot_returns(kl[s]["closes"], kl[s]["opens"], kl[s]["complete"]) for s in ("BTC", "ETH")}
    slots = [k for k in sr["BTC"] if not k.startswith("_")]
    series = {}
    for sl in slots:
        b, e = sr["BTC"][sl], sr["ETH"][sl]
        series[sl] = {"BTC": b, "ETH": e, "CLUSTER": 0.5 * (b + e)}
    # P3 baseline: per-day statistic (1/44) x sum of the 44 slot returns outside [07:00, 09:00)
    keep = [j for j in range(48) if j not in EXCL_P3ALL]
    p3 = {s: np.nanmean(sr[s]["_profile"][:, keep], axis=1) for s in ("BTC", "ETH")}  # internal per-day statistic
    for s in ("BTC", "ETH"):
        nmiss = np.isnan(sr[s]["_profile"][:, keep]).sum(axis=1)
        p3[s][nmiss > 0] = np.nan
    series["p3all_44slots"] = {"BTC": p3["BTC"], "ETH": p3["ETH"], "CLUSTER": 0.5 * (p3["BTC"] + p3["ETH"])}
    # paired same-day difference pre - fix1530 (design i-s)
    series["pre_minus_fix1530"] = {k: series["pre"][k] - series["fix1530"][k] for k in ("BTC", "ETH", "CLUSTER")}

    out: dict = {"label": c.LABEL, "quelle": "S:a2v_sigma30.py (R-3..R-8)",
                 "period_returns": f"{days_s[0]}..{days_s[-1]}", "n_days": len(days),
                 "class_day_counts": {k: int(m.sum()) for k, m in masks.items()},
                 "kline_meta": {s: {k: v for k, v in kl[s]["meta"].items() if k != "incomplete_days"}
                                for s in ("BTC", "ETH")},
                 "units": "bp (1e4 x log return)"}

    # ---- B-1: dispersion per slot / class / symbol, by year
    disp = {}
    for sl, ser in series.items():
        cell = {}
        aq = "minus" not in sl                     # Fassung 2 (A-6): no |r| quantiles for difference series
        for cl in CLASSES:
            m = masks[cl]
            sub = {k: describe(ser[k][m], aq) for k in ("BTC", "ETH", "CLUSTER")}
            if sub["BTC"].get("n", 0) >= 3 and sub["ETH"].get("n", 0) >= 3:
                sub["sigma_pooled"] = float(np.sqrt((sub["BTC"]["sd"] ** 2 + sub["ETH"]["sd"] ** 2) / 2))
            sub["by_year"] = {}
            for y in YEARS:
                my = m & (year == y)
                if my.sum() < 3:
                    continue
                yy = {k: describe(ser[k][my], aq) for k in ("BTC", "ETH", "CLUSTER")}
                yy["sigma_pooled"] = float(np.sqrt((yy["BTC"]["sd"] ** 2 + yy["ETH"]["sd"] ** 2) / 2))
                sub["by_year"][y] = yy
            cell[cl] = sub
        disp[sl] = cell
    out["dispersion"] = disp

    # intraday SD profile (48 slots), all days and FRI / MODO / WE
    prof = {}
    for cl in ("ALL", "FRI", "MODO", "WE"):
        m = masks[cl]
        prof[cl] = {s: [float(np.nanstd(sr[s]["_profile"][m, j], ddof=1)) for j in range(48)]
                    for s in ("BTC", "ETH")}
        clu = 0.5 * (sr["BTC"]["_profile"] + sr["ETH"]["_profile"])
        prof[cl]["CLUSTER"] = [float(np.nanstd(clu[m, j], ddof=1)) for j in range(48)]
    out["sd_profile_48_slots"] = {"slot_start_utc": [f"{(30*j)//60:02d}:{(30*j)%60:02d}" for j in range(48)],
                                  "by_class": prof}

    # ---- R-6: SD ratios with week-block bootstrap band
    wb = WeekBoot(days)
    out["bootstrap"] = {"unit": "ISO-Woche (alle Klassen gemeinsam)", "n_weeks": wb.W, "n_rep": c.N_BOOT,
                        "seed": c.SEED}

    def sd_of(sl, k, cl):
        x = series[sl][k]
        return float(np.nanstd(x[masks[cl] & np.isfinite(x)], ddof=1))

    ratio_defs = {
        "FRI/MODO": (("pre", "FRI"), ("pre", "MODO")), "FRI_W/MODO": (("pre", "FRI_W"), ("pre", "MODO")),
        "FRI_MQ/MODO": (("pre", "FRI_MQ"), ("pre", "MODO")), "FRI_MQ/FRI_W": (("pre", "FRI_MQ"), ("pre", "FRI_W")),
        "WE/MODO": (("pre", "WE"), ("pre", "MODO")), "FRI/WE": (("pre", "FRI"), ("pre", "WE")),
        "NONFRI/MODO": (("pre", "NONFRI"), ("pre", "MODO")),
        "fix1530_ALL/pre_MODO": (("fix1530", "ALL"), ("pre", "MODO")),
        "pre_FRI/fix1530_FRI": (("pre", "FRI"), ("fix1530", "FRI")),
        "pre_MODO/fix1530_MODO": (("pre", "MODO"), ("fix1530", "MODO")),
        "post60_ALL_per30min/pre_ALL": (("post60", "ALL"), ("pre", "ALL")),
        "pre_oc_ALL/pre_ALL": (("pre_oc", "ALL"), ("pre", "ALL")),
    }
    for k in SHIFTS:
        ratio_defs[f"shift{k:+d}h_ALL/pre_ALL"] = ((f"shift{k:+d}h", "ALL"), ("pre", "ALL"))
    ratios = {}
    for name, ((sa, ca), (sb, cb)) in ratio_defs.items():
        cell = {}
        for k in ("BTC", "ETH", "CLUSTER"):
            fa = 1 / np.sqrt(2) if sa == "post60" else 1.0     # 60-min SD per 30 min (sqrt-time scaling)
            pt = fa * sd_of(sa, k, ca) / sd_of(sb, k, cb)
            reps = fa * wb.sd_reps(series[sa][k], masks[ca]) / wb.sd_reps(series[sb][k], masks[cb])
            cell[k] = {"ratio": pt, "band": band(reps)}
        # pooled sigma ratio
        def pooled(sl, cl):
            return np.sqrt((sd_of(sl, "BTC", cl) ** 2 + sd_of(sl, "ETH", cl) ** 2) / 2)
        def pooled_reps(sl, cl):
            return np.sqrt((wb.sd_reps(series[sl]["BTC"], masks[cl]) ** 2 + wb.sd_reps(series[sl]["ETH"], masks[cl]) ** 2) / 2)
        fa = 1 / np.sqrt(2) if sa == "post60" else 1.0
        cell["POOLED"] = {"ratio": float(fa * pooled(sa, ca) / pooled(sb, cb)),
                          "band": band(fa * pooled_reps(sa, ca) / pooled_reps(sb, cb))}
        ratios[name] = cell
    out["sd_ratios"] = ratios

    # bootstrap bands for the class SDs of r_pre themselves (cluster and pooled)
    sdb = {}
    for cl in CLASSES:
        sdb[cl] = {k: band(wb.sd_reps(series["pre"][k], masks[cl])) for k in ("BTC", "ETH", "CLUSTER")}
    out["sd_pre_bootstrap_band"] = sdb

    # ---- B-2: rho(BTC, ETH) per class (pre, plus fix1530 and post60 as report)
    rho = {}
    for sl in ("pre", "fix1530", "post60", "pre_oc"):
        cell = {}
        for cl in CLASSES:
            m = masks[cl] & np.isfinite(series[sl]["BTC"]) & np.isfinite(series[sl]["ETH"])
            a, b = series[sl]["BTC"][m], series[sl]["ETH"][m]
            cell[cl] = {"n": int(m.sum()), "pearson": float(np.corrcoef(a, b)[0, 1]),
                        "spearman": float(stats.spearmanr(a, b).statistic),
                        "pearson_band": band(wb.corr_reps(series[sl]["BTC"], series[sl]["ETH"], masks[cl]))}
            cell[cl]["by_year"] = {}
            for y in YEARS:
                my = m & (year == y)
                if my.sum() >= 5:
                    cell[cl]["by_year"][y] = {"n": int(my.sum()),
                                              "pearson": float(np.corrcoef(series[sl]["BTC"][my], series[sl]["ETH"][my])[0, 1])}
        rho[sl] = cell
    out["rho_btc_eth"] = rho
    # correlation of cc and oc definitions of r_pre (A-3 report)
    out["corr_pre_cc_vs_oc"] = {k: float(np.corrcoef(series["pre"][k], series["pre_oc"][k])[0, 1])
                                for k in ("BTC", "ETH", "CLUSTER")}
    # A-3: on Bybit 1-min candles the open equals the previous close (counts only)
    out["open_eq_prev_close"] = {s: {"at_0730_days": int((kl[s]["opens"][:, 450] == kl[s]["closes"][:, 449]).sum()),
                                     "n_days": int(kl[s]["opens"].shape[0]),
                                     "within_day_all_minutes": int((kl[s]["opens"][:, 1:] == kl[s]["closes"][:, :-1]).sum()),
                                     "within_day_minute_pairs": int(kl[s]["opens"][:, 1:].size)}
                                 for s in ("BTC", "ETH")}

    # ---- B-3: autocorrelation over consecutive events and variance factor
    pers = {}
    for sl in ("pre", "fix1530", "pre_minus_fix1530", "p3all_44slots", "post60"):
        cell = {}
        for cl in ("FRI", "FRI_W", "FRI_MQ", "MODO", "WE", "NONFRI", "ALL"):
            cell[cl] = {k: persistence(series[sl][k][masks[cl]]) for k in ("CLUSTER", "BTC", "ETH")}
        pers[sl] = cell
    out["persistence"] = pers

    # cross-correlation event vs placebo aggregated per week / month (R-9 covariance term)
    def agg_corr(event_cls, plac_cls, keyfun):
        x = series["pre"]["CLUSTER"]
        ev, pl_ = {}, {}
        for i, d in enumerate(days):
            if not np.isfinite(x[i]):
                continue
            kk = keyfun(d)
            if fine[i] in c.CLASS_SETS[event_cls]:
                ev.setdefault(kk, []).append(x[i])
            elif fine[i] in c.CLASS_SETS[plac_cls]:
                pl_.setdefault(kk, []).append(x[i])
        keys = sorted(set(ev) & set(pl_))
        a = np.array([np.sum(ev[kk]) / len(ev[kk]) for kk in keys])     # internal aggregation only
        b = np.array([np.sum(pl_[kk]) / len(pl_[kk]) for kk in keys])
        return {"n_pairs": len(keys), "pearson": float(np.corrcoef(a, b)[0, 1])}
    out["cross_corr_event_vs_placebo"] = {
        "FRI_vs_MODO_same_iso_week": agg_corr("FRI", "MODO", lambda d: d.isocalendar()[:2]),
        "FRI_W_vs_MODO_same_iso_week": agg_corr("FRI_W", "MODO", lambda d: d.isocalendar()[:2]),
        "FRI_MQ_vs_FRI_W_same_month": agg_corr("FRI_MQ", "FRI_W", lambda d: (d.year, d.month)),
        "FRI_vs_NONFRI_same_iso_week": agg_corr("FRI", "NONFRI", lambda d: d.isocalendar()[:2]),
        "rule": "Pearson der Klassen-Aggregate je Woche/Monat (nur Korrelation ausgegeben)"}
    # same-day correlation pre vs fix1530 (paired design)
    out["corr_pre_vs_fix1530_same_day"] = {
        cl: float(np.corrcoef(series["pre"]["CLUSTER"][masks[cl]], series["fix1530"]["CLUSTER"][masks[cl]])[0, 1])
        for cl in ("FRI", "MODO", "ALL")}
    # formula check: SD(cluster) vs sigma_pooled * sqrt((1 + rho) / 2)
    fchk = {}
    for cl in CLASSES:
        dd = disp["pre"][cl]
        r_ = rho["pre"][cl]["pearson"]
        fchk[cl] = {"sd_cluster_direct": dd["CLUSTER"]["sd"],
                    "sigma_pooled_x_sqrt_half_1_plus_rho": dd["sigma_pooled"] * np.sqrt((1 + r_) / 2),
                    "sd_cluster_exact_unequal": float(np.sqrt(dd["BTC"]["sd"] ** 2 + dd["ETH"]["sd"] ** 2
                                                              + 2 * r_ * dd["BTC"]["sd"] * dd["ETH"]["sd"]) / 2)}
    out["formula_check_cluster_sd"] = fchk
    c.check_out(out)
    return out


if __name__ == "__main__":
    res = main()
    h = c.dump(res, c.WORK / "a2v_sigma30.json")
    print("sha256", h)
