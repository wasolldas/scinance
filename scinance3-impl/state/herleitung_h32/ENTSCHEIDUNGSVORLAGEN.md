# Entscheidungsvorlagen H-32: Zweistufen-Design fuer den beta-neutralen Querschnitts-IC (Pilot auf der Vorperiode, Test auf W1/W2)

> ENTWURF der Herleitung, Stand 2026-10-20. Nichts hier ist beschlossen oder registriert; entscheiden darf nur der
> Orchestrator, DEC-99 erst nach Zustimmung des Nutzers. Die Registrierung setzt DEC-99, den Vorlauf v6 (outcome-frei)
> und ein adversarisches Review voraus.
>
> **Ergebnisblindheit.** Keine Datenrechnung: weder das Pilotfenster noch W1/W2 wurden geoeffnet, kein Panel geladen,
> keine reale IC berechnet, kein Outcome. Jede Power-, MDE-, Zuordnungs- und Uebergabe-Zahl stammt aus
> `src/bybit_edge/research/power_p1.py` mit Nuisance aus der Akte. Nicht geoeffnet: alle Siegeldateien
> (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`), `survivorship_bias_UNION_REAL.json`,
> `stress_rel.json`/`stress_abs.json` (koennen Tage ab 2026-07-01 tragen), keine Datei mit Daten ab 2026-07-01
> (Blind-Siegel DEC-96 E3). Aus `feasibility.json` (A1) wurden nur Datums-/K-Metadaten der Pilotbasis gelesen, keine
> Steigungen. Ein synthetischer Check (Repo-Code auf einem kuenstlichen Panel, kein Realdatum) prueft zwei Annahmen
> (Abschnitt EV-8).
>
> **Fundstellen-Kuerzel.**
> - `[v5e <pfad>]` = `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json` (sha256 `94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2`), JSON-Pfad;
> - `[wp7k]` = `state/runs/wp7_20260921/decile_degeneration_weekly.csv` (sha256 `7c6119afe3bbaa862acd5f65bfcb3e53ffb8244e7056aba7f5a56df3a0fac9e5`), nur Spalten `week`, `n_symbols`;
>   die Reihe stimmt in allen 103 urteilstragenden Wochen von W1/W2 exakt mit der v5e-K_t-Reihe ueberein (0 Abweichungen) und ist damit die A3-Lebend-Maske;
> - `[pj <pfad>]` = `state/herleitung_h32/power_h32.json` (sha256 `df17cafa337bc548c01f08bb85bf2845cc87e203e39541d45804049b94d51bf3`, zweimal bitgleich erzeugt);
> - `[abg.]` = hier abgeleitet, Rechenweg daneben; `[sek]` Sekundaerbeleg; UNBELEGT blockiert.
>
> **Notation.** `fm8` = `fm_neutral_8w`. "In Richtung" heisst vorzeichenbereinigt (positiv fuer mom1/mom2/mom4,
> negativ fuer rev_gap). `m` = Mittel des fm8-Fenstermittels unter der stress-Null in Richtung (das extremere aus
> driftfrei/Drift 0,002). S1/S2/S3 = drei Lesarten der Test-SE (EV-5). z_krit = 1,6449, MDE-Faktor = 2,4865 (DEC-94 (1)).

---

## 0. Befund in Kuerze

1. **Die Testseite traegt.** Mit fm8 als Primaerstatistik und bindender SE (S1, stress) ist die MDE80 des schwaecheren
   Testfensters W1: mom1 **0,0206**, mom2 0,0237, mom4 0,0287, rev_gap **0,0195** (W2: 0,0165 / 0,0184 / 0,0221 / 0,0167)
   `[pj power.power_table.<v>.S1_draws_sd_bindend.thresholds]`. Die Auftragszahl "MDE80 ~0,0176" (W1 mom1) rechnet ohne
   Varianzfaktor c und ohne das mechanische Null-Mittel (Richtung Testbarkeit); P-1-konform sind 0,0192 (S2) bis 0,0206 (S1).
2. **Der Pilot ist weniger praezise als angenommen.** Die Vorperiode hat kleinere Querschnitte (K_t 120/202/339 gegen
   345/419/514 in W1), der Boden steigt auf 0,0705 (W1 0,0486). Erwartete Pilot-SE mom1 **0,0071** (nicht 0,0047), rev_gap
   0,0070, mom2 0,0075, mom4 0,0085 `[pj power.pilot_precision]`. Der Pilot ist damit etwa so praezise wie ein Testfenster.
3. **Pilotfenster korrigiert:** erste Formationswoche mit K_t >= 117 ist **2022-04-18** (K 120), nicht 2022-04-04 (K 111);
   letzte zulaessige Formationswoche ist **2024-06-17** (die Woche 2024-06-24 haette ihr Outcome 2024-07-01..07-07 in W1).
   W_P = 114, identisch mit der A1-Nuisance-Basis `[wp7k]`, `herleitung_a1/feasibility.json`.
4. **Neuer Befund Blind-Siegel:** Die letzte W2-Outcome-Woche der Drittfassung (2026-06-29..07-05) reicht 5 Tage in den
   Blindbereich ab 2026-07-01. Vorschlag: W2 endet mit der Outcome-Woche 2026-06-22..28 (w_judged 50); W1 bleibt bindend,
   keine Power-Wirkung.
5. **Uebergaberegel (Empfehlung Lesart A, Pilot-Punkt):** Uebergabe, wenn Vorzeichen richtig UND Pilot-Punkt minus
   Null-Gutschrift >= MDE80 des schwaecheren Testfensters (SE = groessere aus eingefrorener Null-SE und K-bereinigter
   Pilot-Streuung) UND t >= 2. 50-%-Uebergabe bei wahrem IC 0,0197 (mom1) / 0,0207 (rev_gap); Lesart B (untere
   80-%-Grenze) erst bei 0,0288 / 0,0297. Bei IC 0 Uebergabe 0,1..0,3 %.
6. **Erwartung unter dem Literaturband:** Bei Weg-B-Werten 0,004..0,012 (BELEGE 2026-10-20) liegt die
   Uebergabewahrscheinlichkeit je Variante bei 0,4..14 % (Lesart A) bzw. < 1 % (B); nur bei IC um 0,02 und darueber
   (Ficura-A* 0,033: 77..97 %) wird uebergeben. Wahrscheinlichster Ausgang: GL-012 (Pilot) mit gemessenem Grund, W1/W2
   bleiben dann ungeoeffnet.
7. **K = 4** (mom1, mom2, mom4, rev_gap); H-30-Varianten strukturell ausgeschlossen; keine Universums-Variante (U0
   empfohlen). Die Selektionsdecke bindet unter DEC-94 (7) erst ab K = 12.
8. **DEC-52 ist unter der Uebergaberegel tot:** Bedingung (ii) erzwingt Fenster-Power >= 0,80 in beiden Fenstern, also
   C10. Das schmale DEC-52-Band (mom1 0,0195..0,0206) faellt weg (Richtung Strenge).
9. **Positivkontrolle:** Die PRD-Kontrollwelt mit 8 Sektoren (Schock 0,375 sigma_e) erhoeht die Wochen-SD des fm8-IC um
   **+17,6 %** (synthetisch) und wuerde die 10-%-Regel DEC-94 (5) gegen eine Ein-Faktor-Power-Zeile verletzen; die reale
   Sektor-/Stil-Streuung ist UNBELEGT und wird erst im Pilot gemessen. Vorschlag: Power-Zeile mit der groesseren SE aus
   Null und Pilot, Kontrollwelt auf diese SD kalibriert, Injektion auf den realisierten fm8-IC kalibriert (nominal
   0,0206 ergibt realisiert nur 0,0156).
10. **Voraussetzung DEC-99** (C.18 fuer 3.0 praezisiert, Lockerung Richtung Testbarkeit); Wortlaut in EV-1.

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
| C-7 | Faktoranteil = Median des Querschnitts-R^2 der Wochenrendite auf das PIT-Beta (W1 3,2 %, W2 1,4 %) | gesehen; **vorzeichenfreie Verwandte von C-1** (R^2 statt IC), das Vorzeichen des Beta-IC ist nicht gesehen | `[v5e windows.<W>.factor_calibration.factor_share]` |
| C-8 | v5e-W2-Kalibrierung enthaelt die Woche 2026-06-29..07-05 (5 Tage im Blindbereich), berechnet 2026-10-12 vor DEC-96 | neu festgestellt, offengelegt | v5e W2 = 52 Wochen 2025-07-07..2026-06-29 |
| C-9 | Pilotperiode: A1 hat A3-Faktorrenditen (Dezil-L/S auf mom1/mom2/mom4/rev_gap) 2022-04..2024-06 berechnet; gespeichert nur R^2 (0,063..0,068), Steigungen, Residual-Streuung, **kein Mittel** | existiert; Steigungswerte in dieser Herleitung nicht gelesen | `herleitung_a1/FEASIBILITY.md` 3.2, `feasibility.json ...a3_factor_regression` |
| C-10 | Literaturband (beta-neutraler Wochen-IC): Weg B 0,004..0,012; Ficura-A* 0,033 (Large and Liquid) / -0,064 (Small or Illiquid); LTW FM > 1 Mio -0,011..-0,019; "Momentum grosser Coins seit Anfang 2021 nicht profitabel" (Ficura); Ficura-Stichprobe ueberlappt das Pilotfenster bis 2022-12 | gesehen | `BELEGE_AUS_PDF_2026-10-20.md` 4, 8 |
| C-11 | Ereignis 2025-10 (Flash Crash, ohne Wert) aus He et al. v7; Vorwissen der Agenten ueber Marktniveaus 2022-2026 (nicht quantifizierbar, in keiner Zahl verwendet) | offengelegt | BELEGE 9 |

**Befund:** Fuer die fm8-Statistik der vier Varianten ist **keine reale IC gelesen** worden, weder in W1/W2 noch im
Pilotfenster. Gesehen sind nur Differenzen (C-3), vorzeichenfreie Verwandte (C-7), Streuungen (C-6) und das
Literaturband (C-10). W1/W2 und das Pilotfenster gelten fuer H-32 als blind, mit dem Etikett C.17 aus der
Erstfassung Abschnitt 7.

---

## EV-1 - Programmregel DEC-99 (Voraussetzung, Wortlaut-Vorschlag)

**Frage.** C.18 fuehrt aeltere Historie als "rein deskriptives Aera-Profil" (Kompendium C.18). Ein Pilot-Schaetzfenster,
das den Prior fuer die Testfenster liefert, ist damit nicht vereinbar. DEC-98 Nachtrag 2 benennt den Pilot als einzigen
Prior-Weg fuer H-32.

**Wortlaut-Vorschlag:**

> **DEC-99 - Programmregel REZENZ 3.0 (C.18 praezisiert): das juengste Fenster ist notwendige Bedingung; aeltere Daten
> nur vorab registriert als Pilot-Schaetzfenster oder als zusaetzliches Urteilsfenster - prospektiv, Etikett
> "Lockerung (Richtung Testbarkeit), beschlossen nach GL-032..034".**
> - **Anlass:** GL-032, GL-033, GL-034 (drei Kandidaten an der Power gescheitert, kein Verdikt); DEC-98 Nachtrag 2: kein
>   Literatur-Prior >= 0,020 fuer den beta-neutralen Querschnitts-IC belegt; ein Prior ist nur ueber eine Pilot-Schaetzung
>   auf Daten vor dem ersten urteilstragenden Fenster zu gewinnen. C.18 laesst das in der geltenden Fassung nicht zu.
> - **Regel:**
>   (1) **Notwendige Bedingung REZENZ.** Jede Registrierung hat ein urteilstragendes Fenster, das am juengsten
>   ergebnisblind nutzbaren Tag endet (bei einem Blind-Siegel: am letzten Tag vor dem Siegel); dieses Fenster muss
>   bestehen. Kein PASS ohne Bestehen des juengsten Fensters.
>   (2) **Aeltere Daten** (vor dem fruehesten urteilstragenden Fenster) duerfen nur vorab registriert genutzt werden:
>   (a) als **Pilot-Schaetzfenster**: es liefert ausschliesslich Prior und Nuisance (Streuung, Varianzfaktor) fuer die
>   Power-Zuordnung nach einer vorab fixierten, mechanischen Uebergaberegel; es ist nie urteilstragend, sein Ergebnis geht
>   in kein Gate und keine Verdiktzeile ein und ist nach der Uebergabe verbraucht (Etikett "Pilot, nicht urteilstragend");
>   oder (b) als **zusaetzliches Urteilsfenster** unter C.10 (jedes Fenster muss bestehen), nie als Ersatz des juengsten.
>   (3) **Bedingungen eines Pilot-Schaetzfensters:** K der Registrierung zaehlt alle Pilot-Varianten; Varianten ohne
>   Uebergabe gehen mit p = 1 in den festen BH-Nenner ein; Uebergaberegel und Prior-Lesart sind vor dem Oeffnen des
>   Pilotfensters registriert; die letzte Outcome-Woche des Pilotfensters endet vor dem ersten Kalendertag des ersten
>   urteilstragenden Fensters (keine Kalenderwoche ist zugleich Pilot-Outcome und Testwoche; der Rueckblick von
>   Charakteristiken und Betas eines Testfensters in die Pilotperiode ist Formation und zulaessig, DEC-75 (8));
>   ein Code-Waechter verhindert im Pilot-Modus jede
>   Outcome-Rechnung ausserhalb des Pilotfensters (Siegel-Test); das Pilot-Ergebnis wird mit sha256 festgehalten (DEC oder
>   GL-Vermerk), bevor ein Testfenster gerechnet wird.
>   (4) Ein Pilot-Schaetzfenster ist **kein Zensus im Sinne von DEC-58 E2**: die Uebergabe ist eine registrierte Stufe
>   derselben Hypothese mit eigenem K, keine Promotion aus einem Zensus.
>   (5) **Unveraendert:** alpha 0,05 einseitig je Fenster, C.10 hart oder DEC-52 nach DEC-94 (6), Power-Ziel 0,80,
>   DEC-94 (1)-(9), DEC-53, Blind-Siegel DEC-96 E3. Der Pilot aendert keine Fehlerrate des Tests (getrennte Daten);
>   er bestimmt nur, ob und mit welchem Prior getestet wird.
> - **Etikett (Pflicht):** "Lockerung (Richtung Testbarkeit) von C.18 'aeltere Historie rein deskriptiv', beschlossen nach
>   Kenntnis von GL-032, GL-033, GL-034 und DEC-98 Nachtrag 2, vor jeder Pilot-Zahl. Fehlerraten und Power-Ziel
>   unveraendert. Nicht rueckwirkend (GL-032..034, DEC-92/93/97 bleiben)."
> - **Rueckbauweg:** neue DEC; Registrierungen unter DEC-99 bleiben unter DEC-99.

**Richtung:** Testbarkeit (der Kern der Lockerung). **Empfehlung:** dem Nutzer vorlegen; ohne DEC-99 ist H-32 nicht
registrierbar (kein belegter Prior, DEC-98 E1 (a)).

**Begruendung, dass DEC-99 keine Fehlerrate bewegt:** Pilot und Test teilen keinen Datenpunkt (EV-2). Unter der
globalen Null ist die Rate falscher Uebergaben je Variante 0,1..0,3 % (Lesart A) und der Test behaelt danach alpha 0,05
je Fenster (C.10 gemeinsam 0,25 %). Die Gesamtrate eines falschen H-32-PASS ist hoechstens 4 x 0,003 x 0,0025, also
etwa 3e-5 [abg.]. Die Lockerung betrifft die Herkunft des Priors, nicht die Schwelle.

**Kompendium C.17 stuetzt das Design:** "die Entdeckungszelle ist NICHT konfirmatorisch, Konfirmation braucht ANDERE
Zellen/Fenster" - der Pilot ist die Entdeckungszelle, W1/W2 sind die anderen Fenster.

---

## EV-2 - Fenster: Pilotbeginn, Pilotende, W2-Schnitt am Blind-Siegel

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
W1 (dort Formationsrendite von mom1/mom2/mom4 und Gap-Woche-Vorlauf von rev_gap). Code-Lesart:
`prelaunch.slice_window(weeks, "2022-04-18", "2024-06-30")` ergibt 115 Wochen, w_judged = 114. **Richtung:** Strenge
(Datentrennung).

**(c) W2-Schnitt am Blind-Siegel (neu).** W2 der Drittfassung hat 52 Wochen 2025-07-07..2026-06-29; die letzte
Outcome-Woche 2026-06-29..07-05 (Schlusskurs 2026-07-05) liegt mit 5 Tagen im Blindbereich ab 2026-07-01. DEC-96 E3
verlangt, das Panel bei 2026-06-30 abzuschneiden, und DEC-98 E1 (b) erfasst A3-Fenster ausdruecklich (fm8 regressiert
auf das BTC-Beta, das Outcome enthaelt die BTC-Rendite dieser Woche).

| Lesart | W2 | w_judged | MDE80 W2 mom1 (S1) | Richtung |
|---|---|---:|---:|---|
| **W2-Schnitt (Empfehlung)** | 2025-07-01..2026-06-28 (Wochen 2025-07-07..2026-06-22) | 50 | 0,0165 | Strenge, siegelkonform |
| wie Drittfassung | 2025-07-01..2026-06-30 | 51 | 0,0164 | Testbarkeit (minimal), Siegelverstoss durch Nebenprodukt |

W1 bleibt in jeder Variante das schwaechere Fenster `[pj power.sensitivity_W2_uncut_w_judged_51]`; der Schnitt kostet
keine Power der Uebergaberegel. Offenlegung C-8: die v5e-W2-Kalibrierung enthaelt diese Woche bereits (vor DEC-96).

---

## EV-3 - Varianten und Selektions-K

**(a) Varianten.** mom1, mom2, mom4 (positiv), rev_gap (negativ, Lag-2-Gap-Design wie DEC-87 (B)). Richtungen aus PRD
5.3, unveraendert; eine Richtung wird nie nach dem Pilot gewaehlt (Bedingung (i) der Uebergaberegel). Ein
Zwei-Richtungen-Design fuer mom1 (Momentum ODER Reversal, BELEGE 8: Vorzeichen haengt am Universum) wuerde K
verdoppeln und ist nicht vorgeschlagen (Richtung Strenge).

**(b) H-30-Varianten: Ausschluss (empfohlen).**
- `vol_beta`: unter fm8 strukturell neutralisiert - das OLS-Residuum ist per Konstruktion orthogonal zum Beta, das
  vol_beta misst (C.4, DEC-87 (H)). Unter fm8 als Primaerstatistik ist ein IC ~0 garantiert, kein Test.
- `vol_rv`, `vol_max`: GL-012 der Drittfassung wegen Wochen-Drag-Spread(D10-D1)/Kante 2,764 > 0,5 (DEC-88). Der Drag
  haengt an sigma, nicht am Beta; fm8 beseitigt die Ursache nicht. Ein A3-V-Design braucht ein Outcome, das den Drag
  strukturell entfernt (eigene Hypothese).
- **Richtung:** neutral (struktureller Grund vorab bekannt); K kleiner.

**(c) K.**

| Lesart | K | z_max(K) | wirksames z (DEC-94 (7)) | BH-Nenner | Richtung |
|---|---:|---:|---:|---:|---|
| **K = 4 eigene Familie F-H32, F-XSEC1 (7, alle p = 1) in der Ueber-Familie F-WEEK (BY am Wellenschluss) (Empfehlung)** | 4 | 1,052 | 1,6449 | 4 | Testbarkeit relativ zu K = 11 (BH-Nenner), ohne z-Wirkung |
| K = 11 (4 + 7, Review Programm-Bilanz B-1 (2)) | 11 | 1,622 | 1,6449 | 11 | Strenge (nur BH, report-only) |
| K = 12 (mit einer Universums-Variante U1 + 7) | 12 | 1,665 | 1,665 | 12 | Strenge, Schwelle +1,2 % |

`[pj power.selection]`. In keiner Lesart aendert sich das bindende z, solange K <= 11. Die F-XSEC1-Varianten haben nie
eine reale IC erzeugt; sie in der Ueber-Familie mitzufuehren, deckt die Bilanz-Auflage ohne Doppelzaehlung.

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

**Bewertung.** (1) Die Zuordnung der Bybit-Umsatzdezile zu Ficuras USD-Schwellen ist **UNBELEGT** (die Akte fuehrt keine
Umsatzniveaus, der Spread-Zensus nur Raenge, Stichtag 2026-09-21); alle Bybit-Perps koennten bereits "liquide" im Sinne
der Quelle sein. (2) Die einzige Quelle mit Liquiditaetssplit meldet fuer grosse Coins nach 2021 kein Momentum mehr -
der Liquid-Prior ist fuer Pilot und Testfenster gerade nicht gestuetzt. (3) U1 kostet MDE (+10 %), Pilotlaenge (-8
Wochen) und eine Gabelung Richtung Testbarkeit.

**Empfehlung: U0** (Richtung Strenge). Das Liquiditaets-Teiluniversum wird im Pilot und im Test fuer jede Variante als
report-only Sensitivitaet berichtet (nie uebergabe- oder urteilsrelevant; IC_ohne_D1 wie Drittfassung Gate (4c), dazu
Buckets 3..10). U1 nur, wenn der Orchestrator den Universums-Befund hoeher gewichtet - dann vor dem Pilot, mit K = 5.

---

## EV-5 - SE der Power-Zeile und Null-Mittel-Gutschrift

**Fundstellen.** `[v5e windows.<W>.beta_control_recommended_high_rep.{stress,stress_drifting}.variants.<v>]` (1.000
Replikate): `factor_sd` (SD des Wochen-IC unter der Null), `mean_ic_draws_sd` (SD des Fenstermittels), `mean_ic_draws_mean`.
`[v5e ...beta_control_method_study...fm_neutral_8w.variants.<v>.n_ic_pooled]`: 13.500 / 300 = **45** IC-Wochen je
Replikat in W1 (W2: 44) statt 52/51 - die Null-Simulation hat keine Beta-Vorlaufwochen (Etikett der Drittfassung
"Coverage 0,889/0,877"); der Lauf dagegen schaetzt Betas auf dem vollen Panel und hat 52/51 Wochen.

| Lesart | Formel | W1 mom1 | MDE80 W1 mom1 (+ Gutschrift) | Richtung |
|---|---|---:|---:|---|
| **S1 (Empfehlung, bindend)** | SE = SD des Fenstermittels der Null (`mean_ic_draws_sd`, max driftfrei/Drift) | 0,00794 | **0,0206** | Strenge (45-Wochen-Mittel, ~+7..13 % gegen 52 Wochen) |
| S2 | sqrt(max(1, c_sim)) x SD / sqrt(w_judged), c_sim = 45 x draws_sd^2 / SD^2 = 1,080 | 0,00739 | 0,0192 | P-1-exakt fuer 52 Wochen, aber ohne K_fm8-Verlust |
| S3 (Auftrag) | SD / sqrt(w_judged), c = 1 | 0,00711 | 0,0185 (ohne Gutschrift 0,0176) | Testbarkeit (verstoesst gegen DEC-94 (4) c = max(1, c_hat)) |

`[pj power.nuisance.<v>.<W>.se]`. **Nebenbefund:** Die Bilanz-Konvention c_hat = 52 x draws_sd^2 / SD^2 (1,25..1,28)
ist ein Artefakt der 45-Wochen-Ziehungen; mit konsistenter Wochenzahl liegt c_hat bei 0,99..1,11. Der synthetische
Check (EV-8) bestaetigt: 52-Wochen-SD des Fenstermittels 0,0070..0,0072 gegen S1 0,0079.

**Gutschrift.** Das mechanische Null-Mittel in Richtung (stress, extremeres aus driftfrei/Drift) ist W1 mom1 +0,00087,
mom2 +0,00142, mom4 +0,00185, rev_gap -0,00114 (gegen die Richtung). Die Testschwelle ist
`T = z_krit x SE + max(0, m)`: ein positives m erhoeht die Schwelle, ein negatives wird nicht gutgeschrieben
(Richtung Strenge). Umgesetzt im Gate als zweite Bedingung "Statistik >= 95-%-Quantil der stress-Null" (EV-7).

**Empfehlung:** S1 bindend bis zum Vorlauf v6; v6 rechnet die Null mit 8 Beta-Vorlaufwochen (52/50 Wochen) und den
realen K_fm8-Reihen neu; dann gilt das Maximum aus v6-SE und S1-Lesart nicht mehr, sondern die v6-SE (P-1 (3):
SE des registrierten Tests). Die Power-Tabelle unten ist mit S1 gerechnet; S2/S3 stehen in `[pj power.power_table.<v>]`.
Bericht: unter der measured-Kalibrierung waere MDE80 W1 mom1 0,0185 (nicht bindend, DEC-94 (5)).

---

## EV-6 - Uebergaberegel P -> T und Prior-Lesart

**Regel U (eine Regel, vorab fixiert, mechanisch, je Variante v):**

- Eingaben aus dem Pilot (nur Pilotfenster): x_P = Mittel der fm8-Wochen-ICs in Richtung; SE_P nach P-1 (4):
  max(B_P/sqrt(W_P), SD/sqrt(W_P), SE_stat) mit stationaerem Bootstrap (mittlere Blocklaenge 4, 1.000, Seed 53,
  `power_p1.stationary_bootstrap_se`); t_P = x_P / SE_P; 80-%-Band x_P +- 1,2816 x SE_P (normal, zweiseitig); die
  realisierte K-bereinigte Streuung F2_real = max(0, SD_P^2 - mean_t 1/(k_t - 1)) mit k_t = Zahl der Symbole im
  fm8-IC der Woche t; c_real = max(1, W_P x SE_stat^2 / SD_P^2).
- Test-SE je Fenster: SE_T,W = max(SE_W,eingefroren (v6), SE_W,Pilot) mit
  SE_W,Pilot = sqrt(c_real) x sqrt(V_W + F2_real) / sqrt(w_judged,W), V_W = mean_t 1/(K_fm8,t - 1) des Testfensters
  (outcome-frei aus v6). Das ist DEC-94 (5): beide Quellen, die groessere bindet.
- Null-Gutschrift m = max_W m_W, m_W = eingefrorenes Null-Mittel in Richtung (v6, stress, extremeres aus
  driftfrei/Drift); es dient zugleich als Proxy fuer das ungemessene Null-Mittel der Pilotperiode (heute W1: mom1
  +0,00087, mom2 +0,00142, mom4 +0,00185, rev_gap -0,00114 -> keine Gutschrift).
- **(i)** x_P > 0. **(ii)** x_P - max(0, m) >= 2,4865 x max_W SE_T,W (MDE80 des schwaecheren Testfensters).
  **(iii)** t_P >= 2,0.
- Alle drei erfuellt -> **Uebergabe**; Prior der Zuordnung pi = x_P (Lesart A); Regime =
  `power_p1.assign_regime([pi - max(0, m_W1), pi - max(0, m_W2)], [SE_T,W1, SE_T,W2])` (unter (ii) stets C10);
  Doppelausweis `assign_regime_a3_practice`. Sonst **GL-012 (Pilot)** mit dem gemessenen Grund (welche Bedingung,
  welche Zahlen); p = 1 im BH-Nenner 4.

**Vorab-Zahlen der Schwelle (ii)** (S1, v5e; der Pilot kann sie nur erhoehen): mom1 0,0206, mom2 0,0237, mom4 0,0287,
rev_gap 0,0195 (jeweils auf x_P, Gutschrift eingerechnet). (iii) bindet erst, wenn SE_P > halbe Schwelle (~0,0103), also
bei einer Pilot-Streuung ~45 % ueber der Vorhersage; sonst redundant, bleibt als Waechter.

**Gabelung Prior-Lesart.**

| Lesart | Bedingung (ii) wirkt auf | wahrer IC fuer 50 % / 80 % Uebergabe (mom1 / rev_gap) | P(Uebergabe), IC = 0 | Zwei-Stufen-Power mom1 bei IC 0,020 / 0,025 / 0,033 | Richtung |
|---|---|---|---|---|---|
| **A Punkt (Empfehlung)** | x_P | 0,0197 / 0,0207 ; 0,0257 / 0,0266 | 0,003 / 0,002 | 0,39 / 0,71 / 0,96 | Testbarkeit |
| B untere 80-%-Grenze (x_P - 1,2816 SE_P) | x_P - 1,2816 SE_P | 0,0288 / 0,0297 ; 0,0348 / 0,0356 | < 0,001 | 0,08 / 0,27 / 0,72 | Strenge |

`[pj power.handover_oc.<v>.{A_punkt,B_untere_80}]` (Pilot-SE vorhergesagt, Null-Mittel W1 als Pilot-Proxy).

Uebergabewahrscheinlichkeit, Lesart A (Lesart B) je wahrem IC:

| IC | mom1 | mom2 | mom4 | rev_gap |
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

**Bewertung.** (1) Die Fehlerrate des Tests ist von der Lesart unabhaengig (getrennte Daten). (2) DEC-51 (2) nennt die
"A-priori-Erwartung" als Vergleichsgroesse; der Pilot-Punkt ist der Schaetzer dieser Erwartung, und unter (ii) gilt fuer
jede uebergebene Variante Power >= 0,80 am Pilot-Punkt. (3) Die DROP-Lesart des Tests bezieht sich auf Effekte >= MDE80;
eine uebergebene Variante mit wahrem IC knapp unter MDE80 erzeugt deshalb keine falsche Widerlegung der registrierten
Effektgroesse. (4) Lesart B verschiebt die 50-%-Schwelle um 1,28 SE_P (~+0,009) und verwirft Effekte zwischen 0,021 und
0,029, die der Test mit >= 0,80 saehe, als GL-012 - Verlust ohne Gewinn an Fehlerkontrolle. (5) Gegenargument fuer B:
Gewinnerfluch bei 4 Varianten; er wirkt aber nur auf die Hoehe des berichteten Priors, nicht auf das Regime (unter (ii)
stets C10) und nicht auf die Positivkontrolle (injiziert MDE80, nicht x_P).
**Empfehlung: Lesart A** - offen etikettiert als Gabelung Richtung Testbarkeit; die Strenge liegt in (ii) mit S1 und in
der Pilot-Streuung als zweiter SE-Quelle.

**DEC-52 unter der Regel.** `assign_regime` gaebe DEC52 in einem schmalen Band unter der C10-Schwelle (mom1 0,0195..0,0206,
mom2 0,0222..0,0237, mom4 0,0267..0,0287, rev_gap 0,0190..0,0195) `[pj power.power_table.<v>.S1_draws_sd_bindend.first_prior_dec52_or_c10]`.
(ii) schliesst es aus. Alternative "(ii) := assign_regime(pi) != GL012" waere Richtung Testbarkeit (+~5 Prozentpunkte
Uebergabe nahe 0,02). **Empfehlung:** (ii) wie oben (Richtung Strenge, einfacher).

**Literaturband (C-10) als Erwartung, nicht als Prior:** Weg B 0,004..0,012 -> Uebergabe A: mom1 1,3..13,7 %, mom2
0,8..8,6 %, mom4 0,4..4,0 %, rev_gap 0,9..10,9 %; B: < 1 %. Ficura-A* 0,033 -> A 97/92/77/96 %, B 72/56/29/68 %
`[pj power.handover_literature_band]`.

**Nach dem Pilot ist das Pilotfenster verbraucht:** fuer die vier fm8-Statistiken nicht mehr blind (Etikett fuer jede
spaetere Hypothese), nie urteilstragend. Ohne Uebergabe bleiben W1/W2 ungeoeffnet und blind.

---

## EV-7 - Teststufe: Statistik, Schwelle, Bedingungen, was nicht gerechnet wird

**Statistik:** Mittel der woechentlichen Spearman-ICs der Charakteristik gegen das fm8-neutralisierte Folgewochen-Outcome
(`ic.apply_beta_control("fm_neutral_8w", ...)` + `ic.weekly_ic_series`, close_at_last, min 10 Symbole), exakt die
IC_res der Drittfassung, jetzt Primaerstatistik.

**Bedingungen je Fenster (C.10 hart):** (1a) Vorzeichen; (1b) Statistik in Richtung >= z_krit x SE_W, SE_W =
max(B_W/sqrt(W), SD/sqrt(W), SE_stat) (P-1 (4), Boden aus K_fm8); (1c) Statistik in Richtung >= q95_W (95-%-Quantil des
fm8-Fenstermittels unter der stress-Null, extremeres aus driftfrei/Drift 0,002, eingefroren aus v6; P-1 (1): Null-Quantile
auf dem Niveau 1 - alpha); (4b) nur rev_gap: Bounce-Kill je Fenster wie Drittfassung. Vor-Verdikt-Kill: Selektionsdecke
(Mittel des Maximums ueber K = 4, **vorzeichenbereinigt**) >= eingefrorene Schwelle -> GL-012.

**Nebenbefund Decke:** `nulls._mean_of_max` nimmt das Maximum der rohen (nicht vorzeichenbereinigten) Fenstermittel;
eine negativ registrierte Variante (rev_gap) traegt dort ihre Gegenrichtung bei. Fuer H-32 neue, vorzeichenbereinigte
Funktion (additiv, A3-Code unberuehrt). Grobe Naeherung K = 4: Decke / Schwelle 0,64..0,67 `[pj power.ceiling_check]`.

**Nicht gerechnet (Empfehlung, Richtung Strenge/Blindheitsschutz):** roher IC, Lag-Profil, Beta-Kalibrierungs-IC,
Persistenz-Null. Jede dieser Zahlen wuerde W1/W2 fuer kuenftige Roh-, Lag- oder Beta-Hypothesen entblinden und traegt
kein Gate. Ausrichtung (Lag) ist ueber T1-Fixtures abgesichert. Report-only bleiben: Block-Permutations-p (Max-p), BH
(Nenner 4), Liquiditaets-Teiluniversen (EV-4), Survivorship-Etikett (synthetisch).

---

## EV-8 - Positivkontrolle in Produktionskonfiguration (Pruefung der Power-Annahme)

**Befund aus dem synthetischen Check** (`[pj synthetischer_check]`; Repo-Code `positive_control.synthesize_window_returns`,
`characteristics.beta_characteristic`, `ic.apply_beta_control`, `ic.weekly_ic_series` auf einem kuenstlichen Panel K = 419,
52 Urteilswochen + 8 Vorlaufwochen, W1-stress-Welt der registrierten Drittfassung; kein Realdatum):

| Sektorschock / sigma_e | Wochen-SD fm8-IC mom1 | SD des 52-Wochen-Mittels |
|---:|---:|---:|
| 0 | 0,0520 | 0,0070 |
| 0,1 | 0,0520 | 0,0072 |
| 0,2 | 0,0527 | 0,0075 |
| 0,375 (PRD-Fixture, DEC-89) | 0,0611 (**+17,6 %**) | 0,0088 |

- fm8 entfernt nur das BTC-Beta; gemeinsame Sektor-/Stilschocks bleiben in der Statistik. Die stress-Null der Akte ist
  Ein-Faktor; die reale Zusatzstreuung ist **UNBELEGT** und wird erst im Pilot gemessen (F2_real, EV-6).
- Mit der PRD-Sektorwelt und einer Ein-Faktor-Power-Zeile waere die Positivkontrolle nach DEC-94 (5) NICHT BESTANDEN
  (SD > 1,10 x Power-Zeile).
- Injektion: nominal 0,0206 ergibt realisiert 0,0156 (75 %) im fm8-IC; Bestehensquote an der eingefrorenen Schwelle
  0,617 gegen 0,633 vorhergesagt aus realisiertem Mittel und SD; Negativkontrolle 0,033. Die Mechanik ist konsistent,
  die Injektion muss aber auf den **realisierten** fm8-IC kalibriert werden.

**Vorgeschlagene Regel (vorab fixiert, je uebergebener Variante):**
1. **Welt:** stress-Kalibrierung je Fenster aus der YAML (rho_f, beta_sd, null_scales), Marktspalte = Faktor, Drift 0,
   reale Wochenform (K_t, PIT-Masken); Sektorschock sigma_g per Bisektion so, dass die Wochen-SD des fm8-IC der
   Negativkontrolle der bindenden Power-Zeilen-SD (max aus Null und Pilot, EV-6) auf +-5 % entspricht (sigma_g = 0, wenn die
   Null bindet).
2. **Injektion:** Amplitude auf getrennten Kalibrierungs-Seeds (1000..1049, gemeinsame Zufallszahlen) so gewaehlt, dass
   der realisierte Injektionseffekt (positiv minus negativ, fm8) im bindenden Fenster MDE80_T,v - max(0, m) auf +-5 %
   trifft.
3. **Seeds:** 53..252 (200) fuer positiv und negativ.
4. **BESTANDEN genau dann, wenn:** (a) DEC-94 (5): SD der Kontrollwelt <= 1,10 x SD der Power-Zeile in jedem Fenster;
   (b) Anteil PASS der Fensterbedingungen (1a)-(1c) im bindenden Fenster >= 0,80 - 2,326 x sqrt(0,16/200) = **0,734**;
   (c) Negativkontrolle: falsche PASS-Quote je Fenster <= 0,05 + 2,326 x sqrt(0,0475/200) = **0,086**;
   (d) realisierter Injektionseffekt auf den Urteils-Seeds innerhalb +-10 % des Ziels. Sonst kein Lauf, neue DEC.
5. Die gemeinsame C10-Quote wird berichtet (erwartet ~0,8 x Power des anderen Fensters), nicht geurteilt.

Kontrolle der Strenge: Unter S1 (konservativ) liegt die erwartete Bestehensquote bei Injektion MDE80 ueber 0,80
(realisierte 52-Wochen-SE ~0,0071 statt 0,0079) - die Regel prueft, dass die Annahme nicht optimistisch ist, wie DEC-91
es verlangt haette.

---

## 2. Power vorab (nur Nuisance, ohne Pilot) - Prior-Gitter

Prior = erwartete Statistik in Richtung (das, was der Pilot-Punkt schaetzt). S1, W2 geschnitten (w_judged 50).
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

**Pilot-Praezision** (vorhergesagt, W_P 114, Boden aus `[wp7k]`, Faktorstreuung F2 und c aus v5e-stress):

| | mom1 | mom2 | mom4 | rev_gap |
|---|---:|---:|---:|---:|
| SD_P (Woche) | 0,0728 | 0,0779 | 0,0860 | 0,0730 |
| **SE_P** | **0,0071** | 0,0075 | 0,0085 | 0,0070 |
| Auftrag (0,0511 / sqrt(117)) | 0,0047 | - | - | - |
| Sens.: F doppelt / Neulistungen (K_fm8 ~ K - 8 Wochen Listungen) | 0,0076 / 0,0074 | 0,0092 / 0,0078 | 0,0119 / 0,0088 | 0,0076 / 0,0074 |

Rechenweg [abg.]: SD_P^2 = mean_t 1/(K_t - 1) (Pilot, 0,00504) + F2, F2 = max_W (SD_W^2 - mean_t 1/(K_t - 1)) (W1 mom1
0,00026); SE_P = sqrt(c) x SD_P / sqrt(114), c = max_W max(1, c_sim). Listungszahlen je Jahr aus WELLE1 Teil 6 (2022:
86, 2023: 113, 2024: 228).

---

## 3. Bauliste und Bauaufwand (nach DEC-99, vor der Registrierung)

Additiv in neuen Dateien (A3-Code-Fingerprint der Drittfassung bleibt unberuehrt; DEC-94 (8)).

| # | Baustein | Inhalt | Umfang (Code + Tests) |
|---|---|---|---|
| B-1 | Vorlauf v6 (outcome-frei) | fm8-stress-Null mit 8 Beta-Vorlaufwochen (reale Lebend-Masken davor) fuer W1, W2 (geschnitten), K = 4, 1.000 Replikate, driftfrei und Drift 0,002: Fenstermittel-SD, Wochen-SD, Null-Mittel, q95, vorzeichenbereinigte Decke K = 4; K_fm8-Reihen (lebend und 8 gueltige Beta-Wochen; nur `returns_valid`, kein Renditewert) fuer W1, W2, Pilot; Boden je Fenster; Stress-Abdeckung nur fensterbeschraenkt (Pilot, W1, W2) ausgeben; Daten-Fingerprints | ~250 + 150 Zeilen; Cloud ~0,5-1 h |
| B-2 | Pilot-Modus `--pilot` | Startsperre (YAML-sha256); Waechter: keine Outcome-Woche nach 2024-06-30 (monkeypatch-Siegeltest wie `test_seal_*`); fm8-Wochen-IC je Variante nur im Pilotfenster; SE_P (P-1 (4), `power_p1.stationary_bootstrap_se`), Band, t, F2_real, c_real; Regel U mechanisch; Regime via `power_p1`; Artefakte DEC-53 (Wochenserie CSV + sha256, Bootstrap-Fingerprint), `h32_pilot.json` mit result_sha256 | ~300 + 300 |
| B-3 | Testlauf H-32 | Startsperre YAML UND `--pilot-result` + sha256; Regel U wird aus dem Pilot-JSON deterministisch nachgerechnet (keine Handwahl); nur uebergebene Varianten; neue reine Gate-Funktion (P-1: z_krit aus YAML, SE-Regel P-1 (4), q95, Decke, Bounce) mit T4; BH Nenner 4; Waechter: keine Outcome-Woche nach 2026-06-28; kein roher IC, kein Lag-Profil, kein Beta-IC | ~400 + 300 |
| B-4 | Positivkontrolle H-32 | Welt-SD-Kalibrierung (Sektor-Bisektion), Injektions-Kalibrierung, 200 Seeds, Kriterien EV-8 | ~250 + 200 |
| B-5 | Schema/Template | YAML-Felder `pilot_window`, `handover_rule`, `alpha`, `z_krit`, `mde_faktor`, `primary_statistic`, `windows.<W>.frozen_v6`, T5-Pins | ~150 + 100 |
| B-6 | Tests | DEC-39-Trio fuer fm8-primaer; T2 N >= 3 mit Fingerprint; T4 Uebergabe-Arithmetik auf konserviertem Pilot-Payload; Monotonie (hoeherer Pilot-Punkt kippt nie von Uebergabe zu GL-012); T5; T6; T7 | in den Zahlen oben |

**Summe:** ~1.350 Zeilen Code, ~1.050 Zeilen Tests; zwei Bau-Sitzungen (Builder) plus Abnahme. Rechenzeit Cloud: v6
~0,5-1 h, Pilot < 15 min, Positivkontrolle ~15-30 min, Testlauf ~1 h (Null-Nachrechnung +-10 %) - Lauf-Dauer UNBELEGT.
Panel: derselbe Harvest-Export wie v5e (as_of 2026-09-28), keine neuen Daten.

**Reihenfolge:** DEC-99 (Nutzer) -> Orchestrator-Entscheidungen zu EV-1..EV-8 -> Bau B-1..B-6 -> Vorlauf v6 -> finale
YAML + sha256 -> adversarisches Review -> Registrierung -> Pilot -> Uebergabe-Vermerk (sha256) -> bei Uebergabe:
Positivkontrolle allein -> Testlauf -> GL-Eintrag; ohne Uebergabe: GL-012 (Pilot), W1/W2 bleiben ungeoeffnet.

---

## 4. UNBELEGT und offene Punkte

| Punkt | Status | Wirkung |
|---|---|---|
| Literatur-Prior des beta-neutralen Wochen-IC >= 0,020 | UNBELEGT (DEC-98 N2) | ersetzt durch den Pilot; setzt DEC-99 voraus |
| Reale Sektor-/Stil-Streuung des fm8-IC (Null ist Ein-Faktor) | UNBELEGT bis zum Pilot | kann MDE80_T und Schwelle (ii) erhoehen; Kontrollwelt haengt daran |
| Mechanisches Null-Mittel der Pilotperiode | UNBELEGT (Proxy W1-stress, ~0,001) | Groessenordnung 5 % der Schwelle; optional v6-Pilot-Kalibrierung |
| 52-Wochen-SE der Null mit Beta-Vorlauf, K_fm8-Reihen | offen (v6) | S1 bis dahin bindend (konservativ) |
| Zuordnung Bybit-Umsatzdezile zu "Large and Liquid" | UNBELEGT | Grund fuer U0 |
| Laufzeit des Testlaufs | UNBELEGT (~1 h geschaetzt) | Positivkontrolle ohnehin vorgeschaltet |

---

## 5. Gabelungs-Bilanz (DEC-93 H-1)

| EV | Empfehlung | Richtung |
|---|---|---|
| EV-1 DEC-99 | beschliessen (Nutzer) | **Testbarkeit** (Lockerung C.18) |
| EV-2a Pilotbeginn | K >= 117 (2022-04-18) | neutral (gegen 134 numerisch ohne Wirkung) |
| EV-2b Pilotende | 2024-06-17 (statt 06-24) | Strenge |
| EV-2c W2-Schnitt | 2026-06-28 | Strenge |
| EV-3a Richtungen | fest, kein Zwei-Richtungen-mom1 | Strenge |
| EV-3b H-30 | ausgeschlossen | neutral |
| EV-3c K | 4, F-XSEC1 in F-WEEK | **Testbarkeit** gegen K = 11 (ohne z-Wirkung) |
| EV-4 Universum | U0 | Strenge |
| EV-5 SE | S1 + Gutschrift nur positiv | Strenge |
| EV-6 MDE80-Quelle | max(Null, Pilot) | Strenge |
| EV-6 Prior-Lesart | A (Punkt) | **Testbarkeit** |
| EV-6 DEC-52 | ausgeschlossen durch (ii) | Strenge |
| EV-6 Pilot-Null-Mittel | Proxy W1 statt Pilot-Kalibrierung | Testbarkeit (minimal) |
| EV-7 Nebengroessen | nicht rechnen | Strenge (Blindheitsschutz) |
| EV-8 Positivkontrolle | Welt auf bindende SD, Injektion realisiert | Strenge |

Vier Gabelungen fallen Richtung Testbarkeit (davon DEC-99 als Voraussetzung), neun Richtung Strenge, zwei neutral.

---

## 6. Was nicht folgt

Kein Verdikt ueber Momentum, Reversal oder einen beta-neutralen Querschnittseffekt; keine Registrierung; keine Zahl aus
Pilot, W1 oder W2. Der Pilot wird erst nach DEC-99, Registrierung und Review gebaut und gerechnet. Die erwarteten
Uebergabewahrscheinlichkeiten sind Eigenschaften der Regel unter angenommenen wahren Werten, keine Vorhersage des
Ergebnisses. Hinweis ohne Empfehlung: Da der Pilot etwa so praezise ist wie ein Testfenster (SE 0,0071 gegen 0,0079),
erlaubt DEC-99 (2b) ihn alternativ als drittes Urteilsfenster; dafuer fehlte ein Prior wie bisher - das ist nicht
Gegenstand dieser Herleitung.
