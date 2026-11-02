"""H-27 review, check point 1 and 4: independent nuisance of the daily premium (pre-period only).

Per symbol and RV estimator (cc = close-to-close as in the derivation; pk Parkinson, gk Garman-Klass,
rs Rogers-Satchell from the same daily candle -- check point 4, report only):
  SD, ACF, variance factor c of the window-mean statistic by several estimators
  (truncated ACF sums, Bartlett own + power_p1, Parzen, batch means, overlapping batch means,
  stationary bootstrap), monthly non-overlapping variant; RV-only ratios (allowed, pre-period).
Plus a Monte Carlo check of the binding rule P-3 (max of six estimators) on Gaussian series with
the measured ACF.  No premium mean, no DVOL mean is printed or stored (guard_out).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/scinance/src")
from rv_common import LABEL, guard_out, premium  # noqa: E402
from bybit_edge.research import power_p1  # noqa: E402

LAGS = [1, 5, 10, 15, 20, 25, 29, 30, 35, 40, 45, 60, 90, 120]


def acf_all(x: np.ndarray, kmax: int) -> np.ndarray:
    d = x - x.mean()
    g0 = d @ d
    return np.array([1.0] + [float(d[k:] @ d[:-k] / g0) for k in range(1, kmax + 1)])


def c_trunc(rho: np.ndarray, K: int) -> float:
    return float(1 + 2 * rho[1:K + 1].sum())


def c_kernel(rho: np.ndarray, B: int, kind: str) -> float:
    k = np.arange(1, B + 1)
    u = k / (B + 1.0)
    if kind == "bartlett":
        w = 1 - u
    elif kind == "parzen":
        w = np.where(u <= 0.5, 1 - 6 * u ** 2 + 6 * u ** 3, 2 * (1 - u) ** 3)
    else:
        raise ValueError(kind)
    return float(1 + 2 * (w * rho[1:B + 1]).sum())


def c_bm(x: np.ndarray, L: int) -> float:
    m = x.size // L
    bm = x[:m * L].reshape(m, L).mean(1)
    return float(L * bm.var(ddof=1) / x.var(ddof=1))


def c_obm(x: np.ndarray, L: int) -> float:
    """Overlapping batch means (Meketon/Schmeiser): all n-L+1 windows, bias-corrected."""
    n = x.size
    cs = np.concatenate([[0.0], np.cumsum(x)])
    wm = (cs[L:] - cs[:-L]) / L
    mu = x.mean()
    sig2 = n * L / ((n - L + 1) * (n - L)) * float(((wm - mu) ** 2).sum())
    return float(sig2 / x.var(ddof=1))


def c_window_exact(rho: np.ndarray, n: int, K: int) -> float:
    """Finite-window factor n Var(mean_n)/Var(x) = 1 + 2 sum_{k<n} (1 - k/n) rho_k, lags <= K."""
    k = np.arange(1, min(K, n - 1) + 1)
    return float(1 + 2 * ((1 - k / n) * rho[k]).sum())


def describe(x: np.ndarray, boot: bool = True) -> dict:
    if not np.all(np.isfinite(x)):
        raise RuntimeError("gap in series")
    rho = acf_all(x, 200)
    out = {"n": int(x.size), "sd": float(x.std(ddof=1)),
           "acf": {str(k): float(rho[k]) for k in LAGS},
           "first_lag_acf_lt_0": int(np.argmax(rho[1:] < 0) + 1),
           "c_trunc": {str(K): c_trunc(rho, K) for K in (29, 35, 45, 60, 90, 120)},
           "c_bartlett": {str(B): c_kernel(rho, B, "bartlett") for B in (30, 60, 90, 120, 180)},
           "c_bartlett_power_p1": {str(B): power_p1.variance_factor(x, B).c_hat for B in (60, 90, 120)},
           "c_parzen": {str(B): c_kernel(rho, B, "parzen") for B in (60, 90, 120, 180)},
           "c_bm": {str(L): c_bm(x, L) for L in (30, 60, 90, 120)},
           "c_obm": {str(L): c_obm(x, L) for L in (60, 90, 120, 184)},
           "c_window_n_lags45": {str(n): c_window_exact(rho, n, 45) for n in (184, 274, 365)},
           "c_window_n_lags120": {str(n): c_window_exact(rho, n, 120) for n in (184, 274, 365)}}
    if boot:
        v = x.var(ddof=1)
        out["c_statboot"] = {str(b): float(x.size * power_p1.stationary_bootstrap_se(x, float(b), 2000, seed=127) ** 2 / v)
                             for b in (30, 60, 90)}
    six = [out["c_bartlett"][b] for b in ("60", "90", "120")] + [out["c_bm"][L] for L in ("60", "90", "120")]
    out["c_rule_P3_max6"] = float(max(1.0, *six))
    # monthly non-overlapping (all 30 phases), SD and lag-1 ACF averaged over phases
    sds, a1 = [], []
    for ph in range(30):
        s = x[ph::30]
        sds.append(float(s.std(ddof=1)))
        d = s - s.mean()
        a1.append(float(d[1:] @ d[:-1] / (d @ d)))
    out["monthly"] = {"sd_m": float(np.mean(sds)), "acf1": float(np.mean(a1))}
    return out


def mc_rule_bias(rho_emp: np.ndarray, n: int, reps: int, seed: int) -> dict:
    """Gaussian series with ACF = empirical ACF tapered to zero by lag 90 (Tukey taper from lag 60);
    true c known exactly; distribution of the six estimators and of the P-3 max rule."""
    K = 90
    taper = np.ones(K + 1)
    j = np.arange(61, K + 1)
    taper[61:] = 0.5 * (1 + np.cos(np.pi * (j - 60) / (K - 60)))
    r = rho_emp[:K + 1] * taper
    c_true = float(1 + 2 * r[1:].sum())
    c_true_365 = c_window_exact(r, 365, K)
    # circulant embedding
    m = 1
    while m < 2 * (n + K):
        m *= 2
    acv = np.zeros(m)
    acv[:K + 1] = r
    acv[m - K:] = r[1:][::-1]
    lam = np.fft.fft(acv).real
    lam_min = float(lam.min())
    lam = np.clip(lam, 0, None)
    rng = np.random.default_rng(seed)
    res = {k: [] for k in ("b60", "b90", "b120", "bm60", "bm90", "bm120", "obm90", "max6")}
    for _ in range(reps):
        z = rng.standard_normal(m) + 1j * rng.standard_normal(m)
        x = np.fft.fft(np.sqrt(lam / m) * z).real[:n]
        rr = acf_all(x, 120)
        vals = {"b60": c_kernel(rr, 60, "bartlett"), "b90": c_kernel(rr, 90, "bartlett"),
                "b120": c_kernel(rr, 120, "bartlett"), "bm60": c_bm(x, 60), "bm90": c_bm(x, 90),
                "bm120": c_bm(x, 120), "obm90": c_obm(x, 90)}
        vals["max6"] = max(1.0, *[vals[k] for k in ("b60", "b90", "b120", "bm60", "bm90", "bm120")])
        for k, v in vals.items():
            res[k].append(v)
    summ = {k: {"q10": float(np.quantile(v, 0.1)), "q50": float(np.quantile(v, 0.5)),
                "q90": float(np.quantile(v, 0.9)), "sd": float(np.std(v))} for k, v in res.items()}
    return {"c_true_longrun": c_true, "c_true_window365": c_true_365, "embedding_min_eigen": lam_min,
            "reps": reps, "n": n, "estimators": summ,
            "share_max6_ge_28": float(np.mean(np.array(res["max6"]) >= 28.0))}


def main() -> None:
    out: dict = {"label": LABEL}
    frames = {}
    for sym in ("BTC", "ETH"):
        for est in ("cc", "pk", "gk", "rs"):
            f = premium(sym, est)
            frames[(sym, est)] = f
            ok = np.isfinite(f["S1"])
            if not ok.all():
                raise RuntimeError(f"{sym} {est}: {int((~ok).sum())} missing days")
            rv = f["rv"]
            rec = {"rv_rms": float(np.sqrt(np.mean(rv ** 2))),
                   "ratio_rvmean_to_rvrms": float(np.mean(rv) / np.sqrt(np.mean(rv ** 2)))}
            for u in ("S1", "S3") if est != "cc" else ("S1", "S2", "S3"):
                rec[u] = describe(f[u], boot=(est == "cc" and sym == "BTC") or (est == "pk" and u == "S1"))
            out[f"{sym}/{est}"] = rec
            print(sym, est, "sd S1", round(rec["S1"]["sd"], 2), "c_rule", round(rec["S1"]["c_rule_P3_max6"], 1),
                  "c_trunc45", round(rec["S1"]["c_trunc"]["45"], 1), flush=True)
        # RV-only comparisons between estimators (allowed: RV, pre-period)
        cc, pk = frames[(sym, "cc")]["rv"], frames[(sym, "pk")]["rv"]
        out[f"{sym}/rv_compare"] = {
            "ratio_rms_pk_to_cc": float(np.sqrt(np.mean(pk ** 2) / np.mean(cc ** 2))),
            "sd_volpts_rv_cc_minus_rv_pk": float(100 * np.std(cc - pk, ddof=1)),
            "corr_premium_cc_pk_S1": float(np.corrcoef(frames[(sym, "cc")]["S1"], frames[(sym, "pk")]["S1"])[0, 1])}
    # Monte Carlo of the P-3 binding rule on BTC S1 (cc)
    x = frames[("BTC", "cc")]["S1"]
    out["mc_rule_bias_BTC_S1_cc"] = mc_rule_bias(acf_all(x, 120), x.size, 2000, 2701)
    # leg (BTC+ETH) in S3 (scale-free) -- aggregation check
    leg = 0.5 * (frames[("BTC", "cc")]["S3"] + frames[("ETH", "cc")]["S3"])
    out["LEG/cc/S3"] = describe(leg, boot=False)
    out["corr_btc_eth_cc"] = {u: float(np.corrcoef(frames[("BTC", "cc")][u], frames[("ETH", "cc")][u])[0, 1])
                              for u in ("S1", "S3")}
    guard_out(out)
    (HERE / "nuisance_review.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("mc_rule_bias_BTC_S1_cc",)}, indent=1))


if __name__ == "__main__":
    main()
