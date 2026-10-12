## H-28 / H-29 / H-30 - Drittfassung (ENTWURF 2026-10-12): Kohorte F-XSEC1 (A3), Klasse W, kapitalfrei

**Status:** ENTWURF der Herleitung, NICHT registriert. Registrieren darf nur der Orchestrator, nach adversarischem Review
und erst nach Erledigung der Vorbedingungen V1-V9 (Abschnitt 0). Grundlage ist der Vorlauf v5d
(`state/runs/wp13a_20261012_v5d/`, nach DEC-85 (v) bindend in beide Richtungen) mit der Methode `fm_neutral_8w` (DEC-86).
Fuer diesen Entwurf wurde keine reale Charakteristik-gegen-Folgerendite-Rechnung ausgefuehrt und keine Siegeldatei
geoeffnet: weder `*_L_window_sealed.json` noch `weekly_ic_series.csv` noch `ic_series_*_UNION_REAL.csv`. Das L-Fenster
bleibt versiegelt (sha256 `694402aa4dc7e06e1a0c12e9ea164027e38a66f9ec71fe7109a5f5c0c7de1a4a`, nur aus dem Lauf-Log
zitiert). Aenderungen nach der Registrierung nur als neuer Eintrag (append-only).

**Fundstellen-Kuerzel.**

| Kuerzel | Bedeutung |
|---|---|
| `[v5d <pfad>]` | `wp13a_prelaunch.json` (sha256 `b0cb4629f6ce8639e3de34689a6f00fe63bc93dc957a97163f8839e1ef5948d9`), JSON-Pfad unter `windows.<W>.` |
| `[v5d-md]` | `wp13a_prelaunch.md` (sha256 `1488b31781f0b89a699ea606aa655cbb185b75d5283f1c0e844ffec3a4b31cd1`) |
| `[log]` | `cloud_run.log` (v5d), bzw. `state/runs/wp13a_20261012/cloud_run.log` (v5c, Aufrufzeile) |
| `[abg.]` | in dieser Herleitung aus offenen Zahlen abgeleitet, Rechenweg angegeben |
| `[EV-x]` | `ENTSCHEIDUNGSVORLAGEN.md`, Vorlage x |
| `[sek]` | Sekundaerbeleg |
| UNBELEGT | keine Fundstelle, blockiert die abhaengige Groesse |

---

### 0. Vorbedingungen der Registrierung (aus der Herleitung; ohne sie ist der Eintrag nicht lauffaehig)

| Nr | Befund | Fundstelle | Abhilfe vor der Registrierung |
|---|---|---|---|
| V1 | Der v5d-Gewinnerlauf W1 (1.000 Rep.) lief mit der W2-Kalibrierung (rho_f 0,04158/0,08317, beta_sd 0,44648/0,58333 statt 0,04624/0,09248 bzw. 0,57367/0,77067). Ursache: `study` aus der Fensterschleife in `prelaunch.assemble_prelaunch_report`. Die DEC-86-Zahlen fuer W1 (Decke 0,0074/0,0079, Null-Mittel 0,00058/0,00124) sind damit nicht die W1-Null. Korrekt kalibriert betraegt die DEC-77-Marge in W1 stress nur +0,76 SE. | [v5d `W1.beta_control_recommended_high_rep.*.rho_f/beta_sd`]; [abg.] | Defekt beheben. **Vorlauf v5e** (outcome-frei) rechnet den W1-Gewinner neu: `fm_neutral_8w`, measured und stress, W1-Kalibrierung, 1.000 Rep., Seed 53. Ergebnis bindend in beide Richtungen (DEC-85 (v)); bei Nichtbestehen neue Orchestrator-DEC, kein stiller Methodenwechsel (DEC-86). |
| V2 | Eingefrorene Nullkonstanten passen nicht zum Lauf. Die Vorlage traegt v3-Werte (TS-8w, rho 0,2), `run_full` rechnet aber fm_neutral_8w nach; die +-10-%-Pruefung scheitert (-60..-97 %), d. h. KEIN Verdikt. Ausserdem liest der Code die Kalibrierung global aus W1, DEC-86 verlangt sie "je Fenster". | `run.run_full`, `assert_null_calibration`; `scripts/wp13_xsec.py cmd_emit_registered_template`; [EV-A], [EV-D] | Schema `windows.<W>.calibration`; `run_full` liest je Fenster; `--emit-registered-template` schreibt die fm8-stress-Zellen. Die Konstanten kommen aus v5e mit exakt der Lauf-Konfiguration. |
| V3 | H-30-Drag hat Tageseinheit (Wochen-Outcome und Kante) und falsches Vorzeichen (verdoppelt den Drag). Feasibility hochgerechnet ~2,8 > 0,5. | [EV-G]; [v5d-md] L-Zeile | DEC zur Praezisierung von DEC-75 (4); v5e rechnet die Feasibility auf L neu. Bei > 0,5: GL-012 fuer H-30 vor dem Lauf, K bleibt 7. |
| V4 | `gates.evaluate`: Bounce ist nur Etikett (DEC-75 (5): KEIN PASS) und nur W1; Liquiditaets-Etikett invertiert und nur W1. Zwei Tests pinnen das Fehlverhalten. | [EV-I] | Code und Tests auf Gate (4) dieses Entwurfs umstellen. |
| V5 | Gate (5) wird im Lauf nicht geprueft; Erreichbarkeit fuer vol_max und vol_beta UNBELEGT. | `run.run_full` (keine Gate-(5)-Rechnung); [v5d `gate5_reachability`] nur vol_rv | Outcome-frei in v5e messen; Gate (5) in `run_full`/`gates` einbauen. |
| V6 | Die Power-Zeile ohne Beta-Kontroll-Quantil ist unvollstaendig (mom4 W1 P = 0,57). Die Zuordnung C.10/DEC-52/GL-012 je Variante steht aus. | [EV-F] | Mechanische Zuordnung auf v5e-Zahlen, schriftlich vor der Registrierung. |
| V7 | DEC-53 und Tests: residualisierte Wochenserie wird nicht geschrieben, kein Generator-Fingerprint, kein KEIN-VERDIKT-Abbruch. T2 nur N = 2; T3, T5-Pin, T6, T7 fehlen. T1-End-to-End-Fixtures nutzen nicht `fm_neutral_8w`, und das Positiv-Fixture ist nicht das PRD-Fixture (0,06 + Beta + Sektoren). BH-Nenner = Zahl der Eintraege statt K = 7. | Abschnitte 5, 6 | Bau mit Tests, Abnahme durch den Orchestrator. |
| V8 | Beta-Kontroll-Quantil: DEC-76 E1 (b) verlangt "driftend", der Code rechnet driftfrei. | [EV-E] | Entscheidung; Empfehlung: das extremere von driftfrei und Drift 0,002. |
| V9 | Daten-Fingerprints: Die Union-Range- und `delisting_dates`-Hashes der Zweitfassung gehoeren zum Panel 2026-09-14/16 (`state/runs/wp7_20260921/`). v5d rechnete auf dem Harvest-Export 2026-09-28; dessen Union-Range-Hash und der `delisting_dates.json`-Hash sind UNBELEGT. | [log]; DEC-84 | In v5e erheben und in `data_fingerprints` eintragen; Lauf-Argumente pinnen (Abschnitt 10). |

Erst danach wird `registered_proposal.yaml` final erzeugt. Dessen sha256 wird hier eingetragen und ist der Wert fuer
`--registered-sha256`.

---

### 1. Gemeinsame Festlegungen der Kohorte (bindend fuer alle drei Hypothesen)

#### 1.1 Klasse, Kohorte, Varianten

| Feld | Wert | Fundstelle |
|---|---|---|
| Klasse | W, kapitalfrei | PRD 3.2, 5.3; DEC-73 E1 |
| Selektions-K | **7**; bleibt Nenner fuer Decke und BH, auch wenn Varianten nicht laufen | DEC-73 E1; DEC-74 (e) |
| Varianten | H-28: mom1, mom2, mom4 (positiv). H-29: rev_gap (negativ). H-30: vol_rv, vol_max, vol_beta (negativ) | PRD 5.3; DEC-51 (1) |
| Verdikt-Einheit | je Variante. Eine Hypothese ist PASS, wenn mindestens eine ihrer Varianten PASS ist; jede Variante wird einzeln berichtet | [EV-J] (Festlegung dieses Entwurfs) |
| Methode der Beta-Kontrolle | `fm_neutral_8w`, Beta-Fenster 8 Wochen | DEC-86; DEC-77 E2 |

#### 1.2 Panel, Universum, Datenbezug

- **Union-Panel:** `panel_1d` (877 Ueberlebende) + `panel_1d_delisted` (261 delistet), zusammen 1.138 Symbole,
  2.085 Tage, 299 ISO-Wochen 2020-12-28..2026-09-14 [log].
- **Bezug:** Harvest-Export `exports/scinance/scinance_panel_1d_2026-09-28.zip`, sha256
  `03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb` [log; DEC-84]. Nur exakte Schluessel lesen, Groesse
  und SHA256 pruefen, in ein frisches Sitzungsverzeichnis entpacken, nie ins Repo, nie unter `data/harvest`
  (UEBERGABE 2026-10-12 Abschnitt 1). Zugangsdaten nur aus `HARVEST_S3_*`.
- **Stichtag und Optionen:** as_of 2026-09-28; `--allow-partial` (69 Quellen-Luecken, DEC-66) wie in v5c/v5d [log v5c].
- **PIT-Maske:** Ein Symbol lebt ab >= 8 Wochen Historie bis zur Woche des Delisting-Datums; wiedergelistete Symbole
  bekommen eine eigene Spalte `<Symbol>#delisted` (DEC-72). Delisting-Datum = Announcement-Datum: Die Maske endet einige
  Tage vor dem Handelsende, das ist konservativ (DEC-74 Nachtrag (2), Etikett).
- **NO_HISTORY in den Urteilsfenstern:** W1 LITUSDT, MONUSDT, DATAUSDT; W2 SPCXUSDT [v5d `no_history_symbols`].
  Etikett "<= 1 % des Querschnitts fehlt".

#### 1.3 Fenster

| Fenster | Kalender | ISO-Wochen | geurteilt (W) | K min / Median / max (geurteilte Wochen) | Rolle |
|---|---|---:|---:|---|---|
| W1 | 2024-07-01..2025-06-30 | 53 (2024-07-01..2025-06-30) | **52** | 345 / 419 / 514 | urteilstragend |
| W2 | 2025-07-01..2026-06-30 | 52 (2025-07-07..2026-06-29) | **51** | 514 / 589 / 603 | urteilstragend |
| L | 2021-03-01..2024-06-30 | 174 | - | (versiegelt) | Aera-Profil, versiegelt, kein Vorzeichen-Argument |

Fundstellen: [v5d `noise_floor_and_threshold.floor.{k_series,w_judged,weeks}`]; W = Wochenzahl - 1, die letzte Woche hat
kein t+1 (DEC-75 (1), Review v2 W-10). Symbol-Wochen der geurteilten Wochen: W1 22.300, W2 29.126 [abg.: Summe k_series].
Die 11 Wochen 2026-07-01..2026-09-14 werden **nicht beurteilt und nach dem Verdikt nicht nachgereicht**.

#### 1.4 Cluster-Einheit, Metrik, Konvention

- **Cluster-Einheit:** Kalenderwoche (ISO, DEC-51 (3)). Die K_t Symbole einer Woche ergeben **einen** Spearman-Rank-IC
  (L-7: Panel-Mitglieder sind Beobachtungen, keine Hypothesen).
- **Urteilstragende Groesse je Variante und Fenster:** Mittel der Wochen-ICs ueber die geurteilten Wochen. Wochen mit
  K_t < 10 werden ausgelassen (`ic.weekly_ic_series`, `min_universe` 10). Ein degenerierter Querschnitt (Nullvarianz)
  liefert IC 0,0 (`pit_universe.spearman_rank_ic`, Etikett).
- **Outcome:** Folgewochen-Log-Rendite r_{t+1}, nicht ueberlappend (DEC-51 (5)). Das Querschnitts-Demeaning im Code ist
  fuer Spearman ein No-op (Review v2 B-9).
- **Survivorship-Konvention (urteilstragend):** `close_at_last`. Ein in t lebendes, in t+1 delistetes Symbol bleibt mit
  Folgerendite 0 im Querschnitt (PRD 4.1 DoD (4); DEC-74 (i)). Betroffene Symbol-Wochen: W1 80, W2 140
  [v5d `delisting.n_symbol_weeks_delisting`]. Die Konvention `drop` ist Pflicht-Sensitivitaet und wird nur berichtet.

#### 1.5 Charakteristik-Definitionen (je Woche t, PIT)

Alle Charakteristiken werden auf dem vollen Panel gebaut und erst danach auf die Fenster geschnitten (DEC-75 (8);
`run.build_all_characteristics_full_panel`).

| Variante | Definition | Code |
|---|---|---|
| mom1 / mom2 / mom4 | Summe der Wochen-Log-Renditen der Wochen t-n+1..t (n = 1/2/4) | `characteristics.momentum_characteristic` |
| rev_gap | Wochen-Log-Rendite der Woche t-1; Woche t ist das Gap, Outcome ist t+1 | `reversal_gap_characteristic` |
| vol_rv | SD (ddof 1) der Tages-Log-Renditen der Woche t, mindestens 2 Tage; **Tageseinheit** (V3) | `realized_vol_characteristic` |
| vol_max | groesste Tages-Log-Rendite der Woche t | `max_return_characteristic` |
| vol_beta | OLS-Beta zu BTCUSDT ueber die Wochen t-7..t, mindestens 4 Wochen mit Marktrendite | `beta_characteristic` (`trail_win` 8, `min_weeks` 4) |

#### 1.6 Outcome je Hypothese

- **H-28, H-29:** r_{t+1}.
- **H-30:** vol-gewichtetes, drag-bereinigtes r_{t+1}. Das Gewicht target/vol_rv[t] ist PIT (DEC-75 (4), Review v2 B-6
  geschlossen). Die **Drag-Definition ist offen** ([EV-G], V3). Die heutige Code-Fassung `(r_{t+1} - vol_rv[t]^2/2) x w`
  wird NICHT registriert.
- **Beta-Kontrolle fuer H-30:** Es wird dieselbe fm-Neutralisierung auf das H-30-Outcome angewandt
  (`run.h30_outcome_for_window`, im Code als "documented composition choice" gefuehrt). Die Komposition wird hiermit
  registriert und ist ausdruecklich zu bestaetigen.

#### 1.7 Beta-Kontrolle `fm_neutral_8w` und Kalibrierung der Null

- **Konstruktion:** Fuer jede Outcome-Woche t+1 eine Querschnitts-OLS (Achsenabschnitt und Steigung) von r_{t+1} auf das
  PIT-Beta zu BTCUSDT. Das Beta wird ueber die Wochen t-7..t aus `returns_est` geschaetzt (nicht handelnde
  Symbol-Wochen = NaN, DEC-85 (iii)) und braucht 8 gueltige Wochen. Gerechnet wird ueber die Symbole, die in t und t+1
  leben und endliches Beta und Outcome haben, mindestens 5. Das Residuum ersetzt r_{t+1}
  (`ic.fm_neutralize_outcome`, `ic.apply_beta_control`). Danach IC_res,W = Mittel-IC der Charakteristik gegen das Residuum.
- **Null fuer Decke und Quantil:** Faktor-Panel r_i = beta_i x f + e_i mit AR(1)-Faktor (rho_f), Marktspalte := Faktor
  (DEC-85 (i)), sigma_e idiosynkratisch (DEC-76 (e)), beta_sd bisektionell kalibriert (DEC-78 Nachtrag, DEC-81).
  Driftfrei: Entscheidung zur Drift offen, V8.

| Groesse | W1 | W2 | Fundstelle |
|---|---:|---:|---|
| sigma_f (BTC-Wochen-SD) | 0,06685 | 0,05514 | [v5d `beta_control_method_study.sigma_f`] |
| sigma_e (idiosynkratisch, Median) | 0,12064 | 0,10729 | [v5d `beta_control_method_study.sigma_e_used`] |
| rho_f measured / stress | 0,04624 / 0,09248 | 0,04158 / 0,08317 | [v5d `...calibrations.{measured,stress}.rho_f`] |
| Ziel-Faktoranteil measured / stress | 0,03211 / 0,06422 | 0,01389 / 0,02777 | [v5d `...target_factor_share`] |
| beta_sd kalibriert measured / stress | 0,57367 / 0,77067 | 0,44648 / 0,58333 | [v5d `...beta_sd_calibrated`] |
| beta_sd analytischer Erstwert (nur Bericht) | 0,32870 / 0,47276 | 0,23089 / 0,32886 | [v5d `...beta_sd_analytic_first_guess`] |
| Gegenprobe z (<= 3), Marktspalten-Baender | 0,63 / 0,02, beide ok | 1,90 / 1,24, beide ok | [v5d `...gegenprobe`]; DEC-81, DEC-85 (ii) |
| Coverage der Beta-Kontrolle in der Simulation | 0,889 | 0,877 | [v5d `...fm_neutral_8w.coverage_mean`]; real ~1 (Gate-Audit v5c, Etikett) |

#### 1.8 Urteilstragende Groessen

**(a) Rauschboden und Schwelle** (DEC-74 (a)/(b), DEC-75 (8)): `IC_min = 2,4865 x B x max(1, c_rho_bk) / sqrt(W)`.
B = E_t[1/sqrt(K_t-1)] ist die exakte Permutationsvarianz, signal-agnostisch und blind fuer Korrelationsstruktur
(Review v1). c_rho_bk ist der bias-korrigierte Wert aus der Persistenz-Null (+1/W je Lag) und wird auf >= 1 gedeckelt;
die Deckelung ist eine registrierte Abweichung von DEC-74 (b) nach DEC-75 (8).

| | W1 | W2 |
|---|---:|---:|
| B | 0,04858 | 0,04192 |
| W (geurteilt) | 52 | 51 |
| SE_Boden = B/sqrt(W) | 0,006737 | 0,005870 |

Fundstelle: [v5d `noise_floor_and_threshold.floor.e_floor`, `.w_judged`, `selection_ceiling_analytic.se_mean_ic`].

| Variante | IC_min_capped W1 | IC_min_capped W2 | c_rho_bk W1 / W2 | c_rho roh W1 / W2 | Persistenz-q95 in Richtung W1 / W2 (nur Bericht) |
|---|---:|---:|---|---|---|
| mom1 | **0,01966** | **0,01744** | 1,1739 / 1,1948 | 1,1098 / 1,1307 | -0,0064 / -0,0362 |
| mom2 | **0,01754** | **0,01558** | 1,0469 / 1,0677 | 0,9744 / 0,9953 | +0,0074 / -0,0094 |
| mom4 | **0,01729** | **0,01541** | 1,0325 / 1,0555 | 0,9589 / 0,9823 | +0,0081 / -0,0064 |
| rev_gap | **0,01727** | **0,01531** | 1,0309 / 1,0492 | 0,9573 / 0,9756 | +0,0063 / +0,0195 (q05) |
| vol_rv | **0,01694** | **0,01470** | 1,0110 / 1,0070 | 0,9358 / 0,9300 | -0,0112 / -0,0105 |
| vol_max | **0,01698** | **0,01464** | 1,0139 / 1,0028 | 0,9389 / 0,9254 | -0,0119 / -0,0101 |
| vol_beta | **0,01675** (roh 0,01657) | **0,01460** (roh 0,01354) | 0,9891 / 0,9276 | 0,9121 / 0,8434 | -0,0118 / -0,0105 |

Fundstelle: [v5d `noise_floor_and_threshold.ic_min_capped_per_variant`, `.ic_min_raw_per_variant`,
`.persistence_null.variants.<v>`]. Registriert werden IC_min_capped, also derselbe Wert in Registry und Artefakt
(Review v2 B-4). Die Mittel der Persistenz-Null liegen fuer mom1/2/4 bei -0,0036..-0,0469 und fuer rev_gap bei
+0,018/+0,030, also gegen die registrierten Richtungen; die Komponente ist report-only (DEC-75 (6)). In der
Persistenz-Null haben nicht lebende Symbole sigma = 0 (W1 550, W2 402 von 1.138; Etikett). Die AR(1)-Fits nutzen nur
lebende Wochen, aber die null-aufgefuellten `returns`. Die Wirkung ist klein (nur Luecken), in v5e wird auf `returns_est`
nachgerechnet (UEBERGABE 2026-10-12 Punkt 4).

**(b) Beta-Kontroll-Quantil q(v, W)** (DEC-76 E1 (b)): 99,36-%-Quantil in Hypothesenrichtung des Mittel-IC unter der
fm_neutral_8w-Null, Kalibrierung stress, driftfrei (Drift offen, V8).

| Variante | q W1 (vorlaeufig, 300 Rep.) | SD W1 | q W2 (1.000 Rep.) | SD W2 |
|---|---:|---:|---:|---:|
| mom1 | +0,02042 | 0,00799 | +0,01700 | 0,00636 |
| mom2 | +0,02291 | 0,00883 | +0,02029 | 0,00704 |
| mom4 | +0,02815 | 0,01044 | +0,02490 | 0,00832 |
| rev_gap | -0,01422 | 0,00749 | -0,01546 | 0,00662 |
| vol_rv | -0,02202 | 0,00734 | -0,01639 | 0,00623 |
| vol_max | -0,02202 | 0,00734 | -0,01639 | 0,00623 |
| vol_beta | -0,00567 | 0,00223 | -0,00483 | 0,00194 |

Fundstelle: W1 [v5d `W1.beta_control_method_study.calibrations.stress.methods.fm_neutral_8w.variants.<v>.quantile_one_sided`,
`mean_ic_draws_sd`]; W2 [v5d `W2.beta_control_recommended_high_rep.stress.variants.<v>`]. In der Simulation sind vol_rv
und vol_max identisch (Proxy |r|, Etikett; Gate-Audit v5c Punkt 3). Die W1-Werte werden durch v5e ersetzt (V1/V2): Ein
99,36-%-Quantil aus 300 Ziehungen hat ~10 % MC-Fehler [abg.: 0,253 x SD].

**(c) Selektionsdecke (GL-012-bindend)** [EV-A]: fm_neutral_8w, stress, Fensterkalibrierung, driftfrei, Mittel des
Maximums ueber K = 7, Seed 53.

| | W1 | W2 |
|---|---:|---:|
| **bindend** | **0,00810** (300 Rep., vorlaeufig, v5e 1.000 Rep. Pflicht) | **0,00685** (1.000 Rep.) |
| min IC_min / Decke | 2,07 | 2,13 |
| Bericht: fm8 measured | 0,00750 | 0,00637 |
| Bericht: roh stress / roh measured | 0,02777 / 0,01770 | 0,01740 / 0,01154 |
| Bericht: analytisch 1,3868 x SE_Boden (ohne 1/sqrt(2), [EV-C]) | 0,00934 | 0,00814 |
| Bericht: gemessen, reines Rauschen (300 Rep.) | 0,00919 | 0,00778 |
| historisch: TS-8w v3 (rho_f 0,2) | 0,04963 | 0,04993 |

**(d) Power-Zeile des vollstaendigen registrierten Tests** [EV-F]. Prior 0,03 [sek, R2 0.3C; PRD 5.3]. Die Spalte
"Prior 0,01" gilt nur fuer die IC_min-Komponente.

| Variante | P_ICmin W1 / W2 | P_beta W1 / W2 | MDE80 (voller Test) W1 / W2 | P bei Prior 0,01 W1 / W2 |
|---|---|---|---|---|
| mom1 | 0,90 / 0,96 | 0,89 / 0,98 | 0,0271 / 0,0233 | 0,11 / 0,14 |
| mom2 | 0,96 / 0,99 | **0,79** / 0,92 | **0,0303** / 0,0262 | 0,14 / 0,19 |
| mom4 | 0,97 / 0,99 | **0,57** / **0,73** | **0,0369** / **0,0319** | 0,15 / 0,19 |
| rev_gap | 0,97 / 0,99 | 0,96 / 0,99 | 0,0236 / 0,0210 | **0,15 / 0,19** (DEC-75 (8)) |
| vol_rv / vol_max | 0,97 / 0,99 | 0,86 / 0,99 | 0,0282 / 0,0216 | 0,15 / 0,21 |
| vol_beta | 0,98 / 1,00 | ~0 (strukturell, [EV-H]) | nicht erreichbar | - |

Rechenwege [abg.]:
- P_ICmin = Phi(Prior x 2,4865 / IC_min - 2,4865), wie in der Zweitfassung.
- P_beta = Phi((Prior - max(IC_min, |q|)) / SD), mit q und SD aus Tabelle (b).
- MDE80 = max(IC_min x (1 + 0,8416/2,4865), max(IC_min, |q|) + 0,8416 x SD).
- Die gemeinsame Power wird durch das Minimum genaehert (rohe und neutralisierte ICs sind bei einem Faktoranteil von
  3,2 %/1,4 % hoch korreliert); die exakte Gemeinsamkeit ist UNBELEGT.

**Zuordnungsregel (vorab, mechanisch, VOR der Registrierung auf v5e-Zahlen; Entwurfsstand = Prognose):**
- P_voll >= 0,80 in beiden Fenstern: C.10 hart.
- MDE80 > Prior in einem Fenster: GL-012-Feasibility-DROP der Variante (DEC-51 (2), K bleibt 7), ausser P_voll < 0,60
  UND der DEC-52-Zweig ist gebaut und getestet (DEC-52 (i)).
- rev_gap: C.10 hart gegen den registrierten Prior 0,03. Die DEC-52-Zulaessigkeit nach DEC-75 (8) ist festgestellt
  (0,15/0,19 < 0,60), wird aber nicht genutzt; Etikett "unterpowert gegen Lag-2-Prior 0,01".
- Prognose: mom4 wird GL-012-Fall, mom2 ist offen (W1 an der Grenze innerhalb des MC-Fehlers), die uebrigen gehen in
  C.10 hart. vol_beta siehe [EV-H], H-30 siehe V3.

#### 1.9 Gate-Text (1)-(7), geltende Fassung (DEC-75 (7))

Vor-Verdikt-Pruefungen fuer den ganzen Lauf, in dieser Reihenfolge:
- (P0) **Startsperre:** `--registered-sha256` = sha256 der registrierten YAML, sonst kein Lauf (DEC-75 E2).
- (P1) **Null-Kalibrierung:** Die nachgerechnete Decke und die Quantile q(v, W) liegen je innerhalb +-10 % der
  eingefrorenen Werte (`run.assert_null_calibration`), sonst KEIN VERDIKT fuer keine Hypothese (C.14).
- (P2) **GL-012-Decke:** Ist Decke_W >= IC_min(v, W) in einem Fenster, ist die Variante DROP mit Etikett GL-012, vor
  jeder PASS-Logik (DEC-75 (2)).

**Ein A3-Faktor (je Variante v) gilt als kapitalfrei BESTANDEN, wenn:**

**(1) Roher Mittel-IC, C.10 hart, in W1 UND W2 je einzeln:**
- (1a) sign(IC_W) = registrierte Richtung;
- (1b) |IC_W| >= 2,4865 x SE_W mit SE_W = max(B_W, SD(IC_t,W)) / sqrt(W_W) (DEC-75 (1); B_W und W_W aus 1.8 (a));
- (1c) die der Richtung zugewandte Grenze des einseitigen Moving-Block-Bootstrap-Intervalls liegt jenseits 0. Block 4,
  1.000 Ziehungen, Seed 53, Niveau 1 - 0,0064 = 0,9936, Perzentilmethode (DEC-75 (1); `run.moving_block_bootstrap_ci`);
- (1d) |IC_W| >= IC_min_capped(v, W) (Tabelle 1.8 (a)).
- Alpha-Semantik: Kritwert-Faktor 2,4865 je Fenster (Groesse 0,0064, gemeinsam 4,1e-5); MDE = IC_min (DEC-74 (d)).

**(2) Querschnitts-Permutations-Null und Persistenz-Null:**
- Der Permutationsboden B_W ist in (1b) die Untergrenze der SE.
- Report-only (DEC-75 (6); DEC-76 E1 (d)), nie bindend:
  - Block-Permutations-p (faktorerhaltend, Outcome-Wochen in Bloecken der Laenge 4 permutiert, 1.000, Seed 53, Max-p ueber W1/W2);
  - Persistenz-Null (AR(1), im Lauf 200 Simulationen, nur W1, `run.run_full`).

**(3) FDR:**
- BH alpha 0,10 ueber die K = 7 Varianten (Max-p) ist report-only (DEC-75 (6)).
- Bindend ist Benjamini-Yekutieli ueber F-WEEK am Wellenschluss (DEC-74 (e)). Bis dahin traegt jedes PASS das Etikett
  "vorlaeufig bis F-WEEK geschlossen".

**(3b) Beta-Kontrolle, zusaetzliche PASS-Bedingung, in W1 UND W2** (DEC-75 (3), DEC-76 E1 (b), DEC-77 E2, DEC-86):
- IC_res,W = Mittel-IC gegen das fm_neutral_8w-neutralisierte Outcome (1.7);
- (3b-i) gleiches Vorzeichen wie registriert;
- (3b-ii) |IC_res,W| >= IC_min_capped(v, W);
- (3b-iii) IC_res,W liegt jenseits q(v, W) in registrierter Richtung (Tabelle 1.8 (b), finale Werte aus v5e).
- Zusaetzlich wird der IC der reinen Beta-Charakteristik je Fenster als Kalibrierung berichtet.

**(4) H-29 (rev_gap) zusaetzlich:**
- (4a) Gap-Design: eine Woche (registrierte Abweichung von PRD 5.3, [EV-B]).
- (4b) Bounce: Ist |IC_bounce,W| >= |IC_W| in einem Fenster, gibt es KEIN PASS; Etikett "Artefakt Bounce" (DEC-75 (5)).
  - Fixture: Random Walk ohne Reversion, Schlusskurs springt je Woche zufaellig auf Bid oder Ask
    (`run.bounce_fixture_ic`, Groesse wie Fenster W).
  - Die Parameter spread 0,003 und sigma_true 0,03 sind Code-Konstanten, ihre Herleitung ist UNBELEGT.
  - Im Ein-Wochen-Gap ist der Bounce-IC strukturell ~0: Formation und Outcome teilen keinen Schlusskurs.
- (4c) Liquiditaet: Ist IC_ohne_D1,W > -0,5 x IC_min(rev_gap, W) in mindestens einem Fenster, gibt es das Etikett
  "Illiquiditaets-Artefakt" (H-16-Muster); das Verdikt steht, die Lesart ist eingeschraenkt (PRD 5.3 Gate (4); DEC-74 (f)).
  D1 ist das unterste Dezil des trailing-8-Wochen-Median-Turnovers (PIT).

**(5) H-30 zusaetzlich (je Variante und Fenster):**
- Median ueber die Wochen von Spearman(Rang der Charakteristik, Rang des trailing-8-Wochen-Median-Turnovers) < 0,60.
  Eine strukturelle Verletzung ist GL-012 vor dem Lauf, ohne Gate-Anpassung (DEC-74 (g)).
- Belegt: vol_rv W1 0,159 (Q25/Q75 0,105/0,227), W2 0,142 (0,105/0,164), L 0,115 [v5d `gate5_reachability`; v5d-md].
- vol_max und vol_beta: UNBELEGT (V5).

**(6) DEC-53-Artefakte** (Abschnitt 5) sind geschrieben und per T7 reproduzierbar, sonst KEIN VERDIKT.

**(7) Adversariales Beta-Fixture:** Das Gate faellt darauf durch. Das ist ein T1-Test mit `fm_neutral_8w`, der vor dem
Lauf gruen sein muss (Vorbedingung, keine Laufzeitgroesse).

**Verdikt je Variante:**
- PASS genau dann, wenn kein Vor-Verdikt-Kill greift und (1) und (3b) in beiden Fenstern sowie (4), (5) wo anwendbar,
  (6) und (7) erfuellt sind.
- Sonst DROP mit Etikett der verfehlten Komponente.
- (2) und (3) aendern das Verdikt nie, sie sind nur Etiketten.

**DEC-52-Zweig (nur fuer Varianten, deren Zuordnung VOR dem Lauf "DEC-52" lautet; Entwurfsstand: keine; Code fehlt):**
Ersetzt (1) und (3b) je Fenster durch:
- Vorzeichen registriert UND |IC_W| >= 0,5 x IC_min(v, W); Magnituden-Band [0,5x; 2,0x] laut PRD 3.5 (ii), Auslegung als
  Band oder Etikett im Review klaeren;
- Signifikanz ausschliesslich auf dem gepoolten Schaetzer (Wochen W1 und W2) mit fenster-geclustertem stationaerem
  Bootstrap, einseitig in registrierter Richtung, gepooltes alpha 0,01. Kritwert-Faktor 3,1680 (DEC-51-Zahlenwert;
  Semantik analog 2,4865, DEC-74 (d); im Review pruefen). Die gepoolte SE wird direkt gerechnet, kein Faktor 1/sqrt(2).
- Beta-Kontrolle analog: Vorzeichen und 0,5x je Fenster; gepoolter IC_res jenseits des 0,99-Quantils der gepoolten
  stress-Null, die v5e rechnen muss. Der Retro-Check liegt vor (DEC-52 Nachtrag).

#### 1.10 Abweichungen vom PRD-Text und Etiketten (registriert)

1. Reversal-Gap eine Woche statt ein Tag (Lag-2-Reversal; PRD-Ein-Tages-Design nicht getestet) [EV-B].
2. Faktor 1/sqrt(2) wird nicht verwendet; die Je-Fenster-Decke ist analytisch 1,3868 x SE [EV-C].
3. Deckelung max(1, c_rho_bk), Abweichung von DEC-74 (b) nach DEC-75 (8).
4. Persistenz-Null und Faktor-Null rechnen mit Wochen-Proxies (vol_rv und vol_max in der Simulation identisch).
   Die Null-Simulation hat keinen Vorlauf vor dem Fenster (Coverage 0,89/0,88).
5. Delisting-Datum = Announcement-Datum.
6. Schluesselname `res_quantile_drifting` = driftfreie stress-Null (bis V8).
7. H-30: Komposition Beta-Kontrolle x vol-gewichtetes Outcome (1.6); Drag-Definition offen (V3).
8. Oekonomisches Etikett mit zwei Kostenbasen (Abschnitt 2, Zeile 2).

---

### 2. Die zwoelf Pflichtzeilen (PRD 3.3.1-3.3.12)

| # | Zeile | Inhalt (Kohorte; Varianten-Details in Abschnitt 8) | Fundstelle |
|---|---|---|---|
| 1 | **Power** | alpha 0,05 einseitig in registrierter Richtung, Power 0,80, z 2,4865, Cluster Kalenderwoche, N = W 52/51. rho ist gemessen und gedeckelt, nie 0 (DEC-51 (3)): c_rho_bk aus der Persistenz-Null, die reale IC-Autokorrelation wird nach dem Lauf nur berichtet. Erwarteter Effekt 0,03 [sek]. Detektierbarer Effekt und Power je Variante siehe 1.8 (a)/(d); Zuordnungsregel 1.8 (d). | DEC-51; DEC-74 (b)/(d); DEC-75 (8); [abg.] |
| 2 | **Entscheidungsrelevanz** | PASS einer Variante: getrennte Tradability-Registrierung mit gemessener Dezil-Slippage (DEC-67 E4), kein Kapitalpfad vor `tradability3`. DROP aller drei: Klasse W auf Bybit-Perps im Wochenhorizont erschoepft (D.7 breit bestaetigt); fuer A3-R gilt das nur fuer das Lag-2-Design. Oekonomische Mindestmagnitude als ETIKETT (C.2): Portfolio IC 0,0101 (f 3,51, sigma_xs 1.018 bp, 18 bp), Einzelposition 0,062. Kostenbasen 18 bp (A3-M), 30 bp (A3-R), 4,5-7,5 bp (A3-V); die Taker-Wand 11 bp ist getrennt (B4 nicht ausgeloest). | PRD 5.3; DEC-74 (k); DEC-73 E4; Review v1 (zwei Kostenbasen) |
| 3 | **Cluster-Einheit** | Kalenderwoche; K_t Symbole bilden einen IC (L-7). Resampling: Moving Block, Block 4 Wochen. N_cluster = 52/51 geurteilte Wochen. | DEC-51 (3); DEC-75 (1) |
| 4 | **Selektions-Deflation** | K = 7. Bindende Decke fm8 stress 0,00810 / 0,00685 < min IC_min 0,01675 / 0,01460. Analytisch 0,00934 / 0,00814; gemessenes Rauschen 0,00919 / 0,00778. Kill: Decke >= IC_min -> GL-012 vor dem Verdikt. | DEC-75 (2); DEC-76 (c); [EV-A]; [EV-C] |
| 5 | **Adversariales Fixture** | Klasse W: Faktor mechanisch mit Markt-Beta korreliert, dominanter Marktfaktor, AR(1) rho 0,2, Drift, Beta 0,5..2,0; kein Gate darf feuern. Der Test muss auf `fm_neutral_8w` umgestellt werden (V7). H-29: Random Walk mit Bounce. H-30: Vol-Dispersion ohne Zusammenhang mit E[r_log] = mu - sigma^2/2 (FEHLT, V3/V7). | PRD 3.3.5; DEC-75 (3); `test_adversarial_beta_fixture_end_to_end_drop` |
| 6 | **Kostenmodell-Bindung** | `constants_hash`: n/a, kapitalfrei. Das Kostenkonstanten-Modul `tradability3` ist nicht gebaut; die Werkzeug-Entscheidung ist offen. PRD 3.4 nennt sie "DEC-59", im Log ist DEC-59 aber anders belegt (Welle-1-Vorfragen; Review v1), die Werkzeug-DEC hat also noch keine Nummer. Keine Kostengroesse in einer PASS-Bedingung (C.2). | PRD 3.3.6, 3.4; Review v1 |
| 7 | **Irreversibilitaets-Probe** | nachladbar: Tageskerzen und Funding oeffentlich (Bybit v5), Delisting-Announcements oeffentlich, Panel-Export im Harvest-Archiv. | PRD 3.3.7; DEC-84 |
| 8 | **Positivkontroll-Vorschaltung** | vorgeschaltet: ja (Abschnitt 3). Laufzeit des Laufs UNBELEGT (v5d-Vorlauf 2 h [log]). | PRD 3.3.8; Zustandsmaschine |
| 9 | **Kapital/Steuer/Venue** | Kapitalbasis n/a (kapitalfrei), Steuer n/a, Venue-Ereignis n/a. Zahler nach 2024: Delisting-Hazard der Kohorten 2023/24 ~50 % (Etikett). | PRD 3.3.9; Erstfassung |
| 10 | **Stress-Episode** | Abdeckungsnachweis, kein Filter (DEC-56 (1)). STRESS_REL: W1 22 Tage, W2 8 Tage. STRESS_ABS: W1 2, W2 1 (Abschnitt 4). | DEC-55/56 |
| 11 | **Ergebnis-Artefakte** | Abschnitt 5; ohne Artefakte KEIN VERDIKT. | DEC-53 |
| 12 | **Test-Pflichten** | T0-T7, Abschnitt 6. | PRD 3.3.12; DEC-75 (7) |

---

### 3. Positivkontroll-Vorschaltung

Ablauf nach der Zustandsmaschine, VOR dem realen Lauf, allein und mit identischem Code-Commit:
- `run.run_full` laeuft mit der registrierten YAML auf einem synthetischen Union-Panel in Produktionsgroesse
  (K-Reihe und W wie W1/W2).
- Positiv-Fixture nach PRD 5.3: injizierter Querschnitts-IC 0,06, unabhaengig vom Beta, auf einem Panel mit gemeinsamem
  BTC-Beta-Faktor (Marktspalte := Faktor) und Sektor-Bloecken. Alle injizierten Varianten muessen PASS haben.
- Null-Fixture (Charakteristik je Woche permutiert): kein PASS. Adversariales Beta-Fixture: kein PASS.
- Ausrichtungs-Fixture: IC exakt +1,000 / -1,000.
- Ergebnis wird als eigenes Artefakt geschrieben. Ein PASS der Positivkontrolle ist Vorbedingung des Laufs; sonst kein
  Lauf und neue DEC.

Heutiger Stand:
- Die End-to-End-Tests (`test_positive_fixture_end_to_end_pass`, `test_null_fixture_end_to_end_drop`,
  `test_adversarial_beta_fixture_end_to_end_drop`) laufen mit der alten TS-8w-Residualisierung und der
  v3-Drift-Null-Quantile.
- Das Positiv-Fixture nutzt IC 0,30 ohne Beta-Faktor; fuer die PRD-Definition reicht das nicht (V7).

---

### 4. Stress-Episoden (Abdeckungsnachweis, DEC-56 (1); kein Filter, kein Gate)

| Liste | Datei, sha256 | W1 | W2 |
|---|---|---|---|
| STRESS_REL (97,5-%-Perzentil der juengsten 24 Monate, BTC/ETH-Tagesvol, + 2026-08-19) | `state/runs/stress_rel.json` `6648a210c25fd3dd2f1e94d645fc4045bfcd99e3ea7ec8767d5c18edc45cb69e`; Kanon `eb83fe402b7b87243b1fc93691079a073461a42b6c17341502bc8c83678ca667` | 22 Tage (2024-08-05 .. 2025-04-09) | 8 Tage (2025-10-10 .. 2026-06-05) |
| STRESS_ABS (99-%-Perzentil der Gesamthistorie, + 2025-10-10, 2026-08-19) | `state/runs/stress_abs.json` `b8008257e963eaa2bd81882d1169503ca8f4c38d7860d65c357b8db3308fc11e` | 2 (2024-08-05, 2025-02-03) | 1 (2025-10-10) |

Fundstellen: [v5d `stress_rel`, `stress_abs`]; die Tageslisten stehen im Artefakt. Der Default-Pfad
`state/wp10_stress_canon/` in `scripts/wp13_xsec.py` existiert nicht. v5c/v5d riefen `--stress-rel state/runs/...` auf [log v5c].

---

### 5. Ergebnis-Artefakte (DEC-53, Pflicht; sonst KEIN VERDIKT)

Der Lauf schreibt nach `state/runs/wp13_run_<YYYYMMDD>/`, je mit sha256:

| # | Artefakt | Stand im Code |
|---|---|---|
| 1 | Rohe Wochen-IC-Serie je Variante und Fenster als CSV (Cluster-Serie, `close_at_last`) | vorhanden (`wp13_run_<H>_<W>_ic_weekly.csv`) |
| 2 | Residualisierte Wochen-IC-Serie (fm_neutral_8w) je Variante und Fenster als CSV; urteilstragend nach (3b) | **FEHLT** (V7) |
| 3 | `drop`-Sensitivitaet, Lag-Profil -1..+2, IC der Beta-Charakteristik, Liquiditaets- und Bounce-Werte je Fenster | im JSON, Liquiditaet/Bounce nur W1 (V4) |
| 4 | Bootstrap- und Permutations-Replikate ODER Seed 53 + Generator-Fingerprint (Bit-Generator, numpy-Version, sha256 der Ziehungen) | Seed ja, **Fingerprint FEHLT**; der Docstring verspricht eine Fingerprint-Datei, der Code schreibt keine (V7) |
| 5 | Null-Nachrechnung gegen die eingefrorenen Werte (`null_calibration`), verwendete Kalibrierung (`calibration_used_for_stress_null`) | vorhanden |
| 6 | K-Reihe und Wochenliste je Fenster | Wochenliste ja; K-Reihe im Payload je IC-Woche |
| 7 | L-Fenster getrennt und versiegelt (`wp13_run_L_window_sealed.json`), erst nach dem GL-Eintrag oeffnen | vorhanden |
| 8 | Loud fail "KEIN VERDIKT", wenn 1, 2 oder 4 fehlt | **FEHLT** (V7) |

---

### 6. Test-Pflichten T0-T7 (Abnahme durch den Orchestrator, Tests nie reduzieren)

| Stufe | Inhalt | vorhanden (Test-ID) | fehlt / umzustellen |
|---|---|---|---|
| T0 | reine Funktionen | `test_wp13_xsec.py`: `test_momentum_characteristic_trailing_sum`, `test_reversal_gap_characteristic_shifts_by_one_week`, `test_fm_neutralize_outcome_residuals_orthogonal_to_beta`, `test_w_judged_is_n_weeks_minus_one_and_floor_drops_final_week`, `test_c_rho_bias_correction_additive_plus_one_over_w`, ...; `test_wp13_run.py`: `test_se_of_mean_ic_uses_max_of_floor_and_sd`, `test_moving_block_bootstrap_ci_bound_direction` | Drag-Einheit und -Vorzeichen (V3) |
| T1 | positiv / null / adversarial + Zusatzfixtures | `test_positive_fixture_end_to_end_pass`, `test_null_fixture_end_to_end_drop`, `test_adversarial_beta_fixture_end_to_end_drop`, `test_alignment_fixture_perfect_and_mirrored_ic`, `test_lag_profile_only_lag_plus1_shows_the_effect`, `test_delisting_fixture_conventions_agree_on_signal_free_panel`, `test_near_threshold_hit_rate_about_half`, `test_survivorship_drawdown_fixture_is_deterministic_and_reports_ic_min_units` | alle End-to-End mit `fm_neutral_8w` und der registrierten Null; Positiv-Fixture nach PRD (0,06 + Beta + Sektoren); H-30-Fixture (Vol-Dispersion ohne Zusammenhang, log-Drag); H-29-Bounce mit "kein PASS" |
| T2 | Determinismus N >= 3 mit Fingerprint | `test_beta_controlled_factor_null_beta_sd_mode_determinism_same_seed` u. a. (N = 2) | N >= 3, sha256 der Payloads, `run_full` Ende-zu-Ende |
| T3 | Checkpoint-Round-Trip | keiner | FEHLT; entweder Checkpoint mit Test bauen oder per DEC begruenden, warum der Lauf ohne Checkpoint bleibt (DEC-75 (7) verlangt T3) |
| T4 | Gate-Arithmetik auf konserviertem Payload | `test_t4_gate_arithmetic_pure_on_conserved_payload`, `test_gl012_kill_forces_drop_before_pass_logic`, `test_c10_hard_one_window_failing_drops_whole_hypothesis`, `test_beta_control_quantile_failure_drops_even_with_ic_min_satisfied` | Bounce = kein PASS je Fenster; Liquiditaets-Etikett-Richtung je Fenster; Gate (5); Payload aus dem Positivkontroll-Lauf konservieren und pinnen |
| T5 | Konstanten-Pin | `constants_hash` n/a | Pin der registrierten YAML (sha256 + IC_min, q, Decke) gegen v5e (`test_ic_min_pins_registered_values`, in der Zweitfassung zitiert, existiert nicht) |
| T6 | Legacy-Import-Sperre | keiner fuer `wp13_xsec` gefunden | FEHLT: `wp13_xsec` und `scripts/wp13_xsec.py` importieren `_legacy_v1` nicht |
| T7 | Artefakt-Round-Trip | keiner | FEHLT: Artefakte laden, Gate-Schaetzer (Mittel-IC, Bootstrap-Grenze, IC_res) bitgleich reproduzieren; Fehlendes -> KEIN VERDIKT |
| Siegel | Vorlauf berechnet keine reale IC | `test_seal_prelaunch_never_calls_ic_with_real_returns`, `test_seal_prelaunch_report_json_no_real_ic_key` | auf v5e erweitern |
| Startsperre | sha256-Lock | `test_run_refuses_without_registered_sha256`, `test_run_refuses_with_wrong_registered_sha256` | - |
| Null-Kalibrierung | +-10 % | `test_run_full_raises_null_calibration_error_when_registered_has_drifted`, `test_run_full_raises_null_calibration_error_on_stale_per_variant_quantile` | Kalibrierung je Fenster (V2) |

Baseline der Suite: 1.992 passed / 3 failed (Legacy, sandbox-bedingt) / 9 skipped (UEBERGABE 2026-10-12).

---

### 7. Kill-Bedingungen (vorab; keine wird nach dem Lesen der IC-Serie geaendert)

| Nr | Bedingung | Folge | Stand |
|---|---|---|---|
| K1 | min K_t < 134 in einem Fenster | Kohorte nicht lauffaehig (PRD 5.3 Kill (2)) | W1 345, W2 514: nicht ausgeloest |
| K2 | Decke_W >= IC_min(v, W) | GL-012-DROP der Variante vor dem Verdikt (DEC-75 (2)) | 0,0081 / 0,00685 < IC_min: nicht ausgeloest (vorlaeufig W1) |
| K3 | Null-Nachrechnung ausserhalb +-10 % | KEIN VERDIKT fuer den ganzen Lauf (C.14) | Vorlage scheitert sicher; Vorschlag erst nach V1/V2 |
| K4 | H-30-Feasibility in Wocheneinheiten > 0,5 (Spread/Kante oder SE/Kante) | GL-012-DROP H-30 vor dem Lauf, K bleibt 7 (DEC-74 (h), DEC-75 (4)) | Prognose ~2,8: ausgeloest (V3) |
| K5 | Gate-(5)-Median >= 0,60 fuer eine H-30-Variante | GL-012 dieser Variante vor dem Lauf (DEC-74 (g)) | vol_rv nicht ausgeloest; vol_max/vol_beta offen |
| K6 | MDE80 des vollen Tests > Prior 0,03 | GL-012 der Variante (DEC-51 (2)), ausser DEC-52-Zweig nach 1.8 (d) | Prognose mom4 ausgeloest, mom2 offen |
| K7 | Variante strukturell durch die Beta-Kontrolle neutralisiert | GL-012 vorab, Etikett C.4 | vol_beta (Empfehlung [EV-H]) |
| K8 | DEC-53-Artefakte unvollstaendig | KEIN VERDIKT | Code-Bau V7 |
| K9 | Positivkontrolle besteht nicht | kein Lauf | offen |
| K10 | Startsperre (sha256) | kein Lauf | Code vorhanden |
| K11 | W1-Gewinnerlauf (v5e) verfehlt die DEC-77-Regel | keine Registrierung mit fm_neutral_8w; Orchestrator-DEC (DEC-85 (v)) | offen (V1) |

**Etiketten statt Kill:**
- Survivorship-Fixture-Verzerrung >= 0,5 IC_min: rev_gap W2 -0,58, mom1 W2 -0,44, W1 -0,19/-0,20, jeweils ein
  unkontrolliertes Panel in Hypothesenrichtung verzerrt; der Lauf nutzt das kontrollierte Union-Panel (DEC-76;
  [v5d `survivorship_fixture`]).
- Liquiditaet (4c), NO_HISTORY, Stress-Abdeckung.
- **NICHT in der Kill-Liste:** sigma_xs (B4, nur Etikett C.2).

---

### 8. Die drei Hypothesen

#### 8a. H-28 - A3-M Querschnitts-Momentum

**Hypothese:** Auf dem PIT-Union-Universum der Bybit-USDT-Perps gilt fuer mindestens eine Formationslaenge
(1, 2, 4 Wochen) in W1 und W2 jeweils:
- der mittlere woechentliche Spearman-Rank-IC zwischen Formationsrendite (bis Woche t) und Folgewochenrendite (t+1)
  ist positiv und >= IC_min der Variante;
- der IC gegen das fm_neutral_8w-beta-neutralisierte Outcome ist positiv, >= IC_min und liegt ueber dem registrierten
  Null-Quantil.

**Ertragsquelle / Zahler:** Prognose; Zahler sind spaet einsteigende Momentum-Chaser und Halter, die aus
Verlustpositionen getrieben werden (PRD 5.3).

```yaml
id: H-28
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Siehe Satz oben (mindestens eine Formationslaenge 1/2/4 Wochen; roh UND beta-neutralisiert; W1 UND W2)."
ertragsquelle: "Prognose; Zahler: spaet einsteigende Momentum-Chaser, aus Verlustpositionen getriebene Halter"
metric: "Mittel des woechentlichen Spearman-Rank-IC (Charakteristik_t vs. Folgewochen-Log-Rendite_t+1, close_at_last, min_universe 10) ueber die geurteilten Wochen je Fenster"
varianten: [mom1, mom2, mom4]
charakteristik: "Summe der Wochen-Log-Renditen t-n+1..t, n = 1/2/4 (characteristics.momentum_characteristic)"
richtung: positiv
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen: 53, geurteilt: 52, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, wochen: 52, geurteilt: 51, rolle: urteilstragend}
  - {id: L,  von: 2021-03-01, bis: 2024-06-30, wochen: 174, rolle: aera-profil, versiegelt: true}
fenster_regel: "C10_hart je Variante nach Zuordnungsregel 1.8 (d); Prognose mom4 GL-012 (DEC-51 (2)), mom2 offen bis v5e"
threshold:
  W1: {mom1: 0.01966, mom2: 0.01754, mom4: 0.01729}
  W2: {mom1: 0.01744, mom2: 0.01558, mom4: 0.01541}
  formel: "2.4865 * E_t[1/sqrt(K_t-1)] * max(1, c_rho_bk) / sqrt(W_geurteilt)"
  ref: "v5d windows.<W>.noise_floor_and_threshold.ic_min_capped_per_variant (sha256 b0cb4629f6ce8639e3de34689a6f00fe63bc93dc957a97163f8839e1ef5948d9); T5-Pin zu bauen (V7)"
structural_null:
  komponenten: [permutationsboden_als_SE_untergrenze, beta_kontrolle_fm_neutral_8w_PASS, selektionsdecke_faktor_null_GL012, block_permutation_p_report_only, persistenz_ar1_report_only]
  permutation_floor: {W1: 0.04858, W2: 0.04192, ref: "v5d windows.<W>.noise_floor_and_threshold.floor.e_floor"}
  beta_control_quantile: {W1: {mom1: 0.02042, mom2: 0.02291, mom4: 0.02815}, W2: {mom1: 0.01700, mom2: 0.02029, mom4: 0.02490}, kalibrierung: "stress, Fenster-eigen, driftfrei (V8)", status: "W1 vorlaeufig 300 Rep. (V1)", ref: "W1 beta_control_method_study.calibrations.stress.methods.fm_neutral_8w; W2 beta_control_recommended_high_rep.stress"}
  persistence_q95_report_only: {W1: {mom1: -0.0064, mom2: 0.0074, mom4: 0.0081}, W2: {mom1: -0.0362, mom2: -0.0094, mom4: -0.0064}}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 52, W2: 51, rho_ref: "c_rho_bk (Persistenz-Null, +1/W je Lag, gedeckelt >= 1): W1 1.1739/1.0469/1.0325, W2 1.1948/1.0677/1.0555"}
  a_priori_effekt: 0.03
  a_priori_ref: "R2 0.3C [sek], PRD 5.3"
  detectable_effect_full_test_mde80: {W1: {mom1: 0.0271, mom2: 0.0303, mom4: 0.0369}, W2: {mom1: 0.0233, mom2: 0.0262, mom4: 0.0319}}
  per_fenster_power_full_test: {W1: {mom1: 0.89, mom2: 0.79, mom4: 0.57}, W2: {mom1: 0.96, mom2: 0.92, mom4: 0.73}}
  zuordnungsregel: "1.8 (d), mechanisch auf v5e-Zahlen VOR der Registrierung"
  ref: "abgeleitet aus v5d (Formeln 1.8 (d))"
selection: {K: 7, ceiling_binding: {W1: 0.00810, W2: 0.00685, schaetzer: "Mittel des Maximums ueber 7 Varianten, fm_neutral_8w, stress, driftfrei, Seed 53", status_W1: "vorlaeufig, v5e 1000 Rep."}, ceiling_analytic: {W1: 0.00934, W2: 0.00814}, ceiling_noise_measured: {W1: 0.00919, W2: 0.00778}, regel: "Decke >= IC_min -> GL-012-DROP vor dem Verdikt"}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, kosten_bp_woche: 18, ref: "DEC-74 (k); PRD 5.3", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "Tradability-Registrierung mit gemessener Dezil-Slippage (DEC-67 E4); kein Kapitalpfad vor tradability3", on_drop: "A3-M auf Bybit-Perps im Wochenhorizont widerlegt (mit H-29/H-30: Klasse W erschoepft)"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", steuer: "n/a", venue_event: "n/a", zahler_post_2024: "Delisting-Hazard 2023/24 ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json sha256 6648a210c25fd3dd2f1e94d645fc4045bfcd99e3ea7ec8767d5c18edc45cb69e", rolle: abdeckungsnachweis, n_tage: {W1: 22, W2: 8}, stress_abs: {W1: 2, W2: 1}}
irreversibility_probe: {ergebnis: nachladbar, ref: "Bybit v5 oeffentlich; Harvest-Export; DEC-84"}
positive_control: {laufzeit_geschaetzt_h: "UNBELEGT", vorgeschaltet: true, ref: "Abschnitt 3"}
fixtures: {positive: "IC 0.06 + BTC-Beta-Faktor + Sektoren (zu bauen)", null: "Charakteristik je Woche permutiert", adversarial: "Beta-korreliert, AR(1) rho 0.2, Drift, Beta 0.5..2.0, mit fm_neutral_8w", alignment: "+1.000/-1.000", lag_profile: "-1..+2", delisting: "drop vs close_at_last", near_threshold: "Trefferquote 0.4-0.6", survivorship: "Drawdown -40 %/8 W, 30 % geloescht"}
artifacts:
  cluster_series_ref: "state/runs/wp13_run_<datum>/wp13_run_H-28_<v>_<W>_ic_weekly.csv + residualisierte Serie (V7), je sha256"
  bootstrap_replicates_ref: "Seed 53 + Generator-Fingerprint (V7)"
fdr_family: "F-XSEC1 (K = 7, BH 0.10 report-only, Max-p, Block-Permutation 1000)"
over_family: "F-WEEK (Benjamini-Yekutieli am Wellenschluss, bindend; Verdikt bis dahin vorlaeufig)"
feasibility_verdict: "bestanden fuer mom1; mom2/mom4 nach Zuordnungsregel (V6)"
constants_hash: "n/a - kapitalfrei; tradability3 nicht gebaut"
data_fingerprints: ["panel_export 03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb", "union_range_2026-09-28 UNBELEGT (V9)", "delisting_dates_2026-09-28 UNBELEGT (V9)", "prelaunch_v5d b0cb4629f6ce8639e3de34689a6f00fe63bc93dc957a97163f8839e1ef5948d9", "prelaunch_v5e <nach V1>", "registered_yaml <final>", "as_of 2026-09-28"]
stats3_version: "wp13_xsec e8fa088 (Vorlauf v5d); Lauf-Commit nach V2/V4/V5/V7 im GL-Eintrag"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e]
```

#### 8b. H-29 - A3-R Kurzfrist-Reversal im Gap-Design (Lag 2)

**Hypothese:** Auf dem PIT-Union-Universum ist der mittlere woechentliche Spearman-Rank-IC zwischen der Rendite der
Woche t-1 (Woche t ist das Gap) und der Folgewochenrendite t+1 in W1 und W2 jeweils:
- negativ und <= -IC_min;
- auch gegen das fm_neutral_8w-neutralisierte Outcome negativ, <= -IC_min und unter dem registrierten Null-Quantil;
- und vom Bounce-Fixture nicht erklaert.

**Ertragsquelle / Zahler:** Praemie fuer Liquiditaetsbereitstellung; Zahler sind durchgedrueckter Fluss und liquidierte
gehebelte Halter (PRD 5.3).

```yaml
id: H-29
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Siehe Satz oben (Gap eine Woche = Lag-2-Reversal; roh UND beta-neutralisiert; Bounce-Regel; W1 UND W2)."
ertragsquelle: "Praemie Liquiditaetsbereitstellung; Zahler: durchgedrueckter Fluss, liquidierte gehebelte Halter"
metric: "wie H-28"
varianten: [rev_gap]
charakteristik: "Wochen-Log-Rendite der Woche t-1; Woche t ist Gap (characteristics.reversal_gap_characteristic)"
richtung: negativ
windows: "wie H-28"
fenster_regel: "C10_hart gegen Prior 0.03 (P 0.97/0.99); DEC-52 nach DEC-75 (8) zulaessig festgestellt (P 0.15/0.19 bei Prior 0.01), nicht genutzt [EV-F]"
threshold:
  W1: {rev_gap: 0.01727}
  W2: {rev_gap: 0.01531}
  formel: "wie H-28"
  ref: "v5d windows.<W>.noise_floor_and_threshold.ic_min_capped_per_variant"
structural_null:
  komponenten: [permutationsboden_als_SE_untergrenze, beta_kontrolle_fm_neutral_8w_PASS, selektionsdecke_faktor_null_GL012, bounce_fixture_kein_PASS, liquiditaets_sensitivitaet_etikett, block_permutation_p_report_only, persistenz_ar1_report_only]
  permutation_floor: {W1: 0.04858, W2: 0.04192}
  beta_control_quantile: {W1: {rev_gap: -0.01422}, W2: {rev_gap: -0.01546}, status: "W1 vorlaeufig (V1)"}
  persistence_q05_report_only: {W1: {rev_gap: 0.0063}, W2: {rev_gap: 0.0195}}
  bounce: {regel: "|IC_bounce,W| >= |IC_W| in einem Fenster -> kein PASS (DEC-75 (5))", fixture: "run.bounce_fixture_ic, spread 0.003, sigma_true 0.03 (UNBELEGT), Seed 53", struktur: "Gap eine Woche -> kein gemeinsamer Schlusskurs, IC_bounce ~ 0"}
  liquiditaet: {regel: "IC_ohne_D1,W > -0.5 * IC_min(W) in einem Fenster -> Etikett Illiquiditaets-Artefakt", d1: "unterstes Dezil trailing-8-Wochen-Median-Turnover, PIT"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 52, W2: 51, rho_ref: "c_rho_bk W1 1.0309, W2 1.0492"}
  a_priori_effekt: 0.03
  a_priori_ref: "aus dem Ein-Tages-Design uebernommen (DEC-75 (8)); fuer Lag 2 UNBELEGT (Review v2 W-14) - Etikett"
  detectable_effect_full_test_mde80: {W1: 0.0236, W2: 0.0210}
  per_fenster_power_full_test: {W1: 0.96, W2: 0.99}
  power_prior_0_01: {W1: 0.15, W2: 0.19}
  zuordnungsregel: "1.8 (d)"
selection: "wie H-28"
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, kosten_bp_woche: 30, label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "wie H-28", on_drop: "Lag-2-Reversal widerlegt; PRD-Ein-Tages-Gap-Design NICHT getestet"}
capital_tax_venue: "wie H-28"
stress_episode: "wie H-28"
irreversibility_probe: "wie H-28"
positive_control: "wie H-28"
fixtures: {adversarial_zusatz: "Random Walk mit Bid-Ask-Bounce ohne Reversion: kein PASS", sonst: "wie H-28"}
artifacts: {cluster_series_ref: "wp13_run_H-29_rev_gap_<W>_ic_weekly.csv + residualisiert + Liquiditaet/Bounce je Fenster (V4/V7)", bootstrap_replicates_ref: "Seed 53 + Generator-Fingerprint"}
fdr_family: "wie H-28"
over_family: "wie H-28"
feasibility_verdict: bestanden
constants_hash: "n/a - kapitalfrei"
data_fingerprints: "wie H-28"
stats3_version: "wie H-28"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e]
```

#### 8c. H-30 - A3-V Vol-/MAX-/Beta-Anomalie (vol-gewichtet, drag-bereinigt) - LAUF GESPERRT bis V3

**Hypothese:** Auf dem PIT-Union-Universum gilt fuer mindestens eine Vol-Charakteristik (realisierte Vol, MAX-Tagesrendite,
8-Wochen-Beta zu BTC) in W1 und W2 jeweils:
- der mittlere woechentliche Spearman-Rank-IC gegen die vol-gewichtete, drag-bereinigte Folgewochenrendite ist negativ
  und <= -IC_min;
- auch nach fm_neutral_8w-Neutralisierung negativ, <= -IC_min und unter dem registrierten Null-Quantil;
- und die Charakteristik ist gegen die Turnover-Achse nicht redundant (Gate (5)).

**Ertragsquelle / Zahler:** Praemie gegen Lotterie-Nachfrage; Zahler sind Kaeufer hochvolatiler Perps. Die
BAB-Hebelbegruendung traegt in Krypto nicht (PRD 5.3).

**Sperre:**
- Die Drag-Definition ist offen: Tageseinheit und verdoppelnder Abzug (V3, [EV-G]).
- Feasibility in Wocheneinheiten hochgerechnet: Spread/Kante ~2,8 > 0,5 [abg.: 0,395 x 7; v5d-md L-Zeile;
  PRD 5.3 Tag x 7]. Bestaetigt v5e das, gilt GL-012 fuer H-30 vor dem Lauf (DEC-74 (h)); die drei Varianten werden
  dann nicht gerechnet, K bleibt 7.
- vol_beta ist unter fm_neutral_8w strukturell nicht bestehbar: Null-SD 0,0022/0,0019 gegen IC_min 0,0168/0,0146
  (K7, [EV-H]).

```yaml
id: H-30
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Siehe Satz oben (mindestens eine Vol-Charakteristik; roh UND beta-neutralisiert; Gate (5); W1 UND W2)."
ertragsquelle: "Praemie gegen Lotterie-Nachfrage; Zahler: Kaeufer hochvolatiler Perps"
metric: "Mittel des woechentlichen Spearman-Rank-IC (Charakteristik_t vs. vol-gewichtete, drag-bereinigte Folgewochen-Log-Rendite_t+1, close_at_last), je Fenster"
varianten: [vol_rv, vol_max, vol_beta]
charakteristik: {vol_rv: "SD der Tages-Log-Renditen der Woche t (Tageseinheit)", vol_max: "max Tages-Log-Rendite der Woche t", vol_beta: "OLS-Beta zu BTCUSDT t-7..t, min 4 Wochen"}
outcome: "o_t+1 = (r_t+1 [+/-] sigma_w,t^2/2) * target/sigma_w,t; Einheit und Vorzeichen OFFEN (V3, EV-G); Gewicht PIT aus Woche t (DEC-75 (4))"
richtung: negativ
windows: "wie H-28"
fenster_regel: "C10_hart nach 1.8 (d), nur falls V3 bestanden"
threshold:
  W1: {vol_rv: 0.01694, vol_max: 0.01698, vol_beta: 0.01675}
  W2: {vol_rv: 0.01470, vol_max: 0.01464, vol_beta: 0.01460}
  formel: "wie H-28"
  ref: "v5d windows.<W>.noise_floor_and_threshold.ic_min_capped_per_variant"
structural_null:
  komponenten: [permutationsboden_als_SE_untergrenze, beta_kontrolle_fm_neutral_8w_PASS, selektionsdecke_faktor_null_GL012, vol_drag_feasibility_L, gate5_turnover_redundanz, block_permutation_p_report_only, persistenz_ar1_report_only]
  beta_control_quantile: {W1: {vol_rv: -0.02202, vol_max: -0.02202, vol_beta: -0.00567}, W2: {vol_rv: -0.01639, vol_max: -0.01639, vol_beta: -0.00483}, status: "W1 vorlaeufig; vol_rv = vol_max in der Simulation (Proxy |r|)"}
  persistence_q95_report_only: {W1: {vol_rv: -0.0112, vol_max: -0.0119, vol_beta: -0.0118}, W2: {vol_rv: -0.0105, vol_max: -0.0101, vol_beta: -0.0105}}
  vol_drag_feasibility_L: {kante_bp_woche: 91.42, spread_d10_d1_ueber_kante_tageseinheit: 0.395, se_ueber_kante_tageseinheit: 0.025, hochrechnung_wocheneinheit: {spread: 2.8, se: 0.18}, grenze: 0.5, status: "Neuberechnung v5e (V3)", ref: "v5d-md Fenster L; prelaunch.h30_feasibility"}
  gate5: {grenze: 0.60, vol_rv: {W1: 0.159, W2: 0.142}, vol_max: UNBELEGT, vol_beta: UNBELEGT}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 52, W2: 51, rho_ref: "c_rho_bk W1 1.0110/1.0139/1.0 (gedeckelt), W2 1.0070/1.0028/1.0 (gedeckelt)"}
  a_priori_effekt: 0.03
  a_priori_ref: "R2 0.3C [sek]"
  detectable_effect_full_test_mde80: {W1: {vol_rv: 0.0282, vol_max: 0.0282, vol_beta: "nicht erreichbar"}, W2: {vol_rv: 0.0216, vol_max: 0.0216, vol_beta: "nicht erreichbar"}}
  per_fenster_power_full_test: {W1: {vol_rv: 0.86, vol_max: 0.86, vol_beta: "~0"}, W2: {vol_rv: 0.99, vol_max: 0.99, vol_beta: "~0"}}
  zuordnungsregel: "1.8 (d); vorbehaltlich V3 (Outcome-Definition aendert die Null)"
selection: "wie H-28"
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, kosten_bp_woche: "4.5-7.5", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "wie H-28", on_drop: "A3-V widerlegt; bei GL-012 (V3): A3-V auf diesem Panel nicht schaetzbar (Drag dominiert), kein Verdikt ueber die Praemie"}
capital_tax_venue: "wie H-28"
stress_episode: "wie H-28"
irreversibility_probe: "wie H-28"
positive_control: "wie H-28"
fixtures: {adversarial_zusatz: "identische Vol-Dispersion ohne Zusammenhang, E[r_log] = mu - sigma^2/2 (FEHLT, V3/V7)", sonst: "wie H-28"}
artifacts: "wie H-28"
fdr_family: "wie H-28"
over_family: "wie H-28"
feasibility_verdict: "OFFEN - Prognose verfehlt (V3); vol_beta strukturell (K7)"
constants_hash: "n/a - kapitalfrei"
data_fingerprints: "wie H-28"
stats3_version: "wie H-28"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e]
```

---

### 9. Entscheidungsrelevanz und Nicht-Wiederholungs-Nachweis (C.1)

- **PASS einer Variante:** getrennte Tradability-Registrierung mit gemessener Dezil-Slippage (DEC-67 E4); kein
  Kapitalpfad vor `tradability3`. Jedes PASS ist "vorlaeufig bis F-WEEK geschlossen".
- **DROP aller drei:** Klasse W auf Bybit-Perps im Wochenhorizont ist erschoepft (D.7 auf breiter Basis bestaetigt). Fuer
  A3-R gilt das nur im Lag-2-Design; ein GL-012 von H-30 ist kein Verdikt ueber die Lotterie-Praemie.
- **Nicht-Wiederholung:** Breite K >= 345 statt N = 5. Der Rauschboden sinkt von 0,50 auf 0,049/0,042. Wochenhorizont
  statt Stunden; explizite Bounce-, Drag- und Beta-Kontrolle; survivorship-freies Union-Panel (DEC-72).

---

### 10. Lauf (erst nach Registrierung, Positivkontrolle und allen Vorbedingungen) und Rueckbauweg

**Lauf-Befehl** (Cloud, DEC-83; Panel aus dem Harvest-Export in ein frisches Sitzungsverzeichnis):

```
python scripts/wp13_xsec.py --run --registered <registrierte YAML> --registered-sha256 <sha256 aus diesem Eintrag> \
  --panel-base <dir>/panel_1d --delisted-base <dir>/panel_1d_delisted \
  --start-year 2021 --end-year 2026 --as-of 2026-09-28 --convention close_at_last --allow-partial \
  --out scinance3-impl/state/runs/wp13_run_<YYYYMMDD>
```

- Die Argumente sind identisch zum Vorlauf [log v5c]; sonst weicht die Null-Nachrechnung ab (K3).
- Danach Gate-Check gegen genau diesen Text, GL-032, L-Siegel erst nach dem GL-Eintrag.

**Rueckbauweg:** Die Registry ist append-only; ein Widerruf ist ein neuer Eintrag. Erst-, Zweit- und Drittfassung bleiben
stehen. Code-Aenderungen V1-V7 sind additiv und ersetzend mit Tests; alte Artefakte (v3..v5d) bleiben. Die registrierte
YAML ist per sha256 gepinnt. Der Entwurf selbst hat im Repo nichts geaendert.

**Vorschlags-YAML** (Scratchpad, nicht registriert):
- `registered_proposal.yaml`, sha256 `df36f45eb4e52880a74c9cdda0d14a8e42284595ce18841be1f47f22a590801c`; statisch
  geprueft gegen `run.load_registered_yaml`, beta_control, Kalibrierungsblock, rules, 7 Hypothesen-Eintraege. W1-Werte
  sind vorlaeufig.
- Vorlage `registered_template.yaml`, sha256 `c2c7dff2b592647610b1a9a01a87eca7ad745afe2a074a2840224a44026b6a94`:
  scheitert an `beta_control.method` leer, an der +-10-%-Pruefung (-60..-97 %) und an GL-012 in allen Varianten.
