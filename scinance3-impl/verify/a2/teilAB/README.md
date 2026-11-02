# verify/a2/teilAB - unabhaengige Nachpruefung A2-Vorarbeit Teil A/B (REVIEW_A2_VORARBEIT.md, NACHRECHNUNG_ORCHESTRATOR.md)

Review: rv_sigma.py (Streuung/rho/ACF/c, eigener Lader mit Assert vor jedem Preis, Seed 4711), rv_power.py (N, SE, MDE80, Konjunktions-
Power, MC-Seed 11), rv_oi.py (OI aus den Rohpartitionen), rv_fut.py (Futures-Kalender), rv_timing.py (Zeitlage), rv_did.py (DiD-Streuung),
rv_band.py (Blockwahl), cmp_sigma.py (Vergleich), keyscan.py / pathscan.py / guardtest.py (Siegel-Scans); SPEC_A2_review.md (Auftrag).
Orchestrator: a2_fut_check.py, a2_joint_check.py, a2_spot.py (NACHRECHNUNG_ORCHESTRATOR.md; eigener Code).
Pins: die Review-Skripte sind nicht per sha256 gepinnt (nur Namen, REVIEW_A2_VORARBEIT.md Z. 130-135); gepinnt sind nur Ausgaben
(rv_sigma.json e7b85dd0..., rv_power.json ea034145..., rv_oi.json 8e2e6b80...; Praefixe, Dateien nicht im Repo).
Reproduktion: Eingaben wie ../../../derivations/a2/teilAB/README.md; guardtest.py importiert a2v_common (Layout dort). Laufzeit < 1 min.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
