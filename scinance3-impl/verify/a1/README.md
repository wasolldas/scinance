# verify/a1 - unabhaengige Nachpruefung A1 (H-31)

Review (REVIEW_A1.md Z. 5-6, 172-173): rv_load.py, rv_formation.py, rv_nuisance.py, rv_power.py, rv_wp7_zerofill.py (eigene Nachrechnung,
eigener Lader); SPEC_A1_review.md (Auftrag). Nicht per sha256 gepinnt, nur per Namen in der Akte.
Reproduktion: cd /tmp && PYTHONPATH=/home/user/scinance/src python -I rv_load.py, danach rv_formation.py, rv_nuisance.py, rv_power.py,
rv_wp7_zerofill.py (je Sekunden; Panel ausserhalb des Repos, siehe ../../derivations/a1/README.md). Ausgaben rv_formation.json,
rv_nuisance.json liegen nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
