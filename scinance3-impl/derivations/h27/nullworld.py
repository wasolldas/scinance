"""H-27 null world (FEASIBILITY.md P-5, DEC-94 (5) (ii)): Jensen bias and SE of the window statistic
when IV equals the true conditional forward vol (no variance risk premium).

Model per symbol: h_t = mu + phi (h_{t-1} - mu) + eta e_t, r_t = exp(h_t / 2) z_t, z standardised
Student-t(nu).  Calibrated ONLY on realized returns of the pre-period (prices <= 2024-05-31) by
simulated moments (common random numbers): SD of y = ln RV30^2 (overlapping, forward 30 days),
ACF(y) at lags 30 and 90, kurtosis of leave-one-out standardised daily returns; mu matches mean(y).
Null IV: IV(t)^2 = (365/30) sum_k E_t[exp(h_{t+k})] in closed form.
Outputs: calibrated (mu, phi, eta, nu), moment fit, J (mean window statistic under the null) and
SE_null(n) for S1/S2/S3 and window lengths n; no real IV is used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from h27_common import NUISANCE_FIRST_IV_DAY, NUISANCE_LAST_IV_DAY  # noqa: E402
from h27_series import ANN, H, daily_log_returns  # noqa: E402

SEED = 96
R_CAL = 120
PHI = [0.95, 0.97, 0.98, 0.985, 0.99, 0.993, 0.996, 0.998]
ETA = [0.04, 0.06, 0.08, 0.10, 0.13, 0.16, 0.20, 0.25, 0.30]
NU = [4.5, 6.0, 8.0, 15.0]
WINDOW_DAYS = [181, 184, 274, 275, 365, 366]
M_WIN = 6000


def acf_rows(y: np.ndarray, k: int) -> np.ndarray:
    d = y - y.mean(axis=-1, keepdims=True)
    return (d[..., k:] * d[..., :-k]).sum(-1) / (d * d).sum(-1)


def moments(r: np.ndarray) -> dict[str, np.ndarray]:
    """r: (..., T) daily returns of the pre-period; t-set = all t with a full 30-day target."""
    r2 = r * r
    cs = np.concatenate([np.zeros(r.shape[:-1] + (1,)), np.cumsum(r2, axis=-1)], axis=-1)
    # y_t for t = 0..T-31 uses r_{t+1..t+30}
    s30 = cs[..., H + 1:] - cs[..., 1:-H]
    y = np.log(ANN / H * s30)
    # leave-one-out standardisation by the centred 31-day window
    T = r.shape[-1]
    k = 15
    win = cs[..., 2 * k + 1:] - cs[..., :-(2 * k + 1)]            # sums over [s-k, s+k]
    centre = r2[..., k:T - k]
    loo = (win - centre) / (2 * k)
    z = r[..., k:T - k] / np.sqrt(loo)
    kurt = (z ** 4).mean(-1) / (z ** 2).mean(-1) ** 2
    return {"mean_y": y.mean(-1), "sd_y": y.std(-1, ddof=1), "ac30": acf_rows(y, 30),
            "ac90": acf_rows(y, 90), "kurt": kurt}


def std_t(rng: np.random.Generator, nu: float, shape) -> np.ndarray:
    return rng.standard_t(nu, size=shape) / np.sqrt(nu / (nu - 2.0))


def sim_returns(mu, phi, eta, z, e, h0) -> tuple[np.ndarray, np.ndarray]:
    R, T = e.shape
    h = np.empty((R, T))
    prev = h0
    for t in range(T):
        prev = mu + phi * (prev - mu) + eta * e[:, t]
        h[:, t] = prev
    return np.exp(h / 2.0) * z, h


def calibrate(r_data: np.ndarray) -> dict:
    T = r_data.size
    m_data = {k: float(v) for k, v in moments(r_data).items()}
    rng = np.random.default_rng(SEED)
    e = rng.standard_normal((R_CAL, T))
    u0 = rng.standard_normal(R_CAL)
    zs = {nu: std_t(np.random.default_rng(SEED + int(nu * 10)), nu, (R_CAL, T)) for nu in NU}
    best = None
    table = []
    for nu in NU:
        for phi in PHI:
            for eta in ETA:
                h0 = u0 * eta / np.sqrt(1 - phi * phi)
                r, _ = sim_returns(0.0, phi, eta, zs[nu], e, h0)
                m = moments(r)
                dist = 0.0
                fit = {}
                for key in ("sd_y", "ac30", "ac90", "kurt"):
                    mm, sd = float(m[key].mean()), float(m[key].std(ddof=1))
                    fit[key] = (mm, sd)
                    dist += ((mm - m_data[key]) / sd) ** 2
                mu = m_data["mean_y"] - float(m["mean_y"].mean())
                table.append((dist, phi, eta, nu, mu))
                if best is None or dist < best[0]:
                    best = (dist, phi, eta, nu, mu, fit)
    dist, phi, eta, nu, mu, fit = best
    table.sort()
    return {"data_moments": m_data, "phi": phi, "eta": eta, "nu": nu, "mu": mu,
            "distance": dist, "fit_sim_mean_sd": {k: list(v) for k, v in fit.items()},
            "top5": [list(x) for x in table[:5]], "R_cal": R_CAL, "T": int(T)}


def null_windows(p: dict, n_days: int, M: int, seed: int, sigma_ref: float) -> dict:
    mu, phi, eta, nu = p["mu"], p["phi"], p["eta"], p["nu"]
    rng = np.random.default_rng(seed)
    T = n_days + H
    e = rng.standard_normal((M, T))
    z = std_t(rng, nu, (M, T))
    h0 = mu + rng.standard_normal(M) * eta / np.sqrt(1 - phi * phi)
    r, h = sim_returns(mu, phi, eta, z, e, h0)
    # IV_null(t) for t = 0..n-1 from h_t
    hh = h[:, :n_days] - mu
    acc = np.zeros_like(hh)
    for k in range(1, H + 1):
        var_k = 0.5 * eta * eta * (1 - phi ** (2 * k)) / (1 - phi * phi)
        acc += np.exp(mu + phi ** k * hh + var_k)
    iv2 = ANN / H * acc
    r2 = r * r
    cs = np.concatenate([np.zeros((M, 1)), np.cumsum(r2, axis=1)], axis=1)
    rv2 = ANN / H * (cs[:, 1 + H:1 + H + n_days] - cs[:, 1:1 + n_days])
    iv, rv = np.sqrt(iv2), np.sqrt(rv2)
    stats = {"S1": 100 * (iv - rv), "S2": 100 * (iv2 - rv2), "S3": np.log(iv / rv)}
    # per-window level (observable in a run: the window's own IV), used to express S1/S2 at the
    # reference level sigma_ref (pre-period RV rms) -- removes the cross-window level spread of a
    # near-unit-root vol process, which is not part of a fixed-level comparison
    lvl = np.sqrt(iv2.mean(axis=1))
    norm = {"S1": sigma_ref / lvl, "S2": (sigma_ref / lvl) ** 2, "S3": np.ones(M)}
    out = {}
    for u, x in stats.items():
        wm = x.mean(axis=1)
        wn = wm * norm[u]
        out[u] = {"J": float(wm.mean()), "J_mc_se": float(wm.std(ddof=1) / np.sqrt(M)),
                  "se_null": float(wm.std(ddof=1)), "sd_daily_null": float(x.std(ddof=1)),
                  "c_null": float(n_days * wm.var(ddof=1) / x.var(ddof=1)),
                  "J_at_ref": float(wn.mean()), "se_null_at_ref": float(wn.std(ddof=1))}
    out["iv_rms_volpts"] = float(100 * np.sqrt(iv2.mean()))
    out["rv_rms_volpts"] = float(100 * np.sqrt(rv2.mean()))
    out["window_level_volpts_p10_p50_p90"] = [float(100 * q) for q in np.quantile(lvl, [0.1, 0.5, 0.9])]
    out["sigma_ref_volpts"] = float(100 * sigma_ref)
    return out


def main() -> None:
    res = {"seed": SEED, "M_windows": M_WIN,
           "note": "Null world: IV = true conditional forward vol; J is the structural null (C.4)."}
    for sym in ("BTC", "ETH"):
        days, r = daily_log_returns(sym)
        sel = np.array([NUISANCE_FIRST_IV_DAY < d for d in days])   # returns from 2021-03-25
        rr = r[sel]
        if not np.all(np.isfinite(rr)):
            raise RuntimeError(f"{sym}: gap in pre-period returns")
        cal = calibrate(rr)
        # reference level = pre-period RV rms (same definition as nuisance.py)
        r2 = rr * rr
        cs = np.concatenate([[0.0], np.cumsum(r2)])
        s30 = cs[H:] - cs[:-H]
        sigma_ref = float(np.sqrt(np.mean(ANN / H * s30)))
        res[sym] = {"calibration": cal, "sigma_ref": sigma_ref, "windows": {}, "nu_sensitivity_365": {}}
        for i, n in enumerate(WINDOW_DAYS):
            res[sym]["windows"][str(n)] = null_windows(cal, n, M_WIN, SEED + 1000 + i, sigma_ref)
        for j, nu in enumerate(NU):
            alt = dict(cal, nu=nu)
            w = null_windows(alt, 365, M_WIN, SEED + 2000 + j, sigma_ref)
            res[sym]["nu_sensitivity_365"][str(nu)] = {u: {k: w[u][k] for k in ("J_at_ref", "se_null_at_ref")}
                                                       for u in ("S1", "S2", "S3")}
        print(sym, json.dumps(res[sym]["calibration"], indent=1), flush=True)
    (HERE / "nullworld.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({s: res[s]["windows"]["365"] for s in ("BTC", "ETH")}, indent=1))


if __name__ == "__main__":
    main()
