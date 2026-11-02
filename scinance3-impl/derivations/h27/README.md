# derivations/h27 - Herleitung H-27 (VRP auf DVOL-Backfill), Stufe 1: Feasibility (C.12), Nuisance, Nullwelt, Power

Zweck: Praemien-Reihe (IV minus RV, drei Einheiten S1/S2/S3), Nuisance (SD, ACF, Varianzfaktor c nach Regel P-3), Nullwelt-
SE, Power/MDE80 und Datenproben (Katalog, Schema, DVOL, Panel-Konvention). Nur Nuisance der Vorperiode; kein Praemien-Mittel.

Dateien: h27_common.py (Lader, Waechter, Client-Anbindung), h27_series.py, nuisance.py, nullworld.py, power_h27.py,
panel_coverage.py, catalog_check.py, catalog_check2.py, conv_check.py, dvol_probe.py, schema_probe_stream.py,
SPEC_H27_herleitung.md (Auftrag). Alle 11 Skripte sind byte-identisch zu den Pins in state/herleitung_h27/feasibility.json
(skripte_sha256; Stand 2026-10-13 ueberholt: 4 davon, gleiche sha256).

Reproduktion (nur in einer Sitzung mit Archivzugang; Marktdaten sind nicht im Repo):
  Eingabe: Data-Harvest-Archiv ueber den fremden Client (Geschwisterordner harvest_client/ mit harvest_data.py; bleibt ausserhalb
    des Repos, enthaelt Zugangs-Doku). Zugang ausschliesslich ueber die Umgebungs-Secrets HARVEST_S3_ENDPOINT / HARVEST_S3_ACCESS_KEY /
    HARVEST_S3_SECRET_KEY; die Skripte enthalten weder Host noch Schluessel. Katalog-Fingerabdruck: partitions_sha256 031bc30871cd06d893bcce1f9a01bacbb7e1512f242ad8ec544dfa041e14c7d7.
  Aufruf: je Skript python3 -I <skript>.py im Skriptordner (Cache hcache/ entsteht daneben; Marktdaten, nie committen).
  Ergebnis in der Akte: state/herleitung_h27/feasibility.json (sha256 097a7966cfbf83c297d4dc934fc8fbd01d4e612efb45c67b8ba591337d389319), FEASIBILITY.md, DATENPROBE.md,
  KONTAMINATION.md; Review: ../../verify/h27/. Die HF-RV-Fortsetzung steht in ../hfrv/ (nutzt dieselben Module).

Warnungen:
- Ausgaben (nuisance.json, power.json, *.log) entstehen im Skriptordner: nie committen (DEC-103 N1 (2c)).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
