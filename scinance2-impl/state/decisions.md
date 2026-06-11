# Entscheidungs-Log (DEC-xx)

> Format: DEC-xx · Frage · Optionen · Entscheidung · Begründung · Rückbauweg
> Keine Entscheidung ohne Eintrag, kein Eintrag ohne Entscheidung. (CLAUDE.md Autonomie-Protokoll §3)

---

### DEC-01 · Wo liegt die Verfassung?
- **Frage:** FINAL_PRD.md lag in `edge-reconciliation/results/`, Framework erwartet Repo-Root.
- **Optionen:** (a) Kopie in Root, Original bleibt; (b) Move; (c) Symlink.
- **Entscheidung:** (a) Kopie in Root.
- **Begründung:** Reconciliation-Artefakte bleiben als abgeschlossener, in sich konsistenter Run unangetastet (Audit-Trail); Root-Kopie ist die Arbeits-Verfassung. Reversibelste Option.
- **Rückbauweg:** Root-Kopie löschen; Original unverändert.
