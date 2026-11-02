import json, math, sys
from statistics import NormalDist
N = NormalDist()
Phi, Pinv = N.cdf, N.inv_cdf
Z = 2.4865
PRIOR = 0.03
path = sys.argv[1]
d = json.load(open(path))
rows = []
pool = {}
for W in ("W1", "W2"):
    w = d["windows"][W]
    nf = w["noise_floor_and_threshold"]
    floor = nf["floor"]["e_floor"]; wj = nf["w_judged"]
    icmin = nf["ic_min_capped_per_variant"]
    fz = w["frozen_null_constants"]
    hr = w["beta_control_recommended_high_rep"]
    for v in ("mom1", "rev_gap", "mom2", "mom4"):
        q = fz["res_quantile_binding"][v]
        # binding drift variant for sd (DEC-88): the one whose quantile equals the binding one
        sdq = None
        for cell in ("stress", "stress_drifting"):
            vv = hr[cell]["variants"][v]
            if abs(vv["quantile_one_sided"] - q) < 1e-12:
                sdq = vv["mean_ic_draws_sd"]; bindcell = cell
        thr_b = max(icmin[v], abs(q))
        p_beta = Phi((PRIOR - thr_b) / sdq)
        mde_beta = thr_b + 0.8416 * sdq
        # DEC-88 floor-based raw condition
        p_icmin_dec88 = Phi(PRIOR * Z / icmin[v] - Z)
        mde_dec88 = max(1.3385 * icmin[v], mde_beta)
        for cal in ("measured", "stress"):
            none = w["beta_control_method_study"]["calibrations"][cal]["methods"]["none"]["variants"][v]
            fsd = none["factor_sd"]; sdmean = none["mean_ic_draws_sd"]; nullmean = none["mean_ic_draws_mean"]
            sign = 1 if none["direction"] == "positive" else -1
            disp = max(floor, fsd)
            se = disp / math.sqrt(wj)
            p_mag = Phi(PRIOR / se - Z)
            mde_mag = (Z + 0.8416) * se
            # IC_min condition with the true sampling SD of the mean
            p_icmin = Phi((PRIOR - icmin[v]) / sdmean)
            mde_icmin = icmin[v] + 0.8416 * sdmean
            # sensitivity: mechanical null mean in hypothesis direction added to prior
            shift = sign * nullmean
            p_mag_shift = Phi((PRIOR + shift) / se - Z)
            p_voll = min(p_mag, p_icmin, p_beta)
            mde = max(mde_mag, mde_icmin, mde_beta)
            rows.append((v, W, cal, floor, fsd, sdmean, se, p_mag, mde_mag, p_icmin, p_beta, mde_beta, p_voll, mde, shift, p_mag_shift, p_icmin_dec88, mde_dec88, bindcell))
            pool.setdefault((v, cal), []).append((fsd, wj, sdmean))
print("v W cal floor factor_sd sd_mean SE P_mag MDE_mag P_ICmin P_beta MDE_beta P_voll MDE80 nullshift P_mag+shift | DEC88 P_ICmin MDE80 | beta-cell")
for r in rows:
    print("%-7s %s %-8s %.5f %.4f %.5f %.5f %.3f %.4f %.3f %.3f %.4f %.3f %.4f %+.4f %.3f | %.3f %.4f | %s" % r)
print()
print("C.10 joint power (product W1*W2 of P_voll, upper bound) and DEC-52 pooled raw test (alpha 0.01 one-sided, z 2.3263):")
for (v, cal), lst in sorted(pool.items()):
    (s1, w1, m1), (s2, w2, m2) = lst
    pv = [r[12] for r in rows if r[0] == v and r[2] == cal]
    var_pool = (w1 * s1 ** 2 + w2 * s2 ** 2) / (w1 + w2) ** 2
    se_pool = math.sqrt(var_pool)
    p_pool = Phi(PRIOR / se_pool - 2.3263)
    mde_pool = (2.3263 + 0.8416) * se_pool
    print("%-7s %-8s joint_C10<=%.3f  pooled SE %.5f  P_pool(0.03) %.3f  MDE80_pool %.4f" % (v, cal, pv[0] * pv[1], se_pool, p_pool, mde_pool))
