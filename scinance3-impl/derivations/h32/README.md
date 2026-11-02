# derivations/h32 - Herleitung H-32 (Zwei-Stufen-Design, fm8-Daempfung) und Laufskripte der Vorlaeufe

Zweck: h32_power.py: Power/MDE/Zuordnung/Uebergabeschwelle aus der Nuisance der Akte (v5e-Vorlauf-JSON, WP-7-Wochen-K, A1-Pilotbasis);
sector_check.py: synthetischer Sektor-/Power-Check (keine Marktdaten); assemble.py: Montage power_h32.json. run/: Laufskripte der
Vorlaeufe und des Pilots (rufen scripts/h32_fm8.py bzw. scripts/wp13_xsec.py des Repos).

Dateien: assemble.py, h32_power.py, sector_check.py (je byte-identisch zu den Pins in state/herleitung_h32/power_h32.json, Feld skripte),
SPEC_H32_herleitung.md; run/run_h32_pilot.sh (Pilot, DEC-101 Teil 2), run/run_h32_v6.sh, run/run_h32_v6b.sh (Vorlauf v6b zweimal),
run/run_v5e.sh (wp13a-v5e-Vorlauf, erzeugt state/runs/wp13a_20261012_v5e; das Ergebnis wp13a_prelaunch.json ist in der Akte mit
sha256 94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2 vielfach gepinnt). run_h32_v6.sh und run_v5e.sh sind per Namen nicht in der Akte genannt.

Reproduktion von power_h32.json (aus Repo-Dateien, keine Marktdaten):
  Eingaben: v5e-Vorlauf-JSON (sha256 94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2);
    WP-7-Wochen-K-Reihe decile_degeneration_weekly.csv (nur Spalten week, n_symbols; sha256 7c6119afe3bbaa862acd5f65bfcb3e53ffb8244e7056aba7f5a56df3a0fac9e5); A1-Pilotbasis-Metadaten.
  Aufruf: PYTHONPATH=<repo>/src python3 h32_power.py <repo> <out>; sector_check.py <repo> <power_json> <out>; assemble.py <scratch_dir> <out>.
  Ergebnis in der Akte: state/herleitung_h32/power_h32.json (sha256 f0d6e6d9c55e0a9326ab5b32988eb86bbd0c62ef283b0c3101a4889a402a56a3), ENTSCHEIDUNGSVORLAGEN.md; Review: ../../verify/h32/.

Warnungen:
- run/*.sh NICHT ausfuehren: sie schreiben nach state/runs/ bzw. benoetigen das Panel ausserhalb des Repos; der Pilot ist
  einmalig (DEC-99 (3), DEC-101 E10) und durch die registrierte YAML-sha256 gesperrt. Sie dienen nur als Nachweis, wie die Artefakte entstanden.
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
