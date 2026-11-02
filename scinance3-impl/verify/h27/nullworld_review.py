"""H-27 review, check point 1 (Jensen) and 4 (RV estimator bound): independent null worlds.

(A) log-SV model of the derivation (own implementation), BTC parameters phi 0.996, eta 0.06,
    nu 4.5 (derivation's calibration) and nu sensitivity; additionally a moment check of the
    kurtosis edge (nu < 4.5).
(B) GARCH(1,1) with standardised-t innovations, fitted by ML on BTC daily returns
    2021-03-25..2024-05-31 (own code) -- an independent model in which IV reacts to realised
    returns (as DVOL does).
Per model and window length n: J (mean window statistic under the null, at the reference level),
SE_null (SD of the window statistic at the reference level), c_null; for RV_hat (close-to-close,
30 daily returns) and for the noise-free QV (sqrt of the true integrated variance) -- the latter is
the lower bound for ANY RV estimator (intraday, range).  Only RV of the pre-period is used.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import optimize, special

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rv_common import ANN, H, PRICE_LAST, daily_vars, guard_out  # noqa: E402

M = 6000
NS = [184, 274, 365]


def std_t(rng, nu, shape):
    return rng.standard_t(nu, size=shape) / math.sqrt(nu / (nu - 2.0))


def window_stats(iv2: np.ndarray, rv2: np.ndarray, qv2: np.ndarray, sigma_ref: float, n: int) -> dict:
    """iv2, rv2, qv2: (M, n) annualised variances for the n IV days of each window."""
    iv, rv, qv = np.sqrt(iv2), np.sqrt(rv2), np.sqrt(qv2)
    lvl = np.sqrt(iv2.mean(axis=1))
    out = {}
    for tag, r in (("rv_cc", rv), ("qv_noisefree", qv)):
        s1 = 100 * (iv - r)
        s3 = np.log(iv / r)
        for u, x, norm in (("S1", s1, sigma_ref / lvl), ("S3", s3, np.ones_like(lvl))):
            wm = x.mean(axis=1)
            wn = wm * norm
            out[f"{tag}/{u}"] = {"J_at_ref": float(wn.mean()), "J_mc_se": float(wn.std(ddof=1) / math.sqrt(wn.size)),
                                 "se_null_at_ref": float(wn.std(ddof=1)),
                                 "c_null": float(n * wm.var(ddof=1) / x.var(ddof=1)),
                                 "sd_daily_at_ref": float((x * norm[:, None]).std(ddof=1))}
    return out


# ---------------------------------------------------------------- (A) log-SV
def sv_world(phi, eta, nu, sigma_ref, n, seed):
    rng = np.random.default_rng(seed)
    T = n + H
    mu = 2 * math.log(sigma_ref / math.sqrt(ANN))       # level: E exp(h) ~ sigma_ref^2/ANN (irrelevant at_ref)
    h = mu + rng.standard_normal(M) * eta / math.sqrt(1 - phi * phi)
    hs = np.empty((M, T))
    for t in range(T):
        h = mu + phi * (h - mu) + eta * rng.standard_normal(M)
        hs[:, t] = h
    z = std_t(rng, nu, (M, T))
    r2 = np.exp(hs) * z * z
    s2 = np.exp(hs)
    # E_t exp(h_{t+k}) given h_t
    hh = hs[:, :n] - mu
    acc = np.zeros((M, n))
    for k in range(1, H + 1):
        acc += np.exp(mu + phi ** k * hh + 0.5 * eta * eta * (1 - phi ** (2 * k)) / (1 - phi * phi))
    iv2 = ANN / H * acc
    c_r = np.concatenate([np.zeros((M, 1)), np.cumsum(r2, 1)], 1)
    c_s = np.concatenate([np.zeros((M, 1)), np.cumsum(s2, 1)], 1)
    rv2 = ANN / H * (c_r[:, 1 + H:1 + H + n] - c_r[:, 1:1 + n])
    qv2 = ANN / H * (c_s[:, 1 + H:1 + H + n] - c_s[:, 1:1 + n])
    return window_stats(iv2, rv2, qv2, sigma_ref, n)


def loo_kurtosis(r: np.ndarray) -> float:
    r2 = r * r
    k = 15
    cs = np.concatenate([[0.0], np.cumsum(r2)])
    win = cs[2 * k + 1:] - cs[:-(2 * k + 1)]
    loo = (win - r2[k:r.size - k]) / (2 * k)
    z = r[k:r.size - k] / np.sqrt(loo)
    return float((z ** 4).mean() / (z ** 2).mean() ** 2)


def kurt_check(r_data, phi, eta, sigma_ref):
    """Simulated LOO kurtosis (mean, sd over 200 paths of the data length) per nu vs data."""
    T = r_data.size
    out = {"data": loo_kurtosis(r_data)}
    for nu in (3.5, 4.0, 4.5, 6.0):
        rng = np.random.default_rng(4500 + int(nu * 10))
        ks = []
        for _ in range(200):
            h = rng.standard_normal() * eta / math.sqrt(1 - phi * phi)
            e = rng.standard_normal(T)
            hs = np.empty(T)
            for t in range(T):
                h = phi * h + eta * e[t]
                hs[t] = h
            r = np.exp(hs / 2) * std_t(rng, nu, T)
            ks.append(loo_kurtosis(r))
        out[f"nu_{nu}"] = [float(np.mean(ks)), float(np.std(ks))]
    return out


# ---------------------------------------------------------------- (B) GARCH(1,1)-t
def garch_nll(p, r):
    w, a, b, nu = p
    if w <= 0 or a < 0 or b < 0 or a + b >= 0.9999 or nu <= 2.05:
        return 1e12
    s2 = np.empty(r.size)
    s2[0] = r.var()
    for t in range(1, r.size):
        s2[t] = w + a * r[t - 1] ** 2 + b * s2[t - 1]
    z2 = r * r / s2
    c = special.gammaln((nu + 1) / 2) - special.gammaln(nu / 2) - 0.5 * math.log(math.pi * (nu - 2))
    ll = c - 0.5 * np.log(s2) - (nu + 1) / 2 * np.log1p(z2 / (nu - 2))
    return -float(ll.sum())


def garch_fit(r):
    v = r.var()
    best = None
    for a0, b0, nu0 in ((0.05, 0.90, 5.0), (0.10, 0.85, 4.0), (0.03, 0.95, 6.0)):
        x0 = [v * (1 - a0 - b0), a0, b0, nu0]
        res = optimize.minimize(garch_nll, x0, args=(r,), method="Nelder-Mead",
                                options={"maxiter": 6000, "xatol": 1e-10, "fatol": 1e-8})
        if best is None or res.fun < best.fun:
            best = res
    w, a, b, nu = best.x
    return {"omega": float(w), "alpha": float(a), "beta": float(b), "nu": float(nu),
            "persistence": float(a + b), "nll": float(best.fun),
            "uncond_vol_ann": float(math.sqrt(ANN * w / (1 - a - b)))}


def garch_world(g, sigma_ref, n, seed, burn=600):
    w, a, b, nu = g["omega"], g["alpha"], g["beta"], g["nu"]
    pers = a + b
    vbar = w / (1 - pers)
    rng = np.random.default_rng(seed)
    T = burn + n + H
    s2 = np.full(M, vbar)
    S2 = np.empty((M, T))
    R2 = np.empty((M, T))
    z = std_t(rng, nu, (M, T))
    for t in range(T):
        S2[:, t] = s2
        r = np.sqrt(s2) * z[:, t]
        R2[:, t] = r * r
        s2 = w + a * r * r + b * s2
    S2, R2 = S2[:, burn:], R2[:, burn:]
    # E_t sigma2_{t+k}, k>=1, given information at end of day t: sigma2_{t+1} known
    s_next = np.concatenate([S2[:, 1:], (w + a * R2[:, -1:] + b * S2[:, -1:])], 1)[:, :n]
    acc = np.zeros((M, n))
    for k in range(1, H + 1):
        acc += vbar + pers ** (k - 1) * (s_next - vbar)
    iv2 = ANN / H * acc
    c_r = np.concatenate([np.zeros((M, 1)), np.cumsum(R2, 1)], 1)
    c_s = np.concatenate([np.zeros((M, 1)), np.cumsum(S2, 1)], 1)
    rv2 = ANN / H * (c_r[:, 1 + H:1 + H + n] - c_r[:, 1:1 + n])
    qv2 = ANN / H * (c_s[:, 1 + H:1 + H + n] - c_s[:, 1:1 + n])
    return window_stats(iv2, rv2, qv2, sigma_ref, n)


def main() -> None:
    ds, dv = daily_vars("BTC")
    sel = np.array([d >= "2021-03-25" for d in ds])
    r = dv["r"][sel]
    if not np.all(np.isfinite(r)) or max(np.array(ds)[sel]) > PRICE_LAST:
        raise RuntimeError("pre-period returns not clean")
    cs = np.concatenate([[0.0], np.cumsum(r * r)])
    sigma_ref = float(np.sqrt(np.mean(ANN / H * (cs[H:] - cs[:-H]))))
    out = {"sigma_ref_rv_rms_pre_period": sigma_ref, "M": M, "n_returns": int(r.size)}
    out["SV"] = {}
    for nu in (4.5, 6.0, 15.0):
        out["SV"][f"phi0.996_eta0.06_nu{nu}"] = {str(n): sv_world(0.996, 0.06, nu, sigma_ref, n, 9600 + n + int(nu))
                                                for n in (NS if nu == 4.5 else [365])}
        print("SV nu", nu, json.dumps(out["SV"][f"phi0.996_eta0.06_nu{nu}"]["365"]["rv_cc/S1"]), flush=True)
    out["SV_kurtosis_check"] = kurt_check(r, 0.996, 0.06, sigma_ref)
    print("kurt", out["SV_kurtosis_check"], flush=True)
    g = garch_fit(r)
    out["GARCH_fit"] = g
    print("garch", g, flush=True)
    out["GARCH"] = {str(n): garch_world(g, sigma_ref, n, 7700 + n) for n in NS}
    print("GARCH 365", json.dumps(out["GARCH"]["365"], indent=0), flush=True)
    guard_out(out)
    (HERE / "nullworld_review.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
