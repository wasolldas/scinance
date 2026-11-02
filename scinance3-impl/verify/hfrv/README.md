# verify/hfrv - unabhaengige Nachpruefung HF-RV-Nuisance (REVIEW_HFRV.md Abschnitt 7, NACHRECHNUNG_ORCHESTRATOR.md)

Skripte mit gekuerzter sha256 (REVIEW_HFRV.md Z. 306-310, alle fuenf stimmen): review_hfrv.py a749af2f...165394a4, compare.py
3d91572e...57b8cb58, c_robust.py de3fd9d5...17cd1ad0, a2_review.py 830c4dab...a5f789d2, keyscan.py a643d013...b0c27469.
Orchestrator: hfrv_spot.py (NACHRECHNUNG_ORCHESTRATOR.md Z. 3). SPEC_HFRV_review.md (Auftrag).
Aufruf: python3 -I review_hfrv.py (~5 s), compare.py, c_robust.py, a2_review.py. Eingaben wie ../../derivations/hfrv/README.md.
Nicht uebernommen: der Rerun-Ordner des Reviewers (Kopien der Herleitung mit umgeleiteter Ausgabe; hfrv_common.py dort mit anderer
sha256 als der Pin) und die Ergebnis-JSON (review_hfrv.json u.a.).
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
