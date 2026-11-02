"""Consolidate the Stufe-1 intermediate JSONs into scinance3-impl/state/herleitung_a1/feasibility.json.
Only formation-side numbers, nuisance dispersion/ratio numbers and the power arithmetic are copied."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")

import a1_common as C  # noqa: E402

SCRIPTS = ["a1_common.py", "a1_model.py", "a1_window_census.py", "a1_nuisance.py", "a1_formation_sensitivity.py",
           "a1_power.py", "a1_kill4_ci.py", "a1_psi_by_class.py", "a1_selfcheck.py", "a1_check_factor.py",
           "a1_bookkeeping.py", "a1_explore.py", "a1_consolidate.py", "run_all.sh"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def j(name: str):
    return json.loads((C.WORK / name).read_text(encoding="utf-8"))


def main():
    out = {
        "titel": "A1 (H-31) Stufe 1 - Feasibility (C.12), Herleitung, ENTWURF, nicht registriert",
        "stand": "2026-10-13",
        "etikett_ergebnisblindheit": (
            "Ab 2024-07-01 nur formationsseitige Groessen (Schluessel, D1, Spread der Formationswoche, K, "
            "Intervallklassen, PIT-Betas aus Vergangenheitsrenditen, Markt-Faktor-SD, Zeitreihen-Autokorrelation "
            "des Schluessels je Symbol). Outcome-seitig nur Streuung/Kovarianz/Verhaeltnis auf 2021-03-01..2024-06-30 "
            "(letzte Haltewoche 2024-06-24); kein Rendite-Mittel ausgegeben oder gespeichert. Keine Tagesdaten nach "
            "2026-06-28 geladen. Keine Siegeldatei geoeffnet."),
        "skripte": {s: sha(C.WORK / s) for s in SCRIPTS if (C.WORK / s).is_file()},
        "configs": {},
        "kill4_ci_formationsseitig": j("kill4_ci.json"),
        "psi_innerhalb_formationswoche_nach_klasse": j("psi_by_class.json"),
        "buchhaltung_formationsseitig": j("bookkeeping.json"),
        "stress_abdeckung": {
            "STRESS_REL_sha256": "eb83fe402b7b87243b1fc93691079a073461a42b6c17341502bc8c83678ca667",
            "STRESS_REL_episoden": {"W1": 13, "W2": 6, "nuisance_2021-03..2024-06": 15},
            "STRESS_ABS_sha256": "b75fb7a08a6d590363f62828de99f23359c1c63fe1f385d0e4f37ba09bccf794",
            "STRESS_ABS_episoden": {"W1": 2, "W2": 1, "nuisance_2021-03..2024-06": 9},
        },
    }
    for cfg, suf, label in (("A_dec70_1h_eingeschlossen", "", "DEC-70-Konstruktion wie im Auftrag, alle Intervallklassen intervall-normiert (DEC-67 E2/DEC-84)"),
                            ("B_1h_symbolwochen_ausgeschlossen", "_excl1h", "DEC-58-E3-Lesart: Symbol-Woche ausgeschlossen, wenn die Formationswoche einen 1h-Tag hat (look-ahead-frei)")):
        wc = j(f"window_census{suf}.json")
        nu = j(f"nuisance{suf}.json")
        fs = j(f"formation_sensitivity{suf}.json")
        fe = j(f"power{suf}.json")
        win = {}
        for wn, w in wc["windows"].items():
            win[wn] = {k: v for k, v in w.items()}
        out["configs"][cfg] = {
            "beschreibung": label,
            "fingerprint": wc["fingerprint"],
            "fenster_formationsseitig": win,
            "symbole_ueber_beide_fenster": wc["symbols_both_windows"],
            "nuisance": nu,
            "formationsseitige_sensitivitaeten": fs,
            "power": {k: v for k, v in fe.items() if k not in ("fingerprint",)},
        }
    (C.OUT / "feasibility.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print("written", C.OUT / "feasibility.json", sha(C.OUT / "feasibility.json"))


if __name__ == "__main__":
    main()
