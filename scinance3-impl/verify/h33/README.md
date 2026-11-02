# verify/h33 - unabhaengige Nachpruefung H-33 (REVIEW_H33.md)

review_h33.py (sha256 723fa4a4...dee4, REVIEW_H33.md Z. 16; eigene Nachrechnung mit power_p1 und h32_fm8.estimators, zweimal gerechnet, Ausgabe out1 = out2);
SPEC_H33_review.md (Auftrag). Eingaben wie ../../derivations/h33/README.md; keine Marktdaten. Ausgaben out1.json / out2.json
(sha256 97f76824...6fbe, bitgleich) liegen nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
