# Entscheidungsvorlagen H-32: Zweistufen-Design fuer den beta-neutralen Querschnitts-IC (Pilot auf der Vorperiode, Test auf W1/W2)

> **STAND NACH REVIEW (2026-10-20):** DEC-99 ist beschlossen (`state/decisions.md`, Wortlaut nach Review Abschnitt 6 plus
> (7) F-WEEK-Zaehlregel, (8) W2-Ende 2026-06-28, (9) H-26 gesperrt). Die Review-Auflagen fuer den Herleitungstext sind
> eingearbeitet (`REVIEW_H32.md` Abschnitt 5): **A-2** C.17 um Persistenz-Null und B-13 ergaenzt, Befundsatz korrigiert
> (Abschnitt 1); **A-3** F-WEEK nach DEC-99 (7), Endpower und Doppelausweis m = 11, p-Groesse (EV-3c, Abschnitt 2);
> **A-4** fm8-Daempfung ~25 % in Erwartungs- und DROP-Zeilen (EV-6, EV-7); **A-6/A-7** v6 friert E[SE-Regel] und m_P
> ein, Regel (ii) mit max(0, m_P, m_W1, m_W2), Kontrollwelt an F2_real (EV-5, EV-6, EV-8); **A-8** Gabelungsbilanz
> 5/4/3/3 (Abschnitt 5); **B-6** harter Panel-Schnitt, W2-Neukalibrierung, Stress-Listen-Filter (EV-2c). Ausserdem aus
> dem beschlossenen DEC-99 (3)/(5): genau ein Pilotlauf, Pflicht-Doppelausweis mu_sel, Verbrauch des Pilotabschnitts.
> Nicht Teil dieses Textes: A-1 (DEC-99, erledigt), A-5 als Bau, A-9 (DEC-98-Nachtrag, Orchestrator).
>
> ENTWURF der Herleitung. Nichts hier ist registriert; registrieren darf nur der Orchestrator. Die Registrierung setzt
> den Bau, den Vorlauf v6 (ohne Outcome) und die Abnahme voraus (DEC-99 "Erste Anwendung").
>
> **Ergebnisblindheit.** Keine Datenrechnung: weder das Pilotfenster noch W1/W2 wurden geoeffnet, kein Panel geladen,
> keine reale IC berechnet, kein Outcome. Jede Power-, MDE-, Zuordnungs- und Uebergabe-Zahl stammt aus
> `src/bybit_edge/research/power_p1.py` mit Nuisance aus der Akte. Nicht geoeffnet: alle Siegeldateien
> (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`), `survivorship_bias_UNION_REAL.json`,
> `stress_rel.json`/`stress_abs.json` (koennen Tage ab 2026-07-01 tragen), keine Datei mit Daten ab 2026-07-01
> (Blind-Siegel DEC-96 E3). Aus `feasibility.json` (A1) wurden nur Datums-/K-Metadaten der Pilotbasis gelesen, keine
> Steigungen. Synthetische Checks (Repo-Code auf einem kuenstlichen Panel, kein Realdatum): EV-8.
>
> **Fundstellen-Kuerzel.**
> - `[v5e <pfad>]` = `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json` (sha256 `94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2`), JSON-Pfad;
> - `[wp7k]` = `state/runs/wp7_20260921/decile_degeneration_weekly.csv` (sha256 `7c6119afe3bbaa862acd5f65bfcb3e53ffb8244e7056aba7f5a56df3a0fac9e5`), nur Spalten `week`, `n_symbols`;
>   die Reihe stimmt in allen 103 urteilstragenden Wochen von W1/W2 exakt mit der v5e-K_t-Reihe ueberein (0 Abweichungen) und ist damit die A3-Lebend-Maske;
> - `[pj <pfad>]` = `state/herleitung_h32/power_h32.json` (sha256 `f0d6e6d9c55e0a9326ab5b32988eb86bbd0c62ef283b0c3101a4889a402a56a3`, zweimal bitgleich erzeugt; alle Zahlen der Erstfassung `df17cafa...` unveraendert, neu: Bloecke `power.f_week_by_end_power` und `fm8_daempfung`);
> - `[Review B-n]` = `state/herleitung_h32/REVIEW_H32.md`; `[abg.]` = hier abgeleitet; `[sek]` Sekundaerbeleg; UNBELEGT blockiert.
>
> **Notation.** `fm8` = `fm_neutral_8w`. "In Richtung" heisst vorzeichenbereinigt (positiv fuer mom1/mom2/mom4,
> negativ fuer rev_gap). `m_W` = Mittel des fm8-Fenstermittels unter der stress-Null in Richtung (das extremere aus
> driftfrei/Drift 0,002); `m_P` dasselbe fuer die Pilotperiode (v6). S1/S2/S3 = Lesarten der Test-SE (EV-5).
> z_krit = 1,6449, MDE-Faktor = 2,4865 (DEC-94 (1)).

---

## 0. Befund in Kuerze

1. **Die Testseite traegt.** Mit fm8 als Primaerstatistik und bindender SE (S1, stress) ist die MDE80 des schwaecheren
   Testfensters W1: mom1 **0,0206**, mom2 0,0237, mom4 0,0287, rev_gap **0,0195** (W2: 0,0165 / 0,0184 / 0,0221 / 0,0167)
   `[pj power.power_table.<v>.S1_draws_sd_bindend.thresholds]`. Die Auftragszahl "MDE80 ~0,0176" rechnet ohne c und ohne
   Null-Mittel (Richtung Testbarkeit). Nach v6 traegt die Power-Zeile E[SE-Regel] (A-6, [Review B-7]).
2. **Endpower nach F-WEEK (DEC-99 (7)).** m = Zahl der tatsaechlich getesteten Eintraege. Bei wahrem Effekt = MDE80
   ist die Endpower nach BY fuer mom1 0,74 (m = 1) / 0,67 (2) / 0,55 (3) / 0,48 (4); alte Zaehlung m = 11 (report-only)
   0,26 `[pj power.f_week_by_end_power]`. Die Zuordnung bleibt je Fenster (DEC-94 (6), DEC-99 (6)); die Endpower ist
   Pflicht-Ausweis in Zeile 1.
3. **Der Pilot ist weniger praezise als angenommen.** K_t 120/202/339 (W1 345/419/514), Boden 0,0705 (W1 0,0486).
   Erwartete Pilot-SE mom1 **0,0071** (nicht 0,0047), rev_gap 0,0070, mom2 0,0075, mom4 0,0085 `[pj power.pilot_precision]`.
4. **Fenster:** Pilot-Formationswochen 2022-04-18..2024-06-17 (W_P 114; 2022-04-04 hat K 111; die Woche 2024-06-24 haette
   ihr Outcome in W1). W2 endet 2026-06-28 (DEC-99 (8), w_judged 50). **Harter Panel-Schnitt vor jeder Rechnung**:
   Test und v6 <= 2026-06-28, Pilot <= 2024-06-30; W2 in v6 auf dem geschnittenen Fenster neu kalibriert (B-6).
5. **Uebergaberegel U (Lesart A, Pilot-Punkt):** Vorzeichen richtig UND x_P - max(0, m_P, m_W1, m_W2) >= MDE80 des
   schwaecheren Testfensters (Schwelle mit E[SE-Regel], Streuung mit se_mean, jeweils max aus v6-Null und K-bereinigter
   Pilot-Streuung) UND t >= 2. 50-%-Uebergabe bei wahrem fm8-IC 0,0197 (mom1) / 0,0207 (rev_gap) (S1-gestuetzt, v6
   aendert die Zahlen); bei IC 0 0,1..0,5 % [Review B-14]. Pflicht-Doppelausweis mu_sel (DEC-99 (3)).
6. **Erwartung unter dem Literaturband, fm8-gedaempft (A-4):** fm8 daempft ein beta-unabhaengiges Signal um ~25 %
   (realisiert/injiziert 0,754 synthetisch; [Review B-4] 0,751/0,764). Weg-B-Literaturwerte 0,004..0,012 ergeben dann
   Uebergabe mom1 0,9..6,6 %, rev_gap 0,6..4,9 %, mom2 0,5..3,9 %, mom4 0,3..1,8 % (Lesart A); Ficura-A* 0,033 mom1 77 %,
   mom4 41 % `[pj fm8_daempfung]`. Wahrscheinlichster Ausgang bleibt GL-012 (Pilot); W1/W2 bleiben dann ungeoeffnet.
7. **K = 4** (mom1, mom2, mom4, rev_gap), BH-Nenner 4 (fest, p = 1 ohne Uebergabe); H-30 strukturell ausgeschlossen; U0.
8. **DEC-52 ist unter der Uebergaberegel tot** (Bedingung (ii) erzwingt C10).
9. **Positivkontrolle:** Kontrollwelt mit sigma_g an der im Pilot gemessenen Zusatzstreuung F2_real (Null-SD als
   Untergrenze); PRD-Sektorwelt (+17,6 % Wochen-SD) nur report-only; Gabelung Richtung Testbarkeit gegenueber der
   woertlichen DEC-89-Welt (A-7). Injektion auf den realisierten fm8-Effekt kalibriert, Ziel mit E[SE-Regel].
10. **Gabelungsbilanz (A-8):** 5 Testbarkeit, 4 Strenge, 3 Pflicht, 3 neutral.

---

## 1. Ergebnisblindheit an der Akte geprueft (Grundlage des Etiketts C.17)

**Frage:** Sind W1/W2 und das Pilotfenster fuer die fm8-Statistik der vier Varianten blind?

| # | Groesse | Status | Fundstelle |
|---|---|---|---|
| C-1 | Beta-Kalibrierungs-IC (`beta_calibration_mean_ic`, realer Mittel-IC der Beta-Charakteristik) | **nie berechnet**: nur im Lauf-Modus vorgesehen; kein `wp13_run*`-Ordner, kein Treffer in `state/runs` (Siegeldateien ausgenommen), kein Lauf-Commit in der Git-Historie | `run.variant_window_payload`; DEC-92 |
| C-2 | Lag-Profil -1..+2 | **nie berechnet** (wie C-1) | `run.lag_profile` |
| C-3 | Survivorship-Differenz real: IC_union - IC_survivors des **rohen 4-Wochen-Momentum-IC**, 271 Wochen (ganze Historie inkl. Pilot und W1/W2) | **gesehen**: +0,0033 [-0,0076; +0,0132]; Differenz, kein Niveau, nicht fm8 | `WELLE1_BEFUND_TEIL6_2026-09-21.md`, `wp7_report.md` Z. 15 |
| C-4 | WP-7-Rohserie des 4-Wochen-Momentum-IC (alle Wochen inkl. Pilot, W1, W2) | **berechnet und versiegelt, nie gelesen** - "keine reale IC je berechnet" (STAND 2026-10-18) ist woertlich ungenau: berechnet ja, gelesen nein | `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv` (nicht geoeffnet) |
| C-5 | Survivorship-Fixture (synthetisch) | gesehen, kein Outcome: mom1 -0,198/-0,438, rev_gap -0,189/-0,579 IC_min-Einheiten | `[v5e windows.<W>.survivorship_fixture]` |
| C-6 | Streuungen der Fenster (real, ohne Charakteristik-Outcome-Verknuepfung) | gesehen: sigma_f 0,0669/0,0551, rho_f 0,046/0,042, sigma_e 0,121/0,107, Median-Symbol-Vol 0,172/0,133, sigma_xs 9,85 %, Boden 0,0486/0,0419, K-Reihen | `[v5e windows.<W>.factor_calibration]`, DEC-67 |
| C-7 | Faktoranteil = Median des Querschnitts-R^2 der Wochenrendite auf das PIT-Beta (W1 3,2 %, W2 1,4 %) | gesehen; vorzeichenfreie Verwandte von C-1 (R^2 statt IC), das Vorzeichen des Beta-IC ist nicht gesehen | `[v5e windows.<W>.factor_calibration.factor_share]` |
| C-8 | v5e-W2-Kalibrierung enthaelt die Woche 2026-06-29..07-05 (5 Tage im Blindbereich), berechnet 2026-10-12 vor DEC-96 | offengelegt; v6 kalibriert W2 auf dem geschnittenen Fenster neu (B-6) | v5e W2 = 52 Wochen 2025-07-07..2026-06-29 |
| C-9 | Pilotperiode: A1 hat A3-Faktorrenditen (Dezil-L/S auf mom1/mom2/mom4/rev_gap) 2022-04..2024-06 berechnet; gespeichert nur R^2 (0,063..0,068), Steigungen, Residual-Streuung, **kein Mittel** (Code-Waechter `_no_mean`) | existiert; Steigungswerte in dieser Herleitung nicht gelesen | `herleitung_a1/FEASIBILITY.md` 3.2, `feasibility.json ...a3_factor_regression` |
| C-10 | Literaturband (beta-neutraler Wochen-IC, **nicht fm8-gedaempft**): Weg B 0,004..0,012; Ficura-A* 0,033 (Large and Liquid) / -0,064 (Small or Illiquid); LTW FM > 1 Mio -0,011..-0,019; "Momentum grosser Coins seit Anfang 2021 nicht profitabel" (Ficura); Ficura-Stichprobe ueberlappt das Pilotfenster bis 2022-12 | gesehen | `BELEGE_AUS_PDF_2026-10-20.md` 4, 8 |
| C-11 | Ereignis 2025-10 (Flash Crash, ohne Wert) aus He et al. v7; Vorwissen der Agenten ueber Marktniveaus 2022-2026 (nicht quantifizierbar, in keiner Zahl verwendet) | offengelegt | BELEGE 9 |
| **C-12** | **Persistenz-Null W1/W2** (DEC-74 (c)): AR(1) je Symbol auf den **Wochenrenditen des Fensters** - das sind die H-32-Outcomes; daraus Median-phi, Null-Mittel und q95 je Variante. Null-Mittel fuer mom1/mom2/mom4 **negativ**, fuer rev_gap **positiv**: die Eigen-Autokorrelation der Renditen wirkt **gegen** beide registrierten Richtungen. Roh-IC, nicht fm8; vermutlich zu grossen Teilen Kendall-Bias (-1/T) der phi-Schaetzung | **gesehen** (richtungstragend, modellbasiert): in der Registry (Zweitfassung Z. 121, q95 Z. 178/241; Drittfassung Tabelle "Persistenz-q in Richtung" mit den Null-Quantilen, z. B. mom1 q95 -0,0064/-0,0362, rev_gap q05 +0,0063/+0,0195, und dem Satz "Mittel ... gegen die registrierten Richtungen") beim Lesen dieser Herleitung mitgelesen; offen in v5e | `hypothesis_registry.md`; `herleitung_h28_h30_v3/DRITTFASSUNG_H28_H30_entwurf.md` Z. 168; `[v5e windows.<W>.noise_floor_and_threshold.persistence_null]` |
| **C-13** | **L-IC-Details 2021-03..2024-06** (deckt das Pilotfenster) | berechnet und versiegelt (v5c/v5d/v5e, DEC-75 (8)), **nie geoeffnet** | `*_L_window_sealed.json` |
| **C-14** | A1-Funding-Bein-Mittel der Pilotperiode implizit (phi x Spread ~83 bp/Woche, 2022-04..2024-06) | gesehen; Funding-Ebene, kein Preis-Querschnitt | DEC-93 Etikett (ii) |
| **C-15** | H-27-Nuisance 2021-03-24..2024-05-31 (DVOL/RV-Streuung, Marktebene) | gesehen; Marktebene | `herleitung_h27/FEASIBILITY.md`, GL-034 |
| **C-16** | A1-Groessen W1/W2: EW-Faktor-SD 13,2 %/7,9 %, Beta-Fehlanpassung, Formations-Spread 175,8/339,6 bp/Woche, psi | gesehen; Funding-/Marktebene, kein Preis-Querschnitt | `herleitung_a1/FEASIBILITY.md`, DEC-93 |
| **C-17** | Aera-Uebergang (Kompendium C.18: "D3-Uebergang endet ~Mitte 2024") liegt an der Grenze Pilot/W1 | Etikett: "Pilot ist Screening, nie Konfirmation" (DEC-99 (2a)) | Kompendium C.18 |

**Befund (korrigiert nach [Review B-2]):** Fuer die fm8-Statistik der vier Varianten ist **keine reale IC gelesen**
worden, weder in W1/W2 noch im Pilotfenster. Gesehen sind u. a. eine **modellbasierte, richtungstragende
Eigen-Autokorrelations-Groesse der W1/W2-Renditen** (Persistenz-Null C-12, Richtung **gegen** H-32, also kein
Testbarkeits-Vorteil), Differenzen (C-3), eine vorzeichenfreie Verwandte (C-7), Streuungen (C-6, C-14..C-16) und das
Literaturband (C-10). Fuer den Pilot-Mittelwert ist nichts gelesen; die L-IC-Details liegen versiegelt (C-13). W1/W2 und
das Pilotfenster gelten fuer H-32 als blind im Sinne von C.17, mit dem Etikett der Erstfassung Abschnitt 7.

---

## EV-1 - Programmregel DEC-99 (BESCHLOSSEN)

DEC-99 ist am 2026-10-20 nach Nutzer-Zustimmung beschlossen (`state/decisions.md`): Wortlaut nach [Review Abschnitt 6]
plus (7) F-WEEK-Zaehlregel (nur getestete Hypothesen zaehlen in m, Doppelausweis alte Zaehlung), (8) W2-Ende 2026-06-28,
(9) H-26 bleibt gesperrt. Massgeblich ist der Text in `decisions.md`; der Herleitungsvorschlag vom selben Tag ist durch
ihn ersetzt (Akte). Fuer H-32 folgen daraus unmittelbar:
- (1) W2 ist das juengste Fenster und muss bestehen (C.10); (2a) Pilot nur Screening, GL-012 (Pilot) kein Verdikt;
- (3) Panel-Schnitt am letzten Pilot-Outcome-Tag vor jeder Pilot-Rechnung; **genau ein Pilotlauf**; Pilot-sha256 vor jedem
  Testfenster; **Pflicht-Doppelausweis** mu_sel und Power daran (EV-6);
- (5) Verbrauch des Pilotabschnitts fuer korrelierte Statistiken (Etikett, Erstfassung 7);
- (6) Pilot gibt das Mittel aus; Zuordnung nach der Pilotstufe mechanisch; Prior = Pilot-Punkt; Literatur-Prior ersetzt;
- (7) F-WEEK: m = Zahl der tatsaechlich getesteten Eintraege (EV-3c, Abschnitt 2);
- (8) W2 2025-07-01..2026-06-28, w_judged 50.

**Richtung:** Testbarkeit (Lockerung von C.18 und der F-WEEK-Zaehlung). Fehlerraten je Test und Power-Ziel unveraendert.

---

## EV-2 - Fenster: Pilotbeginn, Pilotende, W2-Schnitt, Panel-Schnitt

**Fundstellen.** `[wp7k]`: K_t (Lebend-Maske der Union) je Woche; erste Woche mit K_t >= 117 = 2022-04-18 (K 120),
danach nie unter 117; 2022-04-04 K 111, 2022-04-11 K 115; erste Woche mit K_t >= 134 = 2022-05-23 (K 136). PRD 4.1:
K_min = 117 ist "notwendig, nicht hinreichend", 134 die notwendige Breite des Per-Fenster-Designs. A1-Pilotbasis:
2022-04-18..2024-06-17, Haltewochen bis 2024-06-24, 114 Wochen, K 120/202/339 (`feasibility.json`), deckungsgleich.

**(a) Pilotbeginn.**

| Lesart | erste Formationswoche | W_P | K min/Median/max | SE_P mom1 | Richtung |
|---|---|---:|---|---:|---|
| **P-117 (Empfehlung)** | 2022-04-18 | 114 | 120/202/339 | 0,00709 | neutral (Programm-Floor K_min, A1-Praezedenz) |
| P-134 | 2022-05-23 | 109 | 136/203/339 | 0,00715 | Strenge (Per-Fenster-Breite), praktisch ohne Wirkung (+0,9 % SE) |
| Auftrag 2022-04-04..2024-06-24 | 2022-04-04 | 117 | 111/202/340 | 0,00703 | **unzulaessig**: zwei Wochen mit K < 117 und eine Outcome-Woche in W1 |

`[pj power.pilot_windows, power.pilot_precision]`

**(b) Pilotende.** Letzte Formationswoche **2024-06-17**, letzte Outcome-Woche 2024-06-24..06-30. Die Auftragslesart
"Formationswochen bis 2024-06-24" haette als letztes Outcome die Woche 2024-07-01..07-07, die erste Kalenderwoche von
W1. Code-Lesart: `prelaunch.slice_window(weeks, "2022-04-18", "2024-06-30")` ergibt 115 Wochen, w_judged = 114.
**Klasse:** Pflicht (Datentrennung, DEC-99 (3)).

**(c) W2-Ende (beschlossen, DEC-99 (8)).** W2 2025-07-01..2026-06-28, Wochen 2025-07-07..2026-06-22, w_judged 50,
MDE80 W2 mom1 (S1) 0,0165 (ungeschnitten 0,0164); W1 bleibt das schwaechere Fenster `[pj power.sensitivity_W2_uncut_w_judged_51]`.
**Klasse:** Pflicht (DEC-96 E3).

**(d) Harter Panel-Schnitt vor jeder Rechnung (B-6, neu).** Die Waechter auf Outcome-Wochen allein reichen nicht:
Charakteristiken und Betas werden auf dem vollen Panel gebaut (DEC-75 (8)), das bis as_of 2026-09-28 reicht; ohne Schnitt
gingen BTC-Renditen ab 2026-07-01 in Beta-Schaetzungen ein (DEC-96 E3: "Panel dort bei 2026-06-30 abschneiden").
- Test-Modus und Vorlauf v6: die Tagesdaten werden **vor** dem Bau von Wochenrenditen, Charakteristiken, Betas,
  Kalibrierung und Nullen auf <= **2026-06-28** abgeschnitten; Pilot-Modus auf <= **2024-06-30** (DEC-99 (3)).
- Der Daten-Fingerprint wird auf den Dateien geprueft (V7), danach geschnitten; ein Waechter prueft das Maximaldatum des
  geschnittenen Panels und bricht laut ab (C.14); T1-Test "Panel-Schnitt".
- **W2-Neukalibrierung in v6:** sigma_f, rho_f, Faktoranteil, beta_sd (measured/stress/zero mit Gegenproben) und
  null_scales fuer W2 werden auf dem geschnittenen Fenster neu bestimmt; die v5e-W2-Werte (mit Woche 2026-06-29..07-05,
  C-8) werden nicht registriert. W1 wird in v6 auf demselben geschnittenen Panel nachgerechnet und muss v5e innerhalb der
  Suchtoleranz treffen (Determinismus-Kontrolle; W1-Daten liegen vor dem Schnitt).
- **Stress-Listen** (`stress_rel.json`, `stress_abs.json`) nur mit Datumsfilter laden (<= 2026-06-28 bzw. <= 2024-06-30);
  spaetere Eintraege werden nie gelesen, gezaehlt oder ausgegeben.
- **Klasse:** Pflicht (DEC-96 E3, DEC-99 (3)).

---

## EV-3 - Varianten, Selektions-K und F-WEEK

**(a) Varianten.** mom1, mom2, mom4 (positiv), rev_gap (negativ, Lag-2-Gap-Design wie DEC-87 (B)). Richtungen aus PRD
5.3, unveraendert; eine Richtung wird nie nach dem Pilot gewaehlt (Bedingung (i) der Uebergaberegel). Ein
Zwei-Richtungen-Design fuer mom1 (Momentum ODER Reversal, BELEGE 8) wuerde K verdoppeln und ist nicht vorgeschlagen
(Richtung Strenge).

**(b) H-30-Varianten: Ausschluss (empfohlen).**
- `vol_beta`: unter fm8 strukturell neutralisiert - das OLS-Residuum ist per Konstruktion orthogonal zum Beta (C.4,
  DEC-87 (H)).
- `vol_rv`, `vol_max`: GL-012 der Drittfassung wegen Wochen-Drag-Spread(D10-D1)/Kante 2,764 > 0,5 (DEC-88). Der Drag
  haengt an sigma, nicht am Beta; fm8 beseitigt die Ursache nicht (eigene Hypothese noetig).
- **Richtung:** neutral (struktureller Grund vorab bekannt).

**(c) K, BH und F-WEEK (nach DEC-99 (7)).**
- Familie F-H32: **K = 4**, BH alpha 0,10 report-only mit **festem Nenner 4** (nicht uebergebene Eintraege p = 1);
  Selektionsdecke ueber 4 (vorzeichenbereinigt). DEC-94 (7): z = max(1,6449, z_max(4) = 1,052) = 1,6449 `[pj power.selection]`.
- Ueber-Familie **F-WEEK** (Benjamini-Yekutieli, alpha 0,10, am Wellenschluss, **bindend**): **m = Zahl der Hypothesen-
  Eintraege, fuer die ein p-Wert tatsaechlich berechnet wurde** - fuer H-32 die uebergebenen Eintraege (1..4) zuzueglich
  weiterer in der Welle getesteter Hypothesen. F-XSEC1 (7 x p = 1, GL-032) und nicht uebergebene H-32-Eintraege zaehlen
  nicht in m (DEC-99 (7)).
- **Doppelausweis (Pflicht, report-only):** alte Zaehlung m = 11 (F-XSEC1 7 + F-H32 4, p = 1-Eintraege eingeschlossen).
- **p-Groesse je Eintrag (DEC-74 (e), unveraendert nach DEC-99 (6)):** Max-p ueber W1/W2 des Block-Permutations-p der
  fm8-Primaerstatistik - Outcome-Wochen in Bloecken der Laenge 4 permutiert (vor der fm8-Neutralisierung, Betas der
  Formationswochen bleiben), **10.000 Permutationen**, Seed 53, einseitig in Richtung. Im YAML registriert (Erstfassung 11).
- Die K = 11-Lesart der Programm-Bilanz-Review (B-1 (2)) ist durch DEC-99 (7) erledigt.
- **Richtung:** K = 4 als eigene Familie = Testbarkeit gegenueber K = 11 (BH-Nenner), ohne z-Wirkung; die F-WEEK-Zaehlung
  ist beschlossen (DEC-99 (7)), keine Gabelung der Herleitung.

---

## EV-4 - Universums-Variante (BELEGE: Momentum-Vorzeichen haengt am Universum)

**Fundstellen.** BELEGE 2026-10-20, 3.1/8: Ficura (gleichgewichtet, 2017-06..2022-12) Large and Liquid (Marktkap. >= 50
Mio, Volumen >= 5 Mio USD/Woche) 1-Wochen-Momentum +1,36 %/Woche (t 2,33), Small or Illiquid -3,91 % (t -7,31), breit
(> 1 Mio / > 100 Tsd.) -0,12 % (t -0,22); Momentum grosser Coins "seit Anfang 2021 nicht mehr profitabel"; LTW FM > 1 Mio
negativ, > 10 Mio positiv.

**Kandidat U1:** mom1 auf dem PIT-Teiluniversum ohne die zwei umsatzschwaechsten Dezile (trailing-8-Wochen-Median-
Turnover, `characteristics.decile_bucket`: Bucket 1 = niedrigster Umsatz; behalten 3..10). Look-ahead-frei, vorab fixiert.
Achtung Konvention: im WP-7-Spread-Zensus ist D1 das liquideste Dezil, in `decile_bucket` das illiquideste.

| Groesse | U0 (nur volles Universum) | U1 (zusaetzlich mom1 auf Buckets 3..10) |
|---|---|---|
| K | 4 | 5 |
| K_t W1 min/Median | 345/419 | 276/336 |
| fm8-SD W1 (Naeherung: Boden mit K_liq, gleiche Faktorstreuung) | 0,0513 | 0,0567 |
| MDE80 W1 (S1 skaliert) | 0,0206 | **0,0227** |
| Pilotbeginn (K_liq >= 117) / W_P / SE_P | 2022-04-18 / 114 / 0,0071 | **2022-06-13** / 106 / 0,0080 |

`[pj power.universe_variant_U1_mom1_buckets_3_10]`

**Bewertung.** (1) Die Zuordnung der Bybit-Umsatzdezile zu Ficuras USD-Schwellen ist **UNBELEGT**. (2) Die einzige Quelle
mit Liquiditaetssplit meldet fuer grosse Coins nach 2021 kein Momentum mehr. (3) U1 kostet MDE (+10 %), Pilotlaenge (-8
Wochen) und eine Gabelung Richtung Testbarkeit.

**Empfehlung: U0** (Default, neutral). Das Liquiditaets-Teiluniversum (ohne Bucket 1; Buckets 3..10) wird im Pilot und im
Test fuer jede Variante report-only berichtet. U1 nur vor dem Pilot, mit K = 5.

---

## EV-5 - SE der Power-Zeile, E[SE-Regel] und Null-Mittel-Gutschrift

**Fundstellen.** `[v5e windows.<W>.beta_control_recommended_high_rep.{stress,stress_drifting}.variants.<v>]` (1.000
Replikate): `factor_sd`, `mean_ic_draws_sd`, `mean_ic_draws_mean`. Die v5e-Null hat keine Beta-Vorlaufwochen: 45 (W1) /
44 (W2) IC-Wochen je Replikat statt 52/51 ([Review Abschnitt 1] bestaetigt).

| Lesart | Formel | W1 mom1 | MDE80 W1 mom1 (+ Gutschrift) | Richtung |
|---|---|---:|---:|---|
| **S1 (bindend bis v6)** | SE = SD des Fenstermittels der Null (`mean_ic_draws_sd`, max driftfrei/Drift) | 0,00794 | **0,0206** | Strenge (45-Wochen-Mittel, ~+7..13 % gegen 52 Wochen) |
| S2 | sqrt(max(1, c_sim)) x SD / sqrt(w_judged), c_sim = 45 x draws_sd^2 / SD^2 = 1,080 | 0,00739 | 0,0192 | P-1-exakt fuer 52 Wochen, ohne K_fm8-Verlust |
| S3 (Auftrag) | SD / sqrt(w_judged), c = 1 | 0,00711 | 0,0185 (ohne Gutschrift 0,0176) | Testbarkeit (verstoesst gegen DEC-94 (4)) |

**Nach v6 (A-6, [Review B-7]):** Die Lauf-SE ist max(Boden, SD/sqrt(W), SE_stat); ihr Erwartungswert liegt ueber der
SD des Fenstermittels (synthetisch [Review]: mom1 W1 x1,009, W2 x1,030; rev_gap x1,033 / x1,057). v6 friert deshalb je
Fenster und Variante zwei Groessen ein: **`se_mean`** (SD des 52/50-Wochen-Fenstermittels der stress-Null mit Beta-Vorlauf)
und **`e_se_rule`** (Erwartungswert der SE nach Regel P-1 (4) ueber die Null-Replikate, Bootstrap wie im Lauf). Power-Zeile
(DEC-94 (3)): Schwelle T_W = z_krit x e_se_rule_W + max(0, m_W), Streuung SD = se_mean_W:
P_W = Phi((pi - max(0, m_W) - z_krit x e_se_rule_W) / se_mean_W); MDE80_W = z_krit x e_se_rule_W + 0,8416 x se_mean_W +
max(0, m_W). Ohne diese Korrektur laege die Power an MDE80 bei 0,77..0,80 [Review B-7]. Bis v6 bindet S1 (deckt das ab).

**Nebenbefund:** Die Bilanz-Konvention c_hat = 52 x draws_sd^2 / SD^2 (1,25..1,28) ist ein Artefakt der 45-Wochen-
Ziehungen; mit konsistenter Wochenzahl liegt c_hat bei 0,99..1,11 (DEC-98-Nachtrag: Auflage A-9, Orchestrator).

**Gutschrift.** Das mechanische Null-Mittel in Richtung (stress, extremeres aus driftfrei/Drift) ist W1 mom1 +0,00087,
mom2 +0,00142, mom4 +0,00185, rev_gap -0,00114. Die Testschwelle enthaelt nur den positiven Teil (negatives m wird nicht
gutgeschrieben; Richtung Strenge); im Gate als Bedingung "Statistik >= 95-%-Quantil der stress-Null" (EV-7).
Bericht: unter der measured-Kalibrierung waere MDE80 W1 mom1 0,0185 (nicht bindend, DEC-94 (5)).

---

## EV-6 - Uebergaberegel P -> T und Prior-Lesart

**Regel U (eine Regel, vorab fixiert, mechanisch, je Variante v):**

- Eingaben aus dem Pilot (nur Pilotfenster, Panel <= 2024-06-30, genau ein Lauf): x_P = Mittel der fm8-Wochen-ICs in
  Richtung; SE_P nach P-1 (4): max(B_P/sqrt(W_P), SD_P/sqrt(W_P), SE_stat) mit stationaerem Bootstrap (mittlere
  Blocklaenge 4, 1.000, Seed 53, `power_p1.stationary_bootstrap_se`); t_P = x_P / SE_P; 80-%-Band x_P +- 1,2816 x SE_P;
  F2_real = max(0, SD_P^2 - mean_t 1/(k_t - 1)) mit k_t = Symbole im fm8-IC der Woche t; c_real = max(1, W_P x SE_stat^2 / SD_P^2).
- Pilot-Quelle je Testfenster (DEC-94 (5) (i), K-bereinigt): SE_W,Pilot = sqrt(c_real) x sqrt(v_fm8_W + F2_real) /
  sqrt(w_judged_W), v_fm8_W = mean_t 1/(K_fm8,t - 1) des Testfensters (v6, ohne Outcome).
- Test-Groessen: SE_T,W = max(e_se_rule_W (v6), SE_W,Pilot) fuer die Schwelle; SD_T,W = max(se_mean_W (v6), SE_W,Pilot)
  fuer die Streuung. MDE80*_v = max_W (1,6449 x SE_T,W + 0,8416 x SD_T,W).
- Null-Gutschrift **m* = max(0, m_P, m_W1, m_W2)** (A-6, [Review B-8]): m_P = mechanisches Null-Mittel der **Pilotperiode**
  in Richtung, von v6 aus einer Pilotperioden-Kalibrierung (sigma_f, rho_f, Faktoranteil; nur Streuung und
  Autokorrelation, Waechter "kein Mittel"; stress, driftfrei und Drift 0,002) eingefroren; m_W1, m_W2 entsprechend fuer
  die Testfenster.
- **(i)** x_P > 0. **(ii)** x_P - m* >= MDE80*_v. **(iii)** t_P >= 2,0.
- Alle drei erfuellt -> **Uebergabe**; Prior der Zuordnung pi = x_P (Lesart A); Regime =
  `power_p1.assign_regime([pi - max(0, m_W1), pi - max(0, m_W2)], [SE_T,W1, SE_T,W2], sds=[SD_T,W1, SD_T,W2])` (unter (ii)
  stets C10); Doppelausweis `assign_regime_a3_practice`. Sonst **GL-012 (Pilot)** mit gemessenem Grund; p = 1 im BH-Nenner 4.
- **Pflicht-Doppelausweis (DEC-99 (3), [Review B-5]):** mu_sel = Loesung von P_mu(X >= x_P | X >= c_v) = 0,5 mit
  X ~ N(mu, SE_P^2) und c_v = MDE80*_v + m* (die registrierte Uebergabeschwelle auf x_P); dazu die gemeinsame Testpower
  an mu_sel. Etikett an Pflichtzeile 1; keine Entscheidungswirkung (eine selektionsbereinigte Entscheidungsregel waere
  nicht selbstkonsistent). Beispiel mom1 [Review B-5]: x_P = c + 0,25 SE_P -> mu_sel 0,004 (Power 0,02); c + 1 SE_P ->
  0,0255 (0,92).
- **Genau ein Pilotlauf** (DEC-99 (3)); **Verbrauch** des Pilotabschnitts fuer korrelierte Statistiken (DEC-99 (5)).

**Vorab-Zahlen der Schwelle (ii)** (S1, v5e; v6 ersetzt sie, der Pilot kann sie nur erhoehen): mom1 0,0206, mom2 0,0237,
mom4 0,0287, rev_gap 0,0195 (auf x_P, mit Gutschrift aus W1; m_P unbekannt bis v6). (iii) bindet nur, wenn SE_P > halbe
Schwelle; sonst redundant ([Review Abschnitt 1]).

**Gabelung Prior-Lesart.**

| Lesart | Bedingung (ii) wirkt auf | wahrer fm8-IC fuer 50 % / 80 % Uebergabe (mom1 / rev_gap) | P(Uebergabe), IC = 0 | Zwei-Stufen-Power mom1 bei fm8-IC 0,020 / 0,025 / 0,033 | Richtung |
|---|---|---|---|---|---|
| **A Punkt (Empfehlung)** | x_P | 0,0197 / 0,0207 ; 0,0257 / 0,0266 | 0,003 / 0,002 (MC 0,1..0,5 %) | 0,39 / 0,71 / 0,96 | Testbarkeit |
| B untere 80-%-Grenze | x_P - 1,2816 SE_P | 0,0288 / 0,0297 ; 0,0348 / 0,0356 | < 0,001 | 0,08 / 0,27 / 0,72 | Strenge |

`[pj power.handover_oc.<v>.{A_punkt,B_untere_80}]` (S1-gestuetzt, Pilot-SE vorhergesagt, m_P := m_W1; v6 aendert die
Zahlen; MC der vollen Regel liegt leicht darunter, weil die Pilot-Quelle in ~30 % der Faelle bindet [Review B-14]).
"Zwei-Stufen-Power" = Uebergabe x C10-Gemeinsampower, **vor** F-WEEK (dazu Abschnitt 2).

Uebergabewahrscheinlichkeit, Lesart A (Lesart B) je wahrem fm8-IC:

| fm8-IC | mom1 | mom2 | mom4 | rev_gap |
|---:|---|---|---|---|
| 0,000 | 0,003 (0,000) | 0,002 (0,000) | 0,001 (0,000) | 0,002 (0,000) |
| 0,004 | 0,013 (0,000) | 0,008 (0,000) | 0,004 (0,000) | 0,009 (0,000) |
| 0,008 | 0,049 (0,002) | 0,029 (0,001) | 0,013 (0,000) | 0,036 (0,001) |
| 0,012 | 0,137 (0,009) | 0,086 (0,004) | 0,040 (0,001) | 0,109 (0,006) |
| 0,015 | 0,252 (0,026) | 0,167 (0,012) | 0,082 (0,004) | 0,210 (0,018) |
| 0,020 | 0,514 (0,106) | 0,381 (0,057) | 0,211 (0,019) | 0,462 (0,084) |
| 0,025 | 0,771 (0,295) | 0,641 (0,179) | 0,415 (0,067) | 0,731 (0,253) |
| 0,030 | 0,926 (0,566) | 0,848 (0,399) | 0,647 (0,183) | 0,908 (0,519) |
| 0,033 | 0,969 (0,722) | 0,923 (0,557) | 0,767 (0,291) | 0,960 (0,682) |

**fm8-Daempfung (A-4, [Review B-4]).** Das PIT-Beta nutzt die Wochen t-7..t und enthaelt damit die Formationswoche(n);
die Querschnittsregression nimmt einen Teil eines beta-unabhaengigen Signals mit. Realisiert/injiziert synthetisch
**0,754** (mom1, W1-stress-Welt, 300 Paare mit gemeinsamen Zufallszahlen, `[pj fm8_daempfung]`; Review 0,751 stress /
0,764 measured). Das ist eine Eigenschaft von fm8, kein Designfehler (ein verzoegertes Beta daempft weniger, verrauscht
aber mehr, [Review B-4]). Die Tabelle oben ist auf der fm8-Skala. Ein Literatur- oder Signalwert s entspricht auf der
fm8-Skala ~0,75 s; fuer mom2/mom4 (mehr Formationswochen im Beta-Fenster) vermutlich staerker gedaempft.

**Literaturband (C-10) als Erwartung, auf fm8-Skala (x 0,754), Lesart A (B):**

| Literaturwert | mom1 | mom2 | mom4 | rev_gap |
|---:|---|---|---|---|
| 0,004 (Weg B unten) | 0,009 (0,000) | 0,005 (0,000) | 0,003 (0,000) | 0,006 (0,000) |
| 0,012 (Weg B oben) | 0,066 (0,003) | 0,039 (0,001) | 0,018 (0,000) | 0,049 (0,002) |
| 0,020 | 0,255 (0,026) | 0,170 (0,013) | 0,083 (0,004) | 0,213 (0,019) |
| 0,033 (Ficura-A*) | 0,766 (0,289) | 0,636 (0,175) | 0,410 (0,066) | 0,726 (0,248) |

`[pj fm8_daempfung.uebergabe_bei_literaturwert_auf_fm8_skala]` (mom2/mom4: Obergrenzen). Ungedaempft (Erstfassung) waeren
es mom1 1,3..13,7 % im Weg-B-Band und 97 % bei 0,033 - zu guenstig.

**Bewertung der Lesart.** (1) Die Fehlerrate des Tests ist von der Lesart unabhaengig (getrennte Daten). (2) DEC-99 (6):
die "A-priori-Erwartung" ist der Pilot-Punkt der registrierten Lesart. (3) Die DROP-Lesart des Tests bezieht sich auf
Effekte >= MDE80. (4) Lesart B verschiebt die 50-%-Schwelle um 1,28 SE_P (~+0,009) und korrigiert den Gewinnerfluch
nicht, sondern verschiebt nur die Operationscharakteristik [Review B-5]. (5) Der Gewinnerfluch wird ueber den
Pflicht-Doppelausweis mu_sel offen gelegt. **Empfehlung: Lesart A** (Richtung Testbarkeit, etikettiert).

**DEC-52 unter der Regel.** `assign_regime` gaebe DEC52 in einem schmalen Band unter der C10-Schwelle (mom1 0,0195..0,0206,
mom2 0,0222..0,0237, mom4 0,0267..0,0287, rev_gap 0,0190..0,0195); (ii) schliesst es aus (Richtung Strenge).

**Nach dem Pilot ist das Pilotfenster verbraucht** (DEC-99 (5)); ohne Uebergabe bleiben W1/W2 ungeoeffnet und blind.

---

## EV-7 - Teststufe: Statistik, Schwelle, Bedingungen, F-WEEK, was nicht gerechnet wird

**Statistik:** Mittel der woechentlichen Spearman-ICs der Charakteristik gegen das fm8-neutralisierte Folgewochen-Outcome
(`ic.apply_beta_control("fm_neutral_8w", ...)` + `ic.weekly_ic_series`, close_at_last, min 10 Symbole) - die IC_res der
Drittfassung, jetzt Primaerstatistik.

**Bedingungen je Fenster (C.10 hart):** (1a) Vorzeichen; (1b) Statistik in Richtung >= z_krit x SE_W, SE_W =
max(B_W/sqrt(W), SD/sqrt(W), SE_stat) (P-1 (4), Boden aus K_fm8); (1c) Statistik in Richtung >= q95_W (95-%-Quantil des
fm8-Fenstermittels der stress-Null, extremeres aus driftfrei/Drift 0,002, v6); (4b) nur rev_gap: Bounce-Kill je Fenster.
Vor-Verdikt-Kill: vorzeichenbereinigte Selektionsdecke ueber K = 4 >= eingefrorene Schwelle -> GL-012 des Eintrags
(eine Decke, vier Schwellen - die kleinste, rev_gap, bindet zuerst; grob 0,62..0,68 der Schwelle [Review B-15]).

**F-WEEK (A-3):** Ein vorlaeufiger PASS wird am Wellenschluss durch BY ueber F-WEEK (alpha 0,10, m nach DEC-99 (7))
bestaetigt oder nicht; p je Eintrag = Max-p des Block-Permutations-p (10.000, Block 4, Seed 53). Doppelausweis m = 11
report-only. Endpower in Abschnitt 2.

**DROP-Lesart mit Daempfung (A-4):** Ein DROP bedeutet "fm8-IC >= MDE80 (W1 mom1 0,0206) mit Power 0,80 nicht vorhanden";
auf ein beta-unabhaengiges Signal umgerechnet (/ 0,754) entspricht das ~0,027 (mom1), 0,031 (mom2, Untergrenze), 0,038
(mom4, Untergrenze), 0,026 (rev_gap) `[pj fm8_daempfung.drop_lesart_beta_unabhaengiges_signal_bei_mde80]` - Etikett.

**Nicht gerechnet (Blindheitsschutz):** roher IC, Lag-Profil, Beta-Kalibrierungs-IC. Persistenz-Null: nicht gerechnet,
**neutral** (bindet nachweislich nicht; dieses Wissen stammt aus C-12). Report-only: BH (Nenner 4),
Liquiditaets-Teiluniversen (EV-4), Survivorship-Etikett (synthetisch).

**Nebenbefund Decke:** `nulls._mean_of_max` nimmt rohe Vorzeichen ([Review B-15] bestaetigt); fuer H-32 neue,
vorzeichenbereinigte Funktion (additiv).

---

## EV-8 - Positivkontrolle in Produktionskonfiguration (Pruefung der Power-Annahme)

**Befund aus dem synthetischen Check** (`[pj synthetischer_check]`; Repo-Code auf einem kuenstlichen Panel K = 419,
52 Urteilswochen + 8 Vorlaufwochen, W1-stress-Welt der Drittfassung; kein Realdatum):

| Sektorschock / sigma_e | Wochen-SD fm8-IC mom1 | SD des 52-Wochen-Mittels |
|---:|---:|---:|
| 0 | 0,0520 | 0,0070 |
| 0,1 | 0,0520 | 0,0072 |
| 0,2 | 0,0527 | 0,0075 |
| 0,375 (PRD-Fixture, DEC-89) | 0,0611 (**+17,6 %**; Review +19 %) | 0,0088 |

Injektion nominal 0,0206 -> realisiert 0,0156 (0,754, EV-6); Bestehensquote an der eingefrorenen Schwelle 0,617 gegen
0,633 vorhergesagt; Negativkontrolle 0,033.

**Regel (vorab fixiert, je uebergebener Variante; A-6/A-7):**
1. **Welt:** stress-Kalibrierung je Fenster aus der YAML (rho_f, beta_sd, null_scales; W2 aus v6 neu), Marktspalte =
   Faktor, Drift 0, reale Wochenform (K_t, PIT-Masken, Panel geschnitten); 8 Sektorbloecke mit Schock sigma_g, per Bisektion
   so gewaehlt, dass die Wochen-SD des fm8-IC der Negativkontrolle **sqrt(v_fm8_W + max(F2_null,W, F2_real))** auf +-5 %
   trifft - also an der im Pilot **gemessenen** Zusatzstreuung F2_real, mit der Null-Streuung als Untergrenze
   (sigma_g = 0, wenn F2_real <= F2_null).
2. **Injektion:** Amplitude auf getrennten Kalibrierungs-Seeds (1000..1049, gemeinsame Zufallszahlen) so, dass der
   **realisierte** Injektionseffekt (positiv minus negativ, fm8) im bindenden Fenster 1,6449 x SE_T,W + 0,8416 x SD_T,W
   (MDE80 ohne Gutschrift, e_se_rule-Lesart EV-5; die Gutschrift traegt die Null selbst) auf +-5 % trifft.
3. **Urteils-Seeds:** 53..252 (200), positiv und negativ; Gate-Kette (1a)-(1c), (4b) mit den eingefrorenen Konstanten.
4. **BESTANDEN genau dann, wenn:** (a) Wochen-SD der Kontrollwelt <= 1,10 x SD der Power-Zeile je Fenster (DEC-94 (5);
   jetzt eine Konsistenzpruefung zwischen gemessener Streuung und Power-Zeile); (b) PASS-Anteil im bindenden Fenster
   >= 0,734; (c) falsche PASS-Quote je Fenster <= 0,086; (d) realisierter Injektionseffekt auf den Urteils-Seeds innerhalb
   +-10 % des Ziels. Sonst kein Lauf, neue DEC.
5. **Report-only:** PK-Quote zusaetzlich in der woertlichen PRD-/DEC-89-Sektorwelt (Schock 0,375 sigma_e); gemeinsame
   C10-Quote.

**Etikett (A-7, [Review B-9]):** Die Kalibrierung der Kontrollwelt an F2_real statt der woertlichen PRD-Sektorwelt ist
eine Gabelung **Richtung Testbarkeit** (die PRD-Welt wuerde die 10-%-Regel gegen eine Ein-Faktor-Power-Zeile verletzen);
die Realismuspruefung leistet F2_real aus dem Pilot.

---

## 2. Power vorab (nur Nuisance, ohne Pilot) - Prior-Gitter und F-WEEK-Endpower

Prior = erwartete fm8-Statistik in Richtung (was der Pilot-Punkt schaetzt). S1, W2 geschnitten (w_judged 50).
Fenster-Power W1 / W2, Regime P-1 (DEC-52-Gate Produkt), Regime A3-Praxis; "nur DEC-94" = zugelassen nur durch DEC-94.

| Prior | mom1 | mom2 | mom4 | rev_gap |
|---:|---|---|---|---|
| 0,010 | 0,31 / 0,43 GL012 (0,10); A3 GL012 | 0,25 / 0,37 GL012 (0,06) | 0,19 / 0,28 GL012 (0,03) | 0,36 / 0,44 GL012 (0,13) |
| 0,015 | 0,55 / 0,73 GL012 (0,45) | 0,45 / 0,64 GL012 (0,30) | 0,34 / 0,50 GL012 (0,14) | 0,60 / 0,72 GL012 (0,50) |
| 0,020 | 0,78 / 0,92 **DEC52** (0,83); A3 GL012, nur DEC-94 | 0,67 / 0,86 GL012 (0,67) | 0,52 / 0,73 GL012 (0,41) | 0,82 / 0,91 **C10**; A3 GL012, nur DEC-94 |
| 0,025 | 0,92 / 0,99 **C10**; nur DEC-94 | 0,84 / 0,96 **C10**; nur DEC-94 | 0,69 / 0,88 GL012 (0,72) | 0,94 / 0,98 **C10**; nur DEC-94 |
| 0,033 | 0,99 / 1,00 **C10**; A3 C10 | 0,97 / 1,00 **C10**; A3 C10 | 0,89 / 0,98 **C10**; nur DEC-94 | 0,99 / 1,00 **C10**; A3 C10 |

MDE80 W1 / W2 (P-1, S1): mom1 0,0206 / 0,0165; mom2 0,0237 / 0,0184; mom4 0,0287 / 0,0221; rev_gap 0,0195 / 0,0167.
A3-Praxis (Schwelle 2,4865 SE): MDE80 W1 0,0273 / 0,0312 / 0,0377 / 0,0261. `[pj power.power_table.<v>.S1_draws_sd_bindend]`

**F-WEEK-Endpower (A-3, DEC-99 (7)).** BY mit m Eintraegen verlangt fuer eine einzelne Ablehnung Max-p <= 0,10 / (m x H_m):
m = 1: 0,100 (C10 bindet), 2: 0,0333, 3: 0,0182, 4: 0,0120; alte Zaehlung m = 11: 0,0030. Endpower = gemeinsame Power
beider Fenster mit z_eff = max(1,6449, Phi^-1(1 - Schwelle)), p normal genaehert (der Lauf nutzt den Permutations-p)
`[pj power.f_week_by_end_power]`:

| Variante | Prior = MDE80 (W1) | m = 1 | m = 2 | m = 3 | m = 4 | m = 11 (alt, report-only) |
|---|---:|---:|---:|---:|---:|---:|
| mom1 | 0,0206 | 0,74 | 0,67 | 0,55 | 0,48 | 0,26 |
| mom2 | 0,0237 | 0,75 | 0,68 | 0,57 | 0,49 | 0,27 |
| mom4 | 0,0287 | 0,76 | 0,69 | 0,57 | 0,50 | 0,28 |
| rev_gap | 0,0195 | 0,72 | 0,64 | 0,52 | 0,44 | 0,23 |

Je Fenster Power 0,80 durch die BY-Stufe hiesse MDE80 W1 mom1 0,0206 (m = 1) / 0,0221 / 0,0242 / 0,0255 (m = 4) / 0,0294
(m = 11); rev_gap 0,0195 / 0,0210 / 0,0230 / 0,0243 / 0,0282. **Lesart:** DEC-99 (6) laesst die Zuordnung je Fenster
(DEC-94 (6)) unveraendert; die Endpower ist ein Pflicht-Ausweis in Pflichtzeile 1 (Review B-3 Lesart (b)), keine
Zuordnungsgrundlage. m ist erst nach der Uebergabe bekannt; ausgewiesen wird die Zeile fuer das tatsaechliche m und
fuer m = 11.

**Pilot-Praezision** (vorhergesagt, W_P 114, Boden aus `[wp7k]`, Faktorstreuung F2 und c aus v5e-stress):

| | mom1 | mom2 | mom4 | rev_gap |
|---|---:|---:|---:|---:|
| SD_P (Woche) | 0,0728 | 0,0779 | 0,0860 | 0,0730 |
| **SE_P** | **0,0071** | 0,0075 | 0,0085 | 0,0070 |
| Auftrag (0,0511 / sqrt(117)) | 0,0047 | - | - | - |
| Sens.: F doppelt / Neulistungen (K_fm8 ~ K - 8 Wochen Listungen) | 0,0076 / 0,0074 | 0,0092 / 0,0078 | 0,0119 / 0,0088 | 0,0076 / 0,0074 |

Rechenweg [abg.]: SD_P^2 = mean_t 1/(K_t - 1) (Pilot, 0,00504) + F2, F2 = max_W (SD_W^2 - mean_t 1/(K_t - 1)); SE_P =
sqrt(c) x SD_P / sqrt(114), c = max_W max(1, c_sim). Listungszahlen je Jahr aus WELLE1 Teil 6 (2022: 86, 2023: 113, 2024: 228).

---

## 3. Bauliste und Bauaufwand (nach DEC-99, vor der Registrierung)

Additiv in neuen Dateien (A3-Code-Fingerprint der Drittfassung bleibt unberuehrt; DEC-94 (8)). **Neu** = nach Review.

| # | Baustein | Inhalt | Umfang (Code + Tests) |
|---|---|---|---|
| B-0 **neu** | Panel-Schnitt | Funktion "Tagespanel auf <= Stichtag abschneiden" vor jedem Wochen-/Charakteristik-/Beta-Bau; Fingerprint auf den Dateien vorher, Maximaldatum-Waechter nachher (loud fail); Stichtage aus der YAML (`seal.panel_cut_test` 2026-06-28, `seal.panel_cut_pilot` 2024-06-30); Stress-Listen nur mit Datumsfilter | ~60 + 60 |
| B-1 | Vorlauf v6 (ohne Outcome) | fm8-stress-Null mit 8 Beta-Vorlaufwochen fuer W1, W2 (geschnitten), K = 4, 1.000 Replikate, driftfrei und Drift 0,002: `se_mean`, `sd_week`, `null_mean`, `q95`, vorzeichenbereinigte `ceiling_k4`; **neu: `e_se_rule`** (Erwartungswert der SE nach P-1 (4) ueber die Replikate, stationaerer Bootstrap wie im Lauf); **neu: W2-Neukalibrierung** auf dem geschnittenen Fenster (sigma_f, rho_f, Faktoranteil, beta_sd measured/stress/zero mit Gegenproben, null_scales) und W1-Nachrechnung als Determinismus-Kontrolle; **neu: Pilotperioden-Kalibrierung** (sigma_f, rho_f, Faktoranteil; Waechter "kein Mittel") und `m_P` je Variante (stress, driftfrei/Drift); K_fm8-Reihen fuer P, W1, W2 nur aus `returns_valid`; Stress-Abdeckung fensterbeschraenkt | ~350 + 220; Cloud ~1-1,5 h |
| B-2 | Pilot-Modus `--pilot` | Startsperre; **Panel-Schnitt 2024-06-30 (B-0)**; Siegel-Waechter (keine Outcome-Woche nach 2024-06-30); Pilot-Statistiken; Regel U mit m* = max(0, m_P, m_W1, m_W2) und e_se_rule/se_mean; `power_p1`-Zuordnung; **neu: mu_sel + Power an mu_sel**; **neu: Neulauf-Sperre** (ein vorhandenes Pilot-Ergebnis blockiert einen zweiten Lauf ausser mit `--pilot-rerun-dec <DEC>`); DEC-53-Artefakte; `h32_pilot.json` | ~340 + 330 |
| B-3 | Testlauf H-32 | Startsperre YAML und Pilot-Ergebnis (sha256); **Panel-Schnitt 2026-06-28**; nur uebergebene Eintraege; P-1-Gate als reine Funktion (T4); **neu: F-WEEK-Ausgabe** - Block-Permutations-p (10.000, Block 4, Seed 53, vor der Neutralisierung permutiert), Max-p, m nach DEC-99 (7), BY-Vorbehalt und Doppelausweis m = 11; BH Nenner 4; kein roher IC, kein Lag-Profil, kein Beta-IC | ~450 + 330 |
| B-4 | Positivkontrolle H-32 | **geaendert:** Welt-SD an sqrt(v_fm8 + max(F2_null, F2_real)) (Sektor-Bisektion); Injektionsziel mit e_se_rule; 200 Seeds; Kriterien EV-8; **neu: Bericht in der PRD-Sektorwelt (report-only)** | ~280 + 220 |
| B-5 | Schema/Template | YAML-Felder `pilot_window`, `handover_rule`, `fdr`, `seal`, `alpha`, `z_krit`, `mde_faktor`, `primary_statistic`, `windows.<W>.frozen_v6` (inkl. `e_se_rule`), `pilot_window.frozen_v6.m_P`; T5-Pins | ~170 + 110 |
| B-6 | Tests | DEC-39-Trio fuer fm8-primaer (**T1 positiv: realisierte Injektion**); **T1 Panel-Schnitt** (ein Datum nach dem Stichtag im Panel -> Abbruch bzw. nachweislich abgeschnitten); Pilot- und Siegel-Leck; T0 mu_sel; T2 N >= 3; T4 Uebergabe- und Gate-Arithmetik; Monotonie; T5; T6; T7 | in den Zahlen oben |

**Summe:** ~1.650 Zeilen Code, ~1.270 Zeilen Tests (nach Review +~300 / +~220); zwei Bau-Sitzungen plus Abnahme.
Rechenzeit Cloud: v6 ~1-1,5 h (Pilot-Kalibrierung und e_se_rule ~+0,5 h), Pilot < 15 min, Positivkontrolle ~15-30 min,
Testlauf ~1 h Null-Nachrechnung plus ~1 h Permutationen (10.000 x 2 Fenster je uebergebenem Eintrag; Dauer UNBELEGT).
Panel: derselbe Harvest-Export wie v5e (as_of 2026-09-28), geschnitten.

**Reihenfolge (DEC-99 "Erste Anwendung"):** Bau B-0..B-6 -> Abnahme -> Vorlauf v6 (Realdaten, nur Nuisance) -> finale YAML
+ sha256 -> Registrierung -> Pilot (genau einmal) -> Uebergabe-Vermerk (sha256) -> bei Uebergabe: Positivkontrolle allein
-> Testlauf -> GL-Eintrag (vorlaeufig) -> F-WEEK-BY am Wellenschluss; ohne Uebergabe: GL-012 (Pilot), W1/W2 ungeoeffnet.

---

## 4. UNBELEGT und offene Punkte

| Punkt | Status | Wirkung |
|---|---|---|
| Literatur-Prior des beta-neutralen Wochen-IC >= 0,020 | UNBELEGT (DEC-98 N2) | ersetzt durch den Pilot (DEC-99 (6)) |
| Reale Sektor-/Stil-Streuung des fm8-IC (Null ist Ein-Faktor) | UNBELEGT bis zum Pilot (F2_real) | kann MDE80* und Schwelle (ii) erhoehen; Kontrollwelt haengt daran |
| Mechanisches Null-Mittel der Pilotperiode m_P | UNBELEGT bis v6 [Review B-8] | geht in m* ein (nur erhoehend) |
| e_se_rule, se_mean mit Beta-Vorlauf, K_fm8-Reihen, W2-Neukalibrierung | offen (v6) | S1 bis dahin bindend |
| Daempfung fuer mom2/mom4 | nur mom1 gemessen (0,754) | Erwartungszahlen dort Obergrenzen |
| Zuordnung Bybit-Umsatzdezile zu "Large and Liquid" | UNBELEGT | Grund fuer U0 |
| Laufzeit von Testlauf und 10.000 Permutationen | UNBELEGT (~2 h geschaetzt) | Positivkontrolle ohnehin vorgeschaltet |

---

## 5. Gabelungs-Bilanz (DEC-93 H-1; korrigiert nach [Review B-11], A-8)

| EV | Empfehlung | Klasse |
|---|---|---|
| EV-1 DEC-99 | beschlossen | **Testbarkeit** (Lockerung C.18, F-WEEK-Zaehlung) |
| EV-3c K | 4 als eigene Familie, BH-Nenner 4 | **Testbarkeit** (gegen K = 11, ohne z-Wirkung) |
| EV-6 Prior-Lesart | A (Punkt), Doppelausweis mu_sel | **Testbarkeit** |
| EV-6 Pilot-Null-Mittel | Herleitung: Proxy W1; nach A-6: m_P aus v6 in m* | **Testbarkeit** (Erstfassung; durch die Auflage geschlossen) |
| EV-8 Kontrollwelt | sigma_g an F2_real, PRD-Welt report-only | **Testbarkeit** |
| EV-3a Richtungen | fest, kein Zwei-Richtungen-mom1 | Strenge |
| EV-5 SE | S1 bindend bis v6 | Strenge |
| EV-6 DEC-52 | durch (ii) ausgeschlossen | Strenge |
| EV-7 Nebengroessen | roher IC, Lag-Profil, Beta-IC nicht rechnen | Strenge (Blindheitsschutz) |
| EV-2b Pilotende | 2024-06-17 | Pflicht (Datentrennung, DEC-99 (3)) |
| EV-2c/d W2-Ende, Panel-Schnitt | 2026-06-28, harter Schnitt | Pflicht (DEC-96 E3, DEC-99 (8)) |
| EV-6 MDE80-Quelle | max(v6-Null, Pilot) | Pflicht (DEC-94 (5) woertlich) |
| EV-2a Pilotbeginn | K >= 117 | neutral (gegen 134 numerisch ohne Wirkung) |
| EV-3b H-30 | ausgeschlossen | neutral (struktureller Grund) |
| EV-4 Universum | U0 | neutral (Default) |

**Bilanz: 5 Testbarkeit, 4 Strenge, 3 Pflicht, 3 neutral.** Vorab beschlossene Hebel (keine Gabelung dieser Herleitung,
aber ausgewiesen): P-1 (DEC-94, Schwelle 2,4865 -> 1,6449 SE) und fm8 als Primaerstatistik (DEC-98 E1 (a), Wochen-SD
0,13 -> 0,05) - zusammen MDE80 W1 mom1 0,060 (GL-032, stress) -> 0,0206; dazu DEC-99 (7) (F-WEEK-Zaehlung).
Persistenz-Null "nicht rechnen" ist neutral (bindet nachweislich nicht, Wissen aus C-12).

---

## 6. Was nicht folgt

Kein Verdikt ueber Momentum, Reversal oder einen beta-neutralen Querschnittseffekt; keine Registrierung; keine Zahl aus
Pilot, W1 oder W2. Die erwarteten Uebergabewahrscheinlichkeiten sind Eigenschaften der Regel unter angenommenen wahren
Werten (S1-gestuetzt, v6 aendert sie), keine Vorhersage des Ergebnisses. Hinweis ohne Empfehlung: Da der Pilot etwa so
praezise ist wie ein Testfenster (SE 0,0071 gegen 0,0079), erlaubt DEC-99 (2b) ihn alternativ als drittes Urteilsfenster;
dafuer fehlte ein Prior wie bisher - das ist nicht Gegenstand dieser Herleitung.
