# Review H-32 (adversarisch): Zweistufen-Design Pilot/Test fuer den beta-neutralen Querschnitts-IC

> Stand 2026-10-20. Zweiter, adversarischer Gutachter. Gegenstand: `state/herleitung_h32/` (ENTSCHEIDUNGSVORLAGEN.md =
> `[EV Z. n]`, ERSTFASSUNG_H32_entwurf.md = `[EF Z. n]`, power_h32.json = `[pj]`) und die Herleitungs-Skripte im
> Sitzungs-Scratchpad `h32_herleitung/`. Massstab: CLAUDE.md, PRD 3.3/5.3, DEC-51/52/53/58 E2/85/87/89/91-98 mit
> Nachtraegen, GL-032..034, `power_p1.py`, Drittfassung H-28..H-30 (Registry, YAML).
>
> **Ergebnisblindheit des Reviews.** Keine Datenrechnung: kein Panel geladen, weder Pilotfenster noch W1/W2 geoeffnet,
> keine reale IC, kein Outcome. Gelesen: v5e-Vorlauf-JSON (offen; sha256 `94d65559...5ae3b2` geprueft; nur Schluessel,
> Nuisance-Werte `factor_sd`, `mean_ic_draws_sd`, `mean_ic_draws_mean`, `n_ic_pooled`, K-Reihen), aus
> `wp7_20260921/decile_degeneration_weekly.csv` nur Kopfzeile und Spalten `week`, `n_symbols`; Akten-Texte. Stellen,
> die reale Werte der Persistenz-Null tragen, nur mit maskierten Ziffern gelesen (Vorzeichen und Stellenzahl sichtbar,
> siehe B-2). Nie geoeffnet: `*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`,
> `survivorship_bias_UNION_REAL.json`, `stress_rel.json`/`stress_abs.json`. Keine Datei mit Daten ab 2026-07-01.
> Synthetische Checks nur mit Repo-Code auf kuenstlichen Panels. Nichts committet. Eigene Skripte:
> Scratchpad `h32_review/` (`rv_power.py`, `rv_oc.py`, `rv_ceiling.py`, `rv_inject.py`, `rv_sector.py`, `rv_serule.py`,
> `rv_wc.py`, `rv_attn.py`).

---

## Urteil: ZUSTIMMUNG MIT AUFLAGEN (kein VETO)

Die Rechenarbeit ist korrekt und vollstaendig reproduziert (power_h32.json bitgleich nachgebaut). Das Design aendert
keine Fehlerrate des Tests; die Uebergaberegel ist eindeutig, mechanisch und monoton. Drei Punkte sind vor der Vorlage
an den Nutzer bzw. vor der Registrierung zwingend zu beheben (B-1 DEC-99-Wortlaut, B-2 C.17-Inventur, B-3 F-WEEK-BY
gegen Power-Zeile); acht weitere Auflagen (B-4..B-11) betreffen Etiketten, v6-Inhalte und den Bau. Keiner der Punkte
ist ein Fehler, der eine registrierte Zahl in Richtung Testbarkeit verschiebt; mehrere Erwartungs- und Etikettaussagen
sind zu guenstig (B-4, B-5, B-9, B-11).

## Kurzfassung

1. Zahlen reproduziert: `[pj]` bitgleich (sha256 `df17cafa...1bf3`); MDE80 S1 W1 0,0206/0,0237/0,0287/0,0195, W2 0,0165/0,0184/0,0221/0,0167; SE_P 0,0071; Pilot 2022-04-18..2024-06-17 (W_P 114, K 120/202/339); c aus 45/44 Simulationswochen - Bilanz-c_hat ist Artefakt; W2-Siegelbefund bestaetigt.
2. HOCH: DEC-99 behauptet "DEC-94 (1)-(9) unveraendert", kollidiert aber woertlich mit DEC-94 (5) (i) (Vorperiode "kein Mittel"; "versiegelt -> nur Null"), DEC-94 (6) (Zuordnung vor der Registrierung), DEC-51 (2), DEC-98 E1 (a). Ausdruecklich praezisieren (Wortlaut Abschnitt 6).
3. HOCH: C.17-Liste unvollstaendig: die Persistenz-Null W1/W2 (AR(1) je Symbol auf den Outcome-Renditen; Null-Mittel mom1/2/4 negativ, rev_gap positiv) steht in Registry und Drittfassungs-Entwurf - richtungstragend, nicht "vorzeichenfrei".
4. HOCH (programmweit geerbt): F-WEEK-BY ist bindend (m = 11 -> Max-p <= 0,0030); Power des endgueltigen PASS bei MDE80 nur 0,22..0,26 statt 0,80. Vor der Registrierung per DEC klaeren.
5. MITTEL: fm8 daempft ein beta-unabhaengiges Signal um ~25 % (Beta-Fenster t-7..t enthaelt die Formationswoche; synthetisch 0,75/0,76) -> Literatur-Erwartung zu guenstig (Uebergabe mom1 im Band 0,9..6,5 % statt 1,3..13,7 %).
6. MITTEL: Gewinnerfluch nur bei knapper Uebergabe (x_P = Schwelle + 0,25 SE_P -> selektionsbereinigt 0,004); Korrektur vorab fixierbar als Pflicht-Doppelausweis; Lesart B ist keine Bias-Korrektur.
7. MITTEL: harter Panel-Schnitt (Siegel), W2-Neukalibrierung, Pilot-Null-Mittel in v6, E[SE-Regel] in v6/PK, PK-Kriterium (a) tautologisch, Pilot-Neulauf/Pilot-Shopping regeln; Gabelungsbilanz korrigiert: 5 Testbarkeit / 4 Strenge / 3 Pflicht / 3 neutral.
8. Empfehlung: Lesart A mit Doppelausweis mu_sel, K = 4 mit BH-Doppelausweis 4/11, U0, DEC-99 im Wortlaut von Abschnitt 6; Bau +~200 Zeilen.

---

## 1. Was bestaetigt ist (keine Beanstandung)

| Pruefung | Ergebnis | Beleg |
|---|---|---|
| Reproduzierbarkeit | `h32_power.py` + `assemble.py` erneut gerechnet: `out_power.json` und `power_h32.json` bitgleich (sha256 `bcb0d91c...` bzw. `df17cafa...`) | Scratchpad `h32_review/rerun_*` |
| MDE80 je Variante/Fenster (eigener Code `rv_power.py` + `power_p1`) | S1: W1 0,0206 / 0,0237 / 0,0287 / 0,0195; W2 (w 50) 0,0165 / 0,0184 / 0,0221 / 0,0167. S2: W1 mom1 0,0192; S3: 0,0185, ohne Gutschrift 0,0177 (Auftragszahl 0,0176 = c 1, ohne Null-Mittel) | `[EV Z. 31-34, 251-255]` |
| Herkunft von c | v5e-Null simuliert das Fenster ohne Beta-Vorlauf: `beta_controlled_factor_null` simuliert `n_weeks` = 53/52 und schaetzt das Beta mit `min_weeks = 8` im simulierten Fenster (nulls.py Z. 1647-1655) -> `n_ic_pooled / n_reps` = 13.500/300 = **45** (W1), **44** (W2) fuer fm8, 52/51 fuer den Roh-IC. c_sim = 45 x draws_sd^2 / SD^2 = 0,99..1,11; Bilanz-Konvention mit 52 = 1,14..1,28 (Faktor 52/45 = 1,156) - **Artefakt bestaetigt** | v5e `beta_control_method_study`; `rv_power.py` |
| Herkunft des Null-Mittels | v5e `beta_control_recommended_high_rep.{stress, stress_drifting}.variants.<v>.mean_ic_draws_mean` (1.000 Rep.); in Richtung W1 mom1 +0,00076 / +0,00087 (driftfrei/Drift), rev_gap -0,00114 / -0,00126 -> keine Gutschrift. Per-Woche-Erwartung, von 45 vs. 52 Wochen nicht verzerrt | `[EV Z. 261-264]` |
| Pilot-SE | SD_P^2 = mean 1/(K_t - 1) (0,005043) + F2 (W1 mom1 0,00026) -> SD_P 0,0728; x sqrt(c 1,080) / sqrt(114) = **0,00709** (mom2 0,00753, mom4 0,00848, rev_gap 0,00703); Boden-SE 0,00660 bindet nicht | `[EV Z. 430-438]` |
| Pilotfenster | K_t: 2022-04-04 111, 2022-04-11 115, **2022-04-18 120**, danach nie < 117; erste Woche K >= 134 = 2022-05-23 (136). `slice_window` schliesst ISO-Wochenstarts ein (prelaunch.py Z. 92), `w_judged = n - 1` (nulls.py Z. 226-231): Slice 2022-04-18..2024-06-30 -> 115 Wochen, W_P 114, letzte Outcome-Woche 2024-06-24..30. Formationswoche 2024-06-24 haette das Outcome 2024-07-01..07 (erste W1-Woche) - Korrektur richtig. Frueher geht nicht (PRD 5.3 Kill (2), K_min 117), spaeter kostet nur Praezision; ein Embargo ist nicht noetig (unter H0 ist die Teststatistik von der Pilotauswahl unabhaengig, die geteilten Formationsrenditen gehen nur als Charakteristik in W1 ein) | `[EV Z. 146-165]`; WP-7-K-Reihe stimmt in allen 103 W1/W2-Wochen mit v5e ueberein (0 Abweichungen) |
| W2-Siegelbefund | v5e W2: `n_weeks` 52, `week_end` 2026-06-29 -> letzte Outcome-Woche 2026-06-29..07-05 im Blindbereich; Schnitt auf 2025-07-01..2026-06-28 (51 Wochen, w 50) richtig; W1 bleibt bindend | `[EV Z. 167-178]` |
| Uebergaberegel U | eindeutig (alle Eingaben vor dem Pilot eingefroren oder aus dem Pilot mechanisch), monoton in x_P (Verschiebung aendert SE_stat, SD_P, F2_real nicht) und in jeder SE; (iii) ist praktisch redundant, weil die Pilot-Quelle in (ii) MDE80* >= 2,4865 x 1,03 SE_P erzwingt | `[EF Z. 109-126]` |
| DEC-52 unter U | (ii) erzwingt Fenster-Power >= 0,80 in beiden Fenstern (Gutschrift je Fenster <= max m) -> stets C10 | `[EV Z. 333-336]` |
| K, z, Decke | z_max(4) = 1,0523, z_max(11) = 1,622, z_max(12) = 1,665 -> bindet erst ab K = 12 (DEC-94 (7)); Nebenbefund `_mean_of_max` roh vorzeichenbehaftet bestaetigt (nulls.py Z. 648-661) | `[EV Z. 199-206, 359-361]` |
| Ergebnisblindheit C-1/C-2 | `beta_calibration_mean_ic`/`lag_profile` in keiner Lauf-Ausgabe ausserhalb der Siegeldateien (Suche mit Ausschluss der Siegel); kein `--run` in der Git-Historie | `[EV Z. 71-72]` |

---

## 2. Befunde (nummeriert, Schweregrad, Beleg)

### B-1 (HOCH; Pruefpunkt 6) DEC-99-Wortlaut: "DEC-94 (1)-(9) unveraendert" ist unzutreffend

`[EV Z. 123]` sagt "(5) Unveraendert: ... DEC-94 (1)-(9)". Der Pilot kollidiert woertlich mit:
- **DEC-94 (5) (i)** (decisions.md Z. 506): die Vorperiode liefert "nur Streuung und Autokorrelation, **kein Mittel
  ausgegeben**, Waechter im Code" - der Pilot gibt genau das Mittel aus; und "**ist die Vorperioden-Statistik
  versiegelt, nur (ii)**" - die L-IC-Details 2021-03..2024-06 (deckt das Pilotfenster) liegen versiegelt in den
  L-Dateien v5c/v5d/v5e (DEC-75 (8), decisions.md Z. 282: "Siegel nur fuer L-IC-Details").
- **DEC-94 (6)** (Z. 507): "Die Zuordnung wird einmal **vor der Registrierung** festgestellt" - unter H-32 erst nach
  der Pilotstufe.
- **DEC-51 (2)**: "A-priori-Erwartung" - unter H-32 ein selektionsbehafteter Schaetzer (B-5).
- **DEC-98 E1 (a)** (Z. 553): "Prior aus der Literatur ... blockiert bis belegt".

Ohne ausdrueckliche Praezisierung ist das Etikett "Fehlerraten und Power-Ziel unveraendert" zwar fuer die Fehlerrate
richtig, die Aussage "DEC-94 unveraendert" aber falsch. **Auflage:** Wortlaut wie Abschnitt 6 (Absatz (6)).

### B-2 (HOCH; Pruefpunkt 5) C.17-Inventur unvollstaendig: Persistenz-Null W1/W2 gesehen

Die Persistenz-Null (DEC-74 (c)) fittet je Symbol ein AR(1) auf **die Wochenrenditen des Fensters** (nulls.py Z. 29-31,
278-323; prelaunch.py Z. 133), also auf genau die Renditen, die bei H-32 Outcome sind. Die Akte nennt daraus
richtungstragende Groessen:
- `state/hypothesis_registry.md` Z. 121 (Zweitfassung): Median-phi und Q25 je Fenster, Null-Mittel "fuer mom1/mom2/mom4
  negativ ... und fuer rev_gap positiv: die Wochen-Autokorrelation der Renditen wirkt GEGEN beide registrierten
  Richtungen"; Z. 178/241: q95 je Variante und Fenster;
- `herleitung_h28_h30_v3/DRITTFASSUNG_H28_H30_entwurf.md` Z. 168: dieselbe Aussage (Groessenordnung 0,0x);
- offen in v5e: `windows.<W>.noise_floor_and_threshold.persistence_null` (phi je Symbol, `mean_ic_draws_mean` je Variante).

Das ist der Eigen-Autokorrelationsanteil des Wochen-IC von mom1/rev_gap in W1/W2 - **keine** "vorzeichenfreie
Verwandte" (`[EV Z. 83-86]` ist insoweit falsch). Einschraenkungen: roh, nicht fm8; vermutlich zu grossen Teilen
Kendall-Bias der phi-Schaetzung (-1/T, Drittfassung ABGLEICH W-Punkt) und Vol-Gewichtung; die Richtung spricht
**gegen** H-32 (kein Testbarkeits-Vorteil). **Auflage:** als C-12 in Tabelle und Etikett C.17 (`[EF Z. 286-296]`)
aufnehmen; Befundsatz umformulieren: "keine reale IC gelesen; gesehen u. a. eine modellbasierte, richtungstragende
Eigen-Autokorrelations-Groesse der W1/W2-Renditen (gegen die Richtungen)". Offenlegung: Der Reviewer hat diese Werte
nur maskiert gesehen.

### B-3 (HOCH, programmweit geerbt; Pruefpunkte 3/7) F-WEEK-BY bindend gegen Power-Zeile 0,80

`[EF Z. 34, 196]`, Registry Z. 697 ("Bindend ist BY ueber F-WEEK am Wellenschluss"), DEC-74 (e) (Z. 253: p = Max-p,
>= 10.000 Permutationen). Mit m = 11 (F-XSEC1 7 mit p = 1, F-H32 4) verlangt BY fuer eine einzelne Ablehnung
Max-p <= 0,10 / (11 x 3,0199) = **0,0030** (z 2,747). Bei wahrem Effekt = MDE80* (S1) [`h32_review`, Inline-Rechnung]:

| | vorlaeufiger PASS (C10) | endgueltig nach BY, m = 11 | m = 4 |
|---|---:|---:|---:|
| mom1 | 0,74 | **0,26** | 0,48 |
| rev_gap | 0,72 | **0,22** | 0,44 |

Die "Power 0,80" der Pflichtzeile 1 gilt nur je Fenster und fuer das vorlaeufige Verdikt. Die Drittfassung hatte
dieselbe Struktur; der Widerspruch wurde nie aufgeloest (DEC-94 (7) regelt nur die Selektionsdecke). Ausserdem ist
offen, welche p-Groesse in BY eingeht (`[EF Z. 195]`: Block-Permutation 1.000, report-only; DEC-74 (e): >= 10.000).
**Auflage (Orchestrator, vor der Registrierung, programmweit, prospektiv):** entweder (a) Power-Zeile bis durch die
BY-Stufe (dann ist H-32 bei Pilot-Punkten unter ~0,028 GL-012) oder (b) DEC: "DEC-51-Power gilt fuer das Fenster-Gate;
F-WEEK-BY ist nachgelagerter Vorbehalt mit ausgewiesener Endpower" - in beiden Faellen p-Groesse und
Permutationszahl im YAML. Kein Veto, weil nicht H-32-spezifisch.

### B-4 (MITTEL; Pruefpunkte 4c/2) fm8 daempft ein beta-unabhaengiges Signal um ~25 %

Ursache: das PIT-Beta nutzt die Wochen t-7..t (characteristics.py Z. 244-245), enthaelt also die Formationswoche von
mom1 (und alle Formationswochen von mom2/mom4/rev_gap); die Querschnittsregression des Outcomes auf dieses Beta nimmt
einen Teil des Signals mit. Synthetisch (`rv_inject.py`, PK-Welt W1, 40 CRN-Paare, Injektion 0,0206): realisierter
Anteil **0,751 +- 0,006** (stress) / **0,764** (measured); mit um eine Woche verzoegertem Beta 0,913 / 0,924, dann aber
Null-Wochen-SD 0,080 statt 0,052 - das registrierte fm8 hat das bessere Signal/Rausch-Verhaeltnis, **kein
Designfehler**. Folgen:
- PK-Injektion auf realisierten Effekt kalibrieren: richtig (`[EV Z. 387-398]`); T1-positiv ebenso ("injiziert" ->
  "realisiert", `[EF Z. 254]`).
- Die Erwartungszahlen `[EV Z. 48-50, 338-340]` vergleichen das Literaturband (L/S- bzw. t/sqrt(N)-Wege, kein fm8)
  ungedaempft mit der fm8-MDE. Auf fm8-Skala (x 0,75, fuer mom1 gemessen; mom2/mom4 vermutlich staerker gedaempft)
  [`rv_attn.py`]: Uebergabe A bei 0,004..0,012: mom1 **0,9..6,5 %** (statt 1,3..13,7), rev_gap 0,6..4,8 %; Ficura-A*
  0,033: mom1 **76 %** (statt 97), mom4 40 % (statt 77). Richtung Testbarkeit in der Erwartung, nicht in der Fehlerrate.
- DROP-Zeile `[EF Z. 208, 312]`: MDE80 0,0206 auf fm8-Skala entspricht einem beta-unabhaengigen Signal von ~0,027 -
  Etikett.

### B-5 (MITTEL; Pruefpunkt 2) Gewinnerfluch der Lesart A: nur am Rand, vorab korrigierbar

Bedingt median-unverzerrter Schaetzer mu_sel (abgeschnittene Normalverteilung, Uebergabeschwelle c = 0,0206,
SE_P 0,00709, mom1) [`rv_wc.py`]:

| x_P | mu_sel | gemeinsame Testpower am Punkt / an mu_sel |
|---|---:|---|
| c + 0,25 SE_P | 0,0042 | 0,82 / 0,02 |
| c + 0,50 SE_P | 0,0166 | 0,88 / 0,50 |
| c + 1,00 SE_P | 0,0255 | 0,95 / 0,92 |
| c + 2,00 SE_P | 0,0346 | 1,00 / 1,00 |

MC der vollen Regel: E[x_P - m | Uebergabe] >= 0,021 fuer jeden wahren IC 0..0,015 [`rv_oc.py`]. Der Fluch wirkt nur
auf die berichtete Power (Regime stets C10, PK injiziert MDE80) - insoweit ist `[EV Z. 328-329]` richtig; "Power 0,80
am Prior" ist fuer knappe Uebergaben aber kosmetisch. "Ueber 4 Varianten" entsteht kein zusaetzlicher Max-Fluch
(jede Variante hat ihre eigene Schwelle; Abhaengigkeit mom1/mom2/mom4 nur in der Zahl der Uebergaben). **Korrektur,
vorab fixierbar:** Pflicht-Doppelausweis mu_sel (registrierte Formel: Loesung von P_mu(X >= x_P | X >= c_v) = 0,5,
X ~ N(mu, SE_P^2)) und der Power an mu_sel, Etikett an Pflichtzeile 1. Eine selektionsbereinigte
**Entscheidungs**regel ist nicht selbstkonsistent (jede Schwelle hat an ihrem Rand denselben Fluch); Lesart B ist
deshalb keine Bias-Korrektur, sondern nur eine strengere Operationscharakteristik.

### B-6 (MITTEL; Pruefpunkte 4a/5) Siegel-Umsetzung und W2-Kalibrierung

- Die Waechter PP4/P7 (`[EF Z. 160, 174]`) pruefen Outcome-Wochen. DEC-96 E3 (decisions.md Z. 530) verlangt
  ausdruecklich "Panel dort bei 2026-06-30 abschneiden"; der Lauf baut Charakteristiken und Betas auf dem vollen Panel
  (DEC-75 (8)), das bis as_of 2026-09-28 reicht (BTC-Renditen ab 2026-07-01 gingen in Beta-Schaetzungen ein, auch ohne
  Ausgabe). **Auflage:** harter Panel-Schnitt vor jeder Rechnung - Test und v6 <= 2026-06-28, Pilot-Modus <= 2024-06-30 -
  mit Test (Bauliste B-1..B-3).
- Der YAML-Entwurf uebernimmt fuer W2 `calibration` und `null_scales` aus v5e (`[EF Z. 436-437]`); diese enthalten die
  Woche 2026-06-29..07-05 (C-8) und gehoeren nicht zum registrierten Fenster. **Auflage:** v6 kalibriert W2 auf dem
  geschnittenen Fenster neu (DEC-87 (D) "Kalibrierung je Fenster") oder registriert die Abweichung mit Etikett.
- Stress-Listen (`[EF Z. 216]`) nur mit Datumsfilter <= 2026-06-28 laden, spaetere Eintraege nie ausgeben.

### B-7 (MITTEL; Pruefpunkte 1/7) Power-Zeile mit der SE-Regel des Gates (DEC-94 (3))

Die Lauf-SE ist max(Boden, SD/sqrt(W), SE_stat); ihr Erwartungswert liegt ueber der wahren SD des Fenstermittels
(synthetisch, `rv_serule.py`, 3.000 Reihen, Bootstrap 500): mom1 W1 x1,009, W2 x1,030; rev_gap x1,033 / x1,057; Power
bei MDE80 (mit wahrer SD) **0,77..0,80**. Solange S1 bindet (45-Wochen-SD, ~7..13 % konservativ), ist das gedeckt; nach
v6 nicht. **Auflage:** v6 friert je Fenster/Variante zusaetzlich E[SE nach Regel P-1 (4)] ein; Power-Zeile
T = z_krit x E[SE_Regel], SD = se_mean; PK-Injektionsziel entsprechend - sonst erwartete PK-Quote ~0,775 und
P(Quote < 0,734) ~8 % (Fehlalarm).

### B-8 (MITTEL; Pruefpunkt 2) Pilot-Null-Mittel ist UNBELEGT, nicht nur "minimal"

`[EV Z. 285-287, 472, 495]`: Proxy W1-stress (+0,00087). Das mechanische Null-Mittel haengt an Faktoranteil,
Autokorrelation und Drift des Fensters; fuer 2022-2024 liegt keine Kalibrierung vor. Ein hoeheres Pilot-Null-Mittel
erhoeht nur die Falsch-Uebergabe (nicht die Testfehlerrate), ist aber genau die Gabelung, die die Herleitung als
"Testbarkeit (minimal)" fuehrt. **Auflage (Strenge, billig, DEC-94 (5) (i)-konform):** v6 kalibriert die Pilotperiode
(sigma_f, rho_f, Faktoranteil - nur Streuung/Autokorrelation, Waechter "kein Mittel") und friert m_P (stress,
driftfrei/Drift) ein; Regel (ii) nutzt max(0, m_P, m_W1, m_W2).

### B-9 (MITTEL; Pruefpunkt 4b) Positivkontroll-Welt und 10-%-Regel

Die Sektorwirkung ist reproduziert (`rv_sector.py`, 40 Seeds: Wochen-SD 0,0515 -> 0,0615, **+19 %**; Herleitung +17,6 %).
Weder Welt noch Regel sind "falsch": die PRD-Sektorstaerke 0,375 sigma_e (positive_control.py Z. 71-73) ist eine
Fixture-Konstante ohne Messung, die 10-%-Regel DEC-94 (5) soll pruefen, ob die Power-Annahme realistisch ist. Der
Vorschlag `[EV Z. 391-404]` (sigma_g auf die bindende Power-SD) macht Kriterium (a) nahezu tautologisch; die
Realismuspruefung leistet dann allein F2_real aus dem Pilot. Akzeptabel unter drei Auflagen: (i) als Gabelung
**Richtung Testbarkeit** gegenueber der woertlichen DEC-89/PRD-Welt etikettieren (nicht "Strenge", `[EV Z. 497]`);
(ii) sigma_g an die gemessene Groesse F2_real kalibrieren (Null-SD als Untergrenze), nicht an die Power-SD selbst;
(iii) PK-Quote zusaetzlich in der PRD-Sektorwelt berichten (report-only). Zur 75-%-Injektion siehe B-4.

### B-10 (MITTEL; Pruefpunkt 6) Versteckte Gabelungen Richtung Testbarkeit

- **Pilot-Neulauf:** nicht geregelt. Auflage: genau ein Pilotlauf; Neulauf nur bei nachgewiesenem Code-/Datenfehler
  per DEC, beide Ergebnisse offengelegt, das korrigierte bindet in beide Richtungen (DEC-85-Muster).
- **Pilot-Shopping:** nach GL-012 (Pilot) koennte eine spaetere Hypothese korrelierte Statistiken (Universums-Variante,
  andere Formationslaenge, andere Neutralisierung) auf demselben Abschnitt erneut pilotieren oder direkt auf W1/W2
  registrieren. Auflage DEC-99: Pilotabschnitt programmweit verbraucht fuer korrelierte Statistiken; ein weiterer Pilot
  zaehlt K kumulativ; jede spaetere Registrierung einer solchen Statistik fuehrt das Pilot-Ergebnis als gesehen.
- Fensterende, K, U0: keine versteckte Gabelung (W2-Schnitt ist Pflicht, K ohne z-Wirkung, U0 ist der Default).

### B-11 (MITTEL; Pruefpunkt 6) Gabelungsbilanz zu guenstig klassifiziert

`[EV Z. 481-499]` zaehlt arithmetisch richtig (4 / 9 / 2), klassifiziert aber Pflichterfuellung als Strenge:
EV-2b, EV-2c (Datentrennung, DEC-96 E3) und EV-6 "MDE80-Quelle max(Null, Pilot)" (= DEC-94 (5) woertlich) sind keine
Wahl; EV-8 ist Testbarkeit (B-9); EV-7 "Persistenz-Null nicht rechnen" ist neutral (bindet nachweislich nicht - dieses
Wissen stammt aus B-2). **Korrigiert:** Testbarkeit 5 (EV-1, EV-3c, EV-6 Lesart, EV-6 Pilot-Null-Proxy, EV-8), echte
Strenge 4 (EV-3a, EV-5 S1 nur bis v6, EV-6 DEC-52-Ausschluss, EV-7 ohne Persistenz-Null), Pflicht 3, neutral 3 (EV-2a,
EV-3b, EV-4). Zusaetzlich gehoeren die vorab beschlossenen Hebel als Zeile in die Bilanz: P-1 (DEC-94, Schwelle 2,4865
-> 1,6449 SE) und fm8 primaer (DEC-98 E1 (a), Wochen-SD 0,13 -> 0,05) - zusammen MDE80 W1 mom1 0,060 (GL-032) -> 0,0206.

### B-12 (NIEDRIG; Pruefpunkt 4d) c_hat-Artefakt: Folgen fuer DEC-98/Bilanz

Bilanz Z. 118 und 189-197: fm8-c 1,11..1,27 -> richtig 1,00..1,11 (c = max(1, c_sim)); fm8-Dauern ~13..18 % kuerzer
(W1-stress mom1 22,8 -> ~19,4 Wochen); Roh-IC-c unberuehrt (52/51 Simulationswochen). Bilanz-Vorbehalt (a) Z. 200 und
DEC-98 E1 (a) Z. 553 ("Kalibrierungs-IC, Lag-Profil gesehen") sind zu korrigieren: nie berechnet (Abschnitt 1). DEC-98
E1 (a) "MDE80 ~0,018 / ~0,015" ist c = 1 ohne Null-Mittel (P-1-konform 0,0192..0,0206 / 0,0155..0,0165). Ein
DEC-98-Nachtrag genuegt; keine Gate-Wirkung.

### B-13 (NIEDRIG; Pruefpunkt 5) Pilotfenster blind - ja; Liste ergaenzen

Fuer den fm8-Mittelwert der Pilotperiode ist nichts gelesen: A1 hat dort A3-Faktorrenditen nur als Kovarianz genutzt
(Code-Waechter `_no_mean`, FEASIBILITY.md "Mittelwert ... weder ausgegeben noch gespeichert"), H-27 sah Marktvolatilitaet,
WP-7 eine Differenz (C-3), die Rohserie ist versiegelt. Das reicht. Ergaenzen: eigene Zeile "L-IC-Details 2021-03..
2024-06 berechnet und versiegelt (v5c/v5d/v5e, DEC-75 (8)) - deckt das Pilotfenster, nie geoeffnet"; A1-Funding-Bein-
Mittel der Pilotperiode implizit (DEC-93 Etikett (ii)); H-27-Nuisance 2021-03-24..2024-05-31 (Marktebene); A1-W1/W2-
Groessen (EW-Faktor-SD, Beta-Fehlanpassung, Funding-Spread, psi) - Funding/Marktebene, kein Preis-Querschnitt. C.18:
der Aera-Uebergang (Kompendium C.18: "D3-Uebergang endet ~Mitte 2024") liegt an der Grenze Pilot/W1 - das vorhandene
Etikett `[EF Z. 279-280]` ist richtig und gehoert auch in den DEC-99-Text ("Pilot ist Screening, nie Konfirmation").

### B-14 (NIEDRIG; Pruefpunkt 2) Operationscharakteristik

Analytisch exakt reproduziert (`rv_oc.py`, alle 36 Zellen der Tabelle `[EV Z. 310-320]`; 50-%-/80-%-Punkte A 0,0197/
0,0257, B 0,0288/0,0348 fuer mom1). MC der vollen Regel (zufaellige SE_P, F2_real, c_real, Bootstrap; synthetische
Gauss-AR(1)-Reihen) liegt leicht darunter, weil die Pilot-Quelle in ~30 % der Faelle bindet: mom1 IC 0: 0,10 %;
0,012: 12,5 %; 0,020: 44,7 % (analytisch 0,3 / 13,7 / 51,4 %). Mit v6-SE (~S2) analytisch bis 0,5 % bei IC 0, MC 0,25 %.
"Bei IC 0 hoechstens 0,3 %" haelt damit naeherungsweise (0,1..0,5 %); Etikett "S1-gestuetzt, v6 aendert die Zahlen".

### B-15 (NIEDRIG; Pruefpunkt 3) Selektionsdecke

Naeherung `[EV Z. 361]` 0,64..0,67 bestaetigt mit einem Charakteristik-Korrelationsmodell (mom1/mom2/mom4/rev_gap,
vorzeichenbereinigt, rev_gap negativ korreliert mit mom2/mom4) [`rv_ceiling.py`]: Decke W1 0,0086 / W2 0,0068,
Verhaeltnis zur kleinsten Schwelle (rev_gap) 0,66..0,68 / 0,62; obere Schranke unter Unabhaengigkeit 0,76 / 0,70. Kein
Kill erwartet. Hinweis fuer den Bau: eine Decke, vier Schwellen - die kleinste (rev_gap) bindet.

### B-16 (NIEDRIG; Pruefpunkt 6) DEC-99 (1) Wortlaut

"endet am juengsten ergebnisblind nutzbaren Tag" passt nicht zum Wochenraster (W2 endet 2026-06-28) -> "mit der
letzten vollstaendigen Cluster-Einheit vor dem Siegel"; "muss bestehen" fuer den DEC-52-Zweig praezisieren (Screen im
juengsten Fenster).

---

## 3. Pruefpunkte im Einzelnen (Zuordnung)

| Pruefpunkt | Ergebnis | Befunde |
|---|---|---|
| 1 Power-Zahlen, c, Null-Mittel, Pilot-SE, Fenster | korrekt; c-Artefakt bestaetigt; S1 nur bis v6 konservativ | Abschnitt 1, B-7, B-12 |
| 2 Uebergaberegel, OC, Lesart A/B, Gewinnerfluch | eindeutig/monoton; OC reproduziert; Fluch am Rand, Korrektur per Doppelausweis | B-5, B-8, B-14 |
| 3 K, BH, F-WEEK, Decke | konsistent mit DEC-51 (4)/DEC-94 (7); BY-Stufe gegen Power ungeklaert | B-3, B-15 |
| 4 Neue Befunde a-d | (a) richtig, Umsetzung schaerfen; (b) Welt und Regel je teilweise; (c) Daempfung ist Eigenschaft von fm8, nicht nur der PK; (d) DEC-98-Nachtrag | B-4, B-6, B-9, B-12 |
| 5 Ergebnisblindheit | W1/W2: keine reale IC gelesen, aber Persistenz-Null gesehen; Pilot blind | B-2, B-13 |
| 6 DEC-99, Gabelungen | Richtung ehrlich, Bezug zu DEC-94 (5)/(6) falsch; Neulauf/Shopping fehlen; Bilanz zu guenstig | B-1, B-10, B-11, B-16 |
| 7 Pflichtzeilen, Gate, Trio, Bauliste | vollstaendig und registrierbar nach Ergaenzungen | Abschnitt 4 |

---

## 4. Pflichtzeilen, Gate-Text, DEC-39-Trio, Bauliste (Pruefpunkt 7)

- **Zwoelf Pflichtzeilen** `[EF Z. 203-218]`: vollstaendig nach PRD 3.3. Ergaenzen: Zeile 1 - Endpower nach F-WEEK
  (B-3), mu_sel-Doppelausweis (B-5), Power mit E[SE-Regel] (B-7), W2-MDE80 auch im Text; Zeile 2 - fm8-Daempfung
  (B-4); Zeile 4 - BH-Doppelausweis Nenner 4 und 11 (kostet nichts, beseitigt die Gabelung EV-3c weitgehend); Zeile 10 -
  Datumsfilter der Stress-Listen (B-6).
- **Gate-Text** `[EF Z. 151-199]`: maschinell pruefbar, registrierbar. Ergaenzen: Panel-Schnitt als (PP0')/(P0'')
  (B-6); Regel (ii) mit m_P (B-8); Quelle der F-WEEK-p (B-3).
- **DEC-39-Trio** `[EF Z. 249-262]`: Klasse-W-adversarial (Beta-Proxy bei dominantem Markt) vorhanden, Pilot- und
  Siegel-Leck gut. T1-positiv auf realisierte Injektion umstellen (B-4); T1 "Panel-Schnitt" ergaenzen.
- **Bauliste** `[EV Z. 443-462]`, `[EF Z. 457-470]`: Umfang plausibel (~1.350 + ~1.050 Zeilen; PK-Laufzeit
  ~15-30 min ist bei ~0,04-0,1 s je synthetischer Fensterreplik realistisch). Zusaetzlich (~150-250 Zeilen):
  Panel-Schnitt + Test, W2-Neukalibrierung in v6, Pilot-Null m_P in v6 (~+30 min Cloud), E[SE-Regel] in v6,
  mu_sel-Funktion + T0, PK-Bericht in der PRD-Sektorwelt.

---

## 5. Empfehlung an den Orchestrator

1. **Urteil:** ZUSTIMMUNG MIT AUFLAGEN. Vorlage an den Nutzer erst mit dem DEC-99-Wortlaut unten (B-1, B-10, B-16);
   Registrierung erst nach A-1..A-9.
2. **EV-Lesarten:**
   - EV-1: DEC-99 im Wortlaut von Abschnitt 6 vorlegen.
   - EV-2: wie empfohlen (P-117 ab 2022-04-18, Ende 2024-06-17, W2 bis 2026-06-28) plus harter Panel-Schnitt (B-6).
   - EV-3: K = 4, H-30 ausgeschlossen, keine Zwei-Richtungen-Variante; BH-Doppelausweis 4/11.
   - EV-4: U0, Liquiditaets-Teiluniversen report-only.
   - EV-5: S1 bis v6; danach v6-se_mean plus E[SE-Regel] (B-7); Gutschrift nur positiv.
   - EV-6: **Lesart A** (Punkt) - mit Pflicht-Doppelausweis mu_sel und Power an mu_sel (B-5); Lesart B nicht, weil sie
     den Fluch nicht korrigiert, nur die Operationscharakteristik verschiebt; m = max(0, m_P, m_W1, m_W2) mit
     v6-Pilot-Null (B-8); (ii) wie empfohlen (DEC-52 ausgeschlossen).
   - EV-7: wie empfohlen; Persistenz-Null als "neutral, bindet nachweislich nicht" etikettieren.
   - EV-8: Vorschlag mit den drei Auflagen aus B-9.
3. **Vor der Registrierung zu aendern (Auflagen):**
   - A-1 DEC-99-Wortlaut (Abschnitt 6) nach Nutzer-Zustimmung beschliessen.
   - A-2 C.17-Tabelle und -Etikett um B-2 (Persistenz-Null) und B-13 ergaenzen; Befundsatz `[EV Z. 83-86]` korrigieren.
   - A-3 F-WEEK-BY gegen Power-Zeile per DEC klaeren (B-3), p-Groesse und Permutationszahl ins YAML.
   - A-4 Erwartungs- und DROP-Zeilen um die fm8-Daempfung ergaenzen (B-4); T1-positiv realisiert.
   - A-5 Panel-Schnitt vor jeder Rechnung, W2-Neukalibrierung, Stress-Listen-Filter (B-6).
   - A-6 v6 friert zusaetzlich E[SE-Regel] und m_P ein (B-7, B-8); PK-Injektionsziel mit E[SE-Regel].
   - A-7 PK-Welt: sigma_g an F2_real, PRD-Sektorwelt report-only, Etikett Testbarkeit (B-9).
   - A-8 Gabelungsbilanz korrigieren (B-11).
   - A-9 DEC-98-Nachtrag zu c_hat, Bilanz-Dauern und "Kalibrierungs-IC/Lag-Profil nie berechnet" (B-12).

---

## 6. DEC-99 - vorgeschlagener Wortlaut (Aenderungen gegen `[EV Z. 98-129]`)

> **DEC-99 - Programmregel REZENZ 3.0 und Pilot-Schaetzfenster (C.18 praezisiert) - prospektiv, Etikett "Lockerung
> (Richtung Testbarkeit), beschlossen nach GL-032..034 und DEC-98 Nachtrag 2".**
> (1) **Notwendige Bedingung REZENZ.** Jede Registrierung hat ein urteilstragendes Fenster, das mit der letzten
> vollstaendigen Cluster-Einheit vor dem juengsten ergebnisblind nutzbaren Tag endet (bei einem Blind-Siegel: vor dem
> Siegel); dieses Fenster muss bestehen (C.10: alle Fensterbedingungen; DEC-52-Zweig: der Screen im juengsten Fenster).
> (2) **Aeltere Daten** nur vorab registriert: (a) als Pilot-Schaetzfenster (Prior und Nuisance fuer eine vorab
> fixierte, mechanische Uebergaberegel; nie urteilstragend; Etikett "Pilot, nicht urteilstragend; Screening, nie
> Konfirmation (C.17/C.18)"; GL-012 (Pilot) ist kein Verdikt) oder (b) als zusaetzliches Urteilsfenster unter C.10,
> nie als Ersatz des juengsten.
> (3) **Bedingungen eines Pilot-Schaetzfensters:** K zaehlt alle Pilot-Varianten, nicht uebergebene mit p = 1 im festen
> BH-Nenner; Uebergaberegel und Prior-Lesart vor dem Oeffnen registriert; letzte Pilot-Outcome-Woche endet vor dem
> ersten Kalendertag des ersten urteilstragenden Fensters; **das Panel wird vor jeder Rechnung am letzten
> Pilot-Outcome-Tag abgeschnitten** (Code-Waechter mit Test); **genau ein Pilotlauf** - ein Neulauf nur bei
> nachgewiesenem Code- oder Datenfehler per DEC, beide Ergebnisse offengelegt, das korrigierte bindet in beide
> Richtungen; Pilot-Ergebnis mit sha256 festgehalten, bevor ein Testfenster gerechnet wird; **Pflicht-Doppelausweis**
> des selektionsbereinigten Pilot-Schaetzers (bedingt median-unverzerrt gegeben die registrierte Uebergabeschwelle)
> und der Power daran.
> (4) Ein Pilot-Schaetzfenster ist kein Zensus im Sinne von DEC-58 E2 (registrierte Stufe derselben Hypothese mit
> eigenem K).
> (5) **Verbrauch.** Nach dem Pilot ist der Pilotabschnitt programmweit fuer jede Statistik, die mit einer dort
> gerechneten korreliert (gleiche Charakteristik-Familie, andere Neutralisierung, Formationslaenge oder Universum),
> nicht mehr blind; ein weiterer Pilot auf demselben Abschnitt zaehlt alle frueheren Pilot-Varianten kumulativ in K;
> jede spaetere Registrierung einer solchen Statistik auf den Testfenstern fuehrt das Pilot-Ergebnis als gesehen.
> (6) **Verhaeltnis zu geltenden Regeln (nur fuer Registrierungen mit Pilot-Schaetzfenster, ausdruecklich):**
> DEC-94 (5) (i): das Pilot-Schaetzfenster gibt das Mittel aus; "ist die Vorperioden-Statistik versiegelt, nur (ii)"
> gilt fuer ein nach (2a) registriertes Pilotfenster nicht, die bestehenden Siegeldateien (L-IC-Details v5c/v5d/v5e,
> WP-7-Rohserie) bleiben geschlossen. DEC-94 (6): die Zuordnung wird nach der Pilotstufe und vor jedem Testfenster
> mechanisch nach der registrierten Uebergaberegel festgestellt, nie danach. DEC-51 (2): die "A-priori-Erwartung" ist
> der Pilot-Punkt der registrierten Lesart. DEC-98 E1 (a): der Pilot ersetzt den Literatur-Prior. **Unveraendert:**
> alpha 0,05 einseitig je Fenster, z_krit, Power-Ziel 0,80, C.10 / DEC-52 nach DEC-94 (6), DEC-94 (1)-(4) und (7)-(9),
> DEC-53, DEC-96 E3, DEC-74 (e). Der Pilot aendert keine Fehlerrate des Tests (getrennte Daten).
> - **Etikett (Pflicht):** "Lockerung (Richtung Testbarkeit) von C.18 'aeltere Historie rein deskriptiv' und
>   Praezisierung von DEC-94 (5) (i)/(6), DEC-51 (2), DEC-98 E1 (a) fuer Pilot-Registrierungen; beschlossen nach Kenntnis
>   von GL-032, GL-033, GL-034 und DEC-98 Nachtrag 2, vor jeder Pilot-Zahl. Fehlerraten und Power-Ziel unveraendert.
>   Nicht rueckwirkend."
> - **Rueckbauweg:** neue DEC; Registrierungen unter DEC-99 bleiben unter DEC-99.

---

## 7. Reproduktion (Scratchpad `h32_review/`, ausserhalb des Repos)

| Skript | Inhalt | Laufzeit |
|---|---|---|
| `rv_power.py` | Nuisance aus v5e, S1/S2/S3, c_sim/c_Bilanz, MDE80, Pilot-K und SE_P; schreibt `rv_nuis.json` | < 1 s |
| `rv_oc.py` | OC analytisch (Lesart A/B, S1 und v6~S2) und MC der vollen Regel | ~50 s |
| `rv_wc.py` | mu_sel und Power daran | < 1 s |
| `rv_attn.py` | Uebergabe im Literaturband auf fm8-Skala | < 1 s |
| `rv_ceiling.py` | vorzeichenbereinigte Decke K = 4 (Gauss-Naeherung) | ~5 s |
| `rv_inject.py` | fm8-Daempfung einer Injektion (stress/measured, Beta t-7..t vs. verzoegert) | ~6 s je Kalibrierung |
| `rv_sector.py` | Wochen-SD mit/ohne PRD-Sektorbloecke | ~10 s |
| `rv_serule.py` | E[SE-Regel P-1 (4)] gegen wahre SD des Mittels | ~3 min |

Herleitungs-Skripte `h32_power.py`/`assemble.py` unveraendert erneut ausgefuehrt: `power_h32.json` bitgleich.
