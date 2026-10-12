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

## 3. Naechste Schritte

1. **Drittfassung H-28..H-30** (Herleitung durch einen Opus-Agenten, adversarisches Opus-Review, dann
   Registrierung durch den Orchestrator): Methode `fm_neutral_8w` mit den v5d-Kalibrierungen; offene Punkte aus
   DEC-86 (bindende Decke, Gap 1 Woche, Faktor 1/sqrt(2)); Gate-Text (1)-(7), zwoelf Pflichtzeilen, T0-T7;
   YAML per `scripts/wp13_xsec.py --emit-registered-template <v5d-json> <yaml>`, sha256 in die Registrierung.
2. **Lauf** `scripts/wp13_xsec.py --run --registered <yaml> --registered-sha256 <hash>` in der Cloud
   (Positivkontrolle zuerst, laut Zustandsmaschine), dann Gate-Check und GL-032.
3. A1 (Funding) danach: V-1 ist jetzt weitgehend belegt (DEC-84); Registrierung vorbereiten.
4. Nebenbei: `persistence_null`, `h30_feasibility`, Survivorship-Fixture nutzen noch die null-aufgefuellten
   Renditen (DEC-85-Builder-Hinweis, nicht urteilstragend) - bei Gelegenheit auf `returns_est` umstellen.
