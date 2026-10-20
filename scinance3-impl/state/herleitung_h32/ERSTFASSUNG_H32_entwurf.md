## H-32 - Erstfassung (ENTWURF 2026-10-20): A3-fm8, beta-neutraler Wochen-Querschnitts-IC im Zweistufen-Design (Pilot 2022-04..2024-06, Test W1/W2), Klasse W, kapitalfrei

> **NICHT REGISTRIERT.** Entwurf der Herleitung; registrieren darf nur der Orchestrator. Zahlen mit Fundstelle;
> `[pj <pfad>]` = `state/herleitung_h32/power_h32.json` (sha256 `df17cafa337bc548c01f08bb85bf2845cc87e203e39541d45804049b94d51bf3`),
> `[v5e <pfad>]` = `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json` (sha256 `94d65559...5ae3b2`), `[wp7k]` =
> `state/runs/wp7_20260921/decile_degeneration_weekly.csv` (nur `week`, `n_symbols`), `[EV-n]` = Entscheidungsvorlage
> in `ENTSCHEIDUNGSVORLAGEN.md` (dort Richtung jeder Gabelung). Alle Werte mit "v6" werden vom Vorlauf v6 eingefroren
> und ersetzen die v5e-Vorabzahlen; keine v6-Zahl darf eine Realisierung aus Pilot, W1 oder W2 enthalten.
> Ergebnisblind: keine reale IC, kein Outcome; Siegeldateien nie geoeffnet.

### 0. Vorbedingungen der Registrierung (ohne sie ist der Eintrag nicht lauffaehig)

| # | Vorbedingung | Stand |
|---|---|---|
| V1 | **DEC-99** (REZENZ 3.0, Pilot-Schaetzfenster zulaessig) beschlossen nach Nutzer-Zustimmung | offen, Wortlaut EV-1 |
| V2 | Orchestrator-Entscheidungen EV-2..EV-8 | offen |
| V3 | Bau B-1..B-6 (Bauliste Abschnitt 12), Abnahme durch den Orchestrator (Tests nie reduziert) | offen |
| V4 | Vorlauf v6 (outcome-frei) mit eingefrorenen Konstanten je Fenster und K_fm8-Reihen | offen |
| V5 | finale Registrierungsdatei `state/registered/h32_v1.yaml` + sha256, Code-Commit und code_sha256 | offen |
| V6 | adversarisches Review (zweiter Reviewer) ohne offenes VETO | offen |
| V7 | Daten: derselbe Harvest-Export wie v5e (`scinance_panel_1d_2026-09-28.zip`, sha256 `03dc0e7c...6b16cb`), Fingerprints union_range `a7e4dec7...793a`, delisting_dates `852bf753...2933` | vorhanden |
| V8 | Blind-Siegel DEC-96 E3 gewahrt: keine Rechnung auf Tagen ab 2026-07-01 | Waechter im Code (B-2, B-3) |

---

### 1. Festlegungen (bindend fuer alle Eintraege)

#### 1.1 Klasse, Familie, Varianten

- Klasse W, kapitalfrei. Familie **F-H32**, **K = 4** Varianten, je ein Eintrag:
  `H-32_mom1` (positiv), `H-32_mom2` (positiv), `H-32_mom4` (positiv), `H-32_rev_gap` (negativ, Lag-2-Gap).
- Hypothesen-PASS, wenn mindestens ein Eintrag PASS ist; jeder Eintrag wird einzeln berichtet.
- **K = 4 bleibt Nenner** (vorzeichenbereinigte Selektionsdecke, BH-Nenner 4); Eintraege ohne Uebergabe gehen mit
  p = 1 ein. Ueber-Familie **F-WEEK** (Benjamini-Yekutieli am Wellenschluss, bindend) enthaelt F-XSEC1 (7 Eintraege,
  alle p = 1, GL-032) und F-H32 (4) [EV-3].
- Nicht aufgenommen: H-30-Varianten (vol_beta strukturell unter fm8, C.4; vol_rv/vol_max Drag-Feasibility 2,764 > 0,5,
  durch fm8 nicht behoben) [EV-3]; keine Universums-Variante (U0) [EV-4]; keine Zwei-Richtungen-Variante.

#### 1.2 Panel, Universum, Datenbezug

Wie Drittfassung H-28..H-30 (Registry-Abschnitt "Panel und Universum"): Union `panel_1d` + `panel_1d_delisted`,
PIT-Maske DEC-72, Delisting-Datum = Announcement-Datum (Etikett), `--allow-partial` (DEC-66), Bezug nur ueber exakte
Schluessel des Harvest-Exports, Pruefung von Groesse und sha256, Entpacken in ein frisches Sitzungsverzeichnis (nie ins
Repo, nie unter `data/harvest`), Zugangsdaten nur aus `HARVEST_S3_*`. Daten-Fingerprints V7, Abweichung = KEIN VERDIKT.

#### 1.3 Fenster

| Fenster | Kalender (Slice) | Formationswochen (geurteilt) | Outcome-Wochen | W | K_t min/Median/max | Rolle |
|---|---|---|---|---:|---|---|
| **P** | 2022-04-18..2024-06-30 | 2022-04-18..2024-06-17 | 2022-04-25..2024-06-24 (Ende 2024-06-30) | 114 | 120/202/339 | **Pilot, nicht urteilstragend**, nach der Uebergabe verbraucht |
| **W1** | 2024-07-01..2025-06-30 | 2024-07-01..2025-06-23 | 2024-07-08..2025-06-30 (Ende 2025-07-06) | 52 | 345/419/514 | urteilstragend |
| **W2** | 2025-07-01..2026-06-28 | 2025-07-07..2026-06-15 | 2025-07-14..2026-06-22 (Ende 2026-06-28) | 50 | 514/589/603 (v6: geschnitten) | urteilstragend, juengstes Fenster (DEC-99 (1)) |
| L | 2021-03-01..2024-06-30 | - | - | - | versiegelt | Aera-Profil der Drittfassung, bleibt versiegelt; H-32 oeffnet die Siegeldatei nie |

- P: erste Woche mit K_t >= 117 (K_min, PRD 4.1) `[wp7k]`; identisch mit der A1-Nuisance-Basis. Davor < 117 (2022-04-04: 111).
- P endet vor dem ersten Kalendertag von W1; keine Kalenderwoche ist zugleich Pilot-Outcome und W1-Woche [EV-2b].
  Der Rueckblick der W1-Charakteristiken (mom2/mom4, rev_gap-Gap) und der 8-Wochen-Betas in die Pilotperiode ist
  Formation, kein Outcome des Tests, und zulaessig (DEC-75 (8)).
- W2 endet mit der Outcome-Woche 2026-06-22..28 (Blind-Siegel DEC-96 E3) [EV-2c]; registrierte Abweichung von der
  Drittfassung (dort Outcome-Woche bis 2026-07-05).
- Die Charakteristiken und Betas werden auf dem vollen Panel gebaut und danach geschnitten (DEC-75 (8)); Formationsdaten
  vor Fensterbeginn sind zulaessig, Outcomes nur innerhalb des Fensters.

#### 1.4 Cluster-Einheit, Metrik, Konvention

- Cluster = Kalenderwoche (ISO). Je Woche ein Spearman-Rank-IC ueber die lebenden Symbole mit gueltigem PIT-Beta;
  Wochen mit < 10 gueltigen Symbolen fallen aus.
- **Primaerstatistik je Variante und Fenster:** Mittel der Wochen-ICs der Charakteristik (Woche t) gegen das
  **fm_neutral_8w-neutralisierte** Folgewochen-Outcome (t+1) - exakt `ic.apply_beta_control("fm_neutral_8w", ...)` und
  `ic.weekly_ic_series(..., convention="close_at_last")`, d. h. die IC_res der Drittfassung.
- Survivorship-Konvention `close_at_last` (urteilstragend); `drop` nur Sensitivitaet.
- In Richtung: y = s x Statistik, s = +1 (mom1, mom2, mom4), s = -1 (rev_gap).

#### 1.5 Charakteristiken (je Woche t, PIT; wie Drittfassung)

mom1/mom2/mom4: Summe der Wochen-Log-Renditen t-n+1..t, n = 1/2/4. rev_gap: Wochen-Log-Rendite der Woche t-1, Woche t
ist das Gap. Code `characteristics.momentum_characteristic`, `characteristics.reversal_gap_characteristic`.

#### 1.6 Beta-Kontrolle und Null

- `fm_neutral_8w`: je Outcome-Woche t+1 Querschnitts-OLS des Outcomes auf das PIT-Beta zu BTCUSDT (t-7..t aus
  `returns_est`, 8 gueltige Wochen noetig), Residuum ersetzt das Outcome (DEC-86).
- Null: faktorerhaltende Null der Drittfassung (DEC-85/87), Kalibrierung je Fenster aus der Akte (W1/W2 v5e: measured und
  stress; Marktspalte = Faktor; beta_sd kalibriert), **stress bindend**. Neu in v6: 8 Beta-Vorlaufwochen (reale Masken),
  K = 4, Fenstermittel ueber 52/50 Wochen, 1.000 Replikate, Seed 53, driftfrei und Drift 0,002/Woche.
- Eingefroren je Fenster W und Variante v (v6): `sd_week` (SD des Wochen-IC), `se_mean` (SD des Fenstermittels),
  `null_mean` (in Richtung, extremeres aus driftfrei/Drift), `q95` (95-%-Quantil des Fenstermittels in Richtung,
  extremeres aus driftfrei/Drift), `ceiling_k4` (Mittel des Maximums der vorzeichenbereinigten Fenstermittel ueber die
  4 Varianten, stress, driftfrei), `k_fm8_series` und `floor_fm8` = mean_t 1/sqrt(K_fm8,t - 1), `v_fm8` = mean_t
  1/(K_fm8,t - 1).
- Vorabwerte bis v6 (v5e, 45/44 Simulationswochen, konservativ) [EV-5]: se_mean W1 mom1/mom2/mom4/rev_gap
  0,00794/0,00896/0,01078/0,00785; W2 (geschnitten, x sqrt(51/50)) 0,00643/0,00714/0,00847/0,00671; null_mean W1
  +0,00087/+0,00142/+0,00185/-0,00114, W2 +0,00054/+0,00068/+0,00099/-0,00046 `[pj power.nuisance]`.

#### 1.7 Stufe P - Pilot (Schaetzung, nicht urteilstragend)

Je Variante v, nur Formationswochen 2022-04-18..2024-06-17:
- x_P = Mittel der fm8-Wochen-ICs in Richtung; SD_P = Stichproben-SD (ddof 1) der Wochen-ICs; W_P = Zahl der endlichen
  Wochen (Soll 114).
- SE_P = max(B_P / sqrt(W_P), SD_P / sqrt(W_P), SE_stat), B_P = mean_t 1/sqrt(k_t - 1) mit k_t = Symbole im fm8-IC der
  Woche, SE_stat = SD der Mittel des stationaeren Bootstraps (Politis/Romano, mittlere Blocklaenge 4, 1.000 Replikate,
  Seed 53; `power_p1.stationary_bootstrap_se`) - P-1 (4).
- t_P = x_P / SE_P; 80-%-Band x_P +- 1,2816 x SE_P (normal, zweiseitig); Bericht: Perzentil-Band des Bootstraps.
- Streuungs-Nuisance fuer die Test-SE (DEC-94 (5) (i)): F2_real = max(0, SD_P^2 - mean_t 1/(k_t - 1)),
  c_real = max(1, W_P x SE_stat^2 / SD_P^2).
- Vorhersage (keine Bindung): SE_P mom1 0,0071, mom2 0,0075, mom4 0,0085, rev_gap 0,0070 `[pj power.pilot_precision]`.
- Nicht gerechnet: roher IC, Lag-Profil, Beta-Kalibrierungs-IC, irgendein Outcome ausserhalb von P.

#### 1.8 Uebergaberegel U (woertlich; vorab fixiert, mechanisch, nicht nach dem Sehen waehlbar)

> Fuer jede Variante v werden aus dem Pilot-Ergebnis berechnet:
> SE_T,W = max(se_mean_W,v (v6, eingefroren), sqrt(c_real) x sqrt(v_fm8_W + F2_real) / sqrt(w_judged_W)) fuer W in {W1, W2};
> m = max(null_mean_W1,v, null_mean_W2,v) (v6, in Richtung);
> MDE80*_v = 2,4865 x max(SE_T,W1, SE_T,W2).
> Die Variante wird **uebergeben**, genau wenn
> (i) x_P > 0 (Vorzeichen in registrierter Richtung) UND
> (ii) x_P - max(0, m) >= MDE80*_v UND
> (iii) t_P >= 2,0.
> Prior der Zuordnung: **pi_v = x_P** (Lesart A; Alternative B "x_P - 1,2816 x SE_P" ist nicht registriert) [EV-6].
> Regime: `power_p1.assign_regime([pi_v - max(0, null_mean_W1,v), pi_v - max(0, null_mean_W2,v)], [SE_T,W1, SE_T,W2])`;
> unter (ii) ist es stets C10. Doppelausweis: `power_p1.assign_regime_a3_practice` mit denselben Eingaben; ist dort
> GL012, traegt der Eintrag "zugelassen nur durch DEC-94 (Lockerung)".
> Nicht uebergebene Varianten: Status **GL-012 (Pilot)** mit gemessenem Grund (verfehlte Bedingung, x_P, SE_P, t_P,
> MDE80*_v); p = 1 im BH-Nenner 4; kein Test, kein Verdikt.
> Das Pilot-Ergebnis (`h32_pilot.json`, result_sha256) und die Uebergabe werden vom Orchestrator festgehalten (DEC- oder
> GL-Vermerk), bevor ein Testfenster gerechnet wird. Das Pilotfenster ist danach verbraucht.

Vorabwerte von MDE80*_v (v5e, nur Null-Quelle; der Pilot kann sie nur erhoehen): mom1 0,0206, mom2 0,0237, mom4 0,0287,
rev_gap 0,0195 (auf x_P, inklusive Gutschrift) `[pj power.handover_oc.<v>.A_punkt.pilot_threshold_on_point]`.

#### 1.9 Stufe T - Test (nur uebergebene Varianten)

- y_W = Primaerstatistik in Richtung, W in {W1, W2}.
- SE_W (Lauf) = max(floor_fm8,W / sqrt(w_judged_W), SD(IC_t,W) / sqrt(w_judged_W), SE_stat,W), SE_stat aus dem
  stationaeren Bootstrap der Wochenserie (Block 4, 1.000, Seed 53) - P-1 (4).
- Schwelle je Fenster: T_W = max(z_krit x SE_W, q95_W,v), z_krit = 1,6449 (alpha 0,05 einseitig, DEC-51 (1),
  DEC-94 (1)).
- Power-Zeile (P-1 (3), vor dem Test festgestellt): Fenster-Power P_W = Phi((pi_v - max(0, null_mean_W,v)) / SE_T,W - 1,6449);
  MDE80_W = 2,4865 x SE_T,W + max(0, null_mean_W,v).
- Vorab (v5e, S1) MDE80 W1 / W2: mom1 0,0206 / 0,0165, mom2 0,0237 / 0,0184, mom4 0,0287 / 0,0221, rev_gap
  0,0195 / 0,0167; A3-Praxis W1: 0,0273 / 0,0312 / 0,0377 / 0,0261 `[pj power.power_table]`.

#### 1.10 Selektion

- DEC-94 (7): z = max(1,6449, z_max(4) = 1,052) = 1,6449 `[pj power.selection]`.
- Vor-Verdikt-Kill: ceiling_k4_W >= T_W,eingefroren (= z_krit x se_mean_W,v + max(0, null_mean_W,v)) in einem Fenster ->
  GL-012 des Eintrags. Vorab grob: Decke / Schwelle 0,64..0,67 `[pj power.ceiling_check]` - kein Kill erwartet.

---

### 2. Gate-Text (woertlich, Fassung fuer den Bau)

**Pilot-Modus (`--pilot`) - Abbrueche vor jeder Ausgabe (rc 1, KEINE UEBERGABE fuer keine Variante):**
- (PP0) Startsperre: sha256 der `--registered`-Datei = `--registered-sha256`.
- (PP1) Schema: `pilot_window`, `handover_rule`, `alpha` = 0,05, `z_krit` = 1,6449, `mde_faktor` = 2,4865, `primary_statistic`
  = `fm_neutral_8w`, je Fenster die v6-Konstanten aller 4 Varianten; fehlend oder ungueltig = Abbruch.
- (PP2) Daten-Fingerprints = YAML.
- (PP3) T5-Pins: `pilot_window.w_pilot` = W_P des geladenen Fensters (114), `rules.mean_block` = 4, `rules.n_boot` >= 1.000,
  `rules.seed` = 53.
- (PP4) **Siegel-Waechter:** keine Outcome-Woche ausserhalb 2022-04-25..2024-06-24 (letzter Kalendertag 2024-06-30) wird
  einer Charakteristik gegenuebergestellt (monkeypatch-Test auf `ic.weekly_ic_series`); kein roher IC, kein Lag-Profil.
- (PP5) DEC-53-Artefakte (Wochenserie je Variante CSV + sha256, Bootstrap-Fingerprint) vor der Uebergabe geschrieben und per
  Round-Trip verifiziert.
- Ausgabe je Variante: x_P, SE_P, SD_P, W_P, t_P, 80-%-Band, F2_real, c_real, SE_T,W, MDE80*_v, Bedingungen (i)-(iii),
  Uebergabe ja/nein, pi_v, Regime P-1 und A3-Praxis, Etikett.

**Test-Modus (`--run`) - Abbrueche vor jedem Verdikt (rc 1, KEIN VERDIKT):**
- (P0) Startsperre YAML; (P0') **Pilot-Sperre:** `--pilot-result` mit sha256 = `--pilot-result-sha256`; die Uebergabe wird
  aus diesem JSON mit Regel U deterministisch nachgerechnet und muss bitgleich sein; abweichend = Abbruch.
- (P1) Schema wie PP1; (P2) `beta_control` = fm_neutral_8w / 8; (P3) Daten-Fingerprints; (P4) T5-Pins (`w_judged` 52/50,
  Block, Replikate, Seed, z_krit); (P5) `returns_valid` vorhanden.
- (P6) Null-Nachrechnung je Fenster (v6-Konfiguration): se_mean, null_mean, q95, ceiling_k4 je innerhalb +-10 % der
  eingefrorenen Werte (bei eingefrorenem Wert ~0: absolut 1e-4); geurteilt wird gegen die eingefrorenen Werte.
- (P7) **Siegel-Waechter:** keine Outcome-Woche nach 2026-06-22 (letzter Kalendertag 2026-06-28); kein roher IC, kein
  Lag-Profil, kein Beta-Kalibrierungs-IC.
- (P8) DEC-53-Artefakte vor jedem Verdikt geschrieben und verifiziert.

**Nicht uebergebene Eintraege:** nicht gerechnet; Verdikt "GL-012 (Pilot): <gemessener Grund>", p = 1.

**Uebergebene Eintraege - Vor-Verdikt-Kill:** ceiling_k4_W >= T_W,eingefroren in einem Fenster -> DROP mit Etikett GL-012.

**PASS genau dann, wenn in W1 UND W2 (C.10 hart) gilt:**
- (1a) y_W > 0 (NaN verfehlt);
- (1b) y_W >= 1,6449 x SE_W (SE_W nach 1.9; NaN oder 0 verfehlt);
- (1c) y_W >= q95_W,v (eingefroren);
- und nur fuer `H-32_rev_gap`: (4b) kein Bounce-Kill - |IC_bounce,W| >= |Statistik_W| in einem Fenster -> KEIN PASS,
  Etikett "Artefakt Bounce" (Fixture wie Drittfassung: `rules.bounce_spread` 0,003621, `windows.<W>.bounce_sigma_true`
  W1 0,17186 / W2 0,13311, Seed 53).

Sonst DROP mit Etikett der verfehlten Bedingung. Ein DEC-52-Zweig existiert nicht (Regel U laesst nur C10 zu).

**Etiketten (report-only, nie Gate-Eingang):** Liquiditaet (Mittel-IC ohne Bucket 1 des trailing-8-Wochen-Median-
Turnovers und auf Buckets 3..10; "Illiquiditaets-Artefakt", wenn ohne Bucket 1 nicht jenseits 0,5 x T_W in Richtung);
Survivorship (synthetisch, v5e: mom1 -0,198/-0,438, rev_gap -0,189/-0,579 IC_min-Einheiten); Block-Permutations-p
(Block 4, 1.000, Seed 53, Max-p); BH alpha 0,10 ueber Nenner 4; "zugelassen nur durch DEC-94" (Doppelausweis);
"zugelassen nur durch DEC-99 (Pilot-Prior)" an jedem Eintrag; "vorlaeufig bis F-WEEK geschlossen" an jedem PASS.

**Verdikt H-32:** PASS, wenn mindestens ein Eintrag PASS ist; "GL-012 (Pilot)", wenn kein Eintrag uebergeben wurde;
sonst DROP.

---

### 3. Die zwoelf Pflichtzeilen (PRD 3.3)

| # | Zeile | Inhalt |
|---|---|---|
| 1 | Power | alpha 0,05 einseitig je Fenster (z_krit 1,6449), Power 0,80, Cluster Woche, W 52/50; SE = SE des registrierten Tests (P-1 (3)/(4)), bindend die groessere aus v6-Null (stress) und Pilot-Streuung (DEC-94 (5)); Prior = Pilot-Punkt (DEC-99, Lesart A); Zuordnung mechanisch nach Regel U, nur C10. Vorab-MDE80 W1: 0,0206 / 0,0237 / 0,0287 / 0,0195. Doppelausweis A3-Praxis. |
| 2 | Entscheidungsrelevanz | PASS: getrennte Tradability-Registrierung (Dezil-Slippage, DEC-67 E4), "vorlaeufig bis F-WEEK". DROP eines uebergebenen Eintrags: beta-neutraler Wochen-IC dieser Charakteristik >= MDE80 auf Bybit-Perps 2024-07..2026-06 mit Power 0,80 nicht vorhanden. GL-012 (Pilot): kein Verdikt, gemessener Pilot-Punkt unter MDE80. Oekonomisches Etikett (C.2): Portfolio 0,0101, Einzelposition 0,062 (DEC-74 (k)); MDE80 ~0,02 liegt ueber dem Portfolio-, unter dem Einzelpositionswert. |
| 3 | Cluster-Einheit | Kalenderwoche; stationaerer Bootstrap (Block 4); N = 52/50 (Test), 114 (Pilot); Varianzfaktor c = max(1, c_hat) aus v6 bzw. Pilot (c_hat v5e 0,99..1,11 bei konsistenter Wochenzahl). |
| 4 | Selektions-Deflation | K = 4 (F-H32), z_max(4) = 1,052 < 1,6449; Decke ceiling_k4 (vorzeichenbereinigt, v6) < Schwelle, sonst GL-012; F-WEEK mit F-XSEC1 (7, p = 1). |
| 5 | Adversariales Fixture | Beta-korrelierte Charakteristik auf einem Panel mit dominantem, autokorreliertem, driftendem Marktfaktor (rho 0,2, Drift 0,002, beta 0,5..2,0) unter fm8 als Primaerstatistik: kein PASS (T1). Pilot-Leck-Fixture: Pilot-Modus bricht ab, wenn ein Outcome nach 2024-06-30 erreicht wird. Bounce-Fixture fuer rev_gap. |
| 6 | Kostenmodell-Bindung | `constants_hash` n/a (kapitalfrei); `tradability3` nicht gebaut. |
| 7 | Irreversibilitaets-Probe | nachladbar (Bybit v5 oeffentlich; Harvest-Export DEC-84). |
| 8 | Positivkontroll-Vorschaltung | ja, nach der Uebergabe und vor dem Test, allein (Abschnitt 4). Pruefen der Power-Annahme mit der 10-%-Regel DEC-94 (5). |
| 9 | Kapital/Steuer/Venue | n/a kapitalfrei; Zahler nach 2024: Delisting-Hazard ~50 % (Etikett). |
| 10 | Stress-Episode | Abdeckungsnachweis STRESS_REL/STRESS_ABS: W1 22/2, W2 8/1 Tage (Registry der Drittfassung, Kalender bis 2026-06-30); nach dem W2-Schnitt zaehlt v6 neu (2025-10-10 liegt innen); Pilot: v6. Die Listen werden nur fensterbeschraenkt ausgewertet (sie koennen Tage ab 2026-07-01 tragen). Nie Filter. |
| 11 | Ergebnis-Artefakte (DEC-53) | Pilot: Wochenserie je Variante (CSV + sha256), Bootstrap-Fingerprint, `h32_pilot.json` (result_sha256). Test: Wochenserie je uebergebenem Eintrag und Fenster, Bootstrap-/Permutations-Fingerprints, `h32_run_fingerprint.json` (Seed, Bit-Generator, Code-Hash, Daten-Fingerprints, Pilot-sha256), Haupt-JSON + MD. Fehlt etwas: KEIN VERDIKT. |
| 12 | Test-Pflichten | T0-T7, Abschnitt 5. |

---

### 4. Positivkontroll-Regel (woertlich, vorab fixiert)

> Die Positivkontrolle laeuft nur, wenn mindestens eine Variante uebergeben wurde, allein und vor dem Test, mit der
> registrierten YAML und dem Pilot-Ergebnis (beide sha256-gesperrt), auf der realen Wochenform von W1 und W2 (Wochen,
> PIT-Masken, K_t, `returns_valid`), mit synthetischen Renditen (reale Renditen werden nicht uebergeben).
> **Welt je Fenster:** stress-Kalibrierung (rho_f, beta_sd, null_scales aus der YAML), Marktspalte = Faktor, Drift 0,
> plus 8 Sektorbloecke mit Schock sigma_g; sigma_g wird per Bisektion (Seeds 2000..2049) so gewaehlt, dass die
> Wochen-SD des fm8-IC der uebergebenen Variante in der Negativkontrolle der bindenden SD der Power-Zeile (SE_T,W x
> sqrt(w_judged_W / c)) auf +-5 % entspricht; ist die Null-Quelle bindend, ist sigma_g = 0.
> **Injektion:** das PRD-Positiv-Fixture (Signal in der Charakteristik, unabhaengig vom Beta); die Amplitude wird auf
> den Seeds 1000..1049 (gemeinsame Zufallszahlen positiv/negativ) so kalibriert, dass der realisierte Injektionseffekt
> (Mittel positiv minus negativ der fm8-Statistik) im bindenden Fenster MDE80_W - max(0, null_mean_W) auf +-5 % trifft.
> **Urteils-Seeds:** 53..252 (200), positiv und negativ; Gate-Kette = Bedingungen (1a)-(1c) und (4b) des Tests mit den
> eingefrorenen Konstanten.
> **BESTANDEN genau dann, wenn fuer jede uebergebene Variante:**
> (a) die Wochen-SD des fm8-IC der Kontrollwelt <= 1,10 x SD der Power-Zeile in jedem Fenster (DEC-94 (5));
> (b) der Anteil der Seeds mit PASS im bindenden Fenster >= 0,734 (= 0,80 - 2,326 x sqrt(0,16/200));
> (c) die falsche PASS-Quote der Negativkontrolle je Fenster <= 0,086 (= 0,05 + 2,326 x sqrt(0,0475/200));
> (d) der realisierte Injektionseffekt auf den Urteils-Seeds innerhalb +-10 % des Ziels liegt.
> Ausgabe "Positivkontrolle BESTANDEN"/"NICHT BESTANDEN"; rc 0 nur bei BESTANDEN, 3 bei NICHT BESTANDEN, 1 bei Abbruch.
> Nicht bestanden: kein Test, Ursachenanalyse, neue DEC. Die gemeinsame C10-Quote wird berichtet, nicht geurteilt.

Begruendung der Zahlen und des Sektor-Befunds: EV-8 (synthetisch: PRD-Sektorwelt +17,6 % Wochen-SD; nominale Injektion
0,0206 realisiert 0,0156).

---

### 5. DEC-39-Trio und Test-Pflichten

| Stufe | Inhalt |
|---|---|
| T0 | Unit-Tests: Pilot-SE (P-1 (4)), Band, t, F2_real/c_real, SE_T,W-Formel, Regel U (jede Bedingung einzeln), vorzeichenbereinigte Decke, Gate-Funktion |
| T1 positiv | stress-Welt der Fensterform mit injiziertem fm8-IC = MDE80: Fensterbedingung besteht mit Quote ~0,8; uebergebener Eintrag besteht end-to-end |
| T1 null | signalfreie stress-Null: falsche PASS-Quote je Fenster <= alpha + MC-Toleranz; Uebergabequote im Pilot <= 0,01 |
| T1 adversarial | Beta-Proxy-Charakteristik bei dominantem, autokorreliertem, driftendem Markt (rho 0,2, Drift 0,002, beta 0,5..2,0): kein PASS unter fm8 primaer; Pilot-Leck: Abbruch, wenn eine Outcome-Woche nach 2024-06-30 erreicht wird; Siegel-Leck Test-Modus: Abbruch bei Outcome nach 2026-06-28 |
| T2 | Determinismus N >= 3 mit Fingerprint (Pilot, Test, Positivkontrolle) |
| T3 | kein Checkpoint (Round-Trip ueber T7, wie Drittfassung) |
| T4 | Uebergabe-Arithmetik auf konserviertem Pilot-Payload (Regel U rein funktional, zweimal gleich); Gate-Arithmetik auf konserviertem Test-Payload; Monotonie: hoeherer x_P kippt nie von Uebergabe zu GL-012, groessere SE nie von GL-012 zu Uebergabe |
| T5 | Pins: z_krit, mde_faktor, alpha, Block, Replikate, Seed, w_judged 52/50, W_P 114, v6-Konstanten in jedem Payload |
| T6 | Legacy-Import-Sperre |
| T7 | Artefakt-Round-Trip: Pilot- und Testserien plus Seed reproduzieren x_P, SE_P und die Gate-Schaetzer bitgleich; fehlt ein Artefakt: KEINE UEBERGABE bzw. KEIN VERDIKT |

---

### 6. Kill-Bedingungen (vorab) und Etiketten statt Kill

| Bedingung | Folge |
|---|---|
| min K_t < 117 im Pilot, < 134 in W1/W2 (PRD 5.3 Kill (2)) | Abbruch (heute: P 120, W1 345, W2 514 - nicht ausgeloest) |
| Regel U verfehlt | GL-012 (Pilot) des Eintrags, kein Verdikt |
| ceiling_k4 >= Schwelle | GL-012 des Eintrags vor dem Verdikt |
| Null-Nachrechnung ausserhalb +-10 %, Pin, Fingerprint, Artefakt, Pilot-sha256 | KEIN VERDIKT (ganzer Lauf) |
| Positivkontrolle NICHT BESTANDEN | kein Test, neue DEC |
| Bounce (nur rev_gap) | KEIN PASS |

Etiketten statt Kill: Liquiditaet, Survivorship (synthetisch), Block-Permutations-p, BH, Gap eine Woche (rev_gap),
Delisting = Announcement-Datum, NO_HISTORY (W1 LIT/MON/DATA, W2 SPCX), "fm8 entfernt nur das BTC-Beta; Sektor-/
Stilfaktoren bleiben Teil der gemessenen Groesse", "Pilot aus anderem Marktregime (2022-2024); die Uebergabe ist keine
Aussage ueber W1/W2".

---

### 7. Etikett C.17 (Wortlaut-Vorschlag) und Kontamination

> "H-32 (A3-fm8): W1/W2 und das Pilotfenster 2022-04..2024-06 sind fuer die fm8-Statistik von mom1/mom2/mom4/rev_gap
> blind - keine reale IC je gelesen. Gesehen: Survivorship-Differenz des rohen 4-Wochen-Momentum-IC IC_union -
> IC_survivors +0,0033 [-0,0076; +0,0132] ueber 271 Wochen (WP-7 B3, ganze Historie); Faktoranteil (R^2 Rendite auf
> PIT-Beta, vorzeichenfrei) W1 3,2 %, W2 1,4 %; Streuungen der Fenster (sigma_f, rho_f, sigma_e, Symbol-Vol, sigma_xs,
> Boden, K); synthetische Survivorship- und Null-Groessen; Literaturband 0,004..0,012 (Weg B) / 0,033 (Ficura-A*,
> Large and Liquid) / negativ bis ~0 breit; Ficura: Momentum grosser Coins seit 2021 nicht profitabel (Stichprobe bis
> 2022-12, ueberlappt den Pilot). Existiert, nicht geoeffnet: WP-7-Rohserie des 4-Wochen-Momentum-IC (alle Wochen),
> L-Siegeldateien v5c/v5d/v5e. Nie berechnet: Beta-Kalibrierungs-IC, Lag-Profil. Pilotperiode: A1 hat dort A3-Faktor-
> renditen gerechnet, gespeichert nur R^2/Steigungen/Residualstreuung, kein Mittel. W2-Kalibrierung v5e enthaelt die
> Woche 2026-06-29..07-05 (vor DEC-96). Vorwissen der Agenten ueber Marktniveaus 2022-2026: nicht quantifizierbar,
> nicht verwendet."

Nach dem Pilot zusaetzlich: "Pilot 2022-04-18..2024-06-17: fm8-IC der vier Varianten gesehen (x_P, SE_P je Variante,
result_sha256 ...)."

---

### 8. Entscheidungsrelevanz und Nicht-Wiederholungs-Nachweis (C.1)

- H-32 ist eine **neue Hypothese** mit eigenem K (DEC-58 E2, DEC-92 "Was nicht folgt", GL-032). F-XSEC1 hat nie
  gerechnet; H-32 wiederholt kein geurteiltes Experiment. Unterschiede zur Drittfassung: fm8 als Primaerstatistik
  (Wochen-SD ~0,05 statt Roh-IC 0,13), P-1-Schwelle (DEC-94), Prior aus dem Pilot statt Literatur 0,03 (DEC-99), W2
  am Blind-Siegel geschnitten, K = 4.
- Gegen D.7 (C-06/H-07/H-08) wie Drittfassung: Breite K_t >= 345 (Test) bzw. >= 120 (Pilot) statt N = 5; Wochen- statt
  Stundenhorizont; Beta-Neutralisierung; survivorship-freies Union-Panel.
- PASS -> Tradability-Registrierung; DROP -> fuer die Charakteristik "beta-neutraler Effekt >= MDE80 nicht vorhanden",
  ausdruecklich KEIN Urteil ueber Effekte < MDE80 und ueber den rohen IC; GL-012 (Pilot) -> kein Verdikt, W1/W2 bleiben
  blind fuer kuenftige Hypothesen.

---

### 9. Abweichungen von PRD/Drittfassung (registriert, etikettiert)

1. Primaerstatistik fm8 statt roher IC; roher IC wird nicht gerechnet (Blindheitsschutz).
2. Schwelle z_krit 1,6449 (P-1) statt 2,4865; Doppelausweis A3-Praxis.
3. Prior aus dem Pilot (DEC-99) statt Literatur 0,03.
4. W2 endet 2026-06-28 (w_judged 50) statt 2026-06-30 mit Outcome bis 2026-07-05.
5. Null mit Beta-Vorlauf (v6) statt ohne; Null-Quantil auf Niveau 0,95 statt 0,9936 (P-1 (1); Review Programm-Bilanz B-1 (5)).
6. Selektionsdecke vorzeichenbereinigt (Nebenbefund: `nulls._mean_of_max` nimmt rohe Vorzeichen).
7. Kein DEC-52-Zweig (Regel U), kein Lag-Profil, kein Beta-Kalibrierungs-IC, keine Persistenz-Null.
8. rev_gap im Ein-Wochen-Gap (DEC-87 (B)) - PRD-Ein-Tages-Design nicht getestet.

---

### 10. Registry-YAML-Block (Entwurf, Template PRD 3.4)

```yaml
id: H-32
kohorte: A3 / F-H32
klasse: W
capital_free: true
hypothese: "Mindestens eine von mom1, mom2, mom4 (positiv) bzw. rev_gap (negativ): mittlerer woechentlicher Rank-IC der Charakteristik gegen das fm_neutral_8w-neutralisierte Folgewochen-Outcome in W1 UND W2 in Richtung >= z_krit * SE (P-1) und >= 95-%-Null-Quantil; getestet nur nach Uebergabe durch den Pilot 2022-04-18..2024-06-17 (Regel U)."
ertragsquelle: "Prognose (mom: spaete Trendfolger; rev_gap: Liquiditaetsbereitstellung) - netto Markt-Beta"
metric: "Mittel des woechentlichen Spearman-IC (Charakteristik_t vs. fm8-Residuum der Folgewochen-Log-Rendite_t+1, close_at_last, min 10) ueber die geurteilten Wochen"
richtung: {mom1: positiv, mom2: positiv, mom4: positiv, rev_gap: negativ}
windows:
  - {id: P,  von: 2022-04-18, bis: 2024-06-30, wochen_geurteilt: 114, rolle: pilot_nicht_urteilstragend}
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen_geurteilt: 52, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-28, wochen_geurteilt: 50, rolle: urteilstragend}
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
  n_eff: "W/c, c = max(1, c_hat) aus v6 und Pilot"
  a_priori_effekt: "Pilot-Punkt x_P je Variante (DEC-99, Lesart A)"
  detectable_effect_mde80_vorab: {W1: {mom1: 0.0206, mom2: 0.0237, mom4: 0.0287, rev_gap: 0.0195}, W2: {mom1: 0.0165, mom2: 0.0184, mom4: 0.0221, rev_gap: 0.0167}}
  zuordnungsregel: "Regel U (ERSTFASSUNG 1.8), power_p1.assign_regime; Doppelausweis assign_regime_a3_practice"
  ref: "state/herleitung_h32/power_h32.json"
selection: {K: 4, z_max: 1.052, ceiling: "v6 ceiling_k4", over_family: F-WEEK}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, label: "Etikett C.2"}
decision_relevance: {on_pass: "Tradability-Registrierung, vorlaeufig bis F-WEEK", on_drop: "beta-neutraler Effekt >= MDE80 der Variante nicht vorhanden", on_gl012_pilot: "kein Verdikt, W1/W2 bleiben blind"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", zahler_post_2024: "Delisting-Hazard ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json, stress_abs.json (nur fensterbeschraenkt auswerten)", rolle: abdeckungsnachweis}
irreversibility_probe: {ergebnis: nachladbar}
positive_control: {vorgeschaltet: true, regel: "ERSTFASSUNG 4", seeds: "53..252"}
fixtures: {positive: "T1 positiv (fm8-Injektion = MDE80)", null: "T1 null (stress-Null)", adversarial: "T1 Beta-Proxy + Pilot-Leck + Siegel-Leck"}
artifacts: {pilot: "h32_pilot_<v>_P_ic_weekly.csv + sha256, h32_pilot.json", test: "h32_run_<v>_<W>_ic_weekly.csv + sha256, h32_run_fingerprint.json"}
fdr_family: "F-H32 (K = 4, BH 0.10 report-only, p = 1 ohne Uebergabe)"
over_family: "F-WEEK (BY, mit F-XSEC1)"
feasibility_verdict: "offen bis Pilot (Regel U)"
constants_hash: "n/a - kapitalfrei"
data_fingerprints: ["panel_export 03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb", "union_range a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933", "as_of 2026-09-28"]
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e, Vorlauf v6]
etiketten: ["zugelassen nur durch DEC-99 (Pilot-Prior)", "C.17 (Abschnitt 7)"]
```

---

### 11. Registrierungsdatei (Schema-Entwurf `state/registered/h32_v1.yaml`, neue Felder fett beschrieben)

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
selection: {K: 4, bh_denominator: 4, bh_alpha: 0.10, bh_report_only: true, over_family: F-WEEK}
pilot_window:                              # NEU
  start: '2022-04-18'
  end: '2024-06-30'
  first_formation_week: '2022-04-18'
  last_formation_week: '2024-06-17'
  last_outcome_day: '2024-06-30'
  w_pilot: 114
  k_min_rule: 117
  role: pilot_nicht_urteilstragend
  se_rule: {floor: true, sd: true, stationary_bootstrap: {mean_block: 4, n_rep: 1000, seed: 53}}
  band: {level: 0.80, form: normal_zweiseitig, z: 1.2816}
  report_only: [bootstrap_percentile_band, liquidity_buckets_3_10, ic_without_bucket_1]
  not_computed: [raw_ic, lag_profile, beta_calibration_ic]
handover_rule:                             # NEU
  version: U-1
  conditions:
    - {id: i,   text: "x_P > 0 in registrierter Richtung"}
    - {id: ii,  text: "x_P - max(0, m) >= mde_faktor * max_W SE_T,W"}
    - {id: iii, text: "t_P >= t_min"}
  t_min: 2.0
  prior_reading: point                     # Lesart A; 'lower80' waere Lesart B
  se_T_sources: [frozen_v6_se_mean, pilot_k_adjusted]   # bindend die groessere (DEC-94 (5))
  pilot_k_adjusted: "sqrt(max(1, c_real)) * sqrt(v_fm8_W + F2_real) / sqrt(w_judged_W)"
  null_mean_credit: "m = max_W null_mean_W (in Richtung), nur positiver Teil"
  regime_function: power_p1.assign_regime
  double_statement: power_p1.assign_regime_a3_practice
  on_fail: {status: gl012_pilot, p_value: 1.0}
  result_lock: "--pilot-result + --pilot-result-sha256 im Testlauf; Uebergabe bitgleich nachgerechnet"
windows:
  W1:
    start: '2024-07-01'
    end: '2025-06-30'
    w_judged: 52
    calibration: {measured: {...v5e...}, stress: {...v5e...}, zero: {...v5e...}}
    null_scales: {sigma_f: 0.06685192489159383, sigma_e_used: 0.1206430784847655}
    frozen_v6: {se_mean: {mom1: .., mom2: .., mom4: .., rev_gap: ..}, sd_week: {...}, null_mean: {...}, q95: {...},
                q95_driftfree: {...}, q95_drifting: {...}, ceiling_k4: .., floor_fm8: .., v_fm8: .., k_fm8_series_sha256: ..}
    bounce_sigma_true: 0.1718564938769564
    survivorship: {mom1_diff_in_ic_min_units: -0.19807571898782755, rev_gap_diff_in_ic_min_units: -0.18910982801933468}
  W2:
    start: '2025-07-01'
    end: '2026-06-28'                      # Blind-Siegel DEC-96 E3
    w_judged: 50
    calibration: {...v5e...}
    null_scales: {sigma_f: 0.05514230351329163, sigma_e_used: 0.10729439736101687}
    frozen_v6: {...}
    bounce_sigma_true: 0.13310944847015532
    survivorship: {mom1_diff_in_ic_min_units: -0.4376229105721445, rev_gap_diff_in_ic_min_units: -0.5793462946362501}
beta_control: {method: fm_neutral_8w, beta_window_weeks: 8}
rules: {seed: 53, n_reps: 1000, mean_block: 4, null_level: 0.95, bounce_spread: 0.003621}
positive_control:
  seeds: [53, 252]
  calibration_seeds_injection: [1000, 1049]
  calibration_seeds_world: [2000, 2049]
  inject_target: mde80_binding_window_minus_credit
  criteria: {sd_ratio_max: 1.10, pass_share_min: 0.734, neg_pass_max: 0.086, injection_tolerance: 0.10}
seal: {pilot_last_outcome_day: '2024-06-30', test_last_outcome_day: '2026-06-28'}
data_fingerprints:
  union_range_fingerprint: a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a
  delisting_dates_sha256: 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933
```

---

### 12. Bauliste (Abnahme durch den Orchestrator; additiv, A3-Code unberuehrt)

1. **Vorlauf v6** (outcome-frei, neues Modul): Null mit 8 Beta-Vorlaufwochen fuer W1/W2 (geschnitten), K = 4, 1.000
   Replikate, driftfrei und Drift 0,002; Ausgabe `frozen_v6` je Fenster; K_fm8-Reihen fuer P, W1, W2 nur aus
   `returns_valid`; Stress-Abdeckung nur fensterbeschraenkt; Template-Emitter fuer `h32_v1.yaml`.
2. **Pilot-Modus** `--pilot` (CLI neu, z. B. `scripts/h32_fm8.py`): Startsperre, Siegel-Waechter (PP4), Pilot-Statistiken
   (1.7), Regel U, `power_p1`-Zuordnung, DEC-53-Artefakte, `h32_pilot.json`.
3. **Testlauf** `--run`: Pilot-Sperre (P0'), nur uebergebene Eintraege, P-1-Gate als neue reine Funktion (T4),
   `power_p1.stationary_bootstrap_se`, Siegel-Waechter (P7), keine Nebengroessen.
4. **Positivkontrolle** `--positive-control`: Welt- und Injektions-Kalibrierung, 200 Seeds, Kriterien Abschnitt 4.
5. **Neue vorzeichenbereinigte Decke** (nicht `nulls._mean_of_max` aendern).
6. **Tests** Abschnitt 5; Gesamtzahl der Tests steigt, keine wird reduziert.
Aufwand: ~1.350 Zeilen Code, ~1.050 Zeilen Tests, zwei Bau-Sitzungen; Cloud: v6 ~0,5-1 h, Pilot < 15 min,
Positivkontrolle ~15-30 min, Test ~1 h (UNBELEGT).

---

### 13. Ablauf und Rueckbauweg

DEC-99 -> EV-Entscheidungen -> Bau -> Vorlauf v6 -> YAML + sha256 -> Review -> Registrierung -> Pilot (nur P) ->
Uebergabe-Vermerk mit sha256 -> [keine Uebergabe: GL-012 (Pilot), Ende, W1/W2 ungeoeffnet] -> Positivkontrolle allein ->
[NICHT BESTANDEN: neue DEC] -> Test W1/W2 -> Gate-Check nur gegen diesen Text -> GL-Eintrag. Rueckbauweg: Registry
append-only; dieser Entwurf hat keine Rechtswirkung.
