"""H-32 review: independent recomputation of the derivation's power numbers.
Inputs: v5e prelaunch JSON (open nuisance file; sealed file never opened), WP-7 CSV columns
'week' and 'n_symbols' only (K metadata). No real IC, no panel, no outcome."""
import csv, json, math, os, sys, hashlib
from statistics import NormalDist
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as P
N = NormalDist()
R = "/home/user/scinance/scinance3-impl/state/runs/"
V5E = R + "wp13a_20261012_v5e/wp13a_prelaunch.json"
KCSV = R + "wp7_20260921/decile_degeneration_weekly.csv"
for p in (V5E, KCSV):
    b = os.path.basename(p)
    assert not (b.endswith("_L_window_sealed.json") or b.endswith("weekly_ic_series.csv") or "UNION_REAL" in b)
raw = open(V5E, "rb").read(); assert hashlib.sha256(raw).hexdigest().startswith("94d65559")
d = json.loads(raw)
# K metadata: read only two columns via csv module, keep only those
K = {}
with open(KCSV) as f:
    for row in csv.reader(f):
        if row[0] == "week": continue
        K[row[0]] = int(row[1])
VAR = ("mom1", "mom2", "mom4", "rev_gap"); S = {"mom1": 1, "mom2": 1, "mom4": 1, "rev_gap": -1}
Z = P.z_krit(0.05); MF = P.mde_factor(0.05); ZP = P.Z_POWER
out = {}
win = {}
for W in ("W1", "W2"):
    w = d["windows"][W]; fl = w["noise_floor_and_threshold"]["floor"]
    ks, wks = fl["k_series"], fl["weeks"]
    mism = sum(1 for a, b in zip(wks, ks) if K.get(a) != b)
    win[W] = dict(wj=fl["w_judged"], V=sum(1/(k-1) for k in ks)/len(ks), E=fl["e_floor"], kmin=min(ks),
                  kmed=sorted(ks)[len(ks)//2], kmax=max(ks), first=wks[0], last=wks[-1], mism=mism, n=len(wks))
    st = w["beta_control_method_study"]
    hr = w["beta_control_recommended_high_rep"]
    win[W]["n_sim_weeks"] = {v: st["calibrations"]["stress"]["methods"]["fm_neutral_8w"]["variants"][v]["n_ic_pooled"] / st["n_reps"] for v in VAR}
    win[W]["hr"] = {cal: {v: {k: hr[cal]["variants"][v][k] for k in ("factor_sd", "mean_ic_draws_sd", "mean_ic_draws_mean", "quantile_one_sided")} for v in VAR} for cal in ("measured", "stress", "stress_drifting")}
    win[W]["hr_nweeks"] = hr["stress"]["n_weeks"]
print({W: {k: win[W][k] for k in ("wj", "V", "E", "kmin", "kmed", "kmax", "first", "last", "mism", "n", "hr_nweeks")} for W in win})
print("n_sim_weeks", {W: win[W]["n_sim_weeks"] for W in win})
# per variant nuisance
nu = {}
for v in VAR:
    nu[v] = {}
    for W in ("W1", "W2"):
        f, dr = win[W]["hr"]["stress"][v], win[W]["hr"]["stress_drifting"][v]
        sd = max(f["factor_sd"], dr["factor_sd"]); dsd = max(f["mean_ic_draws_sd"], dr["mean_ic_draws_sd"])
        m = max(S[v]*f["mean_ic_draws_mean"], S[v]*dr["mean_ic_draws_mean"])
        nsw = win[W]["n_sim_weeks"][v]
        wj = win[W]["wj"]; wje = 50 if W == "W2" else wj
        csim = nsw * dsd**2 / sd**2; cbil = wj * dsd**2 / sd**2
        S1 = dsd * math.sqrt(wj / wje)
        S2 = math.sqrt(max(1, csim)) * sd / math.sqrt(wje)
        S3 = sd / math.sqrt(wje)
        nu[v][W] = dict(sd=sd, dsd=dsd, m=m, nsw=nsw, csim=csim, cbil=cbil, S1=S1, S2=S2, S3=S3, wje=wje,
                        F2=sd**2 - win[W]["V"], credit=max(0, m))
for v in VAR:
    for W in ("W1", "W2"):
        x = nu[v][W]
        print(f"{v:7s} {W} sd {x['sd']:.4f} dsd {x['dsd']:.5f} m {x['m']:+.5f} nsw {x['nsw']:.1f} c_sim {x['csim']:.3f} c_bil {x['cbil']:.3f} "
              f"MDE80 S1 {P.mde80(x['S1'], Z)+x['credit']:.4f} S2 {P.mde80(x['S2'], Z)+x['credit']:.4f} S3 {P.mde80(x['S3'], Z)+x['credit']:.4f} (S3 no credit {P.mde80(x['S3'], Z):.4f}) F2 {x['F2']:.5f}")
# spec 0.0176
print("spec MDE80 W1 mom1 c=1 no credit:", MF * 0.0511 / math.sqrt(52))
# pilot K series
wk = sorted(K)
f117 = next(a for a in wk if K[a] >= 117); f134 = next(a for a in wk if K[a] >= 134)
print("first K>=117", f117, K[f117], "first K>=134", f134, K[f134], "2022-04-04", K.get("2022-04-04"), "2022-04-11", K.get("2022-04-11"))
print("any K<117 after f117:", [a for a in wk if a >= f117 and K[a] < 117][:3])
def pil(first, last="2024-06-17"):
    ks = [K[a] for a in wk if first <= a <= last]
    return dict(n=len(ks), kmin=min(ks), kmed=sorted(ks)[len(ks)//2], kmax=max(ks), V=sum(1/(k-1) for k in ks)/len(ks),
                E=sum(1/math.sqrt(k-1) for k in ks)/len(ks))
PM = pil(f117); print("pilot main", PM, "last weeks", [a for a in wk if "2024-06-01" <= a <= "2024-07-08"])
print("week after 2024-06-17 in csv:", [a for a in wk if a > "2024-06-17"][:2])
for v in VAR:
    F2 = max(nu[v][W]["F2"] for W in ("W1", "W2")); c = max(max(1, nu[v][W]["csim"]) for W in ("W1", "W2"))
    sdp = math.sqrt(PM["V"] + F2); sep = math.sqrt(c) * sdp / math.sqrt(PM["n"])
    nu[v]["P"] = dict(F2=F2, c=c, sdp=sdp, sep=max(sep, PM["E"]/math.sqrt(PM["n"])), floor=PM["E"]/math.sqrt(PM["n"]))
    print(f"pilot {v:7s} SD_P {sdp:.4f} SE_P {nu[v]['P']['sep']:.5f} (floor-SE {nu[v]['P']['floor']:.5f}) F2 {F2:.5f} c {c:.3f}")
json.dump({"win": {W: {k: v for k, v in win[W].items() if k != "hr"} for W in win}, "nu": nu, "PM": PM}, open("rv_nuis.json", "w"), indent=1)
