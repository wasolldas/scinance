# derivations/a1 - Herleitung A1 (H-31), Stufe 1: Feasibility vor jedem Design (outcome-blind)

Zweck: Fensterzensus, Nuisance (SD, Autokorrelation, Varianzfaktor c), Formations-Sensitivitaet, Power/MDE80 und
Kill-4-CI des Funding-Sortier-Kandidaten A1 auf der Vorperiode. Outcome-Groessen nur fuer Haltewochen, die vor 2024-07-01
enden (Waechter assert_nuisance_holding_week in a1_common.py); keine Woche nach 2026-06-28 wird beruehrt.

Dateien: a1_common.py (Lader, Konstanten, Waechter), a1_explore.py (Union-Panel einmal laden, Cache), a1_window_census.py,
a1_nuisance.py, a1_formation_sensitivity.py, a1_psi_by_class.py, a1_power.py, a1_kill4_ci.py, a1_check_factor.py,
a1_selfcheck.py, a1_bookkeeping.py, a1_model.py, a1_consolidate.py (Montage feasibility.json), run_all.sh,
SPEC_A1_herleitung.md (Auftrag an die Herleitung). Die 14 Skripte sind byte-identisch zu den Pins in
state/herleitung_a1/feasibility.json (Feld skripte). Nicht gepinnt, daher nicht hier: a1_explore2.py (Exploration).

Reproduktion (nur mit dem Panel ausserhalb des Repos; Marktdaten sind nicht im Repo):
  Eingabe: Union-Panel (panel_1d + panel_1d_delisted), geladen ueber den Repo-Lader wp7_universe.panel_load.
    Fingerabdruck laut feasibility.json: union_range_sha256 a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a
                                          delisting_dates_sha256 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933
  Aufruf: sh run_all.sh (beide Konfigurationen A1_EXCL1H=0/1, danach Kill-4, Selbstcheck, Buchhaltung, Montage).
  Ergebnis in der Akte: state/herleitung_a1/feasibility.json (sha256 b4680f7c0b7e58ce9a6fa256f6913656cb8b432b55b40bc915aa0f930ca72d9e; Feld skripte = Pins),
  FEASIBILITY.md, REVIEW_A1.md (Review: ../../verify/a1/).

Warnungen:
- a1_consolidate.py schreibt state/herleitung_a1/feasibility.json (a1_common.OUT): nur in einer Wegwerfkopie des Repos laufen lassen.
- a1_explore.py schreibt cache/a1_data.pkl (Panel-Cache = Marktdaten) neben das Skript: nie committen (.gitignore).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
