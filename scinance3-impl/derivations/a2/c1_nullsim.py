"""C-1: null simulation J-(i) (DEC-103 E4) on the pre-period, binding SE (DEC-94 (5)), threshold terms,
MDE80 single / product against {P2'', P3fix, P3all} for W1/W2 (power_p1).  Rules R-C1..R-C17 in c_common
(Fassung 2: R-C12a channel-free class output, R-C13 scaled test null, R-C14 stress binds, R-C15 Gate (4) factor,
R-C16 PK criterion, R-C17 bivariate report).  Prints only sha256 and counts.  Output: work/c1.json.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_common as cc  # noqa: E402

P1 = cc.load_power_p1()
Z = P1.z_krit(0.05)
Z80 = P1.Z_POWER
Z_A3 = P1.Z_PER_WINDOW_A3_PRACTICE
OI = 0.841741598737593                      # Teil B oi_attenuation FRI/MODO factor_strict (0,842)
PRIORS = [5.0, 8.0, 12.0, 16.5, 25.0]
CONDS = ("P2ss", "P3fix", "P3all")
SERIES = {"E": "r_pre", "P2ss": "r_pre", "P3fix": "r_1530", "P3all": "p3all_slot_mean"}
G4 = 0.95 ** 2                              # R-C15: Gate (4), 0.95 per negative symbol (XRP, BNB), provisional
Z_PK = 2.3263478740408408                   # R-C16: Phi^-1(0.99)
PK_SEEDS = 200
_N = __import__("statistics").NormalDist()


def sd(v: np.ndarray) -> float:
    v = v[np.isfinite(v)]
    return float(np.std(v, ddof=1))


def corr(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1])


def exkurt(v: np.ndarray) -> float:
    c = v - v.mean()                               # centring only
    m2 = float((c ** 2).mean())
    return float((c ** 4).mean() / m2 ** 2 - 3.0)


def skew(v: np.ndarray) -> float:
    c = v - v.mean()
    m2 = float((c ** 2).mean())
    return float((c ** 3).mean() / m2 ** 1.5)


# ------------------------------------------------------------------------------------------------ analytic SE
def se_term(sd_: float, c: float, n: int) -> float:
    return sd_ * math.sqrt(c / n)


def cov_mean(n_common: int, rho: float, sd_a: float, sd_b: float, n_a: int, n_b: int) -> float:
    return n_common * rho * sd_a * sd_b / (n_a * n_b)


def se_contrasts(N: dict, common: dict, sds: dict, cs: dict, rhos: dict) -> dict:
    """R-C7: SE of Delta_j = E - P_j; event-placebo covariance only if it raises the SE (no credit)."""
    se_e = se_term(sds["E"], cs["E"], N["E"])
    out = {"se_event": se_e}
    for j in CONDS:
        se_p = se_term(sds[j], cs[j], N[j])
        cv = cov_mean(common[("E", j)], rhos[("E", j)], sds["E"], sds[j], N["E"], N[j])
        cv_used = min(0.0, cv)
        out[j] = {"se_placebo": se_p, "cov_event_placebo_used": cv_used,
                  "se": math.sqrt(se_e ** 2 + se_p ** 2 - 2.0 * cv_used),
                  "se_c1": math.sqrt((sds["E"] ** 2) / N["E"] + (sds[j] ** 2) / N[j] - 2.0 * cv_used)}
    return out


def contrast_cov(N: dict, common: dict, sds: dict, cs: dict, rhos: dict, se: dict) -> np.ndarray:
    """Covariance matrix of (Delta_P2ss, Delta_P3fix, Delta_P3all) (R-15 of Teil B, cross terms from same-day rho)."""
    var_e = se["se_event"] ** 2
    C = np.zeros((3, 3))
    for a, ja in enumerate(CONDS):
        for b, jb in enumerate(CONDS):
            if a == b:
                C[a, b] = se[ja]["se"] ** 2
                continue
            c_ea = min(0.0, cov_mean(common[("E", ja)], rhos[("E", ja)], sds["E"], sds[ja], N["E"], N[ja]))
            c_eb = min(0.0, cov_mean(common[("E", jb)], rhos[("E", jb)], sds["E"], sds[jb], N["E"], N[jb]))
            key = (ja, jb) if (ja, jb) in common else (jb, ja)
            c_ab = cov_mean(common[key], rhos[key], sds[ja], sds[jb], N[ja], N[jb])
            C[a, b] = var_e - c_ea - c_eb + c_ab
    return C


# ------------------------------------------------------------------------------------------------ null per window
def null_block(pn: cc.PermNull, x: np.ndarray, seed: int) -> dict:
    L = pn.draw_labels(cc.R_REP, seed)
    v = pn.centred_replicates(x, L)
    ex = pn.exact_cumulants(x)
    R = v.size
    q = lambda p: float(np.quantile(v, p))          # noqa: E731  (quantiles of the CENTRED null)
    sv = np.sort(v)
    def ci(p):
        k = R * p
        h = 1.96 * math.sqrt(R * p * (1 - p))
        lo, hi = int(max(0, math.floor(k - h))), int(min(R - 1, math.ceil(k + h)))
        return [float(sv[lo]), float(sv[hi])]
    sdv = float(np.std(v, ddof=1))
    d95r, d99r = -q(0.05), -q(0.01)
    c05, c01 = ci(0.05), ci(0.01)
    return {"n_rep": R, "seed": seed, "sd_mc": sdv, "sd_exact": ex["sd"],
            "d95_reg": d95r, "d99_reg": d99r, "d95_reg_ci95_mc": [-c05[1], -c05[0]],
            "d99_reg_ci95_mc": [-c01[1], -c01[0]], "d95_other": q(0.95), "d99_other": q(0.99),
            "tail_factor_95_reg": d95r / sdv, "tail_factor_99_reg": d99r / sdv,
            "excess_kurtosis_mc": exkurt(v), "excess_kurtosis_exact": ex["excess_kurtosis"],
            "skew_mc": skew(v), "skew_exact": ex["skew"],
            "label_check": "alle Replikat-Zeilen gegen den Hash des realen Label-Vektors geprueft (R-C6)",
            "_sum_within_var_pop": ex["sum_within_var_pop"]}


def structure(pn: cc.PermNull) -> dict:
    nw = pn.n_w
    return {"n_U": pn.n, "W_event": pn.W, "N_P2ss": pn.N_P, "weeks_permutable": len(pn.perm_weeks),
            "weeks_fixed_event_only_friday": len(pn.fixed_event_weeks),
            "placebo_days_in_weeks_without_event_friday": pn.fixed_placebo_days,
            "n_w_hist": {str(k): int((nw == k).sum()) for k in sorted(set(nw.tolist()))},
            "a_weight": pn.a, "sum_within_dof": float(np.sum((nw - 1) / nw)),
            "kappa_efficiency": pn.a * float(np.sum((nw - 1) / nw)),
            "f_p3_over_p2": pn.N_P / (pn.N_P + pn.W)}


def shift_sd_iid(pn: cc.PermNull, sigma: float) -> float:
    """SD (iid model) of the null shift E_perm[T] implied by the calendar structure (a location, never computed
    from returns; only its spread from sigma and the weights)."""
    var = 0.0
    for w in pn.perm_weeks:
        n = len(pn.idx_of_week[w])
        var += (1.0 / pn.W - (n - 1) / pn.N_P) ** 2 * sigma ** 2 / n
    var += len(pn.fixed_event_weeks) * (sigma / pn.W) ** 2
    var += pn.fixed_placebo_days * (sigma / pn.N_P) ** 2
    return math.sqrt(var)


# ------------------------------------------------------------------------------------------------ power helpers
def null_power(pi_c: float, nul: dict, mode: str) -> float:
    """Null condition of P2'' (q95 term): 'unscaled' (Fassung 1): Phi((kappa pi - d95)/SD_null);
    'scaled' (R-C13): threshold k d95, SD of the centred statistic k SD_null (= SE_T)."""
    k = nul["k"] if mode == "scaled" else 1.0
    return P1.condition_power(nul["kappa"] * pi_c, k * nul["d95"], k * nul["sd"])


def cond_powers(pi_e: float, f_oi: float, se: dict, nul: dict | None, z: float, mode: str = "scaled",
                g4: float = 1.0) -> dict:
    pc = f_oi * pi_e
    out = {"z_P2ss": P1.window_power(pc, se["P2ss"], z),
           "z_P3fix": P1.window_power(pi_e, se["P3fix"], z),
           "z_P3all": P1.window_power(pi_e, se["P3all"], z)}
    if nul is not None:
        out["null_P2ss"] = null_power(pc, nul, mode)
    if g4 != 1.0:
        out["gate4_provisional"] = g4
    return out


def bisect(fun, lo=0.1, hi=200.0, target=0.80) -> float:
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if fun(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


_U = np.linspace(-9.0, 9.0, 7201)
_PHI = np.exp(-0.5 * _U ** 2) / math.sqrt(2.0 * math.pi)
_ERFC = np.frompyfunc(math.erfc, 1, 1)


def biv_upper(a: float, b: float, rho: float) -> float:
    """P(Z1 >= a, Z2 >= b) for a standard bivariate normal with correlation rho (quadrature, deterministic)."""
    if rho >= 1.0 - 1e-12:
        return 1.0 - _N.cdf(max(a, b))
    s = math.sqrt(1.0 - rho * rho)
    m = _U >= a
    if not m.any():
        return 0.0
    u = _U[m]
    cond = 0.5 * np.asarray(_ERFC((b - rho * u) / (s * math.sqrt(2.0))), dtype=float)
    return float(np.trapezoid(_PHI[m] * cond, u))


def p2_bivariate(pi_c: float, se_y: float, z: float, nul: dict, mode: str) -> float:
    """R-C17 (report): exact P2'' condition y >= z SE and y - max(0, m) >= k d95 under the model of the mode."""
    if mode == "scaled":
        sd_c, thr_c = nul["k"] * nul["sd"], nul["k"] * nul["d95"]
        rho = math.sqrt(max(0.0, 1.0 - (nul["k"] * nul["sd_shift"]) ** 2 / se_y ** 2))
    else:
        sd_c, thr_c, rho = nul["sd"], nul["d95"], min(1.0, nul["sd"] / se_y)
    return biv_upper((z * se_y - pi_c) / se_y, (thr_c - nul["kappa"] * pi_c) / sd_c, rho)


class Joint:
    """Monte Carlo P(all test conditions) under a multivariate normal model (report only); the noise is drawn once
    (common random numbers), only the means move with the prior.  Fourth variable = centred null statistic c with
    SD sd_c, correlation rho with y_P2'' and covariance with the P3 contrasts through y_P2''."""

    def __init__(self, se: dict, C3: np.ndarray, nul: dict | None, z: float, draws: np.ndarray, mode: str):
        thr = [z * se["P2ss"], z * se["P3fix"], z * se["P3all"]]
        if nul is None:
            C = C3
        else:
            if mode == "scaled":
                sd_c, thr_c = nul["k"] * nul["sd"], nul["k"] * nul["d95"]
                rho = math.sqrt(max(0.0, 1.0 - (nul["k"] * nul["sd_shift"]) ** 2 / se["P2ss"] ** 2))
            else:
                sd_c, thr_c, rho = nul["sd"], nul["d95"], min(1.0, nul["sd"] / se["P2ss"])
            C = np.zeros((4, 4))
            C[:3, :3] = C3
            C[3, 3] = sd_c ** 2
            C[0, 3] = C[3, 0] = rho * sd_c * se["P2ss"]
            for a in (1, 2):
                C[a, 3] = C[3, a] = rho * (sd_c / se["P2ss"]) * C3[0, a]
            C += np.eye(4) * 1e-12
            thr.append(thr_c)
        Lc = np.linalg.cholesky(C)
        self.noise = draws[:, :C.shape[0]] @ Lc.T
        self.thr = np.array(thr)
        self.nul = nul

    def __call__(self, pi_e: float, f_oi: float) -> float:
        mu = [f_oi * pi_e, pi_e, pi_e]
        if self.nul is not None:
            mu.append(self.nul["kappa"] * f_oi * pi_e)
        return float(np.mean(np.all(self.noise >= self.thr - np.array(mu), axis=1)))


# ------------------------------------------------------------------------------------------------ main
def weekday_flags() -> dict:
    """Pre-only mode (orchestrator note 2026-10-31): in the pre-period there are no Mon-Thu futures days and no
    outlier days (Teil A 3a / N5), so the classes are pure weekday classes; verified against the calendar in the
    full run (the pre-period sections must be bit-identical)."""
    return {d: {"opt_BTC": True, "opt_ETH": True, "fut_BTC": False, "fut_ETH": False, "max_delay_s": 0.0}
            for d in cc.days_range(cc.FIRST_RETURN_DAY, cc.LAST_RETURN_DAY)}


def main(pre_only: bool = False) -> dict:
    if pre_only:
        inputs = {cc.F_KLINE.name: cc.sha256(cc.F_KLINE), "abgleich_extract_log": "ausstehend (pre-only)"}
        flags, cal_meta = weekday_flags(), {"mode": "pre-only, reine Wochentagsklassen"}
    else:
        inputs = cc.check_inputs([cc.F_KLINE.name, cc.F_CAL.name])
        flags, cal_meta = cc.load_calendar_flags()
    days, closes, kmeta = cc.load_closes()
    assert days[0].isoformat() == cc.FIRST_RETURN_DAY and days[-1].isoformat() <= cc.LAST_RETURN_DAY
    di = {d: i for i, d in enumerate(days)}
    me = np.array([cc.is_month_end_friday(d) for d in days])
    sr = {s: cc.slot_returns(closes[s]) for s in closes}
    X = {"pre": 0.5 * (sr["BTCUSDT"]["pre"] + sr["ETHUSDT"]["pre"]),
         "fix1530": 0.5 * (sr["BTCUSDT"]["fix1530"] + sr["ETHUSDT"]["fix1530"]),
         "p3all": 0.5 * (cc.p3all_value(sr["BTCUSDT"]["profile"], me) + cc.p3all_value(sr["ETHUSDT"]["profile"], me))}
    del closes, sr
    slot_of = {"E": "pre", "P2ss": "pre", "P3fix": "fix1530", "P3all": "p3all"}

    def vals(dl, key):
        return X[slot_of[key]][[di[d] for d in dl]]

    def disp(S, sds_):
        """R-C12a: class dispersion as {series, n, sd}; never a union of classes."""
        return {j: {"series": SERIES[j], "n": int(np.isfinite(vals(S[j], j)).sum()), "sd": sds_[j]}
                for j in ("E", "P2ss", "P3fix", "P3all")}

    # ---------------------------------------------------------------- classes and calendar checks (pre-period)
    pre_days_all = cc.days_range(cc.FIRST_RETURN_DAY, cc.LAST_RETURN_DAY)
    chk = {"days": len(pre_days_all),
           "days_without_btc_eth_option_delivery": sum(not cc.day_flags(d, flags)["opt_both"] for d in pre_days_all),
           "outlier_days": sum(cc.day_flags(d, flags)["outlier"] for d in pre_days_all),
           "modo_futures_days": sum(cc.day_flags(d, flags)["fut_any"] and d.weekday() < 4 for d in pre_days_all),
           "fridays_with_futures_delivery": sum(cc.day_flags(d, flags)["fut_any"] and d.weekday() == 4
                                                for d in pre_days_all)}
    outl_all = sorted(d.isoformat() for d in flags if cc.day_flags(d, flags)["outlier"] and d.year >= 2020)

    # ---------------------------------------------------------------- pooled c_bind and same-day correlations (VP)
    def pre_sets(lo, hi):
        S = cc.window_sets(lo, hi, flags)
        S["P3all"] = [d for d in S["P3all"] if np.isfinite(X["p3all"][di[d]])]   # first extract day has no slot 00:00
        return S

    VP = pre_sets(cc.FIRST_RETURN_DAY, cc.LAST_RETURN_DAY)
    cser = {k: cc.c_bind(vals(VP[k if k != "E" else "E"], k), P1) for k in ("E", "P2ss", "P3fix", "P3all")}
    cs = {k: cser[k]["c_bind"] for k in cser}
    fri_w = [d for d in VP["E"] if not cc.is_month_end_friday(d)]
    modo = VP["P2ss"]
    rhos = {("E", "P2ss"): 0.0,
            ("E", "P3fix"): corr(vals(fri_w, "E"), vals(fri_w, "P3fix")),
            ("E", "P3all"): corr(vals(VP["E"], "E"), vals(VP["E"], "P3all")),
            ("P2ss", "P3fix"): corr(vals(modo, "P2ss"), vals(modo, "P3fix")),
            ("P2ss", "P3all"): corr(vals(modo, "P2ss"), vals(modo, "P3all")),
            ("P3fix", "P3all"): corr(vals(VP["P3fix"], "P3fix"), vals(VP["P3fix"], "P3all"))}
    sd_vp = {k: sd(vals(VP[k], k)) for k in ("E", "P2ss", "P3fix", "P3all")}

    def commons(S):
        sE, s2, s3f, s3a = set(S["E"]), set(S["P2ss"]), set(S["P3fix"]), set(S["P3all"])
        return {("E", "P2ss"): len(sE & s2), ("E", "P3fix"): len(sE & s3f), ("E", "P3all"): len(sE & s3a),
                ("P2ss", "P3fix"): len(s2 & s3f), ("P2ss", "P3all"): len(s2 & s3a),
                ("P3fix", "P3all"): len(s3f & s3a)}

    def counts(S):
        return {k: len(v) for k, v in S.items()}

    # Teil B reproduction (pooled cluster SD and c of FRI / MODO)
    repro = {"sd_cluster_FRI": sd_vp["E"], "sd_cluster_MODO": sd_vp["P2ss"], "c_bind_FRI": cs["E"],
             "c_bind_MODO": cs["P2ss"], "teil_B": {"sd_cluster_FRI": 43.82975761851162,
                                                   "sd_cluster_MODO": 42.45299339852021,
                                                   "c_bind_FRI": 1.1490904838090488, "c_bind_MODO": 1.3177393036700162}}

    # ---------------------------------------------------------------- pre-period windows: null and analytic SE
    pre = {}
    pn_vp = None
    for k, (wi, (lo, hi)) in enumerate(cc.PRE_WINDOWS.items()):
        S = pre_sets(lo, hi)
        U = sorted(S["E"] + S["P2ss"])
        pn = cc.PermNull(U, np.array([d.weekday() == 4 for d in U]))
        x = np.array([X["pre"][di[d]] for d in U])
        nb = null_block(pn, x, cc.SEED_NULL + k)
        st = structure(pn)
        sdw = {j: sd(vals(S[j], j)) for j in ("E", "P2ss", "P3fix", "P3all")}
        N = counts(S)
        cm = commons(S)
        se_win = se_contrasts(N, cm, sdw, cs, rhos)
        se_vp_scaled = se_contrasts(N, cm, sd_vp, cs, rhos)
        sigma_w2 = nb["_sum_within_var_pop"] / st["sum_within_dof"]
        blk = {"range": [lo, hi], "counts": N, "structure": st, "null_P2ss": {kk: v for kk, v in nb.items()
                                                                                 if not kk.startswith("_")},
               "sigma_within_cluster_pre": math.sqrt(sigma_w2),
               "sd_null_shift_iid_sigma_within": shift_sd_iid(pn, math.sqrt(sigma_w2)),
               "class_dispersion": disp(S, sdw),
               "se_analytic_window_sd": {j: {"se": se_win[j]["se"], "se_c1": se_win[j]["se_c1"]} for j in CONDS},
               "se_analytic_vp_sd": {j: se_vp_scaled[j]["se"] for j in CONDS},
               "se_event_window_sd": se_win["se_event"]}
        sdn = nb["sd_mc"]
        f3 = st["f_p3_over_p2"]
        bind = {}
        for j in CONDS:
            null_sd = sdn if j == "P2ss" else f3 * sdn
            se_a = se_win[j]["se"]
            seb = max(se_a, null_sd)
            row = {"se_analytic": se_a, "se_analytic_c1": se_win[j]["se_c1"], "null_sd": null_sd,
                   "ratio_null_to_analytic": null_sd / se_a, "ratio_null_to_analytic_c1": null_sd / se_win[j]["se_c1"],
                   "se_bind": seb, "se_bind_source": "analytisch" if se_a >= null_sd else "Null-Simulation",
                   "z_se_bind": Z * seb}
            if j == "P2ss":
                row["d95_reg"] = nb["d95_reg"]
                row["threshold_terms"] = {"null_d95_reg": nb["d95_reg"], "z_krit_se": Z * seb}
                row["threshold_binding_term"] = "z_krit x SE" if Z * seb >= nb["d95_reg"] else "Null-Quantil"
                row["margin_z_minus_null_95"] = Z * seb - nb["d95_reg"]
                row["margin_z_minus_null_99_vs_99"] = P1.z_krit(0.01) * seb - nb["d99_reg"]
                kk = max(1.0, seb / sdn)
                row["scaled_null_R_C13"] = {"k": kk, "q95_eff_term": kk * nb["d95_reg"], "z_krit_se": Z * seb,
                                            "binding_term": "z_krit x SE" if Z * seb >= kk * nb["d95_reg"]
                                            else "skaliertes Null-Quantil",
                                            "rise_over_z_term": max(0.0, kk * nb["d95_reg"] - Z * seb)}
            else:
                row["null_d95_reg_equiv"] = f3 * nb["d95_reg"]
                row["threshold_binding_term"] = ("z_krit x SE (Null-Bedingung identisch mit der von P2'', "
                                                 "R-C6-Identitaet)")
            bind[j] = row
        blk["binding"] = bind
        pre[wi] = blk
        if wi.startswith("VP"):
            pn_vp = (pn, sigma_w2)

    # R-C12a cross-file check against the committed Teil B JSON (structure only: series and day sets; Teil B classes
    # of the pre-period are weekday classes; no value is read or combined)
    def tb_sets():
        F = set(VP["E"])
        me_ = {d for d in F if cc.is_month_end_friday(d)}
        mo = set(VP["P2ss"])
        we = {d for d in pre_days_all if d.weekday() >= 5}
        return {"FRI": F, "FRI_W": F - me_, "FRI_MQ": me_, "MODO": mo, "WE": we, "NONFRI": mo | we,
                "ALL": set(pre_days_all)}
    tbs = tb_sets()
    same_series = {"E": "pre", "P2ss": "pre", "P3fix": "fix1530", "P3all": None}   # P3all: 40-slot values on FRI_MQ
    cross = []
    from itertools import combinations as _comb
    for j, ser in same_series.items():
        mine = set(VP[j])
        if ser is None:
            continue
        for a, b in _comb(tbs, 2):
            if not (tbs[a] & tbs[b]) and (tbs[a] | tbs[b]) == mine:
                cross.append({"class": j, "series": ser, "union_of_teil_B": [a, b]})
        for a in tbs:
            rest = tbs[a] - mine
            if mine < tbs[a] and any(rest == tbs[b] for b in tbs):
                cross.append({"class": j, "series": ser, "part_of_teil_B": a,
                              "complement_in_teil_B": [b for b in tbs if rest == tbs[b]]})
    cross_file = {"teil_B_json": "a2_vorarbeit.json (Commit 363f3d9), teil_B_sigma30.dispersion.<slot>.<Klasse>.CLUSTER",
                  "findings": cross,
                  "identical_classes": [{"class": j, "teil_B": [a for a in tbs if tbs[a] == set(VP[j])]}
                                        for j in ("E", "P2ss", "P3fix") if any(tbs[a] == set(VP[j]) for a in tbs)]}

    if pre_only:
        return {"label": cc.LABEL, "rules": "R-C1..R-C17 (Docstring c_common.py)", "inputs_sha256": inputs,
                "mode": "pre-only (Kerzen + Wochentagsklassen; W1/W2 erst mit Kalender)",
                "power_p1_sha256": cc.sha256(cc.POWER_P1), "kline_meta": kmeta, "calendar_meta": cal_meta,
                "z_krit": Z, "c_bind_pooled_pre_period": cser,
                "same_day_rho": {f"{a}|{b}": v for (a, b), v in rhos.items()},
                "class_dispersion_pre_period_pooled": disp(VP, sd_vp), "teil_B_reproduction": repro,
                "cross_file_check_teil_B": cross_file, "pre_windows": pre,
                "n_rep_null": cc.R_REP, "seed_null_base": cc.SEED_NULL}

    # ---------------------------------------------------------------- transfer to W1/W2 (calendar only)
    pn_vp_obj, sig2_vp = pn_vp
    v_keys = [k for k in cc.PRE_WINDOWS if not k.startswith("VP")]
    tau95 = max(pre[k]["null_P2ss"]["tail_factor_95_reg"] for k in v_keys)
    tau99 = max(pre[k]["null_P2ss"]["tail_factor_99_reg"] for k in v_keys)
    stress_key = max(v_keys, key=lambda k: pre[k]["sigma_within_cluster_pre"])
    sig2_stress = pre[stress_key]["sigma_within_cluster_pre"] ** 2
    sd_stress = {j: pre[stress_key]["class_dispersion"][j]["sd"] for j in ("E", "P2ss", "P3fix", "P3all")}
    LINES = (("stress", sd_stress, sig2_stress), ("zentral", sd_vp, sig2_vp))   # R-C14: stress binds

    def line_eval(S, sds_, sig2, seed, full=True):
        U = sorted(S["E"] + S["P2ss"])
        pn = cc.PermNull(U, np.array([d.weekday() == 4 for d in U]))
        st = structure(pn)
        N, cm = counts(S), commons(S)
        se_a = se_contrasts(N, cm, sds_, cs, rhos)
        null_sd = pn.a * math.sqrt(sig2 * st["sum_within_dof"])
        kappa, f3 = st["kappa_efficiency"], st["f_p3_over_p2"]
        seb = {"P2ss": max(se_a["P2ss"]["se"], null_sd), "P3fix": max(se_a["P3fix"]["se"], f3 * null_sd),
               "P3all": max(se_a["P3all"]["se"], f3 * null_sd)}
        d95 = tau95 * null_sd
        k_w = max(1.0, seb["P2ss"] / null_sd)
        nul = {"sd": null_sd, "d95": d95, "kappa": kappa, "k": k_w,
               "sd_shift": shift_sd_iid(pn, math.sqrt(sig2))}
        res = {"structure": st, "counts": N,
               "se_analytic": {j: se_a[j]["se"] for j in CONDS},
               "se_analytic_c1": {j: se_a[j]["se_c1"] for j in CONDS},
               "cov_event_placebo_used": {j: se_a[j]["cov_event_placebo_used"] for j in CONDS},
               "null_sd_transfer": null_sd, "null_d95_transfer": d95, "null_d99_transfer": tau99 * null_sd,
               "kappa_efficiency": kappa, "k_scale_R_C13": k_w, "sd_null_shift_iid_sigma_within": nul["sd_shift"],
               "se_bind": seb,
               "se_bind_source": {j: ("analytisch" if seb[j] == se_a[j]["se"] else "Null-Simulation") for j in CONDS},
               "largest_se_condition": max(CONDS, key=lambda j: seb[j]),
               "threshold_P2ss": {"z_krit_se": Z * seb["P2ss"], "null_term_unscaled_d95": d95,
                                  "null_term_scaled_k_d95": k_w * d95,
                                  "binding_unscaled": "z_krit x SE" if Z * seb["P2ss"] >= d95 else "Null-Quantil",
                                  "binding_scaled": ("z_krit x SE" if Z * seb["P2ss"] >= k_w * d95
                                                     else "skaliertes Null-Quantil (+ max(0, Zentrum))"),
                                  "rise_scaled_over_z_at_zero_shift": max(0.0, k_w * d95 - Z * seb["P2ss"]),
                                  "rise_scaled_over_unscaled_null_term": (k_w - 1.0) * d95}}
        res["mde80_single_by_condition_contrast_scale"] = {
            "z_P2ss": P1.mde80(seb["P2ss"], Z),
            "null_P2ss_unscaled_fassung1": (d95 + Z80 * null_sd) / kappa,
            "null_P2ss_scaled": (k_w * d95 + Z80 * k_w * null_sd) / kappa,
            "z_P3fix": P1.mde80(seb["P3fix"], Z), "z_P3all": P1.mde80(seb["P3all"], Z)}
        if not full:
            out = {"counts": N, "weeks_permutable": st["weeks_permutable"],
                   "weeks_fixed": st["weeks_fixed_event_only_friday"], "kappa_efficiency": kappa,
                   "se_bind": seb, "null_sd_transfer": null_sd, "k_scale_R_C13": k_w,
                   "mde80_single_by_condition_contrast_scale": res["mde80_single_by_condition_contrast_scale"]}
            for lab, f_oi in (("unabgeschwaecht", 1.0), ("oi_0842", OI)):
                out[f"product_scaled_gate4_{lab}"] = bisect(
                    lambda p: math.prod(cond_powers(p, f_oi, seb, nul, Z, "scaled", G4).values()))
                out[f"product_scaled_{lab}"] = bisect(
                    lambda p: math.prod(cond_powers(p, f_oi, seb, nul, Z, "scaled").values()))
                out[f"product_unscaled_fassung1_{lab}"] = bisect(
                    lambda p: math.prod(cond_powers(p, f_oi, seb, nul, Z, "unscaled").values()))
            return out
        C3 = contrast_cov(N, cm, sds_, cs, rhos, se_a)
        dvec = np.sqrt(np.diag(C3))
        Rm = C3 / np.outer(dvec, dvec)
        sb = np.array([seb[j] for j in CONDS])
        C3b = Rm * np.outer(sb, sb)
        res["test_corr_matrix"] = Rm.tolist()
        draws = np.random.default_rng(seed).standard_normal((cc.N_MC, 4))
        j_s = Joint(seb, C3b, nul, Z, draws, "scaled")
        j_u = Joint(seb, C3b, nul, Z, draws, "unscaled")
        j_z = Joint(seb, C3b, None, Z, draws, "scaled")
        for lab, f_oi in (("unabgeschwaecht", 1.0), ("oi_0842", OI)):
            def prod(p, mode="scaled", g4=1.0, z=Z, with_null=True):
                return math.prod(cond_powers(p, f_oi, seb, nul if with_null else None, z, mode, g4).values())

            def biv(p, mode):
                return (p2_bivariate(f_oi * p, seb["P2ss"], Z, nul, mode)
                        * P1.window_power(p, seb["P3fix"], Z) * P1.window_power(p, seb["P3all"], Z))
            m = {"product_scaled_gate4_bindend_vorlaeufig": bisect(lambda p: prod(p, g4=G4)),
                 "product_scaled": bisect(lambda p: prod(p)),
                 "product_unscaled_fassung1": bisect(lambda p: prod(p, mode="unscaled")),
                 "product_z_only": bisect(lambda p: prod(p, with_null=False)),
                 "product_bivariate_scaled_bericht": bisect(lambda p: biv(p, "scaled")),
                 "product_bivariate_unscaled_bericht": bisect(lambda p: biv(p, "unscaled")),
                 "product_scaled_gate4_a3_practice": bisect(lambda p: prod(p, g4=G4, z=Z_A3)),
                 "single_max_over_conditions_scaled": bisect(
                     lambda p: min(cond_powers(p, f_oi, seb, nul, Z, "scaled").values())),
                 "joint_scaled_bericht": bisect(lambda p: j_s(p, f_oi)),
                 "joint_scaled_gate4_bericht": bisect(lambda p: G4 * j_s(p, f_oi)),
                 "joint_unscaled_fassung1_bericht": bisect(lambda p: j_u(p, f_oi)),
                 "joint_z_only_bericht": bisect(lambda p: j_z(p, f_oi))}
            pm = m["single_max_over_conditions_scaled"]
            m["single_binding_condition"] = min(cond_powers(pm - 1e-6, f_oi, seb, nul, Z, "scaled").items(),
                                                key=lambda kv: kv[1])[0]
            tgt = m["product_scaled_gate4_bindend_vorlaeufig"]
            e_share = G4 * j_s(tgt, f_oi)
            m["pk_at_target"] = {"target": tgt, "expected_pass_share_joint_x_gate4": e_share,
                                 "binomial_se_200": math.sqrt(e_share * (1 - e_share) / PK_SEEDS),
                                 "criterion_b": e_share - Z_PK * math.sqrt(e_share * (1 - e_share) / PK_SEEDS),
                                 "product_at_target": prod(tgt, g4=G4)}
            res[f"mde80_event_scale_{lab}"] = m
            grid = {}
            for pr in PRIORS:
                cp = cond_powers(pr, f_oi, seb, nul, Z, "scaled", G4)
                grid[str(pr)] = {"single_powers": cp, "product_scaled_gate4": math.prod(cp.values()),
                                 "product_scaled": prod(pr), "product_unscaled_fassung1": prod(pr, mode="unscaled"),
                                 "joint_scaled_gate4_bericht": G4 * j_s(pr, f_oi)}
            res[f"prior_grid_{lab}"] = grid
        res["_nul"] = nul
        return res

    test = {}
    for wi_, (wn, (lo, hi)) in enumerate(cc.TEST_WINDOWS.items()):
        S = cc.window_sets(lo, hi, flags)
        U = sorted(S["E"] + S["P2ss"])
        pn = cc.PermNull(U, np.array([d.weekday() == 4 for d in U]))
        lines = {}
        for li, (line, sds_, sig2) in enumerate(LINES):
            r = line_eval(S, sds_, sig2, cc.SEED_MC + wi_ + 10 * (line == "stress"))
            r.pop("_nul")
            st_, n_ = r.pop("structure"), r.pop("counts")
            lines[line] = r
        test[wn] = {"range": [lo, hi], "counts": n_, "common_days": {f"{a}|{b}": v for (a, b), v in commons(S).items()},
                    "structure": st_,
                    "fixed_event_fridays_without_p2ss_partner": [pn.days[pn.idx_of_week[w][0]].isoformat()
                                                                 for w in pn.fixed_event_weeks],
                    "lines": lines}

    # W2 forks F-1 / F-3 / F-4 (Abschnitt 5.3), both lines, compact
    S2 = cc.window_sets(*cc.TEST_WINDOWS["W2"], flags)
    wk_with_p2 = {d.isocalendar()[:2] for d in S2["P2ss"]}
    S_f3 = dict(S2, E=[d for d in S2["E"] if d.isocalendar()[:2] in wk_with_p2])
    S_f4 = dict(S2, P2ss=[d for d in cc.days_range(*cc.TEST_WINDOWS["W2"])
                          if d.weekday() < 4 and not cc.day_flags(d, flags)["outlier"]])
    test["W2"]["forks"] = {line: {"F1_woertlich": line_eval(S2, sds_, sig2, 0, full=False),
                                  "F3_E_ohne_Freitage_ohne_P2ss_Partner": line_eval(S_f3, sds_, sig2, 0, full=False),
                                  "F4_P2strich_alle_MoDo": line_eval(S_f4, sds_, sig2, 0, full=False)}
                           for line, sds_, sig2 in LINES}

    # regimes (C10 by the product in both windows; DEC52 by the product of the DEC-52 gate powers of the z conditions
    # times the weaker window's null factor and the Gate-(4) factor - B-9 (a), consistent treatment)
    regimes = {}
    for line, _, _ in LINES:
        for lab, f_oi in (("unabgeschwaecht", 1.0), ("oi_0842", OI)):
            rr = {}
            for pr in PRIORS:
                g = [test[w]["lines"][line][f"prior_grid_{lab}"][str(pr)] for w in ("W1", "W2")]
                prods = [x["product_scaled_gate4"] for x in g]
                gp = 1.0
                for j in CONDS:
                    fj = f_oi if j == "P2ss" else 1.0
                    ses = [test[w]["lines"][line]["se_bind"][j] for w in ("W1", "W2")]
                    gp *= P1.dec52_gate_power([fj * pr, fj * pr], ses)["power_product"]
                gp_cons = gp * min(x["single_powers"]["null_P2ss"] for x in g) * G4
                reg = "C10" if min(prods) >= 0.80 else ("DEC52" if gp_cons >= 0.80 else "GL012")
                rr[str(pr)] = {"product_scaled_gate4_W1_W2": prods, "dec52_gate_product_z": gp,
                               "dec52_consistent_null_gate4": gp_cons, "regime_by_product": reg}
            regimes[f"{line}|{lab}"] = rr

    # DEC-103 E7 reproduction of the product line with the Teil B SEs (code check)
    tb = {"W1": {"P2ss": 7.339544738217955, "P3fix": 7.184071559406464, "P3all": 6.529579298596177},
          "W2": {"P2ss": 7.575461242752314, "P3fix": 7.185827559572715, "P3all": 6.5296181761425895}}
    e7 = {w: {"single": P1.mde80(tb[w]["P2ss"], Z),
              "product": bisect(lambda p, w=w: math.prod(cond_powers(p, 1.0, tb[w], None, Z).values()))}
          for w in tb}

    out = {"label": cc.LABEL, "rules": "R-C1..R-C17 (Docstring c_common.py)", "inputs_sha256": inputs,
           "power_p1_sha256": cc.sha256(cc.POWER_P1), "kline_meta": kmeta, "calendar_meta": cal_meta,
           "calendar_checks_pre_period": chk, "outlier_days_calendar_upto_2026-06-30": outl_all,
           "z_krit": Z, "z_power": Z80, "z_a3_practice": Z_A3, "oi_factor": OI, "priors_bp": PRIORS,
           "gate4_factor_provisional": G4, "pk_seeds": PK_SEEDS, "pk_z": Z_PK,
           "c_bind_pooled_pre_period": cser, "same_day_rho": {f"{a}|{b}": v for (a, b), v in rhos.items()},
           "class_dispersion_pre_period_pooled": disp(VP, sd_vp), "teil_B_reproduction": repro,
           "cross_file_check_teil_B": cross_file, "pre_windows": pre, "transfer": {"tail_factor_95_reg_max_V": tau95, "tail_factor_99_reg_max_V": tau99,
                                            "sigma_within_pre_pooled": math.sqrt(sig2_vp),
                                            "stress_window_binding_R_C14": stress_key,
                                            "sigma_within_stress": math.sqrt(sig2_stress)},
           "test_windows": test, "regimes": regimes, "dec103_e7_reproduction_teil_B_se": e7,
           "n_rep_null": cc.R_REP, "seed_null_base": cc.SEED_NULL, "n_mc_joint": cc.N_MC, "seed_mc_base": cc.SEED_MC}
    return out


if __name__ == "__main__":
    po = "--pre-only" in sys.argv
    res = main(pre_only=po)
    h = cc.dump(res, cc.WORK / ("c1_pre.json" if po else "c1.json"))
    print("c1_pre.json" if po else "c1.json", "sha256", h)
    print("counts", {k: v["counts"] for k, v in res["pre_windows"].items()})
