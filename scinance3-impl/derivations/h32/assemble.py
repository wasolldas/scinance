"""Assemble power_h32.json (deterministic): power numbers (h32_power.py), synthetic sector/power check
(sector_check.py), script hashes and a short summary block. Sorted keys, 6 significant digits.

Usage: python3 assemble.py <scratch_dir> <out_json>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

SCRATCH, OUT = sys.argv[1], sys.argv[2]


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def r6(x):
    if isinstance(x, float):
        return float(f"{x:.6g}")
    if isinstance(x, dict):
        return {k: r6(v) for k, v in x.items()}
    if isinstance(x, list):
        return [r6(v) for v in x]
    return x


pw = json.load(open(os.path.join(SCRATCH, "out_power.json")))
sc = json.load(open(os.path.join(SCRATCH, "out_sector.json")))

V = ("mom1", "mom2", "mom4", "rev_gap")

# ---- fm8 attenuation of a beta-independent signal (Review H-32 B-4): the PIT beta uses weeks t-7..t and so
# contains the formation week(s); the cross-sectional FM regression absorbs part of an injected signal.
# Factor measured here on the synthetic PC world (mom1, W1 stress, 300 CRN pairs): realized / injected.
REPO = os.environ.get("H32_REPO", "/home/user/scinance")
sys.path.insert(0, os.path.join(REPO, "src"))
from bybit_edge.research import power_p1 as P  # noqa: E402

pc = sc["power_check_null_world"]
attn = pc["realized_injection_mean"] / pc["injected_signal_ic"]
LIT = (0.004, 0.012, 0.020, 0.033)
damp = {"faktor_realisiert_durch_injiziert_mom1_W1": attn,
        "quelle": "sector_check.py power_check_null_world (synthetisch); Review H-32 B-4: 0,751 stress / 0,764 measured",
        "hinweis": "fuer mom1 gemessen; mom2/mom4 (mehr Formationswochen im Beta-Fenster) vermutlich staerker gedaempft -> Werte dort Obergrenzen",
        "uebergabe_bei_literaturwert_auf_fm8_skala": {}, "drop_lesart_beta_unabhaengiges_signal_bei_mde80": {}}
for v in V:
    oc = pw["handover_oc"][v]
    se_p = oc["se_pilot"]
    row = {}
    for reading in ("A_punkt", "B_untere_80"):
        thr, m_p = oc[reading]["pilot_threshold_on_point"], oc[reading]["m_pilot_proxy"]
        row[reading] = {str(ic): P.condition_power(ic * attn + m_p, thr, se_p) for ic in LIT}
    damp["uebergabe_bei_literaturwert_auf_fm8_skala"][v] = row
    mde = max(pw["power_table"][v]["S1_draws_sd_bindend"]["thresholds"][W]["mde80"] for W in ("W1", "W2"))
    damp["drop_lesart_beta_unabhaengiges_signal_bei_mde80"][v] = {"mde80_fm8": mde, "signal_aequivalent": mde / attn}
summary = {
    "handover_threshold_lesart_A_on_pilot_point": {v: pw["handover_oc"][v]["A_punkt"]["pilot_threshold_on_point"] for v in V},
    "handover_threshold_lesart_B_on_pilot_point": {v: pw["handover_oc"][v]["B_untere_80"]["pilot_threshold_on_point"] for v in V},
    "se_pilot_predicted": {v: pw["handover_oc"][v]["se_pilot"] for v in V},
    "breakeven_prior_C10_p1": {v: pw["power_table"][v]["S1_draws_sd_bindend"]["breakeven_C10_p1"] for v in V},
    "breakeven_prior_C10_a3_praxis": {v: pw["power_table"][v]["S1_draws_sd_bindend"]["breakeven_C10_a3_praxis"] for v in V},
    "mde80_W1_W2_S1": {v: {W: pw["power_table"][v]["S1_draws_sd_bindend"]["thresholds"][W]["mde80"] for W in ("W1", "W2")} for v in V},
    "ic_for_50pct_handover_A": {v: pw["handover_oc"][v]["A_punkt"]["ic_for_50pct_handover"] for v in V},
    "ic_for_50pct_handover_B": {v: pw["handover_oc"][v]["B_untere_80"]["ic_for_50pct_handover"] for v in V},
    "sector_world_sd_increase_rel_0375": sc["sd_by_sector_strength"][-1]["sd_weekly_ic"] / sc["sd_by_sector_strength"][0]["sd_weekly_ic"] - 1.0,
    "fm8_daempfung": attn,
    "f_week_end_power_at_mde80_m1_to_4_and_11": {v: {m: pw["f_week_by_end_power"]["variants"][v]["end_power_at_mde80"][m]["joint"]
                                                    for m in ("1", "2", "3", "4", "11")} for v in V},
}
out = {
    "titel": "H-32 Herleitung (Zweistufen-Design, beta-neutraler Querschnitts-IC): Power, Pilot-Praezision, Uebergaberegel",
    "stand": "2026-10-20",
    "ergebnisblind": ("Keine reale IC, kein Panel, kein Outcome. Eingaben: v5e-Vorlauf-JSON (offen), WP-7-Wochen-K "
                      "(Spalten week, n_symbols), A1-Pilotbasis-Metadaten; synthetischer Sektor-/Power-Check mit Repo-Code "
                      "auf einem kuenstlichen Panel. Keine Siegeldatei geoeffnet."),
    "skripte": {
        "h32_power.py": sha(os.path.join(SCRATCH, "h32_power.py")),
        "sector_check.py": sha(os.path.join(SCRATCH, "sector_check.py")),
        "assemble.py": sha(os.path.join(SCRATCH, "assemble.py")),
        "ort": "Sitzungs-Scratchpad h32_herleitung/ (ausserhalb des Repos)",
    },
    "zusammenfassung": summary,
    "power": pw,
    "synthetischer_check": sc,
    "fm8_daempfung": damp,
    "stand_review": "Auflagen A-2, A-3, A-4, A-6, A-7, A-8, B-6 aus REVIEW_H32.md eingearbeitet (2026-10-20, nach DEC-99)",
}
with open(OUT, "w") as f:
    json.dump(r6(out), f, indent=1, sort_keys=True)
    f.write("\n")
print(OUT, sha(OUT))
