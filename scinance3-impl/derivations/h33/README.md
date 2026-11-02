# derivations/h33 - Herleitung H-33 (beta-neutrales Kurzfrist-Reversal), outcome-frei, aus der H-32-Nuisance

Zweck: Umrechnung der v6b-Nuisance von H-32 auf die NEGATIVE Richtung, Literatur-Prior-Band, Power-Linien und Prior-Gitter (DEC-102
Option (a)). Kein Panel, kein Outcome, kein Harvest-Client.

Dateien: h33_compute.py (Skript sha256 ef0788a0cca30cfa27b3afe53f106ffeea5411237f8f4c0d821c649a2ef346b0, gepinnt in power_h33.json meta.skript und nuisance_neg.json skript_sha256),
SPEC_H33_herleitung.md (Auftrag).

Reproduktion (vollstaendig aus Repo-Dateien moeglich, keine Marktdaten):
  Eingaben (sha256 laut power_h33.json meta.eingaben_sha256):
    h32_v1_yaml     0fadda785f37a9ab24b31f650611a468f5c6bfef8be8fb65a7dc54261c1bbd60
    spread_census   fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083
    v6b_json        f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c
    v6b_replicates  3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef
  Aufruf: python3 -I h33_compute.py <repo_root> <out_dir>   (zweimal, Ergebnis bitgleich; out_dir ausserhalb von state/).
  Ergebnis in der Akte: state/herleitung_h33/power_h33.json (sha256 026494b6681fb3d5b97d0e2cf77c9845b953bde7e31e97f976bbf3207b5b5bc9),
  nuisance_neg.json (sha256 05e6f2a0a396d0be008579e6d160147c2002d7229a176a01c0f2c1b2076f0835),
  ENTSCHEIDUNGSVORLAGEN.md; Review: ../../verify/h33/.

Warnungen:
- Ausgabe in ein eigenes out_dir leiten, nicht auf die committeten JSON (Nuisance-Dateien, DEC-103 N1 (2c)).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
