"""Review A1 -- power / GL-012 arithmetic from own recomputed inputs (rv_formation.json, rv_nuisance.json)
plus the derivation's W1 binding SD (372.9 bp, PIT projection P2). theta=1 unless noted."""
import json, math
from scipy.stats import norm
SP = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_review"
fo, nu = json.load(open(SP + "/rv_formation.json")), json.load(open(SP + "/rv_nuisance.json"))
phi = nu["phi_ratio_of_sums"]; spr = {w: fo["A_" + w]["spread_mean_bp"] for w in ("W1", "W2")}
prem = {w: spr[w] * phi for w in spr}; prem_pool = (prem["W1"] + prem["W2"]) / 2
def run(sd, c, label):
    se = {w: sd[w] * math.sqrt(c / 52) for w in sd}
    sp = math.sqrt(se["W1"] ** 2 + se["W2"] ** 2) / 2
    P = {w: norm.cdf(prem[w] / se[w] - 1.6449) for w in se}
    print(f"{label:48s} SE {se['W1']:.1f}/{se['W2']:.1f}  P {P['W1']:.3f}/{P['W2']:.3f}  3.168*SEp {3.168*sp:.1f} vs prem {prem_pool:.1f}"
          f"  GL012={3.168*sp > prem_pool}  theta_min {3.168*sp/prem_pool:.3f}  MDE80_W1 {2.4865*se['W1']:.1f} vs {prem['W1']:.1f}")
    return se, sp
sd_der = {"W1": 372.9, "W2": nu["sd_bp"]["x"]}
print("prem W1/W2/pool", {k: round(v, 1) for k, v in prem.items()}, round(prem_pool, 1))
run(sd_der, 1.0, "derivation SDs, c=1")
run(sd_der, 1 / 0.41, "derivation SDs, c=1/0.41 (DEC-67 E4)")
run(sd_der, nu["c_stationary4_x"], "derivation SDs, c=stationary bootstrap (meas.)")
# W2 projection with the funding leg scaled by k (Bartlett long-run components from nuisance)
L = nu["lrv_bp2"]
for kname in ("k_sd", "k_mean"):
    k = nu[kname]["W2"]
    var = L["var_p"] + k * k * L["var_g"] + 2 * k * L["cov_pg"]
    lrv = L["pp"] + k * k * L["gg"] + 2 * k * L["pg"]
    c_w2 = lrv / var
    sdW2 = math.sqrt(var)
    print(f"  W2 projection {kname}={k:.2f}: SD {sdW2:.1f} bp, c_W2 {c_w2:.3f}, long-run SD {math.sqrt(lrv):.1f}")
    run({"W1": 372.9, "W2": max(sdW2, nu['sd_bp']['x'])}, max(1.0, c_w2), f"W2 funding leg scaled ({kname}), c=max(1,c_W2)")
# phi needed in W2 for GL-012 freedom at theta=1, c=1 (derivation SEs)
se1, se2 = 372.9 / math.sqrt(52), nu["sd_bp"]["x"] / math.sqrt(52)
bound = 3.168 * math.sqrt(se1 ** 2 + se2 ** 2) / 2
phi_w2 = (2 * bound - prem["W1"]) / spr["W2"]
print("phi_W2 needed (c=1):", round(phi_w2, 3), "= share of nuisance phi", round(phi_w2 / phi, 3))
