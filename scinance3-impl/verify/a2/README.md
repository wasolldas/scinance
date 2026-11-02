# verify/a2 - unabhaengige Nachpruefung A2 Teil C (F0)

Review (Rolle Review): `rv_common.py`, `r1_main.py`, `r3_extra.py`, `s0_leak_channel_presence.py`, `s2_guard_probe.py`
(sha256-Pins in `state/herleitung_a2/REVIEW_A2_TEILC.md` Abschnitt 6; byte-identisch), `SPEC_A2_teilC_review.md` (Auftrag).
Orchestrator: `a2_null_check.py`, `a2_p3fix_check.py`, `a2_teilc_check.py`, `a2_teilc_f2_check.py` (eigener Code, andere
Seeds; `state/herleitung_a2/NACHRECHNUNG_ORCHESTRATOR.md`).

Reproduktion: Eingaben wie `derivations/a2` (siehe `data_manifest/EXTRACT_LOG.json`); `r3_extra.py` braucht `work/r1.json`
aus `r1_main.py`; `s2_guard_probe.py` liest die Teil-C-Skripte (Pfad hart kodiert auf das Sandbox-Arbeitsverzeichnis) und
`state/herleitung_a2/a2_teilC.json`. Ergebnis-Hashes stehen in der Akte (REVIEW_A2_TEILC.md).

Warnungen: `a2_null_check.py` schreibt die Vereinigungs-Streuung der Wochentage (Kanal-Typ B-1, DEC-103 N1 (2c)) -
seine Ausgabe gehoert nie ins Repo oder in eine CI-Ausgabe; `work/` ist per `.gitignore` ausgeschlossen. Kein Skript
bildet den Kontrast mit den realen Labels; so lassen. `s0_leak_channel_presence.py` sucht das in Fassung 2 entfernte
Feld und ist nur historischer Nachweis.
