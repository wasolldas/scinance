# Adversarischer Registrierungs-Review H-28/H-29/H-30 Drittfassung (v3) - 2026-10-12

Rolle: adversarischer Registrierungs-Reviewer mit Veto-Recht, nur lesend. Keine Repo-Datei geaendert, nichts
committet (`git status` vor und nach dem Review leer; Tests mit `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`).
Siegel gewahrt: keine `*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv` geoeffnet,
gehasht oder gegrept; kein `--run`, keine Positivkontrolle, keine reale Charakteristik-Outcome-Rechnung.

Gegenstand:
- Registry-Text `scratchpad/drittfassung/DRITTFASSUNG_H28_H30_final.md` (760 Zeilen, im Folgenden "Text").
- Registrierungs-YAML `scratchpad/reg/h28_h30_v3.yaml`, sha256 `bd948f34...c299` (nachgerechnet, stimmt).
- Code `849ec4a` (Arbeitsbaum sauber = 849ec4a). Vorlauf v5e: `wp13a_prelaunch.json` sha256 `94d65559...b3b2`,
  `wp13a_prelaunch.md` sha256 `dede4f05...f4fb` (beide nachgerechnet, stimmen).

Gelesen: DEC-51..53, DEC-73..DEC-89 (inkl. DEC-86-Nachtrag); Verfassung `scinance3-impl/CLAUDE.md`; PRD 3.1, 3.3,
3.4, 5.3; REVIEW v1, v2, Gate-Audit v5c; Herleitungsakte (Entwurf, ENTSCHEIDUNGSVORLAGEN, ABGLEICH); Registry
(Erst-/Zweitfassung, Rueckzuege); Code `gates.py`, `run.py`, `positive_control.py`, `nulls.py` (relevante Teile),
`ic.py` (IC, Beta-Kontrolle), `characteristics.py` (mom/rev/beta/decile), `prelaunch.py` (Freeze-Aufruf),
`scripts/wp13_xsec.py`, `wp7_universe/panel_load.py` (Wochenrenditen, Fingerprint); Tests (Namen, T1/PC-Tests).

Eigene Nachrechnungen (nur Vorlauf-JSON, YAML, Synthetik): Skripte unter `scratchpad/review_v3/`
(`cmp.py`, `power.py`, `nums.py`, `nums2.py`, `nums3.py`), `--emit-registered-template` auf v5e nach
`scratchpad/review_v3/emitted.yaml`, `run.validate_registered/resolve_rules/check_data_fingerprints` auf die YAML,
`run.bounce_fixture_ic` mit den registrierten Parametern (rein synthetisch), `run.code_fingerprint()`,
WP-13-Testsuite (`tests/unit/test_wp13_run.py`, `test_wp13_xsec.py`): **266 passed** (613 s).

---

## 0. Urteil

**VETO (formal), aufhebbar ohne Code-, YAML- oder Vorlauf-Eingriff.** Zwei blockierende Punkte, beide reine
Text-/Log-Ergaenzungen (Abschnitt 7, B-1 und B-2). Der sha256 der YAML (`bd948f34...c299`) bleibt unveraendert;
nach Behebung gilt FREIGABE, ohne dass die Zahlen erneut geprueft werden muessen.

Sachlich ist die Drittfassung sauber:
- Kein Torpfosten verschoben, in keine Richtung (Abschnitt 1).
- Alle Zahlen in Text und YAML stimmen mit v5e ueberein; die YAML-Konstanten sind **bitgleich** zum Vorlauf, die YAML
  ist exakt die `--emit-registered-template`-Ausgabe aus v5e plus die zwei DEC-88-Sperren (Abschnitt 2).
- Die DEC-88-Power-Zuordnung reproduziert sich mit den Formeln aus Vorlage F auf drei Stellen (Abschnitt 2).
- `gates.evaluate`/`run_full`/`evaluate_entry` werten Gate (1)-(7) genau wie registriert aus; im registrierten
  CLI-Pfad gibt es keinen PASS-Pfad ausserhalb des Textes und keinen erreichbaren stillen Rueckfall (Abschnitt 3).
- `--positive-control` entspricht DEC-89 E2 und laeuft ueber denselben Per-Eintrag-Pfad wie der Lauf (Abschnitt 4).

---

## 1. Torpfosten (Text und YAML gegen DEC-73..89)

Ergebnis: **keine Verschiebung.** Gepruefte Punkte:

| Regel | Bindende Quelle | Text / YAML / Code | Befund |
|---|---|---|---|
| SE = max(B_W, SD(IC_t))/sqrt(W), W 52/51 | DEC-75 (1) | Text 328-332; `run.se_of_mean_ic` 289-298; YAML `w_judged` 52/51 | gleich |
| \|IC\| >= 2,4865 x SE | DEC-75 (1), DEC-74 (d) | Text 328; `gates.py:100` | gleich |
| Block-Bootstrap Block 4, 1.000, Seed 53, Niveau 0,9936, Perzentil | DEC-75 (1) | Text 333-336; `run.py:301-340`; YAML `block_len`/`level` T5-gepinnt | gleich |
| \|IC\| >= IC_min_capped, max(1, c_rho_bk) | DEC-74 (a)/(b), DEC-75 (8) | YAML `ic_min_capped` = v5e bitgleich | gleich |
| Beta-Kontrolle: Vorzeichen, >= IC_min, jenseits q (99,36 %) | DEC-75 (3), DEC-76 (b), DEC-87 (E) | Text 352-358; `gates.py:104-115`; `nulls.binding_quantile` | gleich; q = extremeres von 0/0,002 |
| Methode fm_neutral_8w, Beta-Fenster 8 | DEC-86, DEC-88 | YAML `beta_control`; `run.resolve_beta_control` | gleich |
| GL-012-Decke = fm8, stress, driftfrei, Mittel des Max. ueber 7, 1.000, Seed 53 | DEC-87 (A), DEC-88 | YAML 0,0083400760 / 0,0068524887 | gleich |
| Kill Decke >= IC_min vor dem Verdikt | DEC-75 (2) | `gates.py:182-188, 211-213` | gleich |
| Stress = 2 x rho_f und 2 x Anteil | DEC-78, DEC-85 (iv) | YAML `calibration.stress` = v5e | gleich |
| Kalibrierung je Fenster | DEC-87 (D) | YAML `windows.<W>.calibration`; globaler Block abgewiesen | gleich |
| Gap eine Woche, DEC-52 nicht genutzt | DEC-87 (B) | Text 360-362, Abweichung 1 | gleich |
| Bounce je Fenster -> KEIN PASS | DEC-75 (5), DEC-87 (I) | `gates.py:200-216` | gleich |
| Liquiditaet: Etikett bei IC_ohne_D1 > -0,5 IC_min in >= 1 Fenster | DEC-74 (f), DEC-87 (I) | `gates.py:229-242` | gleich |
| Survivorship = Etikett | DEC-76, DEC-89 E3 (2) | `gates.py:244-252` | gleich |
| Persistenz-Null report-only, 1.000 Sim., beide Fenster | DEC-75 (6), DEC-89 E3 (4) | `run.py:1153-1169` (evaluate_entry) | gleich |
| BH 0,10 report-only, Nenner fest 7, gesperrt = p 1 | DEC-74 (e), DEC-87 (J) | `run.py:1380-1398`, `benjamini_hochberg` 467-498 | gleich |
| Power-Zuordnung, MDE80 > 0,03 -> GL-012 | DEC-51 (2), DEC-87 (F), DEC-88 | YAML-Sperren mom2/mom4 | gleich (Abschnitt 2) |
| H-30 Feasibility > 0,5 -> GL-012 vor dem Lauf | DEC-74 (h), DEC-87 (G) | v5e 2,764; YAML-Sperren vol_rv/vol_max/vol_beta | gleich |
| vol_beta strukturell (C.4) | DEC-87 (H) | YAML-Grund | gleich |
| Bounce-Parameter gemessen | DEC-89 E1 | YAML 0,003621 / 0,17186 / 0,13311 | gleich (Zensus D10 36,21 bp nachgelesen) |
| K-Floor 134 | PRD 5.3 Kill (2) | Text 657 | gleich |

Die Varianten-Auswahl (gerechnet nur mom1, rev_gap) ist keine nachtraegliche Teilkohorte im Sinne Gate-Audit v5c
Punkt 3: jede Sperre folgt einer vorab bestehenden Regel (DEC-51 (2) via DEC-87 (F), DEC-74 (h) via DEC-87 (G),
C.4 via DEC-87 (H)), mechanisch auf outcome-freien v5e-Zahlen, und K = 7 bleibt in Decke und BH-Nenner.

---

## 2. Konsistenz (Text, YAML, v5e)

**YAML gegen v5e, bitgleich** (`review_v3/cmp.py`, Vergleich mit `==`, 0 Abweichungen):
`windows.<W>.{start,end}`, alle 7 `ic_min_capped` [v5e `<W>.noise_floor_and_threshold.ic_min_capped_per_variant`],
`w_judged`, `ceiling_method_stress` und alle 2 x 7 Quantile [v5e `<W>.frozen_null_constants`], alle
`calibration.{measured,stress,zero}.{rho_f,beta_sd_calibrated,target_factor_share}`
[v5e `<W>.beta_control_method_study.calibrations`], stress-Paar zusaetzlich = `frozen_null_constants.{rho_f,
beta_sd_calibrated}`, `bounce_sigma_true` = [v5e `<W>.factor_preserving_null.driftfree.sigma_e_median_symbol_weekly`],
`survivorship` = [v5e `<W>.survivorship_fixture.*_diff_in_ic_min_units`], `null_scales` = [v5e
`<W>.beta_control_recommended_high_rep.stress.{sigma_f, sigma_e_used}`] (0,06685192489159383 / 0,1206430784847655;
0,05514230351329163 / 0,10729439736101687), `data_fingerprints` = [v5e `data_fingerprints`].

**YAML gegen Generator:** `scripts/wp13_xsec.py --emit-registered-template` auf v5e erzeugt eine Datei, die sich von der
Registrierungs-YAML nur durch die vier Zeilen `status: gl012_pre_run` + `reason` bei `H-28_mom2` und `H-28_mom4`
unterscheidet (DEC-88). Keine Handeingriffe an Zahlen.

**Code-Pruefungen auf der YAML:** `validate_registered(require_frozen_constants=True)` bestanden;
`resolve_rules` = {seed 53, n_reps_bootstrap/_permutation 1.000, n_reps_factor_null 1.000, n_sims_persistence 1.000,
block_len 4, level 0,9936, bh_alpha 0,1, bounce_spread 0,003621}; `check_data_fingerprints` gegen v5e bestanden;
`binding_quantile` mom1 W1/W2 +0,022435/+0,017005, rev_gap -0,016663/-0,015457 (je driftfrei bindend). Bestaetigt
Text 26-29.

**Text-Zahlen gegen v5e (Stichproben, alle stimmen):**
- IC_min aus der Formel nachgerechnet: mom1 W1 2,4865 x 0,0485790 x 1,1739065 / sqrt(52) = 0,0196639 (bitgleich YAML);
  rev_gap W2 0,0153148; vol_beta W1 (gedeckelt) 0,0167508; c_rho_bk und Persistenz-q aller 14 Zellen = Text 168-176.
- Gewinner-Bestaetigung [v5e `beta_control_confirmation.attempts[0].windows.<W>.row`] = Text 134-137;
  Schwachstelle mom4 W1 stress 0,0016463 vs. 0,0016842, SE 0,0106068/sqrt(1000) -> 0,11 SE = Text 139-146.
- Kalibrierungstabelle inkl. Gegenprobe z 0,63/0,02/1,03 und 1,90/1,24/1,90 = Text 151-158.
- Decken analytisch 0,009342/0,008141, Rauschen 0,009185/0,007782, Drift 0,008514/0,006957, min IC_min/Decke
  2,008/2,131 = Text 200-207.
- Floor 0,0485790/0,0419214, K 345/419/514 und 514/589/603, Symbol-Wochen 22.300/29.126, Delisting 80/140,
  NO_HISTORY, Gate (5) 0,159/0,150/0,154 und 0,142/0,104/0,050, H-30 91,42 / 2,764 / 0,175 / 7,0, STRESS 22/8 und
  2/1, Coverage 0,889/0,877, Zensus-sha256 und STRESS-sha256 = Text.

**Power-Zuordnung DEC-88 gegen Vorlage F** (`review_v3/power.py`; Formeln wie ENTSCHEIDUNGSVORLAGEN F bzw. DEC-88,
q = bindendes Quantil, sd = `mean_ic_draws_sd` der bindenden Driftzelle):

| Variante | W1 P_ICmin / P_beta / P_voll / MDE80 | W2 P_ICmin / P_beta / P_voll / MDE80 | Zuordnung |
|---|---|---|---|
| mom1 | 0,904 / 0,832 / **0,832** / 0,0291 | 0,963 / 0,976 / **0,963** / 0,0233 | C.10 hart |
| mom2 | 0,961 / 0,597 / 0,597 / **0,0353** | 0,989 / 0,912 / 0,912 / 0,0264 | GL-012 |
| mom4 | 0,966 / 0,380 / 0,380 / **0,0424** | 0,991 / 0,722 / 0,722 / **0,0321** | GL-012 |
| rev_gap | 0,967 / 0,949 / **0,949** / 0,0238 | 0,991 / 0,986 / **0,986** / 0,0210 | C.10 hart |
| vol_rv, vol_max (formal) | 0,946 / 0,0245 | 0,986 / 0,0216 | GL-012 (Feasibility) |

Identisch mit DEC-88 und Text 66-74. MDE80 = max(1,3385 IC_min, max(IC_min,|q|) + 0,8416 sd) ist die zu (1d)/(3b)
passende Form (1,3385 = 3,3281/2,4865).

---

## 3. Code gegen Text (Gate (1)-(7), Abbrueche, Rueckfaelle)

| Text | Code | Befund |
|---|---|---|
| P0 Startsperre | `scripts/wp13_xsec.py:238-258` | vor jedem Panel-Byte |
| P1 Schema strikt, vor Panel | `scripts/wp13_xsec.py:279-288` -> `run.validate_registered(..., True)` `run.py:819-925` | alle genannten Ablehnungen vorhanden |
| P2 beta_control | `run.resolve_beta_control` (`run.py:1251`) | nach Panel-Ladung, vor allem anderen |
| P3 Fingerprints | `run.py:1254-1255`, `check_data_fingerprints` | YAML traegt den Block -> immer geprueft |
| P4 T5-Pins | `resolve_rules` (`run.py:1259`), `registered_window_constants` | block_len, level, w_judged -> ConstantPinError |
| P5 returns_valid | `nulls.estimation_returns` (`run.py:1269`) | ValueError -> rc 1 |
| P6 Null-Nachrechnung +-10 %, alle 7, abs 1e-4 bei 0 | `run.py:1325-1352`, `assert_null_calibration` 239-272 | gleich; geurteilt gegen eingefrorene Werte |
| P7 DEC-53 vor Verdikt | `write_run_artifacts`/`verify_run_artifacts`, `cmd_run` loggt erst danach | gleich |
| gesperrt: nicht gerechnet, DROP + Etikett, p 1 | `_locked_result`, `p_by_variant` init 1,0 | gleich |
| GL-012 vor PASS-Logik | `gates.py:182-188, 211-213` | gleich |
| (1a)-(1d), NaN verfehlt, SE 0/NaN verfehlt | `gates.py:99-102` | gleich |
| (3b-i)-(3b-iii), Quantil ohne IC_res verfehlt | `gates.py:104-115`; q aus YAML (`run.py:1185-1186` via ctx) | gleich |
| (4b) Bounce je Fenster, registrierte Parameter, Seed 53 | `gates.py:200-209`; `run.py:1129-1141`; `bounce_fixture_ic` ohne Defaults | gleich |
| (4c) Liquiditaet je Fenster | `gates.py:229-242`; `run.py:1123-1128` | gleich (Bedingung nicht mehr invertiert) |
| Survivorship-Etikett mom1/rev_gap | `run.py:1171-1176`, `gates.py:244-252` | gleich |
| (5) nur H-30 | `gates.py:117-121` | gesperrt, nicht ausgewertet |
| Verdikt je Hypothese, H-30 "GL-012 vor dem Lauf" | `aggregate_hypotheses` `run.py:1431-1463` | gleich |

Zusaetzlich geprueft: `variant_window_payload` liefert immer W1 und W2 (keine Ein-Fenster-Payload, die
`gates.evaluate` als PASS durchliesse); `beta_control_method` ist gesetzt, also nie der `residualize_outcome`-Altpfad;
`fm_neutralize_outcome` (OLS mit Achsenabschnitt, t und t+1 lebend, >= 5) und PIT-Beta aus `returns_est` mit
`min_weeks = 8` wie im Text; Wochenrendite `returns[t] = ln(c_t/c_{t-1})` (`panel_load.py:313-321`), rev_gap teilt
keinen Schlusskurs mit dem Outcome; Vorlauf-Pipeline zwischen 92607da und 849ec4a ohne Diff
(`prelaunch/nulls/characteristics/ic`), `gates.py`-Diff nur das Survivorship-Etikett, `run.py` nur Extraktion von
`evaluate_entry` plus DEC-89-Eingaben (alte Bounce-Defaults und W1-only-Persistenz entfernt). Die Nachrechnung in P6
benutzt dieselbe Funktion, dieselben Fensterarrays, Seed, Replikate und Quantilniveau (1,0 - 0,0064 == 0,9936 in
float) wie der Freeze in `prelaunch.py:1077-1081` -> bei identischem Panel bitgleich.

**PASS-Pfade ausserhalb des Textes / stille Rueckfaelle:** im registrierten CLI-Pfad keine erreichbar. Die
theoretischen Rueckfaelle (`gates.py:110` Quantil fehlt -> erfuellt; `run.py:1339` und Folgezeilen Decke/Quantil
fehlt -> Nachrechnung; `resolve_rules` block_len/level fehlt -> Code-Konstante; `registered_window_constants`
w_judged fehlt -> Fensterwert; `gates.py:205` Bounce nicht endlich -> keine Pruefung) sind durch den strikten
Preflight bzw. die deterministische Fixture versperrt (Abschnitt 7, N-7/N-8).

---

## 4. Positivkontrolle

**DEC-89 E2, Punkt fuer Punkt:**
- Welt der kalibrierten stress-Null: `nulls.simulate_factor_panel` (dieselbe Funktion wie die eingefrorene Null) mit
  `null_scales` (= v5e stress-Zelle, bitgleich), stress-rho_f/beta_sd des Fensters, `market_index` (Marktspalte :=
  Faktor), Drift 0 (`positive_control.py:101-128, 158-168`). Zusatz: 8 Sektorbloecke, sigma_g = 0,375 sigma_e
  (PRD-Fixture) und Injektion IC 0,06: mom1 positiv (r[t-1]), rev_gap negativ (r[t-2], Ein-Wochen-Gap)
  (`:170-184`).
- Echte Fensterform: Wochenraster, PIT-alive, returns_valid, Symbolreihenfolge; reale Renditen werden vor der
  Kontrolle geloescht (`scripts/wp13_xsec.py:408-410`), `run_positive_control` hat kein `returns`-Argument.
- Eingefrorene Konstanten aus der YAML; Test-Fixture `pc_report` patcht alle Null-Funktionen auf Abbruch und
  beweist so, dass nichts nachgerechnet wird.
- Seeds 53/54/55; jede andere Seed-Tupel ergibt nie BESTANDEN (`positive_control.py:349-353`).
- Negativkontrolle: identischer Zufallsstrom, Signal 0 (Test `..._negative_control_differs_only_by_it`).
- Kriterium (`_criteria`, `:368-378`): beide Eintraege PASS in allen Seeds UND Negativkontrolle in keinem Seed PASS;
  fehlender/gesperrter Pflicht-Eintrag -> nicht bestanden; rc 0 nur bei BESTANDEN, 3 sonst, 1 bei Abbruch.

**Testet sie den Lauf-Pfad?** Ja fuer alles, was einen falschen Verdikt erzeugen kann: dieselben Leser
(`resolve_beta_control`, `validate_registered` strikt, `check_data_fingerprints`, `resolve_rules`,
`registered_window_constants` mit w_judged-Pin), dieselben Charakteristik-/Beta-Funktionen mit denselben Parametern
wie `compute_all_characteristics`/`run_full`, und dieselbe Per-Eintrag-Kette `run.evaluate_entry` ->
`run_hypothesis` -> `variant_window_payload` -> `gates.evaluate` gegen dieselben YAML-Konstanten. Nicht abgedeckt
sind nur: die reale Wochenrenditen-Konstruktion (by design, DEC-89 E2; von mir im Code gelesen, ohne Look-ahead),
die Null-Nachrechnung (nur Abbruchpfad), Artefakte (nur Abbruchpfad), BH/Persistenz/Permutation (nur Etiketten) und
die triviale Aggregation. Ein Defekt dort fuehrt zu KEIN VERDIKT oder falschen Etiketten, nicht zu einem falschen
PASS/DROP. Zaehne belegt: `test_dec89_pc_fails_when_the_injected_signal_is_too_weak`,
`test_dec89_pc_fails_with_a_broken_gate` (Decke ueber IC_min bzw. Immer-PASS-Gate -> NICHT BESTANDEN).

Grenze (kein Defekt): IC 0,06 gegen effektive Schwellen <= 0,0224 belegt Funktion, nicht Power an der Schwelle;
dafuer steht `test_near_threshold_hit_rate_about_half`.

---

## 5. Pflichtzeilen und Reviews

Die zwoelf Zeilen (Text 621-649) sind vorhanden und mit Fundstellen belegt. Einschraenkungen: Zeile 3 ohne
effektives N als Zahl (N-5), Zeile 5 mit ueberzogener Aussage zur Negativkontrolle (N-2).

Review v1 (alle Punkte in DEC-74): erfuellt. Review v2: B-1..B-9 erfuellt (B-5/B-6 durch DEC-87 (G) und Sperre
gegenstandslos, B-7 Bounce in Kraft, Survivorship nach DEC-76 Etikett); W-10..W-14, W-16..W-21 erfuellt;
**W-15 (Kendall-Bias der AR(1)-phi) im Finaltext nicht adressiert** (N-3). Gate-Audit v5c: D1 (Marktspalte :=
Faktor) und D2 (NaN statt 0, Beta-min_weeks je Symbol ueber `returns_est`) umgesetzt (DEC-85, Code); Punkt 3
(Teilkohorte) nicht verletzt (Abschnitt 1); Anmerkung "rho_f nicht Kendall-korrigiert" bleibt Anmerkung.

---

## 6. Was den Lauf ungueltig machen oder einen Falsch-PASS/-DROP erzeugen koennte

- **Bounce-Kill ist in der registrierten Konfiguration wirkungslos, aber kein Falsch-DROP-Pfad:** synthetisch
  nachgerechnet (`run.bounce_fixture_ic`, registrierte Parameter, Seed 53): W1 (53 Wochen, K 419) IC_bounce
  -0,0036; W2 (52 Wochen, K 587/588/589 je nach K der letzten, ungeurteilten Woche) -0,0049/+0,0062/+0,0031. Alle
  |IC_bounce| < IC_min(rev_gap) 0,01727/0,01531, also kann (4b) gegen ein sonst bestehendes Fenster nie feuern. Das
  entspricht DEC-89 E1 ("Parameter tragen kaum"). Hinweis: die Fixture ist ein Einzelzug (SD ~0,007); bei K 590/594
  laege W2 bei 0,0147/0,0162 - die Unbedenklichkeit gilt fuer die tatsaechlichen K.
- **Drift 0,002 ist UNBELEGT als Messgroesse** (EV-E), aber bindend nach DEC-87 (E). Gegenrechnung: der mechanische
  Term skaliert mit E[f_t f_{t+1}] = rho sigma_f^2 + mu^2; die stress-Welt (W1 4,1e-4) liegt auch bei einer
  realen Wochendrift von ~0,01 ueber measured + Drift (2,1e-4 + 1,0e-4). Kein Defekt.
- **Positivkontrolle ist kein technisches Gate des Laufs** (`cmd_run` prueft kein BESTANDEN-Artefakt); die
  Reihenfolge ist prozedural (N-9).
- **Code-Stand nur als Commit genannt** (N-6): nach dem Registrierungs-Commit ist HEAD != 849ec4a.
- Laufzeit > Werkzeuglimit (v5e-Erfahrung, `cloud_run.log`): Lauf als eigenstaendiger Prozess starten; ohne
  Checkpoint bedeutet ein Abbruch Neustart, nie ein Teilverdikt (DEC-53-Pruefung).

---

## 7. Beanstandungen

### Blockierend (formal; vor der Registrierung zu beheben, kein Code-/YAML-Eingriff)

**B-1 Nicht-Wiederholungs-Nachweis (C.1) fehlt.** PRD 5.3 verlangt ihn "woertlich in die Registrierung"
(`PRD_SCINANCE3.md:649`). Erst- und Zweitfassung trugen ihn (`hypothesis_registry.md:26`, `:145`), der Entwurf auch
(`herleitung_h28_h30_v3/DRITTFASSUNG_H28_H30_entwurf.md:652-659`); im Finaltext fehlt er (einziger Treffer
"Wiederholung" ist Text:146, Seed-Wiederholung). Da der Eintrag append-only eingefroren wird, ist der Mangel nach der
Registrierung nur per Neueintrag heilbar. Behebung: Absatz einfuegen, z. B. nach "Kill-Bedingungen": "A3 wiederholt
nicht D.7 (C-06/H-07/H-08): Breite K_t >= 345 statt N = 5 (H-07: max|z| = sqrt(N-1) = 2,0 < 2,5), Rauschboden
0,04858/0,04192 statt 0,50, Wochen- statt Stundenhorizont, explizite Bounce-, Drag- und Beta-Kontrolle,
survivorship-freies Union-Panel (DEC-72)."

**B-2 "DEC-89 E2 Nachtrag" ist zitiert, existiert aber nicht.** Text:409 (und `positive_control.py:104`,
`scripts/wp13_xsec.py:551`, Commit 849ec4a) beruft sich darauf; `decisions.md` endet mit DEC-89 (`:445-451`) ohne
Nachtrag. Die Aenderung (PC-Welt mit `null_scales` statt sigma_e = bounce_sigma_true und sigma_f aus der
Anteils-Inversion) aendert die in DEC-89 E2 "vorab fixierte" Kontrolle und ist damit eine Entscheidung ohne Eintrag
(`decisions.md:6`: "Keine Entscheidung ohne Eintrag"). Inhaltlich ist sie DEC-89-E2-treu ("kalibrierte
Faktorstruktur") und strenger, und es wurde noch keine Kontrolle gerechnet - also kein Torpfosten, nur fehlende
Akte. Behebung: Nachtrag an DEC-89 anhaengen (Anlass, Entscheidung `windows.<W>.null_scales` = v5e
`beta_control_method_study.{sigma_f, sigma_e_used}`, Begruendung, Rueckbauweg), vor oder mit der Registrierung.

### Nicht blockierend (im selben Textdurchgang korrigieren, wo moeglich)

- **N-1** Text:719 "Zu den Skalen siehe Abweichung Code/Text 1" verweist ins Leere (Text:407 "Verbleibend: keine").
  Ersetzen durch die Skalen selbst (null_scales 0,06685/0,05514 und 0,12064/0,10729).
- **N-2** Text:386-387 und Pflichtzeile 5 (Text:629): "Die Negativkontrolle ... prueft es [Gate (7)] zusaetzlich in
  Produktionsgroesse" trifft nicht zu. Die Negativwelt ist die kalibrierte stress-Null, driftfrei
  (`positive_control.py:76`), Faktoranteil 6,4 %/2,8 %, rho_f 0,092/0,083 - nicht das adversariale Fixture nach
  DEC-75 (3)/PRD 3.3.5 (dominanter, driftender Markt, rho 0,2, Beta U(0,5..2)). Gate (7) ist allein durch
  `test_dec87_t1_fm8_adversarial_beta_fixture_drops_where_the_raw_gate_would_fire` belegt. Formulierung auf
  "signalfreie Kontrolle in der stress-Null" zuruecknehmen.
- **N-3** Review v2 W-15 nicht adressiert: `ABGLEICH.md:46` "offen (gering)", Empfehlung "in v5e mitrechnen" nicht
  umgesetzt (`nulls.fit_ar1_per_symbol` `:278-322` ohne Korrektur). Wirkt nur ueber c_rho_bk auf IC_min. Als Etikett
  unter "Etiketten statt Kill" fuehren.
- **N-4** PRD 5.3 Metrik "als Nicht-Trivialitaets-Anker die Dezil-L/S-Bruttorendite" (`PRD_SCINANCE3.md:621`) wird
  weder gerechnet noch unter "Abweichungen vom PRD-Text" (Text:676-685) gefuehrt. Als Abweichung 7 eintragen
  (report-only, nicht gebaut).
- **N-5** PRD 3.3.3 verlangt effektives N mit gemessenem rho (`PRD_SCINANCE3.md:113`); Pflichtzeile 3 nennt nur
  N = 52/51. Aus c_rho_bk [abg.: W/c^2]: mom1 37,7/35,7, rev_gap 48,9/46,3. Ergaenzen.
- **N-6** Code-Stand pinnen: der Lauf schreibt `code.code_sha256` und `git_commit` (`run.py:1498-1527`), nach dem
  Registrierungs-Commit ist HEAD aber nicht mehr 849ec4a. Wert bei 849ec4a (sauberer Baum, 19 Dateien):
  `code_sha256 65852b4167ee0a1d27b2a60bbf25d370e51339bfbdee3b4e5fa7ce6b3dc2701d`. In den Lauf-Abschnitt aufnehmen;
  GL-Pruefung: Fingerprint-`code_sha256` = dieser Wert. Das deckt auch die drei Laufparameter, die aus Code-Defaults
  statt aus der YAML kommen (`n_reps_bootstrap`, `n_reps_permutation`, `n_sims_persistence`, `run.py` resolve_rules).
- **N-7** `run_full` validiert selbst nur nicht-strikt (`run.py:1253`); die Strenge kommt aus dem CLI-Preflight. Die
  Rueckfaelle aus Abschnitt 3 greifen nur bei direktem Aufruf, nicht im registrierten Befehl. Kein Lauf-Risiko.
- **N-8** Bounce-Kill bei nicht endlichem IC_bounce still uebersprungen (`gates.py:205`, Text:371 registriert). C.14
  wuerde Abbruch verlangen; unerreichbar (deterministische Fixture, Werte in Abschnitt 6).
- **N-9** Die Positivkontrolle sperrt den Lauf nur prozedural (Text:729). Auflage fuer den GL-Eintrag: rc 0,
  `result_sha256` und Pfad von `wp13_positive_control.json` vor dem Lauf nennen.
- **N-10** C.17: Der Lauf rechnet und berichtet den realen IC der gesperrten Charakteristik vol_beta gegen die
  Roh-Folgerendite (`beta_calibration_mean_ic`, `run.py:635`, DEC-75 (3)-Pflicht, Text:358) und das Lag-Profil
  (rev_gap Lag -1 = Reversal ohne Gap). Text:315 ("gesperrt: keine IC") ist dadurch missverstaendlich. Etikett:
  jede kuenftige Beta-/A3-V- oder Ein-Tages-Gap-Registrierung auf diesem Panel muss diese Zahlen als gesehen
  offenlegen.
- **N-11** Text:694-695: Ein abweichendes `--as-of` aendert den Union-Fingerprint nur bei anderem Jahr
  (`panel_load.py:108-109, 246`). Unschaedlich (as_of waehlt nur frozen/open-Pfade), Satz praezisieren.
- **N-12** Modul-Docstring `positive_control.py:28-31` beschreibt noch die alte Skalenableitung; Code (`:101-128`) und
  Test (`test_wp13_run.py:2568`) nutzen `null_scales`. Nur Doku, keine Aenderung (wuerde den Code-Hash aendern).

---

## 8. Bedingungen zur Aufhebung des VETO

1. B-1: Nicht-Wiederholungs-Nachweis in den Registry-Text.
2. B-2: Nachtrag zu DEC-89 (E2, `null_scales`) in `decisions.md`, vor oder mit der Registrierung.
3. Empfohlen im selben Durchgang: N-1, N-2, N-3, N-4, N-5, N-6, N-10 (Textaenderungen), N-9 (GL-Auflage).

Unveraendert bleiben duerfen: YAML (sha256 `bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299`),
Code 849ec4a, Vorlauf v5e. Nach Erfuellung von 1 und 2 ist der Eintrag registrierbar; die Positivkontrolle laeuft
dann allein und zuerst, der Lauf nur bei rc 0.
