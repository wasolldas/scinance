# Scinance - Einstieg

Neue Sitzung? Zuerst lesen:
1. `scinance3-impl/UEBERGABE_2026-10-09.md` - Stand, offene Arbeit, Autopilot, Datenzugang.
2. `scinance3-impl/CLAUDE.md` - Verfassung von Scinance 3.0 (bindend).

Harte Regeln, auch bevor du weiterliest:
- Das Repository ist oeffentlich: nie Zugangsdaten, nie den Hostnamen des Heim-Datendienstes ins Repo, in Commits oder Logs.
- Zugangsdaten nur aus Umgebungs-Secrets (`HARVEST_S3_*`), nie aus Chat oder hochgeladenen Dateien.
- Nie unter `data/harvest` schreiben. Kein Live-Order-Code.
- Versiegelte Dateien unter `scinance3-impl/state/runs/` (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`) nicht oeffnen.
- Arbeitsbranch: `claude/subagent-prd-development-T16fE`.
