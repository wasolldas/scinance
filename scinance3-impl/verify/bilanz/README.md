# verify/bilanz - unabhaengige Nachpruefung Programm-Bilanz (REVIEW_PROGRAMM_BILANZ_2026-10-18.md Abschnitt "Skripte")

review_check.py (b3bdc074...a1bb3fdf: Nuisance-Lesung mit Waechter, ganzzahlige Dauern mit power_p1, fm8 auf W1/W2),
rerun/census_copy.py (21ed2e70...8797b1de: Kopie von ../../derivations/bilanz/bilanz_census.py mit nach Scratchpad umgeleiteter Ausgabe;
Ergebnis-JSON identisch bis auf das Feld skript); SPEC_BILANZ_review.md (Auftrag). Die Ausgabe review_check.json (92e8c17a...) liegt nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
