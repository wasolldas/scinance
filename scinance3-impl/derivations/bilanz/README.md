# derivations/bilanz - Programm-Bilanz P-2: Power-Zensus ueber die verbleibenden Kandidaten

Zweck: Power/MDE/Zuordnung je Kandidat aus den Nuisance-Groessen der Akte (kein Outcome, kein Panel, keine DVOL-/Trade-Daten);
alle Power-Zahlen laufen ueber bybit_edge.research.power_p1 (DEC-94 (8)); Tabellen im Markdown.

Dateien: bilanz_census.py (sha256 4f90415f428e022cb9a8f32326eba2ad008e70fc3350b3507e54ad6612c34bfb, gepinnt in programm_bilanz.json Feld skript), make_tables.py (liest
programm_bilanz.json, schreibt tables.md; nur per Name in PROGRAMM_BILANZ_2026-10-18.md genannt), SPEC_BILANZ_power_zensus.md (Auftrag).

Reproduktion (aus Repo-Dateien, keine Marktdaten):
  Eingaben (programm_bilanz.json quellen_sha256):
    wp13a_20261012_v5e/wp13a_prelaunch.json  94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2
    herleitung_a1/feasibility.json           b4680f7c0b7e58ce9a6fa256f6913656cb8b432b55b40bc915aa0f930ca72d9e
    herleitung_h27/feasibility.json          097a7966cfbf83c297d4dc934fc8fbd01d4e612efb45c67b8ba591337d389319
    wp7_20260921/wp7_report.json             eb79a63b64c21651f97d6aabe2c0e2b3fba07ccabf8489201ba697cc05d27e6f
  Aufruf: PYTHONPATH=/home/user/scinance/src python3 -I bilanz_census.py, danach python3 -I make_tables.py.
  Ergebnis in der Akte: state/programm_bilanz.json (sha256 c4b2970251f8933920fff057b921056376e74c6521455bacf04eddfe8748cb4f), PROGRAMM_BILANZ_2026-10-18.md,
  REVIEW_PROGRAMM_BILANZ_2026-10-18.md; Review: ../../verify/bilanz/.

Warnungen:
- bilanz_census.py schreibt state/programm_bilanz.json direkt (OUT_JSON) und ueberschreibt die committete Datei: nur in Wegwerfkopie.
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
