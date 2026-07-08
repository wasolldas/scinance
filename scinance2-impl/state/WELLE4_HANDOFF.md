# Welle 4 — Handoff für die Rückkehr in 2 Wochen

**An dich:** Kurzfassung dessen, was seit dem Startschuss ("Ja, klingt gut,
los geht's!") autonom passiert ist, und was jetzt von dir gebraucht wird.
Alles Folgende ist bereits committed und auf `claude/subagent-prd-development-T16fE`
gepusht.

## Was passiert ist (in einem Satz)

Die 5 aus dem Cross-Domain-Research-Run (edge-research-v3) vorregistrierten
Hypothesen H-09..H-13 sind jetzt vollständig als Code implementiert, von
frischen Agenten (nicht den Bauenden selbst) gegen die Registry geprüft,
alle gefundenen Fehler behoben, und in einem konsolidierten Runner für
deinen nächsten lokalen Lauf zusammengeführt.

## Was du jetzt tun musst

1. Repo auf `claude/subagent-prd-development-T16fE` pullen (oder die
   Ergebnis-Zweig-Historie sichten).
2. Prüfen, dass die read-only Harvester-Junction `data/harvest` auf deiner
   Maschine steht (wie bisher).
3. `run_wave4.ps1` (Windows) bzw. `run_wave4.sh` (Linux/WSL) starten —
   ein Befehl, keine Pflicht-Parameter, läuft unbeaufsichtigt
   (Details: `scinance2-impl/handoff_local/README_WAVE4.md`).
4. Ergebnisse aus `handoff_local/results/wave4_<timestamp>/` in eine neue
   Session hochladen — die Auswertung gegen die Registry (gate-auditor,
   H-09/H-10/H-12 unter der F-XDOM1-Beide-Stufen-Regel) läuft dann
   automatisch.

**Erwarteter Ausgang heute:** H-11 und H-13 werden voraussichtlich noch als
GESPERRT zurückkommen (H-11 braucht ≥730 Tage lückenlosen Backfill, H-13
braucht 2 vol-regime-disjunkte IV-Snapshot-Tage im erst seit ~2026-06-16
laufenden Deribit-Live-Stream) — das ist der korrekte, erwartete Ausgang,
kein Fehler. H-09/H-10/H-12 sollten echte Verdikte liefern.

## Was inhaltlich passiert ist (Phasen A–E)

| Phase | Ergebnis |
|---|---|
| A — Registry-Brücke | H-09..H-13 wörtlich aus `edge-research-v3/results/` in `hypothesis_registry.md` übernommen (DEC-19). |
| B — Bau | 5 Module (`c09_bunch`, `c10_pointer`, `c11_anen`, `c12_frag`, `c13_tailshape`) + CLI + T2-Runner + Tests, gegen synthetische Harvester-Bäume verifiziert. |
| C — Adversarial-Audit | 5 unabhängige, frische Fable-5-Prüfungen (nicht die Bauenden) gegen Registry/`hardened_hypotheses.md`. Verdikte: H-09 FAIL, H-10 FAIL, H-11 FAIL (1 kritisch), H-12 PASS-WITH-NOTES, H-13 PASS-WITH-NOTES. Volltexte: `state/audit_h09.md`..`audit_h13.md`. |
| D — Fix-Loop | Alle Befunde in Runde 1 (von max. 2 gedeckelten Runden) behoben, erneut getestet, committed. |
| E — Konsolidierung | `run_wave4.{ps1,sh}` gebaut; F-XDOM1 (zweite BH-FDR-Stufe für den Kohorten-Lauf H-09/H-10/H-12) vorregistriert (DEC-22) — das war eine bindende Vorbedingung aus der Registry, kein optionaler Schritt. |

## Der wichtigste Einzelbefund

H-11s Statistik-Kern hatte einen kritischen Fehler: die Analog-Ensemble-
Prognose wurde als Punktschätzer (Mittelwert der 20 Analoga) bewertet statt
als die registrierte VERTEILUNG (echtes CRPS). Das hätte den Lauf gegen die
eigene Pre-Registration nicht adjudizierbar gemacht. Gefunden vom
unabhängigen Audit, gefixt, mit einer eigenen Charakterisierungs-Test
dokumentiert, warum das Gate zusätzlich Bootstrap-Signifikanz verlangt statt
sich auf CRPSS allein zu verlassen. Da H-11 heute ohnehin gesperrt ist,
hatte der Fehler keine Live-Konsequenz — aber er wäre beim ersten
tatsächlichen Lauf nach Entsperrung falsch gewesen.

## Bekannte offene Punkte (bewusst zurückgestellt, dokumentiert)

Keiner davon ist Gate-relevant oder blockiert den heutigen Lauf. Vollständige
Liste in den jeweiligen Audit-Reports; die wichtigsten:

- H-09: Fill-Level-Robustheits-Mitbericht fehlt noch (nur Order-Level
  implementiert) — nicht urteilstragend.
- H-11: PIT/Rank-Histogramm ist jetzt implementiert; die Manifest-basierte
  Entsperr-Prüfung nutzt jetzt `harvest_manifest.sqlite` primär.
- H-13: Lognormal-Weibull-Mixture-Sensitivität (registriertes Anti-Gaming-
  Artefakt) ist noch nicht gebaut — als offener Punkt vermerkt, kein
  stilles Weglassen.
- Ein geerbter SQL-Operator-Präzedenz-Bug in `c01_ofi_sign/oos.py`
  (Bestandscode, auch von H-05b/H-05c genutzt) wurde identifiziert, aber
  bewusst NICHT angefasst (eigenes WP, Schutzgut-Prozess nötig).

## Programmstand insgesamt

Vor Welle 4: 9 DROP, 2 PARK, 2 kapitalfreie WEITER, 0 handelbare Kanten
(`PROGRAM_FINAL_REPORT.md`). Welle 4 fügt 5 neue, noch nicht verdikt-
entschiedene Messfragen hinzu — der heutige `run_wave4`-Lauf liefert die
ersten echten Zahlen für H-09/H-10/H-12.

## Vollständige Quellen

- `state/wave4_state.md` — Phasen-Log + Changelog mit allen Commit-Hashes.
- `state/audit_h09.md` .. `audit_h13.md` — volle Audit-Berichte.
- `state/decisions.md` — DEC-19 bis DEC-22 (Registry-Brücke, Modell-
  Routing, F-POINTER-dvol-Interpretation, F-XDOM1).
- `handoff_local/README_WAVE4.md` — technische Runner-Dokumentation.
