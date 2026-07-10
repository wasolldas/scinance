# Scinance 2.0 — Welle 5 Implementation State (GPU-Pattern-Mining H-14..H-18)

**Run gestartet:** 2026-07-09
**Branch:** `scinance2-wave2` (Fortsetzung, kein eigener Branch — Praezedenzfall Welle 3/4)
**Herkunft:** Fable-5-Recherche-Netzwerk (`state/GPU_RESEARCH_SCAN_2026-07-09.md`), Uebergabe via DEC-24.
**Verfassung:** `scinance2-impl/CLAUDE.md`, Registry-Abschnitt "Welle 5 — GPU-Pattern-Mining (H-14..H-18)" in `state/hypothesis_registry.md`.

## Ausgangslage

Nach der kombinierten Bugfix-Runde (5 kritische Befunde aus dem Fable-5-Review-Netzwerk
ueber die gesamte Codebasis, `state/CRITICAL_REVIEW_2026-07-09.md`) gab der Nutzer explizit
gruenes Licht: "Erst bugfix runde, dann gpu wave 5 start!" Welle 5 ist die erste Welle mit
Rechenaufwand-Tag **GPU** (Zielmaschine: RTX 5060 Ti Blackwell, CUDA 12.8+/PyTorch 2.7+,
82GB RAM — Sandbox hat kein torch/keine GPU).

## Die 5 Welle-5-Hypothesen

| H-xx | Kandidat | Familie | Kritiker-Score | Modul |
|---|---|---|---|---|
| H-14 | PANEL-LAG (Cross-Venue-Lead-Lag-Graph) | F-PANELLAG | 12/12 | `research/c14_panellag/` |
| H-15 | DSM-01 (Trade-Tape-Grammatik) | F-GRAMMAR | 11/12 | `research/c15_grammar/` |
| H-16 | V-02 Time-Arrow-CNN | F-ARROW | 11/12 | `research/c16_arrow/` |
| H-17 | VENUE-FINGERPRINT | F-VENUE | 11/12 | `research/c17_venue/` |
| H-18 | GL-006/H-04 High-N-Power-Audit | F-LEADLAG (wiederverwendet) | 10/12 | `research/c18_leadlag_audit/` |

Alle 5: **capital_free=true**, keine H-xxb-Tradability-Folge impliziert, hartes
Ein-Fenster-Kriterium (bzw. T1/T2 bei H-18), kein Graubereich. **Keine Kohorten-Regel wie
Welle 4** — die 5 Hypothesen laufen sinnvollerweise EINZELN nacheinander (VRAM-/
Zeit-Konkurrenz um dieselbe Karte). H-18 ist explizit KEINE neue Hypothese, sondern ein
Aufloesungs-Audit von GL-006 (H-04) — das GL-006-Verdikt selbst bleibt unveraendert.

## Phasen-Log

- [x] Phase A — WP-0 Bruecke: H-14..H-18 woertlich aus `GPU_RESEARCH_SCAN_2026-07-09.md` in
      `hypothesis_registry.md` uebernommen, DEC-24 protokolliert (2026-07-09/10).
- [x] Phase B — 5 parallele Fable-5-Builder (Module + CLI + T3-Runner + Tests, torch-optional
      nach m18_patchtst-Muster, Compute-Gating gegen jeden CPU-Fallback-Pfad). Abgeschlossen
      2026-07-10. Zwei Session-Limit-Unterbrechungen (Reset 23:30 UTC, dann 5:00 UTC), beide
      per SendMessage-Resume ohne Kontextverlust fortgesetzt.
- [x] Phase C — 5 parallele Fable-5-Adversarial-Audits (frische Agenten, nicht die Builder).
      Abgeschlossen 2026-07-10. Verdikte: H-14 PASS-WITH-NOTES (1 CRITICAL), H-15 "bedingt
      freigegeben" (2 HIGH), H-16 PASS (nur 2 LOW), H-17 PASS-WITH-NOTES (1 MEDIUM), H-18
      PASS-WITH-NOTES (1 HIGH). Volltexte: `state/audit_h14.md`..`audit_h18.md`.
- [x] Phase D — Fix-Loop. Alle Befunde behoben: H-14 (Checkpoint-Provenienz-Pruefung,
      weiter_indication-Nulling bei Positivkontroll-Fehlschlag, RC_DATA_MISSING-Crash), H-15
      (Architektur-Drift-Gate, Symbol-Identitaets-Check, echtes Per-Symbol-Checkpointing),
      H-17 (tatsaechlich-erreichter-Batch-Check gegen c17_venue/contrastive.py), H-18
      (Runner-Selftest-Gate-Durchsetzung, Datenbindungs-Sichtbarkeit in CLI/SUMMARY). H-16
      brauchte keinen Fix (nur 2 dokumentierte LOW-Punkte). Abgeschlossen 2026-07-10.
- [x] Phase E — Regression + Handoff-Dokumentation. Voller Repo-Testlauf: 1095 passed, 2
      vorbestehende Failures + 4 Collection-Errors (fehlende Sandbox-Dependencies,
      unabhaengig von Welle 5, identisch zur Welle-4-Baseline). Keine Regression.

**Welle 5 Implementierung: VOLLSTAENDIG.** Naechster Schritt liegt beim User: die 5
T3-Runner (`run_h14`..`run_h18`) NACHEINANDER auf der lokalen RTX-Maschine ausfuehren (siehe
`state/WELLE5_HANDOFF.md`).

## CHANGELOG (Commit-Referenzen)

- W5-BRIDGE (2026-07-09/10): H-14..H-18 in `hypothesis_registry.md` uebernommen (`d087ba5`), DEC-24.
- W5-BUILD H-16 (2026-07-10): Time-Arrow-CNN, 38 Tests. Commit `a859baa`.
- W5-BUILD H-18 (2026-07-10): GL-006-Power-Audit, 39 Tests. Commit `4a3623b`.
- W5-BUILD H-15 (2026-07-10): Trade-Tape-Grammatik, 35 Tests. Commit `56f1959`.
- W5-BUILD H-17 (2026-07-10): Venue-Fingerprint, 18 Tests. Commit `b392826`.
- W5-BUILD H-14 (2026-07-10): PANEL-LAG, 20 Tests. Commit `2d38637`.
- W5-AUDIT H-16 (2026-07-10): PASS, 2 LOW. Commit `04bcd26`.
- W5-AUDIT H-18 (2026-07-10): PASS-WITH-NOTES, 1 HIGH + 1 MEDIUM + 1 LOW. Commit `1f45587`.
- W5-FIX H-18 (2026-07-10): Runner-Selftest-Gate + Datenbindungs-Sichtbarkeit. Commit `7083beb`.
- W5-AUDIT H-14+H-15 (2026-07-10): PASS-WITH-NOTES (1 CRITICAL) bzw. "bedingt freigegeben"
  (2 HIGH). Commit `0f4da28`.
- W5-AUDIT H-17 (2026-07-10): PASS-WITH-NOTES, 1 MEDIUM + 1 LOW. Commit `b1ba230`.
- W5-FIX H-17 (2026-07-10): Achieved-Batch-Compute-Gate + ASCII-Kommentar. Commit `a989e1f`.
- W5-FIX H-14 (2026-07-10): Checkpoint-Provenienz + weiter_indication-Nulling. Commit `f5b4f9d`.
- W5-FIX H-15 (2026-07-10): Architektur-Drift-Gate + Symbol-Identitaet + echtes Checkpointing.
  Commit `77cdc61`.
- **Welle 5 abgeschlossen 2026-07-10.** Kein GPU-Lauf in dieser Session (Sandbox hat keine
  GPU). Naechster Schritt: User fuehrt die 5 T3-Runner lokal aus.
