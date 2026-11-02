"""H-33 derivation (outcome-free): convert the v6b nuisance of H-32 to the NEGATIVE direction, literature prior band,
power lines and prior grid.  No panel, no outcome, no harvest client; inputs are the v6b artifact (nuisance only), the
registered H-32 YAML (cross-check), the GL-035 dispersion numbers (Lesart S only) and literature numbers typed in from the
evidence files (each with its source).  Writes power_h33.json and nuisance_neg.json (deterministic, sorted keys).

Usage: python3 -I h33_compute.py <repo_root> <out_dir>
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from bybit_edge.research import power_p1  # noqa: E402
from bybit_edge.research.h32_fm8 import constants as C  # noqa: E402
from bybit_edge.research.h32_fm8 import estimators as est  # noqa: E402
from bybit_edge.research.wp13_xsec import characteristics, ic  # noqa: E402

V6B_DIR = REPO / "scinance3-impl/state/runs/h32_20261021_v6b"
V6B_JSON = V6B_DIR / "h32_prelaunch.json"
V6B_REP = V6B_DIR / "h32_prelaunch_p_replicates.json"
REG_YAML = REPO / "scinance3-impl/state/registered/h32_v1.yaml"
SPREAD = REPO / "scinance3-impl/state/runs/wp7_20260921/spread_census.json"
PINS = {
    "v6b_json": "f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c",
    "v6b_replicates": "3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef",
    "h32_v1_yaml": "0fadda785f37a9ab24b31f650611a468f5c6bfef8be8fb65a7dc54261c1bbd60",
    "spread_census": "fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083",
}
FJ = "state/runs/h32_20261021_v6b/h32_prelaunch.json"
FR = "state/runs/h32_20261021_v6b/h32_prelaunch_p_replicates.json"

VARS = ("mom1", "mom2", "mom4")
WINS = ("W1", "W2")
S_NEG = -1.0
Z = float(C.Z_KRIT)
ZP = float(C.Z_POWER)
GRID = (0.010, 0.015, 0.020, 0.025, 0.033, 0.048)
M_GRID = (1, 2, 3, 14)
M_BIND, M_OLD = 3, 14
#: GL-035 (gate_log.md) / state/runs/h32_pilot_v1/h32_pilot.md, column F2_real and c_real -- dispersion only (Lesart S).
F2_REAL = {"mom1": 0.010331, "mom2": 0.012016, "mom4": 0.013072}
C_REAL = {"mom1": 1.000, "mom2": 1.000, "mom4": 1.000}
#: power_h32.json fm8_daempfung.faktor_realisiert_durch_injiziert_mom1_W1 (synthetic, mom1); mom2/mom4 upper bound.
FM8_DAMP = 0.75423
RANK_FACTOR = 0.955          # RECHERCHE_BELEGE 1.2 / BELEGE_AUS_PDF 4: Spearman ~ 0.955 x Pearson for small IC


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def q(x, lvl):
    a = np.asarray(x, dtype=np.float64)
    a = a[np.isfinite(a)]
    return float(np.quantile(a, lvl))


def main() -> None:
    hashes = {"v6b_json": sha256_file(V6B_JSON), "v6b_replicates": sha256_file(V6B_REP), "h32_v1_yaml": sha256_file(REG_YAML),
              "spread_census": sha256_file(SPREAD)}
    for k, v in PINS.items():
        if hashes[k] != v:
            raise SystemExit(f"pin mismatch {k}: {hashes[k]} != {v}")
    d = json.loads(V6B_JSON.read_text(encoding="utf-8"))
    rep = json.loads(V6B_REP.read_text(encoding="utf-8"))
    reg = yaml.safe_load(REG_YAML.read_text(encoding="utf-8"))
    spread = json.loads(SPREAD.read_text(encoding="utf-8"))

    checks: list[str] = []
    nuis: dict = {"windows": {}}
    draws_neg: dict = {}
    for wn in WINS:
        w = d["windows"][wn]
        fz = w["frozen_v6"]
        cells = w["null"]["cells"]
        regfz = reg["windows"][wn]["frozen_v6"]
        nuis_w: dict = {
            "w_judged": int(w["geometry"]["w_judged"]),
            "floor_fm8": {"value": float(w["floor_fm8"]), "herkunft": f"[fj: {FJ}#windows.{wn}.floor_fm8]", "richtungsfrei": True,
                          "registrierbar_aus_v6b": "ja"},
            "v_fm8": {"value": float(w["v_fm8"]), "herkunft": f"[fj: {FJ}#windows.{wn}.v_fm8]", "richtungsfrei": True,
                      "registrierbar_aus_v6b": "ja"},
            "k_fm8_series_sha256": {"value": w["k_fm8_series_sha256"], "herkunft": f"[fj: {FJ}#windows.{wn}.k_fm8_series_sha256]",
                                    "registrierbar_aus_v6b": "ja (unveraendert)"},
            "k_alive_min_median_max": [w["k"]["min"], w["k"]["median"], w["k"]["max"]],
            "calibration_stress": {"rho_f": cells["driftfree"]["rho_f"], "beta_sd": cells["driftfree"]["beta_sd"],
                                   "sigma_f": cells["driftfree"]["sigma_f"], "sigma_e": cells["driftfree"]["sigma_e"],
                                   "herkunft": f"[fj: {FJ}#windows.{wn}.null.cells.driftfree]"},
            "bounce_sigma_true": {"value": float(w["bounce_sigma_true"]), "herkunft": f"[fj: {FJ}#windows.{wn}.bounce_sigma_true]"},
            "variants": {},
        }
        draws_neg[wn] = {}
        raw_first = {}
        raw_all = {}
        for v in VARS:
            cdf, cdr = cells["driftfree"]["variants"][v], cells["drifting"]["variants"][v]
            # cross-checks of the v6b artifact (registered YAML = JSON; replicate file = drifting cell)
            for key in ("se_mean", "e_se_rule", "sd_week", "null_mean", "q95"):
                if float(regfz[key][v]) != float(fz[key][v]):
                    raise SystemExit(f"{wn}/{v}/{key}: YAML != JSON")
            cell = rep["windows"][wn]["cell"][v]
            if cell != "drifting":
                raise SystemExit(f"{wn}/{v}: replicate cell {cell}, expected drifting")
            draws_raw = np.asarray(rep["windows"][wn]["variants"][v], dtype=np.float64)
            if draws_raw.size != 10000 or not np.all(np.isfinite(draws_raw)):
                raise SystemExit(f"{wn}/{v}: replicate count / finiteness")
            first = draws_raw[:1000]
            if est.series_sha256(first) != cdr["draws_sha256"]:
                raise SystemExit(f"{wn}/{v}: first 1000 replicates do not hash to the drifting cell's draws_sha256")
            if abs(float(first.mean()) - float(cdr["null_mean"])) > 1e-15:
                raise SystemExit(f"{wn}/{v}: mean of first 1000 != drifting null_mean")
            if q(first, 0.95) != float(cdr["q95"]):
                raise SystemExit(f"{wn}/{v}: q95 of first 1000 != drifting q95")
            if q(draws_raw, 0.95) != float(fz["q95_10000"][v]):
                raise SystemExit(f"{wn}/{v}: q95 of 10000 != q95_10000")
            if abs(float(first.std(ddof=1)) - float(cdr["se_mean"])) > 1e-15:
                raise SystemExit(f"{wn}/{v}: SD of first 1000 != drifting se_mean")
            checks.append(f"{wn}/{v}: replicates = drifting cell (hash, mean, sd, q95_1000, q95_10000 bitgleich)")
            raw_first[v], raw_all[v] = first, draws_raw
            dneg = S_NEG * draws_raw
            draws_neg[wn][v] = dneg
            m_df_neg, m_dr_neg = -float(cdf["null_mean"]), -float(cdr["null_mean"])
            binding_neg = "drifting" if m_dr_neg > m_df_neg else "driftfree"
            q95n_dr_1000 = q(S_NEG * first, 0.95)
            q95n_dr_10000 = q(dneg, 0.95)
            q95n_dr = max(q95n_dr_1000, q95n_dr_10000)
            dev95_dr = q95n_dr - m_dr_neg                       # recentred 95 % quantile of the drifting cell (own mean)
            dev95_pos_v6b = float(fz["q95"][v]) - float(fz["null_mean"][v])
            dev95_pos_dr = float(cdr["q95"]) - float(cdr["null_mean"])
            nuis_w["variants"][v] = {
                "se_mean": {"value": float(fz["se_mean"][v]), "zellen": {"driftfree": cdf["se_mean"], "drifting": cdr["se_mean"]},
                            "herkunft": f"[fj: {FJ}#windows.{wn}.frozen_v6.se_mean.{v}] (= max der Zellen)", "richtungsfrei": True,
                            "registrierbar_aus_v6b": "ja"},
                "e_se_rule": {"value": float(fz["e_se_rule"][v]), "zellen": {"driftfree": cdf["e_se_rule"], "drifting": cdr["e_se_rule"]},
                              "herkunft": f"[fj: {FJ}#windows.{wn}.frozen_v6.e_se_rule.{v}]", "richtungsfrei": True,
                              "registrierbar_aus_v6b": "ja"},
                "sd_week": {"value": float(fz["sd_week"][v]), "zellen": {"driftfree": cdf["sd_week"], "drifting": cdr["sd_week"]},
                            "herkunft": f"[fj: {FJ}#windows.{wn}.frozen_v6.sd_week.{v}]", "richtungsfrei": True,
                            "registrierbar_aus_v6b": "ja"},
                "null_mean_raw": {"driftfree": float(cdf["null_mean"]), "drifting": float(cdr["null_mean"]),
                                  "herkunft": f"[fj: {FJ}#windows.{wn}.null.cells.<zelle>.variants.{v}.null_mean] (Rohrichtung = H-32-Richtung positiv)"},
                "null_mean_neg": {"driftfree": m_df_neg, "drifting": m_dr_neg, "frozen_neg": max(m_df_neg, m_dr_neg),
                                  "regel": "null_mean_neg = -null_mean_raw je Zelle; eingefroren = groesseres in negativer Richtung",
                                  "registrierbar_aus_v6b": "ja"},
                "binding_cell_neg": {"value": binding_neg,
                                     "regel": "pnull.binding_cells auf die negativen Null-Mittel (groesseres Null-Mittel in Richtung)",
                                     "registrierbar_aus_v6b": "ja (Bestimmung); die Replikate dieser Zelle: nein"},
                "q95_neg_drifting_1000": {"value": q95n_dr_1000, "herkunft": f"[fj: {FR}#windows.{wn}.variants.{v}[0:1000]] -> -Q_0.05",
                                          "registrierbar_aus_v6b": "ja"},
                "q95_neg_drifting_10000": {"value": q95n_dr_10000, "herkunft": f"[fj: {FR}#windows.{wn}.variants.{v}] -> -Q_0.05",
                                           "registrierbar_aus_v6b": "ja"},
                "q95_neg_drifting_max": q95n_dr,
                "q95_neg_driftfree_1000": {"value": None, "registrierbar_aus_v6b": "nein",
                                           "grund": "v6b speichert fuer die driftfreie Zelle nur Mittel, SD, oberes q95 und draws_sha256; die "
                                                    "10.000 driftfreien Replikate wurden gerechnet und verworfen (vorlauf.py: nur die bindende Zelle "
                                                    "der positiven Richtung geht in die p-Datei)"},
                "q95_neg_driftfree_10000": {"value": None, "registrierbar_aus_v6b": "nein", "grund": "wie oben"},
                "q95_neg_frozen_dec101_e5": {"value": None, "registrierbar_aus_v6b": "nein",
                                             "regel": "max(q95_1000 ueber beide Zellen, q95_10000 der bindenden Zelle) - beides braucht driftfrei"},
                "dev95_neg_drifting": {"value": dev95_dr, "regel": "q95_neg_drifting_max - null_mean_neg(drifting) = q95_eff(k=1) bei m < 0 "
                                       "mit Drift-Zellen-Form (vorlaeufig bis v7)"},
                "dev95_pos_v6b_frozen": dev95_pos_v6b, "dev95_pos_drifting_1000": dev95_pos_dr,
                "skew_hinweis": "dev95_neg < dev95_pos: die Rohreplikate sind rechtsschief (Review B-4), das obere Quantil in "
                                "negativer Richtung ist das duennere untere Roh-Quantil",
                "p_replikate_neg": {"drifting": "ja: -d der 10.000 Replikate (Datei-sha256 unveraendert, Transformation im Code)",
                                    "driftfree": "nein (v7)"},
                "survivorship": None,
            }
        # signed selection ceiling K = 3 (negative direction), drifting cell (joint replicates of the same simulated panels)
        signs = {v: -1 for v in VARS}
        ceil = {}
        for n, lab in ((1000, "1000"), (10000, "10000")):
            ceil[f"raw_{lab}"] = est.signed_selection_ceiling({v: raw_all[v][:n] for v in VARS}, signs)
            ceil[f"recentred_{lab}"] = est.signed_selection_ceiling(
                {v: raw_all[v][:n] - float(cells["drifting"]["variants"][v]["null_mean"]) for v in VARS}, signs)
        ceil_pos3 = est.signed_selection_ceiling({v: raw_all[v][:1000] for v in VARS}, {v: 1 for v in VARS})
        nuis_w["ceiling_k3_neg"] = {
            "drifting_raw_1000": ceil["raw_1000"], "drifting_raw_10000": ceil["raw_10000"],
            "drifting_recentred_1000": ceil["recentred_1000"], "drifting_recentred_10000": ceil["recentred_10000"],
            "driftfree": None, "registrierbar_aus_v6b": "Drift-Zelle ja (gemeinsame Replikate je Simulation); driftfreie Zelle "
                                                         "(H-32-Konvention der Decke) nein -> v7",
            "bericht_k3_positive_richtung_drifting_1000": ceil_pos3,
            "bericht_v6b_ceiling_k4": {"driftfree": cells["driftfree"]["ceiling_k4"], "drifting": cells["drifting"]["ceiling_k4"]},
            "herkunft": f"[fj: {FR}#windows.{wn}.variants.(mom1,mom2,mom4)] mit estimators.signed_selection_ceiling, Vorzeichen -1",
        }
        # survivorship label (mom1 only in v6b), sign reversed for the negative direction
        sv = w["survivorship"]
        t_pos_mom1 = Z * float(fz["e_se_rule"]["mom1"]) + max(0.0, float(fz["null_mean"]["mom1"]))
        t_neg_mom1 = Z * float(fz["e_se_rule"]["mom1"]) + max(0.0, -float(fz["null_mean"]["mom1"]))
        diff_raw = float(sv["mom1_diff"])
        nuis_w["variants"]["mom1"]["survivorship"] = {
            "diff_raw_drop_minus_close_at_last": diff_raw,
            "in_positive_richtung_schwellen_einheiten_v6b": float(sv["mom1_diff_in_ic_min_units"]),
            "t_pos_v6b": t_pos_mom1, "check_diff_over_t_pos": diff_raw / t_pos_mom1,
            "diff_neg": -diff_raw, "t_neg": t_neg_mom1, "in_negativer_richtung_t_pos_einheiten": -float(sv["mom1_diff_in_ic_min_units"]),
            "in_negativer_richtung_t_neg_einheiten": -diff_raw / t_neg_mom1,
            "richtung": "positiv in H-33-Richtung: das unkontrollierte Ueberlebenden-Panel (drop) erzeugt im signalfreien Fixture "
                        "mechanisches Reversal - Richtung Testbarkeit, falls nicht kontrolliert; registriert ist close_at_last (kontrolliert)",
            "herkunft": f"[fj: {FJ}#windows.{wn}.survivorship] (prelaunch.survivorship_drawdown_fixture, synthetisch)",
        }
        for v in ("mom2", "mom4"):
            nuis_w["variants"][v]["survivorship"] = {"value": None, "status": "UNBELEGT (v6b rechnet das Fixture nur fuer mom1/rev_gap) -> v7"}
        nuis["windows"][wn] = nuis_w

    # ------------------------------------------------------------------------------------------------------------
    # power lines (negative direction), Lesart T (v6b null only) and S (GL-035 dispersion, DEC-94 (5) (i))
    # ------------------------------------------------------------------------------------------------------------
    def window_terms(lesart: str, wn: str, v: str) -> dict:
        nv = nuis["windows"][wn]["variants"][v]
        w_j = nuis["windows"][wn]["w_judged"]
        v_fm8 = nuis["windows"][wn]["v_fm8"]["value"]
        e_se, se_m, sd_wk = nv["e_se_rule"]["value"], nv["se_mean"]["value"], nv["sd_week"]["value"]
        m = nv["null_mean_neg"]["frozen_neg"]                           # binding cell (driftfree) -- exact from v6b
        dev95 = nv["dev95_neg_drifting"]["value"]                        # shape of the drifting cell (provisional until v7)
        if lesart == "T":
            se_t, sd_t, k = e_se, se_m, 1.0
            se_pilot = None
        else:
            se_pilot = math.sqrt(C_REAL[v]) * math.sqrt(v_fm8 + F2_REAL[v]) / math.sqrt(w_j)
            se_t, sd_t = max(e_se, se_pilot), max(se_m, se_pilot)
            k = est.k_pred(v_fm8, F2_REAL[v], sd_wk)
        # q95_eff(k) = max(0, m) + k (q95 - m); m < 0 -> k * (q95 - m); provisional (q95 - m) := dev95 of the drifting cell
        q95_eff = max(0.0, m) + k * dev95
        t1b = Z * se_t + max(0.0, m)
        t1c = q95_eff
        out = {"se_t": se_t, "sd_t": sd_t, "se_w_pilot": se_pilot, "k": k, "m_neg": m, "dev95": dev95, "q95_eff": q95_eff,
               "T_1b": t1b, "T_1c": t1c, "T": max(t1b, t1c), "binding_condition": "1c" if t1c > t1b else "1b",
               "mde80_1b": t1b + ZP * sd_t, "mde80_1c": t1c + ZP * sd_t, "mde80_w": max(t1b, t1c) + ZP * sd_t,
               "mde80_1b_bericht_mechanischer_zug": t1b + abs(min(0.0, m)) + ZP * sd_t,
               "mde80_1c_bericht_spec_woertlich_q95neg_ohne_rezentrierung": nv["q95_neg_drifting_max"] + ZP * se_m,
               "a3_praxis_mde80": power_p1.mde80(se_t, power_p1.Z_PER_WINDOW_A3_PRACTICE, sd_t)}
        out["draws_transformed"] = est.scaled_replicates(draws_neg[wn][v], nv["null_mean_neg"]["drifting"], k)
        return out

    def power_at(lesart: str, v: str, pi: float) -> dict:
        terms = {wn: window_terms(lesart, wn, v) for wn in WINS}
        wp = {}
        for wn in WINS:
            t = terms[wn]
            wp[wn] = {"P_1b": power_p1.condition_power(pi, t["T_1b"], t["sd_t"]),
                      "P_1c": power_p1.condition_power(pi, t["T_1c"], t["sd_t"]),
                      "P_window": power_p1.condition_power(pi, t["T"], t["sd_t"])}
        ses = [terms[wn]["se_t"] for wn in WINS]
        sds = [terms[wn]["sd_t"] for wn in WINS]
        pri_eff = [pi - (terms[wn]["T"] - Z * terms[wn]["se_t"]) for wn in WINS]
        r = power_p1.assign_regime(pri_eff, ses, sds=sds)
        r1b = power_p1.assign_regime([pi - max(0.0, terms[wn]["m_neg"]) for wn in WINS], ses, sds=sds)
        a3 = power_p1.assign_regime_a3_practice([pi - max(0.0, terms[wn]["m_neg"]) for wn in WINS], ses, sds)
        for i, wn in enumerate(WINS):
            if abs(r["window_power"][i] - wp[wn]["P_window"]) > 1e-12:
                raise SystemExit("assign_regime window power != P_window")
        endp = {}
        for m in M_GRID:
            win_in = {wn: {"se_t": terms[wn]["se_t"], "sd_t": terms[wn]["sd_t"], "null_mean": terms[wn]["m_neg"],
                           "q95": terms[wn]["q95_eff"], "draws": terms[wn]["draws_transformed"]} for wn in WINS}
            er = est.end_power_replicates(pi, m, win_in)
            bound = est.by_threshold(m)
            gm = {}
            for wn in WINS:
                qrep = float(np.quantile(terms[wn]["draws_transformed"], 1.0 - bound))
                thr = max(Z * terms[wn]["se_t"], qrep, terms[wn]["q95_eff"])
                gm[wn] = power_p1.condition_power(pi, thr, terms[wn]["sd_t"])
            na = est.end_power(pi, m, {wn: {"se_t": terms[wn]["se_t"], "sd_t": terms[wn]["sd_t"], "null_mean": terms[wn]["m_neg"]}
                                       for wn in WINS})
            endp[str(m)] = {"replicates_lower_bound": {"joint": er["joint"], "window_power": er["window_power"],
                                                       "binding": {wn: er["window_detail"][wn]["binding"] for wn in WINS},
                                                       "by_threshold_p": er["by_threshold_p"], "z_eff": er["z_eff"]},
                            "gate_method_bericht": {"joint": math.prod(gm.values()), "window_power": gm},
                            "normal_approximation_report_only": {"joint": na["joint"], "window_power": na["window_power"]}}
        return {"window_power": wp, "joint_product": math.prod(wp[wn]["P_window"] for wn in WINS),
                "regime_p1": r["regime"], "regime_p1_reason": r["reason"], "dec52_gate_power_product": r["gate_power_product"],
                "regime_p1_only_1b_bericht": r1b["regime"], "regime_a3_practice": a3["regime"],
                "a3_window_power": a3["window_power"], "zugelassen_nur_durch_dec94": a3["zugelassen_nur_durch_dec94"],
                "end_power": endp}

    power: dict = {}
    for les in ("T", "S"):
        pl: dict = {"variants": {}}
        for v in VARS:
            terms = {wn: window_terms(les, wn, v) for wn in WINS}
            mde_star = max(terms[wn]["mde80_w"] for wn in WINS)
            pl["variants"][v] = {
                "windows": {wn: {k2: v2 for k2, v2 in terms[wn].items() if k2 != "draws_transformed"} for wn in WINS},
                "mde80_star": mde_star,
                "min_prior_c10": mde_star,
                "a3_praxis_mde80_star": max(terms[wn]["a3_praxis_mde80"] for wn in WINS),
                "grid": {f"{pi:.3f}": power_at(les, v, pi) for pi in GRID},
            }
        power[les] = pl

    # ------------------------------------------------------------------------------------------------------------
    # literature (each number with its source), conversions A* / B / FM, reversal direction, fm8 scale
    # ------------------------------------------------------------------------------------------------------------
    lit = {
        "ficura_2023": {
            "quelle": "Ficura, FFA WP 3/2023, PDF scratchpad/pdfs_2026-10-20/WP_wps-202301-0003.pdf; Stichprobe 2017/06-2022/12 (S. 4); "
                      "gleichgewichtete Quintile, Folgewochenrendite, NW-t (S. 7-8); BELEGE_AUS_PDF 3.1",
            "n_weeks_abg": 291,
            "S_r": {"large_liquid": {"1W": 0.0136, "2W": 0.0144, "4W": 0.0084, "t": {"1W": 2.332, "2W": 2.686, "4W": 1.570},
                                     "fundstelle": "S. 8 Tab. 3 (oberer Teil)"},
                    "small_illiquid": {"1W": -0.0391, "2W": -0.0335, "4W": -0.0315, "t": {"1W": -7.309, "2W": -6.352, "4W": -6.769},
                                       "fundstelle": "S. 8 Tab. 3 (unterer Teil)"},
                    "breit_M1M_V100K": {"1W": -0.0012, "2W": -0.0015, "4W": -0.0050, "t": {"1W": -0.216, "2W": -0.304, "4W": -1.054},
                                        "fundstelle": "S. 13 Tab. 7 Panel A Spalte 1"},
                    "M10M_V1M": {"1W": 0.0144, "2W": 0.0177, "4W": 0.0113, "t": {"1W": 2.075, "2W": 2.479, "4W": 1.950},
                                 "fundstelle": "S. 13 Tab. 7 Panel A Spalte 2"},
                    "illiquide_M1M_Vlt100K": {"1W": -0.0306, "2W": -0.0258, "4W": -0.0258, "t": {"1W": -5.928, "2W": -5.118, "4W": -5.701},
                                              "fundstelle": "S. 13 Tab. 7 Panel B Spalte 1"}},
            "meanx_1W": {"large_liquid": {"Q1": -0.169, "Q5": 0.245}, "small_illiquid": {"Q1": -0.279, "Q5": 0.330},
                         "fundstelle": "S. 11 Tab. 5"},
            "btc_alpha_1W": {"large_liquid": 0.0131, "small_illiquid": -0.0390, "fundstelle": "S. 11 Tab. 5"},
            "stabilitaet": "Standard-Momentum (gross/liquide) seit Anfang 2021 nicht mehr profitabel; Reversal klein/illiquide stabil (S. 7)",
            "treiber": "Reversal haengt an Coins mit Wochenvolumen < 100 Tsd. USD (S. 13-14, Tab. 7 Panel A/B Spalte 1)",
        },
        "ltw_nber_w25882": {
            "quelle": "Liu/Tsyvinski/Wu, NBER WP 25882 (2019), PDF; Stichprobe 2014-2018 (S. 6); BELEGE_AUS_PDF 2",
            "fm_gt_1mio": {"r1": -0.002, "r2": 0.000, "r4": -0.001, "t": {"r1": -0.692, "r2": 0.020, "r4": -0.274},
                           "fundstelle": "S. 32 Tab. 13 Panel D (Regressor Quintilsnummer 1..5)"},
            "fm_gt_10mio": {"r1": 0.005, "r2": 0.007, "r4": 0.003, "t": {"r1": 1.668, "r2": 2.095, "r4": 0.693},
                            "fundstelle": "S. 32 Tab. 13 Panel E"},
            "vw_quintil_long_short": {"1W": 0.027, "2W": 0.033, "4W": 0.025, "t": {"1W": 1.994, "2W": 2.442, "4W": 2.002},
                                      "fundstelle": "S. 13 Tab. 4"},
            "n_weeks_abg": 260,
        },
        "bianchi_ssrn_3239670": {
            "quelle": "Bianchi/Babiak/Dickerson, SSRN 3239670, PDF; 2017-03..2022-03, taeglich (S. 5)",
            "reversal_1tag_ic_abg": {"gleichgewichtet": 0.090, "wertgewichtet": 0.023, "fundstelle": "BELEGE_AUS_PDF 4 (aus S. 24-25 Tab. 1-2)"},
            "wochenhorizont": "UNBELEGT (nur 1-Tages-Reversal, Haltedauer 1 Tag)",
            "sigma_xs_woche_abg": 0.182,
        },
        "dobrynskaya": {"status": "[sek] Abstract: Momentum 2-4 Wochen, Umschlag in Reversal nach ~1 Monat (2014-2020); Zahlen UNBELEGT "
                                  "(PDF fehlt, BELEGE_AUS_PDF 10)"},
        "shen_urquhart_wang_2020": {"status": "nur ueber Ficura S. 3-4: woechentliches Reversal (gleichgewichtet, ohne Mindest-Marktkap.); "
                                              "kein Textextrakt, Zahlen UNBELEGT"},
        "zaremba_2021": {"status": "nur ueber Ficura S. 4: kleine Coins 1-Tages-Reversal, grosse 1-Tages-Momentum; Zahlen UNBELEGT"},
    }
    fic = lit["ficura_2023"]
    sx = {"large_liquid": fic["meanx_1W"]["large_liquid"]["Q5"] - fic["meanx_1W"]["large_liquid"]["Q1"],
          "small_illiquid": fic["meanx_1W"]["small_illiquid"]["Q5"] - fic["meanx_1W"]["small_illiquid"]["Q1"]}
    hz = {"mom1": "1W", "mom2": "2W", "mom4": "4W"}
    conv: dict = {"S_x_1W": sx, "regel_A_stern": "IC_n = S_r(n) / S_x(1W) der Gruppe (Ausgangsstreuung = Streuung der Vorwochenrendite "
                                                  "derselben Gruppe; Normalitaet, Quintile, k = 2,800 kuerzt sich)", "variants": {}}
    for v in VARS:
        h = hz[v]
        n_f = fic["n_weeks_abg"]
        cv: dict = {}
        # Weg A* (raw IC, momentum direction) -> reversal direction (x -1)
        a_si = fic["S_r"]["small_illiquid"][h] / sx["small_illiquid"]
        a_ll = fic["S_r"]["large_liquid"][h] / sx["large_liquid"]
        a_br = (fic["S_r"]["breit_M1M_V100K"][h] / sx["small_illiquid"], fic["S_r"]["breit_M1M_V100K"][h] / sx["large_liquid"])
        a_ill = (fic["S_r"]["illiquide_M1M_Vlt100K"][h] / sx["small_illiquid"], fic["S_r"]["illiquide_M1M_Vlt100K"][h] / sx["large_liquid"])
        a_m10 = (fic["S_r"]["M10M_V1M"][h] / sx["small_illiquid"], fic["S_r"]["M10M_V1M"][h] / sx["large_liquid"])
        cv["weg_A_stern_roh_reversal_richtung"] = {
            "klein_illiquide": -a_si, "gross_liquide": -a_ll,
            "breit_M1M_V100K_band": sorted([-a_br[0], -a_br[1]]),
            "illiquide_V_lt_100K_band": sorted([-a_ill[0], -a_ill[1]]),
            "M10M_V1M_band": sorted([-a_m10[0], -a_m10[1]]),
            "hinweis": "Baender ohne eigene meanx: S_x der Gruppen klein/illiquide (0,609) und gross/liquide (0,414) als Klammer",
        }
        if v == "mom1":
            cv["weg_A_stern_roh_reversal_richtung"]["klein_illiquide_btc_alpha"] = -fic["btc_alpha_1W"]["small_illiquid"] / sx["small_illiquid"]
        # Weg B: (t / sqrt(N)) x SD(IC_t) with the programme's v6b null weekly SD (strict: the null SD understates the real SD)
        sdw = {wn: nuis["windows"][wn]["variants"][v]["sd_week"]["value"] for wn in WINS}
        t_si = fic["S_r"]["small_illiquid"]["t"][h]
        t_br = fic["S_r"]["breit_M1M_V100K"]["t"][h]
        t_ll = fic["S_r"]["large_liquid"]["t"][h]
        cv["weg_B_reversal_richtung"] = {
            "regel": "IC = (t / sqrt(N)) x sd_week_W,v (v6b-Null-Wochen-SD; Pilot-SD NICHT verwendet: wuerde den Prior pilotabhaengig machen)",
            "klein_illiquide": {wn: -(t_si / math.sqrt(n_f)) * sdw[wn] for wn in WINS},
            "breit_M1M_V100K": {wn: -(t_br / math.sqrt(n_f)) * sdw[wn] for wn in WINS},
            "gross_liquide": {wn: -(t_ll / math.sqrt(n_f)) * sdw[wn] for wn in WINS},
        }
        # LTW FM (equal weight, quintile number regressor): IC ~ b sqrt(2) / sigma_xs, sigma in (0.148, 0.182, 0.25)
        key = {"mom1": "r1", "mom2": "r2", "mom4": "r4"}[v]
        b1 = lit["ltw_nber_w25882"]["fm_gt_1mio"][key]
        cv["weg_FM_ltw_gt_1mio_reversal_richtung"] = {f"sigma_{s}": -(b1 * math.sqrt(2.0) / s) for s in (0.148, 0.182, 0.25)}
        cv["weg_B_ltw_fm_gt_1mio_reversal_richtung"] = {
            wn: -(lit["ltw_nber_w25882"]["fm_gt_1mio"]["t"][key] / math.sqrt(lit["ltw_nber_w25882"]["n_weeks_abg"])) * sdw[wn] for wn in WINS}
        # fm8 scale
        def f8(x):
            return x * FM8_DAMP + 0.0          # + 0.0 normalises a negative zero
        A = cv["weg_A_stern_roh_reversal_richtung"]
        cv["fm8_skala"] = {
            "faktor": FM8_DAMP, "faktor_hinweis": "mom1 synthetisch (power_h32.json fm8_daempfung); mom2/mom4 vermutlich staerker "
                                                  "gedaempft -> Werte dort Obergrenzen (Richtung Testbarkeit)",
            "R1_klein_illiquide_A_stern": f8(A["klein_illiquide"]),
            "R1_klein_illiquide_A_stern_rang": f8(A["klein_illiquide"]) * RANK_FACTOR,
            "R1b_klein_illiquide_B": {wn: f8(cv["weg_B_reversal_richtung"]["klein_illiquide"][wn]) for wn in WINS},
            "R2_illiquide_V_lt_100K_A_stern_band": [f8(x) for x in A["illiquide_V_lt_100K_band"]],
            "R3_breit_ficura_A_stern_band": [f8(x) for x in A["breit_M1M_V100K_band"]],
            "R3_breit_ficura_B": {wn: f8(cv["weg_B_reversal_richtung"]["breit_M1M_V100K"][wn]) for wn in WINS},
            "R3_breit_ltw_fm_band": sorted([f8(x) for x in cv["weg_FM_ltw_gt_1mio_reversal_richtung"].values()]),
            "R3_breit_ltw_fm_B": {wn: f8(cv["weg_B_ltw_fm_gt_1mio_reversal_richtung"][wn]) for wn in WINS},
            "R4_gross_liquide_A_stern": f8(A["gross_liquide"]),
            "R4_M10M_V1M_A_stern_band": [f8(x) for x in A["M10M_V1M_band"]],
            "R4_gross_liquide_B": {wn: f8(cv["weg_B_reversal_richtung"]["gross_liquide"][wn]) for wn in WINS},
        }
        conv["variants"][v] = cv

    # power at the literature readings (Lesart T and S)
    lit_power: dict = {}
    for les in ("T", "S"):
        lit_power[les] = {}
        for v in VARS:
            fm = conv["variants"][v]["fm8_skala"]
            pts = {"R1_A_stern": fm["R1_klein_illiquide_A_stern"], "R1_A_stern_rang": fm["R1_klein_illiquide_A_stern_rang"],
                   "R1b_B_W1sd": fm["R1b_klein_illiquide_B"]["W1"], "R3_ficura_breit_oben": fm["R3_breit_ficura_A_stern_band"][1],
                   "R3_ltw_fm_oben": fm["R3_breit_ltw_fm_band"][-1]}
            lit_power[les][v] = {}
            for name, pi in pts.items():
                if pi <= 0.0:
                    lit_power[les][v][name] = {"prior": pi, "regime_p1": "GL012", "hinweis": "Prior <= 0"}
                    continue
                pa = power_at(les, v, pi)
                lit_power[les][v][name] = {"prior": pi, "regime_p1": pa["regime_p1"], "joint_product": pa["joint_product"],
                                           "window_power": {wn: pa["window_power"][wn]["P_window"] for wn in WINS},
                                           "regime_a3_practice": pa["regime_a3_practice"],
                                           "end_power_m3_replicates": pa["end_power"]["3"]["replicates_lower_bound"]["joint"],
                                           "end_power_m14_replicates": pa["end_power"]["14"]["replicates_lower_bound"]["joint"]}

    # ------------------------------------------------------------------------------------------------------------
    # synthetic bounce fixture for mom1/mom2/mom4 (no data; size of the bid-ask artefact in the negative direction)
    # ------------------------------------------------------------------------------------------------------------
    def bounce_mom(n_weeks: int, n_sym: int, spread: float, sigma_true: float, trail: int, seed: int = 53) -> float:
        rng = np.random.default_rng(seed)
        true_log_ret = rng.normal(0.0, sigma_true, size=(n_weeks, n_sym))
        true_log_price = np.cumsum(true_log_ret, axis=0)
        side = rng.integers(0, 2, size=(n_weeks, n_sym))
        hs = math.log(1.0 + spread / 2.0)
        obs = true_log_price + np.where(side == 1, hs, -hs)
        ret = np.diff(obs, axis=0, prepend=obs[[0]])
        ret[0] = 0.0
        alive = np.ones((n_weeks, n_sym), dtype=bool)
        ch = characteristics.momentum_characteristic(ret, trail_win=trail)
        return float(ic.weekly_ic_series(ch, ret, alive, convention="close_at_last", min_universe=5)["mean_ic"])

    bounce: dict = {"spread": None, "windows": {}}
    d10 = [x for x in spread["deciles"] if x["decile"] == 10][0]["perp_spread_bp_median"]
    bounce["spread"] = round(d10 / 1e4, 6)
    for wn in WINS:
        w = d["windows"][wn]
        n_weeks = int(w["geometry"]["n_weeks"])
        k_med = max(int(np.median([w["k"]["median"]])), 10)
        sig = float(w["bounce_sigma_true"])
        bounce["windows"][wn] = {"n_weeks": n_weeks, "n_symbols": k_med, "sigma_true": sig,
                                 "ic_bounce_raw": {v: bounce_mom(n_weeks, k_med, bounce["spread"], sig, {"mom1": 1, "mom2": 2, "mom4": 4}[v])
                                                   for v in VARS}}
        bounce["windows"][wn]["ic_bounce_neg"] = {v: -x for v, x in bounce["windows"][wn]["ic_bounce_raw"].items()}
        bounce["windows"][wn]["verhaeltnis_zu_T_neg"] = {
            v: bounce["windows"][wn]["ic_bounce_neg"][v] / (Z * nuis["windows"][wn]["variants"][v]["e_se_rule"]["value"]) for v in VARS}
    bounce["hinweis"] = ("synthetisch (Logik wie wp13_xsec.run.bounce_fixture_ic, Charakteristik mom_n statt rev_gap; Spread = D10 des "
                         "WP-7-Spread-Zensus 36,21 bp, strengste Wahl), kein Datenbezug; K = Median der lebenden Symbole; "
                         "ic_bounce_* = EIN Seed (53) wie im H-32-Code")
    # multi-seed mean (seeds 53..252) and the analytic expectation: the single-seed value is sampling noise
    seeds = tuple(range(53, 253))
    for wn in WINS:
        bw = bounce["windows"][wn]
        h = math.log(1.0 + bounce["spread"] / 2.0)
        sig = bw["sigma_true"]
        bw["mehrseed_53_252"] = {}
        for v in VARS:
            n = {"mom1": 1, "mom2": 2, "mom4": 4}[v]
            vals = np.array([bounce_mom(bw["n_weeks"], bw["n_symbols"], bounce["spread"], sig, n, seed=s) for s in seeds])
            t_neg = Z * nuis["windows"][wn]["variants"][v]["e_se_rule"]["value"]
            bw["mehrseed_53_252"][v] = {
                "mean_raw": float(vals.mean()), "sd_single_seed_raw": float(vals.std(ddof=1)),
                "se_of_mean_raw": float(vals.std(ddof=1) / math.sqrt(vals.size)),
                "analytisch_pearson_raw": -h * h / (math.sqrt(n) * (sig * sig + 2.0 * h * h)),
                "anteil_seeds_abs_ge_T_neg": float(np.mean(np.abs(vals) >= t_neg)),
                "anteil_seeds_abs_ge_half_T_neg": float(np.mean(np.abs(vals) >= 0.5 * t_neg)),
            }
    bounce["mehrseed_hinweis"] = ("Mittel ueber 200 Seeds; analytisch: Cov(r_t, r_t+1) = -h^2, h = ln(1 + Spread/2), Var(r) = sigma^2 + 2 h^2, "
                                  "mom_n-Korrelation mit 1/sqrt(n) verduennt; anteil_seeds_abs_ge_T_neg = Wahrscheinlichkeit, dass der "
                                  "Ein-Seed-Bounce-Kill einen Effekt genau an der Schwelle T = z_krit x e_se_rule zufaellig toetet")

    # synthetic survivorship fixture (prelaunch.survivorship_drawdown_fixture logic, sized by the tradable K median and n_weeks;
    # the sizes K 417 / 526 reproduce the v6b mom1 AND rev_gap differences bit for bit -> mom2 / mom4 computed the same way)
    from bybit_edge.research.wp7_universe import pit_universe as pu

    def surv_fixture(n_weeks: int, k: int, char: str, seed: int = 53) -> float:
        rng = np.random.default_rng(seed)
        r = rng.normal(0.0, 0.05, size=(n_weeks, k))
        cum = characteristics.momentum_characteristic(r, trail_win=8)
        trg = []
        for j in range(k):
            idx = np.flatnonzero(cum[:, j] < -0.40)
            if idx.size:
                trg.append((j, int(idx[0])))
        trg.sort(key=lambda p: p[1])
        chosen = trg[: int(round(0.30 * k))]
        last = np.full(k, n_weeks - 1, dtype=np.int64)
        surv = np.ones(k, dtype=bool)
        for j, t in chosen:
            last[j] = min(t + 1, n_weeks - 1)
            surv[j] = False
        a_c = pu.pit_alive_mask(np.zeros(k, dtype=np.int64), last, n_weeks, min_weeks_history=0)
        a_u = np.ones((n_weeks, k), dtype=bool) & surv[None, :]
        if char == "rev_gap":
            ch = characteristics.reversal_gap_characteristic(r)
        else:
            ch = characteristics.momentum_characteristic(r, trail_win={"mom1": 1, "mom2": 2, "mom4": 4}[char])
        c = ic.weekly_ic_series(ch, r, a_c, convention="close_at_last")["mean_ic"]
        u = ic.weekly_ic_series(ch, r, a_u, convention="drop")["mean_ic"]
        return float(u - c)

    surv_k = {"W1": 417, "W2": 526}
    for wn in WINS:
        w = d["windows"][wn]
        nwk = int(w["geometry"]["n_weeks"])
        for chk in ("mom1", "rev_gap"):
            if surv_fixture(nwk, surv_k[wn], chk) != float(w["survivorship"][f"{chk}_diff"]):
                raise SystemExit(f"{wn}: survivorship fixture does not reproduce v6b {chk}_diff")
        checks.append(f"{wn}: Survivorship-Fixture mit K {surv_k[wn]}, {nwk} Wochen reproduziert v6b mom1_diff und rev_gap_diff bitgleich")
        for v in ("mom2", "mom4"):
            diff_raw = surv_fixture(nwk, surv_k[wn], v)
            t_neg = Z * nuis["windows"][wn]["variants"][v]["e_se_rule"]["value"]
            nuis["windows"][wn]["variants"][v]["survivorship"] = {
                "diff_raw_drop_minus_close_at_last": diff_raw, "diff_neg": -diff_raw, "t_neg": t_neg,
                "in_negativer_richtung_t_neg_einheiten": -diff_raw / t_neg,
                "herkunft": f"synthetisch neu gerechnet (Fixture wie prelaunch.survivorship_drawdown_fixture, K {surv_k[wn]}, {nwk} Wochen, "
                            "Seed 53; Groessen reproduzieren v6b mom1/rev_gap bitgleich); kein Datenbezug",
                "registrierbar_aus_v6b": "nein (nicht im Artefakt) - aber ohne Daten reproduzierbar; v7 friert es mit ein"}

    # spread census composition (counts and median spreads only)
    census = {"n_symbols": spread["n_symbols"], "deciles": spread["deciles"], "source": spread["source"],
              "sha256": hashes["spread_census"],
              "hinweis": "Umsatzdezile ohne USD-Umsatz: Zuordnung zu Ficura-Schwellen (Wochenvolumen 100 Tsd. / 5 Mio. USD, "
                         "Marktkap. 1/10/50 Mio. USD) nicht moeglich -> UNBELEGT"}

    sel = {"K": 3, "z_max_K3": power_p1.selection_z(3), "z_used": power_p1.effective_z(0.05, 3), "z_krit": Z,
           "by_threshold": {str(m): est.by_threshold(m) for m in M_GRID}, "bh_denominator": 3}
    kill = {}
    for wn in WINS:
        cz = nuis["windows"][wn]["ceiling_k3_neg"]
        kill[wn] = {}
        for v in VARS:
            t_neg = Z * nuis["windows"][wn]["variants"][v]["e_se_rule"]["value"] + max(0.0, nuis["windows"][wn]["variants"][v]["null_mean_neg"]["frozen_neg"])
            kill[wn][v] = {"T_frozen_neg": t_neg, "ceiling_raw_1000_over_T": cz["drifting_raw_1000"] / t_neg,
                           "ceiling_recentred_10000_over_T": cz["drifting_recentred_10000"] / t_neg}

    meta = {"schema": "H-33 Herleitung (outcome-frei)", "erstellt": "2026-10-26",
            "etikett_dec102_e2": "beschlossen nach Kenntnis von GL-035 (Pilot-Vorzeichen der mom-Varianten); Richtung Testbarkeit; "
                                 "Richtungswahl nach Kenntnis korrelierter Daten eines anderen Fensters (2022-04..2024-06)",
            "eingaben_sha256": hashes, "checks": checks, "z_krit": Z,
            "skript": {"pfad": "scratchpad/h33_herleitung/h33_compute.py (ausserhalb des Repos)",
                       "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "aufruf": "python3 -I h33_compute.py <repo> <out>; zweimal gerechnet, bitgleich"}, "z_power": ZP, "grid": list(GRID), "m_grid": list(M_GRID),
            "f2_real_gl035_lesart_S": F2_REAL, "c_real_gl035": C_REAL,
            "lesarten": {"T": "nur v6b-Null (SE_T = e_se_rule, SD_T = se_mean, k = 1)",
                         "S": "DEC-94 (5): groessere SE ueber v6b-Null und GL-035-Streuung (SE_W,Pilot = sqrt(c_real) sqrt(v_fm8 + F2_real) / "
                              "sqrt(W)), k_pred = max(1, sqrt(v_fm8 + F2_real) / sd_week)"},
            "q95_eff_vorlaeufig": "q95_eff(k) = k x dev95 der Drift-Zelle (Form der Drift-Zelle, eigenes Mittel); bindend nach v7: "
                                  "max(0, m) + k (q95_neg - m) mit q95_neg = max(q95_1000 beider Zellen, q95_10000 driftfrei), m = driftfreies Null-Mittel"}
    power_json = {"meta": meta, "selection": sel, "pre_verdict_kill": kill, "power_lines": power, "literatur": lit,
                  "umrechnung": conv, "power_an_literatur_lesarten": lit_power, "bounce_fixture_synthetisch": bounce,
                  "spread_zensus": census}
    nuis_json = {"meta": {"schema": "H-33 nuisance in negativer Richtung (aus v6b)", "erstellt": "2026-10-26",
                          "etikett_dec102_e2": meta["etikett_dec102_e2"], "eingaben_sha256": hashes, "checks": checks,
                          "regel": "y = -IC; null_mean_neg = -null_mean_raw; q95_neg = -Q_0.05(Rohreplikate); SD-Groessen richtungsfrei"},
                 "skript_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 "windows": nuis["windows"]}

    def dump(obj, path: Path):
        txt = json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False)
        path.write_text(txt + "\n", encoding="ascii")
        return hashlib.sha256((txt + "\n").encode("ascii")).hexdigest()

    OUT.mkdir(parents=True, exist_ok=True)
    h1 = dump(power_json, OUT / "power_h33.json")
    h2 = dump(nuis_json, OUT / "nuisance_neg.json")
    print("power_h33.json", h1)
    print("nuisance_neg.json", h2)


if __name__ == "__main__":
    main()
