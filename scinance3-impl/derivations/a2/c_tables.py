"""Render the Markdown tables of NULL_SIMULATION_A2.md / PILOT_ROUTE_A2.md from the JSON (helper; no data access).
Rounding: SE / SD / quantile distances two decimals, MDE80 and thresholds one decimal, powers two to four decimals.
Fassung 2: class dispersion as {series, n, sd} (R-C12a), scaled test null (R-C13), stress binding (R-C14), Gate-(4)
factor (R-C15), PK criterion (R-C16), funding pre-period/W1/W2 (R-C18).
Usage: python3 c_tables.py [path-to-a2_teilC.json | work]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_common as cc  # noqa: E402


def f(x, d=2):
    if x is None:
        return "-"
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pw(x):
    return f(x, 3) if x < 0.01 else f(x, 2)


def load(arg: str | None):
    if arg and arg != "work":
        j = json.loads(Path(arg).read_text(encoding="ascii"))
        return j["teil_C1"], j.get("teil_C2"), j.get("teil_C3")
    w = cc.WORK
    rd = lambda n: json.loads((w / n).read_text(encoding="ascii")) if (w / n).exists() else None  # noqa: E731
    return rd("c1.json"), rd("c2.json"), rd("c3.json")


def t_pre(c1):
    print("\n### T1 Null J-(i) je Vorperioden-Fenster (P2''-Kontrast, Cluster x, bp)\n")
    print("| Fenster | N_E / N_P'' | Wochen permutierbar (n_w) | Null-SD MC / exakt | d95 reg. [MC-95-%-Band] | d99 reg. | "
          "d95 / d99 Gegenrichtung | tau95 = d95/SD | Exzess-Kurtosis MC / exakt | Schiefe exakt | sigma_within | "
          "SD der Null-Verschiebung (iid, aus sigma_within) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, v in c1["pre_windows"].items():
        s, nb = v["structure"], v["null_P2ss"]
        hist = ", ".join(f"{a}:{b}" for a, b in s["n_w_hist"].items())
        print(f"| {k} | {s['W_event']} / {s['N_P2ss']} | {s['weeks_permutable']} ({hist}) | {f(nb['sd_mc'])} / {f(nb['sd_exact'])} | "
              f"{f(nb['d95_reg'])} [{f(nb['d95_reg_ci95_mc'][0])}; {f(nb['d95_reg_ci95_mc'][1])}] | {f(nb['d99_reg'])} | "
              f"{f(nb['d95_other'])} / {f(nb['d99_other'])} | {f(nb['tail_factor_95_reg'], 3)} | "
              f"{f(nb['excess_kurtosis_mc'], 3)} / {f(nb['excess_kurtosis_exact'], 3)} | {f(nb['skew_exact'], 3)} | "
              f"{f(v['sigma_within_cluster_pre'])} | {f(v['sd_null_shift_iid_sigma_within'])} |")
    print("\n### T2 Null-SD gegen analytische SE je Vorperioden-Fenster, bindende SE (DEC-94 (5)), Schwellen-Term "
          "(unskaliert / skaliert R-C13)\n")
    print("| Fenster | Bedingung | SD Klasse E / Placebo (Reihe) | SE analytisch c_bind / c=1 | SE Teil-B-Art (VP-SD, Fenster-N) | "
          "Null-SD (P3: N_P/(N_P+W) x) | Null/analytisch | SE_bind (Quelle) | z_krit x SE_bind | d95 reg. | "
          "k x d95 (R-C13) | bindender Term unskaliert / skaliert |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, v in c1["pre_windows"].items():
        cd = v["class_dispersion"]
        for j in ("P2ss", "P3fix", "P3all"):
            b = v["binding"][j]
            if j == "P2ss":
                d95, sc = b["d95_reg"], b["scaled_null_R_C13"]
                kd, term = f(sc["q95_eff_term"]), f"{b['threshold_binding_term']} / {sc['binding_term']}"
            else:
                d95, kd, term = b["null_d95_reg_equiv"], "-", "z_krit x SE (Null-Bed. = P2'')"
            print(f"| {k} | {j} | {f(cd['E']['sd'])} / {f(cd[j]['sd'])} ({cd[j]['series']}) | {f(b['se_analytic'])} / "
                  f"{f(b['se_analytic_c1'])} | {f(v['se_analytic_vp_sd'][j])} | {f(b['null_sd'])} | "
                  f"{f(b['ratio_null_to_analytic'], 3)} | {f(b['se_bind'])} ({b['se_bind_source']}) | {f(b['z_se_bind'])} | "
                  f"{f(d95)} | {kd} | {term} |")


def t_test(c1):
    tr = c1["transfer"]
    print(f"\nTransfer: sigma_within gepoolt {f(tr['sigma_within_pre_pooled'])}, Stress ({tr['stress_window_binding_R_C14']}, "
          f"bindend nach R-C14) {f(tr['sigma_within_stress'])}; tau95 = {f(tr['tail_factor_95_reg_max_V'], 4)}, "
          f"tau99 = {f(tr['tail_factor_99_reg_max_V'], 4)}")
    print("\n### T3 Struktur der Testfenster und bindende SE je Bedingung (stress bindend, zentral Bericht)\n")
    print("| Fenster / Linie | N_E / N_P'' / N_P3fix / N_P3all | Wochen perm. / fix | kappa | SE_bind P2'' / P3fix / P3all | "
          "groesster SE | Null-SD / d95 | k (R-C13) | SD Null-Verschiebung | Schwelle P2'': z SE / d95 / k d95 | bindend unskaliert / skaliert |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for w, t in c1["test_windows"].items():
        for line in ("stress", "zentral"):
            L, n, s = t["lines"][line], t["counts"], t["structure"]
            sb, th = L["se_bind"], L["threshold_P2ss"]
            print(f"| {w} {line} | {n['E']} / {n['P2ss']} / {n['P3fix']} / {n['P3all']} | {s['weeks_permutable']} / "
                  f"{s['weeks_fixed_event_only_friday']} | {f(L['kappa_efficiency'], 3)} | {f(sb['P2ss'])} / {f(sb['P3fix'])} / "
                  f"{f(sb['P3all'])} | {L['largest_se_condition']} | {f(L['null_sd_transfer'])} / {f(L['null_d95_transfer'])} | "
                  f"{f(L['k_scale_R_C13'], 3)} | {f(L['sd_null_shift_iid_sigma_within'])} | {f(th['z_krit_se'])} / "
                  f"{f(th['null_term_unscaled_d95'])} / {f(th['null_term_scaled_k_d95'])} | {th['binding_unscaled']} / "
                  f"{th['binding_scaled']} |")
    print("\n### T4 MDE80 neu (P-1, bp, Ereignis-Skala; W1 / W2)\n")
    print("| Linie | Einzel max (bindende Bed.) | Produkt nur z | Produkt unskaliert (Fassung 1) | Produkt skaliert (a)+(b) | "
          "**Produkt skaliert x Gate (4) (bindend, vorlaeufig)** | bivariat exakt (Bericht): skaliert W1 / W2 // unskaliert W1 / W2 | "
          "gemeinsam skaliert x Gate (4) (Bericht) | A3-Praxis |")
    print("|---|---|---|---|---|---|---|---|---|")
    for line in ("stress", "zentral"):
        for lab in ("unabgeschwaecht", "oi_0842"):
            a = [c1["test_windows"][w]["lines"][line][f"mde80_event_scale_{lab}"] for w in ("W1", "W2")]

            def two(key, d=1):
                return f"{f(a[0][key], d)} / {f(a[1][key], d)}"
            print(f"| {line}, {lab} | {two('single_max_over_conditions_scaled')} ({a[0]['single_binding_condition']} / "
                  f"{a[1]['single_binding_condition']}) | {two('product_z_only')} | {two('product_unscaled_fassung1')} | "
                  f"{two('product_scaled')} | **{two('product_scaled_gate4_bindend_vorlaeufig')}** | "
                  f"{two('product_bivariate_scaled_bericht')} // {two('product_bivariate_unscaled_bericht')} | "
                  f"{two('joint_scaled_gate4_bericht')} | {two('product_scaled_gate4_a3_practice')} |")
    print("\n### T5 Einzel-MDE80 je Bedingung (Kontrast-Skala; W1 / W2)\n")
    print("| Linie | z P2'' | Null P2'' unskaliert (Fassung 1) | Null P2'' skaliert (R-C13) | z P3fix | z P3all |")
    print("|---|---|---|---|---|---|")
    for line in ("stress", "zentral"):
        a = [c1["test_windows"][w]["lines"][line]["mde80_single_by_condition_contrast_scale"] for w in ("W1", "W2")]
        print(f"| {line} | " + " | ".join(f"{f(a[0][k], 1)} / {f(a[1][k], 1)}" for k in
                                         ("z_P2ss", "null_P2ss_unscaled_fassung1", "null_P2ss_scaled", "z_P3fix", "z_P3all")) + " |")
    print("\n### T6 Prior-Gitter: Produkt-Power (skaliert x Gate (4)) W1 / W2, gemeinsam (Bericht), Regime nach Produkt\n")
    print("| Prior (bp) | stress: Produkt W1 / W2 | Regime | zentral: Produkt W1 / W2 | gemeinsam W1 / W2 | Regime | "
          "stress OI 0,842: Produkt W1 / W2 | Regime |")
    print("|---|---|---|---|---|---|---|---|")
    for pr in c1["priors_bp"]:
        def g(line, lab):
            return [c1["test_windows"][w]["lines"][line][f"prior_grid_{lab}"][str(pr)] for w in ("W1", "W2")]
        s_, z_, o_ = g("stress", "unabgeschwaecht"), g("zentral", "unabgeschwaecht"), g("stress", "oi_0842")
        rg = lambda key: c1["regimes"][key][str(pr)]["regime_by_product"]  # noqa: E731
        print(f"| {f(pr, 1)} | {pw(s_[0]['product_scaled_gate4'])} / {pw(s_[1]['product_scaled_gate4'])} | "
              f"{rg('stress|unabgeschwaecht')} | {pw(z_[0]['product_scaled_gate4'])} / {pw(z_[1]['product_scaled_gate4'])} | "
              f"{pw(z_[0]['joint_scaled_gate4_bericht'])} / {pw(z_[1]['joint_scaled_gate4_bericht'])} | "
              f"{rg('zentral|unabgeschwaecht')} | {pw(o_[0]['product_scaled_gate4'])} / {pw(o_[1]['product_scaled_gate4'])} | "
              f"{rg('stress|oi_0842')} |")
    print("\n### T6a W2-Gabelungen F-1 / F-3 / F-4 (Produkt-MDE80, Ereignis-Skala, unabgeschwaecht)\n")
    print("| Linie | Gabelung | N_E / N_P'' | kappa | SE_bind P2'' / P3fix / P3all | skaliert x Gate (4) | skaliert | "
          "unskaliert (Fassung 1) |")
    print("|---|---|---|---|---|---|---|---|")
    for line, fk in c1["test_windows"]["W2"]["forks"].items():
        for name, x in fk.items():
            sb = x["se_bind"]
            print(f"| {line} | {name} | {x['counts']['E']} / {x['counts']['P2ss']} | {f(x['kappa_efficiency'], 3)} | "
                  f"{f(sb['P2ss'])} / {f(sb['P3fix'])} / {f(sb['P3all'])} | {f(x['product_scaled_gate4_unabgeschwaecht'], 1)} | "
                  f"{f(x['product_scaled_unabgeschwaecht'], 1)} | {f(x['product_unscaled_fassung1_unabgeschwaecht'], 1)} |")


def t_c2(c2):
    print("\n### T7 Funding-Zeitstempel je Periode und Symbol\n")
    print("| Periode | Symbol | Tage | Tage ohne Zeitstempel | Zeitstempel | Tage 8h (00/08/16) | Anteil 8h | Nicht-8h-Tage |")
    print("|---|---|---|---|---|---|---|---|")
    for p, v in c2["periods"].items():
        for s, x in v["per_symbol"].items():
            print(f"| {p} | {s} | {x['days']} | {x['days_without_timestamp']} | {x['timestamps']} | {x['days_8h']} | "
                  f"{f(x['share_days_8h'], 4)} | {x['n_days_not_8h']} |")
    print("\n### T8 Funding um 08:00 in Ereignis- und Placebo-Menge (beide Symbole) und Schutzregel G-C8\n")
    print("| Periode | Menge | Tage | 08:00 in beiden Symbolen | 8h-Muster in beiden | Termin in [07:00, 08:00) BTC / ETH | Tage von G-C8 betroffen |")
    print("|---|---|---|---|---|---|---|")
    for p, v in c2["periods"].items():
        for nm, bb in v["both_symbols"].items():
            b = v["per_symbol"]["BTCUSDT"]["share_by_set"][nm]
            e = v["per_symbol"]["ETHUSDT"]["share_by_set"][nm]
            print(f"| {p} | {nm} | {bb['n_days']} | {bb['days_funding_0800_both']} ({f(bb['share_0800_both'], 4)}) | "
                  f"{bb['days_8h_both']} | {b['days_with_funding_in_0700_0800']} / {e['days_with_funding_in_0700_0800']} | "
                  f"{bb['days_hit_by_protective_rule_G_C8']} |")


def t_c3(c3):
    print("\n### T10 Pilot-Schwelle c_A2 (Kontrast-Skala, bp): Regel R0 und Varianten\n")
    print("| Linie | Variante | MDE80prod W1 | MDE80prod W2 | c_A2 (max_W) | bindendes Fenster |")
    print("|---|---|---|---|---|---|")
    for line in ("stress", "zentral"):
        for k, v in c3["thresholds"][line].items():
            if "mde80_prod_by_window" in v:
                m = v["mde80_prod_by_window"]
                print(f"| {line} | {k} | {f(m['W1'], 1)} | {f(m['W2'], 1)} | {f(v['c_A2'], 1)} | {v['binding_window']} |")
        oi = c3["thresholds"][line]["lesart_OI_0842"]
        kp = c3["thresholds"][line]["k_pred_by_window_pre_pilot"]
        print(f"| {line} | lesart_OI_0842: Ereignis-Skala W1 / W2; Schwelle auf x_P = 0,842 x max | "
              f"{f(oi['event_scale_by_window']['W1'], 1)} | {f(oi['event_scale_by_window']['W2'], 1)} | "
              f"{f(oi['threshold_on_pilot_contrast'], 1)} (auf x_P) | - |")
        print(f"| {line} | k_pred,W vor dem Pilot (SE_T,W / Null-SD_W) | {f(kp['W1'], 3)} | {f(kp['W2'], 3)} | - | - |")
    print("\n### T11 Power der Pilotstufe (Uebergabe-Wahrscheinlichkeit) und Zwei-Stufen-Power gegen das Prior-Gitter\n")
    print("| Prior (bp) | Kontrast: R0 stress (bindend) | R0 zentral | R5 stress | Fassung 1 | Zwei-Stufen R0 stress / zentral | "
          "Ereignis 0,842: R0 stress | R0 zentral | R5 stress | Fassung 1 | Zwei-Stufen R0 stress / zentral |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for pr, row in sorted(c3["pilot_power_grid"].items(), key=lambda kv: float(kv[0])):
        cells = []
        for sc in ("kontrast_skala", "ereignis_skala_oi_0842"):
            cells += [f(row[f"{sc}|stress"]["pilot_handover_power"], 4), f(row[f"{sc}|zentral"]["pilot_handover_power"], 4),
                      f(row[f"{sc}|R5_stress"]["pilot_handover_power"], 4),
                      f(row[f"{sc}|fassung1_zentral"]["pilot_handover_power"], 4),
                      f"{f(row[f'{sc}|stress']['two_stage_power_product'], 4)} / "
                      f"{f(row[f'{sc}|zentral']['two_stage_power_product'], 4)}"]
        print(f"| {f(float(pr), 1)} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    c1, c2, c3 = load(sys.argv[1] if len(sys.argv) > 1 else None)
    t_pre(c1)
    t_test(c1)
    t_c2(c2)
    t_c3(c3)
