"""Assemble a2_teilC.json from work/c1.json, c2.json, c3.json (R-C12).  Prints only sha256.
Usage: python3 c_build.py [--out PATH]   (default: the official file under state/herleitung_a2/)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_common as cc  # noqa: E402

SCRIPTS = ["c_common.py", "c1_nullsim.py", "c2_funding.py", "c3_pilot.py", "c_build.py", "c_tables.py", "test_c_guards.py",
           "run_all.sh"]


def main(out: Path) -> str:
    if cc.sha256(cc.A2_VORARBEIT) != cc.A2_VORARBEIT_SHA:
        raise RuntimeError("a2_vorarbeit.json (Fassung 2) changed")
    parts = {k: json.loads((cc.WORK / f"{k}.json").read_text(encoding="ascii")) for k in ("c1", "c2", "c3")}
    for p in parts.values():
        p.pop("label", None)
    obj = {
        "label": cc.LABEL,
        "stand": "Fassung 2 (2026-10-31) nach REVIEW_A2_TEILC.md: VETO-Aufloesung A-1, Auflagen A-2..A-9 eingearbeitet; "
                 "Entwurf der Herleitung Teil C; nichts registriert, kein Verdikt",
        "festlegungen_orchestrator_2026-10-31": "Festlegung des Orchestrators (2026-10-31, nach Kenntnis der Nuisance "
                 "einschliesslich der Pilot-Power-Tabelle, Richtung Strenge): (a) Null-Bedingung als eigener Faktor, "
                 "exakte bivariate P2''-Bedingung Bericht; (b) Test skaliert seine Null wie DEC-101 E2, Pilot-Schwelle mit "
                 "k_pred (U-4 woertlich); (c) Stress-Kalibrierung V1 bindet; (d) Regel R0 registriert, R1/R2 Bericht, "
                 "R3/R5 strengere Alternativen; (e) PK-Kriterium (b) = erwartete Quote - 2,3263 Binomial-SE, Gate (4) in "
                 "der PK-Kette; (f) Gate (4) als Faktor 0,95 je Symbol (vorlaeufig, UNBELEGT bis Negativ-Panel-Daten)",
        "regeln": "R-C1..R-C12 im Docstring von c_common.py (vor der ersten Zahl geschrieben)",
        "kuerzel": "[aj-C:<pfad>] = dieses JSON; teil_C1 = Null-Simulation/bindende SE/MDE80, teil_C2 = Funding W2, "
                   "teil_C3 = Pilot-Regel (Vorlage), kanal_scan_R_C12a = Varianzzerlegungs-Scan",
        "skripte_sha256": {s: cc.sha256(cc.HERE / s) for s in SCRIPTS},
        "work_sha256": {f"{k}.json": cc.sha256(cc.WORK / f"{k}.json") for k in ("c1", "c2", "c3")},
        "wiederverwendet_sha256": {"power_p1.py": cc.sha256(cc.POWER_P1),
                                   "a2_vorarbeit.json (Fassung 2, nur Konstanten-Abgleich)": cc.A2_VORARBEIT_SHA},
        "teil_C1": parts["c1"], "teil_C2": parts["c2"], "teil_C3": parts["c3"],
    }
    obj["kanal_scan_R_C12a"] = dict(cc.assert_no_variance_channel(obj),
                                    entfernt_gegen_fassung1="teil_C1.pre_windows.<V>.sd_of_null_shift_iid (SD der "
                                    "Vereinigung E u P2'' x Kalenderfaktor, Review B-1)")
    return cc.dump(obj, out)


if __name__ == "__main__":
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else cc.OUT_DIR / "a2_teilC.json"
    print("a2_teilC.json sha256", main(out))
