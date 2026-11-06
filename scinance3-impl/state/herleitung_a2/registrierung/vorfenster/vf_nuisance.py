"""Binding pre-window nuisance for A2 under DEC-107 BE-04 / DEC-108: window VF = 2023-07-01..2024-06-30 (12 months before
W1), zone X. Reuses the sealed Teil-C machinery (c_common / c1_nullsim, unchanged) on a combined kline grid that adds the
June-2024 extract. Outputs ONLY dispersion, counts, c, analytic SE per contrast, permutation-null SD and quantile DISTANCES
(R-C6: no mean, no median, no sign of any expiry-day return). V3 (2023-06..2024-05) is recomputed as a cross-check against
the sealed Teil-C numbers. Orchestrator run, Konto Zone X entry."""
import sys, json, hashlib
from pathlib import Path
sys.path.insert(0, "/home/user/scinance_work/a2_teilC")
import numpy as np, pyarrow.parquet as pq, pyarrow as pa
import c_common as cc
import c1_nullsim as c1

HERE = Path(__file__).resolve().parent
RAW = Path("/home/user/scinance_work/hf_data/raw")
F_OLD = RAW / "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-05-31.parquet"
F_JUN = RAW / "bybit_kline1m_BTCUSDT_ETHUSDT_2024-06-01_2024-06-30.parquet"
F_COMB = HERE / "work" / "bybit_kline1m_BTCUSDT_ETHUSDT_2021-03-24_2024-06-30.parquet"
WINDOWS = {"VF_2023-07..2024-06": ("2023-07-01", "2024-06-30"),      # binding pre-window (12 months before W1)
           "V3_2023-06..2024-05": ("2023-06-01", "2024-05-31")}      # cross-check against sealed Teil C

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# combined grid (sorted; schema of the sealed file)
t = pa.concat_tables([pq.read_table(F_OLD), pq.read_table(F_JUN)]).sort_by([("symbol", "ascending"), ("start_ms", "ascending")])
pq.write_table(t, F_COMB)
cc.F_KLINE = F_COMB
cc.LAST_RETURN_DAY = "2024-06-30"
cc.assert_kline_dates.__defaults__ = (F_COMB,)
inputs = {"kline_2021-03-24_2024-05-31": sha(F_OLD), "kline_2024-06-01_2024-06-30": sha(F_JUN), "kline_combined": sha(F_COMB),
          **cc.check_inputs([cc.F_CAL.name])}
flags, cal_meta = cc.load_calendar_flags()
days, closes, kmeta = cc.load_closes()
assert days[0].isoformat() == cc.FIRST_RETURN_DAY and days[-1].isoformat() == "2024-06-30", days[-1]
di = {d: i for i, d in enumerate(days)}
me = np.array([cc.is_month_end_friday(d) for d in days])
sr = {s: cc.slot_returns(closes[s]) for s in closes}
X = {"pre": 0.5 * (sr["BTCUSDT"]["pre"] + sr["ETHUSDT"]["pre"]),
     "fix1530": 0.5 * (sr["BTCUSDT"]["fix1530"] + sr["ETHUSDT"]["fix1530"]),
     "p3all": 0.5 * (cc.p3all_value(sr["BTCUSDT"]["profile"], me) + cc.p3all_value(sr["ETHUSDT"]["profile"], me))}
del closes, sr
slot_of = {"E": "pre", "P2ss": "pre", "P3fix": "fix1530", "P3all": "p3all"}
def vals(dl, key): return X[slot_of[key]][[di[d] for d in dl]]
def pre_sets(lo, hi):
    S = cc.window_sets(lo, hi, flags)
    S["P3all"] = [d for d in S["P3all"] if np.isfinite(X["p3all"][di[d]])]
    return S
def counts(S): return {k: len(v) for k, v in S.items()}
def commons(S):
    sE, s2, s3f, s3a = set(S["E"]), set(S["P2ss"]), set(S["P3fix"]), set(S["P3all"])
    return {("E", "P2ss"): len(sE & s2), ("E", "P3fix"): len(sE & s3f), ("E", "P3all"): len(sE & s3a),
            ("P2ss", "P3fix"): len(s2 & s3f), ("P2ss", "P3all"): len(s2 & s3a), ("P3fix", "P3all"): len(s3f & s3a)}

# pooled c and rho exactly as Teil C (pre-period to 2024-05-31) so that the V3 cross-check is like for like
VP = pre_sets(cc.FIRST_RETURN_DAY, "2024-05-31")
cser = {k: cc.c_bind(vals(VP[k], k), c1.P1) for k in ("E", "P2ss", "P3fix", "P3all")}
cs = {k: cser[k]["c_bind"] for k in cser}
fri_w = [d for d in VP["E"] if not cc.is_month_end_friday(d)]
modo = VP["P2ss"]
rhos = {("E", "P2ss"): 0.0,
        ("E", "P3fix"): c1.corr(vals(fri_w, "E"), vals(fri_w, "P3fix")),
        ("E", "P3all"): c1.corr(vals(VP["E"], "E"), vals(VP["E"], "P3all")),
        ("P2ss", "P3fix"): c1.corr(vals(modo, "P2ss"), vals(modo, "P3fix")),
        ("P2ss", "P3all"): c1.corr(vals(modo, "P2ss"), vals(modo, "P3all")),
        ("P3fix", "P3all"): c1.corr(vals(VP["P3fix"], "P3fix"), vals(VP["P3fix"], "P3all"))}
# W2 counts (sealed Teil C) for the "SE with confirmation-window counts" line
c1j = json.loads((cc.WORK / "c1.json").read_text())
N_W2 = c1j["test_windows"]["W2"]["counts"]; CM_W2 = c1j["test_windows"]["W2"]["common_days"]
CM_W2 = {tuple(k.split("|")): v for k, v in CM_W2.items()} if all("|" in k for k in CM_W2) else None

out = {"label": "A2 Vorfenster-Nuisance (DEC-107 BE-04 / DEC-108; VR-b10 (i)): nur Streuung, Zaehlung, c, SE, Null-SD, Quantil-Abstaende; kein Mittel, kein Vorzeichen (R-C6)",
       "inputs_sha256": inputs, "kline_meta": kmeta, "calendar_meta": cal_meta, "c_bind_pooled_pre_period_to_2024-05-31": cs,
       "same_day_rho": {f"{a}|{b}": v for (a, b), v in rhos.items()}, "n_rep_null": cc.R_REP, "windows": {}}
for k, (wi, (lo, hi)) in enumerate(WINDOWS.items()):
    S = pre_sets(lo, hi)
    U = sorted(S["E"] + S["P2ss"])
    pn = cc.PermNull(U, np.array([d.weekday() == 4 for d in U]))
    x = np.array([X["pre"][di[d]] for d in U])
    nb = c1.null_block(pn, x, cc.SEED_NULL + 10 + k)
    st = c1.structure(pn)
    sdw = {j: c1.sd(vals(S[j], j)) for j in ("E", "P2ss", "P3fix", "P3all")}
    cw = {j: cc.c_bind(vals(S[j], j), c1.P1)["c_bind"] for j in ("E", "P2ss", "P3fix", "P3all")}
    N, cm = counts(S), commons(S)
    se_win = c1.se_contrasts(N, cm, sdw, cs, rhos)
    se_win_cw = c1.se_contrasts(N, cm, sdw, cw, rhos)
    sdn, f3 = nb["sd_mc"], st["f_p3_over_p2"]
    blk = {"range": [lo, hi], "counts": N, "structure": st, "class_sd": sdw, "c_bind_window": cw,
           "null_P2ss": {kk: v for kk, v in nb.items() if not kk.startswith("_")},
           "se_analytic_c_pooled": {j: se_win[j]["se"] for j in c1.CONDS},
           "se_analytic_c_window": {j: se_win_cw[j]["se"] for j in c1.CONDS},
           "se_analytic_c1": {j: se_win[j]["se_c1"] for j in c1.CONDS}, "binding": {}}
    for j in c1.CONDS:
        null_sd = sdn if j == "P2ss" else f3 * sdn
        se_a = se_win[j]["se"]
        blk["binding"][j] = {"se_analytic": se_a, "null_sd": null_sd, "se_bind": max(se_a, null_sd),
                             "se_bind_source": "analytisch" if se_a >= null_sd else "Null-Simulation"}
    if CM_W2 is not None:
        se_w2 = c1.se_contrasts(N_W2, CM_W2, sdw, cs, rhos)
        blk["se_with_W2_counts"] = {j: se_w2[j]["se"] for j in c1.CONDS}
    else:
        blk["se_with_W2_counts"] = {"note": "W2 common_days key format not parsed", "keys": list(c1j["test_windows"]["W2"]["common_days"])[:6]}
    out["windows"][wi] = blk
h = cc.dump(out, HERE / "work" / "vf_nuisance.json")
print("vf_nuisance.json sha256", h)
for wi, b in out["windows"].items():
    print(wi, "counts", b["counts"])
    print("   class_sd", {j: round(v, 2) for j, v in b["class_sd"].items()}, "c_window", {j: round(v, 3) for j, v in b["c_bind_window"].items()})
    print("   se_analytic(c pooled)", {j: round(v, 2) for j, v in b["se_analytic_c_pooled"].items()}, "| c window", {j: round(v, 2) for j, v in b["se_analytic_c_window"].items()})
    print("   null_sd P2ss", round(b["null_P2ss"]["sd_mc"], 2), "d95_reg", round(b["null_P2ss"].get("d95_reg", float('nan')), 2),
          "| se_bind", {j: (round(v["se_bind"], 2), v["se_bind_source"]) for j, v in b["binding"].items()})
    print("   se_with_W2_counts", b["se_with_W2_counts"] if "note" in b["se_with_W2_counts"] else {j: round(v, 2) for j, v in b["se_with_W2_counts"].items()})
