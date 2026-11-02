# verify/h27 - unabhaengige Nachpruefung H-27 (REVIEW_H27.md Abschnitt 6)

Skripte mit gekuerzter sha256 (Praefix...Suffix, REVIEW_H27.md Z. 294-300, alle acht stimmen): rv_common.py bd8880ab...bb59b147,
nuisance_review.py ffd9469d...12faa63a, nullworld_review.py 82a80181...ab1ff267, noise_share.py a4f4f14e...b8b7627c, power_review.py
e45e4102...5b4c1cb2, conv_review.py 8ffd90a0...f9be7deb, setup_cache.py fd944b22...cc47f238, keyscan.py 8113ae8d...e8f869fa.
SPEC_H27_review.md (Auftrag). Eingaben und Zugang wie ../../derivations/h27/README.md (Archivzugang ueber Umgebungs-Secrets HARVEST_S3_*;
setup_cache.py kopiert den Cache der Vorperiode). Ausgaben nuisance_review.json, nullworld_review.json, noise_share.json, power_review.json
liegen nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
