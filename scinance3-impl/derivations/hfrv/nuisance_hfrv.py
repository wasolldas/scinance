"""HF-RV nuisance (Option 3, DEC-98): dispersion and persistence of the daily premium
IV - RV_fwd30^HF on the pre-period, six RV variants -- NEVER its mean or sign.

Rules R-1..R-13 in hfrv_common.py (fixed before any number).  Statistics via the H-27 code
(nuisance.describe, copied unchanged), power / days via power_p1 (hfrv_power, solver copied from
the programme balance).  Writes scinance3-impl/state/herleitung_hfrv/nuisance_hfrv.json.

Run: python3 -I nuisance_hfrv.py      (paths are absolute; data files are read, never executed)
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/scinance/src")
import hfrv_common as hc  # noqa: E402
import hfrv_power as hp  # noqa: E402
from nuisance import acf, contiguous, describe  # noqa: E402  (H-27 code, unchanged copy)
from bybit_edge.research import power_p1 as pp  # noqa: E402

UNITS = ("S1", "S2", "S3")
ACF_OUT = (1, 10, 20, 30, 60, 120, 180)
SD_H27 = 18.597398507580287          # [fj:nuisance.BTC.S1.sd]
SD_ASSUMED_HF = 15.1                 # REVIEW_H27 B-1 (UNBELEGT)
C_CONSENSUS_REVIEW = 18.6            # REVIEW_H27 B-2 (Konsens)
PRIOR_V_LIT = 0.14
LOG_CENTRAL = 0.1431


# ----------------------------------------------------------------------------------------------
# extra statistics (copied estimator definitions from the H-27 review where stated)
# ----------------------------------------------------------------------------------------------

def acf_all(x: np.ndarray, kmax: int) -> np.ndarray:
    """review nuisance_review.acf_all (unchanged)."""
    d = x - x.mean()
    g0 = d @ d
    return np.array([1.0] + [float(d[k:] @ d[:-k] / g0) for k in range(1, kmax + 1)])


def c_consensus(x: np.ndarray) -> float:
    """Tapered ACF sum = review mc_rule_bias c_true_longrun (Tukey taper lags 60..90)."""
    K = 90
    rho = acf_all(x, K)
    taper = np.ones(K + 1)
    j = np.arange(61, K + 1)
    taper[61:] = 0.5 * (1 + np.cos(np.pi * (j - 60) / (K - 60)))
    r = rho[:K + 1] * taper
    return float(1 + 2 * r[1:].sum())


def kappa(x: np.ndarray) -> dict:
    """review noise_share: kappa_L = E[x^2] / E[x_s x_{s+L}] on the daily variance proxy (pairs
    with both values finite)."""
    out = {}
    for L in (1, 2, 3, 4, 5):
        a, b = x[L:], x[:-L]
        ok = np.isfinite(a) & np.isfinite(b)
        out[str(L)] = float(np.mean(x[np.isfinite(x)] ** 2) / np.mean(a[ok] * b[ok]))
    out["kappa_L2_3_5_review"] = float(np.mean([out["2"], out["3"], out["5"]]))
    out["kappa_L2_5"] = float(np.mean([out["2"], out["3"], out["4"], out["5"]]))
    return out


def gap_aware(x_full: np.ndarray) -> dict:
    """Report only (if the longest gap-free run is shorter than the finite sample): SD over all
    finite values and ACF from pairwise-complete products."""
    ok = np.isfinite(x_full)
    x = x_full[ok]
    d = np.where(ok, x_full - x.mean(), 0.0)
    g0 = float(np.sum(d * d)) / ok.sum()
    acfs = {}
    for k in ACF_OUT:
        m = ok[k:] & ok[:-k]
        acfs[str(k)] = float(np.sum((d[k:] * d[:-k])[m]) / m.sum() / g0)
    return {"n_finite": int(ok.sum()), "sd_all_finite": float(np.std(x, ddof=1)), "acf_pairwise": acfs}


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    ra = np.argsort(np.argsort(a[ok])).astype(float)
    rb = np.argsort(np.argsort(b[ok])).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def premium(iv: np.ndarray, rv: np.ndarray) -> dict[str, np.ndarray]:
    """Exactly the units of h27_series.premium_frame (in memory only)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return {"S1": 100.0 * (iv - rv), "S2": 100.0 * (iv * iv - rv * rv), "S3": np.log(iv / rv)}


def stat_block(x_full: np.ndarray) -> dict:
    d = describe(x_full)
    x = contiguous(x_full)
    d["acf_out"] = {str(k): acf(x, k) for k in ACF_OUT}
    d["c_consensus_tapered_acf"] = c_consensus(x)
    if d["n_contiguous_used"] < d["n_finite"]:
        d["gap_aware_report"] = gap_aware(x_full)
    return d


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ----------------------------------------------------------------------------------------------

def main() -> None:
    t0 = time.time()
    fj = json.loads(hc.H27_FJ.read_text())
    out: dict = {"label": hc.LABEL, "stand_utc": "2026-10-21",
                 "regeln": "R-1..R-13 in scratchpad/hfrv_herleitung/hfrv_common.py (vor jeder Zahl fixiert)",
                 "period_iv_days": f"{hc.NUISANCE_FIRST_IV_DAY}..{hc.NUISANCE_LAST_IV_DAY}",
                 "price_days": f"<= {hc.RV_LAST_PRICE_DAY}", "seed_bootstrap": 27,
                 "inputs_sha256": {p.name: sha(p) for p in (*hc.KLINE.values(), hc.DVOL)}}
    # --- data ------------------------------------------------------------------------------------
    kl = {s: hc.load_kline(s) for s in ("BTC", "ETH")}
    out["data_kline"] = {s: kl[s]["meta"] for s in kl}
    rvd = {s: hc.rv_day_variants(kl[s]) for s in kl}
    out["data_rv_day"] = {s: rvd[s]["diag"] for s in rvd}
    iv, iv_meta = hc.load_iv()
    out["data_dvol"] = iv_meta
    # R-13 panel cross-check (counts only)
    pc = {}
    for s in kl:
        panel = hc.panel_closes_truncated(s)
        k = kl[s]
        last = {k["days"][i]: k["closes"][i, hc.MIN_PER_DAY - 1] for i in range(len(k["days"]))
                if np.isfinite(k["closes"][i, hc.MIN_PER_DAY - 1])}
        common = sorted(set(panel) & set(last))
        rel = [abs(last[d] / panel[d] - 1.0) for d in common]
        pc[s] = {"n_common_days": len(common), "n_equal": int(sum(1 for d in common if last[d] == panel[d])),
                 "max_rel_dev": float(max(rel)) if rel else None,
                 "days_rel_dev_gt_1e-9": [d for d, r in zip(common, rel) if r > 1e-9][:20]}
    out["check_last_1min_close_vs_panel_1d"] = pc
    # --- series (in memory) ------------------------------------------------------------------------
    t_days = hc.days_range(hc.NUISANCE_FIRST_IV_DAY, hc.NUISANCE_LAST_IV_DAY)
    ivs = {s: np.array([iv[s].get(t, np.nan) for t in t_days]) for s in kl}
    rv30 = {s: {v: hc.rv_fwd30(rvd[s]["rv"][v], kl[s]["days"], t_days) for v in hc.VARIANTS} for s in kl}
    prem = {s: {v: premium(ivs[s], rv30[s][v]) for v in hc.VARIANTS} for s in kl}
    leg = {v: {u: 0.5 * (prem["BTC"][v][u] + prem["ETH"][v][u]) for u in UNITS} for v in hc.VARIANTS}
    # --- missing-day accounting --------------------------------------------------------------------
    miss = {}
    for s in kl:
        miss[s] = {v: {"n_t": len(t_days), "n_iv_missing": int(np.isnan(ivs[s]).sum()),
                       "n_rv30_missing": int(np.isnan(rv30[s][v]).sum()),
                       "n_premium_missing": int(np.isnan(prem[s][v]["S1"]).sum())} for v in hc.VARIANTS}
    out["missing"] = miss
    # --- RV level (allowed), signature, kappa, noise -----------------------------------------------
    lvl = {}
    for s in kl:
        rows = {}
        for v in hc.VARIANTS:
            r = rv30[s][v][np.isfinite(rv30[s][v])]
            rows[v] = {"rms_rv_fwd30": float(np.sqrt(np.mean(r * r))), "n": int(r.size)}
        for v in hc.VARIANTS:
            rows[v]["ratio_rms_to_cc"] = rows[v]["rms_rv_fwd30"] / rows["v6_cc"]["rms_rv_fwd30"]
            rows[v]["ratio_rms_to_30min"] = rows[v]["rms_rv_fwd30"] / rows["v5_30min"]["rms_rv_fwd30"]
            rows[v]["level_bias_volpts_vs_cc"] = 100 * (rows[v]["rms_rv_fwd30"] - rows["v6_cc"]["rms_rv_fwd30"])
        lvl[s] = rows
    out["rv_level"] = lvl
    kap = {}
    sel_lo = hc.day_idx("2021-03-25") - hc.day_idx(hc.FIRST_KLINE_DAY)
    for s in kl:
        rows = {}
        for v in hc.VARIANTS:
            x = rvd[s]["rv"][v][sel_lo:]
            k = kappa(x)
            sig = lvl[s][v]["rms_rv_fwd30"]
            k["sd_noise_volpts_delta"] = 100 * math.sqrt(max(k["kappa_L2_3_5_review"] - 1, 0) / 120.0) * sig
            k["n_days_finite"] = int(np.isfinite(x).sum())
            rows[v] = k
        kap[s] = rows
    out["kappa_rv_day"] = kap
    # --- statistics -------------------------------------------------------------------------------
    stats: dict = {}
    for s in ("BTC", "ETH"):
        stats[s] = {v: {u: stat_block(prem[s][v][u]) for u in UNITS} for v in hc.VARIANTS}
        print(f"stats {s} done ({time.time()-t0:.0f}s)", flush=True)
    stats["LEG_BTCETH"] = {v: {u: stat_block(leg[v][u]) for u in UNITS} for v in hc.VARIANTS}
    print(f"stats LEG done ({time.time()-t0:.0f}s)", flush=True)
    out["stats"] = stats
    # noise-free predictions and ratios
    ratios = {}
    for s in ("BTC", "ETH"):
        rows = {}
        for v in hc.VARIANTS:
            sd = stats[s][v]["S1"]["sd"]
            rows[v] = {"sd_S1": sd, "ratio_sd_to_cc_same_data": sd / stats[s]["v6_cc"]["S1"]["sd"],
                       "noise_sd_delta": kap[s][v]["sd_noise_volpts_delta"],
                       "sd_S1_noise_free_delta": math.sqrt(max(sd ** 2 - kap[s][v]["sd_noise_volpts_delta"] ** 2, 0)),
                       "ratio_sd_S3_to_cc": stats[s][v]["S3"]["sd"] / stats[s]["v6_cc"]["S3"]["sd"],
                       "ratio_sd_S2_to_cc": stats[s][v]["S2"]["sd"] / stats[s]["v6_cc"]["S2"]["sd"]}
            if s == "BTC":
                rows[v]["ratio_sd_to_h27_18_60"] = sd / SD_H27
        ratios[s] = rows
    out["sd_ratios"] = ratios
    # correlations
    corr = {"pearson_btc_eth": {}, "spearman_btc_eth": {}, "pearson_hf_vs_cc_same_symbol": {}}
    for v in hc.VARIANTS:
        corr["pearson_btc_eth"][v] = {u: pearson(prem["BTC"][v][u], prem["ETH"][v][u]) for u in UNITS}
        corr["spearman_btc_eth"][v] = {u: spearman(prem["BTC"][v][u], prem["ETH"][v][u]) for u in UNITS}
        corr["pearson_hf_vs_cc_same_symbol"][v] = {
            s: {u: pearson(prem[s][v][u], prem[s]["v6_cc"][u]) for u in UNITS} for s in ("BTC", "ETH")}
    out["correlations"] = corr
    # decomposition (report): P_cc = P_v + D_v with D_v = RV_v - RV_cc (vol points, RV only)
    dec = {}
    for s in ("BTC", "ETH"):
        rows = {}
        for v in hc.VARIANTS:
            if v == "v6_cc":
                continue
            Dv = 100.0 * (rv30[s][v] - rv30[s]["v6_cc"])
            pv = prem[s][v]["S1"]
            ok = np.isfinite(Dv) & np.isfinite(pv)
            sd_d = float(np.std(Dv[ok], ddof=1))
            cov = float(np.cov(pv[ok], Dv[ok], ddof=1)[0, 1])
            rows[v] = {"sd_D_volpts": sd_d, "corr_D_with_P_v_S1": cov / (sd_d * float(np.std(pv[ok], ddof=1))),
                       "corr_D_with_RV_v": pearson(Dv, rv30[s][v]),
                       "var_P_v": float(np.var(pv[ok], ddof=1)), "var_D": sd_d ** 2, "two_cov_P_v_D": 2 * cov,
                       "var_P_cc_identity": float(np.var(pv[ok], ddof=1)) + sd_d ** 2 + 2 * cov,
                       "corr_RV_v_with_RV_cc": pearson(rv30[s][v], rv30[s]["v6_cc"])}
        dec[s] = rows
    out["decomposition_P_cc_eq_P_v_plus_D"] = dec
    # --- power / window length ---------------------------------------------------------------------
    null365 = {s: {u: fj["nullwelt"][s]["windows"]["365"][u]["se_null_at_ref"] for u in UNITS} for s in ("BTC", "ETH")}
    pri = {"BTC": fj["power"]["configs"]["BTC/S1"]["priors"],
           "BTC_S3": fj["power"]["configs"]["BTC/S3"]["priors"],
           "BTC_S2": fj["power"]["configs"]["BTC/S2"]["priors"],
           "ETH": fj["power"]["configs"]["ETH/S1"]["priors"],
           "LEG": fj["power"]["configs"]["LEG_MEAN/S1"]["priors"]}
    sig_cc = fj["nuisance"]["rv_level_BTC"]["sigma_n_rms"]
    # DEC-98 Nachtrag 2 (report, direction strictness): pi-2 7.14 VP (BVIX route), Q-density 3.16 VP
    extra_priors = {"dec98n2_pi2_7_14": 7.14, "dec98n2_qdensity_3_16": 3.16}
    pw: dict = {"inputs": {"se_null_365_h27": null365, "priors_fj": pri, "extra_priors_report": extra_priors,
                           "c_consensus_review": C_CONSENSUS_REVIEW, "z_krit": hp.Z, "mde_factor": hp.ZMDE,
                           "a3_threshold": pp.Z_PER_WINDOW_A3_PRACTICE, "start": hp.START_VRP.isoformat()},
                "BTC_S1": {}, "report": {}}
    for v in hc.VARIANTS:
        st = stats["BTC"][v]["S1"]
        sd = st["sd"]
        cs = {"c_rule_P3": st["c_bind"], "c_consensus_measured": max(1.0, st["c_consensus_tapered_acf"]),
              "c_consensus_review_18_6": C_CONSENSUS_REVIEW}
        row = {"sd": sd, "c": cs}
        for cname, c in cs.items():
            for null_name, na in (("se_null_h27", (null365["BTC"]["S1"], 365)), ("nuisance_only", None)):
                key = f"{cname}|{null_name}"
                blk = {"windows_L12": {pn: hp.window_rows(pv, sd, c, na) for pn, pv in pri["BTC"].items()}}
                blk["durations"] = {pn: hp.duration_block(pv, sd, c, na) for pn, pv in
                                    {**pri["BTC"], **extra_priors}.items()}
                # pi-2 evaluated at the variant's own RV level (report; level bias needs own J)
                sig_v = lvl["BTC"][v]["rms_rv_fwd30"]
                p_lvl = 100 * sig_v * (math.exp(LOG_CENTRAL) - 1)
                blk["durations"]["pi2_central_at_variant_level"] = hp.duration_block(p_lvl, sd, c, na)
                # counter-reading (strictness): literature RV close-to-close-like, the variant's level
                # bias b = rms(RV_v)/rms(RV_cc) lowers the expected premium: sigma_cc (e^l - b)
                b_lvl = lvl["BTC"][v]["ratio_rms_to_cc"]
                p_cc_lvl = 100 * sig_cc * (math.exp(LOG_CENTRAL) - b_lvl)
                blk["durations"]["pi2_central_cc_literature_level_bias"] = (
                    hp.duration_block(p_cc_lvl, sd, c, na) if p_cc_lvl > 0 else {"prior": p_cc_lvl, "days": None})
                row[key] = blk
        pw["BTC_S1"][v] = row
        print(f"power {v} done ({time.time()-t0:.0f}s)", flush=True)
    # report: S3/S2 BTC, ETH S1, LEG S1, conjunction (c rule, SE_null H-27, central prior)
    for v in hc.VARIANTS:
        rep = {}
        for lab, (stt, prk, na) in {
                "BTC_S3": (stats["BTC"][v]["S3"], "BTC_S3", (null365["BTC"]["S3"], 365)),
                "BTC_S2": (stats["BTC"][v]["S2"], "BTC_S2", (null365["BTC"]["S2"], 365)),
                "ETH_S1": (stats["ETH"][v]["S1"], "ETH", (null365["ETH"]["S1"], 365)),
                "LEG_S1": (stats["LEG_BTCETH"][v]["S1"], "LEG", (null365["BTC"]["S1"], 365))}.items():
            rep[lab] = {
                "c_rule": hp.duration_block(pri[prk]["pi2_central"], stt["sd"], stt["c_bind"], na),
                "c_consensus_measured": hp.duration_block(pri[prk]["pi2_central"], stt["sd"],
                                                          max(1.0, stt["c_consensus_tapered_acf"]), na)}
        for cn in ("c_rule", "c_consensus_measured"):
            b = pw["BTC_S1"][v][("c_rule_P3" if cn == "c_rule" else "c_consensus_measured") + "|se_null_h27"]
            nb = b["durations"]["pi2_central"]["days"]["c10_p1"]
            ne = rep["ETH_S1"][cn]["days"]["c10_p1"]
            rep[f"conjunction_BTC_and_ETH_{cn}"] = {
                "c10_p1_days": None if (nb is None or ne is None) else max(nb, ne),
                "full_c10_p1": hp.daily_full(hp.START_VRP, None if (nb is None or ne is None) else max(nb, ne))}
        pw["report"][v] = rep
    # selection ceiling (DEC-94 (7)): C10 days per window with z = max(z_krit, z_max(K)) (closed form,
    # n = c ((z + 0.8416) SD / prior)^2 -- equals the bisection for C10, see solver_check), report only
    selk = {}
    for v in ("v3_5min_sub", "v6_cc"):
        st = stats["BTC"][v]["S1"]
        for cname, c in (("c_rule_P3", st["c_bind"]), ("c_consensus_measured", max(1.0, st["c_consensus_tapered_acf"]))):
            for pn, pv in (("pi2_central", pri["BTC"]["pi2_central"]), ("dec98n2_pi2_7_14", extra_priors["dec98n2_pi2_7_14"])):
                rows = {}
                for K in (1, 6, 12, 18, 54):
                    ze = pp.effective_z(pp.ALPHA_WINDOW, K)
                    n = c * ((ze + pp.Z_POWER) * st["sd"] / pv) ** 2
                    rows[str(K)] = {"z_eff": ze, "c10_days": n, "full_c10": hp.daily_full(hp.START_VRP, n)}
                selk[f"{v}|{cname}|{pn}"] = rows
    pw["selection_K_report"] = selk
    out["power"] = pw
    # --- reproduction check of the H-27 reference with the H-27 numbers (solver sanity) -----------
    out["solver_check_h27_reference"] = hp.duration_block(pri["BTC"]["pi2_central"], SD_H27,
                                                          fj["nuisance"]["BTC"]["S1"]["c_bind"],
                                                          (null365["BTC"]["S1"], 365))
    # --- R-10 recommendation, R-9 verdict ----------------------------------------------------------
    order = ("v3_5min_sub", "v2_5min", "v4_15min", "v5_30min")
    qual = {}
    for v in order:
        ratios_v = {s: lvl[s][v]["ratio_rms_to_30min"] for s in ("BTC", "ETH")}
        qual[v] = {"signature_ratio_to_30min": ratios_v,
                   "qualifies": all(0.95 <= r <= 1.05 for r in ratios_v.values())}
    rec = next((v for v in order if qual[v]["qualifies"]), "v5_30min")
    sd_rec = stats["BTC"][rec]["S1"]["sd"]
    verdict = ("bestaetigt" if 14.1 <= sd_rec <= 16.1 else
               "nicht bestaetigt (guenstiger)" if sd_rec < 14.1 else "nicht bestaetigt (unguenstiger)")
    out["recommendation_R10"] = {"order": list(order), "qualification": qual, "recommended": rec,
                                 "sd_btc_s1_recommended": sd_rec, "sd_assumed_review": SD_ASSUMED_HF,
                                 "verdict_R9": verdict,
                                 "sd_btc_s1_rec_minus_15_1": sd_rec - SD_ASSUMED_HF}
    out["skripte_sha256"] = {p.name: sha(p) for p in sorted(HERE.glob("*.py"))}
    hc.check_out(out)
    hc.OUT_DIR.mkdir(parents=True, exist_ok=True)
    (hc.OUT_DIR / "nuisance_hfrv.json").write_text(json.dumps(out, indent=1, sort_keys=False))
    print("WROTE nuisance_hfrv.json", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
