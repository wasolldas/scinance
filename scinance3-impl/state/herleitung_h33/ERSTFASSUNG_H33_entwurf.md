## H-33 - Erstfassung (ENTWURF 2026-10-26): beta-neutrales Kurzfrist-Reversal 1/2/4 Wochen (fm8-Wochen-Querschnitts-IC, negative Richtung) auf W1/W2 mit Literatur-Prior, Klasse W, kapitalfrei

> **NICHT REGISTRIERT, kein Verdikt.** Entwurf der Herleitung; registrieren darf nur der Orchestrator. **Registrierung
> blockiert: Prior UNBELEGT** (DEC-102 E3; `ENTSCHEIDUNGSVORLAGEN.md` EV-1) - Rueckfrage an den Nutzer mit dem Prior-Gitter.
> **Etikett (DEC-102 E2, Pflicht in jeder Datei):** "beschlossen nach Kenntnis von GL-035 (Pilot-Vorzeichen der
> mom-Varianten); Richtung Testbarkeit; Richtungswahl nach Kenntnis korrelierter Daten eines anderen Fensters
> (2022-04..2024-06)".
> Fundstellen: `[fj: <datei>#<json-pfad>]` mit `power_h33.json` (sha256 `026494b6681fb3d5b97d0e2cf77c9845b953bde7e31e97f976bbf3207b5b5bc9`),
> `nuisance_neg.json` (sha256 `05e6f2a0a396d0be008579e6d160147c2002d7229a176a01c0f2c1b2076f0835`), v6b `h32_prelaunch.json`
> (sha256 `f872a3af...f98c`), v6b `h32_prelaunch_p_replicates.json` (sha256 `3c498e07...56ef`); `[EV-n]` =
> `ENTSCHEIDUNGSVORLAGEN.md`. Ergebnisblind: keine reale IC, kein Outcome, kein Panel; Siegeldateien nie geoeffnet.

### 0. Vorbedingungen der Registrierung

| # | Vorbedingung | Stand 2026-10-26 |
|---|---|---|
| V1 | DEC-102 (Rahmen, Etikett, Prior-Regel, Ausschluss rev_gap) | beschlossen |
| V2 | **Prior aus der Literatur** | **UNBELEGT** -> Nutzerentscheid (Referenz-Lesart R3 empfohlen, Gitter [EV-1 2.6]) |
| V3 | EV-0 (C.17-Befund Persistenz-Null in H-33-Richtung) | offen, Nutzerkenntnis |
| V4 | EV-2..EV-6 (K, Nuisance-Lesart T/S, v7, Gate-Details, DEC-52) | Orchestrator, **vor** der Prior-Entscheidung des Nutzers festzulegen |
| V5 | Zuordnung je Eintrag (mechanisch, `power_p1.assign_regime`, Abschnitt 1.7) | offen bis V2/V4 |
| V6 | nur wenn ein Eintrag C10: Bau (Abschnitt 12), Abnahme, **Vorlauf v7** zweimal bitgleich, PP3-Trockenprobe, YAML + sha256 | offen |
| V7 | Review (adversarisch) und Gate-Review ohne VETO | offen |
| V8 | Daten: Pins der v6b-Akte unveraendert (union_range `e503bedb...`, delisting_register `a28c7eb7...`, delisted_tree `250a923b...`, delisting_dates `c1306c56...`, universe_excluded `50aaee3c...`, Runner as_of 2026-09-28 / 2021..2026 / allow_partial) | vorhanden |
| V9 | Blind-Siegel DEC-96 E3: Panel-Schnitt 2026-06-28 vor jeder Rechnung | Waechter im Code (H-32) |

---

### 1. Festlegungen

#### 1.1 Klasse, Familie, Varianten
- Klasse W, kapitalfrei. Neue Hypothese H-33 mit eigenem K (DEC-58 E2, DEC-102 E1). Familie **F-H33, K = 3**:
  `H-33_rev1` (Charakteristik mom1), `H-33_rev2` (mom2), `H-33_rev4` (mom4), alle **Richtung negativ** (Reversal).
- Hypothesen-PASS, wenn mindestens ein Eintrag PASS ist (nach F-WEEK); jeder Eintrag wird einzeln berichtet.
- K = 3 bleibt Nenner (Selektionsdecke vorzeichenbereinigt, BH-Nenner 3); Eintraege, die vor der Registrierung GL-012 sind,
  gehen mit p = 1 in den BH-Nenner und zaehlen nicht in m von F-WEEK (DEC-99 (7)).
- Nicht aufgenommen [EV-2]: rev_gap (DEC-102 E4), 2-Wochen-Reversal mit Gap, Liquiditaets-Universen.

#### 1.2 Panel, Universum, Datenbezug
Wie H-32 (registrierte Fassung `state/registered/h32_v1.yaml`): Union `panel_1d` + Delisted-Baum v2, PIT-Maske DEC-72,
Register-Datum = letzter Handelstag (DEC-100 E1), `--allow-partial`, Universum **lineare USDT-Perpetuals** (DEC-101 E1;
1.182 -> 1.066 Symbole; Filter vor Schnitt und Rechnung), Fingerprints und Runner-Pins wie V8, Panel-Schnitt 2026-06-28
vor jedem Bau, Maximaldatum-Waechter. Bezug nur ueber exakte Schluessel des Harvest-Exports, nie unter `data/harvest`.

#### 1.3 Fenster (REZENZ, DEC-99 (1); kein Pilot)
| Fenster | Formationswochen | Outcome-Wochen | w_judged | K alive min/Median/max | Rolle |
|---|---|---|---:|---|---|
| W1 | 2024-07-01..2025-06-23 | 2024-07-08..2025-06-30 | 52 | 343 / 416,5 / 500 | urteilstragend |
| W2 | 2025-07-07..2026-06-15 | 2025-07-14..2026-06-22 (Ende 2026-06-28) | 50 | 501 / 526 / 545 | urteilstragend, juengstes Fenster (muss bestehen) |

Quelle `[fj: h32_prelaunch.json#windows.<W>.geometry]`, `#windows.<W>.k`. **Kein Pilot** (DEC-102 E2/E5; der Abschnitt
2022-04..2024-06 ist fuer fm8-korrelierte Statistiken verbraucht, DEC-99 (5)). C.10 hart; DEC-52-Zweig ausgeschlossen [EV-6].

#### 1.4 Cluster, Metrik, Konvention
Cluster = Kalenderwoche. Primaerstatistik exakt die H-32-Statistik: Mittel der woechentlichen Spearman-ICs der Charakteristik
(Woche t) gegen das `fm_neutral_8w`-Residuum der Folgewochen-Log-Rendite (t+1), `close_at_last`, min 10 Symbole. **In
Richtung: y = -1 x Statistik.** fm8-Skala: ein beta-unabhaengiges Signal erscheint zu ~75 % (0,754 synthetisch fuer mom1;
mom2/mom4 vermutlich staerker gedaempft).

#### 1.5 Charakteristiken
mom_n = Summe der Wochen-Log-Renditen t-n+1..t, n = 1/2/4 (`characteristics.momentum_characteristic`). rev1 teilt den
Wochenschluss t mit dem Outcome (kein Gap) - Bounce-Pruefung fuer alle drei [EV-5].

#### 1.6 Null und eingefrorene Groessen (negative Richtung) `[fj: nuisance_neg.json#windows]`
- Faktorerhaltende Null der v6b-Akte (stress, 8 Beta-Vorlaufwochen, reale Masken, Seed 53), Zellen driftfrei / Drift 0,002.
- **Richtungsfrei, aus v6b:** se_mean, e_se_rule, sd_week (je Maximum der Zellen), floor_fm8, v_fm8, K-Reihen.
- **Null-Mittel:** null_mean_neg = -null_mean_raw je Zelle; eingefroren das groessere in negativer Richtung = **driftfreie
  Zelle** (alle sechs Faelle). Unter DEC-101 E2 keine Gutschrift (m < 0).
- **q95_neg** = max(q95_neg_1000 ueber beide Zellen, q95_neg_10000 der bindenden Zelle) (DEC-101 E5), q95_neg einer Zelle =
  -Quantil_0,05 ihrer Rohreplikate; **die driftfreien Replikate liegen nicht vor -> Vorlauf v7** [EV-4]. Bis dahin
  vorlaeufig: Form der Drift-Zelle (dev95 = q95_neg_drift - m_drift).
- Selektionsdecke `ceiling_k3_neg` (Mittel des Maximums der vorzeichenbereinigten Fenstermittel ueber rev1/rev2/rev4; Zelle wie
  H-32 driftfrei -> v7; Drift-Zelle als Bericht).

| Fenster | Var. | se_mean | e_se_rule | sd_week | m_neg driftfrei (bindend) | m_neg Drift | q95_neg Drift 1.000 / 10.000 | dev95 Drift | T_neg = z e_se_rule |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| W1 | rev1 | 0,007302 | 0,007441 | 0,051279 | -0,001221 | -0,001290 | 0,009992 / 0,010696 | 0,011986 | 0,012240 |
| W1 | rev2 | 0,008090 | 0,008123 | 0,056866 | -0,001583 | -0,001679 | 0,010274 / 0,011489 | 0,013168 | 0,013361 |
| W1 | rev4 | 0,009768 | 0,009370 | 0,065995 | -0,001934 | -0,002066 | 0,012377 / 0,012766 | 0,014832 | 0,015412 |
| W2 | rev1 | 0,006197 | 0,006630 | 0,044494 | -0,000847 | -0,000936 | 0,009019 / 0,009293 | 0,010229 | 0,010906 |
| W2 | rev2 | 0,007046 | 0,007084 | 0,048215 | -0,001379 | -0,001502 | 0,009668 / 0,009825 | 0,011327 | 0,011653 |
| W2 | rev4 | 0,008190 | 0,007981 | 0,054924 | -0,001784 | -0,001953 | 0,010826 / 0,010857 | 0,012811 | 0,013127 |

floor_fm8 W1 0,048821 / W2 0,043639; v_fm8 0,002391 / 0,001905. Decke K = 3 (Drift-Zelle, roh / rezentriert, 10.000):
W1 0,0023 / 0,0039, W2 0,0017 / 0,0031; Decke/T <= 0,32 - kein Vor-Verdikt-Kill `[fj: power_h33.json#pre_verdict_kill]`.

#### 1.7 Prior, Power-Zeile und Zuordnung (ohne Pilot, vor der Registrierung, mechanisch)
- **Prior pi_v** (fm8-Skala, je Variante, aus der Literatur; Wert und Lesart vom Nutzer nach EV-1; Default bei Stille:
  keiner - UNBELEGT blockiert).
- **Power-Zeile** (DEC-94 (3), P-1; Lesart nach EV-3, empfohlen S):
  SE_T,W = e_se_rule (T) bzw. max(e_se_rule, SE_W,F2) (S), SD_T,W = se_mean (T) bzw. max(se_mean, SE_W,F2) (S) mit
  SE_W,F2 = sqrt(c_ref) sqrt(v_fm8_W + F2_ref,v) / sqrt(w_judged_W), F2_ref aus GL-035 (0,010331 / 0,012016 / 0,013072,
  c_ref 1,000), k_ref,W = max(1, sqrt(v_fm8_W + F2_ref,v) / sd_week_W,v) (T: k_ref = 1).
  T_1b = z_krit SE_T + max(0, m); T_1c = q95_eff(k_ref) = max(0, m) + k_ref (q95_neg - m); Fenster-Power
  P_W = Phi((pi_v - max(T_1b, T_1c)) / SD_T); MDE80_W = max(T_1b, T_1c) + z_80 SD_T.
- **Zuordnung:** `power_p1.assign_regime(priors = [pi_v - (max(T_1b, T_1c) - z_krit SE_T,W)]_W, ses = [SE_T,W], sds = [SD_T,W])`;
  C10 -> Eintrag wird getestet; sonst **GL-012 vor der Registrierung** (kein DEC-52-Zweig, EV-6). Doppelausweis
  `assign_regime_a3_practice` (Etikett "zugelassen nur durch DEC-94" falls A3 GL012).
- **MDE80 (negative Richtung)** `[fj: power_h33.json#power_lines.<T|S>.variants.<v>.windows.<W>.mde80_w]`:

| Variante | Lesart T W1 (1b / 1c) | T W2 (1b / 1c) | MDE80\* T | Lesart S W1 (1b / 1c) | S W2 (1b / 1c) | MDE80\* S | A3-Praxis MDE80\* (T) |
|---|---|---|---:|---|---|---:|---:|
| rev1 | 0,018385 / 0,018132 | 0,016121 / 0,015444 | **0,018385** | 0,038892 / 0,039529 | 0,038897 / 0,038595 | **0,039529** | 0,024648 |
| rev2 | 0,020169 / 0,019977 | 0,017583 / 0,017257 | **0,020169** | 0,041388 / 0,041804 | 0,041488 / 0,041761 | **0,041804** | 0,027006 |
| rev4 | 0,023633 / 0,023053 | 0,020020 / 0,019704 | **0,023633** | 0,042878 / 0,042460 | 0,043033 / 0,043110 | **0,043110** | 0,031519 |

(1c)-Spalten vorlaeufig mit der Form der Drift-Zelle (v7 ersetzt sie); unter T bindet (1b) ueberall.
- **Endpower nach F-WEEK** (Pflicht-Ausweis, keine Zuordnungsgrundlage): `estimators.end_power_replicates` mit den
  transformierten Replikaten d' = max(0, m) + k_ref (d_neg - m), BY-Schwelle 0,10 / (m H_m): m = 3 0,0182 (bindend, H-33
  allein), Doppelausweis alte Zaehlung m = 14 (7 + 4 + 3) 0,0022 `[fj: power_h33.json#selection.by_threshold]`. Werte am
  Gitter: [EV-1 2.6].

#### 1.8 Test (nur zugeordnete Eintraege)
- y_W = -1 x Mittel der fm8-Wochen-ICs, W in {W1, W2}, Panel <= 2026-06-28.
- SE_W = max(floor_fm8,W / sqrt(w_judged), SD(IC_t,W) / sqrt(w_judged), SE_stat,W), stationaerer Bootstrap Block 4, 1.000,
  Seed 53 (P-1 (4)).
- k_W,v = max(1, SD(IC_t,W) / sd_week_W,v); q95_eff,W,v = max(0, m_W,v) + k_W,v (q95_neg,W,v - m_W,v) (DEC-101 E2).
- p_W,v aus den 10.000 Replikaten der bindenden Zelle (v7), transformiert d' = max(0, m) + k (d_neg - m); p = (1 + #{d' >= y})
  / (1 + R); Max-p ueber W1/W2.

#### 1.9 Selektion und FDR
- DEC-94 (7): z = max(1,6449, z_max(3) = 0,853) = 1,6449 `[fj: power_h33.json#selection]`.
- Vor-Verdikt-Kill: ceiling_k3_neg,W >= T_W,frozen = 1,6449 x e_se_rule_W,v + max(0, m_W,v) -> GL-012 des Eintrags.
- BH (report-only) F-H33: alpha 0,10, Nenner 3. **F-WEEK** (BY 0,10, bindend, Wellenschluss): m = getestete Eintraege
  (DEC-99 (7)); Doppelausweis m = 14 (report-only). Block-Permutation und Normalnaeherung report-only.

---

### 2. Gate-Text (woertlich, Fassung fuer den Bau)

**Test-Modus (`--run`, Hypothese H-33, ohne Pilot) - Abbrueche vor jedem Verdikt (rc 1, KEIN VERDIKT):**
- (P0) Startsperre: sha256 der `--registered`-Datei = `--registered-sha256`.
- (P0') **Zuordnungs-Sperre:** `prior.source` = `literature`, `pilot` = `none`; die Zuordnung je Eintrag (`assignment`) wird
  aus `prior`, `dispersion_nuisance` und den eingefrorenen Konstanten mit `power_p1.assign_regime` deterministisch
  nachgerechnet und muss bitgleich sein; abweichend = Abbruch. Kein Pilot-Ergebnis wird gelesen.
- (P0'') **PK-Sperre:** `--pc-result` mit sha256 = `--pc-result-sha256`, Ergebnis "Positivkontrolle BESTANDEN" unter
  derselben registrierten Datei; sonst Abbruch.
- (P0''') **Panel-Schnitt:** Tagesdaten auf <= `seal.panel_cut_test` (2026-06-28) abgeschnitten, bevor irgendetwas gebaut
  wird; Maximaldatum-Waechter; Stress-Listen nur mit Datumsfilter.
- (P1) Schema: `hypotheses.*.direction` = `negative`, K = 3, `primary_statistic` = `fm_neutral_8w`, `alpha` 0,05, `z_krit`
  1,6448536, `mde_faktor` 2,4865, je Fenster `frozen_neg` aller 3 Varianten; fehlend oder ungueltig = Abbruch.
- (P2) `beta_control` = fm_neutral_8w / 8. (P3) Daten-Fingerprints, Universums-Pin, Runner-Pins. (P4) T5-Pins (`w_judged`
  52/50, Block 4, n_boot 1.000, Seed 53, n_reps 10.000, Richtung, K). (P4') p-Replikate: Datei-sha256 = `fdr.replicates_sha256`
  (v7), Zelle je Fenster/Variante = `binding_cell_neg`, die ersten 1.000 reproduzieren das eingefrorene `null_mean_neg`.
  (P5) `returns_valid` vorhanden.
- (P6) Null-Nachrechnung je Fenster: se_mean, e_se_rule, null_mean_neg, q95_neg, ceiling_k3_neg je innerhalb +-10 % (bei
  ~0: absolut 1e-4); geurteilt wird gegen die eingefrorenen Werte.
- (P7) Siegel-Waechter: keine Outcome-Woche nach 2026-06-22; kein roher IC, kein Lag-Profil, kein Beta-Kalibrierungs-IC.
- (P8) DEC-53-Artefakte vor jedem Verdikt geschrieben und verifiziert.

**Eintraege mit Zuordnung GL-012:** nicht gerechnet; Verdikt "GL-012 vor der Registrierung: <Prior, MDE80\*, Fenster-Power>",
p = 1 (BH-Nenner 3), nicht in m von F-WEEK.

**Zugeordnete Eintraege - Vor-Verdikt-Kill:** ceiling_k3_neg_W >= T_W,frozen in einem Fenster -> DROP mit Etikett GL-012.

**Vorlaeufiger PASS genau dann, wenn in W1 UND W2 (C.10 hart) gilt:**
- (1a) y_W > 0 (NaN verfehlt), y_W = -1 x mittlerer fm8-Wochen-IC;
- (1b) y_W >= 1,6449 x SE_W (SE_W nach 1.8; NaN oder 0 verfehlt);
- (1c) y_W >= q95_eff,W,v = max(0, m_W,v) + k_W,v (q95_neg,W,v - m_W,v), k_W,v = max(1, SD(IC_t,W) / sd_week_W,v);
- (4b) kein Bounce-Kill, fuer **jeden** Eintrag: |IC_bounce,W,v| >= |Statistik_W| in einem Fenster -> KEIN PASS, Etikett
  "Artefakt Bounce"; IC_bounce,W,v = Mittel ueber die Seeds 53..252 des Bounce-Fixtures (Charakteristik mom_n, Spread
  `rules.bounce_spread` 0,003621, `windows.<W>.bounce_sigma_true`, K = Median der lebenden Symbole).

Sonst DROP mit Etikett der verfehlten Bedingung. Kein DEC-52-Zweig.

**F-WEEK (bindend, am Wellenschluss; DEC-99 (7)):** p je getestetem Eintrag = Max-p (1.8); BY alpha 0,10 ueber alle in der
Welle tatsaechlich getesteten Eintraege (m). Ein vorlaeufiger PASS, den BY nicht ablehnt, wird DROP mit Etikett "F-WEEK-BY
nicht bestanden"; jedes Ergebnis traegt den Doppelausweis "alte Zaehlung m = 14: abgelehnt ja/nein" (report-only).

**Etiketten (report-only, nie Gate-Eingang):** Liquiditaet (Mittel ohne Umsatz-Bucket 1; "Illiquiditaets-Artefakt" unter
0,5 x T_W in Richtung); Survivorship (synthetisch, negative Richtung) +0,47/+0,59/+0,49 (W1) und +0,58/+0,70/+0,64 (W2)
T_neg-Einheiten; BH Nenner 3; "zugelassen nur durch DEC-94" (Doppelausweis); DEC-102-E2-Etikett; C.17 (Abschnitt 7);
"fm8-Skala (Daempfung ~25 %)"; Lesart der Streuungs-Nuisance (EV-3); unskaliertes p report-only.

**Verdikt H-33:** PASS, wenn mindestens ein Eintrag PASS ist (nach F-WEEK); "GL-012 vor der Registrierung", wenn kein Eintrag
zugeordnet ist; sonst DROP.

---

### 3. Die zwoelf Pflichtzeilen (PRD 3.3)

| # | Zeile | Inhalt |
|---|---|---|
| 1 | Power | alpha 0,05 einseitig je Fenster (z_krit 1,6449), Power 0,80, Cluster Woche, W 52/50; SE/SD nach Lesart T (v6b-Null) oder S (groessere SE mit GL-035-Streuung, DEC-94 (5), empfohlen); MDE80\* T rev1/rev2/rev4 0,0184 / 0,0202 / 0,0236, S 0,0395 / 0,0418 / 0,0431; Prior aus der Literatur, **UNBELEGT** (Gitter EV-1 2.6); Zuordnung mechanisch vor der Registrierung (1.7), nur C10; Endpower nach F-WEEK m = 3 und Doppelausweis m = 14 (Replikat-Quantile, Untergrenze); Doppelausweis A3-Praxis. |
| 2 | Entscheidungsrelevanz | PASS (nach F-WEEK): getrennte Tradability-Registrierung (Reversal = Liquiditaetsbereitstellung, Kosten D10-Spread 36 bp als Etikett). DROP eines getesteten Eintrags: fm8-Reversal-IC >= MDE80 der Variante auf Bybit-USDT-Perps 2024-07..2026-06 mit Power 0,80 je Fenster nicht vorhanden; beta-unabhaengig ~MDE80 / 0,754 (T: rev1 0,024; S: rev1 0,052); kein Urteil ueber kleinere Effekte, den rohen IC oder illiquide Teiluniversen. GL-012 vor der Registrierung: kein Verdikt. Oekonomisches Etikett (C.2): Portfolio 0,0101, Einzelposition 0,062 (DEC-74 (k), wie H-32). |
| 3 | Cluster-Einheit | Kalenderwoche; stationaerer Bootstrap Block 4; N = 52/50; Autokorrelation der Statistik in se_mean (v6b) enthalten, c = max(1, c_hat). |
| 4 | Selektions-Deflation | K = 3 (F-H33), z_max(3) = 0,853 < 1,6449; Decke ceiling_k3_neg < Schwelle (Decke/T <= 0,32), sonst GL-012; BH Nenner 3 (report-only); F-WEEK-BY bindend, m = getestete Eintraege, Doppelausweis 14; p = Max-p aus den transformierten Null-Replikaten. |
| 5 | Adversariales Fixture | Beta-Proxy-Charakteristik bei dominantem, autokorreliertem, driftendem Markt (rho 0,2, Drift +-0,002, beta 0,5..2,0) unter fm8: kein PASS in **negativer** Richtung; Bounce-Fixture fuer rev1/rev2/rev4 (Spread 36,21 bp): Mittel-IC ~1e-4, kein PASS; Survivorship-Fixture (drop): Reversal-Artefakt +0,47..+0,70 T_neg muss unter `close_at_last` verschwinden; Siegel-Leck und Panel-Schnitt: Abbruch. |
| 6 | Kostenmodell-Bindung | `constants_hash` n/a (kapitalfrei). |
| 7 | Irreversibilitaets-Probe | nachladbar (Harvest-Export; v6b-Pins). |
| 8 | Positivkontroll-Vorschaltung | ja, allein und vor dem Test, nur fuer zugeordnete Eintraege (Abschnitt 4). |
| 9 | Kapital/Steuer/Venue | n/a kapitalfrei; Delisting-Hazard (Etikett). |
| 10 | Stress-Episode | Abdeckungsnachweis aus v6b (Datumsfilter <= 2026-06-28): W1 rel 22 / abs 2 Tage, W2 8 / 1. Nie Filter. |
| 11 | Ergebnis-Artefakte (DEC-53) | Wochenserie je Eintrag und Fenster (CSV + sha256), Bootstrap-/Permutations-Fingerprints, `h33_run_fingerprint.json` (Seed, Bit-Generator, Code-Hash, Daten-Fingerprints, Panel-Schnitt, PK-sha256, Replikat-sha256 v7), Haupt-JSON + MD; fehlt etwas: KEIN VERDIKT. |
| 12 | Test-Pflichten | T0-T7, Abschnitt 5. |

---

### 4. Positivkontroll-Regel (woertlich, vorab fixiert; H-32 Erstfassung 4 + DEC-101 Teil 2 E8, negative Richtung, ohne Pilot)

> Die Positivkontrolle laeuft nur fuer Eintraege mit Zuordnung C10, allein und vor dem Test, mit der registrierten YAML
> (sha256-gesperrt), auf der realen Wochenform von W1 und W2 (Wochen, PIT-Masken, K_t, `returns_valid`; Panel <= 2026-06-28)
> und ausschliesslich synthetischen Renditen.
> **Welt je Fenster:** stress-Kalibrierung (rho_f, beta_sd, null_scales aus der YAML), Marktspalte = Faktor, Drift 0, plus
> 8 Sektorbloecke mit Schock sigma_g; sigma_g per Bisektion (Seeds 2000..2049) so, dass die Wochen-SD des fm8-IC des
> Eintrags in der Negativkontrolle sqrt(v_fm8_W + max(F2_null,W,v, F2_ref,v)) auf +-5 % trifft (F2_null = sd_week^2 - v_fm8;
> F2_ref = `dispersion_nuisance.f2_ref` - Lesart S: GL-035 F2_real; Lesart T: F2_ref := F2_null, dann sigma_g = 0).
> **Injektion:** PRD-Positiv-Fixture mit Vorzeichen s = -1: die Folgewochenrendite traegt -c z(Charakteristik_t)
> (z-Wert ueber die Mitglieder der Woche, beta-unabhaengig); c auf den Seeds 1000..1049 (gemeinsame Zufallszahlen positiv/
> negativ) so kalibriert, dass der **realisierte** Effekt in Richtung (Mittel positiv minus negativ von y = -fm8-Statistik)
> im bindenden Fenster das **Ziel F** auf +-5 % trifft:
> Ziel_W = max(z_krit SE_T,W + z_80 SD_T,W - min(0, m_df,W), q95_eff,W(k_ref,W) - m_df,W + z_80 SD_T,W),
> m_df,W = eingefrorenes Null-Mittel der driftfreien Zelle in negativer Richtung (< 0, also +|m_df|), q95_eff,W(k) =
> max(0, m_W) + k (q95_neg,W - m_W), k_ref,W wie Abschnitt 1.7, SE_T/SD_T wie die registrierte Power-Zeile; bindendes Fenster
> argmax_W.
> **Urteils-Seeds:** 53..252 (200), positiv und negativ; Gate-Kette = Bedingungen (1a)-(1c) und (4b) des Tests in
> Produktionskonfiguration: je Seed k = max(1, SD(IC_t) / sd_week), q95_eff, Bounce-Kill gegen das Mehrseed-Mittel.
> **BESTANDEN genau dann, wenn fuer jeden zugeordneten Eintrag:**
> (a) Wochen-SD des fm8-IC der Kontrollwelt <= 1,10 x SD der Power-Zeile in jedem Fenster (DEC-94 (5));
> (b) Anteil der Seeds mit PASS im bindenden Fenster >= 0,734;
> (c) falsche PASS-Quote der Negativkontrolle je Fenster <= 0,086;
> (d) realisierter Injektionseffekt auf den Urteils-Seeds innerhalb +-10 % des Ziels.
> rc 0 nur bei BESTANDEN, 3 bei NICHT BESTANDEN, 1 bei Abbruch. Nicht bestanden: kein Test, Ursachenanalyse, neue DEC.
> **Report-only:** PRD-/DEC-89-Sektorwelt (Schock 0,375 sigma_e), gemeinsame C10-Quote, unskalierte Kette.

Etikett: "Welt-SD an der GL-035-Streuung (DEC-94 (5) (i), kein Mittel; beschlossen nach Kenntnis von GL-035) - Richtung
Strenge" (Lesart S) bzw. "Ein-Faktor-Welt, Realismuspruefung leer - Richtung Testbarkeit" (Lesart T).

---

### 5. DEC-39-Trio und Test-Pflichten

| Stufe | Inhalt |
|---|---|
| T0 | Panel-Schnitt; Richtung aus der YAML (y = -IC); null_mean_neg/q95_neg/dev95 aus Rohreplikaten (Vorzeichen, -Q_0,05); bindende Zelle negativ; q95_eff bei m < 0 = k (q95 + |m|); Zuordnung (1.7) inkl. (1c) ueber den effektiven Prior; BY 0,10 / (m H_m) fuer m = 3, 14; Mehrseed-Bounce; Gate-Funktion |
| T1 positiv | stress-Welt der Fensterform mit realisiertem Reversal-Effekt = MDE80: PASS-Quote ~0,8; zugeordneter Eintrag besteht end-to-end |
| T1 null | signalfreie stress-Null (driftfrei und Drift): falsche PASS-Quote je Fenster <= alpha + MC-Toleranz in negativer Richtung |
| T1 adversarial | Beta-Proxy bei driftendem, persistentem Markt: kein PASS in negativer Richtung unter fm8; reiner Bid-Ask-Bounce (36 bp): kein PASS; Survivorship-drop-Panel: kein PASS unter `close_at_last`; Siegel-Leck (Outcome nach 2026-06-28) und ungeschnittenes Panel: Abbruch; YAML mit `pilot` != none oder Richtung positiv: Abbruch |
| T2 | Determinismus N >= 3 mit Fingerprint (v7, Zuordnung, PK, Test) |
| T3 | kein Checkpoint (Round-Trip ueber T7) |
| T4 | Zuordnungs- und Gate-Arithmetik auf konserviertem Payload (zweimal gleich); Monotonie: hoeherer Prior kippt nie von C10 zu GL-012, groessere SE nie von GL-012 zu C10; v7-Bruecke (draws_sha256 je Zelle = v6b) |
| T5 | Pins: z_krit, mde_faktor, alpha, Block, Replikate, Seed, w_judged 52/50, K 3, Richtung negativ, n_reps 10.000, Panel-Schnitt, frozen_neg in jedem Payload |
| T6 | Legacy-Import-Sperre |
| T7 | Artefakt-Round-Trip: Testserien plus Seed reproduzieren Gate-Schaetzer und p bitgleich; fehlt ein Artefakt: KEIN VERDIKT |

H-32-Regression: `tests/unit/test_h32*.py` unveraendert gruen; Vorlage aus v6b re-emittiert bitgleich.

---

### 6. Kill-Bedingungen (vorab) und Etiketten statt Kill

| Bedingung | Folge |
|---|---|
| Prior UNBELEGT / MDE80\* > Prior in einem Fenster (nicht C10) | GL-012 vor der Registrierung des Eintrags (kein Verdikt) |
| min K_t < 134 in W1/W2 (PRD 5.3 Kill (2)) | Abbruch (heute 343 / 501, nicht ausgeloest) |
| Panel nicht geschnitten / Datum nach dem Stichtag | Abbruch, KEIN VERDIKT |
| Zuordnung nicht bitgleich nachrechenbar, PK-Sperre, Pin, Fingerprint, Replikat-sha, Null-Nachrechnung ausserhalb +-10 %, Artefakt | KEIN VERDIKT (ganzer Lauf) |
| ceiling_k3_neg >= Schwelle | GL-012 des Eintrags vor dem Verdikt |
| Positivkontrolle NICHT BESTANDEN | kein Test, neue DEC |
| Bounce (alle drei Eintraege, Mehrseed-Mittel) | KEIN PASS |
| F-WEEK-BY lehnt nicht ab | DROP (Etikett), am Wellenschluss |

Etiketten statt Kill: Liquiditaet, Survivorship (synthetisch, mit H-33-Richtung), BH, Delisting = letzter Handelstag,
NO_HISTORY (Relisted-Symbole, DEC-100 N1 (2)), "fm8 entfernt nur das BTC-Beta", "fm8-Skala", DEC-102-E2-Etikett, C.17.

---

### 7. Etikett C.17 (Wortlaut-Vorschlag)

> "H-33 (fm8-Reversal, mom1/mom2/mom4 negativ, W1/W2): Fuer die fm8-Statistik wurde in W1/W2 keine reale IC gelesen.
> Gesehen: (a) **Pilot GL-035** 2022-04-18..2024-06-17 (anderes Fenster, gleiche Statistik, umgekehrte Richtung): x_P
> -0,038/-0,050/-0,045 (t -3,3/-4,1/-3,6), rev_gap +0,017 - Anlass der Richtungswahl (DEC-102 E2); SD_P/F2_real/k_pred als
> Streuungs-Nuisance (Lesart S). (b) **Persistenz-Null W1/W2** (v5d/v5e, Roh-IC, AR(1) je Symbol auf den Outcome-Renditen der
> Fenster): Null-Mittel der mom-Varianten in negativer Richtung +0,004..+0,047, q95 (positive Richtung) mom1 -0,0064 (W1) /
> -0,0362 (W2), Median phi 0,00, Q25 -0,04 / -0,09 - **richtungstragend mit H-33** (modellbasiert, Kendall-Anteil ~ -1/T).
> (c) v6b-Nuisance (Streuungen, Autokorrelation, Faktoranteil, K, Null-Mittel und -Quantile; mechanisches Momentum, gegen
> H-33). (d) WP-7 B3 Survivorship-Differenz roher 4-Wochen-Momentum-IC +0,0033 (gegen H-33). (e) synthetische Survivorship-
> und Bounce-Groessen. (f) Literaturband: klein/illiquide Reversal (Ficura -0,064 roh), breit ~0, gross/liquide Momentum,
> Momentum grosser Coins seit 2021 unprofitabel (Ficura, Stichprobe bis 2022-12). (g) WP-7-Spread-Zensus (Schnappschuss
> 2026-09, Zaehlungen und Median-Spreads). (h) A1-/H-27-/HF-RV-/A2-Groessen, DEC-100-Listen und Zaehlungen. Nie geoeffnet:
> Siegeldateien (L-IC v5c/v5d/v5e, WP-7-Rohserie), Pilot-Wochenreihen. Vorwissen der Agenten ueber 2024-2026: nicht
> quantifizierbar, nicht verwendet. W1/W2 sind fuer H-33 damit **nicht voll ergebnisblind** (b)."

---

### 8. Entscheidungsrelevanz und Nicht-Wiederholungs-Nachweis (C.1) - Wortlaut

> "H-33 ist eine **neue Hypothese** mit eigenem K = 3 (DEC-58 E2, DEC-102 E1). Sie wiederholt kein geurteiltes Experiment:
> (1) **H-29 (A3-R, rev_gap, Drittfassung F-XSEC1):** roher IC, Lag-2-Gap-Charakteristik, Schwelle 2,4865 SE; GL-032 GL-012
> vor dem Lauf; die Positivkontrolle bestand fuer rev_gap, eine reale IC wurde nie berechnet. H-33 nutzt fm8, Charakteristiken
> ohne Gap (mom1/mom2/mom4), P-1-Schwelle, skalierte Null, W2 bis 2026-06-28. (2) **H-32_rev_gap (GL-035):** GL-012 (Pilot),
> abgeschlossen; nach DEC-102 E4 nicht Teil von H-33. rev2 enthaelt die rev_gap-Woche t-1 (Korrelation der Charakteristiken
> ~0,7 unter iid); W1/W2 wurden fuer rev_gap nie gerechnet; der Pilotwert (+0,017) ist gesehen und etikettiert. (3)
> **H-32_mom1/mom2/mom4 (GL-035):** dieselbe Statistik mit positiver Richtung; nur der Pilot 2022-04..2024-06 wurde gerechnet
> (kein Test, kein Verdikt); W1/W2 sind fuer diese Statistik ungeoeffnet. H-33 kehrt die Richtung um - beschlossen nach
> Kenntnis des Pilot-Vorzeichens (DEC-102 E2, Testbarkeit); der Pilotabschnitt ist verbraucht und liefert keinen Prior. (4)
> **H-28_mom1 (Drittfassung):** roher IC, positive Richtung, GL-032, nie gelaufen. (5) **2.0-Kohorte (D.7, C-06/H-07/H-08):**
> Breite K_t >= 343 statt N = 5, Wochen- statt Stundenhorizont, Beta-Neutralisierung, survivorship-freies Union-Panel.
> PASS (nach F-WEEK) -> Tradability-Registrierung; DROP -> 'fm8-Reversal-IC >= MDE80 der Variante nicht vorhanden', kein
> Urteil ueber kleinere Effekte, den rohen IC oder illiquide Teiluniversen; GL-012 vor der Registrierung -> kein Verdikt."

---

### 9. Abweichungen von PRD / H-32 (registriert, etikettiert, mit Richtung)

1. Richtung negativ fuer mom1/mom2/mom4 (H-32: positiv) - neue Hypothese, Etikett DEC-102 E2 (Testbarkeit).
2. Kein Pilot, Prior aus der Literatur (DEC-102 E3) statt Pilot-Punkt (DEC-99 (6)); keine Uebergaberegel U - die Zuordnung
   erfolgt vor der Registrierung (P-1 (6), 1.7).
3. K = 3 statt 4 (rev_gap ausgeschlossen, DEC-102 E4); BH-Nenner 3; F-WEEK-Doppelausweis 14 statt 11.
4. Bindende Zelle in negativer Richtung = driftfrei (Regel DEC-99 N1 auf die negativen Null-Mittel); Replikate dieser Zelle
   aus Vorlauf v7 (Strenge) [EV-4]; bis dahin Form der Drift-Zelle (vorlaeufig, nur Power-Zeile).
5. (1c)-MDE80 mit rezentriertem Quantil q95_eff (DEC-101 E2) statt des Auftragswortlauts "q95_neg + z_80 se_mean" (Strenge).
6. Streuungs-Nuisance der Power-Zeile und der PK-Welt aus GL-035 (Lesart S, DEC-94 (5) (i); Strenge) [EV-3] - falls gewaehlt.
7. Bounce-Kill (4b) fuer alle drei Eintraege (H-32 nur rev_gap; Strenge) gegen das Mittel ueber 200 Seeds statt eines Seeds
   (Testbarkeit gegenueber dem Ein-Seed-Kill, dessen Zufallsrate an der Schwelle 2..6,5 % je Fenster betruege).
8. Nur C10, kein DEC-52-Zweig (Abweichung von P-1 (6) in Richtung Strenge) [EV-6].
9. Survivorship-Etikett fuer mom2/mom4 synthetisch neu gerechnet (Fixture reproduziert v6b mom1/rev_gap bitgleich).
10. Endpower nach F-WEEK als strenge Untergrenze (z_eff auch auf (1b)); Gate-Methode und Normalnaeherung report-only.
11. Ergebnisblindheit eingeschraenkt (C.17 (b)): W1/W2 fuer die Reversal-Richtung nicht voll blind (Testbarkeit) [EV-0].

---

### 10. Registry-YAML-Block (Entwurf, Template PRD 3.4)

```yaml
id: H-33
kohorte: A3 / F-H33
klasse: W
capital_free: true
hypothese: "Mindestens eine von mom1, mom2, mom4 in NEGATIVER Richtung (Kurzfrist-Reversal 1/2/4 Wochen): mittlerer woechentlicher Rank-IC der Charakteristik gegen das fm_neutral_8w-neutralisierte Folgewochen-Outcome in W1 UND W2 in Richtung >= z_krit * SE (P-1) und >= skaliertes 95-%-Null-Quantil; bestaetigt durch F-WEEK-BY; Prior aus der Literatur."
ertragsquelle: "Prognose (Kurzfrist-Reversal: Liquiditaetsbereitstellung / Ueberreaktion) - netto Markt-Beta"
metric: "Mittel des woechentlichen Spearman-IC (mom_n_t vs. fm8-Residuum der Folgewochen-Log-Rendite_t+1, close_at_last, min 10), y = -1 x Mittel; fm8-Skala (Daempfung ~25 %)"
richtung: {rev1: negativ, rev2: negativ, rev4: negativ}
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen_geurteilt: 52, rolle: urteilstragend, K_min_median_max: [343, 416.5, 500]}
  - {id: W2, von: 2025-07-01, bis: 2026-06-28, wochen_geurteilt: 50, rolle: urteilstragend, panel_schnitt: 2026-06-28, K_min_median_max: [501, 526, 545]}
pilot: "none (DEC-99 (5): Pilotabschnitt fuer fm8-korrelierte Statistiken verbraucht; DEC-102 E2/E5)"
fenster_regel: "C10_hart (nur C10, EV-6)"
threshold: {formel: "max(1.6449 * SE_W, q95_eff_W) mit q95_eff = max(0, m) + k * (q95_neg - m), k = max(1, SD(IC_t,W)/sd_week)", SE_W: "max(floor_fm8/sqrt(W), SD/sqrt(W), SE_stat stationaer Block 4)", ref: "ERSTFASSUNG_H33 1.8; DEC-101 E2; v7 frozen_neg"}
structural_null: {komponenten: [faktorerhaltende_null_stress_fm8_negativ, bindende_zelle_driftfrei, q95_neg_max_1000_10000, selektionsdecke_k3_vorzeichenbereinigt, bounce_alle_eintraege_mehrseed, null_scaling_im_testlauf], kill_check: "ceiling_k3_neg / T <= 0.32 (v6b-Drift-Zelle) -> kein Vor-Verdikt-Kill"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z_krit: 1.6449
  mde_faktor: 2.4865
  cluster_unit: kalenderwoche
  nuisance_lesart: "<T | S - Orchestrator, EV-3; empfohlen S>"
  detectable_effect_mde80_T: {W1: {rev1: 0.018385, rev2: 0.020169, rev4: 0.023633}, W2: {rev1: 0.016121, rev2: 0.017583, rev4: 0.020020}}
  detectable_effect_mde80_S: {W1: {rev1: 0.039529, rev2: 0.041804, rev4: 0.042878}, W2: {rev1: 0.038897, rev2: 0.041761, rev4: 0.043110}}
  a_priori_effekt: "UNBELEGT - Literatur-Lesart vom Nutzer (EV-1; Referenz R3 'breit, gleichgewichtet'); Gitter 0.010/0.015/0.020/0.025/0.033/0.048"
  zuordnungsregel: "power_p1.assign_regime mit (1c) ueber den effektiven Prior, nur C10; Doppelausweis assign_regime_a3_practice"
  end_power_f_week: "estimators.end_power_replicates, m = 3 (bindend), m = 14 (Doppelausweis)"
  ref: "state/herleitung_h33/power_h33.json"
selection: {K: 3, z_max: 0.853, ceiling: "ceiling_k3_neg (v7, driftfrei)", bh_denominator: 3, over_family: F-WEEK}
fdr: {p: "Max-p ueber W1/W2 aus 10.000 Replikaten der bindenden Zelle (v7), negative Richtung, transformiert d' = max(0, m) + k (d - m)", n_reps: 10000, family: "F-H33 BH 0.10 report-only, Nenner 3", over_family: "F-WEEK BY 0.10 bindend, m = getestete Eintraege (DEC-99 (7))", doppelausweis_m: 14}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, label: "Etikett C.2"}
decision_relevance: {on_pass: "Tradability-Registrierung nach F-WEEK", on_drop: "fm8-Reversal-IC >= MDE80 der Variante nicht vorhanden (beta-unabhaengig ~MDE80/0,754)", on_gl012: "kein Verdikt"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei"}
stress_episode: {rolle: abdeckungsnachweis, v6b: "W1 22/2, W2 8/1 Tage (Datumsfilter <= 2026-06-28)"}
irreversibility_probe: {ergebnis: nachladbar}
positive_control: {vorgeschaltet: true, regel: "ERSTFASSUNG_H33 4 (H-32 Erstfassung 4 + DEC-101 Teil 2 E8, negative Richtung, ohne Pilot)", seeds: "53..252"}
fixtures: {positive: "T1 positiv (realisierter Reversal-Effekt = MDE80)", null: "T1 null (stress, beide Zellen)", adversarial: "T1 Beta-Proxy, Bounce 36 bp, Survivorship-drop, Siegel-Leck, Panel-Schnitt"}
feasibility_verdict: "blockiert: Prior UNBELEGT (DEC-102 E3)"
constants_hash: "n/a - kapitalfrei"
data_fingerprints: ["union_range e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589", "delisting_register a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22", "delisted_tree 250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401", "delisting_dates c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3", "universe_excluded 50aaee3c1e63d560b69a7aa42748abdea0e0cf742f6ff3f618e6f00c54083098", "prelaunch_v6b_json f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c", "replicates_v6b 3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef", "prelaunch_v7 <sha256>", "replicates_v7 <sha256>", "spread_census fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083", "as_of 2026-09-28", "panel_cut_test 2026-06-28"]
etiketten: ["DEC-102 E2 (nach Kenntnis von GL-035, Testbarkeit)", "C.17 (Abschnitt 7; W1/W2 nicht voll blind)", "fm8-Skala (Daempfung ~25 %)", "Prior-Lesart <R..> (Nutzerentscheid)", "Streuungs-Nuisance <T|S>", "nur C10 (Strenge)"]
```

---

### 11. Registrierungsdatei (Schema-Entwurf `state/registered/h33_v1.yaml`)

```yaml
hypothesis: H-33
code_commit_prelaunch: <v7-Commit>
code_commit_registration: <Registrierungs-Commit>
hypotheses:
  H-33_rev1: {hypothesis: H-33, variant: mom1, direction: negative}
  H-33_rev2: {hypothesis: H-33, variant: mom2, direction: negative}
  H-33_rev4: {hypothesis: H-33, variant: mom4, direction: negative}
primary_statistic: fm_neutral_8w
universe: {rule: linear_usdt_perpetual, excluded_at_prelaunch: {usdc_perp: 68, dated_future: 48, other: 0}}
alpha: 0.05
z_krit: 1.6448536
mde_faktor: 2.4865
seal: {panel_cut_test: '2026-06-28', stress_list_date_filter: true}
pilot: {mode: none, reason: "DEC-99 (5): Pilotabschnitt 2022-04-18..2024-06-24 fuer fm8-korrelierte Statistiken verbraucht; DEC-102 E2/E5"}
prior:
  source: literature
  value: {mom1: <pi>, mom2: <pi>, mom4: <pi>}          # Nutzerentscheid; UNBELEGT blockiert
  reading: <R1_A_stern | R3_breit | ...>
  band: {R1_A_stern: {mom1: 0.0484, mom2: 0.0415, mom4: 0.0390}, R3_breit_oben: {mom1: 0.0144, mom2: 0.0027, mom4: 0.0091}, R4_gross_liquide: {mom1: -0.0248, mom2: -0.0262, mom4: -0.0153}}
  scale: fm8
  fm8_damping: 0.75423
  label: "Literatur-Prior (DEC-102 E3); Richtungswahl nach Kenntnis von GL-035 (DEC-102 E2)"
  ref: state/herleitung_h33/power_h33.json#umrechnung
dispersion_nuisance:                                   # EV-3
  reading: <T | S>
  f2_ref: {mom1: 0.010331, mom2: 0.012016, mom4: 0.013072}   # S: GL-035 F2_real; T: F2_null je Fenster
  c_ref: {mom1: 1.0, mom2: 1.0, mom4: 1.0}
  label: "Streuungs-Nuisance aus GL-035 (DEC-94 (5) (i)), kein Mittel; beschlossen nach Kenntnis von GL-035"
assignment:                                            # vor der Registrierung, mechanisch, P0'
  rule: "power_p1.assign_regime(priors=[pi - (max(T_1b,T_1c) - z_krit*SE_T)], ses=SE_T, sds=SD_T); nur C10, sonst GL-012"
  entries: {H-33_rev1: <C10|GL012>, H-33_rev2: <C10|GL012>, H-33_rev4: <C10|GL012>}
  window_power: {...}
  double_statement: power_p1.assign_regime_a3_practice
  on_gl012: {status: gl012_pre_registration, p_value: 1.0, in_f_week_m: false}
fdr:
  p_source: factor_preserving_null_replicates
  p_formula: "p = (1 + #{d' >= y}) / (1 + R), d' = max(0, m) + k (d_neg - m), d_neg = -raw replicate window mean of the binding cell (negative direction), k = max(1, SD(IC_t,W)/sd_week_W,v), m = frozen null_mean_neg"
  n_reps: 10000
  replicates_sha256: <v7>
  replicates_cell: "per window and variant the drift cell with the larger null mean in the NEGATIVE direction (driftfree)"
  combine: max_p
  report_only: [block_permutation_fm8_window_mean, normal_approximation, unscaled_null]
  family: {name: F-H33, method: BH, alpha: 0.10, denominator: 3, report_only: true}
  over_family: {name: F-WEEK, method: BY, alpha: 0.10, binding: true, m_rule: "DEC-99 (7)", double_statement_m: 14}
null_scaling: {enabled: true, rule: "k = max(1, SD(IC_t,W)/sd_week_W,v); q95_eff = max(0,m) + k*(q95_neg - m); p from max(0,m) + k*(d_neg - m)", direction: strictness, ref: DEC-101 E2}
selection: {K: 3, ceiling: ceiling_k3_neg}
fweek_counting: {in_m: tested_only, method: BY, alpha: 0.10, double_statement_m: 14}
windows:
  W1:
    start: '2024-07-01'
    end: '2025-06-30'
    w_judged: 52
    calibration: <unveraendert aus h32_v1.yaml windows.W1.calibration>
    null_scales: {sigma_e_used: 0.12323095978582714, sigma_f: 0.06685192489159383}
    frozen_neg:
      se_mean: {mom1: 0.007302437893063986, mom2: 0.008089705275703178, mom4: 0.009768035341097337}
      e_se_rule: {mom1: 0.007441102766442681, mom2: 0.008122760986094501, mom4: 0.00936994244458985}
      sd_week: {mom1: 0.05127914041549264, mom2: 0.056865519514139776, mom4: 0.0659948199928681}
      null_mean_neg: {mom1: -0.0012207223210487662, mom2: -0.0015826633666051091, mom4: -0.0019339056030023211}
      null_mean_neg_driftfree: {...}
      null_mean_neg_drifting: {mom1: -0.0012901650979848683, mom2: -0.0016790699412476185, mom4: -0.00206577452448383}
      binding_cell_neg: {mom1: driftfree, mom2: driftfree, mom4: driftfree}
      q95_neg: <v7>
      q95_neg_1000: <v7>
      q95_neg_10000: <v7>
      q95_neg_driftfree: <v7>
      q95_neg_drifting: <v7; v6b-Wert 1.000 / 10.000 als Bruecke>
      ceiling_k3_neg: <v7, driftfrei>
      floor_fm8: 0.04882131048278087
      v_fm8: 0.002391017809866642
      k_fm8_series_sha256: f35fb20b65144169a53a7e9d1784fa88d7f7acfe75b0406b359bb57b3e1f9cc1
    bounce_sigma_true: 0.17354241498115813
    survivorship_neg_t_units: {mom1: 0.4699, mom2: 0.5900, mom4: 0.4883}
  W2:
    start: '2025-07-01'
    end: '2026-06-28'
    w_judged: 50
    calibration: <unveraendert aus h32_v1.yaml windows.W2.calibration>
    null_scales: {sigma_e_used: 0.10904950559211316, sigma_f: 0.054611863018019804}
    frozen_neg: {... wie W1; floor_fm8 0.043638979223103405, v_fm8 0.0019045663339909372, k_fm8_series_sha256 6b69b6f7bbd0505510f37c9cd853bbf19339f5aa36294978aaedcb1e5f574795}
    bounce_sigma_true: 0.1342852104278142
    survivorship_neg_t_units: {mom1: 0.5838, mom2: 0.7033, mom4: 0.6384}
beta_control: {method: fm_neutral_8w, beta_window_weeks: 8}
rules: {seed: 53, n_reps: 1000, mean_block: 4, n_boot: 1000, null_level: 0.95, bounce_spread: 0.003621, bounce_seeds: [53, 252]}
positive_control:
  seeds: [53, 252]
  calibration_seeds_injection: [1000, 1049]
  calibration_seeds_world: [2000, 2049]
  world_sd_target: "sqrt(v_fm8_W + max(F2_null_W, f2_ref))"
  inject_sign: -1
  inject_target: "Ziel_W = max(z_krit SE_T + z_80 SD_T - min(0, m_df), q95_eff(k_ref) - m_df + z_80 SD_T), argmax_W"
  null_scaling: {enabled: true, rule: "wie Testlauf (DEC-101 E2); k je Seed"}
  criteria: {sd_ratio_max: 1.10, pass_share_min: 0.734, neg_pass_max: 0.086, injection_tolerance: 0.10}
  scope: assigned_entries_only
runner: {as_of: '2026-09-28', start_year: 2021, end_year: 2026, allow_partial: true}
data_fingerprints:
  union_range_fingerprint: e503bedb388cf8aaa9f3f28735cc4d83a659528447d95d027476027a4cb0c589
  delisting_dates_sha256: c1306c561246a684a29b166bc0a8663f2345a0a21e5798ea7e2a7a823bbaf1f3
  delisting_register_sha256: a28c7eb73c586895f710511a73ca58d33570c283397ff356a5dff46c4d639b22
  delisted_tree_sha256: 250a923b5c04f18025f9a7ffc72dbbd3b08b75e44bbcd38876b8effa6427e401
  prelaunch_v6b_sha256: f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c
  replicates_v6b_sha256: 3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef
labels: ["DEC-102 E2", "C.17 W1/W2 nicht voll blind (Persistenz-Null)", "fm8-Skala", "nur C10 (Strenge)"]
```

---

### 12. Bauliste (Abnahme durch den Orchestrator; additiv, H-32-Verhalten bitgleich)

0. **Konfiguration je Hypothese** (DEC-102 E5): Konstanten-Satz H-33 additiv neben H-32 (`HYPOTHESIS` H-33, `ENTRY`
   H-33_rev1/rev2/rev4, `DIRECTION` negativ, `VARIANTS` (mom1, mom2, mom4), K 3, BH-Nenner 3, F-WEEK-Doppelausweis 14);
   Richtung aus `hypotheses.*.direction` der YAML, gegen den Konstanten-Satz gepinnt (T5). Funktionen erhalten die
   Konfiguration als Parameter mit H-32-Default; H-32: `test_h32*.py` unveraendert gruen, Vorlage aus v6b bitgleich.
1. **Vorlauf v7** (`--prelaunch --hypothesis H-33`, nur W1/W2): Kalibrierung aus `h32_v1.yaml` lesen und nachrechnen (muss
   gleich sein), beide Zellen mit 10.000 Replikaten und `keep_draws` fuer **beide** Zellen; Bruecke: `draws_sha256` der ersten
   1.000 Rohreplikate je Zelle/Variante = v6b-Zellen, Drift-Zelle 10.000 = v6b-p-Datei; Umrechnung in die negative Richtung
   (null_mean_neg, bindende Zelle, q95_neg nach DEC-101 E5, ceiling_k3_neg); Survivorship mom1/mom2/mom4; Mehrseed-Bounce;
   p-Datei v7 (bindende Zelle negativ); Vorlage `h33_v1_TEMPLATE.yaml`. Zweimal bitgleich (result_sha256). Dauer: hoechstens
   die v6b-Dauer 1 h 41 min (P/W1/W2 inkl. Kalibrierungssuche, REGISTRIERUNG_H32 V4); v7 ohne P und ohne Suche.
2. **Zuordnung ohne Pilot** (`assignment.py`, rein): Prior, `dispersion_nuisance`, eingefrorene Konstanten -> Regime je
   Eintrag (Abschnitt 1.7), Fensterpowers, A3-Doppelausweis, Endpower m 3/14; nur C10; T0/T4.
3. **Testlauf `--run`** mit `prior.source: literature`: Startsperre, Zuordnungs-Sperre (P0'), PK-Sperre (P0''), Panel-Schnitt,
   nur C10-Eintraege, Gate mit Richtung aus der YAML, Bounce-Kill fuer alle Eintraege (Mehrseed), p aus v7, F-WEEK (m
   getestet, Doppelausweis 14); kein Pilot-Eingang (`--pilot-result` wird abgelehnt).
4. **Positivkontrolle** ohne Pilot: Welt-SD-Ziel aus `dispersion_nuisance`, Injektion mit Vorzeichen -1, Ziel F, Gate-Kette
   in Produktionskonfiguration, Kriterien (a)-(d) unveraendert, nur zugeordnete Eintraege.
5. **Schema** `validate_registered` fuer H-33: `pilot.mode: none` nur mit `prior.source: literature`; Richtung negativ; K 3;
   `frozen_neg`-Schluessel; `assignment`; `dispersion_nuisance`.
6. **Tests** Abschnitt 5 (T0-T7), Gesamtzahl steigt, keiner wird reduziert; Siegelmuster nur als Abweisungskonstanten.
7. **PP3-Trockenprobe** fuer W1/W2 (K-Reihen gegen die Pins, keine IC).

---

### 13. Ablauf und Rueckbauweg

Nutzerentscheid Prior-Lesart (+ EV-0) -> [Referenz R3: alle drei GL-012 vor der Registrierung, kein Bau, kein v7, W1/W2
bleiben fuer fm8-Reversal ungeoeffnet] / [Lesart mit C10-Eintrag: EV-Festlegung -> Bau -> Abnahme -> v7 x2 -> PP3 -> YAML +
sha256 -> Review -> Registrierung (DEC-103) -> Positivkontrolle allein -> Test W1/W2 -> Gate-Check nur gegen diesen Text ->
GL-Eintrag -> F-WEEK am Wellenschluss]. Rueckbauweg: Entwurf ohne Rechtswirkung; Registry append-only.
