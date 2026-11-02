"""A1 Stufe 1 -- NUISANCE measurement on 2021-03-01..2024-06-30 (task rule 1).

LABEL (bindend, wird in jede Ausgabe geschrieben): "Nuisance 2021-03-01..2024-06-30, nur
Streuungs-/Kovarianz-Groessen und Verhaeltnisse; der Mittelwert der A1-Rendite (gesamt, Preisbein,
Funding-Bein) und der MOM/REV-Faktorrenditen wird weder ausgegeben noch gespeichert."

Guards:
  * every holding week is checked by ``a1_common.assert_nuisance_holding_week`` (ends <= 2024-06-30);
  * the weekly A1 series lives only in memory; only SDs, autocorrelations, correlations, R^2,
    regression slopes, variance ratios and the funding-persistence RATIO leave this module;
  * ``_no_mean`` asserts that no output key contains a level of a return series.
The persistence RATIO (holding-week funding spread / formation spread) is explicitly allowed
by the task ("nur das Verhaeltnis").
"""
from __future__ import annotations

import json
import pickle
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")

import numpy as np  # noqa: E402

import a1_common as C  # noqa: E402
import a1_model as M  # noqa: E402

LABEL = ("Nuisance 2021-03-01..2024-06-30, nur Streuungs-/Kovarianz-Groessen und Verhaeltnisse; "
         "der Mittelwert der A1-Rendite (gesamt, Preisbein, Funding-Bein) und der MOM/REV-Faktorrenditen "
         "wird weder ausgegeben noch gespeichert.")
K_MIN = 117
MBB_BLOCK = 4          # = registered A3 rules.block_len (moving block over weeks)
MBB_REPS = 2000
SEED = 53


def autocorr(x: np.ndarray, lag: int) -> float:
    a, b = x[:-lag] - x.mean(), x[lag:] - x.mean()
    return float(np.sum(a * b) / np.sum((x - x.mean()) ** 2))


def dispersion_stats(x: np.ndarray) -> dict:
    """SD, autocorrelations 1..4, long-run variance factors and the MBB variance ratio of the
    mean -- never the mean itself."""
    T = x.size
    sd = float(x.std(ddof=1))
    rho = {k: autocorr(x, k) for k in (1, 2, 3, 4)}
    c_trunc = 1.0 + 2.0 * sum((1.0 - k / T) * rho[k] for k in rho)
    c_bartlett = 1.0 + 2.0 * sum((1.0 - k / 5.0) * rho[k] for k in rho)
    c_ar1 = (1.0 + rho[1]) / (1.0 - rho[1])
    # moving-block bootstrap of the mean on the DEMEANED series (variance only)
    rng = np.random.default_rng(SEED)
    z = x - x.mean()
    nb = int(np.ceil(T / MBB_BLOCK))
    reps = np.empty(MBB_REPS)
    for i in range(MBB_REPS):
        st = rng.integers(0, T - MBB_BLOCK + 1, size=nb)
        reps[i] = np.concatenate([z[s:s + MBB_BLOCK] for s in st])[:T].mean()
    se_mbb = float(reps.std(ddof=1))
    ratio = (se_mbb * np.sqrt(T) / sd) ** 2
    return {"T": int(T), "sd": sd, "sd_bp": sd * 1e4, "rho": rho, "c_lrv_trunc4": c_trunc,
            "c_lrv_bartlett4": c_bartlett, "c_ar1": c_ar1, "mbb_block": MBB_BLOCK, "mbb_reps": MBB_REPS,
            "mbb_variance_ratio": float(ratio)}


def ols_r2_slope(y: np.ndarray, X: np.ndarray) -> dict:
    """R^2, residual SD and slopes of y on [1, X] (intercept never reported)."""
    A = np.column_stack([np.ones(y.size), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ coef
    r2 = 1.0 - float(np.sum(resid ** 2) / np.sum((y - y.mean()) ** 2))
    dof = y.size - A.shape[1]
    return {"r2": r2, "resid_sd": float(np.sqrt(np.sum(resid ** 2) / dof)), "slopes": [float(c) for c in coef[1:]],
            "n": int(y.size), "dof": int(dof)}


def decile_ls(char_row: np.ndarray, ret_row: np.ndarray, mask: np.ndarray) -> float:
    """Top-decile minus bottom-decile EW holding-week return of a characteristic (factor return)."""
    idx = np.flatnonzero(mask & ~np.isnan(char_row))
    n = idx.size
    k = max(1, n // 10)
    o = idx[np.argsort(char_row[idx], kind="mergesort")]
    return float(ret_row[o[-k:]].mean() - ret_row[o[:k]].mean())


def _no_mean(obj, path=""):
    banned = ("mean_return", "mean_total", "mean_price", "mean_funding", "alpha", "intercept", "premium")
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(b in str(k).lower() for b in banned):
                raise RuntimeError(f"forbidden output key {path}/{k}")
            _no_mean(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_mean(v, f"{path}[{i}]")


def main() -> None:
    d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
    weeks, key = d["weeks"], d["key"]
    r_log = d["returns"]
    valid = d["returns_valid"]
    R = np.where(valid, np.expm1(r_log), 0.0)           # simple weekly return, 0 where not computable
    Fw = d["f_sum_w"]
    fac = M.market_factors(d)
    ts_all = C.nuisance_formation_weeks(weeks)
    # characteristics of the A3 factors (PIT at t): mom1/mom2/mom4, rev_gap
    rz = np.where(valid, r_log, 0.0)
    mom = {k: np.full_like(rz, np.nan) for k in (1, 2, 4)}
    for k in mom:
        for t in range(rz.shape[0]):
            mom[k][t] = rz[max(0, t - k + 1):t + 1].sum(axis=0)
    rev = np.full_like(rz, np.nan)
    rev[1:] = rz[:-1]

    recs = []
    for t in ts_all:
        C.assert_nuisance_holding_week(weeks, t + 1)
        m = C.universe_mask(d, t)
        u = np.flatnonzero(m)
        if u.size < 10:
            continue
        d1 = C.d1_members(key[t], m)
        p = float(R[t + 1, d1].mean() - R[t + 1, u].mean())
        g = float(Fw[t + 1, u].mean() - Fw[t + 1, d1].mean())
        s = float(key[t, u].mean() - key[t, d1].mean())
        s_next_key = float(key[t + 1, u].mean() - key[t + 1, d1].mean())
        n_invalid = int((~valid[t + 1, d1]).sum() + (~valid[t + 1, u]).sum())
        ku, kn = key[t, u], key[t + 1, u]
        xs_pear = float(np.corrcoef(ku, kn)[0, 1]) if ku.std() > 0 and kn.std() > 0 else np.nan
        rk = np.argsort(np.argsort(ku)); rn = np.argsort(np.argsort(kn))
        xs_spear = float(np.corrcoef(rk, rn)[0, 1])
        d1_next = C.d1_members(key[t + 1], d["alive"][t + 1])
        retention = float(np.isin(d1, d1_next).mean()) if d1_next is not None else np.nan
        recs.append({"t": t, "K": int(u.size), "n_d1": int(d1.size), "p": p, "g": g, "s": s, "s_next_key": s_next_key,
                     "f_ew": fac["ew"][t + 1], "f_btc": fac["btc"][t + 1], "n_invalid": n_invalid,
                     "xs_pear": xs_pear, "xs_spear": xs_spear, "d1_retention": retention,
                     "mom1": decile_ls(mom[1][t], R[t + 1], m), "mom2": decile_ls(mom[2][t], R[t + 1], m),
                     "mom4": decile_ls(mom[4][t], R[t + 1], m), "rev": decile_ls(rev[t], R[t + 1], m)})

    out = {"label": LABEL, "fingerprint": d["fingerprint"], "bases": {}}
    bases = {"K_ge_117": [r for r in recs if r["K"] >= K_MIN], "all_K_ge_10": recs}
    for bname, rs in bases.items():
        p = np.array([r["p"] for r in rs]); g = np.array([r["g"] for r in rs])
        x = p + g
        s = np.array([r["s"] for r in rs]); sn = np.array([r["s_next_key"] for r in rs])
        f_ew = np.array([r["f_ew"] for r in rs]); f_btc = np.array([r["f_btc"] for r in rs])
        ok = ~np.isnan(f_ew) & ~np.isnan(f_btc)
        res = {
            "first_formation_week": weeks[rs[0]["t"]], "last_formation_week": weeks[rs[-1]["t"]],
            "last_holding_week": weeks[rs[-1]["t"] + 1], "n_weeks": len(rs),
            "K": {"min": int(min(r["K"] for r in rs)), "median": float(np.median([r["K"] for r in rs])),
                  "max": int(max(r["K"] for r in rs))},
            "n_d1": {"min": int(min(r["n_d1"] for r in rs)), "median": float(np.median([r["n_d1"] for r in rs])),
                     "max": int(max(r["n_d1"] for r in rs))},
            "invalid_return_cells": int(sum(r["n_invalid"] for r in rs)),
            "total": dispersion_stats(x), "price_leg": dispersion_stats(p), "funding_leg": dispersion_stats(g),
            "corr_price_funding": float(np.corrcoef(p, g)[0, 1]),
            "var_share_price": float(p.var(ddof=1) / x.var(ddof=1)),
            "var_share_funding": float(g.var(ddof=1) / x.var(ddof=1)),
            "var_share_cov": float(2 * np.cov(p, g)[0, 1] / x.var(ddof=1)),
            "formation_spread_bp_sd": float(s.std(ddof=1) * 1e4),
            "formation_spread_bp_median": float(np.median(s) * 1e4),   # formation-side (allowed anywhere)
            # funding persistence: ONLY ratios (task)
            "persistence": {
                "phi_funding_leg_ratio_of_sums": float(g.sum() / s.sum()),
                "phi_key_ratio_of_sums": float(sn.sum() / s.sum()),
                "phi_funding_leg_slope_through_origin": float(np.sum(g * s) / np.sum(s * s)),
                "phi_funding_leg_median_weekly_ratio": float(np.median(g / s)),
                "xs_key_lag1_pearson_mean": float(np.nanmean([r["xs_pear"] for r in rs])),
                "xs_key_lag1_spearman_mean": float(np.nanmean([r["xs_spear"] for r in rs])),
                "d1_retention_mean": float(np.nanmean([r["d1_retention"] for r in rs])),
            },
            "market_regression": {
                "price_on_ew": ols_r2_slope(p[ok], f_ew[ok]), "price_on_btc": ols_r2_slope(p[ok], f_btc[ok]),
                "total_on_ew": ols_r2_slope(x[ok], f_ew[ok]), "total_on_btc": ols_r2_slope(x[ok], f_btc[ok]),
                "sd_f_ew": float(np.std(f_ew[ok], ddof=1)), "sd_f_btc": float(np.std(f_btc[ok], ddof=1)),
            },
        }
        # A3-factor regressions (dispersion only): R^2 and residual SD
        F = {k: np.array([r[k] for r in rs]) for k in ("mom1", "mom2", "mom4", "rev")}
        res["a3_factor_regression"] = {
            "label": "MOM/REV-Faktorrenditen nur als Kovarianz-Groessen (A3-L-Siegel-Geist): kein Faktor-Mittel",
            "total_on_mom1_rev": ols_r2_slope(x, np.column_stack([F["mom1"], F["rev"]])),
            "total_on_mom1_mom2_mom4_rev": ols_r2_slope(x, np.column_stack([F["mom1"], F["mom2"], F["mom4"], F["rev"]])),
            "total_on_mkt_mom1_mom2_mom4_rev": ols_r2_slope(
                x[ok], np.column_stack([f_ew[ok], F["mom1"][ok], F["mom2"][ok], F["mom4"][ok], F["rev"][ok]])),
        }
        for k in ("total_on_mom1_rev", "total_on_mom1_mom2_mom4_rev", "total_on_mkt_mom1_mom2_mom4_rev"):
            reg = res["a3_factor_regression"][k]
            # dispersion of the residual series (autocorrelation for the residual-alpha SE)
            n_reg = len(reg["slopes"])
            if k == "total_on_mkt_mom1_mom2_mom4_rev":
                Xr = np.column_stack([f_ew[ok], F["mom1"][ok], F["mom2"][ok], F["mom4"][ok], F["rev"][ok]]); yr = x[ok]
            elif k == "total_on_mom1_rev":
                Xr = np.column_stack([F["mom1"], F["rev"]]); yr = x
            else:
                Xr = np.column_stack([F["mom1"], F["mom2"], F["mom4"], F["rev"]]); yr = x
            A = np.column_stack([np.ones(yr.size), Xr])
            coef, *_ = np.linalg.lstsq(A, yr, rcond=None)
            e = yr - A @ coef
            reg["resid_dispersion"] = dispersion_stats(e)
            reg["n_regressors"] = n_reg
        # PIT-model calibration: predicted price-leg variance (formation-side betas / idio) vs realized
        cal = {}
        for fname in ("ew", "btc"):
            var_f = float(np.nanvar(np.array([r["f_" + fname] for r in rs]), ddof=1))
            preds = []
            for r in rs:
                t = r["t"]
                m = C.universe_mask(d, t)
                d1 = C.d1_members(key[t], m)
                beta, idio = M.trailing_beta_idio(d, fac[fname], t)
                preds.append(M.predicted_ls_price_variance(beta, idio, d1, m, var_f))
            pm = float(np.mean([q["pred_var"] for q in preds]))
            cal[fname] = {"var_f": var_f, "pred_var_mean": pm, "pred_sd_bp": float(np.sqrt(pm) * 1e4),
                          "factor_var_mean": float(np.mean([q["factor_var"] for q in preds])),
                          "idio_var_mean": float(np.mean([q["idio_var"] for q in preds])),
                          "delta_mean": float(np.mean([q["delta"] for q in preds])),
                          "delta_rms": float(np.sqrt(np.mean([q["delta"] ** 2 for q in preds]))),
                          "kappa_price": float(p.var(ddof=1) / pm), "kappa_total": float(x.var(ddof=1) / pm),
                          "n_d1_mean": float(np.mean([q["n_d1"] for q in preds]))}
        res["pit_model_calibration"] = cal
        # sub-period SDs (52-week blocks, K >= 117 base only meaningful)
        blocks = []
        for i in range(0, len(rs), 52):
            xb = x[i:i + 52]
            if xb.size >= 26:
                blocks.append({"from": weeks[rs[i]["t"]], "to": weeks[rs[min(i + 51, len(rs) - 1)]["t"]],
                               "n": int(xb.size), "sd_bp": float(xb.std(ddof=1) * 1e4),
                               "median_n_d1": float(np.median([r["n_d1"] for r in rs[i:i + 52]]))})
        res["sd_by_52w_block"] = blocks
        out["bases"][bname] = res
    _no_mean(out)
    path = C.WORK / f"nuisance{C.SUFFIX}.json"
    path.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(json.dumps(out, indent=1, default=float)[:20000])


if __name__ == "__main__":
    main()
