# Hypothesen-Registry (PRD §8 — Pflicht vor jedem Gate-Lauf)

> Regel: Hypothese, Schwellwerte, Fenster und FDR-Familie werden HIER festgeschrieben,
> BEVOR der zugehörige Validierungslauf startet. Keine Post-hoc-Schwellenanpassung.
> Der gate-auditor hat Veto gegen jeden Lauf ohne registrierten Eintrag.

## Registrierte Hypothesen

### H-01 · E-15 / CS-03 (S3 Pre-Settlement, iter-5-Fixes)
- **Registriert:** 2026-06-10 (vor Lauf-Start; Tore aus verdict.md §Welle-1 wörtlich, im PRD §3 übernommen)
- **Hypothese:** Mit korrigiertem Time-Stop (Tick-Zeit) und friction-aware Hard-Stop steigt die S3-Netto-Edge messbar; die Tail-Verluste (E-10) verschwinden.
- **Gate (vorregistriert):**
  - time_stop_exceeded-Count: 1 → erwartet ~60-70 (Fix-Wirksamkeit)
  - n>120s-Trades: 68 → erwartet ~0
  - n<-30bps-Trades: 33 → erwartet ~0
  - **WEITER:** aggregierte Netto-Edge ≥ -5 bps UND E-17-Divergenz geklärt
  - **DROP:** aggregierte Netto-Edge ≤ -10 bps
  - **GRAUBEREICH:** dazwischen → ein (1) weiteres vorregistriertes Fenster, dann endgültig
- **Fenster:** 5 Symbole (BTC/ETH/SOL/BNB/XRP), ~24h-Replay, single-pass
- **FDR-Familie:** F-S3 (einzelner konfirmatorischer Test, keine Korrektur nötig — aber Folge-Tests an S3 zählen in diese Familie)
- **Status:** Lauf beim User in Arbeit; Ergebnis via handoff_local erwartet

(Weitere Hypothesen werden in Phase 2 PLAN registriert, bevor ihre Läufe starten: C-42-Repro, C-31-CFAR.)
