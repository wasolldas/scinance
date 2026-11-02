"""Gate audit H-32 registration: recompute the v6 core numbers from the v6 artefact only (no panel, no outcome).

Reads: v6 JSON, K series CSVs, p replicates (null draws), template YAML.  Uses power_p1 and handover from the repo.
Writes rr_check.json next to this script.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path("/home/user/scinance")
sys.path.insert(0, str(REPO / "src"))
from bybit_edge.research import power_p1  # noqa: E402
from bybit_edge.research.h32_fm8 import artifacts, handover, estimators as est, constants as C  # noqa: E402

RUN = REPO / "scinance3-impl/state/runs/h32_20261021_v6"
TPL = REPO / "scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"
OUT = Path(__file__).with_name("rr_check.json")
VARS = ("mom1", "mom2", "mom4", "rev_gap")
WINS = ("W1", "W2")
N = power_p1._N
Z = power_p1.z_krit(0.05)
ZP = power_p1.Z_POWER


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


res: dict = {"files": {}, "consistency": {}, "recompute": {}, "power": {}, "oc": {}, "endpower": {}}
for p in (RUN / "h32_prelaunch.json", RUN / "h32_prelaunch_p_replicates.json", RUN / "h32_prelaunch.md", TPL,
          RUN / "h32_prelaunch_P_k_fm8.csv", RUN / "h32_prelaunch_W1_k_fm8.csv", RUN / "h32_prelaunch_W2_k_fm8.csv"):
    res["files"][p.name] = sha(p)

js = json.loads((RUN / "h32_prelaunch.json").read_text())
reg = yaml.safe_load(TPL.read_text())
prep = json.loads((RUN / "h32_prelaunch_p_replicates.json").read_text())

# ---------------------------------------------------------------- result_sha256 (canonical, without code)
core = {k: v for k, v in js.items() if k not in ("code", "result_sha256")}
res["consistency"]["result_sha256_recomputed"] = artifacts.canonical_sha256(core)
res["consistency"]["result_sha256_artifact"] = js["result_sha256"]
res["consistency"]["code_sha256_artifact"] = js["code"]["code_sha256"]
res["consistency"]["code_sha256_head"] = artifacts.code_fingerprint()["code_sha256"]
res["consistency"]["p_file_sha_in_json"] = js["p_replicates"]["file_sha256"]
res["consistency"]["p_file_sha_in_yaml"] = reg["fdr"]["replicates_sha256"]

# ---------------------------------------------------------------- YAML frozen == JSON frozen (bitwise)
mism = []
for wn in WINS:
    fj = js["windows"][wn]["frozen_v6"]
    fy = reg["windows"][wn]["frozen_v6"]
    for k, v in fy.items():
        if isinstance(v, dict):
            for vv, x in v.items():
                if float(x) != float(fj[k][vv]):
                    mism.append(f"{wn}.{k}.{vv}")
        elif k == "k_fm8_series_sha256":
            if v != fj[k]:
                mism.append(f"{wn}.{k}")
        elif float(v) != float(fj[k]):
            mism.append(f"{wn}.{k}")
    for name, blk in reg["windows"][wn]["calibration"].items():
        for k, x in blk.items():
            if float(x) != float(js["windows"][wn]["calibration_report"]["calibration"][name][k]):
                mism.append(f"{wn}.calibration.{name}.{k}")
    for k, x in reg["windows"][wn]["null_scales"].items():
        if float(x) != float(js["windows"][wn]["calibration_report"]["null_scales"][k]):
            mism.append(f"{wn}.null_scales.{k}")
    if float(reg["windows"][wn]["bounce_sigma_true"]) != float(js["windows"][wn]["bounce_sigma_true"]):
        mism.append(f"{wn}.bounce")
for v in VARS:
    if float(reg["pilot_window"]["frozen_v6"]["m_P"][v]) != float(js["windows"]["P"]["m_P"][v]):
        mism.append(f"P.m_P.{v}")
if reg["pilot_window"]["frozen_v6"]["k_fm8_series_sha256"] != js["windows"]["P"]["k_fm8_series_sha256"]:
    mism.append("P.k_sha")
res["consistency"]["yaml_vs_json_mismatches"] = mism
res["consistency"]["yaml_fingerprints"] = reg["data_fingerprints"]
res["consistency"]["json_fingerprints"] = {k: v for k, v in js["data_fingerprints"].items() if k != "union_range_detail"}

# ---------------------------------------------------------------- K series, floor, v
for wn in ("P", "W1", "W2"):
    w = js["windows"][wn]
    k = np.asarray(w["k_fm8_series"], dtype=np.float64)
    csv = np.loadtxt(RUN / f"h32_prelaunch_{wn}_k_fm8.csv", delimiter=",", skiprows=1)[:, 1]
    sha_k = hashlib.sha256(np.ascontiguousarray(k.astype("<i8")).tobytes()).hexdigest()
    floor = float(np.mean(1 / np.sqrt(k - 1)))
    vv = float(np.mean(1 / (k - 1)))
    res["recompute"][f"{wn}_k"] = {"n": int(k.size), "csv_equal": bool(np.array_equal(csv, k)), "sha_ok": sha_k == w["k_fm8_series_sha256"],
                                   "floor": floor, "floor_art": w["floor_fm8"], "v": vv, "v_art": w["v_fm8"],
                                   "kfm8_min_med_max": [int(k.min()), float(np.median(k)), int(k.max())],
                                   "k_alive_min_med_max_art": [w["k"]["min"], w["k"]["median"], w["k"]["max"]],
                                   "geometry": w["geometry"]}

# ---------------------------------------------------------------- frozen = max over cells; binding cells; draws
for wn in ("W1", "W2"):
    cells = js["windows"][wn]["null"]["cells"]
    fz = js["windows"][wn]["frozen_v6"]
    rows = {}
    for v in VARS:
        a, b = cells["driftfree"]["variants"][v], cells["drifting"]["variants"][v]
        row = {}
        for key in ("se_mean", "e_se_rule", "sd_week", "null_mean", "q95"):
            mx = max(a[key], b[key])
            row[key] = {"recomputed_max_cells": mx, "frozen": fz[key][v], "equal": mx == fz[key][v],
                        "cell": "driftfree" if a[key] >= b[key] else "drifting"}
        d = np.asarray(prep["windows"][wn]["variants"][v], dtype=np.float64)
        cell = prep["windows"][wn]["cell"][v]
        first = d[:1000]
        cc = cells[cell]["variants"][v]
        row["binding_cell"] = cell
        row["binding_cell_expected"] = "drifting" if b["null_mean"] > a["null_mean"] else "driftfree"
        row["first1000"] = {"mean": float(first.mean()), "sd": float(first.std(ddof=1)), "q95": float(np.quantile(first, 0.95)),
                            "cell_mean": cc["null_mean"], "cell_se_mean": cc["se_mean"], "cell_q95": cc["q95"],
                            "draws_sha_cell": cc["draws_sha256"], "draws_sha_recomputed": est.series_sha256(first)}
        row["all10000"] = {"n": int(d.size), "n_nan": int(np.isnan(d).sum()), "mean": float(np.nanmean(d)), "sd": float(np.nanstd(d, ddof=1)),
                           "q95": float(np.nanquantile(d, 0.95))}
        rows[v] = row
    # ceiling (driftfree cell) only reported; check frozen == driftfree cell
    res["recompute"][f"{wn}_cells"] = rows
    res["recompute"][f"{wn}_ceiling"] = {"frozen": fz["ceiling_k4"], "driftfree_cell": cells["driftfree"]["ceiling_k4"],
                                        "drifting_cell": cells["drifting"]["ceiling_k4"]}
# m_P
cp = js["windows"]["P"]["null"]["cells"]
res["recompute"]["m_P"] = {v: {"driftfree": cp["driftfree"]["variants"][v]["null_mean"], "drifting": cp["drifting"]["variants"][v]["null_mean"],
                               "max": max(cp["driftfree"]["variants"][v]["null_mean"], cp["drifting"]["variants"][v]["null_mean"]),
                               "frozen": js["windows"]["P"]["m_P"][v],
                               "se_mean_P_max": max(cp["driftfree"]["variants"][v]["se_mean"], cp["drifting"]["variants"][v]["se_mean"]),
                               "sd_week_P_max": max(cp["driftfree"]["variants"][v]["sd_week"], cp["drifting"]["variants"][v]["sd_week"])}
                         for v in VARS}

# ---------------------------------------------------------------- thresholds, ceiling ratio, power line
thr = {}
for wn in WINS:
    fz = reg["windows"][wn]["frozen_v6"]
    for v in VARS:
        t = Z * fz["e_se_rule"][v] + max(0.0, fz["null_mean"][v])
        thr[(wn, v)] = t
        res["power"][f"T_{wn}_{v}"] = {"T": t, "ceiling_over_T": fz["ceiling_k4"] / t, "q95": fz["q95"][v],
                                      "gate_threshold_expected": max(t, fz["q95"][v]),
                                      "q95_minus_T": fz["q95"][v] - t}
rows = {}
for v in VARS:
    hc = handover.handover_constants(reg, v)
    mde = {}
    mde_1c = {}
    for wn in WINS:
        fz = reg["windows"][wn]["frozen_v6"]
        mde[wn] = power_p1.mde80(fz["e_se_rule"][v], Z, sd=fz["se_mean"][v])
        mde_1c[wn] = fz["q95"][v] + ZP * fz["se_mean"][v]          # condition (1c) alone, no credit
    m_star = max(0.0, reg["pilot_window"]["frozen_v6"]["m_P"][v], *(reg["windows"][w]["frozen_v6"]["null_mean"][v] for w in WINS))
    mstar_ = max(mde.values())
    c_v = mstar_ + m_star
    # pure rule U on a synthetic pilot payload exactly at the boundary (SE_W,Pilot not binding: F2 = 0, c = 1)
    se_p = res["recompute"]["m_P"][v]["se_mean_P_max"]
    hv = handover.evaluate_handover({"x_p": c_v, "se_p": se_p, "f2_real": 0.0, "c_real": 1.0}, hc)
    hv_lo = handover.evaluate_handover({"x_p": c_v - 1e-9, "se_p": se_p, "f2_real": 0.0, "c_real": 1.0}, hc)
    # A3 practice MDE80 W1 (no credit) and on x_P (with credit)
    fz1 = reg["windows"]["W1"]["frozen_v6"]
    a3_w1 = 2.4865 * fz1["e_se_rule"][v] + ZP * fz1["se_mean"][v]
    rows[v] = {"MDE80_W1": mde["W1"], "MDE80_W2": mde["W2"], "MDE80_star": mstar_, "m_star": m_star, "threshold_on_xP": c_v,
               "MDE80_1c_W1": mde_1c["W1"], "MDE80_1c_W2": mde_1c["W2"],
               "MDE80_1b_plus_credit_W1": mde["W1"] + max(0.0, fz1["null_mean"][v]),
               "MDE80_1b_plus_credit_W2": mde["W2"] + max(0.0, reg["windows"]["W2"]["frozen_v6"]["null_mean"][v]),
               "rule_U_at_threshold": {"handed": hv["handed_over"], "conds": hv["conditions"], "regime": hv["regime_p1"]["regime"],
                                       "window_power": hv["regime_p1"]["window_power"], "regime_a3": hv["regime_a3_practice"]["regime"],
                                       "label_only_dec94": hv["label_only_dec94"], "mu_sel": hv["mu_sel"],
                                       "power_at_mu_sel": None if hv["power_at_mu_sel"] is None else hv["power_at_mu_sel"]["window_power"],
                                       "mde80_star_code": hv["mde80_star"], "threshold_code": hv["threshold_on_point"],
                                       "t_p": hv["t_p"]},
               "rule_U_just_below": hv_lo["handed_over"],
               "A3_MDE80_W1_no_credit": a3_w1, "A3_MDE80_W1_on_xP": a3_w1 + max(0.0, fz1["null_mean"][v])}
res["power"]["rows"] = rows

# ---------------------------------------------------------------- end power at the threshold (draft method vs. replicate quantile)
def H(m: int) -> float:
    return sum(1.0 / i for i in range(1, m + 1))


ep = {}
for v in VARS:
    c_v = rows[v]["threshold_on_xP"]
    e_draft, e_full = {}, {}
    for m in (1, 2, 3, 4, 11):
        a = 0.10 / (m * H(m))
        z_eff = max(Z, N.inv_cdf(1 - a))
        pd, pf = 1.0, 1.0
        detail = {}
        for wn in WINS:
            fz = reg["windows"][wn]["frozen_v6"]
            sd = fz["se_mean"][v]
            t_draft = z_eff * fz["e_se_rule"][v] + max(0.0, fz["null_mean"][v])
            d = np.asarray(prep["windows"][wn]["variants"][v], dtype=np.float64)
            # p = (1 + #{d >= y}) / (1 + R) <= a  <=>  #{d >= y} <= a (1 + R) - 1
            R = d.size
            kmax = math.floor(a * (1 + R) - 1)
            srt = np.sort(d)[::-1]
            y_by = float(srt[kmax]) if kmax >= 0 else float("inf")   # need y > the (kmax+1)-th largest
            t_full = max(Z * fz["e_se_rule"][v] + max(0.0, fz["null_mean"][v]), fz["q95"][v], y_by)
            pd *= N.cdf((c_v - t_draft) / sd)
            pf *= N.cdf((c_v - t_full) / sd)
            detail[wn] = {"t_draft": t_draft, "t_by_replicates": y_by, "t_full": t_full}
        e_draft[m] = pd
        e_full[m] = {"power": pf, "alpha_by": a, **detail}
    ep[v] = {"draft_method": e_draft, "full_gate_with_replicate_p": e_full}
res["endpower"] = ep

# ---------------------------------------------------------------- OC of rule U at IC = 0 (analytic upper bound with v6 constants)
for v in VARS:
    c_v = rows[v]["threshold_on_xP"]
    mp = res["recompute"]["m_P"][v]
    sdp = mp["se_mean_P_max"]
    res["oc"][v] = {"SD_P_null": sdp, "c_v": c_v,
                    "P_handover_if_true_mean_eq_m_P": 1 - N.cdf((c_v - mp["frozen"]) / sdp),
                    "P_handover_if_true_mean_eq_0": 1 - N.cdf(c_v / sdp),
                    "t_P_at_c_v": c_v / sdp}

# ---------------------------------------------------------------- SE rule vs SD of the mean (size of (1b) alone under the null model)
size = {}
for wn in WINS:
    fz = reg["windows"][wn]["frozen_v6"]
    for v in VARS:
        ratio = fz["e_se_rule"][v] / fz["se_mean"][v]
        size[f"{wn}_{v}"] = {"e_se_rule_over_se_mean": ratio,
                             "approx_size_1b_alone": 1 - N.cdf((Z * fz["e_se_rule"][v] - fz["null_mean"][v]) / fz["se_mean"][v]),
                             "size_with_q95": 1 - N.cdf((max(Z * fz["e_se_rule"][v], fz["q95"][v]) - fz["null_mean"][v]) / fz["se_mean"][v])}
res["size"] = size

OUT.write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({"consistency": res["consistency"]}, indent=1, default=str))
for v in VARS:
    r = rows[v]
    print(v, {k: (round(x, 6) if isinstance(x, float) else x) for k, x in r.items() if k != "rule_U_at_threshold"})
    print("   U@thr", r["rule_U_at_threshold"]["handed"], r["rule_U_at_threshold"]["regime"],
          [round(x, 4) for x in r["rule_U_at_threshold"]["window_power"]], r["rule_U_at_threshold"]["regime_a3"],
          "mu_sel", r["rule_U_at_threshold"]["mu_sel"], "below:", r["rule_U_just_below"])
    print("   endpower draft", {m: round(x, 4) for m, x in ep[v]["draft_method"].items()})
    print("   endpower full ", {m: round(x["power"], 4) for m, x in ep[v]["full_gate_with_replicate_p"].items()})
    print("   OC", {k: round(x, 5) for k, x in res["oc"][v].items()})
for k, x in res["power"].items():
    if k.startswith("T_"):
        print(k, {kk: round(vv, 6) for kk, vv in x.items()})
for k, x in res["size"].items():
    print("size", k, {kk: round(vv, 4) for kk, vv in x.items()})
