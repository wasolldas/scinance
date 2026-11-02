"""Independent re-computation for the adversarial review of the H-33 derivation (outcome-free).

Reads ONLY the v6b nuisance artifact (prelaunch JSON + p replicates), the registered H-32 YAML (cross-check) and the
derivation's JSON outputs (for comparison).  No panel, no outcome, no harvest client, no sealed files.
All power / MDE / regime numbers via power_p1 and h32_fm8.estimators; own closed forms only as a cross-check.

Usage: python3 -I review_h33.py <repo_root>
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402

from bybit_edge.research import power_p1  # noqa: E402
from bybit_edge.research.h32_fm8 import constants as C  # noqa: E402
from bybit_edge.research.h32_fm8 import estimators as est  # noqa: E402

ST = REPO / "scinance3-impl/state"
V6B = ST / "runs/h32_20261021_v6b/h32_prelaunch.json"
REP = ST / "runs/h32_20261021_v6b/h32_prelaunch_p_replicates.json"
HJ = ST / "herleitung_h33/power_h33.json"
NJ = ST / "herleitung_h33/nuisance_neg.json"

VARS = ("mom1", "mom2", "mom4")
WINS = ("W1", "W2")
Z = float(C.Z_KRIT)
ZP = float(C.Z_POWER)
GRID = (0.010, 0.015, 0.020, 0.025, 0.033, 0.048)
# GL-035 (gate_log.md table): F2_real, c_real -- dispersion only, used ONLY for reading S (as the derivation does)
F2 = {"mom1": 0.01033, "mom2": 0.01202, "mom4": 0.01307}            # gate_log rounding (5 digits)
F2_H = {"mom1": 0.010331, "mom2": 0.012016, "mom4": 0.013072}       # derivation (pilot md, 6 digits)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    out: dict = {"inputs": {"v6b": sha(V6B), "rep": sha(REP), "power_h33": sha(HJ), "nuisance_neg": sha(NJ)}}
    d = json.loads(V6B.read_text())
    rep = json.loads(REP.read_text())
    hj = json.loads(HJ.read_text())
    nj = json.loads(NJ.read_text())

    # ---------------- 1. nuisance in the negative direction -----------------
    nuis: dict = {}
    for wn in WINS:
        w = d["windows"][wn]
        fz = w["frozen_v6"]
        cells = w["null"]["cells"]
        nuis[wn] = {"v_fm8": float(w["v_fm8"]), "w": int(w["geometry"]["w_judged"]), "floor": float(w["floor_fm8"])}
        for v in VARS:
            df, dr = cells["driftfree"]["variants"][v], cells["drifting"]["variants"][v]
            raw = np.asarray(rep["windows"][wn]["variants"][v], dtype=np.float64)
            assert rep["windows"][wn]["cell"][v] == "drifting"
            assert est.series_sha256(raw[:1000]) == dr["draws_sha256"]
            neg = -raw
            q1000 = float(np.quantile(neg[:1000], 0.95))
            q10000 = float(np.quantile(neg, 0.95))
            q1000_alt = -float(np.quantile(raw[:1000], 0.05))
            m_df, m_dr = -float(df["null_mean"]), -float(dr["null_mean"])
            # shape indicator of the two cells in the POSITIVE tail (only thing v6b keeps for driftfree)
            dev_pos_df = float(df["q95"]) - float(df["null_mean"])
            dev_pos_dr = float(dr["q95"]) - float(dr["null_mean"])
            # lower-tail shape of the drifting cell vs its upper tail (skew)
            dev_neg_dr = max(q1000, q10000) - m_dr
            nuis[wn][v] = {
                "se_mean": float(fz["se_mean"][v]), "e_se_rule": float(fz["e_se_rule"][v]), "sd_week": float(fz["sd_week"][v]),
                "se_mean_cells": [float(df["se_mean"]), float(dr["se_mean"])],
                "m_neg_df": m_df, "m_neg_dr": m_dr, "binding_neg": "driftfree" if m_df >= m_dr else "drifting",
                "q95n_dr_1000": q1000, "q95n_dr_1000_alt_minus_q05": q1000_alt, "q95n_dr_10000": q10000,
                "dev95_neg_dr": dev_neg_dr, "dev95_pos_df_1000": dev_pos_df, "dev95_pos_dr_1000": dev_pos_dr,
                "shape_diff_pos_df_minus_dr": dev_pos_df - dev_pos_dr,
                "mean_check_first1000": float(raw[:1000].mean()) + m_dr * 1.0,   # should be 0 (raw mean = -m_dr)
                "mean_10000_neg": float(neg.mean()), "sd_10000": float(neg.std(ddof=1)),
                "skew_10000": float(((neg - neg.mean()) ** 3).mean() / neg.std() ** 3),
            }
        # selection ceiling K = 3, negative direction (drifting cell; raw = H-32 convention, recentred = report)
        draws = {v: np.asarray(rep["windows"][wn]["variants"][v], dtype=np.float64) for v in VARS}
        sg = {v: -1 for v in VARS}
        nuis[wn]["ceiling"] = {
            "raw_1000": est.signed_selection_ceiling({v: draws[v][:1000] for v in VARS}, sg),
            "raw_10000": est.signed_selection_ceiling(draws, sg),
            "rec_10000": est.signed_selection_ceiling({v: draws[v] - float(d["windows"][wn]["null"]["cells"]["drifting"]["variants"][v]["null_mean"]) for v in VARS}, sg),
        }
    out["nuisance"] = nuis

    # ---------------- 2. power lines (reading T and S) -----------------------
    def terms(les: str, wn: str, v: str, f2: dict) -> dict:
        n = nuis[wn][v]
        vf, wj = nuis[wn]["v_fm8"], nuis[wn]["w"]
        m = max(n["m_neg_df"], n["m_neg_dr"])           # frozen (driftfree), negative
        dev = n["dev95_neg_dr"]                          # provisional shape (drifting cell)
        if les == "T":
            se_t, sd_t, k = n["e_se_rule"], n["se_mean"], 1.0
        else:
            sp = math.sqrt(vf + f2[v]) / math.sqrt(wj)
            se_t, sd_t = max(n["e_se_rule"], sp), max(n["se_mean"], sp)
            k = est.k_pred(vf, f2[v], n["sd_week"])
        q95n = max(n["q95n_dr_1000"], n["q95n_dr_10000"])
        q95eff = est.q95_effective(m, k, q95n - (n["m_neg_dr"] - m))   # = max(0,m) + k*(q95n_dr - m_dr) since m<0
        t1b = Z * se_t + max(0.0, m)
        t1c = q95eff
        dr_t = est.scaled_replicates(-np.asarray(rep["windows"][wn]["variants"][v], dtype=np.float64), n["m_neg_dr"], k)
        return {"se_t": se_t, "sd_t": sd_t, "k": k, "m": m, "t1b": t1b, "t1c": t1c, "T": max(t1b, t1c),
                "mde_1b": power_p1.mde80(se_t, Z, sd_t) + max(0.0, m), "mde_1c": t1c + ZP * sd_t,
                "mde_w": max(t1b, t1c) + ZP * sd_t, "mde_1c_no_recentre": q95n + ZP * n["se_mean"],
                "mde_1b_with_pull": t1b + abs(min(0.0, m)) + ZP * sd_t, "draws": dr_t}

    def at(les: str, v: str, pi: float, f2: dict) -> dict:
        tt = {wn: terms(les, wn, v, f2) for wn in WINS}
        wp = {wn: power_p1.condition_power(pi, tt[wn]["T"], tt[wn]["sd_t"]) for wn in WINS}
        r = power_p1.assign_regime([pi - (tt[wn]["T"] - Z * tt[wn]["se_t"]) for wn in WINS], [tt[wn]["se_t"] for wn in WINS],
                                   sds=[tt[wn]["sd_t"] for wn in WINS])
        a3 = power_p1.assign_regime_a3_practice([pi - max(0.0, tt[wn]["m"]) for wn in WINS], [tt[wn]["se_t"] for wn in WINS],
                                                [tt[wn]["sd_t"] for wn in WINS])
        ep = {}
        for mm in (3, 14):
            e = est.end_power_replicates(pi, mm, {wn: {"se_t": tt[wn]["se_t"], "sd_t": tt[wn]["sd_t"], "null_mean": tt[wn]["m"],
                                                       "q95": tt[wn]["t1c"], "draws": tt[wn]["draws"]} for wn in WINS})
            # own cross-check of the threshold (closed form, no estimator)
            b = 0.10 / (mm * sum(1.0 / i for i in range(1, mm + 1)))
            from statistics import NormalDist
            ze = max(Z, NormalDist().inv_cdf(1 - b))
            own = 1.0
            for wn in WINS:
                thr = max(ze * tt[wn]["se_t"], float(np.quantile(tt[wn]["draws"], 1 - b)), tt[wn]["t1c"])
                own *= NormalDist().cdf((pi - thr) / tt[wn]["sd_t"])
            ep[str(mm)] = {"joint": e["joint"], "own": own}
        return {"wp": wp, "joint": wp["W1"] * wp["W2"], "regime": r["regime"], "gate": r["gate_power_product"],
                "a3": a3["regime"], "ep": ep}

    lines: dict = {}
    for les, f2 in (("T", F2_H), ("S", F2_H), ("S_gl035_rounded", F2)):
        L = "S" if les.startswith("S") else "T"
        lines[les] = {}
        for v in VARS:
            tt = {wn: terms(L, wn, v, f2) for wn in WINS}
            lines[les][v] = {"windows": {wn: {k: x for k, x in tt[wn].items() if k != "draws"} for wn in WINS},
                             "mde_star": max(tt[wn]["mde_w"] for wn in WINS),
                             "grid": {f"{pi:.3f}": at(L, v, pi, f2) for pi in GRID}}
    out["lines"] = lines

    # ---------------- 3. compare with the derivation ------------------------
    cmp_rows = []
    for les in ("T", "S"):
        for v in VARS:
            hv = hj["power_lines"][les]["variants"][v]
            mv = lines[les][v]
            for wn in WINS:
                for key_h, key_m in (("mde80_1b", "mde_1b"), ("mde80_1c", "mde_1c"), ("mde80_w", "mde_w"), ("k", "k"),
                                     ("se_t", "se_t"), ("sd_t", "sd_t"), ("T_1c", "t1c")):
                    a, b = float(hv["windows"][wn][key_h]), float(mv["windows"][wn][key_m])
                    cmp_rows.append((les, v, wn, key_h, a, b, (b - a) / a if a else float("nan")))
            for pi in GRID:
                g_h = hv["grid"][f"{pi:.3f}"]
                g_m = mv["grid"][f"{pi:.3f}"]
                for wn in WINS:
                    a, b = g_h["window_power"][wn]["P_window"], g_m["wp"][wn]
                    cmp_rows.append((les, v, f"{wn}@{pi}", "P_window", a, b, (b - a) / a if a else float("nan")))
                cmp_rows.append((les, v, f"@{pi}", "regime", g_h["regime_p1"], g_m["regime"], None))
                cmp_rows.append((les, v, f"@{pi}", "a3", g_h["regime_a3_practice"], g_m["a3"], None))
                for mm in ("3", "14"):
                    a = g_h["end_power"][mm]["replicates_lower_bound"]["joint"]
                    b = g_m["ep"][mm]["joint"]
                    cmp_rows.append((les, v, f"@{pi}", f"EP m{mm}", a, b, (b - a) / a if a else float("nan")))
    worst = 0.0
    mism = []
    for r in cmp_rows:
        if r[6] is None:
            if r[4] != r[5]:
                mism.append(r)
        elif isinstance(r[6], float) and math.isfinite(r[6]):
            worst = max(worst, abs(r[6]))
            if abs(r[6]) > 1e-9:
                mism.append(r)
    out["compare"] = {"n": len(cmp_rows), "max_rel_dev": worst, "mismatches": mism[:50]}

    # nuisance_neg.json spot checks
    nc = []
    for wn in WINS:
        for v in VARS:
            a = nj["windows"][wn]["variants"][v]
            n = nuis[wn][v]
            nc.append((wn, v, a["null_mean_neg"]["frozen_neg"] - max(n["m_neg_df"], n["m_neg_dr"]),
                       a["q95_neg_drifting_1000"]["value"] - n["q95n_dr_1000"], a["q95_neg_drifting_10000"]["value"] - n["q95n_dr_10000"],
                       a["dev95_neg_drifting"]["value"] - n["dev95_neg_dr"], a["binding_cell_neg"]["value"] == n["binding_neg"]))
    out["nuisance_compare"] = nc
    out["ceiling_compare"] = {wn: {k: (nj["windows"][wn]["ceiling_k3_neg"][f"drifting_{k.replace('rec', 'recentred')}"], nuis[wn]["ceiling"][k])
                                   for k in ("raw_1000", "raw_10000", "rec_10000")} for wn in WINS}

    # ---------------- 4. literature conversions (re-typed from BELEGE_AUS_PDF 2.3 / 3.1) ----------
    sx_si, sx_ll = 0.330 + 0.279, 0.245 + 0.169
    f8 = 0.75423
    lit = {}
    for v, h, s_si, s_ll, s_br, b_ltw in (("mom1", "1W", -0.0391, 0.0136, -0.0012, -0.002), ("mom2", "2W", -0.0335, 0.0144, -0.0015, 0.000),
                                         ("mom4", "4W", -0.0315, 0.0084, -0.0050, -0.001)):
        lit[v] = {"R1_A": -s_si / sx_si * f8, "R4_A": -s_ll / sx_ll * f8,
                  "R3_ficura": sorted([-s_br / sx_si * f8, -s_br / sx_ll * f8]),
                  "R3_ltw_fm": sorted([-b_ltw * math.sqrt(2) / s * f8 for s in (0.148, 0.182, 0.25)])}
    # Weg B with the literature-implied SD(IC_t) 0.24 (BELEGE 4, Ficura L&L) instead of the v6b null SD -- report only
    lit["weg_B_with_source_sd_0p24_mom1_R1"] = 7.309 / math.sqrt(291) * 0.24 * f8
    lit["weg_B_with_null_sd_W1_mom1_R1"] = 7.309 / math.sqrt(291) * nuis["W1"]["mom1"]["sd_week"] * f8
    out["literature"] = lit
    out["derivation_literature"] = {v: {k: hj["umrechnung"]["variants"][v]["fm8_skala"][k] for k in
                                        ("R1_klein_illiquide_A_stern", "R4_gross_liquide_A_stern", "R3_breit_ficura_A_stern_band",
                                         "R3_breit_ltw_fm_band", "R1b_klein_illiquide_B")} for v in VARS}

    # ---------------- 5. bounce numbers of the derivation (read only) -------
    b = hj["bounce_fixture_synthetisch"]
    out["bounce"] = {wn: {"single_seed_neg": b["windows"][wn]["ic_bounce_neg"], "ratio_T": b["windows"][wn]["verhaeltnis_zu_T_neg"],
                          "multiseed": b["windows"][wn]["mehrseed_53_252"]} for wn in WINS}

    # ---------------- 6. what would the persistence-null mean imply (record numbers only) ----
    # registry/Drittfassung: mom1 q95 (positive dir.) W1 -0.0064 / W2 -0.0362; null means mom1/2/4 -0.0036..-0.0469.
    # SE of the persistence-null window mean ~ the raw-IC floor B/sqrt(W): W1 0.006737, W2 0.005870 (Drittfassung table)
    pn = {}
    for wn, q95, se in (("W1", -0.0064, 0.006737), ("W2", -0.0362, 0.005870)):
        mean_est = q95 - Z * se          # rough: q95 = mean + z se under normality
        pn[wn] = {"mom1_null_mean_raw_est": mean_est, "in_reversal_dir": -mean_est, "fm8_scaled_x0.754": -mean_est * f8,
                  "vs_T_MDE80_rev1": lines["T"]["mom1"]["windows"][wn]["mde_w"], "vs_S_MDE80_rev1": lines["S"]["mom1"]["windows"][wn]["mde_w"]}
    out["persistence_null_record_based"] = pn

    txt = json.dumps(out, sort_keys=True, indent=1, default=lambda o: None)
    print(txt)


if __name__ == "__main__":
    main()
