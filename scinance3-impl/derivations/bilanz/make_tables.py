"""Render markdown tables (German decimal comma, ASCII) from programm_bilanz.json."""
import json
import math
from pathlib import Path

D = json.loads(Path("/home/user/scinance/scinance3-impl/state/programm_bilanz.json").read_text())
OUT = Path(__file__).resolve().parent / "tables.md"
L: list[str] = []


def f(x, k=1):
    if x is None:
        return "-"
    return f"{x:.{k}f}".replace(".", ",")


def c(x):
    return "-" if x is None else str(int(math.ceil(x - 1e-9)))


# ---------------- A3 nuisance table
L.append("### A3 Nuisance")
L.append("| Fenster-Basis | Kalibrierung | Variante | SD(IC_t) roh | c_hat (Null) | SD fm8 | c_hat fm8 | Boden E[1/sqrt(K-1)] | K min/Median/max |")
L.append("|---|---|---|---:|---:|---:|---:|---:|---|")
for W in ("W1", "W2"):
    w = D["A3"]["windows"][W]
    for cal in ("measured", "stress"):
        for v in ("mom1", "rev_gap"):
            a = w["cells"][f"{cal}|{v}|none"]
            b = w["cells"][f"{cal}|{v}|fm_neutral_8w"]
            L.append(f"| {W} | {cal} | {v} | {f(a['factor_sd'],4)} | {f(a['c_hat_null'],3)} | {f(b['factor_sd'],4)} | "
                     f"{f(b['c_hat_null'],3)} | {f(w['e_floor'],4)} | {w['K_min']}/{f(w['K_median'],0)}/{w['K_max']} |")

L.append("\n### A3 Dauer (Roh-IC, c = max(1, c_hat))")
L.append("| Basis | Variante | Wochen je Fenster C10 P-1 | DEC-52-Gate P-1 | C10 A3-Praxis | DEC-52 A3 (3,168) | voll (C10 P-1) | voll (A3-Praxis) | mit c = 1: C10 P-1 / A3 |")
L.append("|---|---|---:|---:|---:|---:|---|---|---|")
for W in ("W1", "W2"):
    w = D["A3"]["windows"][W]
    for cal in ("stress", "measured"):
        for v in ("mom1", "rev_gap"):
            a = w["cells"][f"{cal}|{v}|none"]
            dd, d1, fd = a["dur_c"], a["dur_c1"], a["full_dates_c"]
            L.append(f"| {W}-{cal} | {v} | {f(dd['c10_p1'])} | {f(dd['dec52_gate_p1'])} | {f(dd['c10_a3'])} | "
                     f"{f(dd['dec52_gate_a3_3168'])} | {fd['c10_p1']} | {fd['c10_a3']} | {f(d1['c10_p1'])} / {f(d1['c10_a3'])} |")

L.append("\n### A3 fm8 (neue Hypothese, Option)")
L.append("| Basis | Variante | SD fm8 | c | Wochen C10 P-1 | C10 A3-Praxis | voll P-1 | voll A3 |")
L.append("|---|---|---:|---:|---:|---:|---|---|")
for W in ("W1", "W2"):
    w = D["A3"]["windows"][W]
    for cal in ("stress", "measured"):
        for v in ("mom1", "rev_gap"):
            a = w["cells"][f"{cal}|{v}|fm_neutral_8w"]
            dd, fd = a["dur_c"], a["full_dates_c"]
            L.append(f"| {W}-{cal} | {v} | {f(a['sd_used'],4)} | {f(a['c_used'],3)} | {f(dd['c10_p1'])} | {f(dd['c10_a3'])} | {fd['c10_p1']} | {fd['c10_a3']} |")

L.append("\n### A3 Breite (Roh-IC, mom1)")
L.append("| Basis | Faktor-Anteil F | K wie gemessen | 2 K | 4 K | K -> unendlich | Gewinn max. |")
L.append("|---|---:|---:|---:|---:|---:|---:|")
for W in ("W1", "W2"):
    w = D["A3"]["windows"][W]
    for cal in ("stress", "measured"):
        a = w["cells"][f"{cal}|mom1|none"]
        bl = a["breadth_lever"]
        lv = bl["levels"]
        gain = 1 - lv["K_inf"]["c10_p1"] / lv["K_x1"]["c10_p1"]
        L.append(f"| {W}-{cal} | {f(bl['factor_component_sd'],4)} | {f(lv['K_x1']['c10_p1'])} | {f(lv['K_x2']['c10_p1'])} | "
                 f"{f(lv['K_x4']['c10_p1'])} | {f(lv['K_inf']['c10_p1'])} | -{f(100*gain,0)} % |")

L.append("\n### A3 Prior-Sensitivitaet W1-stress mom1")
for p, v in D["A3"]["prior_sensitivitaet_W1_stress_mom1"].items():
    L.append(f"- prior {p}: C10 P-1 {f(v['c10_p1'])} / A3 {f(v['c10_a3'])} Wochen")
L.append("\n### A3 Selektions-K")
for k, v in D["A3"]["selektions_K_W1_stress_mom1"].items():
    L.append(f"- K {k}: z_eff {f(v['z_eff'],4)} (z_max {f(v['selection_z'],4)}): {f(v['c10_weeks'])} Wochen")
L.append("\n### A3 historisch (Bericht)")
for k, v in D["A3"]["historisch_W1_W2_bericht"].items():
    L.append(f"- {k}: P-1 {v['p1_regime']} (Fenster {f(v['p1_window_power'][0],3)}/{f(v['p1_window_power'][1],3)}, Gate {f(v['p1_gate_product'],3)}); A3 {v['a3_regime']} ({f(v['a3_window_power'][0],3)}/{f(v['a3_window_power'][1],3)})")

# ---------------- A1
A1 = D["A1"]
L.append("\n### A1 Dauer (SD 372,9 bindend; Wochen je Fenster)")
L.append("| Spread-Annahme (bp/Woche) | theta | prem (bp) | c | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 | voll C10 P-1 | voll A3 |")
L.append("|---|---:|---:|---|---:|---:|---:|---:|---|---|")
for sk in ("nuisance_2022_04_2024_06", "W1", "W2_ohne_1h", "W2"):
    for th in (1.0, 0.77, 0.5):
        for ck in ("c1_P1", "c_DEC67_E4"):
            g = A1["grid"][f"{sk}|theta={th}|W1_projektion_bindend|{ck}"]
            dd = g["dur"]
            L.append(f"| {sk} ({f(A1['spreads_bp'][sk])}) | {f(th,2)} | {f(g['prem_bp'])} | {'1' if ck=='c1_P1' else '2,439 (E4)'} | "
                     f"{f(dd['c10_p1'])} | {f(dd['dec52_gate_p1'])} | {f(dd['c10_a3'])} | {f(dd['dec52_gate_a3_3168'])} | {g['full_c10_p1']} | {g['full_c10_a3']} |")
L.append("\n### A1 SD 354,5 (P1 direkt) Vergleich theta 1, W1-Spread, c 1")
g = A1["grid"]["W1|theta=1.0|P1_nuisance_direkt|c1_P1"]
L.append(f"- C10 P-1 {f(g['dur']['c10_p1'])} Wochen, voll {g['full_c10_p1']}")
L.append("\n### A1 historisch")
for k, v in A1["historisch_W1_W2_bericht"].items():
    L.append(f"- {k}: P-1 {v['p1_regime']} (Fenster {f(v['p1_window_power'][0],3)}/{f(v['p1_window_power'][1],3)}, Gate {f(v['p1_gate_product'],3)}), A3 {v['a3_regime']}, theta_min P-1 {f(v['theta_min_p1'],3)}")
L.append("\n### A1 ungleiche Fenster")
for k, v in A1["ungleiche_fenster_W1_dann_W2"].items():
    L.append(f"- {k}: priors {f(v['priors'][0])}/{f(v['priors'][1])}: C10 P-1 {f(v['c10_p1'])}, admit P-1 (DEC52) {f(v['admit_p1'])}, C10 A3 {f(v['c10_a3'])}, A3 mit DEC52 {f(v['admit_a3_with_dec52'])}")
h = A1["hedge_hebel_dauer_theta1_W1"]
L.append(f"\n- Hedge: SD-Verhaeltnis {f(h['sd_ratio'],3)}: C10 P-1 {f(h['ohne']['c10_p1'])} -> {f(h['mit']['c10_p1'])}; A3 {f(h['ohne']['c10_a3'])} -> {f(h['mit']['c10_a3'])}")

# ---------------- H27
H = D["H27"]
L.append("\n### H-27 / VRP Dauer (Tage je Fenster)")
L.append("| Konfiguration | SD | c | Prior | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 | voll C10 P-1 | voll DEC-52 P-1 | voll A3 |")
L.append("|---|---:|---:|---|---:|---:|---:|---:|---|---|---|")
names = {"ref_daily_cc_c_bind": "Referenz (Tagesschluss, c Regel P-3)",
         "daily_cc_c_konsens": "Tagesschluss, Konsens-c",
         "hf_rv_c_bind": "HF-RV (UNBELEGT), c Regel",
         "hf_rv_c_konsens": "HF-RV (UNBELEGT), Konsens-c",
         "leg_mean_btc_eth": "Bein BTC+ETH (Tagesmittel)"}
for ck, nm in names.items():
    for pk in ("pi2_central", "pi2_low", "pi2_high", "pi1"):
        v = H["configs"][f"{ck}|{pk}"]
        dd = v["dur"]
        L.append(f"| {nm} | {f(v['sd'],1)} | {f(v['c'],1)} | {pk} {f(v['prior'],2)} | {f(dd['c10_p1'])} | {f(dd['dec52_gate_p1'])} | "
                 f"{f(dd['c10_a3'])} | {f(dd['dec52_gate_a3_3168'])} | {v['full_c10_p1']} | {v['full_dec52_gate_p1']} | {v['full_c10_a3']} |")
m = H["monatsziele_nicht_ueberlappend"]
L.append(f"\n- Monatsziele: pi2 zentral C10 P-1 {f(m['pi2_central']['dur_months']['c10_p1'])} Monate = {f(m['pi2_central']['c10_p1_days'])} Tage, voll {m['pi2_central']['full_c10_p1']}; A3 {f(m['pi2_central']['dur_months']['c10_a3'])} Monate; Power 12 M {f(m['pi2_central']['power_12m_p1'],3)} gegen ueberlappend {f(m['overlap_power_12m_p1'],3)}")
for k, v in H["zwei_beine_theorie"].items():
    L.append(f"- zwei Beine {k}: Varianzfaktor {f(v['varianzfaktor'],3)}: C10 P-1 {f(v['dur']['c10_p1'])} Tage / A3 {f(v['dur']['c10_a3'])}")

# ---------------- A2
A2 = D["A2"]
L.append("\n### A2 (Arbeitswerte)")
L.append("| Verfallsmenge | Laenge je Fenster | N je Fenster | SE Ereignis | SE Placebo | SE(Delta) | MDE80 P-1 | MDE80 A3-Praxis | Prior | Power P-1 | Regime P-1 / A3 |")
L.append("|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|")
for k, v in A2["rows"].items():
    lab, yrs = k.split("|")
    L.append(f"| {lab} | {yrs} | {v['N_je_Fenster']} | {f(v['se_event'],2)} | {f(v['se_placebo'],2)} | {f(v['se_delta'],2)} | {f(v['mde80_p1'],1)} | {f(v['mde80_a3'],1)} | "
             f"{'16,5 [sek]' if 'prior_sek' in v else 'UNBELEGT'} | {f(v.get('power_p1'),3) if 'power_p1' in v else '-'} | {(v['regime_p1'] + ' / ' + v['regime_a3']) if 'regime_p1' in v else '-'} |")
mm = A2["monatlich_prior_16_5_jahre_je_fenster"]
L.append(f"\n- monatlich, Prior 16,5: Jahre je Fenster C10 P-1 {f(mm['c10_p1'],2)} / A3 {f(mm['c10_a3'],2)}")
for k, v in A2["N_je_Fenster_nach_prior_durch_sigma30"].items():
    L.append(f"- prior/sigma30 = {k}: N_C10 P-1 {f(v['N_c10_p1'])} / A3 {f(v['N_c10_a3'])} Ereignisse je Fenster (ohne Placebo)")

# ---------------- A4
A4 = D["A4"]
L.append("\n### A4")
for k, v in A4["N_je_Fenster_nach_prior_durch_sigma_w"].items():
    L.append(f"- prior/sigma_w = {k}: N_C10 P-1 {f(v['N_c10_p1'])}, DEC-52 {f(v['N_dec52_gate_p1'])}, A3 {f(v['N_c10_a3'])} Zyklen je Fenster")
L.append(f"- MDE80 4 Zyklen {f(A4['mde80_4_zyklen_in_sigma_w'],3)} sigma_w; 8 Zyklen {f(A4['mde80_8_zyklen_in_sigma_w'],3)}; Verfaelle {A4['quartalsverfaelle_ab_registrierung']}")

# ---------------- options
L.append("\n### Regel-Optionen")
L.append("| Option | Daten (gesamt, relativ) | Fehlerrate gemeinsam | Power gemeinsam am Prior | Richtung |")
L.append("|---|---:|---:|---:|---|")
for k, v in D["regel_optionen"].items():
    L.append(f"| {k}: {v['label']} | {f(v['daten_faktor_gesamt'],3)} | {v['fp_gemeinsam']:.2e} | {f(v['power_gemeinsam_am_prior'],2)} | {v['richtung']} |")
L.append("\n| Option | A3 Roh-IC W1-stress mom1 | A3-fm8 W1-stress mom1 | A1 theta 1 W1-Spread | VRP Referenz |")
L.append("|---|---|---|---|---|")
rows = D["regel_optionen_je_kandidat"]
for ok in rows["H27_ref"]:
    cells = []
    for ck in ("A3_W1_stress_mom1", "A3_fm8_W1_stress_mom1", "A1_W1spread_theta1_c1", "H27_ref"):
        v = rows[ck][ok]
        cells.append(f"{v['fenster']} x {f(v['n_je_fenster'])} -> {v['voll']}")
    L.append(f"| {ok} | " + " | ".join(cells) + " |")

OUT.write_text("\n".join(L) + "\n", encoding="ascii")
print("wrote", OUT)
