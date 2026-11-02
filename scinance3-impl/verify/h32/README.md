# verify/h32 - unabhaengige Nachpruefung H-32 (REVIEW_H32.md, REVIEW_REGISTRIERUNG_H32.md, ..._NACHPRUEFUNG.md)

Review der Herleitung: rv_power.py, rv_oc.py, rv_ceiling.py, rv_inject.py, rv_sector.py, rv_serule.py, rv_wc.py, rv_attn.py (REVIEW_H32.md Z. 16-17).
Registrierungs-Review: rr_check.py, rr_q95_mc.py, rr_size_twins.py, rr_twins.py (REVIEW_REGISTRIERUNG_H32.md); Nachpruefung: rr2_check.py,
rr2_locks.py, rr2_pk.py, rr2_pk_f.py, rr2_u3k.py (..._NACHPRUEFUNG.md). Orchestrator: h32_v6_power.py. smoke/: Builder-Smoke-Skripte auf synthetischem Panel
(REVIEW_REGISTRIERUNG_H32.md Z. 17 nennt nur das Verzeichnis; sie importieren tests.unit.h32_fixtures aus einem Worktree und lesen einen
Pickle-Zwischenstand, der nicht uebernommen ist). SPEC_H32_review.md, SPEC_H32_registrierung_review.md (Auftraege).
Pins: Skripte nicht per sha256 gepinnt (Namen); gepinnt sind Re-Emissionen/Ausgaben (h32_v1_reemit.yaml bddfb9cb... / a3079cf9...,
rerun_power_h32.json df17cafa..., rerun_out_power.json bcb0d91c...), nicht hier. Eingaben wie ../../derivations/h32/README.md.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
