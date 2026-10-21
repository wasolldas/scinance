# H-32 - Registrierungsentwurf (Orchestrator, 2026-10-21, nach Vorlauf v6) - NICHT registriert, wartet auf den Gate-Review

> Grundlage: `ERSTFASSUNG_H32_entwurf.md` (Stand nach Review, Abschnitte 1, 2, 4, 9, 10, 11), `REVIEW_H32.md`
> (ZUSTIMMUNG MIT AUFLAGEN, eingearbeitet), DEC-99 (+N1), DEC-100 (+N1), Vorlauf v6 `state/runs/h32_20261021_v6/`
> (result_sha256 `2ae9bad63a69580d551183764579318f7e5f82f1bc050a30c9bd470c09dd6fa0`), Template
> `h32_v1_TEMPLATE.yaml` (sha256 `bddfb9cb8213fefee20a19cf4eb091be1058359732552732a061bea0b2a28d90`).
> Registriert wird erst nach `REVIEW_REGISTRIERUNG_H32.md` ohne offenes VETO: dann Kopie des Templates nach
> `state/registered/h32_v1.yaml`, sha256 in Registry und DEC, Code-Commit = HEAD.

## 1. Vorbedingungen (Erstfassung 0) - Stand

| # | Vorbedingung | Stand 2026-10-21 |
|---|---|---|
| V1 | DEC-99 | beschlossen 2026-10-20 (+N1 p-Konvention) |
| V2 | EV-2..EV-8 | entschieden durch den Orchestrator wie in der Erstfassung kodiert (Abschnitt 3 unten), DEC-101-Entwurf |
| V3 | Bau B-0..B-6, Abnahme | f7dd471, a3106f5, 716191b, 9364993; `tests/unit/test_h32*.py` + `test_power_p1.py` 196 passed (2026-10-21) |
| V4 | Vorlauf v6 | gelaufen 2026-10-21 13:28..15:28 UTC, rc 0, Panel-Schnitt 2026-06-28 (82 Tage entfernt), 1.000 Replikate, 1.000 Bootstrap, 10.000 p-Replikate, Seed 53 |
| V5 | `state/registered/h32_v1.yaml` + sha256, Code-Commit | offen (nach Review) |
| V6 | Review ohne VETO | offen (`REVIEW_REGISTRIERUNG_H32.md`) |
| V7 | Daten | **geaendert (DEC-100 N1):** Ueberlebenden-Baum aus dem Zip 2026-09-28 (sha256 03dc0e7c...6b16cb) + Delisted-Baum v2 aus `rest.kline1d`/`rest.fundingRateAll` und Register `bybit/delisting_dates` 2026-10-21; Fingerprints: union_range `e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589`, delisting_register `a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22`, delisted_tree `250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401`, delisting_dates `c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3` |
| V8 | Blind-Siegel / Panel-Schnitt | Waechter im Code; v6-Artefakt: letzte Woche 2026-06-22 |

## 2. Vorlauf v6 - Kernzahlen (eingefroren; Orchestrator-Nachrechnung `scratchpad/orch_check/h32_v6_power.py`)

| Fenster | Formationswochen | w_judged | K min/Median/max | floor_fm8 | v_fm8 |
|---|---|---|---|---:|---:|
| P | 2022-04-18..2024-06-17 (Outcome bis 2024-06-24, Panel <= 2024-06-30) | 114 | 127 / 213 / 353 | 0,068771 | 0,004804 |
| W1 | 2024-07-01..2025-06-23 | 52 | 360 / 440 / 536 | 0,047441 | 0,002258 |
| W2 | 2025-07-07..2026-06-15 | 50 | 537 / 590 / 603 | 0,041552 | 0,001727 |

Kalibrierung (nur Streuung/Autokorrelation/Faktoranteil): P stress rho_f 0,2352 / beta_sd 0,5277; W1 measured 0,0462 /
0,5366, stress 0,0925 / 0,7129, zero 0 / 0,5396; W2 measured 0,0702 / 0,4415, stress 0,1404 / 0,5705, zero 0 / 0,4415;
alle Gegenproben ok. m_P (stress, Richtung): mom1 0,002176, mom2 0,003274, mom4 0,004296, rev_gap -0,002540.

| Fenster | Variante | se_mean | e_se_rule | sd_week | null_mean | q95 | T_W,v = z x e_se_rule + max(0, null_mean) | ceiling_k4 / T |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| W1 | mom1 | 0,006982 | 0,007250 | 0,050019 | +0,001101 | 0,012655 | 0,01303 | 0,584 |
| W1 | mom2 | 0,007723 | 0,007968 | 0,055793 | +0,001344 | 0,014786 | 0,01445 | 0,526 |
| W1 | mom4 | 0,009397 | 0,009313 | 0,065547 | +0,001835 | 0,017766 | 0,01715 | 0,443 |
| W1 | rev_gap | 0,007098 | 0,007235 | 0,049802 | -0,000800 | 0,010149 | 0,01190 | 0,639 |
| W2 | mom1 | 0,006389 | 0,006406 | 0,043140 | +0,001238 | 0,011792 | 0,01177 | 0,592 |
| W2 | mom2 | 0,007357 | 0,006902 | 0,047323 | +0,001626 | 0,014182 | 0,01298 | 0,537 |
| W2 | mom4 | 0,008621 | 0,007900 | 0,054706 | +0,002172 | 0,017004 | 0,01517 | 0,460 |
| W2 | rev_gap | 0,006444 | 0,006374 | 0,043002 | -0,001107 | 0,008571 | 0,01048 | 0,665 |

ceiling_k4: W1 0,007602, W2 0,006975 -> **kein Vor-Verdikt-Kill** (Decke/Schwelle 0,44..0,67, Erstfassung 1.10).
bounce_sigma_true W1 0,172364 / W2 0,132020; Survivorship (Schwellen-Einheiten) W1 mom1 -0,696, rev_gap -0,507; W2
-0,823 / -0,518. Stress-Abdeckung (Datumsfilter <= 2026-06-28): W1 rel 22 / abs 2 Tage, W2 rel 8 / abs 1.
p-Replikate: R 10.000, Datei-sha256 `f10250dda8e842c7e748e758cad97926361edc30011c43b18c84a70e02847a62`, Zelle je Fenster/
Variante = groesseres Null-Mittel (mom*: drifting; rev_gap: driftfree).

**Power-Zeile vor dem Pilot (Erstfassung 1.8/1.9; SE_T = e_se_rule, SD_T = se_mean, z_krit 1,6449, z_80 0,8416):**

| Variante | MDE80 W1 | MDE80 W2 | MDE80* (max) | m* = max(0, m_P, m_W1, m_W2) | Uebergabeschwelle auf x_P | Endpower an der Schwelle, m = 1 / 2 / 3 / 4 / 11 | A3-Praxis MDE80 W1 |
|---|---:|---:|---:|---:|---:|---|---:|
| mom1 | 0,01780 | 0,01591 | 0,01780 | 0,002176 | **0,01998** | 0,757 / 0,680 / 0,560 / 0,479 / 0,252 | 0,0239 |
| mom2 | 0,01961 | 0,01754 | 0,01961 | 0,003274 | **0,02288** | 0,786 / 0,716 / 0,605 / 0,528 / 0,300 | - |
| mom4 | 0,02323 | 0,02025 | 0,02323 | 0,004296 | **0,02752** | 0,799 / 0,735 / 0,631 / 0,558 / 0,335 | - |
| rev_gap | 0,01787 | 0,01591 | 0,01787 | 0 | **0,01787** | 0,699 / 0,617 / 0,493 / 0,414 / 0,203 | 0,0240 |

(Erstfassung-Vorabwerte aus v5e: 0,0206 / 0,0237 / 0,0287 / 0,0195 - v6 liegt mit dem vollstaendigen Panel um 3..8 %
darunter; Richtung: mehr Symbole, kleinere Null-Streuung.) Der Pilot kann die Schwellen nur erhoehen (SE_W,Pilot).

## 3. DEC-101 (Entwurf) - Registrierung H-32: Entscheidungen des Orchestrators zu EV-2..EV-8, Abweichungen, C.17

- **EV-2 (Fenster):** P 2022-04-18..2024-06-17 (Formation; K_t >= 117 ab 2022-04-18), Pilot-Panel <= 2024-06-30; W1
  2024-07-01..2025-06-30 (52); W2 2025-07-01..2026-06-28 (50, DEC-99 (8)); Panel-Schnitt vor jeder Rechnung [EV-2b].
- **EV-3 (Varianten, K):** K = 4 (mom1, mom2, mom4, rev_gap); keine H-30-Varianten; BH-Nenner 4; F-WEEK m nach DEC-99 (7)
  mit Doppelausweis 11.
- **EV-4 (Universum):** keine Universums-Variante (U0); Union-Panel, PIT-Maske DEC-72.
- **EV-5 (SE der Power-Zeile):** SE_T = e_se_rule (v6), SD_T = se_mean (v6), jeweils max mit SE_W,Pilot; Null-Mittel-
  Gutschrift m* = max(0, m_P, m_W1, m_W2).
- **EV-6 (Uebergaberegel):** U-2 (Erstfassung 1.8 woertlich), Prior-Lesart A (Pilot-Punkt), Pflicht-Doppelausweis mu_sel
  und A3-Praxis; genau ein Pilotlauf.
- **EV-7 (Test):** Schwelle max(z_krit x SE_W, q95_W,v), SE-Regel P-1 (4), p aus Null-Replikaten (DEC-99 N1), Max-p W1/W2,
  Etiketten Bounce/Liquiditaet/Survivorship; nicht gerechnet: roher IC, Lag-Profil, Beta-Kalibrierungs-IC, DEC-52-Zweig.
- **EV-8 (Positivkontrolle):** Erstfassung Abschnitt 4 woertlich (Welt-SD an F2_real, Injektion auf den realisierten
  Effekt, Urteils-Seeds 53..252, Kriterien (a)-(d)); vor dem Test, nach dem Pilot.
- **Abweichungen (Erstfassung 9, ergaenzt):** 10. Delisting-Datum = letzter Handelstag aus `bybit/delisting_dates`
  (DEC-100 E1) statt Announcement-Datum; Announcement bleibt Etikett. 11. Panel vollstaendig (Delisted-Baum v2, DEC-100
  N1): W1 ist nicht mehr v5e-identisch (5 Symbole mehr), die W1-Determinismus-Kontrolle gegen v5e (Review H-32 B-6)
  entfaellt mit Grund; Ersatz: T2-Determinismus-Tests auf Fixtures, Zweitbau des Baums bitgleich; ein v6-Zweitlauf ist
  optional (2 h) und nicht Bedingung. 12. p-Konvention: Null-Replikate statt Block-Permutation (DEC-99 N1) - ersetzt
  Erstfassung 9.8 und 1.10; Block-Permutation report-only. 13. Fingerprints wie V7 oben; `delisting_register_sha256`
  und `delisted_tree_sha256` sind neue Pflicht-Pins. 14. Pilot-Vorabwert W_P 114 bestaetigt (v6: 114 geurteilte Wochen;
  das Log zaehlt 115 Kalenderwochen inkl. der Outcome-Woche 2024-06-24).
- **C.17 (gesehen, nicht ergebnisnah; Stand 2026-10-21):** aus v6 nur Nuisance (Streuung, Autokorrelation, Faktoranteil,
  Null-Quantile, K-Reihen, Stress-Zaehlungen); aus DEC-100 N1 nur Symbol-/Datumslisten, Zaehlungen je Tag und die
  Gleichheit von Tagesschluessen als Zaehlung; aus DEC-98 N5 nur VRP-Nuisance (BTC/ETH-Vol, kein Querschnitt); aus
  der A1-/H-27-Akte die bereits gelisteten Groessen (Beta-Kalibrierungs-IC, Lag-Profil, Survivorship-Differenz, Streuungen,
  Literatur-Band). Kein realer fm8-IC, kein roher IC einer Variante in P, W1 oder W2 wurde je berechnet.
- **Etiketten:** "zugelassen nur durch DEC-99 (Pilot-Prior)", "fm8-Skala (Daempfung ~25 %)", "beschlossen nach GL-032..034".
- **Was nicht folgt:** kein Verdikt; der Pilot ist nicht gelaufen; W1/W2 bleiben blind.

## 4. Registry-YAML-Block (Erstfassung 10, aktualisiert auf v6)

```yaml
id: H-32
kohorte: A3 / F-H32
klasse: W
capital_free: true
hypothese: "Mindestens eine von mom1, mom2, mom4 (positiv) bzw. rev_gap (negativ): mittlerer woechentlicher Rank-IC der Charakteristik gegen das fm_neutral_8w-neutralisierte Folgewochen-Outcome in W1 UND W2 in Richtung >= z_krit * SE (P-1) und >= 95-%-Null-Quantil; getestet nur nach Uebergabe durch den Pilot 2022-04-18..2024-06-17 (Regel U); bestaetigt durch F-WEEK-BY."
ertragsquelle: "Prognose (mom: spaete Trendfolger; rev_gap: Liquiditaetsbereitstellung) - netto Markt-Beta"
metric: "Mittel des woechentlichen Spearman-IC (Charakteristik_t vs. fm8-Residuum der Folgewochen-Log-Rendite_t+1, close_at_last, min 10) ueber die geurteilten Wochen; fm8-Skala (Daempfung ~25 %)"
richtung: {mom1: positiv, mom2: positiv, mom4: positiv, rev_gap: negativ}
windows:
  - {id: P,  von: 2022-04-18, bis: 2024-06-30, wochen_geurteilt: 114, rolle: pilot_nicht_urteilstragend, panel_schnitt: 2024-06-30, K_min_median_max: [127, 213, 353]}
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen_geurteilt: 52, rolle: urteilstragend, K_min_median_max: [360, 440, 536]}
  - {id: W2, von: 2025-07-01, bis: 2026-06-28, wochen_geurteilt: 50, rolle: urteilstragend, panel_schnitt: 2026-06-28, K_min_median_max: [537, 590, 603]}
fenster_regel: "C10_hart (Regel U laesst nur C10 zu)"
threshold: {formel: "max(1.6449 * SE_W, q95_W)", SE_W: "max(floor_fm8/sqrt(W), SD/sqrt(W), SE_stat stationaer Block 4)", ref: "ERSTFASSUNG 1.9; v6 frozen_v6"}
structural_null: {komponenten: [faktorerhaltende_null_stress_fm8, q95_driftfrei_und_drift, selektionsdecke_k4_vorzeichenbereinigt, bounce_rev_gap], ref: "v6 windows.<W>.frozen_v6", kill_check: "ceiling_k4 / T_W,v 0.44..0.67 -> kein Vor-Verdikt-Kill"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z_krit: 1.6449
  mde_faktor: 2.4865
  cluster_unit: kalenderwoche
  se_schwelle: "e_se_rule (v6), max mit Pilot-Quelle"
  sd_streuung: "se_mean (v6), max mit Pilot-Quelle"
  n_eff: "W/c, c = max(1, c_hat) aus v6 und Pilot"
  a_priori_effekt: "Pilot-Punkt x_P je Variante (DEC-99 (6), Lesart A); Doppelausweis mu_sel (DEC-99 (3))"
  detectable_effect_mde80_v6: {W1: {mom1: 0.01780, mom2: 0.01961, mom4: 0.02323, rev_gap: 0.01787}, W2: {mom1: 0.01591, mom2: 0.01754, mom4: 0.02025, rev_gap: 0.01591}}
  handover_threshold_on_pilot_point_v6: {mom1: 0.01998, mom2: 0.02288, mom4: 0.02752, rev_gap: 0.01787}
  end_power_f_week_at_threshold_v6: {m1: [0.70, 0.80], m4: [0.41, 0.56], m11_report_only: [0.20, 0.34]}
  zuordnungsregel: "Regel U (ERSTFASSUNG 1.8), power_p1.assign_regime; Doppelausweis assign_regime_a3_practice"
  ref: "state/runs/h32_20261021_v6/h32_prelaunch.json; state/herleitung_h32/REGISTRIERUNG_H32_entwurf.md Abschnitt 2"
selection: {K: 4, z_max: 1.052, ceiling: "v6 ceiling_k4 (W1 0.007602, W2 0.006975)", bh_denominator: 4, over_family: F-WEEK}
fdr: {p: "Max-p ueber W1/W2 aus 10.000 Replikaten der faktorerhaltenden Null (DEC-99 N1), einseitig; Block-Permutation report-only", n_reps: 10000, replicates_sha256: f10250dda8e842c7e748e758cad97926361edc30011c43b18c84a70e02847a62, seed: 53, family: "F-H32 BH 0.10 report-only, Nenner 4", over_family: "F-WEEK BY 0.10 bindend, m nach DEC-99 (7)", doppelausweis_m: 11}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, label: "Etikett C.2"}
decision_relevance: {on_pass: "Tradability-Registrierung nach F-WEEK", on_drop: "fm8-IC >= MDE80 der Variante nicht vorhanden (beta-unabhaengig ~MDE80/0,75)", on_gl012_pilot: "kein Verdikt, W1/W2 bleiben blind"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", zahler_post_2024: "Delisting-Hazard ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json, stress_abs.json (nur mit Datumsfilter <= Panel-Schnitt)", rolle: abdeckungsnachweis, v6: "W1 22/2, W2 8/1 Tage"}
irreversibility_probe: {ergebnis: nachladbar}
positive_control: {vorgeschaltet: true, regel: "ERSTFASSUNG 4", seeds: "53..252", welt: "sigma_g an F2_real (Null-SD Untergrenze); PRD-Sektorwelt report-only"}
fixtures: {positive: "T1 positiv (realisierter fm8-Effekt = MDE80)", null: "T1 null (stress-Null)", adversarial: "T1 Beta-Proxy + Pilot-Leck + Siegel-Leck + Panel-Schnitt"}
artifacts: {prelaunch: "state/runs/h32_20261021_v6/ (result_sha256 2ae9bad63a69580d551183764579318f7e5f82f1bc050a30c9bd470c09dd6fa0)", pilot: "h32_pilot_<v>_P_ic_weekly.csv + sha256, h32_pilot.json", test: "h32_run_<v>_<W>_ic_weekly.csv + sha256, h32_run_fingerprint.json"}
fdr_family: "F-H32 (K = 4, BH 0.10 report-only, p = 1 ohne Uebergabe)"
over_family: "F-WEEK (BY 0.10, m = getestete Eintraege, DEC-99 (7); Doppelausweis m = 11)"
feasibility_verdict: "offen bis Pilot (Regel U)"
constants_hash: "n/a - kapitalfrei"
data_fingerprints: ["panel_export 03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb", "union_range e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589", "delisting_register a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22", "delisted_tree 250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401", "delisting_dates c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3", "prelaunch_v6 96edd5ea896834253e376407ea6efc53cc83a5bb158429e7690d42761ddb831a", "registered_yaml <sha256 nach Registrierung>", "spread_census fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083", "as_of 2026-09-28", "panel_cut_test 2026-06-28", "panel_cut_pilot 2024-06-30"]
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e, Delisted-Baum v2 (DEC-100 N1), Vorlauf v6]
etiketten: ["zugelassen nur durch DEC-99 (Pilot-Prior)", "C.17 (Abschnitt 3)", "fm8-Skala (Daempfung ~25 %)", "beschlossen nach GL-032..034"]
```
