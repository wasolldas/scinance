# derivations/a2 - Herleitungsskripte A2-Vorarbeit Teil C (EXP-CLOCK, DEC-103) - F0 (DEC-104 E9)

Zweck: Null-Simulation J-(i) (DEC-103 E4) auf der Vorperiode, bindende SE (DEC-94 (5)), Funding-Intervall W2,
Pilot-Uebergaberegel U-A2 (Vorlage). Nur Streuung, Quantil-Abstaende, Zaehlungen, Schwellen, Powers; kein Mittel,
kein Vorzeichen, nie der Kontrast mit den realen Labels (Waechter R-C6, Test `test_c_guards.py`).

Dateien: `c_common.py` (Regeln, Lader, Waechter), `c1_nullsim.py` (C-1), `c2_funding.py` (C-2), `c3_pilot.py` (C-3),
`c_build.py` (Montage a2_teilC.json), `c_tables.py` (Tabellen), `test_c_guards.py` (T0-Tests), `run_all.sh`,
`SPEC_A2_teilC.md` (Auftrag an die Herleitung). Die Skripte sind **byte-identisch** zu den in
`state/herleitung_a2/a2_teilC.json` (`skripte_sha256`) gepinnten Fassungen (vom Orchestrator am 2026-11-02 geprueft);
jede Aenderung bricht den Pin und braucht eine neue Fassung mit neuem JSON.

Reproduktion (nur mit den Datenextrakten ausserhalb des Repos; Marktdaten sind nicht im Repo):
- Eingaben: siehe `data_manifest/EXTRACT_LOG.json` (vier Parquet-Extrakte mit sha256); Repo-Eingaben
  `state/herleitung_a2/a2_vorarbeit.json` und `src/bybit_edge/research/power_p1.py` (Hashes in a2_teilC.json).
- Aufruf: `bash run_all.sh` (pytest der Waechter, zwei volle Laeufe, Bitgleichheits-Vergleich, offizielle JSON).
- Ergebnis im Repo: `state/herleitung_a2/a2_teilC.json` (Fassung 2), `NULL_SIMULATION_A2.md`, `PILOT_ROUTE_A2.md`.

Warnungen:
- `c_build.py` ohne `--out` ueberschreibt die committete `state/herleitung_a2/a2_teilC.json`.
- Pfade sind hart kodiert (`c_common.RAW` / `OUT_DIR` / `POWER_P1` unter `/home/user/...`, Sandbox); `work/` entsteht
  relativ zum Skript und ist per `.gitignore` ausgeschlossen - Laufausgaben nie committen (DEC-103 N1 (2c)).
- Teil A/B (`a2v_*.py`, Review `rv_*.py`) folgen mit F0b in `teilAB/`.
