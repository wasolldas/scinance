"""Review A1 -- NUISANCE 2021-03-01..2024-06-30 (holding weeks END <= 2024-06-30), K >= 117.
LABEL: nur Streuungs-/Kovarianz-Groessen und Verhaeltnisse; kein Mittelwert einer Rendite
(gesamt, Preisbein, Funding-Bein) wird ausgegeben oder gespeichert. Series live only in memory."""
import sys, pickle, json
from datetime import date, timedelta
import numpy as np

SP = "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_review"
d = pickle.load(open(SP + "/cache/rv_data.pkl", "rb"))
weeks, key, alive = d["weeks"], d["key"], d["alive"]
R = np.where(d["returns_valid"], np.expm1(d["returns"]), np.nan)
F = d["fsum"]
def end(w): return (date.fromisoformat(w) + timedelta(days=6)).isoformat()
p, g, s, ninv = [], [], [], 0
for t in range(len(weeks) - 1):
    if weeks[t] < "2021-03-01" or end(weeks[t + 1]) > "2024-06-30":
        continue
    assert end(weeks[t + 1]) <= "2024-06-30", "OUTCOME BLINDNESS"
    m = alive[t] & alive[t + 1]
    if m.sum() < 117:
        continue
    u = np.flatnonzero(m); k = u.size // 10
    dd = u[np.argsort(key[t, u], kind="stable")[:k]]
    ninv += int(np.isnan(R[t + 1, dd]).sum() + np.isnan(R[t + 1, u]).sum())
    # invalid return -> 0 (as the derivation) for comparability; count reported
    Rd, Ru = np.nan_to_num(R[t + 1, dd]), np.nan_to_num(R[t + 1, u])
    p.append(Rd.mean() - Ru.mean())
    g.append(F[t + 1, u].mean() - F[t + 1, dd].mean())
    s.append(key[t, u].mean() - key[t, dd].mean())
p, g, s = map(np.array, (p, g, s)); x = p + g; T = x.size
def ac(z, k):
    zc = z - z.mean(); return float(np.sum(zc[:-k] * zc[k:]) / np.sum(zc * zc))
def xc(a, b, k):  # sample cross-autocovariance cov(a_t, b_{t+k}), k may be negative
    ac_, bc = a - a.mean(), b - b.mean(); n = a.size
    return float(np.sum(ac_[:n - k] * bc[k:]) / n) if k >= 0 else float(np.sum(ac_[-k:] * bc[:n + k]) / n)
def lrv(a, b, L=4):  # Bartlett long-run covariance
    return sum((1 - abs(k) / (L + 1)) * xc(a, b, k) for k in range(-L, L + 1))
def boot_ratio(z, kind, reps=4000, blk=4, seed=7):
    rng = np.random.default_rng(seed); zc = z - z.mean(); n = z.size; out = np.empty(reps)
    for r in range(reps):
        if kind == "mbb":
            st = rng.integers(0, n - blk + 1, size=int(np.ceil(n / blk)))
            sm = np.concatenate([zc[a:a + blk] for a in st])[:n]
        else:  # stationary bootstrap (Politis-Romano), mean block blk, circular
            idx = np.empty(n, int); i = rng.integers(n)
            for j in range(n):
                idx[j] = i
                i = rng.integers(n) if rng.random() < 1.0 / blk else (i + 1) % n
            sm = zc[idx]
        out[r] = sm.mean()
    return float(out.var(ddof=1) * n / z.var(ddof=1))
res = {"label": "Nuisance 2021-03..2024-06, nur Streuung/Kovarianz/Verhaeltnis; kein Rendite-Mittel",
       "T": T, "invalid_return_cells": ninv,
       "sd_bp": {"x": x.std(ddof=1) * 1e4, "p": p.std(ddof=1) * 1e4, "g": g.std(ddof=1) * 1e4, "s": s.std(ddof=1) * 1e4},
       "rho_x": [ac(x, k) for k in (1, 2, 3, 4)], "rho_p": [ac(p, k) for k in (1, 2, 3, 4)],
       "rho_g": [ac(g, k) for k in (1, 2, 3, 4)], "corr_pg": float(np.corrcoef(p, g)[0, 1]),
       "c_bartlett_x": lrv(x, x) / (x.var(ddof=0)),
       "c_mbb4_x": boot_ratio(x, "mbb"), "c_stationary4_x": boot_ratio(x, "sb"),
       "c_stationary8_x": boot_ratio(x, "sb", blk=8),
       "phi_ratio_of_sums": float(g.sum() / s.sum()),
       "g_on_s_R2": float(np.corrcoef(g, s)[0, 1] ** 2)}
# Bartlett long-run components (variance units), used for the window projection
res["lrv_bp2"] = {"pp": lrv(p, p) * 1e8, "gg": lrv(g, g) * 1e8, "pg": lrv(p, g) * 1e8,
                  "var_p": p.var(ddof=0) * 1e8, "var_g": g.var(ddof=0) * 1e8, "cov_pg": float(np.cov(p, g, ddof=0)[0, 1]) * 1e8}
# rho_1(x) uncertainty: stationary-bootstrap SE of rho_1 (block 4)
rng = np.random.default_rng(11); rr = []
for r in range(2000):
    idx = np.empty(T, int); i = rng.integers(T)
    for j in range(T):
        idx[j] = i; i = rng.integers(T) if rng.random() < 0.25 else (i + 1) % T
    rr.append(ac(x[idx], 1))
res["rho1_x_boot_sd"] = float(np.std(rr, ddof=1))
# scale factors spread SD window / nuisance, and spread MEAN window / nuisance (ratio only; no level printed)
fj = json.load(open(SP + "/rv_formation.json"))
res["k_sd"] = {w: fj["A_" + w]["spread_sd_bp"] / (s.std(ddof=1) * 1e4) for w in ("W1", "W2")}
res["k_mean"] = {w: fj["A_" + w]["spread_mean_bp"] / (s.mean() * 1e4) for w in ("W1", "W2")}
json.dump(res, open(SP + "/rv_nuisance.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
