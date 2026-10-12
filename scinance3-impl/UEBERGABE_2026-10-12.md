# Scinance 3.0 - Uebergabe (Stand 2026-10-12)

> Ergaenzt `UEBERGABE_2026-10-09.md` (Rollen, Regeln, Fallen, Datei-Landkarte gelten weiter).
> Hier nur, was sich seither geaendert hat und was als Naechstes kommt.

## 1. Arbeitsweise seit 2026-10-10 (DEC-83, Nutzer-Auflage)

- **Cloud-first:** gerechnet wird in der Cloud-Sitzung; alle Daten kommen vom Thin Client (Data-Harvest).
  Nutzer-PC/Autopilot nur noch Rueckfall. Laengere Laeufe als Hintergrundprozess der Sitzung.
- **Bybit-REST ist aus der Cloud geo-gesperrt** (CloudFront, US-Region) - nicht per Allowlist loesbar.
- **Panel `panel_1d` + `panel_1d_delisted`:** liegt im Harvest-Archiv unter festem Schluessel
  `exports/scinance/INDEX.json` -> `scinance_panel_1d_2026-09-28.zip` (Data-Harvest DEC-45,
  `state/ANTWORT_DATA_HARVEST_PANEL_2026-10-12.md`). Nur exakte Schluessel lesen, Groesse + SHA256 pruefen,
  Zip hat Windows-Pfadtrenner -> mit Pfadpruefung in ein frisches Sitzungsverzeichnis entpacken (nie ins Repo,
  nie unter `data/harvest`), dann `--panel-base <dir>/panel_1d --delisted-base <dir>/panel_1d_delisted`.
  Stand reicht fuer WP-13 vollstaendig (Fenster enden 2026-06-30). Variante B (taeglicher Panel-Strom auf dem
  Thin Client) ist beim Data-Harvest-Projekt in Arbeit; Abweichungen angenommen (DEC-84).
- **Branches:** jede Cloud-Sitzung hat einen eigenen Branch; Commits zusaetzlich per Fast-Forward auf
  `claude/subagent-prd-development-T16fE` pushen (Merge-Commit, falls der Autopilot dort etwas gepusht hat).

## 2. Was seit 2026-10-09 passiert ist

| DEC | Inhalt |
|---|---|
| 81 | Kalibrierung: Suche mit gemeinsamen Zufallszahlen, Gegenprobe auf Standardfehler-Basis, realer Querschnitt; `beta_characteristic` bitgleich ~36x schneller |
| 82/84 | Erweiterte V-1: I skaliert exakt mit dem Intervall (Totzonen-Klumpen 1h/2h/4h/8h exakt bei 0,00125/0,0025/0,005/0,01 %); Auto-Switch seit 2025-10-30: 1h-Episoden kurz (Median 8 Tage, 129 Symbole), Rueckwechsel meist auf 4h (`state/runs/v1x_20261012/`) |
| 83 | Cloud-first |
| 85 | Gate-Audit-VETO gegen v5c ("keine Methode"): simulierte Marktspalte verfehlte DEC-77-Ziele (D1), Null-Renditen statt NaN (D2); v5d vorab fixiert, bindend |
| 86 | **v5d: vier Beta-Kontroll-Methoden bestehen in W1 und W2; registriert wird `fm_neutral_8w`** (`state/runs/wp13a_20261012_v5d/`) |

Tests: 1.992 passed / 3 failed (Legacy `test_execution_live.py`, Sandbox-bedingt, unveraendert) / 9 skipped.

## 3. Ergebnis A3 und naechste Schritte (Stand Abend 2026-10-12)

- **A3 (H-28..H-30, Kohorte F-XSEC1) ist abgeschlossen: GL-032, alle sieben Varianten GL-012 vor dem Lauf.**
  Drittfassung registriert (DEC-90, `state/registered/h28_h30_v3.yaml`), Positivkontrolle in Produktionskonfiguration
  NICHT BESTANDEN (DEC-91): die Power-Zuordnung hatte mit dem Boden-SE statt der registrierten SE gerechnet; mit der
  faktorbedingten IC-Streuung (W1 0,09/0,13 statt Boden 0,049) ist der Test in W1 bei Prior 0,03 zu schwach (Power
  0,47/0,21). Feststellung im registrierten Design, KEIN Verdikt ueber die Effekte. Gate-Audit bestaetigt; kein
  DEC-52-Zweig nachtraeglich (DEC-92). Keine reale IC berechnet, alle Siegel geschlossen.
- **Methodische Lehre:** Power/MDE immer mit der SE-Regel des registrierten Tests inkl. faktorbedingter Streuung unter
  der kalibrierten Null rechnen; Positivkontrolle in Produktionskonfiguration vor jedem Lauf (hat den Fehler gefangen).
- **Naechster Kandidat: A1** (Funding-Long-Bein gegen Universums-Hedge, DEC-70). V-1 ist jetzt empirisch belegt
  (DEC-84). Vor einer Registrierung: Herleitung mit Power auf der realistischen SE (Lehre oben), Positivkontroll-Plan.
- Ein anderes A3-Design (z. B. fm8-neutralisierter IC als Primaerstatistik, gepoolte Fenster) nur als NEUE Hypothese
  mit eigenem K (DEC-58 E2) und mit Offenlegung der gesehenen Zahlen (Etikett C.17).
- Nebenbei: `persistence_null`/`h30_feasibility`/Survivorship auf `returns_est` sind erledigt (DEC-87); offene
  Kosmetik: Docstring `positive_control.py` (Skalen) - aendert den Code-Hash, deshalb erst mit der naechsten Aenderung.
- Data-Harvest Variante B (taeglicher Panel-Strom) beim Data-Harvest-Projekt; bis dahin Zip-Export (Stand 2026-09-28).
