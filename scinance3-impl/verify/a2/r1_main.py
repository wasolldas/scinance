"""Review A2 Teil C: independent recomputation of C-1 (null J-(i), analytic SE, binding SE, threshold terms,
transfer to W1/W2, MDE80 single/product/joint), C-2 (funding W2) and C-3 (pilot threshold, pilot power, error
rates).  Own code, own seeds.  RV-1..RV-5 in rv_common.  Prints only sha256 and counts.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rv_common as rv  # noqa: E402

P1 = rv.load_power_p1()
Z = P1.z_krit(0.05)
Z80 = P1.Z_POWER
N = NormalDist()
OI = 0.841741598737593
PRIORS = [5.0, 8.0, 12.0, 16.5, 25.0]
R = 50_000
SEED_NULL = 7001
SEED_MC = 9001
CONDS = ("P2ss", "P3fix", "P3all")
PRE = {"V1": (rv.date(2021, 6, 1), rv.date(2022, 5, 31)), "V2": (rv.date(2022, 6, 1), rv.date(2023, 5, 31)),
       "V3": (rv.date(2023, 6, 1), rv.date(2024, 5, 31)), "VP": (rv.D_LO, rv.D_HI)}
TEST = {"W1": (rv.date(2024, 7, 1), rv.date(2025, 6, 30)), "W2": (rv.W2_LO, rv.W2_HI)}


def sd1(v):
    v = v[np.isfinite(v)]
    return float(np.std(v, ddof=1))


def rho(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1])


def bisect(f, lo=0.01, hi=300.0, tgt=0.80):
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if f(mid) >= tgt else (mid, hi)
    return hi


def main():
    inputs = rv.check_hashes()
    flags, cmeta = rv.load_calendar()
    K = rv.load_cluster_series()
    days, X = K["days"], K["X"]
    di = {d: i for i, d in enumerate(days)}
    slot = {"E": "pre", "P2ss": "pre", "P3fix": "f1530", "P3all": "p3all"}

    def vals(dl, k):
        return X[slot[k]][[di[d] for d in dl]]

    def presets(lo, hi):
        S = rv.sets_of(lo, hi, flags)
        S["P3all"] = [d for d in S["P3all"] if np.isfinite(X["p3all"][di[d]])]
        return S

    # calendar checks pre-period
    pre_days = rv.drange(rv.D_LO, rv.D_HI)
    cal_pre = {"days": len(pre_days),
               "no_btc_eth_option": sum(not rv.fl(flags, d)["opt_both"] for d in pre_days),
               "outlier": sum(rv.fl(flags, d)["outlier"] for d in pre_days),
               "modo_futures": sum(rv.fl(flags, d)["fut"] and d.weekday() < 4 for d in pre_days),
               "fri_futures": sum(rv.fl(flags, d)["fut"] and d.weekday() == 4 for d in pre_days)}
    outliers = sorted(d.isoformat() for d in flags if rv.fl(flags, d)["outlier"] and d >= rv.date(2019, 1, 1))

    VP = presets(*PRE["VP"])
    c = {k: rv.c_rule(vals(VP[k], k)) for k in ("E", "P2ss", "P3fix", "P3all")}
    c_p1 = {k: P1.variance_factor(vals(VP[k], k)[np.isfinite(vals(VP[k], k))], 4).c_hat for k in ("E", "P2ss")}
    fri_w = [d for d in VP["E"] if not rv.month_end_friday(d)]
    R_ = {("E", "P2ss"): 0.0,
          ("E", "P3fix"): rho(vals(fri_w, "E"), vals(fri_w, "P3fix")),
          ("E", "P3all"): rho(vals(VP["E"], "E"), vals(VP["E"], "P3all")),
          ("P2ss", "P3fix"): rho(vals(VP["P2ss"], "P2ss"), vals(VP["P2ss"], "P3fix")),
          ("P2ss", "P3all"): rho(vals(VP["P2ss"], "P2ss"), vals(VP["P2ss"], "P3all")),
          ("P3fix", "P3all"): rho(vals(VP["P3fix"], "P3fix"), vals(VP["P3fix"], "P3all"))}
    sdvp = {k: sd1(vals(VP[k], k)) for k in ("E", "P2ss", "P3fix", "P3all")}

    def common(S):
        s = {k: set(v) for k, v in S.items()}
        return {(a, b): len(s[a] & s[b]) for (a, b) in R_}

    def se_an(Nn, cm, sds, cc=None):
        cc = c if cc is None else cc
        ve = sds["E"] ** 2 * cc["E"] / Nn["E"]
        out = {}
        for j in CONDS:
            vp = sds[j] ** 2 * cc[j] / Nn[j]
            cov = cm[("E", j)] * R_[("E", j)] * sds["E"] * sds[j] / (Nn["E"] * Nn[j])
            out[j] = math.sqrt(ve + vp - 2 * min(0.0, cov))
        return out

    # ---------------------------------------------------------- pre-period windows
    pre = {}
    for k, (nm, (lo, hi)) in enumerate(PRE.items()):
        S = presets(lo, hi)
        nl = rv.Null(S["E"], S["P2ss"])
        x = np.array([X["pre"][di[d]] for d in nl.U])
        J = nl.draws(R, SEED_NULL + k)
        v = nl.replicates(x, J)
        ex = nl.exact(x, h=0.02 if nm != "VP" else 0.05)
        Nn = {kk: len(vv) for kk, vv in S.items()}
        sdw = {kk: sd1(vals(S[kk], kk)) for kk in ("E", "P2ss", "P3fix", "P3all")}
        sa = se_an(Nn, common(S), sdw)
        sa1 = se_an(Nn, common(S), sdw, {kk: 1.0 for kk in c})
        cen = v - v.mean()
        nsd = float(np.std(v, ddof=1))
        f3 = nl.NP / (nl.NP + nl.W)
        sig_ww = math.sqrt(ex["k2"] / float(np.sum((nl.nw - 1) / nl.nw)))
        ss_w = sum(float(np.sum(d ** 2)) for d in nl.devs(x))
        sig_ww_classic = math.sqrt(ss_w / float(np.sum(nl.nw - 1)))
        bind = {}
        for j in CONDS:
            ns = nsd if j == "P2ss" else f3 * nsd
            bind[j] = {"se_an": sa[j], "se_an_c1": sa1[j], "null_sd": ns, "ratio": ns / sa[j],
                       "se_bind": max(sa[j], ns), "src": "analytisch" if sa[j] >= ns else "Null"}
        pre[nm] = {"N": Nn, "n_w_hist": {str(n): int((nl.nw == n).sum()) for n in sorted(set(nl.nw.tolist()))},
                   "fixed_event_weeks": len(nl.fix_ev), "kappa": nl.kappa,
                   "null_mc": {"sd": nsd, "d95_reg": -float(np.quantile(v, 0.05)), "d99_reg": -float(np.quantile(v, 0.01)),
                               "d95_oth": float(np.quantile(v, 0.95)), "d99_oth": float(np.quantile(v, 0.99)),
                               "exkurt": float(np.mean(cen ** 4) / np.mean(cen ** 2) ** 2 - 3), "n_rep": R, "seed": SEED_NULL + k},
                   "null_exact": {"sd": ex["sd"], "d95_reg": -ex["q05"], "d99_reg": -ex["q01"], "d95_oth": ex["q95"],
                                  "d99_oth": ex["q99"], "skew": ex["skew"], "exkurt": ex["exkurt"],
                                  "grid_step_bp": ex["grid_step_scaled"]},
                   "tau95_exact": -ex["q05"] / ex["sd"], "tau95_mc": -float(np.quantile(v, 0.05)) / nsd,
                   "tau99_exact": -ex["q01"] / ex["sd"],
                   "sd_class": sdw, "sigma_within": sig_ww, "sigma_within_classic": sig_ww_classic,
                   "binding": bind, "z_se_bind_P2ss": Z * bind["P2ss"]["se_bind"],
                   "term": "z" if Z * bind["P2ss"]["se_bind"] >= -float(np.quantile(v, 0.05)) else "null"}
    # ---------------------------------------------------------- transfer to W1 / W2
    vkeys = ["V1", "V2", "V3"]
    tau95_mc = max(pre[k]["tau95_mc"] for k in vkeys)
    tau95_ex = max(pre[k]["tau95_exact"] for k in vkeys)
    sig_c = pre["VP"]["sigma_within"]
    stress_k = max(vkeys, key=lambda k: pre[k]["sigma_within"])
    sig_s = pre[stress_k]["sigma_within"]
    sd_s = {j: max(pre[k]["sd_class"][j] for k in vkeys) for j in sdvp}

    def window(S, sds, sig, tau, seed, with_joint=True):
        nl = rv.Null(S["E"], S["P2ss"])
        Nn = {kk: len(vv) for kk, vv in S.items()}
        cm = common(S)
        sa = se_an(Nn, cm, sds)
        nsd = nl.a * sig * math.sqrt(float(np.sum((nl.nw - 1) / nl.nw)))
        f3 = nl.NP / (nl.NP + nl.W)
        seb = {"P2ss": max(sa["P2ss"], nsd), "P3fix": max(sa["P3fix"], f3 * nsd), "P3all": max(sa["P3all"], f3 * nsd)}
        d95 = tau * nsd
        kap = nl.kappa

        def powers(p, f, z=Z, null=True, kp=1.0):
            out = [P1.window_power(f * p, seb["P2ss"], z), P1.window_power(p, seb["P3fix"], z),
                   P1.window_power(p, seb["P3all"], z)]
            if null:
                out.append(P1.condition_power(kap * f * p, kp * d95, nsd))
            return out
        res = {"N": Nn, "weeks_perm": len(nl.perm), "weeks_fixed_event": len(nl.fix_ev), "kappa": kap,
               "fixed_fridays": [nl.U[i[0]].isoformat() for i in nl.fix_ev],
               "se_an": sa, "null_sd": nsd, "d95": d95, "se_bind": seb,
               "z_se_P2ss": Z * seb["P2ss"],
               "mde_single": {"z_P2ss": P1.mde80(seb["P2ss"], Z), "null_P2ss": (d95 + Z80 * nsd) / kap,
                              "z_P3fix": P1.mde80(seb["P3fix"], Z), "z_P3all": P1.mde80(seb["P3all"], Z)}}
        res["mde_single_max"] = max(res["mde_single"].values())
        # joint (report): own covariance model
        if with_joint:
            ve = sds["E"] ** 2 * c["E"] / Nn["E"]
            cov_ep = {j: min(0.0, cm[("E", j)] * R_[("E", j)] * sds["E"] * sds[j] / (Nn["E"] * Nn[j])) for j in CONDS}
            def cpp(i, j):
                key = (i, j) if (i, j) in cm else (j, i)
                return cm[key] * R_[key] * sds[i] * sds[j] / (Nn[i] * Nn[j])
            C = np.zeros((4, 4))
            for a_, i in enumerate(CONDS):
                for b_, j in enumerate(CONDS):
                    C[a_, b_] = sa[i] ** 2 if i == j else ve - cov_ep[i] - cov_ep[j] + cpp(i, j)
            dd = np.sqrt(np.diag(C[:3, :3]))
            sb = np.array([seb[j] for j in CONDS])
            C[:3, :3] = C[:3, :3] / np.outer(dd, dd) * np.outer(sb, sb)
            C[3, 3] = nsd ** 2
            C[0, 3] = C[3, 0] = nsd ** 2
            C[1, 3] = C[3, 1] = C[2, 3] = C[3, 2] = kap * sig ** 2 / nl.W
            L = np.linalg.cholesky(C)
            rng = np.random.default_rng(seed)
            noise = rng.standard_normal((400_000, 4)) @ L.T
            thr = np.array([Z * seb["P2ss"], Z * seb["P3fix"], Z * seb["P3all"], d95])

            def joint(p, f):
                mu = np.array([f * p, p, p, kap * f * p])
                return float(np.mean(np.all(noise >= thr - mu, axis=1)))
        for lab, f in (("u", 1.0), ("oi", OI)):
            m = {"single_P2ss_z": bisect(lambda p: P1.window_power(f * p, seb["P2ss"], Z)),
                 "single_max": bisect(lambda p: min(powers(p, f))),
                 "prod_z": bisect(lambda p: math.prod(powers(p, f, null=False))),
                 "prod_null": bisect(lambda p: math.prod(powers(p, f))),
                 "prod_null_a3": bisect(lambda p: math.prod(powers(p, f, z=P1.Z_PER_WINDOW_A3_PRACTICE)))}
            if with_joint:
                m["joint_null"] = bisect(lambda p: joint(p, f))
            res["mde_" + lab] = m
            res["grid_" + lab] = {str(p): {"prod_null": math.prod(powers(p, f)), "prod_z": math.prod(powers(p, f, null=False)),
                                           **({"joint": joint(p, f)} if with_joint else {})} for p in PRIORS}
        res["_powers"] = powers
        return res

    test, fork = {}, {}
    for k, (wn, (lo, hi)) in enumerate(TEST.items()):
        S = rv.sets_of(lo, hi, flags)
        test[wn] = {"zentral": window(S, sdvp, sig_c, tau95_mc, SEED_MC + k),
                    "stress": window(S, sd_s, sig_s, tau95_mc, SEED_MC + 10 + k),
                    "zentral_tau_exact": window(S, sdvp, sig_c, tau95_ex, 0, with_joint=False)}
    # W2 forks F-3 / F-4 (central)
    S2 = rv.sets_of(*TEST["W2"], flags)
    wk_p2 = {d.isocalendar()[:2] for d in S2["P2ss"]}
    S3 = dict(S2, E=[d for d in S2["E"] if d.isocalendar()[:2] in wk_p2])
    S4 = dict(S2, P2ss=[d for d in rv.drange(*TEST["W2"]) if d.weekday() < 4 and not rv.fl(flags, d)["outlier"]])
    for nm, S in (("F3", S3), ("F4", S4)):
        w = window(S, sdvp, sig_c, tau95_mc, 0, with_joint=False)
        fork[nm] = {"N": w["N"], "kappa": w["kappa"], "se_bind": w["se_bind"], "mde_single_max": w["mde_single_max"],
                    "prod_null_u": w["mde_u"]["prod_null"]}
    # ---------------------------------------------------------- pilot rule U-A2 (k_pred = 1 and expected)
    se_p = {j: pre["VP"]["binding"][j]["se_bind"] for j in CONDS}
    null_p = pre["VP"]["null_exact"]["sd"]
    k_exp = max(1.0, pre["VP"]["binding"]["P2ss"]["se_an"] / null_p)
    def cA2(kp, line="zentral", f=1.0, null=True):
        return max(bisect(lambda p: math.prod(test[w][line]["_powers"](p, f, null=null, kp=kp))) for w in TEST)
    c1, ce = cA2(1.0), cA2(k_exp)
    def pilot_power(mu_c, mu3, cthr):
        t = max(cthr, 2.0 * se_p["P2ss"])
        return (1 - N.cdf((t - mu_c) / se_p["P2ss"])) * N.cdf(mu3 / se_p["P3fix"]) * N.cdf(mu3 / se_p["P3all"])
    grid = {}
    for p in PRIORS:
        tp_u = test["W1"]["zentral"]["grid_u"][str(p)]["prod_null"] * test["W2"]["zentral"]["grid_u"][str(p)]["prod_null"]
        tp_o = test["W1"]["zentral"]["grid_oi"][str(p)]["prod_null"] * test["W2"]["zentral"]["grid_oi"][str(p)]["prod_null"]
        grid[str(p)] = {"kontrast_k1": pilot_power(p, p, c1), "kontrast_kexp": pilot_power(p, p, ce),
                        "ereignis_k1": pilot_power(OI * p, p, c1), "ereignis_kexp": pilot_power(OI * p, p, ce),
                        "two_stage_kontrast_k1": pilot_power(p, p, c1) * tp_u,
                        "two_stage_ereignis_k1": pilot_power(OI * p, p, c1) * tp_o,
                        "pilot_power_at_minimal_threshold_2se": pilot_power(p, p, 0.0)}
    pilot = {"se_pilot": se_p, "null_sd_pilot_exact": null_p, "k_pred_expected": k_exp,
             "c_A2_k1": c1, "c_A2_kexp": ce, "c_A2_k1_by_window": {w: bisect(lambda p, w=w: math.prod(
                 test[w]["zentral"]["_powers"](p, 1.0))) for w in TEST},
             "c_A2_without_null": cA2(1.0, null=False), "c_A2_stress": cA2(1.0, line="stress"),
             "t_at_c": c1 / se_p["P2ss"], "alpha_pilot_k1": 1 - N.cdf(c1 / se_p["P2ss"]),
             "alpha_pilot_kexp": 1 - N.cdf(ce / se_p["P2ss"]),
             "two_stage_false_pass_k1": (1 - N.cdf(c1 / se_p["P2ss"])) * 0.05 ** 2, "grid": grid}
    # ---------------------------------------------------------- funding W2 (RV-3)
    fz = pl.read_parquet(rv.FUND, columns=["symbol", "fts"])
    fd = [rv.ms_day(m) for m in fz["fts"].to_list()]
    assert min(fd) >= rv.W2_LO and max(fd) <= rv.W2_HI
    per = {}
    for s, m, d in zip(fz["symbol"].to_list(), fz["fts"].to_list(), fd):
        per.setdefault(s, {}).setdefault(d, []).append(int(m) % 86_400_000)
    w2days = rv.drange(rv.W2_LO, rv.W2_HI)
    eight = {0, 8 * 3_600_000, 16 * 3_600_000}
    fund = {}
    for s, dd in per.items():
        is8 = {d: sorted(dd.get(d, [])) == sorted(eight) for d in w2days}
        early = {d: any(7 * 3_600_000 <= t < 8 * 3_600_000 for t in dd.get(d, [])) for d in w2days}
        has08 = {d: 8 * 3_600_000 in dd.get(d, []) for d in w2days}
        months = {}
        for d in w2days:
            months.setdefault(d.strftime("%Y-%m"), 0)
            months[d.strftime("%Y-%m")] += 0 if is8[d] else 1
        fund[s] = {"days": len(w2days), "days_with_ts": sum(1 for d in w2days if d in dd), "n_ts": sum(len(v) for v in dd.values()),
                   "days_8h": sum(is8.values()), "days_early_07_08": sum(early.values()), "non8h_by_month": months,
                   "dup": sum(len(v) - len(set(v)) for v in dd.values()), "_has08": has08}
    S2all = rv.sets_of(rv.W2_LO, rv.W2_HI, flags)
    modo_all = [d for d in w2days if d.weekday() < 4]
    we = [d for d in w2days if d.weekday() >= 5]
    both08 = lambda dl: sum(fund["BTCUSDT"]["_has08"][d] and fund["ETHUSDT"]["_has08"][d] for d in dl)  # noqa: E731
    fund_sets = {"E": [len(S2all["E"]), both08(S2all["E"])], "P2ss": [len(S2all["P2ss"]), both08(S2all["P2ss"])],
                 "MoDo_all": [len(modo_all), both08(modo_all)], "WE": [len(we), both08(we)]}
    for s in fund:
        fund[s].pop("_has08")
    for w in test.values():
        for ln in w.values():
            ln.pop("_powers", None)
    w2_modo_fut = [d.isoformat() for d in rv.drange(rv.W2_LO, rv.W2_HI) if d.weekday() < 4 and rv.fl(flags, d)["fut"]]
    out = {"inputs": inputs, "calendar_meta": cmeta, "calendar_pre": cal_pre, "outliers_since_2019": outliers,
           "kline_rows": K["n_rows"], "c_bind_vp": c, "c_bartlett4_power_p1_check": c_p1, "rho": {f"{a}|{b}": v for (a, b), v in R_.items()},
           "sd_class_vp": sdvp, "pre": pre, "tau95_mc_max": tau95_mc, "tau95_exact_max": tau95_ex,
           "sigma_within_central": sig_c, "stress_window": stress_k, "sigma_within_stress": sig_s,
           "test": test, "forks_W2": fork, "pilot": pilot, "funding": fund, "funding_sets_both_08": fund_sets,
           "w2_modo_futures_days": {"n": len(w2_modo_fut), "first": w2_modo_fut[0] if w2_modo_fut else None,
                                    "range_apr_jun_all": w2_modo_fut[-48:][0] if len(w2_modo_fut) >= 48 else None},
           "seeds": {"null": SEED_NULL, "mc": SEED_MC, "n_rep": R}}
    return out


if __name__ == "__main__":
    o = main()
    h = rv.dump(o, rv.WORK / "r1.json")
    print("r1.json sha256", h)
    print("counts pre", {k: v["N"] for k, v in o["pre"].items()})
