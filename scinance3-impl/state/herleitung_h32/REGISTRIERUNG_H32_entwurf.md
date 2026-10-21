# H-32 - Registrierungsentwurf (Orchestrator, Stand 2026-10-21 nach Vorlauf v6b, DEC-101 und Nachpruefung) - NICHT registriert

> Fassung 3 (Fassung 2 nach `REVIEW_REGISTRIERUNG_H32_NACHPRUEFUNG.md`: VETO aufgehoben, Auflagen N-1..N-5 eingearbeitet;
> v6a ist nach DEC-101 E1 verworfen, Akte `state/runs/h32_20261021_v6/`). **Code-Bezug (N-5.2):** v6b ist mit dem Code-Commit
> `6e4b447` gerechnet und nur damit bitgleich reproduzierbar (der Block `power_line` des Artefakts zeigt die Regel U-2);
> die seitherigen Aenderungen (U-3 f07d060, N-1..N-4) beruehren keine eingefrorene Konstante, nur Regeltexte, Gate-Kette der
> Positivkontrolle, Injektionsziel, Uebergaberegel und Sperre; Registrierungs-Commit = HEAD bei der Registrierung.
> Grundlage: `ERSTFASSUNG_H32_entwurf.md` (Abschnitte 1, 2, 4, 9, 10, 11), `REVIEW_H32.md`, `REVIEW_REGISTRIERUNG_H32.md`
> (VETO aufloesbar, V-1/A-1..A-5 -> DEC-101 Teil 1 umgesetzt, Commits 6e4b447, f07d060), DEC-99 (+N1), DEC-100 (+N1/N2),
> DEC-101 Teil 1, Vorlauf v6b `state/runs/h32_20261021_v6b/` (zweimal gerechnet, alle Artefakte bitgleich; result_sha256
> `eee9ced98582913b891b2466990f467f8a58db58d8a880bab7d19ca0be965ab1`, JSON sha256 `f872a3af...`), Vorlage
> `h32_v1_TEMPLATE.yaml` (wird nach N-1..N-4 aus v6b neu emittiert: nur Regeltexte und neue Felder, keine Konstante; Regel U-4),
> PP3-Trockenprobe `state/runs/h32_20261021_v6b/h32_pp3_dry_run.json` (BESTANDEN: K_fm8-Reihen P/W1/W2 = Pins, keine IC).
> Registriert wird erst nach Nachpruefung ohne offenes VETO: Kopie der Vorlage nach `state/registered/h32_v1.yaml`, sha256 in
> Registry und DEC-101 Teil 2, Code-Commit = HEAD.

## 1. Vorbedingungen (Erstfassung 0) - Stand

| # | Vorbedingung | Stand 2026-10-21 |
|---|---|---|
| V1 | DEC-99 | beschlossen 2026-10-20 (+N1 p-Konvention) |
| V2 | EV-2..EV-8 | entschieden durch den Orchestrator wie in der Erstfassung kodiert (Abschnitt 3 unten), DEC-101-Entwurf |
| V3 | Bau B-0..B-6 + DEC-101 Teil 1 + U-3, Abnahme | f7dd471, a3106f5, 716191b, 9364993, 6e4b447, f07d060; `tests/unit/test_h32*.py` + `test_power_p1.py` 277 passed; `tests/unit` gesamt 2.368 passed / 3 bekannte Altfaelle (`test_execution_live.py`) / 9 skipped (2026-10-21) |
| V4 | Vorlauf v6b | 2026-10-21 17:22..19:03 UTC, zweimal parallel, **alle Artefakte bitgleich**; Universum 1.182 -> 1.066 Symbole (68 USDC-Perps, 48 datierte Futures ausgeschlossen, excluded_sha256 `50aaee3c...`); Panel-Schnitt 2026-06-28 (82 Tage), 1.000 Replikate, 1.000 Bootstrap, 10.000 p-Replikate, Seed 53; Runner-Pins as_of 2026-09-28, 2021..2026, allow_partial |
| V5 | `state/registered/h32_v1.yaml` + sha256, Code-Commit | offen (nach Review) |
| V6 | Review ohne VETO | VETO vom 16:00 UTC aufgeloest (DEC-101 Teil 1); Nachpruefung 19:24 UTC: VETO aufgehoben, ZUSTIMMUNG MIT AUFLAGEN N-1..N-5 (umgesetzt in DEC-101 Teil 2; keine erneute Vetopruefung noetig, wenn N-1/N-2 wie formuliert) |
| V7 | Daten | **geaendert (DEC-100 N1):** Ueberlebenden-Baum aus dem Zip 2026-09-28 (sha256 03dc0e7c...6b16cb) + Delisted-Baum v2 aus `rest.kline1d`/`rest.fundingRateAll` und Register `bybit/delisting_dates` 2026-10-21; Fingerprints: union_range `e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589`, delisting_register `a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22`, delisted_tree `250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401`, delisting_dates `c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3` |
| V8 | Blind-Siegel / Panel-Schnitt | Waechter im Code; v6b: letzte Woche 2026-06-22; PP3-Trockenprobe bestanden (Pilot-Schnitt 2024-06-30: 810 Tage entfernt) |

## 2. Vorlauf v6b - Kernzahlen (eingefroren; Quelle `h32_prelaunch.md`/`.json`; Universum lineare USDT-Perps)

| Fenster | Formationswochen | w_judged | K min/Median/max | floor_fm8 | v_fm8 | K-Reihe sha256 |
|---|---|---|---|---:|---:|---|
| P | 2022-04-18..2024-06-17 (Outcome bis 2024-06-24, Panel <= 2024-06-30) | 114 | 126 / 206 / 339 | 0,069642 | 0,004924 | 4a2f0937... |
| W1 | 2024-07-01..2025-06-23 | 52 | 343 / 416 / 500 | 0,048821 | 0,002391 | f35fb20b... |
| W2 | 2025-07-07..2026-06-15 | 50 | 501 / 526 / 545 | 0,043639 | 0,001905 | 6b69b6f7... |

(v6a zum Vergleich: P 127/213/353, W1 360/440/536, W2 537/590/603 - die Differenz sind die Zwillinge.)
Kalibrierung (nur Streuung/Autokorrelation/Faktoranteil): P stress rho_f 0,2352 / beta_sd 0,5277 / Faktoranteil 0,0359; W1
measured 0,0462 / 0,5396 / 0,0258, stress 0,0925 / 0,7168 / 0,0517, zero 0 / 0,5396; W2 measured 0,0702 / 0,4391 / 0,0124,
stress 0,1404 / 0,5705 / 0,0248, zero 0 / 0,4391; alle Gegenproben ok. m_P (stress, Richtung): mom1 0,002152, mom2
0,002857, mom4 0,003829, rev_gap -0,002079.

| Fenster | Variante | se_mean | e_se_rule | sd_week | null_mean | q95_1000 | q95_10000 | **q95 (= max)** | T_W,v = z x e_se_rule + max(0, null_mean) | ceiling_k4 / T |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| W1 | mom1 | 0,007302 | 0,007441 | 0,051279 | +0,001290 | 0,013947 | 0,013290 | 0,013947 | 0,01353 | 0,578 |
| W1 | mom2 | 0,008090 | 0,008123 | 0,056866 | +0,001679 | 0,015960 | 0,015176 | 0,015960 | 0,01504 | 0,520 |
| W1 | mom4 | 0,009768 | 0,009370 | 0,065995 | +0,002066 | 0,019828 | 0,018380 | 0,019828 | 0,01748 | 0,447 |
| W1 | rev_gap | 0,007429 | 0,007425 | 0,050975 | -0,001196 | 0,010300 | 0,010533 | 0,010533 | 0,01221 | 0,640 |
| W2 | mom1 | 0,006197 | 0,006630 | 0,044494 | +0,000936 | 0,011426 | 0,011573 | 0,011573 | 0,01184 | 0,567 |
| W2 | mom2 | 0,007046 | 0,007084 | 0,048215 | +0,001502 | 0,013422 | 0,013498 | 0,013498 | 0,01315 | 0,511 |
| W2 | mom4 | 0,008190 | 0,007981 | 0,054924 | +0,001953 | 0,016353 | 0,016395 | 0,016395 | 0,01508 | 0,445 |
| W2 | rev_gap | 0,006486 | 0,006629 | 0,044489 | -0,001224 | 0,008847 | 0,009239 | 0,009239 | 0,01090 | 0,616 |

ceiling_k4: W1 0,007820, W2 0,006714 -> **kein Vor-Verdikt-Kill** (Decke/Schwelle 0,45..0,64). bounce_sigma_true W1
0,173542 / W2 0,134285; Survivorship (Schwellen-Einheiten) W1 mom1 -0,425, rev_gap -0,448; W2 -0,538 / -0,522.
Stress-Abdeckung (<= 2026-06-28): W1 rel 22 / abs 2 Tage, W2 rel 8 / abs 1. p-Replikate R 10.000, Datei-sha256
`3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef`, Zelle = groesseres Null-Mittel (mom*: drifting,
rev_gap: driftfree). (T_W,v und Decke/T vom Orchestrator aus den Konstanten gerechnet.)

**Power-Zeile vor dem Pilot (v6b `power_line`, report-only; Regel U-3 = DEC-101 Teil 2):**

| Variante | MDE80 W1 (1b / 1c) | MDE80 W2 (1b / 1c) | MDE80*_U (max_W z SE_T + z_80 SD_T) | m* | Schwelle_U = MDE80*_U + m* | max_W MDE80_1c | **U-3-Schwelle auf x_P = max** | bindend | Endpower an der Schwelle (Replikat-Quantil), m = 1 / 2 / 3 / 4 / 11 |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| mom1 | 0,019676 / 0,020093 | 0,017057 / 0,016788 | 0,018385 | 0,002152 | 0,020538 | 0,020093 | **0,020538** | U | 0,751 / 0,689 / 0,548 / 0,444 / 0,201 |
| mom2 | 0,021848 / 0,022769 | 0,019084 / 0,019428 | 0,020169 | 0,002857 | 0,023027 | 0,022769 | **0,023027** | U | 0,738 / 0,661 / 0,494 / 0,382 / 0,124 |
| mom4 | 0,025699 / 0,028049 | 0,021974 / 0,023288 | 0,023633 | 0,003829 | 0,027462 | 0,028049 | **0,028049** | (1c) | 0,738 / 0,675 / 0,507 / 0,379 / 0,126 (an der U-3-Schwelle, Nachpruefung 7.3) |
| rev_gap | 0,018465 / 0,016785 | 0,016363 / 0,014698 | 0,018465 | 0 | 0,018465 | 0,016785 | **0,018465** | U | 0,703 / 0,620 / 0,497 / 0,417 / 0,205 |

(Endpower nach der Artefakt-Methode `end_power_replicates` = strenge **Untergrenze** (z_eff auch auf (1b); Nachpruefung N-5.4);
mit (1b) = z_krit und BY nur auf dem transformierten p: rev_gap m = 4 0,478, m = 11 0,279. Normalnaeherung report-only:
m = 4 0,49 / 0,51 / 0,55 / 0,42.) Regel U-4 (Teil 2, N-3): der (1c)-Term nutzt k_pred,W = max(1, sqrt(v_fm8,W + F2_real) /
sd_week_W,v) aus dem Pilot - vor dem Pilot (k_pred = 1) identische Schwellen; der Pilot kann die Schwellen nur erhoehen.
A3-Praxis (2,4865) auf x_P mit Gutschrift (N-5.3): mom1 0,0259, mom2 0,0287, mom4 0,0336, rev_gap 0,0247 - jede
Uebergabe darunter traegt "zugelassen nur durch DEC-94".

## 3. DEC-101 (Entwurf) - Registrierung H-32: Entscheidungen des Orchestrators zu EV-2..EV-8, Abweichungen, C.17

- **EV-2 (Fenster):** P 2022-04-18..2024-06-17 (Formation; K_t >= 117 ab 2022-04-18), Pilot-Panel <= 2024-06-30; W1
  2024-07-01..2025-06-30 (52); W2 2025-07-01..2026-06-28 (50, DEC-99 (8)); Panel-Schnitt vor jeder Rechnung [EV-2b].
- **EV-3 (Varianten, K):** K = 4 (mom1, mom2, mom4, rev_gap); keine H-30-Varianten; BH-Nenner 4; F-WEEK m nach DEC-99 (7)
  mit Doppelausweis 11.
- **EV-4 (Universum):** keine Universums-Variante (U0); Union-Panel, PIT-Maske DEC-72; **Universum = lineare USDT-Perpetuals
  (DEC-101 E1, Filter vor jeder Rechnung; 1.182 -> 1.066 Symbole).**
- **EV-5 (SE der Power-Zeile):** SE_T = e_se_rule (v6), SD_T = se_mean (v6), jeweils max mit SE_W,Pilot; Null-Mittel-
  Gutschrift m* = max(0, m_P, m_W1, m_W2).
- **EV-6 (Uebergaberegel):** **U-4** (DEC-101 Teil 2, Review A-4 + Nachpruefung N-3): Bedingung (ii) lautet x_P >= max(m* +
  max_W(z_krit SE_T,W + z_80 SD_T,W), max_W(max(0, m_W) + k_pred,W (q95_W,v - m_W) + z_80 SD_T,W)) mit k_pred,W = max(1,
  sqrt(v_fm8,W + F2_real) / sd_week_W,v) - die Schwelle deckt beide Gate-Bedingungen ((1b) mit Gutschrift, (1c) skaliert);
  sonst Erstfassung 1.8 woertlich; Prior-Lesart A (Pilot-Punkt), Pflicht-Doppelausweis mu_sel und A3-Praxis; genau ein
  Pilotlauf (gepinntes Verzeichnis `scinance3-impl/state/runs/h32_pilot_v1`). Richtung: Strenge, vor jeder Pilot-Zahl.
- **EV-7 (Test):** Schwelle max(z_krit x SE_W, q95_eff,W,v) mit q95_eff = max(0, m) + k (q95 - m), k = max(1, SD(IC_t,W) /
  sd_week_W,v) (DEC-101 E2), SE-Regel P-1 (4), p aus den gleich transformierten Null-Replikaten (DEC-99 N1 + DEC-101 E2), Max-p W1/W2,
  Etiketten Bounce/Liquiditaet/Survivorship; nicht gerechnet: roher IC, Lag-Profil, Beta-Kalibrierungs-IC, DEC-52-Zweig.
- **EV-8 (Positivkontrolle):** Erstfassung Abschnitt 4 mit zwei Korrekturen (DEC-101 Teil 2, N-1/N-2): Gate-Kette = die des
  Tests einschliesslich skalierter Null (k je Seed aus der Wochen-SD der synthetischen Serie gegen sd_week); Injektionsziel F:
  Ziel_W = max(z_krit SE_T,W + z_80 SD_T,W - min(0, m_df,W), q95_eff,W(k_pred,W) - m_df,W + z_80 SD_T,W), bindendes Fenster
  argmax_W, erwartete PASS-Quote 0,80 (Etikett "Korrektur nach DEC-94 (3), vor jeder Pilot-Zahl"); Welt-SD an F2_real,
  Urteils-Seeds 53..252, Kriterien (a)-(d) unveraendert; vor dem Test, nach dem Pilot.
- **Abweichungen (Erstfassung 9, ergaenzt):** 10. Delisting-Datum = letzter Handelstag aus `bybit/delisting_dates`
  (DEC-100 E1) statt Announcement-Datum; Announcement bleibt Etikett. 11. Panel vollstaendig (Delisted-Baum v2, DEC-100
  N1): W1 ist nicht mehr v5e-identisch (vor der Bereinigung K W1 +15 / +21,5 / +22 gegen v5e; nach DEC-101 E1 343/416/500),
  die W1-Determinismus-Kontrolle gegen v5e (Review H-32 B-6) entfaellt mit Grund; Ersatz: T2-Determinismus-Tests auf
  Fixtures, Zweitbau des Baums bitgleich, **v6b zweimal bitgleich**, PP3-Trockenprobe bestanden. 12. p-Konvention: Null-Replikate statt Block-Permutation (DEC-99 N1) - ersetzt
  Erstfassung 9.8 und 1.10; Block-Permutation report-only. 13. Fingerprints wie V7 oben; `delisting_register_sha256`
  und `delisted_tree_sha256` sind neue Pflicht-Pins. 14. Pilot-Vorabwert W_P 114 bestaetigt (v6b: 114 geurteilte Wochen;
  das Log zaehlt 115 Kalenderwochen inkl. der Outcome-Woche 2024-06-24). 15. Universum = lineare USDT-Perps (DEC-101 E1,
  Etikett "Bereinigung (Strenge), beschlossen nach Kenntnis der v6-Nuisance, vor jeder Pilot-Zahl"); skalierte Null im
  Testlauf (DEC-101 E2, `null_scaling`); q95 = max(1.000er, 10.000er Quantil) (E5); Regel U-3 (Teil 2); Pilot-Pfad
  gepinnt; Runner-Pins; Errata B-9 (K W1 gegen v5e +15/+21,5/+22 vor der Bereinigung; Null-Mittel richtungstragend;
  Tagesschluss-Vergleich bis 2026-09-14 nur Zaehlung; Pilotperioden-Kalibrierung neu gesehen; A3-Praxis-Etikett;
  F-WEEK-Doppelausweis 7 + 4 + Welle; P-Start fest nach DEC-99).
- **C.17 (gesehen, nicht ergebnisnah; Stand 2026-10-21):** aus v6a/v6b nur Nuisance (Streuung, Autokorrelation, Faktoranteil,
  Null-Quantile, K-Reihen, Stress-Zaehlungen; die Null-Mittel sind richtungstragend, modellbasiert; rho_f/sigma_f/
  Faktoranteil/Querschnittsstreuung der Pilotperiode neu gesehen, DEC-94 (5) (i)); der Tagesschluss-Gleichheitsvergleich
  (BEFUND 3) umfasste Tage bis 2026-09-14 (nur Zaehlung, kein Wert); aus DEC-100 N1 nur Symbol-/Datumslisten, Zaehlungen je Tag und die
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
  - {id: P,  von: 2022-04-18, bis: 2024-06-30, wochen_geurteilt: 114, rolle: pilot_nicht_urteilstragend, panel_schnitt: 2024-06-30, K_min_median_max: [126, 206, 339]}
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen_geurteilt: 52, rolle: urteilstragend, K_min_median_max: [343, 416, 500]}
  - {id: W2, von: 2025-07-01, bis: 2026-06-28, wochen_geurteilt: 50, rolle: urteilstragend, panel_schnitt: 2026-06-28, K_min_median_max: [501, 526, 545]}
fenster_regel: "C10_hart (Regel U laesst nur C10 zu)"
threshold: {formel: "max(1.6449 * SE_W, q95_eff_W) mit q95_eff = max(0, m) + k * (q95 - m), k = max(1, SD(IC_t,W)/sd_week)", SE_W: "max(floor_fm8/sqrt(W), SD/sqrt(W), SE_stat stationaer Block 4)", ref: "ERSTFASSUNG 1.9; DEC-101 E2; v6b frozen_v6"}
structural_null: {komponenten: [faktorerhaltende_null_stress_fm8, q95_max_1000_10000, selektionsdecke_k4_vorzeichenbereinigt, bounce_rev_gap, null_scaling_im_testlauf], ref: "v6b windows.<W>.frozen_v6; DEC-101 E2/E5", kill_check: "ceiling_k4 / T_W,v 0.45..0.64 -> kein Vor-Verdikt-Kill"}
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
  detectable_effect_mde80_v6b: {W1: {mom1: 0.020093, mom2: 0.022769, mom4: 0.028049, rev_gap: 0.018465}, W2: {mom1: 0.017057, mom2: 0.019428, mom4: 0.023288, rev_gap: 0.016363}, rule: "max((1b) mit Gutschrift, (1c))"}
  handover_threshold_on_pilot_point_v6b_u4_kpred1: {mom1: 0.020538, mom2: 0.023027, mom4: 0.028049, rev_gap: 0.018465}
  end_power_f_week_at_threshold_v6b_replicates_lower_bound: {m1: [0.70, 0.75], m4: [0.38, 0.44], m11_report_only: [0.12, 0.21]}
  zuordnungsregel: "Regel U-4 (ERSTFASSUNG 1.8 + DEC-101 Teil 2, k_pred aus dem Pilot), power_p1.assign_regime; Doppelausweis assign_regime_a3_practice"
  ref: "state/runs/h32_20261021_v6b/h32_prelaunch.json power_line; state/herleitung_h32/REGISTRIERUNG_H32_entwurf.md Abschnitt 2"
selection: {K: 4, z_max: 1.052, ceiling: "v6b ceiling_k4 (W1 0.007820, W2 0.006714)", bh_denominator: 4, over_family: F-WEEK}
fdr: {p: "Max-p ueber W1/W2 aus 10.000 Replikaten der faktorerhaltenden Null (DEC-99 N1), transformiert d' = max(0, m) + k (d - m) (DEC-101 E2, Block null_scaling), einseitig; Block-Permutation report-only", n_reps: 10000, replicates_sha256: 3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef, seed: 53, family: "F-H32 BH 0.10 report-only, Nenner 4", over_family: "F-WEEK BY 0.10 bindend, m nach DEC-99 (7)", doppelausweis_m: 11}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, label: "Etikett C.2"}
decision_relevance: {on_pass: "Tradability-Registrierung nach F-WEEK", on_drop: "fm8-IC >= MDE80 der Variante nicht vorhanden (beta-unabhaengig ~MDE80/0,75)", on_gl012_pilot: "kein Verdikt, W1/W2 bleiben blind"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", zahler_post_2024: "Delisting-Hazard ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json, stress_abs.json (nur mit Datumsfilter <= Panel-Schnitt)", rolle: abdeckungsnachweis, v6: "W1 22/2, W2 8/1 Tage"}
irreversibility_probe: {ergebnis: nachladbar}
positive_control: {vorgeschaltet: true, regel: "ERSTFASSUNG 4 + DEC-101 Teil 2 (N-1 Gate-Kette mit skalierter Null, N-2 Injektionsziel F)", seeds: "53..252", welt: "sigma_g an F2_real (Null-SD Untergrenze); PRD-Sektorwelt report-only"}
fixtures: {positive: "T1 positiv (realisierter fm8-Effekt = MDE80)", null: "T1 null (stress-Null)", adversarial: "T1 Beta-Proxy + Pilot-Leck + Siegel-Leck + Panel-Schnitt"}
artifacts: {prelaunch: "state/runs/h32_20261021_v6b/ (result_sha256 eee9ced98582913b891b2466990f467f8a58db58d8a880bab7d19ca0be965ab1; v6a verworfen)", pilot: "h32_pilot_<v>_P_ic_weekly.csv + sha256, h32_pilot.json", test: "h32_run_<v>_<W>_ic_weekly.csv + sha256, h32_run_fingerprint.json"}
fdr_family: "F-H32 (K = 4, BH 0.10 report-only, p = 1 ohne Uebergabe)"
over_family: "F-WEEK (BY 0.10, m = getestete Eintraege, DEC-99 (7); Doppelausweis m = 11)"
feasibility_verdict: "offen bis Pilot (Regel U)"
constants_hash: "n/a - kapitalfrei"
data_fingerprints: ["panel_export 03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb", "union_range e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589", "delisting_register a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22", "delisted_tree 250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401", "delisting_dates c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3", "prelaunch_v6b_json f872a3af25753e84... (voll: state/runs/h32_20261021_v6b/, sha256 der JSON-Datei; result_sha256 eee9ced98582913b891b2466990f467f8a58db58d8a880bab7d19ca0be965ab1)", "code_commit_prelaunch 6e4b447", "universe_excluded 50aaee3c1e63d560b69a7aa42748abdea0e0cf742f6ff3f618e6f00c54083098", "registered_yaml <sha256 nach Registrierung>", "spread_census fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083", "as_of 2026-09-28", "panel_cut_test 2026-06-28", "panel_cut_pilot 2024-06-30"]
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e, Delisted-Baum v2 (DEC-100 N1), DEC-101 Teil 1, Vorlauf v6b x2, PP3-Trockenprobe]
etiketten: ["zugelassen nur durch DEC-99 (Pilot-Prior)", "C.17 (Abschnitt 3)", "fm8-Skala (Daempfung ~25 %)", "beschlossen nach GL-032..034", "Universum bereinigt (Strenge, DEC-101 E1)", "Regel U-4 (Strenge, DEC-101 Teil 2)", "Positivkontrolle korrigiert (DEC-94 (3), DEC-101 Teil 2)"]
```
