# Auftrag: A2-Registrierungsentwurf unter Verfassung 3.1 (DEC-107 N1 (3); E7 (d) Zustandsmaschine) - 2026-11-04

Rolle: Herleitung. Du schreibst einen **Entwurf** der Registrierung (der Orchestrator registriert, nach Review). Nichts im Repo
aendern, nichts committen, **keine Marktdaten** (kein harvest_data, keine Extrakte unter /home/user/scinance_work), keine
Siegeldatei (`state/runs/*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`), kein Mittel und kein
Vorzeichen von r_pre-Kontrasten irgendeiner Periode. Rollen statt Modellnamen, keine Hostnamen, ASCII, Deutsch (YAML-Schluessel
wie im Template). Ausgabe nach `<herleitung_a2/registrierung>/`:
A2_REGISTRIERUNGSENTWURF_3_1.md (Herleitung je Pflichtzeile), a2_registration_3_1.yaml (**muss den Linter bestehen**),
calc/a2_reg_calc.py (+ .out, .json: OC-Zeile, Schutzzeile, Blickplan-Grenzen, Jahresbuch, Strenge-Quotient; feste Seeds).

## Pflichtlektuere (Pfade unter /home/user/scinance/)
1. `scinance3-impl/PRD_SCINANCE3_v3.md`: Kopf 0.1, Abschnitt 2 (VR-b*, VR-c*, VR-d*, VR-e04..VR-e12, VR-f*), Abschnitt 3 (PZ-01..PZ-30,
   YAML 3.3), Abschnitt 4.2 (A2).
2. `scinance3-impl/state/decisions.md`: DEC-103 (+N1) A2-Design, DEC-104 (E2..E8, N1, N2, N4), DEC-105, **DEC-107 (1), (2) BE-04,
   Nachtrag 1 (1)-(3)**.
3. `scinance3-impl/state/herleitung_a2/NULL_SIMULATION_A2.md` (SE, Null, Gate-(4)-Faktor, Pilot-Route; nur Streuungen, keine
   Mittel lesen - falls dort Mittel/Vorzeichen stehen, nicht zitieren).
4. `scinance3-impl/state/feasibility/A2.yaml` und der Rechner `src/bybit_edge/research/feasibility31/` (ausfuehren:
   `PYTHONPATH=src python3 -m bybit_edge.research.feasibility31.cli scinance3-impl/state/feasibility/A2.yaml --format md`).
5. `scinance3-impl/state/herleitung_stabilitaetstest/HERLEITUNG_STABILITAETSTEST.md` Abschnitte 1, 2, 4, 6.1, 7.
6. `scinance3-impl/state/registered/TEMPLATE_3_1.yaml`, Linter `src/bybit_edge/research/registry31/` (lint.py, schema.py; Aufruf
   siehe `tests/unit/test_registry31.py` - ggf. `python3 -c "from bybit_edge.research.registry31 import lint; ..."`).
7. `scinance3-impl/state/FENSTERREGISTER.md` (Zonen je Familie, Abschnitt 6, 9, 10; A2-Ausnahme Zone V), `state/KONTO_ZONE_X.md`,
   `state/hypothesis_registry.md` (Kopf-Nachtrag), `state/gate_log.md` (GL-036 als Praezedenz), `state/DATENANNAHMEN_REGISTER.md`
   Zeilen 1, 5 (Negativ-Panel XRP/BNB/SOL erledigt), 12.

## Zu leisten
1. YAML nach Template 3.1, Variante (c): `decision_rule` mit `stability_test` (alpha 0,05, kostenquote_q je Blickplan aus
   stab_results.json s4/s4b, entfaellt <= 12 Monate, an jedem Wirksamkeits-Stopp), `screen: null`; Schwelle t-artig aus der
   Konfirmations-SE (DEC-104 N2 (7); DEC-107 N1 (2)) mit Null-Quantil-Boden (VR-e12); `looks`: Zone V ein Blick (W1/W2, A2-Ausnahme),
   Zone K Quartalsblicke 2027-04-01, 2027-07-01, 2027-10-01, 2028-01-01, O'Brien-Fleming alpha 0,0025, Futility; `sesoi_curve`
   22 bp Taker (Gabelung Maker 10,8 bp als Etikett); `nuisance` nach BE-04 (bindend: juengstes Vorfenster 2023-07-01..2024-06-30,
   **SE dort "nachzuliefern durch den Orchestrator, Konto-Eintrag" - Platzhalterwert 7,58 aus der Null-Simulation W2 mit
   Sensitivitaet 7,34 / 8,52**), Stress als Sensitivitaetszeile; `oc_line` mit p_pass_0, p_pass_sesoi, p_pass_prior_median,
   **p_pass_nur_aelter_1mde** (Schutzzeile; simulieren), seeds; `strictness_ratio` mit Zerlegung; `annual_book` 2027;
   `economic_minimum`, `decision_relevance`, `capital_tax_venue` (Steuer UNBELEGT), `stress_episode` (STRESS_ABS-Tage in den
   Fenstern zaehlen aus `state/runs/stress_abs.json` - nur Daten), `irreversibility_probe`, `positive_control` (Kriterium nach
   DEC-103 N1 (8e)), `prior_label` (UNBELEGT, Spanne 5..25 bp), `selection.K` (Konto-Inventar: A2-Varianten zaehlen, DEC-103 N1),
   `c_overlap` 1,3177, `n_eff`, `lesestatus`, `c17_refs` (Oeffnungen aus dem Konto-Inventar, die A2 betreffen), `windows` mit Zonen.
2. Je Pflichtzeile ein Absatz Herleitung mit Fundstelle; Zahlen aus dem Rechner oder eigener Rechnung (nachvollziehbar).
3. Feasibility-Satz: MDE80 je Blick (V allein 24 Monate: 23,08 bp; K1 2027-04-01: 20,64 bp bzw. 20,95 bp mit GSD-Aufschlag),
   Entscheidung fruehestens 2027-04-01; Stress-Sensitivitaet.
4. Gabelungsregister: alle Festlegungen mit Alternative und Richtung (Testbarkeit/Strenge).
5. Was nicht folgt; Kurzfassung <= 12 Zeilen; Liste der offenen Punkte fuer den Review und fuer den Orchestrator (Vorfenster-SE,
   Negativ-Panel-Probe, Positivkontroll-Fixture).
