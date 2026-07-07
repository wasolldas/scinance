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
- [ ] Phase B — 5 parallele Fable-5-Builder (Module + CLI + Runner + Tests, gegen synthetische Harvester-Baeume verifiziert)
- [ ] Phase C — 5 parallele Fable-5-Adversarial-Audits (Spezifikations-Treue-Pruefung durch frische Agenten, nicht die Builder selbst)
- [ ] Phase D — Fix-Loop (nur bei Befund, Deckel 2 Runden)
- [ ] Phase E — Regression + Runner-Konsolidierung (`run_wave4.{ps1,sh}`) + Handoff-Dokumentation fuer den User (2-Wochen-Rueckkehr)

## CHANGELOG

- W4-BRIDGE (2026-07-07): H-09..H-13 aus `edge-research-v3/results/{CROSSDOMAIN_PRD.md,deep_validation/hardened_hypotheses.md}` woertlich in `scinance2-impl/state/hypothesis_registry.md` uebernommen (Abschnitt "Welle 4 — Cross-Domain-Track"), DEC-19 protokolliert. GL-Zaehlung bleibt bei GL-013. Naechster Schritt: Agentennetzwerk Phase B (5 parallele Fable-5-Builder).
