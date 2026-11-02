"""Gate audit H-32, follow-up: recompute the v6b core numbers from the v6b artefact only (no panel, no outcome).

Reads: v6b JSON, K CSVs, p replicates (null draws), template YAML (U-3).  Uses power_p1, handover, estimators from HEAD.
Writes rr2_check.json next to this script.
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
from bybit_edge.research.h32_fm8 import artifacts, handover, estimators as est, constants as C, universe  # noqa: E402

RUN = REPO / "scinance3-impl/state/runs/h32_20261021_v6b"
TPL = REPO / "scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"
OUT = Path(__file__).with_name("rr2_check.json")
VARS = ("mom1", "mom2", "mom4", "rev_gap")
WINS = ("W1", "W2")
N = power_p1._N
Z = power_p1.z_krit(0.05)
ZP = power_p1.Z_POWER

res: dict = {"files": {}, "consistency": {}, "recompute": {}, "power": {}, "endpower": {}, "oc": {}, "size": {}, "scaling": {}}
for p in sorted(RUN.iterdir()):
    res["files"][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
res["files"][TPL.name] = hashlib.sha256(TPL.read_bytes()).hexdigest()
js = json.loads((RUN / "h32_prelaunch.json").read_text())
reg = yaml.safe_load(TPL.read_text())
prep = json.loads((RUN / "h32_prelaunch_p_replicates.json").read_text())

# ---------------------------------------------------------------- hashes, universe
core = {k: v for k, v in js.items() if k not in ("code", "result_sha256")}
c = res["consistency"]
c["result_sha256_ok"] = artifacts.canonical_sha256(core) == js["result_sha256"]
c["p_file_sha"] = [js["p_replicates"]["file_sha256"], reg["fdr"]["replicates_sha256"], res["files"]["h32_prelaunch_p_replicates.json"]]
u = js["universe"]
ex = u["excluded_symbols"]
c["universe"] = {"n_before": u["n_before"], "n_after": u["n_after"], "excluded": u["excluded"],
                 "excluded_sha_ok": universe.excluded_sha256(ex) == u["excluded_sha256"],
                 "n_perp": sum(1 for s in ex if s.endswith("PERP")), "n_dated": sum(1 for s in ex if "-" in s),
                 "all_excluded_not_linear_usdt": all(not universe.is_linear_usdt_perpetual(s) for s in ex),
                 "yaml_pin": reg["universe"]}
c["fingerprints_json"] = {k: v for k, v in js["data_fingerprints"].items() if k != "union_range_detail"}
c["fingerprints_yaml"] = reg["data_fingerprints"]
c["runner_json"], c["runner_yaml"] = js.get("runner"), reg.get("runner")
c["cut"] = js["cut"]

mism = []
for wn in WINS:
    fj, fy = js["windows"][wn]["frozen_v6"], reg["windows"][wn]["frozen_v6"]
    for k, v in fy.items():
        if isinstance(v, dict):
            mism += [f"{wn}.{k}.{vv}" for vv, x in v.items() if float(x) != float(fj[k][vv])]
        elif k == "k_fm8_series_sha256":
            mism += [f"{wn}.{k}"] if v != fj[k] else []
        elif float(v) != float(fj[k]):
            mism.append(f"{wn}.{k}")
for v in VARS:
    if float(reg["pilot_window"]["frozen_v6"]["m_P"][v]) != float(js["windows"]["P"]["m_P"][v]):
        mism.append(f"P.m_P.{v}")
c["yaml_vs_json_mismatches"] = mism

# ---------------------------------------------------------------- K, floor, v
for wn in ("P", "W1", "W2"):
    w = js["windows"][wn]
    k = np.asarray(w["k_fm8_series"], dtype=np.float64)
    csv = np.loadtxt(RUN / f"h32_prelaunch_{wn}_k_fm8.csv", delimiter=",", skiprows=1)[:, 1]
    sha_k = hashlib.sha256(np.ascontiguousarray(k.astype("<i8")).tobytes()).hexdigest()
    res["recompute"][f"{wn}_k"] = {"csv_equal": bool(np.array_equal(csv, k)), "sha_ok": sha_k == w["k_fm8_series_sha256"],
                                   "floor_ok": float(np.mean(1 / np.sqrt(k - 1))) == w["floor_fm8"],
                                   "v_ok": float(np.mean(1 / (k - 1))) == w["v_fm8"], "series": [int(x) for x in k],
                                   "geometry": w["geometry"], "k_alive": w["k"]}

# ---------------------------------------------------------------- frozen = max(cells), q95 rule, binding cells
for wn in WINS:
    cells = js["windows"][wn]["null"]["cells"]
    fz = js["windows"][wn]["frozen_v6"]
    rows = {}
    for v in VARS:
        a, b = cells["driftfree"]["variants"][v], cells["drifting"]["variants"][v]
        row = {}
        for key in ("se_mean", "e_se_rule", "sd_week", "null_mean"):
            row[key] = max(a[key], b[key]) == fz[key][v]
        q1000 = max(a["q95"], b["q95"])
        d = np.asarray(prep["windows"][wn]["variants"][v], dtype=np.float64)
        q10000 = float(np.quantile(d[np.isfinite(d)], 0.95))
        row["q95_1000_ok"] = q1000 == fz["q95_1000"][v]
        row["q95_10000_ok"] = q10000 == fz["q95_10000"][v]
        row["q95_max_ok"] = max(q1000, q10000) == fz["q95"][v]
        cell = prep["windows"][wn]["cell"][v]
        row["binding_cell"] = cell
        row["binding_expected"] = "drifting" if b["null_mean"] > a["null_mean"] else "driftfree"
        first = d[:1000]
        cc = cells[cell]["variants"][v]
        row["first1000_mean_ok"] = float(first.mean()) == cc["null_mean"]
        row["first1000_sha_ok"] = est.series_sha256(first) == cc["draws_sha256"]
        row["all10000"] = {"mean": float(d.mean()), "sd": float(d.std(ddof=1)), "n_nan": int(np.isnan(d).sum())}
        row["exceed_q95_frozen_last9000"] = float((d[1000:] >= fz["q95"][v]).mean())
        row["null_mean_driftfree"] = a["null_mean"]
        rows[v] = row
    res["recompute"][f"{wn}_cells"] = rows
    res["recompute"][f"{wn}_ceiling_ok"] = fz["ceiling_k4"] == cells["driftfree"]["ceiling_k4"]
cp = js["windows"]["P"]["null"]["cells"]
res["recompute"]["m_P"] = {v: {"ok": max(cp["driftfree"]["variants"][v]["null_mean"], cp["drifting"]["variants"][v]["null_mean"]) == js["windows"]["P"]["m_P"][v],
                               "se_mean_P": max(cp["driftfree"]["variants"][v]["se_mean"], cp["drifting"]["variants"][v]["se_mean"]),
                               "m_P": js["windows"]["P"]["m_P"][v]} for v in VARS}

# ---------------------------------------------------------------- thresholds, power line, U-3
pw = {}
for v in VARS:
    hc = handover.handover_constants(reg, v)
    per = {}
    for wn in WINS:
        fz = reg["windows"][wn]["frozen_v6"]
        t = Z * fz["e_se_rule"][v] + max(0.0, fz["null_mean"][v])
        per[wn] = {"T": t, "ceil_over_T": fz["ceiling_k4"] / t, "q95": fz["q95"][v],
                   "mde80_1b_credit": power_p1.mde80(fz["e_se_rule"][v], Z, sd=fz["se_mean"][v]) + max(0.0, fz["null_mean"][v]),
                   "mde80_1c": fz["q95"][v] + ZP * fz["se_mean"][v],
                   "u_comp": power_p1.mde80(fz["e_se_rule"][v], Z, sd=fz["se_mean"][v])}
    m_star = max(0.0, reg["pilot_window"]["frozen_v6"]["m_P"][v], *(reg["windows"][w]["frozen_v6"]["null_mean"][v] for w in WINS))
    thr_u = max(p["u_comp"] for p in per.values()) + m_star
    thr_1c = max(p["mde80_1c"] for p in per.values())
    c_v = max(thr_u, thr_1c)
    se_p = res["recompute"]["m_P"][v]["se_mean_P"]
    h_at = handover.evaluate_handover({"x_p": c_v, "se_p": se_p, "f2_real": 0.0, "c_real": 1.0}, hc)
    h_lo = handover.evaluate_handover({"x_p": c_v - 1e-9, "se_p": se_p, "f2_real": 0.0, "c_real": 1.0}, hc)
    h_hi = handover.evaluate_handover({"x_p": c_v + 0.5 * se_p, "se_p": se_p, "f2_real": 0.0, "c_real": 1.0}, hc)
    fz1 = reg["windows"]["W1"]["frozen_v6"]
    a3_on_xp = max(2.4865 * reg["windows"][w]["frozen_v6"]["e_se_rule"][v] + ZP * reg["windows"][w]["frozen_v6"]["se_mean"][v]
                   + max(0.0, reg["windows"][w]["frozen_v6"]["null_mean"][v]) for w in WINS)
    pw[v] = {"per_window": per, "m_star": m_star, "threshold_u": thr_u, "threshold_1c": thr_1c, "c_v_u3": c_v,
             "code_threshold": h_at["threshold_on_point"], "code_binding": h_at["threshold_binding"], "handed_at": h_at["handed_over"],
             "handed_below": h_lo["handed_over"], "regime_at": h_at["regime_p1"]["regime"], "window_power_1b_at": h_at["regime_p1"]["window_power"],
             "window_power_1c_at": {wn: N.cdf((c_v - per[wn]["q95"]) / reg["windows"][wn]["frozen_v6"]["se_mean"][v]) for wn in WINS},
             "a3_at": h_at["regime_a3_practice"]["regime"], "a3_mde80_on_xp_credit": a3_on_xp,
             "mu_sel_at_plus_half_se": h_hi["mu_sel"], "rule_version": h_at["rule_version"],
             "artifact_power_line_threshold": js["power_line"]["variants"][v]["handover_threshold_on_point"]}
res["power"] = pw
res["consistency"]["cond_ii_text_equal"] = reg["handover_rule"]["conditions"][1]["text"] == C.HANDOVER_COND_II
res["consistency"]["handover_version"] = [reg["handover_rule"]["version"], C.HANDOVER_VERSION]


def H(m: int) -> float:
    return sum(1.0 / i for i in range(1, m + 1))


# ---------------------------------------------------------------- end power at the U-3 threshold
for v in VARS:
    c_v = pw[v]["c_v_u3"]
    out = {"gate_plus_scaled_p_k1": {}, "builder_method": {}}
    for m in (1, 2, 3, 4, 11):
        a = 0.10 / (m * H(m))
        z_eff = max(Z, N.inv_cdf(1 - a))
        pg, pb = 1.0, 1.0
        for wn in WINS:
            fz = reg["windows"][wn]["frozen_v6"]
            sd = fz["se_mean"][v]
            nm = fz["null_mean"][v]
            d = np.asarray(prep["windows"][wn]["variants"][v], dtype=np.float64)
            d_k1 = est.scaled_replicates(d, nm, 1.0)                    # test-run transform at k = 1
            R = d.size
            kmax = math.floor(a * (1 + R) - 1)
            y_by = float(np.sort(d_k1)[::-1][kmax])                      # p <= a  <=>  y > the (kmax+1)-th largest
            t_g = max(Z * fz["e_se_rule"][v] + max(0.0, nm), fz["q95"][v], y_by)
            t_b = max(z_eff * fz["e_se_rule"][v] + max(0.0, nm), float(np.quantile(d, 1 - a)), fz["q95"][v])
            pg *= N.cdf((c_v - t_g) / sd)
            pb *= N.cdf((c_v - t_b) / sd)
        out["gate_plus_scaled_p_k1"][m] = pg
        out["builder_method"][m] = pb
    res["endpower"][v] = out

# ---------------------------------------------------------------- OC of U-3 at IC = 0
for v in VARS:
    c_v, mp = pw[v]["c_v_u3"], res["recompute"]["m_P"][v]
    res["oc"][v] = {"loc_m_P": 1 - N.cdf((c_v - mp["m_P"]) / mp["se_mean_P"]), "loc_0": 1 - N.cdf(c_v / mp["se_mean_P"]),
                    "t_at_c_v": c_v / mp["se_mean_P"]}

# ---------------------------------------------------------------- size of (1b)+(1c) under the null model, k = 1
for wn in WINS:
    fz = reg["windows"][wn]["frozen_v6"]
    for v in VARS:
        res["size"][f"{wn}_{v}"] = {"e_se_over_se": fz["e_se_rule"][v] / fz["se_mean"][v],
                                    "size_1b_alone": 1 - N.cdf((Z * fz["e_se_rule"][v] - fz["null_mean"][v]) / fz["se_mean"][v]),
                                    "size_gate": 1 - N.cdf((max(Z * fz["e_se_rule"][v], fz["q95"][v]) - fz["null_mean"][v]) / fz["se_mean"][v])}

# ---------------------------------------------------------------- scaled null: gate (1c) vs p consistency, k grid
for wn in WINS:
    fz = reg["windows"][wn]["frozen_v6"]
    for v in VARS:
        d = np.asarray(prep["windows"][wn]["variants"][v], dtype=np.float64)
        nm, q = fz["null_mean"][v], fz["q95"][v]
        rows = {}
        for k in (1.0, 1.1, 1.3):
            q_eff = est.q95_effective(nm, k, q)
            pv = (1 + int((est.scaled_replicates(d, nm, k) >= q_eff).sum())) / (1 + d.size)
            rows[str(k)] = {"q95_eff": q_eff, "p_at_q95_eff": pv}
        res["scaling"][f"{wn}_{v}"] = rows

OUT.write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res["consistency"], indent=1, default=str)[:2500])
for wn in ("P", "W1", "W2"):
    r = res["recompute"][f"{wn}_k"]
    print(wn, {k: r[k] for k in ("csv_equal", "sha_ok", "floor_ok", "v_ok", "k_alive")})
for wn in WINS:
    bad = {v: [k for k, x in r.items() if isinstance(x, bool) and not x] for v, r in res["recompute"][f"{wn}_cells"].items()}
    print(wn, "cell checks failing:", bad, "ceiling_ok", res["recompute"][f"{wn}_ceiling_ok"],
          "exceed9k", {v: round(r["exceed_q95_frozen_last9000"], 4) for v, r in res["recompute"][f"{wn}_cells"].items()},
          "binding", {v: (r["binding_cell"], r["binding_expected"]) for v, r in res["recompute"][f"{wn}_cells"].items()})
print("m_P ok", {v: x["ok"] for v, x in res["recompute"]["m_P"].items()})
for v in VARS:
    p = pw[v]
    print(v, "T/ceil", {wn: (round(p["per_window"][wn]["T"], 6), round(p["per_window"][wn]["ceil_over_T"], 3)) for wn in WINS},
          "mde1b", {wn: round(p["per_window"][wn]["mde80_1b_credit"], 6) for wn in WINS},
          "mde1c", {wn: round(p["per_window"][wn]["mde80_1c"], 6) for wn in WINS})
    print("   m*", round(p["m_star"], 6), "thr_u", round(p["threshold_u"], 6), "thr_1c", round(p["threshold_1c"], 6), "c_v", round(p["c_v_u3"], 6),
          "code", round(p["code_threshold"], 6), p["code_binding"], "handed", p["handed_at"], "below", p["handed_below"], p["regime_at"],
          "pw1b", [round(x, 3) for x in p["window_power_1b_at"]], "pw1c", {k: round(x, 3) for k, x in p["window_power_1c_at"].items()},
          "a3", p["a3_at"], round(p["a3_mde80_on_xp_credit"], 5), "mu_sel+0.5se", p["mu_sel_at_plus_half_se"], "artifact thr", round(p["artifact_power_line_threshold"], 6))
    print("   endpower gate+p(k=1)", {m: round(x, 3) for m, x in res["endpower"][v]["gate_plus_scaled_p_k1"].items()},
          "builder", {m: round(x, 3) for m, x in res["endpower"][v]["builder_method"].items()})
    print("   OC", {k: round(x, 5) for k, x in res["oc"][v].items()})
for k, x in res["size"].items():
    print("size", k, {kk: round(vv, 4) for kk, vv in x.items()})
for k, x in res["scaling"].items():
    print("scale", k, {kk: (round(vv["q95_eff"], 6), round(vv["p_at_q95_eff"], 4)) for kk, vv in x.items()})
