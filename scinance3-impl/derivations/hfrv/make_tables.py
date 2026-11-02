"""Render markdown tables from nuisance_hfrv.json and a2_census.json (German decimal commas).
Writes scratchpad/hfrv_herleitung/tables.md (copied by hand into the case files)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path("/home/user/scinance/scinance3-impl/state/herleitung_hfrv")
V = ("v1_1min", "v2_5min", "v3_5min_sub", "v4_15min", "v5_30min", "v6_cc")
VT = {"v1_1min": "(i) 1-min", "v2_5min": "(ii) 5-min", "v3_5min_sub": "(iii) 5-min sub",
      "v4_15min": "(iv) 15-min", "v5_30min": "(v) 30-min", "v6_cc": "(vi) cc"}


def f(x, k=2):
    if x is None:
        return "-"
    if isinstance(x, str):
        return x
    s = f"{x:,.{k}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    j = json.loads((OUT / "nuisance_hfrv.json").read_text())
    L = []
    st = j["stats"]
    for leg in ("BTC", "ETH", "LEG_BTCETH"):
        for u, k in (("S1", 2), ("S2", 2), ("S3", 3)):
            L.append(f"\n### {leg} {u}\n")
            L.append("| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | "
                     "c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |")
            L.append("|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|")
            for v in V:
                s = st[leg][v][u]
                a = s["acf_out"]
                acfs = " / ".join(f(a[x], 3) for x in ("1", "10", "20", "30", "60", "120", "180"))
                cb = " / ".join(f(s["c_bartlett"][x], 1) for x in ("60", "90", "120"))
                cm = " / ".join(f(s["c_batch_means"][x], 1) for x in ("60", "90", "120"))
                cs = " / ".join(f(s["c_stationary_bootstrap"][x], 1) for x in ("30", "60", "90"))
                m = s["monthly"]
                L.append(f"| {VT[v]} | {s['n_contiguous_used']} ({s['n_finite']}) | {f(s['sd'], k)} | {acfs} | "
                         f"{s['first_lag_acf_below_0_10']} | {f(s['excess_kurtosis'], 2)} | {cb} | {cm} | {cs} | "
                         f"**{f(s['c_bind'], 2)}** | {f(s['c_consensus_tapered_acf'], 1)} | "
                         f"{f(m['sd_m'], k)} / {f(m['acf1'], 2)} / {f(m['c_bind_m'], 1)} |")
    L.append("\n### RV-Niveau, Signatur, kappa, Rauschen\n")
    L.append("| Symbol | Variante | rms RV_fwd30 % | /cc | /30-min | Niveau-Abw. VP | kappa L1 | kappa L2,3,5 (Review) | kappa L2..5 | Rausch-SD VP (Delta) | SD S1 | SD/SD_cc | SD rauschfrei (Delta) |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for s_ in ("BTC", "ETH"):
        for v in V:
            lv = j["rv_level"][s_][v]
            kp = j["kappa_rv_day"][s_][v]
            r = j["sd_ratios"][s_][v]
            L.append(f"| {s_} | {VT[v]} | {f(100*lv['rms_rv_fwd30'], 2)} | {f(lv['ratio_rms_to_cc'], 3)} | "
                     f"{f(lv['ratio_rms_to_30min'], 3)} | {f(lv['level_bias_volpts_vs_cc'], 2)} | {f(kp['1'], 2)} | "
                     f"{f(kp['kappa_L2_3_5_review'], 2)} | {f(kp['kappa_L2_5'], 2)} | {f(kp['sd_noise_volpts_delta'], 2)} | "
                     f"{f(r['sd_S1'], 2)} | {f(r['ratio_sd_to_cc_same_data'], 3)} | {f(r['sd_S1_noise_free_delta'], 2)} |")
    L.append("\n### Korrelationen\n")
    L.append("| Variante | Pearson BTC/ETH S1 / S2 / S3 | Spearman BTC/ETH S1 / S2 / S3 | Pearson HF vs cc BTC S1 | ETH S1 |")
    L.append("|---|---|---|---:|---:|")
    c = j["correlations"]
    for v in V:
        p = " / ".join(f(c["pearson_btc_eth"][v][u], 3) for u in ("S1", "S2", "S3"))
        sp = " / ".join(f(c["spearman_btc_eth"][v][u], 3) for u in ("S1", "S2", "S3"))
        L.append(f"| {VT[v]} | {p} | {sp} | {f(c['pearson_hf_vs_cc_same_symbol'][v]['BTC']['S1'], 3)} | "
                 f"{f(c['pearson_hf_vs_cc_same_symbol'][v]['ETH']['S1'], 3)} |")
    # power
    pw = j["power"]["BTC_S1"]
    L.append("\n### Fenster-SE und Zuordnung bei zwei Fenstern zu n IV-Tagen (BTC S1, pi-2 zentral 9,47)\n")
    L.append("| Variante | c | SE_null | SE n 335 (Quelle) | Power P-1 335 | Regime P-1 / A3 335 | SE n 365 | Power P-1 365 | Regime P-1 / A3 365 |")
    L.append("|---|---|---|---:|---:|---|---:|---:|---|")
    for v in V:
        for cn in ("c_rule_P3", "c_consensus_measured", "c_consensus_review_18_6"):
            for nn in ("se_null_h27", "nuisance_only"):
                w = pw[v][f"{cn}|{nn}"]["windows_L12"]["pi2_central"]
                a, b = w["335"], w["365"]
                L.append(f"| {VT[v]} | {cn} {f(pw[v]['c'][cn], 1)} | {nn} | {f(a['se'], 2)} ({a['binding_source']}) | "
                         f"{f(a['window_power_p1'], 3)} | {a['regime_p1']} / {a['regime_a3']} | {f(b['se'], 2)} | "
                         f"{f(b['window_power_p1'], 3)} | {b['regime_p1']} / {b['regime_a3']} |")
    L.append("\n### Tage je Fenster und Datum 'voll' (zwei Fenster ab 2026-07-01, RV-Ziel +30 Tage)\n")
    L.append("| Variante | c | SE_null | Prior | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 (3,168) | voll C10 P-1 | voll DEC-52 P-1 | voll C10 A3 |")
    L.append("|---|---|---|---|---:|---:|---:|---:|---|---|---|")
    for v in V:
        for cn in ("c_rule_P3", "c_consensus_measured", "c_consensus_review_18_6"):
            for nn in ("se_null_h27", "nuisance_only"):
                for pn in ("pi2_central", "pi2_low", "pi2_high", "pi1", "dec98n2_pi2_7_14", "dec98n2_qdensity_3_16",
                           "pi2_central_at_variant_level", "pi2_central_cc_literature_level_bias"):
                    if nn == "nuisance_only" and pn not in ("pi2_central",):
                        continue
                    if cn == "c_consensus_review_18_6" and pn not in ("pi2_central",):
                        continue
                    d = pw[v][f"{cn}|{nn}"]["durations"][pn]
                    dd = d["days"]
                    if dd is None:
                        continue
                    L.append(f"| {VT[v]} | {cn} {f(d['c'], 1)} | {nn} | {pn} {f(d['prior'], 2)} | {f(dd['c10_p1'], 1)} | "
                             f"{f(dd['dec52_gate_p1'], 1)} | {f(dd['c10_a3'], 1)} | {f(dd['dec52_gate_a3_3168'], 1)} | "
                             f"{d['full_c10_p1']} | {d['full_dec52_gate_p1']} | {d['full_c10_a3']} |")
    L.append("\n### Bericht: S3/S2/ETH/Bein (c Regel bzw. Konsens, SE_null H-27, pi-2 zentral)\n")
    L.append("| Variante | Konfiguration | c | SD | Prior | C10 P-1 Tage | voll | C10 A3 Tage | voll A3 |")
    L.append("|---|---|---|---:|---:|---:|---|---:|---|")
    for v in V:
        rep = j["power"]["report"][v]
        for lab in ("BTC_S3", "BTC_S2", "ETH_S1", "LEG_S1"):
            for cn in ("c_rule", "c_consensus_measured"):
                d = rep[lab][cn]
                L.append(f"| {VT[v]} | {lab} | {cn} {f(d['c'], 1)} | {f(d['sd'], 3)} | {f(d['prior'], 3)} | "
                         f"{f(d['days']['c10_p1'], 1)} | {d['full_c10_p1']} | {f(d['days']['c10_a3'], 1)} | {d['full_c10_a3']} |")
        for cn in ("c_rule", "c_consensus_measured"):
            d = rep[f"conjunction_BTC_and_ETH_{cn}"]
            L.append(f"| {VT[v]} | Konjunktion BTC+ETH | {cn} | - | - | {f(d['c10_p1_days'], 1)} | {d['full_c10_p1']} | - | - |")
    (HERE / "tables.md").write_text("\n".join(L) + "\n")
    print("tables.md written", len(L))


if __name__ == "__main__":
    main()
