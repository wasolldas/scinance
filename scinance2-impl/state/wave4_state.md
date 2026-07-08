# Scinance 2.0 — Welle 4 Implementation State (Cross-Domain-Track H-09..H-13)

**Run gestartet:** 2026-07-07
**Branch:** `scinance2-wave2` (Fortsetzung, kein eigener Branch — Praezedenzfall Welle 3)
**Herkunft:** `edge-research-v3/` Cross-Domain-Research-Run (eigenes CLAUDE.md, 6 Fachgebiete), Uebergabe via DEC-19.
**Verfassung:** `edge-research-v3/results/CROSSDOMAIN_PRD.md` + `hardened_hypotheses.md` (woertlich uebernommen in `hypothesis_registry.md` Abschnitt "Welle 4"), Scinance-2.0-Kern-Verfassung (`scinance2-impl/CLAUDE.md`) unveraendert bindend.

## Welle-3-Stand (uebernommen, unveraendert)
Programm nach GL-013: 9 DROP, 2 PARK, 2 kapitalfreie WEITER, 0 handelbare Kanten (`PROGRAM_FINAL_REPORT.md`). Welle 4 eroeffnet eine neue Suchachse (6 fachfremde Disziplinen), keine Reaktivierung gefallener Hypothesen.

## Die 5 Welle-4-Hypothesen

| H-xx | Disziplin | Familie | Reifegrad | Modul (geplant) |
|---|---|---|---|---|
| H-09 | Mechanism Design | F-BUNCH | sofort testbar | `research/c09_bunch/` |
| H-10 | Dendrochronologie | F-POINTER | sofort testbar | `research/c10_pointer/` |
| H-11 | Climatology (§5) | F-ANEN | **data-gated** (>=730d Manifest) | `research/c11_anen/` |
| H-12 | Econophysics/RMT | F-FRAG | sofort testbar | `research/c12_frag/` |
| H-13 | EVT/Aktuarmathematik | F-TAILSHAPE | **data-gated** (2 Live-IV-Snapshot-Tage) | `research/c13_tailshape/` |

Alle 5: **capital_free=true**, keine H-xxb-Tradability-Folge impliziert, hartes Ein-Fenster-Kriterium, kein Graubereich, GL-012-Feasibility bestanden (0 struktureller DROP).

## Phasen-Log (Agentennetzwerk-Ausfuehrung)

- [x] Phase A — WP-0 Bruecke: H-09..H-13 woertlich in `hypothesis_registry.md` uebernommen, DEC-19 protokolliert (2026-07-07, Orchestrator direkt statt Subagent — Transkriptions-Treue).
- [x] Phase B — 5 parallele Fable-5-Builder (Module + CLI + Runner + Tests, gegen synthetische Harvester-Baeume verifiziert). Abgeschlossen 2026-07-08.
- [x] Phase C — 5 parallele Fable-5-Adversarial-Audits (Spezifikations-Treue-Pruefung durch frische Agenten, nicht die Builder selbst). Abgeschlossen 2026-07-08. Befunde: `state/audit_h09.md`..`audit_h13.md`.
- [x] Phase D — Fix-Loop (Runde 1 von max. 2 gedeckelten Runden genuegte fuer alle 4 Befund-Module). Abgeschlossen 2026-07-08.
- [x] Phase E — Regression + Runner-Konsolidierung (`run_wave4.{ps1,sh}`) + F-XDOM1-Vorregistrierung (DEC-22) + Handoff-Dokumentation. Abgeschlossen 2026-07-08.

**Welle 4 Implementierung: VOLLSTAENDIG.** Naechster Schritt liegt beim User: `run_wave4.sh`/`.ps1` auf der lokalen Maschine gegen den echten Harvester-Bestand ausfuehren (siehe `handoff_local/README_WAVE4.md`).

## CHANGELOG

- W4-BRIDGE (2026-07-07): H-09..H-13 aus `edge-research-v3/results/{CROSSDOMAIN_PRD.md,deep_validation/hardened_hypotheses.md}` woertlich in `scinance2-impl/state/hypothesis_registry.md` uebernommen (Abschnitt "Welle 4 — Cross-Domain-Track"), DEC-19 protokolliert. GL-Zaehlung bleibt bei GL-013.
- W4-BUILD (2026-07-07/08, Phase B): 5 Module (`c09_bunch`, `c10_pointer`, `c11_anen`, `c12_frag`, `c13_tailshape`) + CLI + T2-Runner + Tests gebaut, gegen synthetische Hive-Baeume verifiziert, committed (u.a. b6fa3e3..2266a38, 603e0a7..590e05f, 4700fd2). Ein Bau-Zwischenfall: H-12 verlor einen Builder-Agenten an einen Server-Fehler, ein Fortsetzungsagent uebernahm die 4 fertigen Dateien und ergaenzte `driver.py`. Ein zweiter Zwischenfall: Fable-5-Wochenlimit unterbrach H-12/H-13 kurz (DEC-20, per DEC-20-Korrektur revidiert, nachdem der User klaergestellt hatte, dass Fable 5 laenger verfuegbar bleibt).
- W4-AUDIT (2026-07-08, Phase C): 5 unabhaengige, frische Fable-5-Audits (nicht die Builder) gegen die Registry/`hardened_hypotheses.md` geprueft. Verdikte: H-09 FAIL (2 HIGH), H-10 FAIL (1 HIGH), H-11 FAIL (1 KRITISCH + 2 HIGH), H-12 PASS-WITH-NOTES (3 LOW), H-13 PASS-WITH-NOTES (1 HIGH). Volltexte: `state/audit_h09.md`..`audit_h13.md` (committed 36aaf82).
- W4-FIX (2026-07-08, Phase D): H-12s 3 LOW-Befunde vom Orchestrator direkt gefixt (36aaf82). H-09/H-10/H-11/H-13s Befunde durch 4 parallele Fable-5-Fix-Agenten behoben — alle 4 wurden einmal durch ein Session-Limit unterbrochen (13:40 UTC) und nach Reset per SendMessage aus dem Transkript fortgesetzt, kein Neustart, kein Kontextverlust. Committed: H-13 (583e6ca), H-11 (e1a44a5), H-09 (4100956), H-10 (dcad665). H-11s Bug 1 (kritisch: CRPS als Punktprognose statt registrierter Verteilung) war der schwerwiegendste Einzelbefund des gesamten Programms in diesem Zyklus.
- W4-REGRESSION (2026-07-08): Voller Repo-Testlauf (`tests/unit`, --continue-on-collection-errors): 888 passed, 12 failed/4 errors — alle 12+4 VORBESTEHEND und umgebungsbedingt (fehlende `aiohttp`/`sortedcontainers`/pytest-asyncio-Plugin im Sandbox, unabhaengig von Welle 4 verifiziert per `git stash`-Vergleich durch den H-10-Fix-Agenten). Keine Regression durch Welle-4-Arbeit.
- W4-CONSOLIDATE (2026-07-08, Phase E): F-XDOM1 vorregistriert (DEC-22) — bindende Kohorten-Regel fuer den gemeinsamen H-09/H-10/H-12-Lauf in `run_wave4`. `aggregate_wave4_fdr.py` (Stage-2-BH-FDR-Aggregator, Muster F-WAVE2), `run_wave4.{ps1,sh}` (konsolidierter T3-Runner: H-11/H-13-Entsperr-Check zuerst, dann Kohorte H-09/H-10/H-12, dann F-XDOM1-Aggregation), `README_WAVE4.md`, 15 neue Tests. Verifiziert: 107/107 Tests gruen, Dry-Run + echter Lauf ohne Junction beide sauber (exit 0 bzw. 2). Committed badd140.
- **Welle 4 abgeschlossen 2026-07-08.** Kein Lauf gegen echte Daten in dieser Session (T2/T3 sind Nutzer-Maschinen-Stufen per Testpyramide). Naechster Schritt: User fuehrt `run_wave4.sh`/`.ps1` lokal aus; `gate-auditor`-Auswertung (`state/morning_report.md`-Muster) folgt danach.
