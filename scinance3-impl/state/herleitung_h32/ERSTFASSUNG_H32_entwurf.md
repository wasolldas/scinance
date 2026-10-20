## H-32 - Erstfassung (ENTWURF 2026-10-20, Stand nach Review): A3-fm8, beta-neutraler Wochen-Querschnitts-IC im Zweistufen-Design (Pilot 2022-04..2024-06, Test W1/W2), Klasse W, kapitalfrei

> **NICHT REGISTRIERT.** Entwurf der Herleitung; registrieren darf nur der Orchestrator. DEC-99 ist beschlossen; die
> Review-Auflagen A-2, A-3, A-4, A-6, A-7, A-8 und B-6 (`REVIEW_H32.md` Abschnitt 5) sind eingearbeitet, dazu
> DEC-99 (3)/(5) (ein Pilotlauf, mu_sel, Verbrauch). Zahlen mit Fundstelle;
> `[pj <pfad>]` = `state/herleitung_h32/power_h32.json` (sha256 `f0d6e6d9c55e0a9326ab5b32988eb86bbd0c62ef283b0c3101a4889a402a56a3`),
> `[v5e <pfad>]` = `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json` (sha256 `94d65559...5ae3b2`), `[wp7k]` =
> `state/runs/wp7_20260921/decile_degeneration_weekly.csv` (nur `week`, `n_symbols`), `[EV-n]` = Entscheidungsvorlage
> in `ENTSCHEIDUNGSVORLAGEN.md`, `[Review B-n]` = `REVIEW_H32.md`. Alle Werte mit "v6" friert der Vorlauf v6 ein und
> ersetzen die v5e-Vorabzahlen; keine v6-Zahl darf eine Realisierung aus Pilot, W1 oder W2 enthalten.
> Ergebnisblind: keine reale IC, kein Outcome; Siegeldateien nie geoeffnet.

### 0. Vorbedingungen der Registrierung (ohne sie ist der Eintrag nicht lauffaehig)

| # | Vorbedingung | Stand |
|---|---|---|
| V1 | **DEC-99** (REZENZ 3.0, Pilot-Schaetzfenster, F-WEEK-Zaehlregel, W2-Ende 2026-06-28) | **beschlossen 2026-10-20** |
| V2 | Orchestrator-Entscheidungen zu EV-2..EV-8 | offen |
| V3 | Bau B-0..B-6 (Bauliste Abschnitt 12), Abnahme durch den Orchestrator (Tests nie reduziert) | offen |
| V4 | Vorlauf v6 (Realdaten, nur Nuisance, Panel <= 2026-06-28) mit eingefrorenen Konstanten je Fenster, W2-Neukalibrierung, Pilotperioden-Kalibrierung (m_P), e_se_rule, K_fm8-Reihen | offen |
| V5 | finale Registrierungsdatei `state/registered/h32_v1.yaml` + sha256, Code-Commit und code_sha256 | offen |
| V6 | Abnahme der Auflagen durch den Orchestrator (Review ZUSTIMMUNG MIT AUFLAGEN, kein VETO) | offen |
| V7 | Daten: derselbe Harvest-Export wie v5e (`scinance_panel_1d_2026-09-28.zip`, sha256 `03dc0e7c...6b16cb`), Fingerprints union_range `a7e4dec7...793a`, delisting_dates `852bf753...2933` | vorhanden |
| V8 | Blind-Siegel DEC-96 E3: **harter Panel-Schnitt vor jeder Rechnung** (Test/v6 <= 2026-06-28, Pilot <= 2024-06-30), Stress-Listen nur mit Datumsfilter | Waechter im Code (B-0) |

---

### 1. Festlegungen (bindend fuer alle Eintraege)

#### 1.1 Klasse, Familie, Varianten

- Klasse W, kapitalfrei. Familie **F-H32**, **K = 4** Varianten, je ein Eintrag:
  `H-32_mom1` (positiv), `H-32_mom2` (positiv), `H-32_mom4` (positiv), `H-32_rev_gap` (negativ, Lag-2-Gap).
- Hypothesen-PASS, wenn mindestens ein Eintrag PASS ist; jeder Eintrag wird einzeln berichtet.
- **K = 4 bleibt Nenner** der Kohorte (vorzeichenbereinigte Selektionsdecke, BH-Nenner 4); Eintraege ohne Uebergabe
  gehen dort mit p = 1 ein (DEC-99 (3)).
- Ueber-Familie **F-WEEK** (Benjamini-Yekutieli, alpha 0,10, am Wellenschluss, bindend) nach **DEC-99 (7)**: m = Zahl
  der Eintraege, fuer die ein p-Wert tatsaechlich berechnet wurde (bei H-32 die uebergebenen, 1..4, zuzueglich weiterer
  getesteter Hypothesen der Welle); F-XSEC1 (GL-032) und nicht uebergebene Eintraege zaehlen nicht in m.
  Doppelausweis alte Zaehlung m = 11 (report-only).
- Nicht aufgenommen: H-30-Varianten (vol_beta strukturell unter fm8, C.4; vol_rv/vol_max Drag-Feasibility 2,764 > 0,5,
  durch fm8 nicht behoben) [EV-3]; keine Universums-Variante (U0) [EV-4]; keine Zwei-Richtungen-Variante.

#### 1.2 Panel, Universum, Datenbezug

Wie Drittfassung H-28..H-30: Union `panel_1d` + `panel_1d_delisted`, PIT-Maske DEC-72, Delisting-Datum =
Announcement-Datum (Etikett), `--allow-partial` (DEC-66), Bezug nur ueber exakte Schluessel des Harvest-Exports,
Pruefung von Groesse und sha256, Entpacken in ein frisches Sitzungsverzeichnis (nie ins Repo, nie unter `data/harvest`),
Zugangsdaten nur aus `HARVEST_S3_*`. Daten-Fingerprints V7 auf den Dateien, Abweichung = KEIN VERDIKT.
**Panel-Schnitt (DEC-96 E3, DEC-99 (3), [Review B-6]):** unmittelbar nach der Fingerprint-Pruefung und vor dem Bau von
Wochenrenditen, Charakteristiken, Betas, Kalibrierungen und Nullen werden die Tagesdaten abgeschnitten - Test-Modus und
Vorlauf v6 auf <= 2026-06-28, Pilot-Modus auf <= 2024-06-30; ein Waechter prueft das Maximaldatum (loud fail).

#### 1.3 Fenster

| Fenster | Kalender (Slice) | Formationswochen (geurteilt) | Outcome-Wochen | W | K_t min/Median/max | Rolle |
|---|---|---|---|---:|---|---|
| **P** | 2022-04-18..2024-06-30 | 2022-04-18..2024-06-17 | 2022-04-25..2024-06-24 (Ende 2024-06-30) | 114 | 120/202/339 | **Pilot, nicht urteilstragend; Screening, nie Konfirmation (C.17/C.18)**; nach der Uebergabe verbraucht (DEC-99 (5)) |
| **W1** | 2024-07-01..2025-06-30 | 2024-07-01..2025-06-23 | 2024-07-08..2025-06-30 (Ende 2025-07-06) | 52 | 345/419/514 | urteilstragend |
| **W2** | 2025-07-01..2026-06-28 | 2025-07-07..2026-06-15 | 2025-07-14..2026-06-22 (Ende 2026-06-28) | 50 | v6 (geschnitten) | urteilstragend, juengstes Fenster (DEC-99 (1), (8)) |
| L | 2021-03-01..2024-06-30 | - | - | - | versiegelt | Aera-Profil der Drittfassung, bleibt versiegelt; H-32 oeffnet die Siegeldatei nie |

- P: erste Woche mit K_t >= 117 (K_min, PRD 4.1) `[wp7k]`; identisch mit der A1-Nuisance-Basis. Davor < 117 (2022-04-04: 111).
- P endet vor dem ersten Kalendertag von W1; keine Kalenderwoche ist zugleich Pilot-Outcome und W1-Woche [EV-2b].
  Der Rueckblick der W1-Charakteristiken (mom2/mom4, rev_gap-Gap) und der 8-Wochen-Betas in die Pilotperiode ist
  Formation, kein Outcome des Tests, und zulaessig (DEC-75 (8)).
- W2 endet mit der Outcome-Woche 2026-06-22..28 (DEC-99 (8)); Abweichung von der Drittfassung (dort bis 2026-07-05).
- Die Charakteristiken und Betas werden auf dem (geschnittenen) vollen Panel gebaut und danach geschnitten (DEC-75 (8)).

#### 1.4 Cluster-Einheit, Metrik, Konvention

- Cluster = Kalenderwoche (ISO). Je Woche ein Spearman-Rank-IC ueber die lebenden Symbole mit gueltigem PIT-Beta;
  Wochen mit < 10 gueltigen Symbolen fallen aus.
- **Primaerstatistik je Variante und Fenster:** Mittel der Wochen-ICs der Charakteristik (Woche t) gegen das
  **fm_neutral_8w-neutralisierte** Folgewochen-Outcome (t+1) - exakt `ic.apply_beta_control("fm_neutral_8w", ...)` und
  `ic.weekly_ic_series(..., convention="close_at_last")`, d. h. die IC_res der Drittfassung.
- **fm8-Daempfung (Etikett, [Review B-4]):** Das PIT-Beta (t-7..t) enthaelt die Formationswoche(n); ein beta-unabhaengiges
  Signal erscheint in der Primaerstatistik zu ~75 % (synthetisch 0,754 fuer mom1 `[pj fm8_daempfung]`; mom2/mom4
  vermutlich staerker). Alle Schwellen, MDE80 und Priors dieser Fassung sind auf der fm8-Skala.
- Survivorship-Konvention `close_at_last` (urteilstragend); `drop` nur Sensitivitaet.
- In Richtung: y = s x Statistik, s = +1 (mom1, mom2, mom4), s = -1 (rev_gap).

#### 1.5 Charakteristiken (je Woche t, PIT; wie Drittfassung)

mom1/mom2/mom4: Summe der Wochen-Log-Renditen t-n+1..t, n = 1/2/4. rev_gap: Wochen-Log-Rendite der Woche t-1, Woche t
ist das Gap. Code `characteristics.momentum_characteristic`, `characteristics.reversal_gap_characteristic`.

#### 1.6 Beta-Kontrolle und Null

- `fm_neutral_8w`: je Outcome-Woche t+1 Querschnitts-OLS des Outcomes auf das PIT-Beta zu BTCUSDT (t-7..t aus
  `returns_est`, 8 gueltige Wochen noetig), Residuum ersetzt das Outcome (DEC-86).
- Null: faktorerhaltende Null der Drittfassung (DEC-85/87), stress bindend. Kalibrierung je Fenster: W1 wie v5e
  (in v6 auf dem geschnittenen Panel nachgerechnet, muss v5e treffen); **W2 in v6 neu auf dem geschnittenen Fenster**
  (sigma_f, rho_f, Faktoranteil, beta_sd measured/stress/zero mit Gegenproben, null_scales) - die v5e-W2-Werte enthalten
  die Woche 2026-06-29..07-05 und werden nicht registriert [Review B-6]. **Pilotperiode in v6 kalibriert** (sigma_f,
  rho_f, Faktoranteil; nur Streuung und Autokorrelation, Waechter "kein Mittel", DEC-94 (5) (i)) [Review B-8].
- v6-Null: 8 Beta-Vorlaufwochen (reale Masken), K = 4, Fenstermittel ueber 52/50 Wochen, 1.000 Replikate, Seed 53,
  driftfrei und Drift 0,002/Woche.
- Eingefroren je Fenster W und Variante v (v6): `se_mean` (SD des Fenstermittels), `e_se_rule` (Erwartungswert der SE
  nach Regel P-1 (4) ueber die Replikate, stationaerer Bootstrap wie im Lauf; [Review B-7]), `sd_week`, `null_mean`
  (in Richtung, extremeres aus driftfrei/Drift), `q95` (95-%-Quantil des Fenstermittels in Richtung, extremeres aus
  driftfrei/Drift), `ceiling_k4` (Mittel des Maximums der vorzeichenbereinigten Fenstermittel ueber die 4 Varianten,
  stress, driftfrei), `k_fm8_series`, `floor_fm8` = mean_t 1/sqrt(K_fm8,t - 1), `v_fm8` = mean_t 1/(K_fm8,t - 1);
  fuer die Pilotperiode `m_P` je Variante (stress, extremeres aus driftfrei/Drift).
- Vorabwerte bis v6 (v5e, 45/44 Simulationswochen, konservativ) [EV-5]: se_mean W1 mom1/mom2/mom4/rev_gap
  0,00794/0,00896/0,01078/0,00785; W2 (x sqrt(51/50)) 0,00643/0,00714/0,00847/0,00671; null_mean W1
  +0,00087/+0,00142/+0,00185/-0,00114, W2 +0,00054/+0,00068/+0,00099/-0,00046 `[pj power.nuisance]`; bis v6 gilt
  e_se_rule := se_mean (S1).

#### 1.7 Stufe P - Pilot (Schaetzung, nicht urteilstragend)

**Genau ein Pilotlauf** (DEC-99 (3)): ein Neulauf nur bei nachgewiesenem Code- oder Datenfehler per DEC, beide Ergebnisse
offengelegt, das korrigierte bindet in beide Richtungen; der Pilot-Modus verweigert einen zweiten Lauf ohne DEC-Verweis.
Je Variante v, Panel <= 2024-06-30, nur Formationswochen 2022-04-18..2024-06-17:
- x_P = Mittel der fm8-Wochen-ICs in Richtung; SD_P = Stichproben-SD (ddof 1); W_P = Zahl der endlichen Wochen (Soll 114).
- SE_P = max(B_P / sqrt(W_P), SD_P / sqrt(W_P), SE_stat), B_P = mean_t 1/sqrt(k_t - 1) mit k_t = Symbole im fm8-IC der
  Woche, SE_stat = SD der Mittel des stationaeren Bootstraps (mittlere Blocklaenge 4, 1.000 Replikate, Seed 53;
  `power_p1.stationary_bootstrap_se`) - P-1 (4).
- t_P = x_P / SE_P; 80-%-Band x_P +- 1,2816 x SE_P (normal, zweiseitig); Bericht: Perzentil-Band des Bootstraps.
- Streuungs-Nuisance fuer die Test-SE (DEC-94 (5) (i), DEC-99 (6)): F2_real = max(0, SD_P^2 - mean_t 1/(k_t - 1)),
  c_real = max(1, W_P x SE_stat^2 / SD_P^2).
- Vorhersage (keine Bindung): SE_P mom1 0,0071, mom2 0,0075, mom4 0,0085, rev_gap 0,0070 `[pj power.pilot_precision]`.
- Nicht gerechnet: roher IC, Lag-Profil, Beta-Kalibrierungs-IC, irgendein Outcome ausserhalb von P.

#### 1.8 Uebergaberegel U (woertlich; vorab fixiert, mechanisch, nicht nach dem Sehen waehlbar)

> Fuer jede Variante v werden aus dem Pilot-Ergebnis und den v6-Konstanten berechnet:
> SE_W,Pilot = sqrt(c_real) x sqrt(v_fm8_W + F2_real) / sqrt(w_judged_W) fuer W in {W1, W2};
> SE_T,W = max(e_se_rule_W,v, SE_W,Pilot) (Schwellen-SE); SD_T,W = max(se_mean_W,v, SE_W,Pilot) (Streuung);
> m* = max(0, m_P,v, null_mean_W1,v, null_mean_W2,v) (in Richtung);
> MDE80*_v = max_W (1,6449 x SE_T,W + 0,8416 x SD_T,W).
> Die Variante wird **uebergeben**, genau wenn
> (i) x_P > 0 (Vorzeichen in registrierter Richtung) UND
> (ii) x_P - m* >= MDE80*_v UND
> (iii) t_P >= 2,0.
> Prior der Zuordnung: **pi_v = x_P** (Lesart A; DEC-99 (6); Alternative B "x_P - 1,2816 x SE_P" ist nicht registriert) [EV-6].
> Regime: `power_p1.assign_regime([pi_v - max(0, null_mean_W1,v), pi_v - max(0, null_mean_W2,v)], [SE_T,W1, SE_T,W2],
> sds=[SD_T,W1, SD_T,W2])`; unter (ii) ist es stets C10. Doppelausweis: `power_p1.assign_regime_a3_practice` mit denselben
> Eingaben; ist dort GL012, traegt der Eintrag "zugelassen nur durch DEC-94 (Lockerung)".
> **Pflicht-Doppelausweis (DEC-99 (3)):** mu_sel_v = Loesung von P_mu(X >= x_P | X >= c_v) = 0,5, X ~ N(mu, SE_P^2),
> c_v = MDE80*_v + m* (die Uebergabeschwelle auf x_P); dazu die gemeinsame Testpower an mu_sel_v (wie Pflichtzeile 1).
> Keine Entscheidungswirkung.
> Nicht uebergebene Varianten: Status **GL-012 (Pilot)** mit gemessenem Grund (verfehlte Bedingung, x_P, SE_P, t_P,
> MDE80*_v, m*); p = 1 im BH-Nenner 4; kein Test, kein Verdikt, nicht in m von F-WEEK (DEC-99 (7)).
> Das Pilot-Ergebnis (`h32_pilot.json`, result_sha256) und die Uebergabe werden vom Orchestrator festgehalten (DEC- oder
> GL-Vermerk), bevor ein Testfenster gerechnet wird. Danach ist der Pilotabschnitt fuer jede korrelierte Statistik
> verbraucht (DEC-99 (5)).

Vorabwerte von MDE80*_v + m* (v5e, S1, m_P := m_W1; v6 ersetzt sie, der Pilot kann sie nur erhoehen): mom1 0,0206,
mom2 0,0237, mom4 0,0287, rev_gap 0,0195 (auf x_P) `[pj power.handover_oc.<v>.A_punkt.pilot_threshold_on_point]`.

#### 1.9 Stufe T - Test (nur uebergebene Varianten)

- y_W = Primaerstatistik in Richtung, W in {W1, W2}, Panel <= 2026-06-28.
- SE_W (Lauf) = max(floor_fm8,W / sqrt(w_judged_W), SD(IC_t,W) / sqrt(w_judged_W), SE_stat,W), SE_stat aus dem
  stationaeren Bootstrap der Wochenserie (Block 4, 1.000, Seed 53) - P-1 (4).
- Schwelle je Fenster: T_W = max(z_krit x SE_W, q95_W,v), z_krit = 1,6449 (alpha 0,05 einseitig, DEC-51 (1), DEC-94 (1)).
- **Power-Zeile** (DEC-94 (3), [Review B-7]; vor dem Test festgestellt): Fenster-Power
  P_W = Phi((pi_v - max(0, null_mean_W,v) - 1,6449 x SE_T,W) / SD_T,W); MDE80_W = 1,6449 x SE_T,W + 0,8416 x SD_T,W +
  max(0, null_mean_W,v). Zuordnung je Fenster (DEC-94 (6), DEC-99 (6)).
- **Endpower nach F-WEEK (DEC-99 (7), Pflicht-Ausweis, keine Zuordnungsgrundlage):** mit m = Zahl der getesteten
  Eintraege verlangt BY fuer eine einzelne Ablehnung Max-p <= 0,10 / (m x H_m); Endpower = Produkt der Fenster-Powers mit
  z_eff = max(1,6449, Phi^-1(1 - 0,10 / (m x H_m))). Doppelausweis m = 11 (report-only).
- Vorab (v5e, S1) MDE80 W1 / W2: mom1 0,0206 / 0,0165, mom2 0,0237 / 0,0184, mom4 0,0287 / 0,0221, rev_gap
  0,0195 / 0,0167; A3-Praxis W1: 0,0273 / 0,0312 / 0,0377 / 0,0261 `[pj power.power_table]`. Endpower an MDE80 fuer
  m = 1 / 2 / 3 / 4 / 11: mom1 0,74 / 0,67 / 0,55 / 0,48 / 0,26; mom2 0,75 / 0,68 / 0,57 / 0,49 / 0,27; mom4 0,76 / 0,69 /
  0,57 / 0,50 / 0,28; rev_gap 0,72 / 0,64 / 0,52 / 0,44 / 0,23 `[pj power.f_week_by_end_power]`.

#### 1.10 Selektion und FDR

- DEC-94 (7): z = max(1,6449, z_max(4) = 1,052) = 1,6449 `[pj power.selection]`.
- Vor-Verdikt-Kill: ceiling_k4_W >= T_W,eingefroren (= 1,6449 x e_se_rule_W,v + max(0, null_mean_W,v)) in einem Fenster ->
  GL-012 des Eintrags (eine Decke, vier Schwellen; die kleinste, rev_gap, bindet zuerst). Vorab grob: Decke / Schwelle
  0,62..0,68 [Review B-15] - kein Kill erwartet.
- BH (report-only) innerhalb F-H32: alpha 0,10, fester Nenner 4, nicht uebergebene Eintraege p = 1.
- **p je Eintrag (DEC-74 (e)):** Max-p ueber W1/W2 des einseitigen Block-Permutations-p der fm8-Primaerstatistik: die
  Outcome-Wochen (Rohrenditen) werden in Bloecken der Laenge 4 permutiert, danach fm8 mit den unveraenderten
  Formationswochen-Betas angewendet; **10.000 Permutationen**, Seed 53.
- **F-WEEK (bindend, am Wellenschluss):** BY alpha 0,10 ueber die getesteten Eintraege der Welle (DEC-99 (7));
  Doppelausweis m = 11 (report-only).

---

### 2. Gate-Text (woertlich, Fassung fuer den Bau)

**Pilot-Modus (`--pilot`) - Abbrueche vor jeder Ausgabe (rc 1, KEINE UEBERGABE fuer keine Variante):**
- (PP0) Startsperre: sha256 der `--registered`-Datei = `--registered-sha256`.
- (PP0') **Neulauf-Sperre:** liegt fuer diese Registrierung bereits ein Pilot-Ergebnis vor, bricht der Modus ab, ausser mit
  `--pilot-rerun-dec <DEC-Nummer>` (DEC-99 (3)); beide Ergebnisse werden offengelegt.
- (PP1) Schema: `pilot_window`, `handover_rule`, `fdr`, `seal`, `alpha` = 0,05, `z_krit` = 1,6449, `mde_faktor` = 2,4865,
  `primary_statistic` = `fm_neutral_8w`, je Fenster die v6-Konstanten aller 4 Varianten inkl. `e_se_rule`, `m_P` je
  Variante; fehlend oder ungueltig = Abbruch.
- (PP2) Daten-Fingerprints der Dateien = YAML.
- (PP2') **Panel-Schnitt:** Tagesdaten auf <= `seal.panel_cut_pilot` (2024-06-30) abgeschnitten, bevor Wochenrenditen,
  Charakteristiken oder Betas gebaut werden; Maximaldatum-Waechter.
- (PP3) T5-Pins: `pilot_window.w_pilot` = W_P des geladenen Fensters (114), `rules.mean_block` = 4, `rules.n_boot` >= 1.000,
  `rules.seed` = 53.
- (PP4) **Siegel-Waechter:** keine Outcome-Woche ausserhalb 2022-04-25..2024-06-24 wird einer Charakteristik
  gegenuebergestellt (monkeypatch-Test auf `ic.weekly_ic_series`); kein roher IC, kein Lag-Profil.
- (PP5) DEC-53-Artefakte (Wochenserie je Variante CSV + sha256, Bootstrap-Fingerprint) vor der Uebergabe geschrieben und
  per Round-Trip verifiziert.
- Ausgabe je Variante: x_P, SE_P, SD_P, W_P, t_P, 80-%-Band, F2_real, c_real, SE_T,W, SD_T,W, m*, MDE80*_v, Bedingungen
  (i)-(iii), Uebergabe ja/nein, pi_v, Regime P-1 und A3-Praxis, mu_sel_v und Power daran, Etikett.

**Test-Modus (`--run`) - Abbrueche vor jedem Verdikt (rc 1, KEIN VERDIKT):**
- (P0) Startsperre YAML; (P0') **Pilot-Sperre:** `--pilot-result` mit sha256 = `--pilot-result-sha256`; die Uebergabe wird
  aus diesem JSON mit Regel U deterministisch nachgerechnet und muss bitgleich sein; abweichend = Abbruch.
- (P0'') **Panel-Schnitt:** Tagesdaten auf <= `seal.panel_cut_test` (2026-06-28) abgeschnitten, bevor irgendetwas gebaut
  wird; Maximaldatum-Waechter; Stress-Listen nur mit Datumsfilter.
- (P1) Schema wie PP1; (P2) `beta_control` = fm_neutral_8w / 8; (P3) Daten-Fingerprints; (P4) T5-Pins (`w_judged` 52/50,
  Block, Replikate, Seed, z_krit, `fdr.n_perm` = 10.000); (P5) `returns_valid` vorhanden.
- (P6) Null-Nachrechnung je Fenster (v6-Konfiguration): se_mean, e_se_rule, null_mean, q95, ceiling_k4 je innerhalb
  +-10 % der eingefrorenen Werte (bei eingefrorenem Wert ~0: absolut 1e-4); geurteilt wird gegen die eingefrorenen Werte.
- (P7) **Siegel-Waechter:** keine Outcome-Woche nach 2026-06-22 (letzter Kalendertag 2026-06-28); kein roher IC, kein
  Lag-Profil, kein Beta-Kalibrierungs-IC.
- (P8) DEC-53-Artefakte vor jedem Verdikt geschrieben und verifiziert.

**Nicht uebergebene Eintraege:** nicht gerechnet; Verdikt "GL-012 (Pilot): <gemessener Grund>", p = 1 (BH-Nenner 4),
nicht in m von F-WEEK.

**Uebergebene Eintraege - Vor-Verdikt-Kill:** ceiling_k4_W >= T_W,eingefroren in einem Fenster -> DROP mit Etikett GL-012.

**Vorlaeufiger PASS genau dann, wenn in W1 UND W2 (C.10 hart) gilt:**
- (1a) y_W > 0 (NaN verfehlt);
- (1b) y_W >= 1,6449 x SE_W (SE_W nach 1.9; NaN oder 0 verfehlt);
- (1c) y_W >= q95_W,v (eingefroren);
- und nur fuer `H-32_rev_gap`: (4b) kein Bounce-Kill - |IC_bounce,W| >= |Statistik_W| in einem Fenster -> KEIN PASS,
  Etikett "Artefakt Bounce" (Fixture wie Drittfassung: `rules.bounce_spread` 0,003621, `windows.<W>.bounce_sigma_true`
  W1 0,17186 / W2 aus v6, Seed 53).

Sonst DROP mit Etikett der verfehlten Bedingung. Ein DEC-52-Zweig existiert nicht (Regel U laesst nur C10 zu).

**F-WEEK (bindend, am Wellenschluss; DEC-99 (7)):** p je getestetem Eintrag = Max-p (1.10); BY alpha 0,10 ueber alle in
der Welle tatsaechlich getesteten Eintraege (m). Ein vorlaeufiger PASS, den BY nicht ablehnt, wird DROP mit Etikett
"F-WEEK-BY nicht bestanden"; jedes Ergebnis traegt den Doppelausweis "alte Zaehlung m = 11: abgelehnt ja/nein"
(report-only). Bis zum Wellenschluss traegt jeder PASS das Etikett "vorlaeufig bis F-WEEK geschlossen".

**Etiketten (report-only, nie Gate-Eingang):** Liquiditaet (Mittel-IC ohne Bucket 1 des trailing-8-Wochen-Median-
Turnovers und auf Buckets 3..10; "Illiquiditaets-Artefakt", wenn ohne Bucket 1 nicht jenseits 0,5 x T_W in Richtung);
Survivorship (synthetisch, v5e: mom1 -0,198/-0,438, rev_gap -0,189/-0,579 IC_min-Einheiten; W2 in v6 neu); BH alpha 0,10
ueber Nenner 4; "zugelassen nur durch DEC-94" (Doppelausweis); "zugelassen nur durch DEC-99 (Pilot-Prior)" an jedem
Eintrag; mu_sel-Doppelausweis; "fm8-Skala (Daempfung ~25 %)".

**Verdikt H-32:** PASS, wenn mindestens ein Eintrag PASS ist (nach F-WEEK); "GL-012 (Pilot)", wenn kein Eintrag
uebergeben wurde; sonst DROP.

---

### 3. Die zwoelf Pflichtzeilen (PRD 3.3)

| # | Zeile | Inhalt |
|---|---|---|
| 1 | Power | alpha 0,05 einseitig je Fenster (z_krit 1,6449), Power 0,80 je Fenster, Cluster Woche, W 52/50; Schwellen-SE = e_se_rule (v6), Streuung = se_mean (v6), je max mit der K-bereinigten Pilot-Streuung (DEC-94 (3)/(5)); Prior = Pilot-Punkt (DEC-99 (6), Lesart A); Zuordnung mechanisch nach Regel U, nur C10. Vorab-MDE80 W1 / W2: mom1 0,0206 / 0,0165, mom2 0,0237 / 0,0184, mom4 0,0287 / 0,0221, rev_gap 0,0195 / 0,0167 (S1, bis v6). **Endpower nach F-WEEK-BY (DEC-99 (7))** fuer das tatsaechliche m (an MDE80: m = 1 0,72..0,76, m = 4 0,44..0,50) und Doppelausweis m = 11 (0,23..0,28). **mu_sel und Power an mu_sel** (DEC-99 (3)). Doppelausweis A3-Praxis. |
| 2 | Entscheidungsrelevanz | PASS (nach F-WEEK): getrennte Tradability-Registrierung (Dezil-Slippage, DEC-67 E4). DROP eines uebergebenen Eintrags: fm8-IC >= MDE80 (W1 mom1 0,0206) auf Bybit-Perps 2024-07..2026-06 mit Power 0,80 je Fenster nicht vorhanden; **auf ein beta-unabhaengiges Signal umgerechnet (fm8-Daempfung ~25 %) ~0,027 (mom1), 0,026 (rev_gap), >= 0,031 (mom2), >= 0,038 (mom4)** `[pj fm8_daempfung]`; kein Urteil ueber kleinere Effekte oder den rohen IC. GL-012 (Pilot): kein Verdikt. Oekonomisches Etikett (C.2): Portfolio 0,0101, Einzelposition 0,062 (DEC-74 (k)). |
| 3 | Cluster-Einheit | Kalenderwoche; stationaerer Bootstrap (Block 4); N = 52/50 (Test), 114 (Pilot); c = max(1, c_hat) aus v6 bzw. Pilot (c_hat v5e 0,99..1,11 bei konsistenter Wochenzahl). |
| 4 | Selektions-Deflation | K = 4 (F-H32), z_max(4) = 1,052 < 1,6449; Decke ceiling_k4 (vorzeichenbereinigt, v6) < Schwelle, sonst GL-012; BH Nenner 4 (report-only); F-WEEK-BY bindend mit m nach DEC-99 (7), Doppelausweis m = 11; p = Max-p Block-Permutation, 10.000. |
| 5 | Adversariales Fixture | Beta-korrelierte Charakteristik auf einem Panel mit dominantem, autokorreliertem, driftendem Marktfaktor (rho 0,2, Drift 0,002, beta 0,5..2,0) unter fm8 als Primaerstatistik: kein PASS (T1). Pilot-Leck, Siegel-Leck und Panel-Schnitt-Fixture: Abbruch. Bounce-Fixture fuer rev_gap. |
| 6 | Kostenmodell-Bindung | `constants_hash` n/a (kapitalfrei); `tradability3` nicht gebaut. |
| 7 | Irreversibilitaets-Probe | nachladbar (Bybit v5 oeffentlich; Harvest-Export DEC-84). |
| 8 | Positivkontroll-Vorschaltung | ja, nach der Uebergabe und vor dem Test, allein (Abschnitt 4): Welt an der gemessenen Streuung F2_real, Injektion realisiert, 10-%-Regel DEC-94 (5). |
| 9 | Kapital/Steuer/Venue | n/a kapitalfrei; Zahler nach 2024: Delisting-Hazard ~50 % (Etikett). |
| 10 | Stress-Episode | Abdeckungsnachweis STRESS_REL/STRESS_ABS je Fenster aus v6; die Listen werden **nur mit Datumsfilter** geladen (<= 2026-06-28 Test, <= 2024-06-30 Pilot), spaetere Eintraege nie gelesen oder ausgegeben (DEC-96 E3). Drittfassung (Kalender bis 2026-06-30): W1 22/2, W2 8/1. Nie Filter. |
| 11 | Ergebnis-Artefakte (DEC-53) | Pilot: Wochenserie je Variante (CSV + sha256), Bootstrap-Fingerprint, `h32_pilot.json` (result_sha256). Test: Wochenserie je uebergebenem Eintrag und Fenster, Bootstrap- und Permutations-Fingerprints, `h32_run_fingerprint.json` (Seed, Bit-Generator, Code-Hash, Daten-Fingerprints, Panel-Schnitt-Datum, Pilot-sha256), Haupt-JSON + MD. Fehlt etwas: KEIN VERDIKT. |
| 12 | Test-Pflichten | T0-T7, Abschnitt 5. |

---

### 4. Positivkontroll-Regel (woertlich, vorab fixiert)

> Die Positivkontrolle laeuft nur, wenn mindestens eine Variante uebergeben wurde, allein und vor dem Test, mit der
> registrierten YAML und dem Pilot-Ergebnis (beide sha256-gesperrt), auf der realen Wochenform von W1 und W2 (Wochen,
> PIT-Masken, K_t, `returns_valid`; Panel <= 2026-06-28), mit synthetischen Renditen (reale Renditen werden nicht
> uebergeben).
> **Welt je Fenster:** stress-Kalibrierung (rho_f, beta_sd, null_scales aus der YAML; W2 aus v6), Marktspalte = Faktor,
> Drift 0, plus 8 Sektorbloecke mit Schock sigma_g; sigma_g wird per Bisektion (Seeds 2000..2049) so gewaehlt, dass die
> Wochen-SD des fm8-IC der uebergebenen Variante in der Negativkontrolle **sqrt(v_fm8_W + max(F2_null,W,v, F2_real,v))**
> auf +-5 % trifft (F2_null = sd_week^2 - v_fm8 aus v6; F2_real aus dem Pilot); ist F2_real <= F2_null, ist sigma_g = 0.
> **Injektion:** das PRD-Positiv-Fixture (Signal in der Charakteristik, unabhaengig vom Beta); die Amplitude wird auf
> den Seeds 1000..1049 (gemeinsame Zufallszahlen positiv/negativ) so kalibriert, dass der **realisierte**
> Injektionseffekt (Mittel positiv minus negativ der fm8-Statistik) im bindenden Fenster
> 1,6449 x SE_T,W + 0,8416 x SD_T,W auf +-5 % trifft (MDE80 ohne Gutschrift; die Gutschrift traegt die Null selbst).
> **Urteils-Seeds:** 53..252 (200), positiv und negativ; Gate-Kette = Bedingungen (1a)-(1c) und (4b) des Tests mit den
> eingefrorenen Konstanten.
> **BESTANDEN genau dann, wenn fuer jede uebergebene Variante:**
> (a) die Wochen-SD des fm8-IC der Kontrollwelt <= 1,10 x SD der Power-Zeile in jedem Fenster (DEC-94 (5));
> (b) der Anteil der Seeds mit PASS im bindenden Fenster >= 0,734 (= 0,80 - 2,326 x sqrt(0,16/200));
> (c) die falsche PASS-Quote der Negativkontrolle je Fenster <= 0,086 (= 0,05 + 2,326 x sqrt(0,0475/200));
> (d) der realisierte Injektionseffekt auf den Urteils-Seeds innerhalb +-10 % des Ziels liegt.
> Ausgabe "Positivkontrolle BESTANDEN"/"NICHT BESTANDEN"; rc 0 nur bei BESTANDEN, 3 bei NICHT BESTANDEN, 1 bei Abbruch.
> Nicht bestanden: kein Test, Ursachenanalyse, neue DEC.
> **Report-only:** dieselbe Kontrolle zusaetzlich in der woertlichen PRD-/DEC-89-Sektorwelt (Schock 0,375 sigma_e) und die
> gemeinsame C10-Quote.

Etikett (A-7): Die Welt-Kalibrierung an F2_real statt der woertlichen PRD-Sektorwelt ist eine Gabelung **Richtung
Testbarkeit** (die PRD-Welt erhoeht die Wochen-SD um +17,6 %, Review +19 %, und verletzte die 10-%-Regel gegen eine
Ein-Faktor-Power-Zeile); die Realismuspruefung leistet F2_real aus dem Pilot.

---

### 5. DEC-39-Trio und Test-Pflichten

| Stufe | Inhalt |
|---|---|
| T0 | Unit-Tests: Panel-Schnitt, Pilot-SE (P-1 (4)), Band, t, F2_real/c_real, SE_T,W/SD_T,W, m*, Regel U (jede Bedingung einzeln), mu_sel (bekannte Werte der abgeschnittenen Normalverteilung), vorzeichenbereinigte Decke, BY-Schwelle 0,10 / (m x H_m), Gate-Funktion |
| T1 positiv | stress-Welt der Fensterform mit **realisiertem** fm8-Injektionseffekt = MDE80 (Amplitude auf den realisierten Effekt kalibriert, nicht nominal): Fensterbedingung besteht mit Quote ~0,8; uebergebener Eintrag besteht end-to-end |
| T1 null | signalfreie stress-Null: falsche PASS-Quote je Fenster <= alpha + MC-Toleranz; Uebergabequote im Pilot <= 0,01 |
| T1 adversarial | Beta-Proxy-Charakteristik bei dominantem, autokorreliertem, driftendem Markt (rho 0,2, Drift 0,002, beta 0,5..2,0): kein PASS unter fm8 primaer; Pilot-Leck: Abbruch, wenn eine Outcome-Woche nach 2024-06-30 erreicht wird; Siegel-Leck Test-Modus: Abbruch bei Outcome nach 2026-06-28; **Panel-Schnitt:** ein Panel mit Tagen nach dem Stichtag wird nachweislich abgeschnitten (Betas und Charakteristiken identisch zu einem Panel, das am Stichtag endet), sonst Abbruch |
| T2 | Determinismus N >= 3 mit Fingerprint (Pilot, Test, Positivkontrolle, v6) |
| T3 | kein Checkpoint (Round-Trip ueber T7, wie Drittfassung) |
| T4 | Uebergabe-Arithmetik auf konserviertem Pilot-Payload (Regel U rein funktional, zweimal gleich); Gate- und F-WEEK-Arithmetik auf konserviertem Test-Payload; Monotonie: hoeherer x_P kippt nie von Uebergabe zu GL-012, groessere SE oder groesseres m* nie von GL-012 zu Uebergabe; Neulauf-Sperre |
| T5 | Pins: z_krit, mde_faktor, alpha, Block, Replikate, Seed, w_judged 52/50, W_P 114, n_perm 10.000, Panel-Schnitt-Daten, v6-Konstanten in jedem Payload |
| T6 | Legacy-Import-Sperre |
| T7 | Artefakt-Round-Trip: Pilot- und Testserien plus Seed reproduzieren x_P, SE_P, die Gate-Schaetzer und die Permutations-p bitgleich; fehlt ein Artefakt: KEINE UEBERGABE bzw. KEIN VERDIKT |

---

### 6. Kill-Bedingungen (vorab) und Etiketten statt Kill

| Bedingung | Folge |
|---|---|
| min K_t < 117 im Pilot, < 134 in W1/W2 (PRD 5.3 Kill (2)) | Abbruch (heute: P 120, W1 345, W2 514 - nicht ausgeloest) |
| Panel nicht geschnitten / Datum nach dem Stichtag erreicht | Abbruch (KEINE UEBERGABE bzw. KEIN VERDIKT) |
| Regel U verfehlt | GL-012 (Pilot) des Eintrags, kein Verdikt |
| ceiling_k4 >= Schwelle | GL-012 des Eintrags vor dem Verdikt |
| Null-Nachrechnung ausserhalb +-10 %, Pin, Fingerprint, Artefakt, Pilot-sha256 | KEIN VERDIKT (ganzer Lauf) |
| zweiter Pilotlauf ohne DEC | Abbruch |
| Positivkontrolle NICHT BESTANDEN | kein Test, neue DEC |
| Bounce (nur rev_gap) | KEIN PASS |
| F-WEEK-BY lehnt nicht ab | DROP (Etikett), am Wellenschluss |

Etiketten statt Kill: Liquiditaet, Survivorship (synthetisch), BH, Gap eine Woche (rev_gap), Delisting =
Announcement-Datum, NO_HISTORY (W1 LIT/MON/DATA, W2 SPCX), "fm8 entfernt nur das BTC-Beta; Sektor-/Stilfaktoren bleiben
Teil der gemessenen Groesse", "fm8-Skala: beta-unabhaengiges Signal erscheint zu ~75 %", "Pilot aus anderem Marktregime
(2022-2024, Aera-Uebergang ~Mitte 2024); Screening, nie Konfirmation".

---

### 7. Etikett C.17 (Wortlaut-Vorschlag) und Kontamination

> "H-32 (A3-fm8): Fuer die fm8-Statistik von mom1/mom2/mom4/rev_gap wurde weder in W1/W2 noch im Pilotfenster
> 2022-04..2024-06 eine reale IC gelesen. Gesehen: (a) Persistenz-Null W1/W2 - AR(1) je Symbol auf den
> Wochenrenditen der Fenster (den H-32-Outcomes); Null-Mittel und Quantile je Variante, richtungstragend: fuer
> mom1/mom2/mom4 negativ, fuer rev_gap positiv, also gegen die registrierten Richtungen (Roh-IC, modellbasiert,
> vermutlich ueberwiegend Kendall-Bias); (b) Survivorship-Differenz des rohen 4-Wochen-Momentum-IC IC_union -
> IC_survivors +0,0033 [-0,0076; +0,0132] ueber 271 Wochen (WP-7 B3, ganze Historie); (c) Faktoranteil (R^2 Rendite auf
> PIT-Beta, vorzeichenfrei) W1 3,2 %, W2 1,4 %; (d) Streuungen der Fenster (sigma_f, rho_f, sigma_e, Symbol-Vol,
> sigma_xs, Boden, K), A1-Groessen W1/W2 (EW-Faktor-SD, Beta-Fehlanpassung, Funding-Spread, psi), A1-Funding-Bein-Mittel
> der Pilotperiode implizit (~83 bp/Woche), H-27-Nuisance 2021-03-24..2024-05-31 (Marktebene); (e) synthetische
> Survivorship- und Null-Groessen; (f) Literaturband 0,004..0,012 (Weg B) / 0,033 (Ficura-A*, Large and Liquid) /
> negativ bis ~0 breit, ungedaempft (auf fm8-Skala ~0,75-fach); Ficura: Momentum grosser Coins seit 2021 nicht profitabel
> (Stichprobe bis 2022-12, ueberlappt den Pilot). Existiert, nie geoeffnet: WP-7-Rohserie des 4-Wochen-Momentum-IC (alle
> Wochen), L-IC-Details 2021-03..2024-06 in den Siegeldateien v5c/v5d/v5e (decken das Pilotfenster). Nie berechnet:
> Beta-Kalibrierungs-IC, Lag-Profil. Pilotperiode: A1 hat dort A3-Faktorrenditen gerechnet, gespeichert nur
> R^2/Steigungen/Residualstreuung, kein Mittel. W2-Kalibrierung v5e enthaelt die Woche 2026-06-29..07-05 (vor DEC-96;
> in v6 ersetzt). Aera-Uebergang ~Mitte 2024 an der Grenze Pilot/W1. Vorwissen der Agenten ueber Marktniveaus
> 2022-2026: nicht quantifizierbar, nicht verwendet."

Nach dem Pilot zusaetzlich (DEC-99 (5)): "Pilot 2022-04-18..2024-06-17: fm8-IC der vier Varianten gesehen (x_P, SE_P je
Variante, result_sha256 ...); Pilotabschnitt fuer korrelierte Statistiken verbraucht."

---

### 8. Entscheidungsrelevanz und Nicht-Wiederholungs-Nachweis (C.1)

- H-32 ist eine **neue Hypothese** mit eigenem K (DEC-58 E2, DEC-92 "Was nicht folgt", GL-032), erste Anwendung von
  DEC-99. F-XSEC1 hat nie gerechnet; H-32 wiederholt kein geurteiltes Experiment. Unterschiede zur Drittfassung: fm8 als
  Primaerstatistik (Wochen-SD ~0,05 statt Roh-IC 0,13), P-1-Schwelle (DEC-94), Prior aus dem Pilot (DEC-99), W2 am
  Blind-Siegel geschnitten (DEC-99 (8)), K = 4, F-WEEK-Zaehlung DEC-99 (7).
- Gegen D.7 (C-06/H-07/H-08) wie Drittfassung: Breite K_t >= 345 (Test) bzw. >= 120 (Pilot) statt N = 5; Wochen- statt
  Stundenhorizont; Beta-Neutralisierung; survivorship-freies Union-Panel.
- PASS (nach F-WEEK) -> Tradability-Registrierung; DROP -> fuer die Charakteristik "fm8-IC >= MDE80 nicht vorhanden"
  (beta-unabhaengiges Signal ~0,027 bei mom1, fm8-Daempfung), ausdruecklich KEIN Urteil ueber kleinere Effekte und ueber
  den rohen IC; GL-012 (Pilot) -> kein Verdikt, W1/W2 bleiben blind fuer kuenftige Hypothesen.

---

### 9. Abweichungen von PRD/Drittfassung (registriert, etikettiert)

1. Primaerstatistik fm8 statt roher IC; roher IC wird nicht gerechnet (Blindheitsschutz).
2. Schwelle z_krit 1,6449 (P-1) statt 2,4865; Doppelausweis A3-Praxis.
3. Prior aus dem Pilot (DEC-99) statt Literatur 0,03.
4. W2 endet 2026-06-28 (w_judged 50, DEC-99 (8)); Panel vor jeder Rechnung geschnitten; W2 neu kalibriert.
5. Null mit Beta-Vorlauf (v6), Power-Zeile mit e_se_rule und se_mean; Null-Quantil auf Niveau 0,95 statt 0,9936
   (P-1 (1)).
6. Selektionsdecke vorzeichenbereinigt (Nebenbefund: `nulls._mean_of_max` nimmt rohe Vorzeichen).
7. Kein DEC-52-Zweig (Regel U), kein Lag-Profil, kein Beta-Kalibrierungs-IC, keine Persistenz-Null.
8. F-WEEK: m nach DEC-99 (7) (nur getestete Eintraege), Doppelausweis m = 11; p = Block-Permutations-Max-p mit 10.000.
9. rev_gap im Ein-Wochen-Gap (DEC-87 (B)) - PRD-Ein-Tages-Design nicht getestet.

---

### 10. Registry-YAML-Block (Entwurf, Template PRD 3.4)

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
  - {id: P,  von: 2022-04-18, bis: 2024-06-30, wochen_geurteilt: 114, rolle: pilot_nicht_urteilstragend, panel_schnitt: 2024-06-30}
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen_geurteilt: 52, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-28, wochen_geurteilt: 50, rolle: urteilstragend, panel_schnitt: 2026-06-28}
fenster_regel: "C10_hart (Regel U laesst nur C10 zu)"
threshold: {formel: "max(1.6449 * SE_W, q95_W)", SE_W: "max(floor_fm8/sqrt(W), SD/sqrt(W), SE_stat stationaer Block 4)", ref: "ERSTFASSUNG 1.9; v6"}
structural_null: {komponenten: [faktorerhaltende_null_stress_fm8, q95_driftfrei_und_drift, selektionsdecke_k4_vorzeichenbereinigt, bounce_rev_gap], ref: "v6 windows.<W>.frozen_v6"}
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
  detectable_effect_mde80_vorab: {W1: {mom1: 0.0206, mom2: 0.0237, mom4: 0.0287, rev_gap: 0.0195}, W2: {mom1: 0.0165, mom2: 0.0184, mom4: 0.0221, rev_gap: 0.0167}}
  end_power_f_week_at_mde80_vorab: {m1: [0.72, 0.76], m4: [0.44, 0.50], m11_report_only: [0.23, 0.28]}
  zuordnungsregel: "Regel U (ERSTFASSUNG 1.8), power_p1.assign_regime; Doppelausweis assign_regime_a3_practice"
  ref: "state/herleitung_h32/power_h32.json"
selection: {K: 4, z_max: 1.052, ceiling: "v6 ceiling_k4", bh_denominator: 4, over_family: F-WEEK}
fdr: {p: "Max-p ueber W1/W2, Block-Permutation (Block 4) der Outcome-Wochen vor fm8, einseitig", n_perm: 10000, seed: 53, family: "F-H32 BH 0.10 report-only, Nenner 4", over_family: "F-WEEK BY 0.10 bindend, m nach DEC-99 (7)", doppelausweis_m: 11}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, label: "Etikett C.2"}
decision_relevance: {on_pass: "Tradability-Registrierung nach F-WEEK", on_drop: "fm8-IC >= MDE80 der Variante nicht vorhanden (beta-unabhaengig ~MDE80/0,75)", on_gl012_pilot: "kein Verdikt, W1/W2 bleiben blind"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", zahler_post_2024: "Delisting-Hazard ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json, stress_abs.json (nur mit Datumsfilter <= Panel-Schnitt)", rolle: abdeckungsnachweis}
irreversibility_probe: {ergebnis: nachladbar}
positive_control: {vorgeschaltet: true, regel: "ERSTFASSUNG 4", seeds: "53..252", welt: "sigma_g an F2_real (Null-SD Untergrenze); PRD-Sektorwelt report-only"}
fixtures: {positive: "T1 positiv (realisierter fm8-Effekt = MDE80)", null: "T1 null (stress-Null)", adversarial: "T1 Beta-Proxy + Pilot-Leck + Siegel-Leck + Panel-Schnitt"}
artifacts: {pilot: "h32_pilot_<v>_P_ic_weekly.csv + sha256, h32_pilot.json", test: "h32_run_<v>_<W>_ic_weekly.csv + sha256, h32_run_fingerprint.json"}
fdr_family: "F-H32 (K = 4, BH 0.10 report-only, p = 1 ohne Uebergabe)"
over_family: "F-WEEK (BY 0.10, m = getestete Eintraege, DEC-99 (7); Doppelausweis m = 11)"
feasibility_verdict: "offen bis Pilot (Regel U)"
constants_hash: "n/a - kapitalfrei"
data_fingerprints: ["panel_export 03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb", "union_range a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933", "as_of 2026-09-28", "panel_cut_test 2026-06-28", "panel_cut_pilot 2024-06-30"]
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e, Vorlauf v6]
etiketten: ["zugelassen nur durch DEC-99 (Pilot-Prior)", "C.17 (Abschnitt 7)", "fm8-Skala (Daempfung ~25 %)"]
```

---

### 11. Registrierungsdatei (Schema-Entwurf `state/registered/h32_v1.yaml`)

```yaml
hypotheses:
  H-32_mom1:    {hypothesis: H-32, variant: mom1,    direction: positive}
  H-32_mom2:    {hypothesis: H-32, variant: mom2,    direction: positive}
  H-32_mom4:    {hypothesis: H-32, variant: mom4,    direction: positive}
  H-32_rev_gap: {hypothesis: H-32, variant: rev_gap, direction: negative}
primary_statistic: fm_neutral_8w          # Pflicht; roher IC wird nicht gerechnet
alpha: 0.05
z_krit: 1.6448536                          # DEC-94 (1)/(2); Zahl, kein Faktor ohne alpha
mde_faktor: 2.4865                         # nur Power-Zeile, nie Schwelle
seal:                                      # NEU (DEC-96 E3, DEC-99 (3)/(8), Review B-6)
  panel_cut_test: '2026-06-28'             # Test-Modus und Vorlauf v6: Tagesdaten <= Stichtag vor jedem Bau
  panel_cut_pilot: '2024-06-30'            # Pilot-Modus
  stress_list_date_filter: true            # Stress-Listen nur <= Stichtag laden, spaetere nie ausgeben
fdr:                                       # NEU (A-3)
  p_statistic: block_permutation_fm8_window_mean   # Outcome-Wochen in Bloecken permutiert, danach fm8
  sided: one
  combine: max_p                           # schwaecheres Fenster (DEC-74 (e))
  block_len: 4
  n_perm: 10000                            # DEC-74 (e): >= 10.000
  seed: 53
  family: {name: F-H32, method: BH, alpha: 0.10, denominator: 4, report_only: true}
  over_family: {name: F-WEEK, method: BY, alpha: 0.10, binding: true, m_rule: "DEC-99 (7): nur getestete Eintraege", double_statement_m: 11}
selection: {K: 4, ceiling: ceiling_k4}
pilot_window:                              # NEU
  start: '2022-04-18'
  end: '2024-06-30'
  first_formation_week: '2022-04-18'
  last_formation_week: '2024-06-17'
  last_outcome_day: '2024-06-30'
  w_pilot: 114
  k_min_rule: 117
  role: pilot_nicht_urteilstragend
  single_run: {required: true, rerun_requires_dec: true}       # DEC-99 (3)
  se_rule: {floor: true, sd: true, stationary_bootstrap: {mean_block: 4, n_rep: 1000, seed: 53}}
  band: {level: 0.80, form: normal_zweiseitig, z: 1.2816}
  frozen_v6: {m_P: {mom1: .., mom2: .., mom4: .., rev_gap: ..}, calibration: {...nur Streuung/Autokorrelation...}, k_fm8_series_sha256: ..}
  report_only: [bootstrap_percentile_band, liquidity_buckets_3_10, ic_without_bucket_1, mu_sel, power_at_mu_sel]
  not_computed: [raw_ic, lag_profile, beta_calibration_ic]
handover_rule:                             # NEU
  version: U-2                             # nach Review: m* mit m_P, e_se_rule/se_mean, mu_sel
  conditions:
    - {id: i,   text: "x_P > 0 in registrierter Richtung"}
    - {id: ii,  text: "x_P - m* >= max_W (z_krit * SE_T,W + 0.8416 * SD_T,W)"}
    - {id: iii, text: "t_P >= t_min"}
  t_min: 2.0
  prior_reading: point                     # Lesart A; 'lower80' waere Lesart B
  se_T: "max(e_se_rule_W (v6), SE_W,Pilot)"
  sd_T: "max(se_mean_W (v6), SE_W,Pilot)"
  pilot_k_adjusted: "SE_W,Pilot = sqrt(max(1, c_real)) * sqrt(v_fm8_W + F2_real) / sqrt(w_judged_W)"
  null_mean_credit: "m* = max(0, m_P, m_W1, m_W2) in Richtung"
  regime_function: power_p1.assign_regime
  double_statement: [power_p1.assign_regime_a3_practice, mu_sel]
  mu_sel: "Loesung von P_mu(X >= x_P | X >= c_v) = 0.5, X ~ N(mu, SE_P^2), c_v = MDE80*_v + m*"
  on_fail: {status: gl012_pilot, p_value: 1.0, in_f_week_m: false}
  result_lock: "--pilot-result + --pilot-result-sha256 im Testlauf; Uebergabe bitgleich nachgerechnet"
windows:
  W1:
    start: '2024-07-01'
    end: '2025-06-30'
    w_judged: 52
    calibration: {measured: {...v5e, in v6 nachgerechnet...}, stress: {...}, zero: {...}}
    null_scales: {sigma_f: 0.06685192489159383, sigma_e_used: 0.1206430784847655}
    frozen_v6: {se_mean: {mom1: .., mom2: .., mom4: .., rev_gap: ..}, e_se_rule: {...}, sd_week: {...}, null_mean: {...},
                q95: {...}, q95_driftfree: {...}, q95_drifting: {...}, ceiling_k4: .., floor_fm8: .., v_fm8: .., k_fm8_series_sha256: ..}
    bounce_sigma_true: 0.1718564938769564
    survivorship: {mom1_diff_in_ic_min_units: -0.19807571898782755, rev_gap_diff_in_ic_min_units: -0.18910982801933468}
  W2:
    start: '2025-07-01'
    end: '2026-06-28'                      # DEC-99 (8)
    w_judged: 50
    calibration: {...v6 NEU auf dem geschnittenen Fenster...}
    null_scales: {...v6 NEU...}
    frozen_v6: {...}
    bounce_sigma_true: ..                  # v6 NEU (geschnittenes Fenster)
    survivorship: {...v6 NEU...}
beta_control: {method: fm_neutral_8w, beta_window_weeks: 8}
rules: {seed: 53, n_reps: 1000, mean_block: 4, null_level: 0.95, bounce_spread: 0.003621}
positive_control:
  seeds: [53, 252]
  calibration_seeds_injection: [1000, 1049]
  calibration_seeds_world: [2000, 2049]
  world_sd_target: "sqrt(v_fm8_W + max(F2_null_W, F2_real))"      # A-7
  inject_target: "realisiert: z_krit * SE_T,W + 0.8416 * SD_T,W im bindenden Fenster"
  criteria: {sd_ratio_max: 1.10, pass_share_min: 0.734, neg_pass_max: 0.086, injection_tolerance: 0.10}
  report_only: [prd_sector_world_0375, joint_c10_share]
data_fingerprints:
  union_range_fingerprint: a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a
  delisting_dates_sha256: 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933
```

---

### 12. Bauliste (Abnahme durch den Orchestrator; additiv, A3-Code unberuehrt). Neu/geaendert nach Review markiert.

0. **NEU - Panel-Schnitt** (B-6): Tagespanel auf <= `seal.panel_cut_*` abschneiden vor jedem Bau; Fingerprint vorher auf
   den Dateien, Maximaldatum-Waechter nachher; Stress-Listen nur mit Datumsfilter; T1-Test.
1. **Vorlauf v6** (Realdaten, nur Nuisance, neues Modul): Null mit 8 Beta-Vorlaufwochen fuer W1/W2, K = 4, 1.000
   Replikate, driftfrei und Drift 0,002; `frozen_v6` je Fenster; **NEU** `e_se_rule` (A-6); **NEU** W2-Neukalibrierung auf
   dem geschnittenen Fenster und W1-Nachrechnung als Determinismus-Kontrolle; **NEU** Pilotperioden-Kalibrierung mit
   Waechter "kein Mittel" und `m_P` je Variante (A-6); K_fm8-Reihen fuer P, W1, W2 nur aus `returns_valid`;
   Stress-Abdeckung nur fensterbeschraenkt; Template-Emitter fuer `h32_v1.yaml`.
2. **Pilot-Modus** `--pilot` (CLI neu, z. B. `scripts/h32_fm8.py`): Startsperre, **NEU** Neulauf-Sperre (DEC-99 (3)),
   Panel-Schnitt 2024-06-30, Siegel-Waechter (PP4), Pilot-Statistiken (1.7), Regel U-2 (m*, SE_T/SD_T), `power_p1`-
   Zuordnung, **NEU** mu_sel und Power an mu_sel, DEC-53-Artefakte, `h32_pilot.json`.
3. **Testlauf** `--run`: Pilot-Sperre (P0'), Panel-Schnitt 2026-06-28 (P0''), nur uebergebene Eintraege, P-1-Gate als
   neue reine Funktion (T4), `power_p1.stationary_bootstrap_se`, Siegel-Waechter (P7), **NEU** F-WEEK-Ausgabe
   (Block-Permutations-p 10.000, Max-p, BY mit m nach DEC-99 (7), Doppelausweis m = 11), keine Nebengroessen.
4. **Positivkontrolle** `--positive-control`: **GEAENDERT** Welt-SD an sqrt(v_fm8 + max(F2_null, F2_real)), Injektionsziel
   mit e_se_rule/se_mean, realisiert kalibriert; 200 Seeds; Kriterien Abschnitt 4; **NEU** Bericht in der PRD-Sektorwelt.
5. **Neue vorzeichenbereinigte Decke** (nicht `nulls._mean_of_max` aendern).
6. **Tests** Abschnitt 5 (**NEU** T1 Panel-Schnitt, T1 positiv realisiert, T0 mu_sel und BY-Schwelle, T4 Neulauf-Sperre
   und F-WEEK-Arithmetik); Gesamtzahl der Tests steigt, keine wird reduziert.

Aufwand: ~1.650 Zeilen Code, ~1.270 Zeilen Tests (nach Review +~300 / +~220), zwei Bau-Sitzungen; Cloud: v6 ~1-1,5 h,
Pilot < 15 min, Positivkontrolle ~15-30 min, Test ~1 h Null-Nachrechnung plus ~1 h Permutationen (UNBELEGT).

---

### 13. Ablauf und Rueckbauweg

DEC-99 (beschlossen) -> EV-Entscheidungen -> Bau -> Abnahme -> Vorlauf v6 (Panel <= 2026-06-28) -> YAML + sha256 ->
Registrierung -> Pilot (genau einmal, Panel <= 2024-06-30) -> Uebergabe-Vermerk mit sha256 -> [keine Uebergabe: GL-012
(Pilot), Ende, W1/W2 ungeoeffnet] -> Positivkontrolle allein -> [NICHT BESTANDEN: neue DEC] -> Test W1/W2 -> Gate-Check
nur gegen diesen Text -> GL-Eintrag (vorlaeufig) -> F-WEEK-BY am Wellenschluss. Rueckbauweg: Registry append-only;
dieser Entwurf hat keine Rechtswirkung.
